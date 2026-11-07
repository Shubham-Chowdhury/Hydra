"""Interest Service for Hydra (Phase 6 / M006).

Coordinates the natural language Interest Decoder agent, model status reporting,
and explicit user confirmation workflows.
"""

from typing import Any, Dict, Optional

from app.agents.interest_decoder import InterestDecoderAgent
from app.domain.interest import (
    ConfirmedInterestRecord,
    InterestDecodingResult,
)
from app.knowledge.graph import HydraKnowledgeGraph


class InterestService:
    """Application orchestration service for the Interest Decoder subsystem."""

    def __init__(
        self,
        agent: Optional[InterestDecoderAgent] = None,
        graph: Optional[HydraKnowledgeGraph] = None,
        force_lexical: bool = False,
    ) -> None:
        self.agent = agent or InterestDecoderAgent(knowledge_graph=graph, force_lexical=force_lexical)

    def decode_interests(self, text: str) -> InterestDecodingResult:
        """Executes the Interest Decoder agent on student natural language text."""
        return self.agent.decode(text)

    def confirm_interest(self, concept_id: str, original_similarity: float) -> ConfirmedInterestRecord:
        """Processes explicit user confirmation for an advisory candidate concept."""
        return self.agent.confirm(concept_id, original_similarity)

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic status of the embedding engine and taxonomy."""
        return self.agent.get_model_status()

