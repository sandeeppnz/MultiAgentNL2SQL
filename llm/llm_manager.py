# llm/llm_manager.py
import asyncio
from llm.openai_client import OpenAIClient
from llm.ollama_client import OllamaClient
from core.utils.logger import get_logger

logger = get_logger("LLMManager")

class LLMManager:
    def __init__(self):
        self.openai = OpenAIClient()
        self.ollama = OllamaClient()

    async def gather_first(self, tasks, timeout=20):
        """Return first completed successful result."""
        done, pending = await asyncio.wait(
            tasks,
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in done:
            result = task.result()
            if result:
                # cancel remaining tasks
                for p in pending:
                    p.cancel()
                return result

        # none returned valid result → return None
        return None

    async def parallel_generate(self, prompts):
        """Run multiple prompts concurrently (for Gen Agents G1–G5)."""
        tasks = [
            asyncio.create_task(self.openai.acomplete(p, temperature=t))
            for p, t in prompts
        ]
        return await self.gather_first(tasks)

    async def parallel_repair(self, prompts):
        """Run multiple repair agents using local SLMs."""
        tasks = [
            asyncio.create_task(self.ollama.acomplete(p))
            for p in prompts
        ]
        return await self.gather_first(tasks)
