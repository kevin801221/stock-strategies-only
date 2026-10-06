"""Bounded, process-local screening jobs; external data requests remain sequential."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import threading
import time
import uuid

from stock_strategies.evaluate import evaluate
from stock_strategies.market import apply_market_filter, get_market_state
from stock_strategies.sheet import read_watchlist


def screen(strategy, limit=None, *, progress=None, cancel=None, delay=0.4):
    cancel = cancel or threading.Event()
    report = progress or (lambda **state: None)
    if cancel.is_set():
        rows = []
    else:
        rows = read_watchlist()
    if limit is not None:
        rows = rows[:limit]
    total = len(rows)
    report(completed=0, total=total, current=None)
    params = strategy["params"]
    market_enabled = params.get("market_filter_enabled", True)
    market = {"bullish": True, "close": None, "ma20": None, "note": "已關閉大盤濾鏡"}
    if market_enabled and not cancel.is_set():
        market = get_market_state(int(params.get("market_filter_ma_period", 20)))

    results = []
    for index, row in enumerate(rows):
        if cancel.is_set():
            break
        sid, name = str(row["stock_id"]), row.get("name", "")
        report(completed=index, total=total, current=sid)
        try:
            result = evaluate(sid, name, strategy=strategy)
            if result is None:
                raise ValueError("未回傳評估結果")
        except Exception as exc:
            result = {"stock_id": sid, "name": name, "action": "ERROR", "risk_notes": [str(exc)[:160]]}
        results.append(result)
        report(completed=len(results), total=total, current=sid)
        if index + 1 < total and cancel.wait(delay):
            break

    downgraded = apply_market_filter(results, market) if market_enabled else 0
    order = {"BUY": 0, "WATCH": 1, "SKIP": 2, "ERROR": 3}
    results.sort(key=lambda row: (order.get(row.get("action"), 4), -(row.get("signal_score") or 0)))
    return {
        "strategy": {"id": strategy["id"], "name": strategy["name"]},
        "market": market,
        "downgraded": downgraded,
        "summary": {"total": len(results), **{
            action.lower(): sum(row.get("action") == action for row in results)
            for action in order
        }},
        "results": results,
    }


class RunBusy(RuntimeError):
    pass


class RunManager:
    """One active job, bounded history, snapshots under a lock, cooperative cancellation."""

    def __init__(self, runner=screen, *, retention_seconds=3600, max_history=20):
        self._runner = runner
        self._retention = retention_seconds
        self._max_history = max_history
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="screening")
        self._jobs = {}
        self._events = {}
        self._done = {}

    def _prune(self, reserve=False):
        finished = [key for key, job in self._jobs.items() if job.get("finished") is not None]
        for key in finished:
            if time.monotonic() - self._jobs[key]["finished"] >= self._retention or (reserve and len(self._jobs) >= self._max_history):
                del self._jobs[key]
                self._events.pop(key, None)
                self._done.pop(key, None)

    def _snapshot(self, job):
        return deepcopy({key: value for key, value in job.items() if key != "finished"})

    def start(self, strategy, limit=None):
        with self._lock:
            self._prune(reserve=True)
            if any(job["status"] in ("queued", "running", "cancelling") for job in self._jobs.values()):
                raise RunBusy("已有選股任務執行中，請稍後再試")
            key = uuid.uuid4().hex
            job = {
                "id": key, "status": "queued", "completed": 0, "total": None, "current": None,
                "strategy": {"id": strategy["id"], "name": strategy["name"]},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "result": None, "error": None,
            }
            self._jobs[key] = job
            self._events[key] = threading.Event()
            self._done[key] = threading.Event()
            self._executor.submit(self._execute, key, deepcopy(strategy), limit)
            return self._snapshot(job)

    def _execute(self, key, strategy, limit):
        with self._lock:
            job, cancel = self._jobs[key], self._events[key]
            job["status"] = "cancelling" if cancel.is_set() else "running"

        def progress(**state):
            with self._lock:
                job.update(state)

        try:
            result = self._runner(strategy, limit, progress=progress, cancel=cancel)
            with self._lock:
                job.update(result=result, status="cancelled" if cancel.is_set() else "completed")
        except Exception as exc:
            with self._lock:
                job.update(status="cancelled" if cancel.is_set() else "failed", error=str(exc)[:300])
        finally:
            with self._lock:
                job["current"] = None
                job["finished"] = time.monotonic()
                self._done[key].set()

    def run_sync(self, strategy, limit=None):
        with self._lock:
            started = self.start(strategy, limit)
            job = self._jobs[started["id"]]
            done = self._done[started["id"]]
        done.wait()
        with self._lock:
            if job["status"] == "failed":
                raise RuntimeError(job["error"])
            return deepcopy(job["result"])

    def get(self, key):
        with self._lock:
            self._prune()
            job = self._jobs.get(key)
            return self._snapshot(job) if job else None

    def cancel(self, key):
        with self._lock:
            job = self._jobs.get(key)
            if not job:
                return None
            if job["status"] in ("queued", "running", "cancelling"):
                self._events[key].set()
                job["status"] = "cancelling"
            return self._snapshot(job)

    def shutdown(self):
        self._executor.shutdown(wait=True)
