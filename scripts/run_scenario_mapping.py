#!/usr/bin/env python3
"""
ASCCD Attack Scenario Mapping CLI.

Processes preprocessed real data or CTGAN-generated synthetic data into
structured supply-chain attack scenarios.

Usage:
    python scripts/run_scenario_mapping.py --input data/processed/test.csv --source real
    python scripts/run_scenario_mapping.py --input data/generated/synthetic_attacks.csv --source synthetic --save-db
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.common.database import get_db_session
from src.common.logging import get_logger
from src.scenarios.mapper import ScenarioMapper

logger = get_logger("run_scenario_mapping")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Map network intrusion records to supply chain attack scenarios."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to input CSV containing attack records (real or synthetic)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/reports/mapped_scenarios.json"),
        help="Path to save mapped scenarios JSON (default: artifacts/reports/mapped_scenarios.json)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="real",
        choices=["real", "synthetic"],
        help="Data source identifier (real or synthetic)",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Maximum records to map (default: all)",
    )
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Persist mapped scenarios to the database",
    )
    return parser.parse_args()


def main() -> int:
    """Execute scenario mapping workflow."""
    args = parse_args()

    if not args.input.exists():
        logger.error("Input file not found", path=str(args.input))
        return 1

    logger.info("Loading input records for scenario mapping", path=str(args.input))
    df = pd.read_csv(args.input)
    logger.info("Loaded dataset successfully", rows=len(df), cols=len(df.columns))

    mapper = ScenarioMapper()
    scenarios = mapper.map_dataframe(df, source=args.source, max_records=args.max_records)
    logger.info("Mapped records to supply chain scenarios", count=len(scenarios))

    # Stage distribution summary
    stage_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for s in scenarios:
        stage_counts[s.affected_stage] = stage_counts.get(s.affected_stage, 0) + 1
        severity_counts[s.severity] = severity_counts.get(s.severity, 0) + 1

    logger.info("Scenario stage distribution", **stage_counts)
    logger.info("Scenario severity distribution", **severity_counts)

    # Save to JSON
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump([s.to_dict() for s in scenarios], f, indent=2)
    logger.info("Exported mapped scenarios", output_file=str(args.output))

    # Save to database if requested
    if args.save_db:
        from src.common.database import init_db
        init_db()
        logger.info("Persisting mapped scenarios to database...")
        with get_db_session() as session:
            count = mapper.save_to_db(scenarios, session)
        logger.info("Saved scenarios to database", inserted=count)

    return 0


if __name__ == "__main__":
    sys.exit(main())
