"""
SQL Generation Agents (G1–G5)
Each agent uses a different prompting strategy to produce SQL.
All inherit from BaseGenerationAgent.
"""

from agents.base import BaseGenerationAgent
from llm.llm_manager import LLMManager

# Every generator will use the shared LLM Manager.
llm = LLMManager()


# ------------------------------------------------------------
# G1 — Deterministic Template Generator
# ------------------------------------------------------------

class DeterministicGenerator(BaseGenerationAgent):
    """
    Very strict SQL prompting.
    Minimal temperature, minimal creativity.
    Used as baseline generator.
    """

    async def generate(self, question: str, context: dict) -> str:
        prompt = f"""
You are a SQL expert. Generate ONLY valid SQL for Microsoft SQL Server.
Use strict structure. No commentary.

Tables available: {context.get('tables')}

Question: {question}

Rules:
- Always join fact tables to corresponding dimension tables using keys.
- Always include GROUP BY when aggregating.
- Never hallucinate column names.
- Never output explanations.

Return ONLY SQL.
"""
        return await llm.openai.acomplete(prompt, temperature=0.0)


# ------------------------------------------------------------
# G2 — Soft Template Generator
# ------------------------------------------------------------

class SoftTemplateGenerator(BaseGenerationAgent):
    """
    More flexible generator.
    Allows some creativity to solve ambiguous questions.
    """

    async def generate(self, question: str, context: dict) -> str:
        prompt = f"""
You are an expert SQL analyst.

Generate SQL for the given question and tables:
{context.get('tables')}

Be concise and correct, but flexible in interpretation.
Output ONLY SQL.

Question:
{question}
"""
        return await llm.openai.acomplete(prompt, temperature=0.2)


# ------------------------------------------------------------
# G3 — Join-Heavy Generator
# ------------------------------------------------------------

class JoinHeavyGenerator(BaseGenerationAgent):
    """
    Forces explicit JOIN reasoning using schema.
    This agent is crucial when questions involve relationships.
    """

    async def generate(self, question: str, context: dict) -> str:
        schema_text = context.get("schema_text", "")

        prompt = f"""
You are a SQL JOIN expert.

You MUST write correct joins based on schema:

{schema_text}

Instructions:
- Always join fact → dimensions.
- Use clear join conditions.
- Do NOT omit any required join.

Tables: {context.get('tables')}

Generate SQL for:
{question}

Return ONLY SQL.
"""
        return await llm.openai.acomplete(prompt, temperature=0.0)


# ------------------------------------------------------------
# G4 — Minimal Prompt Generator
# ------------------------------------------------------------

class MinimalGenerator(BaseGenerationAgent):
    """
    Minimal prompt, very short instructions.
    Helpful to produce alternative structures.
    """

    async def generate(self, question: str, context: dict) -> str:
        prompt = f"""
SQL only. SQL Server. Tables: {context.get('tables')}
Question: {question}
"""
        return await llm.openai.acomplete(prompt, temperature=0.1)


# ------------------------------------------------------------
# G5 — Canonical Style Generator
# ------------------------------------------------------------

class CanonicalGenerator(BaseGenerationAgent):
    """
    Produces SQL in canonical formatting:
    - explicit table aliases
    - consistent SELECT layout
    - sqlglot-friendly
    """

    async def generate(self, question: str, context: dict) -> str:
        prompt = f"""
Generate SQL in canonical formatting style.
Always:
- Use table aliases (f, d, p, c).
- Place SELECT columns on separate lines.
- Fully qualify columns.
- Use JOIN ... ON lines clearly.

Tables: {context.get('tables')}

Question:
{question}

Return ONLY SQL.
"""
        return await llm.openai.acomplete(prompt, temperature=0.0)


# ------------------------------------------------------------
# G6 — Local Minimal SLM Generator
# ------------------------------------------------------------

class LocalMinimalSLMGenerator(BaseGenerationAgent):
    """
    EXPERIMENTAL:
    Local SLM generation using Ollama.
    Minimal instruction prompt.
    Useful for cheap offline SQL alternatives.
    """

    async def generate(self, question: str, context: dict) -> str:
        prompt = f"""
Write SQL (SQL Server syntax).
Tables: {context.get('tables')}
Question: {question}

Return ONLY SQL.
"""
        return await llm.ollama.acomplete(prompt)


# ------------------------------------------------------------
# G7 — Local Canonical SLM Generator
# ------------------------------------------------------------

class LocalCanonicalSLMGenerator(BaseGenerationAgent):
    """
    EXPERIMENTAL:
    Canonical SQL generation using local SLM (LLaMA/Qwen).
    Produces stable, structured SQL with aliases.
    """

    async def generate(self, question: str, context: dict) -> str:
        prompt = f"""
Produce SQL in canonical format:
- include table aliases (a, b, c)
- use explicit JOIN ... ON
- break SELECT columns across lines
- avoid extra commentary

Tables available: {context.get('tables')}
Question: {question}

Return ONLY SQL.
"""
        return await llm.ollama.acomplete(prompt)
