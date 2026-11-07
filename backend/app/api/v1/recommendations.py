"""Student profile evaluation and recommendation endpoint."""

from typing import Optional

from fastapi import APIRouter

from app.api.schemas.recommendation import (
    AffordabilityDto,
    DataProvenanceDto,
    DiscoveredRelationshipDto,
    EvaluationResponse,
    PreferenceFitDto,
    ProgrammeEvaluationDto,
    ReasoningTreeNodeDto,
    RuleOutcomeDto,
)
from app.api.schemas.student import StudentProfileRequest
from app.domain.frames import StudentFrame, SubjectScore
from app.rules.engine import ReasoningTreeNode
from app.services.evaluation import EvaluationService
from app.services.programme_service import ProgrammeService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])
_baseline_eval_service = EvaluationService(programme_service=ProgrammeService(include_all_domains=False))
_multi_eval_service = EvaluationService(programme_service=ProgrammeService(include_all_domains=True))


def _map_reasoning_tree(node: Optional[ReasoningTreeNode]) -> Optional[ReasoningTreeNodeDto]:
    """Recursively converts internal domain ReasoningTreeNode to ReasoningTreeNodeDto."""
    if node is None:
        return None
    return ReasoningTreeNodeDto(
        node_id=node.node_id,
        expression_type=node.expression_type,
        status=node.status.value if hasattr(node.status, "value") else str(node.status),
        is_mandatory=node.is_mandatory,
        expected_value=node.expected_value,
        observed_value=node.observed_value,
        facts_used=node.facts_used,
        evidence=node.evidence,
        missing_facts=node.missing_facts,
        explanation=node.explanation,
        provenance=node.provenance,
        children=[_map_reasoning_tree(child) for child in node.children if child is not None],
    )


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_student_profile(payload: StudentProfileRequest, all_domains: bool = False):
    """Evaluates a student profile against academic programmes."""
    # Convert boundary DTO into internal domain frame
    student_frame = StudentFrame(
        student_id=payload.student_id,
        subject_scores=[
            SubjectScore(
                subject_code=s.subject_code,
                subject_name=s.subject_name,
                score=s.score,
                max_score=s.max_score,
                grading_scale=s.grading_scale,
            )
            for s in payload.subject_scores
        ],
        entrance_exam_name=payload.entrance_exam_name,
        entrance_rank=payload.entrance_rank,
        preferred_locations=payload.preferred_locations,
        total_budget_inr=payload.total_budget_inr,
        preferred_disciplines=payload.preferred_disciplines,
        career_goals=payload.career_goals,
        certifications=payload.certifications,
    )

    # Coordinate domain evaluation
    eval_service = _multi_eval_service if all_domains else _baseline_eval_service
    bundle = eval_service.evaluate_profile(student_frame)

    # Convert domain results into wire DTOs
    evaluations_dto = []
    for ev in bundle.evaluations:
        evaluations_dto.append(
            ProgrammeEvaluationDto(
                programme_id=ev.programme.programme_id,
                programme_title=ev.programme.title,
                institution_name=ev.programme.institution_name,
                location=ev.programme.location,
                discipline=ev.programme.discipline,
                eligibility_status=ev.trace.final_status.value,
                affordability=AffordabilityDto(
                    is_affordable=ev.affordability.is_affordable,
                    total_budget_inr=ev.affordability.total_budget_inr,
                    estimated_total_tuition_inr=ev.affordability.estimated_total_tuition_inr,
                    currency=ev.affordability.currency,
                    cost_basis=ev.affordability.cost_basis,
                ),
                preference_fit=PreferenceFitDto(
                    fit_score=ev.preference_fit.fit_score,
                    criteria_breakdown=ev.preference_fit.criteria_breakdown,
                    notes=ev.preference_fit.notes,
                ),
                evidence=ev.trace.evidence,
                rules_fired=[
                    RuleOutcomeDto(
                        rule_id=r.rule_id,
                        rule_name=r.rule_name,
                        status=r.status.value,
                        facts_used=r.facts_used,
                        expected_value=r.expected_value,
                        observed_value=r.observed_value,
                        explanation=r.explanation,
                        is_mandatory=r.is_mandatory,
                    )
                    for r in ev.trace.rules_evaluated
                ],
                reasoning_trace=ev.trace.summary_explanation,
                missing_facts=ev.trace.missing_facts,
                data_provenance=DataProvenanceDto(
                    is_synthetic=ev.programme.is_synthetic,
                    dataset_label=ev.programme.dataset_label,
                    provenance=ev.programme.provenance,
                ),
                discovered_relationships=[
                    DiscoveredRelationshipDto(
                        source=rel.source,
                        relationship=rel.relationship,
                        target=rel.target,
                        target_type=rel.target_type,
                        source_type=rel.source_type,
                        provenance_path=list(rel.provenance_path),
                    )
                    for rel in ev.discovered_relationships
                ],
                reasoning_tree=_map_reasoning_tree(ev.trace.reasoning_tree),
                parent_frame_id=ev.programme.parent_frame_id,
            )
        )

    all_relationships_dto = [
        DiscoveredRelationshipDto(
            source=rel.source,
            relationship=rel.relationship,
            target=rel.target,
            target_type=rel.target_type,
            source_type=rel.source_type,
            provenance_path=list(rel.provenance_path),
        )
        for rel in bundle.discovered_relationships
    ]

    return EvaluationResponse(
        evaluations=evaluations_dto,
        discovered_relationships=all_relationships_dto,
        is_synthetic=bundle.is_synthetic,
        audit_timestamp=bundle.audit_timestamp,
    )

