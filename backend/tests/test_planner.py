"""Unit and integration test suite for Hydra Heist Planner using A* (M003).

Tests state-space problem formulation, admissible heuristic, Dijkstra fallback,
AND/OR requirement branching, immutable historical fact handling, path reconstruction,
and API endpoint contracts.
"""

import pytest
from fastapi.testclient import TestClient

from app.agents.heist_planner import HeistPlannerAgent
from app.agents.twin_agent import TwinAgent
from app.domain.frames import (
    AcademicPrerequisite,
    EntrancePrerequisite,
    ProgrammeFrame,
)
from app.domain.planner import (
    ActionCategory,
    PlanningAction,
    PlanningResult,
    PlanningState,
)
from app.main import app
from app.services.planner_service import PlannerService
from app.services.programme_service import ProgrammeService


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def cs_programme() -> ProgrammeFrame:
    return ProgrammeFrame(
        programme_id="PLAN_TEST_CS",
        title="B.Tech. in Computer Science (Synthetic)",
        institution_name="Demo Tech Institute",
        location="Bengaluru, Karnataka",
        discipline="Computer Science",
        annual_tuition_inr=150000.0,
        duration_years=4,
        estimated_total_tuition_inr=600000.0,
        academic_prerequisites=[
            AcademicPrerequisite(
                subject_code="MATH",
                subject_name="Mathematics",
                min_score=80.0,
                grading_scale="percentage",
                is_mandatory=True,
            ),
            AcademicPrerequisite(
                subject_code="PHYS",
                subject_name="Physics",
                min_score=75.0,
                grading_scale="percentage",
                is_mandatory=True,
            ),
        ],
        entrance_prerequisites=[
            EntrancePrerequisite(
                exam_name="JEE Main",
                max_rank=35000,
                is_mandatory=True,
            )
        ],
    )


@pytest.fixture
def biotech_programme() -> ProgrammeFrame:
    return ProgrammeFrame(
        programme_id="PLAN_TEST_BIO",
        title="B.Tech. in Biotechnology (Synthetic)",
        institution_name="Demo Bio Institute",
        location="Hyderabad, Telangana",
        discipline="Biotechnology",
        annual_tuition_inr=120000.0,
        duration_years=4,
        estimated_total_tuition_inr=480000.0,
        academic_prerequisites=[],
    )


def test_1_planning_state_fingerprint_and_immutability():
    """Verifies deterministic state hashing and immutability."""
    s1 = PlanningState(
        satisfied_conditions=frozenset(["REQ_MATH", "REQ_PHYS"]),
        violated_conditions=frozenset(),
        unknown_conditions=frozenset(["REQ_ENTRANCE"]),
    )
    s2 = PlanningState(
        satisfied_conditions=frozenset(["REQ_PHYS", "REQ_MATH"]),  # Order reversed
        violated_conditions=frozenset(),
        unknown_conditions=frozenset(["REQ_ENTRANCE"]),
    )
    assert s1.fingerprint == s2.fingerprint
    assert s1 == s2


def test_2_action_application_transitions_state():
    """Verifies applying a PlanningAction moves unknown condition to satisfied."""
    initial_state = PlanningState(
        satisfied_conditions=frozenset(["REQ_PHYS"]),
        violated_conditions=frozenset(),
        unknown_conditions=frozenset(["REQ_MATH"]),
    )
    action = PlanningAction(
        action_id="ACT_GATHER_MATH",
        title="Provide Math Score",
        description="Submit Math Transcript",
        category=ActionCategory.INFORMATION_GATHERING,
        cost=2.0,
        satisfies_conditions=["REQ_MATH"],
    )

    next_state = initial_state.apply_action(action)
    assert "REQ_MATH" in next_state.satisfied_conditions
    assert "REQ_MATH" not in next_state.unknown_conditions
    assert next_state.fingerprint != initial_state.fingerprint


def test_3_known_optimal_path_found(cs_programme: ProgrammeFrame):
    """Verifies that A* discovers an optimal 2-step pathway when 2 prerequisites are missing."""
    prog_service = ProgrammeService()
    # Mock / register test programme in service
    prog_service._programmes.append(cs_programme)

    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_NEEDS_PATH",
        "subject_scores": [
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
            # MATH missing
            # JEE Main missing
        ],
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = HeistPlannerAgent(programme_service=prog_service)
    result = agent.plan_pathway(twin, "PLAN_TEST_CS", use_heuristic=True)

    assert isinstance(result, PlanningResult)
    assert result.goal_reached is True
    assert len(result.actions) == 2
    action_ids = [a.action_id for a in result.actions]
    assert "ACT_GATHER_MATH" in action_ids
    assert "ACT_APPEAR_JEE_MAIN" in action_ids
    assert result.total_cost == sum(a.cost for a in result.actions)
    assert result.total_duration_days > 0


