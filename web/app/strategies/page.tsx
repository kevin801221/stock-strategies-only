"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, errorMessage, Strategy } from "@/lib/api";
import { SourceBadge } from "@/components/ActionBadge";
import { EmptyState, ErrorCard, Skeleton } from "@/components/Feedback";

export default function StrategiesPage() {
  const [items, setItems] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [sort, setSort] = useState("name");
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null);
    api.listStrategies(controller.signal).then(data => setItems(data.strategies)).catch(err => { if (!controller.signal.aborted) setError(errorMessage(err)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [reload]);
  const filtered = useMemo(() => items.filter(s => (source === "all" || s.source === source) && `${s.name} ${s.description || ""}`.toLowerCase().includes(query.trim().toLowerCase())).sort((a, b) => sort === "updated" ? (b.updated_at || "").localeCompare(a.updated_at || "") : a.name.localeCompare(b.name, "zh-TW")), [items, source, query, sort]);
  async function remove(id: string) {
    if (deleting) return;
    setDeleting(id); setError(null);
    try { await api.deleteStrategy(id); setItems(previous => previous.filter(s => s.id !== id)); setConfirmId(null); }
    catch (err) { setError(errorMessage(err)); }
    finally { setDeleting(null); }
  }
  return <div className="space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">STRATEGY WORKSPACE</p><h1 className="mt-2 text-3xl font-semibold">策略庫</h1><p className="mt-2 text-sm text-muted">把你的投資思路，整理成可重複驗證的條件。</p></div><div className="flex gap-2"><Link href="/strategies/new" className="btn-ghost">＋ 建立策略</Link><Link href="/strategies/ai" className="btn-primary">AI 策略助手 ↗</Link></div></div>
    <div className="flex flex-col gap-3 sm:flex-row"><input className="input sm:max-w-sm" type="search" aria-label="搜尋策略" placeholder="搜尋策略名稱或說明…" value={query} onChange={e => setQuery(e.target.value)} /><select className="input sm:w-auto" aria-label="策略來源" value={source} onChange={e => setSource(e.target.value)}><option value="all">所有來源</option><option value="default">內建策略</option><option value="manual">手動建立</option><option value="ai">AI 生成</option></select><select className="input sm:w-auto" aria-label="策略排序" value={sort} onChange={e => setSort(e.target.value)}><option value="name">依名稱排序</option><option value="updated">最近更新</option></select></div>
    {error && <ErrorCard message={error} retry={() => setReload(value => value + 1)} />}
    {loading ? <Skeleton /> : <>
      <p className="text-xs text-muted">{filtered.length} 個策略</p>
      {!filtered.length && !error && <EmptyState title={items.length ? "沒有符合的策略" : "建立你的第一個策略"}>{items.length ? <button className="btn-ghost mt-3" onClick={() => { setQuery(""); setSource("all"); }}>清除篩選</button> : <Link href="/strategies/new" className="btn-primary mt-3">手動建立策略</Link>}</EmptyState>}
      <div className="grid gap-4 md:grid-cols-2">{filtered.map(strategy => <article key={strategy.id} className="card flex flex-col transition hover:border-accent/30">
        <div className="flex items-center justify-between gap-3"><SourceBadge source={strategy.source} /><span className="font-mono text-xs text-muted">{strategy.id}</span></div><h2 className="mt-4 text-lg font-semibold">{strategy.name}</h2><p className="mt-2 line-clamp-3 text-sm leading-6 text-muted">{strategy.description || "尚未新增策略說明"}</p>
        {strategy.error ? <div className="mt-4"><ErrorCard message={strategy.error} /></div> : <dl className="my-5 grid grid-cols-3 gap-4 rounded-lg bg-panel2/60 p-4">{[["EPS 門檻", strategy.params.eps_threshold], ["ROE 門檻", strategy.params.roe_threshold], ["BUY 分數", strategy.params.min_total_score_for_buy], ["停利", pct(strategy.params.target_return)], ["停損", pct(strategy.params.stop_loss)], ["持有天數", strategy.params.hold_days]].map(([label, value]) => <div key={String(label)}><dt className="text-xs text-muted">{label}</dt><dd className="mt-1 font-mono text-sm">{String(value ?? "—")}</dd></div>)}</dl>}
        <div className="mt-auto border-t border-line pt-4">
          {confirmId === strategy.id ? <div className="rounded-lg border border-err/25 bg-err/5 p-3" role="group" aria-label="確認刪除策略"><p className="mb-3 text-sm">確定刪除「{strategy.name}」？此操作無法復原。</p><div className="flex gap-2"><button className="btn-danger" disabled={!!deleting} onClick={() => remove(strategy.id)}>{deleting ? "刪除中…" : "確認刪除"}</button><button className="btn-ghost" disabled={!!deleting} onClick={() => setConfirmId(null)}>保留策略</button></div></div> : <div className="flex gap-2">{!strategy.error && <Link href={`/strategies/${encodeURIComponent(strategy.id)}`} className="btn-ghost flex-1">檢視與執行 →</Link>}<button className="btn-danger" disabled={["default", "conservative"].includes(strategy.id) || !!deleting} onClick={() => setConfirmId(strategy.id)} aria-label={`刪除 ${strategy.name}`}>{["default", "conservative"].includes(strategy.id) ? "內建策略" : "刪除"}</button></div>}
        </div>
      </article>)}</div>
    </>}
  </div>;
}
function pct(value: number | boolean | undefined) { return typeof value === "number" ? `${Number((value * 100).toFixed(1))}%` : "—"; }
