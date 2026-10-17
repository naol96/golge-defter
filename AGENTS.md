# Gölge Defter — Agent rehberi

Bu depoda çalışan tüm ajanlar **buradan** başlar.

## İlk okuma (sırayla, kısa)

1. `README.md` — kapsam: **PAPER/MOCK**, LIVE emir yok
2. `docs/architecture.md` — altı katman ve Gölge Defter kuralları
3. `docs/roadmap.md` — hangi faz sırada
4. `docs/agents/README.md` — ortak disiplin (test, rapor, yasaklar)

## Rol dosyaları

| Rol | Dosya | Ne zaman |
| --- | --- | --- |
| Orkestrasyon | `docs/agents/00-orkestrator.md` | Faz planlama, rapor, paralel koordinasyon |
| Piyasa veri | `docs/agents/01-piyasa-adaptor.md` | OKX ATK salt okunur adaptör |
| Analist | `docs/agents/02-analist.md` | BUY/PASS + gerekçe (tutar/emir yok) |
| Anayasa | `docs/agents/03-anayasa.md` | `risk.py` genişletme, deterministik kurallar |
| Gölge Defter | `docs/agents/04-golge-defter.md` | shadow kayıtlar, 15/60 dk gözlem |
| PAPER icra | `docs/agents/05-paper-icra.md` | simüle pozisyon, stop takibi |
| Kokpit | `docs/agents/06-kokpit.md` | Streamlit UI (son faz) |

## Faz sonu zorunluluğu

Her faz bitince `docs/reports/` altına rapor yaz: `docs/agents/faz-raporu-sablonu.md` şablonunu kopyala.

## Test (her değişiklikten sonra)

```bash
pytest -q -n auto   # pytest-xdist yoksa: pytest -q
python -m golge_defter.demo
```

CI: `.github/workflows/tests.yml`
