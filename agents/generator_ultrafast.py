# core/generator_ultrafast.py

from llm.llm_manager import LLMManager
from core.prompt_builder_ultrafast import UltraFastPromptBuilder

class UltraFastGenerator:
    def __init__(self):
        self.llm = LLMManager()
        self.pb = UltraFastPromptBuilder()

    async def generate(self, question: str, context: dict):
        prompt = self.pb.build(question, context)
        return await self.llm.openai.acomplete(prompt, temperature=0)
