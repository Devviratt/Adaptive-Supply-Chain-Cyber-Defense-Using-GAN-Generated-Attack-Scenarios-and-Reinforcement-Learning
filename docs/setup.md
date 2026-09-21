# Setup Guide

## Prerequisites

- **Python 3.11+** — [python.org](https://www.python.org/downloads/) or pyenv
- **Node.js 18+** — [nodejs.org](https://nodejs.org/) or nvm
- **Git** — [git-scm.com](https://git-scm.com/)
- **Docker** (optional) — [docker.com](https://www.docker.com/)

## Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/Devviratt/Adaptive-Supply-Chain-Cyber-Defense-Using-GAN-Generated-Attack-Scenarios-and-Reinforcement-Learning.git
cd "Adaptive-Supply-Chain-Cyber-Defense-Using-GAN-Generated-Attack-Scenarios-and-Reinforcement-Learning"

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

The pipeline supports both development mode (generating a realistic sample) and full dataset mode:

### Development Mode (Quickstart without 6GB download)
```bash
# Generate a 50,000-row realistic development sample matching CIC-IDS2017 schema
python scripts/download_dataset.py --generate-dev-sample --rows 50000
```

### Full Dataset Mode
```bash
# Display download instructions and verify existing raw CSVs in data/raw/
python scripts/download_dataset.py
```

## Data Preprocessing Pipeline

```bash
# 1. Inspect raw CSV files and schema
python scripts/preprocess.py --inspect

# 2. Run preprocessing, stratified splitting, and feature selection
python scripts/preprocess.py

# Or run with development downsampling:
python scripts/preprocess.py --sample 50000

# 3. Validate processed datasets and artifacts
python scripts/preprocess.py --validate
```

## ML Pipeline (Phases 3 - 9)

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
