# 📈 台股每日選股機器人

> ✅ **現有版本穩定、開箱即用** — 每日選股、🌙 夜盤盤前快報、策略庫 Web UI 全部正常運作，`uv run python main.py` 直接跑即可，不需要任何額外設定。
>
> 🏗️ **另外有一個進行中的進階升級（V3.4）** — 正在打造「多流派因子 × 持有週期 × regime 自適應」的新選股引擎（地基已完成、105 測試全綠）。**這個升級完成前，完全不影響你現在的使用**——你照用穩定版，升級好了才會無痛接上。好奇的話 → [🏗️ V3.4 章節](#️-v34進行中--多角色股市策略系統重構)

## 🌙 新功能（已上線）：夜盤盤前快報
- 因為最近的夜盤台指期跌了三千多點，連帶 6/8 星期一股市也重挫——**夜盤是隔日台股盤勢的領先指標**，這版就把夜盤觀察機制做進來了。
- 新增一支**早上 08:00 的盤前排程**：讀昨晚整段台指期夜盤，推播「今日開盤方向預判（大漲/小漲/平盤/小跌/大跌）」，並把前一天選出的 BUY/WATCH 疊上「夜盤順風🟢 / 逆風🔴」標籤。
- 跟原本收盤後 14:30 的選股報告**互補**：晚上選股、隔天早上用夜盤校準方向。詳見 → [🌙 夜盤盤前快報](#-夜盤盤前快報詳解)
- 這支程式還在星期天開盤前推薦過一支即使大盤被狂殺、依舊漲停的股票，也推薦了星期一可以「便宜加碼」的標的，還不錯～
---

> **基本面 × 技術面 × 歷史回測** — 全自動掃描、評分、推播  
> 每天收盤後自動跑，Telegram 收通知，Google Sheet 存紀錄  
> 零伺服器成本，GitHub Actions 免費跑

[![GitHub Actions](https://img.shields.io/badge/自動排程-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)](#-github-actions-自動排程)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](#)
[![Telegram](https://img.shields.io/badge/通知-Telegram_Bot-26A5E4?logo=telegram&logoColor=white)](#-telegram-通知範例)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📣 感謝大家的支持！

沒想到這個小專案挺受歡迎 🙏 真心感謝每一位 Star、Fork、回報問題與提出建議的朋友。

接下來會**持續更新**，重點方向：

- 🎨 **全新 UI / UX** — 不再只有 Telegram 通知，將推出互動式網頁 Dashboard（今日訊號表、個股卡片、Performance 回測曲線）
- 🤖 **Multi-Agent 互動介面** — 結合 CopilotKit + LangGraph，讓你直接「跟 AI 對話」管理觀察清單、重跑選股、做 what-if 回測

敬請期待，也歡迎繼續提 issue 與 PR 一起把它做得更好！

---

## 🆕 V3.3 — 策略庫 + AI 生策略 Web UI

過去只有 Telegram 通知，這版開始有了**完整的互動式網頁介面**。`main.py` 的單一寫死策略也重構成「**參數化策略**」，每個策略 = `strategies/<id>.json` 一份檔案，可在網頁上建立、調參、執行。

新增兩個服務：

- **FastAPI 後端** (`api/`)：策略 CRUD、Gemini 自動生策略、用任一策略執行 watchlist
- **Next.js 前端** (`web/`)：策略庫列表、手動建立表單、AI 生策略（自然語言 → JSON）、Dashboard

> 介面預覽截圖在最下方 → [🖼️ Web UI 介面預覽](#-web-ui-介面預覽)

### 啟動方式（兩個 terminal）

```bash
# Terminal 1 — 後端
uv sync
uv run uvicorn api.main:app --reload --port 8000

# Terminal 2 — 前端
cd web && npm install && npm run dev
```

開 http://localhost:3000 即可。需新增環境變數 `GEMINI_API_KEY`（AI 生策略用，可選）。詳見 [`web/README.md`](web/README.md) 與 [`strategies/SCHEMA.md`](strategies/SCHEMA.md)。

原本的 `main.py` 走排程跑 default 策略，跟新 UI 完全相容。

---

## 🏗️ V3.4（進行中）— 多角色股市策略系統重構

> 舊版策略本質是「一份扁平 20 格參數 + 固定四技術訊號」，表達力有限。這版正在做一次**地基級重構**：把策略升級成「**多流派因子 × 持有週期 × 大盤 regime 自適應**」，用**多角色 AI 專家協作**設計、用**確定性回測引擎**驗證，產出更精準的策略庫。

> ### ✅ 這會影響我現在的使用嗎？完全不會。
> `uv run python main.py` 跑的**還是原本穩定的選股邏輯**，所有現有功能（夜盤快報、策略庫、Telegram 通知）照常。V3.4 是**獨立並行開發**的新引擎——它要等全部完成、且經過充分歷史回測驗證後，才會無痛接上 `main.py`。**在那之前，你開箱即用、零影響。** 下面的內容是給想了解技術方向、或想一起貢獻的人看的 👇

### 為什麼這樣重構（舊策略「太 rough」的三個根因）

1. **表達力弱** — 扁平參數無法表達「電子股一套、金融股另一套」「多頭放寬、空頭收緊」這種分層／條件邏輯。
2. **輸入維度窄** — 只有日 K 價量 + 年度 EPS/ROE，缺三大法人籌碼、月營收動能、估值分位、融資券、大盤結構。
3. **回測太薄** — 只算勝率、固定持有 20 日，沒有分市況、最大回撤、夏普；「歷史勝率 70%」可能只是某段大多頭撐出來的假象。

### 架構：兩層 + 四塊共用地基

```
研發層（多 AI 專家 workflow，跑一次、人工挑）
  資料專家 + Regime專家 → 7流派分析師 → 回測工程師 → 風控批判 → 首席策略長
  產出 → strategies/v2/*.json + 研發報告
        │ 共用「純 Python 確定性地基」（研發驗證過＝上線一模一樣）
固化層（每天跑進 main.py）
  逐檔: 算因子 → 判大盤 regime → 套最佳策略 → 規則決定 BUY/WATCH/SKIP → LLM 寫成專家會議紀要
```

> 關鍵設計：**回測數字一律來自確定性引擎，LLM 不臆造**。AI 專家負責「設計因子、看回測調整、組裝策略、寫人話理由」，買賣訊號由可回測的量化規則決定——所以「多專家」與「可回測」能並存。

### 進度

| 階段 | 內容 | 狀態 |
|---|---|---|
| **P1 資料層** | FinMind 7 dataset 的 point-in-time loader（法人／月營收／估值／融資券／外資持股／大盤指數）+ 快取限流 + `FactorContext` | ✅ 完成 |
| **P2 因子層** | 7 流派 **29 因子**（價值3／成長3／動能4／籌碼4／營收3／反轉3／突破3 + legacy 相容6）+ registry + `build_panel` | ✅ 完成 |
| **P3 回測引擎** | `regime_classify`（判多／盤／空）+ 分市況 `backtest_v2`（夏普／最大回撤／樣本外）+ 投組聚合 | 🔜 規劃中 |
| **P4 策略 schema** | 分層 schema（factors 加權 + regime_overrides + period）+ v1/v2 向後相容 | 🔜 |
| **P5 研發 workflow** | 多專家協作設計 + 回測驗證 → 產策略庫 | 🔜 |
| **P6 固化 runtime** | `evaluate_v2` + LLM 解說員，接回 `main.py` | 🔜 |
| **P7 前端／API** | 策略庫 v2 + AI 生成器升級 | 🔜 |

> P1 + P2 共 **105 個自動化測試全綠**，所有因子無未來資訊（point-in-time）、值域 0~1、缺料統一處理。

### 怎麼測

```bash
# 1) 單元測試（不需任何 token）
uv run pytest -q

# 2) 對真實股票算 29 個因子（需 .env 內的 FINMIND_TOKEN）
uv run python -c "
from dotenv import load_dotenv; load_dotenv('.env')
from stock_strategies.context import build_context
from stock_strategies.factors import FACTOR_REGISTRY, compute_factor, compute_all_factors
ctx = build_context('2330', '2024-06-28')
for n in sorted(FACTOR_REGISTRY): print(f'{n:32s}', compute_factor(n, ctx, {}))
fl = [{'name': n, 'weight': 1} for n in FACTOR_REGISTRY]
print('composite =', round(compute_all_factors(ctx, fl, {})['composite'], 3))
"
```

實測台積電（2330）2024-06-28：動能派頂、價值派趴、成長派不錯——方向完全符合當時 AI 題材大多頭、估值偏貴的現實，證明因子有意義。

### 設計文件

- **完整設計規格**：[`docs/superpowers/specs/`](docs/superpowers/specs/)（169K 字，含 8 個跨模組介面契約 §4、回測方法、七流派因子公式）
- **實作計畫**：[`docs/superpowers/plans/`](docs/superpowers/plans/)（P1、P2… 每塊 bite-sized TDD）

---

## 🌙 夜盤盤前快報（詳解）

### 為什麼看夜盤？

台指期**夜盤交易時段為 15:00 ～ 隔日 05:00**，這段時間涵蓋了歐美股市與國際消息的反應。隔天台股 09:00 開盤往往會「跳空」去貼齊夜盤的位置——所以**昨晚夜盤的漲跌，是今日台股開盤方向的領先參考**。6/8 那次台指期夜盤重挫三千多點，隔天現貨開盤就跟著大跌，就是最直接的例子。

### 夜盤在系統裡的兩個角色

夜盤訊號接在**兩個地方**，定位不同：

| | 14:30 收盤後選股（`main.py`） | 🌙 08:00 盤前快報（`premarket.py`） |
|---|---|---|
| 夜盤角色 | **情緒風控濾鏡** | **開盤方向預測** |
| 用哪段夜盤 | 昨晚（已反映在今收）→ 風控 | 昨晚（隔日就要開盤）→ 預測 |
| 怎麼作用 | 昨晚夜盤**大跌** → BUY 自動降 WATCH；小跌標逆風；報告標頭顯示夜盤濾鏡狀態 | 推「今日開盤方向預判」+ 把昨日 BUY/WATCH 貼順風/逆風 |

> **為什麼分兩處？** `main.py` 14:30 跑時，今晚夜盤還沒開始，只能拿到「昨晚」那段——它已反映在今天收盤價，所以在 main 裡定位是**風控**（夜盤重挫 → 隔日選股轉保守），而非精準開盤預測。真正「夜盤預測今日開盤」的角色，由隔天早上 08:00、夜盤收完後跑的盤前快報負責。兩者都**不重跑個股選股**，各只多打 1 次台指期 API，省 FinMind 額度。
>
> 註：夜盤是**大盤級**訊號，對 watchlist 每檔影響相同，若直接加進個股分數只會整體平移、不改變排名，因此設計成**門檻/濾鏡**（比照加權月線濾鏡）而非個股加分。

### 開盤方向分類

讀台指期夜盤近月（FinMind `TaiwanFuturesDaily` 的 `after_market` session），用漲跌幅分五級（門檻可在 `config.py` 調）：

| 夜盤漲跌幅 | 預判 | 對昨日 BUY/WATCH 的標籤 |
|---|---|---|
| ≥ +1.5% | 🚀 大漲 | 夜盤順風🟢（回檔承接優於追高，留意開高走低） |
| +0.5 ~ +1.5% | 🟢 小漲 | 夜盤順風🟢 |
| −0.5 ~ +0.5% | ⚪ 平盤 | 夜盤中性⚪（看量價表態） |
| −1.5 ~ −0.5% | 🟠 小跌 | 夜盤逆風🔴（等止穩再進） |
| ≤ −1.5% | 🔴 大跌 | 夜盤逆風🔴（嚴設停損／觀望） |

### 快報長這樣

```
🌙 夜盤盤前快報 2026/06/09 (週二)

🚀 台指期夜盤 +2.13% (+916 點)
近月收 43999 | 量 73,636
📈 開盤方向預判：大漲 → 今日開盤偏多，留意開高走低、別追高

📋 昨日訊號 × 夜盤對照 (2026-06-09)
🟡 WATCH 6510 精測 50分 · 夜盤順風🟢
🟡 WATCH 2330 台積電 50.2分 · 夜盤順風🟢
🟡 WATCH 2357 華碩 50.6分 · 夜盤順風🟢
↳ 夜盤偏多 — 回檔承接優於追高，開高別追、留意開高走低

💡 夜盤僅領先參考，開盤後仍以實際量價為準
```

### 啟用方式

本機先測一次（會真的發一則 Telegram）：

```bash
uv run python premarket.py
```

要排程自動跑，把 `premarket.yml` 一起搬進 `.github/workflows/`（secret 跟 `daily.yml` 共用，不用另外設）：

```bash
cp premarket.yml .github/workflows/premarket.yml
git add . && git commit -m "setup: enable premarket workflow" && git push
```

之後每個交易日**台灣時間 08:00**（夜盤 05:00 收完、開盤 09:00 前）自動推播。週一會自動抓到上週五的夜盤；若 08:00 夜盤資料還沒更新，會取最近一筆並標明資料日期。

> 微調門檻：改 `stock_strategies/config.py` 的 `night_gap_big`（大漲/大跌界線，預設 1.5%）與 `night_gap_small`（平盤界線，預設 0.5%）。

---

## 這是什麼？

一個 **單檔 Python 腳本**，幫你每天自動做三件事：

```
Google Sheet 股票池 → 跑策略評分 → Telegram 推播 + Sheet 紀錄
```

你只需要維護一張 Google Sheet 的觀察清單，系統每天台股收盤後自動：

1. **抓資料** — 透過 FinMind API 取得基本面財報 + 日 K 線
2. **跑策略** — 基本面篩選 → 技術面評分 → 3 年歷史回測
3. **發通知** — Telegram 推播買進/觀察訊號，附完整進出場價位
4. **存紀錄** — 結果寫回 Google Sheet，累積歷史追蹤

**不用租伺服器、不用學框架、不用碰資料庫。** Fork 這個 repo，設好環境變數，就會自動跑。

---

## 📱 Telegram 通知長這樣

**第一則 — 市場總覽**

```
📊 V3.0 每日選股報告 2026/04/09
掃描 15 檔 | BUY 2 | WATCH 5 | SKIP 8

🌡️ 市場氛圍
🟢 偏多 — 多數標的上漲且站穩月線，可積極佈局
池內均漲 +1.8% | 10/15 檔上漲 | 11/15 檔站上月線

📡 類股強弱排名
🔥 CPO (3檔) 5日均漲+4.2% | BUY 1 WATCH 1
📈 機器人 (2檔) 5日均漲+1.5% | BUY 1 WATCH 0
📉 重電 (2檔) 5日均漲-0.8% | BUY 0 WATCH 1
```

**第二則 — 個股詳情**

```
🟢 BUY — 建議進場 (2)

2308 台達電  綜合 72 分
🔥 5日+3.8% | 20日+8.2% | 距高點-5% | 站上月季線 | 量能放大
進場 1660 → 停損 1527.2 / 目標 1826
風報比 1:1.25 | 建議部位 20%
基本面✅ | 技術分 75 | 勝率 68% (12次)
觸發: 均線多頭, KD黃金交叉, MACD多頭
💡 為何買: 所有條件皆達標
```

**第三則 — 操作建議**

```
🧠 今日操作建議

🔑 最值得關注
• 2308 台達電 (BUY, 72分)
  技術面出現均線多頭/KD黃金交叉/MACD多頭，帶量上攻，多頭排列
  若進場: 進 1660 → 損 1527.2 / 標 1826

📌 操作方向
• 市場偏多，可挑選技術面強勢股分批進場
• 優先選回測勝率>60%、站穩月線的標的
```

> 通知分三則推送：市場總覽 → 個股詳情 → 操作建議，手機閱讀友善。

---

## ⚡ 5 分鐘部署

### 前置準備

你需要準備四組免費的 API / 帳號：

| 服務 | 用途 | 取得方式 |
|------|------|----------|
| [FinMind](https://finmindtrade.com/) | 台股財報 + K 線資料 | 免費註冊，拿 API token |
| [Telegram Bot](https://t.me/BotFather) | 推播通知 | 找 @BotFather 建 bot |
| [Google Sheet](https://sheets.google.com) | 股票池 + 訊號紀錄 | 建一張空的 Sheet |
| [GCP Service Account](https://console.cloud.google.com/) | 程式讀寫 Sheet 的權限 | 建 SA，下載 JSON 金鑰 |

### Step 1：Fork & Clone

```bash
# Fork 這個 repo 到你的 GitHub，然後
git clone https://github.com/<你的帳號>/stock-strategies-only.git
cd stock-strategies-only
```

### Step 2：建立 Google Sheet

建一張新的 Google Sheet，第一個分頁命名為 **`Watchlist`**，欄位如下：

| stock_id | name | category | enabled |
|----------|------|----------|---------|
| 2330 | 台積電 | AI | TRUE |
| 2308 | 台達電 | CPO | TRUE |
| 2049 | 上銀 | 機器人 | TRUE |

- `stock_id` — 台股代號
- `category` — 自訂類股分類（用於類股強弱排名）
- `enabled` — 設 `FALSE` 可暫停追蹤，不用刪除

> `Signals` 分頁不用手動建，程式第一次跑會自動建立。

記下 Sheet ID（網址中 `https://docs.google.com/spreadsheets/d/【這段】/edit`）。

### Step 3：設定 Google Service Account

1. 到 [Google Cloud Console](https://console.cloud.google.com/) 建專案
2. 啟用 **Google Sheets API** 和 **Google Drive API**
3. 建立 **Service Account**，下載 JSON 金鑰
4. 把 JSON 裡的 `client_email`（長得像 `xxx@xxx.iam.gserviceaccount.com`）加到你的 Google Sheet 共用權限（**編輯者**）

### Step 4：設定 Telegram Bot

1. Telegram 搜尋 **@BotFather**，輸入 `/newbot` 建立機器人，拿到 `BOT_TOKEN`
2. 搜尋 **@userinfobot**，拿到你的 `CHAT_ID`

### Step 5：設定 FinMind

到 [finmindtrade.com](https://finmindtrade.com/) 免費註冊，登入後在個人頁面取得 API Token。

### Step 6：本機測試

```bash
# 安裝 uv（如果還沒有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安裝依賴
uv sync

# 複製環境變數範本，填入你的值
cp .env.example .env
# 編輯 .env，填入上面拿到的各組 token

# 跑一次看看
uv run python main.py
```

成功的話，你的 Telegram 會收到選股通知，Google Sheet 的 Signals 分頁會出現新資料。

### Step 7：GitHub Actions 自動排程

到你 fork 的 repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**，加入五個 secret：

| Secret 名稱 | 值 |
|---|---|
| `FINMIND_TOKEN` | 你的 FinMind API token |
| `TELEGRAM_BOT_TOKEN` | 你的 Telegram Bot token |
| `TELEGRAM_CHAT_ID` | 你的 Telegram Chat ID |
| `GOOGLE_SHEET_ID` | 你的 Google Sheet ID |
| `GOOGLE_CREDS_JSON` | Service Account JSON **整串貼進去** |

把 workflow 搬到正確位置（兩支共用同一組 secret）：

```bash
mkdir -p .github/workflows
cp daily.yml .github/workflows/daily.yml          # 收盤後 14:30 選股
cp premarket.yml .github/workflows/premarket.yml  # 盤前 08:00 夜盤快報
git add . && git commit -m "setup: enable daily + premarket workflow" && git push
```

到 **Actions** 分頁點 **Run workflow** 各手動跑一次測試。沒問題後，每個交易日**台灣時間 14:30**（選股）與 **08:00**（夜盤快報）會自動執行。只想要其中一支就只複製對應的 yml 即可。

> GitHub Actions 免費額度：Private repo 每月 2000 分鐘，這個 workflow 每次約 2 分鐘，每月最多跑 22 天（交易日）= 44 分鐘，完全免費。

---

## 🧠 選股策略解析

### 評分公式

```
綜合分 = 基本面 × 30% + 技術面 × 30% + 回測勝率 × 40%
```

| 綜合分 | 動作 | 條件 |
|--------|------|------|
| ≥ 65 | 🟢 **BUY** | 基本面通過 + 技術分 ≥ 50 + 綜合分 ≥ 65 |
| ≥ 50 | 🟡 **WATCH** | 接近但未全過 |
| < 50 | ⚪ **SKIP** | 不符合 |

### 基本面篩選

```python
# 近 3 年每年都要達標
EPS > 5.0   # 每股盈餘
ROE > 15%   # 股東權益報酬率
```

通過 = 100 分，未通過 = 40 分。這是成長股篩選的基本門檻，過濾掉體質差的公司。

### 技術面評分（0-100）

四大指標各 25 分：

| 指標 | 滿分條件（25 分） | 部分得分 |
|------|-------------------|----------|
| **均線排列** | 收盤 > MA20 > MA60（多頭排列） | 收盤 > MA20（12 分） |
| **布林通道** | 貼近下軌反彈（距下軌 < 3%） | 收盤在中軌下方（10 分） |
| **KD 指標** | K > D 且 K < 80（黃金交叉未過熱） | K > D（10 分） |
| **MACD** | 柱狀 > 0 且 DIF > DEA | 柱狀 > 0（10 分） |

### 歷史回測

對過去 3 年所有技術分 ≥ 60 的交易日，模擬：
- 以**收盤價進場**
- 持有 **20 個交易日**
- **+10% 停利** / **-8% 停損** / 到期以收盤結算

```
回測分 = 歷史勝率 × 100
```

> ⚠️ 回測樣本 < 8 次時系統會標註「統計弱」，這種勝率參考就好。

### 風險管理

每筆交易自動計算：

```
停損價 = 進場價 × (1 - 8%)
目標價 = 進場價 × (1 + 10%)
風報比 = 10% / 8% = 1.25
建議部位 = min(2% / 停損%, 20%) = 25%（上限 20%）
```

---

## 🔧 自訂你的策略

### 調整參數

修改 `stock_strategies/config.py` 裡的 `CONFIG`：

```python
CONFIG = {
    "eps_threshold": 5.0,       # EPS 門檻，降低可納入更多股票
    "roe_threshold": 15.0,      # ROE 門檻
    "backtest_years": 3,        # 回測年數
    "hold_days": 20,            # 持有天數（交易日）
    "target_return": 0.10,      # 停利 10%
    "stop_loss": 0.08,          # 停損 8%
    "min_tech_score_for_signal": 60,  # 回測取樣的技術分門檻
    "min_total_score_for_buy": 65,    # BUY 的綜合分門檻
}
```

### 改寫策略的幾個方向

**加入新技術指標（以 RSI 為例）**

```python
# 在 stock_strategies/indicators.py 的 add_indicators() 裡新增
delta = df["close"].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
df["rsi"] = 100 - (100 / (1 + gain / loss))

# 在同一個檔案的 tech_score_at() 裡新增評分邏輯
if pd.notna(row.get("rsi")) and 30 < row["rsi"] < 70:
    score += 20
    signals.append("RSI 中性區")
```

**調整評分權重**

```python
# stock_strategies/evaluate.py 裡的綜合分公式
signal_score = round(
    0.3 * fund_score +   # 基本面 30%
    0.3 * tech_score +   # 技術面 30%
    0.4 * bt_score,      # 回測 40%（目前權重最高）
    1
)
# 想更重視技術面？改成 0.2 / 0.5 / 0.3
```

**週期股策略**

預設策略適合成長股（台達電、上銀這類）。週期股（面板、記憶體、航運）建議：
- 降低或跳過 EPS/ROE 門檻
- 改看營收年增率
- 加入產業景氣指標

---

## 📐 系統架構

```
【收盤後 14:30 — main.py 選股】
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Google Sheet │────▶│  Python 腳本  │────▶│  Telegram   │
│  (Watchlist) │     │              │     │  (通知推播)  │
└─────────────┘     │  1. 讀觀察清單 │     └─────────────┘
                    │  2. FinMind API│
┌─────────────┐     │  3. 策略評分   │     ┌─────────────┐
│   FinMind   │────▶│  4. 歷史回測   │────▶│ Google Sheet │
│ (財報 + K線) │     │  5. 發通知     │     │  (Signals)  │
└─────────────┘     └──────────────┘     └─────────────┘

【盤前 08:00 — premarket.py 夜盤快報】
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FinMind   │────▶│  夜盤近月漲跌  │────▶│  Telegram   │
│ (台指期夜盤) │     │  → 開盤方向    │     │ (盤前快報)   │
└─────────────┘     │  + 疊加昨日訊號 │     └─────────────┘
┌─────────────┐     │  (順風/逆風)   │
│ Google Sheet │────▶│              │
│  (Signals)  │     └──────────────┘
└─────────────┘

         ┌──────────────────────────┐
         │       GitHub Actions      │
         │  14:30 選股 / 08:00 夜盤   │
         │       每交易日自動觸發      │
         └──────────────────────────┘
```

---

## 🗂️ 檔案結構

```
stock-strategies-only/
├── main.py                    # 入口①：收盤後 14:30 選股（串接整個流程）
├── premarket.py               # 入口②：盤前 08:00 夜盤快報
├── stock_strategies/
│   ├── config.py              # 策略參數 & 常數（含夜盤門檻）
│   ├── sheet.py               # Google Sheet 讀寫
│   ├── data.py                # FinMind API 資料抓取
│   ├── market.py              # 大盤濾鏡（加權指數月線）
│   ├── night_session.py       # 夜盤抓取 + 開盤方向分類
│   ├── indicators.py          # 技術指標計算 + 評分
│   ├── backtest.py            # 歷史回測
│   ├── evaluate.py            # 綜合評估（組合以上模組）
│   └── notify.py              # Telegram 格式化 + 發送
├── pyproject.toml             # Python 依賴管理（uv）
├── uv.lock                    # 鎖定版本
├── daily.yml                  # GitHub Actions：收盤後選股（14:30）
├── premarket.yml              # GitHub Actions：盤前夜盤快報（08:00）
├── .env.example               # 環境變數範本
└── README.md
```

---

## ❓ FAQ

<details>
<summary><b>FinMind 免費帳號有請求限制嗎？</b></summary>

有，免費帳號每天約 600 次請求。每檔股票需要 2 次（財報 + K 線），所以觀察清單 **300 檔以內**不會超限。一般散戶追蹤 10-50 檔完全沒問題。

</details>

<details>
<summary><b>可以用其他資料源取代 FinMind 嗎？</b></summary>

可以。只需要改 `stock_strategies/data.py` 裡的三個函式，回傳格式一樣就行。常見替代：[TWSE OpenData](https://openapi.twse.com.tw/)、Yahoo Finance（需額外套件）。

</details>

<details>
<summary><b>GitHub Actions 要錢嗎？</b></summary>

Private repo 每月免費 2000 分鐘，這個 workflow 每次約 2 分鐘，每月最多跑 22 天 = 44 分鐘，完全免費。Public repo 更是無限制。

</details>

<details>
<summary><b>想用 LINE Notify 而不是 Telegram？</b></summary>

改寫 `stock_strategies/notify.py` 裡的 `send_telegram()` 函式，換成 LINE Notify API 即可，其他模組完全不用動。

</details>

<details>
<summary><b>回測勝率可信嗎？</b></summary>

看樣本數。系統會自動標註：
- **< 8 次**：基本無統計意義
- **8-15 次**：僅供參考
- **> 20 次**：相對可信，但仍不保證未來表現

回測用的是固定停損停利結算，對趨勢型成長股比較適用。

</details>

<details>
<summary><b>怎麼用 AI 助手管理觀察清單？</b></summary>

如果你有接 Google Sheets MCP（如 Claude Desktop），可以直接用對話操作：

> 「把 2330 台積電加進 watchlist，category 放 AI」  
> 「先把 3081 聯亞停掉，還沒反轉」

下次排程自動納入或排除。

</details>

---

## 🖼️ Web UI 介面預覽

**Dashboard — 一鍵執行今日選股**
挑一個策略、按下執行，即時看到 watchlist 每檔的綜合分與 BUY / WATCH / SKIP 結果，並標出市場氛圍。

![Dashboard](assets/dashboard.jpg)

**策略庫 — 所有策略集中管理**
每個策略一張卡片，列出 EPS / ROE 門檻、總分門檻、持有日等關鍵參數，可直接「跑一次」或新增。

![策略庫](assets/strategy-library.jpg)

**手動建立策略 — 全參數化表單**
基本面門檻、回測與訊號、風險（停利 / 停損）、評分加權、技術訊號開關全部可調，所有欄位都有預設值。

![手動建立策略](assets/strategy-create.jpg)

**AI 生策略 — 用一句話生出參數**
輸入「我想做短線動能，5–10 天持有，停損 -5%、停利 +15%」這類自然語言，Gemini 自動生出對應策略 JSON，可再微調後存進策略庫。

![AI 生策略](assets/strategy-ai.jpg)

---

## 🛣️ Roadmap

**✅ 最新完成**

- [x] 🌙 **夜盤盤前快報** — 早上 08:00 讀台指期夜盤，預判今日開盤方向，疊加昨日訊號順風/逆風

**🚧 進行中（下一個大版本）**

- [ ] 🎨 **互動式網頁 Dashboard** — 今日訊號表、個股詳情卡、Performance 回測曲線（Next.js + Tailwind）
- [ ] 🤖 **Multi-Agent 對話介面** — CopilotKit + LangGraph，用對話管理 watchlist、重跑選股、what-if 回測

**📋 規劃中**

- [ ] 類股強弱前置過濾 — 順風類股才出訊號
- [ ] 資金控管模組 — 追蹤總部位曝險
- [ ] 追蹤停利 — 已進場部位的每日監控
- [ ] 週期股策略 — 營收年增率 + 景氣指標
- [ ] 週報自動生成 — 每週日回顧本週訊號表現

---

## 📄 License

[MIT License](LICENSE) — 自由使用、修改、散佈。

---

## ⚠️ 免責聲明

本專案僅供**學習與研究**用途。程式產生的訊號**不構成投資建議**。股票投資有風險，任何交易決策請自行判斷並承擔責任。過去的回測表現不代表未來的獲利保證。
