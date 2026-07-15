"""Scandinavian-minimalist dark mode theme configuration for Streamlit.

Defines the complete visual design system including colors, typography,
spacing, and custom CSS for the AQI prediction dashboard.
"""

from __future__ import annotations

from typing import Dict


# ──────────────────────────────────────────────────────────────────────────────
# Color Palette
# ──────────────────────────────────────────────────────────────────────────────

COLORS: Dict[str, str] = {
    # Base
    "background": "#0A0A0F",
    "surface": "#12121A",
    "card": "#1A1A24",
    "sidebar": "#0F0F16",
    "border": "#2A2A36",

    # Typography
    "text_primary": "#E8E8EC",
    "text_secondary": "#8A8A9A",
    "text_muted": "#5A5A6A",

    # Accent
    "accent_primary": "#7C6CFF",
    "accent_secondary": "#5B4DD4",
    "accent_glow": "rgba(124, 108, 255, 0.15)",

    # AQI Status Colors
    "aqi_good": "#34D399",
    "aqi_moderate": "#FBBF24",
    "aqi_unhealthy_sg": "#FB923C",
    "aqi_unhealthy": "#EF4444",
    "aqi_very_unhealthy": "#A855F7",
    "aqi_hazardous": "#991B1B",

    # Utility
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#EF4444",
    "info": "#60A5FA",
}

# ──────────────────────────────────────────────────────────────────────────────
# AQI Color Mapping
# ──────────────────────────────────────────────────────────────────────────────


def get_aqi_color(value: float) -> str:
    """Get the appropriate color for an AQI value.

    Args:
        value: AQI numeric value.

    Returns:
        str: Hex color code.
    """
    if value <= 50:
        return COLORS["aqi_good"]
    elif value <= 100:
        return COLORS["aqi_moderate"]
    elif value <= 150:
        return COLORS["aqi_unhealthy_sg"]
    elif value <= 200:
        return COLORS["aqi_unhealthy"]
    elif value <= 300:
        return COLORS["aqi_very_unhealthy"]
    else:
        return COLORS["aqi_hazardous"]


def get_aqi_label(value: float) -> str:
    """Get the human-readable AQI category label.

    Args:
        value: AQI numeric value.

    Returns:
        str: Category label.
    """
    if value <= 50:
        return "Good"
    elif value <= 100:
        return "Moderate"
    elif value <= 150:
        return "Unhealthy (Sensitive)"
    elif value <= 200:
        return "Unhealthy"
    elif value <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
    /* ── Global Overrides ────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0A0A0F 0%, #0D0D14 50%, #0A0A0F 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* ── Sidebar ─────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F0F16 0%, #0A0A10 100%);
        border-right: 1px solid rgba(124, 108, 255, 0.08);
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #E8E8EC !important;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .stMarkdown p {
        color: #8A8A9A;
    }

    /* ── Cards ────────────────────────────────────────────────── */
    .metric-card {
        background: linear-gradient(135deg, #1A1A24 0%, #16161E 100%);
        border: 1px solid rgba(124, 108, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .metric-card:hover {
        border-color: rgba(124, 108, 255, 0.3);
        box-shadow: 0 8px 32px rgba(124, 108, 255, 0.08);
        transform: translateY(-2px);
    }

    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1;
        margin: 8px 0;
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #8A8A9A;
    }

    .metric-delta {
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 4px;
    }

    /* ── AQI Gauge ────────────────────────────────────────────── */
    .aqi-gauge-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 32px;
    }

    .aqi-circle {
        width: 220px;
        height: 220px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
        transition: all 0.5s ease;
    }

    .aqi-circle::before {
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 50%;
        padding: 4px;
        background: conic-gradient(from 0deg, currentColor, transparent);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        opacity: 0.4;
        animation: rotate 8s linear infinite;
    }

    @keyframes rotate {
        to { transform: rotate(360deg); }
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px var(--glow-color, rgba(124, 108, 255, 0.2)); }
        50% { box-shadow: 0 0 40px var(--glow-color, rgba(124, 108, 255, 0.4)); }
    }

    .aqi-number {
        font-size: 4.5rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1;
    }

    .aqi-label {
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-top: 8px;
        color: #8A8A9A;
    }

    /* ── Section Headers ─────────────────────────────────────── */
    .section-header {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #5A5A6A;
        padding: 16px 0 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        margin-bottom: 16px;
    }

    /* ── Alert Banner ────────────────────────────────────────── */
    .alert-banner {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(239, 68, 68, 0.06) 100%);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 16px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .alert-banner.warning {
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.12) 0%, rgba(251, 191, 36, 0.06) 100%);
        border-color: rgba(251, 191, 36, 0.25);
    }

    /* ── Plotly Chart Overrides ───────────────────────────────── */
    .js-plotly-plot .plotly .bg {
        fill: transparent !important;
    }

    /* ── News Card ────────────────────────────────────────────── */
    .news-card {
        background: rgba(26, 26, 36, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        backdrop-filter: blur(8px);
    }

    .risk-indicator {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .risk-low {
        background: rgba(52, 211, 153, 0.15);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.2);
    }

    .risk-moderate {
        background: rgba(251, 191, 36, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(251, 191, 36, 0.2);
    }

    .risk-high {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }

    /* ── Streamlit Widget Overrides ───────────────────────────── */
    .stSelectbox label, .stSlider label, .stRadio label {
        color: #8A8A9A !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    div[data-testid="stMetricValue"] {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        color: #8A8A9A;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #7C6CFF;
    }

    /* ── Scrollbar ────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(124, 108, 255, 0.2);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(124, 108, 255, 0.4);
    }
</style>
"""
