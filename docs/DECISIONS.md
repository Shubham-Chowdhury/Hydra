# Hydra Architecture Decision Records (ADRs)

**System Name**: Hydra  
**Status**: Phase 0 Baseline  
**Document Purpose**: Document significant technical decisions, considered alternatives, rationale, and consequences.

---

## ADR-001: Domain Frames Implemented as Python Dataclasses with Pydantic Boundary DTOs

### Context
Hydra requires a structured symbolic representation for academic entities (students, programmes, institutions, requirements) supporting slot access, inheritance, and fast in-memory operations. At the same time, FastAPI requires strict request/response serialization and schema generation.

### Decision
- **Internal Domain Frames**: Use standard Python `dataclasses` (with slots and type annotations) in `backend/app/domain/` for internal domain logic, graph attachments, and rule evaluations.
- **Boundary DTOs**: Use Pydantic models exclusively at the API boundary in `backend/app/api/schemas/` for incoming request parsing and outgoing JSON serialization.

### Alternatives Considered
1. *Pydantic for everything*: High overhead for recursive graph traversals and slot manipulation; tightly couples domain logic to validation framework.
2. *Raw Python dicts*: Lacks static type checking, auto-completion, and enforces no slot schema.

### Consequences
- **Positive**: Clean separation of internal domain logic from external transport schemas. Fast in-memory operations without framework overhead.
- **Negative**: Requires explicit mapping functions between Pydantic DTOs and domain dataclasses.

---

## ADR-002: NetworkX for the Semantic Network (Phase 1 Baseline & Phase 2 Expansion)

### Context
Hydra models typed relationships among programmes, institutions, prerequisites, skills, and careers. The graph must support directed edges, relationship attributes, pathfinding, and subgraph extraction.

### Decision
Use **NetworkX** (`MultiDiGraph`) in `backend/app/knowledge/graph.py` as the semantic network implementation, paired with bounded traversal algorithms in `backend/app/knowledge/traversal.py`.
- **Phase 1**: Implement a minimal NetworkX graph representing synthetic programmes, required skills, and downstream careers, with at least one genuine graph traversal returning discovered relationships in `POST /api/v1/recommendations/evaluate`.
- **Phase 2**: Expand graph reasoning with multi-hop prerequisite chaining, ontology traversal, and cycle detection.

### Alternatives Considered
1. *Neo4j / Graph Database*: Requires running an external database daemon, adds deployment overhead, authentication, and network latency during in-memory reasoning.
2. *Custom Adjacency List*: Reinvents graph algorithms (Dijkstra, DFS, topological sort, cycle detection).
3. *RDF / SPARQL triple store (rdflib)*: Unnecessary syntactic and semantic complexity for the prototype's requirements.

### Consequences
- **Positive**: Lightweight, pure Python, zero external daemons, rapid in-memory traversal, native integration with Python data structures. Included directly in Phase 1 dependencies.
- **Negative**: Graph must fit in RAM (acceptable for tens of thousands of academic nodes in this scope). If scale reaches millions of nodes, migration to a graph database will be evaluated.

---

## ADR-003: Deterministic Rule Engine with Immutable Audit Traces

### Context
Admissions eligibility checks must be verifiable, explainable, and accountable. Black-box ML models or opaque boolean logic cannot provide the necessary auditability for academic decision support.

### Decision
Implement a pure, transparent **IF–THEN Rule Engine** in Python. Every rule evaluation generates an immutable `InferenceTrace` containing:
- Specific rule ID and name.
- Input facts inspected and their values.
- Boolean evaluation outcome.
- Plain-language justification string.
- List of missing or violated facts.

### Alternatives Considered
1. *External Business Rule Management System (e.g., Drools)*: Massive JVM dependency, extreme complexity.
2. *Ad-hoc IF statements scattered in controllers*: Impossible to trace, verify, or extract explanations uniformly.
3. *LLM-driven eligibility prompts*: Non-deterministic, prone to hallucinations, cannot guarantee institutional compliance.

