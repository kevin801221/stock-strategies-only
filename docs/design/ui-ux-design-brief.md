# 設計 Prompt：台股每日選股機器人「訊號儀表板 + AI 專家會議」介面

你是世界級金融產品設計師。請為一款台股每日選股系統設計一套完整的高擬真 dark-mode-first 網頁介面與設計系統。以下是純設計 brief（不涉及後端、不寫程式邏輯、不寫演算法），請聚焦視覺、版面、資訊架構、互動、狀態與設計語言。

## 1. 產品定位與設計目標

**一句話定位**：給台股散戶的「每日盤後選股 + 盤前校準」決策儀表板——每天自動掃描觀察池，用基本面×技術面×籌碼×回測四維評分，產出 BUY/WATCH/SKIP 訊號，並由多位 AI 專家開「會議」逐檔解說。

**設計目標氣質**（缺一不可）：
- **專業可信**（professional, trustworthy）：這是會影響真金白銀決策的工具，視覺不能花俏輕浮，要像 Bloomberg Terminal 的冷靜與 Linear 的克制。
- **數據密集但好讀**（dense yet legible）：單畫面要塞進數十檔股票 × 每檔十幾個數字，靠層級、對齊、tabular 數字、留白節奏讓人秒讀，不靠堆 emoji。
- **台股在地感**（local credibility）：紅漲綠跌（見下方色彩鐵律）、繁體中文為主、台股代號慣例（4 碼如 2330 台積電）、台指期/月線/季線/法人/融資等在地術語自然呈現。
- 去除現版「陽春感」：現版靠 emoji 當 icon、原生 select/table、純文字數字、無圖表。新設計要用正式 icon set、自訂元件、資料視覺化全面升級。

## 2. 目標使用者與情境

- **使用者**：有基本盤感的台股散戶／兼職投資人，看得懂均線、KD、法人買賣超，但沒時間自己掃幾十檔。
- **裝置**：desktop-first（盤後在電腦前做功課、調策略、看回測），但**必須能在手機上舒服看訊號表與盤前快報**（通勤時、開盤前快速掃一眼）。
- **兩個核心心情/情境**：
  1. **盤後決策**（14:30 後）：「今天有哪些可以買？為什麼？進場/停損/目標價多少？風險在哪？」——專注、想看細節、想被說服。
  2. **盤前校準**（隔日 08:00）：「昨晚台指期夜盤怎麼走？我昨天挑的票今天開盤是順風還逆風？」——快速、低注意力、要一眼看懂方向。

## 3. 設計語言 / Visual Direction

方向定調：**dark-mode-first 的專業金融儀表板，氣質 = Linear（克制、銳利、優雅的層級）× Bloomberg-lite（資訊密度、tabular 數字、狀態色嚴謹）× 富果 Fugle（台股在地親和、圖表現代）**。要有觀點，不要通用 admin template 感。

### 色彩系統

**深色基底（沿用現有 token 並擴充）**：
- `bg` 背景 `#0b0d10`、`panel` 卡片 `#13171d`、`panel2` 次層 `#1a1f27`、`line` 分隔線 `#252b35`
- `text` 主文字 `#e6e9ee`、`muted` 次要文字 `#8a93a0`
- `accent` 主互動藍 `#3b82f6`（連結、focus、主按鈕、選取態）

**台股漲跌色鐵律（最重要，務必正確，與美股相反）**：
- **漲 = 紅**。所有正報酬、上漲、漲幅 chg_5d/chg_20d 正值、夜盤上漲、權益曲線上升段 → 用**紅色系**（建議 `#ef4444` 暖紅，或更飽和的台股紅 `#e84545`）。
- **跌 = 綠**。所有負報酬、下跌、漲幅負值、夜盤下跌 → 用**綠色系**（建議 `#22c55e`）。
- 設計師注意：這跟 Robinhood/美股直覺相反，**不可把綠當漲、紅當跌**，否則整個產品在台灣使用者眼中是壞掉的。所有走勢圖、漲跌數字、箭頭、迷你 sparkline 都遵守紅漲綠跌。

