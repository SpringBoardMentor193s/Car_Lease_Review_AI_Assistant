# Fairness Engine — System Architecture

## 1. Purpose

The Fairness Engine is a backend subsystem designed to evaluate car lease and loan contracts and produce a quantitative, explainable **Contract Fairness Score**. Its goal is to transform unstructured legal/financial contract documents into structured risk-normalized fairness assessments suitable for consumer decision support and negotiation assistance.

This system is designed to be:

- Deterministic and explainable
- Schema-driven and auditable
- Market-calibrated and configurable
- Extensible without business logic rewrites
- Suitable for regulated financial environments

---

## 2. High-Level Architecture

    
         Contract PDF/Image
                  ↓
               OCR Layer
                  ↓
           LLM Extraction
                  ↓
       ContractFacts (Validated JSON)
                  ↓
        Fairness Scoring Engine
                  ↓
     FairnessReport (Structured Output)
                  ↓
        API / Frontend / Analytics


The system cleanly separates:

- **Fact extraction** from documents
- **Fairness evaluation** logic
- **Market calibration data**
- **External interfaces**

This separation ensures robustness, testability, and regulatory explainability.

---

## 3. Core Design Principles

### 3.1 Schema-First Architecture

All domain data contracts are defined using **Pydantic models** and auto-generated JSON Schemas. This ensures:

- Strong validation at system boundaries
- Zero schema drift between backend and clients
- Machine-verifiable data integrity

Schemas are treated as *artifacts*, not sources of truth.

---

### 3.2 Configuration-Driven Scoring Logic

Fairness evaluation logic is not hardcoded in Python. Instead:

- All scoring logic is declared in versioned configuration files
- Business policy changes require no redeploy
- Rule weights, penalty factors, and scoring methods are externally configurable

This enables regulatory tuning, market adaptation, and A/B testing.

---

### 3.3 Market-Normalized Scoring

All numeric contract values are evaluated relative to **market benchmark distributions** (mean, std, bounds). This ensures:

- Scores are comparable across time, markets, and vehicles
- Extreme values are penalized smoothly, not abruptly
- Fairness judgments reflect real-world expectations

---

### 3.4 Explainability by Construction

Every score produced by the engine must:

- Map to a specific contract clause
- Be traceable to a benchmark and rule
- Produce a natural-language explanation

This ensures auditability and consumer trust.

---

### 3.5 Versioned Contracts and Backward Compatibility

Schemas and scoring configurations are versioned to guarantee:

- Stable historical behavior
- Safe rule evolution
- Reproducibility of past decisions

---

## 4. Module Architecture

           fairness_scoring_engine/
             │
             ├── models/ ← Source of truth (Pydantic)
             │ ├── contract_facts.py ← Contract input model
             │ ├── scoring_rules.py ← Rule configuration model
             │ └── fairness_report.py ← Output model
             │
             ├── schemas/ ← Auto-generated artifacts (DO NOT EDIT)
             │ ├── contract_facts.schema.json
             │ ├── scoring_rules.schema.json
             │ └── fairness_report.schema.json
             │
             ├── data/ ← Runtime configuration (editable)
             │ ├── market_benchmarks.json
             │ └── scoring_rules.json
             │
             ├── engine/ ← Core computation logic
             │   └── scorer.py ← Rule evaluation engine
             │              
             ├── pipelines/ ← End-to-end orchestration
             │ ├── extract_pipeline.py ← OCR → LLM → ContractFacts
             │ ├── scoring_pipeline.py ← ContractFacts → FairnessReport
             │ └── comparison_pipeline.py ← Multi-contract comparison
             │
             ├── api/ ← Integration layer
             │ ├── routes.py ← FastAPI endpoints
             │ ├── dependencies.py
             │ └── schemas.py ← Request/response bindings
             │
             ├── versions/ ← Backward-compatible snapshots
             │ └── v1/
             │ ├── schemas/
             │ └── data/
             │
             ├── scripts/ ← Tooling and automation
             │ └── generate_schemas.py
             │
             ├── tests/     
             │
             ├── config/
             │
             └── docs/
             └── architecture.md

---

## 5. Layer Responsibilities

### 5.1 `models/` — Domain Contracts (Source of Truth)

Defines all structured data using **Pydantic**:

- `ContractFacts`: Extracted contract terms
- `ScoringRules`: Declarative scoring logic
- `FairnessReport`: Engine output

These models generate both runtime validation and JSON schemas.

---

### 5.2 `schemas/` — Generated Artifacts

Contains auto-generated JSON Schemas derived from Pydantic models.

These are:

- Used for LLM output validation
- Exposed to frontend clients
- Versioned for backward compatibility

Never manually edited.

---

### 5.3 `data/` — Market Truth + Business Policy

Contains runtime-editable configuration:

- Market benchmark distributions
- Rule weightings and scoring parameters

These files allow system behavior to change without code redeployment.

---

### 5.4 `engine/` — Fairness Computation Core

Implements:

- Numeric normalization (z-score, percentile, threshold)
- Categorical rule evaluation
- Risk penalty logic
- Score aggregation
- Red-flag detection

This layer contains **no domain constants**, only computation mechanics.

---

### 5.5 `pipelines/` — Orchestration Layer

Coordinates multi-stage workflows:

- OCR → LLM → Schema validation
- Fact extraction → Fairness scoring
- Multi-offer comparison and ranking

Ensures deterministic, testable processing.

---

### 5.6 `api/` — External Interface

Exposes system functionality via FastAPI:

- Contract upload
- Fairness scoring
- Report retrieval
- Comparison endpoints

Auto-generates OpenAPI documentation.

---

### 5.7 `versions/` — Backward Compatibility

Stores immutable snapshots of:

- Schema versions
- Benchmark datasets
- Rule configurations

Ensures reproducibility and regulatory traceability.

---

## 6. Data Flow

### 6.1 Contract Processing

     PDF → OCR → Text → LLM → ContractFacts (validated)

Invalid or incomplete extraction fails fast.

---

### 6.2 Fairness Evaluation

     ContractFacts + MarketBenchmarks + ScoringRules
                              ↓
                   Fairness Scoring Engine
                              ↓
                        FairnessReport


Each output score is explainable and auditable.

---

## 7. Explainability Strategy

For every fairness sub-score, the engine records:

- Input value
- Benchmark reference
- Rule applied
- Score contribution
- Natural-language explanation

This enables:

- User-facing trust explanations
- Debugging
- Regulatory audit trails

---

## 8. Extensibility Strategy

New fairness dimensions can be added by:

1. Adding field to `ContractFacts`
2. Updating benchmark dataset
3. Adding rule in `scoring_rules.json`

No scoring engine code changes required.

---

## 9. Reliability & Safety

- All inputs are schema-validated
- All scoring logic is deterministic
- All configuration is versioned
- All outputs are reproducible

This design supports regulated consumer finance environments.

---

## 10. Why This Architecture

This system is intentionally designed closer to **financial risk engines** than typical AI pipelines:

- Rules + benchmarks + deterministic scoring
- LLM used only for extraction, not judgment
- Strong separation between policy and execution
- Full explainability and auditability

This enables:

- Trustworthy consumer-facing recommendations
- Safe negotiation assistance
- Regulatory review readiness
- Long-term maintainability

---

## 11. Summary

The Fairness Engine implements a **schema-first, configuration-driven, explainable inference system** that transforms unstructured legal contracts into auditable financial fairness assessments.

It is designed for:

- Production-grade robustness
- Regulatory compatibility
- Market adaptability
- Long-term system evolution

This architecture enables both rapid prototyping and enterprise-grade deployment without redesign.

---
