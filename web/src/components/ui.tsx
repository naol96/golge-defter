import { type ReactNode, useEffect, useId, useRef, useState } from "react";
import { decimalSign, fmtDecimal } from "../lib/format";
import { statusMeta } from "../lib/labels";

export function Panel({
  id,
  eyebrow,
  title,
  actions,
  children,
  className = "",
  footer,
}: {
  id?: string;
  eyebrow?: string;
  title: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  footer?: ReactNode;
}) {
  const headingId = useId();
  return (
    <section className={`panel ${className}`} id={id} aria-labelledby={headingId}>
      <header className="panel-head">
        <div>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          <h2 id={headingId}>{title}</h2>
        </div>
        {actions && <div className="panel-actions">{actions}</div>}
      </header>
      <div className="panel-body">{children}</div>
      {footer && <footer className="panel-foot">{footer}</footer>}
    </section>
  );
}

export function StatusPill({ status, label }: { status: string; label?: string }) {
  const meta = statusMeta(status);
  return (
    <span className={`pill tone-${meta.tone}`} title={meta.help || status}>
      <span className="pill-icon" aria-hidden="true">
        {meta.icon}
      </span>
      {label ?? meta.label}
    </span>
  );
}

export function Swatch({ color }: { color: string }) {
  return <span className="swatch" style={{ background: color }} aria-hidden="true" />;
}

export function Segmented<T extends string | number>({
  value,
  options,
  onChange,
  label,
  size = "md",
}: {
  value: T;
  options: { value: T; label: ReactNode; count?: number }[];
  onChange: (v: T) => void;
  label: string;
  size?: "sm" | "md";
}) {
  return (
    <div className={`segmented seg-${size}`} role="radiogroup" aria-label={label}>
      {options.map((o) => (
        <button
          key={String(o.value)}
          type="button"
          role="radio"
          aria-checked={o.value === value}
          className={o.value === value ? "on" : ""}
          onClick={() => onChange(o.value)}
        >
          {o.label}
          {o.count != null && <span className="seg-count">{o.count}</span>}
        </button>
      ))}
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="empty">
      <div className="empty-mark" aria-hidden="true">
        g.
      </div>
      <strong>{title}</strong>
      {children && <p>{children}</p>}
    </div>
  );
}

export function Skeleton({ h = 16, w = "100%", r = 6 }: { h?: number; w?: number | string; r?: number }) {
  return <span className="skeleton" style={{ height: h, width: w, borderRadius: r }} aria-hidden="true" />;
}

/** Counterfactual PnL: sign glyph + color, never color alone. */
export function Pnl({ value, places = 6, unit = true }: { value: string | null | undefined; places?: number; unit?: boolean }) {
  if (value == null) return <span className="muted">—</span>;
  const sign = decimalSign(value);
  const cls = sign === 1 ? "pnl-pos" : sign === -1 ? "pnl-neg" : "muted";
  return (
    <span className={`pnl ${cls}`} title={`Ham değer: ${value}`}>
      {fmtDecimal(value, places, { signed: true })}
      {unit && <small> USDT</small>}
    </span>
  );
}

export function CopyButton({ text, label = "Kopyala" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      className="btn btn-ghost btn-xs"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setDone(true);
          window.setTimeout(() => setDone(false), 1400);
        } catch {
          /* Clipboard may be blocked; the value stays selectable on screen. */
        }
      }}
    >
      {done ? "Kopyalandı ✓" : label}
    </button>
  );
}

/** Horizontal meter: value against a hard limit, with the limit drawn as a tick. */
export function Meter({
  value,
  max,
  limit,
  tone = "accent",
  label,
}: {
  value: number;
  max: number;
  limit?: number;
  tone?: "accent" | "warn" | "danger";
  label: string;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const lim = limit != null ? Math.max(0, Math.min(100, (limit / max) * 100)) : null;
  return (
    <div className={`meter meter-${tone}`} role="meter" aria-valuemin={0} aria-valuemax={max} aria-valuenow={value} aria-label={label}>
      <span className="meter-fill" style={{ width: `${pct}%` }} />
      {lim != null && <span className="meter-limit" style={{ left: `${lim}%` }} />}
    </div>
  );
}

export function Drawer({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const headingId = useId();
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeRef.current();
      if (e.key === "Tab") {
        const items = ref.current?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), [tabindex="0"]');
        const first = items?.[0], last = items?.[items.length - 1];
        if (e.shiftKey && (document.activeElement === first || document.activeElement === ref.current)) { e.preventDefault(); last?.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      prev?.focus?.();
    };
  }, [open]);
  if (!open) return null;
  return (
    <div className="drawer-root">
      <div className="drawer-scrim" onClick={onClose} />
      <div className="drawer" role="dialog" aria-modal="true" aria-labelledby={headingId} tabIndex={-1} ref={ref}>
        <header className="drawer-head">
          <h2 id={headingId}>{title}</h2>
          <button type="button" className="btn btn-ghost btn-icon" onClick={onClose} aria-label="Kapat">
            ✕
          </button>
        </header>
        <div className="drawer-body">{children}</div>
      </div>
    </div>
  );
}

export function KV({ rows }: { rows: [ReactNode, ReactNode][] }) {
  return (
    <dl className="kv">
      {rows.map(([k, v], i) => (
        <div key={i}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Floating tooltip anchored to viewport coordinates; flips to stay on-screen. */
export function FloatTip({ x, y, children }: { x: number; y: number; children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ left: x, top: y });
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const w = el.offsetWidth;
    const h = el.offsetHeight;
    let left = x + 14;
    let top = y - h - 10;
    if (left + w > window.innerWidth - 12) left = x - w - 14;
    if (top < 8) top = y + 16;
    setPos({ left: Math.max(8, left), top });
  }, [x, y]);
  return (
    <div className="float-tip" ref={ref} style={{ left: pos.left, top: pos.top }} role="tooltip">
      {children}
    </div>
  );
}
