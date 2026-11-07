"""Twin service for managing and constructing Student Digital Twins."""

from typing import Any, Dict, List, Optional

from app.agents.twin_agent import TwinAgent
from app.domain.frames import StudentFrame
from app.domain.twin import TwinSnapshot
from app.services.programme_service import ProgrammeService


class TwinService:
    """Application service orchestrating Student Digital Twin construction."""

    def __init__(
        self,
        programme_service: Optional[ProgrammeService] = None,
        twin_agent: Optional[TwinAgent] = None,
    ) -> None:
        self._programme_service = programme_service or ProgrammeService()
        self._twin_agent = twin_agent or TwinAgent(
            knowledge_graph=self._programme_service.graph,
            frame_registry=self._programme_service.frame_registry,
            programmes=self._programme_service.get_all(),
        )
        self._snapshots_by_id: Dict[str, TwinSnapshot] = {}
        self._snapshots_by_snapshot_id: Dict[str, TwinSnapshot] = {}

    @property
    def agent(self) -> TwinAgent:
        """Returns the underlying TwinAgent instance."""
        return self._twin_agent

    def construct_twin(self, profile: Any) -> TwinSnapshot:
        """Constructs an auditable Student Digital Twin snapshot."""
        snapshot = self._twin_agent.construct_twin(profile)
        self._snapshots_by_id[snapshot.twin_id] = snapshot
        self._snapshots_by_snapshot_id[snapshot.snapshot_id] = snapshot
        return snapshot

    def register_snapshot(self, snapshot: TwinSnapshot) -> None:
        """Registers a snapshot in the in-memory session cache."""
        self._snapshots_by_id[snapshot.twin_id] = snapshot
        self._snapshots_by_snapshot_id[snapshot.snapshot_id] = snapshot

    def get_twin(self, twin_id: str) -> Optional[TwinSnapshot]:
        """Retrieves an existing snapshot by twin_id."""
        return self._snapshots_by_id.get(twin_id)

    def get_snapshot(self, identifier: str) -> Optional[TwinSnapshot]:
        """Retrieves an existing snapshot by twin_id or snapshot_id if previously generated in session."""
        return self._snapshots_by_snapshot_id.get(identifier) or self._snapshots_by_id.get(identifier)

    def compute_fingerprint(self, profile: Any) -> str:
        """Pure helper to compute the deterministic profile fingerprint without constructing or persisting a snapshot."""
        return self._twin_agent.compute_fingerprint(profile)

