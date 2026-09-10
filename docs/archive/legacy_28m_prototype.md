# ARCHIVED: Legacy 28M Nano Prototype & From-Scratch Monolithic Hypothesis
> **Archive Date**: 2026-09-06  
> **Status**: DEPRECATED & ARCHIVED  
> **Superseded By**: Dual-Tier Product Architecture (**Flash 135M** + **Pro 0.5B**)

---

## 1. Archived Hypothesis Summary
In the initial experimental phase of Wrench-SLM, an exploratory hypothesis proposed training a single monolithic ~25M-28M parameter Transformer from scratch with zero pretraining and zero external base weights.

## 2. Why This Design Was Deprecated
1. **Severe Under-Capacity**: At 25M-28M parameters, the model lacked the representational capacity for natural language intent understanding, slot filling, and syntax flexibility.
2. **Rote Overfitting & Punctuation Hallucination**: The model collapsed into rote memorization of exact training strings. On slight phrasing variations, it exhibited punctuation concatenation errors (`{"args}}{"cmd}}`), requiring heavy FSM crutches to be usable.
3. **No Hardware Segmentation**: A single 28M model neither satisfied high-performance GPU workstation needs nor targeted low-power 24/7 hardware appliances like Raspberry Pi.

## 3. The New Product Baseline
All new development and training strictly follow the **Dual-Tier Speculative Tool Execution Architecture**:
* **Flash Version (135M)**: Low-power CPU / Raspberry Pi 4/5 24/7 hardware gateway (< 85MB INT4, < 180MB RAM, 35ms-50ms latency, 5W power).
* **Pro Version (0.5B)**: Workstation / RTX 5070 Ti GPU powerhouse (~1.0GB BF16, 12ms-15ms latency, deep slot-filling and multi-tool orchestration).
