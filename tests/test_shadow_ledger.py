from decimal import Decimal as D

from contracts.models import MarketSnapshot, ShadowCategory
from core.shadow_evaluator import evaluate_due_shadows, shadow_pnl
from storage.database import Database


def test_shadow_pnl_uses_ask_entry_bid_exit():
    pnl = shadow_pnl(D("100"), D("99"), D("25"))
    assert pnl < 0


def test_idempotent_shadow_evaluation(tmp_path):
    db = Database(tmp_path / "t.db")
    created = 1_800_000_000
    sid = db.insert_shadow(
        symbol="AVAX-USDT",
        category=ShadowCategory.PASS_OBSERVATION,
        entry_ask=D("25"),
        notional_usdt=D("12.5"),
        reason="test",
        constitution_rule="ANALYST",
        created_at=created,
        source="MOCK",
    )
    market_15 = MarketSnapshot("AVAX-USDT", D("24.9"), D("25"), created + 16 * 60, source="MOCK")
    assert evaluate_due_shadows(db, market_15, created + 16 * 60) == 1
    assert evaluate_due_shadows(db, market_15, created + 16 * 60) == 0
    market_60 = MarketSnapshot("AVAX-USDT", D("24.8"), D("24.9"), created + 61 * 60, source="MOCK")
    assert evaluate_due_shadows(db, market_60, created + 61 * 60) == 1
    with db.session() as conn:
        rows = conn.execute(
            "SELECT horizon_minutes, status FROM shadow_evaluations WHERE shadow_id=?",
            (sid,),
        ).fetchall()
    assert len(rows) == 2
    assert all(r["status"] == "COMPLETE" for r in rows)
