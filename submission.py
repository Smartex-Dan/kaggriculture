"""
Kaggriculture competition submission agent.
Self-contained - no local package imports, safe for Kaggle's exec-based
agent loading. Built from confirmed mechanics only.
"""

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
FIRST_YIELD_DAY = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}


def _classify(cell):
    if cell is None:
        return "EMPTY"
    if cell == "LOCKED":
        return "LOCKED"
    kind = cell.get("kind") if hasattr(cell, "get") else None
    if kind == "PLANT":
        return "CROP"
    if kind == "WEED":
        return "WEED"
    return "OTHER"


def _direction_toward(cur, target):
    cx, cy = cur
    tx, ty = target
    if tx > cx: return "EAST"
    if tx < cx: return "WEST"
    if ty > cy: return "SOUTH"
    if ty < cy: return "NORTH"
    return None


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    tiles = me["tiles"]
    pos = tuple(me["farmer"])
    day = obs["day"]
    money = me["money"]
    seeds = private["seeds"]
    shed = private["shed"]
    prices = obs["market"]["prices"]
    hands = me.get("hands", [])
    hires_today = me.get("hires_today", 0)
    n_hands = len(hands)

    market_orders = []

    for item, qty in shed.items():
        if qty > 0 and item in prices:
            market_orders.append(["SELL", item, qty])

    if n_hands == 0 and hires_today == 0:
        market_orders.append(["HIRE"])

    empty_tiles = []
    crop_tiles = []
    for y, row in enumerate(tiles):
        for x, cell in enumerate(row):
            c = _classify(cell)
            if c == "EMPTY":
                empty_tiles.append((x, y))
            elif c == "CROP":
                crop_tiles.append((x, y, cell))

    plantable_crops = [c for c in CROPS if seeds.get(c, 0) > 0]

    if empty_tiles and not plantable_crops:
        crop = max(CROPS, key=lambda c: prices.get(c, 0) - SEED_COST[c])
        cost = SEED_COST[crop]
        if money >= cost:
            market_orders.append(["BUY_SEED", crop, 1])
            if n_hands > 0 and money >= cost * 2:
                market_orders.append(["BUY_SEED", crop, 1])

    hand_actions = None
    if n_hands > 0:
        hand_pos = tuple(hands[0])
        hand_op = ["PASS"]
        if empty_tiles and seeds.get("MELON", 0) > 0:
            h_target = min(empty_tiles, key=lambda t: _dist(t, hand_pos))
            if hand_pos == h_target:
                hand_op = ["PLANT", "MELON"]
            else:
                d = _direction_toward(hand_pos, h_target)
                if d:
                    hand_op = [d]
        hand_actions = [hand_op] * n_hands

    def result(op, *args):
        return {"farmer": [op, *args], "hands": hand_actions or [], "market": market_orders[:10]}

    harvestable = [(x, y, c) for x, y, c in crop_tiles
                   if day - c["planted_day"] >= FIRST_YIELD_DAY.get(c["crop"], 999)]
    if harvestable:
        hx, hy, _c = min(harvestable, key=lambda t: _dist((t[0], t[1]), pos))
        if pos == (hx, hy):
            return result("HARVEST")
        d = _direction_toward(pos, (hx, hy))
        if d:
            return result(d)

    thirsty = [(x, y, c) for x, y, c in crop_tiles if not c.get("watered_today", True)]
    if thirsty:
        tx, ty, _c = min(thirsty, key=lambda t: _dist((t[0], t[1]), pos))
        if pos == (tx, ty):
            return result("WATER")
        d = _direction_toward(pos, (tx, ty))
        if d:
            return result(d)

    if empty_tiles and plantable_crops:
        crop = max(plantable_crops, key=lambda c: prices.get(c, 0))
        target = min(empty_tiles, key=lambda t: _dist(t, pos))
        if pos == target:
            return result("PLANT", crop)
        d = _direction_toward(pos, target)
        if d:
            return result(d)

    center = (4, 4)
    if pos != center:
        d = _direction_toward(pos, center)
        if d:
            return result(d)

    return result("PASS")