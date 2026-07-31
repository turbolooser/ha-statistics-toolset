// HA Statistics Toolset — sidebar panel (custom element, no external dependencies).
// UI language follows Home Assistant (hass.language): German or English (fallback).
// Read-only: only 'simulate' / 'detect' are used here.

const STRINGS = {
  de: {
    title: "HA Statistics Toolset",

    langLabel: "Sprache:",
    tabWorkflow: "Geführter Ablauf",
    tabSim: "Auslesen / Reparieren",
    tabBackups: "Backups",
    tabConfig: "Konfiguration",
    introWorkflow:
      "Führt Schritt für Schritt durch eine sichere Reparatur: Auslesen, Sichern, " +
      "Reparieren, erneut prüfen — dann bewusst entscheiden. Für einzelne Aktionen ohne " +
      "geführten Ablauf die anderen Tabs nutzen." +
      "<br>Quelle, Zyklus und Zeitraum werden automatisch erkannt und hier nicht " +
      "manuell angepasst — dafür gibt es den Tab „Auslesen / Reparieren“.",
    wizStep1: "Auslesen",
    wizStep2: "Sichern",
    wizStep3: "Reparieren",
    wizStep4: "Prüfen & entscheiden",
    wizBackupNow: "Jetzt sichern",
    wizKeep: "Behalten",
    wizRollback: "Zurück auf Sicherung",
    wizRollbackConfirm:
      "Setzt {id} exakt auf den Stand der in Schritt 2 angelegten Sicherung zurück — " +
      "macht die Reparatur rückgängig. Fortfahren?",
    wizKeepConfirm:
      "Behält den reparierten Stand von {id} — die Sicherung aus Schritt 2 bleibt als " +
      "Sicherheitsnetz unter Backups erhalten, wird aber nicht automatisch angewendet. " +
      "Fortfahren?",
    introSim:
      "Z\u00e4hler ausw\u00e4hlen, Quelle/Zyklus/Zeitraum pr\u00fcfen (werden automatisch erkannt)." +
      "<br>\u2022 <b>Auslesen:</b> nur lesen, zeigt die Vorschau der bereinigten Reihe." +
      "<br>\u2022 <b>Fixen:</b> schreibt die Reihe \u2014 nur verf\u00fcgbar, wenn der Simulationsmodus aus und dieser Z\u00e4hler freigegeben ist. Vorher immer auslesen und die Vorschau pr\u00fcfen.",
    introBackups:
      "Z\u00e4hler suchen, um vorhandene Sicherungen zu sehen, mehrere auf einmal neu anzulegen oder eine Sicherung direkt wiederherzustellen." +
      "<br>\u2022 <b>Sicherung erstellen:</b> immer m\u00f6glich, deckt die gesamte Historie ab." +
      "<br>\u2022 <b>Wiederherstellen:</b> nur verf\u00fcgbar, wenn der Simulationsmodus aus und der Z\u00e4hler freigegeben ist \u2014 setzt ihn exakt auf den gesicherten Stand zur\u00fcck, der bisherige Stand wird davor automatisch mitgesichert.",
    introConfig:
      "Simulationsmodus und die Liste der beschreibbaren Z\u00e4hler direkt hier setzen." +
      "<br>\u2022 <b>Simulationsmodus an:</b> nichts wird geschrieben, Reparieren/Wiederherstellen verweigern." +
      "<br>\u2022 <b>Freigabeliste leer:</b> alle Z\u00e4hler sind beschreibbar." +
      "<br>\u2022 <b>Freigabeliste gef\u00fcllt:</b> nur diese \u2014 alles andere wird auch bei ausgeschaltetem Simulationsmodus abgewiesen." +
      "<br>\u00c4nderungen wirken sofort, kein Neustart n\u00f6tig.",
    loading: "Lade\u2026",
    working: "Arbeite\u2026",
    noBackups: "Noch keine Sicherungen vorhanden.",
    makeBackup: "Sicherung erstellen",
    reload: "Aktualisieren",
    selectAll: "Alle sichtbaren auswählen",
    selectedCount: "{n} ausgewählt",
    noMatches: "Keine Zähler gefunden.",
    bkSearchHint: "Tippen zum Suchen…",
    bkTableHint: "Zähler suchen, um vorhandene Sicherungen zu sehen.",
    bkMoreHint: "{n} weitere — Filter eingrenzen",
    bkSelectAllMatches: "Alle {n} Treffer auswählen",
    bkDeselectAllMatches: "Alle {n} Treffer abwählen",
    bkRemove: "Entfernen",
    bkGroupCount: "{n} Sicherungen",
    tabTransfer: "Übertragen",
    introTransfer:
      "Zähler umbenannt? Die komplette Statistik-Historie von der alten, verwaisten " +
      "statistic_id auf die neue Entity verschieben." +
      "<br>Die Quelle wird danach geleert — vorher automatisch gesichert. Das Ziel darf " +
      "noch keine eigene Statistik haben.",
    transferFrom: "Von (alte statistic_id)",
    tTransferFrom: "Die verwaiste statistic_id, von der die Historie wegverschoben wird — auch Zähler ohne lebende Entity werden hier gelistet.",
    transferTo: "Nach (aktuelle Entity)",
    tTransferTo: "Die Entity, die die Historie ab jetzt trägt. Darf noch keine eigene Statistik haben.",
    transferBtn: "Übertragen",
    transferConfirm:
      "Verschiebt die komplette Statistik-Historie von {from} nach {to}. {from} wird danach " +
      "geleert — die Daten werden vorher automatisch gesichert. {to} darf noch keine eigene " +
      "Statistik haben. Fortfahren?",
    transferDone: "Übertragen",
    bkDone: "Sicherung erstellt",
    bkWhen: "Zeitpunkt",
    bkKind: "Art",
    bkRange: "Zeitraum",
    bkFile: "Datei",
    bkAction: "Aktion",
    restoreBtn: "Wiederherstellen",
    restoreConfirm: "Setzt {id} exakt auf den Stand dieser Sicherung zur\u00fcck: die komplette Statistik wird geleert und aus der Datei {file} neu aufgebaut. Der aktuelle Stand wird davor automatisch als eigene Sicherung angelegt. Fortfahren?",
    restoreDone: "Wiederhergestellt",
    restoreDisabledTip: "Nur verf\u00fcgbar, wenn der Simulationsmodus ausgeschaltet und dieser Z\u00e4hler beschreibbar ist.",
    bkPartial: "unvollst\u00e4ndig",
    cfgSimToggle: "Simulationsmodus (nichts wird geschrieben)",
    cfgAllowEdit: "Beschreibbare Z\u00e4hler (ein statistic_id pro Zeile, leer = alle)",
    cfgAllowPh: "z. B. sensor.mein_testzaehler",
    cfgAdminToggle: "Panel nur f\u00fcr Admins sichtbar",
    cfgSave: "Speichern",
    cfgSaved: "Gespeichert.",
    cfgVia: "Quelle der Einstellung",
    cfgDir: "Sicherungsordner",
    cfgCount: "Anzahl Sicherungen",
    subtitle: "Statistiken simulieren & prüfen — nur lesen.",
    warnSim:
      "⚠️ Simulationsmodus aktiv — es wird nichts geschrieben. Reparieren/Wiederherstellen " +
      "erfolgt über die Dienste, nur nach vollständigem Backup.",
    warnWrite: "✎ Schreiben aktiv für: {ids}",
    warnWriteAll: "✎ Schreiben aktiv — für alle Zähler (keine Freigabeliste gesetzt)!",
    filterPh: "Zähler filtern — Name, * als Platzhalter (z. B. *energie* oder *zaehler*)",
    energyOnly: "⚡ nur Energie",
    matches: "Treffer",
    counter: "Zähler",
    autodetect: "↻ Auto-erkennen",
    source: "Quelle",
    selfMode: "— Selbst-Modus (nur Ausreißer glätten) —",
    cycle: "Zyklus",
    range: "Zeitraum",
    rAll: "Alles",
    rYtd: "Dieses Jahr",
    rLast: "Letztes Jahr",
    rY2: "Vorletztes Jahr",
    rMtd: "Dieser Monat",
    r12: "12 Monate",
    tAll: "Gesamter vorhandener Statistik-Zeitraum des Zählers (wird automatisch erkannt).",
    noData: "Keine Daten in diesem Zeitraum — Daten erst ab",
    notes: "Hinweise",
    start: "Start",
    end: "Ende",
    run: "Auslesen",
    running: "Lese aus…",
    fix: "Fixen",
    fixing: "Fixe…",
    fixDisabledTip: "Nur verfügbar, wenn der Simulationsmodus in der Konfiguration ausgeschaltet und dieser Zähler beschreibbar ist.",
    fixConfirm: "Schreibt die reparierte Reihe von {id} in die Statistik-Datenbank. Vorher wird automatisch eine vollständige Sicherung angelegt — bei Bedarf über den Backups-Tab wiederherstellbar. Fortfahren?",
    fixDone: "Repariert.",
    pick: "— Zähler wählen —",
    detHint: "Quelle, Zyklus und Zeitraum werden beim Wählen automatisch erkannt.",
    srcAuto: "Quelle automatisch erkannt",
    srcSelf: "Selbst-Modus (keine separate Quelle)",
    cycleGuessed: "Zyklus aus dem Entity-Namen geraten — bitte prüfen, ein falscher Zyklus baut die Reihe falsch auf.",
    cycleGuessedShort: "Zyklus geraten",
    cycleRead: "Zyklus exakt aus der utility_meter-Konfiguration gelesen.",
    cycleReadShort: "Zyklus gelesen",
    extendable: "Historie verlängerbar",
    counterFrom: "Zähler hat Daten ab:",
    sourceFrom: "Quelle reicht zurück bis:",
    wStartMoved: "Start auf {ts} angehoben — davor hat die Quelle keine Daten.",
    wSourceOutliers: "{count} unplausible Sprünge in der Quelle wurden geglättet und dabei {amount} kWh entfernt — die vorgeschlagene Summe liegt deshalb unter dem Rohwert der Quelle.",
    outliers: "Ausreißer (Zähler)",
    outlierMarker: "Ausreißer",
    emptyCurrent: "Der Zähler hat in diesem Zeitraum keine Statistikdaten — hier ist nichts zu zeichnen. Eine Reparatur würde die Historie für diesen Zeitraum neu anlegen.",
    emptyProposed: "Für diesen Zeitraum lässt sich keine Reihe ableiten.",
    srcOutliers: "Ausreißer (Quelle)",
    current: "Aktuell",
    proposed: "Vorschlag",
    endsum: "Endsumme",
    refdelta: "Referenz-Delta",
    points: "Punkte",
    pickTip: "Bitte zuerst einen Zähler wählen.",
    hint: 'Zähler wählen — Quelle, Zyklus und Zeitraum werden erkannt. Dann „Auslesen".',
    err: "Fehler",
    tCounter: "Der beschädigte Zähler, dessen Statistik korrigiert werden soll. Auswahl startet die automatische Erkennung.",
    tSource: "Sensor, aus dem der Zähler abgeleitet wird (Wahrheitsquelle). Leer = Selbst-Modus: nur die Ausreißer des Zählers werden geglättet.",
    tCycle: "Reset-Regel des Zählers — wird aus der utility_meter-Konfiguration gelesen. yearly = 1. Jan · quarterly = Jan/Apr/Jul/Okt · bimonthly = Jan/Mär/Mai/… · monthly = Monatserster · weekly = Montag · daily = Mitternacht · hourly = zur Minute 0 · Gesamtzähler = läuft ohne Reset weiter (API-Wert: none).",
    cycleNone: "Gesamtzähler — läuft ohne Reset weiter",
    tStart: "Erster Zeitpunkt des Bereichs — zugleich der Nullpunkt der Summe.",
    tEnd: "Letzter Zeitpunkt des Bereichs.",
  },
  en: {
    title: "HA Statistics Toolset",

    langLabel: "Language:",
    tabWorkflow: "Guided workflow",
    tabSim: "Read / Fix",
    tabBackups: "Backups",
    tabConfig: "Configuration",
    introWorkflow:
      "Walks you through a safe repair step by step: read, back up, fix, recheck — then " +
      "decide on purpose. For one-off actions without the guided flow, use the other tabs." +
      "<br>Source, cycle and range are detected automatically and not adjustable here — " +
      "that's what the \"Read / Fix\" tab is for.",
    wizStep1: "Read",
    wizStep2: "Back up",
    wizStep3: "Fix",
    wizStep4: "Recheck & decide",
    wizBackupNow: "Back up now",
    wizKeep: "Keep",
    wizRollback: "Roll back to backup",
    wizRollbackConfirm:
      "Puts {id} back to exactly the snapshot taken in step 2 — undoes the fix. Continue?",
    wizKeepConfirm:
      "Keeps the repaired state of {id} — the step-2 backup stays available under Backups " +
      "as a safety net, but is not applied automatically. Continue?",
    introSim:
      "Pick a counter, review source/cycle/range (detected automatically)." +
      "<br>\u2022 <b>Read:</b> read-only, shows the preview of the cleaned-up series." +
      "<br>\u2022 <b>Fix:</b> writes the series \u2014 only available when simulation mode is off and this counter is allowed. Always read first and review the preview.",
    introBackups:
      "Search for a counter to see its existing backups, create several at once, or restore one directly." +
      "<br>\u2022 <b>Create backup:</b> always possible, covers the whole history." +
      "<br>\u2022 <b>Restore:</b> only available when simulation mode is off and the counter is allowed \u2014 puts it back exactly to the saved state, automatically saving the current state first.",
    introConfig:
      "Set simulation mode and the list of writable counters right here." +
      "<br>\u2022 <b>Simulation mode on:</b> nothing is written, fix/restore refuse." +
      "<br>\u2022 <b>Empty allowlist:</b> every counter is writable." +
      "<br>\u2022 <b>Allowlist with entries:</b> only those \u2014 everything else is refused even with simulation mode off." +
      "<br>Changes take effect immediately, no restart needed.",
    loading: "Loading\u2026",
    working: "Working\u2026",
    noBackups: "No backups yet.",
    makeBackup: "Create backup",
    reload: "Refresh",
    selectAll: "Select all visible",
    selectedCount: "{n} selected",
    noMatches: "No counters found.",
    bkSearchHint: "Type to search…",
    bkTableHint: "Search for a counter to see its existing backups.",
    bkMoreHint: "{n} more — narrow the filter",
    bkSelectAllMatches: "Select all {n} matches",
    bkDeselectAllMatches: "Deselect all {n} matches",
    bkRemove: "Remove",
    bkGroupCount: "{n} backups",
    tabTransfer: "Transfer",
    introTransfer:
      "Renamed a counter? Move its whole statistics history from the old, orphaned " +
      "statistic_id onto the new entity." +
      "<br>The source is cleared afterwards — saved automatically first. The target must " +
      "not have any statistics of its own yet.",
    transferFrom: "From (old statistic_id)",
    tTransferFrom: "The orphaned statistic_id to move the history away from — counters with no live entity left are listed here too.",
    transferTo: "To (current entity)",
    tTransferTo: "The entity that should carry the history from now on. Must not have any statistics of its own yet.",
    transferBtn: "Transfer",
    transferConfirm:
      "Moves the whole statistics history from {from} to {to}. {from} is cleared afterwards " +
      "— its data is saved automatically first. {to} must not have any statistics of its " +
      "own yet. Continue?",
    transferDone: "Transferred",
    bkDone: "Backup created",
    bkWhen: "Time",
    bkKind: "Kind",
    bkRange: "Range",
    bkFile: "File",
    bkAction: "Action",
    restoreBtn: "Restore",
    restoreConfirm: "Puts {id} back to exactly this snapshot: its whole statistics history is cleared and rebuilt from the file {file}. The current state is saved as its own snapshot automatically first. Continue?",
    restoreDone: "Restored",
    restoreDisabledTip: "Only available when simulation mode is off and this counter is writable.",
    bkPartial: "partial",
    cfgSimToggle: "Simulation mode (nothing is written)",
    cfgAllowEdit: "Writable counters (one statistic_id per line, empty = all)",
    cfgAllowPh: "e.g. sensor.my_test_counter",
    cfgAdminToggle: "Panel visible to admins only",
    cfgSave: "Save",
    cfgSaved: "Saved.",
    cfgVia: "Setting comes from",
    cfgDir: "Backup folder",
    cfgCount: "Backup count",
    subtitle: "Simulate & review statistics — read-only.",
    warnSim:
      "⚠️ Simulation mode active — nothing is written. Fix/restore run via the services, " +
      "only after a full backup.",
    warnWrite: "✎ Writing enabled for: {ids}",
    warnWriteAll: "✎ Writing enabled — for every counter (no allowlist set)!",
    filterPh: "Filter counters — name, * as wildcard (e.g. *energy* or *meter*)",
    energyOnly: "⚡ energy only",
    matches: "matches",
    counter: "Counter",
    autodetect: "↻ Auto-detect",
    source: "Source",
    selfMode: "— self mode (smooth outliers only) —",
    cycle: "Cycle",
    range: "Range",
    rAll: "All",
    rYtd: "This year",
    rLast: "Last year",
    rY2: "Year before last",
    rMtd: "This month",
    r12: "12 months",
    tAll: "The counter's entire available statistics range (detected automatically).",
    noData: "No data in this range — data only from",
    notes: "Notes",
    start: "Start",
    end: "End",
    run: "Read",
    running: "Reading…",
    fix: "Fix",
    fixing: "Fixing…",
    fixDisabledTip: "Only available when simulation mode is off in the configuration and this counter is writable.",
    fixConfirm: "Writes the repaired series of {id} to the statistics database. A full backup is created automatically first — restorable via the Backups tab if needed. Continue?",
    fixDone: "Fixed.",
    pick: "— select counter —",
    detHint: "Source, cycle and range are detected automatically on selection.",
    srcAuto: "source auto-detected",
    srcSelf: "self mode (no separate source)",
    cycleGuessed: "Cycle guessed from the entity name — please verify; a wrong cycle rebuilds the series wrongly.",
    cycleGuessedShort: "cycle guessed",
    cycleRead: "Cycle read straight from the utility_meter configuration.",
    cycleReadShort: "cycle read",
    extendable: "history extendable",
    counterFrom: "Counter has data from:",
    sourceFrom: "Source reaches back to:",
    wStartMoved: "Start moved up to {ts} — the source has no data before that.",
    wSourceOutliers: "{count} implausible jump(s) in the source were smoothed, removing {amount} kWh — the proposed sum is therefore below the source's raw value.",
    outliers: "Outliers (counter)",
    outlierMarker: "outlier",
    emptyCurrent: "The counter has no statistics in this range — nothing to draw. A repair would create the history for this period.",
    emptyProposed: "No series can be derived for this range.",
    srcOutliers: "Outliers (source)",
    current: "Current",
    proposed: "Proposed",
    endsum: "End sum",
    refdelta: "Reference delta",
    points: "Points",
    pickTip: "Please select a counter first.",
    hint: 'Select a counter — source, cycle and range are detected. Then "Read".',
    err: "Error",
    tCounter: "The corrupted counter to repair. Selecting it starts auto-detection.",
    tSource: "The sensor the counter is derived from (source of truth). Empty = self mode: only the counter's own outliers are smoothed.",
    tCycle: "The counter's reset rule — read from the utility_meter configuration. yearly = Jan 1 · quarterly = Jan/Apr/Jul/Oct · bimonthly = Jan/Mar/May/… · monthly = 1st of month · weekly = Monday · daily = midnight · hourly = at minute 0 · running total = keeps counting without any reset (API value: none).",
    cycleNone: "Running total — never resets",
    tStart: "First moment of the range — also the zero point of the sum.",
    tEnd: "Last moment of the range.",
  },
};

