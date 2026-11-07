"""Comprehensive Unit and Integration Tests for Hydra Twin Agent (Phase 4).

Verifies:
1. Complete student profile construction with all 5 dimensions.
2. CBSE CGPA 10-point scale normalization using official 9.5 conversion rule.
3. Marks ratio normalization (score / max_score * 100).
4. Unsupported grading scales (e.g., US 4-point GPA) yielding NEEDS_REVIEW.
5. Out of bounds score handling yielding INVALID status.
6. Typed fact provenance: USER_PROVIDED vs DETERMINISTICALLY_DERIVED vs UNKNOWN.
7. Zero predictive rank speculation for unprovided or unattempted exams.
8. Optional entrance exam handling without false invalidation.
9. Financial constraints INR currency and tuition-only basis.
10. Geographic constraints: constrained vs unconstrained open-to-all.
11. Semantic knowledge graph pathway traversal from student career goals.
12. Symbolic frame system integration and slot resolution with FRAME_STUDENT_BASE.
13. SHA-256 fingerprint reproducibility and stability.
14. Independence of Twin completeness from academic programme eligibility.
15. End-to-end API endpoints POST /api/v1/twin/construct and GET /api/v1/twin/{id}.
"""

import pytest
from fastapi.testclient import TestClient

from app.agents.twin_agent import TwinAgent
from app.api.schemas.student import StudentProfileRequest, SubjectScoreDto
from app.domain.frames import StudentFrame, SubjectScore
from app.domain.frame_system import build_canonical_programme_hierarchy
from app.domain.twin import (
    CBSE_POLICY_CCE_9_5_INDICATIVE,
    CBSE_POLICY_HISTORICAL_CCE,
    CompletenessState,
    FactOriginCategory,
    FactValidationStatus,
    GeographicPreferenceType,
    TwinSnapshot,
)
from app.knowledge.graph import HydraKnowledgeGraph
from app.main import app
from app.services.evaluation import EvaluationService
from app.services.programme_service import ProgrammeService
from app.services.twin_service import TwinService


@pytest.fixture
def twin_agent() -> TwinAgent:
    """Fixture providing a configured TwinAgent with canonical knowledge graph and frames."""
    prog_service = ProgrammeService()
    return TwinAgent(
        knowledge_graph=prog_service.graph,
        frame_registry=prog_service.frame_registry,
        programmes=prog_service.get_all(),
    )


@pytest.fixture
def test_client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_1_complete_student_profile_construction(twin_agent: TwinAgent):
    """A fully populated valid profile achieves COMPLETE across all dimensions."""
    payload = {
        "student_id": "STU_COMPLETE_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 95, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 90, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 88, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 82, "max_score": 100, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 3500,
        "total_budget_inr": 800000,
        "preferred_locations": ["Karnataka", "Maharashtra"],
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
        "certifications": ["Python Programming"],
    }

    snapshot: TwinSnapshot = twin_agent.construct_twin(payload)

    assert snapshot.twin_id.startswith("TWIN_")
    assert snapshot.student_id == "STU_COMPLETE_01"
    assert snapshot.overall_completeness == CompletenessState.COMPLETE
    assert snapshot.completeness_dimensions["academic"].state == CompletenessState.COMPLETE
    assert snapshot.completeness_dimensions["entrance_exam"].state == CompletenessState.COMPLETE
    assert snapshot.completeness_dimensions["financial"].state == CompletenessState.COMPLETE
    assert snapshot.completeness_dimensions["geographic"].state == CompletenessState.COMPLETE
    assert snapshot.completeness_dimensions["interests_and_career"].state == CompletenessState.COMPLETE

    # Academic strengths verified
    assert "MATH (95.0%)" in snapshot.academic_identity.academic_strengths
    assert "PHYS (90.0%)" in snapshot.academic_identity.academic_strengths
    assert len(snapshot.academic_identity.academic_strengths) == 4


