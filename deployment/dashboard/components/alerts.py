"""AQI hazardous level alert component.

Displays soft modal alerts when forecast AQI exceeds critical thresholds,
with health advice and municipal action recommendations.
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from deployment.dashboard.styles.theme import COLORS, get_aqi_color, get_aqi_label


def render_alerts(
    predictions: List[Dict[str, Any]],
    threshold: int = 150,
) -> None:
    """Render alert banners when forecast AQI exceeds thresholds.

    Displays health advice and recommended actions based on
    the severity of predicted air quality levels.

    Args:
        predictions: List of hourly prediction dicts.
        threshold: AQI value threshold for triggering alerts.
    """
    # Find max predicted AQI
    max_pred = max(
        (p.get("aqi_predicted", 0) for p in predictions),
        default=0,
    )

    if max_pred <= threshold:
        return

    # Find when it first exceeds threshold
    exceeding = [
        p for p in predictions
        if p.get("aqi_predicted", 0) > threshold
    ]

    if not exceeding:
        return

    first_exceed = exceeding[0]
    max_val = max(p.get("aqi_predicted", 0) for p in exceeding)
    hours_exceeding = len(exceeding)
    color = get_aqi_color(max_val)
    level = get_aqi_label(max_val)

    # Severity-based content
    if max_val > 300:
        icon = "🚨"
        severity = "EMERGENCY"
        banner_class = ""
        health_advice = [
            "Stay indoors with windows and doors sealed",
            "Use N95/KN95 masks if you must go outside",
            "Run air purifiers on maximum setting",
            "Avoid all strenuous physical activity",
            "Seek medical help if experiencing breathing difficulty",
            "Keep emergency medications accessible",
        ]
        municipal_actions = [
            "Issue public health emergency advisory",
            "Activate emergency air quality protocols",
            "Suspend outdoor construction activities",
            "Deploy water sprinklers on major roads",
            "Provide free N95 masks at public health centers",
        ]
    elif max_val > 200:
        icon = "⚠️"
        severity = "HEALTH ALERT"
        banner_class = ""
        health_advice = [
            "Limit outdoor activities significantly",
            "Wear N95 masks when going outdoors",
            "Keep windows closed and use air purifiers",
            "Sensitive groups should stay indoors",
            "Stay hydrated and monitor health symptoms",
        ]
        municipal_actions = [
            "Issue air quality health advisory",
            "Restrict heavy vehicle traffic in city center",
            "Monitor industrial emission compliance",
            "Increase road water spraying frequency",
        ]
    else:
        icon = "⚡"
        severity = "AIR QUALITY ADVISORY"
        banner_class = "warning"
        health_advice = [
            "Sensitive groups should reduce outdoor exertion",
            "Consider wearing masks during peak hours",
            "Keep windows closed during morning and evening",
            "Monitor AQI updates regularly",
        ]
        municipal_actions = [
            "Increase monitoring frequency",
            "Alert hospitals and clinics",
            "Review local emission sources",
        ]

    # Alert banner
    st.markdown(
        f"""
        <div class="alert-banner {banner_class}">
            <span style="font-size: 1.5rem;">{icon}</span>
            <div>
                <div style="font-weight: 700; color: {color};
                            font-size: 0.85rem; letter-spacing: 0.08em;">
                    {severity}
                </div>
                <div style="color: {COLORS['text_secondary']}; font-size: 0.8rem;
                            margin-top: 4px;">
                    AQI forecast to reach <b style="color: {color};">{int(max_val)}</b>
                    ({level}) for {hours_exceeding} hours in the next 3 days.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Expandable health advice
    with st.expander(f"{icon} Health Recommendations", expanded=max_val > 200):
        for advice in health_advice:
            st.markdown(
                f"""<div style="color: {COLORS['text_secondary']};
                    font-size: 0.8rem; padding: 4px 0 4px 16px;
                    border-left: 2px solid {color}30;">
                    {advice}
                </div>""",
                unsafe_allow_html=True,
            )

    # Expandable municipal actions
    with st.expander("🏛️ Recommended Municipal Actions"):
        for action in municipal_actions:
            st.markdown(
                f"""<div style="color: {COLORS['text_secondary']};
                    font-size: 0.8rem; padding: 4px 0 4px 16px;
                    border-left: 2px solid {COLORS['accent_primary']}30;">
                    {action}
                </div>""",
                unsafe_allow_html=True,
            )
