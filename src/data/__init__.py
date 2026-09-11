"""
ASCCD Data Package.

Provides dataset loading, cleaning, preprocessing, splitting, and validation
for the CIC-IDS2017 network attack dataset used in the ASCCD project.
"""

from src.data.loader import discover_csv_files, load_dataset, load_single_csv
from src.data.preprocessor import DataPreprocessor, PreprocessingReport
from src.data.splitter import SplitStatistics, stratified_split
from src.data.validator import (
    DataValidator,
    ValidationCheck,
    ValidationReport,
    validate_processed_data,
)

__all__ = [
    "discover_csv_files",
    "load_single_csv",
    "load_dataset",
    "DataPreprocessor",
    "PreprocessingReport",
    "stratified_split",
    "SplitStatistics",
    "DataValidator",
    "ValidationCheck",
    "ValidationReport",
    "validate_processed_data",
]
