import { useMemo, useRef, useState } from "react";
import type { Analytics, CountMap, Outcome } from "../api/types";
import { fmtInt, fmtPct, fmtTime } from "../lib/format";
import { CATEGORY_META, RULE_META, STATUS_ORDER, ruleLabel, statusMeta } from "../lib/labels";
import { Empty, FloatTip, Pnl, Swatch } from "./ui";

const sumCounts = (c: CountMap) => Object.values(c).reduce((a, b) => a + b, 0);

export function Legend({ counts, onToggle, hidden }: { counts?: CountMap; onToggle?: (s: string) => void; hidden?: Set<string> }) {
  return (
    <ul className="legend" aria-label="Lejant">
      {STATUS_ORDER.map((s) => {
        const meta = statusMeta(s);
        const off = hidden?.has(s);
        const content = (
          <>
            <Swatch color={meta.color} />
            <span>{meta.label}</span>
            {counts && <b>{fmtInt(counts[s] ?? 0)}</b>}
          </>
        );
        return (
          <li key={s} className={off ? "off" : ""}>
            {onToggle ? (
              <button type="button" aria-pressed={!off} onClick={() => onToggle(s)}>
                {content}
              </button>
            ) : (
              content
            )}
          </li>
        );
      })}
    </ul>
  );
}

/** 100% stacked bar of the decision mix; every segment is direct-labelled when it fits. */
export function DecisionMix({ summary }: { summary: CountMap }) {
  const total = sumCounts(summary);
  const [hover, setHover] = useState<{ s: string; x: number; y: number } | null>(null);
  if (!total) return <Empty title="Henüz karar yok">Worker ilk kararı yazdığında dağılım burada görünür.</Empty>;
  return (
    <div className="mix">
      <div className="mix-bar" role="img" aria-label={STATUS_ORDER.map((s) => `${statusMeta(s).label} ${summary[s] ?? 0}`).join(", ")}>
        {STATUS_ORDER.filter((s) => summary[s]).map((s) => {
          const pct = ((summary[s] ?? 0) / total) * 100;
          return (
            <span
              key={s}
              className="mix-seg"
              style={{ flexGrow: summary[s], background: statusMeta(s).color }}
              onPointerMove={(e) => setHover({ s, x: e.clientX, y: e.clientY })}
              onPointerLeave={() => setHover(null)}
            >
              {pct >= 9 && <span className="mix-label">{fmtPct(pct, 0)}</span>}
            </span>
          );
        })}
      </div>
      <Legend counts={summary} />
      {hover && (
        <FloatTip x={hover.x} y={hover.y}>
          <strong>{statusMeta(hover.s).label}</strong>
          <span>
            {fmtInt(summary[hover.s])} karar · {fmtPct(((summary[hover.s] ?? 0) / total) * 100, 1)}
          </span>
          <small>{statusMeta(hover.s).help}</small>
        </FloatTip>
      )}
    </div>
  );
}

/** Stacked columns per time bucket with a column-wide hover target and tooltip. */
export function Timeline({ data, hidden }: { data: Analytics; hidden: Set<string> }) {
  const wrap = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<{ i: number; x: number; y: number } | null>(null);
  const series = STATUS_ORDER.filter((s) => !hidden.has(s));
  const buckets = data.timeline;
  const max = Math.max(1, ...buckets.map((b) => series.reduce((a, s) => a + (b.counts[s] ?? 0), 0)));
  const niceMax = niceCeil(max);
  const W = 720;
  const H = 220;
  const pad = { l: 34, r: 8, t: 10, b: 26 };
  const iw = W - pad.l - pad.r;
  const ih = H - pad.t - pad.b;
  const band = iw / Math.max(1, buckets.length);
  const barW = Math.min(24, band * 0.7);
  const y = (v: number) => pad.t + ih - (v / niceMax) * ih;
  const ticks = [0, niceMax / 2, niceMax];
  const labelEvery = Math.ceil(buckets.length / 8);

  if (!buckets.some((b) => sumCounts(b.counts))) {
    return <Empty title="Bu pencerede karar yok">Zaman aralığını genişletmeyi deneyin.</Empty>;
  }

  const hb = hover ? buckets[hover.i] : null;
  return (
    <div className="chart" ref={wrap}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img" aria-label="Zamana göre karar dağılımı">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} className={t === 0 ? "axis" : "grid"} />
            <text x={pad.l - 8} y={y(t)} className="tick" textAnchor="end" dominantBaseline="middle">
              {fmtInt(t)}
            </text>
          </g>
        ))}
        {buckets.map((b, i) => {
          const cx = pad.l + band * i + band / 2;
          let acc = 0;
          const segs = series
            .filter((s) => b.counts[s])
            .map((s) => {
              const v = b.counts[s] ?? 0;
              const y0 = y(acc);
              acc += v;
              return { s, y0, y1: y(acc) };
            });
          return (
            <g key={b.t} className={hover && hover.i !== i ? "dim" : ""}>
              {segs.map((seg, k) => {
                const top = k === segs.length - 1;
                const h = Math.max(0, seg.y0 - seg.y1 - (top ? 0 : 2));
                return top ? (
                  <path key={seg.s} d={roundTopRect(cx - barW / 2, seg.y1, barW, seg.y0 - seg.y1, 3)} fill={statusMeta(seg.s).color} />
                ) : (
                  <rect key={seg.s} x={cx - barW / 2} y={seg.y1 + 2} width={barW} height={h} fill={statusMeta(seg.s).color} />
                );
              })}
              {i % labelEvery === 0 && (
                <text x={cx} y={H - 8} className="tick" textAnchor="middle">
                  {fmtTime(b.t, true)}
                </text>
              )}
              <rect
                x={pad.l + band * i}
                y={pad.t}
                width={band}
                height={ih}
                fill="transparent"
                onPointerMove={(e) => setHover({ i, x: e.clientX, y: e.clientY })}
                onPointerLeave={() => setHover(null)}
              />
            </g>
          );
        })}
      </svg>
      {hb && hover && (
        <FloatTip x={hover.x} y={hover.y}>
          <strong>
            {fmtTime(hb.t, true)} – {fmtTime(hb.t + data.window.bucket_minutes * 60, true)}
          </strong>
          {STATUS_ORDER.map((s) => (
            <span key={s} className="tip-row">
              <Swatch color={statusMeta(s).color} />
              {statusMeta(s).label}
              <b>{fmtInt(hb.counts[s] ?? 0)}</b>
            </span>
          ))}
          <small>Toplam {fmtInt(sumCounts(hb.counts))} karar</small>
        </FloatTip>
      )}
    </div>
  );
}

