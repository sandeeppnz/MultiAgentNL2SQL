# core/confidence/fusion_confidence.py

from core.confidence.structural_confidence import StructuralConfidenceAgent
from core.confidence.semantic_confidence import SemanticConfidenceAgent
from core.confidence.validator_confidence import ValidatorConfidenceAgent
from core.confidence.similarity_confidence import SimilarityConfidenceAgent


def clamp(v: float) -> float:
    """Ensure confidence scores remain between 0 and 1."""
    if v is None:
        return 0.0
    return max(0.0, min(1.0, float(v)))


class FusionConfidenceAgent:
    """
    Combines confidence signals:
      C1 — structural confidence (static rules)
      C2 — semantic LLM scoring
      C3 — validator confidence (fusion validator)
      C4 — similarity confidence (optional)
    """

    def __init__(self):
        self.struct = StructuralConfidenceAgent()
        self.semantic = SemanticConfidenceAgent()
        self.validator = ValidatorConfidenceAgent()
        self.similarity = SimilarityConfidenceAgent()

    async def score(self, question: str, sql: str, reference_sql: str = "") -> float:
        # -------------------------
        # C1 — structural
        # -------------------------
        s1 = clamp(self.struct.score(sql))

        # -------------------------
        # C2 — semantic
        # -------------------------
        s2_raw = await self.semantic.score(question, sql)
        s2 = clamp(s2_raw)

        # -------------------------
        # C3 — validator fusion
        # -------------------------
        s3_raw = await self.validator.score(question, sql)
        s3 = clamp(s3_raw)

        # -------------------------
        # C4 — embedding similarity
        # Skip if no reference SQL
        # -------------------------
        if reference_sql:
            s4 = clamp(self.similarity.score(sql, reference_sql))
        else:
            s4 = 0.0

        # -------------------------
        # Final weighted ensemble
        # -------------------------
        fused = (
            0.25 * s1 +
            0.35 * s2 +
            0.30 * s3 +
            0.10 * s4
        )

        return clamp(fused)