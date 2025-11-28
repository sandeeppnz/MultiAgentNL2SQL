# core/schema_graph/schema_loader.py

from sqlalchemy import create_engine, inspect
from core.config import settings
from core.utils.logger import get_logger

logger = get_logger("SchemaLoader")


class SchemaLoader:
    """
    Loads validated, normalized star-schema metadata:
      - tables (dbo only)
      - cleaned column names
      - PKs (supports composite)
      - FKs (supports composite)
    """

    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)

    def _clean_identifier(self, name: str) -> str:
        """
        Normalize SQL Server identifier:
        - strip brackets [ProductKey]
        - strip quotes
        - strip whitespace
        - unify casing
        """
        if not name:
            return ""

        return (
            name.replace("[", "")
                .replace("]", "")
                .replace('"', "")
                .replace("`", "")
                .strip()
        )

    def load(self) -> dict:
        insp = inspect(self.engine)
        schema = {}

        # Only use dbo schema (common DW pattern)
        tables = insp.get_table_names(schema="dbo")
        if not tables:
            # fallback: use default schema list
            tables = insp.get_table_names()

        # Filter out system/internal tables
        tables = [
            t for t in tables
            if not t.lower().startswith(("sys", "ms_", "queue_", "trace"))
        ]

        for table in tables:
            table_clean = self._clean_identifier(table)
            columns = insp.get_columns(table)

            # Clean column names
            col_names = [
                self._clean_identifier(c["name"])
                for c in columns
            ]

            # Primary keys
            pk_info = insp.get_pk_constraint(table)
            raw_pk = pk_info.get("constrained_columns", []) or []
            primary_keys = [self._clean_identifier(c) for c in raw_pk]

            # Foreign keys
            foreign_keys = []
            fk_info = insp.get_foreign_keys(table) or []

            for fk in fk_info:
                constrained = fk.get("constrained_columns") or []
                referred = fk.get("referred_columns") or []
                ref_table = fk.get("referred_table")

                # Normalize
                constrained = [self._clean_identifier(c) for c in constrained]
                referred = [self._clean_identifier(c) for c in referred]
                ref_table = self._clean_identifier(ref_table) if ref_table else None

                # Validate FK mapping
                if not ref_table:
                    logger.warning(f"Skipping FK on {table_clean}: missing referred_table")
                    continue

                if len(constrained) != len(referred):
                    logger.warning(
                        f"Skipping FK on {table_clean}: mismatched columns {constrained} → {referred}"
                    )
                    continue

                foreign_keys.append({
                    "constrained_columns": constrained,
                    "referred_table": ref_table,
                    "referred_columns": referred
                })

            # Add to schema map
            schema[table_clean] = {
                "columns": col_names,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }

        return schema
