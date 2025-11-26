# core/token_reducer/llm_compressor.py

from llm.llm_manager import LLMManager

llm = LLMManager()

class LLMCompressor:
    """
    Optional LLM compression to reduce token size.
    """

    async def summarize_context(self, context: dict) -> dict:
        text = f"""
Summarize the following schema and join info.
Keep only essential tables, key columns, and FK relationships.
Make summary extremely compact.

{context}
"""

        summary = await llm.openai.acomplete(text, temperature=0)

        context["summary"] = summary
        return context
