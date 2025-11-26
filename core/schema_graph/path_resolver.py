# core/schema_graph/path_resolver.py

from collections import deque

class PathResolver:
    """
    BFS-based path finding for schema graph tables.
    """

    def __init__(self, graph):
        self.graph = graph

    def shortest_path(self, src: str, dst: str):
        """Return shortest path between tables (list of table names)."""

        if src == dst:
            return [src]

        visited = set()
        queue = deque([[src]])

        while queue:
            path = queue.popleft()
            node = path[-1]

            if node == dst:
                return path

            if node not in visited:
                visited.add(node)
                for neigh in self.graph.neighbors(node):
                    new_path = list(path)
                    new_path.append(neigh)
                    queue.append(new_path)

        return None

    def join_chain(self, path):
        """
        Convert path to JOIN-chain description.
        Useful for repair agents.
        """
        if not path or len(path) < 2:
            return ""

        chain = " → ".join(path)
        return chain
