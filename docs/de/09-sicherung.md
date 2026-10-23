# Sicherung, Import und Export

<a id="export"></a>

## Sicherung herunterladen

⚙ Einstellungen → Speichern & Sicherung → **Sicherung herunterladen / einspielen (ZIP)** → **⬇ Sicherung herunterladen**. Die ZIP-Datei enthält alles: Einstellungen, Geräte, Zeitprofile, Regeln, `log.csv` und alle Protokolldateien, Tagesaufzeichnungen mit Prüfsummen, KI-Ergebnisse, Tonprofile, Notizen, Kommentare zu Unterbrechungen, benannte Bereiche, Listen, Kacheln, Anordnung der Ansichten (`layout.json`), Videos und – falls gespeichert – Ton.

> Die Datei kann groß werden (Hunderte MB). Am besten regelmäßig herunterladen und an einem anderen Ort aufbewahren.

**Ohne Geheimnisse:** Die normale Sicherung und die tägliche Sicherung auf Netzlaufwerk/NAS enthalten **nicht** den geheimen Schlüssel der Prüfkette (`kette_schluessel.json`), keine Passwörter von Netzwerk-Kameras und keine Handy-Kennungen. So taugt eine verlorene Sicherung nicht dazu, Daten unbemerkt neu durchzurechnen oder sich als dein Handy auszugeben.

<a id="umzug"></a>

### Umzug auf ein neues Gerät (mit Schlüssel)

Unter **🔑 Umzug auf neues Gerät (mit Schlüssel)** ein Kennwort (mindestens 8 Zeichen, zweimal) eingeben und **⬇ Umzugs-Sicherung herunterladen**. Die ZIP enthält zusätzlich den Kettenschlüssel und die Zugangsdaten – **verschlüsselt** mit dem Kennwort (scrypt und HMAC-SHA256, verschlüsseln und danach gegen Verändern sichern). Ohne das Kennwort lassen sie sich nicht lesen. Das Kennwort wandert nie in die Adresse und wird nicht gespeichert; bewahre es getrennt von der Datei auf.

Beim Einspielen fragt die Vorschau nach dem Kennwort. Ein falsches Kennwort bricht ab, bevor etwas eingespielt wird. Ohne Kennwort wird die Datei wie eine normale Sicherung eingespielt.

Zum Weiterverarbeiten gibt es außerdem `log.csv` (Reiter Protokolle), die Notizen als CSV (📝 Alle Notizen) und das Lärmprotokoll als PDF.

<a id="import"></a>

## Sicherung einspielen

