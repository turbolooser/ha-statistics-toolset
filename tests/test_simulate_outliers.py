"""Covers `simulate`'s outlier_periods: "N outliers found" alone doesn't say *where* — the
panel highlights the corresponding bar in the chart, so the service response has to
actually carry which period(s) an outlier falls into, and it has to agree with how the
chart itself buckets timestamps into bars (see engine/periods.py: period_label vs
aggregate_periods).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from statistics_toolset_stub import FakeRecorder, load_init

DOMAIN = "statistics_toolset"
HOUR = 3600.0
BASE = 1_735_689_600.0  # 2025-01-01 00:00 UTC
BERLIN = "Europe/Berlin"


@pytest.fixture
def loaded():
    fake = FakeRecorder()
    init_module, io, _coordinator = load_init(fake)
    io.READ_ONLY_MODE = False
    return init_module, io, fake


def _ramp_with_one_spike(start_ts: float, hours: int, spike_at: int) -> list[tuple[float, float, float]]:
    """A cumulative series that grows by 1.0/hour, except one hour that jumps by 5000 —
    the offset method keeps that extra 5000 in the series forever after, so this produces
    exactly one outlier (the jump in), not a second one on the way back down."""
    rows = []
    acc = 0.0
    for i in range(hours):
        acc += 5000.0 if i == spike_at else 1.0
        ts = start_ts + i * HOUR
        rows.append((ts, acc, acc))
    return rows


def test_simulate_reports_which_bar_an_outlier_falls_into(loaded) -> None:
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        spike_index = 400  # a few weeks in, so the series spans more than one month
        rows = _ramp_with_one_spike(BASE, hours=24 * 70, spike_at=spike_index)
        fake.set_history("sensor.test", rows)

        start = datetime.fromtimestamp(rows[0][0], tz=timezone.utc)
        end = datetime.fromtimestamp(rows[-1][0], tz=timezone.utc)
        result = await fake.hass.services.async_call(
            DOMAIN, "simulate",
            {
                "statistic_id": "sensor.test",
                "reference_id": "",
                "cycle": "monthly",
                "start": start,
                "end": end,
                "max_rate_per_hour": 25.0,
            },
        )

        assert result["outliers_found"] == 1
        assert len(result["outlier_periods"]) == 1

        expected_label = (
            datetime.fromtimestamp(rows[spike_index][0], tz=ZoneInfo(BERLIN)).strftime("%Y-%m")
        )
        assert result["outlier_periods"] == [expected_label]

        # Must actually be one of the bars in the chart the panel highlights it against —
        # a label the frontend can't find in current_periods would just render nothing.
        charted_labels = {p["label"] for p in result["current_periods"]}
        assert expected_label in charted_labels

    asyncio.run(scenario())


def test_simulate_reports_no_outlier_periods_when_the_series_is_clean(loaded) -> None:
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        rows = _ramp_with_one_spike(BASE, hours=24 * 10, spike_at=-1)  # -1 never matches i
        fake.set_history("sensor.test", rows)

        start = datetime.fromtimestamp(rows[0][0], tz=timezone.utc)
        end = datetime.fromtimestamp(rows[-1][0], tz=timezone.utc)
        result = await fake.hass.services.async_call(
            DOMAIN, "simulate",
            {
                "statistic_id": "sensor.test",
                "reference_id": "",
                "cycle": "monthly",
                "start": start,
                "end": end,
                "max_rate_per_hour": 25.0,
            },
        )
        assert result["outliers_found"] == 0
        assert result["outlier_periods"] == []

    asyncio.run(scenario())
