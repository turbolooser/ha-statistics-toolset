"""Orchestration for the simulate / fix / backup / restore flows.

Design intent:
* ``simulate`` and ``backup`` never modify statistics (safe in read-only mode).
* ``fix`` and ``restore`` write, and are additionally gated by the central
  ``READ_ONLY_MODE`` lock in :mod:`.recorder_io` — no code path can write while it is on.
* Every ``fix`` takes a timestamped JSON backup *before* touching anything, so a repair is
  always reversible via ``restore``.
"""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    CYCLE_NONE,
    CYCLES,
    DEFAULT_MAX_RATE_PER_HOUR,
    DEFAULT_MEDIAN_RATE,
    DOMAIN,
    PLAUSI_TOLERANCE,
)
from .engine import (
    aggregate_periods,
    build_reference,
    derive_series,
    estimate_max_rate,
    find_outliers,
    period_label,
    plausibility_check,
)
from .recorder_io import (
    assert_writable,
    clear_statistic,
    read_full_history,
    read_metadata,
    read_statistics,
    stat_range,
    write_statistics,
)

# Map name suffixes to utility_meter cycles, for auto-detection.
_CYCLE_SUFFIXES = {
    "yearly": ("_jahr", "_year", "_yearly", "_annual"),
    "monthly": ("_monat", "_month", "_monthly"),
    "weekly": ("_woche", "_week", "_weekly"),
    "daily": ("_tag", "_day", "_daily", "_today"),
}


def _guess_cycle(statistic_id: str) -> str:
    """Guess the utility_meter cycle from the entity name (defaults to monthly)."""
    name = statistic_id.lower()
    for cycle, suffixes in _CYCLE_SUFFIXES.items():
        if any(name.endswith(sfx) or f"{sfx}_" in name for sfx in suffixes):
            return cycle
    return "monthly"


def _cycle_from_utility_meter_data(hass: HomeAssistant, statistic_id: str) -> tuple[str, str]:
    """Read the counter's **actual** cycle from utility_meter's runtime data.

    Returns ``(cycle, how)``; ``cycle`` is '' when it could not be read. Guessing from the
    entity name is a fallback only — a wrong cycle means a wrongly rebuilt series, and the
    real value is right there in ``hass.data``.

    A meter configured with a free ``cron`` pattern instead of a cycle cannot be expressed
    by our reset rules, so it is reported as unsupported rather than silently mapped.
    """
    info = _meter_info_for(hass, statistic_id)
    if info is None:
        return "", ""
    if info.get("cron"):  # CONF_CRON_PATTERN — arbitrary schedule, not one of our cycles
        return "", "unsupported_cron_pattern"
    cycle = info.get("cycle")  # CONF_METER_TYPE
    if isinstance(cycle, str) and cycle in CYCLES:
        return cycle, "utility_meter"
    if cycle in (None, ""):
        # A meter without a cycle is a permanent total that never resets.
        return CYCLE_NONE, "utility_meter"
    return "", f"unsupported_cycle:{cycle}"


# hass.data keys, used as plain strings so we don't import (and depend on) the
# utility_meter / integration components. Both are HassKey, which subclasses str.
_DATA_UTILITY = "utility_meter"  # utility_meter.const.DATA_UTILITY
_DATA_METER_SENSORS = "utility_meter_sensors"  # utility_meter.const.DATA_TARIFF_SENSORS
_DATA_ENTITY_COMPONENTS = "entity_components"  # entity_component.DATA_INSTANCES


def _source_from_config_entry(hass: HomeAssistant, statistic_id: str) -> str:
    """Source of a UI-created helper (utility_meter or integration config entry)."""
    entry = er.async_get(hass).async_get(statistic_id)
    if entry and entry.config_entry_id:
        ce = hass.config_entries.async_get_entry(entry.config_entry_id)
        if ce:
            src = ce.options.get("source") or ce.data.get("source")
            if isinstance(src, str) and src:
                return src
    return ""


def _meter_info_for(hass: HomeAssistant, statistic_id: str) -> dict | None:
    """Return the utility_meter runtime info that owns ``statistic_id``, if any.

    YAML meters have no config entry, so this is the only exact way to resolve them. The
    meters live in ``hass.data['utility_meter']`` keyed by meter name (YAML) or entry id
    (UI); each carries its ``source`` and ``cycle`` plus the sensor objects it created.
    """
    meters = hass.data.get(_DATA_UTILITY)
    if not isinstance(meters, dict):
        return None
    for info in meters.values():
        if not isinstance(info, dict):
            continue
        sensors = info.get(_DATA_METER_SENSORS) or []
        try:
            if any(getattr(s, "entity_id", None) == statistic_id for s in sensors):
                return info
        except TypeError:  # sensors not iterable
            continue
    return None


