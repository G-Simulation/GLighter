# GLighter (Lärmprotokoll / Noise Log)

Das vollständige Handbuch mit Bildern, Suche und Querverweisen steht in der App unter **📖 Handbuch**. The full manual with pictures, search and links is in the app under **📖 Manual**.

**Inhalt / Contents:** 1. Schnellstart in 5 Minuten · 2. Live-Ansicht · 3. Protokolle · 4. Ereignis-Fenster · 5. KI: Geräuscharten und Tonprofile · 6. Geräte · 7. Home Assistant · 8. Drucken und Lärmprotokoll · 9. Sicherung, Import und Export · 10. Unterbrechungen, Datenkette und Updates · 11. Einstellungen von A bis Z · 12. Rechtliches und Datenschutz · 13. Fehlerbehebung und häufige Fragen · 14. GLighter Pro · 15. Glossar


---

# Deutsch

## 1. Schnellstart in 5 Minuten

GLighter hört dauerhaft mit und schreibt ein **Lärmprotokoll**: Wann war es wie laut, wie lange, welche Art von Geräusch – mit Prüfsummen, damit niemand die Daten unbemerkt ändern kann. **Ton wird dabei nicht gespeichert**, nur Messwerte.

### 1. Mikrofon anschließen

- Ein USB-Mikrofon oder ein Mikrofon an der Soundkarte des Home-Assistant-Rechners anschließen. Der Eintrag „Server-Mikrofon“ ist schon da.
- Weitere Räume: Handys als Mikrofon hinzufügen, siehe Geräte.
- Zeigt die Kachel **Pegel** einen Wert und bewegt sich die Kurve bei einem Klopfer, kommt Ton an. Erscheint der blaue Hinweis „Das Signal ist sehr leise“, die Mikrofon-Lautstärke erhöhen (⚙ Einstellungen → Geräte → Mikrofon) oder die richtige Buchse wählen.

### 2. Schwelle prüfen

Eine **Störung** wird gezählt, wenn der Pegel über der **Schwelle** liegt (orange gestrichelte Linie). Standard: „Passt sich an, mit Grenzen“ – die Schwelle liegt 10 dB über dem normalen Hintergrund, aber nie unter −95 und nie über −30 dBFS.

- Ein lautes Klopfen sollte deutlich über die Linie gehen und rot markiert werden.
- Werden zu viele Kleinigkeiten gezählt: „Wie viel lauter als normal?“ erhöhen (z. B. 12 dB). Wird zu wenig gezählt: verringern.
- Einzelheiten: Einstellungen → Erkennung.

> **Tipp:** Pegel sind **dBFS** – relativ zur Soundkarte, deshalb negativ (−80 sehr leise, −20 sehr laut). Wichtig ist der Abstand zum Hintergrund, nicht der absolute Wert. Siehe Glossar.

### 3. Mehrere Mikrofone einpegeln (optional)

Wenn du mehrere Geräte vergleichen willst: ⚙ Einstellungen → Geräte → **Geräte einpegeln**. Alle Mikrofone nebeneinander legen, 5 s Ruhe, dann ein gleichmäßiges Geräusch. Danach zeigen alle Geräte beim selben Geräusch denselben Wert.

### 4. Erste Störung ansehen

- Im Reiter **Live** steht unten „Ereignisse heute“. Ein Klick öffnet die Störung mit Grafik, Spektrogramm und erkannter Art.
- Im Reiter **Protokolle** siehst du ganze Tage und Wochen, den Verlauf mit allen Geräten untereinander und die Liste aller Störungen.
- Was du gerade hörst, trägst du oben unter **📝 Notiz jetzt** ein („Schritte oben“, „Bass“) – die Notiz kommt automatisch zur letzten Störung.

### 5. Sichern und Updates

- Regelmäßig unter ⚙ Einstellungen → Speichern & Sicherung → **Sicherung herunterladen** eine Sicherung ziehen. Siehe Sicherung.
- Updates ohne Aufnahmelücke: neuen Ordner nach `\\homeassistant\share\gaslighter_update\` kopieren. Siehe Updates.

> **Wichtig:** GLighter ist eine Gedächtnisstütze und Dokumentation, keine geeichte Lärmmessung in dB(A). Für Vermieter, Hausverwaltung oder Behörden zählt vor allem: regelmäßig, nachvollziehbar, mit eigenen Notizen. Siehe Lärmprotokoll.

## 2. Live-Ansicht

Der Reiter **Live** zeigt, was gerade passiert: Kacheln mit den aktuellen Werten, die Grafik der letzten Minuten, das Spektrogramm und die Ereignisse von heute.

### Kopfzeile

| Element | Bedeutung |
|---|---|
| **LIVE** | Die Anzeige folgt der Gegenwart. Nach dem Zurückspulen hier wieder zurück zu Live. |
| **Ruhig / STÖRUNG** | Zustand des gewählten Geräts. Rot = gerade über der Schwelle. Außerhalb der Überwachungszeit lässt sich hier „trotzdem erfassen“ einschalten. |
| **Aufzeichnung stoppen** | Hält die Aufzeichnung an (wird in `aufzeichnung.csv` festgehalten). Am Handy im Menü ⋯. |
| **🌓 Auto / ☀ / 🌙** | Hell, dunkel oder wie Home Assistant. |
| **⚙ Einstellungen** | Alle Einstellungen, siehe Einstellungen. |

### Geräteleiste und Kacheln

Die Leiste unter der Notiz zeigt alle Geräte mit Anzahl der Störungen heute. Antippen wählt das Gerät. Sind mehrere Geräte live, wechselt die Ansicht im **Rundlauf** automatisch (Dauer über ⚙ in der Leiste).

- **Pegel** – aktueller Spitzenpegel.
- **Hintergrund** – der gelernte „normale“ Pegel.
- **Schwelle** – ab hier zählt es als Störung; darunter steht, wie sie berechnet wird.
- **Geräusch jetzt** – was die KI gerade hört (nur mit eingeschalteter Geräuscherkennung).
- **Ereignisse** – Störungen heute und insgesamt.

### Die Grafik

- **Blaue Fläche** = Pegel, **graue Linie** = Hintergrund, **orange gestrichelt** = Schwelle, **rot** = Störung, gepunktete farbige Linien = eigene Referenzlinien (z. B. „Fernseher −70 dB“).
- **Pegelspur / Lautstärke-Balken** schaltet die Darstellung um.
- **🗂 Ebenen** blendet Kurven ein und aus: Hintergrund, Schwelle, tief/mittel/hoch, dominante Frequenz, Klangschwerpunkt.
- **Zeitfenster** und **− / +** ändern die gezeigte Zeit; **Auto** passt die Höhe an.
- Darunter das **Spektrogramm**: Frequenz über Zeit, hell = laut. Tiefe Geräusche (Bass, Trittschall) liegen unten, Stimmen und Geschirr weiter oben.

### Bedienung

| Am Computer | Am Handy / Tablet |
|---|---|
| Strg + Mausrad oder Touchpad spreizen = Zeit zoomen (Mausrad allein scrollt die Seite; einstellbar unter ⚙ → Allgemein → „Mausrad im Diagramm“) | zwei Finger spreizen = Zeit zoomen |
| Ziehen oder seitlich wischen = in der Zeit blättern | waagerecht wischen = blättern, senkrecht = Seite scrollen |
| Umschalt + Ziehen = Bereich aufziehen und hineinzoomen | − / + |
| Umschalt + Mausrad oder Strg + Mausrad über der dB-Beschriftung = Höhe zoomen (unten bündig) | „Auto“ |
| Doppelklick = zurück zu Live | Doppeltippen = zurück zu Live |
| Über eine Störung fahren = Einzelheiten | Störung antippen = Einzelheiten |

**Mit der Tastatur:** Mit Tab auf die Grafik gehen (blauer Rahmen). Dann **+ / −** Zeit zoomen, **← / →** in der Zeit blättern, **↑ / ↓** Höhe, **0** zurücksetzen, **Ende** zurück zu Live. Screenreader lesen den aktuellen Pegel, die Schwelle und den Zustand vor.

Weiter zurück als die letzten 10 Minuten zeigt die Grafik den **ganzen Tag** aus der Tagesaufzeichnung (Zeitfenster 1 h, 6 h oder „Heute“).

### 📝 Notiz jetzt

Für das, was du gerade hörst – einfach lostippen oder Merkmale antippen (oben, unten, Klopfen, Bass, aufgewacht …).

- **Ohne eigene Uhrzeit**: Liegt kurz vorher eine Störung (Einstellung „Notiz zuordnen“, Standard 5 min), gilt die Notiz für sie. Die Leiste zeigt vorher, wohin sie kommt.
- **läuft noch**: Die Notiz bekommt einen Zeitraum von der ersten Eingabe bis zum Speichern.
- **Von / bis und Zeuge** stehen immer direkt im Bereich; leer lassen heißt „automatisch“ (Uhrzeit beim Speichern).
- **Nur Markierungen, kein Text?** Dann bildet GLighter beim Speichern einen Satz daraus, z. B. „Deutliche Schritte im Treppenhaus“. Du kannst ihn später ändern.

### Eigene Schnellwahl

- **＋ Eigene** am Ende der Tasten: Namen eingeben (z. B. „Waschmaschine“, „Nachbar 2. OG“) → **Anlegen**. Die Taste (★) gibt es dann in allen Notiz-Feldern, auch abgedockt, und im Filter der Notizen.
- **Rechtsklick oder lange drücken** auf eine Taste öffnet „Schnellwahl verwalten“: eigene **umbenennen** oder **löschen**, eingebaute **aus- und wieder einblenden**. Alte Notizen behalten ihre Bezeichnung.
- **Lernen:** Tippst du ein Wort öfter selbst (ab 3×), schlägt GLighter es als Taste vor (💡). Angelegt wird sie nur, wenn du **＋** drückst; **✕** heißt „nicht mehr vorschlagen“.
- **Reihenfolge:** Was du am häufigsten drückst, steht vorne – am Handy sind das die ersten 6.
- Die eigenen Tasten liegen in `clips/schnellwahl.json` und sind in der Sicherung (ZIP) enthalten.

**Abdocken (Pro):** Mit **⧉** neben dem Titel löst du den Notizbereich als eigenes kleines Fenster heraus. In Chrome und Edge bleibt es über anderen Programmen liegen (z. B. über einem Spiel oder Film), sonst ist es ein normales Zusatzfenster. **Zurückholen** oder das Fenster schließen setzt ihn wieder ein.
- Strg + Enter speichert. Am Handy ist die Leiste zunächst zugeklappt.

### 🏷 Bereich markieren

1. „🏷 Bereich markieren“ antippen – über der Grafik erscheint ein Hinweis mit **Fertig**.
2. Den Bereich waagerecht aufziehen (0,15 s bis 2 min).
3. Eine **vorhandene Art** antippen (Tonprofil 🧩 oder benannter Bereich 🏷) oder einen neuen Namen eingeben – gleicher Name = gleiche Art, die KI lernt daraus. Siehe KI.

### Ereignisse heute

Die Liste unten zeigt alle Störungen des Tages (alle Geräte oder das gewählte). Ein Klick öffnet die Störung, siehe Ereignis-Fenster. Spalten wählst du über ⚙. Am Handy erscheinen die Einträge als Karten.

**Nur sichtbarer Bereich** (Standard: an): Die Tabelle zeigt nur, was im Graphen darüber gerade zu sehen ist. Sie läuft live mit und folgt dem Zoomen und Verschieben. Aus: alle Ereignisse ab dem Anfang des Graphen.

**Spaltenbreiten:** Ziehst du eine Spalte am Rand im Kopf breiter oder schmaler, merkt sich GLighter die Breite (auf dem Server, für alle Browser gleich). Zurücksetzen über **▦ Layout anpassen** → **＋ Bereich hinzufügen** → **Spaltenbreiten der Tabellen zurücksetzen**.

### Anordnen und eigene Kacheln

Auch die Live-Ansicht besteht aus Bereichen (Notiz, Live-Bild, Ereignisse). Mit **▦ Layout anpassen** verschiebst du sie, änderst die Breite, benennst sie um oder blendest sie aus – mit der Maus, mit **↑ / ↓** (auch am Handy) oder mit der Tastatur. **📊 ＋ Kachel** legt eine Kachel an, z. B. „Störungen heute“ als große Zahl. Alles dazu unter Protokolle → Layout anpassen und Kacheln.

## 3. Protokolle

Der Reiter **Protokolle** zeigt einen Zeitraum vollständig: Zusammenfassung, Wochenleiste, Verlauf aller Geräte, Auswertungen und die Liste aller Störungen.

### Zeitraum und Filter

- **Erfassungszeit** (eingestellte Überwachungszeit, z. B. 22–6 Uhr), **Heute**, **Gestern**, **7 Tage**, **30 Tage** oder **Von–bis**. ‹ › blättert um einen ganzen Zeitraum.
- **Quelle / Gerät**, **Art** (Mehrfachauswahl, z. B. Klopfen + Schritte) und **Liste** filtern alles darunter. Geräte, die es nicht mehr gibt, deren Daten aber vorhanden sind, stehen als „(ehemalig)“ in der Auswahl.
- **🖨 Protokoll** erstellt das Lärmprotokoll für Zeitraum, Gerät und Liste, **⬇ Bild (SVG)** ein Bild. Siehe Drucken.

### Bereiche anordnen (Dashboard)

Live und Protokolle bestehen aus **Bereichen** (Übersicht, Unterbrechungen, Verlauf, Ereignisse nach Uhrzeit, je Tag, Ereignisse im Zeitraum, Notizen und Bewegung, Sensoren im Zeitraum). Jeder Bereich hat oben eine Leiste:

- **▾ / ▸** klappt ein und aus (auch Doppelklick auf die Leiste).
- **✕** blendet aus. Wieder einfügen über **▦ Layout anpassen** → **＋ Bereich hinzufügen**.
- **⌖ nur sichtbarer Bereich** (Ereignisse, Sensoren): zeigt nur, was im Verlauf gerade zu sehen ist – zieh im Verlauf z. B. 20:00–22:00 auf, dann zeigen Tabelle bzw. Liste nur diese Zeit.

### ▦ Layout anpassen

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

### 📊 Kacheln (eigene Statistiken)

**📊 ＋ Kachel** (oben über den Bereichen, in Live und Protokolle) bzw. im Bearbeiten **＋ Bereich hinzufügen** → **Neue Kachel** legt eine Kachel als eigenen Bereich an – verschieben, breiter ziehen, umbenennen, einklappen und ausblenden wie die anderen.

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
- Jede Kachel erscheint auch **in Home Assistant** als Sensor (siehe Home Assistant → Kacheln).

### Zusammenfassung und Wochenleiste

Der Ring zeigt, wie viel der Zeit **störungsfrei** war. Daneben: Anzahl der Störungen, gestörte Zeit, längste Ruhe, aufgezeichnete Zeit und lautestes Ereignis.

Die **Kreise** darunter sind die letzten 7 Nächte bzw. Tage. Antippen wählt den Tag; die neueste Nacht bleibt immer sichtbar. Darunter stehen die **Datenkette** (Prüfsummen) und Unterbrechungen, siehe Unterbrechungen.

### Verlauf

Im Verlauf stehen die Geräte untereinander, für denselben Zeitraum. Je Zeile wählst du **Gerät** und **Darstellung** (Pegelspur, Lautstärke-Balken, Spektrogramm) und blendest Ebenen ein. „＋ Zeile hinzufügen“, ↑ ↓ ✕ ordnen die Zeilen; der Griff unter jeder Zeile ändert die Höhe.

- Läuft der Tag noch, endet die Zeitachse bei **jetzt** – das Neueste steht rechts und der Verlauf wächst jede Minute mit.
- Bei mehr als 2 Tagen zeigt er Minutenwerte, beim Hineinzoomen wieder die 125-ms-Werte.
- Oben markiert die KI je Störung die erkannte Art in ihrer Farbe; **blau** = laut Home Assistant an (z. B. Fernseher).
- **Schraffiert** = nicht aufgezeichnet (z. B. Stromausfall). Anklicken, um einen Kommentar zu setzen, siehe Unterbrechungen.

Bedienung wie im Live-Bild: Mausrad/zwei Finger zoomen, Bereich aufziehen, hineingezoomt ziehen oder ‹ › zum Verschieben, Umschalt + Mausrad für die Höhe, Doppelklick oder „Ganzer Zeitraum“ für alles. Am Handy liegen Prüf-Schwelle, Drucken und Bereich markieren unter **⋯ Werkzeuge**, die Ebenen hinter **🗂 Ebenen**.

### 📏 Prüf-Schwelle

Mit der Prüf-Schwelle schaust du nachträglich, welche Spitzen über einem frei gewählten Wert lagen – z. B. „Wie oft war es über −50 dB?“

1. „📏 Prüf-Schwelle“ antippen, Wert eingeben oder die violette Linie im Verlauf ziehen.
2. Je Gerät stehen Anzahl und Dauer der Spitzen im sichtbaren Ausschnitt (aus den 125-ms-Werten; weniger als 0,5 s Abstand = eine Spitze).
3. „Liste der Spitzen“ zeigt jede Spitze mit Uhrzeit, Dauer, Höhe, Abstand, **Art (KI)** und **Tonprofil**. Ein Klick springt im Verlauf dorthin.

Die Art kommt aus der Störung, wenn die Spitze in einer liegt, sonst aus dem gespeicherten **KI-Fingerabdruck** (ⓕ). Mögliche Hinweise: „kein Fingerabdruck an dieser Stelle“, „an diesem Tag kein KI-Fingerabdruck“, „nicht geprüft“ (mehr als 2000 Spitzen). Siehe KI.

> Die Prüf-Schwelle ist **nur eine Anzeige**. Gespeicherte Daten, Störungen und Prüfsummen bleiben unverändert. Beim Drucken wird sie mitgedruckt.

### Ereignisse im Zeitraum

- **Gruppen** fasst gleichartige Störungen zusammen (Abstand höchstens „Gruppe: höchste Pause“), **Alle einzeln** zeigt jede.
- **Sortieren:** Klick auf eine Spaltenüberschrift (Start, Dauer, Spitze, Schwelle, Hintergrund); noch ein Klick dreht die Reihenfolge um. Die Sortierung bleibt im Browser gespeichert.
- **Filtern mit Mehrfachauswahl:** Unter **Quelle / Gerät** und **Art** ein oder mehrere Einträge anklicken, z. B. nur „Türsensor Erschütterung“ und „Stimme“. Die Zeile über der Tabelle zählt Störungen und Sensor-Ereignisse getrennt.
- **Sensor-Ereignisse** (Home-Assistant-Regel „als Ereignis“, Handy als Bewegungsmelder) stehen zeitlich einsortiert mit orangem Rand; ✎ = Notiz.
- Auf schmalen Bildschirmen klappt ⊕ am Zeilenanfang die übrigen Spalten auf.
- Klick = im Verlauf hinspringen, Doppelklick oder ▶ = Ereignis öffnen, ⋮ = weitere Aktionen (Lärmspur herunterladen, KI neu bewerten, löschen).
- Markieren, dann **In Liste übernehmen** oder löschen. Gelöschte Einträge landen zur Sicherheit im Papierkorb; die Tagesaufzeichnung bleibt.
- **📝 Alle Notizen**, **🔎 Geräusch prüfen** (eigene Audiodatei auswerten, wird nicht gespeichert), **🧩 Profile & neu untersuchen**, **log.csv herunterladen**.

### Geräuschart bestätigen oder korrigieren

Die erkannte Art steht als farbiges Kästchen in der Spalte **Art**. Solange du sie nicht bestätigt hast, ist sie ein **„Vorschlag der Erkennung (Konfidenz x %)“** – so steht es auch in Lärmprotokoll, Ausdruck und Rohdaten. **Klick auf das Kästchen** (oder ⋮ → Geräuschart bestätigen): **Stimmt** bestätigt den Vorschlag, eine andere Art korrigiert ihn, **Bestätigung zurücknehmen** macht es rückgängig. Deine Bestätigung liegt in einer eigenen Datei (`bestaetigt.json`); die Einschätzung der Erkennung, `log.csv` und die Tagesaufzeichnung bleiben unverändert. Die Erkennung sagt nichts darüber, aus welcher Wohnung ein Geräusch kommt.

### Bekannte Geräusche ausfiltern

⋮ → **Als Muster ausfiltern …** legt aus der Störung ein Muster an (Gerät, Art, Uhrzeit, Dauer und Spitze vorbelegt, mit Vorschau „trifft auf N Störungen der letzten 30 Tage zu“). Ausgefilterte fehlen danach in der Liste; die Anzahl nennt sie („N nach Muster ausgefiltert“), **⊘ ausgefilterte zeigen** holt sie gekennzeichnet zurück.

### Notizen in der Tabelle

Jede angelegte Notiz steht als eigene Zeile **„📝 Notiz“** in der Tabelle, mit Zeit (von–bis), Gerät, Markierungen, Zeuge und Text. Liegt im Zeitraum der Notiz eine Störung, ist sie verknüpft: In der Notiz-Zeile steht **„🔗 Störung …“** (Klick öffnet die Störung), in der Störungs-Zeile der Notiztext. Mit **✎** bearbeitest du die Notiz. Im Filter **„📝 Notizen“** blendest du alle Notiz-Zeilen aus oder ein. Notizen zählen nicht als Störung.

### Protokolllisten

Eigene Listen wie „Bad“ oder „Garten“ sammeln Störungen zusätzlich zur Gesamtliste – von Hand („In Liste übernehmen“, im Ereignis unter „Listen“) oder automatisch je Gerät und Uhrzeit (⚙ Einstellungen → Geräte → Karte des Geräts → **Protokolllisten**). Jede Liste hat eine eigene Notiz und ein eigenes Lärmprotokoll.

## 4. Ereignis-Fenster

Ein Doppelklick auf eine Störung öffnet alle Einzelheiten.

### Kopfzahlen

Dauer, Spitze, Schwelle, Hintergrund, Spur (gezeigter Zeitraum) und:

- **Über dem Lautesten davor** bzw. **Leiser als das Lauteste davor** – Abstand der Spitze zum lautesten Pegel der Zeit davor (Störungen nicht mitgezählt). Belegt, dass die Störung lauter war als z. B. ein laufender Fernseher.
- Zustände aus Home Assistant (z. B. „Fernseher: aus“, Lautstärke), siehe Home Assistant.

### Grafik

- **Rot** = die Störung, **rote Linien** = Beginn und Ende, hellrot = Vor- und Nachlauf.
- **Gestrichelte Kästen** = Vorschläge der App aus deinen Tonprofilen („Teller klappern? 100 %“). Vorschläge außerhalb der Störung sind blasser. Antippen: ✓ Stimmt / ✕ Stimmt nicht.
- Darunter das **Spektrogramm**; bei mehreren Geräten der **Vergleich der Geräte** (Spitze je Gerät, Abstand zum lautesten).
- **▶ Ablauf zeigen** lässt einen Zeiger in Echtzeit darüber laufen (ohne Ton).

### Art, Profil und Listen

- **Art (KI)** mit Sicherheit in %. „Falsch? Korrigieren“ setzt die Art von Hand – deine Korrektur hat Vorrang. **🔎 Neu bewerten** wertet erneut aus (braucht den gespeicherten KI-Fingerabdruck).
- **🧩 Profil**: das ähnlichste eigene Tonprofil. **✓ Bestätigen** oder ein anderes wählen – beides wird ein neues Lernbeispiel.
- **Listen**: Störung einer Protokollliste zuordnen oder entfernen.

### Notizen und benannte Bereiche

- **📝 Notiz bei …** (oder Taste N, langes Drücken auf die Grafik) legt eine Notiz an genau dieser Stelle an, mit Schnell-Merkmalen und Zeuge.
- **🏷 Bereich benennen**: in der Grafik waagerecht ziehen und einen Namen wählen. Siehe KI → Lernen.
- **Notiz zum Ereignis**: ein freies Textfeld je Störung, wird automatisch gespeichert.

## 5. KI: Geräuscharten und Tonprofile

GLighter erkennt die **Art** eines Geräuschs mit einer kleinen KI, die komplett auf deinem Home-Assistant-Rechner läuft (YAMNet, keine Cloud). Zusätzlich lernt die App deine eigenen **Tonprofile**.

### Eingebaute Erkennung

Ohne dass du etwas anlernen musst, ordnet die KI jede Störung einer von 10 Arten zu:

| | Art | | Art |
|---|---|---|---|
| 🔨 | Klopfen/Schlag | 📺 | TV/Musik |
| 🚪 | Tür | 🔩 | Kratzen/Knarren |
| 👣 | Schritte | 🔔 | Signal/Alarm |
| 🗣 | Stimme | 🐾 | Tier |
| 〰 | Dauergeräusch | ❓ | Sonstiges |

Dazu setzt sie etwa jede Sekunde **Marker** mit feineren Arten (Türknallen, Schublade, Geschirr, Bohren, Möbelrücken, Rufen, Lachen, Bass, Hund …). Die Kachel **Geräusch jetzt** zeigt laufend, was gerade zu hören ist.

Einschalten: ⚙ Einstellungen → Erkennung → **Geräuschart erkennen (lokale KI)** (Standard an).

> Bei Stimmen erkennt die KI **nur die Art, nie den Inhalt**. Eine Spracherkennung gibt es bewusst nicht. Was du selbst gehört hast, trägst du als Notiz ein. Siehe Rechtliches.

### Eigene Tonprofile

Für Geräusche, die bei dir typisch sind („Testtür“, „Teller klappern“, „eigener Fernseher“):

1. **🧩 Tonprofil aufnehmen** (oben in der Notiz-Leiste), Name eingeben, **Start**.
2. 3 s Ruhe – dann das Geräusch machen, gern mehrmals. Jedes Gerät, das es gehört hat, speichert ein eigenes Beispiel (Klangfarbe, Pegelverlauf, KI-Fingerabdruck, kein Ton).
3. Prüfen und **Übernehmen**.

Jede neue Störung wird mit allen Profilen verglichen; ab 70 % Ähnlichkeit steht das Profil daran. Ein Profil kann **Hintergrund** sein (z. B. eigener Fernseher): solche Störungen bleiben grau sichtbar, zählen aber nicht. Verwalten unter **🧩 Profile & neu untersuchen**.

### Lernen aus Bereichen

Hat die KI ein Geräusch nicht oder falsch erkannt:

- Im Ereignis-Fenster **🏷 Bereich benennen** und den Bereich aufziehen, oder im Live-Bild bzw. Verlauf **🏷 Bereich markieren**.
- Eine vorhandene Art antippen oder einen neuen Namen eingeben. Gleicher Name = gleiche Art.
- In anderen Störungen schlägt die App ähnliche Stellen vor („Teller klappern? 87 %“). **✓ Stimmt** / **✕ Stimmt nicht** verbessern die Erkennung weiter. **🔎 Ähnliche finden** sucht in allen Störungen.

### Neu untersuchen

**🧩 Profile & neu untersuchen** → Zeitraum wählen → **Neu untersuchen**: Jede Störung bekommt ihr Profil neu (bestätigte bleiben) und die Tagesaufzeichnung wird durchgehend durchsucht – auch unter der Schwelle (z. B. „Fernseher lief 20:10–23:40“). Nach neuen Profilen einfach erneut starten.

### KI-Fingerabdruck

Einmal pro Sekunde, wenn etwas zu hören ist (mindestens 3 dB über dem Hintergrund), speichert die App die Zahlen der KI – **kein Ton**, nicht zurückverwandelbar. Damit funktionieren „Neu untersuchen“, die Spalte „Art (KI)“ der Prüf-Schwelle und das Lernen genauer.

- **KI-Fingerabdruck auch zwischen den Störungen speichern** (⚙ → Erkennung → Geräuschart erkennen (KI), Standard an, je Gerät): etwa 2–10 MB pro Gerät und Tag. Darunter steht, ob er läuft und wie viele Sekunden heute gespeichert wurden.
- **KI-Fingerabdruck speichern** (⚙ → Allgemein): zusätzlich der volle Fingerabdruck je Störung, für „Neu bewerten“.

> Wird der Rechner zu langsam, kommen die Geräte reihum dran; dann fehlt der Fingerabdruck an einzelnen Stellen. Die KI kann irren, besonders bei sehr leisen Geräuschen.

## 6. Geräte

Unter ⚙ Einstellungen → **Geräte** → Quellen stehen alle Mikrofone. Bis zu 9 Geräte sind möglich.

### Server-Mikrofon

Das Mikrofon am Home-Assistant-Rechner. Unter **Mikrofon** wählst du Eingang, Buchse und Lautstärke. Meist „Standard“ lassen. **Brummfilter** (50 Hz in Europa) entfernt Netzbrummen.

### Handy als Mikrofon

> **🔒 Pro:** Handys, Stream-URLs und IP-Kameras sind externe Geräte und gehören zu GLighter Pro. Das Server-Mikrofon ist immer frei.

- **Handy (Browser)**: „+ Handy (Browser)“, QR-Code scannen, Seite in Chrome öffnen, Zertifikatswarnung bestätigen, **Start**. Der Bildschirm muss an bleiben (Ladegerät). Der Link ist geheim und gehört nur zu diesem Handy.
- **Stream (z. B. App „IP Webcam“)**: „+ Handy-App / Stream-URL“, Adresse `http://HANDY-IP:8080/audio.wav`. Läuft auch mit ausgeschaltetem Bildschirm. Mit Login: Benutzername und Passwort in die eigenen Felder.
- Der Handy-Port ist standardmäßig **18443** (Add-on → Netzwerk, „8443/tcp“).

