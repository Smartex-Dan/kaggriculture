"""
Observation parsing / state representation.

Matches the confirmed Kaggriculture obs schema (verified against a
real obs dump on 2026-08-11):

{
    "remainingOverageTime": int,
    "step": int,
    "player": int,               # index into "farms" that is "us"
    "farms": [
        {
            "money": float,
            "tiles": [[None | "LOCKED" | ..., ...] x10] x10,
            "farmer": [x, y],
            "hands": [...],
            "unlocked_quadrants": ["NW", ...],
            "hires_today": int,
        },
        ...  # one entry per player - both are PUBLIC
    ],
    "private": {                 # only OUR data - opponent's is hidden
        "shed": {resource: qty, ...},
        "seeds": {crop: qty, ...},
        "inventories": [{...}],  # per farm-hand inventory
    },
    "market": {
        "inventory": {resource: qty, ...},
        "prices": {resource: price, ...},
    },
    "town": {"unlocked_shops": [shop_name, ...]},
    "day": int,
    "hour": int,
}
"""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GameState:
    step: int
    player: int
    farms: list
    private: dict
    market: dict
    town: dict
    day: int
    hour: int
    raw: Any = field(repr=False, default=None)

    @property
    def turns_remaining(self) -> int:
        return 720 - self.step

    @property
    def my_farm(self) -> dict:
        return self.farms[self.player]

    @property
    def opponent_farm(self) -> dict:
        # Public fields only - opponent's shed/seeds are never here.
        other = 1 - self.player
        return self.farms[other]

    @property
    def my_money(self) -> float:
        return self.my_farm["money"]

    @property
    def my_position(self) -> list:
        return self.my_farm["farmer"]

    @property
    def my_shed(self) -> dict:
        return self.private["shed"]

    @property
    def my_seeds(self) -> dict:
        return self.private["seeds"]

    @property
    def prices(self) -> dict:
        return self.market["prices"]

    @property
    def market_inventory(self) -> dict:
        return self.market["inventory"]

    def tile_at(self, farm_index: int, x: int, y: int) -> Optional[str]:
        """None = empty/unplanted, 'LOCKED' = unowned quadrant, or a crop/tile state string."""
        return self.farms[farm_index]["tiles"][y][x]

    def my_tile(self, x: int, y: int) -> Optional[str]:
        return self.tile_at(self.player, x, y)


def parse_observation(obs: Any) -> GameState:
    return GameState(
        step=obs["step"],
        player=obs["player"],
        farms=obs["farms"],
        private=obs["private"],
        market=obs["market"],
        town=obs["town"],
        day=obs["day"],
        hour=obs["hour"],
        raw=obs,
    )