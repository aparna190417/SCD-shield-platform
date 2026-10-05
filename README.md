\# NVIDIA SCD-SHIELD



\## Autonomous Supercomputer Cluster Diagnostics \& Self-Healing Reliability Engine



SCD-SHIELD is a production-style diagnostic and governance platform designed for autonomous supercomputer cluster reliability.



It combines:



\- LLM-assisted incident diagnosis

\- Structured incident validation

\- Evidence retrieval

\- Context building

\- Prompt versioning

\- Diagnostic output parsing and repair

\- Governance and safety decisions

\- Controlled repair execution

\- Adversarial testing

\- Property-based testing

\- REST API with FastAPI

\- Structured logging



\---



\## Architecture



```text

Incident

&#x20;  |

&#x20;  v

FastAPI API

&#x20;  |

&#x20;  v

Diagnostic Service

&#x20;  |

&#x20;  +---- Context Builder

&#x20;  |

&#x20;  +---- Evidence Retriever

&#x20;  |

&#x20;  +---- Prompt Registry

&#x20;  |

&#x20;  +---- Prompt Renderer

&#x20;  |

&#x20;  +---- LLM Adapter

&#x20;  |

&#x20;  v

Diagnostic Result

&#x20;  |

&#x20;  v

Governance / CPTP

&#x20;  |

&#x20;  +---- APPROVE

&#x20;  |       |

&#x20;  |       v

&#x20;  |    Repair Executor

&#x20;  |

&#x20;  +---- REVIEW

&#x20;  |       |

&#x20;  |       v

&#x20;  |    Human Review

&#x20;  |

&#x20;  +---- REJECT

&#x20;          |

&#x20;          v

&#x20;       Action Blocked```



\---



\## Key Features



\### 1. Incident Diagnostics



Accepts structured cluster incidents containing:



Incident ID

Timestamp

Node ID

Incident type

Severity

Description

Telemetry

Metadata



\### 2. LLM Diagnostic Pipeline



The diagnostic service performs:



* Prompt loading
* Context generation
* Evidence retrieval
* Prompt rendering
* LLM request
* Structured output parsing
* Output repair when required



\### 3. Governance



The platform does not blindly execute LLM recommendations.

Every diagnostic result passes through governance controls.



Possible decisions:



* Decision	Behaviour
* approve	Controlled action may execute
* review	Human review required
* reject	Action is blocked



High LLM confidence does not automatically bypass governance rules.



\### 4. Controlled Repair



Repair execution is separated from diagnosis and protected by the governance boundary.



Diagnosis

&#x20;  ↓

Governance

&#x20;  ↓

Approved?

&#x20;┌─┴───────────────┐

&#x20;│                 │

YES               NO

&#x20;│                 │

&#x20;↓                 ↓

Execute        Block / Review



\### 5. Evidence Retrieval



The diagnostic pipeline can retrieve relevant evidence before generating a diagnosis.



\### 6. Prompt Versioning



Prompts are maintained as versioned files.



prompts/

├── v1/

│   ├── system.md

│   ├── developer.md

│   ├── user.md

│   └── diagnostic\_system.md

│

└── v2\_challenger/

&#x20;   ├── system.md

&#x20;   ├── developer.md

&#x20;   ├── user.md

&#x20;   └── diagnostic\_system.md



\### 7. Output Repair



Invalid or malformed diagnostic responses can be sent through a controlled repair path before final validation.



\### 8. Safety Testing



The project includes:



* Unit tests
* Integration tests
* Adversarial tests
* Property-based tests
* Governance safety tests
* API



\---



The application is built using FastAPI.



Start the API

python -m uvicorn services.api.app:app --reload



API:



http://127.0.0.1:8000



Swagger documentation:



http://127.0.0.1:8000/docs

Endpoints

Health Check

GET /health



Example:



{

&#x20; "status": "healthy",

&#x20; "service": "scd-shield",

&#x20; "version": "1.0.0"

}

Diagnostic

POST /diagnose



Runs the diagnostic pipeline for an incident.



Complete Workflow

POST /diagnose/workflow



Runs:



Incident

&#x20;  ↓

Diagnosis

&#x20;  ↓

Governance

&#x20;  ↓

Controlled Repair Decision



Example incident:



{

&#x20; "incident\_id": "INC-999",

&#x20; "timestamp": "2026-10-05T12:00:00Z",

&#x20; "node\_id": "node-test",

&#x20; "incident\_type": "hardware",

&#x20; "severity": "critical",

&#x20; "description": "Test GPU communication failure",

&#x20; "telemetry": {

&#x20;   "link\_errors": 99,

&#x20;   "temperature\_c": 82,

&#x20;   "gpu\_utilization": 95

&#x20; },

&#x20; "metadata": {

&#x20;   "cluster": "test-cluster",

&#x20;   "gpu\_type": "H100"

&#x20; }

}

