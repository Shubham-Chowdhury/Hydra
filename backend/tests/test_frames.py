"""Comprehensive unit tests for Hydra Generalised Frame System (Phase 2).

Verifies:
1. Explicit child override of an inherited default.
2. Inherited default distinction and provenance tracking.
3. Single-parent inheritance.
4. Multiple-parent identical values.
5. Multiple-parent conflicting values without child override (conflict detected).
6. Explicit child override resolving a multiple-parent conflict.
7. Collection merge under MERGE_UNIQUE (deterministic, sorted, deduplicated union).
8. Parent registration order independence.
9. Rejection of unknown parent frame with ValueError.
10. Rejection of cyclic inheritance with ValueError.
11. Provenance path correctness (child -> parent -> root).
12. Immutability check: parent frames are never mutated by child resolution.
13. Decision-relevant conflict propagation.
"""

import pytest

from app.domain.frame_system import (
    FrameDefinition,
    FrameRegistry,
    FrameSlot,
    MergePolicy,
    SlotResolution,
    SlotSourceType,
    create_canonical_frame_registry,
)


def test_1_explicit_child_override_of_inherited_default():
    """Child slot with OVERRIDE explicitly replaces parent default value."""
    registry = FrameRegistry()
    parent = FrameDefinition(
        frame_id="PARENT_ENG",
        slots={
            "duration_years": FrameSlot(name="duration_years", value=4, is_default=True),
            "discipline": FrameSlot(name="discipline", value="Engineering", is_default=False),
        },
    )
    registry.register(parent)

    child = FrameDefinition(
        frame_id="CHILD_FAST_TRACK",
        parent_frame_ids=["PARENT_ENG"],
        slots={
            "duration_years": FrameSlot(
                name="duration_years",
                value=3,
                is_default=False,
                override_policy=MergePolicy.OVERRIDE,
            )
        },
    )
    registry.register(child)

    resolved = registry.resolve_frame("CHILD_FAST_TRACK")
    duration_res = resolved["duration_years"]

    assert duration_res.effective_value == 3
    assert duration_res.source_type == SlotSourceType.EXPLICIT_CHILD
    assert duration_res.is_inherited is False
    assert duration_res.provenance_path == ["CHILD_FAST_TRACK"]


def test_2_inherited_default_distinction_and_provenance():
    """Child inherits parent default slot with proper inherited source type and provenance."""
    registry = FrameRegistry()
    parent = FrameDefinition(
        frame_id="PARENT_BASE",
        slots={
            "currency": FrameSlot(name="currency", value="INR", is_default=True),
            "cost_basis": FrameSlot(name="cost_basis", value="tuition_only_total", is_default=True),
        },
    )
    registry.register(parent)

    child = FrameDefinition(
        frame_id="CHILD_PROG",
        parent_frame_ids=["PARENT_BASE"],
        slots={},
    )
    registry.register(child)

    resolved = registry.resolve_frame("CHILD_PROG")
    curr_res = resolved["currency"]

    assert curr_res.effective_value == "INR"
    assert curr_res.source_type == SlotSourceType.INHERITED_DEFAULT
    assert curr_res.is_inherited is True
    assert curr_res.provenance_path == ["CHILD_PROG", "PARENT_BASE"]


def test_3_single_parent_inheritance():
    """Single-parent inheritance faithfully passes down multiple slots."""
    registry = FrameRegistry()
    parent = FrameDefinition(
        frame_id="PARENT_ROOT",
        slots={
            "campus_mode": FrameSlot(name="campus_mode", value="ON_CAMPUS", is_default=True),
            "grading_scale": FrameSlot(name="grading_scale", value="percentage", is_default=True),
        },
    )
    registry.register(parent)

    child = FrameDefinition(
        frame_id="CHILD_INTERMEDIATE",
        parent_frame_ids=["PARENT_ROOT"],
        slots={
            "specialization": FrameSlot(name="specialization", value="Software", is_default=False)
        },
    )
    registry.register(child)

    resolved = registry.resolve_frame("CHILD_INTERMEDIATE")
    assert resolved["campus_mode"].effective_value == "ON_CAMPUS"
    assert resolved["grading_scale"].effective_value == "percentage"
    assert resolved["specialization"].effective_value == "Software"


