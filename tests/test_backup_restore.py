"""Backup/restore scenarios against a stubbed recorder.

The point of the feature: after a repair you must be able to jump back to any earlier
snapshot of *that one counter*, without touching anything else. These tests cover the cases
that decide whether that actually holds — especially a repair that extended the history,
where a range-limited snapshot would leave data behind.

Home Assistant is not installed here, so ``conftest`` stubs the modules the integration
imports and a small fake recorder stands in for the database.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from statistics_toolset_stub import FakeRecorder, load_coordinator, load_recorder_io

HOUR = 3600.0
# The stub's clock says 2026, and read_full_history only looks back to 2015 — test data has
# to sit inside that window, like real statistics do.
BASE_2024 = 1_704_067_200.0  # 2024-01-01 00:00 UTC
BASE_2025 = 1_735_689_600.0  # 2025-01-01 00:00 UTC


@pytest.fixture
def recorder(tmp_path: Path):
    """A fake recorder plus the integration modules wired to it."""
    fake = FakeRecorder()
    io = load_recorder_io(fake)
    coordinator = load_coordinator(fake, io)
    return fake, io, coordinator, tmp_path


def series(start: float, count: int, step: float = 1.0) -> list[tuple[float, float, float]]:
    return [(start + i * HOUR, i * step, i * step) for i in range(count)]


def run(awaitable):
    return asyncio.run(awaitable)


def test_backup_covers_full_history_not_a_range(recorder) -> None:
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 100))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    data = coordinator._read_backup_file(path)
    assert data["format"] == 2
    assert data["summary"]["points"] == 100, "a snapshot must hold everything"
    assert data["metadata"]["unit_of_measurement"] == "kWh"
    assert data["checksum"].startswith("sha256:")


def test_restore_after_a_repair_that_extended_history(recorder) -> None:
    """The case a range snapshot cannot fix: the repair wrote *earlier* points as well."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 24))  # counter starts in 2025
    snapshot = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))

    # A repair extends the history backwards into 2024 and rewrites everything.
    fake.set_history("sensor.test", series(BASE_2024, 500))
    assert len(fake.history["sensor.test"]) == 500

    result = run(coordinator.restore(fake.hass, snapshot, tmp))
    assert result["full_history"] is True
    assert result["restored_points"] == 24
    assert len(fake.history["sensor.test"]) == 24, "the extra 476 points must be gone"
    assert fake.cleared == ["sensor.test"], "exactly one id may be cleared"


def test_restore_never_touches_other_counters(recorder) -> None:
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.target", series(BASE_2025, 10))
    fake.set_history("sensor.other", series(BASE_2025, 42))
    snapshot = run(coordinator.backup(fake.hass, "sensor.target", tmp, "kWh"))
    fake.set_history("sensor.target", series(BASE_2025, 99))

    run(coordinator.restore(fake.hass, snapshot, tmp))
    assert len(fake.history["sensor.other"]) == 42, "an unrelated counter changed"
    assert fake.cleared == ["sensor.target"]


def test_restore_writes_a_pre_restore_snapshot_first(recorder) -> None:
    """The jump back must itself be undoable."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 10))
    old = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    fake.set_history("sensor.test", series(BASE_2025, 50))  # state we might want back

    result = run(coordinator.restore(fake.hass, old, tmp))
    safety = Path(result["safety_net"])
    assert safety.exists() and "pre-restore" in safety.name
    assert coordinator._read_backup_file(safety)["summary"]["points"] == 50

    # ... and that snapshot restores the 50-point state again.
    run(coordinator.restore(fake.hass, safety, tmp))
    assert len(fake.history["sensor.test"]) == 50


def test_corrupt_backup_is_refused_before_anything_is_cleared(recorder) -> None:
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 20))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    data = coordinator._read_backup_file(path)
    data["rows"][5][2] = 999_999.0  # tamper with a value, leave the checksum
    coordinator._write_backup_file(path, data)

    with pytest.raises(Exception, match="backup_corrupt"):
        run(coordinator.restore(fake.hass, path, tmp))
    assert fake.cleared == [], "nothing may be cleared when the file is not trustworthy"
    assert len(fake.history["sensor.test"]) == 20, "data must be untouched"


def test_pre_070_range_snapshot_is_imported_without_clearing(recorder) -> None:
    """Old snapshots only cover a range — clearing on that basis would lose history."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 100))
    legacy = tmp / "sensor.test.20260101_000000.backup.json"
    legacy.write_text(json.dumps({
        "statistic_id": "sensor.test",
        "unit_of_measurement": "kWh",
        "created_utc": "2026-01-01T00:00:00+00:00",
        "rows": [[ts, state, total] for ts, state, total in series(BASE_2025, 10)],
    }), encoding="utf-8")

    result = run(coordinator.restore(fake.hass, legacy, tmp))
    assert result["full_history"] is False
    assert fake.cleared == [], "a partial snapshot must not clear the series"
    assert len(fake.history["sensor.test"]) == 100, "the rest of the history stays"


