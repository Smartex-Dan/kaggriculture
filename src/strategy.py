"""StrategicPlanner - V0.5: adds seed-cost discovery rotation across
all 5 crops (not just MELON), reads costs from the knowledge base."""

from typing import Optional
from src.actions import CROPS
from src.farm import find_empty_tiles, find_thirsty_crop_tiles, find_harvestable_crop_tiles
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

        market_orders = []
        if not state.my_farm.get("hands") and state.my_farm.get("hires_today", 0) == 0:
            market_orders.append(["HIRE"])

        n_hands = len(state.my_farm.get("hands", []))
        pos = tuple(state.my_position)

        # --- HAND LOGIC ---
        # A hand only lives ~23 turns/day, nowhere near enough for a full
        # crop cycle - so its job is to PLANT a second tile that the
        # farmer's own (already farm-wide) water/harvest scan will pick up
        # and service on later days, once the hand is long gone.
        hand_action = ["PASS"]
        hand_planted = False
        hand_target = None
        if n_hands > 0:
            hand_pos = tuple(farm["hands"][0])
            empty_tiles_for_hand = find_empty_tiles(farm)
            if empty_tiles_for_hand and has_seeds(state.my_seeds, "MELON"):
                hand_target = min(
                    empty_tiles_for_hand,
                    key=lambda t: abs(t[0] - hand_pos[0]) + abs(t[1] - hand_pos[1]),
                )
                if hand_pos == hand_target:
                    hand_action = ["PLANT", "MELON"]
                    hand_planted = True
                    telemetry.record_plant("MELON")
                else:
                    d = direction_toward(hand_pos, hand_target)
                    if d:
                        hand_action = [d]
        hand_actions = [hand_action] * n_hands if n_hands else None

        # --- FARMER LOGIC ---
        harvestable = find_harvestable_crop_tiles(farm)
        if harvestable:
            hx, hy, _c = min(harvestable, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))
            if pos == (hx, hy):
                telemetry.crops_harvested += 1
                return self._farmer_action("HARVEST", market=market_orders, hand_actions=hand_actions)
            d = direction_toward(pos, (hx, hy))
            if d:
                return self._farmer_action(d, market=market_orders, hand_actions=hand_actions)

        thirsty = find_thirsty_crop_tiles(farm)
        if thirsty:
            tx, ty, _c = min(thirsty, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))
            if pos == (tx, ty):
                telemetry.water_actions += 1
                return self._farmer_action("WATER", market=market_orders, hand_actions=hand_actions)
            d = direction_toward(pos, (tx, ty))
            if d:
                return self._farmer_action(d, market=market_orders, hand_actions=hand_actions)

        sellable = sellable_produce(state.my_shed)
        if sellable:
            resource = max(sellable, key=lambda r: state.prices.get(r, 0))
            qty = sellable[resource]
            telemetry.record_sale(resource, qty)
            market_orders.append(["SELL", resource, qty])
            return self._farmer_action("PASS", market=market_orders, hand_actions=hand_actions)

        # Calculate seeds available for the farmer (accounting for hand's reservation)
        farmer_seeds = dict(state.my_seeds)
        if hand_planted and farmer_seeds.get("MELON", 0) > 0:
            farmer_seeds["MELON"] -= 1

        all_empty_tiles = find_empty_tiles(farm)
        # Avoid targeting the exact tile the hand is currently targeting if others are available
        empty_tiles = [t for t in all_empty_tiles if t != hand_target] if (hand_target and len(all_empty_tiles) > 1) else all_empty_tiles
        plantable_crops = [c for c in CROPS if has_seeds(farmer_seeds, c)]

        if empty_tiles and plantable_crops:
            crop = max(plantable_crops, key=lambda c: state.prices.get(c, 0))
            target = min(empty_tiles, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))
            if pos == target:
                telemetry.record_plant(crop)
                return self._farmer_action("PLANT", crop, market=market_orders, hand_actions=hand_actions)
            d = direction_toward(pos, target)
            if d:
                return self._farmer_action(d, market=market_orders, hand_actions=hand_actions)

        if empty_tiles and not plantable_crops:
            crop = _crop_needing_cost_discovery(state) or self._best_buyable_crop(state)
            if crop and can_afford(state.my_money, _seed_cost(crop)):
                # Buy 2 when a hand exists, so there's enough shared seed
                # stock for both the farmer's own plant AND the hand's.
                qty = 2 if n_hands > 0 else 1
                telemetry.seeds_bought += 1
                market_orders.append(["BUY_SEED", crop, qty])
                return self._farmer_action("PASS", market=market_orders, hand_actions=hand_actions)

        center = (4, 4)
        if pos != center:
            d = direction_toward(pos, center)
            if d:
                return self._farmer_action(d, market=market_orders, hand_actions=hand_actions)

        return self._farmer_action("PASS", market=market_orders, hand_actions=hand_actions)

    def _best_buyable_crop(self, state) -> str:
        from src.economy import best_crop
        costs = {c: _seed_cost(c) for c in CROPS}
        return best_crop(state.prices, costs, CROPS)

    def _farmer_action(self, op: str, *args, market: Optional[list] = None, hand_actions: Optional[list] = None) -> dict:
        return {"farmer": [op, *args], "hands": hand_actions or [], "market": market or []}