# core/token_reducer/reducer.py

from core.token_reducer.table_summarizer import TableSummarizer
from core.token_reducer.join_path_summarizer import JoinPathSummarizer
from core.token_reducer.llm_compressor import LLMCompressor
from core.utils.logger import get_logger

logger = get_logger("TokenReducer")


class TokenReducer:
    """
    Token reduction / prompt compression engine.

    Produces:
      - compressed columns (heuristics)
      - compressed join paths
      - compressed schema text
      - optional LLM-based summary
    """

    def __init__(self, use_llm=True, max_prompt_chars=4500):
        self.use_llm = use_llm
        self.max_prompt_chars = max_prompt_chars

        self.table_summarizer = TableSummarizer()
        self.join_path_summarizer = JoinPathSummarizer()
        self.llm_compressor = LLMCompressor()

    async def compress(self, context: dict) -> dict:
        """
        Compress the full schema context produced by orchestrator._build_schema_context().

        Returns a NEW compressed context dictionary.
        """

        if not context:
            logger.warning("TokenReducer received empty context")
            return {}

        compressed = dict(context)

        # --------------------------------------------------------
        # 1. TABLE-LEVEL COMPRESSION
        # --------------------------------------------------------
        try:
            compressed["columns"] = (
                self.table_summarizer.compress_columns(context.get("columns", {}))
            )
        except Exception as e:
            logger.error(f"Column compression failed: {e}")
            compressed["columns"] = context.get("columns", {})

        # schema_text
        try:
            compressed["schema_text"] = (
                self.table_summarizer.compress_schema_text(
                    context.get("schema_text", "")
                )
            )
        except Exception as e:
            logger.error(f"Schema text compression failed: {e}")
            compressed["schema_text"] = context.get("schema_text", "")

        # --------------------------------------------------------
        # 2. JOIN PATH COMPRESSION
        # --------------------------------------------------------
        try:
            compressed["join_paths"] = (
                self.join_path_summarizer.compress_join_paths(
                    context.get("join_paths", "")
                )
            )
        except Exception as e:
            logger.error(f"Join path compression failed: {e}")
            compressed["join_paths"] = context.get("join_paths", "")

        # --------------------------------------------------------
        # 3. OPTIONAL LLM-BASED COMPRESSION
        # --------------------------------------------------------
        if self.use_llm:
            try:
                compressed = await self.llm_compressor.summarize_context(
                    compressed, 
                    max_chars=self.max_prompt_chars
                )
            except Exception as e:
                logger.error(f"LLM summarization failed: {e}")

        # --------------------------------------------------------
        # 4. FINAL TRIM — enforce hard cap
        # --------------------------------------------------------
        for key in ["schema_text", "join_paths"]:
            if key in compressed and isinstance(compressed[key], str):
                if len(compressed[key]) > self.max_prompt_chars:
                    compressed[key] = compressed[key][: self.max_prompt_chars] + "..."

        return compressed
