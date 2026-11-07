"""Pydantic schemas for Student Digital Twin responses (Phase 4)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FactRecordDto(BaseModel):
    """Auditable atomic fact record in the Student Digital Twin."""

    fact_id: str
    field_name: str
    actual_value: Any
    original_value: Any
    unit_or_scale: Optional[str] = None
    origin_category: str
    validation_status: str
    explanation: str = ""
    evidence_reference: Optional[str] = None
    input_fact_ids: List[str] = Field(default_factory=list)
    derivation_rule: Optional[str] = None


class NormalizedSubjectScoreDto(BaseModel):
    """Subject score with conservative normalization representation."""

    subject_code: str
    subject_name: str
    original_score: float
    max_score: float
    grading_scale: str
    normalized_percentage: Optional[float] = None
    conversion_status: str
    conversion_explanation: str = ""
    board: Optional[str] = None
    conversion_policy_id: Optional[str] = None
    examination_year: Optional[int] = None
    is_indicative: bool = False
    is_institution_authorized: bool = False


class AcademicIdentityDto(BaseModel):
    """Structured representation of student academic transcript and strengths."""

    subject_scores: List[NormalizedSubjectScoreDto] = Field(default_factory=list)
    score_based_academic_highlights: List[str] = Field(default_factory=list)
    academic_strengths: List[str] = Field(default_factory=list)
    highlight_threshold: float = 75.0
    highlight_heuristic_version: str = "1.0"
    missing_subjects: List[str] = Field(default_factory=list)
    unsupported_grading_scales: List[str] = Field(default_factory=list)


class EntranceExamProfileDto(BaseModel):
    """Verified entrance examination profile without speculative predictions."""

    exam_name: Optional[str] = None
    rank: Optional[int] = None
    rank_basis: Optional[str] = None
    academic_year: Optional[int] = None
    missing_details: List[str] = Field(default_factory=list)
    interpretation_notes: str = ""


class FinancialConstraintsDto(BaseModel):
    """Explicit financial constraints in INR for total education duration."""

    total_budget_inr: float = 0.0
    currency: str = "INR"
    cost_basis: str = "tuition_only_total"
    is_budget_provided: bool = False
    affordability_readiness: bool = False
    notes: str = ""


class GeographicPreferencesDto(BaseModel):
    """Explicit geographic location preferences."""

    preferred_locations: List[str] = Field(default_factory=list)
    preference_type: str = "not_provided"
    is_unconstrained: bool = True
    notes: str = ""


class InterestsAndGoalsDto(BaseModel):
    """Explicit interests and career ambitions with verified graph links."""

    preferred_disciplines: List[str] = Field(default_factory=list)
    career_goals: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    unmapped_interests: List[str] = Field(default_factory=list)


class DimensionCompletenessDto(BaseModel):
    """Detailed completeness assessment for a single profile dimension."""

    dimension_name: str
    state: str
    available_facts: List[str] = Field(default_factory=list)
    missing_facts: List[str] = Field(default_factory=list)
    invalid_facts: List[str] = Field(default_factory=list)
    review_facts: List[str] = Field(default_factory=list)
    explanation: str = ""


class DiscoveredPathwayDto(BaseModel):
    """Discovered semantic pathway connecting preferences to academic entities."""

    source: str
    relationship: str
    target: str
    target_type: str
    source_type: str = "direct"
    provenance_path: List[str] = Field(default_factory=list)


class TwinSnapshotDto(BaseModel):
    """Structured, immutable Student Digital Twin snapshot."""

    twin_id: str
    snapshot_id: Optional[str] = None
    student_id: Optional[str] = None
    student_profile_version: str = "1.0.0"
    schema_version: str = "1.0.0"
    policy_version: str = "1.0.0"
    created_at: str
    profile_fingerprint: str
    overall_completeness: str
    completeness_dimensions: Dict[str, DimensionCompletenessDto]
    academic_identity: AcademicIdentityDto
    entrance_exam_profile: EntranceExamProfileDto
    financial_constraints: FinancialConstraintsDto
    geographic_preferences: GeographicPreferencesDto
    interests_and_goals: InterestsAndGoalsDto
    facts: Dict[str, FactRecordDto]
    semantic_network_pathways: List[Dict[str, Any]] = Field(default_factory=list)
    frame_representation: Dict[str, Any] = Field(default_factory=dict)
    missing_information: List[str] = Field(default_factory=list)
    validation_findings: List[str] = Field(default_factory=list)
    is_synthetic: bool = True


class StudentTwinResponse(BaseModel):
    """Canonical API response envelope for Student Digital Twin construction."""

    snapshot: TwinSnapshotDto
    disclaimer: str = (
        "Hydra Digital Twin representations are deterministically synthesized from student inputs "
        "and symbolic knowledge networks for decision support. No automated admissions decisions are made."
    )

