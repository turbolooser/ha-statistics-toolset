"""A fake recorder, so the backup/restore flows can be tested without Home Assistant.

The integration only reaches the database through :mod:`recorder_io`, which makes this
possible: the stub implements exactly the handful of recorder functions used there, keeps the
statistics in a dict, and records which ids were cleared. That last part is what lets a test
assert "no other counter was touched".
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

INTEGRATION = (
    Path(__file__).resolve().parent.parent / "custom_components" / "statistics_toolset"
)
HOUR = 3600.0


class FakeRecorder:
    """Holds statistics per id and mimics the recorder's behaviour closely enough."""

    def __init__(self) -> None:
        self.history: dict[str, list[tuple[float, float | None, float | None]]] = {}
        self.metadata: dict[str, dict] = {}
        self.cleared: list[str] = []
        self.drop_writes = False  # simulate an import that does nothing
        # Simulates the real recorder's commit-visibility race: a read this many times right
        # after an import still sees the pre-import state, before catching up. Reproduces the
        # live bug where async_block_till_done() drained the task queue but a same-call
        # read-back still saw 0 rows, while a later read saw the correct data.
        self.visibility_lag = 0
        self._lag_remaining: dict[str, int] = {}
        self.clock = "20260101_000000"
        self.hass = types.SimpleNamespace(
            data={},
            states=types.SimpleNamespace(get=lambda _entity_id: None),
            async_add_executor_job=self._run_job,
            # A directory that legitimately does not exist: list_backups() on a missing
            # directory returns [], which is the correct read-only behaviour to test against.
            config=types.SimpleNamespace(
                path=lambda *parts: str(Path("/tmp/statistics_toolset_test_config", *parts))
            ),
            # clear_statistic() bridges instance.async_clear_statistics's on_done callback
            # back to the event loop via this; no real thread hop happens in tests, so
            # calling straight through is a faithful enough stand-in.
            loop=types.SimpleNamespace(call_soon_threadsafe=lambda fn, *a: fn(*a)),
        )

    async def _run_job(self, func, *args):
        return func(*args)

    # recorder_io calls this on the recorder instance as well as on hass.
    async def async_add_executor_job(self, func, *args):
        return func(*args)

    async def async_block_till_done(self) -> None:
        """No-op here: async_import_statistics already applies synchronously in the stub,
        unlike the real recorder where it only queues the write. Present so write_statistics
        can call it unconditionally."""
        return None

    def set_history(self, statistic_id: str, rows: list) -> None:
        self.history[statistic_id] = [tuple(row) for row in rows]
        self.metadata.setdefault(statistic_id, {
            "has_mean": False, "has_sum": True, "name": None, "source": "recorder",
            "statistic_id": statistic_id, "unit_of_measurement": "kWh",
        })

    # --- the recorder API surface recorder_io uses -------------------------------
    def statistics_during_period(self, _hass, start, end, ids, _period, _units, _types):
        statistic_id = next(iter(ids))
        if self._lag_remaining.get(statistic_id, 0) > 0:
            self._lag_remaining[statistic_id] -= 1
            return {statistic_id: []}
        rows = self.history.get(statistic_id, [])
        begin, finish = start.timestamp(), end.timestamp()
        return {
            statistic_id: [
                {"start": ts, "state": state, "sum": total}
                for ts, state, total in rows
                if begin <= ts <= finish
            ]
        }

    def get_metadata(self, _hass, statistic_ids=None, **_kwargs):
        return {
            statistic_id: (1, self.metadata[statistic_id])
            for statistic_id in (statistic_ids or set())
            if statistic_id in self.metadata
        }

    def async_clear_statistics(self, statistic_ids: list[str], *, on_done=None) -> None:
        """Mirrors the real ``Recorder.async_clear_statistics`` — a queued task that calls
        ``on_done`` when finished, not a plain function run via an executor job (that
        mismatch was the actual bug: :func:`recorder_io.clear_statistic` used to run the
        raw ``clear_statistics`` through ``async_add_executor_job``, on a different thread
        than the one its internal assertion checks against)."""
        for statistic_id in statistic_ids:
            self.cleared.append(statistic_id)
            self.history.pop(statistic_id, None)
        if on_done:
            on_done()

    def async_import_statistics(self, _hass, metadata: dict, statistics: list[dict]) -> None:
        if self.drop_writes:
            return
        statistic_id = metadata["statistic_id"]
        if self.visibility_lag:
            self._lag_remaining[statistic_id] = self.visibility_lag
        self.metadata[statistic_id] = dict(metadata)
        existing = {ts: (ts, state, total) for ts, state, total in self.history.get(statistic_id, [])}
        for entry in statistics:
            ts = entry["start"].timestamp()
            existing[ts] = (ts, entry["state"], entry["sum"])
        self.history[statistic_id] = [existing[ts] for ts in sorted(existing)]


