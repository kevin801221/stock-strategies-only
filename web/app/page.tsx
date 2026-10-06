"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, errorMessage, Market, Strategy } from "@/lib/api";
import { SourceBadge } from "@/components/ActionBadge";
import { EmptyState, ErrorCard, Skeleton } from "@/components/Feedback";
import RunControl from "@/components/RunControl";
import SignalResults from "@/components/SignalResults";
import { useRun } from "@/hooks/useRun";

export default function Dashboard() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [picked, setPicked] = useState("");
  const [market, setMarket] = useState<Market | null>(null);
  const [watchCount, setWatchCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [marketLoading, setMarketLoading] = useState(true);
  const [watchLoading, setWatchLoading] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [reload, setReload] = useState(0);
  const run = useRun(picked);
  useEffect(() => {
    const controller = new AbortController();
    const signal = controller.signal;
    const fail = (key: string, error: unknown) => { if (!signal.aborted) setErrors(prev => ({ ...prev, [key]: errorMessage(error) })); };
    setErrors({}); setLoading(true); setMarketLoading(true); setWatchLoading(true);
    api.listStrategies(signal).then(data => {
      const usable = data.strategies.filter(s => !s.error);
      setStrategies(usable);
      let remembered = "";
      try { remembered = sessionStorage.getItem("screening:selected") || ""; } catch {}
      setPicked(prev => [prev, remembered, "default"].find(id => usable.some(s => s.id === id)) || usable[0]?.id || "");
      if (usable.length !== data.strategies.length) fail("strategies", new Error("部分策略檔無法讀取，請到策略庫查看"));
    }).catch(error => fail("strategies", error)).finally(() => { if (!signal.aborted) setLoading(false); });
    api.getMarket(signal).then(setMarket).catch(error => fail("market", error)).finally(() => { if (!signal.aborted) setMarketLoading(false); });
    api.getWatchlist(signal).then(data => { setWatchCount(data.items.length); if (data.error) fail("watchlist", new Error(data.error)); }).catch(error => fail("watchlist", error)).finally(() => { if (!signal.aborted) setWatchLoading(false); });
    return () => controller.abort();
  }, [reload]);
  const selected = strategies.find(s => s.id === picked);
  const displayedMarket = run.result?.market || market;
  const marketKnown = displayedMarket?.close != null;
  return <div className="space-y-8">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">YOUR MARKET, IN FOCUS</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">今日訊號</h1><p className="mt-2 text-sm text-muted">從市場脈動到個股判斷，讓每一次研究都有依據。</p></div><Link href="/strategies" className="btn-ghost">管理策略 <span aria-hidden="true">↗</span></Link></div>
    <div className="grid gap-4 md:grid-cols-3">
      <div className="card relative overflow-hidden"><p className="label">加權指數 · 市場狀態</p><div className={`mt-3 text-2xl font-semibold ${marketKnown ? displayedMarket?.bullish ? "text-rise" : "text-fall" : "text-muted"}`}>{marketLoading && !displayedMarket ? "載入中…" : !marketKnown ? "資料待確認" : displayedMarket?.bullish ? "▲ 站上均線" : "▼ 跌破均線"}</div><p className="mt-3 text-xs leading-6 text-muted">{errors.market || displayedMarket?.note || "市場資料尚未取得"}</p>{marketKnown && <div className="mt-3 border-t border-line pt-3 font-mono text-xs text-muted">加權 {displayedMarket?.close?.toLocaleString("zh-TW")} <span className="mx-2">/</span> 均線 {displayedMarket?.ma20?.toLocaleString("zh-TW", { maximumFractionDigits: 0 })}</div>}</div>
      <div className="card"><p className="label">我的觀察池</p><div className="mt-3 font-mono text-3xl">{watchLoading ? "—" : errors.watchlist ? "—" : watchCount ?? "—"}<span className="ml-2 text-sm text-muted">檔股票</span></div><p className="mt-3 text-xs leading-6 text-muted">{errors.watchlist ? "尚未連接觀察池，請確認 Google Sheet 設定。" : "同步 Google Sheet 中啟用的股票，每次執行重新讀取。"}</p></div>
      <div className="card"><p className="label">策略工作區</p><div className="mt-3 font-mono text-3xl">{loading ? "—" : strategies.length}<span className="ml-2 text-sm text-muted">個可用策略</span></div><p className="mt-3 text-xs leading-6 text-muted">用既有策略開始，或建立適合自己的篩選條件。</p><Link href="/strategies/ai" className="mt-3 inline-block text-xs text-blue-300 hover:underline">用 AI 設計策略 →</Link></div>
    </div>
    {!!Object.keys(errors).length && <ErrorCard message={Object.values(errors).join("；")} retry={() => setReload(value => value + 1)} />}
    <section className="card">
      <div className="mb-5 flex items-center gap-3"><span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10 font-mono text-xs text-accent">01</span><h2 className="font-medium">選擇策略，開始今日研究</h2></div>
      {loading ? <Skeleton rows={1} /> : !strategies.length ? <EmptyState title="先建立你的第一個策略"><Link href="/strategies/new" className="btn-primary mt-3">建立策略</Link></EmptyState> : <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div><label htmlFor="strategy" className="label">本次使用策略</label><select id="strategy" className="input" value={picked} disabled={run.running} onChange={e => setPicked(e.target.value)}>{strategies.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
          {selected && <div className="mt-3 space-y-2"><SourceBadge source={selected.source} /><p className="text-xs leading-6 text-muted">{selected.description}</p><Link className="text-xs text-blue-300 hover:underline" href={`/strategies/${selected.id}`}>查看與調整參數 →</Link></div>}
        </div><div className="lg:border-l lg:border-line lg:pl-6"><RunControl run={run} disabled={!picked} /></div>
      </div>}
    </section>
    {run.result ? <SignalResults run={run.result} /> : !run.running && <EmptyState title="準備好，讓數據說話">選擇一個策略並開始選股。完成後可比較評分、篩選訊號，並展開查看個股風險與交易參考。</EmptyState>}
  </div>;
}
