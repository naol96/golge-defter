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
                VALUES (1, '100', '0', '');

                CREATE TABLE IF NOT EXISTS paper_state_meta (
                  id INTEGER PRIMARY KEY CHECK (id = 1),
                  day_start_balance_usdt TEXT NOT NULL DEFAULT '100',
                  day_start_day TEXT NOT NULL DEFAULT ''
                );
                INSERT OR IGNORE INTO paper_state_meta (id, day_start_balance_usdt, day_start_day)
                VALUES (1, '100', '');

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
                  feed_source TEXT DEFAULT '',
                  PRIMARY KEY (shadow_id, horizon_minutes),
                  FOREIGN KEY (shadow_id) REFERENCES shadow_trades(id)
                );

                CREATE TABLE IF NOT EXISTS decisions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  symbol TEXT NOT NULL,
                  signal_action TEXT NOT NULL,
                  signal_reason TEXT NOT NULL,
                  signal_origin TEXT NOT NULL,
                  status TEXT NOT NULL,
                  rule TEXT NOT NULL,
                  explanation TEXT NOT NULL,
                  notional_usdt TEXT NOT NULL,
                  market_source TEXT NOT NULL,
                  ref_id INTEGER,
                  created_at INTEGER NOT NULL
                );

                CREATE VIEW IF NOT EXISTS paper_positions AS
                SELECT * FROM positions;
                """
            )
            self._ensure_column(conn, "shadow_evaluations", "feed_source", "TEXT DEFAULT ''")
            self._ensure_column(conn, "decisions", "rules_version", "TEXT DEFAULT ''")
            self._ensure_column(conn, "positions", "market_source", "TEXT NOT NULL DEFAULT ''")
            # Recover provenance for old positions only from an unambiguous decision.
            conn.execute("""
                UPDATE positions SET market_source = (
                    SELECT MIN(d.market_source) FROM decisions d
                    WHERE d.status='APPROVED_PAPER' AND d.ref_id=positions.id
                      AND d.symbol=positions.symbol
                    HAVING COUNT(DISTINCT d.market_source)=1
                )
                WHERE market_source='' AND EXISTS (
                    SELECT 1 FROM decisions d WHERE d.status='APPROVED_PAPER'
                      AND d.ref_id=positions.id AND d.symbol=positions.symbol
                    GROUP BY d.ref_id HAVING COUNT(DISTINCT d.market_source)=1
                )
            """)

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, decl: str) -> None:
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")

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

    def get_day_start_balance(self, utc_day: str) -> Decimal:
        with self.session() as conn:
            row = conn.execute(
                "SELECT day_start_balance_usdt, day_start_day FROM paper_state_meta WHERE id = 1"
            ).fetchone()
            if row is None:
                bal = conn.execute("SELECT balance_usdt FROM paper_state WHERE id = 1").fetchone()
                return Decimal(str(bal["balance_usdt"]))
            if row["day_start_day"] != utc_day:
                bal = conn.execute("SELECT balance_usdt FROM paper_state WHERE id = 1").fetchone()
                balance = Decimal(str(bal["balance_usdt"]))
                conn.execute(
                    "UPDATE paper_state_meta SET day_start_balance_usdt = ?, day_start_day = ? WHERE id = 1",
                    (str(balance), utc_day),
                )
                return balance
            return Decimal(str(row["day_start_balance_usdt"]))

    def get_open_portfolio(self) -> tuple[int, Decimal]:
        with self.session() as conn:
            rows = conn.execute(
                "SELECT notional_usdt FROM positions WHERE status = 'OPEN'"
            ).fetchall()
        exposure = Decimal("0")
        for row in rows:
            exposure += Decimal(str(row["notional_usdt"]))
        return len(rows), exposure

    def get_last_close_at(self, symbol: str) -> int | None:
        with self.session() as conn:
            row = conn.execute(
                "SELECT MAX(closed_at) AS ts FROM positions WHERE symbol = ? AND status = 'CLOSED'",
                (symbol,),
            ).fetchone()
        if row is None or row["ts"] is None:
            return None
        return int(row["ts"])

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

    def insert_decision(
        self,
        *,
        symbol: str,
        signal_action: str,
        signal_reason: str,
        signal_origin: str,
        status: str,
        rule: str,
        explanation: str,
        notional_usdt: Decimal,
        market_source: str,
        ref_id: int | None,
        created_at: int,
        rules_version: str = "",
    ) -> int:
        with self.session() as conn:
            cur = conn.execute(
                """
                INSERT INTO decisions
                (symbol, signal_action, signal_reason, signal_origin, status, rule,
                 explanation, notional_usdt, market_source, ref_id, created_at, rules_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    signal_action,
                    signal_reason,
                    signal_origin,
                    status,
                    rule,
                    explanation,
                    str(notional_usdt),
                    market_source,
                    ref_id,
                    created_at,
                    rules_version,
                ),
            )
            return int(cur.lastrowid)
