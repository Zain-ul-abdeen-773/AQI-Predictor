"""Animated AQI gauge component for the Streamlit dashboard.

Renders a prominent circular AQI indicator with smooth color
transitions based on air quality level.
"""

from __future__ import annotations

import streamlit as st

from deployment.dashboard.styles.theme import get_aqi_color, get_aqi_label


def render_aqi_gauge(aqi_value: float) -> None:
    """Render an animated circular AQI gauge.

    Displays a large, prominently styled circle with the current AQI
    value. Color transitions gracefully based on AQI level:
    - Green (Good) → Yellow (Moderate) → Orange → Red → Purple → Maroon

    Args:
        aqi_value: Current AQI numeric value.
    """
    color = get_aqi_color(aqi_value)
    label = get_aqi_label(aqi_value)

    # Glow intensity based on severity
    glow_intensity = min(0.6, aqi_value / 500)
    glow_spread = int(20 + aqi_value * 0.1)

    gauge_html = f"""
    <div class="aqi-gauge-container">
        <div class="aqi-circle" style="
            background: radial-gradient(circle at 30% 30%,
                {color}18 0%,
                {color}08 40%,
                transparent 70%),
                linear-gradient(135deg, #1A1A24 0%, #12121A 100%);
            border: 2px solid {color}40;
            box-shadow:
                0 0 {glow_spread}px {color}{int(glow_intensity * 255):02x},
                inset 0 0 30px {color}10;
            color: {color};
            animation: pulse-glow 3s ease-in-out infinite;
            --glow-color: {color}{int(glow_intensity * 255):02x};
        ">
            <div class="aqi-number" style="color: {color};">
                {int(aqi_value)}
            </div>
            <div class="aqi-label">AQI</div>
        </div>

        <div style="
            margin-top: 20px;
            text-align: center;
        ">
            <div style="
                display: inline-block;
                padding: 6px 20px;
                border-radius: 20px;
                background: {color}15;
                border: 1px solid {color}30;
                color: {color};
                font-size: 0.85rem;
                font-weight: 600;
                letter-spacing: 0.05em;
            ">{label}</div>
        </div>

        <div style="
            margin-top: 12px;
            color: #5A5A6A;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        ">Sargodha, Pakistan</div>
    </div>
    """

    st.markdown(gauge_html, unsafe_allow_html=True)
