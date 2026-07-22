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
    conn.commit()

    count = cur.execute("SELECT COUNT(*) FROM models").fetchone()[0]
    print(f"Inserted {count} rows into {DB_PATH.name}")
    conn.close()


if __name__ == "__main__":
    main()