"""Oracle Application Service for Hydra (Phase 5 / M005).

Coordinates data acquisition, data readiness evaluation, model training,
and query execution for the Oracle admissions forecasting subsystem.
"""

from typing import Any, Dict, List, Optional

from app.agents.oracle_agent import OracleAgent
from app.domain.admissions import AdmissionCutoffObservation
from app.domain.oracle import (
    CutoffForecast,
    DataReadinessReport,
    ForecastTarget,
    OracleStatus,
)
from app.knowledge.provenance_registry import ProvenanceRegistry
from app.services.admissions_service import AdmissionsService


class OracleService:
    """Application orchestration service for the Oracle Agent."""

    def __init__(
        self,
        admissions_service: Optional[AdmissionsService] = None,
        registry: Optional[ProvenanceRegistry] = None,
    ) -> None:
        self.admissions_service = admissions_service or AdmissionsService()
        self.registry = registry or self.admissions_service.registry
        self.agent = OracleAgent(registry=self.registry)

    def _get_observations(self) -> List[AdmissionCutoffObservation]:
        """Loads all cutoff observations known to AdmissionsService."""
        all_obs, _ = self.admissions_service.query_cutoffs(limit=10000)
        return all_obs

    def get_status(self) -> Dict[str, Any]:
        """Audits current dataset readiness and reports operational status."""
        observations = self._get_observations()
        report = self.agent.evaluate_readiness(observations)
        return {
            "status": report.status.value,
            "readiness_report": report.to_dict(),
            "active_model_version": self.agent.forecaster.model_version,
            "is_trained": self.agent.forecaster.is_trained,
            "models_available": self.list_models(),
        }

    def forecast(self, target: ForecastTarget) -> CutoffForecast:
        """Executes a cutoff forecast request through the Oracle Agent."""
        observations = self._get_observations()
        return self.agent.forecast(observations, target)

    def list_models(self) -> List[Dict[str, Any]]:
        """Returns catalog of registered Oracle forecasting models and their configurations."""
        return [
            {
                "model_id": "oracle_ols_lag_v1.0.0",
                "name": "Chronological Lag Ordinary Least Squares",
                "type": "transparent_regression",
                "features": ["lag_1_closing_rank", "counselling_round_offset"],
                "prediction_target": "closing_rank",
                "uncertainty_interval": "90% [p10, p90] Gaussian residual interval",
                "is_active": True,
            },
            {
                "model_id": "oracle_historical_median_baseline_v1.0.0",
                "name": "Historical Cohort Median Baseline",
                "type": "non_parametric_baseline",
                "features": ["historical_median_cohort_closing_rank"],
                "prediction_target": "closing_rank",
                "uncertainty_interval": "heuristic +/- 10% band",
                "is_active": True,
            },
        ]

