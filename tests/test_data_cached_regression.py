import pandas as pd
from stock_strategies import data


def test_get_price_history_uses_cache(monkeypatch):
    raw = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "open": [10, 11], "max": [10.5, 11.5], "min": [9.5, 10.5],
        "close": [10.2, 11.2], "Trading_Volume": [1000, 1100],
    })
    monkeypatch.setattr(data, "fetch_finmind_cached", lambda *a, **k: raw.copy())
    df = data.get_price_history("2330", years=1)
    assert {"date", "open", "high", "low", "close", "volume"}.issubset(df.columns)
    assert df.iloc[1]["high"] == 11.5    # max→high
    assert df.iloc[1]["volume"] == 1100  # Trading_Volume→volume


def test_get_fundamental_computes_roe(monkeypatch):
    """ROE 由 年度淨利/年底權益 自算（根因B：FinMind 財報無 ROE 欄）。"""
    fs = pd.DataFrame({
        "date": pd.to_datetime(["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"] * 2),
        "type": ["EPS"] * 4 + ["TotalConsolidatedProfitForThePeriod"] * 4,
        "value": [10.0, 10.0, 10.0, 10.0, 1e11, 1e11, 1e11, 1e11],
    })
    bs = pd.DataFrame({
        "date": pd.to_datetime(["2024-12-31"]),
        "type": ["EquityAttributableToOwnersOfParent"],
        "value": [2e12],
    })

    def fake(dataset, sid, start, **k):
        return fs.copy() if dataset == "TaiwanStockFinancialStatements" else bs.copy()

    monkeypatch.setattr(data, "fetch_finmind_cached", fake)
    f = data.get_fundamental("2330")
    assert f["eps"][2024] == 40.0                  # 4 季 EPS 加總
    assert abs(f["roe"][2024] - 20.0) < 0.1        # 年度淨利4e11 / 年底權益2e12 = 20%


def test_get_fundamental_roe_skips_incomplete_year(monkeypatch):
    """只有部分季淨利的年度不算 ROE（避免年度低估誤判）。"""
    fs = pd.DataFrame({
        "date": pd.to_datetime(["2024-03-31", "2024-06-30"] * 2),  # 只有 2 季
        "type": ["EPS"] * 2 + ["TotalConsolidatedProfitForThePeriod"] * 2,
        "value": [10.0, 10.0, 1e11, 1e11],
    })
    bs = pd.DataFrame({"date": pd.to_datetime(["2024-06-30"]),
                       "type": ["EquityAttributableToOwnersOfParent"], "value": [2e12]})

    def fake(dataset, sid, start, **k):
        return fs.copy() if dataset == "TaiwanStockFinancialStatements" else bs.copy()

    monkeypatch.setattr(data, "fetch_finmind_cached", fake)
    f = data.get_fundamental("2330")
    assert 2024 not in f["roe"]   # 季數不足 4，不算 ROE
