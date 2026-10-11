# Chapter 4: Calibrated Confidence and Probabilities

The defining feature separating TypeSafe Jev from generic LLM text generation is **Probability Calibration**. Understanding calibration allows software architects to build robust, automated routing policies with mathematical guarantees.

---

## 4.1 What Is Probability Calibration?

In standard generative LLMs, when a model claims `"I am 90% sure the answer is Python"`, that probability is rarely calibrated. Across a sample of 1,000 such statements, the model might only be right 60% of the time (overconfident) or 98% of the time (underconfident).

### Formal Definition of Calibration
A decision model is **perfectly calibrated** if, for all predictions made with probability $p$, the empirical accuracy equals $p$:

$$P(\text{Outcome} = 1 \mid \hat{P} = p) = p$$

```
Expected Calibration Error (ECE) Curve:
1.0 ┌───────────────────────────/ Perfect Calibration (y = x)
    │                         /
    │                       / • Calibrated Jev Predictions
    │                     /
    │                   / 
0.0 └─────────────────/───────────
    0.0                         1.0
          Predicted Probability
```

TypeSafe trains Jev using **Reinforcement Learning for Calibrated Decisions (RLCD)**, optimizing the loss function directly against true empirical distribution frequencies rather than human preference rewards (RLHF).

---

## 4.2 Confidence vs Probability

In Jev:
- **Probability** ($\mathbf{p} \in [0, 1]^K$): Represents the likelihood distribution assigned to each individual candidate choice or level.
- **Confidence** ($c \in [0, 1]$): Measures the certainty or **entropy** of the distribution. When one option dominates ($\mathbf{p} = [0.95, 0.03, 0.02]$), confidence is near $1.0$. When the model is torn between options ($\mathbf{p} = [0.49, 0.51]$), confidence drops near $0.0$.

---

## 4.3 Three-Tier Confidence Gating Policy

By mapping confidence scores into discrete execution policies, your application can safely automate decisions without human bottlenecking while preventing dangerous false positives.

```
       0.0                 0.50                 0.85                 1.0
Confidence: ├────────────────────┼────────────────────┼────────────────────┤
Action:     │     REVIEW TIER    │    CONFIRM TIER    │     AUTO TIER      │
            │  Escalate to Human │  Prompt User with  │ Autonomous Direct  │
            │  or Rule Fallback  │  Suggested Choice  │      Dispatch      │
```

### Python Implementation Pattern

```python
from enum import Enum

class ActionPolicy(str, Enum):
    AUTO = "auto"
    CONFIRM = "confirm"
    REVIEW = "review"

def determine_policy(confidence: float, auto_thresh: float = 0.85, review_thresh: float = 0.50) -> ActionPolicy:
    if confidence >= auto_thresh:
        return ActionPolicy.AUTO
    elif confidence >= review_thresh:
        return ActionPolicy.CONFIRM
    else:
        return ActionPolicy.REVIEW
```

---

## 4.4 Tuning Thresholds on Custom Domains

When deploying Jev in production:
1. **Run in Shadow Mode**: Log Jev choices and confidence scores alongside existing manual or regex workflows for 7–14 days.
2. **Compute Brier Scores & ECE**: Evaluate prediction accuracy across confidence bins ($[0.0-0.5]$, $[0.5-0.7]$, $[0.7-0.9]$, $[0.9-1.0]$).
3. **Set Thresholds by Action Risk**:
   - *Low-risk actions* (e.g., tagging a ticket): Set auto threshold to `0.70`.
   - *Destructive actions* (e.g., restarting a database cluster): Set auto threshold to `0.98` or require human signoff regardless.
