#!/usr/bin/env python3
"""
ASCCD Controlled Experiments Execution CLI.

Executes scientific benchmarking across Experiment A (Rule-Based Baseline),
Experiment B (DQN without GAN), Experiment C (DQN with GAN), and Experiment D (PPO).
Exports publication reports, figures, and persists results to the database.

Usage:
    python scripts/run_experiments.py --dev-mode
    python scripts/run_experiments.py --experiments A B C --episodes 50
    python scripts/run_experiments.py --experiments A B C D --episodes 100
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.database import get_db_session
from src.common.logging import get_logger
from src.evaluation import EvaluationEngine

logger = get_logger("run_experiments")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for experiment execution."""
    parser = argparse.ArgumentParser(
        description="Run ASCCD controlled benchmark experiments A, B, C, and D."
    )
    parser.add_argument(
        "--experiments",
        nargs="+",
        default=["A", "B", "C"],
        help="List of experiment IDs to execute (default: A B C).",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=None,
        help="Number of evaluation episodes per experiment (default: from config or 10 in dev-mode).",
    )
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Run in accelerated development mode (shorter episodes, fast training).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/evaluation.yaml"),
        help="Path to evaluation configuration YAML (default: config/evaluation.yaml).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/reports"),
        help="Directory to save JSON and CSV reports (default: artifacts/reports).",
    )
    return parser.parse_args()


def main() -> int:
    """Execute evaluation experiments pipeline."""
    args = parse_args()
    logger.info(
        "Initializing ASCCD Evaluation Engine...",
        experiments=args.experiments,
        dev_mode=args.dev_mode,
    )

    engine = EvaluationEngine(config_path=args.config)

    # Execute all experiments with optional database logging
    try:
        with get_db_session() as session:
            summary = engine.run_all_experiments(
                experiment_ids=args.experiments,
                n_episodes=args.episodes,
                dev_mode=args.dev_mode,
                session=session,
            )
    except Exception as e:
        logger.warning("running_without_db_session", error=str(e))
        summary = engine.run_all_experiments(
            experiment_ids=args.experiments,
            n_episodes=args.episodes,
            dev_mode=args.dev_mode,
            session=None,
        )

    # Export reports and figures
    json_path, csv_path, fig_path = engine.export_reports(summary, output_dir=args.output_dir)

    # Print summary table to terminal
    print("\n" + "=" * 78)
    print("ASCCD CONTROLLED BENCHMARK EXPERIMENTS SUMMARY")
    print("=" * 78)
    print(f"{'Exp':<4} | {'Condition Name':<22} | {'Model':<10} | {'Mitig %':<8} | {'Avail %':<8} | {'Reward':<10}")
    print("-" * 78)
    for exp_id, res in summary.experiments.items():
        print(
            f"{exp_id:<4} | {res.name:<22} | {res.model_type:<10} | "
            f"{res.mitigation_success_rate * 100.0:>6.1f}% | "
            f"{res.service_availability * 100.0:>6.1f}% | "
            f"{res.mean_reward:>7.2f} ± {res.std_reward:<4.1f}"
        )
    print("-" * 78)

    if summary.relative_gains:
        print("\nRELATIVE IMPROVEMENTS & SCIENTIFIC VALUE-ADD:")
        for comp_name, gains in summary.relative_gains.items():
            print(f"  • {comp_name.replace('_', ' ')}:")
            if "mitigation_delta_pct" in gains:
                sign = "+" if gains["mitigation_delta_pct"] >= 0 else ""
                print(f"      - Mitigation Gain:    {sign}{gains['mitigation_delta_pct']:.1f}%")
            if "reward_delta" in gains:
                sign = "+" if gains["reward_delta"] >= 0 else ""
                print(f"      - Mean Reward Delta:  {sign}{gains['reward_delta']:.2f}")
            if "availability_delta_pct" in gains:
                sign = "+" if gains["availability_delta_pct"] >= 0 else ""
                print(f"      - Availability Delta: {sign}{gains['availability_delta_pct']:.1f}%")

    print("\nARTIFACT REPORTS EXPORTED:")
    print(f"  • Summary JSON:  {json_path}")
    print(f"  • Metrics CSV:   {csv_path}")
    if fig_path:
        print(f"  • Comparison Fig: {fig_path}")
    print("=" * 78 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
