import { useEffect, useMemo, useRef, useState } from "react";
import type { Analytics, DecisionRow, ShadowRow } from "../api/types";
import { useNow } from "../hooks";
import { fmtDateTime, fmtDecimal, fmtDuration, fmtInt, fmtRelative, fmtTime } from "../lib/format";
import { CATEGORY_META, RULE_META, STATUS_ORDER, isLiveSource, ruleLabel, sourceLabel, statusMeta } from "../lib/labels";
import { Drawer, Empty, KV, Pnl, Segmented, StatusPill } from "./ui";

const PAGE = 25;

function downloadCsv(name: string, header: string[], rows: (string | number | null | undefined)[][]) {
  const cell = (v: unknown) => {
    const s = v == null ? "" : String(v);
    return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const csv = [header, ...rows].map((r) => r.map(cell).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Pager({ page, pages, onPage, total }: { page: number; pages: number; onPage: (p: number) => void; total: number }) {
  if (pages <= 1) return <span className="pager-info">{fmtInt(total)} kayıt</span>;
  return (
    <div className="pager">
      <span className="pager-info">
        {fmtInt(total)} kayıt · sayfa {page + 1}/{pages}
      </span>
      <button type="button" className="btn btn-ghost btn-sm" disabled={page === 0} onClick={() => onPage(page - 1)} aria-label="Önceki sayfa">
        ←
      </button>
      <button type="button" className="btn btn-ghost btn-sm" disabled={page >= pages - 1} onClick={() => onPage(page + 1)} aria-label="Sonraki sayfa">
        →
      </button>
    </div>
  );
}

export interface DecisionFilter {
  status: string;
  rule: string;
  symbol: string;
  origin: string;
  q: string;
}
export const EMPTY_FILTER: DecisionFilter = { status: "ALL", rule: "", symbol: "", origin: "", q: "" };

export function DecisionExplorer({
  data,
  filter,
  onFilter,
  searchRef,
}: {
  data: Analytics;
  filter: DecisionFilter;
  onFilter: (f: DecisionFilter) => void;
  searchRef?: React.RefObject<HTMLInputElement>;
}) {
  const [page, setPage] = useState(0);
  const [open, setOpen] = useState<DecisionRow | null>(null);
  const now = useNow();
  const rows = data.decisions;
  const opts = useMemo(
    () => ({
      rules: [...new Set(rows.map((r) => r.rule))].sort(),
      symbols: [...new Set(rows.map((r) => r.symbol))].sort(),
      origins: [...new Set(rows.map((r) => r.signal_origin))].sort(),
    }),
    [rows],
  );
  const base = useMemo(
    () =>
      rows.filter((r) => {
        if (filter.rule && r.rule !== filter.rule) return false;
        if (filter.symbol && r.symbol !== filter.symbol) return false;
        if (filter.origin && r.signal_origin !== filter.origin) return false;
        if (filter.q) {
          const q = filter.q.toLocaleLowerCase("tr");
          const hay = `${r.id} ${r.symbol} ${r.rule} ${r.explanation} ${r.signal_reason}`.toLocaleLowerCase("tr");
          if (!hay.includes(q)) return false;
        }
        return true;
      }),
    [rows, filter.rule, filter.symbol, filter.origin, filter.q],
  );
  const filtered = filter.status === "ALL" ? base : base.filter((r) => r.status === filter.status);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE));
  useEffect(() => setPage(0), [filter]);
  const visible = filtered.slice(page * PAGE, page * PAGE + PAGE);
  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const r of base) c[r.status] = (c[r.status] ?? 0) + 1;
    return c;
  }, [base]);
  const set = (patch: Partial<DecisionFilter>) => onFilter({ ...filter, ...patch });
  const active = filter.rule || filter.symbol || filter.origin || filter.q || filter.status !== "ALL";

  const linked = open ? data.shadow.filter((s) => s.shadow_id === open.ref_id && open.status !== "APPROVED_PAPER") : [];

  return (
    <>
      <div className="toolbar">
        <Segmented
          label="Karar sınıfı"
          value={filter.status}
          onChange={(status) => set({ status })}
          options={[
            { value: "ALL", label: "Tümü", count: base.length },
            ...STATUS_ORDER.map((s) => ({ value: s as string, label: statusMeta(s).short, count: counts[s] ?? 0 })),
          ]}
        />
        <div className="toolbar-fields">
          <label className="field search">
            <span className="sr-only">Ara</span>
            <input
              ref={searchRef}
              type="search"
              placeholder="Ara: parite, kural, gerekçe…  ( / )"
              value={filter.q}
              onChange={(e) => set({ q: e.target.value })}
            />
          </label>
          <Select label="Parite" value={filter.symbol} options={opts.symbols} onChange={(symbol) => set({ symbol })} />
          <Select label="Kural" value={filter.rule} options={opts.rules} onChange={(rule) => set({ rule })} render={ruleLabel} />
          <Select label="Sinyal" value={filter.origin} options={opts.origins} onChange={(origin) => set({ origin })} render={sourceLabel} />
          {active && (
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => onFilter(EMPTY_FILTER)}>
              Temizle
            </button>
          )}
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() =>
              downloadCsv(
                "golge-kararlar.csv",
                ["id", "zaman", "parite", "durum", "ham_durum", "kural", "aksiyon", "sinyal", "kaynak", "tutar_usdt", "gerekce", "analist_gerekce"],
                filtered.map((r) => [r.id, new Date(r.created_at * 1000).toISOString(), r.symbol, r.status, r.raw_status, r.rule, r.signal_action, r.signal_origin, r.market_source, r.notional_usdt, r.explanation, r.signal_reason]),
              )
            }
          >
            ⤓ CSV
          </button>
        </div>
      </div>

      {visible.length ? (
        <div className="table-wrap" tabIndex={0} role="region" aria-label="Karar listesi">
          <table className="table rows-clickable">
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Zaman</th>
                <th scope="col">Parite</th>
                <th scope="col">Karar</th>
                <th scope="col">Kural</th>
                <th scope="col" className="wide">
                  Gerekçe
                </th>
                <th scope="col">Sinyal / veri</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((r) => (
                <tr key={r.id} onClick={() => setOpen(r)}>
                  <td className="mono muted">
                    <button type="button" className="row-link" onClick={(e) => (e.stopPropagation(), setOpen(r))} aria-label={`Karar ${r.id} detayı`}>
                      {r.id}
                    </button>
                  </td>
                  <td className="mono nowrap" title={fmtDateTime(r.created_at)}>
                    {fmtTime(r.created_at)}
                    <small>{fmtRelative(r.created_at, now)}</small>
                  </td>
                  <th scope="row" className="sym">
                    {r.symbol}
                    <small>{r.signal_action}</small>
                  </th>
                  <td>
                    <StatusPill status={r.status} />
                  </td>
                  <td>
                    <span className="rule-tag" title={RULE_META[r.rule]?.detail}>
                      {ruleLabel(r.rule)}
                    </span>
                  </td>
                  <td className="wide clamp">{r.explanation}</td>
                  <td className="nowrap">
                    <span className={`src ${r.signal_origin === "LLM" ? "src-llm" : ""}`}>{sourceLabel(r.signal_origin)}</span>
                    <small>
                      {isLiveSource(r.market_source) && <i className="live-dot" aria-hidden="true" />}
                      {sourceLabel(r.market_source)}
                    </small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty title={rows.length ? "Filtreyle eşleşen karar yok" : "Henüz karar kaydı yok"}>
          {rows.length ? "Filtreleri gevşetin veya temizleyin." : "Worker çalıştığında kararlar burada akar."}
        </Empty>
      )}
      <div className="table-foot">
        <span className="muted">Son {fmtInt(rows.length)} karar yüklendi</span>
        <Pager page={page} pages={pages} onPage={setPage} total={filtered.length} />
      </div>

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open ? `Karar #${open.id} · ${open.symbol}` : ""}>
        {open && (
          <>
            <div className="drawer-hero">
              <StatusPill status={open.status} />
              {open.raw_status !== open.status && (
                <span className="badge badge-muted" title="Saklanan ham durum; görüntüde teknik olarak sınıflandı">
                  ham: {open.raw_status}
                </span>
              )}
              <p>{statusMeta(open.status).help}</p>
            </div>
            <ol className="journey" aria-label="Kararın yolculuğu">
              <li>
                <span>01 · Veri</span>
                <strong>
                  {isLiveSource(open.market_source) && <i className="live-dot" />}
                  {sourceLabel(open.market_source)}
                </strong>
                <small>{fmtDateTime(open.created_at)}</small>
              </li>
              <li>
                <span>02 · Analist</span>
                <strong>
                  {open.signal_action} · {sourceLabel(open.signal_origin)}
                </strong>
                <small>{open.signal_reason}</small>
              </li>
              <li className="journey-accent">
                <span>03 · Anayasa</span>
                <strong>
                  {ruleLabel(open.rule)} <code>{open.rule}</code>
                </strong>
                <small>{RULE_META[open.rule]?.detail ?? open.explanation}</small>
              </li>
              <li>
                <span>04 · Sonuç</span>
                <strong>{statusMeta(open.status).label}</strong>
                <small>{open.explanation}</small>
              </li>
            </ol>
            <KV
              rows={[
                ["Anayasal tutar", `${fmtDecimal(open.notional_usdt, 4)} USDT`],
                ["Kural sürümü", open.rules_version || "—"],
                ["Gölge kaydı", open.ref_id && open.status !== "APPROVED_PAPER" ? `#${open.ref_id}` : "—"],
              ]}
            />
            {linked.length > 0 && (
              <>
                <h3 className="drawer-sub">Karşı-olgusal gözlem</h3>
                <div className="horizon-cards">
                  {linked.map((s) => (
                    <HorizonCard key={s.horizon_minutes} row={s} now={now} />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </Drawer>
    </>
  );
}

function HorizonCard({ row, now }: { row: ShadowRow; now: number }) {
  const done = row.status === "COMPLETE";
  return (
    <div className={`horizon ${done ? "done" : ""}`}>
      <span className="horizon-h">{row.horizon_minutes} dk</span>
      {done ? <Pnl value={row.pnl_usdt} places={6} /> : <strong>{row.target_at > now ? `${fmtDuration(row.target_at - now)} kaldı` : "Ölçüm sırada"}</strong>}
      <small>
        Giriş {fmtDecimal(row.entry_ask, 4)} → {done ? `çıkış ${fmtDecimal(row.exit_bid, 4)}` : "bekleniyor"}
      </small>
      {row.note && <small className="note">{row.note}</small>}
    </div>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
  render = (v) => v,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
  render?: (v: string) => string;
}) {
  return (
    <label className="field select">
      <span className="sr-only">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} aria-label={label}>
        <option value="">{label}: tümü</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {render(o)}
          </option>
        ))}
      </select>
    </label>
  );
}

export function ShadowExplorer({ rows }: { rows: ShadowRow[] }) {
  const [horizon, setHorizon] = useState<"ALL" | 15 | 60>("ALL");
  const [status, setStatus] = useState("ALL");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(0);
  const [open, setOpen] = useState<ShadowRow | null>(null);
  const now = useNow();
  const filtered = rows.filter(
    (r) =>
      (horizon === "ALL" || r.horizon_minutes === horizon) &&
      (status === "ALL" || r.status === status) &&
      (!category || r.category === category),
  );
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE));
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    setPage(0);
  }, [horizon, status, category]);
  const visible = filtered.slice(page * PAGE, page * PAGE + PAGE);

  return (
    <>
      <div className="toolbar">
        <Segmented
          label="Pencere"
          value={horizon}
          onChange={setHorizon}
          options={[
            { value: "ALL", label: "Tüm pencereler" },
            { value: 15, label: "15 dk" },
            { value: 60, label: "60 dk" },
          ]}
        />
        <Segmented
          label="Ölçüm durumu"
          value={status}
          onChange={setStatus}
          options={[
            { value: "ALL", label: "Tümü" },
            { value: "COMPLETE", label: "Tamamlandı" },
            { value: "PENDING", label: "Bekliyor" },
          ]}
        />
        <div className="toolbar-fields">
          <label className="field select">
            <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Sınıf">
              <option value="">Sınıf: tümü</option>
              {Object.entries(CATEGORY_META).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() =>
              downloadCsv(
                "golge-defter.csv",
                ["shadow_id", "parite", "sinif", "kural", "pencere_dk", "durum", "giris_ask", "cikis_bid", "pnl_usdt", "hedef", "olcum", "giris_kaynak", "cikis_kaynak", "sinyal_kokeni", "not"],
                filtered.map((r) => [r.shadow_id, r.symbol, r.category, r.rule, r.horizon_minutes, r.status, r.entry_ask, r.exit_bid, r.pnl_usdt, new Date(r.target_at * 1000).toISOString(), r.evaluated_at ? new Date(r.evaluated_at * 1000).toISOString() : "", r.entry_source, r.feed_source, r.signal_origin, r.note]),
              )
            }
          >
            ⤓ CSV
          </button>
        </div>
      </div>
      {visible.length ? (
        <div className="table-wrap" tabIndex={0} role="region" aria-label="Gölge kayıtları">
          <table className="table rows-clickable">
            <thead>
              <tr>
                <th scope="col">Kayıt</th>
                <th scope="col">Parite</th>
                <th scope="col">Sınıf</th>
                <th scope="col">Pencere</th>
                <th scope="col">Durum</th>
                <th scope="col" className="num">
                  Karşı-olgusal sonuç
                </th>
                <th scope="col">Veri</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((r) => {
                const meta = CATEGORY_META[r.category];
                const done = r.status === "COMPLETE";
                const progress = Math.min(1, Math.max(0, (now - r.created_at) / (r.target_at - r.created_at)));
                return (
                  <tr key={`${r.shadow_id}-${r.horizon_minutes}`} onClick={() => setOpen(r)}>
                    <td className="mono muted">
                      <button type="button" className="row-link" onClick={(e) => (e.stopPropagation(), setOpen(r))} aria-label={`Gölge kaydı ${r.shadow_id} detayı`}>
                        #{r.shadow_id}
                      </button>
                      <small>{fmtTime(r.created_at, true)}</small>
                    </td>
                    <th scope="row" className="sym">
                      {r.symbol}
                    </th>
                    <td>
                      <StatusPill status={meta?.status ?? r.category} label={meta?.label ?? r.category} />
                      <small className="rule-sub">{ruleLabel(r.rule)}</small>
                    </td>
                    <td className="mono">{r.horizon_minutes} dk</td>
                    <td>
                      {done ? (
                        <span className="eval eval-done">✓ Ölçüldü</span>
                      ) : (
                        <span className="eval">
                          <span className="eval-bar" aria-hidden="true">
                            <span style={{ width: `${progress * 100}%` }} />
                          </span>
                          {r.target_at > now ? `${fmtDuration(r.target_at - now)} kaldı` : "Ölçüm sırada"}
                        </span>
                      )}
                    </td>
                    <td className="num">
                      <Pnl value={r.pnl_usdt} />
                      {r.note && <small className="note">{r.note}</small>}
                    </td>
                    <td className="nowrap">
                      <small className="block">Giriş: {sourceLabel(r.entry_source)}</small>
                      <small className="block">Çıkış: {r.feed_source ? sourceLabel(r.feed_source) : "—"}</small>
                      <small className="block">Sinyal: {sourceLabel(r.signal_origin)}</small>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty title={rows.length ? "Filtreyle eşleşen gölge kaydı yok" : "Henüz gölge kaydı yok"}>
          Engellenen veya pas geçilen adaylar burada 15 ve 60 dakika sonra yeniden ölçülür.
        </Empty>
      )}
      <div className="table-foot">
        <span className="muted">PnL karşı-olgusaldır; kesin önlenen zarar değildir.</span>
        <Pager page={page} pages={pages} onPage={setPage} total={filtered.length} />
      </div>
      <Drawer open={!!open} onClose={() => setOpen(null)} title={open ? `Gölge #${open.shadow_id} · ${open.symbol} · ${open.horizon_minutes} dk` : ""}>
        {open && (
          <>
            <div className="drawer-hero">
              <StatusPill status={CATEGORY_META[open.category]?.status ?? open.category} label={CATEGORY_META[open.category]?.label} />
              <p>{open.reason}</p>
            </div>
            <div className="horizon-cards">
              {rows
                .filter((s) => s.shadow_id === open.shadow_id)
                .map((s) => (
                  <HorizonCard key={s.horizon_minutes} row={s} now={now} />
                ))}
            </div>
            <KV
              rows={[
                ["Kural", `${ruleLabel(open.rule)} (${open.rule})`],
                ["Varsayımsal tutar", `${fmtDecimal(open.notional_usdt, 4)} USDT`],
                ["Giriş (ask)", fmtDecimal(open.entry_ask, 4)],
                ["Kayıt zamanı", fmtDateTime(open.created_at)],
                ["Hedef ölçüm", fmtDateTime(open.target_at)],
                ["Gerçek ölçüm", fmtDateTime(open.evaluated_at)],
                ["Giriş / çıkış kaynağı", `${sourceLabel(open.entry_source)} / ${open.feed_source ? sourceLabel(open.feed_source) : "—"}`],
                ["Sinyal kökeni", sourceLabel(open.signal_origin)],
                ["Ham sınıf", open.raw_category],
              ]}
            />
            <p className="fineprint">
              Karşı-olgusal sonuç, işlem yapılsaydı ne olacağının gözlemidir; ücret ve stop varsayımları içerir ve kesin
              önlenen zarar olarak yorumlanmamalıdır.
            </p>
          </>
        )}
      </Drawer>
    </>
  );
}
