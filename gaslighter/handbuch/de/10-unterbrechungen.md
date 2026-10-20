# Unterbrechungen, Datenkette und Updates

## Unterbrechungen {#liste}

Läuft das Add-on nicht (Stromausfall, Home Assistant neu gestartet, Update über den Add-on-Store), fehlt die Aufnahme. GLighter merkt sich das beim nächsten Start und zeigt es in Protokolle unter der Zusammenfassung:

- **ohne Herunterfahren beendet, z. B. Stromausfall** – das Add-on konnte sich nicht abmelden (Strom weg, Absturz).
- **von Home Assistant angehalten / neu gestartet** – sauber beendet (Neustart, Add-on gestoppt).
- **Update** – neue Fassung installiert.
- **Lücke in der Tagesaufzeichnung, Ursache nicht protokolliert** – in den Daten fehlen mehr als 90 Sekunden, ohne dass der Start es gemerkt hat (z. B. Umzug auf eine neue Installation). Gilt für das Mikrofon am Rechner und Streams; bewusste Pausen zählen nicht, Handys werden nicht geprüft.

Nach einem Stromausfall startet Home Assistant das Add-on von selbst, sobald der Rechner wieder läuft.

## Kommentar setzen {#kommentar}

![Kommentar direkt im Verlauf](unterbrechung_{lang}.png)

- Im **Verlauf** auf die schraffierte Fläche klicken bzw. tippen – ein kleines Fenster mit Zeitraum und Ursache öffnet sich. Text eingeben, z. B. „Sicherung rausgeflogen“, **Speichern**.
- Oder in der Liste „Nicht aufgezeichnet …“ auf **📝 Kommentar**.

Der Kommentar steht in der Schraffur, in der Liste, im Druck und im Lärmprotokoll. Die Aufzeichnung selbst bleibt unverändert.

## Watchdog {#watchdog}

Auf der Add-on-Seite in Home Assistant den Schalter **Watchdog** einschalten: Wird das Add-on unerwartet beendet, startet Home Assistant es neu.

## Datenkette (Prüfsummen) {#datenkette}

Jede geschriebene Minute der Tagesaufzeichnung bekommt eine SHA-256-Prüfsumme, die auf der vorherigen aufbaut. Ändert jemand nachträglich einen Wert oder entfernt eine Minute, passt die Kette ab dieser Stelle nicht mehr.

- Protokolle zeigt „🛡 Datenkette geprüft: vollständig und unverändert“ bzw. wo es abweicht.
- Das Lärmprotokoll listet je Gerät und Tag das Ergebnis und die letzte Prüfsumme.
- Jedes Gerät meldet stündlich seine Prüfsumme an Home Assistant (dort unabhängig gespeichert).
- Aus einer Sicherung ergänzte Tage haben einen eigenen Abschnitt in der Kette, siehe [Sicherung](#sicherung/zusammenfuehren).

## Updates {#updates}

> **Neu (Sicherheit):** Updates aus `share` werden nur übernommen, wenn in der Konfiguration **„Updates aus /share annehmen“ (`share_update`)** eingeschaltet ist **und** der Ordner eine gültige Signatur von G-Simulation enthält (`manifest.txt` + `manifest.sig`). Unsignierte oder veränderte Ordner werden abgelehnt (Hinweis im Protokoll). Gestartet wird eine geprüfte Kopie unter `/data/update_run`.

**Ohne Aufnahmelücke:** den Ordner `gaslighter` aus der Update-Zip per Samba nach `\\homeassistant\share\gaslighter_update\` kopieren (vorhandene Dateien überschreiben). Nach 10–20 s startet nur das Programm neu; die Aufnahme läuft weiter und wird nachgeliefert. Startet die neue Fassung nicht, nimmt das Add-on automatisch wieder die vorige.

**Volle Installation** (nur wenn eine Version es verlangt, z. B. neuer Name oder Watchdog): den Ordner aus der vollen Zip nach `\\homeassistant\addons\` kopieren und das Add-on in Home Assistant neu erstellen. Das gibt eine kurze Lücke.

Jeder Start, jedes Update und jede Unterbrechung steht mit Uhrzeit und Version in Protokolle und im Lärmprotokoll.
