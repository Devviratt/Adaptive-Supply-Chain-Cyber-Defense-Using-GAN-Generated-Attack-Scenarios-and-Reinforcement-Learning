"""Tests for balanced DQN training scenario preparation."""

from __future__ import annotations

from collections import Counter

import pandas as pd
from scripts.train_dqn import (
    build_training_scenarios,
    load_evaluation_scenarios,
    load_scenarios_for_condition,
    sample_balanced_rows,
)
from src.environment.supply_chain_env import STAGE_NAMES
from src.scenarios.mapper import ScenarioMapper


def test_sample_balanced_rows_caps_each_label_and_can_include_benign() -> None:
    real = pd.DataFrame(
        {"Label": ["benign"] * 5 + ["dos"] * 3 + ["ddos"] * 2, "Flow Duration": range(10)}
    )
    synthetic = pd.DataFrame(
        {"Label": ["benign"] * 3 + ["dos"] + ["ddos"] * 4, "Flow Duration": range(8)}
    )

    sampled = sample_balanced_rows(
        [(real, "real"), (synthetic, "synthetic")],
        seed=7,
        include_benign=True,
        samples_per_category=2,
    )

    assert sampled["_training_label"].value_counts().to_dict() == {
        "benign": 2,
        "ddos": 2,
        "dos": 2,
    }


def test_build_training_scenarios_covers_each_stage_for_each_label() -> None:
    rows = pd.DataFrame(
        [
            {
                "Label": "ddos",
                "Flow Duration": 1000,
                "_training_source": "real",
                "_training_label": "ddos",
            },
            {
                "Label": "benign",
                "Flow Duration": 500,
                "_training_source": "synthetic",
                "_training_label": "benign",
            },
        ]
    )

    scenarios = build_training_scenarios(rows, ScenarioMapper(), "augmented")

    assert len(scenarios) == len(rows) * len(STAGE_NAMES)
    assert Counter(scenario.attack_category for scenario in scenarios) == {
        "ddos": len(STAGE_NAMES),
        "benign": len(STAGE_NAMES),
    }
    assert {scenario.affected_stage for scenario in scenarios} == set(STAGE_NAMES)
    assert {scenario.source for scenario in scenarios} == {"real", "synthetic"}


def test_load_scenarios_uses_requested_data_root(tmp_path) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame({"Label": ["dos"], "Flow Duration": [1000]}).to_csv(
        processed / "train.csv",
        index=False,
    )

    scenarios = load_scenarios_for_condition(
        "real_only",
        seed=3,
        data_root=tmp_path,
    )

    assert scenarios is not None
    assert len(scenarios) == len(STAGE_NAMES)
    assert {scenario.attack_category for scenario in scenarios} == {"dos"}


def test_load_evaluation_scenarios_uses_held_out_test_split(tmp_path) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame({"Label": ["benign"] * 3 + ["ddos"] * 2, "Flow Duration": range(5)}).to_csv(
        processed / "test.csv", index=False
    )

    scenarios = load_evaluation_scenarios(tmp_path, seed=3)

    assert len(scenarios) == 5 * len(STAGE_NAMES)
    assert {scenario.attack_category for scenario in scenarios} == {"benign", "ddos"}
    assert {scenario.source for scenario in scenarios} == {"real"}
    assert {scenario.affected_stage for scenario in scenarios} == set(STAGE_NAMES)
