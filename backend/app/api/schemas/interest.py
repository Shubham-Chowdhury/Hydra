"""Pydantic Transport Schemas for the Interest Decoder Subsystem (M006)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DecodeInterestRequest(BaseModel):
    """API payload containing free-text student interest narrative."""

    interest_text: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Free-form student text describing interests, passions, or technical curiosities",
    )


class CanonicalConceptDto(BaseModel):
    """Transport schema for a canonical ontology concept."""

    concept_id: str
    name: str
    concept_type: str
    description: str
    keywords: List[str]
    related_node_ids: List[str]


class CandidateConceptDto(BaseModel):
    """Transport schema for a model-suggested candidate concept."""

    concept: CanonicalConceptDto
    similarity_score: float
    explanation: str
    related_graph_nodes: List[Dict[str, str]]
    alternative_interpretations: List[str]
    uncertainty: float
    status: str
    model_version: str
    provenance: str
    is_neural: Optional[bool] = None


class InterestDecodingResponse(BaseModel):
    """API response model containing candidate concepts and similarity rankings."""

    input_text: str
    candidates: List[CandidateConceptDto]
    top_concept: Optional[CandidateConceptDto] = None
    taxonomy_version: str
    model_version: str
    model_status: Optional[str] = None
    dimensions: Optional[int] = None
    is_estimate: bool = True
    disclaimer: str


class InterestModelStatusResponse(BaseModel):
    """API response model containing operational status and architectural diagnostics."""

    status: str
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


class ConfirmInterestRequest(BaseModel):
    """API payload for explicitly confirming an advisory candidate concept."""

    concept_id: str = Field(..., description="Canonical concept ID to confirm")
    similarity_score: float = Field(..., description="Original similarity score from decoding")


class ConfirmedInterestResponse(BaseModel):
    """API response confirming transition to USER_CONFIRMED status."""

    concept_id: str
    concept_name: str
    concept_type: str
    original_similarity: float
    confirmed_at: str
    status: str

