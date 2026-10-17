# Rol: Anayasa / risk motoru

Deterministik kurallar: `src/golge_defter/risk.py`. Ağ veya LLM **yok**.

## Ne zaman bu role geçilir

- Yeni risk kuralı veya `Decision` açıklaması
- `tighten_position_limit` ile kullanıcı sıkılaştırması
- Pozisyon boyutu / spread / günlük zarar mantığı

## Kurallar

1. Mevcut `evaluate()` sözleşmesini koru; kırıcı değişiklik → önce test güncelle
2. Kurallar **yalnızca sıkılaştırılabilir** (README tablosu)
3. `TECHNICAL_BLOCK` ≠ `SHADOW_RISK` (minimum emir ayrımı korunur)
4. Her yeni red yolu için **en az bir** `tests/test_risk.py` senaryosu

## Değişiklik boyutu

- Tek PR/faz: en fazla **bir** yeni kural veya **bir** net bugfix
- Refactor yasak (isim değişikliği turu ayrı faz)

## Test

```bash
pytest -q -n auto tests/test_risk.py
python -m golge_defter.demo
```

Demo çıktısı değiştiyse raporda **hangi senaryo** etkilendiğini yaz.

## Faz raporu

- Kural tablosu satırı (varsa)
- Önce/sonra karar örneği (status + rule)
