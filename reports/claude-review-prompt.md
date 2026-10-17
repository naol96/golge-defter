# Claude bağımsız inceleme promptu

Bu depodaki mevcut MVP'yi teknik hakem olarak incele. Kod yazmaya başlamadan önce `docs/golge_defter_final.md`, `AGENTS.md`, `reports/claude-review-bundle.md`, `reports/jury-audit/findings-before.md` ve `reports/jury-audit/summary.md` dosyalarını oku. Sıfırdan yazım veya yeni özellik önerme; LIVE emir / blockchain gönderimi / mesaj gönderimi yapma. API anahtarlarını veya .env içeriğini okuma/çıktılama.

Önce P0/P1/P2 bulgularını, sonra yalnızca kanıta dayalı GO/NO-GO kararını ver. Başka bir ajanın “geçti” beyanını test kanıtı sayma; ham çıktıyı ve testin gerçekte neyi doğruladığını kontrol et.

1. ATK borsa timestamp'i korunuyor mu? 3 saniyelik bütçe tüm snapshot için mi? Hatalı/eksik fiyat veya min emir metadata'sı işlem/PnL üretebilir mi?
2. Gerçek ATK fiyatı ile DEMO/LLM sinyal kökeni ayrılıyor mu? Enjekte taşıma testleri canlı kanıt diye sunuluyor mu?
3. Analyst yalnızca symbol/action/reason üretebiliyor mu? Başarısız veya farklı parite yanıtı gölge performansına giriyor mu?
4. Minimum emrin altında kalan BUY/PASS ve riskle çakışan adaylar teknik sayılıyor mu? Eski OBSERVATION kayıtları ve ham kayıt koruması tutarlı mı?
5. 15/60 dakika sonuçlarında giriş ask, çıkış bid, tekil alış/satış komisyonu ve Decimal doğru mu? Hedef öncesi fiyat, gecikme, sınırlı stop etiketi ve idempotency doğru mu?
6. Stop takipçisi stale/future/invalid/yanlış kaynaklı fiyatı reddediyor mu? Gap-down gerçek bid üzerinden mi? Günlük zarar her iki ücreti kapsıyor mu? UTC reset ve stop → yeni karar sırası doğru mu?
7. Günlük sınır `min(%5 gün başı bakiye, 5 USDT)` gerçekten uygulanıyor mu? Hiçbir düzeltme var olan sınırı gevşetiyor mu?
8. Dashboard/rapor sayaçları eş zamanlı yazma altında aynı snapshot'a mı ait? ATK gözlem sayaçlarında hem giriş hem çıkış doğrulanıyor mu? Teknik ölçümler risk koruması diye toplanıyor mu?
9. Yerel SHA-256 kapsamı / batch kayıt sayısı doğru mu? URL veya manifest flag'i gerçek receipt/hash kanıtı gibi gösteriliyor mu?
10. PnL gösterimi küçük negatif değeri sıfıra gizliyor mu, ham Decimal'i değiştiriyor mu? Kaynak ve sınırlamalar görünür mü?
11. Eski verinin doğrulanamayan quote yaşı / stop notu / günlük zarar muhasebesi dürüstçe belirtilmiş mi? rules_v2_audit1 eski kurallardan ayrılıyor mu?
12. Mevcut çalışan süreçler ile düzeltilmiş kodun testleri karıştırılıyor mu? Uzak CI / gerçek LLM / gerçek tarayıcı / blockchain review yapılmış gibi sunuluyor mu?

İzinli yerel kontroller:

```bash
.venv/bin/python -m pytest -q -n auto
.venv/bin/python -m golge_defter.demo
node tests/test_kokpit_ui.js
```

Ağ denemesi gerekli görülürse yalnızca `reports/jury-audit/probe_atk.py` salt okunur, izole PAPER senaryosunu kullan; bu scriptin de kapsamını önce incele. Canlı worker DB'sini değiştirme.

Çıktı:

- P0 / P1 / P2: dosya:satır, tetikleyici, mevcut ve beklenen davranış, tekrar üretme komutu, en küçük düzeltme.
- Gerçek çalıştırılan komutlar ve ham sonuçları; çalıştırılamayanları açıkça yaz.
- PAPER/DEMO jüri sunumu için GO/NO-GO.
- LLM performansı / doğrulanmış blockchain / kesin önlenen zarar iddiaları için ayrı GO/NO-GO.
- Bulgusuzsa “bulgu yok” de; kanıt sınırlarını ayrıca belirt.
