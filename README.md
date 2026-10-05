# 🚀 NVIDIA SCD-SHIELD

### Autonomous Supercomputer Cluster Diagnostics & Self-Healing Reliability Engine

> **SCD-SHIELD** is an AI-assisted diagnostic and governed remediation platform designed for autonomous supercomputer cluster reliability. It analyzes cluster incidents, generates structured root-cause hypotheses, evaluates evidence, and controls remediation actions through a governance layer.

---

## 📌 Overview

Modern supercomputer and GPU clusters can experience complex failures involving:

- GPU communication failures
- Interconnect degradation
- Hardware faults
- Node failures
- Thermal anomalies
- Performance degradation
- Cluster-level reliability issues

**SCD-SHIELD** provides a structured pipeline for diagnosing these incidents using LLM-assisted reasoning while maintaining a strict boundary between **AI recommendations** and **operational execution**.

The system combines:

- Incident ingestion
- Context construction
- Prompt engineering
- LLM-based diagnostics
- Structured output parsing
- Failure classification
- Evidence analysis
- Governance decisions
- Controlled remediation
- Automated testing
- API-based access

---

# ✨ Key Features

### 🧠 AI-Assisted Diagnostics

Uses an LLM adapter architecture to generate structured diagnostic reasoning from cluster incidents.

### 🔍 Root-Cause Analysis

Produces:

- Failure family
- Affected entity
- Primary hypothesis
- Supporting evidence
- Contradicting evidence
- Recommended mitigation

### 🛡️ Governance Layer

AI-generated recommendations are evaluated before any remediation action.

Possible governance decisions:

```text
APPROVE
REVIEW
REJECT
```

### ⚙️ Controlled Remediation

Approved actions can be passed to the repair execution layer.

Rejected actions are blocked.

Actions requiring additional validation can be routed for human review.

### 🧪 Strong Testing

The project includes:

- Unit tests
- Integration tests
- Adversarial tests
- Property-based tests
- API validation tests
- Error-handling tests
- Governance tests

### 📡 REST API

Built with **FastAPI** and automatically documented using OpenAPI / Swagger.

### 📝 Prompt Versioning

Prompts are maintained as versioned files:

```text
prompts/
├── v1/
└── v2_challenger/
```

### 🔌 LLM Adapter Architecture

The diagnostic layer uses an adapter pattern so the underlying LLM implementation can be replaced without changing the rest of the application.

---

# 🏗️ System Architecture

```text
                     ┌─────────────────────┐
                     │      Incident       │
                     │       Input         │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │     FastAPI API     │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ Diagnostic Service  │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   Context Builder   │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │    Prompt System    │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │     LLM Adapter     │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   Output Parser     │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ Diagnostic Result   │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ Governance / CPTP   │
                     └──────────┬──────────┘
                                │
                   ┌────────────┼────────────┐
                   │            │            │
                   ▼            ▼            ▼
              ┌─────────┐ ┌─────────┐ ┌─────────┐
              │ APPROVE │ │ REVIEW  │ │ REJECT  │
              └────┬────┘ └────┬────┘ └────┬────┘
                   │            │            │
                   ▼            ▼            ▼
              ┌─────────┐ ┌─────────┐ ┌─────────┐
              │ Repair  │ │ Human   │ │ Block   │
              │Executor │ │ Review  │ │ Action  │
              └─────────┘ └─────────┘ └─────────┘
```

---

# 📂 Project Structure

```text
SCD-shield-platform/
│
├── services/
│   ├── __init__.py
│   │
│   └── api/
│       ├── __init__.py
│       └── app.py
│
├── shield/
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── settings.py
│   │
│   ├── context/
│   │   ├── __init__.py
│   │   └── builder.py
│   │
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── cptp.py
│   │   └── repair_executor.py
│   │
│   ├── governance/
│   │   ├── __init__.py
│   │   └── decision.py
│   │
│   ├── ingress/
│   │   ├── __init__.py
│   │   ├── diagnostic_service.py
│   │   ├── llm_adapter.py
│   │   ├── llm_factory.py
│   │   ├── openai_adapter.py
│   │   ├── output_parser.py
│   │   ├── prompt_registry.py
│   │   ├── prompt_renderer.py
│   │   ├── repair.py
│   │   └── schemas.py
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── retriever.py
│   │   └── store.py
│   │
│   └── tools/
│       └── __init__.py
│
├── prompts/
│   ├── v1/
│   │   ├── developer.md
│   │   ├── diagnostic_system.md
│   │   ├── system.md
│   │   └── user.md
│   │
│   └── v2_challenger/
│       ├── developer.md
│       ├── diagnostic_system.md
│       ├── system.md
│       └── user.md
│
├── tests/
│   ├── __init__.py
│   │
│   ├── unit/
│   │   ├── test_context_builder.py
│   │   ├── test_cptp.py
│   │   ├── test_decision.py
│   │   ├── test_diagnostic_service.py
│   │   ├── test_ingress_schemas.py
│   │   ├── test_llm_adapter.py
│   │   ├── test_llm_factory.py
│   │   ├── test_logging.py
│   │   ├── test_openai_adapter.py
│   │   ├── test_orchestrator.py
│   │   ├── test_output_parser.py
│   │   ├── test_prompt_registry.py
│   │   ├── test_prompt_renderer.py
│   │   ├── test_repair.py
│   │   ├── test_repair_executor.py
│   │   ├── test_retriever.py
│   │   └── test_settings.py
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_diagnostic_api.py
│   │
│   ├── adversarial/
│   │   └── test_governance_safety.py
│   │
│   └── property/
│       └── test_cptp_properties.py
│
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

# 🔄 Diagnostic Workflow

The main diagnostic pipeline follows this flow:

```text
Incident
   ↓
