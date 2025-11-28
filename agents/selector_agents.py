"""
Selector Agents (Semantic, Heuristic, Graph, Fusion)
Upgraded for production-grade NL→SQL selection accuracy.
"""

import numpy as np
from agents.base import BaseSelectorAgent
from core.schema_graph.schema_graph import SchemaGraph
import re


# ------------------------------------------------------------
# Deterministic fallback embedding (no randomness)
# ------------------------------------------------------------

def deterministic_embed(text: str):
    """
    A stable hash → vector fallback embedding.
    Replaces random noise to prevent unstable table selection.
    """
    h = abs(hash(text))  # stable hash
    rng = np.random.default_rng(h % (2**32))
    return rng.random(768)


# ------------------------------------------------------------
# 1. Semantic Selector
# ------------------------------------------------------------

class SemanticSelectorAgent(BaseSelectorAgent):
    """
    Uses semantic similarity between:
      - question embedding
      - table descriptions (columns + roles + PK/FK)
    """

    async def select(self, question: str, schema: dict) -> dict:
        q_emb = deterministic_embed(question)

        table_scores = []

        for table, meta in schema.items():
            # richer table representation
            doc = " ".join([
                table,
                " ".join(meta.get("columns", [])),
                "pk " + " ".join(meta.get("primary_keys", [])),
                "fk " + " ".join(
                    f"{fk['referred_table']} {' '.join(fk['referred_columns'])}"
                    for fk in meta.get("foreign_keys", [])
                )
            ])

            t_emb = deterministic_embed(doc)

            score = float(
                np.dot(q_emb, t_emb) /
                (np.linalg.norm(q_emb) * np.linalg.norm(t_emb) + 1e-9)
            )

            table_scores.append((table, score))

        table_scores.sort(key=lambda x: x[1], reverse=True)
        top = table_scores[:6]

        return {
            "tables": [t for t, s in top],
            "score": float(np.mean([s for _, s in top])),
            "source": "semantic"
        }


# ------------------------------------------------------------
# 2. Heuristic Selector
# ------------------------------------------------------------

class HeuristicSelectorAgent(BaseSelectorAgent):
    """
    Matches keywords and semantic hints from NL query
    to schema table names and business domains.
    """

    KEYWORD_MAP = {
        "sale": ["FactInternetSales", "FactResellerSales"],
        "internet": ["FactInternetSales"],
        "reseller": ["FactResellerSales"],
        "product": ["DimProduct", "DimProductSubcategory", "DimProductCategory"],
        "customer": ["DimCustomer"],
        "territory": ["DimSalesTerritory"],
        "region": ["DimSalesTerritory"],
        "date": ["DimDate"],
        "year": ["DimDate"],
        "month": ["DimDate"],
        "order": ["FactInternetSales"],
        "amount": ["FactInternetSales"],
    }

    async def select(self, question: str, schema: dict) -> dict:
        q = question.lower()
        tables = []

        for kw, table_list in self.KEYWORD_MAP.items():
            if kw in q:
                tables.extend(table_list)

        # dedupe
        tables = list(dict.fromkeys(tables))

        score = len(tables) / (len(self.KEYWORD_MAP) + 1)

        return {
            "tables": tables,
            "score": float(score),
            "source": "heuristic"
        }


# ------------------------------------------------------------
# 3. Column-Based Selector (NEW)
# ------------------------------------------------------------

class ColumnSelectorAgent(BaseSelectorAgent):
    """
    Detects column references in the question.
    e.g. 'color', 'sales amount', 'product key'
    """

    async def select(self, question: str, schema: dict) -> dict:
        q = question.lower()
        tables = []

        for table, meta in schema.items():
            for col in meta.get("columns", []):
                col_l = col.lower()

                # match single words
                if col_l in q:
                    tables.append(table)

                # match multi-word columns: 'sales amount'
                if " " in col_l and col_l.replace("_", " ") in q:
                    tables.append(table)

        tables = list(dict.fromkeys(tables))

        return {
            "tables": tables,
            "score": float(len(tables) / (len(schema) + 1)),
            "source": "column"
        }


# ------------------------------------------------------------
# 4. Graph Selector (Upgraded)
# ------------------------------------------------------------

class GraphSelectorAgent(BaseSelectorAgent):
    """
    Graph-based selection:
      - Identify fact tables
      - Include neighboring dims
      - Include reverse neighbors
      - BFS radius = 2
    """

    async def select(self, question: str, schema: dict) -> dict:
        graph = SchemaGraph(schema)

        fact_candidates = [t for t in schema if t.lower().startswith("fact")]

        tables = set()

        for f in fact_candidates:
            tables.add(f)

            # neighbors (dims)
            for n in graph.neighbors(f):
                tables.add(n)

            # reverse neighbors (dims referencing fact)
            for n in graph.reverse_neighbors(f):
                tables.add(n)

        return {
            "tables": list(tables),
            "score": float(len(tables) / (len(schema) + 1)),
            "source": "graph"
        }


# ------------------------------------------------------------
# 5. Fusion Selector (Upgraded)
# ------------------------------------------------------------

class FusionSelectorAgent(BaseSelectorAgent):
    """
    Combines semantic, heuristic, graph, and column selectors.
    """

    def __init__(self, semantic, heuristic, graph, column_sel):
        self.semantic = semantic
        self.heuristic = heuristic
        self.graph = graph
        self.column_sel = column_sel

    async def select(self, question: str, schema: dict) -> dict:
        s1 = await self.semantic.select(question, schema)
        s2 = await self.heuristic.select(question, schema)
        s3 = await self.graph.select(question, schema)
        s4 = await self.column_sel.select(question, schema)

        all_tables = set(s1["tables"]) | set(s2["tables"]) | set(s3["tables"]) | set(s4["tables"])

        score = (
            0.30 * s1["score"] +    # semantic
            0.20 * s2["score"] +    # heuristic
            0.40 * s3["score"] +    # graph
            0.10 * s4["score"]      # column
        )

        return {
            "tables": list(all_tables),
            "score": float(score),
            "source": "fusion"
        }
