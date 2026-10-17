// One place for every user-facing label and for the status → color slot mapping.
// Series colors live in CSS (--s-approved …) so light/dark swap without JS.

export const STATUS_ORDER = ["APPROVED_PAPER", "SHADOW_RISK", "SHADOW_PASS", "TECHNICAL_BLOCK", "NO_DECISION"] as const;

export interface StatusMeta {
  label: string;
  short: string;
  tone: "approved" | "risk" | "pass" | "technical" | "neutral";
  color: string;
  icon: string;
  help: string;
}

export const STATUS_META: Record<string, StatusMeta> = {
  NO_DECISION: {
    label: "Karar yok", short: "Karar yok", tone: "neutral", color: "var(--ink-3)", icon: "—",
    help: "Veri veya sinyal doğrulanamadı; PAPER ya da gölge kaydı oluşmadı.",
  },
  APPROVED_PAPER: {
    label: "PAPER onayı",
    short: "Onay",
    tone: "approved",
    color: "var(--s-approved)",
    icon: "✓",
    help: "Anayasadan geçti; yalnızca PAPER icra edildi.",
  },
  SHADOW_RISK: {
    label: "Risk engeli",
    short: "Risk",
    tone: "risk",
    color: "var(--s-risk)",
    icon: "⛉",
    help: "Anayasa kuralı işlemi durdurdu; Gölge Defter'de izleniyor.",
  },
  SHADOW_PASS: {
    label: "Pas gözlemi",
    short: "Pas",
    tone: "pass",
    color: "var(--s-pass)",
    icon: "◌",
    help: "Analist PASS dedi; aday yine de 15/60 dk gözlenir.",
  },
  TECHNICAL_BLOCK: {
    label: "Teknik engel",
    short: "Teknik",
    tone: "technical",
    color: "var(--s-technical)",
    icon: "⚙",
    help: "İcra edilemez (minimum emir). Risk vetosu değildir.",
  },
};

export const CATEGORY_META: Record<string, { label: string; status: string }> = {
  CONSTITUTIONAL_RISK_BLOCK: { label: "Anayasal risk", status: "SHADOW_RISK" },
  PASS_OBSERVATION: { label: "Pas gözlemi", status: "SHADOW_PASS" },
  TECHNICAL_UNEXECUTABLE: { label: "Teknik kayıt", status: "TECHNICAL_BLOCK" },
};

export const RULE_META: Record<string, { label: string; detail: string }> = {
  OK: { label: "Uygun", detail: "Tüm anayasa kontrolleri geçti." },
  EXPOSURE: { label: "Toplam risk", detail: "Açık pozisyonların toplamı bakiyenin %50'sini aşamaz." },
  SPREAD: { label: "Makas", detail: "Alış-satış makası %0,15'i aşarsa giriş yok." },
  COOLDOWN: { label: "Bekleme", detail: "Aynı paritede kapanıştan sonra 15 dk beklenir." },
  MAX_POSITIONS: { label: "Pozisyon sayısı", detail: "Aynı anda en fazla 2 açık pozisyon." },
  PAIR: { label: "Parite", detail: "Yalnızca izinli pariteler işlem görebilir." },
  DAILY_LOSS: { label: "Günlük zarar", detail: "Gün başı bakiyenin %5'i ile 5 USDT sınırından küçüğü." },
  ANALYST: { label: "Analist pas", detail: "Analist işlem önermedi." },
  DATA: { label: "Veri kontrolü", detail: "Bayat, gelecekteki veya tutarsız piyasa verisiyle işlem yapılmaz." },
  SIGNAL: { label: "Sinyal kontrolü", detail: "Analist yanıtı doğrulanamadı; karar verilmedi." },
  STALE_DATA: { label: "Veri yaşı", detail: "Piyasa verisi 10 saniyeden eski olamaz." },
  MIN_ORDER: { label: "Min emir", detail: "Anayasal tutar borsa minimum emrinin altında (teknik)." },
  OBSERVATION: { label: "Eski min emir kaydı", detail: "Eski sınıflandırma; minimum altında kalan aday teknik kayıttır." },
  ANALYST_PASS: { label: "Analist pas", detail: "Analist işlem önermedi." },
  PASS: { label: "Analist pas", detail: "Analist işlem önermedi." },
};

export function statusMeta(status: string | null | undefined): StatusMeta {
  return (
    STATUS_META[status ?? ""] ?? {
      label: status || "—",
      short: status || "—",
      tone: "neutral",
      color: "var(--ink-3)",
      icon: "·",
      help: "",
    }
  );
}

export function ruleLabel(rule: string | null | undefined): string {
  if (!rule) return "—";
  return RULE_META[rule]?.label ?? rule;
}

export const SOURCE_LABELS: Record<string, string> = {
  ATK_LIVE_MARKET: "ATK canlı",
  ATK: "ATK canlı",
  MOCK: "Mock",
  FIXTURE: "Fixture",
  FIXTURE_SYNTHETIC_NOT_LIVE: "Sentetik",
  LLM: "LLM",
  DEMO: "Demo analist",
  UNKNOWN: "Bilinmiyor",
};

export function sourceLabel(src: string | null | undefined): string {
  if (!src) return "—";
  return SOURCE_LABELS[src] ?? src;
}

export function isLiveSource(src: string | null | undefined): boolean {
  return src === "ATK_LIVE_MARKET" || src === "ATK";
}
