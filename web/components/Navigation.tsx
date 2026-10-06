"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
const items = [{ href: "/", label: "今日訊號" }, { href: "/strategies", label: "策略庫" }, { href: "/strategies/new", label: "建立策略" }, { href: "/strategies/ai", label: "AI 策略助手" }];
export default function Navigation() {
  const pathname = usePathname();
  return <header className="sticky top-0 z-20 border-b border-line bg-bg/95 backdrop-blur-xl">
    <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
      <Link href="/" className="flex w-fit items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl border border-accent/30 bg-accent/10 text-xl text-accent" aria-hidden="true">↗</span><span className="text-sm font-semibold tracking-wide">Stock Strategies<span className="ml-2 text-xs font-normal text-muted">台股研究工作台</span></span></Link>
      <nav aria-label="主要導覽" className="flex gap-1 overflow-x-auto">
        {items.map(item => {
          const selected = pathname === item.href || (item.href === "/strategies" && /^\/strategies\/(?!new$|ai$).+/.test(pathname));
          return <Link key={item.href} href={item.href} aria-current={selected ? "page" : undefined} className={`shrink-0 rounded-lg px-3 py-2 text-sm transition ${selected ? "bg-accent/10 text-blue-300" : "text-muted hover:bg-panel hover:text-text"}`}>{item.label}</Link>;
        })}
      </nav>
    </div>
  </header>;
}
