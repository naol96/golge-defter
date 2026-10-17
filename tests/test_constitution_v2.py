from decimal import Decimal as D

from golge_defter.risk import AnalystSignal, Constitution, MarketSnapshot, evaluate

NOW = 1_800_000_000


def _buy(**kwargs):
    defaults = {
        "pair": "AVAX-USDT",
        "balance": "80",
        "min_order": "10",
        "bid": "24.99",
        "ask": "25",
        "age": 0,
        "daily_loss": "0",
        "day_start": "80",
        "open_count": 0,
        "exposure": "0",
        "last_close": None,
    }
    defaults.update(kwargs)
    return evaluate(
        constitution=Constitution(),
        signal=AnalystSignal(defaults["pair"], "BUY", "test"),
        market=MarketSnapshot(
            defaults["pair"], D(defaults["bid"]), D(defaults["ask"]), NOW - defaults["age"]
        ),
        available_usdt=D(defaults["balance"]),
        min_order_usdt=D(defaults["min_order"]),
        daily_realized_loss_usdt=D(defaults["daily_loss"]),
        now=NOW,
        open_position_count=defaults["open_count"],
        open_exposure_usdt=D(defaults["exposure"]),
        last_pair_close_at=defaults["last_close"],
        day_start_balance_usdt=D(defaults["day_start"]),
    )


def test_max_two_open_positions():
    d = _buy(open_count=2)
    assert d.status == "SHADOW_RISK"
    assert d.rule == "MAX_POSITIONS"


def test_exposure_cap_blocks_third_slice():
    d = _buy(balance="80", exposure="30")
    assert d.status == "SHADOW_RISK"
    assert d.rule == "EXPOSURE"


def test_pair_cooldown():
    d = _buy(last_close=NOW - 60)
    assert d.rule == "COOLDOWN"


def test_daily_loss_uses_percent_of_day_start():
    d = _buy(day_start="50", daily_loss="2.5")
    assert d.rule == "DAILY_LOSS"


def test_sub_40_minimum_is_technical_not_risk():
    d = _buy(balance="35", day_start="35")
    assert d.rule == "MIN_ORDER"
    assert d.status == "TECHNICAL_BLOCK"


def test_technical_min_order_when_balance_above_observation_threshold():
    d = _buy(balance="50", min_order="15", day_start="50")
    assert d.status == "TECHNICAL_BLOCK"
    assert d.rule == "MIN_ORDER"