def test_verification_catches_a_failed_import(recorder) -> None:
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 30))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    fake.drop_writes = True  # simulate an import that silently does nothing

    with pytest.raises(Exception, match="restore_verification_failed"):
        run(coordinator.restore(fake.hass, path, tmp))


def test_verification_retries_through_a_commit_visibility_delay(recorder) -> None:
    """Live bug: async_block_till_done() drains the recorder's task queue, but a read-back
    inside the same service call could still see 0 rows before the commit became visible —
    while a manual read moments later showed the data was actually there. Simulate that lag
    and confirm the retry loop rides it out instead of raising restore_verification_failed."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 30))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    fake.set_history("sensor.test", series(BASE_2025, 5))  # state we're restoring away from

    fake.visibility_lag = 3  # first 3 reads after the import still see the old/empty state
    result = run(coordinator.restore(fake.hass, path, tmp))
    assert result["verified"] is True
    assert result["restored_points"] == 30
    assert len(fake.history["sensor.test"]) == 30


def test_simulate_retries_through_a_commit_visibility_delay_after_restore(recorder) -> None:
    """Live bug: restoring a counter and immediately reading it back (as the guided workflow
    does when a user restores, then switches straight to the Read step) could hit the same
    commit-visibility race as restore's own verification — simulate()'s initial read saw 0
    rows and raised source_no_statistics, even though the data was there moments later."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 30))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    fake.set_history("sensor.test", series(BASE_2025, 5))

    run(coordinator.restore(fake.hass, path, tmp))

    start = datetime.fromtimestamp(BASE_2025, tz=timezone.utc)
    end = datetime.fromtimestamp(BASE_2025 + 29 * HOUR, tz=timezone.utc)
    # restore()'s own retries already rode out its lag budget; simulate the lag still being
    # in effect for the *next* read, exactly like the live bug (guided workflow reads right
    # after restore returns, before the commit is actually visible).
    fake._lag_remaining["sensor.test"] = 3
    preview = run(
        coordinator.simulate(
            fake.hass, "sensor.test", "", "monthly", start, end, "kWh", max_rate=0.0
        )
    )
    assert preview.current_end_sum != 0.0


