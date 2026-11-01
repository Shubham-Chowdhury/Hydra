"""Deterministic IF–THEN Rule Evaluator for Hydra.

Evaluates student profiles against programme prerequisites with full explanation traces,
nested ALL OF and ANY OF requirement expressions, and hierarchical reasoning trees.
Pure Python implementation with zero framework or network dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.domain.frames import (
    AcademicPrerequisite,
    CertificationPrerequisite,
    EligibilityStatus,
    EntrancePrerequisite,
    ProgrammeFrame,
    StudentFrame,
)
from app.rules.expressions import (
    AllOf,
    AnyOf,
    CertificationRequirement,
    EntranceRankRequirement,
    ExpressionEvaluationResult,
    RequirementExpression,
    RuleStatus,
    SubjectScoreRequirement,
)


@dataclass(frozen=True)
class RuleEvaluationRecord:
    """Detailed audit record of an individual evaluated rule."""

    rule_id: str
    rule_name: str
    status: RuleStatus
    facts_used: Dict[str, Any]
    expected_value: str
    observed_value: str
    explanation: str
    is_mandatory: bool = True


@dataclass
class ReasoningTreeNode:
    """Hierarchical node in an explainable reasoning tree."""

    node_id: str
    expression_type: str
    status: RuleStatus
    is_mandatory: bool
    expected_value: str
    observed_value: str
    facts_used: Dict[str, Any]
    evidence: List[str]
    missing_facts: List[str]
    explanation: str
    provenance: Optional[str] = None
    children: List["ReasoningTreeNode"] = field(default_factory=list)


@dataclass
class InferenceTrace:
    """Comprehensive, explainable reasoning trace for an evaluation."""

    programme_id: str
    final_status: EligibilityStatus
    rules_evaluated: List[RuleEvaluationRecord] = field(default_factory=list)
    rules_fired: List[RuleEvaluationRecord] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    missing_facts: List[str] = field(default_factory=list)
    summary_explanation: str = ""
    reasoning_tree: Optional[ReasoningTreeNode] = None


class RuleEngine:
    """Pure deterministic IF–THEN rule evaluation engine."""

    RULE_SUBJECT_PREREQUISITE = "RULE_SUBJECT_PREREQUISITE"
    RULE_GRADING_SCALE_COMPATIBILITY = "RULE_GRADING_SCALE_COMPATIBILITY"
    RULE_ENTRANCE_REQUIREMENT = "RULE_ENTRANCE_REQUIREMENT"
    RULE_CERTIFICATION_REQUIREMENT = "RULE_CERTIFICATION_REQUIREMENT"

    def evaluate(
        self,
        student: StudentFrame,
        programme: ProgrammeFrame,
        frame_registry: Optional[Any] = None,
    ) -> InferenceTrace:
        """Evaluates student eligibility against all mandatory prerequisites for a programme."""
        # 1. Determine or build the root requirement expression
        root_expr = programme.requirement_expression
        if root_expr is None:
            root_expr = self._build_default_expression_for_programme(programme)

        # 2. Evaluate the root expression under Three-Valued Logic
        result = root_expr.evaluate(student)

        # 3. Build ReasoningTreeNode hierarchy
        tree_node = self._build_reasoning_tree(result)

        # 4. Flatten atomic evaluation records for backward compatibility
        records: List[RuleEvaluationRecord] = []
        dummy_evidence: List[str] = []
        dummy_missing: List[str] = []
        self._flatten_tree_results(result, records, dummy_evidence, dummy_missing)

        # 5. Inspect frame hierarchy if frame_registry and parent_frame_id are present
        frame_conflict_records: List[RuleEvaluationRecord] = []
        frame_missing_facts: List[str] = []
        if programme.parent_frame_id and frame_registry:
            try:
                resolved_slots = frame_registry.resolve_slots(programme.parent_frame_id)
                for slot_name, slot_res in resolved_slots.items():
                    if slot_res.has_decision_relevant_conflict:
                        candidates_repr = [
                            c.competing_values for c in slot_res.conflicts
                        ]
                        frame_conflict_records.append(
                            RuleEvaluationRecord(
                                rule_id=f"RULE_FRAME_CONFLICT_{slot_name.upper()}",
                                rule_name=f"Frame Conflict: {slot_name}",
                                status=RuleStatus.NEEDS_REVIEW,
                                facts_used={
                                    "slot_name": slot_name,
                                    "conflict_candidates": candidates_repr,
                                },
                                expected_value="Unconflicted deterministic prerequisite",
                                observed_value=(
                                    f"Conflicting values from parents: "
                                    f"{slot_res.conflicts[0].competing_values if slot_res.conflicts else {}}"
                                ),
                                explanation=(
                                    f"Unresolved conflict in decision-relevant prerequisite slot '{slot_name}' "
                                    f"requires manual transcript evaluation."
                                ),
                                is_mandatory=True,
                            )
                        )
                        frame_missing_facts.append(
                            f"Unresolved conflict in decision-relevant prerequisite slot '{slot_name}' across frames {slot_res.inheritance_path}"
                        )
                    elif slot_res.has_unresolved_conflict:
                        # Descriptive slot conflict (is_decision_relevant=False)
                        # Recorded as informational non-mandatory record so it does NOT affect eligibility
                        frame_conflict_records.append(
                            RuleEvaluationRecord(
                                rule_id=f"RULE_DESCRIPTIVE_CONFLICT_{slot_name.upper()}",
                                rule_name=f"Descriptive Notice: {slot_name}",
                                status=RuleStatus.SATISFIED,
                                facts_used={
                                    "slot_name": slot_name,
                                    "conflict_candidates": [
                                        c.competing_values for c in slot_res.conflicts
                                    ],
                                },
                                expected_value="Informational display",
                                observed_value=f"Arbitrated to: {slot_res.resolved_value}",
                                explanation=(
                                    f"Descriptive slot '{slot_name}' has competing inherited values "
                                    f"arbitrated via precedence without affecting eligibility."
                                ),
                                is_mandatory=False,
                            )
                        )
            except Exception:
                pass

        records.extend(frame_conflict_records)

        # 6. Synthesize Overall Three-State Eligibility from the AST root evaluation and frame conflicts
        has_decision_frame_conflict = any(
            r.is_mandatory and r.status == RuleStatus.NEEDS_REVIEW
            for r in frame_conflict_records
        )

        if result.status == RuleStatus.VIOLATED:
            final_status = EligibilityStatus.INELIGIBLE
            summary = "Applicant does not satisfy one or more mandatory academic prerequisites."
        elif result.status == RuleStatus.NEEDS_REVIEW or has_decision_frame_conflict:
            final_status = EligibilityStatus.NEEDS_REVIEW
            summary = "Applicant profile is missing required information or requires manual transcript evaluation."
        else:
            final_status = EligibilityStatus.ELIGIBLE
            summary = "Applicant satisfies all verified mandatory prerequisites with positive evidence."

        # Filter rules fired (all that yielded conclusive satisfaction, violation, or review flag)
        rules_fired = [
            r
            for r in records
            if r.status in (RuleStatus.SATISFIED, RuleStatus.VIOLATED, RuleStatus.NEEDS_REVIEW)
        ]

        # Combine evidence and missing facts from root AST result plus frame conflicts
        combined_evidence = list(dict.fromkeys(result.evidence))
        combined_missing = list(dict.fromkeys(result.missing_facts + frame_missing_facts))

        return InferenceTrace(
            programme_id=programme.programme_id,
            final_status=final_status,
            rules_evaluated=records,
            rules_fired=rules_fired,
            evidence=combined_evidence,
            missing_facts=combined_missing,
            summary_explanation=summary,
            reasoning_tree=tree_node,
        )

    def _build_default_expression_for_programme(self, programme: ProgrammeFrame) -> RequirementExpression:
        """Constructs canonical AllOf expression from programme prerequisites."""
        exprs: List[RequirementExpression] = []

        # Academic prerequisites
        for prereq in programme.academic_prerequisites:
            exprs.append(
                SubjectScoreRequirement(
                    subject_code=prereq.subject_code,
                    subject_name=prereq.subject_name,
                    min_score=prereq.min_score,
                    grading_scale=prereq.grading_scale,
                    is_mandatory=prereq.is_mandatory,
                    expression_id=f"{self.RULE_SUBJECT_PREREQUISITE}_{prereq.subject_code.upper()}",
                )
            )

        # Entrance prerequisites
        for entrance_req in programme.entrance_prerequisites:
            exprs.append(
                EntranceRankRequirement(
                    exam_name=entrance_req.exam_name,
                    max_rank=entrance_req.max_rank,
                    is_mandatory=entrance_req.is_mandatory,
                    expression_id=f"{self.RULE_ENTRANCE_REQUIREMENT}_{entrance_req.exam_name.upper().replace(' ', '_')}",
                )
            )

        # Certification prerequisites
        for cert_req in programme.certification_prerequisites:
            exprs.append(
                CertificationRequirement(
                    certification_name=cert_req.certification_name,
                    is_mandatory=cert_req.is_mandatory,
                    expression_id=f"{self.RULE_CERTIFICATION_REQUIREMENT}_{cert_req.certification_name.upper().replace(' ', '_')}",
                )
            )

        if not exprs:
            # Neutral placeholder if no prerequisites defined
            return AllOf(
                requirements=[
                    SubjectScoreRequirement(
                        subject_code="GENERAL",
                        subject_name="General Eligibility",
                        min_score=0.0,
                        is_mandatory=False,
                    )
                ],
                label="General Programme Requirements",
            )

        return AllOf(
            requirements=exprs,
            expression_id=f"ROOT_ALL_OF_{programme.programme_id}",
            label=f"All Mandatory Prerequisites for {programme.title}",
        )

    def _build_reasoning_tree(self, result: ExpressionEvaluationResult) -> ReasoningTreeNode:
        """Recursively constructs ReasoningTreeNode tree from ExpressionEvaluationResult."""
        return ReasoningTreeNode(
            node_id=result.node_id,
            expression_type=result.expression_type,
            status=result.status,
            is_mandatory=result.is_mandatory,
            expected_value=result.expected_value,
            observed_value=result.observed_value,
            facts_used=result.facts_used,
            evidence=result.evidence,
            missing_facts=result.missing_facts,
            explanation=result.explanation,
            provenance=result.provenance,
            children=[self._build_reasoning_tree(c) for c in result.children],
        )

    def _flatten_tree_results(
        self,
        node: ExpressionEvaluationResult,
        records: List[RuleEvaluationRecord],
        evidence: List[str],
        missing_facts: List[str],
    ) -> None:
        """Flattens tree results into linear rule records for backward compatibility."""
        if not node.children:
            # Leaf node
            rule_id = self.RULE_SUBJECT_PREREQUISITE if node.expression_type == "SUBJECT_SCORE" else (
                self.RULE_ENTRANCE_REQUIREMENT if node.expression_type == "ENTRANCE_RANK" else (
                    self.RULE_CERTIFICATION_REQUIREMENT if node.expression_type == "CERTIFICATION" else node.node_id
                )
            )
            # If grading scale compatibility issue, use that rule id
            if any("grading scale" in m.lower() for m in node.missing_facts):
                rule_id = self.RULE_GRADING_SCALE_COMPATIBILITY

            records.append(
                RuleEvaluationRecord(
                    rule_id=rule_id,
                    rule_name=node.node_id,
                    status=node.status,
                    facts_used=node.facts_used,
                    expected_value=node.expected_value,
                    observed_value=node.observed_value,
                    explanation=node.explanation,
                    is_mandatory=node.is_mandatory,
                )
            )
            evidence.extend(node.evidence)
            if node.is_mandatory or node.status == RuleStatus.NEEDS_REVIEW:
                missing_facts.extend(node.missing_facts)
        else:
            for child in node.children:
                self._flatten_tree_results(child, records, evidence, missing_facts)
