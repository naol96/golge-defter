"""Read-only ATK → DEMO agent → constitution → isolated PAPER DB → dashboard.

Run from repo root: .venv/bin/python reports/jury-audit/probe_atk.py
Never uses the worker DB, credentials, a live broker or synthetic future prices.
"""
import json
from pathlib import Path
import sys
import tempfile
import time
import threading
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from adapters.okx_atk import OkxAtkMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import resolve_signal
from core.decision_engine import run_decision_cycle
from dashboard.snapshot import build_kokpit_snapshot
from dashboard.serve_kokpit import KokpitHandler
from storage.database import Database

started = time.monotonic()
try:
    tick = OkxAtkMarketAdapter().fetch_snapshot("AVAX-USDT")
    now = int(time.time())
    signal = resolve_signal(tick, analyst="demo")
    with tempfile.TemporaryDirectory(prefix="golge-live-audit-", dir=Path(__file__).resolve().parents[2] / "data") as directory:
        db = Database(Path(directory) / "isolated.db")
        decision, ref = run_decision_cycle(db, rules=ConstitutionRules(), signal=signal, market=tick, now=now)
        shadow_decision, shadow_ref = run_decision_cycle(
            db, rules=ConstitutionRules(), signal=signal, market=tick, now=int(time.time())
        )
        # Exercise the actual JSON and HTML endpoints, not just an internal render.
        server = ThreadingHTTPServer(("127.0.0.1", 0), KokpitHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            relative_db = db.path.relative_to(Path(__file__).resolve().parents[2])
            with urlopen(base + "/api/snapshot?" + urlencode({"db": str(relative_db)}), timeout=3) as response:
                snap = json.load(response)
            with urlopen(base + "/", timeout=3) as response:
                html = response.read().decode()
                assert 'id="root"' in html or 'id="shadow-body"' in html
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        assert snap["decisions_summary"].get("APPROVED_PAPER") == 1
        assert snap["decisions_summary"].get("SHADOW_RISK") == 1

        result = {
            "probe": "ACTUAL_READ_ONLY_ATK_TO_ISOLATED_PAPER_DASHBOARD",
            "elapsed_s": round(time.monotonic() - started, 3),
            "market": {"symbol": tick.symbol, "bid": str(tick.bid), "ask": str(tick.ask),
                       "captured_at": tick.captured_at, "source": tick.source,
                       "min_order_usdt": str(tick.min_order_usdt), "age_s": now - tick.captured_at},
            "signal_origin": signal.origin,
            "status": decision.status,
            "rule": decision.rule,
            "shadow_branch": {"status": shadow_decision.status, "rule": shadow_decision.rule, "ref": shadow_ref},
            "http_dashboard": "HTML and /api/snapshot verified",
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
