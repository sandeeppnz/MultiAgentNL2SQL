"""
Base agent interfaces for the multi-agent NL→SQL system.
All specialized agents inherit from these abstract base classes.
"""

from abc import ABC, abstractmethod


# -------------------------------------------------------------------
# BaseAgent
# -------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Master abstract class for all agent types.
    Provides:
      - name
      - kind
      - base async run wrapper
    """

    kind: str = "base"
    name: str = "BaseAgent"

    def __init__(self, name: str = None):
        if name:
            self.name = name

    async def run(self, *args, **kwargs):
        """
        Default behavior — subclasses override.
        If called directly, raise explicit error.
        """
        raise NotImplementedError(
            f"Agent '{self.name}' must override run()"
        )


# -------------------------------------------------------------------
# SQL Generation Agents
# -------------------------------------------------------------------

class BaseGenerationAgent(BaseAgent):
    """
    SQL Generation Agents (G1–G7).
    Implement:
        async def generate(question, context) -> str
    """

    kind = "generation"

    @abstractmethod
    async def generate(self, question: str, context: dict) -> str:
        pass

    async def run(self, question: str, context: dict):
        return await self.generate(question, context)


# -------------------------------------------------------------------
# SQL Repair Agents
# -------------------------------------------------------------------

class BaseRepairAgent(BaseAgent):
    """
    Repair agents (R1–R10).
    Implement:
        async def repair(sql, diagnostics) -> str
    """

    kind = "repair"

    @abstractmethod
    async def repair(self, sql: str, diagnostics: dict) -> str:
        pass

    async def run(self, sql: str, diagnostics: dict):
        return await self.repair(sql, diagnostics)


# -------------------------------------------------------------------
# Table Selector Agents
# -------------------------------------------------------------------

class BaseSelectorAgent(BaseAgent):
    """
    Selector agents choose tables relevant to a question.
    Return format:
        {
            "tables": [...],
            "score": float,
            "source": "semantic" | "heuristic" | "graph"
        }
    """

    kind = "selector"

    @abstractmethod
    async def select(self, question: str, schema: dict) -> dict:
        pass

    async def run(self, question: str, schema: dict):
        return await self.select(question, schema)


# -------------------------------------------------------------------
# Semantic Validator Agents
# -------------------------------------------------------------------

class BaseValidatorAgent(BaseAgent):
    """
    Validators determine if SQL answers the question.
    Must return:
        {
            "valid": True/False,
            "score": float,
            "reason": "..."
        }
    """

    kind = "validator"

    @abstractmethod
    async def validate(self, question: str, sql: str) -> dict:
        pass

    async def run(self, question: str, sql: str):
        return await self.validate(question, sql)
