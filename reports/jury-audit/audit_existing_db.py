"""Recalculate existing stored results from a read-only consistent backup.

This verifies arithmetic and stored metadata, not historical feed authenticity.
"""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.shadow_evaluator import shadow_pnl
from dashboard.snapshot import build_kokpit_snapshot

root=Path(__file__).resolve().parents[2]
original=root/"data/golge.db"
with tempfile.TemporaryDirectory(prefix="golge-history-audit-") as directory:
    path=Path(directory)/"frozen.db"
    with sqlite3.connect(f"file:{original}?mode=ro",uri=True) as source:
        with sqlite3.connect(path) as destination:
            source.backup(destination)
    conn=sqlite3.connect(f"file:{path}?mode=ro",uri=True)
    conn.row_factory=sqlite3.Row
    rows=conn.execute("""
        SELECT st.entry_ask,st.notional_usdt,st.created_at,st.target_15_at,st.target_60_at,
               st.category,st.source,se.*
        FROM shadow_evaluations se JOIN shadow_trades st ON st.id=se.shadow_id
        WHERE se.status='COMPLETE'
    """).fetchall()
    mismatches=[]; before_due=[]; missing_notes=0; mixed_sources=0
    horizons={"15":0,"60":0}
    for row in rows:
        computed=shadow_pnl(Decimal(row["entry_ask"]),Decimal(row["exit_bid"]),Decimal(row["notional_usdt"]))
        if computed != Decimal(row["pnl_usdt"]): mismatches.append([row["shadow_id"],row["horizon_minutes"],str(computed),row["pnl_usdt"]])
        target=row["target_15_at"] if row["horizon_minutes"]==15 else row["target_60_at"]
        if row["evaluated_at"] is None or row["evaluated_at"]<target: before_due.append([row["shadow_id"],row["horizon_minutes"]])
        if "stop_dogrulamasi_sinirli" not in (row["note"] or ""): missing_notes+=1
        if row["source"] != row["feed_source"] and not {row["source"],row["feed_source"]}<={"ATK","ATK_LIVE_MARKET"}: mixed_sources+=1
        horizons[str(row["horizon_minutes"])]+=1
    snapshot=build_kokpit_snapshot(path)
    report=snapshot["report"]
    for horizon in ("15","60"):
        assert snapshot["eval_breakdown"][horizon]["COMPLETE"] == horizons[horizon] == report[f"complete_{horizon}m"]
    raw_decisions=conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    assert sum(snapshot["decisions_summary"].values())==raw_decisions
    assert sum(report["decisions_by_signal_origin"].values())==raw_decisions
    assert report["pending_evaluations"] == sum(h["PENDING"] for h in snapshot["eval_breakdown"].values())
    conn.close()
    print(json.dumps({"source_db":str(original),"method":"READ_ONLY_BACKUP_RECALCULATION",
        "decisions":snapshot["decisions_summary"],"signal_origins":report["decisions_by_signal_origin"],
        "market_sources":report["decisions_by_market_source"],"completed_horizons":horizons,
        "pnl_mismatches":mismatches,"before_due":before_due,"mixed_source_results":mixed_sources,
        "legacy_missing_limited_stop_notes":missing_notes,"dashboard_counter_consistency":"PASS",
        "note":"Stored arithmetic only. Historical quote age is not persisted, so historical freshness is unverified. No production records modified."},indent=2,ensure_ascii=False))
    if mismatches or before_due or mixed_sources: raise SystemExit(1)
