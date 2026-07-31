"""Covers `transfer`: moving a counter's whole history onto a different statistic_id.

The scenario this exists for: an entity gets renamed, so its long-term statistics are still
in the database but orphaned under the old statistic_id, while the new id starts at zero.
`transfer` copies the old history onto the new id and clears the old one — a straight move,
never a merge, so these tests focus on: it actually moves the data, it clears the source
afterwards, it refuses onto a non-empty target, and it respects the same write locks and
verification-retry machinery as `restore`.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from statistics_toolset_stub import FakeRecorder, load_coordinator, load_recorder_io

HOUR = 3600.0
BASE_2025 = 1_735_689_600.0  # 2025-01-01 00:00 UTC


@pytest.fixture
def recorder(tmp_path: Path):
    fake = FakeRecorder()
    io = load_recorder_io(fake)
    coordinator = load_coordinator(fake, io)
    return fake, io, coordinator, tmp_path


def series(start: float, count: int, step: float = 1.0) -> list[tuple[float, float, float]]:
    return [(start + i * HOUR, i * step, i * step) for i in range(count)]


def run(awaitable):
    return asyncio.run(awaitable)


def test_transfer_moves_the_whole_history_and_clears_the_source(recorder) -> None:
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.old_name_energy", series(BASE_2025, 50))

    result = run(coordinator.transfer(fake.hass, "sensor.old_name_energy", "sensor.new_name_energy", tmp))

    assert result["transferred_points"] == 50
    assert result["verified"] is True
    assert len(fake.history["sensor.new_name_energy"]) == 50
    assert "sensor.old_name_energy" not in fake.history, "the source must be cleared, not duplicated"
    assert fake.cleared == ["sensor.old_name_energy"]


def test_transfer_writes_a_safety_net_of_the_source_first(recorder) -> None:
    """The source is about to be cleared — its state must be recoverable via restore."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.old_name_energy", series(BASE_2025, 20))

    result = run(coordinator.transfer(fake.hass, "sensor.old_name_energy", "sensor.new_name_energy", tmp))

    safety = Path(result["safety_net"])
    assert safety.exists() and "pre-transfer" in safety.name
    data = coordinator._read_backup_file(safety)
    assert data["statistic_id"] == "sensor.old_name_energy"
    assert data["summary"]["points"] == 20


def test_transfer_refuses_an_empty_source(recorder) -> None:
    fake, _io, coordinator, tmp = recorder
    with pytest.raises(Exception, match="transfer_source_empty"):
        run(coordinator.transfer(fake.hass, "sensor.nothing_here", "sensor.new_name_energy", tmp))
    assert fake.cleared == []


def test_transfer_refuses_onto_a_target_that_already_has_data(recorder) -> None:
    """A move, never a merge — no logic exists to reconcile overlapping timestamps."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.old_name_energy", series(BASE_2025, 30))
    fake.set_history("sensor.new_name_energy", series(BASE_2025, 5))

    with pytest.raises(Exception, match="transfer_target_not_empty"):
        run(coordinator.transfer(fake.hass, "sensor.old_name_energy", "sensor.new_name_energy", tmp))

    assert fake.cleared == [], "nothing may be cleared when the transfer is refused"
    assert len(fake.history["sensor.old_name_energy"]) == 30, "source must be untouched"
    assert len(fake.history["sensor.new_name_energy"]) == 5, "target must be untouched"


def test_transfer_verification_retries_through_a_commit_visibility_delay(recorder) -> None:
    """Same eventually-consistent recorder behaviour restore has to ride out."""
    fake, _io, coordinator, tmp = recorder
    fake.set_history("sensor.old_name_energy", series(BASE_2025, 40))
    fake.visibility_lag = 3

    result = run(coordinator.transfer(fake.hass, "sensor.old_name_energy", "sensor.new_name_energy", tmp))
    assert result["verified"] is True
    assert len(fake.history["sensor.new_name_energy"]) == 40


def test_transfer_respects_the_write_allowlist_for_both_ids(recorder) -> None:
    fake, io, coordinator, tmp = recorder
    io.WRITE_ALLOWLIST = ("sensor.new_name_energy",)  # only the target is allowed
    fake.set_history("sensor.old_name_energy", series(BASE_2025, 10))

    with pytest.raises(Exception, match="not_in_allowlist"):
        run(coordinator.transfer(fake.hass, "sensor.old_name_energy", "sensor.new_name_energy", tmp))
