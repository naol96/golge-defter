# Faz raporu — Gönderilen React frontend'in entegrasyonu

- **Tarih:** 2026-10-17
- **Rol:** `docs/agents/06-kokpit.md`
- **Roadmap maddesi:** Karar kartları ve otomatik yenilenen kokpit — kullanıcının gönderdiği tasarım
- **Ajan:** Codex

## Hedef

`/home/hazar/İndirilenler/Telegram Desktop/frontend.zip` içindeki tasarımı mevcut denetlenmiş PAPER backend'ine bağlayıp varsayılan frontend olarak kullanmak.

## Kaynak ve kapsam

Arşivin yalnızca `web/` kaynak/config/lockfile dosyaları ile tasarımın ihtiyaç duyduğu salt okunur `dashboard/analytics.py` ve uyarlanmış testleri alındı. Arşivdeki `.git`, `.venv`, `node_modules`, eski core/backend kopyaları, veritabanı, kanıtlar ve hazır dist alınmadı. Üretim çıktısı kaynaklardan yeniden derlendi.

Arşiv SHA-256 ve kapsam kaydı: [source.json](../../reports/frontend-import/source.json).

## Yapılan değişiklikler

| Dosya / alan | Özet |
| --- | --- |
| `web/` | Gönderilen React/TypeScript/Vite tasarımı: genel bakış, karar akışı, Gölge Defter, anayasa, sistem & kanıt. |
| `dashboard/analytics.py` | Mevcut SQLite üzerinde salt okunur grafik/tablolar; Decimal sonuçlar; teknik sınıf ve sinyal kökeni ayrımı; eski kayıt sınırlama notları. |
| `dashboard/serve_kokpit.py` | Varsayılan React build servisi; `/api/analytics`; mevcut snapshot ve simülasyon uçları korunur. `--ui classic` önceki arayüzü açar. Statik dosya kök kontrolü gerçek path containment kullanır. React iptal ettiği isteklerde bağlantı kapanışları gereksiz traceback üretmez. |
| `scripts/start_kokpit.sh` | React build kontrolü ve `--ui web` ile başlatma. |
| `tests/test_analytics.py` | 7 analitik/API doğrulaması; teknik sınıf, ham veri koruması, Decimal ve salt okunur davranış. |
| `reports/jury-audit/probe_atk.py` | HTML kontrolü hem yeni React root'u hem önceki kokpit ile uyumlu hale getirildi; bu fazda yeni ATK çağrısı yapılmadı. |
| README / `web/README.md` | Derleme, çalıştırma, kaynak ve kanıt sınırları. |
| `reports/frontend-import/` | Gerçek test çıktıları, Chrome sürücüsü ve ekran görüntüleri. |

Risk motoru, ATK adaptörü, worker, pozisyon/shadow hesapları ve veritabanı kayıtları bu frontend fazında değiştirilmedi.

### Tasarımın denetlenen davranışla eşleşmesi

- Sabit 40 USDT gözlem açıklaması yerine adaptörün pariteye bağlı minimum emir kontrolü gösterilir.
- Günlük zarar sınırı `min(gün başı bakiye × %5, 5 USDT)` olarak açıklanır. Anayasa panelinin kod varsayılanı olduğu görünür.
- NO_DECISION tüm dağılım/zaman serilerinde görünür; gölge adayı yüzdesine dahil edilmez.
- PnL altı ondalık ve küçük değer göstergesi taşır; ham değer tooltip'te tutulur. Açık tutar toplamı BigInt ile gösterim için toplanır; float yalnızca görsel oranlarda kullanılır.
- Offline demo verileri ATK veya LLM diye etiketlenmez: FIXTURE_SYNTHETIC_NOT_LIVE / DEMO. Demo canlı ATK sayaçları sıfırdır; fake hash açıkça DEMO_HASH_NOT_PROOF'tur.
- Veri modu değişirken önceki modun payload'ı yeni etiket altında gösterilmez. Simülasyon geçmişi de moda bağlı sıfırlanır.
- Drawer klavye odağını içeride tutar; saat güncellemesi odak çalmaz; Escape kapatır.
- Koyu tema varsayılan; açık/koyu/sistem seçimi ve önceki kayıtlı tercih korunur.

