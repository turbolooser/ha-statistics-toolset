"""HA Statistics Toolset - simulate and repair corrupted Home Assistant statistics.

⚠️ This integration can write to the statistics database. Take a full backup first and
always run ``simulate`` before ``fix``. While ``READ_ONLY_MODE`` is on (default), all write
paths are disabled. See the README for the full risk warning.
"""

from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    ADMIN_ONLY_MODE,
    BACKUP_SUBDIR,
    CONF_ADMIN_ONLY,
    CONF_READ_ONLY,
    CONF_WRITE_ALLOWLIST,
    CONF_BACKUP_FILE,
    CONF_CONFIRM,
    CONF_CYCLE,
    CONF_END,
    CONF_FROM_STATISTIC_ID,
    CONF_MAX_RATE,
    CONF_ANCHOR_SUM,
    CONF_REFERENCE_ID,
    CONF_START,
    CONF_STATISTIC_ID,
    CONF_TO_STATISTIC_ID,
    CYCLES,
    DOMAIN,
    READ_ONLY_MODE,
    SERVICE_BACKUP,
    SERVICE_DETECT,
    SERVICE_FIX,
    SERVICE_LIST_BACKUPS,
    SERVICE_RESTORE,
    SERVICE_SET_CONFIG,
    SERVICE_STATUS,
    SERVICE_TRANSFER,
    WRITE_ALLOWLIST,
    SERVICE_SIMULATE,
)
from .coordinator import Preview, backup, detect, fix, list_backups, restore, simulate, transfer
from .recorder_io import write_locks

_LOGGER = logging.getLogger(__name__)

def _translated(key: str, **placeholders: str) -> HomeAssistantError:
    """Build an error whose text Home Assistant renders in the user's own language.

    The wording lives in ``strings.json`` / ``translations/*.json`` — never inline, so no
    message ends up showing two languages at once.
    """
    return HomeAssistantError(
        translation_domain=DOMAIN,
        translation_key=key,
        translation_placeholders=placeholders or None,
    )

def _optional_entity(value: object) -> str:
    """Empty string means 'self mode' (use the counter itself); else a valid entity_id."""
    if value in (None, ""):
        return ""
    return cv.entity_id(value)


# configuration.yaml:
#   statistics_toolset:
#     read_only: false
#     write_allowlist:
#       - sensor.some_test_counter
# Both keys are optional. Left out, the safe defaults from const.py apply. Keeping this in
# YAML rather than in the code means it survives a HACS update and no entity id has to be
# committed to the repository.
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_READ_ONLY): cv.boolean,
                vol.Optional(CONF_WRITE_ALLOWLIST): vol.All(
                    cv.ensure_list, [cv.entity_id]
                ),
                vol.Optional(CONF_ADMIN_ONLY): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_TARGET_FIELDS = {
    vol.Required(CONF_STATISTIC_ID): cv.entity_id,
    vol.Optional(CONF_REFERENCE_ID, default=""): _optional_entity,
    vol.Required(CONF_CYCLE): vol.In(CYCLES),
    vol.Required(CONF_START): cv.datetime,
    vol.Required(CONF_END): cv.datetime,
    vol.Optional(CONF_MAX_RATE, default=0.0): vol.Coerce(float),  # 0 = auto (from data)
    vol.Optional(CONF_ANCHOR_SUM, default=0.0): vol.Coerce(float),
}

