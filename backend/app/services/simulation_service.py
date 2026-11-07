"""Simulation and Boss-Fight application service for Hydra."""

from typing import Any, Dict, Optional

from app.agents.boss_fight import BossFightAgent
from app.agents.simulator import SimulatorAgent
from app.domain.simulation import (
    BossFightReport,
    MonteCarloConfig,
    ScenarioType,
    SimulationResult,
)
from app.domain.twin import TwinSnapshot
from app.services.programme_service import ProgrammeService
from app.services.twin_service import TwinService


class SimulationService:
    """Service orchestrating counterfactual scenario simulations, Monte Carlo modeling, and Boss-Fight stress tests."""

    def __init__(
        self,
        programme_service: Optional[ProgrammeService] = None,
        twin_service: Optional[TwinService] = None,
        simulator_agent: Optional[SimulatorAgent] = None,
        boss_fight_agent: Optional[BossFightAgent] = None,
    ) -> None:
        self.programme_service = programme_service or ProgrammeService()
        self.twin_service = twin_service or TwinService()
        self.simulator_agent = simulator_agent or SimulatorAgent(
            programme_service=self.programme_service
        )
        self.boss_fight_agent = boss_fight_agent or BossFightAgent(
            programme_service=self.programme_service
        )

    def run_simulation(
        self,
        twin_snapshot: TwinSnapshot,
        programme_id: str,
        scenario_type: ScenarioType,
        parameters: Optional[Dict[str, Any]] = None,
        monte_carlo_config: Optional[MonteCarloConfig] = None,
    ) -> SimulationResult:
        """Executes either deterministic counterfactual or Monte Carlo simulation."""
        if scenario_type == ScenarioType.MONTE_CARLO_MULTIVARIATE:
            return self.simulator_agent.run_monte_carlo(
                twin_snapshot=twin_snapshot,
                programme_id=programme_id,
                config=monte_carlo_config,
            )
        return self.simulator_agent.run_deterministic_scenario(
            twin_snapshot=twin_snapshot,
            programme_id=programme_id,
            scenario_type=scenario_type,
            parameters=parameters,
        )

    def run_stress_test(
        self,
        twin_snapshot: TwinSnapshot,
        programme_id: str,
    ) -> BossFightReport:
        """Executes adversarial Boss-Fight battery against a programme."""
        return self.boss_fight_agent.stress_test(
            twin_snapshot=twin_snapshot,
            target_programme_id=programme_id,
        )