def test_4_dijkstra_fallback_produces_identical_cost(cs_programme: ProgrammeFrame):
    """Verifies that Dijkstra fallback (h=0) reaches the goal with identical optimal cost."""
    prog_service = ProgrammeService()
    prog_service._programmes.append(cs_programme)

    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_NEEDS_PATH",
        "subject_scores": [
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = HeistPlannerAgent(programme_service=prog_service)
    astar_res = agent.plan_pathway(twin, "PLAN_TEST_CS", use_heuristic=True)
    dijkstra_res = agent.plan_pathway(twin, "PLAN_TEST_CS", use_heuristic=False)

    assert astar_res.goal_reached is True
    assert dijkstra_res.goal_reached is True
    assert astar_res.total_cost == dijkstra_res.total_cost
    assert dijkstra_res.heuristic_used == "Dijkstra (h=0)"


def test_5_already_eligible_returns_zero_cost(cs_programme: ProgrammeFrame):
    """Verifies that an already fully satisfied student requires zero actions."""
    prog_service = ProgrammeService()
    prog_service._programmes.append(cs_programme)

    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_ELIGIBLE",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 15000,
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = HeistPlannerAgent(programme_service=prog_service)
    result = agent.plan_pathway(twin, "PLAN_TEST_CS")

    assert result.goal_reached is True
    assert len(result.actions) == 0
    assert result.total_cost == 0.0
    assert result.initial_status == "eligible"


def test_6_immutable_historical_violation_returns_no_path(cs_programme: ProgrammeFrame):
    """Verifies that an immutable completed score failure cannot be satisfied by illegal retroactive actions."""
    prog_service = ProgrammeService()
    prog_service._programmes.append(cs_programme)

    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_FAILED_MATH",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 50.0, "max_score": 100.0, "grading_scale": "percentage"},  # 50% vs 80% req
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 15000,
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = HeistPlannerAgent(programme_service=prog_service)
    result = agent.plan_pathway(twin, "PLAN_TEST_CS")

    assert result.goal_reached is False
    assert len(result.actions) == 0
    assert any("immutable" in w.lower() for w in result.warnings)


def test_7_alternative_pathway_or_branch(biotech_programme: ProgrammeFrame):
    """Verifies that OR requirement branches allow achieving goal via alternative pathway."""
    prog_service = ProgrammeService()
    prog_service._programmes.append(biotech_programme)

    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_BIO",
        "subject_scores": [],
        "total_budget_inr": 500000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = HeistPlannerAgent(programme_service=prog_service)
    result = agent.plan_pathway(twin, "PLAN_TEST_BIO")

    assert result.goal_reached is True
    assert len(result.actions) == 1
    assert result.actions[0].category == ActionCategory.ELIGIBILITY_PATHWAY
    assert len(result.alternative_routes) >= 2


def test_8_api_plan_endpoint(client: TestClient):
    """Verifies POST /api/v1/planner/plan with profile payload for canonical catalogue programme."""
    payload = {
        "target_programme_id": "SYNTH_IN_CS_01",
        "profile": {
            "student_id": "PLAN_API_STUDENT",
            "subject_scores": [
                {"subject_code": "PHYS", "subject_name": "Physics", "score": 80.0, "max_score": 100.0, "grading_scale": "percentage"},
                # Missing MATH, ENG, JEE Main
            ],
            "total_budget_inr": 700000.0,
        },
        "use_heuristic": True,
    }
    response = client.post("/api/v1/planner/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "plan_id" in data
    assert data["target_programme_id"] == "SYNTH_IN_CS_01"
    assert data["goal_reached"] is True
    assert len(data["actions"]) >= 2
    assert data["total_cost"] > 0
    assert data["total_duration_days"] > 0


def test_9_api_plan_invalid_programme_returns_404(client: TestClient):
    """Verifies that planning toward an unknown programme ID returns 404."""
    payload = {
        "target_programme_id": "NON_EXISTENT_PROG_ID",
        "profile": {
            "student_id": "TEST_STUDENT",
            "subject_scores": [],
            "total_budget_inr": 500000.0,
        },
    }
    response = client.post("/api/v1/planner/plan", json=payload)
    assert response.status_code == 404


def test_10_heuristic_admissibility_on_shared_actions():
    """Mathematically proves h(n) <= h*(n) when a single action satisfies multiple conditions.

    Counterexample test:
    Conditions c1, c2 unsatisfied.
    Action A1 satisfies BOTH c1 and c2 at cost 5.0.
    Action A2 satisfies c1 alone at cost 6.0.
    Action A3 satisfies c2 alone at cost 7.0.

    True optimal cost h*(n) = 5.0 (using A1).
    A flawed sum-of-mins would calculate: min(c1) + min(c2) = 5.0 + 5.0 = 10.0 > 5.0 (INADMISSIBLE).
    Our h_max calculates: max(min(c1), min(c2)) = max(5.0, 5.0) = 5.0 <= 5.0 (STRICTLY ADMISSIBLE).
    """
    agent = HeistPlannerAgent()
    state = PlanningState(
        satisfied_conditions=frozenset(),
        violated_conditions=frozenset(),
        unknown_conditions=frozenset(["c1", "c2"]),
    )
    target_conditions = {"c1", "c2"}
    candidate_actions = [
        PlanningAction(
            action_id="A1_SHARED",
            title="Shared Action",
            description="Satisfies both c1 and c2",
            category=ActionCategory.PREPARATION,
            cost=5.0,
            satisfies_conditions=["c1", "c2"],
        ),
        PlanningAction(
            action_id="A2_SOLO",
            title="Solo c1",
            description="Satisfies c1",
            category=ActionCategory.PREPARATION,
            cost=6.0,
            satisfies_conditions=["c1"],
        ),
        PlanningAction(
            action_id="A3_SOLO",
            title="Solo c2",
            description="Satisfies c2",
            category=ActionCategory.PREPARATION,
            cost=7.0,
            satisfies_conditions=["c2"],
        ),
    ]

    h_val = agent._admissible_heuristic(
        state=state,
        target_conditions=target_conditions,
        or_branches={},
        candidate_actions=candidate_actions,
    )

    true_optimal_cost = 5.0
    # Strict admissibility check: h(n) <= h*(n)
    assert h_val <= true_optimal_cost, f"Heuristic {h_val} overestimates true cost {true_optimal_cost}"
    assert h_val == 5.0


def test_11_heuristic_admissibility_with_or_branches():
    """Verifies that OR-branch heuristic h_AnyOf = min_b h(b) remains strictly admissible."""
    agent = HeistPlannerAgent()
    state = PlanningState(
        satisfied_conditions=frozenset(),
        violated_conditions=frozenset(),
        unknown_conditions=frozenset(["base_req", "opt1", "opt2"]),
    )
    target_conditions = {"base_req", "opt1", "opt2"}
    or_branches = {
        "BRANCH_A": {"opt1"},
        "BRANCH_B": {"opt2"},
    }
    candidate_actions = [
        PlanningAction(
            action_id="ACT_BASE",
            title="Base Action",
            description="Base requirement",
            category=ActionCategory.PREPARATION,
            cost=3.0,
            satisfies_conditions=["base_req"],
        ),
        PlanningAction(
            action_id="ACT_OPT1",
            title="Option 1 Action",
            description="Fulfills branch A",
            category=ActionCategory.PREPARATION,
            cost=8.0,
            satisfies_conditions=["opt1"],
        ),
        PlanningAction(
            action_id="ACT_OPT2",
            title="Option 2 Action",
            description="Fulfills branch B",
            category=ActionCategory.PREPARATION,
            cost=4.0,
            satisfies_conditions=["opt2"],
        ),
    ]

    h_val = agent._admissible_heuristic(
        state=state,
        target_conditions=target_conditions,
        or_branches=or_branches,
        candidate_actions=candidate_actions,
    )

    # Base needs 3.0. Branches: Branch A needs 8.0, Branch B needs 4.0.
    # Combined lower bound = max(3.0, min(8.0, 4.0)) = max(3.0, 4.0) = 4.0.
    # True optimal plan: ACT_BASE (3.0) + ACT_OPT2 (4.0) = 7.0.
    # 4.0 <= 7.0, so strictly admissible!
    assert h_val <= 7.0
    assert h_val == 4.0


def test_12_astar_optimality_and_efficiency_vs_dijkstra(cs_programme: ProgrammeFrame):
    """Verifies that A* achieves exact same optimal cost as Dijkstra while expanding <= nodes."""
    prog_service = ProgrammeService()
    prog_service._programmes.append(cs_programme)

    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_OPTIMALITY_TEST",
        "subject_scores": [
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = HeistPlannerAgent(programme_service=prog_service)
    astar_res = agent.plan_pathway(twin, "PLAN_TEST_CS", use_heuristic=True)
    dijkstra_res = agent.plan_pathway(twin, "PLAN_TEST_CS", use_heuristic=False)

    assert astar_res.goal_reached is True
    assert dijkstra_res.goal_reached is True
    assert astar_res.total_cost == dijkstra_res.total_cost
    assert astar_res.nodes_expanded <= dijkstra_res.nodes_expanded


def test_13_zero_cost_action_preserves_non_negativity():
    """Verifies that zero-cost actions preserve non-negativity without cycles or negative heuristics."""
    agent = HeistPlannerAgent()
    state = PlanningState(
        satisfied_conditions=frozenset(),
        violated_conditions=frozenset(),
        unknown_conditions=frozenset(["req_free"]),
    )
    candidate_actions = [
        PlanningAction(
            action_id="ACT_FREE",
            title="Free Declaration",
            description="Satisfies free requirement at zero cost",
            category=ActionCategory.DOCUMENTATION,
            cost=0.0,
            satisfies_conditions=["req_free"],
        )
    ]
    h_val = agent._admissible_heuristic(
        state=state,
        target_conditions={"req_free"},
        or_branches={},
        candidate_actions=candidate_actions,
    )
    assert h_val == 0.0


