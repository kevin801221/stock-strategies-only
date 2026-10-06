const BASE = (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/$/, "");

export type StrategyParams = Record<string, number | boolean>;
export type Strategy = {
  id: string;
  name: string;
  description?: string;
  source?: "default" | "manual" | "ai";
  created_at?: string;
  updated_at?: string;
  params: StrategyParams;
  error?: string;
};
export type Market = { bullish: boolean; close?: number | null; ma20?: number | null; note: string };
export type Action = "BUY" | "WATCH" | "SKIP" | "ERROR";
export type StockResult = {
  stock_id: string;
  name?: string;
  action: Action;
  date?: string;
  signal_score?: number;
  entry_price?: number;
  stop_loss_price?: number;
  target_price?: number;
  risk_reward_ratio?: number;
  position_size_pct?: number;
  entry_rule?: string;
  risk_notes?: string[];
  components?: {
    fundamental_pass?: boolean;
    eps_min?: number | null;
    roe_min?: number | null;
    tech_score?: number;
    tech_signals?: string[];
    backtest_winrate?: number | null;
    backtest_samples?: number;
    volume_patterns?: string[];
    volume_verdict?: string;
  };
  trend?: { chg_5d?: number; chg_20d?: number; vol_ratio?: number; pct_from_high?: number; above_ma20?: boolean; above_ma60?: boolean };
};
export type RunResult = {
  strategy: { id: string; name: string };
  market: Market;
  downgraded: number;
  summary: { total: number; buy: number; watch: number; skip: number; error: number };
  results: StockResult[];
};
export type RunJob = {
  id: string;
  status: "queued" | "running" | "cancelling" | "completed" | "cancelled" | "failed";
  strategy: { id: string; name: string };
  completed: number;
  total: number | null;
  current: string | null;
  created_at: string;
  result: RunResult | null;
  error: string | null;
};
export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "發生未預期的錯誤，請稍後再試";
}

async function jfetch<T>(path: string, init?: RequestInit, timeout = 30_000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const abort = () => controller.abort();
  init?.signal?.addEventListener("abort", abort, { once: true });
  if (init?.signal?.aborted) controller.abort();
  try {
    const headers = new Headers(init?.headers);
    if (init?.body) headers.set("Content-Type", "application/json");
    const res = await fetch(`${BASE}${path}`, { ...init, headers, signal: controller.signal, cache: "no-store" });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      const detail: unknown = body?.detail;
      const message = typeof detail === "string" ? detail
        : Array.isArray(detail) ? detail.map((item: { loc?: string[]; msg?: string }) => `${item.loc?.slice(1).join(".") || "欄位"}：${item.msg || "格式錯誤"}`).join("；")
        : `請求失敗（${res.status}），請稍後重試`;
      throw new ApiError(message, res.status);
    }
    return await res.json() as T;
  } catch (error) {
    if (init?.signal?.aborted) throw error;
    if (controller.signal.aborted) throw new Error("連線逾時，請稍後重試；背景選股任務會繼續執行");
    if (error instanceof TypeError) throw new Error("無法連線至服務，請確認後端已啟動後重試");
    throw error;
  } finally {
    clearTimeout(timer);
    init?.signal?.removeEventListener("abort", abort);
  }
}

export const api = {
  listStrategies: (signal?: AbortSignal) => jfetch<{ strategies: Strategy[] }>("/api/strategies", { signal }),
  getDefaults: (signal?: AbortSignal) => jfetch<{ params: StrategyParams }>("/api/strategies/defaults", { signal }),
  getStrategy: (id: string, signal?: AbortSignal) => jfetch<Strategy>(`/api/strategies/${encodeURIComponent(id)}`, { signal }),
  saveStrategy: (s: Partial<Strategy>) => jfetch<Strategy>("/api/strategies", { method: "POST", body: JSON.stringify(s) }),
  deleteStrategy: (id: string) => jfetch<{ ok: boolean }>(`/api/strategies/${encodeURIComponent(id)}`, { method: "DELETE" }),
  generateAI: (prompt: string, name?: string) => jfetch<Strategy>("/api/strategies/generate", { method: "POST", body: JSON.stringify({ prompt, name }) }, 120_000),
  getMarket: (signal?: AbortSignal) => jfetch<Market>("/api/market", { signal }),
  getWatchlist: (signal?: AbortSignal) => jfetch<{ items: { stock_id: string; name?: string }[]; error?: string }>("/api/watchlist", { signal }),
  startRun: (strategy_id: string) => jfetch<RunJob>("/api/runs", { method: "POST", body: JSON.stringify({ strategy_id }) }),
  getRun: (id: string, signal?: AbortSignal) => jfetch<RunJob>(`/api/runs/${encodeURIComponent(id)}`, { signal }),
  cancelRun: (id: string) => jfetch<RunJob>(`/api/runs/${encodeURIComponent(id)}`, { method: "DELETE" }),
};
