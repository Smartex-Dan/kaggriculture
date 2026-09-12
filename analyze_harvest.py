"""
One-off analysis: does HARVEST actually cause yield, or does the
crop produce on its own timer regardless of what action we send?

Filters action_log.csv down to only the harvest-toggle rows (PASS or
HARVEST while standing on a crop tile) and reports whether shed
quantity ever increased on a skipped (PASS) turn.
"""
import csv

with open("experiments/action_log.csv", newline="") as f:
    rows = list(csv.DictReader(f))

# Only rows relevant to the toggle test: op is HARVEST or PASS, AND
# the farmer was standing on an actual crop (crop column non-empty).
toggle_rows = [r for r in rows if r["op"] in ("HARVEST", "PASS") and r["crop"]]

def shed_changed(r):
    try:
        before = float(r["shed_before_qty"])
        after = float(r["shed_after_qty"])
        return after > before
    except (ValueError, TypeError):
        return False

harvest_rows = [r for r in toggle_rows if r["op"] == "HARVEST"]
pass_rows = [r for r in toggle_rows if r["op"] == "PASS"]

harvest_hits = [r for r in harvest_rows if shed_changed(r)]
pass_hits = [r for r in pass_rows if shed_changed(r)]

print(f"Total toggle-test rows: {len(toggle_rows)}")
print(f"HARVEST attempts: {len(harvest_rows)}, shed increased on: {len(harvest_hits)}")
print(f"PASS (skipped) attempts: {len(pass_rows)}, shed increased on: {len(pass_hits)}")
print()

if pass_hits:
    print("YIELD HAPPENED WITHOUT CALLING HARVEST - it's automatic, not action-gated:")
    for r in pass_hits[:10]:
        print(f"  step={r['step']} crop={r['crop']} shed {r['shed_before_qty']} -> {r['shed_after_qty']}")
else:
    print("No shed increase ever occurred on a skipped (PASS) turn.")
    print("-> Consistent with HARVEST genuinely being required to produce yield.")

                                                                  
