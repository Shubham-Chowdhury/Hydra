"""Interest Decoder Domain Models for Hydra (Phase 6 / M006).

Defines canonical concept structures, candidate concepts, similarity metrics,
confirmation lifecycles, and decoding results.

CRITICAL ARCHITECTURAL DIRECTIVES:
1. Strict Tripartite Status Lifecycle:
   - STUDENT_STATED: Raw, unverified free text provided by the student.
   - MODEL_SUGGESTED: Advisory concepts proposed by the neural/semantic embedding decoder.
   - USER_CONFIRMED: Concepts explicitly reviewed, accepted, and authorized by the user.
2. Zero Silent Twin Mutation: The Decoder must never mutate the student's digital twin
   without explicit user confirmation.
3. Decoupled Probabilities: Raw cosine similarity scores represent semantic vector
   proximities, NEVER calibrated admission probabilities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class InterestStatus(str, Enum):
    """Lifecycle classification of an interest concept."""

    STUDENT_STATED = "STUDENT_STATED"
    MODEL_SUGGESTED = "MODEL_SUGGESTED"
    USER_CONFIRMED = "USER_CONFIRMED"
    REJECTED = "REJECTED"


class ModelOperationalStatus(str, Enum):
    """Operational readiness state of the interest embedding model."""

    READY_NEURAL = "READY_NEURAL"
    FALLBACK_TO_LEXICAL = "FALLBACK_TO_LEXICAL"
    UNAVAILABLE = "UNAVAILABLE"


class ConceptType(str, Enum):
    """Ontological type of a canonical concept from Hydra's Knowledge Graph."""

    DISCIPLINE = "discipline"
    SKILL = "skill"
    CAREER = "career"
    INTEREST_AREA = "interest_area"


@dataclass(frozen=True)
class CanonicalConcept:
    """An authoritative concept node rooted in Hydra's semantic ontology."""

    concept_id: str
    name: str
    concept_type: ConceptType
    description: str
    keywords: List[str] = field(default_factory=list)
    related_node_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "concept_type": self.concept_type.value,
            "description": self.description,
            "keywords": list(self.keywords),
            "related_node_ids": list(self.related_node_ids),
        }


@dataclass(frozen=True)
class InterestModelStatus:
    """Operational diagnostic metadata for the active embedding model."""

    status: ModelOperationalStatus
    model_id: str
    architecture: str
    dimensions: int
    parameter_count: str
    is_neural: bool
    taxonomy_version: str
    canonical_concepts_indexed: int
    similarity_metric: str
    license: str
    hardware_requirements: str
    runtime_device: str
    provenance: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "model_id": self.model_id,
            "architecture": self.architecture,
            "dimensions": self.dimensions,
            "parameter_count": self.parameter_count,
            "is_neural": self.is_neural,
            "taxonomy_version": self.taxonomy_version,
            "canonical_concepts_indexed": self.canonical_concepts_indexed,
            "similarity_metric": self.similarity_metric,
            "license": self.license,
            "hardware_requirements": self.hardware_requirements,
            "runtime_device": self.runtime_device,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class CandidateConcept:
    """A model-suggested canonical concept matching free-text student interests."""

    concept: CanonicalConcept
    similarity_score: float  # Cosine similarity in range [-1.0, 1.0]
    explanation: str
    related_graph_nodes: List[Dict[str, str]] = field(default_factory=list)
    alternative_interpretations: List[str] = field(default_factory=list)
    uncertainty: float = 0.0
    status: InterestStatus = InterestStatus.MODEL_SUGGESTED
    model_version: str = "sentence-transformers/all-MiniLM-L6-v2"
    provenance: str = "DERIVED_VIA_NEURAL_SENTENCE_EMBEDDING"
    is_neural: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept": self.concept.to_dict(),
            "similarity_score": round(self.similarity_score, 4),
            "explanation": self.explanation,
            "related_graph_nodes": list(self.related_graph_nodes),
            "alternative_interpretations": list(self.alternative_interpretations),
            "uncertainty": round(self.uncertainty, 4),
            "status": self.status.value,
            "model_version": self.model_version,
            "provenance": self.provenance,
            "is_neural": self.is_neural,
        }


@dataclass(frozen=True)
class ConfirmedInterestRecord:
    """An interest concept explicitly verified and accepted by the student."""

    concept_id: str
    concept_name: str
    concept_type: ConceptType
    original_similarity: float
    confirmed_at: str
    status: InterestStatus = InterestStatus.USER_CONFIRMED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "concept_type": self.concept_type.value,
            "original_similarity": self.original_similarity,
            "confirmed_at": self.confirmed_at,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class InterestDecodingResult:
    """Complete result payload from the Interest Decoder inference pipeline."""

    input_text: str
    candidates: List[CandidateConcept]
    top_concept: Optional[CandidateConcept]
    taxonomy_version: str
    model_version: str
    model_status: str = ModelOperationalStatus.READY_NEURAL.value
    dimensions: int = 384
    is_estimate: bool = True
    disclaimer: str = (
        "Model-suggested concepts are advisory semantic interpretations. "
        "They do not alter the Student Digital Twin until explicitly confirmed by the user."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_text": self.input_text,
            "candidates": [c.to_dict() for c in self.candidates],
            "top_concept": self.top_concept.to_dict() if self.top_concept else None,
            "taxonomy_version": self.taxonomy_version,
            "model_version": self.model_version,
            "model_status": self.model_status,
            "dimensions": self.dimensions,
            "is_estimate": self.is_estimate,
            "disclaimer": self.disclaimer,
        }