Schema Validation
   ↓
Context Construction
   ↓
Prompt Rendering
   ↓
LLM Diagnostic Request
   ↓
Structured Output Parsing
   ↓
Diagnostic Validation
   ↓
Governance Evaluation
   ↓
Action Decision
   ↓
Controlled Execution
```

This separation keeps diagnostic reasoning independent from operational execution.

---

# 📡 API

## Health Check

```http
GET /health
```

Returns the service health and metadata.

---

## Diagnostic Endpoint

```http
POST /diagnose
```

Analyzes a supercomputer cluster incident.

---

## Diagnostic Workflow

```http
POST /diagnose/workflow
```

Runs the complete diagnostic and governance workflow.

---

# 🧪 Example Incident

```json
{
  "incident_id": "INC-999",
  "timestamp": "2026-10-05T12:00:00Z",
  "node_id": "node-test",
  "incident_type": "hardware",
  "severity": "critical",
  "description": "Test GPU communication failure",
  "telemetry": {
    "link_errors": 99,
    "temperature_c": 82,
    "gpu_utilization": 95
  },
  "metadata": {
    "cluster": "test-cluster",
    "gpu_type": "H100"
  }
}
```

---

# 📤 Example Diagnostic Response

The diagnostic system produces structured information such as:

```json
{
  "incident_id": "INC-999",
  "failure_family": "interconnect",
  "affected_entity": "node-a",
  "primary_hypothesis": "GPU communication degradation",
  "supporting_evidence": [
    "High link error count",
    "Elevated GPU utilization"
  ],
  "contradicting_evidence": [],
  "recommended_action": "Collect link health counters",
  "confidence": 0.82
}
```

---

# 🛡️ Governance

SCD-SHIELD intentionally separates **diagnosis** from **execution**.

The LLM can recommend an action, but the recommendation is not automatically treated as safe.

The governance layer evaluates the action.

## Governance Outcomes

### APPROVE

The proposed action satisfies the governance conditions and may proceed to controlled execution.

### REVIEW

The action requires additional human validation before execution.

### REJECT

The action violates governance constraints or is considered unsafe.

```text
                Diagnostic
                     │
                     ▼
              Governance Layer
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       APPROVE     REVIEW     REJECT
          │          │          │
          ▼          ▼          ▼
       Execute     Human      Block
                   Review     Action
```

---

# ⚙️ CPTP

The project contains a governance / controlled-transition component referred to as **CPTP**.

Its purpose is to enforce controlled transitions between diagnostic reasoning and operational actions.

The implementation is tested through both normal and adversarial scenarios.

---

# 🤖 LLM Integration

The project provides an adapter-based LLM architecture.

```text
LLMRequest
    │
    ▼
LLMAdapter
    │
    ├── FakeLLMAdapter
    │
    └── OpenAIAdapter
```

The fake adapter provides deterministic responses for testing.

The production adapter can connect to an OpenAI-compatible LLM configuration.

---

# 🧩 Prompt Engineering

Prompt templates are maintained separately from application logic.

```text
prompts/
│
├── v1/
│   ├── developer.md
│   ├── diagnostic_system.md
│   ├── system.md
│   └── user.md
│
└── v2_challenger/
    ├── developer.md
    ├── diagnostic_system.md
    ├── system.md
    └── user.md
```

This makes prompt versions easier to:

- Maintain
- Compare
- Test
- Improve
- Replace

---

# 🔎 Retrieval Layer

The project contains retrieval components for supporting diagnostic context.

```text
shield/retrieval/
├── models.py
├── retriever.py
└── store.py
```

The retrieval layer is designed to provide relevant contextual information to the diagnostic pipeline.

---

# 🔧 Repair Execution

The repair subsystem separates proposed remediation from actual execution.

```text
Diagnostic Recommendation
          │
          ▼
   Governance Decision
          │
          ▼
   Repair Executor
          │
          ▼
   Controlled Action
