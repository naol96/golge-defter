"""Deterministic pre-trade checks. No API / network / LIVE order side effects.

All monetary values are Decimal. Spread and limits are fractions (0.0015 = 0.15%).
"""
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Literal

D = Decimal
AllowedDirection = Literal["BUY", "PASS"]


@dataclass(frozen=True)
class Constitution:
    max_position_fraction: Decimal = D("0.25")
    allowed_pairs: frozenset[str] = frozenset({"AVAX-USDT", "BTC-USDT", "ETH-USDT"})
    max_spread_fraction: Decimal = D("0.0015")
    stop_loss_fraction: Decimal = D("0.025")
    max_daily_realized_loss_usdt: Decimal = D("5")
    max_data_age_seconds: int = 10


@dataclass(frozen=True)
class MarketSnapshot:
    pair: str
    bid: Decimal
    ask: Decimal
    captured_at: int  # UTC Unix epoch seconds; mock timestamps still require explicit labels


@dataclass(frozen=True)
class AnalystSignal:
    pair: str
    direction: AllowedDirection
    reason: str


@dataclass(frozen=True)
class Decision:
    status: Literal["APPROVED_PAPER", "SHADOW_RISK", "SHADOW_PASS", "TECHNICAL_BLOCK", "NO_DECISION"]
    rule: str
    explanation: str
    constitutional_amount_usdt: Decimal
    spread_fraction: Decimal | None


def _number(value: Decimal, name: str) -> Decimal:
    try:
        result = D(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{name}: invalid decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{name}: must be finite")
    return result


def tighten_position_limit(constitution: Constitution, requested_fraction: Decimal) -> tuple[Constitution, str]:
    """Never expand the active maximum. Return an explicit reason on rejected loosening."""
    fraction = _number(requested_fraction, "requested_fraction")
    if fraction <= 0 or fraction > 1:
        return constitution, "Geçersiz oran; mevcut güvenlik tavanı korundu."
    if fraction > constitution.max_position_fraction:
        return constitution, (f"Talep %{fraction * 100:g} mevcut sert sınırı aşıyor; "
                              f"etkin tavan %{constitution.max_position_fraction * 100:g} olarak korundu.")
    return replace(constitution, max_position_fraction=fraction), f"Tavan %{fraction * 100:g} olarak sıkılaştırıldı."


def evaluate(*, constitution: Constitution, signal: AnalystSignal, market: MarketSnapshot,
             available_usdt: Decimal, min_order_usdt: Decimal,
             daily_realized_loss_usdt: Decimal, now: int) -> Decision:
    """Fail-closed. Only APPROVED_PAPER is eligible for a simulated execution.

    PASS still receives a deterministic hypothetical amount for shadow records.
    Market data must be fresh and internally consistent before any observation.
    """
    balance = _number(available_usdt, "available_usdt")
    minimum = _number(min_order_usdt, "min_order_usdt")
    daily_loss = _number(daily_realized_loss_usdt, "daily_realized_loss_usdt")
    if balance < 0 or minimum <= 0 or daily_loss < 0:
        raise ValueError("negative balances/losses or nonpositive minimum are invalid")
    amount = balance * constitution.max_position_fraction
    nil = Decision("NO_DECISION", "DATA", "Güvenilir piyasa verisi olmadan karar verilmedi.", amount, None)
    if not isinstance(now, int) or not isinstance(market.captured_at, int):
        return nil
    if market.captured_at > now or now - market.captured_at > constitution.max_data_age_seconds:
        return replace(nil, explanation="Bayat veya gelecek tarihli fiyat verisi; emir ve PnL kapalı.")
    bid, ask = _number(market.bid, "bid"), _number(market.ask, "ask")
    if bid <= 0 or ask <= 0 or bid > ask or signal.pair != market.pair:
        return replace(nil, explanation="Tutarsız fiyat veya sinyal paritesi; karar verilmedi.")
    spread = (ask - bid) / ask
    if signal.direction not in ("BUY", "PASS"):
        return Decision("NO_DECISION", "SIGNAL", "Desteklenmeyen sinyal; yalnızca BUY/PASS.", amount, spread)
    if signal.direction == "PASS":
        return Decision("SHADOW_PASS", "ANALYST", "Analist PAS önerdi; alım yapılmadı.", amount, spread)
    if signal.pair not in constitution.allowed_pairs:
        return Decision("SHADOW_RISK", "PAIR", "Parite Anayasa izinli listesinde değil.", amount, spread)
    if daily_loss >= constitution.max_daily_realized_loss_usdt:
        return Decision("SHADOW_RISK", "DAILY_LOSS", "Günlük gerçekleşmiş zarar limiti doldu.", amount, spread)
    # This is an exchange-executability issue, not 'capital saved by the constitution'.
    if amount < minimum:
        return Decision("TECHNICAL_BLOCK", "MIN_ORDER", "Anayasal tutar borsa minimum emrinin altında.", amount, spread)
    if spread > constitution.max_spread_fraction:
        return Decision("SHADOW_RISK", "SPREAD", "Spread anayasal eşiği aşıyor.", amount, spread)
    return Decision("APPROVED_PAPER", "OK", "Sadece PAPER icraya uygun (LIVE desteklenmiyor).", amount, spread)
