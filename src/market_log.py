"""
Basic market snapshotting - one row per turn, per resource.
Not prediction, just data collection per V0.5 scope.
"""
import csv
import os

_PATH = os.path.join("experiments", "market_log.csv")
_last_prices = {}


def log_market(state) -> None:
    global _last_prices
    row_base = {"step": state.step}
    file_exists = os.path.isfile(_PATH)
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    with open(_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "resource", "price", "prev_price", "inventory"])
        if not file_exists:
            writer.writeheader()
        for resource, price in state.prices.items():
            writer.writerow({
                **row_base, "resource": resource, "price": price,
                "prev_price": _last_prices.get(resource),
                "inventory": state.market_inventory.get(resource),
            })
    _last_prices = dict(state.prices)