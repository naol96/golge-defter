import { useCallback, useMemo, useRef, useState } from "react";
import { type DataSource, demoSource, liveSource } from "./api/client";
import type { Analytics, Snapshot } from "./api/types";
import { DecisionMix, Legend, OutcomeMatrix, Ring, RuleBars, SymbolBars, Timeline, TimelineTable } from "./components/charts";
import { ConstitutionGrid, Positions, Simulator } from "./components/constitution";
import { KpiStrip, ROUTES, ROUTE_LABELS, type Route, Topbar } from "./components/layout";
import { type DecisionFilter, DecisionExplorer, EMPTY_FILTER, ShadowExplorer } from "./components/tables";
import { CopyButton, Empty, KV, Panel, Segmented, Skeleton, StatusPill } from "./components/ui";
import { useHashRoute, useHotkeys, useNow, usePolling, useTheme } from "./hooks";
import { fmtDateTime, fmtDuration, fmtInt, fmtRelative, shortHash } from "./lib/format";
import { isLiveSource, ruleLabel, sourceLabel } from "./lib/labels";

const SNAPSHOT_MS = 20_000;
const WINDOWS = [
  { value: 1, label: "1 sa", bucket: 5 },
  { value: 3, label: "3 sa", bucket: 10 },
  { value: 6, label: "6 sa", bucket: 15 },
  { value: 24, label: "24 sa", bucket: 60 },
];

function initialDemo(): boolean {
  return new URLSearchParams(window.location.search).get("demo") === "1" || import.meta.env.VITE_DEMO === "1";
}

