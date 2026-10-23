#!/usr/bin/env python3
"""
ASCCD Rule-Based Baseline Evaluation CLI.

Executes systematic benchmark evaluation of the deterministic heuristic defense
policy across configurable simulation episodes and exports results.

Usage:
    python scripts/run_baseline.py --episodes 50
    python scripts/run_baseline.py --episodes 100 --output artifacts/reports/baseline_results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gymnasium as gym
from src.baselines import RuleBasedDefensePolicy
from src.common.logging import get_logger

logger = get_logger("run_baseline")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for baseline evaluation."""
    parser = argparse.ArgumentParser(
        description="Run benchmark evaluation of the rule-based defense policy."
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=50,
        help="Total evaluation episodes to execute (default: 50)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Initial random seed for reproducible evaluation (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/reports/baseline_results.json"),
        help="Path to export evaluation metrics JSON (default: artifacts/reports/baseline_results.json)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/baseline.yaml"),
        help="Path to custom baseline configuration YAML (default: config/baseline.yaml)",
    )
    return parser.parse_args()


def main() -> int:
    """Execute baseline evaluation."""
    args = parse_args()
    logger.info("Initializing rule-based baseline policy...", episodes=args.episodes, seed=args.seed)

    policy = RuleBasedDefensePolicy(config_path=args.config)
    env = gym.make("asccd/SupplyChain-v0")

    logger.info("Running evaluation episodes...")
    results = policy.evaluate(env, n_episodes=args.episodes, seed=args.seed)
    env.close()

    # Log summary
    logger.info(
        "Baseline evaluation completed",
        mean_reward=results.mean_reward,
        mitigation_rate=f"{results.mitigation_rate * 100:.1f}%",
        mean_availability=f"{results.mean_availability * 100:.1f}%",
        mean_episode_length=results.mean_episode_length,
    )

    # Print summary to terminal
    print("\n" + "=" * 55)
    print("RULE-BASED DEFENSE BASELINE (EXPERIMENT A) SUMMARY")
    print("=" * 55)
    print(f"Policy Name:          {results.policy_name}")
    print(f"Total Episodes:       {results.n_episodes}")
    print(f"Mean Cumulative Rew:  {results.mean_reward:.2f} ± {results.std_reward:.2f}")
    print(f"Mitigation Rate:      {results.mitigation_rate * 100:.1f}% ({results.mitigated_episodes}/{results.n_episodes})")
    print(f"Mean Service Uptime:  {results.mean_availability * 100:.1f}%")
    print(f"Mean Steps/Episode:   {results.mean_episode_length:.1f}")
    print("\nAction Distribution:")
    for action, count in results.action_distribution.items():
        pct = (count / max(1, sum(results.action_distribution.values()))) * 100.0
        print(f"  - {action:<10}: {count:5d} ({pct:5.1f}%)")
    print("=" * 55 + "\n")

    # Save to JSON
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results.to_dict(), f, indent=2)
    logger.info("Saved baseline evaluation report", path=str(args.output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
