# Mimari ve metodoloji

Bu belge, hackathon için hazırlanan **Gölge Defter + Yatırım Anayasası** proje taslağının hedef ilkelerini özetler. Bu ilkelerin tamamı henüz kodlanmış değildir.

## Altı hedef katman

1. **Piyasa veri adaptörü:** OKX ATK üzerinden doğrulanmış fiyatlar; 3 sn timeout, 10 sn bayat veri sınırı; bağlantı yoksa etiketsiz sabit fiyatla işlem yapılmaz.
2. **Analist ajan:** Nitel `BUY` / `PASS` kararı + bir cümle gerekçe. Tutar tayin edemez ve emir gönderemez.
3. **Deterministik pozisyon boyutlama:** Kullanılabilir USDT bakiye × etkin anayasal oran. Minimum emir tutarı > anayasal tutar ise **TECHNICAL_BLOCK**.
4. **Yatırım Anayasası:** %25 pozisyon tavanı, izinli üç parite, %0,15 spread, %2,5 stop, 5 USDT günlük gerçekleşmiş zarar sınırı; kurallar sadece sıkılaştırılabilir.
5. **İcra:** Varsayılan PAPER. LIVE ancak ayrıca uygulanacak bir bağlayıcı, kill-switch açık durumun test edilmesi, açık işlem onayı ve borsanın izinlerinin doğrulanması sonrası düşünülebilir. Mevcut kodda LIVE yoktur.
6. **Açık pozisyon takipçisi:** PAPER giriş ask ve güncel bid üzerinden zarar kesme, kapanış, ücret ve UTC-günlük zarar sayacı (henüz geliştirilmedi).

## Gölge Defter hedef metodolojisi

- Ayrı sınıflar: `SHADOW_RISK`, `SHADOW_PASS`, `TECHNICAL_BLOCK`. Teknik engeller **önlenen kayıp** toplamına dahil edilmez.
- Giriş `entry_ask`, çıkış `exit_bid` kullanılır; spread ikinci kez düşülmez, alım/satım komisyonları ayrıca hesaplanır.
- 15. ve 60. dakikada hedef + gerçekleşen ölçüm zamanları Unix epoch saniyesi olarak saklanır.
- Mum içi stop doğrulaması yalnızca giriş sonrası zaman aralığında yapılır. Mum geçmişi yoksa `stop_dogrulamasi_sinirli` etiketi kullanılır.
- Sonuçlar idempotent olmalıdır: Bir kez hesaplanan pencere üzerine yazılmaz.
- Gerçek piyasa ile MOCK veri açıkça ayrılmalı. Karşı-olgusal değerler kesin "önlenen zarar" iddiası değildir.

## Güvenlik

- API anahtarı, secret veya hesap bilgisi repoya yazılmaz. `.env` gitignore kapsamındadır.
- `Withdraw` izni istenmez. Başlangıçta OKX anahtarı gerekmiyor.
- Çalışan kaynak `src/golge_defter/risk.py` yalnızca **PAPER ön-karar** uygular; ağ ve emir fonksiyonu bulunmaz.
- Piyasayla entegrasyondan önce minimum lot, fiyat/size hassasiyeti, komisyon ve stop davranışı doğrulanmalıdır.
