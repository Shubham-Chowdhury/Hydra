"""Generalised Frame-Based Knowledge Representation System for Hydra.

Provides structured frame definitions, inheritance trees, slot resolution,
provenance tracking, deterministic multiple inheritance, conflict arbitration,
and cycle detection.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class MergePolicy(str, Enum):
    """Policies governing how inherited slot values are merged."""

    OVERRIDE = "override"
    MERGE_UNIQUE = "merge_unique"
    REQUIRE_CONSISTENCY = "require_consistency"


class SlotSourceType(str, Enum):
    """Origin of a resolved slot value."""

    EXPLICIT = "explicit"
    EXPLICIT_CHILD = "explicit"
    INHERITED_EXPLICIT = "inherited_explicit"
    INHERITED_DEFAULT = "inherited_default"
    DEFAULT = "default"


@dataclass(frozen=True)
class ConflictRecord:
    """Audit record of a multiple-inheritance conflict between parent frames."""

    slot_name: str
    competing_values: Dict[str, Any]
    competing_frames: List[str]
    is_decision_relevant: bool
    resolution_outcome: str
    is_resolved: bool

    @property
    def resolved_by(self) -> Optional[str]:
        """Frame ID that resolved this conflict, if resolved by child override."""
        if "RESOLVED_BY_CHILD_OVERRIDE: Child frame '" in self.resolution_outcome:
            try:
                return self.resolution_outcome.split("'")[1]
            except IndexError:
                return None
        return None


@dataclass(frozen=True)
class SlotModificationRecord:
    """Audit record of an explicit collection modification (removal or replacement)."""

    operation: str  # "REMOVE" or "REPLACE"
    slot_name: str
    modified_by_frame_id: str
    affected_items: List[Any]
    details: str


@dataclass
class FrameSlot:
    """A declared attribute or constraint slot within a frame."""

    name: str
    value: Any
    value_type: str = "any"
    merge_policy: MergePolicy = MergePolicy.OVERRIDE
    is_decision_relevant: bool = False
    is_default: bool = False
    removed_items: List[Any] = field(default_factory=list)

    def __init__(
        self,
        name: str,
        value: Any = None,
        value_type: str = "any",
        merge_policy: Optional[MergePolicy] = None,
        override_policy: Optional[MergePolicy] = None,
        is_decision_relevant: bool = False,
        is_default: bool = False,
        removed_items: Optional[List[Any]] = None,
    ) -> None:
        self.name = name
        self.value = value if value is not None else []
        self.value_type = value_type
        # Accept either merge_policy or override_policy
        self.merge_policy = (
            merge_policy
            if merge_policy is not None
            else (override_policy or MergePolicy.OVERRIDE)
        )
        self.is_decision_relevant = is_decision_relevant
        self.is_default = is_default
        self.removed_items = list(removed_items or [])


@dataclass(frozen=True)
class SlotResolution:
    """The fully arbitrated result of resolving a slot through frame inheritance."""

    slot_name: str
    resolved_value: Any
    source_type: SlotSourceType
    source_frame_id: str
    inheritance_path: List[str]
    conflicts: List[ConflictRecord] = field(default_factory=list)
    is_conflicted: bool = False
    modifications: List[SlotModificationRecord] = field(default_factory=list)

    @property
    def effective_value(self) -> Any:
        """Alias for resolved_value."""
        return self.resolved_value

    @property
    def provenance_path(self) -> List[str]:
        """Alias for inheritance_path."""
        return self.inheritance_path

    @property
    def is_inherited(self) -> bool:
        """Whether this resolved value was inherited from an ancestor frame."""
        return self.source_type in (
            SlotSourceType.INHERITED_EXPLICIT,
            SlotSourceType.INHERITED_DEFAULT,
        )

    @property
    def has_unresolved_conflict(self) -> bool:
        """True if any conflict on this slot remains unresolved."""
        return any(not c.is_resolved for c in self.conflicts)

    @property
    def has_decision_relevant_conflict(self) -> bool:
        """True if any unresolved conflict on this slot is marked as decision-relevant."""
        return any(not c.is_resolved and c.is_decision_relevant for c in self.conflicts)


@dataclass
class FrameDefinition:
    """Structural definition of an entity frame in Hydra."""

    frame_id: str
    frame_type: str = "generic"
    parent_ids: List[str] = field(default_factory=list)
    slots: Dict[str, FrameSlot] = field(default_factory=dict)

    def __init__(
        self,
        frame_id: str,
        frame_type: str = "generic",
        parent_ids: Optional[List[str]] = None,
        parent_frame_ids: Optional[List[str]] = None,
        slots: Optional[Dict[str, FrameSlot]] = None,
    ) -> None:
        self.frame_id = frame_id
        self.frame_type = frame_type
        # Accept either parent_ids or parent_frame_ids
        p_ids = parent_ids if parent_ids is not None else (parent_frame_ids or [])
        self.parent_ids = list(p_ids)
        self.slots = dict(slots or {})

    def set_slot(
        self,
        name: str,
        value: Any = None,
        value_type: str = "any",
        merge_policy: MergePolicy = MergePolicy.OVERRIDE,
        is_decision_relevant: bool = False,
        is_default: bool = False,
        removed_items: Optional[List[Any]] = None,
    ) -> None:
        """Adds or updates a slot on this frame."""
        self.slots[name] = FrameSlot(
            name=name,
            value=value,
            value_type=value_type,
            merge_policy=merge_policy,
            is_decision_relevant=is_decision_relevant,
            is_default=is_default,
            removed_items=removed_items,
        )

    def get_slot(self, name: str) -> Optional[FrameSlot]:
        """Returns slot if explicitly declared on this frame."""
        return self.slots.get(name)


class FrameRegistry:
    """Registry managing frame definitions, inheritance resolution, and cycle validation."""

    def __init__(self) -> None:
        self._frames: Dict[str, FrameDefinition] = {}

    def register_frame(self, frame: FrameDefinition) -> None:
        """Registers a frame definition with validation of parents and cycle detection."""
        if not frame.frame_id or not frame.frame_id.strip():
            raise ValueError("Frame ID cannot be empty.")
        if not frame.frame_type or not frame.frame_type.strip():
            raise ValueError(f"Frame type cannot be empty for frame '{frame.frame_id}'.")

        # Check for unknown parent frames
        for pid in frame.parent_ids:
            if pid not in self._frames:
                raise ValueError(
                    f"Frame '{frame.frame_id}' references unknown parent frame '{pid}'."
                )

        # Temporarily place in registry to check for cycles
        self._frames[frame.frame_id] = frame
        try:
            self._detect_cycle(frame.frame_id)
        except Exception:
            del self._frames[frame.frame_id]
            raise

    # Alias for convenience
    register = register_frame

    def deregister_frame(self, frame_id: str) -> bool:
        """Deregisters a frame if it exists and has no child frames referencing it."""
        if frame_id not in self._frames:
            return False
        # Guard: check if any other frame references this frame as a parent
        for other in self._frames.values():
            if frame_id in other.parent_ids:
                raise ValueError(
                    f"Cannot deregister frame '{frame_id}': referenced as parent by '{other.frame_id}'."
                )
        del self._frames[frame_id]
        return True


    def get_frame(self, frame_id: str) -> Optional[FrameDefinition]:
        """Retrieves a frame definition by ID."""
        return self._frames.get(frame_id)

    def has_frame(self, frame_id: str) -> bool:
        """Checks if a frame exists in the registry."""
        return frame_id in self._frames

    def get_all_frames(self) -> List[FrameDefinition]:
        """Returns all registered frames."""
        return list(self._frames.values())

    def _detect_cycle(self, start_id: str) -> None:
        """Detects inheritance cycles starting from start_id using DFS."""
        visited: Set[str] = set()
        recursion_stack: List[str] = []

        def dfs(curr: str) -> None:
            visited.add(curr)
            recursion_stack.append(curr)

            node = self._frames.get(curr)
            if node:
                for parent_id in node.parent_ids:
                    if parent_id not in visited:
                        dfs(parent_id)
                    elif parent_id in recursion_stack:
                        cycle_path = " -> ".join(recursion_stack + [parent_id])
                        raise ValueError(
                            f"Cyclic frame inheritance detected: {cycle_path}"
                        )

            recursion_stack.pop()

        dfs(start_id)

    def get_ancestors_topological(self, frame_id: str) -> List[str]:
        """Returns ordered list of ancestors (breadth-first, deterministic, parent order independent)."""
        if frame_id not in self._frames:
            raise ValueError(f"Frame '{frame_id}' not found in registry.")

        # Deterministic BFS collection of ancestors
        queue: List[str] = list(sorted(self._frames[frame_id].parent_ids))
        seen: Set[str] = set(queue)
        ancestors: List[str] = []

        while queue:
            current = queue.pop(0)
            ancestors.append(current)
            current_frame = self._frames.get(current)
            if current_frame:
                # Sort parent IDs to ensure registration-order independence
                for p in sorted(current_frame.parent_ids):
                    if p not in seen:
                        seen.add(p)
                        queue.append(p)

        return ancestors

    def resolve_slots(self, frame_id: str) -> Dict[str, SlotResolution]:
        """Deterministically resolves all slots for a frame across its inheritance hierarchy.

        Semantics:
        1. Explicit child slot always overrides inherited slots.
        2. Merges collection slots when MergePolicy.MERGE_UNIQUE is specified.
        3. Flags unresolvable conflicts between multiple parents.
        4. Distinguishes defaults from verified facts.
        """
        frame = self._frames.get(frame_id)
        if not frame:
            raise ValueError(f"Frame '{frame_id}' not found in registry.")

        resolved: Dict[str, SlotResolution] = {}
        ancestors = self.get_ancestors_topological(frame_id)

        # Collect all slot names across child and all ancestors
        all_slot_names: Set[str] = set(frame.slots.keys())
        for anc_id in ancestors:
            anc = self._frames.get(anc_id)
            if anc:
                all_slot_names.update(anc.slots.keys())

        # Resolve each slot independently and deterministically
        for slot_name in sorted(all_slot_names):
            resolved[slot_name] = self._resolve_single_slot(
                frame=frame, slot_name=slot_name, ancestors=ancestors
            )

        return resolved

    def _resolve_single_slot(
        self, frame: FrameDefinition, slot_name: str, ancestors: List[str]
    ) -> SlotResolution:
        """Resolves a single slot with conflict detection and merge policies."""
        explicit_slot = frame.slots.get(slot_name)

        # 1. Gather all definitions from parents
        parent_contributions: List[Tuple[str, FrameSlot, List[str]]] = []
        for anc_id in ancestors:
            anc = self._frames.get(anc_id)
            if anc and slot_name in anc.slots:
                # Compute path from target frame to this ancestor
                path = self._compute_path(frame.frame_id, anc_id)
                parent_contributions.append((anc_id, anc.slots[slot_name], path))

        # Case A: Child explicitly defines this slot
        if explicit_slot is not None:
            # Check if parents had competing values
            conflicts: List[ConflictRecord] = []
            modifications: List[SlotModificationRecord] = []
            if len(parent_contributions) > 1:
                unique_parent_vals = {
                    anc_id: str(slot.value) for anc_id, slot, _ in parent_contributions
                }
                if len(set(unique_parent_vals.values())) > 1:
                    conflicts.append(
                        ConflictRecord(
                            slot_name=slot_name,
                            competing_values=unique_parent_vals,
                            competing_frames=[anc_id for anc_id, _, _ in parent_contributions],
                            is_decision_relevant=explicit_slot.is_decision_relevant,
                            resolution_outcome=(
                                f"RESOLVED_BY_CHILD_OVERRIDE: Child frame '{frame.frame_id}' "
                                f"explicitly overrides parent values."
                            ),
                            is_resolved=True,
                        )
                    )

            # Guard against removing mandatory admission requirements
            if explicit_slot.removed_items:
                if explicit_slot.is_decision_relevant or slot_name in (
                    "academic_prerequisites",
                    "entrance_prerequisites",
                    "mandatory_subjects",
                ):
                    raise ValueError(
                        f"Mandatory admission requirements cannot be removed through a descriptive collection operation on slot '{slot_name}'."
                    )

            # Check if merge_policy is MERGE_UNIQUE for collections
            if explicit_slot.merge_policy == MergePolicy.MERGE_UNIQUE and isinstance(
                explicit_slot.value, (list, set)
            ):
                merged_set = set(deepcopy(explicit_slot.value))
                for _, p_slot, _ in parent_contributions:
                    if isinstance(p_slot.value, (list, set)):
                        merged_set.update(p_slot.value)

                # Process explicit removal of inherited collection items
                if explicit_slot.removed_items:
                    actually_removed = sorted([x for x in explicit_slot.removed_items if x in merged_set])
                    merged_set.difference_update(explicit_slot.removed_items)
                    modifications.append(
                        SlotModificationRecord(
                            operation="REMOVE",
                            slot_name=slot_name,
                            modified_by_frame_id=frame.frame_id,
                            affected_items=actually_removed,
                            details=(
                                f"Child frame '{frame.frame_id}' explicitly removed {actually_removed} "
                                f"from inherited collection '{slot_name}'."
                            ),
                        )
                    )

                final_val = sorted(list(merged_set)) if isinstance(explicit_slot.value, list) else merged_set
                return SlotResolution(
                    slot_name=slot_name,
                    resolved_value=final_val,
                    source_type=SlotSourceType.EXPLICIT,
                    source_frame_id=frame.frame_id,
                    inheritance_path=[frame.frame_id],
                    conflicts=conflicts,
                    is_conflicted=False,
                    modifications=modifications,
                )

            # Collection replacement under OVERRIDE
            if explicit_slot.merge_policy == MergePolicy.OVERRIDE and isinstance(
                explicit_slot.value, (list, set)
            ) and parent_contributions:
                parent_items = set()
                for _, p_slot, _ in parent_contributions:
                    if isinstance(p_slot.value, (list, set)):
                        parent_items.update(p_slot.value)
                if parent_items:
                    modifications.append(
                        SlotModificationRecord(
                            operation="REPLACE",
                            slot_name=slot_name,
                            modified_by_frame_id=frame.frame_id,
                            affected_items=sorted(list(parent_items)),
                            details=(
                                f"Child frame '{frame.frame_id}' explicitly replaced inherited collection '{slot_name}'."
                            ),
                        )
                    )

            source_type = (
                SlotSourceType.DEFAULT if explicit_slot.is_default else SlotSourceType.EXPLICIT
            )
            return SlotResolution(
                slot_name=slot_name,
                resolved_value=deepcopy(explicit_slot.value),
                source_type=source_type,
                source_frame_id=frame.frame_id,
                inheritance_path=[frame.frame_id],
                conflicts=conflicts,
                is_conflicted=False,
                modifications=modifications,
            )

        # Case B: Child does NOT explicitly define this slot - inherit from parents
        if not parent_contributions:
            raise KeyError(f"Slot '{slot_name}' unexpectedly absent across hierarchy.")

        # Check if multiple parents provide different scalar values
        unique_parent_vals = {
            anc_id: slot.value for anc_id, slot, _ in parent_contributions
        }
        val_representations = {
            anc_id: str(v) for anc_id, v in unique_parent_vals.items()
        }

        # Check policy
        first_policy = parent_contributions[0][1].merge_policy
        is_decision_relevant = any(s.is_decision_relevant for _, s, _ in parent_contributions)

        # Policy MERGE_UNIQUE on collection
        if first_policy == MergePolicy.MERGE_UNIQUE and all(
            isinstance(s.value, (list, set)) for _, s, _ in parent_contributions
        ):
            merged_collection = set()
            all_paths: List[str] = []
            for anc_id, slot, path in parent_contributions:
                merged_collection.update(slot.value)
                all_paths.extend(path)
            sorted_unique_path = list(dict.fromkeys(all_paths))

            return SlotResolution(
                slot_name=slot_name,
                resolved_value=sorted(list(merged_collection)),
                source_type=SlotSourceType.INHERITED_EXPLICIT,
                source_frame_id=parent_contributions[0][0],
                inheritance_path=sorted_unique_path,
                conflicts=[],
                is_conflicted=False,
            )

        # Scalar values comparison
        if len(set(val_representations.values())) > 1:
            # Conflicting values from parents without child override!
            conflict = ConflictRecord(
                slot_name=slot_name,
                competing_values=val_representations,
                competing_frames=[anc_id for anc_id, _, _ in parent_contributions],
                is_decision_relevant=is_decision_relevant,
                resolution_outcome=(
                    f"UNRESOLVED_CONFLICT: Competing values from parents "
                    f"{list(unique_parent_vals.keys())} without child override."
                ),
                is_resolved=False,
            )
            # Deterministic fallback to first alphabetically sorted parent, but flag conflict
            sorted_parent_ids = sorted(unique_parent_vals.keys())
            chosen_parent_id = sorted_parent_ids[0]
            chosen_contribution = next(c for c in parent_contributions if c[0] == chosen_parent_id)

            return SlotResolution(
                slot_name=slot_name,
                resolved_value=deepcopy(chosen_contribution[1].value),
                source_type=(
                    SlotSourceType.INHERITED_DEFAULT
                    if chosen_contribution[1].is_default
                    else SlotSourceType.INHERITED_EXPLICIT
                ),
                source_frame_id=chosen_parent_id,
                inheritance_path=chosen_contribution[2],
                conflicts=[conflict],
                is_conflicted=is_decision_relevant,  # Unresolved conflict: only flags conflict if decision-relevant
            )

        # Compatible / Single parent contribution
        chosen = parent_contributions[0]
        source_type = (
            SlotSourceType.INHERITED_DEFAULT
            if chosen[1].is_default
            else SlotSourceType.INHERITED_EXPLICIT
        )
        return SlotResolution(
            slot_name=slot_name,
            resolved_value=deepcopy(chosen[1].value),
            source_type=source_type,
            source_frame_id=chosen[0],
            inheritance_path=chosen[2],
            conflicts=[],
            is_conflicted=False,
        )

    def _compute_path(self, start_id: str, target_id: str) -> List[str]:
        """Computes shortest path from start_id to target_id."""
        if start_id == target_id:
            return [start_id]
        queue: List[List[str]] = [[start_id]]
        seen: Set[str] = {start_id}
        while queue:
            path = queue.pop(0)
            node_id = path[-1]
            node = self._frames.get(node_id)
            if node:
                for p in sorted(node.parent_ids):
                    if p == target_id:
                        return path + [p]
                    if p not in seen:
                        seen.add(p)
                        queue.append(path + [p])
        return [start_id, target_id]

    # Alias for convenience
    resolve_frame = resolve_slots



def build_canonical_programme_hierarchy() -> FrameRegistry:
    """Builds the canonical demonstration frame hierarchy for Hydra academic programmes."""
    reg = FrameRegistry()

    # 0. Base Student Frame (Phase 4 Twin Agent foundation)
    student_base = FrameDefinition(frame_id="FRAME_STUDENT_BASE", frame_type="student_template")
    student_base.set_slot("currency", "INR", value_type="str", is_default=True)
    student_base.set_slot("cost_basis", "tuition_only_total", value_type="str", is_default=True)
    student_base.set_slot("grading_scale_default", "percentage", value_type="str", is_default=True)
    student_base.set_slot("status", "active", value_type="str", is_default=True)
    student_base.set_slot("preferred_locations", [], value_type="list", is_default=True)
    student_base.set_slot("preferred_disciplines", [], value_type="list", is_default=True)
    student_base.set_slot("career_goals", [], value_type="list", is_default=True)
    student_base.set_slot("is_synthetic", True, value_type="bool", is_default=True)
    reg.register_frame(student_base)

    # 1. Base Programme Frame
    base = FrameDefinition(frame_id="FRAME_PROGRAMME_BASE", frame_type="programme_template")
    base.set_slot("duration_years", 4, value_type="int", is_default=True)
    base.set_slot("currency", "INR", value_type="str", is_default=True)
    base.set_slot("cost_basis", "tuition_only_total", value_type="str", is_default=True)
    base.set_slot("is_synthetic", True, value_type="bool", is_default=True)
    reg.register_frame(base)

    # 2. Engineering Category
    eng = FrameDefinition(
        frame_id="FRAME_ENGINEERING_BASE",
        frame_type="academic_category",
        parent_ids=["FRAME_PROGRAMME_BASE"],
    )
    eng.set_slot("broad_discipline", "Engineering", value_type="str")
    eng.set_slot("accreditation_body", "DEMO_ACCREDITATION_BOARD", value_type="str")
    reg.register_frame(eng)

    # 3. Computing Subcategory
    comp = FrameDefinition(
        frame_id="FRAME_COMPUTING_BASE",
        frame_type="academic_category",
        parent_ids=["FRAME_ENGINEERING_BASE"],
    )
    comp.set_slot("discipline", "Computer Science", value_type="str")
    comp.set_slot(
        "skills_developed",
        ["Programming", "Algorithms", "Data Structures"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    comp.set_slot(
        "career_paths",
        ["Software Engineer"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(comp)

    # 4. Specialised Computing Branches
    # A. Computer Science Specialisation
    cs_spec = FrameDefinition(
        frame_id="FRAME_SPEC_CS",
        frame_type="programme_template",
        parent_ids=["FRAME_COMPUTING_BASE"],
    )
    cs_spec.set_slot(
        "skills_developed",
        ["Software Architecture"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    cs_spec.set_slot(
        "career_paths",
        ["Systems Architect"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(cs_spec)

    # B. Data Science Specialisation
    ds_spec = FrameDefinition(
        frame_id="FRAME_SPEC_DS",
        frame_type="programme_template",
        parent_ids=["FRAME_COMPUTING_BASE"],
    )
    ds_spec.set_slot("discipline", "Data Science", value_type="str")  # Child override of discipline
    ds_spec.set_slot(
        "skills_developed",
        ["Machine Learning", "Statistical Modeling", "Python Programming"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    ds_spec.set_slot(
        "career_paths",
        ["Data Scientist", "Machine Learning Engineer"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(ds_spec)

    # 5. Life Sciences Category
    life = FrameDefinition(
        frame_id="FRAME_LIFE_SCIENCES_BASE",
        frame_type="academic_category",
        parent_ids=["FRAME_PROGRAMME_BASE"],
    )
    life.set_slot("broad_discipline", "Life Sciences", value_type="str")
    reg.register_frame(life)

    # 6. Biotechnology Specialisation
    bio_spec = FrameDefinition(
        frame_id="FRAME_SPEC_BIO",
        frame_type="programme_template",
        parent_ids=["FRAME_LIFE_SCIENCES_BASE"],
    )
    bio_spec.set_slot("discipline", "Biotechnology", value_type="str")
    bio_spec.set_slot(
        "skills_developed",
        ["Molecular Biology", "Bioinformatics", "Biochemical Analysis"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    bio_spec.set_slot(
        "career_paths",
        ["Biomedical Researcher", "Bioinformatics Analyst"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(bio_spec)

    # 7. Robotics Specialisation (Child of Engineering Base)
    rob_spec = FrameDefinition(
        frame_id="FRAME_SPEC_ROB",
        frame_type="programme_template",
        parent_ids=["FRAME_ENGINEERING_BASE"],
    )
    rob_spec.set_slot("discipline", "Robotics", value_type="str")
    rob_spec.set_slot(
        "skills_developed",
        ["Robotic Control Systems", "Embedded AI", "Computer Vision"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    rob_spec.set_slot(
        "career_paths",
        ["Robotics Engineer", "Autonomous Systems Specialist"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(rob_spec)

    # 8. Medicine & Health Sciences
    med_base = FrameDefinition(
        frame_id="FRAME_MEDICINE_BASE",
        frame_type="academic_category",
        parent_ids=["FRAME_PROGRAMME_BASE"],
    )
    med_base.set_slot("broad_discipline", "Medicine & Health Sciences", value_type="str")
    reg.register_frame(med_base)

    mbbs_spec = FrameDefinition(
        frame_id="FRAME_SPEC_MBBS",
        frame_type="programme_template",
        parent_ids=["FRAME_MEDICINE_BASE"],
    )
    mbbs_spec.set_slot("discipline", "Medicine & Surgery", value_type="str")
    mbbs_spec.set_slot(
        "skills_developed",
        ["Clinical Diagnostics", "Pathology", "Surgical Anatomy", "Patient Care"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    mbbs_spec.set_slot(
        "career_paths",
        ["Physician", "Medical Specialist", "Clinical Researcher"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(mbbs_spec)

    pharm_spec = FrameDefinition(
        frame_id="FRAME_SPEC_PHARM",
        frame_type="programme_template",
        parent_ids=["FRAME_MEDICINE_BASE"],
    )
    pharm_spec.set_slot("discipline", "Pharmacy", value_type="str")
    pharm_spec.set_slot(
        "skills_developed",
        ["Pharmacology", "Drug Formulation", "Medicinal Chemistry"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    pharm_spec.set_slot(
        "career_paths",
        ["Pharmacist", "Clinical Pharmacologist", "Drug Safety Specialist"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(pharm_spec)

    # 9. Law & Legal Studies
    law_base = FrameDefinition(
        frame_id="FRAME_LAW_BASE",
        frame_type="academic_category",
        parent_ids=["FRAME_PROGRAMME_BASE"],
    )
    law_base.set_slot("broad_discipline", "Law & Legal Studies", value_type="str")
    reg.register_frame(law_base)

    llb_spec = FrameDefinition(
        frame_id="FRAME_SPEC_LLB",
        frame_type="programme_template",
        parent_ids=["FRAME_LAW_BASE"],
    )
    llb_spec.set_slot("discipline", "Law", value_type="str")
    llb_spec.set_slot(
        "skills_developed",
        ["Constitutional Law", "Legal Drafting", "Jurisprudence", "Advocacy"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    llb_spec.set_slot(
        "career_paths",
        ["Advocate / Litigator", "Corporate Counsel", "Legal Analyst"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(llb_spec)

    # 10. Business & Management
    mgmt_base = FrameDefinition(
        frame_id="FRAME_MANAGEMENT_BASE",
        frame_type="academic_category",
        parent_ids=["FRAME_PROGRAMME_BASE"],
    )
    mgmt_base.set_slot("broad_discipline", "Business & Management", value_type="str")
    reg.register_frame(mgmt_base)

    bba_spec = FrameDefinition(
        frame_id="FRAME_SPEC_BBA",
        frame_type="programme_template",
        parent_ids=["FRAME_MANAGEMENT_BASE"],
    )
    bba_spec.set_slot("discipline", "Business Administration", value_type="str")
    bba_spec.set_slot(
        "skills_developed",
        ["Financial Analysis", "Strategic Management", "Marketing Analytics", "Operations"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    bba_spec.set_slot(
        "career_paths",
        ["Management Consultant", "Business Operations Lead", "Product Strategist"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(bba_spec)

    # 11. Design & Architecture
    design_base = FrameDefinition(
        frame_id="FRAME_DESIGN_BASE",
        frame_type="academic_category",
        parent_ids=["FRAME_PROGRAMME_BASE"],
    )
    design_base.set_slot("broad_discipline", "Design & Architecture", value_type="str")
    reg.register_frame(design_base)

    bdes_spec = FrameDefinition(
        frame_id="FRAME_SPEC_BDES",
        frame_type="programme_template",
        parent_ids=["FRAME_DESIGN_BASE"],
    )
    bdes_spec.set_slot("discipline", "Design", value_type="str")
    bdes_spec.set_slot(
        "skills_developed",
        ["User Experience (UX) Design", "Interaction Design", "Prototyping", "Design Systems"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    bdes_spec.set_slot(
        "career_paths",
        ["Product Designer", "UI/UX Lead", "Design Technologist"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(bdes_spec)

    # 12. Pure & Applied Sciences
    sci_base = FrameDefinition(
        frame_id="FRAME_SCIENCES_BASE",
        frame_type="academic_category",
        parent_ids=["FRAME_PROGRAMME_BASE"],
    )
    sci_base.set_slot("broad_discipline", "Pure & Applied Sciences", value_type="str")
    reg.register_frame(sci_base)

    math_spec = FrameDefinition(
        frame_id="FRAME_SPEC_MATH_COMP",
        frame_type="programme_template",
        parent_ids=["FRAME_SCIENCES_BASE"],
    )
    math_spec.set_slot("discipline", "Mathematics & Computing", value_type="str")
    math_spec.set_slot(
        "skills_developed",
        ["Discrete Mathematics", "Combinatorics", "Cryptography", "Stochastic Calculus"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    math_spec.set_slot(
        "career_paths",
        ["Quantitative Researcher", "Cryptographer", "Algorithm Engineer"],
        value_type="list",
        merge_policy=MergePolicy.MERGE_UNIQUE,
    )
    reg.register_frame(math_spec)

    return reg


create_canonical_frame_registry = build_canonical_programme_hierarchy

