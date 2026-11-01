"""Unit tests for Provenance and Source Metadata System (Phase 3)."""

from pathlib import Path
import pytest

from app.domain.provenance import (
    DatasetSnapshot,
    RecordProvenance,
    SourceDocument,
    SourceStatus,
    ValidationStatus,
)
from app.knowledge.provenance_registry import ProvenanceRegistry


def test_1_source_document_dataclass_and_serialisation():
    """SourceDocument correctly serialises to and from dictionary with all provenance fields."""
    doc = SourceDocument(
        source_id="SRC_TEST_DOC_01",
        title="Official Test Admissions Document 2026",
        issuing_authority="Admissions Authority Test",
        canonical_url="https://test.admissions.gov/doc-2026",
        source_type="html_webpage",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.OFFICIAL_SOURCE,
        publication_date="2026-05-01",
        original_artifact_path="data/raw/test/doc.html",
        sha256_checksum="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        document_version="v1.0",
        access_notes="Public access without login",
        verification_notes="Verified against test portal",
    )

    data = doc.to_dict()
    assert data["source_id"] == "SRC_TEST_DOC_01"
    assert data["source_status"] == "official_source"
    assert data["academic_year"] == 2026

    reconstituted = SourceDocument.from_dict(data)
    assert reconstituted == doc


def test_2_dataset_snapshot_creation_and_serialisation():
    """DatasetSnapshot retains processing counts, checksums, and validation status."""
    snap = DatasetSnapshot(
        snapshot_id="SNAP_TEST_001",
        dataset_id="DATASET_TEST_ORCR",
        snapshot_version="1.0.0",
        academic_year=2026,
        source_document_ids=["SRC_TEST_DOC_01"],
        importer_version="TEST_PARSER_V1",
        source_artifact_checksum="checksum_abc_123",
        created_at="2026-10-29T20:00:00Z",
        records_processed=100,
        records_accepted=95,
        records_quarantined=5,
        records_duplicate=2,
        validation_status=ValidationStatus.VALID,
        quarantine_file_path="data/quarantine/SNAP_TEST_001.jsonl",
    )

    data = snap.to_dict()
    assert data["records_processed"] == 100
    assert data["records_accepted"] == 95
    assert data["records_quarantined"] == 5
    assert data["records_duplicate"] == 2

    reconstituted = DatasetSnapshot.from_dict(data)
    assert reconstituted == snap


