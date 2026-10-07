"""StrategicPlanner - V0.6: multi-hand hiring to run several parallel
MELON cycles at once. Official Object Types table confirms MELON's
profit/tile/day (~$129.5) dominates every other crop (~6x the next
best), so we commit hard to MELON rather than rotating crops."""

from typing import Optional
from src.actions import CROPS
from src.farm import find_empty_tiles, find_thirsty_crop_tiles, find_harvestable_crop_tiles
from src.inventory import sellable_produce, has_seeds, can_afford
from src.navigation import direction_toward
from src.telemetry import telemetry
from src.diagnostics import diff_and_log
from src.knowledge import knowledge, CONFIRMED
from src.market_log import log_market

_FIRST_YIELD_DAY = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
_FALLBACK_SEED_COST = {"MELON": 80, "WHEAT": 10, "CARROT": 10, "TOMATO": 10, "STRAWBERRY": 10}

# Cheap to raise (Fibonacci hire cost resets daily: 1,1,2,3,5...) - start
# at 3 and watch whether the farmer can actually keep 4 tiles (1 own +
# 3 hands) watered daily before pushing higher.
N_HANDS_TARGET = 1


def _seed_cost(crop: str) -> float:
    return knowledge.get(f"seed_cost.{crop}") or _FALLBACK_SEED_COST.get(crop, 10)


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class StrategicPlanner:
    def decide(self, state) -> dict:
        telemetry.start(state.my_money)
        diff_and_log(state)
        farm = state.my_farm
        log_market(state)
        pos = tuple(state.my_position)
        hands = farm.get("hands", [])
        n_hands = len(hands)
        hires_today = farm.get("hires_today", 0)

        market_orders = []

        # --- SELL: independent of farmer's physical action ---
        sellable = sellable_produce(state.my_shed)
        for resource, qty in sellable.items():
            telemetry.record_sale(resource, qty)
            market_orders.append(["SELL", resource, qty])

        # --- HIRE: up to N_HANDS_TARGET per day, nearly free (fib resets daily) ---
        if n_hands < N_HANDS_TARGET and hires_today < N_HANDS_TARGET:
            market_orders.append(["HIRE"])

        empty_tiles = find_empty_tiles(farm)
        plantable_crops = [c for c in CROPS if has_seeds(state.my_seeds, c)]

        # --- BUY_SEED: cover farmer + every hand that might plant this turn.
        # Per spec: if 2+ units PLANT the same turn with insufficient stock,
        # NONE succeed - so under-buying isn't just wasteful, it's a total
        # planting failure for everyone that turn.
        if empty_tiles and not plantable_crops:
            crop = "MELON"
            cost = _seed_cost(crop)
            slots_needed = 1 + n_hands
            for i in range(slots_needed):
                if can_afford(state.my_money, cost * (i + 1)):
                    telemetry.seeds_bought += 1
                    market_orders.append(["BUY_SEED", crop, 1])

        # --- HANDS: each claims a distinct empty tile to plant MELON,
        # avoiding both target collisions and the same-turn insufficient-
        # seed failure mode. ---
        claimed = set()
        hand_actions = []
        if n_hands > 0:
            available_seeds = state.my_seeds.get("MELON", 0)
            for hpos in hands:
                hpos = tuple(hpos)
                avail = [t for t in empty_tiles if t not in claimed]
                if avail and available_seeds > 0:
                    h_target = min(avail, key=lambda t: _dist(t, hpos))
                    if hpos == h_target:
                        hand_actions.append(["PLANT", "MELON"])
                        telemetry.record_plant("MELON")
                        available_seeds -= 1
                        claimed.add(h_target)
                    else:
                        d = direction_toward(hpos, h_target)
                        hand_actions.append([d] if d else ["PASS"])
                        claimed.add(h_target)
                else:
                    hand_actions.append(["PASS"])

        # --- FARMER: physical action priority ---
        harvestable = [
            (x, y, crop_info)
            for x, y, crop_info in find_harvestable_crop_tiles(farm)
            if state.day - crop_info.get("planted_day", state.day) >=
            _FIRST_YIELD_DAY.get(crop_info.get("crop"), 999)
        ]
        if harvestable:
            hx, hy, _c = min(harvestable, key=lambda t: _dist((t[0], t[1]), pos))
            if pos == (hx, hy):
                telemetry.crops_harvested += 1
                return self._farmer_action("HARVEST", market=market_orders, hand_actions=hand_actions)
            d = direction_toward(pos, (hx, hy))
            if d:
                return self._farmer_action(d, market=market_orders, hand_actions=hand_actions)

        thirsty = find_thirsty_crop_tiles(farm)
        if thirsty:
            tx, ty, _c = min(thirsty, key=lambda t: _dist((t[0], t[1]), pos))
            if pos == (tx, ty):
                telemetry.water_actions += 1
                return self._farmer_action("WATER", market=market_orders, hand_actions=hand_actions)
            d = direction_toward(pos, (tx, ty))
            if d:
                return self._farmer_action(d, market=market_orders, hand_actions=hand_actions)

        if empty_tiles and plantable_crops:
            farmer_avail = [t for t in empty_tiles if t not in claimed]
            if farmer_avail:
                crop = max(plantable_crops, key=lambda c: state.prices.get(c, 0))
                target = min(farmer_avail, key=lambda t: _dist(t, pos))
                if pos == target:
                    telemetry.record_plant(crop)
                    return self._farmer_action("PLANT", crop, market=market_orders, hand_actions=hand_actions)
                d = direction_toward(pos, target)
                if d:
                    return self._farmer_action(d, market=market_orders, hand_actions=hand_actions)

        center = (4, 4)
        if pos != center:
            d = direction_toward(pos, center)
            if d:
                return self._farmer_action(d, market=market_orders, hand_actions=hand_actions)

        return self._farmer_action("PASS", market=market_orders, hand_actions=hand_actions)

    def _farmer_action(self, op: str, *args, market: Optional[list] = None, hand_actions: Optional[list] = None) -> dict:
        return {"farmer": [op, *args], "hands": hand_actions or [], "market": market or []}