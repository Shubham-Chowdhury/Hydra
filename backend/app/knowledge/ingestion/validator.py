"""Validation and Quarantine Pipeline for Admissions Ingestion (Phase 3).

Applies strict record-level validation rules to prevent corrupt, malformed, or
unverifiable records from entering the authoritative admissions knowledge base.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from app.domain.provenance import (
    DatasetSnapshot,
    SourceDocument,
    SourceStatus,
    ValidationStatus,
)


@dataclass
class ValidationFinding:
    """Detailed validation issue encountered on a single record."""

    rule_code: str
    field_name: str
    message: str


@dataclass
class RecordValidationResult:
    """Outcome of validating a single candidate admissions record."""

    is_valid: bool
    status: ValidationStatus
    findings: List[ValidationFinding] = field(default_factory=list)
    quarantined_record: Optional[Dict[str, Any]] = None


class AdmissionRecordValidator:
    """Stateless validator enforcing admissions schema integrity and boundary conditions."""

    VALID_QUOTAS = {"AI", "HS", "OS", "JK", "LA", "GO", "AP"}
    VALID_SEAT_TYPES = {
        "OPEN",
        "GEN-EWS",
        "OBC-NCL",
        "SC",
        "ST",
        "OPEN (PWD)",
        "OPEN (PW_D)",
        "OPEN (PWD)",
        "GEN-EWS (PWD)",
        "OBC-NCL (PWD)",
        "SC (PWD)",
        "ST (PWD)",
    }

    def validate_cutoff_row(
        self,
        raw_row: Dict[str, Any],
        row_index: int,
        seen_keys: Set[Tuple[str, str, str, str, str, int, int]],
    ) -> RecordValidationResult:
        """Validates a candidate cutoff record."""
        findings: List[ValidationFinding] = []

        # 1. Required text identifiers
        inst_name = str(raw_row.get("institution_name", "")).strip()
        if not inst_name:
            findings.append(
                ValidationFinding(
                    rule_code="VAL_REQ_INSTITUTION",
                    field_name="institution_name",
                    message="Official institution name is missing or empty.",
                )
            )

        prog_title = str(raw_row.get("programme_title", "")).strip()
        if not prog_title:
            findings.append(
                ValidationFinding(
                    rule_code="VAL_REQ_PROGRAMME",
                    field_name="programme_title",
                    message="Official programme title is missing or empty.",
                )
            )

        # 2. Academic year validation
        year_raw = raw_row.get("academic_year")
        academic_year = None
        try:
            academic_year = int(year_raw)
            if not (2015 <= academic_year <= 2035):
                findings.append(
                    ValidationFinding(
                        rule_code="VAL_YEAR_OUT_OF_BOUNDS",
                        field_name="academic_year",
                        message=f"Academic year '{academic_year}' is outside reasonable bounds (2015-2035).",
                    )
                )
        except (ValueError, TypeError):
            findings.append(
                ValidationFinding(
                    rule_code="VAL_YEAR_INVALID",
                    field_name="academic_year",
                    message=f"Academic year '{year_raw}' is not a valid integer.",
                )
            )

        # 3. Counselling round validation
        round_raw = raw_row.get("counselling_round")
        counselling_round = None
        try:
            counselling_round = int(round_raw)
            if not (1 <= counselling_round <= 10):
                findings.append(
                    ValidationFinding(
                        rule_code="VAL_ROUND_OUT_OF_BOUNDS",
                        field_name="counselling_round",
                        message=f"Counselling round '{counselling_round}' is outside bounds (1-10).",
                    )
                )
        except (ValueError, TypeError):
            findings.append(
                ValidationFinding(
                    rule_code="VAL_ROUND_INVALID",
                    field_name="counselling_round",
                    message=f"Counselling round '{round_raw}' is not a valid integer.",
                )
            )

        # 4. Opening and Closing rank validation
        open_rank_raw = raw_row.get("opening_rank")
        close_rank_raw = raw_row.get("closing_rank")
        open_rank = None
        close_rank = None

        try:
            open_rank = int(open_rank_raw)
            if open_rank <= 0:
                findings.append(
                    ValidationFinding(
                        rule_code="VAL_RANK_NON_POSITIVE",
                        field_name="opening_rank",
                        message=f"Opening rank '{open_rank}' must be a positive integer.",
                    )
                )
        except (ValueError, TypeError):
            findings.append(
                ValidationFinding(
                    rule_code="VAL_RANK_INVALID",
                    field_name="opening_rank",
                    message=f"Opening rank '{open_rank_raw}' is not a valid integer.",
                )
            )

        try:
            close_rank = int(close_rank_raw)
            if close_rank <= 0:
                findings.append(
                    ValidationFinding(
                        rule_code="VAL_RANK_NON_POSITIVE",
                        field_name="closing_rank",
                        message=f"Closing rank '{close_rank}' must be a positive integer.",
                    )
                )
        except (ValueError, TypeError):
            findings.append(
                ValidationFinding(
                    rule_code="VAL_RANK_INVALID",
                    field_name="closing_rank",
                    message=f"Closing rank '{close_rank_raw}' is not a valid integer.",
                )
            )

        # Check rank ordering (Opening rank <= Closing rank)
        if open_rank is not None and close_rank is not None and open_rank > 0 and close_rank > 0:
            if open_rank > close_rank:
                findings.append(
                    ValidationFinding(
                        rule_code="VAL_RANK_ORDER_INVERTED",
                        field_name="ranks",
                        message=f"Opening rank ({open_rank}) cannot exceed closing rank ({close_rank}).",
                    )
                )

        # 5. Quota validation
        quota = str(raw_row.get("quota", "")).strip().upper()
        if not quota:
            findings.append(
                ValidationFinding(
                    rule_code="VAL_QUOTA_EMPTY",
                    field_name="quota",
                    message="Counselling quota is required.",
                )
            )

        # 6. Seat type validation
        seat_type = str(raw_row.get("seat_type", "")).strip().upper()
        if not seat_type:
            findings.append(
                ValidationFinding(
                    rule_code="VAL_SEAT_TYPE_EMPTY",
                    field_name="seat_type",
                    message="Seat type / category is required.",
                )
            )

        # 7. Duplicate detection
        gender_pool = str(raw_row.get("gender_pool", "")).strip()
        if inst_name and prog_title and academic_year and counselling_round and quota and seat_type:
            key = (
                inst_name.lower(),
                prog_title.lower(),
                quota,
                seat_type,
                gender_pool.lower(),
                counselling_round,
                academic_year,
            )
            if key in seen_keys:
                findings.append(
                    ValidationFinding(
                        rule_code="VAL_DUPLICATE_RECORD",
                        field_name="composite_key",
                        message=f"Duplicate observation encountered for key {key}.",
                    )
                )
            else:
                seen_keys.add(key)

        is_valid = len(findings) == 0
        status = ValidationStatus.VALID if is_valid else ValidationStatus.QUARANTINED

        quarantine_payload = None
        if not is_valid:
            quarantine_payload = {
                "row_index": row_index,
                "raw_data": raw_row,
                "errors": [f.message for f in findings],
                "rule_codes": [f.rule_code for f in findings],
                "quarantine_timestamp": datetime.now(timezone.utc).isoformat(),
            }

        return RecordValidationResult(
            is_valid=is_valid,
            status=status,
            findings=findings,
            quarantined_record=quarantine_payload,
        )


class ProvenanceInvariantValidator:
    """Enforces non-negotiable provenance invariants across records, snapshots, and sources (Phase 3.1)."""

    @staticmethod
    def validate_derived_from_official_invariants(
        source_doc: Optional[SourceDocument],
        snapshot: Optional[DatasetSnapshot],
        observation: Any,
    ) -> List[ValidationFinding]:
        """Validates that records claiming derived_from_official satisfy all strict evidentiary requirements."""
        findings: List[ValidationFinding] = []

        is_synthetic = getattr(observation, "is_synthetic", False)
        source_status = getattr(observation, "source_status", None)
        obs_id = getattr(observation, "observation_id", "unknown_observation")
        row_prov = getattr(observation, "source_row_provenance", "")

        # 1. Synthetic records can NEVER claim derived_from_official or official_source
        if is_synthetic:
            if source_status in (SourceStatus.DERIVED_FROM_OFFICIAL, SourceStatus.OFFICIAL_SOURCE):
                findings.append(
                    ValidationFinding(
                        rule_code="PROV_SYNTHETIC_OFFICIAL_CONFLICT",
                        field_name="source_status",
                        message=f"Record '{obs_id}' is marked synthetic but claims official origin '{source_status.value}'.",
                    )
                )

        # 2. Strict checks when record claims derived_from_official
        if source_status == SourceStatus.DERIVED_FROM_OFFICIAL:
            if is_synthetic:
                findings.append(
                    ValidationFinding(
                        rule_code="PROV_DERIVED_CANNOT_BE_SYNTHETIC",
                        field_name="is_synthetic",
                        message=f"Record '{obs_id}' claims derived_from_official but has is_synthetic=True.",
                    )
                )

            # Must reference an existing source document
            if not source_doc:
                findings.append(
                    ValidationFinding(
                        rule_code="PROV_SOURCE_DOC_MISSING",
                        field_name="source_document_id",
                        message=f"Record '{obs_id}' references non-existent source document.",
                    )
                )
            else:
                # Source document itself MUST be an authentic official_source
                if source_doc.source_status != SourceStatus.OFFICIAL_SOURCE:
                    findings.append(
                        ValidationFinding(
                            rule_code="PROV_DERIVED_WITHOUT_OFFICIAL_SOURCE",
                            field_name="source_document_id",
                            message=(
                                f"Record '{obs_id}' claims derived_from_official, but source document "
                                f"'{source_doc.source_id}' has status '{source_doc.source_status.value}', "
                                "which is not official_source."
                            ),
                        )
                    )
                # Official source document MUST have verified artifact path and SHA-256 checksum
                if not source_doc.original_artifact_path or not source_doc.sha256_checksum:
                    findings.append(
                        ValidationFinding(
                            rule_code="PROV_MISSING_ARTIFACT_OR_CHECKSUM",
                            field_name="source_document.sha256_checksum",
                            message=(
                                f"Source document '{source_doc.source_id}' lacks a verified original_artifact_path "
                                "or SHA-256 checksum."
                            ),
                        )
                    )

            # Must reference an existing snapshot
            if not snapshot:
                findings.append(
                    ValidationFinding(
                        rule_code="PROV_SNAPSHOT_MISSING",
                        field_name="snapshot_id",
                        message=f"Record '{obs_id}' references non-existent dataset snapshot.",
                    )
                )
            else:
                # Snapshot checksum must match source document checksum
                if source_doc and source_doc.sha256_checksum:
                    if snapshot.source_artifact_checksum != source_doc.sha256_checksum:
                        findings.append(
                            ValidationFinding(
                                rule_code="PROV_CHECKSUM_MISMATCH",
                                field_name="snapshot.source_artifact_checksum",
                                message=(
                                    f"Snapshot checksum '{snapshot.source_artifact_checksum}' does not match "
                                    f"source document checksum '{source_doc.sha256_checksum}'."
                                ),
                            )
                        )
                # Snapshot must include source document in its source_document_ids
                if source_doc and source_doc.source_id not in snapshot.source_document_ids:
                    findings.append(
                        ValidationFinding(
                            rule_code="PROV_SNAPSHOT_SOURCE_MISMATCH",
                            field_name="snapshot.source_document_ids",
                            message=(
                                f"Snapshot '{snapshot.snapshot_id}' does not register source document "
                                f"'{source_doc.source_id}' in its source list."
                            ),
                        )
                    )

            # Must have reproducible row-level provenance
            if not row_prov or not row_prov.strip() or not row_prov.startswith("row_"):
                findings.append(
                    ValidationFinding(
                        rule_code="PROV_MISSING_ROW_LOCATION",
                        field_name="source_row_provenance",
                        message=f"Record '{obs_id}' lacks reproducible source row provenance ('{row_prov}').",
                    )
                )

        return findings


