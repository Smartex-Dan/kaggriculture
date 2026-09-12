"""Episode telemetry - accumulates counts across one episode."""
import csv
import os
from dataclasses import dataclass, field


@dataclass
class Telemetry:
    starting_money: float = 0.0
    crops_planted: dict = field(default_factory=dict)    # crop -> count
    crops_harvested: int = 0
    sales_events: int = 0
    produce_sold: dict = field(default_factory=dict)     # resource -> qty
    seeds_bought: int = 0
    water_actions: int = 0
    errors: int = 0
    _started: bool = field(default=False, repr=False)

    def start(self, money: float):
        if not self._started:
            self.starting_money = money
            self._started = True

    def record_plant(self, crop: str):
        self.crops_planted[crop] = self.crops_planted.get(crop, 0) + 1

    def record_sale(self, resource: str, qty: float):
        self.sales_events += 1
        self.produce_sold[resource] = self.produce_sold.get(resource, 0) + qty

    def report(self, agent_label: str, opponent_label: str, final_money: float) -> str:
        profit = final_money - self.starting_money
        return (
            f"EPISODE\n{'-' * 40}\n"
            f"Agent: {agent_label}\nOpponent: {opponent_label}\n\n"
            f"Starting money: ${self.starting_money:,.0f}\n"
            f"Final money:    ${final_money:,.0f}\n"
            f"Profit:         ${profit:,.0f}  "
            f"(informational only - NOT a confirmed win condition yet)\n\n"
            f"Crops planted:   {sum(self.crops_planted.values())} {dict(self.crops_planted)}\n"
            f"Crops harvested: {self.crops_harvested}\n"
            f"Sale events:     {self.sales_events}\n"
            f"Produce sold:    {sum(self.produce_sold.values())} {dict(self.produce_sold)}\n"
            f"Seeds bought:    {self.seeds_bought}\n"
            f"Water actions:   {self.water_actions}\n"
            f"Errors:          {self.errors}\n"
        )

    def log_to_csv(self, path: str, version: str, opponent: str, final_money: float):
        """Appends one row per episode. n_games=1 for now - real aggregation
        (100-game runs, actual win_rate) comes once the win condition is confirmed."""
        profit = final_money - self.starting_money
        row = {
            "experiment_id": "", "version": version, "opponent": opponent,
            "n_games": 1, "win_rate": "",  # blank - win condition unconfirmed
            "avg_bank": final_money, "median_bank": final_money,
            "notes": f"profit={profit:.0f} (informational, not win condition)",
        }
        file_exists = os.path.isfile(path)
        with open(path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)


telemetry = Telemetry()