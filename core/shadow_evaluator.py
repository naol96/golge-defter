from decimal import Decimal

from contracts.models import MarketSnapshot, compatible_sources
from storage.database import Database

DEFAULT_FEE_RATE = Decimal("0.001")


def shadow_pnl(entry_ask: Decimal, exit_bid: Decimal, notional: Decimal) -> Decimal:
    qty = notional / entry_ask
    buy_fee = notional * DEFAULT_FEE_RATE
    sell_gross = qty * exit_bid
    sell_fee = sell_gross * DEFAULT_FEE_RATE
    return sell_gross - sell_fee - notional - buy_fee


def evaluate_due_shadows(db: Database, market: MarketSnapshot, now: int) -> int:
    if not market.is_usable(now):
        return 0
    sources = compatible_sources(market.source)
    placeholders = ",".join("?" for _ in sources)
    updated = 0
    with db.session() as conn:
        rows = conn.execute(
            f"""
            SELECT st.id, st.entry_ask, st.notional_usdt, st.created_at,
                   st.target_15_at, st.target_60_at,
                   se.horizon_minutes, se.status
            FROM shadow_trades st
            JOIN shadow_evaluations se ON se.shadow_id = st.id
            WHERE st.symbol = ? AND se.status = 'PENDING'
              AND st.source IN ({placeholders})
            """,
            (market.symbol, *sources),
        ).fetchall()
        for row in rows:
            horizon = int(row["horizon_minutes"])
            due_at = int(row["target_15_at"] if horizon == 15 else row["target_60_at"])
            if now < due_at or market.captured_at < due_at:
                continue
            entry = Decimal(str(row["entry_ask"]))
            notional = Decimal(str(row["notional_usdt"]))
            pnl = shadow_pnl(entry, market.bid, notional)
            note = "stop_dogrulamasi_sinirli"
            if now > due_at + 120:
                note += ";LATE_EVALUATION"
            cur = conn.execute(
                """
                UPDATE shadow_evaluations
                SET status='COMPLETE', exit_bid=?, pnl_usdt=?, evaluated_at=?, note=?, feed_source=?
                WHERE shadow_id=? AND horizon_minutes=? AND status='PENDING'
                """,
                (str(market.bid), str(pnl), now, note, market.source, row["id"], horizon),
            )
            updated += cur.rowcount
    return updated