def _stub_home_assistant(fake: FakeRecorder) -> None:
    """Install the Home Assistant modules the integration imports."""

    class HomeAssistantError(Exception):
        def __init__(self, *args, translation_key=None, **kwargs):
            # Tests match on the translation key, which is what users would see rendered.
            super().__init__(translation_key or (args[0] if args else ""))
            self.translation_key = translation_key

    def module(name: str, **attributes):
        mod = types.ModuleType(name)
        for key, value in attributes.items():
            setattr(mod, key, value)
        sys.modules[name] = mod
        return mod

    module("homeassistant")
    module("homeassistant.core", HomeAssistant=object)
    module("homeassistant.exceptions", HomeAssistantError=HomeAssistantError)
    registry = types.SimpleNamespace(async_get=lambda _hass: None)
    module("homeassistant.helpers", entity_registry=registry)
    module("homeassistant.helpers.entity_registry", async_get=registry.async_get)
    module("homeassistant.util")
    module(
        "homeassistant.util.dt",
        UTC=timezone.utc,
        utcnow=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
        utc_from_timestamp=lambda ts: datetime.fromtimestamp(ts, timezone.utc),
        DEFAULT_TIME_ZONE="Europe/Berlin",
    )
    module("homeassistant.components")
    module("homeassistant.components.recorder", get_instance=lambda _hass: fake)
    module(
        "homeassistant.components.recorder.statistics",
        # clear_statistics (the raw function) is deliberately not imported by recorder_io.py
        # anymore — see async_clear_statistics above for why.
        async_import_statistics=fake.async_import_statistics,
        get_metadata=fake.get_metadata,
        statistics_during_period=fake.statistics_during_period,
    )


def _load(name: str) -> types.ModuleType:
    package = sys.modules.get("statistics_toolset_pkg")
    if package is None:
        package = types.ModuleType("statistics_toolset_pkg")
        package.__path__ = [str(INTEGRATION)]
        sys.modules["statistics_toolset_pkg"] = package
    full_name = f"statistics_toolset_pkg.{name}"
    spec = importlib.util.spec_from_file_location(full_name, INTEGRATION / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


def load_recorder_io(fake: FakeRecorder) -> types.ModuleType:
    _stub_home_assistant(fake)
    io = _load("recorder_io")
    io.READ_ONLY_MODE = False  # tests exercise the write paths explicitly
    io.WRITE_ALLOWLIST = ()
    return io


def load_coordinator(fake: FakeRecorder, io: types.ModuleType) -> types.ModuleType:
    coordinator = _load("coordinator")

    # _verify_restore's retry backoff is real (0.2s..1.5s) to survive a slow live recorder;
    # in tests that would add seconds per verification-failure case for no benefit, since only
    # the retry *logic* is under test, not real wall-clock timing.
    async def _instant_sleep(_seconds: float) -> None:
        return None

    coordinator.asyncio.sleep = _instant_sleep

    # The stamp comes from the fake clock so several snapshots stay distinguishable.
    original_backup = coordinator.backup

    async def backup(hass, statistic_id, backup_dir, unit="", label="backup"):
        path = await original_backup(hass, statistic_id, backup_dir, unit, label)
        stamped = path.with_name(f"{statistic_id}.{fake.clock}.{label}{coordinator.BACKUP_SUFFIX}")
        if stamped != path:
            path.replace(stamped)
        return stamped

    coordinator.backup = backup
    return coordinator


# --- extra stubbing needed to load __init__.py (services, config entries) --------------


def _cv_entity_id(value: object) -> str:
    if isinstance(value, str) and "." in value:
        return value
    raise ValueError(f"invalid entity id {value!r}")


def _cv_boolean(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.lower()
        if low in ("1", "true", "yes", "on"):
            return True
        if low in ("0", "false", "no", "off"):
            return False
    raise ValueError(f"invalid boolean {value!r}")


def _cv_ensure_list(value: object) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _cv_string(value: object) -> str:
    if isinstance(value, str):
        return value
    raise ValueError(f"expected string, got {value!r}")


class FakeServiceCall:
    """Mimics ``homeassistant.core.ServiceCall`` — a service handler only reads ``.data``."""

    def __init__(self, data: dict) -> None:
        self.data = data


class FakeServices:
    """Captures registered service handlers and lets a test invoke them like HA would."""

    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], tuple] = {}

    def async_register(self, domain, service, handler, schema=None, supports_response=None):
        self._handlers[(domain, service)] = (handler, schema)

    async def async_call(self, domain, service, service_data=None, **_kwargs):
        handler, schema = self._handlers[(domain, service)]
        # Real voluptuous validation, so a schema bug shows up here too, not just in prod.
        data = schema(service_data or {}) if schema is not None else (service_data or {})
        return await handler(FakeServiceCall(data))


class FakeConfigEntry:
    """Stands in for ``homeassistant.config_entries.ConfigEntry``."""

    def __init__(self, entry_id: str, domain: str, options: dict | None = None) -> None:
        self.entry_id = entry_id
        self.domain = domain
        self.options = dict(options or {})
        self.update_listeners: list = []

    def add_update_listener(self, listener):
        self.update_listeners.append(listener)
        return lambda: self.update_listeners.remove(listener)

    def async_on_unload(self, _unload_callback) -> None:
        pass  # nothing in these tests relies on unload cleanup firing


