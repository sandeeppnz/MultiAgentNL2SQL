# core/token_reducer/join_path_summarizer.py

class JoinPathSummarizer:
    """
    Compress join path metadata.
    Only includes:
      - table pairs
      - actual join column mapping
    """

    def compress_join_paths(self, join_paths_text: str) -> str:
        lines = join_paths_text.split("\n")
        compressed = []

        for ln in lines:
            if " = " in ln:
                # reduce to: FactInternetSales.ProductKey = DimProduct.ProductKey
                parts = ln.split(":")
                if len(parts) > 1:
                    compressed.append(parts[-1].strip())
            else:
                compressed.append(ln)

        return "\n".join(compressed[:10])  # safety: keep only first 10 paths
