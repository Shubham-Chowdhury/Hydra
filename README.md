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
- `POST /api/v1/recommendations/evaluate` — Student evaluation endpoint accepting `StudentProfileRequest` and returning `EvaluationResponse` with 3-state eligibility, INR affordability, preference fit, and trace.
- `GET /api/v1/data-sources` — Registered admissions data source documents and verification status.
- `GET /api/v1/admissions/cutoffs` — Verified historical cutoff observations with deterministic filtering and mandatory legal disclaimer.
- `GET /api/v1/admissions/programmes` — Unique academic programmes derived from admissions records.
- `GET /api/v1/admissions/eligibility-criteria` — Authoritative eligibility criteria published by official examination authorities.
- `POST /api/v1/twin/construct` — Twin Agent construction endpoint transforming student profile inputs into an explainable, structured, and versioned `TwinSnapshot` (M001).
- `GET /api/v1/twin/{twin_id}` — Retrieval of an existing Student Digital Twin snapshot by identifier.
- `POST /api/v1/franchise/auction` — Franchise Agents simulated auction evaluation and bid ranking (M002).
- `GET /api/v1/franchise/franchises` — Available programme franchise agents and metadata.
- `POST /api/v1/planner/plan` — Heist Planner A* state-space planning with admissible lower-bound heuristic (M003).
- `POST /api/v1/simulator/run` — Simulator counterfactual scenario generation and bounded Monte Carlo sampling (M004).
- `POST /api/v1/boss-fight/stress-test` — Adversarial Boss-Fight 6-attack stress testing and surviving alternatives discovery (M004).
- `GET /api/v1/oracle/status` — Oracle forecasting model status and data readiness diagnostics (M005).
- `POST /api/v1/oracle/forecast` — Admissions cutoff time-series forecasting with uncertainty bounds (M005).
- `GET /api/v1/interests/status` — Neural Interest Decoder dual-engine operational status (M006).
- `POST /api/v1/interests/decode` — Dense semantic decoding of natural language interest narratives (M006).
- `POST /api/v1/interests/confirm` — User confirmation of suggested interest concepts (M006).
- `POST /api/v1/referee/evaluate` — Central Referee multi-agent synthesis and 9-tier decision arbitration (M007).

For complete technical specifications, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Documentation Index

- [AGENTS.md](AGENTS.md): Persistent engineering and verification rules for AI agents and developers.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Comprehensive 13-layer architecture, dependency rules, and agent contracts.
- [docs/ROADMAP.md](docs/ROADMAP.md): Canonical 11-phase delivery plan, repository structure, and Phase 1 vertical slice specification.
- [docs/DECISIONS.md](docs/DECISIONS.md): Architectural Decision Records (ADRs) explaining technical trade-offs.
- [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md): Admissions knowledge base data provenance protocols, source registry, and quarantine rules.
- [docs/engineering/IMPLEMENTATION_WALKTHROUGH.md](docs/engineering/IMPLEMENTATION_WALKTHROUGH.md): Master architectural guide, method-by-method implementation walkthrough, and symbolic AI reference.

---

## Project Status

