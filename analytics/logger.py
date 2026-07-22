import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "llm_cost.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS requests_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT,
    difficulty TEXT,
    provider TEXT,
    model_name TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    actual_cost REAL,
    baseline_provider TEXT,
    baseline_model_name TEXT,
    baseline_cost REAL,
    cheapest_provider TEXT,
    cheapest_model_name TEXT,
    cheapest_cost REAL,
    latency_ms REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def _ensure_table(conn):
    conn.execute(SCHEMA)


def get_baseline_model(conn):
    """The most expensive model in the catalog — what we'd pay if every
    request just went to the biggest, priciest model with no routing at all."""
    row = conn.execute(
        """
        SELECT provider, model_name, cost_input_per_1m, cost_output_per_1m
        FROM models
        ORDER BY (cost_input_per_1m + cost_output_per_1m) DESC
        LIMIT 1
        """
    ).fetchone()
    return row  # (provider, model_name, cost_input_per_1m, cost_output_per_1m)


def log_request(prompt, difficulty, provider, model_name, input_tokens, output_tokens,
                 cost_input_per_1m, cost_output_per_1m, latency_ms, cheapest=None):
    conn = sqlite3.connect(DB_PATH)
    _ensure_table(conn)

    actual_cost = (input_tokens / 1_000_000) * cost_input_per_1m + \
                  (output_tokens / 1_000_000) * cost_output_per_1m

    baseline_provider, baseline_model, b_cost_in, b_cost_out = get_baseline_model(conn)
    baseline_cost = (input_tokens / 1_000_000) * b_cost_in + \
                     (output_tokens / 1_000_000) * b_cost_out

    if cheapest:
        cheapest_provider = cheapest["provider"]
        cheapest_model = cheapest["model_name"]
        cheapest_cost = (input_tokens / 1_000_000) * cheapest["cost_input_per_1m"] + \
                         (output_tokens / 1_000_000) * cheapest["cost_output_per_1m"]
    else:
        cheapest_provider = provider
        cheapest_model = model_name
        cheapest_cost = actual_cost

    conn.execute(
        """
        INSERT INTO requests_log (
            prompt, difficulty, provider, model_name,
            input_tokens, output_tokens, actual_cost,
            baseline_provider, baseline_model_name, baseline_cost,
            cheapest_provider, cheapest_model_name, cheapest_cost,
            latency_ms
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (prompt, difficulty, provider, model_name, input_tokens, output_tokens, actual_cost,
         baseline_provider, baseline_model, baseline_cost,
         cheapest_provider, cheapest_model, cheapest_cost, latency_ms),
    )
    conn.commit()
    conn.close()
    return actual_cost, baseline_cost, cheapest_cost