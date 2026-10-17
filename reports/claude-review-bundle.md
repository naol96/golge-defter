# Claude review paketi — jüri öncesi denetim

Bu paket bağımsız inceleme içindir; Claude incelemesi yapılmış değildir.

## Önce oku

1. `docs/golge_defter_final.md` — asıl şartname, değiştirilmedi.
2. `AGENTS.md`, `docs/architecture.md`, `docs/agents/README.md` — PAPER-only ve değerlendirme disiplini.
3. `reports/jury-audit/findings-before.md` — kod değişmeden önceki P0/P1/P2 listesi.
4. `reports/jury-audit/summary.md` — sekiz denetim maddesi, düzeltmeler, ham kanıt bağlantıları ve kalan sınırlar.
5. `reports/jury-audit/review.patch` — 76d36e3 tabanına göre yalnızca denetimle ilgili kaynak/test/belge farkı. Ara commit 23b1224 bazı düzeltmeleri içerir; HEAD-only diff bütün denetim değişikliğini göstermez.

## Kanıtlar

| Dosya | Niteliği |
| --- | --- |
| `reports/jury-audit/baseline-regressions.txt` | Düzeltme öncesi 23 failed / 1 passed |
| `reports/jury-audit/pytest-final.txt` | 80 Python testi geçti |
| `reports/jury-audit/demo-final.txt` | MOCK / SIMULATED smoke |
| `reports/jury-audit/ui-tests-final.txt` | 5 Node VM arayüz testi geçti |
| `reports/jury-audit/atk-live-probe.txt` | Sandbox ağ erişimi denemesi timeout; başarı sayılmaz |
| `reports/jury-audit/atk-network-e2e.txt` | Gerçek salt okunur ATK → DEMO → PAPER + Shadow → HTML/JSON dashboard; izole DB |
| `reports/jury-audit/existing-db-recalculation.json` | Tarihsel DB'nin salt okunur kopyasında 323 PnL'nin aritmetik doğrulaması; geçmiş fiyat tazeliği kanıtı değildir |
| `reports/jury-audit/changed-files.txt` | İncelenecek kaynak/test/belge dosyaları |

## Kritik okuma noktaları

- `adapters/okx_atk.py`: borsa timestamp'i değişmez; eksik timestamp/minimum metadata fail-closed; ticker + instrument ortak 3 sn bütçe; yalnızca market ve read-only MCP.
- `contracts/models.py`: `MarketSnapshot.is_usable`, kaynak aileleri, `rules_v2_audit1`.
- `core/constitution.py`: teknik uygulanabilirlik risk/PASS sınıflandırmasından önce; günlük limit iki sert sınırın küçüğü.
- `core/position_monitor.py`: kaynak ve tazelik; alış + satış ücretleri; conditional UPDATE.rowcount.
- `core/shadow_evaluator.py`: hedef zamanından eski fiyatla tamamlanmaz; kaynak ve tazelik; dönem sonu Decimal hesabı ve sınırlı stop notu; idempotency.
- `core/analyst.py`, `core/decision_engine.py`: yalnızca symbol/action/reason; miktar alanı reddi; gerçek market bağlamı; fail-closed cevap NO_DECISION ve gölge başarı üretmez.
- `report.py`, `dashboard/snapshot.py`: aynı SQLite snapshot; 15/60 aynı kaynak koşulları; eski teknik yanlış sınıflar sunumda düzeltilir, ham veri tutulur.
- `chain/anchor_job.py`: yerel hash kapsamı ve batch sayısı; manifest bir blockchain receipt değildir.
- `dashboard/kokpit/app.js`: Decimal değerleri değiştirmeyen gösterim yuvarlaması; kökenler / hedef ve ölçüm zamanı / sınırlamalar; zincir URL'si doğrulanmış sayılmaz.
- `tests/test_jury_audit.py`: gerçek ağ kullanmayan regresyonlar ve enjekte ATK taşımasıyla E2E. Bu testteki ATK etiketi gerçek ağ başarısı kanıtı değildir.
- `tests/test_kokpit_ui.js`: Node VM; gerçek tarayıcı görsel QA değildir.

## Beklenen review çıktısı

`reports/claude-review-prompt.md` içindeki şablonu kullan. Özellikle mevcut düzeltmelerin yeni hata, geriye dönük veri uyuşmazlığı veya yanıltıcı iddia üretip üretmediğini denetle. Her bulgu için dosya/satır, tekrarlama, beklenen/mevcut davranış ve önem seviyesi ver.

Gerçek LLM performansı, intrabar stop veya blockchain doğrulaması varmış gibi değerlendirme yapma. PAPER/DEMO sunumu ve bu iddialar için GO/NO-GO'yu ayrı ver.

ZIP paketi kod, şartname, testler, fark ve kanıtların beyaz listeyle toplanmış kopyasını içerir. Secret, .env, .aws, DB, log klasörü veya hesap verileri pakete dahil edilmez. Paket bütünlüğü `SHA256SUMS` ile denetlenebilir.
