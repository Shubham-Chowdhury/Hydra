"""Admissions Knowledge Base Domain Models for Hydra (Phase 3).

Models authoritative institution profiles, academic programmes, historical cutoff
observations, seat matrix allocations, and verified formal eligibility criteria.

CRITICAL DISTINCTION:
Historical cutoff observations represent observed allocation boundaries from past
counselling cycles. They are NOT universal eligibility rules, guaranteed minimums,
or predictors of future admission.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.domain.provenance import RecordProvenance, SourceStatus, ValidationStatus


HISTORICAL_CUTOFF_DISCLAIMER = (
    "Historical cutoff observations describe past counselling outcomes. "
    "They do not guarantee future admission."
)


@dataclass(frozen=True)
class Institution:
    """Authoritative representation of a higher-education institution."""

    institution_id: str
    official_name: str
    institution_type: Optional[str] = None  # e.g., "IIT", "NIT", "IIIT", "GFTI"
    location: Optional[str] = None
    source_references: List[str] = field(default_factory=list)
    provenance: SourceStatus = SourceStatus.OFFICIAL_SOURCE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "institution_id": self.institution_id,
            "official_name": self.official_name,
            "institution_type": self.institution_type,
            "location": self.location,
            "source_references": list(self.source_references),
            "provenance": self.provenance.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Institution":
        return cls(
            institution_id=data["institution_id"],
            official_name=data["official_name"],
            institution_type=data.get("institution_type"),
            location=data.get("location"),
            source_references=list(data.get("source_references", [])),
            provenance=SourceStatus(data.get("provenance", "official_source")),
        )


@dataclass(frozen=True)
class AcademicProgrammeRecord:
    """Official academic programme offering by an institution."""

    programme_id: str
    institution_id: str
    official_title: str
    academic_year: int
    degree_type: Optional[str] = None  # e.g., "B.Tech.", "B.S.", "Dual Degree"
    discipline: Optional[str] = None
    duration_years: Optional[int] = 4
    source_references: List[str] = field(default_factory=list)
    provenance: SourceStatus = SourceStatus.OFFICIAL_SOURCE
    is_synthetic: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "programme_id": self.programme_id,
            "institution_id": self.institution_id,
            "official_title": self.official_title,
            "academic_year": self.academic_year,
            "degree_type": self.degree_type,
            "discipline": self.discipline,
            "duration_years": self.duration_years,
            "source_references": list(self.source_references),
            "provenance": self.provenance.value,
            "is_synthetic": self.is_synthetic,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AcademicProgrammeRecord":
        prov = SourceStatus(data.get("provenance", "official_source"))
        return cls(
            programme_id=data["programme_id"],
            institution_id=data["institution_id"],
            official_title=data["official_title"],
            academic_year=int(data["academic_year"]),
            degree_type=data.get("degree_type"),
            discipline=data.get("discipline"),
            duration_years=data.get("duration_years", 4),
            source_references=list(data.get("source_references", [])),
            provenance=prov,
            is_synthetic=bool(data.get("is_synthetic", prov == SourceStatus.SYNTHETIC_DEMO)),
        )


@dataclass(frozen=True)
class AdmissionCutoffObservation:
    """Historical cutoff observation from an official counselling allocation round.

    This record represents an observed past event, NEVER a deterministic eligibility rule.
    """

    observation_id: str
    institution_id: str
    programme_id: str
    institution_name: str
    programme_title: str
    academic_year: int
    counselling_round: int
    exam_name: str  # "JEE Advanced" or "JEE Main"
    quota: str  # "AI", "HS", "OS"
    seat_type: str  # "OPEN", "GEN-EWS", "OBC-NCL", "SC", "ST", "OPEN (PwD)", etc.
    gender_pool: str  # "Gender-Neutral", "Female-only (including Supernumerary)"
    opening_rank: int
    closing_rank: int
    rank_basis: str  # "CRL", "CATEGORY_RANK", "PREPARATORY"
    source_document_id: str
    snapshot_id: str
    source_row_provenance: str
    validation_status: ValidationStatus = ValidationStatus.VALID
    source_status: SourceStatus = SourceStatus.OFFICIAL_SOURCE
    is_synthetic: bool = False
    disclaimer: str = HISTORICAL_CUTOFF_DISCLAIMER

    def __post_init__(self) -> None:
        """Enforces domain and provenance invariants on cutoff observations."""
        if self.is_synthetic and self.source_status in (
            SourceStatus.OFFICIAL_SOURCE,
            SourceStatus.DERIVED_FROM_OFFICIAL,
        ):
            raise ValueError(
                f"Provenance integrity violation: Cutoff observation {self.observation_id} is marked synthetic "
                f"but claims official status '{self.source_status.value}'."
            )
        if not self.is_synthetic and self.source_status == SourceStatus.SYNTHETIC_DEMO:
            raise ValueError(
                f"Provenance integrity violation: Cutoff observation {self.observation_id} has synthetic_demo "
                "status but is_synthetic is False."
            )
        if not self.source_row_provenance or not self.source_row_provenance.strip():
            raise ValueError(
                f"Provenance integrity violation: Cutoff observation {self.observation_id} missing source_row_provenance."
            )
        if not self.source_document_id or not self.source_document_id.strip():
            raise ValueError(
                f"Provenance integrity violation: Cutoff observation {self.observation_id} missing source_document_id."
            )
        if not self.snapshot_id or not self.snapshot_id.strip():
            raise ValueError(
                f"Provenance integrity violation: Cutoff observation {self.observation_id} missing snapshot_id."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "institution_id": self.institution_id,
            "programme_id": self.programme_id,
            "institution_name": self.institution_name,
            "programme_title": self.programme_title,
            "academic_year": self.academic_year,
            "counselling_round": self.counselling_round,
            "exam_name": self.exam_name,
            "quota": self.quota,
            "seat_type": self.seat_type,
            "gender_pool": self.gender_pool,
            "opening_rank": self.opening_rank,
            "closing_rank": self.closing_rank,
            "rank_basis": self.rank_basis,
            "source_document_id": self.source_document_id,
            "snapshot_id": self.snapshot_id,
            "source_row_provenance": self.source_row_provenance,
            "validation_status": self.validation_status.value,
            "source_status": self.source_status.value,
            "is_synthetic": self.is_synthetic,
            "disclaimer": self.disclaimer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdmissionCutoffObservation":
        status = SourceStatus(data.get("source_status", "official_source"))
        is_synth = bool(data.get("is_synthetic", status == SourceStatus.SYNTHETIC_DEMO))
        return cls(
            observation_id=data["observation_id"],
            institution_id=data["institution_id"],
            programme_id=data["programme_id"],
            institution_name=data["institution_name"],
            programme_title=data["programme_title"],
            academic_year=int(data["academic_year"]),
            counselling_round=int(data["counselling_round"]),
            exam_name=data["exam_name"],
            quota=data["quota"],
            seat_type=data["seat_type"],
            gender_pool=data["gender_pool"],
            opening_rank=int(data["opening_rank"]),
            closing_rank=int(data["closing_rank"]),
            rank_basis=data["rank_basis"],
            source_document_id=data["source_document_id"],
            snapshot_id=data["snapshot_id"],
            source_row_provenance=data["source_row_provenance"],
            validation_status=ValidationStatus(data.get("validation_status", "valid")),
            source_status=status,
            is_synthetic=is_synth,
            disclaimer=data.get("disclaimer", HISTORICAL_CUTOFF_DISCLAIMER),
        )


@dataclass(frozen=True)
class SeatMatrixObservation:
    """Historical seat matrix allocation observation."""

    observation_id: str
    institution_id: str
    programme_id: str
    academic_year: int
    seat_category: str
    seat_pool: str
    capacity: int
    source_document_id: str
    snapshot_id: str
    source_row_provenance: str
    validation_status: ValidationStatus = ValidationStatus.VALID
    source_status: SourceStatus = SourceStatus.OFFICIAL_SOURCE
    is_synthetic: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "institution_id": self.institution_id,
            "programme_id": self.programme_id,
            "academic_year": self.academic_year,
            "seat_category": self.seat_category,
            "seat_pool": self.seat_pool,
            "capacity": self.capacity,
            "source_document_id": self.source_document_id,
            "snapshot_id": self.snapshot_id,
            "source_row_provenance": self.source_row_provenance,
            "validation_status": self.validation_status.value,
            "source_status": self.source_status.value,
            "is_synthetic": self.is_synthetic,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeatMatrixObservation":
        return cls(
            observation_id=data["observation_id"],
            institution_id=data["institution_id"],
            programme_id=data["programme_id"],
            academic_year=int(data["academic_year"]),
            seat_category=data["seat_category"],
            seat_pool=data["seat_pool"],
            capacity=int(data["capacity"]),
            source_document_id=data["source_document_id"],
            snapshot_id=data["snapshot_id"],
            source_row_provenance=data["source_row_provenance"],
            validation_status=ValidationStatus(data.get("validation_status", "valid")),
            source_status=SourceStatus(data.get("source_status", "official_source")),
            is_synthetic=bool(data.get("is_synthetic", False)),
        )


@dataclass(frozen=True)
class FormalEligibilityCriterion:
    """Verified formal eligibility rule published by an authoritative examination body."""

    criterion_id: str
    authority: str  # e.g., "JEE (Advanced) Office"
    academic_year: int
    criterion_number: str  # e.g., "Criterion 1", "Criterion 2"
    title: str
    description: str
    source_document_id: str
    source_status: SourceStatus = SourceStatus.OFFICIAL_SOURCE
    is_mandatory: bool = True
    criterion_scope: str = "exam_appearance_eligibility"  # e.g., "exam_appearance_eligibility", "programme_admission_eligibility"
    target_examination: Optional[str] = "JEE (Advanced)"

    def __post_init__(self) -> None:
        if not self.criterion_scope or not self.criterion_scope.strip():
            raise ValueError(
                f"FormalEligibilityCriterion '{self.criterion_id}' must specify an explicit criterion_scope."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "authority": self.authority,
            "academic_year": self.academic_year,
            "criterion_number": self.criterion_number,
            "title": self.title,
            "description": self.description,
            "source_document_id": self.source_document_id,
            "source_status": self.source_status.value,
            "is_mandatory": self.is_mandatory,
            "criterion_scope": self.criterion_scope,
            "target_examination": self.target_examination,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormalEligibilityCriterion":
        return cls(
            criterion_id=data["criterion_id"],
            authority=data["authority"],
            academic_year=int(data["academic_year"]),
            criterion_number=data["criterion_number"],
            title=data["title"],
            description=data["description"],
            source_document_id=data["source_document_id"],
            source_status=SourceStatus(data.get("source_status", "official_source")),
            is_mandatory=bool(data.get("is_mandatory", True)),
            criterion_scope=data.get("criterion_scope", "exam_appearance_eligibility"),
            target_examination=data.get("target_examination", "JEE (Advanced)"),
        )

