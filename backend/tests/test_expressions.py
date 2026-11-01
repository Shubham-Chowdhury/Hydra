"""Unit tests for Hydra Requirement Expressions AST and Three-Valued Logic (Phase 2).

Verifies:
1. Atomic SubjectScoreRequirement (SATISFIED, VIOLATED, NEEDS_REVIEW for missing score and scale).
2. Atomic EntranceRankRequirement (SATISFIED, VIOLATED, NEEDS_REVIEW for missing exam/rank, optional).
3. Atomic CertificationRequirement (SATISFIED, VIOLATED, NEEDS_REVIEW).
4. Composite AllOf conjunction (all satisfied, mandatory violated, needs_review, optional semantics).
5. Composite AnyOf disjunction (at least one satisfied, all violated, unresolved needs_review).
6. Nested composite expressions (AllOf containing AnyOf, AnyOf containing AllOf).
7. Canonical alternative admission pathways demonstration:
   (Math >= 80% AND Physics >= 75%) OR (JEE Main rank <= 15000)
   - Student A (boards satisfied, no entrance exam) -> SATISFIED
   - Student B (boards violated, JEE Main cutoff satisfied) -> SATISFIED
   - Student C (boards violated, JEE Main rank worse than cutoff) -> VIOLATED
   - Student D (missing facts on both pathways) -> NEEDS_REVIEW
8. Validation error on empty expressions or empty children.
"""

import pytest

from app.domain.frames import StudentFrame, SubjectScore
from app.rules.expressions import (
    AllOf,
    AnyOf,
    CertificationRequirement,
    EntranceRankRequirement,
    RuleStatus,
    SubjectScoreRequirement,
)


def test_1_atomic_subject_score_requirement():
    """SubjectScoreRequirement evaluates SATISFIED, VIOLATED, or NEEDS_REVIEW accurately."""
    req = SubjectScoreRequirement(
        expression_id="REQ_MATH_80",
        subject_code="MATH",
        min_score=80.0,
        grading_scale="percentage",
        is_mandatory=True,
    )

    # 1. Satisfied
    student_pass = StudentFrame(
        subject_scores=[SubjectScore(subject_code="MATH", subject_name="Mathematics", score=85.0)]
    )
    res_pass = req.evaluate(student_pass)
    assert res_pass.status == RuleStatus.SATISFIED
    assert res_pass.is_satisfied is True
    assert "85.0%" in res_pass.observed_value

    # 2. Violated
    student_fail = StudentFrame(
        subject_scores=[SubjectScore(subject_code="MATH", subject_name="Mathematics", score=72.0)]
    )
    res_fail = req.evaluate(student_fail)
    assert res_fail.status == RuleStatus.VIOLATED
    assert res_fail.is_violated is True

    # 3. Missing fact -> NEEDS_REVIEW
    student_missing = StudentFrame(subject_scores=[])
    res_missing = req.evaluate(student_missing)
    assert res_missing.status == RuleStatus.NEEDS_REVIEW
    assert res_missing.needs_review is True
    assert len(res_missing.missing_facts) > 0

    # 4. Incompatible grading scale -> NEEDS_REVIEW
    student_scale = StudentFrame(
        subject_scores=[
            SubjectScore(
                subject_code="MATH",
                subject_name="Mathematics",
                score=9.0,
                max_score=10.0,
                grading_scale="cgpa_10",
            )
        ]
    )
    res_scale = req.evaluate(student_scale)
    assert res_scale.status == RuleStatus.NEEDS_REVIEW
    assert "Incompatible grading scale" in res_scale.explanation