### Video

Bei Streams lässt sich **🎥 Video aufnehmen** einschalten: Bei einer Störung entsteht eine mp4-Datei **ohne Ton**. Ohne Störung wird nichts gespeichert. Qualität unter Speichern & Sicherung → Video, Ordner unter Speicherort.

> Kameraaufnahmen in Wohnungen können nach § 201a StGB problematisch sein – nur eigene Räume, keine fremden Personen filmen.

### Handy als Bewegungsmelder

Ein als Gerät eingerichtetes Handy kann zusätzlich zum Mikrofon als **Bewegungsmelder** dienen – wie ein Bewegungs- oder Vibrationssensor in Home Assistant:

- **🫨 Erschütterung** (Beschleunigungssensor): Das Handy liegt flach auf dem Boden, einem Tisch oder an der Wand und meldet Vibrationen – z. B. Trampeln, Bass, der durch die Decke kommt, Türenknallen oder Möbelrücken. Das belegt Körperschall, den man nicht nur hört, sondern spürt.
- **🏃 Bewegung im Kamerabild**: Die Kamera des Handys erkennt Bewegung im Bild (z. B. im Treppenhaus). Plötzliche Helligkeitsänderungen (Licht an/aus) werden herausgerechnet.
- **📐 Neigung**: Das Handy merkt sich nach dem Start seine Ruhelage und meldet, wenn es bewegt, gekippt oder angehoben wird (Empfindlichkeit hoch/mittel/niedrig ≈ 3°/6°/12°). Liegt es 1 Minute ruhig in einer neuen Lage, gilt diese als neue Ruhelage.

**Einschalten:** ⚙ Einstellungen → Geräte → Karte des Handys → **Handy als Bewegungsmelder** → „Erschütterung“ und/oder „Bewegung im Kamerabild“ anhaken, **Empfindlichkeit** wählen (hoch, mittel, niedrig). Danach am Handy die Seite neu laden und **Start** tippen. Der Browser fragt nach der Kamera bzw. (iPhone) nach „Bewegung und Ausrichtung“.

### Mit der App IP Webcam

Ist das Handy über **„+ Handy-App / Stream-URL“** mit der Android-App **IP Webcam** verbunden, liest GLighter die Sensoren der App mit (`http://HANDY:8080/sensors.json`, ein Login aus der Adresse wird mitbenutzt). Auf der Karte des Geräts heißt der Kasten **„IP Webcam: Handy-Sensoren mitlesen“**, mit denselben Schaltern (Erschütterung, Neigung, Bewegung im Kamerabild) und derselben Empfindlichkeit.

- **Erschütterung und Neigung** kommen aus dem Beschleunigungssensor des Handys – in IP Webcam müssen die Sensoren eingeschaltet sein.
- **Bewegung im Kamerabild** nutzt die **Bewegungserkennung** von IP Webcam – in der App einschalten.
- Fehlt etwas oder ist die App nicht erreichbar, steht auf der Karte ein Hinweis, was einzuschalten ist.

> **Datenschutz:** Ausgewertet wird nur auf dem Handy. Gesendet werden nur Zahlen (Stärke der Erschütterung, Anteil der veränderten Bildpunkte) – **kein Bild und kein Video**. Das Vorschaubild sieht man nur auf dem Handy selbst.

**Was dabei entsteht:**
- Am Handy und in der Geräteleiste blinkt 🫨 bzw. 🏃, solange ausgelöst ist.
- Jede Erschütterung bzw. Bewegung wird mit Beginn, Ende und Spitze gespeichert (`bewegung.csv` im Datenordner). Sie gilt bis 20 s nach dem letzten Auslösen als „an“.
- Im Reiter **Protokolle** steht die Liste „Erschütterung und Bewegung im Zeitraum“; ein Klick zeigt die Stelle im Verlauf. Das Lärmprotokoll enthält eine eigene Tabelle.
- In **Home Assistant** erscheint je Handy ein Sensor „Erschütterung“ (Vibration) bzw. „Bewegung“ (Bewegung) – nutzbar in Automationen und in den Regeln, z. B. „nur festhalten“, damit es bei jeder Störung und im Tagesverlauf steht.

Gehört zu den externen Geräten und damit zu GLighter Pro.

### Geräte-Karte

- **Name**, **aktiv**, **Verstärkung (dB)** und Brummfilter.
- **⏺ Nur aufzeichnen (keine Erkennung)**: Der Pegel wird weiter in der Tagesaufzeichnung gespeichert (mit Prüfsummen-Kette, live und im Verlauf sichtbar, im Lärmprotokoll-Graphen). Aus diesem Gerät entstehen aber keine Störungen, keine KI-Einordnung, keine Lärmspur und keine Meldung an Home Assistant. Die Kachel zeigt „⏺ nur Aufzeichnung“. Schaltest du die Erkennung wieder ein, gilt sie ab dann; ältere Zeiten lassen sich mit „Neu untersuchen“ auswerten.
- **⚙ Pegel & Schwelle**: eigene Einstellungen nur für dieses Gerät.
- **📏 Eigene Referenzlinien**: z. B. „Fernseher −70 dB“, erscheinen in allen Grafiken dieses Geräts.
- **Protokolllisten**: Störungen dieses Geräts automatisch einer Liste zuordnen, auf Wunsch nur zu bestimmten Uhrzeiten.
- Aus einer Sicherung übernommene Geräte, die nicht erreichbar waren, sind ausgeschaltet und tragen den Hinweis „bitte prüfen“.

### Geräte einpegeln

Damit Pegel verschiedener Geräte vergleichbar sind:

1. Alle Mikrofone nebeneinander legen, etwa gleich weit (ca. 1 m) vom Lautsprecher.
2. **Geräte einpegeln** → mitmessende Geräte anhaken (mindestens zwei).
3. **Testgeräusch** wählen: **hier abspielen** (über den PC oder das Handy, auf dem die Einstellungen offen sind; mit **▶ Probehören** die Lautstärke prüfen), **auf Handy X abspielen** (ein verbundenes Handy spielt das Rauschen und misst dafür selbst nicht mit) oder **eigenes Geräusch** (Dunstabzug, Föhn …).
4. **Messung starten**: Die Schritte **1 Ruhe → 2 Geräusch → 3 Ergebnis** stehen groß da, darunter der Pegel jedes Geräts – so sieht man sofort, ob jedes Gerät das Geräusch hört. Das Testgeräusch startet und stoppt von selbst.
5. Ergebnis prüfen: Ist ein Gerät zu leise oder unruhig, steht dabei, was zu tun ist (z. B. „näher an den Lautsprecher“). Dann **Übernehmen und festhalten**.

Jedes Gerät bekommt eine eigene Verstärkung, sodass alle beim selben Geräusch denselben Wert zeigen. Jede Messung wird festgehalten und erscheint im Lärmprotokoll. Ändert sich die Verstärkung später von Hand, steht beim Gerät „⚠ seit dem Einpegeln geändert“; liegt das Einpegeln über 3 Monate zurück, wird erneutes Einpegeln empfohlen.

### Mehrere Räume vergleichen

Löst ein Gerät aus, speichern alle anderen für denselben Zeitraum mit („Bei einer Störung alle Geräte mitspeichern“). Im Ereignis-Fenster zeigt **Vergleich der Geräte** die Spitze je Gerät. Ein Fernseher im Wohnzimmer ist dort am lautesten und hat viele Höhen; Klopfen über Decke und Wände ist in allen Räumen ähnlich und tief.

## 7. Home Assistant

GLighter arbeitet mit Home Assistant zusammen: Regeln fragen Zustände ab (Fernseher an, Waschmaschine läuft, Sensor ausgelöst), und über MQTT meldet die App Störungen, Prüfsummen und Schalter zurück.

### Regeln

⚙ Einstellungen → Reiter **Regeln** → **＋ Regel hinzufügen**. Zuerst wählst du, was die Regel tun soll, danach das Gerät aus der Liste (mit Suche). Zustände, Nachlauf und Höchstdauer werden passend vorbelegt. Keine Automation, kein YAML.

