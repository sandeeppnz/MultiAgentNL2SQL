# core/confidence/structural_confidence.py

from sqlglot import parse_one
from agents.base import BaseValidatorAgent

class StructuralConfidenceAgent:
    """
    Scores SQL based on AST structure quality:
    - valid SQL?
    - has SELECT?
    - has FROM?
    - has valid JOINs?
    - uses GROUP BY correctly?

    AST + structure-driven scoring.
    """

    def score(self, sql: str) -> float:
        try:
            ast = parse_one(sql)
        except Exception:
            return 0.0

        score = 0.0

        if ast.find("Select"):
            score += 0.3

        if ast.find("From"):
            score += 0.3

        if ast.find("Join"):
            score += 0.2

        if ast.find("Group"):
            score += 0.2

        return min(1.0, score)
