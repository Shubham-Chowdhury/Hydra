"""Central Referee Agent for Hydra (Phase 7 / M007).

Synthesizes multi-agent outputs, enforces the decision hierarchy, resolves inter-agent
conflicts, and generates explainable admissions recommendations.

MATHEMATICAL AND ARCHITECTURAL DIRECTIVES:
1. Decision Hierarchy Enforcement:
   Level 1: Verified Formal Mandatory Rules
   Level 2: Verified External Evidence
   Level 3: Student-Provided Information (labeled)
   Level 4: Deterministically Derived Information
   Level 5: Advisory Historical Observations
   Level 6: Predictions with Uncertainty
   Level 7: Hypothetical Simulation Scenarios
   Level 8: Synthetic Examples
   Level 9: Unknown Facts (yields needs_review)
2. Precedence Invariant:
   No advisory forecast, auction proposal, or preference score can overturn
   a verified mandatory rule violation.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.domain.referee import (
    AgentResponseEnvelope,
    ConflictRecord,
    RefereeEvaluationResult,
    RefereeProgrammeDecision,
)


class RefereeAgent:
    """The Central Referee orchestrates multi-agent validation and conflict resolution."""

    REFEREE_VERSION: str = "hydra_referee_v1.0.0"

    HIERARCHY_LEVELS: List[str] = [
        "1. Verified Formal Mandatory Rules",
        "2. Verified External Evidence",
        "3. Student-Provided Information (Explicitly Labeled)",
        "4. Deterministically Derived Facts",
        "5. Advisory Historical Observations",
        "6. Predictions with Uncertainty",
        "7. Hypothetical Simulation Scenarios",
        "8. Synthetic Demonstration Fixtures",
        "9. Unknown Facts (needs_review)",
    ]

    def validate_envelopes(
        self, envelopes: List[AgentResponseEnvelope]
    ) -> Tuple[str, str, str]:
        """Validates that all agent response envelopes reference a consistent Twin snapshot,
        Twin ID, and profile fingerprint. Rejects cross-student or mismatched responses.
        """
        if not envelopes:
            raise ValueError("Referee cannot evaluate an empty set of agent envelopes.")

        first_snap = envelopes[0].snapshot_id
        first_twin = envelopes[0].twin_id
        first_fp = envelopes[0].profile_fingerprint

        for env in envelopes:
            if env.snapshot_id != first_snap:
                raise ValueError(
                    f"Referee snapshot mismatch: Envelope '{env.agent_name}' references snapshot "
                    f"'{env.snapshot_id}', expected '{first_snap}'."
                )
            if env.twin_id != first_twin:
                raise ValueError(
                    f"Referee Twin ID mismatch: Envelope '{env.agent_name}' references Twin "
                    f"'{env.twin_id}', expected '{first_twin}'."
                )
            if first_fp and env.profile_fingerprint and env.profile_fingerprint != first_fp:
                raise ValueError(
                    f"Referee profile fingerprint mismatch (cross-student response detected): "
                    f"Envelope '{env.agent_name}' has fingerprint '{env.profile_fingerprint}', "
                    f"expected '{first_fp}'. Never mix responses across different student profiles."
                )

        return first_snap, first_twin, first_fp

    def detect_and_resolve_conflicts(
        self,
        evaluations: List[Dict[str, Any]],
        franchise_bids: List[Dict[str, Any]],
        oracle_forecasts: Dict[str, Dict[str, Any]],
        boss_fight_reports: Dict[str, Dict[str, Any]],
    ) -> List[ConflictRecord]:
        """Identifies conflicting assertions between agents and applies decision hierarchy resolution."""
        conflicts: List[ConflictRecord] = []

        eval_map = {e["programme_id"]: e for e in evaluations}

        # Conflict 1: Franchise submits candidate proposal despite mandatory rule violation
        for bid in franchise_bids:
            prog_id = bid.get("programme_id")
            if prog_id in eval_map:
                eval_item = eval_map[prog_id]
                eval_status = eval_item.get("eligibility_status")
                bid_status = bid.get("proposal_status")

                if eval_status == "ineligible" and bid_status in ("UNCONDITIONAL_CANDIDATE", "CONDITIONAL_CANDIDATE"):
                    conflicts.append(
                        ConflictRecord(
                            conflict_id=f"CONF_{uuid.uuid4().hex[:8]}",
                            agents_involved=["FranchiseAgent", "DeterministicRuleEngine"],
                            field_or_claim=f"programme_eligibility_{prog_id}",
                            claim_a=f"FranchiseAgent submitted {bid_status}",
                            claim_b="DeterministicRuleEngine found mandatory rule violation (ineligible)",
                            resolution_strategy="Enforce Rule 1: Mandatory formal eligibility rule has absolute precedence.",
                            resolved_value="ineligible",
                            is_resolved=True,
                            explanation=(
                                f"Programme '{prog_id}' has definitive mandatory rule violations. "
                                f"Franchise proposal '{bid_status}' overridden to NO_BID per decision hierarchy."
                            ),
                        )
                    )

        # Conflict 2: Boss-Fight claims robustness for an ineligible programme
        for prog_id, report in boss_fight_reports.items():
            if prog_id in eval_map:
                eval_status = eval_map[prog_id].get("eligibility_status")
                robustness = report.get("overall_robustness", "")
                if eval_status == "ineligible" and "robust" in robustness.lower():
                    conflicts.append(
                        ConflictRecord(
                            conflict_id=f"CONF_{uuid.uuid4().hex[:8]}",
                            agents_involved=["BossFightAgent", "DeterministicRuleEngine"],
                            field_or_claim=f"robustness_{prog_id}",
                            claim_a=f"BossFight reports {robustness}",
                            claim_b="Programme is baseline ineligible",
                            resolution_strategy="Enforce Rule 1: Baseline ineligibility precludes robustness.",
                            resolved_value="fails_under_tested_scenarios",
                            is_resolved=True,
                            explanation="A programme that fails baseline admission cannot be classified as robust.",
                        )
                    )

        return conflicts

    def synthesize_decisions(
        self,
        snapshot_id: str,
        twin_id: str,
        student_name: str,
        evaluations: List[Dict[str, Any]],
        auction_results: Optional[Dict[str, Any]],
        heist_plans: Dict[str, Dict[str, Any]],
        oracle_forecasts: Dict[str, Dict[str, Any]],
        boss_fight_reports: Dict[str, Dict[str, Any]],
        interest_result: Optional[Dict[str, Any]],
        envelopes: List[AgentResponseEnvelope],
    ) -> RefereeEvaluationResult:
        """Consolidates all verified agent analyses into final recommendations."""
        # Detect and resolve conflicts
        bids = auction_results.get("all_bids", []) if auction_results else []
        conflicts = self.detect_and_resolve_conflicts(
            evaluations=evaluations,
            franchise_bids=bids,
            oracle_forecasts=oracle_forecasts,
            boss_fight_reports=boss_fight_reports,
        )

        decisions: List[RefereeProgrammeDecision] = []
        auction_rankings = auction_results.get("rankings", []) if auction_results else []
        rank_lookup = {r["programme_id"]: r["rank"] for r in auction_rankings}

        for ev in evaluations:
            prog_id = ev["programme_id"]
            title = ev.get("programme_title", prog_id)
            inst = ev.get("institution_name", "Academic Institution")
            elig = ev.get("eligibility_status", "needs_review")
            afford = bool(ev.get("is_affordable", True))
            tuition = float(ev.get("estimated_total_tuition_inr", 0.0))
            budget = float(ev.get("total_budget_inr", 0.0))
            fit = float(ev.get("preference_fit_score", 0.0))

            # Matching franchise bid
            matching_bid = next((b for b in bids if b.get("programme_id") == prog_id), None)
            prop_status = matching_bid.get("proposal_status") if matching_bid else None
            pref_coverage = float(matching_bid.get("evidence_coverage_ratio", 1.0)) if matching_bid else 1.0
            active_dims = list(matching_bid.get("active_dimensions", [])) if matching_bid else []
            is_insufficient_pref = bool(matching_bid.get("is_insufficient_evidence", False)) if matching_bid else False

            # If conflict was resolved to ineligible, ensure proposal reflects no-bid
            if any(c.field_or_claim == f"programme_eligibility_{prog_id}" for c in conflicts):
                prop_status = "NO_BID"

            # Matching auction rank
            auc_rank = rank_lookup.get(prog_id)

            # Matching heist plan
            plan = heist_plans.get(prog_id)
            has_plan = plan.get("is_achievable", False) if plan else False
            plan_actions = [a["action_name"] for a in plan.get("actions", [])] if plan else []

            # Matching oracle forecast
            oracle_item = oracle_forecasts.get(prog_id)
            oracle_st = oracle_item.get("status", "INSUFFICIENT_VERIFIED_DATA") if oracle_item else "INSUFFICIENT_VERIFIED_DATA"

            # Matching boss-fight report
            bf = boss_fight_reports.get(prog_id)
            bf_robust = bf.get("overall_robustness") if bf else None
            bf_surv = bf.get("attacks_survived", 0) if bf else 0
            bf_tot = bf.get("total_attacks_tested", 0) if bf else 0

            # Narrative explanation synthesis
            summary_parts = []
            if elig == "eligible":
                if afford:
                    summary_parts.append("Fully eligible with verified prerequisites and tuition within budget.")
                else:
                    summary_parts.append(
                        f"Academically eligible, but tuition (₹{int(tuition):,}) exceeds student budget (₹{int(budget):,})."
                    )
            elif elig == "ineligible":
                summary_parts.append("Mandatory admission requirements not satisfied.")
            else:
                summary_parts.append("Information incomplete; requires manual verification of missing prerequisites.")

            if is_insufficient_pref:
                summary_parts.append(
                    f"Preference fit is exploratory (evidence coverage {pref_coverage*100:.0f}%, "
                    f"{len(active_dims)}/4 dimensions provided)."
                )

            if bf_robust:
                summary_parts.append(f"Adversarial stress test: {bf_robust} ({bf_surv}/{bf_tot} scenarios survived).")

            if oracle_st == "READY" and oracle_item and oracle_item.get("point_prediction") is not None:
                summary_parts.append(f"Oracle advisory cutoff forecast: ~{oracle_item['point_prediction']}.")
            elif oracle_st == "INSUFFICIENT_VERIFIED_DATA":
                summary_parts.append("Oracle cutoff forecast unavailable: Verified official cutoff records lacking.")

            decision = RefereeProgrammeDecision(
                programme_id=prog_id,
                programme_title=title,
                institution_name=inst,
                eligibility_status=elig,
                is_affordable=afford,
                tuition_inr=tuition,
                student_budget_inr=budget,
                preference_fit=fit,
                preference_evidence_coverage=pref_coverage,
                active_preference_dimensions=active_dims,
                is_insufficient_preference_evidence=is_insufficient_pref,
                franchise_proposal_status=prop_status,
                auction_rank=auc_rank,
                oracle_status=oracle_st,
                oracle_forecast=oracle_item,
                heist_plan_discovered=has_plan,
                heist_plan_actions=plan_actions,
                boss_fight_robustness=bf_robust,
                boss_fight_survived=bf_surv,
                boss_fight_total=bf_tot,
                rule_traces=ev.get("reasoning_trace", {}).get("rules_evaluated", []),
                decision_summary=" ".join(summary_parts),
            )
            decisions.append(decision)

        # Rank top recommended programmes: Eligible + Affordable first, sorted by fit/auction
        top_candidates = [
            d.programme_id
            for d in sorted(
                decisions,
                key=lambda x: (
                    x.eligibility_status == "eligible",
                    x.is_affordable,
                    -(x.auction_rank or 999),
                    x.preference_fit,
                ),
                reverse=True,
            )
            if d.eligibility_status == "eligible"
        ]

        now_iso = datetime.now(timezone.utc).isoformat()
        eval_id = f"REF_EVAL_{uuid.uuid4().hex[:12]}"

        return RefereeEvaluationResult(
            evaluation_id=eval_id,
            snapshot_id=snapshot_id,
            twin_id=twin_id,
            student_name=student_name,
            programme_decisions=decisions,
            top_recommended_programmes=top_candidates,
            conflicts_detected=conflicts,
            interest_decoder_result=interest_result,
            agent_envelopes=envelopes,
            hierarchy_rules_applied=self.HIERARCHY_LEVELS,
            audit_timestamp=now_iso,
        )