def _source_from_utility_meter_data(hass: HomeAssistant, statistic_id: str) -> str:
    """Source of a utility_meter (YAML or UI), read from its runtime data."""
    info = _meter_info_for(hass, statistic_id)
    src = info.get("source") if info else None
    return src if isinstance(src, str) and src else ""


def _source_from_state_attribute(hass: HomeAssistant, statistic_id: str) -> str:
    """Source of a Riemann ``integration`` sensor, which exposes it as a state attribute."""
    state = hass.states.get(statistic_id)
    if state is not None:
        src = state.attributes.get("source")
        # Guard against sensors using 'source' for something that isn't an entity_id.
        if isinstance(src, str) and src.count(".") == 1 and not src.endswith("."):
            return src
    return ""


def _source_from_entity_object(hass: HomeAssistant, statistic_id: str) -> str:
    """Last resort: ask the live entity object (private attributes, hence defensive).

    Covers counters whose integration keeps the source nowhere public —
    ``utility_meter`` uses ``_sensor_source_id``, ``integration`` uses ``_source_entity``.
    """
    try:
        component = hass.data.get(_DATA_ENTITY_COMPONENTS, {}).get("sensor")
        entity = component.get_entity(statistic_id) if component else None
    except Exception:  # noqa: BLE001 - internal API, must never break detection
        return ""
    for attr in ("_sensor_source_id", "_source_entity"):
        src = getattr(entity, attr, None)
        if isinstance(src, str) and src:
            return src
    return ""


def _guess_source(hass: HomeAssistant, statistic_id: str) -> tuple[str, str]:
    """Resolve the counter's source entity. Returns ``(source, how)``; '' → self mode.

    Tried in order of reliability; ``how`` names the winning strategy so ``detect`` can
    report *why* it proposes that source (or that none was found).
    """
    for how, finder in (
        ("config_entry", _source_from_config_entry),
        ("utility_meter", _source_from_utility_meter_data),
        ("state_attribute", _source_from_state_attribute),
        ("entity_object", _source_from_entity_object),
    ):
        src = finder(hass, statistic_id)
        if src and src != statistic_id:  # a self-reference is not a source
            return src, how
    return "", "none"


async def _source_chain(
    hass: HomeAssistant, statistic_id: str, max_depth: int = 5
) -> list[tuple[str, str, float]]:
    """Follow source references upstream, returning ``[(entity, how, first_ts), …]``.

    Counters are often derived in stages (``…_monat`` → a permanent total → a Riemann
    integration sensor). The further upstream, the less derived — and the less likely to
    have inherited a defect — so the root is the better reference.

    Only sensors with cumulative (``sum``) statistics are followed: the chain typically ends
    at a power sensor in W, which is not a usable reference. Cycles in the graph and repeated
    entities are guarded against.
    """
    chain: list[tuple[str, str, float]] = []
    seen = {statistic_id}
    current = statistic_id
    for _ in range(max_depth):
        source, how = _guess_source(hass, current)
        if not source or source in seen:
            break
        first_ts, _end = await stat_range(hass, source)
        if first_ts is None:
            break  # not cumulative (e.g. a mean-only power sensor) → chain ends here
        chain.append((source, how, first_ts))
        seen.add(source)
        current = source
    return chain


