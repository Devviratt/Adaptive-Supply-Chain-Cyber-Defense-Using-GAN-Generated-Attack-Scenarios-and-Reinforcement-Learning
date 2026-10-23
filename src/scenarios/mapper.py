"""
ASCCD Attack Scenario Mapper.

Transforms tabular network intrusion feature records (real CIC-IDS2017
or CTGAN-generated synthetic data) into structured supply-chain cyber-defense
attack scenarios with risk and impact semantics.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import structlog
import yaml

from src.scenarios.models import AttackScenario

logger = structlog.get_logger(__name__)


# Default mapping rules if configuration file is not found
DEFAULT_CATEGORY_RULES: dict[str, dict[str, Any]] = {
    "web_attack": {
        "affected_stage": "supplier",
        "severity": "high",
        "propagation_risk": 0.75,
        "availability_impact": 0.20,
        "integrity_impact": 0.85,
        "confidentiality_impact": 0.70,
        "base_duration_steps": 15,
        "description": "Web vulnerabilities targeting source repositories or dependency registry portals.",
    },
    "brute_force": {
        "affected_stage": "build",
        "severity": "medium",
        "propagation_risk": 0.60,
        "availability_impact": 0.25,
        "integrity_impact": 0.75,
        "confidentiality_impact": 0.80,
        "base_duration_steps": 10,
        "description": "Credential stuffing or brute force targeting build agents or distribution servers.",
    },
    "botnet": {
        "affected_stage": "build",
        "severity": "high",
        "propagation_risk": 0.80,
        "availability_impact": 0.40,
        "integrity_impact": 0.70,
        "confidentiality_impact": 0.65,
        "base_duration_steps": 20,
        "description": "Compromised CI/CD build nodes hijacked for lateral movement or illicit tasks.",
    },
    "dos": {
        "affected_stage": "deployment",
        "severity": "high",
        "propagation_risk": 0.20,
        "availability_impact": 0.90,
        "integrity_impact": 0.10,
        "confidentiality_impact": 0.05,
        "base_duration_steps": 25,
        "description": "Volumetric denial of service targeting production services or registry endpoints.",
    },
    "ddos": {
        "affected_stage": "deployment",
        "severity": "critical",
        "propagation_risk": 0.25,
        "availability_impact": 0.95,
        "integrity_impact": 0.10,
        "confidentiality_impact": 0.05,
        "base_duration_steps": 30,
        "description": "Distributed denial of service causing broad production system unavailability.",
    },
    "portscan": {
        "affected_stage": "deployment",
        "severity": "low",
        "propagation_risk": 0.15,
        "availability_impact": 0.10,
        "integrity_impact": 0.05,
        "confidentiality_impact": 0.30,
        "base_duration_steps": 5,
        "description": "Reconnaissance scan probing service topology and port vulnerabilities.",
    },
    "infiltration": {
        "affected_stage": "supplier",
        "severity": "critical",
        "propagation_risk": 0.85,
        "availability_impact": 0.30,
        "integrity_impact": 0.90,
        "confidentiality_impact": 0.90,
        "base_duration_steps": 35,
        "description": "Targeted stealth intrusion directly compromising developer workstation or upstream codebase.",
    },
    "benign": {
        "affected_stage": "deployment",
        "severity": "low",
        "propagation_risk": 0.00,
        "availability_impact": 0.00,
        "integrity_impact": 0.00,
        "confidentiality_impact": 0.00,
        "base_duration_steps": 1,
        "description": "Normal, authorized operational traffic with zero malicious consequence.",
    },
    "default": {
        "affected_stage": "deployment",
        "severity": "medium",
        "propagation_risk": 0.30,
        "availability_impact": 0.30,
        "integrity_impact": 0.30,
        "confidentiality_impact": 0.30,
        "base_duration_steps": 10,
        "description": "Fallback scenario profile for unrecognized network flow labels.",
    },
}


class ScenarioMapper:
    """Translates network flow telemetry records into supply-chain attack scenarios."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        config_path: str | Path | None = None,
    ) -> None:
        """Initialize the ScenarioMapper with optional configuration."""
        self.config = self._load_config(config, config_path)
        mapping_cfg = self.config.get("scenario_mapping", {})
        self.categories: dict[str, dict[str, Any]] = mapping_cfg.get(
            "categories", DEFAULT_CATEGORY_RULES
        )
        self.modulation_cfg: dict[str, Any] = mapping_cfg.get(
            "modulation",
            {
                "enabled": True,
                "duration_feature": "Flow Duration",
                "bytes_rate_feature": "Flow Bytes/s",
                "packets_rate_feature": "Flow Packets/s",
                "syn_flag_feature": "SYN Flag Count",
                "min_duration_steps": 1,
                "max_duration_steps": 50,
                "severity_upgrade_threshold": 0.85,
            },
        )

    def _load_config(
        self,
        config: dict[str, Any] | None,
        config_path: str | Path | None,
    ) -> dict[str, Any]:
        """Load mapping configuration from dictionary or YAML file."""
        if config is not None:
            return config

        default_path = Path("config/scenario.yaml")
        path = Path(config_path) if config_path else default_path
        if path.exists():
            try:
                with open(path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("Failed to parse scenario config file", path=str(path), error=str(e))
        return {}

    def _extract_label(self, record: dict[str, Any] | pd.Series) -> str:
        """Extract and normalize attack label from a data record."""
        # Check standard column names
        for col in ["Label", "label", "Attack", "attack", "attack_category", "Class", "class"]:
            if col in record and pd.notna(record[col]):
                raw_label = str(record[col]).strip().lower()
                # 1. Prioritize exact match
                if raw_label in self.categories and raw_label != "default":
                    return raw_label
                # 2. Substring match with longest categories first (e.g., 'ddos' before 'dos')
                sorted_cats = sorted(
                    [c for c in self.categories.keys() if c != "default"],
                    key=len,
                    reverse=True,
                )
                for cat in sorted_cats:
                    if cat in raw_label or raw_label in cat:
                        return cat
                return raw_label
        return "benign"

    def _compute_modulation(
        self,
        record: dict[str, Any] | pd.Series,
        base_rule: dict[str, Any],
    ) -> tuple[float, float, int, str]:
        """Compute feature-driven modulation for impact, propagation, duration, and severity."""
        if not self.modulation_cfg.get("enabled", True):
            return (
                base_rule["availability_impact"],
                base_rule["propagation_risk"],
                base_rule["base_duration_steps"],
                base_rule["severity"],
            )

        duration_feat = self.modulation_cfg.get("duration_feature", "Flow Duration")
        bytes_feat = self.modulation_cfg.get("bytes_rate_feature", "Flow Bytes/s")
        packets_feat = self.modulation_cfg.get("packets_rate_feature", "Flow Packets/s")
        syn_feat = self.modulation_cfg.get("syn_flag_feature", "SYN Flag Count")

        def _get_val(feat_name: str) -> float:
            if feat_name in record:
                val = record[feat_name]
                try:
                    num_val = float(val)
                    if np.isfinite(num_val) and num_val > 0:
                        return num_val
                except (ValueError, TypeError):
                    pass
            return 0.0

        dur_val = _get_val(duration_feat)
        bytes_val = _get_val(bytes_feat)
        pkts_val = _get_val(packets_feat)
        syn_val = _get_val(syn_feat)

        # Logarithmic scaling factors [0, 1]
        # Microseconds flow duration (e.g., 100 to 1e8)
        dur_factor = float(np.clip(np.log10(dur_val + 1.0) / 8.0, 0.0, 1.0)) if dur_val > 0 else 0.2
        # Volumetric factor
        vol_factor = float(np.clip(np.log10(bytes_val + pkts_val + 1.0) / 8.0, 0.0, 1.0)) if (bytes_val + pkts_val) > 0 else 0.1
        # SYN flag anomaly factor
        syn_factor = float(np.clip(syn_val / 50.0, 0.0, 1.0)) if syn_val > 0 else 0.0

        # Modulate availability impact
        base_avail = float(base_rule.get("availability_impact", 0.0))
        if base_avail > 0.05:  # Only modulate non-zero attack availability
            mod_avail = float(np.clip(base_avail * (0.8 + 0.4 * vol_factor), 0.0, 1.0))
        else:
            mod_avail = base_avail

        # Modulate propagation risk
        base_prop = float(base_rule.get("propagation_risk", 0.0))
        if base_prop > 0.05:
            mod_prop = float(np.clip(base_prop * (0.85 + 0.3 * syn_factor), 0.0, 1.0))
        else:
            mod_prop = base_prop

        # Modulate duration steps
        base_dur_steps = int(base_rule.get("base_duration_steps", 1))
        min_steps = int(self.modulation_cfg.get("min_duration_steps", 1))
        max_steps = int(self.modulation_cfg.get("max_duration_steps", 50))
        if base_dur_steps > 1:
            scaled_dur = int(np.clip(round(base_dur_steps * (0.7 + 0.6 * dur_factor)), min_steps, max_steps))
        else:
            scaled_dur = min_steps

        # Dynamic severity upgrade
        base_sev = base_rule.get("severity", "medium")
        upgrade_thresh = float(self.modulation_cfg.get("severity_upgrade_threshold", 0.85))
        severity = base_sev
        if vol_factor >= upgrade_thresh or dur_factor >= upgrade_thresh:
            if base_sev == "low":
                severity = "medium"
            elif base_sev == "medium":
                severity = "high"
            elif base_sev == "high":
                severity = "critical"

        return mod_avail, mod_prop, scaled_dur, severity

    def map_record(
        self,
        record: dict[str, Any] | pd.Series,
        source: str = "real",
        scenario_id: str | None = None,
    ) -> AttackScenario:
        """Map a single network flow record into a structured AttackScenario.

        Args:
            record: Dictionary or Series containing feature values and optional label.
            source: Data origin ("real" or "synthetic").
            scenario_id: Optional explicit scenario ID; generated if None.

        Returns:
            Structured AttackScenario object.
        """
        label = self._extract_label(record)
        rule = self.categories.get(label, self.categories.get("default", DEFAULT_CATEGORY_RULES["default"]))

        mod_avail, mod_prop, duration_steps, severity = self._compute_modulation(record, rule)

        # Build feature vector of continuous flow features
        feature_vector: dict[str, float] = {}
        for k, v in record.items():
            if str(k).lower() not in ["label", "attack", "class", "scenario_id", "source"]:
                try:
                    float_val = float(v)
                    if np.isfinite(float_val):
                        feature_vector[str(k)] = round(float_val, 4)
                except (ValueError, TypeError):
                    continue

        if not scenario_id:
            # Deterministic hash if feature vector exists, else uuid
            if feature_vector:
                feat_hash = hashlib.md5(json.dumps(sorted(feature_vector.items())).encode()).hexdigest()[:8]
                scenario_id = f"scen_{label}_{feat_hash}"
            else:
                scenario_id = f"scen_{label}_{uuid.uuid4().hex[:8]}"

        return AttackScenario(
            scenario_id=scenario_id,
            attack_category=label,
            severity=severity,
            affected_stage=rule.get("affected_stage", "deployment"),
            propagation_risk=mod_prop,
            availability_impact=mod_avail,
            integrity_impact=float(rule.get("integrity_impact", 0.0)),
            confidentiality_impact=float(rule.get("confidentiality_impact", 0.0)),
            duration_steps=duration_steps,
            source=source,
            feature_vector=feature_vector,
            description=rule.get("description", ""),
        )

    def map_dataframe(
        self,
        df: pd.DataFrame,
        source: str = "real",
        max_records: int | None = None,
    ) -> list[AttackScenario]:
        """Map a batch DataFrame of records into a list of AttackScenario objects.

        Args:
            df: DataFrame containing flow records.
            source: "real" or "synthetic".
            max_records: Optional limit on number of records to map.

        Returns:
            List of AttackScenario instances.
        """
        scenarios: list[AttackScenario] = []
        limit = max_records if max_records is not None else len(df)
        records = df.head(limit).to_dict(orient="records")

        for idx, rec in enumerate(records):
            scen_id = f"scen_{source}_{idx:06d}"
            scenarios.append(self.map_record(rec, source=source, scenario_id=scen_id))

        return scenarios

    def map_batch(
        self,
        batch: pd.DataFrame | list[dict[str, Any]],
        source: str = "real",
        max_records: int | None = None,
    ) -> list[AttackScenario]:
        """Map a batch of records (DataFrame or list of dicts) into AttackScenarios."""
        if isinstance(batch, pd.DataFrame):
            return self.map_dataframe(batch, source=source, max_records=max_records)
        df = pd.DataFrame(batch)
        return self.map_dataframe(df, source=source, max_records=max_records)

    def to_dataframe(self, scenarios: list[AttackScenario]) -> pd.DataFrame:
        """Convert a list of AttackScenario instances to a tabular pandas DataFrame."""
        rows = [s.to_dict() for s in scenarios]
        df = pd.DataFrame(rows)
        return df

    def save_to_db(self, scenarios: list[AttackScenario], session: Any) -> int:
        """Save a collection of AttackScenario instances to the database.

        Args:
            scenarios: List of AttackScenario objects.
            session: SQLAlchemy session.

        Returns:
            Count of successfully inserted scenarios.
        """
        from src.common.models import Scenario

        inserted_count = 0
        for scen in scenarios:
            # Check if exists
            exists = session.query(Scenario).filter_by(scenario_id=scen.scenario_id).first()
            if not exists:
                session.add(scen.to_orm())
                inserted_count += 1
        session.commit()
        return inserted_count

    def stream_scenarios(
        self,
        df: pd.DataFrame,
        source: str = "real",
        loop: bool = True,
        shuffle: bool = True,
        seed: int = 42,
    ) -> Generator[AttackScenario, None, None]:
        """Stream AttackScenario objects sequentially or infinitely for RL simulation episodes.

        Args:
            df: DataFrame of source attack records.
            source: "real" or "synthetic".
            loop: Whether to loop indefinitely across the dataset.
            shuffle: Whether to shuffle records per epoch.
            seed: Random seed for shuffling.

        Yields:
            AttackScenario instances.
        """
        rng = np.random.default_rng(seed)
        n = len(df)
        if n == 0:
            return

        while True:
            indices = rng.permutation(n) if shuffle else np.arange(n)
            for idx in indices:
                rec = df.iloc[idx].to_dict()
                scen_id = f"scen_{source}_{idx:06d}_{uuid.uuid4().hex[:6]}"
                yield self.map_record(rec, source=source, scenario_id=scen_id)

            if not loop:
                break
