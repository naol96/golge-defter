# Gölge Defter + Yatırım Anayasası

**Shadow Ledger + Investment Constitution** — OKX TR × Team1 Türkiye Agentic Hackathon (Ankara, 17 Ekim 2026)

> **Durum:** Başlangıç deposu / erken aşama prototip. Piyasa bağlantısı ve OKX Agent Trade Kit (ATK) entegrasyonu henüz uygulanmadı. Bu depoda gerçek emir gönderimi **yoktur**.

## Amaç

Kâr vaat eden bir alım satım botu yerine, yapay zekâ sinyallerini deterministik yatırım kurallarıyla denetleyen ve **engellenen ya da pas geçilen** aday işlemleri Gölge Defter'de görünür kılan bir mimari.

- **Analist:** `BUY` veya `PASS` ve kısa gerekçe önerir; **tutar üretmez ve emir göndermez**.
- **Anayasa:** Sert risk kurallarını uygular; kullanıcı bunları yalnızca sıkılaştırabilir.
- **Pozisyon boyutlama:** Kullanılabilir bakiyeden hesaplanır; minimum emir tutarı tavanı ihlal ettirmez.
- **Gölge Defter:** Risk engeli, pas gözlemi ve teknik olarak icra edilemez kayıtları ayırır.
- **Açık pozisyon takibi:** Sonraki aşamada PAPER pozisyonlarının zarar kesme kontrolünü yönetecek.
- **İcra:** Bu başlangıç sürümünde **yalnızca simülasyon/PAPER**. LIVE bağlantısı bilinçli olarak mevcut değildir.

## Varsayılan sert sınırlar

| Kural | Değer |
| --- | --- |
| Tek işlem tavanı | Kullanılabilir bakiyenin %25'i |
| İzinli pariteler | `AVAX-USDT`, `BTC-USDT`, `ETH-USDT` |
| En yüksek spread | %0,15 |
| Stop-loss sınırı | %2,5 |
| Günlük gerçekleşmiş zarar sınırı | 5 USDT |
| Veri yaşı | En fazla 10 saniye |

## Mevcut prototip

Python bağımlılığı olmadan çalışabilen deterministik **risk/pozisyon karar motoru** ve birim testleri mevcut. Gerçek OKX fiyatları çekilmez, LLM çağrısı yapılmaz ve emir gönderilmez.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest -q
python -m golge_defter.demo
```

Demo senaryoları **MOCK / SIMULATED** olarak etiketlenmiştir; gerçek piyasa verisi veya gerçek başarı ölçümü değildir.

## Hedef akış

```text
OKX ATK / onaylı veri adaptörü (gelecek) 
           ↓
Analist ajan — nitel BUY / PASS (gelecek)
           ↓
Deterministik pozisyon boyutlama
           ↓
Yatırım Anayasası / risk kuralları
           ├─ PASS / BLOCKED → Gölge Defter → 15 & 60 dk ileri gözlem (gelecek)
           └─ APPROVED → PAPER icra → açık pozisyon stop takipçisi (gelecek)
```

## Dosyalar

- `src/golge_defter/risk.py`: Temel anayasa ve risk değerlendirme motoru.
- `src/golge_defter/demo.py`: Açıkça simüle edilmiş kullanım örneği.
- `tests/`: Kritik güvenlik kontrollerinin birim testleri.
- `docs/architecture.md`: Mimari, güvenlik ve değerlendirme standartları.
- `docs/roadmap.md`: Uygulama planı ve tamamlanmamış modüller.
- `AGENTS.md` ve `docs/agents/`: Hackathon ajan rolleri, test disiplini ve faz rapor şablonu.
- `docs/reports/`: Faz sonu değişiklik raporları.
- `scripts/publish.sh`: GitHub CLI ile yeni **private** depo oluşturup push etme yardımcısı.

## Bağlantılar

- [OKX Agent Trade Kit (resmî)](https://github.com/okx/agent-trade-kit)
- [ATK yapılandırma](https://github.com/okx/agent-trade-kit/blob/github-main/docs/configuration.md)

**Uyarı:** Finansal tavsiye değildir. Gerçek işlem yapan bir sistem değildir. Gerçek para kullanmadan önce borsa şartları, yetki modeli, emir semantiği ve takipçi davranışı ayrıca doğrulanmalıdır.
