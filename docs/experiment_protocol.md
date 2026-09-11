# Experiment Protocol

## Not yet executed.

Experiments will be documented here once they are run. This file defines the protocol.

## Experimental Conditions

| ID | Name | Model | Training Data | Description |
|----|------|-------|---------------|-------------|
| A | Rule-Based Baseline | rule_based | N/A | Deterministic rules |
| B | DQN without GAN | dqn | Real only | DQN on original scenarios |
| C | DQN with GAN | dqn_gan | Real + Synthetic | DQN on augmented scenarios |
| D | PPO Comparison | ppo | Real + Synthetic | Optional comparison |

## Evaluation Protocol

1. Train models on training scenarios
2. Evaluate all models on the SAME held-out test scenarios
3. Use multiple random seeds (42, 123, 456, 789, 1024)
4. Report mean ± standard deviation for all metrics
5. Generate comparison tables and charts

## Metrics

See `config/evaluation.yaml` for the complete metrics list.

## Results

*Not evaluated yet.*
