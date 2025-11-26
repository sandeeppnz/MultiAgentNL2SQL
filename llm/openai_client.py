# llm/openai_client.py
import asyncio
import aiohttp
import json
from core.config import settings

class OpenAIClient:
    def __init__(self, model: str = "gpt-4.1-mini", timeout: int = 30):
        self.api_key = settings.OPENAI_API_KEY
        self.url = "https://api.openai.com/v1/chat/completions"
        self.model = model
        self.timeout = timeout

    async def acomplete(self, prompt: str, temperature: float = 0.0):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert SQL generator."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                ) as resp:
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]
            except asyncio.TimeoutError:
                return None
            except Exception as e:
                return None
