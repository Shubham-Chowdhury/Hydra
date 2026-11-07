"""Franchise orchestration service for Hydra.

Coordinates dynamically instantiated Franchise Agents for catalogue programmes,
evaluates student Twins, and executes simulated programme auctions.
"""

from typing import Any, Dict, List, Optional

from app.agents.franchise_agent import FranchiseAgentFactory
from app.domain.franchise import AuctionResult, ProgrammeBid, ScoringPolicy
from app.domain.twin import TwinSnapshot
from app.services.auction_service import AuctionService
from app.services.programme_service import ProgrammeService
from app.services.twin_service import TwinService


class FranchiseService:
    """Service orchestrating Franchise Agents and running simulated auctions."""

    def __init__(
        self,
        programme_service: Optional[ProgrammeService] = None,
        twin_service: Optional[TwinService] = None,
        auction_service: Optional[AuctionService] = None,
    ) -> None:
        self.programme_service = programme_service or ProgrammeService()
        self.twin_service = twin_service or TwinService()
        self.auction_service = auction_service or AuctionService()

    def evaluate_and_run_auction(
        self,
        twin_snapshot: TwinSnapshot,
        programme_ids: Optional[List[str]] = None,
        scoring_policy: Optional[ScoringPolicy] = None,
    ) -> AuctionResult:
        """Instantiates Franchise Agents for catalogue programmes, gathers bids, and executes auction."""
        all_programmes = self.programme_service.get_all()
        if programme_ids:
            requested = set(programme_ids)
            programmes = [p for p in all_programmes if p.programme_id in requested]
            if not programmes:
                raise ValueError(
                    f"None of the requested programme_ids were found in catalogue: {programme_ids}"
                )
        else:
            programmes = all_programmes

        bids: List[ProgrammeBid] = []
        for prog in programmes:
            agent = FranchiseAgentFactory.create_for_programme(
                programme=prog,
                frame_registry=self.programme_service.frame_registry,
                scoring_policy=scoring_policy,
            )
            bid = agent.evaluate(twin_snapshot)
            bids.append(bid)

        return self.auction_service.run_auction(bids, scoring_policy=scoring_policy)

    def get_available_franchises(self) -> List[Dict[str, Any]]:
        """Returns metadata for all available programme franchise agents."""
        programmes = self.programme_service.get_all()
        return [
            {
                "programme_id": p.programme_id,
                "title": p.title,
                "institution_name": p.institution_name,
                "location": p.location,
                "discipline": p.discipline,
                "agent_id": f"AGENT_FRANCHISE_{p.programme_id}",
                "is_synthetic": getattr(p, "is_synthetic", True),
                "dataset_label": getattr(
                    p, "dataset_label", "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"
                ),
            }
            for p in programmes
        ]

