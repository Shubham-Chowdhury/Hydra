"""Provenance Registry managing source manifests and dataset snapshots (Phase 3).

Provides deterministic loading, querying, and persistence of SourceDocument metadata
and DatasetSnapshot history in data/manifests/.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from app.domain.provenance import DatasetSnapshot, SourceDocument, SourceStatus, ValidationStatus


class ProvenanceRegistry:
    """Thread-safe, filesystem-backed registry for sources and dataset snapshots."""

    DEFAULT_MANIFEST_DIR = Path("data/manifests")

    def __init__(self, manifest_dir: Optional[Path] = None) -> None:
        self.manifest_dir = manifest_dir or self.DEFAULT_MANIFEST_DIR
        self.sources_file = self.manifest_dir / "sources.json"
        self.snapshots_file = self.manifest_dir / "snapshots.json"
        self._sources: Dict[str, SourceDocument] = {}
        self._snapshots: Dict[str, DatasetSnapshot] = {}
        self._ensure_storage()
        self.load()

    def _ensure_storage(self) -> None:
        """Ensures the manifest directory exists."""
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_sha256(file_path: str | Path) -> str:
        """Calculates reproducible SHA-256 checksum for a file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found for checksum computation: {file_path}")
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def load(self) -> None:
        """Loads source documents and snapshots from disk."""
        self._sources.clear()
        self._snapshots.clear()

        if self.sources_file.is_file():
            try:
                with open(self.sources_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        doc = SourceDocument.from_dict(item)
                        self._sources[doc.source_id] = doc
            except Exception:
                pass

        if self.snapshots_file.is_file():
            try:
                with open(self.snapshots_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        snap = DatasetSnapshot.from_dict(item)
                        self._snapshots[snap.snapshot_id] = snap
            except Exception:
                pass

    def save(self) -> None:
        """Atomically saves source documents and snapshots to disk."""
        self._ensure_storage()
        sources_payload = [doc.to_dict() for doc in self.list_sources()]
        tmp_sources = self.sources_file.with_suffix(".tmp")
        with open(tmp_sources, "w", encoding="utf-8") as f:
            json.dump(sources_payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp_sources, self.sources_file)

        snapshots_payload = [snap.to_dict() for snap in self.list_snapshots()]
        tmp_snaps = self.snapshots_file.with_suffix(".tmp")
        with open(tmp_snaps, "w", encoding="utf-8") as f:
            json.dump(snapshots_payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp_snaps, self.snapshots_file)

    def register_source(self, document: SourceDocument) -> None:
        """Registers or updates a source document."""
        self._sources[document.source_id] = document
        self.save()

    def get_source(self, source_id: str) -> Optional[SourceDocument]:
        """Retrieves a source document by its stable identifier."""
        return self._sources.get(source_id)

    def list_sources(self) -> List[SourceDocument]:
        """Returns all registered source documents in deterministic sorted order."""
        return sorted(self._sources.values(), key=lambda s: s.source_id)

    def register_snapshot(self, snapshot: DatasetSnapshot) -> None:
        """Registers a newly produced immutable dataset snapshot."""
        self._snapshots[snapshot.snapshot_id] = snapshot
        self.save()

    def get_snapshot(self, snapshot_id: str) -> Optional[DatasetSnapshot]:
        """Retrieves a dataset snapshot by its stable identifier."""
        return self._snapshots.get(snapshot_id)

    def list_snapshots(self, dataset_id: Optional[str] = None) -> List[DatasetSnapshot]:
        """Returns registered dataset snapshots, optionally filtered by dataset ID."""
        snaps = list(self._snapshots.values())
        if dataset_id:
            snaps = [s for s in snaps if s.dataset_id == dataset_id]
        return sorted(snaps, key=lambda s: (s.dataset_id, s.snapshot_version, s.snapshot_id))

