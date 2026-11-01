# Hydra

Hydra is an explainable AI-powered academic decision-support and planning system. It helps students explore academic programmes and career pathways, evaluate their eligibility, compare alternatives, plan proactive action sequences to satisfy admission criteria, simulate possible academic futures, and stress-test these plans under adverse conditions.

---

## System Overview

Hydra combines symbolic AI reasoning with selective machine learning to provide transparent, trustworthy academic guidance. 

### Core AI Foundations

- **Domain Frames**: Strongly-typed Python dataclasses representing students, programmes, institutions, qualifications, skills, and careers with explicit slot inheritance.
- **Semantic Network (NetworkX)**: A typed, directed multigraph modeling academic pathways, subject prerequisites, skill development, and career trajectories. (Introduced in Phase 1 with genuine traversal; deepened in Phase 2).
- **Deterministic Rule Engine**: An auditable IF–THEN inference engine that evaluates admissions criteria and produces comprehensive traces (rules evaluated, rules fired, facts used, plain-language justifications).
- **Three-State Eligibility Model**: Clear classification into `eligible`, `ineligible`, or `needs_review` (missing facts are never treated as satisfied eligibility), strictly decoupled from affordability and preference fit.
- **Demonstration Context**: India-focused synthetic demonstration catalogue using INR (`total_budget_inr`, `estimated_total_tuition_inr`), supporting grading scales, entrance exams (e.g., JEE Main, MHT-CET), entrance ranks, and location preferences with explicit synthetic labelling.
- **Explainability**: Every decision is supported by an audit trail that explicitly distinguishes verified institutional facts from probabilistic predictive estimates.

### Six Specialised Agents

Hydra features six specialised agents coordinated through a central Referee:

1. **Twin Agent**: Builds and maintains the student's structured academic and financial profile.
2. **Franchise Agents**: Represent individual academic programmes and produce simulated suitability bids.
3. **Oracle Agent**: Estimates future admission cutoffs and competitive thresholds using historical data and ML models.
4. **Heist Planner Agent**: Formulates step-by-step action plans (A* search) to unlock prerequisites and bridge credential gaps.
5. **Simulator Agent**: Explores alternative scenarios and "what-if" counterfactuals across academic branches.
6. **Boss-Fight Agent**: Introduces adversarial conditions (grade drops, fee hikes, cutoff spikes) to stress-test plan resilience.

A central **Referee** coordinates the agents, cross-examines proposals against authoritative rules, resolves conflicts, and generates an auditable reasoning bundle.

---

## Architecture & Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS. Strictly a presentation and interaction layer; never computes eligibility.
- **Backend**: Python 3.13, FastAPI, Pydantic v2 (API validation schemas), Python dataclasses (internal domain frames), NetworkX (semantic graph).
- **Inference**: Deterministic pure-Python rule engine with immutable trace logging.
- **Future ML/DL**: scikit-learn, sentence-transformers, PyTorch (introduced in Phase 8 and Phase 9).

### Architectural Boundaries & Dependency Flow
- **Request Flow (Runtime)**: React UI → FastAPI routes (`/api/v1/`) → Application Services (`app/services/`) → Domain Reasoning & Knowledge (`app/domain/`, `app/knowledge/`, `app/rules/`) → Structured JSON Response → React UI.
- **Code Dependency Principle (Compile-Time)**: Inward-only dependencies. Domain frames, rule engines, and knowledge networks must NEVER import React, FastAPI, Starlette, HTTP request objects, or frontend-specific types.

### Canonical API Endpoints

- `GET /api/health` — Health and service liveness check.
- `GET /api/v1/programmes` — Programme catalog retrieval with explicit synthetic demonstration tags and provenance.
- `POST /api/v1/recommendations/evaluate` — Student evaluation endpoint accepting `StudentProfileRequest` (subject scores with grading scale, entrance exam name, entrance rank, preferred locations, total budget in INR, preferred disciplines, career goals) and returning `EvaluationResponse` (eligibility status `eligible`, `ineligible`, `needs_review`; affordability on total duration INR tuition basis; preference fit; evidence; rule IDs; human-readable trace; graph-discovered skills/careers; runtime UTC timestamp; and synthetic provenance).
- `GET /api/v1/data-sources` — Registered admissions data source documents and verification status.
- `GET /api/v1/admissions/cutoffs` — Verified historical cutoff observations with deterministic filtering and mandatory legal disclaimer.
- `GET /api/v1/admissions/programmes` — Unique academic programmes derived from admissions records.
- `GET /api/v1/admissions/eligibility-criteria` — Authoritative eligibility criteria published by official examination authorities.
- `POST /api/v1/twin/construct` — Twin Agent construction endpoint transforming student profile inputs into an explainable, structured, and versioned `TwinSnapshot` with typed fact provenance, conservative grading scale normalizations, and multidimensional completeness auditing.
- `GET /api/v1/twin/{twin_id}` — Retrieval of an existing Student Digital Twin snapshot by identifier.

