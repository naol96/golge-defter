"""Background PAPER worker: live ATK ticks, decisions, shadow 15/60 follow-up."""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

from adapters.mock_market import MockMarketAdapter
from adapters.okx_atk import OkxAtkMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import resolve_signal
from core.decision_engine import run_decision_cycle, utc_day
from core.position_monitor import monitor_open_positions
from core.shadow_evaluator import evaluate_due_shadows
from storage.database import Database

DEFAULT_SYMBOLS = ("AVAX-USDT", "BTC-USDT", "ETH-USDT")
_STOP = False


def _handle_stop(*_args: object) -> None:
    global _STOP
    _STOP = True


def run_cycle(
    db: Database,
    *,
    symbols: list[str],
    source: str,
    analyst: str,
) -> None:
    adapter = OkxAtkMarketAdapter() if source == "atk" else MockMarketAdapter()
    rules = ConstitutionRules()
    for symbol in symbols:
        now = int(time.time())
        day = utc_day(now)
        try:
            market = adapter.fetch_snapshot(symbol)
        except Exception as exc:
            logging.warning("MARKET_UNAVAILABLE %s: %s", symbol, exc)
            continue
        signal = resolve_signal(market, analyst=analyst)
        decision, ref_id = run_decision_cycle(
            db, rules=rules, signal=signal, market=market, now=now
        )
        monitor_open_positions(db, market, now, day)
        evaluate_due_shadows(db, market, now)
        logging.info(
            "cycle symbol=%s source=%s decision=%s rule=%s ref=%s",
            symbol,
            market.source,
            decision.status,
            decision.rule,
            ref_id,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Gölge Defter ATK worker (PAPER)")
    parser.add_argument("--db", default="data/golge.db")
    parser.add_argument("--source", choices=["atk", "mock"], default="atk")
    parser.add_argument("--analyst", choices=["demo", "llm"], default="demo")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    db = Database(args.db)
    logging.info(
        "worker_start source=%s analyst=%s interval=%ss db=%s",
        args.source,
        args.analyst,
        args.interval,
        args.db,
    )
    while not _STOP:
        run_cycle(db, symbols=args.symbols, source=args.source, analyst=args.analyst)
        time.sleep(max(5, args.interval))
    logging.info("worker_stop")


if __name__ == "__main__":
    main()
