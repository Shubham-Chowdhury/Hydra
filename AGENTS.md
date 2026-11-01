# AGENTS.md — Persistent Engineering & Verification Protocol for Hydra

This file governs all AI-assisted engineering and autonomous agent tasks within the **Hydra** repository. Every agent must read, internalize, and strictly adhere to these directives prior to making modifications.

---

## 1. Core Operating Directives

1. **Context and Source Inspection First**
   - Always inspect and read existing files, architecture documentation (`docs/ARCHITECTURE.md`), and the roadmap (`docs/ROADMAP.md`) before editing or adding code.
   - Never assume an interface, signature, or dependency is present without verifying the actual file.

2. **Preserve Working Functionality**
   - Preserve existing working features, tests, and documentation.
   - Refactor conservatively. Avoid wholesale file rewrites when surgical, targeted edits achieve the goal.

3. **Phase-Bound Scope Control**
   - Strictly implement only the assigned phase and scope.
   - Do not pull in future-phase capabilities (e.g., neural nets, complex search, full auth, cloud persistence) prematurely.
   - Keep module footprints lean and cohesive.

4. **Integrity of Admissions & Academic Domain Data**
   - **Zero Fabrication**: Never fabricate admissions policies, university criteria, cutoffs, or model performance metrics.
   - **Explicit Synthetic Labelling**: All demonstration catalogs MUST be explicitly labelled in code, schemas, and UI (`is_synthetic: True`, `dataset_label: "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"`, `provenance: "SYNTHETIC_DEMO_RECORD_V1"`).
   - **Fictional Institution Names**: Never invent real university names (e.g., no IITs, NITs, BITS). Use synthetic names (e.g., "Demo Institute of Technology, Bengaluru", "Synthetic College of Engineering, Hyderabad").
   - Never describe synthetic demo data as authoritative or official university data. Official datasets will be introduced only in Phase 3 when sources and verification can be established.

5. **Separation of Verified Facts vs. Predictive Estimates & Grading Integrity**
   - Verified facts (accreditations, mandatory prerequisites, rule evaluations) are authoritative.
   - Predictive estimates (Oracle cutoffs, embedding similarities, forecast bands) must be explicitly flagged as probabilistic estimates (`is_estimate: True`, `confidence: float`).
   - Predictive models or heuristic embeddings MUST NEVER silently override or bypass mandatory deterministic eligibility rules.
   - Missing required facts must NEVER be interpreted as satisfying an eligibility condition. If a prerequisite fact is absent, the state must be `needs_review` or `ineligible`, never `eligible`.
   - **No Silent Grading Scale Conflation**: Do not compare scores from incompatible grading systems (e.g., percentage vs. 10-point CGPA). Missing or unrecognized grading conversions must yield `needs_review`.

6. **Backend Exclusivity for Inference and Eligibility**
   - The Python backend is the sole authority for evaluating eligibility, applying inheritance, running rules, and computing traces.
   - The frontend React client is strictly a presentation and interaction layer. The frontend must NEVER independently calculate eligibility.

7. **Architectural Dependency Direction vs. Request Flow**
   - **Request Flow (Runtime)**: React frontend → FastAPI API routes (`app/api/v1/`) → Application Services (`app/services/`) → Domain Reasoning & Knowledge Core (`app/domain/`, `app/knowledge/`, `app/rules/`) → Structured Results returned to React.
   - **Code Dependency Principle (Compile-Time)**: Inward-only dependencies. Domain frames, rule engines, and knowledge networks must NEVER import React, FastAPI, Starlette, HTTP request objects, or frontend-specific types.
   - API transport schemas (Pydantic DTOs in `app/api/schemas/`) are strictly decoupled from internal domain frames (Python dataclasses in `app/domain/`).

8. **Standardized Knowledge-Core Layout**
   - Domain frames: `backend/app/domain/`
   - Semantic network & graph traversal: `backend/app/knowledge/`
   - Rule evaluation & inference traces: `backend/app/rules/`
   - Application orchestration services: `backend/app/services/`
   - API routers & schemas: `backend/app/api/v1/` and `backend/app/api/schemas/`
   - Automated tests: `backend/tests/unit/` and `backend/tests/integration/`
   - Terminology rule: Maintain strict separation between domain data, synthetic demonstration catalogs, predictive estimates, and inferred relationships. Never describe knowledge representation as both a graph service and knowledge service unless explicitly partitioned.

9. **Canonical API Contracts and Budget Semantics**
   All implementations must use the canonical API endpoints:
   - `GET /api/health` — Service health and liveness check.
   - `GET /api/v1/programmes` — Programme catalog retrieval.
   - `POST /api/v1/recommendations/evaluate` — Student evaluation endpoint returning programme evaluations, eligibility status, affordability, preference fit, evidence, rule IDs, and reasoning traces.
   - Never introduce alternative evaluation endpoints without documented justification and full synchronization across documentation.
   - **Currency & Budget Semantics**: Use INR consistently for demonstration data. Budget comparisons must compare `total_budget_inr` against `estimated_total_tuition_inr` for the entire programme duration, explicitly labeled as tuition-only (`cost_basis: "tuition_only_total"`). Never perform undocumented currency conversions.

