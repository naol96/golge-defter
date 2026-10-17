#!/usr/bin/env python3
"""Decision-batch hash manifest for Fuji anchoring (Plan B: local manifest + optional RPC)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _decision_digest(conn: sqlite3.Connection, limit: int) -> str:
    rows = conn.execute(
        """
        SELECT id, symbol, status, rule, market_source, created_at
        FROM decisions ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gölge Defter anchor manifest")
    parser.add_argument("--db", default="data/golge.db")
    parser.add_argument("--out", default="evidence/anchor_manifest.json")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--label", default="golge_batch")
    args = parser.parse_args()

    db_path = Path(args.db)
    conn = sqlite3.connect(db_path)
    try:
        digest = _decision_digest(conn, args.limit)
        count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    finally:
        conn.close()

    manifest = {
        "label": args.label,
        "db": str(db_path.resolve()),
        "decision_count": count,
        "batch_limit": args.limit,
        "sha256": digest,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fuji_contract": os.environ.get("FUJI_ANCHOR_CONTRACT", ""),
        "snowtrace_tx": os.environ.get("FUJI_LAST_TX", ""),
        "note": "Set FUJI_* env after on-chain anchor; worker DB is read-only here.",
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
