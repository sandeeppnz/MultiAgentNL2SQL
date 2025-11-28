# core/token_reducer/llm_compressor.py

from llm.llm_manager import LLMManager
from core.utils.logger import get_logger

logger = get_logger("LLMCompressor")
llm = LLMManager()


class LLMCompressor:
    """
    Optional LLM-driven compression for:
      - schema_text
      - columns
      - join paths

    Produces:
      context["summary"] = compressed text
    """

    async def summarize_context(self, context: dict, max_chars=2000) -> dict:
        """
        Summarizes <= 3 parts:
            - columns summary
            - join paths summary
            - schema_text summary

        Adds:
            context["summary"] = final_compressed_text

        NEVER replaces original keys; generator/prompt_builder chooses what to use.
        """

        # Build input chunks
        columns_section = str(context.get("columns", ""))[:1500]
        joins_section = str(context.get("join_paths", ""))[:1500]
        schema_section = str(context.get("schema_text", ""))[:2000]

        prompt = f"""
You are a compression engine for a SQL generation system.

TASK:
Summarize the following STAR-SCHEMA metadata into a very compact,
token-efficient form. MUST preserve:
  - table names
  - key columns (keys, ids, names, dates)
  - FK relationships
  - join chains (summarized)

DO NOT include:
  - unnecessary prose
  - comments
  - long text
  - full column lists

OUTPUT FORMAT (VERY IMPORTANT):
Return ONLY the compressed summary as plain text. No JSON.

--- COLUMNS ---
{columns_section}

--- JOINS ---
{joins_section}

--- SCHEMA ---
{schema_section}

Produce the most compact but accurate representation possible.
"""

        # Try LLM compression
        try:
            summary = await llm.openai_complete(prompt, temperature=0)
        except Exception as e:
            logger.error(f"LLMCompressor: OpenAI exception: {e}")
            summary = None

        # Validate output
        if not summary or not isinstance(summary, str):
            logger.warning("LLMCompressor: Falling back to deterministic compression")

            # Deterministic fallback
            summary = self._fallback(context)

        # Enforce max length
        summary = summary.strip()
        if len(summary) > max_chars:
            summary = summary[:max_chars] + "..."

        context["summary"] = summary
        return context

    # ------------------------------------------------------------
    # Deterministic fallback (always safe)
    # ------------------------------------------------------------

    def _fallback(self, context: dict) -> str:
        """
        In case the LLM fails, provide a deterministic fallback summary.
        """

        cols = context.get("columns", {})
        col_summary = ", ".join(
            f"{t}({', '.join(cols[t][:3])}...)"
            for t in list(cols)[:5]
        )

        joins = context.get("join_paths", "").split("\n")
        join_summary = "; ".join(joins[:5])

        return f"Tables: {col_summary}\nJoins: {join_summary}"
