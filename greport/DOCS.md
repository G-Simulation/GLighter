# GReport

Eine kurze Hilfe gibt es auch in der App: „?“ oben rechts.

## Notiz jetzt
Oben steht groß die Uhrzeit – sie wird mit der Notiz festgehalten. Text eintippen (Enter speichert, Alt+Enter neue Zeile) oder Tasten der Schnellwahl antippen. Ohne Text bildet GReport aus den Tasten einen Satz, z. B. „Deutliche Schritte von oben“. Der Zeitpunkt ist der Moment des ersten Tastendrucks; unter „🕒 jetzt · Zeit ändern“ lassen sich von und bis von Hand setzen, „läuft noch“ setzt bis = beim Speichern. Mit ⧉ wird der Notizbereich als kleines Fenster abgedockt.

## Schnellwahl verwalten
⋯ → **Schnellwahl verwalten** (oder **＋ Eigene**, Rechtsklick bzw. lange auf ein Wort drücken):
- **Umbenennen:** jedes Wort, auch die eingebauten. Alte Notizen behalten ihre Zuordnung, nur die Beschriftung ändert sich.
- **Gruppe:** Woher, Was, Wie stark, Folgen, Maßnahmen, Sonstiges oder Eigene – davon hängt die Farbe ab.
- **Farbe der Gruppe:** Farbfeld neben der Gruppenüberschrift; gilt für alle Wörter der Gruppe, ↺ = Standardfarbe.
- **Pflicht:** Häkchen neben der Gruppe – sie bekommt ein Sternchen. Sind alle Pflicht-Gruppen gewählt, leuchten die Tasten und „Speichern“ pulsierend auf. Gespeichert wird trotzdem immer.
- **Reihenfolge:** „Nach Gebrauch“ (häufige Wörter nach vorne) oder „Fest angeordnet“ (ziehen oder ▲▼).
- **Zeigen:** Häkchen weg blendet ein Wort aus (auch in Home Assistant).
- **Auf Standard zurücksetzen:** eingebaute Wörter, Gruppen und Reihenfolge; eigene Wörter bleiben.

Diese Wörter stehen auch in Home Assistant in der Auswahlliste „Schnellwahl“. Ohne Pro sind 5 eigene Wörter möglich. Mit Pro stellst du unter „Eigene Tasten höchstens“ bis zu 200 ein (Standard 40), und unter „Je Gruppe zeigen“, wie viele Tasten je Gruppe sichtbar sind (der Rest hinter „+ mehr“, 0 = alle).

## Datum und Uhrzeit
⋯ → **Datum und Uhrzeit**: Datum (18.10.2026, 18.10.26, So. 18.10., 2026-10-18, 18. Okt. 2026), Uhrzeit (mit/ohne Sekunden, 12 Stunden), Wochentag davor, „Heute/Gestern“ in der Liste. Gilt in der App und in der Export-Tabelle.

## Home Assistant
- **Logbuch:** jede neue Notiz erscheint als Eintrag „GReport“ (abschaltbar in der Konfiguration).
- **Auswahlliste „Schnellwahl“ und Knopf „Hinzufügen“** (Gerät „GReport“, braucht den MQTT-Broker Mosquitto): Wort wählen, Knopf drücken – die Notiz ist mit der Uhrzeit angelegt. Der Knopf lässt sich auch in Automationen verwenden (z. B. Zigbee-Taster).

## Mit GLighter
Ist GLighter installiert, findet es GReport selbst (über `/share/greport`). Mit GLighter Pro erscheinen die Notizen dort an den Störungen, im Verlauf und im Lärmprotokoll; geändert werden sie in GReport.

## Sicherung
Menü ⋯ → **Sicherung herunterladen (ZIP)** ist immer frei. Mit Pro zusätzlich eine tägliche Sicherung nach `/share/greport/sicherung` (14 Tage).

## Textdatei & Import/Export (Pro)
Menü ⋯ → **Textdatei & Import/Export**.

**Tagebuch als Textdatei:** Einschalten und Datei wählen (unter `/share` oder `/media`, Standard `/share/greport/greport_tagebuch.txt`). GReport führt die Datei nach Tagen:

```
So. 18.10.2026
05:07:12  [Klopfen, oben, stark] Bass dröhnt seit 22 Uhr – Zeuge: Anna
05:15:08  [Schritte, oben]

Mo. 19.10.2026
23:41:10 – 23:45:00  [Tür, Treppenhaus] Tür knallt mehrmals (geändert)
```

Gibt es den Tag schon, kommt die Notiz nach Uhrzeit darunter, sonst entsteht am Ende ein neuer Absatz mit dem Datum. Geänderte Notizen werden ersetzt (mit „(geändert)“), gelöschte entfernt. Format Text oder CSV, auf Wunsch eine Datei pro Monat (`…_2026-10.txt`). Die Datei wird von GReport geführt – eigene Änderungen darin gehen beim nächsten Schreiben verloren. Der fälschungssichere Stand bleibt die Datenbank von GReport.

**Export:** Text, CSV oder JSON – herunterladen oder direkt in eine Datei schreiben.

**Import:** Pfad einer Datei auf dem Home-Assistant-Rechner eintragen oder eine Datei hochladen, dann **Vorschau** und **Übernehmen**. Gelesen werden das Text-Tagebuch, CSV und JSON (auch die Exporte von GReport). Doppelte Notizen (gleiche Kennung oder gleiche Zeit, gleicher Text, gleiche Wörter) werden übersprungen, unbekannte Wörter als eigene angelegt.

## Pro
Ein GReport-Schlüssel oder ein GLighter-Pro-Schlüssel (Menü ⋯ → Pro). Geprüft wird offline.
