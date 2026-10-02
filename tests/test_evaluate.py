import numpy as np
import pandas as pd
from fastapi.encoders import jsonable_encoder

import stock_strategies.evaluate as evaluate_module


def test_evaluate_returns_json_serializable_fundamental_pass(monkeypatch):
    prices = pd.DataFrame({
        "open": np.linspace(100, 150, 120),
        "high": np.linspace(101, 151, 120),
        "low": np.linspace(99, 149, 120),
        "close": np.linspace(100, 150, 120),
        "volume": np.linspace(1000, 2000, 120),
    })

    monkeypatch.setattr(
        evaluate_module,
        "get_fundamental",
        lambda stock_id: {
            "eps": {2024: np.float64(6), 2025: np.float64(7)},
            "roe": {2024: np.float64(16), 2025: np.float64(17)},
        },
    )
    monkeypatch.setattr(
        evaluate_module,
        "get_price_history",
        lambda stock_id, years: prices.copy(),
    )
    monkeypatch.setattr(
        evaluate_module,
        "add_indicators",
        lambda df: df.assign(ma20=120.0, ma60=110.0, bb_upper=200.0),
    )
    monkeypatch.setattr(
        evaluate_module,
        "tech_score_at",
        lambda latest, params: {"score": 75, "signals": ["均線多頭"]},
    )
    monkeypatch.setattr(
        evaluate_module,
        "backtest",
        lambda df, params: {"winrate": 0.6, "samples": 10},
    )
    monkeypatch.setattr(
        evaluate_module,
        "detect_patterns",
        lambda df: {"patterns": [], "bonus": 0, "details": {}},
    )

    result = evaluate_module.evaluate("2308", "台達電")

    assert result is not None
    assert type(result["components"]["fundamental_pass"]) is bool
    jsonable_encoder(result)
