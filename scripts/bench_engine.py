#!/usr/bin/env python3
"""Times the engine on synthetic data — no Home Assistant, no real statistics needed.

Every millisecond measured here happens inside a service call, so it is time a user waits.
Written after ``value_at`` turned out to rebuild its search keys on every call, which made
``derive_series`` quadratic: ~9.8 s for 21 600 points (2.5 years hourly) instead of ~80 ms.

Usage:
    python3 scripts/bench_engine.py [--points 21600]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "custom_components" / "statistics_toolset"))

from engine import (  # noqa: E402  - path set above
    aggregate_periods,
    build_reference,
    derive_series,
    estimate_max_rate,
    find_outliers,
    plausibility_check,
)

HOUR = 3600.0
TIMEZONE = "Europe/Berlin"  # any DST-observing zone exercises the reset rules


def timed(label: str, function):
    started = time.perf_counter()
    result = function()
    elapsed = time.perf_counter() - started
    print(f"  {label:24s} {elapsed * 1000:8.1f} ms")
    return result, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=21_600,
                        help="hourly data points to simulate (default 21600 = 2.5 years)")
    args = parser.parse_args()

    start = 1_707_570_000.0
    raw = [(start + i * HOUR, i * 1.0) for i in range(args.points)]
    print(f"{args.points} hourly points\n")

    budget = 0.0
    rate, elapsed = timed("estimate_max_rate", lambda: estimate_max_rate(raw))
    budget += elapsed
    reference, elapsed = timed("build_reference", lambda: build_reference(raw, rate, 0.8))
    budget += elapsed
    _, elapsed = timed("find_outliers", lambda: find_outliers(raw, rate))
    budget += elapsed

    rows = None
    for cycle in ("quarter-hourly", "hourly", "daily", "weekly", "monthly", "yearly", "none"):
        result, elapsed = timed(
            f"derive_series {cycle}",
            lambda c=cycle: derive_series(reference, c, TIMEZONE, raw[0][0], raw[-1][0], raw[0][0]),
        )
        if cycle == "hourly":  # the most reset-heavy cycle carries the budget
            rows, budget = result, budget + elapsed

    _, elapsed = timed(
        "plausibility_check",
        lambda: plausibility_check(rows, reference, raw[-1][0], raw[0][0], 1.0),
    )
    budget += elapsed
    _, elapsed = timed(
        "aggregate_periods",
        lambda: aggregate_periods([(ts, total) for ts, _state, total in rows], TIMEZONE),
    )
    budget += elapsed

    print(f"\n  one simulate run: {budget * 1000:.0f} ms of computation")
    if budget > 2.0:
        print("  WARNING: that is slow enough for users to notice — check for quadratic work")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
