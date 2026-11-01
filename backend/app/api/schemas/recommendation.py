"""Pydantic schemas for recommendation and evaluation responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RuleOutcomeDto(BaseModel):
    """Auditable record of a single evaluated rule."""

    rule_id: str
    rule_name: str
    status: str
    facts_used: Dict[str, Any]
    expected_value: str
    observed_value: str
    explanation: str
    is_mandatory: bool


class ReasoningTreeNodeDto(BaseModel):
    """Hierarchical node in a structured reasoning tree for nested expressions."""

    node_id: str
    expression_type: str
    status: str
    is_mandatory: bool
    expected_value: str
    observed_value: str
    facts_used: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    missing_facts: List[str] = Field(default_factory=list)
    explanation: str = ""
    provenance: Optional[str] = None
    children: List["ReasoningTreeNodeDto"] = Field(default_factory=list)


class AffordabilityDto(BaseModel):
    """Affordability status and details."""

    is_affordable: bool
    total_budget_inr: float
    estimated_total_tuition_inr: float
    currency: str = "INR"
    cost_basis: str = "tuition_only_total"


class PreferenceFitDto(BaseModel):
    """Preference fit score and breakdown."""

    fit_score: float = Field(..., ge=0.0, le=1.0)
    criteria_breakdown: Dict[str, float]
    notes: str


class DataProvenanceDto(BaseModel):
    """Data provenance and synthetic demonstration markers."""

    is_synthetic: bool = True
    dataset_label: str = "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"
    provenance: str = "SYNTHETIC_DEMO_RECORD_V1"


class DiscoveredRelationshipDto(BaseModel):
    """Relationship triple discovered via graph traversal with provenance."""

    source: str
    relationship: str
    target: str
    target_type: str
    source_type: str = "direct"  # "direct", "inherited", "traversed"
    provenance_path: List[str] = Field(default_factory=list)


class ProgrammeEvaluationDto(BaseModel):
    """Single evaluated programme recommendation."""

    programme_id: str
    programme_title: str
    institution_name: str
    location: str
    discipline: str
    eligibility_status: str  # "eligible", "ineligible", "needs_review"
    affordability: AffordabilityDto
    preference_fit: PreferenceFitDto
    evidence: List[str]
    rules_fired: List[RuleOutcomeDto]
    reasoning_trace: str
    missing_facts: List[str]
    data_provenance: DataProvenanceDto
    discovered_relationships: List[DiscoveredRelationshipDto]
    reasoning_tree: Optional[ReasoningTreeNodeDto] = None
    parent_frame_id: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Consolidated response payload for POST /api/v1/recommendations/evaluate."""

    evaluations: List[ProgrammeEvaluationDto]
    discovered_relationships: List[DiscoveredRelationshipDto]
    is_synthetic: bool = True
    audit_timestamp: str


ReasoningTreeNodeDto.model_rebuild()
ProgrammeEvaluationDto.model_rebuild()

