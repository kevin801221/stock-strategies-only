"use client";
import { useMemo, useState } from "react";
import { Action, RunResult, StockResult } from "@/lib/api";
import { ActionBadge } from "./ActionBadge";
import { EmptyState } from "./Feedback";

const labels = { ALL: "全部訊號", BUY: "可進場", WATCH: "持續觀察", SKIP: "未符合", ERROR: "資料異常" };
const number = (value?: number | null, digits = 1) => typeof value === "number" && Number.isFinite(value) ? value.toLocaleString("zh-TW", { maximumFractionDigits: digits }) : "—";

function Change({ value }: { value?: number }) {
  return <span className={`font-mono ${value == null || value === 0 ? "text-muted" : value > 0 ? "text-rise" : "text-fall"}`}>
    {value == null ? "—" : `${value > 0 ? "▲ +" : value < 0 ? "▼ " : ""}${number(value, 2)}%`}
  </span>;
}
function exportRows(rows: StockResult[], strategy: string) {
  const escape = (value: unknown) => {
    let text = String(value ?? "");
    if (/^[=+@\-\t\r]/.test(text)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  };
  const data = [
    ["代號", "名稱", "訊號", "綜合分", "參考價", "停損價", "目標價", "回測勝率", "樣本數", "風險提示"],
    ...rows.map(r => [r.stock_id, r.name, r.action, r.signal_score, r.entry_price, r.stop_loss_price, r.target_price, r.components?.backtest_winrate == null ? "" : r.components.backtest_winrate * 100, r.components?.backtest_samples, r.risk_notes?.join("；")]),
  ].map(row => row.map(escape).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob(["\ufeff", data], { type: "text/csv;charset=utf-8;" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `signals-${strategy}-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function SignalResults({ run }: { run: RunResult }) {
  const [filter, setFilter] = useState<Action | "ALL">("ALL");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("signal");
  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const result = run.results.filter(r => (filter === "ALL" || r.action === filter) && `${r.stock_id} ${r.name || ""}`.toLowerCase().includes(needle));
    if (sort === "score") result.sort((a, b) => (b.signal_score ?? -1) - (a.signal_score ?? -1));
    if (sort === "stock") result.sort((a, b) => a.stock_id.localeCompare(b.stock_id));
    if (sort === "winrate") result.sort((a, b) => (b.components?.backtest_winrate ?? -1) - (a.components?.backtest_winrate ?? -1));
    return result;
  }, [run, filter, query, sort]);
  return <section className="space-y-4" aria-label="選股結果">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><p className="eyebrow">SCREENING RESULTS</p><h2 className="mt-1 text-xl font-semibold">{run.strategy.name} <span className="text-sm font-normal text-muted">執行結果</span></h2></div>
      <button className="btn-ghost" disabled={!rows.length} onClick={() => exportRows(rows, run.strategy.id)}>匯出 CSV <span aria-hidden="true">↓</span></button>
    </div>
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      {(Object.keys(labels) as (keyof typeof labels)[]).map(action => {
        const count = action === "ALL" ? run.summary.total : run.summary[action.toLowerCase() as "buy" | "watch" | "skip" | "error"];
        return <button key={action} aria-pressed={filter === action} onClick={() => setFilter(action)} className={`rounded-xl border px-4 py-3 text-left transition ${filter === action ? "border-accent bg-accent/10" : "border-line bg-panel hover:bg-panel2"}`}>
          <div className="text-xs text-muted">{labels[action]}</div>
          <div className="mt-2 flex items-end justify-between"><span className="font-mono text-2xl">{count}</span><span className={`text-xs ${action === "BUY" ? "text-buy" : action === "WATCH" ? "text-watch" : action === "ERROR" ? "text-err" : "text-muted"}`}>{action}</span></div>
        </button>;
      })}
    </div>
    <div className="flex flex-wrap gap-2 text-xs text-muted"><span>{run.market.note}</span>{run.downgraded > 0 && <span className="text-watch">{run.downgraded} 檔因大盤濾鏡降為 WATCH</span>}</div>
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <input type="search" className="input sm:max-w-xs" aria-label="搜尋股票" placeholder="搜尋股票代號或名稱…" value={query} onChange={e => setQuery(e.target.value)} />
      <select aria-label="結果排序" className="input sm:w-auto" value={sort} onChange={e => setSort(e.target.value)}>
        <option value="signal">訊號優先</option><option value="score">綜合分：高到低</option><option value="winrate">回測勝率：高到低</option><option value="stock">股票代號</option>
      </select>
      <span className="text-xs text-muted sm:ml-auto">顯示 {rows.length} / {run.summary.total} 檔</span>
    </div>
    {!rows.length ? <EmptyState title={run.summary.total ? "沒有符合條件的股票" : "觀察池尚無可評估股票"}>
      {run.summary.total ? <button onClick={() => { setFilter("ALL"); setQuery(""); }} className="btn-ghost mt-3">清除篩選</button> : "請確認 Google Sheet 的 watchlist 已有啟用的股票。"}
    </EmptyState> : <div className="overflow-hidden rounded-xl border border-line bg-panel">
      <div className="hidden grid-cols-[1.5fr_1fr_1fr_1fr_1fr_24px] gap-4 border-b border-line bg-panel2/50 px-5 py-3 text-xs text-muted md:grid" aria-hidden="true">
        <span>股票 / 訊號</span><span>綜合評分</span><span>5 日 / 20 日漲跌</span><span>回測勝率</span><span>參考收盤價</span><span />
      </div>
      {rows.map((row, index) => <StockCard key={`${row.stock_id}-${index}`} row={row} />)}
    </div>}
  </section>;
}

function StockCard({ row: r }: { row: StockResult }) {
  const c = r.components;
  return <details className="group border-b border-line last:border-0 open:bg-panel2/30">
    <summary className="grid cursor-pointer list-none grid-cols-[1fr_auto] items-center gap-4 px-4 py-4 transition hover:bg-panel2/60 sm:px-5 md:grid-cols-[1.5fr_1fr_1fr_1fr_1fr_24px]">
      <div className="min-w-0"><div className="mb-2 flex flex-wrap items-center gap-2"><span className="font-mono font-semibold">{r.stock_id}</span><ActionBadge action={r.action} /></div><div className="truncate text-sm text-muted">{r.name || "未提供名稱"}</div></div>
      <div className="w-24 md:w-auto"><div className="font-mono text-xl">{number(r.signal_score)}<span className="ml-1 text-xs text-muted">/100</span></div><div className="mt-2 h-1 overflow-hidden rounded-full bg-line"><div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(100, Math.max(0, r.signal_score ?? 0))}%` }} /></div></div>
      <div className="hidden space-y-1 text-xs md:block"><div><Change value={r.trend?.chg_5d} /></div><div><Change value={r.trend?.chg_20d} /></div></div>
      <div className="hidden md:block"><div className="font-mono text-sm">{c?.backtest_winrate == null ? "—" : `${number(c.backtest_winrate * 100)}%`}</div><div className="mt-1 text-xs text-muted">{c?.backtest_samples ?? 0} 次樣本</div></div>
      <div className="hidden font-mono text-sm md:block">{number(r.entry_price, 2)}</div>
      <span className="hidden text-muted transition-transform group-open:rotate-180 md:block" aria-hidden="true">⌄</span>
      <span className="col-span-2 text-xs text-muted md:hidden">展開交易參考與風險說明 <span aria-hidden="true">⌄</span></span>
    </summary>
    <div className="border-t border-line p-4 sm:p-5">
      <div className="grid gap-6 md:grid-cols-2">
        <section><h3 className="mb-3 text-sm font-medium">交易參考</h3><dl className="grid grid-cols-3 gap-3">
          <Metric label="參考價" value={number(r.entry_price, 2)} /><Metric label="停損價" value={number(r.stop_loss_price, 2)} /><Metric label="目標價" value={number(r.target_price, 2)} />
          <Metric label="報酬 / 風險" value={number(r.risk_reward_ratio, 2)} /><Metric label="建議部位" value={r.position_size_pct == null ? "—" : `${number(r.position_size_pct)}%`} /><Metric label="資料日期" value={r.date || "—"} />
        </dl>{r.entry_rule && <p className="mt-3 text-xs leading-6 text-muted">{r.entry_rule}</p>}</section>
        <section><h3 className="mb-3 text-sm font-medium">評分與趨勢</h3><dl className="grid grid-cols-3 gap-3">
          <Metric label="技術分" value={number(c?.tech_score)} /><Metric label="基本面" value={c?.fundamental_pass == null ? "—" : c.fundamental_pass ? "符合門檻" : "未過門檻"} /><Metric label="回測勝率" value={c?.backtest_winrate == null ? "無樣本" : `${number(c.backtest_winrate * 100)}%`} />
          <div><dt className="label">5 日漲跌</dt><dd className="text-sm"><Change value={r.trend?.chg_5d} /></dd></div><div><dt className="label">20 日漲跌</dt><dd className="text-sm"><Change value={r.trend?.chg_20d} /></dd></div><Metric label="量比" value={number(r.trend?.vol_ratio, 2)} />
        </dl><p className="mt-3 text-xs text-muted">回測樣本 {c?.backtest_samples ?? 0} 次{(c?.backtest_samples ?? 0) < 8 ? " · 樣本不足，僅供參考" : ""}</p></section>
      </div>
      {!!c?.tech_signals?.length && <div className="mt-4 flex flex-wrap gap-2">{c.tech_signals.map(s => <span key={s} className="rounded-md border border-line bg-panel px-2 py-1 text-xs text-muted">{s}</span>)}</div>}
      {c?.volume_verdict && <p className="mt-3 text-xs text-muted">{c.volume_verdict}</p>}
      {!!r.risk_notes?.length && <div className="mt-4 rounded-lg border border-watch/20 bg-watch/5 p-3"><h3 className="text-xs font-medium text-watch">{r.action === "ERROR" ? "資料處理失敗" : "風險提示"}</h3><ul className="mt-2 space-y-1 text-xs leading-5 text-muted">{r.risk_notes.map((note, i) => <li key={i}>{note}</li>)}</ul></div>}
    </div>
  </details>;
}
function Metric({ label, value }: { label: string; value: string }) {
  return <div><dt className="label">{label}</dt><dd className="break-words font-mono text-sm">{value}</dd></div>;
}
