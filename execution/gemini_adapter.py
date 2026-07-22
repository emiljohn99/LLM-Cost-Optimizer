import os
import time

from base import LLMProvider


class GeminiAdapter(LLMProvider):
    provider_name = "Google"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self._configured = False

    def _configure(self):
        if not self._configured:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._configured = True

    def generate(self, prompt: str, model_name: str, **kwargs) -> str:
        import google.generativeai as genai
        self._configure()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, **kwargs)
        return response.text

    def stream(self, prompt: str, model_name: str, **kwargs):
        import google.generativeai as genai
        self._configure()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, stream=True, **kwargs)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def embeddings(self, text: str, model_name: str = "models/text-embedding-004") -> list:
        import google.generativeai as genai
        self._configure()
        result = genai.embed_content(model=model_name, content=text)
        return result["embedding"]

    def health(self) -> dict:
        if not self.api_key:
            return {"available": False, "latency_ms": None, "error": "no API key set"}
        start = time.time()
        try:
            import google.generativeai as genai
            self._configure()
            list(genai.list_models())
            return {"available": True, "latency_ms": (time.time() - start) * 1000, "error": None}
        except Exception as e:
            return {"available": False, "latency_ms": None, "error": str(e)}