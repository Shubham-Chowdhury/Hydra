"""Simulated Programme Auction Service for Hydra.

Aggregates, validates, and deterministically ranks Franchise Agent proposals (bids)
for an individual student Twin context.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional

from app.domain.franchise import (
    AuctionRankingItem,
    AuctionResult,
    ProgrammeBid,
    ProposalStatus,
    ScoringPolicy,
)


class AuctionService:
    """Deterministic simulated auction coordinator comparing Franchise Agent proposals."""

    def __init__(self, default_policy: Optional[ScoringPolicy] = None) -> None:
        self.default_policy = default_policy or ScoringPolicy()

    def run_auction(
        self,
        bids: List[ProgrammeBid],
        scoring_policy: Optional[ScoringPolicy] = None,
    ) -> AuctionResult:
        """Executes a simulated auction over a set of ProgrammeBid proposals for a single student."""
        if not bids:
            raise ValueError("Cannot run auction with an empty list of programme bids.")

        policy = scoring_policy or self.default_policy

        # 1. Validate common Twin and Snapshot context
        twin_id = bids[0].twin_id
        snapshot_id = bids[0].snapshot_id

        seen_programmes = set()
        for b in bids:
            if not isinstance(b, ProgrammeBid):
                raise TypeError(f"Invalid bid item type: {type(b)}")
            if b.twin_id != twin_id:
                raise ValueError(
                    f"Conflicting twin_id detected: {b.twin_id} != {twin_id}. "
                    "Auction requires a single student Twin context."
                )
            if b.snapshot_id != snapshot_id:
                raise ValueError(
                    f"Conflicting snapshot_id detected: {b.snapshot_id} != {snapshot_id}. "
                    "Auction requires a single student Twin snapshot context."
                )
            if b.programme_id in seen_programmes:
                raise ValueError(
                    f"Duplicate bid detected for programme: {b.programme_id}."
                )
            seen_programmes.add(b.programme_id)

        # 2. Partition proposals by qualification tier
        unconditional_bids: List[ProgrammeBid] = []
        conditional_bids: List[ProgrammeBid] = []
        no_bids: List[ProgrammeBid] = []

        for b in bids:
            if b.proposal_status == ProposalStatus.UNCONDITIONAL_CANDIDATE:
                unconditional_bids.append(b)
            elif b.proposal_status == ProposalStatus.CONDITIONAL_CANDIDATE:
                conditional_bids.append(b)
            else:
                no_bids.append(b)

        # 3. Deterministic Sorting Key with explicit tie-breakers
        def candidate_sort_key(bid: ProgrammeBid) -> tuple:
            # A zero-dimensional profile is strictly UNSCORED (composite score is None).
            # It must not receive an ordinary numerical score that inflates its auction ranking.
            # Scored proposals rank ahead of unscored exploratory proposals.
            is_unscored = getattr(bid, "is_unscored", False) or bid.composite_preference_score is None
            score = -1.0 if is_unscored else round(bid.composite_preference_score, 4)
            return (
                1 if is_unscored else 0,  # 0 for scored (ranks first), 1 for unscored (ranks after)
                -score,  # Primary: higher composite score first
                0 if bid.affordability_status else 1,  # Secondary: affordable first
                -round(bid.academic_alignment or 0.0, 4),  # Tertiary: higher academic alignment first
                bid.programme_id,  # Quaternary: alphabetical programme ID
            )

        unconditional_bids.sort(key=candidate_sort_key)
        conditional_bids.sort(key=candidate_sort_key)
        no_bids.sort(key=lambda b: b.programme_id)

        # 4. Assemble ranking items with transparent explanations
        ranked_items: List[AuctionRankingItem] = []
        unconditional_items: List[AuctionRankingItem] = []
        conditional_items: List[AuctionRankingItem] = []
        no_bid_items: List[AuctionRankingItem] = []

        current_rank = 1

        # Tier 1: Unconditional Candidates
        for i, b in enumerate(unconditional_bids):
            tie_breaker = None
            if i > 0:
                prev = unconditional_bids[i - 1]
                b_score = -1.0 if (getattr(b, "is_unscored", False) or b.composite_preference_score is None) else round(b.composite_preference_score, 4)
                p_score = -1.0 if (getattr(prev, "is_unscored", False) or prev.composite_preference_score is None) else round(prev.composite_preference_score, 4)
                if b_score == p_score:
                    if b.affordability_status != prev.affordability_status:
                        tie_breaker = "Affordability Status (Affordable preferred)"
                    elif round(b.academic_alignment, 4) != round(prev.academic_alignment, 4):
                        tie_breaker = "Academic Alignment score"
                    else:
                        tie_breaker = "Alphabetical Programme ID"

            if getattr(b, "is_unscored", False) or b.composite_preference_score is None:
                expl = (
                    f"Unconditional Candidate (Rank #{current_rank}). "
                    f"Unscored: No preference or academic constraints provided (Exploratory listing). "
                    f"Affordability: {'Yes' if b.affordability_status else 'No'}."
                )
            else:
                expl = (
                    f"Unconditional Candidate (Rank #{current_rank}). "
                    f"Composite fit: {b.composite_preference_score:.2f} "
                    f"(Affordability: {'Yes' if b.affordability_status else 'No'}, "
                    f"Discipline: {b.discipline_alignment:.2f}, Career: {b.career_alignment:.2f})."
                )
            item = AuctionRankingItem(
                rank=current_rank,
                bid=b,
                explanation=expl,
                tie_breaker_applied=tie_breaker,
                is_positive_bid=True,
            )
            unconditional_items.append(item)
            ranked_items.append(item)
            current_rank += 1

        # Tier 2: Conditional Candidates (Needs Review)
        for i, b in enumerate(conditional_bids):
            tie_breaker = None
            if i > 0:
                prev = conditional_bids[i - 1]
                b_score = -1.0 if (getattr(b, "is_unscored", False) or b.composite_preference_score is None) else round(b.composite_preference_score, 4)
                p_score = -1.0 if (getattr(prev, "is_unscored", False) or prev.composite_preference_score is None) else round(prev.composite_preference_score, 4)
                if b_score == p_score:
                    if b.affordability_status != prev.affordability_status:
                        tie_breaker = "Affordability Status"
                    else:
                        tie_breaker = "Programme ID"

            missing_str = ", ".join(b.missing_facts) if b.missing_facts else "verification pending"
            if getattr(b, "is_unscored", False) or b.composite_preference_score is None:
                expl = (
                    f"Conditional Candidate (Rank #{current_rank}). "
                    f"Unscored (Exploratory listing). "
                    f"Conditional on: {missing_str}."
                )
            else:
                expl = (
                    f"Conditional Candidate (Rank #{current_rank}). "
                    f"Composite fit: {b.composite_preference_score:.2f}. "
                    f"Conditional on: {missing_str}."
                )
            item = AuctionRankingItem(
                rank=current_rank,
                bid=b,
                explanation=expl,
                tie_breaker_applied=tie_breaker,
                is_positive_bid=True,
            )
            conditional_items.append(item)
            ranked_items.append(item)
            current_rank += 1

        # Tier 3: No-Bid (Ineligible - excluded from positive ranking)
        for b in no_bids:
            reasons = "; ".join(b.warnings) if b.warnings else "Prerequisites violated"
            expl = f"No Bid (Excluded from positive ranking): {reasons}."
            item = AuctionRankingItem(
                rank=current_rank,
                bid=b,
                explanation=expl,
                tie_breaker_applied=None,
                is_positive_bid=False,
            )
            no_bid_items.append(item)
            ranked_items.append(item)
            current_rank += 1

        now_utc = datetime.now(timezone.utc).isoformat()
        auction_id = f"AUCTION_{twin_id[:12]}_{uuid.uuid4().hex[:8]}"

        summary = (
            f"Simulated Auction {auction_id}: evaluated {len(bids)} programme proposals. "
            f"{len(unconditional_items)} unconditional candidates, "
            f"{len(conditional_items)} conditional candidates, "
            f"{len(no_bid_items)} no-bid (ineligible) programmes."
        )

        return AuctionResult(
            auction_id=auction_id,
            twin_id=twin_id,
            snapshot_id=snapshot_id,
            policy_version=policy.policy_version,
            total_bids=len(bids),
            unconditional_candidates=unconditional_items,
            conditional_candidates=conditional_items,
            no_bid_candidates=no_bid_items,
            ranked_bids=ranked_items,
            auction_summary=summary,
            executed_at=now_utc,
        )

