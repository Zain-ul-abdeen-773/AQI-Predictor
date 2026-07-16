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

**Enterprise-grade Air Quality Index forecasting system for Sargodha, Pakistan**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![AWS](https://img.shields.io/badge/AWS-Serverless-FF9900.svg)](https://aws.amazon.com/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC.svg)](https://www.terraform.io/)

[Live Demo](https://huggingface.co/spaces/Zain-773/AQI-Predictor) | [API Docs](https://huggingface.co/spaces/Zain-773/AQI-Predictor/docs)

</div>

---

## Overview

Pearls AQI Predictor is a production-ready, end-to-end machine learning system that forecasts Air Quality Index (AQI) **72 hours (3 days)** into the future for Sargodha, Pakistan (32.08N, 72.67E). It features a multi-model architecture with 8 trained models, SHAP-based explainability, real-time data ingestion, and a serverless AWS deployment pipeline.

Built as a competitive submission for the **Pearls Engineering Program**, this project demonstrates full-stack MLOps proficiency spanning data engineering, model development, infrastructure-as-code, and production deployment.

---

## Architecture

```
                    ┌──────────────────────────────────┐
                    │        External Data Sources       │
                    │   AQICN API  |  OpenWeatherMap     │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │         Data Pipeline             │
                    │  Ingestion → Feature Engineering  │
                    │  (Hourly via AWS Lambda)          │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │      Feature Store (Parquet)      │
                    │   Partitioned by year (2021-2026) │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │       Training Pipeline           │
                    │  8 Models + Optuna HPO + SHAP     │
                    │  (Daily via ECS Fargate)          │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │        Model Registry             │
                    │  Versioning + Champion Promotion  │
                    └──────────────┬───────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                                         │
   ┌──────────▼──────────┐              ┌──────────────▼──────────┐
   │     FastAPI Server    │              │    Frontend Dashboard    │
   │  /predict /explain    │◄─────────────│  Plotly.js + Dark Mode   │
   │  /health /historical  │              │  AQI Gauge + Advisories  │
   └───────────────────────┘              └─────────────────────────┘
```

---

## Key Features

| Category | Details |
|----------|---------|
| **Multi-Model Zoo** | 8 trained models: Ridge, ElasticNet, Random Forest, Extra Trees, Gradient Boosting, SVR, LightGBM (Optuna), XGBoost (Optuna), Bi-LSTM + Multi-Head Attention |
| **Explainability** | SHAP TreeExplainer/GradientExplainer + Temporal Grad-CAM for LSTM |
| **Drift Detection** | Population Stability Index (PSI) monitoring |
| **Anomaly Detection** | Isolation Forest for outlier identification |
| **Prediction Intervals** | Conformal prediction at 80% and 95% confidence |
| **Health Advisories** | AQI-based alerts with municipal recommendations |
| **Infrastructure Validation** | LangGraph multi-agent pipeline (Linter, Checkov, OPA/Rego) |
| **CI/CD** | GitHub Actions (hourly ingestion + daily training) + AWS CodePipeline |
| **Serverless Deployment** | AWS Lambda (API) + ECS Fargate (training) + EventBridge (scheduling) |

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11, FastAPI, Uvicorn, Mangum |
| **ML/DL** | scikit-learn, LightGBM, XGBoost, PyTorch, Optuna |
| **Data** | Pandas, NumPy, SciPy, aiohttp |
| **Explainability** | SHAP, Custom Grad-CAM |
| **Frontend** | HTML/CSS/JS (primary), Next.js 16 + React 19 (alternative) |
| **Visualization** | Plotly.js, Matplotlib |
| **Infrastructure** | Terraform, Docker, AWS (Lambda, ECS, ECR, EventBridge, SSM) |
| **Validation** | LangGraph, LangChain, OPA/Rego |
| **CI/CD** | GitHub Actions, AWS CodePipeline, AWS CodeBuild |
| **Configuration** | Pydantic v2, pydantic-settings, python-dotenv |
| **Testing** | pytest, pytest-asyncio, httpx |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- API keys: [AQICN](https://aqicn.org/data-platform/token/) (free) and [OpenWeatherMap](https://openweathermap.org/api) (free tier)

### Installation

```bash
git clone https://github.com/Zain-ul-abdeen-773/AQI-Predictor.git
cd AQI-Predictor

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
AQICN_API_KEY=your_aqicn_token
OPENWEATHER_API_KEY=your_openweather_key
```

### Generate Training Data

```bash
# Backfill historical data (synthetic generation for development)
python -m data_pipeline.backfill --years 2
```

### Train Models

```bash
# Train all 8 models (including Bi-LSTM with Attention)
python -m training_pipeline.train

# Train specific models only
python -m training_pipeline.train --models Ridge LightGBM XGBoost

# Skip LSTM for faster iteration
python -m training_pipeline.train --skip-lstm
```

### Launch Application

```bash
uvicorn deployment.api.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) for the dashboard, or [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger API documentation.

### Docker Deployment

```bash
docker-compose up --build
```

---

## Project Structure

```
.
├── config/                         # Application configuration
│   ├── settings.py                 #   Pydantic BaseSettings (env loading)
│   └── schemas.py                  #   Request/response validation schemas
│
├── data_pipeline/                  # Data ingestion & engineering
│   ├── ingest.py                   #   Real-time AQICN + OpenWeather API client
│   ├── backfill.py                 #   Historical data generation (5 years)
│   └── transformers.py             #   Feature engineering (37 features)
│
├── feature_pipeline/               # Feature store management
│   └── register.py                 #   Hopsworks/local Parquet store
│
├── training_pipeline/              # Model training & evaluation
│   ├── train.py                    #   Training orchestrator
│   ├── evaluation.py               #   Metrics, drift detection, anomaly detection
│   ├── explainability.py           #   SHAP analysis
│   ├── registry.py                 #   Model versioning & promotion
│   └── models/                     #   Model implementations
│       ├── baseline.py             #     Ridge / ElasticNet
│       ├── ensemble_trees.py       #     RF, ExtraTrees, GBR, SVR
│       ├── tree_ensemble.py        #     LightGBM + Optuna
│       ├── xgboost_model.py        #     XGBoost + Optuna
│       ├── deep_learning.py        #     Bi-LSTM + Multi-Head Attention
│       ├── grad_cam.py             #     Temporal Grad-CAM
│       └── callbacks.py            #     Training callbacks
│
├── deployment/                     # Application serving
│   ├── api/                        #   FastAPI backend
│   │   ├── main.py                 #     App entry point & routes
│   │   ├── dependencies.py         #     Dependency injection
│   │   └── middleware.py           #     CORS, rate limiting, error handling
│   ├── frontend/                   #   Vanilla HTML/JS/CSS dashboard
│   │   ├── index.html
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── web_app/                    #   Next.js 16 alternative frontend
│
├── infrastructure/                 # Cloud infrastructure
│   ├── terraform/                  #   AWS IaC (Lambda, ECS, ECR, EventBridge)
│   │   ├── main.tf
│   │   ├── pipeline.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── validation_agents/          #   LangGraph multi-agent validation
│       ├── validate.py             #     Orchestrator
│       ├── agents/                 #     Linter, Security, Policy agents
│       └── policies/               #     OPA Rego policies
│
├── data/                           # Data storage
│   ├── feature_store/              #   Partitioned Parquet (year=YYYY/)
│   └── backfill_features.csv       #   Generated training data
│
├── models/                         # Trained model artifacts
│   └── sargodha_aqi_forecast_model/
│       └── <timestamp>/            #   model.pkl, metadata.json, metrics.json
│
├── tests/                          # Test suite
│   ├── test_api.py
│   ├── test_data_pipeline.py
│   ├── test_feature_pipeline.py
│   ├── test_training_pipeline.py
│   └── test_validation.py
│
├── .github/workflows/              # CI/CD pipelines
│   ├── feature_pipeline_cron.yml   #   Hourly data ingestion
│   └── training_pipeline_cron.yml  #   Daily model retraining
│
├── Dockerfile                      # Multi-stage Python 3.11 build
├── docker-compose.yml              # Container orchestration
├── buildspec.yml                   # AWS CodeBuild specification
├── requirements.txt                # Python dependencies
└── pyproject.toml                  # Project metadata & tool config
```

---

## Models

### Model Zoo (8 Models)

| Model | Type | Description | Hyperparameter Tuning |
|-------|------|-------------|----------------------|
| Ridge Regression | Linear | L2-regularized baseline with RobustScaler | Grid search |
| ElasticNet | Linear | L1+L2 regularization | Grid search |
| Random Forest | Ensemble | Bagged decision trees | Default |
| Extra Trees | Ensemble | Randomized split selection | Default |
| Gradient Boosting | Ensemble | Sequential boosting | Default |
| SVR | Kernel | RBF kernel support vectors | Default |
| LightGBM | GBDT | Gradient boosting with leaf-wise growth | Optuna (50 trials) |
| XGBoost | GBDT | Gradient boosting with level-wise growth | Optuna (50 trials) |
| Bi-LSTM + Attention | Deep Learning | Bidirectional LSTM with Multi-Head Attention | Manual + callbacks |

### Model Selection

The training pipeline automatically evaluates all models and promotes the best performer (lowest RMSE) as the **champion model**. Users can select any model from the zoo via the API or dashboard.

---

## Feature Engineering

The system engineers **37 features** from raw pollutant and weather data:

| Feature Group | Features | Description |
|---------------|----------|-------------|
| **Temporal** | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`, `month_sin`, `month_cos` | Cyclical encoding preserving periodicity |
| **AQI Derivatives** | `aqi_change_1h`, `aqi_change_3h`, `aqi_change_6h` | Rate of change at multiple horizons |
| **Wind-Pollutant** | `wind_u_pm25`, `wind_v_pm25`, `wind_u_pm10`, `wind_v_pm10` | U/V decomposition x pollutant interaction |
| **Atmospheric** | `temp_humidity_index`, `thermal_inversion` | Boundary layer and inversion detection |
| **Lag Features** | `aqi_lag_6h`, `aqi_lag_12h`, `aqi_lag_24h` | Autoregressive inputs (leakage-safe) |
| **Rolling Stats** | `pm25_rolling_mean_6h`, `pm25_rolling_std_6h`, `pm25_rolling_mean_24h` | Short/long-term trends |

> **Leakage Prevention**: Short-horizon lags (1h, 3h) are deliberately excluded from the feature set to prevent information leakage in the 72-hour forecasting context.

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard UI |
| `GET` | `/health` | Service health check and readiness status |
| `GET` | `/models` | List all available models with performance metrics |
| `POST` | `/predict?model_id=<id>` | Generate 72-hour AQI forecast |
| `POST` | `/explain` | SHAP feature contribution analysis |
| `GET` | `/historical?hours=168` | Historical AQI observations |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/redoc` | ReDoc API documentation |

### Example Request

```bash
# Get 72-hour forecast using the champion model
curl -X POST http://localhost:8000/predict

# Get forecast from a specific model
curl -X POST "http://localhost:8000/predict?model_id=lightgbm"

# Get SHAP explanations
curl -X POST http://localhost:8000/explain

# Check service health
curl http://localhost:8000/health
```

### Example Response (`/predict`)

```json
{
  "model_id": "ridge",
  "forecast_hours": 72,
  "predictions": [
    {"hour": 1, "aqi": 142.5, "category": "Unhealthy for Sensitive Groups"},
    {"hour": 2, "aqi": 145.1, "category": "Unhealthy for Sensitive Groups"},
    ...
  ],
  "confidence_intervals": {
    "80_pct": {"lower": [...], "upper": [...]},
    "95_pct": {"lower": [...], "upper": [...]}
  },
  "health_advisory": "Sensitive groups should reduce prolonged outdoor exertion."
}
```

---

## Infrastructure

### AWS Serverless Architecture

| Service | Purpose | Trigger |
|---------|---------|---------|
| **Lambda** (Feature Pipeline) | Hourly data ingestion from AQICN + OpenWeather | EventBridge (cron) |
| **ECS Fargate** (Training) | Daily model retraining on latest data | EventBridge (daily) |
| **Lambda** (API) | Serve predictions via Function URL | HTTP requests |
| **ECR** | Docker image registry | CodeBuild push |
| **SSM Parameter Store** | Encrypted API key management | Runtime access |
| **CodePipeline** | Automated build and deploy | GitHub webhook |

### Terraform Provisioning

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### Infrastructure Validation (LangGraph)

A multi-agent system validates infrastructure changes before deployment:

```bash
python -m infrastructure.validation_agents.validate
```

**Agents:**
1. **Linter Agent** - Terraform syntax and best practices
2. **Security Agent** - Checkov security scanning
3. **Policy Agent** - OPA/Rego organizational policy enforcement
4. **Decision Agent** - Final pass/fail determination

---

## Testing

```bash
# Run full test suite
pytest tests/ -v

# Run specific modules
pytest tests/test_api.py -v
pytest tests/test_data_pipeline.py -v
pytest tests/test_training_pipeline.py -v
pytest tests/test_feature_pipeline.py -v
pytest tests/test_validation.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

---

## CI/CD Pipelines

### GitHub Actions

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `feature_pipeline_cron.yml` | Every hour | Ingest latest AQI + weather data |
| `training_pipeline_cron.yml` | Daily at 02:00 UTC | Retrain models on fresh data |
| `infra_validation.yml` | On PR to `main` | Validate Terraform changes |

### AWS CodePipeline

Triggered on push to `main`:
1. **Source** - Pull from GitHub
2. **Build** - Docker build + push to ECR
3. **Deploy** - Update Lambda/ECS with new image

---

## Dashboard

The frontend provides a premium dark-mode interface with:

- **AQI Gauge** - Animated radial gauge with EPA color-coded severity levels
- **72-Hour Forecast Chart** - Interactive Plotly.js visualization with confidence bands
- **Model Selector** - Switch between all 8 trained models in real time
- **SHAP Visualization** - Feature contribution bar charts for prediction transparency
- **Health Advisories** - Context-aware alerts based on predicted AQI levels
- **Responsive Design** - Optimized for desktop and mobile viewports

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AQICN_API_KEY` | AQICN data platform token | `demo` |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | - |
| `AWS_REGION` | AWS deployment region | `us-east-1` |
| `TARGET_CITY` | Forecast target city | `Sargodha` |
| `FORECAST_HORIZON_HOURS` | Prediction window | `72` |
| `LOOKBACK_WINDOW_HOURS` | Input sequence length | `72` |
| `AQI_ALERT_THRESHOLD` | Health alert trigger level | `150` |
| `LSTM_HIDDEN_SIZE` | LSTM hidden dimension | `128` |
| `LSTM_NUM_LAYERS` | LSTM layer count | `2` |
| `OPTUNA_N_TRIALS` | HPO trial budget | `50` |
| `FASTAPI_PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Run tests (`pytest tests/ -v`)
4. Commit changes (`git commit -m "feat: add my feature"`)
5. Push to branch (`git push origin feature/my-feature`)
6. Open a Pull Request

---

## License

This project is licensed under the MIT License. Built for the [Pearls Engineering Program](https://pearls.tech).

---

<div align="center">

**Developed by [Zain ul Abdeen](https://github.com/Zain-ul-abdeen-773)**

</div>
