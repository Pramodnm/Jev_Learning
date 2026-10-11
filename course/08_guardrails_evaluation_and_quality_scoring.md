# Chapter 8: Guardrails, Evaluation, and Quality Scoring

A critical application of TypeSafe Jev in production is serving as a **bi-directional guardrail and quality evaluator** around LLM agent swarms.

---

## 8.1 Pre-Flight Safety & Command Guardrailing

Before an agent or user prompt reaches a code execution tool or shell, evaluate it with Jev for hazard probabilities.

### Command Risk Assessment Example

```python
command_state = {
    "proposed_command": "kubectl delete namespace production --grace-period=0 --force",
    "caller": "automated_remediation_agent",
    "cluster": "k8s-prod-primary"
}

questions = {
    "is_destructive": {
        "type": "noul",
        "instructions": "Will executing `proposed_command` permanently delete resources or data in `cluster`?"
    },
    "requires_human_mfa": {
        "type": "noul",
        "instructions": "Does this action violate automated remediation safety boundaries and require explicit admin approval?"
    }
}
```

If `is_destructive.noul >= 0.85`, the execution engine halts immediately and prompts for MFA authorization.

---

## 8.2 Post-Flight Quality Scoring & Hallucination Checks

After an LLM specialist generates code or an answer, Jev can score the output for completeness and factual adherence:

```python
verification_state = {
    "user_specification": "Implement a thread-safe singleton in Python with double-checked locking.",
    "agent_output": generated_code_string
}

questions = {
    "thread_safety_score": {
        "type": "score",
        "instructions": "Rate whether the code in `agent_output` correctly implements thread synchronization and thread safety.",
        "criteria": [
            "Lacks locks or has race conditions",
            "Partially synchronized but flawed",
            "Correct, robust thread-safe implementation"
        ]
    },
    "is_hallucinated_import": {
        "type": "noul",
        "instructions": "Does the generated code import non-existent modules or fictitious packages?"
    }
}
```

---

## 8.3 CI/CD Failure Triage & Flaky Test Detection

In DevOps pipelines, Jev can parse build logs to differentiate between flaky tests, network timeouts, and real code regressions:

```python
ci_log_state = {
    "pipeline_id": "ci-run-84920",
    "failed_step": "pytest tests/integration/",
    "log_tail": "ConnectionResetError: [Errno 104] Connection reset by peer while contacting redis-test-broker:6379"
}

questions = {
    "failure_category": {
        "type": "choice",
        "instructions": "Classify the root cause of the build failure from `log_tail`.",
        "criteria": {
            "flaky_infrastructure": "Transient network timeout, DNS glitch, or Docker socket drop",
            "code_assertion_failure": "Unit test assert failure or business logic error",
            "syntax_or_compilation": "Syntax error, missing package, or unhandled exception"
        }
    }
}
```

If `failure_category.choice == "flaky_infrastructure"` with `confidence >= 0.90`, GitHub Actions automatically triggers an immediate job re-run, saving developer time.
