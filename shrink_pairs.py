import re

shrink_map = {
    "hour_month_heatmap.png": ("\\textwidth", "0.85\\textwidth"),
    "monthly_aqi_timeseries.png": ("\\textwidth", "0.85\\textwidth"),
    "acf_pacf_analysis.png": ("\\textwidth", "0.85\\textwidth"),
    "hourly_acf_168h.png": ("\\textwidth", "0.85\\textwidth"),
    "pollution_wind_rose.png": ("0.9\\textwidth", "0.75\\textwidth"),
    "granger_causality.png": ("0.85\\textwidth", "0.75\\textwidth"),
    "feature_importance_mutual_info.png": ("0.85\\textwidth", "0.75\\textwidth"),
    "pair_plot_by_aqi_level.png": ("0.9\\textwidth", "0.75\\textwidth"),
}

with open("docs/documentation.tex", encoding="utf-8") as f:
    text = f.read()

for img, (old_w, new_w) in shrink_map.items():
    pattern = r"\\includegraphics\[width=" + re.escape(old_w) + r"\]\{" + re.escape(img) + r"\}"
    replacement = r"\\includegraphics[width=" + new_w + r"]{" + img + r"}"
    text = re.sub(pattern, replacement, text)

with open("docs/documentation.tex", "w", encoding="utf-8") as f:
    f.write(text)
