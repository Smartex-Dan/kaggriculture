"""
Opponent modeling from public observation data only (money, land,
workers, crops, animals, production/purchasing patterns).
"""


class OpponentModel:
    def update(self, public_obs) -> None:
        raise NotImplementedError

    def inferred_strategy(self) -> str:
        raise NotImplementedError
