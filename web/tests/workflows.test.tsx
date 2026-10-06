import { act, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { api, RunJob, RunResult } from "@/lib/api";
import SignalResults from "@/components/SignalResults";
import StrategyForm from "@/components/StrategyForm";
import Dashboard from "@/app/page";
import { useRun } from "@/hooks/useRun";
import { PARAM_GROUPS } from "@/lib/strategy-fields";

vi.mock("next/link", () => ({ default: ({ href, children, ...props }: React.PropsWithChildren<{ href: string }>) => <a href={href} {...props}>{children}</a> }));
const result: RunResult = {
  strategy: { id: "conservative", name: "保守策略" }, market: { bullish: false, note: "跌破均線" }, downgraded: 0,
  summary: { total: 3, buy: 1, watch: 0, skip: 1, error: 1 },
  results: [
    { stock_id: "2330", name: "台積電", action: "BUY", signal_score: 88, components: { backtest_winrate: 0, backtest_samples: 10 } },
    { stock_id: "2317", name: "鴻海", action: "SKIP", risk_notes: ["價格資料不足"] },
    { stock_id: "9999", name: "錯誤股票", action: "ERROR", risk_notes: ["資料來源逾時"] },
  ],
};
const job: RunJob = { id: "job1", status: "running", strategy: result.strategy, completed: 1, total: 3, current: "2330", created_at: "2026-09-25", result: null, error: null };
const defaults = Object.fromEntries(PARAM_GROUPS.flatMap(group => group.fields).map(field => [field.key, field.kind === "bool" ? true : field.key.startsWith("weight") ? field.key === "weight_backtest" ? 0.4 : 0.3 : field.percent ? 0.1 : Math.max(field.min || 0, 5)]));

beforeEach(() => {
  vi.spyOn(api, "getDefaults").mockResolvedValue({ params: defaults });
});

test("results retain error and missing-data rows, and preserve zero winrate", () => {
  render(<SignalResults run={result} />);
  expect(screen.getByText("錯誤股票")).toBeTruthy();
  expect(screen.getByText("價格資料不足")).toBeTruthy();
  expect(screen.getAllByText("0%").length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole("button", { name: /資料異常/ }));
  expect(screen.queryByText("台積電")).toBeNull();
  expect(screen.getByText("錯誤股票")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /全部訊號/ }));
  fireEvent.change(screen.getByRole("searchbox", { name: "搜尋股票" }), { target: { value: "2330" } });
  expect(screen.getByText("台積電")).toBeTruthy();
  expect(screen.queryByText("錯誤股票")).toBeNull();
});

test("form reports defaults failure and recovers with retry", async () => {
  vi.mocked(api.getDefaults).mockRejectedValueOnce(new Error("offline"));
  render(<StrategyForm />);
  expect(await screen.findByRole("alert")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "重新嘗試" }));
  expect(await screen.findByLabelText("策略名稱 *")).toBeTruthy();
});

test("form blocks invalid weights and empty numeric fields before saving", async () => {
  const save = vi.spyOn(api, "saveStrategy").mockResolvedValue({ id: "new", name: "new", params: defaults });
  render(<StrategyForm />);
  fireEvent.change(await screen.findByLabelText("策略名稱 *"), { target: { value: "new" } });
  fireEvent.change(screen.getByLabelText("基本面權重 (%)"), { target: { value: "90" } });
  expect((screen.getByRole("button", { name: "儲存到策略庫" }) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.change(screen.getByLabelText("基本面權重 (%)"), { target: { value: "30" } });
  const hold = screen.getByLabelText("持有天數") as HTMLInputElement;
  fireEvent.change(hold, { target: { value: "" } });
  expect(hold.validity.valueMissing).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "儲存到策略庫" }));
  expect(save).not.toHaveBeenCalled();
  fireEvent.change(hold, { target: { value: "10" } });
  fireEvent.click(screen.getByRole("button", { name: "儲存到策略庫" }));
  await waitFor(() => expect(save).toHaveBeenCalledOnce());
  expect(save.mock.calls[0][0].params?.hold_days).toBe(10);
});

test("run resumes from saved job and cancels cooperatively", async () => {
  sessionStorage.setItem("screening:conservative", "job1");
  const get = vi.spyOn(api, "getRun").mockResolvedValue(job);
  const cancel = vi.spyOn(api, "cancelRun").mockResolvedValue({ ...job, status: "cancelling" });
  const { result: hook } = renderHook(() => useRun("conservative"));
  await waitFor(() => expect(hook.current.job?.id).toBe("job1"));
  expect(hook.current.running).toBe(true);
  await act(() => hook.current.cancel());
  expect(cancel).toHaveBeenCalledWith("job1");
  expect(get).toHaveBeenCalled();
});

test("run start remembers selected strategy and suppresses duplicate clicks", async () => {
  const start = vi.spyOn(api, "startRun").mockResolvedValue(job);
  vi.spyOn(api, "getRun").mockResolvedValue(job);
  const { result: hook } = renderHook(() => useRun("conservative"));
  await act(async () => { await Promise.all([hook.current.start(), hook.current.start()]); });
  expect(start).toHaveBeenCalledOnce();
  expect(sessionStorage.getItem("screening:selected")).toBe("conservative");
});

test("dashboard restores the selected custom strategy on refresh", async () => {
  sessionStorage.setItem("screening:selected", "conservative");
  sessionStorage.setItem("screening:conservative", "job1");
  vi.spyOn(api, "listStrategies").mockResolvedValue({ strategies: [
    { id: "default", name: "預設", params: defaults }, { id: "conservative", name: "保守", params: defaults },
  ] });
  vi.spyOn(api, "getMarket").mockResolvedValue(result.market);
  vi.spyOn(api, "getWatchlist").mockResolvedValue({ items: [] });
  const get = vi.spyOn(api, "getRun").mockResolvedValue(job);
  render(<Dashboard />);
  const select = await screen.findByLabelText("本次使用策略") as HTMLSelectElement;
  await waitFor(() => expect(select.value).toBe("conservative"));
  await waitFor(() => expect(get).toHaveBeenCalledWith("job1", expect.any(AbortSignal)));
  expect(await screen.findByRole("button", { name: "取消執行" })).toBeTruthy();
});

test("changing strategy ignores a late response from the previous run", async () => {
  let resolve!: (job: RunJob) => void;
  vi.spyOn(api, "startRun").mockImplementation(() => new Promise(done => { resolve = done; }));
  vi.spyOn(api, "getRun").mockResolvedValue(job);
  const { result: hook, rerender } = renderHook(({ id }) => useRun(id), { initialProps: { id: "conservative" } });
  let starting!: Promise<void>;
  act(() => { starting = hook.current.start(); });
  rerender({ id: "default" });
  await act(async () => { resolve(job); await starting; });
  expect(hook.current.job).toBeNull();
  expect(hook.current.running).toBe(false);
  expect(sessionStorage.getItem("screening:conservative")).toBe("job1");
});

test("an expired job unlocks the run controls and explains recovery", async () => {
  const { ApiError } = await import("@/lib/api");
  sessionStorage.setItem("screening:conservative", "expired");
  vi.spyOn(api, "getRun").mockRejectedValue(new ApiError("紀錄已過期", 404));
  const { result: hook } = renderHook(() => useRun("conservative"));
  await waitFor(() => expect(hook.current.error).toBe("紀錄已過期"));
  expect(hook.current.running).toBe(false);
  expect(sessionStorage.getItem("screening:conservative")).toBeNull();
});
