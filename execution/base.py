from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class LLMProvider(ABC):
    """Common interface every provider adapter must implement.
    The router only ever talks to this interface, never to a specific SDK."""

    provider_name: str = "base"

    @abstractmethod
    def generate(self, prompt: str, model_name: str, **kwargs) -> str:
        """Send a prompt, return the full text response."""
        raise NotImplementedError

    @abstractmethod
    def stream(self, prompt: str, model_name: str, **kwargs):
        """Send a prompt, yield text chunks as they arrive."""
        raise NotImplementedError

    @abstractmethod
    def embeddings(self, text: str, model_name: str) -> list:
        """Return an embedding vector for text."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict:
        """Return {'available': bool, 'latency_ms': float|None, 'error': str|None}."""
        raise NotImplementedError

    def cost(self, input_tokens: int, output_tokens: int, cost_input_per_1m: float, cost_output_per_1m: float) -> float:
        """Compute request cost in dollars given token counts and per-1M rates."""
        return (input_tokens / 1_000_000) * cost_input_per_1m + (output_tokens / 1_000_000) * cost_output_per_1m

    def token_count(self, text: str) -> int:
        """Rough token estimate (chars / 4). Adapters may override with a real tokenizer."""
        return max(1, len(text) // 4)