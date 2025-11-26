from agents.repair_agents import (
    OpenAIGeneralRepairAgent,
    OpenAIJoinRepairAgent,
    OpenAISemanticRepairAgent
)

self.repair_agents = [
    OpenAIGeneralRepairAgent(),
    OpenAIJoinRepairAgent(),
    OpenAISemanticRepairAgent()
]


self.repair_agents = []

if USE_SLM_REPAIR:
    self.repair_agents.extend([
        GrammarFixAgent(),
        JoinRepairAgent(),
        ColumnFixAgent(),
        GroupByRepairAgent(),
        DimCompletionAgent(),
        ASTCanonicalRepairAgent(),
        SemanticRepairAgent(),
    ])

# Add OpenAI repair agents always
self.repair_agents.extend([
    OpenAIGeneralRepairAgent(),
    OpenAIJoinRepairAgent(),
    OpenAISemanticRepairAgent()
])