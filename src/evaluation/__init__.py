"""
ASCCD Evaluation and Experimentation Module.

Exports the core EvaluationEngine and benchmark result dataclasses.
"""

from src.evaluation.engine import EvaluationEngine
from src.evaluation.models import ComparisonSummary, ExperimentResult

__all__ = [
    "ComparisonSummary",
    "EvaluationEngine",
    "ExperimentResult",
]