async def detect(hass: HomeAssistant, statistic_id: str) -> dict:
    """Suggest cycle, source, range and max_rate for a counter. Read-only."""
    cycle, cycle_via = _cycle_from_utility_meter_data(hass, statistic_id)
    if not cycle:
        cycle = _guess_cycle(statistic_id)
        cycle_via = f"name_guess:{cycle_via}" if cycle_via else "name_guess"
    counter_first, end_ts = await stat_range(hass, statistic_id)
    first_ts = counter_first
    source_first: float | None = None

    # Prefer the root of the source chain over the directly configured source.
    chain = await _source_chain(hass, statistic_id)
    if chain:
        source, how, src_first = chain[-1]
        source_first = src_first
        if len(chain) > 1:
            how = f"{how}:root_of_{len(chain)}"
        # What is repairable is bounded by the *source*, not by the counter: statistics can
        # be written for periods the counter never covered, which is how a history gets
        # extended back. The counter's own start is reported separately for reference.
        first_ts = src_first
    else:
        source, how = "", "none"
        direct, direct_how = _guess_source(hass, statistic_id)
        if direct:
            # There was a source, but it carries no cumulative statistics.
            how = f"discarded:{direct_how}:no_statistics"

    ref_id = source or statistic_id
    raw_ref = [
        (ts, s) for ts, _st, s in await read_statistics(
            hass,
            ref_id,
            dt_util.utc_from_timestamp(first_ts) if first_ts else dt_util.utcnow(),
            dt_util.utcnow(),
        ) if s is not None
    ] if first_ts else []
    max_rate = estimate_max_rate(raw_ref) if raw_ref else DEFAULT_MAX_RATE_PER_HOUR
    return {
        "statistic_id": statistic_id,
        "cycle": cycle,
        "cycle_via": cycle_via,  # read from utility_meter, or guessed from the name
        "reference_id": source,  # '' means self mode
        "source_detected": bool(source),
        "source_via": how,  # how it was resolved, or why it was discarded
        # Full upstream chain, nearest first — the proposal is its last entry.
        "source_chain": [entity for entity, _how, _first in chain],
        "start": dt_util.utc_from_timestamp(first_ts).isoformat() if first_ts else None,
        "end": dt_util.utc_from_timestamp(end_ts).isoformat()
        if end_ts
        else dt_util.utcnow().isoformat(),
        # Where the counter's own data begins vs. how far the source reaches back. When the
        # source starts earlier, a repair can extend the counter's history to that point.
        "counter_start": dt_util.utc_from_timestamp(counter_first).isoformat()
        if counter_first
        else None,
        "source_start": dt_util.utc_from_timestamp(source_first).isoformat()
        if source_first
        else None,
        "max_rate_per_hour": max_rate,
    }

_LOGGER = logging.getLogger(__name__)


@dataclass
class Preview:
    """Read-only result of a ``simulate`` run (also returned by ``fix``)."""

    statistic_id: str
    reference_id: str
    cycle: str
    outliers: list[tuple[float, float, float]]
    current_end_sum: float
    proposed_end_sum: float
    reference_delta: float
    points: int
    current_periods: list[tuple[str, float]] = field(default_factory=list)
    proposed_periods: list[tuple[str, float]] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    # Outliers smoothed out of the **source** while building the reference. Without these,
    # a repair silently drops that amount and the preview would claim "0 outliers" while
    # the proposed end sum sits below the source's raw delta.
    source_outliers: int = 0
    source_removed: float = 0.0
    raw_reference_delta: float = 0.0
    # Which bar(s) of current_periods an outlier falls into — "1 outlier" alone doesn't say
    # where; the panel highlights these bars instead of leaving that to guesswork.
    outlier_periods: list[str] = field(default_factory=list)


def _source_cleanup(
    raw_ref: list[tuple[float, float]],
    reference: list[tuple[float, float]],
    max_rate: float,
) -> tuple[int, float, float]:
    """Return ``(count, removed, raw_delta)`` for the smoothing applied to the source.

    ``build_reference`` quietly removes implausible jumps from the source. That is the point
    of it, but it must not be invisible: the proposed sum then sits below the source's raw
    delta, and a preview reporting only the *counter's* outliers would look like nothing
    happened.
    """
    if not raw_ref or not reference:
        return 0, 0.0, 0.0
    raw_delta = raw_ref[-1][1] - raw_ref[0][1]
    clean_delta = reference[-1][1] - reference[0][1]
    return len(find_outliers(raw_ref, max_rate)), raw_delta - clean_delta, raw_delta


