# Research Gap

## Context

Software supply-chain attacks have become a significant cybersecurity threat. Incidents such as SolarWinds, Codecov, and various npm/PyPI package compromises demonstrate the potential impact of attacks targeting the software development and distribution pipeline.

## Prior Work

### GAN-Based Attack Data Augmentation
Recent research has explored the use of Generative Adversarial Networks (GANs) — including CTGAN, WGAN, and other variants — to augment cybersecurity datasets. These approaches address class imbalance and data scarcity in intrusion detection datasets, enabling better training of classification models.

### Reinforcement Learning for Cyber Defense
Separately, researchers have applied reinforcement learning techniques to adaptive cyber defense, including network defense, intrusion response, and automated mitigation. RL agents have shown promise in learning reactive defense policies that outperform static rule-based approaches in simulated environments.

### Software Supply-Chain Security
Supply-chain security research has focused on dependency analysis, SBOM (Software Bill of Materials), vulnerability propagation modeling, and trust framework design. However, experimental platforms that combine attack scenario generation with adaptive defense within supply-chain-specific environments remain limited.

## Identified Gap

> Recent research has separately advanced GAN-based attack-data augmentation and adaptive reinforcement-learning-based cyber defense. However, there is **limited experimental evaluation** of whether GAN-generated attack-scenario diversity can improve RL-based mitigation decisions within a **simulated software supply-chain dependency environment**.

## What This Project Contributes

This project provides an experimental platform to evaluate:

1. Whether CTGAN-generated synthetic attack scenarios provide meaningful diversity beyond the original dataset
2. Whether this diversity translates to improved RL-based defense performance
3. How adaptive RL defense compares to deterministic rule-based approaches

## Important Caveats

- We do NOT claim that "no one has ever done this."
- We acknowledge that related work exists in each individual area.
- Our contribution is the **integration and experimental evaluation** of these components within a supply-chain simulation context.
- Results are specific to our simulated environment and may not directly transfer to production systems.
