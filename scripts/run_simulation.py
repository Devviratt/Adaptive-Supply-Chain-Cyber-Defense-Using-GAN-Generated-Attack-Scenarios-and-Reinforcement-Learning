#!/usr/bin/env python3
"""
ASCCD Supply Chain Environment Simulation CLI.

Runs interactive or benchmark simulation episodes in the custom
Gymnasium supply-chain cyber-defense environment.

Usage:
    python scripts/run_simulation.py --episodes 3 --render
    python scripts/run_simulation.py --episodes 10 --policy random
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gymnasium as gym
import numpy as np
from src.common.logging import get_logger
from src.environment import DefenseAction

logger = get_logger("run_simulation")


def parse_args() -> argparse.Namespace:
    """Parse CLI options for simulation runner."""
    parser = argparse.ArgumentParser(
        description="Run supply-chain cyber-defense simulation episodes."
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=3,
        help="Number of simulation episodes to execute (default: 3)",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="heuristic",
        choices=["heuristic", "random", "passive"],
        help="Defense action selection policy (heuristic, random, passive)",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Print ASCII visualization of supply-chain stages per step",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for simulation reproducibility",
    )
    return parser.parse_args()


def select_heuristic_action(obs: np.ndarray) -> int:
    """Simple operational heuristic for demonstration before Phase 6 baseline."""
    # obs: [s_h, s_r, b_h, b_r, r_h, r_r, d_h, d_r, sev, tgt, prop, step]
    risks = [obs[1], obs[3], obs[5], obs[7]]
    healths = [obs[0], obs[2], obs[4], obs[6]]
    max_risk = max(risks)
    min_health = min(healths)

    if max_risk >= 0.6:
        return DefenseAction.REBUILD
    elif max_risk >= 0.3:
        return DefenseAction.ISOLATE
    elif min_health < 0.5:
        return DefenseAction.RECOVER
    elif max_risk > 0.15:
        return DefenseAction.BLOCK
    return DefenseAction.MONITOR


def main() -> int:
    """Run simulation loop across episodes."""
    args = parse_args()
    logger.info("Initializing supply-chain simulation environment...", episodes=args.episodes, policy=args.policy)

    env = gym.make("asccd/SupplyChain-v0")
    rng = np.random.default_rng(args.seed)

    episode_rewards: list[float] = []
    mitigated_count = 0

    for ep in range(args.episodes):
        obs, info = env.reset(seed=int(args.seed + ep))
        ep_reward = 0.0
        terminated = False
        truncated = False
        step = 0

        logger.info(
            f"--- Starting Episode {ep + 1}/{args.episodes} ---",
            scenario=info["attack_category"],
            target=info["affected_stage"],
            severity=info["severity"],
        )

        while not (terminated or truncated):
            step += 1
            if args.policy == "random":
                action = int(rng.integers(0, 5))
            elif args.policy == "passive":
                action = DefenseAction.MONITOR
            else:
                action = select_heuristic_action(obs)

            obs, reward, terminated, truncated, step_info = env.step(action)
            ep_reward += reward

            if args.render:
                print(env.render())

        episode_rewards.append(ep_reward)
        if step_info.get("mitigated", False):
            mitigated_count += 1

        logger.info(
            f"Episode {ep + 1} finished",
            steps=step,
            reward=round(ep_reward, 2),
            mitigated=step_info.get("mitigated", False),
        )

    env.close()

    mean_rew = float(np.mean(episode_rewards))
    mit_rate = (mitigated_count / args.episodes) * 100.0

    print("\n" + "=" * 50)
    print("SIMULATION SUMMARY")
    print("=" * 50)
    print(f"Episodes:           {args.episodes}")
    print(f"Policy:             {args.policy.capitalize()}")
    print(f"Mean Reward:        {mean_rew:.2f}")
    print(f"Mitigation Rate:    {mit_rate:.1f}% ({mitigated_count}/{args.episodes})")
    print("=" * 50 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
