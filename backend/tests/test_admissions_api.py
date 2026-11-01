"""API integration tests for Admissions Knowledge Base endpoints (Phase 3)."""

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_1_get_data_sources_list(client):
    """GET /api/v1/data-sources returns all registered sources with provenance classifications."""
    response = client.get("/api/v1/data-sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5

    source_ids = [s["source_id"] for s in data]
    assert "SRC_JEEADV_2026_ELIGIBILITY" in source_ids
    assert "SRC_JOSAA_SYNTHETIC_FIXTURE_2026" in source_ids
    assert "SRC_JOSAA_2026_ORCR" in source_ids

    # Verify official source fields
    jeeadv_source = next(s for s in data if s["source_id"] == "SRC_JEEADV_2026_ELIGIBILITY")
    assert jeeadv_source["source_status"] == "official_source"
    assert jeeadv_source["sha256_checksum"] is not None
    assert len(jeeadv_source["sha256_checksum"]) == 64
    assert jeeadv_source["retrieval_timestamp"] is not None

    # Verify synthetic demo fixture source fields
    josaa_fixture = next(s for s in data if s["source_id"] == "SRC_JOSAA_SYNTHETIC_FIXTURE_2026")
    assert josaa_fixture["source_status"] == "synthetic_demo"
    assert "synthetic" in josaa_fixture["source_id"].lower()


def test_2_get_data_source_by_id(client):
    """GET /api/v1/data-sources/{source_id} returns the specific source or 404."""
    response = client.get("/api/v1/data-sources/SRC_JEEADV_2026_ELIGIBILITY")
    assert response.status_code == 200
    doc = response.json()
    assert doc["source_id"] == "SRC_JEEADV_2026_ELIGIBILITY"
    assert "JEE (Advanced)" in doc["title"]

    # Unknown source returns 404
    resp_404 = client.get("/api/v1/data-sources/NONEXISTENT_SOURCE_ID")
    assert resp_404.status_code == 404


def test_3_get_data_source_snapshots(client):
    """GET /api/v1/data-sources/{source_id}/snapshots returns associated snapshots."""
    response = client.get("/api/v1/data-sources/SRC_JEEADV_2026_ELIGIBILITY/snapshots")
    assert response.status_code == 200
    snapshots = response.json()
    assert isinstance(snapshots, list)
    assert len(snapshots) >= 1
    assert "SNAP_JEEADV_ELIGIBILITY" in snapshots[0]["snapshot_id"]
    assert snapshots[0]["validation_status"] == "valid"


def test_4_get_historical_cutoffs_endpoint(client):
    """GET /api/v1/admissions/cutoffs returns paginated historical observations with disclaimer."""
    response = client.get("/api/v1/admissions/cutoffs?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "results" in data
    assert "disclaimer" in data
    assert "Historical cutoff observations describe past counselling outcomes" in data["disclaimer"]
    assert len(data["results"]) <= 10
    assert len(data["results"]) > 0

    top_cutoff = data["results"][0]
    assert "opening_rank" in top_cutoff
    assert "closing_rank" in top_cutoff
    assert "source_row_provenance" in top_cutoff
    assert top_cutoff["is_synthetic"] is True
    assert top_cutoff["source_status"] == "synthetic_demo"
    assert top_cutoff["source_document_id"] == "SRC_JOSAA_SYNTHETIC_FIXTURE_2026"


def test_5_get_historical_cutoffs_filters(client):
    """GET /api/v1/admissions/cutoffs filters accurately by seat_type and institution."""
    response = client.get("/api/v1/admissions/cutoffs?institution=Bombay&seat_type=OPEN")
    assert response.status_code == 200
    data = response.json()
    for item in data["results"]:
        assert "Bombay" in item["institution_name"]
        assert item["seat_type"] == "OPEN"
        assert item["rank_basis"] == "CRL"


def test_6_get_admissions_programmes(client):
    """GET /api/v1/admissions/programmes returns derived programme offerings."""
    response = client.get("/api/v1/admissions/programmes")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] > 0
    assert len(data["results"]) > 0
    prog = data["results"][0]
    assert "programme_id" in prog
    assert "official_title" in prog
    assert "institution_id" in prog


def test_7_get_eligibility_criteria(client):
    """GET /api/v1/admissions/eligibility-criteria returns formal verified criteria."""
    response = client.get("/api/v1/admissions/eligibility-criteria?academic_year=2026")
    assert response.status_code == 200
    criteria = response.json()
    assert isinstance(criteria, list)
    assert len(criteria) == 5

    crit_titles = [c["title"] for c in criteria]
    assert any("Performance in JEE" in t for t in crit_titles)
    assert any("Age Limit" in t for t in crit_titles)
    assert any("Number of attempts" in t for t in crit_titles)
    assert all(c["is_mandatory"] is True for c in criteria)
    assert all(c["source_status"] == "official_source" for c in criteria)
    assert all(c["criterion_scope"] == "exam_appearance_eligibility" for c in criteria)
    assert all(c["target_examination"] == "JEE (Advanced)" for c in criteria)


def test_8_phase_1_and_2_canonical_endpoints_preserved(client):
    """Canonical endpoints (health, catalogue, recommendations) remain completely functional."""
    # 1. Health
    h_resp = client.get("/api/health")
    assert h_resp.status_code == 200
    assert h_resp.json()["status"] == "ok"

    # 2. Synthetic catalogue
    prog_resp = client.get("/api/v1/programmes")
    assert prog_resp.status_code == 200
    assert len(prog_resp.json()) == 4

    # 3. Recommendation evaluation
    payload = {
        "student_id": "REGRESSION_TEST_STU",
        "subject_scores": [
            {"subject_code": "BIO", "subject_name": "Biology", "score": 80.0},
            {"subject_code": "CHEM", "subject_name": "Chemistry", "score": 80.0},
        ],
        "total_budget_inr": 600000,
        "preferred_disciplines": ["Biotechnology"],
    }
    rec_resp = client.post("/api/v1/recommendations/evaluate", json=payload)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert len(rec_data["evaluations"]) == 4
    bio_eval = next(e for e in rec_data["evaluations"] if e["programme_id"] == "SYNTH_IN_BIO_03")
    assert bio_eval["eligibility_status"] == "eligible"