def _clamped_start(
    raw_ref: list[tuple[float, float]], start: datetime, end: datetime
) -> tuple[float, float, list[dict]]:
    """Return ``(null_ts, end_ts, warnings)``, moving the start into the reference series.

    A requested start before the source's first data point cannot be rebuilt — the
    plausibility check would reject the whole run. Rather than failing on a range the user
    got from a preset ("all", "this year"), clamp to the first reference point and say so.

    Warnings are **structured** (``code`` plus values), not prose: the frontend renders them
    in the user's language. ``message`` is a plain-English fallback for anyone calling the
    service directly.
    """
    null_ts, end_ts = start.timestamp(), end.timestamp()
    warnings: list[dict] = []
    if raw_ref and raw_ref[0][0] > null_ts:
        moved_by = raw_ref[0][0] - null_ts
        null_ts = raw_ref[0][0]
        # Long-term statistics sit on hour boundaries, so any start that isn't on :00 gets
        # nudged by up to an hour. Reporting that as "the source has no data before this"
        # would be both noisy and untrue — only a real gap is worth a warning.
        if moved_by > 3600:
            moved = dt_util.utc_from_timestamp(null_ts)
            warnings.append(
                {
                    "code": "start_moved_up",
                    "timestamp": moved.isoformat(),
                    "message": (
                        f"Start moved up to {moved.isoformat()}: the source has no data "
                        "before that."
                    ),
                }
            )
    return null_ts, end_ts, warnings


def _timestamped_backup_path(backup_dir: Path, statistic_id: str) -> Path:
    """Return a unique, timestamped backup path so repeated backups never collide."""
    stamp = dt_util.utcnow().strftime("%Y%m%d_%H%M%S")
    return backup_dir / f"{statistic_id}.{stamp}.backup.json"


# Shared by every retry loop that rides out the recorder's commit-visibility lag (see
# _verify_restore below). Live-verified 2026-07-31: fix/restore against a 28k-point counter
# took 25-45s under real DB load in one environment — the previous ~8s budget was too tight
# and produced false-negative errors (source_no_statistics, restore_verification_failed)
# even though the write had actually succeeded. 20 attempts starting at 0.3s, capped at 3s,
# growing by 1.5x ≈ 48s worst case.
_VISIBILITY_RETRY_ATTEMPTS = 20
_VISIBILITY_RETRY_START_DELAY = 0.3
_VISIBILITY_RETRY_MAX_DELAY = 3.0


async def _read_sum_series_retrying(
    hass: HomeAssistant, statistic_id: str, start: datetime, end: datetime
) -> list[tuple[float, float]]:
    """Read a series' (timestamp, sum) points, retrying against the recorder's
    commit-visibility lag (see ``_verify_restore``) — a fix or restore that just touched
    this same statistic_id can still read back empty for a moment afterwards, e.g. when the
    guided workflow reads a counter immediately after restoring it.
    """
    delay = _VISIBILITY_RETRY_START_DELAY
    rows: list[tuple[float, float]] = []
    for _attempt in range(_VISIBILITY_RETRY_ATTEMPTS):
        rows = [
            (ts, s)
            for ts, _state, s in await read_statistics(hass, statistic_id, start, end)
            if s is not None
        ]
        if rows:
            return rows
        await asyncio.sleep(delay)
        delay = min(delay * 1.5, _VISIBILITY_RETRY_MAX_DELAY)
    return rows


