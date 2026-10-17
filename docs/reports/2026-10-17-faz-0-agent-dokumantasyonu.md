# Faz raporu — FAZ-0: Agent dokümantasyonu

- **Tarih:** 2026-10-17
- **Rol:** `docs/agents/00-orkestrator.md` (plan) + tüm rol şablonları
- **Roadmap maddesi:** Hazır — proje tanıtımı ve belgeler (genişletme)
- **Ajan(lar):** Jcode

## Hedef

Depoda çalışacak ajanlar için minimal rol rehberleri, ortak disiplin ve faz rapor akışı tanımlamak.

## Yapılan değişiklikler

| Dosya | Özet |
| --- | --- |
| `AGENTS.md` | Giriş noktası ve rol indeksi |
| `docs/agents/README.md` | Ortak kurallar, paralel test, yasaklar |
| `docs/agents/00-06-*.md` | Orkestratör + 6 katman rolü |
| `docs/agents/faz-raporu-sablonu.md` | Faz sonu rapor şablonu |
| `docs/reports/.gitkeep` | Rapor dizini |
| `README.md` | Dosya listesine agent belgeleri eklendi |

```bash
git show --stat fd6c12c | tail -n +2
# 13 files changed, 436 insertions(+)
```

## Test sonuçları

| Komut | Sonuç |
| --- | --- |
| `pytest -q -n auto` | PASS (12) — `pytest-xdist` dev bağımlılığı ile |
| `python -m golge_defter.demo` | PASS (smoke, kod değişmedi) |
| CI | bekliyor |

Paralel test notu: tek test dosyası (`test_risk.py`); `-n auto` gelecek fazlarda `test_market.py` ile birlikte koşturulacak.

## Sonraki faz

- **FAZ-B:** OKX ATK piyasa adaptörü (`01-piyasa-adaptor.md`)
