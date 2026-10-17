# Gölge Defter + Yatırım Anayasası: Kapsamlı Proje, Mimari ve Strateji Raporu

**Proje Adı**: Gölge Defter + Yatırım Anayasası

**Hedef Etkinlik**: OKX TR x Team1 Türkiye Agentic Hackathon (17 Ekim 2026, Ankara)

**Odak Pariteler**: AVAX/USDT (Merkez Parite), BTC/USDT, ETH/USDT

**Temel Mimari İlke**: Yapay zekâ modeli yalnızca piyasa yönünü önerir (Alım veya Pas); işlem tutarı, güvenlik tavanları, açık pozisyon takibi ve emir icrası sabit kurallarla yönetilir.

---

## 1. Yönetici Özeti ve Değer Önerisi

30 ile 50 dolar büyüklüğündeki bir yarışma bakiyesi ve 8 saatlik bir zaman diliminde *"Yapay zekâ ajanımız %40 kâr etti"* iddiası istatistiksel olarak kanıtlanamaz ve piyasanın yatay veya düşüş yönlü gittiği senaryolarda çöker.

**Gölge Defter + Yatırım Anayasası**, otonom ajanların başarısını rastlantısal kâr rakamlarıyla değil, **"Ajan hangi işlemi, hangi anayasal maddeyle engelledi ve gözlenen varsayımlar altında olası zararı nasıl görünür kıldı?"** sorusunun denetlenebilir, karşı-olgusal (gölge) analiziyle kanıtlamak üzere tasarlanmıştır:

1. **Kesin Yetki Ayrılığı**: Dil modeli asla işlem büyüklüğü (tutar) belirlemez ve doğrudan borsaya emir gönderemez; yalnızca piyasa göstergelerini yorumlayarak parite adı, işlem yönü (Alım veya Pas) ve kısa gerekçe sunar.
2. **Kurallara Bağlı Pozisyon Boyutlama**: Sistemde modelin ürettiği bir "aday tutar" kavramı yoktur. İşlem büyüklüğü yalnızca mevcut kullanılabilir bakiye ve etkin anayasal oran üzerinden matematiksel olarak hesaplanır.
3. **Gerçekçi Fırsat ile Teknik Engelin Ayrılması**: Anayasa tarafından risk kuralları nedeniyle durdurulan gerçekçi fırsatlar ile borsanın minimum emir sınırına takılan teknik kayıtlar birbirinden ayrı sınıflandırılarak jüri önünde tam metodolojik dürüstlük sağlanır.
4. **Varsayılan Sanal Mod ve Açık Pozisyon Koruması**: Sistem varsayılan olarak sanal (paper) modda çalışır. Canlı borsa emri yalnızca **acil durdurma anahtarı (kill-switch) kapalıyken ve kullanıcıdan açık onay alındığında** devreye girer. Açılan her pozisyon arka planda bağımsız bir risk takipçisi tarafından izlenir.

---

## 2. İncelenen Örnek Yaklaşımlar ve Projenin Farkı

Otonom ticaret yarışmalarında öne çıkan üç temel yaklaşımla bu projenin farkı aşağıda özetlenmiştir:

| Yaklaşım Tipi | Mevcut Örneklerin Odak Noktası | Gölge Defter + Yatırım Anayasası'nın Farkı |
| --- | --- | --- |
| **Doğal Dil Strateji Simülatörleri** | Kullanıcının yazdığı stratejileri geçmiş veride simüle ederek parametre duyarlılığını göstermek. | Geçmiş veriyi değil, **o an canlı piyasada pas geçilen veya engellenen işlemleri** 15 ve 60 dakika ileriye dönük izlemek. |
| **Komut Satırı Risk ve Bakiye Botları** | Ekran arayüzü olmadan zarar kesme uygulamak ve işlem sonrası kalan küsurat bakiyeleri temizlemek. | Güvenlik sınırlarını komut satırından çıkarıp kullanıcının doğal dille sıkılaştırabildiği şeffaf bir **Yatırım Anayasası** ve Karar Kartı arayüzüne taşımak. |
| **Saf Kantitatif Momentum Ajanları** | Emir defteri derinliği ve oynaklığa göre kademeli limit emirler göndererek risk-getiri oranını optimize etmek. | Kantitatif alış-satış makası ve limit emir disiplinini korurken, **"yapılmayan işlemlerin de finansal değerini ölçen"** karşı-olgusal bir denetim katmanı eklemek. |