| Art | Was passiert | Beispiel |
|---|---|---|
| 📈 **Schwelle anheben** (Pro) | Erkennung läuft weiter, nur unempfindlicher | eigener Fernseher, Sonos |
| 🔕 **keine Störung melden** | Graph läuft weiter, keine Störung | Sprachassistent, eigene Tür |
| ⏸ **pausieren** | in dieser Zeit nicht auswerten | Staubsauger |
| 📝 **nur festhalten** | weiter aufnehmen und mitschreiben, wann es an war | Fernseher |
| 🚩 **als Ereignis** | wie festhalten, dazu Fähnchen und eigene Zeile | Tür-, Vibrationssensor |

Jede Regel ist eine **Karte**. Zugeklappt zeigt sie Name, Art, Gerät, den Zustand jetzt und einen Schalter (an/aus). Ein Klick klappt sie auf:

| Feld | Bedeutung |
|---|---|
| **Name** | Unter diesem Namen wird die Regel festgehalten, z. B. „Erschütterung Wand“. Leer = Name aus Home Assistant. |
| Aktion | die Art (oben), jederzeit änderbar |
| Gerät (Home Assistant) | z. B. `media_player.fernseher`, `binary_sensor.vibration_wand` |
| Für welches Gerät | für welches Mikrofon die Regel gilt (oder alle) |
| aktiv bei | Zustände zum Anhaken (z. B. *an*, *spielt*). Unter **Bedingung als Text** geht auch `!off` = alles außer off, `>1` = Zahl größer 1 |
| Nachlauf, höchstens | bei Schwelle anheben, keine Störung melden und pausieren: so lange danach weiter, Höchstdauer |

Unten in der Karte: **▶ Testen** (fragt Home Assistant jetzt und sagt, ob die Regel greift), **⧉ Kopieren**, **✕ Löschen**. Oben im Reiter steht, ob Home Assistant verbunden ist und welche Regeln gerade aktiv sind.

### Schwelle anheben (Fernseher, Sonos)

Läuft dein eigener Fernseher, soll er keine Störung auslösen – Lärm von außen, der deutlich lauter ist, aber schon. Die Regel hebt dafür die Schwelle an, solange das Gerät an ist (plus Nachlauf). Die Erkennung läuft weiter.

- **Anhebung:** z. B. +10 dB (0–40). Im Graph siehst du die angehobene Schwelle.
- **Mit der Lautstärke mitgehen:** Meldet das Gerät seine Lautstärke, folgt die Anhebung ihr. Beispiel: eingepegelt bei 35 % mit +9 dB → bei 18 % etwa +4,5 dB, stumm keine Anhebung (höchstens das Doppelte).
- **🎚 Einpegeln – gedrückt halten:** Fernseher oder Sonos so laut laufen lassen wie sonst, sonst möglichst still. Taste mindestens 3 Sekunden gedrückt halten. Solange gemessen wird, nimmt GLighter den Pegel; beim Loslassen übernimmt es die aktuelle Lautstärke. Anhebung = Pegel des Geräts (95 %) + 3 dB Abstand über der normalen Schwelle. Das Ergebnis steht in der Karte und im Protokoll.
- **Nachweis:** In der Ereignistabelle steht bei jeder Störung in dieser Zeit „📈 Fernseher +9 dB“, in der Störung „Schwelle +9 dB“. Die Zeiträume stehen in `ha_anhebung.csv`. Die Tagesaufzeichnung läuft unverändert weiter.
- Ohne Pro wird die Regel gespeichert, wirkt aber nicht.

„jetzt: …“ zeigt live, was Home Assistant meldet – so siehst du, welchen Zustand ein Gerät wirklich hat. Im Zweifel wird aufgenommen.

**Festhalten** schreibt jeden Wechsel in `ha_zustand.csv`. An jeder Störung steht dann z. B. „Fernseher: an · 🔊 18 %“, im Verlauf erscheint oben ein **schmaler blauer Streifen** (je Sensor eine eigene Spur), und das Lärmprotokoll nennt den Zustand. Nur **pausieren** färbt die ganze Höhe (dort wurde nicht ausgewertet).

**Als Ereignis** zeichnet je Sensor ein farbiges Fähnchen und eine rote Linie über die ganze Höhe. Die Farbe wählst du in der Regel unter **Farbe** (↺ = automatisch). Jedes „an“ steht unter **📡 Sensor-Ereignisse** in der Ereignistabelle – mit Uhrzeit, Dauer und Notiz (✎). Sensor-Ereignisse zählen **nicht** als Störung und werden getrennt gezählt. Die Umstellung gilt auch rückwirkend, weil die Zustände schon in `ha_zustand.csv` stehen.

**Notiz zum Zeitraum:** Klick auf den Streifen (oder ✎ in der Liste) öffnet ein Fenster für eine Notiz, z. B. „eigener Film geschaut“. Sie steht im Streifen, in der Liste und im Lärmprotokoll.

**Filter „📡 Sensoren“** (Protokolle, oben): Mehrfachauswahl, welche Sensoren, Handy-Erschütterung/-Bewegung und ob Störungen gezeigt werden. Gilt für Verlauf, Listen und Tabelle. Meldet der Fernseher seine Lautstärke, wird sie mitgeschrieben.

> Bereits Festgehaltenes behält seinen Namen, auch wenn du ihn später änderst.

### Zigbee-Sensoren (Vibration, Bewegung, Tür)

Sensoren, die in Home Assistant eingebunden sind (z. B. über Zigbee2MQTT oder ZHA), funktionieren genauso:

1. Regel hinzufügen, Entität des Sensors wählen (z. B. `binary_sensor.vibration_decke_occupancy`).
2. Name eingeben, z. B. „Erschütterung Decke“.
3. Aktion **als Ereignis** (oder **nur festhalten**), „an bei“ `on`.

Ab dann steht bei jeder Störung, ob gleichzeitig eine Erschütterung gemeldet wurde – ein starker Hinweis auf Trittschall oder Klopfen über das Gebäude.

### MQTT: Steuern und Melden

Ist MQTT eingerichtet, erscheint in Home Assistant das Gerät **GLighter** mit:

- Schalter **Aufzeichnung**, **Manuell erfassen (außerhalb der Zeit)**, Zahl **Pause (Minuten)**, Tasten **Pause 15 min**, **Pause 1 h**, **Fortsetzen**, Sensor **Pause bis**.
- Je Gerät: Ereignis **Störung (Auslöser)** (beginn, ende, erkannt – mit Spitze, Dauer, Art, Profil), Geräte-Auslöser für Automationen, Sensor „Letzte Geräuschart“ und stündlich die aktuelle **Prüfsumme** (in Home Assistant unabhängig gespeichert).

Beispiel – 10 Minuten Pause, wenn die Katzentoilette reinigt:

```yaml
automation:
  - alias: "GLighter pausieren, wenn das Katzenklo reinigt"
    trigger:
      - platform: state
        entity_id: sensor.katzenklo_status
        to: "cleaning"
    action:
      - service: mqtt.publish
        data:
          topic: gaslighter/pause/set
          payload: '{"minutes": 10, "reason": "Katzenklo"}'
```

Eine von Hand gestoppte Aufzeichnung wird durch eine Pause aus Home Assistant nicht automatisch wieder gestartet.

### Störung direkt im Dashboard erfassen

Mit MQTT meldet das Add-on zwei Elemente am Gerät „GLighter“:

- **Störung / Notiz erfassen**: Textfeld. Text eingeben, Enter drücken, schon ist die Notiz mit der aktuellen Uhrzeit gespeichert. Das Feld leert sich danach.
- **Störung jetzt markieren**: Knopf. Ein Tipp legt sofort eine Notiz „Störung (Home Assistant)“ an, ohne Text.

Beide legst du auf ein beliebiges Dashboard (z. B. als Karte „Entitäten“). Liegt kurz davor eine Störung, wird die Notiz ihr zugeordnet, genau wie bei der Notizleiste im Live-Bild.

### Keine Störung melden (Graph läuft weiter)

Manchmal soll eine Störung nicht gemeldet werden, der Graph aber trotzdem weiterlaufen, zum Beispiel wenn du selbst die Tür öffnest.

- **In einer Regel:** Wähle bei der Aktion **„keine Störung melden“**. Solange die Bedingung gilt und für den **Nachlauf** (z. B. 10 Minuten), entsteht keine Störung. Der Graph wird weiter aufgezeichnet, es gibt keine Lücke.
- **Vorlauf (s), z. B. für einen Sprachassistenten:** Das Rufwort („Hey Jarvis“) kommt, *bevor* der Assistent auf „hört zu“ wechselt. Mit **Vorlauf** zählt auch eine Störung nicht, die bis zu so viele Sekunden vor dem Einschalten der Regel begann. Dafür hält GLighter jede Störung so lange (Vorlauf + 2 s) zurück, bevor sie gemeldet wird. Pegel und Graph bleiben unverändert; im Protokoll steht „nicht gezählt“. **Einrichten:** Regel hinzufügen, Entität `assist_satellite.…` wählen – Zustände `!idle`, „keine Störung melden“, Vorlauf 3 s und Nachlauf 0,5 min werden vorbelegt. So zählen Rufwort, Befehl und die Antwort aus dem Lautsprecher nicht.
- **Als Knopf im Dashboard:** Am Gerät „GLighter“ gibt es **„Keine Störung melden (Dauer starten)“**, **„Störungen wieder melden“**, die einstellbare **Dauer** (1–240 Minuten, Standard 10) und **„Keine Störungsmeldung bis“**. Lege sie auf dein Dashboard. Ein Tipp auf den Knopf startet die eingestellte Dauer.

### Kacheln als Sensoren

Jede Kachel, die du in GLighter angelegt hast (Live oder Protokolle, siehe Kacheln), erscheint mit MQTT im Gerät **GLighter** als eigener Sensor, z. B. `sensor.gaslighter_tile_s_1a2b3c4d` (eindeutige Kennung `gaslighter_tile_<Kennung>`).

- **Zustand** ist der Hauptwert der Kachel: Anzahl, Gesamtdauer in Sekunden oder Spitze in dBFS. Der Name ist der Name der Kachel bzw. die eigene Überschrift aus **✎**.
- **Attribute:** Zeitraum (von, bis), Anzahl der Einträge, Darstellung, Aufteilung, Kennzahl, `eintraege` (Name und Wert je Balken, Listen- oder Tabellenzeile) und bei Aufteilung nach Zeit `verlauf` (Werte für Grafiken).
- Aktualisiert wird jede Minute und kurz nach jeder neuen Störung – gesendet wird nur, was sich geändert hat.
- „Gewählter Zeitraum“ gilt in Home Assistant als **heute**.
- Löschst du eine Kachel, verschwindet auch der Sensor aus Home Assistant.

Im **Dashboard in Home Assistant** (siehe unten) setzt der Bereich **Eigene Kacheln** diese Sensoren passend ein: Zahlen als Kachel-Karte, Trends als Statistik-Grafik, Balken als Verlaufs-Grafik, Listen und Tabellen als Text-Karte.

### Dashboard in Home Assistant anlegen

⚙ Einstellungen → Reiter **Regeln** → **Dashboard in Home Assistant**. GLighter legt dort mit einem Klick ein fertiges Dashboard mit seinen Entitäten an. Du wählst:

- **Name** und **Adresse** (z. B. `gsim-glighter`, steht danach in der Adresszeile von Home Assistant),
- ob es in der **Seitenleiste** steht und ob es **nur für Administratoren** sichtbar ist,
- welche **Bereiche** hinein sollen: Jetzt (Störung, Pegel, heute), Pegel der letzten 24 Stunden, Störung erfassen, Keine Störung melden, Aufzeichnung und Pause, weitere Mikrofone, **eigene Kacheln**, Knopf „GLighter öffnen“.

**In Home Assistant anlegen** erstellt das Dashboard. Gibt es unter der Adresse schon eins, fragt GLighter nach, bevor es ersetzt wird (Änderungen, die du dort gemacht hast, gehen dabei verloren). Ohne Klick ändert GLighter in Home Assistant nichts.

Unter **Als YAML anzeigen** steht dieselbe Vorlage zum Kopieren: in Home Assistant ein Dashboard anlegen, **Bearbeiten** → ⋮ → **Rohdaten-Konfigurationseditor**, einfügen, speichern. Das Dashboard kannst du danach in Home Assistant frei weiter bearbeiten.

## 8. Drucken und Lärmprotokoll

Es gibt zwei Ausdrucke: das **Lärmprotokoll** (Bericht mit Zusammenfassung und Liste) und den **Verlauf als Notenblatt** (die Kurven Zeile für Zeile).

### Lärmprotokoll

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

**Musterfilter:** Standardmäßig sind alle Störungen enthalten; nach Muster ausgefilterte stehen mit dem Vermerk „nach Muster … ausgefiltert“ darin. Mit **nach Muster ausgefilterte weglassen** fehlen sie, und oben steht, welche Muster wie viele entfernt haben.

Oben auf der Seite (wird nicht mitgedruckt) wählst du **Tagesgrafik** (Standard an) und **Grafik je Störung** (Standard aus): eine kleine Grafik mit Umfeld unter jeder Störung, die eine Notiz hat oder aus der gewählten Liste stammt (höchstens 300).

Im Browser drucken oder als PDF speichern. Das ausgedruckte Dokument heißt immer „Lärmprotokoll“.

> Pegel sind relative dBFS-Werte, keine geeichte Messung in dB(A). Tonaufnahmen kommen nie ins Protokoll. Keine Rechtsberatung.

### Verlauf drucken (Notenblatt)

Im Verlauf **🖨 Drucken**:

- **Zeitraum**: von–bis oder Schnellwahl „Sichtbarer Ausschnitt“, „Zeitraum des Berichts“, „Alle Daten“.
- **Zeit je Zeile**: 1 min bis 1 h (Standard 10 min – ein ganzer Tag sind 144 Zeilen).
- **Geräte** untereinander, **Inhalt** (Pegelspur, Spektrogramm, Störungs-Infos und Notizen), **Zeilen ohne Aufzeichnung zusammenfassen** (Standard an).
- **Skala**: gleich für alle Zeilen (vergleichbar) oder je Zeile angepasst (mehr Einzelheiten); **A4 quer** oder **hoch**.
- **Belege (Zusammenfassung, Zeitachse, Prüfsummen)** (Standard an): oben eine Zusammenfassung nach Zeitpunkt, Art, Intensität, Dauer und Häufigkeit, unten Messmethode, Zeitachse mit allen Tagen, Prüfsummen mit Erklärung und der Link zu den Rohdaten (CSV). Bei jeder Störung stehen Impulse und, falls nicht bestätigt, „Vorschlag der Erkennung (Konfidenz x %)“.
- **nach Muster ausgefilterte weglassen**: wie beim Lärmprotokoll.

Der Dialog schätzt Zeilen und Seiten. **Vorschau öffnen** baut die Seiten in einem neuen Fenster auf; dort **Drucken** oder als PDF speichern. Eine aktive Prüf-Schwelle wird mitgedruckt, mit Zählung je Zeile.

## 9. Sicherung, Import und Export

### Sicherung herunterladen

⚙ Einstellungen → Speichern & Sicherung → **Sicherung herunterladen / einspielen (ZIP)** → **⬇ Sicherung herunterladen**. Die ZIP-Datei enthält alles: Einstellungen, Geräte, Zeitprofile, Regeln, `log.csv` und alle Protokolldateien, Tagesaufzeichnungen mit Prüfsummen, KI-Ergebnisse, Tonprofile, Notizen, Kommentare zu Unterbrechungen, benannte Bereiche, Listen, Kacheln, Anordnung der Ansichten (`layout.json`), Videos und – falls gespeichert – Ton.

> Die Datei kann groß werden (Hunderte MB). Am besten regelmäßig herunterladen und an einem anderen Ort aufbewahren.

**Ohne Geheimnisse:** Die normale Sicherung und die tägliche Sicherung auf Netzlaufwerk/NAS enthalten **nicht** den geheimen Schlüssel der Prüfkette (`kette_schluessel.json`), keine Passwörter von Netzwerk-Kameras und keine Handy-Kennungen. So taugt eine verlorene Sicherung nicht dazu, Daten unbemerkt neu durchzurechnen oder sich als dein Handy auszugeben.

### Umzug auf ein neues Gerät (mit Schlüssel)

Unter **🔑 Umzug auf neues Gerät (mit Schlüssel)** ein Kennwort (mindestens 8 Zeichen, zweimal) eingeben und **⬇ Umzugs-Sicherung herunterladen**. Die ZIP enthält zusätzlich den Kettenschlüssel und die Zugangsdaten – **verschlüsselt** mit dem Kennwort (scrypt und HMAC-SHA256, verschlüsseln und danach gegen Verändern sichern). Ohne das Kennwort lassen sie sich nicht lesen. Das Kennwort wandert nie in die Adresse und wird nicht gespeichert; bewahre es getrennt von der Datei auf.

Beim Einspielen fragt die Vorschau nach dem Kennwort. Ein falsches Kennwort bricht ab, bevor etwas eingespielt wird. Ohne Kennwort wird die Datei wie eine normale Sicherung eingespielt.

Zum Weiterverarbeiten gibt es außerdem `log.csv` (Reiter Protokolle), die Notizen als CSV (📝 Alle Notizen) und das Lärmprotokoll als PDF.

### Sicherung einspielen

> **🔒 Pro:** Der erste Import ist kostenlos (z. B. für den Umzug), weitere Importe gehören zu GLighter Pro. Das Herunterladen einer Sicherung ist immer frei.

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

### Tägliche Sicherung auf Netzlaufwerk, NAS oder USB

> **🔒 Pro:** Die tägliche Sicherung und „Platz sparen“ gehören zu GLighter Pro. **„⬇ Sicherung herunterladen“ und `log.csv` bleiben immer frei.** Läuft Pro ab, hält die tägliche Sicherung an; schon ausgelagerte Tage bleiben lesbar.

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

### Platz sparen

Mit **„Platz sparen: alte Daten nur im Ziel behalten“** werden Dateien, die älter sind als „Löschen nach (Tagen)“ und geprüft im Ziel liegen, hier durch einen Verweis auf die Kopie ersetzt. **Protokolle, Verlauf, Druck und Prüfsummen-Kette funktionieren weiter** – sie lesen diese Tage aus dem Ziel. Schläft das Netzlaufwerk, dauert das erste Laden etwas länger („Netzlaufwerk wacht evtl. gerade auf“). Ist es gar nicht erreichbar, fehlen diese alten Tage, bis es wieder da ist. Einstellungen, `log.csv` und die Daten der letzten Tage bleiben immer hier.

Ist zusätzlich **„Alte Aufnahmen automatisch löschen“** eingeschaltet, löscht GLighter bei eingestelltem Ziel nur noch, was geprüft im Ziel liegt.

### Was beim Einspielen passiert

