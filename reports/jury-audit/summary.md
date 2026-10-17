# Gölge Defter — jüri öncesi MVP denetimi

Tarih: 2026-10-17. Şartname: `docs/golge_defter_final.md` (değiştirilmedi).
Kapsam: mevcut çalışan PAPER MVP'nin hata düzeltmeleri; yeniden yazım, yeni ürün özelliği, LIVE emir ve blockchain gönderimi yok.

**Sonuç: PAPER + açıkça DEMO olarak etiketli analist sunumu için şartlı GO. Gerçek LLM başarısı, doğrulanmış blockchain kaydı veya kesin “önlenen zarar” iddiası için kanıt yok.**

## Önce bulgular

Kod düzeltmesinden önce P0/P1/P2: [findings-before.md](findings-before.md).
Başlangıçtaki 34 test geçerken, yeni hata senaryolarının ilk çalıştırması **23 failed, 1 passed** verdi: [baseline-regressions.txt](baseline-regressions.txt).

## İstenen sekiz kontrol

| Kontrol | Sonuç / kanıt |
| --- | --- |
| ATK ve DEMO kökenleri | Giriş ve çıkış kaynakları ayrı; sinyal kökeni ayrı. Mevcut tarihsel kopyada 313 kararın tamamı ATK_LIVE_MARKET + DEMO. Bu bir LLM başarı ölçümü değildir. |
| Dashboard sayaçları | Rapor ve snapshot aynı SQLite okuma transaction'ını kullanır. Eş zamanlı yazma regresyonu geçti. 15/60 ATK sayaçlarında hem giriş hem çıkış ATK olmalı. |
| 15/60 shadow PnL | Ask giriş, bid çıkış, her yönde %0,1 ücret varsayımı; spread tekrar düşülmez. Tam Decimal testleri, hedef öncesi fiyat reddi, geç ölçüm ve idempotency geçti. |
| Teknik blok / risk ayrımı | Minimum altındaki BUY ve PASS her durumda TECHNICAL_BLOCK. Eski OBSERVATION/MIN_ORDER yanlış risk kayıtları, ham kayıtlar değiştirilmeden raporda teknik sayılır. |
| Stop / daily loss / stale | Alış komisyonu gerçekleşmiş zarara dahil. UTC gün geçişi, stop eşitliği, gap-down, çift kapanış engeli ve stale/future/invalid veri senaryoları geçti. Yeni karar öncesinde stoplar işlenir. |
| SHA-256 / blockchain | Manifest yalnızca LOCAL_SHA256, blockchain_verified=false. Dışarıdan URL eklenmesi doğrulama değildir. Hash edilen karar adedi batch limitine uyar. Tam karar alanları hash kapsamındadır. |
| PnL gösterim hassasiyeti | Birincil web kokpitinde altı ondalık, tam sayı aritmetiğiyle gösterim yuvarlaması, ham değer tooltip'i; küçük negatif değer “−<0,000001”. Depolanan Decimal değiştirilmez. |
| Gerçek ATK → Agent → Constitution → PAPER/Shadow → Dashboard | Salt okunur gerçek ATK, DEMO analist, izole geçici DB, bir PAPER ve bir SHADOW_RISK; gerçek HTML ve JSON uçları doğrulandı. 15/60 sonuçlar PENDING. |

## Gerçek test çıktıları

| Komut | Çıktı |
| --- | --- |
| `.venv/bin/python -m pytest -q -n auto` | **80 passed in 1.26s** — [ham çıktı](pytest-final.txt) |
| `.venv/bin/python -m golge_defter.demo` | PASS, MOCK / SIMULATED — [ham çıktı](demo-final.txt) |
| `node tests/test_kokpit_ui.js` | **5 tests, 5 pass, 0 fail** — [ham çıktı](ui-tests-final.txt) |
| `node --check dashboard/kokpit/app.js` | PASS (exit 0) |
| `git diff --check` | PASS (exit 0) |
| `.venv/bin/python reports/jury-audit/probe_atk.py` (izinli ağ erişimi) | PASS — [gerçek ATK + HTTP çıktısı](atk-network-e2e.txt) |
| `.venv/bin/python reports/jury-audit/audit_existing_db.py` | PASS — [tarihsel yeniden hesaplama](existing-db-recalculation.json) |

