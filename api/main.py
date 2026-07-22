import os
import sqlite3
import sys
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).parent.parent
for sub in ["classifier", "router", "execution", "analytics"]:
    sys.path.insert(0, str(ROOT / sub))

from pipeline import handle_prompt  # noqa: E402
from executor import execute  # noqa: E402

DB_PATH = ROOT / "data" / "llm_cost.db"

# Comma-separated list of keys allowed to call this API. Set in .env as API_KEYS=key1,key2
from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT / ".env")
VALID_API_KEYS = {k.strip() for k in os.environ.get("API_KEYS", "").split(",") if k.strip()}

app = FastAPI(title="LLM Cost Optimizer API")


def require_api_key(x_api_key: str | None = Header(default=None)):
    if not VALID_API_KEYS:
        return  # no keys configured yet -> open access (dev mode)
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


class GenerateRequest(BaseModel):
    prompt: str
    top_n: int = 5


@app.post("/generate")
def generate(req: GenerateRequest, x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)

    routed = handle_prompt(req.prompt, top_n=req.top_n)
    result = execute(routed)

    if not result["response"]:
        raise HTTPException(status_code=502, detail={"error": "all candidates failed", "attempts": result["attempts"]})

    return {
        "prompt": req.prompt,
        "difficulty": routed["difficulty"],
        "provider": result["provider"],
        "model": result["model_name"],
        "response": result["response"],
        "cost": round(result["actual_cost"], 6),
        "baseline_cost": round(result["baseline_cost"], 6),
        "saved": round(result["saved"], 6),
        "cheapest_available": result.get("cheapest"),
        "attempts_before_success": result["attempts"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/providers")
def providers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT provider, model_name, category, cost_input_per_1m, cost_output_per_1m, avg_latency_ms FROM models"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/analytics")
def analytics():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) AS n FROM requests_log").fetchone()["n"]
    if total == 0:
        conn.close()
        return {"total_requests": 0}

    totals = conn.execute(
        "SELECT SUM(actual_cost) AS actual, SUM(baseline_cost) AS baseline, "
        "SUM(cheapest_cost) AS cheapest, AVG(latency_ms) AS avg_latency FROM requests_log"
    ).fetchone()
    actual = totals["actual"] or 0
    baseline = totals["baseline"] or 0
    cheapest = totals["cheapest"] or actual

    by_model = conn.execute(
        "SELECT provider, model_name, COUNT(*) AS n, SUM(actual_cost) AS cost "
        "FROM requests_log GROUP BY provider, model_name ORDER BY n DESC"
    ).fetchall()

    conn.close()

    return {
        "total_requests": total,
        "actual_cost": round(actual, 6),
        "baseline_cost": round(baseline, 6),
        "saved": round(baseline - actual, 6),
        "saved_pct": round((baseline - actual) / baseline * 100, 2) if baseline else 0,
        "true_cheapest_cost": round(cheapest, 6),
        "avg_latency_ms": round(totals["avg_latency"], 0),
        "by_model": [dict(r) for r in by_model],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)