- **Nichts wird doppelt und nichts überschrieben**: vorhandene Störungen, Notizen und Listen bleiben, nur Fehlendes kommt dazu. Mehrmals einspielen ist unschädlich.
- **Tage, die es schon gibt** (z. B. „heute“ nach einer Neuinstallation): Die fehlenden Minuten werden ergänzt. Die Prüfsummen-Kette bleibt prüfbar – der eingespielte Teil bekommt einen eigenen Abschnitt, und unter „Unterbrechungen“ steht „Import …: um N Minuten ergänzt“. Überschneiden sich die Zeiten mit anderen Daten, wird der Tag übersprungen und im Bericht genannt.
- **Geräte, die es nicht mehr gibt**: Ihre Daten werden trotzdem eingespielt und sind als „(ehemalig)“ im Verlauf, im Gerätefilter und im Druck auswählbar.
- Speicherorte (Ausgabe- und Clip-Ordner) bleiben die dieses Systems.

### Zurücksetzen

⚙ → Allgemein → **Zurücksetzen**: wahlweise Messdaten & Störungen, Notizen & Listen, Tonprofile oder Einstellungen auf Standard. Geräte und Verbindungen bleiben immer. Vorher wird eine Sicherung angeboten.

### Suchverzeichnis

GLighter führt ein **Suchverzeichnis** (SQLite-Datei `suchindex.sqlite` im App-Datenordner). Es beschleunigt Lärmprotokolle über Wochen und Monate:

- **Kettenprüfung je Tag:** Das Ergebnis wird mit einer SHA-256-Prüfsumme über den *Inhalt* aller Dateien des Tages gespeichert. Ändert sich auch nur ein Byte, wird der Tag neu geprüft – die Prüfung ist genauso streng wie ohne Verzeichnis.
- **Verdichtete Tagesspuren** (je 10 Sekunden) für die Grafiken im Lärmprotokoll.

Das Verzeichnis enthält nur abgeleitete Daten, ändert nie Aufzeichnung, Datenkette oder Störungen, ist nicht in der Sicherung und füllt sich nach dem Start langsam im Hintergrund. **Einstellungen → Allgemein → Sicherung → Neu aufbauen** leert es; es baut sich danach von selbst wieder auf. Fehlt es oder ist es beschädigt, arbeitet GLighter ohne – nur langsamer.

## 10. Unterbrechungen, Datenkette und Updates

### Unterbrechungen

Läuft das Add-on nicht (Stromausfall, Home Assistant neu gestartet, Update über den Add-on-Store), fehlt die Aufnahme. GLighter merkt sich das beim nächsten Start und zeigt es in Protokolle unter der Zusammenfassung:

- **ohne Herunterfahren beendet, z. B. Stromausfall** – das Add-on konnte sich nicht abmelden (Strom weg, Absturz).
- **von Home Assistant angehalten / neu gestartet** – sauber beendet (Neustart, Add-on gestoppt).
- **Update** – neue Fassung installiert.
- **Lücke in der Tagesaufzeichnung, Ursache nicht protokolliert** – in den Daten fehlen mehr als 90 Sekunden, ohne dass der Start es gemerkt hat (z. B. Umzug auf eine neue Installation). Gilt für das Mikrofon am Rechner und Streams; bewusste Pausen zählen nicht, Handys werden nicht geprüft.

Nach einem Stromausfall startet Home Assistant das Add-on von selbst, sobald der Rechner wieder läuft.

### Kommentar setzen

- Im **Verlauf** auf die schraffierte Fläche klicken bzw. tippen – ein kleines Fenster mit Zeitraum und Ursache öffnet sich. Text eingeben, z. B. „Sicherung rausgeflogen“, **Speichern**.
- Oder in der Liste „Nicht aufgezeichnet …“ auf **📝 Kommentar**.

Der Kommentar steht in der Schraffur, in der Liste, im Druck und im Lärmprotokoll. Die Aufzeichnung selbst bleibt unverändert.

### Watchdog

Auf der Add-on-Seite in Home Assistant den Schalter **Watchdog** einschalten: Wird das Add-on unerwartet beendet, startet Home Assistant es neu.

### Datenkette (Prüfsummen)

Jede geschriebene Minute der Tagesaufzeichnung bekommt eine SHA-256-Prüfsumme, die auf der vorherigen aufbaut. Ändert jemand nachträglich einen Wert oder entfernt eine Minute, passt die Kette ab dieser Stelle nicht mehr.

- Protokolle zeigt „🛡 Datenkette geprüft: vollständig und unverändert“ bzw. wo es abweicht.
- Das Lärmprotokoll listet je Gerät und Tag das Ergebnis und die letzte Prüfsumme.
- Jedes Gerät meldet stündlich seine Prüfsumme an Home Assistant (dort unabhängig gespeichert).
- Aus einer Sicherung ergänzte Tage haben einen eigenen Abschnitt in der Kette, siehe Sicherung.

### Updates

> **Neu (Sicherheit):** Updates aus `share` werden nur übernommen, wenn in der Konfiguration **„Updates aus /share annehmen“ (`share_update`)** eingeschaltet ist **und** der Ordner eine gültige Signatur von G-Simulation enthält (`manifest.txt` + `manifest.sig`). Unsignierte oder veränderte Ordner werden abgelehnt (Hinweis im Protokoll). Gestartet wird eine geprüfte Kopie unter `/data/update_run`.

