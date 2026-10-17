from __future__ import annotations

from abc import ABC, abstractmethod

from contracts.models import MarketSnapshot


class MarketAdapter(ABC):
    timeout_seconds: float = 3.0

    @abstractmethod
    def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        raise NotImplementedError
