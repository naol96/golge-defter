import time
from decimal import Decimal as D

from adapters.mock_market import MockMarketAdapter
from contracts.models import AnalystSignal, ConstitutionRules
from core.constitution import evaluate


def test_mock_snapshot_is_fresh():
    snap = MockMarketAdapter().fetch_snapshot("AVAX-USDT")
    assert snap.source == "MOCK"
    now = int(time.time())
    decision = evaluate(
        constitution=ConstitutionRules(),
        signal=AnalystSignal("AVAX-USDT", "BUY", "t"),
        market=snap,
        available_usdt=D("80"),
        min_order_usdt=D("10"),
        daily_realized_loss_usdt=D("0"),
        now=now,
    )
    assert decision.status == "APPROVED_PAPER"