### Consequences
- **Positive**: 100% deterministic, testable, verifiable, and directly generates explainability artifacts for students and advisors.
- **Negative**: Rules must be authored and maintained as structured code entities.

---

## ADR-004: Three-State Eligibility Decoupled from Affordability and Preference Fit

### Context
Students often conflate being academically qualified with being able to afford a programme or having high interest in it. Furthermore, incomplete application data or incompatible grading schemes often lead naive systems to issue false negatives or false positives.

### Decision
1. **Three Eligibility States**:
   - `eligible`: All mandatory requirements explicitly satisfied with verified positive evidence in compatible grading scales.
   - `ineligible`: At least one mandatory requirement explicitly violated.
   - `needs_review`: One or more mandatory requirements have missing or ambiguous data, or grading scales cannot be compatibly compared. **Missing facts or incompatible scales are never interpreted as eligible.**
2. **Decoupled Evaluation Dimensions**:
   - `Academic Eligibility`: Pure deterministic evaluation of prerequisites, grades, and entrance ranks.
   - `Affordability`: Independent comparison of student `total_budget_inr` against programme `estimated_total_tuition_inr` (labeled `cost_basis: "tuition_only_total"`). An applicant can be `eligible: true` but `is_affordable: false`.
   - `Preference Fit`: Independent heuristic alignment score $[0.0, 1.0]$ based on preferred disciplines and target careers.

### Alternatives Considered
1. *Single Aggregate Score (e.g., 0-100)*: Conflates financial inability with academic disqualification; lacks transparency.
2. *Binary Eligible/Ineligible*: Fails when transcript data is incomplete, creating misleading outcomes.
3. *Implicit Currency Conversion*: Introducing undocumented dynamic FX conversions creates unpredictable affordability judgments.

### Consequences
- **Positive**: High fidelity, transparent decision states; protects students from false assumptions when profile data is incomplete; keeps financial and academic gates clearly separated.
- **Negative**: Requires the UI to present multi-dimensional status indicators clearly.

---

## ADR-005: Central Referee for Multi-Agent Orchestration

### Context
Hydra contains six specialised agents (Twin, Franchise, Oracle, Heist Planner, Simulator, Boss-Fight). Allowing direct, unconstrained peer-to-peer communication risks circular dependencies, state desynchronization, and untraceable reasoning.

### Decision
All multi-agent communication is mediated by the **Central Referee**. Agents do not invoke each other directly. The Referee:
1. Dispatches read-only snapshots to agents.
2. Collects structured proposals and bids.
3. Cross-examines proposals against the Rule Engine and Knowledge Graph.
4. Identifies contradictions and flags uncertainties.
5. Emits the final unified decision bundle.

### Alternatives Considered
1. *Peer-to-peer Agent Mesh*: Hard to debug, non-deterministic execution order, potential deadlock/race conditions.
2. *Shared Blackboard with Global State*: Mutable global state risks race conditions and breaks functional purity.

### Consequences
- **Positive**: Clear audit trail, deterministic coordination, clean separation of concerns, testable agent modules.
- **Negative**: Referee logic must be maintained as the central coordinator.

---

## ADR-006: Frontend-Backend Boundary, Request Flow, and Dependency Direction

### Context
Modern web architectures must decide where domain logic and business rules reside, and how runtime execution differs from code dependency structures.

### Decision
1. **Inference Authority**: The Python FastAPI backend is the **sole authority** for inference, rule evaluation, graph traversal, and agent coordination. The React frontend is strictly a presentation and interaction layer.
2. **Runtime Request Flow**:
   React Frontend → FastAPI Routers (`app/api/v1/`) → Application Services (`app/services/`) → Domain Reasoning & Knowledge (`app/domain/`, `app/knowledge/`, `app/rules/`, `app/referee/`) → Structured DTO Response → React UI.
3. **Compile-Time Code Dependency Principle**:
   Dependencies are strictly inward-only. Domain frames (`app/domain/`), rule evaluation (`app/rules/`), and semantic networks (`app/knowledge/`) must NEVER import FastAPI, Starlette, HTTP request objects, or frontend-specific types.
