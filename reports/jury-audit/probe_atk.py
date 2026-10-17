"""Read-only ATK → DEMO agent → constitution → isolated PAPER DB → dashboard.

Run from repo root: .venv/bin/python reports/jury-audit/probe_atk.py
Never uses the worker DB, credentials, a live broker or synthetic future prices.
"""
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from adapters.okx_atk import OkxAtkMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import resolve_signal
from core.decision_engine import run_decision_cycle
from dashboard.snapshot import build_kokpit_snapshot
from storage.database import Database

started = time.monotonic()
try:
    tick = OkxAtkMarketAdapter().fetch_snapshot("AVAX-USDT")
    now = int(time.time())
    signal = resolve_signal(tick, analyst="demo")
    with tempfile.TemporaryDirectory(prefix="golge-live-audit-") as directory:
        db = Database(Path(directory) / "isolated.db")
        decision, ref = run_decision_cycle(db, rules=ConstitutionRules(), signal=signal, market=tick, now=now)
        snap = build_kokpit_snapshot(db.path)
        result = {
            "probe": "ACTUAL_READ_ONLY_ATK_TO_ISOLATED_PAPER_DASHBOARD",
            "elapsed_s": round(time.monotonic() - started, 3),
            "market": {"symbol": tick.symbol, "bid": str(tick.bid), "ask": str(tick.ask),
                       "captured_at": tick.captured_at, "source": tick.source,
                       "min_order_usdt": str(tick.min_order_usdt), "age_s": now - tick.captured_at},
            "signal_origin": signal.origin,
            "status": decision.status,
            "rule": decision.rule,
            "notional_usdt": str(decision.notional_usdt),
            "dashboard_counts": snap["decisions_summary"],
            "paper_positions": len(snap["open_positions"]),
            "shadow_evaluations": snap["eval_breakdown"],
            "live_orders_sent": 0,
            "notes": "DEMO signal, not LLM; no synthetic 15/60 result and no worker DB writes.",
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if decision.status == "NO_DECISION":
            raise SystemExit(2)
except Exception as exc:
    print(json.dumps({"probe": "ACTUAL_READ_ONLY_ATK", "error_type": type(exc).__name__,
        "error": str(exc), "elapsed_s": round(time.monotonic()-started, 3),
        "live_orders_sent": 0, "result": "FAIL_CLOSED; live integration not proven"}, ensure_ascii=False))
    raise SystemExit(1)
