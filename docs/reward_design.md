# Reward Function Design

## Overview

The reward function guides the DQN agent's behavior by providing feedback after each action in the supply-chain environment. A well-designed reward must balance competing objectives.

## Reward Formula

```
R = w_mitigation * mitigation_bonus
  + w_containment * containment_reward
  + w_availability * availability_reward
  - w_impact * attack_impact_penalty
  - w_cost * action_cost_penalty
  - w_delay * response_delay_penalty
  - w_unnecessary * unnecessary_action_penalty
```

## Component Breakdown

### Positive Rewards

| Component | Description | Rationale |
|-----------|-------------|-----------|
| Mitigation bonus | Large reward when attack is fully mitigated | Primary objective — resolve the incident |
| Containment reward | Reward for limiting attack propagation | Preventing spread is critical even before full mitigation |
| Availability reward | Reward proportional to service availability | Maintaining service is an operational priority |

### Negative Rewards (Penalties)

| Component | Description | Rationale |
|-----------|-------------|-----------|
| Attack impact | Penalty proportional to stages affected | Failure to contain has real consequences |
| Action cost | Penalty for expensive actions | More aggressive actions have higher operational cost |
| Response delay | Small per-step penalty | Encourages timely response, discourages passive monitoring during attacks |
| Unnecessary action | Penalty for aggressive action when risk is low | Prevents over-reactive behavior (e.g., blocking when only monitoring is needed) |

## Configuration

All weights and magnitudes are stored in `config/dqn.yaml` under the `reward` section.

### Default Weights

```yaml
reward:
  weights:
    mitigation: 1.0
    containment: 0.3
    availability: 0.4
    impact: -0.5
    cost: -0.2
    delay: -0.1
    unnecessary: -0.3
```

### Action Costs

| Action | Cost | Justification |
|--------|------|---------------|
| Monitor | 0.01 | Minimal overhead — passive observation |
| Isolate | 0.15 | Moderate — restricts communication |
| Block | 0.25 | Higher — prevents all traffic to/from stage |
| Rebuild | 0.35 | Highest — requires full stage reconstruction |
| Recover | 0.20 | Moderate — restores service after mitigation |

## Design Decisions

1. **Mitigation has the highest weight** because the primary goal is to resolve attacks.
2. **Action costs are relatively low** compared to impact penalties to avoid overly passive behavior.
3. **The step penalty is small** to allow some deliberation without indefinite monitoring.
4. **Unnecessary action penalty targets over-reaction**, specifically aggressive actions when risk is below the suspicious threshold.

## Verification

Reward behavior is verified via unit tests in `tests/unit/test_reward.py` that confirm:
- Correct mitigation receives positive reward
- Attack impact produces negative reward
- Unnecessary aggressive actions are penalized
- Total reward is bounded and reasonable