**Ohne Aufnahmelücke:** den Ordner `gaslighter` aus der Update-Zip per Samba nach `\\homeassistant\share\gaslighter_update\` kopieren (vorhandene Dateien überschreiben). Nach 10–20 s startet nur das Programm neu; die Aufnahme läuft weiter und wird nachgeliefert. Startet die neue Fassung nicht, nimmt das Add-on automatisch wieder die vorige.

**Volle Installation** (nur wenn eine Version es verlangt, z. B. neuer Name oder Watchdog): den Ordner aus der vollen Zip nach `\\homeassistant\addons\` kopieren und das Add-on in Home Assistant neu erstellen. Das gibt eine kurze Lücke.

Jeder Start, jedes Update und jede Unterbrechung steht mit Uhrzeit und Version in Protokolle und im Lärmprotokoll.

## 11. Einstellungen von A bis Z

Ganz oben wählst du **Alle Geräte** oder ein einzelnes Gerät. Beim Gerät lassen sich mit „Eigene Einstellungen für dieses Gerät“ abweichende Werte festlegen (Schwelle, Mindestdauer, Aufnahmezeit, Speichern). Die Leiste oben zeigt live Pegel, Hintergrund, Schwelle und die **Vorschau** (lila) deiner noch nicht gespeicherten Einstellungen.

**🎯 Schwelle automatisch einstellen** (🔒 Pro) – schlägt Werte für „Wann gilt etwas als Störung?“ vor, für das oben gewählte Gerät (auch ein verbundenes Handy). **Aus der letzten Nacht** nimmt die Ruhezeit der letzten Nacht ohne die Störungen darin – kein Warten, am zuverlässigsten. **Jetzt messen** (30 s, 1 min oder 5 min): in der Zeit leise sein; war es zwischendurch deutlich lauter, steht „Messung gestört – bitte wiederholen“. Der Vorschlag steht als Tabelle „jetzt → Vorschlag“ da; erst **Übernehmen** trägt ihn ein (lila Vorschau), **Speichern** behält ihn. ⓘ erklärt jede Einstellung; „Hilfe anzeigen“ blendet die Texte aus.

### Geräte

- **Quellen (Mikrofone)** – siehe Geräte.
- **Geräte einpegeln (gleich laut stellen)** – siehe Einpegeln.
- **Mikrofon** – Eingang am Server, Buchse, Lautstärke, Tonqualität (16000 Hz reicht für Klopfen).
- **Messort und Fenster** – je Gerät in der Gerätekarte: wo im Raum gemessen wird (z. B. „Schlafzimmer, Regal an der Wand zum Nachbarn“) und ob das Fenster **meist offen**, **meist geschlossen** oder **wechselnd** ist. Optional ein Fenstersensor aus Home Assistant (Regel „nur festhalten“). Beides steht in der Messmethode von Lärmprotokoll, Ausdruck und Beweispaket.

### Erkennung

### Wann gilt etwas als Störung?

> **🔒 Pro:** Ohne Pro sind diese Werte nur zum Ansehen; GLighter arbeitet mit den Standardwerten. Ändern lassen sie sich mit GLighter Pro.

| Einstellung | Bedeutung |
|---|---|
| Art der Schwelle | **Passt sich an, mit Grenzen** (empfohlen), **Passt sich an**, **Fest** |
| Wie viel lauter als normal? | Abstand zum Hintergrund, 8–10 dB ist ein guter Start. Kleiner = empfindlicher. |
| Untergrenze / Obergrenze | Tiefer bzw. höher geht die Schwelle nie. |
| Feste Schwelle | nur bei „Fest“ |
| „Normal“ wird gelernt aus den letzten … | Zeitraum für den Hintergrund (z. B. 60 s) |
| So wird „normal“ berechnet | **Leiseste Momente** (empfohlen), typischer Pegel, Minimum, Durchschnitt, Maximum |
| Anpassung, wenn es lauter / leiser wird | Groß = Lärm zieht die Schwelle kaum mit; klein = folgt schnell |
| Mindestdauer (ms) | 0 = jeder Klopfer zählt; 40–60 filtert Knackser |

### Geräuschart erkennen (KI)

**Geräuschart erkennen (lokale KI)** – ordnet Störungen ein (Tür, Klopfen, Musik …), kein Ton wird gespeichert. **KI-Fingerabdruck zu jeder Störung speichern** – bessere Unterscheidung beim Lernen und „Neu bewerten“ ohne Ton. **KI-Fingerabdruck auch zwischen den Störungen speichern** – durchgehend, für „Neu untersuchen“; siehe KI-Fingerabdruck.

**Tonprofile** – siehe KI. **Andere Werte zu bestimmten Uhrzeiten** (Zeitprofile) – z. B. nachts empfindlicher, allgemein oder je Gerät.

### Muster ausfiltern

Bekannte, wiederkehrende Geräusche (Uhrschlag zur vollen Stunde, Kühlschrank, Heizung, Wecker, eigener Fernseher) lassen sich **in der Anzeige** ausblenden. Ein Muster verbindet beliebig viele Bedingungen:

| Bedingung | Beispiel |
|---|---|
| Gerät | nur das Mikrofon im Flur |
| Art oder Tonprofil | „Signal“, Tonprofil „Kühlschrank“ oder „Hintergrund (eigenes Gerät)“ |
| Uhrzeit von–bis, Wochentage | 06:00–06:20, Mo–Fr (auch über Mitternacht) |
| Dauer von–bis, Spitze von–bis (dBFS) | 2–8 s, −45 bis −30 dBFS |
| Abstand zur Schwelle | 0 bis 4 dB über der Schwelle |
| Wiederholung | alle 60 Minuten ab Minute 0, ± 2 Minuten (= jede volle Stunde) |
| Zustand in Home Assistant | nur wenn die Regel „Fernseher an“ gerade greift |

Dazu ein Name und eine Farbe. **Anlegen:** hier mit **＋ Muster anlegen** oder in der Ereignisliste über **⋮ → Als Muster ausfiltern …** – dann sind Gerät, Art, Uhrzeit (± 15 Min.), Dauer und Spitze aus der Störung vorbelegt. Vor dem Speichern steht, wie viele Störungen der letzten 30 Tage das Muster träfe, mit Beispielen.

**Wirkung:** Passende Störungen fehlen in Listen, Zählern, Kacheln, in den Kachel-Sensoren für Home Assistant und sind in Grafiken nur noch blass zu sehen. Die Anzahl sagt dann z. B. „(12 nach Muster ausgefiltert)“. Der Schalter **⊘ ausgefilterte zeigen** über den Bereichen holt sie zurück, gekennzeichnet mit dem Namen des Musters.

**Gespeichert wird nichts anders:** Die Muster liegen in `muster.json` (in der Sicherung enthalten). `log.csv`, Tagesaufzeichnung, Prüfsummen und Ereignisdateien bleiben unverändert – ein Muster löschen zeigt alles wieder wie vorher.

**Lärmprotokoll, Ausdruck und Export** enthalten standardmäßig **alle** Störungen, ausgefilterte mit dem Vermerk „nach Muster … ausgefiltert“ (in der CSV-Spalte `nach_muster_ausgefiltert`). Mit **nach Muster ausgefilterte weglassen** fehlen sie, und oben steht, welche Muster wie viele Störungen entfernt haben.

> **🔒 Pro:** Ein Muster ist frei, mehrere gehen mit GLighter Pro. Ohne Pro bleiben weitere Muster gespeichert, es gilt nur das erste.

### Zeiten & Pausen

- **Wann wird überwacht?** – Überwachen ab / bis (beide leer = rund um die Uhr, über Mitternacht möglich). Außerhalb davon wird nichts gezählt; über die Anzeige oben lässt sich trotzdem erfassen.
- **Ruhezeit** – Ruhezeit ab / bis (üblich 22:00–6:00), Sonntag ganztägig Ruhezeit. Notizen und Störungen in der Ruhezeit bekommen 🌙.
- **Andere Werte zu bestimmten Uhrzeiten** – siehe oben (Zeitprofile).
- **Regeln (Home Assistant)** – eigener Reiter **Regeln**, siehe Home Assistant.

### Speichern & Sicherung

### Was wird gespeichert?

| Einstellung | Bedeutung |
|---|---|
| Umfeld vor und nach der Störung (s) | so viele Sekunden vor und nach der Störung werden beim Ansehen gezeigt |
| Tagesaufzeichnung mit Ebenen | tief/mittel/hoch, Frequenz für den ganzen Tag (+1–2 MB pro Gerät und Tag) |
| Tagesaufzeichnung mit Spektrum | Spektrogramm für jeden Moment (+3–8 MB pro Gerät und Tag) |
| Bei einer Störung alle Geräte mitspeichern | die anderen Geräte speichern für denselben Zeitraum eine Lärmspur (kein Ton) – zum Vergleich der Räume |

### Echten Ton speichern (nicht empfohlen)

Standard **aus**. Eingeschaltet wird zu jeder Störung zusätzlich eine WAV-Datei gespeichert. **Ton nur ohne erkannte Stimmen** (empfohlen) verhindert das Speichern, sobald die KI irgendwo Stimmen erkennt. Lies vorher Rechtliches.

### Video

Video-Breite, Bilder pro Sekunde, Videoqualität (für IP-Kameras und Handys).

### Speicherort

**Ordner für Lärmspuren** – leer = Standard. Nur ändern, wenn neue Lärmspuren woanders liegen sollen (z. B. `/media/gaslighter`). Für eine Kopie auf dem NAS ist die **tägliche Sicherung** gedacht, nicht dieser Ordner.

### Aufbewahren & automatisch löschen

**Alte Aufnahmen automatisch löschen** und **Löschen nach (Tagen)** – aus = es wird nie etwas gelöscht. Mit tägliche Sicherung wird nur gelöscht, was geprüft im Ziel liegt.

### Sicherung

**Sicherung herunterladen / einspielen (ZIP)** – immer kostenlos. **Tägliche Sicherung** auf Netzlaufwerk, NAS oder USB (Pro). Beides siehe Sicherung.

### Allgemein

- **Sprache** – Deutsch, Englisch oder wie der Browser.
- **„Auto“-Höhe im Live-Bild** – „mit Schwelle“ (Standard): Die Schwelle ist immer im Bild. „nur Messwerte“: enger um Pegel und Hintergrund.
- **Mausrad im Diagramm** – „nur mit Strg“ (Standard): Das Mausrad scrollt die Seite, zum Zoomen Strg gedrückt halten. „Zoomt immer“: wie früher, das Mausrad zoomt direkt.
- **Protokoll & Notizen** – **Störungen zusammenfassen bei bis zu (s) Abstand** (Gruppen in der Liste), **Notiz gehört zur Störung, wenn bis zu (min) danach**.
- **GLighter Pro** – siehe Pro.
- **GReport (Notizen-App)** – GReport ist der Notiz-Teil als eigene App (z. B. fürs Handy oder für Mitbewohner). Ist GReport installiert, erscheinen seine Notizen mit Pro automatisch hier – an den Störungen, im Verlauf und im Lärmprotokoll, markiert mit „GReport“. Geändert werden sie in GReport.
- **Zurücksetzen** – siehe Zurücksetzen.
- **Diagnose** – Angaben zu Mikrofon und Soundkarte für die Fehlersuche.

## 12. Rechtliches und Datenschutz

> **Keine Rechtsberatung.** Die Rechtslage unterscheidet sich je nach Land. Im Zweifel einen Anwalt oder den Mieterverein fragen.

### Was gespeichert wird

- **Messwerte**: Pegel, Hintergrund, Schwelle, Frequenzbänder (23 Terzbänder) in 125-ms-Schritten. Aus dieser Auflösung lässt sich nach Forschungsergebnissen keine verständliche Sprache zurückgewinnen.
- **KI-Ergebnisse** und **KI-Fingerabdruck**: Zahlen, die beschreiben, wie es klingt – kein Ton, nicht zurückverwandelbar.
- **Deine Notizen**, Listen, Tonprofile, Zustände aus Home Assistant.
- Alles bleibt **auf deinem Rechner**. Es gibt keine Cloud und keine Übertragung an Dritte.

### Kein Ton, keine Spracherkennung

Ton liegt nur kurz im Arbeitsspeicher (Live-Anzeige, Erkennung) und wird laufend überschrieben. Bei Stimmen wird nur die **Art** erkannt, nie der Inhalt – eine Spracherkennung gibt es bewusst nicht.

> **Achtung § 201 StGB:** Das Aufnehmen des nichtöffentlich gesprochenen Worts kann strafbar sein, wenn es nicht nur zufällig geschieht. Bei einer Daueraufzeichnung Richtung Nachbarschaft ist das vorhersehbar. Deshalb ist „Echten Ton speichern“ standardmäßig aus und erst nach einem Hinweis einschaltbar. Heimliche Tonaufnahmen sind vor Gericht meist nicht verwertbar. Tonaufnahmen kommen nie ins Lärmprotokoll.

### Video

Kameraaufnahmen in Wohnungen können nach § 201a StGB problematisch sein. Nur eigene Räume filmen, keine fremden Personen, nicht in fremde Wohnungen oder den Hausflur.

### Aussagekraft

- Pegel sind **dBFS** (relativ zur Soundkarte), keine geeichte Messung in dB(A).
- Überzeugend ist ein Protokoll, das **regelmäßig** geführt wird, **nachvollziehbar** ist (Uhrzeit, Dauer, Art, Auswirkung, Zeugen) und **unverändert** ist (Datenkette).
- Eigene Notizen („aufgewacht“, „Kind geweckt“) und Zeugen machen den Unterschied.

### Was die Aufzeichnung belegt und was nicht

> **Keine Rechtsberatung.** Die folgenden Punkte sind sachliche Hinweise aus veröffentlichten Entscheidungen und Fachbeiträgen. Sie versprechen keinen Erfolg vor Gericht. Für den Einzelfall eine Anwältin oder einen Anwalt, den Mieterverein oder eine Opferberatung fragen.

**Belegt werden kann:** wann es wie lange und wie laut (relativ, dBFS) war, wie oft und zu welchen Uhrzeiten – über Wochen und Monate, auch dass an ruhigen Tagen gemessen wurde. Dazu, dass die Tagesaufzeichnung seither unverändert ist (Prüfsummen).

**Nicht belegt werden kann:**

- **woher** ein Geräusch kommt und wer es verursacht – die Erkennung „Klopfen“ sagt nicht, aus welcher Wohnung,
- **wie laut in dB(A)** – das Mikrofon ist nicht kalibriert: Werte sind Indizien und ersetzen kein Gutachten,
- dass die **Geräuschart** stimmt, solange sie ein „Vorschlag der Erkennung“ ist – prüfe sie und bestätige oder korrigiere sie mit einem Klick in der Ereignisliste. Deine Bestätigung liegt getrennt (`bestaetigt.json`), die Einschätzung der Erkennung bleibt gespeichert.

**Was hilft:** Zeugen (Nachbarn, Hausverwaltung, Polizei), zeitnahe Notizen mit Zeitpunkt, Art, Intensität, Dauer und Häufigkeit, Meldungen mit Datum und Vorgangsnummer. In strittigen Fällen holen Gerichte eigene Gutachten ein – die Aufzeichnung kann zeigen, wann sich eine Messung lohnt.

**Prüfsummen** zeigen, dass die Daten seit der Aufzeichnung nicht verändert wurden; sie sind keine elektronische Signatur. Digitale Daten haben vor Gericht keine Echtheitsvermutung – lege deshalb Rohdaten (CSV) und Prüfsummen bei (Beweispaket, siehe Drucken).

### Kurze Hinweise in der App

Mit **💡 Hilfe anzeigen** (⚙ Einstellungen → Allgemein) erscheinen an einigen Stellen kurze Hinweise. Jeder lässt sich mit ✕ einzeln ausblenden; „Hilfe anzeigen“ aus blendet alle aus. **Warum?** nennt die Quelle.

| Wo | Hinweis | Quelle |
|---|---|---|
| Geräte (Einrichtung) | An einem festen Ort messen und eintragen, ob das Fenster offen oder geschlossen ist. | AG Wolfratshausen 5 C 274/20 |
| Ereignisliste | Erkannte Geräuscharten prüfen und bestätigen oder korrigieren; die Erkennung zeigt nicht, aus welcher Wohnung es kommt. | LG Berlin II 56 S 100/23 WEG |
| Aufzeichnung, Live | Auch an ruhigen Tagen messen – eine lückenlose Zeitreihe zeigt Häufigkeit und Muster glaubwürdiger. | BGH VIII ZR 1/16 Rn. 14; § 238 Abs. 2 StGB |
| Export, Lärmprotokoll | Messwerte als Indiz weitergeben und bei Streit ein Gutachten anregen. | AG München 472 C 18927/16; OLG Celle 4 U 199/09 |
| Export, Lärmprotokoll | Rohdaten (CSV) und Prüfsummen beilegen. | § 371 ZPO; Irskens, EDVGT 2024 |
| Allgemein | Keine heimlichen Ton- oder Videoaufnahmen von Nachbarn ergänzen. | BGH VI ZR 1370/20; BVerfG 1 BvR 1611/96; AG München 173 C 11834/23 |
| Allgemein | Nicht mit Gegenlärm antworten, sondern dokumentieren und den Rechtsweg gehen. | AG München 173 C 11834/23 |

## 13. Fehlerbehebung und häufige Fragen

### „Das Signal ist sehr leise“

Der Hintergrund liegt sehr tief (unter −85 dBFS). Mikrofon an der richtigen Buchse? Mikrofon-Lautstärke in ⚙ → Geräte → Mikrofon erhöhen oder die Verstärkung des Geräts anheben.

### „Die Schwelle liegt an der Untergrenze“

Es ist so leise, dass die Schwelle nicht tiefer darf. Das ist gewollt, wenn sehr leise Geräusche nicht zählen sollen. Sonst die Untergrenze in ⚙ → Erkennung senken.

### Zu viele oder zu wenige Störungen

- Zu viele: „Wie viel lauter als normal?“ erhöhen oder „Mindestdauer“ auf 40–60 ms.
- Zu wenige: Abstand verringern, Untergrenze senken.
- Eigener Fernseher zählt mit: Tonprofil als **Hintergrund** anlegen oder eine Home-Assistant-Regel „festhalten“ bzw. „pausieren“.

### Spalte „Art (KI)“ zeigt nichts

- „Die KI-Erkennung ist ausgeschaltet“: ⚙ → Erkennung → **Geräuschart erkennen** einschalten.
- „KI-Modell nicht gefunden“: das Add-on einmal mit der **vollen Zip** neu installieren (Update-Zips enthalten das Modell nicht).
- „kein Fingerabdruck an dieser Stelle“: An dieser Sekunde wurde nichts gespeichert (zu leise oder Rechner ausgelastet). Prüfe in ⚙ → Erkennung, ob der Fingerabdruck läuft.

### Lücke im Verlauf

Schraffiert = das Add-on lief nicht. Die Ursache steht in Protokolle unter „Nicht aufgezeichnet …“. Kommentar setzen: auf die Schraffur klicken. Siehe Unterbrechungen.

### Handy verbindet nicht

- Port 18443 freigegeben (Add-on → Netzwerk)? Zertifikatswarnung bestätigt?
- Bildschirm an lassen oder die App „IP Webcam“ als Stream nutzen.
- Neuer Link: in der Geräte-Karte den QR-Code neu erzeugen.

### Update wird nicht übernommen

Der Ordner muss als `\\homeassistant\share\gaslighter_update\gaslighter\…` liegen. Nach 10–20 s ohne weitere Änderungen startet das Programm neu. Die Version steht oben neben dem Namen.

### Wo liegen die Daten?

`/share/gaslighter` (über Samba `\\homeassistant\share\gaslighter`): `log.csv`, `clips/` (Tagesaufzeichnung in `clips/tag/`, KI in `clips/ki/`, Notizen, Listen, Profile), Einstellungen und Geräte in `/data`.

## 14. GLighter Pro

GLighter ist kostenlos. **Aufzeichnung, Live-Ansicht, Protokolle, Lärmprotokoll zum Drucken, Export (`log.csv`, Notizen) und das Erstellen einer Sicherung** sind immer frei – ohne Zeitlimit und ohne Werbung.

Die Jahreslizenz **GLighter Pro** schaltet zusätzlich frei:

| Funktion | Ohne Pro | Mit Pro |
|---|---|---|
| Import einer Sicherung | einmal kostenlos (z. B. Umzug) | beliebig oft |
| Erweiterte Einstellungen der Erkennung (Reiter „Erkennung“ → „Wann gilt etwas als Störung?“) und 🎯 Schwelle automatisch einstellen | nur ansehen, Standardwerte | frei einstellbar, auch je Gerät und in Zeitprofilen |
| Externe Geräte: Handy im Browser, Handy-App / Stream-URL, IP-Kamera | gesperrt | bis zu 8 zusätzliche Geräte |
| Handy als Bewegungsmelder (Erschütterung, Bewegung im Bild) | gesperrt | ✔ |
| 📊 Eigene Statistiken selbst einstellen (Statistiken) | Vorlagen | frei einstellbar |
| ⊘ Muster ausfiltern (Muster) | 1 Muster | bis zu 30 Muster |
| Tägliche Sicherung auf Netzlaufwerk/NAS/USB und „Platz sparen“ (Sicherung) | „⬇ Sicherung herunterladen“ von Hand | jeden Tag automatisch, geprüft |

Das Server-Mikrofon (am Home-Assistant-Rechner) funktioniert immer ohne Pro.

### Kaufen

⚙ Einstellungen → Allgemein → **GLighter Pro** → **🛒 Pro kaufen** öffnet die Seite von GLighter auf gsimulations.de. Die Lizenz gilt **1 Jahr ab Kauf** für **1 Home-Assistant-Installation**. Sie verlängert sich **nicht** automatisch – es gibt kein Abo. Nach dem Kauf kommt der Lizenzschlüssel per E-Mail.

### Schlüssel eintragen

1. ⚙ Einstellungen → Allgemein → **GLighter Pro**.
2. Den Schlüssel aus der E-Mail vollständig einfügen. Er beginnt mit `GL1-`; Leerzeichen und Zeilenumbrüche stören nicht.
3. **🔑 Aktivieren**. Danach steht dort „Pro aktiv – gültig bis …“.

Der Schlüssel wird **ohne Internet** geprüft – GLighter sendet nichts an G-Simulation. Er wird in der Sicherung **nicht** mitgespeichert; nach einer Neuinstallation einfach wieder eintragen.

An gesperrten Stellen steht **🔒 Pro**. Ein Klick darauf erklärt die Funktion und bietet „Pro kaufen“ und „Schlüssel eintragen“ an.

### Ablauf und Verlängern

14 Tage vor dem Ablauf erscheint oben einmal ein Hinweis mit „Verlängern“. Nach dem Ablauf läuft alles Kostenlose weiter, aufgezeichnete Daten bleiben vollständig erhalten:

- Externe Geräte nehmen nicht mehr auf (sie bleiben eingerichtet und laufen mit einem neuen Schlüssel sofort weiter).
- Die erweiterten Einstellungen behalten ihre Werte, lassen sich aber nicht mehr ändern.
- Weitere Importe brauchen wieder Pro.

Zum Verlängern eine neue Lizenz kaufen und den neuen Schlüssel eintragen.

### Umzug auf einen neuen Rechner

Sicherung auf dem alten Rechner herunterladen, GLighter auf dem neuen installieren und die Sicherung einspielen – der **erste Import ist kostenlos**. Danach den Pro-Schlüssel wieder eintragen.
Damit auch der Schlüssel der Prüfkette und die Zugangsdaten mitkommen, die Umzugs-Sicherung mit Kennwort verwenden.

## 15. Glossar

| Begriff | Bedeutung |
|---|---|
| **dBFS** | Pegel relativ zum Maximum der Soundkarte (0 dBFS). Immer negativ: −80 sehr leise, −50 Gespräch, −20 sehr laut. Keine geeichten dB(A). |
| **Hintergrund** | der gelernte „normale“ Pegel, aus den leisesten Momenten der letzten Zeit |
| **Schwelle** | ab diesem Pegel zählt es als Störung; passt sich standardmäßig dem Hintergrund an |
| **Störung / Ereignis** | ein Ausschlag über der Schwelle (endet 0,5 s darunter, längstens 5 min) |
| **Spitze** | der höchste Pegel innerhalb von 125 ms bzw. einer Störung |
| **Gruppe** | aufeinanderfolgende Störungen derselben Art mit kurzer Pause dazwischen |
| **Tagesaufzeichnung** | durchgehende Messwerte des ganzen Tages je Gerät (`clips/tag/`) |
| **Lärmspur** | Messwerte einer Störung mit Umfeld (Pegel, Frequenzbänder), kein Ton |
| **Spektrogramm** | Frequenz über Zeit, hell = laut; unten tief, oben hoch |
| **Terzbänder** | 23 Frequenzbereiche von 50 Hz bis 8 kHz |
| **Ebenen** | zusätzliche Kurven: tief/mittel/hoch, dominante Frequenz, Klangschwerpunkt |
| **Tonprofil** | eigene, angelernte Geräuschart (🧩) |
| **Benannter Bereich** | von Hand markierter und benannter Abschnitt (🏷), Lernbeispiel |
| **KI-Fingerabdruck** | Zahlen der KI je Sekunde, beschreibt den Klang, kein Ton (ⓕ) |
| **Prüf-Schwelle** | frei gewählter Wert zum nachträglichen Zählen von Spitzen, nur Anzeige |
| **Datenkette** | SHA-256-Prüfsummen je Minute, machen Änderungen sichtbar |
| **Erfassungszeit** | eingestellte Überwachungszeit (z. B. 22–6 Uhr) |
| **Ruhezeit** | Zeitraum für 🌙 im Protokoll (z. B. 22–6 Uhr, Sonntag) |
| **Einpegeln** | Verstärkung der Geräte angleichen, damit Pegel vergleichbar sind |
| **Festhalten** | Home-Assistant-Regel, die Zustände mitschreibt, ohne zu pausieren |


---

# English

## 1. Quick start in 5 minutes

GLighter listens continuously and writes a **noise log**: when it was how loud, for how long and what kind of sound – with checksums so nobody can change the data unnoticed. **No sound is stored**, only measurements.

### 1. Connect a microphone

- Plug a USB microphone (or one on the sound card) into the Home Assistant computer. The entry “Server microphone” already exists.
- More rooms: add phones as microphones, see Devices.
- If the **Level** tile shows a value and the curve moves when you knock, sound arrives. If the blue note “The signal is very quiet” appears, raise the microphone volume (⚙ Settings → Devices → Microphone) or pick the right input.

### 2. Check the threshold

A **disturbance** is counted when the level rises above the **threshold** (orange dashed line). Default: “Adapts, with limits” – the threshold sits 10 dB above the normal background, but never below −95 and never above −30 dBFS.

- A loud knock should clearly cross the line and be marked red.
- Too many small things counted: raise “How much louder than normal?” (e.g. 12 dB). Too few: lower it.
- Details: Settings → Detection.

> **Tip:** Levels are **dBFS** – relative to the sound card, therefore negative (−80 very quiet, −20 very loud). What matters is the distance to the background, not the absolute value. See Glossary.

### 3. Level-match several microphones (optional)

To compare devices: ⚙ Settings → Devices → **Level-match devices**. Put all microphones side by side, 5 s of quiet, then a steady sound. Afterwards all devices show the same value for the same sound.

### 4. Look at the first disturbance

- In the **Live** tab, “Events today” is at the bottom. A click opens the disturbance with chart, spectrogram and detected type.
- The **Logs** tab shows whole days and weeks, the history of all devices below each other and the list of all disturbances.
- Write down what you hear right now under **📝 Note now** (“steps upstairs”, “bass”) – the note is attached to the last disturbance automatically.

### 5. Backups and updates

- Regularly download a backup under ⚙ Settings → Storage & backup → **Download backup**. See Backup.
- Updates without a recording gap: copy the new folder to `\\homeassistant\share\gaslighter_update\`. See Updates.

> **Important:** GLighter is a memory aid and documentation, not a calibrated dB(A) measurement. For landlords, property managers or authorities what counts most is: regular, traceable, with your own notes. See Noise log.

## 2. Live view

The **Live** tab shows what is happening now: tiles with current values, the chart of the last minutes, the spectrogram and today's events.

### Header

| Element | Meaning |
|---|---|
| **LIVE** | The view follows the present. After rewinding, go back to live here. |
| **Quiet / DISTURBANCE** | State of the selected device. Red = currently above the threshold. Outside the monitoring time you can “record anyway” here. |
| **Stop recording** | Pauses recording (logged in `aufzeichnung.csv`). On a phone in the ⋯ menu. |
| **🌓 Auto / ☀ / 🌙** | Light, dark or like Home Assistant. |
| **⚙ Settings** | All settings, see Settings. |

### Device bar and tiles

The bar below the note shows all devices with today's number of disturbances. Tap to select. With several live devices the view **rotates** automatically (duration via ⚙ in the bar).

- **Level** – current peak level.
- **Background** – the learned “normal” level.
- **Threshold** – from here it counts as a disturbance; below it says how it is calculated.
- **Sound now** – what the AI hears right now (only with sound type detection on).
- **Events** – disturbances today and in total.

### The chart

- **Blue area** = level, **grey line** = background, **orange dashed** = threshold, **red** = disturbance, dotted coloured lines = your own reference lines (e.g. “TV −70 dB”).
- **Level trace / Loudness bars** switches the display.
- **🗂 Layers** toggles curves: background, threshold, low/mid/high, dominant frequency, spectral centroid.
- **Time window** and **− / +** change the time shown; **Auto** fits the height.
- Below, the **spectrogram**: frequency over time, bright = loud. Low sounds (bass, footfall) are at the bottom, voices and dishes higher up.

### Controls

| Computer | Phone / tablet |
|---|---|
| Ctrl + mouse wheel or touchpad pinch = zoom time (the wheel alone scrolls the page; change under ⚙ → General → “Mouse wheel on the chart”) | spread two fingers = zoom time |
| Drag or swipe sideways = move in time | swipe horizontally = move, vertically = scroll the page |
| Shift + drag = select a range and zoom in | − / + |
| Shift + wheel or Ctrl + wheel over the dB labels = zoom height (bottom-aligned) | “Auto” |
| Double click = back to live | Double tap = back to live |
| Hover over a disturbance = details | Tap a disturbance = details |

**With the keyboard:** Tab to the chart (blue frame). Then **+ / −** zoom time, **← / →** move in time, **↑ / ↓** height, **0** reset, **End** back to live. Screen readers read the current level, threshold and state.

Further back than the last 10 minutes the chart shows the **whole day** from the day recording (time window 1 h, 6 h or “Today”).

### 📝 Note now

For what you hear right now – just start typing or tap tags (upstairs, downstairs, knocking, bass, woke up …).

- **Without a time of its own**: if there was a disturbance shortly before (setting “Assign note”, default 5 min), the note belongs to it. The bar shows beforehand where it goes.
- **still going**: the note gets a period from the first input until saving.
- **From / to and witness** are always shown right in the area; leave them empty for “automatic” (time at saving).
- **Only tags, no text?** GLighter builds a sentence from them when saving, e.g. “Clear footsteps in the stairwell”. You can edit it later.

### Custom quick select

- **＋ Custom** at the end of the buttons: enter a name (e.g. “washing machine”, “neighbour 2nd floor”) → **Create**. The button (★) then appears in all note fields, also when detached, and in the notes filter.
- **Right-click or long-press** a button to open “Manage quick select”: **rename** or **delete** your own, **hide and show** built-in ones. Old notes keep their label.
- **Learning:** if you type a word yourself more often (3× or more), GLighter suggests it as a button (💡). It is only created when you press **＋**; **✕** means “stop suggesting”.
- **Order:** what you press most often comes first – on a phone these are the first 6.
- Your buttons are stored in `clips/schnellwahl.json` and are included in the backup (ZIP).

**Detach (Pro):** **⧉** next to the title detaches the note area into its own small window. In Chrome and Edge it stays on top of other programs (e.g. over a game or film), otherwise it is a normal extra window. **Bring back** or closing the window puts it back.
- Ctrl + Enter saves. On a phone the bar starts collapsed.

### 🏷 Mark range

1. Tap “🏷 Mark range” – a hint with **Done** appears above the chart.
2. Drag across the range horizontally (0.15 s to 2 min).
3. Tap an **existing type** (sound profile 🧩 or named range 🏷) or enter a new name – same name = same type, the AI learns from it. See AI.

### Events today

The list at the bottom shows all disturbances of the day (all devices or the selected one). A click opens the disturbance, see Event window. Choose columns via ⚙. On a phone the entries appear as cards.

**Visible range only** (default: on): the table only shows what the chart above currently shows. It follows live, zooming and panning. Off: all events from the start of the chart.

**Column widths:** if you drag a column edge in the header to make it wider or narrower, GLighter remembers the width (on the server, the same for every browser). Reset via **▦ Customise layout** → **＋ Add section** → **Reset table column widths**.

### Arranging and own tiles

The Live view also consists of sections (note, live chart, events). With **▦ Customise layout** you move them, change their width, rename or hide them – with the mouse, with **↑ / ↓** (also on phones) or with the keyboard. **📊 ＋ Tile** adds a tile, e.g. “Disturbances today” as a big number. Details under Logs → Customise layout and Tiles.

## 3. Logs

The **Logs** tab shows a period completely: summary, week strip, history of all devices, statistics and the list of all disturbances.

### Period and filters

- **Monitoring time** (the set monitoring hours, e.g. 22–6), **Today**, **Yesterday**, **7 days**, **30 days** or **From–to**. ‹ › moves by a whole period.
- **Source / device**, **Type** (multiple choice, e.g. knocking + footsteps) and **List** filter everything below. Devices that no longer exist but still have data are listed as “(former)”.
- **🖨 Noise log** creates the noise log for period, device and list, **⬇ Image (SVG)** an image. See Printing.

### Arranging sections (dashboard)

Live and Logs consist of **sections** (overview, interruptions, history, events by hour, per day, events in the period, notes and motion, sensors in the period). Each section has a bar at the top:

- **▾ / ▸** collapses and expands (also double-click on the bar).
- **✕** hides it. Insert it again via **▦ Customise layout** → **＋ Add section**.
- **⌖ visible range only** (events, sensors): only shows what is currently visible in the history – drag e.g. 20:00–22:00 in the history and the table or list shows only that time.

### ▦ Customise layout (designer)

**▦ Customise layout** switches Live and Logs into edit mode – much like editing a dashboard in Home Assistant:

- **Move:** drag the ⠿ handle or use **↑ / ↓** in a section's bar to move it one place up or down.
- **Width:** drag the left or right edge (e.g. two sections side by side). The height follows the content.
- **✎ Change title:** your own name for the section or tile. Leave it empty to restore the original.
- **▾ / ▸** collapses and expands, **✕** takes the section out of the view.
- **＋ Add section** opens the library: all sections of this view (shown or hidden) to insert or remove, plus **new tiles** and **ready-made templates** (see below). You can also reset the remembered **table column widths** there.
- **↺ Reset** restores the default arrangement of this view after asking. **Done** ends editing.

**With the keyboard:** in edit mode pick a section with Tab (it gets a clear frame), then

| Key | Effect |
|---|---|
| ↑ / ↓ | one place up / down |
| ← / → | one column left / right |
| Shift + ← / → | narrower / wider |
| Shift + ↑ / ↓ | collapse / expand |
| F2 | change title |
| Delete | remove (after asking) |

Screen readers read the name of every section and announce the new position after each change.

**On phones** all sections are stacked. Change the order in edit mode with **↑ / ↓** – the arrangement on the PC is kept.

**Stored on the server:** arrangement, widths, collapsed and hidden sections, your own titles and the hand-dragged **table column widths** are kept in `layout.json` next to `sources.json`. PC, tablet and phone therefore show the same. If the server had no arrangement yet, GLighter takes the one saved in the browser the first time it opens. `layout.json` is part of the backup (ZIP) and comes back with “Take over settings and devices”. The layout never changes data.

“Sensors in the period” is hidden at first: sensor events (“as event”) are already in the table, “only record state” (e.g. TV) appears as a 📡 hint on every disturbance that falls into that time.

### 📊 Tiles (custom statistics)

**📊 ＋ Tile** (above the sections, in Live and Logs) or, in edit mode, **＋ Add section** → **New tile** adds a tile as its own section – move, widen, rename, collapse and hide it like the others.

**Kinds of tiles:**

- **Number** – big number with a label, e.g. disturbances today, disturbances in the last 7 days, average peak.
- **Trend** – line over days, weeks or months.
- **Bars** – e.g. per hour, weekday or day.
- **List** – the most frequent types, devices, sensors or note buttons (3 to 20 entries).
- **Table** – all values to sort and filter (like the other tables).

**Configuring:**

- **Templates (free for everyone):** e.g. “Disturbances today”, “Disturbances, last 7 days”, “Average peak (7 days)”, “Disturbance time today”, “Most frequent types (7 days)”, “Disturbances per device (30 days)”, “Trend per day (30 days)”, “Disturbances per hour (night)”, “Types compared”, “Trend per week”, “Per weekday”, “Total duration per day”, “Sensors per day”, “Notes by button”. A template goes into the view where you click it.
- **Configure your own (Pro):** *name*, *what to count* (disturbances – also just one type or sound profile –, sensors, notes with a quick-select button), *measure* (count, total duration, avg or highest peak), *split by* (hour, weekday, day, week, month, type, device, note button, sensor), *display* (number, line, bars, list, table), *period* (selected period, today, last 24 h / 7 / 30 / 90 / 365 days or a **custom period** from–to), *device*, **thresholds** (*only from peak* in dBFS, *only from duration* in seconds) and *night only / quiet hours only / weekend only*. The preview shows the result right away.
- **Clicking a bar**, a list entry or a table row (also with Enter or Space) filters the event table to it; click again or **✕** to remove the filter.
- **⚙** configures or deletes. Tiles only read – they never change data. Stored in `clips/statistik.json`, included in the backup.
- Every tile also appears **in Home Assistant** as a sensor (see Home Assistant → Tiles).

### Summary and week strip

The ring shows how much of the time was **undisturbed**. Next to it: number of disturbances, disturbed time, longest quiet, recorded time and the loudest event.

The **circles** below are the last 7 nights or days. Tap to choose a day; the newest one always stays visible. Below are the **data chain** (checksums) and interruptions, see Interruptions.

### History

The history shows the devices below each other for the same period. Per row choose **device** and **display** (level trace, loudness bars, spectrogram) and toggle layers. “＋ Add row”, ↑ ↓ ✕ arrange the rows; the handle below each row changes its height.

- While the day is still running the time axis ends at **now** – the newest data is on the right and the history grows every minute.
- With more than 2 days it shows minute values, zooming in brings back the 125 ms values.
- At the top the AI marks the detected type of each disturbance in its colour; **blue** = on according to Home Assistant (e.g. TV).
- **Hatched** = not recorded (e.g. power cut). Click it to add a comment, see Interruptions.

Controls as in the live view: wheel/two fingers zoom, drag a range, when zoomed drag or ‹ › to move, Shift + wheel for the height, double click or “Whole period” for everything. On a phone, test threshold, print and mark range are under **⋯ Tools**, the layers behind **🗂 Layers**.

### 📏 Test threshold

With the test threshold you check afterwards which peaks were above a freely chosen value – e.g. “How often was it above −50 dB?”

1. Tap “📏 Test threshold”, enter a value or drag the purple line in the history.
2. Per device you see number and duration of the peaks in the visible section (from the 125 ms values; less than 0.5 s apart = one peak).
3. “List of peaks” shows each peak with time, duration, height, distance, **Type (AI)** and **Sound profile**. A click jumps there in the history.

The type comes from the disturbance if the peak lies in one, otherwise from the stored **AI fingerprint** (ⓕ). Possible notes: “no fingerprint at this spot”, “no AI fingerprint on this day”, “not checked” (more than 2000 peaks). See AI.

> The test threshold is **display only**. Stored data, disturbances and checksums stay unchanged. It is printed along when printing.

### Events in the period

- **Groups** combines disturbances of the same type (at most “Group: max. pause” apart), **All single** shows each.
- **Sorting:** click a column header (start, duration, peak, threshold, background); click again to reverse. The sort order is remembered in the browser.
- **Filter with multiple choice:** under **Source / device** and **Type** click one or more entries, e.g. only “door sensor vibration” and “voice”. The line above the table counts disturbances and sensor events separately.
- **Sensor events** (Home Assistant rule “as event”, phone as motion sensor) are sorted in by time with an orange edge; ✎ = note.
- On narrow screens ⊕ at the start of a row expands the remaining columns.
- Click = jump there in the history, double click or ▶ = open the event, ⋮ = more actions (download noise track, re-evaluate, delete).
- Select, then **Add to list** or delete. Deleted entries are kept in a recycle bin for safety; the day recording stays.
- **📝 All notes**, **🔎 Check a sound** (analyse your own audio file, not stored), **🧩 Profiles & re-scan**, **Download log.csv**.

### Confirm or correct the sound type

The detected type is shown as a coloured box in the **Type** column. Until you confirm it, it is a **“suggestion of the detection (confidence x %)”** – that is also how it appears in the noise log, the print and the raw data. **Click the box** (or ⋮ → Confirm sound type): **Correct** confirms the suggestion, another type corrects it, **Withdraw confirmation** undoes it. Your confirmation is kept in a separate file (`bestaetigt.json`); the detection's estimate, `log.csv` and the day recording stay unchanged. The detection says nothing about which flat a sound comes from.

### Filter out known sounds

⋮ → **Filter out as pattern …** creates a pattern from the disturbance (device, type, time, duration and peak prefilled, with the preview “matches N disturbances of the last 30 days”). Filtered disturbances are then missing from the list; the count names them (“N filtered out by pattern”), **⊘ show filtered** brings them back with a mark.

### Notes in the table

Every note you create appears as its own row **“📝 Note”** in the table, with time (from–to), device, tags, witness and text. If a disturbance lies in the note’s period, they are linked: the note row shows **“🔗 Disturbance …”** (click opens it) and the disturbance row shows the note text. **✎** edits the note. The filter **“📝 Notes”** hides or shows all note rows. Notes are not counted as disturbances.

### Log lists

Your own lists such as “bathroom” or “garden” collect disturbances in addition to the full list – by hand (“Add to list”, or in the event under “Lists”) or automatically per device and time (⚙ Settings → Devices → device card → **Log lists**). Each list has its own note and its own noise log.

## 4. Event window

Double-clicking a disturbance opens all details.

### Key figures

Duration, peak, threshold, background, track (period shown) and:

- **Above the loudest before** or **Quieter than the loudest before** – distance of the peak to the loudest level of the time before (disturbances not counted). Shows that the disturbance was louder than e.g. a running TV.
- States from Home Assistant (e.g. “TV: off”, volume), see Home Assistant.

### Chart

- **Red** = the disturbance, **red lines** = start and end, light red = pre- and post-roll.
- **Dashed boxes** = suggestions from your sound profiles (“dishes clattering? 100 %”). Suggestions outside the disturbance are paler. Tap: ✓ Correct / ✕ Wrong.
- Below, the **spectrogram**; with several devices the **device comparison** (peak per device, distance to the loudest).
- **▶ Show playback** runs a pointer across it in real time (no sound).

### Type, profile and lists

- **Type (AI)** with confidence in %. “Wrong? Correct it” sets the type by hand – your correction wins. **🔎 Re-evaluate** analyses again (needs the stored AI fingerprint).
- **🧩 Profile**: the most similar sound profile. **✓ Confirm** or choose another – both become a new learning example.
- **Lists**: add the disturbance to a log list or remove it.

### Notes and named ranges

- **📝 Note at …** (or key N, long press on the chart) adds a note at exactly this point, with quick tags and witness.
- **🏷 Name a range**: drag horizontally in the chart and choose a name. See AI → Learning.
- **Note on this event**: a free text field per disturbance, saved automatically.

## 5. AI: sound types and sound profiles

GLighter recognises the **type** of a sound with a small AI that runs entirely on your Home Assistant computer (YAMNet, no cloud). In addition the app learns your own **sound profiles**.

### Built-in detection

Without any training the AI assigns each disturbance to one of 10 types:

| | Type | | Type |
|---|---|---|---|
| 🔨 | Knock/bang | 📺 | TV/music |
| 🚪 | Door | 🔩 | Scrape/creak |
| 👣 | Footsteps | 🔔 | Signal/alarm |
| 🗣 | Voice | 🐾 | Animal |
| 〰 | Steady noise | ❓ | Other |

It also sets **markers** with finer types about every second (door slam, drawer, dishes, drilling, furniture, shouting, laughter, bass, dog …). The **Sound now** tile shows continuously what can be heard.

Switch on: ⚙ Settings → Detection → **Recognize sound type (local AI)** (on by default).

> For voices the AI detects **only the type, never the content**. There is deliberately no speech recognition. Write down what you heard yourself as a note. See Legal.

### Your own sound profiles

For sounds typical in your home (“test door”, “dishes clattering”, “own TV”):

1. **🧩 Record sound profile** (at the top of the note bar), enter a name, **Start**.
2. 3 s of quiet – then make the sound, several times if you like. Each device that heard it stores its own example (timbre, level course, AI fingerprint, no sound).
3. Check and **Apply**.

Every new disturbance is compared with all profiles; from 70 % similarity the profile is shown on it. A profile can be **background** (e.g. your own TV): such disturbances stay visible in grey but do not count. Manage them under **🧩 Profiles & re-scan**.

### Learning from ranges

If the AI missed or mislabelled a sound:

- In the event window **🏷 Name a range** and drag across it, or in the live view or history **🏷 Mark range**.
- Tap an existing type or enter a new name. Same name = same type.
- In other disturbances the app suggests similar spots (“dishes clattering? 87 %”). **✓ Correct** / **✕ Wrong** keep improving the detection. **🔎 Find similar** searches all disturbances.

### Re-scan

**🧩 Profiles & re-scan** → choose the period → **Re-scan**: each disturbance gets its profile again (confirmed ones stay) and the day recording is searched throughout – also below the threshold (e.g. “TV ran 20:10–23:40”). After new profiles simply start again.

### AI fingerprint

Once per second, when something can be heard (at least 3 dB above the background), the app stores the numbers of the AI – **no sound**, cannot be turned back into audio. This makes “Re-scan”, the “Type (AI)” column of the test threshold and learning more accurate.

- **Also store AI fingerprint between disturbances** (⚙ → Detection → Recognize sound type (AI), on by default, per device): about 2–10 MB per device and day. Below it you see whether it is running and how many seconds were stored today.
- **Store AI fingerprint** (⚙ → General): additionally the full fingerprint per disturbance, for “Re-evaluate”.

> If the computer becomes too slow, the devices take turns; then the fingerprint is missing at some spots. The AI can be wrong, especially with very quiet sounds.

## 6. Devices

All microphones are under ⚙ Settings → **Devices** → Sources. Up to 9 devices are possible.

### Server microphone

The microphone on the Home Assistant computer. Under **Microphone** you choose input, jack and volume. Usually leave it on “Default”. The **hum filter** (50 Hz in Europe) removes mains hum.

### Phone as a microphone

> **🔒 Pro:** phones, stream URLs and IP cameras are external devices and part of GLighter Pro. The server microphone is always free.

- **Phone (browser)**: “+ Phone (browser)”, scan the QR code, open the page in Chrome, accept the certificate warning, **Start**. The screen must stay on (charger). The link is secret and belongs to this phone only.
- **Stream (e.g. the app “IP Webcam”)**: “+ Phone app / stream URL”, address `http://PHONE-IP:8080/audio.wav`. Also works with the screen off. With a login: user name and password in their own fields.
- The phone port is **18443** by default (add-on → Network, “8443/tcp”).

