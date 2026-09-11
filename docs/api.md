# API Documentation

## Base URL

```
http://localhost:8000/api
```

## Interactive Docs

- Swagger UI: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- ReDoc: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

## Available Endpoints (Phase 1)

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Basic health check |
| GET | `/api/health/ready` | Readiness check (includes DB) |

### Project

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/project/status` | Project status and module completion |
| GET | `/api/project/team` | Team member information |

## Planned Endpoints (Future Phases)

See `docs/task_board.md` for implementation timeline.

| Method | Endpoint | Phase |
|--------|----------|-------|
| GET | `/api/scenarios` | 10 |
| POST | `/api/scenarios/generate` | 10 |
| GET | `/api/supply-chain/state` | 10 |
| POST | `/api/simulation/step` | 10 |
| POST | `/api/rl/train` | 10 |
| GET | `/api/experiments` | 10 |
| GET | `/api/evaluation/summary` | 10 |
| GET | `/api/logs` | 10 |
