"""Evaluation orchestration service for Hydra recommendations.

Coordinates domain frames, rule evaluations, graph traversal, affordability, and preference fit.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.domain.frames import EligibilityStatus, ProgrammeFrame, StudentFrame
from app.knowledge.graph import DiscoveredRelationship
from app.rules.engine import InferenceTrace, RuleEngine
from app.services.programme_service import ProgrammeService


@dataclass(frozen=True)
class AffordabilityResult:
    """Independent affordability evaluation."""

    is_affordable: bool
    total_budget_inr: float
    estimated_total_tuition_inr: float
    currency: str = "INR"
    cost_basis: str = "tuition_only_total"


@dataclass(frozen=True)
class PreferenceFitResult:
    """Independent preference fit score and criteria breakdown."""

    fit_score: float  # Bounded strictly [0.0, 1.0]
    criteria_breakdown: Dict[str, float]
    notes: str


@dataclass
class SingleEvaluationResult:
    """Complete evaluation bundle for a single academic programme."""

    programme: ProgrammeFrame
    trace: InferenceTrace
    affordability: AffordabilityResult
    preference_fit: PreferenceFitResult
    discovered_relationships: List[DiscoveredRelationship] = field(default_factory=list)


@dataclass
class EvaluationBundle:
    """Complete response bundle containing all evaluated programmes."""

    evaluations: List[SingleEvaluationResult]
    discovered_relationships: List[DiscoveredRelationship]
    is_synthetic: bool = True
    audit_timestamp: str = ""


class EvaluationService:
    """Service orchestrating student profile evaluations."""

    def __init__(self, programme_service: Optional[ProgrammeService] = None) -> None:
        self.programme_service = programme_service or ProgrammeService()
        self.rule_engine = RuleEngine()

    def evaluate_profile(self, student: StudentFrame) -> EvaluationBundle:
        """Evaluates a student profile against all catalogue programmes with deterministic sorting."""
        programmes = self.programme_service.get_all()
        evaluations: List[SingleEvaluationResult] = []
        all_discovered_relationships: List[DiscoveredRelationship] = []

        for prog in programmes:
            # 1. Rule Evaluation
            trace = self.rule_engine.evaluate(
                student, prog, frame_registry=self.programme_service.frame_registry
            )

            # 2. Independent Affordability Computation
            affordability = self._compute_affordability(student, prog)

            # 3. Independent Preference-Fit Score
            preference_fit = self._compute_preference_fit(student, prog)

            # 4. Genuine Graph Traversal for Pathways (Programme -> Skills -> Careers)
            discovered = self.programme_service.graph.discover_pathways(
                prog.programme_id, max_depth=2
            )
            all_discovered_relationships.extend(discovered)

            evaluations.append(
                SingleEvaluationResult(
                    programme=prog,
                    trace=trace,
                    affordability=affordability,
                    preference_fit=preference_fit,
                    discovered_relationships=discovered,
                )
            )

        # 5. Deterministic Ordering
        evaluations.sort(key=self._sorting_key)

        # 6. Deduplicate aggregated relationships
        unique_relationships: List[DiscoveredRelationship] = []
        seen = set()
        for rel in all_discovered_relationships:
            key = (rel.source, rel.relationship, rel.target)
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)

        # Runtime ISO 8601 UTC timestamp
        audit_timestamp = datetime.now(timezone.utc).isoformat()

        return EvaluationBundle(
            evaluations=evaluations,
            discovered_relationships=unique_relationships,
            is_synthetic=True,
            audit_timestamp=audit_timestamp,
        )

    def _compute_affordability(
        self, student: StudentFrame, programme: ProgrammeFrame
    ) -> AffordabilityResult:
        """Computes affordability independently from eligibility."""
        is_affordable = student.total_budget_inr >= programme.estimated_total_tuition_inr
        return AffordabilityResult(
            is_affordable=is_affordable,
            total_budget_inr=student.total_budget_inr,
            estimated_total_tuition_inr=programme.estimated_total_tuition_inr,
            currency="INR",
            cost_basis="tuition_only_total",
        )

    def _compute_preference_fit(
        self, student: StudentFrame, programme: ProgrammeFrame
    ) -> PreferenceFitResult:
        """Calculates a normalized preference fit score between 0.0 and 1.0.

        Weights:
        - Discipline match: 0.40
        - Career goal match: 0.40
        - Location match: 0.20
        """
        has_any_preferences = bool(
            student.preferred_disciplines
            or student.career_goals
            or student.preferred_locations
        )

        if not has_any_preferences:
            return PreferenceFitResult(
                fit_score=0.50,
                criteria_breakdown={"discipline": 0.5, "career": 0.5, "location": 0.5},
                notes="Neutral baseline fit: no location, discipline, or career preferences were specified.",
            )

        # 1. Discipline Match (weight 0.4)
        discipline_score = 0.0
        if student.preferred_disciplines:
            for disc in student.preferred_disciplines:
                if disc.strip().lower() in programme.discipline.strip().lower():
                    discipline_score = 1.0
                    break

        # 2. Career Match (weight 0.4)
        career_score = 0.0
        if student.career_goals:
            matches = 0
            for goal in student.career_goals:
                goal_norm = goal.strip().lower()
                for prog_career in programme.career_paths:
                    if goal_norm in prog_career.strip().lower() or prog_career.strip().lower() in goal_norm:
                        matches += 1
                        break
            career_score = min(1.0, matches / max(1, len(student.career_goals)))

        # 3. Location Match (weight 0.2)
        location_score = 0.0
        if student.preferred_locations:
            for loc in student.preferred_locations:
                loc_norm = loc.strip().lower()
                if loc_norm in programme.location.strip().lower():
                    location_score = 1.0
                    break

        # Weighted aggregate
        total_score = round(
            (discipline_score * 0.40) + (career_score * 0.40) + (location_score * 0.20), 2
        )
        total_score = max(0.0, min(1.0, total_score))

        notes = (
            f"Discipline match: {discipline_score:.1f}, "
            f"Career match: {career_score:.1f}, "
            f"Location match: {location_score:.1f}"
        )

        return PreferenceFitResult(
            fit_score=total_score,
            criteria_breakdown={
                "discipline": discipline_score,
                "career": career_score,
                "location": location_score,
            },
            notes=notes,
        )

    def _sorting_key(self, result: SingleEvaluationResult) -> tuple:
        """Deterministic sorting key:

        1. Eligibility status: ELIGIBLE (0) > NEEDS_REVIEW (1) > INELIGIBLE (2)
        2. Affordability: is_affordable True (0) > False (1)
        3. Preference fit score: descending (-score)
        4. Programme ID: ascending
        """
        status_priority = {
            EligibilityStatus.ELIGIBLE: 0,
            EligibilityStatus.NEEDS_REVIEW: 1,
            EligibilityStatus.INELIGIBLE: 2,
        }
        return (
            status_priority.get(result.trace.final_status, 3),
            0 if result.affordability.is_affordable else 1,
            -result.preference_fit.fit_score,
            result.programme.programme_id,
        )

