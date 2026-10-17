from decimal import Decimal as D

from core.min_order import min_notional_usdt


def test_min_notional_from_min_sz_and_ask():
    assert min_notional_usdt(D("25"), D("0.1")) == D("2.5000")


def test_min_notional_respects_lot_step():
    n = min_notional_usdt(D("100"), D("0.00001"), lot_sz_base=D("0.00000001"))
    assert n == D("0.0010")
