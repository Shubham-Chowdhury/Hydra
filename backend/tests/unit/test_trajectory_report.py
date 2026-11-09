"""Unit tests for the Deep Trajectory Sequence Model and Comprehensive Assessment Report Service."""

import pytest
from starlette.testclient import TestClient

from app.domain.assessment_report import UserInteractionEvent
from app.main import app
from app.services.assessment_report_service import AssessmentReportService
from app.services.trajectory_model import DeepTrajectorySequenceModel


@pytest.fixture
def sample_profile():
    return {
        "student_id": "STU_TEST_01",
        "subject_scores": [
            {"subject_code": "MATH", "subject_name": "Mathematics", "score": 90, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "PHYS", "subject_name": "Physics", "score": 85, "max_score": 100, "grading_scale": "percentage"},
            {"subject_code": "ENG", "subject_name": "English", "score": 80, "max_score": 100, "grading_scale": "percentage"},
        ],
        "entrance_exam_name": "JEE Main",
        "entrance_rank": 14000,
        "total_budget_inr": 900000,
        "preferred_locations": ["Karnataka", "Maharashtra"],
        "preferred_disciplines": ["Computer Science", "Data Science"],
        "career_goals": ["Software Engineer"],
    }


def test_trajectory_model_feature_extraction(sample_profile):
    model = DeepTrajectorySequenceModel()
    features = model.extract_features(sample_profile)
    assert len(features) == 16
    assert features[0] == 0.9  # Math 90/100
    assert features[1] == 0.85  # Physics 85/100
    assert features[2] == 0.8  # English 80/100
    assert features[3] > 0.0  # Rank percentile


def test_trajectory_model_predict(sample_profile):
    model = DeepTrajectorySequenceModel()
    insights = model.predict(sample_profile)

    assert 0.50 <= insights.career_readiness_score <= 1.0
    assert 0.0 <= insights.risk_assessment_index <= 0.60
    assert insights.is_estimate is True
    assert insights.is_synthetic is True
    assert insights.confidence >= 0.80
    assert len(insights.projected_career_outcomes) > 0

    # Domain affinity distribution
    total_aff = sum(insights.domain_affinity_weights.values())
    assert 0.99 <= total_aff <= 1.01


def test_assessment_report_service_generation(sample_profile):
    service = AssessmentReportService()
    report = service.generate_report(sample_profile)

    assert report.report_id.startswith("REP_")
    assert report.student_id == "STU_TEST_01"
    assert "voice_script" in report.__dataclass_fields__
    assert len(report.voice_script) > 50
    assert report.verified_eligibility_breakdown["total"] > 0
    assert report.verified_eligibility_breakdown["eligible"] >= 0
    assert len(report.top_recommended_pathways) > 0
    assert report.neural_insights.career_readiness_score > 0.5


def test_comprehensive_report_api_endpoint(sample_profile):
    client = TestClient(app)
    response = client.post(
        "/api/v1/assessment/comprehensive-report",
        json={"profile": sample_profile},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert "voice_script" in data
    assert "neural_insights" in data
    assert data["neural_insights"]["career_readiness_score"] > 0.5
    assert data["neural_insights"]["is_estimate"] is True

