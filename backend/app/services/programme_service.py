"""Programme service managing the academic catalogue and knowledge graph."""

from typing import List, Optional

from app.domain.catalogue import get_synthetic_programmes
from app.domain.frames import ProgrammeFrame
from app.domain.frame_system import FrameRegistry, build_canonical_programme_hierarchy
from app.knowledge.graph import HydraKnowledgeGraph


class ProgrammeService:
    """Manages catalogue access and knowledge graph indexing."""

    def __init__(
        self,
        programmes: Optional[List[ProgrammeFrame]] = None,
        frame_registry: Optional[FrameRegistry] = None,
    ) -> None:
        self._programmes: List[ProgrammeFrame] = (
            list(programmes) if programmes is not None else get_synthetic_programmes()
        )
        self._frame_registry = frame_registry or build_canonical_programme_hierarchy()
        self._graph = HydraKnowledgeGraph()
        self._graph.populate_from_programmes(self._programmes, registry=self._frame_registry)

    @property
    def frame_registry(self) -> FrameRegistry:
        """Returns the authoritative frame registry."""
        return self._frame_registry

    @property
    def graph(self) -> HydraKnowledgeGraph:
        """Returns the semantic knowledge graph."""
        return self._graph

    def get_all(self) -> List[ProgrammeFrame]:
        """Returns all programmes in the catalogue."""
        return list(self._programmes)

    def get_by_id(self, programme_id: str) -> Optional[ProgrammeFrame]:
        """Returns a single programme by ID, or None if not found."""
        for prog in self._programmes:
            if prog.programme_id == programme_id:
                return prog
        return None

