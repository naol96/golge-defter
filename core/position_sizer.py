from decimal import Decimal

from contracts.models import ConstitutionRules


def position_notional_usdt(balance_usdt: Decimal, rules: ConstitutionRules) -> Decimal:
    return balance_usdt * rules.max_position_fraction

