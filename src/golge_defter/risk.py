"""Backward-compatible shim over core.constitution + contracts."""
from decimal import Decimal
from typing import Literal

from contracts.models import AnalystSignal as _AnalystSignal
from contracts.models import ConstitutionRules as Constitution
from contracts.models import MarketSnapshot as _MarketSnapshot
from core.constitution import DecisionResult, evaluate as _evaluate, tighten_position_limit

D = Decimal
AllowedDirection = Literal["BUY", "PASS"]


class MarketSnapshot(_MarketSnapshot):
    def __init__(self, pair: str, bid: Decimal, ask: Decimal, captured_at: int):
        super().__init__(symbol=pair, bid=bid, ask=ask, captured_at=captured_at, source="MOCK")

    @property
    def pair(self) -> str:
        return self.symbol


class AnalystSignal(_AnalystSignal):
    def __init__(self, pair: str, direction: AllowedDirection, reason: str):
        super().__init__(symbol=pair, action=direction, reason=reason, origin="DEMO")

    @property
    def pair(self) -> str:
        return self.symbol

    @property
    def direction(self) -> AllowedDirection:
        return self.action


class Decision(DecisionResult):
    @property
    def constitutional_amount_usdt(self) -> Decimal:
        return self.notional_usdt


def evaluate(
    *,
    constitution: Constitution,
    signal: AnalystSignal,
    market: MarketSnapshot,
    available_usdt: Decimal,
    min_order_usdt: Decimal,
    daily_realized_loss_usdt: Decimal,
    now: int,
) -> Decision:
    result = _evaluate(
        constitution=constitution,
        signal=_AnalystSignal(
            symbol=signal.symbol, action=signal.action, reason=signal.reason, origin=signal.origin
        ),
        market=_MarketSnapshot(
            symbol=market.symbol,
            bid=market.bid,
            ask=market.ask,
            captured_at=market.captured_at,
            source=getattr(market, "source", "MOCK"),
            min_order_usdt=getattr(market, "min_order_usdt", Decimal("10")),
        ),
        available_usdt=available_usdt,
        min_order_usdt=min_order_usdt,
        daily_realized_loss_usdt=daily_realized_loss_usdt,
        now=now,
        mode="PAPER",
    )
    return Decision(
        status=result.status,
        rule=result.rule,
        explanation=result.explanation,
        notional_usdt=result.notional_usdt,
        spread_fraction=result.spread_fraction,
        shadow_category=result.shadow_category,
    )
