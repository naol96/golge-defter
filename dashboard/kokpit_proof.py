"""Salt okunur 4 panel kokpit — canlı worker DB'sine yazmaz."""
from __future__ import annotations

import sqlite3
import time
from decimal import Decimal
from pathlib import Path

import streamlit as st

from contracts.models import ConstitutionRules

st.set_page_config(page_title="Gölge Defter — Live Proof", layout="wide")
st.title("GÖLGE DEFTER — Live Proof")
st.caption("PAPER ONLY · SQLite salt okunur · Worker döngüsü burada çalıştırılmaz")

rules = ConstitutionRules()
db_path = st.sidebar.text_input("SQLite (ro)", value="data/golge.db")
refresh = st.sidebar.slider("Yenileme (sn)", 5, 120, 30)
if st.sidebar.button("Yenile"):
    st.rerun()

time.sleep(0)  # placeholder for auto-refresh via streamlit fragment if enabled later

path = Path(db_path).expanduser().resolve()
if not path.is_file():
    st.error(f"DB bulunamadı: {path}")
    st.stop()

conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row


def scalar(sql: str, params: tuple = ()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


pid_file = Path("data/atk_worker.pid")
worker_ok = False
if pid_file.is_file():
    try:
        import os

        worker_ok = os.kill(int(pid_file.read_text().strip()), 0) is None
    except (OSError, ValueError):
        worker_ok = False

last_dec = conn.execute(
    "SELECT created_at, market_source, status, rule FROM decisions ORDER BY id DESC LIMIT 1"
).fetchone()
now = int(time.time())

with st.container(border=True):
    st.subheader("1 · Canlı sistem")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Worker", "AKTIF" if worker_ok else "KONTROL")
    c2.metric("Kural sürümü (kod)", rules.rules_version)
    src = last_dec["market_source"] if last_dec else "—"
    c3.metric("Son kaynak", src)
    if last_dec:
        age = now - int(last_dec["created_at"])
        c4.metric("Son karar (sn önce)", age)
    else:
        c4.metric("Son karar", "—")

with st.container(border=True):
    st.subheader("2 · Yatırım Anayasası (MVP)")
    bal = Decimal(str(scalar("SELECT balance_usdt FROM paper_state WHERE id=1") or "0"))
    open_n = scalar("SELECT COUNT(*) FROM positions WHERE status='OPEN'")
    st.write(
        {
            "tek_islem_tavan": f"%{rules.max_position_fraction * 100:g}",
            "max_acik_pozisyon": rules.max_open_positions,
            "max_toplam_risk": f"%{rules.max_total_exposure_fraction * 100:g}",
            "gunluk_zarar": f"gün başı bakiyenin %{rules.max_daily_realized_loss_fraction * 100:g}'i",
            "bekleme": f"{rules.pair_cooldown_seconds // 60} dk / parite",
            "gözlem_esigi": f"{rules.observation_min_balance_usdt} USDT + min emir",
            "paper_bakiye": str(bal),
            "acik_pozisyon": open_n,
        }
    )

with st.container(border=True):
    st.subheader("3 · Gölge Defter")
    shadow_stats = conn.execute(
        """
        SELECT se.status, COUNT(*) AS c
        FROM shadow_evaluations se
        GROUP BY se.status
        """
    ).fetchall()
    st.write("Değerlendirme durumu:", {r["status"]: r["c"] for r in shadow_stats})
    recent = conn.execute(
        """
        SELECT st.id, st.symbol, st.category, se.horizon_minutes, se.status, se.pnl_usdt, se.feed_source
        FROM shadow_evaluations se
        JOIN shadow_trades st ON st.id = se.shadow_id
        ORDER BY se.evaluated_at DESC NULLS LAST, st.id DESC
        LIMIT 12
        """
    ).fetchall()
    st.dataframe([dict(r) for r in recent], use_container_width=True)

with st.container(border=True):
    st.subheader("4 · Analist kararları")
    by_status = conn.execute(
        "SELECT status, COUNT(*) AS c FROM decisions GROUP BY status ORDER BY c DESC"
    ).fetchall()
    st.write("Özet:", {r["status"]: r["c"] for r in by_status})
    decisions = conn.execute(
        """
        SELECT id, symbol, signal_origin, signal_action, status, rule, market_source, created_at
        FROM decisions ORDER BY id DESC LIMIT 15
        """
    ).fetchall()
    st.dataframe([dict(r) for r in decisions], use_container_width=True)

conn.close()
st.caption(f"Otomatik yenileme için sayfayı ~{refresh}s aralıkla yenileyin veya `streamlit run dashboard/kokpit_proof.py`.")
