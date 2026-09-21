#!/usr/bin/env python3
"""
ASCCD Dataset Download and Ingestion Helper for CIC-IDS2017.

Provides guided acquisition of the Canadian Institute for Cybersecurity
CIC-IDS2017 benchmark dataset, verification of raw CSV files, creation
of downsampled development sets, and generation of synthetic development
samples for local verification without downloading 6GB of raw data.

Usage:
    # 1. Show instructions & check existing files:
    python scripts/download_dataset.py

    # 2. Generate a synthetic development sample (e.g. 5,000 or 50,000 rows):
    python scripts/download_dataset.py --generate-dev-sample --rows 50000

    # 3. Create a development sample from existing full raw CSVs:
    python scripts/download_dataset.py --sample 50000

Author: Deekshay G (primary), reviewed by Anandavarthan & Dev Virat
"""

import argparse
import sys
from pathlib import Path
from typing import Any

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.logging import get_logger

logger = get_logger(__name__)

CANONICAL_FILES = [
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
]

# Standard CIC-IDS2017 column names (subset of key numerical columns + label)
REPRESENTATIVE_COLUMNS = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd IAT Total",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",
    "Bwd IAT Total",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Max",
    "Bwd IAT Min",
    "Fwd PSH Flags",
    "Bwd PSH Flags",
    "Fwd URG Flags",
    "Bwd URG Flags",
    "Fwd Header Length",
    "Bwd Header Length",
    "Fwd Packets/s",
    "Bwd Packets/s",
    "Min Packet Length",
    "Max Packet Length",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",
    "FIN Flag Count",
    "SYN Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "CWE Flag Count",
    "ECE Flag Count",
    "Down/Up Ratio",
    "Average Packet Size",
    "Avg Fwd Segment Size",
    "Avg Bwd Segment Size",
    "Fwd Header Length.1",
    "Subflow Fwd Packets",
    "Subflow Fwd Bytes",
    "Subflow Bwd Packets",
    "Subflow Bwd Bytes",
    "Init_Win_bytes_forward",
    "Init_Win_bytes_backward",
    "act_data_pkt_fwd",
    "min_seg_size_forward",
    "Active Mean",
    "Active Std",
    "Active Max",
    "Active Min",
    "Idle Mean",
    "Idle Std",
    "Idle Max",
    "Idle Min",
    "Label",
]


