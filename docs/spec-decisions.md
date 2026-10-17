# Spec decisions

## Kaynak belgeler

| Belge | Durum |
|-------|--------|
| `docs/golge_defter_final.md` | Repoda (önceden untracked) |
| `Gölge Defter Yatırım Anayasasıl last.md` | Bulunamadı |
| `OKX_TR_Team1_Agentic_Hackathon_2026_Kaynakli_Arastirma.md` | Bulunamadı |

## Kararlar

1. **MVP modu:** Yalnızca PAPER; LIVE istekleri `LIVE_REJECTED`.
2. **Analist:** Varsayılan `demo_signal` (`origin=DEMO`); gerçek LLM entegrasyonu modüler (`core/analyst.py`).
3. **ATK:** OKX MCP `market_get_ticker` stdio; başarısızlıkta MOCK fiyatla devam edilmez; karar motoru ve takipçiler fail-closed.
4. **Komisyon:** `0.001` varsayımı kodda etiketli (`DEFAULT_FEE_RATE`).
5. **Gölge sınıfları:** `CONSTITUTIONAL_RISK_BLOCK`, `PASS_OBSERVATION`, `TECHNICAL_UNEXECUTABLE`.
6. **Eski API:** `golge_defter.risk` geriye dönük uyumluluk shim'i.
7. **Kill-switch / canlı onay:** Hackathon MVP'de uygulanmadı; spec'teki canlı emir akışı bilinçli olarak kapalı.

## Jüri denetimi düzeltmeleri

- Güncel düzeltme sürümü `rules_v2_audit1`; eski `rules_v2` kayıtları geriye dönük değiştirilmez.
- Günlük gerçekleşmiş zarar sınırı `min(gün başı bakiye × %5, 5 USDT)`; iki sınırdan daha sıkı olanı uygulanır.
- Minimum emir altındaki BUY/PASS adayları risk fırsatı değildir; `TECHNICAL_BLOCK` olarak ayrılır.
- Yerel SHA-256 ve dışarıdan verilen işlem URL'si blockchain doğrulaması değildir. Mevcut kod receipt ve zincirdeki hash eşleşmesini doğrulamaz.
- Mum verisi olmadan yapılan dönem sonu shadow hesabı `stop_dogrulamasi_sinirli` notuyla gösterilir.
- Güncel test ve kalan sınırlar: `reports/jury-audit/summary.md`.
