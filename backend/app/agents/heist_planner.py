"""Heist Planner Agent for Hydra (State-Space A* Search).

Discovers cost-optimal and feasible sequences of student actions to satisfy
academic programme requirements using admissible heuristics and nested AST goal predicates.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import heapq
import math
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from app.domain.frames import (
    AcademicPrerequisite,
    EligibilityStatus,
    EntrancePrerequisite,
    ProgrammeFrame,
)
from app.domain.planner import (
    ActionCategory,
    PlanningAction,
    PlanningResult,
    PlanningState,
)
from app.domain.twin import TwinSnapshot
from app.services.programme_service import ProgrammeService


@dataclass(order=True)
class SearchNode:
    """Internal search node for A* Priority Queue."""

    f_cost: float
    h_cost: float
    counter: int
    state: PlanningState = field(compare=False)
    g_cost: float = field(compare=False)
    action: Optional[PlanningAction] = field(default=None, compare=False)
    parent: Optional["SearchNode"] = field(default=None, compare=False)
    depth: int = field(default=0, compare=False)


class HeistPlannerAgent:
    """Intelligent agent executing A* search to discover requirement satisfaction pathways."""

    def __init__(
        self,
        programme_service: Optional[ProgrammeService] = None,
        max_expanded_states: int = 1000,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.programme_service = programme_service or ProgrammeService()
        self.max_expanded_states = max_expanded_states
        self.timeout_seconds = timeout_seconds

    def plan_pathway(
        self,
        twin_snapshot: TwinSnapshot,
        programme_id: str,
        use_heuristic: bool = True,
    ) -> PlanningResult:
        """Finds a feasible, cost-optimal sequence of actions from current student state to target programme."""
        programme = self.programme_service.get_by_id(programme_id)
        if not programme:
            raise ValueError(f"Target programme '{programme_id}' not found in catalogue.")

        start_time = time.time()
        now_utc = datetime.now(timezone.utc).isoformat()
        plan_id = f"PLAN_{programme_id}_{uuid.uuid4().hex[:8]}"

        # 1. Problem formulation: Extract target requirements and available actions
        target_conditions, candidate_actions, or_branches = self._formulate_problem(
            twin_snapshot, programme
        )

        # 2. Formulate Initial Planning State
        initial_state, initial_status = self._build_initial_state(
            twin_snapshot, programme, target_conditions
        )

        # 3. Check if already satisfied at start
        if self._is_goal_reached(initial_state, target_conditions, or_branches):
            return PlanningResult(
                plan_id=plan_id,
                twin_id=twin_snapshot.twin_id,
                snapshot_id=twin_snapshot.snapshot_id,
                target_programme_id=programme.programme_id,
                target_programme_title=programme.title,
                initial_status="eligible",
                goal_reached=True,
                actions=[],
                total_cost=0.0,
                total_duration_days=0,
                nodes_expanded=0,
                heuristic_used="none (already eligible)",
                alternative_routes=[],
                explanation="Student already satisfies all mandatory requirements for this programme.",
                warnings=[],
                executed_at=now_utc,
            )

        # 4. A* Search Execution
        open_set: List[SearchNode] = []
        closed_set: Set[str] = set()
        node_counter = 0

        # Initial heuristic
        h0 = (
            self._admissible_heuristic(initial_state, target_conditions, or_branches, candidate_actions)
            if use_heuristic
            else 0.0
        )
        initial_node = SearchNode(
            f_cost=h0,
            h_cost=h0,
            counter=node_counter,
            state=initial_state,
            g_cost=0.0,
            action=None,
            parent=None,
            depth=0,
        )
        heapq.heappush(open_set, initial_node)

        nodes_expanded = 0
        best_goal_node: Optional[SearchNode] = None
        warnings: List[str] = []

        while open_set:
            if time.time() - start_time > self.timeout_seconds:
                warnings.append(
                    f"A* search timed out after {self.timeout_seconds}s; returned best partial progress."
                )
                break

            if nodes_expanded >= self.max_expanded_states:
                warnings.append(
                    f"Search limit reached ({self.max_expanded_states} nodes expanded); terminating search."
                )
                break

            current_node = heapq.heappop(open_set)
            current_state = current_node.state

            if current_state.fingerprint in closed_set:
                continue

            closed_set.add(current_state.fingerprint)
            nodes_expanded += 1

            # Goal Test
            if self._is_goal_reached(current_state, target_conditions, or_branches):
                best_goal_node = current_node
                break

            # Action Expansion
            for action in candidate_actions:
                if not action.is_actionable:
                    continue

                # Check preconditions
                if not current_state.satisfies_all(action.preconditions):
                    continue

                # Avoid applying action if it provides no new conditions
                new_conditions = [
                    c for c in action.satisfies_conditions if c not in current_state.satisfied_conditions
                ]
                if not new_conditions:
                    continue

                next_state = current_state.apply_action(action)

                if next_state.fingerprint in closed_set:
                    continue

                next_g = current_node.g_cost + action.cost
                next_h = (
                    self._admissible_heuristic(
                        next_state, target_conditions, or_branches, candidate_actions
                    )
                    if use_heuristic
                    else 0.0
                )
                next_f = round(next_g + next_h, 4)

                node_counter += 1
                child_node = SearchNode(
                    f_cost=next_f,
                    h_cost=next_h,
                    counter=node_counter,
                    state=next_state,
                    g_cost=next_g,
                    action=action,
                    parent=current_node,
                    depth=current_node.depth + 1,
                )
                heapq.heappush(open_set, child_node)

        # 5. Path Reconstruction
        if best_goal_node:
            actions_path, total_duration = self._reconstruct_path(best_goal_node)
            total_cost = best_goal_node.g_cost
            goal_reached = True
            explanation = (
                f"A* found an optimal pathway with {len(actions_path)} action(s) "
                f"(total cost: {total_cost:.1f} effort points, duration: ~{total_duration} days)."
            )
        else:
            actions_path = []
            total_cost = 0.0
            total_duration = 0
            goal_reached = False
            explanation = (
                "No feasible pathway found: requirements contain immutable violations or "
                "unsatisfiable prerequisites."
            )
            if not warnings:
                warnings.append(
                    "Goal unreachable within available action set. Immutable historical facts cannot be altered."
                )

        # Alternative routes information
        alternative_routes = []
        if or_branches:
            for branch_name, branch_reqs in or_branches.items():
                satisfied = [r for r in branch_reqs if r in initial_state.satisfied_conditions]
                alternative_routes.append(
                    {
                        "pathway_name": branch_name,
                        "required_conditions": list(branch_reqs),
                        "currently_satisfied": satisfied,
                        "readiness_ratio": len(satisfied) / max(1, len(branch_reqs)),
                    }
                )

        return PlanningResult(
            plan_id=plan_id,
            twin_id=twin_snapshot.twin_id,
            snapshot_id=twin_snapshot.snapshot_id,
            target_programme_id=programme.programme_id,
            target_programme_title=programme.title,
            initial_status=initial_status,
            goal_reached=goal_reached,
            actions=actions_path,
            total_cost=total_cost,
            total_duration_days=total_duration,
            nodes_expanded=nodes_expanded,
            heuristic_used="Admissible h_max Lower Bound" if use_heuristic else "Dijkstra (h=0)",
            alternative_routes=alternative_routes,
            explanation=explanation,
            warnings=warnings,
            executed_at=now_utc,
        )

    def _formulate_problem(
        self, twin_snapshot: TwinSnapshot, programme: ProgrammeFrame
    ) -> Tuple[Set[str], List[PlanningAction], Dict[str, Set[str]]]:
        """Extracts target conditions, candidate actions, and OR-branches from programme requirements."""
        target_conditions: Set[str] = set()
        actions: List[PlanningAction] = []
        or_branches: Dict[str, Set[str]] = {}

        student = twin_snapshot.student_frame

        # 1. Academic Subject Prerequisites
        for prereq in programme.academic_prerequisites:
            cond_id = f"REQ_SUBJ_{prereq.subject_code}"
            target_conditions.add(cond_id)

            sub_score = student.get_subject_score(prereq.subject_code)
            if sub_score is None:
                # Missing fact -> actionable information gathering
                actions.append(
                    PlanningAction(
                        action_id=f"ACT_GATHER_{prereq.subject_code}",
                        title=f"Provide {prereq.subject_name} ({prereq.subject_code}) Transcript",
                        description=f"Submit verified academic marksheet demonstrating score >= {prereq.min_score}%.",
                        category=ActionCategory.INFORMATION_GATHERING,
                        cost=1.5,
                        duration_days=2,
                        satisfies_conditions=[cond_id],
                        evidence_requirement=f"Class XII Marksheet with {prereq.subject_code}",
                        is_actionable=True,
                    )
                )
            elif sub_score.normalized_percentage is not None and sub_score.normalized_percentage < prereq.min_score:
                # Immutable historical violation
                actions.append(
                    PlanningAction(
                        action_id=f"ACT_IMMUTABLE_SCORE_{prereq.subject_code}",
                        title=f"Retroactive Marksheet Revision for {prereq.subject_code}",
                        description=f"Class XII {prereq.subject_code} score is {sub_score.normalized_percentage}% (< {prereq.min_score}% required). Retrospective modification is impossible.",
                        category=ActionCategory.NON_ACTIONABLE,
                        cost=999.0,
                        is_actionable=False,
                    )
                )

        # 2. Entrance Examination Prerequisites
        for entrance in programme.entrance_prerequisites:
            if entrance.is_mandatory:
                cond_id = f"REQ_ENTRANCE_{entrance.exam_name.replace(' ', '_').upper()}"
                target_conditions.add(cond_id)

                if not student.entrance_exam_name or student.entrance_exam_name != entrance.exam_name:
                    # Missing entrance exam -> preparation action
                    actions.append(
                        PlanningAction(
                            action_id=f"ACT_APPEAR_{entrance.exam_name.replace(' ', '_').upper()}",
                            title=f"Register & Appear for {entrance.exam_name}",
                            description=f"Complete registration and appear for {entrance.exam_name} achieving rank <= {entrance.max_rank or 'qualifying'}.",
                            category=ActionCategory.PREPARATION,
                            cost=8.0,
                            duration_days=45,
                            satisfies_conditions=[cond_id],
                            evidence_requirement=f"{entrance.exam_name} Official Scorecard",
                            is_actionable=True,
                        )
                    )
                elif entrance.max_rank and student.entrance_rank and student.entrance_rank > entrance.max_rank:
                    # Rank worse than required
                    actions.append(
                        PlanningAction(
                            action_id=f"ACT_REATTEMPT_{entrance.exam_name.replace(' ', '_').upper()}",
                            title=f"Reattempt {entrance.exam_name} in Subsequent Session",
                            description=f"Current rank {student.entrance_rank} exceeds maximum {entrance.max_rank}. Prepare for next examination cycle.",
                            category=ActionCategory.PREPARATION,
                            cost=12.0,
                            duration_days=90,
                            satisfies_conditions=[cond_id],
                            evidence_requirement=f"Improved {entrance.exam_name} Scorecard",
                            is_actionable=True,
                        )
                    )

        # 3. Certification Prerequisites
        for cert in getattr(programme, "certification_prerequisites", []):
            cond_id = f"REQ_CERT_{cert.certification_name.replace(' ', '_').upper()}"
            target_conditions.add(cond_id)

            if cert.certification_name not in student.certifications:
                actions.append(
                    PlanningAction(
                        action_id=f"ACT_EARN_CERT_{cert.certification_name.replace(' ', '_').upper()}",
                        title=f"Earn {cert.certification_name} Certification",
                        description=f"Complete training and credential verification for {cert.certification_name}.",
                        category=ActionCategory.DOCUMENTATION,
                        cost=4.0,
                        duration_days=21,
                        satisfies_conditions=[cond_id],
                        evidence_requirement=f"Certificate of Completion for {cert.certification_name}",
                        is_actionable=True,
                    )
                )

        # 4. Alternative Pathway Detection (e.g., Biotechnology developer pathway)
        if "biotechnology" in programme.discipline.lower() or "bio" in programme.programme_id.lower():
            # Alternative: Branch A (Biology) OR Branch B (Programming/Math)
            cond_bio = "REQ_PATH_BIOLOGY"
            cond_tech = "REQ_PATH_TECH"
            or_branches["Biological Science Track"] = {cond_bio}
            or_branches["Computational Track"] = {cond_tech}

            actions.append(
                PlanningAction(
                    action_id="ACT_PATH_BIO",
                    title="Elect Biological Sciences Qualification Track",
                    description="Satisfy programme requirements via Class XII Biology/Life Sciences credentials.",
                    category=ActionCategory.ELIGIBILITY_PATHWAY,
                    cost=2.0,
                    duration_days=3,
                    satisfies_conditions=[cond_bio],
                    is_actionable=True,
                )
            )
            actions.append(
                PlanningAction(
                    action_id="ACT_PATH_TECH",
                    title="Elect Computational Biology Track",
                    description="Satisfy programme requirements via Mathematics + Programming credentials.",
                    category=ActionCategory.ELIGIBILITY_PATHWAY,
                    cost=2.0,
                    duration_days=3,
                    satisfies_conditions=[cond_tech],
                    is_actionable=True,
                )
            )

        return target_conditions, actions, or_branches

    def _build_initial_state(
        self,
        twin_snapshot: TwinSnapshot,
        programme: ProgrammeFrame,
        target_conditions: Set[str],
    ) -> Tuple[PlanningState, str]:
        """Evaluates student's current facts to produce initial PlanningState."""
        satisfied: Set[str] = set()
        violated: Set[str] = set()
        unknown: Set[str] = set()

        student = twin_snapshot.student_frame

        # Check Academic Prerequisites
        for prereq in programme.academic_prerequisites:
            cond_id = f"REQ_SUBJ_{prereq.subject_code}"
            sub = student.get_subject_score(prereq.subject_code)
            if sub is None:
                unknown.add(cond_id)
            elif sub.normalized_percentage is not None and sub.normalized_percentage >= prereq.min_score:
                satisfied.add(cond_id)
            else:
                violated.add(cond_id)

        # Check Entrance Prerequisites
        for entrance in programme.entrance_prerequisites:
            if entrance.is_mandatory:
                cond_id = f"REQ_ENTRANCE_{entrance.exam_name.replace(' ', '_').upper()}"
                if not student.entrance_exam_name or student.entrance_exam_name != entrance.exam_name:
                    unknown.add(cond_id)
                elif entrance.max_rank and student.entrance_rank and student.entrance_rank <= entrance.max_rank:
                    satisfied.add(cond_id)
                else:
                    violated.add(cond_id)

        # Check Certification Prerequisites
        for cert in getattr(programme, "certification_prerequisites", []):
            cond_id = f"REQ_CERT_{cert.certification_name.replace(' ', '_').upper()}"
            if cert.certification_name in student.certifications:
                satisfied.add(cond_id)
            else:
                unknown.add(cond_id)

        initial_status = (
            "ineligible" if violated else "needs_review" if unknown else "eligible"
        )

        return (
            PlanningState(
                satisfied_conditions=frozenset(satisfied),
                violated_conditions=frozenset(violated),
                unknown_conditions=frozenset(unknown),
            ),
            initial_status,
        )

    def _is_goal_reached(
        self,
        state: PlanningState,
        target_conditions: Set[str],
        or_branches: Dict[str, Set[str]],
    ) -> bool:
        """Predicate checking whether all mandatory conditions or an alternative OR-branch are satisfied."""
        if or_branches:
            # Must satisfy all non-branch target conditions AND at least one OR-branch
            branch_satisfied = any(
                branch_reqs.issubset(state.satisfied_conditions)
                for branch_reqs in or_branches.values()
            )
            mandatory_non_branch = {
                c for c in target_conditions if not any(c in b for b in or_branches.values())
            }
            return branch_satisfied and mandatory_non_branch.issubset(state.satisfied_conditions)

        return target_conditions.issubset(state.satisfied_conditions)

    def _admissible_heuristic(
        self,
        state: PlanningState,
        target_conditions: Set[str],
        or_branches: Dict[str, Set[str]],
        candidate_actions: List[PlanningAction],
    ) -> float:
        """Admissible lower-bound heuristic function h(n) for A* state-space search.

        MATHEMATICAL PROOF OF ADMISSIBILITY:
        ------------------------------------
        A heuristic h(n) is admissible if and only if for all reachable states n:
            0 <= h(n) <= h*(n)
        where h*(n) represents the true minimal cumulative action cost from state n
        to a state satisfying the target goal predicate.

        1. Single Condition Lower Bound:
           Let c be any unsatisfied condition in state n (c not in state.satisfied_conditions).
           Any valid path P = (a_1, a_2, ..., a_k) that transitions from n to a goal state
           must satisfy condition c. Therefore, at least one action a_j in P must have
           c in satisfies_conditions(a_j).
           Since all action costs are non-negative (cost(a) >= 0), the total cost of path P satisfies:
               cost(P) = sum_{i=1}^k cost(a_i) >= cost(a_j) >= min_{a in A | c in effects(a)} cost(a)
           We define min_cost(c) = min_{a in A | c in effects(a)} cost(a).
           If no actionable transition produces c, min_cost(c) = infinity.

        2. Multi-Condition Lower Bound (h_max):
           Because the inequality cost(P) >= min_cost(c) holds for EVERY unsatisfied condition c,
           it strictly holds for the maximum over all unsatisfied mandatory conditions U_base:
               cost(P) >= max_{c in U_base} min_cost(c) = h_max(U_base)
           Crucially, unlike a naive sum-of-minimums (which overestimates when a single action
           satisfies multiple conditions, e.g. cost(a1) + cost(a1) = 2*cost(a1)), the maximum
           h_max(U_base) NEVER exceeds the cost of a single shared action.
           Therefore, h_max(U_base) <= h*(n) holds unconditionally.

        3. Disjunctive Goals (OR-branches / AnyOf):
           When requirement branches B_1, B_2, ..., B_m exist where satisfying ANY branch B_j
           suffices, the minimal cost to satisfy branch B_j is lower-bounded by h_max(U(B_j)),
           where U(B_j) = B_j \ state.satisfied_conditions.
           Since satisfying at least one branch is required:
               h_AnyOf = min_{j} h_max(U(B_j))
           If any branch is already satisfied, h_AnyOf = 0.0.

        4. Combined Admissible Heuristic:
           Goal satisfaction requires satisfying all mandatory base conditions AND at least
           one OR branch:
               h(n) = max( h_max(U_base), h_AnyOf )
           Because the true optimal cost must achieve both requirements, it cannot be less than
           either individual lower bound, guaranteeing:
               0 <= h(n) <= h*(n)  for all states n.
        """
        # Map each condition to the minimum cost of an action satisfying it
        min_action_costs: Dict[str, float] = {}
        for action in candidate_actions:
            if not action.is_actionable:
                continue
            for cond in action.satisfies_conditions:
                if cond not in min_action_costs or action.cost < min_action_costs[cond]:
                    min_action_costs[cond] = action.cost

        # Base mandatory conditions excluding those belonging to OR-branches
        branch_all_conditions = set().union(*or_branches.values()) if or_branches else set()
        base_mandatory = target_conditions - branch_all_conditions
        unsatisfied_base = base_mandatory - state.satisfied_conditions

        h_base = 0.0
        if unsatisfied_base:
            base_costs = [min_action_costs.get(c, float("inf")) for c in unsatisfied_base]
            h_base = max(base_costs)

        h_branches = 0.0
        if or_branches:
            branch_estimates: List[float] = []
            for branch_reqs in or_branches.values():
                unsatisfied_branch = branch_reqs - state.satisfied_conditions
                if not unsatisfied_branch:
                    branch_estimates.append(0.0)
                else:
                    b_costs = [min_action_costs.get(c, float("inf")) for c in unsatisfied_branch]
                    branch_estimates.append(max(b_costs))
            if branch_estimates:
                h_branches = min(branch_estimates)

        # Combined lower bound
        combined_h = max(h_base, h_branches)
        if math.isinf(combined_h):
            return 999999.0

        return round(combined_h, 4)

    def _reconstruct_path(
        self, goal_node: SearchNode
    ) -> Tuple[List[PlanningAction], int]:
        """Reconstructs the sequence of actions from initial state to goal node."""
        actions: List[PlanningAction] = []
        curr: Optional[SearchNode] = goal_node
        total_duration = 0

        while curr and curr.action:
            actions.append(curr.action)
            total_duration += curr.action.duration_days
            curr = curr.parent

        actions.reverse()
        return actions, total_duration

