# Faz raporu — Kokpit: hackathon kontrol masası

- **Tarih:** 2026-10-17
- **Rol:** `docs/agents/06-kokpit.md`
- **Roadmap maddesi:** Streamlit karar kartları ve otomatik yenilenen kokpit (mevcut stdlib HTTP + HTML/CSS/JS kokpiti üzerinden tasarım iyileştirmesi)
- **Ajan:** Codex

## Hedef

Projenin karar denetimi ve gölge gözlem farkını jüriye ilk ekranda anlatan, etkileşimli bir PAPER kontrol masası oluşturmak.

## Yapılan değişiklikler

| Dosya | Özet |
| --- | --- |
| `dashboard/kokpit/index.html` | Marka, proje anlatısı, dört adımlı karar akışı, bölüm bağlantıları, öne alınmış simülasyon ve erişilebilir durum alanları. |
| `dashboard/kokpit/styles.css` | Sıcak beyaz / mürekkep / yeşil palet, tipografik hiyerarşi, iki sütunlu çalışma alanı, mobil düzen, klavye odağı ve azaltılmış hareket desteği. |
| `dashboard/kokpit/app.js` | Örnek talep düğmeleri, gönderim bekleme durumu, bağlantı hatası, boş karar durumu ve çalışır zincir doğrulama bağlantısı. |

Backend iş mantığı ve anayasa kuralları değiştirilmedi. Harici font, görsel veya yeni bağımlılık eklenmedi. Gerçek veri gözlemleri ile PAPER/MOCK icra ayrımı ve karşı-olgusal sonuç sınırı görünür tutuldu.

## Test sonuçları

| Komut / kontrol | Sonuç |
| --- | --- |
| `.venv/bin/python -m pytest -q -n auto` | PASS — 34 test |
| `.venv/bin/python -m golge_defter.demo` | PASS — MOCK / SIMULATED |
| `node --check dashboard/kokpit/app.js` | PASS |
| `git diff --check` | PASS |
| Yerel HTTP sayfa + snapshot uçları | PASS |
| POST simülasyon: %80 talebi | PASS — etkin tavan %25 |
| Node VM: gerçek snapshot render ve boş karar durumu | PASS |
| CI | Yerelde çalıştırılmadı; uzak CI bekliyor |

Pytest ve demo ayrı süreçlerde eş zamanlı çalıştırıldı.

## Davranış örnekleri

- MOCK / SIMULATED: “Bakiyemin %80'i ile al” → etkin tavan %25 korunur.
- MOCK / SIMULATED: “Bakiyemin %10'u ile al” örneği tek düğmeyle simülasyon formuna gönderilir.
- Bağlantı kesilirse üstte güncellik uyarısı, bağlantı rozetinde kontrol durumu gösterilir.
- Karar yoksa boş alan yerine açıklama gösterilir.

Metin mockup: Marka / bölüm gezinmesi / PAPER etiketi → proje anlatısı + karar yolculuğu → beş veri göstergesi → simülasyon + anayasa → karar akışı + gölge kayıtlar → sistem + zincir kanıtı.

## Çalıştırma

```bash
bash scripts/start_kokpit.sh
# Alternatif önizleme (bu çalışma sırasında başlatıldı):
.venv/bin/python -m dashboard.serve_kokpit --port 8502
```

## Bilinçli ertelemeler

- Tarayıcı yüzeyi ortamda etkin değil (`CUA_REPL_ENABLED_SURFACES is required`); ekran görüntüsü ve gerçek tarayıcıda mobil/görsel kontrol tamamlanamadı. Node render kontrolü görsel doğrulama yerine geçmez.
- Yedek Streamlit arayüzleri bu tasarım kapsamına alınmadı.

## Sonraki faz

- Jüri sunum cihazında 8501/8502 kokpitini açıp ekran boyutuna göre görsel kontrol yapmak.
- Risk / blokör: LIVE emir desteği yok; yalnızca PAPER/MOCK.
