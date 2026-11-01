"""Admissions Knowledge Query Service for Hydra (Phase 3).

Provides provenance-aware querying of authoritative admissions data, historical cutoff
observations, dataset snapshots, and verified eligibility rules.

CRITICAL ARCHITECTURAL DIRECTIVE:
Historical cutoffs are queryable historical observations only. They are NEVER converted
into mandatory student eligibility prerequisites and NEVER conflated with predictive estimates.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.domain.admissions import (
    AcademicProgrammeRecord,
    AdmissionCutoffObservation,
    FormalEligibilityCriterion,
    Institution,
)
from app.domain.provenance import DatasetSnapshot, SourceDocument, SourceStatus
from app.knowledge.provenance_registry import ProvenanceRegistry


class AdmissionsService:
    """Read-only query service for the Admissions Knowledge Base."""

    def __init__(
        self,
        registry: Optional[ProvenanceRegistry] = None,
        data_dir: Optional[Path] = None,
    ) -> None:
        self.registry = registry or ProvenanceRegistry()
        self.data_dir = data_dir or Path("data")
        self.normalized_josaa_dir = self.data_dir / "normalized" / "josaa"
        self.normalized_jeeadv_dir = self.data_dir / "normalized" / "jeeadv" / "2026"
        self._cached_cutoffs: Optional[List[AdmissionCutoffObservation]] = None
        self._cached_criteria: Optional[List[FormalEligibilityCriterion]] = None

    def list_sources(self, status: Optional[str] = None) -> List[SourceDocument]:
        """Returns registered sources, optionally filtered by SourceStatus."""
        sources = self.registry.list_sources()
        if status:
            target_status = status.lower()
            sources = [s for s in sources if s.source_status.value.lower() == target_status]
        return sources

    def get_source(self, source_id: str) -> Optional[SourceDocument]:
        """Retrieves a single source document by ID."""
        return self.registry.get_source(source_id)

    def list_snapshots(self, dataset_id: Optional[str] = None) -> List[DatasetSnapshot]:
        """Returns dataset snapshots, optionally filtered by dataset ID."""
        return self.registry.list_snapshots(dataset_id=dataset_id)

    def get_snapshot(self, snapshot_id: str) -> Optional[DatasetSnapshot]:
        """Retrieves a specific dataset snapshot by ID."""
        return self.registry.get_snapshot(snapshot_id)

    def _load_cutoffs(self) -> List[AdmissionCutoffObservation]:
        """Loads all normalised cutoff records from disk (cached in memory)."""
        if self._cached_cutoffs is not None:
            return self._cached_cutoffs

        cutoffs: List[AdmissionCutoffObservation] = []
        if self.normalized_josaa_dir.is_dir():
            for json_file in sorted(self.normalized_josaa_dir.glob("*.json")):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        records = json.load(f)
                        for item in records:
                            cutoffs.append(AdmissionCutoffObservation.from_dict(item))
                except Exception:
                    pass

        self._cached_cutoffs = cutoffs
        return cutoffs

    def query_cutoffs(
        self,
        academic_year: Optional[int] = None,
        institution: Optional[str] = None,
        programme: Optional[str] = None,
        counselling_round: Optional[int] = None,
        seat_type: Optional[str] = None,
        quota: Optional[str] = None,
        rank_basis: Optional[str] = None,
        source_status: Optional[str] = None,
        is_synthetic: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AdmissionCutoffObservation], int]:
        """Queries historical cutoff observations with deterministic filtering and pagination."""
        all_cutoffs = self._load_cutoffs()
        filtered = all_cutoffs

        if academic_year is not None:
            filtered = [c for c in filtered if c.academic_year == academic_year]

        if institution:
            inst_lower = institution.strip().lower()
            filtered = [c for c in filtered if inst_lower in c.institution_name.lower() or inst_lower in c.institution_id.lower()]

        if programme:
            prog_lower = programme.strip().lower()
            filtered = [c for c in filtered if prog_lower in c.programme_title.lower() or prog_lower in c.programme_id.lower()]

        if counselling_round is not None:
            filtered = [c for c in filtered if c.counselling_round == counselling_round]

        if seat_type:
            st_upper = seat_type.strip().upper()
            filtered = [c for c in filtered if c.seat_type.upper() == st_upper]

        if quota:
            q_upper = quota.strip().upper()
            filtered = [c for c in filtered if c.quota.upper() == q_upper]

        if rank_basis:
            rb_upper = rank_basis.strip().upper()
            filtered = [c for c in filtered if c.rank_basis.upper() == rb_upper]

        if source_status:
            ss_lower = source_status.strip().lower()
            filtered = [c for c in filtered if c.source_status.value.lower() == ss_lower]

        if is_synthetic is not None:
            filtered = [c for c in filtered if c.is_synthetic is is_synthetic]

        total_count = len(filtered)
        paged = filtered[offset : offset + limit]
        return paged, total_count

    def clear_cache(self) -> None:
        """Clears in-memory caches to reload disk partitions."""
        self._cached_cutoffs = None
        self._cached_criteria = None

    def query_programmes(
        self,
        academic_year: Optional[int] = None,
        institution: Optional[str] = None,
        is_synthetic: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AcademicProgrammeRecord], int]:
        """Derives unique official academic programme offerings from normalised observations."""
        cutoffs = self._load_cutoffs()
        progs_dict: Dict[str, AcademicProgrammeRecord] = {}

        for c in cutoffs:
            if c.programme_id not in progs_dict:
                rec = AcademicProgrammeRecord(
                    programme_id=c.programme_id,
                    institution_id=c.institution_id,
                    official_title=c.programme_title,
                    academic_year=c.academic_year,
                    degree_type="B.Tech." if "Bachelor of Technology" in c.programme_title or "B.Tech" in c.programme_title else None,
                    discipline=c.programme_title.split("(")[0].strip() if "(" in c.programme_title else c.programme_title,
                    duration_years=4,
                    source_references=[c.source_document_id],
                    provenance=c.source_status,
                    is_synthetic=c.is_synthetic,
                )
                progs_dict[c.programme_id] = rec

        progs = sorted(progs_dict.values(), key=lambda p: (p.institution_id, p.official_title))

        if academic_year is not None:
            progs = [p for p in progs if p.academic_year == academic_year]

        if institution:
            inst_lower = institution.strip().lower()
            progs = [p for p in progs if inst_lower in p.institution_id.lower()]

        if is_synthetic is not None:
            progs = [p for p in progs if p.is_synthetic is is_synthetic]

        total_count = len(progs)
        paged = progs[offset : offset + limit]
        return paged, total_count

    def list_eligibility_criteria(
        self,
        academic_year: Optional[int] = None,
        criterion_scope: Optional[str] = None,
    ) -> List[FormalEligibilityCriterion]:
        """Returns verified formal eligibility criteria from official authorities."""
        if self._cached_criteria is None:
            criteria: List[FormalEligibilityCriterion] = []
            crit_file = self.normalized_jeeadv_dir / "eligibility_criteria.json"
            if crit_file.is_file():
                try:
                    with open(crit_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data:
                            criteria.append(FormalEligibilityCriterion.from_dict(item))
                except Exception:
                    pass
            self._cached_criteria = criteria

        result = list(self._cached_criteria)
        if academic_year is not None:
            result = [c for c in result if c.academic_year == academic_year]
        if criterion_scope is not None:
            scope_clean = criterion_scope.strip().lower()
            result = [c for c in result if c.criterion_scope.lower() == scope_clean]
        return result

