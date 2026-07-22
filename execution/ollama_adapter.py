import time

import requests

from base import LLMProvider


class OllamaAdapter(LLMProvider):
    provider_name = "Ollama"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def generate(self, prompt: str, model_name: str, **kwargs) -> str:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False, **kwargs},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def stream(self, prompt: str, model_name: str, **kwargs):
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": True, **kwargs},
            timeout=120,
            stream=True,
        )
        resp.raise_for_status()
        import json
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                if chunk.get("response"):
                    yield chunk["response"]

    def embeddings(self, text: str, model_name: str = "nomic-embed-text") -> list:
        resp = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": model_name, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    def health(self) -> dict:
        start = time.time()
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            return {"available": True, "latency_ms": (time.time() - start) * 1000, "error": None}
        except Exception as e:
            return {"available": False, "latency_ms": None, "error": str(e)}