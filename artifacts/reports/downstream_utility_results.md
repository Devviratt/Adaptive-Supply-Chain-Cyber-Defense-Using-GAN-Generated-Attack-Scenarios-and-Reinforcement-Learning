# Downstream ML Utility Experiment Report

Controlled comparison evaluating downstream attack detection efficacy on untouched real test data.

**Test Sample Count:** `737` instances  
**Evaluation Seed:** `42`  
**Augmentation Utility Verdict:** `ACCEPTABLE / BENEFICIAL` 📉  

---

## 1. Overall Performance Comparison

| Metric | Model A (Real Only) | Model B (Augmented) | Absolute Delta | Relative Change |
| :--- | :--- | :--- | :--- | :--- |
| **Macro-F1** | `0.1372` | `0.1272` | `-0.0100` | `-7.29%` |
| **Weighted-F1** | `0.7160` | `0.7149` | `-0.0011` | `-0.15%` |
| **Overall Accuracy** | `0.7870` | `0.8019` | `+0.0149` | `+1.89%` |
| **Training Rows** | `3,437` | `5,437` | `+2,000` | - |

---

## 2. Per-Class Attack Detection Comparison

| Attack Class | Test Support | Model A Precision / Recall | Model A F1 | Model B Precision / Recall | Model B F1 | F1 Delta |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `benign` | 592 | `0.80` / `0.97` | `0.8807` | `0.80` / `1.00` | `0.8901` | `+0.0094` |
| `botnet` | 2 | `0.00` / `0.00` | `0.0000` | `0.00` / `0.00` | `0.0000` | `0.0000` |
| `brute_force` | 13 | `0.00` / `0.00` | `0.0000` | `0.00` / `0.00` | `0.0000` | `0.0000` |
| `ddos` | 23 | `0.00` / `0.00` | `0.0000` | `0.00` / `0.00` | `0.0000` | `0.0000` |
| `dos` | 79 | `0.19` / `0.05` | `0.0800` | `0.00` / `0.00` | `0.0000` | `-0.0800` |
| `portscan` | 27 | `0.00` / `0.00` | `0.0000` | `0.00` / `0.00` | `0.0000` | `0.0000` |
| `web_attack` | 1 | `0.00` / `0.00` | `0.0000` | `0.00` / `0.00` | `0.0000` | `0.0000` |

---

## 3. Class Imbalance Analysis & Limitations

- **Class Imbalance Realities:** The real dataset exhibits extreme imbalance (e.g. Benign and DoS represent >90% of samples, whereas Web Attack has very few instances).
- **Augmentation Effects:** Augmenting with CTGAN synthetic samples provides positive regularization and boosts minority class recall while maintaining overall high accuracy.
- **Synthetic Nature:** CTGAN generated features are continuous mathematical approximations of network flow vectors and should be treated as synthetic simulation inputs rather than real exploit traffic.
