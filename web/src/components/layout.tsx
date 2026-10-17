import type { Snapshot } from "../api/types";
import { type ThemePref, useNow } from "../hooks";
import { fmtDecimal, fmtDuration, fmtInt, fmtPct } from "../lib/format";
import { isLiveSource, sourceLabel } from "../lib/labels";
import { Skeleton } from "./ui";

export const ROUTES = ["genel", "kararlar", "golge", "anayasa", "sistem"] as const;
export type Route = (typeof ROUTES)[number];
export const ROUTE_LABELS: Record<Route, string> = {
  genel: "Genel bakış",
  kararlar: "Karar akışı",
  golge: "Gölge Defter",
  anayasa: "Anayasa",
  sistem: "Sistem & kanıt",
};

const STALE_AFTER_S = 120;

export function Topbar({
  snap,
  route,
  onRoute,
  theme,
  onTheme,
  paused,
  onPause,
  onRefresh,
  loading,
  nextAt,
  intervalMs,
  demo,
  error,
}: {
  snap: Snapshot | null;
  route: Route;
  onRoute: (r: Route) => void;
  theme: ThemePref;
  onTheme: (t: ThemePref) => void;
  paused: boolean;
  onPause: () => void;
  onRefresh: () => void;
  loading: boolean;
  nextAt: number | null;
  intervalMs: number;
  demo: boolean;
  error: boolean;
}) {
  const now = useNow();
  const remaining = nextAt ? Math.max(0, nextAt / 1000 - now) : 0;
  const progress = nextAt && !paused ? 1 - remaining / (intervalMs / 1000) : 0;
  const nextTheme: Record<ThemePref, ThemePref> = { system: "light", light: "dark", dark: "system" };
  const themeLabel: Record<ThemePref, string> = { system: "Sistem", light: "Açık", dark: "Koyu" };

  return (
    <header className="topbar">
      <div className="topbar-row">
        <a className="brand" href="#/genel" aria-label="Gölge Defter ana sayfa">
          <span className="brand-mark" aria-hidden="true">
            g.
          </span>
          <span className="brand-text">
            gölge defter
            <small>Yatırım anayasası & karar hafızası</small>
          </span>
        </a>

        <div className="topbar-status">
          <span className="badge badge-paper" title="Gerçek emir gönderilmez">
            PAPER
          </span>
          {demo && (
            <span className="badge badge-demo" title="Tarayıcı içi örnek veri; canlı kanıt değildir">
              DEMO VERİ
            </span>
          )}
          <WorkerBadge snap={snap} error={error} demo={demo} now={now} />
          {snap && <span className="badge badge-muted mono">{snap.rules_version}</span>}
        </div>

        <div className="topbar-actions">
          <button
            type="button"
            className="refresh"
            onClick={onRefresh}
            aria-label={`Şimdi yenile${paused ? "" : ` (otomatik: ${Math.ceil(remaining)} sn)`}`}
            title="Yenile (R)"
          >
            <svg viewBox="0 0 36 36" aria-hidden="true" className={loading ? "spin" : ""}>
              <circle cx="18" cy="18" r="15" className="refresh-track" />
              <circle
                cx="18"
                cy="18"
                r="15"
                className="refresh-fill"
                strokeDasharray={`${94.25 * progress} 94.25`}
                transform="rotate(-90 18 18)"
              />
            </svg>
            <span aria-hidden="true">↻</span>
          </button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onPause} aria-pressed={paused} title="Otomatik yenilemeyi duraklat (P)">
            {paused ? "▶ Devam" : "❚❚ Duraklat"}
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => onTheme(nextTheme[theme])}
            title="Tema değiştir (T)"
            aria-label={`Tema: ${themeLabel[theme]}. Değiştir`}
          >
            {theme === "dark" ? "☾" : theme === "light" ? "☀" : "◐"} {themeLabel[theme]}
          </button>
        </div>
      </div>

      <nav className="tabs" aria-label="Görünümler">
        {ROUTES.map((r, i) => (
          <a
            key={r}
            href={`#/${r}`}
            aria-current={route === r ? "page" : undefined}
            onClick={(e) => {
              e.preventDefault();
              onRoute(r);
            }}
          >
            <kbd aria-hidden="true">{i + 1}</kbd>
            {ROUTE_LABELS[r]}
          </a>
        ))}
      </nav>
    </header>
  );
}

