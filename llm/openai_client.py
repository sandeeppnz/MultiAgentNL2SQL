# llm/openai_client.py
import asyncio
import aiohttp
import json
from core.config import settings
from core.utils.logger import get_logger

logger = get_logger("OpenAIClient")


class OpenAIClient:
    def __init__(self, model: str | None = None, timeout: int = 30):
        self.api_key = settings.OPENAI_API_KEY
        base = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
        self.url = f"{base.rstrip('/')}/chat/completions"
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout

    async def acomplete(self, prompt: str, temperature: float = 0.0):
        """
        SAFE async completion.
        Returns:
          - string (content)
          - None (on failure)
        Never raises.
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert SQL assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                ) as resp:

                    # -----------------------------
                    # Check HTTP status
                    # -----------------------------
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"OpenAI HTTP {resp.status}: {text[:500]}")
                        return None

                    # -----------------------------
                    # Parse JSON safely
                    # -----------------------------
                    try:
                        data = await resp.json()
                    except Exception:
                        txt = await resp.text()
                        logger.error(f"OpenAI JSON parse failure: {txt[:500]}")
                        return None

                    # -----------------------------
                    # Extract content safely
                    # -----------------------------
                    try:
                        # new format
                        if "choices" in data and data["choices"]:
                            choice = data["choices"][0]

                            # OpenAI Python API v1
                            if isinstance(choice, dict):
                                msg = choice.get("message")
                                if isinstance(msg, dict):
                                    return msg.get("content", "").strip()

                                # stream delta format (sometimes returned)
                                delta = choice.get("delta")
                                if isinstance(delta, dict):
                                    return delta.get("content", "").strip()

                        logger.error(f"OpenAI returned unexpected structure: {data}")
                        return None

                    except Exception as e:
                        logger.error(f"OpenAI message extraction error: {e}")
                        return None

        except asyncio.TimeoutError:
            logger.error("OpenAI timeout")
            return None

        except Exception as e:
            logger.error(f"OpenAI request exception: {e}")
            return None
