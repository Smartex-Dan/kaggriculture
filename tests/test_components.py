import pytest
from src.state import parse_observation, GameState
from src.actions import empty_action, CROPS, MOVEMENT, CROP_OPS, MARKET_OPS
from src.navigation import direction_toward
from src.farm import (
    classify_tile, find_empty_tiles, find_crop_tiles,
    find_thirsty_crop_tiles, find_harvestable_crop_tiles,
    EMPTY, LOCKED, CROP, WEED, OTHER
)
from src.inventory import sellable_produce, has_seeds, can_afford
from src.economy import expected_profit, crop_score, best_crop
from src.telemetry import Telemetry
from src.knowledge import Knowledge, CONFIRMED, PROBABLE, HYPOTHESIS, UNKNOWN
from src.strategy import StrategicPlanner
from src import action_log
import src.diagnostics as diagnostics
from src.monitoring import init_sentry


def make_dummy_obs():
    tiles = [[None for _ in range(10)] for _ in range(10)]
    tiles[0][0] = "LOCKED"
    tiles[1][1] = {"kind": "PLANT", "crop": "MELON", "yield_units": 1, "watered_today": False, "consecutive_unwatered": 1}
    tiles[1][2] = {"kind": "WEED"}
    return {
        "remainingOverageTime": 100,
        "step": 24,
        "player": 0,
        "farms": [
            {
                "money": 500.0,
                "tiles": tiles,
                "farmer": [1, 1],
                "hands": [[5, 4]],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            {
                "money": 300.0,
                "tiles": [[None]*10 for _ in range(10)],
                "farmer": [4, 4],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            }
        ],
        "private": {
            "shed": {"MELON": 2, "WHEAT": 0},
            "seeds": {"MELON": 1, "WHEAT": 0},
            "inventories": [{}],
        },
        "market": {
            "inventory": {"MELON": 10, "WHEAT": 20},
            "prices": {"MELON": 100.0, "WHEAT": 15.0},
        },
        "town": {"unlocked_shops": []},
        "day": 1,
        "hour": 0,
    }


def test_state_parsing():
    obs = make_dummy_obs()
    state = parse_observation(obs)
    assert state.step == 24
    assert state.player == 0
    assert state.my_money == 500.0
    assert state.opponent_farm["money"] == 300.0
    assert state.my_position == [1, 1]
    assert state.my_shed == {"MELON": 2, "WHEAT": 0}
    assert state.my_seeds == {"MELON": 1, "WHEAT": 0}
    assert state.prices["MELON"] == 100.0
    assert state.turns_remaining == 696
    assert state.my_tile(0, 0) == "LOCKED"
    assert state.my_tile(1, 1)["kind"] == "PLANT"


def test_farm_classification():
    assert classify_tile(None) == EMPTY
    assert classify_tile("LOCKED") == LOCKED
    assert classify_tile({"kind": "PLANT"}) == CROP
    assert classify_tile({"kind": "WEED"}) == WEED
    assert classify_tile({"kind": "UNKNOWN_KIND"}) == OTHER


def test_navigation():
    assert direction_toward((0, 0), (2, 0)) == "EAST"
    assert direction_toward((2, 0), (0, 0)) == "WEST"
    assert direction_toward((0, 0), (0, 2)) == "SOUTH"
    assert direction_toward((0, 2), (0, 0)) == "NORTH"
    assert direction_toward((1, 1), (1, 1)) is None


def test_inventory_and_economy():
    assert sellable_produce({"MELON": 2, "WHEAT": 0}) == {"MELON": 2}
    assert has_seeds({"MELON": 1}, "MELON") is True
    assert has_seeds({"MELON": 0}, "MELON") is False
    assert can_afford(100, 50) is True
    assert can_afford(40, 50) is False

    assert expected_profit(100, 20, 10, 5) == 65
    assert crop_score(100, 30) == 70
    assert best_crop({"MELON": 100, "WHEAT": 20}, {"MELON": 80, "WHEAT": 10}, ("MELON", "WHEAT")) == "MELON"


def test_action_log_and_strategy(tmp_path):
    obs = make_dummy_obs()
    state = parse_observation(obs)
    planner = StrategicPlanner()
    action = planner.decide(state)
    assert "farmer" in action
    assert "hands" in action
    assert "market" in action


def test_init_sentry():
    # Test if init_sentry runs without raising an error
    init_sentry()

