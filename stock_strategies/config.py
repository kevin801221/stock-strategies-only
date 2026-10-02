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
   # ── 基本面與大盤條件 ──
    "roe_threshold": 10.0,              # 條件 ④：ROE > 10%
    "roe_years": 5,                     # 條件 ④：連續五年
    "market_above_ma20": True,          # 條件 ④：大盤在月線（20日線）上才成立

    # ── 技術面與籌碼面條件 ──
    "ma20_trending_up": True,           # 條件 ①：20日均線向上
    "margin_increase_top_rank": 100,    # 條件 ②：融資增加前 100 名
    "fund_holding_min_count": 100,      # 條件 ③：基金持有 > 100 檔
    "min_tech_score_for_signal": 60,
    "min_total_score_for_buy": 65,
    # 夜盤開盤方向分類門檻（漲跌幅 %）
    "night_gap_big": 1.5,    # |漲跌幅| ≥ 1.5% → 大漲 / 大跌
    "night_gap_small": 0.5,  # 0.5 ~ 1.5% → 小漲 / 小跌；< 0.5% → 平盤
}
