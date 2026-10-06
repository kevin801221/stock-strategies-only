"""FastAPI 後端

啟動：
  uv run uvicorn api.main:app --reload --port 8000

提供：
  GET    /api/health
  GET    /api/strategies              列出所有策略
  GET    /api/strategies/defaults     回傳預設參數 schema
  GET    /api/strategies/{id}         取單一策略
  POST   /api/strategies              新增 / 更新策略
  DELETE /api/strategies/{id}         刪除
  POST   /api/strategies/generate     AI 生策略 (Gemini)
  GET    /api/market                  目前大盤狀態
  GET    /api/watchlist               讀 watchlist
  POST   /api/run                     用指定策略跑一次完整評分
"""

from __future__ import annotations

import os
import time
import traceback
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from stock_strategies import loader
from stock_strategies.market import get_market_state
from stock_strategies.sheet import read_watchlist

from api.services.ai_generator import generate_strategy_with_ai
from api.services.runs import RunBusy, RunManager

app = FastAPI(title="Stock Strategies API", version="1.1.0")
runs = RunManager()


@app.exception_handler(loader.StrategyError)
async def strategy_error(_request: Request, exc: loader.StrategyError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

# CORS：dev 期間給 localhost:3000 (Next.js)
_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins_env.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Schemas ----------


class StrategyIn(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    source: Optional[str] = "manual"
    params: dict[str, Any] = Field(default_factory=dict)


class AIGenerateIn(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000, description="使用者用自然語言描述想要的策略風格")
    name: Optional[str] = Field(None, max_length=120)

    @field_validator("prompt")
    @classmethod
    def nonempty_prompt(cls, value):
        if not value.strip():
            raise ValueError("請輸入策略描述")
        return value.strip()


class RunIn(BaseModel):
    strategy_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    limit: Optional[int] = Field(None, ge=1, le=1000, strict=True, description="只跑前 N 檔")


# ---------- Routes ----------


@app.get("/api/health")
def health():
    return {"ok": True, "ts": int(time.time())}


@app.get("/api/strategies")
def list_strategies():
    return {"strategies": loader.list_strategies()}


@app.get("/api/strategies/defaults")
def defaults():
    return {"params": loader.param_defaults()}


@app.get("/api/strategies/{sid}")
def get_strategy(sid: str):
    s = loader.get_strategy(sid)
    if not s:
        raise HTTPException(404, f"找不到策略 {sid}")
    return s


@app.post("/api/strategies")
def save_strategy(payload: StrategyIn):
    try:
        clean = loader.save_strategy(payload.model_dump())
        return clean
    except loader.StrategyError as e:
        raise HTTPException(400, str(e))


@app.delete("/api/strategies/{sid}")
def delete_strategy(sid: str):
    if sid in ("default", "conservative"):
        raise HTTPException(400, "預設策略不可刪除")
    ok = loader.delete_strategy(sid)
    if not ok:
        raise HTTPException(404, f"找不到策略 {sid}")
    return {"ok": True}


@app.post("/api/strategies/generate")
def generate_strategy(payload: AIGenerateIn):
    try:
        strategy = generate_strategy_with_ai(payload.prompt, name=payload.name)
        return strategy
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"AI 生策略失敗：{e}")


@app.get("/api/market")
def market():
    return get_market_state()


@app.get("/api/watchlist")
def watchlist():
    try:
        return {"items": read_watchlist()}
    except Exception as e:
        # 沒設定 Google Sheet 時不要整個 500
        return {"items": [], "error": str(e)}


def _load_run_strategy(payload: RunIn):
    strategy = loader.get_strategy(payload.strategy_id)
    if not strategy:
        raise HTTPException(404, f"找不到策略 {payload.strategy_id}")
    return strategy


@app.post("/api/run")
def run(payload: RunIn):
    """Compatibility endpoint; browser clients use /api/runs for short requests."""
    strategy = _load_run_strategy(payload)
    try:
        return runs.run_sync(strategy, payload.limit)
    except RunBusy as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"選股失敗：{exc}") from exc


@app.post("/api/runs", status_code=202)
def start_run(payload: RunIn):
    strategy = _load_run_strategy(payload)
    try:
        return runs.start(strategy, payload.limit)
    except RunBusy as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/runs/{job_id}")
def get_run(job_id: str):
    job = runs.get(job_id)
    if job is None:
        raise HTTPException(404, "執行紀錄不存在或已過期，請重新執行")
    return job


@app.delete("/api/runs/{job_id}")
def cancel_run(job_id: str):
    job = runs.cancel(job_id)
    if job is None:
        raise HTTPException(404, "執行紀錄不存在或已過期")
    return job
