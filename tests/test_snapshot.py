import time

from adapters.mock_market import MockMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import demo_signal
from core.decision_engine import run_decision_cycle
from dashboard.snapshot import build_kokpit_snapshot, resolve_db_path
from storage.database import Database


def test_resolve_db_path_default_golge():
    resolved = resolve_db_path("data/golge.db")
    assert resolved.name == "golge.db"
    assert resolved.parent.name == "data"


def test_resolve_db_path_rejects_outside_root():
    import pytest

    with pytest.raises(ValueError):
        resolve_db_path("/etc/hosts.db")


def test_build_kokpit_snapshot_keys(tmp_path):
    db_path = tmp_path / "snap.db"
    db = Database(db_path)
    market = MockMarketAdapter().fetch_snapshot("AVAX-USDT")
    run_decision_cycle(
        db,
        rules=ConstitutionRules(),
        signal=demo_signal(market),
        market=market,
        now=int(time.time()),
    )
    snap = build_kokpit_snapshot(db_path)
    assert "worker_active" in snap
    assert "report" in snap
    assert snap["decisions_summary"]
    assert "constitution" in snap
    assert snap["recent_decisions"]
