from __future__ import annotations

import time
from datetime import datetime, timezone

from contracts.models import AnalystSignal, ConstitutionRules, DecisionResult, MarketSnapshot
from core.constitution import evaluate
from core.paper_broker import open_paper_position
from storage.database import Database


def utc_day(now: int) -> str:
    return datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")


def run_decision_cycle(
    db: Database,
    *,
    rules: ConstitutionRules,
    signal: AnalystSignal,
    market: MarketSnapshot,
    now: int | None = None,
) -> tuple[DecisionResult, int | None]:
    now = int(now or time.time())
    daily_loss = db.get_daily_loss(utc_day(now))
    decision = evaluate(
        constitution=rules,
        signal=signal,
        market=market,
        available_usdt=db.get_paper_balance(),
        min_order_usdt=market.min_order_usdt,
        daily_realized_loss_usdt=daily_loss,
        now=now,
        mode="PAPER",
    )
    ref_id: int | None = None
    if decision.shadow_category is not None:
        ref_id = db.insert_shadow(
            symbol=signal.symbol,
            category=decision.shadow_category,
            entry_ask=market.ask,
            notional_usdt=decision.notional_usdt,
            reason=signal.reason,
            constitution_rule=decision.rule,
            created_at=now,
            source=market.source,
        )
    if decision.status == "APPROVED_PAPER":
        pos = open_paper_position(
            db,
            market=market,
            notional_usdt=decision.notional_usdt,
            rules=rules,
            now=now,
        )
        ref_id = pos.id
    return decision, ref_id