async def simulate(
    hass: HomeAssistant,
    statistic_id: str,
    reference_id: str,
    cycle: str,
    start: datetime,
    end: datetime,
    unit: str,
    max_rate: float = 0.0,
) -> Preview:
    """Analyse a counter and return a preview of the proposed repair. Read-only.

    If ``reference_id`` is empty, the counter itself is used as the source ("self mode"):
    only its own outliers are smoothed. Otherwise the trusted source sensor is used for a
    full reconstruction.
    """
    ref_source = reference_id or statistic_id
    raw_ref = await _read_sum_series_retrying(hass, ref_source, start, end)
    if not raw_ref:
        # Typical when a range preset reaches back before the source existed. Say so with
        # the actual availability instead of failing deeper down with "series is empty".
        src_first, _src_end = await stat_range(hass, ref_source)
        available = (
            dt_util.utc_from_timestamp(src_first).isoformat()
            if src_first
            else ""  # no statistics at all
        )
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="source_no_data" if available else "source_no_statistics",
            translation_placeholders={
                "source": ref_source,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "available": available,
            },
        )
    if max_rate <= 0:  # 0 = auto: estimate the outlier threshold from the data
        max_rate = estimate_max_rate(raw_ref)
    reference = await hass.async_add_executor_job(
        build_reference, raw_ref, max_rate, DEFAULT_MEDIAN_RATE
    )

    target_sum = (
        raw_ref
        if statistic_id == ref_source
        else await _read_sum_series_retrying(hass, statistic_id, start, end)
    )
    outliers = find_outliers(target_sum, max_rate)
    current_end_sum = target_sum[-1][1] if target_sum else 0.0

    null_ts, end_ts, warnings = _clamped_start(raw_ref, start, end)
    source_outliers, source_removed, raw_delta = _source_cleanup(raw_ref, reference, max_rate)
    if source_outliers:
        warnings.append(
            {
                "code": "source_outliers_removed",
                "count": source_outliers,
                "amount": round(source_removed, 3),
                "message": (
                    f"{source_outliers} implausible jump(s) totalling "
                    f"{source_removed:.3f} were smoothed out of the source, so the proposed "
                    f"sum is below its raw delta of {raw_delta:.3f}."
                ),
            }
        )
    tz_name = str(dt_util.DEFAULT_TIME_ZONE)
    rows = await hass.async_add_executor_job(
        derive_series, reference, cycle, tz_name, null_ts, end_ts, null_ts
    )
    reference_delta = plausibility_check(rows, reference, end_ts, null_ts, PLAUSI_TOLERANCE)

    proposed_sum = [(ts, summed) for ts, _state, summed in rows]

    return Preview(
        statistic_id=statistic_id,
        reference_id=reference_id,
        cycle=cycle,
        outliers=outliers,
        current_end_sum=current_end_sum,
        proposed_end_sum=rows[-1][2] if rows else 0.0,
        reference_delta=reference_delta,
        points=len(rows),
        current_periods=aggregate_periods(target_sum, tz_name),
        proposed_periods=aggregate_periods(proposed_sum, tz_name),
        warnings=warnings,
        source_outliers=source_outliers,
        source_removed=round(source_removed, 3),
        raw_reference_delta=round(raw_delta, 3),
        outlier_periods=sorted({period_label(ts, tz_name) for ts, _delta, _rate in outliers}),
    )


BACKUP_FORMAT = 2  # 1 = range snapshot (pre-0.7), 2 = full history + metadata + checksum
BACKUP_SUFFIX = ".json.gz"  # gzip: a 2.5-year snapshot shrinks from 1.07 MB to 0.16 MB


def _write_backup_file(path: Path, payload: dict) -> None:
    """Write a snapshot, gzip-compressed and without pretty-printing."""
    blob = json.dumps(payload, separators=(",", ":")).encode()
    if path.suffix == ".gz":
        path.write_bytes(gzip.compress(blob, 6))
    else:
        path.write_bytes(blob)


def _read_backup_file(path: Path) -> dict:
    """Read a snapshot, transparently handling gzip and the older plain JSON files."""
    blob = path.read_bytes()
    if blob[:2] == b"\x1f\x8b":  # gzip magic
        blob = gzip.decompress(blob)
    return json.loads(blob.decode("utf-8"))


def _checksum(rows: list) -> str:
    """Stable digest of the stored points, so a damaged file is caught before writing."""
    payload = json.dumps(rows, separators=(",", ":"), sort_keys=True).encode()
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _summarise(rows: list) -> dict:
    sums = [row[2] for row in rows if row[2] is not None]
    return {
        "points": len(rows),
        "first_ts": rows[0][0] if rows else None,
        "last_ts": rows[-1][0] if rows else None,
        "first_sum": sums[0] if sums else None,
        "last_sum": sums[-1] if sums else None,
    }


async def backup(
    hass: HomeAssistant,
    statistic_id: str,
    backup_dir: Path,
    unit: str = "",
    label: str = "backup",
) -> Path:
    """Write a timestamped **full** snapshot of a counter's statistics. Reads only.

    Deliberately not limited to a range: the recorder can only delete a whole
    ``statistic_id``, so an exact rollback has to clear and re-import everything. A range
    snapshot would leave behind whatever a repair wrote outside it — which is exactly the
    case when a repair extends the history backwards.

    Repeatable; every snapshot is uniquely timestamped, so the snapshots of one counter form
    the list of states you can jump back to. ``label`` marks automatic ones (``pre-fix``,
    ``pre-restore``).
    """
    rows = await read_full_history(hass, statistic_id)
    metadata = await read_metadata(hass, statistic_id) or {
        "has_mean": False, "has_sum": True, "name": None, "source": "recorder",
        "statistic_id": statistic_id, "unit_of_measurement": unit or None,
    }
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt_util.utcnow().strftime("%Y%m%d_%H%M%S")
    path = backup_dir / f"{statistic_id}.{stamp}.{label}{BACKUP_SUFFIX}"
    await hass.async_add_executor_job(
        _write_backup_file,
        path,
        {
            "format": BACKUP_FORMAT,
            "statistic_id": statistic_id,
            "created_utc": dt_util.utcnow().isoformat(),
            "created_by": f"{DOMAIN} (label: {label})",
            "unit_of_measurement": metadata.get("unit_of_measurement") or unit,
            "metadata": metadata,
            "summary": _summarise(rows),
            "checksum": _checksum(rows),
            "rows": rows,
        },
    )
    _LOGGER.info(
        "statistics_toolset: full backup of %s (%d points) -> %s", statistic_id, len(rows), path
    )
    return path


