"""Shared data contracts for Shadow Ledger MVP."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal

D = Decimal

AllowedAction = Literal["BUY", "PASS"]
TradingMode = Literal["PAPER", "LIVE"]
DataSource = Literal[
    "ATK",
    "ATK_LIVE_MARKET",
    "MOCK",
    "FIXTURE",
    "FIXTURE_SYNTHETIC_NOT_LIVE",
]


class ShadowCategory(str, Enum):
    CONSTITUTIONAL_RISK_BLOCK = "CONSTITUTIONAL_RISK_BLOCK"
    PASS_OBSERVATION = "PASS_OBSERVATION"
    TECHNICAL_UNEXECUTABLE = "TECHNICAL_UNEXECUTABLE"


@dataclass(frozen=True)
class ConstitutionRules:
    max_position_fraction: Decimal = D("0.25")
    allowed_pairs: frozenset[str] = frozenset({"AVAX-USDT", "BTC-USDT", "ETH-USDT"})
    max_spread_fraction: Decimal = D("0.0015")
    stop_loss_fraction: Decimal = D("0.025")
    max_daily_realized_loss_fraction: Decimal = D("0.05")
    max_daily_realized_loss_usdt: Decimal = D("5")  # legacy fallback when day start unknown
    max_open_positions: int = 2
    max_total_exposure_fraction: Decimal = D("0.50")
    pair_cooldown_seconds: int = 15 * 60
    observation_min_balance_usdt: Decimal = D("40")
    max_data_age_seconds: int = 10
    rules_version: str = "rules_v2"


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    bid: Decimal
    ask: Decimal
    captured_at: int  # UTC epoch seconds
    source: DataSource = "MOCK"
    min_order_usdt: Decimal = D("10")


@dataclass(frozen=True)
class AnalystSignal:
    symbol: str
    action: AllowedAction
    reason: str
    origin: Literal["LLM", "DEMO"] = "DEMO"


@dataclass(frozen=True)
class DecisionResult:
    status: Literal[
        "APPROVED_PAPER",
        "SHADOW_RISK",
        "SHADOW_PASS",
        "TECHNICAL_BLOCK",
        "NO_DECISION",
        "LIVE_REJECTED",
    ]
    rule: str
    explanation: str
    notional_usdt: Decimal
    spread_fraction: Decimal | None
    shadow_category: ShadowCategory | None = None


@dataclass(frozen=True)
class Position:
    id: int
    symbol: str
    entry_price: Decimal
    notional_usdt: Decimal
    quantity: Decimal
    stop_loss_price: Decimal
    opened_at: int
    mode: TradingMode = "PAPER"
    status: Literal["OPEN", "CLOSED"] = "OPEN"


@dataclass(frozen=True)
class ExecutedTrade:
    position_id: int
    symbol: str
    side: Literal["BUY", "SELL"]
    price: Decimal
    notional_usdt: Decimal
    fee_usdt: Decimal
    executed_at: int
    mode: TradingMode = "PAPER"


@dataclass(frozen=True)
class ShadowTrade:
    id: int
    symbol: str
    category: ShadowCategory
    entry_ask: Decimal
    notional_usdt: Decimal
    reason: str
    constitution_rule: str
    created_at: int
    source: DataSource


@dataclass(frozen=True)
class ShadowEvaluation:
    shadow_id: int
    horizon_minutes: Literal[15, 60]
    status: Literal["PENDING", "COMPLETE", "STOP_VERIFICATION_LIMITED"]
    exit_bid: Decimal | None
    pnl_usdt: Decimal | None
    evaluated_at: int | None
    note: str = ""
