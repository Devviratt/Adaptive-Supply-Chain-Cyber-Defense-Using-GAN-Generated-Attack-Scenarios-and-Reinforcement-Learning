# CIC-IDS2017 Data Ingestion and Preprocessing Pipeline

**Document Version:** 1.0.0  
**Phase:** 2 — Dataset Ingestion + Preprocessing  
**Owner:** Deekshay G (Lead Data & ML Engineer)  
**Reviewed by:** C A Anandavarthan (Team Lead & Systems Architect), Dev Virat (Security & Architecture)

---

## 1. Executive Summary

This document details the architecture, design rationale, mathematical transformations, leakage-prevention guarantees, and operational procedures for the **ASCCD Data Ingestion and Preprocessing Pipeline**. The pipeline processes the Canadian Institute for Cybersecurity **CIC-IDS2017** benchmark dataset into standardized, clean, and isolated train/validation/test partitions for downstream GAN scenario synthesis (Phase 3) and Reinforcement Learning cyber defense policy training (Phase 4).

---

## 2. Dataset Context & Academic Scope

### 2.1 Why CIC-IDS2017 is Used
CIC-IDS2017 (Canadian Institute for Cybersecurity, University of New Brunswick) is an established, peer-reviewed network intrusion benchmark collected over 5 days (Monday–Friday) of realistic traffic. It contains 80+ network flow features calculated with CICFlowMeter, encompassing benign traffic alongside diverse modern attack profiles:
- DoS (Hulk, GoldenEye, slowloris, Slowhttptest)
- DDoS (LOIC)
- PortScan
- Web Attacks (Brute Force, XSS, SQL Injection)
- Infiltration
- Botnet (ARES)
- Brute Force (FTP-Patator, SSH-Patator)
- Heartbleed

### 2.2 What CIC-IDS2017 Provides
- **Attack/Network Flow Behavior Signatures:** Packet intervals, inter-arrival times (IAT), packet length distributions, flow byte/packet rates, and flag counts.
- **Statistical Variability:** Natural variance across benign background operations and structured attack signatures.
- **Ground Truth Labels:** Standard multi-class ground truth for evaluation.

### 2.3 What CIC-IDS2017 Does NOT Provide (Critical Distinction)
> [!IMPORTANT]
> **Academic Scope Notice:** CIC-IDS2017 does **not** represent a software supply chain. It contains network perimeter and enterprise flow traffic. In the ASCCD system:
> 1. **CIC-IDS2017 serves as the empirical feature source** representing network-layer telemetry and external attack behaviors.
> 2. **Supply chain semantics** (dependency compromise, malicious commits, build tampering, CI/CD pipeline poisoning, code signing abuse, package repository substitution) are modeled in the custom simulation environment (Phases 4 & 5).
> 3. Downstream RL agents observe synthesized multidimensional states combining network telemetry (derived from CIC-IDS2017 feature distributions) and supply chain system states.

---

## 3. Data Pipeline Architecture

```
Raw CSVs (data/raw/)
       │
       ▼
┌──────────────────────────────┐
│       1. Data Loader         │  --> Discover CSVs, strip header whitespace,
│   (src/data/loader.py)       │      detect labels, concatenate frames
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      2. Cleaning Pass        │  --> Drop identifiers (IP, port, timestamp),
│ (src/data/preprocessor.py)   │      remove exact duplicates, map Inf to NaN,
└──────────────┬───────────────┘      impute/drop NaNs, normalize attack labels
               │
               ▼
┌──────────────────────────────┐
│     3. Stratified Split      │  --> Two-stage stratified split (70% / 15% / 15%)
│   (src/data/splitter.py)     │      with rare class protection and fixed seed
└──────────────┬───────────────┘
               │
         ┌─────┴───────────────────────┐
         ▼                             ▼
   Training Set (70%)           Val (15%) & Test (15%)
         │                             │
         ▼                             │
┌──────────────────────────────┐       │
│  4. Feature Selection & Fit  │       │
│      (TRAIN ONLY)            │       │
│ - Variance Threshold (>0.01) │       │
│ - Correlation Filter (<0.95) │       │
│ - Fit StandardScaler         │       │
│ - Fit LabelEncoder           │       │
└──────────────┬───────────────┘       │
               │                       │
               ▼                       ▼
┌──────────────────────────────────────────────┐
│           5. Transform All Splits            │
│  - Transform X_train, X_val, X_test          │
│  - Export train.{csv,pq}, val, test          │
│  - Export scaler, encoder, reports           │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│            6. Automated Validator            │
│           (src/data/validator.py)            │
│  - Zero NaNs, zero Infs                      │
│  - Feature dimension parity across splits    │
│  - Artifact existence & integrity            │
│  - Export validation_report.{json,md}        │
└──────────────────────────────────────────────┘
```

---

## 4. Pipeline Stages & Leakage Prevention

### 4.1 Step 1: Identifier & Metadata Removal
Configuration in `config/preprocessing.yaml` specifies candidate identifier columns to drop if present:
- `Flow ID`, `Source IP`, `Source Port`, `Destination IP`, `Destination Port`, `Timestamp`

These are strictly identifiers that cause memorization and target leakage in machine learning models. The preprocessor drops any matching columns prior to feature selection.