4. **Cohesive Module Design**:
   Avoid sprawling abstractions or empty placeholder modules. The codebase will use a small number of cohesive, understandable modules.

### Alternatives Considered
1. *Shared logic in TypeScript/WebAssembly*: Duplicates rule engines, creates synchronization bugs and security risks.
2. *Full server-rendered UI (e.g., Jinja2)*: Poor interactive experience for graph exploration and multiverse scenarios.
3. *Ad-hoc framework imports in domain*: Directly importing FastAPI request objects in rule evaluators breaks testability and portability.

### Consequences
- **Positive**: Zero rule duplication, consistent enforcement, secure and easily testable business logic with pure unit tests.
- **Negative**: Interactive UI updates requiring re-evaluation require network requests to the API.

---

## ADR-007: Phased Dependency Strategy

### Context
Hydra will eventually use scikit-learn, sentence-transformers, PyTorch, and graph visualizers. Installing all dependencies upfront bloats the environment, introduces binary conflicts, and slows down early development.

### Decision
Dependencies are introduced strictly on a **phase-by-phase basis** aligned with the canonical 11-phase roadmap:
- **Phase 0**: Zero application dependencies; documentation, engineering contract, and configuration only.
- **Phase 1**: Core backend (FastAPI, Pydantic, uvicorn, NetworkX, pytest) + core frontend (React, TypeScript, Vite, Tailwind CSS).
- **Phase 2**: Generalized symbolic inheritance, multi-rule priority chaining, and advanced graph reasoning tools.
- **Phase 3**: Admissions catalog validation and data provenance logging.
- **Phase 4**: Twin Agent profile models and transcript normalization.
- **Phase 5**: Franchise Agent suitability bidding protocol.
- **Phase 6**: A* search and planning algorithms.
- **Phase 7**: Simulation counterfactual engine and adversarial stress-testing harness.
- **Phase 8**: scikit-learn, pandas (Oracle historical admissions cutoff forecasting).
- **Phase 9**: sentence-transformers, PyTorch (Interest Decoder NLP embeddings; optional GNN).
- **Phase 10**: Production hardening, security scanning, and end-to-end audit tools.

### Consequences
- **Positive**: Lean initial footprint, fast installs, clear tracking of dependency rationale.
- **Negative**: Requires incremental dependency updates in later phases.

---

## ADR-008: Windows Environment Strategy (Python 3.13 via Launcher, npm.cmd)

### Context
The environment audit identified that:
1. The default `python` in PATH resolves to MSYS2 Python 3.14 which lacks `pip`.
2. Python 3.13.15 is installed with `pip 26.2.1` and accessible via `py -3.13`.
3. PowerShell restricts execution of `.ps1` scripts, blocking direct `npm` wrapper scripts.

### Decision
1. **Python**: All Python commands must use the Python launcher targeting 3.13: `py -3.13 -m venv .venv`. Once activated, `.venv\Scripts\python.exe` is the standard runtime.
2. **Node/npm**: Frontend package operations must use `npm.cmd` or run with execution policy bypass.

### Consequences
- **Positive**: Avoids broken MSYS2 Python 3.14; avoids PowerShell execution policy errors; guarantees reproducible builds.
- **Negative**: Documented convention must be consistently followed by developers and agents on Windows.

---

## ADR-009: Canonical API Contracts and Routing Layout

### Context
To prevent endpoint fragmentation and ensure contract stability across frontend and backend implementations, canonical API routes must be standardized upfront.

