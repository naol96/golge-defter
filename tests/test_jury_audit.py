"""PAPER-only regression cases from the final specification audit. No network."""
from dataclasses import replace
from decimal import Decimal as D
import time

import pytest

from adapters.okx_atk import OkxAtkMarketAdapter
from contracts.models import AnalystSignal, ConstitutionRules, MarketSnapshot, ShadowCategory
from core.constitution import evaluate
from core.decision_engine import run_decision_cycle, utc_day
from core.paper_broker import open_paper_position
from core.position_monitor import monitor_open_positions
from core.shadow_evaluator import evaluate_due_shadows, shadow_pnl
from dashboard.snapshot import build_kokpit_snapshot
from report import build_report
from storage.database import Database

NOW = 1_800_000_000


def market(*, at=NOW, source="MOCK", bid="99.9", ask="100", minimum="10"):
    return MarketSnapshot("AVAX-USDT", D(bid), D(ask), at, source, D(minimum))


def shadow(db, *, source="MOCK", category=ShadowCategory.PASS_OBSERVATION):
    return db.insert_shadow(symbol="AVAX-USDT", category=category, entry_ask=D("100"),
        notional_usdt=D("25"), reason="MOCK audit", constitution_rule="ANALYST",
        created_at=NOW, source=source)


@pytest.mark.parametrize("action", ["BUY", "PASS"])
@pytest.mark.parametrize("balance,bid", [("30", "99.9"), ("30", "90"), ("50", "90")])
def test_unexecutable_is_technical_before_risk_or_pass(action, balance, bid):
    tick = market(bid=bid, minimum="15")
    decision = evaluate(constitution=ConstitutionRules(),
        signal=AnalystSignal(tick.symbol, action, "audit"), market=tick,
        available_usdt=D(balance), min_order_usdt=tick.min_order_usdt,
        daily_realized_loss_usdt=D("5"), now=NOW)
    assert decision.status == "TECHNICAL_BLOCK"
    assert decision.shadow_category == ShadowCategory.TECHNICAL_UNEXECUTABLE


@pytest.mark.parametrize("age", [11, -1])
def test_atk_preserves_exchange_timestamp(monkeypatch, age):
    monkeypatch.setattr("adapters.okx_atk.time.time", lambda: NOW)
    adapter = OkxAtkMarketAdapter()
    def tool(name, args, **kwargs):
        rows = [{"ts": str((NOW-age)*1000), "bidPx": "99.9", "askPx": "100"}] if name == "market_get_ticker" else [{"minSz":"0.01","lotSz":"0.01"}]
        return {"ok":True,"data":{"data":rows}}
    monkeypatch.setattr(adapter, "_call_tool", tool)
    assert adapter.fetch_snapshot("AVAX-USDT").captured_at == NOW-age


def test_atk_missing_timestamp_is_not_fresh(monkeypatch):
    adapter=OkxAtkMarketAdapter()
    monkeypatch.setattr(adapter, "_call_tool", lambda *a, **kw: {"data":{"data":[{"bidPx":"99.9","askPx":"100"}]}})
    with pytest.raises((ValueError, RuntimeError)):
        adapter.fetch_snapshot("AVAX-USDT")


@pytest.mark.parametrize("tick", [market(at=NOW+900-11), market(at=NOW+901), market(at=NOW+900,bid="101"), market(at=NOW+900,bid="0")])
def test_invalid_market_cannot_complete_shadow(tmp_path, tick):
    db=Database(tmp_path/"audit.db"); shadow(db)
    assert evaluate_due_shadows(db,tick,NOW+900) == 0


def test_mock_cannot_complete_atk_shadow(tmp_path):
    db=Database(tmp_path/"audit.db"); shadow(db,source="ATK_LIVE_MARKET")
    assert evaluate_due_shadows(db,market(at=NOW+900),NOW+900) == 0


