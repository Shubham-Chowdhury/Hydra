"""Franchise Agent and Simulated Auction domain models for Hydra.

Represents academic programme agent proposals (bids), proposal statuses,
alignment scoring policies, and deterministic auction results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.domain.frames import EligibilityStatus


class ProposalStatus(str, Enum):
    """The qualification state of a programme-specific proposal (bid)."""

    UNCONDITIONAL_CANDIDATE = "unconditional_candidate"
    CONDITIONAL_CANDIDATE = "conditional_candidate"
    NO_BID = "no_bid"


@dataclass(frozen=True)
class ScoringPolicy:
    """Documented and versioned heuristic preference weighting policy for Franchise bidding.

    NOTE ON HEURISTIC NATURE:
    Weights (0.35 discipline, 0.30 career, 0.20 academic, 0.15 geographic) are versioned
    demonstration heuristics (v1.0), NOT empirical truths or university-mandated admissions cutoffs.
    When student profile dimensions are omitted, weights are dynamically renormalized across
    active dimensions to prevent silent penalties for missing optional fields.
    """

    policy_version: str = "v1.0"
    weight_discipline: float = 0.35
    weight_career: float = 0.30
    weight_academic: float = 0.20
    weight_geographic: float = 0.15

    def __post_init__(self) -> None:
        total = round(
            self.weight_discipline
            + self.weight_career
            + self.weight_academic
            + self.weight_geographic,
            4,
        )
        if total != 1.0:
            raise ValueError(
                f"ScoringPolicy weights must sum to 1.0 (got {total})"
            )


@dataclass(frozen=True)
class AlignmentScores:
    """Multi-dimensional alignment scores between student profile and programme."""

    academic_alignment: float  # [0.0, 1.0]
    discipline_alignment: float  # [0.0, 1.0]
    career_alignment: float  # [0.0, 1.0]
    geographic_alignment: float  # [0.0, 1.0]
    composite_score: Optional[float]  # [0.0, 1.0] or None when unscored
    evidence_coverage_ratio: float = 1.0  # [0.0, 1.0]
    active_dimensions: List[str] = field(default_factory=list)
    is_insufficient_evidence: bool = False
    evidence_tier: str = "comprehensive"  # "comprehensive", "partial", "exploratory", "unscored"
    is_unscored: bool = False
    neutral_baseline_display: float = 0.50


@dataclass(frozen=True)
class ProgrammeBid:
    """Immutable structured proposal submitted by a Franchise Agent for a specific student."""

    bid_id: str
    agent_id: str
    programme_id: str
    programme_title: str
    institution_name: str
    twin_id: str
    snapshot_id: str
    eligibility_status: EligibilityStatus
    affordability_status: bool
    total_budget_inr: float
    estimated_total_tuition_inr: float
    academic_alignment: float
    discipline_alignment: float
    career_alignment: float
    geographic_alignment: float
    composite_preference_score: Optional[float]  # None when unscored
    proposal_status: ProposalStatus
    policy_version: str
    evidence_references: List[str]
    missing_facts: List[str]
    warnings: List[str]
    reasoning_trace: Dict[str, Any]
    created_at: str
    evidence_coverage_ratio: float = 1.0
    active_dimensions: List[str] = field(default_factory=list)
    is_insufficient_evidence: bool = False
    evidence_tier: str = "comprehensive"
    is_unscored: bool = False
    neutral_baseline_display: float = 0.50
    currency: str = "INR"
    cost_basis: str = "tuition_only_total"
    is_synthetic: bool = True
    dataset_label: str = "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes bid to a standard dictionary representation."""
        return {
            "bid_id": self.bid_id,
            "agent_id": self.agent_id,
            "programme_id": self.programme_id,
            "programme_title": self.programme_title,
            "institution_name": self.institution_name,
            "twin_id": self.twin_id,
            "snapshot_id": self.snapshot_id,
            "eligibility_status": self.eligibility_status.value,
            "affordability_status": self.affordability_status,
            "total_budget_inr": self.total_budget_inr,
            "estimated_total_tuition_inr": self.estimated_total_tuition_inr,
            "currency": self.currency,
            "cost_basis": self.cost_basis,
            "academic_alignment": self.academic_alignment,
            "discipline_alignment": self.discipline_alignment,
            "career_alignment": self.career_alignment,
            "geographic_alignment": self.geographic_alignment,
            "composite_preference_score": self.composite_preference_score,
            "evidence_coverage_ratio": self.evidence_coverage_ratio,
            "active_dimensions": list(self.active_dimensions),
            "is_insufficient_evidence": self.is_insufficient_evidence,
            "evidence_tier": self.evidence_tier,
            "is_unscored": self.is_unscored,
            "neutral_baseline_display": self.neutral_baseline_display,
            "proposal_status": self.proposal_status.value,
            "policy_version": self.policy_version,
            "evidence_references": list(self.evidence_references),
            "missing_facts": list(self.missing_facts),
            "warnings": list(self.warnings),
            "reasoning_trace": self.reasoning_trace,
            "created_at": self.created_at,
            "is_synthetic": self.is_synthetic,
            "dataset_label": self.dataset_label,
        }


@dataclass(frozen=True)
class AuctionRankingItem:
    """Individual ranked item within an auction result."""

    rank: int
    bid: ProgrammeBid
    explanation: str
    tie_breaker_applied: Optional[str] = None
    is_positive_bid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "bid": self.bid.to_dict(),
            "explanation": self.explanation,
            "tie_breaker_applied": self.tie_breaker_applied,
            "is_positive_bid": self.is_positive_bid,
        }


@dataclass(frozen=True)
class AuctionResult:
    """Deterministic result of a simulated programme auction."""

    auction_id: str
    twin_id: str
    snapshot_id: str
    policy_version: str
    total_bids: int
    unconditional_candidates: List[AuctionRankingItem]
    conditional_candidates: List[AuctionRankingItem]
    no_bid_candidates: List[AuctionRankingItem]
    ranked_bids: List[AuctionRankingItem]
    auction_summary: str
    executed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auction_id": self.auction_id,
            "twin_id": self.twin_id,
            "snapshot_id": self.snapshot_id,
            "policy_version": self.policy_version,
            "total_bids": self.total_bids,
            "unconditional_candidates": [
                item.to_dict() for item in self.unconditional_candidates
            ],
            "conditional_candidates": [
                item.to_dict() for item in self.conditional_candidates
            ],
            "no_bid_candidates": [
                item.to_dict() for item in self.no_bid_candidates
            ],
            "ranked_bids": [item.to_dict() for item in self.ranked_bids],
            "auction_summary": self.auction_summary,
            "executed_at": self.executed_at,
        }

