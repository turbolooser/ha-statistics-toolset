"""Derive a counter's (state, sum) series from the trusted reference.

    sum[t]   = reference[t] - reference[null_ts]            # cumulative
    state[t] = reference[t] - reference[cycle_reset(t)]     # saw-tooth per cycle

A built-in plausibility check asserts that the derived end sum equals the reference delta,
so a broken reference or an off-by-one cycle rule is caught *before* anything is written.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .cycles import cycle_reset
from .outliers import Point
from .reference import timestamps_of, value_at

# A derived row is (timestamp, state, sum).
Row = tuple[float, float, float]


class PlausibilityError(Exception):
    """Raised when a derived series fails its sanity check (do not write it)."""


def _iso(ts: float) -> str:
    """UTC timestamp as a short ISO string, for readable error messages."""
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def derive_series(
    reference: Sequence[Point],
    cycle: str,
    tz_name: str,
    start_ts: float,
    end_ts: float,
    null_ts: float,
    round_digits: int = 3,
    extra_timestamps: Sequence[float] = (),
) -> list[Row]:
    """Derive ``(timestamp, state, sum)`` rows for a counter.

    Args:
        reference: Cleaned cumulative ``(timestamp, value)`` reference, sorted ascending.
        cycle: Counter cycle type (see :mod:`.cycles`).
        tz_name: IANA timezone name for the DST-correct cycle reset, e.g. ``Europe/Berlin``.
        start_ts: First timestamp (inclusive) of the range to rebuild.
        end_ts: Last timestamp (inclusive) of the range to rebuild.
        null_ts: Zero point for the cumulative ``sum`` (usually the range start).
        round_digits: Decimal places for the written values.
        extra_timestamps: Timestamps to also emit a row for, beyond the reference's own —
            normally the counter's *own* existing points. The reference is stepped (last
            known value carried forward, same rule as ``value_at``), so an hour missing from
            the reference — a gap in its own recorder history — still gets overwritten
            instead of silently keeping whatever (possibly corrupt) value already sits
            there. Without this, a write only ever touches timestamps the reference happens
            to have, and a source-side gap leaves the old value at that hour untouched even
            though every neighbouring hour was rebuilt (found live: 6 hours in a real
            counter's history stayed corrupt after a fix, each one a gap in the source).
    """
    tz = ZoneInfo(tz_name)
    keys = timestamps_of(reference)  # built once; see value_at() on why this matters
    base = value_at(reference, null_ts, keys)
    if base is None:
        base = reference[0][1] if reference else 0.0

    timestamps = sorted(
        {ts for ts, _val in reference if start_ts <= ts <= end_ts}
        | {ts for ts in extra_timestamps if start_ts <= ts <= end_ts}
    )

    rows: list[Row] = []
    for ts in timestamps:
        val = value_at(reference, ts, keys)
        if val is None:
            continue  # ts predates the reference entirely — nothing to derive it from
        dt_local = datetime.fromtimestamp(ts, timezone.utc).astimezone(tz)
        reset_ts = cycle_reset(dt_local, cycle).timestamp()
        reset_val = value_at(reference, reset_ts, keys)
        if reset_val is None:
            reset_val = base
        state = max(0.0, val - reset_val)
        cumulative = val - base
        rows.append((ts, round(state, round_digits), round(cumulative, round_digits)))
    return rows


def plausibility_check(
    rows: Sequence[Row],
    reference: Sequence[Point],
    end_ts: float,
    null_ts: float,
    tolerance: float,
) -> float:
    """Assert the derived end sum matches the reference delta; return that delta.

    Raises:
        PlausibilityError: If the series is empty, the range is outside the reference,
            or the end sum deviates from the reference delta by more than ``tolerance``.
    """
    if not rows:
        raise PlausibilityError("Derived series is empty.")
    keys = timestamps_of(reference)
    start_val = value_at(reference, null_ts, keys)
    end_val = value_at(reference, end_ts, keys)
    if start_val is None or end_val is None:
        # Name the actual boundaries: "outside the reference" alone is undiagnosable, and
        # the usual cause is a range that starts before the source has any data.
        span = (
            f"reference covers {_iso(reference[0][0])} .. {_iso(reference[-1][0])}"
            if reference
            else "reference series is empty"
        )
        raise PlausibilityError(
            f"Requested range {_iso(null_ts)} .. {_iso(end_ts)} lies outside the reference "
            f"series ({span}). Pick a start at or after the reference start."
        )
    expected = end_val - start_val
    got = rows[-1][2]
    if abs(got - expected) > tolerance:
        raise PlausibilityError(
            f"End sum {got:.3f} deviates from reference delta {expected:.3f} "
            f"(tolerance {tolerance})."
        )
    return expected
