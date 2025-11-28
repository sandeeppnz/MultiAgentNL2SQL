import aiohttp

from core.config import settings

class OpenAIClient:
    def __init__(self, model=None):
        self.api_key = settings.OPENAI_API_KEY
        base = settings.OPENAI_API_BASE.rstrip("/") or "https://api.openai.com/v1"
        self.url = f"{base}/chat/completions"
        self.model = model or settings.OPENAI_MODEL

        # FIX: proper total timeout
        self.session_timeout = aiohttp.ClientTimeout(total=12)

    async def acomplete(self, prompt, temperature=0.0):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert SQL generator."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
        }

        async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
            try:
                async with session.post(self.url, headers=headers, json=data) as resp:
                    js = await resp.json()
                    return js["choices"][0]["message"]["content"]
            except Exception:
                return None
