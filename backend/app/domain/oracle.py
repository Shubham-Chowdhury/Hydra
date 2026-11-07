"""Oracle Agent Domain Models for Hydra (Phase 5 / M005).

Defines data readiness, forecast target specifications, uncertainty intervals,
model evaluation metrics, and advisory cutoff forecast structures.

CRITICAL ARCHITECTURAL DIRECTIVES:
1. Honest Provenance: Only verified official records can enter training pipelines.
   Synthetic demonstration fixtures and unverified sources are strictly excluded.
2. Advisory Exclusivity: Oracle forecasts are probabilistic estimates and must NEVER
   override, bypass, or be inserted into deterministic eligibility AST rules.
3. No Fake Predictions: If verified historical data is insufficient, Oracle returns
   an explicit INSUFFICIENT_VERIFIED_DATA status with full diagnostic explanation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class OracleStatus(str, Enum):
    """Operational status of the Oracle forecasting subsystem."""

    READY = "READY"
    INSUFFICIENT_VERIFIED_DATA = "INSUFFICIENT_VERIFIED_DATA"
    MODEL_NOT_TRAINED = "MODEL_NOT_TRAINED"
    MODEL_VALIDATION_FAILED = "MODEL_VALIDATION_FAILED"
    FORECAST_UNAVAILABLE = "FORECAST_UNAVAILABLE"


class RejectionReason(str, Enum):
    """Specific reasons for rejecting observations from the training pipeline."""

    SYNTHETIC_DEMO_REJECTED = "synthetic_demo_rejected"
    UNVERIFIED_SOURCE_REJECTED = "unverified_source_rejected"
    QUARANTINED_RECORD_REJECTED = "quarantined_record_rejected"
    SOURCE_DOCUMENT_NOT_FOUND = "source_document_not_found"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    MISSING_ROW_PROVENANCE = "missing_row_provenance"
    INVALID_RANK_BOUNDS = "invalid_rank_bounds"
    INCOMPATIBLE_RANK_BASIS = "incompatible_rank_basis"
    UNRESOLVED_IDENTITY = "unresolved_identity"
    DUPLICATE_OBSERVATION = "duplicate_observation"


@dataclass(frozen=True)
class ForecastTarget:
    """Exact specification of an academic admissions cutoff forecast query."""

    institution_id: str
    programme_id: str
    future_academic_year: int
    counselling_round: int
    exam_name: str
    seat_type: str  # e.g., "OPEN", "OBC-NCL", "SC", "ST", "GEN-EWS"
    quota: str  # e.g., "AI", "HS", "OS"
    gender_pool: str  # e.g., "Gender-Neutral", "Female-only (including Supernumerary)"
    rank_basis: str  # "CRL", "CATEGORY_RANK"
    target_type: str = "closing_rank"  # "closing_rank", "opening_rank", "rank_range"

    def __post_init__(self) -> None:
        if self.future_academic_year < 2020:
            raise ValueError(f"Invalid future academic year: {self.future_academic_year}")
        if self.counselling_round < 1:
            raise ValueError(f"Invalid counselling round: {self.counselling_round}")
        if not self.institution_id or not self.programme_id:
            raise ValueError("Institution and Programme IDs are mandatory.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "institution_id": self.institution_id,
            "programme_id": self.programme_id,
            "future_academic_year": self.future_academic_year,
            "counselling_round": self.counselling_round,
            "exam_name": self.exam_name,
            "seat_type": self.seat_type,
            "quota": self.quota,
            "gender_pool": self.gender_pool,
            "rank_basis": self.rank_basis,
            "target_type": self.target_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForecastTarget":
        return cls(
            institution_id=data["institution_id"],
            programme_id=data["programme_id"],
            future_academic_year=int(data["future_academic_year"]),
            counselling_round=int(data.get("counselling_round", 1)),
            exam_name=data.get("exam_name", "JEE Advanced"),
            seat_type=data.get("seat_type", "OPEN"),
            quota=data.get("quota", "AI"),
            gender_pool=data.get("gender_pool", "Gender-Neutral"),
            rank_basis=data.get("rank_basis", "CRL"),
            target_type=data.get("target_type", "closing_rank"),
        )


@dataclass(frozen=True)
class DataReadinessReport:
    """Audit report from the Data Readiness Pipeline inspecting cutoff records."""

    total_records_inspected: int
    eligible_records_count: int
    rejected_records_count: int
    rejections_by_reason: Dict[str, int]
    eligible_academic_years: List[int]
    verified_sources_used: List[str]
    status: OracleStatus
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records_inspected": self.total_records_inspected,
            "eligible_records_count": self.eligible_records_count,
            "rejected_records_count": self.rejected_records_count,
            "rejections_by_reason": self.rejections_by_reason,
            "eligible_academic_years": list(self.eligible_academic_years),
            "verified_sources_used": list(self.verified_sources_used),
            "status": self.status.value,
            "message": self.message,
        }


@dataclass(frozen=True)
class EvaluationMetrics:
    """Performance evaluation of a forecasting model against temporal holdout data."""

    mae: float
    median_absolute_error: float
    baseline_mae: float
    baseline_median_absolute_error: float
    interval_coverage: float  # Percentage of ground truth inside [p10, p90]
    train_samples: int
    test_samples: int
    interval_coverage_p10_p90: float = 0.0
    interval_coverage_p5_p95: float = 0.0
    coverage_ci_p10_p90: Tuple[float, float] = (0.0, 0.0)
    coverage_ci_p5_p95: Tuple[float, float] = (0.0, 0.0)
    nominal_coverage_p10_p90: float = 0.80
    nominal_coverage_p5_p95: float = 0.90

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mae": round(self.mae, 2),
            "median_absolute_error": round(self.median_absolute_error, 2),
            "baseline_mae": round(self.baseline_mae, 2),
            "baseline_median_absolute_error": round(self.baseline_median_absolute_error, 2),
            "interval_coverage": round(self.interval_coverage, 4),
            "interval_coverage_p10_p90": round(self.interval_coverage_p10_p90, 4),
            "interval_coverage_p5_p95": round(self.interval_coverage_p5_p95, 4),
            "coverage_ci_p10_p90": [round(x, 4) for x in self.coverage_ci_p10_p90],
            "coverage_ci_p5_p95": [round(x, 4) for x in self.coverage_ci_p5_p95],
            "nominal_coverage_p10_p90": self.nominal_coverage_p10_p90,
            "nominal_coverage_p5_p95": self.nominal_coverage_p5_p95,
            "train_samples": self.train_samples,
            "test_samples": self.test_samples,
        }


@dataclass(frozen=True)
class CutoffForecast:
    """Structured advisory cutoff forecast produced by the Oracle Agent.

    MATHEMATICAL STATISTICAL DISTINCTIONS:
    - Prediction Interval (PI) vs. Confidence Interval (CI):
      A Confidence Interval estimates the uncertainty of the population mean response E[Y|X=x0],
      accounting only for parameter estimation variance: s_conf = s_e * sqrt(1/n + (x0 - x_bar)^2 / S_xx).
      A Prediction Interval estimates the uncertainty of a single future realization Y0 at x0,
      incorporating both parameter estimation variance AND individual observation variance (+1):
      s_pred = s_e * sqrt(1 + 1/n + (x0 - x_bar)^2 / S_xx).
    - Under a Gaussian residual assumption N(0, s_pred^2):
      An 80% symmetric interval [p10, p90] uses critical value z_0.10 = 1.2816.
      A 90% symmetric interval [p5, p95] uses critical value z_0.05 = 1.6449.
    - Calibration Status:
      An interval is ONLY marked 'is_calibrated: True' if validated across empirical chronological
      holdout samples (n >= 50) with empirical coverage matching nominal rate within tolerance (0.05)
      and nominal rate falling within the 95% Wilson score binomial confidence interval.
    """

    target: ForecastTarget
    status: OracleStatus
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
    calibration_notes: str = (
        "Finite-sample theoretical prediction interval using Student's t critical values (df = n - 2) "
        "under Gaussian residual assumption. Theoretical intervals remain distinct from empirically calibrated intervals; "
        "holdout calibration requires verified admissions records (n >= 50) and Wilson score binomial coverage verification."
    )
    holdout_samples_count: Optional[int] = None
    empirical_coverage_p10_p90: Optional[float] = None
    empirical_coverage_p5_p95: Optional[float] = None
    coverage_confidence_interval: Optional[Tuple[float, float]] = None
    nominal_coverage_rate: float = 0.80
    calibration_tolerance: float = 0.05
    model_version: str = "oracle_ols_lag_v1.0.0"
    training_snapshot_id: Optional[str] = None
    training_records_count: int = 0
    training_date: Optional[str] = None
    features_used: List[str] = field(default_factory=list)
    metrics: Optional[EvaluationMetrics] = None
    is_estimate: bool = True
    confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = (
        "Advisory forecast only. Admission cutoffs fluctuate annually based on candidate pool dynamics. "
        "Forecasts MUST NEVER be used as guaranteed admission criteria or formal eligibility prerequisites."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target.to_dict(),
            "status": self.status.value,
            "point_prediction": self.point_prediction,
            "interval_p10": self.interval_p10,
            "interval_p90": self.interval_p90,
            "interval_p5": self.interval_p5,
            "interval_p95": self.interval_p95,
            "prediction_standard_error": self.prediction_standard_error,
            "uncertainty_band": self.uncertainty_band,
            "critical_value_p10_p90": self.critical_value_p10_p90,
            "critical_value_p5_p95": self.critical_value_p5_p95,
            "degrees_of_freedom": self.degrees_of_freedom,
            "interval_type": self.interval_type,
            "is_calibrated": self.is_calibrated,
            "calibration_notes": self.calibration_notes,
            "holdout_samples_count": self.holdout_samples_count,
            "empirical_coverage_p10_p90": self.empirical_coverage_p10_p90,
            "empirical_coverage_p5_p95": self.empirical_coverage_p5_p95,
            "coverage_confidence_interval": (
                [round(x, 4) for x in self.coverage_confidence_interval]
                if self.coverage_confidence_interval
                else None
            ),
            "nominal_coverage_rate": self.nominal_coverage_rate,
            "calibration_tolerance": self.calibration_tolerance,
            "model_version": self.model_version,
            "training_snapshot_id": self.training_snapshot_id,
            "training_records_count": self.training_records_count,
            "training_date": self.training_date,
            "features_used": list(self.features_used),
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "is_estimate": self.is_estimate,
            "confidence": self.confidence,
            "warnings": list(self.warnings),
            "disclaimer": self.disclaimer,
        }

