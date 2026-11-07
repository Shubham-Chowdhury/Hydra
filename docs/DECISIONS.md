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
- **Positive**: Synthetic test fixtures can never masquerade as verified official outcomes; JoSAA network limitations are honestly documented; provenance invariants are enforced at compile and runtime; JEE Advanced rules are correctly scoped. Crucial distinction enforced: JEE Advanced 2026 eligibility criteria are extracted from an authentic official HTML artifact with verified checksum, whereas JoSAA cutoff records are synthetic demo fixtures that must never be interpreted as real historical admissions outcomes.
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

---

## ADR-011: Twin Agent Semantic and Integrity Corrections (Phase 4.1)

### Status
Accepted (Phase 4.1)

### Context
Phase 4 established the Student Digital Twin construction engine. Prior to proceeding to Phase 5 (Franchise Agents & Auction), an exhaustive audit identified seven semantic, regulatory, and architectural refinements required to prevent misleading academic representations and strengthen system invariants:
1. **CBSE Regulatory Accuracy**: The universal application of `percentage = CGPA * 9.5` ignored CBSE Examination Bylaws Rule 44 and CBSE circular dated 30-Nov-2023 (`Calculation_Percentage_Class_X_XII_30112023.pdf`), which explicitly states that the Board does not declare official percentages or calculation rules; calculation is strictly at the discretion of the admitting institution or employer.
2. **Geographic Semantics**: A binary `is_unconstrained` flag conflated omitting location preferences (neutral) with affirmative intent to study anywhere in India.
3. **Academic Highlight Framing**: Labeling subjects with $\ge 75\%$ as "Academic Strengths" risked communicating an inference of general cognitive aptitude rather than a deterministic test-score threshold.
4. **Client Verification Integrity**: Client payloads could attempt to inject `is_verified: true` or external origin claims.
5. **Collection Immutability**: Frozen dataclasses allow shallow mutation of internal dicts and lists unless deeply protected.
6. **Frame Isolation**: Shared `FrameRegistry` must guarantee that dynamic student frames never contaminate `FRAME_STUDENT_BASE` or each other.
7. **Semantic Graph Traversal Orientation**: Ensure reverse query traversal preserves forward edge directions.

### Decision
1. **Server-Authorized CBSE Normalization & Trust Boundary**:
   - Introduce `AuthorizedConversionPolicy`, `AUTHORIZED_CONVERSION_POLICIES` registry, and `resolve_authorized_conversion_policy`.
   - Enforce server trust boundary: client input cannot self-authorize conversion policies. For historical CCE Class X cohorts (2009–2017), the indicative 9.5 multiplier is authorized under `CBSE_HISTORICAL_CCE_INDICATIVE`.
   - For modern cohorts (e.g. 2026), client attempts to pass conversion policies are rejected with `NEEDS_REVIEW` per CBSE Rule 44 circular (30-Nov-2023), as CBSE does not prescribe an official percentage formula. Raw CGPA is retained under `NEEDS_REVIEW` requiring manual transcript review.
2. **Geographic Tri-State Classification**:
   - Replace binary boolean assumptions with `GeographicPreferenceType`: `NOT_PROVIDED` (neutral, unfiltered), `PREFERRED_LOCATIONS` (user-specified list), and `ANYWHERE_IN_INDIA` (explicit nationwide confirmation).
3. **Score-Based Academic Highlights**:
   - Formally adopt `score_based_academic_highlights` backed by versioned heuristic constants (`SCORE_HIGHLIGHT_THRESHOLD = 75.0`, `HIGHLIGHT_HEURISTIC_VERSION = "1.0"`).
   - Retain `academic_strengths` as a backward-compatible alias.
   - Display clear UI disclaimers that highlights represent relative test scores, not cognitive aptitude.
4. **Server-Exclusive Fact Verification**:
   - Enforce `FactOriginCategory.USER_PROVIDED` on all student-reported entrance exam facts. Discard any client-injected verification flags or claims of external authority.
5. **Universal Deep Recursive Immutability**:
   - Implement `freeze_value` and `unfreeze_value`. In `TwinSnapshot.__post_init__` and `FactRecord.__post_init__`, recursively freeze all nested dictionaries into `MappingProxyType` and all lists/sets into `tuple`. In-place mutations on nested fact dicts, frame slots, or pathways raise `TypeError` or `AttributeError`.
