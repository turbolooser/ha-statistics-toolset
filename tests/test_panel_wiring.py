"""Static checks that the panel's counter lists and filters stay wired up correctly.

There is no Node runtime in CI, so the actual JS logic is verified ad hoc (node scripts, not
committed) whenever it changes; these regex checks catch a future edit silently breaking the
wiring — e.g. a refactor that reverts ``_counterIds`` to reading only ``hass.states``, which
would make counters written straight into the recorder (no live entity, like the
``make_test_sensors.py`` scenarios) disappear from every picker again.
"""

from __future__ import annotations

import re
from pathlib import Path

_PANEL = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "statistics_toolset"
    / "panel"
    / "panel.js"
)
_SOURCE = _PANEL.read_text(encoding="utf-8")


def test_de_and_en_string_tables_have_the_exact_same_keys() -> None:
    """A key present in only one language renders as literal "undefined" in the other —
    happened for real with tabTransfer/introTransfer after the Transfer tab was split out,
    invisible in German (the default) and only noticed by switching to English."""
    block = re.search(r"const STRINGS = \{(.*)\n\};", _SOURCE, re.S).group(1)
    de_start = block.index("de: {")
    en_start = block.index("en: {")
    de_block, en_block = block[de_start:en_start], block[en_start:]

    def keys(text: str) -> set[str]:
        return set(re.findall(r"^ {4}(\w+):", text, re.M))

    de_keys, en_keys = keys(de_block), keys(en_block)
    assert de_keys == en_keys, (
        f"only in DE: {sorted(de_keys - en_keys)}, only in EN: {sorted(en_keys - de_keys)}"
    )
    assert len(de_keys) > 50, "sanity check: the key split above must have actually matched something"


