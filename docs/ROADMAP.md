# Hydra Project Roadmap & Implementation Milestones

**System Name**: Hydra  
**Status**: Phase 0 Baseline  
**Document Purpose**: Define implementation phases, vertical slice specifications, repository evolution, and explicit verification criteria.

---

## 1. Canonical Phased Implementation Roadmap

Hydra is delivered across eleven disciplined, incrementally verified phases.

| Phase | Milestone Name | Primary Focus | Dependencies | Canonical Deliverables |
|---|---|---|---|---|
| **Phase 0** | **Environment audit and engineering contract** | Environment inspection, architectural baseline, agent contracts, AGENTS.md, repo plan | None | Documentation baseline, `.gitignore`, audit report (Complete) |
| **Phase 1** | **Full-stack foundation and first working vertical slice** | Lean full-stack pipeline: FastAPI backend, Vite + React + Tailwind frontend, canonical endpoints, `StudentFrame` and `ProgrammeFrame` dataclasses, minimal NetworkX semantic network, genuine graph traversal for skills/careers, deterministic IF–THEN rule evaluator, 3-state eligibility check, INR affordability (`total_budget_inr` vs `estimated_total_tuition_inr`), preference fit, immutable trace logging, Pydantic boundary validation, and automated test suite | Phase 0 | End-to-end working vertical slice, test suite, UI cards (Complete) |
| **Phase 2** | **Symbolic AI core: frames, semantic networks, inheritance, rule engine and inference explanations** | Generalized Python frame hierarchy, multi-level slot inheritance, relationship inheritance rules, conflict handling, reusable rule-engine abstractions, richer multi-condition inference explanation traces, and comprehensive NetworkX graph reasoning | Phase 1 | Symbolic knowledge representation & rule engine modules (Complete) |
| **Phase 3** | **Admissions knowledge base and data provenance** | Curated admissions datasets, schema validation, data provenance trackers, audit trail logging, synthetic data tagging rigor | Phase 2 | Knowledge base ingestion, provenance models (Complete) |
| **Phase 4** | **Twin Agent** | Autonomous student digital twin construction, typed fact provenance, conservative grading scale normalization, multidimensional completeness | Phase 3 | Twin agent module, profile normalization, Twin inspector (Complete) |
| **Phase 4.1** | **Twin Agent semantic & integrity corrections** | Policy-aware CBSE CGPA normalization, geographic tri-state classification, score-based academic highlights, server fact verification authority, deep immutability, frame isolation | Phase 4 | Hardened Twin Agent, expanded test suite (Complete) |
| **Phase 5** | **Franchise Agents and simulated auction (M002)** | Programme representative agents, multi-criteria suitability bidding protocol, capacity and pitch generation, deterministic auction tie-breakers | Phase 4.1 | Franchise agent society, bidding engine, React auction UI (Complete) |
| **Phase 6** | **Heist Planner using A\* (M003)** | Forward state-space search and A\* planning over prerequisite graphs to unlock pathways and remediate deficiencies with admissible heuristic | Phase 5 | A\* planner engine, milestone action plans, React planner UI (Complete) |
| **Phase 7** | **Simulator and Boss-Fight Agent (M004)** | Counterfactual branching scenario simulator ("what-if" models) and adversarial stress-testing agent (6-attack battery, plan fragility scoring) | Phase 6 | Simulator & Boss-Fight agent modules, React stress testing UI (Complete) |
| **Phase 8** | **Oracle Agent and ML forecasting (M005)** | Historical admissions cutoff time-series regression and forecasting with data-readiness gating and calibrated confidence intervals $[P_{10}, P_{90}]$ | Phase 7 | Oracle agent module, cutoff forecasting, React oracle UI (Complete) |
| **Phase 9** | **Deep-learning Interest Decoder & GNN assessment (M006)** | Sentence embeddings for unstructured student interest statements with tripartite confirmation lifecycle; GNN formally evaluated | Phase 8 | Interest decoder, dense embedding matcher, GNN assessment report (Complete) |
| **Phase 10** | **Referee integration & system-wide verification (M007)** | Central Referee multi-agent arbitration synthesis, conflict detection, 9-tier decision hierarchy, end-to-end verification (Scenarios A–H) | Phase 9 | Central Referee service, full integration, React referee UI (Complete) |

---

## 2. Phase 1: Full-Stack Foundation & First Working Vertical Slice

The immediate goal of Phase 1 is to establish the full-stack foundation and implement a lean, fully functional working vertical slice connecting the React frontend to the Python FastAPI backend.

### Canonical API Contracts

Phase 1 establishes and exposes the three canonical API endpoints:

1. `GET /api/health`
   - **Purpose**: System health and service liveness check.
   - **Response**: `{"status": "ok", "version": "0.1.0"}`

2. `GET /api/v1/programmes`
   - **Purpose**: Retrieves the available synthetic demonstration programme catalogue.
   - **Response**: Array of programme summary objects, each tagged with `is_synthetic: true`, `dataset_label`, and `provenance`.

