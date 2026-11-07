"""Domain models for Hydra Heist Planner (A* State-Space Planning).

Represents planning states, typed actions, admissibility metrics, and execution pathways.
"""

from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, FrozenSet, List, Optional, Sequence


class ActionCategory(str, Enum):
    """Semantic category of a candidate planning action."""

    INFORMATION_GATHERING = "information_gathering"
    DOCUMENTATION = "documentation"
    PREPARATION = "preparation"
    ELIGIBILITY_PATHWAY = "eligibility_pathway"
    PREFERENCE_CHANGE = "preference_change"
    NON_ACTIONABLE = "non_actionable"


@dataclass(frozen=True)
class PlanningAction:
    """An action that transitions the student from one planning state to another."""

    action_id: str
    title: str
    description: str
    category: ActionCategory
    preconditions: Sequence[str] = field(default_factory=tuple)
    satisfies_conditions: Sequence[str] = field(default_factory=tuple)
    cost: float = 1.0  # Non-negative action cost for A*
    cost_unit: str = "effort_points"
    duration_days: int = 0
    evidence_requirement: Optional[str] = None
    is_actionable: bool = True

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError(f"Action cost must be non-negative (got {self.cost})")
        object.__setattr__(self, "preconditions", tuple(self.preconditions))
        object.__setattr__(self, "satisfies_conditions", tuple(self.satisfies_conditions))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "preconditions": list(self.preconditions),
            "satisfies_conditions": list(self.satisfies_conditions),
            "cost": self.cost,
            "cost_unit": self.cost_unit,
            "duration_days": self.duration_days,
            "evidence_requirement": self.evidence_requirement,
            "is_actionable": self.is_actionable,
        }


@dataclass(frozen=True)
class PlanningState:
    """Immutable state representation in the planning state space."""

    satisfied_conditions: FrozenSet[str]
    violated_conditions: FrozenSet[str]
    unknown_conditions: FrozenSet[str]

    @property
    def fingerprint(self) -> str:
        """Deterministic fingerprint representing this state."""
        sat = ",".join(sorted(self.satisfied_conditions))
        viol = ",".join(sorted(self.violated_conditions))
        unk = ",".join(sorted(self.unknown_conditions))
        raw = f"SAT:[{sat}]|VIOL:[{viol}]|UNK:[{unk}]"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def is_condition_satisfied(self, condition_id: str) -> bool:
        return condition_id in self.satisfied_conditions

    def satisfies_all(self, condition_ids: Sequence[str]) -> bool:
        return all(c in self.satisfied_conditions for c in condition_ids)

    def apply_action(self, action: PlanningAction) -> "PlanningState":
        """Produces a new immutable PlanningState by applying the effects of an action."""
        new_sat = set(self.satisfied_conditions)
        new_viol = set(self.violated_conditions)
        new_unk = set(self.unknown_conditions)

        for cond in action.satisfies_conditions:
            new_sat.add(cond)
            new_viol.discard(cond)
            new_unk.discard(cond)

        return PlanningState(
            satisfied_conditions=frozenset(new_sat),
            violated_conditions=frozenset(new_viol),
            unknown_conditions=frozenset(new_unk),
        )


@dataclass(frozen=True)
class PlanningResult:
    """Outcome of an A* planning execution for a target programme."""

    plan_id: str
    twin_id: str
    snapshot_id: str
    target_programme_id: str
    target_programme_title: str
    initial_status: str
    goal_reached: bool
    actions: List[PlanningAction]
    total_cost: float
    total_duration_days: int
    nodes_expanded: int
    heuristic_used: str
    alternative_routes: List[Dict[str, Any]]
    explanation: str
    warnings: List[str]
    executed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "twin_id": self.twin_id,
            "snapshot_id": self.snapshot_id,
            "target_programme_id": self.target_programme_id,
            "target_programme_title": self.target_programme_title,
            "initial_status": self.initial_status,
            "goal_reached": self.goal_reached,
            "actions": [a.to_dict() for a in self.actions],
            "total_cost": self.total_cost,
            "total_duration_days": self.total_duration_days,
            "nodes_expanded": self.nodes_expanded,
            "heuristic_used": self.heuristic_used,
            "alternative_routes": self.alternative_routes,
            "explanation": self.explanation,
            "warnings": list(self.warnings),
            "executed_at": self.executed_at,
        }