**Feature Count Arithmetic Verification:**
- **Raw Development Dataset:** 73 total columns (72 flow/numerical columns + 1 `Label` column).
- **Identifiers Present in Raw Development Dataset:** 1 column (`Destination Port`). The other 5 candidate identifier columns (`Flow ID`, `Source IP`, `Source Port`, `Destination IP`, `Timestamp`) are not present in flow-only benchmark files.
- **Post-Identifier Feature Count:** $72 \text{ raw features} - 1 \text{ dropped identifier} = 71 \text{ features}$.
- **Post-Variance / Post-Correlation Feature Count:** $71 - 0 - 0 = 71 \text{ features}$.
- **Final Partition Dimensions:** `train.csv` (3,437 × 72), `val.csv` (736 × 72), `test.csv` (737 × 72) — each containing 71 scaled numerical features plus 1 `Label` column.
- **Artifact Consistency:** `scaler.n_features_in_ == 71`, `feature_list.json == 71`, `preprocessing_report.json == 71`.

### 4.2 Step 2: Anomaly Cleaning & Label Normalization
1. **Deduplication:** Repeated packets and duplicated flow records are removed.
2. **Infinite Values:** Ratios such as `Flow Bytes/s` and `Flow Packets/s` produce $\pm\infty$ on zero-duration flows. Infs are mapped to NaN, then resolved via the configured missing value strategy (`drop_rows` or median imputation).
3. **Label Normalization:** CIC-IDS2017 uses varied tool names and Windows-1252 / latin-1 byte quirks (e.g. `\x96` or `\u2013` en-dashes in `Web Attack \x96 Brute Force`). All labels are mapped to canonical categories:
   - `benign`
   - `dos`
   - `ddos`
   - `portscan`
   - `brute_force`
   - `web_attack`
   - `botnet`
   - `infiltration`
   - `heartbleed`
   - `unknown` (fallback)

### 4.3 Step 3: Stratified Train / Validation / Test Splitting
Splitting occurs **before** any feature statistics or scaling parameters are computed:
- **Ratios:** 70% Training, 15% Validation, 15% Testing.
- **Stratification:** Two-stage split (Train vs. Val+Test, then Val vs. Test) ensuring that class ratios are uniformly distributed across all three splits.
- **Rare Classes:** Classes with fewer instances than the partition threshold are handled safely without crashing stratification.

### 4.4 Step 4: Strict Leakage Prevention
> [!CAUTION]
> **Data Leakage Guarantee:**
> - `variance_threshold` is computed **solely on the Training set**.
> - `correlation_threshold` is computed **solely on the Training set**.
> - `StandardScaler.mean_` and `StandardScaler.scale_` are computed **solely on the Training set**.
> - Validation and Test sets are transformed using the fitted training parameters.

---

## 5. Development Mode vs. Full Dataset

To facilitate reproducible development, testing, and continuous integration without requiring the 6GB multi-file raw download:

| Feature | Development Mode | Full Dataset Mode |
|---------|------------------|-------------------|
| **Data Source** | `python scripts/download_dataset.py --generate-dev-sample` | Official UNB CSV download (8 files) |
| **Row Count** | 5,000 to 50,000 rows (configurable via `--rows`) | ~2,830,743 rows |
| **File Size** | ~5 MB to ~50 MB | ~6 GB raw CSV |
| **Purpose** | Unit tests, integration tests, CI/CD, local debugging | Final GAN training, benchmarking, thesis evaluation |
| **Schema** | Exact CIC-IDS2017 schema (73 columns + label) | Exact CIC-IDS2017 schema |

---

## 6. Generated Artifacts

Upon running `python scripts/preprocess.py`, the following artifacts are produced in `data/processed/`:

| Artifact | Format | Description |
|----------|--------|-------------|
| `train.csv` / `train.parquet` | CSV / Parquet | Processed training partition (scaled features + label) |
| `val.csv` / `val.parquet` | CSV / Parquet | Processed validation partition |
| `test.csv` / `test.parquet` | CSV / Parquet | Processed testing partition |
| `scaler.joblib` | Scikit-learn Joblib | Fitted `StandardScaler` containing training means and scales |
| `label_encoder.joblib` | Scikit-learn Joblib | Fitted `LabelEncoder` for integer conversion |
| `feature_list.json` | JSON | Exact list of retained features after variance/correlation filtering |
| `label_mapping.json` | JSON | Dictionary of raw label strings mapped to canonical categories |
| `preprocessing_report.json` | JSON | Detailed metrics: row drops, missing values, duplicates, feature counts |
| `split_statistics.json` | JSON | Partition sizes, exact class counts, and split ratios |
| `class_distribution_splits.png` | PNG Chart | Publication-quality logarithmic class distribution chart |
| `validation_report.json` / `.md` | JSON / Markdown | Automated verification results for 11 validation checks |

---

## 7. CLI Usage Guide

### 7.1 Generate Development Sample
```bash
python scripts/download_dataset.py --generate-dev-sample --rows 50000
```

### 7.2 Inspect Raw Dataset
```bash
python scripts/preprocess.py --inspect
```

### 7.3 Run End-to-End Preprocessing
```bash
# Run on full raw data
python scripts/preprocess.py

# Run on a 50,000-row development sample
python scripts/preprocess.py --sample 50000

# Custom input/output paths
python scripts/preprocess.py --input data/raw --output data/processed --config config/preprocessing.yaml
```

### 7.4 Validate Processed Data
```bash
python scripts/preprocess.py --validate
```

---

## 8. Reproducibility Protocol

To reproduce identical preprocessing outputs:
1. Ensure Python 3.11 environment with dependencies from `pyproject.toml`.
2. Keep `random_seed: 42` in `config/preprocessing.yaml`.
3. Run `python scripts/preprocess.py`.
4. Outputs in `data/processed/` will match exact row counts, feature variances, and validation checksums.
