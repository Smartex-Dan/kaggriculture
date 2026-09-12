"""Inventory awareness - what to sell, whether we can afford to plant/buy."""


def sellable_produce(shed: dict) -> dict:
    """Non-zero produce quantities currently in the shed."""
    return {k: v for k, v in shed.items() if v > 0}


def has_seeds(seeds: dict, crop: str) -> bool:
    return seeds.get(crop, 0) > 0


def can_afford(money: float, cost: float) -> bool:
    return money >= cost