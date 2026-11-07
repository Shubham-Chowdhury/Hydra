"""Heist Planner API router (A* Search)."""

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.planner import PlanningRequestDto, PlanningResultDto
from app.api.v1.twin import _twin_service
from app.services.planner_service import PlannerService
from app.services.programme_service import ProgrammeService

router = APIRouter(prefix="/planner", tags=["Heist Planner (A* Search)"])

_prog_service = ProgrammeService(include_all_domains=True)
_planner_service = PlannerService(twin_service=_twin_service, programme_service=_prog_service)


@router.post(
    "/plan",
    response_model=PlanningResultDto,
    status_code=status.HTTP_200_OK,
    summary="Execute A* Pathway Planning toward Target Programme",
)
def plan_programme_pathway(request: PlanningRequestDto) -> PlanningResultDto:
    """Finds an optimal sequence of verifiable student actions to satisfy target programme prerequisites."""
    twin_snapshot = None

    # 1. Resolve Twin Snapshot
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

    # 2. Execute A* Planning
    try:
        result = _planner_service.generate_plan(
            twin_snapshot=twin_snapshot,
            programme_id=request.target_programme_id,
            use_heuristic=request.use_heuristic,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return PlanningResultDto(**result.to_dict())

