import time
from decimal import Decimal as D

from adapters.mock_market import MockMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import demo_signal
from core.decision_engine import run_decision_cycle
from storage.database import Database


def test_mock_end_to_end_cycle(tmp_path):
    db = Database(tmp_path / "e2e.db")
    market = MockMarketAdapter().fetch_snapshot("AVAX-USDT")
    signal = demo_signal(market)
    assert signal.origin == "DEMO"
    now = int(time.time())
    decision, ref = run_decision_cycle(
        db, rules=ConstitutionRules(), signal=signal, market=market, now=now
    )
    assert decision.status in {"APPROVED_PAPER", "SHADOW_PASS", "TECHNICAL_BLOCK"}
    assert ref is not None
