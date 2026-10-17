// Offline demo dataset (clearly labelled DEMO in the UI). Lets the kokpit be shown
// without the Python worker; the shapes match the live API exactly.
import type { Analytics, CountMap, DecisionRow, Outcome, ShadowRow, SimulationResult, Snapshot } from "./types";

const RULE_TEXT: Record<string, string> = {
  EXPOSURE: "Toplam açık risk anayasal %50 tavanını aşar.",
  SPREAD: "Makas %0,15 tavanını aşıyor.",
  COOLDOWN: "Parite 15 dk bekleme süresinde.",
  MAX_POSITIONS: "Açık pozisyon sayısı 2 sınırında.",
  MIN_ORDER: "Anayasal tutar borsa minimum emrinin (10 USDT) altında; risk vetosu değil.",
  OBSERVATION: "Bakiye gözlem eşiğinin altında; teknik kayıt.",
};
const PASS_REASONS = ["Momentum zayıf, hacim ortalamanın altında.", "Kısa vadeli trend belirsiz; pas geçildi."];
const BUY_REASONS = ["Kısa vadeli kırılım ve artan hacim.", "Destek seviyesinden toparlanma sinyali."];

function rng(seed: number) {
  return () => {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
  };
}

function gauss(r: () => number) {
  return Math.sqrt(-2 * Math.log(r() || 1e-9)) * Math.cos(2 * Math.PI * r());
}

interface DemoData {
  decisions: DecisionRow[];
  shadow: ShadowRow[];
  base: number;
}

let cache: DemoData | null = null;

function build(): DemoData {
  if (cache) return cache;
  const r = rng(42);
  const base = Math.floor(Date.now() / 1000);
  const prices: Record<string, number> = { "BTC-USDT": 67250, "ETH-USDT": 2610, "AVAX-USDT": 26.4 };
  const decisions: DecisionRow[] = [];
  const shadow: ShadowRow[] = [];
  let t = base - 3 * 3600;
  let shadowId = 0;
  for (let id = 1; ; id++) {
    t += 40 + Math.floor(r() * 70);
    if (t > base - 20) break;
    const symbol = Object.keys(prices)[Math.floor(r() * 3)]!;
    prices[symbol]! *= 1 + gauss(r) * 0.0015;
    const roll = r();
    let status: string, rule: string, action = "BUY", explanation: string;
    if (roll < 0.05) [status, rule, explanation] = ["APPROVED_PAPER", "OK", "Sadece PAPER icraya uygun (LIVE desteklenmiyor)."];
    else if (roll < 0.38) {
      rule = ["EXPOSURE", "EXPOSURE", "SPREAD", "COOLDOWN", "MAX_POSITIONS"][Math.floor(r() * 5)]!;
      [status, explanation] = ["SHADOW_RISK", RULE_TEXT[rule]!];
    } else if (roll < 0.58) {
      [status, rule, action, explanation] = ["SHADOW_PASS", "ANALYST_PASS", "PASS", PASS_REASONS[Math.floor(r() * 2)]!];
    } else {
      rule = r() < 0.7 ? "MIN_ORDER" : "OBSERVATION";
      [status, explanation] = ["TECHNICAL_BLOCK", RULE_TEXT[rule]!];
    }
    let ref: number | null = null;
    if (status !== "APPROVED_PAPER") {
      ref = ++shadowId;
      const ask = prices[symbol]! * 1.0004;
      const category =
        status === "SHADOW_RISK" ? "CONSTITUTIONAL_RISK_BLOCK" : status === "SHADOW_PASS" ? "PASS_OBSERVATION" : "TECHNICAL_UNEXECUTABLE";
      for (const h of [15, 60] as const) {
        const target = t + h * 60;
        const done = target <= base;
        const drift = gauss(r) * 0.004 * Math.sqrt(h / 15);
        const exit = ask * (1 + drift);
        shadow.push({
          shadow_id: ref,
          symbol,
          raw_category: category,
          category,
          rule,
          entry_ask: ask.toFixed(4),
          notional_usdt: "9.3728",
          reason: explanation,
          entry_source: "FIXTURE_SYNTHETIC_NOT_LIVE",
          signal_origin: "DEMO",
          created_at: t,
          horizon_minutes: h,
          status: done ? "COMPLETE" : "PENDING",
          exit_bid: done ? exit.toFixed(4) : null,
          pnl_usdt: done ? (9.3728 * (exit / ask - 1) - 0.0187).toFixed(8) : null,
          evaluated_at: done ? target + 3 + Math.floor(r() * 20) : null,
          note: done ? "MOCK / SIMULATED; stop_dogrulamasi_sinirli" : "",
          feed_source: done ? "FIXTURE_SYNTHETIC_NOT_LIVE" : "",
          target_at: target,
        });
      }
    }
    decisions.push({
      id,
      symbol,
      signal_action: action,
      signal_reason: (action === "PASS" ? PASS_REASONS : BUY_REASONS)[Math.floor(r() * 2)]!,
      signal_origin: "DEMO",
      raw_status: status,
      status,
      rule,
      explanation,
      notional_usdt: "9.3728",
      market_source: "FIXTURE_SYNTHETIC_NOT_LIVE",
      ref_id: ref,
      created_at: t,
      rules_version: "DEMO / rules_v2_audit1",
    });
  }
  decisions.reverse();
  shadow.sort((a, b) => b.shadow_id - a.shadow_id || a.horizon_minutes - b.horizon_minutes);
  cache = { decisions, shadow, base };
  return cache;
}

