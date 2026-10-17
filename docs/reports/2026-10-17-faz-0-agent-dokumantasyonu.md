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

## Test sonuçları

| Komut | Sonuç |
| --- | --- |
| `pytest -q` | PASS (12 test) |
| `python -m golge_defter.demo` | Değişiklik yok |

## Sonraki faz

- **FAZ-B:** OKX ATK piyasa adaptörü (`01-piyasa-adaptor.md`)
