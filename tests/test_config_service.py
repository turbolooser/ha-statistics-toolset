"""Exercises the panel-configurable write locks end to end, without Home Assistant.

This is the part that would have caught the ``WRITE_ALLOWLIST`` NameError before it reached
a real instance (``__init__.py`` is actually imported here, unlike the other test modules),
and it verifies the behaviour the "configure without leaving the dashboard" feature depends
on: a config entry is created on first use, ``set_config`` persists to it, and the effective
locks update *immediately* rather than racing the background reload that
``async_update_entry`` schedules.
"""

from __future__ import annotations

import asyncio

import pytest

from statistics_toolset_stub import FakeRecorder, load_init

DOMAIN = "statistics_toolset"


@pytest.fixture
def loaded():
    """(init module, recorder_io module, fake recorder) sharing one fake Home Assistant."""
    fake = FakeRecorder()
    init_module, io, _coordinator = load_init(fake)
    return init_module, io, fake


def test_async_setup_defaults_to_read_only_with_no_config(loaded) -> None:
    init_module, io, fake = loaded
    asyncio.run(init_module.async_setup(fake.hass, {}))
    read_only, allowlist = io.write_locks(fake.hass)
    assert read_only is True  # the safe default, matching const.READ_ONLY_MODE
    assert allowlist == ()
    assert fake.hass.data[DOMAIN]["configured_via"] == "defaults"


def test_yaml_config_is_picked_up(loaded) -> None:
    init_module, io, fake = loaded
    config = {DOMAIN: {"read_only": False, "write_allowlist": ["sensor.test_a"]}}
    asyncio.run(init_module.async_setup(fake.hass, config))
    read_only, allowlist = io.write_locks(fake.hass)
    assert (read_only, allowlist) == (False, ("sensor.test_a",))
    assert fake.hass.data[DOMAIN]["configured_via"] == "yaml"


def test_set_config_creates_an_entry_and_takes_effect_immediately(loaded) -> None:
    """The core promise: no detour through Settings, and no race with the reload."""
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        assert fake.hass.config_entries.async_entries(DOMAIN) == []  # nothing yet

        result = await fake.hass.services.async_call(
            DOMAIN, "set_config",
            {"read_only": False, "write_allowlist": ["sensor.stat_toolset_test_clean"]},
        )
        assert result == {
            "read_only": False,
            "write_allowlist": ["sensor.stat_toolset_test_clean"],
            "admin_only": True,  # not sent, so it stays at the safe default
        }

        # Effective immediately — not waiting on the reload task scheduled in the background.
        read_only, allowlist = io.write_locks(fake.hass)
        assert (read_only, allowlist) == (False, ("sensor.stat_toolset_test_clean",))

        # A config entry now exists and carries the same options (this is what persists
        # across a restart — YAML never gets written back to).
        entries = fake.hass.config_entries.async_entries(DOMAIN)
        assert len(entries) == 1
        assert entries[0].options["read_only"] is False
        assert entries[0].options["write_allowlist"] == ["sensor.stat_toolset_test_clean"]

        # Let the background reload (scheduled by async_update_entry) actually run; the
        # result must be identical, not just "eventually consistent with a different value".
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        read_only, allowlist = io.write_locks(fake.hass)
        assert (read_only, allowlist) == (False, ("sensor.stat_toolset_test_clean",))

    asyncio.run(scenario())


def test_set_config_only_changes_the_fields_it_receives(loaded) -> None:
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        await fake.hass.services.async_call(
            DOMAIN, "set_config",
            {"read_only": False, "write_allowlist": ["sensor.a", "sensor.b"]},
        )
        # Flip only read_only; the allowlist must survive untouched.
        await fake.hass.services.async_call(DOMAIN, "set_config", {"read_only": True})
        read_only, allowlist = io.write_locks(fake.hass)
        assert read_only is True
        assert allowlist == ("sensor.a", "sensor.b")

    asyncio.run(scenario())


