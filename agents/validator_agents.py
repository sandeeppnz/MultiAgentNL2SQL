"""
Semantic SQL Validator Agents (V1–V4)
Evaluates whether SQL answers the natural language question.
"""

from agents.base import BaseValidatorAgent
from llm.llm_manager import LLMManager
from sqlglot import parse_one
import re

llm = LLMManager()

# ============================================================
# V1 — Cheap OpenAI Semantic Validator
# ============================================================

class CheapOpenAIVerifierAgent(BaseValidatorAgent):
    """
    Uses a cheap OpenAI model (e.g., gpt-4o-mini or gpt-4.1-mini)
    to determine whether SQL answers the question.
    """

    async def validate(self, question: str, sql: str) -> dict:
        prompt = f"""
You are a semantic SQL validator.

Question:
{question}

SQL:
{sql}

Task:
Evaluate if the SQL fully and correctly answers the question.

Respond ONLY in this JSON structure:
{{
  "valid": true/false,
  "score": 0.0 to 1.0,
  "reason": "..."
}}
"""

        result = await llm.openai.acomplete(prompt, temperature=0)

        # Fallback parsing (Option C scaffold = simple logic)
        is_valid = "true" in result.lower()
        score = 0.9 if is_valid else 0.2

        return {
            "valid": is_valid,
            "score": score,
            "reason": result
        }


# ============================================================
# V2 — Local SLM Validator (Ollama)
# ============================================================

class LocalSLMValidatorAgent(BaseValidatorAgent):
    """
    Local SLM semantic validation.
    Very fast, offline, cheap.
    """

    async def validate(self, question: str, sql: str) -> dict:
        prompt = f"""
Determine if this SQL answers the question.

Question:
{question}

SQL:
{sql}

Answer with: yes or no, and a short reason.
"""

        result = await llm.ollama.acomplete(prompt)
        is_yes = "yes" in result.lower()

        return {
            "valid": is_yes,
            "score": 0.7 if is_yes else 0.2,
            "reason": result
        }


# ============================================================
# V3 — Structural Intent Validator (Rule-Based)
# ============================================================

class StructuralIntentValidator(BaseValidatorAgent):
    """
    Deterministic rule-based validation.
    No LLM used.
    Checks:
    - missing WHERE for time range
    - missing GROUP BY when using aggregates
    - missing JOINs for referenced columns
    """

    async def validate(self, question: str, sql: str) -> dict:

        errors = []
        q = question.lower()
        s = sql.lower()

        # rule 1: if year mentioned → expect WHERE or JOIN DimDate
        if "year" in q and ("dimdate" not in s and "calendar" not in s):
            errors.append("Question refers to year but SQL not using DimDate.")

        # rule 2: aggregates without GROUP BY
        if re.search(r"(count|sum|avg|min|max)\(", s) and "group by" not in s:
            # Some questions want total only; we skip if no dimension selected
            if "total" not in q and "overall" not in q:
                errors.append("SQL uses aggregates without GROUP BY.")

        # rule 3: fact table check
        if "sales" in q and "fact" not in s:
            errors.append("Sales question should reference a fact table.")

        return {
            "valid": len(errors) == 0,
            "score": 1.0 if len(errors) == 0 else 0.1,
            "reason": "; ".join(errors) if errors else "OK"
        }


# ============================================================
# V4 — Fusion Semantic Validator
# ============================================================

class FusionValidatorAgent(BaseValidatorAgent):
    """
    Combines:
      - Cheap OpenAI semantic reasoning
      - Local SLM semantic reasoning
      - Structural rule checks

    Produces a final, robust semantic score.
    """

    def __init__(self):
        self.openai = CheapOpenAIVerifierAgent()
        self.slm = LocalSLMValidatorAgent()
        self.struct = StructuralIntentValidator()

    async def validate(self, question: str, sql: str) -> dict:
        v1 = await self.openai.validate(question, sql)
        v2 = await self.slm.validate(question, sql)
        v3 = await self.struct.validate(question, sql)

        # Weighted fusion
        score = (
            0.50 * v1["score"] +
            0.30 * v2["score"] +
            0.20 * v3["score"]
        )

        valid = score > 0.55

        reason = f"OpenAI: {v1['reason']}\nSLM: {v2['reason']}\nStruct: {v3['reason']}"

        return {
            "valid": valid,
            "score": float(score),
            "reason": reason
        }
