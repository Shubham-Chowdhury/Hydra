"""Programme catalogue retrieval endpoints."""

from typing import List
from fastapi import APIRouter

from app.api.schemas.programme import (
    AcademicPrerequisiteDto,
    EntrancePrerequisiteDto,
    ProgrammeResponse,
)
from app.services.programme_service import ProgrammeService

router = APIRouter(prefix="/programmes", tags=["Programmes"])
_baseline_programme_service = ProgrammeService(include_all_domains=False)
_multi_programme_service = ProgrammeService(include_all_domains=True)


@router.get("", response_model=List[ProgrammeResponse])
def get_programmes(all_domains: bool = False):
    """Retrieves the academic catalogue (default 4 baseline, or all multi-domain programmes if all_domains=true)."""
    service = _multi_programme_service if all_domains else _baseline_programme_service
    programmes = service.get_all()
    response = []
    for p in programmes:
        response.append(
            ProgrammeResponse(
                programme_id=p.programme_id,
                title=p.title,
                institution_name=p.institution_name,
                location=p.location,
                discipline=p.discipline,
                annual_tuition_inr=p.annual_tuition_inr,
                duration_years=p.duration_years,
                estimated_total_tuition_inr=p.estimated_total_tuition_inr,
                currency=p.currency,
                cost_basis=p.cost_basis,
                academic_prerequisites=[
                    AcademicPrerequisiteDto(
                        subject_code=ap.subject_code,
                        subject_name=ap.subject_name,
                        min_score=ap.min_score,
                        grading_scale=ap.grading_scale,
                        is_mandatory=ap.is_mandatory,
                    )
                    for ap in p.academic_prerequisites
                ],
                entrance_prerequisites=[
                    EntrancePrerequisiteDto(
                        exam_name=ep.exam_name,
                        max_rank=ep.max_rank,
                        is_mandatory=ep.is_mandatory,
                    )
                    for ep in p.entrance_prerequisites
                ],
                skills_developed=p.skills_developed,
                career_paths=p.career_paths,
                is_synthetic=p.is_synthetic,
                dataset_label=p.dataset_label,
                provenance=p.provenance,
            )
        )
    return response

