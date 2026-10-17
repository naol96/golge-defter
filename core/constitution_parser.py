"""Natural-language tightening requests (deterministic, no code execution)."""
from __future__ import annotations

from contracts.models import ConstitutionRules
from core.user_rules import apply_user_request


def apply_user_cap_request(rules: ConstitutionRules, text: str) -> tuple[ConstitutionRules, str, str]:
    """Backward-compatible alias for position-cap phrasing."""
    return apply_user_request(rules, text)