3. `POST /api/v1/recommendations/evaluate`
   - **Purpose**: Evaluates a student profile against academic programmes using deterministic rules and graph traversal.
   - **Input Payload (`StudentProfileRequest`)**:
     - `student_id: Optional[str]`
     - `subject_scores: List[SubjectScoreDto]` (`subject_code`, `subject_name`, `score`, `max_score`, `grading_scale`)
     - `entrance_exam_name: Optional[str]` (e.g., `"JEE Main"`, `"MHT-CET"`, `"KCET"`, or `None`)
     - `entrance_rank: Optional[int]` (e.g., `24500` or `None`)
     - `preferred_locations: List[str]` (e.g., `["Karnataka", "Maharashtra"]`)
     - `total_budget_inr: float` (e.g., `800000.0` for ₹8,00,000 total programme budget)
     - `preferred_disciplines: List[str]` (e.g., `["Computer Science", "Engineering"]`)
     - `career_goals: List[str]` (e.g., `["Software Engineer"]`)
   - **Output Payload (`EvaluationResponse`)**:
     - `evaluations: List[ProgrammeEvaluationDto]`, each containing:
       - `programme_id: str` (e.g., `"SYNTH_IN_CS_01"`)
       - `programme_title: str` (e.g., `"B.Tech. in Computer Science (Synthetic)"`)
       - `institution_name: str` (Synthetic name, e.g., `"Demo Institute of Technology, Bengaluru"`)
       - `data_provenance: ProvenanceDto` (`is_synthetic: true`, `dataset_label: "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"`, `provenance: "SYNTHETIC_DEMO_RECORD_V1"`)
       - `eligibility_status: "eligible" | "ineligible" | "needs_review"`
       - `affordability: AffordabilityDto` (`is_affordable: bool`, `total_budget_inr: float`, `estimated_total_tuition_inr: float`, `currency: "INR"`, `cost_basis: "tuition_only_total"`)
       - `preference_fit: PreferenceFitDto` (`fit_score: float` bounded $[0.0, 1.0]$, `criteria_breakdown: Dict[str, float]`)
       - `evidence: List[str]` (evaluated score and rank comparisons)
       - `rules_fired: List[RuleOutcomeDto]` (rule IDs, rule names, status `SATISFIED` / `VIOLATED`)
       - `reasoning_trace: str` (human-readable explanation string)
       - `missing_facts: List[str]` (e.g., unstated prerequisite courses or unrecognized grading scales)
     - `discovered_relationships: List[DiscoveredRelationshipDto]` (skills developed and downstream careers extracted via genuine NetworkX graph traversal)
     - `is_synthetic: true`
     - `audit_timestamp: str` (dynamically generated at runtime in ISO 8601 UTC)

### User Flow
1. **Open UI**: User opens the Hydra web interface (React + Vite + Tailwind CSS).
2. **Profile Input**: User enters or loads an India-focused student profile (subject grades with grading scale, optional entrance exam and rank, preferred states, total education budget in INR, and career goals).
3. **Submit to API**: Frontend dispatches profile to `POST /api/v1/recommendations/evaluate`.
4. **Backend Processing & Evaluation**:
   - Validates incoming request using Pydantic DTOs (`backend/app/api/schemas/`).
   - Translates DTO into domain frame `StudentFrame` (`backend/app/domain/student.py`).
   - Delegates to `EvaluationService` (`backend/app/services/evaluation.py`).
   - Evaluates profile against curated synthetic programme frames (`backend/app/domain/programme.py`).
   - Executes deterministic rules (`backend/app/rules/engine.py`) checking subject minimums, entrance ranks, and grading scale compatibility.
   - Performs genuine NetworkX graph traversal (`backend/app/knowledge/graph.py`) to discover related skills and downstream careers.
   - Compares `total_budget_inr` with `estimated_total_tuition_inr` (labeled `cost_basis: "tuition_only_total"`).
   - Assembles an auditable inference trace with rule IDs, facts used, and runtime UTC timestamp.
5. **Multi-Dimensional Response Display**:
   - **Academic Eligibility**: Distinctly classified as `eligible`, `ineligible`, or `needs_review`.
   - **Affordability**: Separately classified as `affordable` or `unaffordable` with INR total tuition vs. budget breakdown.
   - **Preference Fit**: Relative fit score $[0.0, 1.0]$ based on discipline and career alignment.
   - **Audit Trail**: Expandable inspector showing facts evaluated, rule IDs fired, and plain-language reasons.
   - **Graph Discovery**: Discovered skills developed by the programme and downstream careers enabled.

### Three-State Eligibility Semantics

- **`eligible`**: The student meets all mandatory subject requirements and entrance rank benchmarks with verified evidence in compatible grading scales.
- **`ineligible`**: The student fails at least one mandatory prerequisite (e.g., student scored below minimum mathematics benchmark or entrance rank exceeded cutoff).
- **`needs_review`**: The student profile is missing critical required information (e.g., required laboratory safety certification not reported, or subject scores provided in an incompatible/unrecognized grading scale without an explicit mapping). **Missing facts are never treated as passed checks.**

### Explicitly Labelled Synthetic Catalogue (India Context, INR)

The Phase 1 demonstration dataset contains 4 synthetic academic programmes designed specifically to exercise each edge case with transparent provenance:

1. `SYNTH_IN_CS_01`: *B.Tech. in Computer Science (Synthetic)*
   - **Institution**: Demo Institute of Technology, Bengaluru (Karnataka)
   - **Tuition**: ₹1,50,000/yr $\times$ 4 years = ₹6,00,000 (`estimated_total_tuition_inr: 600000.0`, `cost_basis: "tuition_only_total"`)
   - **Academic Criteria**: Math $\ge 80\%$, English $\ge 70\%$, Physics $\ge 75\%$.
   - **Target Behavior**: Exercises clear eligibility and affordability for standard qualifying profiles.

