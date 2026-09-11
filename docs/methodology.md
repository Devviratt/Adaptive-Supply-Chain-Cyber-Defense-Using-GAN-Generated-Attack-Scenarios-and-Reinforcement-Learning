# Methodology

## Research Overview

This project investigates whether GAN-generated synthetic attack-scenario diversity can improve the performance of a reinforcement-learning-based adaptive defense policy in a simulated software supply-chain environment.

## Pipeline

### 1. Dataset Acquisition

We use the **CIC-IDS2017** dataset, a publicly available network intrusion detection dataset published by the Canadian Institute for Cybersecurity. It contains labeled network traffic flows covering benign traffic and several attack types (DoS, DDoS, Port Scan, Brute Force, Web Attacks, Botnet, Infiltration).

**Important distinction:** CIC-IDS2017 provides network/attack behavior features. It is not a native software-supply-chain dataset. The supply-chain context is provided by our simulation environment. We use CIC-IDS2017 as a source of realistic attack feature distributions.

### 2. Data Preprocessing

The preprocessing pipeline performs:
- Schema inspection and column identification
- Duplicate removal
- Missing value handling (NaN, Inf)
- Label normalization across attack categories
- Categorical encoding
- Numerical scaling (StandardScaler, fitted on training set only)
- Feature selection (variance threshold + correlation filter)
- Stratified train/validation/test split (70/15/15)

Preprocessing artifacts are saved for reproducibility.

### 3. Synthetic Data Generation (CTGAN)

We use CTGAN (Conditional Tabular GAN) to generate synthetic attack-scenario feature vectors. CTGAN is designed for tabular data and handles mixed continuous/discrete columns.

The GAN does NOT generate real exploits. It generates tabular feature vectors that resemble attack traffic patterns.

### 4. Synthetic Data Validation

Generated data is validated against real data using:
- Feature distribution comparison (KL divergence)
- Statistical summary comparison
- Correlation structure comparison
- Class balance assessment
- Diversity measurement (duplicate ratio)
- Range/constraint compliance
- Downstream utility testing

### 5. Scenario Mapping

Validated feature records are mapped to structured supply-chain attack scenarios:
- Attack category
- Severity level
- Affected supply-chain stage (Supplier, Build, Registry, Deployment)
- Propagation risk
- Impact scores (availability, integrity, confidentiality)

Mapping logic is deterministic and documented.

### 6. Supply-Chain Simulation

A custom Gymnasium environment simulates a simplified 4-stage software supply chain. Attack scenarios affect one or more stages. The environment models consequences (risk propagation, availability degradation, integrity compromise) rather than real exploitation.

### 7. Reinforcement Learning

A DQN agent learns to select defensive actions in response to supply-chain attack states. The agent observes a 12-dimensional state vector and chooses from 5 discrete actions.

### 8. Evaluation

The evaluation engine runs three primary experiments:
- **Experiment A:** Rule-based baseline
- **Experiment B:** DQN trained on real scenarios only
- **Experiment C:** DQN trained on real + validated synthetic scenarios

Comparison metrics include mitigation success rate, service availability, cumulative reward, and robustness across scenario types and random seeds.

## Ethical Considerations

All attack scenarios are simulated or dataset-derived. No real-world exploitation is performed. The system is designed for defensive research and cybersecurity education.
