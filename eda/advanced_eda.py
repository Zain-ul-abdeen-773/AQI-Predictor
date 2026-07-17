"""
Advanced Exploratory Data Analysis (EDA) - Part 2
==================================================
Extends the base EDA with advanced statistical analyses:
- Autocorrelation (ACF/PACF) for time-series modeling guidance
- Granger causality tests (weather → AQI)
- Hypothesis testing (seasonal differences, weekend effects)
- Pollution wind rose analysis
- Pair plots with kernel density
- Lag-correlation heatmap
- Hourly heatmap (hour vs month)
- Cumulative distribution functions
- Rolling volatility analysis
- Cross-correlation between pollutants

Outputs appended to: eda/plots/ and eda/reports/
"""

import os
import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "backfill_features.csv"
PLOTS_DIR = Path(__file__).resolve().parent / "plots"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def autocorrelation_analysis(df: pd.DataFrame):
    """ACF/PACF plots for AQI time series — guides ARIMA/lag selection."""
    print("[A1] Autocorrelation (ACF/PACF) analysis...")
    from statsmodels.tsa.stattools import acf, pacf
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

    # Daily aggregation for cleaner signal
    daily_aqi = df.set_index("timestamp")["aqi_value"].resample("D").mean().dropna()

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle("Autocorrelation Analysis - Daily AQI (Sargodha)", fontsize=14, fontweight="bold")

    plot_acf(daily_aqi, lags=60, ax=axes[0], color="#2c3e50", alpha=0.05)
    axes[0].set_title("Autocorrelation Function (ACF) - 60 Day Lags")
    axes[0].set_xlabel("Lag (days)")
    axes[0].axvline(7, color="red", ls="--", alpha=0.5, label="7-day cycle")
    axes[0].axvline(30, color="orange", ls="--", alpha=0.5, label="30-day cycle")
    axes[0].legend()

    plot_pacf(daily_aqi, lags=60, ax=axes[1], color="#8e44ad", alpha=0.05, method="ywm")
    axes[1].set_title("Partial Autocorrelation Function (PACF) - 60 Day Lags")
    axes[1].set_xlabel("Lag (days)")

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "acf_pacf_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Compute ACF values for report
    acf_values = acf(daily_aqi, nlags=30)
    pacf_values = pacf(daily_aqi, nlags=30, method="ywm")
    acf_report = pd.DataFrame({
        "lag": range(len(acf_values)),
        "acf": acf_values,
        "pacf": pacf_values
    })
    acf_report.to_csv(REPORTS_DIR / "autocorrelation_values.csv", index=False)

    # Hourly ACF
    fig, ax = plt.subplots(figsize=(14, 4))
    hourly_acf = acf(df["aqi_value"].dropna(), nlags=168)  # 7 days of hours
    ax.bar(range(len(hourly_acf)), hourly_acf, width=1, color="#3498db", alpha=0.7)
    ax.axhline(0, color="black", lw=0.5)
    ax.axhline(1.96/np.sqrt(len(df)), color="red", ls="--", alpha=0.5)
    ax.axhline(-1.96/np.sqrt(len(df)), color="red", ls="--", alpha=0.5)
    ax.set_xlabel("Lag (hours)")
    ax.set_ylabel("ACF")
    ax.set_title("Hourly Autocorrelation (168h = 7 days) - Strong 24h Periodicity", fontweight="bold")
    for h in [24, 48, 72, 96, 120, 144, 168]:
        ax.axvline(h, color="orange", ls=":", alpha=0.4)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "hourly_acf_168h.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved ACF/PACF plots (daily + hourly)")


