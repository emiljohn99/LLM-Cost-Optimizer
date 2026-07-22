import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "llm_cost.db"

# Which model categories are eligible candidates for each difficulty tier.
DIFFICULTY_TO_CATEGORIES = {
    "simple": ["Budget", "Small", "Fast"],
    "medium": ["Balanced", "General", "Enterprise"],
    "hard": ["Premium", "Reasoning"],
}

# Scoring weights: score = quality - LAMBDA * cost_norm - MU * latency_norm
LAMBDA = 0.4
MU = 0.2
QUALITY_WEIGHT = 0.6


def _fetch_candidates(categories):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" for _ in categories)
    rows = conn.execute(
        f"""
        SELECT * FROM models
        WHERE category IN ({placeholders}) AND is_active = 1
        """,
        categories,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _normalize(values):
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def route(difficulty: str, top_n: int = 3):
    categories = DIFFICULTY_TO_CATEGORIES.get(difficulty)
    if categories is None:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    candidates = _fetch_candidates(categories)
    if not candidates:
        raise RuntimeError(f"No models available for difficulty '{difficulty}'")

    quality_raw = [(c["coding_score"] + c["reasoning_score"]) / 2 for c in candidates]
    cost_raw = [c["cost_input_per_1m"] + c["cost_output_per_1m"] for c in candidates]
    latency_raw = [c["avg_latency_ms"] for c in candidates]

    quality_norm = _normalize(quality_raw)
    cost_norm = _normalize(cost_raw)
    latency_norm = _normalize(latency_raw)

    scored = []
    for c, q, cost, lat in zip(candidates, quality_norm, cost_norm, latency_norm):
        score = QUALITY_WEIGHT * q - LAMBDA * cost - MU * lat
        scored.append({
            "provider": c["provider"],
            "model_name": c["model_name"],
            "category": c["category"],
            "cost_input_per_1m": c["cost_input_per_1m"],
            "cost_output_per_1m": c["cost_output_per_1m"],
            "avg_latency_ms": c["avg_latency_ms"],
            "coding_score": c["coding_score"],
            "reasoning_score": c["reasoning_score"],
            "score": round(score, 4),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]


def get_cheapest(difficulty: str):
    """The single lowest cost_input+cost_output model in this difficulty's
    category set — regardless of whether we actually have an adapter/key for it."""
    categories = DIFFICULTY_TO_CATEGORIES.get(difficulty)
    if categories is None:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    candidates = _fetch_candidates(categories)
    if not candidates:
        return None

    cheapest = min(candidates, key=lambda c: c["cost_input_per_1m"] + c["cost_output_per_1m"])
    return {
        "provider": cheapest["provider"],
        "model_name": cheapest["model_name"],
        "cost_input_per_1m": cheapest["cost_input_per_1m"],
        "cost_output_per_1m": cheapest["cost_output_per_1m"],
    }


if __name__ == "__main__":
    import sys

    difficulty = sys.argv[1] if len(sys.argv) > 1 else "hard"
    ranked = route(difficulty)
    print(f"Difficulty: {difficulty}\n")
    for i, m in enumerate(ranked, 1):
        print(f"{i}. {m['provider']}/{m['model_name']}  score={m['score']}  "
              f"cost_in={m['cost_input_per_1m']}  cost_out={m['cost_output_per_1m']}  "
              f"latency={m['avg_latency_ms']}ms  coding={m['coding_score']}  reasoning={m['reasoning_score']}")