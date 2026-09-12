# """
# V0.4 - Deterministic farming agent.

# Purpose: replace random movement with a purposeful priority-based
# loop (see strategy.py for the priority order).
# """
# import sys
# import os
# import sentry_sdk

# try:
#     _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# except NameError:
#     _project_root = os.getcwd()

# if _project_root not in sys.path:
#     sys.path.insert(0, _project_root)

# from src.state import parse_observation
# from src.strategy import StrategicPlanner

# _planner = StrategicPlanner()


# def agent(obs):
#     try:
#         state = parse_observation(obs)
#         return _planner.decide(state)
#     except Exception:
#         sentry_sdk.capture_exception()
#         raise

"""V0.5 - Mechanics & Economic Discovery agent."""
import sys
import os
import sentry_sdk

try:
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    _project_root = os.getcwd()

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.state import parse_observation
from src.strategy import StrategicPlanner
from src import action_log

_planner = StrategicPlanner()


def agent(obs):
    try:
        state = parse_observation(obs)
        action_log.finalize(state)  # resolve last turn's logged action first
        action = _planner.decide(state)
        op = action["farmer"][0]
        args = tuple(action["farmer"][1:])
        action_log.start(state.step, op, args, tuple(state.my_position), state)
        return action
    except Exception:
        sentry_sdk.capture_exception()
        raise