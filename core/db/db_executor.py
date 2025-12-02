# core/db/db_executor.py

import asyncio
import pandas as pd
from sqlalchemy import create_engine, text

from core.db.db_safety import is_safe_sql
from core.db.db_results import normalize_results
from core.config import settings


class DBExecutionError(Exception):
    pass


class DBExecutor:
    def __init__(self, row_limit: int = 500, timeout: int = 15):
        self.row_limit = row_limit
        self.timeout = timeout

        # Standard sync engine (pyodbc)
        self.engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            echo=False,
        )

    async def execute(self, sql: str):
        if not is_safe_sql(sql):
            raise DBExecutionError("Unsafe or non-read-only SQL blocked.")

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._run_sync, sql),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            raise DBExecutionError("SQL execution timed out.")
        except Exception as e:
            raise DBExecutionError(str(e))

    def _run_sync(self, sql: str):
        sql = sql.strip().rstrip(";")
        upper = sql.upper()

        if "ORDER BY" in upper:
            # Split at the *last* ORDER BY (safe for subqueries)
            before, order_by_part = sql.rsplit("ORDER BY", 1)
            before = before.strip()
            order_by_part = order_by_part.strip()

            # Wrap safely
            limited_sql = f"""
            SELECT TOP {self.row_limit} *
            FROM (
                {before}
            ) AS limited_alias
            ORDER BY {order_by_part}
            """
        else:
            limited_sql = f"""
            SELECT TOP {self.row_limit} *
            FROM (
                {sql}
            ) AS limited_alias
            """

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(limited_sql))
                rows = result.fetchall()
                df = pd.DataFrame(rows, columns=result.keys())
                return normalize_results(df)
        except Exception as e:
            raise DBExecutionError(str(e))
