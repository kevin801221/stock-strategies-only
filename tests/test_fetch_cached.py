import pandas as pd

from stock_strategies import cache


def _patch_api(monkeypatch, rows_by_call):
    """mock _rate_limited_get 回傳每次呼叫對應的 data；記錄呼叫次數。"""
    state = {"n": 0}

    def fake(params, timeout, max_retries):
        i = state["n"]; state["n"] += 1
        return {"status": 200, "data": rows_by_call[min(i, len(rows_by_call) - 1)]}

    monkeypatch.setattr(cache, "_rate_limited_get", fake)
    return state


def test_cache_hit_skips_api(monkeypatch):
    # 新鮮度以 max_date 距今判定（spec §6 / _is_fresh），故用近兩日資料才會命中快取
    today = pd.Timestamp.now().normalize()
    d0 = (today - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    d1 = today.strftime("%Y-%m-%d")
    start = (today - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    rows = [[{"date": d0, "close": 10}, {"date": d1, "close": 11}]]
    state = _patch_api(monkeypatch, rows)
    df1 = cache.fetch_finmind_cached("TaiwanStockPrice", "2330", start)
    assert len(df1) == 2
    assert state["n"] == 1
    # 第二次：新鮮快取 → 不打 API
    df2 = cache.fetch_finmind_cached("TaiwanStockPrice", "2330", start)
    assert state["n"] == 1  # 沒再呼叫
    assert len(df2) == 2


def test_end_date_filters_future(monkeypatch):
    rows = [[
        {"date": "2024-01-02", "close": 10},
        {"date": "2024-01-05", "close": 12},
        {"date": "2024-01-10", "close": 15},
    ]]
    _patch_api(monkeypatch, rows)
    df = cache.fetch_finmind_cached(
        "TaiwanStockPrice", "2330", "2024-01-01", end_date="2024-01-05"
    )
    assert df["date"].max() <= __import__("pandas").Timestamp("2024-01-05")
    assert len(df) == 2


def test_force_refresh_rehits_api(monkeypatch):
    rows = [[{"date": "2024-01-02", "close": 10}]]
    state = _patch_api(monkeypatch, rows)
    cache.fetch_finmind_cached("TaiwanStockPrice", "2330", "2024-01-01")
    cache.fetch_finmind_cached("TaiwanStockPrice", "2330", "2024-01-01", force_refresh=True)
    assert state["n"] == 2


def test_incremental_only_fetches_after_max_date(monkeypatch):
    """過期快取應只增量抓 max_date-7d 之後，不可退回全量重抓（review issue #2）。"""
    captured = {}

    def fake(params, timeout, max_retries):
        captured["start_date"] = params["start_date"]
        return {"status": 200, "data": [{"date": "2020-01-09", "close": 11}]}

    monkeypatch.setattr(cache, "_rate_limited_get", fake)
    # 預先寫一個「過期」快取：max_date = 2020-01-02（距今已過 fresh_days）
    old = pd.DataFrame({"date": pd.to_datetime(["2020-01-02"]), "close": [10]})
    cache._write_cache("TaiwanStockPrice", "2330", old)
    cache.fetch_finmind_cached("TaiwanStockPrice", "2330", "2015-01-01")
    # 增量起點應為 max_date(2020-01-02) - 7d = 2019-12-26，而非請求的 2015-01-01
    assert captured["start_date"] == "2019-12-26"


def test_long_format_rows_survive_incremental(monkeypatch):
    """long-format（同 date 多 type，如財報 EPS/淨利）增量合併不可被砍成一列。
    根因A回歸測試：原本 drop_duplicates(subset=['date']) 會把同 date 多列砍成一列。"""
    seq = [
        [{"date": "2024-01-02", "type": "EPS", "value": 5},
         {"date": "2024-01-02", "type": "ROE", "value": 20}],   # 冷啟動：同 date 兩 type
        [{"date": "2024-01-02", "type": "EPS", "value": 5},
         {"date": "2024-01-02", "type": "ROE", "value": 20}],   # 增量 overlap：同樣兩列
    ]
    st = {"n": 0}

    def fake(params, timeout, max_retries):
        i = st["n"]; st["n"] += 1
        return {"status": 200, "data": seq[min(i, 1)]}

    monkeypatch.setattr(cache, "_rate_limited_get", fake)
    cache.fetch_finmind_cached("TaiwanStockFinancialStatements", "2330", "2024-01-01")  # 冷啟動寫快取
    df = cache.fetch_finmind_cached("TaiwanStockFinancialStatements", "2330", "2024-01-01")  # 過期→增量
    assert len(df[df["type"] == "EPS"]) == 1
    assert len(df[df["type"] == "ROE"]) == 1
    assert len(df) == 2   # 兩 type 都在，沒被砍成一列


def test_is_fresh_tolerates_weekend():
    """price 快取停在週五，週一檢查應視為新鮮（用工作日算，週末不算過期）。
    否則每個週一都會把整批 watchlist 重抓 → 撞 FinMind 額度。"""
    cache._write_cache("TaiwanStockPrice", "TEST_WK",
                       pd.DataFrame({"date": pd.to_datetime(["2026-06-12"])}))  # 週五
    monday = pd.Timestamp("2026-06-15")     # 隔週末，0 個交易日
    assert cache._is_fresh("TaiwanStockPrice", "TEST_WK", None, today=monday) is True
    tuesday = pd.Timestamp("2026-06-16")    # 隔了週一(1個交易日)，該增量更新
    assert cache._is_fresh("TaiwanStockPrice", "TEST_WK", None, today=tuesday) is False


def test_financial_statements_use_quarterly_freshness():
    """財報季度更新：季報日(3/31)距今數十個交易日仍應視為新鮮，不每次重抓撞額度。"""
    cache._write_cache("TaiwanStockFinancialStatements", "TEST_Q",
                       pd.DataFrame({"date": pd.to_datetime(["2026-03-31"])}))  # Q1 季報日
    assert cache._is_fresh("TaiwanStockFinancialStatements", "TEST_Q", None,
                           today=pd.Timestamp("2026-06-15")) is True   # 兩個半月後仍新鮮
    cache._write_cache("TaiwanStockBalanceSheet", "TEST_Q2",
                       pd.DataFrame({"date": pd.to_datetime(["2026-03-31"])}))
    assert cache._is_fresh("TaiwanStockBalanceSheet", "TEST_Q2", None,
                           today=pd.Timestamp("2026-06-15")) is True
