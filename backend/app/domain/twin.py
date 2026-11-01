"""Student Digital Twin Domain Models for Hydra (Phase 4).

Pure Python dataclasses modeling the student digital twin, fact provenance,
grading scale normalization, multidimensional completeness, and immutable snapshots.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FactOriginCategory(str, Enum):
    """Origin category of a fact represented in the Student Digital Twin."""

    USER_PROVIDED = "user_provided"
    DETERMINISTICALLY_DERIVED = "deterministically_derived"
    EXTERNAL_VERIFIED = "external_verified"
    UNKNOWN = "unknown"


class FactValidationStatus(str, Enum):
    """Validation lifecycle and integrity status of a fact."""

    VALID = "valid"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"
    MISSING = "missing"


class CompletenessState(str, Enum):
    """Completeness outcome for the overall Twin and individual dimensions."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class FactRecord:
    """A single atomic, auditable fact in the Student Digital Twin with provenance."""

    fact_id: str
    field_name: str
    actual_value: Any
    original_value: Any
    unit_or_scale: Optional[str] = None
    origin_category: FactOriginCategory = FactOriginCategory.USER_PROVIDED
    validation_status: FactValidationStatus = FactValidationStatus.VALID
    explanation: str = ""
    evidence_reference: Optional[str] = None
    input_fact_ids: List[str] = field(default_factory=list)
    derivation_rule: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "field_name": self.field_name,
            "actual_value": self.actual_value,
            "original_value": self.original_value,
            "unit_or_scale": self.unit_or_scale,
            "origin_category": self.origin_category.value,
            "validation_status": self.validation_status.value,
            "explanation": self.explanation,
            "evidence_reference": self.evidence_reference,
            "input_fact_ids": list(self.input_fact_ids),
            "derivation_rule": self.derivation_rule,
        }


@dataclass(frozen=True)
class NormalizedSubjectScore:
    """A subject score with both original and conservatively normalized representations."""

    subject_code: str
    subject_name: str
    original_score: float
    max_score: float
    grading_scale: str
    normalized_percentage: Optional[float] = None
    conversion_status: FactValidationStatus = FactValidationStatus.VALID
    conversion_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_code": self.subject_code,
            "subject_name": self.subject_name,
            "original_score": self.original_score,
            "max_score": self.max_score,
            "grading_scale": self.grading_scale,
            "normalized_percentage": self.normalized_percentage,
            "conversion_status": self.conversion_status.value,
            "conversion_explanation": self.conversion_explanation,
        }


@dataclass(frozen=True)
class AcademicIdentity:
    """Structured representation of student academic transcript and strengths."""

    subject_scores: List[NormalizedSubjectScore] = field(default_factory=list)
    academic_strengths: List[str] = field(default_factory=list)
    missing_subjects: List[str] = field(default_factory=list)
    unsupported_grading_scales: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_scores": [s.to_dict() for s in self.subject_scores],
            "academic_strengths": list(self.academic_strengths),
            "missing_subjects": list(self.missing_subjects),
            "unsupported_grading_scales": list(self.unsupported_grading_scales),
        }


@dataclass(frozen=True)
class EntranceExamProfile:
    """Verified entrance examination profile without speculative predictions."""

    exam_name: Optional[str] = None
    rank: Optional[int] = None
    rank_basis: Optional[str] = None
    academic_year: Optional[int] = None
    missing_details: List[str] = field(default_factory=list)
    interpretation_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exam_name": self.exam_name,
            "rank": self.rank,
            "rank_basis": self.rank_basis,
            "academic_year": self.academic_year,
            "missing_details": list(self.missing_details),
            "interpretation_notes": self.interpretation_notes,
        }


@dataclass(frozen=True)
class FinancialConstraints:
    """Explicit financial constraints in INR for total education duration."""

    total_budget_inr: float = 0.0
    currency: str = "INR"
    cost_basis: str = "tuition_only_total"
    is_budget_provided: bool = False
    affordability_readiness: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_budget_inr": self.total_budget_inr,
            "currency": self.currency,
            "cost_basis": self.cost_basis,
            "is_budget_provided": self.is_budget_provided,
            "affordability_readiness": self.affordability_readiness,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class GeographicPreferences:
    """Explicit geographic location preferences without speculative assumptions."""

    preferred_locations: List[str] = field(default_factory=list)
    is_unconstrained: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preferred_locations": list(self.preferred_locations),
            "is_unconstrained": self.is_unconstrained,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class InterestsAndGoals:
    """Explicit interests and career ambitions with verified graph links."""

    preferred_disciplines: List[str] = field(default_factory=list)
    career_goals: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    unmapped_interests: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preferred_disciplines": list(self.preferred_disciplines),
            "career_goals": list(self.career_goals),
            "certifications": list(self.certifications),
            "unmapped_interests": list(self.unmapped_interests),
        }


@dataclass(frozen=True)
class DimensionCompleteness:
    """Detailed completeness assessment for a single profile dimension."""

    dimension_name: str
    state: CompletenessState
    available_facts: List[str] = field(default_factory=list)
    missing_facts: List[str] = field(default_factory=list)
    invalid_facts: List[str] = field(default_factory=list)
    review_facts: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension_name": self.dimension_name,
            "state": self.state.value,
            "available_facts": list(self.available_facts),
            "missing_facts": list(self.missing_facts),
            "invalid_facts": list(self.invalid_facts),
            "review_facts": list(self.review_facts),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class TwinSnapshot:
    """Immutable, versioned snapshot of a constructed Student Digital Twin."""

    twin_id: str
    student_id: Optional[str]
    student_profile_version: str
    schema_version: str
    created_at: str  # UTC ISO 8601
    profile_fingerprint: str
    overall_completeness: CompletenessState
    completeness_dimensions: Dict[str, DimensionCompleteness]
    academic_identity: AcademicIdentity
    entrance_exam_profile: EntranceExamProfile
    financial_constraints: FinancialConstraints
    geographic_preferences: GeographicPreferences
    interests_and_goals: InterestsAndGoals
    facts: Dict[str, FactRecord]
    semantic_network_pathways: List[Dict[str, Any]] = field(default_factory=list)
    frame_representation: Dict[str, Any] = field(default_factory=dict)
    missing_information: List[str] = field(default_factory=list)
    validation_findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "student_id": self.student_id,
            "student_profile_version": self.student_profile_version,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "profile_fingerprint": self.profile_fingerprint,
            "overall_completeness": self.overall_completeness.value,
            "completeness_dimensions": {
                k: v.to_dict() for k, v in self.completeness_dimensions.items()
            },
            "academic_identity": self.academic_identity.to_dict(),
            "entrance_exam_profile": self.entrance_exam_profile.to_dict(),
            "financial_constraints": self.financial_constraints.to_dict(),
            "geographic_preferences": self.geographic_preferences.to_dict(),
            "interests_and_goals": self.interests_and_goals.to_dict(),
            "facts": {k: v.to_dict() for k, v in self.facts.items()},
            "semantic_network_pathways": list(self.semantic_network_pathways),
            "frame_representation": dict(self.frame_representation),
            "missing_information": list(self.missing_information),
            "validation_findings": list(self.validation_findings),
        }