export default function App() {
  const [demo, setDemo] = useState(initialDemo);
  const source: DataSource = demo ? demoSource : liveSource;
  const [route, go] = useHashRoute(ROUTES, "genel");
  const [theme, setTheme] = useTheme();
  const [paused, setPaused] = useState(false);
  const [hours, setHours] = useState(3);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [chartView, setChartView] = useState<"chart" | "table">("chart");
  const [filter, setFilter] = useState<DecisionFilter>(EMPTY_FILTER);
  const searchRef = useRef<HTMLInputElement>(null);
  const bucket = WINDOWS.find((w) => w.value === hours)?.bucket ?? 10;

  const snapPoll = usePolling<Snapshot>((s) => source.snapshot(s), SNAPSHOT_MS, { paused, deps: [demo] });
  const anaPoll = usePolling<Analytics>((s) => source.analytics({ hours, bucket }, s), SNAPSHOT_MS, {
    paused,
    deps: [demo, hours],
  });
  const snap = snapPoll.data;
  const ana = anaPoll.data;
  const error = snapPoll.error ?? anaPoll.error;
  const refresh = useCallback(() => {
    snapPoll.refresh();
    anaPoll.refresh();
  }, [snapPoll, anaPoll]);

  useHotkeys({
    r: refresh,
    p: () => setPaused((p) => !p),
    t: () => setTheme(theme === "system" ? "light" : theme === "light" ? "dark" : "system"),
    "/": () => {
      go("kararlar");
      window.setTimeout(() => searchRef.current?.focus(), 30);
    },
    ...Object.fromEntries(ROUTES.map((r, i) => [String(i + 1), () => go(r)])),
  });

  const enableDemo = () => {
    const url = new URL(window.location.href);
    url.searchParams.set("demo", "1");
    window.history.replaceState(null, "", url);
    setDemo(true);
  };
  const disableDemo = () => {
    const url = new URL(window.location.href);
    url.searchParams.delete("demo");
    window.history.replaceState(null, "", url);
    setDemo(false);
  };

  const pickRule = (rule: string) => {
    setFilter({ ...EMPTY_FILTER, rule });
    go("kararlar");
  };

  return (
    <>
      <a className="skip" href="#main">
        İçeriğe geç
      </a>
      <Topbar
        snap={snap}
        route={route}
        onRoute={go}
        theme={theme}
        onTheme={setTheme}
        paused={paused}
        onPause={() => setPaused((p) => !p)}
        onRefresh={refresh}
        loading={snapPoll.loading || anaPoll.loading}
        nextAt={snapPoll.nextAt}
        intervalMs={SNAPSHOT_MS}
        demo={demo}
        error={!!error}
      />
      <main id="main" className="workspace">
        {error && !demo && <ErrorBanner error={error} hasData={!!snap} onRetry={refresh} onDemo={enableDemo} />}
        {demo && (
          <div className="banner banner-demo" role="status">
            <strong>Demo modu.</strong> Tarayıcı içinde üretilen örnek veriler gösteriliyor; canlı piyasa veya ölçüm kanıtı değildir.
            <button type="button" className="btn btn-ghost btn-sm" onClick={disableDemo}>
              Canlı veriye dön
            </button>
          </div>
        )}

        {route === "genel" && (
          <Overview
            snap={snap}
            ana={ana}
            hours={hours}
            setHours={setHours}
            hidden={hidden}
            setHidden={setHidden}
            chartView={chartView}
            setChartView={setChartView}
            onPickRule={pickRule}
            source={source}
            go={go}
          />
        )}

        {route === "kararlar" && (
          <>
            <PageHead title="Karar akışı" lead="Analist sinyalinden anayasa kararına kadar her adım. Satıra tıkla, kararın yolculuğunu gör." />
            <Panel title="Kararlar" eyebrow={ana ? `Son ${fmtInt(ana.decisions.length)} kayıt` : "Yükleniyor"}>
              {ana ? <DecisionExplorer data={ana} filter={filter} onFilter={setFilter} searchRef={searchRef} /> : <TableSkeleton />}
            </Panel>
          </>
        )}

        {route === "golge" && (
          <>
            <PageHead
              title="Gölge Defter"
              lead="İşleme dönüşmeyen her aday 15 ve 60 dakika sonra yeniden ölçülür. Sonuçlar karşı-olgusaldır; kesin önlenen zarar değildir."
            />
            <div className="grid grid-3">
              <Panel title="Ölçüm ilerlemesi" eyebrow="15 / 60 dk">
                {snap ? (
                  <div className="rings">
                    <Ring label="15 dk" value={snap.eval_breakdown["15"].COMPLETE} total={snap.eval_breakdown["15"].COMPLETE + snap.eval_breakdown["15"].PENDING} />
                    <Ring label="60 dk" value={snap.eval_breakdown["60"].COMPLETE} total={snap.eval_breakdown["60"].COMPLETE + snap.eval_breakdown["60"].PENDING} />
                  </div>
                ) : (
                  <Skeleton h={120} />
                )}
              </Panel>
              <Panel title="Karşı-olgusal sonuçlar" eyebrow="Tüm kaynaklar · sınıf × pencere" className="span-2">
                {ana ? <OutcomeMatrix outcomes={ana.outcomes} /> : <Skeleton h={160} />}
              </Panel>
            </div>
            <Panel title="Gölge kayıtları" eyebrow={ana ? `Son ${fmtInt(new Set(ana.shadow.map((s) => s.shadow_id)).size)} aday` : "Yükleniyor"}>
              {ana ? <ShadowExplorer rows={ana.shadow} /> : <TableSkeleton />}
            </Panel>
          </>
        )}

        {route === "anayasa" && (
          <>
            <PageHead title="Yatırım Anayasası" lead="Kod varsayılanları gösterilir; karar anındaki kullanıcı sıkılaştırmaları bu özete dahil değildir. Kurallar yalnızca sıkılaştırılabilir." />
            {snap ? <ConstitutionGrid snap={snap} /> : <Skeleton h={260} />}
            <div className="grid grid-2">
              <Simulator key={source.kind} source={source} snap={snap} />
              <Panel title="Açık PAPER pozisyonlar" eyebrow="Stop takibi">
                {snap ? <Positions snap={snap} /> : <Skeleton h={140} />}
              </Panel>
            </div>
          </>
        )}

        {route === "sistem" && <SystemView snap={snap} demo={demo} />}
      </main>
      <Footer snap={snap} updatedAt={snapPoll.updatedAt} paused={paused} />
    </>
  );
}

function PageHead({ title, lead }: { title: string; lead: string }) {
  return (
    <div className="page-head">
      <h1>{title}</h1>
      <p>{lead}</p>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="table-skel">
      {Array.from({ length: 8 }, (_, i) => (
        <Skeleton key={i} h={34} />
      ))}
    </div>
  );
}

