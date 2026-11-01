"""Unit tests for NetworkX semantic network and pathway traversal."""

import pytest
from app.domain.catalogue import get_synthetic_programmes
from app.knowledge.graph import HydraKnowledgeGraph, RelationshipType


@pytest.fixture
def populated_graph() -> HydraKnowledgeGraph:
    graph = HydraKnowledgeGraph()
    programmes = get_synthetic_programmes()
    graph.populate_from_programmes(programmes)
    return graph


def test_programme_skill_career_traversal(populated_graph: HydraKnowledgeGraph):
    """Verifies that Programme -> Skill -> Career paths are discovered accurately."""
    pathways = populated_graph.discover_pathways("SYNTH_IN_CS_01", max_depth=2)
    assert len(pathways) > 0

    # Check that skills and careers exist in discovered pathways
    targets = {p.target for p in pathways}
    assert "Algorithms" in targets
    assert "Software Engineer" in targets


def test_correct_relationship_types(populated_graph: HydraKnowledgeGraph):
    """Verifies relationship types on edges match canonical ontology."""
    pathways = populated_graph.discover_pathways("SYNTH_IN_CS_01", max_depth=2)
    rel_types = {p.relationship for p in pathways}

    assert RelationshipType.PROGRAMME_DEVELOPS_SKILL in rel_types
    assert RelationshipType.SKILL_RELEVANT_TO_CAREER in rel_types


def test_missing_node_handling_returns_empty(populated_graph: HydraKnowledgeGraph):
    """Verifies querying a non-existent programme returns empty list without raising."""
    pathways = populated_graph.discover_pathways("NON_EXISTENT_PROG", max_depth=2)
    assert pathways == []
    skills = populated_graph.get_connected_skills("NON_EXISTENT_PROG")
    assert skills == []
    careers = populated_graph.get_connected_careers("NON_EXISTENT_PROG")
    assert careers == []


def test_absence_of_unrelated_careers(populated_graph: HydraKnowledgeGraph):
    """Verifies CS programme does not traverse to unrelated careers like Biomedical Researcher."""
    cs_careers = populated_graph.get_connected_careers("SYNTH_IN_CS_01")
    assert "Software Engineer" in cs_careers
    assert "Biomedical Researcher" not in cs_careers


def test_bounded_traversal_depth_1_vs_depth_2(populated_graph: HydraKnowledgeGraph):
    """Verifies depth=1 traversal does not include skill-to-career downstream hops."""
    depth_1_paths = populated_graph.discover_pathways("SYNTH_IN_CS_01", max_depth=1)
    depth_2_paths = populated_graph.discover_pathways("SYNTH_IN_CS_01", max_depth=2)

    # In depth 1, only outgoing edges from Programme are retrieved
    depth_1_sources = {p.source for p in depth_1_paths}
    assert "Algorithms" not in depth_1_sources  # Skill cannot be source in depth 1

    # In depth 2, Skill becomes source for career hops
    depth_2_sources = {p.source for p in depth_2_paths}
    assert "Algorithms" in depth_2_sources
    assert len(depth_2_paths) > len(depth_1_paths)


def test_is_a_relationship_sync_from_frame_registry():
    """Verifies graph synchronization with FrameRegistry creates IS_A edges."""
    from app.domain.frame_system import create_canonical_frame_registry

    registry = create_canonical_frame_registry()
    graph = HydraKnowledgeGraph()
    graph.sync_from_frame_registry(registry)

    # FRAME_SPEC_CS -> FRAME_COMPUTING_BASE -> FRAME_ENGINEERING_BASE -> FRAME_PROGRAMME_BASE
    assert graph.has_is_a_path("FRAME_SPEC_CS", "FRAME_COMPUTING_BASE") is True
    assert graph.has_is_a_path("FRAME_SPEC_CS", "FRAME_ENGINEERING_BASE") is True
    assert graph.has_is_a_path("FRAME_SPEC_CS", "FRAME_PROGRAMME_BASE") is True

    # Life sciences branch is separate
    assert graph.has_is_a_path("FRAME_SPEC_CS", "FRAME_LIFE_SCIENCES_BASE") is False
    assert graph.has_is_a_path("FRAME_SPEC_BIO", "FRAME_LIFE_SCIENCES_BASE") is True


def test_is_a_cycle_detection_rejection():
    """Graph rejects any IS_A edge insertion that would create a directed cycle."""
    graph = HydraKnowledgeGraph()
    graph.add_entity("NODE_A", "Frame")
    graph.add_entity("NODE_B", "Frame")
    graph.add_entity("NODE_C", "Frame")

    graph.add_relationship("NODE_A", RelationshipType.IS_A, "NODE_B")
    graph.add_relationship("NODE_B", RelationshipType.IS_A, "NODE_C")

    # Closing cycle: C -> A
    with pytest.raises(ValueError, match="Cannot add IS_A relationship: closes a cycle"):
        graph.add_relationship("NODE_C", RelationshipType.IS_A, "NODE_A")


def test_relationship_provenance_and_source_type(populated_graph: HydraKnowledgeGraph):
    """Verifies discovered relationships have explicit source_type and provenance_path."""
    from app.domain.frame_system import create_canonical_frame_registry

    registry = create_canonical_frame_registry()
    populated_graph.sync_from_frame_registry(registry)

    pathways = populated_graph.discover_pathways("SYNTH_IN_CS_01", max_depth=2)
    assert len(pathways) > 0

    # Direct edges
    direct_edges = [p for p in pathways if p.source_type == "direct"]
    assert len(direct_edges) > 0
    for de in direct_edges:
        assert de.source == "B.Tech. in Computer Science (Synthetic)"
        assert de.provenance_path[0] == "SYNTH_IN_CS_01"

    # Multi-hop traversed edges
    traversed_edges = [p for p in pathways if p.source_type == "traversed"]
    assert len(traversed_edges) > 0
    for te in traversed_edges:
        assert len(te.provenance_path) >= 2


def test_programme_service_integration_with_registry():
    """Verifies ProgrammeService seamlessly integrates FrameRegistry with HydraKnowledgeGraph."""
    from app.services.programme_service import ProgrammeService

    service = ProgrammeService()
    programmes = service.get_all()
    assert len(programmes) == 4

    cs_prog = service.get_by_id("SYNTH_IN_CS_01")
    assert cs_prog is not None
    assert cs_prog.parent_frame_id == "FRAME_SPEC_CS"

    # Verify graph inside service has IS_A edges
    assert service.graph.has_is_a_path("FRAME_SPEC_CS", "FRAME_PROGRAMME_BASE") is True

