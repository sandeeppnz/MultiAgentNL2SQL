# llm/ollama_client.py
import aiohttp
import asyncio
from core.config import settings

class OllamaClient:
    def __init__(self, model: str = "llama3", timeout: int = 20):
        self.model = model
        self.url = f"{settings.OLLAMA_HOST}/api/generate"
        self.timeout = timeout

    async def acomplete(self, prompt: str, temperature: float = 0.0):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.url, json=payload, timeout=self.timeout) as resp:
                    data = await resp.json()
                    return data.get("response")
            except asyncio.TimeoutError:
                return None
            except Exception:
                return None
