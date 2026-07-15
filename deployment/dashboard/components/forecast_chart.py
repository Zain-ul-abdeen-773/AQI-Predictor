"""3-day forecast chart component using Plotly.

Renders an interactive minimalist line chart with cubic interpolation,
prediction intervals, and clean typography.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
import streamlit as st

from deployment.dashboard.styles.theme import COLORS, get_aqi_color


def render_forecast_chart(
    predictions: List[Dict[str, Any]],
    historical: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Render a 3-day AQI forecast timeline chart.

    Displays a smooth cubic interpolation line with 80% and 95%
    prediction intervals shown as shaded bands.

    Args:
        predictions: List of hourly prediction dicts with keys:
            timestamp, aqi_predicted, aqi_lower_80, aqi_upper_80,
            aqi_lower_95, aqi_upper_95
        historical: Optional list of historical AQI data points.
    """
    st.markdown('<div class="section-header">3-Day AQI Forecast</div>',
                unsafe_allow_html=True)

    fig = go.Figure()

    timestamps = [p["timestamp"] for p in predictions]
    aqi_values = [p["aqi_predicted"] for p in predictions]

    # ── 95% Prediction Interval (lighter band) ──
    upper_95 = [p.get("aqi_upper_95", p["aqi_predicted"] + 30) for p in predictions]
    lower_95 = [p.get("aqi_lower_95", max(0, p["aqi_predicted"] - 30)) for p in predictions]

    fig.add_trace(go.Scatter(
        x=timestamps + timestamps[::-1],
        y=upper_95 + lower_95[::-1],
        fill="toself",
        fillcolor="rgba(124, 108, 255, 0.06)",
        line=dict(color="rgba(0,0,0,0)"),
        name="95% Interval",
        showlegend=True,
        hoverinfo="skip",
    ))

    # ── 80% Prediction Interval (darker band) ──
    upper_80 = [p.get("aqi_upper_80", p["aqi_predicted"] + 15) for p in predictions]
    lower_80 = [p.get("aqi_lower_80", max(0, p["aqi_predicted"] - 15)) for p in predictions]

    fig.add_trace(go.Scatter(
        x=timestamps + timestamps[::-1],
        y=upper_80 + lower_80[::-1],
        fill="toself",
        fillcolor="rgba(124, 108, 255, 0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="80% Interval",
        showlegend=True,
        hoverinfo="skip",
    ))

    # ── Historical line (if provided) ──
    if historical:
        hist_ts = [h["timestamp"] for h in historical]
        hist_aqi = [h.get("aqi", h.get("aqi_value", 0)) for h in historical]

        fig.add_trace(go.Scatter(
            x=hist_ts,
            y=hist_aqi,
            mode="lines",
            name="Historical",
            line=dict(
                color="rgba(138, 138, 154, 0.5)",
                width=1.5,
                dash="dot",
            ),
            hovertemplate="<b>%{x|%b %d, %H:%M}</b><br>AQI: %{y:.0f}<extra></extra>",
        ))

    # ── Main forecast line ──
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=aqi_values,
        mode="lines",
        name="Forecast",
        line=dict(
            color=COLORS["accent_primary"],
            width=2.5,
            shape="spline",
            smoothing=1.3,
        ),
        hovertemplate=(
            "<b>%{x|%b %d, %H:%M}</b><br>"
            "AQI: <b>%{y:.0f}</b><extra></extra>"
        ),
    ))

    # ── AQI Threshold Lines ──
    threshold_levels = [
        (50, "Good", COLORS["aqi_good"]),
        (100, "Moderate", COLORS["aqi_moderate"]),
        (150, "Unhealthy (SG)", COLORS["aqi_unhealthy_sg"]),
        (200, "Unhealthy", COLORS["aqi_unhealthy"]),
    ]

    for threshold, label, color in threshold_levels:
        max_aqi = max(aqi_values) if aqi_values else 100
        if threshold <= max_aqi * 1.3:
            fig.add_hline(
                y=threshold,
                line=dict(color=f"{color}30", width=1, dash="dot"),
                annotation=dict(
                    text=label,
                    font=dict(size=9, color=f"{color}80"),
                    xanchor="right",
                ),
            )

    # ── Layout (Scandinavian minimalist) ──
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, -apple-system, sans-serif",
            color=COLORS["text_secondary"],
            size=11,
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=360,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color=COLORS["text_muted"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=False,
            tickfont=dict(size=10, color=COLORS["text_muted"]),
            tickformat="%b %d\n%H:%M",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.03)",
            gridwidth=1,
            showline=False,
            zeroline=False,
            tickfont=dict(size=10, color=COLORS["text_muted"]),
            title=None,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=COLORS["card"],
            bordercolor=COLORS["border"],
            font=dict(size=12, color=COLORS["text_primary"]),
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": False,
        "staticPlot": False,
    })