@pytest.mark.parametrize("tick", [market(at=NOW-11,bid="95"), market(at=NOW+1,bid="95"), market(bid="-1"), market(bid="NaN")])
def test_invalid_market_cannot_close_position(tmp_path, tick):
    db=Database(tmp_path/"audit.db")
    open_paper_position(db,market=market(at=NOW-20),notional_usdt=D("25"),rules=ConstitutionRules(),now=NOW-20)
    assert monitor_open_positions(db,tick,NOW,utc_day(NOW)) == []
    assert db.get_daily_loss(utc_day(NOW)) == 0


def test_mock_cannot_close_atk_position(tmp_path):
    db=Database(tmp_path/"audit.db")
    open_paper_position(db,market=market(source="ATK_LIVE_MARKET"),notional_usdt=D("25"),rules=ConstitutionRules(),now=NOW)
    assert monitor_open_positions(db,market(bid="95"),NOW,utc_day(NOW)) == []


def test_stop_loss_counts_both_fees_and_utc_reset(tmp_path):
    db=Database(tmp_path/"audit.db")
    pos=open_paper_position(db,market=market(),notional_usdt=D("25"),rules=ConstitutionRules(),now=NOW)
    assert monitor_open_positions(db,market(bid="95"),NOW,utc_day(NOW)) == [pos.id]
    # quantity .25; sell 23.75; sell fee .02375; buy fee .025.
    assert db.get_daily_loss(utc_day(NOW)) == D("1.29875")
    assert db.get_paper_balance() == D("98.70125")
    assert monitor_open_positions(db,market(bid="95"),NOW,utc_day(NOW)) == []
    assert db.get_daily_loss(utc_day(NOW+86400)) == 0


@pytest.mark.parametrize("horizon,bid,expected", [(15,"99","-0.29975"),(60,"101","0.19975")])
def test_exact_shadow_pnl_and_limited_stop_note(tmp_path,horizon,bid,expected):
    db=Database(tmp_path/"audit.db"); sid=shadow(db)
    at=NOW+horizon*60
    evaluate_due_shadows(db,market(at=at,bid=bid,ask=str(D(bid)+1)),at)
    with db.session() as conn:
        row=conn.execute("SELECT * FROM shadow_evaluations WHERE shadow_id=? AND horizon_minutes=?",(sid,horizon)).fetchone()
    assert D(row["pnl_usdt"]) == D(expected)
    assert "stop_dogrulamasi_sinirli" in row["note"]
    assert evaluate_due_shadows(db,market(at=at,bid="90"),at) == 0


def test_live_counter_requires_both_entry_and_exit(tmp_path):
    db=Database(tmp_path/"audit.db")
    for source,feed in [("MOCK","ATK_LIVE_MARKET"),("ATK_LIVE_MARKET","MOCK"),("ATK_LIVE_MARKET","ATK_LIVE_MARKET")]:
        sid=shadow(db,source=source)
        with db.session() as conn:
            conn.execute("UPDATE shadow_evaluations SET status='COMPLETE',feed_source=?,pnl_usdt='-1',evaluated_at=? WHERE shadow_id=?",(feed,NOW+3600,sid))
    report=build_report(db.path)
    assert report["complete_15m_live_feed"] == report["complete_60m_live_feed"] == 1
    snap=build_kokpit_snapshot(db.path)
    assert sum(snap["eval_breakdown"]["15"].values()) == 3
    assert snap["report"]["complete_15m"] == snap["eval_breakdown"]["15"]["COMPLETE"]


def test_daily_loss_never_loosens_fixed_five_usdt():
    decision=evaluate(constitution=ConstitutionRules(),signal=AnalystSignal("AVAX-USDT","BUY","audit"),
        market=market(),available_usdt=D("200"),min_order_usdt=D("10"),daily_realized_loss_usdt=D("5"),
        day_start_balance_usdt=D("200"),now=NOW)
    assert decision.rule == "DAILY_LOSS"


