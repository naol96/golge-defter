"""Natural-language tightening requests (deterministic, no code execution)."""
from __future__ import annotations

import re
from decimal import Decimal

from contracts.models import ConstitutionRules
from core.constitution import tighten_position_limit

_PCT_RE = re.compile(r"(%\s*)?(\d+(?:[.,]\d+)?)\s*(%|yüzde|percent)?", re.I)


def apply_user_cap_request(rules: ConstitutionRules, text: str) -> tuple[ConstitutionRules, str, str]:
    """Return (effective_rules, user_request_label, applied_message)."""
    match = _PCT_RE.search(text)
    if not match:
        return rules, text.strip(), "Doğal dil talebi tanınmadı; sert sınırlar korundu."
    raw = match.group(2).replace(",", ".")
    pct = Decimal(raw)
    if pct > 1:
        pct = pct / Decimal(100)
    new_rules, msg = tighten_position_limit(rules, pct)
    return new_rules, text.strip(), msg

