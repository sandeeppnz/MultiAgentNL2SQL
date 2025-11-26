# agents/selector_agents.py

import numpy as np
from agents.base import BaseSelectorAgent
from core.schema_graph.schema_graph import SchemaGraph



# TODO: replace with real emb model (sentence-transformers or OpenAI)
def fake_embed(text: str):
    """Placeholder embedding until real model is added."""
    return np.random.rand(768)

class SemanticSelectorAgent(BaseSelectorAgent):
    """
    Uses semantic similarity between:
      - question embedding
      - table description embeddings
    """

    async def select(self, question: str, schema: dict) -> dict:
        q_emb = fake_embed(question)

        table_scores = []
        for table, meta in schema.items():
            doc = table + " " + " ".join(meta.get("columns", []))
            t_emb = fake_embed(doc)

            score = float(np.dot(q_emb, t_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(t_emb)))
            table_scores.append((table, score))

        # pick top-N tables
        table_scores.sort(key=lambda x: x[1], reverse=True)
        top = table_scores[:5]

        return {
            "tables": [t for t, s in top],
            "score": float(np.mean([s for _, s in top])),
            "source": "semantic"
        }


class HeuristicSelectorAgent(BaseSelectorAgent):
    """
    Matches keywords and structural hints in natural language
    to known schema tables.

    Time questions → include DimDate
    Product → include product tables
    Customer → include customer tables
    “total sales” → include FactInternetSales
    Detect measure words (count, sum, avg)

    """

    KEYWORD_MAP = {
        "sale": ["FactInternetSales", "FactResellerSales"],
        "internet": ["FactInternetSales"],
        "reseller": ["FactResellerSales"],
        "product": ["DimProduct", "DimProductSubcategory", "DimProductCategory"],
        "customer": ["DimCustomer"],
        "date": ["DimDate", "DimCalendar"],
        "year": ["DimDate"],
        "month": ["DimDate"],
    }

    async def select(self, question: str, schema: dict) -> dict:
        q = question.lower()
        tables = []

        for keyword, table_list in self.KEYWORD_MAP.items():
            if keyword in q:
                tables.extend(table_list)

        # Deduplicate
        tables = list(dict.fromkeys(tables))

        # Score = proportion of keywords matched
        score = len(tables) / (len(self.KEYWORD_MAP) + 1)

        return {
            "tables": tables,
            "score": float(score),
            "source": "heuristic"
        }


class GraphSelectorAgent(BaseSelectorAgent):
    """
    Uses schema graph connectivity:
      - find nearest fact tables
      - include their connected dimension tables
      - ensure join paths are short
    """

    async def select(self, question: str, schema: dict) -> dict:
        graph = SchemaGraph(schema)

        # TODO: Improve fact table detection (measure detection)
        fact_candidates = [t for t in schema if t.lower().startswith("fact")]

        # simple: pick all facts for now
        tables = list(fact_candidates)

        # Add neighbors (dims)
        for f in fact_candidates:
            for neigh in graph.neighbors(f):
                if neigh not in tables:
                    tables.append(neigh)

        score = len(tables) / (len(schema) + 1)

        return {
            "tables": tables,
            "score": float(score),
            "source": "graph"
        }


class FusionSelectorAgent(BaseSelectorAgent):
    """
    Combines results of:
      - semantic selector
      - heuristic selector
      - graph selector
    """

    def __init__(self, semantic, heuristic, graph):
        self.semantic = semantic
        self.heuristic = heuristic
        self.graph = graph

    async def select(self, question: str, schema: dict) -> dict:
        s1 = await self.semantic.select(question, schema)
        s2 = await self.heuristic.select(question, schema)
        s3 = await self.graph.select(question, schema)

        all_tables = set(s1["tables"]) | set(s2["tables"]) | set(s3["tables"])

        score = (
            0.50 * s1["score"] +
            0.20 * s2["score"] +
            0.30 * s3["score"]
        )

        return {
            "tables": list(all_tables),
            "score": float(score),
            "source": "fusion"
        }


# Later, when you add:

# FactTableSelectorAgent

# MetricSelectorAgent

# DimensionHeuristicAgent

# ColumnSelectorAgent

# JoinPathSelectorAgent