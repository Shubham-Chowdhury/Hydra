"""Interest Decoder Agent for Hydra (Phase 6 / M006).

Provides neural sentence embedding decoding of natural language student interest descriptions
into canonical ontology concepts, utilizing pretrained transformer embeddings (via fastembed/ONNX),
with an explicit deterministic lexical hashing baseline fallback, cosine similarity ranking,
knowledge-graph traversal, and an explicit user confirmation lifecycle.

MATHEMATICAL AND ARCHITECTURAL DIRECTIVE:
1. Cosine Similarity:
   Cosine similarity between input embedding A and concept anchor B is computed as:
   cosine(A, B) = (A . B) / (||A|| * ||B||)
   Because vectors are normalized to unit Euclidean length (||A|| = 1, ||B|| = 1),
   cosine(A, B) = sum_{i=1}^D (A_i * B_i).
2. Deep Learning vs Lexical Baseline:
   - Primary: sentence-transformers/all-MiniLM-L6-v2 (384-dimensional dense neural embedding,
     22.7M parameters, local ONNX Runtime CPU execution, Apache 2.0).
   - Fallback: 128-dimensional character n-gram hashing baseline (retained as an explicit
     non-neural fallback when transformer weights or ONNX runtimes are unavailable).
3. Strict Status Lifecycle:
   Raw Text (STUDENT_STATED) -> Inference (MODEL_SUGGESTED) -> Explicit Approval (USER_CONFIRMED).
4. Zero Silent Twin Mutation:
   Model outputs are advisory candidates only. The student Digital Twin is updated
   ONLY upon receiving an explicit confirmation request.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
import os
import re
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from fastembed import TextEmbedding

    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False

from app.domain.interest import (
    CandidateConcept,
    CanonicalConcept,
    ConceptType,
    ConfirmedInterestRecord,
    InterestDecodingResult,
    InterestModelStatus,
    InterestStatus,
    ModelOperationalStatus,
)
from app.knowledge.graph import HydraKnowledgeGraph, RelationshipType


class LexicalHashingEncoder:
    """Explicit lexical subword character n-gram hashing baseline.

    NOTE ON REALITY:
    This is an explicit lexical feature extraction baseline using character n-gram
    hashing, NOT deep learning or a transformer. It is retained as a zero-dependency
    local fallback when neural sentence transformer weights cannot be loaded.
    """

    DIMENSIONS: int = 128
    MODEL_ID: str = "hydra_lexical_ngram_hashing_v1.0"
    MODEL_VERSION: str = "hydra_dense_semantic_v1.0.0"
    ARCHITECTURAL_DESCRIPTION: str = "128-D Lexical Subword n-Gram Hashing Baseline (Non-Neural)"
    IS_NEURAL: bool = False
    PARAMETER_COUNT: str = "0 (Rule/Hashing-based, No Trained Weights)"
    LICENSE: str = "Apache 2.0 (Hydra Core)"

    STOPWORDS: Set[str] = {
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
        "he", "him", "his", "she", "her", "its", "they", "them", "their",
        "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is",
        "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
        "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or",
        "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
        "against", "between", "into", "through", "during", "before", "after", "above",
        "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
        "again", "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        "can", "will", "just", "don", "should", "now", "like", "enjoy", "love", "want",
        "interested", "interest", "good", "passionate", "working", "building", "creating",
    }

    def preprocess(self, text: str) -> List[str]:
        """Normalizes text by lowercasing, stripping special characters, and removing stopwords."""
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        tokens = [t.strip() for t in clean.split() if t.strip()]
        return [t for t in tokens if t not in self.STOPWORDS]

    def _hash_ngram(self, ngram: str) -> Tuple[int, float]:
        """Hashes an n-gram into a deterministic coordinate index [0, DIMENSIONS-1] and sign {+1, -1}."""
        digest = hashlib.sha256(ngram.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % self.DIMENSIONS
        sign = 1.0 if (digest[4] % 2 == 0) else -1.0
        return idx, sign

    def encode(self, text: str) -> List[float]:
        """Encodes text into a normalized 128-dimensional continuous semantic unit vector."""
        tokens = self.preprocess(text)
        if not tokens:
            return [0.0] * self.DIMENSIONS

        vector = [0.0] * self.DIMENSIONS

        # Unigrams
        for token in tokens:
            w_idx, w_sign = self._hash_ngram(token)
            vector[w_idx] += w_sign * 3.0

            # Subword character 3-gram and 4-gram embeddings
            padded = f"<{token}>"
            for n in (3, 4):
                if len(padded) >= n:
                    for i in range(len(padded) - n + 1):
                        sub = padded[i : i + n]
                        s_idx, s_sign = self._hash_ngram(sub)
                        vector[s_idx] += s_sign * 1.0

        # Word bigrams (e.g. "machine learning", "deep learning")
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            b_idx, b_sign = self._hash_ngram(bigram)
            vector[b_idx] += b_sign * 4.0

        # Euclidean L2 Normalization: ||v||_2 = sqrt(sum(v_i^2))
        norm = math.sqrt(sum(x * x for x in vector))
        if norm < 1e-9:
            return [0.0] * self.DIMENSIONS

        return [x / norm for x in vector]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculates cosine similarity between two unit vectors: dot(v1, v2)."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        return max(-1.0, min(1.0, dot))


# Backwards compatibility alias
DenseSemanticEncoder = LexicalHashingEncoder


class NeuralSentenceEmbeddingEncoder:
    """Genuine deep learning sentence embedding encoder using ONNX Runtime CPU.

    Uses pretrained sentence-transformers/all-MiniLM-L6-v2 model via fastembed.
    Projects natural language text into a 384-dimensional dense semantic vector space.
    Vectors are Euclidean L2-normalized so dot product equals cosine similarity.
    """

    DIMENSIONS: int = 384
    MODEL_ID: str = "sentence-transformers/all-MiniLM-L6-v2"
    MODEL_VERSION: str = "all-MiniLM-L6-v2-onnx"
    ARCHITECTURAL_DESCRIPTION: str = "6-layer MiniLM Transformer with Mean Pooling (ONNX Runtime Local CPU)"
    IS_NEURAL: bool = True
    PARAMETER_COUNT: str = "22.7M parameters"
    LICENSE: str = "Apache 2.0 (Hugging Face / sentence-transformers)"

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        if not FASTEMBED_AVAILABLE:
            raise RuntimeError("fastembed is not installed in the current environment.")
        # Resolve persistent model cache location
        resolved_cache = (
            cache_dir
            or os.environ.get("FASTEMBED_CACHE_PATH")
            or os.environ.get("HYDRA_MODEL_CACHE_DIR")
        )
        if not resolved_cache:
            user_cache = os.path.join(os.path.expanduser("~"), ".cache", "fastembed")
            temp_cache = os.path.join(tempfile.gettempdir(), "fastembed_cache")
            if os.path.exists(user_cache):
                resolved_cache = user_cache
            elif os.path.exists(temp_cache):
                resolved_cache = temp_cache
            else:
                resolved_cache = user_cache

        self.cache_dir = resolved_cache
        # Load local ONNX model
        self._model = TextEmbedding(model_name=self.MODEL_ID, cache_dir=self.cache_dir)

    def encode(self, text: str) -> List[float]:
        """Encodes text into a normalized 384-dimensional continuous unit vector."""
        cleaned = text.strip()
        if not cleaned:
            return [0.0] * self.DIMENSIONS

        # fastembed returns generator of numpy arrays, already L2-normalized
        embedding_gen = self._model.embed([cleaned])
        emb_arr = next(embedding_gen)
        return [float(x) for x in emb_arr]

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encodes multiple texts in a single batch pass."""
        if not texts:
            return []
        cleaned = [t.strip() if t.strip() else " " for t in texts]
        embedding_gen = self._model.embed(cleaned)
        return [[float(x) for x in emb] for emb in embedding_gen]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculates cosine similarity between two unit vectors: dot(v1, v2)."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        return max(-1.0, min(1.0, dot))


