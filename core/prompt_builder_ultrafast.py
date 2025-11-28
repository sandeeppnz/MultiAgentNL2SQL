# core/prompt_builder_ultrafast.py

class UltraFastPromptBuilder:

    def build(self, question: str, context: dict) -> str:
        tables = context.get("tables", [])
        cols = context.get("columns", {})
        joins = context.get("joins", "")

        return f"""
Generate valid SQL Server (T-SQL) ONLY.

Question:
{question}

Tables:
{', '.join(tables)}

Columns:
{'; '.join(f"{t}: {', '.join(c)}" for t, c in cols.items())}

Joins:
{joins}

Rules:
- Use only listed tables/columns.
- Strict FK→PK join correctness.
- T-SQL only.
- No invented tables or columns.
- Always use explicit JOIN ... ON.

Return ONLY SQL.
""".strip()