def test_stop_close_same_tick_blocks_next_buy(monkeypatch, tmp_path):
    """MOCK worker E2E: stop and daily loss must precede the next decision."""
    import shadow_agent
    db=Database(tmp_path/"worker.db")
    rules=ConstitutionRules()
    db.get_day_start_balance(utc_day(NOW))
    open_paper_position(db,market=market(at=NOW-1),notional_usdt=D("25"),rules=rules,now=NOW-1)
    db.add_daily_loss(utc_day(NOW),D("4"))
    tick=market(bid="95",ask="95.01")
    monkeypatch.setattr(shadow_agent.time,"time",lambda: NOW)
    monkeypatch.setattr(shadow_agent.MockMarketAdapter,"fetch_snapshot",lambda self,symbol: tick)
    shadow_agent.run_cycle(db,symbols=[tick.symbol],source="mock",analyst="demo")
    snap=build_kokpit_snapshot(db.path)
    assert snap["recent_decisions"][0]["rule"] == "DAILY_LOSS"
    assert snap["open_positions"] == []
    assert snap["decisions_summary"] == {"SHADOW_RISK":1}


def test_injected_atk_transport_to_dashboard_paper_and_shadow(monkeypatch,tmp_path):
    """MOCK transport of ATK API shape, NOT evidence of an actual live fetch."""
    import shadow_agent
    import adapters.okx_atk
    tick_time=[NOW]
    price=[D("100")]
    def tool(self,name,args,**kwargs):
        if name == "market_get_ticker":
            row={"instId":args["instId"],"ts":str(tick_time[0]*1000),"askPx":str(price[0]),"bidPx":str(price[0]-D("0.01"))}
        else:
            row={"instId":args["instId"],"minSz":"0.01","lotSz":"0.01"}
        return {"ok":True,"data":{"data":[row]}}
    monkeypatch.setattr(adapters.okx_atk.OkxAtkMarketAdapter,"_call_tool",tool)
    monkeypatch.setattr(shadow_agent.time,"time",lambda: tick_time[0])
    db=Database(tmp_path/"transport.db")
    # Two cycles: first PAPER, second blocked by portfolio exposure.
    for _ in range(2):
        shadow_agent.run_cycle(db,symbols=["AVAX-USDT"],source="atk",analyst="demo")
    snap=build_kokpit_snapshot(db.path)
    assert snap["decisions_summary"] == {"APPROVED_PAPER":1,"SHADOW_RISK":1}
    assert snap["report"]["decisions_by_signal_origin"] == {"DEMO":2}
    assert snap["report"]["decisions_by_market_source"] == {"ATK_LIVE_MARKET":2}
    for horizon in (15,60):
        tick_time[0]=NOW+horizon*60
        price[0]=D("101")
        adapter=OkxAtkMarketAdapter()
        tick=adapter.fetch_snapshot("AVAX-USDT")
        assert evaluate_due_shadows(db,tick,tick_time[0]) == 1
        assert evaluate_due_shadows(db,tick,tick_time[0]) == 0
    snap=build_kokpit_snapshot(db.path)
    assert snap["report"]["complete_15m_live_feed"] == 1
    assert snap["report"]["complete_60m_live_feed"] == 1
    assert snap["recent_shadow"][0]["signal_origin"] == "DEMO"
    assert all("stop_dogrulamasi_sinirli" in r["note"] for r in snap["recent_shadow"])
    assert all(r["entry_source"] == r["feed_source"] == "ATK_LIVE_MARKET" for r in snap["recent_shadow"])


def test_legacy_technical_rows_are_not_risk_counts(tmp_path):
    db=Database(tmp_path/"legacy.db")
    sid=shadow(db,category=ShadowCategory.CONSTITUTIONAL_RISK_BLOCK)
    with db.session() as conn:
        conn.execute("UPDATE shadow_trades SET constitution_rule='OBSERVATION' WHERE id=?",(sid,))
    db.insert_decision(symbol="AVAX-USDT",signal_action="BUY",signal_reason="legacy",signal_origin="DEMO",
        status="SHADOW_RISK",rule="OBSERVATION",explanation="old classification",notional_usdt=D("7.5"),
        market_source="MOCK",ref_id=sid,created_at=NOW)
    snap=build_kokpit_snapshot(db.path)
    assert snap["report"]["decisions_shadow_risk"] == 0
    assert snap["report"]["decisions_technical_block"] == 1
    assert snap["report"]["shadow_by_category"] == {"TECHNICAL_UNEXECUTABLE":1}
    assert snap["recent_decisions"][0]["status"] == "TECHNICAL_BLOCK"
    assert snap["recent_decisions"][0]["raw_status"] == "SHADOW_RISK"
    assert all(r["category"] == "TECHNICAL_UNEXECUTABLE" for r in snap["recent_shadow"])
    with db.session() as conn:
        assert conn.execute("SELECT status FROM decisions").fetchone()[0] == "SHADOW_RISK"