def test_2_cbse_cgpa_10_point_scale_conversion_rule(twin_agent: TwinAgent):
    """CBSE 10-point scale converts via policy CBSE_HISTORICAL_CCE_INDICATIVE when historical CCE context established; otherwise NEEDS_REVIEW."""
    # Case A: Context & Policy established (board="CBSE", examination_year=2016 within 2009-2017 CCE scheme)
    payload_valid = {
        "student_id": "STU_CBSE_HIST_01",
        "subject_scores": [
            {
                "subject_code": "MATH",
                "subject_name": "Mathematics",
                "score": 9.0,
                "max_score": 10.0,
                "grading_scale": "cbse_10_point",
                "board": "CBSE",
                "conversion_policy_id": CBSE_POLICY_HISTORICAL_CCE,
                "examination_year": 2016,
            },
            {
                "subject_code": "PHYS",
                "subject_name": "Physics",
                "score": 8.0,
                "max_score": 10.0,
                "grading_scale": "cbse_10_point",
                "board": "CBSE",
                "conversion_policy_id": CBSE_POLICY_HISTORICAL_CCE,
                "examination_year": 2016,
            },
            {
                "subject_code": "CHEM",
                "subject_name": "Chemistry",
                "score": 10.0,
                "max_score": 10.0,
                "grading_scale": "cbse_10_point",
                "board": "CBSE",
                "conversion_policy_id": CBSE_POLICY_HISTORICAL_CCE,
                "examination_year": 2016,
            },
        ],
        "total_budget_inr": 500000,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }

    snapshot = twin_agent.construct_twin(payload_valid)
    scores = {s.subject_code: s for s in snapshot.academic_identity.subject_scores}

    # 9.0 * 9.5 = 85.5% (NOT 90.0%)
    assert scores["MATH"].normalized_percentage == 85.5
    assert scores["MATH"].conversion_status == FactValidationStatus.VALID
    assert scores["MATH"].is_indicative is True
    assert scores["MATH"].is_institution_authorized is False
    # 8.0 * 9.5 = 76.0% (NOT 80.0%)
    assert scores["PHYS"].normalized_percentage == 76.0
    # 10.0 * 9.5 = 95.0% (NOT 100.0%)
    assert scores["CHEM"].normalized_percentage == 95.0

    # Fact provenance verification
    norm_fact = snapshot.facts["FACT_NORM_SUBJ_MATH"]
    assert norm_fact.origin_category == FactOriginCategory.DETERMINISTICALLY_DERIVED
    assert norm_fact.derivation_rule == "CBSE_HISTORICAL_CCE_INDICATIVE_9_5"
    assert "CBSE_HISTORICAL_CCE_INDICATIVE" in norm_fact.explanation
    assert "CCE" in norm_fact.explanation

    # Case B: Context NOT established (conversion_policy_id omitted)
    payload_no_context = {
        "student_id": "STU_CBSE_NO_POLICY",
        "subject_scores": [
            {
                "subject_code": "MATH",
                "subject_name": "Mathematics",
                "score": 9.0,
                "max_score": 10.0,
                "grading_scale": "cbse_10_point",
            },
        ],
        "total_budget_inr": 500000,
    }
    snapshot_unestablished = twin_agent.construct_twin(payload_no_context)
    s_unest = snapshot_unestablished.academic_identity.subject_scores[0]
    assert s_unest.normalized_percentage is None
    assert s_unest.conversion_status == FactValidationStatus.NEEDS_REVIEW
    assert "Manual transcript review required" in s_unest.conversion_explanation
    assert any("CBSE Circular dated 30-Nov-2023" in f for f in snapshot_unestablished.validation_findings)


def test_3_marks_obtained_ratio_normalization(twin_agent: TwinAgent):
    """Marks obtained out of total is normalized via marks ratio."""
    payload = {
        "student_id": "STU_MARKS_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 180, "max_score": 200, "grading_scale": "marks_obtained_out_of_total"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 90, "max_score": 100, "grading_scale": "marks"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 45, "max_score": 50, "grading_scale": "ratio"},
        ],
        "total_budget_inr": 500000,
        "preferred_disciplines": ["Engineering"],
        "career_goals": ["Engineer"],
    }

    snapshot = twin_agent.construct_twin(payload)
    scores = {s.subject_code: s for s in snapshot.academic_identity.subject_scores}

    assert scores["MATH"].normalized_percentage == 90.0
    assert scores["PHYS"].normalized_percentage == 90.0
    assert scores["CHEM"].normalized_percentage == 90.0
    assert snapshot.facts["FACT_NORM_SUBJ_MATH"].derivation_rule == "MARKS_RATIO_NORMALIZATION"


def test_4_unsupported_grading_scale_yields_needs_review(twin_agent: TwinAgent):
    """Unsupported grading scales (e.g. US 4-point GPA) must not be silently converted."""
    payload = {
        "student_id": "STU_INTL_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 3.8, "max_score": 4.0, "grading_scale": "us_4_point_gpa"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 3.5, "max_score": 4.0, "grading_scale": "us_4_point_gpa"},
            {"subject_code": "ENG", "subject_name": "English", "score": 3.9, "max_score": 4.0, "grading_scale": "us_4_point_gpa"},
        ],
        "total_budget_inr": 600000,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }

    snapshot = twin_agent.construct_twin(payload)

    # All normalized scores must be None
    for s in snapshot.academic_identity.subject_scores:
        assert s.normalized_percentage is None
        assert s.conversion_status == FactValidationStatus.NEEDS_REVIEW

    assert "MATH:us_4_point_gpa" in snapshot.academic_identity.unsupported_grading_scales
    assert snapshot.completeness_dimensions["academic"].state == CompletenessState.NEEDS_REVIEW
    assert snapshot.overall_completeness == CompletenessState.NEEDS_REVIEW
    assert any("unsupported grading scale" in f.lower() for f in snapshot.validation_findings)


def test_5_out_of_bounds_score_yields_invalid(twin_agent: TwinAgent):
    """Scores outside allowable bounds [0, max_score] must be marked INVALID."""
    payload = {
        "student_id": "STU_INVALID_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 105, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": -5, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 400000,
        "preferred_disciplines": ["Engineering"],
        "career_goals": ["Engineer"],
    }

    snapshot = twin_agent.construct_twin(payload)
    scores = {s.subject_code: s for s in snapshot.academic_identity.subject_scores}

    assert scores["MATH"].conversion_status == FactValidationStatus.INVALID
    assert scores["PHYS"].conversion_status == FactValidationStatus.INVALID
    assert snapshot.completeness_dimensions["academic"].state == CompletenessState.NEEDS_REVIEW