2. `SYNTH_IN_DS_02`: *B.Tech. in Data Science (Synthetic)*
   - **Institution**: National Demonstration University, Pune (Maharashtra)
   - **Tuition**: ₹1,75,000/yr $\times$ 4 years = ₹7,00,000 (`estimated_total_tuition_inr: 700000.0`)
   - **Academic Criteria**: Math $\ge 85\%$, Programming $\ge 75\%$, or JEE Main rank $\le 25,000$.
   - **Target Behavior**: Exercises clear ineligibility when subject scores or entrance ranks fail benchmarks.

3. `SYNTH_IN_BIO_03`: *B.Tech. in Biotechnology (Synthetic)*
   - **Institution**: Synthetic College of Engineering, Hyderabad (Telangana)
   - **Tuition**: ₹1,25,000/yr $\times$ 4 years = ₹5,00,000 (`estimated_total_tuition_inr: 500000.0`)
   - **Academic Criteria**: Biology $\ge 75\%$, Chemistry $\ge 75\%$, plus mandatory Laboratory Safety Training certification.
   - **Target Behavior**: Exercises `needs_review` when certification is unstated or when grading scale is incompatible.

4. `SYNTH_IN_ROB_04`: *B.Tech. in Robotics & AI (Synthetic)*
   - **Institution**: Metropolitan Demo University, Delhi NCR (Delhi)
   - **Tuition**: ₹4,00,000/yr $\times$ 4 years = ₹16,00,000 (`estimated_total_tuition_inr: 1600000.0`)
   - **Academic Criteria**: Math $\ge 75\%$, Physics $\ge 75\%$.
   - **Target Behavior**: Demonstrates `eligible: true` combined with `is_affordable: false` when student budget is below ₹16,00,000 (e.g., ₹10,00,000).

> **Integrity Notice**: All demonstration records must be tagged with `is_synthetic: true`, `dataset_label: "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"`, and display a prominent UI badge indicating: *"Demonstration synthetic data — not official institutional admissions information."*

### Explicit Phase 1 vs. Phase 2 Boundary

To prevent postponing core reasoning while keeping Phase 1 achievable:
- **Phase 1 Deliverable**: Delivers a complete, functional end-to-end slice with:
  1. Strongly-typed `StudentFrame` and `ProgrammeFrame` Python dataclasses.
  2. Minimal in-memory `NetworkX` semantic network in `backend/app/knowledge/graph.py`.
  3. At least one genuine graph traversal returning related skills and careers (`Programme -[:DEVELOPS_SKILL]-> Skill -[:LEADS_TO_CAREER]-> Career`).
  4. Deterministic IF–THEN eligibility evaluator (`backend/app/rules/engine.py`) returning an `InferenceTrace`.
  5. 3-state eligibility model (`eligible`, `ineligible`, `needs_review`) strictly decoupled from INR affordability and preference fit.
  6. Pydantic request and response schemas validating all boundary payloads.
  7. Accessible React form and results presentation.
  8. Automated test suite verifying rules, graph traversal, and API contracts.
- **Phase 2 Expansion**: Deepens and generalizes the symbolic core:
  1. Multi-level slot inheritance (Institution $\rightarrow$ Faculty $\rightarrow$ Programme) with override semantics and non-inheritable guards.
  2. Generalized relationship inheritance and conflict-resolution strategies.
  3. Reusable rule-engine abstractions with prioritized rule chains.
  4. Richer multi-condition inference traces and audit explainers.
  5. Comprehensive NetworkX ontology queries and cycle-bounded traversals.

### Phase 1 Acceptance Criteria

- [ ] FastAPI backend serves `GET /api/health`, `GET /api/v1/programmes`, and `POST /api/v1/recommendations/evaluate`.
- [ ] Backend dependencies explicitly include `networkx`.
- [ ] Internal domain logic uses Python dataclasses (`StudentFrame`, `ProgrammeFrame`); boundaries use Pydantic DTOs.
- [ ] NetworkX graph represents synthetic programmes, skills, and careers with typed edges; genuine traversal returns discovered relationships.
- [ ] Rule evaluator evaluates prerequisites and returns full inference trace (rules evaluated, rules fired, facts used, plain-language reason).
- [ ] Backend strictly distinguishes the three eligibility states (`eligible`, `ineligible`, `needs_review`).
- [ ] Affordability is decoupled from academic eligibility and uses INR total duration basis (`total_budget_inr` vs `estimated_total_tuition_inr`, labeled `cost_basis: "tuition_only_total"`).
- [ ] Missing prerequisite facts or incompatible grading scales strictly produce `needs_review`.
- [ ] Student profile inputs support subject scores with grading scale, entrance exam name, entrance rank, preferred locations, and total budget in INR.
- [ ] Synthetic data is visibly and programmatically flagged (`is_synthetic: True`, `dataset_label: "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"`), using fictional university names.
- [ ] Audit timestamp is generated at runtime in UTC (ISO 8601).
- [ ] Automated tests pass (`pytest` for backend API, graph traversal, and rules; `npm.cmd run build` / tests for frontend).

---

## 3. Subsequent Canonical Phase Roadmaps

