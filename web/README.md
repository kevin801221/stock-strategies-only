# 📊 Stock Strategies Web UI

Next.js + Tailwind 前端，後端是 `api/` 下的 FastAPI。

## 開發啟動

```bash
# 1. 後端（在專案根目錄）
uv sync                              # 安裝新增的 fastapi / pydantic / google-generativeai
# --reload-include 只看 Python，避免存策略 JSON 時 server 重啟把 /api/run 切斷
uv run uvicorn api.main:app --reload --reload-include '*.py' --port 8000

# 2. 前端（另開一個 terminal，進 web/）
cd web
cp .env.local.example .env.local     # 可選：需要直連後端時設定
npm install
npm run dev
```

> 選股現在採背景任務與短請求輪詢，預設可使用同源代理。需要直連時可設定 `NEXT_PUBLIC_API_BASE`；本機 FastAPI 的 CORS 預設允許 `http://localhost:3000`。

開瀏覽器 http://localhost:3000 即可。

## 環境變數

延用根目錄的 `.env`（FINMIND_TOKEN、GOOGLE_*、TELEGRAM_*），另外新增：

| 變數 | 必填 | 說明 |
| --- | --- | --- |
| `GEMINI_API_KEY` | AI 頁要用 | Google AI Studio 申請 |
| `GEMINI_MODEL` |  | 預設 `gemini-2.5-flash` |
| `CORS_ORIGINS` |  | 預設 `http://localhost:3000` |
| `STRATEGY_DIR` |  | 策略 JSON 存放目錄，預設 `./strategies` |
| `NEXT_PUBLIC_API_BASE` |  | 留空走同源代理；需要直連時設定後端公開網址 |

## 頁面

- `/` — Dashboard：選策略 + 執行今日選股
- `/strategies` — 策略庫列表
- `/strategies/new` — 手動建立策略（表單）
- `/strategies/ai` — AI 自然語言 → 策略 JSON
- `/strategies/[id]` — 策略詳情 + 跑一次 watchlist

## 資料夾

```
web/
├── app/
│   ├── layout.tsx          全站 layout / 導航
│   ├── page.tsx            Dashboard
│   ├── globals.css
│   └── strategies/
│       ├── page.tsx        列表
│       ├── new/page.tsx    手動建立
│       ├── ai/page.tsx     AI 生
│       └── [id]/page.tsx   詳情
├── components/
│   ├── ActionBadge.tsx
│   └── StrategyForm.tsx
├── lib/api.ts              fetch wrapper
├── tailwind.config.ts
├── next.config.js          /api/* 代理到 FastAPI
└── package.json
```

## 2026-09 操作改善

- 今日訊號與策略詳情共用結果畫面：BUY / WATCH / SKIP / ERROR 篩選、代號與名稱搜尋、排序、個股交易參考與風險展開、CSV 匯出。
- 執行選股改用背景任務，顯示逐檔進度，可取消並保留已完成結果。同一分頁重新整理會記住所選策略並恢復任務；重新連線會自動重試。
- 策略庫支援搜尋、來源篩選、最近更新排序、編輯參數與行內刪除確認；內建策略依 ID 保護刪除。
- 表單以百分比顯示風險與權重，檢查必填、數值範圍及三項權重合計 100%。API 仍接受正的權重總和，評分時按比例正規化。
- 缺資料時顯示未知狀態，零勝率保留為 0%；漲跌採紅漲綠跌，與 BUY / WATCH 訊號色分開。

### 背景選股 API

| 方法 | 路徑 | 行為 |
| --- | --- | --- |
| POST | `/api/runs` | `{ "strategy_id": "default", "limit": 10 }`，立即回傳 202 與任務 ID；limit 可省略 |
| GET | `/api/runs/{id}` | 取得 status、completed、total、current、result、error |
| DELETE | `/api/runs/{id}` | 要求取消；目前股票處理完後停止 |
| POST | `/api/run` | 保留同步介面，與背景介面共用執行數限制 |

任務狀態：queued → running → completed / failed；取消時為 cancelling → cancelled。

任務存在 API 程序記憶體中，**請使用單一 Uvicorn worker**。同時僅允許一個選股任務，其餘回傳 409；各檔仍依序執行並保留原有間隔。最多保留 20 次結果，完成後 1 小時過期，API 重啟會清除記錄。關閉網頁不會取消任務。取消不會中斷已送出的外部請求，因此不一定立即完成。多程序或多實例部署需另接共用任務儲存與工作佇列。

前端 GET 預設經 Next.js 同源代理，背景輪詢不需維持長連線；`NEXT_PUBLIC_API_BASE` 僅在需要直連後端時設定，並需在 build 前設定。它是瀏覽器可見的位址，遠端部署不可使用 localhost。對應網域需加入 `CORS_ORIGINS`。AI 生成仍採單次請求，前端逾時為 120 秒。

### 驗證

建議 Node.js 22.12+（CI 使用 Node 22）及 Python 3.12。

```bash
# 根目錄
uv sync --frozen
uv run pytest -q

# web/
npm ci
npm test          # jsdom + React Testing Library：表單、搜尋、任務恢復與錯誤處理
npm run check     # TypeScript
npm run build     # 正式版編譯
```

`.github/workflows/ci.yml` 會在 push 與 pull request 執行上述檢查。測試使用隔離策略目錄和模擬資料，不需金鑰，不會發送通知。

Next.js / React 已更新至 15.5.26 / 19.0.8。PostCSS 固定 8.5.28，並透過 npm override 統一 Next.js 的間接版本；更新 Next.js 後應再次執行 `npm audit --omit=dev` 與完整編譯，確認此覆寫仍有必要。