const LANG_KEY = "statistics_toolset_lang"; // "auto" | "de" | "en"

class StatisticsToolsetPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._lang = this._resolveLang();
    this._t = STRINGS[this._lang];
    if (this._filterText === undefined) this._filterText = "";
    if (this._energyOnly === undefined) this._energyOnly = true;
    if (this._statMeta === undefined) {
      this._statMeta = new Map(); // placeholder until the async fetch below resolves
      this._loadStatisticIds();
    }
    if (!this._built) this._build();
  }

  /**
   * Counters written straight into the recorder (e.g. the make_test_sensors.py scenarios,
   * or any statistic left behind by a renamed/removed entity) have no live state, so they
   * never show up in hass.states — the "Zähler" list would silently omit exactly the
   * counters someone set up to test against. recorder/list_statistic_ids sees them too.
   */
  async _loadStatisticIds() {
    try {
      const rows = await this._hass.callWS({ type: "recorder/list_statistic_ids" });
      this._statMeta = new Map(rows.map((r) => [r.statistic_id, r]));
    } catch (e) {
      this._statMeta = new Map();
    }
    this._refreshCounters();
  }

  // ---- language ----------------------------------------------------------
  _resolveLang() {
    let override = "auto";
    try {
      override = localStorage.getItem(LANG_KEY) || "auto";
    } catch (e) {
      /* ignore */
    }
    if (override === "de" || override === "en") return override;
    const l = (this._hass && this._hass.language ? this._hass.language : "en").toLowerCase();
    return l.startsWith("de") ? "de" : "en";
  }

  _setLang(value) {
    try {
      localStorage.setItem(LANG_KEY, value);
    } catch (e) {
      /* ignore */
    }
    this._lang = this._resolveLang();
    this._t = STRINGS[this._lang];
    this._built = false;
    this._build();
  }

  _storedLangChoice() {
    try {
      return localStorage.getItem(LANG_KEY) || "auto";
    } catch (e) {
      return "auto";
    }
  }

  // ---- helpers -----------------------------------------------------------
  _fmt(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
      d.getDate()
    ).padStart(2, "0")}T${String(d.getHours()).padStart(2, "0")}:${String(
      d.getMinutes()
    ).padStart(2, "0")}`;
  }

  _isoToLocal(iso) {
    const d = new Date(iso);
    return isNaN(d.getTime()) ? "" : this._fmt(d);
  }

  /** Date range of a preset, or null for "all" (which depends on detection). */
  _presetRange(preset) {
    const now = new Date();
    const Y = now.getFullYear();
    if (preset === "ytd") return { s: new Date(Y, 0, 1), e: now };
    if (preset === "last") return { s: new Date(Y - 1, 0, 1), e: new Date(Y - 1, 11, 31, 23, 59) };
    if (preset === "y2") return { s: new Date(Y - 2, 0, 1), e: new Date(Y - 2, 11, 31, 23, 59) };
    if (preset === "mtd") return { s: new Date(Y, now.getMonth(), 1), e: now };
    if (preset === "12m") {
      const s = new Date(now);
      s.setMonth(s.getMonth() - 12);
      return { s, e: now };
    }
    return null;
  }

  _setRange(preset) {
    if (preset === "all") {
      // Whole available history — comes from 'detect'. Not yet known: detect it now, which
      // fills start/end with exactly that range.
      const r = this._detectedRange;
      if (!r || !r.start) {
        this._autodetect(this.querySelector("#st-stat").value);
        return;
      }
      this.querySelector("#st-start").value = this._isoToLocal(r.start);
      this.querySelector("#st-end").value = r.end
        ? this._isoToLocal(r.end)
        : this._fmt(new Date());
      return;
    }
    const range = this._presetRange(preset);
    if (!range) return;
    this.querySelector("#st-start").value = this._fmt(range.s);
    this.querySelector("#st-end").value = this._fmt(range.e);
  }

  // ---- tabs ---------------------------------------------------------------
  _setTab(name) {
    this._tab = name;
    const T = this._t;
    this.querySelectorAll("[data-tab]").forEach((b) =>
      b.classList.toggle("on", b.dataset.tab === name)
    );
    this.querySelectorAll("[data-pane]").forEach((pane) => {
      pane.hidden = pane.dataset.pane !== name;
    });
    // The result card belongs to the simulation tab only.
    const result = this.querySelector("#st-result");
    if (result) result.hidden = name !== "sim";
    const intro = this.querySelector("#st-intro");
    if (intro) {
      // introConfig carries structure (bold labels, line breaks) that .textContent can't
      // render; these strings are fixed, developer-authored copy, not user input, so
      // .innerHTML here is safe. introSim/introBackups are plain sentences and render
      // identically either way.
      intro.innerHTML =
        name === "workflow" ? T.introWorkflow
        : name === "backups" ? T.introBackups
        : name === "transfer" ? T.introTransfer
        : name === "config" ? T.introConfig
        : T.introSim;
    }
    if (name === "backups") this._loadBackups();
    if (name === "config") this._loadStatus();
  }

  async _service(service, data = {}) {
    const res = await this._hass.callService(
      "statistics_toolset", service, data, undefined, false, true
    );
    return res.response || res;
  }

  /** Ticks a "still working" label with elapsed seconds while a long service call is in
   *  flight. A large counter's fix/backup/restore can take well over a minute under real
   *  DB load (live-verified 2026-07-31, 28k points) — a static "Working…" looks stuck
   *  instead of in progress. `setText` writes the label wherever the caller displays it
   *  (a message span or a button's own text); call the returned function when done. */
  _startWorking(setText, label) {
    const start = Date.now();
    setText(label);
    const id = setInterval(() => {
      setText(`${label} (${Math.round((Date.now() - start) / 1000)}s)`);
    }, 1000);
    return () => clearInterval(id);
  }

  // ---- backups ------------------------------------------------------------

  /**
   * Renders the "select one or more counters to back up" control. Search-first, not a
   * dump: with an empty filter this shows a hint instead of every counter (218 on a real
   * system) — the wall of checkboxes this replaced was reported as "murks". Matches appear
   * as a capped dropdown below the filter; picking one turns it into a removable chip above
   * the filter, so the current selection stays visible and correctable across re-filtering
   * without having to search again. Selections persist in ``_bkSelected`` regardless of the
   * current filter — narrowing the filter never silently drops a choice made before.
   */
  _renderBkPicklist() {
    const T = this._t;
    const box = this.querySelector("#st-bk-picklist");
    if (!box) return;
    if (!this._bkSelected) this._bkSelected = new Set();

    const selectedIds = Array.from(this._bkSelected).sort();
    const chips = selectedIds.length
      ? `<div class="st-bk-chips">${selectedIds
          .map(
            (id) =>
              `<span class="st-chip st-bk-chip">${this._esc(id)}
                 <button type="button" class="st-bk-chip-x" data-id="${this._esc(id)}"
                   aria-label="${this._esc(T.bkRemove)}">×</button>
               </span>`
          )
          .join("")}</div>`
      : "";

    if (!this._filterText.trim()) {
      box.innerHTML = `${chips}<div class="st-hint st-bk-hint">${this._esc(T.bkSearchHint)}</div>`;
      return;
    }
    const ids = this._counterIds();
    if (!ids.length) {
      box.innerHTML = `${chips}<div class="st-empty">${this._esc(T.noMatches)}</div>`;
      return;
    }
    const MAX_SHOWN = 12;
    const shown = ids.slice(0, MAX_SHOWN);
    const more = ids.length - shown.length;
    box.innerHTML = `${chips}
      <div class="st-bk-dropdown">
        ${shown
          .map((id) => {
            const picked = this._bkSelected.has(id);
            return `<button type="button" class="st-bk-option${picked ? " picked" : ""}"
                data-id="${this._esc(id)}">${picked ? "✓ " : ""}${this._esc(id)}</button>`;
          })
          .join("")}
        ${more > 0
          ? `<div class="st-hint st-bk-more">${this._esc(T.bkMoreHint.replace("{n}", String(more)))}</div>`
          : ""}
        <div class="st-bk-bulk">
          <button type="button" class="st-bk-selectall" id="st-bk-selectall">${this._esc(
            T.bkSelectAllMatches.replace("{n}", String(ids.length))
          )}</button>
          <button type="button" class="st-bk-selectall" id="st-bk-deselectall">${this._esc(
            T.bkDeselectAllMatches.replace("{n}", String(ids.length))
          )}</button>
        </div>
      </div>`;
  }

  /** Event delegation: the picklist's contents are replaced on every filter change, so a
   *  listener on individual buttons would be lost each time — one listener on the
   *  container, attached once in _build(), survives that. */
  _onBkPicklistClick(e) {
    const target = e.target.closest("button");
    if (!target) return;
    if (!this._bkSelected) this._bkSelected = new Set();
    if (target.id === "st-bk-selectall") {
      this._counterIds().forEach((id) => this._bkSelected.add(id));
    } else if (target.id === "st-bk-deselectall") {
      this._counterIds().forEach((id) => this._bkSelected.delete(id));
    } else if (target.classList.contains("st-bk-option")) {
      const id = target.dataset.id;
      if (this._bkSelected.has(id)) this._bkSelected.delete(id);
      else this._bkSelected.add(id);
    } else if (target.classList.contains("st-bk-chip-x")) {
      this._bkSelected.delete(target.dataset.id);
    } else {
      return;
    }
    this._renderBkPicklist();
    const bkCount = this.querySelector("#st-bk-matchcount");
    if (bkCount) {
      const matchText = `${this._counterIds().length} ${this._t.matches}`;
      const selected = this._bkSelected.size;
      bkCount.textContent = selected
        ? `${matchText} · ${this._t.selectedCount.replace("{n}", selected)}`
        : matchText;
    }
  }

  /** Toggles one counter's backup history open/closed; collapsed state survives a re-render
   *  (e.g. after making a new backup) via ``_bkCollapsed``, so expanding several groups to
   *  compare them doesn't get reset by an unrelated refresh. */
  _toggleBkGroup(statId) {
    if (!this._bkCollapsed) this._bkCollapsed = new Set();
    if (this._bkCollapsed.has(statId)) this._bkCollapsed.delete(statId);
    else this._bkCollapsed.add(statId);
    this._renderBkTable();
  }

  async _loadBackups() {
    const T = this._t;
    const box = this.querySelector("#st-bk-list");
    if (!box) return;
    box.innerHTML = `<div class="st-hint">${T.loading}</div>`;
    try {
      // Shows every counter's backups; the "Zähler" column already names which is which,
      // and the picklist above is for choosing what to back up, not for narrowing this view.
      const r = await this._service("list_backups", { statistic_id: "" });
      this._bkRows = r.backups || [];
      this._renderBkTable();
    } catch (e) {
      box.innerHTML = `<div class="st-err">${this._esc(String(e.message || e))}</div>`;
    }
  }

  /**
   * Renders the backup table from the last fetched rows (``_bkRows``), using the current
   * write-lock status for the restore button. Split out from ``_loadBackups`` so that a
   * write-status change (from ``_refreshWarnBanner``) can re-gate the buttons without an
   * unnecessary re-fetch of the list itself.
   *
   * Search-first, grouped by counter: an empty filter shows a hint instead of every backup
   * of every counter (hundreds of rows on a real system) — the flat, unsorted table this
   * replaced was reported as "murks". A non-empty filter groups matches by counter into a
   * one-line summary (latest snapshot + its own restore button) that expands to the full
   * per-counter history on click; expanded/collapsed state persists in ``_bkCollapsed``
   * across re-renders, so a newly matched group starts open (the filter already narrowed
   * things — no extra click should be needed) while a group the user deliberately collapsed
   * stays collapsed through a reload.
   */
  _renderBkTable() {
    const T = this._t;
    const box = this.querySelector("#st-bk-list");
    if (!box) return;
    if (!this._filterText.trim()) {
      box.innerHTML = `<div class="st-hint st-bk-hint">${this._esc(T.bkTableHint)}</div>`;
      return;
    }
    const rows = (this._bkRows || []).filter((b) =>
      this._matches(b.statistic_id || "", this._filterText)
    );
    if (!rows.length) {
      box.innerHTML = `<div class="st-empty">${this._esc(
        (this._bkRows || []).length ? T.noMatches : T.noBackups
      )}</div>`;
      return;
    }
    if (!this._bkCollapsed) this._bkCollapsed = new Set();

    // list_backups already returns newest-first; grouping preserves that order per counter.
    const groups = new Map();
    for (const b of rows) {
      const statId = b.statistic_id || "";
      if (!groups.has(statId)) groups.set(statId, []);
      groups.get(statId).push(b);
    }

    const status = this._writeStatus || { readOnly: true, allowlist: [] };
    const canRestore = (statId) =>
      !status.readOnly && (!status.allowlist.length || status.allowlist.includes(statId));

    const restoreBtn = (b, extraClass) => {
      const writable = canRestore(b.statistic_id || "");
      return `<button class="st-bk-restore-btn${extraClass}" data-file="${this._esc(
        b.file
      )}" data-stat="${this._esc(b.statistic_id || "")}"${
        writable ? "" : ` disabled title="${this._esc(T.restoreDisabledTip)}"`
      }>${T.restoreBtn}</button>`;
    };

    const detailRow = (b) => `<tr>
          <td>${this._esc(this._localTs(b.created_utc))}</td>
          <td><span class="st-tag">${this._esc(b.label || "-")}</span>${
      b.full_history ? "" : ` <span class="st-tag">${this._esc(T.bkPartial)}</span>`
    }</td>
          <td class="num">${this._n(b.points)}</td>
          <td class="num">${this._n(b.end_sum)}</td>
          <td>${this._esc(String(b.first || "").slice(0, 10))} … ${this._esc(
      String(b.last || "").slice(0, 10)
    )}</td>
          <td class="st-file" title="${this._esc(b.file)}">${this._esc(b.file)}</td>
          <td>${restoreBtn(b, "")}</td>
        </tr>`;

    const groupHtml = ([statId, items]) => {
      const latest = items[0];
      const open = !this._bkCollapsed.has(statId);
      return `
        <div class="st-bk-group${open ? " open" : ""}">
          <div class="st-bk-group-summary" data-stat="${this._esc(statId)}">
            <span class="st-bk-group-chevron">${open ? "▾" : "▸"}</span>
            <span class="st-bk-group-name">${this._esc(statId)}</span>
            <span class="st-count">${this._esc(
              T.bkGroupCount.replace("{n}", String(items.length))
            )}</span>
            <span class="st-hint">${this._esc(this._localTs(latest.created_utc))}</span>
            <span class="num">${this._n(latest.end_sum)}</span>
            ${restoreBtn(latest, " st-bk-group-restore")}
          </div>
          <div class="st-bk-group-detail">
            <div class="st-table-wrap">
            <table class="st-table">
              <tr><th>${T.bkWhen}</th><th>${T.bkKind}</th>
                  <th class="num">${T.points}</th><th class="num">${T.endsum}</th>
                  <th>${T.bkRange}</th><th>${T.bkFile}</th><th>${T.bkAction}</th></tr>
              ${items.map(detailRow).join("")}
            </table>
            </div>
          </div>
        </div>`;
    };

    box.innerHTML = Array.from(groups.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(groupHtml)
      .join("");
  }

  /**
   * Restore clears the counter's whole statistics history and rebuilds it from the file —
   * an explicit confirmation is required, same as fix, and it names both the counter and
   * the file so there is no ambiguity about what is about to be overwritten.
   */
  async _restoreBackup(file, statId) {
    const T = this._t;
    const msg = this.querySelector("#st-bk-msg");
    if (!window.confirm(T.restoreConfirm.replace("{id}", statId).replace("{file}", file))) return;
    const stop = this._startWorking((t) => (msg.textContent = t), T.working);
    try {
      const r = await this._service("restore", { backup_file: file, confirm: true });
      msg.textContent = `${T.restoreDone}: ${this._n(r.restored_points)} ${T.points}`;
      stop(); // before _loadBackups() below — otherwise its own await keeps the ticker
      // running against this now-settled message and stomps "restoreDone" with a stale tick.
      await this._loadBackups(); // the restore itself created a new pre-restore snapshot
    } catch (e) {
      stop();
      msg.textContent = `${T.err}: ${e.message || e}`;
    }
  }

  async _makeBackup() {
    const T = this._t;
    const msg = this.querySelector("#st-bk-msg");
    const btn = this.querySelector("#st-bk-make");
    const ids = Array.from(this._bkSelected || []);
    if (!ids.length) {
      msg.textContent = T.pickTip;
      return;
    }
    btn.disabled = true;
    let done = 0;
    const failed = [];
    for (const id of ids) {
      msg.textContent = `${T.working} (${done + 1}/${ids.length}) ${id}`;
      try {
        // One service call per counter: each backup is a separate, full-history file —
        // never a combined snapshot of several counters in one.
        await this._service("backup", { statistic_id: id });
        done++;
      } catch (e) {
        failed.push(id);
      }
    }
    btn.disabled = false;
    msg.textContent = failed.length
      ? `${T.bkDone}: ${done}/${ids.length}. ${T.err}: ${failed.join(", ")}`
      : `${T.bkDone}: ${done}/${ids.length}`;
    await this._loadBackups();
  }

  /** Enabled purely on simulation mode: unlike Fix/Restore, the two ids here are typed in
   *  freely rather than picked from the current counter, so the per-id allowlist can only be
   *  checked once the service call actually runs — a real rejection still surfaces through
   *  the error message, this just avoids offering the button when writing is off entirely. */
  _updateTransferButton() {
    const btn = this.querySelector("#st-transfer-btn");
    if (!btn) return;
    const writable = !(this._writeStatus || { readOnly: true }).readOnly;
    btn.disabled = !writable;
    btn.title = writable ? "" : this._t.fixDisabledTip;
  }

  async _transfer() {
    const T = this._t;
    const msg = this.querySelector("#st-transfer-msg");
    const from = this.querySelector("#st-transfer-from").value.trim();
    const to = this.querySelector("#st-transfer-to").value.trim();
    if (!from || !to) {
      msg.textContent = T.pickTip;
      return;
    }
    if (!window.confirm(T.transferConfirm.replaceAll("{from}", from).replaceAll("{to}", to))) {
      return;
    }
    const btn = this.querySelector("#st-transfer-btn");
    btn.disabled = true;
    const stop = this._startWorking((t) => (msg.textContent = t), T.working);
    try {
      const r = await this._service("transfer", {
        from_statistic_id: from,
        to_statistic_id: to,
        confirm: true,
      });
      msg.textContent = `${T.transferDone}: ${this._n(r.transferred_points)} ${T.points}`;
      this.querySelector("#st-transfer-from").value = "";
      this.querySelector("#st-transfer-to").value = "";
      stop(); // before _loadBackups() below — otherwise its own await keeps the ticker
      // running against this now-settled message and stomps "transferDone" with a stale tick.
      await this._loadBackups(); // the source's pre-transfer snapshot shows up here
    } catch (e) {
      stop();
      msg.textContent = `${T.err}: ${e.message || e}`;
    }
    this._updateTransferButton(); // restore the correct disabled state, not just "enabled"
  }

  // ---- configuration --------------------------------------------------------
  // Editable here, not just displayed: that is the point of this tab — set_config writes
  // straight to the config entry, so nothing requires a detour through Settings.
  async _loadStatus() {
    const T = this._t;
    const box = this.querySelector("#st-cfg");
    if (!box) return;
    box.innerHTML = `<div class="st-hint">${T.loading}</div>`;
    try {
      const r = await this._service("status");
      const allow = (r.write_allowlist || []).join("\n");
      const row = (label, value) =>
        `<div class="st-cfg-row"><b>${this._esc(label)}</b><span>${value}</span></div>`;
      box.innerHTML = `
        <label class="st-cfg-check">
          <input type="checkbox" id="st-cfg-ro" ${r.read_only ? "checked" : ""}>
          ${this._esc(T.cfgSimToggle)}
        </label>
        <label class="st-cfg-label">${this._esc(T.cfgAllowEdit)}</label>
        <textarea id="st-cfg-allow" class="st-cfg-textarea" rows="4"
          placeholder="${this._esc(T.cfgAllowPh)}">${this._esc(allow)}</textarea>
        <label class="st-cfg-check">
          <input type="checkbox" id="st-cfg-admin" ${r.admin_only ? "checked" : ""}>
          ${this._esc(T.cfgAdminToggle)}
        </label>
        <div class="st-actions">
          <button class="st-btn" id="st-cfg-save">${T.cfgSave}</button>
          <span class="st-hint" id="st-cfg-msg"></span>
        </div>
        <div style="margin-top:18px">
          ${row(T.cfgVia, this._esc(r.configured_via || "-"))}
          ${row(T.cfgDir, `<span class="st-file">${this._esc(r.backup_dir || "")}</span>`)}
          ${row(T.cfgCount, this._n(r.backup_count))}
        </div>`;
      this.querySelector("#st-cfg-save").addEventListener("click", () => this._saveConfig());
    } catch (e) {
      box.innerHTML = `<div class="st-err">${this._esc(String(e.message || e))}</div>`;
    }
  }

  /**
   * The write-status banner on the main tab used to be a string baked in at first render,
   * never touching the live status — so it kept saying "simulation only" even after write
   * mode was switched on. It now asks the status service, same as the config tab does.
   */
  async _refreshWarnBanner() {
    const T = this._t;
    const el = this.querySelector("#st-warn");
    try {
      const r = await this._service("status");
      this._writeStatus = { readOnly: !!r.read_only, allowlist: r.write_allowlist || [] };
      if (el) {
        el.textContent = r.read_only
          ? T.warnSim
          : this._writeStatus.allowlist.length
          ? T.warnWrite.replace("{ids}", this._writeStatus.allowlist.join(", "))
          : T.warnWriteAll;
      }
    } catch (e) {
      this._writeStatus = { readOnly: true, allowlist: [] }; // fail safe: assume the stricter state
      if (el) el.textContent = T.warnSim;
    }
    this._updateFixButton();
    this._updateTransferButton();
    // Re-gate already-rendered restore buttons too, without a network round trip — the
    // rows themselves haven't changed, only which counters are currently writable.
    if (this._bkRows) this._renderBkTable();
  }

  /** Fix is only ever enabled when simulation mode is off AND this counter is allowed —
   *  never inferred from anything the user can't see, so it can't silently drift out of
   *  sync with what the backend would actually accept. */
  _updateFixButton() {
    const btn = this.querySelector("#st-fix");
    if (!btn) return;
    const status = this._writeStatus || { readOnly: true, allowlist: [] };
    const statId = (this.querySelector("#st-stat") || {}).value || "";
    const writable =
      !status.readOnly && (!status.allowlist.length || status.allowlist.includes(statId));
    btn.disabled = !writable || !statId;
    btn.title = writable ? "" : this._t.fixDisabledTip;
    this._updateWizFixButton(status);
  }

  /** Same gating as the manual tab's Fix/Restore buttons, keyed on the counter the guided
   *  workflow itself picked (this._wizStatId) rather than #st-stat's — the two tabs never
   *  share a visible counter selection, but they share the write-status source of truth.
   *  Gates both step 3 (Fix) and step 4's rollback (Restore) — both write, both need it. */
  _updateWizFixButton(status) {
    status = status || this._writeStatus || { readOnly: true, allowlist: [] };
    const statId = this._wizStatId || "";
    const writable =
      !status.readOnly && (!status.allowlist.length || status.allowlist.includes(statId));
    for (const id of ["st-wiz-fix", "st-wiz-rollback"]) {
      const btn = this.querySelector(`#${id}`);
      if (!btn) continue;
      btn.disabled = !writable || !statId;
      btn.title = writable ? "" : this._t.fixDisabledTip;
    }
  }

  async _saveConfig() {
    const T = this._t;
    const msg = this.querySelector("#st-cfg-msg");
    const readOnly = this.querySelector("#st-cfg-ro").checked;
    const allowText = this.querySelector("#st-cfg-allow").value;
    const allowlist = allowText
      .split(/[\n,]/)
      .map((s) => s.trim())
      .filter(Boolean);
    const adminOnly = this.querySelector("#st-cfg-admin").checked;
    msg.textContent = T.working;
    try {
      await this._service("set_config", {
        read_only: readOnly,
        write_allowlist: allowlist,
        admin_only: adminOnly,
      });
      msg.textContent = T.cfgSaved;
      await this._loadStatus();
      await this._refreshWarnBanner(); // the sim tab's banner must not go stale
    } catch (e) {
      msg.textContent = `${T.err}: ${e.message || e}`;
    }
  }

  /** Escape text that goes into innerHTML (entity ids come from the backend). */
  _esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  /** A timestamp in the viewer's locale — ISO with +00:00 is not for humans. */
  _localTs(iso) {
    const d = new Date(iso);
    return isNaN(d.getTime()) ? this._esc(iso) : d.toLocaleString();
  }

  /**
   * Detection status as compact badges in their own row. Details go into the tooltip
   * rather than into a wrapping paragraph, which previously stretched the grid cell.
   */
  _renderStatus(d) {
    const el = this.querySelector("#st-status");
    if (!el) return;
    const T = this._t;
    const chain = d.source_chain || [];
    const guessed = String(d.cycle_via || "").startsWith("name_guess");
    const badge = (cls, text, tip) =>
      `<span class="st-badge ${cls}"${tip ? ` title="${this._esc(tip)}"` : ""}>${this._esc(text)}</span>`;

    const parts = [
      d.source_detected
        ? badge("ok", `✓ ${T.srcAuto}`, chain.join("  →  "))
        : badge("", `• ${T.srcSelf}`, T.tSource),
      guessed
        ? badge("warn", `⚠ ${T.cycleGuessedShort}`, T.cycleGuessed)
        : badge("ok", `✓ ${T.cycleReadShort}`, T.cycleRead),
    ];
    // A counter whose source reaches further back can have its history extended.
    if (d.source_start && d.counter_start && new Date(d.source_start) < new Date(d.counter_start)) {
      parts.push(
        badge("", `↥ ${T.extendable}`, `${T.counterFrom} ${this._localTs(d.counter_start)}\n${T.sourceFrom} ${this._localTs(d.source_start)}`)
      );
    }
    if (chain.length > 1) {
      const txt = chain.join(" → ");
      parts.push(`<span class="st-chain" title="${this._esc(txt)}">${this._esc(txt)}</span>`);
    }
    el.innerHTML = parts.join("");
  }

  /** Grey out presets that lie entirely outside the counter's detected data range. */
  _markRangePresets() {
    const r = this._detectedRange;
    const first = r && r.start ? new Date(r.start) : null;
    this.querySelectorAll("[data-range]").forEach((b) => {
      const preset = b.dataset.range;
      const range = this._presetRange(preset);
      const empty = first && range && range.e < first;
      b.disabled = !!empty;
      b.classList.toggle("off", !!empty);
      b.title = empty
        ? `${this._t.noData} ${first.toLocaleDateString()}`
        : preset === "all"
        ? this._t.tAll
        : b.title;
    });
  }

  _setSelectValue(sel, value) {
    if (!sel) return;
    if (value && !Array.from(sel.options).some((o) => o.value === value)) {
      const o = document.createElement("option");
      o.value = value;
      o.textContent = value;
      sel.appendChild(o);
    }
    sel.value = value || "";
  }

  // ---- sensor filtering --------------------------------------------------
  _matches(id, pattern) {
    const p = (pattern || "").trim().toLowerCase();
    if (!p) return true;
    const s = id.toLowerCase();
    if (p.includes("*")) {
      const rx =
        "^" +
        p.split("*").map((x) => x.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*") +
        "$";
      try {
        return new RegExp(rx).test(s);
      } catch (e) {
        return s.includes(p.replace(/\*/g, ""));
      }
    }
    return s.includes(p);
  }

  _isEnergy(id) {
    const state = this._hass.states[id];
    if (state) {
      const a = state.attributes || {};
      const u = String(a.unit_of_measurement || "").toLowerCase();
      return a.device_class === "energy" || ["kwh", "wh", "mwh"].includes(u);
    }
    // No live entity (an orphaned statistic) — the recorder's own metadata still knows
    // the unit, so this doesn't have to fall back to "not energy" by default.
    const meta = this._statMeta.get(id);
    const u = String(
      (meta && (meta.unit_of_measurement || meta.display_unit_of_measurement)) || ""
    ).toLowerCase();
    return ["kwh", "wh", "mwh"].includes(u);
  }

  /** Every sensor.* the recorder knows about, live entity or orphaned statistic alike. */
  _allSensorIds() {
    const fromStates = Object.keys(this._hass.states).filter((e) => e.startsWith("sensor."));
    const fromStats = Array.from(this._statMeta.keys()).filter((e) => e.startsWith("sensor."));
    return Array.from(new Set([...fromStates, ...fromStats]));
  }

  _counterIds() {
    return this._allSensorIds()
      .filter((e) => !this._energyOnly || this._isEnergy(e))
      .filter((e) => this._matches(e, this._filterText))
      .sort();
  }

  _energyIds() {
    return this._allSensorIds()
      .filter((e) => this._isEnergy(e))
      .sort();
  }

  _counterOptions(selected) {
    const ids = this._counterIds();
    return (
      `<option value="">${this._t.pick} (${ids.length})</option>` +
      ids
        .map((id) => `<option value="${id}"${id === selected ? " selected" : ""}>${id}</option>`)
        .join("")
    );
  }

  _sourceOptions(selected) {
    return (
      `<option value="">${this._t.selfMode}</option>` +
      this._energyIds()
        .map((id) => `<option value="${id}"${id === selected ? " selected" : ""}>${id}</option>`)
        .join("")
    );
  }

  /** Every tab's filter row (search box + energy-only chip) and every counter <select>
   *  shares the same _filterText/_energyOnly state and the same filtered id list — filter
   *  once, it applies wherever a counter is picked, instead of each tab inventing its own
   *  filtering behaviour. Called after any change to that shared state, or to the filtered
   *  set itself (e.g. a fresh recorder/list_statistic_ids fetch). */
  _refreshCounters() {
    const count = this._counterIds().length;
    const matchText = `${count} ${this._t.matches}`;

    // #st-transfer-from lists the same ids as every other picker on purpose: an orphaned
    // statistic_id (no live entity left) is exactly what you transfer *from*, and
    // _counterOptions() already includes those via _allSensorIds()/_statMeta.
    for (const id of ["st-stat", "st-wiz-stat", "st-transfer-from", "st-transfer-to"]) {
      const sel = this.querySelector(`#${id}`);
      if (sel) sel.innerHTML = this._counterOptions(sel.value);
    }
    for (const id of ["st-filter", "st-bk-filter", "st-wiz-filter", "st-transfer-filter"]) {
      const el = this.querySelector(`#${id}`);
      if (el && el.value !== this._filterText) el.value = this._filterText;
    }
    for (const id of ["st-energy", "st-bk-energy", "st-wiz-energy", "st-transfer-energy"]) {
      const el = this.querySelector(`#${id}`);
      if (el) el.classList.toggle("on", this._energyOnly);
    }
    for (const id of ["st-count", "st-wiz-count", "st-transfer-count"]) {
      const el = this.querySelector(`#${id}`);
      if (el) el.textContent = matchText;
    }

    // Backups tab: its own picklist + count (selection count on top of the match count),
    // kept in sync so switching tabs never shows a stale filter value or a list built from
    // the old filter.
    this._renderBkPicklist();
    if (this._bkRows) this._renderBkTable(); // only after the list has actually been fetched
    const bkCount = this.querySelector("#st-bk-matchcount");
    if (bkCount) {
      const selected = (this._bkSelected || new Set()).size;
      bkCount.textContent = selected
        ? `${matchText} · ${this._t.selectedCount.replace("{n}", selected)}`
        : matchText;
    }
  }

  /** Wires one filter row (search input + energy-only toggle chip) to the shared
   *  _filterText/_energyOnly state — see _refreshCounters(). Every tab with a counter
   *  picker calls this once with its own element ids; missing ids are silently skipped so
   *  a tab without a match-count span or without an energy toggle still works. */
  _wireFilterRow(filterId, energyId) {
    const filter = this.querySelector(`#${filterId}`);
    if (filter) {
      filter.addEventListener("input", (e) => {
        this._filterText = e.target.value;
        this._refreshCounters();
      });
    }
    const energy = this.querySelector(`#${energyId}`);
    if (energy) {
      energy.addEventListener("click", (e) => {
        this._energyOnly = !this._energyOnly;
        e.target.classList.toggle("on", this._energyOnly);
        this._refreshCounters();
      });
    }
  }

  // ---- auto-detection ----------------------------------------------------
  async _autodetect(statId) {
    if (!statId) return;
    try {
      const res = await this._hass.callService(
        "statistics_toolset",
        "detect",
        { statistic_id: statId },
        undefined,
        false,
        true
      );
      const d = res.response || res;
      this._detectedRange = { start: d.start, end: d.end }; // for the "all" range preset
      this._setSelectValue(this.querySelector("#st-ref"), d.reference_id || "");
      const cyc = this.querySelector("#st-cycle");
      if (cyc && d.cycle) cyc.value = d.cycle;
      if (d.start) this.querySelector("#st-start").value = this._isoToLocal(d.start);
      if (d.end) this.querySelector("#st-end").value = this._isoToLocal(d.end);
      this._renderStatus(d);
      this._markRangePresets();
    } catch (e) {
      /* leave fields as they are */
    }
  }

  // ---- guided workflow ----------------------------------------------------
  // A separate, self-contained tab next to the manual Read/Fix/Backups/Transfer tabs —
  // not a replacement for them. It walks 1 Read -> 2 Backup -> 3 Fix -> 4 Recheck &
  // decide, calling the exact same services those manual tabs use, just in a fixed order
  // with nothing to forget. Reuses #st-ref/#st-cycle/#st-start/#st-end as an internal
  // auto-detection scratchpad (via the existing _autodetect()/_readFormData()) — the
  // guided flow deliberately never shows or lets you edit them; that is the difference
  // from the manual tab, which exists precisely for when you *do* want to override them.

  _setWizStep(step) {
    this._wizStep = step;
    this.querySelectorAll("[data-wiz-panel]").forEach((p) => {
      p.hidden = Number(p.dataset.wizPanel) !== step;
    });
    this.querySelectorAll(".st-wizard-step").forEach((el) => {
      el.classList.toggle("on", Number(el.dataset.step) === step);
    });
  }

  async _wizRun() {
    const T = this._t;
    const statId = this.querySelector("#st-wiz-stat").value;
    const msg = this.querySelector("#st-wiz-run-msg");
    const err = this.querySelector("#st-wiz-err");
    err.textContent = "";
    if (!statId) {
      msg.textContent = T.pickTip;
      return;
    }
    this.querySelector("#st-stat").value = statId; // sync the shared scratchpad
    const btn = this.querySelector("#st-wiz-run");
    btn.disabled = true;
    const stop = this._startWorking((t) => (msg.textContent = t), T.running);
    try {
      await this._autodetect(statId);
      // Captured once, here — not re-read from the shared scratchpad in later steps, since
      // switching to the manual tab in between and changing source/cycle/range there must
      // never silently change what the guided flow goes on to write in step 3.
      this._wizData = this._readFormData();
      const preview = await this._service("simulate", this._wizData);
      this._renderResult(preview, "st-wiz-result");
      this._wizStatId = statId;
      msg.textContent = "";
      this._updateWizFixButton();
      this._setWizStep(2);
    } catch (e) {
      err.textContent = `${T.err}: ${e.message || e}`;
    } finally {
      stop();
      btn.disabled = false;
    }
  }

  async _wizBackup() {
    const T = this._t;
    const msg = this.querySelector("#st-wiz-backup-msg");
    const btn = this.querySelector("#st-wiz-backup");
    btn.disabled = true;
    const stop = this._startWorking((t) => (msg.textContent = t), T.working);
    try {
      const r = await this._service("backup", { statistic_id: this._wizStatId });
      this._wizBackupFile = r.backup_file;
      msg.textContent = `${T.bkDone}: ${this._esc(String(r.backup_file).split("/").pop())}`;
      this._setWizStep(3);
    } catch (e) {
      msg.textContent = `${T.err}: ${e.message || e}`;
    } finally {
      stop();
      btn.disabled = false;
    }
  }

  async _wizFix() {
    const T = this._t;
    const msg = this.querySelector("#st-wiz-fix-msg");
    const btn = this.querySelector("#st-wiz-fix");
    if (!window.confirm(T.fixConfirm.replace("{id}", this._wizStatId))) return;
    btn.disabled = true;
    const stop = this._startWorking((t) => (msg.textContent = t), T.working);
    try {
      const preview = await this._service("fix", { ...this._wizData, confirm: true });
      this._renderResult(preview, "st-wiz-result");
      msg.textContent = T.fixDone;
      stop(); // before the recheck call below — otherwise its own await keeps the ticker
      // running against this now-settled message and stomps "fixDone" with a stale tick.
      this._setWizStep(4);
      await this._wizRecheck();
    } catch (e) {
      stop();
      msg.textContent = `${T.err}: ${e.message || e}`;
    } finally {
      btn.disabled = false;
    }
  }

  /** Re-runs the read-only preview after a fix (or a rollback), so step 4 always shows
   *  the counter's actual current state rather than the write's own response. */
  async _wizRecheck() {
    try {
      const preview = await this._service("simulate", this._wizData);
      this._renderResult(preview, "st-wiz-result");
    } catch (e) {
      /* the fix/restore already reported its own result; leave that visible */
    }
  }

  async _wizRollback() {
    const T = this._t;
    const msg = this.querySelector("#st-wiz-decide-msg");
    if (!window.confirm(T.wizRollbackConfirm.replace("{id}", this._wizStatId))) return;
    const btn = this.querySelector("#st-wiz-rollback");
    btn.disabled = true;
    const stop = this._startWorking((t) => (msg.textContent = t), T.working);
    try {
      const r = await this._service("restore", {
        backup_file: this._wizBackupFile,
        confirm: true,
      });
      msg.textContent = `${T.restoreDone}: ${this._n(r.restored_points)} ${T.points}`;
      stop(); // before the recheck call below — otherwise its own await keeps the ticker
      // running against this now-settled message and stomps "restoreDone" with a stale tick.
      await this._wizRecheck();
    } catch (e) {
      stop();
      msg.textContent = `${T.err}: ${e.message || e}`;
    } finally {
      btn.disabled = false;
    }
  }

  _wizKeep() {
    // A real decision, not a neutral "close" — confirmed the same way Rollback is, so
    // neither of the two step-4 outcomes is a single accidental click away from the other.
    if (!window.confirm(this._t.wizKeepConfirm.replaceAll("{id}", this._wizStatId || ""))) return;
    this._wizReset();
  }

  /** Drops the in-progress workflow back to step 1. Used both when the user is done
   *  (Keep) and when the counter selection changes mid-flow (see the #st-wiz-stat change
   *  listener) — a stale _wizData/_wizStatId/_wizBackupFile tied to a *different* counter
   *  than the one now shown in the picker would otherwise silently carry over into Fix. */
  _wizReset() {
    this._wizBackupFile = null;
    this._wizStatId = null;
    this._wizData = null;
    this.querySelector("#st-wiz-run-msg").textContent = "";
    this.querySelector("#st-wiz-backup-msg").textContent = "";
    this.querySelector("#st-wiz-fix-msg").textContent = "";
    this.querySelector("#st-wiz-decide-msg").textContent = "";
    this._updateWizFixButton();
    this._setWizStep(1);
  }

  // ---- rendering ---------------------------------------------------------
  _build() {
    this._built = true;
    const T = this._t;
    const choice = this._storedLangChoice();
    const now = new Date();
    const yearStart = new Date(now.getFullYear(), 0, 1, 0, 0);
    const info = (tip) => `<span class="st-i" title="${tip}">&#9432;</span>`;
    const field = (label, tip, control, extra = "") =>
      `<label><span class="st-fl">${label} ${info(tip)}${extra}</span>${control}</label>`;

    this.innerHTML = `
      <style>
        .st-wrap{max-width:980px;margin:0 auto;padding:22px;box-sizing:border-box;width:100%;
          font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif);color:var(--primary-text-color);font-size:16px;}
        .st-wrap *{box-sizing:border-box;}
        [data-pane="sim"],[data-pane="workflow"]{font-size:15px;} /* one notch below the 16px shared by Backups/Config */
        .st-card{background:var(--card-background-color,#fff);border-radius:14px;
          box-shadow:var(--ha-card-box-shadow,0 2px 6px rgba(0,0,0,.15));padding:22px;margin-bottom:18px;}
        .st-top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;}
        .st-langbox{display:inline-flex;align-items:center;gap:7px;white-space:nowrap;}
        .st-tabs{display:flex;flex-wrap:wrap;gap:4px;border-bottom:2px solid var(--divider-color,#ccc);
          margin:18px 0 0;}
        .st-tab{background:none;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;
          padding:10px 16px;font-size:1em;font-weight:500;cursor:pointer;color:var(--secondary-text-color);}
        .st-tab:hover{color:var(--primary-text-color);}
        .st-tab.on{color:var(--primary-color,#03a9f4);border-bottom-color:var(--primary-color,#03a9f4);}
        .st-intro{font-size:.97em;color:var(--secondary-text-color);line-height:1.5;
          margin:14px 0 18px;padding-left:12px;border-left:3px solid var(--primary-color,#03a9f4);}
        .st-table{width:100%;border-collapse:collapse;font-size:.95em;margin-top:12px;}
        .st-table th,.st-table td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--divider-color,#ccc);}
        .st-table th{color:var(--secondary-text-color);font-weight:500;}
        .st-table td.num{text-align:right;font-variant-numeric:tabular-nums;}
        .st-tag{font-size:.92em;padding:2px 8px;border-radius:12px;background:var(--secondary-background-color,#f5f5f5);
          border:1px solid var(--divider-color,#ccc);}
        .st-tag-warn{border-color:var(--warning-color,#ffa600);color:var(--warning-color,#ffa600);}
        .st-file{font-family:ui-monospace,monospace;font-size:.92em;white-space:nowrap;
          overflow:hidden;text-overflow:ellipsis;max-width:170px;}
        .st-table-wrap{overflow-x:auto;} /* safety net if a column still overflows narrow screens */
        .st-cfg-row{display:flex;gap:12px;padding:9px 0;border-bottom:1px solid var(--divider-color,#ccc);}
        .st-cfg-row b{min-width:230px;font-weight:500;}
        .st-cfg-check{display:flex;align-items:center;gap:9px;font-size:1em;cursor:pointer;margin-bottom:14px;}
        .st-cfg-check input{width:18px;height:18px;cursor:pointer;}
        .st-cfg-label{display:block;font-size:.9em;color:var(--secondary-text-color);margin-bottom:6px;}
        .st-cfg-textarea{width:100%;box-sizing:border-box;padding:9px;border-radius:8px;
          border:1px solid var(--divider-color,#ccc);background:var(--secondary-background-color,#f5f5f5);
          color:var(--primary-text-color);font-size:.9em;font-family:ui-monospace,monospace;resize:vertical;}
        .st-bk-picklist{margin:12px 0;}
        .st-bk-hint{padding:10px 2px;}
        .st-bk-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;}
        .st-bk-chip{display:inline-flex;align-items:center;gap:6px;background:var(--primary-color,#03a9f4);
          color:var(--text-primary-color,#fff);border-color:transparent;padding:6px 8px 6px 12px;}
        .st-bk-chip-x{background:none;border:none;color:inherit;cursor:pointer;font-size:1.1em;
          line-height:1;padding:0 2px;opacity:.85;}
        .st-bk-chip-x:hover{opacity:1;}
        .st-bk-dropdown{max-height:320px;overflow-y:auto;border:1px solid var(--divider-color,#ccc);
          border-radius:8px;padding:4px;background:var(--secondary-background-color,#f5f5f5);
          display:flex;flex-direction:column;gap:2px;}
        .st-bk-option{display:block;width:100%;box-sizing:border-box;text-align:left;
          background:none;border:none;border-radius:6px;padding:7px 10px;font-size:.95em;
          color:var(--primary-text-color);cursor:pointer;}
        .st-bk-option:hover{background:var(--card-background-color,#fff);}
        .st-bk-option.picked{color:var(--primary-color,#03a9f4);font-weight:500;}
        .st-bk-more{padding:4px 10px;font-size:.9em;}
        .st-bk-bulk{display:flex;gap:4px;margin-top:2px;border-top:1px solid var(--divider-color,#ccc);
          padding-top:4px;}
        .st-bk-selectall{flex:1;background:none;border:none;padding:8px 10px;font-size:.95em;
          color:var(--primary-color,#03a9f4);cursor:pointer;text-align:left;border-radius:6px;}
        .st-bk-selectall:hover{background:var(--card-background-color,#fff);text-decoration:underline;}
        .st-bk-group{border:1px solid var(--divider-color,#ccc);border-radius:8px;margin-bottom:8px;
          overflow:hidden;}
        .st-bk-group-summary{display:flex;align-items:center;gap:10px;padding:9px 12px;
          cursor:pointer;background:var(--secondary-background-color,#f5f5f5);flex-wrap:wrap;}
        .st-bk-group-summary:hover{background:var(--card-background-color,#fff);}
        .st-bk-group-chevron{color:var(--secondary-text-color);width:1em;flex:none;}
        .st-bk-group-name{font-weight:500;flex:1 1 auto;min-width:160px;
          overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
        .st-bk-group-detail{display:none;padding:0 12px 12px;}
        .st-bk-group.open .st-bk-group-detail{display:block;}
        .st-bk-group.open .st-bk-group-chevron{transform:none;}
        .st-bk-group-restore{margin-left:auto;}
        .st-h{font-size:1.85em;font-weight:500;margin:0 0 4px;}
        .st-sub{color:var(--secondary-text-color);margin:0 0 14px;font-size:1em;}
        .st-warn{background:var(--warning-color,#ffa600);color:#111;border-radius:8px;
          padding:11px 13px;font-size:.95em;margin-bottom:18px;}
        .st-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px;}
        .st-row input[type=search]{flex:1 1 260px;min-width:0;padding:11px;border-radius:8px;
          border:1px solid var(--divider-color,#ccc);background:var(--secondary-background-color,#f5f5f5);
          color:var(--primary-text-color);font-size:1em;}
        .st-chip{padding:9px 14px;border-radius:20px;border:1px solid var(--divider-color,#ccc);
          background:var(--secondary-background-color,#f5f5f5);color:var(--primary-text-color);
          font-size:.95em;cursor:pointer;white-space:nowrap;}
        .st-chip:hover{border-color:var(--primary-color,#03a9f4);}
        .st-chip.on{background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff);border-color:transparent;}
        .st-chip.off,.st-chip:disabled{opacity:.4;cursor:not-allowed;text-decoration:line-through;}
        .st-wizard-step{cursor:default;}
        .st-wizard-step:hover{border-color:var(--divider-color,#ccc);}
        /* Action buttons (st-btn/st-btn2/st-bk-restore-btn) are rounded rectangles; pills
           (st-chip) are reserved for filters/toggles — restore is a destructive action like
           Fix, so it shares that shape and st-btn-fix's red, just sized for a table row. */
        .st-bk-restore-btn{background:var(--error-color,#db4437);color:#fff;border:none;
          border-radius:8px;padding:8px 14px;font-size:.95em;font-weight:500;cursor:pointer;
          white-space:nowrap;}
        .st-bk-restore-btn:disabled{background:var(--disabled-color,#888);opacity:.6;
          cursor:not-allowed;}
        .st-chip.off:hover{border-color:var(--divider-color,#ccc);}
        .st-note{background:var(--secondary-background-color,#f5f5f5);border-left:3px solid var(--warning-color,#ffa600);
          border-radius:6px;padding:9px 12px;margin:0 0 14px;font-size:.97em;color:var(--primary-text-color);}
        .st-count{font-size:.95em;color:var(--secondary-text-color);white-space:nowrap;}
        .st-lbl{font-size:.95em;color:var(--secondary-text-color);white-space:nowrap;}
        .st-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;align-items:start;}
        .st-grid label{display:flex;flex-direction:column;gap:6px;min-width:0;}
        .st-fl{display:inline-flex;align-items:center;font-size:.95em;color:var(--secondary-text-color);}
        .st-i{margin-left:6px;cursor:help;color:var(--primary-color,#03a9f4);font-size:1.15em;font-weight:700;}
        .st-i:hover{filter:brightness(1.2);}
        /* Status lives in its own full-width row: putting it inside a grid cell made that
           cell taller and pushed the neighbouring fields out of line. min-height reserves
           the space so nothing jumps once detection returns. */
        .st-status{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:14px 0 0;min-height:26px;}
        .st-badge{display:inline-flex;align-items:center;gap:5px;white-space:nowrap;font-size:.92em;
          padding:3px 9px;border-radius:20px;background:var(--secondary-background-color,#f5f5f5);
          border:1px solid var(--divider-color,#ccc);color:var(--secondary-text-color);}
        .st-badge.ok{border-color:var(--success-color,#43a047);color:var(--success-color,#43a047);}
        .st-badge.warn{border-color:var(--warning-color,#ffa600);color:var(--warning-color,#ffa600);}
        .st-chain{font-size:.88em;color:var(--secondary-text-color);font-family:ui-monospace,monospace;
          white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;flex:1 1 auto;min-width:0;}
        .st-grid select,.st-grid input{width:100%;min-width:0;padding:11px;border-radius:8px;
          border:1px solid var(--divider-color,#ccc);background:var(--secondary-background-color,#f5f5f5);
          color:var(--primary-text-color);font-size:1em;}
        .st-actions{display:flex;gap:12px;align-items:center;margin-top:20px;flex-wrap:wrap;}
        .st-btn{background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff);
          border:none;border-radius:8px;padding:13px 26px;font-size:.95em;font-weight:500;cursor:pointer;}
        .st-btn:disabled{opacity:.6;cursor:default;}
        .st-btn-fix{background:var(--error-color,#db4437);}
        .st-btn-fix:disabled{background:var(--disabled-color,#888);}
        .st-btn2{background:transparent;color:var(--primary-color,#03a9f4);border:1px solid var(--primary-color,#03a9f4);
          border-radius:8px;padding:12px 18px;font-size:.95em;cursor:pointer;}
        .st-lang{font-size:.95em;padding:6px 9px;border-radius:8px;border:1px solid var(--divider-color,#ccc);
          background:var(--secondary-background-color,#f5f5f5);color:var(--primary-text-color);}
        .st-kpis{display:flex;flex-wrap:wrap;gap:24px;margin:6px 0 18px;}
        .st-kpi{font-size:.95em;color:var(--secondary-text-color);}
        .st-kpi b{display:block;font-size:1.6em;color:var(--primary-text-color);margin-top:2px;}
        .st-graph-h{font-size:1em;margin:16px 0 4px;font-weight:500;}
        .st-empty{font-size:.95em;color:var(--secondary-text-color);border:1px dashed var(--divider-color,#ccc);
          border-radius:8px;padding:14px;text-align:center;}
        .st-hint{color:var(--secondary-text-color);font-size:1em;}
        .st-err{color:var(--error-color,#db4437);font-size:.95em;margin-top:10px;white-space:pre-wrap;}
      </style>
      <div class="st-wrap">
        <div class="st-card">
          <div class="st-top">
            <div>
              <div class="st-h">${T.title}</div>
              <div class="st-sub">${T.subtitle}</div>
            </div>
            <div class="st-langbox">
              <span class="st-lbl">${T.langLabel}</span>
              <select id="st-lang" class="st-lang">
                <option value="auto"${choice === "auto" ? " selected" : ""}>🌐 Auto</option>
                <option value="de"${choice === "de" ? " selected" : ""}>Deutsch</option>
                <option value="en"${choice === "en" ? " selected" : ""}>English</option>
              </select>
            </div>
          </div>

          <div class="st-tabs">
            <button class="st-tab" data-tab="workflow">${T.tabWorkflow}</button>
            <button class="st-tab" data-tab="sim">${T.tabSim}</button>
            <button class="st-tab" data-tab="backups">${T.tabBackups}</button>
            <button class="st-tab" data-tab="transfer">${T.tabTransfer}</button>
            <button class="st-tab" data-tab="config">${T.tabConfig}</button>
          </div>
          <div class="st-intro" id="st-intro"></div>

          <div data-pane="workflow" hidden>
            <div class="st-row" id="st-wiz-steps">
              <span class="st-chip st-wizard-step" data-step="1">1 · ${T.wizStep1}</span>
              <span class="st-chip st-wizard-step" data-step="2">2 · ${T.wizStep2}</span>
              <span class="st-chip st-wizard-step" data-step="3">3 · ${T.wizStep3}</span>
              <span class="st-chip st-wizard-step" data-step="4">4 · ${T.wizStep4}</span>
            </div>

            <div class="st-row">
              <input id="st-wiz-filter" type="search" placeholder="${T.filterPh}" value="${this._filterText}">
              <button class="st-chip${this._energyOnly ? " on" : ""}" id="st-wiz-energy">${T.energyOnly}</button>
              <span class="st-count" id="st-wiz-count"></span>
            </div>
            <div class="st-grid">
              ${field(T.counter, T.tCounter, `<select id="st-wiz-stat">${this._counterOptions("")}</select>`)}
            </div>

            <div class="st-wiz-panel" data-wiz-panel="1">
              <div class="st-actions">
                <button class="st-btn" id="st-wiz-run">${T.run}</button>
                <span class="st-hint" id="st-wiz-run-msg"></span>
              </div>
            </div>

            <div class="st-wiz-panel" data-wiz-panel="2" hidden>
              <div class="st-actions">
                <button class="st-btn" id="st-wiz-backup">${T.wizBackupNow}</button>
                <span class="st-hint" id="st-wiz-backup-msg"></span>
              </div>
            </div>

            <div class="st-wiz-panel" data-wiz-panel="3" hidden>
              <div class="st-actions">
                <button class="st-btn st-btn-fix" id="st-wiz-fix" disabled title="${T.fixDisabledTip}">${T.fix}</button>
                <span class="st-hint" id="st-wiz-fix-msg"></span>
              </div>
            </div>

            <div class="st-wiz-panel" data-wiz-panel="4" hidden>
              <div class="st-actions">
                <button class="st-btn st-btn-fix" id="st-wiz-rollback" disabled title="${T.fixDisabledTip}">${T.wizRollback}</button>
                <button class="st-btn" id="st-wiz-keep">${T.wizKeep}</button>
                <span class="st-hint" id="st-wiz-decide-msg"></span>
              </div>
            </div>

            <div class="st-err" id="st-wiz-err"></div>
            <div id="st-wiz-result"></div>
          </div>

          <div data-pane="sim">
          <div class="st-warn" id="st-warn">${T.loading}</div>

          <div class="st-row">
            <input id="st-filter" type="search" placeholder="${T.filterPh}" value="${this._filterText}">
            <button class="st-chip${this._energyOnly ? " on" : ""}" id="st-energy">${T.energyOnly}</button>
            <span class="st-count" id="st-count"></span>
          </div>

          <div class="st-grid">
            ${field(T.counter, T.tCounter, `<select id="st-stat">${this._counterOptions("")}</select>`)}
            ${field(T.source, T.tSource, `<select id="st-ref">${this._sourceOptions("")}</select>`)}
            ${field(
              T.cycle,
              T.tCycle,
              `<select id="st-cycle">
                <option value="yearly">yearly</option>
                <option value="quarterly">quarterly</option>
                <option value="bimonthly">bimonthly</option>
                <option value="monthly" selected>monthly</option>
                <option value="weekly">weekly</option>
                <option value="daily">daily</option>
                <option value="hourly">hourly</option>
                <option value="quarter-hourly">quarter-hourly</option>
                <option value="none">${T.cycleNone}</option>
              </select>`
            )}
            ${field(T.start, T.tStart, `<input id="st-start" type="datetime-local" value="${this._fmt(yearStart)}">`)}
            ${field(T.end, T.tEnd, `<input id="st-end" type="datetime-local" value="${this._fmt(now)}">`)}
          </div>

          <div class="st-status" id="st-status"></div>

          <div class="st-row" style="margin-top:14px;margin-bottom:0">
            <span class="st-lbl">${T.range}:</span>
            <button class="st-chip" data-range="all" title="${T.tAll}">${T.rAll}</button>
            <button class="st-chip" data-range="ytd">${T.rYtd}</button>
            <button class="st-chip" data-range="last" title="${now.getFullYear() - 1}">${T.rLast}</button>
            <button class="st-chip" data-range="y2" title="${now.getFullYear() - 2}">${T.rY2}</button>
            <button class="st-chip" data-range="mtd">${T.rMtd}</button>
            <button class="st-chip" data-range="12m">${T.r12}</button>
          </div>

          <div class="st-actions">
            <button class="st-btn" id="st-run">${T.run}</button>
            <button class="st-btn st-btn-fix" id="st-fix" disabled title="${T.fixDisabledTip}">${T.fix}</button>
            <button class="st-btn2" id="st-auto">${T.autodetect}</button>
            <span class="st-hint" id="st-fixmsg"></span>
            <span class="st-hint" style="font-size:.97em">${T.detHint}</span>
          </div>
          <div class="st-err" id="st-err"></div>
          </div>

          <div data-pane="backups" hidden>
            <div class="st-row">
              <input id="st-bk-filter" type="search" placeholder="${T.filterPh}" value="${this._filterText}">
              <button class="st-chip${this._energyOnly ? " on" : ""}" id="st-bk-energy">${T.energyOnly}</button>
              <span class="st-count" id="st-bk-matchcount"></span>
            </div>
            <div class="st-bk-picklist" id="st-bk-picklist"></div>
            <div class="st-actions">
              <button class="st-btn" id="st-bk-make">${T.makeBackup}</button>
              <button class="st-btn2" id="st-bk-reload">${T.reload}</button>
              <span class="st-hint" id="st-bk-msg"></span>
            </div>
            <div id="st-bk-list"></div>
          </div>

          <div data-pane="transfer" hidden>
            <div class="st-row">
              <input id="st-transfer-filter" type="search" placeholder="${T.filterPh}" value="${this._filterText}">
              <button class="st-chip${this._energyOnly ? " on" : ""}" id="st-transfer-energy">${T.energyOnly}</button>
              <span class="st-count" id="st-transfer-count"></span>
            </div>
            <div class="st-grid">
              ${field(T.transferFrom, T.tTransferFrom, `<select id="st-transfer-from">${this._counterOptions("")}</select>`)}
              ${field(T.transferTo, T.tTransferTo, `<select id="st-transfer-to">${this._counterOptions("")}</select>`)}
            </div>
            <div class="st-actions">
              <button class="st-btn st-btn-fix" id="st-transfer-btn" disabled title="${T.fixDisabledTip}">${T.transferBtn}</button>
              <span class="st-hint" id="st-transfer-msg"></span>
            </div>
          </div>

          <div data-pane="config" hidden>
            <div id="st-cfg"></div>
          </div>
        </div>
        <div id="st-result"><div class="st-card st-hint">${T.hint}</div></div>
      </div>`;

    this.querySelector("#st-run").addEventListener("click", () => this._run());
    this.querySelector("#st-fix").addEventListener("click", () => this._fix());
    this.querySelector("#st-lang").addEventListener("change", (e) => this._setLang(e.target.value));
    // Every tab with a counter picker gets the exact same filter row, wired to the same
    // shared _filterText/_energyOnly state — filter once, it applies everywhere a counter
    // is picked, instead of each tab inventing its own filtering behaviour.
    this._wireFilterRow("st-filter", "st-energy");
    this._wireFilterRow("st-bk-filter", "st-bk-energy");
    this._wireFilterRow("st-wiz-filter", "st-wiz-energy");
    this._wireFilterRow("st-transfer-filter", "st-transfer-energy");
    this.querySelector("#st-stat").addEventListener("change", (e) => {
      this._autodetect(e.target.value);
      this._updateFixButton(); // the allowlist is per-counter, so switching counters changes it
    });
    this.querySelector("#st-auto").addEventListener("click", () =>
      this._autodetect(this.querySelector("#st-stat").value)
    );
    this.querySelectorAll("[data-range]").forEach((b) =>
      b.addEventListener("click", () => this._setRange(b.dataset.range))
    );
    this.querySelectorAll("[data-tab]").forEach((b) =>
      b.addEventListener("click", () => this._setTab(b.dataset.tab))
    );
    this.querySelector("#st-bk-make").addEventListener("click", () => this._makeBackup());
    this.querySelector("#st-bk-reload").addEventListener("click", () => this._loadBackups());
    this.querySelector("#st-transfer-btn").addEventListener("click", () => this._transfer());
    this.querySelector("#st-wiz-run").addEventListener("click", () => this._wizRun());
    // Picking a different counter mid-flow must not silently keep going against the old
    // one — drop back to step 1 so "Read" has to run again for whatever is now selected.
    this.querySelector("#st-wiz-stat").addEventListener("change", () => {
      if (this._wizStep && this._wizStep !== 1) this._wizReset();
    });
    this.querySelector("#st-wiz-backup").addEventListener("click", () => this._wizBackup());
    this.querySelector("#st-wiz-fix").addEventListener("click", () => this._wizFix());
    this.querySelector("#st-wiz-keep").addEventListener("click", () => this._wizKeep());
    this.querySelector("#st-wiz-rollback").addEventListener("click", () => this._wizRollback());
    // Delegated: the picklist's innerHTML is replaced on every filter change, so binding to
    // the container (which itself persists) beats re-binding to each option/chip every time.
    this.querySelector("#st-bk-picklist").addEventListener("click", (e) =>
      this._onBkPicklistClick(e)
    );
    // Delegated for the same reason: the table's innerHTML is rebuilt on every reload.
    this.querySelector("#st-bk-list").addEventListener("click", (e) => {
      const btn = e.target.closest(".st-bk-restore-btn");
      if (btn) {
        if (!btn.disabled) this._restoreBackup(btn.dataset.file, btn.dataset.stat);
        return;
      }
      const summary = e.target.closest(".st-bk-group-summary");
      if (summary) this._toggleBkGroup(summary.dataset.stat);
    });
    this._refreshCounters();
    this._setTab(this._tab || "workflow");
    this._setWizStep(this._wizStep || 1);
    this._refreshWarnBanner();
  }

  /** The read-only analysis and the write share the same form fields. */
  _readFormData() {
    return {
      statistic_id: this.querySelector("#st-stat").value,
      reference_id: this.querySelector("#st-ref").value, // '' = self mode
      cycle: this.querySelector("#st-cycle").value,
      start: this.querySelector("#st-start").value.replace("T", " ") + ":00",
      end: this.querySelector("#st-end").value.replace("T", " ") + ":00",
    };
  }

  async _run() {
    const T = this._t;
    const btn = this.querySelector("#st-run");
    const err = this.querySelector("#st-err");
    err.textContent = "";
    const data = this._readFormData();
    if (!data.statistic_id) {
      err.textContent = T.pickTip;
      return;
    }
    btn.disabled = true;
    const stop = this._startWorking((t) => (btn.textContent = t), T.running);
    try {
      const res = await this._hass.callService(
        "statistics_toolset",
        "simulate",
        data,
        undefined,
        false,
        true
      );
      this._renderResult(res.response || res);
    } catch (e) {
      err.textContent = `${T.err}: ${e.message || e}`;
    } finally {
      stop();
      btn.disabled = false;
      btn.textContent = T.run;
    }
  }

  /**
   * Writes the repaired series. Only reachable when _updateFixButton() has already
   * determined this counter is writable, but that only ever enables the button — the
   * actual write still needs an explicit confirmation, since it changes the statistics
   * database and (per README/ARCHITECTURE) must never be silent.
   */
  async _fix() {
    const T = this._t;
    const btn = this.querySelector("#st-fix");
    const err = this.querySelector("#st-err");
    const fixmsg = this.querySelector("#st-fixmsg");
    err.textContent = "";
    fixmsg.textContent = "";
    const data = this._readFormData();
    if (!data.statistic_id) {
      err.textContent = T.pickTip;
      return;
    }
    if (!window.confirm(T.fixConfirm.replace("{id}", data.statistic_id))) return;
    btn.disabled = true;
    const label = btn.textContent;
    const stop = this._startWorking((t) => (btn.textContent = t), T.fixing);
    try {
      const res = await this._hass.callService(
        "statistics_toolset",
        "fix",
        { ...data, confirm: true },
        undefined,
        false,
        true
      );
      this._renderResult(res.response || res);
      fixmsg.textContent = T.fixDone;
    } catch (e) {
      err.textContent = `${T.err}: ${e.message || e}`;
    } finally {
      stop();
      btn.textContent = label;
      this._updateFixButton(); // restore the correct disabled state, not just "enabled"
    }
  }

  /**
   * Render a backend warning in the selected language. The backend sends {code, …} so the
   * text is chosen here — a bilingual string would show the other language too.
   */
  _warningText(w) {
    if (typeof w === "string") return this._esc(w); // pre-0.5 backend
    if (w && w.code === "start_moved_up") {
      return this._esc(this._t.wStartMoved.replace("{ts}", this._localTs(w.timestamp)));
    }
    if (w && w.code === "source_outliers_removed") {
      return this._esc(
        this._t.wSourceOutliers
          .replace("{count}", w.count)
          .replace("{amount}", this._n(w.amount))
      );
    }
    return this._esc((w && w.message) || "");
  }

  _renderResult(r, targetId = "st-result") {
    const T = this._t;
    const kpi = (label, val) => `<div class="st-kpi">${label}<b>${val}</b></div>`;
    const box = this.querySelector(`#${targetId}`);
    const notes = (r.warnings || []).length
      ? `<div class="st-note"><b>${T.notes}:</b><br>${(r.warnings || [])
          .map((w) => this._warningText(w))
          .join("<br>")}</div>`
      : "";
    box.innerHTML = `
      <div class="st-card">
        ${notes}
        <div class="st-kpis">
          ${kpi(T.outliers, r.outliers_found ?? "–")}
          ${
            r.source_outliers
              ? kpi(T.srcOutliers, `${r.source_outliers} · −${this._n(r.source_removed)}`)
              : ""
          }
          ${kpi(`${T.endsum} (${T.current})`, this._n(r.current_end_sum))}
          ${kpi(`${T.endsum} (${T.proposed})`, this._n(r.proposed_end_sum))}
          ${kpi(T.refdelta, this._n(r.reference_delta))}
          ${kpi(T.points, r.points ?? "–")}
        </div>
        <div class="st-graph-h">${T.current}${
      (r.outlier_periods || []).length ? ` <span class="st-tag st-tag-warn">⚠ ${T.outlierMarker}</span>` : ""
    }</div>
        ${this._svgBars(
          r.current_periods || [],
          "var(--error-color,#db4437)",
          T.emptyCurrent,
          r.outlier_periods
        )}
        <div class="st-graph-h">${T.proposed}</div>
        ${this._svgBars(r.proposed_periods || [], "var(--success-color,#43a047)", T.emptyProposed)}
      </div>`;
  }

  _n(v) {
    return v === undefined || v === null ? "–" : Number(v).toLocaleString();
  }

  /** outlierLabels: period labels (e.g. "2024-10") to draw in the warning color instead of
   *  the normal series color — "1 outlier" alone doesn't say *where*; this points at it
   *  directly instead of leaving the reader to guess which bar looks wrong. */
  _svgBars(periods, color, emptyText, outlierLabels) {
    // An empty chart is a legitimate result — the counter simply has no statistics in this
    // range. Saying so beats a bare dash that looks like something went wrong.
    if (!periods.length) {
      return `<div class="st-empty">${this._esc(emptyText || "—")}</div>`;
    }
    const outliers = new Set(outlierLabels || []);
    const w = 900,
      h = 170,
      pad = 26;
    const max = Math.max(...periods.map((p) => p.value), 1);
    const bw = (w - 2 * pad) / periods.length;
    const bars = periods
      .map((p, i) => {
        const bh = ((h - 2 * pad) * p.value) / max;
        const x = pad + i * bw;
        const y = h - pad - bh;
        const isOutlier = outliers.has(p.label);
        const fill = isOutlier ? "var(--warning-color,#ffa600)" : color;
        const lbl =
          periods.length <= 16
            ? `<text x="${x + bw / 2}" y="${h - 7}" font-size="13" text-anchor="middle"
                 fill="var(--secondary-text-color)">${p.label.slice(2)}</text>`
            : "";
        return `<rect x="${x + 1}" y="${y}" width="${Math.max(bw - 2, 1)}" height="${bh}"
                  fill="${fill}" rx="2"><title>${p.label}: ${p.value}${
          isOutlier ? ` — ${this._t.outlierMarker}` : ""
        }</title></rect>${lbl}`;
      })
      .join("");
    return `<svg viewBox="0 0 ${w} ${h}" width="100%" style="overflow:visible">
      <text x="${pad}" y="16" font-size="13" fill="var(--secondary-text-color)">max ${this._n(
      Math.round(max)
    )} kWh</text>${bars}</svg>`;
  }
}

customElements.define("statistics-toolset-panel", StatisticsToolsetPanel);