DETECT_SCHEMA = vol.Schema({vol.Required(CONF_STATISTIC_ID): cv.entity_id})
SIMULATE_SCHEMA = vol.Schema(_TARGET_FIELDS)
FIX_SCHEMA = vol.Schema({**_TARGET_FIELDS, vol.Required(CONF_CONFIRM): cv.boolean})
# A backup always covers the counter's whole history, so it needs no range.
BACKUP_SCHEMA = vol.Schema({vol.Required(CONF_STATISTIC_ID): cv.entity_id})
LIST_BACKUPS_SCHEMA = vol.Schema(
    {vol.Optional(CONF_STATISTIC_ID, default=""): _optional_entity}
)
RESTORE_SCHEMA = vol.Schema(
    {vol.Required(CONF_BACKUP_FILE): cv.string, vol.Required(CONF_CONFIRM): cv.boolean}
)
TRANSFER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FROM_STATISTIC_ID): cv.entity_id,
        vol.Required(CONF_TO_STATISTIC_ID): cv.entity_id,
        vol.Required(CONF_CONFIRM): cv.boolean,
    }
)
# Both fields optional: a caller changes only what it sends, e.g. the panel's config tab
# can flip read_only without having to resend the whole allowlist.
SET_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_READ_ONLY): cv.boolean,
        vol.Optional(CONF_WRITE_ALLOWLIST): vol.All(cv.ensure_list, [cv.entity_id]),
        vol.Optional(CONF_ADMIN_ONLY): cv.boolean,
    }
)


def _unit_for(hass: HomeAssistant, statistic_id: str) -> str:
    """Return the counter's unit, defaulting to kWh for energy meters."""
    state = hass.states.get(statistic_id)
    if state is not None and (unit := state.attributes.get("unit_of_measurement")):
        return str(unit)
    return "kWh"


def _backup_dir(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(BACKUP_SUBDIR))


async def _ensure_config_entry(hass: HomeAssistant) -> ConfigEntry:
    """Return the integration's config entry, creating it if the user never added one.

    Editing the write locks from the panel has to persist across restarts, and options only
    persist on a config entry — YAML does not get written back to. Rather than making the
    user visit Settings -> Add integration first (exactly the detour this feature removes),
    the entry is created silently on first use with no user input needed, the same one
    ``config_flow.async_step_user`` would create if they had.
    """
    entries = hass.config_entries.async_entries(DOMAIN)
    if entries:
        return entries[0]
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    return result["result"]


