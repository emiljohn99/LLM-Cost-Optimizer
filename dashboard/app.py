import sqlite3
from pathlib import Path

from flask import Flask, render_template

DB_PATH = Path(__file__).parent.parent / "data" / "llm_cost.db"

app = Flask(__name__)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def dashboard():
    conn = get_conn()

    total = conn.execute("SELECT COUNT(*) AS n FROM requests_log").fetchone()["n"]

    if total == 0:
        conn.close()
        return render_template("index.html", total=0)

    totals = conn.execute(
        "SELECT SUM(actual_cost) AS actual, SUM(baseline_cost) AS baseline, "
        "SUM(cheapest_cost) AS cheapest, AVG(latency_ms) AS avg_latency FROM requests_log"
    ).fetchone()
    actual = totals["actual"] or 0
    baseline = totals["baseline"] or 0
    cheapest_total = totals["cheapest"] or actual
    saved = baseline - actual
    pct = (saved / baseline * 100) if baseline else 0
    missed = actual - cheapest_total
    missed_pct = (missed / actual * 100) if actual else 0

    by_difficulty = conn.execute(
        """
        SELECT difficulty, COUNT(*) AS n, SUM(actual_cost) AS actual, SUM(baseline_cost) AS baseline
        FROM requests_log GROUP BY difficulty ORDER BY n DESC
        """
    ).fetchall()

    by_model = conn.execute(
        """
        SELECT provider, model_name, COUNT(*) AS n, SUM(actual_cost) AS actual
        FROM requests_log GROUP BY provider, model_name ORDER BY n DESC
        """
    ).fetchall()

    missing_adapters = conn.execute(
        """
        SELECT cheapest_provider AS provider, cheapest_model_name AS model_name,
               COUNT(*) AS n, SUM(actual_cost - cheapest_cost) AS missed_cost
        FROM requests_log
        WHERE provider != cheapest_provider OR model_name != cheapest_model_name
        GROUP BY cheapest_provider, cheapest_model_name
        ORDER BY missed_cost DESC
        """
    ).fetchall()

    recent = conn.execute(
        """
        SELECT prompt, difficulty, provider, model_name, actual_cost, saved_amount, latency_ms, created_at
        FROM (
            SELECT *, (baseline_cost - actual_cost) AS saved_amount FROM requests_log
        )
        ORDER BY id DESC LIMIT 20
        """
    ).fetchall()

    avg_saved_per_request = saved / total
    monthly_projection = [
        ("1k req/day", avg_saved_per_request * 1000 * 30),
        ("10k req/day", avg_saved_per_request * 10000 * 30),
        ("100k req/day", avg_saved_per_request * 100000 * 30),
    ]

    conn.close()

    return render_template(
        "index.html",
        total=total,
        actual=actual,
        baseline=baseline,
        saved=saved,
        pct=pct,
        cheapest_total=cheapest_total,
        missed=missed,
        missed_pct=missed_pct,
        avg_latency=totals["avg_latency"],
        by_difficulty=by_difficulty,
        by_model=by_model,
        missing_adapters=missing_adapters,
        recent=recent,
        monthly_projection=monthly_projection,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)