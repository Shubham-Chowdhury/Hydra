"""Unit and integration test suite for Hydra Franchise Agents and Simulated Auction (M002).

Tests agent instantiation, proposal generation (bids), proposal qualification tiers,
affordability decoupling, deterministic auction ranking, tie-breaking, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.agents.franchise_agent import FranchiseAgent, FranchiseAgentFactory
from app.agents.twin_agent import TwinAgent
from app.domain.frames import (
    AcademicPrerequisite,
    EligibilityStatus,
    EntrancePrerequisite,
    ProgrammeFrame,
    SubjectScore,
)
from app.domain.franchise import (
    AuctionResult,
    ProgrammeBid,
    ProposalStatus,
    ScoringPolicy,
)
from app.domain.frame_system import FrameRegistry
from app.main import app
from app.services.auction_service import AuctionService
from app.services.franchise_service import FranchiseService
from app.services.programme_service import ProgrammeService
from app.services.twin_service import TwinService


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_cs_programme() -> ProgrammeFrame:
    return ProgrammeFrame(
        programme_id="TEST_PROG_CS",
        title="B.Tech. in Computer Science (Synthetic)",
        institution_name="Test Institute of Technology",
        location="Bengaluru, Karnataka",
        discipline="Computer Science",
        annual_tuition_inr=150000.0,
        duration_years=4,
        estimated_total_tuition_inr=600000.0,
        currency="INR",
        cost_basis="tuition_only_total",
        academic_prerequisites=[
            AcademicPrerequisite(
                subject_code="MATH",
                subject_name="Mathematics",
                min_score=80.0,
                grading_scale="percentage",
                is_mandatory=True,
            ),
            AcademicPrerequisite(
                subject_code="PHYS",
                subject_name="Physics",
                min_score=75.0,
                grading_scale="percentage",
                is_mandatory=True,
            ),
        ],
        entrance_prerequisites=[
            EntrancePrerequisite(
                exam_name="JEE Main",
                max_rank=35000,
                is_mandatory=True,
            )
        ],
        skills_developed=["Algorithms", "Systems"],
        career_paths=["Software Engineer", "Systems Architect"],
        is_synthetic=True,
        dataset_label="SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
    )


@pytest.fixture
def sample_biotech_programme() -> ProgrammeFrame:
    return ProgrammeFrame(
        programme_id="TEST_PROG_BIO",
        title="B.Tech. in Biotechnology (Synthetic)",
        institution_name="Test Bio Institute",
        location="Hyderabad, Telangana",
        discipline="Biotechnology",
        annual_tuition_inr=120000.0,
        duration_years=4,
        estimated_total_tuition_inr=480000.0,
        currency="INR",
        cost_basis="tuition_only_total",
        academic_prerequisites=[
            AcademicPrerequisite(
                subject_code="BIO",
                subject_name="Biology",
                min_score=75.0,
                grading_scale="percentage",
                is_mandatory=True,
            )
        ],
        skills_developed=["Genomics", "Biochemistry"],
        career_paths=["Biomedical Engineer", "Bioinformatician"],
        is_synthetic=True,
        dataset_label="SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
    )


@pytest.fixture
def eligible_twin() -> any:
    agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_ELIGIBLE",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 80.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 15000,
        "preferred_locations": ["Bengaluru, Karnataka"],
        "total_budget_inr": 800000.0,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
    }
    return agent.construct_twin(profile)


def test_1_dynamic_franchise_agent_creation(sample_cs_programme: ProgrammeFrame):
    """Verifies dynamic instantiation of FranchiseAgent via factory with correct agent identity."""
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    assert isinstance(agent, FranchiseAgent)
    assert agent.programme.programme_id == "TEST_PROG_CS"
    assert agent.agent_id == "AGENT_FRANCHISE_TEST_PROG_CS"


def test_2_invalid_programme_rejection():
    """Verifies TypeError when non-ProgrammeFrame is passed to factory or agent."""
    with pytest.raises(TypeError):
        FranchiseAgentFactory.create_for_programme("not_a_programme")


def test_3_eligible_profile_generates_unconditional_bid(
    sample_cs_programme: ProgrammeFrame, eligible_twin: any
):
    """Verifies that an academically and competitively qualified profile yields UNCONDITIONAL_CANDIDATE."""
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(eligible_twin)

    assert isinstance(bid, ProgrammeBid)
    assert bid.programme_id == "TEST_PROG_CS"
    assert bid.proposal_status == ProposalStatus.UNCONDITIONAL_CANDIDATE
    assert bid.eligibility_status == EligibilityStatus.ELIGIBLE
    assert bid.affordability_status is True
    assert bid.academic_alignment >= 0.8
    assert bid.discipline_alignment == 1.0
    assert bid.career_alignment == 1.0
    assert bid.geographic_alignment == 1.0
    assert bid.composite_preference_score >= 0.90
    assert bid.bid_id.startswith("BID_TEST_PROG_CS_")
    assert bid.is_synthetic is True


def test_4_ineligible_profile_generates_no_bid(
    sample_cs_programme: ProgrammeFrame
):
    """Verifies that a demonstrated prerequisite violation produces NO_BID."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_INELIGIBLE",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 60.0, "max_score": 100.0, "grading_scale": "percentage"},  # Below 80 min
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 50000,  # Worse than 35000 max_rank
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    assert bid.proposal_status == ProposalStatus.NO_BID
    assert bid.eligibility_status == EligibilityStatus.INELIGIBLE
    assert len(bid.warnings) > 0
    assert any("does not meet mandatory prerequisites" in w for w in bid.warnings)


