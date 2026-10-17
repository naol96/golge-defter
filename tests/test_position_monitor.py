from decimal import Decimal as D

from contracts.models import ConstitutionRules, MarketSnapshot
from core.paper_broker import open_paper_position
from core.position_monitor import monitor_open_positions
from storage.database import Database


def test_stop_loss_closes_position_once(tmp_path):
    db = Database(tmp_path / "p.db")
    db.set_paper_balance(D("100"))
    market = MarketSnapshot("AVAX-USDT", D("25"), D("25.01"), 1000, source="MOCK")
    pos = open_paper_position(
        db, market=market, notional_usdt=D("20"), rules=ConstitutionRules(), now=1000
    )
    crash = MarketSnapshot("AVAX-USDT", D("24"), D("24.01"), 1001, source="MOCK")
    closed = monitor_open_positions(db, crash, 1001, "1970-01-01")
    assert closed == [pos.id]
    assert monitor_open_positions(db, crash, 1002, "1970-01-01") == []
