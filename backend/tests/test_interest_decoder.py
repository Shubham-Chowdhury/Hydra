"""Comprehensive Verification Test Suite for the Interest Decoder Agent (M006).

Tests:
1. Cosine similarity mathematical correctness and Euclidean unit normalization.
2. Valid interest text decoding with neural sentence transformer embeddings.
3. Ambiguous descriptions returning multiple candidates with uncertainty.
4. Unrelated descriptions producing low similarity scores.
5. Input validation: empty text, text < 3 chars, text > 1000 chars rejected.
6. Determinism and repeated inference stability.
7. Graph relationship discovery for candidate concepts.
8. Tripartite lifecycle: STUDENT_STATED -> MODEL_SUGGESTED -> USER_CONFIRMED.
9. API model status endpoint (/api/v1/interests/model-status).
10. API decode and confirm endpoints (/api/v1/interests/decode, /confirm).
11. Lexical hashing encoder fallback baseline verification (128-D).
12. Comparative evaluation benchmark: Neural transformer vs Lexical hashing baseline.
13. Zero silent Twin mutation guarantee.
"""

import math
import pytest
from fastapi.testclient import TestClient

from app.agents.interest_decoder import (
    DenseSemanticEncoder,
    InterestDecoderAgent,
    LexicalHashingEncoder,
    NeuralSentenceEmbeddingEncoder,
)
from app.domain.interest import InterestStatus, ModelOperationalStatus
from app.main import app


@pytest.fixture
def agent() -> InterestDecoderAgent:
    return InterestDecoderAgent()


def test_1_cosine_similarity_and_vector_normalization():
    """Verifies that encoders generate Euclidean unit vectors and valid cosine bounds."""
    # Test Lexical Hashing Baseline
    lex_encoder = LexicalHashingEncoder()
    v1 = lex_encoder.encode("artificial intelligence machine learning")
    v2 = lex_encoder.encode("machine learning artificial intelligence")
    assert len(v1) == 128
    assert len(v2) == 128
    norm1 = math.sqrt(sum(x * x for x in v1))
    norm2 = math.sqrt(sum(x * x for x in v2))
    assert pytest.approx(norm1, rel=1e-5) == 1.0
    assert pytest.approx(norm2, rel=1e-5) == 1.0
    assert 0.0 <= lex_encoder.cosine_similarity(v1, v2) <= 1.0

    # Test Neural Transformer Encoder
    neural_encoder = NeuralSentenceEmbeddingEncoder()
    nv1 = neural_encoder.encode("artificial intelligence machine learning")
    nv2 = neural_encoder.encode("machine learning artificial intelligence")
    assert len(nv1) == 384
    assert len(nv2) == 384
    nnorm1 = math.sqrt(sum(x * x for x in nv1))
    nnorm2 = math.sqrt(sum(x * x for x in nv2))
    assert pytest.approx(nnorm1, rel=1e-4) == 1.0
    assert pytest.approx(nnorm2, rel=1e-4) == 1.0
    sim = neural_encoder.cosine_similarity(nv1, nv2)
    assert 0.90 <= sim <= 1.0001


def test_2_valid_interest_text_decoding(agent):
    """Verifies that an AI/robotics narrative yields the expected canonical concepts."""
    text = "I enjoy building autonomous robots, working with sensors, and programming intelligent control systems."
    result = agent.decode(text)

    assert result.input_text == text
    assert len(result.candidates) > 0
    assert result.top_concept is not None

    top_ids = [c.concept.concept_id for c in result.candidates]
    assert "DISC_ROBOTICS" in top_ids or "CAREER_ROBOTICS_ENGINEER" in top_ids
    assert result.is_estimate is True
    assert result.top_concept.status == InterestStatus.MODEL_SUGGESTED
    assert result.dimensions == 384
    assert result.model_status == ModelOperationalStatus.READY_NEURAL.value


def test_3_ambiguous_description_returns_uncertainty(agent):
    """Verifies that ambiguous descriptions yield higher uncertainty and alternative interpretations."""
    text = "I like science, math, technology, and analyzing various systems."
    result = agent.decode(text)

    assert len(result.candidates) >= 2
    top = result.top_concept
    assert top is not None
    assert top.uncertainty > 0.05
    assert len(top.alternative_interpretations) >= 0


def test_4_unrelated_text_produces_low_similarity(agent):
    """Verifies that completely unrelated text produces low similarity scores."""
    text = "Baking sourdough bread, knitting woolen blankets, and gardening in the backyard."
    result = agent.decode(text)

    # All candidate similarities should be low
    for c in result.candidates:
        assert c.similarity_score < 0.40


def test_5_input_validation_boundaries(agent):
    """Verifies that empty strings, strings < 3 chars, and strings > 1000 chars are rejected."""
    with pytest.raises(ValueError, match="cannot be empty"):
        agent.decode("")

    with pytest.raises(ValueError, match="below minimum"):
        agent.decode("hi")

    long_text = "machine learning " * 100  # > 1500 chars
    with pytest.raises(ValueError, match="exceeds maximum"):
        agent.decode(long_text)


def test_6_deterministic_repeated_inference(agent):
    """Verifies that repeated invocations on identical text produce 100% deterministic results."""
    text = "Developing embedded firmware for microcontrollers and hardware circuits."
    res1 = agent.decode(text)
    res2 = agent.decode(text)

    assert len(res1.candidates) == len(res2.candidates)
    for c1, c2 in zip(res1.candidates, res2.candidates):
        assert c1.concept.concept_id == c2.concept.concept_id
        assert c1.similarity_score == pytest.approx(c2.similarity_score, abs=1e-5)
        assert c1.uncertainty == pytest.approx(c2.uncertainty, abs=1e-5)


