import os
import time
from datetime import datetime, timedelta

import requests
import pandas as pd

from .config import FINMIND_URL
from .cache import fetch_finmind_cached


def fetch_finmind(
    dataset: str,
    stock_id: str,
    start_date: str,
    timeout: int = 30,
    max_retries: int = 2,
) -> pd.DataFrame:
    """FinMind GET with retry + timeout 30s.
    對 timeout / connection error 自動 retry，間隔 exponential backoff (1s, 2s)。
    """
    params = {
        "dataset": dataset,
        "data_id": stock_id,
        "start_date": start_date,
        "token": os.environ["FINMIND_TOKEN"],
    }
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            r = requests.get(FINMIND_URL, params=params, timeout=timeout)
            r.raise_for_status()
            return pd.DataFrame(r.json().get("data", []))
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as e:
            last_err = e
            if attempt < max_retries:
                wait = 1.0 * (2 ** attempt)
                print(
                    f"[finmind] {dataset}/{stock_id} {type(e).__name__}, "
                    f"retry {attempt + 1}/{max_retries} after {wait:.1f}s"
                )
                time.sleep(wait)
                continue
            raise
    if last_err:
        raise last_err
    return pd.DataFrame()


def get_price_history(stock_id: str, years: int = 3) -> pd.DataFrame:
    start = (datetime.now() - timedelta(days=365 * years + 60)).strftime("%Y-%m-%d")
    df = fetch_finmind_cached("TaiwanStockPrice", stock_id, start)
    if df.empty:
        return df
    df = df.rename(columns={"max": "high", "min": "low", "Trading_Volume": "volume"})
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("date").reset_index(drop=True)


def get_fundamental(stock_id: str) -> dict:
    """近 3 完整年度 EPS、ROE。

    EPS = 該年單季 EPS 加總（年度）。
    ROE = 年度淨利 / 年底歸屬母公司權益 × 100——FinMind 財報無 ROE 欄，故自算。
    """
    start = f"{datetime.now().year - 4}-01-01"
    fs = fetch_finmind_cached("TaiwanStockFinancialStatements", stock_id, start)
    if fs.empty:
        return {"eps": {}, "roe": {}}

    fs = fs.copy()
    fs["date"] = pd.to_datetime(fs["date"])
    fs["year"] = fs["date"].dt.year
    fs["value"] = pd.to_numeric(fs["value"], errors="coerce")

    eps = fs[fs["type"] == "EPS"].groupby("year")["value"].sum().to_dict()
    roe = _compute_roe(fs, stock_id, start)

    cy = datetime.now().year
    return {
        "eps": {y: round(v, 2) for y, v in eps.items() if cy - 3 <= y < cy},
        "roe": {y: round(v, 2) for y, v in roe.items() if cy - 3 <= y < cy},
    }


def _compute_roe(fs: pd.DataFrame, stock_id: str, start: str) -> dict:
    """ROE = 年度淨利 / 年底歸屬母公司權益 × 100。
    FinMind TaiwanStockFinancialStatements 無 ROE 欄，故以損益表淨利
    (TotalConsolidatedProfitForThePeriod) + 資產負債表權益
    (EquityAttributableToOwnersOfParent) 自算。只對「該年 4 季淨利齊全」的
    年度計算，避免年度淨利不完整造成低估誤判。
    """
    ni = fs[fs["type"] == "TotalConsolidatedProfitForThePeriod"]
    if ni.empty:
        return {}
    bs = fetch_finmind_cached("TaiwanStockBalanceSheet", stock_id, start)
    if bs.empty or "type" not in bs.columns:
        return {}
    bs = bs.copy()
    bs["date"] = pd.to_datetime(bs["date"])
    bs["year"] = bs["date"].dt.year
    bs["value"] = pd.to_numeric(bs["value"], errors="coerce")
    eq = bs[bs["type"] == "EquityAttributableToOwnersOfParent"].sort_values("date")
    if eq.empty:
        return {}

    ni_sum = ni.groupby("year")["value"].sum()
    ni_cnt = ni.groupby("year")["value"].count()
    eq_year_end = eq.groupby("year")["value"].last()   # 該年最後一筆＝年底權益

    roe = {}
    for y, profit in ni_sum.items():
        eq_y = eq_year_end.get(y)
        if ni_cnt.get(y, 0) >= 4 and eq_y and eq_y > 0:
            roe[int(y)] = profit / eq_y * 100
    return roe
