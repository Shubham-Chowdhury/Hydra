"""End-to-end integration and verification tests for Alternative Admission Pathways (Phase 2.1).

Verifies:
1. Scenario A: Academic satisfied, entrance absent -> ELIGIBLE.
2. Scenario B: Academic violated, entrance satisfied -> ELIGIBLE.
3. Scenario C: Both branches violated -> INELIGIBLE.
4. Scenario D: Neither branch satisfied with missing facts -> NEEDS_REVIEW.
5. Scenario E: Reasoning tree records both branches with complete AST metadata.
6. Scenario F: API endpoint POST /api/v1/recommendations/evaluate works end-to-end.
7. Scenario G: Descriptive frame conflict does not cause needs_review, decision-relevant conflict causes needs_review.
8. Scenario H: Baseline 4-programme catalogue and Biotechnology fix remain invariant.
"""

import pytest
from fastapi.testclient import TestClient

from app.domain.catalogue import (
    get_synthetic_alternative_pathway_programme,
    get_synthetic_programmes,
)
from app.domain.frame_system import (
    FrameDefinition,
    FrameRegistry,
    FrameSlot,
    MergePolicy,
)
from app.domain.frames import (
    EligibilityStatus,
    ProgrammeFrame,
    StudentFrame,
    SubjectScore,
)
from app.main import app
from app.rules.engine import RuleEngine, RuleStatus
from app.services.evaluation import EvaluationService
from app.services.programme_service import ProgrammeService


@pytest.fixture
def alt_programme() -> ProgrammeFrame:
    """Returns the synthetic alternative admission pathway programme."""
    return get_synthetic_alternative_pathway_programme()


@pytest.fixture
def eval_service_with_alt(alt_programme) -> EvaluationService:
    """EvaluationService configured with baseline programmes plus alternative pathway programme."""
    all_progs = get_synthetic_programmes(include_alternative_demo=True)
    prog_service = ProgrammeService(programmes=all_progs)
    return EvaluationService(programme_service=prog_service)


def test_scenario_a_academic_satisfied_entrance_absent_is_eligible(eval_service_with_alt, alt_programme):
    """Scenario A: Academic path satisfied (Math >= 80, Phys >= 75), entrance exam absent -> ELIGIBLE."""
    student = StudentFrame(
        student_id="STU_ALT_A",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=78.0),
        ],
        entrance_exam_name=None,
        entrance_rank=None,
        total_budget_inr=1000000.0,
    )

    bundle = eval_service_with_alt.evaluate_profile(student)
    alt_eval = next(e for e in bundle.evaluations if e.programme.programme_id == alt_programme.programme_id)

    assert alt_eval.trace.final_status == EligibilityStatus.ELIGIBLE
    assert "satisfies all verified mandatory prerequisites" in alt_eval.trace.summary_explanation

    # Root tree should be satisfied
    tree = alt_eval.trace.reasoning_tree
    assert tree is not None
    assert tree.expression_type == "ANY_OF"
    assert tree.status == RuleStatus.SATISFIED


def test_scenario_b_academic_violated_entrance_satisfied_is_eligible(eval_service_with_alt, alt_programme):
    """Scenario B: Academic path violated (Math 70 < 80), entrance satisfied (JEE Main 12000 <= 15000) -> ELIGIBLE."""
    student = StudentFrame(
        student_id="STU_ALT_B",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=70.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=70.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=12000,
        total_budget_inr=1000000.0,
    )

    bundle = eval_service_with_alt.evaluate_profile(student)
    alt_eval = next(e for e in bundle.evaluations if e.programme.programme_id == alt_programme.programme_id)

    assert alt_eval.trace.final_status == EligibilityStatus.ELIGIBLE
    tree = alt_eval.trace.reasoning_tree
    assert tree is not None
    assert tree.status == RuleStatus.SATISFIED
    # Child 0 (Academic AllOf) is violated
    assert tree.children[0].status == RuleStatus.VIOLATED
    # Child 1 (Entrance rank) is satisfied
    assert tree.children[1].status == RuleStatus.SATISFIED


def test_scenario_c_both_branches_violated_is_ineligible(eval_service_with_alt, alt_programme):
    """Scenario C: Both academic and entrance pathways violated -> INELIGIBLE."""
    student = StudentFrame(
        student_id="STU_ALT_C",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=70.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=70.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=25000,  # Cutoff is 15000
        total_budget_inr=1000000.0,
    )

    bundle = eval_service_with_alt.evaluate_profile(student)
    alt_eval = next(e for e in bundle.evaluations if e.programme.programme_id == alt_programme.programme_id)

    assert alt_eval.trace.final_status == EligibilityStatus.INELIGIBLE
    tree = alt_eval.trace.reasoning_tree
    assert tree is not None
    assert tree.status == RuleStatus.VIOLATED
    assert tree.children[0].status == RuleStatus.VIOLATED
    assert tree.children[1].status == RuleStatus.VIOLATED


