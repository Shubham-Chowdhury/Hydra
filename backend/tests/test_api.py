"""Integration tests for the canonical Hydra API endpoints using FastAPI TestClient."""

from fastapi.testclient import TestClient
import pytest
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_health_endpoint(client: TestClient):
    """Verifies GET /api/health returns ok status and version."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_api_programmes_endpoint(client: TestClient):
    """Verifies GET /api/v1/programmes returns the 4 synthetic demonstration programmes."""
    response = client.get("/api/v1/programmes")
    assert response.status_code == 200
    programmes = response.json()
    assert len(programmes) == 4
    prog_ids = [p["programme_id"] for p in programmes]
    assert "SYNTH_IN_CS_01" in prog_ids
    assert "SYNTH_IN_DS_02" in prog_ids
    assert "SYNTH_IN_BIO_03" in prog_ids
    assert "SYNTH_IN_ROB_04" in prog_ids

    # Verify synthetic provenance flags
    for p in programmes:
        assert p["is_synthetic"] is True
        assert p["dataset_label"] == "SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL"
        assert p["currency"] == "INR"


def test_api_recommendations_evaluate_valid(client: TestClient):
    """Verifies POST /api/v1/recommendations/evaluate processes valid student profile."""
    payload = {
        "student_id": "TEST_STU_100",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 88.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 78.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 82.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 18000,
        "preferred_locations": ["Karnataka", "Maharashtra"],
        "total_budget_inr": 800000.0,
        "preferred_disciplines": ["Computer Science", "Data Science"],
        "career_goals": ["Software Engineer", "Data Scientist"],
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["is_synthetic"] is True
    assert "audit_timestamp" in data
    assert len(data["evaluations"]) == 4

    # Check top evaluated programme
    top_eval = data["evaluations"][0]
    assert top_eval["eligibility_status"] in ("eligible", "ineligible", "needs_review")
    assert "affordability" in top_eval
    assert top_eval["affordability"]["currency"] == "INR"
    assert top_eval["affordability"]["cost_basis"] == "tuition_only_total"
    assert "evidence" in top_eval
    assert "rules_fired" in top_eval
    assert len(data["discovered_relationships"]) > 0


def test_api_recommendations_malformed_payload_rejected(client: TestClient):
    """Verifies POST /api/v1/recommendations/evaluate rejects invalid payloads with 422."""
    # Negative score should be rejected
    bad_payload = {
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": -10.0}
        ]
    }
    response = client.post("/api/v1/recommendations/evaluate", json=bad_payload)
    assert response.status_code == 422

    # Negative rank should be rejected
    bad_rank = {
        "subject_scores": [],
        "entrance_rank": 0  # ge=1 required
    }
    response = client.post("/api/v1/recommendations/evaluate", json=bad_rank)
    assert response.status_code == 422


def test_api_timestamp_is_utc_iso8601(client: TestClient):
    """Verifies evaluation response includes a dynamically generated UTC ISO 8601 timestamp."""
    payload = {
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 85.0}
        ]
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    ts = data["audit_timestamp"]
    assert "+00:00" in ts or ts.endswith("Z") or "T" in ts


def test_api_recommendations_ineligible_outcome(client: TestClient):
    """Verifies API correctly flags an applicant with substandard marks as ineligible."""
    payload = {
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 50.0},
            {"subject_code": "ENG", "subject_name": "English", "score": 75.0},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 70.0},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 45000,
        "total_budget_inr": 800000.0,
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    cs_eval = next(e for e in data["evaluations"] if e["programme_id"] == "SYNTH_IN_CS_01")
    assert cs_eval["eligibility_status"] == "ineligible"
    assert any("below the required minimum benchmark" in ev for ev in cs_eval["evidence"])


def test_api_recommendations_needs_review_outcome(client: TestClient):
    """Verifies API returns needs_review when mandatory facts are omitted."""
    payload = {
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0},
            {"subject_code": "ENG", "subject_name": "English", "score": 85.0},
        ],
        "total_budget_inr": 800000.0,
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    cs_eval = next(e for e in data["evaluations"] if e["programme_id"] == "SYNTH_IN_CS_01")
    assert cs_eval["eligibility_status"] == "needs_review"
    assert any("Physics" in mf for mf in cs_eval["missing_facts"])


def test_api_recommendations_eligible_unaffordable_outcome(client: TestClient):
    """Verifies API decouples eligibility from affordability when budget is insufficient."""
    payload = {
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0},
            {"subject_code": "ENG", "subject_name": "English", "score": 85.0},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 15000,
        "total_budget_inr": 100000.0,  # Below tuition of 600,000
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    cs_eval = next(e for e in data["evaluations"] if e["programme_id"] == "SYNTH_IN_CS_01")
    assert cs_eval["eligibility_status"] == "eligible"
    assert cs_eval["affordability"]["is_affordable"] is False
    assert cs_eval["affordability"]["total_budget_inr"] == 100000.0
    assert cs_eval["affordability"]["estimated_total_tuition_inr"] == 600000.0


def test_api_optional_entrance_rank_exceeded_remains_eligible(client: TestClient):
    """Verifies that exceeding an optional entrance cutoff does NOT cause ineligibility over API."""
    payload = {
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0},
            {"subject_code": "PROG", "subject_name": "Programming", "score": 85.0},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 32000,  # Exceeds DS optional cutoff of 25000
        "total_budget_inr": 800000.0,
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    ds_eval = next(e for e in data["evaluations"] if e["programme_id"] == "SYNTH_IN_DS_02")
    assert ds_eval["eligibility_status"] == "eligible"
    assert any("non-mandatory and does not disqualify" in ev.lower() for ev in ds_eval["evidence"])


def test_api_mandatory_entrance_rank_exceeded_is_ineligible(client: TestClient):
    """Verifies that exceeding a mandatory entrance cutoff causes ineligibility over API."""
    payload = {
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0},
            {"subject_code": "ENG", "subject_name": "English", "score": 85.0},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 36000,  # Exceeds CS mandatory cutoff of 35000
        "total_budget_inr": 800000.0,
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    cs_eval = next(e for e in data["evaluations"] if e["programme_id"] == "SYNTH_IN_CS_01")
    assert cs_eval["eligibility_status"] == "ineligible"
    assert any("exceeds mandatory cutoff" in ev.lower() for ev in cs_eval["evidence"])


def test_api_mandatory_entrance_exam_incompatible_is_ineligible(client: TestClient):
    """Verifies that reporting an incompatible entrance exam for a mandatory criterion is ineligible."""
    payload = {
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90.0},
            {"subject_code": "ENG", "subject_name": "English", "score": 85.0},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85.0},
        ],
        "entrance_exam_name": "NEET",  # Incompatible with mandatory JEE Main
        "entrance_rank": 1000,
        "total_budget_inr": 800000.0,
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    cs_eval = next(e for e in data["evaluations"] if e["programme_id"] == "SYNTH_IN_CS_01")
    assert cs_eval["eligibility_status"] == "ineligible"
    assert any("incompatible with required mandatory" in ev.lower() for ev in cs_eval["evidence"])


def test_api_biotechnology_developer_profile_returns_eligible(client: TestClient):
    """Verifies that developer's profile yields eligible for Biotechnology over canonical API.

    Bio 80%, Chem 80%, budget 600k, Telangana, Biotechnology, Biomedical Researcher.
    """
    payload = {
        "student_id": "STU_DEV_BIO_API",
        "subject_scores": [
            {"subject_code": "BIO", "subject_name": "Biology", "score": 80.0, "max_score": 100.0, "grading_scale": "percentage"},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 80.0, "max_score": 100.0, "grading_scale": "percentage"},
        ],
        "total_budget_inr": 600000.0,
        "preferred_locations": ["Telangana"],
        "preferred_disciplines": ["Biotechnology"],
        "career_goals": ["Biomedical Researcher"],
        "certifications": [],
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Biotechnology must be first and eligible
    top_eval = data["evaluations"][0]
    assert top_eval["programme_id"] == "SYNTH_IN_BIO_03"
    assert top_eval["eligibility_status"] == "eligible"
    assert top_eval["affordability"]["is_affordable"] is True
    assert top_eval["affordability"]["total_budget_inr"] == 600000.0
    assert top_eval["affordability"]["estimated_total_tuition_inr"] == 500000.0
    assert top_eval["preference_fit"]["fit_score"] == 1.0
    assert len(top_eval["missing_facts"]) == 0

    # The other 3 programmes must legitimately evaluate to needs_review
    other_evals = [e for e in data["evaluations"] if e["programme_id"] != "SYNTH_IN_BIO_03"]
    assert len(other_evals) == 3
    for ev in other_evals:
        assert ev["eligibility_status"] == "needs_review"
        assert len(ev["missing_facts"]) > 0


def test_api_frontend_payload_structure_and_grading_scale_handled(client: TestClient):
    """Verifies API correctly handles custom score values, max_scores, and grading scales from frontend."""
    payload = {
        "subject_scores": [
            {"subject_code": "BIO", "subject_name": "Biology", "score": 40.0, "max_score": 50.0, "grading_scale": "percentage"},  # 80%
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 160.0, "max_score": 200.0, "grading_scale": "percentage"},  # 80%
        ],
        "total_budget_inr": 600000.0,
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    bio_eval = next(e for e in data["evaluations"] if e["programme_id"] == "SYNTH_IN_BIO_03")
    assert bio_eval["eligibility_status"] == "eligible"


def test_api_phase2_reasoning_tree_and_provenance(client: TestClient):
    """Verifies API returns structured reasoning tree and graph relationship provenance."""
    payload = {
        "subject_scores": [
            {"subject_code": "BIO", "subject_name": "Biology", "score": 85.0},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 82.0},
        ],
        "total_budget_inr": 700000.0,
    }
    response = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    for ev in data["evaluations"]:
        # Verify parent frame ID exists
        assert ev["parent_frame_id"] is not None
        assert ev["parent_frame_id"].startswith("FRAME_")

        # Verify hierarchical reasoning tree structure
        assert ev["reasoning_tree"] is not None
        tree = ev["reasoning_tree"]
        assert "node_id" in tree
        assert "expression_type" in tree
        assert "status" in tree
        assert "children" in tree
        assert isinstance(tree["children"], list)

        # Verify relationship provenance tags
        for rel in ev["discovered_relationships"]:
            assert rel["source_type"] in ("direct", "inherited", "traversed")
            assert isinstance(rel["provenance_path"], list)




