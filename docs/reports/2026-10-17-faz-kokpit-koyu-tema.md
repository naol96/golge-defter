# Faz raporu — Kokpit: koyu tema

- **Tarih:** 2026-10-17
- **Rol:** `docs/agents/06-kokpit.md`
- **Roadmap maddesi:** Karar kartları ve otomatik yenilenen kokpit
- **Ajan:** Codex

## Hedef

Okunaklı koyu tema ile kalıcı açık/koyu tema seçimi eklemek.

## Yapılan değişiklikler

| Dosya | Özet |
| --- | --- |
| `dashboard/kokpit/index.html` | Varsayılan koyu tema, ilk çizimden önce kayıtlı seçimi yükleme ve tema düğmesi. |
| `dashboard/kokpit/styles.css` | Koyu yüzeyler, tablo satırları, form, durum rozetleri ve yerel tarayıcı kontrolleri. |
| `dashboard/kokpit/app.js` | Açık/koyu geçişi, aria-pressed durumu ve localStorage kalıcılığı. |

## Test sonuçları

| Komut | Sonuç |
| --- | --- |
| `.venv/bin/python -m pytest -q -n auto` | PASS — 34 test |
| `.venv/bin/python -m golge_defter.demo` | PASS |
| `node --check dashboard/kokpit/app.js` | PASS |
| Node VM tema kontrolü | PASS — iki yönlü geçiş, düğme durumu, kalıcılık ve depolama hatası |
| `git diff --check` | PASS |
| CI | Uzak CI çalıştırılmadı |

Pytest ve PAPER demo eş zamanlı ayrı süreçlerde çalıştırıldı.

## Davranış örnekleri

PAPER/MOCK kokpit ilk kez koyu açılır. “Tema: Koyu” düğmesi açık temaya geçirir; seçim aynı tarayıcıda saklanır. Depolama kapalıysa düğme oturum içinde çalışır.

Metin mockup: koyu yeşil zemin → açık metin ve yeşil vurgu → koyu tablo başlığı ve dönüşümlü koyu satırlar.

Çalıştırma: `bash scripts/start_kokpit.sh`; mevcut önizleme: http://127.0.0.1:8502.

## Bilinçli ertelemeler

- Ortamın tarayıcı yüzeyi etkin olmadığı için ekran görüntüsü ile görsel kontrol yapılamadı.

## Sonraki faz

- Sunum cihazında tema renklerinin görsel kontrolü.
- Risk / blokör: yok; PAPER ve iş mantığı değişmedi.