- **Completed Milestones**:
  - **Phase 0 — Environment audit and engineering contract**: Complete.
  - **Phase 1 — Full-stack foundation and first working vertical slice**: Complete (React + TypeScript UI, FastAPI backend, canonical endpoints, 4 synthetic demonstration programmes in INR, deterministic eligibility rule evaluation, minimal NetworkX traversal).
  - **Phase 2 — Symbolic AI core: frames, semantic networks, inheritance, rule engine and inference explanations**: Complete (Generalised frame registry with multiple inheritance and conflict arbitration, requirement expression AST with Three-Valued Logic, alternative admission pathways, hierarchical reasoning tree inspector, and typed graph provenance).
  - **Phase 3 — Admissions knowledge base and data provenance**: Complete (Authoritative source registry, SHA-256 artifact verification, row-level provenance, ingestion & quarantine pipeline, decoupled historical cutoffs with mandatory disclaimer, verified JEE Advanced criteria extracted from genuine official HTML artifact, read-only admissions API, and frontend evidence view).
  - **Phase 3.1 — Provenance integrity correction and admissions-data audit**: Complete (Stop-ship synthetic fixture reclassification: JoSAA cutoff records explicitly classified as synthetic demonstration fixtures, real JoSAA endpoints unverified due to remote NIC SSL handshake timeouts, scoped examination criteria, and regression hardening).
  - **Phase 4 — Twin Agent: Student Digital Twin Construction**: Complete (Deterministic 11-step profile transformation pipeline, typed fact provenance taxonomy, conservative grading normalizations, zero predictive rank speculation, multidimensional completeness engine across 5 dimensions, FRAME_STUDENT_BASE frame hierarchy integration, semantic graph pathway discovery, canonical API endpoints, and interactive frontend Digital Twin inspector).
  - **Phase 4.1 — Twin Agent Semantic and Integrity Corrections (M001)**: Complete (Server-authorized CBSE CGPA normalization, geographic tri-state classification distinguishing unprovided neutrality from anywhere-in-India scope, score-based academic highlights threshold heuristics with non-cognitive disclaimers, rejection of client verification flags, deep recursive snapshot immutability, frame registry concurrency safety, forward semantic network preservation, and 144 passing backend tests).
  - **Phase 5 — Franchise Agents & Simulated Auction (M002)**: Complete (Autonomous programme representative agents, multi-criteria suitability bidding protocol with dynamic weight renormalization `v1.0`, simulated second-price auction engine, strict `NO_BID` candidate exclusion, and interactive React auction UI).
  - **Phase 6 — Heist Planner using A* (M003)**: Complete (Forward state-space planning engine, immutable `PlanningState` condition tracking, 6 typed semantic action categories, mathematically proven admissible heuristic $h_{\max}(n) = \max_{c \in U(n)} \min_a \text{cost}(a)$ with disjunctive resolution, closed-set cycle detection, and interactive React roadmap UI).
  - **Phase 7 — Simulator & Boss-Fight Agent (M004)**: Complete (Isolated in-memory counterfactual sandboxing, domain-bounded Monte Carlo simulation with physical clamping on rank/marks/budget/tuition, empirical quantile monotonicity $p10 \le p50 \le p90$, PSD covariance validation, 6-attack standard adversarial battery, surviving alternative discovery, and interactive React stress-testing UI).
  - **Phase 8 — Oracle Agent & Cutoff Forecasting (M005)**: Complete (Admissions cutoff time-series forecasting, data readiness gating rejecting 100% of unverified data with `INSUFFICIENT_VERIFIED_DATA` status, OLS lag regression with temporal train/test split, calibrated $[p10, p90]$ prediction intervals, and interactive React forecasting UI).
  - **Phase 9 — Neural Interest Decoder & GNN Assessment (M006)**: Complete (Dual-engine semantic interest decoder with `fastembed` ONNX `MiniLM-L6-v2` 384-D dense embeddings and 128-D lexical hashing fallback, tripartite lifecycle `STUDENT_STATED` $\to$ `MODEL_SUGGESTED` $\to$ `USER_CONFIRMED`, formal GNN evidence gate rejection to prevent overfitting, and interactive React decoder UI).
  - **Phase 10 — Central Referee Multi-Agent Orchestration & Validation Sprint (M007)**: Complete (Central multi-agent arbitration synthesizing proposals across all 6 specialized agents, 9-tier decision hierarchy with mandatory rule supremacy, stale snapshot rejection, envelope integrity auditing, and complete system-wide verification across all 9 navigation views).
- **System Verification Status**:
  - **Backend**: **244 passing tests / 0 failures** (`pytest`).
  - **Frontend**: **0 errors / 1,606 modules transformed** (`npm run build`).
  - **All 9 Navigation Views**: Fully operational and interactive in the UI.

---

## Development Setup & Prerequisites

### Prerequisites (Observed in Environment Audit)

- **Operating System**: Windows 11 (PowerShell 5.1)
- **Python**: Python 3.13 (via Python Launcher: `py -3.13`) with `pip 26.2+`
  - *Note*: MSYS2 Python 3.14 on this system lacks `pip` and must not be used.
- **Node.js**: v24.19+ with `npm 11.17+` (use `npm.cmd` on Windows)
- **Git**: Git 2.55+

### Initializing the Local Environment

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

3. **Backend Dependencies (Reproducible Exact Lockfile)**
   ```powershell
   pip install -r backend/requirements.lock
   pip check  # Verifies zero broken dependency requirements
   ```
   *Note*: `backend/requirements.txt` contains top-level direct dependencies. `backend/requirements.lock` provides an exact-version lock for all 46 direct and transitive dependencies (without per-wheel cryptographic SHA-256 binary hashes).

4. **Neural Embedding Cache & Offline Execution**
   - The Interest Decoder uses `sentence-transformers/all-MiniLM-L6-v2` (Apache-2.0, 22.7M parameters) via FastEmbed and ONNX Runtime CPU.
   - The 90.4MB ONNX weights (`model.onnx`, SHA-256: `bbd7b466f6d58e646fdc2bd5fd67b2f5e93c0b687011bd4548c420f7bd46f0c5`) are cached locally under `%LOCALAPPDATA%\Temp\fastembed_cache\models--Qdrant--all-MiniLM-L6-v2-onnx\snapshots\d13954661f83248295ba75c1ed411eef3b7b936e` (Windows) or `~/.cache/fastembed/`.
   - Once cached, embedding inference operates 100% offline with zero outbound network requests.
   - If FastEmbed or ONNX is absent, `InterestDecoder` automatically activates `LexicalHashingEncoder` (128-D character n-gram hashing) as an offline fallback.

5. **Frontend Setup**
   ```powershell
   cd frontend
   npm.cmd install
   npm.cmd run build
   ```

---

## License & Attribution

Hydra is an academic research and educational prototype. All demonstration data is synthetic and explicitly labelled as such.

