# Scenario Model

## Not yet implemented.

This document will describe the scenario mapping logic once implemented in Phase 4.

## Planned Design

### Input
A validated attack feature record (from CIC-IDS2017 or CTGAN-generated)

### Output
- `scenario_id` — Unique identifier
- `attack_category` — Mapped attack type
- `severity` — low / medium / high / critical
- `affected_stage` — Supplier / Build / Registry / Deployment
- `propagation_risk` — [0, 1]
- `availability_impact` — [0, 1]
- `integrity_impact` — [0, 1]
- `confidentiality_impact` — [0, 1]
- `duration_steps` — Expected scenario duration

### Supply-Chain Stages
1. **Supplier** — Source code dependencies, third-party libraries
2. **Build** — CI/CD pipeline, build system
3. **Registry** — Package distribution, artifact storage
4. **Deployment** — Production environment

### Mapping Assumptions
All mapping assumptions will be documented here with justification.
