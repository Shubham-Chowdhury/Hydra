"""Franchise Agents and Simulated Auction API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status

from app.agents.twin_agent import TwinAgent
from app.api.schemas.franchise import (
    AuctionRequestDto,
    AuctionResultDto,
    FranchiseInfoDto,
)
from app.api.v1.twin import _twin_service
from app.domain.franchise import ScoringPolicy
from app.services.franchise_service import FranchiseService
from app.services.programme_service import ProgrammeService

router = APIRouter(prefix="/franchises", tags=["Franchise Agents & Auction"])

# Shared service instances
_twin_agent = _twin_service.agent
_prog_service = ProgrammeService(include_all_domains=True)
_franchise_service = FranchiseService(twin_service=_twin_service, programme_service=_prog_service)


@router.get(
    "/programmes",
    response_model=List[FranchiseInfoDto],
    summary="List available Programme Franchise Agents",
)
def get_available_franchises() -> List[FranchiseInfoDto]:
    """Retrieves all active Programme Franchise Agents and catalogue metadata."""
    franchises = _franchise_service.get_available_franchises()
    return [FranchiseInfoDto(**f) for f in franchises]


@router.post(
    "/auction",
    response_model=AuctionResultDto,
    status_code=status.HTTP_200_OK,
    summary="Execute Simulated Programme Auction",
)
def run_programme_auction(request: AuctionRequestDto) -> AuctionResultDto:
    """Runs a deterministic simulated auction of Franchise Agent proposals for a student Twin."""
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
        # Construct ad-hoc Twin from student profile payload
        twin_snapshot = _twin_service.construct_twin(request.profile)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either snapshot_id, twin_id, or student profile payload.",
        )

    # 2. Parse Scoring Policy if provided
    scoring_policy: Optional[ScoringPolicy] = None
    if request.scoring_policy:
        try:
            scoring_policy = ScoringPolicy(
                policy_version=request.scoring_policy.policy_version,
                weight_discipline=request.scoring_policy.weight_discipline,
                weight_career=request.scoring_policy.weight_career,
                weight_academic=request.scoring_policy.weight_academic,
                weight_geographic=request.scoring_policy.weight_geographic,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid scoring policy: {str(e)}",
            )

    # 3. Execute Auction
    try:
        auction_result = _franchise_service.evaluate_and_run_auction(
            twin_snapshot=twin_snapshot,
            programme_ids=request.programme_ids,
            scoring_policy=scoring_policy,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return AuctionResultDto(**auction_result.to_dict())