def test_5_missing_facts_generate_conditional_bid(
    sample_cs_programme: ProgrammeFrame
):
    """Verifies that missing prerequisite evidence yields CONDITIONAL_CANDIDATE (NEEDS_REVIEW)."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_MISSING_MATH",
        "subject_scores": [
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
            # MATH missing!
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 10000,
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    assert bid.proposal_status == ProposalStatus.CONDITIONAL_CANDIDATE
    assert bid.eligibility_status == EligibilityStatus.NEEDS_REVIEW
    assert any("conditional on missing facts" in w.lower() for w in bid.warnings)


def test_6_eligible_unaffordable_profile_remains_unconditional_with_warning(
    sample_cs_programme: ProgrammeFrame
):
    """Verifies affordability decoupling: applicant is ELIGIBLE / UNCONDITIONAL but affordability is False with warning."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_LOW_BUDGET",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 10000,
        "total_budget_inr": 200000.0,  # Below 600,000 tuition
    }
    twin = twin_agent.construct_twin(profile)

    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    assert bid.proposal_status == ProposalStatus.UNCONDITIONAL_CANDIDATE
    assert bid.eligibility_status == EligibilityStatus.ELIGIBLE
    assert bid.affordability_status is False
    assert any("exceeds stated budget" in w for w in bid.warnings)


