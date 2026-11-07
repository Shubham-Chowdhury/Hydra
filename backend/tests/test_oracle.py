"""Comprehensive Verification Test Suite for the Oracle Agent (M005).

Tests:
1. Synthetic source exclusion (guaranteed rejection of synthetic demo rows).
2. Unverified source exclusion.
3. Quarantined row exclusion.
4. Verified record inclusion with checksum and row provenance validation.
5. Deduplication of identical historical observations.
6. Temporal chronological train/test splitting (no future data leakage).
7. Baseline vs. OLS Lag-Regression model evaluation (MAE, median error).
8. Prediction interval calculation ([p10, p90] coverage bounds).
9. Insufficient data status returned honestly when authentic records are lacking.
10. Strict rule isolation: Oracle forecasts are advisory only and never alter eligibility rules.
11. Full API endpoint test coverage (/status, /models, /forecast).
"""

import math
import pytest
from fastapi.testclient import TestClient

from app.agents.oracle_agent import (
    BaselineForecaster,
    DataReadinessValidator,
    LagRegressionForecaster,
    OracleAgent,
)
from app.domain.admissions import AdmissionCutoffObservation
from app.domain.oracle import ForecastTarget, OracleStatus, RejectionReason
from app.domain.provenance import SourceDocument, SourceStatus, ValidationStatus
from app.knowledge.provenance_registry import ProvenanceRegistry
from app.main import app


