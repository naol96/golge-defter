import time

from adapters.mock_market import MockMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import demo_signal
from core.decision_engine import run_decision_cycle
from report import build_report
from storage.database import Database


def test_decision_row_persisted(tmp_path):
    db = Database(tmp_path / "d.db")
    market = MockMarketAdapter().fetch_snapshot("AVAX-USDT")
    signal = demo_signal(market)
    now = int(time.time())
    run_decision_cycle(db, rules=ConstitutionRules(), signal=signal, market=market, now=now)
    with db.session() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM decisions").fetchone()
    assert int(row["c"]) == 1


def test_build_report_counts(tmp_path):
    db_path = tmp_path / "r.db"
    db = Database(db_path)
    market = MockMarketAdapter().fetch_snapshot("AVAX-USDT")
    run_decision_cycle(
        db,
        rules=ConstitutionRules(),
        signal=demo_signal(market),
        market=market,
        now=int(time.time()),
    )
    report = build_report(db_path)
    assert report["decisions_by_status"]
    assert "notes" in report
