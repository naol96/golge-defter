// Display-only formatting. Stored decimal strings are never parsed into floats for
// rounding; fmtDecimal works on the digit string with BigInt so 0.1 + 0.2 issues
// can't leak into what the jury sees.

const DECIMAL_RE = /^([+-]?)(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/;

export function fmtDecimal(value: unknown, places = 2, opts: { signed?: boolean } = {}): string {
  const match = DECIMAL_RE.exec(String(value ?? "").trim());
  if (!match) return "—";
  const [, signRaw = "", intPart = "0", fracPart = "", expRaw] = match;
  const exponent = Number(expRaw || 0);
  if (Math.abs(exponent) > 1000) return "—";
  const digits = intPart + fracPart;
  const point = intPart.length + exponent;
  const integer = point <= 0 ? "0" : digits.slice(0, point).padEnd(point, "0");
  const fraction = point < 0 ? "0".repeat(-point) + digits : digits.slice(Math.max(0, point));
  const padded = fraction.padEnd(places + 1, "0");
  let scaled = BigInt(integer + padded.slice(0, places));
  if ((padded[places] ?? "0") >= "5") scaled += 1n;
  const nonzero = /[1-9]/.test(digits);
  const negative = signRaw === "-" && nonzero;
  const sign = negative ? "−" : opts.signed && nonzero ? "+" : "";
  if (scaled === 0n && nonzero) {
    return places === 0 ? `${sign}<1` : `${sign}<0,${"0".repeat(places - 1)}1`;
  }
  const result = scaled.toString().padStart(places + 1, "0");
  const whole = (places === 0 ? result : result.slice(0, -places)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return places === 0 ? `${sign}${whole}` : `${sign}${whole},${result.slice(-places)}`;
}

/** Exact sum for monetary strings; Number is reserved for visual ratios. */
export function sumDecimals(values: string[]): string {
  const parts = values.map((value) => {
    const match = DECIMAL_RE.exec(value);
    if (!match || Math.abs(Number(match[4] || 0)) > 1000) throw new Error("Invalid decimal");
    let scale = (match[3] || "").length - Number(match[4] || 0);
    let units = BigInt(match[2]! + (match[3] || "")) * (match[1] === "-" ? -1n : 1n);
    if (scale < 0) { units *= 10n ** BigInt(-scale); scale = 0; }
    return { units, scale };
  });
  const scale = Math.max(0, ...parts.map((p) => p.scale));
  const units = parts.reduce((sum, p) => sum + p.units * 10n ** BigInt(scale - p.scale), 0n);
  const digits = (units < 0n ? -units : units).toString().padStart(scale + 1, "0");
  return `${units < 0n ? "-" : ""}${scale ? digits.slice(0, -scale) + "." + digits.slice(-scale) : digits}`;
}

/** Sign of a decimal string without float conversion: -1, 0, 1, or null when unparsable. */
export function decimalSign(value: unknown): -1 | 0 | 1 | null {
  const match = DECIMAL_RE.exec(String(value ?? "").trim());
  if (!match) return null;
  if (!/[1-9]/.test((match[2] ?? "") + (match[3] ?? ""))) return 0;
  return match[1] === "-" ? -1 : 1;
}

export function fmtInt(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return Math.round(value).toLocaleString("tr-TR");
}

export function fmtPct(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const text = Number(value.toFixed(digits)).toLocaleString("tr-TR", { maximumFractionDigits: digits });
  return `%${text}`;
}

const timeFmt = new Intl.DateTimeFormat("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
const shortTimeFmt = new Intl.DateTimeFormat("tr-TR", { hour: "2-digit", minute: "2-digit" });
const dateTimeFmt = new Intl.DateTimeFormat("tr-TR", {
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

export function fmtTime(epoch: number | null | undefined, short = false): string {
  if (!epoch) return "—";
  return (short ? shortTimeFmt : timeFmt).format(new Date(epoch * 1000));
}

export function fmtDateTime(epoch: number | null | undefined): string {
  if (!epoch) return "—";
  return dateTimeFmt.format(new Date(epoch * 1000));
}

/** "3 sn", "4 dk", "2 sa 5 dk" — compact Turkish durations. */
export function fmtDuration(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds)) return "—";
  const s = Math.max(0, Math.round(Math.abs(seconds)));
  if (s < 60) return `${s} sn`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} dk`;
  const h = Math.floor(m / 60);
  const rest = m % 60;
  if (h < 48) return rest ? `${h} sa ${rest} dk` : `${h} sa`;
  return `${Math.floor(h / 24)} gün`;
}

export function fmtRelative(epoch: number | null | undefined, now: number): string {
  if (!epoch) return "—";
  const diff = now - epoch;
  if (Math.abs(diff) < 5) return "şimdi";
  return diff > 0 ? `${fmtDuration(diff)} önce` : `${fmtDuration(-diff)} sonra`;
}

export function shortHash(hash: string | undefined, head = 10, tail = 8): string {
  if (!hash) return "—";
  return hash.length <= head + tail + 1 ? hash : `${hash.slice(0, head)}…${hash.slice(-tail)}`;
}
