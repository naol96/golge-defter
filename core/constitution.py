"""Deterministic constitution checks (no network, no LIVE orders)."""
from decimal import Decimal, InvalidOperation
from typing import Literal

from contracts.models import (
    AnalystSignal,
    ConstitutionRules,
    DecisionResult,
    MarketSnapshot,
    ShadowCategory,
)

D = Decimal

Constitution = ConstitutionRules


def _number(value: Decimal, name: str) -> Decimal:
    try:
        result = D(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{name}: invalid decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{name}: must be finite")
    return result


def _daily_loss_limit(constitution: ConstitutionRules, day_start_balance_usdt: Decimal | None) -> Decimal:
    if day_start_balance_usdt is not None:
        base = _number(day_start_balance_usdt, "day_start_balance_usdt")
        return base * constitution.max_daily_realized_loss_fraction
    return _number(constitution.max_daily_realized_loss_usdt, "max_daily_realized_loss_usdt")


def tighten_position_limit(
    constitution: ConstitutionRules, requested_fraction: Decimal
) -> tuple[ConstitutionRules, str]:
    from dataclasses import replace

    fraction = _number(requested_fraction, "requested_fraction")
    if fraction <= 0 or fraction > 1:
        return constitution, "Geçersiz oran; mevcut güvenlik tavanı korundu."
    if fraction > constitution.max_position_fraction:
        return constitution, (
            f"Talep %{fraction * 100:g} mevcut sert sınırı aşıyor; "
            f"etkin tavan %{constitution.max_position_fraction * 100:g} olarak korundu."
        )
    return replace(constitution, max_position_fraction=fraction), (
        f"Tavan %{fraction * 100:g} olarak sıkılaştırıldı."
    )


def tighten_spread_limit(
    constitution: ConstitutionRules, requested_fraction: Decimal
) -> tuple[ConstitutionRules, str]:
    from dataclasses import replace

    fraction = _number(requested_fraction, "requested_fraction")
    if fraction <= 0 or fraction > 1:
        return constitution, "Geçersiz makas oranı; mevcut makas tavanı korundu."
    if fraction > constitution.max_spread_fraction:
        return constitution, (
            f"Talep %{fraction * 100:g} mevcut makas tavanından gevşek; "
            f"etkin tavan %{constitution.max_spread_fraction * 100:g} korundu."
        )
    return replace(constitution, max_spread_fraction=fraction), (
        f"Makas tavanı %{fraction * 100:g} olarak sıkılaştırıldı."
    )


def evaluate(
    *,
    constitution: ConstitutionRules,
    signal: AnalystSignal,
    market: MarketSnapshot,
    available_usdt: Decimal,
    min_order_usdt: Decimal,
    daily_realized_loss_usdt: Decimal,
    now: int,
    mode: Literal["PAPER", "LIVE"] = "PAPER",
    open_position_count: int = 0,
    open_exposure_usdt: Decimal = D("0"),
    last_pair_close_at: int | None = None,
    day_start_balance_usdt: Decimal | None = None,
) -> DecisionResult:
    if mode == "LIVE":
        return DecisionResult(
            "LIVE_REJECTED",
            "MODE",
            "LIVE modu MVP kapsamında devre dışı.",
            D("0"),
            None,
            None,
        )

    balance = _number(available_usdt, "available_usdt")
    minimum = _number(min_order_usdt, "min_order_usdt")
    daily_loss = _number(daily_realized_loss_usdt, "daily_realized_loss_usdt")
    exposure = _number(open_exposure_usdt, "open_exposure_usdt")
    if balance < 0 or minimum <= 0 or daily_loss < 0 or exposure < 0:
        raise ValueError("negative balances/losses or nonpositive minimum are invalid")
    if open_position_count < 0:
        raise ValueError("open_position_count must be nonnegative")

    amount = balance * constitution.max_position_fraction
    nil = DecisionResult(
        "NO_DECISION",
        "DATA",
        "Güvenilir piyasa verisi olmadan karar verilmedi.",
        amount,
        None,
        None,
    )
    if not isinstance(now, int) or not isinstance(market.captured_at, int):
        return nil
    if market.captured_at > now or now - market.captured_at > constitution.max_data_age_seconds:
        return DecisionResult(
            "NO_DECISION",
            "DATA",
            "Bayat veya gelecek tarihli fiyat verisi; emir ve PnL kapalı.",
            amount,
            None,
            None,
        )

    bid, ask = _number(market.bid, "bid"), _number(market.ask, "ask")
    pair = signal.symbol
    if bid <= 0 or ask <= 0 or bid > ask or pair != market.symbol:
        return DecisionResult(
            "NO_DECISION",
            "DATA",
            "Tutarsız fiyat veya sinyal paritesi; karar verilmedi.",
            amount,
            None,
            None,
        )

    spread = (ask - bid) / ask
    if signal.action not in ("BUY", "PASS"):
        return DecisionResult(
            "NO_DECISION",
            "SIGNAL",
            "Desteklenmeyen sinyal; yalnızca BUY/PASS.",
            amount,
            spread,
            None,
        )

    if signal.action == "PASS":
        return DecisionResult(
            "SHADOW_PASS",
            "ANALYST",
            "Analist PAS önerdi; alım yapılmadı.",
            amount,
            spread,
            ShadowCategory.PASS_OBSERVATION,
        )

    if pair not in constitution.allowed_pairs:
        return DecisionResult(
            "SHADOW_RISK",
            "PAIR",
            "Parite Anayasa izinli listesinde değil.",
            amount,
            spread,
            ShadowCategory.CONSTITUTIONAL_RISK_BLOCK,
        )

    loss_limit = _daily_loss_limit(constitution, day_start_balance_usdt)
    if daily_loss >= loss_limit:
        return DecisionResult(
            "SHADOW_RISK",
            "DAILY_LOSS",
            "Günlük gerçekleşmiş zarar limiti doldu.",
            amount,
            spread,
            ShadowCategory.CONSTITUTIONAL_RISK_BLOCK,
        )

    if last_pair_close_at is not None:
        elapsed = now - int(last_pair_close_at)
        if elapsed < constitution.pair_cooldown_seconds:
            return DecisionResult(
                "SHADOW_RISK",
                "COOLDOWN",
                "Parite bekleme süresi dolmadı; yeni alım yok.",
                amount,
                spread,
                ShadowCategory.CONSTITUTIONAL_RISK_BLOCK,
            )

    if balance < constitution.observation_min_balance_usdt and amount < minimum:
        return DecisionResult(
            "SHADOW_RISK",
            "OBSERVATION",
            "Bakiye gözlem eşiğinde; %25 tavan minimum emri karşılamıyor.",
            amount,
            spread,
            ShadowCategory.CONSTITUTIONAL_RISK_BLOCK,
        )

    if open_position_count >= constitution.max_open_positions:
        return DecisionResult(
            "SHADOW_RISK",
            "MAX_POSITIONS",
            "Açık pozisyon sayısı anayasal üst sınırda.",
            amount,
            spread,
            ShadowCategory.CONSTITUTIONAL_RISK_BLOCK,
        )

    max_exposure = balance * constitution.max_total_exposure_fraction
    if exposure + amount > max_exposure:
        return DecisionResult(
            "SHADOW_RISK",
            "EXPOSURE",
            "Toplam açık risk anayasal %50 tavanını aşar.",
            amount,
            spread,
            ShadowCategory.CONSTITUTIONAL_RISK_BLOCK,
        )

    if spread > constitution.max_spread_fraction:
        return DecisionResult(
            "SHADOW_RISK",
            "SPREAD",
            "Spread anayasal eşiği aşıyor.",
            amount,
            spread,
            ShadowCategory.CONSTITUTIONAL_RISK_BLOCK,
        )

    if amount < minimum:
        return DecisionResult(
            "TECHNICAL_BLOCK",
            "MIN_ORDER",
            "Anayasal tutar borsa minimum emrinin altında.",
            amount,
            spread,
            ShadowCategory.TECHNICAL_UNEXECUTABLE,
        )

    return DecisionResult(
        "APPROVED_PAPER",
        "OK",
        "Sadece PAPER icraya uygun (LIVE desteklenmiyor).",
        amount,
        spread,
        None,
    )


Decision = DecisionResult
