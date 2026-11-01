"""Typed Provenance and Source Metadata Domain Models for Hydra (Phase 3).

Establishes strict tracking of source documents, dataset snapshots, and row-level
provenance across official, derived, synthetic, and unverified admission data.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceStatus(str, Enum):
    """Explicit, validated data-source classification."""

    OFFICIAL_SOURCE = "official_source"
    DERIVED_FROM_OFFICIAL = "derived_from_official"
    SYNTHETIC_DEMO = "synthetic_demo"
    UNVERIFIED = "unverified"


class ValidationStatus(str, Enum):
    """Validation lifecycle status for records and dataset snapshots."""

    VALID = "valid"
    QUARANTINED = "quarantined"
    PENDING = "pending"


@dataclass(frozen=True)
class SourceDocument:
    """Metadata representing an authoritative or registered source document."""

    source_id: str
    title: str
    issuing_authority: str
    canonical_url: str
    source_type: str  # e.g., "html_webpage", "counselling_report_csv", "bulletin_pdf"
    academic_year: int
    retrieval_timestamp: str  # UTC ISO 8601
    source_status: SourceStatus
    publication_date: Optional[str] = None
    original_artifact_path: Optional[str] = None
    sha256_checksum: Optional[str] = None
    document_version: Optional[str] = None
    access_notes: str = ""
    verification_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialises to JSON-compatible dictionary."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "issuing_authority": self.issuing_authority,
            "canonical_url": self.canonical_url,
            "source_type": self.source_type,
            "academic_year": self.academic_year,
            "retrieval_timestamp": self.retrieval_timestamp,
            "source_status": self.source_status.value,
            "publication_date": self.publication_date,
            "original_artifact_path": self.original_artifact_path,
            "sha256_checksum": self.sha256_checksum,
            "document_version": self.document_version,
            "access_notes": self.access_notes,
            "verification_notes": self.verification_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceDocument":
        """Instantiates from dictionary representation."""
        status_raw = data.get("source_status", "unverified")
        return cls(
            source_id=data["source_id"],
            title=data["title"],
            issuing_authority=data["issuing_authority"],
            canonical_url=data["canonical_url"],
            source_type=data["source_type"],
            academic_year=int(data["academic_year"]),
            retrieval_timestamp=data["retrieval_timestamp"],
            source_status=SourceStatus(status_raw),
            publication_date=data.get("publication_date"),
            original_artifact_path=data.get("original_artifact_path"),
            sha256_checksum=data.get("sha256_checksum"),
            document_version=data.get("document_version"),
            access_notes=data.get("access_notes", ""),
            verification_notes=data.get("verification_notes", ""),
        )


@dataclass(frozen=True)
class DatasetSnapshot:
    """Immutable record of an ingestion run and its resulting dataset partition."""

    snapshot_id: str
    dataset_id: str
    snapshot_version: str
    academic_year: int
    source_document_ids: List[str]
    importer_version: str
    source_artifact_checksum: str
    created_at: str  # UTC ISO 8601
    records_processed: int
    records_accepted: int
    records_quarantined: int
    records_duplicate: int = 0
    validation_status: ValidationStatus = ValidationStatus.VALID
    quarantine_file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialises to JSON-compatible dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "dataset_id": self.dataset_id,
            "snapshot_version": self.snapshot_version,
            "academic_year": self.academic_year,
            "source_document_ids": list(self.source_document_ids),
            "importer_version": self.importer_version,
            "source_artifact_checksum": self.source_artifact_checksum,
            "created_at": self.created_at,
            "records_processed": self.records_processed,
            "records_accepted": self.records_accepted,
            "records_quarantined": self.records_quarantined,
            "records_duplicate": self.records_duplicate,
            "validation_status": self.validation_status.value,
            "quarantine_file_path": self.quarantine_file_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetSnapshot":
        """Instantiates from dictionary representation."""
        val_status_raw = data.get("validation_status", "valid")
        return cls(
            snapshot_id=data["snapshot_id"],
            dataset_id=data["dataset_id"],
            snapshot_version=data["snapshot_version"],
            academic_year=int(data["academic_year"]),
            source_document_ids=list(data["source_document_ids"]),
            importer_version=data["importer_version"],
            source_artifact_checksum=data["source_artifact_checksum"],
            created_at=data["created_at"],
            records_processed=int(data["records_processed"]),
            records_accepted=int(data["records_accepted"]),
            records_quarantined=int(data["records_quarantined"]),
            records_duplicate=int(data.get("records_duplicate", 0)),
            validation_status=ValidationStatus(val_status_raw),
            quarantine_file_path=data.get("quarantine_file_path"),
        )


@dataclass(frozen=True)
class RecordProvenance:
    """Row-level provenance information attached to ingested admission records."""

    source_document_id: str
    snapshot_id: str
    source_location: str  # e.g., "row_42", "section_criterion_1"
    parser_version: str
    source_record_id: Optional[str] = None
    original_labels: Dict[str, str] = field(default_factory=dict)
    normalised_values: Dict[str, Any] = field(default_factory=dict)
    validation_status: ValidationStatus = ValidationStatus.VALID
    source_status: SourceStatus = SourceStatus.OFFICIAL_SOURCE
    transformation_notes: str = ""
    is_synthetic: bool = False

    def __post_init__(self) -> None:
        """Enforces provenance invariants on record creation."""
        if self.is_synthetic and self.source_status in (
            SourceStatus.OFFICIAL_SOURCE,
            SourceStatus.DERIVED_FROM_OFFICIAL,
        ):
            raise ValueError(
                f"Provenance integrity violation: Provenance entry for '{self.source_location}' is synthetic "
                f"but claims official status '{self.source_status.value}'."
            )
        if not self.is_synthetic and self.source_status == SourceStatus.SYNTHETIC_DEMO:
            raise ValueError(
                f"Provenance integrity violation: Provenance entry for '{self.source_location}' has synthetic_demo "
                "status but is_synthetic is False."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialises to JSON-compatible dictionary."""
        return {
            "source_document_id": self.source_document_id,
            "snapshot_id": self.snapshot_id,
            "source_location": self.source_location,
            "parser_version": self.parser_version,
            "source_record_id": self.source_record_id,
            "original_labels": dict(self.original_labels),
            "normalised_values": dict(self.normalised_values),
            "validation_status": self.validation_status.value,
            "source_status": self.source_status.value,
            "transformation_notes": self.transformation_notes,
            "is_synthetic": self.is_synthetic,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecordProvenance":
        """Instantiates from dictionary representation."""
        status = SourceStatus(data.get("source_status", "official_source"))
        is_synth = bool(data.get("is_synthetic", status == SourceStatus.SYNTHETIC_DEMO))
        return cls(
            source_document_id=data["source_document_id"],
            snapshot_id=data["snapshot_id"],
            source_location=data["source_location"],
            parser_version=data["parser_version"],
            source_record_id=data.get("source_record_id"),
            original_labels=dict(data.get("original_labels", {})),
            normalised_values=dict(data.get("normalised_values", {})),
            validation_status=ValidationStatus(data.get("validation_status", "valid")),
            source_status=status,
            transformation_notes=data.get("transformation_notes", ""),
            is_synthetic=is_synth,
        )


