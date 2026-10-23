"""
ASCCD Defense Policies and Models API Router.

Endpoints for requesting defense policy predictions (Rule-Based, DQN, PPO)
and inspecting trained model artifacts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from fastapi import APIRouter, HTTPException

from src.api.schemas.defense import ModelInfoSchema, PredictRequest, PredictResponse
from src.baselines.rule_based import RuleBasedDefensePolicy
from src.environment.models import DefenseAction
from src.rl.dqn_agent import DQNDefenseAgent
from src.rl.ppo_agent import PPODefenseAgent

router = APIRouter()

# Global cached policies
_rule_policy: RuleBasedDefensePolicy | None = None
_dqn_agent: DQNDefenseAgent | None = None
_ppo_agent: PPODefenseAgent | None = None


def get_rule_policy() -> RuleBasedDefensePolicy:
    global _rule_policy
    if _rule_policy is None:
        _rule_policy = RuleBasedDefensePolicy()
    return _rule_policy


def get_dqn_agent() -> DQNDefenseAgent:
    global _dqn_agent
    if _dqn_agent is None:
        model_path = Path("artifacts/models/dqn/dqn_augmented_final.zip")
        if not model_path.exists():
            model_path = Path("artifacts/models/dqn/dqn_default_final.zip")
        if model_path.exists():
            _dqn_agent = DQNDefenseAgent.load(model_path)
        else:
            _dqn_agent = DQNDefenseAgent()
    return _dqn_agent


def get_ppo_agent() -> PPODefenseAgent:
    global _ppo_agent
    if _ppo_agent is None:
        model_path = Path("artifacts/models/ppo/ppo_default_final.zip")
        if model_path.exists():
            _ppo_agent = PPODefenseAgent.load(model_path)
        else:
            _ppo_agent = PPODefenseAgent()
    return _ppo_agent


@router.post("/predict", response_model=PredictResponse)
def predict_action(payload: PredictRequest) -> PredictResponse:
    """Predict the optimal defensive action given a 12-dimensional state vector."""
    obs = np.array(payload.observation, dtype=np.float32)
    model_type = payload.model_type.lower()

    if model_type in ["rule", "rule_based", "baseline"]:
        policy = get_rule_policy()
        action, _ = policy.predict(obs)
    elif model_type in ["dqn", "dqn_gan"]:
        agent = get_dqn_agent()
        action, _ = agent.predict(obs, deterministic=payload.deterministic)
    elif model_type in ["ppo"]:
        agent = get_ppo_agent()
        action, _ = agent.predict(obs, deterministic=payload.deterministic)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model_type '{payload.model_type}'. Choose 'rule_based', 'dqn', or 'ppo'.",
        )

    action_name = DefenseAction.get_name(action)
    return PredictResponse(
        action=action,
        action_name=action_name,
        model_type=model_type,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/models", response_model=list[ModelInfoSchema])
def list_models() -> list[ModelInfoSchema]:
    """List trained defense models and checkpoints stored in artifacts."""
    models: list[ModelInfoSchema] = []
    base_dir = Path("artifacts/models")

    if base_dir.exists():
        for zip_file in base_dir.glob("**/*.zip"):
            st = zip_file.stat()
            algo = "DQN" if "dqn" in zip_file.name.lower() else ("PPO" if "ppo" in zip_file.name.lower() else "CTGAN")
            models.append(
                ModelInfoSchema(
                    name=zip_file.name,
                    algorithm=algo,
                    path=str(zip_file),
                    size_bytes=st.st_size,
                    modified_at=datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat(),
                )
            )

    return sorted(models, key=lambda m: m.name)