function ErrorBanner({ error, hasData, onRetry, onDemo }: { error: Error; hasData: boolean; onRetry: () => void; onDemo: () => void }) {
  return (
    <div className="banner banner-error" role="alert">
      <div>
        <strong>{hasData ? "Veri yenilenemedi — gösterilen kayıtlar güncel olmayabilir." : "Kokpit verisi alınamadı."}</strong>
        <span>{error.message}</span>
        {!hasData && (
          <small>
            Sunucuyu başlatın: <code>python -m dashboard.serve_kokpit</code> · DB yoksa önce worker'ı çalıştırın.
          </small>
        )}
      </div>
      <div className="banner-actions">
        <button type="button" className="btn btn-sm" onClick={onRetry}>
          Tekrar dene
        </button>
        {!hasData && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={onDemo}>
            Demo veriyle aç
          </button>
        )}
      </div>
    </div>
  );
}

function Overview({
  snap,
  ana,
  hours,
  setHours,
  hidden,
  setHidden,
  chartView,
  setChartView,
  onPickRule,
  source,
  go,
}: {
  snap: Snapshot | null;
  ana: Analytics | null;
  hours: number;
  setHours: (h: number) => void;
  hidden: Set<string>;
  setHidden: (s: Set<string>) => void;
  chartView: "chart" | "table";
  setChartView: (v: "chart" | "table") => void;
  onPickRule: (r: string) => void;
  source: DataSource;
  go: (r: Route) => void;
}) {
  const now = useNow();
  const toggle = (s: string) => {
    const next = new Set(hidden);
    next.has(s) ? next.delete(s) : next.add(s);
    setHidden(next);
  };
  return (
    <>
      <section className="hero">
        <div>
          <span className="eyebrow">OKX TR × Team1 Türkiye · Agentic Hackathon</span>
          <h1>
            Her sinyal bir işlem olmak zorunda değil<span className="accent">.</span>
          </h1>
          <p>Yapay zekâ önerir. Anayasa sınırlar. Gölge Defter, alınmayan kararların izini tutar.</p>
        </div>
        <ol className="flow" aria-label="Karar denetim akışı">
          <li>
            <span>01</span>
            <strong>Piyasa verisi</strong>
            <small>OKX ATK · salt okunur</small>
          </li>
          <li>
            <span>02</span>
            <strong>Analist ajan</strong>
            <small>BUY / PASS + gerekçe</small>
          </li>
          <li className="flow-accent">
            <span>03</span>
            <strong>Yatırım Anayasası</strong>
            <small>Deterministik sert sınırlar</small>
          </li>
          <li className="flow-split">
            <span>04</span>
            <strong>
              PAPER icra <em>veya</em> Gölge Defter
            </strong>
            <small>Gerçek emir yok — karar ve gözlem var</small>
          </li>
        </ol>
      </section>

      <KpiStrip snap={snap} />

      <div className="grid grid-3">
        <Panel
          className="span-2"
          eyebrow="Zaman serisi"
          title="Kararların ritmi"
          actions={
            <>
              <Segmented size="sm" label="Zaman aralığı" value={hours} onChange={setHours} options={WINDOWS.map((w) => ({ value: w.value, label: w.label }))} />
              <Segmented
                size="sm"
                label="Görünüm"
                value={chartView}
                onChange={setChartView}
                options={[
                  { value: "chart", label: "Grafik" },
                  { value: "table", label: "Tablo" },
                ]}
              />
            </>
          }
        >
          {ana ? (
            <>
              <Legend onToggle={toggle} hidden={hidden} />
              {chartView === "chart" ? <Timeline data={ana} hidden={hidden} /> : <TimelineTable data={ana} />}
              <p className="caption">
                {ana.window.bucket_minutes} dakikalık dilimler · pencere en son karara göre hizalanır ({fmtDateTime(ana.window.end)}).
              </p>
            </>
          ) : (
            <Skeleton h={240} />
          )}
        </Panel>
        <Panel eyebrow="Dağılım" title="Kararlar nereye gidiyor?">
          {snap ? <DecisionMix summary={snap.decisions_summary} /> : <Skeleton h={120} />}
          {ana && (
            <>
              <h3 className="sub-h">Pariteye göre</h3>
              <SymbolBars symbols={ana.symbols} />
            </>
          )}
        </Panel>
      </div>

      <div className="grid grid-3">
        <Panel eyebrow="Anayasa" title="En çok devreye giren kurallar" actions={<span className="muted small">Tıkla → filtrele</span>}>
          {ana ? <RuleBars rules={ana.rules} onPick={onPickRule} /> : <Skeleton h={180} />}
        </Panel>
        <Panel
          className="span-2"
          eyebrow="Canlı akış"
          title="Son kararlar"
          actions={
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => go("kararlar")}>
              Tümü →
            </button>
          }
        >
          {ana ? (
            ana.decisions.length ? (
              <ol className="feed">
                {ana.decisions.slice(0, 7).map((d) => (
                  <li key={d.id}>
                    <span className="feed-time mono" title={fmtDateTime(d.created_at)}>
                      {fmtRelative(d.created_at, now)}
                    </span>
                    <strong className="feed-sym">{d.symbol}</strong>
                    <StatusPill status={d.status} />
                    <span className="feed-text">
                      <b>{ruleLabel(d.rule)}</b> — {d.explanation}
                    </span>
                    <span className={`src ${d.signal_origin === "LLM" ? "src-llm" : ""}`}>{sourceLabel(d.signal_origin)}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <Empty title="Henüz karar yok" />
            )
          ) : (
            <TableSkeleton />
          )}
        </Panel>
      </div>

      <div className="grid grid-2">
        <Simulator key={source.kind} source={source} snap={snap} />
        <Panel eyebrow="Gölge Defter" title="Alınmayan kararlar ne oldu?" actions={<button type="button" className="btn btn-ghost btn-sm" onClick={() => go("golge")}>Detay →</button>}>
          {snap && (
            <div className="rings">
              <Ring label="15 dk" value={snap.eval_breakdown["15"].COMPLETE} total={snap.eval_breakdown["15"].COMPLETE + snap.eval_breakdown["15"].PENDING} />
              <Ring label="60 dk" value={snap.eval_breakdown["60"].COMPLETE} total={snap.eval_breakdown["60"].COMPLETE + snap.eval_breakdown["60"].PENDING} />
            </div>
          )}
          {ana ? <OutcomeMatrix outcomes={ana.outcomes} /> : <Skeleton h={160} />}
        </Panel>
      </div>
    </>
  );
}

function SystemView({ snap, demo }: { snap: Snapshot | null; demo: boolean }) {
  const now = useNow();
  const anchor = snap?.anchor;
  const safeTx = useMemo(() => {
    if (!anchor?.snowtrace_tx) return null;
    try {
      const u = new URL(String(anchor.snowtrace_tx));
      return u.protocol === "https:" ? u.href : null;
    } catch {
      return null;
    }
  }, [anchor]);
  if (!snap) return <Skeleton h={300} />;
  const r = snap.report;
  const age = snap.last_decision_age_s != null ? snap.last_decision_age_s + (now - snap.generated_at) : null;
  return (
    <>
      <PageHead title="Sistem & kanıt" lead="Verinin nereden geldiği, ne kadar taze olduğu ve neyin kanıtlanıp neyin kanıtlanmadığı." />
      <div className="grid grid-2">
        <Panel eyebrow="Bağlantı" title="Veri & worker">
          <KV
            rows={[
              ["Worker", snap.worker_active ? "Aktif" : "Çalışmıyor"],
              ["Son piyasa kaynağı", <span key="s">{isLiveSource(snap.last_market_source) && <i className="live-dot" />}{sourceLabel(snap.last_market_source)}</span>],
              ["Son karar yaşı", age != null ? fmtDuration(age) : "—"],
              ["Bekleyen değerlendirme", fmtInt(r.pending_evaluations)],
              ["Açık PAPER pozisyon", fmtInt(snap.open_positions.length)],
              ["Kural sürümü", snap.rules_version],
              ["Veritabanı", <code key="db" className="break">{snap.db}</code>],
              ["Snapshot zamanı", fmtDateTime(snap.generated_at)],
            ]}
          />
        </Panel>
        <Panel eyebrow="Köken" title="Sinyal ve veri kaynakları">
          <SourceBars title="Sinyal kökeni" counts={r.decisions_by_signal_origin} />
          <SourceBars title="Piyasa kaynağı (kararlar)" counts={r.decisions_by_market_source} />
          <SourceBars title="Gölge giriş kaynağı" counts={r.shadow_by_feed_source} />
          <p className="fineprint">ATK piyasa verisi bir LLM sinyali anlamına gelmez; kökenler ayrı sayılır.</p>
        </Panel>
        <Panel eyebrow="Doğrulanabilirlik" title="Yerel hash & zincir durumu">
          {anchor ? (
            <>
              <div className="hash-box">
                <span className="mono" title={anchor.sha256}>
                  {shortHash(anchor.sha256, 16, 12)}
                </span>
                {anchor.sha256 && <CopyButton text={anchor.sha256} />}
              </div>
              <KV
                rows={[
                  ["Kanıt türü", anchor.proof_kind],
                  ["Manifest kayıt sayısı", fmtInt(anchor.decision_count)],
                  ["Hash kapsamı", `Son en fazla ${anchor.batch_limit ?? "—"} karar`],
                  ["Üretim", anchor.generated_at ?? "—"],
                  ["Zincir doğrulaması", <span key="v" className="warn-text">⚠ Doğrulanmış blockchain kanıtı yok</span>],
                ]}
              />
              {safeTx && (
                <a className="ext" href={safeTx} target="_blank" rel="noopener noreferrer">
                  Bildirilen işlem bağlantısı (doğrulanmadı) ↗
                </a>
              )}
            </>
          ) : (
            <Empty title="Yerel hash manifesti yok">Manifest oluşturulduğunda burada görünür; yerel SHA-256 tek başına blockchain kanıtı değildir.</Empty>
          )}
        </Panel>
        <Panel eyebrow="Dürüstlük" title="Ölçüm notları">
          <ul className="notes">
            {r.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
          {demo && <p className="fineprint">Demo modunda notlar örnek veriyi açıklar.</p>}
        </Panel>
      </div>
      <Panel eyebrow="Kısayollar" title="Klavye">
        <ul className="shortcuts">
          {[
            ["1–5", "Görünümler arasında geç"],
            ["/", "Kararlarda ara"],
            ["R", "Şimdi yenile"],
            ["P", "Otomatik yenilemeyi duraklat"],
            ["T", "Tema: sistem → açık → koyu"],
            ["Esc", "Paneli kapat"],
          ].map(([k, v]) => (
            <li key={k}>
              <kbd>{k}</kbd>
              {v}
            </li>
          ))}
        </ul>
        <p className="fineprint">Görünümler: {ROUTES.map((r) => ROUTE_LABELS[r]).join(" · ")}</p>
      </Panel>
    </>
  );
}

function SourceBars({ title, counts }: { title: string; counts: Record<string, number> }) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((a, [, v]) => a + v, 0);
  return (
    <div className="source-bars">
      <h3 className="sub-h">{title}</h3>
      {entries.length ? (
        entries.map(([k, v]) => (
          <div key={k} className="source-row">
            <span>
              {isLiveSource(k) && <i className="live-dot" />}
              {sourceLabel(k)}
            </span>
            <span className="rulebar-track">
              <span className="source-fill" style={{ width: `${(v / total) * 100}%` }} />
            </span>
            <b>{fmtInt(v)}</b>
          </div>
        ))
      ) : (
        <span className="muted">—</span>
      )}
    </div>
  );
}

function Footer({ snap, updatedAt, paused }: { snap: Snapshot | null; updatedAt: number | null; paused: boolean }) {
  return (
    <footer className="footer">
      <span className="footer-brand">
        shadow ledger <small>Alınmayan kararın da kaydı var.</small>
      </span>
      <span>
        {updatedAt ? `Güncellendi ${new Date(updatedAt).toLocaleTimeString("tr-TR")}` : "Bağlanıyor…"}
        {paused && " · duraklatıldı"}
      </span>
      <span>{snap?.rules_version ?? ""} · PAPER simülasyonu · Gerçek emir gönderilmez · Finansal tavsiye değildir</span>
    </footer>
  );
}