**訊號狀態色（語意固定，與漲跌色分離管理，避免混淆）**：
- `BUY` = `#22c55e` 綠（建議進場）、`WATCH` = `#eab308` 黃（觀察）、`SKIP` = `#64748b` 灰（不符合）、`ERROR` = `#ef4444` 紅（評估出錯）。
- 注意這裡 BUY 用綠、漲用紅會在同畫面並存——請用「形狀/位置/標籤」區隔語意：訊號用實心 pill/badge（有文字 BUY/WATCH），漲跌用數字顏色 + 箭頭。設計上明確區分「這是訊號狀態」vs「這是漲跌幅」，例如訊號 badge 一律帶文字標籤與 icon，漲跌幅一律是裸數字 + 三角箭頭，讓兩套色不會被誤讀。

**來源徽章色**：AI 生成 = 紫 `#a855f7`、手動 = 藍 `#3b82f6`、預設 = 灰 `#64748b`。

**Regime 三態燈號色**：多頭 bull = 紅、盤整 range = 黃/琥珀、空頭 bear = 綠（同樣遵守紅漲綠跌邏輯，多頭市況用紅）。

**因子流派配色**（7 流派各一色，用於雷達圖/評分條分組著色）：value 價值、growth 成長、momentum 動能、chips 籌碼、revenue 營收、reversal 反轉、breakout 突破——各給一個可區分的 hue（建議偏冷的科技感調色盤，飽和度適中，不刺眼），missing 缺料因子統一灰。

### 字型配對
- **數字**：用 tabular / monospace 等寬數字字型（建議 `JetBrains Mono`、`IBM Plex Mono` 或 `Geist Mono`），所有價格、分數、百分比、代號都對齊等寬，方便縱向掃讀比較。股票代號用 mono。
- **中文 UI 文字**：`Noto Sans TC` / `PingFang TC`，標題可用稍重字重（600–700），內文 400–500。
- **英文/標籤**：搭配 `Inter` 或 `Geist Sans`。
- 建立清楚字級階層：頁面標題、卡片標題、區塊小標（小寫上標 muted label，沿用現有 `.label` 概念但更精緻）、數據主值（大、mono、可帶單位）、輔助說明。

### 形狀 / 尺度
- 圓角 scale：卡片 `rounded-xl`（~12px）、按鈕/input/chip `rounded-lg`（~8px）、pill/badge 全圓角。
- 陰影：dark mode 用極克制陰影 + 1px 邊框（`line` 色）界定層級，靠 panel/panel2 的明度差堆疊層次，而非重陰影。hover 態可加微弱發光（accent 色 1px ring）。
- 間距 scale：建立 4/8/12/16/24/32 的 spacing scale，資料密集區用緊湊間距、敘事區（專家紀要、理由）用寬鬆間距，形成節奏。

### Data-viz 視覺規範
- **評分**：signal_score（0–100）用評分環（donut/radial gauge）或水平評分條，標出 65（BUY 門檻）與 50（WATCH 門檻）兩條閾值刻度線。
- **因子**：29 個因子（0–1）用**雷達圖**（按 7 流派分區著色）或分組水平條，缺料因子顯示為灰色虛線/置空，hover 顯示因子中文 description 與所屬 school。
- **權益曲線**：line/area chart，上漲段紅、回撤段綠（紅漲綠跌），標註最大回撤區間（drawdown band）。
- **漲跌**：迷你 sparkline + 三角箭頭，紅漲綠跌。
- **權重圓餅**：weight_fundamental/technical/backtest 三權重用小圓餅或 stacked bar，即時反映加總是否 = 1.00。
- 圖表風格：細線、grid 線極淡、無多餘裝飾、tooltip 深色玻璃感、軸標 mono 數字。整體像 Linear 的圖表——資訊清楚、零花俏。

### Icon 風格
- 全面改用 `lucide` 線性 icon（1.5px stroke），取代現版所有 emoji。趨勢用 `trending-up`/`trending-down`、訊號用實心狀態點、籌碼/法人/營收等各配一個語意 icon。emoji 僅在「市場氛圍燈號」「夜盤方向」「量價結論」等原始資料本身帶 emoji 的字串中保留呈現，UI chrome 一律用 lucide。

### 整體 mood
冷靜、銳利、可信、密度高但呼吸順暢；像一個給專業人士的終端機，但有現代 SaaS 的精緻與親和。深色為主，狀態色克制使用、只在關鍵處點亮。

## 4. 資訊架構 / Sitemap