def test_2_atomic_entrance_rank_requirement():
    """EntranceRankRequirement respects cutoffs, missing facts, and mandatory flags."""
    req_mandatory = EntranceRankRequirement(
        expression_id="REQ_JEE_10K",
        exam_name="JEE Main",
        max_rank=10000,
        is_mandatory=True,
    )

    # 1. Within cutoff -> SATISFIED
    st_pass = StudentFrame(entrance_exam_name="JEE Main", entrance_rank=8500)
    assert req_mandatory.evaluate(st_pass).status == RuleStatus.SATISFIED

    # 2. Worse than cutoff -> VIOLATED
    st_fail = StudentFrame(entrance_exam_name="JEE Main", entrance_rank=12500)
    assert req_mandatory.evaluate(st_fail).status == RuleStatus.VIOLATED

    # 3. Missing exam name -> NEEDS_REVIEW
    st_no_exam = StudentFrame(entrance_exam_name=None, entrance_rank=8500)
    assert req_mandatory.evaluate(st_no_exam).status == RuleStatus.NEEDS_REVIEW

    # 4. Incompatible examination name -> VIOLATED
    st_diff_exam = StudentFrame(entrance_exam_name="NEET", entrance_rank=2000)
    res_diff = req_mandatory.evaluate(st_diff_exam)
    assert res_diff.status == RuleStatus.VIOLATED
    assert "Incompatible entrance examination" in res_diff.explanation

    # 5. Non-mandatory missing rank remains SATISFIED (does not block eligibility)
    req_optional = EntranceRankRequirement(
        expression_id="REQ_JEE_OPTIONAL",
        exam_name="JEE Main",
        max_rank=10000,
        is_mandatory=False,
    )
    st_empty = StudentFrame()
    res_opt = req_optional.evaluate(st_empty)
    assert res_opt.status == RuleStatus.SATISFIED


def test_3_atomic_certification_requirement():
    """CertificationRequirement checks verified student certifications."""
    req = CertificationRequirement(
        expression_id="REQ_AWS_CERT",
        certification_name="AWS Solutions Architect",
        is_mandatory=True,
    )

    # 1. Possesses certification -> SATISFIED
    st_cert = StudentFrame(certifications=["AWS Solutions Architect", "Python Pro"])
    assert req.evaluate(st_cert).status == RuleStatus.SATISFIED

    # 2. Lacks certification -> NEEDS_REVIEW
    st_no_cert = StudentFrame(certifications=["Python Pro"])
    assert req.evaluate(st_no_cert).status == RuleStatus.NEEDS_REVIEW

    # 3. Optional certification missing -> NEEDS_REVIEW (non-mandatory)
    req_opt = CertificationRequirement(
        expression_id="REQ_OPT_CERT",
        certification_name="Docker Certified Associate",
        is_mandatory=False,
    )
    assert req_opt.evaluate(st_no_cert).status == RuleStatus.NEEDS_REVIEW
    assert req_opt.evaluate(st_no_cert).is_mandatory is False


def test_4_composite_all_of():
    """AllOf requires every mandatory child to be satisfied."""
    req_all = AllOf(
        expression_id="ALL_CS_CORE",
        children=[
            SubjectScoreRequirement("MATH", "MATH", 75.0, is_mandatory=True),
            SubjectScoreRequirement("PHY", "PHY", 70.0, is_mandatory=True),
        ],
    )

    # 1. All satisfied -> SATISFIED
    st_all_pass = StudentFrame(
        subject_scores=[
            SubjectScore("MATH", "Mathematics", 80.0),
            SubjectScore("PHY", "Physics", 75.0),
        ]
    )
    assert req_all.evaluate(st_all_pass).status == RuleStatus.SATISFIED

    # 2. One violated -> VIOLATED
    st_one_fail = StudentFrame(
        subject_scores=[
            SubjectScore("MATH", "Mathematics", 80.0),
            SubjectScore("PHY", "Physics", 65.0),
        ]
    )
    assert req_all.evaluate(st_one_fail).status == RuleStatus.VIOLATED

    # 3. One needs review, none violated -> NEEDS_REVIEW
    st_missing_phy = StudentFrame(
        subject_scores=[SubjectScore("MATH", "Mathematics", 80.0)]
    )
    assert req_all.evaluate(st_missing_phy).status == RuleStatus.NEEDS_REVIEW


