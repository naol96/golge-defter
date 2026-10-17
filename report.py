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


def _ensure_schema(db_path: Path) -> None:
    if not db_path.is_file():
        raise SystemExit(
            f"Database not found: {db_path}\n"
            "Worker writes to data/golge.db (see start_atk.sh). "
            "Run: python report.py --db data/golge.db"
        )
    if db_path.stat().st_size == 0:
        raise SystemExit(
            f"Database is empty: {db_path}\n"
            "Use the worker database: python report.py --db data/golge.db"
        )
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='decisions'"
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise SystemExit(
            f"No Gölge Defter schema in {db_path} (missing decisions table).\n"
            "Start the worker: bash start_atk.sh\n"
            "Then: python report.py --db data/golge.db --out evidence/measurement_report.md"
        )


def build_report(db_path: Path, *, connection: sqlite3.Connection | None = None) -> dict:
    if connection is None:
        _ensure_schema(db_path)
    conn = connection if connection is not None else sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    if connection is None:
        conn.execute("BEGIN")
    try:
        decisions = {str(r[0]): int(r[1]) for r in conn.execute("""
            SELECT CASE WHEN status='SHADOW_RISK' AND rule IN ('OBSERVATION','MIN_ORDER')
                        THEN 'TECHNICAL_BLOCK' ELSE status END AS effective_status, COUNT(*)
            FROM decisions GROUP BY effective_status
        """)}
        signal_origins = _count_by(conn, "decisions", "signal_origin")
        market_sources = _count_by(conn, "decisions", "market_source")
        shadow_by_cat = {str(r[0]): int(r[1]) for r in conn.execute("""
            SELECT CASE WHEN constitution_rule IN ('OBSERVATION','MIN_ORDER')
                        THEN 'TECHNICAL_UNEXECUTABLE' ELSE category END AS effective_category, COUNT(*)
            FROM shadow_trades GROUP BY effective_category
        """)}
        shadow_by_source = _count_by(conn, "shadow_trades", "source")
        eval_status = _count_by(conn, "shadow_evaluations", "status")
        pending = conn.execute(
            "SELECT COUNT(*) FROM shadow_evaluations WHERE status='PENDING'"
        ).fetchone()[0]
        complete_15 = conn.execute(
            "SELECT COUNT(*) FROM shadow_evaluations WHERE horizon_minutes=15 AND status='COMPLETE'"
        ).fetchone()[0]
        live_15 = conn.execute(
            """
            SELECT COUNT(*) FROM shadow_evaluations se
            JOIN shadow_trades st ON st.id = se.shadow_id
            WHERE se.horizon_minutes=15 AND se.status='COMPLETE'
              AND se.feed_source IN ('ATK_LIVE_MARKET', 'ATK')
              AND st.source IN ('ATK_LIVE_MARKET', 'ATK')
            """
        ).fetchone()[0]
        complete_60 = conn.execute(
            "SELECT COUNT(*) FROM shadow_evaluations WHERE horizon_minutes=60 AND status='COMPLETE'"
        ).fetchone()[0]
        technical_blocks = int(decisions.get("TECHNICAL_BLOCK", 0))
        risk_blocks = int(decisions.get("SHADOW_RISK", 0))
        live_60 = conn.execute(
            """
            SELECT COUNT(*) FROM shadow_evaluations se
            JOIN shadow_trades st ON st.id = se.shadow_id
            WHERE se.horizon_minutes=60 AND se.status='COMPLETE'
              AND st.source IN ('ATK_LIVE_MARKET', 'ATK')
              AND se.feed_source IN ('ATK_LIVE_MARKET', 'ATK')
            """
        ).fetchone()[0]
        last_decision = conn.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        paper_balance = conn.execute(
            "SELECT balance_usdt FROM paper_state WHERE id = 1"
        ).fetchone()
        open_positions = conn.execute(
            "SELECT COUNT(*) FROM positions WHERE status = 'OPEN'"
        ).fetchone()[0]
    finally:
        if connection is None:
            conn.close()

    return {
        "db": str(db_path),
        "decisions_by_status": decisions,
        "decisions_by_market_source": market_sources,
        "decisions_by_signal_origin": signal_origins,
        "shadow_by_category": shadow_by_cat,
        "shadow_by_feed_source": shadow_by_source,
        "evaluations_by_status": eval_status,
        "pending_evaluations": int(pending),
        "complete_15m": int(complete_15),
        "complete_15m_live_feed": int(live_15),
        "complete_60m": int(complete_60),
        "complete_60m_live_feed": int(live_60),
        "decisions_technical_block": technical_blocks,
        "decisions_shadow_risk": risk_blocks,
        "last_decision": dict(last_decision) if last_decision else None,
        "paper_balance_usdt": str(paper_balance[0]) if paper_balance else None,
        "open_paper_positions": int(open_positions),
        "notes": [
            "PAPER only; no LIVE orders.",
            "ATK market data does not imply an LLM signal; signal origins are counted separately.",
            "Legacy OBSERVATION/MIN_ORDER risk rows are counted as technical without rewriting stored records.",
            "COMPLETE counts include all categories; technical observations are not risk protection metrics.",
            "Live-feed counts require both entry and exit from ATK; they are not verified LLM performance.",
            "FIXTURE/MOCK counts are not live market proof.",
            "Pending 15/60 rows are normal until horizon elapses; feed_source fills on COMPLETE.",
            "TECHNICAL_BLOCK/MIN_ORDER: constitutional notional (25% of balance) below the per-symbol adapter minimum, not a risk veto.",
        ],
    }


