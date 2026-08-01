# Changelog

Alle nennenswerten Änderungen an **HA Statistics Toolset**. / All notable changes.

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach
[Semantic Versioning](https://semver.org/lang/de/). Jede veröffentlichte Version hat ein
[GitHub-Release](https://github.com/turbolooser/ha-statistics-toolset/releases) — nur darüber
sieht HACS ein Update.

> ⚠️ `READ_ONLY_MODE = True` ist in allen Versionen der Standard: `fix`/`restore` sind
> gesperrt, bis er in `const.py` bewusst abgeschaltet wird.

## [Unreleased]

## [0.18.8] — 2026-08-01

### Added
- Neues optionales Feld `anchor_sum` bei `simulate`/`fix`: setzt die neu berechnete Summe am
  Bereichsstart auf diesen Wert fort statt bei 0 neu zu beginnen. Betrifft Zähler, deren
  echter Zyklus-Reset vor dem Beginn der Referenzquelle liegt (z. B. ein Jahres-Zähler,
  dessen saubere Referenz erst mitten im Jahr angelegt wurde, weil die Quelle da erst
  korrigiert wurde) — ohne dieses Feld kappt eine Reparatur ab dem Referenz-Start
  klammheimlich alles, was der Zähler vorher schon akkumuliert hatte. Live gefunden: ein
  Jahres-Zähler fiel nach einem Fix von 4778 kWh auf 203 kWh, weil die Referenz erst seit
  Juli existierte, der Zähler aber seit Januar lief.

## [0.18.7] — 2026-08-01

### Fixed
- Die Balkendiagramme "Aktuell" und "Vorschlag" hatten unterschiedliche Zeitskalen, ohne das
  anzuzeigen: jedes Diagramm streckt seine eigene Anzahl Perioden auf dieselbe Pixelbreite —
  hat "Aktuell" 10 Perioden und "Vorschlag" 38 (eine Reparatur kann die Historie über die
  Referenz hinaus verlängern), zeigt Balken Nr. 5 in beiden Diagrammen eine andere
  Kalenderperiode. Beide Diagramme werden jetzt auf dieselbe, gemeinsame Perioden-Achse
  ausgerichtet (fehlende Periode auf einer Seite = 0-Balken statt Auslassen).



### Fixed
- Nach dem Deinstallieren blieb das Sidebar-Panel als Geisterleiche im laufenden Prozess
  hängen, bis Home Assistant neu gestartet wurde — obwohl Dateien und Config-Entry längst
  weg waren. `panel_custom`-Panels leben nur im Arbeitsspeicher; `async_unload_entry` (läuft
  auch bei jedem Reload) meldet das Panel bewusst nicht ab, aber bei einer echten Entfernung
  läuft danach kein Setup mehr, das es neu registrieren würde. Neues `async_remove_entry`
  meldet das Panel jetzt gezielt bei der tatsächlichen Deinstallation ab.

## [0.18.5] — 2026-08-01

### Fixed
- Eine Stunde, die in der **Quelle** selbst fehlte (Lücke in deren Recorder-Historie), wurde
  beim Reparieren stillschweigend übersprungen — der alte, ggf. korrupte Wert des Zählers
  blieb an genau dieser Stunde unangetastet stehen, während alle Nachbarstunden korrekt neu
  aufgebaut wurden. Live gefunden: 6 Stunden in einem echten Zähler blieben nach einer
  Reparatur weiterhin als Ausreißer gemeldet. `derive_series()` schreibt jetzt für jede
  vorhandene Stunde des Zählers eine Zeile — fehlt sie in der Quelle, wird der letzte
  bekannte Referenzwert fortgeschrieben, statt die Stunde auszulassen.

Diese Version geht ins besonders sensible Schreiben (`fix`) — vor dem Update ein
vollständiges Backup anlegen, wie immer.

### Fixed
- Der neue Zeit-Indikator ("Working… (Ns)") aus 0.18.3 konnte die fertige Erfolgsmeldung
  (z. B. "Restored: N points") dauerhaft überschreiben und bei der letzten Sekundenanzeige
  einfrieren, wenn nach dem Setzen der Meldung noch ein weiterer Aufruf lief (die
  Prüfung nach Fix/Restore, oder das Neuladen der Sicherungsliste) — live gefunden bei
  Rollback auf `spike`: die Daten waren korrekt geschrieben, die Anzeige blieb aber bei
  "Working… (30s)" hängen. Betroffen: Ablauf-Tab (Reparieren, Zurück auf Sicherung),
  Backups-Tab (Wiederherstellen), Übertragen-Tab.

## [0.18.3] — 2026-07-31

### Fixed
- `restore_verification_failed` konnte fälschlich auftreten, obwohl der Restore selbst
  erfolgreich war — live reproduziert direkt nach einem 45s-Fix auf einen 28k-Punkte-Zähler.
  Das Retry-Budget der Commit-Visibility-Prüfung (Restore-Verify wie auch der neue
  Read-Retry aus 0.18.2) war mit ~8s zu knapp für reale DB-Last; jetzt ~48s (20 Versuche,
  Backoff bis 3s).

### Changed
- Lang laufende Schreib-/Lese-Aktionen (Sichern, Reparieren, Zurück auf Sicherung,
  Auslesen, Übertragen) zeigen jetzt die verstrichene Zeit an ("Arbeite… (12s)"), damit
  klar bleibt, dass das Panel noch arbeitet und nicht hängt.

## [0.18.2] — 2026-07-31

### Fixed
- `source_no_statistics` konnte auftreten, wenn direkt nach einem Restore im selben Zähler
  gelesen wurde (z. B. im Geführten Ablauf: Restore → sofort Auslesen) — derselbe
  Commit-Visibility-Race wie beim Restore selbst, jetzt auch für `simulate()`s ersten Read
  mit begrenztem Retry abgesichert.

## [0.18.1] — 2026-07-31

### Geändert / Changed

- Chart-Titel gekürzt: „Aktuell (evtl. beschädigt)" → „Aktuell", „Vorgeschlagen
  (bereinigt)" → „Vorschlag" (analog auf Englisch: „Current (possibly corrupted)" →
  „Current", „Proposed (clean)" → „Proposed"). Wirkt sich auch auf die Endsummen-KPIs aus
  (jetzt „Endsumme (Aktuell)"/„Endsumme (Vorschlag)").
- Bestätigungstext vor `Fixen` nennt jetzt explizit, dass die automatische Sicherung bei
  Bedarf über den Backups-Tab wiederherstellbar ist (gleicher Wortlaut wie im geführten
  Ablauf).

## [0.18.0] — 2026-07-31

### Hinzugefügt / Added

- **Ausreißer werden im Balkendiagramm markiert.** „1 Ausreißer" allein sagte nicht, welcher
  Balken gemeint ist — der betroffene Monat im „Aktuell"-Chart wird jetzt in Warnfarbe
  hervorgehoben (Tooltip nennt den Grund). Neues Feld `outlier_periods` in der
  `simulate`/`fix`-Antwort.
- **Geführter Ablauf ist jetzt der Standard-Tab** beim Öffnen/Neuladen des Panels statt
  „Auslesen/Reparieren".

### Geändert / Changed

- **Schritt 4 (Prüfen & entscheiden):** „Zurück auf Sicherung" steht jetzt links, „Behalten"
  rechts, und beide fragen vor der Ausführung explizit nach — „Behalten" war bisher die
  einzige Aktion ohne Bestätigung, obwohl sie den Ablauf genauso endgültig abschließt wie
  ein Rollback.

## [0.17.3] — 2026-07-31

### Behoben / Fixed

- **Übertragen-Tab-Titel zeigte „undefined" auf Englisch.** Beim Herauslösen von `transfer`
  in einen eigenen Tab wurde `tabTransfer`/`introTransfer` nur im deutschen Textblock
  ergänzt, nicht im englischen — dort blieb der alte, ungenutzte `transferTitle`-Schlüssel
  stehen. Unsichtbar auf Deutsch (Standardsprache), erst beim Umschalten auf Englisch
  aufgefallen. Neuer Test vergleicht jetzt die Schlüsselmengen beider Sprachblöcke, damit
  das nicht wieder unbemerkt passiert.

## [0.17.2] — 2026-07-31

### Behoben / Fixed

- **Geführter Ablauf:** Zähler mitten im Ablauf gewechselt (nach „Auslesen" einen anderen
  ausgewählt) führte dazu, dass Sichern/Reparieren noch mit den Daten des alten Zählers
  weiterliefen. Die Auswahl springt jetzt automatisch zurück auf Schritt 1, sobald der
  Zähler nach dem Auslesen geändert wird — „Auslesen" muss dann bewusst erneut ausgeführt
  werden.

## [0.17.1] — 2026-07-31

### Geändert / Changed

- **Filter-Systematik im ganzen Panel konsistent gemacht.** Übertragen und Geführter
  Ablauf hatten keine oder nur eine unvollständige Filtermöglichkeit (Übertragen: freie
  Texteingabe statt Auswahl). Jetzt haben alle vier Tabs mit Zähler-Auswahl (Auslesen/
  Reparieren, Geführter Ablauf, Backups, Übertragen) dieselbe Filterzeile
  (Suchfeld + „nur Energie"-Chip + Trefferanzahl), gespeist aus demselben geteilten Zustand
  — einmal filtern wirkt überall. Übertragen nutzt jetzt Dropdowns statt Freitext (auch
  verwaiste `statistic_id`s ohne lebende Entity werden dort weiterhin gelistet).
- Die Verdrahtung dafür läuft jetzt über eine einzige Hilfsfunktion (`_wireFilterRow`)
  statt vierfach kopierten Code.

## [0.17.0] — 2026-07-31

### Hinzugefügt / Added

- **Neuer Tab „Geführter Ablauf"**, eigenständig neben den bestehenden manuellen Tabs:
  1 Auslesen → 2 Sichern → 3 Reparieren → 4 Erneut prüfen & entscheiden (`Behalten` oder
  `Zurück auf Sicherung`). Nutzt ausschließlich bestehende Dienste (`simulate`, `backup`,
  `fix`, `restore`) in fester Reihenfolge — kein neuer Dienst. Quelle/Zyklus/Zeitraum
  werden automatisch erkannt und sind hier bewusst nicht editierbar (Unterschied zum
  manuellen „Auslesen/Reparieren"-Tab). Die im Schritt „Sichern" angelegte Sicherung wird
  fest gemerkt, damit „Zurück auf Sicherung" exakt diese wiederherstellt, unabhängig davon,
  was zwischenzeitlich im manuellen Tab verändert wurde.
- HACS-Ansicht: `render_readme` deaktiviert — HACS zeigt jetzt nur die kurze
  Repo-Beschreibung + Link zum Repository statt des vollständigen (und dort teils defekt
  dargestellten) READMEs.

## [0.16.1] — 2026-07-31

### Geändert / Changed

- `transfer` hat jetzt einen eigenen Tab im Panel statt als Unterabschnitt im Backups-Tab
  zu laufen.

## [0.16.0] — 2026-07-31

### Hinzugefügt / Added

- **Neuer Dienst `transfer`**: verschiebt die komplette Statistik-Historie einer Entity auf
  eine andere `statistic_id` — für den Fall einer umbenannten Entity, deren alte Historie
  sonst verwaist unter der alten ID läge, während die neue bei null anfängt. Verweigert,
  wenn das Ziel bereits Statistik hat (nur Verschieben, nie Zusammenführen); legt vor dem
  Leeren der Quelle automatisch eine Sicherung an. Direkt im Backups-Tab des Panels
  nutzbar, mit derselben Bestätigung wie Restore.
- Buttons im Panel auf einheitliche Schriftgröße gebracht.
- Screenshots im README.

## [0.15.1] — 2026-07-31

### Behoben / Fixed

- **„Sicherung erstellen" und „Aktualisieren" sahen unterschiedlich aus** (Aktions-Button
  vs. Filter-Chip), obwohl direkt nebeneinander — beide nutzen jetzt dasselbe Button-Paar
  wie der Sim-Tab (`st-btn`/`st-btn2`).
- **Wiederherstellen-Button war pillenförmig** wie ein Filter-Chip, obwohl eine destruktive
  Aktion wie Fixen — hat jetzt dieselbe abgerundete Rechteck-Form und dasselbe Rot wie der
  Fix-Button, nur kompakter für die Tabellenzeile. Designregel damit klargezogen: Pillen nur
  für Filter/Toggles, abgerundete Rechtecke für Aktionen.
- **„Alle Treffer abwählen"** ergänzt neben „Alle Treffer auswählen" in der Zähler-Auswahl
  fürs Sichern.

## [0.15.0] — 2026-07-31

### Geändert / Changed

- **Backups-Tab überarbeitet: "search-first" statt Voll-Dump.** Bisher zeigte der Tab beim
  Öffnen sofort jeden Zähler als Checkbox (218 auf einem echten System) und jede
  Sicherungsdatei als eigene, unsortierte Tabellenzeile — bei echter Historie eine Wand aus
  hunderten Zeilen. Jetzt:
  - **Zähler-Auswahl fürs Sichern:** leerer Filter zeigt nur einen Suchhinweis; Treffer
    erscheinen als Dropdown (max. 12 sichtbar, „N weitere — Filter eingrenzen" sonst), eine
    Auswahl wird zum entfernbaren Chip über dem Filterfeld — sichtbar und korrigierbar auch
    nach erneutem Filtern, ohne wieder zu suchen.
  - **Sicherungsübersicht:** nach Zähler gruppiert statt einer flachen Liste. Jede Gruppe
    zeigt eine Zusammenfassung (neueste Sicherung + direkter Wiederherstellen-Button) und
    klappt zur vollen Historie dieses Zählers auf; passende Gruppen öffnen sich beim Filtern
    automatisch, manuell eingeklappte bleiben es auch nach einem Reload.
  - Leerer Filter zeigt jetzt in beiden Bereichen einen Hinweis statt eines Dumps.

## [0.14.0] — 2026-07-31

### Hinzugefügt / Added

- **Sidebar-Panel jetzt für alle Nutzer freischaltbar.** Bisher war das Panel per
  `require_admin=True` hart auf Admins beschränkt, unabhängig davon, ob Schreiben überhaupt
  erlaubt war. Neuer Schalter **„Panel nur für Admins sichtbar"** im Config-Tab des Panels
  (und unter Settings → Konfigurieren): aus zeigt das Panel jedem Nutzer, an den Schreibsperren
  (Simulationsmodus/Freigabeliste) ändert das nichts — die entscheiden weiterhin, wer
  tatsächlich schreiben darf, nicht wer das Panel sehen kann. Wirkt sofort, kein HA-Neustart
  nötig — das Panel wird bei jeder Änderung live neu registriert.

## [0.13.3] — 2026-07-30

### Behoben / Fixed

- **`restore` schlug live weiterhin fehl (`restore_verification_failed`, `actual: 0`), obwohl
  der Import selbst erfolgreich war.** `async_block_till_done()` (0.13.2) garantiert nur, dass
  die Recorder-Warteschlange abgearbeitet wurde — nicht, dass der Datenbank-Commit bereits für
  einen frischen Lesezugriff sichtbar ist; Commits laufen auf einem eigenen Zyklus. Live
  bestätigt: ein Lesezugriff direkt nach dem fehlgeschlagenen `restore` zeigte 0 Punkte, ein
  manueller Lesezugriff wenige Sekunden später die korrekt wiederhergestellten 21603 Punkte.
  `_verify_restore()` liest jetzt mit kurzem, steigendem Backoff (bis zu 8 Versuche, ~8 s
  Budget) erneut, statt sich auf einen einzigen Lesezugriff zu verlassen.
- **Blockierende Datei-I/O im Event-Loop** (`Detected blocking call to write_bytes`, live im
  HA-Log gefunden): `_write_backup_file`/`_read_backup_file` liefen bisher synchron im
  Event-Loop statt über `hass.async_add_executor_job`. Betraf das Schreiben jedes Backups und
  das Lesen beim `restore`.

## [0.13.2] — 2026-07-30

### Behoben / Fixed

- **`restore` schlug nach 0.13.1 weiterhin fehl, jetzt mit `restore_verification_failed`.**
  Zweite Hälfte desselben Problems: `async_import_statistics` reiht den eigentlichen
  Schreibvorgang nur in die Recorder-Warteschlange ein und kehrt sofort zurück — die
  anschließende Verifikation las die Daten teils zurück, bevor der Import überhaupt
  gelaufen war. Behoben mit `instance.async_block_till_done()` (demselben Mechanismus, den
  HAs eigene Importpfade nutzen): reiht eine Synchronisationsaufgabe *hinter* dem Import in
  dieselbe Warteschlange ein und wartet, bis sie durchläuft — erst danach kehrt der
  Schreibvorgang wirklich zurück. Betrifft `restore` und `fix` gleichermaßen (beide nutzen
  `write_statistics`).
- **Dateiname in der Backup-Tabelle zerstörte das Layout** (Umbruch mitten im Zeichen).
  Zeigt jetzt gekürzt mit Auslassungspunkten und dem vollen Namen als Tooltip; die Tabelle
  hat zusätzlich einen horizontalen Scroll-Container als Sicherheitsnetz.

### Hinzugefügt / Added

- **Backups-Tabelle folgt jetzt demselben Sensorfilter** wie die Auswahlliste darüber.
  Nach Zeitpunkt/Datum durchsuchen entfällt — Filtertext eintippen genügt, um die
  Sicherungen eines bestimmten Zählers zu finden.

## [0.13.1] — 2026-07-30

### Behoben / Fixed

- **`restore` schlug fehl mit „Detected unsafe call not in recorder thread".** Das Leeren
  der Statistik (`clear_statistics`) verlangt intern den *eigenen* Arbeits-Thread des
  Recorders; aufgerufen wurde es aber über `instance.async_add_executor_job`, das auf
  einem anderen, generischen Executor-Thread des Recorders läuft. Behoben durch denselben
  Weg, den der eingebaute Dienst `recorder/clear_statistics` selbst nutzt:
  `instance.async_clear_statistics(..., on_done=...)`, dessen Rückruf über
  `hass.loop.call_soon_threadsafe` in den Event-Loop zurückgebrückt wird, mit 10 Sekunden
  Zeitlimit. Betraf ausschließlich `restore` (`fix` und `backup` waren nicht betroffen, da
  sie `clear_statistics` nicht aufrufen).
- Neuer Test hält fest, dass die rohe `clear_statistics`-Funktion nicht mehr importiert
  wird — verifiziert per Gegenprobe, dass er die vorherige fehlerhafte Version erkannt
  hätte.

## [0.13.0] — 2026-07-30

### Hinzugefügt / Added

- **Wiederherstellen direkt im Backups-Reiter.** Jede Zeile der Sicherungstabelle hat jetzt
  einen eigenen „Wiederherstellen"-Button, statt nur den Dienstaufruf zu erklären. Ein
  Bestätigungsdialog nennt Zähler und Dateiname und weist auf die automatische
  Vorher-Sicherung hin, bevor tatsächlich geschrieben wird.
- Der Button ist genau wie „Fixen" gesperrt, solange der Simulationsmodus an ist oder der
  betroffene Zähler nicht in der Freigabeliste steht — pro Zeile einzeln bewertet, da jede
  Sicherung zu einem anderen Zähler gehören kann. Ändert sich der Schreibstatus (z. B. nach
  dem Speichern der Konfiguration), werden bereits angezeigte Buttons ohne erneuten
  Netzwerkaufruf neu bewertet.

### Geändert / Changed

- Der Hinweistext „Dienst manuell aufrufen" ist entfallen, da es jetzt einen echten Button
  gibt. Einleitungstext des Backups-Reiters entsprechend erweitert (Erstellen vs.
  Wiederherstellen als getrennte Punkte).

## [0.12.0] — 2026-07-30

### Hinzugefügt / Added

- **Backups-Reiter: mehrere Zähler auf einmal sichern.** Statt einer Einzelauswahl steht
  jetzt eine Checkbox-Liste unter dem Filter (mit „Alle sichtbaren auswählen"). Jeder
  angehakte Zähler bekommt sein eigenes, vollständiges Backup — nie eine kombinierte
  Sicherung mehrerer Zähler in einer Datei. Die Auswahl bleibt beim Ändern des Filters
  erhalten, auch wenn ein bereits gewähltes Element dadurch vorübergehend ausgeblendet
  wird. Ergebnis nennt Erfolge und fehlgeschlagene Zähler einzeln (z. B. „3/4. Fehler:
  sensor.x").
- **Zweiter Button „Fixen"** neben dem bisherigen (jetzt „Auslesen" genannten) Knopf.
  Fixen ist nur anklickbar, wenn der Simulationsmodus aus **und** der gewählte Zähler in
  der Freigabeliste ist (oder keine Freigabeliste gesetzt ist) — der Status kommt aus
  demselben `status`-Dienst wie der Warnbanner, nicht aus einer geratenen Annahme. Vor dem
  eigentlichen Schreiben fragt ein Bestätigungsdialog, der den Zähler beim Namen nennt und
  auf die automatische Vorher-Sicherung hinweist.

### Behoben / Fixed

- **Schriftgrößen im Backups-Reiter** (Tabelle, Kennzeichnungs-Chips, Dateinamen) waren
  kleiner als im Rest des Panels — jetzt auf dasselbe Niveau gebracht.

### Geändert / Changed

- Reiter „Simulieren / Reparieren" heißt jetzt „Auslesen / Reparieren", passend zum neuen
  Button-Paar; Basisschrift auf diesem Reiter 1 px kleiner als in Backups/Konfiguration.
- Einleitungstext des Konfigurations-Reiters trägt jetzt Struktur (Aufzählung statt
  Fließtext); der Einleitungstext des Auslesen/Reparieren-Reiters erklärt jetzt explizit
  beide Aktionen.

—

## [0.11.0] — 2026-07-30

### Behoben / Fixed

- **Zähler ohne Live-Entity waren in keiner Auswahl im Panel auffindbar — auch nicht ohne
  Filter.** Die Zähler-Liste kam ausschließlich aus `hass.states`; ein per
  `recorder/import_statistics` angelegter Zähler (z. B. die Szenarien aus
  `make_test_sensors.py`) hat aber keine Entity und damit keinen State. Das Panel fragt
  jetzt zusätzlich `recorder/list_statistic_ids` ab und vereinigt beide Quellen — betrifft
  die Zähler-Auswahl im Reiter *Simulieren/Reparieren* ebenso wie im Reiter *Backups*. Der
  Energie-Filter erkennt solche Zähler über die Einheit aus den Recorder-Metadaten, wenn
  kein Live-State existiert.
- **Zähler-Auswahl im Backups-Reiter hatte keinen eigenen Filter** und zeigte je nach
  Zustand des Simulieren-Tabs entweder unsinnig viele oder scheinbar zufällig wenige
  Einträge. Der Reiter hat jetzt eine eigene Filterzeile (Textsuche + „nur Energie"), die
  denselben Filterzustand wie der Simulieren-Tab teilt — einmal filtern, wirkt überall.

## [0.10.1] — 2026-07-30

### Behoben / Fixed

- **Der Warnbanner auf der Hauptseite war fest einprogrammiert und zeigte immer „Nur
  Simulation (kein Schreiben)" — unabhängig vom tatsächlichen Zustand, auch nach dem
  Speichern der Konfiguration oder einem Neuladen der Seite.** Er fragt jetzt beim Öffnen
  des Panels und direkt nach dem Speichern in der Konfiguration den `status`-Dienst ab und
  zeigt einen von drei Texten: Simulationsmodus aktiv, Schreiben aktiv für eine konkrete
  Freigabeliste, oder eine deutliche Warnung, wenn Schreiben ohne jede Einschränkung
  aktiviert ist.

## [0.10.0] — 2026-07-30

### Hinzugefügt / Added

- **Konfiguration direkt im Panel — kein Umweg mehr über Einstellungen.** Der
  Konfigurations-Reiter zeigt jetzt ein Formular statt nur einer Anzeige: Simulationsmodus
  als Kontrollkästchen, beschreibbare Zähler als Textfeld (ein `statistic_id` pro Zeile),
  Speichern-Knopf. Wirkt sofort, kein Neustart nötig.
- Neuer Service **`set_config`** (schreibt nur die Konfiguration, nie Statistikdaten):
  ändert Simulationsmodus und/oder Freigabeliste. Nur die übergebenen Felder werden
  geändert — ein Aufruf mit nur `read_only` lässt die Freigabeliste unangetastet, eine
  leere Liste hebt die Einschränkung auf. Legt beim ersten Aufruf automatisch einen
  Config-Entry an, falls noch keiner existiert (kein manuelles „Integration hinzufügen"
  nötig), und aktualisiert den wirksamen Zustand sofort — ohne auf den Reload zu warten,
  den `async_update_entry` im Hintergrund anstößt.
- `tests/test_config_service.py`: lädt `__init__.py` erstmals vollständig (mit
  nachgebildetem `hass.config_entries`, Services, `voluptuous`-Validierung) und deckt u. a.
  ab: Config-Entry wird bei Bedarf erstellt, UI-Einstellung hat Vorrang vor YAML, Teil-Updates
  lassen unberührte Felder unverändert, leere Freigabeliste hebt die Einschränkung auf,
  `async_unload_entry` fällt auf die sicheren Vorgaben zurück. Verifiziert außerdem, dass
  dieser Test den 0.9.1-Fehler (`WRITE_ALLOWLIST` nicht importiert) gefangen hätte.

### Behoben / Fixed

- Panel-Registrierung: die Importe von `panel_custom`/`http` standen außerhalb des
  Best-Effort-`try/except` — ein Fehlschlag dort hätte den gesamten Integrations-Start zu
  Fall gebracht statt nur die Sidebar-Anzeige zu überspringen. Jetzt innerhalb des Blocks.

### Geändert / Changed

- Der Einleitungstext des Konfigurations-Reiters beschreibt jetzt das Bearbeiten, nicht
  mehr den Verweis auf Einstellungen.
- CI installiert zusätzlich `voluptuous` für die neuen Tests.

## [0.9.1] — 2026-07-30

### Behoben / Fixed

- **Setup schlug auf einer echten Instanz fehl:** `NameError: name 'WRITE_ALLOWLIST' is not
  defined` in `__init__.py`, weil der 0.9.0-Umbau der Schreibsperren die Konstante nutzt,
  ohne sie zu importieren. Die vorhandenen Tests haben das nicht gefangen, weil sie
  `__init__.py` bewusst nicht laden (es hängt an Home Assistant, das lokal nicht installiert
  ist) — der Fehler zeigte sich erst beim echten Start.

### Hinzugefügt / Added

- `tests/test_lint.py`: lässt `pyflakes` über alle Integrationsdateien laufen und schlägt
  bei jedem verwendeten, aber nirgends gebundenen Namen fehl — unabhängig davon, ob eine
  Testabdeckung den betroffenen Codepfad je ausführt. CI installiert `pyflakes` entsprechend.

## [0.9.0] — 2026-07-30

### Hinzugefügt / Added

- **Konfigurationsseite in der UI** (Einstellungen → Geräte & Dienste → HA Statistics
  Toolset → Konfigurieren): Simulationsmodus ein/aus und Freigabeliste der beschreibbaren
  Zähler lassen sich jetzt klicken statt in YAML einzutragen. Eine Änderung lädt die
  Integration automatisch neu — kein Neustart nötig. `configuration.yaml` funktioniert
  weiterhin, die UI-Einstellung hat aber Vorrang.
- Neuer Service **`status`** (nur lesend): meldet, ob gerade geschrieben werden darf, welche
  Zähler freigegeben sind, woher die Einstellung stammt (UI/YAML/Vorgabe), wo Sicherungen
  liegen und wie viele es gibt.
- **Panel: drei Reiter** — *Simulieren/Reparieren*, *Backups*, *Konfiguration*. Der
  Backups-Reiter zeigt alle Sicherungen als Tabelle (Zeitpunkt, Art, Zähler, Punkte,
  Endsumme, Zeitraum, Datei) und legt auf Knopfdruck eine neue an. Der Konfigurations-Reiter
  zeigt den `status`-Dienst lesbar an.
- **Einleitender Text unter dem Titel**, je Reiter passend formuliert, damit klar ist, was
  dort passiert, bevor man klickt.
- Vor der Sprachauswahl steht jetzt die Beschriftung „Sprache:" / „Language:".

## [0.8.0] — 2026-07-30

### Hinzugefügt / Added

- **Die Schreibsperren sind konfigurierbar — über `configuration.yaml`, nicht im Code:**

  ```yaml
  statistics_toolset:
    read_only: false
    write_allowlist:
      - sensor.mein_testzaehler
  ```

  Beide Schlüssel optional, ohne sie gelten die sicheren Vorgaben aus `const.py`. Der Grund
  für YAML statt Code: eine Freigabe in `const.py` ist beim nächsten HACS-Update wieder weg,
  und eine Allowlist im Repository würde für jede Installation gelten. Gelesen wird beim
  Zugriff, nicht beim Import, sodass ein Neustart genügt.
- Beim Start wird protokolliert, welche Sperren gelten; ist Schreiben ohne Allowlist
  freigegeben, erscheint eine Warnung.

### Geändert / Changed

- `simulate` meldet in `read_only_mode` den tatsächlich wirksamen Zustand statt der Konstante.

## [0.7.0] — 2026-07-30

Backup und Restore erfüllen jetzt das eigentliche Ziel: nach einer Reparatur auf **jeden
früheren Stand** eines Zählers zurückspringen, ohne etwas anderes zu verändern.

### Geändert / Changed

- **Sicherungen umfassen den kompletten Verlauf eines Zählers**, nicht mehr einen Zeitraum.
  Grund: der Recorder kann nur ganze `statistic_id`s löschen, ein exakter Rücksprung ist
  also nur als „leeren und vollständig neu einspielen" möglich. Eine Bereichssicherung würde
  alles stehen lassen, was eine Reparatur außerhalb davon geschrieben hat — genau der Fall,
  wenn sie die Historie nach hinten verlängert.
- **Sicherungen sind gzip-komprimiert** (`.json.gz`): 2,5 Jahre stündlich schrumpfen von
  1,07 MB auf 0,16 MB, 48 Zähler mit je 5 Sicherungen von 0,26 GB auf 0,04 GB.
- **Metadaten werden mitgesichert** (`has_sum`, `has_mean`, Einheit, Name, Quelle) und beim
  Wiederherstellen verwendet. Vorher wurde beim Schreiben immer „Summe, kein Mittelwert"
  angenommen, was bei einem Mittelwert-Sensor eine falsch interpretierte Reihe ergibt.
- `restore` liefert jetzt eine Antwort mit Punktzahl, `full_history`, Prüfergebnis und dem
  Pfad der automatischen Vorher-Sicherung.

### Hinzugefügt / Added

- **`restore` setzt exakt zurück**: Datei prüfen (Prüfsumme, Zugehörigkeit, Metadaten) →
  Ist-Zustand automatisch als `pre-restore` sichern → `clear_statistics` **nur für diese
  eine ID** → Vollimport → Punktzahl und Endsumme gegen die Datei verifizieren. Bei
  Abweichung Abbruch mit Nennung der Vorher-Sicherung. Eine Sicherung aus einer älteren
  Version deckt nur einen Zeitraum ab und wird deshalb **ohne** Leeren eingespielt und als
  unvollständig gemeldet.
- **`fix` schreibt nur mit brauchbarer Sicherung.** Die `pre-fix`-Sicherung wird nach dem
  Schreiben wieder eingelesen und ihre Prüfsumme neu berechnet; ist sie unlesbar, leer,
  beschädigt oder gehört zu einem anderen Zähler, wird nichts geschrieben.
- **Neuer Service `list_backups`** (nur lesend): alle Sicherungen mit Zeitpunkt, Kennzeichnung
  (`backup`, `pre-fix`, `pre-restore`), Zeitraum, Punktzahl, Endsumme und Größe, neueste
  zuerst. Ohne diese Liste wäre „auf jeden beliebigen Stand zurück" praktisch nicht nutzbar.
- **Zweites Schloss `WRITE_ALLOWLIST`** in `const.py`: ist die Liste gefüllt, sind **nur**
  diese `statistic_id`s beschreib- und löschbar — auch mit `READ_ONLY_MODE = False` und
  `confirm: true`. Damit lässt sich an Testzählern arbeiten, während echte Daten technisch
  unerreichbar bleiben.
- **`scripts/make_test_sensors.py`**: klont einen echten Zähler (nur lesend) in fünf
  Testreihen — `clean`, `spike`, `gap`, `short`, `frozen`. Jede Ziel-ID muss `test` im Namen
  tragen, sonst verweigert das Skript den Start.
- 13 Szenario-Tests gegen einen nachgebildeten Recorder, unter anderem: Rücksprung nach einer
  Reparatur, die die Historie verlängert hat; kein anderer Zähler wird berührt; beschädigte
  Datei wird **vor** dem Leeren abgewiesen; fehlgeschlagener Import wird erkannt; Allowlist
  blockt; Sicherung funktioniert auch im Read-only-Modus.

## [0.6.2] — 2026-07-30

### Behoben / Fixed

- **Der erste Balken zeigte den Zählerstand statt den Verbrauch.** `aggregate_periods` nahm
  als Ausgangswert 0 an; ein laufender Zähler steht aber schon bei Tausenden von kWh. Der
  erste Monat bekam dadurch den absoluten Stand als „Verbrauch" (z. B. 25 494 statt 494) und
  die Skalierung drückte alle übrigen Monate zu einer flachen Linie. Ausgangswert ist jetzt
  der Beginn der Reihe — für „Aktuell" und „Vorgeschlagen" gleichermaßen korrekt.

### Geändert / Changed

- **`none` heißt jetzt „Gesamtzähler — läuft ohne Reset weiter".** „none (kein Reset)" las
  sich wie „kein Zyklus erkannt", gemeint ist ein Zähler, der bewusst nie zurückgesetzt wird.
  Der technische Wert bleibt `none`; er steht zur Klarstellung in der Beschreibung.

## [0.6.1] — 2026-07-30

### Hinzugefügt / Added

- `scripts/live_check.py`: prüft `detect`/`simulate` gegen die Rohdaten des Recorders — rein
  lesend, ohne Zugangsdaten oder Entity-IDs im Code. Es findet die Zähler auf der Instanz
  selbst, nimmt bis zu zwei pro Zyklustyp und rechnet jede Vorschau nach; am wichtigsten:
  **jede** Abweichung vom Rohwert muss ausgewiesen sein. Konfiguration über `HA_TOKEN` und
  `HA_URL`, Rückgabewert ≠ 0 bei Fehlern.
- `scripts/bench_engine.py`: misst die Laufzeit der Mechanik auf synthetischen Daten, ohne
  Home Assistant, und warnt oberhalb von zwei Sekunden pro Durchlauf.
- `scripts/README.md` beschreibt beide und was sie prüfen.

### Geändert / Changed

- **Beispiele in Doku und `services.yaml` sind jetzt generisch** (`sensor.house_energy_monthly`
  statt der Entity-IDs einer echten Anlage). Auch die Beschreibung der mehrstufigen
  Zählerkette und die Beispielzahlen im Changelog nennen keine fremden Messwerte mehr.
- `.gitignore` schließt `*.log` aus: die Ausgabe von `live_check.py` enthält die Entity-IDs
  der geprüften Instanz.

## [0.6.0] — 2026-07-30

### Behoben / Fixed

- **Quadratischer Aufwand in der Kernberechnung — Faktor 58 schneller.** `value_at` baute bei
  *jedem* Aufruf die Suchliste neu auf, womit die Binärsuche zu einer linearen Suche wurde;
  `derive_series` rief das pro Datenpunkt auf. Bei 21 600 Punkten (2,5 Jahre stündlich)
  waren das ~467 Millionen Operationen: **9 776 ms → 79 ms** für `derive_series`, die
  gesamte Engine-Arbeit **9 864 ms → 171 ms**. Gemessen an den echten Daten, nicht geschätzt.
- **Rechenarbeit blockiert Home Assistant nicht mehr.** `build_reference` und `derive_series`
  laufen jetzt im Executor statt im Event-Loop. Vorher stand HA für die Dauer der Berechnung
  still — bei einem Zeitraum über „Alles" waren das rund zehn Sekunden, in denen
  Automationen und Oberfläche warteten. Aufgefallen ist es, weil eine WebSocket-Verbindung
  während einer Simulation in den Keepalive-Timeout lief.

### Hinzugefügt / Added

- `value_at(reference, ts, timestamps)` nimmt die Schlüsselliste optional entgegen;
  `timestamps_of()` erzeugt sie einmalig. Ohne Argument verhält sich die Funktion wie vorher.
- Drei Tests halten die Laufzeit fest: 10 000 Lookups unter einer Sekunde, `derive_series`
  über 21 600 Punkte unter zwei Sekunden, und identische Ergebnisse mit und ohne
  Schlüsselliste.

## [0.5.4] — 2026-07-30

### Geändert / Changed

- Schriftbasis im Panel von 17 auf 16 px — alles skaliert über die eine Basisgröße mit.

### Behoben / Fixed

- **Leerer Graph erklärt sich jetzt.** Hat der Zähler im gewählten Zeitraum keine
  Statistikdaten, stand über dem oberen Graphen nur ein „—", was wie ein Fehler aussah.
  Tatsächlich ist das der normale Fall bei einem Zeitraum vor der Entstehung des Zählers
  (Endsumme „Aktuell" ist dann 0). Dort steht jetzt: „Der Zähler hat in diesem Zeitraum keine
  Statistikdaten — hier ist nichts zu zeichnen. Eine Reparatur würde die Historie für diesen
  Zeitraum neu anlegen."

## [0.5.3] — 2026-07-30

### Behoben / Fixed

- **Die Klemm-Warnung war sachlich falsch.** Bei Start 13:50 meldete sie „Start auf 14:00
  angehoben — davor hat die Quelle keine Daten", obwohl die Quelle Daten seit Februar 2024
  hat. Tatsächlich liegen Langzeitstatistiken nur auf **Stundengrenzen**, der Start rutschte
  also um 10 Minuten. Die Warnung erscheint jetzt nur noch bei einer echten Lücke
  (Verschiebung über eine Stunde); die Rasterung passiert stillschweigend.
- **Ausreißer in der Quelle wurden stillschweigend entfernt.** `build_reference` glättet
  unplausible Sprünge der Quelle — gezählt und angezeigt wurden aber nur die des Zählers.
  Eine Simulation konnte dadurch „Ausreißer 0" melden, während die vorgeschlagene Summe
  mehrere hundert kWh unter dem Rohwert der Quelle lag. Die Vorschau weist das jetzt aus:
  `source_outliers`, `source_removed` und `raw_reference_delta` in der Service-Antwort, eine
  eigene Kennzahl **Ausreißer (Quelle)** im Panel und ein Hinweis, der Anzahl und entfernte
  Menge nennt. Die Kennzahl der Zähler-Ausreißer heißt jetzt eindeutig
  **Ausreißer (Zähler)**.

## [0.5.2] — 2026-07-30

### Geändert / Changed

- **Größere Schrift im Panel.** Alle Größen sind jetzt in `em` statt `rem` angegeben und
  hängen damit an *einer* Basisgröße im Panel (17 px) — `rem` bezieht sich auf die
  Browser-Wurzel und ignorierte die Panel-Basis, weshalb „alles größer" vorher zwanzig
  Einzeländerungen gewesen wäre. Am stärksten gewachsen sind die Stellen, die zu klein
  waren: Quellkette 12 → 15 px, Badges 12,5 → 15,6 px, Feldbeschriftungen 14,4 → 16,2 px,
  Kennzahlen 23 → 26 px, Titel 27 → 31 px.
- Die Beschriftungen der Balkengrafiken (Monat, Maximum) wachsen von 10/11 auf 13 Einheiten.

### Hinzugefügt / Added

- `tests/test_panel_css.py`: hält die Lesbarkeit fest — Mindestbasis 16 px, keine Schrift
  unter 0,85 em, kein `rem` (das würde die Basis umgehen), SVG-Beschriftungen mindestens
  12 Einheiten, und die Balkenbreite muss bei maximaler Balkenzahl noch für ein Label
  reichen.

## [0.5.1] — 2026-07-30

### Geändert / Changed

- **Service-Dialog und Fehlermeldungen sind einsprachig.** Alle Texte liegen jetzt in
  `strings.json` bzw. `translations/de.json` / `translations/en.json`, wie Home Assistant es
  für Integrationen vorsieht — HA zeigt die Sprache des Nutzers. `services.yaml` enthält nur
  noch Struktur (Selektoren, `required`, Beispiele) und **keine** Texte mehr; vorher stand
  dort in jedem Feld „Deutsch — English" untereinander.
- Fehler werden über `translation_key` geworfen (`read_only_mode`, `confirm_required_fix`,
  `confirm_required_restore`, `source_no_data`, `source_no_statistics`, `backup_incomplete`,
  `backup_no_rows`) statt mit fest eingebautem, doppelsprachigem Text.
- Die Zyklus-Auswahl ist übersetzt und erklärt sich selbst: „Zweimonatlich (Jan/Mär/Mai/…)",
  „Kein Zyklus — permanenter Zähler ohne Reset" statt der rohen Schlüssel.

### Hinzugefügt / Added

- `tests/test_translations.py`: prüft ohne Home Assistant, was hassfest in der CI verlangt —
  jeder Service und jedes Feld übersetzt, Selector-Optionen vollständig, keine Texte in
  `services.yaml`, alle im Code verwendeten Exception-Schlüssel vorhanden, Platzhalter
  zwischen den Sprachen identisch, und **keine Sprachmischung** in einer Datei.
- CI installiert `pyyaml` für diese Tests.

## [0.5.0] — 2026-07-30

### Geändert / Changed

- **Der vorgeschlagene Zeitraum richtet sich nach der Quelle, nicht mehr nach dem Zähler.**
  Reparierbar ist, was die Quelle abdeckt — `import_statistics` kann Punkte auch für
  Zeiträume schreiben, die der Zähler nie hatte. Vorher begrenzte der (kurze) Zählerbereich
  den Vorschlag, wodurch die Vorjahres-Presets gesperrt blieben und die Wurzel-Erkennung aus
  0.4.4 ihren eigenen Vorteil verlor. `detect` liefert `counter_start` und `source_start`
  jetzt getrennt; das Panel zeigt „Historie verlängerbar", wenn die Quelle weiter zurückreicht.
- **Hinweise sind nicht mehr zweisprachig.** Das Backend liefert strukturierte Warnungen
  (`code` + Werte statt Prosa), das Panel formuliert sie in der **gewählten** Sprache und
  zeigt Zeitpunkte in lokaler Schreibweise statt als ISO-String mit `+00:00`.

### Behoben / Fixed

- **Panel-Layout:** Der Erkennungs-Hinweis saß in der Grid-Zelle „Quelle", brach mehrzeilig
  um und schob dadurch „Zyklus" und „Ende" aus der Ausrichtung. Er steht jetzt als eigene
  Zeile in voller Breite unter dem Formular — kompakte Badges (Quelle · Zyklus ·
  Verlängerbarkeit), Details im Tooltip, die Quellkette einzeilig mit Auslassung. Die Zeile
  hat eine Mindesthöhe, damit beim Erkennen nichts springt; das Grid richtet Felder oben aus.
- Entity-IDs werden beim Einsetzen in die Statuszeile HTML-escaped.

## [0.4.5] — 2026-07-30

### Geändert / Changed

- Integration heißt jetzt **HA Statistics Toolset** (Anzeigename in HACS, Sidebar und Panel).
  Die Domain bleibt `statistics_toolset` — sie zu ändern würde bestehende Statistiken,
  Service-Aufrufe und Automationen brechen.

### Hinzugefügt / Added

- Dieses Changelog, rückwirkend aus Releases und Commits aufgebaut.

## [0.4.4] — 2026-07-30

### Hinzugefügt / Added

- **Alle `utility_meter`-Zyklen** werden unterstützt: `quarter-hourly`, `hourly`, `daily`,
  `weekly`, `monthly`, `bimonthly` (Monate 1,3,5,7,9,11), `quarterly` (1,4,7,10), `yearly`
  sowie **`none`** für einen Zähler ohne Zyklus (permanenter Gesamtzähler, kein Reset). Die
  Reset-Punkte entsprechen den Cron-Mustern aus `utility_meter.sensor.PERIOD2CRON`.
- **Transitive Quellauflösung** (`_source_chain`): mehrstufige Zähler
  (`…_monthly` → permanenter Gesamtzähler → Riemann-Integralsensor) werden nach oben verfolgt,
  vorgeschlagen wird die **Wurzel** — am wenigsten abgeleitet und oft mit längerer Historie.
  Die vollständige Kette steht in `source_chain` und wird im Panel angezeigt.
- `detect` meldet `cycle_via`; das Panel warnt sichtbar, wenn der Zyklus geraten wurde.

### Geändert / Changed

- Der Zyklus wird **exakt aus der `utility_meter`-Konfiguration gelesen**
  (`hass.data["utility_meter"]`, Schlüssel `cycle`); die Namensheuristik ist nur noch
  Rückfall für Zähler, die kein `utility_meter` sind.

### Behoben / Fixed

- Stündliche Zähler (`…_hourly`) wurden still als `monthly` geraten — das hätte die Reihe
  falsch wieder aufgebaut.
- Meter mit freiem `cron`-Muster werden als *nicht unterstützt* gemeldet, statt auf einen
  ähnlichen Zyklus abgebildet zu werden.
- Kettenverfolgung stoppt vor nicht-kumulativen Sensoren (Leistung in W) und ist gegen
  Ringreferenzen abgesichert (`max_depth` + `seen`-Set).

## [0.4.3] — 2026-07-30

### Behoben / Fixed

- **Bereichsstart war zu grob:** `stat_range` gab den Start des ersten *Monatsbuckets*
  zurück (Monatserster), obwohl der erste echte Datenpunkt Tage später liegen kann. Der
  vorgeschlagene Zeitraum begann damit *vor* der Reihe und `plausibility_check` lehnte jede
  Reparatur ab (`Requested range lies outside the reference series`). Der erste Monat wird
  nun mit Stundenauflösung nachgesehen.
- **Mittelwert-Sensoren galten als kumulative Quelle:** ein Leistungssensor (W,
  `has_sum=False`) antwortet auf eine `sum`-Abfrage mit Buckets *ohne* `sum`-Schlüssel.
  Dadurch wurde `sensor.current_power` als Quelle akzeptiert und der erkannte Bereich
  beschnitten. Es zählen nur Buckets mit `sum` — damit greift auch das Verwerfen unbrauchbarer
  Quellen aus 0.4.2 überhaupt erst.
- Ein zu früher Start wird auf den ersten Referenzpunkt **geklemmt** und in
  `Preview.warnings` gemeldet, statt den Lauf abzulehnen. `fix` klemmt identisch, damit
  geschriebene und gezeigte Reihe übereinstimmen.
- Ein Zeitraum ohne Daten nennt den **verfügbaren** Zeitraum statt `series is empty`;
  `PlausibilityError` benennt beide Grenzen.

### Hinzugefügt / Added

- Panel: Zeitraum-Presets, die komplett vor dem Datenbeginn liegen, werden **ausgegraut**;
  Hinweise aus der Simulation werden angezeigt.
- Tests: `estimate_max_rate` (Schwelle über echtem Verbrauch, unter Phantom-Sprung;
  Untergrenze bei dünnen Daten) und die diagnostizierbare `PlausibilityError`.

## [0.4.2] — 2026-07-30

### Behoben / Fixed

- **Quellsensoren wurden bei YAML-Zählern nie erkannt.** Die Erkennung sah nur in den
  Config-Entry; per **YAML/Package** konfigurierte `utility_meter` haben keinen und landeten
  daher immer im Selbst-Modus.

### Hinzugefügt / Added

- Erkennungskette mit vier Wegen, vom zuverlässigsten abwärts: `config_entry` →
  `utility_meter`-Laufzeitdaten (`hass.data`, Match über `utility_meter_sensors`) →
  `state_attribute` (Riemann-`integration` veröffentlicht `source`) → laufendes
  Entity-Objekt. Die `hass.data`-Schlüssel werden als Strings genutzt, daher kein Import und
  keine `manifest`-Abhängigkeit auf `utility_meter`.
- Eine Quelle **ohne eigene Statistik** wird verworfen (statt später an der
  Plausibilitätsprüfung zu scheitern) und der Selbst-Modus genutzt; beginnt die Quelle später
  als der Zähler, wird der Bereichsstart nachgezogen.
- `detect` liefert `source_via`, damit ein Vorschlag nachvollziehbar ist.

## [0.4.1] — 2026-07-30

> Ohne GitHub-Release veröffentlicht und daher für HACS unsichtbar — Inhalt ist in 0.4.2
> enthalten.

### Hinzugefügt / Added

- Panel: Zeitraum-Presets **Alles** (gesamter erkannter Statistik-Zeitraum) und
  **Vorletztes Jahr**; die Jahres-Buttons zeigen die konkrete Jahreszahl als Tooltip.

### Geändert / Changed

- Kommentare und Docstrings auf den v0.4-Stand gebracht (`DEFAULT_MAX_RATE_PER_HOUR` ist nur
  noch Rückfall, Selbst-Modus in `reference.py`).

## [0.4.0] — 2026-07-30

### Hinzugefügt / Added

- **Service `detect`** (nur lesen): schlägt Quelle, Zyklus, Zeitraum und Ausreißer-Schwelle
  automatisch vor — Zyklus aus dem Entity-Namen, Quelle aus der `utility_meter`-Konfiguration,
  Zeitraum aus den vorhandenen Statistiken.
- **Selbst-Modus:** `reference_id` ist optional; leer bedeutet, der Zähler ist seine eigene
  Quelle und nur seine Ausreißer werden geglättet.
- `engine.estimate_max_rate`: die Ausreißer-Schwelle wird aus der Median-Stundenrate der
  Daten geschätzt (× großzügiger Faktor, mit Untergrenze).
- Panel: Zähler auswählen füllt Quelle, Zyklus und Zeitraum automatisch; Button
  **↻ Auto-erkennen**, farbige Info-Icons, größere Schrift.

### Entfernt / Removed

- Das Feld **Max. Rate** aus Panel und `services.yaml` — eine Zahl, die niemand belastbar
  schätzen kann, gehört nicht in ein Formular. `DEFAULT_MAX_RATE_PER_HOUR` bleibt als
  Rückfall, wenn keine Daten zum Schätzen vorliegen.

## [0.3.1] – [0.3.4] — 2026-07-30

### Hinzugefügt / Added

- Panel folgt der Home-Assistant-Sprache (`hass.language`, Rückfall Englisch) mit manuellem
  Umschalter **Auto/DE/EN**.
- Sensor-Filter mit `*` als Platzhalter und Umschalter **nur Energie**.
- Info-Tooltips je Feld, Zeitraum-Presets (dieses/letztes Jahr, Monat, 12 Monate), native
  Kalender-Auswahl für die Datumsfelder.

### Behoben / Fixed

- Panel-Layout (`box-sizing`/Breite).

## [0.3.0] — 2026-07-30

### Hinzugefügt / Added

- **Dashboard-Panel in der Seitenleiste** (`panel_custom`, nur Admin): Simulation starten und
  **Vorher/Nachher-Graphen** als selbst gerendertes SVG ansehen — ein einzelnes Custom
  Element ohne Build-Schritt, Framework oder CDN-Abhängigkeit.
- `engine/periods.py`: Monats-Aggregate für die Graphen, DST-korrekt in lokaler Zeitzone.

## [0.2.0] — 2026-07-30

### Hinzugefügt / Added

- **Zentrales `READ_ONLY_MODE`-Schloss** in der einzigen Schreibfunktion
  (`recorder_io.write_statistics`) — kein Codepfad kann schreiben, solange es aktiv ist.
- Services **`backup`** (mit Zeitstempel, wiederholbar) und **`restore`**; jeder `fix` legt
  vorher automatisch eine JSON-Sicherung an.
- Zweisprachige Service-Beschreibungen (DE/EN), Ein-Klick-HACS-Button im README.

### Behoben / Fixed

- CI (Hassfest, HACS-Validierung, Engine-Tests).

## [0.1.0] — 2026-07-30

### Hinzugefügt / Added

- Erste Fassung als HACS-Integration: erkennt und repariert beschädigte Langzeitstatistiken
  von Zählern.
- Services `simulate` (nur lesen, Vorschau) und `fix` über die **offiziellen** Recorder-APIs
  (`import_statistics`) — kein direkter SQLite-Zugriff.
- HA-unabhängige Mechanik in `engine/`: Reset-Regeln je Zyklus (DST-korrekt),
  Ausreißer-Erkennung mit **Offset-Methode** (nicht kaskadierend), Ableitung von
  `state`/`sum` und Plausibilitätsprüfung `Endsumme == Quell-Delta`.
- Unit-Tests ohne Home Assistant (`pytest tests/`).

[Unreleased]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.5.4...v0.6.0
[0.5.4]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.4.5...v0.5.0
[0.4.5]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.4.4...v0.4.5
[0.4.4]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.4.0...v0.4.2
[0.4.1]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/turbolooser/ha-statistics-toolset/compare/v0.3.4...v0.4.0
[0.3.0]: https://github.com/turbolooser/ha-statistics-toolset/releases/tag/v0.3.0
