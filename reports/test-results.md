# Test results

Komut: `PYTHONPATH=. .venv/bin/pytest -q -n auto`

Sonuç: **17 passed** (2026-10-17)

## Zorunlu 6 test (test_risk.py)

| # | Senaryo | Test | Sonuç |
|---|---------|------|--------|
| 1 | %25 tavan 30 USDT → 7.5 | `test_min_order_is_technical_not_risk` | PASS |
| 2 | %80 reddet, %15 sıkılaştır | `test_user_cannot_loosen_cap`, `test_user_can_tighten_cap` | PASS |
| 3 | Min emir TECHNICAL | `test_min_order_is_technical_not_risk` | PASS |
| 4 | Bayat veri | `test_stale_data_refused` | PASS |
| 5 | Günlük zarar | `test_at_loss_limit_new_buy_blocked` | PASS |
| 6 | Idempotent gölge | `test_idempotent_shadow_evaluation` | PASS |