def hypothesis_testing(df: pd.DataFrame):
    """Statistical hypothesis tests for seasonal and temporal effects."""
    print("[A2] Hypothesis testing (seasonal/weekend effects)...")

    results = {}

    # 1. Weekend vs Weekday AQI (Mann-Whitney U test)
    df_t = df.copy()
    df_t["is_weekend"] = df_t["timestamp"].dt.dayofweek >= 5
    weekend_aqi = df_t[df_t["is_weekend"]]["aqi_value"]
    weekday_aqi = df_t[~df_t["is_weekend"]]["aqi_value"]
    stat, p_val = stats.mannwhitneyu(weekend_aqi, weekday_aqi, alternative="two-sided")
    results["weekend_vs_weekday"] = {
        "test": "Mann-Whitney U",
        "statistic": round(float(stat), 2),
        "p_value": round(float(p_val), 6),
        "weekend_median": round(float(weekend_aqi.median()), 2),
        "weekday_median": round(float(weekday_aqi.median()), 2),
        "significant": bool(p_val < 0.05),
        "interpretation": "Significant difference" if p_val < 0.05 else "No significant difference"
    }

    # 2. Winter vs Summer AQI (Mann-Whitney U)
    df_t["month"] = df_t["timestamp"].dt.month
    winter = df_t[df_t["month"].isin([11, 12, 1, 2])]["aqi_value"]
    summer = df_t[df_t["month"].isin([5, 6, 7, 8])]["aqi_value"]
    stat, p_val = stats.mannwhitneyu(winter, summer, alternative="greater")
    results["winter_vs_summer"] = {
        "test": "Mann-Whitney U (one-sided: winter > summer)",
        "statistic": round(float(stat), 2),
        "p_value": round(float(p_val), 8),
        "winter_median": round(float(winter.median()), 2),
        "summer_median": round(float(summer.median()), 2),
        "significant": bool(p_val < 0.05),
        "effect_size_r": round(float(stat / (len(winter) * len(summer))), 4),
        "interpretation": "Winter AQI significantly higher" if p_val < 0.05 else "No significant seasonal difference"
    }

    # 3. Kruskal-Wallis test across all seasons
    seasons = {
        "Winter": df_t[df_t["month"].isin([12, 1, 2])]["aqi_value"],
        "Spring": df_t[df_t["month"].isin([3, 4, 5])]["aqi_value"],
        "Summer": df_t[df_t["month"].isin([6, 7, 8])]["aqi_value"],
        "Autumn": df_t[df_t["month"].isin([9, 10, 11])]["aqi_value"],
    }
    stat, p_val = stats.kruskal(*seasons.values())
    results["seasonal_kruskal_wallis"] = {
        "test": "Kruskal-Wallis H",
        "statistic": round(float(stat), 2),
        "p_value": float(f"{p_val:.2e}"),
        "seasonal_medians": {k: round(float(v.median()), 2) for k, v in seasons.items()},
        "significant": bool(p_val < 0.05),
        "interpretation": "Significant seasonal differences exist" if p_val < 0.05 else "No seasonal differences"
    }

    # 4. Spearman rank correlation: Temperature vs AQI
    rho, p_val = stats.spearmanr(df["temperature_c"].dropna(), df["aqi_value"].dropna())
    results["temperature_aqi_spearman"] = {
        "test": "Spearman rank correlation",
        "rho": round(float(rho), 4),
        "p_value": float(f"{p_val:.2e}"),
        "significant": bool(p_val < 0.05),
        "interpretation": f"{'Negative' if rho < 0 else 'Positive'} monotonic relationship (rho={rho:.3f})"
    }

    # 5. Levene's test for variance homogeneity (day vs night)
    df_t["is_night"] = df_t["timestamp"].dt.hour.isin(range(0, 6)) | df_t["timestamp"].dt.hour.isin(range(20, 24))
    night_aqi = df_t[df_t["is_night"]]["aqi_value"]
    day_aqi = df_t[~df_t["is_night"]]["aqi_value"]
    stat, p_val = stats.levene(night_aqi, day_aqi)
    results["day_night_variance"] = {
        "test": "Levene's test (variance homogeneity)",
        "statistic": round(float(stat), 2),
        "p_value": round(float(p_val), 6),
        "night_std": round(float(night_aqi.std()), 2),
        "day_std": round(float(day_aqi.std()), 2),
        "significant": bool(p_val < 0.05),
        "interpretation": "Unequal variance (heteroscedastic)" if p_val < 0.05 else "Equal variance (homoscedastic)"
    }

    with open(REPORTS_DIR / "hypothesis_tests.json", "w") as f:
        json.dump(results, f, indent=2)

    # Visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Statistical Hypothesis Tests - AQI Analysis", fontsize=14, fontweight="bold")

    # Weekend vs Weekday
    ax = axes[0, 0]
    data_box = [weekday_aqi.values, weekend_aqi.values]
    bp = ax.boxplot(data_box, labels=["Weekday", "Weekend"], patch_artist=True)
    bp["boxes"][0].set_facecolor("#3498db")
    bp["boxes"][1].set_facecolor("#e74c3c")
    for box in bp["boxes"]:
        box.set_alpha(0.6)
    ax.set_ylabel("AQI")
    p = results["weekend_vs_weekday"]["p_value"]
    ax.set_title(f"Weekend vs Weekday AQI\n(Mann-Whitney p={p:.4f})")

    # Seasonal comparison
    ax = axes[0, 1]
    season_data = [v.values for v in seasons.values()]
    bp = ax.boxplot(season_data, labels=list(seasons.keys()), patch_artist=True)
    colors = ["#3498db", "#27ae60", "#e74c3c", "#f39c12"]
    for box, color in zip(bp["boxes"], colors):
        box.set_facecolor(color)
        box.set_alpha(0.6)
    ax.set_ylabel("AQI")
    p = results["seasonal_kruskal_wallis"]["p_value"]
    ax.set_title(f"Seasonal AQI Comparison\n(Kruskal-Wallis p={p:.2e})")

    # Day vs Night
    ax = axes[1, 0]
    data_box = [day_aqi.values, night_aqi.values]
    bp = ax.boxplot(data_box, labels=["Day (6-20h)", "Night (20-6h)"], patch_artist=True)
    bp["boxes"][0].set_facecolor("#f1c40f")
    bp["boxes"][1].set_facecolor("#2c3e50")
    for box in bp["boxes"]:
        box.set_alpha(0.6)
    ax.set_ylabel("AQI")
    p = results["day_night_variance"]["p_value"]
    ax.set_title(f"Day vs Night AQI Variance\n(Levene's p={p:.4f})")

    # Temperature vs AQI (Spearman)
    ax = axes[1, 1]
    sample = df.sample(3000, random_state=42)
    ax.scatter(sample["temperature_c"], sample["aqi_value"], alpha=0.2, s=8, color="#8e44ad")
    rho = results["temperature_aqi_spearman"]["rho"]
    ax.set_xlabel("Temperature (C)")
    ax.set_ylabel("AQI")
    ax.set_title(f"Temperature vs AQI\n(Spearman rho={rho:.4f})")

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "hypothesis_tests.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  5 hypothesis tests completed. Seasonal diff: {results['seasonal_kruskal_wallis']['significant']}")