def test_scenario_d_neither_branch_satisfied_with_missing_facts_is_needs_review(
    eval_service_with_alt, alt_programme
):
    """Scenario D: Academic violated (Math 70), entrance unobserved (missing) -> NEEDS_REVIEW under 3-valued logic."""
    student = StudentFrame(
        student_id="STU_ALT_D",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=70.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=78.0),
        ],
        entrance_exam_name=None,
        entrance_rank=None,
        total_budget_inr=1000000.0,
    )

    bundle = eval_service_with_alt.evaluate_profile(student)
    alt_eval = next(e for e in bundle.evaluations if e.programme.programme_id == alt_programme.programme_id)

    # False OR Unknown = Unknown -> NEEDS_REVIEW
    assert alt_eval.trace.final_status == EligibilityStatus.NEEDS_REVIEW
    tree = alt_eval.trace.reasoning_tree
    assert tree is not None
    assert tree.status == RuleStatus.NEEDS_REVIEW
    assert tree.children[0].status == RuleStatus.VIOLATED
    assert tree.children[1].status == RuleStatus.NEEDS_REVIEW
    assert len(alt_eval.trace.missing_facts) > 0


def test_scenario_e_reasoning_tree_ast_metadata_integrity(eval_service_with_alt, alt_programme):
    """Scenario E: Reasoning tree records both branches with complete AST structure and explanation."""
    student = StudentFrame(
        student_id="STU_ALT_E",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=82.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=76.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=14000,
        total_budget_inr=1000000.0,
    )

    bundle = eval_service_with_alt.evaluate_profile(student)
    alt_eval = next(e for e in bundle.evaluations if e.programme.programme_id == alt_programme.programme_id)

    tree = alt_eval.trace.reasoning_tree
    assert tree is not None
    assert tree.expression_type == "ANY_OF"
    assert len(tree.children) == 2

    academic_branch = tree.children[0]
    assert academic_branch.expression_type == "ALL_OF"
    assert len(academic_branch.children) == 2
    assert academic_branch.children[0].expression_type == "SUBJECT_SCORE"
    assert academic_branch.children[1].expression_type == "SUBJECT_SCORE"

    entrance_branch = tree.children[1]
    assert entrance_branch.expression_type == "ENTRANCE_RANK"
    assert "15000" in entrance_branch.expected_value
    assert entrance_branch.facts_used["exam"] == "JEE Main"
    assert entrance_branch.observed_value == "14000"


def test_scenario_f_api_endpoint_evaluation_with_alternative_pathway():
    """Scenario F: Direct API test of alternative pathways via POST /api/v1/recommendations/evaluate."""
    client = TestClient(app)

    # 1. Payload with academic satisfied, entrance absent
    payload_a = {
        "student_id": "API_STU_ALT_A",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 85.0},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 80.0},
            {"subject_code": "ENG", "subject_name": "English", "score": 75.0},
        ],
        "total_budget_inr": 800000,
    }
    response_a = client.post("/api/v1/recommendations/evaluate", json=payload_a)
    assert response_a.status_code == 200
    data_a = response_a.json()
    assert "evaluations" in data_a
    assert len(data_a["evaluations"]) >= 4

    # 2. Payload with academic violated, entrance satisfied
    payload_b = {
        "student_id": "API_STU_ALT_B",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 60.0},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 60.0},
            {"subject_code": "ENG", "subject_name": "English", "score": 60.0},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 10000,
        "total_budget_inr": 800000,
    }
    response_b = client.post("/api/v1/recommendations/evaluate", json=payload_b)
    assert response_b.status_code == 200
    data_b = response_b.json()
    assert "evaluations" in data_b


