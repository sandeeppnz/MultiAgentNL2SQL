# core/schema_graph/path_resolver.py

from collections import deque


class PathResolver:
    """
    BFS-based join path search over schema graph.
    Produces:
      - clean table paths
      - robust join chains
    """

    def __init__(self, graph):
        self.graph = graph

    # ------------------------------------------------------------
    # Safe helper accessors
    # ------------------------------------------------------------

    def _neighbors(self, table: str):
        """Outgoing FK edges."""
        try:
            return self.graph.neighbors(table)
        except Exception:
            return []

    def _reverse_neighbors(self, table: str):
        """Incoming FK edges."""
        try:
            return self.graph.reverse_neighbors(table)
        except Exception:
            return []

    # ------------------------------------------------------------
    # BFS shortest join path
    # ------------------------------------------------------------

    def shortest_path(self, src: str, dst: str, max_depth=6):
        """
        BFS shortest path between src and dst.
        Limits depth to avoid cycles.
        """
        if src == dst:
            return [src]

        visited = set()
        queue = deque([[src]])

        while queue:
            path = queue.popleft()
            node = path[-1]

            if len(path) > max_depth:
                continue

            if node == dst:
                return path

            if node in visited:
                continue

            visited.add(node)

            neighbors = self._neighbors(node) + self._reverse_neighbors(node)

            for neigh in neighbors:
                if neigh not in path:  # avoid cycle
                    new_path = path + [neigh]
                    queue.append(new_path)

        return None

    # ------------------------------------------------------------
    # JOIN CHAIN BUILDER
    # ------------------------------------------------------------

    def join_chain(self, path):
        """
        Given a list of tables [A,B,C], create join chain:
           A.col = B.col AND B.col = C.col
        Supports:
          - multiple FK columns
          - direction-aware constraints
        """

        if not path or len(path) < 2:
            return ""

        joins = []

        for a, b in zip(path, path[1:]):
            keymap = self.graph.join_keys(a, b)

            if not keymap:
                continue

            constrained = keymap.get("constrained", [])
            referred = keymap.get("referred", [])

            # Multi-column FK support
            for c, r in zip(constrained, referred):
                joins.append(f"{a}.{c} = {b}.{r}")

        return " AND ".join(joins)
