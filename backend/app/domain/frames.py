"""Domain frames for Hydra academic decision-support.

Pure Python dataclasses without external framework dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EligibilityStatus(str, Enum):
    """The Hydra three-state eligibility outcome."""

    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class SubjectScore:
    """An academic subject score in a student transcript."""

    subject_code: str
    subject_name: str
    score: float
    max_score: float = 100.0
    grading_scale: str = "percentage"  # "percentage", "cbse_10_point", etc.

    @property
    def normalized_percentage(self) -> Optional[float]:
        """Calculates normalized percentage if grading scale is standard percentage or ratio."""
        if self.grading_scale == "percentage" and self.max_score > 0:
            return (self.score / self.max_score) * 100.0
        return None


@dataclass
class StudentFrame:
    """Domain frame representing the student profile."""

    student_id: Optional[str] = None
    subject_scores: List[SubjectScore] = field(default_factory=list)
    entrance_exam_name: Optional[str] = None
    entrance_rank: Optional[int] = None
    preferred_locations: List[str] = field(default_factory=list)
    total_budget_inr: float = 0.0
    preferred_disciplines: List[str] = field(default_factory=list)
    career_goals: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

    def get_subject_score(self, subject_code: str) -> Optional[SubjectScore]:
        """Retrieves score by case-insensitive subject code."""
        code_upper = subject_code.strip().upper()
        for s in self.subject_scores:
            if s.subject_code.strip().upper() == code_upper:
                return s
        return None


@dataclass(frozen=True)
class AcademicPrerequisite:
    """Mandatory or optional subject benchmark prerequisite."""

    subject_code: str
    subject_name: str
    min_score: float
    grading_scale: str = "percentage"
    is_mandatory: bool = True


@dataclass(frozen=True)
class EntrancePrerequisite:
    """Entrance examination requirement or competitive cutoff benchmark."""

    exam_name: str
    max_rank: Optional[int] = None
    is_mandatory: bool = False


@dataclass(frozen=True)
class CertificationPrerequisite:
    """Required external certification, training, or portfolio item."""

    certification_name: str
    is_mandatory: bool = True


@dataclass
class ProgrammeFrame:
    """Domain frame representing an academic programme."""

    programme_id: str
    title: str
    institution_name: str
    location: str
    discipline: str
    academic_prerequisites: List[AcademicPrerequisite] = field(default_factory=list)
    entrance_prerequisites: List[EntrancePrerequisite] = field(default_factory=list)
    certification_prerequisites: List[CertificationPrerequisite] = field(default_factory=list)
    annual_tuition_inr: float = 0.0
    duration_years: int = 4
    estimated_total_tuition_inr: float = 0.0
    currency: str = "INR"
    cost_basis: str = "tuition_only_total"
    skills_developed: List[str] = field(default_factory=list)
    career_paths: List[str] = field(default_factory=list)
    parent_frame_id: Optional[str] = None
    requirement_expression: Optional[Any] = None
    is_synthetic: bool = True
    dataset_label: str = "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"
    provenance: str = "SYNTHETIC_DEMO_RECORD_V1"

    def __post_init__(self) -> None:
        if self.estimated_total_tuition_inr == 0.0 and self.annual_tuition_inr > 0:
            self.estimated_total_tuition_inr = self.annual_tuition_inr * self.duration_years

