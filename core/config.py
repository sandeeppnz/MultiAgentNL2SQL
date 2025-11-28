import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Always load from closest .env
load_dotenv(find_dotenv())


def flag(name: str, default: bool = False) -> bool:
    """Helper for boolean env flags."""
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "y")


class settings:
    # ============================================================
    # Feature Flags
    # ============================================================
    USE_SLM_REPAIR = flag("USE_SLM_REPAIR", False)
    ENABLE_SLM_GENERATORS = flag("ENABLE_SLM_GENERATORS", False)

    # ============================================================
    # OpenAI Configuration
    # ============================================================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

    # Normalize base URL (remove trailing slash)
    raw_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_API_BASE = raw_base.rstrip("/")

    # Default model
    OPENAI_MODEL = os.getenv(
        "OPENAI_MODEL",
        "gpt-4o-mini"     # safer + fastest + stable
    )

    # ============================================================
    # Ollama Configuration
    # ============================================================
    raw_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_HOST = raw_host.rstrip("/")

    # Default local model
    OLLAMA_MODEL = os.getenv(
        "OLLAMA_MODEL",
        "llama3.1:8b"   # safe default for validation/generation
    ).strip()

    # ============================================================
    # Database
    # ============================================================
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

    # ============================================================
    # Sanity checks (optional but useful)
    # ============================================================
    if not OPENAI_API_KEY:
        print("⚠ WARNING: OPENAI_API_KEY is empty!")

    if ENABLE_SLM_GENERATORS and not OLLAMA_MODEL:
        print("⚠ WARNING: ENABLE_SLM_GENERATORS=True but OLLAMA_MODEL is empty!")

    if DATABASE_URL == "":
        print("⚠ WARNING: DATABASE_URL is empty!")



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