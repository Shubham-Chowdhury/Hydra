"""Boss-Fight Agent for Hydra (Adversarial Stress Testing).

Executes adversarial attacks against proposed programmes and academic plans to evaluate
fragility, constraint boundaries, and surviving fallbacks.
"""

from copy import deepcopy
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.domain.frames import EligibilityStatus, ProgrammeFrame
from app.domain.simulation import (
    AdversarialAttackType,
    AttackOutcome,
    BossFightReport,
    RobustnessClassification,
)
from app.domain.twin import TwinSnapshot
from app.rules.engine import RuleEngine
from app.services.programme_service import ProgrammeService


class BossFightAgent:
    """Adversarial stress-testing agent challenging applicant proposals with hostile perturbations."""

    def __init__(
        self,
        programme_service: Optional[ProgrammeService] = None,
        rule_engine: Optional[RuleEngine] = None,
    ) -> None:
        self.programme_service = programme_service or ProgrammeService()
        self.rule_engine = rule_engine or RuleEngine()

    def stress_test(
        self,
        twin_snapshot: TwinSnapshot,
        target_programme_id: str,
    ) -> BossFightReport:
        """Executes a standardized battery of adversarial attacks against the student/programme pairing."""
        programme = self.programme_service.get_by_id(target_programme_id)
        if not programme:
            raise ValueError(f"Target programme '{target_programme_id}' not found.")

        now_utc = datetime.now(timezone.utc).isoformat()
        report_id = f"BOSS_FIGHT_{target_programme_id}_{uuid.uuid4().hex[:8]}"

        base_student = twin_snapshot.student_frame
        base_trace = self.rule_engine.evaluate(
            base_student, programme, frame_registry=self.programme_service.frame_registry
        )
        base_status = base_trace.final_status.value
        base_affordable = base_student.total_budget_inr >= programme.estimated_total_tuition_inr

        attack_outcomes: List[AttackOutcome] = []

        # Attack 1: Rank Drops by 15,000 positions
        curr_rank = base_student.entrance_rank or 20000
        perturbed_s1 = deepcopy(base_student)
        perturbed_s1.entrance_rank = curr_rank + 15000
        t1 = self.rule_engine.evaluate(
            perturbed_s1, programme, frame_registry=self.programme_service.frame_registry
        )
        survived_1 = t1.final_status == EligibilityStatus.ELIGIBLE
        attack_outcomes.append(
            AttackOutcome(
                attack_type=AdversarialAttackType.RANK_WORSENS,
                perturbation_description=f"Entrance rank slips from {curr_rank} to {perturbed_s1.entrance_rank} (+15,000).",
                baseline_status=base_status,
                perturbed_status=t1.final_status.value,
                survived=survived_1,
                failed_constraint="RULE_ENTRANCE_REQUIREMENT" if not survived_1 else None,
                explanation="Violates mandatory competitive rank threshold" if not survived_1 else "Rank remained within buffer margin.",
            )
        )

        # Attack 2: Programme Tuition Hikes by 25%
        perturbed_p2 = deepcopy(programme)
        perturbed_p2.estimated_total_tuition_inr = round(programme.estimated_total_tuition_inr * 1.25, 2)
        survived_2 = base_student.total_budget_inr >= perturbed_p2.estimated_total_tuition_inr
        attack_outcomes.append(
            AttackOutcome(
                attack_type=AdversarialAttackType.TUITION_HIKED,
                perturbation_description=f"Tuition hiked +25% from INR {programme.estimated_total_tuition_inr:,.0f} to INR {perturbed_p2.estimated_total_tuition_inr:,.0f}.",
                baseline_status="Affordable" if base_affordable else "Unaffordable",
                perturbed_status="Affordable" if survived_2 else "Unaffordable",
                survived=survived_2,
                failed_constraint="FINANCIAL_BUDGET_EXCEEDED" if not survived_2 else None,
                explanation="Student budget insufficient to absorb 25% tuition inflation" if not survived_2 else "Student budget absorbed tuition increase.",
            )
        )

        # Attack 3: Family Educational Budget Drops by 30%
        perturbed_s3 = deepcopy(base_student)
        perturbed_s3.total_budget_inr = round(base_student.total_budget_inr * 0.70, 2)
        survived_3 = perturbed_s3.total_budget_inr >= programme.estimated_total_tuition_inr
        attack_outcomes.append(
            AttackOutcome(
                attack_type=AdversarialAttackType.BUDGET_REDUCED,
                perturbation_description=f"Educational budget reduced by 30% to INR {perturbed_s3.total_budget_inr:,.0f}.",
                baseline_status="Affordable" if base_affordable else "Unaffordable",
                perturbed_status="Affordable" if survived_3 else "Unaffordable",
                survived=survived_3,
                failed_constraint="FINANCIAL_BUDGET_EXCEEDED" if not survived_3 else None,
                explanation="Budget cut causes programme to become unaffordable" if not survived_3 else "Budget cut safely absorbed.",
            )
        )

        # Attack 4: Stricter Closing Cutoff (20% tighter)
        perturbed_p4 = deepcopy(programme)
        if perturbed_p4.entrance_prerequisites and perturbed_p4.entrance_prerequisites[0].max_rank:
            pr = perturbed_p4.entrance_prerequisites[0]
            new_max = int(pr.max_rank * 0.80)
            perturbed_p4.entrance_prerequisites = [type(pr)(exam_name=pr.exam_name, max_rank=new_max, is_mandatory=pr.is_mandatory)]
            t4 = self.rule_engine.evaluate(base_student, perturbed_p4, frame_registry=self.programme_service.frame_registry)
            survived_4 = t4.final_status == EligibilityStatus.ELIGIBLE
            failed_c = "RULE_ENTRANCE_CUTOFF_TIGHTENED" if not survived_4 else None
            p_stat = t4.final_status.value
        else:
            survived_4 = True
            failed_c = None
            p_stat = base_status

        attack_outcomes.append(
            AttackOutcome(
                attack_type=AdversarialAttackType.CUTOFF_STIFFENS,
                perturbation_description="Closing cutoff ranks tighten by 20% due to increased applicant competition.",
                baseline_status=base_status,
                perturbed_status=p_stat,
                survived=survived_4,
                failed_constraint=failed_c,
                explanation="Tightened cutoff eliminates applicant" if not survived_4 else "Applicant rank survived tightened cutoff.",
            )
        )

        # Attack 5: Unobtainable Document (Key Subject Marksheet Missing)
        perturbed_s5 = deepcopy(base_student)
        perturbed_s5.subject_scores = [s for s in base_student.subject_scores if s.subject_code != "MATH"]
        t5 = self.rule_engine.evaluate(perturbed_s5, programme, frame_registry=self.programme_service.frame_registry)
        survived_5 = t5.final_status == EligibilityStatus.ELIGIBLE
        attack_outcomes.append(
            AttackOutcome(
                attack_type=AdversarialAttackType.DOCUMENT_UNOBTAINABLE,
                perturbation_description="Key prerequisite transcript (Mathematics) is unverified or unobtainable.",
                baseline_status=base_status,
                perturbed_status=t5.final_status.value,
                survived=survived_5,
                failed_constraint="RULE_SUBJECT_PREREQUISITE" if not survived_5 else None,
                explanation="Prerequisite evaluation collapses to needs_review/ineligible" if not survived_5 else "Not affected.",
            )
        )

        # Attack 6: Preference Shift (Relocation restricted)
        perturbed_s6 = deepcopy(base_student)
        perturbed_s6.preferred_locations = ["Non-Matching Region"]
        attack_outcomes.append(
            AttackOutcome(
                attack_type=AdversarialAttackType.PREFERENCE_SHIFTS,
                perturbation_description="Candidate restricts geographical relocation to a non-matching state.",
                baseline_status=base_status,
                perturbed_status=base_status,
                survived=True,  # Preference does not break formal eligibility
                failed_constraint=None,
                explanation="Preference fit drops to 0.0 for location, but formal eligibility remains intact.",
            )
        )

        # 5. Robustness Classification
        survived_count = sum(1 for a in attack_outcomes if a.survived)
        failed_count = len(attack_outcomes) - survived_count

        if base_status == "needs_review":
            classification = RobustnessClassification.INSUFFICIENT_EVIDENCE
        elif failed_count == 0:
            classification = RobustnessClassification.ROBUST_UNDER_TESTED_SCENARIOS
        elif failed_count <= 2:
            classification = RobustnessClassification.FRAGILE
        else:
            classification = RobustnessClassification.FAILS_UNDER_TESTED_SCENARIOS

        # 6. Discover Surviving Alternative Programmes
        surviving_alts: List[str] = []
        all_progs = self.programme_service.get_all()
        for p in all_progs:
            if p.programme_id == target_programme_id:
                continue
            tr = self.rule_engine.evaluate(
                perturbed_s1, p, frame_registry=self.programme_service.frame_registry
            )
            if tr.final_status == EligibilityStatus.ELIGIBLE and base_student.total_budget_inr >= p.estimated_total_tuition_inr:
                surviving_alts.append(f"{p.title} ({p.institution_name})")

        # Fallback Recommendation
        if classification == RobustnessClassification.ROBUST_UNDER_TESTED_SCENARIOS:
            fallback = "Plan exhibits strong robustness under tested adversarial stressors."
        elif classification == RobustnessClassification.FRAGILE:
            fallback = (
                f"Plan is fragile under financial or rank stress. Consider preparing resilient fallbacks: "
                f"{', '.join(surviving_alts) if surviving_alts else 'Seek scholarship or lower-tuition alternatives'}."
            )
        else:
            fallback = (
                f"Plan fails under multiple adverse perturbations. Recommended fallback options: "
                f"{', '.join(surviving_alts) if surviving_alts else 'Re-evaluate programme targets'}."
            )

        disclaimer = (
            "BOSS-FIGHT ADVERSARIAL STRESS TEST: Tests survival against synthetic worst-case perturbations. "
            "Labels apply strictly to tested scenarios and do not constitute admission forecasts."
        )

        return BossFightReport(
            report_id=report_id,
            target_programme_id=programme.programme_id,
            target_programme_title=programme.title,
            snapshot_id=twin_snapshot.snapshot_id,
            overall_robustness=classification,
            total_attacks_tested=len(attack_outcomes),
            attacks_survived=survived_count,
            attacks_failed=failed_count,
            attack_outcomes=attack_outcomes,
            surviving_alternative_programmes=surviving_alts,
            fallback_recommendation=fallback,
            disclaimer=disclaimer,
            executed_at=now_utc,
        )