### Phase 2: Symbolic AI Core: Frames, Semantic Networks, Inheritance, Rule Engine and Inference Explanations
- **Domain Frames**: Formalize slot inheritance hierarchy across `InstitutionFrame`, `FacultyFrame`, and `ProgrammeFrame` with override mechanics and non-inheritable slot guards.
- **Semantic Network (`app/knowledge/`)**: NetworkX MultiDiGraph modeling academic prerequisites, developed skills, and target careers with cycle detection and bounded traversal.
- **Rule Engine (`app/rules/`)**: Deterministic IF–THEN inference engine recording evaluated conditions, fired rules, facts inspected, and structured explanation traces.

### Phase 3: Admissions Knowledge Base and Data Provenance (Completed)
- **Provenance Data Models**: Formalized `SourceDocument`, `DatasetSnapshot`, and `RecordProvenance` domain dataclasses with explicit `SourceStatus` (`official_source`, `derived_from_official`, `synthetic_demo`, `unverified`) and `ValidationStatus`.
- **Authoritative Source Registry**: Centralized manifest registry in `data/manifests/sources.json` and `data/manifests/snapshots.json` backed by `ProvenanceRegistry` with deterministic SHA-256 file checksums.
- **Ingestion & Quarantine Pipeline**: Strict record-level validation (`AdmissionRecordValidator`) rejecting non-positive ranks, inverted rank bounds, malformed identifiers, and duplicate keys into `data/quarantine/*.jsonl` with machine-readable error codes.
- **Official JEE (Advanced) Eligibility Ingestion**: Authentic HTML artifact retrieved from `https://jeeadv.ac.in/eligibility.html`, verified via SHA-256 (`d64c3026e63cd6f618eb7ee76a84db8ce80d5de4f21c4307ba7210b05c20374a`), and parsed into 5 formal mandatory criteria.
- **JoSAA Historical Cutoff Ingestion**: Deterministic CSV parser (`JoSAAImporter`) supporting published counselling formats, attaching row-level provenance (`row_index`) and immutable snapshot IDs.
- **Decoupled Historical Observations**: Cutoff observations strictly represent historical allocation boundaries, never universal eligibility prerequisites or admission guarantees.
- **Admissions API Endpoints**: Read-only endpoints (`GET /api/v1/data-sources`, `GET /api/v1/data-sources/{id}/snapshots`, `GET /api/v1/admissions/cutoffs`, `GET /api/v1/admissions/programmes`, `GET /api/v1/admissions/eligibility-criteria`) with pagination and mandatory disclaimer.
- **Frontend Evidence Inspector**: Accessible React view (`AdmissionsEvidenceView`) allowing developers and students to audit data sources, filter historical cutoffs, inspect source metadata, and verify formal criteria.

### Phase 3.1: Provenance Integrity Correction and Admissions-Data Audit (Completed)
- **Stop-Ship Fixture Reclassification**: Corrected the JoSAA fixture source from `SRC_JOSAA_FIXTURE_2026` to `SRC_JOSAA_SYNTHETIC_FIXTURE_2026`, setting `source_status = SourceStatus.SYNTHETIC_DEMO` and `is_synthetic = True` on every cutoff observation.
- **Evidentiary Invariant Enforcement**: Built `ProvenanceInvariantValidator` and domain invariants enforcing that `derived_from_official` strictly requires an authentic `official_source` document with verified artifact path and matching SHA-256 checksum. Prohibited synthetic records from claiming official status.
- **JEE (Advanced) 2026 Scope Clarification**: Scoped all 5 extracted criteria to `criterion_scope: "exam_appearance_eligibility"` and `target_examination: "JEE (Advanced)"`, preventing conflation between examination appearance eligibility and degree admission rules.
- **Honest Remote Limitation Documentation**: Documented NIC portal SSL handshake timeouts for official JoSAA endpoints, keeping them registered as explicitly `unverified` awaiting offline artifacts.
- **Unmistakable UI & API Demarcation**: Added prominent test fixture notices and badge demarcations in `AdmissionsEvidenceView.tsx` and API responses, ensuring illustrative records (e.g. IIT Bombay CSE rank 67) cannot be mistaken for real admissions outcomes.
- **Exhaustive Regression Suite**: Added comprehensive provenance invariant unit and integration tests (115 total tests passing, 0 failures).

### Phase 4: Twin Agent — Student Digital Twin Construction (Completed)
- **Deterministic Twin Pipeline**: Implemented `TwinAgent` (`backend/app/agents/twin_agent.py`) executing an 11-step pipeline transforming raw student profile requests into immutable, versioned `TwinSnapshot` objects.
- **Typed Fact Provenance & Origin Categories**: Every atomic attribute is tracked as an auditable `FactRecord` with explicit origin categories (`USER_PROVIDED`, `DETERMINISTICALLY_DERIVED`, `EXTERNAL_VERIFIED`, `UNKNOWN`), validation lifecycle states (`VALID`, `NEEDS_REVIEW`, `INVALID`, `MISSING`), derivation rules, and plain-language explanations.
- **Conservative Grading Scale Normalization**:
  - `percentage`: Valid within $[0, max\_score]$, normalized via standard percentage ratio.
  - `marks_obtained_out_of_total`: Normalized via explicit marks ratio rule `MARKS_RATIO_NORMALIZATION`.
  - `cbse_10_point`: Converted strictly via official CBSE formula $\text{Percentage} = \text{CGPA} \times 9.5$ with derivation rule `CBSE_CGPA_X_9_5`.
  - Unsupported scales (e.g. US 4-point GPA, letter grades): Normalized score set to `None`, validation status flagged as `NEEDS_REVIEW`, preserving the raw score while mandating manual transcript audit.
  - Out-of-bounds scores: Marked `INVALID`.
