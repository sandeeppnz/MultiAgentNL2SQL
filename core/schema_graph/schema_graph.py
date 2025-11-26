# core/schema_graph/schema_graph.py

from collections import defaultdict

class SchemaGraph:
    """
    Advanced graph representation of database schema:
    - tracks FK edges with column mappings
    - differentiates fact vs dimension tables
    """

    def __init__(self, schema: dict):
        self.schema = schema
        self.graph = self._build_graph()
        self.reverse = self._build_reverse_map()
        self.roles = self._detect_roles()

    def _build_graph(self):
        """
        Build directional graph:
          table A --fk(A.col -> B.pk)--> table B
        """
        g = defaultdict(list)

        for table, meta in self.schema.items():
            for fk in meta.get("foreign_keys", []):
                ref = fk["referred_table"]

                g[table].append({
                    "to": ref,
                    "constrained_columns": fk["constrained_columns"],
                    "referred_columns": fk["referred_columns"]
                })

        return g

    def _build_reverse_map(self):
        """
        Reverse lookup:
          dimension table → list of fact tables referencing it
        """
        r = defaultdict(list)

        for table, edges in self.graph.items():
            for edge in edges:
                r[edge["to"]].append(table)

        return r

    def _detect_roles(self):
        """
        Heuristic: Fact tables typically:
        - start with 'Fact'
        Dimension tables:
        - start with 'Dim'
        """
        roles = {}

        for table in self.schema:
            t = table.lower()

            if t.startswith("fact"):
                roles[table] = "fact"
            elif t.startswith("dim"):
                roles[table] = "dimension"
            else:
                roles[table] = "other"

        return roles

    # -----------------------------
    # public API
    # -----------------------------

    def neighbors(self, table: str):
        """Return tables reachable from table via FK edges."""
        return [edge["to"] for edge in self.graph.get(table, [])]

    def reverse_neighbors(self, table: str):
        """Tables referencing this table."""
        return self.reverse.get(table, [])

    def table_role(self, table: str):
        """Return: fact, dimension, or other."""
        return self.roles.get(table, "other")

    def join_keys(self, table_a: str, table_b: str):
        """
        Return join key mapping between two connected tables.
        Output:
          {
             "a_col": "ProductKey",
             "b_col": "ProductKey"
          }
        """
        # outbound FK
        for edge in self.graph.get(table_a, []):
            if edge["to"] == table_b:
                return {
                    "from": table_a,
                    "to": table_b,
                    "constrained": edge["constrained_columns"],
                    "referred": edge["referred_columns"]
                }

        # inbound FK (reverse edge)
        for edge in self.graph.get(table_b, []):
            if edge["to"] == table_a:
                return {
                    "from": table_b,
                    "to": table_a,
                    "constrained": edge["constrained_columns"],
                    "referred": edge["referred_columns"]
                }

        return None
