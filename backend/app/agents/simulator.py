"""Simulator Agent for Hydra (Deterministic Counterfactuals & Seeded Monte Carlo).

Evaluates hypothetical 'what-if' scenarios altering admissions conditions, student budget,
and competitive entrance ranks in an isolated sandbox state.
"""

from copy import deepcopy
from datetime import datetime, timezone
import math
import random
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.domain.frames import EligibilityStatus, ProgrammeFrame, StudentFrame
from app.domain.simulation import (
    DistributionMetric,
    MonteCarloConfig,
    ScenarioDefinition,
    ScenarioType,
    SimulationResult,
)
from app.domain.twin import TwinSnapshot
from app.rules.engine import RuleEngine
from app.services.programme_service import ProgrammeService


class SimulatorAgent:
    """Agent executing isolated hypothetical simulations and Monte Carlo analysis."""

    def __init__(
        self,
        programme_service: Optional[ProgrammeService] = None,
        rule_engine: Optional[RuleEngine] = None,
    ) -> None:
        self.programme_service = programme_service or ProgrammeService()
        self.rule_engine = rule_engine or RuleEngine()

    def run_deterministic_scenario(
        self,
        twin_snapshot: TwinSnapshot,
        programme_id: str,
        scenario_type: ScenarioType,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> SimulationResult:
        """Executes a deterministic counterfactual simulation on an isolated clone of student/programme."""
        programme = self.programme_service.get_by_id(programme_id)
        if not programme:
            raise ValueError(f"Target programme '{programme_id}' not found.")

        params = parameters or {}
        now_utc = datetime.now(timezone.utc).isoformat()
        sim_id = f"SIM_{programme_id}_{uuid.uuid4().hex[:8]}"

        # 1. Baseline Evaluation
        base_student = twin_snapshot.student_frame
        base_trace = self.rule_engine.evaluate(
            base_student, programme, frame_registry=self.programme_service.frame_registry
        )
        base_eligible = base_trace.final_status == EligibilityStatus.ELIGIBLE
        base_affordable = base_student.total_budget_inr >= programme.estimated_total_tuition_inr

        # 2. Construct Isolated Counterfactual Sandbox
        hypo_student = deepcopy(base_student)
        hypo_programme = deepcopy(programme)

        changed_vars: Dict[str, Any] = {}
        original_vals: Dict[str, Any] = {}
        hypo_vals: Dict[str, Any] = {}
        assumptions: List[str] = []

        # 3. Apply Scenario Perturbation
        if scenario_type == ScenarioType.TUITION_INCREASE:
            pct = params.get("tuition_increase_pct", 0.20)
            original_vals["estimated_total_tuition_inr"] = programme.estimated_total_tuition_inr
            new_tuition = round(programme.estimated_total_tuition_inr * (1.0 + pct), 2)
            hypo_programme.estimated_total_tuition_inr = new_tuition
            changed_vars["estimated_total_tuition_inr"] = f"+{pct * 100:.1f}%"
            hypo_vals["estimated_total_tuition_inr"] = new_tuition
            assumptions.append(f"Institutional tuition fee rises by {pct * 100:.1f}% across all 4 years.")

        elif scenario_type == ScenarioType.BUDGET_DECREASE:
            pct = params.get("budget_decrease_pct", 0.25)
            original_vals["total_budget_inr"] = base_student.total_budget_inr
            new_budget = max(0.0, round(base_student.total_budget_inr * (1.0 - pct), 2))
            hypo_student.total_budget_inr = new_budget
            changed_vars["total_budget_inr"] = f"-{pct * 100:.1f}%"
            hypo_vals["total_budget_inr"] = new_budget
            assumptions.append(f"Student family educational budget reduces by {pct * 100:.1f}%.")

        elif scenario_type == ScenarioType.ENTRANCE_RANK_DETERIORATION:
            slip = params.get("rank_slip_positions", 15000)
            curr_rank = base_student.entrance_rank or 20000
            original_vals["entrance_rank"] = curr_rank
            new_rank = curr_rank + slip
            hypo_student.entrance_rank = new_rank
            changed_vars["entrance_rank"] = f"+{slip} positions"
            hypo_vals["entrance_rank"] = new_rank
            assumptions.append(f"Entrance examination competitive rank drops by {slip} places.")

        elif scenario_type == ScenarioType.CUTOFF_MOVEMENT:
            stricter_pct = params.get("cutoff_tighten_pct", 0.20)
            if programme.entrance_prerequisites:
                orig_prereq = programme.entrance_prerequisites[0]
                if orig_prereq.max_rank:
                    original_vals["max_rank"] = orig_prereq.max_rank
                    new_max = int(orig_prereq.max_rank * (1.0 - stricter_pct))
                    hypo_programme.entrance_prerequisites = [
                        type(orig_prereq)(
                            exam_name=orig_prereq.exam_name,
                            max_rank=new_max,
                            is_mandatory=orig_prereq.is_mandatory,
                        )
                    ]
                    changed_vars["cutoff_max_rank"] = f"-{stricter_pct * 100:.1f}% (Stricter)"
                    hypo_vals["max_rank"] = new_max
                    assumptions.append(f"Closing cutoff rank becomes {stricter_pct * 100:.1f}% more competitive.")

        elif scenario_type == ScenarioType.GEOGRAPHIC_PREFERENCE_CHANGE:
            new_locs = params.get("new_preferred_locations", ["Delhi"])
            original_vals["preferred_locations"] = list(base_student.preferred_locations)
            hypo_student.preferred_locations = list(new_locs)
            changed_vars["preferred_locations"] = new_locs
            hypo_vals["preferred_locations"] = new_locs
            assumptions.append(f"Student restricts preferred locations strictly to: {', '.join(new_locs)}.")

        elif scenario_type == ScenarioType.MISSING_MANDATORY_EVIDENCE:
            original_vals["subject_scores_count"] = len(base_student.subject_scores)
            hypo_student.subject_scores = [s for s in base_student.subject_scores if s.subject_code != "MATH"]
            changed_vars["subject_scores"] = "Removed Mathematics transcript"
            hypo_vals["subject_scores_count"] = len(hypo_student.subject_scores)
            assumptions.append("Mathematics official marksheet cannot be verified or provided.")

        else:
            assumptions.append(f"Applied generic counterfactual scenario {scenario_type.value}.")

        # 4. Evaluate Counterfactual State
        scenario_trace = self.rule_engine.evaluate(
            hypo_student, hypo_programme, frame_registry=self.programme_service.frame_registry
        )
        scenario_eligible = scenario_trace.final_status == EligibilityStatus.ELIGIBLE
        scenario_affordable = hypo_student.total_budget_inr >= hypo_programme.estimated_total_tuition_inr

        eligibility_changed = base_eligible != scenario_eligible
        affordability_changed = base_affordable != scenario_affordable

        delta_summary = (
            f"Scenario '{scenario_type.value}': Eligibility "
            f"({'CHANGED: ' + base_trace.final_status.value + ' -> ' + scenario_trace.final_status.value if eligibility_changed else 'Preserved as ' + base_trace.final_status.value}); "
            f"Affordability ({'CHANGED: ' + ('Affordable -> Unaffordable' if base_affordable and not scenario_affordable else 'Unaffordable -> Affordable') if affordability_changed else ('Remains ' + ('Affordable' if base_affordable else 'Unaffordable'))})."
        )

        scenario_def = ScenarioDefinition(
            scenario_id=f"SCEN_{scenario_type.value.upper()}_{sim_id[-6:]}",
            scenario_type=scenario_type,
            base_snapshot_id=twin_snapshot.snapshot_id,
            changed_variables=changed_vars,
            original_values=original_vals,
            hypothetical_values=hypo_vals,
            assumptions=assumptions,
            is_hypothetical=True,
            random_seed=None,
        )

        return SimulationResult(
            simulation_id=sim_id,
            snapshot_id=twin_snapshot.snapshot_id,
            target_programme_id=programme.programme_id,
            scenario=scenario_def,
            baseline_eligible=base_eligible,
            baseline_affordable=base_affordable,
            scenario_eligible=scenario_eligible,
            scenario_affordable=scenario_affordable,
            eligibility_changed=eligibility_changed,
            affordability_changed=affordability_changed,
            delta_summary=delta_summary,
            warnings=[
                "HYPOTHETICAL SIMULATION: Values represent synthetic counterfactual projections and do not modify authoritative records."
            ],
            executed_at=now_utc,
        )

    def run_monte_carlo(
        self,
        twin_snapshot: TwinSnapshot,
        programme_id: str,
        config: Optional[MonteCarloConfig] = None,
    ) -> SimulationResult:
        """Executes a seeded stochastic Monte Carlo simulation across N iterations."""
        programme = self.programme_service.get_by_id(programme_id)
        if not programme:
            raise ValueError(f"Target programme '{programme_id}' not found.")

        cfg = config or MonteCarloConfig()
        iterations = min(1000, max(10, cfg.iterations))
        rng = random.Random(cfg.seed)

        now_utc = datetime.now(timezone.utc).isoformat()
        sim_id = f"SIM_MC_{programme_id}_{uuid.uuid4().hex[:8]}"

        base_student = twin_snapshot.student_frame
        base_budget = base_student.total_budget_inr
        base_rank = base_student.entrance_rank or 25000
        base_tuition = programme.estimated_total_tuition_inr

        budgets: List[float] = []
        ranks: List[int] = []
        tuitions: List[float] = []

        eligible_affordable_count = 0
        eligible_unaffordable_count = 0
        ineligible_count = 0

        for _ in range(iterations):
            # Stochastic Variations with strict boundary constraints
            b_var = max(0.0, float(rng.gauss(base_budget, base_budget * cfg.budget_std_dev_pct)))
            r_var = max(1, int(round(rng.gauss(base_rank, base_rank * cfg.rank_slip_std_dev_pct))))
            inflation = max(-0.02, float(rng.gauss(cfg.tuition_inflation_mean_pct, 0.04)))
            t_var = max(0.0, float(base_tuition * (1.0 + inflation)))

            budgets.append(b_var)
            ranks.append(r_var)
            tuitions.append(t_var)

            # Evaluate sample
            s_sample = deepcopy(base_student)
            s_sample.total_budget_inr = b_var
            s_sample.entrance_rank = r_var

            p_sample = deepcopy(programme)
            p_sample.estimated_total_tuition_inr = t_var

            trace = self.rule_engine.evaluate(
                s_sample, p_sample, frame_registry=self.programme_service.frame_registry
            )
            is_elig = trace.final_status == EligibilityStatus.ELIGIBLE
            is_afford = b_var >= t_var

            if is_elig and is_afford:
                eligible_affordable_count += 1
            elif is_elig and not is_afford:
                eligible_unaffordable_count += 1
            else:
                ineligible_count += 1

        # Summary Metrics
        def calc_metric(name: str, values: List[float]) -> DistributionMetric:
            sorted_v = sorted(values)
            n = len(sorted_v)
            if n == 0:
                return DistributionMetric(name, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

            # True empirical percentiles with monotonicity guarantee: p10 <= p50 <= p90
            idx_10 = max(0, min(n - 1, int(math.ceil(0.10 * n)) - 1))
            idx_50 = max(0, min(n - 1, int(math.ceil(0.50 * n)) - 1))
            idx_90 = max(0, min(n - 1, int(math.ceil(0.90 * n)) - 1))

            p10 = sorted_v[idx_10]
            p50 = sorted_v[idx_50]
            p90 = sorted_v[idx_90]

            # Monotonic ordering guarantee
            p50 = max(p10, p50)
            p90 = max(p50, p90)

            return DistributionMetric(
                variable_name=name,
                mean=sum(sorted_v) / n,
                median=p50,
                p10=p10,
                p50=p50,
                p90=p90,
                min_val=sorted_v[0],
                max_val=sorted_v[-1],
            )

        metrics = {
            "budget_inr": calc_metric("Budget (INR)", budgets),
            "entrance_rank": calc_metric("Entrance Rank", [float(r) for r in ranks]),
            "tuition_inr": calc_metric("Total Tuition (INR)", tuitions),
        }

        outcome_freqs = {
            "eligible_and_affordable": round(eligible_affordable_count / iterations, 3),
            "eligible_unaffordable": round(eligible_unaffordable_count / iterations, 3),
            "ineligible": round(ineligible_count / iterations, 3),
        }

        scenario_def = ScenarioDefinition(
            scenario_id=f"SCEN_MC_{sim_id[-6:]}",
            scenario_type=ScenarioType.MONTE_CARLO_MULTIVARIATE,
            base_snapshot_id=twin_snapshot.snapshot_id,
            changed_variables={"iterations": iterations, "seed": cfg.seed},
            original_values={
                "base_budget_inr": base_budget,
                "base_entrance_rank": base_rank,
                "base_tuition_inr": base_tuition,
            },
            hypothetical_values=outcome_freqs,
            assumptions=[
                f"Reproducible stochastic Monte Carlo across {iterations} iterations with random seed {cfg.seed}.",
                f"Hypothetical Gaussian demonstration model: Budget sigma={cfg.budget_std_dev_pct*100:.0f}%, Rank sigma={cfg.rank_slip_std_dev_pct*100:.0f}%.",
                "Explicit Boundary Enforcement: All sampled ranks >= 1 (positive integers), budgets >= 0 INR, tuitions >= 0 INR.",
                "Parameters are hypothetical demonstration assumptions, NOT fitted empirical observations from universities.",
            ],
            is_hypothetical=True,
            random_seed=cfg.seed,
        )

        delta_summary = (
            f"Monte Carlo ({iterations} iterations): {outcome_freqs['eligible_and_affordable'] * 100:.1f}% eligible & affordable, "
            f"{outcome_freqs['eligible_unaffordable'] * 100:.1f}% eligible but tuition exceeded budget, "
            f"{outcome_freqs['ineligible'] * 100:.1f}% prerequisite violated."
        )

        return SimulationResult(
            simulation_id=sim_id,
            snapshot_id=twin_snapshot.snapshot_id,
            target_programme_id=programme.programme_id,
            scenario=scenario_def,
            baseline_eligible=base_student.total_budget_inr >= programme.estimated_total_tuition_inr,
            baseline_affordable=base_student.total_budget_inr >= programme.estimated_total_tuition_inr,
            scenario_eligible=outcome_freqs["eligible_and_affordable"] > 0.5,
            scenario_affordable=outcome_freqs["eligible_and_affordable"] > 0.5,
            eligibility_changed=False,
            affordability_changed=False,
            monte_carlo_metrics=metrics,
            monte_carlo_outcome_frequencies=outcome_freqs,
            delta_summary=delta_summary,
            warnings=[
                "SIMULATION DISCLAIMER: Monte Carlo outcome frequencies reflect statistical parameter modeling and are NOT admission guarantees or real-world probabilities."
            ],
            executed_at=now_utc,
        )

    @staticmethod
    def validate_covariance_matrix(matrix: List[List[float]]) -> Tuple[bool, str]:
        """Validates that a covariance matrix is dimensionally square, symmetric, finite,
        and positive semi-definite (PSD).

        Checks:
        1. Non-empty square dimension (N x N).
        2. Finite elements (no NaN, no Inf).
        3. Symmetry: Cov(X, Y) == Cov(Y, X).
        4. Positive semi-definiteness: lambda_min >= -1e-8.

        Returns (True, explanation) if valid, or (False, error_reason) if degenerate,
        asymmetric, non-finite, or containing negative eigenvalues.
        """
        import numpy as np

        if not matrix or not isinstance(matrix, list) or len(matrix) == 0:
            return False, "Matrix must be a non-empty list of lists."

        n_rows = len(matrix)
        for row in matrix:
            if not isinstance(row, list) or len(row) != n_rows:
                return False, f"Matrix is not square: expected {n_rows} columns, got {len(row) if isinstance(row, list) else 'non-list'}."

        try:
            arr = np.array(matrix, dtype=float)
        except (ValueError, TypeError) as e:
            return False, f"Matrix elements cannot be parsed as floats: {e}"

        # Check finiteness (no NaN or Inf)
        if not np.all(np.isfinite(arr)):
            return False, "Matrix contains non-finite values (NaN or Inf)."

        # Check symmetry
        if not np.allclose(arr, arr.T, atol=1e-8):
            return False, "Matrix is asymmetric: Cov(X, Y) != Cov(Y, X)."

        # Check positive semi-definiteness via eigenvalues
        eigenvalues = np.linalg.eigvalsh(arr)
        min_eig = float(np.min(eigenvalues))
        if min_eig < -1e-8:
            return False, f"Matrix is not positive semi-definite (minimum eigenvalue: {min_eig:.6f} < 0)."

        return True, "Matrix is valid symmetric positive semi-definite."

