"use client";
import { useRun } from "@/hooks/useRun";
import { ErrorCard } from "./Feedback";

type Controller = ReturnType<typeof useRun>;
export default function RunControl({ run, disabled = false }: { run: Controller; disabled?: boolean }) {
  const { job, running, error } = run;
  const total = job?.total;
  return <div className="space-y-3">
    <div className="flex flex-wrap items-center gap-3">
      <button onClick={run.start} disabled={disabled || running} className="btn-primary">
        {running ? <><span className="spinner" />選股執行中</> : <>開始選股 <span aria-hidden="true">↗</span></>}
      </button>
      {running && job && <button onClick={run.cancel} disabled={job.status === "cancelling"} className="btn-ghost">
        {job.status === "cancelling" ? "正在取消…" : "取消執行"}
      </button>}
      {job && !running && <span className="text-xs text-muted">{job.status === "cancelled" ? "已取消 · 保留已完成結果" : job.status === "completed" ? "本次選股已完成" : "本次執行失敗"}</span>}
    </div>
    {running && <div className="rounded-lg border border-accent/20 bg-accent/5 p-4" role="status" aria-live="polite">
      <div className="mb-2 flex justify-between gap-3 text-sm">
        <span>{job?.status === "cancelling" ? "目前股票處理完畢後停止" : job?.current ? `正在分析 ${job.current}` : "正在準備觀察池與市場資料…"}</span>
        <span className="shrink-0 font-mono text-muted">{job?.completed ?? 0} / {total ?? "—"}</span>
      </div>
      <progress className="h-1.5 w-full" max={total || 1} value={total ? job?.completed ?? 0 : undefined} aria-label="選股進度" />
      <p className="mt-2 text-xs text-muted">依觀察池大小需要數分鐘。重新整理後可繼續查看進度。</p>
    </div>}
    {error && <ErrorCard message={error} />}
  </div>;
}
