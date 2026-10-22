"""
ASCCD Evaluation and Experimentation Engine.

Executes scientific benchmark experiments A, B, C (and D) across varying defense
policies and data grounding regimes. Computes comprehensive multi-objective
security, availability, and decision-quality metrics, with automated reporting,
database persistence, and publication-ready visualization generation.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import pandas as pd
import structlog
import yaml

from src.baselines.rule_based import RuleBasedDefensePolicy
from src.environment.models import DefenseAction
from src.environment.supply_chain_env import SupplyChainEnv
from src.evaluation.models import ComparisonSummary, ExperimentResult
from src.rl.dqn_agent import DQNDefenseAgent
from src.rl.ppo_agent import PPODefenseAgent
from src.scenarios.mapper import ScenarioMapper
from src.scenarios.models import AttackScenario

logger = structlog.get_logger(__name__)


class EvaluationEngine:
    """Scientific evaluation engine for benchmarking adaptive supply-chain defense policies."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_path: str | Path | None = None,
    ) -> None:
        """Initialize the evaluation engine.

        Args:
            config: Optional pre-loaded evaluation configuration dictionary.
            config_path: Optional path to evaluation configuration YAML (default: config/evaluation.yaml).
        """
        self.config = self._load_config(config, config_path)
        eval_cfg = self.config.get("evaluation", {})

        self.experiments_cfg = {
            exp["id"]: exp for exp in eval_cfg.get("experiments", [])
        }
        self.n_eval_episodes = int(eval_cfg.get("n_eval_episodes", 50))
        self.seeds = list(eval_cfg.get("seeds", [42, 123, 456, 789, 1024]))
        self.use_held_out = bool(eval_cfg.get("use_held_out_scenarios", True))

        reports_cfg = eval_cfg.get("reports", {})
        self.output_dir = Path(reports_cfg.get("output_dir", "artifacts/reports"))
        self.figures_dir = Path(reports_cfg.get("figures_dir", "artifacts/figures"))
        self.generate_plots = bool(reports_cfg.get("generate_plots", True))

        self.scenario_mapper = ScenarioMapper()
        self._test_scenarios_cache: list[AttackScenario] | None = None

    def _load_config(
        self,
        config: dict[str, Any] | None,
        config_path: str | Path | None,
    ) -> dict[str, Any]:
        """Load YAML configuration safely."""
        if config is not None:
            return config
        path = Path(config_path) if config_path else Path("config/evaluation.yaml")
        if path.exists():
            try:
                with open(path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("failed_loading_eval_config", path=str(path), error=str(e))
        return {}

    def get_held_out_scenarios(self) -> list[AttackScenario]:
        """Retrieve held-out test attack scenarios from data/processed/test.csv."""
        if self._test_scenarios_cache is not None:
            return self._test_scenarios_cache

        test_path = Path("data/processed/test.csv")
        if test_path.exists():
            try:
                df = pd.read_csv(test_path)
                attack_df = df[df["Label"] != 0] if "Label" in df.columns else df
                self._test_scenarios_cache = self.scenario_mapper.map_batch(
                    attack_df.head(200), source="real"
                )
                logger.info(
                    "loaded_held_out_test_scenarios",
                    count=len(self._test_scenarios_cache),
                    path=str(test_path),
                )
                return self._test_scenarios_cache
            except Exception as e:
                logger.warning("failed_loading_held_out_test_csv", error=str(e))

        # Fallback to mapped default scenarios
        self._test_scenarios_cache = []
        return self._test_scenarios_cache

    def evaluate_policy(
        self,
        policy: Any,
        env: gym.Env,
        experiment_id: str,
        name: str,
        model_type: str,
        dataset: str,
        n_episodes: int | None = None,
        seeds: list[int] | None = None,
    ) -> ExperimentResult:
        """Run systematic evaluation of any policy on the environment.

        Args:
            policy: Policy object implementing `predict(obs)` (RuleBased, DQN, PPO).
            env: SupplyChainEnv instance.
            experiment_id: Condition identifier ("A", "B", "C", "D").
            name: Descriptive name.
            model_type: Policy architecture type.
            dataset: Data grounding type.
            n_episodes: Total evaluation episodes.
            seeds: List of seeds to cycle through across episodes.

        Returns:
            ExperimentResult with aggregated security, availability, and decision metrics.
        """
        total_episodes = n_episodes or self.n_eval_episodes
        eval_seeds = seeds or self.seeds
        n_seeds = len(eval_seeds)

        episode_rewards: list[float] = []
        availability_samples: list[float] = []
        total_downtime_steps = 0
        mitigated_episodes = 0
        contained_episodes = 0
        catastrophic_failures = 0
        cumulative_impact = 0.0

        unnecessary_actions = 0
        total_actions = 0
        response_step_samples: list[int] = []
        action_counts = {DefenseAction.get_name(a): 0 for a in range(5)}
        class_performance: dict[str, dict[str, Any]] = {}

        for ep in range(total_episodes):
            seed = eval_seeds[ep % n_seeds] + ep
            obs, info = env.reset(seed=seed)

            # Determine initial attack class and stage
            unwrapped_env = getattr(env, "unwrapped", env)
            active_scen = getattr(unwrapped_env, "active_scenario", None)
            attack_class = active_scen.attack_category if active_scen else "unknown"
            if active_scen:
                initial_target_stage = getattr(active_scen.affected_stage, "value", str(active_scen.affected_stage))
            else:
                initial_target_stage = "supplier"

            if attack_class not in class_performance:
                class_performance[attack_class] = {"total": 0, "mitigated": 0, "rewards": []}
            class_performance[attack_class]["total"] += 1

            ep_reward = 0.0
            steps = 0
            first_defense_step: int | None = None
            terminated = False
            truncated = False

            while not (terminated or truncated):
                steps += 1
                action, _ = policy.predict(obs, deterministic=True)
                action_name = DefenseAction.get_name(action)
                action_counts[action_name] += 1
                total_actions += 1

                # Track decision delay
                if action != int(DefenseAction.MONITOR) and first_defense_step is None:
                    first_defense_step = steps

                # Check for unnecessary intervention (aggressive action when no risk is present)
                risks = [obs[1], obs[3], obs[5], obs[7]] if len(obs) >= 8 else [0.0]
                if action in [int(DefenseAction.BLOCK), int(DefenseAction.REBUILD)] and max(risks) == 0.0:
                    unnecessary_actions += 1

                obs, reward, terminated, truncated, step_info = env.step(action)
                ep_reward += float(reward)

                mean_health = float(step_info.get("mean_health", 1.0))
                availability_samples.append(mean_health)
                if mean_health < 0.30:
                    total_downtime_steps += 1

                # Health deficit impact
                cumulative_impact += max(0.0, 1.0 - mean_health)

            episode_rewards.append(ep_reward)
            class_performance[attack_class]["rewards"].append(ep_reward)

            if first_defense_step is not None:
                response_step_samples.append(first_defense_step)
            else:
                response_step_samples.append(steps)

            # Outcomes
            is_mitigated = bool(step_info.get("mitigated", False))
            if is_mitigated:
                mitigated_episodes += 1
                class_performance[attack_class]["mitigated"] += 1

            if bool(step_info.get("catastrophic_failure", False)):
                catastrophic_failures += 1

            # Containment check: did compromise spread beyond initial target stage?
            stages = getattr(unwrapped_env, "stages", {})
            compromised_stages = [
                s_name for s_name, s_state in stages.items()
                if s_state.is_compromised
            ]
            if not compromised_stages or set(compromised_stages) == {initial_target_stage}:
                contained_episodes += 1

        mean_reward = float(np.mean(episode_rewards)) if episode_rewards else 0.0
        std_reward = float(np.std(episode_rewards)) if episode_rewards else 0.0
        reward_var = float(np.var(episode_rewards)) if episode_rewards else 0.0
        mitigation_rate = float(mitigated_episodes / total_episodes) if total_episodes > 0 else 0.0
        containment_rate = float(contained_episodes / total_episodes) if total_episodes > 0 else 0.0
        mean_avail = float(np.mean(availability_samples)) if availability_samples else 1.0
        mean_impact = float(cumulative_impact / total_episodes) if total_episodes > 0 else 0.0
        avg_response = float(np.mean(response_step_samples)) if response_step_samples else 0.0
        unnecessary_rate = float(unnecessary_actions / max(1, total_actions))

        # Summarize class breakdown
        formatted_class_perf: dict[str, dict[str, float]] = {}
        for c_name, c_data in class_performance.items():
            tot = c_data["total"]
            formatted_class_perf[c_name] = {
                "total_episodes": tot,
                "mitigation_rate": round(c_data["mitigated"] / tot, 4) if tot > 0 else 0.0,
                "mean_reward": round(float(np.mean(c_data["rewards"])), 2) if c_data["rewards"] else 0.0,
            }

        return ExperimentResult(
            experiment_id=experiment_id,
            name=name,
            model_type=model_type,
            dataset=dataset,
            n_episodes=total_episodes,
            seeds=eval_seeds,
            mitigation_success_rate=mitigation_rate,
            containment_rate=containment_rate,
            attack_impact_score=mean_impact,
            service_availability=mean_avail,
            total_downtime_steps=total_downtime_steps,
            unnecessary_intervention_rate=unnecessary_rate,
            avg_response_steps=avg_response,
            action_distribution=action_counts,
            mean_reward=mean_reward,
            std_reward=std_reward,
            reward_variance=reward_var,
            episode_rewards=episode_rewards,
            performance_by_attack_class=formatted_class_perf,
            catastrophic_failures=catastrophic_failures,
        )

    def run_experiment(
        self,
        experiment_id: str,
        n_episodes: int | None = None,
        seeds: list[int] | None = None,
        dev_mode: bool = False,
        session: Any = None,
    ) -> ExperimentResult:
        """Run an individual experiment condition by ID ('A', 'B', 'C', 'D')."""
        exp_cfg = self.experiments_cfg.get(experiment_id)
        if not exp_cfg:
            # Fallback default configurations
            defaults = {
                "A": {"name": "Rule-Based Baseline", "model_type": "rule_based", "dataset": "real"},
                "B": {"name": "DQN without GAN", "model_type": "dqn", "dataset": "real"},
                "C": {"name": "DQN with GAN", "model_type": "dqn_gan", "dataset": "real+synthetic"},
                "D": {"name": "PPO Comparison", "model_type": "ppo", "dataset": "real+synthetic"},
            }
            exp_cfg = defaults.get(
                experiment_id,
                {"name": f"Experiment {experiment_id}", "model_type": "dqn", "dataset": "real"},
            )

        name = exp_cfg.get("name", f"Experiment {experiment_id}")
        model_type = exp_cfg.get("model_type", "dqn")
        dataset = exp_cfg.get("dataset", "real")

        logger.info(
            "running_experiment",
            experiment_id=experiment_id,
            name=name,
            model_type=model_type,
            dev_mode=dev_mode,
        )

        # 1. Prepare evaluation environment with held-out test scenarios
        scenarios = self.get_held_out_scenarios()
        if scenarios:
            env = SupplyChainEnv(scenarios=scenarios)
        else:
            env = gym.make("asccd/SupplyChain-v0")

        # 2. Instantiate or load the appropriate policy
        if experiment_id == "A" or model_type == "rule_based":
            policy = RuleBasedDefensePolicy()

        elif experiment_id == "B" or model_type == "dqn":
            model_path = Path("artifacts/models/dqn/dqn_real_only_final.zip")
            if not model_path.exists():
                model_path = Path("artifacts/models/dqn/dqn_default_final.zip")

            if model_path.exists():
                logger.info("loading_dqn_weights", path=str(model_path))
                policy = DQNDefenseAgent.load(model_path, env=env)
            else:
                logger.info("training_fresh_dqn_real_only")
                agent = DQNDefenseAgent(env=env, n_eval_episodes=2)
                agent.train(
                    env=env,
                    total_timesteps=1000 if dev_mode else 10_000,
                    dev_mode=dev_mode,
                    condition="real_only",
                    save_checkpoints=False,
                )
                policy = agent

        elif experiment_id == "C" or model_type == "dqn_gan":
            model_path = Path("artifacts/models/dqn/dqn_augmented_final.zip")
            if not model_path.exists():
                model_path = Path("artifacts/models/dqn/dqn_default_final.zip")

            if model_path.exists():
                logger.info("loading_dqn_augmented_weights", path=str(model_path))
                policy = DQNDefenseAgent.load(model_path, env=env)
            else:
                logger.info("training_fresh_dqn_augmented")
                agent = DQNDefenseAgent(env=env, n_eval_episodes=2)
                agent.train(
                    env=env,
                    total_timesteps=1000 if dev_mode else 10_000,
                    dev_mode=dev_mode,
                    condition="augmented",
                    save_checkpoints=False,
                )
                policy = agent

        elif experiment_id == "D" or model_type == "ppo":
            model_path = Path("artifacts/models/ppo/ppo_default_final.zip")
            if model_path.exists():
                logger.info("loading_ppo_weights", path=str(model_path))
                policy = PPODefenseAgent.load(model_path, env=env)
            else:
                logger.info("training_fresh_ppo_agent")
                agent = PPODefenseAgent(
                    env=env,
                    n_steps=32 if dev_mode else 128,
                    batch_size=16,
                    n_epochs=2,
                    n_eval_episodes=2,
                )
                agent.train(
                    env=env,
                    total_timesteps=500 if dev_mode else 2000,
                    dev_mode=dev_mode,
                    condition="default",
                    save_checkpoints=False,
                )
                policy = agent

        else:
            policy = RuleBasedDefensePolicy()

        # 3. Execute evaluation
        episodes = n_episodes or (10 if dev_mode else self.n_eval_episodes)
        result = self.evaluate_policy(
            policy=policy,
            env=env,
            experiment_id=experiment_id,
            name=name,
            model_type=model_type,
            dataset=dataset,
            n_episodes=episodes,
            seeds=seeds or self.seeds,
        )
        env.close()

        # 4. Record to database if session is provided
        if session is not None:
            self._save_to_database(result, session)

        return result

    def _save_to_database(self, result: ExperimentResult, session: Any) -> None:
        """Persist experiment run and individual metrics into the database."""
        try:
            from src.common.models import Experiment, ExperimentMetric

            exp_record = (
                session.query(Experiment)
                .filter_by(experiment_id=f"exp_{result.experiment_id.lower()}")
                .first()
            )
            if not exp_record:
                exp_record = Experiment(
                    experiment_id=f"exp_{result.experiment_id.lower()}",
                    model_type=result.model_type,
                    dataset_version="v1",
                    seed=result.seeds[0] if result.seeds else 42,
                    status="completed",
                    started_at=datetime.now(UTC),
                    completed_at=datetime.now(UTC),
                )
                session.add(exp_record)
                session.flush()

            exp_record.set_config(result.to_dict())
            exp_record.status = "completed"
            exp_record.completed_at = datetime.now(UTC)

            # Record high-level metrics
            metrics_map = {
                "mitigation_success_rate": result.mitigation_success_rate,
                "containment_rate": result.containment_rate,
                "service_availability": result.service_availability,
                "mean_reward": result.mean_reward,
                "attack_impact_score": result.attack_impact_score,
            }
            for m_name, m_val in metrics_map.items():
                m_rec = ExperimentMetric(
                    experiment_id=exp_record.id,
                    metric_name=m_name,
                    metric_value=float(m_val),
                )
                session.add(m_rec)

            session.commit()
            logger.info("saved_experiment_to_db", experiment_id=result.experiment_id)
        except Exception as e:
            logger.warning("failed_saving_experiment_to_db", error=str(e))
            session.rollback()

    def run_all_experiments(
        self,
        experiment_ids: list[str] | None = None,
        n_episodes: int | None = None,
        seeds: list[int] | None = None,
        dev_mode: bool = False,
        session: Any = None,
    ) -> ComparisonSummary:
        """Execute complete suite of experiments and calculate comparative gains."""
        target_ids = experiment_ids or ["A", "B", "C"]
        results: dict[str, ExperimentResult] = {}

        for exp_id in target_ids:
            results[exp_id] = self.run_experiment(
                experiment_id=exp_id,
                n_episodes=n_episodes,
                seeds=seeds,
                dev_mode=dev_mode,
                session=session,
            )

        # Compute relative improvements
        relative_gains: dict[str, dict[str, float]] = {}

        if "C" in results and "A" in results:
            res_c = results["C"]
            res_a = results["A"]
            relative_gains["C_vs_A"] = {
                "mitigation_delta_pct": round(
                    (res_c.mitigation_success_rate - res_a.mitigation_success_rate) * 100.0, 2
                ),
                "reward_delta": round(res_c.mean_reward - res_a.mean_reward, 2),
                "availability_delta_pct": round(
                    (res_c.service_availability - res_a.service_availability) * 100.0, 2
                ),
                "impact_reduction": round(res_a.attack_impact_score - res_c.attack_impact_score, 4),
            }

        if "C" in results and "B" in results:
            res_c = results["C"]
            res_b = results["B"]
            relative_gains["C_vs_B"] = {
                "mitigation_delta_pct": round(
                    (res_c.mitigation_success_rate - res_b.mitigation_success_rate) * 100.0, 2
                ),
                "reward_delta": round(res_c.mean_reward - res_b.mean_reward, 2),
                "availability_delta_pct": round(
                    (res_c.service_availability - res_b.service_availability) * 100.0, 2
                ),
                "impact_reduction": round(res_b.attack_impact_score - res_c.attack_impact_score, 4),
            }

        if "B" in results and "A" in results:
            res_b = results["B"]
            res_a = results["A"]
            relative_gains["B_vs_A"] = {
                "mitigation_delta_pct": round(
                    (res_b.mitigation_success_rate - res_a.mitigation_success_rate) * 100.0, 2
                ),
                "reward_delta": round(res_b.mean_reward - res_a.mean_reward, 2),
            }

        summary = ComparisonSummary(
            experiments=results,
            relative_gains=relative_gains,
            timestamp=datetime.now(UTC).isoformat(),
        )

        return summary

    def export_reports(
        self,
        summary: ComparisonSummary,
        output_dir: str | Path | None = None,
    ) -> tuple[Path, Path, Path | None]:
        """Export JSON summary, CSV comparison table, and publication figure."""
        out_path = Path(output_dir or self.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)

        # 1. Export JSON report
        json_file = out_path / "experiments_summary.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(summary.to_dict(), f, indent=2)

        # 2. Export CSV comparison table
        csv_file = out_path / "experiments_comparison.csv"
        rows: list[dict[str, Any]] = []
        for exp_id, res in summary.experiments.items():
            rows.append({
                "Experiment": exp_id,
                "Name": res.name,
                "Model Type": res.model_type,
                "Dataset": res.dataset,
                "Episodes": res.n_episodes,
                "Mitigation Rate (%)": round(res.mitigation_success_rate * 100.0, 2),
                "Containment Rate (%)": round(res.containment_rate * 100.0, 2),
                "Service Availability (%)": round(res.service_availability * 100.0, 2),
                "Mean Reward": round(res.mean_reward, 2),
                "Reward Std": round(res.std_reward, 2),
                "Attack Impact Score": round(res.attack_impact_score, 4),
                "Downtime Steps": res.total_downtime_steps,
                "Avg Response Steps": round(res.avg_response_steps, 2),
            })
        df_csv = pd.DataFrame(rows)
        df_csv.to_csv(csv_file, index=False)

        # 3. Generate visualization bar chart
        figure_file: Path | None = None
        if self.generate_plots and summary.experiments:
            try:
                import matplotlib.pyplot as plt

                exp_names = [f"Exp {k}: {v.name}" for k, v in summary.experiments.items()]
                mitigations = [v.mitigation_success_rate * 100.0 for v in summary.experiments.values()]
                availabilities = [v.service_availability * 100.0 for v in summary.experiments.values()]
                rewards = [v.mean_reward for v in summary.experiments.values()]

                fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

                # Chart 1: Mitigation Success Rate
                bars1 = axes[0].bar(exp_names, mitigations, color=["#4B5563", "#3B82F6", "#10B981", "#8B5CF6"][:len(exp_names)])
                axes[0].set_title("Mitigation Success Rate (%)", fontsize=11, fontweight="bold")
                axes[0].set_ylim(0, 105)
                axes[0].set_ylabel("Rate (%)")
                for bar in bars1:
                    yval = bar.get_height()
                    axes[0].text(bar.get_x() + bar.get_width() / 2, yval + 1.5, f"{yval:.1f}%", ha="center", va="bottom", fontsize=9)

                # Chart 2: Service Availability
                bars2 = axes[1].bar(exp_names, availabilities, color=["#6B7280", "#60A5FA", "#34D399", "#A78BFA"][:len(exp_names)])
                axes[1].set_title("Mean Service Availability (%)", fontsize=11, fontweight="bold")
                axes[1].set_ylim(80, 102)
                axes[1].set_ylabel("Uptime (%)")
                for bar in bars2:
                    yval = bar.get_height()
                    axes[1].text(bar.get_x() + bar.get_width() / 2, yval + 0.3, f"{yval:.1f}%", ha="center", va="bottom", fontsize=9)

                # Chart 3: Mean Cumulative Reward
                bars3 = axes[2].bar(exp_names, rewards, color=["#9CA3AF", "#93C5FD", "#6EE7B7", "#C4B5FD"][:len(exp_names)])
                axes[2].set_title("Mean Cumulative Reward", fontsize=11, fontweight="bold")
                axes[2].set_ylabel("Score")
                for bar in bars3:
                    yval = bar.get_height()
                    axes[2].text(bar.get_x() + bar.get_width() / 2, yval + 1.0, f"{yval:.1f}", ha="center", va="bottom", fontsize=9)

                for ax in axes:
                    ax.set_xticks(range(len(exp_names)))
                    ax.set_xticklabels(exp_names, rotation=15, ha="right", fontsize=9)
                    ax.grid(axis="y", linestyle="--", alpha=0.5)

                plt.tight_layout()
                figure_file = self.figures_dir / "experiment_comparison.png"
                plt.savefig(figure_file, dpi=150)
                plt.close()
                logger.info("exported_comparison_plot", path=str(figure_file))
            except Exception as e:
                logger.warning("failed_generating_comparison_plot", error=str(e))

        return json_file, csv_file, figure_file
