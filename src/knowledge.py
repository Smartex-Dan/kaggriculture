"""
Knowledge layer - tracks what we actually know about Kaggriculture
mechanics, with an explicit confidence level per fact, persisted
across runs so evidence accumulates instead of resetting each episode.

CONFIRMED  - repeatedly demonstrated by experiments (or stated in spec)
PROBABLE   - observed multiple times, not yet exhaustively verified
HYPOTHESIS - our current best guess, seen once or inferred
UNKNOWN    - no reliable evidence yet
"""
import json
import os

CONFIRMED = "CONFIRMED"
PROBABLE = "PROBABLE"
HYPOTHESIS = "HYPOTHESIS"
UNKNOWN = "UNKNOWN"

_PATH = os.path.join("experiments", "knowledge.json")


class Knowledge:
    def __init__(self, path=_PATH):
        self.path = path
        self._facts = {}
        self._load()

    def _load(self):
        if os.path.isfile(self.path):
            try:
                with open(self.path, "r") as f:
                    self._facts = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._facts = {}

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._facts, f, indent=2, sort_keys=True)

    def record(self, key: str, value, confidence: str, note: str = ""):
        """Reinforces a repeated matching value (raising confidence);
        a contradicting value drops back to HYPOTHESIS instead of
        silently overwriting a CONFIRMED fact with a fluke."""
        existing = self._facts.get(key)
        if existing and existing["value"] == value:
            existing["evidence_count"] += 1
            existing["confidence"] = confidence
            if note:
                existing["note"] = note
        elif existing and existing["value"] != value:
            self._facts[key] = {
                "value": value, "confidence": HYPOTHESIS, "evidence_count": 1,
                "note": f"CONTRADICTS prior value {existing['value']!r} - re-verify. {note}",
            }
        else:
            self._facts[key] = {"value": value, "confidence": confidence,
                                 "evidence_count": 1, "note": note}

    def get(self, key: str, default=None):
        fact = self._facts.get(key)
        return fact["value"] if fact else default

    def confidence_of(self, key: str) -> str:
        fact = self._facts.get(key)
        return fact["confidence"] if fact else UNKNOWN

    def report(self) -> str:
        lines = ["KNOWLEDGE BASE", "-" * 40]
        for level in (CONFIRMED, PROBABLE, HYPOTHESIS, UNKNOWN):
            keys = [k for k, v in self._facts.items() if v["confidence"] == level]
            if not keys:
                continue
            lines.append(f"\n{level}:")
            for k in sorted(keys):
                f = self._facts[k]
                lines.append(f"  {k} = {f['value']!r}  (n={f['evidence_count']}) {f.get('note', '')}")
        return "\n".join(lines)


knowledge = Knowledge()

# Seed with what V0.4 already established, so V0.5 starts ahead.
knowledge.record("seed_cost.MELON", 80, CONFIRMED,
                  "confirmed via repeated BUY_SEED money deltas in V0.4")
knowledge.record("weed_rule", "2 consecutive missed waterings converts a crop tile to WEED",
                  CONFIRMED, "V0.4: consecutive_unwatered 0->1->WEED pattern observed 20+ times")
knowledge.record("melon.lifespan_turns", 312, CONFIRMED,
                  "max_lifespan_step = (planted_day+13)*24 in every observed MELON tile")
knowledge.record("harvest.v04_result", "0/548 attempts succeeded", CONFIRMED,
                  "every V0.4 HARVEST call produced zero shed/tile change")

knowledge.record("agent_statelessness", "self.* instance attributes on StrategicPlanner do NOT persist across turns - kaggle_environments exec()'s agent.py fresh each turn. Any cross-turn state must be derived from obs fields (e.g. state.step) or read/written to disk.",
                  CONFIRMED, "discovered via failed harvest-toggle test - 652/652 calls were HARVEST, 0 PASS, despite explicit toggle logic")

knowledge.record("harvest_action_effect", "no observed effect on shed contents",
                  PROBABLE, "cross-episode comparison: old run called HARVEST on 100% of "
                  "day-tick turns (8/8 ticks fired), new run called PASS on 100% of the same "
                  "day-tick turns (8/8 still fired) - switching the action didn't change the outcome")
