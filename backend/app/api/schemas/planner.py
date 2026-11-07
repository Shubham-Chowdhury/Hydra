"""Pydantic transport schemas for Heist Planner (A* Search)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.api.schemas.student import StudentProfileRequest


class PlanningActionDto(BaseModel):
    """Structured action within a planned requirement pathway."""

    action_id: str
    title: str
    description: str
    category: str
    preconditions: List[str]
    satisfies_conditions: List[str]
    cost: float
    cost_unit: str
    duration_days: int
    evidence_requirement: Optional[str] = None
    is_actionable: bool


class PlanningRequestDto(BaseModel):
    """Request payload for executing A* pathway planning."""

    target_programme_id: str = Field(
        ...,
        description="Target academic programme ID to plan toward.",
    )
    snapshot_id: Optional[str] = Field(
        default=None,
        description="ID of a previously constructed Twin snapshot.",
    )
    twin_id: Optional[str] = Field(
        default=None,
        description="ID of student Twin if retrieving most recent snapshot.",
    )
    profile: Optional[StudentProfileRequest] = Field(
        default=None,
        description="Student profile payload to construct Twin ad-hoc if snapshot not provided.",
    )
    use_heuristic: bool = Field(
        default=True,
        description="Whether to use admissible A* heuristic (True) or Dijkstra baseline (False).",
    )


class PlanningResultDto(BaseModel):
    """Complete structured response bundle from an A* planning execution."""

    plan_id: str
    twin_id: str
    snapshot_id: str
    target_programme_id: str
    target_programme_title: str
    initial_status: str
    goal_reached: bool
    actions: List[PlanningActionDto]
    total_cost: float
    total_duration_days: int
    nodes_expanded: int
    heuristic_used: str
    alternative_routes: List[Dict[str, Any]]
    explanation: str
    warnings: List[str]
    executed_at: str