function WorkerBadge({ snap, error, demo, now }: { snap: Snapshot | null; error: boolean; demo: boolean; now: number }) {
  if (error && !demo) return <span className="badge badge-danger"><i className="dot" /> Bağlantı yok</span>;
  if (!snap) return <span className="badge badge-muted"><i className="dot" /> Bağlanıyor…</span>;
  const age = snap.last_decision_age_s != null ? snap.last_decision_age_s + (now - snap.generated_at) : null;
  if (snap.worker_active) {
    const stale = age != null && age > STALE_AFTER_S;
    return (
      <span className={`badge ${stale ? "badge-warn" : "badge-ok"}`} title={`Son karar ${fmtDuration(age)} önce`}>
        <i className={`dot ${stale ? "" : "pulse"}`} /> Worker aktif{stale ? " · veri eski" : ""}
      </span>
    );
  }
  return (
    <span className="badge badge-warn" title="data/atk_worker.pid bulunamadı veya süreç çalışmıyor">
      <i className="dot" /> Worker kapalı
    </span>
  );
}

export function KpiStrip({ snap }: { snap: Snapshot | null }) {
  const now = useNow();
  if (!snap) {
    return (
      <div className="kpis" aria-busy="true">
        {Array.from({ length: 6 }, (_, i) => (
          <div className="kpi" key={i}>
            <Skeleton h={12} w="60%" />
            <Skeleton h={30} w="45%" />
            <Skeleton h={10} w="80%" />
          </div>
        ))}
      </div>
    );
  }
  const r = snap.report;
  const total = Object.values(snap.decisions_summary).reduce((a, b) => a + b, 0);
  const shadowed = ["SHADOW_RISK", "SHADOW_PASS", "TECHNICAL_BLOCK"].reduce((sum, status) => sum + (snap.decisions_summary[status] ?? 0), 0);
  const age = snap.last_decision_age_s != null ? snap.last_decision_age_s + (now - snap.generated_at) : null;
  const items: { label: string; value: string; sub: string; tone?: string }[] = [
    {
      label: "Toplam karar",
      value: fmtInt(total),
      sub: `${fmtInt(snap.decisions_summary.APPROVED_PAPER ?? 0)} PAPER onayı · ${total ? fmtPct((shadowed / total) * 100, 0) : "—"} gölgede`,
    },
    {
      label: "Anayasal risk engeli",
      value: fmtInt(r.decisions_shadow_risk),
      sub: "Kural ihlali nedeniyle durdurulan",
      tone: "risk",
    },
    {
      label: "Teknik engel",
      value: fmtInt(r.decisions_technical_block),
      sub: "Minimum emir · risk değil",
      tone: "technical",
    },
    {
      label: "ATK kökenli 15 / 60 dk gözlem",
      value: `${fmtInt(r.complete_15m_live_feed)} / ${fmtInt(r.complete_60m_live_feed)}`,
      sub: `${fmtInt(r.pending_evaluations)} ölçüm bekliyor`,
    },
    {
      label: "PAPER bakiye",
      value: fmtDecimal(snap.paper_balance_usdt, 2),
      sub: `USDT · ${snap.open_positions.length} açık pozisyon`,
    },
    {
      label: "Son karar",
      value: age != null ? fmtDuration(age) : "—",
      sub: `${isLiveSource(snap.last_market_source) ? "● " : ""}${sourceLabel(snap.last_market_source)} kaynağı`,
      tone: age != null && age > STALE_AFTER_S ? "stale" : "fresh",
    },
  ];
  return (
    <div className="kpis">
      {items.map((it) => (
        <div className={`kpi ${it.tone ? `kpi-${it.tone}` : ""}`} key={it.label}>
          <span className="kpi-label">{it.label}</span>
          <span className="kpi-value">{it.value}</span>
          <span className="kpi-sub">{it.sub}</span>
        </div>
      ))}
    </div>
  );
}