def test_4_multiple_parent_identical_values():
    """Multiple parents providing identical values merge cleanly without conflict."""
    registry = FrameRegistry()
    parent_a = FrameDefinition(
        frame_id="PARENT_A",
        slots={"language": FrameSlot(name="language", value="English", is_default=True)},
    )
    parent_b = FrameDefinition(
        frame_id="PARENT_B",
        slots={"language": FrameSlot(name="language", value="English", is_default=True)},
    )
    registry.register(parent_a)
    registry.register(parent_b)

    child = FrameDefinition(
        frame_id="CHILD_DUAL",
        parent_frame_ids=["PARENT_A", "PARENT_B"],
        slots={},
    )
    registry.register(child)

    resolved = registry.resolve_frame("CHILD_DUAL")
    lang_res = resolved["language"]

    assert lang_res.effective_value == "English"
    assert lang_res.is_conflicted is False
    assert len(lang_res.conflicts) == 0


def test_5_multiple_parent_conflicting_values_without_child_override():
    """Multiple parents providing different values without child override detects conflict."""
    registry = FrameRegistry()
    parent_a = FrameDefinition(
        frame_id="PARENT_ACADEMIC",
        slots={
            "duration_years": FrameSlot(
                name="duration_years",
                value=4,
                is_decision_relevant=True,
                override_policy=MergePolicy.REQUIRE_CONSISTENCY,
            )
        },
    )
    parent_b = FrameDefinition(
        frame_id="PARENT_POLYTECHNIC",
        slots={
            "duration_years": FrameSlot(
                name="duration_years",
                value=3,
                is_decision_relevant=True,
                override_policy=MergePolicy.REQUIRE_CONSISTENCY,
            )
        },
    )
    registry.register(parent_a)
    registry.register(parent_b)

    child = FrameDefinition(
        frame_id="CHILD_HYBRID",
        parent_frame_ids=["PARENT_ACADEMIC", "PARENT_POLYTECHNIC"],
        slots={},
    )
    registry.register(child)

    resolved = registry.resolve_frame("CHILD_HYBRID")
    duration_res = resolved["duration_years"]

    assert duration_res.is_conflicted is True
    assert len(duration_res.conflicts) == 1
    assert duration_res.conflicts[0].is_resolved is False
    assert duration_res.conflicts[0].is_decision_relevant is True


def test_6_explicit_child_override_resolving_parent_conflict():
    """Explicit child slot value cleanly resolves parent conflict with documented audit."""
    registry = FrameRegistry()
    parent_a = FrameDefinition(
        frame_id="PARENT_ONLINE",
        slots={"duration_years": FrameSlot(name="duration_years", value=2, is_decision_relevant=True)},
    )
    parent_b = FrameDefinition(
        frame_id="PARENT_OFFLINE",
        slots={"duration_years": FrameSlot(name="duration_years", value=4, is_decision_relevant=True)},
    )
    registry.register(parent_a)
    registry.register(parent_b)

    child = FrameDefinition(
        frame_id="CHILD_CUSTOM",
        parent_frame_ids=["PARENT_ONLINE", "PARENT_OFFLINE"],
        slots={
            "duration_years": FrameSlot(
                name="duration_years",
                value=3,
                override_policy=MergePolicy.OVERRIDE,
                is_decision_relevant=True,
            )
        },
    )
    registry.register(child)

    resolved = registry.resolve_frame("CHILD_CUSTOM")
    duration_res = resolved["duration_years"]

    assert duration_res.effective_value == 3
    assert duration_res.is_conflicted is False
    assert len(duration_res.conflicts) == 1
    assert duration_res.conflicts[0].is_resolved is True
    assert duration_res.conflicts[0].resolved_by == "CHILD_CUSTOM"