- **Zero Predictive Speculation**: Strictly records reported entrance exam names and ranks without speculative rank guessing, percentile predictions, or invented aptitude metrics.
- **Multidimensional Completeness Engine**: Assesses completeness independently across 5 dimensions (`academic`, `entrance_exam`, `financial`, `geographic`, `interests_and_career`), strictly decoupling completeness from academic programme eligibility.
- **Symbolic Frame System Integration**: Registers `FRAME_STUDENT_BASE` in `FrameRegistry` with inherited defaults (`currency: INR`, `cost_basis: tuition_only_total`), creating child instance frames `FRAME_STUDENT_{twin_id}` resolving explicit slots with full provenance paths.
- **Semantic Network Traversal**: Traverses `HydraKnowledgeGraph` to discover verified pathway edges connecting stated career ambitions and disciplines to academic programmes and skills.
- **Canonical API & Interactive UI**: Serves canonical endpoints `POST /api/v1/twin/construct` and `GET /api/v1/twin/{id}`, paired with an interactive frontend view (`StudentDigitalTwinView.tsx`) featuring 5 preset fixtures, dimensional completeness cards, academic normalization inspector, symbolic frame viewer, semantic pathway graph viewer, and auditable fact provenance table.
- **Automated Verification**: Comprehensive unit and integration test suite (`backend/tests/test_twin_agent.py`) expanding total repository test count to 130 passing tests.

### Phase 5: Franchise Agents and Simulated Auction
- **Programme Franchise Agents**: Independent agents representing individual academic programmes.
- **Bidding Protocol**: Produces multi-criteria suitability bids $[0.0, 1.0]$ based on student academic profile, career alignment, and cohort capacity.
- **Simulated Auction**: Referee orchestrates bid collection, ranking, and student preference matching.

### Phase 6: Heist Planner Using A*
- **Action Sequence Formulation**: A* search over academic prerequisite and skill transition graphs.
- **Remediation Milestones**: Generates cost-effective, bounded action pathways (summer courses, prerequisite certifications, exam retakes) to bridge deficiency gaps for `ineligible` or `needs_review` students.

### Phase 7: Simulator and Boss-Fight Agent
- **Simulator Agent**: Counterfactual exploration engine exploring branching scenario trees ("what if tuition rises 10%?", "what if exam score is 5 points higher?").
- **Boss-Fight Agent**: Adversarial stress-testing injecting realistic stochastic shocks (severe cutoff spikes, economic tuition inflation, sudden grade drops) to calculate plan survival scores and identify single points of failure.

### Phase 8: Oracle Agent and ML Forecasting
- **Admissions Cutoff Forecasting**: Historical admissions time-series regression models forecasting competitive cutoff scores.
- **Uncertainty Calibration**: Produces calibrated confidence bands $[P_{10}, P_{50}, P_{90}]$. Strictly flagged with `is_estimate: True`; never overrides mandatory prerequisite verification.

### Phase 9: Deep-Learning Interest Decoder; Optional GNN Extension
- **Interest Decoder**: Sentence embedding models (e.g., `sentence-transformers`) computing semantic cosine similarity between unstructured student interest statements and programme syllabi.
- **Optional GNN Extension**: Graph Neural Network link prediction exploring novel career-to-skill trajectories.

### Phase 10: Referee Integration, End-to-End Verification, Security and Release Hardening
- **Referee Multi-Agent Synthesis**: Central Referee arbitrates between Twin, Franchise, Oracle, Planner, Simulator, and Boss-Fight outputs into a unified explainable decision bundle.
- **System Verification & Hardening**: Full accessibility audit (WCAG AA), security audit (secret leak prevention, input sanitization), cross-browser responsiveness, performance benchmarking, and production build verification.

---

## 4. Standardized Repository Structure

The target repository structure evolves cleanly without premature file clutter:

