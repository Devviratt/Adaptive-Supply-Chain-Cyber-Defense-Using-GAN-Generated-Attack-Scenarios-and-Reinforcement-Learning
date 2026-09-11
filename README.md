# Adaptive Supply Chain Cyber Defense Using GAN-Generated Attack Scenarios and Reinforcement Learning

[![CI](https://github.com/YOUR_ORG/asccd/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_ORG/asccd/actions/workflows/ci.yml)
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
- Node.js 18+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_ORG/asccd.git
cd asccd

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
make setup

# Or manually:
pip install -e ".[dev]"
cp .env.example .env
cd frontend && npm install && cd ..
```

### Running Locally

```bash
# Start backend (terminal 1)
make run-backend

# Start frontend (terminal 2)
make run-frontend
```

The API will be available at `http://localhost:8000` and the dashboard at `http://localhost:5173`.

### Running Tests

```bash
make test          # All tests
make test-unit     # Unit tests only
make lint          # Linting
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
