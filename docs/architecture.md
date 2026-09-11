# System Architecture

## Overview

ASCCD follows a modular, layered architecture designed for reproducible ML research with a production-quality web interface.

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Dashboard (Frontend)                  │
├─────────────────────────────────────────────────────────────────┤
│                     FastAPI Backend (API Layer)                 │
├──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│  Data    │  GAN     │ Scenario │   RL     │    Evaluation       │
│ Pipeline │ Pipeline │ Mapper   │ Agents   │    Engine           │
├──────────┴──────────┴──────────┴──────────┴─────────────────────┤
│              Supply-Chain Simulation Environment                │
├─────────────────────────────────────────────────────────────────┤
│           Common (Config, Logging, Database, Exceptions)        │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Frontend (React + TypeScript)
- Renders 10 dashboard pages
- Consumes REST API
- No direct ML computation

### API Layer (FastAPI)
- REST endpoints for all operations
- Pydantic request/response validation
- Background task management for long-running ML jobs
- SQLAlchemy database interaction
- Authentication and CORS

### ML Pipeline Modules
- **Data Pipeline:** Loading, cleaning, encoding, scaling, splitting CIC-IDS2017
- **GAN Pipeline:** CTGAN training, synthetic generation, validation
- **Scenario Mapper:** Attack features → supply-chain scenarios
- **RL Agents:** DQN (primary), PPO (optional), rule-based baseline
- **Evaluation Engine:** Metrics computation, cross-experiment comparison

### Simulation Environment (Gymnasium)
- Custom `SupplyChainEnv` with 4 stages
- 12-dimensional state space, 5 discrete actions
- Configurable reward function

### Common Layer
- Configuration loading (YAML + .env)
- Structured logging
- Database engine and ORM models
- Exception hierarchy

## Data Flow

```
CIC-IDS2017 CSV files
       │
       ▼
  DataLoader → raw DataFrames
       │
       ▼
  Preprocessor → cleaned, encoded, scaled features
       │
       ├─── train split → CTGAN training → synthetic data → validation
       │
       ▼
  ScenarioMapper → structured attack scenarios
       │
       ▼
  SupplyChainEnv → RL episodes
       │
       ├─── DQN Agent (training)
       ├─── Rule-Based Baseline (evaluation)
       │
       ▼
  EvaluationEngine → metrics → reports → dashboard
```

## Database Schema

See `src/common/models.py` for ORM definitions:
- `scenarios` — Attack scenario records (real + synthetic)
- `experiments` — Experiment run metadata
- `experiment_metrics` — Per-step/episode metric recordings
- `simulation_runs` — Episode-level simulation results
- `training_runs` — ML model training records
- `system_events` — Application event log

## Configuration

All module behavior is controlled via YAML configuration files in `config/`:
- `base.yaml` — Global settings
- `preprocessing.yaml` — Data pipeline
- `gan.yaml` — CTGAN hyperparameters
- `dqn.yaml` — DQN + reward function
- `environment.yaml` — Supply chain environment
- `baseline.yaml` — Rule-based baseline
- `evaluation.yaml` — Experiment protocol
