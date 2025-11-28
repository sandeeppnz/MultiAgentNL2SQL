# llm/ollama_client.py
import aiohttp
import asyncio
from core.config import settings
from core.utils.logger import get_logger

logger = get_logger("OllamaClient")


class OllamaClient:
    """
    Safe Ollama async client.
    Ensures:
      - always returns a string or None
      - does not crash on bad responses
      - logs failures for debugging
    """

    def __init__(self, model: str | None = None, timeout: int = 20):
        self.model = model or settings.OLLAMA_MODEL
        self.url = f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate"
        self.timeout = timeout

    async def acomplete(self, prompt: str, temperature: float = 0.0):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    json=payload,
                    timeout=self.timeout
                ) as resp:

                    # -------------------------
                    # Check HTTP status
                    # -------------------------
                    if resp.status != 200:
                        txt = await resp.text()
                        logger.error(f"Ollama HTTP {resp.status}: {txt[:500]}")
                        return None

                    # -------------------------
                    # Parse JSON safely
                    # -------------------------
                    try:
                        data = await resp.json()
                    except Exception:
                        txt = await resp.text()
                        logger.error(f"Ollama JSON parse error: {txt[:500]}")
                        return None

                    # -------------------------
                    # Extract response safely
                    # -------------------------
                    # Normal Ollama format: {"response": "..."}
                    if isinstance(data, dict):
                        if "response" in data:
                            return data["response"]

                        # Some models return {"message": {"content": "..."}}
                        msg = data.get("message")
                        if isinstance(msg, dict):
                            return msg.get("content")

                        # Some return {"content": "..."}
                        if "content" in data:
                            return data["content"]

                        logger.error(f"Ollama unexpected response structure: {data}")
                        return None

                    return None

        except asyncio.TimeoutError:
            logger.error("Ollama timeout")
            return None

        except Exception as e:
            logger.error(f"Ollama exception: {e}")
            return None
