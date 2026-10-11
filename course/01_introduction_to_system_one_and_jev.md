# Chapter 1: Introduction to System One Models & TypeSafe Jev

## 1.1 The Cognitive Duality: System 1 vs System 2 in AI

In Daniel Kahneman’s landmark cognitive treatise *Thinking, Fast and Slow*, human cognition is bifurcated into two modes of thought:

```
┌────────────────────────────────────────────────────────┐
│                   HUMAN COGNITION                      │
├────────────────────────────┬───────────────────────────┤
│          SYSTEM 1          │          SYSTEM 2         │
│  Fast, Instinctive, Direct │ Slow, Deliberate, Logical │
│  "Is this an emergency?"   │ "Solve 348 * 29 Step-by-Step" │
└────────────────────────────┴───────────────────────────┘
```

For the first decade of the LLM revolution (2017–2025), artificial intelligence was dominated almost entirely by **System Two-style architectures**: autoregressive transformer decoders that generate answers token by token. 

While ideal for essay generation, complex mathematics, and multi-step reasoning, using a generative LLM for simple routing or categorization is an anti-pattern:
- **Autoregressive Overhead**: Generating `"category": "billing"` requires generating syntax tokens (`{`, `"`, `c`, `a`, `t`, ...), taking 500–2000 ms.
- **Hallucination Risk**: Free-form decoders can output invalid categories or fail JSON validation.
- **Token Tax**: Output tokens cost 3x to 5x more than input tokens on major frontier providers.

**System One Models** are designed specifically to perform fast, non-generative, typed probabilistic evaluations directly over structured or unstructured state.

---

## 1.2 Who Created Jev? Background & History

**Jev** is the flagship System One decision model created by **TypeSafe AI**, founded in 2024 by:
- **Diogo Almeida**: Former OpenAI technical lead who worked on RLHF, InstructGPT, and ChatGPT.
- **Erik Gafni** & **Sasha Sheng**: Systems and machine learning engineers.

TypeSafe AI emerged from stealth in September 2026 backed by a $40M seed round led by DCVC. 

### Why is it Named Jev?
The model is named after **William Stanley Jevons**, the 19th-century economist who formulated the **Jevons Paradox**: *as technological progress increases the efficiency with which a resource is used, the rate of consumption of that resource rises.*

When decision intelligence drops from $0.05 / call (and 2 seconds) to **$0.00004 / call (and 80 milliseconds)**, developers begin placing AI decision gates in every loop, microservice, webhook, and routing table.

---

## 1.3 Technical Specifications: Jev 1.13 at a Glance

| Specification | Jev 1.13 Parameter | Comparison with Frontier Chat LLMs |
| :--- | :--- | :--- |
| **Primary Function** | Typed Decisions (Noul, Choice, Score) | Free-form Text / Code Generation |
| **Output Type** | Calibrated Probabilities & JSON Enums | Autoregressive Token Stream |
| **Type Error Rate** | **0.0% (Structural Guarantee)** | 0.5% – 5.0% (JSON Parsing Failures) |
| **Input Pricing** | **$0.042 per Million Tokens** | $2.50 – $15.00 per Million Tokens |
| **Output Pricing** | **$0.00 (Free / Unmetered)** | $10.00 – $60.00 per Million Tokens |
| **Latency** | **70 ms – 500 ms** | 1,500 ms – 8,000 ms |
| **Context Window** | 64k Tokens (State + Questions) | 128k – 1M Tokens |
| **Max Choice Options**| 255 discrete options | Open-ended |

---

## 1.4 What Jev Does NOT Do (Boundaries)

Understanding Jev's boundaries prevents architectural misuse:
1. **No Free-Form Generation**: Jev cannot write essays, summarize articles in prose, or draft email replies.
2. **No Code Synthesis**: Jev will not write Python or TypeScript code; it selects choices and rates code snippets.
3. **No Tool Execution Loops**: Jev does not call HTTP tools or interact with databases; it outputs routing instructions for host applications.
4. **No Multimodal Inputs**: Current versions evaluate text and JSON structures only.

---

## 1.5 Summary

Jev is the dedicated decision router of modern software. In the next chapter, we dive deep into the three mathematical primitives that govern every Jev interaction: **Noul**, **Choice**, and **Score**.
