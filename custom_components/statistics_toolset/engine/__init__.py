"""Home-Assistant-independent core mechanic of the HA Statistics Toolset.

This package contains pure functions operating on plain ``(timestamp, value)`` data so
that the repair logic can be unit-tested without a running Home Assistant instance.

The public surface:

* :func:`~.reference.build_reference` - turn a raw cumulative series into a cleaned,
  monotonic reference (outliers removed via the offset method).
* :func:`~.derive.derive_series` - derive a counter's ``(state, sum)`` series for a given
  cycle type and time range from that reference.
* :func:`~.derive.plausibility_check` - assert the derived end sum equals the reference
  delta before anything is written back.
"""

from __future__ import annotations

from .cycles import cycle_reset
from .derive import PlausibilityError, derive_series, plausibility_check
from .outliers import clean_cumulative, estimate_max_rate, find_outliers
from .periods import aggregate_periods, period_label
from .reference import build_reference, timestamps_of, value_at

__all__ = [
    "cycle_reset",
    "clean_cumulative",
    "find_outliers",
    "estimate_max_rate",
    "aggregate_periods",
    "period_label",
    "build_reference",
    "value_at",
    "timestamps_of",
    "derive_series",
    "plausibility_check",
    "PlausibilityError",
]
