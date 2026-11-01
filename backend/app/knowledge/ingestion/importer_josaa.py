"""JoSAA Historical Cutoffs Importer and Ingestion Pipeline (Phase 3).

Parses official JoSAA counselling CSV exports and test fixtures, applies deterministic
normalisation, validates every row, attaches row-level provenance, partitions invalid
records to quarantine, and creates reproducible dataset snapshots.
"""

import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.domain.admissions import AdmissionCutoffObservation
from app.domain.provenance import (
    DatasetSnapshot,
    RecordProvenance,
    SourceDocument,
    SourceStatus,
    ValidationStatus,
)
from app.knowledge.ingestion.normaliser import (
    normalize_gender_pool,
    normalize_institution_id,
    normalize_programme_id,
    normalize_quota,
    normalize_seat_type,
    normalize_whitespace,
    parse_rank_value,
)
from app.knowledge.ingestion.validator import AdmissionRecordValidator
from app.knowledge.provenance_registry import ProvenanceRegistry


@dataclass
class JoSAAImportReport:
    """Detailed summary of a JoSAA dataset ingestion execution."""

    snapshot_id: str
    source_document_id: str
    importer_version: str
    records_processed: int
    records_accepted: int
    records_quarantined: int
    records_duplicate: int
    source_checksum: str
    quarantine_path: Optional[str] = None
    normalized_path: Optional[str] = None