For complete technical specifications, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Documentation Index

- [AGENTS.md](AGENTS.md): Persistent engineering and verification rules for AI agents and developers.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Comprehensive 13-layer architecture, dependency rules, and agent contracts.
- [docs/ROADMAP.md](docs/ROADMAP.md): Canonical 11-phase delivery plan, repository structure, and Phase 1 vertical slice specification.
- [docs/DECISIONS.md](docs/DECISIONS.md): Architectural Decision Records (ADRs) explaining technical trade-offs.
- [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md): Admissions knowledge base data provenance protocols, source registry, and quarantine rules.

---

## Project Status

- **Completed Milestones**:
  - **Phase 0 — Environment audit and engineering contract**: Complete.
  - **Phase 1 — Full-stack foundation and first working vertical slice**: Complete (React + TypeScript UI, FastAPI backend, canonical endpoints, 4 synthetic demonstration programmes in INR, deterministic eligibility rule evaluation, minimal NetworkX traversal).
  - **Phase 2 — Symbolic AI core: frames, semantic networks, inheritance, rule engine and inference explanations**: Complete (Generalised frame registry with multiple inheritance and conflict arbitration, requirement expression AST with Three-Valued Logic, alternative admission pathways, hierarchical reasoning tree inspector, and typed graph provenance).
  - **Phase 3 — Admissions knowledge base and data provenance**: Complete (Authoritative source registry, SHA-256 artifact verification, row-level provenance, ingestion & quarantine pipeline, decoupled historical cutoffs with mandatory disclaimer, verified JEE Advanced criteria, read-only admissions API, and frontend evidence view).
  - **Phase 3.1 — Provenance integrity correction and admissions-data audit**: Complete (Stop-ship synthetic fixture reclassification, evidentiary invariant enforcement, scoped examination criteria, honest NIC SSL documentation, and regression hardening).
  - **Phase 4 — Twin Agent: Student Digital Twin Construction**: Complete (Deterministic 11-step profile transformation pipeline, typed fact provenance taxonomy, conservative grading normalizations, zero predictive rank speculation, multidimensional completeness engine across 5 dimensions, FRAME_STUDENT_BASE frame hierarchy integration, semantic graph pathway discovery, canonical API endpoints, and interactive frontend Digital Twin inspector).
- **Next Milestone**: **Phase 5 — Franchise Agents and Simulated Auction** (Programme franchise agents, multi-criteria suitability bidding protocol, and Central Referee auction orchestration).

---

## Development Setup & Prerequisites

### Prerequisites (Observed in Environment Audit)

- **Operating System**: Windows 11 (PowerShell 5.1)
- **Python**: Python 3.13 (via Python Launcher: `py -3.13`) with `pip 26.2+`
  - *Note*: MSYS2 Python 3.14 on this system lacks `pip` and must not be used.
- **Node.js**: v24.19+ with `npm 11.17+` (use `npm.cmd` on Windows)
- **Git**: Git 2.55+

### Initializing the Local Environment (For Phase 1)

1. **Git Repository Setup**
   ```powershell
   git init
   git remote add origin https://github.com/Shubham-Chowdhury/Hydra.git
   ```

2. **Python Virtual Environment**
   ```powershell
   py -3.13 -m venv .venv
   .venv\Scripts\activate
   python -m pip install --upgrade pip
   ```

3. **Backend Dependencies (Phase 1)**
   ```powershell
   pip install -r backend/requirements.txt
   ```

4. **Frontend Setup (Phase 1)**
   ```powershell
   cd frontend
   npm.cmd install
   ```

---

## License & Attribution

Hydra is an academic research and educational prototype. All demonstration data is synthetic and explicitly labelled as such.

