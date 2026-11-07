"""Simulation and Boss-Fight API router (M004)."""

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.simulation import (
    BossFightReportDto,
    BossFightRequestDto,
    SimulationRequestDto,
    SimulationResultDto,
)
from app.api.v1.twin import _twin_service
from app.domain.simulation import MonteCarloConfig, ScenarioType
from app.services.programme_service import ProgrammeService
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation & Boss-Fight"])

_prog_service = ProgrammeService(include_all_domains=True)
_simulation_service = SimulationService(twin_service=_twin_service, programme_service=_prog_service)


@router.post(
    "/run",
    response_model=SimulationResultDto,
    status_code=status.HTTP_200_OK,
    summary="Run Counterfactual Scenario or Monte Carlo Simulation",
)
def run_simulation(request: SimulationRequestDto) -> SimulationResultDto:
    """Executes an isolated counterfactual perturbation or stochastic Monte Carlo simulation."""
    twin_snapshot = None

    if request.snapshot_id:
        twin_snapshot = _twin_service.get_snapshot(request.snapshot_id)
        if not twin_snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Twin snapshot '{request.snapshot_id}' not found in active session cache.",
            )
    elif request.twin_id:
        twin_snapshot = _twin_service.get_twin(request.twin_id)
        if not twin_snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student Twin '{request.twin_id}' not found in active session cache.",
            )
    elif request.profile:
        twin_snapshot = _twin_service.construct_twin(request.profile)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either snapshot_id, twin_id, or student profile payload.",
        )

    try:
        scenario_type = ScenarioType(request.scenario_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid scenario_type '{request.scenario_type}'.",
        )

    mc_config = None
    if request.monte_carlo_config:
        mc_config = MonteCarloConfig(
            iterations=request.monte_carlo_config.iterations,
            seed=request.monte_carlo_config.seed,
            budget_std_dev_pct=request.monte_carlo_config.budget_std_dev_pct,
            rank_slip_std_dev_pct=request.monte_carlo_config.rank_slip_std_dev_pct,
            tuition_inflation_mean_pct=request.monte_carlo_config.tuition_inflation_mean_pct,
        )

    try:
        result = _simulation_service.run_simulation(
            twin_snapshot=twin_snapshot,
            programme_id=request.target_programme_id,
            scenario_type=scenario_type,
            parameters=request.parameters,
            monte_carlo_config=mc_config,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return SimulationResultDto(**result.to_dict())


@router.post(
    "/stress-test",
    response_model=BossFightReportDto,
    status_code=status.HTTP_200_OK,
    summary="Execute Boss-Fight Adversarial Stress Test",
)
def run_boss_fight_stress_test(request: BossFightRequestDto) -> BossFightReportDto:
    """Attacks applicant proposals with adversarial stressors to evaluate fragility."""
    twin_snapshot = None

    if request.snapshot_id:
        twin_snapshot = _twin_service.get_snapshot(request.snapshot_id)
        if not twin_snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Twin snapshot '{request.snapshot_id}' not found in active session cache.",
            )
    elif request.twin_id:
        twin_snapshot = _twin_service.get_twin(request.twin_id)
        if not twin_snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student Twin '{request.twin_id}' not found in active session cache.",
            )
    elif request.profile:
        twin_snapshot = _twin_service.construct_twin(request.profile)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either snapshot_id, twin_id, or student profile payload.",
        )

    try:
        report = _simulation_service.run_stress_test(
            twin_snapshot=twin_snapshot,
            programme_id=request.target_programme_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return BossFightReportDto(**report.to_dict())

