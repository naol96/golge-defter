import time
from decimal import Decimal

import pytest

from adapters.mock_market import MockMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import demo_signal
from core.decision_engine import run_decision_cycle
from dashboard.analytics import build_analytics
from dashboard.serve_kokpit import KokpitHandler
from storage.database import Database


def _seed(db_path, cycles=3):
    db = Database(db_path)
    now = int(time.time())
    for i, symbol in enumerate(["AVAX-USDT", "BTC-USDT", "SOL-USDT"][:cycles]):
        market = MockMarketAdapter().fetch_snapshot(symbol)
        run_decision_cycle(
            db, rules=ConstitutionRules(), signal=demo_signal(market), market=market, now=now + i
        )
    return db


def test_build_analytics_shape(tmp_path):
    db_path = tmp_path / "a.db"
    _seed(db_path)
    data = build_analytics(db_path, hours=2, bucket_minutes=15, limit=50)
    assert data["window"]["bucket_minutes"] == 15
    assert len(data["timeline"]) == 8
    assert sum(sum(b["counts"].values()) for b in data["timeline"]) == 3
    assert {r["symbol"] for r in data["symbols"]} == {"AVAX-USDT", "BTC-USDT", "SOL-USDT"}
    assert sum(r["total"] for r in data["rules"]) == 3
    assert len(data["decisions"]) == 3
    assert data["decisions"][0]["id"] > data["decisions"][-1]["id"]


def test_build_analytics_outcomes_aggregate_decimal(tmp_path):
    db_path = tmp_path / "o.db"
    _seed(db_path)
    import sqlite3

    conn = sqlite3.connect(db_path)
    sid = conn.execute("SELECT id FROM shadow_trades LIMIT 1").fetchone()[0]
    conn.execute(
        "UPDATE shadow_evaluations SET status='COMPLETE', pnl_usdt='0.10', evaluated_at=1 "
        "WHERE shadow_id=? AND horizon_minutes=15",
        (sid,),
    )
    conn.commit()
    conn.close()
    data = build_analytics(db_path)
    row = next(o for o in data["outcomes"] if o["horizon_minutes"] == 15)
    assert row["count"] == 1 and row["positive"] == 1
    assert Decimal(row["sum_pnl_usdt"]) == Decimal("0.10")


def test_build_analytics_clamps_limits(tmp_path):
    db_path = tmp_path / "c.db"
    _seed(db_path, cycles=1)
    data = build_analytics(db_path, hours=10_000, bucket_minutes=0, limit=0)
    assert data["window"]["hours"] == 24 * 7
    assert data["window"]["bucket_minutes"] == 1
    assert len(data["decisions"]) == 1


def test_build_analytics_missing_db(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_analytics(tmp_path / "missing.db")


def test_http_analytics_rejects_bad_params(monkeypatch):
    import dashboard.serve_kokpit as module
    responses = []
    monkeypatch.setattr(module, "_json_response", lambda handler, status, payload: responses.append((status, payload)))
    handler = object.__new__(KokpitHandler)
    for query in ("db=/etc/x.db", "db=../x.db", "hours=abc"):
        handler.path = f"/api/analytics?{query}"
        handler.do_GET()
        status, payload = responses[-1]
        assert status == 400 and "error" in payload


def test_analytics_keeps_legacy_technical_separate_and_preserves_raw_data(tmp_path):
    from contracts.models import ShadowCategory
    db = Database(tmp_path / "legacy.db")
    now = int(time.time())
    sid = db.insert_shadow(symbol="AVAX-USDT", category=ShadowCategory.CONSTITUTIONAL_RISK_BLOCK,
        entry_ask=Decimal("100"), notional_usdt=Decimal("7.5"), reason="MOCK audit",
        constitution_rule="OBSERVATION", created_at=now - 1000, source="MOCK")
    db.insert_decision(symbol="AVAX-USDT", signal_action="BUY", signal_reason="MOCK audit",
        signal_origin="DEMO", status="SHADOW_RISK", rule="OBSERVATION", explanation="legacy",
        notional_usdt=Decimal("7.5"), market_source="MOCK", ref_id=sid, created_at=now - 1000)
    with db.session() as conn:
        conn.execute("UPDATE shadow_evaluations SET status='COMPLETE',pnl_usdt='-0.0000001',evaluated_at=? WHERE shadow_id=? AND horizon_minutes=15", (now, sid))
    data = build_analytics(db.path)
    assert data["decisions"][0]["status"] == "TECHNICAL_BLOCK"
    assert data["decisions"][0]["raw_status"] == "SHADOW_RISK"
    assert data["outcomes"][0]["category"] == "TECHNICAL_UNEXECUTABLE"
    assert Decimal(data["outcomes"][0]["sum_pnl_usdt"]) == Decimal("-0.0000001")
    complete = next(row for row in data["shadow"] if row["status"] == "COMPLETE")
    assert complete["signal_origin"] == "DEMO"
    assert "stop doğrulaması belgelenmedi" in complete["note"]
    with db.session() as conn:
        assert conn.execute("SELECT status FROM decisions").fetchone()[0] == "SHADOW_RISK"
        assert conn.execute("SELECT note FROM shadow_evaluations WHERE horizon_minutes=15").fetchone()[0] == ""


def test_analytics_read_does_not_write_database(tmp_path):
    import hashlib
    path = tmp_path / "readonly.db"
    _seed(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    build_analytics(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