Project Structure

SCD-shield-platform/

│

├── prompts/

│   ├── v1/

│   └── v2\_challenger/

│

├── services/

│   └── api/

│       └── app.py

│

├── shield/

│   ├── config/

│   ├── context/

│   ├── engines/

│   ├── governance/

│   ├── ingress/

│   ├── orchestration/

│   ├── retrieval/

│   └── tools/

│

├── tests/

│   ├── adversarial/

│   ├── integration/

│   ├── property/

│   └── unit/

│

├── .env.example

├── .gitignore

├── pyproject.toml

└── README.md

Testing



The project currently has a comprehensive automated test suite.



Run all tests:



pytest -q



Current result:



130 passed



Run integration tests:



pytest -q tests/integration/test\_diagnostic\_api.py



Run adversarial tests:



pytest -q tests/adversarial



Run property-based tests:



pytest -q tests/property



Run linting:



ruff check shield services tests



Check Git whitespace/errors:



git diff --check

Test Coverage



The test suite covers:



API health endpoint

Diagnostic endpoint

Workflow endpoint

Input validation

Diagnostic service

LLM adapters

Prompt registry

Prompt rendering

Output parsing

Output repair

Evidence retrieval

Context building

Governance decisions

CPTP behaviour

Repair execution

Adversarial safety cases

Property-based invariants

LLM Providers



The application supports a deterministic fake provider for development and testing.



It can also be configured for an OpenAI-based provider.



Example environment configuration:



LLM\_PROVIDER=fake

OPENAI\_API\_KEY=

OPENAI\_MODEL=



For real LLM usage, configure the appropriate provider settings in .env.



Never commit API keys or secrets to GitHub.



Safety Model



SCD-SHIELD follows a diagnose → govern → execute architecture.



The LLM is responsible for producing a structured diagnostic result.



The governance layer independently determines whether the recommended action can proceed.



Therefore:



LLM confidence ≠ execution permission



This separation is important for autonomous infrastructure systems where unsafe recommendations must not directly trigger repairs.



Example Workflow

1\. Cluster incident received

&#x20;         ↓

2\. Incident schema validation

&#x20;         ↓

3\. Evidence retrieval

&#x20;         ↓

4\. Context construction

&#x20;         ↓

5\. Versioned prompt rendering

&#x20;         ↓

6\. LLM diagnosis

&#x20;         ↓

7\. Structured output validation

&#x20;         ↓

8\. Output repair if required

&#x20;         ↓

9\. Governance decision

&#x20;         ↓

&#x20;  ┌──────┼──────┐

&#x20;  ↓      ↓      ↓

&#x20;APPROVE REVIEW REJECT

&#x20;  ↓      ↓      ↓

&#x20;EXECUTE HUMAN  BLOCK

&#x20;         REVIEW

Development



Create and activate the virtual environment:



Windows

python -m venv .venv

.venv\\Scripts\\Activate.ps1



Install the project dependencies according to the project configuration.



Run the application:



python -m uvicorn services.api.app:app --reload



Run tests:



pytest -q



Run linting:



ruff check shield services tests

Git Workflow



Check status:



git status



Run validation:



ruff check shield services tests

pytest -q

git diff --check



Commit:



git add .

git commit -m "your message"



Push:



git push origin main

Current Project Status

Completed

&#x20;FastAPI diagnostic API

&#x20;Health endpoint

&#x20;Incident validation

&#x20;Diagnostic service

&#x20;LLM adapter architecture

&#x20;Fake LLM provider

&#x20;OpenAI adapter

&#x20;Prompt registry

&#x20;Prompt renderer

&#x20;Evidence retrieval

&#x20;Context builder

&#x20;Structured output parser

&#x20;Diagnostic output repair

&#x20;Governance layer

&#x20;CPTP safety controls

&#x20;Controlled repair execution

&#x20;Integration testing

&#x20;Adversarial testing

&#x20;Property-based testing

&#x20;Structured logging

&#x20;Swagger/OpenAPI documentation

&#x20;GitHub repository

Validation

Tests: 130 passed

Ruff: All checks passed

Git working tree: Clean

Technology Stack

Python 3.13

FastAPI

Pydantic

Uvicorn

Pytest

Hypothesis

Ruff

LangChain

Chroma

OpenAI-compatible LLM integration

Repository



GitHub:



https://github.com/aparna190417/SCD-shield-platform