def test_counter_ids_include_orphaned_statistics_not_just_live_entities() -> None:
    """A statistic with no entity (e.g. a make_test_sensors.py scenario) must be selectable.

    ``Object.keys(this._hass.states)`` alone only sees live entities; the fix merges in
    ``recorder/list_statistic_ids`` results via ``_statMeta``.
    """
    assert "_loadStatisticIds" in _SOURCE, "no fetch of recorder/list_statistic_ids found"
    assert "recorder/list_statistic_ids" in _SOURCE
    assert "_allSensorIds" in _SOURCE, "counter lists must go through the merged id source"
    assert "_counterIds() {" in _SOURCE
    counter_ids_body = re.search(r"_counterIds\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "_allSensorIds" in counter_ids_body, "_counterIds regressed to a states-only source"


def test_is_energy_falls_back_to_recorder_metadata() -> None:
    """A live-less statistic has no state attributes, so unit must come from _statMeta."""
    is_energy_body = re.search(r"_isEnergy\(id\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "_statMeta" in is_energy_body, "_isEnergy no longer has an orphaned-statistic path"


def test_backups_tab_has_its_own_filter_row() -> None:
    """Reported as confusing/unfiltered ('Sensorenauswahl unsinnig') — must have a filter."""
    assert 'id="st-bk-filter"' in _SOURCE
    assert 'id="st-bk-energy"' in _SOURCE
    assert 'id="st-bk-matchcount"' in _SOURCE


def test_refresh_counters_keeps_every_tab_in_sync() -> None:
    """Filtering on any tab must update every other tab's picker, count and filter controls —
    all four counter pickers (Sim, Workflow, Backups, Transfer) share one filter state."""
    body = re.search(r"_refreshCounters\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    for needle in (
        "st-stat", "st-wiz-stat", "st-transfer-from", "st-transfer-to",  # <select>s
        "st-filter", "st-wiz-filter", "st-bk-filter", "st-transfer-filter",  # search boxes
        "st-energy", "st-wiz-energy", "st-bk-energy", "st-transfer-energy",  # energy chips
        "st-count", "st-wiz-count", "st-bk-matchcount", "st-transfer-count",  # match counts
        "_renderBkPicklist",
    ):
        assert needle in body, f"_refreshCounters no longer touches {needle}"


def test_every_counter_picker_wires_the_same_filter_row_helper() -> None:
    """Requested explicitly: filter logic/systematics must be consistent everywhere — no
    tab may hand-roll its own filter wiring."""
    assert "_wireFilterRow" in _SOURCE
    wire_calls = re.findall(r'_wireFilterRow\("([\w-]+)",\s*"([\w-]+)"\)', _SOURCE)
    wired_filters = {pair[0] for pair in wire_calls}
    for filter_id in ("st-filter", "st-bk-filter", "st-wiz-filter", "st-transfer-filter"):
        assert filter_id in wired_filters, f"{filter_id} is not wired via _wireFilterRow"


def test_backups_tab_allows_selecting_several_counters() -> None:
    """Requested explicitly: pick several counters, one backup file per counter."""
    assert 'id="st-bk-picklist"' in _SOURCE
    assert "_bkSelected" in _SOURCE, "no persistent multi-selection state found"
    assert "_renderBkPicklist" in _SOURCE
    assert "_onBkPicklistClick" in _SOURCE

    make_backup_body = re.search(r"async _makeBackup\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "_bkSelected" in make_backup_body, "_makeBackup must iterate the selection"
    # One call per counter — never an array/list of ids in a single call, which would
    # imply a combined backup instead of one file per counter.
    assert re.search(r'for \(const \w+ of ids\)', make_backup_body), (
        "_makeBackup should loop and back up each selected counter individually"
    )
    assert '"backup"' in make_backup_body or "'backup'" in make_backup_body


def test_fix_button_only_enabled_when_writable() -> None:
    """Requested: two buttons — read, and fix (only usable when simulation mode is off)."""
    assert 'id="st-fix"' in _SOURCE
    assert "disabled" in re.search(r'id="st-fix"[^>]*', _SOURCE).group(0), (
        "the fix button must start disabled until _updateFixButton proves it writable"
    )
    assert "_updateFixButton" in _SOURCE
    assert "_writeStatus" in _SOURCE

    update_body = re.search(r"_updateFixButton\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "readOnly" in update_body and "allowlist" in update_body, (
        "fix must be gated on both simulation mode and the per-counter allowlist"
    )

    fix_body = re.search(r"async _fix\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "window.confirm" in fix_body, "a write action must ask for explicit confirmation"
    assert "confirm: true" in fix_body, "the fix service call must set confirm: true"
    assert '"fix"' in fix_body or "'fix'" in fix_body


def test_counter_change_refreshes_fix_button_state() -> None:
    """The allowlist is per counter, so switching counters must re-evaluate the button."""
    assert re.search(r'#st-stat"\).addEventListener\("change".*?_updateFixButton', _SOURCE, re.S)


def test_backups_tab_does_not_dump_every_counter_on_an_empty_filter() -> None:
    """The "murks" complaint: 218 real counters used to render as a checkbox wall (and every
    backup file as its own flat table row) the instant the tab opened, before typing
    anything. Both renderers must now show a hint instead when the filter is empty."""
    picklist_body = re.search(r"_renderBkPicklist\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "this._filterText.trim()" in picklist_body
    assert "bkSearchHint" in picklist_body

    table_body = re.search(r"_renderBkTable\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "this._filterText.trim()" in table_body
    assert "bkTableHint" in table_body


def test_backups_table_groups_by_counter_and_stays_collapsible() -> None:
    """Requested: something smarter than a flat, unsorted per-file table."""
    assert "_bkCollapsed" in _SOURCE, "no persistent expand/collapse state found"
    assert "_toggleBkGroup" in _SOURCE
    table_body = re.search(r"_renderBkTable\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "groups.set" in table_body or "groups.get" in table_body, (
        "rows must be grouped by statistic_id, not rendered as one flat list"
    )
    assert "st-bk-group-summary" in table_body


def test_guided_workflow_is_a_separate_tab_from_the_manual_ones() -> None:
    """Requested explicitly: a guided step-by-step tab *next to* the manual tabs, not a
    replacement — the distinction between guided and manual must be unmistakable."""
    assert 'data-tab="workflow"' in _SOURCE
    assert 'data-pane="workflow" hidden' in _SOURCE
    # Every manual tab/pane must still be present and untouched.
    for tab in ("sim", "backups", "transfer", "config"):
        assert f'data-tab="{tab}"' in _SOURCE
        assert f'data-pane="{tab}"' in _SOURCE


def test_guided_workflow_steps_through_read_backup_fix_recheck() -> None:
    assert 'id="st-wiz-stat"' in _SOURCE
    assert 'id="st-wiz-run"' in _SOURCE
    assert 'id="st-wiz-backup"' in _SOURCE
    assert 'id="st-wiz-fix"' in _SOURCE
    assert 'id="st-wiz-keep"' in _SOURCE
    assert 'id="st-wiz-rollback"' in _SOURCE
    assert "_setWizStep" in _SOURCE

    run_body = re.search(r"async _wizRun\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert '"simulate"' in run_body or "'simulate'" in run_body
    assert "_autodetect" in run_body, "the guided flow must auto-detect, never ask to type it"

    backup_body = re.search(r"async _wizBackup\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert '"backup"' in backup_body or "'backup'" in backup_body
    assert "_wizBackupFile" in backup_body, "the backup taken here must be remembered for step 4"

    fix_body = re.search(r"async _wizFix\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "window.confirm" in fix_body, "a write action must ask for explicit confirmation"
    assert '"fix"' in fix_body or "'fix'" in fix_body

    rollback_body = re.search(r"async _wizRollback\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "window.confirm" in rollback_body
    assert '"restore"' in rollback_body or "'restore'" in rollback_body
    # Step 4 must roll back to the snapshot from step 2, not fix's own internal one.
    assert "_wizBackupFile" in rollback_body

    update_body = re.search(r"_updateWizFixButton\(status\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "readOnly" in update_body and "allowlist" in update_body, (
        "the guided flow's write buttons must be gated the same way as the manual ones"
    )
    assert "st-wiz-fix" in update_body and "st-wiz-rollback" in update_body

    # Detected params are captured once in step 1 (_wizData) and reused in steps 3/4 —
    # never re-read from the shared #st-ref/#st-cycle/#st-start/#st-end scratchpad, which
    # the manual tab could have changed in the meantime.
    assert "this._wizData = this._readFormData()" in run_body
    assert '"fix", { ...this._wizData' in fix_body or "'fix', { ...this._wizData" in fix_body


def test_changing_the_wizard_counter_mid_flow_resets_to_step_1() -> None:
    """Reported: picking a different counter after Read must not silently keep the old
    counter's data around through Backup/Fix — it has to force Read again."""
    assert "_wizReset" in _SOURCE
    listener = re.search(
        r'#st-wiz-stat"\)\.addEventListener\("change".*?\}\);', _SOURCE, re.S
    )
    assert listener, "#st-wiz-stat has no change listener"
    assert "_wizReset" in listener.group(0)

    reset_body = re.search(r"_wizReset\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "_wizStatId" in reset_body and "_wizData" in reset_body and "_wizBackupFile" in reset_body
    assert "_setWizStep(1)" in reset_body


def test_outlier_bars_are_highlighted_in_the_current_chart() -> None:
    """Requested: "1 outlier" alone doesn't say where it is — the offending bar in the
    "current" chart must be visually marked, not just counted in a KPI."""
    assert "outlier_periods" in _SOURCE

    svg_sig = re.search(r"_svgBars\(periods, color, emptyText, outlierLabels\)", _SOURCE)
    assert svg_sig, "_svgBars must accept which periods are outliers"

    svg_body = re.search(r"_svgBars\(periods.*?\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "outliers.has(p.label)" in svg_body, "must look up each bar against the outlier set"
    assert "warning-color" in svg_body, "an outlier bar must render in a distinct color"

    render_body = re.search(r"_renderResult\(r, targetId.*?\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "r.outlier_periods" in render_body, (
        "_renderResult must pass the backend's outlier_periods into the current-chart call"
    )


def test_guided_workflow_is_the_default_tab() -> None:
    """Requested: opening/refreshing the dashboard should land on the guided flow, not the
    manual Read/Fix tab."""
    assert '_setTab(this._tab || "workflow")' in _SOURCE


def test_wizard_step4_offers_rollback_before_keep_and_confirms_both() -> None:
    """Requested: swap Keep to the right of Rollback, and require confirmation for either
    outcome — neither should be a single accidental click away from the other."""
    panel4 = re.search(
        r'data-wiz-panel="4" hidden>(.*?)</div>\s*</div>', _SOURCE, re.S
    ).group(1)
    rollback_pos = panel4.index("st-wiz-rollback")
    keep_pos = panel4.index("st-wiz-keep")
    assert rollback_pos < keep_pos, "Rollback must come before Keep (Keep on the right)"

    keep_body = re.search(r"_wizKeep\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "window.confirm" in keep_body, "Keep must ask for confirmation just like Rollback"

    rollback_body = re.search(r"async _wizRollback\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "window.confirm" in rollback_body


def test_transfer_form_is_wired_and_gated_like_fix() -> None:
    """Requested feature: move a renamed counter's statistics without losing them."""
    assert 'id="st-transfer-from"' in _SOURCE
    assert 'id="st-transfer-to"' in _SOURCE
    assert 'id="st-transfer-btn"' in _SOURCE
    assert "_updateTransferButton" in _SOURCE
    assert "_transfer" in _SOURCE

    update_body = re.search(r"_updateTransferButton\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "readOnly" in update_body, "transfer must be gated on simulation mode like fix"

    transfer_body = re.search(r"async _transfer\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "window.confirm" in transfer_body, "a write action must ask for explicit confirmation"
    assert "confirm: true" in transfer_body
    assert '"transfer"' in transfer_body or "'transfer'" in transfer_body

    warn_banner_body = re.search(
        r"async _refreshWarnBanner\(\) \{(.*?)\n  \}", _SOURCE, re.S
    ).group(1)
    assert "_updateTransferButton" in warn_banner_body, (
        "a write-status change must re-gate the transfer button too"
    )


def test_backups_table_offers_restore_gated_the_same_way_as_fix() -> None:
    """Requested: restore belongs in the Backups tab, not just documented as a manual call."""
    assert "st-bk-restore-btn" in _SOURCE
    assert "_restoreBackup" in _SOURCE
    assert "_renderBkTable" in _SOURCE

    render_body = re.search(r"_renderBkTable\(\) \{(.*?)\n  \}", _SOURCE, re.S).group(1)
    assert "readOnly" in render_body and "allowlist" in render_body, (
        "the restore button must be gated on the same write-lock status as fix"
    )

    restore_body = re.search(
        r"async _restoreBackup\(file, statId\) \{(.*?)\n  \}", _SOURCE, re.S
    ).group(1)
    assert "window.confirm" in restore_body, "restore must ask for explicit confirmation too"
    assert '"restore"' in restore_body or "'restore'" in restore_body
    assert "confirm: true" in restore_body

    # A write-status change (e.g. saving the config tab) must re-gate already-rendered
    # restore buttons without requiring the user to reopen the Backups tab.
    warn_banner_body = re.search(
        r"async _refreshWarnBanner\(\) \{(.*?)\n  \}", _SOURCE, re.S
    ).group(1)
    assert "_renderBkTable" in warn_banner_body
