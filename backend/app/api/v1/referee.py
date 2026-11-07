"""Central Referee API Router for Hydra (M007).

Provides the master evaluation endpoint synthesizing multi-agent analyses,
resolving inter-agent conflicts, and generating explainable decisions.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.referee import (
    RefereeEvaluateRequest,
    RefereeEvaluationResponse,
)
from app.api.v1.twin import _twin_service
from app.services.referee_service import RefereeService

router = APIRouter(prefix="/referee", tags=["Central Referee"])

_referee_service = RefereeService(twin_service=_twin_service)


def get_referee_service() -> RefereeService:
    return _referee_service


@router.post("/evaluate", response_model=RefereeEvaluationResponse)
def evaluate_student_under_referee(
    request: RefereeEvaluateRequest,
    service: RefereeService = Depends(get_referee_service),
) -> Dict[str, Any]:
    """Executes the complete multi-agent pipeline and synthesizes final recommendations."""
    profile_dict = request.profile.model_dump() if request.profile else None
    try:
        result = service.evaluate(
            profile_data=profile_dict,
            snapshot_id=request.snapshot_id,
            include_auction=request.include_auction,
            include_planning=request.include_planning,
            include_stress_test=request.include_stress_test,
            include_oracle=request.include_oracle,
            interest_narrative=request.interest_narrative,
        )
        return result.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

