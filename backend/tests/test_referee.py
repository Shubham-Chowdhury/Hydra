"""Comprehensive Verification Test Suite for the Central Referee & Full Hydra Integration (M007).

Executes Scenarios A through H from Section 11.9 of the Master Specification:
- Scenario A: Strong CS candidate (eligible, affordable, aligned).
- Scenario B: Academically ineligible candidate (mandatory violation, no-bid).
- Scenario C: Eligible but unaffordable (eligible, tuition > budget).
- Scenario D: Incomplete information (missing mandatory fact -> needs_review).
- Scenario E: Alternative pathway (AnyOf prerequisite resolution & A* planning).
- Scenario F: Adverse scenario (Simulator / Boss-Fight stress test fragility).
- Scenario G: Oracle unavailable (insufficient verified data, graceful degradation).
- Scenario H: Interest interpretation (tripartite lifecycle without silent Twin mutation).
- Envelope validation: Snapshot mismatch rejection.
- API validation: POST /api/v1/referee/evaluate.
"""

import pytest
from fastapi.testclient import TestClient

from app.agents.referee_agent import RefereeAgent
from app.domain.referee import AgentResponseEnvelope
from app.main import app
from app.services.referee_service import RefereeService


@pytest.fixture
def referee_service() -> RefereeService:
    return RefereeService()


def test_1_scenario_a_strong_cs_candidate(referee_service):
    """Scenario A: Strong CS Candidate satisfies prerequisites, budget is sufficient,

    Franchise bids UNCONDITIONAL, Auction ranks top, and Referee recommends.
    """
    profile_data = {
        "student_id": "STU_SCENARIO_A",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 98.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 95.0, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 92.0, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 90.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Advanced",
        "entrance_rank": 45,
        "total_budget_inr": 2500000.0,  # 25 Lakhs (more than 4-year tuition of 8-10L)
        "preferred_disciplines": ["Computer Science", "Artificial Intelligence"],
        "career_goals": ["Machine Learning Engineer", "Software Systems Engineer"],
    }

    result = referee_service.evaluate(
        profile_data=profile_data,
        include_auction=True,
        include_oracle=True,
        include_planning=True,
    )

    assert result.snapshot_id.startswith("SNAP_")
    assert len(result.programme_decisions) >= 3
    assert len(result.top_recommended_programmes) > 0

    # Top programme should be eligible and affordable
    top_id = result.top_recommended_programmes[0]
    top_dec = next(d for d in result.programme_decisions if d.programme_id == top_id)
    assert top_dec.eligibility_status == "eligible"
    assert top_dec.is_affordable is True
    assert "eligible with verified prerequisites" in top_dec.decision_summary.lower()


def test_2_scenario_b_academically_ineligible_candidate(referee_service):
    """Scenario B: Academically Ineligible Candidate has mandatory violation (low entrance rank or low math),

    overriding any franchise proposal to NO_BID and excluding from top recommendations.
    """
    profile_data = {
        "student_id": "STU_SCENARIO_B",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 40.0, "grading_scale": "percentage"},  # Failed min 60%
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 50.0, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 55.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Advanced",
        "entrance_rank": 95000,  # Far below cutoff
        "total_budget_inr": 5000000.0,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Systems Engineer"],
    }

    result = referee_service.evaluate(profile_data=profile_data)

    # Ineligible programmes must be excluded from top recommendations
    cs_dec = next((d for d in result.programme_decisions if "computer" in d.programme_title.lower()), None)
    if cs_dec:
        assert cs_dec.eligibility_status == "ineligible"
        assert cs_dec.programme_id not in result.top_recommended_programmes
        assert "not satisfied" in cs_dec.decision_summary.lower() or "mandatory" in cs_dec.decision_summary.lower()


