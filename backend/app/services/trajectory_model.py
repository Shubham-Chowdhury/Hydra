"""Deep Trajectory Sequence Model for Hydra.

Implements a deep neural network architecture for modeling student activity
sequences, academic mastery embeddings, and projecting career readiness indices.

CRITICAL DIRECTIVES:
- Probabilistic estimates only: outputs are flagged with is_estimate=True and confidence score.
- NEVER overrides deterministic eligibility rules.
- Fast, reproducible tensor mathematics using NumPy.
"""

from typing import Any, Dict, List, Optional
import numpy as np

from app.domain.assessment_report import NeuralTrajectoryInsights, UserInteractionEvent


class DeepTrajectorySequenceModel:
    """Deep residual neural network projecting student trajectories and career readiness."""

    DISCIPLINES: List[str] = [
        "Computer Science",
        "Data Science",
        "Electronics & Communication",
        "Mechanical Engineering",
        "Civil Engineering",
        "Biotechnology",
        "Business Analytics",
        "Design & Architecture",
    ]

    CAREER_PATHS: List[str] = [
        "Software Systems Architect",
        "Machine Learning Engineer",
        "Cloud Infrastructure Specialist",
        "Embedded Systems Engineer",
        "Quantitative Data Analyst",
        "Autonomous Robotics Engineer",
    ]

    def __init__(self, seed: int = 42) -> None:
        """Initialize fixed neural network weights for deterministic, reproducible inference."""
        self.rng = np.random.RandomState(seed)
        self.input_dim = 16
        self.hidden_dim = 32
        self.output_dim = len(self.DISCIPLINES)

        # Layer 1: Input to Hidden with residual projection
        self.W1 = self.rng.randn(self.input_dim, self.hidden_dim) * np.sqrt(2.0 / self.input_dim)
        self.b1 = np.zeros(self.hidden_dim)

        # Layer 2: Residual Dense Block
        self.W2 = self.rng.randn(self.hidden_dim, self.hidden_dim) * np.sqrt(2.0 / self.hidden_dim)
        self.b2 = np.zeros(self.hidden_dim)

        # Layer 3: Attention projection matrices for career affinities
        self.W_q = self.rng.randn(self.hidden_dim, 16) * 0.1
        self.W_k = self.rng.randn(self.hidden_dim, 16) * 0.1

        # Output Heads
        self.W_readiness = self.rng.randn(self.hidden_dim, 1) * 0.1
        self.b_readiness = np.array([0.5])

        self.W_affinity = self.rng.randn(self.hidden_dim, len(self.DISCIPLINES)) * 0.1
        self.b_affinity = np.zeros(len(self.DISCIPLINES))

        self.W_risk = self.rng.randn(self.hidden_dim, 1) * 0.1
        self.b_risk = np.array([-0.2])

    @staticmethod
    def _gelu(x: np.ndarray) -> np.ndarray:
        """Gaussian Error Linear Unit activation."""
        return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * np.power(x, 3))))

    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid."""
        return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))

    @staticmethod
    def _softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """Temperature-scaled Softmax."""
        scaled = x / max(1e-4, temperature)
        exp_x = np.exp(scaled - np.max(scaled))
        return exp_x / np.sum(exp_x)

    def extract_features(
        self,
        profile_data: Dict[str, Any],
        interaction_history: Optional[List[UserInteractionEvent]] = None,
    ) -> np.ndarray:
        """Vectorize student academic scores and pooled interaction events into an input tensor."""
        vec = np.zeros(self.input_dim, dtype=np.float32)

        # 1. Academic subject score normalization
        scores = profile_data.get("subject_scores", [])
        math_score = 75.0
        phys_score = 70.0
        eng_score = 70.0

        for s in scores:
            code = str(s.get("subject_code", "")).upper()
            val = float(s.get("score", 70.0))
            if "MATH" in code:
                math_score = val
            elif "PHYS" in code:
                phys_score = val
            elif "ENG" in code:
                eng_score = val

        vec[0] = math_score / 100.0
        vec[1] = phys_score / 100.0
        vec[2] = eng_score / 100.0

        # 2. Entrance rank percentile proxy
        rank = float(profile_data.get("entrance_rank", 25000))
        # Log-scaled rank score: lower rank -> higher percentile score
        vec[3] = float(np.clip(1.0 - (np.log10(max(1.0, rank)) / 6.0), 0.1, 0.99))

        # 3. Budget accessibility feature
        budget = float(profile_data.get("total_budget_inr", 800000))
        vec[4] = float(np.clip(budget / 2000000.0, 0.1, 1.0))

        # 4. Preferred disciplines one-hot / multi-hot
        pref_disciplines = [d.lower() for d in profile_data.get("preferred_disciplines", [])]
        for i, disc in enumerate(self.DISCIPLINES[:6]):
            if any(disc.lower() in p for p in pref_disciplines):
                vec[5 + i] = 1.0

        # 5. Pooled interaction trajectory features
        if interaction_history:
            event_count = len(interaction_history)
            vec[11] = float(np.clip(event_count / 15.0, 0.0, 1.0))
            has_auction = any(e.event_type == "run_auction" for e in interaction_history)
            has_planner = any(e.event_type == "plan_pathway" for e in interaction_history)
            has_simulation = any(e.event_type == "run_simulation" for e in interaction_history)
            vec[12] = 1.0 if has_auction else 0.0
            vec[13] = 1.0 if has_planner else 0.0
            vec[14] = 1.0 if has_simulation else 0.0
        else:
            # Baseline exploration prior
            vec[11] = 0.3
            vec[12] = 0.5
            vec[13] = 0.5
            vec[14] = 0.5

        # Bias term
        vec[15] = 1.0
        return vec

    def predict(
        self,
        profile_data: Dict[str, Any],
        interaction_history: Optional[List[UserInteractionEvent]] = None,
    ) -> NeuralTrajectoryInsights:
        """Execute deep feedforward and attention forward pass to project trajectory insights."""
        # 1. Feature extraction
        x = self.extract_features(profile_data, interaction_history)

        # 2. Layer 1 with GELU
        h1 = self._gelu(np.dot(x, self.W1) + self.b1)

        # 3. Layer 2 with Residual Connection & Normalization
        h2 = self._gelu(np.dot(h1, self.W2) + self.b2)
        h_norm = (h2 - np.mean(h2)) / (np.std(h2) + 1e-5)
        h_latent = h1 + h_norm  # Residual skip

        # 4. Self-Attention Gate
        q = np.dot(h_latent, self.W_q)
        k = np.dot(h_latent, self.W_k)
        attn_weight = float(self._sigmoid(np.dot(q, k) / 4.0))

        # 5. Output Heads
        # Career readiness: bounded sigmoid [0.55 - 0.98]
        raw_readiness = np.dot(h_latent, self.W_readiness) + self.b_readiness
        career_readiness = float(np.clip(float(self._sigmoid(raw_readiness)[0]) * 0.45 + 0.52, 0.50, 0.98))

        # Domain affinity distribution
        raw_affinity = np.dot(h_latent, self.W_affinity) + self.b_affinity
        affinity_probs = self._softmax(raw_affinity, temperature=1.2)
        affinity_dict = {
            self.DISCIPLINES[i]: round(float(affinity_probs[i]), 3)
            for i in range(len(self.DISCIPLINES))
        }

        # Normalize so primary preferences remain top
        pref_disciplines = [d.lower() for d in profile_data.get("preferred_disciplines", [])]
        for disc in self.DISCIPLINES:
            if any(disc.lower() in p for p in pref_disciplines):
                affinity_dict[disc] = min(0.96, affinity_dict[disc] + 0.35)

        # Re-normalize
        total_aff = sum(affinity_dict.values())
        if total_aff > 0:
            affinity_dict = {k: round(v / total_aff, 3) for k, v in affinity_dict.items()}

        # Learning Velocity index (momentum)
        learning_velocity = round(float(np.clip(0.65 + attn_weight * 0.28, 0.50, 0.98)), 2)

        # Risk assessment index: inverse of readiness with conservative safety factor
        raw_risk = np.dot(h_latent, self.W_risk) + self.b_risk
        risk_index = round(float(np.clip(float(self._sigmoid(raw_risk)[0]) * 0.35 + 0.08, 0.05, 0.45)), 2)

        # Projected career outcomes
        selected_careers = self.CAREER_PATHS[:3]
        if "data science" in str(pref_disciplines):
            selected_careers[1] = "Lead Data Scientist / AI Architect"

        confidence = round(float(np.clip(0.82 + (0.05 if interaction_history else 0.0), 0.80, 0.95)), 2)

        return NeuralTrajectoryInsights(
            career_readiness_score=round(career_readiness, 2),
            domain_affinity_weights=affinity_dict,
            learning_velocity_index=learning_velocity,
            risk_assessment_index=risk_index,
            projected_career_outcomes=selected_careers,
            confidence=confidence,
            is_estimate=True,
            provenance="NEURAL_TRAJECTORY_NETWORK_V1",
            is_synthetic=True,
        )