export function TimelineTable({ data }: { data: Analytics }) {
  return (
    <div className="table-wrap" tabIndex={0} role="region" aria-label="Zaman serisi tablosu">
      <table className="table compact">
        <thead>
          <tr>
            <th scope="col">Aralık</th>
            {STATUS_ORDER.map((s) => (
              <th key={s} scope="col" className="num">
                {statusMeta(s).short}
              </th>
            ))}
            <th scope="col" className="num">
              Toplam
            </th>
          </tr>
        </thead>
        <tbody>
          {data.timeline
            .filter((b) => sumCounts(b.counts))
            .reverse()
            .map((b) => (
              <tr key={b.t}>
                <td className="mono">{fmtTime(b.t, true)}</td>
                {STATUS_ORDER.map((s) => (
                  <td key={s} className="num">
                    {b.counts[s] ?? 0}
                  </td>
                ))}
                <td className="num strong">{sumCounts(b.counts)}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

/** Which constitution rules fire most, split by the decision class they produced. */
export function RuleBars({ rules, onPick }: { rules: Analytics["rules"]; onPick?: (rule: string) => void }) {
  const [hover, setHover] = useState<{ rule: string; x: number; y: number } | null>(null);
  if (!rules.length) return <Empty title="Kural kaydı yok" />;
  const max = Math.max(...rules.map((r) => r.total));
  const total = rules.reduce((a, r) => a + r.total, 0);
  return (
    <ol className="rulebars">
      {rules.map((r) => (
        <li key={r.rule}>
          <button
            type="button"
            className="rulebar"
            onClick={() => onPick?.(r.rule)}
            onPointerMove={(e) => setHover({ rule: r.rule, x: e.clientX, y: e.clientY })}
            onPointerLeave={() => setHover(null)}
            title={RULE_META[r.rule]?.detail}
          >
            <span className="rulebar-label">
              {ruleLabel(r.rule)} <code>{r.rule}</code>
            </span>
            <span className="rulebar-track">
              <span className="rulebar-fill" style={{ width: `${(r.total / max) * 100}%` }}>
                {STATUS_ORDER.filter((s) => r.by_status[s]).map((s) => (
                  <span key={s} style={{ flexGrow: r.by_status[s], background: statusMeta(s).color }} />
                ))}
              </span>
            </span>
            <span className="rulebar-value">{fmtInt(r.total)}</span>
          </button>
        </li>
      ))}
      {hover &&
        (() => {
          const r = rules.find((x) => x.rule === hover.rule)!;
          return (
            <FloatTip x={hover.x} y={hover.y}>
              <strong>
                {ruleLabel(r.rule)} · {fmtInt(r.total)} ({fmtPct((r.total / total) * 100, 1)})
              </strong>
              <small>{RULE_META[r.rule]?.detail}</small>
              {STATUS_ORDER.filter((s) => r.by_status[s]).map((s) => (
                <span key={s} className="tip-row">
                  <Swatch color={statusMeta(s).color} />
                  {statusMeta(s).label}
                  <b>{fmtInt(r.by_status[s])}</b>
                </span>
              ))}
              {onPick && <small>Tıkla: karar akışında filtrele</small>}
            </FloatTip>
          );
        })()}
    </ol>
  );
}

export function SymbolBars({ symbols }: { symbols: Analytics["symbols"] }) {
  if (!symbols.length) return null;
  const max = Math.max(...symbols.map((s) => s.total));
  return (
    <ul className="symbolbars">
      {symbols.map((s) => (
        <li key={s.symbol}>
          <span className="sym">{s.symbol}</span>
          <span className="rulebar-track">
            <span className="rulebar-fill" style={{ width: `${(s.total / max) * 100}%` }}>
              {STATUS_ORDER.filter((k) => s.by_status[k]).map((k) => (
                <span key={k} style={{ flexGrow: s.by_status[k], background: statusMeta(k).color }} title={`${statusMeta(k).label}: ${s.by_status[k]}`} />
              ))}
            </span>
          </span>
          <span className="rulebar-value">{fmtInt(s.total)}</span>
        </li>
      ))}
    </ul>
  );
}

/**
 * Counterfactual outcomes per category × horizon. Shows the up/down split as a
 * diverging bar around a neutral center, plus avg/sum. Never framed as "avoided loss".
 */
export function OutcomeMatrix({ outcomes }: { outcomes: Outcome[] }) {
  const rows = useMemo(() => {
    const order = ["CONSTITUTIONAL_RISK_BLOCK", "PASS_OBSERVATION", "TECHNICAL_UNEXECUTABLE"];
    return [...outcomes].sort(
      (a, b) => order.indexOf(a.category) - order.indexOf(b.category) || a.horizon_minutes - b.horizon_minutes,
    );
  }, [outcomes]);
  if (!rows.length) return <Empty title="Tamamlanmış gözlem yok">15 dk dolduğunda ilk karşı-olgusal sonuçlar görünür.</Empty>;
  const maxSide = Math.max(1, ...rows.map((r) => Math.max(r.positive, r.negative)));
  return (
    <div className="table-wrap" tabIndex={0} role="region" aria-label="Karşı-olgusal sonuç matrisi">
      <table className="table outcome-table">
        <thead>
          <tr>
            <th scope="col">Sınıf</th>
            <th scope="col">Pencere</th>
            <th scope="col" className="num">
              n
            </th>
            <th scope="col" className="center">
              <span className="neg-label">▼ net zarar</span> · <span className="pos-label">net kâr ▲</span>
            </th>
            <th scope="col" className="num">
              Ort.
            </th>
            <th scope="col" className="num">
              Toplam
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const meta = CATEGORY_META[r.category];
            return (
              <tr key={`${r.category}-${r.horizon_minutes}`}>
                <th scope="row">
                  <span className="cat">
                    <Swatch color={statusMeta(meta?.status).color} />
                    {meta?.label ?? r.category}
                  </span>
                </th>
                <td className="mono">{r.horizon_minutes} dk</td>
                <td className="num">{fmtInt(r.count)}</td>
                <td>
                  <div className="diverge" title={`${r.negative} aşağı · ${r.positive} yukarı`}>
                    <span className="d-neg">
                      <span style={{ width: `${(r.negative / maxSide) * 100}%` }} />
                      <em>{r.negative}</em>
                    </span>
                    <span className="d-mid" />
                    <span className="d-pos">
                      <span style={{ width: `${(r.positive / maxSide) * 100}%` }} />
                      <em>{r.positive}</em>
                    </span>
                  </div>
                </td>
                <td className="num">
                  <Pnl value={r.avg_pnl_usdt} places={6} unit={false} />
                </td>
                <td className="num">
                  <Pnl value={r.sum_pnl_usdt} places={6} unit={false} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** Ring progress for horizon completion. */
export function Ring({ value, total, label }: { value: number; total: number; label: string }) {
  const pct = total ? value / total : 0;
  const r = 26;
  const c = 2 * Math.PI * r;
  return (
    <figure className="ring">
      <svg viewBox="0 0 64 64" role="img" aria-label={`${label}: ${value}/${total}`}>
        <circle cx="32" cy="32" r={r} className="ring-track" />
        <circle
          cx="32"
          cy="32"
          r={r}
          className="ring-fill"
          strokeDasharray={`${c * pct} ${c}`}
          transform="rotate(-90 32 32)"
        />
        <text x="32" y="33" textAnchor="middle" dominantBaseline="middle">
          {fmtPct(pct * 100, 0)}
        </text>
      </svg>
      <figcaption>
        <strong>{label}</strong>
        <span>
          {fmtInt(value)} / {fmtInt(total)} tamamlandı
        </span>
      </figcaption>
    </figure>
  );
}

function niceCeil(v: number): number {
  if (v <= 4) return 4;
  const pow = 10 ** Math.floor(Math.log10(v));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * pow).find((n) => n >= v) ?? v;
  // Keep the midpoint tick an integer count.
  return step % 2 === 0 ? step : Math.ceil(step / 2) * 2;
}

function roundTopRect(x: number, y: number, w: number, h: number, r: number): string {
  const rr = Math.min(r, h, w / 2);
  if (h <= 0) return "";
  return `M${x},${y + h}V${y + rr}Q${x},${y} ${x + rr},${y}H${x + w - rr}Q${x + w},${y} ${x + w},${y + rr}V${y + h}Z`;
}