6. **Snapshot Identity vs. Profile Fingerprint**:
   - Distinguish `profile_fingerprint` (SHA-256 hash of canonical sorted profile), `twin_id` (`TWIN_{fingerprint[:12]}` for profile representation), and `snapshot_id` (`SNAP_{fingerprint[:8]}_{timestamp_ms}` for each execution run).
   - `TwinService` caches snapshots in memory indexed by both `twin_id` and `snapshot_id`, preserving individual run history without unintentional overwrite.
7. **Frame System Isolation & Concurrency**:
   - Dynamic student frames register `FRAME_STUDENT_{snapshot_id}` (run isolation) and alias `FRAME_STUDENT_{twin_id}` (lookup compatibility). Multi-threaded concurrent constructions via `ThreadPoolExecutor` verify `FRAME_STUDENT_BASE` retains exactly 8 default slots with zero slot contamination.
8. **Directed Semantic Graph Edge Fidelity**:
   - Verify that discovered pathways maintain authentic forward edge directions (`Programme -[:LEADS_TO_CAREER]-> Career`, `Programme -[:RELATED_TO_DISCIPLINE]-> Discipline`) during reverse lookup, with zero mutation of the underlying NetworkX graph.

### Consequences
- **Positive**: Complete compliance with CBSE regulatory reality; strict trust boundary enforcement; truthful geographic intent representation; hardened fact provenance against client spoofing; deep recursive snapshot immutability; 140 passing backend tests; zero frontend build errors.
- **Negative**: Profiles providing CBSE CGPA without authorized historical context require explicit institutional policy authorization or manual transcript review.

---

## ADR-012: Franchise Agents Society and Deterministic Simulated Auction Protocol (Phase 5 / M002)

### Status
Accepted (Phase 5 / M002)

### Context
Hydra requires an agentic mechanism to represent individual academic programmes dynamically. Programmes need to bid for prospective students based on eligibility, multi-dimensional alignment, and capacity, without chaotic or non-deterministic auction outcomes.

### Decision
1. **Dynamic Agent Instantiation**: Instantiate lightweight `FranchiseAgent` instances dynamically per programme from canonical frames.
2. **Deterministic Multi-Stage Auction**: Proposals are partitioned into Unconditional, Conditional, and No-Bid tiers. Tie-breaking deterministically resolves on Affordability -> Academic Alignment -> Canonical Programme ID.
3. **Symbolic AST Rule Reuse**: Franchise agents reuse the symbolic `RuleEngine` directly rather than calculating shadow eligibility logic.

---

## ADR-013: State-Space A* Search for Admissions Pathway Planning (Phase 6 / M003)

### Status
Accepted (Phase 6 / M003)

### Context
When students encounter missing documents, unverified certificates, or complex `AnyOf` prerequisite pathways, they need an optimal action plan. Unbounded graph search or depth-first heuristics risk infinite loops or non-optimal suggestions.

### Decision
1. **Immutable Planning State**: Represent search nodes as immutable `PlanningState` instances with sorted condition fingerprints.
2. **Admissible Heuristic ($h_{\max}$)**: Implement $h_{\max}(n) = \max_{c \in U(n)} \min_{a \in A_c} \text{cost}(a)$, taking the minimum across `AnyOf` branches ($h_{\text{AnyOf}} = \min_{b} h(b)$). This mathematically guarantees $h_{\max}(n) \le h^*(n)$ (admissibility and optimality), eliminating the sum-of-minimums overestimation flaw when a single remedial action satisfies multiple unsatisfied conditions.
3. **Closed-Set Cycle Detection**: Enforce maximum depth (50) and expansion limits (1000) to guarantee bounded execution, alongside Dijkstra fallback ($h(n) = 0$).

---

## ADR-014: Counterfactual Sandboxing, Standardized 6-Attack Adversarial Stress Testing, and Monte Carlo Domain Bounds (Phase 7 / M004)

### Status
Accepted (Phase 7 / M004 & Post-M007 Sprint)

### Context
Prospective applicants need to evaluate sensitivity to real-world disruptions (rank slips, fee hikes, inflation). Ad-hoc parameter adjustments risk mutating the baseline student profile, and unconstrained random sampling risks producing nonsensical values (e.g., negative ranks, negative tuition, scores exceeding 100%).