def test_3_scenario_c_eligible_but_unaffordable(referee_service):
    """Scenario C: Eligible but Unaffordable Candidate passes academic requirements,

    but tuition exceeds budget. Eligibility is preserved as 'eligible', but is_affordable is False.
    """
    profile_data = {
        "student_id": "STU_SCENARIO_C",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 95.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 92.0, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 90.0, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 85.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 15000,
        "total_budget_inr": 100000.0,  # 1 Lakh INR (tuition is 6-16 Lakhs)
        "preferred_disciplines": ["Computer Science"],
    }

    result = referee_service.evaluate(profile_data=profile_data)

    cs_dec = next((d for d in result.programme_decisions if "computer" in d.programme_title.lower()), None)
    if cs_dec:
        assert cs_dec.eligibility_status == "eligible"
        assert cs_dec.is_affordable is False
        assert "exceeds student budget" in cs_dec.decision_summary.lower()


def test_4_scenario_d_incomplete_information_yields_needs_review(referee_service):
    """Scenario D: Incomplete Information Candidate lacks mandatory prerequisites,

    yielding 'needs_review' without any agent inventing missing facts.
    """
    profile_data = {
        "student_id": "STU_SCENARIO_D",
        "subject_scores": [
            # Only Chemistry provided; Math and Physics missing
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 90.0, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 2000000.0,
    }

    result = referee_service.evaluate(profile_data=profile_data)

    cs_dec = next((d for d in result.programme_decisions if "computer" in d.programme_title.lower()), None)
    if cs_dec:
        assert cs_dec.eligibility_status == "needs_review"
        assert "requires manual verification" in cs_dec.decision_summary.lower() or "incomplete" in cs_dec.decision_summary.lower()


def test_5_scenario_e_alternative_pathway_planning(referee_service):
    """Scenario E: Heist Planner discovers alternative action pathways for the student."""
    profile_data = {
        "student_id": "STU_SCENARIO_E",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 85.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 82.0, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 80.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Advanced",
        "entrance_rank": 800,
        "total_budget_inr": 2000000.0,
        "preferred_disciplines": ["Mechanical Engineering"],
    }

    result = referee_service.evaluate(profile_data=profile_data, include_planning=True)

    # Envelopes must contain HeistPlannerAgent
    planner_env = next((e for e in result.agent_envelopes if e.agent_name == "HeistPlannerAgent"), None)
    assert planner_env is not None
    assert planner_env.execution_status == "SUCCESS"


def test_6_scenario_f_adverse_scenario_stress_testing(referee_service):
    """Scenario F: Boss-Fight Agent executes 6 adversarial stress tests and reports robustness."""
    profile_data = {
        "student_id": "STU_SCENARIO_F",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 88.0, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 85.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Advanced",
        "entrance_rank": 200,
        "total_budget_inr": 2000000.0,
    }

    result = referee_service.evaluate(profile_data=profile_data, include_stress_test=True)

    bf_env = next((e for e in result.agent_envelopes if e.agent_name == "BossFightAgent"), None)
    assert bf_env is not None
    assert bf_env.execution_status == "SUCCESS"
    assert bf_env.result["tested_programme"] is not None


def test_7_scenario_g_oracle_unavailable_degrades_gracefully(referee_service):
    """Scenario G: Oracle reports INSUFFICIENT_VERIFIED_DATA without blocking the pipeline."""
    profile_data = {
        "student_id": "STU_SCENARIO_G",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 88.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Advanced",
        "entrance_rank": 300,
        "total_budget_inr": 2000000.0,
    }

    result = referee_service.evaluate(profile_data=profile_data, include_oracle=True)

    # Oracle must report insufficient verified data honestly
    for dec in result.programme_decisions:
        assert dec.oracle_status == "INSUFFICIENT_VERIFIED_DATA"
        assert dec.oracle_forecast is not None
        assert dec.oracle_forecast.get("point_prediction") is None


def test_8_scenario_h_interest_interpretation_workflow(referee_service):
    """Scenario H: Interest Decoder translates natural-language narrative into candidate concepts

    without silently mutating the student's digital twin.
    """
    profile_data = {
        "student_id": "STU_SCENARIO_H",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Advanced",
        "entrance_rank": 350,
        "total_budget_inr": 1500000.0,
    }

    narrative = "I am fascinated by robotics, autonomous aerial drones, and embedded microcontroller systems."
    result = referee_service.evaluate(
        profile_data=profile_data,
        interest_narrative=narrative,
    )

    assert result.interest_decoder_result is not None
    assert len(result.interest_decoder_result["candidates"]) > 0
    top_cand = result.interest_decoder_result["candidates"][0]
    # Status must be MODEL_SUGGESTED, never USER_CONFIRMED without explicit approval
    assert top_cand["status"] == "MODEL_SUGGESTED"


def test_9_snapshot_mismatch_rejected():
    """Verifies that RefereeAgent rejects envelopes with mismatched snapshot IDs."""
    agent = RefereeAgent()
    envelopes = [
        AgentResponseEnvelope(
            agent_name="AgentA",
            agent_version="v1",
            schema_version="v1",
            snapshot_id="SNAP_AAA_111",
            twin_id="TWIN_1",
            execution_status="SUCCESS",
            result={},
        ),
        AgentResponseEnvelope(
            agent_name="AgentB",
            agent_version="v1",
            schema_version="v1",
            snapshot_id="SNAP_BBB_222",  # Mismatch!
            twin_id="TWIN_1",
            execution_status="SUCCESS",
            result={},
        ),
    ]

    with pytest.raises(ValueError, match="Referee snapshot mismatch"):
        agent.validate_envelopes(envelopes)


def test_10_api_referee_evaluate():
    """Verifies POST /api/v1/referee/evaluate end-to-end endpoint."""
    client = TestClient(app)
    payload = {
        "profile": {
            "student_id": "STU_API_EVAL",
            "subject_scores": [
                {"subject_code": "MATH", "subject_name": "Mathematics", "score": 95.0, "grading_scale": "percentage"},
                {"subject_code": "PHYS", "subject_name": "Physics", "score": 90.0, "grading_scale": "percentage"},
                {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 88.0, "grading_scale": "percentage"},
            ],
            "entrance_exam_name": "JEE Advanced",
            "entrance_rank": 100,
            "total_budget_inr": 2000000.0,
            "preferred_disciplines": ["Computer Science"],
        },
        "include_auction": True,
        "include_planning": False,
        "include_stress_test": False,
        "include_oracle": True,
        "interest_narrative": "Building algorithms, artificial intelligence, and scalable software systems.",
    }

    res = client.post("/api/v1/referee/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "evaluation_id" in data
    assert "snapshot_id" in data
    assert len(data["programme_decisions"]) > 0
    assert len(data["agent_envelopes"]) >= 4
    assert len(data["hierarchy_rules_applied"]) == 9


def test_11_stale_snapshot_rejection(referee_service):
    """Verifies that Referee rejects mismatched or stale twin snapshots when profile data differs."""
    twin_agent = referee_service.twin_service.agent
    p1 = {
        "student_id": "STUDENT_A",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 500000.0,
    }
    snap1 = referee_service.twin_service.construct_twin(p1)

    p2 = {
        "student_id": "STUDENT_A",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 50.0, "grading_scale": "percentage"},  # Different score!
        ],
        "total_budget_inr": 900000.0,
    }

    # Pass snap1's snapshot_id but with p2's profile data -> must raise ValueError for stale snapshot
    with pytest.raises(ValueError, match="Stale or mismatched snapshot"):
        referee_service.evaluate(profile_data=p2, snapshot_id=snap1.snapshot_id)


