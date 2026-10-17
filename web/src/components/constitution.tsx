import { useState } from "react";
import type { DataSource } from "../api/client";
import type { SimulationResult, Snapshot } from "../api/types";
import { fmtDecimal, fmtPct, sumDecimals } from "../lib/format";
import { Empty, Meter, Panel } from "./ui";

/** Sum of open notional / balance, computed on display only. */
function exposure(snap: Snapshot): { used: string; balance: number } {
  const balance = Number(snap.paper_balance_usdt ?? 0);
  const used = sumDecimals(snap.open_positions.map((p) => p.notional_usdt));
  return { used, balance };
}

export function ConstitutionGrid({ snap }: { snap: Snapshot }) {
  const c = snap.constitution;
  const { used, balance } = exposure(snap);
  const exposurePct = balance > 0 ? (Number(used) / balance) * 100 : 0;
  const open = snap.open_positions.length;
  const cards: { k: string; title: string; value: string; desc: string; meter?: JSX.Element; tag?: string }[] = [
    {
      k: "position",
      title: "Tek işlem tavanı",
      value: fmtPct(c.tek_islem_tavan_pct, 2),
      desc: "Kullanılabilir bakiyeye göre. Kullanıcı yalnızca düşürebilir.",
      tag: "sıkılaştırılabilir",
    },
    {
      k: "exposure",
      title: "Toplam açık risk",
      value: fmtPct(c.max_toplam_risk_pct, 0),
      desc: `Şu an ${fmtPct(exposurePct, 1)} kullanımda (${fmtDecimal(used, 2)} USDT).`,
      meter: <Meter value={exposurePct} max={100} limit={c.max_toplam_risk_pct} tone={exposurePct >= c.max_toplam_risk_pct ? "danger" : exposurePct >= c.max_toplam_risk_pct * 0.8 ? "warn" : "accent"} label="Toplam risk kullanımı" />,
    },
    {
      k: "positions",
      title: "Açık pozisyon",
      value: `${open} / ${c.max_acik_pozisyon}`,
      desc: "Aynı anda açık kalabilecek en fazla PAPER pozisyon.",
      meter: <Meter value={open} max={c.max_acik_pozisyon} tone={open >= c.max_acik_pozisyon ? "danger" : "accent"} label="Açık pozisyon doluluğu" />,
    },
    {
      k: "spread",
      title: "Makas tavanı",
      value: fmtPct(c.max_spread_pct, 2),
      desc: "Alış-satış makası bu oranı aşarsa giriş yok.",
      tag: "sıkılaştırılabilir",
    },
    { k: "stop", title: "Stop-loss", value: fmtPct(c.stop_loss_pct, 1), desc: "Girişten itibaren zorunlu zarar kesme mesafesi." },
    {
      k: "daily",
      title: "Günlük zarar sınırı",
      value: `≤ ${fmtDecimal(c.gunluk_zarar_usdt, 0)} USDT`,
      desc: `Gün başı bakiyenin ${fmtPct(c.gunluk_zarar_pct, 0)} sınırıyla karşılaştırılır; daha küçük limit uygulanır.`,
    },
    { k: "cooldown", title: "Parite bekleme", value: `${c.bekleme_dk} dk`, desc: "Aynı paritede kapanış sonrası yeniden giriş yok." },
    {
      k: "observe",
      title: "Minimum emir",
      value: "Parite bazında",
      desc: "Adaptörün bildirdiği minimumun altındaki aday teknik kayıttır. Sabit 40 USDT eşiği uygulanmaz.",
    },
  ];
  return (
    <div className="rule-grid">
      {cards.map((card, i) => (
        <article className="rule-card" key={card.k}>
          <span className="rule-no">§{String(i + 1).padStart(2, "0")}</span>
          <h3>{card.title}</h3>
          <strong className="rule-value">{card.value}</strong>
          {card.meter}
          <p>{card.desc}</p>
          {card.tag && <span className="rule-tagline">{card.tag}</span>}
        </article>
      ))}
    </div>
  );
}

const PRESETS = ["Bakiyemin %80'i ile al", "Bakiyemin %10'u ile al", "Makas %0,1 olsun", "Makas %0,5 olsun", "Tavanı %25 yap"];

interface Attempt {
  text: string;
  result?: SimulationResult;
  error?: string;
}

