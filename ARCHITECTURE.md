# Architektur & Design / Architecture & Design

> Primär Deutsch, Kernbegriffe englisch. / German first, key terms in English.

## Leitprinzipien / Guiding principles

1. **Preview vor Schreiben.** Nichts wird geschrieben, ohne dass der Nutzer eine
   Simulation (`simulate`) gesehen und bestätigt hat.
2. **Sicherheit zuerst / defense in depth.** Ein zentrales `READ_ONLY_MODE`-Schloss in der
   *einzigen* Schreibfunktion (`recorder_io.write_statistics`) — kein Codepfad kann
   schreiben, solange es aktiv ist. Zusätzlich `confirm`-Gate an `fix`/`restore`.
3. **Reversibel.** Jeder `fix` legt vorher automatisch eine mit Zeitstempel versehene
   JSON-Sicherung an; `restore` spielt sie zurück.
4. **Nur offizielle APIs.** Ausschließlich Recorder-APIs (`import_statistics`,
   `adjust_sum_statistics`) — nie direkter SQLite-Zugriff.
5. **Modular & testbar.** Die reine Mechanik (`engine/`) ist Home-Assistant-unabhängig und
   per `pytest` ohne HA testbar. Der HA-Anschluss ist dünn und ersetzbar.

## Modul-Struktur / Modules

```
custom_components/statistics_toolset/
├── engine/                 # HA-unabhängige Kern-Mechanik (unit-getestet)
│   ├── cycles.py           #   Reset-Regeln je Zählertyp (DST-korrekt)
│   ├── outliers.py         #   Ausreißer erkennen + Offset-Methode + Schwelle schätzen
│   ├── reference.py        #   Referenz laden + glätten, value_at()
│   ├── derive.py           #   state/sum ableiten + Plausibilitäts-Check
│   └── periods.py          #   kumulative Reihe → Monatsbalken (für die Graphen)
├── panel/panel.js          # Sidebar-Panel: Custom Element, keine externen Abhängigkeiten
├── recorder_io.py          # HA-Glue: lesen / schreiben (Schreibschloss hier) + stat_range
├── coordinator.py          # Orchestrierung: detect / simulate / fix / backup / restore
├── __init__.py             # Service-Registrierung, Schemas, Read-only-Gate, Panel-Anmeldung
├── const.py                # Konstanten inkl. READ_ONLY_MODE
└── services.yaml           # zweisprachige Service-Beschreibungen (DE/EN)
```

**Abhängigkeitsrichtung:** `__init__` → `coordinator` → (`engine`, `recorder_io`).
`engine` hängt von nichts aus HA ab. So bleibt die Logik isoliert prüfbar.

## Datenfluss / Data flow

- **detect** (read-only): Zyklus aus dem Entity-Namen raten → Quelle über die
  Erkennungskette (siehe unten) → Datenbereich über `stat_range` (Monatsbuckets, billig) →
  Ausreißer-Schwelle über `estimate_max_rate`. Liefert reine **Vorschläge** als
  Service-Response; nichts wird angewandt.
- **simulate** (read-only): Quelle lesen → `build_reference` (glätten) → `derive_series`
  → `plausibility_check` → Vorschau (Ausreißer, aktuelle vs. vorgeschlagene Endsumme,
  Monatsbalken via `aggregate_periods`).
- **backup** (read-only auf DB): Reihe lesen → Zeitstempel-JSON schreiben (inkl. Einheit,
  damit `restore` autark ist).
- **fix** (schreibt): `simulate` → automatische `backup` → Reihe neu ableiten →
  `plausibility_check` → `write_statistics`. Gesperrt bei `READ_ONLY_MODE`.
- **restore** (schreibt): JSON lesen → `write_statistics`. Gesperrt bei `READ_ONLY_MODE`.

## Quell-Erkennung: Kette statt einer Annahme

