# core/agent.py

import asyncio
from core.config import settings
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

        # ----------------------------
        # selector agents
        # ----------------------------
        self.selector_agents = [
            SemanticSelectorAgent(),
            HeuristicSelectorAgent(),
            GraphSelectorAgent(),
            FusionSelectorAgent()
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
            agent.select(question) for agent in self.selector_agents
        ])

        # flatten and dedup
        tables = set()
        for r in results:
            for t in r:
                tables.add(t)

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

    async def _repair_sql(self, question: str, sql: str):
        diagnostics = {
            "question": question,
            "schema_text": context.get("schema_text")
        }

        repaired = []
        for agent in self.repair_agents:
            try:
                fixed = await agent.repair(sql, diagnostics)
                repaired.append(fixed)
            except Exception:
                pass

        return repaired

    # ============================================================
    # Confidence Scoring
    # ============================================================

    async def _score_sql(self, question: str, sql: str):
        return await self.confidence.score(question, sql)

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
                repaired_list = await self._repair_sql(question, sql)
                final_list = repaired_list
            else:
                final_list = [sql]

            # score each candidate
            for c in final_list:
                score = await self._score_sql(question, c)
                candidates.append((score, c))

        # 4. pick best
        best = max(candidates, key=lambda x: x[0])

        return {
            "best_sql": best[1],
            "best_score": best[0],
            "all_candidates": candidates,
            "selected_tables": tables
        }
