# Review 1 (40% Milestone) Presentation & Live Demo Script
**Project:** Adaptive Supply Chain Cyber Defense Using GAN-Generated Attack Scenarios and Reinforcement Learning (ASCCD)  
**Team 84** — Dayananda Sagar University (School of Engineering)  
**Guide:** Prof. Namyapriya D  

---

## ⏱️ 5-Minute Presentation Outline & Speaker Roles

| Time | Topic | Speaker | Live Screen Action |
| :---: | :--- | :--- | :--- |
| **0:00 - 1:00** | Introduction & Problem Statement | **C A Anandavarthan** | Open **Overview** page (`http://localhost:5173`) |
| **1:00 - 2:15** | Dataset, Class Imbalance & CTGAN | **Deekshay G** | Switch to **Review 1 Demo ➔ Tab 2 & 3** |
| **2:15 - 3:30** | Scientific GAN Validation Audit | **Deekshay G** | Switch to **Review 1 Demo ➔ Tab 4** |
| **3:30 - 4:30** | Digital Twin Cascading Containment | **Dev Virat** | Switch to **Review 1 Demo ➔ Tab 5** |
| **4:30 - 5:00** | Summary & Scope Completed (40%) | **All / Team Lead** | Conclude & Open for Viva Questions |

---

## 🎙️ Word-for-Word Verbal Script

### 1. Introduction & Research Problem (C A Anandavarthan — 1 min)
> *"Respected guide Prof. Namyapriya D and esteemed panel members. Good morning. We are Team 84, presenting Review 1 for our project: **Adaptive Supply Chain Cyber Defense Using GAN-Generated Attack Scenarios and Reinforcement Learning**.*
>
> *Recent high-profile cyber incidents like SolarWinds and Log4j demonstrated that modern software systems do not fail in isolation; attacks propagate across interconnected supply chain dependencies. Traditional Intrusion Detection Systems only inspect individual network packets at single servers and cannot anticipate cascading supply chain failures.*
>
> *Our research investigates: **Can validated GAN-generated attack-scenario diversity improve the decision robustness and availability of an adaptive defense policy in a simulated supply-chain environment?***
>
> *For Review 1, representing the foundational 40% milestone, we have completed the end-to-end data pipeline, the CTGAN generative attack model, empirical statistical validation, and the 5-stage supply chain digital twin environment."*

---

### 2. Dataset & CTGAN Generative Model (Deekshay G — 1.25 min)
*(Click on **Review 1 Live Demo ➔ Tab 2: Preprocessing**, then **Tab 3: CTGAN Lab**)*

> *"To train adaptive defense systems, we need realistic attack data. We evaluated the Canadian Institute for Cybersecurity **CIC-IDS2017** benchmark, comprising over 2.83 million network sessions.*
>
> *However, we encountered a fundamental challenge: **extreme class imbalance**. Normal benign traffic represents 80.3% of the dataset, whereas critical attacks like Botnets, Brute Force, and Web Infiltrations comprise less than 0.5% combined (a 400:1 ratio). Standard classifiers and RL agents overfit to benign patterns and fail on minority attacks.*
>
> *Rather than basic linear interpolation like SMOTE, we implemented **Conditional Tabular GAN (CTGAN)**. As demonstrated live on screen in Tab 3, we can condition the generator on any attack class—such as DoS, DDoS, or PortScan—and synthesize novel, high-dimensional attack telemetry with tailored flow duration, packet rates, and severity levels targeting specific supply chain stages."*

---

### 3. Scientific Validation Audit (Deekshay G — 1.25 min)
*(Click on **Review 1 Live Demo ➔ Tab 4: Scientific Validation Audit**)*

> *"A critical requirement in generative cyber defense is proving that the synthetic data is mathematically valid and not hallucinated or memorized. We established a three-pillar validation audit:*
>
> 1. ***Marginal Distribution Fidelity:*** *Our Wasserstein-1 distance is **0.1057**, well below the strict 0.15 passing threshold.*
> 2. ***Covariance Alignment:*** *The Pearson correlation matrix similarity between real and synthetic data is **0.9869**, proving that complex dependencies between network packet attributes were faithfully preserved.*
> 3. ***Privacy & Novelty:*** *Nearest-neighbor distance tests revealed a **0.00% exact memorization rate**, proving that CTGAN generates truly novel synthetic vectors.*
> 4. ***Downstream Utility:*** *Augmenting our training data with CTGAN samples improved classifier test accuracy by **+1.49%**."*

---

### 4. Supply Chain Digital Twin & Live Mitigation (Dev Virat — 1 min)
*(Click on **Review 1 Live Demo ➔ Tab 5: Digital Twin Propagation**)*

> *"Now, let us demonstrate how these attack scenarios interact with our software supply chain.*
>
> *On screen is our 5-stage Digital Twin environment: **Supplier ➔ Ingestion ➔ Processing ➔ Registry ➔ Deployment**.*
>
> *When we inject an attack at Stage 1 (Supplier), you can see the vulnerability begin to propagate downstream, threatening build runners and registry integrity. When our autonomous defense triggers an action such as **ISOLATE_NODE** or **FAILOVER_BACKUP**, the compromised dependency is immediately quarantined, preventing lateral movement. As you can see, downstream stages remain at 100% health with zero service interruption.*
>
> *This completes our foundational deliverables for Review 1: Data Pipeline, CTGAN Generation, Statistical Validation, and Environment Formulation. Thank you, and we welcome your questions."*

---

## 🎯 Top 5 Examiner Questions & Rebuttals (Viva Cheat-Sheet)

#### Q1: "Why did you use CTGAN instead of SMOTE?"
- **Answer:** SMOTE operates by drawing linear lines between Euclidean neighbors. In network intrusion data, features have multi-modal continuous distributions and discrete constraints; linear interpolation creates unrealistic values in sparse regions. CTGAN uses Variational Gaussian Mixture Models (VGM) for mode-specific normalization and conditional generator loss to properly capture non-linear tabular distributions.

#### Q2: "What is your contribution for Review 1?"
- **Answer:** Review 1 represents the data and model foundation (40%):
  1. Complete ingestion and preprocessing of 2.83M records from CIC-IDS2017.
  2. Implementation, training, and tuning of the CTGAN architecture.
  3. Comprehensive statistical validation ($W_1 = 0.1057$, Pearson $r = 0.9869$, $0.00\%$ memorization).
  4. Design of the Gymnasium-based Supply Chain Digital Twin with 5 interdependent stages.

#### Q3: "How does network telemetry relate to a software supply chain?"
- **Answer:** Supply chains communicate over internal network endpoints (e.g., git cloning upstream repos, pulling Docker base images, CI/CD artifact push/pull). Intrusion attacks (e.g. DDoS, credential brute-force, web injection) manifest as network telemetry anomalies targeting those specific microservices. Our Scenario Mapper translates those network anomalies into stage-specific risk, availability impact, and propagation probabilities.

#### Q4: "What is the action space of your defense model?"
- **Answer:** The defense system operates on 5 discrete actions: `MONITOR` (passive observation), `ISOLATE_NODE` (quarantine stage), `THROTTLE_TRAFFIC` (rate-limit ingress), `REROUTE_SUPPLY` (switch to authenticated vendor), and `FAILOVER_BACKUP` (activate standby node).

#### Q5: "What is planned for Review 2 and Final Review?"
- **Answer:** Deep Reinforcement Learning defense policy training (DQN and PPO), hyperparameter tuning, and large-scale comparative benchmarking across controlled experimental conditions (Baseline vs Real-Only vs GAN-Augmented) across availability, mitigation success, and decision latency.
