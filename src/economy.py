"""
Profitability / ROI calculations for crops, animals, and land.

Expected Profit = Expected Revenue - Production Costs - Labor Costs - Opportunity Costs
"""


def expected_profit(revenue: float, production_cost: float,
                     labor_cost: float, opportunity_cost: float = 0.0) -> float:
    return revenue - production_cost - labor_cost - opportunity_cost


def crop_score(sale_price: float, seed_cost: float, expected_input_cost: float = 0.0) -> float:
    """
    V0.4 crop scoring - deliberately simple per spec:
    crop_score = expected_sale_value - seed_cost - expected_input_cost

    seed_cost is currently a guess (see strategy.py) since BUY_SEED's
    real cost hasn't been observed yet. Do not treat this as ROI - true
    ROI/market modelling arrives in V0.5.
    """
    return sale_price - seed_cost - expected_input_cost


def best_crop(prices: dict, seed_costs: dict, crops: tuple) -> str:
    """Returns the crop with the highest crop_score among available crops."""
    scored = {c: crop_score(prices.get(c, 0), seed_costs.get(c, 0)) for c in crops}
    return max(scored, key=scored.get)