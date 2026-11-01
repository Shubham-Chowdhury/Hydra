"""Student Digital Twin API endpoints (Phase 4)."""

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.student import StudentProfileRequest
from app.api.schemas.twin import StudentTwinResponse, TwinSnapshotDto
from app.services.twin_service import TwinService

router = APIRouter(prefix="/twin", tags=["Twin Agent"])
_twin_service = TwinService()


@router.post("/construct", response_model=StudentTwinResponse)
def construct_student_digital_twin(payload: StudentProfileRequest):
    """Constructs an auditable Student Digital Twin snapshot using symbolic knowledge representation."""
    snapshot = _twin_service.construct_twin(payload)
    dto = TwinSnapshotDto(**snapshot.to_dict())
    return StudentTwinResponse(snapshot=dto)


@router.get("/{twin_id}", response_model=StudentTwinResponse)
def get_student_digital_twin(twin_id: str):
    """Retrieves an existing Student Digital Twin snapshot by its identifier."""
    snapshot = _twin_service.get_snapshot(twin_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student Digital Twin snapshot '{twin_id}' not found.",
        )
    dto = TwinSnapshotDto(**snapshot.to_dict())
    return StudentTwinResponse(snapshot=dto)

