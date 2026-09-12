"""Canonical action operations for Kaggriculture, per the official spec."""

MOVEMENT = ("NORTH", "SOUTH", "EAST", "WEST", "PASS")
CROP_OPS = ("PLANT", "WATER", "HARVEST", "FERTILIZE")
ANIMAL_OPS = ("BUILD_COOP", "BUILD_PASTURE", "FEED", "CARE", "COLLECT_FERTILIZER")
TERRAIN_OPS = ("DIG", "PICKUP", "DROP", "PLACE")
MARKET_OPS = ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL", "HIRE", "BUY_LAND")
MARKET_RESOURCES = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                     "EGG", "MILK", "WOOL", "FERTILIZER")

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")

LAND_COSTS = {"NE": 1000, "SW": 2000, "SE": 4000}


def empty_action() -> dict:
    """Skeleton matching the official action dict shape."""
    return {"farmer": ["PASS"], "hands": [], "market": []}