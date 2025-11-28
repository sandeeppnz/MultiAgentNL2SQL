# core/confidence/semantic_confidence.py

from agents.validator_agents import FusionValidatorAgent
import re

def clamp(v):
    """Clamp any score into 0–1 range."""
    try:
        val = float(v)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, val))


class SemanticConfidenceAgent:
    """
    Uses FusionValidatorAgent to obtain semantic alignment score.
    Adds:
      - normalization
      - exception safety
      - fallback semantic heuristic
    """

    def __init__(self):
        self.validator = FusionValidatorAgent()

    async def score(self, question: str, sql: str) -> float:
        # -----------------------------------------------------------
        # 1. Run validator safely
        # -----------------------------------------------------------
        try:
            result = await self.validator.validate(question, sql)
            raw_score = result.get("score", 0.0)

        except Exception:
            raw_score = 0.0  # validator failure

        s = clamp(raw_score)

        # -----------------------------------------------------------
        # 2. Fallback semantic heuristic to avoid hard drops
        # -----------------------------------------------------------
        # Basic SQL structure → boost confidence slightly
        sql_l = sql.lower()

        if re.search(r"\bselect\b", sql_l) and re.search(r"\bfrom\b", sql_l):
            s = max(s, 0.15)

        # SQL contains joins → more likely meaningful
        if " join " in sql_l:
            s = max(s, 0.25)

        # Danger patterns → reduce
        if "??" in sql or "undefined" in sql_l:
            s = min(s, 0.2)

        return clamp(s)
