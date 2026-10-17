"""Gölge Defter Streamlit kokpiti (PAPER)."""
from __future__ import annotations

import time
from decimal import Decimal
from pathlib import Path

import streamlit as st

from adapters.mock_market import MockMarketAdapter
from adapters.okx_atk import OkxAtkMarketAdapter
from contracts.models import ConstitutionRules
from core.analyst import demo_signal
from core.constitution_parser import apply_user_cap_request
from core.decision_engine import run_decision_cycle, utc_day
from core.position_monitor import monitor_open_positions
from core.shadow_evaluator import evaluate_due_shadows
from storage.database import Database

st.set_page_config(page_title="Gölge Defter", layout="wide")
st.title("Gölge Defter + Yatırım Anayasası")
st.caption("PAPER modu | LLM önerir, kurallar değerlendirir, broker simüle eder.")

db_path = st.sidebar.text_input("SQLite", value="data/golge.db")
source = st.sidebar.selectbox("Veri kaynağı", ["atk", "mock"], format_func=lambda x: x.upper())
symbol = st.sidebar.selectbox("Parite", ["AVAX-USDT", "BTC-USDT", "ETH-USDT"])
user_rule = st.sidebar.text_input("Doğal dil kuralı (sıkılaştırma)", "")

if st.sidebar.button("Döngüyü çalıştır"):
    db = Database(db_path)
    rules = ConstitutionRules()
    if user_rule.strip():
        rules, _, msg = apply_user_cap_request(rules, user_rule)
        st.sidebar.info(msg)
    adapter = OkxAtkMarketAdapter() if source == "atk" else MockMarketAdapter()
    try:
        market = adapter.fetch_snapshot(symbol)
    except Exception as exc:
        st.error(f"Piyasa verisi alınamadı: {exc}")
        st.stop()
    signal = demo_signal(market)
    now = int(time.time())
    decision, ref_id = run_decision_cycle(db, rules=rules, signal=signal, market=market, now=now)
    monitor_open_positions(db, market, now, utc_day(now))
    evaluate_due_shadows(db, market, now)
    st.session_state["last"] = (market, signal, decision, ref_id, now)

if "last" in st.session_state:
    market, signal, decision, ref_id, now = st.session_state["last"]
    age = now - market.captured_at
    stale = age > ConstitutionRules().max_data_age_seconds
    col1, col2, col3 = st.columns(3)
    col1.metric("Mod", "PAPER")
    col2.metric("Kaynak", market.source)
    col3.metric("Veri yaşı (sn)", age, delta=None)
    if stale:
        st.warning("Bayat veri: yeni alım açılmaz (fail-closed).")
    st.subheader("Karar kartı")
    st.json(
        {
            "sinyal_kaynagi": signal.origin,
            "aksiyon": signal.action,
            "gerekce": signal.reason,
            "durum": decision.status,
            "kural": decision.rule,
            "aciklama": decision.explanation,
            "tutar_usdt": str(decision.notional_usdt),
            "ref_id": ref_id,
        }
    )

    db = Database(db_path)
    with db.session() as conn:
        shadows = conn.execute(
            "SELECT * FROM shadow_trades ORDER BY id DESC LIMIT 20"
        ).fetchall()
        positions = conn.execute(
            "SELECT * FROM positions ORDER BY id DESC LIMIT 20"
        ).fetchall()
        evals = conn.execute(
            """
            SELECT se.*, st.symbol FROM shadow_evaluations se
            JOIN shadow_trades st ON st.id = se.shadow_id
            ORDER BY se.shadow_id DESC, se.horizon_minutes
            LIMIT 40
            """
        ).fetchall()
    st.subheader("Gölge Defter")
    st.dataframe([dict(r) for r in shadows], use_container_width=True)
    st.subheader("Gölge değerlendirmeleri (15/60 dk)")
    st.dataframe([dict(r) for r in evals], use_container_width=True)
    st.subheader("Açık / kapalı pozisyonlar")
    st.dataframe([dict(r) for r in positions], use_container_width=True)
    bal = db.get_paper_balance()
    st.info(f"Sanal bakiye (PAPER): {bal} USDT — gerçek hesap değildir.")
else:
    st.info("Soldan döngüyü çalıştırın. Demo sinyal açıkça DEMO olarak etiketlenir.")
