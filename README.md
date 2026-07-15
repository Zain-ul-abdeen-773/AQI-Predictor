---
title: AQI Predictor
emoji: 📊
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# 🌬️ Pearls AQI Predictor

**Enterprise-grade, end-to-end Air Quality Index prediction system for Sargodha, Pakistan.**

A 100% serverless ML pipeline that forecasts AQI 3 days into the future using multi-model architectures (Ridge, LightGBM, Bi-LSTM with Attention), SHAP explainability, and a premium dark-mode dashboard.

---

## 🏗️ Architecture

```
External APIs (AQICN, OpenWeather)
        │
        ▼
┌─────────────────────┐     ┌──────────────────┐
│   Data Pipeline      │────▶│  Hopsworks       │
│  (Ingest + Features) │     │  Feature Store   │
└─────────────────────┘     └────────┬─────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │ Training Pipeline │
                            │ Ridge│LightGBM│LSTM│
                            └────────┬─────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Model Registry   │
                            └────────┬─────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                                  ▼
           ┌──────────────┐                   ┌──────────────┐
           │  FastAPI      │                   │  Frontend    │
           │  /predict     │◀──────────────────│  (Vanilla    │
           │  /explain     │                   │   HTML/JS)   │
           └──────────────┘                   └──────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repository-url>
cd "AQI Predictor"

# Install dependencies (no virtualenv needed)
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Generate Training Data (Backfill)

```bash
python -m data_pipeline.backfill --years 2
```

### 4. Train Models

```bash
python -m training_pipeline.train
```

### 5. Launch Application

```bash
# Start API server (serves both backend and frontend)
uvicorn deployment.api.main:app --reload --port 8000

# Open in browser
# http://localhost:8000
```

### 6. Using Docker

```bash
docker-compose up --build
# App is available at: http://localhost:8000
# API Docs are at:     http://localhost:8000/docs
```

---

## 📂 Project Structure

```
├── config/                    # Pydantic Settings & Schemas
├── data_pipeline/             # Raw ingestion & feature engineering
├── feature_pipeline/          # Hopsworks Feature Store integration
├── training_pipeline/         # Multi-model ML training
│   └── models/                # Ridge, LightGBM, Bi-LSTM
├── deployment/
│   ├── api/                   # FastAPI backend
│   └── frontend/              # HTML/CSS/JS frontend
├── infrastructure/
│   ├── terraform/             # AWS IaC (Lambda, ECS, EventBridge)
│   └── validation_agents/     # LangGraph validation pipeline
├── tests/                     # Comprehensive test suite
├── .github/workflows/         # CI/CD (hourly + daily)
├── Dockerfile                 # Multi-stage container
└── docker-compose.yml         # API + Dashboard services
```

---

## 🧠 Models

| Model | Architecture | Use Case |
|-------|-------------|----------|
| **Ridge Regression** | Linear + RobustScaler | Statistical baseline |
| **LightGBM** | Gradient boosting + Optuna HPO | Tabular prediction champion |
| **Bi-LSTM + Attention** | PyTorch sequence model | 72h→72h temporal forecasting |
| **Ensemble** | Meta-learner stacking | Combined prediction |

---

## 🔧 Feature Engineering

- **Temporal**: Cyclical sin/cos encoding (hour, day, month)
- **AQI Derivatives**: Change rate over 1h, 3h, 6h windows
- **Wind-Pollutant Interaction**: U/V decomposition × PM2.5/PM10
- **Boundary Layer Proxy**: Temperature-Humidity Index (THI)
- **Thermal Inversion Detection**: Atmospheric trapping conditions
- **Lag Features**: t-1, t-3, t-6, t-12, t-24 autoregressive
- **Rolling Statistics**: 6h and 24h mean/std of PM2.5

---

## 🎯 Advanced Features

- ✅ SHAP explainability (TreeExplainer + GradientExplainer)
- ✅ Asymmetric loss (penalizes hazardous under-predictions)
- ✅ PSI-based data drift detection
- ✅ Isolation Forest anomaly detection
- ✅ Conformal prediction intervals (80% + 95%)
- ✅ Regional news sentiment integration
- ✅ LangGraph multi-agent infrastructure validation
- ✅ Health advisory alerts with municipal recommendations

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health & readiness |
| `POST` | `/predict` | 72-hour AQI forecast |
| `POST` | `/explain` | SHAP feature contributions |
| `GET` | `/historical?hours=168` | Historical AQI data |
| `GET` | `/docs` | Swagger UI documentation |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_data_pipeline.py -v
pytest tests/test_training_pipeline.py -v
pytest tests/test_api.py -v
```

---

## 🏭 Infrastructure

### Terraform (AWS Serverless)
- **Lambda**: Hourly feature pipeline execution
- **ECS Fargate**: Daily model training
- **EventBridge**: Automated scheduling
- **SSM Parameter Store**: Encrypted API key management
- **ECR**: Container image registry

### LangGraph Validation
```bash
python -m infrastructure.validation_agents.validate
```
Runs: Linter → Security (Checkov) → Policy (OPA/Rego) → Decision

---

## 📊 Dashboard

Premium dark-mode web interface served directly via FastAPI featuring:
- 🎯 Animated AQI gauge with color-coded severity (CSS animations)
- 📈 3-day interactive Plotly.js forecast with prediction intervals
- 🔍 SHAP feature contribution visualization
- 📰 Regional news feed with risk assessment
- ⚠️ Health advisory alerts for hazardous conditions

---

## 📜 License

MIT License — Built for the Pearls Engineering Program.
