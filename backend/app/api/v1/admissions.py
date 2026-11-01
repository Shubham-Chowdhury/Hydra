"""Admissions Knowledge Base API Endpoints (Phase 3)."""

from typing import List, Optional
from fastapi import APIRouter, Query

from app.api.schemas.admissions import (
    AdmissionCutoffDto,
    AdmissionsProgrammeDto,
    FormalEligibilityCriterionDto,
    PaginatedCutoffsResponse,
    PaginatedProgrammesResponse,
)
from app.services.admissions_service import AdmissionsService

router = APIRouter(prefix="/admissions", tags=["Admissions Knowledge Base"])
_service = AdmissionsService()


@router.get("/cutoffs", response_model=PaginatedCutoffsResponse)
def get_historical_cutoffs(
    academic_year: Optional[int] = Query(None, description="Academic/counselling year (e.g. 2026)"),
    institution: Optional[str] = Query(None, description="Filter by institution name or ID substring"),
    programme: Optional[str] = Query(None, description="Filter by programme title or ID substring"),
    counselling_round: Optional[int] = Query(None, ge=1, le=10, description="Counselling round number"),
    seat_type: Optional[str] = Query(None, description="Seat type / category (e.g. OPEN, GEN-EWS, OBC-NCL, SC, ST)"),
    quota: Optional[str] = Query(None, description="Counselling quota (e.g. AI, HS, OS)"),
    rank_basis: Optional[str] = Query(None, description="Rank basis (e.g. CRL, CATEGORY_RANK, PREPARATORY)"),
    source_status: Optional[str] = Query(None, description="Filter by source status (e.g. synthetic_demo, official_source, derived_from_official)"),
    is_synthetic: Optional[bool] = Query(None, description="Filter by synthetic vs official origin"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Record offset for pagination"),
):
    """Queries verified historical cutoff observations with deterministic filtering and pagination.

    DISCLAIMER:
    Historical cutoff observations describe past counselling outcomes.
    They do not guarantee future admission.
    """
    records, total_count = _service.query_cutoffs(
        academic_year=academic_year,
        institution=institution,
        programme=programme,
        counselling_round=counselling_round,
        seat_type=seat_type,
        quota=quota,
        rank_basis=rank_basis,
        source_status=source_status,
        is_synthetic=is_synthetic,
        limit=limit,
        offset=offset,
    )

    return PaginatedCutoffsResponse(
        total_count=total_count,
        limit=limit,
        offset=offset,
        results=[
            AdmissionCutoffDto(
                observation_id=c.observation_id,
                institution_id=c.institution_id,
                programme_id=c.programme_id,
                institution_name=c.institution_name,
                programme_title=c.programme_title,
                academic_year=c.academic_year,
                counselling_round=c.counselling_round,
                exam_name=c.exam_name,
                quota=c.quota,
                seat_type=c.seat_type,
                gender_pool=c.gender_pool,
                opening_rank=c.opening_rank,
                closing_rank=c.closing_rank,
                rank_basis=c.rank_basis,
                source_document_id=c.source_document_id,
                snapshot_id=c.snapshot_id,
                source_row_provenance=c.source_row_provenance,
                validation_status=c.validation_status.value,
                source_status=c.source_status.value,
                is_synthetic=c.is_synthetic,
                disclaimer=c.disclaimer,
            )
            for c in records
        ],
    )


@router.get("/programmes", response_model=PaginatedProgrammesResponse)
def get_admissions_programmes(
    academic_year: Optional[int] = Query(None, description="Academic year filter"),
    institution: Optional[str] = Query(None, description="Filter by institution identifier substring"),
    is_synthetic: Optional[bool] = Query(None, description="Filter by synthetic vs official origin"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Record offset for pagination"),
):
    """Retrieves unique academic programmes derived from admissions observations."""
    progs, total_count = _service.query_programmes(
        academic_year=academic_year,
        institution=institution,
        is_synthetic=is_synthetic,
        limit=limit,
        offset=offset,
    )

    return PaginatedProgrammesResponse(
        total_count=total_count,
        limit=limit,
        offset=offset,
        results=[
            AdmissionsProgrammeDto(
                programme_id=p.programme_id,
                institution_id=p.institution_id,
                official_title=p.official_title,
                academic_year=p.academic_year,
                degree_type=p.degree_type,
                discipline=p.discipline,
                duration_years=p.duration_years,
                source_references=p.source_references,
                provenance=p.provenance.value,
                is_synthetic=p.is_synthetic,
            )
            for p in progs
        ],
    )


@router.get("/eligibility-criteria", response_model=List[FormalEligibilityCriterionDto])
def get_formal_eligibility_criteria(
    academic_year: Optional[int] = Query(None, description="Filter by academic year"),
    criterion_scope: Optional[str] = Query(None, description="Filter by criterion scope (e.g. exam_appearance_eligibility)"),
):
    """Retrieves authoritative eligibility criteria published by official examination authorities."""
    criteria = _service.list_eligibility_criteria(academic_year=academic_year, criterion_scope=criterion_scope)
    return [
        FormalEligibilityCriterionDto(
            criterion_id=c.criterion_id,
            authority=c.authority,
            academic_year=c.academic_year,
            criterion_number=c.criterion_number,
            title=c.title,
            description=c.description,
            source_document_id=c.source_document_id,
            source_status=c.source_status.value,
            is_mandatory=c.is_mandatory,
            criterion_scope=c.criterion_scope,
            target_examination=c.target_examination,
        )
        for c in criteria
    ]

