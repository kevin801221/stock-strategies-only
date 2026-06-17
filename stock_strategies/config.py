import os
from pathlib import Path

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

# ── 快取（parquet）──
FINMIND_CACHE_DIR = os.environ.get(
    "FINMIND_CACHE_DIR",
    str(Path(__file__).resolve().parent.parent / ".cache" / "finmind"),
)
# 各頻率快取新鮮天數：超過則增量更新
CACHE_FRESH_DAYS = {"daily": 1, "monthly": 20, "weekly": 5, "quarterly": 60, "static": 7}

# ── 限流（FinMind 免費版約 600 req/hr）──
FINMIND_MIN_INTERVAL = 0.12       # 相鄰請求最小間隔秒
RATE_LIMIT_BACKOFF_BASE = 5       # 限流退避基數秒
RATE_LIMIT_MAX_RETRIES = 4

# ── context ──
MIN_PRICE_ROWS = 60               # 少於此列數視為新股／資料不足

# 台指期在 FinMind 的 data_id（夜盤盤前快報用）
FUTURES_ID = "TX"

CONFIG = {
    "eps_threshold": 5.0,
    "roe_threshold": 15.0,
    "backtest_years": 3,
    "hold_days": 20,
    "target_return": 0.10,
    "stop_loss": 0.08,
    "min_tech_score_for_signal": 60,
    "min_total_score_for_buy": 65,
    # 夜盤開盤方向分類門檻（漲跌幅 %）
    "night_gap_big": 1.5,    # |漲跌幅| ≥ 1.5% → 大漲 / 大跌
    "night_gap_small": 0.5,  # 0.5 ~ 1.5% → 小漲 / 小跌；< 0.5% → 平盤
}
