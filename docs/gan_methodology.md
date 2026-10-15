# CTGAN Methodology, Architecture & Evaluation Protocol

## 1. Mathematical Principles of CTGAN

The software supply chain defense framework relies on generating realistic, diverse network attack telemetry to stress-test adaptive defense policies. Tabular network flow data presents unique challenges:
1. **Multimodal Non-Gaussian Continuous Distributions:** Flow duration, packet lengths, and inter-arrival times (IAT) follow complex distributions with sharp spikes near zero and heavy tails.
2. **Extreme Class Imbalance:** Normal background traffic (`benign`) and large volumetric floods (`dos`) vastly outnumber precision attacks (`web_attack`, `botnet`).
3. **Complex Feature Covariance:** Inter-dependencies between packet counts, byte volumes, and TCP flag states must remain consistent.

To model this, we utilize **Conditional Tabular Generative Adversarial Networks (CTGAN)** (Xu et al., NeurIPS 2019):

### Mode-Specific Normalization
For each continuous feature $C_i$, CTGAN fits a Variational Gaussian Mixture Model (VGM) with $K$ components:
$$P(c_{i, j}) = \sum_{k=1}^K w_k \mathcal{N}(c_{i, j}; \mu_k, \sigma_k)$$
Each scalar value is encoded as a one-hot vector $\beta_{i, j}$ indicating the selected mixture component and a continuous scalar $\alpha_{i, j}$ representing the normalized distance from the mode's center.

### Conditional Generator & Training-by-Sampling
To counteract extreme class imbalance, the conditional generator samples synthetic data conditioned on discrete class labels:
$$\mathbf{z} = [z_1, \dots, z_d, \mathbf{cond}]$$
where $\mathbf{cond}$ is a conditional vector specifying attack category. Training-by-sampling ensures minority attack classes are sampled at equal frequency during discriminator/generator training rounds.

---

## 2. Leakage-Free Architecture & Training Policy

### Strict Isolation Rules
1. **Zero Validation/Test Contamination:** CTGAN is trained **strictly on `data/processed/train.csv`**. Neither `val.csv` nor `test.csv` is ever exposed during transformer fitting, discriminator feedback, or model selection.
2. **Feature Schema Adherence:** The model consumes exactly 71 selected numerical flow features and 1 discrete `Label` column.
3. **No Hallucinated Classes:** The conditional generator strictly enforces that only classes observed in the training split (`benign`, `dos`, `ddos`, `portscan`, `brute_force`, `botnet`, `web_attack`) can be sampled. Classes absent in the development sample (`infiltration`, `heartbleed`) cannot be fabricated.
4. **Physical Constraint Clamping:** Generated features representing physical counters (e.g. `Flow Duration`, `Total Fwd Packets`, `Flow Bytes/s`) are clamped to non-negative domains ($x \ge 0$).

---

## 3. Statistical Validation Metrics

Synthetic data quality is validated against real training data across three dimensions:

### A. 1-D Marginal Fidelity
- **Wasserstein Distance ($W_1$):**
  $$W_1(P, Q) = \int_{-\infty}^\infty |F_P(x) - F_Q(x)| \, dx$$
  Calculated on min-max normalized features $[0, 1]$ to ensure scale invariance across disparate flow counters.
- **Jensen-Shannon Divergence ($D_{JS}$):**
  $$D_{JS}(P \parallel Q) = \frac{1}{2} D_{KL}(P \parallel M) + \frac{1}{2} D_{KL}(Q \parallel M), \quad M = \frac{1}{2}(P + Q)$$
  Evaluated on 20-bin empirical probability distributions with Laplace smoothing.

### B. 2-D Correlation Preservation
- **Pearson Correlation Matrix Similarity:**
  $$\text{Similarity} = 1.0 - \frac{1}{2} \cdot \frac{1}{N^2} \sum_{i,j} |R_{i,j} - S_{i,j}|$$
  where $R$ and $S$ are the correlation matrices of real and synthetic feature spaces.

### C. Diversity & Mode Collapse Auditing
- **Exact Intra-Duplicates:** Proportion of identical rows within the generated dataset ($\le 5\%$).
- **Memorization Rate:** Bit-for-bit matches between synthetic records and real training records ($\le 2\%$).
- **Variance Ratio:** $\sigma_{synth} / \sigma_{real}$; checks that generator has not collapsed onto a single mode.

---

## 4. Downstream ML Utility Protocol

To verify that synthetic data preserves discriminative attack boundaries, a controlled empirical experiment is executed:
- **Model A (Real Only):** `RandomForestClassifier` trained exclusively on real training data ($N_{real} = 3,437$).
- **Model B (Augmented):** Identical `RandomForestClassifier` trained on real training data augmented with accepted conditional synthetic samples ($N_{aug} = N_{real} + N_{synth}$).
- **Untouched Real Test Set:** Both models are evaluated on the identical, untouched test partition (`data/processed/test.csv`, $N_{test} = 737$).
- **Primary Metric:** Macro-Averaged F1-Score ($\text{Macro-F1}$) to ensure performance gains on minority attack classes are strictly evaluated without being obscured by the majority `benign` class.
