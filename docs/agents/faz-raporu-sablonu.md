# Faz raporu — <FAZ_ID>: <kısa başlık>

- **Tarih:** YYYY-MM-DD
- **Rol:** `docs/agents/XX-....md`
- **Roadmap maddesi:** `docs/roadmap.md` içindeki …
- **Ajan(lar):** …

## Hedef

Bu fazda tamamlanması gereken tek cümle.

## Yapılan değişiklikler

| Dosya | Özet |
| --- | --- |
| `path/to/file` | Ne değişti (1 satır) |

```bash
# Faz sonu diff özeti (komut çıktısını yapıştır)
git diff --stat HEAD~1..HEAD
# veya çalışma ağacı:
git diff --stat
```

## Test sonuçları

| Komut | Sonuç |
| --- | --- |
| `pytest -q -n auto` | PASS / FAIL (sayı) |
| `python -m golge_defter.demo` | PASS / FAIL |
| CI | bekliyor / yeşil / kırmızı |

Paralel test notu: hangi dosyalar eş zamanlı koşturuldu.

## Davranış örnekleri

MOCK etiketli kısa log veya tablo (en fazla 5 satır).

## Bilinçli ertelemeler

- …

## Sonraki faz

- Faz …: …
- Risk / blokör: …