```

This architecture prevents unrestricted AI-generated actions from directly affecting the cluster.

---

# 🧪 Testing

Run the complete test suite:

```powershell
pytest -q
```

Current result:

```text
130 passed
```

---

## API Integration Tests

Run:

```powershell
pytest -q tests\integration\test_diagnostic_api.py -vv
```

The integration suite currently contains:

```text
24 tests
```

and all tests pass.

---

## Linting

Run Ruff:

```powershell
ruff check shield services tests
```

Expected result:

```text
All checks passed!
```

---

## Git Validation

Check repository state:

```powershell
git status
```

Expected:

```text
nothing to commit, working tree clean
```

---

# 🧪 Testing Strategy

The project contains multiple levels of testing.

## Unit Tests

Test individual components such as:

- Schemas
- Prompt rendering
- Prompt registry
- LLM adapters
- Output parser
- Diagnostic service
- Governance decisions
- CPTP
- Repair execution
- Retrieval
- Configuration

## Integration Tests

Validate the complete API behavior including:

- Health endpoint
- Diagnostic endpoint
- Workflow endpoint
- Validation failures
- Service errors
- Internal errors
- Governance decisions

## Adversarial Tests

Test governance behavior against potentially unsafe or invalid inputs.

## Property-Based Tests

Use Hypothesis to validate important system invariants across generated inputs.

---

# 🖥️ Installation

## 1. Clone Repository

```powershell
git clone https://github.com/aparna190417/SCD-shield-platform.git
```

```powershell
cd SCD-shield-platform
```

---

## 2. Create Virtual Environment

```powershell
python -m venv .venv
```

---

## 3. Activate Virtual Environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 4. Install Project

```powershell
pip install -e .
```

---

# ▶️ Running the API

Start the FastAPI server:

```powershell
python -m uvicorn services.api.app:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

---

# 📚 API Documentation

After starting the server, open:

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### OpenAPI

```text
http://127.0.0.1:8000/openapi.json
```

The Swagger interface provides interactive access to:

- `/health`
- `/diagnose`
- `/diagnose/workflow`

---

# 🔐 Environment Configuration

Create a local `.env` file based on:

```text
.env.example
```

Sensitive credentials should remain in `.env` and should **never be committed to Git**.

The repository includes `.gitignore` configuration to prevent environment secrets from being committed.

---

# 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development language |
| FastAPI | REST API |
| Pydantic | Data validation |
| Uvicorn | ASGI server |
| Pytest | Testing |
| Hypothesis | Property-based testing |
| Ruff | Linting |
| LangChain | LLM ecosystem |
| Chroma | Retrieval / vector storage |
| OpenAI-compatible API | LLM integration |
| Git | Version control |
| GitHub | Source repository |

---

# 📊 Current Project Status

## ✅ Implemented

- FastAPI service
- Health endpoint
- Diagnostic endpoint
- Diagnostic workflow endpoint
- Incident schemas
- Input validation
- Diagnostic service
- Context builder
- Prompt registry
- Prompt renderer
- LLM adapter architecture
- Fake deterministic LLM adapter
- OpenAI-compatible adapter
- Structured output parser
- Governance decisions
- CPTP
- Repair execution layer
- Retrieval layer
- Prompt versioning
- Adversarial testing
- Property-based testing
- Integration testing
- API documentation
- Logging
- Error handling

---

# ✅ Validation Status

```text
Tests
-------------------------
130 passed

API Integration Tests
-------------------------
24 passed

Ruff
-------------------------
All checks passed

Git
-------------------------
Working tree clean
```

---

# 🎯 Project Goal

The goal of SCD-SHIELD is to demonstrate how AI-assisted infrastructure diagnostics can be combined with deterministic validation and governance controls.

The system focuses on:

```text
AI Reasoning
     +
Structured Diagnostics
     +
Evidence
     +
Governance
     +
Controlled Remediation
```

rather than allowing an LLM to directly perform unrestricted infrastructure operations.

---

# 🔒 Safety Principle

> **AI recommends. Governance decides. Execution remains controlled.**

This principle is central to the architecture of SCD-SHIELD.

---

# 🚀 Future Improvements

Potential future improvements include:

- Real-time cluster telemetry ingestion
- NVIDIA GPU telemetry integration
- Automated incident correlation
- Advanced retrieval pipelines
- Production LLM deployment
- Kubernetes integration
- Prometheus/Grafana integration
- Distributed cluster monitoring
- Real remediation adapters
- Incident history and analytics
- Web-based operations dashboard
- Authentication and authorization
- Audit logging
- Production deployment

---

# 📁 Repository

GitHub:

https://github.com/aparna190417/SCD-shield-platform

---

# 👩‍💻 Author

## Aparna Patel

GitHub:

https://github.com/aparna190417

---

# ⭐ Project Summary

**SCD-SHIELD** is a prototype autonomous supercomputer cluster diagnostic platform that combines:

- FastAPI
- Python
- Prompt Engineering
- LLM adapters
- Structured diagnostics
- Retrieval
- Governance
- Controlled remediation
- Adversarial testing
- Property-based testing
- Automated validation

The project demonstrates a safety-oriented architecture for applying AI reasoning to high-performance computing infrastructure diagnostics.

---

## 🏁 Final Status

**SCD-SHIELD — Functional Prototype**

text
130 Tests Passing
Ruff Clean
API Working
Swagger Documentation Available
Governance Layer Implemented
Prompt System Implemented
Diagnostic Workflow Implemented
```

**Built with Python, FastAPI, Prompt Engineering, LLMs, Testing, and Governance.**
