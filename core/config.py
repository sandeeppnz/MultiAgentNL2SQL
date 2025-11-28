import os


class settings:
    # 1. “OpenAI-only mode” for cloud deployment
    USE_SLM_REPAIR = os.getenv("USE_SLM_REPAIR", "False").lower() == "true"

    ENABLE_SLM_GENERATORS =  os.getenv("ENABLE_SLM_GENERATORS", "False").lower() == "true"

    # API credentials / endpoints
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")  # optional override
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    DATABASE_URL = os.getenv("DATABASE_URL","")


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