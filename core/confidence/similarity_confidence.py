# core/confidence/similarity_confidence.py

import numpy as np
import hashlib


def deterministic_embed(text: str, dim: int = 768):
    """
    Deterministic fake embedding until a real embedding model is added.
    Converts text → SHA-256 hash → numeric vector.
    Ensures stable, deterministic similarity scores.
    """
    if not text:
        text = ""

    # Hash input text
    digest = hashlib.sha256(text.encode("utf-8")).digest()

    # Expand hash into vector
    repeated = (digest * (dim // len(digest) + 1))[:dim]
    arr = np.frombuffer(repeated, dtype=np.uint8).astype(np.float32)

    # Normalize vector
    norm = np.linalg.norm(arr)
    return arr / (norm + 1e-8)


def clamp(v):
    """Ensure similarity ∈ [0, 1]."""
    return max(0.0, min(1.0, float(v)))


class SimilarityConfidenceAgent:
    """
    Computes embedding similarity between:
      - generated SQL
      - reference SQL (gold or canonical)
    
    Clean behavior:
      - if no reference SQL is provided → returns 0.0 (disabled)
      - uses deterministic embeddings (stable)
      - clamps to [0–1]
    """

    def score(self, model_sql: str, reference_sql: str = "") -> float:
        # -----------------------------------------------------
        # 1. No reference → similarity should not contribute
        # -----------------------------------------------------
        if not reference_sql or reference_sql.strip() == "":
            return 0.0   # allow fusion agent to ignore similarity

        # -----------------------------------------------------
        # 2. Deterministic embeddings
        # -----------------------------------------------------
        e1 = deterministic_embed(model_sql)
        e2 = deterministic_embed(reference_sql)

        # cosine sim: [-1, 1]
        sim = float(np.dot(e1, e2))

        # convert to [0,1]
        norm_sim = (sim + 1.0) / 2.0

        return clamp(norm_sim)
