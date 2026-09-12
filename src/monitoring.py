"""
Sentry error monitoring for the Kaggriculture agent.

Call init_sentry() once, as early as possible, before running any
episodes — this is what actually wires error capture in.
"""
import os
import sentry_sdk
from dotenv import load_dotenv

load_dotenv()

SENTRY_DSN = os.environ.get("SENTRY_DSN")


def init_sentry() -> None:
    if not SENTRY_DSN:
        print("SENTRY_DSN not set — skipping Sentry init.")
        return

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=False,
        enable_logs=True,
        traces_sample_rate=1.0,
        profile_session_sample_rate=1.0,
        profile_lifecycle="trace",
    )