"""Analyst layer: schema-validated BUY/PASS only (demo deterministic by default)."""
from __future__ import annotations

import json
from typing import Any

from contracts.models import AnalystSignal, MarketSnapshot


def validate_analyst_payload(payload: dict[str, Any]) -> AnalystSignal:
    if not isinstance(payload, dict) or set(payload) != {"symbol", "action", "reason"}:
        raise ValueError("only symbol, action and reason are permitted")
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


def llm_signal(market: MarketSnapshot) -> AnalystSignal:
    """Optional LLM analyst; fail-closed PASS when unavailable or invalid."""
    import os
    import urllib.error
    import urllib.request

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return AnalystSignal(
            symbol=market.symbol,
            action="PASS",
            reason="LLM_FAIL_CLOSED: OPENAI_API_KEY yapılandırılmadı.",
            origin="LLM",
        )
    prompt = (
        "Piyasa: " + json.dumps({"symbol": market.symbol, "bid": str(market.bid),
            "ask": str(market.ask), "captured_at": market.captured_at, "source": market.source})
        + '\nYalnızca JSON döndür: {"symbol":"' + market.symbol
        + '","action":"BUY veya PASS","reason":"tek cümle"}'
    )
    api_url = os.environ.get(
        "GOLGE_LLM_API_URL",
        "https://api.openai.com/v1/chat/completions",
    ).strip()
    body = json.dumps(
        {
            "model": os.environ.get("GOLGE_LLM_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "system",
                    "content": "Kripto analistisin. Yalnızca BUY veya PASS öner. Emir/tutar üretme.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
    ).encode()
    req = urllib.request.Request(
        api_url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode())
        text = payload["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        signal = parse_analyst_json(text)
        if signal.symbol != market.symbol:
            raise ValueError("analyst symbol differs from market")
        return signal
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError, AttributeError, ValueError, json.JSONDecodeError):
        return AnalystSignal(
            symbol=market.symbol,
            action="PASS",
            reason="LLM_FAIL_CLOSED: model çıktısı doğrulanamadı.",
            origin="LLM",
        )


def resolve_signal(market: MarketSnapshot, analyst: str = "demo") -> AnalystSignal:
    if analyst == "llm":
        return llm_signal(market)
    return demo_signal(market)
