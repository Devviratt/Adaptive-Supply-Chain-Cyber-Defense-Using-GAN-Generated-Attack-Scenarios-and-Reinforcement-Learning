"""Tests for CIC-IDS2017 stratified sample allocation."""

from __future__ import annotations

import pytest
from scripts.sample_cicids2017 import allocate_sample_quotas


def test_allocate_sample_quotas_preserves_rare_classes_and_exact_size() -> None:
    quotas = allocate_sample_quotas(
        {"benign": 1000, "dos": 100, "heartbleed": 5},
        sample_size=500,
        minimum_per_class=20,
    )

    assert sum(quotas.values()) == 500
    assert quotas["heartbleed"] == 5
    assert quotas["dos"] >= 20
    assert all(
        quotas[label] <= count
        for label, count in {
            "benign": 1000,
            "dos": 100,
            "heartbleed": 5,
        }.items()
    )


def test_allocate_sample_quotas_rejects_oversampling() -> None:
    with pytest.raises(ValueError, match="only 3 cleaned rows"):
        allocate_sample_quotas({"dos": 3}, sample_size=4, minimum_per_class=1)