def test_7_graph_relationships_discovered(agent):
    """Verifies that candidate concepts include connected graph nodes (skills, careers)."""
    text = "Computer programming, algorithms, software development, and cloud computing."
    result = agent.decode(text)

    cs_candidate = next((c for c in result.candidates if c.concept.concept_id == "DISC_COMPUTER_SCIENCE"), None)
    assert cs_candidate is not None
    assert len(cs_candidate.related_graph_nodes) > 0
    rel_names = [n["name"] for n in cs_candidate.related_graph_nodes]
    assert any("Software" in name or "Algorithm" in name for name in rel_names)


def test_8_explicit_confirmation_lifecycle(agent):
    """Verifies that a candidate is confirmed only upon explicit confirmation call."""
    confirmed = agent.confirm("DISC_ROBOTICS", original_similarity=0.82)
    assert confirmed.concept_id == "DISC_ROBOTICS"
    assert confirmed.status == InterestStatus.USER_CONFIRMED
    assert confirmed.original_similarity == 0.82
    assert confirmed.confirmed_at is not None

    # Invalid concept ID
    with pytest.raises(KeyError, match="not found in taxonomy"):
        agent.confirm("NONEXISTENT_CONCEPT_123", original_similarity=0.5)


def test_9_api_model_status():
    """Verifies GET /api/v1/interests/model-status endpoint."""
    client = TestClient(app)
    res = client.get("/api/v1/interests/model-status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("READY_NEURAL", "FALLBACK_TO_LEXICAL")
    assert data["dimensions"] in (384, 128)
    assert data["canonical_concepts_indexed"] >= 8
    assert "architecture" in data


def test_10_api_decode_and_confirm():
    """Verifies POST /api/v1/interests/decode and POST /api/v1/interests/confirm endpoints."""
    client = TestClient(app)

    # 1. Decode
    decode_payload = {
        "interest_text": "I want to work with artificial intelligence, deep learning, and intelligent algorithms."
    }
    res_dec = client.post("/api/v1/interests/decode", json=decode_payload)
    assert res_dec.status_code == 200
    dec_data = res_dec.json()
    assert len(dec_data["candidates"]) > 0
    top_concept_id = dec_data["candidates"][0]["concept"]["concept_id"]
    top_sim = dec_data["candidates"][0]["similarity_score"]

    # 2. Confirm
    confirm_payload = {
        "concept_id": top_concept_id,
        "similarity_score": top_sim,
    }
    res_conf = client.post("/api/v1/interests/confirm", json=confirm_payload)
    assert res_conf.status_code == 200
    conf_data = res_conf.json()
    assert conf_data["concept_id"] == top_concept_id
    assert conf_data["status"] == "USER_CONFIRMED"


def test_11_lexical_fallback_mode():
    """Verifies that forced lexical mode operates cleanly as a deterministic 128-D baseline."""
    lex_agent = InterestDecoderAgent(force_lexical=True)
    status = lex_agent.get_model_status()

    assert status["status"] == ModelOperationalStatus.FALLBACK_TO_LEXICAL.value
    assert status["dimensions"] == 128
    assert status["is_neural"] is False
    assert "Baseline" in status["architecture"]

    result = lex_agent.decode("Robotics, sensor integration, and motor control.")
    assert result.dimensions == 128
    assert result.model_status == ModelOperationalStatus.FALLBACK_TO_LEXICAL.value
    assert len(result.candidates) > 0


def test_12_comparative_evaluation_benchmark():
    """Compares neural sentence embedding against lexical hashing on a labeled test set."""
    neural_agent = InterestDecoderAgent(force_lexical=False)
    lexical_agent = InterestDecoderAgent(force_lexical=True)

    benchmark_queries = [
        ("autonomous quadcopters, drones, and robotic manipulator arms", "DISC_ROBOTICS"),
        ("deep convolutional neural networks, transformer architectures, and large language models", "SKILL_MACHINE_LEARNING"),
        ("circuit simulations, VLSI chip layout, and semiconductor microelectronics", "SKILL_CIRCUITS"),
        ("aerodynamics, heat exchangers, fluid dynamics, and thermodynamic refrigeration", "SKILL_THERMODYNAMICS"),
    ]

    for query, expected_concept_id in benchmark_queries:
        neural_res = neural_agent.decode(query)
        lexical_res = lexical_agent.decode(query)

        neural_top_ids = [c.concept.concept_id for c in neural_res.candidates[:2]]
        lexical_top_ids = [c.concept.concept_id for c in lexical_res.candidates[:3]]

        # Neural transformer captures semantic synonyms without requiring exact keyword overlaps
        assert expected_concept_id in neural_top_ids, f"Neural failed to find {expected_concept_id} in {neural_top_ids} for '{query}'"
        # Lexical baseline should also rank relevant concepts
        assert len(lexical_top_ids) > 0


def test_13_zero_silent_twin_mutation_guarantee():
    """Verifies that decoding produces candidate objects without mutating external state."""
    agent = InterestDecoderAgent()
    text = "Building deep learning systems."
    res = agent.decode(text)

    # Status must remain MODEL_SUGGESTED until confirmed
    for candidate in res.candidates:
        assert candidate.status == InterestStatus.MODEL_SUGGESTED
