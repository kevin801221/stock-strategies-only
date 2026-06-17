"""帶 parquet 快取 + 限流退避的 FinMind 取數層。

設計：一檔一 dataset 一 parquet（全歷史，不依日期切檔），讀取時記憶體過濾。
所有新 loader 一律呼叫 fetch_finmind_cached；回測逐日推進時命中快取、不重打 API。
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .config import (
    CACHE_FRESH_DAYS,
    FINMIND_CACHE_DIR,
    FINMIND_URL,
    FINMIND_MIN_INTERVAL,
    RATE_LIMIT_BACKOFF_BASE,
    RATE_LIMIT_MAX_RETRIES,
)


class FinMindRateLimitError(RuntimeError):
    """FinMind 限流且退避重試耗盡。由上層 loader 接住回中性結果。"""


def _cache_dir() -> Path:
    # 每次讀 env：測試會用 monkeypatch 改 FINMIND_CACHE_DIR
    return Path(os.environ.get("FINMIND_CACHE_DIR", FINMIND_CACHE_DIR))


def cache_path(dataset: str, data_id: str) -> Path:
    safe_id = data_id or "_ALL_"
    return _cache_dir() / f"{dataset}__{safe_id}.parquet"


def _meta_path(dataset: str, data_id: str) -> Path:
    return cache_path(dataset, data_id).with_suffix(".meta.json")


def clear_cache(dataset: str | None = None, data_id: str | None = None) -> int:
    """刪除符合條件的快取檔（含 sidecar meta），回傳刪除的 parquet 數。"""
    root = _cache_dir()
    if not root.exists():
        return 0
    if dataset and data_id:
        pattern = f"{dataset}__{data_id}.parquet"
    elif dataset:
        pattern = f"{dataset}__*.parquet"
    else:
        pattern = "*.parquet"
    removed = 0
    for p in root.glob(pattern):
        p.unlink()
        meta = p.with_suffix(".meta.json")
        if meta.exists():
            meta.unlink()
        removed += 1
    return removed


_last_request_monotonic = 0.0


def _throttle() -> None:
    """全域最小間隔節流，避免瞬間爆量。"""
    global _last_request_monotonic
    now = time.monotonic()
    wait = FINMIND_MIN_INTERVAL - (now - _last_request_monotonic)
    if wait > 0:
        time.sleep(wait)
    _last_request_monotonic = time.monotonic()


def _is_rate_limited(resp) -> bool:
    if resp.status_code in (402, 429):
        return True
    try:
        body = resp.json()
    except Exception:
        return False
    return (
        isinstance(body, dict)
        and body.get("status") not in (200, None)
        and "request" in str(body.get("msg", "")).lower()
    )


def _rate_limited_get(params: dict, timeout: int, max_retries: int) -> dict:
    """打 FinMind，處理限流（402/429/body status!=200 含 'request'）：
    指數退避重試，耗盡 raise FinMindRateLimitError。回傳已解析的 json dict。"""
    attempt = 0
    while True:
        _throttle()
        resp = requests.get(FINMIND_URL, params=params, timeout=timeout)
        if _is_rate_limited(resp):
            if attempt >= max_retries:
                raise FinMindRateLimitError(
                    f"FinMind 限流重試 {attempt} 次仍失敗: {params.get('dataset')}"
                )
            backoff = min(RATE_LIMIT_BACKOFF_BASE * (2 ** attempt), 120)
            time.sleep(backoff)
            attempt += 1
            continue
        resp.raise_for_status()
        return resp.json()


def _freq_of(dataset: str) -> str:
    if dataset in ("TaiwanStockFinancialStatements", "TaiwanStockBalanceSheet"):
        return "quarterly"          # 季報才更新，max_date 是季末日，不可當每日判過期
    if dataset == "TaiwanStockMonthRevenue":
        return "monthly"
    if dataset == "TaiwanStockShareholding":
        return "weekly"
    if dataset == "TaiwanStockInfo":
        return "static"
    return "daily"


def _read_cache(dataset: str, data_id: str) -> pd.DataFrame | None:
    p = cache_path(dataset, data_id)
    if not p.exists():
        return None
    try:
        return pd.read_parquet(p)
    except Exception:
        # 損毀 → 刪檔重抓
        p.unlink(missing_ok=True)
        _meta_path(dataset, data_id).unlink(missing_ok=True)
        return None


def _write_cache(dataset: str, data_id: str, df: pd.DataFrame) -> None:
    p = cache_path(dataset, data_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
    meta = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "min_date": str(df["date"].min()) if "date" in df and len(df) else None,
        "max_date": str(df["date"].max()) if "date" in df and len(df) else None,
        "rows": int(len(df)),
    }
    _meta_path(dataset, data_id).write_text(json.dumps(meta))


def _is_fresh(dataset: str, data_id: str, fresh_days: int | None,
              today: pd.Timestamp | None = None) -> bool:
    mp = _meta_path(dataset, data_id)
    if not mp.exists():
        return False
    try:
        meta = json.loads(mp.read_text())
        max_date = pd.to_datetime(meta.get("max_date"))
    except Exception:
        return False
    if pd.isna(max_date):
        return False
    days = fresh_days if fresh_days is not None else CACHE_FRESH_DAYS[_freq_of(dataset)]
    today = (today or pd.Timestamp.now()).normalize()
    # 用「工作日」數判斷新鮮度：週五抓的快取週一檢查＝1 個交易日(<=daily門檻1)，視為新鮮，
    # 不會因週末把整批資料判過期而觸發大量增量抓取（省 FinMind 額度）。
    gap = int(np.busday_count(max_date.normalize().date(), today.date()))
    return gap <= days


def _api_to_df(payload: dict) -> pd.DataFrame:
    df = pd.DataFrame(payload.get("data", []))
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def fetch_finmind_cached(
    dataset: str,
    data_id: str,
    start_date: str,
    end_date: str | None = None,
    *,
    fresh_days: int | None = None,
    force_refresh: bool = False,
    timeout: int = 30,
    max_retries: int = RATE_LIMIT_MAX_RETRIES,
) -> pd.DataFrame:
    """帶 parquet 快取 + 限流退避的 FinMind 取數。

    - 命中新鮮快取 → 直接回（不打 API）
    - 過期 → 增量抓 max_date 之後並合併去重
    - 冷啟動 → 全抓並寫快取
    回傳已正規化 date（datetime64）、升冪排序、去重後的 DataFrame；
    最後依 [start_date, end_date] 切片（end_date 杜絕抓進未來）。
    """
    cached = None if force_refresh else _read_cache(dataset, data_id)

    if cached is not None and not force_refresh and _is_fresh(dataset, data_id, fresh_days):
        df = cached
    else:
        params = {
            "dataset": dataset,
            "data_id": data_id,
            "start_date": start_date,
            "token": os.environ.get("FINMIND_TOKEN", ""),
        }
        # 增量：有舊快取（已含早期全歷史）則只抓 max_date-7d 之後，concat 去重補上新資料。
        # 不可用 min(start_date, inc_start)：當 start_date 早於 cache 時會退回全量重抓，增量失效。
        if cached is not None and len(cached) and "date" in cached.columns:
            inc_start = (cached["date"].max() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
            params["start_date"] = inc_start
        payload = _rate_limited_get(params, timeout=timeout, max_retries=max_retries)
        fresh = _api_to_df(payload)
        if cached is not None and len(cached):
            df = pd.concat([cached, fresh], ignore_index=True)
            # 全欄位去重：移除增量 overlap 的完全重複列。不可用 subset=["date"] 去重——
            # long-format（財報多 type、法人多 name）同一 date 有多列，會被誤砍成一列（根因A）。
            df = df.drop_duplicates()
        else:
            df = fresh
        df = df.reset_index(drop=True)
        if len(df):
            _write_cache(dataset, data_id, df)

    # 切片
    if "date" in df.columns and len(df):
        df = df[df["date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["date"] <= pd.to_datetime(end_date)]
        df = df.sort_values("date").reset_index(drop=True)
    return df
