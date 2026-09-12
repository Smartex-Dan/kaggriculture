"""
MarketModel - tracks market inventory/prices and estimates
expected current and future prices for resources.
"""
from typing import Any


class MarketModel:
    def update(self, observation: Any) -> None:
        raise NotImplementedError

    def expected_price(self, resource: str) -> float:
        raise NotImplementedError

    def expected_future_price(self, resource: str) -> float:
        raise NotImplementedError
