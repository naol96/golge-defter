import time
from decimal import Decimal

from adapters.base import MarketAdapter
from contracts.models import MarketSnapshot


class MockMarketAdapter(MarketAdapter):
    """Explicitly labeled mock prices for tests and UI demos only."""

    def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        now = int(time.time())
        return MarketSnapshot(
            symbol=symbol,
            bid=Decimal("24.99"),
            ask=Decimal("25.00"),
            captured_at=now,
            source="MOCK",
            min_order_usdt=Decimal("10"),
        )
