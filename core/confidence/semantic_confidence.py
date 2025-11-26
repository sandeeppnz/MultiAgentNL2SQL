# core/confidence/semantic_confidence.py

from agents.validator_agents import FusionValidatorAgent

class SemanticConfidenceAgent:
    """
    Uses the FusionValidatorAgent to get semantic score 0–1.
    Uses validator_agents.py (V1–V4).
    """

    def __init__(self):
        self.validator = FusionValidatorAgent()

    async def score(self, question: str, sql: str) -> float:
        result = await self.validator.validate(question, sql)
        return float(result.get("score", 0.0))
