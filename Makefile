.PHONY: help install install-dev lint format test test-unit test-integration test-smoke run-backend run-frontend run docker-build clean setup-env

# ============================================================
# ASCCD - Makefile
# ============================================================

PYTHON := python3
PIP := pip3
UVICORN := uvicorn
NPM := npm

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================
# Setup
# ============================================================

install: ## Install production dependencies
	$(PIP) install -e .

install-dev: ## Install development dependencies
	$(PIP) install -e ".[dev]"

setup-env: ## Create .env from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example — please update values."; \
	else \
		echo ".env already exists."; \
	fi

setup: install-dev setup-env ## Full development setup
	@echo "Setting up frontend..."
	cd frontend && $(NPM) install
	@echo ""
	@echo "============================================================"
	@echo "Setup complete. Update .env with your configuration."
	@echo "Run 'make run' to start the application."
	@echo "============================================================"

# ============================================================
# Code Quality
# ============================================================

lint: ## Run linters
	ruff check src/ tests/
	black --check src/ tests/

format: ## Format code
	black src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Run type checking
	mypy src/

# ============================================================
# Testing
# ============================================================

test: ## Run all tests
	pytest tests/ -v --tb=short

test-unit: ## Run unit tests
	pytest tests/unit/ -v --tb=short

test-integration: ## Run integration tests
	pytest tests/integration/ -v --tb=short

test-smoke: ## Run smoke tests
	pytest tests/smoke/ -v --tb=short

test-cov: ## Run tests with coverage
	pytest tests/ -v --tb=short --cov=src --cov-report=html --cov-report=term

# ============================================================
# Run Application
# ============================================================

run-backend: ## Start FastAPI backend
	$(UVICORN) src.api.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend: ## Start React frontend
	cd frontend && $(NPM) run dev

run: ## Start both backend and frontend (requires two terminals)
	@echo "Start backend:  make run-backend"
	@echo "Start frontend: make run-frontend"

# ============================================================
# ML Pipeline
# ============================================================

download-data: ## Download CIC-IDS2017 dataset
	$(PYTHON) scripts/download_dataset.py

preprocess: ## Run data preprocessing
	$(PYTHON) scripts/preprocess.py

train-gan: ## Train CTGAN model
	$(PYTHON) scripts/train_gan.py

generate-synthetic: ## Generate synthetic data
	$(PYTHON) scripts/generate_synthetic.py

evaluate-utility: ## Run downstream ML utility evaluation
	$(PYTHON) scripts/evaluate_synthetic_utility.py

train-dqn: ## Train DQN agent
	$(PYTHON) scripts/train_dqn.py

run-baseline: ## Run rule-based baseline
	$(PYTHON) scripts/run_baseline.py

run-evaluation: ## Run evaluation
	$(PYTHON) scripts/run_evaluation.py

run-experiments: ## Run all experiments
	$(PYTHON) scripts/run_experiments.py

# ============================================================
# Docker
# ============================================================

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start with Docker
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

# ============================================================
# Maintenance
# ============================================================

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage
