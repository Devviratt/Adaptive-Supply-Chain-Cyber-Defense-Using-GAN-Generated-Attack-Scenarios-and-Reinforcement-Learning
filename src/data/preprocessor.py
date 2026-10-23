"""
ASCCD Data Preprocessor — cleaning, encoding, scaling, feature selection.

Handles the complete preprocessing pipeline for CIC-IDS2017 data.
Designed to prevent data leakage: all transformations are fitted on
training data only.

Author: Deekshay G (primary), reviewed by Anandavarthan & Dev Virat
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, RobustScaler, StandardScaler

from src.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PreprocessingReport:
    """Tracks all preprocessing operations for auditability."""

    source_files: list[str] = field(default_factory=list)
    rows_before_cleaning: int = 0
    rows_after_cleaning: int = 0
    duplicates_removed: int = 0
    nan_values_handled: int = 0
    inf_values_handled: int = 0
    columns_dropped_configured: list[str] = field(default_factory=list)
    columns_dropped_nan_threshold: list[str] = field(default_factory=list)
    features_removed_variance: list[str] = field(default_factory=list)
    features_removed_correlation: list[str] = field(default_factory=list)
    original_feature_count: int = 0
    final_feature_count: int = 0
    label_mapping_applied: dict[str, str] = field(default_factory=dict)
    unmapped_labels: list[str] = field(default_factory=list)
    class_distribution: dict[str, int] = field(default_factory=dict)
    scaler_type: str = ""
    random_seed: int = 42
    preprocessing_version: str = "1.0.0"
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_files": self.source_files,
            "rows_before_cleaning": self.rows_before_cleaning,
            "rows_after_cleaning": self.rows_after_cleaning,
            "duplicates_removed": self.duplicates_removed,
            "nan_values_handled": self.nan_values_handled,
            "inf_values_handled": self.inf_values_handled,
            "columns_dropped_configured": self.columns_dropped_configured,
            "columns_dropped_nan_threshold": self.columns_dropped_nan_threshold,
            "features_removed_variance": self.features_removed_variance,
            "features_removed_correlation": self.features_removed_correlation,
            "original_feature_count": self.original_feature_count,
            "final_feature_count": self.final_feature_count,
            "label_mapping_applied": self.label_mapping_applied,
            "unmapped_labels": self.unmapped_labels,
            "class_distribution": self.class_distribution,
            "scaler_type": self.scaler_type,
            "random_seed": self.random_seed,
            "preprocessing_version": self.preprocessing_version,
            "warnings": self.warnings,
        }

    def save(self, filepath: str | Path) -> None:
        """Save report to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info("preprocessing_report_saved", filepath=str(filepath))


class DataPreprocessor:
    """CIC-IDS2017 data preprocessing pipeline.

    Follows the leakage-safe order:
      1. Drop configured columns
      2. Clean data (duplicates, NaN, Inf)
      3. Normalize labels
      4. (Splitting happens externally before fit_transform)
      5. Fit transformations on training data only
      6. Transform all splits with fitted transformers

    Usage:
        preprocessor = DataPreprocessor(config)
        df_cleaned = preprocessor.clean(df)
        X_train, y_train, X_val, y_val, X_test, y_test = ...  # split first
        preprocessor.fit(X_train)  # fit only on training features
        X_train_scaled = preprocessor.transform(X_train)
        X_val_scaled = preprocessor.transform(X_val)
        X_test_scaled = preprocessor.transform(X_test)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize preprocessor with configuration.

        Args:
            config: Preprocessing configuration dictionary.
        """
        self.config = config
        self.report = PreprocessingReport()
        self.report.random_seed = config.get("random_seed", 42)

        # Scaler — created but NOT fitted until .fit() is called
        scaler_type = config.get("scaler", "standard")
        self.report.scaler_type = scaler_type
        if scaler_type == "standard":
            self.scaler = StandardScaler()
        elif scaler_type == "minmax":
            self.scaler = MinMaxScaler()
        elif scaler_type == "robust":
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unknown scaler type: {scaler_type}")

        # Label encoder
        self.label_encoder = LabelEncoder()
        self.label_mapping: dict[str, str] = config.get("label_mapping", {})
        self.valid_labels: list[str] = config.get("valid_labels", [])

        # Feature selection params
        fs_config = config.get("feature_selection", {})
        self.variance_threshold = fs_config.get("variance_threshold", 0.01)
        self.correlation_threshold = fs_config.get("correlation_threshold", 0.95)

        # Track fitted state
        self._is_fitted = False
        self._feature_names: list[str] = []
        self._features_after_selection: list[str] = []

    # ================================================================
    # STEP 1: Drop configured columns
    # ================================================================
    def drop_configured_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove columns specified in configuration (IPs, ports, timestamps).

        These are identifiers/metadata, not generalizable features.
        """
        drop_cols = self.config.get("drop_columns", [])
        cols_to_drop = [c for c in drop_cols if c in df.columns]
        cols_not_found = [c for c in drop_cols if c not in df.columns]

        if cols_not_found:
            self.report.warnings.append(f"Configured drop columns not in data: {cols_not_found}")

        self.report.columns_dropped_configured = cols_to_drop
        df = df.drop(columns=cols_to_drop, errors="ignore")

        logger.info(
            "columns_dropped",
            dropped=cols_to_drop,
            not_found=cols_not_found if cols_not_found else None,
        )
        return df

    # ================================================================
    # STEP 2: Clean data
    # ================================================================
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the dataframe: duplicates, NaN, Inf, whitespace.

        This modifies the dataframe in-place-style (returns cleaned copy).
        Must be called BEFORE splitting.

        Args:
            df: Raw dataframe after column dropping.

        Returns:
            Cleaned dataframe.
        """
        df = df.copy()
        self.report.rows_before_cleaning = len(df)

        # --- Duplicate removal ---
        n_before = len(df)
        df = df.drop_duplicates()
        self.report.duplicates_removed = n_before - len(df)
        if self.report.duplicates_removed > 0:
            logger.info("duplicates_removed", count=self.report.duplicates_removed)

        # --- Infinity handling ---
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        inf_mask = np.isinf(df[numeric_cols].values) if numeric_cols else np.array([])
        inf_count = int(np.sum(inf_mask)) if inf_mask.size > 0 else 0
        self.report.inf_values_handled = inf_count

        if inf_count > 0:
            inf_strategy = self.config.get("inf_handling", "replace_with_nan")
            if inf_strategy == "replace_with_nan":
                df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
            logger.info("inf_values_handled", count=inf_count, strategy=inf_strategy)

        # --- Drop columns with too many NaN ---
        missing_config = self.config.get("missing_values", {})
        col_threshold = missing_config.get("column_threshold", 0.5)
        nan_fractions = df.isnull().mean()
        high_nan_cols = nan_fractions[nan_fractions > col_threshold].index.tolist()

        if high_nan_cols:
            # Don't drop the Label column even if it has NaN
            high_nan_cols = [c for c in high_nan_cols if c != "Label"]
            self.report.columns_dropped_nan_threshold = high_nan_cols
            df = df.drop(columns=high_nan_cols)
            logger.info(
                "high_nan_columns_dropped",
                columns=high_nan_cols,
                threshold=col_threshold,
            )

        # --- Row-level NaN handling ---
        strategy = missing_config.get("strategy", "drop_rows")
        nan_count_before = int(df.isnull().sum().sum())

        if strategy == "drop_rows":
            df = df.dropna()
        elif strategy == "median":
            # Only fill numeric columns; non-numeric NaN rows are dropped
            for col in df.select_dtypes(include=[np.number]).columns:
                df[col] = df[col].fillna(df[col].median())
            df = df.dropna()  # Drop remaining non-numeric NaN
        elif strategy == "mean":
            for col in df.select_dtypes(include=[np.number]).columns:
                df[col] = df[col].fillna(df[col].mean())
            df = df.dropna()
        elif strategy == "zero":
            for col in df.select_dtypes(include=[np.number]).columns:
                df[col] = df[col].fillna(0)
            df = df.dropna()

        nan_count_after = int(df.isnull().sum().sum())
        self.report.nan_values_handled = nan_count_before - nan_count_after

        self.report.rows_after_cleaning = len(df)

        logger.info(
            "data_cleaned",
            rows_before=self.report.rows_before_cleaning,
            rows_after=self.report.rows_after_cleaning,
            nan_handled=self.report.nan_values_handled,
            strategy=strategy,
        )

        return df.reset_index(drop=True)

    # ================================================================
    # STEP 3: Normalize labels
    # ================================================================
    def normalize_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize the Label column using the configured mapping.

        Labels not in the mapping are set to 'unknown'.

        Args:
            df: DataFrame with a 'Label' column.

        Returns:
            DataFrame with normalized labels.
        """
        if "Label" not in df.columns:
            self.report.warnings.append("No 'Label' column found — skipping normalization")
            return df

        original_labels = df["Label"].unique().tolist()

        # Pre-normalize mapping keys so dash variants match regardless of character encoding
        norm_mapping = {
            re.sub(r"[\x96\u2013\u2014\u2212]", "-", k).strip().lower(): v
            for k, v in self.label_mapping.items()
        }

        def clean_and_map(val: Any) -> str:
            if not isinstance(val, str):
                return "unknown"
            s = val.strip()
            if s in self.label_mapping:
                return self.label_mapping[s]
            normalized = re.sub(r"[\x96\u2013\u2014\u2212]", "-", s).strip().lower()
            if normalized in norm_mapping:
                return norm_mapping[normalized]
            return "unknown"

        # Apply mapping
        df["Label"] = df["Label"].map(clean_and_map)

        # Track unmapped labels
        unmapped = [lbl for lbl in original_labels if clean_and_map(lbl) == "unknown"]
        if unmapped:
            self.report.unmapped_labels = unmapped
            self.report.warnings.append(f"Unmapped labels found (set to 'unknown'): {unmapped}")
            logger.warning("unmapped_labels", labels=unmapped)

        self.report.label_mapping_applied = self.label_mapping
        self.report.class_distribution = df["Label"].value_counts().to_dict()

        logger.info(
            "labels_normalized",
            unique_labels=df["Label"].nunique(),
            distribution=self.report.class_distribution,
        )

        return df

    # ================================================================
    # STEP 4: Feature selection (applied to training features only)
    # ================================================================
    def select_features(self, X: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Select features using variance and correlation thresholds.

        MUST be called on training data only. The selected feature list
        is stored and applied to val/test via transform().

        Args:
            X: Training feature DataFrame (numeric only).

        Returns:
            Tuple of (selected features DataFrame, selection report dict).
        """
        report: dict[str, Any] = {
            "original_count": len(X.columns),
            "removed_variance": [],
            "removed_correlation": [],
            "final_count": 0,
        }

        self.report.original_feature_count = len(X.columns)

        # --- Variance threshold ---
        variances = X.var()
        low_var_cols = variances[variances < self.variance_threshold].index.tolist()
        if low_var_cols:
            X = X.drop(columns=low_var_cols)
            report["removed_variance"] = low_var_cols
            self.report.features_removed_variance = low_var_cols
            logger.info(
                "low_variance_features_removed",
                count=len(low_var_cols),
                features=low_var_cols[:10],  # Log up to 10
            )

        # --- Correlation threshold ---
        if len(X.columns) > 1:
            corr_matrix = X.corr().abs()
            upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            high_corr_cols = [
                col for col in upper_tri.columns if any(upper_tri[col] > self.correlation_threshold)
            ]
            if high_corr_cols:
                X = X.drop(columns=high_corr_cols)
                report["removed_correlation"] = high_corr_cols
                self.report.features_removed_correlation = high_corr_cols
                logger.info(
                    "high_correlation_features_removed",
                    count=len(high_corr_cols),
                    features=high_corr_cols[:10],
                )

        self._features_after_selection = list(X.columns)
        report["final_count"] = len(X.columns)
        self.report.final_feature_count = len(X.columns)

        logger.info(
            "feature_selection_complete",
            original=report["original_count"],
            final=report["final_count"],
            removed_total=(len(report["removed_variance"]) + len(report["removed_correlation"])),
        )

        return X, report

    # ================================================================
    # STEP 5: Fit on training data
    # ================================================================
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series | None = None) -> None:
        """Fit the scaler and label encoder on training data ONLY.

        This is where data-leakage prevention happens. The scaler learns
        statistics ONLY from training features. The label encoder learns
        classes ONLY from training labels.

        Args:
            X_train: Training features (numeric, after feature selection).
            y_train: Training labels (optional, for label encoder).
        """
        # Fit scaler on training features
        self._feature_names = list(X_train.columns)
        self.scaler.fit(X_train)

        # Fit label encoder on training labels
        if y_train is not None:
            self.label_encoder.fit(y_train)

        self._is_fitted = True
        logger.info(
            "preprocessor_fitted",
            n_features=len(self._feature_names),
            scaler=self.report.scaler_type,
        )

    # ================================================================
    # STEP 6: Transform (any split)
    # ================================================================
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features using the fitted scaler.

        Args:
            X: Feature DataFrame to transform.

        Returns:
            Scaled DataFrame with the same columns.

        Raises:
            RuntimeError: If fit() has not been called.
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor not fitted. Call fit(X_train) before transform().")

        # Ensure only the selected features are present
        missing = set(self._feature_names) - set(X.columns)
        if missing:
            raise ValueError(f"Missing {len(missing)} expected features: {sorted(missing)[:5]}")

        X_selected = X[self._feature_names]
        scaled_values = self.scaler.transform(X_selected)
        return pd.DataFrame(scaled_values, columns=self._feature_names, index=X.index)

    def encode_labels(self, y: pd.Series) -> np.ndarray:
        """Encode labels using the fitted label encoder.

        Args:
            y: Series of string labels.

        Returns:
            Numpy array of encoded integer labels.
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor not fitted. Call fit() before encode_labels().")
        return self.label_encoder.transform(y)

    def prepare_raw(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop configured columns, clean anomalies, and normalize labels.

        Args:
            df: Raw DataFrame as loaded from CSV.

        Returns:
            Cleaned and normalized DataFrame ready for splitting.
        """
        df = self.drop_configured_columns(df)
        df = self.clean(df)
        df = self.normalize_labels(df)
        return df

    def fit_transform(self, X: pd.DataFrame, y: pd.Series | None = None) -> pd.DataFrame:
        """Fit on features (with feature selection) and return scaled features.

        Args:
            X: Training feature DataFrame.
            y: Optional training labels.

        Returns:
            Transformed features DataFrame.
        """
        X_selected, _ = self.select_features(X)
        self.fit(X_selected, y)
        return self.transform(X_selected)

    def fit_transform_splits(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        label_column: str = "Label",
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Fit feature selection and scaler strictly on train_df, then transform all splits.

        Eliminates data leakage across splits.

        Args:
            train_df: Training DataFrame with features and label column.
            val_df: Validation DataFrame with features and label column.
            test_df: Test DataFrame with features and label column.
            label_column: Name of the label column.

        Returns:
            Tuple of (train_processed, val_processed, test_processed) DataFrames.
        """
        # Separate features and labels
        X_train = train_df.drop(columns=[label_column], errors="ignore")
        y_train = train_df[label_column] if label_column in train_df.columns else None

        X_val = val_df.drop(columns=[label_column], errors="ignore")
        y_val = val_df[label_column] if label_column in val_df.columns else None

        X_test = test_df.drop(columns=[label_column], errors="ignore")
        y_test = test_df[label_column] if label_column in test_df.columns else None

        # 1. Feature selection ON TRAIN ONLY
        X_train_selected, _ = self.select_features(X_train)
        selected_cols = self._features_after_selection

        # 2. Keep only selected columns in val and test
        X_val_selected = X_val[selected_cols]
        X_test_selected = X_test[selected_cols]

        # 3. Fit scaler ON TRAIN ONLY, and fit label encoder
        self.fit(X_train_selected, y_train)

        # 4. Transform features with fitted scaler
        X_train_scaled = self.transform(X_train_selected)
        X_val_scaled = self.transform(X_val_selected)
        X_test_scaled = self.transform(X_test_selected)

        # 5. Re-attach labels
        train_processed = X_train_scaled.copy()
        if y_train is not None:
            train_processed[label_column] = y_train.values

        val_processed = X_val_scaled.copy()
        if y_val is not None:
            val_processed[label_column] = y_val.values

        test_processed = X_test_scaled.copy()
        if y_test is not None:
            test_processed[label_column] = y_test.values

        return train_processed, val_processed, test_processed

    # ================================================================
    # Artifact saving/loading
    # ================================================================
    def save_artifacts(self, output_dir: str | Path) -> dict[str, str]:
        """Save all preprocessing artifacts for reproducibility.

        Saves:
          - scaler (joblib)
          - label_encoder (joblib)
          - feature_list (JSON)
          - label_mapping (JSON)
          - preprocessing_report (JSON)

        Args:
            output_dir: Directory to save artifacts.

        Returns:
            Dictionary mapping artifact names to file paths.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        artifacts: dict[str, str] = {}

        # Scaler
        scaler_path = output_path / "scaler.joblib"
        joblib.dump(self.scaler, scaler_path)
        artifacts["scaler"] = str(scaler_path)

        # Label encoder
        encoder_path = output_path / "label_encoder.joblib"
        joblib.dump(self.label_encoder, encoder_path)
        artifacts["label_encoder"] = str(encoder_path)

        # Feature list
        features_path = output_path / "feature_list.json"
        with open(features_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "features_after_selection": self._features_after_selection,
                    "features_used_for_scaling": self._feature_names,
                },
                f,
                indent=2,
            )
        artifacts["feature_list"] = str(features_path)

        # Label mapping
        mapping_path = output_path / "label_mapping.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "label_mapping": self.label_mapping,
                    "valid_labels": self.valid_labels,
                    "encoder_classes": (
                        list(self.label_encoder.classes_)
                        if hasattr(self.label_encoder, "classes_")
                        else []
                    ),
                },
                f,
                indent=2,
            )
        artifacts["label_mapping"] = str(mapping_path)

        # Report
        report_path = output_path / "preprocessing_report.json"
        self.report.save(report_path)
        artifacts["preprocessing_report"] = str(report_path)

        logger.info("artifacts_saved", output_dir=str(output_dir), files=list(artifacts.keys()))
        return artifacts

    @classmethod
    def load_artifacts(cls, artifact_dir: str | Path) -> DataPreprocessor:
        """Load a fitted preprocessor from saved artifacts.

        Args:
            artifact_dir: Directory containing saved artifacts.

        Returns:
            Fitted DataPreprocessor instance.
        """
        artifact_path = Path(artifact_dir)

        # Load scaler
        scaler = joblib.load(artifact_path / "scaler.joblib")

        # Load label encoder
        label_encoder = joblib.load(artifact_path / "label_encoder.joblib")

        # Load feature list
        with open(artifact_path / "feature_list.json") as f:
            feature_info = json.load(f)

        # Load label mapping
        with open(artifact_path / "label_mapping.json") as f:
            mapping_info = json.load(f)

        # Reconstruct preprocessor
        preprocessor = cls.__new__(cls)
        preprocessor.scaler = scaler
        preprocessor.label_encoder = label_encoder
        preprocessor.label_mapping = mapping_info.get("label_mapping", {})
        preprocessor.valid_labels = mapping_info.get("valid_labels", [])
        preprocessor._feature_names = feature_info.get("features_used_for_scaling", [])
        preprocessor._features_after_selection = feature_info.get("features_after_selection", [])
        preprocessor._is_fitted = True
        preprocessor.report = PreprocessingReport()
        preprocessor.config = {}

        logger.info("artifacts_loaded", artifact_dir=str(artifact_dir))
        return preprocessor
