"""Analyst layer: schema-validated BUY/PASS only (demo deterministic by default)."""
from __future__ import annotations

import json
from typing import Any

from contracts.models import AnalystSignal, MarketSnapshot


def validate_analyst_payload(payload: dict[str, Any]) -> AnalystSignal:
    symbol = str(payload.get("symbol", "")).strip()
    action = str(payload.get("action", "")).strip().upper()
    reason = str(payload.get("reason", "")).strip()
    if action not in ("BUY", "PASS"):
        raise ValueError("action must be BUY or PASS")
    if not symbol or not reason:
        raise ValueError("symbol and reason are required")
    return AnalystSignal(symbol=symbol, action=action, reason=reason, origin="LLM")


def demo_signal(market: MarketSnapshot) -> AnalystSignal:
    """Explicitly labeled demo signal for MVP when no LLM credentials are configured."""
    spread = (market.ask - market.bid) / market.ask
    if spread <= 0.0015:
        return AnalystSignal(
            symbol=market.symbol,
            action="BUY",
            reason="Demo: dar spread, yapılandırılmış alım sinyali (LLM değil).",
            origin="DEMO",
        )
    return AnalystSignal(
        symbol=market.symbol,
        action="PASS",
        reason="Demo: spread geniş, pas (LLM değil).",
        origin="DEMO",
    )


def parse_analyst_json(text: str) -> AnalystSignal:
    return validate_analyst_payload(json.loads(text))