def test_snapshot_uses_single_read_transaction(monkeypatch,tmp_path):
    import dashboard.snapshot as module
    db=Database(tmp_path/"atomic.db")
    with db.session() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
    original=module.build_report
    def report_then_concurrent_write(path,**kwargs):
        result=original(path,**kwargs)
        run_decision_cycle(db,rules=ConstitutionRules(),signal=AnalystSignal("AVAX-USDT","PASS","MOCK"),market=market(),now=NOW)
        return result
    monkeypatch.setattr(module,"build_report",report_then_concurrent_write)
    snap=module.build_kokpit_snapshot(db.path)
    assert snap["report"]["decisions_by_status"] == snap["decisions_summary"] == {}
    assert snap["recent_decisions"] == []
    assert snap["recent_shadow"] == []
    assert all(v == 0 for h in snap["eval_breakdown"].values() for v in h.values())
    assert build_report(db.path)["decisions_by_status"] == {"SHADOW_PASS":1}


def test_llm_fail_closed_does_not_create_shadow_performance(tmp_path,monkeypatch):
    from core.analyst import resolve_signal
    monkeypatch.delenv("OPENAI_API_KEY",raising=False)
    signal=resolve_signal(market(),analyst="llm")
    assert signal.origin == "LLM"
    db=Database(tmp_path/"llm.db")
    decision,ref=run_decision_cycle(db,rules=ConstitutionRules(),signal=signal,market=market(),now=NOW)
    assert decision.status == "NO_DECISION"
    assert ref is None
    assert build_report(db.path)["shadow_by_category"] == {}


def test_analyst_rejects_amount_authority():
    from core.analyst import validate_analyst_payload
    with pytest.raises(ValueError):
        validate_analyst_payload({"symbol":"AVAX-USDT","action":"BUY","reason":"MOCK","amount":80})


def test_llm_request_contains_market_and_rejects_different_symbol(monkeypatch):
    import json
    import urllib.request
    from core.analyst import llm_signal
    monkeypatch.setenv("OPENAI_API_KEY","MOCK_NOT_A_KEY")
    def urlopen(req,timeout):
        body=json.loads(req.data)
        prompt=body["messages"][1]["content"]
        assert '"bid": "99.9"' in prompt and '"ask": "100"' in prompt
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return json.dumps({"choices":[{"message":{"content":json.dumps({"symbol":"BTC-USDT","action":"BUY","reason":"MOCK"})}}]}).encode()
        return Response()
    monkeypatch.setattr(urllib.request,"urlopen",urlopen)
    signal=llm_signal(market())
    assert signal.action == "PASS" and signal.reason.startswith("LLM_FAIL_CLOSED:")


def test_local_hash_is_not_blockchain_and_batch_count_is_exact(tmp_path,monkeypatch):
    from chain.anchor_job import build_manifest
    db=Database(tmp_path/"chain.db")
    for _ in range(3):
        run_decision_cycle(db,rules=ConstitutionRules(),signal=AnalystSignal("AVAX-USDT","PASS","MOCK"),market=market(),now=NOW)
    monkeypatch.setenv("FUJI_LAST_TX","https://testnet.snowtrace.io/tx/"+"a"*64)
    manifest=build_manifest(db.path,limit=2)
    assert manifest["decision_count"] == 2 and manifest["total_decision_count"] == 3
    assert manifest["blockchain_verified"] is False
    assert manifest["proof_kind"] == "LOCAL_SHA256"
    assert len(manifest["sha256"]) == 64
    first=manifest["sha256"]
    with db.session() as conn:
        conn.execute("UPDATE decisions SET signal_reason='changed' WHERE id=3")
    assert build_manifest(db.path,limit=2)["sha256"] != first


