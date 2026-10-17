# Yatırım Anayasası

## Nedir?

Yatırım Anayasası, yapay zekânın önerdiği her işlemin **emir olarak gönderilmeden önce geçmek zorunda olduğu kurallar listesidir.** Yapay zekâ "AVAX al" der; anayasa bu öneriyi kontrol eder ve **izin verir ya da engeller.**

"Anayasa" denmesinin nedeni: sıradan bir ayardan farklı olarak, temel kuralları **kimse gevşetemez.** Ne yapay zekâ ne kullanıcı ne de bir hata. Kullanıcı yalnızca kuralları daha sıkı hale getirebilir.

Önemli bir ayrım: anayasa **ne zaman alınacağına** karar vermez; o yapay zekânın işidir. Anayasa **ne kadar, hangi koşulda ve hangi sınırlar içinde** işlem yapılabileceğine karar verir. Yani strateji değil, güvenlik çerçevesidir.

---

## Anayasayı Kim Belirliyor?

Anayasayı **iki taraf** belirler, ama yetkileri çok farklıdır:

| Kim | Ne belirliyor | Nasıl |
|---|---|---|
| **Sistem (geliştirici ekip)** | **Sert taban kurallar**: %25 tavan, %2.5 zarar kesme, 3 izinli parite vb. | Koda sabit olarak yazılır. Çalışma sırasında kimse değiştiremez |
| **Kullanıcı** | Yalnızca **daha sıkı** kurallar | Doğal dille yazar ("en fazla %15 kullan") |

### Yapay zekâ anayasayı belirlemez

Projede iki yapay zekâ bileşeni vardır ve ikisinin de kural koyma yetkisi yoktur:

- **Analist** (işlem öneren yapay zekâ) anayasayı göremez ve değiştiremez; yalnızca anayasanın denetlediği taraftır.
- **Anayasa Derleyicisi** kullanıcının cümlesini sayıya çevirir ("en fazla %15" → `0.15`). Kararı o vermez; değeri kendisi düzeltmez, kullanıcının talebini olduğu gibi iletir.

### Son kararı kural motoru verir

**Kural motoru**, yapay zekâ olmayan, sabit kurallarla çalışan bir kod parçasıdır. Gelen değeri sert tabanla karşılaştırır: daha sıkıysa uygular, daha gevşekse reddeder ve bunu ekranda gösterir.

> **Taban kuralları ekip koyar, kullanıcı sıkılaştırabilir, son kararı kod verir. Yapay zekâ yalnızca önerir ya da çevirir.**

### Taban değerler neden bu rakamlar?

%25, %2.5 gibi değerler ekibin seçtiği başlangıç değerleridir. Küçük bakiyeli bir kullanıcı için makul bir risk çerçevesi olsun diye seçilmiştir; bilimsel olarak optimize edilmemiştir.

Projenin iddiası rakamların kendisi değil, şu ilkedir: **taban ne olursa olsun, ne yapay zekâ ne de kullanıcı onu gevşetebilir.**

**Gelecek plan:** Gerçek bir üründe taban değerler, hesap açılışında kullanıcının risk profiline göre belirlenip ardından kilitlenebilir.

---

## 7 Sert Kural

Örneklerde bakiye 50 USDT kabul edilmiştir.

| # | Kural | Değer | Neden var? | 50 USDT ile örnek |
|---|---|---|---|---|
| 1 | **Tek işlem tavanı** | Bakiyenin en fazla %25'i | Tek bir yanlış kararın bütün parayı götürmemesi için | Bir işlemde en fazla 12,5 USDT |
| 2 | **Toplam açık risk** | En fazla %50, aynı anda en fazla 2 pozisyon | Küçük işlemlerin üst üste binip bütün parayı bağlamaması için | Aynı anda en fazla 25 USDT piyasada |
| 3 | **İzinli pariteler** | Yalnızca AVAX, BTC, ETH (USDT karşılığı) | Az bilinen, oynak ya da manipülasyona açık coinlerden uzak durmak için | "DOGE al" önerisi doğrudan engellenir |
| 4 | **Maksimum makas** | Alış-satış farkı en fazla %0.15 | Fark açıksa alır almaz zarardasın demektir; piyasa sığ ya da dengesiz | Makas %0.3 ise işlem yapılmaz |
| 5 | **Zorunlu zarar kesme** | Alış fiyatından en fazla %2.5 düşüş | Kaybın büyümeden durdurulması için | 12,5 USDT'lik pozisyonda en fazla ~0,31 USDT kayıp |
| 6 | **Günlük zarar limiti** | Gün başı bakiyesinin %5'i ile 5 USDT sınırından küçüğü | Kötü bir günde zararın birikip kontrolden çıkmaması için | Gün içinde 2,5 USDT kaybedilirse o gün yeni alım yok |
| 7 | **Bekleme süresi** | Aynı paritede kapanıştan sonra 15 dakika | Zarar sonrası "hemen geri alayım" döngüsünü engellemek için | AVAX zararla satıldıysa 15 dakika AVAX alınmaz |

### Anayasadan bağımsız iki teknik kontrol

- **Minimum emir kontrolü:** Hesaplanan tutar borsanın kabul ettiği en küçük emirden azsa işlem yapılmaz ve "teknik kayıt" olarak ayrı tutulur. Kural ihlali sayılmaz.
- **Asgari bakiye kontrolü:** Minimum emir pariteye ve fiyata bağlıdır. %25 ile hesaplanan tutar adaptörden gelen minimumun altındaysa teknik kayıt oluşur; sabit 40 USDT eşiği tek başına risk engeli sayılmaz.

