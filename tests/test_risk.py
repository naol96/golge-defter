from decimal import Decimal as D
from golge_defter.risk import Constitution, MarketSnapshot, AnalystSignal, evaluate, tighten_position_limit

NOW = 1_800_000_000


def decision(*, pair="AVAX-USDT", direction="BUY", balance="80", min_order="10",
             bid="24.99", ask="25", age=0, daily_loss="0"):
    return evaluate(constitution=Constitution(),
                    signal=AnalystSignal(pair, direction, "Test sinyali"),
                    market=MarketSnapshot(pair, D(bid), D(ask), NOW-age),
                    available_usdt=D(balance), min_order_usdt=D(min_order),
                    daily_realized_loss_usdt=D(daily_loss), now=NOW)


def test_position_is_max_25_percent():
    d = decision(balance="80")
    assert d.constitutional_amount_usdt == D("20.00")
    assert d.status == "APPROVED_PAPER"


def test_user_cannot_loosen_cap():
    c, warning = tighten_position_limit(Constitution(), D("0.80"))
    assert c.max_position_fraction == D("0.25")
    assert "%80" in warning and "%25" in warning


def test_user_can_tighten_cap():
    c, _ = tighten_position_limit(Constitution(), D("0.15"))
    assert c.max_position_fraction == D("0.15")


def test_min_order_is_technical_not_risk():
    d = decision(balance="50", min_order="15")
    assert d.constitutional_amount_usdt == D("12.50")
    assert d.status == "TECHNICAL_BLOCK"


def test_stale_data_refused():
    assert decision(age=11).status == "NO_DECISION"


def test_at_loss_limit_new_buy_blocked():
    d = decision(daily_loss="5")
    assert d.status == "SHADOW_RISK"
    assert d.rule == "DAILY_LOSS"


def test_high_spread_is_risk_block():
    d = decision(bid="24", ask="25")
    assert d.status == "SHADOW_RISK"
    assert d.rule == "SPREAD"


def test_pass_has_reproducible_amount():
    d = decision(direction="PASS", balance="50")
    assert d.status == "SHADOW_PASS"
    assert d.constitutional_amount_usdt == D("12.50")


def test_pair_whitelist():
    assert decision(pair="DOGE-USDT").rule == "PAIR"


def test_future_price_refused():
    assert decision(age=-1).status == "NO_DECISION"


def test_negative_balance_not_accepted():
    try:
        decision(balance="-10")
    except ValueError:
        return
    assert False, "negative balance should be rejected"


def test_no_live_order_status():
    assert decision().status == "APPROVED_PAPER"
