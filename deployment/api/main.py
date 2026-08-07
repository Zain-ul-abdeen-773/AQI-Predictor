"""Flask API service for AQI prediction and explainability.

Endpoints:
- GET  /health      - Liveness and readiness check
- POST /predict     - 3-day AQI forecast with uncertainty estimates
- POST /explain     - SHAP feature contributions for predictions
- GET  /historical  - Historical AQI data (paginated)
- GET  /models      - Model zoo listing
- POST /simulate    - Counterfactual policy simulation
- GET  /satellite/sentinel5p - Simulated satellite grid data
- GET  /shadow/metrics       - Shadow model comparison

Usage:
    gunicorn deployment.api.main:app --bind 0.0.0.0:$PORT --workers 2
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime, timedelta

import numpy as np
from flask import Flask, jsonify, request
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

# --- App Initialization ---
app = Flask(__name__)

# CORS: restrict to known origins in production, allow all in dev
_allowed_origins = os.environ.get("CORS_ORIGINS", "").split(",")
if _allowed_origins == [""]:
    # Default: allow the known frontend domains
    _allowed_origins = [
        "https://aqi-predictor-3cawg37a4-giki.vercel.app",
        "https://aqi-predictor*.vercel.app",
        "http://localhost:3000",
    ]
CORS(app, resources={r"/*": {"origins": _allowed_origins}})


# --- Middleware ---
@app.before_request
def before_request():
    request.start_time = time.time()


@app.after_request
def after_request(response):
    if hasattr(request, "start_time"):
        duration = time.time() - request.start_time
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        logger.info(
            "%s %s -> %d (%.3fs)",
            request.method,
            request.path,
            response.status_code,
            duration,
        )
    return response


# --- Error Handling (never expose internals) ---
@app.errorhandler(404)
def not_found_handler(exc):
    return jsonify(
        {
            "error": "Not Found",
            "message": "The requested resource does not exist.",
        }
    ), 404


@app.errorhandler(Exception)
def global_exception_handler(exc: Exception):
    # Let registered HTTP error handlers take precedence
    from werkzeug.exceptions import HTTPException

    if isinstance(exc, HTTPException):
        return jsonify(
            {
                "error": exc.name,
                "message": exc.description,
            }
        ), exc.code

    logger.error("Unhandled exception on %s: %s", request.path, exc, exc_info=True)
    return jsonify(
        {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Check server logs for details.",
        }
    ), 500


@app.errorhandler(422)
def validation_error_handler(exc):
    return jsonify(
        {
            "error": "Validation Error",
            "message": "Invalid request parameters.",
        }
    ), 422


@app.errorhandler(400)
def bad_request_handler(exc):
    return jsonify(
        {
            "error": "Bad Request",
            "message": "Malformed request body or parameters.",
        }
    ), 400


# --- Helper Functions ---
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
        AQILevel.UNHEALTHY_SENSITIVE: "Members of sensitive groups should limit prolonged outdoor exertion.",
        AQILevel.UNHEALTHY: "Everyone may experience health effects. Sensitive groups should avoid outdoor activities.",
        AQILevel.VERY_UNHEALTHY: "Health alert: Significant risk for entire population. Avoid outdoor activities.",
        AQILevel.HAZARDOUS: "Emergency conditions. Stay indoors. Seek medical attention if experiencing symptoms.",
    }
    return advisories.get(level, "Monitor air quality conditions.")


def _validate_numeric(value, field_name: str, min_val: float, max_val: float) -> float:
    """Validate and clamp a numeric input field."""
    if value is None:
        return 0.0
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number, got: {type(value).__name__}")
    return max(min_val, min(max_val, num))


def _impute_features(df, feature_columns: list) -> np.ndarray:
    """Prepare feature matrix using forward-fill then median imputation.

    Avoids the problematic fillna(0) pattern where 0 could be
    a meaningful value (e.g., zero pollution is valid but rare).
    """
    available_cols = [c for c in feature_columns if c in df.columns]
    subset = df[available_cols].copy()

    # Forward-fill temporal gaps, then fill remaining with column median
    subset = subset.ffill()
    col_medians = subset.median()
    subset = subset.fillna(col_medians)

    # Final safety net: if entire column was NaN, use 0
    subset = subset.fillna(0.0)

    return subset.values.astype(np.float32), available_cols


# --- Endpoints ---


@app.route("/models", methods=["GET"])
def list_models():
    """Get all 8 models in the Model Zoo with evaluation metrics."""
    model_service = get_model_service()
    if not model_service.is_loaded:
        model_service.load()
    return jsonify(
        {
            "models": model_service.get_all_models_list(),
            "default_model_id": model_service.default_model_id,
        }
    )


@app.route("/health", methods=["GET"])
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


@app.route("/predict", methods=["POST"])
def predict():
    model_id = request.args.get("model_id")
    settings = get_settings()
    model_service = get_model_service()
    feature_service = get_feature_service()

    if not model_service.is_loaded:
        model_service.load()

    if not model_service.is_loaded:
        return jsonify({"error": "Service Unavailable", "message": "Model not loaded."}), 503

    features_df = feature_service.get_latest_features(n_hours=settings.lookback_window_hours)

    if features_df is None or features_df.empty:
        # Generate synthetic features for demo/CI mode
        import pandas as pd

        from training_pipeline.train import FEATURE_COLUMNS as _FC

        rng = np.random.default_rng(42)
        n = settings.lookback_window_hours
        features_df = pd.DataFrame({col: rng.normal(50, 20, n).astype(np.float32) for col in _FC})

    from training_pipeline.train import FEATURE_COLUMNS

    X, used_cols = _impute_features(features_df, FEATURE_COLUMNS)

    if len(used_cols) < len(FEATURE_COLUMNS) * 0.5:
        logger.warning(
            "Feature mismatch: using %d/%d columns. Missing: %s",
            len(used_cols),
            len(FEATURE_COLUMNS),
            [c for c in FEATURE_COLUMNS if c not in features_df.columns][:5],
        )

    try:
        model = model_service.get_model(model_id)
        selected_meta = model_service.get_model_metadata(model_id)

        if hasattr(model, "pipeline") or (
            hasattr(model, "model") and hasattr(model.model, "predict")
        ):
            # Tree/linear model: single-step prediction, propagate forward
            current_pred = float(model.predict(X[-1:].reshape(1, -1))[0])
            # Deterministic decay toward mean (no random noise)
            long_term_mean = float(np.mean(X[-24:, 0])) if X.shape[0] >= 24 else current_pred
            predictions = np.array(
                [
                    current_pred + (long_term_mean - current_pred) * (1 - np.exp(-h / 36.0))
                    for h in range(settings.forecast_horizon_hours)
                ]
            )
        else:
            # Sequence model (Bi-LSTM)
            seq_len = min(settings.lookback_window_hours, X.shape[0])
            X_seq = X[-seq_len:].reshape(1, seq_len, X.shape[1])
            if hasattr(model, "predict_with_attention"):
                predictions, _ = model.predict_with_attention(X_seq)
                predictions = predictions.flatten()
            else:
                predictions = model.predict(X_seq).flatten()

        predictions = np.clip(predictions, 0, 500)
    except Exception as e:
        logger.error("Prediction failed for model_id=%s: %s", model_id, e)
        return jsonify({"error": "Prediction Error", "message": "Model inference failed."}), 500

    # Build response
    now = datetime.now(UTC)
    current_aqi = float(predictions[0])
    current_level = classify_aqi(current_aqi)

    hourly_predictions = []
    for h, pred_val in enumerate(predictions):
        pred_val = float(pred_val)
        pred_time = now + timedelta(hours=h)

        # Uncertainty grows with forecast horizon (heuristic estimate, not a statistical CI)
        spread = 8.0 + h * 0.6
        hourly_predictions.append(
            HourlyPrediction(
                timestamp=pred_time,
                aqi_predicted=round(pred_val, 1),
                aqi_lower_80=round(max(0, pred_val - spread * 0.8), 1),
                aqi_upper_80=round(min(500, pred_val + spread * 0.8), 1),
                aqi_lower_95=round(max(0, pred_val - spread * 1.6), 1),
                aqi_upper_95=round(min(500, pred_val + spread * 1.6), 1),
                level=classify_aqi(pred_val),
            )
        )

    alert = any(p.aqi_predicted > settings.aqi_alert_threshold for p in hourly_predictions)

    try:
        model_type = ModelType(selected_meta.get("id", "ridge"))
    except ValueError:
        model_type = ModelType.RIDGE

    summary = generate_health_advisory(classify_aqi(float(np.mean(predictions))))

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
    return jsonify(response.model_dump(mode="json"))


@app.route("/explain", methods=["POST"])
def explain():
    model_service = get_model_service()

    if not model_service.is_loaded:
        return jsonify({"error": "Service Unavailable", "message": "Model not loaded."}), 503

    if model_service.explainer is None:
        # Demo explanations when no live explainer is available
        contributions = [
            SHAPExplanation(
                feature_name="pm25", shap_value=45.2, feature_value=120.0, direction="increase"
            ),
            SHAPExplanation(
                feature_name="wind_speed_ms",
                shap_value=-12.3,
                feature_value=2.5,
                direction="decrease",
            ),
            SHAPExplanation(
                feature_name="temperature_c",
                shap_value=8.1,
                feature_value=38.0,
                direction="increase",
            ),
            SHAPExplanation(
                feature_name="humidity_pct",
                shap_value=-5.4,
                feature_value=65.0,
                direction="decrease",
            ),
            SHAPExplanation(
                feature_name="pm10", shap_value=15.7, feature_value=85.0, direction="increase"
            ),
            SHAPExplanation(
                feature_name="aqi_lag_1h",
                shap_value=22.1,
                feature_value=135.0,
                direction="increase",
            ),
            SHAPExplanation(
                feature_name="wind_pm25_interaction",
                shap_value=-8.9,
                feature_value=300.0,
                direction="decrease",
            ),
            SHAPExplanation(
                feature_name="pollution_intensity",
                shap_value=11.3,
                feature_value=78.0,
                direction="increase",
            ),
        ]
        resp = ExplainResponse(
            prediction_aqi=135.0,
            base_value=100.0,
            contributions=contributions,
            model_type=ModelType.LIGHTGBM,
        )
        result = resp.model_dump(mode="json")
        result["source"] = "demo"
        return jsonify(result)

    try:
        feature_service = get_feature_service()
        features_df = feature_service.get_latest_features(1)
        if features_df is not None and not features_df.empty:
            from training_pipeline.train import FEATURE_COLUMNS

            X, _ = _impute_features(features_df, FEATURE_COLUMNS)

            explanations = model_service.explainer.explain(X[-1:])
            if explanations:
                prediction = float(model_service.model.predict(X[-1:].reshape(1, -1))[0])
                resp = ExplainResponse(
                    prediction_aqi=round(prediction, 1),
                    base_value=model_service.explainer.base_value,
                    contributions=explanations[0],
                    model_type=ModelType.LIGHTGBM,
                )
                result = resp.model_dump(mode="json")
                result["source"] = "live"
                return jsonify(result)
    except Exception as e:
        logger.error("SHAP explanation failed: %s", e)

    return jsonify(
        {"error": "Explanation Error", "message": "Could not generate explanation."}
    ), 500


@app.route("/historical", methods=["GET"])
def get_historical():
    """Return historical feature data with pagination."""
    try:
        hours = int(request.args.get("hours", 168))
    except (ValueError, TypeError):
        hours = 168

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    page_size = 200
    hours = max(1, min(hours, 2160))  # Cap at 90 days

    feature_service = get_feature_service()
    features_df = feature_service.get_latest_features(hours)

    if features_df is None or features_df.empty:
        return jsonify({"data": [], "count": 0, "page": page, "total_pages": 0})

    total_rows = len(features_df)
    total_pages = (total_rows + page_size - 1) // page_size

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    df = features_df.iloc[start_idx:end_idx].copy()
    if "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"].astype(str)

    records = df.to_dict(orient="records")
    return jsonify(
        {
            "data": records,
            "count": len(records),
            "total_count": total_rows,
            "page": page,
            "total_pages": total_pages,
            "source": "feature_store",
        }
    )


@app.route("/explain/lime", methods=["POST", "GET"])
def explain_lime():
    """Return LIME local feature importance for the latest observation."""
    LIME_FALLBACK = [
        {
            "feature_name": "aqi_lag_1h",
            "feature_description": "aqi_lag_1h > 80.0",
            "weight": 38.4,
            "feature_value": 88.0,
            "direction": "increase",
        },
        {
            "feature_name": "pm25_rolling_mean_24h",
            "feature_description": "pm25_rolling_mean_24h > 65.0",
            "weight": 29.7,
            "feature_value": 72.3,
            "direction": "increase",
        },
        {
            "feature_name": "temperature_c",
            "feature_description": "temperature_c > 32.0",
            "weight": 14.2,
            "feature_value": 36.1,
            "direction": "increase",
        },
        {
            "feature_name": "humidity_pct",
            "feature_description": "humidity_pct > 60.0",
            "weight": 11.5,
            "feature_value": 67.8,
            "direction": "increase",
        },
        {
            "feature_name": "wind_speed_ms",
            "feature_description": "wind_speed_ms <= 4.0",
            "weight": -18.3,
            "feature_value": 3.2,
            "direction": "decrease",
        },
        {
            "feature_name": "pbl_height_m",
            "feature_description": "pbl_height_m <= 800.0",
            "weight": -22.6,
            "feature_value": 620.0,
            "direction": "decrease",
        },
        {
            "feature_name": "solar_radiation_wm2",
            "feature_description": "solar_radiation_wm2 <= 400.0",
            "weight": -9.1,
            "feature_value": 280.0,
            "direction": "decrease",
        },
        {
            "feature_name": "aqi_change_rate_6h",
            "feature_description": "aqi_change_rate_6h > 2.0",
            "weight": 8.6,
            "feature_value": 3.4,
            "direction": "increase",
        },
    ]

    try:
        model_service = get_model_service()
        feature_service = get_feature_service()
        features_df = feature_service.get_latest_features(50)

        if not model_service.is_loaded:
            model_service.load()

        if features_df is not None and not features_df.empty:
            from training_pipeline.explainability import LIMEExplainer
            from training_pipeline.train import FEATURE_COLUMNS

            X, available_cols = _impute_features(features_df, FEATURE_COLUMNS)
            lime_exp = LIMEExplainer(
                model=model_service.model,
                training_data=X,
                feature_names=available_cols,
                num_features=10,
            )
            result = lime_exp.explain_instance(X[-1], num_samples=500)

            if not result.get("contributions"):
                raise ValueError(result.get("error", "Empty contributions from LIME"))

            return jsonify(
                {
                    "predicted_value": result["predicted_value"],
                    "local_r2": result["local_r2"],
                    "intercept": result["intercept"],
                    "contributions": result["contributions"],
                    "source": "live",
                }
            )
    except Exception as e:
        logger.warning("LIME explanation failed, returning demo data: %s", e)

    return jsonify(
        {
            "predicted_value": 88.0,
            "local_r2": 0.91,
            "intercept": 42.0,
            "contributions": LIME_FALLBACK,
            "source": "demo",
        }
    )


@app.route("/simulate", methods=["POST"])
def simulate_causal_policy():
    """Counterfactual policy simulation using environmental physics heuristics.

    Note: This uses simplified causal elasticity estimates, not a trained causal model.
    Results are illustrative of directional impacts, not precise forecasts.
    """
    payload = request.get_json(silent=True) or {}

    try:
        traffic_reduction = _validate_numeric(
            payload.get("traffic_reduction_pct"), "traffic_reduction_pct", 0.0, 100.0
        )
        crop_burning_increase = _validate_numeric(
            payload.get("crop_burning_increase_pct"), "crop_burning_increase_pct", 0.0, 200.0
        )
        wind_speed_delta = _validate_numeric(
            payload.get("wind_speed_delta_ms"), "wind_speed_delta_ms", -10.0, 20.0
        )
    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 422

    # Base predicted baseline (88 AQI base curve)
    base_curve = [round(88 + np.sin(i / 5.5) * 16, 1) for i in range(72)]

    # Simplified causal elasticities:
    # Traffic reduction lowers NO2/PM2.5 (~0.35 AQI per % cut)
    traffic_effect = -0.35 * (traffic_reduction / 100.0) * 45.0
    # Crop burning elevates PM2.5 (~0.55 AQI per % increase)
    biomass_effect = 0.55 * (crop_burning_increase / 100.0) * 60.0
    # Wind dispersion: C = C0 / (1 + 0.12 * delta_v)
    wind_dispersion_factor = 1.0 / (1.0 + max(-0.8, 0.12 * wind_speed_delta))

    simulated_curve = []
    for val in base_curve:
        modified = (val + traffic_effect + biomass_effect) * wind_dispersion_factor
        simulated_curve.append(round(float(np.clip(modified, 15.0, 500.0)), 1))

    mean_baseline = float(np.mean(base_curve))
    mean_simulated = float(np.mean(simulated_curve))
    net_delta = round(mean_simulated - mean_baseline, 1)

    if net_delta < -10:
        recommendation = "Significant atmospheric improvement expected from this intervention."
    elif net_delta > 10:
        recommendation = "Hazardous pollution buildup predicted from these conditions."
    else:
        recommendation = "Impacts remain within baseline tolerance limits."

    return jsonify(
        {
            "status": "success",
            "methodology": "heuristic_causal_elasticity",
            "parameters": {
                "traffic_reduction_pct": traffic_reduction,
                "crop_burning_increase_pct": crop_burning_increase,
                "wind_speed_delta_ms": wind_speed_delta,
            },
            "baseline_mean_aqi": round(mean_baseline, 1),
            "simulated_mean_aqi": round(mean_simulated, 1),
            "net_aqi_change": net_delta,
            "baseline_curve": base_curve,
            "simulated_curve": simulated_curve,
            "policy_recommendation": recommendation,
        }
    )


@app.route("/satellite/sentinel5p", methods=["GET"])
def get_satellite_earth_observation():
    """Simulated Sentinel-5P TROPOMI atmospheric column data grid for Sargodha basin.

    NOTE: This returns modeled/synthetic spatial data based on regional baselines,
    not live satellite feeds. For actual Sentinel-5P data, see Copernicus Open Access Hub.
    """
    grid_points = []
    center_lat, center_lon = 32.0836, 72.6711

    # Use a local RNG to avoid contaminating the global numpy state
    rng = np.random.default_rng(seed=42)

    for i in range(-2, 3):
        for j in range(-2, 3):
            lat = round(center_lat + i * 0.08, 4)
            lon = round(center_lon + j * 0.08, 4)
            dist = np.sqrt(i**2 + j**2)

            no2 = round(14.5 + (3 - dist) * 4.2 + rng.normal(0, 0.8), 2)
            aod = round(0.42 + (3 - dist) * 0.12 + rng.normal(0, 0.03), 3)
            u_wind = round(2.5 + rng.normal(0, 0.3), 2)
            v_wind = round(-1.2 + rng.normal(0, 0.3), 2)

            grid_points.append(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "no2_column_density": max(5.0, no2),
                    "aerosol_optical_depth": max(0.1, aod),
                    "wind_u_component": u_wind,
                    "wind_v_component": v_wind,
                    "aqi_proxy": int(np.clip(no2 * 5.2 + aod * 60, 30, 350)),
                }
            )

    return jsonify(
        {
            "satellite": "Copernicus Sentinel-5P TROPOMI",
            "sensor": "OFFL NO2 / AER_AI",
            "data_source": "simulated_regional_baseline",
            "target_region": "Sargodha Basin, Punjab, Pakistan",
            "center_coordinates": {"latitude": center_lat, "longitude": center_lon},
            "observation_time": datetime.now(UTC).isoformat(),
            "grid_resolution": "0.08 deg (~8.8 km)",
            "grid_points": grid_points,
        }
    )


@app.route("/shadow/metrics", methods=["GET"])
def get_shadow_model_metrics():
    """Shadow model canary metrics for champion vs challenger comparison."""
    from deployment.api.shadow_logger import get_shadow_logger

    shadow_logger = get_shadow_logger()
    metrics = shadow_logger.get_metrics_summary()
    metrics["data_source"] = "in_memory_shadow_log"
    return jsonify(metrics)
