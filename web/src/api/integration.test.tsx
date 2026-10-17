import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { demoAnalytics, demoSnapshot } from "./demo";
import { ConstitutionGrid } from "../components/constitution";
import { KpiStrip } from "../components/layout";
import { DecisionMix } from "../components/charts";
import { Pnl } from "../components/ui";

describe("Imported frontend audit compatibility", () => {
  it("labels offline data as synthetic and never counts it as live ATK/LLM proof", () => {
    const snap = demoSnapshot(), ana = demoAnalytics(3, 10);
    expect(snap.report.complete_15m_live_feed).toBe(0);
    expect(snap.report.complete_60m_live_feed).toBe(0);
    expect(snap.report.decisions_by_signal_origin.LLM).toBeUndefined();
    expect(ana.decisions.every((d) => d.market_source === "FIXTURE_SYNTHETIC_NOT_LIVE" && d.signal_origin === "DEMO")).toBe(true);
    expect(ana.shadow.every((s) => s.entry_source === "FIXTURE_SYNTHETIC_NOT_LIVE" && s.signal_origin === "DEMO")).toBe(true);
    expect(ana.shadow.filter((s) => s.status === "COMPLETE").every((s) => s.note?.includes("stop_dogrulamasi_sinirli"))).toBe(true);
    expect(snap.anchor?.proof_kind).toBe("DEMO_HASH_NOT_PROOF");
  });
  it("shows the audited daily loss and per-symbol minimum semantics", () => {
    const html = renderToStaticMarkup(<ConstitutionGrid snap={demoSnapshot()} />);
    expect(html).toContain("≤ 5 USDT");
    expect(html).toContain("daha küçük limit uygulanır");
    expect(html).toContain("Parite bazında");
    expect(html).not.toContain("Eski yedek");
    expect(html).not.toContain("Gözlem eşiği");
  });
  it("does not count NO_DECISION as a shadow trade", () => {
    const snap = demoSnapshot();
    snap.decisions_summary = { APPROVED_PAPER: 1, SHADOW_RISK: 1, TECHNICAL_BLOCK: 1, NO_DECISION: 3 };
    const html = renderToStaticMarkup(<KpiStrip snap={snap} />);
    expect(html).toContain("%33 gölgede");
  });
  it("keeps small negative PnL visible with its raw decimal value", () => {
    const html = renderToStaticMarkup(<Pnl value="-1E-9" />);
    expect(html).toContain("−&lt;0,000001");
    expect(html).toContain("Ham değer: -1E-9");
  });
  it("includes NO_DECISION in the distribution rather than stretching other segments", () => {
    const html = renderToStaticMarkup(<DecisionMix summary={{ APPROVED_PAPER: 1, SHADOW_RISK: 1, NO_DECISION: 3 }} />);
    expect(html).toContain("Karar yok");
    expect(html).toContain("%60");
  });

});
