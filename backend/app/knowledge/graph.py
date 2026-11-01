"""Semantic network implementation using NetworkX for Hydra.

Provides bounded traversal over academic entities, frame inheritance (IS_A),
developed skills, and downstream careers with explicit relationship provenance.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx

from app.domain.frames import ProgrammeFrame
from app.domain.frame_system import FrameRegistry


class RelationshipType:
    """Canonical typed relationships for Hydra's semantic network."""

    IS_A = "IS_A"
    PART_OF = "PART_OF"
    REQUIRES = "REQUIRES"
    PREREQUISITE_OF = "PREREQUISITE_OF"
    PROGRAMME_DEVELOPS_SKILL = "PROGRAMME_DEVELOPS_SKILL"
    SKILL_RELEVANT_TO_CAREER = "SKILL_RELEVANT_TO_CAREER"
    PROGRAMME_RELATED_TO_DISCIPLINE = "PROGRAMME_RELATED_TO_DISCIPLINE"
    PROGRAMME_LEADS_TO_CAREER = "PROGRAMME_LEADS_TO_CAREER"

    # Canonical aliases
    DEVELOPS_SKILL = "PROGRAMME_DEVELOPS_SKILL"
    RELEVANT_TO_CAREER = "SKILL_RELEVANT_TO_CAREER"
    LEADS_TO_CAREER = "PROGRAMME_LEADS_TO_CAREER"
    HAS_DISCIPLINE = "PROGRAMME_RELATED_TO_DISCIPLINE"


@dataclass(frozen=True)
class DiscoveredRelationship:
    """A verified edge discovered during semantic graph traversal."""

    source: str
    relationship: str
    target: str
    target_type: str
    source_type: str = "direct"  # "direct", "inherited", "traversed"
    provenance_path: List[str] = field(default_factory=list)


