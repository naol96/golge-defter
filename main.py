"""Shadow Ledger MVP CLI entry (PAPER only)."""
from __future__ import annotations

import argparse
import time

from adapters.mock_market import MockMarketAdapter
from adapters.okx_atk import OkxAtkMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import resolve_signal
from core.user_rules import apply_user_request
from core.decision_engine import run_decision_cycle, utc_day
from core.position_monitor import monitor_open_positions
from core.shadow_evaluator import evaluate_due_shadows
from storage.database import Database


def main() -> None:
    parser = argparse.ArgumentParser(description="Gölge Defter MVP (PAPER)")
    parser.add_argument("--symbol", default="AVAX-USDT")
    parser.add_argument("--source", choices=["atk", "mock"], default="atk")
    parser.add_argument("--analyst", choices=["demo", "llm"], default="demo")
    parser.add_argument("--db", default="data/golge.db")
    parser.add_argument("--user-rule", default="", help="Doğal dil sıkılaştırma talebi")
    args = parser.parse_args()

    db = Database(args.db)
    adapter = OkxAtkMarketAdapter() if args.source == "atk" else MockMarketAdapter()
    market = adapter.fetch_snapshot(args.symbol)
    signal = resolve_signal(market, analyst=args.analyst)
    now = int(time.time())
    rules = ConstitutionRules()
    user_msg = ""
    if args.user_rule.strip():
        rules, _, user_msg = apply_user_request(rules, args.user_rule)
    decision, ref_id = run_decision_cycle(
        db, rules=rules, signal=signal, market=market, now=now
    )
    monitor_open_positions(db, market, now, utc_day(now))
    evaluate_due_shadows(db, market, now)
    print(
        {
            "mode": "PAPER",
            "market_source": market.source,
            "signal_origin": signal.origin,
            "decision": decision.status,
            "rule": decision.rule,
            "explanation": decision.explanation,
            "ref_id": ref_id,
            "bid": str(market.bid),
            "ask": str(market.ask),
            "data_age_s": now - market.captured_at,
            "user_rule_message": user_msg or None,
        }
    )


if __name__ == "__main__":
    main()
