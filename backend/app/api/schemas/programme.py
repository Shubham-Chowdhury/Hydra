"""Pydantic schemas for programme catalogue representations."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AcademicPrerequisiteDto(BaseModel):
    """Academic prerequisite schema."""

    subject_code: str
    subject_name: str
    min_score: float
    grading_scale: str
    is_mandatory: bool


class EntrancePrerequisiteDto(BaseModel):
    """Entrance prerequisite schema."""

    exam_name: str
    max_rank: Optional[int] = None
    is_mandatory: bool


class ProgrammeResponse(BaseModel):
    """Programme catalog item response."""

    programme_id: str
    title: str
    institution_name: str
    location: str
    discipline: str
    annual_tuition_inr: float
    duration_years: int
    estimated_total_tuition_inr: float
    currency: str = "INR"
    cost_basis: str = "tuition_only_total"
    academic_prerequisites: List[AcademicPrerequisiteDto] = Field(default_factory=list)
    entrance_prerequisites: List[EntrancePrerequisiteDto] = Field(default_factory=list)
    skills_developed: List[str] = Field(default_factory=list)
    career_paths: List[str] = Field(default_factory=list)
    is_synthetic: bool = True
    dataset_label: str = "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"
    provenance: str = "SYNTHETIC_DEMO_RECORD_V1"

