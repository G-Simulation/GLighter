# Changelog

## 1.4.0
- **Pflicht-Gruppen:** In „Schnellwahl verwalten“ lässt sich jede Gruppe als „Pflicht“ markieren, sie bekommt ein Sternchen. Sind in allen Pflicht-Gruppen Tasten gewählt, leuchten diese und „Speichern“ pulsierend auf („Alles Wichtige gewählt“). Das ist nur ein Hinweis, gespeichert wird immer. Wer weniger Bewegung eingestellt hat, sieht einen ruhigen Rand statt des Pulsierens.
- **Kleine Hilfe:** „?“ oben oder ⋯ → Hilfe. Kurz erklärt sind Notiz jetzt, Schnellwahl, Pflicht-Gruppen, Zeit, Liste, Home Assistant, GLighter, Textdatei und Pro.

## 1.3.0
- **Farbe pro Gruppe:** In „Schnellwahl verwalten“ hat jede Gruppe (Woher, Was, Wie stark …) neben der Überschrift ein Farbfeld. Die Farbe gilt für alle Wörter der Gruppe: in „Notiz jetzt“, in der Liste und bei den Filtern. Mit ↺ kommt die Standardfarbe zurück. Im dunklen Modus wird die Farbe etwas aufgehellt.

## 1.2.1
- Schnellwahl: Am PC und im abgedockten Fenster brechen die Tasten wieder in die nächste Zeile um, statt rechts abgeschnitten zu werden. Nur auf Handys mit Touch bleibt je Gruppe eine Zeile zum Wischen, mit einem Pfeil rechts, solange es weitergeht.

## 1.2.0
- **Neu (Pro): Tagebuch als Textdatei.** GReport führt eine gut lesbare Datei nach Tagen: je Tag eine Überschrift, darunter die Notizen nach Uhrzeit. Neue, geänderte und gelöschte Notizen werden sofort eingetragen, nachgetragene Notizen landen unter ihrem Tag.
  - Datei frei wählbar unter `/share` oder `/media`, z. B. auf einem Netzlaufwerk.
  - Format Text oder CSV, auf Wunsch eine Datei pro Monat.
  - Datum und Uhrzeit wie eingestellt.
- **Export in eine Datei** (Text, CSV oder JSON) direkt auf den Home-Assistant-Rechner, oder herunterladen.
- **Import aus Textdateien:** Text-Tagebuch, CSV und JSON, auch die eigenen Exporte. Vorher zeigt eine Vorschau, wie viele Notizen neu sind und wie viele schon vorhanden. Doppelte werden übersprungen, unbekannte Wörter als eigene angelegt.
- Alles unter ⋯ → **Textdatei & Import/Export**. Die ZIP-Sicherung bleibt frei.

## 1.1.0
- **Neues Erscheinungsbild.** Große Uhrzeit als Anker (sie wird mit der Notiz festgehalten). Die Schnellwahl ist nach Gruppen geordnet (Woher, Was, Wie stark, Folgen, Maßnahmen, Sonstiges, Eigene), jede mit eigener Farbe. Die Zeit ist eingeklappt („jetzt · Zeit ändern“), „Speichern“ steht in einer festen Leiste, am Handy unten am Bildschirm.
- Die Liste ist eine Zeitleiste nach Tagen („Heute“, „Gestern“, Datum), mit Filter nach Wörtern. Hell und dunkel, auch am Handy ohne Überbreite.
- **Schnellwahl verwalten** (⋯ → Schnellwahl verwalten, ＋ Eigene oder lange auf ein Wort drücken):
  - alle Wörter umbenennen, auch die eingebauten,
  - jedem Wort eine Gruppe geben,
  - die Reihenfolge selbst festlegen (ziehen oder ▲▼) oder nach Gebrauch,
  - Wörter zeigen oder ausblenden,
  - alles auf Standard zurücksetzen.
  - Die Auswahlliste „Schnellwahl“ in Home Assistant übernimmt Namen und Reihenfolge.
- **Datum und Uhrzeit einstellbar** (⋯ → Datum und Uhrzeit): 18.10.2026 · 18.10.26 · So. 18.10. · 2026-10-18 · 18. Okt. 2026, mit oder ohne Sekunden, 12 Stunden, Wochentag, „Heute/Gestern“. Gilt auch in der Export-Tabelle (CSV, zusätzlich mit genauer Zeit).
- „Quelle / Gerät“ entfällt. „läuft noch (bis = beim Speichern)“ bleibt.

## 1.0.1
- Behoben: Beim Öffnen in Home Assistant kam nur „forbidden“. Der Zugriff über Home Assistant wird jetzt auch über IPv6 erkannt.

## 1.0.0
- Erste Fassung: der Notiz-Teil von GLighter als eigene App.
- Notiz jetzt: Textfeld (Enter speichert), Schnellwahl mit eigenen Tasten (lernt mit, häufigste zuerst), Zeuge, Zeitraum von–bis, „läuft noch“, Notizbereich abdocken (⧉).
- Liste aller Notizen mit Suche, Ändern und Löschen.
- Home Assistant: jede neue Notiz im **Logbuch**, dazu (über MQTT) die Auswahlliste **„Schnellwahl“** und der Knopf **„Hinzufügen“**. In der Liste stehen dieselben Wörter wie in der App.
- Mit **GLighter (Pro)** automatisch verbunden: die Notizen erscheinen dort an den Störungen, im Verlauf und im Lärmprotokoll; „Quelle / Gerät“ zeigt dann die Geräte von GLighter.
- Pro (GReport- oder GLighter-Schlüssel): Export (CSV/JSON) und Import, bis zu 40 eigene Tasten (frei: 5), tägliche Sicherung (14 Tage), mehrere Zeugen. Die Sicherung als ZIP ist immer frei.
