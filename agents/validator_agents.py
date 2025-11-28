"""
Semantic SQL Validator Agents (V1–V4)
Evaluates whether SQL answers the natural language question.
"""

import re
import json

from agents.base import BaseValidatorAgent
from llm.llm_manager import LLMManager
from core.prompt_builder import PromptBuilder

llm = LLMManager()
pb = PromptBuilder()


# ============================================================
# UTIL — SAFE JSON EXTRACTOR
# ============================================================

def safe_extract_json(text: str):
    """Attempts to extract JSON from an LLM response."""
    if not text or not isinstance(text, str):
        return None

    text = text.strip()

    # direct
    try:
        return json.loads(text)
    except Exception:
        pass

    # substring
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return None


# ============================================================
# V1 — Cheap OpenAI Semantic Validator  (with PromptBuilder)
# ============================================================

class CheapOpenAIVerifierAgent(BaseValidatorAgent):
    """
    Uses OpenAI mini models to validate SQL semantics.
    Now supports context-aware validation via PromptBuilder.
    """

    name = "V1-OpenAI-Semantic"

    async def validate(self, question: str, sql: str, context: dict | None = None) -> dict:

        schema_block = ""
        if context:
            # NEW — include light schema info
            schema_block = pb.build_validation_prompt(question, sql, context)

        prompt = f"""
You are a SQL semantic validator.

{schema_block}

Question:
{question}

SQL:
{sql}

Does the SQL fully and correctly answer the question?

Respond ONLY in this JSON format:
{{
  "valid": true/false,
  "score": 0.0 to 1.0,
  "reason": "..."
}}
"""

        # safe call
        try:
            result = await llm.openai.acomplete(prompt, temperature=0)
        except Exception as e:
            return {
                "valid": False,
                "score": 0.1,
                "reason": f"OpenAI exception: {e}"
            }

        if not result or not isinstance(result, str):
            return {
                "valid": False,
                "score": 0.1,
                "reason": "OpenAI returned invalid response"
            }

        # extract JSON
        parsed = safe_extract_json(result)
        if parsed:
            return {
                "valid": parsed.get("valid", False),
                "score": float(parsed.get("score", 0.1)),
                "reason": parsed.get("reason", result)
            }

        # fallback
        lowered = result.lower().strip()
        is_valid = lowered.startswith("true") or lowered.startswith("yes")

        return {
            "valid": is_valid,
            "score": 0.8 if is_valid else 0.2,
            "reason": "Fallback parse: " + result[:200]
        }


# ============================================================
# V2 — Local SLM Validator (no prompt builder)
# ============================================================

class LocalSLMValidatorAgent(BaseValidatorAgent):
    """
    Fast offline validator powered by local SLM (Ollama).
    """

    name = "V2-SLM-Semantic"

    async def validate(self, question: str, sql: str) -> dict:
        prompt = f"""
Does this SQL answer the question?

Question:
{question}

SQL:
{sql}

Respond only: yes or no, then a short explanation.
"""

        try:
            result = await llm.ollama.acomplete(prompt)
        except Exception as e:
            return {
                "valid": False,
                "score": 0.2,
                "reason": f"Ollama exception: {e}"
            }

        if not result or not isinstance(result, str):
            return {
                "valid": False,
                "score": 0.2,
                "reason": "Ollama returned invalid response"
            }

        is_yes = result.lower().strip().startswith("yes")

        return {
            "valid": is_yes,
            "score": 0.7 if is_yes else 0.2,
            "reason": result
        }


# ============================================================
# V3 — Structural Intent Validator (pure rules)
# ============================================================

class StructuralIntentValidator(BaseValidatorAgent):
    """
    Static rule-based validator:
      - ensures DimDate usage for date queries
      - ensures GROUP BY is present when needed
      - ensures fact tables appear for sales queries
    """

    name = "V3-RuleBased"

    async def validate(self, question: str, sql: str) -> dict:
        errors = []
        q = question.lower()
        s = sql.lower()

        # rule 1: date dimension required
        if "year" in q or "month" in q or "date" in q:
            if "dimdate" not in s and "calendar" not in s:
                errors.append("Missing DimDate join for date-based question.")

        # rule 2: aggregates vs group by
        if re.search(r"(count|sum|avg|min|max)\(", s) and "group by" not in s:
            if "total" not in q:
                errors.append("Aggregate used without GROUP BY for dimensional question.")

        # rule 3: fact table requirement
        if "sales" in q and "fact" not in s:
            errors.append("Sales question should reference Fact* table.")

        valid = (len(errors) == 0)
        score = 1.0 if valid else 0.1

        return {
            "valid": valid,
            "score": score,
            "reason": "; ".join(errors) if errors else "OK"
        }


# ============================================================
# V4 — Fusion Validator
# ============================================================

class FusionValidatorAgent(BaseValidatorAgent):
    """
    Combines:
      - V1 OpenAI semantic reasoning (context-aware)
      - V2 Local SLM semantic reasoning
      - V3 structural reasoning
    """

    name = "V4-Fusion"

    def __init__(self):
        self.openai = CheapOpenAIVerifierAgent()
        self.slm = LocalSLMValidatorAgent()
        self.struct = StructuralIntentValidator()

    async def validate(self, question: str, sql: str, context: dict | None = None) -> dict:
        v1 = await self.openai.validate(question, sql, context=context)
        v2 = await self.slm.validate(question, sql)
        v3 = await self.struct.validate(question, sql)

        score = (
            0.50 * v1["score"] +
            0.30 * v2["score"] +
            0.20 * v3["score"]
        )

        valid = score >= 0.55

        reason = (
            f"OpenAI: {v1['reason']}\n"
            f"SLM: {v2['reason']}\n"
            f"Struct: {v3['reason']}"
        )

        return {
            "valid": valid,
            "score": float(score),
            "reason": reason
        }
