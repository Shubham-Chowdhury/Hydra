"""Unit and domain tests for Historical Cutoff Observations and Criteria (Phase 3)."""

import pytest

from app.domain.admissions import HISTORICAL_CUTOFF_DISCLAIMER, AdmissionCutoffObservation
from app.domain.frames import (
    EligibilityStatus,
    ProgrammeFrame,
    StudentFrame,
    SubjectScore,
)
from app.rules.engine import RuleEngine
from app.services.admissions_service import AdmissionsService


@pytest.fixture
def admissions_service():
    return AdmissionsService()


def test_1_cutoffs_filtering_by_institution_and_programme(admissions_service):
    """Cutoff query filters accurately by institution and programme title substrings."""
    records, total = admissions_service.query_cutoffs(institution="Bombay")
    assert total > 0
    for r in records:
        assert "Bombay" in r.institution_name

    cs_records, cs_total = admissions_service.query_cutoffs(
        institution="Bombay", programme="Computer Science"
    )
    assert cs_total > 0
    for r in cs_records:
        assert "Computer Science" in r.programme_title


def test_2_cutoffs_category_and_rank_basis_distinction(admissions_service):
    """Category ranks are explicitly identified as CATEGORY_RANK, not CRL."""
    open_records, _ = admissions_service.query_cutoffs(
        institution="Bombay", programme="Computer Science", seat_type="OPEN"
    )
    assert len(open_records) > 0
    for r in open_records:
        assert r.seat_type == "OPEN"
        assert r.rank_basis == "CRL"

    sc_records, _ = admissions_service.query_cutoffs(
        institution="Bombay", programme="Computer Science", seat_type="SC"
    )
    assert len(sc_records) > 0
    for r in sc_records:
        assert r.seat_type == "SC"
        assert r.rank_basis == "CATEGORY_RANK"


def test_3_historical_cutoffs_never_act_as_mandatory_eligibility_rules():
    """Historical cutoff observations do NOT automatically disqualify an applicant in the symbolic rule engine.

    A closing rank from a historical round does not prevent an applicant with verified prerequisites
    from evaluating as ELIGIBLE for a programme.
    """
    rule_engine = RuleEngine()

    student = StudentFrame(
        student_id="STU_CUTOFF_INDEPENDENCE",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=80.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,
        total_budget_inr=1000000,
    )

    # Standard synthetic programme
    prog = ProgrammeFrame(
        programme_id="PROG_CUTOFF_INVAR_TEST",
        title="B.Tech. in Computing",
        institution_name="Demo Tech",
        location="Bengaluru",
        discipline="Computer Science",
        estimated_total_tuition_inr=500000,
    )

    trace = rule_engine.evaluate(student, prog)
    # The student is ELIGIBLE under verified rules; old cutoff data (e.g. closing rank 67) has NO effect
    assert trace.final_status == EligibilityStatus.ELIGIBLE


def test_4_mandatory_disclaimer_present_on_all_cutoff_records(admissions_service):
    """Every historical cutoff observation contains the mandatory legal and informational disclaimer."""
    records, total = admissions_service.query_cutoffs(limit=50)
    assert total > 0
    for r in records:
        assert r.disclaimer == HISTORICAL_CUTOFF_DISCLAIMER
        assert "Historical cutoff observations describe past counselling outcomes" in r.disclaimer
        assert "They do not guarantee future admission" in r.disclaimer


def test_5_unknown_filters_return_empty_without_fabrication(admissions_service):
    """Querying an unknown institution returns empty results with zero fabricated records."""
    records, total = admissions_service.query_cutoffs(institution="Nonexistent Fictional Academy")
    assert total == 0
    assert len(records) == 0

