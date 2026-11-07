"""Twin Agent: Student Digital Twin Construction Engine for Hydra (Phase 4).

Constructs an explainable, structured, versioned representation of a student profile
using symbolic knowledge representation, typed fact provenance, conservative grading scale
normalizations, and multidimensional completeness auditing.
"""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from app.domain.catalogue import get_synthetic_programmes
from app.domain.frames import ProgrammeFrame, StudentFrame, SubjectScore
from app.domain.frame_system import (
    FrameDefinition,
    FrameRegistry,
    FrameSlot,
    MergePolicy,
    build_canonical_programme_hierarchy,
)
from app.domain.twin import (
    CBSE_POLICY_CCE_9_5_INDICATIVE,
    CBSE_POLICY_HISTORICAL_CCE,
    AcademicIdentity,
    CBSEConversionPolicy,
    CompletenessState,
    DimensionCompleteness,
    EntranceExamProfile,
    FactOriginCategory,
    FactRecord,
    FactValidationStatus,
    FinancialConstraints,
    GeographicPreferenceType,
    GeographicPreferences,
    InterestsAndGoals,
    NormalizedSubjectScore,
    TwinSnapshot,
    compute_canonical_profile_fingerprint,
    freeze_value,
    resolve_authorized_conversion_policy,
    unfreeze_value,
)
from app.knowledge.graph import HydraKnowledgeGraph, RelationshipType

# Versioned heuristics for academic evaluation
SCORE_HIGHLIGHT_THRESHOLD = 75.0
HIGHLIGHT_HEURISTIC_VERSION = "1.0"


