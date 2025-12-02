# core/db/db_executor.py

import asyncio
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError

from core.db.db_safety import is_safe_sql
from core.db.db_results import normalize_results
from core.config import settings
from core.utils.logger import get_logger

logger = get_logger("DBExecutor")


class DBExecutionError(Exception):
    pass


class DBExecutor:
    """
    Safe async SQL runner with:
      - read-only restrictions
      - query timeout
      - row limits
      - clean result normalization
    """

    def __init__(self, timeout: int = 20, row_limit: int = 1000):
        self.timeout = timeout
        self.row_limit = row_limit

        # Example for SQL Server (PyODBC + asyncpg + aioodbc)
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            echo=False,
        )

    # ------------------------------------------------------------
    # Async Safe Execution
    # ------------------------------------------------------------
    async def execute(self, sql: str):
        """
        Executes SQL safely and returns normalized results.
        """

        if not is_safe_sql(sql):
            raise DBExecutionError("Unsafe or non-read-only SQL blocked.")

        try:
            return await asyncio.wait_for(self._run_query(sql), timeout=self.timeout)
        except asyncio.TimeoutError:
            raise DBExecutionError("SQL execution timed out.")
        except Exception as e:
            raise DBExecutionError(f"Execution error: {e}")

    # ------------------------------------------------------------
    # Internal Query Runner
    # ------------------------------------------------------------
    async def _run_query(self, sql: str):
        """
        Runs the SQL and respects row limits.
        """

        limited_sql = f"""
        SELECT TOP {self.row_limit} * FROM (
            {sql}
        ) AS LimitedResult
        """

        async with self.engine.connect() as conn:
            try:
                result = await conn.exec_driver_sql(limited_sql)
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error: {e}")
                raise DBExecutionError(str(e))

            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=result.keys())

            return normalize_results(df)
