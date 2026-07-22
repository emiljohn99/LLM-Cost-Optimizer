import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "llm_cost.db"


def print_report():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) AS n FROM requests_log").fetchone()["n"]
    if total == 0:
        print("No requests logged yet. Run execution/executor.py with some prompts first.")
        return

    totals = conn.execute(
        "SELECT SUM(actual_cost) AS actual, SUM(baseline_cost) AS baseline, "
        "SUM(cheapest_cost) AS cheapest, AVG(latency_ms) AS avg_latency FROM requests_log"
    ).fetchone()
    actual = totals["actual"] or 0
    baseline = totals["baseline"] or 0
    cheapest = totals["cheapest"] or actual
    saved = baseline - actual
    pct = (saved / baseline * 100) if baseline else 0
    missed = actual - cheapest
    missed_pct = (missed / actual * 100) if actual else 0

    print("=" * 50)
    print("LLM COST OPTIMIZER — ANALYTICS")
    print("=" * 50)
    print(f"Total requests:        {total}")
    print(f"Avg latency:           {totals['avg_latency']:.0f} ms")
    print()
    print(f"Actual cost:           ${actual:.6f}")
    print(f"Baseline cost:         ${baseline:.6f}  (if every request used the priciest model)")
    print(f"Saved vs baseline:     ${saved:.6f}  ({pct:.1f}%)")
    print()
    print(f"True cheapest cost:    ${cheapest:.6f}  (best model per tier, even if we lack a key for it)")
    print(f"Missed savings:        ${missed:.6f}  ({missed_pct:.1f}% more than optimal — "
          f"add adapters/keys for these providers to close the gap)")
    print()

    print("By difficulty:")
    for row in conn.execute(
        """
        SELECT difficulty, COUNT(*) AS n, SUM(actual_cost) AS actual, SUM(baseline_cost) AS baseline
        FROM requests_log GROUP BY difficulty
        """
    ):
        d_saved = (row["baseline"] or 0) - (row["actual"] or 0)
        print(f"  {row['difficulty']:8} n={row['n']:4}  cost=${row['actual']:.6f}  saved=${d_saved:.6f}")

    print()
    print("By model used:")
    for row in conn.execute(
        """
        SELECT provider, model_name, COUNT(*) AS n, SUM(actual_cost) AS actual
        FROM requests_log GROUP BY provider, model_name ORDER BY n DESC
        """
    ):
        print(f"  {row['provider']}/{row['model_name']:25} n={row['n']:4}  cost=${row['actual']:.6f}")

    print()
    print("Estimated monthly savings (extrapolated from avg savings/request):")
    avg_saved_per_request = saved / total
    for label, volume in [("1k req/day", 1000), ("10k req/day", 10000), ("100k req/day", 100000)]:
        monthly = avg_saved_per_request * volume * 30
        print(f"  {label:15} -> ${monthly:,.2f}/month")

    conn.close()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print_report()