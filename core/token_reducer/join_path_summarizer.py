# core/token_reducer/join_path_summarizer.py

import re

class JoinPathSummarizer:
    """
    Compress join path metadata while preserving:
      - table sequence
      - essential join clauses
      - multi-hop relationships

    Produces compact but informative join summaries.
    """

    def _clean_key(self, key: str) -> str:
        """Normalize identifier."""
        return (
            key.replace("[", "")
               .replace("]", "")
               .replace("`", "")
               .replace('"', "")
               .strip()
        )

    def _compress_join_clause(self, clause: str) -> str:
        """
        Compress:
           FactInternetSales.ProductKey = DimProduct.ProductKey
        to:
           FIS.ProductKey = DP.ProductKey
        if aliases exist (optional future feature)
        """
        # Basic normalization
        clause = self._clean_key(clause)

        # Remove repeating schema/table prefixes (slight compression)
        clause = re.sub(r"\b(dbo|schema)\.", "", clause, flags=re.I)

        return clause

    def compress_join_paths(self, join_paths_text: str, max_paths=10):
        if not join_paths_text:
            return ""

        lines = join_paths_text.split("\n")
        compressed = []

        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue

            if " → " in ln and ":" in ln:
                # Example:
                # FactInternetSales → DimProduct: FIS.ProductKey = DP.ProductKey
                try:
                    tables, join_clause = ln.split(":", 1)
                except ValueError:
                    continue

                tables = tables.strip()
                join_clause = join_clause.strip()

                compressed_clause = self._compress_join_clause(join_clause)

                compressed.append(f"{tables}: {compressed_clause}")

            elif " = " in ln:
                # Standalone join chains
                compressed.append(self._compress_join_clause(ln))

            # Ignore lines without join info
            else:
                continue

            # Limit output
            if len(compressed) >= max_paths:
                break

        return "\n".join(compressed)
