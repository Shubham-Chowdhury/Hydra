"""Interest Decoder API Router for Hydra (M006).

Provides endpoints for decoding natural-language student interest text,
retrieving embedding model diagnostic status, and confirming candidate concepts.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.interest import (
    ConfirmInterestRequest,
    ConfirmedInterestResponse,
    DecodeInterestRequest,
    InterestDecodingResponse,
    InterestModelStatusResponse,
)
from app.services.interest_service import InterestService

router = APIRouter(prefix="/interests", tags=["Interest Decoder"])


def get_interest_service() -> InterestService:
    return InterestService()


@router.get("/model-status", response_model=InterestModelStatusResponse)
def get_interest_model_status(
    service: InterestService = Depends(get_interest_service),
) -> Dict[str, Any]:
    """Returns the operational status, architecture, and taxonomy of the embedding engine."""
    return service.get_status()


@router.post("/decode", response_model=InterestDecodingResponse)
def decode_student_interests(
    request: DecodeInterestRequest,
    service: InterestService = Depends(get_interest_service),
) -> Dict[str, Any]:
    """Translates free-text student interests into ranked canonical concepts with cosine similarities."""
    try:
        result = service.decode_interests(request.interest_text)
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/confirm", response_model=ConfirmedInterestResponse)
def confirm_candidate_interest(
    request: ConfirmInterestRequest,
    service: InterestService = Depends(get_interest_service),
) -> Dict[str, Any]:
    """Explicitly accepts a candidate concept into USER_CONFIRMED status."""
    try:
        confirmed = service.confirm_interest(request.concept_id, request.similarity_score)
        return confirmed.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

