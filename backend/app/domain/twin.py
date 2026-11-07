"""Student Digital Twin Domain Models for Hydra (Phase 4).

Pure Python dataclasses modeling the student digital twin, fact provenance,
grading scale normalization, multidimensional completeness, and immutable snapshots.
"""

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


class FactOriginCategory(str, Enum):
    """Origin category of a fact represented in the Student Digital Twin."""

    USER_PROVIDED = "user_provided"
    DETERMINISTICALLY_DERIVED = "deterministically_derived"
    EXTERNAL_VERIFIED = "external_verified"
    UNKNOWN = "unknown"


class FactValidationStatus(str, Enum):
    """Validation lifecycle and integrity status of a fact."""

    VALID = "valid"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"
    MISSING = "missing"


class CompletenessState(str, Enum):
    """Completeness outcome for the overall Twin and individual dimensions."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    NEEDS_REVIEW = "needs_review"


class GeographicPreferenceType(str, Enum):
    """Explicit geographic preference classification."""

    NOT_PROVIDED = "not_provided"
    PREFERRED_LOCATIONS = "preferred_locations"
    ANYWHERE_IN_INDIA = "anywhere_in_india"


def freeze_value(val: Any) -> Any:
    """Recursively freezes mutable objects (dicts to MappingProxyType, lists/sets to tuples)."""
    if isinstance(val, (dict, MappingProxyType)):
        return MappingProxyType({k: freeze_value(v) for k, v in val.items()})
    if isinstance(val, (list, tuple, set)):
        return tuple(freeze_value(v) for v in val)
    return val


def unfreeze_value(val: Any) -> Any:
    """Recursively converts MappingProxyType and tuples back into standard dicts and lists for JSON/DTO serialization."""
    if isinstance(val, (dict, MappingProxyType)):
        return {k: unfreeze_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [unfreeze_value(v) for v in val]
    return val


# Policy identifier constants for CBSE / grading conversion
CBSE_POLICY_HISTORICAL_CCE = "CBSE_HISTORICAL_CCE_INDICATIVE"
CBSE_POLICY_CCE_9_5_INDICATIVE = "CBSE_CCE_9_5_INDICATIVE"  # Backward-compatible alias


@dataclass(frozen=True)
class AuthorizedConversionPolicy:
    """Server-authorized conversion policy with strict evidentiary and applicability bounds."""

    policy_id: str
    board: str
    applicable_scheme: str
    min_year: Optional[int]
    max_year: Optional[int]
    multiplier: float
    is_indicative: bool
    authority_name: str
    authority_document: str
    description: str
    is_institution_authorized: bool = False


# Server-side authoritative registry of conversion policies
AUTHORIZED_CONVERSION_POLICIES: Dict[str, AuthorizedConversionPolicy] = {
    CBSE_POLICY_HISTORICAL_CCE: AuthorizedConversionPolicy(
        policy_id=CBSE_POLICY_HISTORICAL_CCE,
        board="CBSE",
        applicable_scheme="CCE_CLASS_X",
        min_year=2009,
        max_year=2017,
        multiplier=9.5,
        is_indicative=True,
        authority_name="Central Board of Secondary Education",
        authority_document="CBSE CCE Examination Guidelines & Grading Manual (2009-2017)",
        description=(
            "Indicative equivalence guideline formula (CGPA * 9.5) officially recommended by CBSE specifically "
            "for Class X CCE grading (2009-2017) for explanatory/advisory display. Not an admitting institution's "
            "authorized conversion policy and does NOT automatically satisfy mandatory percentage admission rules."
        ),
        is_institution_authorized=False,
    ),
}


def resolve_authorized_conversion_policy(
    board: Optional[str],
    grading_scale: str,
    examination_year: Optional[int],
    requested_policy_id: Optional[str] = None,
) -> Tuple[Optional[AuthorizedConversionPolicy], str]:
    """Resolves whether a grading scale conversion is authorized on the server.

    Enforces the server-side trust boundary: client input may declare context (board, year,
    requested policy), but the server alone verifies whether an authorized policy applies.
    """
    clean_scale = grading_scale.strip().lower()
    clean_board = board.strip().upper() if board else ""

    if clean_scale in ("cbse_10_point", "cbse_cgpa", "10_point_cgpa"):
        # Check if the student belongs to the historical CBSE CCE Class X scheme (2009-2017)
        if clean_board == "CBSE" and examination_year and (2009 <= examination_year <= 2017):
            policy = AUTHORIZED_CONVERSION_POLICIES[CBSE_POLICY_HISTORICAL_CCE]
            explanation = (
                f"Server-authorized conversion under policy '{policy.policy_id}': verified historical CBSE CCE Class X "
                f"context (examination year {examination_year}). Indicative equivalence formula: CGPA * 9.5. "
                "Notice: This is an indicative equivalence recommendation for explanatory display only, NOT an admitting "
                "institution's authorized percentage conversion policy. Formal percentage-dependent eligibility evaluations "
                "require an applicable institutional policy or manual review (NEEDS_REVIEW)."
            )
            return policy, explanation

        # If client requested an unauthorized policy or student is outside CCE scope (e.g. modern cohort 2026)
        if requested_policy_id:
            explanation = (
                f"Unauthorized policy selection '{requested_policy_id}' rejected. Client input cannot unilaterally authorize "
                "grading scale conversions. Per CBSE Circular dated 30-Nov-2023 (Rule 44 of Examination Bylaws), CBSE does not "
                "declare official percentage formulas. Percentage calculation is determined solely by admitting institutions. "
                "Retained raw CGPA under NEEDS_REVIEW."
            )
            return None, explanation

        # Standard post-CCE / unestablished context
        explanation = (
            "Raw CGPA retained without automated percentage conversion. Per CBSE Circular dated 30-Nov-2023 "
            "(Rule 44 of Examination Bylaws), CBSE does not prescribe an official percentage conversion formula. "
            "Conversion is determined solely by admitting institutions. Manual transcript review required."
        )
        return None, explanation

    return None, f"No authorized server conversion policy for grading scale '{grading_scale}'."


@dataclass(frozen=True)
class CBSEConversionPolicy:
    """Metadata describing an institutional or historical CBSE conversion policy (backward compatibility)."""

    policy_id: str = CBSE_POLICY_HISTORICAL_CCE
    board: str = "CBSE"
    multiplier: float = 9.5
    is_indicative: bool = True
    authority_reference: str = (
        "CBSE Examination Bylaws Rule 44 & Circular 30-Nov-2023 (Calculation of Percentage). "
        "The board does not prescribe an official formula; admitting institutions/employers calculate percentage."
    )


@dataclass(frozen=True)
class FactRecord:
    """A single atomic, auditable fact in the Student Digital Twin with provenance."""

    fact_id: str
    field_name: str
    actual_value: Any
    original_value: Any
    unit_or_scale: Optional[str] = None
    origin_category: FactOriginCategory = FactOriginCategory.USER_PROVIDED
    validation_status: FactValidationStatus = FactValidationStatus.VALID
    explanation: str = ""
    evidence_reference: Optional[str] = None
    input_fact_ids: Sequence[str] = field(default_factory=tuple)
    derivation_rule: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "actual_value", freeze_value(self.actual_value))
        object.__setattr__(self, "original_value", freeze_value(self.original_value))
        object.__setattr__(self, "input_fact_ids", tuple(self.input_fact_ids))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "field_name": self.field_name,
            "actual_value": unfreeze_value(self.actual_value),
            "original_value": unfreeze_value(self.original_value),
            "unit_or_scale": self.unit_or_scale,
            "origin_category": self.origin_category.value,
            "validation_status": self.validation_status.value,
            "explanation": self.explanation,
            "evidence_reference": self.evidence_reference,
            "input_fact_ids": list(self.input_fact_ids),
            "derivation_rule": self.derivation_rule,
        }


@dataclass(frozen=True)
class NormalizedSubjectScore:
    """A subject score with both original and conservatively normalized representations."""

    subject_code: str
    subject_name: str
    original_score: float
    max_score: float
    grading_scale: str
    normalized_percentage: Optional[float] = None
    conversion_status: FactValidationStatus = FactValidationStatus.VALID
    conversion_explanation: str = ""
    board: Optional[str] = None
    conversion_policy_id: Optional[str] = None
    examination_year: Optional[int] = None
    is_indicative: bool = False
    is_institution_authorized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_code": self.subject_code,
            "subject_name": self.subject_name,
            "original_score": self.original_score,
            "max_score": self.max_score,
            "grading_scale": self.grading_scale,
            "normalized_percentage": self.normalized_percentage,
            "conversion_status": self.conversion_status.value,
            "conversion_explanation": self.conversion_explanation,
            "board": self.board,
            "conversion_policy_id": self.conversion_policy_id,
            "examination_year": self.examination_year,
            "is_indicative": self.is_indicative,
            "is_institution_authorized": self.is_institution_authorized,
        }


@dataclass(frozen=True)
class AcademicIdentity:
    """Structured representation of student academic transcript and score-based highlights."""

    subject_scores: Sequence[NormalizedSubjectScore] = field(default_factory=tuple)
    score_based_academic_highlights: Sequence[str] = field(default_factory=tuple)
    highlight_threshold: float = 75.0
    highlight_heuristic_version: str = "1.0"
    missing_subjects: Sequence[str] = field(default_factory=tuple)
    unsupported_grading_scales: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_scores", tuple(self.subject_scores))
        object.__setattr__(self, "score_based_academic_highlights", tuple(self.score_based_academic_highlights))
        object.__setattr__(self, "missing_subjects", tuple(self.missing_subjects))
        object.__setattr__(self, "unsupported_grading_scales", tuple(self.unsupported_grading_scales))

    @property
    def academic_strengths(self) -> List[str]:
        """Backward-compatible alias for score_based_academic_highlights."""
        return list(self.score_based_academic_highlights)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_scores": [s.to_dict() for s in self.subject_scores],
            "score_based_academic_highlights": list(self.score_based_academic_highlights),
            "academic_strengths": list(self.score_based_academic_highlights),
            "highlight_threshold": self.highlight_threshold,
            "highlight_heuristic_version": self.highlight_heuristic_version,
            "missing_subjects": list(self.missing_subjects),
            "unsupported_grading_scales": list(self.unsupported_grading_scales),
        }


@dataclass(frozen=True)
class EntranceExamProfile:
    """Verified entrance examination profile without speculative predictions."""

    exam_name: Optional[str] = None
    rank: Optional[int] = None
    rank_basis: Optional[str] = None
    academic_year: Optional[int] = None
    missing_details: Sequence[str] = field(default_factory=tuple)
    interpretation_notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "missing_details", tuple(self.missing_details))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exam_name": self.exam_name,
            "rank": self.rank,
            "rank_basis": self.rank_basis,
            "academic_year": self.academic_year,
            "missing_details": list(self.missing_details),
            "interpretation_notes": self.interpretation_notes,
        }


@dataclass(frozen=True)
class FinancialConstraints:
    """Explicit financial constraints in INR for total education duration."""

    total_budget_inr: float = 0.0
    currency: str = "INR"
    cost_basis: str = "tuition_only_total"
    is_budget_provided: bool = False
    affordability_readiness: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_budget_inr": self.total_budget_inr,
            "currency": self.currency,
            "cost_basis": self.cost_basis,
            "is_budget_provided": self.is_budget_provided,
            "affordability_readiness": self.affordability_readiness,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class GeographicPreferences:
    """Explicit geographic location preferences without speculative assumptions."""

    preferred_locations: Sequence[str] = field(default_factory=tuple)
    preference_type: GeographicPreferenceType = GeographicPreferenceType.NOT_PROVIDED
    is_unconstrained: bool = True
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "preferred_locations", tuple(self.preferred_locations))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preferred_locations": list(self.preferred_locations),
            "preference_type": self.preference_type.value,
            "is_unconstrained": self.is_unconstrained,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class InterestsAndGoals:
    """Explicit interests and career ambitions with verified graph links."""

    preferred_disciplines: Sequence[str] = field(default_factory=tuple)
    career_goals: Sequence[str] = field(default_factory=tuple)
    certifications: Sequence[str] = field(default_factory=tuple)
    unmapped_interests: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "preferred_disciplines", tuple(self.preferred_disciplines))
        object.__setattr__(self, "career_goals", tuple(self.career_goals))
        object.__setattr__(self, "certifications", tuple(self.certifications))
        object.__setattr__(self, "unmapped_interests", tuple(self.unmapped_interests))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preferred_disciplines": list(self.preferred_disciplines),
            "career_goals": list(self.career_goals),
            "certifications": list(self.certifications),
            "unmapped_interests": list(self.unmapped_interests),
        }


@dataclass(frozen=True)
class DimensionCompleteness:
    """Detailed completeness assessment for a single profile dimension."""

    dimension_name: str
    state: CompletenessState
    available_facts: Sequence[str] = field(default_factory=tuple)
    missing_facts: Sequence[str] = field(default_factory=tuple)
    invalid_facts: Sequence[str] = field(default_factory=tuple)
    review_facts: Sequence[str] = field(default_factory=tuple)
    explanation: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "available_facts", tuple(self.available_facts))
        object.__setattr__(self, "missing_facts", tuple(self.missing_facts))
        object.__setattr__(self, "invalid_facts", tuple(self.invalid_facts))
        object.__setattr__(self, "review_facts", tuple(self.review_facts))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension_name": self.dimension_name,
            "state": self.state.value,
            "available_facts": list(self.available_facts),
            "missing_facts": list(self.missing_facts),
            "invalid_facts": list(self.invalid_facts),
            "review_facts": list(self.review_facts),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class TwinSnapshot:
    """Immutable, versioned snapshot of a constructed Student Digital Twin."""

    twin_id: str
    snapshot_id: str
    student_id: Optional[str]
    student_profile_version: str
    schema_version: str
    created_at: str  # UTC ISO 8601
    profile_fingerprint: str
    overall_completeness: CompletenessState
    completeness_dimensions: Any  # MappingProxyType / Dict[str, DimensionCompleteness]
    academic_identity: AcademicIdentity
    entrance_exam_profile: EntranceExamProfile
    financial_constraints: FinancialConstraints
    geographic_preferences: GeographicPreferences
    interests_and_goals: InterestsAndGoals
    facts: Any  # MappingProxyType / Dict[str, FactRecord]
    semantic_network_pathways: Sequence[Any] = field(default_factory=tuple)
    frame_representation: Any = field(default_factory=dict)
    missing_information: Sequence[str] = field(default_factory=tuple)
    validation_findings: Sequence[str] = field(default_factory=tuple)
    policy_version: str = "1.0.0"

    def __post_init__(self) -> None:
        object.__setattr__(self, "completeness_dimensions", freeze_value(dict(self.completeness_dimensions)))
        object.__setattr__(self, "facts", freeze_value(dict(self.facts)))
        object.__setattr__(self, "semantic_network_pathways", freeze_value(list(self.semantic_network_pathways)))
        object.__setattr__(self, "frame_representation", freeze_value(dict(self.frame_representation)))
        object.__setattr__(self, "missing_information", tuple(self.missing_information))
        object.__setattr__(self, "validation_findings", tuple(self.validation_findings))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "snapshot_id": self.snapshot_id,
            "student_id": self.student_id,
            "student_profile_version": self.student_profile_version,
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "created_at": self.created_at,
            "profile_fingerprint": self.profile_fingerprint,
            "overall_completeness": self.overall_completeness.value,
            "completeness_dimensions": {
                k: v.to_dict() for k, v in self.completeness_dimensions.items()
            },
            "academic_identity": self.academic_identity.to_dict(),
            "entrance_exam_profile": self.entrance_exam_profile.to_dict(),
            "financial_constraints": self.financial_constraints.to_dict(),
            "geographic_preferences": self.geographic_preferences.to_dict(),
            "interests_and_goals": self.interests_and_goals.to_dict(),
            "facts": {k: v.to_dict() for k, v in self.facts.items()},
            "semantic_network_pathways": unfreeze_value(self.semantic_network_pathways),
            "frame_representation": unfreeze_value(self.frame_representation),
            "missing_information": list(self.missing_information),
            "validation_findings": list(self.validation_findings),
        }

    def to_student_frame(self) -> Any:
        """Converts this TwinSnapshot into an authoritative StudentFrame for symbolic rule evaluation."""
        from app.domain.frames import StudentFrame, SubjectScore

        scores = [
            SubjectScore(
                subject_code=s.subject_code,
                subject_name=s.subject_name,
                score=s.original_score,
                max_score=s.max_score,
                grading_scale=s.grading_scale,
            )
            for s in self.academic_identity.subject_scores
        ]

        return StudentFrame(
            student_id=self.student_id,
            subject_scores=scores,
            entrance_exam_name=self.entrance_exam_profile.exam_name,
            entrance_rank=self.entrance_exam_profile.rank,
            preferred_locations=list(self.geographic_preferences.preferred_locations),
            total_budget_inr=self.financial_constraints.total_budget_inr,
            preferred_disciplines=list(self.interests_and_goals.preferred_disciplines),
            career_goals=list(self.interests_and_goals.career_goals),
            certifications=[],
        )

    @property
    def student_frame(self) -> Any:
        """Convenience property returning an authoritative StudentFrame instance."""
        return self.to_student_frame()


def compute_canonical_profile_fingerprint(profile: Any) -> str:
    """Computes deterministic SHA-256 hash of canonicalized profile representation.

    Pure, stateless function without side-effects, frame mutations, or snapshot allocations.
    """
    if hasattr(profile, "model_dump") and callable(profile.model_dump):
        raw = profile.model_dump()
    elif hasattr(profile, "dict") and callable(profile.dict):
        raw = profile.dict()
    elif isinstance(profile, dict):
        raw = profile
    elif hasattr(profile, "__dict__"):
        raw = vars(profile)
    else:
        raise TypeError(f"Unsupported profile payload type for fingerprint calculation: {type(profile).__name__}")

    subj_list = []
    for s in raw.get("subject_scores", []) or []:
        if isinstance(s, dict):
            code = str(s.get("subject_code", "")).strip().upper()
            name = str(s.get("subject_name", "")).strip()
            score = float(s.get("score", 0.0))
            max_s = float(s.get("max_score", 100.0))
            scale = str(s.get("grading_scale", "percentage")).strip().lower()
            board = str(s.get("board", "")).strip().upper() if s.get("board") else None
            policy = str(s.get("conversion_policy_id", "")).strip() if s.get("conversion_policy_id") else None
            year = int(s.get("examination_year")) if s.get("examination_year") else None
        else:
            code = str(getattr(s, "subject_code", "")).strip().upper()
            name = str(getattr(s, "subject_name", "")).strip()
            score = float(getattr(s, "score", 0.0))
            max_s = float(getattr(s, "max_score", 100.0))
            scale = str(getattr(s, "grading_scale", "percentage")).strip().lower()
            board = str(getattr(s, "board", "")).strip().upper() if getattr(s, "board", None) else None
            policy = str(getattr(s, "conversion_policy_id", "")).strip() if getattr(s, "conversion_policy_id", None) else None
            year = int(getattr(s, "examination_year")) if getattr(s, "examination_year", None) else None

        subj_item: Dict[str, Any] = {
            "subject_code": code,
            "subject_name": name,
            "score": round(score, 4),
            "max_score": round(max_s, 4),
            "grading_scale": scale,
        }
        if board:
            subj_item["board"] = board
        if policy:
            subj_item["conversion_policy_id"] = policy
        if year:
            subj_item["examination_year"] = year

        subj_list.append(subj_item)
    subj_list.sort(key=lambda x: x["subject_code"])

    canonical = {
        "academic_year": 2026,
        "career_goals": sorted([str(g).strip() for g in raw.get("career_goals", []) or [] if str(g).strip()]),
        "certifications": sorted([str(c).strip() for c in raw.get("certifications", []) or [] if str(c).strip()]),
        "entrance_exam_name": (str(raw.get("entrance_exam_name")).strip() if raw.get("entrance_exam_name") else None),
        "entrance_rank": (int(raw.get("entrance_rank")) if raw.get("entrance_rank") is not None else None),
        "preferred_disciplines": sorted([str(d).strip() for d in raw.get("preferred_disciplines", []) or [] if str(d).strip()]),
        "preferred_locations": sorted([str(loc).strip() for loc in raw.get("preferred_locations", []) or [] if str(loc).strip()]),
        "student_id": (str(raw.get("student_id")).strip() if raw.get("student_id") else None),
        "subject_scores": subj_list,
        "total_budget_inr": round(float(raw.get("total_budget_inr", 0.0)), 2),
    }
    encoded = json.dumps(canonical, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

