#!/usr/bin/env python3
"""
Download the CIC-IDS2017 dataset.

Downloads from the public mirror. Supports --sample flag for development.

Usage:
    python scripts/download_dataset.py
    python scripts/download_dataset.py --sample 50000
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Download CIC-IDS2017 dataset")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "raw"),
        help="Directory to save raw data files",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="If set, create a random sample of N rows for development",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("CIC-IDS2017 Dataset Download")
    print("=" * 60)
    print()
    print("The CIC-IDS2017 dataset is available from:")
    print("  https://www.unb.ca/cic/datasets/ids-2017.html")
    print()
    print("Due to the large size (~6GB), automatic download is not")
    print("supported. Please download manually and place CSV files in:")
    print(f"  {output_dir}")
    print()
    print("Expected files:")
    print("  - Monday-WorkingHours.pcap_ISCX.csv")
    print("  - Tuesday-WorkingHours.pcap_ISCX.csv")
    print("  - Wednesday-workingHours.pcap_ISCX.csv")
    print("  - Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv")
    print("  - Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv")
    print("  - Friday-WorkingHours-Morning.pcap_ISCX.csv")
    print("  - Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
    print("  - Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")
    print()

    # Check if files already exist
    csv_files = list(output_dir.glob("*.csv"))
    if csv_files:
        print(f"Found {len(csv_files)} CSV files in {output_dir}:")
        for f in sorted(csv_files):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  {f.name} ({size_mb:.1f} MB)")

        if args.sample:
            print(f"\nCreating sample of {args.sample} rows...")
            _create_sample(csv_files, args.sample, output_dir)
    else:
        print("No CSV files found. Please download the dataset first.")
        print()
        print("Quick option for development:")
        print("  A synthetic sample can be generated after the preprocessing")
        print("  pipeline is implemented (Phase 2).")
        sys.exit(0)


def _create_sample(csv_files, sample_size, output_dir):
    """Create a random sample from the dataset for development."""
    try:
        import pandas as pd
    except ImportError:
        print("pandas is required. Install with: pip install pandas")
        sys.exit(1)

    frames = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, encoding="utf-8", low_memory=False)
            frames.append(df)
            print(f"  Loaded {f.name}: {len(df)} rows")
        except Exception as e:
            print(f"  Warning: Could not load {f.name}: {e}")

    if not frames:
        print("No data loaded.")
        return

    combined = pd.concat(frames, ignore_index=True)
    print(f"\nTotal rows: {len(combined)}")

    sample = combined.sample(n=min(sample_size, len(combined)), random_state=42)
    sample_path = output_dir / "sample.csv"
    sample.to_csv(sample_path, index=False)
    print(f"Sample saved to {sample_path} ({len(sample)} rows)")


if __name__ == "__main__":
    main()