def format_markdown(report: dict) -> str:
    lines = [
        "# Gölge Defter — ölçüm raporu",
        "",
        f"**Veritabanı:** `{report['db']}`",
        "",
        "## Kararlar (durum)",
    ]
    for key, count in sorted(report["decisions_by_status"].items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Kararlar (piyasa kaynağı)"])
    for key, count in sorted(report["decisions_by_market_source"].items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Sinyal kökeni"])
    for key, count in sorted(report["decisions_by_signal_origin"].items()):
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Gölge defter",
            f"- Kategori: {report['shadow_by_category']}",
            f"- feed_source: {report['shadow_by_feed_source']}",
            "",
            "## 15/60 değerlendirme",
            f"- Durum: {report['evaluations_by_status']}",
            f"- Bekleyen: {report['pending_evaluations']}",
            f"- Tamamlanan 15 dk: {report['complete_15m']} (ATK giriş/çıkış kökeni: {report['complete_15m_live_feed']})",
            f"- Tamamlanan 60 dk: {report['complete_60m']} (ATK giriş/çıkış kökeni: {report['complete_60m_live_feed']})",
            "",
            "## Engelleme sınıflandırması",
            f"- TECHNICAL_BLOCK (min emir / icra): {report['decisions_technical_block']}",
            f"- SHADOW_RISK (Anayasa): {report['decisions_shadow_risk']}",
            "",
            "## PAPER durumu",
            f"- Bakiye: {report.get('paper_balance_usdt')} USDT",
            f"- Açık pozisyon: {report.get('open_paper_positions', 0)}",
            "",
            "## Son karar",
        ]
    )
    last = report.get("last_decision")
    if last:
        lines.append(
            f"- id={last.get('id')} status={last.get('status')} "
            f"symbol={last.get('symbol')} market_source={last.get('market_source')}"
        )
    else:
        lines.append("- (yok)")
    lines.extend(["", "## Notlar"])
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gölge Defter kanıt raporu")
    parser.add_argument("--db", default="data/golge.db")
    parser.add_argument(
        "--out",
        default=None,
        help="Write report to file (markdown if path ends with .md, else JSON)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default=None,
        help="Output format (default: markdown for .md --out, else json)",
    )
    args = parser.parse_args()
    report = build_report(Path(args.db))
    fmt = args.format
    if fmt is None and args.out:
        fmt = "markdown" if str(args.out).endswith(".md") else "json"
    if fmt is None:
        fmt = "json"
    if fmt == "markdown":
        body = format_markdown(report)
    else:
        body = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body, encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        print(body)


if __name__ == "__main__":
    main()
