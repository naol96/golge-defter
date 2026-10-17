"""OKX Agent Trade Kit market adapter via MCP stdio (market module)."""
from __future__ import annotations

import json
import subprocess
import threading
import time
from decimal import Decimal
from queue import Empty, Queue

from adapters.base import MarketAdapter
from contracts.models import MarketSnapshot
from core.min_order import min_notional_usdt


class OkxAtkMarketAdapter(MarketAdapter):
    def __init__(
        self,
        site: str = "global",
        min_order_usdt: Decimal = Decimal("10"),
        timeout_seconds: float = 3.0,
    ) -> None:
        self.site = site
        self.min_order_usdt = min_order_usdt
        self.timeout_seconds = timeout_seconds

    def _call_tool(self, name: str, arguments: dict, *, timeout_seconds: float | None = None) -> dict:
        budget = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        if budget <= 0:
            raise TimeoutError("OKX ATK snapshot deadline exceeded")
        deadline = time.monotonic() + budget
        cmd = [
            "npx",
            "-y",
            "@okx_ai/okx-trade-mcp",
            "--modules",
            "market",
            "--read-only",
            "--site",
            self.site,
        ]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=0,
        )
        assert proc.stdin and proc.stdout

        def send(msg: dict) -> None:
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()

        def read_line(timeout: float) -> str | None:
            if timeout <= 0:
                return None
            q: Queue[str | Exception] = Queue()

            def worker() -> None:
                try:
                    q.put(proc.stdout.readline())
                except Exception as exc:  # pragma: no cover
                    q.put(exc)

            t = threading.Thread(target=worker, daemon=True)
            t.start()
            t.join(timeout)
            if t.is_alive():
                return None
            try:
                item = q.get_nowait()
            except Empty:
                return None
            if isinstance(item, Exception):
                raise item
            return item

        def response_for(request_id: int) -> dict:
            while True:
                line = read_line(deadline - time.monotonic())
                if not line:
                    raise TimeoutError(f"OKX ATK MCP response timeout: {name}")
                response = json.loads(line)
                if response.get("id") != request_id:
                    continue  # MCP notifications do not extend the shared deadline.
                if response.get("error"):
                    raise RuntimeError(str(response["error"]))
                return response

        try:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "golge-defter", "version": "0.1"},
                    },
                }
            )
            response_for(1)
            send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                }
            )
            payload = response_for(2)
            if payload.get("result", {}).get("isError"):
                raise RuntimeError("ATK MCP tool returned isError")
            content = payload.get("result", {}).get("content", [])
            if not content:
                raise RuntimeError("empty MCP tool response")
            text = content[0].get("text", "")
            parsed = json.loads(text)
            if not parsed.get("ok"):
                raise RuntimeError(parsed.get("error") or "ATK tool failed")
            return parsed
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=0.1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            proc.stdin.close()
            proc.stdout.close()

    def _instrument_min_order_usdt(self, symbol: str, ask: Decimal, *, timeout_seconds: float) -> Decimal:
        inst = self._call_tool(
            "market_get_instruments", {"instType": "SPOT", "instId": symbol},
            timeout_seconds=timeout_seconds,
        )
        rows = (inst.get("data") or {}).get("data") or []
        if not rows or rows[0].get("instId", symbol) != symbol:
            raise RuntimeError("instrument minimum unavailable or mismatched")
        spec = rows[0]
        min_sz = Decimal(str(spec.get("minSz") or "0"))
        lot_sz = Decimal(str(spec.get("lotSz") or "0"))
        if not min_sz.is_finite() or not lot_sz.is_finite() or min_sz <= 0 or lot_sz <= 0:
            raise RuntimeError("invalid instrument minimum; no assumed fallback")
        return min_notional_usdt(ask, min_sz, lot_sz_base=lot_sz)

    def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        deadline = time.monotonic() + self.timeout_seconds
        data = self._call_tool("market_get_ticker", {"instId": symbol},
                               timeout_seconds=deadline - time.monotonic())
        row = (data.get("data") or {}).get("data") or []
        if not row:
            raise RuntimeError("ticker missing data")
        tick = row[0]
        if tick.get("instId", symbol) != symbol:
            raise RuntimeError("ticker symbol mismatch")
        raw_ts = int(tick.get("ts") or 0)
        if raw_ts <= 0:
            raise RuntimeError("ticker timestamp missing; no fresh-time fallback")
        captured_at = raw_ts // 1000 if raw_ts > 10_000_000_000 else raw_ts
        ask = Decimal(str(tick["askPx"]))
        bid = Decimal(str(tick["bidPx"]))
        if not ask.is_finite() or not bid.is_finite() or not 0 < bid <= ask:
            raise RuntimeError("invalid ticker prices")
        min_order = self._instrument_min_order_usdt(
            symbol, ask, timeout_seconds=deadline - time.monotonic()
        )
        if time.monotonic() > deadline:
            raise TimeoutError("OKX ATK snapshot deadline exceeded")
        return MarketSnapshot(
            symbol=symbol,
            bid=bid,
            ask=ask,
            captured_at=captured_at,
            source="ATK_LIVE_MARKET",
            min_order_usdt=min_order,
        )
