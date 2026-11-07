"""Central Referee Domain Models for Hydra (Phase 7 / M007).

Defines agent envelopes, conflict records, decision hierarchy rules,
and consolidated multi-agent recommendation decisions.

CRITICAL ARCHITECTURAL DIRECTIVES:
1. Strict Decision Hierarchy:
   - Verified Formal Mandatory Rules
   - Verified External Evidence
   - Student-Provided Facts (explicitly labeled)
   - Deterministically Derived Facts
   - Advisory Historical Observations
   - Probabilistic Predictions with Uncertainty
   - Hypothetical Simulation Scenarios
   - Synthetic Demonstration Data
   - Unknown Facts (needs_review)
2. Non-Override Guarantee: High auction scores or predictive cutoffs MUST NEVER
   override a formal mandatory eligibility failure.
3. Snapshot Integrity: All agent outputs evaluated by the Referee must originate
   from the identical Twin snapshot ID.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentContractType(str, Enum):
    """Registered agent subsystems reporting to the Central Referee."""

    TWIN = "twin"
    FRANCHISE = "franchise"
    AUCTION = "auction"
    PLANNER = "planner"
    SIMULATOR = "simulator"
    BOSS_FIGHT = "boss_fight"
    ORACLE = "oracle"
    INTEREST_DECODER = "interest_decoder"


@dataclass(frozen=True)
class AgentResponseEnvelope:
    """Standardized, auditable envelope encapsulating an agent subsystem's output."""

    agent_name: str
    agent_version: str
    schema_version: str
    snapshot_id: str
    twin_id: str
    execution_status: str  # "SUCCESS", "FAILED", "UNAVAILABLE", "SKIPPED"
    result: Dict[str, Any]
    profile_fingerprint: str = ""
    evidence_references: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    unknown_facts: List[str] = field(default_factory=list)
    explanation: str = ""
    timestamp: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "twin_id": self.twin_id,
            "profile_fingerprint": self.profile_fingerprint,
            "execution_status": self.execution_status,
            "result": self.result,
            "evidence_references": list(self.evidence_references),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "unknown_facts": list(self.unknown_facts),
            "explanation": self.explanation,
            "timestamp": self.timestamp,
            "error": self.error,
        }


@dataclass(frozen=True)
class ConflictRecord:
    """An explicit disagreement between agents detected and resolved by the Referee."""

    conflict_id: str
    agents_involved: List[str]
    field_or_claim: str
    claim_a: str
    claim_b: str
    resolution_strategy: str
    resolved_value: Optional[str]
    is_resolved: bool
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "agents_involved": list(self.agents_involved),
            "field_or_claim": self.field_or_claim,
            "claim_a": self.claim_a,
            "claim_b": self.claim_b,
            "resolution_strategy": self.resolution_strategy,
            "resolved_value": self.resolved_value,
            "is_resolved": self.is_resolved,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class RefereeProgrammeDecision:
    """Comprehensive decision and reasoning synthesis for an academic programme candidate."""

    programme_id: str
    programme_title: str
    institution_name: str
    eligibility_status: str  # "eligible", "ineligible", "needs_review"
    is_affordable: bool
    tuition_inr: float
    student_budget_inr: float
    preference_fit: float
    franchise_proposal_status: Optional[str] = None
    auction_rank: Optional[int] = None
    oracle_status: str = "INSUFFICIENT_VERIFIED_DATA"
    oracle_forecast: Optional[Dict[str, Any]] = None
    heist_plan_discovered: bool = False
    heist_plan_actions: List[str] = field(default_factory=list)
    boss_fight_robustness: Optional[str] = None
    boss_fight_survived: int = 0
    boss_fight_total: int = 0
    rule_traces: List[Dict[str, Any]] = field(default_factory=list)
    decision_summary: str = ""
    preference_evidence_coverage: float = 1.0
    active_preference_dimensions: List[str] = field(default_factory=list)
    is_insufficient_preference_evidence: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "programme_id": self.programme_id,
            "programme_title": self.programme_title,
            "institution_name": self.institution_name,
            "eligibility_status": self.eligibility_status,
            "is_affordable": self.is_affordable,
            "tuition_inr": self.tuition_inr,
            "student_budget_inr": self.student_budget_inr,
            "preference_fit": round(self.preference_fit, 3),
            "preference_evidence_coverage": round(self.preference_evidence_coverage, 3),
            "active_preference_dimensions": list(self.active_preference_dimensions),
            "is_insufficient_preference_evidence": self.is_insufficient_preference_evidence,
            "franchise_proposal_status": self.franchise_proposal_status,
            "auction_rank": self.auction_rank,
            "oracle_status": self.oracle_status,
            "oracle_forecast": self.oracle_forecast,
            "heist_plan_discovered": self.heist_plan_discovered,
            "heist_plan_actions": list(self.heist_plan_actions),
            "boss_fight_robustness": self.boss_fight_robustness,
            "boss_fight_survived": self.boss_fight_survived,
            "boss_fight_total": self.boss_fight_total,
            "rule_traces": list(self.rule_traces),
            "decision_summary": self.decision_summary,
        }


@dataclass(frozen=True)
class RefereeEvaluationResult:
    """The master recommendation decision produced by the Central Referee."""

    evaluation_id: str
    snapshot_id: str
    twin_id: str
    student_name: str
    programme_decisions: List[RefereeProgrammeDecision]
    top_recommended_programmes: List[str]
    conflicts_detected: List[ConflictRecord]
    interest_decoder_result: Optional[Dict[str, Any]] = None
    agent_envelopes: List[AgentResponseEnvelope] = field(default_factory=list)
    hierarchy_rules_applied: List[str] = field(default_factory=list)
    audit_timestamp: str = ""
    disclaimer: str = (
        "Admissions decision-support output produced by Hydra Multi-Agent Core. "
        "Formal mandatory rules are deterministic; forecasts and simulations are advisory estimates."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "snapshot_id": self.snapshot_id,
            "twin_id": self.twin_id,
            "student_name": self.student_name,
            "programme_decisions": [p.to_dict() for p in self.programme_decisions],
            "top_recommended_programmes": list(self.top_recommended_programmes),
            "conflicts_detected": [c.to_dict() for c in self.conflicts_detected],
            "interest_decoder_result": self.interest_decoder_result,
            "agent_envelopes": [e.to_dict() for e in self.agent_envelopes],
            "hierarchy_rules_applied": list(self.hierarchy_rules_applied),
            "audit_timestamp": self.audit_timestamp,
            "disclaimer": self.disclaimer,
        }

