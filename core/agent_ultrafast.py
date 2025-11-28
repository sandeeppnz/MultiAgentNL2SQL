# core/orchestrator_ultrafast.py


import re
from agents.generator_ultrafast import UltraFastGenerator
from agents.selectors_ultrafast import UltraFastSelector


class UltraFastNL2SQLOrchestrator:
    def __init__(self, schema):
        self.schema = schema
        self.selector = UltraFastSelector()
        self.generator = UltraFastGenerator()

    def _build_context(self, tables):
        context = {
            "tables": tables,
            "columns": {},
            "joins": ""
        }

        # light schema: columns only
        for t in tables:
            context["columns"][t] = self.schema[t]["columns"]

        # light join info
        jp = []
        for t in tables:
            for fk in self.schema[t]["foreign_keys"]:
                ref = fk["referred_table"]
                if ref in tables:
                    jp.append(f"{t}.{fk['constrained_columns'][0]} = {ref}.{fk['referred_columns'][0]}")
        context["joins"] = "; ".join(jp)

        return context
    
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

    async def run(self, question: str):
        tables = self.selector.select(question, self.schema)
        context = self._build_context(tables)
        sql = await self.generator.generate(question, context)

        canonical_best = self._canonicalize_sql(sql)
        
        return {
            "sql": canonical_best,
            "tables": tables
        }
