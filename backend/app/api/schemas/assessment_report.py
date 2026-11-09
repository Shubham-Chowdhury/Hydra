"""Pydantic Transport DTOs for Comprehensive Assessment & Career Pathway Reports."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.api.schemas.student import StudentProfileRequest


class UserInteractionEventDto(BaseModel):
    """Event representing student exploration activity."""

    event_id: str
    event_type: str
    timestamp: str
    target_id: Optional[str] = None
    domain: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssessmentReportRequest(BaseModel):
    """Payload to trigger comprehensive assessment and trajectory generation."""

    profile: StudentProfileRequest
    interaction_history: Optional[List[UserInteractionEventDto]] = None


class NeuralTrajectoryInsightsDto(BaseModel):
    """Probabilistic output from the deep sequence neural model."""

    career_readiness_score: float
    domain_affinity_weights: Dict[str, float]
    learning_velocity_index: float
    risk_assessment_index: float
    projected_career_outcomes: List[str]
    model_architecture: str
    confidence: float
    is_estimate: bool
    provenance: str
    is_synthetic: bool


class ComprehensiveAssessmentReportDto(BaseModel):
    """Complete consolidated report for presentation and audible speech."""

    report_id: str
    student_id: str
    generated_at: str
    executive_summary: str
    voice_script: str
    academic_standing: Dict[str, Any]
    verified_eligibility_breakdown: Dict[str, int]
    top_recommended_pathways: List[Dict[str, Any]]
    neural_insights: NeuralTrajectoryInsightsDto
    actionable_milestones: List[Dict[str, Any]]
    is_synthetic: bool
    dataset_label: str
    provenance: str

