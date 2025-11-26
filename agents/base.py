"""
Base agent interfaces for the multi-agent NL→SQL system.
All specialized agents (generation, repair, selector, validator)
will inherit from these base classes.
"""

from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Parent class for all agents."""

    @abstractmethod
    async def run(self, *args, **kwargs):
        """Run the agent logic asynchronously."""
        pass


# -------------------------------------------------------------------
# SQL Generation Agents
# -------------------------------------------------------------------

class BaseGenerationAgent(BaseAgent):
    """
    SQL Generation Agents (G1–G5).
    Each agent uses a different prompting strategy or LLM configuration.
    """

    @abstractmethod
    async def generate(self, question: str, context: dict) -> str:
        """
        Generate SQL based on question + context (tables, schema, rules).
        Must be implemented by each generation agent.
        """
        pass

    async def run(self, question: str, context: dict):
        """Uniform run() wrapper for all generation agents."""
        return await self.generate(question, context)


# -------------------------------------------------------------------
# SQL Repair Agents
# -------------------------------------------------------------------

class BaseRepairAgent(BaseAgent):
    """
    SQL Repair Agents (R1–R7).
    These agents take invalid SQL + diagnostics, and attempt to repair it.
    Example:
        - grammar fix
        - join fix
        - missing dim fix
        - column rename fix
        - GROUP BY fix
    """

    @abstractmethod
    async def repair(self, sql: str, diagnostics: dict) -> str:
        """
        Attempt to produce a corrected SQL string.
        """
        pass

    async def run(self, sql: str, diagnostics: dict):
        """Uniform run() wrapper for all repair agents."""
        return await self.repair(sql, diagnostics)


# -------------------------------------------------------------------
# Table Selector Agents
# -------------------------------------------------------------------

class BaseSelectorAgent(BaseAgent):
    """
    Table selector agents (semantic, heuristic, graph-based).
    Each agent returns:
        {
          "tables": [...],
          "score": float,
          "source": "semantic" / "heuristic" / "graph"
        }
    """

    @abstractmethod
    async def select(self, question: str, schema: dict) -> dict:
        """
        Return selected tables + score.
        """
        pass

    async def run(self, question: str, schema: dict):
        """Uniform run() wrapper for all selector agents."""
        return await self.select(question, schema)


# -------------------------------------------------------------------
# Semantic Validator Agents
# -------------------------------------------------------------------

class BaseValidatorAgent(BaseAgent):
    """
    Semantic intent validators.
    These agents answer:
        - Does this SQL answer the question?
        - Is there a missing join?
        - Is the grain correct?
        - Should columns be grouped?
    """

    @abstractmethod
    async def validate(self, question: str, sql: str) -> dict:
        """
        Return validation result:
        {
            "valid": True/False,
            "reason": "...",
            "score": float
        }
        """
        pass

    async def run(self, question: str, sql: str):
        """Uniform run() wrapper for all validator agents."""
        return await self.validate(question, sql)