def test_3_sha256_checksum_reproducibility(tmp_path: Path):
    """File checksum computation is deterministic and reproducible."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Hydra Admissions Knowledge Base Provenance Test", encoding="utf-8")

    checksum1 = ProvenanceRegistry.compute_sha256(test_file)
    checksum2 = ProvenanceRegistry.compute_sha256(test_file)

    assert checksum1 == checksum2
    assert len(checksum1) == 64

    # Different content produces different checksum
    test_file2 = tmp_path / "sample2.txt"
    test_file2.write_text("Different content", encoding="utf-8")
    checksum3 = ProvenanceRegistry.compute_sha256(test_file2)
    assert checksum1 != checksum3


def test_4_provenance_registry_persistence_and_loading(tmp_path: Path):
    """Registry correctly saves and loads sources and snapshots to/from JSON manifests."""
    reg = ProvenanceRegistry(manifest_dir=tmp_path)
    assert len(reg.list_sources()) == 0

    doc = SourceDocument(
        source_id="SRC_PERSIST_01",
        title="Persist Document",
        issuing_authority="Auth",
        canonical_url="https://auth.gov",
        source_type="csv",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.OFFICIAL_SOURCE,
    )
    reg.register_source(doc)
    assert len(reg.list_sources()) == 1

    # Reload in a new registry instance pointing to same directory
    reg2 = ProvenanceRegistry(manifest_dir=tmp_path)
    loaded_doc = reg2.get_source("SRC_PERSIST_01")
    assert loaded_doc is not None
    assert loaded_doc.title == "Persist Document"
    assert loaded_doc.source_status == SourceStatus.OFFICIAL_SOURCE


def test_5_source_status_enforcement():
    """Unverified sources cannot be misidentified as official sources."""
    doc = SourceDocument(
        source_id="SRC_UNVERIFIED_01",
        title="Unverified Document",
        issuing_authority="Unknown",
        canonical_url="https://unknown.net",
        source_type="html",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.UNVERIFIED,
    )
    assert doc.source_status == SourceStatus.UNVERIFIED
    assert doc.source_status != SourceStatus.OFFICIAL_SOURCE


def test_6_synthetic_record_cannot_claim_official_status():
    """Domain model rejects synthetic records masquerading as official or derived-from-official."""
    from app.domain.admissions import AdmissionCutoffObservation

    with pytest.raises(ValueError, match="Provenance integrity violation"):
        AdmissionCutoffObservation(
            observation_id="CUTOFF_BAD_PROV_1",
            institution_id="INST_DEMO",
            programme_id="PROG_DEMO",
            institution_name="Demo Tech",
            programme_title="Computer Science",
            academic_year=2026,
            counselling_round=1,
            exam_name="JEE Advanced",
            quota="AI",
            seat_type="OPEN",
            gender_pool="Gender-Neutral",
            opening_rank=1,
            closing_rank=67,
            rank_basis="CRL",
            source_document_id="SRC_FIXTURE",
            snapshot_id="SNAP_FIXTURE",
            source_row_provenance="row_2",
            source_status=SourceStatus.DERIVED_FROM_OFFICIAL,
            is_synthetic=True,  # Conflict: synthetic but claims derived_from_official
        )

    with pytest.raises(ValueError, match="Provenance integrity violation"):
        AdmissionCutoffObservation(
            observation_id="CUTOFF_BAD_PROV_2",
            institution_id="INST_DEMO",
            programme_id="PROG_DEMO",
            institution_name="Demo Tech",
            programme_title="Computer Science",
            academic_year=2026,
            counselling_round=1,
            exam_name="JEE Advanced",
            quota="AI",
            seat_type="OPEN",
            gender_pool="Gender-Neutral",
            opening_rank=1,
            closing_rank=67,
            rank_basis="CRL",
            source_document_id="SRC_FIXTURE",
            snapshot_id="SNAP_FIXTURE",
            source_row_provenance="row_2",
            source_status=SourceStatus.OFFICIAL_SOURCE,
            is_synthetic=True,  # Conflict: synthetic but claims official_source
        )


def test_7_derived_from_official_requires_genuine_official_source_document():
    """ProvenanceInvariantValidator catches records claiming derived_from_official on synthetic/unverified sources."""
    from app.domain.admissions import AdmissionCutoffObservation
    from app.knowledge.ingestion.validator import ProvenanceInvariantValidator

    # Synthetic demo source document
    synth_source = SourceDocument(
        source_id="SRC_DEMO_FIXTURE",
        title="Demo Fixture",
        issuing_authority="Hydra Demo",
        canonical_url="https://demo.local/fixture",
        source_type="csv",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.SYNTHETIC_DEMO,
        sha256_checksum="1111222233334444555566667777888811112222333344445555666677778888",
        original_artifact_path="data/raw/demo.csv",
    )

    snapshot = DatasetSnapshot(
        snapshot_id="SNAP_DEMO_01",
        dataset_id="DATASET_DEMO",
        snapshot_version="1.0.0",
        academic_year=2026,
        source_document_ids=["SRC_DEMO_FIXTURE"],
        importer_version="TEST_PARSER",
        source_artifact_checksum="1111222233334444555566667777888811112222333344445555666677778888",
        created_at="2026-10-29T20:00:00Z",
        records_processed=1,
        records_accepted=1,
        records_quarantined=0,
    )

    # Observation that falsely claims derived_from_official with is_synthetic=False
    obs = AdmissionCutoffObservation(
        observation_id="CUTOFF_CLAIM_OFFICIAL",
        institution_id="INST_DEMO",
        programme_id="PROG_DEMO",
        institution_name="Demo Tech",
        programme_title="Computer Science",
        academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        quota="AI",
        seat_type="OPEN",
        gender_pool="Gender-Neutral",
        opening_rank=1,
        closing_rank=67,
        rank_basis="CRL",
        source_document_id="SRC_DEMO_FIXTURE",
        snapshot_id="SNAP_DEMO_01",
        source_row_provenance="row_2",
        source_status=SourceStatus.DERIVED_FROM_OFFICIAL,
        is_synthetic=False,
    )

    findings = ProvenanceInvariantValidator.validate_derived_from_official_invariants(
        source_doc=synth_source,
        snapshot=snapshot,
        observation=obs,
    )

    assert len(findings) > 0
    rule_codes = [f.rule_code for f in findings]
    assert "PROV_DERIVED_WITHOUT_OFFICIAL_SOURCE" in rule_codes


def test_8_derived_from_official_requires_matching_artifact_checksum():
    """Checksum mismatch between dataset snapshot and official source document is caught."""
    from app.domain.admissions import AdmissionCutoffObservation
    from app.knowledge.ingestion.validator import ProvenanceInvariantValidator

    official_source = SourceDocument(
        source_id="SRC_REAL_OFFICIAL",
        title="Real Official Bulletin",
        issuing_authority="Admissions Board",
        canonical_url="https://board.gov/report",
        source_type="csv",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.OFFICIAL_SOURCE,
        sha256_checksum="aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000",
        original_artifact_path="data/raw/real.csv",
    )

    # Snapshot with a conflicting checksum
    mismatched_snapshot = DatasetSnapshot(
        snapshot_id="SNAP_REAL_01",
        dataset_id="DATASET_REAL",
        snapshot_version="1.0.0",
        academic_year=2026,
        source_document_ids=["SRC_REAL_OFFICIAL"],
        importer_version="REAL_PARSER",
        source_artifact_checksum="bbbb1111bbbb1111bbbb1111bbbb1111bbbb1111bbbb1111bbbb1111bbbb1111",
        created_at="2026-10-29T20:00:00Z",
        records_processed=10,
        records_accepted=10,
        records_quarantined=0,
    )

    obs = AdmissionCutoffObservation(
        observation_id="CUTOFF_REAL_01",
        institution_id="INST_REAL",
        programme_id="PROG_REAL",
        institution_name="Real Institute",
        programme_title="Engineering",
        academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        quota="AI",
        seat_type="OPEN",
        gender_pool="Gender-Neutral",
        opening_rank=100,
        closing_rank=500,
        rank_basis="CRL",
        source_document_id="SRC_REAL_OFFICIAL",
        snapshot_id="SNAP_REAL_01",
        source_row_provenance="row_5",
        source_status=SourceStatus.DERIVED_FROM_OFFICIAL,
        is_synthetic=False,
    )

    findings = ProvenanceInvariantValidator.validate_derived_from_official_invariants(
        source_doc=official_source,
        snapshot=mismatched_snapshot,
        observation=obs,
    )

    rule_codes = [f.rule_code for f in findings]
    assert "PROV_CHECKSUM_MISMATCH" in rule_codes


def test_9_derived_from_official_requires_reproducible_source_location():
    """Missing or improper source row provenance violates provenance invariants."""
    from app.domain.admissions import AdmissionCutoffObservation
    from app.knowledge.ingestion.validator import ProvenanceInvariantValidator

    official_source = SourceDocument(
        source_id="SRC_REAL_OFFICIAL",
        title="Real Official Bulletin",
        issuing_authority="Admissions Board",
        canonical_url="https://board.gov/report",
        source_type="csv",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.OFFICIAL_SOURCE,
        sha256_checksum="aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000",
        original_artifact_path="data/raw/real.csv",
    )

    snapshot = DatasetSnapshot(
        snapshot_id="SNAP_REAL_01",
        dataset_id="DATASET_REAL",
        snapshot_version="1.0.0",
        academic_year=2026,
        source_document_ids=["SRC_REAL_OFFICIAL"],
        importer_version="REAL_PARSER",
        source_artifact_checksum="aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000aaaa0000",
        created_at="2026-10-29T20:00:00Z",
        records_processed=10,
        records_accepted=10,
        records_quarantined=0,
    )

    # Observation with missing row location ("general")
    obs = AdmissionCutoffObservation(
        observation_id="CUTOFF_REAL_02",
        institution_id="INST_REAL",
        programme_id="PROG_REAL",
        institution_name="Real Institute",
        programme_title="Engineering",
        academic_year=2026,
        counselling_round=1,
        exam_name="JEE Advanced",
        quota="AI",
        seat_type="OPEN",
        gender_pool="Gender-Neutral",
        opening_rank=100,
        closing_rank=500,
        rank_basis="CRL",
        source_document_id="SRC_REAL_OFFICIAL",
        snapshot_id="SNAP_REAL_01",
        source_row_provenance="unspecified_page",
        source_status=SourceStatus.DERIVED_FROM_OFFICIAL,
        is_synthetic=False,
    )

    findings = ProvenanceInvariantValidator.validate_derived_from_official_invariants(
        source_doc=official_source,
        snapshot=snapshot,
        observation=obs,
    )

    rule_codes = [f.rule_code for f in findings]
    assert "PROV_MISSING_ROW_LOCATION" in rule_codes


def test_10_josaa_fixture_is_unambiguously_synthetic_across_all_records():
    """Every record in the JoSAA fixture partition is synthetic and does not claim official derivation."""
    from app.services.admissions_service import AdmissionsService

    svc = AdmissionsService()
    records, total = svc.query_cutoffs(limit=100)
    assert total > 0

    for r in records:
        if "FIXTURE" in r.source_document_id:
            assert r.is_synthetic is True, f"Record {r.observation_id} must have is_synthetic=True"
            assert r.source_status == SourceStatus.SYNTHETIC_DEMO
            assert r.source_status != SourceStatus.DERIVED_FROM_OFFICIAL
            assert r.source_status != SourceStatus.OFFICIAL_SOURCE
            assert "SRC_JOSAA_SYNTHETIC_FIXTURE_2026" in r.source_document_id


def test_11_iit_bombay_cse_example_cannot_masquerade_as_verified_official_fact():
    """The IIT Bombay CSE closing rank 67 record is unambiguously synthetic and excluded from official queries."""
    from app.services.admissions_service import AdmissionsService

    svc = AdmissionsService()

    # Query without filters finds the synthetic test fixture
    records, total = svc.query_cutoffs(institution="Bombay", programme="Computer Science", seat_type="OPEN")
    assert total > 0
    top = next(r for r in records if r.closing_rank == 67)
    assert top.is_synthetic is True
    assert top.source_status == SourceStatus.SYNTHETIC_DEMO
    assert top.source_document_id == "SRC_JOSAA_SYNTHETIC_FIXTURE_2026"
    assert "Historical cutoff observations describe past counselling outcomes" in top.disclaimer

    # Filtering by official_source or is_synthetic=False MUST exclude this fixture record
    official_records, off_total = svc.query_cutoffs(
        institution="Bombay",
        source_status="official_source",
    )
    assert off_total == 0
    assert len(official_records) == 0

    non_synth_records, non_synth_total = svc.query_cutoffs(
        institution="Bombay",
        is_synthetic=False,
    )
    assert non_synth_total == 0
    assert len(non_synth_records) == 0


def test_12_formal_eligibility_criteria_retains_examination_scope():
    """All 5 JEE (Advanced) 2026 criteria are strictly scoped to exam appearance eligibility."""
    from app.services.admissions_service import AdmissionsService

    svc = AdmissionsService()
    criteria = svc.list_eligibility_criteria(academic_year=2026)
    assert len(criteria) == 5

    for c in criteria:
        assert c.source_status == SourceStatus.OFFICIAL_SOURCE
        assert c.source_document_id == "SRC_JEEADV_2026_ELIGIBILITY"
        assert c.criterion_scope == "exam_appearance_eligibility"
        assert c.target_examination == "JEE (Advanced)"
        assert c.academic_year == 2026


