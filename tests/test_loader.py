import pytest

from stock_strategies import loader


@pytest.fixture(autouse=True)
def strategy_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STRATEGY_DIR", tmp_path / "strategies")
    return loader.STRATEGY_DIR


@pytest.mark.parametrize("sid", ["../escape", "/tmp/escape", "a/b", "..", "", "a\\b"])
def test_rejects_unsafe_explicit_ids(sid):
    with pytest.raises(loader.StrategyError):
        loader.save_strategy({"id": sid, "name": "test"})


@pytest.mark.parametrize("operation", [loader.get_strategy, loader.delete_strategy])
def test_reads_and_deletes_reject_path_traversal(operation):
    with pytest.raises(loader.StrategyError):
        operation("../outside")


@pytest.mark.parametrize("params", [
    {"hold_days": "bad"}, {"hold_days": 1.5}, {"hold_days": True},
    {"eps_threshold": float("nan")}, {"roe_threshold": float("inf")},
    {"use_ma_alignment": "false"}, {"weight_technical": -0.5},
    {"weight_fundamental": 0, "weight_technical": 0, "weight_backtest": 0},
    {"stop_loss": 0}, {"market_filter_ma_period": 0}, {"hold_days": 121},
])
def test_invalid_parameters_are_rejected(params):
    with pytest.raises(loader.StrategyError):
        loader.validate_strategy({"name": "test", "params": params})


def test_updates_preserve_creation_timestamp():
    first = loader.save_strategy({"id": "test", "name": "first"})
    updated = loader.save_strategy({"id": "test", "name": "second"})
    assert updated["created_at"] == first["created_at"]
    assert loader.get_strategy("test")["name"] == "second"


def test_generated_ids_do_not_overwrite_same_named_strategy():
    first = loader.save_strategy({"name": "same name"})
    second = loader.save_strategy({"name": "same name"})
    assert first["id"] != second["id"]


def test_corrupt_files_are_reported_but_never_usable(strategy_dir):
    strategy_dir.mkdir()
    (strategy_dir / "broken.json").write_text("[]")
    listed = loader.list_strategies()
    assert listed[0]["error"]
    assert listed[0]["id"] == "broken"
    with pytest.raises(loader.StrategyError):
        loader.get_strategy("broken")


def test_valid_strategy_round_trip_and_defaults():
    saved = loader.save_strategy({"name": "短線策略", "params": {"hold_days": 5}})
    assert saved["params"]["hold_days"] == 5
    assert saved["params"]["use_ma_alignment"] is True
    assert loader.get_strategy(saved["id"]) == saved
    assert loader.delete_strategy(saved["id"])
    assert loader.get_strategy(saved["id"]) is None


def test_extremely_large_number_is_a_validation_error():
    with pytest.raises(loader.StrategyError):
        loader.validate_strategy({"name": "huge", "params": {"hold_days": 10**400}})


def test_listing_tolerates_concurrent_deletion(strategy_dir, monkeypatch):
    loader.save_strategy({"id": "vanishing", "name": "vanishing"})
    monkeypatch.setattr(loader, "get_strategy", lambda _: None)
    assert loader.list_strategies() == []


def test_failed_atomic_replace_keeps_original_strategy(strategy_dir, monkeypatch):
    original = loader.save_strategy({"id": "test", "name": "original"})
    def fail(*args):
        raise OSError("disk unavailable")
    monkeypatch.setattr(loader.os, "replace", fail)
    with pytest.raises(OSError):
        loader.save_strategy({"id": "test", "name": "new"})
    assert loader.get_strategy("test") == original
    assert list(strategy_dir.glob("*.tmp")) == []
