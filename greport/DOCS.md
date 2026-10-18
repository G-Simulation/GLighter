# GReport

## Notiz jetzt
Oben steht groß die Uhrzeit – sie wird mit der Notiz festgehalten. Text eintippen (Enter speichert, Alt+Enter neue Zeile) oder Tasten der Schnellwahl antippen. Ohne Text bildet GReport aus den Tasten einen Satz, z. B. „Deutliche Schritte von oben“. Der Zeitpunkt ist der Moment des ersten Tastendrucks; unter „🕒 jetzt · Zeit ändern“ lassen sich von und bis von Hand setzen, „läuft noch“ setzt bis = beim Speichern. Mit ⧉ wird der Notizbereich als kleines Fenster abgedockt.

## Schnellwahl verwalten
⋯ → **Schnellwahl verwalten** (oder **＋ Eigene**, Rechtsklick bzw. lange auf ein Wort drücken):
- **Umbenennen:** jedes Wort, auch die eingebauten. Alte Notizen behalten ihre Zuordnung, nur die Beschriftung ändert sich.
- **Gruppe:** Woher, Was, Wie stark, Folgen, Maßnahmen, Sonstiges oder Eigene – davon hängt die Farbe ab.
- **Reihenfolge:** „Nach Gebrauch“ (häufige Wörter nach vorne) oder „Fest angeordnet“ (ziehen oder ▲▼).
- **Zeigen:** Häkchen weg blendet ein Wort aus (auch in Home Assistant).
- **Auf Standard zurücksetzen:** eingebaute Wörter, Gruppen und Reihenfolge; eigene Wörter bleiben.

Diese Wörter stehen auch in Home Assistant in der Auswahlliste „Schnellwahl“. Ohne Pro sind 5 eigene Wörter möglich, mit Pro 40.

## Datum und Uhrzeit
⋯ → **Datum und Uhrzeit**: Datum (18.10.2026, 18.10.26, So. 18.10., 2026-10-18, 18. Okt. 2026), Uhrzeit (mit/ohne Sekunden, 12 Stunden), Wochentag davor, „Heute/Gestern“ in der Liste. Gilt in der App und in der Export-Tabelle.

## Home Assistant
- **Logbuch:** jede neue Notiz erscheint als Eintrag „GReport“ (abschaltbar in der Konfiguration).
- **Auswahlliste „Schnellwahl“ und Knopf „Hinzufügen“** (Gerät „GReport“, braucht den MQTT-Broker Mosquitto): Wort wählen, Knopf drücken – die Notiz ist mit der Uhrzeit angelegt. Der Knopf lässt sich auch in Automationen verwenden (z. B. Zigbee-Taster).

## Mit GLighter
Ist GLighter installiert, findet es GReport selbst (über `/share/greport`). Mit GLighter Pro erscheinen die Notizen dort an den Störungen, im Verlauf und im Lärmprotokoll; geändert werden sie in GReport.

## Sicherung, Export, Import
Menü ⋯: **Sicherung (ZIP)** ist immer frei. Pro: Export als Tabelle (CSV) oder für den Import (JSON), Import, Personen/Zeugen zum Antippen und eine tägliche Sicherung nach `/share/greport/sicherung` (14 Tage).

## Pro
Ein GReport-Schlüssel oder ein GLighter-Pro-Schlüssel (Menü ⋯ → Pro). Geprüft wird offline.
