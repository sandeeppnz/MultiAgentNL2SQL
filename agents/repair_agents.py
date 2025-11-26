"""
SQL Repair Agents (R1–R7)
Each agent attempts a different style of repair on invalid SQL.
All agents inherit from BaseRepairAgent.
"""

from agents.base import BaseRepairAgent
from llm.llm_manager import LLMManager

llm = LLMManager()


# ------------------------------------------------------------
# R1 — Grammar Fix Agent
# ------------------------------------------------------------

class GrammarFixAgent(BaseRepairAgent):
    """
    Fixes SQL syntax, missing commas, misplaced keywords,
    invalid SELECT/FROM patterns, etc.
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        prompt = f"""
You are a SQL syntax repair assistant.

Fix ONLY syntax issues in the following SQL:
{sql}

Do NOT change table names.
Do NOT change column names.
Do NOT add new joins.

Return ONLY repaired SQL.
"""
        return await llm.ollama.acomplete(prompt)


# ------------------------------------------------------------
# R2 — Join Repair Agent
# ------------------------------------------------------------

class JoinRepairAgent(BaseRepairAgent):
    """
    Adds missing JOINs using schema information.
    Ensures fact/dim relationships are properly connected.
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        schema_text = diagnostics.get("schema_text", "")

        prompt = f"""
You are a SQL join-fixing expert.

The following SQL has missing or incorrect JOINs:
{sql}

Schema:
{schema_text}

Fix JOIN issues:
- Add missing JOIN ... ON
- Correct join keys
- Do NOT remove existing tables

Return ONLY corrected SQL.
"""
        return await llm.ollama.acomplete(prompt)


# ------------------------------------------------------------
# R3 — Column Fix Agent
# ------------------------------------------------------------

class ColumnFixAgent(BaseRepairAgent):
    """
    Fixes column name mismatches.
    Replaces invalid columns with correct ones from schema.
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        available_cols = diagnostics.get("columns", [])

        prompt = f"""
Fix column names in this SQL:
{sql}

Available columns:
{available_cols}

Rules:
- Replace invalid columns with closest valid ones.
- Do NOT remove tables.
- Do NOT change SQL logic.

Return ONLY SQL.
"""
        return await llm.ollama.acomplete(prompt)


# ------------------------------------------------------------
# R4 — GroupBy Repair Agent
# ------------------------------------------------------------

class GroupByRepairAgent(BaseRepairAgent):
    """
    Ensures GROUP BY is correct:
    - If aggregate functions exist, GROUP BY matching columns must exist.
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        prompt = f"""
The following SQL has GROUP BY issues:
{sql}

Fix GROUP BY:
- Include all non-aggregated columns.
- Do NOT remove aggregates.
- Do NOT change table structure.

Return ONLY corrected SQL.
"""
        return await llm.ollama.acomplete(prompt)


# ------------------------------------------------------------
# R5 — Dim Completion Agent
# ------------------------------------------------------------

class DimCompletionAgent(BaseRepairAgent):
    """
    Adds missing dimension tables based on:
    - schema graph
    - fact table relationships
    - column usage
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        schema_text = diagnostics.get("schema_text", "")

        prompt = f"""
The following SQL is missing required dimension tables:
{sql}

Use schema to add missing JOINs to dimension tables:
{schema_text}

Rules:
- Do NOT remove existing tables.
- Only add required dimension tables.
- Ensure join keys are correct.

Return ONLY SQL.
"""
        return await llm.ollama.acomplete(prompt)


# ------------------------------------------------------------
# R6 — AST Canonical Repair Agent
# ------------------------------------------------------------

class ASTCanonicalRepairAgent(BaseRepairAgent):
    """
    Rewrites SQL into canonical AST format:
    - normalized SELECT
    - explicit JOINs
    - consistent aliases
    - stable ordering
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        prompt = f"""
Rewrite the SQL below into canonical SQL format
while keeping identical logic:

{sql}

Rules:
- Use explicit JOIN ... ON
- Use consistent table aliases (a, b, c)
- Fully qualify columns
- No commentary

Return ONLY canonical SQL.
"""
        return await llm.ollama.acomplete(prompt)


# ------------------------------------------------------------
# R7 — Semantic Repair Agent
# ------------------------------------------------------------

class SemanticRepairAgent(BaseRepairAgent):
    """
    Ensures SQL semantically matches the question.
    Fixes missing filters, wrong grain, incorrect aggregations.
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        question = diagnostics.get("question", "")

        prompt = f"""
The SQL below does NOT correctly answer the question:

Question:
{question}

SQL:
{sql}

Fix the SQL so that it answers the question exactly.
Do NOT change schema.
Do NOT add hallucinated columns.

Return ONLY SQL.
"""
        return await llm.ollama.acomplete(prompt)



# ------------------------------------------------------------
# R8 — General OpenAI Repair Agent
# ------------------------------------------------------------

class OpenAIGeneralRepairAgent(BaseRepairAgent):
    """
    OpenAI mini model general repair.
    Capable of deeper reasoning than SLMs.
    Handles:
      - missing columns
      - missing filters
      - incorrect aggregations
      - subtle logic fixes
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        question = diagnostics.get("question", "")
        schema_text = diagnostics.get("schema_text", "")

        prompt = f"""
The following SQL contains issues and does not fully answer the question.

Question:
{question}

SQL:
{sql}

Schema:
{schema_text}

Fix ALL issues:
- syntax
- missing columns
- incorrect joins
- missing filters
- wrong aggregation/grain
- wrong fact table

Return ONLY the repaired SQL.
"""

        return await llm.openai.acomplete(prompt, temperature=0)


# ------------------------------------------------------------
# R9 — OpenAI Join Reasoning Repair Agent
# ------------------------------------------------------------

class OpenAIJoinRepairAgent(BaseRepairAgent):
    """
    Uses GPT-4o-mini or GPT-4.1-mini to deeply reason about join paths.
    Picks correct dimension tables and FK relationships.
    deeper reasoning
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        schema_text = diagnostics.get("schema_text", "")

        prompt = f"""
The SQL below has incorrect or missing JOINs:

SQL:
{sql}

Fix JOINs using the schema below:
{schema_text}

Rules:
- Add missing join tables.
- Use correct join keys.
- Do not remove necessary joins.
- Maintain SQL Server syntax.

Return ONLY corrected SQL.
"""

        return await llm.openai.acomplete(prompt, temperature=0)


# ------------------------------------------------------------
# R10 — OpenAI Semantic Repair Agent
# ------------------------------------------------------------

class OpenAISemanticRepairAgent(BaseRepairAgent):
    """
    High-level semantic repair.
    Ensures SQL exactly answers the question's intent.
    high-level reasoning
    """

    async def repair(self, sql: str, diagnostics: dict) -> str:
        question = diagnostics.get("question", "")

        prompt = f"""
The SQL below does not correctly answer the question.

Question:
{question}

SQL:
{sql}

Fix the SQL so it fully and precisely answers the question.
Do NOT change table or column names unless needed.
Do NOT hallucinate new tables.

Return ONLY repaired SQL.
"""

        return await llm.openai.acomplete(prompt, temperature=0)
