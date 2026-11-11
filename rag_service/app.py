"""
app.py — a production-shaped HTTP front door for your RAG pipeline.

    GET  /health          → is the service up, is the index loaded, how many chunks
    POST /ask             → {"question": "...", "k": 5}  (requires header  X-API-Key: <APP_API_KEY>)

Two production decisions are already made for you, and both are Milestone 2 material:
  1. The gateway key never leaves the server. Callers use YOUR key (APP_API_KEY), not UNC's.
  2. Every answer logs one JSON line with tokens, cost and latency → Azure Log Analytics picks it up.
"""
import json
import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from rag import RAGPipeline

def log_request_to_mlflow(result, latency_ms):
    """Log request metrics to MLflow when tracking is configured."""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

    if not tracking_uri:
        return

    try:
        import mlflow

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(
            os.getenv("MLFLOW_EXPERIMENT_NAME", "apollo-rag-monitoring")
        )

        usage = result.get("usage", {})

        with mlflow.start_run():
            mlflow.log_metrics({
                "latency_ms": latency_ms,
                "input_tokens": usage.get("input_tokens") or 0,
                "output_tokens": usage.get("output_tokens") or 0,
                "total_tokens": usage.get("total_tokens") or 0,
                "blocked": int(result.get("blocked", False)),
            })

            mlflow.set_tags({
                "defense_layer": result.get("defense_layer") or "none",
                "request_status": "blocked" if result.get("blocked") else "success",
            })

    except Exception as exc:
        print(json.dumps({
            "event": "mlflow_logging_error",
            "error": type(exc).__name__,
        }))

load_dotenv()  # local runs read .env; in Azure there is no .env and the secrets arrive as env vars
APP_API_KEY = os.getenv("APP_API_KEY", "")
state = {"pipeline": None, "error": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build/load the index once per replica. If the key isn't configured yet (first deploy), start anyway
    # so /health can tell you what's wrong instead of crash-looping.
    try:
        state["pipeline"] = RAGPipeline.load()
    except Exception as e:  # noqa: BLE001
        state["error"] = str(e)
        print(json.dumps({"event": "startup_degraded", "error": str(e)}))
    yield


app = FastAPI(title="DATA 790 · RAG service", version="0.1", lifespan=lifespan)


class Ask(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    k: int = Field(default=5, ge=1, le=20)


def require_key(x_api_key: str = Header(default="")):
    if not APP_API_KEY:
        raise HTTPException(503, "APP_API_KEY is not configured on the server")
    if x_api_key != APP_API_KEY:
        raise HTTPException(401, "missing or invalid X-API-Key")


@app.get("/health")
def health():
    p = state["pipeline"]
    return {"ok": p is not None, "chunks": p.size() if p else 0, "error": state["error"],
            "app_key_configured": bool(APP_API_KEY)}


@app.post("/ask", dependencies=[Depends(require_key)])
def ask(body: Ask):
    p = state["pipeline"]
    if p is None:
        # retry the build lazily — the secret may have been added after the first deploy
        try:
            state["pipeline"] = p = RAGPipeline.load()
            state["error"] = None
        except Exception as e:  # noqa: BLE001
            raise HTTPException(503, f"index not available: {e}") from e
    t0 = time.perf_counter()
    result = p.answer(body.question, k=body.k)
    latency_ms = round((time.perf_counter() - t0) * 1000)
    log_request_to_mlflow(result, latency_ms)
    print(json.dumps({"event": "ask", "latency_ms": latency_ms, **result["usage"]}))  # one line per request → logs
    return {**result, "latency_ms": latency_ms}
