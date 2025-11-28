# core/sql_generation/prompt_builder.py

"""
Centralized Prompt Builder for ALL SQL Generation Agents.

This module standardizes:
 - schema formatting
 - join-path reasoning
 - table/column summaries
 - fact/dimension roles
 - guardrails
 - prompt modes (canonical, compact, join_heavy)
 - injection of compressed context from TokenReducer

Every SQL generation agent should call:

    prompt = PromptBuilder().build(question, context, mode="canonical")

Then feed that prompt directly into LLM.
"""

from typing import Dict, List


class PromptBuilder:

    # ============================================================
    # MAIN ENTRY
    # ============================================================

    def build(self, question: str, context: dict, mode: str = "canonical") -> str:
        """
        Construct a fully schema-aware SQL generation prompt.
        Modes:
            - canonical  → verbose, safe, structured, best accuracy
            - compact    → minimal token usage
            - join_heavy → emphasise FK/PK correctness
        """

        tables = context.get("tables", [])
        columns = context.get("columns", {})
        roles = context.get("role_map", {})
        join_paths = context.get("join_paths", "")
        summary = context.get("summary", "")
        schema_text = context.get("schema_text", "")

        # ---- structured components ----
        table_block = self._format_tables(tables)
        column_block = self._format_columns(columns)
        role_block = self._format_roles(roles)
        join_block = self._format_join_paths(join_paths)
        schema_block = self._format_full_schema(schema_text)
        summary_block = self._format_summary(summary)

        # ---- guardrails ----
        guardrails = self._guardrails()

        # ---- Build mode-specific instructions ----
        mode_instructions = self._mode_instructions(mode)

        # ----------------------------------------------------------------
        # FINAL PROMPT (unified structure used by ALL generation agents)
        # ----------------------------------------------------------------
        prompt = f"""
You are an expert SQL Server T-SQL generator.
You must follow the schema and join rules EXACTLY.
Never hallucinate tables or columns. Never invent join keys.

# ========================
# QUESTION
# ========================
{question}

# ========================
# MODE
# ========================
{mode.upper()}

# ========================
# TABLES
# ========================
{table_block}

# ========================
# COLUMNS
# ========================
{column_block}

# ========================
# ROLES (Fact / Dimension)
# ========================
{role_block}

# ========================
# JOIN PATHS (Compressed)
# ========================
{join_block}

# ========================
# COMPRESSED SCHEMA SUMMARY
# ========================
{summary_block}

# ========================
# FULL SCHEMA (Compressed)
# ========================
{schema_block}

# ========================
# GENERATION RULES
# ========================
{guardrails}

# ========================
# MODE INSTRUCTIONS
# ========================
{mode_instructions}

Return ONLY the final SQL. No explanation. No commentary.
"""

        print(prompt)
        return prompt.strip()

    # ============================================================
    # BUILDING BLOCKS
    # ============================================================

    def _format_tables(self, tables: List[str]) -> str:
        if not tables:
            return "(No tables selected — provide best guess)"
        return "\n".join(f"- {t}" for t in tables)

    def _format_columns(self, columns: Dict[str, List[str]]) -> str:
        if not columns:
            return "(No columns)"

        return "\n".join(
            f"{tbl}: {', '.join(cols)}"
            for tbl, cols in columns.items()
        )

    def _format_roles(self, roles: Dict[str, str]) -> str:
        if not roles:
            return "(No roles detected)"

        return "\n".join(f"{tbl}: {role}" for tbl, role in roles.items())

    def _format_join_paths(self, join_paths: str) -> str:
        if not join_paths.strip():
            return "(No join paths available)"
        return join_paths

    def _format_full_schema(self, schema_text: str) -> str:
        if not schema_text.strip():
            return "(No schema)"
        return schema_text

    def _format_summary(self, summary: str) -> str:
        if not summary:
            return "(No LLM summary)"
        return summary

    # ============================================================
    # GUARDRAILS
    # ============================================================

    def _guardrails(self) -> str:
        return """
- Only use tables listed above.
- Only use columns listed under each table.
- DO NOT invent or hallucinate tables, columns, or join keys.
- ALWAYS use explicit JOIN ... ON.
- ALWAYS use correct FK → PK join conditions from JOIN PATHS.
- Use table aliases (a, b, c, ...).
- Use SQL Server (T-SQL) syntax only.
- If aggregation is used, include GROUP BY for all non-aggregated columns.
- Prefer canonical formatting with each SELECT column on a new line.
- Always reference DimDate for date filters.
- Never guess column names — use only provided columns.
"""

    # ============================================================
    # MODE-SPECIFIC INSTRUCTIONS
    # ============================================================

    def _mode_instructions(self, mode: str) -> str:
        mode = mode.lower().strip()

        if mode == "canonical":
            return """
Canonical SQL Mode:
- Use clean canonical formatting.
- SELECT columns each on their own line.
- Explicit JOIN chaining.
- Full qualification of columns (alias.column).
- Strict fact→dimension join correctness.
"""

        if mode == "compact":
            return """
Compact SQL Mode:
- Minimize tokens.
- No comments.
- Use short aliases.
- Use minimal whitespace.
- Keep SQL fully valid and correct.
"""

        if mode == "join_heavy":
            return """
Join-Heavy Mode:
- Prioritize correct FK/PK joins.
- Include ALL needed dimension joins.
- Do NOT simplify join chains.
- Always rely on JOIN PATHS.
"""

        # fallback (canonical)
        return """
Canonical SQL Mode (default):
- Clean formatting, explicit JOINs, strict correctness.
"""