## Test sonuçları

| Komut / kontrol | Sonuç |
| --- | --- |
| `.venv/bin/python -m pytest -q -n auto` | **PASS — 87 passed in 1.29s** |
| `.venv/bin/python -m golge_defter.demo` | **PASS — MOCK / SIMULATED** |
| `npm --prefix web run build` | **PASS — TypeScript + Vite üretim build'i** |
| `npm --prefix web test` | **PASS — 13 test** |
| `node tests/test_kokpit_ui.js` | **PASS — eski arayüzün 5 kontrolü** |
| Gerçek headless Chrome, 8501 | **PASS — 5 görünüm, drawer, simülasyon, kaynak etiketleri, tema, offline ve mobil** |
| `git diff --check` | **PASS** |
| Uzak CI | Çalıştırılmadı |

Pytest ve demo ayrı süreçlerde eş zamanlı çalıştırıldı. Ham çıktılar:

- [pytest.txt](../../reports/frontend-import/pytest.txt)
- [react-tests.txt](../../reports/frontend-import/react-tests.txt)
- [build.txt](../../reports/frontend-import/build.txt)
- [demo.txt](../../reports/frontend-import/demo.txt)
- [classic-ui-tests.txt](../../reports/frontend-import/classic-ui-tests.txt)
- [browser-check.txt](../../reports/frontend-import/browser-check.txt)
- [http-smoke.txt](../../reports/frontend-import/http-smoke.txt) — son sunucu oturumunda HTML/asset ve üç API ucu

## Uçtan uca doğrulama

**Hikâye:** Kullanıcı gönderilen tasarımda görünüm veya simülasyon seçer → React mevcut Python API'lerini çağırır → API SQLite'ı salt okunur okur ya da geçici anayasa simülasyonu hesaplar → yanıt grafikte, tabloda veya sonuç panelinde gösterilir.

| Sınır | Sonuç | Kanıt |
| --- | --- | --- |
| UI render | PASS | Gerçek Chrome; koyu/açık ve 390 px mobil ekran görüntüleri. |
| Client → API | PASS | `/api/snapshot`, `/api/analytics`, `/api/simulate-rule`; beş görünüm ve gerçek form gönderimi. |
| API → data | PASS | SQLite mode=ro; analitik fonksiyonu DB hash'ini değiştirmez. Worker/engine çağrısı yok. |
| Data → response | PASS | Decimal string sonuçlar; sınıf/köken korunur; legacy raw alanlar tutulur. |
| Response → UI | PASS | %80 talebinde %25 sert tavan; kaynaklar görünür; teknik/risk toplamları ayrı. |
| Hata yolu | PASS | Ağ offline yapılınca son iyi veri kalır; kendiliğinden demo moduna geçilmez. |

Chrome'da yakalanan uygulama JavaScript istisnası: **0**. Arka plan başlatma süreci bu yönetilen oturumda kapandığından 8501 açık kalan sunucu oturumunda başlatılıp yeniden doğrulandı. Normal 8501 adresi çalışır durumdadır; worker yeniden başlatılmadı.

## Ekran görüntüleri

- [Masaüstü koyu](../../reports/frontend-import/desktop-dark.png)
- [Masaüstü açık](../../reports/frontend-import/desktop-light.png)
- [Gölge tablo](../../reports/frontend-import/shadow-table.png)
- [Anayasa ve simülasyon](../../reports/frontend-import/constitution.png)
- [Mobil genel bakış](../../reports/frontend-import/mobile-dark.png)
- [Mobil karar tablosu](../../reports/frontend-import/mobile-decisions.png)

## Çalıştırma

```bash
npm --prefix web ci
npm --prefix web run build
bash scripts/start_kokpit.sh
# http://127.0.0.1:8501

# Önceki frontend gerektiğinde:
.venv/bin/python -m dashboard.serve_kokpit --ui classic --port 8502
```