Pytest ve demo ayrı süreçlerde eş zamanlı çalıştırıldı. Uzak CI / bağımsız Claude incelemesi çalıştırılmadı.
İlk sandbox ağ denemesi 3,008 sn'de timeout oldu; bu başarısız deneme de [saklandı](atk-live-probe.txt). Ağ erişimi olan son uçtan uca test 2,8 sn'de tamamlandı; quote yaşı 1 sn idi. Bu tek ölçüm kesintisiz servis garantisi değildir.

## Finansal hesap doğrulamaları (MOCK / SIMULATED)

- Giriş ask 100, tutar 25 → miktar 0,25. Çıkış bid 99 → net **−0,29975 USDT**.
- Aynı giriş, çıkış bid 101 → net **+0,19975 USDT**.
- Stop/gap çıkışı bid 95 → net gerçekleşmiş zarar **1,29875 USDT**, son PAPER bakiye **98,70125 USDT**.
- Günlük sınır `min(gün başı bakiye × %5, 5 USDT)`; şartnamedeki 5 USDT ile mevcut daha sıkı %5 kuralı birlikte korunur.
- Düzeltme sürümü **rules_v2_audit1**. Geçmiş kararların rules_version alanı değiştirilmedi.

## Tarihsel veri: doğrulanan ve doğrulanamayan

`data/golge.db` salt okunur bağlantıdan geçici tutarlı bir kopyaya alındı; asıl kayıtlar değiştirilmedi.
Kopyadaki **205 adet 15 dk + 118 adet 60 dk = 323 tamamlanmış sonuç** için:

- Kayıtlı entry_ask / exit_bid / notional ile Decimal yeniden hesaplama: **0 fark**.
- Hedef zamandan önce tamamlanma: **0**.
- Karışık giriş/çıkış kaynak ailesi: **0**.
- SQL toplamı / dashboard / rapor sayaç tutarsızlığı: **0**.
- Eski kayıtlarda `stop_dogrulamasi_sinirli` notu eksik: **323**. Geriye dönük değiştirilmedi; arayüz eksik doğrulama notunu açıkça belirtir.

Bu kontrol kayıtlı aritmetiği doğrular. Eski adaptör zaman damgasını değiştirebildiği ve quote yaşı ayrıca saklanmadığı için **tarihsel fiyat tazeliği doğrulanamaz**. Bu eski kayıtlar “doğrulanmış canlı performans” sayılmaz. Süren worker nedeniyle farklı zamanda alınan toplamlar değişebilir; kanıt JSON'u tutarlı tek kopyaya aittir.

## Değişen dosyalar

Kaynak/test/belge listesi: [changed-files.txt](changed-files.txt). Tam kaynak farkı: [review.patch](review.patch).

- Veri ve güvenlik: `adapters/okx_atk.py`, `contracts/models.py`, `core/constitution.py`, `core/analyst.py`.
- PAPER / shadow: `core/decision_engine.py`, `core/paper_broker.py`, `core/position_monitor.py`, `core/shadow_evaluator.py`, `storage/database.py`.
- Sayaç / kanıt / sunum: `report.py`, `dashboard/snapshot.py`, `chain/anchor_job.py`, `dashboard/kokpit/app.js`, `dashboard/kokpit/index.html`.
- Giriş noktaları: `shadow_agent.py`, `main.py`, yedek `dashboard/app.py` (stop sıralaması).
- Testler: `tests/test_jury_audit.py`, `tests/test_kokpit_ui.js`, mevcut `tests/test_constitution_v2.py` beklentisi.
- Belgeler: README, spec kararları, yatırım anayasasının uygulanmış zincir iddiası ve bu denetim paketi.

