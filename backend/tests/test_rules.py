"""Comprehensive unit tests for the deterministic IF–THEN rule evaluator.

Verifies mandatory vs optional entrance prerequisites, academic benchmarks, and trace generation.
"""

import pytest
from app.domain.catalogue import get_synthetic_programmes
from app.domain.frames import (
    AcademicPrerequisite,
    EligibilityStatus,
    EntrancePrerequisite,
    ProgrammeFrame,
    StudentFrame,
    SubjectScore,
)
from app.rules.engine import RuleEngine, RuleStatus


@pytest.fixture
def rule_engine() -> RuleEngine:
    return RuleEngine()


@pytest.fixture
def cs_programme() -> ProgrammeFrame:
    """Flagship programme with mandatory JEE Main entrance cutoff (is_mandatory=True)."""
    programmes = {p.programme_id: p for p in get_synthetic_programmes()}
    return programmes["SYNTH_IN_CS_01"]


@pytest.fixture
def ds_programme() -> ProgrammeFrame:
    """Programme with optional/advisory JEE Main entrance benchmark (is_mandatory=False)."""
    programmes = {p.programme_id: p for p in get_synthetic_programmes()}
    return programmes["SYNTH_IN_DS_02"]


@pytest.fixture
def bio_programme() -> ProgrammeFrame:
    """Programme with mandatory certification prerequisite and no entrance exam."""
    programmes = {p.programme_id: p for p in get_synthetic_programmes()}
    return programmes["SYNTH_IN_BIO_03"]