Derlenen dist ve node_modules Git'e alınmaz; temiz klonda ilk iki komut gerekir.

## Davranış örnekleri

- Gerçek DB → tüm kararlar, teknik engeller ve ATK kökenli gözlemler ayrı sayaçlarda.
- MOCK / SIMULATED → %80 talebi API'de %25'te kalır; DB'ye yazılmaz.
- Açıkça seçilen demo → sentetik fiyat / DEMO sinyal, ATK canlı gözlem sayacı 0.
- Bağlantı kesilmesi → son iyi veri ve güncellik uyarısı; otomatik demo yok.

## Bilinçli ertelemeler

- Gerçek LLM, blockchain receipt ve mum içi stop kanıtı önceki denetimdeki sınırlar dahilindedir; frontend bu iddiaları eklemez.
- Bu fazda LIVE emir, deploy/publish veya uzak CI çalıştırılmadı.

## Sonraki faz

- Jüri sunumunu yeni varsayılan frontend üzerinde yürütmek.
- Risk / blokör: frontend entegrasyonunda açık blokör yok; önceki denetimin veri/kanıt sınırları korunur.

## Faz sonu diff özeti

```text
 README.md                                          |    3 +-
 dashboard/analytics.py                             |  181 ++
 dashboard/serve_kokpit.py                          |   49 +-
 .../2026-10-17-faz-react-frontend-entegrasyon.md   |  120 +
 reports/frontend-import/browser-check.mjs          |   80 +
 reports/frontend-import/browser-check.txt          |   25 +
 reports/frontend-import/build.txt                  |   13 +
 reports/frontend-import/classic-ui-tests.txt       |   13 +
 reports/frontend-import/constitution.png           |  Bin 0 -> 166460 bytes
 reports/frontend-import/demo.txt                   |    6 +
 reports/frontend-import/desktop-dark.png           |  Bin 0 -> 149646 bytes
 reports/frontend-import/desktop-light.png          |  Bin 0 -> 149202 bytes
 reports/frontend-import/http-smoke.txt             |   10 +
 reports/frontend-import/mobile-dark.png            |  Bin 0 -> 65563 bytes
 reports/frontend-import/mobile-decisions.png       |  Bin 0 -> 64094 bytes
 reports/frontend-import/pytest.txt                 |    6 +
 reports/frontend-import/react-tests.txt            |   15 +
 reports/frontend-import/shadow-table.png           |  Bin 0 -> 144657 bytes
 reports/frontend-import/source.json                |   20 +
 reports/jury-audit/probe_atk.py                    |    3 +-
 scripts/start_kokpit.sh                            |    7 +-
 tests/test_analytics.py                            |  116 +
 web/.gitignore                                     |    3 +
 web/README.md                                      |   64 +
 web/index.html                                     |   24 +
 web/package-lock.json                              | 2343 ++++++++++++++++++++
 web/package.json                                   |   26 +
 web/src/App.tsx                                    |  534 +++++
 web/src/api/client.ts                              |   62 +
 web/src/api/demo.ts                                |  273 +++
 web/src/api/integration.test.tsx                   |   45 +
 web/src/api/types.ts                               |  155 ++
 web/src/components/charts.tsx                      |  404 ++++
 web/src/components/constitution.tsx                |  255 +++
 web/src/components/layout.tsx                      |  220 ++
 web/src/components/tables.tsx                      |  501 +++++
 web/src/components/ui.tsx                          |  244 ++
 web/src/hooks.ts                                   |  206 ++
 web/src/lib/format.test.ts                         |   64 +
 web/src/lib/format.ts                              |  109 +
 web/src/lib/labels.ts                              |  114 +
 web/src/main.tsx                                   |   11 +
 web/src/styles/app.css                             | 2055 +++++++++++++++++
 web/src/styles/tokens.css                          |  109 +
 web/src/vite-env.d.ts                              |    4 +
 web/tsconfig.json                                  |   19 +
 web/vite.config.ts                                 |   15 +
 47 files changed, 8515 insertions(+), 11 deletions(-)
```