function countBy<T>(rows: T[], key: (row: T) => string): CountMap {
  const out: CountMap = {};
  for (const row of rows) out[key(row)] = (out[key(row)] ?? 0) + 1;
  return out;
}

export function demoSnapshot(): Snapshot {
  const { decisions, shadow } = build();
  const now = Math.floor(Date.now() / 1000);
  const byStatus = countBy(decisions, (d) => d.status);
  const evals = (h: number, s: string) => shadow.filter((x) => x.horizon_minutes === h && x.status === s).length;
  return {
    generated_at: now,
    db: "DEMO (tarayıcı içi örnek veri)",
    worker_active: false,
    rules_version: "DEMO / rules_v2_audit1",
    last_decision_age_s: now - decisions[0]!.created_at,
    last_market_source: "FIXTURE_SYNTHETIC_NOT_LIVE",
    report: {
      db: "DEMO",
      decisions_by_status: byStatus,
      decisions_by_market_source: countBy(decisions, (d) => d.market_source),
      decisions_by_signal_origin: countBy(decisions, (d) => d.signal_origin),
      shadow_by_category: countBy(shadow.filter((s) => s.horizon_minutes === 15), (s) => s.category),
      shadow_by_feed_source: { FIXTURE_SYNTHETIC_NOT_LIVE: shadow.length / 2 },
      evaluations_by_status: countBy(shadow, (s) => s.status),
      pending_evaluations: shadow.filter((s) => s.status === "PENDING").length,
      complete_15m: evals(15, "COMPLETE"),
      complete_15m_live_feed: 0,
      complete_60m: evals(60, "COMPLETE"),
      complete_60m_live_feed: 0,
      decisions_technical_block: byStatus.TECHNICAL_BLOCK ?? 0,
      decisions_shadow_risk: byStatus.SHADOW_RISK ?? 0,
      last_decision: null,
      paper_balance_usdt: "37.4912",
      open_paper_positions: 1,
      notes: ["DEMO verisi; canlı piyasa kanıtı değildir."],
    },
    constitution: {
      tek_islem_tavan_pct: 25,
      max_acik_pozisyon: 2,
      max_toplam_risk_pct: 50,
      max_spread_pct: 0.15,
      stop_loss_pct: 2.5,
      gunluk_zarar_pct: 5,
      gunluk_zarar_usdt: "5",
      bekleme_dk: 15,
      gozlem_esigi_usdt: "40",
      rules_version_code: "rules_v2_audit1",
    },
    paper_balance_usdt: "37.4912",
    open_positions: [
      { id: 1, symbol: "ETH-USDT", notional_usdt: "12.50", entry_price: "2604.12", stop_loss_price: "2539.02", status: "OPEN" },
    ],
    eval_breakdown: {
      "15": { PENDING: evals(15, "PENDING"), COMPLETE: evals(15, "COMPLETE") },
      "60": { PENDING: evals(60, "PENDING"), COMPLETE: evals(60, "COMPLETE") },
    },
    decisions_summary: byStatus,
    anchor: {
      sha256: "9f2c4e1b7a0d3c58e6b1f4a29d7c0e83b5a61f2d4c9e07b8a3d1f6c2e5b94a70",
      decision_count: 100,
      batch_limit: 100,
      generated_at: new Date(build().base * 1000).toISOString(),
      blockchain_verified: false,
      proof_kind: "DEMO_HASH_NOT_PROOF",
    },
  };
}

