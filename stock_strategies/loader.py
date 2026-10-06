"""策略檔載入 / 驗證 / 儲存

策略以 strategies/<id>.json 形式存放。本模組負責：
- 讀取單一策略或全部策略
- 寫入新策略 / 更新現有策略 / 刪除
- 把策略的 params 與預設 CONFIG 合併成扁平 dict，給 evaluate / backtest 使用
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import CONFIG

# 策略目錄：環境變數可覆寫（部署時方便）
STRATEGY_DIR = Path(
    os.environ.get(
        "STRATEGY_DIR",
        str(Path(__file__).resolve().parent.parent / "strategies"),
    )
)

# 允許出現在 params 內的鍵 → 預設值
_PARAM_DEFAULTS: dict = {
    # 基本面
    "eps_threshold": CONFIG["eps_threshold"],
    "roe_threshold": CONFIG["roe_threshold"],
    "fundamental_pass_required": True,
    # 回測
    "backtest_years": CONFIG["backtest_years"],
    "hold_days": CONFIG["hold_days"],
    "min_tech_score_for_signal": CONFIG["min_tech_score_for_signal"],
    # 風險
    "target_return": CONFIG["target_return"],
    "stop_loss": CONFIG["stop_loss"],
    # 評分加權
    "weight_fundamental": 0.3,
    "weight_technical": 0.3,
    "weight_backtest": 0.4,
    "min_total_score_for_buy": CONFIG["min_total_score_for_buy"],
    "min_tech_score_for_buy": 50,
    # 技術訊號開關
    "use_ma_alignment": True,
    "use_bollinger_bounce": True,
    "use_kd_golden_cross": True,
    "use_macd_bullish": True,
    "use_volume_patterns": True,
    # 大盤濾鏡
    "market_filter_enabled": True,
    "market_filter_ma_period": 20,
}


class StrategyError(ValueError):
    """策略驗證失敗"""


_WRITE_LOCK = threading.Lock()
_BOUNDS = {
    "backtest_years": (1, 10), "hold_days": (1, 120),
    "target_return": (0.01, 0.5), "stop_loss": (0.01, 0.5),
    "min_total_score_for_buy": (0, 100), "min_tech_score_for_buy": (0, 100),
    "min_tech_score_for_signal": (0, 100), "market_filter_ma_period": (5, 120),
    "weight_fundamental": (0, 1), "weight_technical": (0, 1), "weight_backtest": (0, 1),
}


def _strategy_path(sid: str) -> Path:
    if not isinstance(sid, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", sid):
        raise StrategyError("策略 ID 只能包含英數字、底線與連字號，長度 1–100")
    path = STRATEGY_DIR / f"{sid}.json"
    if path.is_symlink():
        raise StrategyError("策略檔不可為符號連結")
    return path


def _slugify(text: str) -> str:
    """產生策略 ID。保留 ASCII 英數字與底線；CJK 中文字會被丟掉，
    若清掉後變空字串就回 uuid。"""
    text = re.sub(r"[^a-zA-Z0-9-_]+", "-", text.strip().lower())
    text = text.strip("-")
    if len(text) < 3:
        return "s-" + uuid.uuid4().hex[:8]
    return text


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)


def merge_params(strategy: Optional[dict]) -> dict:
    """把策略的 params 蓋在預設值上，回傳扁平 dict。"""
    merged = dict(_PARAM_DEFAULTS)
    if not strategy:
        return merged
    params = strategy.get("params") or {}
    for k, v in params.items():
        if k in merged and v is not None:
            merged[k] = v
    # 健全性：權重總和不為 0
    total = (
        merged["weight_fundamental"]
        + merged["weight_technical"]
        + merged["weight_backtest"]
    )
    if total <= 0:
        merged["weight_fundamental"] = 0.3
        merged["weight_technical"] = 0.3
        merged["weight_backtest"] = 0.4
    return merged


def validate_strategy(data: dict) -> dict:
    """驗證並補齊一份策略 JSON，回傳乾淨版本（可寫入）"""
    if not isinstance(data, dict):
        raise StrategyError("策略必須是 JSON 物件")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise StrategyError("策略名稱必須為 1–120 字")
    name = name.strip()

    sid = data.get("id") if data.get("id") is not None else _slugify(name)[:80]
    _strategy_path(sid)
    source = data.get("source") or "manual"
    if source not in ("default", "manual", "ai"):
        source = "manual"

    raw_params = data.get("params", {})
    if not isinstance(raw_params, dict):
        raise StrategyError("params 必須是物件")

    clean_params: dict = {}
    for key, default_val in _PARAM_DEFAULTS.items():
        if key in raw_params and raw_params[key] is not None:
            v = raw_params[key]
            if isinstance(default_val, bool):
                if not isinstance(v, bool):
                    raise StrategyError(f"{key} 必須是布林值")
            else:
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise StrategyError(f"{key} 必須是有限數值")
                try:
                    finite = math.isfinite(v)
                except OverflowError:
                    finite = False
                if not finite:
                    raise StrategyError(f"{key} 必須是有限數值")
                if isinstance(default_val, int):
                    if v != int(v):
                        raise StrategyError(f"{key} 必須是整數")
                    v = int(v)
                else:
                    v = float(v)
                if key in _BOUNDS:
                    low, high = _BOUNDS[key]
                    if not low <= v <= high:
                        raise StrategyError(f"{key} 必須介於 {low} 與 {high}")
            clean_params[key] = v
        else:
            clean_params[key] = default_val

    if sum(clean_params[k] for k in ("weight_fundamental", "weight_technical", "weight_backtest")) <= 0:
        raise StrategyError("評分權重總和必須大於 0")
    description = data.get("description") or ""
    if not isinstance(description, str) or len(description) > 4000:
        raise StrategyError("策略說明必須是文字且不超過 4000 字")

    return {
        "id": sid,
        "name": name,
        "description": description.strip(),
        "source": source,
        "created_at": data.get("created_at") or _now_iso(),
        "updated_at": _now_iso(),
        "params": clean_params,
    }


def list_strategies() -> list[dict]:
    _ensure_dir()
    out = []
    for p in sorted(STRATEGY_DIR.glob("*.json")):
        try:
            strategy = get_strategy(p.stem)
            if strategy is not None:
                out.append(strategy)
        except Exception as e:
            out.append({"id": p.stem, "name": p.stem, "error": str(e)})
    return out


def get_strategy(sid: str) -> Optional[dict]:
    path = _strategy_path(sid)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        clean = validate_strategy(data)
        clean["id"] = sid
        clean["updated_at"] = data.get("updated_at") or clean["updated_at"]
        return clean
    except (ValueError, TypeError) as exc:
        raise StrategyError(f"策略 {sid} 無法讀取：{exc}") from exc


def save_strategy(data: dict) -> dict:
    """新增或覆寫一份策略。回傳乾淨版本。"""
    _ensure_dir()
    clean = validate_strategy(data)
    with _WRITE_LOCK:
        path = _strategy_path(clean["id"])
        if data.get("id") is None and path.exists():
            clean["id"] = f"{clean['id']}-{uuid.uuid4().hex[:8]}"
            path = _strategy_path(clean["id"])
        if path.exists():
            clean["created_at"] = get_strategy(clean["id"])["created_at"]
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=STRATEGY_DIR, suffix=".tmp", delete=False) as f:
                temporary = Path(f.name)
                json.dump(clean, f, ensure_ascii=False, indent=2, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return clean


def delete_strategy(sid: str) -> bool:
    path = _strategy_path(sid)
    if path.exists():
        path.unlink()
        return True
    return False


def param_defaults() -> dict:
    """讓 API / 前端拿預設值用"""
    return dict(_PARAM_DEFAULTS)
