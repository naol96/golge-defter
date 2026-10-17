# Rol: Analist ajan

Nitel sinyal: `AnalystSignal(pair, direction, reason)` — yalnızca `BUY` veya `PASS`.

## Yetki sınırı (kritik)

- **Tutar üretmez** (`constitutional_amount_usdt` hesaplamaz)
- **Emir göndermez**
- **Anayasa parametrelerini değiştiremez**
- Gerekçe: tek cümle, Türkçe veya İngilizce, spekülatif iddia yerine gözlem

## Kapsam (minimal)

- Modül: `src/golge_defter/analyst.py`
- Fonksiyon örneği: `suggest(pair: str, context: str) -> AnalystSignal`
- LLM kullanılıyorsa: prompt dosyası **tek** (`docs/prompts/analist.md` veya inline sabit string); tool calling ile emir fonksiyonu **tanımlama**

## Entegrasyon

```text
market snapshot → analist → AnalystSignal → evaluate() → Decision
```

Analist `PASS` döndürürse sonuç her zaman `SHADOW_PASS` (mevcut motor).

## Test

- `tests/test_analyst.py`: deterministik stub (LLM yok) ile BUY/PASS ve geçersiz yön reddi
- Entegrasyon: bir test `evaluate` ile analist çıktısını birleştir (tek senaryo yeter)
- Paralel: `pytest -q -n auto tests/test_analyst.py tests/test_risk.py`

## Yapma

- "Kâr garantisi" metni
- Otomatik BUY bias
- Çoklu ajan tartışma protokolü (hackathon sonrası)

## Faz raporu

- Model/API kullanıldı mı (evet/hayır, MOCK modu)
- Örnek 2 sinyal (BUY + PASS)
