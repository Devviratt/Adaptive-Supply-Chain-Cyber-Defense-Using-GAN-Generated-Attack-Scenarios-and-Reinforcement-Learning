# ASCCD Attack Scenario Model & Semantic Mapping Protocol (Phase 4)

## 1. Overview & Research Context

The ASCCD (Adaptive Supply Chain Cyber Defense) platform evaluates whether GAN-generated synthetic attack diversity improves reinforcement-learning-based defense decisions in a simulated software supply-chain environment.

**The Problem:** Public network intrusion detection datasets (such as **CIC-IDS2017**) capture packet and flow-level network dynamics (e.g., packet arrival times, payload byte counts, TCP flag distributions) but do not inherently contain software supply-chain topological semantics.

**The Solution:** The **Scenario Mapper** (`src/scenarios/mapper.py`) translates continuous tabular feature vectors (both real CIC-IDS2017 records and CTGAN-generated synthetic records) into structured **Attack Scenarios** (`src/scenarios/models.py`) with explicit risk, severity, and CIA (Confidentiality, Integrity, Availability) impact profiles.

---

## 2. Supply-Chain Lifecycle Stages

The simulation models four sequential dependency stages:

```
[Supplier] ───► [Build] ───► [Registry] ───► [Deployment]
  (Code /       (CI/CD        (Package       (Production
Dep. Ingestion)  Pipelines)    Artifacts)     Runtime)
```

1. **`supplier` (Source & Dependency Ingestion):**
   - Upstream third-party open-source dependencies, code repositories (e.g. GitHub, GitLab), developer endpoints.
   - Primary risks: Malicious code injection, poisoned upstream packages, compromised commit signing keys, dependency tampering.
2. **`build` (CI/CD Build & Test Infrastructure):**
   - Automated runners, compilers, build orchestrators (e.g. Jenkins, GitHub Actions runners).
   - Primary risks: Hijacked runners for cryptocurrency mining or lateral pivoting, CI credential theft, pipeline tampering.
3. **`registry` (Artifact & Container Distribution):**
   - Internal/public package repositories, container registries (e.g. Docker Hub, Nexus, Artifactory).
   - Primary risks: Unauthorized image pushes, credential stuffing against distribution endpoints, registry denial-of-service.
4. **`deployment` (Production Runtime Infrastructure):**
   - Kubernetes clusters, application servers, microservice meshes, production databases.
   - Primary risks: Volumetric service denial, DDoS, external port reconnaissance, container escapes.

---

## 3. Attack Category Mapping Rules

| Attack Category | Primary Stage | Default Severity | Propagation Risk | Availability Impact | Integrity Impact | Confidentiality Impact | Base Duration | Mapping Justification |
|---|---|---|---|---|---|---|---|---|
| **`web_attack`** | `supplier` | High | 0.75 | 0.20 | 0.85 | 0.70 | 15 | SQL injection / XSS / web vulnerabilities targeting dependency portal or upstream repository management. High downstream propagation. |
| **`brute_force`** | `build` | Medium | 0.60 | 0.25 | 0.75 | 0.80 | 10 | Credential stuffing / SSH attacks attempting to compromise build runner authorization or push tokens. |
| **`botnet`** | `build` | High | 0.80 | 0.40 | 0.70 | 0.65 | 20 | Compromised build nodes hijacked by C2 infrastructure to move laterally through the enterprise. |
| **`dos`** | `deployment` | High | 0.20 | 0.90 | 0.10 | 0.05 | 25 | Volumetric or connection starvation attacks targeting public endpoints; high localized availability drop. |
| **`ddos`** | `deployment` | Critical | 0.25 | 0.95 | 0.10 | 0.05 | 30 | Distributed floods overwhelming cluster ingress or load balancers, causing severe availability outage. |
| **`portscan`** | `deployment` | Low | 0.15 | 0.10 | 0.05 | 0.30 | 5 | Reconnaissance probing exposed ports; low immediate damage, precursor to further lateral action. |
| **`infiltration`** | `supplier` | Critical | 0.85 | 0.30 | 0.90 | 0.90 | 35 | Stealth intrusion directly into developer workstations or internal networks, endangering code integrity. |
| **`benign`** | `deployment` | Low | 0.00 | 0.00 | 0.00 | 0.00 | 1 | Normal operational pipeline operations; zero malicious disruption. |

---

## 4. Continuous Feature Modulation

Rather than producing static, uniform scenario values for every attack within a class, the **Scenario Mapper** dynamically modulates scenario metrics based on the specific numerical flow telemetry:

1. **Volumetric Modulation ($\text{vol\_factor}$):**
   $$\text{vol\_factor} = \min\left(1.0, \frac{\log_{10}(\text{Flow Bytes/s} + \text{Flow Packets/s} + 1.0)}{8.0}\right)$$
   Modulates availability impact:
   $$\text{Availability Impact} = \text{clip}\left(\text{Base Availability} \times (0.8 + 0.4 \times \text{vol\_factor}), 0.0, 1.0\right)$$

2. **Duration Modulation ($\text{dur\_factor}$):**
   $$\text{dur\_factor} = \min\left(1.0, \frac{\log_{10}(\text{Flow Duration} + 1.0)}{8.0}\right)$$
   $$\text{Duration Steps} = \text{clip}\left(\text{round}(\text{Base Duration} \times (0.7 + 0.6 \times \text{dur\_factor})), 1, 50\right)$$

3. **SYN Anomaly Modulation ($\text{syn\_factor}$):**
   $$\text{syn\_factor} = \min\left(1.0, \frac{\text{SYN Flag Count}}{50.0}\right)$$
   $$\text{Propagation Risk} = \text{clip}\left(\text{Base Propagation} \times (0.85 + 0.3 \times \text{syn\_factor}), 0.0, 1.0\right)$$

4. **Dynamic Severity Upgrade:**
   If $\text{vol\_factor} \ge 0.85$ or $\text{dur\_factor} \ge 0.85$, the scenario's severity escalates by one level (e.g. `medium` $\rightarrow$ `high`, or `high` $\rightarrow$ `critical`).

---

## 5. RL State Vector Embedding

For direct integration into the Gymnasium reinforcement learning environment, each `AttackScenario` provides an 8-dimensional normalized observation vector:

$$\mathbf{v}_{\text{scenario}} = \left[ r_{\text{prop}}, i_{\text{avail}}, i_{\text{integ}}, i_{\text{conf}}, \frac{\text{stage\_idx}}{3}, \frac{\text{sev\_idx}}{3}, \frac{\min(d, 50)}{50}, \mathbb{I}(\text{synthetic}) \right] \in [0, 1]^8$$

---

## 6. CLI Usage & Pipeline Integration

Map any processed real or synthetic dataset via the CLI:

```bash
# Map real test partition and save to database
python scripts/run_scenario_mapping.py --input data/processed/test.csv --source real --save-db

# Map synthetic generated attack dataset
python scripts/run_scenario_mapping.py --input data/generated/synthetic_attacks.csv --source synthetic --save-db
```