def test_verification_gives_up_after_the_retry_budget(recorder) -> None:
    """A lag that never clears is indistinguishable from a genuinely failed import — the
    retry loop must still raise, not hang or silently succeed."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 30))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    fake.drop_writes = True

    with pytest.raises(Exception, match="restore_verification_failed"):
        run(coordinator.restore(fake.hass, path, tmp))


def test_list_backups_orders_and_labels_snapshots(recorder) -> None:
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.a", series(BASE_2025, 10))
    fake.set_history("sensor.b", series(BASE_2025, 20))
    fake.clock = "20260101_100000"
    run(coordinator.backup(fake.hass, "sensor.a", tmp, "kWh"))
    fake.clock = "20260101_120000"
    run(coordinator.backup(fake.hass, "sensor.a", tmp, "kWh", label="pre-fix"))
    run(coordinator.backup(fake.hass, "sensor.b", tmp, "kWh"))

    all_entries = coordinator.list_backups(tmp)
    assert len(all_entries) == 3
    only_a = coordinator.list_backups(tmp, "sensor.a")
    assert len(only_a) == 2
    assert {entry["statistic_id"] for entry in only_a} == {"sensor.a"}
    assert only_a[0]["created_utc"] >= only_a[1]["created_utc"], "newest first"
    assert {entry["label"] for entry in only_a} == {"backup", "pre-fix"}
    assert all(entry["full_history"] for entry in only_a)
    assert only_a[0]["points"] == 10


def test_write_allowlist_blocks_every_other_counter(recorder) -> None:
    """The second lock: with an allowlist set, nothing else can be written or cleared."""
    fake, io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 10))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))

    io.WRITE_ALLOWLIST = ("sensor.playground",)
    with pytest.raises(Exception, match="not_in_allowlist"):
        run(coordinator.restore(fake.hass, path, tmp))
    assert fake.cleared == [], "a blocked id must not be cleared either"

    io.WRITE_ALLOWLIST = ("sensor.test",)
    result = run(coordinator.restore(fake.hass, path, tmp))
    assert result["restored_points"] == 10


def test_read_only_mode_blocks_restore(recorder) -> None:
    fake, io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 10))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    io.READ_ONLY_MODE = True
    with pytest.raises(Exception, match="read_only_mode"):
        run(coordinator.restore(fake.hass, path, tmp))
    assert fake.cleared == []


def test_backup_still_works_in_read_only_mode(recorder) -> None:
    """Snapshots must always be possible — they are the safety net, not a write."""
    fake, io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 10))
    io.READ_ONLY_MODE = True
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    assert path.exists()


def test_fix_refuses_to_write_without_a_usable_snapshot(recorder) -> None:
    """Your rule: no write unless a snapshot exists that could actually restore it."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 20))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))

    # intact snapshot -> accepted
    coordinator._assert_restorable(path, "sensor.test")

    # damaged, wrong counter, empty: each must be refused
    data = coordinator._read_backup_file(path)
    broken = tmp / "broken.json.gz"
    coordinator._write_backup_file(broken, {**data, "rows": [], "checksum": data["checksum"]})
    with pytest.raises(Exception, match="backup_not_usable"):
        coordinator._assert_restorable(broken, "sensor.test")

    with pytest.raises(Exception, match="backup_not_usable"):
        coordinator._assert_restorable(path, "sensor.other")

    tampered = tmp / "tampered.json.gz"
    rows = [list(row) for row in data["rows"]]
    rows[3][2] = 12345.0
    coordinator._write_backup_file(tampered, {**data, "rows": rows})
    with pytest.raises(Exception, match="backup_not_usable"):
        coordinator._assert_restorable(tampered, "sensor.test")

    with pytest.raises(Exception, match="backup_not_usable"):
        coordinator._assert_restorable(tmp / "does-not-exist.json.gz", "sensor.test")


def test_backup_is_gzipped_and_smaller(recorder) -> None:
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 2000))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))
    assert path.name.endswith(".json.gz")
    assert path.read_bytes()[:2] == b"\x1f\x8b", "not gzip-compressed"
    raw = json.dumps(coordinator._read_backup_file(path), separators=(",", ":"))
    assert path.stat().st_size < len(raw) / 2, "compression should more than halve it"


def test_write_locks_come_from_yaml_config(recorder) -> None:
    """The locks are read at call time from hass.data, so YAML wins over the constants."""
    fake, io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 10))
    path = run(coordinator.backup(fake.hass, "sensor.test", tmp, "kWh"))

    # YAML says read-only, even though the constant was switched off for the tests
    fake.hass.data["statistics_toolset"] = {"read_only": True, "write_allowlist": ()}
    with pytest.raises(Exception, match="read_only_mode"):
        run(coordinator.restore(fake.hass, path, tmp))

    # YAML allows writing, but only for another counter
    fake.hass.data["statistics_toolset"] = {
        "read_only": False, "write_allowlist": ("sensor.playground",),
    }
    with pytest.raises(Exception, match="not_in_allowlist"):
        run(coordinator.restore(fake.hass, path, tmp))
    assert fake.cleared == []

    # YAML allows exactly this counter
    fake.hass.data["statistics_toolset"] = {
        "read_only": False, "write_allowlist": ("sensor.test",),
    }
    assert run(coordinator.restore(fake.hass, path, tmp))["restored_points"] == 10


def test_missing_yaml_config_falls_back_to_the_safe_constants(recorder) -> None:
    fake, io, coordinator, tmp = recorder
    fake.set_history("sensor.test", series(BASE_2025, 5))
    fake.hass.data.pop("statistics_toolset", None)
    io.READ_ONLY_MODE = True  # the shipped default
    read_only, allowlist = io.write_locks(fake.hass)
    assert read_only is True and allowlist == ()