def test_set_config_reuses_the_existing_entry(loaded) -> None:
    """A second call must not create a second config entry."""
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        await fake.hass.services.async_call(DOMAIN, "set_config", {"read_only": False})
        await fake.hass.services.async_call(DOMAIN, "set_config", {"read_only": True})
        assert len(fake.hass.config_entries.async_entries(DOMAIN)) == 1

    asyncio.run(scenario())


def test_status_reports_the_effective_locks(loaded) -> None:
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        await fake.hass.services.async_call(
            DOMAIN, "set_config", {"read_only": False, "write_allowlist": ["sensor.x"]},
        )
        status = await fake.hass.services.async_call(DOMAIN, "status", {})
        assert status["read_only"] is False
        assert status["write_allowlist"] == ["sensor.x"]
        assert status["configured_via"] == "ui"
        assert "backup_dir" in status and "backup_count" in status

    asyncio.run(scenario())


def test_ui_options_take_precedence_over_yaml(loaded) -> None:
    """A config entry created via the panel must win over a stale YAML setting."""
    init_module, io, fake = loaded

    async def scenario():
        config = {DOMAIN: {"read_only": True, "write_allowlist": ["sensor.from_yaml"]}}
        await init_module.async_setup(fake.hass, config)
        await fake.hass.services.async_call(
            DOMAIN, "set_config", {"read_only": False, "write_allowlist": ["sensor.from_ui"]},
        )
        read_only, allowlist = io.write_locks(fake.hass)
        assert (read_only, allowlist) == (False, ("sensor.from_ui",))

    asyncio.run(scenario())


def test_unload_entry_falls_back_to_safe_defaults(loaded) -> None:
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        await fake.hass.services.async_call(DOMAIN, "set_config", {"read_only": False})
        assert io.write_locks(fake.hass)[0] is False

        entry = fake.hass.config_entries.async_entries(DOMAIN)[0]
        await init_module.async_unload_entry(fake.hass, entry)
        assert io.write_locks(fake.hass) == (True, ())

    asyncio.run(scenario())


def test_panel_defaults_to_admin_only(loaded) -> None:
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        assert fake.hass.panels.panels[DOMAIN] is True

    asyncio.run(scenario())


def test_set_config_can_open_the_panel_to_every_user(loaded) -> None:
    """The user's explicit request: a dashboard-visible switch, no HA restart needed."""
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        assert fake.hass.panels.panels[DOMAIN] is True  # still admin-only at startup

        result = await fake.hass.services.async_call(
            DOMAIN, "set_config", {"admin_only": False},
        )
        assert result["admin_only"] is False
        # Re-registered immediately, not just persisted to the config entry.
        assert fake.hass.panels.panels[DOMAIN] is False

        entry = fake.hass.config_entries.async_entries(DOMAIN)[0]
        assert entry.options["admin_only"] is False

    asyncio.run(scenario())


def test_unload_entry_falls_back_to_admin_only_panel(loaded) -> None:
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        await fake.hass.services.async_call(DOMAIN, "set_config", {"admin_only": False})
        assert fake.hass.panels.panels[DOMAIN] is False

        entry = fake.hass.config_entries.async_entries(DOMAIN)[0]
        await init_module.async_unload_entry(fake.hass, entry)
        assert fake.hass.panels.panels[DOMAIN] is True

    asyncio.run(scenario())


def test_set_config_can_clear_the_allowlist_with_an_empty_list(loaded) -> None:
    """Sending an empty list must remove the restriction, distinct from omitting the field."""
    init_module, io, fake = loaded

    async def scenario():
        await init_module.async_setup(fake.hass, {})
        await fake.hass.services.async_call(
            DOMAIN, "set_config", {"write_allowlist": ["sensor.a"]},
        )
        assert io.write_locks(fake.hass)[1] == ("sensor.a",)

        await fake.hass.services.async_call(DOMAIN, "set_config", {"write_allowlist": []})
        assert io.write_locks(fake.hass)[1] == ()

    asyncio.run(scenario())
