"""Pydantic Transport Schemas for the Central Referee Subsystem (M007)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.api.schemas.student import StudentProfileRequest


class RefereeEvaluateRequest(BaseModel):
    """API request payload for executing multi-agent evaluation under the Central Referee."""

    profile: Optional[StudentProfileRequest] = Field(None, description="Student academic and financial profile")
    snapshot_id: Optional[str] = Field(None, description="Optional snapshot ID of previously constructed Twin")
    include_auction: bool = Field(True, description="Whether to run Franchise agent auctions")
    include_planning: bool = Field(False, description="Whether to execute A* pathway planning")
    include_stress_test: bool = Field(False, description="Whether to execute Boss-Fight stress test")
    include_oracle: bool = Field(True, description="Whether to query admissions cutoff forecasts")
    interest_narrative: Optional[str] = Field(None, description="Free-text interest statement for semantic decoding")


class ConflictRecordDto(BaseModel):
    """Transport schema for an inter-agent conflict resolved by the Referee."""

    conflict_id: str
    agents_involved: List[str]
    field_or_claim: str
    claim_a: str
    claim_b: str
    resolution_strategy: str
    resolved_value: Optional[str]
    is_resolved: bool
    explanation: str


class RefereeProgrammeDecisionDto(BaseModel):
    """Transport schema for an evaluated programme decision."""

    programme_id: str
    programme_title: str
    institution_name: str
    eligibility_status: str
    is_affordable: bool
    tuition_inr: float
    student_budget_inr: float
    preference_fit: float
    preference_evidence_coverage: float = 1.0
    active_preference_dimensions: List[str] = Field(default_factory=list)
    is_insufficient_preference_evidence: bool = False
    franchise_proposal_status: Optional[str] = None
    auction_rank: Optional[int] = None
    oracle_status: str
    oracle_forecast: Optional[Dict[str, Any]] = None
    heist_plan_discovered: bool
    heist_plan_actions: List[str]
    boss_fight_robustness: Optional[str] = None
    boss_fight_survived: int
    boss_fight_total: int
    rule_traces: List[Dict[str, Any]]
    decision_summary: str


class AgentResponseEnvelopeDto(BaseModel):
    """Transport schema for an agent execution envelope."""

    agent_name: str
    agent_version: str
    schema_version: str
    snapshot_id: str
    twin_id: str
    execution_status: str
    result: Dict[str, Any]
    evidence_references: List[str]
    assumptions: List[str]
    warnings: List[str]
    unknown_facts: List[str]
    explanation: str
    timestamp: str
    error: Optional[str] = None


class RefereeEvaluationResponse(BaseModel):
    """Master response schema returned by the Central Referee."""

    evaluation_id: str
    snapshot_id: str
    twin_id: str
    student_name: str
    programme_decisions: List[RefereeProgrammeDecisionDto]
    top_recommended_programmes: List[str]
    conflicts_detected: List[ConflictRecordDto]
    interest_decoder_result: Optional[Dict[str, Any]] = None
    agent_envelopes: List[AgentResponseEnvelopeDto]
    hierarchy_rules_applied: List[str]
    audit_timestamp: str
    disclaimer: str

