"""Regional news feed with sentiment analysis component.

Fetches regional news from Pakistan media RSS feeds, filters by
keywords, and displays a risk assessment indicator.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from deployment.dashboard.styles.theme import COLORS

logger = logging.getLogger(__name__)


def fetch_news(
    rss_feeds: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    max_articles: int = 5,
) -> List[Dict[str, Any]]:
    """Fetch and filter regional news from RSS feeds.

    Args:
        rss_feeds: List of RSS feed URLs.
        keywords: Keywords for filtering relevant articles.
        max_articles: Maximum number of articles to return.

    Returns:
        List of news article dicts.
    """
    from config.settings import get_settings

    settings = get_settings()
    feeds = rss_feeds or settings.news_rss_feeds
    kws = keywords or settings.news_keywords
    kws_lower = [k.lower() for k in kws]

    articles: List[Dict[str, Any]] = []

    try:
        import feedparser

        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:20]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    text = f"{title} {summary}".lower()

                    matched = [kw for kw in kws_lower if kw in text]
                    if matched:
                        articles.append({
                            "title": title,
                            "url": entry.get("link", ""),
                            "source": feed.feed.get("title", "Unknown"),
                            "published": entry.get("published", ""),
                            "matched_keywords": matched,
                        })
            except Exception as e:
                logger.warning("Failed to parse feed %s: %s", feed_url, e)

    except ImportError:
        logger.info("feedparser not installed — using placeholder news")
        articles = _get_placeholder_news()

    return articles[:max_articles]


def _get_placeholder_news() -> List[Dict[str, Any]]:
    """Generate placeholder news for demo mode."""
    return [
        {
            "title": "Sargodha district reports moderate air quality improvement",
            "url": "#",
            "source": "Dawn News",
            "published": datetime.now().strftime("%Y-%m-%d"),
            "matched_keywords": ["sargodha", "air quality"],
        },
        {
            "title": "Punjab government announces new smog reduction measures",
            "url": "#",
            "source": "The Express Tribune",
            "published": datetime.now().strftime("%Y-%m-%d"),
            "matched_keywords": ["smog"],
        },
        {
            "title": "Crop burning season expected to worsen air pollution",
            "url": "#",
            "source": "Geo News",
            "published": datetime.now().strftime("%Y-%m-%d"),
            "matched_keywords": ["crop burning", "pollution"],
        },
    ]


def compute_risk_factor(articles: List[Dict[str, Any]]) -> str:
    """Compute regional industrial/agricultural activity risk factor.

    Based on the number and severity of matched news articles.

    Args:
        articles: Filtered news articles.

    Returns:
        str: Risk level ('Low', 'Moderate', 'High').
    """
    if not articles:
        return "Low"

    high_risk_keywords = {"hazardous", "emergency", "crop burning", "factory emissions", "smog"}
    high_count = sum(
        1 for a in articles
        if any(kw in high_risk_keywords for kw in a.get("matched_keywords", []))
    )

    if high_count >= 2 or len(articles) >= 5:
        return "High"
    elif high_count >= 1 or len(articles) >= 3:
        return "Moderate"
    return "Low"


def render_news_feed() -> None:
    """Render the regional news feed with risk assessment indicator."""
    st.markdown(
        '<div class="section-header">Regional Activity Monitor</div>',
        unsafe_allow_html=True,
    )

    articles = fetch_news()
    risk_level = compute_risk_factor(articles)

    # Risk indicator
    risk_class = f"risk-{risk_level.lower()}"
    risk_icons = {"Low": "🟢", "Moderate": "🟡", "High": "🔴"}
    risk_icon = risk_icons.get(risk_level, "⚪")

    st.markdown(
        f"""
        <div class="metric-card" style="padding: 16px 20px;">
            <div class="metric-label">Industrial / Agricultural Risk Factor</div>
            <div style="display: flex; align-items: center; gap: 12px; margin-top: 8px;">
                <span style="font-size: 1.5rem;">{risk_icon}</span>
                <span class="risk-indicator {risk_class}">{risk_level}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # News cards
    if not articles:
        st.markdown(
            f'<p style="color: {COLORS["text_muted"]}; font-size: 0.85rem;">'
            f'No relevant regional news found</p>',
            unsafe_allow_html=True,
        )
        return

    for article in articles:
        keywords_html = " ".join(
            f'<span style="background: {COLORS["accent_primary"]}20; '
            f'color: {COLORS["accent_primary"]}; padding: 2px 8px; '
            f'border-radius: 10px; font-size: 0.65rem; margin-right: 4px;">'
            f'{kw}</span>'
            for kw in article.get("matched_keywords", [])[:3]
        )

        st.markdown(
            f"""
            <div class="news-card">
                <div style="font-size: 0.85rem; color: {COLORS['text_primary']};
                            font-weight: 500; margin-bottom: 8px;">
                    {article['title']}
                </div>
                <div style="display: flex; justify-content: space-between;
                            align-items: center;">
                    <span style="color: {COLORS['text_muted']}; font-size: 0.7rem;">
                        {article.get('source', '')} • {article.get('published', '')}
                    </span>
                    <div>{keywords_html}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
