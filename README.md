# Adaptive Supply Chain Cyber Defense Using GAN-Generated Attack Scenarios and Reinforcement Learning

[![CI](https://github.com/Devviratt/Adaptive-Supply-Chain-Cyber-Defense-Using-GAN-Generated-Attack-Scenarios-and-Reinforcement-Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/Devviratt/Adaptive-Supply-Chain-Cyber-Defense-Using-GAN-Generated-Attack-Scenarios-and-Reinforcement-Learning/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Team 84** — Dayananda Sagar University, School of Engineering, Department of Computer Science and Engineering
>
> **Guide:** Prof. Namyapriya D

## Overview

ASCCD is a defensive cybersecurity research platform that studies whether **GAN-generated synthetic attack scenarios** can improve **adaptive reinforcement-learning-based defense decisions** in a **simulated software supply-chain environment**.

### Research Question

> *"Can validated GAN-generated attack-scenario diversity improve the performance and robustness of an RL-based adaptive defense policy in a simulated software supply-chain environment?"*

### Problem Statement

Recent research has separately advanced GAN-based attack-data augmentation and adaptive reinforcement-learning-based cyber defense. However, there is limited experimental evaluation of whether GAN-generated attack-scenario diversity can improve RL-based mitigation decisions within a simulated software supply-chain dependency environment.

## Architecture

```
CIC-IDS2017 Dataset
       │
       ▼
Data Preprocessing (cleaning, encoding, scaling, selection)
       │
       ├──────────────────────┐
       ▼                      ▼
  Real Data              CTGAN Generator
  Distribution           Synthetic Data
       │                      │
       └──────────┬───────────┘
                  ▼
        Synthetic Validation (quality, diversity, distribution)
                  │
                  ▼
          Scenario Mapper (attack type, severity, affected stage)
                  │
                  ▼
     Supply Chain Simulation (Supplier → Build → Registry → Deployment)
                  │
                  ▼
         RL Environment (state, action, reward, transition)
                  │
                  ▼
          DQN Defense Agent
                  │
                  ▼
     Defensive Actions (Monitor, Isolate, Block, Rebuild, Recover)
                  │
                  ▼
        Evaluation Engine (metrics, comparison, reports)
                  │
                  ▼
            Dashboard (experiments, visualization, status)
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11 |
| Data | Pandas, NumPy, Scikit-learn |
| GAN | CTGAN / SDV, PyTorch |
| RL | Gymnasium, Stable-Baselines3, PyTorch |
| Backend | FastAPI, SQLAlchemy, SQLite |
| Frontend | React, TypeScript, Vite |
| Visualization | Recharts, Matplotlib, Plotly |
| Testing | pytest |
| CI/CD | GitHub Actions |
| Containerization | Docker, docker-compose |

## Dataset

We use **CIC-IDS2017** as the primary public attack-data source for network/attack behavior features.

> **Important:** CIC-IDS2017 is not a native software-supply-chain dataset. It provides attack/intrusion feature vectors. The supply-chain context is provided by our custom simulation environment. This distinction is documented throughout the project.

## GAN Methodology

We use **CTGAN** (Conditional Tabular GAN) to generate synthetic attack-scenario features. The synthetic data is validated against real data for:
- Distribution similarity
- Feature statistics
- Correlation preservation
- Class balance
- Diversity checks
- Range/constraint compliance

Synthetic data is explicitly labeled as synthetic and never presented as real data.

## Supply-Chain Environment

A custom **Gymnasium** environment simulates a simplified software supply chain with four stages:

1. **Supplier** — Source code dependencies
2. **Build** — CI/CD build pipeline
3. **Package/Registry** — Package distribution
4. **Deployment** — Production environment

Each stage can be in states: Normal, Suspicious, Compromised, Degraded, or Recovering.

## RL Methodology

We implement **DQN** (Deep Q-Network) using Stable-Baselines3 as the primary RL algorithm. The agent observes a 12-dimensional state vector and selects from 5 discrete defensive actions. The reward function is configurable and encourages successful mitigation while penalizing unnecessary interventions.

## Baseline

A deterministic **rule-based baseline** provides the comparison benchmark. Rules are configurable and documented.

## Evaluation

The core experiment compares:
- **Experiment A:** Rule-based baseline
- **Experiment B:** DQN trained without GAN augmentation
- **Experiment C:** DQN trained with validated GAN-generated scenarios
- **Experiment D:** PPO comparison (optional)

Metrics include mitigation success rate, service availability, cumulative reward, and robustness across scenario types and random seeds.

## Installation

### Prerequisites
- Python 3.11+
- Node.js 20.19+ or 22.12+
- Git

### Setup

Run the following in PowerShell. Python 3.11 or newer and Node.js 20.19+ or 22.12+ are required by the current frontend toolchain.

```powershell
git clone https://github.com/Devviratt/Adaptive-Supply-Chain-Cyber-Defense-Using-GAN-Generated-Attack-Scenarios-and-Reinforcement-Learning.git
Set-Location Adaptive-Supply-Chain-Cyber-Defense-Using-GAN-Generated-Attack-Scenarios-and-Reinforcement-Learning

py -3.13 -m venv "$env:TEMP\asccd313"
& "$env:TEMP\asccd313\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}

Push-Location frontend
npm install
Pop-Location
```

If Python 3.13 is not installed, replace `-3.13` with an installed Python 3.11+ version.
Keep the virtual environment under `$env:TEMP` rather than inside this repository; the shorter install path avoids Windows long-path failures while installing PyTorch. The `&` before `Activate.ps1` is required to run the activation script. Confirm the environment is active with:

```powershell
python -c "import sys; print(sys.executable)"
```

The printed executable should be under `$env:TEMP\asccd313\Scripts`. If `pip install` fails, resolve that first and rerun the install before starting the API; a partially installed environment can produce misleading errors such as `No module named 'pandas'`.

### Run the application

Open two PowerShell terminals at the repository root. Do not `cd backend` (there is no `backend` directory) or use the Makefile commands on Windows; the backend command below runs from the repository root.

**Terminal 1 — backend API**

```powershell
& "$env:TEMP\asccd313\Scripts\Activate.ps1"
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — frontend**

```powershell
Set-Location frontend
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173` for the dashboard and `http://127.0.0.1:8000/api/docs` for the API.

### Prepare data and train the models

For a quick offline run, create the development sample, preprocess it, train CTGAN, generate examples, and train the DQN agent:

```powershell
python scripts\download_dataset.py --generate-dev-sample --rows 50000
python scripts\preprocess.py --input data\raw --output data\quickstart\processed
python scripts\preprocess.py --output data\quickstart\processed --validate

python scripts\train_ctgan_demo.py train --input data\quickstart\processed\train.csv --model artifacts\models\ctgan\model.pkl --epochs 25
python scripts\train_ctgan_demo.py generate --model artifacts\models\ctgan\model.pkl --output data\quickstart\generated\ctgan_samples.csv --count 2000
python scripts\train_ctgan_demo.py validate --input data\quickstart\processed\train.csv --output data\quickstart\generated\ctgan_samples.csv

python scripts\train_dqn.py --condition augmented --data-root data\quickstart --evaluation-data-root data\quickstart --timesteps 100000 --output-dir artifacts\models\dqn\quickstart --report artifacts\reports\dqn_quickstart.json
```

To use the supplied full CIC-IDS2017 archive without loading it all into memory, put its CSV files in `data\raw\cicids2017_full` and create the stratified sample first:

```powershell
python scripts\sample_cicids2017.py --input data\raw\cicids2017_full --output data\cicids2017_sample\raw\training_sample.csv --rows 71429 --minimum-per-class 500
python scripts\preprocess.py --input data\cicids2017_sample\raw --output data\cicids2017_sample\processed
python scripts\train_ctgan_demo.py train --input data\cicids2017_sample\processed\train.csv --model artifacts\models\ctgan\cicids2017_sample\model.pkl --config data\cicids2017_sample\ctgan_config.yaml
python scripts\train_ctgan_demo.py generate --model artifacts\models\ctgan\cicids2017_sample\model.pkl --output data\cicids2017_sample\generated\ctgan_samples.csv --count 2000
python scripts\train_dqn.py --condition augmented --data-root data\cicids2017_sample --evaluation-data-root data\cicids2017_sample --timesteps 100000 --output-dir artifacts\models\dqn\cicids2017_sample --report artifacts\reports\dqn_cicids2017_sample.json
```

The full-archive workflow above trains on a stratified sample and does not perform full-archive evaluation. The archive has very few `infiltration` and `heartbleed` examples; synthetic rows for those classes should be treated as experimental.

### Running Tests

```powershell
python -m pytest
python -m ruff check src tests
python -m black --check src tests
```

## Team

| Name | USN | Responsibilities |
|------|-----|-----------------|
| C A Anandavarthan | ENG23CS0039 | Architecture, Backend, Supply-Chain Env, Integration |
| Deekshay G | ENG23CS0055 | Data Pipeline, CTGAN, Synthetic Validation |
| Dev Virat | ENG24CS1022 | RL/DQN, Evaluation, Experiments |

## Limitations

- CIC-IDS2017 is not a native software-supply-chain dataset — supply-chain context is simulated
- GAN outputs are synthetic feature vectors, not real exploits
- RL is evaluated in a controlled simulation, not production infrastructure
- Computational limitations may restrict experiment scale
- Results may not directly transfer to production systems

## Future Work

- Graph-based supply-chain representation (GAT + RL)
- Additional cybersecurity datasets
- SBOM-aware simulation
- Meta-RL approaches
- Federated learning
- Explainable RL decision analysis

## License

MIT License — see [LICENSE](LICENSE) for details.

## Ethics

This project is intended for academic research, defensive simulation, and cybersecurity education. All attack scenarios are abstract/simulated. No real-world exploitation is performed.
