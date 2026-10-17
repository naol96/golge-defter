"""SQLite persistence for paper trades and shadow ledger."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Iterator

from contracts.models import ShadowCategory

DEFAULT_DB = Path("data/golge.db")


class Database:
    def __init__(self, path: Path | str = DEFAULT_DB) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.session() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS paper_state (
                  id INTEGER PRIMARY KEY CHECK (id = 1),
                  balance_usdt TEXT NOT NULL,
                  daily_loss_usdt TEXT NOT NULL DEFAULT '0',
                  daily_loss_day TEXT NOT NULL
                );
                INSERT OR IGNORE INTO paper_state (id, balance_usdt, daily_loss_usdt, daily_loss_day)
                VALUES (1, '50', '0', '');

                CREATE TABLE IF NOT EXISTS positions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  symbol TEXT NOT NULL,
                  entry_price TEXT NOT NULL,
                  notional_usdt TEXT NOT NULL,
                  quantity TEXT NOT NULL,
                  stop_loss_price TEXT NOT NULL,
                  opened_at INTEGER NOT NULL,
                  closed_at INTEGER,
                  status TEXT NOT NULL DEFAULT 'OPEN',
                  mode TEXT NOT NULL DEFAULT 'PAPER',
                  close_reason TEXT
                );

                CREATE TABLE IF NOT EXISTS shadow_trades (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  symbol TEXT NOT NULL,
                  category TEXT NOT NULL,
                  entry_ask TEXT NOT NULL,
                  notional_usdt TEXT NOT NULL,
                  reason TEXT NOT NULL,
                  constitution_rule TEXT NOT NULL,
                  created_at INTEGER NOT NULL,
                  source TEXT NOT NULL,
                  target_15_at INTEGER NOT NULL,
                  target_60_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS shadow_evaluations (
                  shadow_id INTEGER NOT NULL,
                  horizon_minutes INTEGER NOT NULL CHECK (horizon_minutes IN (15, 60)),
                  status TEXT NOT NULL,
                  exit_bid TEXT,
                  pnl_usdt TEXT,
                  evaluated_at INTEGER,
                  note TEXT DEFAULT '',
                  PRIMARY KEY (shadow_id, horizon_minutes),
                  FOREIGN KEY (shadow_id) REFERENCES shadow_trades(id)
                );
                """
            )

    def get_paper_balance(self) -> Decimal:
        with self.session() as conn:
            row = conn.execute("SELECT balance_usdt FROM paper_state WHERE id = 1").fetchone()
            return Decimal(str(row["balance_usdt"]))

    def set_paper_balance(self, value: Decimal) -> None:
        with self.session() as conn:
            conn.execute(
                "UPDATE paper_state SET balance_usdt = ? WHERE id = 1",
                (str(value),),
            )

    def get_daily_loss(self, utc_day: str) -> Decimal:
        with self.session() as conn:
            row = conn.execute(
                "SELECT daily_loss_usdt, daily_loss_day FROM paper_state WHERE id = 1"
            ).fetchone()
            if row["daily_loss_day"] != utc_day:
                conn.execute(
                    "UPDATE paper_state SET daily_loss_usdt = '0', daily_loss_day = ? WHERE id = 1",
                    (utc_day,),
                )
                return Decimal("0")
            return Decimal(str(row["daily_loss_usdt"]))

    def add_daily_loss(self, utc_day: str, delta: Decimal) -> None:
        current = self.get_daily_loss(utc_day)
        with self.session() as conn:
            conn.execute(
                "UPDATE paper_state SET daily_loss_usdt = ?, daily_loss_day = ? WHERE id = 1",
                (str(current + delta), utc_day),
            )

    def insert_shadow(
        self,
        *,
        symbol: str,
        category: ShadowCategory,
        entry_ask: Decimal,
        notional_usdt: Decimal,
        reason: str,
        constitution_rule: str,
        created_at: int,
        source: str,
    ) -> int:
        target_15 = created_at + 15 * 60
        target_60 = created_at + 60 * 60
        with self.session() as conn:
            cur = conn.execute(
                """
                INSERT INTO shadow_trades
                (symbol, category, entry_ask, notional_usdt, reason, constitution_rule,
                 created_at, source, target_15_at, target_60_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    category.value,
                    str(entry_ask),
                    str(notional_usdt),
                    reason,
                    constitution_rule,
                    created_at,
                    source,
                    target_15,
                    target_60,
                ),
            )
            shadow_id = int(cur.lastrowid)
            for horizon in (15, 60):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO shadow_evaluations
                    (shadow_id, horizon_minutes, status)
                    VALUES (?, ?, 'PENDING')
                    """,
                    (shadow_id, horizon),
                )
            return shadow_id