class JoSAAImporter:
    """Parses, normalises, validates, and stores JoSAA historical cutoff records."""

    IMPORTER_VERSION = "JOSAA_PARSER_V1.0.0"

    def __init__(
        self,
        registry: Optional[ProvenanceRegistry] = None,
        normalized_dir: Optional[Path] = None,
        quarantine_dir: Optional[Path] = None,
    ) -> None:
        self.registry = registry or ProvenanceRegistry()
        self.normalized_dir = normalized_dir or Path("data/normalized/josaa")
        self.quarantine_dir = quarantine_dir or Path("data/quarantine")
        self.validator = AdmissionRecordValidator()
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def import_csv(
        self,
        file_path: str | Path,
        source_document: SourceDocument,
        academic_year: int,
        default_round: int = 1,
        exam_name: str = "JEE Advanced",
    ) -> Tuple[List[AdmissionCutoffObservation], DatasetSnapshot, JoSAAImportReport]:
        """Ingests a JoSAA CSV artifact deterministically."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Source artifact not found: {file_path}")

        # Compute source artifact checksum
        source_checksum = self.registry.compute_sha256(path)

        # Generate stable snapshot identifier from checksum and version
        checksum_short = source_checksum[:12]
        snapshot_id = f"SNAP_JOSAA_{academic_year}_{checksum_short}_{self.IMPORTER_VERSION}"

        accepted_observations: List[AdmissionCutoffObservation] = []
        quarantined_records: List[Dict[str, Any]] = []
        seen_keys: Set[Tuple[str, str, str, str, str, int, int]] = set()

        records_processed = 0
        records_duplicate = 0

        # Determine dataset/record-level provenance classification
        is_synthetic = (
            source_document.source_status == SourceStatus.SYNTHETIC_DEMO
            or "fixture" in source_document.source_id.lower()
            or "fixture" in str(path).lower()
        )
        if is_synthetic:
            record_source_status = SourceStatus.SYNTHETIC_DEMO
        elif source_document.source_status == SourceStatus.OFFICIAL_SOURCE and source_document.sha256_checksum:
            record_source_status = SourceStatus.DERIVED_FROM_OFFICIAL
        else:
            record_source_status = SourceStatus.UNVERIFIED

        # Read CSV with encoding fallback
        encoding = "utf-8"
        try:
            with open(path, "r", encoding=encoding) as f:
                f.read(1024)
        except UnicodeDecodeError:
            encoding = "latin-1"

        with open(path, "r", encoding=encoding, errors="replace") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):  # Header is row 1
                records_processed += 1

                # Normalize keys and values from row
                clean_row = {normalize_whitespace(k): normalize_whitespace(v) for k, v in row.items() if k}

                inst_name = clean_row.get("Institute") or clean_row.get("Institute Name") or clean_row.get("institution_name", "")
                prog_title = clean_row.get("Academic Program Name") or clean_row.get("Programme Title") or clean_row.get("programme_title", "")
                quota_raw = clean_row.get("Quota") or clean_row.get("quota", "AI")
                seat_type_raw = clean_row.get("Seat Type") or clean_row.get("Category") or clean_row.get("seat_type", "OPEN")
                gender_raw = clean_row.get("Gender") or clean_row.get("Gender Pool") or clean_row.get("gender_pool", "Gender-Neutral")

                # Resolve round and year
                round_raw = clean_row.get("Round") or clean_row.get("counselling_round") or str(default_round)
                year_raw = clean_row.get("Year") or clean_row.get("academic_year") or str(academic_year)

                open_rank_raw = clean_row.get("Opening Rank") or clean_row.get("opening_rank")
                close_rank_raw = clean_row.get("Closing Rank") or clean_row.get("closing_rank")

                parsed_open, basis_open = parse_rank_value(open_rank_raw)
                parsed_close, basis_close = parse_rank_value(close_rank_raw)

                # Determine rank basis
                rank_basis = "CRL"
                if seat_type_raw and normalize_seat_type(seat_type_raw) != "OPEN":
                    rank_basis = "CATEGORY_RANK"
                if "PREPARATORY" in (basis_open, basis_close):
                    rank_basis = "PREPARATORY"

                candidate = {
                    "institution_name": normalize_whitespace(inst_name),
                    "programme_title": normalize_whitespace(prog_title),
                    "quota": normalize_quota(quota_raw),
                    "seat_type": normalize_seat_type(seat_type_raw),
                    "gender_pool": normalize_gender_pool(gender_raw),
                    "academic_year": int(year_raw) if str(year_raw).isdigit() else year_raw,
                    "counselling_round": int(round_raw) if str(round_raw).isdigit() else round_raw,
                    "opening_rank": parsed_open,
                    "closing_rank": parsed_close,
                    "rank_basis": rank_basis,
                }

                # Validation
                val_result = self.validator.validate_cutoff_row(candidate, row_idx, seen_keys)

                if val_result.is_valid:
                    inst_id = normalize_institution_id(candidate["institution_name"])
                    prog_id = normalize_programme_id(inst_id, candidate["programme_title"])
                    obs_id = f"CUTOFF_{inst_id}_{prog_id}_{candidate['quota']}_{candidate['seat_type']}_R{candidate['counselling_round']}_{candidate['academic_year']}"

                    observation = AdmissionCutoffObservation(
                        observation_id=obs_id,
                        institution_id=inst_id,
                        programme_id=prog_id,
                        institution_name=candidate["institution_name"],
                        programme_title=candidate["programme_title"],
                        academic_year=candidate["academic_year"],
                        counselling_round=candidate["counselling_round"],
                        exam_name=exam_name,
                        quota=candidate["quota"],
                        seat_type=candidate["seat_type"],
                        gender_pool=candidate["gender_pool"],
                        opening_rank=candidate["opening_rank"],
                        closing_rank=candidate["closing_rank"],
                        rank_basis=candidate["rank_basis"],
                        source_document_id=source_document.source_id,
                        snapshot_id=snapshot_id,
                        source_row_provenance=f"row_{row_idx}",
                        validation_status=ValidationStatus.VALID,
                        source_status=record_source_status,
                        is_synthetic=is_synthetic,
                    )
                    accepted_observations.append(observation)
                else:
                    if any(f.rule_code == "VAL_DUPLICATE_RECORD" for f in val_result.findings):
                        records_duplicate += 1
                    quarantined_records.append(val_result.quarantined_record)

        # Write quarantine file if there are invalid records
        quarantine_file_path: Optional[str] = None
        if quarantined_records:
            q_file = self.quarantine_dir / f"{snapshot_id}.jsonl"
            with open(q_file, "w", encoding="utf-8") as qf:
                for qr in quarantined_records:
                    qf.write(json.dumps(qr, ensure_ascii=False) + "\n")
            quarantine_file_path = str(q_file)

        # Write normalised partition
        normalized_file = self.normalized_dir / f"{snapshot_id}.json"
        with open(normalized_file, "w", encoding="utf-8") as nf:
            json.dump([obs.to_dict() for obs in accepted_observations], nf, indent=2, ensure_ascii=False)

        # Register snapshot
        snapshot = DatasetSnapshot(
            snapshot_id=snapshot_id,
            dataset_id="DATASET_JOSAA_ORCR",
            snapshot_version="1.0.0",
            academic_year=academic_year,
            source_document_ids=[source_document.source_id],
            importer_version=self.IMPORTER_VERSION,
            source_artifact_checksum=source_checksum,
            created_at=datetime.now(timezone.utc).isoformat(),
            records_processed=records_processed,
            records_accepted=len(accepted_observations),
            records_quarantined=len(quarantined_records),
            records_duplicate=records_duplicate,
            validation_status=ValidationStatus.VALID if not quarantined_records else ValidationStatus.QUARANTINED,
            quarantine_file_path=quarantine_file_path,
        )

        self.registry.register_snapshot(snapshot)

        report = JoSAAImportReport(
            snapshot_id=snapshot_id,
            source_document_id=source_document.source_id,
            importer_version=self.IMPORTER_VERSION,
            records_processed=records_processed,
            records_accepted=len(accepted_observations),
            records_quarantined=len(quarantined_records),
            records_duplicate=records_duplicate,
            source_checksum=source_checksum,
            quarantine_path=quarantine_file_path,
            normalized_path=str(normalized_file),
        )

        return accepted_observations, snapshot, report

