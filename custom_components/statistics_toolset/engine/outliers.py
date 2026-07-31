"""Outlier detection and removal for cumulative statistics series.

A cumulative counter should only ever grow by a physically plausible amount per hour.
A larger jump is a phantom (e.g. a corrupted setup phase writing 275,000 kWh). We remove
it with the **offset method**: subtract the phantom part once from every following value.

Critically we must *not* use a cascading replacement (``value = prev + x``): that keeps the
series permanently below the real curve and — because each subsequent original delta then
looks like an outlier too — eats its way through the entire history. The offset method
always compares against the *original* neighbouring value, so a single outlier is corrected
exactly once.
"""

from __future__ import annotations

from collections.abc import Sequence

# A point is (unix_timestamp_seconds, cumulative_value).
Point = tuple[float, float]


def find_outliers(
    series: Sequence[Point], max_rate_per_hour: float
) -> list[tuple[float, float, float]]:
    """Return outlier jumps as ``(timestamp, delta, rate_per_hour)`` tuples.

    Read-only: this is what the ``simulate`` preview reports as "outliers found". ``series``
    must be sorted by timestamp ascending.
    """
    outliers: list[tuple[float, float, float]] = []
    prev: Point | None = None
    for ts, val in series:
        if prev is not None:
            dt_h = max((ts - prev[0]) / 3600.0, 1e-9)
            delta = val - prev[1]
            rate = delta / dt_h
            if rate > max_rate_per_hour:
                outliers.append((ts, delta, rate))
        prev = (ts, val)
    return outliers


def clean_cumulative(
    series: Sequence[Point], max_rate_per_hour: float, median_rate: float
) -> list[Point]:
    """Return ``series`` with outlier jumps removed via the offset method.

    Args:
        series: Cumulative ``(timestamp, value)`` points, sorted ascending.
        max_rate_per_hour: Jumps exceeding this rate (kWh/h) are treated as phantoms.
        median_rate: Plausible hourly consumption substituted for the removed jump.

    Returns:
        A new list with the same timestamps and monotonic, plausible values.
    """
    out: list[Point] = []
    offset = 0.0
    prev: Point | None = None
    for ts, val in series:
        if prev is not None:
            dt_h = max((ts - prev[0]) / 3600.0, 1e-9)
            delta = val - prev[1]  # ORIGINAL delta, not the offset-adjusted one
            if delta / dt_h > max_rate_per_hour:
                offset += delta - median_rate * dt_h
        out.append((ts, val - offset))
        prev = (ts, val)
    return out


def estimate_max_rate(
    series: Sequence[Point], floor: float = 15.0, factor: float = 30.0
) -> float:
    """Estimate a per-hour outlier threshold from the data, so no manual value is needed.

    Uses the median hourly increase (robust against a handful of extreme outliers) times a
    generous factor, never below ``floor``. Real spikes stay under it; phantom jumps (orders
    of magnitude larger) land far above it.
    """
    rates = sorted(
        (series[i][1] - series[i - 1][1]) / max((series[i][0] - series[i - 1][0]) / 3600.0, 1e-9)
        for i in range(1, len(series))
        if series[i][1] - series[i - 1][1] > 0
    )
    if not rates:
        return floor
    median = rates[len(rates) // 2]
    return round(max(median * factor, floor), 1)
