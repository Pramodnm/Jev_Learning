# Chapter 2: Core Primitives — Noul, Choice, and Score

The entire TypeSafe Jev API surface is built around **three mathematical question primitives**. Constraining decisions to these primitives eliminates schema drift and guarantees that responses can be parsed directly into typed application logic.

---

## 2.1 The Evaluation Endpoint Architecture

All Jev requests are sent to a single REST endpoint:
```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json
```
*(Or via OpenAI/OmniRouter compatibility gateways at `/v1/chat/completions` using the `questions` response format).*

### Top-Level Request Structure

```json
{
  "state": "<Text string, JSON object, or Array to evaluate>",
  "model": "jev-latest",
  "questions": {
    "question_id_1": { ... },
    "question_id_2": { ... }
  }
}
```

---

## 2.2 Primitive 1: Noul (Yes / No Probabilities)

### Concept & Etymology
A **Noul** evaluates a binary proposition against the state and returns a **calibrated probability** between `0.0` (definitive False) and `1.0` (definitive True).

### Schema Definition
```json
{
  "is_emergency": {
    "type": "noul",
    "instructions": "Does this alert describe an active or imminent production outage?",
    "criteria": {
      "true": "Critical services down or data loss occurring",
      "false": "Standard warning, transient blip, or informational notice"
    }
  }
}
```

### Response Shape
```json
{
  "answers": {
    "is_emergency": {
      "type": "noul",
      "noul": 0.985
    }
  }
}
```

### Key Rules for Noul:
- `noul` values near `0.5` represent **epistemic uncertainty** (insufficient evidence in state to confirm or deny).
- Noul questions do not return a separate `confidence` field because the probability itself encapsulates the belief distribution.

---

## 2.3 Primitive 2: Choice (Categorical 1-of-N Selection)

### Concept
A **Choice** question selects the single best-fitting option from a discrete set of up to **255 options**.

### Schema Definition
```json
{
  "target_agent": {
    "type": "choice",
    "instructions": "Which specialist agent should execute this user query?",
    "criteria": {
      "code_specialist": "Writing, reviewing, or debugging software code and algorithms",
      "devops_specialist": "Managing Kubernetes, Docker, CI/CD pipelines, and cloud infra",
      "data_specialist": "Writing SQL queries, data modeling, schema validation, statistics",
      "other": "General conversation or queries that do not fit the above domains"
    }
  }
}
```

### Response Shape
```json
{
  "answers": {
    "target_agent": {
      "type": "choice",
      "choice": "code_specialist",
      "confidence": 0.96,
      "probabilities": {
        "code_specialist": 0.96,
        "devops_specialist": 0.02,
        "data_specialist": 0.01,
        "other": 0.01
      }
    }
  }
}
```

### Best Practices for Choice:
1. **Always Include an `"other"` Option**: Because Jev is forced to select an option, providing an `"other"` or `"unclear"` key prevents false positives on out-of-domain input.
2. **Write Descriptive Rubrics in Criteria**: The keys are identifiers; the criteria values tell Jev when the key applies.

---

## 2.4 Primitive 3: Score (Continuous Ordinal Rating)

### Concept
A **Score** question places the input state along an ordered rubric scale of **2 to 10 descriptive levels**. 

Unlike naive integer classifiers, Jev returns a **probability-weighted continuous average** across the levels, allowing fine-grained thresholding (e.g., a score of `1.72` on a 0–3 scale).

### Schema Definition
```json
{
  "complexity_rating": {
    "type": "score",
    "instructions": "Rate the technical complexity of the proposed task.",
    "criteria": [
      "Level 0: One-liner, trivial syntax fix, or direct factual lookup",
      "Level 1: Moderate coding task requiring single-file refactor or script",
      "Level 2: Major architectural refactor spanning multiple services and databases"
    ]
  }
}
```

### Response Shape
```json
{
  "answers": {
    "complexity_rating": {
      "type": "score",
      "score": 1.82,
      "confidence": 0.89,
      "legend": {
        "0": "Level 0: One-liner, trivial syntax fix, or direct factual lookup",
        "1": "Level 1: Moderate coding task requiring single-file refactor or script",
        "2": "Level 2: Major architectural refactor spanning multiple services and databases"
      },
      "probabilities": {
        "0": 0.02,
        "1": 0.14,
        "2": 0.84
      }
    }
  }
}
```

---

## 2.5 Summary Table: Primitives Comparison

| Primitive | Mathematical Type | Output Value | Range | Confidence Field? | Ideal Use Cases |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Noul** | Bernoulli Probability | `noul` (float) | `0.0` to `1.0` | No (embedded) | Safety checks, gatekeeping, bug confirmation |
| **Choice** | Categorical Distribution | `choice` (str), `probs` (map) | Discrete keys | Yes (`0.0`–`1.0`) | Agent routing, intent classification, triage |
| **Score** | Continuous Expectation | `score` (float), `legend` | `0.0` to `N-1` | Yes (`0.0`–`1.0`) | Priority ranking, complexity, quality review |