```
Hydra/
├── .gitignore                     # Phase 0 (Created)
├── AGENTS.md                      # Phase 0 (Created)
├── README.md                      # Phase 0 (Created)
│
├── docs/                          # Architecture & Governance
│   ├── ARCHITECTURE.md            # Phase 0 (Created)
│   ├── ROADMAP.md                 # Phase 0 (Created)
│   └── DECISIONS.md               # Phase 0 (Created)
│
├── backend/                       # Python Backend (Phase 1+)
│   ├── pyproject.toml             # Phase 1: Dependencies & tool configs
│   ├── requirements.txt           # Phase 1: Pinned requirements (FastAPI, Pydantic, uvicorn, networkx, pytest)
│   ├── app/
│   │   ├── __init__.py            # Phase 1
│   │   ├── main.py                # Phase 1: FastAPI entrypoint
│   │   ├── api/                   # Phase 1: Canonical API routes & schemas
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health.py          # Phase 1: GET /api/health
│   │   │   │   ├── programmes.py      # Phase 1: GET /api/v1/programmes
│   │   │   │   └── recommendations.py # Phase 1: POST /api/v1/recommendations/evaluate
│   │   │   └── schemas/           # Phase 1: Pydantic request/response DTOs
│   │   │       ├── __init__.py
│   │   │       ├── student.py
│   │   │       ├── programme.py
│   │   │       └── recommendation.py
│   │   ├── core/                  # Phase 1: Config, CORS & logging
│   │   ├── domain/                # Phase 1-2: Domain frames (dataclasses)
│   │   │   ├── __init__.py
│   │   │   ├── student.py
│   │   │   ├── programme.py
│   │   │   └── institution.py
│   │   ├── knowledge/             # Phase 1-2: Semantic network & graph traversal
│   │   │   ├── __init__.py
│   │   │   ├── graph.py
│   │   │   └── traversal.py
│   │   ├── rules/                 # Phase 1-2: Deterministic rule engine & traces
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   └── traces.py
│   │   ├── services/              # Phase 1: Application orchestration services
│   │   │   ├── __init__.py
│   │   │   ├── evaluation.py
│   │   │   └── programme_service.py
│   │   ├── referee/               # Phase 1, 10: Central Referee coordinator
│   │   │   ├── __init__.py
│   │   │   └── referee.py
│   │   ├── agents/                # Phase 4-8: Specialised agents
│   │   │   ├── __init__.py
│   │   │   ├── twin.py            # Phase 4
│   │   │   ├── franchise.py       # Phase 5
│   │   │   ├── heist.py           # Phase 6
│   │   │   ├── simulator.py       # Phase 7
│   │   │   ├── boss_fight.py      # Phase 7
│   │   │   └── oracle.py          # Phase 8
│   │   └── engines/               # Phase 6-9: Planning, Simulation, ML & NLP
│   │       ├── __init__.py
│   │       ├── planner.py         # Phase 6: A* search
│   │       ├── simulation.py      # Phase 7: Branching scenarios
│   │       ├── stress_test.py     # Phase 7: Adversarial shocks
│   │       ├── forecasting.py     # Phase 8: Oracle cutoff regression
│   │       └── embeddings.py      # Phase 9: Interest decoder
│   └── tests/                     # Phase 1+: Pytest test suite
│       ├── unit/
│       │   ├── test_rules.py
│       │   ├── test_frames.py
│       │   └── test_knowledge.py
│       └── integration/
│           ├── test_api_health.py
│           ├── test_api_programmes.py
│           └── test_api_recommendations.py
│
├── frontend/                      # React Frontend (Phase 1+)
│   ├── package.json               # Phase 1
│   ├── tsconfig.json              # Phase 1
│   ├── vite.config.ts             # Phase 1
│   ├── tailwind.config.js         # Phase 1
│   ├── index.html                 # Phase 1
│   └── src/
│       ├── main.tsx               # Phase 1
│       ├── App.tsx                # Phase 1
│       ├── components/            # Phase 1: Accessible UI components
│       │   ├── ProfileForm.tsx
│       │   ├── ProgrammeCard.tsx
│       │   ├── EligibilityBadge.tsx
│       │   ├── AffordabilityBadge.tsx
│       │   └── TraceInspector.tsx
│       ├── api/                   # Phase 1: Typed API client (canonical endpoints)
│       ├── types/                 # Phase 1: Shared TypeScript interfaces
│       └── hooks/                 # Phase 1: Custom hooks
│
└── data/                          # Explicitly Labelled Data (Phase 1+)
    └── synthetic/                 # Phase 1: Demo catalog JSON/YAML (`is_synthetic: true`)

> **Phase 0 Boundary**: Only the documentation files, `.gitignore`, and engineering policies are created in Phase 0. Application code directories and modules are introduced in Phase 1 as part of the first vertical slice implementation.

---

## 3. Phase 2: Advanced Symbolic AI Core (Complete)

Phase 2 generalised and deepened Hydra's symbolic AI core while preserving 100% backward compatibility with Phase 1 APIs and catalogue models:

1. **Generalised Frame System (`backend/app/domain/frame_system.py`)**:
   - `FrameDefinition` & `FrameSlot`: Explicit types, default flags, and provenance tracking.
   - `MergePolicy`: `OVERRIDE`, `MERGE_UNIQUE` (deterministic sorted collection union), and `REQUIRE_CONSISTENCY`.
   - `FrameRegistry`: Validates parent references, resolves ancestor chains deterministically via topological BFS, and rejects inheritance cycles via DFS cycle detection (`_detect_cycle`).
   - `ConflictRecord`: Multi-parent competing values are detected, recorded, and arbitrated by child override or flagged as `needs_review`.
2. **Prerequisite Expression AST (`backend/app/rules/expressions.py`)**:
   - Atomic requirements: `SubjectScoreRequirement`, `EntranceRankRequirement`, `CertificationRequirement`.
   - Composite requirements: `AllOf` (conjunction) and `AnyOf` (disjunction) with Three-Valued Logic (`SATISFIED`, `VIOLATED`, `NEEDS_REVIEW`).
   - Supports alternative admission pathways, e.g., `(Math >= 80% AND Physics >= 75%) OR (JEE Main rank <= 15000)`.
3. **Advanced Semantic Network (`backend/app/knowledge/graph.py`)**:
   - Synchronizes `IS_A` edges directly from `FrameRegistry`.
   - Rejects cyclic `IS_A` insertions.
   - Enforces relationship provenance tagging (`direct`, `inherited`, `traversed`) with complete provenance paths.
4. **Hierarchical Explainability & UI Inspector (`frontend/src/components/reasoning/TraceInspector.tsx`)**:
   - Interactive tree vs flat rule toggling.
   - Visualizes composite operators (`ALL_OF`, `ANY_OF`), status badges, facts used, and provenance tags.
5. **Testing Verification**:
   - 72 passing backend tests (14 frames, 7 expressions, 9 graph, 22 rules, 14 API, 6 evaluation).
   - Zero compilation errors on frontend production build.

---

## 4. Phase 3 & 3.1: Admissions Knowledge Base and Data Provenance (Complete)

Phase 3 & 3.1 implemented an auditable, versioned admissions knowledge base:
1. **Source Registry & Verification**: SHA-256 artifact verification, row-level provenance, and structured quarantine ingestion pipeline.
2. **Decoupled Historical Cutoffs**: Historical cutoff observations with deterministic filtering and mandatory legal disclaimers. JoSAA cutoff records in the current normalized dataset are generated synthetic demonstration fixtures (`SRC_JOSAA_SYNTHETIC_FIXTURE_2026`, `is_synthetic: True`); real JoSAA opening/closing rank exports, seat matrix, and business rules remain unverified because automated retrieval failed due to remote NIC SSL handshake timeouts. Synthetic JoSAA cutoff records must never be interpreted as actual historical admissions outcomes.
3. **Verified Eligibility Criteria**: Authoritative JEE Advanced 2026 eligibility criteria were extracted from a genuine downloaded official HTML artifact with its verified SHA-256 checksum (`SRC_JEEADV_2026_ELIGIBILITY`).
4. **Provenance Integrity Audit (Phase 3.1)**: Reclassified test fixtures to prevent synthetic records from masquerading as official data; honest NIC SSL documentation.
5. **Testing Verification**: 86 passing backend tests; zero frontend build errors.

---

## 5. Phase 4 & 4.1: Twin Agent — Student Digital Twin Construction (Complete)

Phase 4 & 4.1 implemented Hydra's first functional intelligent agent:
1. **Deterministic 11-Step Transformation Pipeline**: Transforms raw `StudentProfileRequest` into an immutable `TwinSnapshot`.
2. **Typed Fact Provenance Taxonomy**: Distinguishes `USER_PROVIDED`, `DETERMINISTICALLY_DERIVED`, `EXTERNAL_VERIFIED`, and `UNKNOWN`.
3. **Server-Authorized CBSE Normalization**: Enforces server-side authority over grading scale conversion rules. CCE Class X (2009–2017) indicative 9.5 rule authorized; modern cohorts (2026) without authorized policy yield `NEEDS_REVIEW` per CBSE Rule 44 notice (30-Nov-2023).
4. **Tri-State Geographic Classification**: `NOT_PROVIDED` (neutral), `PREFERRED_LOCATIONS`, and `ANYWHERE_IN_INDIA`.
5. **Universal Deep Recursive Immutability**: All nested dictionaries and collections recursively frozen via `MappingProxyType` and `tuple`.
6. **Snapshot Identity & Concurrency Safety**: Multi-threaded execution (`ThreadPoolExecutor`) verified with isolated dynamic student frames and pristine `FRAME_STUDENT_BASE` slots.
7. **Semantic Graph Forward Direction**: Directed edge semantics (`Programme -> Career`) strictly preserved during reverse queries.
8. **Interactive UI Twin Inspector**: Full-featured React tabbed inspector with completeness overview, academic highlights disclaimers, semantic pathways, and fact provenance tables.
9. **Testing Verification**: 144 passing backend tests; clean frontend production build (`tsc -b && vite build`).

---

## 6. Phase 5: Franchise Agents & Simulated Auction (M002 — Complete)

Phase 5 implemented the society of institutional franchise agents representing individual academic programmes:
1. **Programme Franchise Society**: Autonomous `FranchiseAgent` instances constructed per programme.
2. **Suitability Bidding Protocol**: Evaluates multi-criteria alignment (academic preparation, career synergy, capacity match, geographic preference) producing structured `FranchiseBid` DTOs.
3. **Dynamic Weight Renormalization**: Evaluates heuristic weights dynamically across present profile dimensions (`v1.0`), preventing silent score deflation when optional fields are omitted.
4. **Deterministic Simulated Auction Engine**: Executes second-price / multi-criteria simulated auction with deterministic tie-breaking and explicit `NO_BID` exclusion for disqualified candidates.
5. **Interactive UI**: `FranchiseAuctionView.tsx` with bid rankings, component weight visualizers, and programme pitches.
6. **Testing Verification**: 19 dedicated unit/integration tests in `test_franchise.py`.

---

## 7. Phase 6: Heist Planner using A* (M003 — Complete)

Phase 6 implemented forward state-space search for remediation of prerequisite gaps:
1. **Immutable Planning State**: `PlanningState` instances with sorted condition fingerprints, tracking satisfied vs unsatisfied requirements.
2. **Mathematically Proven Admissible Heuristic**: Implemented $h_{\max}(n) = \max_{c \in U(n)} \min_{a \in A_c} \text{cost}(a)$ and $h_{\text{AnyOf}} = \min_b h(b)$, mathematically proving admissibility ($h(n) \le h^*(n)$) and eliminating multi-condition overestimation flaws. Dijkstra fallback ($h(n) = 0$) verified.
3. **A* Search Engine**: Forward search over action libraries (bridge courses, entrance exams, certification programs) with priority queue (`heapq`), closed-set cycle detection, and parent backtracking.
4. **Interactive UI**: `HeistPlannerView.tsx` visualising multi-phase remedial roadmaps, alternative pathway branches, effort/duration budgets, and post-plan eligibility projections.
5. **Testing Verification**: 13 dedicated unit tests in `test_planner.py` covering shared actions, nested OR branches, and zero-cost transitions.

---

## 8. Phase 7: Simulator & Boss-Fight Agent (M004 — Complete)

Phase 7 delivered counterfactual sensitivity simulation and adversarial stress testing:
1. **Isolated Memory Clones**: Clones student frame in memory without mutating base `TwinSnapshot`.
2. **Domain Boundary Enforcement**: Monte Carlo simulation enforces physical bounds: rank $\ge 1$ integer, board scores clamped $[0, 100]$, budget $\ge 0$, tuition $\ge 0$.
3. **Statistical Monotonicity**: Empirical quantile calculation guaranteeing $p10 \le p50 \le p90$, positive semi-definite covariance checks ($\lambda_{\min} \ge 0$), and explicit `is_empirical: False` hypothetical tagging.
4. **6-Attack Adversarial Battery**: `BossFightAgent` subjects plans and proposals to 6 standard perturbations (`RANK_WORSENS`, `TUITION_HIKED`, `BUDGET_REDUCED`, `CUTOFF_STIFFENS`, `DOCUMENT_UNOBTAINABLE`, `PREFERENCE_SHIFTS`).
5. **Surviving Alternative Discovery**: Identifies robust fallback programmes when the target programme fails under stress.
6. **Interactive UI**: `SimulatorBossFightView.tsx` with parameter sliders, distribution charts, vulnerability badges, and stress-test audit cards.
7. **Testing Verification**: 12 dedicated tests in `test_simulation.py`.

---

## 9. Phase 8: Oracle Agent & Admissions Cutoff Forecasting (M005 — Complete)

Phase 8 delivered historical admissions cutoff regression and time-series forecasting:
1. **Data Readiness Gate**: `DataReadinessValidator` strictly inspects observation datasets, rejecting 100% of `synthetic_demo` and `unverified` records. Returns explicit `INSUFFICIENT_VERIFIED_DATA` when authentic historical cutoffs are lacking.
2. **Transparent ML Regression**: Ordinary Least Squares (OLS) lag regression with chronological temporal train/test split.
3. **Calibrated Prediction Intervals**: Reports $[p10, p90]$ prediction intervals alongside baseline medians, documenting standard normal $z_{0.05} = 1.645$ assumptions.
4. **Interactive UI**: `OracleForecastView.tsx` with data readiness diagnostic banners, historical cutoff series inspectors, and uncertainty range visualizations.
5. **Testing Verification**: 11 dedicated tests in `test_oracle.py`.

---

## 10. Phase 9: Neural Interest Decoder & GNN Assessment (M006 — Complete)

Phase 9 delivered natural language student interest narrative decoding:
1. **Dual-Engine Architecture**:
   - Primary: `fastembed` ONNX `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense embeddings, 22.7M parameters) running locally on CPU.
   - Baseline Fallback: `LexicalHashingEncoder` (128-dimensional character n-gram hashing on unit hypersphere) for deterministic fallback (`force_lexical=True`).
   - Operational Status: Reports `READY_NEURAL`, `FALLBACK_TO_LEXICAL`, or `UNAVAILABLE`.