def test_manifest_claim_cannot_self_verify(tmp_path,monkeypatch):
    import json
    import dashboard.snapshot as module
    evidence=tmp_path/"evidence"; evidence.mkdir()
    (evidence/"anchor_manifest.json").write_text(json.dumps({"sha256":"a"*64,"blockchain_verified":True}))
    monkeypatch.setattr(module,"ROOT",tmp_path)
    assert module._load_anchor_manifest()["blockchain_verified"] is False


def test_atk_unknown_minimum_fails_closed(monkeypatch):
    adapter=OkxAtkMarketAdapter()
    def tool(name,args,**kwargs):
        row=[{"ts":str(NOW*1000),"bidPx":"99.9","askPx":"100"}] if name=="market_get_ticker" else []
        return {"data":{"data":row}}
    monkeypatch.setattr(adapter,"_call_tool",tool)
    with pytest.raises(RuntimeError,match="minimum unavailable"):
        adapter.fetch_snapshot("AVAX-USDT")


def test_atk_mcp_notifications_share_three_second_deadline(monkeypatch):
    """Controlled clock: initialization consumes budget; tool gets the remainder."""
    import io,json
    import adapters.okx_atk as module
    clock=[0.0]
    class Stream(io.StringIO):
        def readline(self):
            clock[0]+=0.9
            return super().readline()
    class Process:
        stdin=io.StringIO()
        stdout=Stream('\n'.join(json.dumps(p) for p in [
            {"jsonrpc":"2.0","method":"notification"},
            {"jsonrpc":"2.0","id":1,"result":{}},
            {"jsonrpc":"2.0","method":"notification"},
            {"jsonrpc":"2.0","method":"notification"},
            {"jsonrpc":"2.0","id":2,"result":{"content":[]}},
        ])+'\n')
        def terminate(self): pass
        def wait(self,timeout=None): pass
    monkeypatch.setattr(module.subprocess,"Popen",lambda *a,**kw: Process())
    monkeypatch.setattr(module.time,"monotonic",lambda:clock[0])
    with pytest.raises(TimeoutError):
        OkxAtkMarketAdapter(timeout_seconds=3)._call_tool("market_get_ticker",{})


def test_snapshot_deadline_is_shared_by_ticker_and_instrument(monkeypatch):
    import adapters.okx_atk as module
    clock=[0.0]; budgets=[]
    def tool(self,name,args,**kwargs):
        budgets.append(kwargs["timeout_seconds"])
        clock[0]+=2
        rows=[{"ts":str(NOW*1000),"bidPx":"99.9","askPx":"100"}] if name=="market_get_ticker" else [{"minSz":".01","lotSz":".01"}]
        return {"data":{"data":rows}}
    monkeypatch.setattr(module.time,"monotonic",lambda:clock[0])
    monkeypatch.setattr(module.OkxAtkMarketAdapter,"_call_tool",tool)
    with pytest.raises(TimeoutError):
        module.OkxAtkMarketAdapter().fetch_snapshot("AVAX-USDT")
    assert budgets == [3,1]


def test_worker_time_is_taken_after_fetch(monkeypatch,tmp_path):
    import shadow_agent
    clock=[NOW]
    def fetch(self,symbol):
        clock[0]+=2
        return market(at=clock[0])
    monkeypatch.setattr(shadow_agent.time,"time",lambda:clock[0])
    monkeypatch.setattr(shadow_agent.MockMarketAdapter,"fetch_snapshot",fetch)
    db=Database(tmp_path/"clock.db")
    shadow_agent.run_cycle(db,symbols=["AVAX-USDT"],source="mock",analyst="demo")
    assert build_kokpit_snapshot(db.path)["recent_decisions"][0]["status"] == "APPROVED_PAPER"