### Video

For streams you can switch on **🎥 Record video**: on a disturbance an mp4 file **without sound** is created. Nothing is stored without a disturbance. Quality under Storage & backup → Video, folder under Storage location.

> Camera recordings in homes can be problematic (§ 201a StGB in Germany) – only film your own rooms and no other people.

### Phone as a motion sensor

A phone set up as a device can additionally act as a **motion sensor** – like a motion or vibration sensor in Home Assistant:

- **🫨 Vibration** (accelerometer): the phone lies flat on the floor, a table or against the wall and reports vibrations – e.g. stomping, bass coming through the ceiling, slamming doors or moving furniture. This documents structure-borne noise you feel, not just hear.
- **🏃 Motion in the camera picture**: the phone camera detects motion in the picture (e.g. in the stairwell). Sudden brightness changes (light on/off) are compensated.
- **📐 Tilt**: after starting, the phone remembers its rest position and reports when it is moved, tipped or lifted (sensitivity high/medium/low ≈ 3°/6°/12°). If it lies still in a new position for 1 minute, that becomes the new rest position.

**Switch on:** ⚙ Settings → Devices → card of the phone → **Phone as motion sensor** → tick "Vibration" and/or "Motion in camera picture", choose the **sensitivity** (high, medium, low). Then reload the page on the phone and tap **Start**. The browser asks for the camera or (iPhone) for "motion and orientation".

### With the IP Webcam app

If the phone is connected via **“+ Phone app / stream URL”** with the Android app **IP Webcam**, GLighter reads the app’s sensors (`http://PHONE:8080/sensors.json`; a login in the address is used too). On the device card the box is called **“IP Webcam: read phone sensors”**, with the same switches (vibration, tilt, motion in camera picture) and the same sensitivity.

- **Vibration and tilt** come from the phone’s accelerometer – the sensors must be switched on in IP Webcam.
- **Motion in camera picture** uses IP Webcam’s **motion detection** – switch it on in the app.
- If something is missing or the app is unreachable, the card says what to switch on.

> **Privacy:** everything is evaluated on the phone. Only numbers are sent (vibration strength, share of changed pixels) – **no picture and no video**. The preview is only visible on the phone itself.

**What you get:**
- On the phone and in the device bar 🫨 or 🏃 blinks while triggered.
- Each vibration or motion is stored with start, end and peak (`bewegung.csv` in the data folder). It counts as "on" until 20 s after the last trigger.
- The **Reports** tab lists "Vibration and motion in the period"; a click shows the spot in the history. The noise report contains its own table.
- In **Home Assistant** each phone gets a "Vibration" or "Motion" sensor – usable in automations and in the rules, e.g. "only record state", so it appears with every disturbance and in the daily chart.

Part of the external devices and therefore of GLighter Pro.

### Device card

- **Name**, **active**, **gain (dB)** and hum filter.
- **⏺ Record only (no detection)**: the level is still stored in the day recording (with checksum chain, visible live, in the history and in the noise log chart). But this device creates no disturbances, no AI classification, no noise trace and no report to Home Assistant. The tile shows “⏺ record only”. When you switch detection back on it applies from then on; earlier times can be evaluated with “Re-examine”.
- **⚙ Level & threshold**: own settings for this device only.
- **📏 Own reference lines**: e.g. “TV −70 dB”, shown in all charts of this device.
- **Log lists**: assign disturbances of this device to a list automatically, optionally only at certain times.
- Devices taken over from a backup that were not reachable are switched off and marked “please check”.

### Level-match devices

So that levels of different devices are comparable:

