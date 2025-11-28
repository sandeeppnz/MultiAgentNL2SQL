# core/schema_graph/schema_graph.py

from collections import defaultdict
from typing import List, Dict


class SchemaGraph:
    """
    Robust schema graph for NL→SQL join inference.

    Tracks:
    - forward FK edges (A → B)
    - reverse FK edges (B ← A)
    - fact/dimension roles
    """

    def __init__(self, schema: dict):
        self.schema = schema

        # full directional edges
        self.forward_edges = self._build_forward_graph()
        self.reverse_edges = self._build_reverse_graph()

        # roles: fact / dimension / other
        self.roles = self._detect_roles()

    # ============================================================
    # GRAPH CONSTRUCTION
    # ============================================================

    def _build_forward_graph(self):
        """
        Build directed FK graph:
          A --(A.fk → B.pk)--> B

        Structure:
        forward_edges[A] = [
            {
                "to": B,
                "fk_cols": [...],
                "pk_cols": [...],
            }
        ]
        """
        g = defaultdict(list)

        for table, meta in self.schema.items():
            for fk in meta.get("foreign_keys", []):
                ref = fk["referred_table"]

                g[table].append({
                    "to": ref,
                    "fk_cols": fk["constrained_columns"],
                    "pk_cols": fk["referred_columns"],
                })

        return g

    def _build_reverse_graph(self):
        """
        Reverse FK graph:
          B ← A  (A references B)

        Structure:
        reverse_edges[B] = [
            {
                "from": A,
                "fk_cols": [...],
                "pk_cols": [...],
            }
        ]
        """
        r = defaultdict(list)

        for a, edges in self.forward_edges.items():
            for edge in edges:
                b = edge["to"]
                r[b].append({
                    "from": a,
                    "fk_cols": edge["fk_cols"],
                    "pk_cols": edge["pk_cols"],
                })

        return r

    # ============================================================
    # FACT / DIMENSION ROLE DETECTION
    # ============================================================

    def _detect_roles(self):
        """
        Simple heuristic:
          - startswith("Fact") → fact
          - startswith("Dim") → dimension
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

    # ============================================================
    # PUBLIC API
    # ============================================================

    def neighbors(self, table: str) -> List[str]:
        """
        Outbound FK neighbors.
        A → B
        """
        return [edge["to"] for edge in self.forward_edges.get(table, [])]

    def reverse_neighbors(self, table: str) -> List[str]:
        """
        Inbound FK neighbors.
        B ← A
        """
        return [edge["from"] for edge in self.reverse_edges.get(table, [])]

    def table_role(self, table: str) -> str:
        """Return: fact, dimension, or other."""
        return self.roles.get(table, "other")

    # ============================================================
    # JOIN KEY LOOKUP
    # ============================================================

    def join_keys(self, table_a: str, table_b: str):
        """
        Return join key mapping, fully directional.

        Output structure:
        {
            "from": table_with_fk,
            "to": table_with_pk,
            "constrained": [...],
            "referred": [...],
        }
        """

        # Case 1: A → B (A has FK)
        for edge in self.forward_edges.get(table_a, []):
            if edge["to"] == table_b:
                return {
                    "from": table_a,
                    "to": table_b,
                    "constrained": edge["fk_cols"],
                    "referred": edge["pk_cols"],
                }

        # Case 2: B → A (B has FK)
        for edge in self.forward_edges.get(table_b, []):
            if edge["to"] == table_a:
                return {
                    "from": table_b,
                    "to": table_a,
                    "constrained": edge["fk_cols"],
                    "referred": edge["pk_cols"],
                }

        return None
