const REFRESH_MS = 20000;
const DB = "data/golge.db";

function esc(s) {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmtTs(epoch) {
  if (!epoch) return "—";
  try {
    return new Date(epoch * 1000).toLocaleString("tr-TR");
  } catch {
    return String(epoch);
  }
}

function kvHtml(rows) {
  return `<dl class="kv">${rows
    .map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`)
    .join("")}</dl>`;
}

function renderMetrics(snap) {
  const r = snap.report || {};
  const items = [
    ["15 dk · canlı veri gözlemi", r.complete_15m_live_feed ?? "—"],
    ["60 dk · canlı veri gözlemi", r.complete_60m_live_feed ?? "—"],
    ["Risk nedeniyle engellenen", r.decisions_shadow_risk ?? 0],
    ["Teknik blok", r.decisions_technical_block ?? 0],
    ["PAPER bakiye", `${snap.paper_balance_usdt ?? "—"} USDT`],
  ];
  document.getElementById("metric-strip").innerHTML = items
    .map(
      ([label, value]) =>
        `<div class="metric"><div class="label">${esc(label)}</div><div class="value">${esc(value)}</div></div>`
    )
    .join("");
}

function renderHeader(snap) {
  const wb = document.getElementById("worker-badge");
  if (snap.worker_active) {
    wb.textContent = "Worker AKTIF";
    wb.className = "badge ok";
  } else {
    wb.textContent = "Worker KONTROL";
    wb.className = "badge warn";
  }
  document.getElementById("rules-badge").textContent = snap.rules_version || "rules";

  document.getElementById("footer-db").textContent = snap.db || "";
  document.getElementById("footer-updated").textContent = `Güncelleme: ${fmtTs(snap.generated_at)}`;
}

function renderSystem(snap) {
  const age = snap.last_decision_age_s != null ? `${snap.last_decision_age_s} sn` : "—";
  document.getElementById("system-body").innerHTML = kvHtml([
    ["Son piyasa kaynağı", snap.last_market_source || "—"],
    ["Son karar yaşı", age],
    ["Bekleyen değerlendirme", snap.report?.pending_evaluations ?? "—"],
    ["Açık PAPER pozisyon", (snap.open_positions || []).length],
  ]);
}

function renderConstitution(snap) {
  const c = snap.constitution || {};
  const pos = (snap.open_positions || [])
    .map((p) => `${p.symbol} ${p.notional_usdt} USDT`)
    .join(", ");
  document.getElementById("constitution-body").innerHTML = kvHtml([
    ["Tek işlem tavanı", `%${c.tek_islem_tavan_pct}`],
    ["Max açık pozisyon", c.max_acik_pozisyon],
    ["Max toplam risk", `%${c.max_toplam_risk_pct}`],
    ["Makas tavanı", `%${c.max_spread_pct}`],
    ["Stop", `%${c.stop_loss_pct}`],
    ["Günlük zarar", `%${c.gunluk_zarar_pct}`],
    ["Bekleme", `${c.bekleme_dk} dk / parite`],
    ["Gözlem eşiği", `${c.gozlem_esigi_usdt} USDT`],
    ["Açık pozisyonlar", pos || "—"],
  ]);
}

function renderShadow(snap) {
  const eb = snap.eval_breakdown || {};
  const summary = kvHtml([
    ["15 dk COMPLETE", eb["15"]?.COMPLETE ?? 0],
    ["15 dk PENDING", eb["15"]?.PENDING ?? 0],
    ["60 dk COMPLETE", eb["60"]?.COMPLETE ?? 0],
    ["60 dk PENDING", eb["60"]?.PENDING ?? 0],
  ]);
  const cards = (snap.recent_shadow || [])
    .map((row) => {
      const pnl = row.pnl_usdt != null ? `PnL ${row.pnl_usdt} USDT` : "";
      const feed = row.feed_source ? `feed ${row.feed_source}` : "feed (bekliyor)";
      return `<div class="card">
        <div class="card-head">
          <span class="sym">#${esc(row.shadow_id)} ${esc(row.symbol)}</span>
          <span class="tag">${esc(row.horizon_minutes)} dk</span>
          <span class="tag">${esc(row.status)}</span>
          <span class="tag">${esc(row.category)}</span>
        </div>
        <div class="card-meta">${esc(feed)} ${esc(pnl)}</div>
      </div>`;
    })
    .join("");
  document.getElementById("shadow-body").innerHTML = summary + `<div class="cards shadow-records">${cards || "<p class=\"hint\">Kayıt yok</p>"}</div>`;
}

function renderDecisions(snap) {
  const summary = snap.decisions_summary || {};
  document.getElementById("decision-chips").innerHTML = Object.entries(summary)
    .map(
      ([status, count]) =>
        `<span class="chip status-${esc(status)}">${esc(status)}: ${count}</span>`
    )
    .join("");

  document.getElementById("decisions-body").innerHTML = (snap.recent_decisions || [])
    .map((d) => {
      const expl = d.explanation ? d.explanation.slice(0, 120) : "";
      return `<div class="card">
        <div class="card-head">
          <span class="sym">#${esc(d.id)} ${esc(d.symbol)}</span>
          <span class="tag">${esc(d.status)}</span>
          <span class="tag">${esc(d.rule || "—")}</span>
          <span class="tag">${esc(d.signal_origin)}</span>
        </div>
        <div class="card-meta">${esc(d.market_source)} · ${fmtTs(d.created_at)} · ${esc(expl)}</div>
      </div>`;
    })
    .join("") || '<p class="hint">Henüz karar kaydı yok. Kaynak bağlandığında kararlar burada görünecek.</p>';
}

function renderChain(snap) {
  const a = snap.anchor;
  if (!a) {
    document.getElementById("chain-body").innerHTML =
      '<p class="hint">Henüz zincir kanıtı üretilmedi. Bir kayıt sabitlendiğinde hash ve doğrulama bilgisi burada görünecek.</p>';
    return;
  }
  const tx = a.snowtrace_tx ? "Fuji işlem kaydı mevcut" : "Yerel hash · Fuji işlemi bekleniyor";
  document.getElementById("chain-body").innerHTML = kvHtml([
    ["sha256", (a.sha256 || "").slice(0, 16) + "…"],
    ["Karar sayısı", a.decision_count],
    ["Üretim", a.generated_at],
    ["Zincir", tx],
  ]);
  if (a.snowtrace_tx) {
    try {
      const url = new URL(a.snowtrace_tx);
      if (url.protocol === "https:") {
        const link = document.createElement("a");
        link.href = url.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "İşlemi Snowtrace üzerinde doğrula ↗";
        document.getElementById("chain-body").append(link);
      }
    } catch { /* A malformed proof URL must not interrupt the dashboard. */ }
  }
}

function renderAll(snap) {
  renderHeader(snap);
  renderMetrics(snap);
  renderSystem(snap);
  renderConstitution(snap);
  renderShadow(snap);
  renderDecisions(snap);
  renderChain(snap);
}

async function loadSnapshot() {
  const res = await fetch(`/api/snapshot?db=${encodeURIComponent(DB)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

async function refresh() {
  try {
    const snap = await loadSnapshot();
    renderAll(snap);
    document.getElementById("connection-status").hidden = true;
  } catch (e) {
    document.getElementById("footer-updated").textContent = "Güncelleme başarısız";
    const status = document.getElementById("connection-status");
    status.hidden = false;
    status.textContent = `Veri yenilenemedi. Gösterilen kayıtlar güncel olmayabilir. ${e.message}`;
    const badge = document.getElementById("worker-badge");
    badge.className = "badge warn";
    badge.textContent = "Bağlantı kontrol edilmeli";
  }
}

document.getElementById("sim-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = document.getElementById("sim-input").value;
  const box = document.getElementById("sim-result");
  const button = ev.currentTarget.querySelector("button[type=submit]");
  button.disabled = true;
  box.textContent = "Simüle ediliyor…";
  try {
    const res = await fetch("/api/simulate-rule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Simülasyon başarısız");
    box.innerHTML = `<strong>${esc(data.message)}</strong><br/>Etkin tavan: %${esc(
      data.effective.max_position_fraction_pct
    )} · Makas: %${esc(data.effective.max_spread_fraction_pct)}`;
  } catch (e) {
    box.textContent = e.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById("sim-input").value = button.dataset.prompt;
    document.getElementById("sim-form").requestSubmit();
  });
});

refresh();
setInterval(refresh, REFRESH_MS);
