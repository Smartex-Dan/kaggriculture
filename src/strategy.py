"""StrategicPlanner - V0.5: adds seed-cost discovery rotation across
all 5 crops (not just MELON), reads costs from the knowledge base."""

from typing import Optional
from src.actions import CROPS
from src.farm import find_empty_tiles, find_thirsty_crop_tiles, find_harvestable_crop_tiles, classify_tile, CROP
from src.inventory import sellable_produce, has_seeds, can_afford
from src.navigation import direction_toward
from src.telemetry import telemetry
from src.diagnostics import diff_and_log
from src.knowledge import knowledge, CONFIRMED
from src.market_log import log_market

_FALLBACK_SEED_COST = {"MELON": 80, "WHEAT": 10, "CARROT": 10, "TOMATO": 10, "STRAWBERRY": 10}


def _seed_cost(crop: str) -> float:
    return knowledge.get(f"seed_cost.{crop}") or _FALLBACK_SEED_COST.get(crop, 10)


def _crop_needing_cost_discovery(state) -> Optional[str]:
    for c in CROPS:
        if knowledge.confidence_of(f"seed_cost.{c}") != CONFIRMED and state.my_money >= _FALLBACK_SEED_COST.get(c, 10):
            return c
    return None


class StrategicPlanner:
    def decide(self, state) -> dict:
        telemetry.start(state.my_money)
        diff_and_log(state)
        farm = state.my_farm
        log_market(state)
        pos = tuple(state.my_position)

        # Harvest check FIRST, before thirst.
        harvestable = []
        if state.hour == 0:
            harvestable = find_harvestable_crop_tiles(farm)

        if harvestable:
            hx, hy, _c = min(
                harvestable,
                key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]),
            )
            if pos == (hx, hy):
                telemetry.crops_harvested += 1
                return self._farmer_action("HARVEST")
            d = direction_toward(pos, (hx, hy))
            if d:
                return self._farmer_action(d)

        thirsty = find_thirsty_crop_tiles(farm)
        if thirsty:
            tx, ty, _c = min(thirsty, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))
            if pos == (tx, ty):
                telemetry.water_actions += 1
                return self._farmer_action("WATER")
            d = direction_toward(pos, (tx, ty))
            if d:
                return self._farmer_action(d)

        sellable = sellable_produce(state.my_shed)
        if sellable:
            resource = max(sellable, key=lambda r: state.prices.get(r, 0))
            qty = sellable[resource]
            telemetry.record_sale(resource, qty)
            return self._farmer_action("PASS", market=[["SELL", resource, qty]])

        empty_tiles = find_empty_tiles(farm)
        plantable_crops = [c for c in CROPS if has_seeds(state.my_seeds, c)]

        if empty_tiles and plantable_crops:
            crop = max(plantable_crops, key=lambda c: state.prices.get(c, 0))
            target = min(empty_tiles, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))
            if pos == target:
                telemetry.record_plant(crop)
                return self._farmer_action("PLANT", crop)
            d = direction_toward(pos, target)
            if d:
                return self._farmer_action(d)

        if empty_tiles and not plantable_crops:
            crop = _crop_needing_cost_discovery(state) or self._best_buyable_crop(state)
            if crop and can_afford(state.my_money, _seed_cost(crop)):
                telemetry.seeds_bought += 1
                return self._farmer_action("PASS", market=[["BUY_SEED", crop, 1]])

        center = (4, 4)
        if pos != center:
            d = direction_toward(pos, center)
            if d:
                return self._farmer_action(d)

        return self._farmer_action("PASS")

    def _best_buyable_crop(self, state) -> str:
        from src.economy import best_crop
        costs = {c: _seed_cost(c) for c in CROPS}
        return best_crop(state.prices, costs, CROPS)

    def _farmer_action(self, op: str, *args, market: Optional[list] = None) -> dict:
        return {"farmer": [op, *args], "hands": [], "market": market or []}

