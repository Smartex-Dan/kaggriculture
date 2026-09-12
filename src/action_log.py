"""
Per-action experiment logging.

Logs the action attempted each turn with a snapshot of state just
before it; on the NEXT turn, compares against the new state to
determine the real outcome. This is how "548 HARVEST attempts" turns
into a success rate broken down by crop age instead of a mystery.
"""
import csv
import os
import time

_PATH = os.path.join("experiments", "action_log.csv")
_FIELDS = ["step", "op", "args", "position", "crop", "money_before", "money_after",
           "tile_before", "tile_after", "shed_before_qty", "shed_after_qty", "outcome"]
_RUN_ID = str(int(time.time()))  # set once per process/episode
_FIELDS = ["run_id", "step", "op", "args", "position", "crop", "money_before", "money_after",
           "tile_before", "tile_after", "shed_before_qty", "shed_after_qty", "outcome"]

_pending = None


def start(step: int, op: str, args: tuple, position: tuple, state) -> None:
    """Snapshot the 'before' state right before this action is returned."""
    global _pending
    cell = state.my_tile(*position)
    crop = cell.get("crop") if hasattr(cell, "get") else None
    _pending = {
        "run_id": _RUN_ID,
        "step": step, "op": op, "args": args, "position": position, "crop": crop,
        "money_before": state.my_money,
        "tile_before": dict(cell) if hasattr(cell, "items") else cell,
        "shed_before_qty": state.my_shed.get(crop, 0) if crop else None,
    }


def finalize(state) -> None:
    """Resolve the previous action's real outcome and write one CSV row."""
    global _pending
    if _pending is None:
        return

    x, y = _pending["position"]
    cell_after = state.my_tile(x, y)
    cell_after_dict = dict(cell_after) if hasattr(cell_after, "items") else cell_after
    money_after = state.my_money
    crop = _pending["crop"]
    shed_after_qty = state.my_shed.get(crop, 0) if crop else None

    outcome = _classify(_pending, cell_after_dict, shed_after_qty)

    _write_row({
        "step": _pending["step"], "op": _pending["op"], "args": _pending["args"],
        "position": _pending["position"], "crop": crop,
        "money_before": _pending["money_before"], "money_after": money_after,
        "tile_before": _pending["tile_before"], "tile_after": cell_after_dict,
        "shed_before_qty": _pending["shed_before_qty"], "shed_after_qty": shed_after_qty,
        "outcome": outcome,
    })
    _pending = None


def _classify(pending, tile_after, shed_after_qty) -> str:
    op = pending["op"]
    tile_changed = pending["tile_before"] != tile_after
    if op == "HARVEST":
        before_qty = pending["shed_before_qty"]
        if shed_after_qty is not None and before_qty is not None and shed_after_qty > before_qty:
            return "SUCCESS_SHED_INCREASED"
        return "TILE_CHANGED_NO_SHED_CHANGE" if tile_changed else "NO_EFFECT"
    if op == "PLANT":
        return "PLANTED" if tile_changed else "NO_EFFECT"
    if op == "WATER":
        return "WATERED" if tile_changed else "NO_EFFECT"
    return "OBSERVED"


def _write_row(row: dict) -> None:
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    file_exists = os.path.isfile(_PATH)
    with open(_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def summarize_harvests() -> str:
    if not os.path.isfile(_PATH):
        return "HARVEST EXPERIMENT\nNo action log yet."
    attempts = successes = 0
    by_age_success = {}
    with open(_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["op"] != "HARVEST":
                continue
            attempts += 1
            if row["outcome"] == "SUCCESS_SHED_INCREASED":
                successes += 1
    rate = (successes / attempts * 100) if attempts else 0.0
    return (f"HARVEST EXPERIMENT\nAttempts: {attempts}\nSuccesses: {successes}\n"
            f"Success rate: {rate:.1f}%")