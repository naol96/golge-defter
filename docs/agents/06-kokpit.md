# Rol: Kokpit (Streamlit)

Son faz: karar kartları ve otomatik yenilenen özet. **İş mantığı burada yazılmaz.**

## Kapsam

- `src/golge_defter/ui/app.py` veya repo kökünde `app.py` (tek giriş)
- Okuma: ledger + son `Decision` listesi
- Gösterim: parite, status, rule, tutar, spread, analist gerekçesi
- Otomatik yenileme: `st.fragment` veya `st.rerun` ile **≤30 sn** (hackathon demo)

## Yapma

- Risk kurallarını UI içinde tekrar implemente etme → `evaluate` çağır
- Gizli anahtar alanı (MVP'de gerek yok)

## Test

- UI için zorunlu E2E yok; `tests/test_ui_import.py` yalnızca modül import smoke
- Mantık testleri paper/ledger/risk dosyalarında kalır
- Paralel: `pytest -q -n auto` (tüm paket)

## Faz raporu

- Ekran görüntüsü yolu veya metin mockup
- Çalıştırma: `streamlit run ...` komutu
