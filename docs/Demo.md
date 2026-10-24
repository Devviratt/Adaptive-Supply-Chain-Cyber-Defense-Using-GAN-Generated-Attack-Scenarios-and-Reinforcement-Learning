## What the demo shows

This demo walks through the working backend foundation, CIC-IDS2017 data preprocessing, and a small CTGAN synthetic-data generation run. Supply-chain attack simulation and RL defense are not implemented yet.

The development CSV generated for this demo is synthetic sample data for pipeline development. It must not be described as the full CIC-IDS2017 dataset or as real attack observations.

## One-time setup

Run these commands in PowerShell from the repository root. Python 3.13 64-bit is supported by the current dependency configuration. Create the virtual environment under `%TEMP%`: installing PyTorch into a virtual environment inside this repository can fail on Windows because the project path is long. If an install reports a missing `pandas` module, confirm this temp environment is activated and install the dependencies here.

```powershell
py -3.13 --version
py -3.13 -m venv "$env:TEMP\asccd313"
& "$env:TEMP\asccd313\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -c "import pandas, ctgan, torch; print('Dependencies ready')"
```

If PowerShell blocks activation, run this in that window and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& "$env:TEMP\asccd313\Scripts\Activate.ps1"
```

The sample CSV is expected at `data\raw\CIC-IDS2017_dev_sample.csv`. If `data\raw` does not contain a CSV, generate one:

```powershell
python scripts\download_dataset.py --generate-dev-sample --rows 50000
```

## Demo steps

### 1. Confirm the environment and data

Run from the repository root with the temp environment activated:

```powershell
& "$env:TEMP\asccd313\Scripts\Activate.ps1"
python --version
python -c "import pandas, ctgan, torch; print('Dependencies ready')"
```

The sample CSV is expected at `data\raw\CIC-IDS2017_dev_sample.csv`. Generate the offline development sample if it is missing:

```powershell
python scripts\download_dataset.py --generate-dev-sample --rows 50000
```

This generated development sample is not the full CIC-IDS2017 corpus or real attack observations.

### 2. Start the API

In PowerShell window 1, from the repository root, activate the environment and start the backend:

```powershell
& "$env:TEMP\asccd313\Scripts\Activate.ps1"
python -m uvicorn src.api.main:app --reload --port 8001
```

Open Swagger at <http://127.0.0.1:8001/api/docs>. Expand each section and use **Try it out** on these endpoints:

| Endpoint | What to point out |
| --- | --- |
| `GET /api/health` | Confirms the API is running. |
| `GET /api/health/ready` | Checks the API and local database. |
| `GET /api/project/status` | Returns the current project/module status. |
| `GET /api/project/team` | Returns team roles and responsibilities. |

The `/api/docs` path is intentional; `/docs` returns Not Found because the app customizes the Swagger route.

The project status values returned by `/api/project/status` are currently hardcoded scaffold data and do not reflect the completed preprocessing stage. Use this endpoint to demonstrate the API response; use the pipeline run and validation report to demonstrate data-pipeline progress.

### 3. Inspect the input data

In PowerShell window 2, activate the environment and inspect the raw CSV:

```powershell
& "$env:TEMP\asccd313\Scripts\Activate.ps1"
python scripts\preprocess.py --inspect
```

Point out the file size, row and column counts, and detected label column. The development sample contains generated data and is only being used to demonstrate the pipeline.

### 4. Run preprocessing and validation

Run a reproducible 5,000-row sample through the pipeline:

```powershell
python scripts\preprocess.py --sample 5000
python scripts\preprocess.py --validate
```

Explain the key stages as they appear in the terminal:

1. Load and clean the CSV, including normalizing attack labels and handling missing values.
2. Split data into training, validation, and test sets.
3. Fit scaling and feature-selection transformations on the training set only to help prevent data leakage.
4. Save the processed splits and preprocessing artifacts.
5. Run the validator and review its report.

With the checked-in 50,000-row development sample and seed 42, the 5,000-row run cleaned 86 rows, produced splits of 3,437 / 736 / 737 rows, retained 71 features, and passed all 13 validation checks. Counts can differ if the input sample changes.

### 5. Show the preprocessing artifacts

Open `data\processed\validation_report.md` and `data\processed\class_distribution_splits.png`. The processed split files are `train.csv`, `val.csv`, and `test.csv`; pipeline metadata and transformer artifacts are saved alongside them.

### 6. Train CTGAN, generate rows, and validate them

The GAN is fitted only on `train.csv`; validation and test splits are not used. Use the short development run for a live demo:

```powershell
python scripts\train_ctgan_demo.py train --epochs 5
python scripts\train_ctgan_demo.py generate --count 500
python scripts\train_ctgan_demo.py validate --input data\processed\train.csv
```

Training reads `data\processed\train.csv` only; validation and test splits are not used. The checkpoint is `artifacts\models\ctgan\model.pkl`, with run metadata in `artifacts\models\ctgan\model.metadata.json`. Each generation run creates a new file, starting with `data\generated\ctgan_samples.csv` and then using numbered names such as `ctgan_samples_2.csv`; existing samples are never overwritten. Rows include a `data_origin=synthetic_ctgan` column. Validation without `--output` automatically selects the most recently generated CTGAN sample and creates a correspondingly named validation report. Pass `--output <sample.csv>` to validate a specific sample.

The report includes schema match, synthetic label proportions, duplicate ratio, non-finite numeric values, and per-feature Kolmogorov–Smirnov (KS) statistics. Lower KS values indicate closer marginal feature distributions. In the demo run on the 3,437-row development training split, 5 epochs and 500 generated rows, the observed mean KS statistic was about **0.258** and the maximum was **0.756**. Schema matched, with no duplicate rows or non-finite numeric values. This small prototype result shows some feature distributions still differ substantially; the checks do not establish downstream utility or improved RL defense. Runtime depends on hardware. Five epochs is the short demo setting; the configured research run uses more epochs.

To request class-targeted sample counts, pass JSON counts, for example:

```powershell
python scripts\train_ctgan_demo.py generate --per-class '{"benign":250,"dos":250}'
```

## Suggested short explanation

> “Our demo covers the backend API, CIC-IDS2017 preprocessing, and a prototype CTGAN workflow. We fit the generator on the training split, produce clearly marked synthetic rows, and inspect basic fidelity and validity metrics. The development input is generated sample data, so this demonstrates the pipeline rather than results on the full CIC-IDS2017 corpus. Supply-chain simulation and RL defense remain future implementation stages.”

Command to create synthetic datasets
python scripts\train_ctgan_demo.py generate --count 500
