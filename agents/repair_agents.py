"""
SQL Repair Agents (R1–R10)
All repair agents now use the centralized PromptBuilder.

This ensures:
 - unified guardrails
 - consistent schema context
 - join correctness
 - fact/dimension awareness
 - no hallucination of tables/columns
"""

from agents.base import BaseRepairAgent
from core.prompt_builder import PromptBuilder
from llm.llm_manager import LLMManager

llm = LLMManager()
builder = PromptBuilder()


# ============================================================
# HELPER — Build unified repair prompt
# ============================================================

def build_repair_prompt(sql: str, diagnostics: dict, instruction: str) -> str:
    """
    Wraps any repair instruction inside the unified schema-aware prompt.
    This ensures:
        - correct schema context
        - correct join paths
        - guardrails
        - consistent formatting
    """

    question = diagnostics.get("question", "")
    schema_text = diagnostics.get("schema_text", "")
    summary = diagnostics.get("summary", "")
    join_paths = diagnostics.get("join_paths", "")

    # Build a minimal context for repair
    context = {
        "tables": diagnostics.get("tables", []),
        "columns": diagnostics.get("columns", {}),
        "role_map": diagnostics.get("roles", {}),
        "schema_text": schema_text,
        "summary": summary,
        "join_paths": join_paths,
    }

    # Inject repair-specific instruction
    base_prompt = builder.build(question, context, mode="canonical")

    return f"""
{base_prompt}

# ========================
# SQL TO REPAIR
# ========================
{sql}

# ========================
# REPAIR INSTRUCTION
# ========================
{instruction}

Return ONLY the corrected SQL. Do not explain.
""".strip()


# ============================================================
# R1 — Grammar Fix Agent
# ============================================================

class GrammarFixAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        instruction = """
Fix ONLY SQL syntax errors:
 - missing commas
 - unmatched parentheses
 - invalid SELECT/FROM/WHERE structure
 - malformed JOIN clauses

Do NOT change table names, column names, or add/remove joins.
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.ollama.acomplete(prompt)


# ============================================================
# R2 — Join Repair Agent
# ============================================================

class JoinRepairAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        instruction = """
Fix incorrect or missing JOINs using the schema.
Rules:
 - Add missing JOIN ... ON clauses
 - Use ONLY FK → PK join paths from schema
 - Do NOT remove existing tables
 - Ensure all alias references are valid
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.ollama.acomplete(prompt)


# ============================================================
# R3 — Column Fix Agent
# ============================================================

class ColumnFixAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        instruction = """
Fix invalid or misspelled column names.
Rules:
 - Replace only incorrect columns with valid ones from schema
 - Do NOT hallucinate new columns
 - Preserve the SQL logic
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.ollama.acomplete(prompt)


# ============================================================
# R4 — GroupBy Repair Agent
# ============================================================

class GroupByRepairAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        instruction = """
Fix GROUP BY usage:
 - Include all non-aggregated columns in SELECT
 - Do NOT remove aggregates
 - Maintain exact table aliases and logic
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.ollama.acomplete(prompt)


# ============================================================
# R5 — Dim Completion Agent
# ============================================================

class DimCompletionAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        instruction = """
Add missing dimension tables based on schema graph.
Rules:
 - Insert missing FK → PK joins
 - Do NOT remove existing tables
 - Use correct join keys from schema
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.ollama.acomplete(prompt)


# ============================================================
# R6 — AST Canonical Repair Agent
# ============================================================

class ASTCanonicalRepairAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        instruction = """
Rewrite SQL into canonical SQL Server format WITHOUT altering logic.
Rules:
 - Explicit JOIN ... ON only
 - Use consistent short aliases (a, b, c)
 - Fully qualify columns (alias.column)
 - No comments, no explanations
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.ollama.acomplete(prompt)


# ============================================================
# R7 — Semantic Repair Agent
# ============================================================

class SemanticRepairAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        question = diagnostics.get("question", "")
        instruction = f"""
The SQL does NOT correctly answer the question:

Question:
{question}

Fix the SQL so that the answer matches the intent EXACTLY.
Rules:
 - Use ONLY valid tables and columns
 - No hallucinations
 - No missing filters
 - No missing joins
 - No incorrect grain or aggregation
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.ollama.acomplete(prompt)


# ============================================================
# R8 — OpenAI General Repair Agent
# ============================================================

class OpenAIGeneralRepairAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        question = diagnostics.get("question", "")
        instruction = f"""
Fix ALL issues in SQL:
 - syntax errors
 - incorrect columns
 - incorrect joins
 - missing filters
 - wrong aggregations
 - wrong fact/dimension tables

Question:
{question}
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.openai.acomplete(prompt, temperature=0)


# ============================================================
# R9 — OpenAI Join Reasoning Repair Agent
# ============================================================

class OpenAIJoinRepairAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        instruction = """
Fix JOIN logic using schema join paths.
Rules:
 - Add missing joins
 - Repair incorrect join keys
 - Preserve SQL Server syntax
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.openai.acomplete(prompt, temperature=0)


# ============================================================
# R10 — OpenAI Semantic Repair Agent
# ============================================================

class OpenAISemanticRepairAgent(BaseRepairAgent):
    async def repair(self, sql: str, diagnostics: dict) -> str:
        question = diagnostics.get("question", "")
        instruction = f"""
Fix SQL to correctly answer the question.

Question:
{question}

Rules:
 - No hallucinated tables or columns
 - Use correct join keys
 - Ensure correct aggregation and grain
 - Maintain strict schema correctness
"""
        prompt = build_repair_prompt(sql, diagnostics, instruction)
        return await llm.openai.acomplete(prompt, temperature=0)
