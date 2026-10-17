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
3. **ATK:** OKX MCP `market_get_ticker` stdio; başarısızlıkta UI mock'a düşer, karar motoru fail-closed.
4. **Komisyon:** `0.001` varsayımı kodda etiketli (`DEFAULT_FEE_RATE`).
5. **Gölge sınıfları:** `CONSTITUTIONAL_RISK_BLOCK`, `PASS_OBSERVATION`, `TECHNICAL_UNEXECUTABLE`.
6. **Eski API:** `golge_defter.risk` geriye dönük uyumluluk shim'i.
7. **Kill-switch / canlı onay:** Hackathon MVP'de uygulanmadı; spec'teki canlı emir akışı bilinçli olarak kapalı.
