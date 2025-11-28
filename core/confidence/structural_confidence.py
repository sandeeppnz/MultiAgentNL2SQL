# core/confidence/structural_confidence.py

from sqlglot import parse_one
from sqlglot.expressions import Select, From, Join, Group, Having, Where
import re


def clamp(v):
    try:
        f = float(v)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, f))


class StructuralConfidenceAgent:
    """
    Scores SQL based on AST structure quality.

    Structural signals include:
      - valid parse (SQLGlot)
      - SELECT present
      - FROM present
      - JOIN clauses
      - GROUP BY usage
      - WHERE usage (when aggregates exist)
      - Aggregation consistency
    """

    def score(self, sql: str) -> float:

        # Empty or bad string
        if not sql or not isinstance(sql, str):
            return 0.0

        sql_l = sql.lower()

        # ---------------------------------------------
        # 1. Try AST parsing
        # ---------------------------------------------
        try:
            ast = parse_one(sql)
        except Exception:
            # fallback: basic SQL structure check
            basic = 0.0
            if "select" in sql_l:
                basic += 0.25
            if "from" in sql_l:
                basic += 0.25
            if " join " in sql_l:
                basic += 0.20
            if " group by " in sql_l:
                basic += 0.20
            return clamp(basic)

        score = 0.0

        # ---------------------------------------------
        # 2. Core AST components
        # ---------------------------------------------
        if ast.find(Select):
            score += 0.25

        if ast.find(From):
            score += 0.25

        if ast.find(Join):
            score += 0.20

        if ast.find(Group):
            score += 0.15

        # ---------------------------------------------
        # 3. Aggregation consistency
        # Detect SUM(), COUNT(), AVG(), MAX(), MIN()
        # ---------------------------------------------
        has_agg = bool(re.search(r"\b(sum|count|avg|min|max)\s*\(", sql_l))

        if has_agg:
            score += 0.05  # small bump for detecting aggregation

            # Must have GROUP BY OR no non-aggregated selected columns
            if not ast.find(Group):
                score *= 0.8  # penalty for missing group-by logic

        # ---------------------------------------------
        # 4. WHERE clause improves structural confidence
        # ---------------------------------------------
        if ast.find(Where):
            score += 0.05

        # ---------------------------------------------
        # 5. Penalize unfinished SQL patterns
        # ---------------------------------------------
        if sql_l.strip().endswith(("join", "where", "and", "on")):
            score *= 0.6

        # ---------------------------------------------
        # Normalize to 0–1 range
        # ---------------------------------------------
        return clamp(score)