knowledge.record("yield_production_mechanic", "crops produce 1 yield_units automatically every 24 steps (once/day) once mature, transferred to shed regardless of action taken that turn",
                  PROBABLE, "8/8 shed increases across two episodes landed exactly on step % 24 == 0 boundaries")     

# Explicitly flagged as not yet investigated - deferred per V0.5 rule #8.
for _crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"):
    if knowledge.confidence_of(f"seed_cost.{_crop}") == UNKNOWN:
        knowledge.record(f"seed_cost.{_crop}", None, UNKNOWN, "not yet purchased")
knowledge.record("animal_mechanics", None, UNKNOWN, "deferred - V0.5 priority is crop/harvest mechanics")
knowledge.record("market_price_dynamics", None, UNKNOWN, "deferred - basic price logging comes next pass")
# CORRECTION: the earlier "yield automatic" hypothesis was built on a
# contaminated log (two episodes merged into one action_log.csv). A
# clean single-episode all-PASS test (never calling HARVEST) produced
# ZERO shed increases and both crops decayed to WEED unharvested -
# proving HARVEST is required, not automatic.
knowledge.record("yield_production_mechanic", "REQUIRES a HARVEST call - NOT automatic (correcting prior hypothesis)",
                  CONFIRMED, "clean all-PASS episode: 0/0 HARVEST calls, 0 shed increases, both MELON plants fully decayed to WEED unharvested, profit -$210")
knowledge.record("harvest_timing_hypothesis", "HARVEST likely only succeeds when state.hour == 0 (once per in-game day)",
                  HYPOTHESIS, "every historical HARVEST success landed on a step that is a multiple of 24 (72,120,168,216,240,264,288...) - one in-game day")

knowledge.record("harvest_mechanic", "HARVEST succeeds only at hour==0 with yield_units>0; clears the tile IMMEDIATELY (replantable next turn), but credits the yield to shed only at the START of the NEXT in-game day (24-step delay)",
                  CONFIRMED, "confirmed across two episodes: traced step-by-step shed transfer, and a 25-tile episode produced 10 real harvests + 5 melons sold for real revenue")

knowledge.record("melon_single_tile_cycle_economics", "one farmer running a single MELON tile through repeated plant->water->harvest cycles nets ~$1,270-1,290 profit per ~240-step (10-day) cycle ($1,354-1,371 revenue minus $80 seed cost); 3 full cycles completed in a 720-turn episode for $2,405 total profit vs a -$646 loss when spreading 26 seeds across the whole farm with one farmer",
                  CONFIRMED, "clean episode: 3 PLANT calls (all tile (4,4)), 29 HARVEST calls, 2 sales ($1,354 + $1,371), final money $5,405")
knowledge.record("single_farmer_land_ceiling", "one farmer can reliably sustain roughly 1 actively-cycling crop tile at a time - spreading planting across many tiles causes most to decay to WEED before being reached, net-negative vs concentrating on one tile",
                  PROBABLE, "26-tile spread run: -$646 profit. 1-tile-focus run: +$2,405 profit. Same code, same crop, same seed cost - only the planting-spread pattern differed")

knowledge.record("hire_cost_daily_first", "First HIRE of each day costs exactly $1 - hires_today resets to 0 every day boundary (hour==0), so cost never escalates past the first Fibonacci tier as long as only one hand is hired per day",
                  CONFIRMED, "8 consecutive daily hires (steps 1,25,49,73,97,121,145,169), every single one cost exactly $1")
knowledge.record("hand_lifecycle", "A hired hand vanishes entirely at every day boundary (hands list empties) and a NEW hand spawns at the same fixed position [5,4] if re-hired - hands do NOT persist or retain position/progress across days",
                  CONFIRMED, "hands list observed to empty exactly at every hour==0 tick, then repopulate at [[5,4]] again the following turn after a fresh HIRE call")
knowledge.record("hand_spawn_position", "[5, 4] - possibly on/past the boundary of the unlocked NW quadrant (NW appears to span x=0-4, y=0-4 based on earlier board renders) - unconfirmed whether hand can act there or needs to move into unlocked land first",
                  HYPOTHESIS, "hand spawn coordinate is x=5, one past the last confirmed-unlocked column")