頂部固定導覽列（補上現版缺的 **active 高亮態**）：
- **今日訊號**（Dashboard，首頁）
- **策略庫**（列表 → 詳情 → 新建 / AI 生成）
- **回測 / 成績單**（Performance）
- **盤前快報**（夜盤）

外加一個**常駐右側可收合的 AI 對話側欄（Copilot）**，跨所有頁面可喚出（快捷鍵 `Cmd/Ctrl + K` 或右下角浮動按鈕）。

頂部全域元件：左 logo + 站名、中導覽、右側「大盤 regime 燈號」常駐 mini-indicator（多頭紅/盤整黃/空頭綠 + 站上/跌破月線）、執行狀態、AI Copilot 喚出鈕。底部固定免責聲明（克制、small、muted）。

## 5. 逐畫面設計規格

### 畫面 A — 今日訊號 Dashboard（首頁，最重要）
**目的**：盤後一眼看懂「今天市場怎樣 + 有哪些票可以動作 + 為什麼」。

**版面結構（由上而下）**：
1. **市場狀態列（Market Banner）**：橫跨頂部。並列呈現 — 大盤 regime 燈號（🧭 多頭/盤整/空頭 + market.note 中文字串 + close / ma20 數值）、夜盤濾鏡（順風🟢/逆風🔴/中性⚪ + 台指期夜盤 ±%）、市場氛圍 5 級燈號（🟢偏多 / 🟡中性偏多 / 🟠中性偏空 / 🔴偏空）、池內統計（均漲% / 上漲檔數 / 站月線檔數）、降級提示（downgraded：「X 檔 BUY 已因空頭/夜盤降為 WATCH」）。
2. **摘要 KPI 區**：summary 的 total / buy / watch / skip / error 做成可點擊的 **segmented control / filter tabs**（點 BUY 只看 BUY），每個帶計數 + 狀態色。旁邊放策略選擇 dropdown（自訂下拉，非原生 select）+「執行選股」主按鈕。
3. **今日訊號表（核心）**：高密度資料表，每列一檔。欄位：action badge（BUY綠/WATCH黃/SKIP灰/ERROR紅）、stock_id（mono）+ name、signal_score（小評分環或評分條，標 65/50 閾值）、chg_5d / chg_20d（紅漲綠跌 + 箭頭）、pct_from_high（距 52 週高）、vol_ratio（量比）、above_ma20/above_ma60（兩個狀態 chip）、backtest_winrate %（+ samples）、tech_signals（彩色 chips：均線多頭/布林下軌反彈/KD黃金交叉/MACD多頭）、夜盤順風/逆風標籤、regime 標籤。**可排序、可篩選**（系統預設排序 BUY>WATCH>SKIP，同級分數降序）。整列 hover 高亮，點列展開或進個股詳情。

**狀態**：
- **載入/執行中**：`/api/run` 要跑 1–2 分鐘——設計**逐檔進度 + 骨架列（skeleton rows）**，顯示「掃描中 X/N 檔」，可取消。不要只把按鈕變灰。
- **空狀態**：尚無今日結果 → 引導「選擇策略並執行」。watchlist 未設定 → 「尚未設定觀察池（Google Sheet）」空態插圖 + 說明。
- **錯誤**：用 toast（非原生 alert）+ 行內錯誤卡。
- **防呆**：SKIP/ERROR 列沒有 signal_score/trend/價位，要優雅留白（顯示「—」或「資料不足」），不可破版。

### 畫面 B — 個股詳情 / 個股卡片
**目的**：點一檔，完整呈現「為什麼這個訊號 + 怎麼交易 + 風險」。

