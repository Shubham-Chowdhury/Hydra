"""Pydantic Transport Schemas for the Oracle Subsystem (M005)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ForecastTargetRequest(BaseModel):
    """API request payload for querying an admissions cutoff forecast."""

    institution_id: str = Field(..., description="Target higher-education institution ID")
    programme_id: str = Field(..., description="Target academic programme ID")
    future_academic_year: int = Field(2027, description="Target future academic year for forecasting")
    counselling_round: int = Field(1, description="Counselling round number")
    exam_name: str = Field("JEE Advanced", description="Qualifying entrance examination")
    seat_type: str = Field("OPEN", description="Seat allocation category (OPEN, OBC-NCL, SC, etc.)")
    quota: str = Field("AI", description="Allocation quota (AI, HS, OS)")
    gender_pool: str = Field("Gender-Neutral", description="Gender pool allocation")
    rank_basis: str = Field("CRL", description="Ranking basis (CRL, CATEGORY_RANK)")
    target_type: str = Field("closing_rank", description="Forecast target: closing_rank, opening_rank, rank_range")


class EvaluationMetricsResponse(BaseModel):
    """Evaluation metrics for the trained forecast model."""

    mae: float
    median_absolute_error: float
    baseline_mae: float
    baseline_median_absolute_error: float
    interval_coverage: float
    train_samples: int
    test_samples: int
    interval_coverage_p10_p90: Optional[float] = None
    interval_coverage_p5_p95: Optional[float] = None
    coverage_ci_p10_p90: Optional[List[float]] = None
    coverage_ci_p5_p95: Optional[List[float]] = None
    nominal_coverage_p10_p90: float = 0.80
    nominal_coverage_p5_p95: float = 0.90


class CutoffForecastResponse(BaseModel):
    """API response model containing an advisory cutoff forecast with uncertainty."""

    target: Dict[str, Any]
    status: str
    point_prediction: Optional[float] = None
    interval_p10: Optional[float] = None
    interval_p90: Optional[float] = None
    interval_p5: Optional[float] = None
    interval_p95: Optional[float] = None
    prediction_standard_error: Optional[float] = None
    uncertainty_band: Optional[float] = None
    critical_value_p10_p90: Optional[float] = None
    critical_value_p5_p95: Optional[float] = None
    degrees_of_freedom: Optional[int] = None
    interval_type: str = "student_t_prediction_interval"
    is_calibrated: bool = False
    calibration_notes: str = ""
    holdout_samples_count: Optional[int] = None
    empirical_coverage_p10_p90: Optional[float] = None
    empirical_coverage_p5_p95: Optional[float] = None
    coverage_confidence_interval: Optional[List[float]] = None
    nominal_coverage_rate: float = 0.80
    calibration_tolerance: float = 0.05
    model_version: str
    training_snapshot_id: Optional[str] = None
    training_records_count: int
    training_date: Optional[str] = None
    features_used: List[str]
    metrics: Optional[EvaluationMetricsResponse] = None
    is_estimate: bool = True
    confidence: float = 0.0
    warnings: List[str]
    disclaimer: str


class DataReadinessReportResponse(BaseModel):
    """Audit summary of observations inspected for training readiness."""

    total_records_inspected: int
    eligible_records_count: int
    rejected_records_count: int
    rejections_by_reason: Dict[str, int]
    eligible_academic_years: List[int]
    verified_sources_used: List[str]
    status: str
    message: str


class OracleStatusResponse(BaseModel):
    """Overall status and data readiness diagnostic for the Oracle subsystem."""

    status: str
    readiness_report: DataReadinessReportResponse
    active_model_version: str
    is_trained: bool
    models_available: List[Dict[str, Any]]

