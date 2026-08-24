from datetime import datetime
from typing import Optional

import pandas as pd

from .config import CONFIG
from .data import get_fundamental, get_price_history
from .indicators import add_indicators, tech_score_at
from .backtest import backtest
from .volume import detect_patterns, verdict as volume_verdict
from .loader import merge_params


def evaluate(stock_id: str, name: str, strategy: dict | None = None) -> Optional[dict]:
    """評估一檔股票。strategy 為策略 dict（含 params），不給就用預設值。"""
    params = merge_params(strategy)

    result = {
        "stock_id": stock_id,
        "name": name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "strategy_id": (strategy or {}).get("id", "default"),
        "risk_notes": [],
    }

    try:
        fund = get_fundamental(stock_id)
        eps_vals = list(fund["eps"].values())
        roe_vals = list(fund["roe"].values())
        fund_pass = bool(
            len(eps_vals) >= 2
            and len(roe_vals) >= 2
            and min(eps_vals) > params["eps_threshold"]
            and min(roe_vals) > params["roe_threshold"]
        )

        px = get_price_history(stock_id, params["backtest_years"])
        if len(px) < 100:
            result["action"] = "SKIP"
            result["risk_notes"].append("價格資料不足")
            return result

        px = add_indicators(px)
        latest = px.iloc[-1]
        ts = tech_score_at(latest, params)
        bt = backtest(px, params)

        if params["use_volume_patterns"]:
            vp = detect_patterns(px)
        else:
            vp = {"patterns": [], "bonus": 0, "details": {}}

        fund_score = 100 if fund_pass else 40
        tech_score = max(0, min(100, ts["score"] + vp["bonus"]))
        winrate = bt.get("winrate") or 0.5
        bt_score = winrate * 100

        wf = params["weight_fundamental"]
        wt = params["weight_technical"]
        wb = params["weight_backtest"]
        # 正規化權重
        wsum = wf + wt + wb
        if wsum > 0:
            wf, wt, wb = wf / wsum, wt / wsum, wb / wsum

        signal_score = round(wf * fund_score + wt * tech_score + wb * bt_score, 1)

        fund_gate = (not params["fundamental_pass_required"]) or fund_pass
        if (
            signal_score >= params["min_total_score_for_buy"]
            and fund_gate
            and tech_score >= params["min_tech_score_for_buy"]
        ):
            action = "BUY"
        elif signal_score >= 50:
            action = "WATCH"
        else:
            action = "SKIP"

        entry = float(latest["close"])
        stop_price = round(entry * (1 - params["stop_loss"]), 2)
        target_price = round(entry * (1 + params["target_return"]), 2)
        rr = round(params["target_return"] / params["stop_loss"], 2)
        position_pct = min(2.0 / (params["stop_loss"] * 100) * 100, 20.0)
        entry_rule = (
            f"明日以開盤價進場，停損 -{params['stop_loss']*100:.0f}% / "
            f"停利 +{params['target_return']*100:.0f}%（下方參考價為今日收盤）"
        )

        if bt.get("samples", 0) < 8:
            result["risk_notes"].append(f"回測樣本僅 {bt.get('samples', 0)} 次，統計弱")
        if not fund_pass:
            result["risk_notes"].append("基本面未過門檻")
        if winrate < 0.5:
            result["risk_notes"].append(f"歷史勝率 {winrate*100:.0f}% 低於五成")
        if pd.notna(latest.get("bb_upper")) and latest["close"] > latest["bb_upper"]:
            result["risk_notes"].append("已突破布林上軌，追高風險")
        if "放量滯漲" in vp["patterns"]:
            result["risk_notes"].append("偵測到放量滯漲，高檔爆量疑似出貨")

        chg_5d = (latest["close"] / px.iloc[-6]["close"] - 1) * 100 if len(px) >= 6 else 0
        chg_20d = (latest["close"] / px.iloc[-21]["close"] - 1) * 100 if len(px) >= 21 else 0
        vol_5 = px["volume"].iloc[-5:].mean()
        vol_20 = px["volume"].iloc[-20:].mean()
        vol_ratio = vol_5 / vol_20 if vol_20 > 0 else 1
        high_252 = px["high"].iloc[-252:].max() if len(px) >= 252 else px["high"].max()
        low_252 = px["low"].iloc[-252:].min() if len(px) >= 252 else px["low"].min()
        pct_from_high = (latest["close"] / high_252 - 1) * 100
        above_ma20 = latest["close"] > latest["ma20"] if pd.notna(latest["ma20"]) else False
        above_ma60 = latest["close"] > latest["ma60"] if pd.notna(latest["ma60"]) else False

        result.update({
            "action": action,
            "signal_score": signal_score,
            "components": {
                "fundamental_pass": fund_pass,
                "eps_min": min(eps_vals) if eps_vals else None,
                "roe_min": min(roe_vals) if roe_vals else None,
                "tech_score": tech_score,
                "tech_signals": ts["signals"],
                "backtest_winrate": winrate,
                "backtest_samples": bt.get("samples", 0),
                "volume_patterns": vp["patterns"],
                "volume_details": vp["details"],
                "volume_bonus": vp["bonus"],
                "volume_verdict": volume_verdict(vp["patterns"]),
            },
            "trend": {
                "chg_5d": round(chg_5d, 2),
                "chg_20d": round(chg_20d, 2),
                "vol_ratio": round(vol_ratio, 2),
                "pct_from_high": round(pct_from_high, 1),
                "above_ma20": bool(above_ma20),
                "above_ma60": bool(above_ma60),
            },
            "entry_price": entry,
            "stop_loss_price": stop_price,
            "target_price": target_price,
            "risk_reward_ratio": rr,
            "position_size_pct": round(position_pct, 1),
            "entry_rule": entry_rule,
        })
        return result

    except Exception as e:
        result["action"] = "ERROR"
        result["risk_notes"].append(f"錯誤: {str(e)[:80]}")
        return result
