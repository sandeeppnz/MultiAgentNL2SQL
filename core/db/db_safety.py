# core/db/db_safety.py
import re

DANGEROUS_PATTERNS = [
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bINSERT\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bMERGE\b",
    r"\bEXEC\b",
    r"\bCREATE\b",
]

def is_safe_sql(sql: str) -> bool:
    """
    Rejects any SQL that is not strictly read-only.
    """

    if sql is None:
        return False

    sql_upper = sql.upper()

    # Reject multiple statements
    if ";" in sql_upper.strip()[:-1]:
        return False

    # Reject dangerous commands
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, sql_upper):
            return False

    # Allow only SELECT queries
    if not sql_upper.strip().startswith("SELECT"):
        return False

    return True
