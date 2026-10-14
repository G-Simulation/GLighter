# Sicherung, Import und Export

<a id="export"></a>

## Sicherung herunterladen

⚙ Einstellungen → Allgemein → **Sicherung der ganzen App** → **⬇ Sicherung herunterladen**. Die ZIP-Datei enthält alles: Einstellungen, Geräte, Zeitprofile, Regeln, `log.csv` und alle Protokolldateien, Tagesaufzeichnungen mit Prüfsummen, KI-Ergebnisse, Tonprofile, Notizen, Kommentare zu Unterbrechungen, benannte Bereiche, Listen, Videos und – falls gespeichert – Ton.

> Die Datei kann groß werden (Hunderte MB). Am besten regelmäßig herunterladen und an einem anderen Ort aufbewahren.

Zum Weiterverarbeiten gibt es außerdem `log.csv` (Reiter Protokolle), die Notizen als CSV (📝 Alle Notizen) und das Lärmprotokoll als PDF.

<a id="import"></a>

## Sicherung einspielen

> **🔒 Pro:** Der erste Import ist kostenlos (z. B. für den Umzug), weitere Importe gehören zu [GasLighter Pro](14-pro.md#umzug). Das Herunterladen einer Sicherung ist immer frei.

![Vorschau beim Einspielen](../../gaslighter/app/web/hb/sicherung_de.png)

1. **📂 Sicherung wählen** und **Sicherung prüfen …** – die Datei wird hochgeladen und angesehen, noch nichts verändert.
2. Die Vorschau zeigt Version und Datum der Sicherung und – mit „Einstellungen und Geräte übernehmen“ – jedes Gerät aus der Sicherung:
   - **gibt es hier schon** (wird ersetzt) oder **neu**,
   - **bereit**, **Handy** (verbindet sich, sobald es die App öffnet) oder **nicht erreichbar** (wird ausgeschaltet übernommen, mit Hinweis „bitte prüfen“).
   - Geräte, die nur hier eingerichtet sind, **bleiben unverändert**.
   - Gibt es das Mikrofon der Sicherung hier nicht, bleibt das bisherige eingestellt.
3. Häkchen setzen oder entfernen und **Jetzt einspielen**.

Danach steht ein Bericht da: neue Dateien, zusammengeführte Tage, übersprungene Tage und übernommene Geräte.

<a id="ziel"></a>

### Tägliche Sicherung auf Netzlaufwerk, NAS oder USB

⚙ Einstellungen → Speichern & Ton → **Tägliche Sicherung**. Ist ein Ziel eingestellt, kopiert GasLighter jeden Tag (Standard 03:30) alles Neue dorthin – dieselben Dateien wie in der ZIP-Sicherung, aber **inkrementell**: nur neue und geänderte Dateien, jede danach mit SHA-256 geprüft.

- **Im Ziel wird nie etwas gelöscht.** Ändert sich eine schon gesicherte Datei nachträglich, bleibt die alte Fassung als `….alt-JJJJMMTT-hhmmss` daneben liegen.
- **Ziel nicht erreichbar** (NAS aus, WLAN weg): Die Aufzeichnung läuft normal weiter auf diesem Gerät. Stündlich wird es erneut versucht, und der nächste Lauf holt alles Fehlende nach.
- **Jetzt sichern** startet sofort einen Lauf; daneben stehen letzter Lauf, Anzahl der Dateien und Fehler.

**Beispiele für das Ziel**

| Ziel | So einrichten | Ordner eintragen |
|---|---|---|
| NAS / Windows-Freigabe (SMB) | Home Assistant → Einstellungen → System → Speicher → **Netzwerkspeicher hinzufügen**, Name z. B. `nas_gaslighter`, Verwendung **Freigabe** | `/share/nas_gaslighter` |
| NAS als Medienordner | wie oben, Verwendung **Medien** | `/media/nas_gaslighter` |
| USB-Platte am Home-Assistant-Gerät | Platte anschließen (erscheint unter `/media`) | z. B. `/media/usb/gaslighter` |

> Das Ziel muss schon vorhanden sein und darf **nicht auf demselben Speicher** liegen wie die Daten. Sonst würde ein nicht eingebundenes Netzlaufwerk unbemerkt den eigenen Speicher füllen – GasLighter meldet das dann als Fehler und kopiert nichts.

<a id="auslagern"></a>

### Platz sparen

Mit **„Platz sparen: alte Daten nur im Ziel behalten“** werden Dateien, die älter sind als „Löschen nach (Tagen)“ und geprüft im Ziel liegen, hier durch einen Verweis auf die Kopie ersetzt. **Protokolle, Verlauf, Druck und Prüfsummen-Kette funktionieren weiter** – sie lesen diese Tage aus dem Ziel. Schläft das Netzlaufwerk, dauert das erste Laden etwas länger („Netzlaufwerk wacht evtl. gerade auf“). Ist es gar nicht erreichbar, fehlen diese alten Tage, bis es wieder da ist. Einstellungen, `log.csv` und die Daten der letzten Tage bleiben immer hier.

Ist zusätzlich **„Alte Aufnahmen automatisch löschen“** eingeschaltet, löscht GasLighter bei eingestelltem Ziel nur noch, was geprüft im Ziel liegt.

<a id="zusammenfuehren"></a>

## Was beim Einspielen passiert

- **Nichts wird doppelt und nichts überschrieben**: vorhandene Störungen, Notizen und Listen bleiben, nur Fehlendes kommt dazu. Mehrmals einspielen ist unschädlich.
- **Tage, die es schon gibt** (z. B. „heute“ nach einer Neuinstallation): Die fehlenden Minuten werden ergänzt. Die Prüfsummen-Kette bleibt prüfbar – der eingespielte Teil bekommt einen eigenen Abschnitt, und unter „Unterbrechungen“ steht „Import …: um N Minuten ergänzt“. Überschneiden sich die Zeiten mit anderen Daten, wird der Tag übersprungen und im Bericht genannt.
- **Geräte, die es nicht mehr gibt**: Ihre Daten werden trotzdem eingespielt und sind als „(ehemalig)“ im Verlauf, im Gerätefilter und im Druck auswählbar.
- Speicherorte (Ausgabe- und Clip-Ordner) bleiben die dieses Systems.

<a id="zuruecksetzen"></a>

## Zurücksetzen

⚙ → Allgemein → **Zurücksetzen**: wahlweise Messdaten & Störungen, Notizen & Listen, Tonprofile oder Einstellungen auf Standard. Geräte und Verbindungen bleiben immer. Vorher wird eine Sicherung angeboten.

<a id="suchverzeichnis"></a>

## Suchverzeichnis

GasLighter führt ein **Suchverzeichnis** (SQLite-Datei `suchindex.sqlite` im App-Datenordner). Es beschleunigt Lärmprotokolle über Wochen und Monate:

- **Kettenprüfung je Tag:** Das Ergebnis wird mit einer SHA-256-Prüfsumme über den *Inhalt* aller Dateien des Tages gespeichert. Ändert sich auch nur ein Byte, wird der Tag neu geprüft – die Prüfung ist genauso streng wie ohne Verzeichnis.
- **Verdichtete Tagesspuren** (je 10 Sekunden) für die Grafiken im Lärmprotokoll.

Das Verzeichnis enthält nur abgeleitete Daten, ändert nie Aufzeichnung, Datenkette oder Störungen, ist nicht in der Sicherung und füllt sich nach dem Start langsam im Hintergrund. **Einstellungen → Allgemein → Sicherung → Neu aufbauen** leert es; es baut sich danach von selbst wieder auf. Fehlt es oder ist es beschädigt, arbeitet GasLighter ohne – nur langsamer.

---
[← Drucken und Lärmprotokoll](08-drucken.md) · [Inhalt](README.md) · [Unterbrechungen, Datenkette und Updates →](10-unterbrechungen.md)