## Kalan hatalar / sınırlar

Denetlenen kod yollarında testlerle yeniden üretilmiş açık P0/P1 bırakılmadı. Bu bir bağımsız review veya tüm olası hata yollarının ispatı değildir.

1. **P2 / tarihsel kanıt borcu:** Yukarıdaki 323 eski sonuç için fiyat tazeliği ve mum içi stop kanıtı sonradan üretilemez. Geçmiş günlük zarar sayacı eksik alış komisyonuyla güncellenmiş olabilir; tarihsel pozisyon başına muhasebe defteri bulunmadığından geriye dönük otomatik düzeltme yapılmadı.
2. **Kapsam sınırı:** Mum içi stop verisi yok; shadow PnL dönem sonu ölçümüdür. Yeni sonuçlar sınırlı doğrulama notu taşır. Bu gerçek bir “önlenen zarar” garantisi değildir.
3. **Kapsam sınırı:** Gerçek LLM sağlayıcısıyla bu denetimde çağrı yapılmadı. Şema, yetki alanları, bağlam ve fail-closed yolu enjekte edilmiş yanıtlarla test edildi. Gerçek uçtan uca sonuç DEMO analiste aittir.
4. **Kapsam sınırı:** Gerçek blockchain işlemi / receipt / payload eşleşmesi yok. Yerel hash dışında zincir kanıtı iddia edilmez.
5. **P2 / metadata:** Anayasa paneli kod varsayılanlarını gösterir; karar anındaki kullanıcı sıkılaştırmalarının tam anlık görüntüsü saklanmaz. Panel bunu açıkça belirtir. `rules_v2_audit1` önceki sürümden ayrılır.
6. **P2 / görsel QA:** Tarayıcı yüzeyi bu oturumda etkin değil; gerçek tarayıcı ekran görüntüsü ve mobil görsel kontrol yapılamadı. JS render testleri bunun yerine geçmez. Yedek Streamlit sayfaları birincil tasarımın tüm gösterim iyileştirmelerini taşımaz.
7. **Operasyon:** İzole gerçek ATK + HTTP testi tamamlandı; mevcut uzun ömürlü worker/kokpit süreçlerine bu denetimden otomatik deploy yapılmadı. Sunumdan önce yeni süreçlerle başlatılmalı; eski veri ayrı tutulmalı. Yerel SQLite eski pozisyon kaynaklarını ancak eşleşen karar kaydı varsa geri doldurur; kaynağı belirsiz pozisyonla MOCK/ATK karıştırılmaz.
8. **P2 / doküman borcu:** Eski roadmap ve tarihli teslim kartları farklı anların durumunu gösterir. Güncel test sonucu ve kapsam için bu rapor esas alınmalıdır.

## Sunumda kullanılabilecek doğru ifade

> “Gerçek ATK piyasa verisini, açıkça DEMO olarak etiketli analistle deterministik kurallardan geçiriyoruz. İşlemler PAPER. Shadow sonuçlarımız ücret dahil karşı-olgusal dönem sonu ölçümleri; mum içi stop kanıtı sınırlı. Yerel SHA-256 üretiyoruz; doğrulanmış blockchain işlemi iddiamız yok.”

## Tekrar çalıştırma

```bash
.venv/bin/python -m pytest -q -n auto
.venv/bin/python -m golge_defter.demo
node tests/test_kokpit_ui.js
.venv/bin/python reports/jury-audit/audit_existing_db.py
# Ağ erişimi gerekir; worker DB'sine yazmaz, gerçek emir yok:
.venv/bin/python reports/jury-audit/probe_atk.py
# Birincil kokpit (salt okunur):
bash scripts/start_kokpit.sh
```

Claude inceleme başlangıcı: `reports/claude-review-bundle.md`; prompt: `reports/claude-review-prompt.md`.