### Decision
1. **Isolated Sandbox Memory Clones**: Counterfactual and Monte Carlo simulations clone the student frame in memory without touching the baseline `TwinSnapshot`.
2. **Domain Boundary Constraints**: Monte Carlo sampling strictly enforces physical academic domain boundaries: integer rank $\ge 1$, board scores clamped $[0, 100]$, budget $\ge 0$, and tuition $\ge 0$.
3. **Statistical Validity & Monotonic Quantiles**: Sample distributions compute empirical quantiles ($p10, p50, p90$) with mathematical guarantee of monotonicity ($p10 \le p50 \le p90$). Multivariable perturbations validate covariance matrices for positive semi-definiteness ($\lambda_{\min} \ge 0$).
4. **Hypothetical Demonstration Demarcation**: All simulation parameters and distributions are flagged `is_empirical: False` to prevent confusing hypothetical sensitivity with official historical empirical observations.
5. **6-Attack Standard Adversarial Battery**: `BossFightAgent` subjects candidate programmes to 6 perturbations (`RANK_WORSENS`, `TUITION_HIKED`, `BUDGET_REDUCED`, `CUTOFF_STIFFENS`, `DOCUMENT_UNOBTAINABLE`, `PREFERENCE_SHIFTS`).
6. **Surviving Alternative Discovery**: If the target programme fails, the agent automatically identifies surviving robust alternatives in the catalogue.

---

## ADR-015: Oracle Admissions Forecasting with Data Readiness Gating and Uncertainty Intervals (Phase 8 / M005)

### Status
Accepted (Phase 8 / M005)

### Context
Predicting admissions cutoffs requires genuine machine learning. However, synthetic fixtures or unverified remote portals must never be disguised as real predictions.

### Decision
1. **Data Readiness Gate**: `DataReadinessValidator` strictly inspects observations against checksums, official source statuses, and row provenance. Rejects 100% of `synthetic_demo` and `unverified` records.
2. **Transparent ML & Temporal Splitting**: Fits Ordinary Least Squares lag regression using chronological temporal splits (earlier years train, latest held-out year evaluates).
3. **90% Uncertainty Intervals**: Reports $[p10, p90]$ prediction intervals alongside baseline median comparisons.
4. **No Data, No Fake Predictions**: Returns explicit `INSUFFICIENT_VERIFIED_DATA` when authentic verified historical data is lacking.

---

## ADR-016: Dual-Engine Neural Sentence Embeddings with Lexical Hashing Fallback and Formal GNN Evidence Gate (Phase 9 / M006)

### Status
Accepted (Phase 9 / M006 & Post-M007 Sprint)

### Context
Free-text student statements need to be translated into canonical ontology concepts. The system requires genuine transformer-based neural sentence representations while retaining an offline CPU-compatible deterministic baseline. Additionally, the roadmap proposed an optional Graph Neural Network (GNN).