export function Simulator({ source, snap }: { source: DataSource; snap: Snapshot | null }) {
  const [text, setText] = useState(PRESETS[0]!);
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<Attempt[]>([]);
  const basePos = snap?.constitution.tek_islem_tavan_pct ?? 25;
  const baseSpread = snap?.constitution.max_spread_pct ?? 0.15;

  async function run(input: string) {
    setText(input);
    setBusy(true);
    try {
      const result = await source.simulate(input);
      setHistory((h) => [{ text: input, result }, ...h].slice(0, 6));
    } catch (e) {
      setHistory((h) => [{ text: input, error: (e as Error).message }, ...h].slice(0, 6));
    } finally {
      setBusy(false);
    }
  }

  const latest = history[0];
  const res = latest?.result;
  const tightened =
    res && (res.effective.max_position_fraction_pct < basePos || res.effective.max_spread_fraction_pct < baseSpread);

  return (
    <Panel
      id="simulator"
      eyebrow="Karar laboratuvarı"
      title="Anayasaya meydan oku"
      className="simulator"
      footer={
        <>
          <span className="badge badge-muted">SİMÜLASYON</span>
          <span>Veritabanına yazılmaz. Yetki kullanıcıda, sınır anayasada.</span>
        </>
      }
    >
      <p className="hint">
        Doğal dilde bir talep yaz. Sistem sert sınırları gevşetmeni reddeder, sıkılaştırmanı kabul eder.
      </p>
      <form
        className="sim-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (text.trim()) void run(text);
        }}
      >
        <label htmlFor="sim-input" className="sr-only">
          Yatırım talebin
        </label>
        <input id="sim-input" value={text} onChange={(e) => setText(e.target.value)} autoComplete="off" maxLength={200} />
        <button type="submit" className="btn btn-primary" disabled={busy || !text.trim()}>
          {busy ? "Deneniyor…" : "Test et ↗"}
        </button>
      </form>
      <div className="presets" aria-label="Örnek talepler">
        {PRESETS.map((p) => (
          <button key={p} type="button" className="chip" onClick={() => void run(p)} disabled={busy}>
            {p}
          </button>
        ))}
      </div>

      <div className="sim-result" role="status" aria-live="polite">
        {!latest && <span className="muted">Sonuç burada görünecek.</span>}
        {latest?.error && <span className="error-text">{latest.error}</span>}
        {res && (
          <>
            <div className={`verdict ${tightened ? "verdict-ok" : "verdict-guard"}`}>
              <span aria-hidden="true">{tightened ? "✓" : "⛉"}</span>
              <div>
                <strong>{tightened ? "Sıkılaştırma kabul edildi" : "Sert sınır korundu"}</strong>
                <p>{res.message}</p>
              </div>
            </div>
            <div className="compare">
              <CompareRow label="Tek işlem tavanı" base={basePos} eff={res.effective.max_position_fraction_pct} scale={100} digits={2} />
              <CompareRow label="Makas tavanı" base={baseSpread} eff={res.effective.max_spread_fraction_pct} scale={baseSpread * 1.6} digits={3} />
            </div>
          </>
        )}
      </div>

      {history.length > 1 && (
        <details className="sim-history">
          <summary>Önceki denemeler ({history.length - 1})</summary>
          <ul>
            {history.slice(1).map((h, i) => (
              <li key={i}>
                <button type="button" className="link" onClick={() => setText(h.text)}>
                  “{h.text}”
                </button>
                <span className="muted">{h.error ?? h.result?.message}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </Panel>
  );
}

function CompareRow({ label, base, eff, scale, digits }: { label: string; base: number; eff: number; scale: number; digits: number }) {
  const changed = eff < base;
  return (
    <div className="compare-row">
      <span className="compare-label">{label}</span>
      <div className="compare-bars">
        <span className="cbar cbar-base" style={{ width: `${Math.min(100, (base / scale) * 100)}%` }}>
          <em>Sert sınır {fmtPct(base, digits)}</em>
        </span>
        <span className={`cbar ${changed ? "cbar-eff" : "cbar-same"}`} style={{ width: `${Math.min(100, (eff / scale) * 100)}%` }}>
          <em>Etkin {fmtPct(eff, digits)}</em>
        </span>
      </div>
    </div>
  );
}

export function Positions({ snap }: { snap: Snapshot }) {
  const c = snap.constitution;
  if (!snap.open_positions.length) {
    return <Empty title="Açık PAPER pozisyon yok">Anayasadan geçen bir aday PAPER olarak açıldığında burada izlenir.</Empty>;
  }
  return (
    <ul className="positions">
      {snap.open_positions.map((p) => {
        const entry = Number(p.entry_price);
        const stop = Number(p.stop_loss_price);
        const dist = entry > 0 ? ((entry - stop) / entry) * 100 : 0;
        return (
          <li key={p.id} className="position">
            <div className="position-head">
              <strong>{p.symbol}</strong>
              <span className="badge badge-ok">
                <i className="dot pulse" /> {p.status} · PAPER
              </span>
            </div>
            <div className="position-grid">
              <span>
                <small>Tutar</small>
                {fmtDecimal(p.notional_usdt, 2)} USDT
              </span>
              <span>
                <small>Giriş</small>
                {fmtDecimal(p.entry_price, 2)}
              </span>
              <span>
                <small>Stop</small>
                {fmtDecimal(p.stop_loss_price, 2)}
              </span>
            </div>
            <div className="stop-track" aria-label={`Stop girişin ${fmtPct(dist, 2)} altında`}>
              <span className="stop-mark" style={{ left: 0 }}>
                stop
              </span>
              <span className="stop-gap" />
              <span className="stop-mark entry">giriş</span>
            </div>
            <small className="muted">
              Stop mesafesi {fmtPct(dist, 2)} · anayasa sınırı {fmtPct(c.stop_loss_pct, 1)}
            </small>
          </li>
        );
      })}
    </ul>
  );
}
