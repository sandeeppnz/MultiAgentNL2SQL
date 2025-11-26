# core/token_reducer/reducer.py

from core.token_reducer.table_summarizer import TableSummarizer
from core.token_reducer.join_path_summarizer import JoinPathSummarizer
from core.token_reducer.llm_compressor import LLMCompressor


class TokenReducer:
    """
    Reduces prompt size for schema-aware SQL generation.
    Can run:
      - deterministic compression
      - LLM-based summarization (optional)
    """

    def __init__(self, use_llm=True):
        self.use_llm = use_llm
        self.table_summarizer = TableSummarizer()
        self.join_path_summarizer = JoinPathSummarizer()
        self.llm_compressor = LLMCompressor()

    async def compress(self, context: dict) -> dict:
        """
        Takes a full schema context from orchestrator._build_schema_context()
        and returns a compressed version optimized for generation prompts.
        """

        compressed = dict(context)

        # 1) compress table info
        compressed["columns"] = self.table_summarizer.compress_columns(
            context["columns"]
        )
        compressed["schema_text"] = self.table_summarizer.compress_schema_text(
            context["schema_text"]
        )

        # 2) compress join paths
        compressed["join_paths"] = self.join_path_summarizer.compress_join_paths(
            context["join_paths"]
        )

        # 3) optional LLM summarization
        if self.use_llm:
            compressed = await self.llm_compressor.summarize_context(compressed)

        return compressed