### Decision
Enforce three canonical API endpoints:
1. `GET /api/health`: Health and service liveness check.
2. `GET /api/v1/programmes`: Programme catalogue retrieval with synthetic demonstration tags and provenance metadata.
3. `POST /api/v1/recommendations/evaluate`: Student profile evaluation accepting `StudentProfileRequest` (academic subject scores with `grading_scale`, `entrance_exam_name`, `entrance_rank`, `preferred_locations`, `total_budget_inr`, `preferred_disciplines`, `career_goals`) and returning `EvaluationResponse` (programme evaluations, eligibility status `eligible`/`ineligible`/`needs_review`, affordability on total duration INR tuition basis, preference fit $[0.0, 1.0]$, evidence, rule IDs, human-readable reasoning traces, graph-discovered relationships, runtime UTC audit timestamp, and synthetic provenance).

No alternative evaluation endpoints (such as `/api/v1/evaluate` or `/api/v1/recommend`) are permitted without explicit documented justification and complete document synchronization.

### Consequences
- **Positive**: Predictable, stable contracts between frontend API client and FastAPI routers; avoids endpoint divergence; ensures frontend remains strictly presentational.
- **Negative**: All consumers must conform to the `/api/v1/recommendations/evaluate` payload structure.

---

## ADR-010: India-Focused Synthetic Demonstration Dataset and INR Currency Semantics

### Context
Admissions decision-support prototypes require concrete domain grounding. Using vague, inconsistent currencies or mixing disparate admission models (e.g. US GPA vs. Indian entrance exams) causes confusion, ungrounded comparisons, and fragile reasoning rules.

### Decision
1. **Regional Context & Currency**: All Phase 1 synthetic demonstration programmes and student profiles are India-focused and use **INR** (`total_budget_inr`, `annual_tuition_inr`, `estimated_total_tuition_inr`).
2. **Explicit Cost Basis**: Affordability strictly compares `total_budget_inr` against `estimated_total_tuition_inr` for the entire programme duration, explicitly tagged as `cost_basis: "tuition_only_total"`. No undocumented currency conversions are allowed.
3. **No Fabrication of Real Universities**: All institutional names are explicitly synthetic and fictional (e.g., "Demo Institute of Technology, Bengaluru", "Synthetic College of Engineering, Hyderabad"). Never invent cutoffs or policies for real institutions (such as IITs, NITs, BITS).
4. **Mandatory Provenance Metadata**: Every demonstration record carries `is_synthetic: true`, `dataset_label: "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"`, and `provenance: "SYNTHETIC_DEMO_RECORD_V1"`.
5. **Grading Scale Normalization Guard**: Incompatible grading systems (e.g., percentage vs. 10-point CGPA) must not be silently compared. Without an explicit verified conversion rule, evaluations must yield `needs_review`.

### Alternatives Considered
1. *Multi-currency USD/EUR/INR in Phase 1*: Adds unnecessary complexity with exchange-rate volatility and temporal mismatch before core reasoning is verified.
2. *Scraping or fabricating real university admission cutoffs*: Violates zero-fabrication directives and risks misleading users.

### Consequences
- **Positive**: Clean, unambiguous currency and admissions criteria; realistic Indian engineering pathway modeling (12th Board percentages + entrance exams like JEE Main); transparent synthetic disclosure.
- **Negative**: Official university datasets and international currency conversions are deferred to Phase 3.

---

## ADR-011: Generalised Frame System with Slot Resolution, Conflict Arbitration, and Merge Policies (Phase 2)

### Context
Phase 1 used simple Python dataclasses with direct field access. To scale to complex academic taxonomies with multiple inheritance, domain templates, default values, and conflicting affiliations, Hydra requires a generalized frame-based knowledge representation system.

### Decision
Implement `FrameDefinition`, `FrameSlot`, and `FrameRegistry` in `backend/app/domain/frame_system.py`:
1. **Topological Ancestor Resolution**: Resolves inherited slots breadth-first across parent frames with parent-order independence.
2. **Merge Policies**: Explicit child `OVERRIDE`, collection union under `MERGE_UNIQUE`, and `REQUIRE_CONSISTENCY` for scalar integrity.
3. **Explicit Conflict Tracking**: Multi-parent competing values are recorded in `ConflictRecord`. Explicit child overrides mark conflicts resolved; unresolved decision-relevant conflicts yield `needs_review`.
4. **Cycle Rejection**: Rejects cyclic inheritance definitions using depth-first search (`_detect_cycle`).

