# core/schema_graph/path_resolver.py

from collections import deque

class PathResolver:
    """
    BFS-based path finder with join-chain construction.
    """

    def __init__(self, graph):
        self.graph = graph

    def shortest_path(self, src: str, dst: str):
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
                for neigh in self.graph.neighbors(node) + self.graph.reverse_neighbors(node):
                    if neigh not in path:
                        queue.append(path + [neigh])

        return None

    def join_chain(self, path):
        if not path or len(path) < 2:
            return ""

        joins = []
        for a, b in zip(path, path[1:]):
            keymap = self.graph.join_keys(a, b)

            if not keymap:
                continue

            constrained = keymap["constrained"]
            referred = keymap["referred"]

            joins.append(
                f"{a}.{constrained[0]} = {b}.{referred[0]}"
            )

        return " AND ".join(joins)