def hourly_monthly_heatmap(df: pd.DataFrame):
    """2D heatmap of AQI by hour-of-day vs month — reveals pollution hotspots."""
    print("[A3] Hour x Month AQI heatmap...")

    df_t = df.copy()
    df_t["hour"] = df_t["timestamp"].dt.hour
    df_t["month"] = df_t["timestamp"].dt.month

    pivot = df_t.pivot_table(values="aqi_value", index="hour", columns="month", aggfunc="mean")
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd", interpolation="bicubic")
    ax.set_xticks(range(12))
    ax.set_xticklabels(month_labels)
    ax.set_yticks(range(24))
    ax.set_yticklabels([f"{h:02d}:00" for h in range(24)])
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Hour of Day", fontsize=12)
    ax.set_title("AQI Heatmap: Hour of Day vs Month\n(Sargodha, Pakistan - 5 Year Average)",
                 fontsize=13, fontweight="bold")
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Mean AQI", fontsize=11)

    # Annotate extreme cells
    for i in range(24):
        for j in range(12):
            val = pivot.values[i, j]
            if val > 160:
                ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "hour_month_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()

    pivot.to_csv(REPORTS_DIR / "hour_month_aqi_pivot.csv")
    print("  Saved hour x month heatmap")


def cumulative_distribution(df: pd.DataFrame):
    """Empirical CDF of AQI with EPA threshold annotations."""
    print("[A4] Cumulative distribution function (ECDF)...")

    aqi = df["aqi_value"].dropna().sort_values()
    ecdf = np.arange(1, len(aqi) + 1) / len(aqi)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(aqi, ecdf, color="#2c3e50", lw=2)

    # EPA thresholds
    thresholds = [(50, "Good", "#00e400"), (100, "Moderate", "#ffff00"),
                  (150, "Unhealthy-SG", "#ff7e00"), (200, "Unhealthy", "#ff0000"),
                  (300, "Very Unhealthy", "#8f3f97")]
    for thresh, label, color in thresholds:
        pct = (aqi <= thresh).sum() / len(aqi) * 100
        ax.axvline(thresh, color=color, ls="--", alpha=0.7)
        ax.axhline(pct/100, color=color, ls=":", alpha=0.3)
        ax.text(thresh + 2, 0.02, f"{label}\n({pct:.1f}%)", fontsize=8, color=color, fontweight="bold")

    ax.set_xlabel("AQI Value", fontsize=12)
    ax.set_ylabel("Cumulative Probability", fontsize=12)
    ax.set_title("Empirical CDF of AQI with EPA Category Thresholds\n(Sargodha, 5-Year Dataset)",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(0, 300)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "aqi_ecdf.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Percentile report
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    pct_values = {f"p{p}": round(float(np.percentile(aqi, p)), 1) for p in percentiles}
    pct_values["iqr"] = round(pct_values["p75"] - pct_values["p25"], 1)
    with open(REPORTS_DIR / "aqi_percentiles.json", "w") as f:
        json.dump(pct_values, f, indent=2)
    print("  Saved ECDF with EPA thresholds")


def rolling_volatility(df: pd.DataFrame):
    """Rolling standard deviation (volatility) over time — identifies unstable periods."""
    print("[A5] Rolling volatility analysis...")

    daily = df.set_index("timestamp")["aqi_value"].resample("D").mean().dropna()

    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)
    fig.suptitle("AQI Volatility Analysis - Sargodha", fontsize=14, fontweight="bold")

    # Daily AQI
    axes[0].plot(daily.index, daily.values, color="#2c3e50", lw=0.8, alpha=0.8)
    axes[0].fill_between(daily.index, 0, daily.values, alpha=0.1, color="#3498db")
    axes[0].set_ylabel("Daily Mean AQI")
    axes[0].set_title("Daily Average AQI")
    axes[0].axhline(150, color="red", ls="--", alpha=0.5, label="Unhealthy threshold")
    axes[0].legend()

    # 7-day rolling volatility
    vol_7 = daily.rolling(7).std()
    axes[1].plot(vol_7.index, vol_7.values, color="#e74c3c", lw=1.2)
    axes[1].fill_between(vol_7.index, 0, vol_7.values, alpha=0.2, color="#e74c3c")
    axes[1].set_ylabel("7-Day Rolling Std")
    axes[1].set_title("Short-term Volatility (7-Day Window)")
    axes[1].axhline(vol_7.mean(), color="black", ls="--", alpha=0.5, label=f"Mean={vol_7.mean():.1f}")
    axes[1].legend()

    # 30-day rolling volatility
    vol_30 = daily.rolling(30).std()
    axes[2].plot(vol_30.index, vol_30.values, color="#8e44ad", lw=1.5)
    axes[2].fill_between(vol_30.index, 0, vol_30.values, alpha=0.2, color="#8e44ad")
    axes[2].set_ylabel("30-Day Rolling Std")
    axes[2].set_title("Long-term Volatility (30-Day Window)")
    axes[2].axhline(vol_30.mean(), color="black", ls="--", alpha=0.5, label=f"Mean={vol_30.mean():.1f}")
    axes[2].legend()
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    axes[2].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "rolling_volatility.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Volatility stats
    vol_stats = {
        "mean_7d_volatility": round(float(vol_7.mean()), 2),
        "max_7d_volatility": round(float(vol_7.max()), 2),
        "mean_30d_volatility": round(float(vol_30.mean()), 2),
        "max_30d_volatility": round(float(vol_30.max()), 2),
        "high_volatility_periods_pct": round(float((vol_7 > vol_7.quantile(0.9)).sum() / len(vol_7) * 100), 1),
    }
    with open(REPORTS_DIR / "volatility_analysis.json", "w") as f:
        json.dump(vol_stats, f, indent=2)
    print("  Saved rolling volatility analysis")


