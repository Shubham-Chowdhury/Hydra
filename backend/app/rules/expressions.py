"""Requirement Expression AST and Three-Valued Logic for Hydra.

Implements structured atomic requirements (SubjectScore, EntranceRank, Certification)
and composite requirements (AllOf, AnyOf) with deterministic three-valued truth semantics:
SATISFIED, VIOLATED, and NEEDS_REVIEW.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.domain.frames import StudentFrame


class RuleStatus(str, Enum):
    """The three-valued outcome of a rule or requirement evaluation."""

    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass
class ExpressionEvaluationResult:
    """The structured evaluation outcome of an expression node in the reasoning tree."""

    node_id: str
    expression_type: str
    status: RuleStatus
    is_mandatory: bool
    expected_value: str
    observed_value: str
    facts_used: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    missing_facts: List[str] = field(default_factory=list)
    explanation: str = ""
    provenance: Optional[str] = None
    children: List["ExpressionEvaluationResult"] = field(default_factory=list)

    @property
    def is_satisfied(self) -> bool:
        return self.status == RuleStatus.SATISFIED

    @property
    def is_violated(self) -> bool:
        return self.status == RuleStatus.VIOLATED

    @property
    def needs_review(self) -> bool:
        return self.status == RuleStatus.NEEDS_REVIEW


class RequirementExpression(ABC):
    """Abstract base class for all prerequisite requirement expressions."""

    def __init__(self, expression_id: str, is_mandatory: bool = True, label: Optional[str] = None) -> None:
        if not expression_id or not expression_id.strip():
            raise ValueError("expression_id cannot be empty")
        self.expression_id = expression_id.strip()
        self.is_mandatory = is_mandatory
        self.label = label or self.expression_id

    @abstractmethod
    def evaluate(self, student: StudentFrame, context: Optional[Dict[str, Any]] = None) -> ExpressionEvaluationResult:
        """Evaluates the requirement against a student frame under three-valued logic."""
        pass


class SubjectScoreRequirement(RequirementExpression):
    """Atomic academic prerequisite requiring a minimum subject score."""

    def __init__(
        self,
        subject_code: str,
        subject_name: Optional[str] = None,
        min_score: float = 0.0,
        grading_scale: str = "percentage",
        is_mandatory: bool = True,
        expression_id: Optional[str] = None,
    ) -> None:
        if expression_id is not None and not expression_id.strip():
            raise ValueError("expression_id cannot be empty")
        if not subject_code or not subject_code.strip():
            raise ValueError("subject_code cannot be empty")
        code = subject_code.strip().upper()
        name = (subject_name or code).strip()
        expr_id = expression_id if expression_id and expression_id.strip() else f"REQ_SUBJ_{code}"
        super().__init__(expression_id=expr_id, is_mandatory=is_mandatory, label=f"Subject Benchmark: {name}")
        if min_score < 0:
            raise ValueError("min_score cannot be negative")
        self.subject_code = code
        self.subject_name = name
        self.min_score = min_score
        self.grading_scale = grading_scale.strip().lower()

    def evaluate(self, student: StudentFrame, context: Optional[Dict[str, Any]] = None) -> ExpressionEvaluationResult:
        score_entry = student.get_subject_score(self.subject_code)

        if score_entry is None:
            msg = f"Subject score for '{self.subject_name}' ({self.subject_code}) is missing."
            return ExpressionEvaluationResult(
                node_id=self.expression_id,
                expression_type="SUBJECT_SCORE",
                status=RuleStatus.NEEDS_REVIEW,
                is_mandatory=self.is_mandatory,
                expected_value=f">={self.min_score:.1f}% in {self.grading_scale}",
                observed_value="NOT_REPORTED",
                facts_used={"subject_code": self.subject_code, "status": "NOT_REPORTED"},
                missing_facts=[msg],
                explanation=f"Required subject '{self.subject_name}' was not found in the student profile.",
                provenance="STUDENT_PROFILE_EVALUATION",
            )

        # Grading scale guard
        student_scale = score_entry.grading_scale.strip().lower()
        if student_scale != self.grading_scale and student_scale != "percentage":
            incompatible_msg = (
                f"Incompatible grading scale: Grading scale '{score_entry.grading_scale}' for '{self.subject_name}' "
                f"cannot be directly compared with required '{self.grading_scale}' without verified conversion."
            )
            return ExpressionEvaluationResult(
                node_id=self.expression_id,
                expression_type="SUBJECT_SCORE",
                status=RuleStatus.NEEDS_REVIEW,
                is_mandatory=self.is_mandatory,
                expected_value=self.grading_scale,
                observed_value=student_scale,
                facts_used={
                    "subject_code": self.subject_code,
                    "student_scale": score_entry.grading_scale,
                    "required_scale": self.grading_scale,
                },
                missing_facts=[incompatible_msg],
                explanation=incompatible_msg,
                provenance="STUDENT_TRANSCRIPT",
            )

        # Normalize score
        effective_pct = score_entry.normalized_percentage
        if effective_pct is None:
            effective_pct = score_entry.score

        facts = {
            "subject_code": self.subject_code,
            "subject_name": self.subject_name,
            "raw_score": score_entry.score,
            "max_score": score_entry.max_score,
            "effective_percentage": round(effective_pct, 2),
        }

        if effective_pct >= self.min_score:
            ev = f"{self.subject_name} score of {effective_pct:.1f}% satisfies the minimum benchmark of {self.min_score:.1f}%"
            return ExpressionEvaluationResult(
                node_id=self.expression_id,
                expression_type="SUBJECT_SCORE",
                status=RuleStatus.SATISFIED,
                is_mandatory=self.is_mandatory,
                expected_value=f">={self.min_score:.1f}%",
                observed_value=f"{effective_pct:.1f}%",
                facts_used=facts,
                evidence=[ev],
                explanation=ev,
                provenance="STUDENT_TRANSCRIPT",
            )
        else:
            ev = f"{self.subject_name} score of {effective_pct:.1f}% is below the required minimum benchmark of {self.min_score:.1f}%"
            return ExpressionEvaluationResult(
                node_id=self.expression_id,
                expression_type="SUBJECT_SCORE",
                status=RuleStatus.VIOLATED,
                is_mandatory=self.is_mandatory,
                expected_value=f">={self.min_score:.1f}%",
                observed_value=f"{effective_pct:.1f}%",
                facts_used=facts,
                evidence=[ev],
                explanation=ev,
                provenance="STUDENT_TRANSCRIPT",
            )


class EntranceRankRequirement(RequirementExpression):
    """Atomic entrance exam benchmark requirement with strict mandatory vs optional semantics."""

    def __init__(
        self,
        exam_name: str,
        max_rank: Optional[int] = None,
        is_mandatory: bool = False,
        expression_id: Optional[str] = None,
    ) -> None:
        if expression_id is not None and not expression_id.strip():
            raise ValueError("expression_id cannot be empty")
        if not exam_name or not exam_name.strip():
            raise ValueError("exam_name cannot be empty")
        name = exam_name.strip()
        expr_id = expression_id if expression_id and expression_id.strip() else f"REQ_ENTRANCE_{name.upper().replace(' ', '_')}"
        super().__init__(expression_id=expr_id, is_mandatory=is_mandatory, label=f"Entrance Exam: {name}")
        self.exam_name = name
        self.max_rank = max_rank

    def evaluate(self, student: StudentFrame, context: Optional[Dict[str, Any]] = None) -> ExpressionEvaluationResult:
        expected = f"Rank <={self.max_rank}" if self.max_rank else "Exam Taken"

        # Case 1: Student did not report taking any entrance examination
        if not student.entrance_exam_name:
            if self.is_mandatory:
                msg = f"Mandatory entrance examination '{self.exam_name}' was not taken or reported."
                return ExpressionEvaluationResult(
                    node_id=self.expression_id,
                    expression_type="ENTRANCE_RANK",
                    status=RuleStatus.NEEDS_REVIEW,
                    is_mandatory=True,
                    expected_value=expected,
                    observed_value="NOT_REPORTED",
                    facts_used={"exam_name": self.exam_name, "status": "NOT_REPORTED"},
                    missing_facts=[msg],
                    explanation=msg,
                    provenance="STUDENT_PROFILE",
                )
            else:
                msg = f"Optional entrance examination '{self.exam_name}' was not taken; does not affect eligibility."
                return ExpressionEvaluationResult(
                    node_id=self.expression_id,
                    expression_type="ENTRANCE_RANK",
                    status=RuleStatus.SATISFIED,
                    is_mandatory=False,
                    expected_value=expected,
                    observed_value="NOT_REPORTED",
                    facts_used={"exam_name": self.exam_name, "status": "NOT_REPORTED"},
                    explanation=msg,
                    provenance="STUDENT_PROFILE",
                )

        # Case 2: Incompatible Examination
        exam_match = student.entrance_exam_name.strip().lower() == self.exam_name.strip().lower()
        if not exam_match:
            if self.is_mandatory:
                msg = (
                    f"Incompatible entrance examination: Reported entrance examination '{student.entrance_exam_name}' "
                    f"is incompatible with required mandatory '{self.exam_name}'."
                )
                return ExpressionEvaluationResult(
                    node_id=self.expression_id,
                    expression_type="ENTRANCE_RANK",
                    status=RuleStatus.VIOLATED,
                    is_mandatory=True,
                    expected_value=f"Exam: {self.exam_name}",
                    observed_value=f"Exam: {student.entrance_exam_name}",
                    facts_used={"reported_exam": student.entrance_exam_name, "required_exam": self.exam_name},
                    evidence=[msg],
                    explanation=msg,
                    provenance="STUDENT_PROFILE",
                )
            else:
                msg = (
                    f"Incompatible entrance examination: Reported entrance examination '{student.entrance_exam_name}' "
                    f"does not match optional benchmark '{self.exam_name}'. Non-mandatory criterion does not affect eligibility."
                )
                return ExpressionEvaluationResult(
                    node_id=self.expression_id,
                    expression_type="ENTRANCE_RANK",
                    status=RuleStatus.NEEDS_REVIEW,
                    is_mandatory=False,
                    expected_value=f"Optional Exam: {self.exam_name}",
                    observed_value=f"Exam: {student.entrance_exam_name}",
                    facts_used={"reported_exam": student.entrance_exam_name, "optional_exam": self.exam_name},
                    explanation=msg,
                    provenance="STUDENT_PROFILE",
                )

        # Case 3: Matching Exam Reported
        if self.max_rank is not None:
            if student.entrance_rank is None:
                if self.is_mandatory:
                    msg = f"Mandatory entrance examination '{self.exam_name}' was taken, but rank was not reported."
                    return ExpressionEvaluationResult(
                        node_id=self.expression_id,
                        expression_type="ENTRANCE_RANK",
                        status=RuleStatus.NEEDS_REVIEW,
                        is_mandatory=True,
                        expected_value=f"<={self.max_rank}",
                        observed_value="NOT_REPORTED",
                        facts_used={"exam": self.exam_name, "rank": "MISSING"},
                        missing_facts=[msg],
                        explanation=msg,
                        provenance="STUDENT_PROFILE",
                    )
                else:
                    msg = (
                        f"Optional entrance examination '{self.exam_name}' rank was not reported; "
                        f"this non-mandatory criterion does not affect overall eligibility."
                    )
                    return ExpressionEvaluationResult(
                        node_id=self.expression_id,
                        expression_type="ENTRANCE_RANK",
                        status=RuleStatus.NEEDS_REVIEW,
                        is_mandatory=False,
                        expected_value=f"Optional Rank <={self.max_rank}",
                        observed_value="NOT_REPORTED",
                        facts_used={"exam": self.exam_name, "rank": "NOT_REPORTED"},
                        explanation=msg,
                        provenance="STUDENT_PROFILE",
                    )
            elif student.entrance_rank <= self.max_rank:
                tier = "mandatory" if self.is_mandatory else "optional"
                ev = f"Reported {self.exam_name} rank {student.entrance_rank} satisfies {tier} cutoff benchmark (threshold <={self.max_rank})"
                return ExpressionEvaluationResult(
                    node_id=self.expression_id,
                    expression_type="ENTRANCE_RANK",
                    status=RuleStatus.SATISFIED,
                    is_mandatory=self.is_mandatory,
                    expected_value=f"<={self.max_rank}",
                    observed_value=f"{student.entrance_rank}",
                    facts_used={"exam": self.exam_name, "rank": student.entrance_rank},
                    evidence=[ev],
                    explanation=ev,
                    provenance="STUDENT_PROFILE",
                )
            else:
                if self.is_mandatory:
                    ev = f"Reported {self.exam_name} rank {student.entrance_rank} exceeds mandatory cutoff benchmark (threshold <={self.max_rank})"
                    return ExpressionEvaluationResult(
                        node_id=self.expression_id,
                        expression_type="ENTRANCE_RANK",
                        status=RuleStatus.VIOLATED,
                        is_mandatory=True,
                        expected_value=f"<={self.max_rank}",
                        observed_value=f"{student.entrance_rank}",
                        facts_used={"exam": self.exam_name, "rank": student.entrance_rank},
                        evidence=[ev],
                        explanation=ev,
                        provenance="STUDENT_PROFILE",
                    )
                else:
                    ev = (
                        f"Reported {self.exam_name} rank {student.entrance_rank} exceeds optional cutoff "
                        f"benchmark (threshold <={self.max_rank}), but this criterion is non-mandatory and does not disqualify the applicant"
                    )
                    return ExpressionEvaluationResult(
                        node_id=self.expression_id,
                        expression_type="ENTRANCE_RANK",
                        status=RuleStatus.VIOLATED,
                        is_mandatory=False,
                        expected_value=f"<={self.max_rank}",
                        observed_value=f"{student.entrance_rank}",
                        facts_used={"exam": self.exam_name, "rank": student.entrance_rank},
                        evidence=[ev],
                        explanation=ev,
                        provenance="STUDENT_PROFILE",
                    )

        return ExpressionEvaluationResult(
            node_id=self.expression_id,
            expression_type="ENTRANCE_RANK",
            status=RuleStatus.SATISFIED,
            is_mandatory=self.is_mandatory,
            expected_value="Exam Reported",
            observed_value=self.exam_name,
            facts_used={"exam": self.exam_name},
            evidence=[f"Verified participation in '{self.exam_name}'."],
            explanation=f"Verified participation in '{self.exam_name}'.",
            provenance="STUDENT_PROFILE",
        )


class CertificationRequirement(RequirementExpression):
    """Atomic requirement verifying a student training or portfolio certification."""

    def __init__(
        self,
        certification_name: Optional[str] = None,
        is_mandatory: bool = True,
        expression_id: Optional[str] = None,
        certification_name_or_id: Optional[str] = None,
    ) -> None:
        c_name = certification_name or certification_name_or_id
        if not c_name or not c_name.strip():
            raise ValueError("certification_name cannot be empty")
        name = c_name.strip()
        expr_id = expression_id if expression_id and expression_id.strip() else f"REQ_CERT_{name.upper().replace(' ', '_')}"
        super().__init__(expression_id=expr_id, is_mandatory=is_mandatory, label=f"Certification: {name}")
        self.certification_name = name

    def evaluate(self, student: StudentFrame, context: Optional[Dict[str, Any]] = None) -> ExpressionEvaluationResult:
        target_norm = self.certification_name.strip().lower()
        has_cert = any(c.strip().lower() == target_norm for c in student.certifications)

        if has_cert:
            ev = f"Verified completion of '{self.certification_name}'."
            return ExpressionEvaluationResult(
                node_id=self.expression_id,
                expression_type="CERTIFICATION",
                status=RuleStatus.SATISFIED,
                is_mandatory=self.is_mandatory,
                expected_value="CERTIFIED",
                observed_value="CERTIFIED",
                facts_used={"certification": self.certification_name, "verified": True},
                evidence=[ev],
                explanation=ev,
                provenance="STUDENT_PORTFOLIO",
            )
        else:
            if self.is_mandatory:
                msg = f"Mandatory certification '{self.certification_name}' is not reported."
                return ExpressionEvaluationResult(
                    node_id=self.expression_id,
                    expression_type="CERTIFICATION",
                    status=RuleStatus.NEEDS_REVIEW,
                    is_mandatory=True,
                    expected_value="CERTIFIED",
                    observed_value="NOT_REPORTED",
                    facts_used={"certification": self.certification_name, "verified": False},
                    missing_facts=[msg],
                    explanation=msg,
                    provenance="STUDENT_PORTFOLIO",
                )
            else:
                msg = f"Optional certification '{self.certification_name}' is not reported; does not affect eligibility."
                return ExpressionEvaluationResult(
                    node_id=self.expression_id,
                    expression_type="CERTIFICATION",
                    status=RuleStatus.NEEDS_REVIEW,
                    is_mandatory=False,
                    expected_value="CERTIFIED",
                    observed_value="NOT_REPORTED",
                    facts_used={"certification": self.certification_name, "verified": False},
                    explanation=msg,
                    provenance="STUDENT_PORTFOLIO",
                )


class AllOf(RequirementExpression):
    """Composite logical requirement: ALL constituent requirements must be satisfied (Conjunction)."""

    def __init__(
        self,
        expression_id_or_requirements: Optional[Any] = None,
        requirements: Optional[List[RequirementExpression]] = None,
        is_mandatory: bool = True,
        expression_id: Optional[str] = None,
        label: Optional[str] = None,
        children: Optional[List[RequirementExpression]] = None,
    ) -> None:
        expr_id = expression_id
        child_list = children if children is not None else requirements
        if isinstance(expression_id_or_requirements, (list, tuple)):
            child_list = child_list or list(expression_id_or_requirements)
        elif isinstance(expression_id_or_requirements, str):
            expr_id = expr_id or expression_id_or_requirements

        if not child_list:
            raise ValueError("Cannot construct AllOf with empty children list.")
        if expr_id is not None and not expr_id.strip():
            raise ValueError("expression_id cannot be empty")
        final_id = expr_id.strip() if expr_id and expr_id.strip() else f"ALL_OF_{id(self)}"
        super().__init__(expression_id=final_id, is_mandatory=is_mandatory, label=label or "Conjunction (All Of)")
        self.requirements = child_list

    @property
    def children(self) -> List[RequirementExpression]:
        return self.requirements

    def evaluate(self, student: StudentFrame, context: Optional[Dict[str, Any]] = None) -> ExpressionEvaluationResult:
        child_results: List[ExpressionEvaluationResult] = []
        all_evidence: List[str] = []
        all_missing: List[str] = []
        aggregated_facts: Dict[str, Any] = {}

        has_mandatory_violation = False
        has_mandatory_needs_review = False

        for req in self.requirements:
            res = req.evaluate(student, context)
            child_results.append(res)
            all_evidence.extend(res.evidence)
            all_missing.extend(res.missing_facts)
            aggregated_facts.update(res.facts_used)

            if res.is_mandatory:
                if res.status == RuleStatus.VIOLATED:
                    has_mandatory_violation = True
                elif res.status == RuleStatus.NEEDS_REVIEW:
                    has_mandatory_needs_review = True

        # Three-Valued Logic for ALL OF:
        # 1. Any mandatory child violated => VIOLATED
        # 2. No child violated but at least one mandatory child needs review => NEEDS_REVIEW
        # 3. All mandatory children satisfied => SATISFIED
        if has_mandatory_violation:
            status = RuleStatus.VIOLATED
            explanation = "One or more mandatory requirements in the conjunction were violated."
        elif has_mandatory_needs_review:
            status = RuleStatus.NEEDS_REVIEW
            explanation = "One or more mandatory requirements in the conjunction require review or are missing."
        else:
            status = RuleStatus.SATISFIED
            explanation = "All constituent requirements in the conjunction are satisfied."

        return ExpressionEvaluationResult(
            node_id=self.expression_id,
            expression_type="ALL_OF",
            status=status,
            is_mandatory=self.is_mandatory,
            expected_value="All conditions satisfied",
            observed_value=status.value,
            facts_used=aggregated_facts,
            evidence=all_evidence,
            missing_facts=all_missing,
            explanation=explanation,
            provenance="COMPOSITE_CONJUNCTION",
            children=child_results,
        )


class AnyOf(RequirementExpression):
    """Composite logical requirement: AT LEAST ONE alternative must be satisfied (Disjunction)."""

    def __init__(
        self,
        expression_id_or_requirements: Optional[Any] = None,
        requirements: Optional[List[RequirementExpression]] = None,
        is_mandatory: bool = True,
        expression_id: Optional[str] = None,
        label: Optional[str] = None,
        children: Optional[List[RequirementExpression]] = None,
    ) -> None:
        expr_id = expression_id
        child_list = children if children is not None else requirements
        if isinstance(expression_id_or_requirements, (list, tuple)):
            child_list = child_list or list(expression_id_or_requirements)
        elif isinstance(expression_id_or_requirements, str):
            expr_id = expr_id or expression_id_or_requirements

        if not child_list:
            raise ValueError("Cannot construct AnyOf with empty children list.")
        if expr_id is not None and not expr_id.strip():
            raise ValueError("expression_id cannot be empty")
        final_id = expr_id.strip() if expr_id and expr_id.strip() else f"ANY_OF_{id(self)}"
        super().__init__(expression_id=final_id, is_mandatory=is_mandatory, label=label or "Disjunction (Any Of)")
        self.requirements = child_list

    @property
    def children(self) -> List[RequirementExpression]:
        return self.requirements

    def evaluate(self, student: StudentFrame, context: Optional[Dict[str, Any]] = None) -> ExpressionEvaluationResult:
        child_results: List[ExpressionEvaluationResult] = []
        all_evidence: List[str] = []
        all_missing: List[str] = []
        aggregated_facts: Dict[str, Any] = {}

        satisfied_children: List[ExpressionEvaluationResult] = []
        violated_children: List[ExpressionEvaluationResult] = []
        needs_review_children: List[ExpressionEvaluationResult] = []

        for req in self.requirements:
            res = req.evaluate(student, context)
            child_results.append(res)
            aggregated_facts.update(res.facts_used)

            if res.status == RuleStatus.SATISFIED:
                satisfied_children.append(res)
                all_evidence.extend(res.evidence)
            elif res.status == RuleStatus.VIOLATED:
                violated_children.append(res)
                all_evidence.extend(res.evidence)
            else:
                needs_review_children.append(res)
                all_missing.extend(res.missing_facts)

        # Three-Valued Logic for ANY OF:
        # 1. At least one alternative is SATISFIED => SATISFIED
        # 2. Every alternative is explicitly VIOLATED => VIOLATED
        # 3. No alternative satisfied, but at least one NEEDS_REVIEW => NEEDS_REVIEW
        if len(satisfied_children) > 0:
            status = RuleStatus.SATISFIED
            explanation = (
                f"Alternative admission pathway satisfied via '{satisfied_children[0].node_id}'."
            )
            # When satisfied, missing facts from other unchosen alternatives do not block eligibility
            all_missing = []
        elif len(violated_children) == len(self.requirements):
            status = RuleStatus.VIOLATED
            explanation = "All alternative admission pathways in the disjunction were violated."
        else:
            status = RuleStatus.NEEDS_REVIEW
            explanation = (
                "No alternative admission pathway is satisfied, and one or more alternatives require review."
            )

        return ExpressionEvaluationResult(
            node_id=self.expression_id,
            expression_type="ANY_OF",
            status=status,
            is_mandatory=self.is_mandatory,
            expected_value="At least one alternative satisfied",
            observed_value=status.value,
            facts_used=aggregated_facts,
            evidence=all_evidence,
            missing_facts=all_missing,
            explanation=explanation,
            provenance="COMPOSITE_DISJUNCTION",
            children=child_results,
        )
