"""Read-only aggregates for the web kokpit (timeline, rules, counterfactual outcomes)."""
from __future__ import annotations

import sqlite3
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dashboard.snapshot import resolve_db_path

EFFECTIVE_STATUS = """CASE WHEN status='SHADOW_RISK' AND rule IN ('OBSERVATION','MIN_ORDER')
                         THEN 'TECHNICAL_BLOCK' ELSE status END"""
EFFECTIVE_CATEGORY = """CASE WHEN st.constitution_rule IN ('OBSERVATION','MIN_ORDER')
                           THEN 'TECHNICAL_UNEXECUTABLE' ELSE st.category END"""

MAX_LIMIT = 500


def _dec(value) -> Decimal | None:
    if value is None:
        return None
    try:
        out = Decimal(str(value))
    except InvalidOperation:
        return None
    return out if out.is_finite() else None


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def build_analytics(
    db_path: str | Path | None = None,
    *,
    hours: int = 6,
    bucket_minutes: int = 10,
    limit: int = 200,
) -> dict:
    # Absolute paths are trusted callers (tests/CLI); the HTTP layer only passes relative ones.
    raw = Path(db_path) if db_path is not None else None
    path = raw.resolve() if raw is not None and raw.is_absolute() else resolve_db_path(raw)
    if not path.is_file():
        raise FileNotFoundError(f"DB bulunamadı: {path}")
    hours = _clamp(int(hours), 1, 24 * 7)
    bucket_minutes = _clamp(int(bucket_minutes), 1, 240)
    limit = _clamp(int(limit), 1, MAX_LIMIT)
    bucket_s = bucket_minutes * 60

    now = int(time.time())
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN")
        latest = conn.execute("SELECT MAX(created_at) FROM decisions").fetchone()[0]
        # Anchor the window to the newest record so an idle worker still shows its last session.
        end = max(int(latest or now), 0)
        end = end - end % bucket_s + bucket_s
        start = end - hours * 3600

        timeline_rows = conn.execute(
            f"""
            SELECT (created_at / ?) * ? AS bucket, {EFFECTIVE_STATUS} AS st, COUNT(*) AS c
            FROM decisions WHERE created_at >= ? AND created_at < ?
            GROUP BY bucket, st ORDER BY bucket
            """,
            (bucket_s, bucket_s, start, end),
        ).fetchall()

        rules = conn.execute(
            f"""
            SELECT rule, {EFFECTIVE_STATUS} AS st, COUNT(*) AS c
            FROM decisions GROUP BY rule, st ORDER BY c DESC
            """
        ).fetchall()

        symbols = conn.execute(
            f"""
            SELECT symbol, {EFFECTIVE_STATUS} AS st, COUNT(*) AS c
            FROM decisions GROUP BY symbol, st
            """
        ).fetchall()

        outcomes = conn.execute(
            f"""
            SELECT {EFFECTIVE_CATEGORY} AS category, se.horizon_minutes AS horizon, se.pnl_usdt
            FROM shadow_evaluations se JOIN shadow_trades st ON st.id = se.shadow_id
            WHERE se.status = 'COMPLETE' AND se.pnl_usdt IS NOT NULL
            """
        ).fetchall()

        decisions = conn.execute(
            f"""
            SELECT id, symbol, signal_action, signal_reason, signal_origin,
                   status AS raw_status, {EFFECTIVE_STATUS} AS status, rule, explanation,
                   notional_usdt, market_source, ref_id, created_at, rules_version
            FROM decisions ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

        shadow = conn.execute(
            f"""
            SELECT st.id AS shadow_id, st.symbol, st.category AS raw_category,
                   {EFFECTIVE_CATEGORY} AS category, st.constitution_rule AS rule,
                   st.entry_ask, st.notional_usdt, st.reason, st.source AS entry_source,
                   st.created_at, se.horizon_minutes, se.status, se.exit_bid, se.pnl_usdt,
                   se.evaluated_at, se.note, se.feed_source,
                   COALESCE((SELECT GROUP_CONCAT(DISTINCT d.signal_origin) FROM decisions d
                       WHERE d.ref_id=st.id AND d.status IN ('SHADOW_RISK','SHADOW_PASS','TECHNICAL_BLOCK')
                         AND d.symbol=st.symbol), 'UNKNOWN') AS signal_origin,
                   CASE WHEN se.horizon_minutes=15 THEN st.target_15_at ELSE st.target_60_at END AS target_at
            FROM shadow_evaluations se JOIN shadow_trades st ON st.id = se.shadow_id
            ORDER BY st.id DESC, se.horizon_minutes ASC LIMIT ?
            """,
            (limit * 2,),
        ).fetchall()
    finally:
        conn.close()

    buckets: dict[int, dict[str, int]] = {
        t: {} for t in range(start, end, bucket_s)
    }
    for row in timeline_rows:
        slot = buckets.setdefault(int(row["bucket"]), {})
        slot[str(row["st"])] = int(row["c"])

    rule_map: dict[str, dict] = {}
    for row in rules:
        entry = rule_map.setdefault(str(row["rule"]), {"rule": str(row["rule"]), "total": 0, "by_status": {}})
        entry["by_status"][str(row["st"])] = int(row["c"])
        entry["total"] += int(row["c"])

    symbol_map: dict[str, dict] = {}
    for row in symbols:
        entry = symbol_map.setdefault(str(row["symbol"]), {"symbol": str(row["symbol"]), "total": 0, "by_status": {}})
        entry["by_status"][str(row["st"])] = int(row["c"])
        entry["total"] += int(row["c"])

    groups: dict[tuple[str, int], list[Decimal]] = {}
    for row in outcomes:
        value = _dec(row["pnl_usdt"])
        if value is not None:
            groups.setdefault((str(row["category"]), int(row["horizon"])), []).append(value)
    outcome_list = []
    for (category, horizon), values in sorted(groups.items()):
        total = sum(values, Decimal(0))
        outcome_list.append(
            {
                "category": category,
                "horizon_minutes": horizon,
                "count": len(values),
                "positive": sum(1 for v in values if v > 0),
                "negative": sum(1 for v in values if v < 0),
                "sum_pnl_usdt": str(total),
                "avg_pnl_usdt": str(total / len(values)),
                "min_pnl_usdt": str(min(values)),
                "max_pnl_usdt": str(max(values)),
            }
        )

    shadow_rows = [dict(r) for r in shadow]
    for row in shadow_rows:
        if row["status"] == "COMPLETE" and "stop_dogrulamasi_sinirli" not in (row["note"] or ""):
            row["note"] = "; ".join(filter(None, [row["note"], "Eski kayıt: stop doğrulaması belgelenmedi"]))

    return {
        "generated_at": now,
        "window": {"start": start, "end": end, "hours": hours, "bucket_minutes": bucket_minutes},
        "timeline": [{"t": t, "counts": counts} for t, counts in sorted(buckets.items())],
        "rules": sorted(rule_map.values(), key=lambda r: -r["total"]),
        "symbols": sorted(symbol_map.values(), key=lambda r: -r["total"]),
        "outcomes": outcome_list,
        "decisions": [dict(r) for r in decisions],
        "shadow": shadow_rows,
        "notes": [
            "Aggregates include all data sources; technical categories remain separate from risk.",
            "Counterfactual PnL is an observation, not a verified avoided loss.",
            "Legacy OBSERVATION/MIN_ORDER risk rows are shown as technical.",
        ],
    }
