"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, errorMessage, Strategy } from "@/lib/api";
import { PARAM_GROUPS } from "@/lib/strategy-fields";
import { SourceBadge } from "@/components/ActionBadge";
import { ErrorCard, Skeleton } from "@/components/Feedback";
import RunControl from "@/components/RunControl";
import SignalResults from "@/components/SignalResults";
import StrategyForm from "@/components/StrategyForm";
import { useRun } from "@/hooks/useRun";

export default function StrategyDetail() {
  const { id } = useParams<{ id: string }>();
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const [reload, setReload] = useState(0);
  const run = useRun(id);
  useEffect(() => {
    const controller = new AbortController();
    setStrategy(null); setError(null); setEditing(false); setSaved(false);
    api.getStrategy(id, controller.signal).then(setStrategy).catch(err => { if (!controller.signal.aborted) setError(errorMessage(err)); });
    return () => controller.abort();
  }, [id, reload]);
  return <div className="space-y-6">
    <Link href="/strategies" className="text-sm text-muted hover:text-text">← 回策略庫</Link>
    {error && <ErrorCard message={error} retry={() => setReload(value => value + 1)} />}
    {!strategy && !error && <Skeleton />}
    {strategy && <>
      <section className="card"><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="mb-3"><SourceBadge source={strategy.source} /></div><h1 className="text-2xl font-semibold">{strategy.name}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-muted">{strategy.description}</p></div><button className="btn-ghost" disabled={run.running} onClick={() => { setEditing(value => !value); setSaved(false); }}>{editing ? "返回策略詳情" : "編輯參數"}</button></div>
        {saved && <p role="status" className="mt-3 text-sm text-buy">策略已更新，下次選股會使用新的參數。</p>}
        {!editing && <div className="mt-5 border-t border-line pt-5"><RunControl run={run} /></div>}
      </section>
      {editing ? <StrategyForm key={strategy.updated_at} initial={strategy} saveLabel="儲存變更" onSaved={value => { setStrategy(value); setEditing(false); setSaved(true); }} /> : <>
        {run.result && <SignalResults run={run.result} />}
        <section className="grid gap-4 md:grid-cols-2">{PARAM_GROUPS.map(group => <div className="card" key={group.title}><h2 className="mb-4 text-sm font-medium">{group.title}</h2><dl className="space-y-3">{group.fields.map(field => { const value = strategy.params[field.key]; return <div key={field.key} className="flex justify-between gap-4 text-sm"><dt className="text-muted">{field.label}</dt><dd className="shrink-0 font-mono">{typeof value === "boolean" ? value ? "啟用" : "關閉" : typeof value === "number" ? field.percent ? `${Number((value * 100).toFixed(2))}%` : value : "—"}</dd></div>; })}</dl></div>)}</section>
      </>}
    </>}
  </div>;
}