def test_early_late_and_immutable_evaluation(tmp_path):
    db=Database(tmp_path/"timing.db"); sid=shadow(db)
    assert evaluate_due_shadows(db,market(at=NOW+899),NOW+899)==0
    assert evaluate_due_shadows(db,market(at=NOW+1021,bid="99"),NOW+1021)==1
    with db.session() as conn:
        first=dict(conn.execute("SELECT * FROM shadow_evaluations WHERE shadow_id=? AND horizon_minutes=15",(sid,)).fetchone())
    assert "LATE_EVALUATION" in first["note"]
    assert evaluate_due_shadows(db,market(at=NOW+1100,bid="90"),NOW+1100)==0
    with db.session() as conn:
        second=dict(conn.execute("SELECT * FROM shadow_evaluations WHERE shadow_id=? AND horizon_minutes=15",(sid,)).fetchone())
    assert first==second


def test_position_provenance_migration_recovers_from_matching_decision(tmp_path):
    db=Database(tmp_path/"migration.db")
    result,ref=run_decision_cycle(db,rules=ConstitutionRules(),signal=AnalystSignal("AVAX-USDT","BUY","MOCK"),market=market(source="ATK_LIVE_MARKET"),now=NOW)
    assert result.status=="APPROVED_PAPER"
    with db.session() as conn:
        conn.execute("UPDATE positions SET market_source='' WHERE id=?",(ref,))
    migrated=Database(db.path)
    with migrated.session() as conn:
        assert conn.execute("SELECT market_source FROM positions WHERE id=?",(ref,)).fetchone()[0]=="ATK_LIVE_MARKET"
    assert monitor_open_positions(migrated,market(source="MOCK",bid="95"),NOW,utc_day(NOW))==[]
    assert monitor_open_positions(migrated,market(source="ATK_LIVE_MARKET",bid="95"),NOW,utc_day(NOW))==[ref]


@pytest.mark.parametrize("bid,should_close",[("97.50001",False),("97.5",True),("90",True)])
def test_stop_threshold_and_gap_execute_at_actual_bid(tmp_path,bid,should_close):
    db=Database(tmp_path/"threshold.db")
    position=open_paper_position(db,market=market(),notional_usdt=D("25"),rules=ConstitutionRules(),now=NOW)
    closed=monitor_open_positions(db,market(bid=bid),NOW,utc_day(NOW))
    assert closed==([position.id] if should_close else [])
    if should_close:
        expected=-(shadow_pnl(D("100"),D(bid),D("25")))
        assert db.get_daily_loss(utc_day(NOW))==expected


def test_daily_loss_resets_on_utc_boundary_but_includes_new_close(tmp_path):
    from datetime import datetime,timezone
    midnight=int(datetime(2026,10,18,tzinfo=timezone.utc).timestamp())
    db=Database(tmp_path/"midnight.db")
    db.add_daily_loss(utc_day(midnight-1),D("5"))
    open_paper_position(db,market=market(at=midnight-1),notional_usdt=D("25"),rules=ConstitutionRules(),now=midnight-1)
    monitor_open_positions(db,market(at=midnight,bid="95"),midnight,utc_day(midnight))
    assert db.get_daily_loss(utc_day(midnight))==D("1.29875")


@pytest.mark.parametrize("source",["MOCK","ATK_LIVE_MARKET"])
def test_stale_decision_creates_neither_paper_nor_shadow(tmp_path,source):
    db=Database(tmp_path/"stale.db")
    decision,ref=run_decision_cycle(db,rules=ConstitutionRules(),signal=AnalystSignal("AVAX-USDT","BUY","audit"),market=market(at=NOW-11,source=source),now=NOW)
    snap=build_kokpit_snapshot(db.path)
    assert decision.status=="NO_DECISION" and ref is None
    assert snap["open_positions"]==snap["recent_shadow"]==[]


def test_due_time_requires_quote_from_horizon_not_just_fresh_quote(tmp_path):
    db=Database(tmp_path/"horizon-quote.db"); shadow(db)
    assert evaluate_due_shadows(db,market(at=NOW+899),NOW+900)==0
    assert evaluate_due_shadows(db,market(at=NOW+900),NOW+900)==1