def _preview_response(preview: Preview, _read_only: bool = True) -> ServiceResponse:
    return {
        "statistic_id": preview.statistic_id,
        "reference_id": preview.reference_id,
        "cycle": preview.cycle,
        "outliers_found": len(preview.outliers),
        "outlier_periods": preview.outlier_periods,
        # Outliers smoothed out of the source, plus how much that removed.
        "source_outliers": preview.source_outliers,
        "source_removed": preview.source_removed,
        "raw_reference_delta": preview.raw_reference_delta,
        "current_end_sum": round(preview.current_end_sum, 3),
        "proposed_end_sum": round(preview.proposed_end_sum, 3),
        "reference_delta": round(preview.reference_delta, 3),
        "points": preview.points,
        "read_only_mode": _read_only,
        "current_periods": [{"label": lbl, "value": val} for lbl, val in preview.current_periods],
        "proposed_periods": [{"label": lbl, "value": val} for lbl, val in preview.proposed_periods],
        "warnings": preview.warnings,
    }


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services and pick up the optional YAML configuration."""
    options = config.get(DOMAIN) or {}
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].update({
        "read_only": options.get(CONF_READ_ONLY, READ_ONLY_MODE),
        "write_allowlist": tuple(options.get(CONF_WRITE_ALLOWLIST, WRITE_ALLOWLIST) or ()),
        "admin_only": options.get(CONF_ADMIN_ONLY, ADMIN_ONLY_MODE),
        "configured_via": "yaml" if options else "defaults",
    })

    async def handle_simulate(call: ServiceCall) -> ServiceResponse:
        preview = await simulate(
            hass,
            call.data[CONF_STATISTIC_ID],
            call.data[CONF_REFERENCE_ID],
            call.data[CONF_CYCLE],
            call.data[CONF_START],
            call.data[CONF_END],
            _unit_for(hass, call.data[CONF_STATISTIC_ID]),
            call.data[CONF_MAX_RATE],
            call.data[CONF_ANCHOR_SUM],
        )
        return _preview_response(preview, write_locks(hass)[0])

    async def handle_detect(call: ServiceCall) -> ServiceResponse:
        return await detect(hass, call.data[CONF_STATISTIC_ID])

    async def handle_backup(call: ServiceCall) -> ServiceResponse:
        statistic_id = call.data[CONF_STATISTIC_ID]
        path = await backup(
            hass, statistic_id, _backup_dir(hass), _unit_for(hass, statistic_id)
        )
        entries = await hass.async_add_executor_job(
            list_backups, _backup_dir(hass), statistic_id
        )
        return {"backup_file": str(path), "backups": entries}

    async def handle_status(_call: ServiceCall) -> ServiceResponse:
        """What is currently in force — so the panel can show it instead of guessing."""
        read_only, allowlist = write_locks(hass)
        directory = _backup_dir(hass)
        entries = await hass.async_add_executor_job(list_backups, directory)
        return {
            "read_only": read_only,
            "write_allowlist": list(allowlist),
            "admin_only": (hass.data.get(DOMAIN) or {}).get("admin_only", ADMIN_ONLY_MODE),
            "configured_via": (hass.data.get(DOMAIN) or {}).get("configured_via", "defaults"),
            "backup_dir": str(directory),
            "backup_count": len(entries),
        }

    async def handle_set_config(call: ServiceCall) -> ServiceResponse:
        """Write the locks from the panel, so a Settings-page detour is never required.

        ``async_update_entry`` only *schedules* the reload via the update listener (it fires
        it as a background task, not awaited here) — so hass.data is updated directly as
        well, meaning the very next service call already sees the new locks instead of
        racing the reload.
        """
        entry = await _ensure_config_entry(hass)
        new_options = dict(entry.options)
        if CONF_READ_ONLY in call.data:
            new_options[CONF_READ_ONLY] = call.data[CONF_READ_ONLY]
        if CONF_WRITE_ALLOWLIST in call.data:
            new_options[CONF_WRITE_ALLOWLIST] = list(call.data[CONF_WRITE_ALLOWLIST])
        if CONF_ADMIN_ONLY in call.data:
            new_options[CONF_ADMIN_ONLY] = call.data[CONF_ADMIN_ONLY]
        hass.config_entries.async_update_entry(entry, options=new_options)
        admin_only = new_options.get(CONF_ADMIN_ONLY, ADMIN_ONLY_MODE)
        hass.data.setdefault(DOMAIN, {}).update({
            "read_only": new_options.get(CONF_READ_ONLY, READ_ONLY_MODE),
            "write_allowlist": tuple(new_options.get(CONF_WRITE_ALLOWLIST) or ()),
            "admin_only": admin_only,
            "configured_via": "ui",
        })
        # Re-registered here rather than waiting for the reload the update listener
        # schedules in the background — same reasoning as the write locks above: the panel's
        # own save button expects the change to be visible immediately.
        await _async_register_panel(hass, admin_only)
        read_only, allowlist = write_locks(hass)
        return {"read_only": read_only, "write_allowlist": list(allowlist), "admin_only": admin_only}

    async def handle_list_backups(call: ServiceCall) -> ServiceResponse:
        entries = await hass.async_add_executor_job(
            list_backups, _backup_dir(hass), call.data[CONF_STATISTIC_ID]
        )
        return {"backups": entries, "count": len(entries)}

    async def handle_fix(call: ServiceCall) -> ServiceResponse:
        if write_locks(hass)[0]:
            raise _translated("read_only_mode")
        if not call.data[CONF_CONFIRM]:
            raise _translated("confirm_required_fix")
        preview = await fix(
            hass,
            call.data[CONF_STATISTIC_ID],
            call.data[CONF_REFERENCE_ID],
            call.data[CONF_CYCLE],
            call.data[CONF_START],
            call.data[CONF_END],
            _unit_for(hass, call.data[CONF_STATISTIC_ID]),
            _backup_dir(hass),
            call.data[CONF_MAX_RATE],
            call.data[CONF_ANCHOR_SUM],
        )
        return _preview_response(preview, write_locks(hass)[0])

    async def handle_restore(call: ServiceCall) -> ServiceResponse:
        if write_locks(hass)[0]:
            raise _translated("read_only_mode")
        if not call.data[CONF_CONFIRM]:
            raise _translated("confirm_required_restore")
        target = Path(call.data[CONF_BACKUP_FILE])
        if not target.is_absolute():
            target = _backup_dir(hass) / target
        # backup_dir enables the automatic pre-restore snapshot, so the jump back can
        # itself be undone.
        return await restore(hass, target, _backup_dir(hass))

    async def handle_transfer(call: ServiceCall) -> ServiceResponse:
        # Per-id allowlist checks (both from_id and to_id) happen inside transfer() itself,
        # via the same _assert_writable() every other write path goes through.
        if write_locks(hass)[0]:
            raise _translated("read_only_mode")
        if not call.data[CONF_CONFIRM]:
            raise _translated("confirm_required_transfer")
        return await transfer(
            hass,
            call.data[CONF_FROM_STATISTIC_ID],
            call.data[CONF_TO_STATISTIC_ID],
            _backup_dir(hass),
        )

    hass.services.async_register(
        DOMAIN, SERVICE_SIMULATE, handle_simulate, schema=SIMULATE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DETECT, handle_detect, schema=DETECT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_BACKUP, handle_backup, schema=BACKUP_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_LIST_BACKUPS, handle_list_backups, schema=LIST_BACKUPS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_STATUS, handle_status, schema=vol.Schema({}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_CONFIG, handle_set_config, schema=SET_CONFIG_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_FIX, handle_fix, schema=FIX_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESTORE, handle_restore, schema=RESTORE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_TRANSFER, handle_transfer, schema=TRANSFER_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    await _async_register_panel_static_path(hass)
    await _async_register_panel(hass, hass.data[DOMAIN]["admin_only"])

    read_only, allowlist = write_locks(hass)
    _LOGGER.info(
        "HA Statistics Toolset registered: detect/simulate/backup/list_backups always "
        "available, fix/restore %s%s",
        "DISABLED (read_only)" if read_only else "ENABLED",
        f", writes limited to {', '.join(allowlist)}" if allowlist else "",
    )
    if not read_only and not allowlist:
        _LOGGER.warning(
            "HA Statistics Toolset: writing is enabled for every statistic_id. Consider "
            "listing the ones you actually want to change under 'write_allowlist'"
        )
    return True


_PANEL_URL_BASE = f"/{DOMAIN}_panel"


async def _async_register_panel(hass: HomeAssistant, require_admin: bool) -> None:
    """Register the sidebar dashboard panel. Best-effort: never break setup on failure.

    Called again whenever ``admin_only`` changes (from ``set_config`` or the options UI):
    ``panel_custom.async_register_panel`` has no "update" mode and raises if the url_path is
    already taken, so the previous registration is removed first — the panel briefly
    disappears from ``frontend/get_panels`` and reappears with the new visibility, same as
    HA's own settings panels do when their admin requirement changes. The static path for
    panel.js itself is registered only once (in ``async_setup``); re-adding the same aiohttp
    route on every config change would just accumulate duplicate routes.
    """
    try:
        # Imported here, inside the guard: these are core HA modules that are always
        # present on a real instance, but the try/except should cover their import too,
        # not just the calls below — "best-effort" otherwise only half holds.
        from homeassistant.components import frontend, panel_custom

        if frontend.async_panel_exists(hass, DOMAIN):
            frontend.async_remove_panel(hass, DOMAIN, warn_if_unknown=False)

        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=DOMAIN,
            webcomponent_name="statistics-toolset-panel",
            module_url=f"{_PANEL_URL_BASE}/panel.js",
            sidebar_title="HA Statistics Toolset",
            sidebar_icon="mdi:chart-box-outline",
            require_admin=require_admin,
            config={"read_only_mode": READ_ONLY_MODE},
        )
        _LOGGER.info(
            "statistics_toolset: sidebar panel registered at /%s (admin_only=%s)",
            DOMAIN, require_admin,
        )
    except Exception:  # noqa: BLE001 - panel is optional UX, must never block services
        _LOGGER.exception("statistics_toolset: could not register sidebar panel")


async def _async_register_panel_static_path(hass: HomeAssistant) -> None:
    """Serve panel.js and friends. Separate from panel registration: this only needs to run
    once, while the panel itself is re-registered whenever admin_only changes."""
    panel_dir = Path(__file__).parent / "panel"
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(_PANEL_URL_BASE, str(panel_dir), False)]
        )
    except Exception:  # noqa: BLE001 - optional UX, must never block services
        _LOGGER.exception("statistics_toolset: could not register panel static path")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Apply the options set in the UI; they take precedence over YAML."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].update({
        "read_only": entry.options.get(CONF_READ_ONLY, READ_ONLY_MODE),
        "write_allowlist": tuple(entry.options.get(CONF_WRITE_ALLOWLIST) or ()),
        "admin_only": entry.options.get(CONF_ADMIN_ONLY, ADMIN_ONLY_MODE),
        "configured_via": "ui",
    })
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    # A reload (e.g. from Settings -> Configure, unlike the panel's own save button which
    # already re-registers in handle_set_config) must pick up an admin_only change too.
    await _async_register_panel(hass, hass.data[DOMAIN]["admin_only"])
    read_only, allowlist = write_locks(hass)
    _LOGGER.info(
        "HA Statistics Toolset configured via UI: writing %s%s",
        "disabled (simulation)" if read_only else "ENABLED",
        f", limited to {', '.join(allowlist)}" if allowlist else "",
    )
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload so a changed setting takes effect without restarting Home Assistant."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, _entry: ConfigEntry) -> bool:
    """Fall back to the safe defaults; the services stay registered.

    Also runs before a permanent removal (HA always unloads before removing), so the panel
    is deliberately kept here rather than removed — a *reload* (e.g. from an options change)
    unloads and immediately sets up again, and removing the panel here would make it flash
    off and back on. The permanent case is handled separately in ``async_remove_entry``,
    which only fires when the entry is actually being deleted, not reloaded.
    """
    hass.data.setdefault(DOMAIN, {}).update({
        "read_only": READ_ONLY_MODE,
        "write_allowlist": tuple(WRITE_ALLOWLIST),
        "admin_only": ADMIN_ONLY_MODE,
        "configured_via": "defaults",
    })
    await _async_register_panel(hass, ADMIN_ONLY_MODE)
    return True


async def async_remove_entry(hass: HomeAssistant, _entry: ConfigEntry) -> None:
    """Deregister the sidebar panel when the integration is actually removed.

    ``panel_custom`` panels live only in memory, never in ``.storage`` — unlike
    ``async_unload_entry`` (also called on every reload), this only fires once, right before
    the entry is gone for good. Without it the panel is orphaned in the running process: it
    keeps showing in the sidebar and in ``frontend/get_panels`` even though the integration's
    files and config entry are both gone, until Home Assistant is restarted. Best-effort,
    same as registration — removal must never raise and block the entry from going away.
    """
    try:
        from homeassistant.components import frontend

        if frontend.async_panel_exists(hass, DOMAIN):
            frontend.async_remove_panel(hass, DOMAIN, warn_if_unknown=False)
    except Exception:  # noqa: BLE001 - must never block the entry removal itself
        _LOGGER.exception("statistics_toolset: could not remove sidebar panel")
