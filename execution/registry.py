from claude_adapter import ClaudeAdapter
from gemini_adapter import GeminiAdapter
from groq_adapter import GroqAdapter
from ollama_adapter import OllamaAdapter
from openai_adapter import OpenAIAdapter

# Maps the `provider` string stored in the models table to an adapter instance.
# Providers without a real adapter yet fall through to None (executor skips them).
_REGISTRY = {
    "OpenAI": OpenAIAdapter(),
    "Anthropic": ClaudeAdapter(),
    "Google": GeminiAdapter(),
    "Groq": GroqAdapter(),
    "Ollama": OllamaAdapter(),
}


def get_adapter(provider: str):
    return _REGISTRY.get(provider)