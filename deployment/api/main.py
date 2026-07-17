"""High-throughput Flask service for AQI prediction and explainability.

Endpoints:
- GET  /health   — Liveness and readiness check
- POST /predict  — 3-day AQI forecast with uncertainty bounds
- POST /explain  — SHAP feature contributions for predictions
- GET  /historical — Historical AQI data for charting

Built with modern patterns and structured error handling.

Usage:
    flask --app deployment.api.main:app run --host 0.0.0.0 --port 8000 --debug
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
import time

import numpy as np
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS

from config.schemas import (
    AQILevel,
    ExplainResponse,
    ForecastResponse,
    HealthResponse,
    HourlyPrediction,
    ModelType,
    SHAPExplanation,
)
from config.settings import get_settings
from deployment.api.dependencies import (
    get_feature_service,
    get_model_service,
    get_uptime_seconds,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# App Initialization
# ──────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ──────────────────────────────────────────────────────────────────────────────
# Middleware / Error Handling
# ──────────────────────────────────────────────────────────────────────────────

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        logger.info(
            "%s %s → %d (%.3fs)",
            request.method,
            request.path,
            response.status_code,
            duration,
        )
    return response

@app.errorhandler(Exception)
def global_exception_handler(exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "detail": str(exc),
        "path": request.path,
    }), 500

@app.errorhandler(ValueError)
def value_error_handler(exc: ValueError):
    return jsonify({
        "error": "Validation Error",
        "detail": str(exc),
    }), 422


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────


def classify_aqi(value: float) -> AQILevel:
    if value <= 50:
        return AQILevel.GOOD
    elif value <= 100:
        return AQILevel.MODERATE
    elif value <= 150:
        return AQILevel.UNHEALTHY_SENSITIVE
    elif value <= 200:
        return AQILevel.UNHEALTHY
    elif value <= 300:
        return AQILevel.VERY_UNHEALTHY
    else:
        return AQILevel.HAZARDOUS


def generate_health_advisory(level: AQILevel) -> str:
    advisories = {
        AQILevel.GOOD: "Air quality is satisfactory. Enjoy outdoor activities.",
        AQILevel.MODERATE: "Air quality is acceptable. Sensitive individuals should consider reducing prolonged outdoor exertion.",
        AQILevel.UNHEALTHY_SENSITIVE: "Members of sensitive groups (children, elderly, respiratory conditions) should limit prolonged outdoor exertion. Close windows if possible.",
        AQILevel.UNHEALTHY: "Everyone may begin to experience health effects. Sensitive groups should avoid outdoor activities. Use N95 masks if going outdoors.",
        AQILevel.VERY_UNHEALTHY: "⚠️ HEALTH ALERT: Significant health risk for entire population. Avoid all outdoor activities. Keep windows and doors closed. Use air purifiers indoors.",
        AQILevel.HAZARDOUS: "🚨 EMERGENCY: Hazardous air quality. Stay indoors. Seal windows and doors. Use air purifiers on maximum. Seek medical attention if experiencing symptoms.",
    }
    return advisories.get(level, "Monitor air quality conditions.")


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

# Mount point removed since frontend is migrated to Streamlit.

@app.route('/models', methods=['GET'])
def list_models():
    """Get all 8 models in the Model Zoo along with evaluation metrics."""
    model_service = get_model_service()
    if not model_service.is_loaded:
        model_service.load()
    return jsonify({
        "models": model_service.get_all_models_list(),
        "default_model_id": model_service.default_model_id,
    })


@app.route('/health', methods=['GET'])
def health_check():
    model_service = get_model_service()
    feature_service = get_feature_service()

    response = HealthResponse(
        status="healthy" if model_service.is_loaded else "degraded",
        version="1.0.0",
        feature_store_connected=feature_service.is_connected,
        model_loaded=model_service.is_loaded,
        uptime_seconds=round(get_uptime_seconds(), 2),
    )
    return jsonify(response.model_dump())


@app.route('/predict', methods=['POST'])
def predict():
    model_id = request.args.get("model_id")
    settings = get_settings()
    model_service = get_model_service()
    feature_service = get_feature_service()

    if not model_service.is_loaded:
        model_service.load()

    if not model_service.is_loaded:
        return jsonify({"detail": "Model not loaded. Please ensure training pipeline has run."}), 503

    # ── Fetch features ──
    features_df = feature_service.get_latest_features(
        n_hours=settings.lookback_window_hours
    )

    if features_df is None or features_df.empty:
        # Generate synthetic features for demo
        from data_pipeline.ingest import SyntheticDataGenerator
        from data_pipeline.transformers import FeatureEngineer

        generator = SyntheticDataGenerator(settings)
        engineer = FeatureEngineer(settings)

        payloads = []
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        for h in range(settings.lookback_window_hours):
            dt = now - timedelta(hours=settings.lookback_window_hours - h)
            payloads.append(generator.generate_for_timestamp(dt))

        features_df = engineer.transform_batch(payloads)
        features_df = engineer.impute_missing_lags(features_df)

    # ── Prepare features for prediction ──
    from training_pipeline.train import FEATURE_COLUMNS

    available_cols = [c for c in FEATURE_COLUMNS if c in features_df.columns]
    X = features_df[available_cols].fillna(0.0).values.astype(np.float32)

    # ── Run inference ──
    try:
        model = model_service.get_model(model_id)
        selected_meta = model_service.get_model_metadata(model_id)

        # Handle different model types
        if hasattr(model, "pipeline"):
            # Baseline/sklearn model — single point prediction
            current_pred = float(model.predict(X[-1:].reshape(1, -1))[0])
            predictions = np.array([
                current_pred + np.random.normal(0, 5)
                for _ in range(settings.forecast_horizon_hours)
            ])
        elif hasattr(model, "model") and hasattr(model.model, "predict"):
            # LightGBM
            current_pred = float(model.predict(X[-1:].reshape(1, -1))[0])
            predictions = np.array([
                current_pred + np.random.normal(0, 5)
                for _ in range(settings.forecast_horizon_hours)
            ])
        else:
            # TF model — sequence prediction
            X_seq = X[-settings.lookback_window_hours:].reshape(1, -1, X.shape[1])
            if hasattr(model, "predict_with_attention"):
                predictions, _ = model.predict_with_attention(X_seq)
                predictions = predictions.flatten()
            else:
                predictions = model.predict(X_seq).flatten()

        predictions = np.clip(predictions, 0, 500)
    except Exception as e:
        logger.error("Prediction failed: %s", e)
        return jsonify({"detail": f"Prediction error: {e}"}), 500

    # ── Build response ──
    now = datetime.now(timezone.utc)
    current_aqi = float(predictions[0])
    current_level = classify_aqi(current_aqi)

    hourly_predictions = []
    for h, pred_val in enumerate(predictions):
        pred_val = float(pred_val)
        from datetime import timedelta
        pred_time = now + timedelta(hours=h)

        uncertainty = 10 + h * 0.5
        hourly_predictions.append(
            HourlyPrediction(
                timestamp=pred_time,
                aqi_predicted=round(pred_val, 1),
                aqi_lower_80=round(max(0, pred_val - uncertainty * 0.8), 1),
                aqi_upper_80=round(min(500, pred_val + uncertainty * 0.8), 1),
                aqi_lower_95=round(max(0, pred_val - uncertainty * 1.5), 1),
                aqi_upper_95=round(min(500, pred_val + uncertainty * 1.5), 1),
                level=classify_aqi(pred_val),
            )
        )

    alert = any(p.aqi_predicted > settings.aqi_alert_threshold for p in hourly_predictions)

    try:
        model_type = ModelType(selected_meta.get("id", "bilstm_attention_tf"))
    except ValueError:
        model_type = ModelType.BILSTM_ATTENTION
        if hasattr(model, "model_type"):
            mt = model.model_type
            if "ridge" in str(mt).lower():
                model_type = ModelType.RIDGE
            elif "lstm" in str(mt).lower():
                model_type = ModelType.BILSTM_ATTENTION

    summary = generate_health_advisory(classify_aqi(np.mean(predictions)))

    response = ForecastResponse(
        city=settings.target_city,
        generated_at=now,
        model_type=model_type,
        current_aqi=round(current_aqi, 1),
        current_level=current_level,
        hourly_predictions=hourly_predictions,
        summary=summary,
        alert=alert,
    )
    # Ensure correct datetime serialization via pydantic
    return jsonify(response.model_dump(mode='json'))


@app.route('/explain', methods=['POST'])
def explain():
    model_service = get_model_service()

    if not model_service.is_loaded:
        return jsonify({"detail": "Model not loaded"}), 503

    if model_service.explainer is None:
        # Return mock explanations for demo
        contributions = [
            SHAPExplanation(feature_name="pm25", shap_value=45.2, feature_value=120.0, direction="increase"),
            SHAPExplanation(feature_name="wind_speed_ms", shap_value=-12.3, feature_value=2.5, direction="decrease"),
            SHAPExplanation(feature_name="temperature_c", shap_value=8.1, feature_value=38.0, direction="increase"),
            SHAPExplanation(feature_name="humidity_pct", shap_value=-5.4, feature_value=65.0, direction="decrease"),
            SHAPExplanation(feature_name="pm10", shap_value=15.7, feature_value=85.0, direction="increase"),
            SHAPExplanation(feature_name="aqi_lag_1h", shap_value=22.1, feature_value=135.0, direction="increase"),
            SHAPExplanation(feature_name="wind_pm25_interaction", shap_value=-8.9, feature_value=300.0, direction="decrease"),
            SHAPExplanation(feature_name="pollution_intensity", shap_value=11.3, feature_value=78.0, direction="increase"),
        ]
        resp = ExplainResponse(
            prediction_aqi=135.0,
            base_value=100.0,
            contributions=contributions,
            model_type=ModelType.LIGHTGBM,
        )
        return jsonify(resp.model_dump(mode='json'))

    try:
        feature_service = get_feature_service()
        settings = get_settings()

        features_df = feature_service.get_latest_features(1)
        if features_df is not None and not features_df.empty:
            from training_pipeline.train import FEATURE_COLUMNS
            available_cols = [c for c in FEATURE_COLUMNS if c in features_df.columns]
            X = features_df[available_cols].fillna(0.0).values.astype(np.float32)

            explanations = model_service.explainer.explain(X[-1:])
            if explanations:
                prediction = float(model_service.model.predict(X[-1:].reshape(1, -1))[0])
                resp = ExplainResponse(
                    prediction_aqi=round(prediction, 1),
                    base_value=model_service.explainer.base_value,
                    contributions=explanations[0],
                    model_type=ModelType.LIGHTGBM,
                )
                return jsonify(resp.model_dump(mode='json'))
    except Exception as e:
        logger.error("SHAP explanation failed: %s", e)
        return jsonify({"detail": f"Explanation error: {e}"}), 500

    return jsonify({"detail": "Could not generate explanation"}), 500


@app.route('/historical', methods=['GET'])
def get_historical():
    try:
        hours = int(request.args.get("hours", 168))
    except ValueError:
        hours = 168
    
    hours = max(1, min(hours, 8760))

    feature_service = get_feature_service()
    features_df = feature_service.get_latest_features(hours)

    if features_df is None or features_df.empty:
        # Generate synthetic historical data
        from data_pipeline.ingest import SyntheticDataGenerator
        from datetime import timedelta

        generator = SyntheticDataGenerator()
        now = datetime.now(timezone.utc)

        data = []
        for h in range(hours):
            dt = now - timedelta(hours=hours - h)
            payload = generator.generate_for_timestamp(dt)
            data.append({
                "timestamp": dt.isoformat(),
                "aqi": payload.aqi_value,
                "pm25": next((p.value for p in payload.pollutants if p.name == "pm25"), 0),
                "pm10": next((p.value for p in payload.pollutants if p.name == "pm10"), 0),
                "temperature_c": payload.weather.temperature_c,
                "humidity_pct": payload.weather.humidity_pct,
            })

        return jsonify({"data": data, "count": len(data), "source": "synthetic"})

    # Convert timestamps to string if they are not already
    df = features_df.copy()
    if 'timestamp' in df.columns:
        df['timestamp'] = df['timestamp'].astype(str)
    records = df.to_dict(orient="records")
    return jsonify({"data": records, "count": len(records), "source": "feature_store"})
