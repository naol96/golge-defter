from decimal import Decimal

from contracts.models import MarketSnapshot
from storage.database import Database

FEE_RATE = Decimal("0.001")


def monitor_open_positions(db: Database, market: MarketSnapshot, now: int, utc_day: str) -> list[int]:
    closed: list[int] = []
    with db.session() as conn:
        rows = conn.execute(
            "SELECT * FROM positions WHERE status = 'OPEN' AND symbol = ?",
            (market.symbol,),
        ).fetchall()
        for row in rows:
            stop = Decimal(str(row["stop_loss_price"]))
            if market.bid > stop:
                continue
            entry = Decimal(str(row["entry_price"]))
            notional = Decimal(str(row["notional_usdt"]))
            qty = Decimal(str(row["quantity"]))
            exit_price = market.bid
            proceeds = qty * exit_price
            fee = proceeds * FEE_RATE
            pnl = proceeds - fee - notional
            conn.execute(
                """
                UPDATE positions SET status='CLOSED', closed_at=?, close_reason='STOP_LOSS'
                WHERE id=? AND status='OPEN'
                """,
                (now, row["id"]),
            )
            if conn.total_changes == 0:
                continue
            bal_row = conn.execute("SELECT balance_usdt FROM paper_state WHERE id=1").fetchone()
            balance = Decimal(str(bal_row["balance_usdt"])) + proceeds - fee
            conn.execute("UPDATE paper_state SET balance_usdt=? WHERE id=1", (str(balance),))
            if pnl < 0:
                loss_row = conn.execute(
                    "SELECT daily_loss_usdt, daily_loss_day FROM paper_state WHERE id=1"
                ).fetchone()
                current = Decimal("0")
                if loss_row["daily_loss_day"] == utc_day:
                    current = Decimal(str(loss_row["daily_loss_usdt"]))
                conn.execute(
                    "UPDATE paper_state SET daily_loss_usdt=?, daily_loss_day=? WHERE id=1",
                    (str(current + (-pnl)), utc_day),
                )
            closed.append(int(row["id"]))
    return closed