export function demoAnalytics(hours: number, bucketMinutes: number): Analytics {
  const { decisions, shadow } = build();
  const bucket = bucketMinutes * 60;
  const latest = decisions[0]!.created_at;
  const end = latest - (latest % bucket) + bucket;
  const start = end - hours * 3600;
  const timeline: Analytics["timeline"] = [];
  for (let t = start; t < end; t += bucket) {
    timeline.push({ t, counts: countBy(decisions.filter((d) => d.created_at >= t && d.created_at < t + bucket), (d) => d.status) });
  }
  const group = (key: (d: DecisionRow) => string) => {
    const map = new Map<string, { total: number; by_status: CountMap }>();
    for (const d of decisions) {
      const entry = map.get(key(d)) ?? { total: 0, by_status: {} };
      entry.total++;
      entry.by_status[d.status] = (entry.by_status[d.status] ?? 0) + 1;
      map.set(key(d), entry);
    }
    return [...map.entries()].sort((a, b) => b[1].total - a[1].total);
  };
  const outcomes: Outcome[] = [];
  for (const category of ["CONSTITUTIONAL_RISK_BLOCK", "PASS_OBSERVATION", "TECHNICAL_UNEXECUTABLE"]) {
    for (const h of [15, 60]) {
      const vals = shadow
        .filter((s) => s.category === category && s.horizon_minutes === h && s.pnl_usdt != null)
        .map((s) => Number(s.pnl_usdt));
      if (!vals.length) continue;
      const sum = vals.reduce((a, b) => a + b, 0);
      outcomes.push({
        category,
        horizon_minutes: h,
        count: vals.length,
        positive: vals.filter((v) => v > 0).length,
        negative: vals.filter((v) => v < 0).length,
        sum_pnl_usdt: sum.toFixed(8),
        avg_pnl_usdt: (sum / vals.length).toFixed(8),
        min_pnl_usdt: Math.min(...vals).toFixed(8),
        max_pnl_usdt: Math.max(...vals).toFixed(8),
      });
    }
  }
  return {
    generated_at: Math.floor(Date.now() / 1000),
    window: { start, end, hours, bucket_minutes: bucketMinutes },
    timeline,
    rules: group((d) => d.rule).map(([rule, v]) => ({ rule, ...v })),
    symbols: group((d) => d.symbol).map(([symbol, v]) => ({ symbol, ...v })),
    outcomes,
    decisions: decisions.slice(0, 200),
    shadow: shadow.slice(0, 400),
    notes: ["DEMO verisi"],
  };
}

// Mirrors core/user_rules.py + core/constitution.py tighten_* (rules_v2 defaults).
export function demoSimulate(text: string): SimulationResult {
  const label = text.trim();
  const effective = { max_position_fraction_pct: 25, max_spread_fraction_pct: 0.15 };
  const fmt = (n: number) => String(Number(n.toPrecision(6)));
  if (!label) return { user_request: "", message: "Boş talep; sert sınırlar korundu.", effective };
  const m = /(%\s*)?(\d+(?:[.,]\d+)?)\s*(%|yüzde|percent)?/i.exec(label);
  if (m) {
    const raw = Number(m[2]!.replace(",", "."));
    if (/makas|spread/i.test(label)) {
      const frac = raw / 100;
      if (frac <= 0 || frac > 1) return { user_request: label, message: "Geçersiz makas oranı; mevcut makas tavanı korundu.", effective };
      if (frac > 0.0015)
        return { user_request: label, message: `Talep %${fmt(frac * 100)} mevcut makas tavanından gevşek; etkin tavan %0.15 korundu.`, effective };
      return {
        user_request: label,
        message: `Makas tavanı %${fmt(frac * 100)} olarak sıkılaştırıldı.`,
        effective: { ...effective, max_spread_fraction_pct: frac * 100 },
      };
    }
    const frac = raw > 1 ? raw / 100 : raw;
    if (frac <= 0 || frac > 1) return { user_request: label, message: "Geçersiz oran; mevcut güvenlik tavanı korundu.", effective };
    if (frac > 0.25)
      return { user_request: label, message: `Talep %${fmt(frac * 100)} mevcut sert sınırı aşıyor; etkin tavan %25 olarak korundu.`, effective };
    return {
      user_request: label,
      message: `Tavan %${fmt(frac * 100)} olarak sıkılaştırıldı.`,
      effective: { ...effective, max_position_fraction_pct: frac * 100 },
    };
  }
  return { user_request: label, message: "Doğal dil talebi tanınmadı; sert sınırlar korundu.", effective };
}
