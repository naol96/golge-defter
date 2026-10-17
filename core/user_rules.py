"""Natural-language user requests mapped to deterministic constitution tweaks."""
from __future__ import annotations

import re
from decimal import Decimal

from contracts.models import ConstitutionRules
from core.constitution import tighten_position_limit, tighten_spread_limit

_PCT_RE = re.compile(r"(%\s*)?(\d+(?:[.,]\d+)?)\s*(%|yüzde|percent)?", re.I)
_SPREAD_HINT = re.compile(r"makas|spread", re.I)


def _parse_percent(text: str) -> Decimal | None:
    match = _PCT_RE.search(text)
    if not match:
        return None
    raw = match.group(2).replace(",", ".")
    pct = Decimal(raw)
    if pct > 1:
        pct = pct / Decimal(100)
    return pct


def _parse_spread_fraction(text: str) -> Decimal | None:
    match = _PCT_RE.search(text)
    if not match:
        return None
    raw = match.group(2).replace(",", ".")
    return Decimal(raw) / Decimal(100)


def apply_user_request(
    rules: ConstitutionRules, text: str
) -> tuple[ConstitutionRules, str, str]:
    """Return (effective_rules, user_request_label, applied_message)."""
    label = text.strip()
    if not label:
        return rules, "", "Boş talep; sert sınırlar korundu."

    if _SPREAD_HINT.search(label):
        spread_frac = _parse_spread_fraction(label)
        if spread_frac is not None:
            new_rules, msg = tighten_spread_limit(rules, spread_frac)
            return new_rules, label, msg

    pct = _parse_percent(label)
    if pct is not None:
        new_rules, msg = tighten_position_limit(rules, pct)
        return new_rules, label, msg

    return rules, label, "Doğal dil talebi tanınmadı; sert sınırlar korundu."
