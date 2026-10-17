"""Shadow Ledger MVP CLI entry (PAPER only)."""
from __future__ import annotations

import argparse
import time

from adapters.mock_market import MockMarketAdapter
from adapters.okx_atk import OkxAtkMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import demo_signal
from core.decision_engine import run_decision_cycle, utc_day
from core.position_monitor import monitor_open_positions
from core.shadow_evaluator import evaluate_due_shadows
from storage.database import Database


def main() -> None:
    parser = argparse.ArgumentParser(description="Gölge Defter MVP (PAPER)")
    parser.add_argument("--symbol", default="AVAX-USDT")
    parser.add_argument("--source", choices=["atk", "mock"], default="atk")
    parser.add_argument("--db", default="data/golge.db")
    args = parser.parse_args()

    db = Database(args.db)
    adapter = OkxAtkMarketAdapter() if args.source == "atk" else MockMarketAdapter()
    market = adapter.fetch_snapshot(args.symbol)
    signal = demo_signal(market)
    now = int(time.time())
    decision, ref_id = run_decision_cycle(
        db, rules=ConstitutionRules(), signal=signal, market=market, now=now
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
        }
    )


if __name__ == "__main__":
    main()