def test_7_empty_preferences_yield_neutral_baseline(
    sample_cs_programme: ProgrammeFrame
):
    """Verifies neutral baseline alignment (0.50) when student specifies no preferences."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_NO_PREFS",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 10000,
        "total_budget_inr": 800000.0,
        "preferred_disciplines": [],
        "career_goals": [],
        "preferred_locations": [],
    }
    twin = twin_agent.construct_twin(profile)

    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    assert bid.discipline_alignment == 0.50
    assert bid.career_alignment == 0.50
    assert bid.geographic_alignment == 1.0  # Unconstrained
    assert 0.0 <= bid.composite_preference_score <= 1.0


def test_8_scoring_policy_weight_validation():
    """Verifies that custom ScoringPolicy enforces weight sum == 1.0."""
    with pytest.raises(ValueError):
        ScoringPolicy(weight_discipline=0.5, weight_career=0.5, weight_academic=0.5, weight_geographic=0.5)

    valid_policy = ScoringPolicy(
        weight_discipline=0.4, weight_career=0.3, weight_academic=0.2, weight_geographic=0.1
    )
    assert valid_policy.policy_version == "v1.0"


def test_9_simulated_auction_deterministic_ranking(
    sample_cs_programme: ProgrammeFrame,
    sample_biotech_programme: ProgrammeFrame,
    eligible_twin: any,
):
    """Verifies deterministic simulated auction ranking: Unconditional > Conditional > No-Bid."""
    agent_cs = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid_cs = agent_cs.evaluate(eligible_twin)  # Eligible CS (high preference alignment)

    agent_bio = FranchiseAgentFactory.create_for_programme(sample_biotech_programme)
    bid_bio = agent_bio.evaluate(eligible_twin)  # Missing BIO prerequisite -> Conditional

    auction_service = AuctionService()
    result = auction_service.run_auction([bid_cs, bid_bio])

    assert isinstance(result, AuctionResult)
    assert result.total_bids == 2
    assert len(result.unconditional_candidates) == 1
    assert len(result.conditional_candidates) == 1
    assert result.unconditional_candidates[0].bid.programme_id == "TEST_PROG_CS"
    assert result.conditional_candidates[0].bid.programme_id == "TEST_PROG_BIO"
    assert result.ranked_bids[0].rank == 1
    assert result.ranked_bids[0].bid.programme_id == "TEST_PROG_CS"
    assert result.ranked_bids[1].rank == 2
    assert result.ranked_bids[1].bid.programme_id == "TEST_PROG_BIO"


def test_10_auction_tie_breaking_behavior(sample_cs_programme: ProgrammeFrame, eligible_twin: any):
    """Verifies deterministic tie-breaking when composite scores are equal."""
    # Create two nearly identical programmes
    prog_a = ProgrammeFrame(
        programme_id="PROG_A_EXPENSIVE",
        title="Prog A",
        institution_name="Inst A",
        location="Bengaluru, Karnataka",
        discipline="Computer Science",
        estimated_total_tuition_inr=900000.0,  # Unaffordable
        duration_years=4,
        academic_prerequisites=sample_cs_programme.academic_prerequisites,
        entrance_prerequisites=sample_cs_programme.entrance_prerequisites,
        career_paths=sample_cs_programme.career_paths,
    )
    prog_b = ProgrammeFrame(
        programme_id="PROG_B_AFFORDABLE",
        title="Prog B",
        institution_name="Inst B",
        location="Bengaluru, Karnataka",
        discipline="Computer Science",
        estimated_total_tuition_inr=500000.0,  # Affordable
        duration_years=4,
        academic_prerequisites=sample_cs_programme.academic_prerequisites,
        entrance_prerequisites=sample_cs_programme.entrance_prerequisites,
        career_paths=sample_cs_programme.career_paths,
    )

    agent_a = FranchiseAgentFactory.create_for_programme(prog_a)
    agent_b = FranchiseAgentFactory.create_for_programme(prog_b)

    bid_a = agent_a.evaluate(eligible_twin)
    bid_b = agent_b.evaluate(eligible_twin)

    auction_service = AuctionService()
    result = auction_service.run_auction([bid_a, bid_b])

    # Affordable programme should win tie-breaker over unaffordable programme with equal composite fit
    assert result.ranked_bids[0].bid.programme_id == "PROG_B_AFFORDABLE"
    assert result.ranked_bids[1].bid.programme_id == "PROG_A_EXPENSIVE"
    assert result.ranked_bids[1].tie_breaker_applied is not None
    assert "Affordability" in result.ranked_bids[1].tie_breaker_applied


def test_11_auction_mixed_twin_rejection(sample_cs_programme: ProgrammeFrame):
    """Verifies that an auction containing bids from different Twin snapshots is strictly rejected."""
    twin_agent = TwinAgent()
    p1 = {"student_id": "STUDENT_1", "subject_scores": [], "total_budget_inr": 500000.0}
    p2 = {"student_id": "STUDENT_2", "subject_scores": [], "total_budget_inr": 600000.0}

    t1 = twin_agent.construct_twin(p1)
    t2 = twin_agent.construct_twin(p2)

    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid_1 = agent.evaluate(t1)
    bid_2 = agent.evaluate(t2)

    auction_service = AuctionService()
    with pytest.raises(ValueError, match="Conflicting twin_id detected"):
        auction_service.run_auction([bid_1, bid_2])


def test_12_auction_duplicate_programme_rejection(
    sample_cs_programme: ProgrammeFrame, eligible_twin: any
):
    """Verifies that submitting multiple bids for the same programme ID in one auction is rejected."""
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid1 = agent.evaluate(eligible_twin)
    bid2 = agent.evaluate(eligible_twin)

    auction_service = AuctionService()
    with pytest.raises(ValueError, match="Duplicate bid detected for programme"):
        auction_service.run_auction([bid1, bid2])


def test_13_api_get_available_franchises(client: TestClient):
    """Verifies GET /api/v1/franchises/programmes endpoint returns active franchise agents."""
    response = client.get("/api/v1/franchises/programmes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    for item in data:
        assert "programme_id" in item
        assert "agent_id" in item
        assert item["agent_id"].startswith("AGENT_FRANCHISE_")
        assert item["is_synthetic"] is True


def test_14_api_run_programme_auction_with_profile(client: TestClient):
    """Verifies POST /api/v1/franchises/auction with ad-hoc student profile payload."""
    payload = {
        "profile": {
            "student_id": "API_STUDENT_AUCTION",
            "subject_scores": [
                {"subject_code": "MATH", "subject_name": "Mathematics", "score": 92.0, "max_score": 100.0, "grading_scale": "percentage"},
                {"subject_code": "PHYS", "subject_name": "Physics", "score": 88.0, "max_score": 100.0, "grading_scale": "percentage"},
                {"subject_code": "ENG", "subject_name": "English", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
            ],
            "entrance_exam_name": "JEE Main",
            "entrance_rank": 12000,
            "preferred_locations": ["Bengaluru, Karnataka"],
            "total_budget_inr": 800000.0,
            "preferred_disciplines": ["Computer Science"],
            "career_goals": ["Software Engineer"],
        }
    }
    response = client.post("/api/v1/franchises/auction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "auction_id" in data
    assert "twin_id" in data
    assert "snapshot_id" in data
    assert data["total_bids"] >= 4
    assert len(data["ranked_bids"]) >= 4
    assert data["ranked_bids"][0]["rank"] == 1
    assert data["ranked_bids"][0]["bid"]["proposal_status"] == "unconditional_candidate"


def test_15_api_run_programme_auction_with_snapshot_id(client: TestClient):
    """Verifies POST /api/v1/franchises/auction referencing an existing constructed snapshot."""
    twin_payload = {
        "student_id": "STUDENT_FOR_SNAPSHOT",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 88.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 82.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 78.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 20000,
        "total_budget_inr": 700000.0,
        "preferred_disciplines": ["Computer Science"],
    }
    twin_res = client.post("/api/v1/twin/construct", json=twin_payload)
    assert twin_res.status_code == 200
    snapshot_id = twin_res.json()["snapshot"]["snapshot_id"]

    auction_res = client.post("/api/v1/franchises/auction", json={"snapshot_id": snapshot_id})
    assert auction_res.status_code == 200
    data = auction_res.json()
    assert data["snapshot_id"] == snapshot_id
    assert len(data["ranked_bids"]) >= 4


def test_16_api_run_programme_auction_invalid_snapshot_returns_404(client: TestClient):
    """Verifies that referencing a non-existent snapshot_id returns 404."""
    response = client.post(
        "/api/v1/franchises/auction", json={"snapshot_id": "NON_EXISTENT_SNAPSHOT_ID"}
    )
    assert response.status_code == 404


def test_17_api_run_programme_auction_empty_request_returns_400(client: TestClient):
    """Verifies that an empty auction request returns 400 Bad Request."""
    response = client.post("/api/v1/franchises/auction", json={})
    assert response.status_code == 400


def test_18_weight_renormalization_missing_optional_dimensions(sample_cs_programme: ProgrammeFrame):
    """Verifies that when student omits optional fields (career goals, locations), weights renormalize."""
    twin_agent = TwinAgent()
    # Student specifies ONLY preferred discipline: Computer Science (score 1.0) and has 100% academic scores
    profile = {
        "student_id": "STUDENT_OMITTED_FIELDS",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 95.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 15000,
        "total_budget_inr": 800000.0,
        "preferred_disciplines": ["Computer Science"],
        # career_goals omitted
        # preferred_locations omitted
    }
    twin = twin_agent.construct_twin(profile)

    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    # Discipline alignment is 1.0; Academic alignment is 1.0
    # Career and location were omitted; weights for discipline (0.35) and academic (0.20)
    # are renormalized so composite score reflects present dimensions without a penalty
    assert bid.discipline_alignment == 1.0
    assert bid.academic_alignment == 1.0
    # With renormalization, composite score should be 1.0, not penalized to (0.35*1 + 0.20*1 = 0.55)
    assert bid.composite_preference_score == pytest.approx(1.0, rel=1e-2)


def test_19_no_bid_excluded_from_positive_ranking(sample_cs_programme: ProgrammeFrame):
    """Verifies that an ineligible student receives NO_BID and is excluded from positive rankings."""
    twin_agent = TwinAgent()
    # Student violates mandatory mathematics score
    profile = {
        "student_id": "STUDENT_INELIGIBLE",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 40.0, "max_score": 100.0, "grading_scale": "percentage"},  # 40% vs 80% req
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 10000,
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)

    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    assert bid.eligibility_status == EligibilityStatus.INELIGIBLE
    assert bid.proposal_status == ProposalStatus.NO_BID

    auction_service = AuctionService()
    result = auction_service.run_auction([bid])

    # Must NOT be in unconditional or conditional candidates
    assert len(result.unconditional_candidates) == 0
    assert len(result.conditional_candidates) == 0
    # Must be in no_bid_candidates
    assert len(result.no_bid_candidates) == 1
    assert result.no_bid_candidates[0].is_positive_bid is False
    assert "no bid" in result.no_bid_candidates[0].explanation.lower()


def test_20_all_optional_dimensions_present(sample_cs_programme: ProgrammeFrame):
    """Verifies that when all 4 dimensions are present, coverage ratio is 1.0 and all are active."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_ALL_PRESENT",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 10000,
        "total_budget_inr": 900000.0,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
        "preferred_locations": ["Bengaluru, Karnataka"],
    }
    twin = twin_agent.construct_twin(profile)
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    assert bid.evidence_coverage_ratio == 1.0
    assert len(bid.active_dimensions) == 4
    assert set(bid.active_dimensions) == {"academic", "career", "discipline", "geographic"}
    assert bid.is_insufficient_evidence is False


