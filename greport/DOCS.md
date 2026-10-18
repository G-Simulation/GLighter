# GReport

## Notiz jetzt
Oben im Fenster: Text eintippen (Enter speichert, Alt+Enter neue Zeile) oder Tasten der Schnellwahl antippen. Ohne Text bildet GReport aus den Tasten einen Satz, z. B. „Deutliche Schritte von oben“. Der Zeitpunkt ist der Moment des ersten Tastendrucks; unter „Zeitraum“ lassen sich von und bis von Hand setzen, „läuft noch“ setzt bis = beim Speichern. Mit ⧉ wird der Notizbereich als kleines Fenster abgedockt.

## Schnellwahl anpassen
**＋ Eigene** (oder Rechtsklick / lange drücken auf eine Taste): eigene Tasten anlegen, umbenennen, löschen und eingebaute ausblenden. Diese Wörter stehen auch in Home Assistant in der Auswahlliste „Schnellwahl“. Ohne Pro sind 5 eigene Tasten möglich, mit Pro 40.

## Home Assistant
- **Logbuch:** jede neue Notiz erscheint als Eintrag „GReport“ (abschaltbar in der Konfiguration).
- **Auswahlliste „Schnellwahl“ und Knopf „Hinzufügen“** (Gerät „GReport“, braucht den MQTT-Broker Mosquitto): Wort wählen, Knopf drücken – die Notiz ist mit der Uhrzeit angelegt. Der Knopf lässt sich auch in Automationen verwenden (z. B. Zigbee-Taster).

## Mit GLighter
Ist GLighter installiert, findet es GReport selbst (über `/share/greport`). Mit GLighter Pro erscheinen die Notizen dort an den Störungen, im Verlauf und im Lärmprotokoll; geändert werden sie in GReport. „Quelle / Gerät“ zeigt dann die Geräte von GLighter.

## Sicherung, Export, Import
Menü ⋯: **Sicherung (ZIP)** ist immer frei. Pro: Export als Tabelle (CSV) oder für den Import (JSON), Import, Personen/Zeugen zum Antippen und eine tägliche Sicherung nach `/share/greport/sicherung` (14 Tage).

## Pro
Ein GReport-Schlüssel oder ein GLighter-Pro-Schlüssel (Menü ⋯ → Pro). Geprüft wird offline.
