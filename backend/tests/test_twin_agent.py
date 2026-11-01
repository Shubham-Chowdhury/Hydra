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
    CompletenessState,
    FactOriginCategory,
    FactValidationStatus,
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
    """CBSE 10-point scale must use official percentage = CGPA * 9.5 rule, never * 10."""
    payload = {
        "student_id": "STU_CBSE_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 9.0, "max_score": 10.0, "grading_scale": "cbse_10_point"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 8.0, "max_score": 10.0, "grading_scale": "cbse_10_point"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 10.0, "max_score": 10.0, "grading_scale": "cbse_10_point"},
        ],
        "total_budget_inr": 500000,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }

    snapshot = twin_agent.construct_twin(payload)
    scores = {s.subject_code: s for s in snapshot.academic_identity.subject_scores}

    # 9.0 * 9.5 = 85.5% (NOT 90.0%)
    assert scores["MATH"].normalized_percentage == 85.5
    assert scores["MATH"].conversion_status == FactValidationStatus.VALID
    # 8.0 * 9.5 = 76.0% (NOT 80.0%)
    assert scores["PHYS"].normalized_percentage == 76.0
    # 10.0 * 9.5 = 95.0% (NOT 100.0%)
    assert scores["CHEM"].normalized_percentage == 95.0

    # Fact provenance verification
    norm_fact = snapshot.facts["FACT_NORM_SUBJ_MATH"]
    assert norm_fact.origin_category == FactOriginCategory.DETERMINISTICALLY_DERIVED
    assert norm_fact.derivation_rule == "CBSE_CGPA_X_9_5"
    assert "Official CBSE CGPA conversion formula: 9.0 * 9.5 = 85.50%" in norm_fact.explanation


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
    assert norm_fact.input_fact_ids == ["FACT_ACAD_SUBJ_MATH"]

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
    """Empty preferred locations explicitly interpreted as unconstrained / open to all India."""
    # Constrained profile
    snap_constrained = twin_agent.construct_twin({
        "subject_scores": [{"subject_code": "MATH", "score": 80, "max_score": 100, "grading_scale": "percentage"}],
        "preferred_locations": ["Karnataka", "Goa"],
    })
    assert snap_constrained.geographic_preferences.is_unconstrained is False
    assert snap_constrained.geographic_preferences.preferred_locations == ["Goa", "Karnataka"]

    # Unconstrained profile
    snap_unconstrained = twin_agent.construct_twin({
        "subject_scores": [{"subject_code": "MATH", "score": 80, "max_score": 100, "grading_scale": "percentage"}],
        "preferred_locations": [],
    })
    assert snap_unconstrained.geographic_preferences.is_unconstrained is True
    assert snap_unconstrained.geographic_preferences.preferred_locations == []
    assert "open to academic locations across India" in snap_unconstrained.geographic_preferences.notes


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

    assert frame_rep["frame_id"].startswith("FRAME_STUDENT_TWIN_")
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
