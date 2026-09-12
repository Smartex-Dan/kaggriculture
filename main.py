import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sentry_sdk
from kaggle_environments import make
from src.monitoring import init_sentry
from src.telemetry import telemetry
from src import action_log
from src.knowledge import knowledge


def main():
    init_sentry()

    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
        result = env.run(["src/agent.py", "random"])
    except Exception:
        sentry_sdk.capture_exception()
        raise

    last_step = result[-1]
    for i, agent_result in enumerate(last_step):
        print(f"Agent {i} status: {agent_result['status']}")

    final_money = last_step[0]["observation"]["farms"][0]["money"]
    print(telemetry.report("V0.4", "random", final_money))
    telemetry.log_to_csv("experiments/log.csv", "V0.4-alpha", "random", final_money)
    print(action_log.summarize_harvests())
    print(knowledge.report())
    knowledge.save()

    try:
        print(env.render(mode="ansi"))
    except Exception as e:
        print("ansi render not supported:", e)


if __name__ == "__main__":
    main()