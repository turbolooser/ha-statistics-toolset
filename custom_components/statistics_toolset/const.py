"""Constants for the HA Statistics Toolset integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "statistics_toolset"

# Service names
SERVICE_DETECT: Final = "detect"
SERVICE_SIMULATE: Final = "simulate"
SERVICE_FIX: Final = "fix"
SERVICE_BACKUP: Final = "backup"
SERVICE_RESTORE: Final = "restore"
SERVICE_LIST_BACKUPS: Final = "list_backups"
SERVICE_STATUS: Final = "status"
SERVICE_SET_CONFIG: Final = "set_config"
SERVICE_TRANSFER: Final = "transfer"

# Service call fields
CONF_STATISTIC_ID: Final = "statistic_id"
CONF_REFERENCE_ID: Final = "reference_id"
CONF_CYCLE: Final = "cycle"
CONF_START: Final = "start"
CONF_END: Final = "end"
CONF_MAX_RATE: Final = "max_rate_per_hour"
CONF_CONFIRM: Final = "confirm"
CONF_BACKUP_FILE: Final = "backup_file"
CONF_FROM_STATISTIC_ID: Final = "from_statistic_id"
CONF_TO_STATISTIC_ID: Final = "to_statistic_id"

# configuration.yaml keys — the write locks belong outside the code: a value committed to the
# repository would apply to every user, and a hand-edit of const.py is overwritten by the next
# HACS update. YAML survives updates and keeps entity ids out of the repository.
CONF_READ_ONLY: Final = "read_only"
CONF_WRITE_ALLOWLIST: Final = "write_allowlist"
CONF_ADMIN_ONLY: Final = "admin_only"

# Subdirectory (under the HA config dir) where timestamped backups are written.
BACKUP_SUBDIR: Final = f"{DOMAIN}_backups"

# ---------------------------------------------------------------------------
# SAFETY SWITCH — while True, ALL write paths are disabled (simulation only).
# 'simulate' and 'backup' still work (they never modify statistics). 'fix' and
# 'restore' refuse to run. Keep this True during testing; flip to False (and
# restart HA) only once you have verified simulations and taken a full backup.
# SICHERHEITSSCHALTER — solange True, sind ALLE Schreibpfade deaktiviert (nur
# Simulation). 'simulate' und 'backup' funktionieren weiter (sie ändern nie
# Statistiken). 'fix' und 'restore' verweigern die Ausführung. Für die Testphase
# auf True lassen; erst nach geprüfter Simulation und vollem Backup auf False.
# ---------------------------------------------------------------------------
READ_ONLY_MODE: Final = True

# ---------------------------------------------------------------------------
# SECOND LOCK — an allowlist of statistic_ids that may be written at all.
# Empty tuple = no restriction (the read-only switch above still applies).
# Filled = ONLY these ids can be written or cleared; every other id is refused
# even with READ_ONLY_MODE = False and confirm: true. Use this to try things out
# on a test counter while your real data stays untouchable, e.g.
#     WRITE_ALLOWLIST: Final = ("sensor.statistics_toolset_test",)
# ZWEITES SCHLOSS — Liste der statistic_ids, die überhaupt geschrieben werden
# dürfen. Leeres Tupel = keine Einschränkung. Gefüllt = NUR diese IDs sind
# schreib- und löschbar, alle anderen werden auch mit READ_ONLY_MODE = False und
# confirm: true verweigert. Damit lässt sich an einem Testzähler arbeiten,
# während die echten Daten technisch unerreichbar bleiben.
# ---------------------------------------------------------------------------
WRITE_ALLOWLIST: Final[tuple[str, ...]] = ()

# ---------------------------------------------------------------------------
# PANEL VISIBILITY — while True (default), the sidebar panel is admin-only,
# because it can write to the statistics database. Set to False (via the
# panel's config tab or configuration.yaml) to let every user see it; the
# services themselves are still gated by READ_ONLY_MODE/WRITE_ALLOWLIST above,
# so this only controls who can *see* the panel, not who can write.
# SICHTBARKEIT DES PANELS — solange True (Standard), ist das Panel nur für
# Admins sichtbar, weil es in die Statistik-Datenbank schreiben kann. Auf
# False setzen (Config-Tab oder configuration.yaml), damit jeder User es
# sieht; die Dienste selbst bleiben weiter durch READ_ONLY_MODE/WRITE_ALLOWLIST
# oben geschützt — dieser Schalter regelt nur die Sichtbarkeit.
# ---------------------------------------------------------------------------
ADMIN_ONLY_MODE: Final = True

# Supported utility_meter cycle types -> local reset rule lives in engine.cycles.
# Complete set of utility_meter periods; 'none' is a meter configured without a cycle,
# i.e. a permanent total that never resets.
CYCLE_YEARLY: Final = "yearly"
CYCLE_QUARTERLY: Final = "quarterly"
CYCLE_BIMONTHLY: Final = "bimonthly"
CYCLE_MONTHLY: Final = "monthly"
CYCLE_WEEKLY: Final = "weekly"
CYCLE_DAILY: Final = "daily"
CYCLE_HOURLY: Final = "hourly"
CYCLE_QUARTER_HOURLY: Final = "quarter-hourly"
CYCLE_NONE: Final = "none"
CYCLES: Final = (
    CYCLE_YEARLY,
    CYCLE_QUARTERLY,
    CYCLE_BIMONTHLY,
    CYCLE_MONTHLY,
    CYCLE_WEEKLY,
    CYCLE_DAILY,
    CYCLE_HOURLY,
    CYCLE_QUARTER_HOURLY,
    CYCLE_NONE,
)

# Fallback outlier ceiling for a household power counter (kWh per hour). Since v0.4 the
# threshold is normally derived from the data itself (engine.estimate_max_rate); this value
# is only used when there is no data to estimate from.
DEFAULT_MAX_RATE_PER_HOUR: Final = 25.0

# Assumed plausible hourly consumption used when replacing an outlier delta (kWh/h).
DEFAULT_MEDIAN_RATE: Final = 0.8

# Tolerance for the built-in plausibility assertion (kWh).
PLAUSI_TOLERANCE: Final = 1.0