def list_backups(backup_dir: Path, statistic_id: str = "") -> list[dict]:
    """Return the available snapshots, newest first. Reads only, never touches the database.

    This is what makes "jump back to any earlier state" usable: without a list you would
    have to know the file name.
    """
    if not backup_dir.is_dir():
        return []
    entries: list[dict] = []
    candidates = sorted(backup_dir.glob("*.json")) + sorted(backup_dir.glob("*.json.gz"))
    for path in candidates:
        try:
            data = _read_backup_file(path)
        except (OSError, ValueError, gzip.BadGzipFile) as err:  # unreadable or truncated
            entries.append({"file": path.name, "error": str(err)[:120]})
            continue
        if statistic_id and data.get("statistic_id") != statistic_id:
            continue
        summary = data.get("summary") or _summarise(data.get("rows") or [])
        entries.append({
            "file": path.name,
            "statistic_id": data.get("statistic_id"),
            "created_utc": data.get("created_utc"),
            "label": (data.get("created_by") or "").split("label: ")[-1].rstrip(")") or None,
            "format": data.get("format", 1),
            "full_history": data.get("format", 1) >= 2,
            "points": summary.get("points"),
            "first": dt_util.utc_from_timestamp(summary["first_ts"]).isoformat()
            if summary.get("first_ts") else None,
            "last": dt_util.utc_from_timestamp(summary["last_ts"]).isoformat()
            if summary.get("last_ts") else None,
            "end_sum": summary.get("last_sum"),
            "size_bytes": path.stat().st_size,
        })
    entries.sort(key=lambda item: item.get("created_utc") or "", reverse=True)
    return entries


async def restore(hass: HomeAssistant, backup_file: Path, backup_dir: Path | None = None) -> dict:
    """Put a counter back to the state a snapshot holds. WRITES (gated by the write locks).

    Order matters, and every step exists for a reason:

    1. validate the file — checksum, statistic_id, metadata — *before* touching anything
    2. snapshot the current state as ``pre-restore``, so the jump back can itself be undone
    3. clear the counter's statistics (only this one id)
    4. re-import the snapshot, with the metadata it carries
    5. verify point count and end sum against the file; mismatch raises and names the
       ``pre-restore`` file

    A pre-0.7 snapshot only covers a range. Clearing on that basis would delete history the
    file cannot restore, so those are imported *without* clearing and reported as partial.
    """
    path = Path(backup_file)
    data = await hass.async_add_executor_job(_read_backup_file, path)
    statistic_id = data.get("statistic_id")
    unit = data.get("unit_of_measurement")
    if not statistic_id or not unit:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="backup_incomplete",
            translation_placeholders={"file": path.name},
        )

    raw_rows = data.get("rows") or []
    stored = data.get("checksum")
    if stored and stored != _checksum(raw_rows):
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="backup_corrupt",
            translation_placeholders={"file": path.name},
        )

    rows = [
        (float(ts), float(state), float(summed))
        for ts, state, summed in raw_rows
        if state is not None and summed is not None
    ]
    if not rows:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="backup_no_rows",
            translation_placeholders={"file": path.name},
        )

    full_history = data.get("format", 1) >= BACKUP_FORMAT
    safety_net: Path | None = None
    if backup_dir is not None:
        safety_net = await backup(hass, statistic_id, backup_dir, unit, label="pre-restore")

    if full_history:
        await clear_statistic(hass, statistic_id)  # only this id, nothing else
    else:
        _LOGGER.warning(
            "statistics_toolset: %s is a pre-0.7 range snapshot — importing without clearing, "
            "so points outside its range stay as they are",
            path.name,
        )

    await write_statistics(hass, statistic_id, unit, rows, data.get("metadata"))

    verified = await _verify_restore(hass, statistic_id, rows, full_history)
    if not verified["matches"]:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="restore_verification_failed",
            translation_placeholders={
                "statistic_id": statistic_id,
                "expected": str(len(rows)),
                "actual": str(verified["points"]),
                "safety_net": safety_net.name if safety_net else "-",
            },
        )
    _LOGGER.warning(
        "statistics_toolset: restored %s from %s (%d points, full_history=%s)",
        statistic_id, path.name, len(rows), full_history,
    )
    return {
        "statistic_id": statistic_id,
        "restored_points": len(rows),
        "full_history": full_history,
        "verified": verified["matches"],
        "backup_file": str(path),
        "safety_net": str(safety_net) if safety_net else None,
    }


