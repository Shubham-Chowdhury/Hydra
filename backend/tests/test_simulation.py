"""Unit and integration test suite for Hydra Simulator and Boss-Fight Agent (M004).

Tests deterministic scenario isolation, seeded Monte Carlo reproducibility,
adversarial attack battery, robustness classifications, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.agents.boss_fight import BossFightAgent
from app.agents.simulator import SimulatorAgent
from app.agents.twin_agent import TwinAgent
from app.domain.frames import (
    AcademicPrerequisite,
    EntrancePrerequisite,
    ProgrammeFrame,
)
from app.domain.simulation import (
    MonteCarloConfig,
    RobustnessClassification,
    ScenarioType,
    SimulationResult,
)
from app.main import app
from app.services.programme_service import ProgrammeService
from app.services.simulation_service import SimulationService


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def eligible_twin():
    agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_SIM",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 80.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 15000,
        "preferred_locations": ["Bengaluru, Karnataka"],
        "total_budget_inr": 800000.0,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }
    return agent.construct_twin(profile)


def test_1_scenario_sandbox_isolation(eligible_twin):
    """Verifies that counterfactual modifications never alter the original TwinSnapshot or student frame."""
    prog_service = ProgrammeService()
    sim_agent = SimulatorAgent(programme_service=prog_service)

    orig_budget = eligible_twin.student_frame.total_budget_inr
    result = sim_agent.run_deterministic_scenario(
        eligible_twin,
        "SYNTH_IN_CS_01",
        ScenarioType.BUDGET_DECREASE,
        {"budget_decrease_pct": 0.50},
    )

    assert result.affordability_changed is True
    assert result.scenario_affordable is False
    # Original student frame is strictly unmodified
    assert eligible_twin.student_frame.total_budget_inr == orig_budget
    assert eligible_twin.financial_constraints.total_budget_inr == orig_budget


def test_2_tuition_increase_scenario(eligible_twin):
    """Verifies tuition hike scenario turns an affordable programme into unaffordable while preserving eligibility."""
    prog_service = ProgrammeService()
    sim_agent = SimulatorAgent(programme_service=prog_service)

    # CS programme tuition is 600,000 INR; student budget is 800,000 INR
    # Hike of 50% makes tuition 900,000 INR (> 800,000)
    result = sim_agent.run_deterministic_scenario(
        eligible_twin,
        "SYNTH_IN_CS_01",
        ScenarioType.TUITION_INCREASE,
        {"tuition_increase_pct": 0.50},
    )

    assert result.baseline_affordable is True
    assert result.scenario_affordable is False
    assert result.baseline_eligible is True
    assert result.scenario_eligible is True  # Formal eligibility unaffected!
    assert result.affordability_changed is True
    assert result.eligibility_changed is False


def test_3_entrance_rank_slip_scenario(eligible_twin):
    """Verifies entrance rank deterioration causes eligible programme to become ineligible."""
    prog_service = ProgrammeService()
    sim_agent = SimulatorAgent(programme_service=prog_service)

    # CS max rank is 35,000; student rank is 15,000. Slip of +30,000 puts student at 45,000 (> 35,000)
    result = sim_agent.run_deterministic_scenario(
        eligible_twin,
        "SYNTH_IN_CS_01",
        ScenarioType.ENTRANCE_RANK_DETERIORATION,
        {"rank_slip_positions": 30000},
    )

    assert result.baseline_eligible is True
    assert result.scenario_eligible is False
    assert result.eligibility_changed is True


def test_4_monte_carlo_seeded_reproducibility(eligible_twin):
    """Verifies that identical Monte Carlo seeds yield identical statistical distributions."""
    prog_service = ProgrammeService()
    sim_agent = SimulatorAgent(programme_service=prog_service)

    cfg = MonteCarloConfig(iterations=50, seed=123)
    res1 = sim_agent.run_monte_carlo(eligible_twin, "SYNTH_IN_CS_01", cfg)
    res2 = sim_agent.run_monte_carlo(eligible_twin, "SYNTH_IN_CS_01", cfg)

    assert res1.monte_carlo_outcome_frequencies == res2.monte_carlo_outcome_frequencies
    assert res1.monte_carlo_metrics["budget_inr"].mean == res2.monte_carlo_metrics["budget_inr"].mean
    assert res1.monte_carlo_metrics["entrance_rank"].p90 == res2.monte_carlo_metrics["entrance_rank"].p90


def test_5_monte_carlo_distribution_metrics(eligible_twin):
    """Verifies statistical quantile integrity (min <= p10 <= p50 <= p90 <= max)."""
    prog_service = ProgrammeService()
    sim_agent = SimulatorAgent(programme_service=prog_service)

    cfg = MonteCarloConfig(iterations=100, seed=99)
    res = sim_agent.run_monte_carlo(eligible_twin, "SYNTH_IN_CS_01", cfg)

    m = res.monte_carlo_metrics["budget_inr"]
    assert m.min_val <= m.p10 <= m.median <= m.p90 <= m.max_val
    assert m.median == m.p50
    assert 0.0 <= res.monte_carlo_outcome_frequencies["eligible_and_affordable"] <= 1.0


def test_6_boss_fight_adversarial_battery(eligible_twin):
    """Verifies Boss-Fight agent runs all 6 attack vectors and classifies robustness."""
    prog_service = ProgrammeService()
    boss_agent = BossFightAgent(programme_service=prog_service)

    report = boss_agent.stress_test(eligible_twin, "SYNTH_IN_CS_01")
    assert report.total_attacks_tested == 6
    assert report.attacks_survived + report.attacks_failed == 6
    assert isinstance(report.overall_robustness, RobustnessClassification)
    assert len(report.attack_outcomes) == 6
    assert report.fallback_recommendation is not None
    assert "BOSS-FIGHT ADVERSARIAL STRESS TEST" in report.disclaimer


def test_7_boss_fight_insufficient_evidence_when_baseline_needs_review():
    """Verifies that an applicant with missing prerequisite facts yields INSUFFICIENT_EVIDENCE."""
    agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_INCOMPLETE",
        "subject_scores": [],  # Missing MATH, PHYS
        "total_budget_inr": 800000.0,
    }
    twin = agent.construct_twin(profile)

    boss_agent = BossFightAgent()
    report = boss_agent.stress_test(twin, "SYNTH_IN_CS_01")
    assert report.overall_robustness == RobustnessClassification.INSUFFICIENT_EVIDENCE


def test_8_api_run_simulation_deterministic(client: TestClient):
    """Verifies POST /api/v1/simulation/run with deterministic counterfactual."""
    payload = {
        "target_programme_id": "SYNTH_IN_CS_01",
        "scenario_type": "tuition_increase",
        "parameters": {"tuition_increase_pct": 0.30},
        "profile": {
            "student_id": "API_SIM_STUDENT",
            "subject_scores": [
                {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
                {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
                {"subject_code": "ENG", "subject_name": "English", "score": 80.0, "max_score": 100.0, "grading_scale": "percentage"},
            ],
            "entrance_exam_name": "JEE Main",
            "entrance_rank": 10000,
            "total_budget_inr": 800000.0,
        },
    }
    response = client.post("/api/v1/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "simulation_id" in data
    assert data["target_programme_id"] == "SYNTH_IN_CS_01"
    assert "scenario" in data
    assert data["scenario"]["is_hypothetical"] is True


def test_9_api_run_simulation_monte_carlo(client: TestClient):
    """Verifies POST /api/v1/simulation/run with Monte Carlo stochastic simulation."""
    payload = {
        "target_programme_id": "SYNTH_IN_CS_01",
        "scenario_type": "monte_carlo_multivariate",
        "monte_carlo_config": {"iterations": 50, "seed": 77},
        "profile": {
            "student_id": "API_MC_STUDENT",
            "subject_scores": [
                {"subject_code": "MATH", "subject_name": "Mathematics", "score": 88.0, "max_score": 100.0, "grading_scale": "percentage"},
                {"subject_code": "PHYS", "subject_name": "Physics", "score": 80.0, "max_score": 100.0, "grading_scale": "percentage"},
            ],
            "entrance_exam_name": "JEE Main",
            "entrance_rank": 20000,
            "total_budget_inr": 700000.0,
        },
    }
    response = client.post("/api/v1/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["monte_carlo_metrics"] is not None
    assert "budget_inr" in data["monte_carlo_metrics"]
    assert "entrance_rank" in data["monte_carlo_metrics"]
    assert data["monte_carlo_outcome_frequencies"] is not None


def test_10_api_boss_fight_stress_test(client: TestClient):
    """Verifies POST /api/v1/simulation/stress-test endpoint."""
    payload = {
        "target_programme_id": "SYNTH_IN_CS_01",
        "profile": {
            "student_id": "API_BOSS_STUDENT",
            "subject_scores": [
                {"subject_code": "MATH", "subject_name": "Mathematics", "score": 95.0, "max_score": 100.0, "grading_scale": "percentage"},
                {"subject_code": "PHYS", "subject_name": "Physics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
                {"subject_code": "ENG", "subject_name": "English", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
            ],
            "entrance_exam_name": "JEE Main",
            "entrance_rank": 5000,
            "total_budget_inr": 1200000.0,
        },
    }
    response = client.post("/api/v1/simulation/stress-test", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert data["overall_robustness"] in [
        "robust_under_tested_scenarios",
        "fragile",
        "fails_under_tested_scenarios",
        "insufficient_evidence",
    ]
    assert data["total_attacks_tested"] == 6
    assert len(data["attack_outcomes"]) == 6


def test_11_monte_carlo_statistical_boundaries_and_quantiles(eligible_twin):
    """Verifies that Monte Carlo simulation enforces strict boundary constraints and quantile monotonicity."""
    prog_service = ProgrammeService()
    sim_agent = SimulatorAgent(programme_service=prog_service)

    # Run with 200 iterations
    cfg = MonteCarloConfig(iterations=200, seed=12345, budget_std_dev_pct=0.30, rank_slip_std_dev_pct=0.40)
    result = sim_agent.run_monte_carlo(eligible_twin, "SYNTH_IN_CS_01", config=cfg)

    metrics = result.monte_carlo_metrics
    assert metrics is not None

    # 1. Boundary constraints on ranks: must be integer >= 1
    rank_metric = metrics["entrance_rank"]
    assert rank_metric.min_val >= 1.0
    assert rank_metric.p10 >= 1.0
    assert rank_metric.median >= 1.0
    assert rank_metric.max_val >= rank_metric.min_val

    # 2. Boundary constraints on budgets and tuition: must be >= 0.0
    budget_metric = metrics["budget_inr"]
    tuition_metric = metrics["tuition_inr"]
    assert budget_metric.min_val >= 0.0
    assert tuition_metric.min_val >= 0.0

    # 3. Quantile monotonicity: p10 <= p50 <= p90
    for name, m in metrics.items():
        assert m.min_val <= m.p10, f"{name}: min_val {m.min_val} > p10 {m.p10}"
        assert m.p10 <= m.p50, f"{name}: p10 {m.p10} > p50 {m.p50}"
        assert m.p50 <= m.p90, f"{name}: p50 {m.p50} > p90 {m.p90}"
        assert m.p90 <= m.max_val, f"{name}: p90 {m.p90} > max_val {m.max_val}"


def test_12_covariance_matrix_psd_validation():
    """Verifies positive semi-definite (PSD) and symmetry checks for covariance matrices."""
    # Valid 2x2 PSD matrix
    valid_psd = [
        [1.0, 0.5],
        [0.5, 1.0],
    ]
    is_valid, msg = SimulatorAgent.validate_covariance_matrix(valid_psd)
    assert is_valid is True

    # Asymmetric matrix
    asymmetric = [
        [1.0, 0.8],
        [0.2, 1.0],
    ]
    is_valid, msg = SimulatorAgent.validate_covariance_matrix(asymmetric)
    assert is_valid is False
    assert "asymmetric" in msg.lower()

    # Non-PSD matrix (negative eigenvalue)
    non_psd = [
        [1.0, 1.5],
        [1.5, 1.0],
    ]
    is_valid, msg = SimulatorAgent.validate_covariance_matrix(non_psd)
    assert is_valid is False
    assert "positive semi-definite" in msg.lower()


def test_13_covariance_matrix_non_finite_and_dimension_checks():
    """Verifies that non-finite values (NaN, Inf), non-square shapes, and empty matrices are rejected."""
    # NaN matrix
    import math
    nan_mat = [
        [1.0, float("nan")],
        [float("nan"), 1.0],
    ]
    is_valid, msg = SimulatorAgent.validate_covariance_matrix(nan_mat)
    assert is_valid is False
    assert "non-finite" in msg.lower()

    # Inf matrix
    inf_mat = [
        [1.0, float("inf")],
        [float("inf"), 1.0],
    ]
    is_valid, msg = SimulatorAgent.validate_covariance_matrix(inf_mat)
    assert is_valid is False
    assert "non-finite" in msg.lower()

    # Non-square matrix
    rect_mat = [
        [1.0, 0.5, 0.2],
        [0.5, 1.0, 0.3],
    ]
    is_valid, msg = SimulatorAgent.validate_covariance_matrix(rect_mat)
    assert is_valid is False
    assert "not square" in msg.lower()

    # Empty matrix
    is_valid, msg = SimulatorAgent.validate_covariance_matrix([])
    assert is_valid is False


def test_14_monte_carlo_seeded_reproducibility(eligible_twin):
    """Verifies that identical random seeds yield bit-for-bit identical simulations."""
    prog_service = ProgrammeService()
    sim_agent = SimulatorAgent(programme_service=prog_service)

    cfg1 = MonteCarloConfig(iterations=100, seed=999)
    res1 = sim_agent.run_monte_carlo(eligible_twin, "SYNTH_IN_CS_01", config=cfg1)

    cfg2 = MonteCarloConfig(iterations=100, seed=999)
    res2 = sim_agent.run_monte_carlo(eligible_twin, "SYNTH_IN_CS_01", config=cfg2)

    assert res1.monte_carlo_outcome_frequencies == res2.monte_carlo_outcome_frequencies
    for k in res1.monte_carlo_metrics:
        m1 = res1.monte_carlo_metrics[k]
        m2 = res2.monte_carlo_metrics[k]
        assert m1.mean == m2.mean
        assert m1.median == m2.median
        assert m1.p10 == m2.p10
        assert m1.p90 == m2.p90


def test_15_simulation_hypothetical_demarcation(eligible_twin):
    """Verifies explicit demarcation: simulation data is hypothetical and not empirical university data."""
    prog_service = ProgrammeService()
    sim_agent = SimulatorAgent(programme_service=prog_service)
    cfg = MonteCarloConfig(iterations=50, seed=42)
    res = sim_agent.run_monte_carlo(eligible_twin, "SYNTH_IN_CS_01", config=cfg)

    assert res.scenario.is_hypothetical is True
    assert cfg.is_empirical is False
    assert any("not admission guarantees" in w.lower() for w in res.warnings)