---

## Kullanıcı Kuralları: Sıkılaştırabilir, Gevşetemez

Kullanıcı kendi kurallarını Türkçe, doğal dille yazabilir. Bir yapay zekâ bileşeni (Anayasa Derleyicisi) bu cümleyi sayıya çevirir, kural motoru uygular.

| Kullanıcı yazarsa | Sonuç | Neden |
|---|---|---|
| "Tek işlemde en fazla %15 kullan" | ✅ Etkin değer **%15** | Daha sıkı |
| "Sadece AVAX işlem yap" | ✅ İzinli liste **yalnızca AVAX** | Daha sıkı |
| "Makas en fazla %0.05 olsun" | ✅ Etkin değer **%0.05** | Daha sıkı |
| "Bakiyemin %80'i ile al" | ❌ Etkin değer **%25'te kalır** | Gevşetme; ekranda nedeni açıkça yazar |
| "Zarar kesmeyi kaldır" | ❌ Reddedilir | Sert kural kaldırılamaz |
| "Önceki kuralları yok say" | ❌ Reddedilir | Manipülasyon girişimi |
| "Biraz agresif oyna" | ⏸ Uygulanmaz, sayı istenir | Belirsiz, sayısal karşılığı yok |
| "%15 kullan" ve "%20 kullan" birlikte | ✅ **%15** uygulanır | Çelişkide en sıkı değer seçilir |

Sistem hiçbir kuralı **sessizce** değiştirmez. Reddedilen ya da düşürülen her kural ekranda gerekçesiyle görünür:

> *"Kullanıcı kuralı (%80) sert tavan nedeniyle uygulanmadı; etkin değer %25 olarak korundu."*

---

## Bir Öneri Anayasadan Nasıl Geçer?

Yapay zekâ "AVAX al" dediğinde kontroller sırayla yapılır. İlk takıldığı yerde işlem durur:

1. Parite izinli mi? *(Kural 3)*
2. Bugünkü zarar limiti doldu mu? *(Kural 6)*
3. Bu paritede bekleme süresi geçti mi? *(Kural 7)*
4. Toplam açık risk ve pozisyon sayısı uygun mu? *(Kural 2)*
5. Makas sınırın içinde mi? *(Kural 4)*
6. Tutar hesaplanır: bakiye × etkin yüzde *(Kural 1)*
7. Tutar minimum emri karşılıyor mu? *(Teknik kontrol)*
8. Her şey uygunsa emir gönderilir; zarar kesme seviyesi belirlenir *(Kural 5)*

Engellenen her öneri **hangi maddeye takıldığıyla** birlikte Gölge Defter'e yazılır. 15 ve 60 dakika sonra şu sorunun cevabı hesaplanır: *"Bu kural bizi korudu mu, yoksa kâr mı kaçırttı?"*

---

## Değişiklikler Nasıl Kayıt Altına Alınır?

Hedef mimaride her kural değişikliğinin sürümlenmesi ve zincire sabitlenmesi planlanır. Mevcut MVP kararların kod sürümünü kaydeder; kural başına otomatik sürüm/hash üretimi ve Avalanche'a yazma uygulanmış değildir. `chain/anchor_job.py` yalnızca yerel karar grubu SHA-256 manifesti üretir.

Yerel hash, zincir receipt veya değiştirilemez zaman damgası kanıtı değildir. Mevcut doğrulama sınırları jüri denetim raporunda açıkça ayrılır.

---

## Kısaca

> Yapay zekâ **ne zaman** alınacağını önerir.
> Anayasa **ne kadar ve hangi koşulda** alınabileceğine karar verir.
> Kullanıcı kuralları sıkılaştırabilir, ama kimse gevşetemez.

*Not: Rakamlar (%25, %2.5 vb.) projenin başlangıç değerleridir ve ekipçe değiştirilebilir. Önemli olan mantığın, yani "sert taban + yalnızca sıkılaştırma" ilkesinin korunmasıdır.*

---

## MVP / kod durumu (17 Ekim 2026)

| Madde | Kod (`rules_v2`) | Not |
| --- | --- | --- |
| 1 %25 tavan | Evet | `max_position_fraction` |
| 2 %50 / 2 pozisyon | Evet | `MAX_POSITIONS`, `EXPOSURE` |
| 3 parite listesi | Evet | `PAIR` |
| 4 makas | Evet | `SPREAD` |
| 5 stop | Evet | PAPER `paper_broker` |
| 6 günlük zarar | Evet | min(gün başı bakiye × %5, 5 USDT) |
| 7 bekleme 15 dk | Evet | `COOLDOWN` |
| Min emir | Evet | `TECHNICAL_BLOCK` / gölge teknik |
| Minimum altında gözlem | Evet | `TECHNICAL_BLOCK`; eski OBSERVATION kayıtları risk metriğinden çıkarılır |
| Avalanche hash | Hayır | Faz 2 / bonus |
| Tam Anayasa Derleyicisi | Kısmi | Yalnızca tavan sıkılaştırma |

Canlı worker **15:00 restart** sonrası `rules_v2` etiketi `decisions.rules_version` alanına yazılır; restart öncesi kayıtlar boş veya eski davranıştır.

Jüri denetimi sonrası kod sürümü: `rules_v2_audit1`. Testler ve sınırlamalar: `reports/jury-audit/summary.md`.
