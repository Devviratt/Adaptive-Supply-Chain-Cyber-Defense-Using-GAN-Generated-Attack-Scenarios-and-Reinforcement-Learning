"""Tests for exact class counts in CTGAN-generated samples."""

import pandas as pd
import pytest

import ctgan
from src.gan.ctgan import generate_ctgan


class FakeModel:
    def __init__(self, labels: list[str]):
        self.labels = labels

    def sample(self, count: int, **_kwargs) -> pd.DataFrame:
        repeated_labels = (self.labels * (count // len(self.labels) + 1))[:count]
        return pd.DataFrame({"Label": repeated_labels, "Flow Duration": range(count)})


def test_generate_ctgan_returns_exact_requested_class_count(monkeypatch, tmp_path):
    class FakeCTGAN:
        @staticmethod
        def load(_model_path):
            return FakeModel(["benign", "ddos", "portscan"])

    monkeypatch.setattr(ctgan, "CTGAN", FakeCTGAN)
    output_path = tmp_path / "synthetic.csv"

    generated = generate_ctgan(
        model_path=tmp_path / "model.pkl",
        output_path=output_path,
        count=3,
        per_class={"ddos": 3},
    )

    assert len(generated) == 3
    assert generated["Label"].tolist() == ["ddos"] * 3
    assert output_path.is_file()
    assert (pd.read_csv(output_path)["Label"] == "ddos").all()


def test_generate_ctgan_fails_instead_of_returning_wrong_attack_class(monkeypatch, tmp_path):
    class FakeCTGAN:
        @staticmethod
        def load(_model_path):
            return FakeModel(["benign", "portscan"])

    monkeypatch.setattr(ctgan, "CTGAN", FakeCTGAN)
    output_path = tmp_path / "synthetic.csv"

    with pytest.raises(ValueError, match="Retrain the model"):
        generate_ctgan(
            model_path=tmp_path / "model.pkl",
            output_path=output_path,
            count=2,
            per_class={"ddos": 2},
        )

    assert not output_path.exists()