def test_21_every_optional_feature_absent_yields_insufficient_evidence(sample_cs_programme: ProgrammeFrame):
    """Verifies that omitting all preference dimensions flags insufficient evidence."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_NO_PREFERENCES",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    # Only academic has evidence (1 dimension out of 4)
    assert bid.evidence_coverage_ratio == 0.25
    assert len(bid.active_dimensions) == 1
    assert bid.is_insufficient_evidence is True
    assert any("insufficient preference evidence" in w.lower() for w in bid.warnings)


def test_22_explicit_unknown_tokens_ignored(sample_cs_programme: ProgrammeFrame):
    """Verifies that explicit UNKNOWN or placeholder strings do not count as valid evidence."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_UNKNOWN_TOKENS",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "preferred_disciplines": ["UNKNOWN", "not_provided", ""],
        "career_goals": ["none", "N/A"],
        "preferred_locations": ["anywhere in india", "null"],
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    # Only academic is valid; UNKNOWN disciplines/careers/locations are ignored
    assert "discipline" not in bid.active_dimensions
    assert "career" not in bid.active_dimensions
    assert "geographic" not in bid.active_dimensions
    assert bid.is_insufficient_evidence is True


def test_23_invalid_and_contradictory_values(sample_cs_programme: ProgrammeFrame):
    """Verifies handling of contradictory preferences (matching discipline but disjoint career)."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_CONTRADICTORY",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "preferred_disciplines": ["Computer Science"],  # Match
        "career_goals": ["Classical Archaeologist", "Sculptor"],  # Disjoint
        "preferred_locations": ["Kashmir"],  # Disjoint
        "total_budget_inr": 800000.0,
    }
    twin = twin_agent.construct_twin(profile)
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    assert bid.discipline_alignment == 1.0
    assert bid.career_alignment == 0.0
    assert bid.geographic_alignment == 0.0
    assert 0.0 < bid.composite_preference_score < 1.0


def test_24_favorable_score_never_overrides_mandatory_requirement(sample_cs_programme: ProgrammeFrame):
    """Verifies invariant: Even with 100% preference fit, a mandatory prerequisite failure strictly yields NO_BID."""
    twin_agent = TwinAgent()
    profile = {
        "student_id": "STUDENT_PERFECT_FIT_BUT_INELIGIBLE",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 35.0, "max_score": 100.0, "grading_scale": "percentage"},  # Failed
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 10000,
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
        "preferred_locations": ["Bengaluru, Karnataka"],
        "total_budget_inr": 2000000.0,
    }
    twin = twin_agent.construct_twin(profile)
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    bid = agent.evaluate(twin)

    assert bid.eligibility_status == EligibilityStatus.INELIGIBLE
    assert bid.proposal_status == ProposalStatus.NO_BID
    assert any("mandatory prerequisites" in w.lower() for w in bid.warnings)


def test_25_four_evidence_coverage_cases(sample_cs_programme: ProgrammeFrame):
    """Verifies all 4 explicit evidence coverage cases from FranchiseAgent through AuctionService and DTO mapping:
    Case 1: 4 active dimensions (academic, career, discipline, geographic) -> ratio 1.0, is_insufficient=False.
    Case 2: 2 active dimensions (academic, discipline) -> ratio 0.50, is_insufficient=False.
    Case 3: 1 active dimension (academic only) -> ratio 0.25, is_insufficient=True, warning generated.
    Case 4: 0 active dimensions (no scores or preferences) -> ratio 0.0, is_insufficient=True, neutral 0.50 score.
    """
    twin_agent = TwinAgent()
    agent = FranchiseAgentFactory.create_for_programme(sample_cs_programme)
    auction_service = AuctionService()

    # Case 1: 4 active dimensions
    p1 = {
        "student_id": "STUDENT_CASE_1",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "preferred_disciplines": ["Computer Science"],
        "career_goals": ["Software Engineer"],
        "preferred_locations": ["Bengaluru, Karnataka"],
        "total_budget_inr": 800000.0,
    }
    t1 = twin_agent.construct_twin(p1)
    b1 = agent.evaluate(t1)
    assert b1.active_dimensions == ["academic", "career", "discipline", "geographic"]
    assert b1.evidence_coverage_ratio == 1.0
    assert b1.is_insufficient_evidence is False
    assert b1.is_unscored is False
    assert b1.evidence_tier == "comprehensive"
    assert b1.composite_preference_score == 1.0
    assert not any("insufficient preference evidence" in w.lower() for w in b1.warnings)

    # Case 2: 2 active dimensions (academic, discipline)
    p2 = {
        "student_id": "STUDENT_CASE_2",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "preferred_disciplines": ["Computer Science"],
        "career_goals": [],
        "preferred_locations": [],
        "total_budget_inr": 800000.0,
    }
    t2 = twin_agent.construct_twin(p2)
    b2 = agent.evaluate(t2)
    assert b2.active_dimensions == ["academic", "discipline"]
    assert b2.evidence_coverage_ratio == 0.50
    assert b2.is_insufficient_evidence is False
    assert b2.is_unscored is False
    assert b2.evidence_tier == "partial"
    assert b2.composite_preference_score == 1.0
    assert not any("insufficient preference evidence" in w.lower() for w in b2.warnings)

    # Case 3: 1 active dimension (academic only)
    p3 = {
        "student_id": "STUDENT_CASE_3",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "preferred_disciplines": [],
        "career_goals": [],
        "preferred_locations": [],
        "total_budget_inr": 800000.0,
    }
    t3 = twin_agent.construct_twin(p3)
    b3 = agent.evaluate(t3)
    assert b3.active_dimensions == ["academic"]
    assert b3.evidence_coverage_ratio == 0.25
    assert b3.is_insufficient_evidence is True
    assert b3.is_unscored is False
    assert b3.evidence_tier == "exploratory"
    assert b3.composite_preference_score == 1.0
    assert any("insufficient preference evidence" in w.lower() for w in b3.warnings)

    # Case 4: 0 active dimensions (empty profile) -> Strictly UNSCORED
    p4 = {
        "student_id": "STUDENT_CASE_4",
        "subject_scores": [],
        "preferred_disciplines": [],
        "career_goals": [],
        "preferred_locations": [],
        "total_budget_inr": 800000.0,
    }
    t4 = twin_agent.construct_twin(p4)
    b4 = agent.evaluate(t4)
    assert b4.active_dimensions == []
    assert b4.evidence_coverage_ratio == 0.0
    assert b4.is_insufficient_evidence is True
    assert b4.is_unscored is True
    assert b4.evidence_tier == "unscored"
    assert b4.composite_preference_score is None  # No numerical score assigned
    assert b4.neutral_baseline_display == 0.50  # Display-only metadata
    assert any("unscored" in w.lower() for w in b4.warnings)

    # Verify complete pipeline through AuctionService and DTO serialization for Case 4 (unscored)
    auction_res = auction_service.run_auction([b4])
    dict_repr = auction_res.to_dict()
    from app.api.schemas.franchise import AuctionResultDto
    dto = AuctionResultDto(**dict_repr)
    assert len(dto.ranked_bids) == 1
    ranked_bid = dto.ranked_bids[0].bid
    assert ranked_bid.is_insufficient_evidence is True
    assert ranked_bid.is_unscored is True
    assert ranked_bid.composite_preference_score is None
    assert ranked_bid.evidence_tier == "unscored"
    assert ranked_bid.neutral_baseline_display == 0.50
    assert "unscored" in dto.ranked_bids[0].explanation.lower()


