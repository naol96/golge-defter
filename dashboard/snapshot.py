"""Read-only kokpit snapshot for web UI (and optional Streamlit)."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

from contracts.models import ConstitutionRules
from report import build_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "golge.db"


def resolve_db_path(db_arg: str | Path | None = None) -> Path:
    raw = Path(db_arg or DEFAULT_DB)
    candidate = (ROOT / raw).resolve() if not raw.is_absolute() else raw.resolve()
    root = ROOT.resolve()
    if not str(candidate).startswith(str(root)):
        raise ValueError("DB path must stay under project root")
    if candidate.suffix.lower() != ".db":
        raise ValueError("Expected a .db SQLite file")
    return candidate


def _worker_active() -> bool:
    pid_file = ROOT / "data" / "atk_worker.pid"
    if not pid_file.is_file():
        return False
    try:
        os.kill(int(pid_file.read_text().strip()), 0)
        return True
    except (OSError, ValueError):
        return False


def _load_anchor_manifest() -> dict | None:
    path = ROOT / "evidence" / "anchor_manifest.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _row_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


def build_kokpit_snapshot(db_path: str | Path | None = None) -> dict:
    if db_path is None:
        path = DEFAULT_DB
    else:
        raw = Path(db_path)
        path = raw.resolve() if raw.is_absolute() else resolve_db_path(raw)
    if not path.is_file():
        raise FileNotFoundError(f"DB bulunamadı: {path}")

    rules = ConstitutionRules()
    report = build_report(path)

    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        bal = conn.execute("SELECT balance_usdt FROM paper_state WHERE id=1").fetchone()
        paper_balance = str(bal[0]) if bal else None

        open_positions = conn.execute(
            """
            SELECT id, symbol, notional_usdt, entry_price, stop_loss_price, status
            FROM positions WHERE status='OPEN'
            """
        ).fetchall()

        shadow_horizon = conn.execute(
            """
            SELECT se.horizon_minutes, se.status, COUNT(*) AS c
            FROM shadow_evaluations se
            GROUP BY se.horizon_minutes, se.status
            """
        ).fetchall()

        recent_shadow = conn.execute(
            """
            SELECT st.id AS shadow_id, st.symbol, st.category, se.horizon_minutes,
                   se.status, se.pnl_usdt, se.feed_source, se.evaluated_at, st.created_at
            FROM shadow_evaluations se
            JOIN shadow_trades st ON st.id = se.shadow_id
            ORDER BY COALESCE(se.evaluated_at, 0) DESC, st.id DESC, se.horizon_minutes DESC
            LIMIT 12
            """
        ).fetchall()

        decisions_by_status = conn.execute(
            "SELECT status, COUNT(*) AS c FROM decisions GROUP BY status ORDER BY c DESC"
        ).fetchall()

        recent_decisions = conn.execute(
            """
            SELECT id, symbol, signal_origin, signal_action, status, rule,
                   market_source, explanation, created_at, rules_version
            FROM decisions ORDER BY id DESC LIMIT 15
            """
        ).fetchall()

        last_row = conn.execute(
            "SELECT market_source, created_at, rules_version FROM decisions ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    now = int(time.time())
    last_age_s = None
    last_source = None
    rules_version = rules.rules_version
    if last_row:
        last_age_s = now - int(last_row["created_at"])
        last_source = last_row["market_source"]
        if last_row["rules_version"]:
            rules_version = str(last_row["rules_version"])

    eval_breakdown: dict[str, dict[str, int]] = {
        "15": {"PENDING": 0, "COMPLETE": 0},
        "60": {"PENDING": 0, "COMPLETE": 0},
    }
    for row in shadow_horizon:
        h = str(row["horizon_minutes"])
        st = str(row["status"])
        if h in eval_breakdown:
            eval_breakdown[h][st] = int(row["c"])

    constitution = {
        "tek_islem_tavan_pct": float(rules.max_position_fraction * 100),
        "max_acik_pozisyon": rules.max_open_positions,
        "max_toplam_risk_pct": float(rules.max_total_exposure_fraction * 100),
        "max_spread_pct": float(rules.max_spread_fraction * 100),
        "stop_loss_pct": float(rules.stop_loss_fraction * 100),
        "gunluk_zarar_pct": float(rules.max_daily_realized_loss_fraction * 100),
        "bekleme_dk": rules.pair_cooldown_seconds // 60,
        "gozlem_esigi_usdt": str(rules.observation_min_balance_usdt),
        "rules_version_code": rules.rules_version,
    }

    return {
        "generated_at": now,
        "db": str(path),
        "worker_active": _worker_active(),
        "rules_version": rules_version,
        "last_decision_age_s": last_age_s,
        "last_market_source": last_source,
        "report": report,
        "constitution": constitution,
        "paper_balance_usdt": paper_balance,
        "open_positions": [_row_dict(r) for r in open_positions],
        "eval_breakdown": eval_breakdown,
        "decisions_summary": {r["status"]: int(r["c"]) for r in decisions_by_status},
        "recent_shadow": [_row_dict(r) for r in recent_shadow],
        "recent_decisions": [_row_dict(r) for r in recent_decisions],
        "anchor": _load_anchor_manifest(),
    }
