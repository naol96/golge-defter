#!/usr/bin/env python3
"""Record a constitutional SHADOW_RISK on a separate DB (does not touch data/golge.db)."""
from __future__ import annotations

import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

from adapters.okx_atk import OkxAtkMarketAdapter
from contracts.models import ConstitutionRules
from core.constitution import tighten_spread_limit
from core.analyst import resolve_signal
from core.decision_engine import run_decision_cycle, utc_day
from core.position_monitor import monitor_open_positions
from core.shadow_evaluator import evaluate_due_shadows
from core.user_rules import apply_user_request
from storage.database import Database


def main() -> None:
    parser = argparse.ArgumentParser(description="Hamle A: spread sıkılaştır + canlı ATK döngüsü")
    parser.add_argument("--db", default="evidence/shadow_risk_atk.db")
    parser.add_argument("--symbol", default="BTC-USDT")
    parser.add_argument(
        "--user-rule",
        default="Makas en fazla %0.03 olsun",
        help="Doğal dil makas sıkılaştırma (rehber Hamle A)",
    )
    parser.add_argument("--balance", default="50", help="PAPER başlangıç bakiyesi (USDT)")
    args = parser.parse_args()

    db_path = Path(args.db)
    if db_path.exists():
        print(f"Refusing to overwrite existing DB: {db_path}", file=sys.stderr)
        sys.exit(1)

    db = Database(db_path)
    with db.session() as conn:
        conn.execute(
            "UPDATE paper_state SET balance_usdt = ? WHERE id = 1",
            (str(args.balance),),
        )
        conn.execute(
            "UPDATE paper_state_meta SET day_start_balance_usdt = ? WHERE id = 1",
            (str(args.balance),),
        )

    rules = ConstitutionRules()
    rules, _, user_msg = apply_user_request(rules, args.user_rule)

    market = OkxAtkMarketAdapter().fetch_snapshot(args.symbol)
    spread = (market.ask - market.bid) / market.ask
    if spread <= rules.max_spread_fraction:
        forced, force_msg = tighten_spread_limit(rules, spread * Decimal("0.5"))
        rules = forced
        user_msg = f"{user_msg} · {force_msg} (canlı makas kanıtı)"

    signal = resolve_signal(market, analyst="demo")
    now = int(time.time())
    decision, ref_id = run_decision_cycle(
        db, rules=rules, signal=signal, market=market, now=now
    )
    monitor_open_positions(db, market, now, utc_day(now))
    evaluate_due_shadows(db, market, now)

    out = {
        "db": str(db_path),
        "user_rule_message": user_msg,
        "max_spread_fraction": str(rules.max_spread_fraction),
        "decision": decision.status,
        "rule": decision.rule,
        "explanation": decision.explanation,
        "ref_id": ref_id,
        "market_source": market.source,
        "bid": str(market.bid),
        "ask": str(market.ask),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if decision.status != "SHADOW_RISK":
        sys.exit(2)


if __name__ == "__main__":
    main()
