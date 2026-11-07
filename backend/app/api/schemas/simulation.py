"""Pydantic transport schemas for Simulator and Boss-Fight Agent (M004)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.api.schemas.student import StudentProfileRequest


class MonteCarloConfigDto(BaseModel):
    """Configuration parameters for stochastic Monte Carlo runs."""

    iterations: int = Field(default=100, ge=10, le=1000)
    seed: int = Field(default=42)
    budget_std_dev_pct: float = Field(default=0.15, ge=0.01, le=1.0)
    rank_slip_std_dev_pct: float = Field(default=0.20, ge=0.01, le=1.0)
    tuition_inflation_mean_pct: float = Field(default=0.08, ge=0.0, le=1.0)


class SimulationRequestDto(BaseModel):
    """Request payload for running counterfactual or Monte Carlo simulations."""

    target_programme_id: str = Field(..., description="Target programme ID")
    scenario_type: str = Field(
        default="tuition_increase",
        description="Scenario type: tuition_increase, budget_decrease, entrance_rank_deterioration, cutoff_movement, monte_carlo_multivariate, etc.",
    )
    snapshot_id: Optional[str] = Field(default=None)
    twin_id: Optional[str] = Field(default=None)
    profile: Optional[StudentProfileRequest] = Field(default=None)
    parameters: Optional[Dict[str, Any]] = Field(default=None)
    monte_carlo_config: Optional[MonteCarloConfigDto] = Field(default=None)


class ScenarioDefinitionDto(BaseModel):
    scenario_id: str
    scenario_type: str
    base_snapshot_id: str
    changed_variables: Dict[str, Any]
    original_values: Dict[str, Any]
    hypothetical_values: Dict[str, Any]
    assumptions: List[str]
    is_hypothetical: bool
    random_seed: Optional[int] = None


class DistributionMetricDto(BaseModel):
    variable_name: str
    mean: float
    median: float
    p10: float
    p50: float
    p90: float
    min_val: float
    max_val: float


class SimulationResultDto(BaseModel):
    """Response bundle from a simulation execution."""

    simulation_id: str
    snapshot_id: str
    target_programme_id: str
    scenario: ScenarioDefinitionDto
    baseline_eligible: bool
    baseline_affordable: bool
    scenario_eligible: bool
    scenario_affordable: bool
    eligibility_changed: bool
    affordability_changed: bool
    monte_carlo_metrics: Optional[Dict[str, DistributionMetricDto]] = None
    monte_carlo_outcome_frequencies: Optional[Dict[str, float]] = None
    delta_summary: str
    warnings: List[str]
    executed_at: str


class BossFightRequestDto(BaseModel):
    """Request payload for adversarial stress-testing."""

    target_programme_id: str = Field(..., description="Target programme ID to attack")
    snapshot_id: Optional[str] = Field(default=None)
    twin_id: Optional[str] = Field(default=None)
    profile: Optional[StudentProfileRequest] = Field(default=None)


class AttackOutcomeDto(BaseModel):
    attack_type: str
    perturbation_description: str
    baseline_status: str
    perturbed_status: str
    survived: bool
    failed_constraint: Optional[str] = None
    explanation: str


class BossFightReportDto(BaseModel):
    """Response report from Boss-Fight adversarial evaluation."""

    report_id: str
    target_programme_id: str
    target_programme_title: str
    snapshot_id: str
    overall_robustness: str
    total_attacks_tested: int
    attacks_survived: int
    attacks_failed: int
    attack_outcomes: List[AttackOutcomeDto]
    surviving_alternative_programmes: List[str]
    fallback_recommendation: str
    disclaimer: str
    executed_at: str

