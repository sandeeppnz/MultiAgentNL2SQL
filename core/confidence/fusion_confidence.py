# core/confidence/fusion_confidence.py

from core.confidence.structural_confidence import StructuralConfidenceAgent
from core.confidence.semantic_confidence import SemanticConfidenceAgent
from core.confidence.validator_confidence import ValidatorConfidenceAgent
from core.confidence.similarity_confidence import SimilarityConfidenceAgent

class FusionConfidenceAgent:
    """
    Combines multiple confidence signals into one:
    - structural
    - semantic
    - validator fusion
    - embedding similarity (optional)

    Combine C1–C4 with weights:
    """

    def __init__(self):
        self.struct = StructuralConfidenceAgent()
        self.semantic = SemanticConfidenceAgent()
        self.validator = ValidatorConfidenceAgent()
        self.similarity = SimilarityConfidenceAgent()

    async def score(self, question: str, sql: str, reference_sql: str = "") -> float:
        s1 = self.struct.score(sql)
        s2 = await self.semantic.score(question, sql)
        s3 = await self.validator.score(question, sql)
        s4 = self.similarity.score(sql, reference_sql)

        score = (
            0.25 * s1 +
            0.35 * s2 +
            0.30 * s3 +
            0.10 * s4
        )

        return float(score)