### Consequences
- **Positive**: Expressive symbolic knowledge representation, deterministic multiple inheritance, clean provenance audit trails.
- **Negative**: Requires resolving slots through registry rather than direct raw dictionary indexing.

---

## ADR-012: Prerequisite Requirement Expression AST and Three-Valued Logic (Phase 2)

### Context
Admissions policies often contain complex alternative pathways (e.g. 12th Board marks OR national entrance rank), conjunctions, and certifications. Flat lists of mandatory prerequisites cannot represent disjunctive choices or nested logical conditions without code duplication.

### Decision
Implement an Abstract Syntax Tree (AST) for prerequisite expressions in `backend/app/rules/expressions.py`:
1. **Atomic Nodes**: `SubjectScoreRequirement`, `EntranceRankRequirement`, `CertificationRequirement`.
2. **Composite Nodes**: `AllOf` (conjunction) and `AnyOf` (disjunction).
3. **Deterministic Three-Valued Logic**: `SATISFIED`, `VIOLATED`, `NEEDS_REVIEW`. In `AnyOf`, satisfying any alternative satisfies the rule; in `AllOf`, a single mandatory violation causes `VIOLATED`.
4. **Hierarchical Trace**: Produces `ReasoningTreeNode` for rich tree visualization, while flattening leaf records for 100% backward compatibility.

### Consequences
- **Positive**: Expressive representation of real-world admission pathways; complete explainability down to atomic facts.
- **Negative**: Evaluation tree traversal requires recursive handling in API DTOs and UI inspectors.

---

## ADR-013: NetworkX Graph Synchronization from Frame Registry with Relationship Provenance (Phase 2)

### Context
In Phase 1, graph nodes were populated directly from programme frames. In Phase 2, `IS_A` inheritance relationships originate from the authoritative `FrameRegistry`. To prevent divergence between frame inheritance and semantic graph traversal, the graph must synchronize from the registry.

### Decision
1. `HydraKnowledgeGraph.sync_from_frame_registry()` creates `IS_A` edges directly from `FrameRegistry`, enforcing directed cycle prevention.
2. `discover_pathways()` tags every discovered relationship with its origin `source_type`:
   - `direct`: edge directly attached to the programme node.
   - `inherited`: relationship cascading down from an ancestor frame via `IS_A`.
   - `traversed`: downstream multi-hop hop (e.g., Skill $\rightarrow$ Career).
3. Every discovered relationship carries a `provenance_path` array detailing the traversal sequence.

### Consequences
- **Positive**: Single source of truth for taxonomy; explicit visual provenance in UI; zero divergence between graph and frame hierarchy.
- **Negative**: Graph synchronization step required during service initialization.

---

## ADR-014: Decoupling Historical Cutoffs from Deterministic Eligibility Rules (Phase 3)

### Context
Admissions data systems often confuse historical closing ranks with mandatory eligibility prerequisites. A historical closing rank is an observed allocation boundary from past counselling rounds, highly dependent on cohort size, seat pools, categories, and applicant preferences. It does not represent an absolute eligibility requirement or a guarantee of future admission.

### Decision
1. Strictly decouple historical cutoffs (`AdmissionCutoffObservation`) from the deterministic symbolic rule engine.
2. Historical cutoffs are exposed exclusively via query endpoints (`/api/v1/admissions/cutoffs`) with a mandatory disclaimer:
   *"Historical cutoff observations describe past counselling outcomes. They do not guarantee future admission."*
3. Formal eligibility criteria (`FormalEligibilityCriterion`) from official authorities (e.g. JEE Advanced Office) are maintained separately as verified prerequisite rules.
4. Historical cutoffs are never injected into the student eligibility AST.

### Consequences
- **Positive**: Preserves epistemic integrity; prevents false negatives where qualified applicants are declared ineligible based on historical market clearing ranks; aligns with real-world Indian university admissions.
- **Negative**: Requires educating users that historical cutoffs provide competitive context rather than binary qualification verdicts.