def cross_pollutant_lag_correlation(df: pd.DataFrame):
    """Cross-correlation between pollutants at different lags."""
    print("[A6] Cross-pollutant lag correlation...")

    pollutants = ["aqi_value", "pm25", "pm10", "no2", "so2", "co", "o3"]
    pollutants = [p for p in pollutants if p in df.columns]
    max_lag = 24  # hours

    # Compute lag correlations for each pair with AQI
    lag_corr = {}
    for pol in pollutants:
        if pol == "aqi_value":
            continue
        corrs = []
        for lag in range(max_lag + 1):
            shifted = df[pol].shift(lag)
            corr = df["aqi_value"].corr(shifted)
            corrs.append(corr)
        lag_corr[pol] = corrs

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#e74c3c", "#3498db", "#27ae60", "#f39c12", "#8e44ad", "#1abc9c"]
    for (pol, corrs), color in zip(lag_corr.items(), colors):
        ax.plot(range(max_lag + 1), corrs, "-o", color=color, lw=1.5, markersize=3, label=pol)
    ax.set_xlabel("Lag (hours)", fontsize=12)
    ax.set_ylabel("Pearson Correlation with AQI", fontsize=12)
    ax.set_title("Lag-Correlation: How Past Pollutant Values Predict Current AQI",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, max_lag)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "cross_pollutant_lag_correlation.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Save lag correlation matrix
    lag_df = pd.DataFrame(lag_corr, index=[f"lag_{i}h" for i in range(max_lag + 1)])
    lag_df.to_csv(REPORTS_DIR / "lag_correlation_matrix.csv")
    print("  Saved cross-pollutant lag correlation (24h window)")