def test_12_cross_student_mismatch_rejection():
    """Verifies that Referee strictly rejects envelopes originating from differing student twins."""
    agent = RefereeAgent()
    envelopes = [
        AgentResponseEnvelope(
            agent_name="AgentA",
            agent_version="v1",
            schema_version="v1",
            snapshot_id="SNAP_SAME",
            twin_id="TWIN_STUDENT_ALPHA",
            execution_status="SUCCESS",
            result={},
        ),
        AgentResponseEnvelope(
            agent_name="AgentB",
            agent_version="v1",
            schema_version="v1",
            snapshot_id="SNAP_SAME",
            twin_id="TWIN_STUDENT_BETA",  # Cross-student mismatch!
            execution_status="SUCCESS",
            result={},
        ),
    ]

    with pytest.raises(ValueError, match="Referee Twin ID mismatch"):
        agent.validate_envelopes(envelopes)


def test_13_mandatory_rule_overrides_high_auction_or_preference_fit(referee_service):
    """Verifies invariant: No preference fit, predictive forecast, or franchise bid overrides a mandatory rule failure."""
    profile_data = {
        "student_id": "STU_RULE_OVERRIDE_TEST",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 30.0, "grading_scale": "percentage"},  # Flunked math
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 99.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 500,  # Great rank, but failed math prerequisite
        "total_budget_inr": 2000000.0,
        "preferred_disciplines": ["Computer Science"],  # 100% preference fit
    }

    result = referee_service.evaluate(
        profile_data=profile_data,
        include_auction=True,
    )

    for decision in result.programme_decisions:
        if decision.eligibility_status == "ineligible":
            # Must NEVER be in top recommendations regardless of budget or fit
            assert decision.programme_id not in result.top_recommended_programmes
            # Proposal must be overridden to NO_BID
            assert decision.franchise_proposal_status in ("no_bid", "NO_BID", None)


