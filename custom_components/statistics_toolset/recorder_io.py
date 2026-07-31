"""Home Assistant recorder glue.

Thin async wrappers around the **official** recorder statistics APIs. No direct SQLite
access happens anywhere in this integration — all reads and writes go through the recorder.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    get_metadata,
    statistics_during_period,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .const import DOMAIN, READ_ONLY_MODE, WRITE_ALLOWLIST

# (timestamp_seconds, state, sum) as read back from long-term statistics.
StatRow = tuple[float, float | None, float | None]

# Statistics exist from 2018 at the earliest; this covers any real history.
_EARLIEST = datetime(2015, 1, 1, tzinfo=dt_util.UTC)

# Same budget the recorder's own websocket handler (recorder/clear_statistics) gives itself.
_CLEAR_STATISTICS_TIMEOUT = 10.0


def write_locks(hass: HomeAssistant) -> tuple[bool, tuple[str, ...]]:
    """Return the effective ``(read_only, allowlist)``.

    Configuration from ``configuration.yaml`` wins; the constants in :mod:`.const` are the
    fallback and stay on the safe side. Reading this at call time means a YAML change takes
    effect on reload instead of being baked in at import.
    """
    options = (hass.data.get(DOMAIN) or {}) if hasattr(hass, "data") else {}
    read_only = options.get("read_only", READ_ONLY_MODE)
    allowlist = tuple(options.get("write_allowlist", WRITE_ALLOWLIST) or ())
    return bool(read_only), allowlist


def assert_writable(hass: HomeAssistant, statistic_id: str) -> None:
    """Both write locks, checked in one place — every write path goes through here.

    Read-only blocks everything; a non-empty allowlist restricts writing to the listed ids,
    so a test counter can be worked on while real data stays unreachable even if something
    else goes wrong.
    """
    read_only, allowlist = write_locks(hass)
    if read_only:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="read_only_mode",
        )
    if allowlist and statistic_id not in allowlist:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="not_in_allowlist",
            translation_placeholders={
                "statistic_id": statistic_id,
                "allowlist": ", ".join(allowlist),
            },
        )


async def read_metadata(hass: HomeAssistant, statistic_id: str) -> dict | None:
    """Return the recorder's metadata for ``statistic_id`` (unit, has_sum, …) or ``None``.

    A backup has to carry this: whether a series is a sum or a mean, and in which unit, is
    not recoverable from the values alone, and a restore that guesses it wrong writes a
    series Home Assistant then misinterprets.
    """
    instance = get_instance(hass)
    result = await instance.async_add_executor_job(
        lambda: get_metadata(hass, statistic_ids={statistic_id})
    )
    entry = result.get(statistic_id)
    if not entry:
        return None
    _row_id, meta = entry
    return {
        "has_mean": bool(meta.get("has_mean")),
        "has_sum": bool(meta.get("has_sum")),
        "name": meta.get("name"),
        "source": meta.get("source") or "recorder",
        "statistic_id": statistic_id,
        "unit_of_measurement": meta.get("unit_of_measurement"),
    }


async def read_full_history(hass: HomeAssistant, statistic_id: str) -> list[StatRow]:
    """Read the **entire** hourly history of ``statistic_id``.

    A backup must cover everything, not a chosen range: the recorder can only delete a whole
    ``statistic_id``, so an exact rollback is a clear-and-reimport. A partial backup would
    silently drop whatever lies outside it.
    """
    return await read_statistics(hass, statistic_id, _EARLIEST, dt_util.utcnow())


async def clear_statistic(hass: HomeAssistant, statistic_id: str) -> None:
    """Delete **all** statistics of a single ``statistic_id``. WRITES.

    Gated by the same central read-only lock as every other write path. Only ever called
    with one id, immediately before re-importing a verified full backup.

    Must go through ``instance.async_clear_statistics`` (queued onto the recorder's own
    worker thread), not the raw ``clear_statistics`` function via a plain executor job —
    that runs on the recorder's *db executor* pool, a different thread from the one
    ``StatisticsMetaManager.delete`` asserts against, and raises "Detected unsafe call not
    in recorder thread". This is the same pattern the recorder's own
    ``recorder/clear_statistics`` websocket handler uses: queue the task, bridge its
    ``on_done`` callback (which fires on the recorder thread) back to the event loop via
    ``call_soon_threadsafe``, and await it with a timeout.
    """
    assert_writable(hass, statistic_id)
    instance = get_instance(hass)
    done = asyncio.Event()

    def _on_done() -> None:
        hass.loop.call_soon_threadsafe(done.set)

    instance.async_clear_statistics([statistic_id], on_done=_on_done)
    async with asyncio.timeout(_CLEAR_STATISTICS_TIMEOUT):
        await done.wait()


async def read_statistics(
    hass: HomeAssistant, statistic_id: str, start: datetime, end: datetime
) -> list[StatRow]:
    """Read hourly long-term statistics for ``statistic_id`` in ``[start, end]``.

    Runs in the recorder executor. Returns rows sorted by time ascending.
    """
    instance = get_instance(hass)
    result = await instance.async_add_executor_job(
        statistics_during_period,
        hass,
        start,
        end,
        {statistic_id},
        "hour",
        None,
        {"state", "sum"},
    )
    rows: list[StatRow] = []
    for item in result.get(statistic_id, []):
        rows.append(
            (
                float(item["start"]),
                _as_float(item.get("state")),
                _as_float(item.get("sum")),
            )
        )
    return rows


async def write_statistics(
    hass: HomeAssistant,
    statistic_id: str,
    unit_of_measurement: str,
    rows: list[tuple[float, float, float]],
    metadata: dict | None = None,
) -> None:
    """Overwrite the given ``(timestamp, state, sum)`` points via ``import_statistics``.

    Only the supplied timestamps are affected; existing points at other times are kept.
    This does **not** touch ``statistics_short_term`` — the recorder keeps that in sync
    going forward. Must be called from the event loop; ``async_import_statistics`` hands
    the work to the recorder itself.

    ``async_import_statistics`` only *queues* the write and returns immediately — it does
    not wait for the recorder thread to actually run it. A caller that reads the data back
    right after (``restore``'s verification does exactly that) would otherwise race the
    import and see stale data. ``async_block_till_done`` queues a ``SynchronizeTask`` behind
    it on the same FIFO queue and awaits its completion, so by the time this function
    returns, the write has genuinely happened — not just been scheduled.
    """
    assert_writable(hass, statistic_id)
    # Prefer the metadata a backup carries: whether a series is a sum or a mean is not
    # recoverable from the values, and guessing it writes something HA misreads.
    meta = dict(metadata) if metadata else {
        "has_mean": False,
        "has_sum": True,
        "name": None,
        "source": "recorder",
    }
    meta["statistic_id"] = statistic_id
    meta.setdefault("unit_of_measurement", unit_of_measurement)
    statistics = [
        {
            "start": datetime.fromtimestamp(ts).astimezone().replace(microsecond=0),
            "state": state,
            "sum": summed,
        }
        for ts, state, summed in rows
    ]
    async_import_statistics(hass, meta, statistics)
    await get_instance(hass).async_block_till_done()


async def stat_range(
    hass: HomeAssistant, statistic_id: str
) -> tuple[float | None, float | None]:
    """Return (first_ts, now_ts) of the sensor's **cumulative** statistics — for auto-detect.

    Uses monthly buckets (cheap) just to find the earliest recorded month; the end is
    "now". Returns (None, None) if the sensor has no ``sum`` statistics at all.

    Buckets without a ``sum`` value are ignored on purpose: a mean-only sensor (e.g. power
    in W) still yields buckets for a ``sum`` query, just without the key. Counting those
    would treat such a sensor as a usable cumulative source and clip the detected range to
    it — which is exactly the wrong answer.
    """
    now = dt_util.utcnow()
    far = now - timedelta(days=366 * 8)
    instance = get_instance(hass)
    result = await instance.async_add_executor_job(
        statistics_during_period, hass, far, now, {statistic_id}, "month", None, {"sum"}
    )
    with_sum = [row for row in result.get(statistic_id, []) if row.get("sum") is not None]
    if not with_sum:
        return None, None

    # A monthly bucket starts at the 1st of the month, but the sensor's first actual data
    # point can be days later. Returning the bucket start would put the proposed range
    # *before* the series — which makes the plausibility check reject the repair. So drill
    # into that first month at hourly resolution to get the real first point.
    month_start = float(with_sum[0]["start"])
    hourly = await instance.async_add_executor_job(
        statistics_during_period,
        hass,
        dt_util.utc_from_timestamp(month_start),
        dt_util.utc_from_timestamp(month_start) + timedelta(days=62),
        {statistic_id},
        "hour",
        None,
        {"sum"},
    )
    first_hour = next(
        (
            float(row["start"])
            for row in hourly.get(statistic_id, [])
            if row.get("sum") is not None
        ),
        month_start,
    )
    return max(first_hour, month_start), now.timestamp()


def _as_float(value: object) -> float | None:
    """Best-effort float conversion, tolerating ``None``."""
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