**版面（可做成大卡片或全頁，4 大資訊區）**：
1. **頭部**：stock_id + name（大、mono）、action badge、signal_score 大評分環（標閾值）、date、所用 strategy。
2. **① 交易計畫**：entry_price（明日開盤進場參考）、stop_loss_price（-8%）、target_price（+10%）、risk_reward_ratio（顯示為 1:1.25）、position_size_pct（建議部位，上限 20%）、entry_rule（中文進場規則句直接呈現）。用價格軸視覺呈現停損—進場—目標三點位。
3. **② 趨勢**：chg_5d / chg_20d（紅漲綠跌）、vol_ratio、pct_from_high、above_ma20 / above_ma60 兩個布林 chip，配迷你走勢 sparkline。
4. **③ 評分拆解**：fundamental_pass ✅/❌（+ eps_min / roe_min）、tech_score、backtest_winrate %（N 次 samples）、**因子雷達圖**（29 因子按 7 流派著色，缺料灰）、tech_signals chips。若 V3.4 資料具備：分市況回測 by_regime{多/盤/空} 的勝率分桶、勝率 Wilson 95% 信賴區間（誤差帶視覺化）、significance 標籤（INSUFFICIENT/WEAK/可信，樣本少時顯示「僅供參考」警示）。
5. **④ 量價解析**：volume_patterns chips（倍量柱/梯量柱/縮量柱/低量柱/平量柱/放量滯漲——**放量滯漲為紅色警示**）、volume_verdict 結論句（含 emoji）。
6. **⑤ 風險提示**：risk_notes 做成 ⚠️ 警示標籤列（樣本不足/基本面未過/勝率低於五成/突破布林上軌追高/放量滯漲出貨/被大盤或夜盤降級）。
7. **⑥ 專家會議紀要（V3.4 亮點）**：expert_memo 六位專家各一句（📊資料 data_expert / 📈技術 tech_expert / 💰基本面 fund_expert / 🏦籌碼 chips_expert / 🌐市場 market_expert / 👑首席 chief_conclusion），做成**對話氣泡或專家卡片陣列**，每位有頭像/icon + 角色名 + ≤40 字結論。標示來源 🤖 LLM 或 📋 模板（模板時顯示「LLM 配額用罄，改用模板」狀態）。

**狀態**：缺欄位優雅降級；SKIP/ERROR 檔只顯示基本資訊 + risk_notes。

### 畫面 C — 策略庫列表 + 策略詳情 + 建立/調參 + AI 生成
**C1 策略庫列表**：卡片 grid。每卡：name、source 徽章（default紫藍灰三色）、description（clamp）、updated_at、關鍵參數預覽（EPS≥ / ROE≥ / 總分≥ / 停利 / 停損 / 持有日）。補上**搜尋 / 排序 / 流派篩選**（現版沒有）。default 與 conservative 的刪除鈕 disabled 並標「內建不可刪」。三態：loading 骨架卡 / error / empty。

**C2 策略詳情**：標題卡 + params 分組呈現（非平鋪 key/value）+「跑一次」按鈕 → 結果用與 Dashboard 統一的訊號表元件（不要兩種呈現）。

**C3 建立 / 調參表單（StrategyForm 重設計）**：大型多區塊參數表單，分 6–7 區（基本面門檻 / 回測與訊號 / 風險 / 評分加權 / 技術訊號開關 / 大盤濾鏡）。設計要點：
- boolean 參數（use_ma_alignment / use_bollinger_bounce / use_kd_golden_cross / use_macd_bullish / use_volume_patterns / market_filter_enabled / fundamental_pass_required）用**自訂 toggle switch**。
- 數值範圍參數用 **slider + 數字輸入** 並列，顯示範圍夾擠（target_return/stop_loss 1%~50%、分數 0~100、回測 1~10 年、持有 1~120 日）。
- target_return/stop_loss 以**百分比顯示**（0.10 → 顯示 10%）。
- 三權重 weight_fundamental / weight_technical / weight_backtest 即時驗證**加總 = 1.00**，用權重圓餅/stacked bar 即時回饋，✓ 達標 / ⚠️ 未達標。
- 考慮步驟式（stepper）或分頁式分組，降低 20+ 欄位的壓迫感。

**C4 AI 自然語言生成**：prompt textarea（大、舒適）+ 可選策略名稱 + 4 個範例 chip（點擊填入：短線/存股/保守/激進）+「用 AI 生策略」鈕。流程：生成 → **AI 草稿預覽卡**（可串流逐字浮現的打字感）→ 下接 C3 表單預填 AI 參數供微調 → 確認儲存。支援「重新生成」「與當前對照 diff」。載入態（thinking）、500 錯誤態（如未設 API Key → 友善提示）。

### 畫面 D — 回測 / Performance 成績單
**目的**：驗證策略到底準不準。

