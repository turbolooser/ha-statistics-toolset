"""Build and query the trusted cumulative reference series.

The reference is the single source of truth from which every counter is derived. It is the
cleaned cumulative consumption of a long-running sensor (typically a Riemann ``integration``
sensor that predates the corrupted counters).
"""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Sequence

from .outliers import Point, clean_cumulative


def build_reference(
    raw: Sequence[Point], max_rate_per_hour: float, median_rate: float
) -> list[Point]:
    """Return a cleaned, monotonic reference from a raw cumulative series.

    ``raw`` is a list of ``(timestamp, cumulative_value)`` sorted ascending, e.g. the
    ``sum`` column of the source sensor's long-term statistics — either a separate trusted
    sensor or, in self mode, the counter itself.
    """
    if not raw:
        return []
    return clean_cumulative(raw, max_rate_per_hour, median_rate)


def timestamps_of(reference: Sequence[Point]) -> list[float]:
    """Return just the timestamps of ``reference``, for repeated :func:`value_at` lookups."""
    return [ts for ts, _value in reference]


def value_at(
    reference: Sequence[Point], ts: float, timestamps: Sequence[float] | None = None
) -> float | None:
    """Return the reference value at or immediately before ``ts`` (step lookup).

    Returns ``None`` if ``ts`` predates the first reference point. Uses binary search;
    ``reference`` must be sorted by timestamp ascending.

    Pass ``timestamps`` (from :func:`timestamps_of`) when looking up many values against the
    same reference. Without it the key list is rebuilt per call, which turns the binary
    search into a linear scan — quadratic overall, and that dominated everything else:
    ~10 s for 21 600 points, all of it inside Home Assistant's event loop.
    """
    if not reference:
        return None
    keys = timestamps if timestamps is not None else [p[0] for p in reference]
    idx = bisect_right(keys, ts) - 1
    if idx < 0:
        return None
    return reference[idx][1]
