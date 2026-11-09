"""FastAPI Router for Comprehensive Assessment & Career Pathway Reports."""

from fastapi import APIRouter, HTTPException, status
from app.api.schemas.assessment_report import (
    AssessmentReportRequest,
    ComprehensiveAssessmentReportDto,
    NeuralTrajectoryInsightsDto,
)
from app.services.assessment_report_service import AssessmentReportService

router = APIRouter(prefix="/assessment", tags=["Assessment & Career Pathways"])
report_service = AssessmentReportService()


@router.post(
    "/comprehensive-report",
    response_model=ComprehensiveAssessmentReportDto,
    status_code=status.HTTP_200_OK,
    summary="Generate comprehensive assessment and career pathway report with deep neural insights",
)
def generate_comprehensive_report(request: AssessmentReportRequest) -> ComprehensiveAssessmentReportDto:
    """Consolidates deterministic rule evaluations and deep trajectory sequence insights."""
    try:
        profile_dict = request.profile.model_dump()
        history_list = [h.model_dump() for h in request.interaction_history] if request.interaction_history else None

        report = report_service.generate_report(
            profile_data=profile_dict,
            interaction_history=history_list,
        )

        neural_dto = NeuralTrajectoryInsightsDto(
            career_readiness_score=report.neural_insights.career_readiness_score,
            domain_affinity_weights=report.neural_insights.domain_affinity_weights,
            learning_velocity_index=report.neural_insights.learning_velocity_index,
            risk_assessment_index=report.neural_insights.risk_assessment_index,
            projected_career_outcomes=report.neural_insights.projected_career_outcomes,
            model_architecture=report.neural_insights.model_architecture,
            confidence=report.neural_insights.confidence,
            is_estimate=report.neural_insights.is_estimate,
            provenance=report.neural_insights.provenance,
            is_synthetic=report.neural_insights.is_synthetic,
        )

        return ComprehensiveAssessmentReportDto(
            report_id=report.report_id,
            student_id=report.student_id,
            generated_at=report.generated_at,
            executive_summary=report.executive_summary,
            voice_script=report.voice_script,
            academic_standing=report.academic_standing,
            verified_eligibility_breakdown=report.verified_eligibility_breakdown,
            top_recommended_pathways=report.top_recommended_pathways,
            neural_insights=neural_dto,
            actionable_milestones=report.actionable_milestones,
            is_synthetic=report.is_synthetic,
            dataset_label=report.dataset_label,
            provenance=report.provenance,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {str(exc)}",
        ) from exc

