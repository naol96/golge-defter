from decimal import Decimal as D

from contracts.models import ConstitutionRules
from core.user_rules import apply_user_request


def test_spread_tighten_from_percent_points():
    rules, _, msg = apply_user_request(
        ConstitutionRules(), "Makas en fazla %0.03 olsun"
    )
    assert rules.max_spread_fraction == D("0.0003")
    assert "sıkılaştır" in msg.lower()


def test_position_cap_rejects_above_hard_limit():
    rules, _, msg = apply_user_request(
        ConstitutionRules(), "Bakiyemin %80'i ile al"
    )
    assert rules.max_position_fraction == D("0.25")
    assert "korundu" in msg


def test_position_cap_can_tighten_below_hard_limit():
    rules, _, _ = apply_user_request(ConstitutionRules(), "Tek işlem tavanı %15")
    assert rules.max_position_fraction == D("0.15")
