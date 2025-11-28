# core/confidence/validator_confidence.py

from agents.validator_agents import (
    CheapOpenAIVerifierAgent,
    LocalSLMValidatorAgent,
    StructuralIntentValidator
)

import asyncio


def clamp(v):
    """Clamp confidence score to 0–1."""
    try:
        f = float(v)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, f))


class ValidatorConfidenceAgent:
    """
    Aggregates validator confidence from:
      - Cheap OpenAI validator
      - Local SLM validator
      - Structural rule-based validator

    Adds:
      - exception safety
      - normalization
      - weighted ensemble
      - fallback heuristics
    """

    def __init__(self):
        self.openai = CheapOpenAIVerifierAgent()
        self.slm = LocalSLMValidatorAgent()
        self.struct = StructuralIntentValidator()

    async def score(self, question: str, sql: str) -> float:

        # -------------------------------------------------------
        # 1. Run all validators safely
        # -------------------------------------------------------
        try:
            v1 = await self.openai.validate(question, sql)
            s1 = clamp(v1.get("score", 0.0))
        except Exception:
            s1 = 0.0

        try:
            v2 = await self.slm.validate(question, sql)
            s2 = clamp(v2.get("score", 0.0))
        except Exception:
            s2 = 0.0

        try:
            v3 = await self.struct.validate(question, sql)
            s3 = clamp(v3.get("score", 0.0))
        except Exception:
            s3 = 0.0

        # -------------------------------------------------------
        # 2. Weighted ensemble
        # -------------------------------------------------------
        score = (
            0.45 * s1 +   # OpenAI → highest precision
            0.30 * s2 +   # SLM → partial semantic validation
            0.25 * s3     # structural → essential rules
        )

        # -------------------------------------------------------
        # 3. Fallback: ensure minimum semantic structure floor
        # -------------------------------------------------------
        sql_l = sql.lower()
        if "select" in sql_l and "from" in sql_l:
            score = max(score, 0.15)

        if " join " in sql_l:
            score = max(score, 0.20)

        return clamp(score)
