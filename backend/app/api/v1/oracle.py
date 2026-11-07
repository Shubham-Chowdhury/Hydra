"""Oracle Agent API Router for Hydra (M005).

Provides endpoints for auditing admissions data readiness, querying registered
forecasting models, and generating advisory cutoff forecasts with uncertainty intervals.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends

from app.api.schemas.oracle import (
    CutoffForecastResponse,
    ForecastTargetRequest,
    OracleStatusResponse,
)
from app.domain.oracle import ForecastTarget
from app.services.oracle_service import OracleService

router = APIRouter(prefix="/oracle", tags=["Oracle Forecasting"])


def get_oracle_service() -> OracleService:
    return OracleService()


@router.get("/status", response_model=OracleStatusResponse)
def get_oracle_status(
    service: OracleService = Depends(get_oracle_service),
) -> Dict[str, Any]:
    """Returns the operational status and data readiness diagnostic of the Oracle subsystem."""
    return service.get_status()


@router.get("/models")
def list_oracle_models(
    service: OracleService = Depends(get_oracle_service),
) -> List[Dict[str, Any]]:
    """Returns the list of registered cutoff forecasting and baseline models."""
    return service.list_models()


@router.post("/forecast", response_model=CutoffForecastResponse)
def generate_cutoff_forecast(
    request: ForecastTargetRequest,
    service: OracleService = Depends(get_oracle_service),
) -> Dict[str, Any]:
    """Generates an advisory cutoff forecast with uncertainty intervals for the given target query."""
    target = ForecastTarget(
        institution_id=request.institution_id,
        programme_id=request.programme_id,
        future_academic_year=request.future_academic_year,
        counselling_round=request.counselling_round,
        exam_name=request.exam_name,
        seat_type=request.seat_type,
        quota=request.quota,
        gender_pool=request.gender_pool,
        rank_basis=request.rank_basis,
        target_type=request.target_type,
    )
    forecast = service.forecast(target)
    return forecast.to_dict()

