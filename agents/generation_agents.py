"""
SQL Generation Agents (G1–G7)
All agents now use the centralized PromptBuilder.
"""

from agents.base import BaseGenerationAgent
from core.prompt_builder import PromptBuilder
from llm.llm_manager import LLMManager

llm = LLMManager()
builder = PromptBuilder()


# ============================================================
# Base wrapper for calling PromptBuilder
# ============================================================

def build_prompt(question: str, context: dict, mode: str):
    return builder.build(question, context, mode=mode)


# ============================================================
# G1 — Deterministic Template Generator
# Strict, safe, low temperature
# ============================================================

class DeterministicGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        prompt = build_prompt(question, context, mode="canonical")
        return await llm.openai.acomplete(prompt, temperature=0.0)


# ============================================================
# G2 — Soft Template Generator
# Allows more flexibility in aggregation choices
# ============================================================

class SoftTemplateGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        prompt = build_prompt(question, context, mode="canonical")
        return await llm.openai.acomplete(prompt, temperature=0.2)


# ============================================================
# G3 — Join-Heavy Generator
# Focuses on join correctness
# ============================================================

class JoinHeavyGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        prompt = build_prompt(question, context, mode="join_heavy")
        return await llm.openai.acomplete(prompt, temperature=0.0)


# ============================================================
# G4 — Minimal Prompt Generator
# Compact, efficient, good for short questions
# ============================================================

class MinimalGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        prompt = build_prompt(question, context, mode="compact")
        return await llm.openai.acomplete(prompt, temperature=0.1)


# ============================================================
# G5 — Canonical Style Generator
# Produces highest-quality, readable SQL
# ============================================================

class CanonicalGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        prompt = build_prompt(question, context, mode="canonical")
        return await llm.openai.acomplete(prompt, temperature=0.0)


# ============================================================
# G6 — Local Minimal SLM Generator (Ollama)
# Fast offline generation
# ============================================================

class LocalMinimalSLMGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        prompt = build_prompt(question, context, mode="compact")
        return await llm.ollama.acomplete(prompt, temperature=0.0)


# ============================================================
# G7 — Local Canonical SLM Generator (Ollama)
# Offline canonical mode
# ============================================================

class LocalCanonicalSLMGenerator(BaseGenerationAgent):
    async def generate(self, question: str, context: dict) -> str:
        prompt = build_prompt(question, context, mode="canonical")
        return await llm.ollama.acomplete(prompt, temperature=0.0)
