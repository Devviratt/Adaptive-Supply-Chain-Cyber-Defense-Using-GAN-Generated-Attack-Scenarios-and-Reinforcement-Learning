# ============================================================
# ASCCD - Multi-stage Docker Build
# ============================================================
FROM python:3.11-slim AS backend

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir .

# Copy source
COPY src/ src/
COPY config/ config/
COPY data/ data/
COPY scripts/ scripts/
COPY tests/ tests/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================
# Frontend build stage
# ============================================================
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ============================================================
# Production image
# ============================================================
FROM python:3.11-slim AS production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY src/ src/
COPY config/ config/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
