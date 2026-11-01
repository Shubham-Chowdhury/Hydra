"""Pydantic schemas for student profile inputs."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SubjectScoreDto(BaseModel):
    """Subject score boundary schema."""

    subject_code: str = Field(..., min_length=1, max_length=20, description="Subject code (e.g. MATH, PHYS, ENG)")
    subject_name: str = Field(..., min_length=1, max_length=100, description="Full subject name")
    score: float = Field(..., ge=0.0, description="Observed score value")
    max_score: float = Field(default=100.0, gt=0.0, description="Maximum possible score")
    grading_scale: str = Field(default="percentage", description="Grading scale type, e.g. percentage, cbse_10_point")

    @field_validator("subject_code")
    @classmethod
    def clean_subject_code(cls, v: str) -> str:
        return v.strip().upper()


class StudentProfileRequest(BaseModel):
    """Request payload for student evaluation."""

    student_id: Optional[str] = Field(default=None, description="Optional anonymous student identifier")
    subject_scores: List[SubjectScoreDto] = Field(default_factory=list, description="Academic subject scores")
    entrance_exam_name: Optional[str] = Field(default=None, description="Entrance exam taken (e.g. JEE Main, MHT-CET)")
    entrance_rank: Optional[int] = Field(default=None, ge=1, description="Rank achieved in entrance exam")
    preferred_locations: List[str] = Field(default_factory=list, description="Preferred Indian states/cities")
    total_budget_inr: float = Field(default=0.0, ge=0.0, description="Total education budget in INR for full programme")
    preferred_disciplines: List[str] = Field(default_factory=list, description="Preferred academic disciplines")
    career_goals: List[str] = Field(default_factory=list, description="Target career ambitions")
    certifications: List[str] = Field(default_factory=list, description="Completed certifications or trainings")

