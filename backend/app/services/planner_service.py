"""Heist Planner application service for Hydra.

Coordinates student Twin retrieval, programme resolution, and A* state-space planning.
"""

from typing import Optional

from app.agents.heist_planner import HeistPlannerAgent
from app.domain.planner import PlanningResult
from app.domain.twin import TwinSnapshot
from app.services.programme_service import ProgrammeService
from app.services.twin_service import TwinService


class PlannerService:
    """Service orchestrating A* search planning for academic programme admission."""

    def __init__(
        self,
        programme_service: Optional[ProgrammeService] = None,
        twin_service: Optional[TwinService] = None,
        planner_agent: Optional[HeistPlannerAgent] = None,
    ) -> None:
        self.programme_service = programme_service or ProgrammeService()
        self.twin_service = twin_service or TwinService()
        self.planner_agent = planner_agent or HeistPlannerAgent(
            programme_service=self.programme_service
        )

    def generate_plan(
        self,
        twin_snapshot: TwinSnapshot,
        programme_id: str,
        use_heuristic: bool = True,
    ) -> PlanningResult:
        """Executes A* search to discover requirement satisfaction pathways."""
        return self.planner_agent.plan_pathway(
            twin_snapshot=twin_snapshot,
            programme_id=programme_id,
            use_heuristic=use_heuristic,
        )