1. Put all microphones side by side, about the same distance (approx. 1 m) from the speaker.
2. **Level-match devices** → tick the devices to measure (at least two).
3. Choose the **test sound**: **play here** (through the PC or phone where the settings are open; check the volume with **▶ Preview**), **play on phone X** (a connected phone plays the noise and therefore does not measure itself) or **own sound** (extractor hood, hair dryer …).
4. **Start measurement**: the steps **1 Quiet → 2 Sound → 3 Result** are shown large, below them the level of each device – so you see right away whether every device hears the sound. The test sound starts and stops by itself.
5. Check the result: if a device is too quiet or unsteady, it says what to do (e.g. “move closer to the speaker”). Then **Apply and record**.

Each device gets its own gain so that all show the same value for the same sound. Every measurement is recorded and listed in the noise log. If the gain is changed by hand later, the device shows “⚠ changed since level-matching”; if level-matching is more than 3 months old, doing it again is recommended.

### Comparing rooms

When one device triggers, all others store the same period too (“On a disturbance store all devices”). In the event window **Device comparison** shows the peak per device. A TV in the living room is loudest there and has many highs; knocking through ceiling and walls is similar and low in all rooms.

## 7. Home Assistant

GLighter works together with Home Assistant: rules read states (TV on, washing machine running, sensor triggered), and via MQTT the app reports disturbances, checksums and switches back.

### Rules

⚙ Settings → tab **Rules** → **＋ Add rule**. First choose what the rule should do, then the device from the list (with search). States, delay and maximum duration are pre-filled to match. No automation, no YAML.

| Type | What happens | Example |
|---|---|---|
| 📈 **raise threshold** (Pro) | detection keeps running, only less sensitive | your own TV, Sonos |
| 🔕 **no disturbance reports** | graph keeps running, no disturbance | voice assistant, your own door |
| ⏸ **pause** | not evaluated during this time | vacuum |
| 📝 **only record state** | keep recording and note when it was on | TV |
| 🚩 **as event** | like record, plus a flag and its own row | door, vibration sensor |

Every rule is a **card**. Collapsed it shows name, type, device, the current state and a switch (on/off). A click expands it:

| Field | Meaning |
|---|---|
| **Name** | The rule is recorded under this name, e.g. “Wall vibration”. Empty = name from Home Assistant. |
| Action | the type (above), can be changed any time |
| Device (Home Assistant) | e.g. `media_player.tv`, `binary_sensor.wall_vibration` |
| For which device | which microphone the rule applies to (or all) |
| active when | states to tick (e.g. *on*, *playing*). Under **Condition as text** also `!off` = anything but off, `>1` = number greater than 1 |
| Delay, at most | for raise threshold, no disturbance reports and pause: keep going this long afterwards, maximum duration |

At the bottom of the card: **▶ Test** (asks Home Assistant now and tells whether the rule applies), **⧉ Copy**, **✕ Delete**. The top of the tab shows whether Home Assistant is connected and which rules are active right now.

### Raise threshold (TV, Sonos)

When your own TV is playing it should not cause a disturbance – noise from outside that is clearly louder still should. The rule raises the threshold while the device is on (plus delay). Detection keeps running.

- **Raise by:** e.g. +10 dB (0–40). The graph shows the raised threshold.
- **Follow the volume:** if the device reports its volume, the raise follows it. Example: calibrated at 35 % with +9 dB → at 18 % about +4.5 dB, muted no raise (at most double).
- **🎚 Calibrate – hold down:** let the TV or Sonos play as loud as usual, otherwise keep quiet. Hold the button for at least 3 seconds. While measuring, GLighter takes the level; on release it takes the current volume. Raise = device level (95 %) + 3 dB margin above the normal threshold. The result is shown in the card and in the log.
- **Evidence:** the events table shows “📈 TV +9 dB” for every disturbance in that time, the disturbance itself “threshold +9 dB”. The periods are stored in `ha_anhebung.csv`. The day recording keeps running unchanged.
- Without Pro the rule is saved but has no effect.


“now: …” shows live what Home Assistant reports – so you see which state a device really has. When in doubt, it records.

**Record state** writes every change to `ha_zustand.csv`. Each disturbance then shows e.g. “TV: on · 🔊 18 %”, the history shows a **blue band**, and the noise log names the state. If the TV reports its volume, it is recorded too.

> Entries already recorded keep their name, even if you change it later.

**As event** draws a coloured flag per sensor and a red line across the full height. Choose the colour in the rule under **Colour** (↺ = automatic). Every “on” appears under **📡 Sensor events** in the events table – with time, duration and note (✎). Sensor events do **not** count as disturbances and are counted separately. Switching applies retroactively, because the states are already in `ha_zustand.csv`. “Only record state” shows a thin blue strip at the top (one lane per sensor); only **pause** fills the full height.

**Note for a period:** click the strip (or ✎ in the list) to add a note, e.g. “watched a film”. It appears in the strip, the list and the noise report.

**Filter “📡 Sensors”** (Logs, top): multiple choice of which sensors, phone vibration/motion and whether disturbances are shown. Applies to history, lists and table.

### Zigbee sensors (vibration, motion, door)

Sensors integrated in Home Assistant (e.g. via Zigbee2MQTT or ZHA) work the same way:

1. Add a rule, choose the sensor entity (e.g. `binary_sensor.vibration_ceiling_occupancy`).
2. Enter a name, e.g. “ceiling vibration”.
3. Action **as event** (or **only record state**), “on when” `on`.

From then on every disturbance shows whether a vibration was reported at the same time – a strong hint at footfall or knocking through the building.

### MQTT: control and reports

With MQTT set up, Home Assistant shows the device **GLighter** with:

- Switch **Recording**, **Record manually (outside hours)**, number **Pause (minutes)**, buttons **Pause 15 min**, **Pause 1 h**, **Resume**, sensor **Paused until**.
- Per device: event **Disturbance (trigger)** (start, end, detected – with peak, duration, type, profile), device triggers for automations, sensor “Last sound type” and hourly the current **checksum** (stored independently in Home Assistant).

Example – pause for 10 minutes while the litter box cleans:

```yaml
automation:
  - alias: "Pause GLighter while the litter box cleans"
    trigger:
      - platform: state
        entity_id: sensor.litter_box_status
        to: "cleaning"
    action:
      - service: mqtt.publish
        data:
          topic: gaslighter/pause/set
          payload: '{"minutes": 10, "reason": "litter box"}'
```

Recording stopped by hand is not restarted automatically by a pause from Home Assistant.

### Log a disturbance right from the dashboard

With MQTT the add-on adds two elements to the "GLighter" device:

- **Log disturbance / note**: text field. Type text, press Enter, and the note is saved with the current time. The field clears afterwards.
- **Mark disturbance now**: button. One tap creates a note "Disturbance (Home Assistant)" immediately, without text.

Put both on any dashboard (for example in an "Entities" card). If a disturbance was detected just before, the note is attached to it, exactly like the note bar in the live view.

### No disturbance reports (graph keeps recording)

Sometimes a disturbance should not be reported while the graph keeps recording, for example when you open the door yourself.

- **In a rule:** choose the action **"no disturbance reports"**. While the condition holds and for the **delay** afterwards (for example 10 minutes), no disturbance is created. The graph keeps recording, with no gap.
- **Lead time (s), e.g. for a voice assistant:** the wake word (“Hey Jarvis”) comes *before* the assistant switches to “listening”. With **lead time**, a disturbance that started up to this many seconds before the rule switched on does not count either. For this, GLighter holds each disturbance back that long (lead time + 2 s) before reporting it. Levels and graph stay unchanged; the log says “not counted”. **Set up:** add a rule, choose the entity `assist_satellite.…` – states `!idle`, “no disturbance reports”, lead time 3 s and delay 0.5 min are pre-filled. Wake word, command and the spoken answer then don’t count.
- **As a dashboard button:** the "GLighter" device has **"Start: no disturbance reports"**, **"Report disturbances again"**, an adjustable **duration** (1–240 minutes, default 10) and **"No disturbance reports until"**. Put them on your dashboard. One tap starts the set duration.

### Tiles as sensors

Every tile you created in GLighter (Live or Logs, see Tiles) appears via MQTT in the **GLighter** device as a sensor of its own, e.g. `sensor.gaslighter_tile_s_1a2b3c4d` (unique ID `gaslighter_tile_<id>`).

- The **state** is the tile's main value: count, total duration in seconds or peak in dBFS. The name is the tile's name or your own title from **✎**.
- **Attributes:** period (from, to), number of entries, display, split, measure, `items` (name and value of each bar, list or table row) and, when split by time, `series` (values for charts).
- It is updated every minute and shortly after every new disturbance – only changes are sent.
- “Selected period” counts as **today** in Home Assistant.
- If you delete a tile, its sensor disappears from Home Assistant too.

In the **dashboard in Home Assistant** (see below) the section **Own tiles** places these sensors: numbers as tile cards, trends as statistics graphs, bars as history graphs, lists and tables as markdown cards.

### Create a dashboard in Home Assistant

⚙ Settings → tab **Rules** → **Dashboard in Home Assistant**. With one click GLighter creates a ready-made dashboard with its entities. You choose:

- **Name** and **address** (e.g. `gsim-glighter`, it then appears in the Home Assistant address bar),
- whether it shows in the **sidebar** and whether only **administrators** see it,
- which **sections** go in: now (disturbance, level, today), level of the last 24 hours, log a disturbance, no disturbance reports, recording and pause, other microphones, **own tiles**, “Open GLighter” button.

**Create in Home Assistant** creates the dashboard. If one already exists at that address, GLighter asks before replacing it (changes you made there are lost). Without a click GLighter changes nothing in Home Assistant.

**Show as YAML** has the same template to copy: create a dashboard in Home Assistant, **Edit** → ⋮ → **Raw configuration editor**, paste, save. You can keep editing the dashboard in Home Assistant afterwards.

## 8. Printing and noise log

There are two printouts: the **noise log** (report with summary and list) and the **history as a score sheet** (the curves line by line).

### Noise log

Logs tab → **🖨 Noise log** (for period, device and list) or **📝 All notes** → log. It contains:

- period, devices, summary (count, disturbed time, longest quiet), detected sound types, named ranges,
- the **day history**: one chart per day and device over 24 h (peak, background, threshold, disturbances red, Home Assistant blue, not recorded hatched, notes), same scale per device,
- every disturbance with date, time, duration, level, type, notes, witnesses and states from Home Assistant,
- quiet hours (🌙), countermeasures, level-matching of the devices,
- **interruptions and updates** with cause and your comment,
- the **data chain** per device and day with checksum.
- the **method**: program and version, per device type, microphone/model, place and window, “Microphone not calibrated: values are indications and do not replace an expert report”, whether sound is stored (“No audio is stored” while “Store real audio” is off) and that the sound type is a suggestion of the detection unless you confirmed it,
- a **summary** by time (hours, weekdays, quiet hours), type, intensity (peak), duration and frequency (on how many days, average per day),
- per disturbance **peak, duration and number of impulses** (how often the level rose above the threshold, from the day recording),
- a **gap-free timeline**: every day of the period, including days without disturbance, with “recorded” or “no recording”,
- a short **explanation of the checking procedure** for the data chain.

At the top of the page there is also **⬇ Raw data (CSV)** (all measured values of the disturbances, for experts) and **⬇ Evidence package (ZIP)**: noise log (HTML), raw data, notes, timeline and checksums as CSV and a summary with method as text. Both are also available under 📝 All notes → log.

**Pattern filter:** by default all disturbances are included; those filtered out by a pattern carry the note “filtered out by pattern …”. With **leave out those filtered by pattern** they are omitted and the top names the patterns and how many they removed.

At the top of the page (not printed) choose **Day chart** (on by default) and **Chart per disturbance** (off by default): a small chart with context below every disturbance that has a note or comes from the chosen list (at most 300).

Print in the browser or save as PDF. The printed document is always titled “Lärmprotokoll” (noise log).

> Levels are relative dBFS values, not a calibrated dB(A) measurement. Sound recordings never go into the log. Not legal advice.

### Print history (score sheet)

In the history **🖨 Print**:

- **Period**: from–to or quick choice “Visible section”, “Period of the report”, “All data”.
- **Time per line**: 1 min to 1 h (default 10 min – a whole day is 144 lines).
- **Devices** below each other, **content** (level trace, spectrogram, disturbance info and notes), **Merge lines without recording** (on by default).
- **Scale**: the same for all lines (comparable) or fitted per line (more detail); **A4 landscape** or **portrait**.
- **Evidence (summary, timeline, checksums)** (on by default): a summary by time, type, intensity, duration and frequency at the top; method, timeline with all days, checksums with explanation and the link to the raw data (CSV) at the bottom. Each disturbance shows its impulses and, unless confirmed, “suggestion of the detection (confidence x %)”.
- **leave out those filtered by pattern**: as in the noise log.

The dialog estimates lines and pages. **Open preview** builds the pages in a new window; print there or save as PDF. An active test threshold is printed along, with a count per line.

## 9. Backup, import and export

### Download a backup

⚙ Settings → Storage & backup → **Download / restore backup (ZIP)** → **⬇ Download backup**. The ZIP file contains everything: settings, devices, time profiles, rules, `log.csv` and all log files, day recordings with checksums, AI results, sound profiles, notes, tiles, the arrangement of the views (`layout.json`), comments on interruptions, named ranges, lists, videos and – if stored – sound.

> The file can get large (hundreds of MB). Download it regularly and keep it in another place.

**Without secrets:** the normal backup and the daily backup to a network drive/NAS do **not** contain the secret key of the checksum chain (`kette_schluessel.json`), no passwords of network cameras and no phone IDs. A lost backup can therefore not be used to recompute data unnoticed or to pose as your phone.

### Move to a new device (with key)

Under **🔑 Move to a new device (with key)** enter a password (at least 8 characters, twice) and **⬇ Download move backup**. The ZIP additionally contains the chain key and the access data – **encrypted** with the password (scrypt and HMAC-SHA256, encrypt then authenticate). They cannot be read without the password. The password never goes into the address and is not stored; keep it separate from the file.

When restoring, the preview asks for the password. A wrong password stops before anything is restored. Without a password the file is restored like a normal backup.

For further processing there are also `log.csv` (Logs tab), the notes as CSV (📝 All notes) and the noise log as PDF.

### Restore a backup

> **🔒 Pro:** the first import is free (e.g. when moving), further imports are part of GLighter Pro. Downloading a backup is always free.

1. **📂 Choose backup** and **Check backup …** – the file is uploaded and examined, nothing is changed yet.
2. The preview shows version and date of the backup and – with “Take over settings and devices” – every device from the backup:
   - **already here** (will be replaced) or **new**,
   - **ready**, **phone** (connects as soon as it opens the app) or **not reachable** (taken over switched off, marked “please check”).
   - Devices set up only here **stay unchanged**.
   - If the backup's microphone does not exist here, the current one stays selected.
3. Set or clear the ticks and **Restore now**.

Afterwards a report shows new files, merged days, skipped days and the devices taken over.

**Without the key** (normal backup on another device) the restored days stay checkable: the report and the noise log say “chain complete, key missing: authenticity can only be checked with the original device” – it is checked that no minute is missing and the order is right. Checksums and day files are never changed; which days were restored is noted in a separate file (`kette_fremd.json`). Older backups (up to 1.79) that still contain the key are still accepted.

**Phones** get a new ID without a move – the report names them, they need to be paired again (link or QR code in the device card). If the password of a network camera is missing, the device is set to “please check”.

**Limits when restoring:** before unpacking GLighter checks the number of entries (at most 300,000) and the space the unpacked files need against the free storage. The total size of an upload is fixed with the first part.

### Daily backup to network drive, NAS or USB

> **🔒 Pro:** The daily backup and “save space” are part of GLighter Pro. **“⬇ Download backup” and `log.csv` always stay free.** If Pro expires, the daily backup pauses; days already moved stay readable.

⚙ Settings → Storage & backup → **Daily backup**. With a target set, GLighter copies everything new there every day (default 03:30) – the same files as the ZIP backup, but **incremental**: only new and changed files, each verified with SHA-256 afterwards.

- **Nothing is ever deleted in the target.** If an already backed-up file changes later, the old version stays next to it as `….alt-YYYYMMDD-hhmmss`.
- **Target unreachable** (NAS off, Wi-Fi gone): recording continues normally on this device. It is retried hourly, and the next run catches up everything missing.
- **Back up now** starts a run immediately; last run, number of files and errors are shown next to it.

**Examples for the target**

| Target | How to set up | Folder to enter |
|---|---|---|
| NAS / Windows share (SMB) | Home Assistant → Settings → System → Storage → **Add network storage**, name e.g. `nas_gaslighter`, usage **Share** | `/share/nas_gaslighter` |
| NAS as media folder | as above, usage **Media** | `/media/nas_gaslighter` |
| USB drive on the Home Assistant device | plug it in (appears under `/media`) | e.g. `/media/usb/gaslighter` |

> The target must already exist and must **not be on the same storage** as the data. Otherwise a network drive that is not mounted would silently fill your own storage – GLighter reports this as an error and copies nothing.

### Save space

With **“Save space: keep old data only in the target”**, files older than “Delete after (days)” that are verified in the target are replaced here by a link to the copy. **Reports, history, printing and the checksum chain keep working** – they read these days from the target. If the network drive is asleep, the first load takes a little longer (“network drive may be waking up”). If it is unreachable, these old days are missing until it is back. Settings, `log.csv` and recent days always stay here.

If **“Delete old recordings automatically”** is also on, GLighter only deletes what is verified in the target once a target is set.

### What happens when restoring

- **Nothing twice, nothing overwritten**: existing disturbances, notes and lists stay, only missing data is added. Restoring several times does no harm.
- **Days that already exist** (e.g. “today” after a reinstall): the missing minutes are added. The checksum chain stays verifiable – the restored part gets its own section, and “Interruptions” lists “Import …: extended by N minutes”. If the times overlap with other data, the day is skipped and named in the report.
- **Devices that no longer exist**: their data is still restored and can be chosen as “(former)” in the history, the device filter and printing.
- Storage locations (output and clip folder) stay those of this system.

### Reset

⚙ → General → **Reset**: measurements & disturbances, notes & lists, sound profiles or settings to default. Devices and connections always stay. A backup is offered first.

### Search index

GLighter keeps a **search index** (SQLite file `suchindex.sqlite` in the app data folder). It speeds up noise reports over weeks and months:

- **Chain check per day:** the result is stored with a SHA-256 checksum over the *content* of all files of that day. If a single byte changes, the day is checked again – the check is exactly as strict as without the index.
- **Condensed day tracks** (every 10 seconds) for the charts in the noise report.

The index only contains derived data, never changes the recording, checksum chain or disturbances, is not part of the backup and fills slowly in the background after start. **Settings → General → Backup → Rebuild** clears it; it then rebuilds itself. If it is missing or damaged, GLighter works without it – just slower.

## 10. Interruptions, data chain and updates

### Interruptions