class ConceptTaxonomyRegistry:
    """Authoritative repository of canonical academic concepts from Hydra's knowledge network."""

    TAXONOMY_VERSION: str = "hydra_concept_taxonomy_v1.0.0"

    def __init__(self, encoder: Union[NeuralSentenceEmbeddingEncoder, LexicalHashingEncoder]) -> None:
        self.encoder = encoder
        self.concepts: Dict[str, CanonicalConcept] = {}
        self.concept_embeddings: Dict[str, List[float]] = {}
        self._populate_canonical_concepts()

    def _add_concept(
        self,
        concept_id: str,
        name: str,
        concept_type: ConceptType,
        description: str,
        keywords: List[str],
        related_nodes: List[str],
    ) -> None:
        concept = CanonicalConcept(
            concept_id=concept_id,
            name=name,
            concept_type=concept_type,
            description=description,
            keywords=keywords,
            related_node_ids=related_nodes,
        )
        self.concepts[concept_id] = concept
        anchor_text = f"{name}. {description} Keywords: {', '.join(keywords)}"
        self.concept_embeddings[concept_id] = self.encoder.encode(anchor_text)

    def recompute_embeddings(self, encoder: Union[NeuralSentenceEmbeddingEncoder, LexicalHashingEncoder]) -> None:
        """Recomputes embeddings for all registered concepts with a new encoder."""
        self.encoder = encoder
        for concept_id, concept in self.concepts.items():
            anchor_text = f"{concept.name}. {concept.description} Keywords: {', '.join(concept.keywords)}"
            self.concept_embeddings[concept_id] = self.encoder.encode(anchor_text)

    def _populate_canonical_concepts(self) -> None:
        """Populates canonical disciplines, skills, careers, and interest areas."""
        # Disciplines
        self._add_concept(
            "DISC_COMPUTER_SCIENCE",
            "Computer Science and Engineering",
            ConceptType.DISCIPLINE,
            "Study of algorithms, computation, artificial intelligence, software systems, and data structures.",
            ["programming", "software", "algorithms", "ai", "machine learning", "coding", "web", "cloud"],
            ["SKILL_PYTHON", "SKILL_ALGORITHMS", "CAREER_SOFTWARE_ENGINEER"],
        )
        self._add_concept(
            "DISC_MECHANICAL",
            "Mechanical Engineering",
            ConceptType.DISCIPLINE,
            "Design and analysis of thermal and mechanical systems, thermodynamics, manufacturing, and mechanics.",
            ["machines", "engines", "thermodynamics", "automotive", "cad", "robotics", "mechanics", "manufacturing"],
            ["SKILL_THERMODYNAMICS", "SKILL_CAD", "CAREER_MECHANICAL_DESIGNER"],
        )
        self._add_concept(
            "DISC_ELECTRICAL",
            "Electrical and Electronics Engineering",
            ConceptType.DISCIPLINE,
            "Circuits, signal processing, power systems, microcontrollers, VLSI, and electromagnetism.",
            ["circuits", "electronics", "power", "signals", "microcontrollers", "vlsi", "hardware", "semiconductors"],
            ["SKILL_CIRCUITS", "SKILL_EMBEDDED", "CAREER_HARDWARE_ENGINEER"],
        )
        self._add_concept(
            "DISC_BIOTECHNOLOGY",
            "Biotechnology and Biochemical Engineering",
            ConceptType.DISCIPLINE,
            "Application of biology, biochemistry, genetic engineering, and bio-process design to technological solutions.",
            ["biology", "genetics", "biochemical", "molecular", "pharma", "medicine", "bioinformatics"],
            ["SKILL_BIOCHEM", "CAREER_BIO_RESEARCHER"],
        )
        self._add_concept(
            "DISC_ROBOTICS",
            "Robotics and Autonomous Systems",
            ConceptType.DISCIPLINE,
            "Integration of mechanical design, electronic control, sensors, and intelligent software to build autonomous robots.",
            ["robotics", "robots", "autonomous", "sensors", "actuators", "control", "drones", "automation"],
            ["SKILL_EMBEDDED_SYSTEMS", "CAREER_ROBOTICS_ENGINEER"],
        )

        # Skills
        self._add_concept(
            "SKILL_MACHINE_LEARNING",
            "Machine Learning & Artificial Intelligence",
            ConceptType.SKILL,
            "Statistical modeling, neural networks, deep learning, NLP, and computer vision algorithms.",
            ["ml", "ai", "neural networks", "deep learning", "nlp", "computer vision", "predictive", "statistics"],
            ["CAREER_ML_ENGINEER", "DISC_COMPUTER_SCIENCE"],
        )
        self._add_concept(
            "SKILL_PYTHON",
            "Software & Python Programming",
            ConceptType.SKILL,
            "Object-oriented software development, Python programming, systems architecture, and testing.",
            ["python", "software", "programming", "coding", "git", "backend"],
            ["DISC_COMPUTER_SCIENCE", "CAREER_SOFTWARE_ENGINEER"],
        )
        self._add_concept(
            "SKILL_ALGORITHMS",
            "Data Structures & Algorithms",
            ConceptType.SKILL,
            "Computational complexity, graph algorithms, sorting, searching, and algorithmic optimization.",
            ["algorithms", "data structures", "graphs", "trees", "optimization", "complexity"],
            ["DISC_COMPUTER_SCIENCE", "CAREER_SOFTWARE_ENGINEER"],
        )
        self._add_concept(
            "SKILL_CIRCUITS",
            "Circuit Analysis & Hardware Design",
            ConceptType.SKILL,
            "Analog and digital circuit design, VLSI, PCB layout, and signal conditioning.",
            ["circuits", "analog", "digital", "pcb", "vlsi", "semiconductor"],
            ["DISC_ELECTRICAL", "CAREER_HARDWARE_ENGINEER"],
        )
        self._add_concept(
            "SKILL_CAD",
            "CAD & Mechanical Modeling",
            ConceptType.SKILL,
            "Computer-aided mechanical drafting, 3D modeling, finite element analysis, and manufacturing simulation.",
            ["cad", "3d modeling", "solidworks", "fea", "drafting", "prototyping"],
            ["DISC_MECHANICAL", "CAREER_ROBOTICS_ENGINEER"],
        )
        self._add_concept(
            "SKILL_EMBEDDED_SYSTEMS",
            "Embedded Systems & Firmware Development",
            ConceptType.SKILL,
            "Low-level C/C++ programming for microcontrollers, RTOS, sensors, IoT, and hardware-software interfacing.",
            ["embedded", "firmware", "microcontrollers", "arduino", "raspberry pi", "iot", "c", "c++", "sensors"],
            ["CAREER_HARDWARE_ENGINEER", "DISC_ELECTRICAL"],
        )
        self._add_concept(
            "SKILL_THERMODYNAMICS",
            "Thermal Engineering & Fluid Mechanics",
            ConceptType.SKILL,
            "Heat transfer, fluid flow simulation, CFD, refrigeration, aerodynamics, and energy conversion.",
            ["thermal", "heat", "fluids", "aerodynamics", "cfd", "energy", "cooling"],
            ["CAREER_ROBOTICS_ENGINEER", "DISC_MECHANICAL"],
        )

        # Careers
        self._add_concept(
            "CAREER_SOFTWARE_ENGINEER",
            "Software Systems Engineer",
            ConceptType.CAREER,
            "Designs, architectures, and scales backend, cloud, and distributed software systems.",
            ["software engineer", "backend developer", "systems architect", "full stack"],
            ["DISC_COMPUTER_SCIENCE", "SKILL_PYTHON", "SKILL_ALGORITHMS"],
        )
        self._add_concept(
            "CAREER_HARDWARE_ENGINEER",
            "Hardware & VLSI Engineer",
            ConceptType.CAREER,
            "Designs microelectronics, embedded systems, processor architectures, and silicon chips.",
            ["hardware engineer", "vlsi designer", "silicon architect", "embedded engineer"],
            ["DISC_ELECTRICAL", "SKILL_CIRCUITS", "SKILL_EMBEDDED_SYSTEMS"],
        )
        self._add_concept(
            "CAREER_ROBOTICS_ENGINEER",
            "Robotics Engineer",
            ConceptType.CAREER,
            "Designs, builds, tests, and deploys intelligent autonomous robotic systems for industrial, medical, and aerospace use.",
            ["robotics engineer", "automation lead", "drone developer", "control specialist"],
            ["DISC_ROBOTICS", "DISC_MECHANICAL", "DISC_ELECTRICAL"],
        )
        self._add_concept(
            "CAREER_ML_ENGINEER",
            "Machine Learning Engineer",
            ConceptType.CAREER,
            "Builds, trains, and productionizes deep learning models, LLM systems, and predictive algorithms.",
            ["ml engineer", "ai engineer", "data scientist", "research scientist"],
            ["DISC_COMPUTER_SCIENCE", "SKILL_MACHINE_LEARNING"],
        )


