# core/token_reducer/table_summarizer.py

import re


class TableSummarizer:
    """
    Rule-based compression of table schema info.

    Prioritizes:
      - primary keys
      - foreign keys
      - business attributes (Name, Type, Category, Amount, Date)
      - stable minimal representation

    Ignores:
      - ETL/audit/system columns
      - long text columns
    """

    # ------------------------------------------------------------------------------------
    # Column name heuristics
    # ------------------------------------------------------------------------------------
    BUSINESS_COL_PATTERNS = [
        r"name", r"type", r"category", r"class", r"group",
        r"date", r"year", r"month", r"day",
        r"title", r"desc", r"code",
        r"amount", r"price", r"cost", r"qty", r"quantity",
        r"region", r"state", r"country", r"city",
    ]

    KEY_COL_PATTERNS = [
        r"key$", r"id$", r"id_", r"_id$", r"pk$", r"fk$"
    ]

    IGNORE_PATTERNS = [
        r"rowguid", r"modified", r"created", r"updated", r"load", r"etl",
        r"rowversion", r"audit", r"checksum"
    ]

    def _matches_any(self, col: str, patterns):
        col_l = col.lower()
        return any(re.search(p, col_l) for p in patterns)

    # ------------------------------------------------------------------------------------
    # COLUMN COMPRESSION
    # ------------------------------------------------------------------------------------
    def compress_columns(self, col_map: dict) -> dict:
        """
        Compress per-table column lists using business heuristics.
        """

        compressed = {}

        for table, cols in col_map.items():
            # normalize
            cleaned = [c.strip() for c in cols]

            # STEP 1 — always keep primary/foreign keys
            key_cols = [
                c for c in cleaned if self._matches_any(c, self.KEY_COL_PATTERNS)
            ]

            # STEP 2 — keep business-relevant columns
            business_cols = [
                c for c in cleaned if self._matches_any(c, self.BUSINESS_COL_PATTERNS)
            ]

            # STEP 3 — skip system/audit columns
            ignore_cols = {
                c for c in cleaned if self._matches_any(c, self.IGNORE_PATTERNS)
            }

            keep = []
            keep.extend(key_cols)
            keep.extend([c for c in business_cols if c not in keep])
            keep = [c for c in keep if c not in ignore_cols]

            # STEP 4 — fallback: ensure minimum coverage
            if len(keep) < 3:
                keep = cleaned[:5]

            # STEP 5 — truncate for safety
            compressed[table] = keep[:10]

        return compressed

    # ------------------------------------------------------------------------------------
    # SCHEMA TEXT COMPRESSION
    # ------------------------------------------------------------------------------------
    def compress_schema_text(self, schema_text: str) -> str:
        """
        Compress schema metadata.

        Keep:
         - PK lines
         - FK lines
         - few essential column lines

        Drop:
         - verbose descriptions
         - long column enumerations
        """

        lines = schema_text.split("\n")
        new_lines = []

        for ln in lines:
            if not ln.strip():
                continue

            L = ln.lower()

            # Keep PK/FK mappings
            if "pk:" in L or "primary" in L:
                new_lines.append(ln)
                continue
            if "fk:" in L or "foreign" in L:
                new_lines.append(ln)
                continue

            # Compress very long column lists
            if "columns:" in L:
                if len(ln) > 150:
                    new_lines.append(ln[:150] + "... ]")
                else:
                    new_lines.append(ln)
                continue

            # Skip all other lines
            continue

        return "\n".join(new_lines[:50])  # safety: limit lines
