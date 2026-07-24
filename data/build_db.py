import re
import sqlite3
from pathlib import Path

SQL_PATH = Path(__file__).parent / "llmcost.sql"
DB_PATH = Path(__file__).parent / "llm_cost.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    category TEXT,
    cost_input_per_1m REAL,
    cost_output_per_1m REAL,
    avg_latency_ms INTEGER,
    max_context_tokens INTEGER,
    reasoning_score REAL,
    coding_score REAL,
    vision_score REAL,
    supports_vision INTEGER,
    supports_function_calling INTEGER,
    supports_streaming INTEGER,
    supports_json INTEGER,
    health_score REAL,
    success_rate REAL,
    is_active INTEGER DEFAULT 1
);
"""

ROW_RE = re.compile(
    r"\('([^']*)','([^']*)','([^']*)',"
    r"([\d.]+),([\d.]+),(\d+),(\d+),"
    r"([\d.]+),([\d.]+),([\d.]+),"
    r"(TRUE|FALSE),(TRUE|FALSE),(TRUE|FALSE),(TRUE|FALSE),"
    r"([\d.]+),([\d.]+)\)"
)


def parse_rows(sql_text):
    rows = []
    for m in ROW_RE.finditer(sql_text):
        vals = list(m.groups())
        bool_idx = [10, 11, 12, 13]
        for i in bool_idx:
            vals[i] = 1 if vals[i] == "TRUE" else 0
        rows.append(vals)
    return rows


# Model names in llmcost.sql that turned out to be outdated once we tested
# against the real provider APIs. Applied after the base import.
MODEL_NAME_FIXES = [
    ("DeepSeek", "deepseek-r1", "deepseek-v4-pro"),
    ("DeepSeek", "deepseek-v3", "deepseek-v4-flash"),
    ("Google", "gemini-2.5-flash", "gemini-flash-latest"),
]

# Providers/models we actually have working adapters for but that weren't in
# the original llmcost.sql dataset (Groq, and local Ollama models).
EXTRA_ROWS = [
    ("Groq", "llama-3.1-8b-instant", "Fast", 0.05, 0.08, 300, 128000, 7.8, 7.9, 0.0, 0, 1, 1, 1, 99.9, 99.8),
    ("Groq", "llama-3.3-70b-versatile", "Balanced", 0.59, 0.79, 450, 128000, 9.0, 8.9, 0.0, 0, 1, 1, 1, 99.9, 99.8),
    ("Groq", "openai/gpt-oss-120b", "Premium", 0.15, 0.75, 600, 128000, 9.3, 9.2, 0.0, 0, 1, 1, 1, 99.9, 99.8),
    ("Ollama", "llama3.2:1b", "Budget", 0.0, 0.0, 13000, 128000, 6.5, 6.0, 0.0, 0, 0, 1, 0, 99.0, 98.0),
    ("Ollama", "qwen2.5-coder:7b", "Balanced", 0.0, 0.0, 28000, 32000, 8.0, 8.8, 0.0, 0, 0, 1, 0, 98.5, 97.5),
    ("Ollama", "phi3:mini", "Budget", 0.0, 0.0, 19000, 128000, 7.5, 7.3, 0.0, 0, 0, 1, 0, 98.5, 97.5),
]


def main():
    sql_text = SQL_PATH.read_text(encoding="utf-8")
    rows = parse_rows(sql_text)
    print(f"Parsed {len(rows)} model rows from {SQL_PATH.name}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.execute("DELETE FROM models")

    cur.executemany(
        """
        INSERT INTO models (
            provider, model_name, category,
            cost_input_per_1m, cost_output_per_1m,
            avg_latency_ms, max_context_tokens,
            reasoning_score, coding_score, vision_score,
            supports_vision, supports_function_calling, supports_streaming, supports_json,
            health_score, success_rate
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )

    for provider, old_name, new_name in MODEL_NAME_FIXES:
        cur.execute(
            "UPDATE models SET model_name = ? WHERE provider = ? AND model_name = ?",
            (new_name, provider, old_name),
        )

    cur.executemany(
        """
        INSERT INTO models (
            provider, model_name, category,
            cost_input_per_1m, cost_output_per_1m,
            avg_latency_ms, max_context_tokens,
            reasoning_score, coding_score, vision_score,
            supports_vision, supports_function_calling, supports_streaming, supports_json,
            health_score, success_rate
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        EXTRA_ROWS,
    )

    conn.commit()

    count = cur.execute("SELECT COUNT(*) FROM models").fetchone()[0]
    print(f"Inserted {count} rows into {DB_PATH.name} (base + {len(EXTRA_ROWS)} extra, {len(MODEL_NAME_FIXES)} renamed)")
    conn.close()


if __name__ == "__main__":
    main()