Ein Zähler verrät seine Quelle je nach Herkunft an einer anderen Stelle. `_guess_source`
probiert daher vier Wege in dieser Reihenfolge und liefert `(source, how)` zurück — `how`
kommt als `source_via` in die Response, damit nachvollziehbar bleibt, *warum* eine Quelle
vorgeschlagen wird:

| # | Weg | Deckt ab |
|---|---|---|
| 1 | `config_entry` — Entity- → Config-Registry, `options/data["source"]` | über die UI angelegte Helfer |
| 2 | `utility_meter` — `hass.data["utility_meter"]`, Meter über seine `utility_meter_sensors` matchen | **YAML/Package-Zähler** (haben keinen Config-Entry) |
| 3 | `state_attribute` — Attribut `source` der Entität | Riemann-`integration`-Sensoren, die es selbst veröffentlichen |
| 4 | `entity_object` — laufende Entität, `_sensor_source_id` / `_source_entity` | Rest; privat, daher komplett in `try/except` |

Die `hass.data`-Schlüssel werden **als Strings** benutzt (`"utility_meter"`,
`"utility_meter_sensors"`, `"entity_components"` — alle sind `HassKey`, das von `str` erbt),
damit weder ein Import noch eine `manifest`-Abhängigkeit auf `utility_meter` entsteht. Jeder
Weg ist defensiv: fehlende oder unerwartet geformte Strukturen führen zu „nicht gefunden",
nie zu einer Exception. Eine Selbstreferenz (`source == statistic_id`) gilt nicht als Quelle.

**Verifikation statt Vertrauen:** Eine gefundene Quelle ohne eigene Langzeitstatistik wird
verworfen (`source_via = "discarded:…:no_statistics"`) und der Selbst-Modus genutzt — sonst
würde `simulate` erst später mit einem `PlausibilityError` scheitern. Beginnt die Quelle
später als der Zähler, zieht `detect` den Bereichsstart nach, denn davor kann nichts
rekonstruiert werden. „Statistiken vorhanden" heißt dabei **`sum`-Werte vorhanden**: ein
Mittelwert-Sensor (z. B. Leistung in W) liefert auf eine `sum`-Abfrage ebenfalls Buckets,
nur ohne den Schlüssel — würde man die mitzählen, gälte ein Leistungssensor als brauchbare
kumulative Quelle.

## Zeitfenster: warum sie die häufigste Fehlerquelle waren

Drei Dinge liefen auseinander und erzeugten `PlausibilityError`:

1. **Bereichsstart zu grob.** `stat_range` fand den ersten *Monatsbucket*; dessen Start ist
   der Monatserste, der erste echte Datenpunkt kann Tage später liegen. Der vorgeschlagene
   Start lag damit *vor* der Reihe. Jetzt wird in diesem ersten Monat mit Stundenauflösung
   nachgesehen — ein zusätzlicher, billiger Aufruf für einen exakten Start.
2. **Zu früher Start wird geklemmt.** `_clamped_start` hebt den Nullpunkt auf den ersten
   Referenzpunkt und legt einen Hinweis in `Preview.warnings`, statt den ganzen Lauf
   abzulehnen. `fix` klemmt identisch — geschriebene und gezeigte Reihe müssen gleich sein.