def test_7_collection_merge_under_merge_unique():
    """MERGE_UNIQUE creates a deterministic, sorted, deduplicated union of parent and child lists."""
    registry = FrameRegistry()
    parent_a = FrameDefinition(
        frame_id="PARENT_MATH",
        slots={
            "foundations": FrameSlot(
                name="foundations",
                value=["Algebra", "Calculus"],
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    parent_b = FrameDefinition(
        frame_id="PARENT_CS",
        slots={
            "foundations": FrameSlot(
                name="foundations",
                value=["Calculus", "Algorithms"],
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    registry.register(parent_a)
    registry.register(parent_b)

    child = FrameDefinition(
        frame_id="CHILD_DATA_AI",
        parent_frame_ids=["PARENT_MATH", "PARENT_CS"],
        slots={
            "foundations": FrameSlot(
                name="foundations",
                value=["Statistics", "Algorithms"],
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    registry.register(child)

    resolved = registry.resolve_frame("CHILD_DATA_AI")
    merged_foundations = resolved["foundations"].effective_value

    assert merged_foundations == ["Algebra", "Algorithms", "Calculus", "Statistics"]


def test_8_parent_registration_order_independence():
    """Parent registration order (A then B vs B then A) yields identical resolution."""
    # Order 1: Reg A, then B
    reg1 = FrameRegistry()
    reg1.register(FrameDefinition(frame_id="BASE_A", slots={"flag": FrameSlot(name="flag", value=10)}))
    reg1.register(FrameDefinition(frame_id="BASE_B", slots={"tag": FrameSlot(name="tag", value="beta")}))
    reg1.register(FrameDefinition(frame_id="CHILD", parent_frame_ids=["BASE_A", "BASE_B"], slots={}))

    # Order 2: Reg B, then A
    reg2 = FrameRegistry()
    reg2.register(FrameDefinition(frame_id="BASE_B", slots={"tag": FrameSlot(name="tag", value="beta")}))
    reg2.register(FrameDefinition(frame_id="BASE_A", slots={"flag": FrameSlot(name="flag", value=10)}))
    reg2.register(FrameDefinition(frame_id="CHILD", parent_frame_ids=["BASE_B", "BASE_A"], slots={}))

    res1 = reg1.resolve_frame("CHILD")
    res2 = reg2.resolve_frame("CHILD")

    assert res1["flag"].effective_value == res2["flag"].effective_value
    assert res1["tag"].effective_value == res2["tag"].effective_value


def test_9_rejection_of_unknown_parent_frame():
    """Registering a frame with a non-existent parent frame raises ValueError."""
    registry = FrameRegistry()
    child = FrameDefinition(
        frame_id="ORPHAN_CHILD",
        parent_frame_ids=["NON_EXISTENT_PARENT"],
        slots={},
    )
    with pytest.raises(ValueError, match="unknown parent frame 'NON_EXISTENT_PARENT'"):
        registry.register(child)


def test_10_rejection_of_cyclic_inheritance():
    """Attempting to introduce an inheritance cycle raises ValueError."""
    registry = FrameRegistry()
    registry.register(FrameDefinition(frame_id="FRAME_A", parent_frame_ids=[], slots={}))
    registry.register(FrameDefinition(frame_id="FRAME_B", parent_frame_ids=["FRAME_A"], slots={}))
    registry.register(FrameDefinition(frame_id="FRAME_C", parent_frame_ids=["FRAME_B"], slots={}))

    # Self cycle: first register base frame, then attempt to make it reference itself
    registry.register(FrameDefinition(frame_id="SELF_CYCLE", parent_frame_ids=[], slots={}))
    with pytest.raises(ValueError, match="Cyclic.*inheritance detected"):
        registry.register(FrameDefinition(frame_id="SELF_CYCLE", parent_frame_ids=["SELF_CYCLE"], slots={}))


def test_10b_rejection_of_indirect_cyclic_inheritance():
    """Attempting to register a frame that closes a multi-hop cycle raises ValueError."""
    registry = FrameRegistry()
    registry.register(FrameDefinition(frame_id="NODE_1", slots={}))
    registry.register(FrameDefinition(frame_id="NODE_2", parent_frame_ids=["NODE_1"], slots={}))
    registry.register(FrameDefinition(frame_id="NODE_3", parent_frame_ids=["NODE_2"], slots={}))

    # Attempt to add cyclic link: NODE_1 inherits from NODE_3
    with pytest.raises(ValueError, match="Cyclic.*inheritance detected"):
        registry.register(FrameDefinition(frame_id="NODE_1", parent_frame_ids=["NODE_3"], slots={}))



def test_11_provenance_path_correctness():
    """Multi-level inheritance tracks full ancestry chain in provenance path."""
    registry = FrameRegistry()
    registry.register(
        FrameDefinition(
            frame_id="ROOT",
            slots={"root_attr": FrameSlot(name="root_attr", value="from_root", is_default=True)},
        )
    )
    registry.register(
        FrameDefinition(
            frame_id="MID",
            parent_frame_ids=["ROOT"],
            slots={},
        )
    )
    registry.register(
        FrameDefinition(
            frame_id="LEAF",
            parent_frame_ids=["MID"],
            slots={},
        )
    )

    resolved = registry.resolve_frame("LEAF")
    slot_res = resolved["root_attr"]

    assert slot_res.effective_value == "from_root"
    assert slot_res.provenance_path == ["LEAF", "MID", "ROOT"]


def test_12_immutability_of_parent_frames():
    """Resolving a child frame does not mutate the parent frame definitions or slots."""
    registry = FrameRegistry()
    original_list = ["SkillA", "SkillB"]
    parent = FrameDefinition(
        frame_id="PARENT_SECURE",
        slots={
            "skills": FrameSlot(
                name="skills",
                value=list(original_list),
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    registry.register(parent)

    child = FrameDefinition(
        frame_id="CHILD_SECURE",
        parent_frame_ids=["PARENT_SECURE"],
        slots={
            "skills": FrameSlot(
                name="skills",
                value=["SkillC"],
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    registry.register(child)

    child_resolved = registry.resolve_frame("CHILD_SECURE")
    parent_resolved = registry.resolve_frame("PARENT_SECURE")

    # Parent resolved should retain original items only
    assert parent_resolved["skills"].effective_value == ["SkillA", "SkillB"]
    assert child_resolved["skills"].effective_value == ["SkillA", "SkillB", "SkillC"]
    # Parent definition slot untouched
    assert parent.slots["skills"].value == ["SkillA", "SkillB"]


def test_13_canonical_registry_and_decision_relevant_conflict():
    """The canonical demonstration hierarchy resolves properly and identifies synthetic frames."""
    canonical_reg = create_canonical_frame_registry()

    cs_resolved = canonical_reg.resolve_frame("FRAME_SPEC_CS")
    assert cs_resolved["duration_years"].effective_value == 4
    assert cs_resolved["currency"].effective_value == "INR"
    assert cs_resolved["cost_basis"].effective_value == "tuition_only_total"
    assert "Programming" in cs_resolved["skills_developed"].effective_value

    bio_resolved = canonical_reg.resolve_frame("FRAME_SPEC_BIO")
    assert bio_resolved["duration_years"].effective_value == 4
    assert "Molecular Biology" in bio_resolved["skills_developed"].effective_value


def test_14_robotics_frame_specialisation():
    """FRAME_SPEC_ROB specialises FRAME_ENGINEERING_BASE and maps to SYNTH_IN_ROB_04."""
    from app.domain.catalogue import get_synthetic_programmes

    canonical_reg = create_canonical_frame_registry()
    rob_resolved = canonical_reg.resolve_frame("FRAME_SPEC_ROB")

    # Verify duration, currency, cost_basis inherited from FRAME_PROGRAMME_BASE
    assert rob_resolved["duration_years"].effective_value == 4
    assert rob_resolved["currency"].effective_value == "INR"
    assert rob_resolved["cost_basis"].effective_value == "tuition_only_total"

    # Verify discipline specialized and broad_discipline inherited from FRAME_ENGINEERING_BASE
    assert rob_resolved["discipline"].effective_value == "Robotics"
    assert rob_resolved["broad_discipline"].effective_value == "Engineering"
    assert rob_resolved["accreditation_body"].effective_value == "DEMO_ACCREDITATION_BOARD"

    # Verify skills developed contains robotics specific skills
    skills = rob_resolved["skills_developed"].effective_value
    assert "Robotic Control Systems" in skills
    assert "Embedded AI" in skills
    assert "Computer Vision" in skills

    # Verify career paths contain robotics careers
    careers = rob_resolved["career_paths"].effective_value
    assert "Robotics Engineer" in careers
    assert "Autonomous Systems Specialist" in careers

    # Verify SYNTH_IN_ROB_04 programme maps to FRAME_SPEC_ROB
    programmes = {p.programme_id: p for p in get_synthetic_programmes()}
    assert programmes["SYNTH_IN_ROB_04"].parent_frame_id == "FRAME_SPEC_ROB"


def test_15_collection_removal_and_provenance_audit():
    """Explicit removal of inherited collection items using removed_items preserves parent immutability and tracks provenance."""
    registry = FrameRegistry()
    parent = FrameDefinition(
        frame_id="PARENT_ENGINEERING",
        slots={
            "skills": FrameSlot(
                name="skills",
                value=["Math", "Physics", "Drafting"],
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    registry.register(parent)

    child = FrameDefinition(
        frame_id="CHILD_SOFTWARE",
        parent_frame_ids=["PARENT_ENGINEERING"],
        slots={
            "skills": FrameSlot(
                name="skills",
                value=["Coding", "Algorithms"],
                removed_items=["Drafting"],
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    registry.register(child)

    child_resolved = registry.resolve_frame("CHILD_SOFTWARE")
    parent_resolved = registry.resolve_frame("PARENT_ENGINEERING")

    # Parent remains completely immutable
    assert parent.slots["skills"].value == ["Math", "Physics", "Drafting"]
    assert parent_resolved["skills"].effective_value == ["Drafting", "Math", "Physics"]

    # Child has Drafting removed and Coding, Algorithms added
    assert "Drafting" not in child_resolved["skills"].effective_value
    assert "Math" in child_resolved["skills"].effective_value
    assert "Physics" in child_resolved["skills"].effective_value
    assert "Coding" in child_resolved["skills"].effective_value
    assert "Algorithms" in child_resolved["skills"].effective_value

    # Provenance audit modification record exists
    skills_res = child_resolved["skills"]
    assert len(skills_res.modifications) == 1
    mod = skills_res.modifications[0]
    assert mod.operation == "REMOVE"
    assert mod.slot_name == "skills"
    assert mod.modified_by_frame_id == "CHILD_SOFTWARE"
    assert "Drafting" in mod.affected_items


def test_16_collection_replacement_under_override():
    """Collection replacement under OVERRIDE replaces inherited collection and audits replaced items."""
    registry = FrameRegistry()
    parent = FrameDefinition(
        frame_id="PARENT_GENERIC",
        slots={
            "badges": FrameSlot(
                name="badges",
                value=["Standard", "General"],
                override_policy=MergePolicy.OVERRIDE,
            )
        },
    )
    registry.register(parent)

    child = FrameDefinition(
        frame_id="CHILD_PREMIUM",
        parent_frame_ids=["PARENT_GENERIC"],
        slots={
            "badges": FrameSlot(
                name="badges",
                value=["Honors", "Research-Track"],
                override_policy=MergePolicy.OVERRIDE,
            )
        },
    )
    registry.register(child)

    child_resolved = registry.resolve_frame("CHILD_PREMIUM")
    parent_resolved = registry.resolve_frame("PARENT_GENERIC")

    # Parent immutable
    assert parent_resolved["badges"].effective_value == ["Standard", "General"]

    # Child replaced
    assert child_resolved["badges"].effective_value == ["Honors", "Research-Track"]
    assert len(child_resolved["badges"].modifications) == 1
    mod = child_resolved["badges"].modifications[0]
    assert mod.operation == "REPLACE"
    assert "Standard" in mod.affected_items
    assert "General" in mod.affected_items


def test_17_rejection_of_collection_removal_on_mandatory_admission_prerequisites():
    """Attempting to remove items from decision-relevant or mandatory admission prerequisite slots raises ValueError."""
    registry = FrameRegistry()
    parent = FrameDefinition(
        frame_id="PARENT_ADMISSIONS",
        slots={
            "academic_prerequisites": FrameSlot(
                name="academic_prerequisites",
                value=["MATH_80", "PHYS_75"],
                is_decision_relevant=True,
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    registry.register(parent)

    # Child attempts to remove MATH_80 prerequisite
    child = FrameDefinition(
        frame_id="CHILD_BYPASS",
        parent_frame_ids=["PARENT_ADMISSIONS"],
        slots={
            "academic_prerequisites": FrameSlot(
                name="academic_prerequisites",
                value=[],
                removed_items=["MATH_80"],
                is_decision_relevant=True,
                override_policy=MergePolicy.MERGE_UNIQUE,
            )
        },
    )
    registry.register(child)

    with pytest.raises(
        ValueError,
        match="Mandatory admission requirements cannot be removed",
    ):
        registry.resolve_frame("CHILD_BYPASS")


def test_18_collection_removal_parent_order_independence():
    """Collection removal produces identical deterministic results regardless of parent registration order."""
    def build_registry(parent_order: list[str]) -> FrameRegistry:
        reg = FrameRegistry()
        p1 = FrameDefinition(
            frame_id="PARENT_ALPHA",
            slots={
                "tags": FrameSlot(
                    name="tags",
                    value=["TagA", "Shared"],
                    override_policy=MergePolicy.MERGE_UNIQUE,
                )
            },
        )
        p2 = FrameDefinition(
            frame_id="PARENT_BETA",
            slots={
                "tags": FrameSlot(
                    name="tags",
                    value=["TagB", "Shared"],
                    override_policy=MergePolicy.MERGE_UNIQUE,
                )
            },
        )
        for p in parent_order:
            reg.register(p1 if p == "PARENT_ALPHA" else p2)

        child = FrameDefinition(
            frame_id="CHILD_MERGED",
            parent_frame_ids=parent_order,
            slots={
                "tags": FrameSlot(
                    name="tags",
                    value=["TagChild"],
                    removed_items=["Shared"],
                    override_policy=MergePolicy.MERGE_UNIQUE,
                )
            },
        )
        reg.register(child)
        return reg

    reg_ab = build_registry(["PARENT_ALPHA", "PARENT_BETA"])
    reg_ba = build_registry(["PARENT_BETA", "PARENT_ALPHA"])

    res_ab = reg_ab.resolve_frame("CHILD_MERGED")["tags"]
    res_ba = reg_ba.resolve_frame("CHILD_MERGED")["tags"]

    assert res_ab.effective_value == res_ba.effective_value == ["TagA", "TagB", "TagChild"]


def test_19_descriptive_vs_decision_relevant_conflict_flagging():
    """Conflicting parent values flag conflict only if decision-relevant; descriptive conflicts are not flagged as conflicted."""
    registry = FrameRegistry()
    p1 = FrameDefinition(
        frame_id="PARENT_NORTH",
        slots={
            "campus_description": FrameSlot(
                name="campus_description",
                value="Northern Campus",
                is_decision_relevant=False,
            ),
            "min_math_score": FrameSlot(
                name="min_math_score",
                value=80,
                is_decision_relevant=True,
            ),
        },
    )
    p2 = FrameDefinition(
        frame_id="PARENT_SOUTH",
        slots={
            "campus_description": FrameSlot(
                name="campus_description",
                value="Southern Campus",
                is_decision_relevant=False,
            ),
            "min_math_score": FrameSlot(
                name="min_math_score",
                value=75,
                is_decision_relevant=True,
            ),
        },
    )
    registry.register(p1)
    registry.register(p2)

    child = FrameDefinition(
        frame_id="CHILD_UNSPECIFIED",
        parent_frame_ids=["PARENT_NORTH", "PARENT_SOUTH"],
    )
    registry.register(child)

    resolved = registry.resolve_frame("CHILD_UNSPECIFIED")

    # Descriptive slot conflict: is_conflicted=False, has_decision_relevant_conflict=False
    campus_res = resolved["campus_description"]
    assert campus_res.is_conflicted is False
    assert campus_res.has_decision_relevant_conflict is False
    assert len(campus_res.conflicts) == 1
    assert campus_res.conflicts[0].is_decision_relevant is False

    # Decision-relevant slot conflict: is_conflicted=True, has_decision_relevant_conflict=True
    math_res = resolved["min_math_score"]
    assert math_res.is_conflicted is True
    assert math_res.has_decision_relevant_conflict is True
    assert len(math_res.conflicts) == 1
    assert math_res.conflicts[0].is_decision_relevant is True

