# llm/llm_manager.py
import asyncio
from llm.openai_client import OpenAIClient
from llm.ollama_client import OllamaClient
from core.utils.logger import get_logger

logger = get_logger("LLMManager")


class LLMManager:
    """
    Ensures that ALL LLM calls return CLEAN STRINGS or None.
    Provides:
      - safe OpenAI async completion
      - safe Ollama async completion
      - concurrency helpers
    """

    def __init__(self):
        self.openai = OpenAIClient()
        self.ollama = OllamaClient()

    # ============================================================
    # SAFE OpenAI Completion
    # ============================================================

    async def openai_complete(self, prompt: str, temperature=0.0):
        """
        Safe wrapper that ALWAYS returns a string or None.
        """
        try:
            resp = await self.openai.acomplete(prompt, temperature=temperature)
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None

        # Clean fallback
        if not resp:
            return None

        # Ensure valid string return
        if isinstance(resp, str):
            return resp

        # Try extract content from chat object formats
        try:
            # Modern OpenAI: resp.choices[0].message.content
            if hasattr(resp, "choices"):
                msg = resp.choices[0].message
                content = ""

                if isinstance(msg, dict):         # old format
                    content = msg.get("content", "")
                else:                             # new pydantic-like models
                    content = msg.content

                return content
        except Exception as e:
            logger.error(f"OpenAI parse error: {e}")

        return None

    # ============================================================
    # SAFE Ollama Completion
    # ============================================================

    async def ollama_complete(self, prompt: str):
        """
        Safe wrapper for Ollama completions.
        """
        try:
            resp = await self.ollama.acomplete(prompt)
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

        if not resp:
            return None

        # Ensure string return
        if isinstance(resp, str):
            return resp

        # Ollama Python API usually returns dict: {"response": "..."}
        if isinstance(resp, dict):
            return resp.get("response") or resp.get("content") or None

        return None

    # ============================================================
    # First-Result Strategy
    # ============================================================

    async def gather_first(self, tasks, timeout=20):
        """
        Wait for the first *successful* string result.
        """

        done, pending = await asyncio.wait(
            tasks,
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in done:
            try:
                result = task.result()
            except Exception as e:
                logger.error(f"Task error: {e}")
                continue

            if result and isinstance(result, str):
                for p in pending:
                    p.cancel()
                return result

        return None

    # ============================================================
    # Parallel Generation: Using OpenAI
    # ============================================================

    async def parallel_generate(self, prompts):
        tasks = [
            asyncio.create_task(self.openai_complete(p, temperature=t))
            for p, t in prompts
        ]
        return await self.gather_first(tasks)

    # ============================================================
    # Parallel Repair: Using Ollama
    # ============================================================

    async def parallel_repair(self, prompts):
        tasks = [
            asyncio.create_task(self.ollama_complete(p))
            for p in prompts
        ]
        return await self.gather_first(tasks)
