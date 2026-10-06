"use client";
import { useEffect, useRef, useState } from "react";
import { api, errorMessage, Strategy, StrategyParams } from "@/lib/api";
import { PARAM_GROUPS } from "@/lib/strategy-fields";
import { ErrorCard, Skeleton } from "./Feedback";

type Props = { initial?: Partial<Strategy>; onSaved?: (strategy: Strategy) => void; saveLabel?: string };
const weightKeys = ["weight_fundamental", "weight_technical", "weight_backtest"];

export default function StrategyForm({ initial, onSaved, saveLabel = "儲存到策略庫" }: Props) {
  const [name, setName] = useState(initial?.name || "");
  const [description, setDescription] = useState(initial?.description || "");
  const [params, setParams] = useState<StrategyParams>({});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [saving, setSaving] = useState(false);
  const pending = useRef(false);
  const initialRef = useRef(initial);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setLoadError(null);
    api.getDefaults(controller.signal).then(data => {
      const merged = { ...data.params, ...initialRef.current?.params };
      const sum = weightKeys.reduce((total, key) => total + Number(merged[key]), 0);
      if (sum > 0) weightKeys.forEach(key => { merged[key] = Number(merged[key]) / sum; });
      setParams(merged);
    }).catch(err => { if (!controller.signal.aborted) setLoadError(errorMessage(err)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [reload]);

  const weightSum = weightKeys.reduce((sum, key) => sum + Number(params[key] || 0), 0);
  const weightOk = Math.abs(weightSum - 1) < 0.0001;
  function setParam(key: string, value: number | boolean) { setParams(previous => ({ ...previous, [key]: value })); }
  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current || !weightOk) return;
    pending.current = true; setSaving(true); setError(null);
    try {
      const saved = await api.saveStrategy({ id: initial?.id, name: name.trim(), description, source: initial?.source || "manual", params });
      onSaved?.(saved);
    } catch (err) { setError(errorMessage(err)); }
    finally { setSaving(false); pending.current = false; }
  }
  if (loading) return <Skeleton />;
  if (loadError) return <ErrorCard message={loadError} retry={() => setReload(value => value + 1)} />;
  return <form onSubmit={save} className="space-y-5">
    <fieldset disabled={saving} className="space-y-5">
      <div className="card grid gap-4 sm:grid-cols-2">
        <div><label htmlFor="strategy-name" className="label">策略名稱 *</label><input id="strategy-name" required maxLength={120} className="input" value={name} onChange={e => setName(e.target.value)} placeholder="例：動能短打 V1" /></div>
        <div><label htmlFor="strategy-description" className="label">說明</label><textarea id="strategy-description" maxLength={4000} className="input min-h-[80px]" value={description} onChange={e => setDescription(e.target.value)} placeholder="描述目標與適用情境" /></div>
      </div>
      {PARAM_GROUPS.map((group, index) => <section className="card" key={group.title}>
        <div className="mb-5 flex items-start gap-3"><span className="rounded-md bg-panel2 px-2 py-1 font-mono text-xs text-muted">0{index + 1}</span><div><h2 className="font-medium">{group.title}</h2><p className="mt-1 text-xs text-muted">{group.description}</p></div></div>
        {group.title === "評分加權" && <div className="mb-5 rounded-lg bg-panel2 p-3"><div className="mb-2 flex items-center justify-between text-xs"><span className="text-muted">基本面 / 技術面 / 回測</span><span className={weightOk ? "text-buy" : "text-watch"}>{(weightSum * 100).toFixed(1)}% {weightOk ? "· 配置完成" : "· 請調整為 100%"}</span></div><div className="flex h-2 overflow-hidden rounded-full bg-line">{weightKeys.map((key, index) => <div key={key} className={["bg-blue-400", "bg-purple-400", "bg-amber-400"][index]} style={{ width: `${Math.max(0, Number(params[key]) || 0) / (weightSum || 1) * 100}%` }} />)}</div></div>}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{group.fields.map(field => {
          if (field.kind === "bool") return <label key={field.key} className="flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-line bg-panel2 px-3 py-3 text-sm"><span>{field.label}</span><input className="h-4 w-4 shrink-0 accent-blue-500" type="checkbox" checked={Boolean(params[field.key])} onChange={e => setParam(field.key, e.target.checked)} /></label>;
          const value = Number(params[field.key]) * (field.percent ? 100 : 1);
          return <div key={field.key}><label htmlFor={field.key} className="label">{field.label}</label><input id={field.key} required type="number" inputMode={field.integer ? "numeric" : "decimal"} step={field.integer ? 1 : "any"} min={field.min} max={field.max} className="input font-mono" value={Number.isFinite(value) ? Number(value.toFixed(6)) : ""} onChange={e => setParam(field.key, e.target.valueAsNumber / (field.percent ? 100 : 1))} />{field.min != null && <p className="mt-1.5 text-xs text-muted">範圍 {field.min}–{field.max}</p>}</div>;
        })}</div>
      </section>)}
    </fieldset>
    {error && <ErrorCard message={error} />}
    <div className="sticky bottom-0 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-panel/95 p-4 backdrop-blur-xl"><p className={`text-xs ${weightOk ? "text-muted" : "text-watch"}`}>{weightOk ? "儲存後即可用此策略執行選股。" : "三項評分權重需合計 100% 才能儲存。"}</p><button type="submit" className="btn-primary" disabled={saving || !name.trim() || !weightOk}>{saving ? "儲存中…" : saveLabel}</button></div>
  </form>;
}
