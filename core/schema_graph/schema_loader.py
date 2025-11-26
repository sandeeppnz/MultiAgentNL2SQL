# core/schema_graph/schema_loader.py

from sqlalchemy import create_engine, inspect
from core.config import settings

class SchemaLoader:
    """
    Loads schema metadata from SQL Server via SQLAlchemy+pyodbc.

    Produces a Python dictionary describing:
      - columns
      - primary keys
      - foreign key mappings

    Output
        {
            "FactInternetSales": {
                "columns": [...],
                "primary_key": "...",
                "foreign_keys": {
                    "ProductKey": "DimProduct",
                    "CustomerKey": "DimCustomer"
                }
            },
        ...
        }


    """

    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)

    def load(self) -> dict:
        insp = inspect(self.engine)
        schema = {}

        for table in insp.get_table_names():
            cols = insp.get_columns(table)

            pk = None
            try:
                pks = insp.get_pk_constraint(table).get("constrained_columns", [])
                pk = pks[0] if pks else None
            except Exception:
                pk = None

            fk_map = {}
            try:
                for fk in insp.get_foreign_keys(table):
                    col = fk.get("constrained_columns", [None])[0]
                    ref_table = fk.get("referred_table")
                    if col and ref_table:
                        fk_map[col] = ref_table
            except Exception:
                pass

            schema[table] = {
                "columns": [c["name"] for c in cols],
                "primary_key": pk,
                "foreign_keys": fk_map
            }

        return schema
