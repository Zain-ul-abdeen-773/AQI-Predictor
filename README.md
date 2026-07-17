---
title: AQI Predictor App
emoji: "\U0001F4CA"
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

<div align="center">

# Pearls AQI Predictor

**End-to-end Air Quality Index forecasting system for Sargodha, Pakistan**

Predicting AQI 72 hours (3 days) into the future using a serverless ML pipeline

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000.svg)](https://flask.palletsprojects.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-ee4c2c.svg)](https://pytorch.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io)
[![ClearML](https://img.shields.io/badge/ClearML-1.14+-2D9CDB.svg)](https://clear.ml)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![AWS](https://img.shields.io/badge/AWS-Serverless-FF9900.svg)](https://aws.amazon.com/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC.svg)](https://www.terraform.io/)

[Live Demo](https://huggingface.co/spaces/Zain-773/AQI-Predictor)

</div>

---

## Overview

Pearls AQI Predictor is a production-ready, end-to-end machine learning system that forecasts Air Quality Index (AQI) **72 hours (3 days)** into the future for Sargodha, Pakistan (32.08N, 72.67E). The system features:

- **8 ML models** spanning linear, ensemble, gradient boosting, and deep learning approaches
- **Automated pipelines** for hourly data ingestion and daily model retraining
- **ClearML** as the Feature Store and experiment tracking platform
- **SHAP-based explainability** with Temporal Grad-CAM for deep learning models
- **Serverless AWS deployment** via Terraform infrastructure-as-code
- **Interactive dashboards** with Streamlit + Flask API backend

Built for the **Pearls Engineering Program** to demonstrate full-stack MLOps proficiency.

---

## System Architecture

```mermaid
flowchart TB
    subgraph Sources[Data Sources]
        A1[AQICN API]
        A2[OpenWeatherMap API]
    end

    subgraph FP[Feature Pipeline - Hourly]
        B1[Async Data Ingestion]
        B2[Feature Engineering - 37 features]
        B3[ClearML Feature Store]
    end

    subgraph TP[Training Pipeline - Daily]
        C1[Extract Training Data]
        C2[Train 9 Models + Optuna HPO]
        C3[Evaluate: RMSE, MAE, R2]
        C4[SHAP + LIME Explainability]
        C5[ClearML Model Registry]
    end

    subgraph SV[Serving Layer]
        D1[Flask REST API]
        D2[Streamlit Dashboard]
    end

    subgraph AWS[AWS Serverless - Terraform]
        E1[Lambda - Feature Pipeline]
        E2[Lambda - API Service]
        E3[ECS Fargate - Training]
        E4[EventBridge Scheduler]
        E5[ECR + SSM + CloudWatch]
    end

    subgraph VA[Infra Validation - LangGraph]
        F1[Linter Agent]
        F2[Security Agent - Checkov]
        F3[Policy Agent - OPA/Rego]
        F4[Decision Agent]
    end

    A1 --> B1
    A2 --> B1
    B1 --> B2
    B2 --> B3

    B3 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5

    C5 --> D1
    B3 --> D1
    D1 --> D2

    E4 --> E1
    E4 --> E3
    E1 -.- FP
    E2 -.- D1
    E3 -.- TP

    F1 --> F4
    F2 --> F4
    F3 --> F4
```

---

## Key Features

| Category | Details |
|----------|---------|
| **Multi-Model Zoo** | 9 models: Ridge, ElasticNet, Random Forest, Extra Trees, Gradient Boosting, SVR, LightGBM (Optuna), XGBoost (Optuna), Bi-LSTM + Multi-Head Attention |
| **Feature Store** | ClearML Dataset versioning with local Parquet (Hive-partitioned by year/month) |
| **Experiment Tracking** | ClearML for model registry, metrics logging, and artifact management |
| **Explainability** | SHAP TreeExplainer + GradientExplainer, LIME TabularExplainer, Temporal Grad-CAM |
| **Drift Detection** | Population Stability Index (PSI) monitoring across all features |
| **Anomaly Detection** | Isolation Forest for outlier identification in incoming data |
| **Health Advisories** | AQI-based alerts with context-aware recommendations |
| **Infrastructure Validation** | LangGraph multi-agent pipeline (Linter, Checkov, OPA/Rego) |
| **CI/CD** | GitHub Actions (hourly ingestion + daily training) + AWS CodePipeline |
| **Serverless Deployment** | AWS Lambda (API) + ECS Fargate (training) + EventBridge (scheduling) |

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **API Backend** | Python 3.11, Flask 3.0+, flask-cors |
| **Dashboard** | Streamlit 1.30+, Plotly 5.15+ |
| **ML/DL** | scikit-learn, LightGBM, XGBoost, PyTorch 2.2+, Optuna |
| **Feature Store** | ClearML 1.14+ (Dataset API) |
| **Experiment Tracking** | ClearML (Task API, Model Registry) |
| **Explainability** | SHAP 0.42+, LIME 0.2+, Custom Temporal Grad-CAM |
| **Data Engineering** | Pandas, NumPy, SciPy, aiohttp, tenacity |
| **Infrastructure** | Terraform, Docker, AWS (Lambda, ECS, ECR, EventBridge, SSM) |
| **Validation** | LangGraph, LangChain, OPA/Rego, Checkov |
| **CI/CD** | GitHub Actions, AWS CodePipeline/CodeBuild |
| **Configuration** | Pydantic v2, pydantic-settings, python-dotenv |
| **Testing** | pytest, pytest-asyncio, httpx |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)
- API keys: [AQICN](https://aqicn.org/data-platform/token/) and [OpenWeatherMap](https://openweathermap.org/api)
- ClearML account (free tier): [app.clear.ml](https://app.clear.ml)

### Installation

```bash
git clone https://github.com/Zain-ul-abdeen-773/AQI-Predictor.git
cd AQI-Predictor

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
AQICN_API_KEY=your_aqicn_token
OPENWEATHER_API_KEY=your_openweather_key
CLEARML_API_ACCESS_KEY=your_clearml_key
CLEARML_API_SECRET_KEY=your_clearml_secret
```

### Generate Training Data

```bash
python -m data_pipeline.backfill --years 5
```

### Train Models

```bash
# Train all models
python -m training_pipeline.train

# Train from CSV directly
python -m training_pipeline.train --csv
```

### Launch Application

```bash
# Start Flask API
flask --app deployment.api.main:app run --port 8000

# Start Streamlit dashboard (separate terminal)
streamlit run deployment/streamlit_app/app.py
```

### Docker Deployment

```bash
docker-compose up --build
```

---

## Project Structure

```
.
├── config/                         # Application configuration
│   ├── settings.py                 #   Pydantic BaseSettings (all env vars + hyperparams)
│   └── schemas.py                  #   Pydantic validation schemas (467 lines)
│
├── eda/                            # Exploratory Data Analysis
│   ├── run_eda.py                  #   10-stage base EDA pipeline
│   ├── advanced_eda.py             #   9-stage advanced statistical analysis
│   ├── EDA_Analysis.ipynb          #   Interactive Jupyter notebook (13 sections)
│   ├── plots/                      #   20 PNG visualizations
│   └── reports/                    #   26 CSV/JSON statistical reports
│
├── data_pipeline/                  # Data ingestion & feature engineering
│   ├── ingest.py                   #   Async AQICN + OpenWeather client (aiohttp + tenacity)
│   ├── backfill.py                 #   5-year historical data generation
│   └── transformers.py             #   37-feature engineering (temporal, lag, rolling, interactions)
│
├── feature_pipeline/               # Feature store management
│   └── register.py                 #   ClearML Dataset + local Parquet store
│
├── training_pipeline/              # Model training & evaluation
│   ├── train.py                    #   Training orchestrator (9 models)
│   ├── evaluation.py               #   Metrics + PSI drift + Isolation Forest anomaly
│   ├── explainability.py           #   SHAP TreeExplainer + GradientExplainer
│   ├── registry.py                 #   ClearML model versioning & champion promotion
│   └── models/
│       ├── baseline.py             #     Ridge / ElasticNet
│       ├── ensemble_trees.py       #     RF, ExtraTrees, GBR, SVR
│       ├── tree_ensemble.py        #     LightGBM + Optuna (50 trials)
│       ├── xgboost_model.py        #     XGBoost + Optuna (50 trials)
│       ├── deep_learning.py        #     Bi-LSTM + Multi-Head Attention (PyTorch)
│       ├── grad_cam.py             #     Temporal Grad-CAM explainability
│       └── callbacks.py            #     EarlyStopping, Checkpointing, LR scheduling
│
├── deployment/                     # Serving layer
│   ├── api/
│   │   ├── main.py                 #     Flask REST API (5 endpoints)
│   │   └── dependencies.py         #     Model/feature service loading
│   └── streamlit_app/
│       └── app.py                  #     Interactive Streamlit dashboard (Plotly)
│
├── infrastructure/                 # Cloud infrastructure
│   ├── terraform/                  #   AWS IaC (Lambda, ECS, ECR, EventBridge, SSM)
│   │   ├── main.tf                 #     Core resources
│   │   ├── pipeline.tf             #     CodePipeline/CodeBuild
│   │   ├── provider.tf             #     AWS provider
│   │   ├── variables.tf            #     Input variables
│   │   └── outputs.tf              #     Output values
│   └── validation_agents/          #   LangGraph multi-agent validation
│       ├── validate.py             #     Orchestrator (Linter → Security → Policy → Decision)
│       ├── agents/                 #     4 specialized agents
│       └── policies/               #     OPA Rego compliance rules
│
├── data/                           # Data storage
│   ├── feature_store/              #   Hive-partitioned Parquet (year=YYYY/month=M/)
│   └── backfill_features.csv       #   43,801 rows historical features
│
├── models/                         # Trained model artifacts
│   ├── training_report.json        #   Model comparison report
│   └── sargodha-aqi-forecast-model/
│       └── <timestamp>/            #   model.pkl, metadata.json, metrics.json, params.json
│
├── tests/                          # pytest test suite
│   ├── test_api.py
│   ├── test_data_pipeline.py
│   ├── test_feature_pipeline.py
│   ├── test_training_pipeline.py
│   └── test_validation.py
│
├── .github/workflows/              # CI/CD automation
│   ├── feature_pipeline_cron.yml   #   Hourly: ingest → transform → ClearML push
│   ├── training_pipeline_cron.yml  #   Daily 2AM: train → evaluate → registry
│   └── infra_validation.yml        #   On PR: LangGraph validation
│
├── Dockerfile                      # Multi-stage Python 3.11 build
├── docker-compose.yml              # Container orchestration
├── requirements.txt                # Python dependencies
└── pyproject.toml                  # Project metadata & tool config
```

---

## Models

### Model Zoo

| Model | Type | HPO | Description |
|-------|------|-----|-------------|
| Ridge Regression | Linear | Grid | L2-regularized with RobustScaler |
| ElasticNet | Linear | Grid | L1+L2 combined regularization |
| Random Forest | Ensemble | Default | Bagged decision trees |
| Extra Trees | Ensemble | Default | Extremely randomized trees |
| Gradient Boosting | Ensemble | Default | Sequential boosting |
| SVR | Kernel | Default | RBF kernel support vectors |
| LightGBM | GBDT | Optuna (50 trials) | Leaf-wise growth, TimeSeriesSplit CV |
| XGBoost | GBDT | Optuna (50 trials) | Level-wise growth, TimeSeriesSplit CV |
| Bi-LSTM + Attention | Deep Learning | Callbacks | Bidirectional LSTM + Multi-Head Self-Attention (PyTorch) |

### Current Performance

| Model | RMSE | MAE | R-squared | MAPE |
|-------|------|-----|-----------|------|
| **Ridge (Champion)** | **5.77** | **4.50** | **0.903** | **9.23%** |
| ElasticNet | 6.59 | 4.50 | 0.874 | 9.37% |
| Random Forest | 7.58 | 5.18 | 0.833 | 10.33% |
| Extra Trees | 7.37 | 5.24 | 0.843 | 10.45% |
| Gradient Boosting | 8.10 | 6.30 | 0.810 | 13.89% |

The training pipeline automatically evaluates all models and promotes the best performer (lowest RMSE) as the **champion model**. Champion selection is logged in ClearML.

---

## Feature Engineering

The system engineers **37 features** from raw pollutant and weather data:

| Feature Group | Features | Description |
|---------------|----------|-------------|
| **Cyclical Temporal** | `hour_sin/cos`, `day_sin/cos`, `month_sin/cos` | Preserves periodicity without discontinuities |
| **AQI Change Rate** | `aqi_change_1h`, `aqi_change_3h`, `aqi_change_6h` | Rate of change at multiple horizons |
| **Wind-Pollutant** | `wind_u_pm25`, `wind_v_pm25`, `wind_u_pm10`, `wind_v_pm10` | Vector decomposition x pollutant interaction |
| **Atmospheric** | `temp_humidity_index`, `thermal_inversion_flag` | Boundary layer and inversion detection |
| **Lag Features** | `aqi_lag_6h`, `aqi_lag_12h`, `aqi_lag_24h` | Autoregressive inputs (leakage-safe) |
| **Rolling Stats** | `pm25_rolling_mean_6h`, `pm25_rolling_std_6h`, `pm25_rolling_mean_24h` | Short/long-term statistical trends |
| **Pollution Index** | `pollution_intensity` | Composite normalized pollutant score |

> **Leakage Prevention**: Short-horizon lags (1h, 3h) are excluded from training features to prevent information leakage in the 72-hour forecasting context.

---

## Exploratory Data Analysis

Comprehensive 19-stage EDA on **43,801 hourly observations** spanning **5 years** (2021-2026) with **47 engineered features**. The analysis includes base statistical profiling, advanced time-series diagnostics, hypothesis testing, and causal inference.

**Reproduce:** `python -m eda.run_eda && python -m eda.advanced_eda`  
**Interactive notebook:** `eda/EDA_Analysis.ipynb`

### Dataset Summary

| Metric | Value |
|--------|-------|
| Total Observations | 43,801 (hourly) |
| Time Span | 2021-07-16 to 2026-07-15 |
| Engineered Features | 47 columns |
| Missing Values | 0 (0.0%) |
| Mean AQI | 120.0 |
| Max AQI Recorded | 279.7 |
| Hazardous Hours (AQI > 150) | 16,085 (36.72%) |

### AQI Category Distribution

![AQI Category Distribution](eda/plots/aqi_category_distribution.png)

Over a third of all hours fall in unhealthy or worse categories, highlighting the critical need for accurate forecasting in Sargodha.

### Pollutant Distributions

![Pollutant Distributions](eda/plots/pollutant_distributions.png)

Non-Gaussian distributions with heavy right tails across all pollutants. D'Agostino-Pearson normality tests confirm non-normality (p < 0.001), justifying ensemble and non-parametric model selection.

### Empirical CDF with EPA Thresholds

![ECDF](eda/plots/aqi_ecdf.png)

The empirical cumulative distribution shows what percentage of time falls below each EPA AQI threshold -- critical for risk assessment and alert calibration.

### Correlation Analysis

![Correlation Heatmap](eda/plots/correlation_heatmap.png)

| Feature | Correlation with AQI |
|---------|---------------------|
| CO | 0.980 |
| PM10 | 0.963 |
| NO2 | 0.951 |
| SO2 | 0.951 |
| O3 | -0.947 |

![AQI vs Top Features](eda/plots/aqi_scatter_top_features.png)

### Pair Plot by AQI Level

![Pair Plot](eda/plots/pair_plot_by_aqi_level.png)

Multi-variable pair plot colored by AQI severity category reveals clustering patterns and non-linear relationships between pollutants and weather.

### Temporal Patterns

![Temporal Patterns](eda/plots/temporal_patterns.png)

- **Diurnal**: AQI peaks overnight (boundary layer collapse) and improves midday (convective mixing)
- **Weekly**: Slight weekday/weekend variation from traffic patterns
- **Seasonal**: Strong winter peaks from thermal inversions and biomass burning
- **Yearly**: Slight upward trend over the 5-year period

### Hour x Month AQI Heatmap

![Hour Month Heatmap](eda/plots/hour_month_heatmap.png)

2D heatmap identifies pollution hotspots -- winter nights (Nov-Jan, 22:00-06:00) consistently show the highest AQI values due to thermal inversions and reduced atmospheric mixing.

### Monthly Time Series

![Monthly AQI Time Series](eda/plots/monthly_aqi_timeseries.png)

### Seasonal Decomposition & Stationarity

![Seasonal Decomposition](eda/plots/seasonal_decomposition.png)

**Augmented Dickey-Fuller Test:**
- ADF Statistic: -2.12 (critical 5%: -2.86)
- p-value: 0.237 -- series is **non-stationary**
- Implication: Autoregressive features (lags, rolling stats) are essential

### Autocorrelation Analysis (ACF/PACF)

![ACF PACF](eda/plots/acf_pacf_analysis.png)

- Slow ACF decay confirms non-stationarity
- PACF cuts off after lag 1-2, suggesting AR(1) or AR(2) process
- Periodic bumps at lag 7 and 30 indicate weekly and monthly cycles

![Hourly ACF](eda/plots/hourly_acf_168h.png)

Strong 24-hour periodicity visible in the hourly autocorrelation, confirming the importance of cyclical temporal encoding (sin/cos).

### Rolling Volatility

![Rolling Volatility](eda/plots/rolling_volatility.png)

7-day and 30-day rolling standard deviation identifies unstable periods with high AQI variability -- important for confidence interval calibration.

### Cross-Pollutant Lag Correlation

![Lag Correlation](eda/plots/cross_pollutant_lag_correlation.png)

How past pollutant values predict current AQI at different time lags. All pollutants maintain strong predictive power up to 24h, validating the use of lag features in the model.

### Weather Impact on Air Quality

![Weather-Pollutant Relationships](eda/plots/weather_pollutant_relationships.png)

**Hazardous conditions profile** (AQI > 150):
- Average temperature: 15.3 C (cooler months, inversions)
- Average humidity: 57.8%
- Average wind speed: 0.8 m/s (near-calm, poor dispersion)

### Pollution Wind Rose

![Wind Rose](eda/plots/pollution_wind_rose.png)

Directional pollution analysis reveals prevailing pollution transport patterns. AQI varies significantly by wind direction, with certain sectors consistently bringing higher pollutant loads.

### Granger Causality Tests

![Granger Causality](eda/plots/granger_causality.png)

Statistical test for whether weather variables have predictive causal power over AQI:
- **Temperature**: Granger-causes AQI (significant)
- **Wind speed**: Granger-causes AQI (significant)
- **Pressure**: Granger-causes AQI (significant)
- **Humidity**: Does NOT Granger-cause AQI

### Hypothesis Testing

![Hypothesis Tests](eda/plots/hypothesis_tests.png)

| Test | Result | p-value |
|------|--------|---------|
| Weekend vs Weekday (Mann-Whitney U) | Tested | See report |
| Seasonal Differences (Kruskal-Wallis H) | **Significant** | < 0.001 |
| Temperature-AQI (Spearman) | Negative correlation | < 0.001 |
| Day vs Night Variance (Levene's) | Heteroscedastic | < 0.05 |

### Feature Importance (Mutual Information)

![Feature Importance](eda/plots/feature_importance_mutual_info.png)

Top predictive features: `aqi_lag_1h`, `pollution_intensity`, `co`, `pm10`, `so2`

### Outlier Analysis

![Outlier Box Plots](eda/plots/outlier_boxplots.png)

### Key EDA Insights & Modeling Implications

| Finding | Modeling Implication |
|---------|---------------------|
| Non-Gaussian distributions | Use ensemble/tree-based models over linear assumptions |
| Strong multicollinearity (r > 0.95) | Regularization (Ridge/ElasticNet) or tree-based feature selection |
| Non-stationary series (ADF p=0.24) | Include lag features and rolling statistics |
| 24h periodicity in ACF | Cyclical temporal encoding (sin/cos hour features) |
| PACF cutoff at lag 2 | AR(2) component in data generating process |
| Winter peaks (thermal inversions) | Season and temperature interaction features |
| Granger causality (temp, wind, pressure) | Weather features have genuine predictive power |
| Heteroscedastic day/night variance | Separate confidence intervals by time-of-day |
| 36.7% hazardous hours | Critical need for accurate forecasting and alerts |

> **EDA Artifacts:** 20 PNG visualizations in `eda/plots/`, 26 CSV/JSON reports in `eda/reports/`, and interactive Jupyter notebook at `eda/EDA_Analysis.ipynb`

---

## API Reference

### Flask REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check and readiness |
| `POST` | `/predict` | 72-hour AQI forecast with confidence intervals |
| `POST` | `/explain` | SHAP feature contribution analysis |
| `GET` | `/historical` | Historical AQI data for charting |
| `GET` | `/models` | List available models with metrics |

### Example Usage

```bash
# Health check
curl http://localhost:8000/health

# 72-hour forecast (champion model)
curl -X POST http://localhost:8000/predict

# Forecast with specific model
curl -X POST "http://localhost:8000/predict?model_id=ridge"

# SHAP explanations
curl -X POST http://localhost:8000/explain

# Historical data
curl "http://localhost:8000/historical?hours=168"
```

### Response Format (`/predict`)

```json
{
  "model_id": "ridge",
  "forecast_hours": 72,
  "predictions": [
    {"hour": 1, "aqi": 142.5, "category": "Unhealthy for Sensitive Groups"},
    {"hour": 2, "aqi": 145.1, "category": "Unhealthy for Sensitive Groups"}
  ],
  "confidence_intervals": {
    "80_pct": {"lower": [...], "upper": [...]},
    "95_pct": {"lower": [...], "upper": [...]}
  },
  "health_advisory": "Sensitive groups should reduce prolonged outdoor exertion."
}
```

---

## Streamlit Dashboard

The interactive dashboard connects to the Flask API and provides:

- **72-Hour Forecast Chart** -- Plotly interactive line chart with 95% confidence bands
- **Model Selector** -- Switch between trained models in real time
- **Health Advisories** -- Color-coded alerts based on predicted AQI severity
- **AQI Threshold Markers** -- Visual reference lines for EPA categories

```bash
streamlit run deployment/streamlit_app/app.py
```

---

## CI/CD Pipelines

### GitHub Actions (Automated)

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `feature_pipeline_cron.yml` | Every hour | Ingest data from APIs, engineer features, push to ClearML |
| `training_pipeline_cron.yml` | Daily at 02:00 UTC | Train models, evaluate, promote champion to ClearML registry |
| `infra_validation.yml` | On PR (infra paths) | LangGraph multi-agent Terraform validation |

### Pipeline Flow

```mermaid
graph LR
    subgraph Hourly["Hourly (GitHub Actions)"]
        A[AQICN + OWM APIs] --> B[Feature Engineering]
        B --> C[ClearML Feature Store]
    end

    subgraph Daily["Daily (GitHub Actions)"]
        C --> D[Extract Training Data]
        D --> E[Train 9 Models]
        E --> F[Evaluate + SHAP]
        F --> G[Champion Promotion]
        G --> H[ClearML Model Registry]
    end

    subgraph OnPR["On PR (GitHub Actions)"]
        I[Terraform Changes] --> J[LangGraph Validation]
        J --> K[Linter + Checkov + OPA]
        K --> L[Pass/Fail Gate]
    end
```

---

## Infrastructure

### AWS Serverless (Terraform)

| Service | Purpose | Trigger |
|---------|---------|---------|
| **Lambda** | Feature pipeline (hourly ingestion) | EventBridge cron |
| **Lambda** | API service (Function URL) | HTTP requests |
| **ECS Fargate** | Training pipeline (daily) | EventBridge schedule |
| **ECR** | Docker image registry (lifecycle: 10 images) | CodeBuild push |
| **SSM Parameter Store** | Encrypted API keys | Runtime access |
| **CloudWatch** | Log aggregation (30-day retention) | All services |
| **CodePipeline** | Build + deploy automation | GitHub webhook |

### Provisioning

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### Infrastructure Validation (LangGraph)

Multi-agent system that gates infrastructure changes:

```mermaid
graph LR
    A[Terraform Plan] --> B[Linter Agent]
    B --> C[Security Agent]
    C --> D[Policy Agent]
    D --> E{Decision Agent}
    E -->|Pass| F[Deploy]
    E -->|Fail| G[Remediation Suggestions]
```

---

## Testing

```bash
# Full test suite
pytest tests/ -v

# Individual modules
pytest tests/test_api.py -v
pytest tests/test_data_pipeline.py -v
pytest tests/test_training_pipeline.py -v
pytest tests/test_feature_pipeline.py -v
pytest tests/test_validation.py -v

# With coverage
pytest tests/ --cov=. --cov-report=term-missing
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AQICN_API_KEY` | AQICN data platform token | `demo` |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | -- |
| `CLEARML_API_ACCESS_KEY` | ClearML access key | -- |
| `CLEARML_API_SECRET_KEY` | ClearML secret key | -- |
| `AWS_REGION` | AWS deployment region | `us-east-1` |
| `TARGET_CITY` | Forecast target city | `Sargodha` |
| `FORECAST_HORIZON_HOURS` | Prediction window | `72` |
| `LOOKBACK_WINDOW_HOURS` | Input sequence length | `72` |
| `AQI_ALERT_THRESHOLD` | Health alert trigger | `150` |
| `LSTM_HIDDEN_SIZE` | LSTM hidden dimension | `128` |
| `LSTM_NUM_LAYERS` | LSTM layer count | `2` |
| `OPTUNA_N_TRIALS` | HPO trial budget | `50` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## License

This project is licensed under the MIT License. Built for the [Pearls Engineering Program](https://pearls.tech).

---

<div align="center">

**Developed by [Zain ul Abdeen](https://github.com/Zain-ul-abdeen-773)**

</div>
