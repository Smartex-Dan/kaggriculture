"""Purposeful navigation - step toward a target tile, one move per turn."""
from typing import Optional, Tuple


def direction_toward(current: Tuple[int, int], target: Tuple[int, int]) -> Optional[str]:
    """Single-step direction from current toward target. None if already there."""
    cx, cy = current
    tx, ty = target

    if tx > cx:
        return "EAST"
    if tx < cx:
        return "WEST"
    if ty > cy:
        return "SOUTH"
    if ty < cy:
        return "NORTH"
    return None