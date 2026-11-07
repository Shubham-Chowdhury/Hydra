"""Domain models for Hydra Simulator and Boss-Fight Agent (M004).

Represents hypothetical scenarios, counterfactual parameters, Monte Carlo distributions,
adversarial perturbations, and robustness classifications.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ScenarioType(str, Enum):
    """Categorization of counterfactual scenario perturbations."""

    TUITION_INCREASE = "tuition_increase"
    BUDGET_DECREASE = "budget_decrease"
    ENTRANCE_RANK_DETERIORATION = "entrance_rank_deterioration"
    CUTOFF_MOVEMENT = "cutoff_movement"
    SEAT_AVAILABILITY_REDUCTION = "seat_availability_reduction"
    GEOGRAPHIC_PREFERENCE_CHANGE = "geographic_preference_change"
    MISSING_MANDATORY_EVIDENCE = "missing_mandatory_evidence"
    ALTERNATIVE_PATHWAY_REMOVAL = "alternative_pathway_removal"
    PROGRAMME_REMOVAL = "programme_removal"
    PROGRAMME_PREFERENCE_CHANGE = "programme_preference_change"
    MONTE_CARLO_MULTIVARIATE = "monte_carlo_multivariate"


@dataclass(frozen=True)
class ScenarioDefinition:
    """Explicit, versioned definition of a counterfactual simulation scenario."""

    scenario_id: str
    scenario_type: ScenarioType
    base_snapshot_id: str
    changed_variables: Dict[str, Any]
    original_values: Dict[str, Any]
    hypothetical_values: Dict[str, Any]
    assumptions: List[str]
    is_hypothetical: bool = True
    random_seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type.value,
            "base_snapshot_id": self.base_snapshot_id,
            "changed_variables": self.changed_variables,
            "original_values": self.original_values,
            "hypothetical_values": self.hypothetical_values,
            "assumptions": list(self.assumptions),
            "is_hypothetical": self.is_hypothetical,
            "random_seed": self.random_seed,
        }


@dataclass(frozen=True)
class MonteCarloConfig:
    """Configuration for reproducible stochastic Monte Carlo simulations."""

    iterations: int = 100
    seed: int = 42
    budget_std_dev_pct: float = 0.15
    rank_slip_std_dev_pct: float = 0.20
    tuition_inflation_mean_pct: float = 0.08
    is_empirical: bool = False
    distribution_assumption: str = (
        "Hypothetical Gaussian demonstration perturbation model. "
        "Parameters are demonstration assumptions, NOT fitted empirical observations."
    )


@dataclass(frozen=True)
class DistributionMetric:
    """Summary statistics for a simulated distribution variable."""

    variable_name: str
    mean: float
    median: float
    p10: float
    p50: float
    p90: float
    min_val: float
    max_val: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable_name": self.variable_name,
            "mean": round(self.mean, 2),
            "median": round(self.median, 2),
            "p10": round(self.p10, 2),
            "p50": round(self.p50, 2),
            "p90": round(self.p90, 2),
            "min_val": round(self.min_val, 2),
            "max_val": round(self.max_val, 2),
        }


@dataclass(frozen=True)
class SimulationResult:
    """Complete result of a deterministic or Monte Carlo scenario simulation."""

    simulation_id: str
    snapshot_id: str
    target_programme_id: str
    scenario: ScenarioDefinition
    baseline_eligible: bool
    baseline_affordable: bool
    scenario_eligible: bool
    scenario_affordable: bool
    eligibility_changed: bool
    affordability_changed: bool
    monte_carlo_metrics: Optional[Dict[str, DistributionMetric]] = None
    monte_carlo_outcome_frequencies: Optional[Dict[str, float]] = None
    delta_summary: str = ""
    warnings: List[str] = field(default_factory=list)
    executed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "snapshot_id": self.snapshot_id,
            "target_programme_id": self.target_programme_id,
            "scenario": self.scenario.to_dict(),
            "baseline_eligible": self.baseline_eligible,
            "baseline_affordable": self.baseline_affordable,
            "scenario_eligible": self.scenario_eligible,
            "scenario_affordable": self.scenario_affordable,
            "eligibility_changed": self.eligibility_changed,
            "affordability_changed": self.affordability_changed,
            "monte_carlo_metrics": (
                {k: v.to_dict() for k, v in self.monte_carlo_metrics.items()}
                if self.monte_carlo_metrics
                else None
            ),
            "monte_carlo_outcome_frequencies": self.monte_carlo_outcome_frequencies,
            "delta_summary": self.delta_summary,
            "warnings": list(self.warnings),
            "executed_at": self.executed_at,
        }


class RobustnessClassification(str, Enum):
    """Adversarial stress-test survival classification."""

    ROBUST_UNDER_TESTED_SCENARIOS = "robust_under_tested_scenarios"
    FRAGILE = "fragile"
    FAILS_UNDER_TESTED_SCENARIOS = "fails_under_tested_scenarios"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class AdversarialAttackType(str, Enum):
    """Catalog of adversarial stress-test attack vectors."""

    RANK_WORSENS = "rank_worsens"
    TUITION_HIKED = "tuition_hiked"
    BUDGET_REDUCED = "budget_reduced"
    CUTOFF_STIFFENS = "cutoff_stiffens"
    DOCUMENT_UNOBTAINABLE = "document_unobtainable"
    PATHWAY_DISAPPEARS = "pathway_disappears"
    PREFERENCE_SHIFTS = "preference_shifts"


@dataclass(frozen=True)
class AttackOutcome:
    """Outcome of an individual adversarial attack perturbation."""

    attack_type: AdversarialAttackType
    perturbation_description: str
    baseline_status: str
    perturbed_status: str
    survived: bool
    failed_constraint: Optional[str] = None
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack_type": self.attack_type.value,
            "perturbation_description": self.perturbation_description,
            "baseline_status": self.baseline_status,
            "perturbed_status": self.perturbed_status,
            "survived": self.survived,
            "failed_constraint": self.failed_constraint,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class BossFightReport:
    """Comprehensive stress-test report produced by the Boss-Fight Agent."""

    report_id: str
    target_programme_id: str
    target_programme_title: str
    snapshot_id: str
    overall_robustness: RobustnessClassification
    total_attacks_tested: int
    attacks_survived: int
    attacks_failed: int
    attack_outcomes: List[AttackOutcome]
    surviving_alternative_programmes: List[str]
    fallback_recommendation: str
    disclaimer: str
    executed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "target_programme_id": self.target_programme_id,
            "target_programme_title": self.target_programme_title,
            "snapshot_id": self.snapshot_id,
            "overall_robustness": self.overall_robustness.value,
            "total_attacks_tested": self.total_attacks_tested,
            "attacks_survived": self.attacks_survived,
            "attacks_failed": self.attacks_failed,
            "attack_outcomes": [a.to_dict() for a in self.attack_outcomes],
            "surviving_alternative_programmes": list(
                self.surviving_alternative_programmes
            ),
            "fallback_recommendation": self.fallback_recommendation,
            "disclaimer": self.disclaimer,
            "executed_at": self.executed_at,
        }

