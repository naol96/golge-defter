"""One-page evidence report for hackathon delivery (CLI)."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def _count_by(conn: sqlite3.Connection, table: str, column: str) -> dict[str, int]:
    rows = conn.execute(
        f"SELECT {column}, COUNT(*) AS c FROM {table} GROUP BY {column}"
    ).fetchall()
    return {str(r[0]): int(r[1]) for r in rows}


def build_report(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        decisions = _count_by(conn, "decisions", "status")
        market_sources = _count_by(conn, "decisions", "market_source")
        shadow_by_cat = _count_by(conn, "shadow_trades", "category")
        shadow_by_source = _count_by(conn, "shadow_trades", "source")
        eval_status = _count_by(conn, "shadow_evaluations", "status")
        pending = conn.execute(
            "SELECT COUNT(*) FROM shadow_evaluations WHERE status='PENDING'"
        ).fetchone()[0]
        complete_15 = conn.execute(
            "SELECT COUNT(*) FROM shadow_evaluations WHERE horizon_minutes=15 AND status='COMPLETE'"
        ).fetchone()[0]
        complete_60 = conn.execute(
            "SELECT COUNT(*) FROM shadow_evaluations WHERE horizon_minutes=60 AND status='COMPLETE'"
        ).fetchone()[0]
        live_60 = conn.execute(
            """
            SELECT COUNT(*) FROM shadow_evaluations se
            JOIN shadow_trades st ON st.id = se.shadow_id
            WHERE se.horizon_minutes=60 AND se.status='COMPLETE'
              AND st.source IN ('ATK_LIVE_MARKET', 'ATK')
            """
        ).fetchone()[0]
        last_decision = conn.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    return {
        "db": str(db_path),
        "decisions_by_status": decisions,
        "decisions_by_market_source": market_sources,
        "shadow_by_category": shadow_by_cat,
        "shadow_by_feed_source": shadow_by_source,
        "evaluations_by_status": eval_status,
        "pending_evaluations": int(pending),
        "complete_15m": int(complete_15),
        "complete_60m": int(complete_60),
        "complete_60m_live_feed": int(live_60),
        "last_decision": dict(last_decision) if last_decision else None,
        "notes": [
            "PAPER only; no LIVE orders.",
            "FIXTURE/MOCK counts are not live market proof.",
            "Pending 15/60 rows are normal until horizon elapses.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gölge Defter kanıt raporu")
    parser.add_argument("--db", default="data/golge.db")
    args = parser.parse_args()
    report = build_report(Path(args.db))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