**版面**：
1. **頂部 summary 卡**：count（完成筆數）、winrate_t20（T+20 勝率%）、avg_t20（T+20 平均報酬%）、hit_target（觸及+10%次數）、hit_stop（觸及-8%次數）。做成 metric 卡（大 mono 數字 + 趨勢色）。
2. **權益曲線圖**（V3.4 trades 資料）：line/area，紅漲綠跌，標最大回撤帶。
3. **回測指標**：winrate / samples / avg_return（現役回測**僅這三項，UI 不要出現夏普/最大回撤欄位**）；V3.4 進階回測若有則加：sharpe / sortino / max_drawdown / profit_factor、**分市況 by_regime{bull/range/bear}** 績效分桶 bar chart、**樣本外 oos**（in_sample vs out_sample + degradation verdict 退化對比）、significance 標籤 + Wilson 信賴區間誤差帶。
4. **個別訊號明細表**：每筆 BUY 的 signal_date / entry_close / entry_open / t5_ret / t10_ret / t20_ret / hit_target / hit_stop / status（追蹤中/完成），可展開看 T+5/T+10/T+20 報酬軌跡迷你折線。status「追蹤中」顯示進度（滿 20 交易日完成）。

**狀態**：累積 < 5 筆 → 「樣本累積中，成績單需 ≥5 筆」空態。

### 畫面 E — 夜盤盤前快報（手機優先體驗）
**目的**：08:00 前 30 秒看懂開盤方向 + 昨日訊號順逆風。

**版面（為手機豎屏優化的單欄敘事卡）**：
1. **頂部大數字**：台指期夜盤 ±%（±點數）特大顯示（紅漲綠跌）+ 五級方向燈號（🚀大漲 / 🟢小漲 / ⚪平盤 / 🟠小跌 / 🔴大跌）+ 一句方向預判 direction。近月 close / volume 輔助小字。
2. **昨日訊號 × 夜盤對照**：列出昨日 BUY/WATCH，每檔掛「夜盤順風🟢 / 逆風🔴 / 中性⚪」標籤 + 一句承接操作指引。
3. 標題含日期與週幾、底部免責。整體要能在手機上一屏看完重點，字大、留白足、低認知負荷。

### 畫面 F — Multi-Agent AI 對話介面（Copilot 側欄）
**目的**：用對話管理系統，並把多專家協作「會議感」做成介面亮點。

**形態**：類 CopilotKit 的右側可收合 side panel（桌機）/ 全屏 sheet（手機），跨頁常駐喚出。
**內容**：
- **訊息流**：使用者訊息泡泡（右、accent）、AI 回覆泡泡（左、panel2）。支援串流逐字輸出、工具執行卡片（顯示「正在重跑選股…」「正在回測…」進度）。
- **四類動作的 UI 呈現**：
  1. 管理 watchlist（「把 2330 加進觀察池，category 放 AI」→ 顯示確認卡 + 結果）。
  2. 重跑選股（挑策略觸發 → 嵌入式迷你訊號表結果）。
  3. what-if 回測（調因子權重/持有週期/停損停利 → 即時回傳 by_regime 績效 + 權益曲線小圖對照「改前 vs 改後」）。
  4. 呈現多專家「會議」串流：六位專家（📊資料/📈技術/💰基本面/🏦籌碼/🌐市場/👑首席）依序發言的對話氣泡，每位有專屬 icon/色，首席結論最後收斂並加重強調。標 🤖LLM/📋模板來源。
- **輸入區**：底部 textarea + 範例 prompt chips（「今天有哪些 BUY？」「把這檔停損改成 5% 回測看看」「2330 為什麼只是 WATCH？」）。

## 6. 關鍵元件庫（component sheet 要交付）

