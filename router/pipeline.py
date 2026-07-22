import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "classifier"))

from predict import classify  # noqa: E402
from router import route  # noqa: E402


def handle_prompt(prompt: str, top_n: int = 3):
    difficulty, class_scores = classify(prompt)
    ranked_models = route(difficulty, top_n=top_n)
    return {
        "prompt": prompt,
        "difficulty": difficulty,
        "difficulty_scores": class_scores,
        "chosen_model": ranked_models[0],
        "fallbacks": ranked_models[1:],
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    prompt = " ".join(sys.argv[1:]) or "Design a distributed rate limiter across multiple data centers."
    result = handle_prompt(prompt)

    print(f"Prompt: {result['prompt']}")
    print(f"Difficulty: {result['difficulty']}  ({result['difficulty_scores']})\n")

    chosen = result["chosen_model"]
    print(f"Chosen model: {chosen['provider']}/{chosen['model_name']}  (score={chosen['score']})")

    print("\nFallbacks:")
    for m in result["fallbacks"]:
        print(f"  {m['provider']}/{m['model_name']}  (score={m['score']})")