# Chapter 3: Structuring State and Questions

The quality and calibration of Jev's decisions depend on how you format the **State** and write the **Question Instructions & Criteria**.

---

## 3.1 State Representation Patterns

Jev accepts state in three formats:
1. **Plain Text String**: For raw prompts, logs, or single paragraphs.
2. **JSON Object**: For structured records, alerts, pull requests, and telemetry.
3. **Array of Text/Objects**: For lists of events, comments, or diff chunks.

### Best Practice: Send Structured JSON Records

When evaluating real-world system data, pass structured dictionaries rather than concatenated strings:

```json
{
  "state": {
    "service": "payments-api",
    "cluster": "prod-us-east-1",
    "http_5xx_rate": 0.142,
    "p99_latency_ms": 3200,
    "recent_deploy_commit": "a8f902c",
    "error_log_sample": "ConnectionPoolExhausted: Unable to checkout database connection within 5000ms"
  }
}
```

---

## 3.2 Backtick Field Referencing

When state is a JSON object, you can reference specific nested fields directly inside your question instructions or criteria using backticks (`` `path.to.field` ``).

### Example: Pinpointing Ambiguity
```json
{
  "questions": {
    "is_db_bottleneck": {
      "type": "noul",
      "instructions": "Does the error described in `error_log_sample` originate from the database tier rather than upstream client traffic?"
    },
    "deploy_correlation": {
      "type": "noul",
      "instructions": "Was this incident triggered immediately after the release of commit `recent_deploy_commit`?"
    }
  }
}
```

By referencing `` `error_log_sample` ``, Jev isolates its evaluation to that specific field, avoiding context confusion when the state contains multiple log lines.

---

## 3.3 Structuring Question Instructions & Criteria

### 1. Concrete Descriptions over Abstract Labels
When defining Choice criteria or Score levels, **describe the situation, not the adjective**.

❌ **Poor Criteria Design**:
```json
"criteria": {
  "critical": "Very bad issue",
  "major": "Bad issue",
  "minor": "Not so bad"
}
```

✅ **Calibrated Criteria Design**:
```json
"criteria": {
  "critical": "Customer checkout or login is completely non-functional; active revenue loss occurring",
  "major": "Non-critical feature is failing (e.g. avatar upload); core checkout flow remains operational",
  "minor": "Cosmetic or minor UI rendering defect with an obvious workaround"
}
```

### 2. Using Structured Objects inside Instructions
Instructions themselves can be JSON objects when referencing reference baselines:

```json
{
  "instructions": {
    "baseline_sla": "P99 latency must stay below 500ms and 5xx rate below 1%",
    "evaluation_task": "Does the current metric state violate `baseline_sla`?"
  }
}
```

---

## 3.4 What to Keep in Code vs What to Send to Jev

TypeSafe documents that Jev is a **System One intuitive decision model** and should not be expected to perform exact deterministic arithmetic, calendar math, or regular expression matching.

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│           KEEP IN CODE (PYTHON)       │            DELEGATE TO JEV            │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ Exact date/time calculations          │ Semantic urgency assessment           │
│ Integer arithmetic & counting         │ Complex failure categorization        │
│ Regex / token matching                │ Ambiguous intent routing              │
│ Strict schema enforcement             │ Quality & safety scoring              │
└───────────────────────────────────────┴───────────────────────────────────────┘
```