async def transfer(
    hass: HomeAssistant, from_statistic_id: str, to_statistic_id: str, backup_dir: Path
) -> dict:
    """Move a counter's whole statistics history to a different statistic_id. WRITES.

    The common trigger: an entity gets renamed. Home Assistant keys long-term statistics by
    statistic_id, so a rename leaves the old id's history orphaned (still in the database,
    but attached to nothing) while the new id starts from zero — the numbers look lost even
    though they still exist. This copies the old history under the new id and clears the old
    one, so afterwards there is exactly one place the numbers live, not two.

    Refuses if the target already has any statistics — a straight move only, deliberately
    with no merge logic that would have to guess how to reconcile overlapping timestamps.
    """
    # Checked upfront, before any read/write: clearing the source only happens at the very
    # end, but writing the target happens well before that — without this, a from_id outside
    # the allowlist would only fail *after* the target had already received the data, leaving
    # both ids holding a copy instead of refusing cleanly with nothing changed.
    assert_writable(hass, from_statistic_id)
    assert_writable(hass, to_statistic_id)

    rows = await read_full_history(hass, from_statistic_id)
    if not rows:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="transfer_source_empty",
            translation_placeholders={"statistic_id": from_statistic_id},
        )
    if await read_full_history(hass, to_statistic_id):
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="transfer_target_not_empty",
            translation_placeholders={"statistic_id": to_statistic_id},
        )

    metadata = await read_metadata(hass, from_statistic_id)
    unit = (metadata or {}).get("unit_of_measurement") or ""
    safety_net = await backup(hass, from_statistic_id, backup_dir, unit, label="pre-transfer")

    await write_statistics(hass, to_statistic_id, unit, rows, metadata)
    verified = await _verify_restore(hass, to_statistic_id, rows, full_history=True)
    if not verified["matches"]:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="transfer_verification_failed",
            translation_placeholders={
                "statistic_id": to_statistic_id,
                "expected": str(len(rows)),
                "actual": str(verified["points"]),
                "safety_net": safety_net.name,
            },
        )

    await clear_statistic(hass, from_statistic_id)
    _LOGGER.warning(
        "statistics_toolset: transferred %d points from %s to %s",
        len(rows), from_statistic_id, to_statistic_id,
    )
    return {
        "from_statistic_id": from_statistic_id,
        "to_statistic_id": to_statistic_id,
        "transferred_points": len(rows),
        "verified": verified["matches"],
        "safety_net": str(safety_net),
    }


def _assert_restorable(path: Path, statistic_id: str) -> None:
    """Refuse to continue unless this snapshot could actually restore the counter.

    Checked before any write: the file exists, is readable, belongs to this counter, holds
    points, and its checksum still matches.
    """
    problem = ""
    try:
        data = _read_backup_file(path)
    except (OSError, ValueError, gzip.BadGzipFile) as err:
        problem = f"unreadable ({type(err).__name__})"
    else:
        rows = data.get("rows") or []
        if data.get("statistic_id") != statistic_id:
            problem = f"belongs to {data.get('statistic_id')}"
        elif not rows:
            problem = "contains no points"
        elif data.get("checksum") and data["checksum"] != _checksum(rows):
            problem = "checksum mismatch"
    if problem:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="backup_not_usable",
            translation_placeholders={"file": path.name, "problem": problem},
        )