10. **Input Validation and Schema Rigor**
    - All boundary inputs must be strictly validated using Pydantic schemas (backend) and TypeScript interfaces (frontend).
    - Student profile inputs must explicitly support: academic subject scores with `grading_scale`, `entrance_exam_name` (e.g., JEE Main, MHT-CET), `entrance_rank`, `preferred_locations`, `total_budget_inr`, `preferred_disciplines`, and `career_goals`.
    - Internal domain frames must be represented using structured Python dataclasses with typed slots.

11. **Security and Secret Management**
    - Never hardcode secrets, tokens, or credentials in any file.
    - Never commit `.env` files or credentials to Git. Use environment variable templates (`.env.example`).
    - Never print sensitive environment values to logs or console outputs.

12. **Git & File Safety**
    - Never perform destructive Git operations (e.g., `git reset --hard`, `git push --force`, deleting branches) without explicit user instruction.
    - Do not push to remote repositories unless specifically instructed by the user.
    - Verify working trees and inspect diffs before committing.

13. **Honest Testing & Verification**
    - Always execute actual test suites (`pytest`, `npm test`, `npm run build`) before declaring work complete.
    - Report the exact CLI command executed and the actual terminal output.
    - Never claim tests passed if they were skipped, mocked out, or not run.
    - If a test fails, diagnose and report the failure honestly.
    - Generating files alone never satisfies a completion criterion.

---

## 2. Engineering Quality Standards

- **Small, Cohesive Modules**: Keep modules focused on a single responsibility. Avoid sprawling "utils" or monolithic agent files.
- **Pure Functions & Determinism**: Rule evaluations and frame inheritance logic must be pure, deterministic functions without hidden global state.
- **Bounded Traversal & Search**: All semantic graph traversals (e.g., NetworkX paths) and heuristic searches (e.g., A* planning) must enforce explicit depth limits, timeouts, and cycle detection. Never perform unbounded graph traversals.
- **Stable API Contracts**: Maintain backward-compatible schemas between frontend and backend. Expose standard error envelopes with structured error codes.
- **Accessible & Responsive UI**: Frontend components must satisfy WCAG AA accessibility standards, semantic HTML structure, keyboard navigation, and responsive viewport sizing.
- **Reproducible Local Environment**:
  - Windows Python: Target Python 3.13 via the Python Launcher (`py -3.13`). MSYS2 Python 3.14 on this machine lacks `pip` and must NOT be used.
  - Virtual Environment: Always run and install within `.venv`.
  - Windows Node: Execute npm operations via `npm.cmd` or PowerShell bypass to handle script execution policies.

---

## 3. The Hydra Three-State Eligibility Model

Every academic pathway evaluation in Hydra produces one of three distinct eligibility states:

1. `eligible`: Every mandatory prerequisite and rule is verified as satisfied with positive evidence.
2. `ineligible`: At least one mandatory prerequisite or rule is definitively violated.
3. `needs_review`: One or more required facts are missing, ambiguous, or require manual verification.

Eligibility MUST remain strictly decoupled from:
- **Affordability**: An applicant can be `eligible` but `unaffordable`, or vice-versa.
- **Preference Fit**: An applicant can be `eligible` with `low_preference_fit`.

---

## 4. Agent Inter-Communication Protocol

- The six specialised agents (**Twin**, **Franchise**, **Oracle**, **Heist Planner**, **Simulator**, **Boss-Fight**) do not mutate shared global state.
- All inter-agent data exchanges are mediated through the central **Referee**.
- Agents receive read-only snapshots of the student profile frame and the relevant semantic graph partition.
- Each agent returns an auditable response object containing:
  - Computed output
  - Confidence / uncertainty flags
  - Trace of rules or models consulted
  - List of missing or assumed facts

---

## 5. Verification Checklist for Future Tasks

Before declaring any implementation task complete, verify:

- [ ] Code follows the target architecture in `docs/ARCHITECTURE.md`.
- [ ] Code adheres to the canonical 11-phase roadmap in `docs/ROADMAP.md`.
- [ ] Phase 1 delivers a genuine end-to-end slice with real rule evaluation and NetworkX graph traversal; Phase 2 deepens generalized symbolic inheritance.
- [ ] Endpoints match canonical contracts (`GET /api/health`, `GET /api/v1/programmes`, `POST /api/v1/recommendations/evaluate`).
- [ ] Currency is consistently INR (`total_budget_inr`, `estimated_total_tuition_inr`, `cost_basis: "tuition_only_total"`).
- [ ] Student profile supports grading scale, entrance exam name, entrance rank, and location preferences.
- [ ] No circular imports exist in backend packages.
- [ ] Domain frames and rule engine have no dependencies on FastAPI or frontend code.
- [ ] No frontend component calculates eligibility.
- [ ] Unit tests are written and execute cleanly with `pytest`.
- [ ] Frontend code compiles cleanly (`npm run build` / `tsc`).
- [ ] Synthetic data is prominently tagged with zero fabrication of real universities.
- [ ] Actual command outputs are reported verbatim to the user.

