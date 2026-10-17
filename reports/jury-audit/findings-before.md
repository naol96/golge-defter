# Jüri öncesi denetim — düzeltme öncesi bulgular

Kaynak şartname: `docs/golge_defter_final.md`. Kapsam: mevcut PAPER MVP; yeniden yazım, yeni ürün özelliği ve LIVE emir yok.
Başlangıç testi: 34 passed in 1.24s (`.venv/bin/python -m pytest -q -n auto`).

## P0 — güvenilir olmayan fiyatla durum değiştirme

1. `adapters/okx_atk.py`: 10 saniyeden eski / gelecekteki ticker zaman damgası fetched_at ile değiştiriliyor; eksik zaman da şimdi kabul ediliyor. Stale-data engeli adaptör tarafından atlatılabiliyor.
2. `core/shadow_evaluator.py`, `core/position_monitor.py`: tazelik / fiyat geçerliliği kontrolü yok; worker kararı NO_DECISION olsa bile bu fonksiyonlar çalışıyor. MOCK fiyat canlı girişin değerlendirmesini veya stop kapanışını yapabiliyor.

## P1 — ölçüm / muhasebe / kanıt doğruluğu

1. `core/constitution.py`: bakiye <40 ve tutar <min emir OBSERVATION/SHADOW_RISK; ayrıca PASS ve diğer risk kontrolleri teknik minimumdan önce. İcra edilemez kayıt risk fırsatı sayılabiliyor.
2. `report.py`: 15 dk sayacı çıkış feed_source, 60 dk sayacı giriş source kullanıyor; iki bacak birlikte doğrulanmıyor. `dashboard/snapshot.py` ayrı bağlantılardan farklı anların rapor ve sayaçlarını okuyabiliyor.
3. `core/position_monitor.py`: net gerçekleşmiş zararda alış komisyonu eksik; kapanış UPDATE kontrolü rowcount yerine connection.total_changes. Worker yeni kararı stoplardan önce veriyor.
4. `shadow_agent.py`: now fetch/analist öncesinde; geçerli tick gelecek zamanlı görünebilir. `adapters/okx_atk.py`: 3 sn sınırı her read için yeniden başlıyor, toplam çağrı süresi sınırlanmıyor.
5. `core/shadow_evaluator.py`: mum verisi olmadan sonuç COMPLETE; sınırlı stop doğrulaması notu yok. Kaynak ailesi eşleşmesi yok.
6. `chain/anchor_job.py`, `dashboard/kokpit/app.js`: environment URL zincir kanıtıymış gibi sunulabilir; hash edilen en fazla 200 kayıt yerine tüm kayıt sayısı decision_count olarak yazılıyor. Mevcut manifest yerel SHA-256; işlem URL'si boş, zincir kanıtı yok.
7. `dashboard/kokpit/app.js`: ham Decimal PnL dizeleri; 28 basamaklı değerler okunaksız. Sıfıra çok yakın kayıpların görünüm standardı yok. Giriş kökeni, gerçek/hedef ölçüm zamanı ve sınırlama notları tabloda görünmüyor.
8. `core/analyst.py`: LLM isteği piyasa fiyatlarını içermiyor; fazla alanları kabul ediyor, farklı parite yanıtını PASS'a çevirmiyor. LLM_FAIL_CLOSED PASS gerçek analizden ayrılmıyor.
9. Günlük zarar: şartname 5 USDT, rules_v2 gün başı %5. Büyük bakiyede 5 USDT sınırı gevşiyor. İki sınırın küçüğü uygulanmalı; mevcut %5 sıkılaştırması korunmalı.

## P2 — sunum ve operasyon borcu

- README/roadmap hâlihazırdaki modülleri gelecek aşama sayıyor; yatırım anayasası metni zincire yazmayı uygulanmış gibi anlatıyor.
- Mum içi stop doğrulama, gerçek Fuji receipt/payload doğrulaması ve gerçek LLM çalışması mevcut kanıtlarla gösterilemiyor. Yeni özellik eklenmeyecek; sınırlamalar açık yazılacak.
- Eski DB kayıtları yeni doğrulamalar öncesinde üretildi; geriye dönük doğrulanmış sayılmayacak.
- Tarayıcı yüzeyi bu oturumda kullanılamıyor; görsel doğrulama yapılamıyor.

## Salt okunur mevcut veri incelemesi (anlık, değişebilir)

- 295 karar: 1 APPROVED_PAPER, 73 NO_DECISION, 62 SHADOW_RISK, 159 TECHNICAL_BLOCK.
- Bu kararların piyasa kaynağı ATK_LIVE_MARKET, sinyal kökeni DEMO; gerçek LLM kanıtı değildir.
- 15 dk: 194 COMPLETE / 27 PENDING; 60 dk: 104 COMPLETE / 117 PENDING.
- Manifest: decision_count=211, batch_limit=200, snowtrace_tx boş. Yerel hash dışında blockchain iddiası desteklenmiyor.

P0/P1 düzeltmeleri regresyon testleriyle doğrulanacak. Aktif worker DB'si / geçmiş kanıtlar yeniden yazılmayacak.