class InterestDecoderAgent:
    """The Interest Decoder Agent translates unconstrained student interest narratives

    into canonical academic concepts with cosine similarity ranking and graph traversal.
    """

    MIN_TEXT_LENGTH: int = 3
    MAX_TEXT_LENGTH: int = 1000
    SIMILARITY_THRESHOLD: float = 0.08

    def __init__(
        self,
        knowledge_graph: Optional[HydraKnowledgeGraph] = None,
        force_lexical: bool = False,
        cache_dir: Optional[str] = None,
    ) -> None:
        self.encoder: Union[NeuralSentenceEmbeddingEncoder, LexicalHashingEncoder]
        self.status: ModelOperationalStatus

        if force_lexical or not FASTEMBED_AVAILABLE:
            self.encoder = LexicalHashingEncoder()
            self.status = ModelOperationalStatus.FALLBACK_TO_LEXICAL
        else:
            try:
                self.encoder = NeuralSentenceEmbeddingEncoder(cache_dir=cache_dir)
                self.status = ModelOperationalStatus.READY_NEURAL
            except Exception:
                self.encoder = LexicalHashingEncoder()
                self.status = ModelOperationalStatus.FALLBACK_TO_LEXICAL

        self.taxonomy = ConceptTaxonomyRegistry(encoder=self.encoder)
        self.knowledge_graph = knowledge_graph or HydraKnowledgeGraph()

    def get_model_status(self) -> Dict[str, Any]:
        """Returns diagnostic status and architectural provenance for the active encoder."""
        status_obj = InterestModelStatus(
            status=self.status,
            model_id=self.encoder.MODEL_ID,
            architecture=self.encoder.ARCHITECTURAL_DESCRIPTION,
            dimensions=self.encoder.DIMENSIONS,
            parameter_count=self.encoder.PARAMETER_COUNT,
            is_neural=self.encoder.IS_NEURAL,
            taxonomy_version=self.taxonomy.TAXONOMY_VERSION,
            canonical_concepts_indexed=len(self.taxonomy.concepts),
            similarity_metric="Euclidean-normalized Cosine Proximity ([-1.0, 1.0])",
            license=self.encoder.LICENSE,
            hardware_requirements="CPU only, local ONNX Runtime inference",
            runtime_device="CPU (Local Windows Host)",
            provenance="PRETRAINED_SENTENCE_TRANSFORMER_ONNX" if self.encoder.IS_NEURAL else "LEXICAL_NGRAM_HASHING_BASELINE",
        )
        return status_obj.to_dict()

    def decode(self, student_text: str) -> InterestDecodingResult:
        """Translates free-text student interests into ranked canonical concepts.

        Enforces input validation and returns advisory CandidateConcept models.
        """
        if not student_text or not isinstance(student_text, str):
            raise ValueError("Input student interest text cannot be empty.")

        stripped = student_text.strip()
        if len(stripped) < self.MIN_TEXT_LENGTH:
            raise ValueError(
                f"Input text length ({len(stripped)} chars) is below minimum of {self.MIN_TEXT_LENGTH} characters."
            )
        if len(stripped) > self.MAX_TEXT_LENGTH:
            raise ValueError(
                f"Input text length ({len(stripped)} chars) exceeds maximum allowable length of {self.MAX_TEXT_LENGTH} characters."
            )

        # 1. Encode input text into dense unit vector
        input_vector = self.encoder.encode(stripped)

        # 2. Compute cosine similarity against all indexed canonical concept anchors
        scores: List[Tuple[str, float]] = []
        for concept_id, anchor_vec in self.taxonomy.concept_embeddings.items():
            sim = self.encoder.cosine_similarity(input_vector, anchor_vec)
            if sim >= self.SIMILARITY_THRESHOLD:
                scores.append((concept_id, sim))

        # Sort descending by similarity score
        scores.sort(key=lambda x: x[1], reverse=True)

        candidates: List[CandidateConcept] = []

        for rank, (cid, sim) in enumerate(scores[:5]):
            concept = self.taxonomy.concepts[cid]

            # Discover connected graph nodes
            graph_nodes: List[Dict[str, str]] = []
            for r_id in concept.related_node_ids:
                if r_id in self.taxonomy.concepts:
                    rel_concept = self.taxonomy.concepts[r_id]
                    graph_nodes.append({
                        "node_id": r_id,
                        "name": rel_concept.name,
                        "type": rel_concept.concept_type.value,
                    })

            # Identify alternative interpretations (runner-up concepts within delta <= 0.15)
            alternatives: List[str] = [
                self.taxonomy.concepts[other_id].name
                for other_id, other_sim in scores
                if other_id != cid and abs(sim - other_sim) <= 0.15
            ][:3]

            # Uncertainty metric: 1.0 - margin between this score and subsequent runner-up
            margin = (sim - scores[rank + 1][1]) if (rank + 1 < len(scores)) else (sim - self.SIMILARITY_THRESHOLD)
            uncertainty = max(0.05, min(0.95, round(1.0 - margin, 3)))

            explanation = (
                f"Semantic match ({round(sim * 100, 1)}% vector proximity) with {concept.concept_type.value} "
                f"'{concept.name}' based on extracted themes: {', '.join(concept.keywords[:4])}."
            )

            candidate = CandidateConcept(
                concept=concept,
                similarity_score=sim,
                explanation=explanation,
                related_graph_nodes=graph_nodes,
                alternative_interpretations=alternatives,
                uncertainty=uncertainty,
                status=InterestStatus.MODEL_SUGGESTED,
                model_version=self.encoder.MODEL_ID,
                provenance="DERIVED_VIA_NEURAL_SENTENCE_EMBEDDING" if self.encoder.IS_NEURAL else "DERIVED_VIA_LEXICAL_HASHING_BASELINE",
                is_neural=self.encoder.IS_NEURAL,
            )
            candidates.append(candidate)

        top_concept = candidates[0] if candidates else None

        return InterestDecodingResult(
            input_text=stripped,
            candidates=candidates,
            top_concept=top_concept,
            taxonomy_version=self.taxonomy.TAXONOMY_VERSION,
            model_version=self.encoder.MODEL_ID,
            model_status=self.status.value,
            dimensions=self.encoder.DIMENSIONS,
            is_estimate=True,
        )

    def confirm(
        self,
        concept_id: str,
        original_similarity: float,
    ) -> ConfirmedInterestRecord:
        """Explicitly transitions a candidate concept to USER_CONFIRMED.

        Guarantees that unconfirmed concepts never enter the student's authoritative digital twin.
        """
        if concept_id not in self.taxonomy.concepts:
            raise KeyError(f"Canonical concept ID '{concept_id}' not found in taxonomy.")

        concept = self.taxonomy.concepts[concept_id]
        now_iso = datetime.now(timezone.utc).isoformat()

        return ConfirmedInterestRecord(
            concept_id=concept.concept_id,
            concept_name=concept.name,
            concept_type=concept.concept_type,
            original_similarity=original_similarity,
            confirmed_at=now_iso,
            status=InterestStatus.USER_CONFIRMED,
        )
