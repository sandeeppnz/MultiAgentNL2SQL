# core/confidence/similarity_confidence.py

import numpy as np

def fake_embed(text):
    """Placeholder until real embedding model is added."""
    return np.random.rand(768)

class SimilarityConfidenceAgent:
    """
    Computes embedding similarity between:
    - generated SQL
    - canonical schema-aligned SQL template (or gold SQL)


Later, this can use:

sentence-transformers

OpenAI embeddings

Ollama embeddings


    """

    def score(self, model_sql: str, reference_sql: str = "") -> float:
        if not reference_sql:
            return 0.5  # neutral

        e1 = fake_embed(model_sql)
        e2 = fake_embed(reference_sql)

        sim = float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2)))
        return (sim + 1) / 2  # normalize 0–1
