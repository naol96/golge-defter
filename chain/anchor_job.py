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
        SELECT *
        FROM decisions ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_manifest(db_path: Path, limit: int = 200, label: str = "golge_batch") -> dict:
    if limit <= 0:
        raise ValueError("batch limit must be positive")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        conn.execute("BEGIN")
        digest = _decision_digest(conn, limit)
        total = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    finally:
        conn.close()
    return {
        "label": label,
        "db": str(db_path.resolve()),
        "decision_count": min(total, limit),
        "total_decision_count": total,
        "batch_limit": limit,
        "sha256": digest,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fuji_contract": os.environ.get("FUJI_ANCHOR_CONTRACT", ""),
        "snowtrace_tx": os.environ.get("FUJI_LAST_TX", ""),
        "proof_kind": "LOCAL_SHA256",
        "blockchain_verified": False,
        "note": "Local decision-batch SHA-256 only. Any supplied chain URL is unverified; no receipt/hash verification is implemented.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gölge Defter anchor manifest")
    parser.add_argument("--db", default="data/golge.db")
    parser.add_argument("--out", default="evidence/anchor_manifest.json")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--label", default="golge_batch")
    args = parser.parse_args()

    manifest = build_manifest(Path(args.db), args.limit, args.label)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