---

## ADR-015: Four-Tier Admissions Data Provenance and Snapshot Immutability (Phase 3)

### Context
Hydra integrates data from diverse sources including official government websites, published counselling spreadsheets, and synthetic test catalogues. The system must prevent unverified or synthetic records from being presented as verified official facts.

### Decision
1. Enforce a typed 4-tier provenance classification across all admission records:
   - `official_source`: Primary verified artifacts directly retrieved from official bodies with SHA-256 hashes.
   - `derived_from_official`: Normalized records directly traced through ingestion snapshots to authentic official source documents.
   - `synthetic_demo`: Explicitly synthetic records (`is_synthetic: True`) for testing and demonstrations.
   - `unverified`: Registered portal endpoints whose remote artifacts could not be retrieved due to network constraints.
2. Implement immutable `DatasetSnapshot` records tracking source checksums, record counts, and parser versions.
3. Partition invalid or anomalous rows into structured quarantine files (`data/quarantine/*.jsonl`) with machine-readable rule codes (`VAL_REQ_INSTITUTION`, `VAL_RANK_NON_POSITIVE`, `VAL_RANK_ORDER_INVERTED`, `VAL_DUPLICATE_RECORD`).

### Consequences
- **Positive**: Complete auditability down to the source row and artifact hash; zero silent data loss; explicit quarantine for defective rows.
- **Negative**: Requires maintaining manifests and snapshot metadata across import runs.


---

## ADR-009: Phase 3.1 Provenance Integrity Invariants, JoSAA Fixture Reclassification, and Examination Eligibility Scope

### Status
Accepted (Phase 3.1)

### Context
In Phase 3, `josaa_orcr_fixture_round1_2026.csv` was generated as a local test fixture because automated access to `https://josaa.nic.in` encountered NIC SSL handshake timeouts. However, the fixture records were initially classified as `source_status: "derived_from_official"` and `is_synthetic: false` with source ID `SRC_JOSAA_FIXTURE_2026`, which included an IIT Bombay Computer Science and Engineering record with rank 67. Presenting a synthetic test fixture as official or derived-from-official violated Hydra's fundamental zero-fabrication and provenance integrity mandates. Additionally, extracted JEE (Advanced) 2026 eligibility rules required explicit scoping to clarify they govern examination appearance, not institutional degree admission.

### Decision
1. **Reclassify JoSAA Test Fixture**:
   - Reclassified `SRC_JOSAA_FIXTURE_2026` to `SRC_JOSAA_SYNTHETIC_FIXTURE_2026`.
   - Set `source_status = SourceStatus.SYNTHETIC_DEMO` and `is_synthetic = True` across the source manifest and all normalized cutoff observations.
   - Preserved `https://josaa.nic.in` endpoints as explicitly `unverified` due to remote NIC SSL handshake timeouts.
2. **Enforce Strict Provenance Invariants**:
   - A record can only claim `derived_from_official` if it links to an authentic `official_source` document with a verified original file and matching SHA-256 checksum.
   - Synthetic records (`is_synthetic: True`) are structurally prohibited from claiming `official_source` or `derived_from_official`.
   - Implemented `ProvenanceInvariantValidator` and domain `__post_init__` checks to enforce these rules.
3. **Explicit Scope for JEE (Advanced) 2026 Eligibility Criteria**:
   - Added `criterion_scope: "exam_appearance_eligibility"` and `target_examination: "JEE (Advanced)"` to `FormalEligibilityCriterion`.
   - Explicitly clarified in API and UI that these criteria govern candidate eligibility to appear for the JEE (Advanced) examination, not degree admission or seat allocation.
4. **Unmistakable UI Labelling**:
   - Added prominent warning banners and badges in `AdmissionsEvidenceView.tsx` distinguishing synthetic demonstration fixtures from verified official records.

