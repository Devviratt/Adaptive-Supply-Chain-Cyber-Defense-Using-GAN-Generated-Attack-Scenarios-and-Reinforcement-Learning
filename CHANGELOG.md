# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-09-11

### Added
- Project repository structure and foundation
- Python package configuration (`pyproject.toml`)
- Configuration system (YAML + environment variables)
- Structured logging with structlog
- SQLAlchemy database models (scenarios, experiments, metrics, simulation runs, training runs, system events)
- FastAPI application with health check and project status endpoints
- React + TypeScript + Vite frontend scaffold
- Docker and docker-compose configuration
- Makefile with development commands
- GitHub Actions CI workflow
- Initial test suite (unit + smoke)
- Project documentation skeleton
  - README.md
  - CONTRIBUTING.md
  - docs/team_roles.md
  - docs/project_status.md
  - docs/task_board.md
  - docs/architecture.md
  - docs/methodology.md
  - docs/research_gap.md
  - docs/reward_design.md
  - docs/setup.md
- Configuration files for all modules (base, preprocessing, GAN, DQN, environment, baseline, evaluation)
