# Rol: Gölge Defter

Engellenen, pas geçilen ve teknik blok kayıtlarını saklar; ileride 15/60 dk karşı-olgusal ölçüm.

## Sınıflar (mimari ile uyumlu)

| Decision.status | Gölge tipi |
| --- | --- |
| `SHADOW_RISK` | Risk anayasası engeli |
| `SHADOW_PASS` | Analist pas |
| `TECHNICAL_BLOCK` | Borsa/teknik (önlenen kayıp toplamına **dahil değil**) |

`APPROVED_PAPER` → `executed_trades` (ayrı tablo, paper icra fazında).

## Kapsam faz D (depolama)

- `src/golge_defter/ledger.py` + SQLite dosyası varsayılan `data/golge.db` (gitignore)
- Tablolar: `shadow_trades`, `executed_trades` (şema minimal: id, zaman, parite, status, rule, amount, spread, reason, entry_ask, exit_bid alanları roadmap ile hizalı)
- API: `record_shadow(decision, signal, market)` — idempotent insert (aynı id tekrar yazılmaz)

## Kapsam faz E (gözlem)

- 15 ve 60 dk hedef zamanları Unix epoch saniye
- Bir kez hesaplanan pencere **üzerine yazılmaz**
- Mum yoksa `stop_dogrulamasi_sinirli` etiketi (architecture.md)

## Yapma

- ORM (SQLAlchemy) — ham `sqlite3` yeterli
- Gerçek PnL iddiası; MOCK veride etiket zorunlu

## Test

- `tests/test_ledger.py`: geçici `:memory:` DB
- Paralel: ledger testleri risk testlerinden bağımsız dosyada
- `pytest -q -n auto tests/test_ledger.py tests/test_risk.py`

## Faz raporu

- Şema özeti (tablo + kolon listesi)
- Örnek 3 kayıt (RISK, PASS, TECHNICAL)
- Idempotency test adı