---

## 3. Sistem Mimarisi ve 6 Katmanlı Karar Zinciri

Sistem, piyasa verisinin okunmasından açık pozisyonların kapatılmasına kadar birbirinden bağımsız 6 katmandan oluşur:

### 1. Katman: Piyasa Veri Adaptörü ve Veri Tazeliği Denetimi

* **Bağımsız Veri Adaptörü**: Veri kaynağı (doğrulanmış borsa araçları veya açıkça etiketlenmiş sanal veri sağlayıcı) sabit bir internet adresine bağımlı kılınmaz; tüm iletişim veri adaptörü katmanının sorumluluğundadır.
* **3 Saniye Zaman Aşımı ve Veri Yaşı Kontrolü**: Sahnede yaşanabilecek internet yavaşlamalarına karşı veri çağrılarına en fazla 3 saniyelik bekleme sınırı uygulanır. Önbellekteki fiyat verisinin kaç saniyelik olduğu sürekli izlenir; veri yaşı belirlenen eşiği (10 saniye) aşarsa sistem bayat veriyle karar üretmeyi reddeder ve ekranda *"Bağlantı optimize ediliyor"* uyarısı gösterir.
* **Sabit Fiyat Yasağı**: Ağ kopması durumunda ekranın çökmemesi için tutulan varsayılan örnek veriler **asla işlem açmak veya Gölge Defter kâr/zarar sonucu üretmek için kullanılmaz**; yalnızca arayüz tanıtım verisi olarak etiketlenir.

### 2. Katman: Analist Ajan (Yalnızca Nitel Sinyal)

* **Sorumluluk Sınırı**: Analist ajan teknik göstergeleri (RSI, alış-satış makası, fiyat ivmesi) inceleyerek yalnızca üç çıktı üretir: **Parite Adı** (örneğin AVAX/USDT), **İşlem Yönü** (Alım veya Pas) ve **Kısa Gerekçe**.
* **Tutar Üretmeme Kuralı**: Model hiçbir koşulda dolar cinsinden işlem büyüklüğü önermez; bu sayede modelin hatalı veya aşırı yüksek tutarlı emir önerme riski mimari olarak ortadan kaldırılır.
* **Yalnızca Alım Yönü Kuralı**: Spot piyasada cüzdanda olmayan bir varlığın satılmasını engellemek için ilk aşamada yalnızca Alım yönlü sinyaller işleme alınır.

### 3. Katman: Pozisyon Boyutlayıcı

* **Hesaplama Kuralı**: Hem Alım hem de Pas sinyalleri için anayasal işlem büyüklüğü, kullanılabilir bakiyenin etkin pozisyon yüzdesiyle çarpılmasıyla belirlenir.
* **Minimum Emir Sınırı Denetimi ve Sınıflandırma**:
* Hesaplanan anayasal tutar, borsanın o parite için belirlediği minimum emir büyüklüğünün (örneğin 10 dolar) altındaysa (örneğin 30 dolar bakiyede %25 etkin tavan ile 7.5 dolar çıkıyorsa), anayasal tavan asla delinmez ve işlem **engellenir**.
* Bu durum Gölge Defter'de gerçek bir piyasa fırsatı engeli olarak değil, **"Borsada İcra Edilemez Teknik Kayıt"** statüsüyle kaydedilir.


