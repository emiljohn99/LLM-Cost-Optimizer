import os
import time

from base import LLMProvider


class ClaudeAdapter(LLMProvider):
    provider_name = "Anthropic"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, model_name: str, max_tokens: int = 1024, **kwargs) -> str:
        client = self._get_client()
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return response.content[0].text

    def stream(self, prompt: str, model_name: str, max_tokens: int = 1024, **kwargs):
        client = self._get_client()
        with client.messages.stream(
            model=model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def embeddings(self, text: str, model_name: str = "voyage-3") -> list:
        raise NotImplementedError("Anthropic does not offer a native embeddings API; use Voyage AI directly.")

    def health(self) -> dict:
        if not self.api_key:
            return {"available": False, "latency_ms": None, "error": "no API key set"}
        start = time.time()
        try:
            client = self._get_client()
            client.messages.create(
                model="claude-haiku-4",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return {"available": True, "latency_ms": (time.time() - start) * 1000, "error": None}
        except Exception as e:
            return {"available": False, "latency_ms": None, "error": str(e)}