# core/prompt_builder.py

"""
Fast-Mode Prompt Builder
=========================

This version is optimized for SPEED:

 - minimal schema footprint
 - compressed join-paths
 - no verbose PK/FK dumps
 - no long schema blocks
 - unified formatting for:
      • generation prompts
      • validation prompts
      • repair prompts
 - all prompts < 2,000 tokens

Supports:
   build_sql_prompt(question, context, mode="canonical")
   build_validation_prompt(question, sql, context)
   build_repair_prompt(question, sql, diagnostics)
"""

from typing import Dict, List, Optional


class PromptBuilder:

    # ============================================================
    # PUBLIC ENTRY 1 — SQL GENERATION
    # ============================================================

    def build_sql_prompt(self, question: str, context: dict, mode: str = "canonical") -> str:
        """
        Fast-mode SQL generation prompt.
        Designed for OpenAI mini models and deterministic generators.
        """

        tables = context.get("tables", [])
        columns = context.get("columns", {})
        roles = context.get("role_map", {})
        join_paths = context.get("join_paths", "")

        return f"""
You are an expert SQL Server T-SQL generator.
You MUST follow the schema exactly.
Never hallucinate tables, columns, or join keys.

QUESTION:
{question}

MODE: {mode.upper()}

TABLES:
{self._fmt_tables(tables)}

COLUMNS (compressed):
{self._fmt_columns(columns)}

ROLES (Fact/Dim):
{self._fmt_roles(roles)}

JOIN PATHS:
{self._fmt_join_paths(join_paths)}

RULES:
{self._generation_rules(mode)}

Return ONLY the final SQL.
""".strip()


    # ============================================================
    # PUBLIC ENTRY 2 — VALIDATION PROMPT
    # ============================================================

    def build_validation_prompt(self, question: str, sql: str, context: dict) -> str:
        """
        Lightweight validation prompt.
        Used by CheapOpenAIVerifierAgent (V1).
        """

        tables = context.get("tables", [])
        join_paths = context.get("join_paths", "")

        return f"""
# SQL Semantic Validation Context (FAST)

Tables involved:
{self._fmt_tables(tables)}

Join paths:
{self._fmt_join_paths(join_paths)}

Validation Task:
Determine whether the SQL below fully answers the QUESTION.

QUESTION:
{question}

SQL:
{sql}

Respond ONLY with JSON:
{{
  "valid": true/false,
  "score": 0.0 to 1.0,
  "reason": "..."
}}
""".strip()


    # ============================================================
    # PUBLIC ENTRY 3 — REPAIR PROMPT
    # ============================================================

    def build_repair_prompt(self, question: str, sql: str, diagnostics: dict) -> str:
        """
        Fast-mode repair prompt (OpenAI).
        """

        schema_text = diagnostics.get("schema_text", "")
        # Keep schema light—ONLY include join paths or one-liners
        schema_short = self._shorten_schema(schema_text)

        return f"""
You are an expert SQL repair assistant.

QUESTION:
{question}

BROKEN SQL:
{sql}

SCHEMA (compressed):
{schema_short}

Fix the SQL so that:
- it is valid T-SQL
- uses correct tables and join paths
- answers the question EXACTLY
- no hallucinated columns
- no invented tables

Return ONLY the repaired SQL.
""".strip()


    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    def _fmt_tables(self, tables: List[str]) -> str:
        if not tables:
            return "(none)"
        return "\n".join(f"- {t}" for t in tables)

    def _fmt_columns(self, columns: Dict[str, List[str]]) -> str:
        if not columns:
            return "(none)"
        return "\n".join(f"{tbl}: {', '.join(cols)}" for tbl, cols in columns.items())

    def _fmt_roles(self, roles: Dict[str, str]) -> str:
        if not roles:
            return "(none)"
        return "\n".join(f"{tbl}: {role}" for tbl, role in roles.items())

    def _fmt_join_paths(self, jp: str) -> str:
        if not jp.strip():
            return "(none)"

        lines = [
            ln.strip()
            for ln in jp.split("\n")
            if ln.strip()
        ]

        # Flatten into compact, readable lines
        return "\n".join(lines[:12])  # hard cap

    def _shorten_schema(self, schema_text: str) -> str:
        """ Compress schema for repair prompts """
        if not schema_text:
            return "(none)"

        lines = schema_text.split("\n")

        # include only PK/FK and columns header lines
        out = []
        for ln in lines:
            ln = ln.strip()
            if "Columns" in ln or "PK" in ln or "FK" in ln:
                out.append(ln[:140] + (" ..." if len(ln) > 140 else ""))

        return "\n".join(out[:20])  # keep max 20 lines

    def _generation_rules(self, mode: str) -> str:
        mode = mode.lower()

        base_rules = """
- Use ONLY the listed tables/columns.
- No hallucinated names.
- ALWAYS use explicit JOIN ... ON.
- FK→PK joins must follow JOIN PATHS.
- Use table aliases: a, b, c...
- Include GROUP BY for all non-aggregated columns.
- Use valid SQL Server T-SQL syntax only.
"""

        if mode == "compact":
            return base_rules + """
- Minimize whitespace.
- Use short aliases.
- Keep SQL very compact.
"""

        if mode == "join_heavy":
            return base_rules + """
- Emphasize ALL required joins.
- Do NOT remove dimension joins.
- Fully chain FK→PK joins.
"""

        # Default = canonical
        return base_rules + """
- Clean canonical formatting.
- One SELECT column per line.
- Fully qualify: alias.column.
"""


