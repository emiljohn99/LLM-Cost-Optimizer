import os
import time

from base import LLMProvider


class GroqAdapter(LLMProvider):
    provider_name = "Groq"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, model_name: str, **kwargs) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return response.choices[0].message.content

    def stream(self, prompt: str, model_name: str, **kwargs):
        client = self._get_client()
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs,
        )
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def embeddings(self, text: str, model_name: str) -> list:
        raise NotImplementedError("Groq does not offer an embeddings API.")

    def health(self) -> dict:
        if not self.api_key:
            return {"available": False, "latency_ms": None, "error": "no API key set"}
        start = time.time()
        try:
            client = self._get_client()
            client.models.list()
            return {"available": True, "latency_ms": (time.time() - start) * 1000, "error": None}
        except Exception as e:
            return {"available": False, "latency_ms": None, "error": str(e)}