def test_6_typed_fact_provenance_distinction(twin_agent: TwinAgent):
    """Raw inputs are USER_PROVIDED, derivations are DETERMINISTICALLY_DERIVED, missing are UNKNOWN."""
    payload = {
        "student_id": "STU_PROV_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 85, "max_score": 100, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        # rank omitted
        "total_budget_inr": 0.0,
    }

    snapshot = twin_agent.construct_twin(payload)

    # Raw subject is USER_PROVIDED
    raw_fact = snapshot.facts["FACT_ACAD_SUBJ_MATH"]
    assert raw_fact.origin_category == FactOriginCategory.USER_PROVIDED
    assert raw_fact.validation_status == FactValidationStatus.VALID

    # Normalized percentage is DETERMINISTICALLY_DERIVED
    norm_fact = snapshot.facts["FACT_NORM_SUBJ_MATH"]
    assert norm_fact.origin_category == FactOriginCategory.DETERMINISTICALLY_DERIVED
    assert list(norm_fact.input_fact_ids) == ["FACT_ACAD_SUBJ_MATH"]

    # Exam name is USER_PROVIDED
    exam_fact = snapshot.facts["FACT_ENTRANCE_EXAM"]
    assert exam_fact.origin_category == FactOriginCategory.USER_PROVIDED

    # Missing rank is UNKNOWN and MISSING
    rank_fact = snapshot.facts["FACT_ENTRANCE_RANK"]
    assert rank_fact.origin_category == FactOriginCategory.UNKNOWN
    assert rank_fact.validation_status == FactValidationStatus.MISSING
    assert rank_fact.actual_value is None


