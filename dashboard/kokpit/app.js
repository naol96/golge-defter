const themeToggle = document.getElementById("theme-toggle");
function syncThemeButton() {
  const dark = document.documentElement.dataset.theme === "dark";
  themeToggle.textContent = dark ? "Tema: Koyu" : "Tema: Açık";
  themeToggle.setAttribute("aria-pressed", String(dark));
}
syncThemeButton();
themeToggle.addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  syncThemeButton();
  try { localStorage.setItem("golge-theme", theme); } catch { /* Theme still works without storage. */ }
});

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

// Display-only rounding uses integer arithmetic; stored Decimal values stay intact.
function fmtUsdt(value, places = 6) {
  const match = /^([+-]?)(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/.exec(String(value ?? ""));
  if (!match) return "—";
  const exponent = Number(match[4] || 0);
  if (Math.abs(exponent) > 1000) return "—";
  const digits = match[2] + (match[3] || "");
  const point = match[2].length + exponent;
  const integer = point <= 0 ? "0" : digits.slice(0, point).padEnd(point, "0");
  const fraction = point < 0 ? "0".repeat(-point) + digits : digits.slice(Math.max(0, point));
  const padded = fraction.padEnd(places + 1, "0");
  let scaled = BigInt(integer + padded.slice(0, places));
  if (padded[places] >= "5") scaled += 1n;
  const nonzero = /[1-9]/.test(digits);
  const sign = match[1] === "-" && nonzero ? "−" : "";
  if (scaled === 0n && nonzero) return `${sign}<0,${"0".repeat(places - 1)}1`;
  const result = scaled.toString().padStart(places + 1, "0");
  const whole = result.slice(0, -places).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${sign}${whole},${result.slice(-places)}`;
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
    ["15 dk · ATK kökenli gözlem", r.complete_15m_live_feed ?? "—"],
    ["60 dk · ATK kökenli gözlem", r.complete_60m_live_feed ?? "—"],
    ["Risk nedeniyle engellenen", r.decisions_shadow_risk ?? 0],
    ["Teknik blok", r.decisions_technical_block ?? 0],
    ["PAPER bakiye", `${fmtUsdt(snap.paper_balance_usdt, 2)} USDT`],
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
    ["Sinyal kökenleri", Object.entries(snap.report?.decisions_by_signal_origin || {}).map(([k,v]) => `${k}: ${v}`).join(" · ") || "—"],
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
    ["Günlük zarar", `En fazla ${c.gunluk_zarar_usdt} USDT ve gün başı %${c.gunluk_zarar_pct}`],
    ["Bekleme", `${c.bekleme_dk} dk / parite`],
    ["Minimum emir", "Veri adaptöründen · teknik kayıt"],
    ["Açık pozisyonlar", pos || "—"],
  ]);
}

const STATUS_LABELS = {
  APPROVED_PAPER: "PAPER onayı", SHADOW_RISK: "Risk engeli",
  SHADOW_PASS: "Pas gözlemi", TECHNICAL_BLOCK: "Teknik engel",
  NO_DECISION: "Karar yok", CONSTITUTIONAL_RISK_BLOCK: "Anayasal risk",
  PASS_OBSERVATION: "Pas gözlemi", TECHNICAL_UNEXECUTABLE: "Teknik kayıt", COMPLETE: "Tamamlandı", PENDING: "Bekliyor",
};

function statusHtml(status) {
  const tone = status === "APPROVED_PAPER" || status === "COMPLETE" ? "positive"
    : status === "SHADOW_RISK" || status === "TECHNICAL_BLOCK" ? "blocked" : "neutral";
  return `<span class="table-status ${tone}" title="${esc(status)}">${esc(STATUS_LABELS[status] || status || "—")}</span>`;
}

function tableHtml(caption, headers, rows, empty) {
  return `<div class="table-scroll" role="region" aria-label="${esc(caption)}" tabindex="0">
    <table class="data-table"><caption class="sr-only">${esc(caption)}</caption>
      <thead><tr>${headers.map((h) => `<th scope="col">${esc(h)}</th>`).join("")}</tr></thead>
      <tbody>${rows || `<tr><td colspan="${headers.length}" class="table-empty">${esc(empty)}</td></tr>`}</tbody>
    </table></div>`;
}

function renderShadow(snap) {
  const eb = snap.eval_breakdown || {};
  const summary = `<p class="hint">Tüm kategoriler dahildir. Teknik kayıtlar risk koruması sayılmaz.</p><div class="observation-summary">${[15, 60].map((minutes) =>
    `<span><strong>${minutes} dk</strong> ${esc(eb[minutes]?.COMPLETE ?? 0)} tamamlandı <span class="summary-divider">/</span> ${esc(eb[minutes]?.PENDING ?? 0)} bekliyor</span>`
  ).join("")}</div>`;
  const rows = (snap.recent_shadow || []).map((row) => `<tr>
    <td class="cell-id">#${esc(row.shadow_id)}</td>
    <th scope="row">${esc(row.symbol)}</th>
    <td class="nowrap">${esc(row.horizon_minutes)} dk</td>
    <td>${statusHtml(row.status)}</td>
    <td>${statusHtml(row.category)}</td>
    <td class="numeric">${row.pnl_usdt != null ? `<span title="Ham değer: ${esc(row.pnl_usdt)}">${esc(fmtUsdt(row.pnl_usdt))}</span><small>USDT · karşı-olgusal</small>` : "—"}</td>
    <td class="cell-source">Giriş: ${esc(row.entry_source || "—")}<small>Çıkış: ${esc(row.feed_source || "Bekleniyor")}<br>Sinyal: ${esc(row.signal_origin || "UNKNOWN")}</small></td>
    <td class="cell-time">Hedef: ${esc(fmtTs(row.target_at))}<small>Ölçüm: ${esc(fmtTs(row.evaluated_at))}<br>${esc(row.note || (row.status === "COMPLETE" ? "Eski kayıt: stop doğrulaması belgelenmedi" : "Ölçüm bekleniyor"))}</small></td>
  </tr>`).join("");
  document.getElementById("shadow-body").innerHTML = summary + tableHtml(
    "Gölge gözlem kayıtları", ["Kayıt", "Parite", "Pencere", "Gözlem durumu", "Karar sınıfı", "Net sonuç", "Veri / sinyal kökeni", "Ölçüm / sınırlamalar"],
    rows, "Henüz gölge kaydı yok. Engellenen veya pas geçilen adaylar burada izlenir."
  );
}

function renderDecisions(snap) {
  const summary = snap.decisions_summary || {};
  document.getElementById("decision-chips").innerHTML = Object.entries(summary)
    .map(([status, count]) => `<span class="chip status-${esc(status)}">${esc(STATUS_LABELS[status] || status)}: ${esc(count)}</span>`)
    .join("");
  const rows = (snap.recent_decisions || []).map((d) => `<tr>
    <td class="cell-id">#${esc(d.id)}</td>
    <th scope="row">${esc(d.symbol)}</th>
    <td>${statusHtml(d.status)}</td>
    <td class="cell-rule">${esc(d.rule || "—")}</td>
    <td class="cell-explanation">${esc(d.explanation || "Gerekçe kaydedilmedi.")}</td>
    <td class="cell-source">${esc(d.market_source || "—")}<small>${esc(d.signal_origin || "—")}</small></td>
    <td class="cell-time">${esc(fmtTs(d.created_at))}</td>
  </tr>`).join("");
  document.getElementById("decisions-body").innerHTML = tableHtml(
    "Analist kararları", ["Kayıt", "Parite", "Karar", "Kural", "Gerekçe", "Veri / sinyal kaynağı", "Zaman"],
    rows, "Henüz karar kaydı yok. Kaynak bağlandığında kararlar burada görünecek."
  );
}

function renderChain(snap) {
  const a = snap.anchor;
  if (!a) {
    document.getElementById("chain-body").innerHTML =
      '<p class="hint">Henüz zincir kanıtı üretilmedi. Bir kayıt sabitlendiğinde hash ve doğrulama bilgisi burada görünecek.</p>';
    return;
  }
  const tx = "Doğrulanmış blockchain kanıtı yok";
  document.getElementById("chain-body").innerHTML = kvHtml([
    ["Yerel SHA-256", a.sha256 || "—"],
    ["Manifest kayıt sayısı", a.decision_count],
    ["Hash kapsamı", `Son en fazla ${a.batch_limit ?? "—"} karar · eski manifestlerde kayıt sayısı farklı olabilir`],
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
        link.textContent = "Bildirilen işlem bağlantısı (doğrulanmadı) ↗";
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
