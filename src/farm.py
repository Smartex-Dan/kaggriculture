"""
Crop lifecycle scanning.

CONFIRMED tile schema:
    None                          -> empty tile
    "LOCKED"                      -> unowned quadrant
    {'kind': 'PLANT', 'crop': str, 'planted_day': int,
     'watered_today': bool, 'consecutive_unwatered': int,
     'yield_units': int, 'max_lifespan_step': int,
     'fertilized_until_day': int}  -> a planted crop
    {'kind': 'WEED'}              -> a dead/abandoned crop

CONFIRMED: consecutive_unwatered >= 1 means the NEXT missed watering
converts the tile to WEED (2 consecutive missed waterings kills it).

Tile values with kind='PLANT'/'WEED' come back as dict-like Struct
objects, NOT hashable - never put a raw tile value in a set/dict key.
"""

EMPTY = "EMPTY"
LOCKED = "LOCKED"
CROP = "CROP"
WEED = "WEED"
OTHER = "OTHER"

_seen_kinds = set()


def classify_tile(raw_value) -> str:
    if raw_value is None:
        return EMPTY
    if raw_value == "LOCKED":
        return LOCKED
    kind = raw_value.get("kind") if hasattr(raw_value, "get") else None
    if kind == "PLANT":
        return CROP
    if kind == "WEED":
        return WEED
    if kind not in _seen_kinds:
        _seen_kinds.add(kind)
        print(f"[farm] New tile kind observed: {kind!r}")
    return OTHER


def find_empty_tiles(farm: dict) -> list:
    return [(x, y) for y, row in enumerate(farm["tiles"])
            for x, cell in enumerate(row) if classify_tile(cell) == EMPTY]


def find_crop_tiles(farm: dict) -> list:
    """[(x, y, crop_info), ...] for every planted (non-weed) tile."""
    return [(x, y, cell) for y, row in enumerate(farm["tiles"])
            for x, cell in enumerate(row) if classify_tile(cell) == CROP]


def find_thirsty_crop_tiles(farm: dict) -> list:
    """Crop tiles not watered today - about to start the 2-day
    countdown to becoming WEED."""
    return [(x, y, cell) for x, y, cell in find_crop_tiles(farm)
            if not cell.get("watered_today", True)]


def needs_water(crop_info) -> bool:
    return not crop_info.get("watered_today", True)


def weed_risk(crop_info) -> bool:
    """CONFIRMED: consecutive_unwatered >= 1 means the next missed
    day converts this tile to WEED."""
    return crop_info.get("consecutive_unwatered", 0) >= 1

def find_harvestable_crop_tiles(farm: dict) -> list:
    """Mature crop tiles ready for HARVEST right now (yield_units > 0)."""
    return [(x, y, cell) for x, y, cell in find_crop_tiles(farm)
            if cell.get("yield_units", 0) > 0]