class HydraKnowledgeGraph:
    """In-memory typed MultiDiGraph semantic network."""

    def __init__(self) -> None:
        self._graph = nx.MultiDiGraph()

    @property
    def graph(self) -> nx.MultiDiGraph:
        """Returns the underlying NetworkX graph instance."""
        return self._graph

    def add_node(self, node_id: str, entity_type: str, name: Optional[str] = None) -> None:
        """Adds a typed entity node to the network."""
        if not node_id:
            raise ValueError("node_id cannot be empty")
        node_name = name or node_id
        self._graph.add_node(node_id, entity_type=entity_type, name=node_name)

    # Alias for convenience
    add_entity = add_node

    def add_relationship(
        self,
        source_id: str,
        relation_type: str,
        target_id: str,
        target_type: str = "unknown",
    ) -> None:
        """Adds a validated directed edge between two entity nodes."""
        if not self._graph.has_node(source_id):
            raise KeyError(f"Source node '{source_id}' does not exist in graph")
        if not self._graph.has_node(target_id):
            raise KeyError(f"Target node '{target_id}' does not exist in graph")

        effective_target_type = (
            target_type
            if target_type != "unknown"
            else self._graph.nodes[target_id].get("entity_type", "unknown")
        )

        # Cycle protection for IS_A hierarchy
        if relation_type == RelationshipType.IS_A:
            if source_id == target_id:
                raise ValueError(f"Self-referential IS_A edge detected on '{source_id}'")
            if self._graph.has_node(target_id) and self.has_is_a_path(target_id, source_id):
                raise ValueError(
                    f"Cyclic IS_A relationship detected: Cannot add IS_A relationship: closes a cycle between '{source_id}' and '{target_id}'"
                )

        self._graph.add_edge(
            source_id,
            target_id,
            key=relation_type,
            relation_type=relation_type,
            target_type=effective_target_type,
        )

    def has_is_a_path(self, start_id: str, target_id: str) -> bool:
        """Checks if a directed IS_A path exists from start_id to target_id."""
        visited: Set[str] = set()
        queue: List[str] = [start_id]
        while queue:
            curr = queue.pop(0)
            if curr == target_id:
                return True
            visited.add(curr)
            if self._graph.has_node(curr):
                for _, neighbor, data in self._graph.out_edges(curr, data=True):
                    if data.get("relation_type") == RelationshipType.IS_A and neighbor not in visited:
                        queue.append(neighbor)
        return False

    def sync_from_frame_registry(self, registry: FrameRegistry) -> None:
        """Synchronizes IS_A inheritance hierarchy from authoritative FrameRegistry."""
        # 1. Register all frame nodes
        for frame in registry.get_all_frames():
            if not self._graph.has_node(frame.frame_id):
                self.add_node(frame.frame_id, entity_type="frame", name=frame.frame_id)

        # 2. Add IS_A edges with cycle detection
        for frame in registry.get_all_frames():
            for parent_id in frame.parent_ids:
                if not self._graph.has_node(parent_id):
                    self.add_node(parent_id, entity_type="frame", name=parent_id)
                if not self._graph.has_edge(frame.frame_id, parent_id, key=RelationshipType.IS_A):
                    self.add_relationship(
                        frame.frame_id,
                        RelationshipType.IS_A,
                        parent_id,
                        target_type="frame",
                    )

    def populate_from_programmes(
        self,
        programmes: List[ProgrammeFrame],
        registry: Optional[FrameRegistry] = None,
    ) -> None:
        """Populates the knowledge graph from domain programme frames and optional frame registry."""
        if registry:
            self.sync_from_frame_registry(registry)

        for prog in programmes:
            # Add Programme node
            self.add_node(prog.programme_id, "programme", prog.title)

            # Link Programme to its parent frame if specified
            if prog.parent_frame_id:
                if not self._graph.has_node(prog.parent_frame_id):
                    self.add_node(prog.parent_frame_id, "frame", prog.parent_frame_id)
                self.add_relationship(
                    prog.programme_id,
                    RelationshipType.IS_A,
                    prog.parent_frame_id,
                    target_type="frame",
                )

            # Add Discipline node & relationship
            disc_id = f"DISC_{prog.discipline.upper().replace(' ', '_')}"
            if not self._graph.has_node(disc_id):
                self.add_node(disc_id, "discipline", prog.discipline)
            self.add_relationship(
                prog.programme_id,
                RelationshipType.PROGRAMME_RELATED_TO_DISCIPLINE,
                disc_id,
                "discipline",
            )

            # Add Skills and Programme->Skill relationships
            for skill in prog.skills_developed:
                skill_id = f"SKILL_{skill.upper().replace(' ', '_')}"
                if not self._graph.has_node(skill_id):
                    self.add_node(skill_id, "skill", skill)
                self.add_relationship(
                    prog.programme_id,
                    RelationshipType.PROGRAMME_DEVELOPS_SKILL,
                    skill_id,
                    "skill",
                )

                # Link skill to relevant career paths for this programme
                for career in prog.career_paths:
                    career_id = f"CAREER_{career.upper().replace(' ', '_')}"
                    if not self._graph.has_node(career_id):
                        self.add_node(career_id, "career", career)

                    # Skill -> Career
                    if not self._graph.has_edge(
                        skill_id, career_id, key=RelationshipType.SKILL_RELEVANT_TO_CAREER
                    ):
                        self.add_relationship(
                            skill_id,
                            RelationshipType.SKILL_RELEVANT_TO_CAREER,
                            career_id,
                            "career",
                        )

            # Direct Programme -> Career
            for career in prog.career_paths:
                career_id = f"CAREER_{career.upper().replace(' ', '_')}"
                if not self._graph.has_node(career_id):
                    self.add_node(career_id, "career", career)
                self.add_relationship(
                    prog.programme_id,
                    RelationshipType.PROGRAMME_LEADS_TO_CAREER,
                    career_id,
                    "career",
                )

    def discover_pathways(
        self, programme_id: str, max_depth: int = 2
    ) -> List[DiscoveredRelationship]:
        """Performs bounded graph traversal discovering Programme -> Skill -> Career paths.

        Distinguishes:
        - direct: relationships originating directly on this programme
        - inherited: relationships inherited from ancestor frames via IS_A
        - traversed: multi-hop discovered relationships (Skill -> Career)

        Safely enforces bounded depth and cycle detection.
        """
        if not self._graph.has_node(programme_id):
            return []

        discovered: List[DiscoveredRelationship] = []
        visited_edges: Set[tuple] = set()

        prog_name = self._graph.nodes[programme_id].get("name", programme_id)

        # 1. Discover Direct Outgoing Edges from Programme
        direct_skills: Set[str] = set()
        for _, neighbor, key, data in self._graph.out_edges(programme_id, data=True, keys=True):
            edge_tuple = (programme_id, key, neighbor)
            if edge_tuple not in visited_edges and key != RelationshipType.IS_A:
                visited_edges.add(edge_tuple)
                target_name = self._graph.nodes[neighbor].get("name", neighbor)
                rel_type = data.get("relation_type", key)
                target_type = data.get("target_type", "unknown")
                if target_type == "skill":
                    direct_skills.add(neighbor)

                discovered.append(
                    DiscoveredRelationship(
                        source=prog_name,
                        relationship=rel_type,
                        target=target_name,
                        target_type=target_type,
                        source_type="direct",
                        provenance_path=[programme_id, neighbor],
                    )
                )

        # 2. Discover Inherited Skills & Careers from IS_A Ancestors
        ancestor_queue: List[Tuple[str, List[str]]] = []
        for _, parent, key in self._graph.out_edges(programme_id, keys=True):
            if key == RelationshipType.IS_A:
                ancestor_queue.append((parent, [programme_id, parent]))

        seen_ancestors: Set[str] = set()
        while ancestor_queue:
            curr_anc, curr_path = ancestor_queue.pop(0)
            if curr_anc in seen_ancestors:
                continue
            seen_ancestors.add(curr_anc)

            # Check edges from this ancestor
            for _, anc_neighbor, anc_key, anc_data in self._graph.out_edges(curr_anc, data=True, keys=True):
                if anc_key == RelationshipType.IS_A and anc_neighbor not in seen_ancestors:
                    ancestor_queue.append((anc_neighbor, curr_path + [anc_neighbor]))
                elif anc_key in (
                    RelationshipType.PROGRAMME_DEVELOPS_SKILL,
                    RelationshipType.PROGRAMME_LEADS_TO_CAREER,
                ):
                    edge_tuple = (programme_id, anc_key, anc_neighbor)
                    if edge_tuple not in visited_edges:
                        visited_edges.add(edge_tuple)
                        target_name = self._graph.nodes[anc_neighbor].get("name", anc_neighbor)
                        rel_type = anc_data.get("relation_type", anc_key)
                        target_type = anc_data.get("target_type", "unknown")
                        if target_type == "skill":
                            direct_skills.add(anc_neighbor)

                        discovered.append(
                            DiscoveredRelationship(
                                source=prog_name,
                                relationship=rel_type,
                                target=target_name,
                                target_type=target_type,
                                source_type="inherited",
                                provenance_path=curr_path + [anc_neighbor],
                            )
                        )

        # 3. Multi-hop Traversal: Skill -> Career (depth 2)
        if max_depth >= 2:
            for skill_node in sorted(direct_skills):
                skill_name = self._graph.nodes[skill_node].get("name", skill_node)
                for _, career_node, sub_key, sub_data in self._graph.out_edges(
                    skill_node, data=True, keys=True
                ):
                    sub_edge_tuple = (skill_node, sub_key, career_node)
                    if sub_edge_tuple not in visited_edges:
                        visited_edges.add(sub_edge_tuple)
                        career_name = self._graph.nodes[career_node].get("name", career_node)
                        discovered.append(
                            DiscoveredRelationship(
                                source=skill_name,
                                relationship=sub_data.get("relation_type", sub_key),
                                target=career_name,
                                target_type=sub_data.get("target_type", "unknown"),
                                source_type="traversed",
                                provenance_path=[skill_node, career_node],
                            )
                        )

        # Deterministic sorting
        discovered.sort(key=lambda r: (r.source, r.relationship, r.target))
        return discovered

    def get_connected_skills(self, programme_id: str) -> List[str]:
        """Returns list of skill names directly or inheritantly developed by the programme."""
        if not self._graph.has_node(programme_id):
            return []
        skills = []
        pathways = self.discover_pathways(programme_id, max_depth=1)
        for p in pathways:
            if p.target_type == "skill":
                skills.append(p.target)
        return sorted(list(set(skills)))

    def get_connected_careers(self, programme_id: str) -> List[str]:
        """Returns list of career names reached directly, inheritantly, or via skills."""
        if not self._graph.has_node(programme_id):
            return []
        careers = set()
        pathways = self.discover_pathways(programme_id, max_depth=2)
        for p in pathways:
            if p.target_type == "career":
                careers.add(p.target)
        return sorted(list(careers))