class FakeConfigEntriesManager:
    """Enough of ``hass.config_entries`` to exercise ``_ensure_config_entry``/``set_config``.

    ``async_update_entry`` fires update listeners as a background task rather than awaiting
    them — matching real Home Assistant — which is exactly the race a test needs to catch:
    a service handler that relied on the reload to update ``hass.data`` would see stale locks
    on its very next call.
    """

    def __init__(self, hass) -> None:
        self._hass = hass
        self._entries: dict[str, FakeConfigEntry] = {}
        self._counter = 0
        self.init_module: types.ModuleType | None = None  # set once __init__.py is loaded
        self.flow = types.SimpleNamespace(async_init=self._flow_async_init)

    def async_entries(self, domain: str) -> list[FakeConfigEntry]:
        return [entry for entry in self._entries.values() if entry.domain == domain]

    def async_get_entry(self, entry_id: str) -> FakeConfigEntry | None:
        return self._entries.get(entry_id)

    def async_update_entry(self, entry: FakeConfigEntry, *, options=None) -> bool:
        if options is None or dict(entry.options) == dict(options):
            return False
        entry.options = dict(options)
        for listener in entry.update_listeners:
            asyncio.get_running_loop().create_task(listener(self._hass, entry))
        return True

    async def async_reload(self, entry_id: str) -> bool:
        entry = self._entries[entry_id]
        await self.init_module.async_unload_entry(self._hass, entry)
        return await self.init_module.async_setup_entry(self._hass, entry)

    async def _flow_async_init(self, domain: str, *, context: dict | None = None) -> dict:
        self._counter += 1
        entry = FakeConfigEntry(f"entry_{self._counter}", domain)
        self._entries[entry.entry_id] = entry
        if self.init_module is not None:
            await self.init_module.async_setup_entry(self._hass, entry)
        return {"type": "create_entry", "result": entry}


class FakePanelRegistry:
    """Records what ``_async_register_panel`` did, so a test can assert on ``require_admin``
    without needing the real ``frontend``/``panel_custom`` components."""

    def __init__(self) -> None:
        self.panels: dict[str, bool] = {}  # frontend_url_path -> require_admin

    def async_panel_exists(self, _hass, url_path: str) -> bool:
        return url_path in self.panels

    def async_remove_panel(self, _hass, url_path: str, *, warn_if_unknown: bool = True) -> None:
        self.panels.pop(url_path, None)

    async def async_register_panel(self, _hass, *, frontend_url_path, require_admin, **_kwargs):
        self.panels[frontend_url_path] = require_admin


def load_init(fake: FakeRecorder) -> tuple[types.ModuleType, types.ModuleType, types.ModuleType]:
    """Load ``recorder_io``, ``coordinator`` and ``__init__`` together, HA fully stubbed.

    ``recorder_io``/``coordinator`` are loaded explicitly first so ``__init__.py``'s relative
    imports resolve to these exact instances — the same ones a test can tweak
    (``io.READ_ONLY_MODE`` etc.) — rather than triggering a second, independent auto-import.
    """
    _stub_home_assistant(fake)
    core = sys.modules["homeassistant.core"]
    core.ServiceCall = FakeServiceCall
    core.ServiceResponse = dict
    core.SupportsResponse = types.SimpleNamespace(ONLY="only", OPTIONAL="optional", NONE="none")

    def module(name: str, **attributes):
        mod = types.ModuleType(name)
        for key, value in attributes.items():
            setattr(mod, key, value)
        sys.modules[name] = mod
        return mod

    module(
        "homeassistant.helpers.config_validation",
        entity_id=_cv_entity_id,
        boolean=_cv_boolean,
        ensure_list=_cv_ensure_list,
        string=_cv_string,
        datetime=lambda value: value,  # unused by the schemas these tests exercise
    )
    module("homeassistant.helpers.typing", ConfigType=dict)
    module("homeassistant.config_entries", SOURCE_USER="user", ConfigEntry=FakeConfigEntry)

    panels = FakePanelRegistry()
    module(
        "homeassistant.components.frontend",
        async_panel_exists=panels.async_panel_exists,
        async_remove_panel=panels.async_remove_panel,
    )
    module("homeassistant.components.panel_custom", async_register_panel=panels.async_register_panel)
    module("homeassistant.components.http", StaticPathConfig=lambda *a, **k: None)

    async def _no_static_paths(_configs):
        return None

    fake.hass.http = types.SimpleNamespace(async_register_static_paths=_no_static_paths)
    fake.hass.panels = panels  # exposed for assertions

    manager = FakeConfigEntriesManager(fake.hass)
    fake.hass.config_entries = manager
    fake.hass.services = FakeServices()

    io = _load("recorder_io")
    io.READ_ONLY_MODE = False
    io.WRITE_ALLOWLIST = ()
    coordinator = _load("coordinator")
    init_module = _load("__init__")
    manager.init_module = init_module
    return init_module, io, coordinator