class TwinAgent:
    """Intelligent agent constructing auditable Student Digital Twin snapshots."""

    def __init__(
        self,
        knowledge_graph: Optional[HydraKnowledgeGraph] = None,
        frame_registry: Optional[FrameRegistry] = None,
        programmes: Optional[List[ProgrammeFrame]] = None,
        max_retained_student_frames: int = 1000,
    ) -> None:
        self._programmes: List[ProgrammeFrame] = (
            list(programmes) if programmes is not None else get_synthetic_programmes()
        )
        self._frame_registry: FrameRegistry = (
            frame_registry if frame_registry is not None else build_canonical_programme_hierarchy()
        )
        self._max_retained_student_frames: int = max_retained_student_frames
        self._dynamic_student_frame_ids: List[str] = []
        if knowledge_graph is not None:
            self._graph = knowledge_graph
        else:
            self._graph = HydraKnowledgeGraph()
            self._graph.populate_from_programmes(self._programmes, registry=self._frame_registry)

    @property
    def frame_registry(self) -> FrameRegistry:
        """Authoritative FrameRegistry instance."""
        return self._frame_registry

    @property
    def graph(self) -> HydraKnowledgeGraph:
        """Underlying semantic knowledge graph."""
        return self._graph

    def construct_twin(self, profile: Any) -> TwinSnapshot:
        """Executes the deterministic 11-step Student Digital Twin construction pipeline."""
        # 1. Normalize and unpack payload
        raw_data = self._unpack_profile(profile)

        # 2. Canonical fingerprinting and immutable identity
        fingerprint = self._compute_profile_fingerprint(raw_data)
        twin_id = f"TWIN_{fingerprint[:12]}"
        now = datetime.now(timezone.utc)
        snapshot_id = f"SNAP_{fingerprint[:8]}_{uuid.uuid4().hex}"
        created_at = now.isoformat()

        facts: Dict[str, FactRecord] = {}
        validation_findings: List[str] = []
        missing_information: List[str] = []

        # 3. Fact extraction and grading scale normalization
        academic_identity, acad_facts, acad_findings = self._process_academic_transcript(
            raw_data.get("subject_scores", []), twin_id
        )
        facts.update(acad_facts)
        validation_findings.extend(acad_findings)

        # 4. Process entrance examination profile
        entrance_profile, entrance_facts, entrance_findings, entrance_missing = (
            self._process_entrance_exam(
                raw_data.get("entrance_exam_name"), raw_data.get("entrance_rank"), twin_id
            )
        )
        facts.update(entrance_facts)
        validation_findings.extend(entrance_findings)
        missing_information.extend(entrance_missing)

        # 5. Process financial constraints
        fin_constraints, fin_facts, fin_missing = self._process_finances(
            raw_data.get("total_budget_inr", 0.0), twin_id
        )
        facts.update(fin_facts)
        missing_information.extend(fin_missing)

        # 6. Process geographic preferences
        geo_prefs, geo_facts = self._process_geography(
            raw_data.get("preferred_locations", []), twin_id
        )
        facts.update(geo_facts)

        # 7. Process interests, goals, and semantic network traversal
        interests_goals, interest_facts, semantic_pathways = self._process_interests_and_pathways(
            raw_data.get("preferred_disciplines", []),
            raw_data.get("career_goals", []),
            raw_data.get("certifications", []),
            twin_id,
        )
        facts.update(interest_facts)

        # 8. Frame system registration and slot resolution
        frame_rep = self._resolve_student_frame(twin_id, snapshot_id, raw_data)

        # 9. Multidimensional completeness calculation
        completeness_dims, overall_completeness = self._evaluate_multidimensional_completeness(
            academic_identity=academic_identity,
            entrance_profile=entrance_profile,
            fin_constraints=fin_constraints,
            geo_prefs=geo_prefs,
            interests_goals=interests_goals,
        )

        # Record high-level missing information summaries
        if not academic_identity.subject_scores:
            missing_information.append("Academic transcript has no subject scores recorded.")
        if academic_identity.unsupported_grading_scales:
            missing_information.append(
                f"Unsupported grading scales require manual transcript audit: {', '.join(academic_identity.unsupported_grading_scales)}"
            )

        # 10. Construct immutable snapshot
        return TwinSnapshot(
            twin_id=twin_id,
            snapshot_id=snapshot_id,
            student_id=raw_data.get("student_id"),
            student_profile_version="1.0.0",
            schema_version="1.0.0",
            policy_version="1.0.0",
            created_at=created_at,
            profile_fingerprint=fingerprint,
            overall_completeness=overall_completeness,
            completeness_dimensions=completeness_dims,
            academic_identity=academic_identity,
            entrance_exam_profile=entrance_profile,
            financial_constraints=fin_constraints,
            geographic_preferences=geo_prefs,
            interests_and_goals=interests_goals,
            facts=facts,
            semantic_network_pathways=semantic_pathways,
            frame_representation=frame_rep,
            missing_information=sorted(list(set(missing_information))),
            validation_findings=sorted(list(set(validation_findings))),
        )

    # -------------------------------------------------------------------------
    # Internal Helpers: Pipeline Steps
    # -------------------------------------------------------------------------

    def _unpack_profile(self, profile: Any) -> Dict[str, Any]:
        """Converts diverse student profile input types into a standardized dictionary."""
        if hasattr(profile, "model_dump"):
            return profile.model_dump()
        if hasattr(profile, "__dict__"):
            data: Dict[str, Any] = {}
            for k, v in profile.__dict__.items():
                if k.startswith("_"):
                    continue
                if isinstance(v, list) and v and hasattr(v[0], "__dict__"):
                    data[k] = [item.__dict__ for item in v]
                else:
                    data[k] = v
            return data
        if isinstance(profile, dict):
            return deepcopy(profile)
        raise TypeError(f"Unsupported profile payload type: {type(profile).__name__}")

    def compute_fingerprint(self, profile: Any) -> str:
        """Pure helper to compute the deterministic profile fingerprint without side-effects."""
        raw_data = self._unpack_profile(profile)
        return compute_canonical_profile_fingerprint(raw_data)

    def _compute_profile_fingerprint(self, raw: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash of canonicalized profile representation."""
        return compute_canonical_profile_fingerprint(raw)

    def _process_academic_transcript(
        self, raw_scores: List[Any], twin_id: str
    ) -> Tuple[AcademicIdentity, Dict[str, FactRecord], List[str]]:
        """Validates, normalizes, and audits academic subject scores."""
        normalized_scores: List[NormalizedSubjectScore] = []
        facts: Dict[str, FactRecord] = {}
        findings: List[str] = []
        strengths: List[str] = []
        unsupported_scales: List[str] = []

        for item in raw_scores:
            if isinstance(item, dict):
                code = str(item.get("subject_code", "")).strip().upper()
                name = str(item.get("subject_name", code)).strip()
                score = float(item.get("score", 0.0))
                max_score = float(item.get("max_score", 100.0))
                scale = str(item.get("grading_scale", "percentage")).strip().lower()
                board = str(item.get("board", "")).strip() if item.get("board") else None
                policy = str(item.get("conversion_policy_id", "")).strip() if item.get("conversion_policy_id") else None
                exam_year = int(item.get("examination_year")) if item.get("examination_year") else None
            else:
                code = str(getattr(item, "subject_code", "")).strip().upper()
                name = str(getattr(item, "subject_name", code)).strip()
                score = float(getattr(item, "score", 0.0))
                max_score = float(getattr(item, "max_score", 100.0))
                scale = str(getattr(item, "grading_scale", "percentage")).strip().lower()
                board = str(getattr(item, "board", "")).strip() if getattr(item, "board", None) else None
                policy = str(getattr(item, "conversion_policy_id", "")).strip() if getattr(item, "conversion_policy_id", None) else None
                exam_year = int(getattr(item, "examination_year")) if getattr(item, "examination_year", None) else None

            raw_fact_id = f"FACT_ACAD_SUBJ_{code}"
            norm_fact_id = f"FACT_NORM_SUBJ_{code}"

            raw_fact_val = {
                "score": score,
                "max_score": max_score,
                "grading_scale": scale,
            }
            if board:
                raw_fact_val["board"] = board
            if policy:
                raw_fact_val["conversion_policy_id"] = policy
            if exam_year:
                raw_fact_val["examination_year"] = exam_year

            # User provided fact
            facts[raw_fact_id] = FactRecord(
                fact_id=raw_fact_id,
                field_name=f"subject_score.{code}",
                actual_value=raw_fact_val,
                original_value=raw_fact_val,
                unit_or_scale=scale,
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=f"Reported score of {score}/{max_score} in {name} ({code}) with scale '{scale}'.",
            )

            # Deterministic normalization policy
            norm_pct: Optional[float] = None
            val_status = FactValidationStatus.VALID
            derivation_rule: Optional[str] = None
            explanation = ""
            is_indicative = False
            is_institution_authorized = False

            if scale in ("percentage", "%"):
                if score < 0.0 or score > max_score or max_score <= 0.0:
                    val_status = FactValidationStatus.INVALID
                    explanation = f"Score {score} is invalid for bounds [0.0, {max_score}]."
                    findings.append(f"Invalid score in {code}: {score}/{max_score}.")
                else:
                    norm_pct = round((score / max_score) * 100.0, 2)
                    derivation_rule = "PERCENTAGE_RATIO"
                    explanation = f"Standard percentage ratio: ({score} / {max_score}) * 100 = {norm_pct:.2f}%"

            elif scale in ("marks_obtained_out_of_total", "marks", "ratio"):
                if score < 0.0 or score > max_score or max_score <= 0.0:
                    val_status = FactValidationStatus.INVALID
                    explanation = f"Marks {score}/{max_score} invalid."
                    findings.append(f"Invalid marks ratio for {code}: {score}/{max_score}.")
                else:
                    norm_pct = round((score / max_score) * 100.0, 2)
                    derivation_rule = "MARKS_RATIO_NORMALIZATION"
                    explanation = f"Marks ratio normalization: ({score} / {max_score}) * 100 = {norm_pct:.2f}%"

            elif scale in ("cbse_10_point", "cbse_cgpa", "10_point_cgpa"):
                if score < 0.0 or score > 10.0:
                    val_status = FactValidationStatus.INVALID
                    explanation = f"CBSE CGPA {score} is outside valid 10-point scale [0.0, 10.0]."
                    findings.append(f"Invalid CBSE CGPA in {code}: {score}.")
                else:
                    auth_policy, policy_explanation = resolve_authorized_conversion_policy(
                        board=board,
                        grading_scale=scale,
                        examination_year=exam_year,
                        requested_policy_id=policy,
                    )
                    if auth_policy is not None:
                        norm_pct = round(score * auth_policy.multiplier, 2)
                        derivation_rule = f"{auth_policy.policy_id}_9_5"
                        explanation = policy_explanation
                        is_indicative = auth_policy.is_indicative
                        is_institution_authorized = auth_policy.is_institution_authorized
                    else:
                        norm_pct = None
                        val_status = FactValidationStatus.NEEDS_REVIEW
                        derivation_rule = None
                        explanation = policy_explanation
                        is_indicative = False
                        is_institution_authorized = False
                        findings.append(
                            f"Subject {code} (10-point scale): {policy_explanation}"
                        )

            else:
                # Unsupported grading scale (e.g., US 4-point GPA, letter grades)
                norm_pct = None
                val_status = FactValidationStatus.NEEDS_REVIEW
                explanation = (
                    f"Grading scale '{scale}' is unsupported for automatic conversion. "
                    "Requires manual transcript review to verify equivalence."
                )
                unsupported_scales.append(f"{code}:{scale}")
                findings.append(
                    f"Subject {code} uses unsupported grading scale '{scale}'. Manual transcript verification required."
                )

            # Record normalized fact
            facts[norm_fact_id] = FactRecord(
                fact_id=norm_fact_id,
                field_name=f"normalized_percentage.{code}",
                actual_value=norm_pct,
                original_value=score,
                unit_or_scale="percentage" if norm_pct is not None else scale,
                origin_category=FactOriginCategory.DETERMINISTICALLY_DERIVED,
                validation_status=val_status,
                explanation=explanation,
                input_fact_ids=[raw_fact_id],
                derivation_rule=derivation_rule,
            )

            normalized_scores.append(
                NormalizedSubjectScore(
                    subject_code=code,
                    subject_name=name,
                    original_score=score,
                    max_score=max_score,
                    grading_scale=scale,
                    normalized_percentage=norm_pct,
                    conversion_status=val_status,
                    conversion_explanation=explanation,
                    board=board,
                    conversion_policy_id=policy,
                    examination_year=exam_year,
                    is_indicative=is_indicative,
                    is_institution_authorized=is_institution_authorized,
                )
            )

            if norm_pct is not None and norm_pct >= SCORE_HIGHLIGHT_THRESHOLD:
                strengths.append(f"{code} ({norm_pct:.1f}%)")

        return (
            AcademicIdentity(
                subject_scores=normalized_scores,
                score_based_academic_highlights=sorted(strengths),
                highlight_threshold=SCORE_HIGHLIGHT_THRESHOLD,
                highlight_heuristic_version=HIGHLIGHT_HEURISTIC_VERSION,
                missing_subjects=[],
                unsupported_grading_scales=sorted(list(set(unsupported_scales))),
            ),
            facts,
            findings,
        )

    def _process_entrance_exam(
        self, exam_name: Optional[str], rank: Optional[int], twin_id: str
    ) -> Tuple[EntranceExamProfile, Dict[str, FactRecord], List[str], List[str]]:
        """Processes entrance exam facts strictly without predictive rank speculation."""
        facts: Dict[str, FactRecord] = {}
        findings: List[str] = []
        missing_details: List[str] = []

        cleaned_name = exam_name.strip() if exam_name else None
        valid_rank = int(rank) if (rank is not None and rank > 0) else None

        if cleaned_name and valid_rank:
            facts["FACT_ENTRANCE_EXAM"] = FactRecord(
                fact_id="FACT_ENTRANCE_EXAM",
                field_name="entrance_exam_name",
                actual_value=cleaned_name,
                original_value=exam_name,
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=f"Reported entrance examination: {cleaned_name}",
            )
            facts["FACT_ENTRANCE_RANK"] = FactRecord(
                fact_id="FACT_ENTRANCE_RANK",
                field_name="entrance_rank",
                actual_value=valid_rank,
                original_value=rank,
                unit_or_scale="rank_integer",
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=f"Reported rank {valid_rank} in {cleaned_name}.",
            )
            profile = EntranceExamProfile(
                exam_name=cleaned_name,
                rank=valid_rank,
                rank_basis="ALL_INDIA_RANK",
                academic_year=2026,
                missing_details=[],
                interpretation_notes=f"Student-reported entrance examination: {cleaned_name} with rank {valid_rank} (self-reported; external official verification not performed).",
            )

        elif cleaned_name and not valid_rank:
            missing_details.append("entrance_rank")
            facts["FACT_ENTRANCE_EXAM"] = FactRecord(
                fact_id="FACT_ENTRANCE_EXAM",
                field_name="entrance_exam_name",
                actual_value=cleaned_name,
                original_value=exam_name,
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=f"Reported entrance examination: {cleaned_name} without rank.",
            )
            facts["FACT_ENTRANCE_RANK"] = FactRecord(
                fact_id="FACT_ENTRANCE_RANK",
                field_name="entrance_rank",
                actual_value=None,
                original_value=rank,
                origin_category=FactOriginCategory.UNKNOWN,
                validation_status=FactValidationStatus.MISSING,
                explanation="Entrance rank not provided for reported examination.",
            )
            findings.append(f"Entrance examination '{cleaned_name}' reported without rank.")
            profile = EntranceExamProfile(
                exam_name=cleaned_name,
                rank=None,
                rank_basis=None,
                academic_year=2026,
                missing_details=["entrance_rank"],
                interpretation_notes=f"Exam '{cleaned_name}' specified without rank. Mandatory rank prerequisites cannot be verified.",
            )

        elif not cleaned_name and valid_rank:
            missing_details.append("entrance_exam_name")
            facts["FACT_ENTRANCE_EXAM"] = FactRecord(
                fact_id="FACT_ENTRANCE_EXAM",
                field_name="entrance_exam_name",
                actual_value=None,
                original_value=exam_name,
                origin_category=FactOriginCategory.UNKNOWN,
                validation_status=FactValidationStatus.MISSING,
                explanation="Entrance examination name missing despite reported rank.",
            )
            facts["FACT_ENTRANCE_RANK"] = FactRecord(
                fact_id="FACT_ENTRANCE_RANK",
                field_name="entrance_rank",
                actual_value=valid_rank,
                original_value=rank,
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=f"Rank {valid_rank} reported without associated examination name.",
            )
            findings.append(f"Entrance rank {valid_rank} reported without examination name.")
            profile = EntranceExamProfile(
                exam_name=None,
                rank=valid_rank,
                rank_basis=None,
                academic_year=2026,
                missing_details=["entrance_exam_name"],
                interpretation_notes="Rank provided without entrance examination name.",
            )

        else:
            missing_details.extend(["entrance_exam_name", "entrance_rank"])
            facts["FACT_ENTRANCE_EXAM"] = FactRecord(
                fact_id="FACT_ENTRANCE_EXAM",
                field_name="entrance_exam_name",
                actual_value=None,
                original_value=None,
                origin_category=FactOriginCategory.UNKNOWN,
                validation_status=FactValidationStatus.MISSING,
                explanation="No entrance examination reported.",
            )
            facts["FACT_ENTRANCE_RANK"] = FactRecord(
                fact_id="FACT_ENTRANCE_RANK",
                field_name="entrance_rank",
                actual_value=None,
                original_value=None,
                origin_category=FactOriginCategory.UNKNOWN,
                validation_status=FactValidationStatus.MISSING,
                explanation="No entrance rank reported.",
            )
            profile = EntranceExamProfile(
                exam_name=None,
                rank=None,
                rank_basis=None,
                academic_year=2026,
                missing_details=["entrance_exam_name", "entrance_rank"],
                interpretation_notes="No entrance exam recorded. Applicant can be evaluated on programmes that do not mandate entrance cutoffs.",
            )

        return profile, facts, findings, missing_details

    def _process_finances(
        self, budget: float, twin_id: str
    ) -> Tuple[FinancialConstraints, Dict[str, FactRecord], List[str]]:
        """Validates and structures education financial constraints in INR."""
        facts: Dict[str, FactRecord] = {}
        missing: List[str] = []

        is_provided = budget > 0.0
        if is_provided:
            notes = f"Total tuition budget of INR {budget:,.2f} specified for full programme duration."
            status = FactValidationStatus.VALID
            origin = FactOriginCategory.USER_PROVIDED
        else:
            notes = "No education budget specified (INR 0.00). Affordability checks will default to unbudgeted."
            status = FactValidationStatus.MISSING
            origin = FactOriginCategory.UNKNOWN
            missing.append("total_budget_inr")

        facts["FACT_BUDGET"] = FactRecord(
            fact_id="FACT_BUDGET",
            field_name="total_budget_inr",
            actual_value=budget,
            original_value=budget,
            unit_or_scale="INR",
            origin_category=origin,
            validation_status=status,
            explanation=notes,
        )

        constraints = FinancialConstraints(
            total_budget_inr=budget,
            currency="INR",
            cost_basis="tuition_only_total",
            is_budget_provided=is_provided,
            affordability_readiness=is_provided,
            notes=notes,
        )
        return constraints, facts, missing

    def _process_geography(
        self, locations: List[str], twin_id: str
    ) -> Tuple[GeographicPreferences, Dict[str, FactRecord]]:
        """Processes geographic preferences with explicit tri-state semantics."""
        raw_locs = [str(loc).strip() for loc in locations if str(loc).strip()]

        is_explicit_all_india = any(
            loc.lower() in ("anywhere", "all india", "all_india", "pan_india", "pan india", "anywhere in india")
            for loc in raw_locs
        )

        if is_explicit_all_india:
            pref_type = GeographicPreferenceType.ANYWHERE_IN_INDIA
            cleaned_locs: List[str] = []
            is_unconstrained = True
            notes = "Explicitly unconstrained: applicant confirmed open to academic locations anywhere in India."
        elif raw_locs:
            pref_type = GeographicPreferenceType.PREFERRED_LOCATIONS
            cleaned_locs = sorted(list(set(raw_locs)))
            is_unconstrained = False
            notes = f"Constrained to {len(cleaned_locs)} preferred location(s): {', '.join(cleaned_locs)}."
        else:
            pref_type = GeographicPreferenceType.NOT_PROVIDED
            cleaned_locs = []
            is_unconstrained = True
            notes = "Geographic preference not provided (neutral). Programmes across all locations will be presented without geographic filtering."

        facts = {
            "FACT_GEO_PREFS": FactRecord(
                fact_id="FACT_GEO_PREFS",
                field_name="preferred_locations",
                actual_value=cleaned_locs,
                original_value=locations,
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=notes,
            )
        }

        prefs = GeographicPreferences(
            preferred_locations=cleaned_locs,
            preference_type=pref_type,
            is_unconstrained=is_unconstrained,
            notes=notes,
        )
        return prefs, facts

    def _process_interests_and_pathways(
        self,
        disciplines: List[str],
        career_goals: List[str],
        certifications: List[str],
        twin_id: str,
    ) -> Tuple[InterestsAndGoals, Dict[str, FactRecord], List[Dict[str, Any]]]:
        """Audits preferences and discovers verified pathways across the semantic knowledge graph."""
        cleaned_disc = sorted(list(set([str(d).strip() for d in disciplines if str(d).strip()])))
        cleaned_goals = sorted(list(set([str(g).strip() for g in career_goals if str(g).strip()])))
        cleaned_certs = sorted(list(set([str(c).strip() for c in certifications if str(c).strip()])))

        facts = {
            "FACT_DISCIPLINES": FactRecord(
                fact_id="FACT_DISCIPLINES",
                field_name="preferred_disciplines",
                actual_value=cleaned_disc,
                original_value=disciplines,
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=f"Reported {len(cleaned_disc)} preferred discipline(s).",
            ),
            "FACT_CAREER_GOALS": FactRecord(
                fact_id="FACT_CAREER_GOALS",
                field_name="career_goals",
                actual_value=cleaned_goals,
                original_value=career_goals,
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=f"Reported {len(cleaned_goals)} career goal(s).",
            ),
            "FACT_CERTIFICATIONS": FactRecord(
                fact_id="FACT_CERTIFICATIONS",
                field_name="certifications",
                actual_value=cleaned_certs,
                original_value=certifications,
                origin_category=FactOriginCategory.USER_PROVIDED,
                validation_status=FactValidationStatus.VALID,
                explanation=f"Reported {len(cleaned_certs)} certification(s).",
            ),
        }

        # Semantic graph traversal for career goals and disciplines
        unmapped: List[str] = []
        pathways: List[Dict[str, Any]] = []

        graph_nodes = self._graph.graph.nodes

        # Match career goals in graph
        for goal in cleaned_goals:
            goal_id = f"CAREER_{goal.upper().replace(' ', '_')}"
            if self._graph.graph.has_node(goal_id):
                # Traverse incoming edges to find programmes or skills leading to this career
                for u, _, key, data in self._graph.graph.in_edges(goal_id, data=True, keys=True):
                    u_name = graph_nodes[u].get("name", u)
                    rel = data.get("relation_type", key)
                    u_type = graph_nodes[u].get("entity_type", "unknown")
                    pathways.append(
                        {
                            "source": u_name,
                            "relationship": rel,
                            "target": goal,
                            "target_type": "career",
                            "source_type": u_type,
                            "provenance_path": [u, goal_id],
                        }
                    )
            else:
                unmapped.append(f"career:{goal}")

        # Match disciplines in graph
        for disc in cleaned_disc:
            disc_id = f"DISC_{disc.upper().replace(' ', '_')}"
            if self._graph.graph.has_node(disc_id):
                for u, _, key, data in self._graph.graph.in_edges(disc_id, data=True, keys=True):
                    u_name = graph_nodes[u].get("name", u)
                    rel = data.get("relation_type", key)
                    u_type = graph_nodes[u].get("entity_type", "unknown")
                    pathways.append(
                        {
                            "source": u_name,
                            "relationship": rel,
                            "target": disc,
                            "target_type": "discipline",
                            "source_type": u_type,
                            "provenance_path": [u, disc_id],
                        }
                    )
            else:
                unmapped.append(f"discipline:{disc}")

        # Deterministic sorting of discovered pathways
        pathways.sort(key=lambda x: (x["source"], x["relationship"], x["target"]))

        interests = InterestsAndGoals(
            preferred_disciplines=cleaned_disc,
            career_goals=cleaned_goals,
            certifications=cleaned_certs,
            unmapped_interests=sorted(unmapped),
        )
        return interests, facts, pathways

    def _resolve_student_frame(
        self, twin_id: str, snapshot_id: str, raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates and registers a student frame child of FRAME_STUDENT_BASE, resolving all slots."""
        frame_id = f"FRAME_STUDENT_{snapshot_id}"
        student_frame = FrameDefinition(
            frame_id=frame_id,
            frame_type="student_twin",
            parent_ids=["FRAME_STUDENT_BASE"],
        )

        # Set explicit slots
        student_frame.set_slot("student_id", raw_data.get("student_id") or twin_id, value_type="str")
        student_frame.set_slot("total_budget_inr", float(raw_data.get("total_budget_inr", 0.0)), value_type="float")
        student_frame.set_slot("preferred_locations", raw_data.get("preferred_locations", []), value_type="list")
        student_frame.set_slot("preferred_disciplines", raw_data.get("preferred_disciplines", []), value_type="list")
        student_frame.set_slot("career_goals", raw_data.get("career_goals", []), value_type="list")
        student_frame.set_slot("certifications", raw_data.get("certifications", []), value_type="list")
        student_frame.set_slot("entrance_exam_name", raw_data.get("entrance_exam_name"), value_type="str")
        student_frame.set_slot("entrance_rank", raw_data.get("entrance_rank"), value_type="int")

        # Register frame in registry
        self._frame_registry.register_frame(student_frame)
        self._dynamic_student_frame_ids.append(frame_id)

        # Also register alias for twin_id to ensure backward-compatible lookup
        twin_frame = FrameDefinition(
            frame_id=f"FRAME_STUDENT_{twin_id}",
            frame_type="student_twin",
            parent_ids=["FRAME_STUDENT_BASE"],
        )
        for s_name, s_slot in student_frame.slots.items():
            twin_frame.set_slot(s_name, s_slot.value, s_slot.value_type)
        self._frame_registry.register_frame(twin_frame)

        # Evict oldest dynamic student frame if capacity threshold is exceeded
        while len(self._dynamic_student_frame_ids) > self._max_retained_student_frames:
            oldest_id = self._dynamic_student_frame_ids.pop(0)
            self._frame_registry.deregister_frame(oldest_id)

        # Resolve all slots with provenance
        resolved = self._frame_registry.resolve_slots(frame_id)

        serialized_slots: Dict[str, Any] = {}
        for slot_name, slot_res in resolved.items():
            serialized_slots[slot_name] = {
                "name": slot_name,
                "value": slot_res.resolved_value,
                "source_type": slot_res.source_type.value,
                "source_frame_id": slot_res.source_frame_id,
                "inheritance_path": slot_res.inheritance_path,
                "is_conflicted": slot_res.is_conflicted,
            }

        return {
            "frame_id": frame_id,
            "parent_frame_id": "FRAME_STUDENT_BASE",
            "slots": serialized_slots,
        }

    def _evaluate_multidimensional_completeness(
        self,
        academic_identity: AcademicIdentity,
        entrance_profile: EntranceExamProfile,
        fin_constraints: FinancialConstraints,
        geo_prefs: GeographicPreferences,
        interests_goals: InterestsAndGoals,
    ) -> Tuple[Dict[str, DimensionCompleteness], CompletenessState]:
        """Evaluates completeness across 5 independent dimensions."""
        dims: Dict[str, DimensionCompleteness] = {}

        # 1. Academic Completeness
        valid_academic = [s for s in academic_identity.subject_scores if s.conversion_status == FactValidationStatus.VALID]
        invalid_academic = [s for s in academic_identity.subject_scores if s.conversion_status == FactValidationStatus.INVALID]
        review_academic = [s for s in academic_identity.subject_scores if s.conversion_status == FactValidationStatus.NEEDS_REVIEW]

        if invalid_academic or review_academic:
            acad_state = CompletenessState.NEEDS_REVIEW
            acad_expl = "Academic transcript contains invalid scores or unsupported grading scales requiring manual audit."
        elif len(valid_academic) >= 3:
            acad_state = CompletenessState.COMPLETE
            acad_expl = f"Verified {len(valid_academic)} standard academic subject scores with valid normalization."
        elif len(valid_academic) > 0:
            acad_state = CompletenessState.PARTIAL
            acad_expl = f"Partial transcript: only {len(valid_academic)} subject(s) provided. 3 or more subjects recommended."
        else:
            acad_state = CompletenessState.NEEDS_REVIEW
            acad_expl = "No academic subject scores provided."

        dims["academic"] = DimensionCompleteness(
            dimension_name="academic",
            state=acad_state,
            available_facts=[f"SUBJ_{s.subject_code}" for s in valid_academic],
            missing_facts=["additional_core_subjects"] if len(valid_academic) < 3 else [],
            invalid_facts=[f"SUBJ_{s.subject_code}" for s in invalid_academic],
            review_facts=[f"SUBJ_{s.subject_code}" for s in review_academic],
            explanation=acad_expl,
        )

        # 2. Entrance Exam Completeness
        if entrance_profile.exam_name and entrance_profile.rank:
            ent_state = CompletenessState.COMPLETE
            ent_expl = f"Verified entrance examination {entrance_profile.exam_name} with rank {entrance_profile.rank}."
            ent_avail = ["entrance_exam_name", "entrance_rank"]
            ent_missing = []
        elif entrance_profile.exam_name or entrance_profile.rank:
            ent_state = CompletenessState.PARTIAL
            ent_expl = "Partial entrance examination profile: either exam name or rank is missing."
            ent_avail = ["entrance_exam_name"] if entrance_profile.exam_name else ["entrance_rank"]
            ent_missing = ["entrance_rank"] if entrance_profile.exam_name else ["entrance_exam_name"]
        else:
            ent_state = CompletenessState.PARTIAL
            ent_expl = "No entrance exam recorded. Optional for programmes evaluating exclusively on academic criteria."
            ent_avail = []
            ent_missing = ["entrance_exam_name", "entrance_rank"]

        dims["entrance_exam"] = DimensionCompleteness(
            dimension_name="entrance_exam",
            state=ent_state,
            available_facts=ent_avail,
            missing_facts=ent_missing,
            invalid_facts=[],
            review_facts=[],
            explanation=ent_expl,
        )

        # 3. Financial Completeness
        if fin_constraints.is_budget_provided:
            fin_state = CompletenessState.COMPLETE
            fin_expl = f"Education budget of INR {fin_constraints.total_budget_inr:,.2f} specified."
            fin_avail = ["total_budget_inr"]
            fin_missing = []
        else:
            fin_state = CompletenessState.PARTIAL
            fin_expl = "No education budget specified (defaults to INR 0.00). Affordability checks will default to unbudgeted."
            fin_avail = []
            fin_missing = ["total_budget_inr"]

        dims["financial"] = DimensionCompleteness(
            dimension_name="financial",
            state=fin_state,
            available_facts=fin_avail,
            missing_facts=fin_missing,
            invalid_facts=[],
            review_facts=[],
            explanation=fin_expl,
        )

        # 4. Geographic Completeness
        if geo_prefs.preference_type == GeographicPreferenceType.PREFERRED_LOCATIONS:
            geo_state = CompletenessState.COMPLETE
            geo_expl = f"Constrained to {len(geo_prefs.preferred_locations)} preferred location(s): {', '.join(geo_prefs.preferred_locations)}."
            geo_avail = list(geo_prefs.preferred_locations)
            geo_missing = []
        elif geo_prefs.preference_type == GeographicPreferenceType.ANYWHERE_IN_INDIA:
            geo_state = CompletenessState.COMPLETE
            geo_expl = "Explicitly unconstrained: applicant confirmed open to academic locations anywhere in India."
            geo_avail = ["anywhere_in_india"]
            geo_missing = []
        else:
            geo_state = CompletenessState.COMPLETE
            geo_expl = "Geographic preference not provided (neutral across all locations). Programmes will be presented without geographic filtering."
            geo_avail = ["neutral_unfiltered"]
            geo_missing = []

        dims["geographic"] = DimensionCompleteness(
            dimension_name="geographic",
            state=geo_state,
            available_facts=geo_avail,
            missing_facts=geo_missing,
            invalid_facts=[],
            review_facts=[],
            explanation=geo_expl,
        )

        # 5. Interests and Career Completeness
        has_disc = len(interests_goals.preferred_disciplines) > 0
        has_goals = len(interests_goals.career_goals) > 0

        if has_disc and has_goals:
            int_state = CompletenessState.COMPLETE
            int_expl = "Both preferred disciplines and career goals specified."
            int_missing = []
        elif has_disc or has_goals:
            int_state = CompletenessState.PARTIAL
            int_expl = "Partial preferences: only disciplines or career goals specified."
            int_missing = ["career_goals"] if has_disc else ["preferred_disciplines"]
        else:
            int_state = CompletenessState.NEEDS_REVIEW
            int_expl = "Neither preferred academic disciplines nor career goals specified."
            int_missing = ["preferred_disciplines", "career_goals"]

        dims["interests_and_career"] = DimensionCompleteness(
            dimension_name="interests_and_career",
            state=int_state,
            available_facts=interests_goals.preferred_disciplines + interests_goals.career_goals,
            missing_facts=int_missing,
            invalid_facts=[],
            review_facts=[],
            explanation=int_expl,
        )

        # Overall Completeness State
        states = [d.state for d in dims.values()]
        if CompletenessState.NEEDS_REVIEW in states:
            overall = CompletenessState.NEEDS_REVIEW
        elif all(s == CompletenessState.COMPLETE for s in states):
            overall = CompletenessState.COMPLETE
        else:
            overall = CompletenessState.PARTIAL

        return dims, overall
