"""
ASCCD Baselines Module.

Provides benchmark defense policies for comparative evaluation against
reinforcement learning agents.
"""

from src.baselines.models import BaselineEvaluationResult
from src.baselines.rule_based import RuleBasedDefensePolicy

__all__ = [
    "BaselineEvaluationResult",
    "RuleBasedDefensePolicy",
]
