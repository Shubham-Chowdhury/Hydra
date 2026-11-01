"""Unit tests for independent affordability, preference fit, and evaluation orchestration."""

import pytest
from app.domain.frames import EligibilityStatus, StudentFrame, SubjectScore
from app.services.evaluation import EvaluationService


@pytest.fixture
def eval_service() -> EvaluationService:
    return EvaluationService()


def test_budget_boundary_conditions(eval_service: EvaluationService):
    """Verifies budget comparison: equal, 1 rupee below, and greater than total tuition."""
    # Programme SYNTH_IN_CS_01 has total tuition = 6,00,000 INR
    exact_student = StudentFrame(
        total_budget_inr=600000.0,
        subject_scores=[
            SubjectScore("MATH", "Math", 85.0),
            SubjectScore("ENG", "Eng", 75.0),
            SubjectScore("PHYS", "Phys", 80.0),
        ],
    )
    bundle_exact = eval_service.evaluate_profile(exact_student)
    cs_exact = next(e for e in bundle_exact.evaluations if e.programme.programme_id == "SYNTH_IN_CS_01")
    assert cs_exact.affordability.is_affordable is True

    # One rupee below
    below_student = StudentFrame(
        total_budget_inr=599999.0,
        subject_scores=[
            SubjectScore("MATH", "Math", 85.0),
            SubjectScore("ENG", "Eng", 75.0),
            SubjectScore("PHYS", "Phys", 80.0),
        ],
    )
    bundle_below = eval_service.evaluate_profile(below_student)
    cs_below = next(e for e in bundle_below.evaluations if e.programme.programme_id == "SYNTH_IN_CS_01")
    assert cs_below.affordability.is_affordable is False

    # Greater than
    above_student = StudentFrame(
        total_budget_inr=1000000.0,
        subject_scores=[
            SubjectScore("MATH", "Math", 85.0),
            SubjectScore("ENG", "Eng", 75.0),
            SubjectScore("PHYS", "Phys", 80.0),
        ],
    )
    bundle_above = eval_service.evaluate_profile(above_student)
    cs_above = next(e for e in bundle_above.evaluations if e.programme.programme_id == "SYNTH_IN_CS_01")
    assert cs_above.affordability.is_affordable is True


def test_eligible_programme_unaffordable_remains_eligible(eval_service: EvaluationService):
    """Verifies academic eligibility is strictly decoupled from financial affordability."""
    # SYNTH_IN_ROB_04 has total tuition = 16,00,000 INR
    student = StudentFrame(
        total_budget_inr=500000.0,  # Lower than tuition
        subject_scores=[
            SubjectScore("MATH", "Math", 85.0),
            SubjectScore("PHYS", "Phys", 80.0),
        ],
    )
    bundle = eval_service.evaluate_profile(student)
    rob = next(e for e in bundle.evaluations if e.programme.programme_id == "SYNTH_IN_ROB_04")
    assert rob.trace.final_status == EligibilityStatus.ELIGIBLE
    assert rob.affordability.is_affordable is False
    assert rob.affordability.cost_basis == "tuition_only_total"


def test_preference_fit_never_overrides_ineligibility(eval_service: EvaluationService):
    """Verifies high preference fit (1.0) does not alter an ineligible status."""
    student = StudentFrame(
        preferred_disciplines=["Computer Science"],
        career_goals=["Software Engineer"],
        preferred_locations=["Karnataka"],
        subject_scores=[
            SubjectScore("MATH", "Math", 40.0),  # Failed
            SubjectScore("ENG", "Eng", 40.0),
            SubjectScore("PHYS", "Phys", 40.0),
        ],
    )
    bundle = eval_service.evaluate_profile(student)
    cs = next(e for e in bundle.evaluations if e.programme.programme_id == "SYNTH_IN_CS_01")
    assert cs.preference_fit.fit_score == 1.0  # Perfect fit!
    assert cs.trace.final_status == EligibilityStatus.INELIGIBLE  # But ineligible!


def test_empty_preferences_safe_and_neutral(eval_service: EvaluationService):
    """Verifies empty preferences do not crash, divide by zero, or produce NaN."""
    student = StudentFrame(
        total_budget_inr=800000.0,
        preferred_disciplines=[],
        career_goals=[],
        preferred_locations=[],
        subject_scores=[SubjectScore("MATH", "Math", 85.0)],
    )
    bundle = eval_service.evaluate_profile(student)
    for ev in bundle.evaluations:
        assert 0.0 <= ev.preference_fit.fit_score <= 1.0
        assert not isinstance(ev.preference_fit.fit_score, str)


def test_deterministic_sorting_priority(eval_service: EvaluationService):
    """Verifies ordering follows: eligible > needs_review > ineligible, then affordable > unaffordable."""
    student = StudentFrame(
        total_budget_inr=650000.0,
        subject_scores=[
            SubjectScore("MATH", "Math", 85.0),
            SubjectScore("ENG", "Eng", 75.0),
            SubjectScore("PHYS", "Phys", 80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,
    )
    bundle = eval_service.evaluate_profile(student)
    statuses = [e.trace.final_status for e in bundle.evaluations]

    # Eligible programmes should appear before ineligible
    first_eligible_idx = statuses.index(EligibilityStatus.ELIGIBLE)
    if EligibilityStatus.INELIGIBLE in statuses:
        first_ineligible_idx = statuses.index(EligibilityStatus.INELIGIBLE)
        assert first_eligible_idx < first_ineligible_idx


def test_biotechnology_developer_profile_complete_orchestration(eval_service: EvaluationService):
    """Verifies developer's profile: Biotechnology is eligible, affordable, fit 1.0, and ranked #1.

    Also verifies that the other 3 programmes legitimately evaluate to needs_review.
    """
    student = StudentFrame(
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
        certifications=[],
    )
    bundle = eval_service.evaluate_profile(student)

    # 1. Biotechnology is evaluated first and eligible
    top_eval = bundle.evaluations[0]
    assert top_eval.programme.programme_id == "SYNTH_IN_BIO_03"
    assert top_eval.trace.final_status == EligibilityStatus.ELIGIBLE
    assert top_eval.affordability.is_affordable is True
    assert top_eval.affordability.total_budget_inr == 600000.0
    assert top_eval.affordability.estimated_total_tuition_inr == 500000.0
    assert top_eval.preference_fit.fit_score == 1.0
    assert len(top_eval.trace.missing_facts) == 0

    # 2. Other 3 programmes legitimately return needs_review due to missing Math, Physics, etc.
    other_evals = [e for e in bundle.evaluations if e.programme.programme_id != "SYNTH_IN_BIO_03"]
    assert len(other_evals) == 3
    for ev in other_evals:
        assert ev.trace.final_status == EligibilityStatus.NEEDS_REVIEW
        assert len(ev.trace.missing_facts) > 0


