# Chapter 5: Architectural Patterns for Agentic Development

When architecting AI agent systems, Jev unlocks five core architectural design patterns that drastically outperform traditional monolithic LLM loops.

---

## 5.1 Pattern 1: Speculative Fan-Out (Parallel Multi-Question Evaluation)

### The Problem
In standard agent loops, deciding the next step requires multiple sequential LLM calls:
1. Is the prompt safe? (Call 1: 1.5s)
2. What domain is it? (Call 2: 1.5s)
3. Is human approval needed? (Call 3: 1.5s)
Total routing latency: **4.5 seconds**.

### The Jev Solution
Because Jev evaluates all questions in parallel over a single ingested state in a single non-autoregressive pass, adding 5 or 10 questions adds virtually zero latency:

```
                  ┌─ Question 1 (Safety Noul) ──> p=0.01
                  ├─ Question 2 (Specialist Choice) ─> "code_agent" (conf=0.95)
State ──> Jev ───┼─ Question 3 (Complexity Score) ─> score=1.8 (conf=0.90)
                  └─ Question 4 (Requires DB Migration) ─> p=0.99
                       │
             Single Pass: ~120 ms!
```

---

## 5.2 Pattern 2: Intent Routing & Dispatch

Classify incoming queries or events into dedicated specialist handlers: deterministic code, serverless workers, specialized microservices, or specific LLM agents.

```python
questions = {
    "route": {
        "type": "choice",
        "instructions": "Which specialized handler should process this request?",
        "criteria": {
            "fast_deterministic_sql": "Standard metric lookup or user balance query",
            "gemini_code_specialist": "Complex multi-file refactoring or algorithm design",
            "human_support_queue": "Billing refunds, chargebacks, account disputes"
        }
    }
}
```

---

## 5.3 Pattern 3: Two-Stage SDE Cascade (Structured Decision & Execution)

The **Structured Decision & Execution (SDE) Cascade** combines the sub-second speed and calibrated precision of System One with the deep analytical reasoning of System Two:

```
User Query
    │
    ▼
[Stage 1: Jev System One] ─── (70-300ms) ───► Decision Matrix
                                                • Target Specialist: CodeAgent
                                                • Safety Check: Safe (0.01)
                                                • Complexity: High (2.0)
    │
    ▼
[Stage 2: Gemini 3.7 Flash] ─── (Reasoning & Tools) ───► Generates Implementation
    │
    ▼
[Stage 3: Jev Quality Gate] ─── (100ms Verification) ──► Validated Production Output
```

---

## 5.4 Pattern 4: Composite Scoring & Weighted Matrices

Complex business judgments should not be collapsed into a single vague score. Instead, decompose the judgment into atomic Score and Noul questions, then compute a weighted composite index in deterministic Python code:

$$\text{Composite Score} = w_1 \cdot \text{Readability} + w_2 \cdot \text{Correctness} + w_3 \cdot \text{Security}$$

This keeps the scoring weights transparent, configurable, and auditable.
