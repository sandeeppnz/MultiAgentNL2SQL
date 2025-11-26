class settings:
    # 1. “OpenAI-only mode” for cloud deployment
    USE_SLM_REPAIR = False           
    ENABLE_SLM_GENERATORS = False     


    # 2. “Hybrid mode” for max accuracy and cost savings
    # USE_SLM_REPAIR = True            
    # ENABLE_SLM_GENERATORS = True    
    # OPENAI=False (optional)

    OLLAMA_HOST="http://localhost:11434"


# USE_SLM_REPAIR=False
#     → Only OpenAI repair agents (R8–R10) run.
#       Recommended for production.

# USE_SLM_REPAIR=True
#     → Also run local SLM repair agents (R1–R7).
#       Good for dev, debugging, cost-saving.


# ENABLE_SLM_GENERATORS=False
#     → Only G1–G5 OpenAI generators are used.

# ENABLE_SLM_GENERATORS=True
#     → Add G6 + G7 Ollama generators.