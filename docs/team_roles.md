# Team Roles and Responsibilities

## Team 84 — Dayananda Sagar University

**Guide:** Prof. Namyapriya D

---

## Member 1: C A Anandavarthan

**USN:** ENG23CS0039
**Section:** 7A

### Primary Responsibilities
- Project architecture and system design
- FastAPI backend development and API design
- Supply-chain simulation environment (Gymnasium)
- System integration and release coordination
- Docker containerization and DevOps
- Database design and management

### Modules Owned
- `src/api/` — Backend API
- `src/environment/` — Supply chain environment
- `src/scenarios/` — Scenario mapper
- `src/common/` — Shared utilities
- `docker-compose.yml`, `Dockerfile`

---

## Member 2: Deekshay G

**USN:** ENG23CS0055
**Section:** 7A

### Primary Responsibilities
- CIC-IDS2017 dataset acquisition and exploration
- Data preprocessing pipeline (cleaning, encoding, scaling, selection)
- CTGAN training and synthetic data generation
- Synthetic data validation and quality assessment
- Data experiment design and execution

### Modules Owned
- `src/data/` — Data loading and preprocessing
- `src/gan/` — CTGAN training and generation
- `config/preprocessing.yaml`, `config/gan.yaml`
- `notebooks/01_data_exploration.ipynb`, `notebooks/02_preprocessing.ipynb`
- `notebooks/03_gan_validation.ipynb`

---

## Member 3: Dev Virat

**USN:** ENG24CS1022
**Section:** 7A

### Primary Responsibilities
- Reinforcement learning agent implementation (DQN)
- PPO comparison agent (if feasible)
- Rule-based baseline implementation
- Evaluation engine and metrics computation
- Experiment execution and analysis
- Training pipeline and reproducibility

### Modules Owned
- `src/rl/` — DQN and PPO agents
- `src/baselines/` — Rule-based baseline
- `src/evaluation/` — Evaluation engine
- `config/dqn.yaml`, `config/baseline.yaml`, `config/evaluation.yaml`
- `notebooks/04_rl_evaluation.ipynb`

---

## Shared Responsibilities (All Members)

- Testing and test maintenance
- Documentation and README updates
- Presentation preparation
- Bug fixing and code review
- Final integration and deployment
- Project status and task board updates

---

## Contribution Tracking

Contributions are tracked via:
1. Git commit history (`git log --author="name"`)
2. GitHub pull request records
3. Task board assignments in `docs/task_board.md`
4. Dashboard team contribution page

---

## Communication

- All project-critical information must be committed to the repository
- Do NOT keep important context only in chat or local notes
- Update `docs/project_status.md` after every significant change
- Update `docs/task_board.md` when task status changes
