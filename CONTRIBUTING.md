# Contributing to ASCCD

Thank you for contributing to the Adaptive Supply Chain Cyber Defense project.

## Team Members

This is a 3-member academic project. External contributions are welcome but must follow these guidelines.

## Git Workflow

### Branches

- `main` — Production-ready, stable code
- `development` — Integration branch for features
- `feature/*` — Individual feature branches

### Branch Naming

```
feature/data-preprocessing
feature/ctgan
feature/scenario-mapper
feature/supply-chain-env
feature/dqn
feature/evaluation
feature/dashboard
fix/missing-value-handling
docs/methodology-update
```

### Commit Messages

Use conventional commits:

```
feat: implement CTGAN scenario generator
fix: handle missing network-flow values
test: add scenario mapper validation
docs: update experiment protocol
refactor: extract reward computation
chore: update dependencies
experiment: run DQN seed comparison
```

## Development Setup

```bash
# Clone and create virtual environment
git clone <repo-url>
cd asccd
python3 -m venv .venv
source .venv/bin/activate

# Install dev dependencies
make install-dev

# Setup frontend
cd frontend && npm install && cd ..

# Create environment config
cp .env.example .env
```

## Code Quality

Before submitting:

```bash
# Format code
make format

# Run linter
make lint

# Run tests
make test
```

## Pull Request Process

1. Create a feature branch from `development`
2. Implement changes with tests
3. Update documentation
4. Ensure CI passes
5. Request review from team
6. Merge to `development`

## Code Style

- Python: Black formatting, Ruff linting, 100-char line length
- TypeScript: ESLint + Prettier
- All files must have module-level docstrings
- Functions must have type hints

## Security

- Never commit `.env` files or credentials
- Never implement real exploits or attacks
- All attack scenarios must remain simulated
- Report security concerns to the team privately
