# core/token_reducer/table_summarizer.py

class TableSummarizer:
    """
    Rule-based compression of table schema info.
    Keeps:
      - PK columns
      - FK columns
      - key business columns
    Removes:
      - long text columns
      - unused metadata columns
    """

    def compress_columns(self, col_map: dict) -> dict:
        compressed = {}

        for table, cols in col_map.items():
            # heuristic: keep PK, FK, names, keys
            keep = [
                c for c in cols 
                if "key" in c.lower()
                or "id" in c.lower()
                or "name" in c.lower()
                or "date" in c.lower()
                or "amount" in c.lower()
                or "sales" in c.lower()
            ]

            # fallback if too short
            if len(keep) < 3:
                keep = cols[:5]

            compressed[table] = keep

        return compressed

    def compress_schema_text(self, schema_text: str) -> str:
        """
        Simple deterministic compression:
        - remove long lines
        - keep only PK/FK metadata
        """

        lines = schema_text.split("\n")
        new_lines = []

        for ln in lines:
            if "Columns" in ln and len(ln) > 120:
                # compress column list
                new_lines.append(ln[:120] + "... ]")
            elif "Foreign" in ln:
                new_lines.append(ln)
            elif "PK" in ln:
                new_lines.append(ln)
            else:
                # drop noise lines
                pass

        return "\n".join(new_lines)
