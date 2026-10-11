# TypeSafe Jev & System One Decision Models: Zero to Hero Master Course

Welcome to the definitive, chapter-wise guide on **TypeSafe Jev** and **System One Decision Models** in modern agentic architectures.

---

## 🧭 Course Vision & Philosophy

Most artificial intelligence in 2026 relies on **System Two** generative Large Language Models (LLMs). When software needs to decide which queue an alert belongs to, whether a command is safe, or which specialist agent should handle a query, teams have routinely invoked heavy reasoning models. 

This practice introduces three major liabilities:
1. **Unpredictable Latency**: Autoregressive token-by-token generation adds seconds to critical control loops.
2. **Schema Instability & Hallucination**: Generative models can emit malformed JSON or invalid enum values.
3. **High Operational Cost**: Output tokens are heavily metered, making high-volume triage expensive.

**TypeSafe Jev** represents a paradigm shift: the first dedicated **System One Decision Model**. Jev does not chat, write essays, or invent code. Instead, it acts as a **smart `if` statement**—evaluating unstructured state against typed questions and returning **calibrated probabilities and discrete choices in 70–500 milliseconds at $0.042 per million input tokens with free output**.

---

## 📚 Curriculum Structure

```
course/
├── 00_course_overview.md                         <- [You are here] Syllabus & Curriculum Map
├── 01_introduction_to_system_one_and_jev.md      <- Novice: Cognitive Theory, System 1 vs 2, Background
├── 02_core_primitives_noul_choice_score.md       <- Novice: Noul, Choice, Score APIs & Schemas
├── 03_structuring_state_and_questions.md         <- Intermediate: Context Design & Field Referencing
├── 04_calibrated_confidence_and_probability.md   <- Intermediate: RLCD, Entropy, Confidence Gating
├── 05_architectural_patterns_for_agents.md       <- Intermediate: Speculative Fan-out, Cascades
├── 06_multi_agent_orchestration_with_jev_and_gemini.md <- Advanced: Hybrid Multi-Agent Systems
├── 07_google_adk_and_openapi_integration.md      <- Advanced: OpenAPI Tool Schemas & Function Calling
├── 08_guardrails_evaluation_and_quality_scoring.md <- Advanced: Safety Filters, Citation Checks, CI Triage
├── 09_production_deployment_monitoring_and_optimization.md <- Expert: Benchmarking, Cost, Telemetry
└── 10_expert_case_studies_and_capstone.md        <- Expert: Production DevOps, FinTech, & Capstone
```

---

## 🎯 Target Audience & Prerequisites

- **AI Engineers & Architects**: Designing resilient multi-agent swarms and high-throughput routing pipelines.
- **DevOps & SRE Specialists**: Automating alert triage, CI/CD remediation, and command guardrails.
- **Backend Developers**: Integrating structured decision models into FastAPI, Node.js, or Go microservices.
- **Prerequisites**: Basic understanding of Python 3.10+, REST APIs, and asynchronous programming.

---

## 🚀 Key Takeaways
By completing this course and exploring the accompanying codebase in this repository, you will master:
- Configuring confidence thresholds to split autonomous execution from human oversight.
- Slashing multi-agent routing costs by 90%+ while dropping decision latencies to sub-second speeds.
- Building full-stack production systems using Jev as the router and Google Gemini 3.7 Flash as the specialist execution engine.
