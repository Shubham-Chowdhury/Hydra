"""API Transport Schemas (Pydantic DTOs) for Admissions Knowledge Base (Phase 3)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceDocumentDto(BaseModel):
    """Metadata representing an authoritative or registered source document."""

    source_id: str
    title: str
    issuing_authority: str
    canonical_url: str
    source_type: str
    academic_year: int
    retrieval_timestamp: str
    source_status: str
    publication_date: Optional[str] = None
    original_artifact_path: Optional[str] = None
    sha256_checksum: Optional[str] = None
    document_version: Optional[str] = None
    access_notes: str = ""
    verification_notes: str = ""


class DatasetSnapshotDto(BaseModel):
    """Immutable record of an ingestion run and dataset snapshot."""

    snapshot_id: str
    dataset_id: str
    snapshot_version: str
    academic_year: int
    source_document_ids: List[str]
    importer_version: str
    source_artifact_checksum: str
    created_at: str
    records_processed: int
    records_accepted: int
    records_quarantined: int
    records_duplicate: int
    validation_status: str
    quarantine_file_path: Optional[str] = None


class AdmissionCutoffDto(BaseModel):
    """Historical cutoff observation DTO with mandatory disclaimer."""

    observation_id: str
    institution_id: str
    programme_id: str
    institution_name: str
    programme_title: str
    academic_year: int
    counselling_round: int
    exam_name: str
    quota: str
    seat_type: str
    gender_pool: str
    opening_rank: int
    closing_rank: int
    rank_basis: str
    source_document_id: str
    snapshot_id: str
    source_row_provenance: str
    validation_status: str
    source_status: str
    is_synthetic: bool = False
    disclaimer: str = Field(
        default="Historical cutoff observations describe past counselling outcomes. They do not guarantee future admission."
    )


class AdmissionsProgrammeDto(BaseModel):
    """Derived academic programme DTO from admissions observations."""

    programme_id: str
    institution_id: str
    official_title: str
    academic_year: int
    degree_type: Optional[str] = None
    discipline: Optional[str] = None
    duration_years: Optional[int] = 4
    source_references: List[str]
    provenance: str
    is_synthetic: bool = False


class FormalEligibilityCriterionDto(BaseModel):
    """Verified formal eligibility rule published by an authoritative body."""

    criterion_id: str
    authority: str
    academic_year: int
    criterion_number: str
    title: str
    description: str
    source_document_id: str
    source_status: str
    is_mandatory: bool = True
    criterion_scope: str = "exam_appearance_eligibility"
    target_examination: Optional[str] = "JEE (Advanced)"


class PaginatedCutoffsResponse(BaseModel):
    """Paginated list of historical cutoff observations."""

    total_count: int
    limit: int
    offset: int
    results: List[AdmissionCutoffDto]
    disclaimer: str = Field(
        default="Historical cutoff observations describe past counselling outcomes. They do not guarantee future admission."
    )


class PaginatedProgrammesResponse(BaseModel):
    """Paginated list of admissions programmes."""

    total_count: int
    limit: int
    offset: int
    results: List[AdmissionsProgrammeDto]

