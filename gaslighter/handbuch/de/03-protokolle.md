# Protokolle

Der Reiter **Protokolle** zeigt einen Zeitraum vollständig: Zusammenfassung, Wochenleiste, Verlauf aller Geräte, Auswertungen und die Liste aller Störungen.

![Reiter Protokolle mit Zusammenfassung und Wochenleiste](protokolle_{lang}.png)

## Zeitraum und Filter {#zeitraum}

- **Erfassungszeit** (eingestellte Überwachungszeit, z. B. 22–6 Uhr), **Heute**, **Gestern**, **7 Tage**, **30 Tage** oder **Von–bis**. ‹ › blättert um einen ganzen Zeitraum.
- **Quelle / Gerät**, **Art** (z. B. nur Klopfen) und **Liste** filtern alles darunter. Geräte, die es nicht mehr gibt, deren Daten aber vorhanden sind, stehen als „(ehemalig)“ in der Auswahl.
- **🖨 Protokoll** erstellt das Lärmprotokoll für Zeitraum, Gerät und Liste, **⬇ Bild (SVG)** ein Bild. Siehe [Drucken](#drucken).

## Zusammenfassung und Wochenleiste {#wochenleiste}

Der Ring zeigt, wie viel der Zeit **störungsfrei** war. Daneben: Anzahl der Störungen, gestörte Zeit, längste Ruhe, aufgezeichnete Zeit und lautestes Ereignis.

Die **Kreise** darunter sind die letzten 7 Nächte bzw. Tage. Antippen wählt den Tag; die neueste Nacht bleibt immer sichtbar. Darunter stehen die **Datenkette** (Prüfsummen) und Unterbrechungen, siehe [Unterbrechungen](#unterbrechungen).

## Verlauf {#verlauf}

![Verlauf mit Pegel und Spektrogramm](verlauf_{lang}.png)

Im Verlauf stehen die Geräte untereinander, für denselben Zeitraum. Je Zeile wählst du **Gerät** und **Darstellung** (Pegelspur, Lautstärke-Balken, Spektrogramm) und blendest Ebenen ein. „＋ Zeile hinzufügen“, ↑ ↓ ✕ ordnen die Zeilen; der Griff unter jeder Zeile ändert die Höhe.

- Läuft der Tag noch, endet die Zeitachse bei **jetzt** – das Neueste steht rechts und der Verlauf wächst jede Minute mit.
- Bei mehr als 2 Tagen zeigt er Minutenwerte, beim Hineinzoomen wieder die 125-ms-Werte.
- Oben markiert die KI je Störung die erkannte Art in ihrer Farbe; **blau** = laut Home Assistant an (z. B. Fernseher).
- **Schraffiert** = nicht aufgezeichnet (z. B. Stromausfall). Anklicken, um einen Kommentar zu setzen, siehe [Unterbrechungen](#unterbrechungen/kommentar).

Bedienung wie im Live-Bild: Mausrad/zwei Finger zoomen, Bereich aufziehen, hineingezoomt ziehen oder ‹ › zum Verschieben, Umschalt + Mausrad für die Höhe, Doppelklick oder „Ganzer Zeitraum“ für alles. Am Handy liegen Prüf-Schwelle, Drucken und Bereich markieren unter **⋯ Werkzeuge**, die Ebenen hinter **🗂 Ebenen**.

## 📏 Prüf-Schwelle {#pruefschwelle}

![Prüf-Schwelle mit Liste der Spitzen](pruefschwelle_{lang}.png)

Mit der Prüf-Schwelle schaust du nachträglich, welche Spitzen über einem frei gewählten Wert lagen – z. B. „Wie oft war es über −50 dB?“

1. „📏 Prüf-Schwelle“ antippen, Wert eingeben oder die violette Linie im Verlauf ziehen.
2. Je Gerät stehen Anzahl und Dauer der Spitzen im sichtbaren Ausschnitt (aus den 125-ms-Werten; weniger als 0,5 s Abstand = eine Spitze).
3. „Liste der Spitzen“ zeigt jede Spitze mit Uhrzeit, Dauer, Höhe, Abstand, **Art (KI)** und **Tonprofil**. Ein Klick springt im Verlauf dorthin.

Die Art kommt aus der Störung, wenn die Spitze in einer liegt, sonst aus dem gespeicherten **KI-Fingerabdruck** (ⓕ). Mögliche Hinweise: „kein Fingerabdruck an dieser Stelle“, „an diesem Tag kein KI-Fingerabdruck“, „nicht geprüft“ (mehr als 2000 Spitzen). Siehe [KI](#ki/fingerabdruck).

> Die Prüf-Schwelle ist **nur eine Anzeige**. Gespeicherte Daten, Störungen und Prüfsummen bleiben unverändert. Beim Drucken wird sie mitgedruckt.

## Ereignisse im Zeitraum {#ereignisliste}

![Liste der Ereignisse](ereignisliste_{lang}.png)

- **Gruppen** fasst gleichartige Störungen zusammen (Abstand höchstens „Gruppe: höchste Pause“), **Alle einzeln** zeigt jede.
- **Sortieren:** Klick auf eine Spaltenüberschrift (Start, Dauer, Spitze, Schwelle, Hintergrund); noch ein Klick dreht die Reihenfolge um. Die Sortierung bleibt im Browser gespeichert.
- **Filtern mit Mehrfachauswahl:** Unter **Quelle / Gerät** und **Art** ein oder mehrere Einträge anklicken, z. B. nur „Türsensor Erschütterung“ und „Stimme“. Die Zeile über der Tabelle zählt Störungen und Sensor-Ereignisse getrennt.
- **Sensor-Ereignisse** (Home-Assistant-Regel „als Ereignis“, Handy als Bewegungsmelder) stehen zeitlich einsortiert mit orangem Rand; ✎ = Notiz.
- Auf schmalen Bildschirmen klappt ⊕ am Zeilenanfang die übrigen Spalten auf.
- Klick = im Verlauf hinspringen, Doppelklick oder ▶ = [Ereignis öffnen](#ereignis), ⋮ = weitere Aktionen (Lärmspur herunterladen, KI neu bewerten, löschen).
- Markieren, dann **In Liste übernehmen** oder löschen. Gelöschte Einträge landen zur Sicherheit im Papierkorb; die Tagesaufzeichnung bleibt.
- **📝 Alle Notizen**, **🔎 Geräusch prüfen** (eigene Audiodatei auswerten, wird nicht gespeichert), **🧩 Profile & neu untersuchen**, **log.csv herunterladen**.

## Protokolllisten {#listen}

Eigene Listen wie „Bad“ oder „Garten“ sammeln Störungen zusätzlich zur Gesamtliste – von Hand („In Liste übernehmen“, im Ereignis unter „Listen“) oder automatisch je Gerät und Uhrzeit (⚙ Einstellungen → Geräte → Karte des Geräts → **Protokolllisten**). Jede Liste hat eine eigene Notiz und ein eigenes Lärmprotokoll.