def pollution_wind_analysis(df: pd.DataFrame):
    """Wind direction vs AQI analysis (pseudo wind-rose)."""
    print("[A7] Pollution-wind directional analysis...")

    df_w = df[["wind_direction_deg", "wind_speed_ms", "aqi_value", "pm25"]].dropna()

    # Bin wind directions into 16 sectors
    n_sectors = 16
    sector_width = 360 / n_sectors
    df_w["sector"] = ((df_w["wind_direction_deg"] + sector_width/2) % 360 // sector_width).astype(int)

    sector_stats = df_w.groupby("sector").agg(
        mean_aqi=("aqi_value", "mean"),
        mean_pm25=("pm25", "mean"),
        mean_wind=("wind_speed_ms", "mean"),
        count=("aqi_value", "count")
    ).reset_index()

    # Polar plot
    angles = np.linspace(0, 2*np.pi, n_sectors, endpoint=False)
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), subplot_kw=dict(polar=True))
    fig.suptitle("Pollution by Wind Direction - Sargodha", fontsize=14, fontweight="bold", y=1.02)

    # AQI by wind direction
    ax = axes[0]
    values = sector_stats["mean_aqi"].values
    values_closed = np.append(values, values[0])
    angles_closed = np.append(angles, angles[0])
    ax.plot(angles_closed, values_closed, "o-", color="#e74c3c", lw=2, markersize=5)
    ax.fill(angles_closed, values_closed, alpha=0.2, color="#e74c3c")
    ax.set_thetagrids(np.degrees(angles), directions, fontsize=8)
    ax.set_title("Mean AQI by\nWind Direction", pad=20, fontweight="bold")

    # PM2.5 by wind direction
    ax = axes[1]
    values = sector_stats["mean_pm25"].values
    values_closed = np.append(values, values[0])
    ax.plot(angles_closed, values_closed, "o-", color="#8e44ad", lw=2, markersize=5)
    ax.fill(angles_closed, values_closed, alpha=0.2, color="#8e44ad")
    ax.set_thetagrids(np.degrees(angles), directions, fontsize=8)
    ax.set_title("Mean PM2.5 by\nWind Direction", pad=20, fontweight="bold")

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "pollution_wind_rose.png", dpi=150, bbox_inches="tight")
    plt.close()

    sector_stats["direction"] = directions
    sector_stats.to_csv(REPORTS_DIR / "wind_direction_pollution.csv", index=False)
    print("  Saved pollution wind-rose analysis")


def granger_causality_test(df: pd.DataFrame):
    """Granger causality: Do weather variables Granger-cause AQI?"""
    print("[A8] Granger causality tests (weather -> AQI)...")
    from statsmodels.tsa.stattools import grangercausalitytests

    # Daily aggregation + differencing for stationarity
    daily = df.set_index("timestamp")[["aqi_value", "temperature_c", "humidity_pct",
                                        "wind_speed_ms", "pressure_hpa"]].resample("D").mean().dropna()
    daily_diff = daily.diff().dropna()

    max_lag = 7
    results = {}

    for col in ["temperature_c", "humidity_pct", "wind_speed_ms", "pressure_hpa"]:
        try:
            test_data = daily_diff[["aqi_value", col]].dropna()
            gc_result = grangercausalitytests(test_data, maxlag=max_lag, verbose=False)
            # Get minimum p-value across lags
            p_values = [gc_result[lag][0]["ssr_ftest"][1] for lag in range(1, max_lag + 1)]
            best_lag = np.argmin(p_values) + 1
            results[col] = {
                "best_lag_days": int(best_lag),
                "min_p_value": round(float(min(p_values)), 6),
                "significant": bool(min(p_values) < 0.05),
                "all_p_values": {f"lag_{i+1}": round(float(p), 4) for i, p in enumerate(p_values)},
                "interpretation": f"{col} Granger-causes AQI at lag {best_lag}" if min(p_values) < 0.05
                                  else f"{col} does NOT Granger-cause AQI"
            }
        except Exception as e:
            results[col] = {"error": str(e)}

    with open(REPORTS_DIR / "granger_causality.json", "w") as f:
        json.dump(results, f, indent=2)

    # Summary visualization
    fig, ax = plt.subplots(figsize=(10, 5))
    variables = list(results.keys())
    p_values_min = [results[v].get("min_p_value", 1.0) for v in variables]
    colors_bar = ["#27ae60" if p < 0.05 else "#e74c3c" for p in p_values_min]
    bars = ax.barh(variables, [-np.log10(p) for p in p_values_min], color=colors_bar, alpha=0.8)
    ax.axvline(-np.log10(0.05), color="black", ls="--", label="p=0.05 threshold")
    ax.set_xlabel("-log10(p-value)")
    ax.set_title("Granger Causality: Weather Variables → AQI\n(Green = Significant, Red = Not Significant)",
                 fontweight="bold")
    ax.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "granger_causality.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Granger tests complete. Significant predictors: {[v for v, r in results.items() if r.get('significant')]}")


