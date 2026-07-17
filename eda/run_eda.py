"""
Comprehensive Exploratory Data Analysis (EDA) for Pearls AQI Predictor
======================================================================
Generates statistical reports, visualizations, and insights from the
historical AQI feature dataset for Sargodha, Pakistan.

Outputs:
  - eda/reports/  : JSON/CSV statistical summaries
  - eda/plots/    : PNG visualizations
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

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "backfill_features.csv"
PLOTS_DIR = Path(__file__).resolve().parent / "plots"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"
PLOTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


def load_data() -> pd.DataFrame:
    """Load and parse the backfill features dataset."""
    print("[1/10] Loading dataset...")
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    print(f"  Dataset shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"  Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    return df


def dataset_overview(df: pd.DataFrame):
    """Generate dataset overview statistics."""
    print("[2/10] Dataset overview & missing values...")

    info = {
        "total_rows": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "time_range_start": str(df["timestamp"].min()),
        "time_range_end": str(df["timestamp"].max()),
        "duration_days": int((df["timestamp"].max() - df["timestamp"].min()).days),
        "numeric_columns": int(df.select_dtypes(include=[np.number]).shape[1]),
        "categorical_columns": int(df.select_dtypes(include=["object", "bool"]).shape[1]),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
    }

    # Missing values
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_report = pd.DataFrame({
        "missing_count": missing,
        "missing_pct": missing_pct
    }).sort_values("missing_pct", ascending=False)
    missing_report = missing_report[missing_report["missing_count"] > 0]

    info["columns_with_missing"] = int(len(missing_report))
    info["total_missing_values"] = int(missing.sum())
    info["total_missing_pct"] = round(missing.sum() / (df.shape[0] * df.shape[1]) * 100, 4)

    with open(REPORTS_DIR / "dataset_overview.json", "w") as f:
        json.dump(info, f, indent=2)

    missing_report.to_csv(REPORTS_DIR / "missing_values.csv")
    print(f"  Missing values: {info['total_missing_values']} ({info['total_missing_pct']}%)")
    return info


def descriptive_statistics(df: pd.DataFrame):
    """Compute and save descriptive statistics for all numeric columns."""
    print("[3/10] Descriptive statistics...")

    numeric_df = df.select_dtypes(include=[np.number])
    desc = numeric_df.describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T
    desc["skewness"] = numeric_df.skew()
    desc["kurtosis"] = numeric_df.kurtosis()
    desc["iqr"] = desc["75%"] - desc["25%"]
    desc["cv"] = (desc["std"] / desc["mean"].replace(0, np.nan) * 100).round(2)
    desc.to_csv(REPORTS_DIR / "descriptive_statistics.csv")

    # Key pollutant stats
    pollutants = ["aqi_value", "pm25", "pm10", "no2", "so2", "co", "o3"]
    pollutant_stats = desc.loc[[c for c in pollutants if c in desc.index]]
    pollutant_stats.to_csv(REPORTS_DIR / "pollutant_statistics.csv")
    print(f"  Saved stats for {len(desc)} numeric columns")


def distribution_analysis(df: pd.DataFrame):
    """Plot distributions of key variables."""
    print("[4/10] Distribution analysis...")

    # AQI distribution
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("Distribution of Key Pollutants - Sargodha, Pakistan", fontsize=14, fontweight="bold")

    pollutants = ["aqi_value", "pm25", "pm10", "no2", "so2", "o3"]
    colors = ["#e74c3c", "#8e44ad", "#2980b9", "#27ae60", "#f39c12", "#1abc9c"]

    for ax, col, color in zip(axes.flat, pollutants, colors):
        if col in df.columns:
            data = df[col].dropna()
            ax.hist(data, bins=50, color=color, alpha=0.7, edgecolor="white", density=True)
            # KDE overlay
            kde_x = np.linspace(data.min(), data.max(), 200)
            kde = stats.gaussian_kde(data)
            ax.plot(kde_x, kde(kde_x), color="black", lw=2)
            ax.set_title(f"{col}\n(mean={data.mean():.1f}, std={data.std():.1f})", fontsize=11)
            ax.set_xlabel(col)
            ax.set_ylabel("Density")
            # Normality test (D'Agostino-Pearson)
            if len(data) > 20:
                _, p_val = stats.normaltest(data.sample(min(5000, len(data)), random_state=42))
                ax.text(0.95, 0.95, f"Normal p={p_val:.2e}", transform=ax.transAxes,
                        ha="right", va="top", fontsize=8, style="italic")

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "pollutant_distributions.png", dpi=150, bbox_inches="tight")
    plt.close()

    # AQI Box plot by category
    fig, ax = plt.subplots(figsize=(10, 6))
    bins = [0, 50, 100, 150, 200, 300, 500]
    labels = ["Good", "Moderate", "Unhealthy-SG", "Unhealthy", "Very Unhealthy", "Hazardous"]
    df_temp = df.copy()
    df_temp["aqi_category"] = pd.cut(df_temp["aqi_value"], bins=bins, labels=labels, right=True)
    cat_counts = df_temp["aqi_category"].value_counts()
    cat_pct = (cat_counts / len(df_temp) * 100).round(1)

    colors_cat = ["#00e400", "#ffff00", "#ff7e00", "#ff0000", "#8f3f97", "#7e0023"]
    bars = ax.bar(cat_pct.index.astype(str), cat_pct.values, color=colors_cat[:len(cat_pct)])
    ax.set_title("AQI Category Distribution", fontsize=13, fontweight="bold")
    ax.set_ylabel("Percentage (%)")
    ax.set_xlabel("AQI Category")
    for bar, pct in zip(bars, cat_pct.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{pct:.1f}%", ha="center", fontsize=10)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "aqi_category_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Save category report
    cat_report = pd.DataFrame({"count": cat_counts, "percentage": cat_pct})
    cat_report.to_csv(REPORTS_DIR / "aqi_category_distribution.csv")
    print(f"  Saved distribution plots and category analysis")


def correlation_analysis(df: pd.DataFrame):
    """Compute and visualize correlation matrix."""
    print("[5/10] Correlation analysis...")

    key_cols = ["aqi_value", "pm25", "pm10", "no2", "so2", "co", "o3",
                "temperature_c", "humidity_pct", "wind_speed_ms",
                "pressure_hpa", "precipitation_mm"]
    key_cols = [c for c in key_cols if c in df.columns]
    corr_matrix = df[key_cols].corr()

    # Full heatmap
    fig, ax = plt.subplots(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                center=0, vmin=-1, vmax=1, square=True, linewidths=0.5, ax=ax,
                cbar_kws={"shrink": 0.8})
    ax.set_title("Correlation Matrix: Pollutants & Weather Features\n(Sargodha, Pakistan)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "correlation_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Top correlations with AQI
    aqi_corr = corr_matrix["aqi_value"].drop("aqi_value").sort_values(key=abs, ascending=False)
    aqi_corr.to_csv(REPORTS_DIR / "aqi_correlations.csv")

    # Full correlation matrix
    corr_matrix.to_csv(REPORTS_DIR / "correlation_matrix.csv")

    # Scatter plots of top correlated features
    top_features = aqi_corr.head(4).index.tolist()
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("AQI vs Top Correlated Features", fontsize=13, fontweight="bold")
    for ax, feat in zip(axes.flat, top_features):
        ax.scatter(df[feat], df["aqi_value"], alpha=0.1, s=5, color="#3498db")
        # Regression line
        slope, intercept, r_val, _, _ = stats.linregress(df[feat].dropna(), df["aqi_value"].dropna())
        x_line = np.linspace(df[feat].min(), df[feat].max(), 100)
        ax.plot(x_line, slope * x_line + intercept, color="red", lw=2, label=f"R={r_val:.3f}")
        ax.set_xlabel(feat)
        ax.set_ylabel("AQI")
        ax.set_title(f"AQI vs {feat} (r={aqi_corr[feat]:.3f})")
        ax.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "aqi_scatter_top_features.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Top AQI correlations: {dict(aqi_corr.head(5).round(3))}")


def temporal_trends(df: pd.DataFrame):
    """Analyze temporal patterns: hourly, daily, monthly, yearly."""
    print("[6/10] Temporal trend analysis...")

    df_t = df.copy()
    df_t["hour"] = df_t["timestamp"].dt.hour
    df_t["day_of_week"] = df_t["timestamp"].dt.dayofweek
    df_t["month"] = df_t["timestamp"].dt.month
    df_t["year"] = df_t["timestamp"].dt.year
    df_t["date"] = df_t["timestamp"].dt.date

    # --- Hourly pattern ---
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Temporal Patterns in AQI - Sargodha, Pakistan", fontsize=14, fontweight="bold")

    hourly = df_t.groupby("hour")["aqi_value"].agg(["mean", "std", "median"]).reset_index()
    ax = axes[0, 0]
    ax.plot(hourly["hour"], hourly["mean"], "o-", color="#e74c3c", lw=2, markersize=6)
    ax.fill_between(hourly["hour"], hourly["mean"] - hourly["std"],
                    hourly["mean"] + hourly["std"], alpha=0.2, color="#e74c3c")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("AQI")
    ax.set_title("Diurnal AQI Pattern (Mean +/- Std)")
    ax.set_xticks(range(0, 24, 2))
    ax.axhline(100, color="orange", ls="--", alpha=0.7, label="Moderate threshold")
    ax.legend()

    # --- Day of week pattern ---
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    daily = df_t.groupby("day_of_week")["aqi_value"].agg(["mean", "std"]).reset_index()
    ax = axes[0, 1]
    bars = ax.bar(daily["day_of_week"], daily["mean"], yerr=daily["std"],
                  color=["#3498db"]*5 + ["#e74c3c"]*2, alpha=0.8, capsize=4)
    ax.set_xticks(range(7))
    ax.set_xticklabels(days)
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Mean AQI")
    ax.set_title("Weekly AQI Pattern (Weekend highlighted)")

    # --- Monthly pattern ---
    monthly = df_t.groupby("month")["aqi_value"].agg(["mean", "std", "median"]).reset_index()
    ax = axes[1, 0]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ax.bar(monthly["month"], monthly["mean"], color="#27ae60", alpha=0.8, edgecolor="white")
    ax.errorbar(monthly["month"], monthly["mean"], yerr=monthly["std"],
                fmt="none", color="black", capsize=3)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(months, rotation=45)
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean AQI")
    ax.set_title("Seasonal AQI Pattern")
    ax.axhline(100, color="orange", ls="--", alpha=0.7)

    # --- Yearly trend ---
    yearly = df_t.groupby("year")["aqi_value"].agg(["mean", "std", "count"]).reset_index()
    ax = axes[1, 1]
    ax.plot(yearly["year"], yearly["mean"], "s-", color="#8e44ad", lw=2, markersize=8)
    ax.fill_between(yearly["year"], yearly["mean"] - yearly["std"],
                    yearly["mean"] + yearly["std"], alpha=0.2, color="#8e44ad")
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean AQI")
    ax.set_title("Yearly AQI Trend")

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "temporal_patterns.png", dpi=150, bbox_inches="tight")
    plt.close()

    # --- Monthly time series ---
    fig, ax = plt.subplots(figsize=(16, 5))
    monthly_ts = df_t.groupby(df_t["timestamp"].dt.to_period("M"))["aqi_value"].mean()
    monthly_ts.index = monthly_ts.index.to_timestamp()
    ax.plot(monthly_ts.index, monthly_ts.values, "-", color="#2c3e50", lw=1.5)
    ax.fill_between(monthly_ts.index, 0, monthly_ts.values, alpha=0.15, color="#3498db")
    ax.axhline(100, color="red", ls="--", alpha=0.6, label="Unhealthy threshold")
    ax.axhline(50, color="orange", ls="--", alpha=0.6, label="Moderate threshold")
    ax.set_title("Monthly Average AQI Time Series - Sargodha", fontsize=13, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Monthly Mean AQI")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "monthly_aqi_timeseries.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Save temporal stats
    hourly.to_csv(REPORTS_DIR / "hourly_aqi_pattern.csv", index=False)
    daily.to_csv(REPORTS_DIR / "daily_aqi_pattern.csv", index=False)
    monthly.to_csv(REPORTS_DIR / "monthly_aqi_pattern.csv", index=False)
    yearly.to_csv(REPORTS_DIR / "yearly_aqi_trend.csv", index=False)
    print("  Saved temporal pattern plots and statistics")


def seasonality_decomposition(df: pd.DataFrame):
    """Analyze seasonality and stationarity."""
    print("[7/10] Seasonality & stationarity analysis...")

    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller

    # Resample to daily for cleaner decomposition
    df_daily = df.set_index("timestamp")["aqi_value"].resample("D").mean().dropna()

    # Seasonal decomposition (additive, period=365 days)
    period = min(365, len(df_daily) // 2)
    decomposition = seasonal_decompose(df_daily, model="additive", period=period)

    fig, axes = plt.subplots(4, 1, figsize=(16, 12), sharex=True)
    fig.suptitle("AQI Time Series Decomposition (Additive, Period=365 days)",
                 fontsize=13, fontweight="bold")

    axes[0].plot(decomposition.observed, color="#2c3e50", lw=0.8)
    axes[0].set_ylabel("Observed")
    axes[0].set_title("Original Signal")

    axes[1].plot(decomposition.trend, color="#e74c3c", lw=1.5)
    axes[1].set_ylabel("Trend")
    axes[1].set_title("Long-term Trend")

    axes[2].plot(decomposition.seasonal, color="#27ae60", lw=0.5)
    axes[2].set_ylabel("Seasonal")
    axes[2].set_title("Seasonal Component")

    axes[3].plot(decomposition.resid, color="#7f8c8d", lw=0.5)
    axes[3].set_ylabel("Residual")
    axes[3].set_title("Residuals (Noise)")

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "seasonal_decomposition.png", dpi=150, bbox_inches="tight")
    plt.close()

    # ADF stationarity test
    adf_result = adfuller(df_daily.dropna(), autolag="AIC")
    stationarity_report = {
        "adf_statistic": round(float(adf_result[0]), 4),
        "p_value": round(float(adf_result[1]), 6),
        "lags_used": int(adf_result[2]),
        "num_observations": int(adf_result[3]),
        "critical_values": {k: round(v, 4) for k, v in adf_result[4].items()},
        "is_stationary": bool(adf_result[1] < 0.05),
        "interpretation": "Series is stationary (reject null)" if adf_result[1] < 0.05
                          else "Series is non-stationary (fail to reject null)"
    }
    with open(REPORTS_DIR / "stationarity_test.json", "w") as f:
        json.dump(stationarity_report, f, indent=2)

    print(f"  ADF test p-value: {stationarity_report['p_value']} -> {stationarity_report['interpretation']}")


def weather_pollutant_relationships(df: pd.DataFrame):
    """Analyze relationships between weather and pollutants."""
    print("[8/10] Weather-pollutant relationship analysis...")

    # Temperature vs AQI by season
    df_temp = df.copy()
    df_temp["season"] = df_temp["month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Autumn", 10: "Autumn", 11: "Autumn"
    })

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle("Weather Impact on Air Quality - Sargodha", fontsize=14, fontweight="bold")

    # Temperature vs AQI by season
    ax = axes[0, 0]
    for season, color in zip(["Winter", "Spring", "Summer", "Autumn"],
                             ["#3498db", "#27ae60", "#e74c3c", "#f39c12"]):
        subset = df_temp[df_temp["season"] == season]
        ax.scatter(subset["temperature_c"], subset["aqi_value"], alpha=0.05, s=3, color=color, label=season)
    ax.set_xlabel("Temperature (C)")
    ax.set_ylabel("AQI")
    ax.set_title("Temperature vs AQI (by Season)")
    ax.legend(markerscale=5)

    # Wind speed vs AQI
    ax = axes[0, 1]
    wind_bins = pd.cut(df["wind_speed_ms"], bins=10)
    wind_aqi = df.groupby(wind_bins, observed=True)["aqi_value"].mean()
    ax.bar(range(len(wind_aqi)), wind_aqi.values, color="#1abc9c", alpha=0.8)
    ax.set_xlabel("Wind Speed Bin")
    ax.set_ylabel("Mean AQI")
    ax.set_title("Wind Speed Effect on AQI")
    ax.set_xticks(range(len(wind_aqi)))
    ax.set_xticklabels([f"{i.left:.1f}-{i.right:.1f}" for i in wind_aqi.index], rotation=45, fontsize=8)

    # Humidity vs PM2.5
    ax = axes[1, 0]
    ax.scatter(df["humidity_pct"], df["pm25"], alpha=0.05, s=3, color="#8e44ad")
    ax.set_xlabel("Humidity (%)")
    ax.set_ylabel("PM2.5 (ug/m3)")
    ax.set_title("Humidity vs PM2.5 Concentration")

    # Pressure vs AQI
    ax = axes[1, 1]
    ax.scatter(df["pressure_hpa"], df["aqi_value"], alpha=0.05, s=3, color="#e67e22")
    ax.set_xlabel("Pressure (hPa)")
    ax.set_ylabel("AQI")
    ax.set_title("Atmospheric Pressure vs AQI")

    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "weather_pollutant_relationships.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Seasonal statistics
    seasonal_stats = df_temp.groupby("season")[["aqi_value", "pm25", "pm10", "temperature_c",
                                                 "humidity_pct", "wind_speed_ms"]].agg(["mean", "std", "median"])
    seasonal_stats.columns = ["_".join(col) for col in seasonal_stats.columns]
    seasonal_stats.to_csv(REPORTS_DIR / "seasonal_statistics.csv")
    print("  Saved weather-pollutant relationship analysis")


def feature_importance_eda(df: pd.DataFrame):
    """Quick feature importance via mutual information and variance analysis."""
    print("[9/10] Feature importance (mutual information)...")

    from sklearn.feature_selection import mutual_info_regression
    from sklearn.preprocessing import StandardScaler

    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if c not in ["aqi_value", "year"]]
    X = df[feature_cols].fillna(0)
    y = df["aqi_value"]

    # Mutual Information
    mi_scores = mutual_info_regression(X, y, random_state=42, n_neighbors=5)
    mi_df = pd.DataFrame({"feature": feature_cols, "mutual_info": mi_scores})
    mi_df = mi_df.sort_values("mutual_info", ascending=False).reset_index(drop=True)
    mi_df.to_csv(REPORTS_DIR / "feature_mutual_information.csv", index=False)

    # Plot top 20 features
    fig, ax = plt.subplots(figsize=(10, 8))
    top20 = mi_df.head(20)
    bars = ax.barh(range(len(top20)), top20["mutual_info"].values, color="#3498db", alpha=0.8)
    ax.set_yticks(range(len(top20)))
    ax.set_yticklabels(top20["feature"].values)
    ax.set_xlabel("Mutual Information Score")
    ax.set_title("Top 20 Features by Mutual Information with AQI", fontsize=13, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "feature_importance_mutual_info.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Variance analysis
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    variance = pd.Series(X_scaled.var(axis=0), index=feature_cols).sort_values(ascending=False)
    variance.to_csv(REPORTS_DIR / "feature_variance.csv")

    print(f"  Top 5 features by MI: {mi_df.head(5)['feature'].tolist()}")


def outlier_analysis(df: pd.DataFrame):
    """Detect and characterize outliers in key variables."""
    print("[10/10] Outlier detection & analysis...")

    key_cols = ["aqi_value", "pm25", "pm10", "no2", "so2", "co", "o3",
                "temperature_c", "humidity_pct", "wind_speed_ms"]
    key_cols = [c for c in key_cols if c in df.columns]

    outlier_report = {}
    for col in key_cols:
        data = df[col].dropna()
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = data[(data < lower) | (data > upper)]
        outlier_report[col] = {
            "total": int(len(data)),
            "outlier_count": int(len(outliers)),
            "outlier_pct": round(len(outliers) / len(data) * 100, 2),
            "lower_bound": round(float(lower), 2),
            "upper_bound": round(float(upper), 2),
            "min_value": round(float(data.min()), 2),
            "max_value": round(float(data.max()), 2),
        }

    with open(REPORTS_DIR / "outlier_analysis.json", "w") as f:
        json.dump(outlier_report, f, indent=2)

    # Box plots
    fig, axes = plt.subplots(2, 5, figsize=(18, 8))
    fig.suptitle("Outlier Analysis - Box Plots of Key Variables", fontsize=13, fontweight="bold")
    for ax, col in zip(axes.flat, key_cols):
        bp = ax.boxplot(df[col].dropna(), patch_artist=True, vert=True)
        bp["boxes"][0].set_facecolor("#3498db")
        bp["boxes"][0].set_alpha(0.6)
        ax.set_title(f"{col}\n({outlier_report[col]['outlier_pct']}% outliers)", fontsize=9)
        ax.set_xticklabels([])
    # Hide unused axes
    for i in range(len(key_cols), len(axes.flat)):
        axes.flat[i].set_visible(False)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "outlier_boxplots.png", dpi=150, bbox_inches="tight")
    plt.close()

    # High AQI events analysis
    high_aqi = df[df["aqi_value"] > 150].copy()
    high_aqi_stats = {
        "hazardous_hours": int(len(high_aqi)),
        "hazardous_pct": round(len(high_aqi) / len(df) * 100, 2),
        "max_aqi_recorded": round(float(df["aqi_value"].max()), 1),
        "avg_aqi_during_hazardous": round(float(high_aqi["aqi_value"].mean()), 1) if len(high_aqi) > 0 else 0,
        "common_conditions_during_hazardous": {
            "avg_temperature": round(float(high_aqi["temperature_c"].mean()), 1) if len(high_aqi) > 0 else None,
            "avg_humidity": round(float(high_aqi["humidity_pct"].mean()), 1) if len(high_aqi) > 0 else None,
            "avg_wind_speed": round(float(high_aqi["wind_speed_ms"].mean()), 1) if len(high_aqi) > 0 else None,
        }
    }
    with open(REPORTS_DIR / "hazardous_events_analysis.json", "w") as f:
        json.dump(high_aqi_stats, f, indent=2)

    print(f"  Found {outlier_report['aqi_value']['outlier_count']} AQI outliers ({outlier_report['aqi_value']['outlier_pct']}%)")
    print(f"  Hazardous AQI events (>150): {high_aqi_stats['hazardous_hours']} hours ({high_aqi_stats['hazardous_pct']}%)")


def generate_summary_report(df: pd.DataFrame):
    """Generate a final comprehensive EDA summary."""
    print("\n[FINAL] Generating comprehensive EDA summary report...")

    summary = {
        "project": "Pearls AQI Predictor - Sargodha, Pakistan",
        "analysis_date": str(pd.Timestamp.now()),
        "dataset": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "time_span": f"{df['timestamp'].min()} to {df['timestamp'].max()}",
            "hourly_resolution": True,
            "source": "Synthetic backfill based on AQICN + OpenWeather patterns",
        },
        "key_findings": {
            "mean_aqi": round(float(df["aqi_value"].mean()), 1),
            "median_aqi": round(float(df["aqi_value"].median()), 1),
            "std_aqi": round(float(df["aqi_value"].std()), 1),
            "max_aqi": round(float(df["aqi_value"].max()), 1),
            "min_aqi": round(float(df["aqi_value"].min()), 1),
            "dominant_category": "Determined from category distribution report",
            "strongest_correlations": "See aqi_correlations.csv",
            "best_predictive_features": "See feature_mutual_information.csv",
        },
        "artifacts_generated": {
            "plots": [f.name for f in PLOTS_DIR.glob("*.png")],
            "reports": [f.name for f in REPORTS_DIR.glob("*.*") if f.suffix in [".csv", ".json"]],
        }
    }

    with open(REPORTS_DIR / "eda_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("EDA COMPLETE")
    print("=" * 60)
    print(f"  Plots saved to: {PLOTS_DIR}")
    print(f"  Reports saved to: {REPORTS_DIR}")
    print(f"  Total plots: {len(list(PLOTS_DIR.glob('*.png')))}")
    print(f"  Total reports: {len(list(REPORTS_DIR.glob('*.*')))}")
    print("=" * 60)


def main():
    """Run the full EDA pipeline."""
    print("=" * 60)
    print("PEARLS AQI PREDICTOR - Exploratory Data Analysis")
    print("City: Sargodha, Pakistan")
    print("=" * 60 + "\n")

    df = load_data()
    dataset_overview(df)
    descriptive_statistics(df)
    distribution_analysis(df)
    correlation_analysis(df)
    temporal_trends(df)
    seasonality_decomposition(df)
    weather_pollutant_relationships(df)
    feature_importance_eda(df)
    outlier_analysis(df)
    generate_summary_report(df)


if __name__ == "__main__":
    main()
