#!/usr/bin/env python3
"""
ASCCD DQN Defense Agent Training CLI.

Executes autonomous reinforcement learning agent training using Stable-Baselines3
on the Gymnasium supply chain cyber defense environment. Supports real-only,
GAN-augmented, and dev-mode training workflows.

Usage:
    python scripts/train_dqn.py --dev-mode
    python scripts/train_dqn.py --timesteps 50000 --condition real_only
    python scripts/train_dqn.py --timesteps 50000 --condition augmented
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gymnasium as gym
import pandas as pd

from src.common.logging import get_logger
from src.environment.supply_chain_env import SupplyChainEnv
from src.rl import DQNDefenseAgent
from src.scenarios.mapper import ScenarioMapper
from src.scenarios.models import AttackScenario

logger = get_logger("train_dqn")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for DQN training."""
    parser = argparse.ArgumentParser(
        description="Train the ASCCD DQN reinforcement learning defense agent."
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=None,
        help="Total training environment interaction timesteps (overrides config).",
    )
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Run in accelerated development mode (shorter buffer, fewer timesteps).",
    )
    parser.add_argument(
        "--condition",
        type=str,
        choices=["default", "real_only", "augmented"],
        default="default",
        help="Experimental condition for scenario grounding: default, real_only, or augmented.",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=10,
        help="Number of evaluation episodes to run post-training (default: 10).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for environment and policy initialization (default: 42).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/dqn.yaml"),
        help="Path to DQN configuration YAML (default: config/dqn.yaml).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/models/dqn"),
        help="Directory to save model checkpoints and final weights (default: artifacts/models/dqn).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("artifacts/reports/dqn_training_report.json"),
        help="Path to export JSON training and evaluation summary report.",
    )
    return parser.parse_args()


def load_scenarios_for_condition(condition: str) -> list[AttackScenario] | None:
    """Load attack scenarios tailored to experimental conditions."""
    mapper = ScenarioMapper()

    if condition == "real_only":
        csv_path = Path("data/processed/train.csv")
        if not csv_path.exists():
            csv_path = Path("data/processed/test.csv")
        if csv_path.exists():
            logger.info("loading_real_scenarios", path=str(csv_path))
            df = pd.read_csv(csv_path)
            # Use representative sample of real attack records
            attack_df = df[df["Label"] != 0] if "Label" in df.columns else df
            sample_df = attack_df.head(200)
            return mapper.map_batch(sample_df)

    elif condition == "augmented":
        scenarios: list[AttackScenario] = []
        real_path = Path("data/processed/train.csv")
        if not real_path.exists():
            real_path = Path("data/processed/test.csv")
        if real_path.exists():
            df_real = pd.read_csv(real_path)
            attack_real = df_real[df_real["Label"] != 0] if "Label" in df_real.columns else df_real
            scenarios.extend(mapper.map_batch(attack_real.head(100)))

        syn_path = Path("data/generated/synthetic_attacks.csv")
        if syn_path.exists():
            logger.info("loading_synthetic_scenarios", path=str(syn_path))
            df_syn = pd.read_csv(syn_path)
            scenarios.extend(mapper.map_batch(df_syn.head(100)))

        if scenarios:
            return scenarios

    return None


def main() -> int:
    """Execute the DQN training pipeline."""
    args = parse_args()
    logger.info(
        "Starting DQN training pipeline...",
        condition=args.condition,
        dev_mode=args.dev_mode,
        seed=args.seed,
    )

    # 1. Prepare environment
    scenarios = load_scenarios_for_condition(args.condition)
    if scenarios:
        logger.info("Custom scenarios loaded for condition", count=len(scenarios), condition=args.condition)
        env = SupplyChainEnv(scenarios=scenarios)
    else:
        env = gym.make("asccd/SupplyChain-v0")

    # 2. Initialize DQN agent
    agent = DQNDefenseAgent(
        config_path=args.config,
        checkpoint_dir=str(args.output_dir),
        seed=args.seed,
        n_eval_episodes=args.episodes,
    )

    # 3. Train agent
    training_result = agent.train(
        env=env,
        total_timesteps=args.timesteps,
        dev_mode=args.dev_mode,
        condition=args.condition,
        checkpoint_dir=args.output_dir,
    )

    # 4. Comprehensive post-training evaluation
    eval_result = agent.evaluate(env, n_episodes=args.episodes, seed=args.seed)
    env.close()

    # 5. Export report
    report_data = {
        "training": training_result.to_dict(),
        "evaluation": eval_result.to_dict(),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    logger.info("Training and evaluation report saved", path=str(args.report))

    # 6. Display Summary to Terminal
    print("\n" + "=" * 60)
    print("ASCCD DQN DEFENSE AGENT TRAINING SUMMARY")
    print("=" * 60)
    print(f"Condition:             {args.condition}")
    print(f"Total Timesteps:       {training_result.total_timesteps:,}")
    print(f"Duration:              {training_result.training_duration_seconds:.2f} seconds")
    print(f"Model Path:            {training_result.model_path}")
    print(f"Checkpoints Generated: {len(training_result.checkpoints)}")
    print("-" * 60)
    print("POST-TRAINING BENCHMARK EVALUATION:")
    print(f"Evaluation Episodes:   {eval_result.n_episodes}")
    print(f"Mean Cumulative Rew:   {eval_result.mean_reward:.2f} ± {eval_result.std_reward:.2f}")
    print(f"Mitigation Rate:       {eval_result.mitigation_rate * 100:.1f}% ({eval_result.mitigated_episodes}/{eval_result.n_episodes})")
    print(f"Mean Service Uptime:   {eval_result.mean_availability * 100:.1f}%")
    print(f"Mean Steps/Episode:    {eval_result.mean_episode_length:.1f}")
    print("\nAction Distribution:")
    for action, count in eval_result.action_distribution.items():
        pct = (count / max(1, sum(eval_result.action_distribution.values()))) * 100.0
        print(f"  - {action:<10}: {count:5d} ({pct:5.1f}%)")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
