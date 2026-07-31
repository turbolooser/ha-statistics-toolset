"""Aggregate a cumulative series into per-period consumption for graphing.

The panel shows a *before* (current, still corrupted) and *after* (proposed, clean) bar
chart. Both are derived here from the respective cumulative ``(timestamp, sum)`` series by
taking, per calendar month, the consumption = last sum of the month minus last sum of the
previous month. Months are bucketed DST-correctly in the local timezone.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .outliers import Point

# One bar of the chart: (label, consumption).
Bar = tuple[str, float]


def period_label(ts: float, tz_name: str) -> str:
    """The same "%Y-%m" bucket label a timestamp falls into in ``aggregate_periods`` —
    shared so a caller can point at which bar in the chart a given timestamp belongs to
    (e.g. an outlier) without re-deriving the bucketing rule."""
    return datetime.fromtimestamp(ts, timezone.utc).astimezone(ZoneInfo(tz_name)).strftime("%Y-%m")


def aggregate_periods(sum_series: Sequence[Point], tz_name: str) -> list[Bar]:
    """Return monthly consumption bars from a cumulative ``(timestamp, sum)`` series."""
    if not sum_series:
        return []
    last_by_month: "OrderedDict[str, float]" = OrderedDict()
    for ts, value in sum_series:
        label = period_label(ts, tz_name)
        last_by_month[label] = value  # keeps the last sum seen in that month

    # The baseline is where the series *starts*, not zero. A running counter can already
    # stand at thousands of kWh; treating its first month's cumulative value as consumption
    # produced one giant bar that flattened every other month into a line.
    bars: list[Bar] = []
    prev = sum_series[0][1]
    for label, value in last_by_month.items():
        bars.append((label, round(max(0.0, value - prev), 2)))
        prev = value
    return bars
