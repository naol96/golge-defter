from decimal import Decimal

from contracts.models import ConstitutionRules, MarketSnapshot, Position
from storage.database import Database

DEFAULT_FEE_RATE = Decimal("0.001")  # labeled assumption when exchange fee unavailable


def open_paper_position(
    db: Database,
    *,
    market: MarketSnapshot,
    notional_usdt: Decimal,
    rules: ConstitutionRules,
    now: int,
) -> Position:
    if not market.is_usable(now, rules.max_data_age_seconds):
        raise ValueError("unusable market data; PAPER open rejected")
    entry = market.ask
    qty = notional_usdt / entry
    fee = notional_usdt * DEFAULT_FEE_RATE
    balance = db.get_paper_balance()
    if balance < notional_usdt + fee:
        raise ValueError("insufficient paper balance")
    stop = entry * (Decimal("1") - rules.stop_loss_fraction)
    with db.session() as conn:
        cur = conn.execute(
            """
            INSERT INTO positions
            (symbol, entry_price, notional_usdt, quantity, stop_loss_price, opened_at, status, mode, market_source)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN', 'PAPER', ?)
            """,
            (market.symbol, str(entry), str(notional_usdt), str(qty), str(stop), now, market.source),
        )
        pos_id = int(cur.lastrowid)
        conn.execute(
            "UPDATE paper_state SET balance_usdt = ? WHERE id = 1",
            (str(balance - notional_usdt - fee),),
        )
    return Position(
        id=pos_id,
        symbol=market.symbol,
        entry_price=entry,
        notional_usdt=notional_usdt,
        quantity=qty,
        stop_loss_price=stop,
        opened_at=now,
        mode="PAPER",
        status="OPEN",
    )
