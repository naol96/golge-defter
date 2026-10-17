"""Exchange minimum order notional from instrument size and ask price."""
from __future__ import annotations

from decimal import Decimal, ROUND_UP

D = Decimal


def min_notional_usdt(
    ask: Decimal,
    min_sz_base: Decimal,
    *,
    lot_sz_base: Decimal | None = None,
) -> Decimal:
    """USDT notional for the smallest allowed spot size (minSz at ask)."""
    if ask <= 0 or min_sz_base <= 0:
        raise ValueError("ask and min_sz_base must be positive")
    notional = min_sz_base * ask
    if lot_sz_base is not None and lot_sz_base > 0:
        steps = (min_sz_base / lot_sz_base).to_integral_value(rounding=ROUND_UP)
        qty = steps * lot_sz_base
        notional = qty * ask
    return notional.quantize(D("0.0001"), rounding=ROUND_UP)
