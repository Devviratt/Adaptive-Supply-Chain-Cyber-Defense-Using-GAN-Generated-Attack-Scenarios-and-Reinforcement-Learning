# Synthetic Attack Data Quality & Fidelity Report

**Validation Status:** ⚠️ WARNING  
**Total Real Samples:** 3,437  
**Total Synthetic Samples:** 2,000  
**Total Evaluated Features:** 72  

---

## 1. Key Evaluation Metrics

| Metric | Value | Acceptance Threshold | Result |
| :--- | :--- | :--- | :--- |
| **Mean Wasserstein Distance (W1)** | `0.1057` | `< 0.35` | ✅ PASS |
| **Median Wasserstein Distance** | `0.1017` | Reference | - |
| **Mean Jensen-Shannon Divergence** | `0.5117` | `< 0.50` | ❌ FAIL |
| **Pearson Correlation Similarity** | `0.9869` | `> 0.70` | ✅ PASS |
| **Relative Frobenius Norm Diff** | `0.2787` | Reference | - |
| **Synthetic Exact Duplicate Ratio** | `0.00%` | `< 5.0%` | ✅ PASS |
| **Real-to-Synthetic Memorization** | `0.00%` | `< 2.0%` | ✅ PASS |
| **Mode Collapsed Features** | `0` | `< 5` | ✅ PASS |

---

## 2. Integrity and Schema Checks

- Schema & Column Order Match: `PASS`
- Zero NaN / Inf Values: `PASS`
- Valid Label Set (No Hallucinated Classes): `PASS`

## 3. Class Distribution Comparison

| Class Label | Real Training Count | Synthetic Count | Synthetic Proportion |
| :--- | :--- | :--- | :--- |
| `benign` | 2,763 | 511 | 25.55% |
| `botnet` | 12 | 168 | 8.40% |
| `brute_force` | 60 | 242 | 12.10% |
| `ddos` | 104 | 270 | 13.50% |
| `dos` | 368 | 379 | 18.95% |
| `portscan` | 122 | 292 | 14.60% |
| `web_attack` | 8 | 138 | 6.90% |

---

## 4. Warnings and Failures

- ⚠️ Mean Jensen-Shannon divergence (0.512) exceeded threshold (0.500).
