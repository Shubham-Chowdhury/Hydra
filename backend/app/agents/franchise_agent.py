"""Franchise Agent and Factory for Hydra.

Each Franchise Agent evaluates a specific student Twin against a single academic
programme using Hydra's symbolic AST rule engine, independent affordability evaluation,
and multi-dimensional preference alignment.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.domain.frames import EligibilityStatus, ProgrammeFrame
from app.domain.franchise import (
    AlignmentScores,
    ProgrammeBid,
    ProposalStatus,
    ScoringPolicy,
)
from app.domain.frame_system import FrameRegistry
from app.domain.twin import TwinSnapshot
from app.rules.engine import (
    InferenceTrace,
    ReasoningTreeNode,
    RuleEngine,
    RuleStatus,
)


def _serialize_reasoning_tree(node: Optional[ReasoningTreeNode]) -> Optional[Dict[str, Any]]:
    """Recursively serializes a ReasoningTreeNode to a plain dictionary."""
    if node is None:
        return None
    return {
        "node_id": node.node_id,
        "expression_type": node.expression_type,
        "status": node.status.value,
        "is_mandatory": node.is_mandatory,
        "expected_value": node.expected_value,
        "observed_value": node.observed_value,
        "facts_used": node.facts_used,
        "evidence": list(node.evidence),
        "missing_facts": list(node.missing_facts),
        "explanation": node.explanation,
        "provenance": node.provenance,
        "children": [
            _serialize_reasoning_tree(c) for c in node.children if c is not None
        ],
    }


class FranchiseAgent:
    """Specialized intelligent agent evaluating a student Twin for a single academic programme."""

    def __init__(
        self,
        programme: ProgrammeFrame,
        frame_registry: Optional[FrameRegistry] = None,
        scoring_policy: Optional[ScoringPolicy] = None,
        rule_engine: Optional[RuleEngine] = None,
    ) -> None:
        if not isinstance(programme, ProgrammeFrame):
            raise TypeError("programme must be a valid ProgrammeFrame instance")
        self.programme = programme
        self.frame_registry = frame_registry or FrameRegistry()
        self.scoring_policy = scoring_policy or ScoringPolicy()
        self.rule_engine = rule_engine or RuleEngine()
        self.agent_id = f"AGENT_FRANCHISE_{programme.programme_id}"

    def evaluate(self, twin_snapshot: TwinSnapshot) -> ProgrammeBid:
        """Evaluates a student Twin against this programme and produces an immutable ProgrammeBid."""
        if not isinstance(twin_snapshot, TwinSnapshot):
            raise TypeError("twin_snapshot must be a valid TwinSnapshot instance")

        now_utc = datetime.now(timezone.utc).isoformat()
        student_frame = twin_snapshot.student_frame

        # 1. Deterministic Rule Evaluation using existing symbolic RuleEngine
        trace: InferenceTrace = self.rule_engine.evaluate(
            student_frame, self.programme, frame_registry=self.frame_registry
        )

        # 2. Independent Affordability Check
        affordability_status = (
            student_frame.total_budget_inr
            >= self.programme.estimated_total_tuition_inr
        )

        # 3. Preference and Alignment Scoring
        alignment = self._compute_alignment(student_frame)

        # 4. Determine Proposal Qualification State
        warnings: List[str] = []
        if trace.final_status == EligibilityStatus.INELIGIBLE:
            proposal_status = ProposalStatus.NO_BID
            failed_rules = [
                f"{r.rule_id}: {r.explanation}"
                for r in trace.rules_evaluated
                if r.status == RuleStatus.VIOLATED
            ]
            warnings.append(
                f"Candidate does not meet mandatory prerequisites: {'; '.join(failed_rules) if failed_rules else 'Ineligible'}"
            )
        elif trace.final_status == EligibilityStatus.NEEDS_REVIEW:
            proposal_status = ProposalStatus.CONDITIONAL_CANDIDATE
            warnings.append(
                f"Evaluation conditional on missing facts or review: {', '.join(trace.missing_facts) if trace.missing_facts else 'Verification required'}"
            )
        else:
            proposal_status = ProposalStatus.UNCONDITIONAL_CANDIDATE

        # Affordability warning (does NOT change eligibility status)
        if not affordability_status:
            warnings.append(
                f"Total programme tuition (INR {self.programme.estimated_total_tuition_inr:,.0f}) "
                f"exceeds stated budget (INR {student_frame.total_budget_inr:,.0f})."
            )

        if alignment.is_unscored:
            warnings.append(
                "Profile has no preference or academic constraint evidence (0/4 dimensions provided). "
                "This proposal is UNSCORED (composite preference score is None) and provided for exploratory browsing only."
            )
        elif alignment.is_insufficient_evidence:
            score_str = f"{alignment.composite_score:.2f}" if alignment.composite_score is not None else "N/A"
            warnings.append(
                f"Profile has insufficient preference evidence: only {len(alignment.active_dimensions)}/4 dimensions "
                f"({', '.join(alignment.active_dimensions)}) provided "
                f"(coverage: {alignment.evidence_coverage_ratio * 100:.0f}%). "
                f"Composite score ({score_str}) is an exploratory signal only and must not be interpreted as a comprehensive assessment."
            )

        # 5. Extract Evidence References from twin facts and rule trace
        evidence_refs: List[str] = list(trace.evidence)
        for rr in trace.rules_evaluated:
            evidence_refs.append(f"RULE:{rr.rule_id}")
            for fact_key in rr.facts_used.keys():
                ref = f"FACT:{fact_key}"
                if ref not in evidence_refs:
                    evidence_refs.append(ref)

        # Unique bid ID combining programme and snapshot identity
        bid_id = f"BID_{self.programme.programme_id}_{twin_snapshot.snapshot_id[:20]}"

        return ProgrammeBid(
            bid_id=bid_id,
            agent_id=self.agent_id,
            programme_id=self.programme.programme_id,
            programme_title=self.programme.title,
            institution_name=self.programme.institution_name,
            twin_id=twin_snapshot.twin_id,
            snapshot_id=twin_snapshot.snapshot_id,
            eligibility_status=trace.final_status,
            affordability_status=affordability_status,
            total_budget_inr=student_frame.total_budget_inr,
            estimated_total_tuition_inr=self.programme.estimated_total_tuition_inr,
            academic_alignment=alignment.academic_alignment,
            discipline_alignment=alignment.discipline_alignment,
            career_alignment=alignment.career_alignment,
            geographic_alignment=alignment.geographic_alignment,
            composite_preference_score=alignment.composite_score,
            evidence_coverage_ratio=alignment.evidence_coverage_ratio,
            active_dimensions=alignment.active_dimensions,
            is_insufficient_evidence=alignment.is_insufficient_evidence,
            evidence_tier=alignment.evidence_tier,
            is_unscored=alignment.is_unscored,
            neutral_baseline_display=alignment.neutral_baseline_display,
            proposal_status=proposal_status,
            policy_version=self.scoring_policy.policy_version,
            evidence_references=evidence_refs,
            missing_facts=trace.missing_facts,
            warnings=warnings,
            reasoning_trace={
                "rules_evaluated": [
                    {
                        "rule_id": rr.rule_id,
                        "rule_name": rr.rule_name,
                        "status": rr.status.value,
                        "explanation": rr.explanation,
                        "is_mandatory": rr.is_mandatory,
                        "facts_used": rr.facts_used,
                    }
                    for rr in trace.rules_evaluated
                ],
                "missing_facts": trace.missing_facts,
                "final_status": trace.final_status.value,
                "summary_explanation": trace.summary_explanation,
                "reasoning_tree": _serialize_reasoning_tree(trace.reasoning_tree),
            },
            created_at=now_utc,
            currency="INR",
            cost_basis="tuition_only_total",
            is_synthetic=getattr(self.programme, "is_synthetic", True),
            dataset_label=getattr(
                self.programme,
                "dataset_label",
                "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
            ),
        )

    def _compute_alignment(self, student: Any) -> AlignmentScores:
        """Computes multi-dimensional alignment scores [0.0, 1.0].

        Dynamically renormalizes heuristic weights across present dimensions when
        optional profile fields are omitted, preventing silent zero-penalties.
        Filters out UNKNOWN, empty, or uninformative values so only genuine evidence
        contributes to active weights.
        """
        active_weights: Dict[str, float] = {}
        uninformative = {
            "unknown",
            "not_provided",
            "none",
            "null",
            "undefined",
            "n/a",
            "",
        }

        # 1. Discipline Alignment
        raw_disc = [
            d.strip()
            for d in (getattr(student, "preferred_disciplines", None) or [])
            if d and str(d).strip().lower() not in uninformative
        ]
        if not raw_disc:
            discipline_score = 0.50
        else:
            prog_disc = self.programme.discipline.strip().lower()
            match = any(
                d.lower() in prog_disc or prog_disc in d.lower()
                for d in raw_disc
            )
            discipline_score = 1.0 if match else 0.0
            active_weights["discipline"] = self.scoring_policy.weight_discipline

        # 2. Career Alignment
        raw_careers = [
            c.strip()
            for c in (getattr(student, "career_goals", None) or [])
            if c and str(c).strip().lower() not in uninformative
        ]
        if not raw_careers:
            career_score = 0.50
        else:
            matches = 0
            prog_careers = [
                c.strip().lower()
                for c in getattr(self.programme, "career_paths", [])
            ]
            for goal in raw_careers:
                g_norm = goal.lower()
                if any(g_norm in pc or pc in g_norm for pc in prog_careers):
                    matches += 1
            career_score = min(1.0, matches / max(1, len(raw_careers)))
            active_weights["career"] = self.scoring_policy.weight_career

        # 3. Geographic Alignment
        raw_locs = [
            l.strip()
            for l in (getattr(student, "preferred_locations", None) or [])
            if l
            and str(l).strip().lower()
            not in uninformative.union({"anywhere", "anywhere in india"})
        ]
        if not raw_locs:
            geo_score = 1.0  # Unconstrained (neutral)
        else:
            prog_loc = self.programme.location.strip().lower()
            match = any(
                l.lower() in prog_loc or prog_loc in l.lower()
                for l in raw_locs
            )
            geo_score = 1.0 if match else 0.0
            active_weights["geographic"] = self.scoring_policy.weight_geographic

        # 4. Academic Alignment
        academic_score = 0.50
        has_academic_evidence = False
        if self.programme.academic_prerequisites:
            ratios: List[float] = []
            for prereq in self.programme.academic_prerequisites:
                sub = student.get_subject_score(prereq.subject_code)
                if (
                    sub
                    and sub.normalized_percentage is not None
                    and 0.0 <= sub.normalized_percentage <= 100.0
                ):
                    ratio = min(
                        1.0, sub.normalized_percentage / max(1.0, prereq.min_score)
                    )
                    ratios.append(ratio)
                    has_academic_evidence = True
                else:
                    ratios.append(0.0)
            if ratios and has_academic_evidence:
                academic_score = round(sum(ratios) / len(ratios), 3)
                active_weights["academic"] = self.scoring_policy.weight_academic

        active_dims = sorted(list(active_weights.keys()))
        coverage_ratio = round(len(active_dims) / 4.0, 2)
        num_dims = len(active_dims)

        if num_dims == 4:
            evidence_tier = "comprehensive"
            is_insufficient = False
            is_unscored = False
        elif num_dims >= 2:
            evidence_tier = "partial"
            is_insufficient = False
            is_unscored = False
        elif num_dims == 1:
            evidence_tier = "exploratory"
            is_insufficient = True
            is_unscored = False
        else:  # num_dims == 0
            evidence_tier = "unscored"
            is_insufficient = True
            is_unscored = True

        # Weight Renormalization across present dimensions
        total_active = sum(active_weights.values())
        if not is_unscored and total_active > 0:
            norm_discipline = (
                (active_weights.get("discipline", 0.0) / total_active)
                * discipline_score
            )
            norm_career = (
                (active_weights.get("career", 0.0) / total_active)
                * career_score
            )
            norm_geo = (
                (active_weights.get("geographic", 0.0) / total_active)
                * geo_score
            )
            norm_academic = (
                (active_weights.get("academic", 0.0) / total_active)
                * academic_score
            )
            composite = round(
                norm_discipline + norm_career + norm_geo + norm_academic, 3
            )
            composite = max(0.0, min(1.0, composite))
        else:
            # Zero-dimensional profile: strictly UNSCORED.
            # No genuine numerical match score is assigned so it cannot compete in auction ranking.
            # Display metadata neutral_baseline_display remains available as 0.50.
            composite = None

        return AlignmentScores(
            academic_alignment=academic_score,
            discipline_alignment=discipline_score,
            career_alignment=career_score,
            geographic_alignment=geo_score,
            composite_score=composite,
            evidence_coverage_ratio=coverage_ratio,
            active_dimensions=active_dims,
            is_insufficient_evidence=is_insufficient,
            evidence_tier=evidence_tier,
            is_unscored=is_unscored,
            neutral_baseline_display=0.50,
        )


class FranchiseAgentFactory:
    """Factory for instantiating programme-specific Franchise Agents."""

    @staticmethod
    def create_for_programme(
        programme: ProgrammeFrame,
        frame_registry: Optional[FrameRegistry] = None,
        scoring_policy: Optional[ScoringPolicy] = None,
        rule_engine: Optional[RuleEngine] = None,
    ) -> FranchiseAgent:
        """Instantiates a FranchiseAgent for the specified programme."""
        return FranchiseAgent(
            programme=programme,
            frame_registry=frame_registry,
            scoring_policy=scoring_policy,
            rule_engine=rule_engine,
        )