def generate_dev_sample(output_path: Path, num_rows: int = 50000, seed: int = 42) -> None:
    """Generate a realistic development sample CSV matching CIC-IDS2017 schema.

    Enables offline development and CI/CD testing of the full pipeline without
    requiring the full 6GB multi-file archive.
    """
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed)
    print(f"Generating realistic development dataset ({num_rows:,} rows)...")

    # Class distribution matching realistic attack frequencies in IDS benchmarks
    classes = [
        "BENIGN",
        "DoS Hulk",
        "PortScan",
        "DDoS",
        "DoS GoldenEye",
        "FTP-Patator",
        "SSH-Patator",
        "DoS slowloris",
        "DoS Slowhttptest",
        "Bot",
        "Web Attack \x96 Brute Force",
        "Infiltration",
    ]
    weights = [
        0.80,
        0.08,
        0.04,
        0.03,
        0.015,
        0.01,
        0.01,
        0.005,
        0.005,
        0.003,
        0.0015,
        0.0005,
    ]
    weights = np.array(weights) / sum(weights)

    labels = rng.choice(classes, size=num_rows, p=weights)

    data: dict[str, Any] = {}

    for col in REPRESENTATIVE_COLUMNS[:-1]:
        if "Port" in col:
            data[f" {col}"] = rng.choice([80, 443, 21, 22, 8080, 53, 445, 3389], size=num_rows)
        elif "Flag Count" in col or "Flags" in col:
            data[f" {col}"] = rng.choice([0, 1], size=num_rows, p=[0.85, 0.15])
        elif "Duration" in col or "IAT" in col or "Bytes" in col:
            # Positive skewed distribution typical in network traffic
            vals = rng.exponential(scale=1000.0, size=num_rows)
            # Inject a tiny percentage of inf / nan for robust cleaning test
            inject_idx = rng.choice(num_rows, size=max(1, int(num_rows * 0.001)), replace=False)
            vals[inject_idx] = np.nan
            data[f" {col}"] = vals
        else:
            data[f" {col}"] = np.maximum(0, rng.normal(loc=50.0, scale=30.0, size=num_rows))

    # Add label with occasional whitespace quirks as in raw CIC-IDS2017
    data[" Label"] = labels

    df = pd.DataFrame(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✅ Development sample written to {output_path} ({size_mb:.2f} MB, {len(df)} rows)")
    print("Class counts:")
    for k, v in df[" Label"].value_counts().items():
        print(f"  {k}: {v}")


def create_sample_from_raw(
    csv_files: list[Path], sample_size: int, output_dir: Path, seed: int = 42
) -> None:
    """Create a downsampled development CSV from existing raw CSV files."""
    import pandas as pd

    frames = []
    print(f"Reading from {len(csv_files)} existing CSV files...")
    for f in csv_files:
        try:
            # Sample per file to maintain distribution
            df_file = pd.read_csv(f, nrows=sample_size, low_memory=False)
            frames.append(df_file)
            print(f"  Loaded {f.name}: {len(df_file)} rows")
        except Exception as e:
            print(f"  Warning: could not read {f.name}: {e}")

    if not frames:
        print("❌ No data could be loaded.")
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    if len(combined) > sample_size:
        combined = combined.sample(n=sample_size, random_state=seed).reset_index(drop=True)

    out_file = output_dir / f"CIC-IDS2017_dev_sample_{sample_size}.csv"
    combined.to_csv(out_file, index=False)
    print(f"✅ Downsampled development dataset saved: {out_file} ({len(combined)} rows)")


def main():
    parser = argparse.ArgumentParser(
        description="Acquire or sample the CIC-IDS2017 dataset for ASCCD."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "raw"),
        help="Directory where raw CSV files are placed.",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Sample N rows from existing raw CSV files to create a dev sample.",
    )
    parser.add_argument(
        "--generate-dev-sample",
        action="store_true",
        help="Generate a synthetic development sample for local offline testing.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=50000,
        help="Number of rows for synthetic dev sample (default: 50,000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling or synthetic generation.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("ASCCD: CIC-IDS2017 Dataset Acquisition & Ingestion Manager")
    print("=" * 65)

    if args.generate_dev_sample:
        out_file = output_dir / "CIC-IDS2017_dev_sample.csv"
        generate_dev_sample(out_file, num_rows=args.rows, seed=args.seed)
        return

    csv_files = sorted(output_dir.glob("*.csv"))
    if csv_files:
        print(f"\nFound {len(csv_files)} CSV files in {output_dir}:")
        total_bytes = 0
        for f in csv_files:
            sz = f.stat().st_size
            total_bytes += sz
            print(f"  - {f.name} ({sz / (1024 * 1024):.2f} MB)")
        print(f"Total raw size: {total_bytes / (1024 * 1024 * 1024):.2f} GB")

        if args.sample:
            create_sample_from_raw(csv_files, args.sample, output_dir, seed=args.seed)
        else:
            print("\nDataset is present. Run preprocessing using:")
            print("  python scripts/preprocess.py")
            print("Or validate raw inspection using:")
            print("  python scripts/preprocess.py --inspect")
    else:
        print("\nNo CSV files found in:", output_dir)
        print("\nFull Dataset Download Instructions:")
        print("  1. Visit the official UNB portal:")
        print("     https://www.unb.ca/cic/datasets/ids-2017.html")
        print("  2. Download 'GeneratedLabelledFlows.zip' (~2.5GB compressed, ~6GB uncompressed).")
        print(f"  3. Extract all 8 CSV files into: {output_dir.resolve()}/\n")
        print("Expected canonical CSV files:")
        for fname in CANONICAL_FILES:
            print(f"  - {fname}")
        print("\nDevelopment Mode (Quickstart without full download):")
        print("  Run this script with --generate-dev-sample to create a realistic")
        print("  50,000-row development sample matching the exact schema:")
        print("    python scripts/download_dataset.py --generate-dev-sample --rows 50000")
        print("=" * 65)


if __name__ == "__main__":
    main()
