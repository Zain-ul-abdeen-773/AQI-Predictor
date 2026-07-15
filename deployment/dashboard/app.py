"""Pearls AQI Predictor — Streamlit Dashboard.

Ultra-minimalist, Scandinavian-inspired dark mode dashboard for
real-time and forecasted AQI visualization in Sargodha, Pakistan.

Features:
- Animated AQI gauge with color-coded severity
- Interactive 3-day forecast timeline (Plotly)
- SHAP feature contribution visualization
- Regional news integration with risk assessment
- Hazardous AQI alerts with health recommendations

Usage:
    streamlit run deployment/dashboard/app.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from deployment.dashboard.styles.theme import COLORS, CUSTOM_CSS, get_aqi_color, get_aqi_label
from deployment.dashboard.components.aqi_gauge import render_aqi_gauge
from deployment.dashboard.components.forecast_chart import render_forecast_chart
from deployment.dashboard.components.shap_chart import render_shap_chart
from deployment.dashboard.components.news_feed import render_news_feed
from deployment.dashboard.components.alerts import render_alerts


# ──────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Pearls AQI Predictor | Sargodha",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Pearls AQI Predictor — 3-day air quality forecasting for Sargodha, Pakistan",
    },
)

# Inject custom theme CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Data Fetching (with caching)
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_predictions() -> Dict[str, Any]:
    """Fetch predictions from the FastAPI backend or generate demo data.

    Returns:
        Dict with forecast data, explanations, and metadata.
    """
    try:
        import requests
        response = requests.get("http://localhost:8000/predict", timeout=5)
        if response.ok:
            return response.json()
    except Exception:
        pass

    # Generate demo predictions
    return _generate_demo_data()


@st.cache_data(ttl=300)
def fetch_explanations() -> List[Dict[str, Any]]:
    """Fetch SHAP explanations from the API or use demo data."""
    try:
        import requests
        response = requests.get("http://localhost:8000/explain", timeout=5)
        if response.ok:
            data = response.json()
            return data.get("contributions", [])
    except Exception:
        pass

    return _generate_demo_explanations()


def _generate_demo_data() -> Dict[str, Any]:
    """Generate realistic demo forecast data."""
    import math
    import random

    now = datetime.now(timezone.utc)
    base_aqi = 95 + random.gauss(0, 20)

    predictions = []
    for h in range(72):
        # Simulate diurnal pattern
        hour_effect = 25 * math.cos(2 * math.pi * ((now.hour + h) % 24 - 8) / 24)
        trend = h * 0.15 * random.choice([1, -1])
        noise = random.gauss(0, 8)
        aqi = max(10, min(400, base_aqi + hour_effect + trend + noise))

        pred_time = now + timedelta(hours=h)
        uncertainty = 10 + h * 0.5

        predictions.append({
            "timestamp": pred_time.isoformat(),
            "aqi_predicted": round(aqi, 1),
            "aqi_lower_80": round(max(0, aqi - uncertainty * 0.8), 1),
            "aqi_upper_80": round(min(500, aqi + uncertainty * 0.8), 1),
            "aqi_lower_95": round(max(0, aqi - uncertainty * 1.5), 1),
            "aqi_upper_95": round(min(500, aqi + uncertainty * 1.5), 1),
            "level": get_aqi_label(aqi),
        })

    # Historical data (past 48 hours)
    historical = []
    for h in range(48, 0, -1):
        hist_time = now - timedelta(hours=h)
        hour_effect = 20 * math.cos(2 * math.pi * (hist_time.hour - 8) / 24)
        aqi = max(10, base_aqi + hour_effect + random.gauss(0, 10))
        historical.append({
            "timestamp": hist_time.isoformat(),
            "aqi": round(aqi, 1),
        })

    return {
        "current_aqi": round(base_aqi, 1),
        "current_level": get_aqi_label(base_aqi),
        "city": "Sargodha",
        "model_type": "lightgbm",
        "hourly_predictions": predictions,
        "historical": historical,
        "summary": "Air quality conditions are currently moderate. Monitor conditions.",
        "alert": any(p["aqi_predicted"] > 150 for p in predictions),
        "generated_at": now.isoformat(),
    }


def _generate_demo_explanations() -> List[Dict[str, Any]]:
    """Generate demo SHAP explanations."""
    return [
        {"feature_name": "pm25", "shap_value": 32.5, "feature_value": 88.3, "direction": "increase"},
        {"feature_name": "wind_speed_ms", "shap_value": -18.2, "feature_value": 3.2, "direction": "decrease"},
        {"feature_name": "aqi_lag_1h", "shap_value": 22.1, "feature_value": 112.0, "direction": "increase"},
        {"feature_name": "temperature_c", "shap_value": 8.7, "feature_value": 36.5, "direction": "increase"},
        {"feature_name": "humidity_pct", "shap_value": -6.3, "feature_value": 58.0, "direction": "decrease"},
        {"feature_name": "pm10", "shap_value": 15.4, "feature_value": 145.0, "direction": "increase"},
        {"feature_name": "pollution_intensity", "shap_value": 11.8, "feature_value": 76.0, "direction": "increase"},
        {"feature_name": "wind_pm25_interaction", "shap_value": -9.1, "feature_value": 282.0, "direction": "decrease"},
        {"feature_name": "pressure_hpa", "shap_value": -4.2, "feature_value": 1008.0, "direction": "decrease"},
        {"feature_name": "thermal_inversion_flag", "shap_value": 7.5, "feature_value": 1.0, "direction": "increase"},
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 16px 0;">
            <div style="font-size: 1.4rem; font-weight: 700; color: {COLORS['text_primary']};
                        letter-spacing: -0.02em;">
                🌬️ Pearls AQI
            </div>
            <div style="font-size: 0.75rem; color: {COLORS['text_muted']};
                        margin-top: 4px; letter-spacing: 0.08em;
                        text-transform: uppercase;">
                Air Quality Predictor
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        f"""
        <div style="font-size: 0.7rem; color: {COLORS['text_muted']};
                    text-transform: uppercase; letter-spacing: 0.12em;
                    margin-bottom: 8px;">
            Location
        </div>
        <div style="color: {COLORS['text_primary']}; font-weight: 500;">
            📍 Sargodha, Punjab, Pakistan
        </div>
        <div style="color: {COLORS['text_muted']}; font-size: 0.75rem;
                    font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
            32.0836°N, 72.6711°E
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True, type="secondary"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # Model info
    st.markdown(
        f"""
        <div style="font-size: 0.7rem; color: {COLORS['text_muted']};
                    text-transform: uppercase; letter-spacing: 0.12em;
                    margin-bottom: 8px;">
            Model Information
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background: {COLORS['card']}; border-radius: 8px;
                    padding: 12px; font-size: 0.75rem;">
            <div style="color: {COLORS['text_muted']};">Architecture</div>
            <div style="color: {COLORS['text_primary']}; font-weight: 500;">
                Ridge · LightGBM · Bi-LSTM
            </div>
            <div style="color: {COLORS['text_muted']}; margin-top: 8px;">Forecast Horizon</div>
            <div style="color: {COLORS['text_primary']}; font-weight: 500;">72 hours (3 days)</div>
            <div style="color: {COLORS['text_muted']}; margin-top: 8px;">Explainability</div>
            <div style="color: {COLORS['text_primary']}; font-weight: 500;">SHAP Values</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    st.markdown(
        f"""
        <div style="font-size: 0.65rem; color: {COLORS['text_muted']}; margin-top: 24px;">
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Main Content
# ──────────────────────────────────────────────────────────────────────────────

# Fetch data
data = fetch_predictions()
explanations = fetch_explanations()

current_aqi = data.get("current_aqi", 85)
predictions = data.get("hourly_predictions", [])
historical = data.get("historical", [])

# ── Alerts (top of page) ──
if predictions:
    render_alerts(predictions, threshold=150)

# ── Top Row: AQI Gauge + Key Metrics ──
col_gauge, col_metrics = st.columns([1, 2], gap="large")

with col_gauge:
    render_aqi_gauge(current_aqi)

with col_metrics:
    # Calculate key stats from predictions
    if predictions:
        aqi_values = [p["aqi_predicted"] for p in predictions]
        max_aqi = max(aqi_values)
        min_aqi = min(aqi_values)
        avg_aqi = sum(aqi_values) / len(aqi_values)

        # Hours above unhealthy threshold
        hours_unhealthy = sum(1 for v in aqi_values if v > 150)
    else:
        max_aqi = min_aqi = avg_aqi = current_aqi
        hours_unhealthy = 0

    st.markdown("")
    st.markdown("")

    # Metric cards row
    mc1, mc2, mc3, mc4 = st.columns(4)

    with mc1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Peak (72h)</div>
                <div class="metric-value" style="color: {get_aqi_color(max_aqi)};">
                    {int(max_aqi)}
                </div>
                <div class="metric-delta" style="color: {COLORS['text_muted']};">
                    {get_aqi_label(max_aqi)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with mc2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Low (72h)</div>
                <div class="metric-value" style="color: {get_aqi_color(min_aqi)};">
                    {int(min_aqi)}
                </div>
                <div class="metric-delta" style="color: {COLORS['text_muted']};">
                    {get_aqi_label(min_aqi)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with mc3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Average</div>
                <div class="metric-value" style="color: {get_aqi_color(avg_aqi)};">
                    {int(avg_aqi)}
                </div>
                <div class="metric-delta" style="color: {COLORS['text_muted']};">
                    3-day mean
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with mc4:
        uh_color = COLORS["aqi_unhealthy"] if hours_unhealthy > 0 else COLORS["aqi_good"]
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Unhealthy Hours</div>
                <div class="metric-value" style="color: {uh_color};">
                    {hours_unhealthy}
                </div>
                <div class="metric-delta" style="color: {COLORS['text_muted']};">
                    AQI &gt; 150
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Forecast Chart ──
st.markdown("")
render_forecast_chart(predictions, historical)

# ── Bottom Row: SHAP + News ──
st.markdown("")
col_shap, col_news = st.columns([3, 2], gap="large")

with col_shap:
    render_shap_chart(explanations)

with col_news:
    render_news_feed()

# ── Footer ──
st.markdown(
    f"""
    <div style="text-align: center; padding: 32px 0 16px;
                color: {COLORS['text_muted']}; font-size: 0.65rem;
                border-top: 1px solid {COLORS['border']};
                margin-top: 32px;">
        Pearls AQI Predictor v1.0 — Built for Sargodha, Pakistan
        <br>
        Multi-model ML Pipeline: Ridge · LightGBM · Bi-LSTM + Attention
        <br>
        Explainability: SHAP · Data Source: AQICN + OpenWeatherMap
    </div>
    """,
    unsafe_allow_html=True,
)
