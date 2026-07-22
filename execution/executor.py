import sys
import time
from pathlib import Path

from registry import get_adapter

sys.path.insert(0, str(Path(__file__).parent.parent / "analytics"))
sys.path.insert(0, str(Path(__file__).parent.parent / "router"))
from logger import log_request  # noqa: E402
from router import get_cheapest  # noqa: E402


def execute(routed_result: dict, **generate_kwargs) -> dict:
    """Take a pipeline.handle_prompt() result and actually call a model,
    walking the fallback chain if a provider has no adapter, no health, or errors."""
    prompt = routed_result["prompt"]
    difficulty = routed_result.get("difficulty")
    candidates = [routed_result["chosen_model"], *routed_result["fallbacks"]]

    attempts = []
    for candidate in candidates:
        provider = candidate["provider"]
        model_name = candidate["model_name"]
        adapter = get_adapter(provider)

        if adapter is None:
            attempts.append({"provider": provider, "model_name": model_name, "error": "no adapter registered"})
            continue

        try:
            start = time.time()
            text = adapter.generate(prompt, model_name, **generate_kwargs)
            latency_ms = (time.time() - start) * 1000

            input_tokens = adapter.token_count(prompt)
            output_tokens = adapter.token_count(text)

            cheapest = get_cheapest(difficulty) if difficulty else None
            actual_cost, baseline_cost, cheapest_cost = log_request(
                prompt, difficulty, provider, model_name,
                input_tokens, output_tokens,
                candidate["cost_input_per_1m"], candidate["cost_output_per_1m"],
                latency_ms, cheapest=cheapest,
            )

            is_cheapest = cheapest and cheapest["provider"] == provider and cheapest["model_name"] == model_name

            return {
                "prompt": prompt,
                "provider": provider,
                "model_name": model_name,
                "response": text,
                "attempts": attempts,
                "actual_cost": actual_cost,
                "baseline_cost": baseline_cost,
                "saved": baseline_cost - actual_cost,
                "cheapest": cheapest,
                "cheapest_cost": cheapest_cost,
                "is_cheapest": is_cheapest,
            }
        except Exception as e:
            attempts.append({"provider": provider, "model_name": model_name, "error": str(e)})
            continue

    return {
        "prompt": prompt,
        "provider": None,
        "model_name": None,
        "response": None,
        "attempts": attempts,
        "error": "all candidates failed",
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    sys.path.insert(0, str(Path(__file__).parent.parent / "router"))
    sys.path.insert(0, str(Path(__file__).parent.parent / "classifier"))
    from pipeline import handle_prompt

    prompt = " ".join(sys.argv[1:]) or "How do I center a div in CSS?"
    routed = handle_prompt(prompt, top_n=5)
    result = execute(routed)

    print(f"Prompt: {prompt}")
    print(f"Difficulty: {routed['difficulty']}\n")

    if result["response"]:
        print(f"Served by: {result['provider']}/{result['model_name']}\n")
        print(result["response"])
        print(f"\n---\nCost: ${result['actual_cost']:.6f}  "
              f"(baseline: ${result['baseline_cost']:.6f})  "
              f"Saved: ${result['saved']:.6f}")

        if result["cheapest"]:
            if result["is_cheapest"]:
                print("This was already the cheapest available option for this difficulty tier.")
            else:
                c = result["cheapest"]
                print(f"Cheapest option for '{routed['difficulty']}' would be "
                      f"{c['provider']}/{c['model_name']} (${result['cheapest_cost']:.6f}) — "
                      f"not used because we don't have a working adapter/key for it.")
    else:
        print("All candidates failed.")

    if result["attempts"]:
        print("\nSkipped/failed before success:")
        for a in result["attempts"]:
            print(f"  {a['provider']}/{a['model_name']}: {a['error']}")