2. **Tripartite Lifecycle**: Enforces `STUDENT_STATED` -> `MODEL_SUGGESTED` -> `USER_CONFIRMED` lifecycle to prevent unauthorized mutation of the student digital twin.
3. **Formal GNN Evidence Gate**: Formally evaluated against Section 10.10 criteria; rejected due to small graph size (<35 nodes) and lack of authentic multi-institution outcome data, preventing catastrophic overfitting. Symbolic NetworkX traversal maintained.
4. **Interactive UI**: `InterestDecoderView.tsx` with interactive text narrative input, concept similarity ranking, and confirmation controls.
5. **Testing Verification**: 13 dedicated tests in `test_interest_decoder.py`.

---

## 11. Phase 10: Central Referee Multi-Agent Orchestration & Validation Sprint (M007 — Complete)

Phase 10 implemented central multi-agent arbitration and completed the post-M007 technical validation sprint:
1. **Central Multi-Agent Arbitration**: `RefereeAgent` orchestrates all 6 agents (Twin, Franchise, Oracle, Heist Planner, Simulator, Boss-Fight), synthesising proposals into a single coherent decision bundle.
2. **9-Tier Decision Hierarchy**:
   1. Verified Formal Mandatory Rules
   2. Verified External Evidence
   3. Student-Provided Information (Explicitly Labeled)
   4. Deterministically Derived Facts
   5. Advisory Historical Observations
   6. Predictions with Uncertainty
   7. Hypothetical Simulation Scenarios
   8. Synthetic Demonstration Fixtures
   9. Unknown Facts (yields `needs_review`)
3. **Stale Snapshot & Envelope Integrity**: Verifies SHA-256 fingerprint consistency between `snapshot_id` and raw profile data, rejecting stale or cross-student snapshots with HTTP 400. Validates structured `AgentResponseEnvelope` from all participating agents.
4. **Mandatory Rule Override Protection**: Formally guarantees that positive auction bids or favorable ML forecasts cannot override mandatory prerequisite violations.
5. **Complete System Verification**:
   - 226 passing backend tests across all modules (`pytest`).
   - Clean frontend production build (1,606 modules transformed, 0 TypeScript errors).
   - All 9 views fully wired and interactive in the React application.