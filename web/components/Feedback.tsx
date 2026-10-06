import type { ReactNode } from "react";

export function ErrorCard({ message, retry }: { message: string; retry?: () => void }) {
  return <div role="alert" className="rounded-xl border border-err/30 bg-err/5 p-4 text-sm">
    <div className="font-medium text-red-300">暫時無法完成</div>
    <p className="mt-1 break-words text-muted">{message}</p>
    {retry && <button className="btn-ghost mt-3" onClick={retry}>重新嘗試</button>}
  </div>;
}
export function EmptyState({ title, children }: { title: string; children: ReactNode }) {
  return <div className="rounded-xl border border-dashed border-line px-6 py-12 text-center">
    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-accent/25 bg-accent/10 text-accent" aria-hidden="true">↗</div>
    <h2 className="font-medium">{title}</h2>
    <div className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">{children}</div>
  </div>;
}
export function Skeleton({ rows = 3 }: { rows?: number }) {
  return <div role="status" aria-label="載入中" className="space-y-3">
    {Array.from({ length: rows }, (_, i) => <div key={i} className="h-24 animate-pulse rounded-xl border border-line bg-panel" />)}
    <span className="sr-only">載入中</span>
  </div>;
}