* **Pas Sinyallerinde Tutar Kaydı**: Analist ajan Pas kararı verdiğinde de aynı hesaplama kuralıyla belirlenen tutar ve kullanılan oran kayda geçirilir; böylece 15 ve 60 dakikalık karşı-olgusal kâr/zarar hesabı tamamen tekrar üretilebilir olur.

### 4. Katman: Yatırım Anayasası ve Şeffaf Sıkılaştırma Motoru

* **Varsayılan Güvenlik Sınırları**: Kullanıcı hiçbir kural tanımlamasa dahi sistem aşağıdaki 5 sert sınırı zorunlu olarak uygular:
1. **Tek İşlem Tavanı**: Kullanılabilir bakiyenin en fazla **%25**'i.
2. **İzinli Pariteler**: Yalnızca **AVAX/USDT, BTC/USDT, ETH/USDT** (Team1 ve Avalanche uyumu kapsamında merkez parite AVAX/USDT'dir).
3. **Maksimum Alış-Satış Makası (Spread) Sınırı**: Emir defteri makası en fazla **%0.15**.
4. **Zorunlu Zarar Kesme (Stop-Loss)**: Giriş fiyatından itibaren en fazla **%2.5** düşüş sınırı.
5. **Günlük Gerçekleşmiş Zarar Limiti**: En fazla **5.0 dolar**.


* **Şeffaf Kural Sıkılaştırma ve Red Bildirimi**: Kullanıcı doğal dille yeni bir kural yazdığında, bu kural varsayılan güvenlik sınırlarını **gevşetemez; yalnızca daha katı hale getirebilir**.
* Kullanıcı *"Bakiyemin %80'i ile işlem aç"* yazarsa, sistem bunu sessizce değiştirmez; Anayasa Paneli ve Karar Kartı üzerinde açıkça **"Kullanıcı kuralı (%80) sert tavan nedeniyle uygulanmadı; etkin değer %25 olarak korundu"** uyarısını gösterir.
* Kullanıcı *"Tek işlemde en fazla %15 kullan"* yazarsa, daha sıkı olduğu için etkin değer **%15** olarak uygulanır.


* **Günlük Zarar Limitinin Tanımı**:
* **Kapsam**: Yalnızca kapanmış ve gerçekleşmiş zararlar toplama dahil edilir. Sanal modda sanal işlemlerin gerçekleşmiş zararı, canlı modda ise canlı işlemlerin gerçekleşmiş zararı kendi içinde ayrı izlenir.
* **Sıfırlanma Zamanı**: Zaman dilimi karmaşasını önlemek için günlük zarar sayacı **evrensel saat (UTC 00:00)** standardına göre her gün başında sıfırlanır.



### 5. Katman: İcra Birimi ve Mod Yönetimi

* Tüm anayasal kontrollerden geçen işlem için icra modu belirlenir:
* **Canlı İşlem Koşulu**: Yalnızca **acil durdurma anahtarı (kill-switch) devre dışıysa** VE **kullanıcının açık canlı işlem onayı mevcutsa** emir borsaya iletilir. Aksi tüm durumlarda işlem sanal (paper) modda açılır.



### 6. Katman: Açık Pozisyon Risk ve Zarar Kesme Takipçisi

* Zarar kesme kuralı yalnızca Gölge Defter analizinde kalmaz; onaylanıp açılan her sanal veya canlı pozisyon arka planda çalışan **Açık Pozisyon Risk Takipçisi** tarafından sürekli izlenir.
* Takipçi, her döngüde açık pozisyonların giriş satış fiyatını ve etkin zarar kesme yüzdesini kontrol eder. Güncel piyasa alış fiyatı, belirlenen zarar kesme seviyesinin altına indiği anda pozisyonu otomatik olarak kapatır, gerçekleşen net zararı hesaplar ve günlük gerçekleşmiş zarar sayacına işler.

---

## 4. Gölge Defter Değerlendirme Metodolojisi

Anayasa tarafından engellenen veya pas geçilen işlemlerin 15. ve 60. dakika sonuçları hesaplanırken beş temel standart uygulanır:

1. **İcra Edilebilir Fırsat ile Teknik Engelin Ayrılması**:
* Minimum emir büyüklüğü yetersizliği nedeniyle engellenen kayıtlar, borsada zaten açılamayacak emirler olduğu için ana ekrandaki **"Anayasal Koruma (Önlenen Olası Zarar)"** toplamına dahil edilmez; ayrı bir teknik filtre sayacında gösterilir. Ana koruma metriği yalnızca borsada açılabilir olup anayasal risk maddeleriyle (yüksek makas, parite kısıtı, günlük zarar limiti vb.) durdurulan işlemleri kapsar.


2. **Gerçekçi Giriş/Çıkış ve Tekil Komisyon Hesabı**:
* Sanal giriş fiyatı olarak karar anındaki tahta satış fiyatı, 15. ve 60. dakika çıkış fiyatları olarak ise ilgili değerlendirme anındaki tahta alış fiyatları kullanılır.
* Alış-satış makası (spread) bu iki fiyat arasındaki farkta zaten yer aldığından **ikinci kez düşülmez**; sonuçtan yalnızca alış ve satış yönlü borsa komisyonu düşülür.


3. **Zaman Pencereli Ara Mum Kontrolü**:
* Yalnızca **işlemin kaydedildiği saniye ile değerlendirme saniyesi arasındaki** mumların en düşük fiyatları taranır. Giriş öncesine ait mumlar kesinlikle hariç tutulur.
* İlgili zaman aralığında ara mum verisi mevcut değilse sonuç dürüstçe **"Zarar kesme doğrulaması sınırlı (yalnızca dönem sonu fiyatıyla hesaplandı)"** olarak işaretlenir.


4. **Hedef ve Gerçek Değerlendirme Zamanlarının Saklanması**:
* Her gölge kayıt için 15. ve 60. dakika hedef değerlendirme zamanları ile gerçek ölçüm zamanları yan yana kaydedilir. Aradaki fark belirlenen toleransı aşarsa **"Gecikmeli değerlendirme"** etiketi kanıtlanabilir şekilde eklenir.


5. **Tekrarlanabilir (İdempotent) Değerlendirme Kuralı**:
* Arka plan takipçisi aynı kaydı birden fazla kez tarasa bile, 15. veya 60. dakika sonucu bir kez hesaplandıktan sonra kilitlenir; sonraki döngülerde üzerine yazılmaz veya mükerrer toplama yapılmaz.



---

## 5. Veritabanı Yapısı ve İzlenebilirlik Alanları

Veritabanında tüm zaman kayıtları, Türkiye saati ile evrensel saat arasındaki 3 saatlik farktan kaynaklanabilecek hataları önlemek için **tamsayı saniye (Unix zaman damgası)** olarak tutulur ve iki ayrı tablo kullanılır:

### 1. İcra Edilen İşlemler Tablosu

Onaylanarak sanal veya canlı modda açılan işlemlerin tutulduğu tablodur:

* **Tutulan Bilgiler**: İşlem kimliği, parite adı, işlem yönü (Alım), icra modu rozeti (Sanal veya Canlı), karar kaynağı, uygulanan boyutlama kuralı, giriş satış fiyatı, kapanış alış fiyatı, hesaplanan anayasal tutar, zarar kesme fiyatı, uygulanan komisyon oranı, gerçekleşen net kâr/zarar, açılış zamanı, kapanış zamanı ve pozisyon durumu (Açık, Zarar Kesme İle Kapandı, Manuel Kapandı).

### 2. Gölge İşlemler Tablosu

Anayasa maddelerine takılan veya pas geçilen işlemlerin izlendiği tablodur:

* **Tutulan Bilgiler**: Gölge kayıt kimliği, parite adı, analist sinyali (Alım veya Pas), karar kaynağı, gölge kategorisi (Anayasal Risk Engeli, Pas Gözlemi veya Borsada İcra Edilemez Teknik Kayıt), engelleyen madde ve gerekçesi, uygulanan boyutlama kuralı, hesaplanan anayasal tutar, giriş satış fiyatı, komisyon oranı, kayıt zamanı, 15. dakika hedef ve gerçek değerlendirme zamanları, 15. dakika çıkış alış fiyatı ve net sonucu, 60. dakika hedef ve gerçek değerlendirme zamanları, 60. dakika çıkış alış fiyatı ve net sonucu, doğrulama notu ve gözlem durumu.

---

## 6. Önerilen Sistem Yönergesi (Prompt) Çerçeveleri

### A. Analist Ajan Yönergesi

* **Rolü**: Piyasa göstergelerini inceleyerek yalnızca nitel sinyal üreten analist.
* **Kısıtlamaları**: Asla işlem tutarı belirlemez, yalnızca Alım veya Pas önerir, emir icra yetkisi yoktur.
* **Çıktı İçeriği**: Parite adı, sinyal yönü ve tek cümlelik teknik gerekçe.

### B. Yatırım Anayasası Derleyicisi Yönergesi

* **Rolü**: Kullanıcının doğal dilde yazdığı yatırım tercihlerini yapılandırılmış kural parametrelerine çeviren derleyici.
* **Kısıtlamaları**: Kullanıcının girdiği kural sert güvenlik tavanlarını aşarsa derleyici bunu ham talep olarak iletir; kural motoru ise değeri sert tavana indirgeyerek ekranda *"Kullanıcı kuralı sert tavan nedeniyle uygulanmadı; etkin değer %25"* bildirimini üretir.

---

## 7. İki Aşamalı Hackathon Uygulama ve Doğrulama Planı

### Faz 1: Öğlene Kadar Hedeflenen Çekirdek ve 6 Zorunlu Doğrulama (Saat 09:00 – 13:00)

Canlı borsa bağlantısı olmadan da uçtan uca çalışan **Sanal Mod Karar $\rightarrow$ Anayasa Denetimi $\rightarrow$ Gölge Kayıt $\rightarrow$ 15 ve 60 Dakika Değerlendirme ve Açık Pozisyon Zarar Kesme Takibi** çekirdeğinin kurulması ve aşağıdaki **6 doğrulama senaryosunun** tamamlanması hedeflenir:

1. **Sert Tavan Doğrulaması**: Kullanılabilir bakiye üzerinden %25 tavanının doğru hesaplandığının kanıtlanması.
2. **Kural Sıkılaştırma ve Açık Red Bildirimi Doğrulaması**: Kullanıcı %80 girdiğinde etkin değerin %25 kaldığının ve açık uyarı mesajının üretildiğinin; kullanıcı %15 girdiğinde ise etkin değerin %15'e sıkılaştırıldığının kanıtlanması.
3. **Minimum Emir Sınırı Çakışması Doğrulaması**: Hesaplanan anayasal tutar minimum emir sınırının altında kaldığında işlemin engellendiğinin ve *"Borsada İcra Edilemez Teknik Kayıt"* olarak ayrıldığının kanıtlanması.
4. **Bayat Veri Engeli Doğrulaması**: Fiyat verisinin yaşı 10 saniyeyi aştığında tüm alım sinyallerinin reddedildiğinin kanıtlanması.
5. **Günlük Gerçekleşmiş Zarar Limiti Doğrulaması**: Evrensel gün içinde kapanan işlemlerin toplam zararı 5 dolara ulaştığında yeni alımların durdurulduğunun kanıtlanması.
6. **Tekrarlanabilir (İdempotent) Gölge Değerlendirme Doğrulaması**: Değerlendirme takipçisi arka arkaya çalıştığında, daha önce hesaplanmış 15. ve 60. dakika sonuçlarının değişmediğinin ve mükerrer yazılmadığının kanıtlanması.

### Faz 2: Öğleden Sonra Entegrasyon ve Canlı Kokpit (Saat 13:00 – 19:30)

1. **Doğrulanmış Borsa Veri Adaptörü**: Eldeki resmi dokümantasyona göre canlı fiyat okuma ve 3 saniye zaman aşımı yapısının adaptöre bağlanması.
2. **Otomatik Yenilenen Canlı Kokpit**: Arayüzün donmaması için Karar Kartları, Açık Pozisyonlar ve Gölge Defter tablolarını 10–15 saniyede bir otomatik yenileyen ekranın devreye alınması.
3. **Yedek Video ve Teslim**: Saat 18:45'te çalışan sistemin 60 saniyelik ekran kaydının alınması ve 19:30'da teslimin tamamlanması.

---

## 8. Sahne İçin 2.5 Dakikalık (150 Saniye) Ölçülü Sunum Akışı

* **00:00 – 00:25 | Problem ve Yaklaşım**:
> *"Sayın jüri, kısıtlı bakiye ve 8 saatlik bir hackathon penceresinde 'Yapay zekâmız yüksek kâr etti' iddiası piyasa koşullarına bağlı bir rastlantıdır. Gerçek bir otonom ajanın güvenilirliği kâr iddiasından değil; sermayeyi nasıl koruduğundan ve hangi işlemi NEDEN yapmadığından anlaşılır."*


* **00:25 – 01:05 | Yatırım Anayasası ve Kesin Yetki Ayrılığı**:
> *"Tasarladığımız mimaride dil modeli asla işlem tutarı belirlemez ve doğrudan emir atamaz; yalnızca nitel sinyal önerir. İşlem tutarını kurallara bağlı pozisyon boyutlayıcımız hesaplar. Kullanıcı Türkçe olarak 'Bakiyemin %80'i ile AVAX al' yazsa bile, sistem bunu sessizce geçiştirmez; ekranda 'Kullanıcı kuralı sert tavan nedeniyle uygulanmadı, etkin değer %25' uyarısını gösterir. Hesaplanan tutar borsa minimum emir sınırının altındaysa işlemi güvenle engeller."*


* **01:05 – 01:45 | Karar Kartları, Açık Pozisyon Takipçisi ve Gölge Defter**:
> *"Varsayılan olarak güvenli sanal modda çalışan kokpitimize bakalım. Onaylanan işlemlerde açık pozisyon takipçimiz anlık zarar kesme kontrolü yaparken; alış-satış makası sınırını aşan veya izinli listede olmayan işlemler kırmızı rozetle engellenir ve Gölge Defter'e kaydedilir. Gölge Defter bu işlemleri 15 ve 60 dakika boyunca gerçek alış-satış fiyatları ve komisyonlarla izler."*


* **01:45 – 02:15 | Gözlenen Sonuçlar (Gerçek veya Etiketli Demo Verisiyle)**:
> *"Bugünkü çalışma döngümüzde (veya örnek demo senaryomuzda) Anayasa'nın Madde 3 alış-satış makası filtresiyle durdurduğu icra edilebilir işlemleri görüyorsunuz. Gölge Defter takibimize göre, bu işlemlere girilmiş olsaydı gözlenen varsayımlar altında olası bir net zarar oluşacaktı. Sistemimiz bu riski görünür kıldı ve sermayeyi korudu."*


* **02:15 – 02:30 | Kapanış**:
> *"AVAX merkezli parite yapısıyla Team1 ekosistemine uyumlu, kararları kurallarla denetlenen ve yapmadığı işlemlerin de hesabını veren 'Gölge Defter + Yatırım Anayasası' karşınızda. Teşekkür ederiz."*
