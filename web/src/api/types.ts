// Mirrors dashboard/snapshot.py and dashboard/analytics.py. Monetary values stay
// decimal strings end-to-end; only display code rounds them.

export type DecisionStatus = "APPROVED_PAPER" | "SHADOW_RISK" | "SHADOW_PASS" | "TECHNICAL_BLOCK" | (string & {});
export type ShadowCategory =
  | "CONSTITUTIONAL_RISK_BLOCK"
  | "PASS_OBSERVATION"
  | "TECHNICAL_UNEXECUTABLE"
  | (string & {});
export type EvalStatus = "PENDING" | "COMPLETE" | (string & {});
export type CountMap = Record<string, number>;

export interface Report {
  db: string;
  decisions_by_status: CountMap;
  decisions_by_market_source: CountMap;
  decisions_by_signal_origin: CountMap;
  shadow_by_category: CountMap;
  shadow_by_feed_source: CountMap;
  evaluations_by_status: CountMap;
  pending_evaluations: number;
  complete_15m: number;
  complete_15m_live_feed: number;
  complete_60m: number;
  complete_60m_live_feed: number;
  decisions_technical_block: number;
  decisions_shadow_risk: number;
  last_decision: Record<string, unknown> | null;
  paper_balance_usdt: string | null;
  open_paper_positions: number;
  notes: string[];
}

export interface Constitution {
  tek_islem_tavan_pct: number;
  max_acik_pozisyon: number;
  max_toplam_risk_pct: number;
  max_spread_pct: number;
  stop_loss_pct: number;
  gunluk_zarar_pct: number;
  gunluk_zarar_usdt: string;
  bekleme_dk: number;
  gozlem_esigi_usdt: string;
  rules_version_code: string;
}

export interface OpenPosition {
  id: number;
  symbol: string;
  notional_usdt: string;
  entry_price: string;
  stop_loss_price: string;
  status: string;
}

export interface Anchor {
  sha256?: string;
  decision_count?: number;
  batch_limit?: number;
  generated_at?: string;
  snowtrace_tx?: string;
  blockchain_verified: false;
  proof_kind: string;
  [key: string]: unknown;
}

export interface Snapshot {
  generated_at: number;
  db: string;
  worker_active: boolean;
  rules_version: string;
  last_decision_age_s: number | null;
  last_market_source: string | null;
  report: Report;
  constitution: Constitution;
  paper_balance_usdt: string | null;
  open_positions: OpenPosition[];
  eval_breakdown: Record<"15" | "60", { PENDING: number; COMPLETE: number }>;
  decisions_summary: CountMap;
  anchor: Anchor | null;
}

export interface DecisionRow {
  id: number;
  symbol: string;
  signal_action: string;
  signal_reason: string;
  signal_origin: string;
  raw_status: string;
  status: DecisionStatus;
  rule: string;
  explanation: string;
  notional_usdt: string;
  market_source: string;
  ref_id: number | null;
  created_at: number;
  rules_version: string | null;
}

export interface ShadowRow {
  shadow_id: number;
  symbol: string;
  raw_category: string;
  category: ShadowCategory;
  rule: string;
  entry_ask: string;
  notional_usdt: string;
  reason: string;
  entry_source: string;
  signal_origin: string;
  created_at: number;
  horizon_minutes: 15 | 60;
  status: EvalStatus;
  exit_bid: string | null;
  pnl_usdt: string | null;
  evaluated_at: number | null;
  note: string | null;
  feed_source: string | null;
  target_at: number;
}

export interface Breakdown {
  total: number;
  by_status: CountMap;
}

export interface Outcome {
  category: ShadowCategory;
  horizon_minutes: number;
  count: number;
  positive: number;
  negative: number;
  sum_pnl_usdt: string;
  avg_pnl_usdt: string;
  min_pnl_usdt: string;
  max_pnl_usdt: string;
}

export interface Analytics {
  generated_at: number;
  window: { start: number; end: number; hours: number; bucket_minutes: number };
  timeline: { t: number; counts: CountMap }[];
  rules: (Breakdown & { rule: string })[];
  symbols: (Breakdown & { symbol: string })[];
  outcomes: Outcome[];
  decisions: DecisionRow[];
  shadow: ShadowRow[];
  notes: string[];
}

export interface SimulationResult {
  user_request: string;
  message: string;
  effective: { max_position_fraction_pct: number; max_spread_fraction_pct: number };
}
