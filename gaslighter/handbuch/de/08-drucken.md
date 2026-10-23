# Drucken und Lärmprotokoll

Es gibt zwei Ausdrucke: das **Lärmprotokoll** (Bericht mit Zusammenfassung und Liste) und den **Verlauf als Notenblatt** (die Kurven Zeile für Zeile).

## Lärmprotokoll {#laermprotokoll}

Reiter Protokolle → **🖨 Protokoll** (für Zeitraum, Gerät und Liste) oder **📝 Alle Notizen** → Protokoll. Es enthält:

- Zeitraum, Geräte, Zusammenfassung (Anzahl, gestörte Zeit, längste Ruhe), erkannte Geräuscharten, benannte Bereiche,
- den **Tagesverlauf**: je Tag und Gerät eine Grafik über 24 h (Spitze, Hintergrund, Schwelle, Störungen rot, Home Assistant blau, nicht aufgezeichnet schraffiert, Notizen), gleiche Skala je Gerät,
- jede Störung mit Datum, Uhrzeit, Dauer, Pegel, Art, Notizen, Zeugen und Zuständen aus Home Assistant,
- Ruhezeiten (🌙), Gegenmaßnahmen, Einpegeln der Geräte,
- **Unterbrechungen und Updates** mit Ursache und deinem Kommentar,
- die **Datenkette** je Gerät und Tag mit Prüfsumme.
- die **Messmethode**: Programm und Version, je Gerät Art, Mikrofon/Modell, Messort und Fenster, „Mikrofon nicht kalibriert: Werte sind Indizien und ersetzen kein Gutachten“, ob Ton gespeichert wird („Es wird kein Ton gespeichert“, wenn „Echten Ton speichern“ aus ist) und dass die Geräuschart ein Vorschlag der Erkennung ist, solange du sie nicht bestätigt hast,
- eine **Zusammenfassung** nach Zeitpunkt (Uhrzeiten, Wochentage, Ruhezeit), Art, Intensität (Spitze), Dauer und Häufigkeit (an wie vielen Tagen, im Schnitt je Tag),
- je Störung **Spitze, Dauer und Anzahl der Impulse** (wie oft der Pegel über die Schwelle stieg, aus der Tagesaufzeichnung),
- eine **lückenlose Zeitachse**: jeder Tag des Zeitraums, auch Tage ohne Störung, mit „aufgezeichnet“ oder „keine Aufzeichnung“,
- zur Datenkette eine kurze **Erklärung des Prüfverfahrens**.

Oben auf der Seite gibt es außerdem **⬇ Rohdaten (CSV)** (alle Messwerte der Störungen, für Sachverständige) und **⬇ Beweispaket (ZIP)**: Lärmprotokoll (HTML), Rohdaten, Notizen, Zeitachse und Prüfsummen als CSV und eine Zusammenfassung mit Messmethode als Text. Beides gibt es auch unter 📝 Alle Notizen → Protokoll.

**Musterfilter:** Standardmäßig sind alle Störungen enthalten; nach [Muster](#einstellungen/muster) ausgefilterte stehen mit dem Vermerk „nach Muster … ausgefiltert“ darin. Mit **nach Muster ausgefilterte weglassen** fehlen sie, und oben steht, welche Muster wie viele entfernt haben.

Oben auf der Seite (wird nicht mitgedruckt) wählst du **Tagesgrafik** (Standard an) und **Grafik je Störung** (Standard aus): eine kleine Grafik mit Umfeld unter jeder Störung, die eine Notiz hat oder aus der gewählten Liste stammt (höchstens 300).

Im Browser drucken oder als PDF speichern. Das ausgedruckte Dokument heißt immer „Lärmprotokoll“.

> Pegel sind relative dBFS-Werte, keine geeichte Messung in dB(A). Tonaufnahmen kommen nie ins Protokoll. Keine Rechtsberatung.

## Verlauf drucken (Notenblatt) {#notenblatt}

![Druckdialog](druckdialog_{lang}.png)

Im Verlauf **🖨 Drucken**:

- **Zeitraum**: von–bis oder Schnellwahl „Sichtbarer Ausschnitt“, „Zeitraum des Berichts“, „Alle Daten“.
- **Zeit je Zeile**: 1 min bis 1 h (Standard 10 min – ein ganzer Tag sind 144 Zeilen).
- **Geräte** untereinander, **Inhalt** (Pegelspur, Spektrogramm, Störungs-Infos und Notizen), **Zeilen ohne Aufzeichnung zusammenfassen** (Standard an).
- **Skala**: gleich für alle Zeilen (vergleichbar) oder je Zeile angepasst (mehr Einzelheiten); **A4 quer** oder **hoch**.
- **Belege (Zusammenfassung, Zeitachse, Prüfsummen)** (Standard an): oben eine Zusammenfassung nach Zeitpunkt, Art, Intensität, Dauer und Häufigkeit, unten Messmethode, Zeitachse mit allen Tagen, Prüfsummen mit Erklärung und der Link zu den Rohdaten (CSV). Bei jeder Störung stehen Impulse und, falls nicht bestätigt, „Vorschlag der Erkennung (Konfidenz x %)“.
- **nach Muster ausgefilterte weglassen**: wie beim Lärmprotokoll.

Der Dialog schätzt Zeilen und Seiten. **Vorschau öffnen** baut die Seiten in einem neuen Fenster auf; dort **Drucken** oder als PDF speichern. Eine aktive [Prüf-Schwelle](#protokolle/pruefschwelle) wird mitgedruckt, mit Zählung je Zeile.

![Druckvorschau](druckseite_{lang}.png)