def test_1_all_mandatory_requirements_satisfied_is_eligible(rule_engine, cs_programme):
    """Test 1: Student meeting all mandatory subject benchmarks and entrance cutoff is eligible."""
    student = StudentFrame(
        student_id="STU_001",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,  # Below mandatory cutoff of 35000
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.ELIGIBLE
    assert len(trace.missing_facts) == 0
    assert len(trace.evidence) >= 4


def test_2_verified_mandatory_prerequisite_fails_is_ineligible(rule_engine, cs_programme):
    """Test 2: Student failing mandatory math threshold evaluates to ineligible."""
    student = StudentFrame(
        student_id="STU_002",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=72.0),  # Required: 80%
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.INELIGIBLE
    violated = [r for r in trace.rules_evaluated if r.status == RuleStatus.VIOLATED]
    assert len(violated) == 1
    assert violated[0].facts_used["subject_code"] == "MATH"


def test_3_required_subject_fact_missing_is_needs_review(rule_engine, cs_programme):
    """Test 3: Missing required subject fact evaluates to needs_review, never eligible."""
    student = StudentFrame(
        student_id="STU_003",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=90.0),
            # Missing English and Physics
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.NEEDS_REVIEW
    assert len(trace.missing_facts) >= 2


def test_4_unmapped_grading_scale_is_needs_review(rule_engine, cs_programme):
    """Test 4: Incompatible grading scale (e.g. 10-point CGPA) evaluates to needs_review."""
    student = StudentFrame(
        student_id="STU_004",
        subject_scores=[
            SubjectScore(
                subject_code="MATH",
                subject_name="Mathematics",
                score=9.0,
                max_score=10.0,
                grading_scale="cbse_10_point",  # Non-percentage scale
            ),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.NEEDS_REVIEW
    assert any("grading scale" in f.lower() for f in trace.missing_facts)


# ==============================================================================
# ENTRANCE PREREQUISITE REGRESSION TESTS (MANDATORY VS OPTIONAL)
# ==============================================================================

def test_5_mandatory_entrance_exam_missing_is_needs_review(rule_engine, cs_programme):
    """Test 5: Missing mandatory entrance exam produces needs_review and missing_fact."""
    student = StudentFrame(
        student_id="STU_005",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        # entrance_exam_name is omitted
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.NEEDS_REVIEW
    assert any("mandatory entrance examination" in f.lower() for f in trace.missing_facts)


def test_6_mandatory_entrance_rank_missing_is_needs_review(rule_engine, cs_programme):
    """Test 6: Mandatory entrance exam taken but rank omitted produces needs_review."""
    student = StudentFrame(
        student_id="STU_006",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=None,  # Omitted rank
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.NEEDS_REVIEW
    assert any("rank was not reported" in f.lower() for f in trace.missing_facts)


def test_7_mandatory_entrance_rank_at_cutoff_is_satisfied(rule_engine, cs_programme):
    """Test 7: Entrance rank exactly at mandatory threshold benchmark satisfies prerequisite."""
    student = StudentFrame(
        student_id="STU_007",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=35000,  # Exactly at cutoff of 35000
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.ELIGIBLE
    assert any("satisfies mandatory cutoff" in ev.lower() for ev in trace.evidence)


def test_8_mandatory_entrance_rank_worse_than_cutoff_is_ineligible(rule_engine, cs_programme):
    """Test 8: Entrance rank exceeding mandatory cutoff causes ineligibility."""
    student = StudentFrame(
        student_id="STU_008",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=35001,  # 1 position worse than 35000 cutoff
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.INELIGIBLE
    assert any("exceeds mandatory cutoff" in ev.lower() for ev in trace.evidence)


def test_9_incompatible_entrance_examination_is_ineligible(rule_engine, cs_programme):
    """Test 9: Incompatible entrance examination (e.g. NEET for JEE programme) is ineligible."""
    student = StudentFrame(
        student_id="STU_009",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="NEET",  # Incompatible exam
        entrance_rank=500,
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.INELIGIBLE
    assert any("is incompatible with required mandatory" in ev.lower() for ev in trace.evidence)


def test_10_optional_entrance_rank_missing_remains_eligible(rule_engine, ds_programme):
    """Test 10: Missing rank for an optional entrance benchmark does NOT block eligibility."""
    student = StudentFrame(
        student_id="STU_010",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=90.0),
            SubjectScore(subject_code="PROG", subject_name="Programming", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=None,  # Taken but unstated rank for OPTIONAL benchmark
    )
    trace = rule_engine.evaluate(student, ds_programme)
    # Crucial: Since JEE Main is optional on DS programme, missing rank does not impede eligibility!
    assert trace.final_status == EligibilityStatus.ELIGIBLE
    assert len(trace.missing_facts) == 0


def test_11_optional_entrance_rank_worse_than_cutoff_remains_eligible(rule_engine, ds_programme):
    """Test 11: Rank exceeding an optional cutoff does NOT disqualify applicant."""
    student = StudentFrame(
        student_id="STU_011",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=90.0),
            SubjectScore(subject_code="PROG", subject_name="Programming", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=30000,  # Exceeds optional cutoff of 25000
    )
    trace = rule_engine.evaluate(student, ds_programme)
    # Non-mandatory cutoff failure does not cause ineligibility!
    assert trace.final_status == EligibilityStatus.ELIGIBLE
    assert any("non-mandatory and does not disqualify" in ev.lower() for ev in trace.evidence)


def test_12_optional_entrance_omitted_completely_remains_eligible(rule_engine, ds_programme):
    """Test 12: Completely omitting optional entrance exam leaves applicant eligible."""
    student = StudentFrame(
        student_id="STU_012",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=90.0),
            SubjectScore(subject_code="PROG", subject_name="Programming", score=80.0),
        ],
        entrance_exam_name=None,
        entrance_rank=None,
    )
    trace = rule_engine.evaluate(student, ds_programme)
    assert trace.final_status == EligibilityStatus.ELIGIBLE
    assert len(trace.missing_facts) == 0


def test_13_one_passed_rule_cannot_hide_failed_mandatory_entrance_rule(rule_engine, cs_programme):
    """Test 13: Perfect 100% academic marks cannot mask a failed mandatory entrance cutoff."""
    student = StudentFrame(
        student_id="STU_013",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=100.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=100.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=100.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=50000,  # Exceeds mandatory 35000
    )
    trace = rule_engine.evaluate(student, cs_programme)
    assert trace.final_status == EligibilityStatus.INELIGIBLE


def test_14_irrelevant_missing_field_does_not_change_eligibility(rule_engine, cs_programme):
    """Test 14: Non-essential preference fields do not alter deterministic eligibility."""
    student_minimal = StudentFrame(
        student_id="STU_014A",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,
    )
    student_with_prefs = StudentFrame(
        student_id="STU_014B",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,
        preferred_locations=["Karnataka"],
        career_goals=["Software Engineer"],
    )
    trace_a = rule_engine.evaluate(student_minimal, cs_programme)
    trace_b = rule_engine.evaluate(student_with_prefs, cs_programme)
    assert trace_a.final_status == trace_b.final_status == EligibilityStatus.ELIGIBLE


def test_15_repeat_evaluations_produce_identical_results(rule_engine, cs_programme):
    """Test 15: Pure determinism: identical inputs generate identical traces."""
    student = StudentFrame(
        student_id="STU_015",
        subject_scores=[
            SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0),
            SubjectScore(subject_code="ENG", subject_name="English", score=75.0),
            SubjectScore(subject_code="PHYS", subject_name="Physics", score=80.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=20000,
    )
    trace_1 = rule_engine.evaluate(student, cs_programme)
    trace_2 = rule_engine.evaluate(student, cs_programme)
    assert trace_1.final_status == trace_2.final_status
    assert len(trace_1.rules_evaluated) == len(trace_2.rules_evaluated)
    assert trace_1.evidence == trace_2.evidence


# ==============================================================================
# BIOTECHNOLOGY REGRESSION TESTS (PHASE 1.3)
# ==============================================================================

def test_16_biotechnology_biology80_chemistry80_no_entrance_is_eligible(rule_engine, bio_programme):
    """Test 16: Biotechnology with Biology 80%, Chemistry 80%, and no entrance exam is eligible."""
    student = StudentFrame(
        student_id="STU_BIO_01",
        subject_scores=[
            SubjectScore(subject_code="BIO", subject_name="Biology", score=80.0),
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=80.0),
        ],
        entrance_exam_name=None,
        entrance_rank=None,
    )
    trace = rule_engine.evaluate(student, bio_programme)
    assert trace.final_status == EligibilityStatus.ELIGIBLE
    assert len(trace.missing_facts) == 0
    assert len(trace.evidence) == 2


def test_17_biotechnology_biology_below_minimum_is_ineligible(rule_engine, bio_programme):
    """Test 17: Biology below mandatory minimum (70% < 75%) produces ineligible."""
    student = StudentFrame(
        student_id="STU_BIO_02",
        subject_scores=[
            SubjectScore(subject_code="BIO", subject_name="Biology", score=70.0),  # Required: 75%
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=80.0),
        ],
    )
    trace = rule_engine.evaluate(student, bio_programme)
    assert trace.final_status == EligibilityStatus.INELIGIBLE
    assert any("below the required minimum benchmark" in ev for ev in trace.evidence)


def test_18_biotechnology_chemistry_below_minimum_is_ineligible(rule_engine, bio_programme):
    """Test 18: Chemistry below mandatory minimum (68% < 75%) produces ineligible."""
    student = StudentFrame(
        student_id="STU_BIO_03",
        subject_scores=[
            SubjectScore(subject_code="BIO", subject_name="Biology", score=80.0),
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=68.0),  # Required: 75%
        ],
    )
    trace = rule_engine.evaluate(student, bio_programme)
    assert trace.final_status == EligibilityStatus.INELIGIBLE
    assert any("below the required minimum benchmark" in ev for ev in trace.evidence)


def test_19_biotechnology_missing_biology_is_needs_review(rule_engine, bio_programme):
    """Test 19: Missing Biology prerequisite produces needs_review."""
    student = StudentFrame(
        student_id="STU_BIO_04",
        subject_scores=[
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=80.0),
        ],
    )
    trace = rule_engine.evaluate(student, bio_programme)
    assert trace.final_status == EligibilityStatus.NEEDS_REVIEW
    assert any("Biology" in mf for mf in trace.missing_facts)


def test_20_biotechnology_missing_chemistry_is_needs_review(rule_engine, bio_programme):
    """Test 20: Missing Chemistry prerequisite produces needs_review."""
    student = StudentFrame(
        student_id="STU_BIO_05",
        subject_scores=[
            SubjectScore(subject_code="BIO", subject_name="Biology", score=80.0),
        ],
    )
    trace = rule_engine.evaluate(student, bio_programme)
    assert trace.final_status == EligibilityStatus.NEEDS_REVIEW
    assert any("Chemistry" in mf for mf in trace.missing_facts)


def test_21_biotechnology_incompatible_grading_scale_is_needs_review(rule_engine, bio_programme):
    """Test 21: Incompatible grading scale on mandatory subject produces needs_review."""
    student = StudentFrame(
        student_id="STU_BIO_06",
        subject_scores=[
            SubjectScore(
                subject_code="BIO",
                subject_name="Biology",
                score=8.0,
                max_score=10.0,
                grading_scale="cbse_10_point",
            ),
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=80.0),
        ],
    )
    trace = rule_engine.evaluate(student, bio_programme)
    assert trace.final_status == EligibilityStatus.NEEDS_REVIEW
    assert any("grading scale" in mf.lower() for mf in trace.missing_facts)


def test_22_biotechnology_empty_certifications_does_not_cause_needs_review(rule_engine, bio_programme):
    """Test 22: Empty certifications list does not independently cause needs_review."""
    student = StudentFrame(
        student_id="STU_BIO_07",
        subject_scores=[
            SubjectScore(subject_code="BIO", subject_name="Biology", score=80.0),
            SubjectScore(subject_code="CHEM", subject_name="Chemistry", score=80.0),
        ],
        certifications=[],  # Empty optional certifications
    )
    trace = rule_engine.evaluate(student, bio_programme)
    assert trace.final_status == EligibilityStatus.ELIGIBLE
    assert len(trace.missing_facts) == 0

