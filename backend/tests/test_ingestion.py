"""Integration tests for Admissions Ingestion and Quarantine Pipeline (Phase 3)."""

from pathlib import Path
import pytest

from app.domain.provenance import SourceDocument, SourceStatus, ValidationStatus
from app.knowledge.ingestion.importer_jeeadv import JEEAdvancedEligibilityImporter
from app.knowledge.ingestion.importer_josaa import JoSAAImporter
from app.knowledge.provenance_registry import ProvenanceRegistry


@pytest.fixture
def temp_provenance_env(tmp_path: Path):
    manifest_dir = tmp_path / "manifests"
    normalized_dir = tmp_path / "normalized"
    quarantine_dir = tmp_path / "quarantine"
    registry = ProvenanceRegistry(manifest_dir=manifest_dir)
    return registry, normalized_dir, quarantine_dir


def test_1_josaa_importer_valid_fixture_accepted(temp_provenance_env):
    """Valid JoSAA fixture imports all rows with positive validation and snapshot registration."""
    registry, norm_dir, quar_dir = temp_provenance_env
    source_doc = SourceDocument(
        source_id="SRC_FIXTURE_VALID",
        title="Valid Test Fixture",
        issuing_authority="JoSAA Test Authority",
        canonical_url="https://josaa.nic.in/fixture",
        source_type="csv",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.SYNTHETIC_DEMO,
    )
    registry.register_source(source_doc)

    importer = JoSAAImporter(registry=registry, normalized_dir=norm_dir, quarantine_dir=quar_dir)
    cutoffs, snapshot, report = importer.import_csv(
        file_path="data/raw/josaa/fixtures/josaa_orcr_fixture_round1_2026.csv",
        source_document=source_doc,
        academic_year=2026,
    )

    assert len(cutoffs) == 14
    assert report.records_processed == 14
    assert report.records_accepted == 14
    assert report.records_quarantined == 0
    assert report.records_duplicate == 0
    assert snapshot.validation_status == ValidationStatus.VALID

    # Check top cutoff observation fields
    top_obs = cutoffs[0]
    assert top_obs.institution_name == "Indian Institute of Technology Bombay"
    assert "Computer Science and Engineering" in top_obs.programme_title
    assert top_obs.opening_rank == 1
    assert top_obs.closing_rank == 67
    assert top_obs.quota == "AI"
    assert top_obs.seat_type == "OPEN"
    assert top_obs.source_row_provenance == "row_2"
    assert top_obs.is_synthetic is True
    assert top_obs.source_status == SourceStatus.SYNTHETIC_DEMO
    assert "Historical cutoff observations describe past counselling outcomes" in top_obs.disclaimer


def test_2_josaa_importer_invalid_fixture_quarantined_with_reasons(temp_provenance_env):
    """Invalid records are quarantined with machine-readable reasons and original raw payload preserved."""
    registry, norm_dir, quar_dir = temp_provenance_env
    source_doc = SourceDocument(
        source_id="SRC_FIXTURE_INVALID",
        title="Invalid Test Fixture",
        issuing_authority="JoSAA Test Authority",
        canonical_url="https://josaa.nic.in/invalid_fixture",
        source_type="csv",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.SYNTHETIC_DEMO,
    )
    registry.register_source(source_doc)

    importer = JoSAAImporter(registry=registry, normalized_dir=norm_dir, quarantine_dir=quar_dir)
    cutoffs, snapshot, report = importer.import_csv(
        file_path="data/raw/josaa/fixtures/josaa_orcr_invalid_fixture.csv",
        source_document=source_doc,
        academic_year=2026,
    )

    # 1 valid, 5 quarantined (missing institute, missing programme, negative rank, inverted rank, duplicate)
    assert report.records_processed == 6
    assert report.records_accepted == 1
    assert report.records_quarantined == 5
    assert report.records_duplicate == 1
    assert snapshot.validation_status == ValidationStatus.QUARANTINED
    assert report.quarantine_path is not None
    assert Path(report.quarantine_path).is_file()


def test_3_jeeadv_importer_extracts_all_five_criteria(temp_provenance_env):
    """Authentic JEE (Advanced) HTML artifact is parsed into 5 formal eligibility criteria."""
    registry, norm_dir, _ = temp_provenance_env
    source_doc = SourceDocument(
        source_id="SRC_JEEADV_OFFICIAL",
        title="JEE (Advanced) 2026 Eligibility",
        issuing_authority="JEE (Advanced) Office",
        canonical_url="https://jeeadv.ac.in/eligibility.html",
        source_type="html_webpage",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.OFFICIAL_SOURCE,
    )
    registry.register_source(source_doc)

    importer = JEEAdvancedEligibilityImporter(registry=registry, normalized_dir=norm_dir)
    criteria, snapshot = importer.import_html(
        file_path="data/raw/jeeadv/2026/eligibility.html",
        source_document=source_doc,
        academic_year=2026,
    )

    assert len(criteria) == 5
    assert snapshot.records_accepted == 5
    assert snapshot.validation_status == ValidationStatus.VALID

    crit_numbers = [c.criterion_number for c in criteria]
    assert "Criterion A1" in crit_numbers
    assert "Criterion A2" in crit_numbers
    assert "Criterion A3" in crit_numbers
    assert "Criterion A4" in crit_numbers
    assert "Criterion A5" in crit_numbers

    # Verify Criterion A2 (Age limit) details
    crit_a2 = next(c for c in criteria if "A2" in c.criterion_number)
    assert "Age Limit" in crit_a2.title
    assert "October 1, 2001" in crit_a2.description
    assert crit_a2.is_mandatory is True
    assert crit_a2.source_status == SourceStatus.OFFICIAL_SOURCE
    assert crit_a2.criterion_scope == "exam_appearance_eligibility"
    assert crit_a2.target_examination == "JEE (Advanced)"


def test_4_repeated_imports_produce_deterministic_snapshots(temp_provenance_env):
    """Repeated import executions from the same artifact produce identical snapshot identifiers."""
    registry, norm_dir, quar_dir = temp_provenance_env
    source_doc = SourceDocument(
        source_id="SRC_FIXTURE_REPEAT",
        title="Repeat Fixture",
        issuing_authority="JoSAA",
        canonical_url="https://josaa.nic.in/repeat",
        source_type="csv",
        academic_year=2026,
        retrieval_timestamp="2026-10-29T20:00:00Z",
        source_status=SourceStatus.SYNTHETIC_DEMO,
    )

    importer = JoSAAImporter(registry=registry, normalized_dir=norm_dir, quarantine_dir=quar_dir)
    _, snap1, _ = importer.import_csv(
        file_path="data/raw/josaa/fixtures/josaa_orcr_fixture_round1_2026.csv",
        source_document=source_doc,
        academic_year=2026,
    )
    _, snap2, _ = importer.import_csv(
        file_path="data/raw/josaa/fixtures/josaa_orcr_fixture_round1_2026.csv",
        source_document=source_doc,
        academic_year=2026,
    )

    assert snap1.snapshot_id == snap2.snapshot_id
    assert snap1.source_artifact_checksum == snap2.source_artifact_checksum

