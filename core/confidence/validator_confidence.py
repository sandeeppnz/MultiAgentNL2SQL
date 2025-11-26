# core/confidence/validator_confidence.py

from agents.validator_agents import (
    CheapOpenAIVerifierAgent,
    LocalSLMValidatorAgent,
    StructuralIntentValidator
)

class ValidatorConfidenceAgent:
    """
    Runs each validator and aggregates their scores.
    Aggregates signals from ALL validators (struct, semantic, slm, openai).
    """

    def __init__(self):
        self.openai = CheapOpenAIVerifierAgent()
        self.slm = LocalSLMValidatorAgent()
        self.struct = StructuralIntentValidator()

    async def score(self, question: str, sql: str) -> float:
        s1 = await self.openai.validate(question, sql)
        s2 = await self.slm.validate(question, sql)
        s3 = await self.struct.validate(question, sql)

        score = (s1["score"] + s2["score"] + s3["score"]) / 3
        return float(score)
