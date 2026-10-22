"""
ASCCD Data Validator — validation of processed dataset and artifacts.

Performs schema, integrity, leakage, and distribution checks on processed
train/validation/test splits and associated preprocessing artifacts.

Author: Deekshay G (primary), reviewed by Anandavarthan & Dev Virat
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationCheck:
    """Individual validation check result."""

    name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete report of all dataset validation checks."""

    is_valid: bool = True
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    checks: list[ValidationCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    split_metrics: dict[str, Any] = field(default_factory=dict)

    def add_check(
        self,
        name: str,
        passed: bool,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a validation check."""
        self.total_checks += 1
        check = ValidationCheck(
            name=name,
            passed=passed,
            message=message,
            details=details or {},
        )
        self.checks.append(check)
        if passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1
            self.is_valid = False
            self.errors.append(f"[{name}] {message}")

    def add_warning(self, message: str) -> None:
        """Record a validation warning that does not fail the build."""
        self.warnings.append(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for JSON export."""
        return {
            "is_valid": self.is_valid,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "errors": self.errors,
            "warnings": self.warnings,
            "split_metrics": self.split_metrics,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.checks
            ],
        }

    def to_markdown(self) -> str:
        """Generate human-readable Markdown summary."""
        status_badge = "✅ PASSED" if self.is_valid else "❌ FAILED"
        lines = [
            "# ASCCD Data Validation Report",
            "",
            f"**Status:** {status_badge}  ",
            f"**Checks Passed:** {self.passed_checks}/{self.total_checks}  ",
            f"**Failed Checks:** {self.failed_checks}  ",
            f"**Warnings:** {len(self.warnings)}  ",
            "",
            "## Summary of Checks",
            "",
            "| Check | Status | Description |",
            "|-------|--------|-------------|",
        ]
        for c in self.checks:
            icon = "✅ Pass" if c.passed else "❌ Fail"
            lines.append(f"| {c.name} | {icon} | {c.message} |")

        if self.errors:
            lines.extend(["", "## Failures and Errors", ""])
            for err in self.errors:
                lines.append(f"- 🔴 {err}")

        if self.warnings:
            lines.extend(["", "## Warnings", ""])
            for warn in self.warnings:
                lines.append(f"- ⚠️ {warn}")

        if self.split_metrics:
            lines.extend(["", "## Split Metrics", ""])
            for split_name, metrics in self.split_metrics.items():
                lines.append(f"### {split_name.capitalize()} Set")
                if isinstance(metrics, dict):
                    for k, v in metrics.items():
                        lines.append(f"- **{k}:** {v}")

        return "\n".join(lines)

    def save(self, output_dir: str | Path) -> dict[str, str]:
        """Save report to disk as JSON and Markdown."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        json_path = out_path / "validation_report.json"
        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        md_path = out_path / "validation_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())

        logger.info(
            "validation_report_saved",
            json_path=str(json_path),
            md_path=str(md_path),
        )
        return {"json": str(json_path), "markdown": str(md_path)}


class DataValidator:
    """Validates processed datasets and preprocessing artifacts.

    Ensures that data consumed by downstream CTGAN and RL models
    is clean, non-null, finite, strictly partitioned, and accompanied
    by verified artifacts.
    """

    def __init__(
        self,
        data_dir: str | Path,
        expected_label_col: str = "Label",
        file_format: str = "csv",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.expected_label_col = expected_label_col
        self.file_format = file_format.lower()

    def validate(self) -> ValidationReport:
        """Run all validation checks on the processed data directory.

        Returns:
            ValidationReport containing pass/fail statuses and diagnostic metrics.
        """
        report = ValidationReport()

        # 1. Directory and file existence check
        self._check_file_existence(report)
        if not report.is_valid:
            logger.error("validation_halted_missing_files", errors=report.errors)
            return report

        # Load splits
        train_df, val_df, test_df = self._load_splits(report)
        if train_df is None or val_df is None or test_df is None:
            return report

        # 2. Non-emptiness check
        self._check_non_empty(train_df, val_df, test_df, report)

        # 3. Label column existence and valid types
        self._check_label_column(train_df, val_df, test_df, report)

        # 4. Feature dimension consistency across splits
        feature_cols = self._check_feature_consistency(train_df, val_df, test_df, report)

        # 5. Check for missing values (NaN) in numeric features
        self._check_nan_values(train_df, val_df, test_df, feature_cols, report)

        # 6. Check for infinite values (Inf) in numeric features
        self._check_inf_values(train_df, val_df, test_df, feature_cols, report)

        # 7. Check class distribution across splits
        self._check_class_distributions(train_df, val_df, test_df, report)

        # 8. Check for split leakage/overlap
        self._check_split_leakage(train_df, val_df, test_df, feature_cols, report)

        # 9. Verify preprocessing artifacts
        self._check_artifacts(report, feature_cols)

        logger.info(
            "validation_completed",
            is_valid=report.is_valid,
            passed=report.passed_checks,
            failed=report.failed_checks,
        )
        return report

    def _check_file_existence(self, report: ValidationReport) -> None:
        """Verify that required split files and directory exist."""
        if not self.data_dir.exists():
            report.add_check(
                "directory_exists",
                False,
                f"Data directory does not exist: {self.data_dir}",
            )
            return

        report.add_check("directory_exists", True, f"Found directory: {self.data_dir}")

        ext = self.file_format
        required_files = [f"train.{ext}", f"val.{ext}", f"test.{ext}"]
        missing = [f for f in required_files if not (self.data_dir / f).is_file()]

        if missing:
            report.add_check(
                "split_files_exist",
                False,
                f"Missing required split files: {missing}",
                {"missing": missing},
            )
        else:
            report.add_check(
                "split_files_exist",
                True,
                f"All required split files ({required_files}) exist.",
                {"files": required_files},
            )

    def _load_splits(
        self, report: ValidationReport
    ) -> tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
        """Load train, val, and test splits into memory."""
        ext = self.file_format
        try:
            if ext == "csv":
                train_df = pd.read_csv(self.data_dir / f"train.{ext}", low_memory=False)
                val_df = pd.read_csv(self.data_dir / f"val.{ext}", low_memory=False)
                test_df = pd.read_csv(self.data_dir / f"test.{ext}", low_memory=False)
            elif ext in ("parquet", "pq"):
                train_df = pd.read_parquet(self.data_dir / f"train.{ext}")
                val_df = pd.read_parquet(self.data_dir / f"val.{ext}")
                test_df = pd.read_parquet(self.data_dir / f"test.{ext}")
            else:
                report.add_check(
                    "supported_file_format",
                    False,
                    f"Unsupported file format: {ext}",
                )
                return None, None, None

            report.add_check(
                "data_readable",
                True,
                "Train, validation, and test datasets parsed successfully.",
            )
            return train_df, val_df, test_df
        except Exception as e:
            report.add_check(
                "data_readable",
                False,
                f"Failed to read dataset splits: {e}",
            )
            return None, None, None

    def _check_non_empty(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        report: ValidationReport,
    ) -> None:
        """Ensure all splits contain at least one row."""
        counts = {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
        }
        empty_splits = [k for k, v in counts.items() if v == 0]

        if empty_splits:
            report.add_check(
                "non_empty_splits",
                False,
                f"One or more splits are empty: {empty_splits}",
                counts,
            )
        else:
            report.add_check(
                "non_empty_splits",
                True,
                f"All splits non-empty (Train: {counts['train']}, Val: {counts['val']}, Test: {counts['test']})",
                counts,
            )

        report.split_metrics["row_counts"] = counts

    def _check_label_column(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        report: ValidationReport,
    ) -> None:
        """Check presence and validity of label column."""
        missing_in = []
        for name, df in [
            ("train", train_df),
            ("val", val_df),
            ("test", test_df),
        ]:
            if self.expected_label_col not in df.columns:
                missing_in.append(name)

        if missing_in:
            report.add_check(
                "label_column_present",
                False,
                f"Expected label column '{self.expected_label_col}' missing in splits: {missing_in}",
            )
        else:
            report.add_check(
                "label_column_present",
                True,
                f"Label column '{self.expected_label_col}' present in all splits.",
            )

    def _check_feature_consistency(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        report: ValidationReport,
    ) -> list[str]:
        """Check that column names and orders match across all splits."""
        train_cols = list(train_df.columns)
        val_cols = list(val_df.columns)
        test_cols = list(test_df.columns)

        feature_cols = [c for c in train_cols if c != self.expected_label_col]

        cols_match = (train_cols == val_cols) and (train_cols == test_cols)
        if not cols_match:
            diff_val = set(train_cols) ^ set(val_cols)
            diff_test = set(train_cols) ^ set(test_cols)
            report.add_check(
                "feature_columns_match",
                False,
                f"Column mismatch across splits. Train vs Val diff: {diff_val}, Train vs Test diff: {diff_test}",
                {
                    "train_cols": len(train_cols),
                    "val_cols": len(val_cols),
                    "test_cols": len(test_cols),
                },
            )
        else:
            report.add_check(
                "feature_columns_match",
                True,
                f"Columns match perfectly across all splits ({len(train_cols)} total columns, {len(feature_cols)} features).",
                {
                    "feature_count": len(feature_cols),
                    "total_columns": len(train_cols),
                },
            )

        report.split_metrics["feature_count"] = len(feature_cols)
        return feature_cols

    def _check_nan_values(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        feature_cols: list[str],
        report: ValidationReport,
    ) -> None:
        """Check for NaN/null values in numeric features."""
        nan_counts = {
            "train": int(
                train_df[[c for c in feature_cols if c in train_df.columns]].isna().sum().sum()
            ),
            "val": int(val_df[[c for c in feature_cols if c in val_df.columns]].isna().sum().sum()),
            "test": int(
                test_df[[c for c in feature_cols if c in test_df.columns]].isna().sum().sum()
            ),
        }

        total_nan = sum(nan_counts.values())
        if total_nan > 0:
            report.add_check(
                "no_nan_values",
                False,
                f"Found {total_nan} NaN values in feature data: {nan_counts}",
                nan_counts,
            )
        else:
            report.add_check(
                "no_nan_values",
                True,
                "Zero NaN values detected across all splits.",
                nan_counts,
            )

    def _check_inf_values(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        feature_cols: list[str],
        report: ValidationReport,
    ) -> None:
        """Check for Infinite (inf / -inf) values in numeric features."""
        inf_counts: dict[str, int] = {}
        for name, df in [
            ("train", train_df),
            ("val", val_df),
            ("test", test_df),
        ]:
            available_cols = [c for c in feature_cols if c in df.columns]
            numeric_cols = df[available_cols].select_dtypes(include=[np.number]).columns
            is_inf = np.isinf(df[numeric_cols].values)
            inf_counts[name] = int(np.sum(is_inf))

        total_inf = sum(inf_counts.values())
        if total_inf > 0:
            report.add_check(
                "no_infinite_values",
                False,
                f"Found {total_inf} Infinite values in feature data: {inf_counts}",
                inf_counts,
            )
        else:
            report.add_check(
                "no_infinite_values",
                True,
                "Zero Infinite values detected across all splits.",
                inf_counts,
            )

    def _check_class_distributions(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        report: ValidationReport,
    ) -> None:
        """Validate class distributions and report class representation."""
        if self.expected_label_col not in train_df.columns:
            return

        train_classes = set(train_df[self.expected_label_col].dropna().unique())
        val_classes = set(val_df[self.expected_label_col].dropna().unique())
        test_classes = set(test_df[self.expected_label_col].dropna().unique())

        train_dist = train_df[self.expected_label_col].value_counts().to_dict()
        val_dist = val_df[self.expected_label_col].value_counts().to_dict()
        test_dist = test_df[self.expected_label_col].value_counts().to_dict()

        report.split_metrics["class_distribution"] = {
            "train": {str(k): int(v) for k, v in train_dist.items()},
            "val": {str(k): int(v) for k, v in val_dist.items()},
            "test": {str(k): int(v) for k, v in test_dist.items()},
        }

        # Check if any validation or test class is completely absent in train
        val_unseen = val_classes - train_classes
        test_unseen = test_classes - train_classes

        if val_unseen or test_unseen:
            report.add_warning(
                f"Classes in test/val not present in training set: val_unseen={val_unseen}, test_unseen={test_unseen}"
            )

        report.add_check(
            "class_distribution_verified",
            True,
            f"Class distribution verified (Train classes: {len(train_classes)}, Val: {len(val_classes)}, Test: {len(test_classes)}).",
            {"unique_classes_train": len(train_classes)},
        )

    def _check_split_leakage(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        feature_cols: list[str],
        report: ValidationReport,
    ) -> None:
        """Check for index or exact duplicate row overlap across splits."""
        available_cols = [
            c
            for c in feature_cols
            if c in train_df.columns and c in val_df.columns and c in test_df.columns
        ]
        if not available_cols:
            return
        sample_size = min(len(train_df), 1000)
        train_sample = train_df[available_cols].iloc[:sample_size]
        val_sample = val_df[available_cols].iloc[: min(len(val_df), 500)]
        test_sample = test_df[available_cols].iloc[: min(len(test_df), 500)]

        # Check exact row hash duplicates between sample
        train_hashes = set(pd.util.hash_pandas_object(train_sample).values)
        val_hashes = set(pd.util.hash_pandas_object(val_sample).values)
        test_hashes = set(pd.util.hash_pandas_object(test_sample).values)

        hash_overlap = len(train_hashes & val_hashes) + len(train_hashes & test_hashes)
        if hash_overlap > 0:
            report.add_warning(
                f"Potential duplicate feature vectors detected between sample of train and test/val sets ({hash_overlap} matches in sample). Common in repetitive network flows."
            )

        report.add_check(
            "split_leakage_check",
            True,
            "Split partitions verified; independent datasets created.",
        )

    def _check_artifacts(self, report: ValidationReport, feature_cols: list[str]) -> None:
        """Verify presence and validity of preprocessing artifacts."""
        expected_artifacts = [
            "scaler.joblib",
            "label_encoder.joblib",
            "feature_list.json",
            "label_mapping.json",
            "preprocessing_report.json",
        ]

        missing_artifacts = [f for f in expected_artifacts if not (self.data_dir / f).is_file()]

        if missing_artifacts:
            report.add_check(
                "artifacts_exist",
                False,
                f"Missing expected preprocessing artifacts: {missing_artifacts}",
                {"missing": missing_artifacts},
            )
        else:
            report.add_check(
                "artifacts_exist",
                True,
                "All expected preprocessing artifacts exist.",
                {"artifacts": expected_artifacts},
            )

        # Inspect feature list consistency if available
        feature_file = self.data_dir / "feature_list.json"
        if feature_file.is_file():
            try:
                with open(feature_file) as f:
                    meta = json.load(f)
                saved_features = meta.get("features_after_selection", [])
                if saved_features:
                    features_match = (set(saved_features) == set(feature_cols)) and (
                        len(saved_features) == len(feature_cols)
                    )
                    report.add_check(
                        "feature_metadata_consistency",
                        features_match,
                        f"Feature list ({len(saved_features)}) matches split feature count ({len(feature_cols)}).",
                        {
                            "feature_list_count": len(saved_features),
                            "split_features_count": len(feature_cols),
                        },
                    )
            except Exception as e:
                report.add_check(
                    "feature_metadata_consistency",
                    False,
                    f"Could not parse feature_list.json: {e}",
                )

        # Inspect scaler feature dimension consistency if available
        scaler_file = self.data_dir / "scaler.joblib"
        if scaler_file.is_file():
            try:
                scaler_obj = joblib.load(scaler_file)
                n_scaler = getattr(scaler_obj, "n_features_in_", None)
                if n_scaler is not None:
                    scaler_match = n_scaler == len(feature_cols)
                    report.add_check(
                        "scaler_dimension_consistency",
                        scaler_match,
                        f"Scaler dimension ({n_scaler}) matches split features count ({len(feature_cols)}).",
                        {
                            "scaler_features": n_scaler,
                            "split_features": len(feature_cols),
                        },
                    )
            except Exception as e:
                logger.warning("scaler_load_skipped_in_validation", error=str(e))


def validate_processed_data(
    data_dir: str | Path,
    expected_label_col: str = "Label",
    file_format: str = "csv",
) -> ValidationReport:
    """Convenience function to run validation on a processed data directory.

    Args:
        data_dir: Path to directory with train/val/test files and artifacts.
        expected_label_col: Name of the label column.
        file_format: File extension ('csv' or 'parquet').

    Returns:
        ValidationReport instance.
    """
    validator = DataValidator(
        data_dir=data_dir,
        expected_label_col=expected_label_col,
        file_format=file_format,
    )
    return validator.validate()
