# Faz raporu — Jüri öncesi MVP denetimi

- **Tarih:** 2026-10-17
- **Rol:** `docs/agents/00-orkestrator.md`; piyasa, anayasa, gölge defter, PAPER icra ve kokpit doğrulamaları
- **Roadmap maddesi:** Demo kayıtları ve hackathon sunumu için mevcut MVP doğrulaması
- **Ajan:** Codex (tek ajan; bağımsız Claude review henüz yapılmadı)

## Hedef

`docs/golge_defter_final.md` şartnamesine göre mevcut MVP'yi denetlemek, P0/P1 hatalarını düzeltmek ve gerçek kanıtlarla sınırlı bir PAPER/DEMO jüri sunumu hazırlamak.

## Yapılan değişiklikler

| Alan | Özet |
| --- | --- |
| ATK | Exchange timestamp korunur, eksik zaman / instrument minimum fail-closed; ortak 3 sn bütçe, MCP bildirimleri bütçeyi sıfırlamaz. |
| Risk | Teknik minimum engeli risk/PASS'tan önce; günlük limit min(%5,5 USDT); audit kod sürümü. |
| PAPER | Alış ücreti günlük net zararda; kaynak / tazelik; rowcount ile tekil kapanış; stop önce işlenir. |
| Shadow | Kaynak / tazelik / horizon fiyat zamanı kontrolleri; stop sınırlama ve gecikme notları; Decimal ve idempotency. |
| Rapor / kokpit | Tutarlı SQLite snapshot, iki bacaklı ATK kökeni, geçmiş teknik blok sınıflaması, PnL gösterim hassasiyeti ve açıklık. |
| SHA-256 | Gerçek batch adedi ve tam karar alanları; yerel hash / doğrulanmamış zincir bağlantısı açıkça ayrılır. |
| Kanıt | 80 Python + 5 JS testi, gerçek ATK + HTTP E2E, 323 kayıtlı PnL yeniden hesabı ve Claude review paketi. |

Tam dosya listesi: `reports/jury-audit/changed-files.txt`.
Fark özeti: `reports/jury-audit/diff-stat.txt` (76d36e3 tabanından ilgili dosyalar).
Kod farkı: `reports/jury-audit/review.patch`.

## Test sonuçları

| Komut | Sonuç |
| --- | --- |
| `.venv/bin/python -m pytest -q -n auto` | PASS — 80 passed in 1.26s |
| `.venv/bin/python -m golge_defter.demo` | PASS — MOCK / SIMULATED |
| `node tests/test_kokpit_ui.js` | PASS — 5 test |
| `node --check dashboard/kokpit/app.js` | PASS |
| `git diff --check` | PASS |
| Gerçek salt okunur ATK → izole PAPER/Shadow → HTML ve JSON HTTP | PASS — 2,8 sn; quote yaşı 1 sn; sinyal DEMO |
| Tarihsel kopyada PnL ve dashboard toplamları | PASS — 323 sonuçta 0 aritmetik fark |
| Uzak CI | Çalıştırılmadı |

Ham çıktılar `reports/jury-audit/` altında. Pytest ve demo ayrı süreçlerde eş zamanlı çalıştırıldı. Düzeltme öncesi yeni regresyon çıktısı: 23 failed, 1 passed; son testler tamamen geçti.

## Davranış örnekleri

- MOCK / SIMULATED: 30 USDT × %25 = 7,5; minimum 10 ise TECHNICAL_BLOCK, risk engeli değil.
- MOCK / SIMULATED: ask 100 / bid 99 / tutar 25 → net −0,29975 USDT.
- MOCK / SIMULATED: stop bid 95 → günlük gerçekleşmiş zarar 1,29875 USDT (iki ücret dahil).
- Gerçek ATK fiyatı + DEMO sinyal: bir APPROVED_PAPER, ikinci aday EXPOSURE / SHADOW_RISK; gerçek emir yok.
- Yeni shadow 15/60 satırları hedefleri gelmediği için PENDING bırakıldı.

## Bilinçli ertelemeler ve kalan sınırlar

- Tarihsel fiyat tazeliği ve geçmiş günlük zarar muhasebesi geriye dönük doğrulanamadı; asıl veritabanı değiştirilmedi.
- Mum içi stop doğrulaması, gerçek LLM sağlayıcı çağrısı ve blockchain receipt/hash doğrulaması bu denetimde yapılmadı; varmış gibi sunulmaz.
- Gerçek tarayıcı görsel QA yapılamadı; Node VM ve gerçek HTTP kontrolü yapıldı.
- Mevcut daemon süreçlerine otomatik deploy / restart yapılmadı; doğrulama izole süreç ve DB'ye aittir.
- Eski roadmap / tarihli teslim metinleri doküman borcu olarak kalır. Güncel otorite: `reports/jury-audit/summary.md`.

## Sonraki faz

- Claude review promptu ile bağımsız P0/P1/P2 ve GO/NO-GO incelemesi.
- Sunum cihazında güncel süreçlerle kokpiti başlatıp kaynak/kanıt etiketlerini görsel olarak doğrulamak.
- Risk / blokör: gerçek LLM performansı ve zincir kanıtı iddiaları için kanıt yok; PAPER/DEMO sınırı korunmalıdır.
