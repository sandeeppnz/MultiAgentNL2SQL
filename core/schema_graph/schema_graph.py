# core/schema_graph/schema_graph.py

from collections import defaultdict

class SchemaGraph:
    """
    Simple graph representation of schema relationships.
    Nodes = tables
    Edges = FK connections between tables.

    Purpose:
        Convert the schema into a graph where:
        Nodes = tables
        Edges = foreign key relationships
        This graph powers:
        Join reasoning
        Neighbor/ancestor computation
        Shortest path join suggestions
        Fact table–dimension table detection
        Table expansion in selectors & repair agents


    """

    def __init__(self, schema: dict):
        self.schema = schema
        self.graph = self._build_graph()

    def _build_graph(self):
        g = defaultdict(list)

        for table, meta in self.schema.items():
            for col, ref_table in meta.get("foreign_keys", {}).items():
                # Undirected edge for adjacency
                g[table].append(ref_table)
                g[ref_table].append(table)

        return g

    def neighbors(self, table: str):
        """Return all directly connected tables."""
        return self.graph.get(table, [])

    def is_connected(self, a: str, b: str):
        """Quick check."""
        return b in self.graph.get(a, [])

    def all_tables(self):
        return list(self.graph.keys())
