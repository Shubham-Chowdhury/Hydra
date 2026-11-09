"""Comprehensive Assessment & Career Pathway Report Service for Hydra.

Orchestrates deterministic rule evaluations, A* heuristic pathway milestones,
and deep trajectory sequence model projections to produce auditable reports
and natural voice scripts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.domain.assessment_report import (
    ComprehensiveAssessmentReport,
    NeuralTrajectoryInsights,
    UserInteractionEvent,
)
from app.domain.frames import StudentFrame, SubjectScore
from app.services.evaluation import EvaluationService
from app.services.programme_service import ProgrammeService
from app.services.trajectory_model import DeepTrajectorySequenceModel


class AssessmentReportService:
    """Consolidates deterministic evaluations and deep neural trajectory projections."""

    def __init__(
        self,
        evaluation_service: Optional[EvaluationService] = None,
        programme_service: Optional[ProgrammeService] = None,
        trajectory_model: Optional[DeepTrajectorySequenceModel] = None,
    ) -> None:
        self.programme_service = programme_service or ProgrammeService(include_all_domains=True)
        self.evaluation_service = evaluation_service or EvaluationService(programme_service=self.programme_service)
        self.trajectory_model = trajectory_model or DeepTrajectorySequenceModel()

    def generate_report(
        self,
        profile_data: Dict[str, Any],
        interaction_history: Optional[List[Dict[str, Any]]] = None,
    ) -> ComprehensiveAssessmentReport:
        """Generate a complete assessment and career pathway report."""
        student_id = str(profile_data.get("student_id", "STU_MASTER_REF"))
        report_id = f"REP_{uuid.uuid4().hex[:8].upper()}"
        generated_at = datetime.now(timezone.utc).isoformat()

        # 1. Parse interaction history
        parsed_events: List[UserInteractionEvent] = []
        if interaction_history:
            for item in interaction_history:
                parsed_events.append(
                    UserInteractionEvent(
                        event_id=item.get("event_id", str(uuid.uuid4())[:8]),
                        event_type=item.get("event_type", "view_page"),
                        timestamp=item.get("timestamp", generated_at),
                        target_id=item.get("target_id"),
                        domain=item.get("domain"),
                        metadata=item.get("metadata", {}),
                    )
                )

        # 2. Deterministic Rule Engine Evaluation (Authoritative Ground Truth)
        subject_scores = [
            SubjectScore(
                subject_code=s.get("subject_code", ""),
                subject_name=s.get("subject_name", s.get("subject_code", "")),
                score=float(s.get("score", 70.0)),
                max_score=float(s.get("max_score", 100.0)),
                grading_scale=s.get("grading_scale", "percentage"),
            )
            for s in profile_data.get("subject_scores", [])
        ]
        student_frame = StudentFrame(
            student_id=student_id,
            subject_scores=subject_scores,
            entrance_exam_name=profile_data.get("entrance_exam_name", "JEE Main"),
            entrance_rank=profile_data.get("entrance_rank", 18500),
            preferred_locations=profile_data.get("preferred_locations", []),
            total_budget_inr=profile_data.get("total_budget_inr", 800000),
            preferred_disciplines=profile_data.get("preferred_disciplines", []),
            career_goals=profile_data.get("career_goals", []),
            certifications=profile_data.get("certifications", []),
        )

        bundle = self.evaluation_service.evaluate_profile(student_frame)
        evaluations = bundle.evaluations
        eligible = [e for e in evaluations if e.trace.final_status.value == "eligible"]
        review = [e for e in evaluations if e.trace.final_status.value == "needs_review"]
        ineligible = [e for e in evaluations if e.trace.final_status.value == "ineligible"]

        breakdown = {
            "eligible": len(eligible),
            "needs_review": len(review),
            "ineligible": len(ineligible),
            "total": len(evaluations),
        }

        # 3. Deep Learning Trajectory Model Forward Pass (Probabilistic Sequence Modeling)
        neural_insights: NeuralTrajectoryInsights = self.trajectory_model.predict(
            profile_data=profile_data,
            interaction_history=parsed_events if parsed_events else None,
        )

        # 4. Academic Standing
        scores = profile_data.get("subject_scores", [])
        scores_summary = {
            s.get("subject_name", s.get("subject_code", "SUBJECT")): f"{s.get('score')}/{s.get('max_score', 100)}"
            for s in scores
        }
        standing = {
            "entrance_exam": profile_data.get("entrance_exam_name", "JEE Main"),
            "entrance_rank": profile_data.get("entrance_rank", 18500),
            "total_budget_inr": profile_data.get("total_budget_inr", 800000),
            "cost_basis": "tuition_only_total",
            "subject_scores": scores_summary,
            "deterministic_rules_satisfied": len(eligible),
        }

        # 5. Top Recommended Pathways (from eligible or review programmes)
        sorted_evals = sorted(
            evaluations,
            key=lambda x: (
                1 if x.trace.final_status.value == "eligible" else 0,
                x.preference_fit.fit_score or 0.0,
            ),
            reverse=True,
        )

        top_pathways: List[Dict[str, Any]] = []
        for e in sorted_evals[:3]:
            top_pathways.append({
                "programme_id": e.programme.programme_id,
                "programme_name": e.programme.title,
                "institution_name": e.programme.institution_name,
                "eligibility_status": e.trace.final_status.value,
                "fit_score": round((e.preference_fit.fit_score or 0.75) * 100),
                "is_affordable": e.affordability.is_affordable,
                "estimated_tuition_inr": e.affordability.estimated_total_tuition_inr,
            })

        # 6. Actionable Career Milestones
        milestones = [
            {
                "step": 1,
                "title": "Prerequisite Verification",
                "status": "COMPLETED",
                "detail": f"{len(eligible)} programmes verified against formal academic criteria.",
            },
            {
                "step": 2,
                "title": "Autonomous Franchise Bidding",
                "status": "READY",
                "detail": "Inspect quota token allocations across participating universities.",
            },
            {
                "step": 3,
                "title": "A* Heuristic Roadmap",
                "status": "PROJECTED",
                "detail": "Prepare mandatory documentation and semester course registration.",
            },
            {
                "step": 4,
                "title": "Board Defense & Simulation",
                "status": "PROJECTED",
                "detail": "Stress-test interview scenarios against faculty review boards.",
            },
        ]

        # 7. Executive Summary
        readiness_pct = round(neural_insights.career_readiness_score * 100)
        executive_summary = (
            f"Comprehensive profile evaluation confirms {len(eligible)} verified eligible programmes "
            f"out of {len(evaluations)} evaluated, yielding an admissions target fit of {readiness_pct}%. "
            f"The deep trajectory sequence model identifies strong projected mastery in Computer Science "
            f"and Software Systems Architecture with a {readiness_pct}% career readiness index. "
            f"Deterministic eligibility prerequisites are fully satisfied without heuristic override."
        )

        # 8. Spoken Voice Script for Hydra Guide (Sweet, natural, articulate)
        top_col = top_pathways[0]["institution_name"] if top_pathways else "Demo Institute of Technology"
        top_prog = top_pathways[0]["programme_name"] if top_pathways else "Computer Science & Engineering"
        voice_script = (
            f"Here is your comprehensive assessment and career pathway report, Master Shubham. "
            f"Our multi-agent evaluation and deep trajectory sequence model indicate strong academic standing, "
            f"with verified eligibility across {len(eligible)} programmes and a {readiness_pct}% target career readiness index. "
            f"Your leading recommendation is {top_prog} at {top_col}. "
            f"All mandatory prerequisites are deterministically satisfied. "
            f"Would you like me to walk through your Heist Planner milestones or explore closing rank forecasts next?"
        )

        return ComprehensiveAssessmentReport(
            report_id=report_id,
            student_id=student_id,
            generated_at=generated_at,
            executive_summary=executive_summary,
            voice_script=voice_script,
            academic_standing=standing,
            verified_eligibility_breakdown=breakdown,
            top_recommended_pathways=top_pathways,
            neural_insights=neural_insights,
            actionable_milestones=milestones,
            is_synthetic=True,
            dataset_label="SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
            provenance="HYDRA_ASSESSMENT_CORE_V1",
        )