3. **Leerer Zeitraum meldet Klartext.** Liegt der Bereich komplett vor den Daten der Quelle
   (z. B. Preset „Vorletztes Jahr" bei einer Quelle ab diesem Jahr), nennt der Fehler den
   verfügbaren Zeitraum. Das Panel graut solche Presets zusätzlich aus, sobald die Erkennung
   den Datenbeginn kennt.

## Zyklus: lesen statt raten

Der Zyklus bestimmt die Reset-Regel — ein falscher Wert baut die Reihe falsch wieder auf.
Deshalb wird er **exakt** aus `hass.data["utility_meter"]` gelesen (`cycle`, intern
`CONF_METER_TYPE`); die Namensheuristik (`_jahr`/`_monat`/…) ist nur noch Rückfall für
Zähler, die kein `utility_meter` sind. `detect` meldet die Herkunft in `cycle_via`, und das
Panel warnt sichtbar, wenn geraten wurde.

Unterstützt werden **alle** `utility_meter`-Perioden, mit den Reset-Punkten aus dessen
`PERIOD2CRON` (Offset 0): `quarter-hourly` `0/15 * * * *` · `hourly` `0 * * * *` · `daily` ·
`weekly` (Montag) · `monthly` · `bimonthly` `1 */2` → Monate 1,3,5,7,9,11 · `quarterly`
`1 */3` → 1,4,7,10 · `yearly`. Dazu `none` für einen Meter **ohne** Zyklus: ein permanenter
Gesamtzähler, der nie zurückgesetzt wird — umgesetzt als Reset-Zeitpunkt vor allen Daten,
womit `state == sum` gilt, ohne Sonderfall in `derive_series`. Ein Meter mit freiem
`cron`-Muster lässt sich nicht auf diese Regeln abbilden und wird als *nicht unterstützt*
gemeldet, statt stillschweigend auf etwas Ähnliches abgebildet zu werden.

## Mehrstufige Zähler: die Kette nach oben

Zähler sind oft in Stufen abgeleitet: `…_monthly` → `…_total_permanent`
→ `…_integration` → *(Leistungssensor in W)*. `_source_chain` verfolgt diese
Referenzen aufwärts und `detect` schlägt die **Wurzel** vor, nicht die direkt konfigurierte
Quelle: je weniger abgeleitet, desto weniger Fehler kann sie geerbt haben — und die Wurzel
hat häufig die längere Historie, erlaubt also eine weiter zurückreichende Reparatur.

Grenzen der Verfolgung: nur Stufen mit **kumulativen** (`sum`) Statistiken werden verfolgt,
womit die Kette am Mittelwert-Sensor (W) korrekt endet; `max_depth` und ein `seen`-Set
verhindern Endlosläufe bei Ringreferenzen. Die ganze Kette geht als `source_chain` in die
Response — der Vorschlag bleibt damit nachprüfbar statt magisch.

## Modi: Rekonstruktion vs. Selbst-Modus

`reference_id` ist optional (seit v0.4). Leer heißt **Selbst-Modus**: der Zähler wird seine
eigene Quelle, es werden also nur seine Ausreißer geglättet. Das ist der ehrlichere Default
für den häufigen Fall, dass es überhaupt keinen unabhängigen, langlaufenden Sensor gibt —
ohne diesen Modus müsste der Nutzer eine Quelle *erfinden*, was die Reihe verfälscht.
Implementiert an genau einer Stelle (`ref_source = reference_id or statistic_id`), damit
beide Modi denselben Code- und Prüfpfad durchlaufen.

## Automatik statt Magie-Zahlen

Die Ausreißer-Schwelle war ursprünglich eine Konstante
(`DEFAULT_MAX_RATE_PER_HOUR = 25 kWh/h`) und damit eine Annahme über den Haushalt des
Nutzers. `engine.estimate_max_rate` bestimmt sie stattdessen aus den Daten: **Median** der
stündlichen Zuwächse (robust gegen einzelne Extremwerte) × großzügiger Faktor, nie unter
einer Untergrenze. Echte Spitzen bleiben darunter, Phantom-Sprünge liegen um
Größenordnungen darüber. Der Wert wird berechnet, wenn `max_rate_per_hour <= 0` ist; die
Konstante dient nur noch als Rückfall, wenn gar keine Daten vorliegen. Das Feld ist deshalb
aus Panel und `services.yaml` entfernt — eine Zahl, die niemand belastbar schätzen kann,
gehört nicht in ein Formular.

Ebenso `detect`: Zyklus, Quelle und Zeitraum sind aus dem System **ableitbar**, also werden
sie abgeleitet statt abgefragt. Alle Ergebnisse bleiben Vorschläge und überschreibbar —
Automatik darf Arbeit sparen, aber dem Nutzer nicht die Kontrolle nehmen.

## Dashboard / GUI (umgesetzt, v0.3–v0.4)

Ziel: die Datenreihen **grafisch** vergleichen — aktuelle Reihe **oben**, simulierter Fix
**darunter** (Vorher/Nachher), direkt aus der Simulation heraus.

1. **Stufe 1 (datenseitig, ✅):** `simulate` liefert in der Service-Response kompakte
   Monats-Aggregate (`engine/periods.py`) für *aktuell* und *vorgeschlagen* — klein genug
   für eine Response, aussagekräftig für einen Graph.
2. **Stufe 2 (Lovelace-Vorlage):** verworfen — Stufe 3 macht sie überflüssig, und eine
   Vorlage hätte ApexCharts als externe Abhängigkeit gebraucht.
3. **Stufe 3 (eigenes Panel, ✅):** `panel/panel.js`, als `panel_custom` in der Seitenleiste
   registriert (`require_admin`), mit Auto-Erkennung, Sensor-Filter, Zeitraum-Presets und
   Vorher/Nachher-Balken als **selbst gerendertes SVG**. Bewusst ein einzelnes Custom
   Element ohne Build-Schritt, ohne Framework und ohne CDN-Abhängigkeit: HA-Themevariablen
   für die Optik, `localStorage` nur für die Sprachwahl (Auto/DE/EN).

Bewusst **nicht** direkt in die Statistik geschrieben, um die Vorschau zu erzeugen — die
Graphen entstehen aus der Response, nicht durch ein Probe-Schreiben. Das Panel ist
**read-only**: es ruft ausschließlich `detect` und `simulate`; die Schreibpfade bleiben den
Services vorbehalten, wo `confirm: true` erzwungen wird. Die Panel-Registrierung ist
best-effort in `try/except` — ein Frontend-Fehler darf die Services nie blockieren.

## Erweiterungspunkte / Extension points

- **`transfer`**: Historie eines alten Sensors auf einen umbenannten übertragen
  (statistic_id-Umzug über `import_statistics`).
- **Rand-Handling** (aus der Praxis gelernt): short_term-Basis-`adjust`, `calibrate` nur bei
  falschem Live-State, Rand-Verifikation, `adjust→re-import` wenn die Referenz bis „jetzt"
  reicht. Kommt als robuster Schreib-Nachlauf in den `coordinator`.
- **`config_flow`**: optionale UI-Konfiguration (Standard-Quelle je Zähler, abweichender
  Backup-Ordner). Die Schwellwerte gehören ausdrücklich **nicht** dazu — siehe „Automatik
  statt Magie-Zahlen".
- **Cross-Check**: eine zweite, unabhängige Quelle gegenrechnen und die Abweichung als
  Warnung in die `Preview` legen (`Preview.warnings` existiert schon, wird noch nicht gefüllt).
- **Schreiben aus dem Panel**: `fix`/`restore` mit mehrstufiger Bestätigung; erst sinnvoll,
  wenn `READ_ONLY_MODE` bewusst abgeschaltet werden kann.
- ✅ **Beliebige Zeiträume**: erledigt über die Auto-Erkennung des Datenbereichs plus die
  Zeitraum-Presets im Panel (dieses/letztes Jahr, Monat, 12 Monate).

## Tests / CI

- `tests/` — Engine-Unit-Tests ohne HA (`pytest`), 6 Tests: Reset-Regeln, Nicht-Kaskadieren
  der Offset-Methode, Ausreißer-Erkennung, `value_at`-Stufenlookup, Monatsaggregation,
  Ableitung + Plausibilität.
- **Bekannte Lücke:** `estimate_max_rate` (v0.4) ist noch nicht unit-getestet; die
  HA-abhängigen Teile (`detect`, `recorder_io`, `coordinator`) sind es grundsätzlich nicht —
  bewusst, dafür ist die Grenze zwischen `engine/` und dem HA-Glue so scharf gezogen.
- `.github/workflows/validate.yml` — Hassfest, HACS-Validierung, Engine-Tests bei jedem Push.
