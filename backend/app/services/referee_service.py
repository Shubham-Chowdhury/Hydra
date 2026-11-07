"""Central Referee Application Orchestration Service for Hydra (Phase 7 / M007).

Coordinates the multi-agent pipeline across Twin, Franchise, Auction, Planner,
Simulator, Boss-Fight, Oracle, and Interest Decoder agents, creating standard
response envelopes and delivering synthesized final recommendations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agents.referee_agent import RefereeAgent
from app.domain.oracle import ForecastTarget
from app.domain.planner import PlanningState
from app.domain.referee import AgentResponseEnvelope, RefereeEvaluationResult
from app.domain.simulation import BossFightReport
from app.domain.twin import TwinSnapshot
from app.services.admissions_service import AdmissionsService
from app.services.evaluation import EvaluationService
from app.services.franchise_service import FranchiseService
from app.services.interest_service import InterestService
from app.services.oracle_service import OracleService
from app.services.planner_service import PlannerService
from app.services.programme_service import ProgrammeService
from app.services.simulation_service import SimulationService
from app.services.twin_service import TwinService


class RefereeService:
    """Master orchestrator executing multi-agent pipelines with auditable response envelopes."""

    def __init__(
        self,
        twin_service: Optional[TwinService] = None,
        evaluation_service: Optional[EvaluationService] = None,
        franchise_service: Optional[FranchiseService] = None,
        oracle_service: Optional[OracleService] = None,
        planner_service: Optional[PlannerService] = None,
        simulation_service: Optional[SimulationService] = None,
        interest_service: Optional[InterestService] = None,
        programme_service: Optional[ProgrammeService] = None,
        admissions_service: Optional[AdmissionsService] = None,
    ) -> None:
        self.twin_service = twin_service or TwinService()
        self.programme_service = programme_service or ProgrammeService(include_all_domains=True)
        self.evaluation_service = evaluation_service or EvaluationService(programme_service=self.programme_service)
        self.franchise_service = franchise_service or FranchiseService(programme_service=self.programme_service)
        self.oracle_service = oracle_service or OracleService()
        self.planner_service = planner_service or PlannerService(programme_service=self.programme_service)
        self.simulation_service = simulation_service or SimulationService(programme_service=self.programme_service)
        self.interest_service = interest_service or InterestService()
        self.admissions_service = admissions_service or AdmissionsService()
        self.referee_agent = RefereeAgent()

    def evaluate(
        self,
        profile_data: Optional[Dict[str, Any]] = None,
        snapshot_id: Optional[str] = None,
        include_auction: bool = True,
        include_planning: bool = False,
        include_stress_test: bool = False,
        include_oracle: bool = True,
        interest_narrative: Optional[str] = None,
    ) -> RefereeEvaluationResult:
        """Executes the full multi-agent orchestration sequence and returns the Referee decision."""
        envelopes: List[AgentResponseEnvelope] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Twin Snapshot Resolution and Integrity Gate
        if snapshot_id and profile_data:
            existing_snap = self.twin_service.get_snapshot(snapshot_id)
            if not existing_snap:
                raise KeyError(f"Snapshot ID '{snapshot_id}' not found.")
            computed_fingerprint = self.twin_service.compute_fingerprint(profile_data)
            if computed_fingerprint != existing_snap.profile_fingerprint:
                raise ValueError(
                    f"Stale or mismatched snapshot: Provided snapshot_id '{snapshot_id}' "
                    f"fingerprint ({existing_snap.profile_fingerprint}) does not match "
                    f"provided profile fingerprint ({computed_fingerprint})."
                )
            snapshot = existing_snap
            student_name = profile_data.get("student_id", snapshot.student_frame.student_id or "Student")
        elif snapshot_id:
            existing_snap = self.twin_service.get_snapshot(snapshot_id)
            if not existing_snap:
                raise KeyError(f"Snapshot ID '{snapshot_id}' not found.")
            snapshot = existing_snap
            student_name = snapshot.student_frame.student_id or "Student"
        elif profile_data:
            snapshot = self.twin_service.construct_twin(profile_data)
            student_name = profile_data.get("student_id", "Student")
        else:
            raise ValueError("Either profile_data or snapshot_id must be provided to evaluate under Referee.")

        snapshot_id = snapshot.snapshot_id
        twin_id = snapshot.twin_id
        profile_fingerprint = snapshot.profile_fingerprint

        envelopes.append(
            AgentResponseEnvelope(
                agent_name="TwinAgent",
                agent_version="twin_agent_v1.0.0",
                schema_version="twin_snapshot_v1.0.0",
                snapshot_id=snapshot_id,
                twin_id=twin_id,
                profile_fingerprint=profile_fingerprint,
                execution_status="SUCCESS",
                result={
                    "fingerprint": snapshot.profile_fingerprint,
                    "subjects_count": len(snapshot.academic_identity.subject_scores),
                },
                explanation="Student Digital Twin constructed with provenance demarcation.",
                timestamp=now_iso,
            )
        )

        # 2. Deterministic Rule Engine Evaluation
        student_frame = snapshot.to_student_frame()
        programmes = self.programme_service.get_all()
        bundle = self.evaluation_service.evaluate_profile(student_frame)

        evaluations_dict: List[Dict[str, Any]] = []
        for ev in bundle.evaluations:
            evaluations_dict.append({
                "programme_id": ev.programme.programme_id,
                "programme_title": ev.programme.title,
                "institution_name": ev.programme.institution_name,
                "eligibility_status": ev.trace.final_status.value,
                "is_affordable": ev.affordability.is_affordable,
                "estimated_total_tuition_inr": ev.affordability.estimated_total_tuition_inr,
                "total_budget_inr": ev.affordability.total_budget_inr,
                "preference_fit_score": ev.preference_fit.fit_score,
                "reasoning_trace": {
                    "rules_evaluated": [
                        {
                            "rule_id": r.rule_id,
                            "rule_name": r.rule_name,
                            "status": r.status.value,
                            "explanation": r.explanation,
                            "is_mandatory": r.is_mandatory,
                        }
                        for r in ev.trace.rules_evaluated
                    ]
                },
            })

        envelopes.append(
            AgentResponseEnvelope(
                agent_name="DeterministicRuleEngine",
                agent_version="ast_rule_engine_v1.0.0",
                schema_version="evaluation_v1.0.0",
                snapshot_id=snapshot_id,
                twin_id=twin_id,
                profile_fingerprint=profile_fingerprint,
                execution_status="SUCCESS",
                result={"total_evaluated": len(evaluations_dict)},
                explanation="Evaluated mandatory academic and entrance prerequisites via deterministic AST.",
                timestamp=now_iso,
            )
        )

        # 3. Franchise Agents & Auction
        auction_result_dict: Optional[Dict[str, Any]] = None
        if include_auction:
            try:
                auction = self.franchise_service.run_auction_from_twin(snapshot)
                auction_result_dict = auction.to_dict()
                envelopes.append(
                    AgentResponseEnvelope(
                        agent_name="FranchiseAuctionService",
                        agent_version="franchise_auction_v1.0.0",
                        schema_version="auction_v1.0.0",
                        snapshot_id=snapshot_id,
                        twin_id=twin_id,
                        profile_fingerprint=profile_fingerprint,
                        execution_status="SUCCESS",
                        result={
                            "total_bids": len(auction.all_bids),
                            "unconditional": len(auction.unconditional_candidates),
                            "conditional": len(auction.conditional_candidates),
                        },
                        explanation="Franchise agents evaluated alignment and submitted deterministic auction proposals.",
                        timestamp=now_iso,
                    )
                )
            except Exception as e:
                envelopes.append(
                    AgentResponseEnvelope(
                        agent_name="FranchiseAuctionService",
                        agent_version="franchise_auction_v1.0.0",
                        schema_version="auction_v1.0.0",
                        snapshot_id=snapshot_id,
                        twin_id=twin_id,
                        profile_fingerprint=profile_fingerprint,
                        execution_status="FAILED",
                        result={},
                        error=str(e),
                        timestamp=now_iso,
                    )
                )

        # 4. Oracle Agent Admissions Forecasting
        oracle_forecasts: Dict[str, Dict[str, Any]] = {}
        if include_oracle:
            for prog in programmes:
                target = ForecastTarget(
                    institution_id=prog.institution_name,
                    programme_id=prog.programme_id,
                    future_academic_year=2027,
                    counselling_round=1,
                    exam_name=student_frame.entrance_exam_name or "JEE Advanced",
                    seat_type="OPEN",
                    quota="AI",
                    gender_pool="Gender-Neutral",
                    rank_basis="CRL",
                )
                fc = self.oracle_service.forecast(target)
                oracle_forecasts[prog.programme_id] = fc.to_dict()

            envelopes.append(
                AgentResponseEnvelope(
                    agent_name="OracleAgent",
                    agent_version="oracle_ols_lag_v1.0.0",
                    schema_version="oracle_v1.0.0",
                    snapshot_id=snapshot_id,
                    twin_id=twin_id,
                    profile_fingerprint=profile_fingerprint,
                    execution_status="SUCCESS",
                    result={"targets_queried": len(oracle_forecasts)},
                    warnings=["Oracle cutoffs are advisory and cannot override mandatory rules."],
                    explanation="Queried admissions cutoff estimates with data-readiness gating.",
                    timestamp=now_iso,
                )
            )

        # 5. Heist Planner (A* search)
        heist_plans: Dict[str, Dict[str, Any]] = {}
        if include_planning:
            for prog in programmes:
                try:
                    plan = self.planner_service.plan_pathway(snapshot, prog.programme_id)
                    heist_plans[prog.programme_id] = plan.to_dict()
                except Exception:
                    pass

            envelopes.append(
                AgentResponseEnvelope(
                    agent_name="HeistPlannerAgent",
                    agent_version="heist_astar_v1.0.0",
                    schema_version="planner_v1.0.0",
                    snapshot_id=snapshot_id,
                    twin_id=twin_id,
                    profile_fingerprint=profile_fingerprint,
                    execution_status="SUCCESS",
                    result={"plans_computed": len(heist_plans)},
                    explanation="Computed shortest-cost pathway actions using admissible A* heuristic search.",
                    timestamp=now_iso,
                )
            )

        # 6. Simulator & Boss-Fight Agent (Adversarial stress testing)
        boss_fight_reports: Dict[str, Dict[str, Any]] = {}
        if include_stress_test and programmes:
            # Test top programme or first programme
            target_prog = programmes[0]
            try:
                bf_report = self.simulation_service.run_stress_test(
                    twin_snapshot=snapshot,
                    programme_id=target_prog.programme_id,
                )
                boss_fight_reports[target_prog.programme_id] = bf_report.to_dict()
                envelopes.append(
                    AgentResponseEnvelope(
                        agent_name="BossFightAgent",
                        agent_version="boss_fight_v1.0.0",
                        schema_version="simulation_v1.0.0",
                        snapshot_id=snapshot_id,
                        twin_id=twin_id,
                        profile_fingerprint=profile_fingerprint,
                        execution_status="SUCCESS",
                        result={
                            "tested_programme": target_prog.programme_id,
                            "robustness": bf_report.overall_robustness,
                            "survived": bf_report.attacks_survived,
                        },
                        explanation="Evaluated candidate robustness across 6 adversarial perturbations.",
                        timestamp=now_iso,
                    )
                )
            except Exception as e:
                envelopes.append(
                    AgentResponseEnvelope(
                        agent_name="BossFightAgent",
                        agent_version="boss_fight_v1.0.0",
                        schema_version="simulation_v1.0.0",
                        snapshot_id=snapshot_id,
                        twin_id=twin_id,
                        profile_fingerprint=profile_fingerprint,
                        execution_status="FAILED",
                        result={},
                        error=str(e),
                        timestamp=now_iso,
                    )
                )

        # 7. Interest Decoder (Deep-Learning concept interpretation)
        interest_res_dict: Optional[Dict[str, Any]] = None
        if interest_narrative and len(interest_narrative.strip()) >= 3:
            try:
                dec_res = self.interest_service.decode_interests(interest_narrative.strip())
                interest_res_dict = dec_res.to_dict()
                envelopes.append(
                    AgentResponseEnvelope(
                        agent_name="InterestDecoderAgent",
                        agent_version="hydra_dense_semantic_v1.0.0",
                        schema_version="interest_v1.0.0",
                        snapshot_id=snapshot_id,
                        twin_id=twin_id,
                        profile_fingerprint=profile_fingerprint,
                        execution_status="SUCCESS",
                        result={
                            "candidates_count": len(dec_res.candidates),
                            "top_concept": dec_res.top_concept.concept.name if dec_res.top_concept else None,
                        },
                        explanation="Interpreted free-text interest narrative into canonical ontology concepts.",
                        timestamp=now_iso,
                    )
                )
            except Exception:
                pass

        # 8. Envelope Integrity Verification & Synthesis through Referee Agent
        self.referee_agent.validate_envelopes(envelopes)

        return self.referee_agent.synthesize_decisions(
            snapshot_id=snapshot_id,
            twin_id=twin_id,
            student_name=student_name,
            evaluations=evaluations_dict,
            auction_results=auction_result_dict,
            heist_plans=heist_plans,
            oracle_forecasts=oracle_forecasts,
            boss_fight_reports=boss_fight_reports,
            interest_result=interest_res_dict,
            envelopes=envelopes,
        )