def test_scenario_g_descriptive_conflict_vs_decision_relevant_conflict():
    """Scenario G: Descriptive conflict on frame does NOT cause needs_review; decision-relevant conflict causes needs_review."""
    reg = FrameRegistry()

    # Base frame
    base_frame = FrameDefinition(frame_id="FRAME_BASE")
    reg.register_frame(base_frame)

    # Descriptive conflict: two parents disagree on display_theme (is_decision_relevant=False)
    p_desc_1 = FrameDefinition(
        frame_id="PARENT_THEME_A",
        slots={
            "display_theme": FrameSlot(name="display_theme", value="Dark", is_decision_relevant=False),
        },
    )
    p_desc_2 = FrameDefinition(
        frame_id="PARENT_THEME_B",
        slots={
            "display_theme": FrameSlot(name="display_theme", value="Light", is_decision_relevant=False),
        },
    )
    reg.register_frame(p_desc_1)
    reg.register_frame(p_desc_2)

    child_desc = FrameDefinition(
        frame_id="CHILD_DESCRIPTIVE_CONFLICT",
        parent_ids=["PARENT_THEME_A", "PARENT_THEME_B"],
    )
    reg.register_frame(child_desc)

    # Decision-relevant conflict: two parents disagree on min_physics (is_decision_relevant=True)
    p_req_1 = FrameDefinition(
        frame_id="PARENT_REQ_A",
        slots={
            "min_physics": FrameSlot(name="min_physics", value=80, is_decision_relevant=True),
        },
    )
    p_req_2 = FrameDefinition(
        frame_id="PARENT_REQ_B",
        slots={
            "min_physics": FrameSlot(name="min_physics", value=70, is_decision_relevant=True),
        },
    )
    reg.register_frame(p_req_1)
    reg.register_frame(p_req_2)

    child_req = FrameDefinition(
        frame_id="CHILD_DECISION_CONFLICT",
        parent_ids=["PARENT_REQ_A", "PARENT_REQ_B"],
    )
    reg.register_frame(child_req)

    student = StudentFrame(
        student_id="STU_CONFLICT_TEST",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=90.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=90.0),
        ],
        total_budget_inr=1000000,
    )

    prog_desc = ProgrammeFrame(
        programme_id="PROG_DESC",
        title="Programme with Descriptive Conflict",
        institution_name="Demo Tech",
        location="Bengaluru",
        discipline="Computer Science",
        parent_frame_id="CHILD_DESCRIPTIVE_CONFLICT",
        estimated_total_tuition_inr=500000,
    )

    prog_decision = ProgrammeFrame(
        programme_id="PROG_DECISION",
        title="Programme with Decision Relevant Conflict",
        institution_name="Demo Tech",
        location="Bengaluru",
        discipline="Computer Science",
        parent_frame_id="CHILD_DECISION_CONFLICT",
        estimated_total_tuition_inr=500000,
    )

    engine = RuleEngine()

    # Descriptive conflict evaluation: student remains ELIGIBLE
    trace_desc = engine.evaluate(student, prog_desc, frame_registry=reg)
    assert trace_desc.final_status == EligibilityStatus.ELIGIBLE
    # Contains descriptive notice record, but is not mandatory
    desc_records = [r for r in trace_desc.rules_evaluated if "DESCRIPTIVE" in r.rule_id]
    assert len(desc_records) == 1
    assert desc_records[0].is_mandatory is False

    # Decision-relevant conflict evaluation: student evaluates to NEEDS_REVIEW
    trace_decision = engine.evaluate(student, prog_decision, frame_registry=reg)
    assert trace_decision.final_status == EligibilityStatus.NEEDS_REVIEW
    conflict_records = [r for r in trace_decision.rules_evaluated if "FRAME_CONFLICT" in r.rule_id]
    assert len(conflict_records) == 1
    assert conflict_records[0].is_mandatory is True
    assert len(trace_decision.missing_facts) > 0


def test_scenario_h_baseline_catalogue_and_biotechnology_fix_preserved():
    """Scenario H: Baseline 4-programme catalogue and Biotechnology fix remain invariant."""
    programmes = get_synthetic_programmes()
    assert len(programmes) == 4
    prog_ids = [p.programme_id for p in programmes]
    assert "SYNTH_IN_CS_01" in prog_ids
    assert "SYNTH_IN_DS_02" in prog_ids
    assert "SYNTH_IN_BIO_03" in prog_ids
    assert "SYNTH_IN_ROB_04" in prog_ids

    # Verify Biotechnology developer profile outcome remains ELIGIBLE
    bio_student = StudentFrame(
        student_id="STU_BIO_DEV",
        subject_scores=[
            SubjectScore(subject_code="BIO", subject_name="Biology", score=80.0),
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=80.0),
        ],
        entrance_exam_name=None,
        entrance_rank=None,
        total_budget_inr=600000.0,
        preferred_locations=["Telangana"],
        preferred_disciplines=["Biotechnology"],
        career_goals=["Biomedical Researcher"],
    )

    eval_service = EvaluationService()
    bundle = eval_service.evaluate_profile(bio_student)
    bio_eval = next(e for e in bundle.evaluations if e.programme.programme_id == "SYNTH_IN_BIO_03")

    assert bio_eval.trace.final_status == EligibilityStatus.ELIGIBLE
    assert bio_eval.affordability.is_affordable is True
    assert bio_eval.preference_fit.fit_score == 1.0
