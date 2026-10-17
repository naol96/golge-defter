# Faz raporu — Kokpit: okunabilir kayıt tabloları

- **Tarih:** 2026-10-17
- **Rol:** `docs/agents/06-kokpit.md`
- **Roadmap maddesi:** Karar kartları ve otomatik yenilenen kokpit
- **Ajan:** Codex

## Hedef

Karar ve gölge kayıtlarını hizalı sütunlar üzerinden karşılaştırılabilir hale getirmek.

## Yapılan değişiklikler

| Dosya | Özet |
| --- | --- |
| `dashboard/kokpit/app.js` | Semantik tablolar, Türkçe durum etiketleri, tam gerekçe, boş tablo mesajları ve gözlem özeti. |
| `dashboard/kokpit/index.html` | Karar listesindeki eski kart kapsayıcı sınıfı kaldırıldı. |
| `dashboard/kokpit/styles.css` | Tam genişlik tablolar, sabit başlık, dönüşümlü satır zemini, odaklanabilir yatay kaydırma, sayısal hizalama; anayasa ve sistem satırlarında okunurluk iyileştirmesi. |

## Test sonuçları

| Komut | Sonuç |
| --- | --- |
| `.venv/bin/python -m pytest -q -n auto` | PASS — 34 test |
| `.venv/bin/python -m golge_defter.demo` | PASS |
| `node --check dashboard/kokpit/app.js` | PASS |
| Node VM render kontrolü | PASS — tablo, HTML kaçışı, sıfır PnL, boş kayıtlar |
| `git diff --check` | PASS |
| CI | Uzak CI çalıştırılmadı |

Pytest ve PAPER demo ayrı süreçlerde eş zamanlı çalıştırıldı.

## Davranış örnekleri

MOCK / SIMULATED: BTC-USDT / Risk engeli / kural / tam gerekçe / kaynak / zaman ayrı sütunlarda gösterilir.
MOCK / SIMULATED: sıfır PnL kaydı 0 USDT olarak gösterilir; eksik PnL “—” olarak kalır.

Metin mockup: simülasyon + anayasa → tam genişlik karar tablosu → tam genişlik gölge gözlem tablosu → sistem + kanıt.

Çalıştırma: `bash scripts/start_kokpit.sh` (8501); mevcut önizleme 8502.

## Bilinçli ertelemeler

- Oturumda tarayıcı yüzeyi bulunmadığından ekran görüntüsü ile doğrulama yapılmadı.

## Sonraki faz

- Sunum cihazında tablo genişliklerinin görsel kontrolü.
- Risk / blokör: yok; backend ve PAPER kapsamı değişmedi.
