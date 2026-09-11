# Viva Questions and Answers

## Prepared answers for project presentation and evaluation.

---

### 1. What is the main objective of your project?

To experimentally evaluate whether GAN-generated synthetic attack-scenario diversity can improve the performance and robustness of a reinforcement-learning-based adaptive defense policy in a simulated software supply-chain environment.

### 2. What is your research gap?

Recent research has separately advanced GAN-based attack-data augmentation and adaptive RL-based cyber defense. However, there is limited experimental evaluation of whether GAN-generated attack-scenario diversity can improve RL-based mitigation decisions within a simulated software supply-chain dependency environment.

### 3. Why did you choose CIC-IDS2017?

CIC-IDS2017 is a widely used, publicly available, labeled network intrusion detection dataset. It provides realistic attack feature distributions for multiple attack types. We use it as a source of attack behavior features, not as a supply-chain dataset itself.

### 4. How does your supply chain simulation work?

We built a custom Gymnasium environment with four stages: Supplier, Build, Registry, and Deployment. Attack scenarios affect stages by increasing risk levels. The agent observes a 12-dimensional state vector and selects defensive actions. The environment models consequences (propagation, availability loss, integrity compromise) rather than real exploitation.

### 5. What is CTGAN and why did you use it?

CTGAN (Conditional Tabular GAN) is a generative adversarial network designed specifically for tabular data. It handles mixed continuous and discrete columns. We use it to generate synthetic attack-scenario features to augment the training data for the RL agent.

### 6. How do you validate synthetic data?

We compare synthetic data against real data using distribution similarity (KL divergence), statistical comparisons, correlation structure preservation, class balance assessment, diversity metrics, and range compliance checks.

### 7. What RL algorithm do you use?

DQN (Deep Q-Network) is our primary RL algorithm. We use the Stable-Baselines3 implementation. PPO is an optional secondary comparison.

### 8. What are your defensive actions?

Monitor (observe), Isolate (limit propagation), Block (prevent traffic), Rebuild (restore integrity), Recover (restore service). Each action has configurable costs.

### 9. How do you evaluate your system?

Three experimental conditions: (A) Rule-based baseline, (B) DQN without GAN augmentation, (C) DQN with GAN augmentation. We compare mitigation success, service availability, cumulative reward, and robustness across multiple random seeds.

### 10. What are the limitations?

CIC-IDS2017 is not a native supply-chain dataset, the supply-chain context is simulated, GAN outputs are synthetic features, RL is evaluated in a controlled environment, and results may not directly transfer to production systems.