> **🔒 Pro:** Der erste Import ist kostenlos (z. B. für den Umzug), weitere Importe gehören zu [GLighter Pro](14-pro.md#umzug). Das Herunterladen einer Sicherung ist immer frei.

![Vorschau beim Einspielen](../../gaslighter/app/web/hb/sicherung_de.png)

1. **📂 Sicherung wählen** und **Sicherung prüfen …** – die Datei wird hochgeladen und angesehen, noch nichts verändert.
2. Die Vorschau zeigt Version und Datum der Sicherung und – mit „Einstellungen und Geräte übernehmen“ – jedes Gerät aus der Sicherung:
   - **gibt es hier schon** (wird ersetzt) oder **neu**,
   - **bereit**, **Handy** (verbindet sich, sobald es die App öffnet) oder **nicht erreichbar** (wird ausgeschaltet übernommen, mit Hinweis „bitte prüfen“).
   - Geräte, die nur hier eingerichtet sind, **bleiben unverändert**.
   - Gibt es das Mikrofon der Sicherung hier nicht, bleibt das bisherige eingestellt.
3. Häkchen setzen oder entfernen und **Jetzt einspielen**.

Danach steht ein Bericht da: neue Dateien, zusammengeführte Tage, übersprungene Tage und übernommene Geräte.

**Ohne Schlüssel** (normale Sicherung auf einem anderen Gerät) bleiben die eingespielten Tage prüfbar: Der Bericht und das Lärmprotokoll sagen „Kette vollständig, Schlüssel fehlt: Echtheit nur mit Originalgerät prüfbar“ – geprüft wird, dass keine Minute fehlt und die Reihenfolge stimmt. Prüfsummen und Tagesdateien werden dabei nie verändert; welche Tage eingespielt wurden, steht in einer eigenen Datei (`kette_fremd.json`). Ältere Sicherungen (bis 1.79), die den Schlüssel noch enthalten, werden weiter angenommen.

**Handys** bekommen ohne Umzug eine neue Kennung – der Bericht nennt sie, die Handys müssen neu gekoppelt werden (Link oder QR-Code in der Gerätekarte). Fehlt das Passwort einer Netzwerk-Kamera, steht das Gerät auf „bitte prüfen“.

**Grenzen beim Einspielen:** GLighter prüft vor dem Auspacken die Anzahl der Einträge (höchstens 300 000) und den Platz, den die ausgepackten Dateien brauchen, gegen den freien Speicher. Die Gesamtgröße eines Uploads gilt ab dem ersten Teil.

<a id="ziel"></a>

### Tägliche Sicherung auf Netzlaufwerk, NAS oder USB

> **🔒 Pro:** Die tägliche Sicherung und „Platz sparen“ gehören zu [GLighter Pro](14-pro.md). **„⬇ Sicherung herunterladen“ und `log.csv` bleiben immer frei.** Läuft Pro ab, hält die tägliche Sicherung an; schon ausgelagerte Tage bleiben lesbar.

⚙ Einstellungen → Speichern & Sicherung → **Tägliche Sicherung**. Ist ein Ziel eingestellt, kopiert GLighter jeden Tag (Standard 03:30) alles Neue dorthin – dieselben Dateien wie in der ZIP-Sicherung, aber **inkrementell**: nur neue und geänderte Dateien, jede danach mit SHA-256 geprüft.

- **Im Ziel wird nie etwas gelöscht.** Ändert sich eine schon gesicherte Datei nachträglich, bleibt die alte Fassung als `….alt-JJJJMMTT-hhmmss` daneben liegen.
- **Ziel nicht erreichbar** (NAS aus, WLAN weg): Die Aufzeichnung läuft normal weiter auf diesem Gerät. Stündlich wird es erneut versucht, und der nächste Lauf holt alles Fehlende nach.
- **Jetzt sichern** startet sofort einen Lauf; daneben stehen letzter Lauf, Anzahl der Dateien und Fehler.

**Beispiele für das Ziel**

| Ziel | So einrichten | Ordner eintragen |
|---|---|---|
| NAS / Windows-Freigabe (SMB) | Home Assistant → Einstellungen → System → Speicher → **Netzwerkspeicher hinzufügen**, Name z. B. `nas_gaslighter`, Verwendung **Freigabe** | `/share/nas_gaslighter` |
| NAS als Medienordner | wie oben, Verwendung **Medien** | `/media/nas_gaslighter` |
| USB-Platte am Home-Assistant-Gerät | Platte anschließen (erscheint unter `/media`) | z. B. `/media/usb/gaslighter` |

> Das Ziel muss schon vorhanden sein und darf **nicht auf demselben Speicher** liegen wie die Daten. Sonst würde ein nicht eingebundenes Netzlaufwerk unbemerkt den eigenen Speicher füllen – GLighter meldet das dann als Fehler und kopiert nichts.

<a id="auslagern"></a>

### Platz sparen

Mit **„Platz sparen: alte Daten nur im Ziel behalten“** werden Dateien, die älter sind als „Löschen nach (Tagen)“ und geprüft im Ziel liegen, hier durch einen Verweis auf die Kopie ersetzt. **Protokolle, Verlauf, Druck und Prüfsummen-Kette funktionieren weiter** – sie lesen diese Tage aus dem Ziel. Schläft das Netzlaufwerk, dauert das erste Laden etwas länger („Netzlaufwerk wacht evtl. gerade auf“). Ist es gar nicht erreichbar, fehlen diese alten Tage, bis es wieder da ist. Einstellungen, `log.csv` und die Daten der letzten Tage bleiben immer hier.

Ist zusätzlich **„Alte Aufnahmen automatisch löschen“** eingeschaltet, löscht GLighter bei eingestelltem Ziel nur noch, was geprüft im Ziel liegt.

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

GLighter führt ein **Suchverzeichnis** (SQLite-Datei `suchindex.sqlite` im App-Datenordner). Es beschleunigt Lärmprotokolle über Wochen und Monate:

- **Kettenprüfung je Tag:** Das Ergebnis wird mit einer SHA-256-Prüfsumme über den *Inhalt* aller Dateien des Tages gespeichert. Ändert sich auch nur ein Byte, wird der Tag neu geprüft – die Prüfung ist genauso streng wie ohne Verzeichnis.
- **Verdichtete Tagesspuren** (je 10 Sekunden) für die Grafiken im Lärmprotokoll.

Das Verzeichnis enthält nur abgeleitete Daten, ändert nie Aufzeichnung, Datenkette oder Störungen, ist nicht in der Sicherung und füllt sich nach dem Start langsam im Hintergrund. **Einstellungen → Allgemein → Sicherung → Neu aufbauen** leert es; es baut sich danach von selbst wieder auf. Fehlt es oder ist es beschädigt, arbeitet GLighter ohne – nur langsamer.

---
[← Drucken und Lärmprotokoll](08-drucken.md) · [Inhalt](README.md) · [Unterbrechungen, Datenkette und Updates →](10-unterbrechungen.md)