### Consequences
- **Positive**: Synthetic test fixtures can never masquerade as verified official outcomes; JoSAA network limitations are honestly documented; provenance invariants are enforced at compile and runtime; JEE Advanced rules are correctly scoped.
- **Negative**: None. All 108 existing tests and 7 new regression tests pass without regression.

---

## ADR-010: Student Digital Twin Construction and Multidimensional Completeness Engine (Phase 4)

### Status
Accepted (Phase 4)

### Context
Hydra requires a structured, explainable, and versioned digital representation of a student profile to serve as the unified context provider for specialised agents (Franchise, Oracle, Heist Planner, Simulator, Boss-Fight, and Central Referee). Crucially, the system must distinguish what the student directly provided (`USER_PROVIDED`), what Hydra deterministically derived (`DETERMINISTICALLY_DERIVED`), what is verified external evidence (`EXTERNAL_VERIFIED`), and what remains unstated or unknown (`UNKNOWN`). Under no circumstances may an agent invent facts, fabricate percentile bands, speculate unattempted entrance ranks, or conflate profile completeness with programme eligibility.

### Decision
1. **Typed Fact Provenance & Origin Taxonomy**:
   - Model all atomic student profile attributes as immutable `FactRecord` instances with explicit `origin_category` (`USER_PROVIDED`, `DETERMINISTICALLY_DERIVED`, `EXTERNAL_VERIFIED`, `UNKNOWN`), `validation_status` (`VALID`, `NEEDS_REVIEW`, `INVALID`, `MISSING`), input dependency references, derivation rules, and plain-language explanations.
2. **Conservative Grading Scale Normalization**:
   - `percentage`: Valid for $[0, max\_score]$, normalized via standard percentage ratio.
   - `marks_obtained_out_of_total`: Normalized via explicit marks ratio rule `MARKS_RATIO_NORMALIZATION`.
   - `cbse_10_point`: Converted strictly via the official CBSE formula $\text{Percentage} = \text{CGPA} \times 9.5$, with derivation rule `CBSE_CGPA_X_9_5`.
   - Unsupported scales (e.g. US 4-point GPA, letter grades): Normalized percentage set to `None`, validation status set to `NEEDS_REVIEW`, preserving the raw score while mandating manual transcript audit.
   - Out-of-bounds scores: Marked `INVALID`.
3. **Zero Predictive Rank Speculation**:
   - If an entrance examination rank is unprovided or absent, record `rank = None` and `missing_details = ["entrance_rank"]`.
   - Prohibit speculative rank estimation or percentile projection in the Twin Agent.
4. **Multidimensional Completeness Engine**:
   - Calculate completeness across 5 independent dimensions: `academic`, `entrance_exam`, `financial`, `geographic`, and `interests_and_career`.
   - Decouple completeness from eligibility: an applicant can have a `COMPLETE` twin yet be `INELIGIBLE` for a programme (due to unmet prerequisite minimums), or have a `PARTIAL` twin yet be `ELIGIBLE` (e.g., for programmes with no entrance cutoff requirements).
5. **Frame System & Semantic Network Integration**:
   - Introduce `FRAME_STUDENT_BASE` in `FrameRegistry` providing inherited defaults (`currency: INR`, `cost_basis: tuition_only_total`, `status: active`).
   - Register instance frames `FRAME_STUDENT_{twin_id}` resolving explicit child slots against parent defaults with auditable provenance paths.
   - Traverse the NetworkX semantic graph to discover verified pathway edges connecting stated career goals and disciplines to programmes and skills.
6. **Deterministic Profile Fingerprinting**:
   - Generate canonical SHA-256 hash of sorted, normalized profile inputs to guarantee immutable, reproducible snapshot identifiers (`TWIN_{fingerprint[:12]}`).

### Consequences
- **Positive**: Strict factual auditability; total protection against generative hallucinations; transparent grading scale conversions; decoupled completeness and eligibility semantics.
- **Negative**: Profiles with non-standard transcripts require manual review rather than automated heuristic conversion.




