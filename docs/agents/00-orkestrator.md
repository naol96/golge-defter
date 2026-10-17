# Rol: Orkestratör

Fazları sıraya koyar, ajanları çakışmadan yönlendirir, **faz raporunu** tamamlar.

## Sorumluluk

- `docs/roadmap.md` maddelerini **tek tek** fazlara böl (1–3 saatlik dilimler).
- Hangi rol dosyasının aktif olduğunu net söyle.
- Paralel iş: test yazımı + implementasyon **farklı dizinlerde**.
- Faz bitince `docs/reports/` altında rapor oluştur.

## Faz planı (önerilen sıra)

| Faz | Roadmap | Ana rol |
| --- | --- | --- |
| A | Hazır | Doğrulama: `pytest -q`, demo, CI yeşil |
| B | OKX ATK market adaptör | `01-piyasa-adaptor.md` |
| C | AI analist adaptör | `02-analist.md` |
| D | SQLite shadow/executed | `04-golge-defter.md` |
| E | 15/60 dk gözlem | `04-golge-defter.md` |
| F | PAPER pozisyon + stop | `05-paper-icra.md` |
| G | Streamlit kokpit | `06-kokpit.md` |
| H | Kill-switch / LIVE inceleme | **durdur** — ayrı güvenlik fazı, hackathon sonrası |

## Her faz başlangıcı çıktısı

```text
Faz: <id>
Hedef: <roadmap maddesi>
Rol: <dosya>
Dokunulacak dosyalar: <liste>
Dokunulmayacak: <liste>
Test komutu: pytest -q [-n auto] && python -m golge_defter.demo
```

## Her faz bitişi çıktısı

- `docs/agents/faz-raporu-sablonu.md` doldurulmuş hali
- `git diff --stat` özetini rapora ekle
- Başarısız test veya bilinçli erteleme **açık** yazılır

## Kullanıcıya özet

En fazla **5 satır**: ne bitti, test durumu, sonraki faz.