### Decision
1. **Dual-Engine Architecture**:
   - **Primary Neural Model**: Uses `fastembed` with ONNX runtime executing `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense embeddings, 22.7M parameters). Runs locally and quickly on CPU without PyTorch GPU dependencies.
   - **Baseline Fallback**: Retains `LexicalHashingEncoder` (128-dimensional character n-gram hashing on unit hypersphere) for deterministic, air-gapped fallback (`force_lexical=True`).
   - **Operational Status Reporting**: Explicitly exposes `READY_NEURAL`, `FALLBACK_TO_LEXICAL`, or `UNAVAILABLE`.
2. **Tripartite Lifecycle**: Enforces `STUDENT_STATED` -> `MODEL_SUGGESTED` -> `USER_CONFIRMED`. Guarantees zero silent mutation of the student digital twin.
3. **GNN Rejected at Evidence Gate**: Evaluated against Section 10.10 criteria. The academic knowledge graph has <35 nodes and lacks authentic multi-institution career outcome labels. Training a GNN would cause severe overfitting. Symbolic NetworkX traversal is maintained.

---

## ADR-017: Central Referee Multi-Agent Arbitration and 9-Tier Decision Hierarchy (Phase 10 / M007)

### Status
Accepted (Phase 10 / M007)

### Context
Integrating 6 specialized agents requires centralized validation, envelope auditing, and conflict resolution to prevent advisory models or high auction bids from overriding mandatory requirements.

### Decision
1. **Auditable Response Envelopes**: All agents emit versioned `AgentResponseEnvelope` records tagged with snapshot and twin IDs.
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
3. **Non-Override Guarantee**: Formal mandatory rule violations strictly override any auction bid, preference score, or prediction.

---

## ADR-018: Dynamic Weight Renormalization and NO_BID Exclusion in Franchise Suitability Scoring (Post-M007 Sprint)

### Status
Accepted (Post-M007 Sprint)

### Context
In Franchise Agent suitability evaluation, students who legitimately omit optional profile fields (such as entrance exam ranks when evaluating non-exam programmes, or location preferences) should not be silently penalized with zero scores on those dimensions. Furthermore, programmes that issue a `NO_BID` (e.g. Due to hard eligibility violations or disqualifications) must never appear in positive applicant rankings.

### Decision
1. **Dynamic Weight Renormalization**: Scoring weights are tagged as versioned heuristics (`v1.0`). When an optional profile dimension is omitted, the agent dynamically renormalizes the remaining active weights so they sum to 1.0, preventing score deflation.
2. **Strict NO_BID Exclusion**: Any suitability bid with `is_positive_bid: False` or `suitability_score == 0.0` is explicitly tagged with `NO_BID` and filtered out of positive candidate rankings in `AuctionService`.

---

## ADR-019: Central Referee End-to-End Orchestration, Snapshot Integrity & Stale State Rejection (Post-M007 Sprint)

### Status
Accepted (Post-M007 Sprint)

### Context
The Central Referee orchestrates evaluations across all 6 specialized agents. If a client submits an obsolete or mismatched snapshot identifier, or if an agent returns an evaluation corresponding to a different student profile fingerprint, synthesis would become corrupted.

### Decision
1. **Stale Snapshot Rejection**: The Referee verifies that incoming `snapshot_id` matches the current SHA-256 fingerprint of the student profile. Stale or cross-student snapshots raise explicit HTTP 400 validation errors.
2. **Mandatory Envelope Validation**: Every participating agent returns a structured `AgentResponseEnvelope` with timestamp, confidence, and audit trail. The Referee cross-checks these envelopes before synthesizing the final decision bundle.
3. **Immutable Rule Override Protection**: Even if Franchise bids are high and Oracle forecasts are favorable, if mandatory eligibility rules are violated or unverified, the synthesized status is strictly locked to `ineligible` or `needs_review`.

---

## ADR-020: Exact Dependency Pinning, Statistical Calibration with Wilson Score Intervals, and Pure Stateless Snapshot Fingerprinting (Final Reproducibility Pass)

### Status
Accepted (Final Reproducibility & Report Consistency Pass)

### Context
Following the full implementation of M001–M007, five technical reproducibility and mathematical rigor issues were identified:
1. Version range bounds in `requirements.txt` allowed non-deterministic transitive updates across fresh environments.
2. Oracle interval calibration lacked statistical hypothesis testing, using a naive $n \ge 30$ heuristic without binomial uncertainty on holdout coverage.
3. Referee snapshot validation called `construct_twin()`, triggering unnecessary frame registry allocations and caching extra snapshots.
4. Franchise bids with low preference evidence (e.g. only 1 dimension provided) could be confused with comprehensive evaluations.
5. Exact test suite counts required transparent reconciliation.

### Decision
1. **Reproducible Dependency Strategy**: Pinned direct production dependencies in `backend/requirements.txt` and full 46-package dependency graph in `backend/requirements.lock` (`pip install -r backend/requirements.lock`). Documented FastEmbed model cache (`Qdrant/all-MiniLM-L6-v2-onnx`, revision `d13954661f83248295ba75c1ed411eef3b7b936e`, SHA-256 `bbd7b466f6d58e646fdc2bd5fd67b2f5e93c0b687011bd4548c420f7bd46f0c5`, Apache 2.0). Verified `pip check` reports 0 broken requirements.
2. **Statistical Calibration via Wilson Score Confidence Intervals**: In `OracleAgent`, replaced heuristic calibration with rigorous testing: holdout $n_{\text{test}} \ge 50$, empirical coverage within 5% tolerance ($|\hat{p} - \text{nominal}| \le 0.05$), and nominal coverage contained within the 95% Wilson binomial score interval. Separate coverages tracked for 80% $[p10, p90]$ ($z=1.2816$) and 90% $[p5, p95]$ ($z=1.6449$). Preserved `INSUFFICIENT_VERIFIED_DATA` gate.
3. **Pure Stateless Snapshot Validation**: Extracted `compute_canonical_profile_fingerprint` in `app.domain.twin`. `RefereeService.evaluate` validates snapshot fingerprints without calling `construct_twin()`, ensuring zero frame registry mutations and zero extra snapshots stored.
4. **Franchise Insufficient-Evidence UI Visibility**: Exposed `is_insufficient_evidence`, `evidence_coverage_ratio`, and `active_dimensions` across schemas to React components (`FranchiseAuctionView`, `CentralRefereeView`), rendering prominent warning badges and strikethrough styling on omitted dimensions to clearly mark single-dimension scores as exploratory signals.
5. **Reconciled Test Suite**: Verified 244 collected and 244 passing tests across 18 backend test modules.

