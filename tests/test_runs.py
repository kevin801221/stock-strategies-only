import threading

import pytest

from api.services import runs


@pytest.fixture
def services(monkeypatch):
    monkeypatch.setattr(runs, "read_watchlist", lambda: [{"stock_id": "1", "name": "one"}, {"stock_id": "2"}])
    monkeypatch.setattr(runs, "get_market_state", lambda _: {"bullish": False, "note": "bear"})
    monkeypatch.setattr(runs, "evaluate", lambda sid, name, strategy: {
        "stock_id": sid, "name": name, "action": "BUY", "signal_score": 70, "risk_notes": [],
    })
    return {"id": "test", "name": "test", "params": {}}


def test_screening_reports_progress_and_applies_market_filter(services):
    updates = []
    result = runs.screen(services, progress=lambda **state: updates.append(state), delay=0)
    assert result["summary"] == {"total": 2, "buy": 0, "watch": 2, "skip": 0, "error": 0}
    assert result["downgraded"] == 2
    assert updates[-1]["completed"] == 2
    assert updates[-1]["total"] == 2


def test_one_failed_stock_does_not_discard_the_run(services, monkeypatch):
    def evaluate(sid, *_args, **_kwargs):
        if sid == "1":
            raise RuntimeError("bad stock")
        return {"stock_id": sid, "action": "SKIP"}
    monkeypatch.setattr(runs, "evaluate", evaluate)
    result = runs.screen(services, delay=0)
    assert result["summary"]["error"] == 1
    assert result["summary"]["skip"] == 1


def test_cancellation_stops_before_next_stock(services, monkeypatch):
    cancel = threading.Event()
    seen = []
    def evaluate(sid, *_args, **_kwargs):
        seen.append(sid)
        cancel.set()
        return {"stock_id": sid, "action": "SKIP"}
    monkeypatch.setattr(runs, "evaluate", evaluate)
    result = runs.screen(services, cancel=cancel, delay=0)
    assert seen == ["1"]
    assert result["summary"]["total"] == 1


def test_jobs_reject_duplicate_work_and_expose_terminal_result(services):
    entered, release = threading.Event(), threading.Event(),
    def runner(strategy, limit, *, progress, cancel):
        entered.set()
        assert release.wait(5)
        progress(completed=1, total=1, current="1")
        return {"summary": {"total": 1}}
    store = runs.RunManager(runner=runner)
    try:
        first = store.start(services)
        assert entered.wait(5)
        with pytest.raises(runs.RunBusy):
            store.start(services)
        assert store.get(first["id"])["status"] == "running"
        release.set()
    finally:
        release.set()
        store.shutdown()
    job = store.get(first["id"])
    assert job["status"] == "completed"
    assert job["result"]["summary"]["total"] == 1


def test_job_cancel_failure_and_missing_job(services):
    entered, release = threading.Event(), threading.Event()
    def runner(strategy, limit, *, progress, cancel):
        entered.set()
        assert release.wait(5)
        return {"summary": {"total": 0}}
    store = runs.RunManager(runner=runner)
    try:
        job = store.start(services)
        assert entered.wait(5)
        assert store.cancel(job["id"])["status"] == "cancelling"
        assert store.get("missing") is None
    finally:
        release.set()
        store.shutdown()
    assert store.get(job["id"])["status"] == "cancelled"


def test_job_failure_is_visible_and_releases_capacity(services):
    def runner(*args, **kwargs):
        raise RuntimeError("watchlist unavailable")
    store = runs.RunManager(runner=runner)
    job = store.start(services)
    store.shutdown()
    assert store.get(job["id"])["status"] == "failed"
    assert "watchlist unavailable" in store.get(job["id"])["error"]


def test_full_history_keeps_newest_completed_job_until_next_start(services):
    store = runs.RunManager(runner=lambda *args, **kwargs: {"ok": True}, max_history=1)
    job = store.start(services)
    store.shutdown()
    assert store.get(job["id"])["status"] == "completed"


def test_synchronous_run_uses_same_capacity_guard(services):
    entered, release = threading.Event(), threading.Event()
    def runner(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return {"ok": True}
    store = runs.RunManager(runner=runner)
    try:
        store.start(services)
        assert entered.wait(5)
        with pytest.raises(runs.RunBusy):
            store.run_sync(services)
    finally:
        release.set()
        store.shutdown()


def test_synchronous_run_returns_same_result(services):
    store = runs.RunManager(runner=lambda *args, **kwargs: {"ok": True})
    try:
        assert store.run_sync(services) == {"ok": True}
    finally:
        store.shutdown()
