# core/schema_graph/schema_loader.py

from sqlalchemy import create_engine, inspect
from core.config import settings

class SchemaLoader:
    """
    Loads detailed schema metadata including:
    - columns
    - PK constraints
    - FK constraints (multi-column-aware)
    """

    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)

    def load(self) -> dict:
        insp = inspect(self.engine)
        schema = {}

        for table in insp.get_table_names():
            columns = insp.get_columns(table)

            # Primary key (support composite keys)
            pk_info = insp.get_pk_constraint(table)
            primary_keys = pk_info.get("constrained_columns", []) or []

            # Foreign keys (support composite FKs)
            fk_info = insp.get_foreign_keys(table)
            foreign_keys = []
            for fk in fk_info:
                constrained_cols = fk.get("constrained_columns", [])
                referred_table = fk.get("referred_table", None)
                referred_cols = fk.get("referred_columns", []) or []

                foreign_keys.append({
                    "constrained_columns": constrained_cols,
                    "referred_table": referred_table,
                    "referred_columns": referred_cols
                })

            schema[table] = {
                "columns": [c["name"] for c in columns],
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }

        return schema
