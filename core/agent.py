# core/agent.py

import asyncio
import re
from core.config import settings
from core.db.db_executor import DBExecutor
from core.schema_graph.schema_loader import SchemaLoader
from core.schema_graph.schema_graph import SchemaGraph
from core.schema_graph.path_resolver import PathResolver

from agents.selector_agents import (
    SemanticSelectorAgent, HeuristicSelectorAgent,
    GraphSelectorAgent, FusionSelectorAgent
)

from agents.generation_agents import (
    DeterministicGenerator,
    SoftTemplateGenerator,
    JoinHeavyGenerator,
    MinimalGenerator,
    CanonicalGenerator,
    LocalMinimalSLMGenerator,
    LocalCanonicalSLMGenerator
)

from agents.validator_agents import FusionValidatorAgent
from agents.repair_agents import (
    OpenAIGeneralRepairAgent,
    OpenAIJoinRepairAgent,
    OpenAISemanticRepairAgent
)

from core.confidence.fusion_confidence import FusionConfidenceAgent
from core.token_reducer.reducer import TokenReducer




class NL2SQLOrchestrator:
    """
    The central controller that runs:
    - table selection
    - sql generation
    - validation
    - repair
    - confidence scoring
    """



    def __init__(self):
        # ----------------------------
        # schema setup
        # ----------------------------
        loader = SchemaLoader()
        self.schema = loader.load()

        self.graph = SchemaGraph(self.schema)
        self.path = PathResolver(self.graph)
        self.token_reducer = TokenReducer(use_llm=True)
        self.db = DBExecutor(timeout=20, row_limit=500)

        # ----------------------------
        # selector agents
        # ----------------------------
        semantic_selector = SemanticSelectorAgent()
        heuristic_selector = HeuristicSelectorAgent()
        graph_selector = GraphSelectorAgent()

        from agents.selector_agents import ColumnSelectorAgent
        column_selector = ColumnSelectorAgent()

        fusion_selector = FusionSelectorAgent(
            semantic=semantic_selector,
            heuristic=heuristic_selector,
            graph=graph_selector,
            column_sel=column_selector

        )

        self.selector_agents = [
            semantic_selector,
            heuristic_selector,
            graph_selector,
            column_selector,  
            fusion_selector,
        ]

        # ----------------------------
        # generation agents
        # ----------------------------
        self.generation_agents = [
            DeterministicGenerator(),
            SoftTemplateGenerator(),
            JoinHeavyGenerator(),
            MinimalGenerator(),
            CanonicalGenerator()
        ]

        if settings.ENABLE_SLM_GENERATORS:
            self.generation_agents.extend([
                LocalMinimalSLMGenerator(),
                LocalCanonicalSLMGenerator()
            ])

        # ----------------------------
        # repair agents
        # ----------------------------
        self.repair_agents = []

        # OpenAI repair is ALWAYS included
        self.repair_agents.extend([
            OpenAIGeneralRepairAgent(),
            OpenAIJoinRepairAgent(),
            OpenAISemanticRepairAgent()
        ])

        # Optional: Local SLM repair loop
        if settings.USE_SLM_REPAIR:
            from agents.repair_agents import (
                GrammarFixAgent,
                JoinRepairAgent,
                ColumnFixAgent,
                GroupByRepairAgent,
                DimCompletionAgent,
                ASTCanonicalRepairAgent,
                SemanticRepairAgent
            )
            self.repair_agents.extend([
                GrammarFixAgent(),
                JoinRepairAgent(),
                ColumnFixAgent(),
                GroupByRepairAgent(),
                DimCompletionAgent(),
                ASTCanonicalRepairAgent(),
                SemanticRepairAgent(),
            ])

        # ----------------------------
        # validators
        # ----------------------------
        self.validator = FusionValidatorAgent()

        # ----------------------------
        # confidence
        # ----------------------------
        self.confidence = FusionConfidenceAgent()

    # ============================================================
    # Build Schema Context Block
    # ============================================================

    def _build_schema_context(self, tables: list):
        """
        Build context for generation agents including:
        - table list
        - column map
        - join paths for every table
        - fact/dim roles
        - schema text block
        """
        # column map
        col_map = {t: self.schema[t]["columns"] for t in tables if t in self.schema}

        # roles
        roles = {t: self.graph.table_role(t) for t in tables}

        # join paths (for all pairs)
        join_paths = []
        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                t1 = tables[i]
                t2 = tables[j]
                path = self.path.shortest_path(t1, t2)
                if path:
                    chain = self.path.join_chain(path)
                    join_paths.append(f"{t1} → {t2}: {chain}")

        join_paths_text = "\n".join(join_paths)

        # pretty schema text
        schema_text = "\n\n".join(
            f"{t}:\n  Columns: {', '.join(meta['columns'])}\n"
            f"  PK: {meta['primary_keys']}\n"
            f"  FK: {meta['foreign_keys']}"
            for t, meta in self.schema.items()
        )

        return {
            "tables": tables,
            "columns": col_map,
            "role_map": roles,
            "join_paths": join_paths_text,
            "schema_text": schema_text
        }

    # ============================================================
    # Table Selection
    # ============================================================

    async def _select_tables(self, question: str):
        results = await asyncio.gather(*[
            agent.select(question, self.schema)
            for agent in self.selector_agents
        ])

        tables = set()
        for result in results:
            tables.update(result.get("tables", []))

        return list(tables)

    # ============================================================
    # SQL Generation
    # ============================================================

    async def _generate_sql(self, question: str, context: dict):
        tasks = [
            agent.generate(question, context)
            for agent in self.generation_agents
        ]
        return await asyncio.gather(*tasks)

    # ============================================================
    # Validation
    # ============================================================

    async def _validate(self, question: str, sql: str):
        return await self.validator.validate(question, sql)

    # ============================================================
    # Repair Loop
    # ============================================================

    async def _repair_sql(self, question: str, sql: str, context: dict):
        """
        Repairs SQL using all repair agents.
        Now passes full diagnostics including:
            - tables
            - columns
            - roles
            - join_paths
            - schema_text
            - summary
        """

        diagnostics = {
            "question": question,
            "schema_text": context.get("schema_text", ""),
            "summary": context.get("summary", ""),
            "tables": context.get("tables", []),
            "columns": context.get("columns", {}),
            "roles": context.get("role_map", {}),
            "join_paths": context.get("join_paths", "")
        }

        repaired = []

        for agent in self.repair_agents:
            try:
                fixed = await agent.repair(sql, diagnostics)
                if fixed and isinstance(fixed, str):
                    repaired.append(fixed)
            except Exception:
                # DON’T crash orchestrator — continue repairing
                pass

        return repaired


    # ============================================================
    # Confidence Scoring
    # ============================================================

    async def _score_sql(self, question: str, sql: str):
        return await self.confidence.score(question, sql)


   
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



    # ============================================================
    # MAIN PIPELINE
    # ============================================================

    async def run(self, question: str):
        # 1. table selection
        tables = await self._select_tables(question)
        context = self._build_schema_context(tables)

        # compress tokens
        compressed_context = await self.token_reducer.compress(context)
        # 2. generation
        raw_sql_list = await self._generate_sql(question, compressed_context)

        # 3. validation + repair + scoring
        candidates = []

        for sql in raw_sql_list:
            validation = await self._validate(question, sql)

            if not validation["valid"]:
                repaired_list = await self._repair_sql(
                    question, sql, compressed_context
                )
                final_list = repaired_list
            else:
                final_list = [sql]

            # score each candidate
            for c in final_list:
                score = await self._score_sql(question, c)
                candidates.append((score, c))

        # 4. pick best
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
            "all_candidates": canonical_candidates
        }



    async def execute_sql(self, best_sql: str):
        try:
            return await self.db.execute(best_sql)
        except Exception as e:
            return {"error": str(e)}