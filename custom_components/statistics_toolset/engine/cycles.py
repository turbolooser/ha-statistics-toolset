"""Cycle reset rules for utility_meter counter types.

The only thing that differs between a yearly / monthly / weekly / daily counter is *when*
its ``state`` resets to zero. Everything else in the mechanic is identical. These rules are
evaluated on **local** datetimes so daylight-saving transitions are handled correctly
(a fixed UTC offset would misplace month/week boundaries in winter).
"""

from __future__ import annotations

from datetime import datetime, timedelta

# Public cycle identifiers (kept in sync with const.CYCLES).
# These mirror utility_meter's own periods, whose reset points are defined by the cron
# patterns in ``utility_meter.sensor.PERIOD2CRON`` (with the default offset of 0):
#   quarter-hourly "0/15 * * * *" · hourly "0 * * * *" · daily "0 0 * * *"
#   weekly "0 0 * * 1" (Monday) · monthly "0 0 1 * *" · bimonthly "0 0 1 */2 *"
#   quarterly "0 0 1 */3 *" · yearly "0 0 1 1/12 *"
# In cron, ``*/2`` and ``*/3`` on the month field step from the minimum (January), giving
# months 1,3,5,7,9,11 and 1,4,7,10 respectively.
YEARLY = "yearly"
QUARTERLY = "quarterly"
BIMONTHLY = "bimonthly"
MONTHLY = "monthly"
WEEKLY = "weekly"
DAILY = "daily"
HOURLY = "hourly"
QUARTER_HOURLY = "quarter-hourly"
# A utility_meter configured without a cycle never resets (a permanent, cumulative total).
NONE = "none"

_EPOCH_YEAR = 1970


def cycle_reset(dt_local: datetime, cycle: str) -> datetime:
    """Return the local start (last reset) of the cycle containing ``dt_local``.

    Args:
        dt_local: A timezone-aware datetime in the user's local timezone.
        cycle: One of the identifiers above.

    Returns:
        The timezone-aware local datetime at which the current cycle started
        (i.e. when the counter's ``state`` last reset to 0). For ``none`` this is a point
        before any real data, so ``state`` equals the cumulative sum — a counter that never
        resets.

    Raises:
        ValueError: If ``cycle`` is not a supported type.
    """
    if cycle == NONE:
        return dt_local.replace(
            year=_EPOCH_YEAR, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    if cycle == QUARTER_HOURLY:
        return dt_local.replace(
            minute=dt_local.minute - dt_local.minute % 15, second=0, microsecond=0
        )
    if cycle == HOURLY:
        return dt_local.replace(minute=0, second=0, microsecond=0)

    midnight = dt_local.replace(hour=0, minute=0, second=0, microsecond=0)
    if cycle == YEARLY:
        return midnight.replace(month=1, day=1)
    if cycle == QUARTERLY:
        # Quarters start in January, April, July, October.
        return midnight.replace(month=dt_local.month - (dt_local.month - 1) % 3, day=1)
    if cycle == BIMONTHLY:
        # Two-month periods start in the odd months: January, March, May, …
        return midnight.replace(month=dt_local.month - (dt_local.month - 1) % 2, day=1)
    if cycle == MONTHLY:
        return midnight.replace(day=1)
    if cycle == WEEKLY:
        # Monday is weekday() == 0; Home Assistant's weekly utility_meter resets Monday.
        return midnight - timedelta(days=dt_local.weekday())
    if cycle == DAILY:
        return midnight
    raise ValueError(f"Unsupported cycle type: {cycle!r}")
