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
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gymnasium as gym
import pandas as pd
from src.common.logging import get_logger
from src.environment.supply_chain_env import STAGE_NAMES, SupplyChainEnv
from src.rl import DQNDefenseAgent
from src.scenarios.mapper import ScenarioMapper
from src.scenarios.models import AttackScenario

logger = get_logger("train_dqn")
BENIGN_LABELS = {"0", "0.0", "benign", "normal"}
SAMPLES_PER_CATEGORY = 50
EVALUATION_SAMPLES_PER_CATEGORY = 10


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
        "--data-root",
        type=Path,
        default=PROJECT_ROOT / "data",
        help="Root directory containing processed and generated training data.",
    )
    parser.add_argument(
        "--evaluation-data-root",
        type=Path,
        default=None,
        help="Optional data root whose processed/test.csv is used for held-out evaluation.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("artifacts/reports/dqn_training_report.json"),
        help="Path to export JSON training and evaluation summary report.",
    )
    return parser.parse_args()


def sample_balanced_rows(
    sources: list[tuple[pd.DataFrame, str]],
    seed: int,
    include_benign: bool,
    samples_per_category: int = SAMPLES_PER_CATEGORY,
) -> pd.DataFrame:
    """Take a reproducible, per-label sample from real and synthetic data."""
    labeled_frames = []
    for frame, source in sources:
        if "Label" not in frame.columns or frame.empty:
            continue
        labeled = frame.copy()
        labeled["_training_source"] = source
        labeled["_training_label"] = labeled["Label"].astype(str).str.strip().str.lower()
        if not include_benign:
            labeled = labeled[~labeled["_training_label"].isin(BENIGN_LABELS)]
        if not labeled.empty:
            labeled_frames.append(labeled)

    if not labeled_frames:
        return pd.DataFrame()

    combined = pd.concat(labeled_frames, ignore_index=True)
    balanced = [
        group.sample(n=min(samples_per_category, len(group)), random_state=seed)
        for _, group in combined.groupby("_training_label", sort=True)
    ]
    return (
        pd.concat(balanced, ignore_index=True)
        .sample(frac=1.0, random_state=seed)
        .reset_index(drop=True)
    )


def build_training_scenarios(
    rows: pd.DataFrame,
    mapper: ScenarioMapper,
    condition: str,
) -> list[AttackScenario]:
    """Map each sampled row to all supply-chain stages."""
    scenarios = []
    for index, row in rows.iterrows():
        record = row.drop(labels=["_training_source", "_training_label"]).to_dict()
        source = str(row["_training_source"])
        for stage in STAGE_NAMES:
            scenarios.append(
                mapper.map_record(
                    record,
                    source=source,
                    scenario_id=f"train_{condition}_{index:05d}_{stage}",
                    affected_stage=stage,
                )
            )
    return scenarios


def load_scenarios_for_condition(
    condition: str,
    seed: int = 42,
    data_root: Path | None = None,
) -> list[AttackScenario] | None:
    """Load balanced real or real-plus-CTGAN scenarios for training."""
    if condition == "default":
        return None

    data_root = Path(data_root) if data_root is not None else PROJECT_ROOT / "data"
    real_path = data_root / "processed" / "train.csv"
    if not real_path.is_file():
        raise FileNotFoundError(f"Training split is required for {condition!r}: {real_path}")

    sources = [(pd.read_csv(real_path), "real")]
    include_benign = condition == "augmented"
    if condition == "augmented":
        synthetic_paths = (
            data_root / "generated" / "synthetic_attacks.csv",
            data_root / "generated" / "ctgan_samples.csv",
            data_root / "generated" / "ui_synthetic_attacks.csv",
        )
        synthetic_path = next((path for path in synthetic_paths if path.is_file()), None)
        if synthetic_path is None:
            raise FileNotFoundError(
                "Augmented training requires CTGAN samples; generate them before training."
            )
        sources.append((pd.read_csv(synthetic_path), "synthetic"))

    rows = sample_balanced_rows(
        sources,
        seed=seed,
        include_benign=include_benign,
    )
    if rows.empty:
        raise ValueError(f"No labeled training rows available for {condition!r}.")

    mapper = ScenarioMapper(config_path=PROJECT_ROOT / "config" / "scenario.yaml")
    scenarios = build_training_scenarios(rows, mapper, condition)
    logger.info(
        "loaded_balanced_scenarios",
        condition=condition,
        row_labels=rows["_training_label"].value_counts().to_dict(),
        scenarios=len(scenarios),
        stages=list(STAGE_NAMES),
    )
    return scenarios


def load_evaluation_scenarios(data_root: Path, seed: int = 42) -> list[AttackScenario]:
    """Build a balanced evaluation scenario set from the held-out test split."""
    test_path = Path(data_root) / "processed" / "test.csv"
    if not test_path.is_file():
        raise FileNotFoundError(f"Evaluation split is required: {test_path}")

    rows = sample_balanced_rows(
        [(pd.read_csv(test_path), "real")],
        seed=seed,
        include_benign=True,
        samples_per_category=EVALUATION_SAMPLES_PER_CATEGORY,
    )
    if rows.empty:
        raise ValueError(f"No labeled evaluation rows available in {test_path}.")

    mapper = ScenarioMapper(config_path=PROJECT_ROOT / "config" / "scenario.yaml")
    scenarios = build_training_scenarios(rows, mapper, "evaluation")
    logger.info(
        "loaded_held_out_evaluation_scenarios",
        source=str(test_path),
        row_labels=rows["_training_label"].value_counts().to_dict(),
        scenarios=len(scenarios),
        stages=list(STAGE_NAMES),
    )
    return scenarios


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
    scenarios = load_scenarios_for_condition(
        args.condition,
        seed=args.seed,
        data_root=args.data_root,
    )
    if args.condition == "default":
        env = gym.make("asccd/SupplyChain-v0")
    else:
        if not scenarios:
            raise ValueError(f"No scenarios loaded for training condition {args.condition!r}.")
        logger.info(
            "Custom scenarios loaded for condition",
            count=len(scenarios),
            condition=args.condition,
        )
        env = SupplyChainEnv(scenarios=scenarios)

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

    # 4. Evaluate on held-out scenarios when an evaluation data root is supplied.
    evaluation_env = env
    evaluation_episodes = args.episodes
    if args.evaluation_data_root is not None:
        evaluation_scenarios = load_evaluation_scenarios(
            args.evaluation_data_root,
            seed=args.seed,
        )
        evaluation_env = SupplyChainEnv(scenarios=evaluation_scenarios)
        evaluation_episodes = len(evaluation_scenarios)

    eval_result = agent.evaluate(
        evaluation_env,
        n_episodes=evaluation_episodes,
        seed=args.seed,
    )
    evaluation_env.close()
    if evaluation_env is not env:
        env.close()

    # 5. Export report
    report_data = {
        "training": training_result.to_dict(),
        "evaluation": eval_result.to_dict(),
        "evaluation_data_root": (
            str(args.evaluation_data_root) if args.evaluation_data_root is not None else None
        ),
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
    print(
        f"Mitigation Rate:       {eval_result.mitigation_rate * 100:.1f}% ({eval_result.mitigated_episodes}/{eval_result.n_episodes})"
    )
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