If the add-on is not running (power cut, Home Assistant restarted, update via the add-on store), the recording is missing. GLighter notices this at the next start and shows it in Logs below the summary:

- **ended without shutdown, e.g. power cut** – the add-on could not sign off (power gone, crash).
- **stopped / restarted by Home Assistant** – ended cleanly (restart, add-on stopped).
- **Update** – a new version was installed.
- **Gap in the day recording, cause not logged** – more than 90 seconds are missing in the data without the start noticing (e.g. moving to a new installation). Applies to the microphone on the computer and streams; deliberate pauses do not count, phones are not checked.

After a power cut Home Assistant starts the add-on by itself as soon as the computer runs again.

### Add a comment

- In the **history**, click or tap the hatched area – a small window with period and cause opens. Enter text, e.g. “fuse blown”, **Save**.
- Or in the list “Not recorded …” on **📝 Comment**.

The comment appears in the hatching, the list, the printout and the noise log. The recording itself stays unchanged.

### Watchdog

On the add-on page in Home Assistant switch on **Watchdog**: if the add-on stops unexpectedly, Home Assistant restarts it.

### Data chain (checksums)

Every written minute of the day recording gets a SHA-256 checksum built on the previous one. If someone later changes a value or removes a minute, the chain no longer matches from that point.

- Logs shows “🛡 Data chain checked: complete and unchanged” or where it differs.
- The noise log lists the result and the last checksum per device and day.
- Each device reports its checksum to Home Assistant every hour (stored there independently).
- Days completed from a backup have their own section in the chain, see Backup.

### Updates

> **New (security):** updates from `share` are only used if **“Accept updates from /share” (`share_update`)** is switched on in the configuration **and** the folder contains a valid G-Simulation signature (`manifest.txt` + `manifest.sig`). Unsigned or modified folders are rejected (note in the log). A verified copy under `/data/update_run` is started.

**Without a recording gap:** copy the folder `gaslighter` from the update zip via Samba to `\\homeassistant\share\gaslighter_update\` (overwrite existing files). After 10–20 s only the program restarts; recording continues and is delivered afterwards. If the new version does not start, the add-on automatically goes back to the previous one.

**Full installation** (only when a version requires it, e.g. new name or watchdog): copy the folder from the full zip to `\\homeassistant\addons\` and rebuild the add-on in Home Assistant. This causes a short gap.

Every start, update and interruption is listed with time and version in Logs and in the noise log.

## 11. Settings from A to Z

At the very top choose **All devices** or a single device. For a device, “Own settings for this device” sets different values (threshold, minimum duration, monitoring time, storage). The bar at the top shows level, background, threshold and the **preview** (purple) of your not yet saved settings live.

**🎯 Set threshold automatically** (🔒 Pro) – suggests values for “When does something count as a disturbance?” for the device selected at the top (also a connected phone). **From last night** uses last night’s quiet hours without the disturbances in them – no waiting, most reliable. **Measure now** (30 s, 1 min or 5 min): keep quiet during that time; if it was clearly louder in between, it says “measurement disturbed – please repeat”. The suggestion is shown as a table “now → suggestion”; only **Apply** fills it in (purple preview), **Save** keeps it. ⓘ explains every setting; “Show help” hides the texts.

### Devices

- **Sources (microphones)** – see Devices.
- **Level-match devices** – see Level-matching.
- **Microphone** – input on the server, jack, volume, sound quality (16000 Hz is enough for knocking).
- **Place and window** – per device in the device card: where in the room you measure (e.g. “bedroom, shelf at the wall to the neighbour”) and whether the window is **mostly open**, **mostly closed** or **changing**. Optionally a window sensor from Home Assistant (rule “only record state”). Both appear in the method section of the noise log, the print and the evidence package.

### Detection

### When does something count as a disturbance?

> **🔒 Pro:** without Pro these values are view only and GLighter uses the defaults. They can be changed with GLighter Pro.

| Setting | Meaning |
|---|---|
| Type of threshold | **Adapts, with limits** (recommended), **Adapts**, **Fixed** |
| How much louder than normal? | distance to the background, 8–10 dB is a good start. Smaller = more sensitive. |
| Lower / upper limit | the threshold never goes below or above |
| Fixed threshold | only with “Fixed” |
| “Normal” is learned from the last … | period for the background (e.g. 60 s) |
| How “normal” is calculated | **Quietest moments** (recommended), typical level, minimum, average, maximum |
| Adapting when it gets louder / quieter | large = noise hardly pulls the threshold along; small = follows quickly |
| Minimum duration (ms) | 0 = every knock counts; 40–60 filters clicks |

### Recognize sound type (AI)

**Recognize sound type (local AI)** – classifies disturbances (door, knocking, music …), no sound is stored. **Store AI fingerprint for each disturbance** – better distinction when learning and “re-evaluate” without sound. **Also store AI fingerprint between disturbances** – continuously, for “re-examine”; see AI fingerprint.

**Sound profiles** – see AI. **Different values at certain times** (time profiles) – e.g. more sensitive at night, general or per device.

### Filter out patterns

Known, recurring sounds (clock chime on the hour, fridge, heating, alarm clock, your own TV) can be hidden **in the display**. A pattern combines any number of conditions:

| Condition | Example |
|---|---|
| Device | only the hallway microphone |
| Type or sound profile | “signal”, sound profile “fridge” or “background (own device)” |
| Time from–to, weekdays | 06:00–06:20, Mon–Fri (also across midnight) |
| Duration from–to, peak from–to (dBFS) | 2–8 s, −45 to −30 dBFS |
| Distance to the threshold | 0 to 4 dB above the threshold |
| Repetition | every 60 minutes from minute 0, ± 2 minutes (= every full hour) |
| State in Home Assistant | only while the rule “TV on” applies |

Plus a name and a colour. **Create:** here with **＋ Add pattern** or in the event list via **⋮ → Filter out as pattern …** – device, type, time (± 15 min), duration and peak are then taken from the disturbance. Before saving you see how many disturbances of the last 30 days the pattern would match, with examples.

**Effect:** matching disturbances are missing from lists, counters, tiles and the tile sensors in Home Assistant and are only shown faintly in charts. The count then says e.g. “(12 filtered out by pattern)”. The switch **⊘ show filtered** above the sections brings them back, marked with the pattern name.

**Nothing stored changes:** patterns are kept in `muster.json` (included in the backup). `log.csv`, day recording, checksums and event files stay unchanged – deleting a pattern shows everything as before.

**Noise log, print and export** contain **all** disturbances by default, filtered ones with the note “filtered out by pattern …” (CSV column `nach_muster_ausgefiltert`). With **leave out those filtered by pattern** they are omitted and the top names the patterns and how many disturbances they removed.

> **🔒 Pro:** one pattern is free, several need GLighter Pro. Without Pro further patterns stay stored, only the first applies.

### Times & pauses

- **When to monitor?** – monitor from / to (both empty = around the clock, past midnight possible). Outside of it nothing is counted; you can still capture via the display at the top.
- **Quiet hours** – quiet hours from / to (usually 22:00–6:00), Sunday all day. Notes and disturbances during quiet hours get 🌙.
- **Different values at certain times** – see above (time profiles).
- **Rules (Home Assistant)** – own tab **Rules**, see Home Assistant.

### Storage & backup

### What is stored?

| Setting | Meaning |
|---|---|
| Context before and after the disturbance (s) | this many seconds before and after the disturbance are shown when viewing |
| Day recording with layers | low/mid/high, frequency for the whole day (+1–2 MB per device and day) |
| Day recording with spectrum | spectrogram for every moment (+3–8 MB per device and day) |
| Record all devices on a disturbance | the other devices store a noise track for the same period (no sound) – to compare rooms |

### Store real audio (not recommended)

Default **off**. When on, a WAV file is stored for each disturbance in addition. **Audio only without detected voices** (recommended) prevents storing as soon as the AI detects voices anywhere. Read Legal first.

### Video

Video width, frames per second, video quality (for IP cameras and phones).

### Storage location

**Folder for noise tracks** – empty = default. Only change it if new noise tracks should be stored elsewhere (e.g. `/media/gaslighter`). For a copy on the NAS use the **daily backup**, not this folder.

### Keep & delete automatically

**Delete old recordings automatically** and **Delete after (days)** – off = nothing is ever deleted. With the daily backup, only what is verified in the target is deleted.

### Backup

**Download / restore backup (ZIP)** – always free. **Daily backup** to network drive, NAS or USB (Pro). Both see Backup.

### General

- **Language** – German, English or like the browser.
- **“Auto” height in the live view** – “with threshold” (default): the threshold is always in view. “measurements only”: tighter around level and background.
- **Mouse wheel on the chart** – “only with Ctrl” (default): the wheel scrolls the page, hold Ctrl to zoom. “Always zooms”: as before, the wheel zooms directly.
- **Log & notes** – **Group disturbances up to (s) apart** (groups in the list), **Note belongs to the disturbance if up to (min) after it**.
- **GLighter Pro** – see Pro.
- **GReport (notes app)** – GReport is the notes part as its own app (e.g. for phones or flatmates). When GReport is installed, its notes appear here automatically with Pro – at disturbances, in the history and in the noise log, marked “GReport”. They are edited in GReport.
- **Reset** – see Reset.
- **Diagnostics** – details about microphone and sound card for troubleshooting.

## 12. Legal and privacy

> **Not legal advice.** The law differs by country. If in doubt ask a lawyer or a tenants' association.

### What is stored

- **Measurements**: level, background, threshold, frequency bands (23 third-octave bands) in 125 ms steps. Research shows intelligible speech cannot be recovered at this resolution.
- **AI results** and **AI fingerprint**: numbers describing how it sounds – no audio, cannot be turned back into sound.
- **Your notes**, lists, sound profiles, states from Home Assistant.
- Everything stays **on your computer**. There is no cloud and no transfer to third parties.

### No sound, no speech recognition

Audio only lives briefly in memory (live view, detection) and is overwritten continuously. For voices only the **type** is detected, never the content – there is deliberately no speech recognition.

> **Warning (§ 201 StGB in Germany):** recording non-public speech can be a criminal offence unless it happens merely by chance. With continuous recording towards the neighbours this is foreseeable. That is why “Store real audio” is off by default and can only be switched on after a notice. Secret recordings are usually not admissible in court. Sound recordings never go into the noise log.

### Video

Camera recordings in homes can be problematic (§ 201a StGB). Only film your own rooms, no other people, not into other flats or the stairwell.

### Evidential value

- Levels are **dBFS** (relative to the sound card), not a calibrated dB(A) measurement.
- A log is convincing when it is kept **regularly**, is **traceable** (time, duration, type, effect, witnesses) and **unchanged** (data chain).
- Your own notes (“woke up”, “child woken”) and witnesses make the difference.

### What the recording shows and what not

> **No legal advice.** The following points are factual hints from published decisions and expert articles (German law). They promise no success in court. For your case ask a lawyer, a tenants' association or a victim support service.

**It can show:** when, how long and how loud (relative, dBFS) it was, how often and at what times – over weeks and months, including that quiet days were measured too. And that the day recording has not been changed since (checksums).

**It cannot show:**

- **where** a sound comes from and who causes it – the detection “knocking” does not say which flat,
- **how loud in dB(A)** – the microphone is not calibrated: values are indications and do not replace an expert report,
- that the **sound type** is right while it is a “suggestion of the detection” – check it and confirm or correct it with a click in the event list. Your confirmation is kept separately (`bestaetigt.json`), the detection's estimate stays stored.

**What helps:** witnesses (neighbours, property management, police), timely notes with time, type, intensity, duration and frequency, reports with date and case number. In disputed cases courts obtain their own expert reports – the recording can show when a measurement is worthwhile.

**Checksums** show that the data has not been changed since recording; they are not an electronic signature. Digital data has no presumption of authenticity in court – so attach the raw data (CSV) and checksums (evidence package, see Printing).

### Short hints in the app

With **💡 Show help** (⚙ Settings → General) short hints appear in a few places. Each can be hidden with ✕; switching “Show help” off hides all of them. **Why?** names the source.

| Where | Hint | Source |
|---|---|---|
| Devices (setup) | Measure at a fixed place and note whether the window is open or closed. | AG Wolfratshausen 5 C 274/20 |
| Event list | Check detected sound types and confirm or correct them; the detection does not show which flat a sound comes from. | LG Berlin II 56 S 100/23 WEG |
| Recording, live | Keep measuring on quiet days – a gap-free time series shows frequency and pattern more convincingly. | BGH VIII ZR 1/16 Rn. 14; § 238 Abs. 2 StGB |
| Export, noise log | Pass on the values as an indication and suggest an expert report in a dispute. | AG München 472 C 18927/16; OLG Celle 4 U 199/09 |
| Export, noise log | Attach raw data (CSV) and checksums. | § 371 ZPO; Irskens, EDVGT 2024 |
| General | Do not add secret audio or video recordings of neighbours. | BGH VI ZR 1370/20; BVerfG 1 BvR 1611/96; AG München 173 C 11834/23 |
| General | Do not answer with counter-noise; document and take legal action. | AG München 173 C 11834/23 |

## 13. Troubleshooting and FAQ

### “The signal is very quiet”

The background is very low (below −85 dBFS). Is the microphone in the right jack? Raise the microphone volume in ⚙ → Devices → Microphone or increase the device gain.

### “The threshold is at the lower limit”

It is so quiet that the threshold may not go lower. That is intended if very quiet sounds should not count. Otherwise lower the limit in ⚙ → Detection.

### Too many or too few disturbances

- Too many: raise “How much louder than normal?” or set “Minimum duration” to 40–60 ms.
- Too few: lower the distance, lower the lower limit.
- Your own TV counts: record a sound profile as **background** or add a Home Assistant rule “record state” or “pause”.

### “Type (AI)” column is empty

- “AI detection is switched off”: ⚙ → Detection → switch on **Recognize sound type**.
- “AI model not found”: reinstall the add-on once with the **full zip** (update zips do not contain the model).
- “no fingerprint at this spot”: nothing was stored at that second (too quiet or computer busy). Check in ⚙ → Detection whether the fingerprint is running.

### Gap in the history

Hatched = the add-on was not running. The cause is listed in Logs under “Not recorded …”. Add a comment: click the hatching. See Interruptions.

### Phone does not connect

- Is port 18443 open (add-on → Network)? Certificate warning accepted?
- Keep the screen on or use the app “IP Webcam” as a stream.
- New link: create the QR code again in the device card.

### Update is not picked up

The folder must be at `\\homeassistant\share\gaslighter_update\gaslighter\…`. After 10–20 s without further changes the program restarts. The version is shown at the top next to the name.

### Where is the data?

`/share/gaslighter` (via Samba `\\homeassistant\share\gaslighter`): `log.csv`, `clips/` (day recording in `clips/tag/`, AI in `clips/ki/`, notes, lists, profiles), settings and devices in `/data`.

## 14. GLighter Pro

GLighter is free. **Recording, the live view, reports, the printable noise report, export (`log.csv`, notes) and creating a backup** are always free – no time limit, no ads.

The yearly licence **GLighter Pro** additionally unlocks:

| Feature | Without Pro | With Pro |
|---|---|---|
| Import a backup | once for free (e.g. moving) | as often as needed |
| Advanced detection settings (tab “Detection” → “When is something a disturbance?”) and 🎯 set threshold automatically | view only, defaults | fully adjustable, also per device and in time profiles |
| External devices: phone in the browser, phone app / stream URL, IP camera | locked | up to 8 additional devices |
| Phone as motion sensor (vibration, motion in picture) | locked | ✔ |
| 📊 Configure your own statistics (Statistics) | templates | fully configurable |
| ⊘ Filter out patterns (Patterns) | 1 pattern | up to 30 patterns |
| Daily backup to network drive/NAS/USB and “save space” (Backup) | “⬇ Download backup” by hand | automatic every day, verified |

The server microphone (on the Home Assistant computer) always works without Pro.

### Buy

⚙ Settings → General → **GLighter Pro** → **🛒 Buy Pro** opens the GLighter page on gsimulations.de. The licence is valid for **1 year from purchase** for **1 Home Assistant installation**. It does **not** renew automatically – there is no subscription. After purchase the licence key is sent by e-mail.

### Enter the key

1. ⚙ Settings → General → **GLighter Pro**.
2. Paste the complete key from the e-mail. It starts with `GL1-`; spaces and line breaks do not matter.
3. **🔑 Activate**. It then shows “Pro active – valid until …”.

The key is checked **without internet** – GLighter sends nothing to G-Simulation. It is **not** included in backups; after a reinstall simply enter it again.

Locked places show **🔒 Pro**. Clicking it explains the feature and offers “Buy Pro” and “Enter key”.

### Expiry and renewal

14 days before expiry a notice with “Renew” appears once at the top. After expiry everything free keeps working and recorded data stays complete:

- External devices stop recording (they stay configured and continue immediately with a new key).
- Advanced settings keep their values but can no longer be changed.
- Further imports need Pro again.

To renew, buy a new licence and enter the new key.

### Moving to a new computer

Download a backup on the old computer, install GLighter on the new one and import the backup – the **first import is free**. Then enter your Pro key again.
To take the chain key and the access data along as well, use the move backup with password.

## 15. Glossary

| Term | Meaning |
|---|---|
| **dBFS** | level relative to the sound card's maximum (0 dBFS). Always negative: −80 very quiet, −50 conversation, −20 very loud. Not calibrated dB(A). |
| **Background** | the learned “normal” level, from the quietest moments of the recent time |
| **Threshold** | from this level it counts as a disturbance; adapts to the background by default |
| **Disturbance / event** | a rise above the threshold (ends 0.5 s below it, at most 5 min) |
| **Peak** | the highest level within 125 ms or within a disturbance |
| **Group** | consecutive disturbances of the same type with short pauses |
| **Day recording** | continuous measurements of the whole day per device (`clips/tag/`) |
| **Noise track** | measurements of a disturbance with context (level, frequency bands), no sound |
| **Spectrogram** | frequency over time, bright = loud; low at the bottom, high at the top |
| **Third-octave bands** | 23 frequency ranges from 50 Hz to 8 kHz |
| **Layers** | additional curves: low/mid/high, dominant frequency, spectral centroid |
| **Sound profile** | your own trained sound type (🧩) |
| **Named range** | a section marked and named by hand (🏷), learning example |
| **AI fingerprint** | the AI's numbers per second, describes the sound, no audio (ⓕ) |
| **Test threshold** | freely chosen value for counting peaks afterwards, display only |
| **Data chain** | SHA-256 checksums per minute, make changes visible |
| **Monitoring time** | set monitoring hours (e.g. 22–6) |
| **Quiet hours** | period for 🌙 in the log (e.g. 22–6, Sunday) |
| **Level-matching** | aligning the gain of devices so levels are comparable |
| **Record state** | Home Assistant rule that writes down states without pausing |


---

**Fremde Bestandteile / Third-party components:** uPlot (MIT, `app/web/uplot.LICENSE.txt`), YAMNet (Apache-2.0).
