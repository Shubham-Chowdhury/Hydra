"""Data Sources and Dataset Snapshots API Endpoints (Phase 3)."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.admissions import DatasetSnapshotDto, SourceDocumentDto
from app.services.admissions_service import AdmissionsService

router = APIRouter(prefix="/data-sources", tags=["Data Sources & Provenance"])
_service = AdmissionsService()


@router.get("", response_model=List[SourceDocumentDto])
def list_data_sources(
    status: Optional[str] = Query(None, description="Filter by SourceStatus (e.g. official_source, unverified, derived_from_official)"),
):
    """Retrieves all registered admissions data source documents and their verification status."""
    sources = _service.list_sources(status=status)
    return [
        SourceDocumentDto(
            source_id=s.source_id,
            title=s.title,
            issuing_authority=s.issuing_authority,
            canonical_url=s.canonical_url,
            source_type=s.source_type,
            academic_year=s.academic_year,
            retrieval_timestamp=s.retrieval_timestamp,
            source_status=s.source_status.value,
            publication_date=s.publication_date,
            original_artifact_path=s.original_artifact_path,
            sha256_checksum=s.sha256_checksum,
            document_version=s.document_version,
            access_notes=s.access_notes,
            verification_notes=s.verification_notes,
        )
        for s in sources
    ]


@router.get("/{source_id}", response_model=SourceDocumentDto)
def get_data_source(source_id: str):
    """Retrieves a specific source document by its stable identifier."""
    source = _service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Data source '{source_id}' not found.")
    return SourceDocumentDto(
        source_id=source.source_id,
        title=source.title,
        issuing_authority=source.issuing_authority,
        canonical_url=source.canonical_url,
        source_type=source.source_type,
        academic_year=source.academic_year,
        retrieval_timestamp=source.retrieval_timestamp,
        source_status=source.source_status.value,
        publication_date=source.publication_date,
        original_artifact_path=source.original_artifact_path,
        sha256_checksum=source.sha256_checksum,
        document_version=source.document_version,
        access_notes=source.access_notes,
        verification_notes=source.verification_notes,
    )


@router.get("/{source_id}/snapshots", response_model=List[DatasetSnapshotDto])
def list_snapshots_for_source(source_id: str):
    """Retrieves dataset snapshots associated with a given source document."""
    source = _service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Data source '{source_id}' not found.")

    all_snapshots = _service.list_snapshots()
    filtered = [snap for snap in all_snapshots if source_id in snap.source_document_ids]

    return [
        DatasetSnapshotDto(
            snapshot_id=snap.snapshot_id,
            dataset_id=snap.dataset_id,
            snapshot_version=snap.snapshot_version,
            academic_year=snap.academic_year,
            source_document_ids=snap.source_document_ids,
            importer_version=snap.importer_version,
            source_artifact_checksum=snap.source_artifact_checksum,
            created_at=snap.created_at,
            records_processed=snap.records_processed,
            records_accepted=snap.records_accepted,
            records_quarantined=snap.records_quarantined,
            records_duplicate=snap.records_duplicate,
            validation_status=snap.validation_status.value,
            quarantine_file_path=snap.quarantine_file_path,
        )
        for snap in filtered
    ]