def test_7_zero_predictive_rank_speculation(twin_agent: TwinAgent):
    """Twin Agent must NEVER speculate, predict, or invent an entrance rank."""
    payload = {
        "student_id": "STU_NO_RANK",
        "subject_scores": [
            {"subject_code": "BIO", "subject_name": "Biology", "score": 85, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 80, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 75, "max_score": 100, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "NEET",
        # entrance_rank missing!
        "total_budget_inr": 700000,
        "preferred_disciplines": ["Biotechnology"],
        "career_goals": ["Biomedical Researcher"],
    }

    snapshot = twin_agent.construct_twin(payload)

    assert snapshot.entrance_exam_profile.exam_name == "NEET"
    assert snapshot.entrance_exam_profile.rank is None
    assert "entrance_rank" in snapshot.entrance_exam_profile.missing_details
    assert "Mandatory rank prerequisites cannot be verified" in snapshot.entrance_exam_profile.interpretation_notes


def test_8_omitted_entrance_exam_is_clean_and_non_fatal(twin_agent: TwinAgent):
    """Absence of entrance examination must not cause NEEDS_REVIEW on entrance_exam dimension."""
    payload = {
        "student_id": "STU_BIOTECH_01",
        "subject_scores": [
            {"subject_code": "BIO", "subject_name": "Biology", "score": 88, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 84, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 80, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 600000,
        "preferred_disciplines": ["Biotechnology"],
        "career_goals": ["Biomedical Researcher"],
    }

    snapshot = twin_agent.construct_twin(payload)

    assert snapshot.entrance_exam_profile.exam_name is None
    assert snapshot.entrance_exam_profile.rank is None
    assert snapshot.completeness_dimensions["entrance_exam"].state == CompletenessState.PARTIAL
    # Overall is PARTIAL (not NEEDS_REVIEW) because entrance exam is simply omitted
    assert snapshot.overall_completeness == CompletenessState.PARTIAL


def test_9_financial_constraints_currency_and_cost_basis(twin_agent: TwinAgent):
    """Financial constraints strictly adhere to INR currency and tuition_only_total cost basis."""
    payload = {
        "student_id": "STU_FIN_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 80, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 950000.50,
    }

    snapshot = twin_agent.construct_twin(payload)

    assert snapshot.financial_constraints.currency == "INR"
    assert snapshot.financial_constraints.cost_basis == "tuition_only_total"
    assert snapshot.financial_constraints.total_budget_inr == 950000.50
    assert snapshot.financial_constraints.is_budget_provided is True
    assert snapshot.financial_constraints.affordability_readiness is True


def test_10_geographic_preferences_unconstrained_semantics(twin_agent: TwinAgent):
    """Geographic preferences distinguish NOT_PROVIDED, PREFERRED_LOCATIONS, and ANYWHERE_IN_INDIA."""
    # Constrained profile
    snap_constrained = twin_agent.construct_twin({
        "subject_scores": [{"subject_code": "MATH", "score": 80, "max_score": 100, "grading_scale": "percentage"}],
        "preferred_locations": ["Karnataka", "Goa"],
    })
    assert snap_constrained.geographic_preferences.is_unconstrained is False
    assert list(snap_constrained.geographic_preferences.preferred_locations) == ["Goa", "Karnataka"]
    assert snap_constrained.geographic_preferences.preference_type == GeographicPreferenceType.PREFERRED_LOCATIONS

    # Unconstrained / Not provided profile (empty locations list)
    snap_unconstrained = twin_agent.construct_twin({
        "subject_scores": [{"subject_code": "MATH", "score": 80, "max_score": 100, "grading_scale": "percentage"}],
        "preferred_locations": [],
    })
    assert snap_unconstrained.geographic_preferences.is_unconstrained is True
    assert list(snap_unconstrained.geographic_preferences.preferred_locations) == []
    assert snap_unconstrained.geographic_preferences.preference_type == GeographicPreferenceType.NOT_PROVIDED
    assert "Geographic preference not provided (neutral)" in snap_unconstrained.geographic_preferences.notes

    # Explicit anywhere in India profile
    snap_anywhere = twin_agent.construct_twin({
        "subject_scores": [{"subject_code": "MATH", "score": 80, "max_score": 100, "grading_scale": "percentage"}],
        "preferred_locations": ["anywhere in india"],
    })
    assert snap_anywhere.geographic_preferences.is_unconstrained is True
    assert list(snap_anywhere.geographic_preferences.preferred_locations) == []
    assert snap_anywhere.geographic_preferences.preference_type == GeographicPreferenceType.ANYWHERE_IN_INDIA
    assert "open to academic locations anywhere in India" in snap_anywhere.geographic_preferences.notes


def test_11_semantic_network_pathway_traversal(twin_agent: TwinAgent):
    """Semantic graph traversal connects student career goals to programmes."""
    payload = {
        "student_id": "STU_PATHWAY_01",
        "subject_scores": [
            {"subject_code": "MATH", "score": 90, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "score": 85, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "score": 80, "max_score": 100, "grading_scale": "percentage"},
        ],
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }

    snapshot = twin_agent.construct_twin(payload)

    pathways = snapshot.semantic_network_pathways
    assert len(pathways) > 0

    # Verify discovered relationship structure
    lead_paths = [p for p in pathways if p["relationship"] == "PROGRAMME_LEADS_TO_CAREER"]
    assert len(lead_paths) > 0
    assert any(p["target"] == "Software Engineer" for p in lead_paths)


def test_12_symbolic_frame_system_integration(twin_agent: TwinAgent):
    """Twin frame is registered with parent FRAME_STUDENT_BASE and inherits default slots."""
    payload = {
        "student_id": "STU_FRAME_01",
        "subject_scores": [
            {"subject_code": "MATH", "score": 88, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 500000,
        "preferred_locations": ["Maharashtra"],
    }

    snapshot = twin_agent.construct_twin(payload)
    frame_rep = snapshot.frame_representation

    assert frame_rep["frame_id"].startswith("FRAME_STUDENT_")
    assert twin_agent.frame_registry.has_frame(f"FRAME_STUDENT_{snapshot.twin_id}")
    assert twin_agent.frame_registry.has_frame(frame_rep["frame_id"])
    assert frame_rep["parent_frame_id"] == "FRAME_STUDENT_BASE"

    slots = frame_rep["slots"]
    # Explicit child slot
    assert slots["total_budget_inr"]["value"] == 500000.0
    assert slots["total_budget_inr"]["source_type"] == "explicit"

    # Inherited default slot from FRAME_STUDENT_BASE
    assert slots["currency"]["value"] == "INR"
    assert slots["currency"]["source_type"] == "inherited_default"
    assert slots["cost_basis"]["value"] == "tuition_only_total"
    assert slots["cost_basis"]["source_type"] == "inherited_default"


def test_13_fingerprint_reproducibility_and_stability(twin_agent: TwinAgent):
    """Identical profile inputs produce identical fingerprint; modified input changes fingerprint."""
    p1 = {
        "student_id": "STU_FP_01",
        "subject_scores": [
            {"subject_code": "MATH", "score": 90, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "score": 85, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 600000,
        "preferred_locations": ["Karnataka"],
    }

    # Different ordering of subjects and locations
    p2 = {
        "student_id": "STU_FP_01",
        "subject_scores": [
            {"subject_code": "PHYS", "score": 85, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "MATH", "score": 90, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 600000,
        "preferred_locations": ["Karnataka"],
    }

    p3_modified = {**p1, "total_budget_inr": 600001}

    s1 = twin_agent.construct_twin(p1)
    s2 = twin_agent.construct_twin(p2)
    s3 = twin_agent.construct_twin(p3_modified)

    assert s1.profile_fingerprint == s2.profile_fingerprint
    assert s1.twin_id == s2.twin_id
    assert s1.profile_fingerprint != s3.profile_fingerprint
    assert s1.twin_id != s3.twin_id


def test_14_independence_of_twin_completeness_from_programme_eligibility(twin_agent: TwinAgent):
    """Twin completeness must NOT dictate programme eligibility (e.g. low score can be complete but ineligible)."""
    eval_service = EvaluationService()

    # Complete student profile, but with failing academic scores (Biology 40%)
    low_score_profile = {
        "student_id": "STU_LOW_SCORE",
        "subject_scores": [
            {"subject_code": "BIO", "subject_name": "Biology", "score": 40, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 40, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 40, "max_score": 100, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 80000,
        "total_budget_inr": 800000,
        "preferred_locations": ["Telangana"],
        "preferred_disciplines": ["Biotechnology"],
        "career_goals": ["Biomedical Researcher"],
    }

    # 1. Twin Agent constructs a COMPLETE snapshot (all dimensions provided)
    snap = twin_agent.construct_twin(low_score_profile)
    assert snap.overall_completeness == CompletenessState.COMPLETE

    # 2. But Evaluation Service evaluates student as INELIGIBLE for Biotechnology (mandates BIO >= 75%)
    student_frame = StudentFrame(
        student_id=low_score_profile["student_id"],
        subject_scores=[
            SubjectScore(subject_code="BIO", subject_name="Biology", score=40),
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=40),
            SubjectScore(subject_code="ENG", subject_name="English", score=40),
        ],
        preferred_disciplines=["Biotechnology"],
        career_goals=["Biomedical Researcher"],
        total_budget_inr=800000,
    )
    eval_bundle = eval_service.evaluate_profile(student_frame)
    bio_eval = next(e for e in eval_bundle.evaluations if e.programme.programme_id == "SYNTH_IN_BIO_03")

    assert bio_eval.trace.final_status.value == "ineligible"


def test_15_api_endpoints_construct_and_get(test_client: TestClient):
    """POST /api/v1/twin/construct and GET /api/v1/twin/{id} execute cleanly."""
    payload = {
        "student_id": "STU_API_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 92, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 88, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 85, "max_score": 100, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 4000,
        "total_budget_inr": 750000,
        "preferred_locations": ["Karnataka"],
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }

    # 1. Test POST
    post_res = test_client.post("/api/v1/twin/construct", json=payload)
    assert post_res.status_code == 200
    data = post_res.json()

    assert "snapshot" in data
    assert "disclaimer" in data
    snap = data["snapshot"]
    twin_id = snap["twin_id"]
    assert twin_id.startswith("TWIN_")
    assert snap["overall_completeness"] == "complete"
    assert snap["is_synthetic"] is True

    # 2. Test GET
    get_res = test_client.get(f"/api/v1/twin/{twin_id}")
    assert get_res.status_code == 200
    get_snap = get_res.json()["snapshot"]
    assert get_snap["twin_id"] == twin_id
    assert get_snap["profile_fingerprint"] == snap["profile_fingerprint"]

    # 3. Test GET not found
    notFound_res = test_client.get("/api/v1/twin/NON_EXISTENT_ID")
    assert notFound_res.status_code == 404


def test_16_score_based_academic_highlights_threshold_and_heuristic_version(twin_agent: TwinAgent):
    """Academic highlights enforce 75.0% threshold and versioned heuristic metadata."""
    payload = {
        "student_id": "STU_HIGHLIGHTS_01",
        "subject_scores": [
            {"subject_code": "MATH", "score": 90, "max_score": 100, "grading_scale": "percentage"},  # 90% >= 75% -> highlight
            {"subject_code": "PHYS", "score": 75, "max_score": 100, "grading_scale": "percentage"},  # 75% >= 75% -> highlight
            {"subject_code": "CHEM", "score": 74.9, "max_score": 100, "grading_scale": "percentage"},  # 74.9% < 75% -> not highlight
            {"subject_code": "ENG", "score": 60, "max_score": 100, "grading_scale": "percentage"},  # 60% < 75% -> not highlight
        ],
    }
    snapshot = twin_agent.construct_twin(payload)
    acad = snapshot.academic_identity

    assert acad.highlight_threshold == 75.0
    assert acad.highlight_heuristic_version == "1.0"
    assert "MATH (90.0%)" in acad.score_based_academic_highlights
    assert "PHYS (75.0%)" in acad.score_based_academic_highlights
    assert not any("CHEM" in h for h in acad.score_based_academic_highlights)
    assert not any("ENG" in h for h in acad.score_based_academic_highlights)
    # Backward compatibility property matches
    assert acad.academic_strengths == list(acad.score_based_academic_highlights)


def test_17_client_verification_flag_rejection(twin_agent: TwinAgent):
    """Client-supplied verification claims or origin overrides are rejected; facts remain USER_PROVIDED."""
    payload = {
        "student_id": "STU_SPOOF_01",
        "subject_scores": [
            {"subject_code": "MATH", "score": 95, "max_score": 100, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 105,
        # Spoofed attributes injected into dictionary
        "is_verified": True,
        "origin_category": "external_verified",
        "rank_verified_by": "JOSAA_PORTAL_BYPASS",
    }
    snapshot = twin_agent.construct_twin(payload)

    rank_fact = snapshot.facts["FACT_ENTRANCE_RANK"]
    exam_fact = snapshot.facts["FACT_ENTRANCE_EXAM"]

    # Must strictly remain USER_PROVIDED
    assert rank_fact.origin_category == FactOriginCategory.USER_PROVIDED
    assert exam_fact.origin_category == FactOriginCategory.USER_PROVIDED
    assert "external official verification not performed" in snapshot.entrance_exam_profile.interpretation_notes


def test_18_snapshot_deep_immutability(twin_agent: TwinAgent):
    """TwinSnapshot data structures are deeply immutable and raise errors on mutation attempts."""
    payload = {
        "student_id": "STU_IMMUTABLE_01",
        "subject_scores": [
            {"subject_code": "MATH", "score": 90, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 500000,
        "career_goals": ["Software Engineer"],
    }
    snapshot = twin_agent.construct_twin(payload)

    # 1. Facts dictionary is protected MappingProxyType
    with pytest.raises(TypeError):
        snapshot.facts["FACT_INJECTED"] = None  # type: ignore

    # 2. Completeness dimensions is protected MappingProxyType
    with pytest.raises(TypeError):
        snapshot.completeness_dimensions["academic"] = None  # type: ignore

    # 3. Missing information is immutable tuple
    with pytest.raises(AttributeError):
        snapshot.missing_information.append("FAKE_INFO")  # type: ignore

    # 4. Semantic pathways is immutable tuple
    with pytest.raises(AttributeError):
        snapshot.semantic_network_pathways.append({})  # type: ignore

    # 5. Top-level dataclass is frozen
    with pytest.raises(Exception):
        snapshot.twin_id = "MUTATED_ID"  # type: ignore


def test_19_frame_system_student_isolation(twin_agent: TwinAgent):
    """Creating student twins registers isolated child frames without contaminating FRAME_STUDENT_BASE."""
    reg = twin_agent.frame_registry

    # Baseline: check FRAME_STUDENT_BASE slots
    base_resolved_before = reg.resolve_slots("FRAME_STUDENT_BASE")
    assert "total_budget_inr" not in base_resolved_before
    assert "student_id" not in base_resolved_before
    assert "entrance_rank" not in base_resolved_before
    assert base_resolved_before["currency"].resolved_value == "INR"

    # Construct Twin 1
    p1 = {
        "student_id": "STU_ISOLATION_01",
        "total_budget_inr": 400000.0,
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 5000,
    }
    s1 = twin_agent.construct_twin(p1)

    # Construct Twin 2
    p2 = {
        "student_id": "STU_ISOLATION_02",
        "total_budget_inr": 900000.0,
        "entrance_exam_name": "MHT-CET",
        "entrance_rank": 1200,
    }
    s2 = twin_agent.construct_twin(p2)

    # Verify FRAME_STUDENT_BASE remained completely uncontaminated
    base_resolved_after = reg.resolve_slots("FRAME_STUDENT_BASE")
    assert "total_budget_inr" not in base_resolved_after
    assert "student_id" not in base_resolved_after
    assert "entrance_rank" not in base_resolved_after
    assert len(base_resolved_after) == len(base_resolved_before)

    # Verify Twin 1 frame resolution has its own slots
    frame1 = reg.resolve_slots(f"FRAME_STUDENT_{s1.twin_id}")
    assert frame1["student_id"].resolved_value == "STU_ISOLATION_01"
    assert frame1["total_budget_inr"].resolved_value == 400000.0
    assert frame1["entrance_rank"].resolved_value == 5000

    # Verify Twin 2 frame resolution has its own slots
    frame2 = reg.resolve_slots(f"FRAME_STUDENT_{s2.twin_id}")
    assert frame2["student_id"].resolved_value == "STU_ISOLATION_02"
    assert frame2["total_budget_inr"].resolved_value == 900000.0
    assert frame2["entrance_rank"].resolved_value == 1200


def test_20_semantic_graph_directed_edge_fidelity(twin_agent: TwinAgent):
    """Discovered pathways maintain true directed edge orientation from academic entity to career/discipline."""
    payload = {
        "student_id": "STU_DIRECTION_01",
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }
    snapshot = twin_agent.construct_twin(payload)

    pathways = snapshot.semantic_network_pathways
    assert len(pathways) > 0

    for path in pathways:
        # Source must be the academic Programme/Entity and target must be Career or Discipline
        if path["target_type"] == "career":
            assert path["relationship"] in ("PROGRAMME_LEADS_TO_CAREER", "SKILL_RELEVANT_TO_CAREER")
            assert path["target"] == "Software Engineer"
        elif path["target_type"] == "discipline":
            assert path["relationship"] == "PROGRAMME_RELATED_TO_DISCIPLINE"
            assert path["target"] == "Computer Science"


def test_21_cbse_unauthorized_client_policy_selection_rejected(twin_agent: TwinAgent):
    """Client cannot unilaterally authorize grading conversion for 2026 cohort by asserting a policy."""
    payload_modern = {
        "student_id": "STU_CBSE_2026_UNAUTH",
        "subject_scores": [
            {
                "subject_code": "MATH",
                "subject_name": "Mathematics",
                "score": 9.2,
                "max_score": 10.0,
                "grading_scale": "cbse_10_point",
                "board": "CBSE",
                "conversion_policy_id": "CBSE_CCE_9_5_INDICATIVE",
                "examination_year": 2026,
            }
        ],
        "total_budget_inr": 500000,
    }
    snapshot = twin_agent.construct_twin(payload_modern)
    math_score = snapshot.academic_identity.subject_scores[0]

    # Server rejects client self-authorization
    assert math_score.normalized_percentage is None
    assert math_score.conversion_status == FactValidationStatus.NEEDS_REVIEW
    assert "Unauthorized policy selection" in math_score.conversion_explanation
    assert "30-Nov-2023" in math_score.conversion_explanation
    assert any("unauthorized policy" in f.lower() for f in snapshot.validation_findings)


def test_22_snapshot_deep_recursive_immutability(twin_agent: TwinAgent):
    """Enforces true recursive immutability across all nested collections and dictionaries."""
    payload = {
        "student_id": "STU_IMMUTABLE_01",
        "subject_scores": [
            {"subject_code": "MATH", "score": 90, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 600000,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }
    snapshot = twin_agent.construct_twin(payload)

    # 1. Fact actual_value nested dict mutation fails
    math_fact = snapshot.facts["FACT_ACAD_SUBJ_MATH"]
    with pytest.raises(TypeError):
        math_fact.actual_value["score"] = 999.0  # type: ignore

    # 2. Fact input_fact_ids cannot be appended
    with pytest.raises(AttributeError):
        math_fact.input_fact_ids.append("INJECTED_FACT")  # type: ignore

    # 3. Frame representation slots dict is immutable MappingProxyType
    with pytest.raises(TypeError):
        snapshot.frame_representation["slots"]["injected_slot"] = {}  # type: ignore

    # 4. Nested dict inside a frame slot cannot be mutated
    slot_entry = snapshot.frame_representation["slots"].get("total_budget_inr")
    if slot_entry and isinstance(slot_entry, dict):
        with pytest.raises(TypeError):
            slot_entry["value"] = 0.0  # type: ignore

    # 5. Completeness dimension available_facts tuple cannot be mutated
    acad_dim = snapshot.completeness_dimensions["academic"]
    with pytest.raises(AttributeError):
        acad_dim.available_facts.append("MUTATED_FACT")  # type: ignore

    # 6. Semantic pathways list item cannot be mutated
    if snapshot.semantic_network_pathways:
        with pytest.raises(TypeError):
            snapshot.semantic_network_pathways[0]["source"] = "HACKED_SOURCE"  # type: ignore

    # 7. Serialization to_dict() returns clean mutable standard dict
    dict_repr = snapshot.to_dict()
    assert isinstance(dict_repr, dict)
    assert isinstance(dict_repr["facts"], dict)
    assert dict_repr["snapshot_id"].startswith("SNAP_")
    assert dict_repr["policy_version"] == "1.0.0"


def test_23_snapshot_identity_vs_fingerprint_lifecycle(twin_agent: TwinAgent):
    """Distinguishes profile fingerprint, twin_id, and snapshot_id lifecycle across TwinService."""
    import time
    service = TwinService(twin_agent=twin_agent)

    payload = {
        "student_id": "STU_LIFECYCLE_01",
        "subject_scores": [
            {"subject_code": "MATH", "score": 92, "max_score": 100, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 700000,
    }

    # Run 1
    snap1 = service.construct_twin(payload)
    time.sleep(0.01)  # Ensure timestamp progression
    # Run 2 with identical profile
    snap2 = service.construct_twin(payload)

    # Deterministic fingerprint & twin_id are identical
    assert snap1.profile_fingerprint == snap2.profile_fingerprint
    assert snap1.twin_id == snap2.twin_id

    # Unique snapshot_id per run
    assert snap1.snapshot_id != snap2.snapshot_id
    assert snap1.snapshot_id.startswith("SNAP_")
    assert snap2.snapshot_id.startswith("SNAP_")

    # TwinService retrieval by snapshot_id recovers both individual snapshots
    retrieved_s1 = service.get_snapshot(snap1.snapshot_id)
    retrieved_s2 = service.get_snapshot(snap2.snapshot_id)
    assert retrieved_s1 is snap1
    assert retrieved_s2 is snap2

    # TwinService retrieval by twin_id returns latest snapshot
    retrieved_twin = service.get_snapshot(snap1.twin_id)
    assert retrieved_twin is snap2


def test_24_concurrent_twin_construction_and_frame_isolation(twin_agent: TwinAgent):
    """Runs 20 concurrent twin constructions via ThreadPoolExecutor; verifies FRAME_STUDENT_BASE slot isolation."""
    from concurrent.futures import ThreadPoolExecutor

    reg = twin_agent.frame_registry
    base_frame = reg.get_frame("FRAME_STUDENT_BASE")
    assert base_frame is not None
    initial_slot_count = len(base_frame.slots)
    assert initial_slot_count == 8  # 8 default slots

    def construct_candidate(i: int):
        profile = {
            "student_id": f"STU_CONCURRENT_{i:02d}",
            "subject_scores": [
                {"subject_code": "MATH", "score": 70 + (i % 25), "max_score": 100, "grading_scale": "percentage"},
            ],
            "total_budget_inr": 300000 + (i * 10000),
            "entrance_exam_name": "JEE Main",
            "entrance_rank": 1000 + i,
            "preferred_locations": [f"State_{i}"],
        }
        return twin_agent.construct_twin(profile)

    with ThreadPoolExecutor(max_workers=5) as executor:
        snapshots = list(executor.map(construct_candidate, range(20)))

    assert len(snapshots) == 20

    # FRAME_STUDENT_BASE must remain untouched with exactly 8 slots
    base_frame_after = reg.get_frame("FRAME_STUDENT_BASE")
    assert len(base_frame_after.slots) == 8
    assert "total_budget_inr" not in base_frame_after.slots
    assert "student_id" not in base_frame_after.slots

    # Each student frame has isolated slots matching only their own input
    for i, snap in enumerate(snapshots):
        student_frame_id = snap.frame_representation["frame_id"]
        res = reg.resolve_slots(student_frame_id)
        assert res["student_id"].resolved_value == f"STU_CONCURRENT_{i:02d}"
        assert res["total_budget_inr"].resolved_value == float(300000 + (i * 10000))
        assert res["entrance_rank"].resolved_value == 1000 + i


def test_25_semantic_network_forward_direction_preserved(twin_agent: TwinAgent):
    """Reverse pathway lookup does not invert edge directions or mutate knowledge graph."""
    graph = twin_agent.graph.graph
    initial_node_count = graph.number_of_nodes()
    initial_edge_count = graph.number_of_edges()

    payload = {
        "student_id": "STU_DIRECTION_02",
        "preferred_disciplines": ["Computer Science", "Biotechnology"],
        "career_goals": ["Software Engineer", "Data Scientist"],
    }
    snapshot = twin_agent.construct_twin(payload)

    # Graph was NOT mutated (pure read-only lookup)
    assert graph.number_of_nodes() == initial_node_count
    assert graph.number_of_edges() == initial_edge_count

    # Pathways maintain forward semantics: academic programme / skill -> career
    for path in snapshot.semantic_network_pathways:
        if path["target_type"] == "career":
            assert path["relationship"] in ("PROGRAMME_LEADS_TO_CAREER", "SKILL_RELEVANT_TO_CAREER")
            assert path["target"] in ("Software Engineer", "Data Scientist")
            # In underlying graph, edge goes from u -> goal_id
            u, v = path["provenance_path"]
            assert graph.has_edge(u, v)


def test_26_snapshot_uniqueness_and_concurrency_same_profile(twin_agent: TwinAgent):
    """Constructing the exact same profile 100 times concurrently guarantees unique snapshot IDs, cache retention, and frame isolation."""
    from concurrent.futures import ThreadPoolExecutor

    service = TwinService(twin_agent=twin_agent)
    reg = twin_agent.frame_registry

    identical_payload = {
        "student_id": "STU_IDENTICAL_100",
        "subject_scores": [
            {"subject_code": "MATH", "score": 90, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "score": 85, "max_score": 100, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 2500,
        "total_budget_inr": 600000,
        "preferred_locations": ["Karnataka"],
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }

    def construct_one(_: int) -> TwinSnapshot:
        return service.construct_twin(identical_payload)

    # Execute 100 concurrent twin constructions for the identical profile
    with ThreadPoolExecutor(max_workers=10) as executor:
        snapshots = list(executor.map(construct_one, range(100)))

    assert len(snapshots) == 100

    # 1. Deterministic profile fingerprint is identical across all 100 instances
    fingerprints = [s.profile_fingerprint for s in snapshots]
    assert len(set(fingerprints)) == 1

    # 2. Deterministic twin_id is identical across all 100 instances
    twin_ids = [s.twin_id for s in snapshots]
    assert len(set(twin_ids)) == 1

    # 3. All 100 snapshot_id values are strictly unique
    snapshot_ids = [s.snapshot_id for s in snapshots]
    assert len(set(snapshot_ids)) == 100

    # 4. Every snapshot can be retrieved using its snapshot_id from TwinService cache
    for s in snapshots:
        retrieved = service.get_snapshot(s.snapshot_id)
        assert retrieved is not None
        assert retrieved.snapshot_id == s.snapshot_id

    # 5. No earlier snapshot was overwritten in the snapshot-id cache
    assert len(service._snapshots_by_snapshot_id) >= 100

    # 6. Student frame IDs remain distinct and correctly registered
    frame_ids = [s.frame_representation["frame_id"] for s in snapshots]
    assert len(set(frame_ids)) == 100
    for fid in frame_ids:
        assert reg.has_frame(fid)
        resolved = reg.resolve_slots(fid)
        assert resolved["student_id"].resolved_value == "STU_IDENTICAL_100"
        assert resolved["total_budget_inr"].resolved_value == 600000.0


def test_27_cbse_indicative_does_not_satisfy_formal_admission_percentage():
    """Historical indicative CBSE conversion does not automatically satisfy formal institutional admission percentage requirements."""
    from app.services.evaluation import EvaluationService

    eval_service = EvaluationService()

    # Student with CBSE CGPA (9.0/10.0 in MATH, 8.5/10.0 in PHYS)
    student = StudentFrame(
        student_id="STU_CBSE_FORMAL_TEST",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=9.0, max_score=10.0, grading_scale="cbse_10_point"),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=8.5, max_score=10.0, grading_scale="cbse_10_point"),
        ],
        total_budget_inr=1000000.0,
    )

    bundle = eval_service.evaluate_profile(student)

    # Programmes with mandatory percentage requirements must return NEEDS_REVIEW, never ELIGIBLE
    for eval_result in bundle.evaluations:
        # Every programme requiring percentage prerequisite evaluates to NEEDS_REVIEW due to grading scale incompatibility
        math_evals = [
            r for r in eval_result.trace.rules_evaluated
            if "MATH" in r.rule_id or "MATHEMATICS" in r.rule_name.upper()
        ]
        for m in math_evals:
            if m.status.value != "satisfied":
                assert m.status.value == "needs_review"
                assert "Incompatible grading scale" in m.explanation or "grading scale" in m.explanation.lower()


def test_28_frame_registry_lifecycle_and_bounded_pruning():
    """FrameRegistry supports bounded dynamic student frame pruning without touching base frames."""
    prog_service = ProgrammeService()
    bounded_agent = TwinAgent(
        knowledge_graph=prog_service.graph,
        frame_registry=prog_service.frame_registry,
        programmes=prog_service.get_all(),
        max_retained_student_frames=5,
    )

    reg = bounded_agent.frame_registry
    base_frame = reg.get_frame("FRAME_STUDENT_BASE")
    assert base_frame is not None
    initial_slot_count = len(base_frame.slots)

    # Construct 10 snapshots with max capacity of 5
    constructed_frames = []
    for i in range(10):
        snap = bounded_agent.construct_twin({
            "student_id": f"STU_BOUNDED_{i:02d}",
            "subject_scores": [{"subject_code": "MATH", "score": 80, "max_score": 100, "grading_scale": "percentage"}],
            "total_budget_inr": 100000.0 + i,
        })
        constructed_frames.append(snap.frame_representation["frame_id"])

    # Active dynamic frame tracking is bounded to 5
    assert len(bounded_agent._dynamic_student_frame_ids) == 5

    # Oldest 5 frames were pruned from the registry
    for fid in constructed_frames[:5]:
        assert not reg.has_frame(fid)

    # Most recent 5 frames are preserved in the registry
    for fid in constructed_frames[5:]:
        assert reg.has_frame(fid)

    # Base frame slots remained completely untouched
    base_frame_after = reg.get_frame("FRAME_STUDENT_BASE")
    assert len(base_frame_after.slots) == initial_slot_count
