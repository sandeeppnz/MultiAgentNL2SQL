# core/agent_fast.py
import asyncio
import re
from core.config import settings
from core.schema_graph.schema_loader import SchemaLoader
from core.schema_graph.schema_graph import SchemaGraph
from core.schema_graph.path_resolver import PathResolver

from agents.selector_agents import (
    SemanticSelectorAgent,
    HeuristicSelectorAgent,
    GraphSelectorAgent,
    FusionSelectorAgent,
    ColumnSelectorAgent
)

from agents.generation_agents import (
    DeterministicGenerator,   # fast + accurate
    CanonicalGenerator        # more robust
)

from agents.validator_agents import CheapOpenAIVerifierAgent
from agents.repair_agents import OpenAIGeneralRepairAgent

from core.confidence.semantic_confidence import SemanticConfidenceAgent

from core.prompt_builder import PromptBuilder


class FastNL2SQLOrchestrator:
    """
    ULTRA-FAST NL→SQL Orchestrator
    Optimized for 4–8 second runtime.

    Changes:
      - No TokenReducer LLM calls
      - Only 2 generation agents
      - Only 1 repair agent (OpenAI)
      - Only 1 validator (OpenAI)
      - Smaller prompts
      - No SLM usage
      - No heavy schema dumping
    """

    def __init__(self):
        # schema
        loader = SchemaLoader()
        self.schema = loader.load()
        self.graph = SchemaGraph(self.schema)
        self.path = PathResolver(self.graph)

        # selectors (same)
        semantic = SemanticSelectorAgent()
        heuristic = HeuristicSelectorAgent()
        graph_sel = GraphSelectorAgent()
        column_sel = ColumnSelectorAgent()

        self.selector = FusionSelectorAgent(
            semantic=semantic,
            heuristic=heuristic,
            graph=graph_sel,
            column_sel=column_sel
        )

        # ultra-fast generation agents
        self.generators = [
            DeterministicGenerator(),   # strongest generator
            CanonicalGenerator(),       # robust canonical SQL
        ]

        # fast repair
        self.repair_agent = OpenAIGeneralRepairAgent()

        # fast validator
        self.validator = CheapOpenAIVerifierAgent()

        # fast confidence
        self.confidence = SemanticConfidenceAgent()

        # prompt builder
        self.pb = PromptBuilder()

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------
    def _canonicalize_sql(self, sql: str, reorder_columns=True) -> str:
            if not sql:
                return ""

            # ---------------------------
            # Remove markdown formatting
            # ---------------------------
            sql = sql.replace("```sql", "").replace("```", "")

            # ---------------------------
            # Normalize whitespace
            # ---------------------------
            sql = sql.replace("\n", " ").replace("\r", " ").replace("\t", " ")
            sql = " ".join(sql.split())

            # ----------------------------------
            # Uppercase SQL keywords
            # ----------------------------------
            SQL_KEYWORDS = [
                "select", "from", "where", "group by", "order by", "join", "left join",
                "right join", "inner join", "outer join", "on", "and", "or", "between",
                "as", "limit", "offset", "having"
            ]

            for kw in sorted(SQL_KEYWORDS, key=len, reverse=True):
                pattern = re.compile(rf"\b{kw}\b", re.IGNORECASE)
                sql = pattern.sub(kw.upper(), sql)

            # ----------------------------------
            # Normalize table aliases:
            #   - remove "AS"
            #   - ensure alias is lowercase
            # ----------------------------------
            def alias_replacer(match):
                table = match.group(1)
                alias = match.group(2).lower()
                return f"{table} {alias}"

            sql = re.sub(r"(\b[A-Za-z0-9_]+\b)\s+AS\s+([A-Za-z0-9_]+)", alias_replacer, sql, flags=re.IGNORECASE)

            # ----------------------------------
            # Optional: reorder SELECT columns
            # ----------------------------------
            if reorder_columns:
                m = re.match(r"SELECT (.+?) FROM (.+)", sql, flags=re.IGNORECASE)
                if m:
                    cols = m.group(1)
                    rest = m.group(2)

                    cols_list = [c.strip() for c in cols.split(",")]
                    cols_list.sort(key=str.lower)
                    sql = f"SELECT {', '.join(cols_list)} FROM {rest}"

            # ----------------------------------
            # Normalize JOIN order:
            # Fact table first, dims later
            # ----------------------------------
            # Light heuristic: put Fact* tables first
            tables = re.findall(r"\b(Fact[A-Za-z0-9_]+)\b|\b(Dim[A-Za-z0-9_]+)\b", sql)
            # RESULT is a list of tuples like: [('FactInternetSales',''), ('','DimProduct')]

            # You can extend this to reorder based on schema_graph if needed

            # ----------------------------------
            # Ensure final semicolon
            # ----------------------------------
            sql = sql.rstrip(";") + ";"

            return sql.strip()



    def _build_context(self, tables: list):
        cols = {t: self.schema[t]["columns"] for t in tables if t in self.schema}
        roles = {t: self.graph.table_role(t) for t in tables}

        join_paths = []
        for i in range(len(tables)):
            for j in range(i+1, len(tables)):
                p = self.path.shortest_path(tables[i], tables[j])
                if p:
                    chain = self.path.join_chain(p)
                    join_paths.append(f"{tables[i]} → {tables[j]}: {chain}")

        return {
            "tables": tables,
            "columns": cols,
            "role_map": roles,
            "join_paths": "\n".join(join_paths)
        }

    # ------------------------------------------------------------------
    # Main Fast Execution
    # ------------------------------------------------------------------

    async def run(self, question: str):
        # 1. Table selection
        sel = await self.selector.select(question, self.schema)
        tables = sel["tables"]

        # 2. Build minimal context
        context = self._build_context(tables)

        # 3. Generate SQL (2 fast generators)
        tasks = [
            g.generate(question, context)
            for g in self.generators
        ]
        raw_list = await asyncio.gather(*tasks)

        candidates = []

        # 4. Validate + optional repair
        for sql in raw_list:
            v = await self.validator.validate(question, sql, context=context)

            if not v["valid"]:
                repaired = await self.repair_agent.repair(sql, {
                    "question": question,
                    "schema_text": ""   # skip heavy schema
                })
                sql = repaired

            score = await self.confidence.score(question, sql)
            candidates.append((score, sql))

        # pick best
        best = max(candidates, key=lambda x: x[0])
        canonical_best = self._canonicalize_sql(best[1])
        canonical_candidates = [
            (score, self._canonicalize_sql(sql))
            for score, sql in candidates
        ]

        return {
            "best_sql": canonical_best,
            "best_score": best[0],
            "selected_tables": tables,
            "candidates": canonical_candidates
        }
