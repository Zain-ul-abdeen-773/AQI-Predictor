"""SHAP feature contribution chart component.

Renders a clean horizontal bar chart showing how each feature
contributed to the current AQI prediction.
"""

from __future__ import annotations

from typing import Any, Dict, List

import plotly.graph_objects as go
import streamlit as st

from deployment.dashboard.styles.theme import COLORS


def render_shap_chart(contributions: List[Dict[str, Any]]) -> None:
    """Render SHAP feature contribution horizontal bar chart.

    Displays a clean horizontal bar chart where:
    - Positive SHAP values (increasing AQI) shown in red/orange
    - Negative SHAP values (decreasing AQI) shown in green/teal

    Args:
        contributions: List of contribution dicts with keys:
            feature_name, shap_value, feature_value, direction
    """
    st.markdown(
        '<div class="section-header">Feature Contributions (SHAP)</div>',
        unsafe_allow_html=True,
    )

    if not contributions:
        st.markdown(
            '<p style="color: #5A5A6A; font-size: 0.85rem;">'
            'No explanation data available</p>',
            unsafe_allow_html=True,
        )
        return

    # Sort by absolute SHAP value (most impactful first)
    sorted_contrib = sorted(
        contributions,
        key=lambda x: abs(x.get("shap_value", 0)),
    )

    # Take top 12 features
    sorted_contrib = sorted_contrib[-12:]

    names = [c["feature_name"].replace("_", " ").title() for c in sorted_contrib]
    values = [c["shap_value"] for c in sorted_contrib]
    feature_vals = [c.get("feature_value", 0) for c in sorted_contrib]

    # Color based on direction
    colors = [
        COLORS["aqi_unhealthy"] if v > 0 else COLORS["aqi_good"]
        for v in values
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=names,
        x=values,
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=0),
            cornerradius=4,
        ),
        text=[
            f" {v:+.1f}" for v in values
        ],
        textposition="outside",
        textfont=dict(
            size=10,
            color=COLORS["text_secondary"],
            family="JetBrains Mono, monospace",
        ),
        customdata=feature_vals,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "SHAP Value: %{x:+.2f}<br>"
            "Feature Value: %{customdata:.2f}"
            "<extra></extra>"
        ),
    ))

    # Add zero line
    fig.add_vline(
        x=0,
        line=dict(color=COLORS["border"], width=1),
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, -apple-system, sans-serif",
            color=COLORS["text_secondary"],
            size=11,
        ),
        margin=dict(l=0, r=60, t=10, b=0),
        height=max(300, len(names) * 36),
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.03)",
            showline=False,
            zeroline=False,
            tickfont=dict(size=9, color=COLORS["text_muted"]),
            title=None,
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(size=10, color=COLORS["text_secondary"]),
        ),
        hoverlabel=dict(
            bgcolor=COLORS["card"],
            bordercolor=COLORS["border"],
            font=dict(size=11, color=COLORS["text_primary"]),
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": False,
    })

    # Legend annotation
    st.markdown(
        f"""
        <div style="display: flex; gap: 24px; justify-content: center;
                    padding: 8px 0; font-size: 0.7rem; color: {COLORS['text_muted']};">
            <span>
                <span style="display: inline-block; width: 10px; height: 10px;
                             border-radius: 2px; background: {COLORS['aqi_unhealthy']};
                             margin-right: 6px;"></span>
                Increases AQI (↑ pollution)
            </span>
            <span>
                <span style="display: inline-block; width: 10px; height: 10px;
                             border-radius: 2px; background: {COLORS['aqi_good']};
                             margin-right: 6px;"></span>
                Decreases AQI (↓ pollution)
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
