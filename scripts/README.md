# Skripte / Scripts

Zwei Werkzeuge zum Prüfen der Integration. Beide enthalten **keine** Zugangsdaten, Adressen
oder Entity-IDs — die Zähler werden auf der Instanz gefunden, auf die man sie richtet.
*Neither script contains credentials, hostnames or entity ids.*

## `live_check.py` — Konsistenzprüfung gegen echte Daten

Ruft **nur lesende** Services (`detect`, `simulate`) und `recorder/statistics_during_period`
auf. Es wird nichts geschrieben; der Read-only-Schalter der Integration bleibt unberührt.

```bash
pip install websockets
export HA_TOKEN=<Long-Lived Access Token>          # Profil → Sicherheit → Token erstellen
export HA_URL=ws://homeassistant.local:8123/api/websocket   # optional
python3 scripts/live_check.py --verbose
```

Es sucht die Zähler selbst, nimmt bis zu zwei pro Zyklustyp (damit jede Reset-Regel läuft)
und rechnet jede Vorschau gegen die Rohdaten nach:

| Prüfung | Warum |
|---|---|
| Summe == Rohdelta − ausgewiesene Ausreißer | deckt still verschwundene Mengen auf |
| Referenz-Delta == Summe | die Plausibilitätszahl der Integration muss zur Vorschau passen |
| Punkte == Stundenwerte im Recorder | erkennt abgeschnittene oder doppelte Bereiche |
| aktuelle Endsumme == Zählerstand | Vorschau liest denselben Zähler |
| Balkensumme == Endsumme, keine negativen Balken | Grafik und Zahl dürfen nicht auseinanderlaufen |
| Klemm-Warnung nur bei echter Lücke | Stundenraster ist keine Datenlücke |
| **jede** Abweichung vom Rohwert ist ausgewiesen | eine Reparatur darf nichts stillschweigend verwerfen |

Rückgabewert ≠ 0, wenn eine Prüfung fehlschlägt. Die Ausgabe nennt die Entity-IDs der
geprüften Instanz — sie gehört also nicht in ein öffentliches Issue, ohne sie zu kürzen.

## `make_test_sensors.py` — Testzähler aus einem echten Zähler klonen

Liest einen vorhandenen Zähler (**nur lesend**) und schreibt seinen Verlauf unter Test-IDs
zurück, in fünf Varianten. So lassen sich Reparieren und Wiederherstellen an realistischen
Daten üben, ohne die Originale anzufassen.

```bash
export HA_TOKEN=<Long-Lived Access Token>
python3 scripts/make_test_sensors.py --source sensor.dein_zaehler --dry-run   # erst ansehen
python3 scripts/make_test_sensors.py --source sensor.dein_zaehler            # dann schreiben
```

| Variante | Inhalt | prüft |
|---|---|---|
| `clean` | 1:1-Klon | eine Reparatur darf hier nichts verändern |
| `spike` | ein unplausibler Sprung, der in allen Folgewerten steckt | Ausreißer-Erkennung und deren Ausweisung |
| `gap` | eine Woche fehlt | Klemmung und Bereichserkennung |
| `short` | nur die letzten 30 Tage | Zähler jünger als seine Quelle |
| `frozen` | Werte stehen ab der Mitte still | steckengebliebener Zähler |

Schutz: Jede Ziel-ID **muss** `test` enthalten, sonst verweigert das Skript den Start; der
Quellzähler wird nie geschrieben. In Verbindung mit `WRITE_ALLOWLIST` in `const.py` weist die
Integration selbst alles ab, was nicht in der Liste steht.

Entfernen lassen sich die Testreihen später unter **Entwicklerwerkzeuge → Statistiken**, wo
verwaiste Statistik-IDs gelöscht werden können (die Recorder-WebSocket-API bietet kein
Löschen).

## `bench_engine.py` — Laufzeit der Mechanik

Rein synthetische Daten, kein Home Assistant nötig. Jede gemessene Millisekunde fällt in
einem Service-Aufruf an, ist also Wartezeit für den Nutzer.

```bash
python3 scripts/bench_engine.py --points 21600
```

Warnt und endet mit Rückgabewert 1, wenn ein Durchlauf über zwei Sekunden rechnet — der
Anlass war ein quadratischer Aufwand in `value_at`, der `derive_series` auf ~9,8 s für
21 600 Punkte gebracht hatte (jetzt ~80 ms).