@pytest.fixture
def mock_registry() -> ProvenanceRegistry:
    """Fixture providing a mock ProvenanceRegistry with official and synthetic documents."""
    registry = ProvenanceRegistry()
    official_doc = SourceDocument(
        source_id="SRC_OFFICIAL_TEST_CUTOFFS",
        title="Official Historical Cutoffs 2023-2025",
        issuing_authority="Joint Seat Allocation Authority",
        canonical_url="https://josaa.nic.in/orcr-official.pdf",
        source_type="pdf",
        academic_year=2025,
        retrieval_timestamp="2026-10-30T10:00:00Z",
        source_status=SourceStatus.OFFICIAL_SOURCE,
        sha256_checksum="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    )
    synthetic_doc = SourceDocument(
        source_id="SRC_SYNTHETIC_DEMO",
        title="Synthetic Fixture",
        issuing_authority="Test Fixture",
        canonical_url="https://demo.local/cutoffs.csv",
        source_type="csv",
        academic_year=2026,
        retrieval_timestamp="2026-10-30T10:00:00Z",
        source_status=SourceStatus.SYNTHETIC_DEMO,
        sha256_checksum="123456abcdef123456abcdef123456abcdef123456abcdef123456abcdef123456",
    )
    registry.register_source(official_doc)
    registry.register_source(synthetic_doc)
    return registry


@pytest.fixture
def synthetic_observations() -> list[AdmissionCutoffObservation]:
    """Generates synthetic cutoff observations that must be rejected."""
    return [
        AdmissionCutoffObservation(
            observation_id=f"CUTOFF_SYNTH_{i}",
            institution_id="INST_DEMO_TECH",
            programme_id="PROG_CS_4YR",
            institution_name="Demo Institute of Technology",
            programme_title="Computer Science and Engineering",
            academic_year=2026,
            counselling_round=1,
            exam_name="JEE Advanced",
            quota="AI",
            seat_type="OPEN",
            gender_pool="Gender-Neutral",
            opening_rank=100 + i * 10,
            closing_rank=500 + i * 20,
            rank_basis="CRL",
            source_document_id="SRC_SYNTHETIC_DEMO",
            snapshot_id="SNAP_SYNTH_001",
            source_row_provenance=f"row_{i}",
            source_status=SourceStatus.SYNTHETIC_DEMO,
            is_synthetic=True,
        )
        for i in range(5)
    ]


@pytest.fixture
def verified_multiyear_observations() -> list[AdmissionCutoffObservation]:
    """Generates valid multi-year verified cutoff records for testing forecasting models."""
    observations = []
    # 2023, 2024, 2025 data points
    data_points = [
        # (year, round, open, close)
        (2023, 1, 100, 320),
        (2023, 2, 321, 350),
        (2024, 1, 105, 335),
        (2024, 2, 336, 365),
        (2025, 1, 110, 348),
        (2025, 2, 349, 380),
    ]
    for i, (yr, rnd, o_rank, c_rank) in enumerate(data_points):
        observations.append(
            AdmissionCutoffObservation(
                observation_id=f"CUTOFF_OFFICIAL_{yr}_R{rnd}",
                institution_id="INST_DEMO_TECH",
                programme_id="PROG_CS_4YR",
                institution_name="Demo Institute of Technology",
                programme_title="Computer Science and Engineering",
                academic_year=yr,
                counselling_round=rnd,
                exam_name="JEE Advanced",
                quota="AI",
                seat_type="OPEN",
                gender_pool="Gender-Neutral",
                opening_rank=o_rank,
                closing_rank=c_rank,
                rank_basis="CRL",
                source_document_id="SRC_OFFICIAL_TEST_CUTOFFS",
                snapshot_id="SNAP_OFFICIAL_001",
                source_row_provenance=f"page_4_row_{i+1}",
                source_status=SourceStatus.OFFICIAL_SOURCE,
                validation_status=ValidationStatus.VALID,
                is_synthetic=False,
            )
        )
    return observations


def test_1_synthetic_records_strictly_excluded(mock_registry, synthetic_observations):
    """Verifies that DataReadinessValidator excludes 100% of synthetic records."""
    validator = DataReadinessValidator(registry=mock_registry)
    eligible, report = validator.validate(synthetic_observations)

    assert len(eligible) == 0
    assert report.total_records_inspected == 5
    assert report.rejected_records_count == 5
    assert report.rejections_by_reason[RejectionReason.SYNTHETIC_DEMO_REJECTED.value] == 5
    assert report.status == OracleStatus.INSUFFICIENT_VERIFIED_DATA


def test_2_unverified_and_quarantined_records_excluded(mock_registry):
    """Verifies that unverified source documents or quarantined records are rejected."""
    bad_observations = [
        # Unverified source
        AdmissionCutoffObservation(
            observation_id="CUTOFF_UNVERIFIED_1",
            institution_id="INST_DEMO",
            programme_id="PROG_DEMO",
            institution_name="Demo",
            programme_title="CS",
            academic_year=2024,
            counselling_round=1,
            exam_name="JEE Advanced",
            quota="AI",
            seat_type="OPEN",
            gender_pool="Gender-Neutral",
            opening_rank=100,
            closing_rank=200,
            rank_basis="CRL",
            source_document_id="SRC_UNKNOWN",
            snapshot_id="SNAP_1",
            source_row_provenance="row_1",
            source_status=SourceStatus.UNVERIFIED,
            is_synthetic=False,
        ),
        # Quarantined / invalid validation
        AdmissionCutoffObservation(
            observation_id="CUTOFF_QUARANTINED_1",
            institution_id="INST_DEMO",
            programme_id="PROG_DEMO",
            institution_name="Demo",
            programme_title="CS",
            academic_year=2024,
            counselling_round=1,
            exam_name="JEE Advanced",
            quota="AI",
            seat_type="OPEN",
            gender_pool="Gender-Neutral",
            opening_rank=100,
            closing_rank=200,
            rank_basis="CRL",
            source_document_id="SRC_OFFICIAL_TEST_CUTOFFS",
            snapshot_id="SNAP_1",
            source_row_provenance="row_2",
            source_status=SourceStatus.OFFICIAL_SOURCE,
            validation_status=ValidationStatus.QUARANTINED,
            is_synthetic=False,
        ),
    ]
    validator = DataReadinessValidator(registry=mock_registry)
    eligible, report = validator.validate(bad_observations)

    assert len(eligible) == 0
    assert report.rejected_records_count == 2
    assert report.status == OracleStatus.INSUFFICIENT_VERIFIED_DATA


def test_3_verified_records_included_and_deduplicated(mock_registry, verified_multiyear_observations):
    """Verifies that genuine verified records pass and exact duplicates are filtered."""
    validator = DataReadinessValidator(registry=mock_registry)
    # Add a duplicate of record 0
    duplicate_obs = verified_multiyear_observations + [verified_multiyear_observations[0]]
    eligible, report = validator.validate(duplicate_obs)

    assert len(eligible) == 6
    assert report.rejections_by_reason.get(RejectionReason.DUPLICATE_OBSERVATION.value, 0) == 1
    assert report.status == OracleStatus.READY
    assert len(report.eligible_academic_years) == 3


def test_4_temporal_chronological_split_and_evaluation(mock_registry, verified_multiyear_observations):
    """Verifies temporal splitting (earlier years train, latest year test) and metrics computation."""
    forecaster = LagRegressionForecaster()
    success, metrics = forecaster.train_and_evaluate(verified_multiyear_observations)

    assert success is True
    assert metrics is not None
    assert metrics.train_samples == 4  # 2023, 2024
    assert metrics.test_samples == 2   # 2025
    assert metrics.mae >= 0.0
    assert metrics.interval_coverage >= 0.0
    assert forecaster.is_trained is True


def test_5_prediction_intervals_and_baseline_comparison(mock_registry, verified_multiyear_observations):
    """Verifies forecast generation with [p10, p90] intervals and baseline comparison."""
    agent = OracleAgent(registry=mock_registry)
    success, report, metrics = agent.train_models(verified_multiyear_observations)
    assert success is True
    assert report.status == OracleStatus.READY

    target = ForecastTarget(
        institution_id="INST_DEMO_TECH",
        programme_id="PROG_CS_4YR",
        future_academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CRL",
    )
    forecast = agent.forecast(verified_multiyear_observations, target)

    assert forecast.status == OracleStatus.READY
    assert forecast.point_prediction is not None
    assert forecast.interval_p10 is not None
    assert forecast.interval_p90 is not None
    assert forecast.interval_p10 <= forecast.point_prediction <= forecast.interval_p90
    assert forecast.uncertainty_band == round(forecast.interval_p90 - forecast.interval_p10, 1)
    assert forecast.is_estimate is True
    assert "guaranteed" not in forecast.disclaimer.lower() or "never" in forecast.disclaimer.lower()


def test_6_insufficient_data_status_refuses_fake_forecast(mock_registry, synthetic_observations):
    """Verifies Oracle refuses to produce synthetic point estimates when only demo data is present."""
    agent = OracleAgent(registry=mock_registry)
    target = ForecastTarget(
        institution_id="INST_DEMO_TECH",
        programme_id="PROG_CS_4YR",
        future_academic_year=2027,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CRL",
    )
    forecast = agent.forecast(synthetic_observations, target)

    assert forecast.status == OracleStatus.INSUFFICIENT_VERIFIED_DATA
    assert forecast.point_prediction is None
    assert forecast.interval_p10 is None
    assert forecast.interval_p90 is None
    assert any("insufficient verified" in w.lower() for w in forecast.warnings)


def test_7_rank_basis_segregation(mock_registry, verified_multiyear_observations):
    """Verifies that requesting a forecast with an incompatible rank basis (e.g. CATEGORY_RANK)

    does not conflate with CRL observations.
    """
    agent = OracleAgent(registry=mock_registry)
    agent.train_models(verified_multiyear_observations)

    target_category_rank = ForecastTarget(
        institution_id="INST_DEMO_TECH",
        programme_id="PROG_CS_4YR",
        future_academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CATEGORY_RANK",  # Not in training data (only CRL was provided)
    )
    forecast = agent.forecast(verified_multiyear_observations, target_category_rank)
    assert forecast.status == OracleStatus.FORECAST_UNAVAILABLE
    assert forecast.point_prediction is None


def test_8_api_status_and_models():
    """Verifies GET /api/v1/oracle/status and GET /api/v1/oracle/models endpoints."""
    client = TestClient(app)

    res_status = client.get("/api/v1/oracle/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert "status" in status_data
    assert "readiness_report" in status_data
    assert "active_model_version" in status_data

    res_models = client.get("/api/v1/oracle/models")
    assert res_models.status_code == 200
    models_data = res_models.json()
    assert len(models_data) >= 2
    assert any(m["model_id"] == "oracle_ols_lag_v1.0.0" for m in models_data)


def test_9_api_forecast_insufficient_data():
    """Verifies POST /api/v1/oracle/forecast returns INSUFFICIENT_VERIFIED_DATA on default repository data."""
    client = TestClient(app)
    payload = {
        "institution_id": "INST_DEMO_TECH",
        "programme_id": "PROG_CS_4YR",
        "future_academic_year": 2027,
        "counselling_round": 1,
        "exam_name": "JEE Advanced",
        "seat_type": "OPEN",
        "quota": "AI",
        "gender_pool": "Gender-Neutral",
        "rank_basis": "CRL",
        "target_type": "closing_rank",
    }
    res = client.post("/api/v1/oracle/forecast", json=payload)
    assert res.status_code == 200
    forecast_data = res.json()
    assert forecast_data["status"] == "INSUFFICIENT_VERIFIED_DATA"
    assert forecast_data["point_prediction"] is None
    assert len(forecast_data["warnings"]) > 0


def test_10_ols_math_known_linear_relationship():
    """Verifies that LagRegressionForecaster._fit_ols recovers exact slope and intercept."""
    forecaster = LagRegressionForecaster()
    # Known ground truth: y = 2.0 * x + 50.0
    x = [10.0, 20.0, 30.0, 40.0, 50.0]
    y = [2.0 * xi + 50.0 for xi in x]

    slope, intercept, residual_std, n, mean_x, var_x = forecaster._fit_ols(x, y)

    assert pytest.approx(slope, abs=1e-5) == 2.0
    assert pytest.approx(intercept, abs=1e-5) == 50.0
    assert n == 5
    assert mean_x == 30.0
    assert var_x == 1000.0
    # Zero residual variance, but bounded to minimum 1.0
    assert residual_std == 1.0


def test_11_prediction_interval_monotonicity(mock_registry, verified_multiyear_observations):
    """Verifies that prediction intervals strictly satisfy p5 <= p10 <= point_prediction <= p90 <= p95."""
    agent = OracleAgent(registry=mock_registry)
    target = ForecastTarget(
        institution_id="INST_DEMO_TECH",
        programme_id="PROG_CS_4YR",
        future_academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CRL",
        target_type="closing_rank",
    )

    forecast = agent.forecast(verified_multiyear_observations, target)
    assert forecast.status == OracleStatus.READY
    assert forecast.point_prediction is not None
    assert forecast.interval_p10 is not None
    assert forecast.interval_p90 is not None
    assert forecast.interval_p5 is not None
    assert forecast.interval_p95 is not None
    assert forecast.prediction_standard_error is not None

    # Strict monotonicity across all percentiles
    assert 1.0 <= forecast.interval_p5 <= forecast.interval_p10 <= forecast.point_prediction <= forecast.interval_p90 <= forecast.interval_p95
    assert forecast.uncertainty_band == pytest.approx(forecast.interval_p90 - forecast.interval_p10, abs=1e-2)


def test_12_ols_prediction_standard_error_leverage():
    """Verifies that OLS prediction standard error accounts for parameter uncertainty:

    s_pred(x0) = s_e * sqrt(1 + 1/n + (x0 - mean_x)^2 / S_xx).
    s_pred(x0) is minimized at x0 = mean_x, and strictly increases as x0 moves away from mean_x.
    """
    forecaster = LagRegressionForecaster()
    x = [100.0, 200.0, 300.0, 400.0, 500.0]
    y = [150.0, 260.0, 340.0, 430.0, 560.0]
    forecaster.slope, forecaster.intercept, forecaster.residual_std, forecaster.train_n, forecaster.mean_x, forecaster.var_x = forecaster._fit_ols(x, y)
    forecaster.is_trained = True

    # At mean_x = 300: leverage is minimized (1 + 1/5)
    s_at_mean = forecaster.compute_prediction_standard_error(300.0)
    assert s_at_mean > forecaster.residual_std

    # Further away from mean: x0 = 800
    s_far = forecaster.compute_prediction_standard_error(800.0)
    assert s_far > s_at_mean


def test_13_prediction_interval_percentile_multipliers(mock_registry, verified_multiyear_observations):
    """Verifies appropriate normal multipliers:

    - [p10, p90] interval uses z_0.10 ~ 1.2816 (80% central interval).
    - [p5, p95] interval uses z_0.05 ~ 1.6449 (90% central interval).
    """
    agent = OracleAgent(registry=mock_registry)
    target = ForecastTarget(
        institution_id="INST_DEMO_TECH",
        programme_id="PROG_CS_4YR",
        future_academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CRL",
        target_type="closing_rank",
    )
    forecast = agent.forecast(verified_multiyear_observations, target)

    # Half width 80% vs 90%
    half_width_80 = forecast.point_prediction - forecast.interval_p10
    half_width_90 = forecast.point_prediction - forecast.interval_p5

    assert half_width_90 > half_width_80
    ratio = half_width_90 / half_width_80
    expected_ratio = forecast.critical_value_p5_p95 / forecast.critical_value_p10_p90
    assert pytest.approx(ratio, rel=0.05) == expected_ratio


def test_14_uncalibrated_holdout_disclosure(mock_registry, verified_multiyear_observations):
    """Verifies that interval is flagged as uncalibrated (is_calibrated=False)
    when holdout sample count is insufficient (n < 50).
    """
    agent = OracleAgent(registry=mock_registry)
    target = ForecastTarget(
        institution_id="INST_DEMO_TECH",
        programme_id="PROG_CS_4YR",
        future_academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CRL",
    )
    forecast = agent.forecast(verified_multiyear_observations, target)
    assert forecast.is_calibrated is False
    assert "insufficient" in forecast.calibration_notes.lower()
    assert forecast.holdout_samples_count == 2
    assert forecast.nominal_coverage_rate == 0.80
    assert forecast.calibration_tolerance == 0.05


def test_15_finite_values_and_lower_boundary_clamping(mock_registry):
    """Verifies that predicted cutoffs and intervals are finite, non-NaN, and clamped at rank >= 1.0."""
    forecaster = LagRegressionForecaster()
    # Pathological case where prediction would be negative without clamping
    forecaster.slope = -1.0
    forecaster.intercept = 10.0
    forecaster.residual_std = 50.0
    forecaster.train_n = 5
    forecaster.mean_x = 10.0
    forecaster.var_x = 100.0
    forecaster.is_trained = True

    obs = [
        AdmissionCutoffObservation(
            observation_id="OBS_1",
            institution_id="INST_DEMO",
            programme_id="PROG_1",
            institution_name="Demo",
            programme_title="Test",
            academic_year=2025,
            counselling_round=1,
            exam_name="JEE Advanced",
            quota="AI",
            seat_type="OPEN",
            gender_pool="Gender-Neutral",
            opening_rank=100,  # 10.0 - 1.0 * 100 = -90.0
            closing_rank=120,
            rank_basis="CRL",
            source_document_id="SRC_DOC",
            snapshot_id="SNAP_1",
            source_row_provenance="r1",
            source_status=SourceStatus.OFFICIAL_SOURCE,
            is_synthetic=False,
        )
    ]
    target = ForecastTarget(
        institution_id="INST_DEMO",
        programme_id="PROG_1",
        future_academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CRL",
    )

    point, p10, p90, p5, p95, s_pred, uncertainty = forecaster.forecast(obs, target)
    assert point >= 1.0
    assert p10 >= 1.0
    assert p5 >= 1.0
    import math
    assert not math.isnan(point)
    assert not math.isinf(point)
    assert not math.isnan(p10)
    assert not math.isnan(p90)
    assert p5 <= p10 <= point <= p90 <= p95


def test_16_wilson_score_interval_mathematics():
    """Verifies Wilson score binomial confidence interval calculation."""
    from app.agents.oracle_agent import compute_wilson_score_interval

    # Case 1: 80 successes out of 100 trials (p_hat = 0.80)
    low, high = compute_wilson_score_interval(80, 100, confidence=0.95)
    assert 0.70 <= low <= 0.73
    assert 0.85 <= high <= 0.88
    assert low <= 0.80 <= high

    # Case 2: Boundary 0 successes out of 50
    low_0, high_0 = compute_wilson_score_interval(0, 50, confidence=0.95)
    assert low_0 == 0.0
    assert 0.0 < high_0 < 0.10

    # Case 3: Boundary 50 successes out of 50
    low_50, high_50 = compute_wilson_score_interval(50, 50, confidence=0.95)
    assert 0.90 < low_50 < 1.0
    assert pytest.approx(high_50, abs=1e-6) == 1.0

    # Case 4: Zero n edge case
    low_z, high_z = compute_wilson_score_interval(0, 0)
    assert (low_z, high_z) == (0.0, 1.0)


def test_17_rigorous_calibration_criteria(mock_registry, verified_multiyear_observations):
    """Verifies that is_calibrated requires holdout n >= 50, coverage within 5% tolerance,
    and Wilson CI containing the nominal coverage rate.
    """
    from app.domain.oracle import EvaluationMetrics

    agent = OracleAgent(registry=mock_registry)
    agent.forecaster.is_trained = True
    agent.forecaster.slope = 1.0
    agent.forecaster.intercept = 10.0
    agent.forecaster.residual_std = 20.0
    agent.forecaster.train_n = 100
    agent.forecaster.mean_x = 500.0
    agent.forecaster.var_x = 10000.0

    target = ForecastTarget(
        institution_id="INST_DEMO_TECH",
        programme_id="PROG_CS_4YR",
        future_academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CRL",
    )

    # Scenario A: n_test = 60, coverage = 0.80 (within tolerance, calibrated)
    agent._cached_metrics = EvaluationMetrics(
        mae=10.0,
        median_absolute_error=8.0,
        baseline_mae=15.0,
        baseline_median_absolute_error=12.0,
        interval_coverage=0.80,
        train_samples=200,
        test_samples=60,
        interval_coverage_p10_p90=0.80,
        interval_coverage_p5_p95=0.90,
        coverage_ci_p10_p90=(0.68, 0.88),
        coverage_ci_p5_p95=(0.80, 0.96),
    )
    fc_cal = agent.forecast(verified_multiyear_observations, target)
    assert fc_cal.is_calibrated is True
    assert "statistically calibrated" in fc_cal.calibration_notes.lower()
    assert fc_cal.holdout_samples_count == 60
    assert fc_cal.empirical_coverage_p10_p90 == 0.80
    assert fc_cal.coverage_confidence_interval == (0.68, 0.88)

    # Scenario B: n_test = 60, coverage = 0.65 (outside 5% tolerance: |0.65 - 0.80| = 0.15 > 0.05)
    agent._cached_metrics = EvaluationMetrics(
        mae=10.0,
        median_absolute_error=8.0,
        baseline_mae=15.0,
        baseline_median_absolute_error=12.0,
        interval_coverage=0.65,
        train_samples=200,
        test_samples=60,
        interval_coverage_p10_p90=0.65,
        interval_coverage_p5_p95=0.75,
        coverage_ci_p10_p90=(0.52, 0.76),
        coverage_ci_p5_p95=(0.63, 0.84),
    )
    fc_uncal = agent.forecast(verified_multiyear_observations, target)
    assert fc_uncal.is_calibrated is False
    assert "deviates from nominal" in fc_uncal.calibration_notes.lower()


def test_18_ols_degrees_of_freedom_and_interval_methodology():
    """Verifies that OLS residual degrees of freedom equals n - 2,
    and that prediction standard error matches mathematical specification.
    """
    forecaster = LagRegressionForecaster()
    x = [10.0, 20.0, 30.0, 40.0, 50.0]
    y = [15.0, 28.0, 32.0, 45.0, 56.0]
    n = len(x)
    assert n == 5

    slope, intercept, s_e, train_n, mean_x, var_x = forecaster._fit_ols(x, y)
    forecaster.slope = slope
    forecaster.intercept = intercept
    forecaster.residual_std = s_e
    forecaster.train_n = train_n
    forecaster.mean_x = mean_x
    forecaster.var_x = var_x
    forecaster.dof = max(1, train_n - 2)
    forecaster.is_trained = True

    # 1. Degrees of freedom check: df = n - 2
    assert forecaster.dof == n - 2
    assert forecaster.dof == 3

    # 2. Residual standard error manual calculation: s_e = sqrt(SSR / df)
    residuals = [yi - (intercept + slope * xi) for xi, yi in zip(x, y)]
    ssr = sum(r**2 for r in residuals)
    expected_se = math.sqrt(ssr / (n - 2))
    assert pytest.approx(s_e, rel=1e-5) == expected_se

    # 3. Prediction standard error check at point x0 = 35.0
    x0 = 35.0
    s_pred = forecaster.compute_prediction_standard_error(x0)
    expected_s_pred = expected_se * math.sqrt(1.0 + 1.0 / n + ((x0 - mean_x) ** 2) / var_x)
    assert pytest.approx(s_pred, rel=1e-5) == expected_s_pred

    # 4. Asymptotic normal multipliers: 80% (z=1.2816) vs 90% (z=1.6449)
    half_80 = 1.2816 * s_pred
    half_90 = 1.6449 * s_pred
    assert half_90 > half_80
    assert pytest.approx(half_90 / half_80, rel=1e-3) == (1.6449 / 1.2816)


def test_19_student_t_and_normal_z_prediction_intervals(mock_registry, verified_multiyear_observations):
    """Verifies finite-sample Student's t critical values vs large-sample normal Z multipliers
    for both p10-p90 and p5-p95 interval calculations, preserving holdout calibration separation.
    """
    from app.agents.oracle_agent import student_t_critical_value, normal_z_critical_value

    # 1. Critical value lookup tests
    assert student_t_critical_value(1, 0.90) == 3.0777
    assert student_t_critical_value(1, 0.95) == 6.3138
    assert student_t_critical_value(2, 0.90) == 1.8856
    assert student_t_critical_value(2, 0.95) == 2.9200
    assert student_t_critical_value(3, 0.90) == 1.6377
    assert student_t_critical_value(3, 0.95) == 2.3534
    assert student_t_critical_value(30, 0.90) == 1.3104
    assert student_t_critical_value(30, 0.95) == 1.6973

    # Large df convergence toward normal Z
    assert pytest.approx(student_t_critical_value(100, 0.90), abs=0.01) == 1.29
    assert pytest.approx(student_t_critical_value(100, 0.95), abs=0.02) == 1.66
    assert normal_z_critical_value(0.90) == 1.2816
    assert normal_z_critical_value(0.95) == 1.6449

    agent = OracleAgent(registry=mock_registry)
    target = ForecastTarget(
        institution_id="INST_DEMO_TECH",
        programme_id="PROG_CS_4YR",
        future_academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        seat_type="OPEN",
        quota="AI",
        gender_pool="Gender-Neutral",
        rank_basis="CRL",
        target_type="closing_rank",
    )

    # 2. Test Student's t prediction interval (default)
    fc_t = agent.forecast(verified_multiyear_observations, target, use_student_t=True)
    assert fc_t.status == OracleStatus.READY
    assert fc_t.interval_type == "student_t_prediction_interval"
    assert fc_t.degrees_of_freedom is not None and fc_t.degrees_of_freedom >= 1
    assert fc_t.critical_value_p10_p90 == student_t_critical_value(fc_t.degrees_of_freedom, 0.90)
    assert fc_t.critical_value_p5_p95 == student_t_critical_value(fc_t.degrees_of_freedom, 0.95)
    # Check ordering: p5 <= p10 <= point <= p90 <= p95
    assert 1.0 <= fc_t.interval_p5 <= fc_t.interval_p10 <= fc_t.point_prediction <= fc_t.interval_p90 <= fc_t.interval_p95
    # Distinct from calibrated
    assert fc_t.is_calibrated is False
    assert "theoretical finite-sample student's t" in fc_t.calibration_notes.lower()

    # 3. Test Normal Z prediction interval (large-sample approximation)
    fc_z = agent.forecast(verified_multiyear_observations, target, use_student_t=False)
    assert fc_z.status == OracleStatus.READY
    assert fc_z.interval_type == "large_sample_normal_z_interval"
    assert fc_z.critical_value_p10_p90 == 1.2816
    assert fc_z.critical_value_p5_p95 == 1.6449
    # Check ordering: p5 <= p10 <= point <= p90 <= p95
    assert 1.0 <= fc_z.interval_p5 <= fc_z.interval_p10 <= fc_z.point_prediction <= fc_z.interval_p90 <= fc_z.interval_p95
    assert fc_z.is_calibrated is False
    assert "large-sample asymptotic normal z" in fc_z.calibration_notes.lower()

    # Student's t interval with small df should be wider than normal Z interval
    width_80_t = fc_t.interval_p90 - fc_t.interval_p10
    width_80_z = fc_z.interval_p90 - fc_z.interval_p10
    assert width_80_t >= width_80_z





