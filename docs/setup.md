# Setup Guide

## Prerequisites

- **Python 3.11+** — [python.org](https://www.python.org/downloads/) or pyenv
- **Node.js 18+** — [nodejs.org](https://nodejs.org/) or nvm
- **Git** — [git-scm.com](https://git-scm.com/)
- **Docker** (optional) — [docker.com](https://www.docker.com/)

## Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_ORG/asccd.git
cd asccd

# 2. Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Install everything
make setup
```

This will:
- Install Python dependencies (production + dev)
- Create `.env` from `.env.example`
- Install frontend dependencies

## Manual Setup

```bash
# Python dependencies
pip install -e ".[dev]"

# Environment configuration
cp .env.example .env
# Edit .env with your settings

# Frontend dependencies
cd frontend
npm install
cd ..
```

## Running the Application

### Backend
```bash
make run-backend
# → API at http://localhost:8000
# → Docs at http://localhost:8000/api/docs
```

### Frontend
```bash
make run-frontend
# → Dashboard at http://localhost:5173
```

### Docker
```bash
docker-compose up -d
```

## Running Tests

```bash
make test           # All tests
make test-unit      # Unit tests only
make test-smoke     # Smoke tests only
make lint           # Code linting
make format         # Auto-format code
```

## Dataset Setup

The CIC-IDS2017 dataset must be downloaded separately:

```bash
make download-data
# Or:
python scripts/download_dataset.py
```

For development with a smaller sample:
```bash
python scripts/download_dataset.py --sample 50000
```

## ML Pipeline

```bash
make preprocess         # Step 1: Preprocess data
make train-gan          # Step 2: Train CTGAN
make generate-synthetic # Step 3: Generate synthetic data
make train-dqn          # Step 4: Train DQN agent
make run-baseline       # Step 5: Run baseline
make run-evaluation     # Step 6: Run evaluation
make run-experiments    # Or: Run all experiments
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure virtual env is activated and `pip install -e .` was run |
| Port 8000 in use | Change `APP_PORT` in `.env` |
| Database errors | Delete `asccd.db` and restart |
| Frontend proxy error | Ensure backend is running first |
