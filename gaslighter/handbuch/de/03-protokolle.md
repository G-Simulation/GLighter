# Protokolle

Der Reiter **Protokolle** zeigt einen Zeitraum vollständig: Zusammenfassung, Wochenleiste, Verlauf aller Geräte, Auswertungen und die Liste aller Störungen.

![Reiter Protokolle mit Zusammenfassung und Wochenleiste](protokolle_{lang}.png)

## Zeitraum und Filter {#zeitraum}

- **Erfassungszeit** (eingestellte Überwachungszeit, z. B. 22–6 Uhr), **Heute**, **Gestern**, **7 Tage**, **30 Tage** oder **Von–bis**. ‹ › blättert um einen ganzen Zeitraum.
- **Quelle / Gerät**, **Art** (Mehrfachauswahl, z. B. Klopfen + Schritte) und **Liste** filtern alles darunter. Geräte, die es nicht mehr gibt, deren Daten aber vorhanden sind, stehen als „(ehemalig)“ in der Auswahl.
- **🖨 Protokoll** erstellt das Lärmprotokoll für Zeitraum, Gerät und Liste, **⬇ Bild (SVG)** ein Bild. Siehe [Drucken](#drucken).

## Bereiche anordnen (Dashboard) {#dashboard}

Live und Protokolle bestehen aus **Bereichen** (Übersicht, Unterbrechungen, Verlauf, Ereignisse nach Uhrzeit, je Tag, Ereignisse im Zeitraum, Notizen und Bewegung, Sensoren im Zeitraum). Jeder Bereich hat oben eine Leiste:

- **▾ / ▸** klappt ein und aus (auch Doppelklick auf die Leiste).
- **✕** (nur in **▦ Layout anpassen**) blendet aus. Wieder einfügen über **▦ Layout anpassen** → **＋ Bereich hinzufügen**.
- **⌖ nur sichtbarer Bereich** (Ereignisse, Sensoren): zeigt nur, was im Verlauf gerade zu sehen ist – zieh im Verlauf z. B. 20:00–22:00 auf, dann zeigen Tabelle bzw. Liste nur diese Zeit.

### ▦ Layout anpassen {#designer}

**▦ Layout anpassen** schaltet Live und Protokolle in den Bearbeiten-Modus – ähnlich wie das Bearbeiten eines Dashboards in Home Assistant:

- **Verschieben:** am Griff ⠿ ziehen oder mit **↑ / ↓** in der Leiste eines Bereichs eine Stelle nach oben oder unten.
- **Breite:** an der linken oder rechten Kante ziehen (z. B. zwei Bereiche nebeneinander). Die Höhe richtet sich nach dem Inhalt.
- **✎ Überschrift ändern:** eigener Name für den Bereich oder die Kachel. Leer lassen stellt den ursprünglichen wieder her.
- **▾ / ▸** klappt ein und aus, **✕** nimmt den Bereich aus der Ansicht.
- **＋ Bereich hinzufügen** öffnet die Bibliothek: alle Bereiche dieser Ansicht (angezeigt oder ausgeblendet) zum Einfügen und Entfernen, darunter **neue Kacheln** und **fertige Vorlagen** (siehe unten). Dort lassen sich auch die gemerkten **Spaltenbreiten der Tabellen** zurücksetzen.
- **↺ Zurücksetzen** stellt nach einer Rückfrage die Standardanordnung dieser Ansicht wieder her. **Fertig** beendet das Bearbeiten.

**Mit der Tastatur:** im Bearbeiten mit Tab einen Bereich wählen (er bekommt einen deutlichen Rahmen), dann

| Taste | Wirkung |
|---|---|
| ↑ / ↓ | eine Stelle nach oben / unten |
| ← / → | eine Spalte nach links / rechts |
| Umschalt + ← / → | schmaler / breiter |
| Umschalt + ↑ / ↓ | einklappen / aufklappen |
| F2 | Überschrift ändern |
| Entf | entfernen (mit Rückfrage) |

Screenreader lesen den Namen jedes Bereichs und nach jeder Änderung die neue Stelle vor.

**Am Handy** stehen alle Bereiche untereinander. Die Reihenfolge änderst du im Bearbeiten mit **↑ / ↓** – die Anordnung am PC bleibt dabei erhalten.

**Gespeichert auf dem Server:** Anordnung, Breiten, Einklappen, Ausblenden, eigene Überschriften und die von Hand gezogenen **Spaltenbreiten der Tabellen** liegen in `layout.json` neben `sources.json`. PC, Tablet und Handy zeigen deshalb dasselbe. Gab es auf dem Server noch keine Anordnung, übernimmt GLighter beim ersten Öffnen die bisher im Browser gespeicherte. `layout.json` ist in der Sicherung (ZIP) enthalten und kommt mit „Einstellungen und Geräte übernehmen“ zurück. Das Layout ändert nie Daten.

„Sensoren im Zeitraum“ ist anfangs ausgeblendet: Sensor-Ereignisse („als Ereignis“) stehen schon in der Tabelle, „nur festhalten“ (z. B. Fernseher) steht als 📡-Hinweis bei jeder Störung, die in die Zeit fällt.

### 📊 Kacheln (eigene Statistiken) {#statistik}

In **▦ Layout anpassen** legt **＋ Bereich hinzufügen** → **Neue Kachel** (oder **＋ Bereich hier** an einer freien Stelle im Raster, dann genau dort)  eine Kachel als eigenen Bereich an – verschieben, breiter ziehen, umbenennen, einklappen und ausblenden wie die anderen.

**Arten von Kacheln:**

- **Zahl** – große Zahl mit Beschriftung, z. B. Störungen heute, Störungen der letzten 7 Tage, Ø Spitze.
- **Trend** – Linie über Tage, Wochen oder Monate.
- **Balken** – z. B. pro Stunde, Wochentag oder Tag.
- **Liste** – die häufigsten Arten, Geräte, Sensoren oder Notiz-Tasten (3 bis 20 Einträge).
- **Tabelle** – alle Werte zum Sortieren und Filtern (wie die anderen Tabellen).

**Einstellen:**

- **Vorlagen (für alle frei):** z. B. „Störungen heute“, „Störungen der letzten 7 Tage“, „Ø Spitze (7 Tage)“, „Dauer der Störungen heute“, „Häufigste Arten (7 Tage)“, „Störungen je Gerät (30 Tage)“, „Trend pro Tag (30 Tage)“, „Störungen pro Stunde (nachts)“, „Arten im Vergleich“, „Trend pro Woche“, „Pro Wochentag“, „Gesamtdauer pro Tag“, „Sensoren pro Tag“, „Notizen nach Taste“. Eine Vorlage kommt in die Ansicht, in der du sie anklickst.
- **Selbst einstellen (Pro):** *Name*, *Was zählen* (Störungen – auch nur eine Art oder ein Tonprofil –, Sensoren, Notizen mit einer Schnellwahl-Taste), *Kennzahl* (Anzahl, Gesamtdauer, Ø oder höchste Spitze), *aufgeteilt nach* (Stunde, Wochentag, Tag, Woche, Monat, Art, Gerät, Notiz-Taste, Sensor), *Darstellung* (Zahl, Linie, Balken, Liste, Tabelle), *Zeitraum* (gewählter Zeitraum, heute, letzte 24 h / 7 / 30 / 90 / 365 Tage oder **eigener Zeitraum** von–bis), *Gerät*, **Schwellen** (*nur ab Spitze* in dBFS, *nur ab Dauer* in Sekunden) und *nur nachts / nur Ruhezeit / nur Wochenende*. Die Vorschau zeigt sofort das Ergebnis.
- **Klick auf einen Balken**, einen Listeneintrag oder eine Tabellenzeile (auch mit Eingabe oder Leertaste) filtert die Ereignis-Tabelle darauf, nochmal klicken oder **✕** hebt den Filter auf.
- **⚙** stellt ein oder löscht. Kacheln lesen nur – sie ändern nie Daten. Gespeichert in `clips/statistik.json`, mit in der Sicherung.
- Jede Kachel erscheint auch **in Home Assistant** als Sensor (siehe [Home Assistant → Kacheln](#home-assistant/kacheln)).

## Zusammenfassung und Wochenleiste {#wochenleiste}

Der Ring zeigt, wie viel der Zeit **störungsfrei** war. Daneben: Anzahl der Störungen, gestörte Zeit, längste Ruhe, aufgezeichnete Zeit und lautestes Ereignis.

Die **Kreise** darunter sind die letzten 7 Nächte bzw. Tage. Antippen wählt den Tag; die neueste Nacht bleibt immer sichtbar. Darunter stehen die **Datenkette** (Prüfsummen) und Unterbrechungen, siehe [Unterbrechungen](#unterbrechungen).

## Verlauf {#verlauf}

![Verlauf mit Pegel und Spektrogramm](verlauf_{lang}.png)

Im Verlauf stehen die Geräte untereinander, für denselben Zeitraum. Je Zeile wählst du **Gerät** und **Darstellung** (Pegelspur, Lautstärke-Balken, Spektrogramm) und blendest Ebenen ein. „＋ Zeile hinzufügen“ und – in **▦ Layout anpassen** – ↑ ↓ ✕ ordnen die Zeilen; der Griff unter jeder Zeile ändert die Höhe.

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

### Geräuschart bestätigen oder korrigieren {#art-bestaetigen}

Die erkannte Art steht als farbiges Kästchen in der Spalte **Art**. Solange du sie nicht bestätigt hast, ist sie ein **„Vorschlag der Erkennung (Konfidenz x %)“** – so steht es auch in Lärmprotokoll, Ausdruck und Rohdaten. **Klick auf das Kästchen** (oder ⋮ → Geräuschart bestätigen): **Stimmt** bestätigt den Vorschlag, eine andere Art korrigiert ihn, **Bestätigung zurücknehmen** macht es rückgängig. Deine Bestätigung liegt in einer eigenen Datei (`bestaetigt.json`); die Einschätzung der Erkennung, `log.csv` und die Tagesaufzeichnung bleiben unverändert. Die Erkennung sagt nichts darüber, aus welcher Wohnung ein Geräusch kommt.

### Bekannte Geräusche ausfiltern {#muster}

⋮ → **Als Muster ausfiltern …** legt aus der Störung ein [Muster](#einstellungen/muster) an (Gerät, Art, Uhrzeit, Dauer und Spitze vorbelegt, mit Vorschau „trifft auf N Störungen der letzten 30 Tage zu“). Ausgefilterte fehlen danach in der Liste; die Anzahl nennt sie („N nach Muster ausgefiltert“), **⊘ ausgefilterte zeigen** holt sie gekennzeichnet zurück.

### Notizen in der Tabelle {#notizzeilen}

Jede angelegte Notiz steht als eigene Zeile **„📝 Notiz“** in der Tabelle, mit Zeit (von–bis), Gerät, Markierungen, Zeuge und Text. Liegt im Zeitraum der Notiz eine Störung, ist sie verknüpft: In der Notiz-Zeile steht **„🔗 Störung …“** (Klick öffnet die Störung), in der Störungs-Zeile der Notiztext. Mit **✎** bearbeitest du die Notiz. Im Filter **„📝 Notizen“** blendest du alle Notiz-Zeilen aus oder ein. Notizen zählen nicht als Störung.

## Protokolllisten {#listen}

Eigene Listen wie „Bad“ oder „Garten“ sammeln Störungen zusätzlich zur Gesamtliste – von Hand („In Liste übernehmen“, im Ereignis unter „Listen“) oder automatisch je Gerät und Uhrzeit (⚙ Einstellungen → Geräte → Karte des Geräts → **Protokolllisten**). Jede Liste hat eine eigene Notiz und ein eigenes Lärmprotokoll.
