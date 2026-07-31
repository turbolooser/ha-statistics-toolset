"""Unit tests for the Home-Assistant-independent engine.

These run without Home Assistant: ``pytest tests/``.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from engine import (
    PlausibilityError,
    aggregate_periods,
    build_reference,
    cycle_reset,
    clean_cumulative,
    derive_series,
    estimate_max_rate,
    find_outliers,
    period_label,
    plausibility_check,
    value_at,
)

BERLIN = "Europe/Berlin"
HOUR = 3600.0


def _ramp(start_ts: float, hourly: list[float]) -> list[tuple[float, float]]:
    """Build a cumulative series from a list of hourly increments."""
    pts, acc = [], 0.0
    for i, inc in enumerate(hourly):
        acc += inc
        pts.append((start_ts + i * HOUR, acc))
    return pts


def test_cycle_reset_rules() -> None:
    tz = ZoneInfo(BERLIN)
    dt = datetime(2026, 7, 15, 13, 0, tzinfo=tz)  # a Wednesday
    assert cycle_reset(dt, "yearly") == datetime(2026, 1, 1, tzinfo=tz)
    assert cycle_reset(dt, "monthly") == datetime(2026, 7, 1, tzinfo=tz)
    assert cycle_reset(dt, "weekly") == datetime(2026, 7, 13, tzinfo=tz)  # Monday
    assert cycle_reset(dt, "daily") == datetime(2026, 7, 15, tzinfo=tz)


def test_offset_method_does_not_cascade() -> None:
    """A single outlier must be removed exactly once, not eat the rest of the series."""
    series = _ramp(0.0, [1.0, 1.0, 5000.0, 1.0, 1.0])  # one phantom jump
    cleaned = clean_cumulative(series, max_rate_per_hour=25.0, median_rate=0.8)
    # Total plausible consumption ~ 1+1+0.8+1+1 = 4.8, not thousands.
    assert cleaned[-1][1] < 10.0
    # Later real increments survive (monotonic, ~1/h after the jump).
    assert cleaned[-1][1] > cleaned[-2][1]


def test_find_outliers_reports_the_jump() -> None:
    series = _ramp(0.0, [1.0, 5000.0, 1.0])
    outliers = find_outliers(series, max_rate_per_hour=25.0)
    assert len(outliers) == 1


def test_period_label_matches_aggregate_periods_bucketing() -> None:
    """The panel highlights an outlier's bar by looking up this label in current_periods —
    if the two ever bucket a timestamp differently, the "outlier" marker points at the
    wrong bar instead of a mismatch being caught here."""
    tz = ZoneInfo(BERLIN)
    ts = datetime(2026, 3, 15, 13, 0, tzinfo=tz).timestamp()
    assert period_label(ts, BERLIN) == "2026-03"

    series = [
        (datetime(2026, 1, 1, tzinfo=tz).timestamp(), 100.0),
        (ts, 250.0),
        (datetime(2026, 4, 1, tzinfo=tz).timestamp(), 300.0),
    ]
    bars = aggregate_periods(series, BERLIN)
    assert period_label(ts, BERLIN) in dict(bars)


def test_value_at_step_lookup() -> None:
    ref = [(0.0, 0.0), (HOUR, 1.0), (2 * HOUR, 3.0)]
    assert value_at(ref, -1.0) is None
    assert value_at(ref, HOUR) == 1.0
    assert value_at(ref, 1.5 * HOUR) == 1.0  # step, not interpolation


def test_aggregate_periods_monthly() -> None:
    tz = ZoneInfo(BERLIN)
    jan = datetime(2026, 1, 1, tzinfo=tz).timestamp()
    feb = datetime(2026, 2, 1, tzinfo=tz).timestamp()
    mar = datetime(2026, 3, 1, tzinfo=tz).timestamp()
    # cumulative sums: Jan ends at 100, Feb at 250, Mar at 300
    series = [(jan, 100.0), (feb, 250.0), (mar, 300.0)]
    bars = aggregate_periods(series, BERLIN)
    labels = [b[0] for b in bars]
    assert labels == ["2026-01", "2026-02", "2026-03"]
    # consumption = diff to previous month's last cumulative value
    assert bars[1][1] == 150.0  # Feb: 250 - 100
    assert bars[2][1] == 50.0  # Mar: 300 - 250


def test_derive_and_plausibility_daily() -> None:
    tz = ZoneInfo(BERLIN)
    start = datetime(2026, 3, 1, 0, 0, tzinfo=tz)
    start_ts = start.timestamp()
    raw = _ramp(start_ts, [1.0] * 72)  # 3 days, 1 kWh/h
    ref = build_reference(raw, 25.0, 0.8)
    end_ts = raw[-1][0]
    rows = derive_series(ref, "daily", BERLIN, start_ts, end_ts, start_ts)
    # Daily state resets: it must return to ~0 at each midnight and never exceed ~24.
    assert max(r[1] for r in rows) <= 25.0
    # Plausibility holds: end sum equals reference delta.
    plausibility_check(rows, ref, end_ts, start_ts, tolerance=1.0)


def test_estimate_max_rate_ignores_extreme_outliers() -> None:
    """The threshold must sit above real consumption but far below a phantom jump."""
    series = _ramp(0.0, [1.0] * 50 + [275000.0] + [1.0] * 50)
    rate = estimate_max_rate(series)
    assert rate > 1.0, "real hourly consumption must stay below the threshold"
    assert rate < 275000.0, "the phantom jump must stay above the threshold"
    assert find_outliers(series, rate) != [], "the phantom jump must be detected"


def test_estimate_max_rate_floor_on_sparse_data() -> None:
    assert estimate_max_rate([]) == 15.0
    assert estimate_max_rate([(0.0, 5.0)]) == 15.0  # single point: no rate at all


def test_plausibility_error_names_the_boundaries() -> None:
    """A range before the reference must fail with a diagnosable message, not a bare one."""
    tz = ZoneInfo(BERLIN)
    start = datetime(2026, 3, 1, tzinfo=tz).timestamp()
    ref = build_reference(_ramp(start, [1.0] * 24), 25.0, 0.8)
    rows = derive_series(ref, "daily", BERLIN, start, ref[-1][0], start)
    too_early = start - 30 * 24 * HOUR
    with pytest.raises(PlausibilityError) as exc:
        plausibility_check(rows, ref, ref[-1][0], too_early, tolerance=1.0)
    msg = str(exc.value)
    assert "2026-01-29" in msg, "must name the requested start"
    assert "reference covers 2026-02-28" in msg, "must name where the reference starts"


def test_cycle_reset_hourly_and_quarter_hourly() -> None:
    """PERIOD2CRON: hourly '0 * * * *', quarter-hourly '0/15 * * * *'."""
    tz = ZoneInfo(BERLIN)
    dt = datetime(2026, 7, 15, 13, 37, 42, tzinfo=tz)
    assert cycle_reset(dt, "hourly") == datetime(2026, 7, 15, 13, 0, tzinfo=tz)
    assert cycle_reset(dt, "quarter-hourly") == datetime(2026, 7, 15, 13, 30, tzinfo=tz)
    for minute, want in ((0, 0), (14, 0), (15, 15), (44, 30), (45, 45), (59, 45)):
        got = cycle_reset(datetime(2026, 7, 15, 13, minute, tzinfo=tz), "quarter-hourly")
        assert got.minute == want, f"{minute} -> {got.minute}, want {want}"


def test_cycle_reset_quarterly_and_bimonthly() -> None:
    """Cron '*/3' and '*/2' on the month field step from January."""
    tz = ZoneInfo(BERLIN)
    quarterly_starts = {1: 1, 2: 1, 3: 1, 4: 4, 5: 4, 6: 4, 7: 7, 8: 7, 9: 7, 10: 10, 11: 10, 12: 10}
    bimonthly_starts = {1: 1, 2: 1, 3: 3, 4: 3, 5: 5, 6: 5, 7: 7, 8: 7, 9: 9, 10: 9, 11: 11, 12: 11}
    for month, want in quarterly_starts.items():
        got = cycle_reset(datetime(2026, month, 20, 13, 0, tzinfo=tz), "quarterly")
        assert (got.month, got.day) == (want, 1), f"quarterly month {month} -> {got}"
    for month, want in bimonthly_starts.items():
        got = cycle_reset(datetime(2026, month, 20, 13, 0, tzinfo=tz), "bimonthly")
        assert (got.month, got.day) == (want, 1), f"bimonthly month {month} -> {got}"


def test_cycle_none_never_resets() -> None:
    """A permanent meter has no reset: its state must equal the cumulative sum."""
    tz = ZoneInfo(BERLIN)
    start = datetime(2026, 3, 1, tzinfo=tz).timestamp()
    raw = _ramp(start, [1.0] * 72)
    ref = build_reference(raw, 25.0, 0.8)
    rows = derive_series(ref, "none", BERLIN, start, raw[-1][0], start)
    assert rows, "series must not be empty"
    for _ts, state, summed in rows:
        assert state == summed, "with cycle 'none', state and sum must be identical"
    # ... and it keeps growing instead of sawtoothing back to zero.
    assert rows[-1][1] > rows[0][1] + 60


def test_unsupported_cycle_raises() -> None:
    with pytest.raises(ValueError):
        cycle_reset(datetime(2026, 7, 15, tzinfo=ZoneInfo(BERLIN)), "fortnightly")


def test_value_at_lookups_are_not_quadratic() -> None:
    """A repeated lookup must not rebuild the key list — that made derive_series O(n²).

    Measured on the real data set (21 600 hourly points, 2.5 years): 9.8 s before, 79 ms
    after. The budget below is deliberately loose so it fails only on a genuine regression,
    not on a slow machine.
    """
    import time

    from engine import timestamps_of

    n = 20_000
    ref = [(float(i) * HOUR, float(i)) for i in range(n)]
    keys = timestamps_of(ref)
    t0 = time.perf_counter()
    for i in range(0, n, 2):
        value_at(ref, ref[i][0], keys)
    elapsed = time.perf_counter() - t0
    assert elapsed < 1.0, f"{n // 2} lookups took {elapsed:.1f}s — key list rebuilt per call?"


def test_derive_series_stays_fast_on_long_ranges() -> None:
    """Guards the whole hot path: 2.5 years of hourly points must stay well under a second."""
    import time

    tz_start = datetime(2024, 2, 10, 12, 0, tzinfo=ZoneInfo(BERLIN)).timestamp()
    raw = [(tz_start + i * HOUR, i * 1.0) for i in range(21_600)]
    ref = build_reference(raw, 25.0, 0.8)
    t0 = time.perf_counter()
    rows = derive_series(ref, "hourly", BERLIN, raw[0][0], raw[-1][0], raw[0][0])
    elapsed = time.perf_counter() - t0
    assert len(rows) == len(raw)
    assert elapsed < 2.0, f"derive_series took {elapsed:.1f}s for {len(raw)} points"


def test_value_at_with_and_without_keys_agree() -> None:
    from engine import timestamps_of

    ref = [(0.0, 0.0), (HOUR, 1.0), (2 * HOUR, 3.0)]
    keys = timestamps_of(ref)
    for ts in (-1.0, 0.0, HOUR, 1.5 * HOUR, 99 * HOUR):
        assert value_at(ref, ts) == value_at(ref, ts, keys)


def test_first_bar_is_consumption_not_meter_reading() -> None:
    """A running counter starts high; its first bar must not be that reading.

    Before this, a counter standing at 25 000 kWh produced a 25 000 kWh January bar, which
    scaled the chart so that every other month collapsed into a flat line.
    """
    tz = ZoneInfo(BERLIN)
    jan = datetime(2026, 1, 1, tzinfo=tz).timestamp()
    series = [
        (jan, 25_000.0),  # the meter already stands here when the range begins
        (jan + 10 * 24 * HOUR, 25_300.0),
        (jan + 20 * 24 * HOUR, 25_494.0),  # last value in January
        (datetime(2026, 2, 15, tzinfo=tz).timestamp(), 26_000.0),
    ]
    bars = dict(aggregate_periods(series, BERLIN))
    assert bars["2026-01"] == 494.0, "January consumption, not the meter reading"
    assert bars["2026-02"] == 506.0, "26000 - 25494"
    assert max(bars.values()) < 1000.0, "no bar may carry the absolute meter reading"
