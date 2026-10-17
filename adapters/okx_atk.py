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

    def _call_tool(self, name: str, arguments: dict) -> dict:
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
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
        )
        assert proc.stdin and proc.stdout

        def send(msg: dict) -> None:
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()

        def read_line(timeout: float) -> str | None:
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
            if not read_line(self.timeout_seconds):
                raise TimeoutError("OKX ATK MCP initialize timeout")
            send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                }
            )
            line = read_line(self.timeout_seconds)
            if not line:
                raise TimeoutError(f"OKX ATK MCP tool timeout: {name}")
            payload = json.loads(line)
            if payload.get("error"):
                raise RuntimeError(str(payload["error"]))
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
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()

    def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        data = self._call_tool("market_get_ticker", {"instId": symbol})
        row = (data.get("data") or {}).get("data") or []
        if not row:
            raise RuntimeError("ticker missing data")
        tick = row[0]
        fetched_at = int(time.time())
        raw_ts = int(tick.get("ts") or 0)
        if raw_ts > 10_000_000_000:
            tick_at = int(raw_ts / 1000)
        elif raw_ts > 1_000_000_000:
            tick_at = raw_ts
        else:
            tick_at = fetched_at
        captured_at = tick_at if abs(fetched_at - tick_at) <= 10 else fetched_at
        return MarketSnapshot(
            symbol=symbol,
            bid=Decimal(str(tick["bidPx"])),
            ask=Decimal(str(tick["askPx"])),
            captured_at=captured_at,
            source="ATK_LIVE_MARKET",
            min_order_usdt=self.min_order_usdt,
        )
