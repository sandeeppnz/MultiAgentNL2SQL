"""
SQL Generation Agents (G1–G5)
Each agent uses a different prompting strategy to produce SQL.
All inherit from BaseGenerationAgent.
"""

from agents.base import BaseGenerationAgent
from llm.llm_manager import LLMManager

# Every generator will use the shared LLM Manager.
llm = LLMManager()


def format_schema_context(context: dict) -> str:
    schema_text = context.get("schema_text", "")
    join_paths = context.get("join_paths", "")
    columns = context.get("columns", {})
    roles = context.get("role_map", {})

    col_text = "\n".join(
        f"{tbl}: {', '.join(cols)}" for tbl, cols in columns.items()
    )

    role_text = "\n".join(
        f"{tbl}: {role}" for tbl, role in roles.items()
    )

    return f"""
=== TABLES ===
{context.get('tables')}

=== COLUMNS ===
{col_text}

=== ROLES (fact/dimension) ===
{role_text}

=== JOIN PATHS ===
{join_paths}

=== FULL SCHEMA ===
{schema_text}
"""


# ------------------------------------------------------------
# G1 — Deterministic Template Generator
# ------------------------------------------------------------

class DeterministicGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        schema_block = format_schema_context(context)

        prompt = f"""
You are a SQL Server expert.

Use ONLY the tables, columns, and JOIN relationships provided below.

{schema_block}

Instructions:
- DO NOT hallucinate any table or column.
- Always use valid join keys based on the JOIN PATHS section.
- Always alias tables.
- Ensure GROUP BY when aggregating.
- Use precise SQL Server syntax.

Question:
{question}

Return ONLY the SQL.
"""
        return await llm.openai.acomplete(prompt, temperature=0.0)



# ------------------------------------------------------------
# G2 — Soft Template Generator
# ------------------------------------------------------------

class SoftTemplateGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        schema_block = format_schema_context(context)

        prompt = f"""
Generate SQL for SQL Server using the schema below:

{schema_block}

Rules:
- Use correct join keys.
- Use only valid columns.
- You may decide the best aggregation based on the question.

Question:
{question}

Return ONLY SQL.
"""
        return await llm.openai.acomplete(prompt, temperature=0.2)



# ------------------------------------------------------------
# G3 — Join-Heavy Generator
# ------------------------------------------------------------

class JoinHeavyGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        schema_block = format_schema_context(context)

        prompt = f"""
You specialize in JOIN reasoning.

Use the schema and join paths below:

{schema_block}

Rules:
- ALWAYS join fact tables to dimension tables based on FK→PK mapping.
- ALL joins MUST use exact key names from JOIN PATHS.
- Fully qualify all columns using aliases.

Question:
{question}

Return ONLY SQL.
"""
        return await llm.openai.acomplete(prompt, temperature=0.0)



# ------------------------------------------------------------
# G4 — Minimal Prompt Generator
# ------------------------------------------------------------

class MinimalGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        schema_block = format_schema_context(context)

        prompt = f"""
SQL Server only.
Tables and columns:
{schema_block}

Question:
{question}

SQL:
"""
        return await llm.openai.acomplete(prompt, temperature=0.1)



# ------------------------------------------------------------
# G5 — Canonical Style Generator
# ------------------------------------------------------------

class CanonicalGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        schema_block = format_schema_context(context)

        prompt = f"""
Generate CANONICAL SQL.

Schema:
{schema_block}

Rules:
- Alias each table: a, b, c, d...
- Use explicit JOIN ... ON with correct join keys.
- Put each SELECT column on its own line.
- Fully qualify all columns.

Question:
{question}

Return ONLY canonical SQL.
"""
        return await llm.openai.acomplete(prompt, temperature=0.0)



# ------------------------------------------------------------
# G6 — Local Minimal SLM Generator
# ------------------------------------------------------------

class LocalMinimalSLMGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        schema_block = format_schema_context(context)

        prompt = f"""
Write valid SQL Server code.

Schema:
{schema_block}

Question:
{question}

SQL:
"""
        return await llm.ollama.acomplete(prompt)



# ------------------------------------------------------------
# G7 — Local Canonical SLM Generator
# ------------------------------------------------------------

class LocalCanonicalSLMGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        schema_block = format_schema_context(context)

        prompt = f"""
Rewrite SQL in canonical SQL Server format.

Schema:
{schema_block}

Rules:
- Alias all tables
- Use explicit JOIN ... ON
- Use only valid columns
- No hallucination allowed

Question:
{question}

Return ONLY SQL.
"""
        return await llm.ollama.acomplete(prompt)
