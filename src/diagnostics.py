"""
Turn-by-turn state diff logger + automatic knowledge extraction.

Compares each new observation against the previous turn's values for
OUR farm, prints changes, and feeds seed-cost correlations straight
into the knowledge base instead of us reading logs and updating
constants by hand.
"""
from src.knowledge import knowledge, PROBABLE, CONFIRMED
from typing import Any, Dict

_previous: Dict[str, Any] = {"tiles": None, "shed": None, "seeds": None, "money": None}


def diff_and_log(state) -> None:
    farm = state.my_farm
    tiles = farm["tiles"]
    shed = state.my_shed
    seeds = state.my_seeds
    money = state.my_money
    money_delta = money - _previous["money"] if _previous["money"] is not None else None

    if _previous["tiles"] is not None:
        for y, row in enumerate(tiles):
            for x, cell in enumerate(row):
                old = _previous["tiles"][y][x]
                if old != cell:
                    print(f"[diag] tile ({x},{y}) changed: {old!r} -> {cell!r}  (step={state.step})")

    if _previous["seeds"] is not None:
        for k, v in seeds.items():
            old = _previous["seeds"].get(k)
            if old is not None and v > old and money_delta is not None and money_delta < 0:
                cost = -money_delta / (v - old)
                conf = CONFIRMED if knowledge.confidence_of(f"seed_cost.{k}") in (PROBABLE, CONFIRMED) else PROBABLE
                knowledge.record(f"seed_cost.{k}", cost, conf, "derived from seed-count/money delta")
                print(f"[diag] seeds[{k}] changed: {old} -> {v}  (step={state.step})  inferred seed_cost={cost}")
            elif old != v:
                print(f"[diag] seeds[{k}] changed: {old} -> {v}  (step={state.step})")

    if _previous["shed"] is not None:
        for k, v in shed.items():
            old = _previous["shed"].get(k)
            if old != v:
                print(f"[diag] shed[{k}] changed: {old} -> {v}  (step={state.step})")

    if money_delta:
        print(f"[diag] money changed: {_previous['money']} -> {money}  (step={state.step})")

    _previous["tiles"] = [row[:] for row in tiles]
    _previous["shed"] = dict(shed)
    _previous["seeds"] = dict(seeds)
    _previous["money"] = money