def _compare_restore(written: list, rows: list, full_history: bool, expected_end: float) -> dict:
    """Pure comparison, no I/O — split out so :func:`_verify_restore` can retry cheaply."""
    if full_history:
        # The series must now be exactly the snapshot: same number of points, same end sum.
        end_sums = [row[2] for row in written if row[2] is not None]
        actual_end = end_sums[-1] if end_sums else None
        matches = (
            len(written) == len(rows)
            and actual_end is not None
            and abs(actual_end - expected_end) <= PLAUSI_TOLERANCE
        )
    else:
        # A partial snapshot only claims its own timestamps; the rest of the series stays and
        # legitimately carries a different end sum. So compare where the snapshot applies.
        by_ts = {row[0]: row[2] for row in written}
        actual_end = by_ts.get(rows[-1][0])
        matches = len(written) >= len(rows) and all(
            ts in by_ts
            and by_ts[ts] is not None
            and abs(by_ts[ts] - total) <= PLAUSI_TOLERANCE
            for ts, _state, total in rows
        )
    return {
        "matches": bool(matches),
        "points": len(written),
        "end_sum": actual_end,
        "expected_end_sum": expected_end,
    }


async def _verify_restore(
    hass: HomeAssistant, statistic_id: str, rows: list, full_history: bool
) -> dict:
    """Read the series back and compare it with what was written, retrying briefly.

    ``write_statistics`` already awaits ``async_block_till_done`` — the recorder's task
    queue has drained — but that is not the same as the write being durably committed and
    visible to a fresh read: commits run on their own cycle, separate from task processing.
    Verified live: a restore reported 0 points immediately afterwards, while a manual read
    moments later showed the full, correctly restored series. The same lesson already
    applied in ``scripts/make_test_sensors.py`` — recorder writes are eventually consistent,
    not immediately visible — applies here too, so this polls with a short bounded backoff
    instead of trusting a single read.
    """
    expected_end = rows[-1][2]
    result = {"matches": False, "points": 0, "end_sum": None, "expected_end_sum": expected_end}
    delay = _VISIBILITY_RETRY_START_DELAY
    for _attempt in range(_VISIBILITY_RETRY_ATTEMPTS):
        written = await read_full_history(hass, statistic_id)
        result = _compare_restore(written, rows, full_history, expected_end)
        if result["matches"]:
            return result
        await asyncio.sleep(delay)
        delay = min(delay * 1.5, _VISIBILITY_RETRY_MAX_DELAY)
    return result


async def fix(
    hass: HomeAssistant,
    statistic_id: str,
    reference_id: str,
    cycle: str,
    start: datetime,
    end: datetime,
    unit: str,
    backup_dir: Path,
    max_rate: float = 0.0,
) -> Preview:
    """Back up, rebuild and write the corrected series. WRITES (gated by READ_ONLY_MODE)."""
    preview = await simulate(hass, statistic_id, reference_id, cycle, start, end, unit, max_rate)

    # No write without a verified snapshot. Not "a backup was attempted" — the file is read
    # back and its checksum re-computed, because a snapshot that turns out to be unreadable
    # afterwards is worth nothing. The whole history is captured, since a repair may extend
    # the series beyond the repaired range and only a full snapshot can undo that exactly.
    snapshot = await backup(hass, statistic_id, backup_dir, unit, label="pre-fix")
    await hass.async_add_executor_job(_assert_restorable, snapshot, statistic_id)

    ref_source = reference_id or statistic_id
    raw_ref = [
        (ts, s)
        for ts, _st, s in await read_statistics(hass, ref_source, start, end)
        if s is not None
    ]
    # Same clamping as in simulate — the written series must match the previewed one.
    null_ts, end_ts, _warnings = _clamped_start(raw_ref, start, end)
    if max_rate <= 0:
        max_rate = estimate_max_rate(raw_ref)
    reference = await hass.async_add_executor_job(
        build_reference, raw_ref, max_rate, DEFAULT_MEDIAN_RATE
    )
    rows = await hass.async_add_executor_job(
        derive_series, reference, cycle, str(dt_util.DEFAULT_TIME_ZONE), null_ts, end_ts, null_ts
    )
    plausibility_check(rows, reference, end_ts, null_ts, PLAUSI_TOLERANCE)

    await write_statistics(hass, statistic_id, unit, rows)  # blocked in read-only mode
    _LOGGER.warning(
        "statistics_toolset: rewrote %d points for %s (end sum %.1f)",
        len(rows),
        statistic_id,
        rows[-1][2] if rows else 0.0,
    )
    return preview
