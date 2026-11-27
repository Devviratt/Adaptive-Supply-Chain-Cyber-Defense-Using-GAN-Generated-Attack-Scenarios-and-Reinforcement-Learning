# ASCCD Data Validation Report

**Status:** PASSED  
**Checks Passed:** 13/13  
**Failed Checks:** 0  
**Warnings:** 0  

## Summary of Checks

| Check | Status | Description |
|-------|--------|-------------|
| directory_exists | Pass | Found directory: data\cicids2017_sample\processed |
| split_files_exist | Pass | All required split files (['train.csv', 'val.csv', 'test.csv']) exist. |
| data_readable | Pass | Train, validation, and test datasets parsed successfully. |
| non_empty_splits | Pass | All splits non-empty (Train: 50000, Val: 10714, Test: 10715) |
| label_column_present | Pass | Label column 'Label' present in all splits. |
| feature_columns_match | Pass | Columns match perfectly across all splits (44 total columns, 43 features). |
| no_nan_values | Pass | Zero NaN values detected across all splits. |
| no_infinite_values | Pass | Zero Infinite values detected across all splits. |
| class_distribution_verified | Pass | Class distribution verified (Train classes: 9, Val: 9, Test: 9). |
| split_leakage_check | Pass | Split partitions verified; independent datasets created. |
| artifacts_exist | Pass | All expected preprocessing artifacts exist. |
| feature_metadata_consistency | Pass | Feature list (43) matches split feature count (43). |
| scaler_dimension_consistency | Pass | Scaler dimension (43) matches split features count (43). |

## Split Metrics

### Row_counts Set
- **train:** 50000
- **val:** 10714
- **test:** 10715
### Feature_count Set
### Class_distribution Set
- **train:** {'benign': 40761, 'dos': 4469, 'ddos': 3067, 'brute_force': 534, 'web_attack': 385, 'portscan': 381, 'botnet': 370, 'infiltration': 25, 'heartbleed': 8}
- **val:** {'benign': 8734, 'dos': 957, 'ddos': 657, 'brute_force': 114, 'web_attack': 82, 'portscan': 82, 'botnet': 80, 'infiltration': 6, 'heartbleed': 2}
- **test:** {'benign': 8735, 'dos': 958, 'ddos': 658, 'brute_force': 115, 'web_attack': 83, 'portscan': 81, 'botnet': 79, 'infiltration': 5, 'heartbleed': 1}