def test_5_composite_any_of():
    """AnyOf succeeds if at least one branch is satisfied."""
    req_any = AnyOf(
        expression_id="ANY_ENTRY_PATHWAY",
        children=[
            SubjectScoreRequirement(subject_code="MATH", min_score=90.0, is_mandatory=True),
            EntranceRankRequirement(exam_name="JEE Main", max_rank=5000, is_mandatory=True),
        ],
    )

    # 1. First branch satisfied, second absent -> SATISFIED
    st_math_god = StudentFrame(
        subject_scores=[SubjectScore("MATH", "Mathematics", 95.0)]
    )
    assert req_any.evaluate(st_math_god).status == RuleStatus.SATISFIED

    # 2. First branch failed, second satisfied -> SATISFIED
    st_jee_champ = StudentFrame(
        subject_scores=[SubjectScore("MATH", "Mathematics", 60.0)],
        entrance_exam_name="JEE Main",
        entrance_rank=3000,
    )
    assert req_any.evaluate(st_jee_champ).status == RuleStatus.SATISFIED

    # 3. Both branches violated -> VIOLATED
    st_both_fail = StudentFrame(
        subject_scores=[SubjectScore("MATH", "Mathematics", 70.0)],
        entrance_exam_name="JEE Main",
        entrance_rank=15000,
    )
    assert req_any.evaluate(st_both_fail).status == RuleStatus.VIOLATED

    # 4. Neither satisfied, but at least one branch needs review -> NEEDS_REVIEW
    st_ambiguous = StudentFrame(
        subject_scores=[SubjectScore("MATH", "Mathematics", 70.0)]  # Math fails, entrance missing
    )
    assert req_any.evaluate(st_ambiguous).status == RuleStatus.NEEDS_REVIEW


def test_6_canonical_alternative_admission_pathways():
    """Full demonstration of dual pathways:
    (Math >= 80% AND Physics >= 75%) OR (JEE Main rank <= 15000)
    """
    boards_branch = AllOf(
        expression_id="BOARDS_PATHWAY",
        children=[
            SubjectScoreRequirement(subject_code="MATH", min_score=80.0, is_mandatory=True, expression_id="M_80"),
            SubjectScoreRequirement(subject_code="PHY", min_score=75.0, is_mandatory=True, expression_id="P_75"),
        ],
    )
    entrance_branch = EntranceRankRequirement(
        expression_id="JEE_PATHWAY",
        exam_name="JEE Main",
        max_rank=15000,
        is_mandatory=True,
    )
    admission_rule = AnyOf(
        expression_id="DUAL_ADMISSION_PATHWAY",
        children=[boards_branch, entrance_branch],
    )

    # Student A: High board marks, no entrance exam -> SATISFIED via boards
    st_a = StudentFrame(
        subject_scores=[
            SubjectScore("MATH", "Mathematics", 85.0),
            SubjectScore("PHY", "Physics", 80.0),
        ]
    )
    res_a = admission_rule.evaluate(st_a)
    assert res_a.status == RuleStatus.SATISFIED
    assert len(res_a.children) == 2
    assert res_a.children[0].status == RuleStatus.SATISFIED
    assert res_a.children[1].status == RuleStatus.NEEDS_REVIEW

    # Student B: Violated boards, excellent JEE Main rank -> SATISFIED via JEE
    st_b = StudentFrame(
        subject_scores=[
            SubjectScore("MATH", "Mathematics", 65.0),
            SubjectScore("PHY", "Physics", 60.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=8200,
    )
    res_b = admission_rule.evaluate(st_b)
    assert res_b.status == RuleStatus.SATISFIED
    assert res_b.children[0].status == RuleStatus.VIOLATED
    assert res_b.children[1].status == RuleStatus.SATISFIED

    # Student C: Violated boards, JEE rank beyond cutoff -> VIOLATED overall
    st_c = StudentFrame(
        subject_scores=[
            SubjectScore("MATH", "Mathematics", 65.0),
            SubjectScore("PHY", "Physics", 60.0),
        ],
        entrance_exam_name="JEE Main",
        entrance_rank=28000,
    )
    res_c = admission_rule.evaluate(st_c)
    assert res_c.status == RuleStatus.VIOLATED
    assert res_c.children[0].status == RuleStatus.VIOLATED
    assert res_c.children[1].status == RuleStatus.VIOLATED

    # Student D: Missing Physics, no entrance exam -> NEEDS_REVIEW overall
    st_d = StudentFrame(
        subject_scores=[SubjectScore("MATH", "Mathematics", 85.0)]
    )
    res_d = admission_rule.evaluate(st_d)
    assert res_d.status == RuleStatus.NEEDS_REVIEW


def test_7_expression_validation():
    """Empty expressions or invalid parameters raise ValueError."""
    with pytest.raises(ValueError, match="subject_code cannot be empty"):
        SubjectScoreRequirement("", "MATH", 80.0)

    with pytest.raises(ValueError, match="Cannot construct AllOf with empty children list"):
        AllOf("EMPTY_ALL", children=[])

    with pytest.raises(ValueError, match="Cannot construct AnyOf with empty children list"):
        AnyOf("EMPTY_ANY", children=[])
