# Contributing to AQI Predictor

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+ (for frontend)
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Zain-ul-abdeen-773/AQI-Predictor.git
cd AQI-Predictor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp config/.env.example .env
# Edit .env with your API keys (AQICN_API_KEY required for live data)

# Verify installation
python -c "from config.settings import get_settings; print('OK')"
python -c "from deployment.api.main import app; print('Flask OK')"
```

### Frontend Setup

```bash
cd deployment/web_app
npm install
npm run dev   # Starts on http://localhost:3000
```

### Running Tests

```bash
# Backend tests
python -m pytest tests/ -v --tb=short

# With coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Frontend tests
cd deployment/web_app
npx vitest run
```

### Linting & Formatting

```bash
# Check
ruff check .
ruff format --check .

# Auto-fix
ruff check --fix .
ruff format .
```

## Project Structure

```
AQI-Predictor/
├── config/              # Settings, schemas, environment
├── data_pipeline/       # Data ingestion & transformation
├── feature_pipeline/    # Feature store (ClearML)
├── training_pipeline/   # Model training, evaluation, registry
├── deployment/
│   ├── api/             # Flask REST API
│   └── web_app/         # Next.js frontend
├── tests/               # Python test suite
└── .github/workflows/   # CI/CD pipelines
```

## Coding Standards

- **Python**: Follow PEP 8 (enforced by Ruff). Type annotations required. Docstrings on all public functions.
- **TypeScript**: Follow ESLint/Prettier config in `web_app/`.
- **Commits**: Use conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`).
- **Branches**: Work on feature branches, PR to `main`.

## API Authentication

When `API_AUTH_KEY` environment variable is set, all endpoints (except `/health`) require authentication via:
- Header: `X-API-Key: <key>`
- Query param: `?api_key=<key>`

## Running the API Locally

```bash
# Development mode
flask --app deployment.api.main run --debug --port 8000

# Production mode (Gunicorn)
gunicorn deployment.api.main:app --bind 0.0.0.0:8000 --workers 2
```

## Deployment

- **API**: Auto-deploys to Render on push to `main` (paths: `deployment/api/**`, `training_pipeline/**`)
- **Frontend**: Auto-deploys to Vercel on push to `main`
- **Models**: Stored in ClearML experiment tracker

## Reporting Issues

Please include:
1. Steps to reproduce
2. Expected vs actual behavior
3. Python/Node version
4. Relevant error logs