def pair_plot_analysis(df: pd.DataFrame):
    """Pair plot with KDE for key variables."""
    print("[A9] Pair plot (pollutants + weather)...")

    key_cols = ["aqi_value", "pm25", "temperature_c", "humidity_pct", "wind_speed_ms"]
    sample = df[key_cols].sample(2000, random_state=42)

    # Add AQI category for coloring
    sample["AQI_Level"] = pd.cut(sample["aqi_value"],
                                  bins=[0, 50, 100, 150, 300],
                                  labels=["Good", "Moderate", "Unhealthy-SG", "Unhealthy+"])

    g = sns.pairplot(sample, hue="AQI_Level", diag_kind="kde",
                     palette={"Good": "#00e400", "Moderate": "#f39c12",
                              "Unhealthy-SG": "#ff7e00", "Unhealthy+": "#ff0000"},
                     plot_kws={"alpha": 0.3, "s": 15},
                     diag_kws={"alpha": 0.6})
    g.figure.suptitle("Pair Plot: Key Variables Colored by AQI Category", y=1.02, fontsize=13, fontweight="bold")
    g.savefig(PLOTS_DIR / "pair_plot_by_aqi_level.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved pair plot (5 variables x 4 AQI levels)")


def generate_advanced_summary():
    """Update the EDA summary with advanced analysis counts."""
    print("\n[A10] Updating EDA summary...")

    plots = list(PLOTS_DIR.glob("*.png"))
    reports = [f for f in REPORTS_DIR.glob("*.*") if f.suffix in [".csv", ".json"]]

    summary = {
        "project": "Pearls AQI Predictor - Advanced EDA",
        "analysis_date": str(pd.Timestamp.now()),
        "total_analyses": 19,
        "base_analyses": 10,
        "advanced_analyses": 9,
        "total_plots": len(plots),
        "total_reports": len(reports),
        "advanced_methods": [
            "Autocorrelation (ACF/PACF)",
            "Granger Causality Tests",
            "Mann-Whitney U Tests",
            "Kruskal-Wallis H Test",
            "Spearman Rank Correlation",
            "Levene's Variance Test",
            "Empirical CDF with EPA Thresholds",
            "Rolling Volatility (7-day and 30-day)",
            "Cross-Pollutant Lag Correlation",
            "Pollution Wind Rose (16-sector)",
            "Hour x Month Heatmap",
            "Pair Plot with KDE"
        ],
        "plots_generated": sorted([p.name for p in plots]),
        "reports_generated": sorted([r.name for r in reports]),
    }

    with open(REPORTS_DIR / "eda_advanced_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'=' * 60}")
    print("ADVANCED EDA COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Total plots: {len(plots)}")
    print(f"  Total reports: {len(reports)}")
    print(f"  Advanced analyses: 9")
    print(f"{'=' * 60}")


def main():
    print("=" * 60)
    print("PEARLS AQI PREDICTOR - Advanced EDA (Part 2)")
    print("=" * 60 + "\n")

    df = load_data()
    autocorrelation_analysis(df)
    hypothesis_testing(df)
    hourly_monthly_heatmap(df)
    cumulative_distribution(df)
    rolling_volatility(df)
    cross_pollutant_lag_correlation(df)
    pollution_wind_analysis(df)
    granger_causality_test(df)
    pair_plot_analysis(df)
    generate_advanced_summary()


if __name__ == "__main__":
    main()