- **ActionBadge**：BUY/WATCH/SKIP/ERROR 四態實心 pill（狀態色 + 文字 + 狀態點），多尺寸。
- **SourceBadge**：AI紫/手動藍/預設灰。
- **ChangeValue**：漲跌數字元件（紅漲綠跌 + 三角箭頭 + mono），統一管理漲跌色。
- **SignalScoreGauge**：0–100 評分環/條，標 65/50 閾值線。
- **FactorRadar**：29 因子雷達圖，7 流派著色 + 缺料灰 + hover tooltip。
- **FactorBar**：單因子 0–1 水平評分條（流派色）。
- **RegimeIndicator**：多/盤/空三態燈號（紅/黃/綠）。
- **TechSignalChip / VolumePatternChip**：技術訊號與量價型態彩色 chip（放量滯漲紅警示）。
- **MA Status Chip**：above_ma20 / above_ma60 站上/跌破狀態。
- **StockSignalRow / StockCard**：統一的訊號列與個股卡（Dashboard 與策略詳情共用，解決現版兩種呈現不一致）。
- **TradePlanWidget**：停損—進場—目標 三點位價格軸。
- **EquityCurveChart / RegimeBucketBars / OOSCompare**：回測圖表組。
- **ExpertMemoCard / ExpertChatBubble**：專家紀要卡與會議氣泡。
- **MetricCard**：大 mono 數字 + label + 趨勢色（summary/Performance 用）。
- **正式 Modal / Toast / Dropdown / Tooltip / Toggle / Slider**：取代原生 confirm/alert/select/checkbox。
- **SkeletonRow / EmptyState / ErrorCard / ProgressRunner（逐檔掃描進度）**。

## 7. 互動、微動效、響應式、無障礙

**互動/微動效**（克制、有目的，不浮誇）：
- 訊號表列 hover 微高亮 + accent ring；展開個股卡用順滑高度展開。
- 評分環/權益曲線載入時數值與線條 ease-out 動畫繪入。
- 訊號 badge、chips 出現時極輕微 fade/scale。
- 執行選股：逐檔進度條推進 + 計數跳動。
- AI 回覆與專家會議：串流打字感、專家逐位浮現。
- 篩選 segmented control 切換：列表平滑過濾轉場。
- 刪除策略：自訂 modal 確認（非 confirm），危險動作紅色。

**響應式（desktop-first，手機可用）**：
- 桌機：多欄、寬訊號表、Copilot 為右側固定欄。
- 平板：表格欄位折疊次要欄、Copilot 浮層。
- 手機：訊號表降級為**堆疊卡片列表**（每檔一張精簡卡：action + 代號名稱 + 分數 + 漲跌 + 關鍵 chips），盤前快報為單欄敘事（手機是它的主場），Copilot 為全屏 sheet，導覽收成底部 tab bar 或漢堡。

**無障礙 / 可讀性（數字密集場景關鍵）**：
- 深色背景下主文字對比 ≥ AA（`#e6e9ee` on `#0b0d10`）；數字務必清晰、tabular 對齊。
- 不單靠顏色傳達狀態：訊號 badge 永遠帶文字標籤、漲跌永遠帶箭頭方向、regime 帶文字——色盲（尤其紅綠色盲，本產品紅綠是核心！）也能讀懂。提供「漲跌色可切換」的設計考量（紅漲綠跌 / 綠漲紅跌）作為設定項。
- 字級不過小（資料表最小 ~13px，數字可略大）；行高與欄距保證掃讀；focus 態清晰（accent ring）。
- 大量數字區用斑馬紋或極淡分隔線輔助橫向對齊閱讀。

## 8. 交付物

請產出：
1. **High-fidelity 畫面**（dark mode 為主，**另出 light mode 版**作為深淺雙色系統驗證）：涵蓋畫面 A–F 全部，至少各 1 張主畫面。
2. **完整 design system / component sheet**：色彩 token（含漲跌色與訊號色雙軌、7 流派色）、字型階層、spacing/radius scale、上述全部關鍵元件的各狀態。
3. **關鍵狀態全覆蓋**：每個資料畫面都要出 **default / loading（骨架）/ empty / error / 執行中進度** 五態；SKIP/ERROR 缺欄位的降級呈現；LLM 配額用罄改模板、樣本不足「僅供參考」、因子缺料「資料不足」的提示態。
4. **手機版關鍵畫面**：今日訊號（堆疊卡）、盤前快報（單欄）、Copilot（全屏）。
5. **資料視覺化規格頁**：評分環、因子雷達、權益曲線、by_regime 分桶、權重圓餅的樣式與紅漲綠跌規範示意。

**鐵律重申**：台股**紅漲綠跌**（與美股相反），所有漲跌相關視覺一律遵守；訊號狀態色（BUY綠/WATCH黃/SKIP灰/ERROR紅）與漲跌色分軌管理、靠形狀與標籤區隔，絕不讓使用者把「綠色 BUY badge」誤讀成「下跌」。