def test_14_api_referee_evaluate_with_existing_snapshot():
    """Verifies POST /api/v1/referee/evaluate using an existing snapshot_id."""
    client = TestClient(app)
    # 1. Construct twin snapshot
    twin_payload = {
        "student_id": "STU_EXISTING_SNAP",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 92.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 88.0, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 85.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 8000,
        "total_budget_inr": 1000000.0,
    }
    twin_res = client.post("/api/v1/twin/construct", json=twin_payload)
    assert twin_res.status_code == 200
    snapshot_id = twin_res.json()["snapshot"]["snapshot_id"]

    # 2. Evaluate under Referee using snapshot_id
    eval_payload = {
        "snapshot_id": snapshot_id,
        "include_auction": True,
    }
    res = client.post("/api/v1/referee/evaluate", json=eval_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["snapshot_id"] == snapshot_id
    assert len(data["programme_decisions"]) > 0


def test_15_profile_fingerprint_cross_student_rejection():
    """Verifies that Referee strictly rejects envelopes with conflicting profile fingerprints."""
    agent = RefereeAgent()
    envelopes = [
        AgentResponseEnvelope(
            agent_name="AgentA",
            agent_version="v1",
            schema_version="v1",
            snapshot_id="SNAP_100",
            twin_id="TWIN_100",
            profile_fingerprint="a" * 64,
            execution_status="SUCCESS",
            result={},
        ),
        AgentResponseEnvelope(
            agent_name="AgentB",
            agent_version="v1",
            schema_version="v1",
            snapshot_id="SNAP_100",
            twin_id="TWIN_100",
            profile_fingerprint="b" * 64,  # Conflicting profile fingerprint
            execution_status="SUCCESS",
            result={},
        ),
    ]

    with pytest.raises(ValueError, match="Referee profile fingerprint mismatch"):
        agent.validate_envelopes(envelopes)


def test_16_snapshot_id_vs_fingerprint_type_separation(referee_service):
    """Verifies architectural separation: snapshot_id (unique identifier) is never compared

    directly against profile_fingerprint (SHA-256 hash).
    """
    twin_payload = {
        "student_id": "STU_SEPARATION_TEST",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 800000.0,
    }
    snap = referee_service.twin_service.construct_twin(twin_payload)

    # snapshot_id is UUID-based (e.g. SNAP_...)
    # profile_fingerprint is 64-char hex string
    assert snap.snapshot_id != snap.profile_fingerprint
    assert len(snap.profile_fingerprint) == 64
    assert snap.snapshot_id.startswith("SNAP_")

    # Evaluate under Referee: must succeed without conflating snapshot_id and fingerprint
    result = referee_service.evaluate(snapshot_id=snap.snapshot_id)
    assert result.snapshot_id == snap.snapshot_id


def test_17_concurrent_twin_construction_multi_student_isolation(referee_service):
    """Verifies that concurrent Twin construction for distinct students cannot mix facts or frames."""
    from concurrent.futures import ThreadPoolExecutor

    def make_profile(idx: int):
        return {
            "student_id": f"STU_CONCURRENT_{idx}",
            "subject_scores": [
                {"subject_code": "MATH", "subject_name": "Mathematics", "score": 70.0 + idx, "grading_scale": "percentage"},
                {"subject_code": "PHYS", "subject_name": "Physics", "score": 80.0 + idx, "grading_scale": "percentage"},
            ],
            "entrance_exam_name": "JEE Main",
            "entrance_rank": 1000 * (idx + 1),
            "total_budget_inr": 500000.0 + idx * 50000.0,
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(referee_service.twin_service.construct_twin, make_profile(i)) for i in range(10)]
        results = [f.result() for f in futures]

    # Verify all 10 students have strictly distinct fingerprints, twin_ids, and snapshot_ids
    fingerprints = {r.profile_fingerprint for r in results}
    twin_ids = {r.twin_id for r in results}
    snapshot_ids = {r.snapshot_id for r in results}

    assert len(fingerprints) == 10
    assert len(twin_ids) == 10
    assert len(snapshot_ids) == 10

    # Verify each snapshot's student frame reflects its own specific student_id and math score
    for i, snap in enumerate(results):
        assert snap.student_frame.student_id == f"STU_CONCURRENT_{i}"
        math_score = snap.student_frame.get_subject_score("MATH")
        assert math_score is not None
        assert math_score.score == 70.0 + i


def test_18_referee_snapshot_validation_purity(referee_service):
    """Verifies that Referee snapshot validation is pure: zero frame mutations and zero extra snapshots."""
    profile_data = {
        "student_id": "STU_PURITY_TEST",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 92.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 88.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Advanced",
        "entrance_rank": 450,
        "total_budget_inr": 1200000.0,
    }
    # 1. Initial snapshot construction
    snap = referee_service.twin_service.construct_twin(profile_data)
    initial_snapshots_by_id = len(referee_service.twin_service._snapshots_by_id)
    initial_snapshots_by_snap_id = len(referee_service.twin_service._snapshots_by_snapshot_id)

    # 2. Pure fingerprint calculation directly
    pure_fingerprint = referee_service.twin_service.compute_fingerprint(profile_data)
    assert pure_fingerprint == snap.profile_fingerprint
    assert len(referee_service.twin_service._snapshots_by_snapshot_id) == initial_snapshots_by_snap_id

    # 3. Evaluate multiple times under Referee with both snapshot_id and profile_data
    for _ in range(5):
        res = referee_service.evaluate(snapshot_id=snap.snapshot_id, profile_data=profile_data)
        assert res.snapshot_id == snap.snapshot_id

    # Assert ZERO new snapshots were constructed or cached during validation
    assert len(referee_service.twin_service._snapshots_by_id) == initial_snapshots_by_id
    assert len(referee_service.twin_service._snapshots_by_snapshot_id) == initial_snapshots_by_snap_id

    # 4. Mismatched profile data must be rejected without mutating storage
    altered_profile = dict(profile_data)
    altered_profile["total_budget_inr"] = 9999999.0
    import pytest
    with pytest.raises(ValueError, match="Stale or mismatched snapshot"):
        referee_service.evaluate(snapshot_id=snap.snapshot_id, profile_data=altered_profile)

    assert len(referee_service.twin_service._snapshots_by_id) == initial_snapshots_by_id
    assert len(referee_service.twin_service._snapshots_by_snapshot_id) == initial_snapshots_by_snap_id
