# GasLighter (Lärmprotokoll / Noise Log)

Das vollständige Handbuch mit Bildern, Suche und Querverweisen steht in der App unter **📖 Handbuch**. The full manual with pictures, search and links is in the app under **📖 Manual**.

**Inhalt / Contents:** 1. Schnellstart in 5 Minuten · 2. Live-Ansicht · 3. Protokolle · 4. Ereignis-Fenster · 5. KI: Geräuscharten und Tonprofile · 6. Geräte · 7. Home Assistant · 8. Drucken und Lärmprotokoll · 9. Sicherung, Import und Export · 10. Unterbrechungen, Datenkette und Updates · 11. Einstellungen von A bis Z · 12. Rechtliches und Datenschutz · 13. Fehlerbehebung und häufige Fragen · 14. GasLighter Pro · 15. Glossar


---

# Deutsch

## 1. Schnellstart in 5 Minuten

GasLighter hört dauerhaft mit und schreibt ein **Lärmprotokoll**: Wann war es wie laut, wie lange, welche Art von Geräusch – mit Prüfsummen, damit niemand die Daten unbemerkt ändern kann. **Ton wird dabei nicht gespeichert**, nur Messwerte.

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

- Regelmäßig unter ⚙ Einstellungen → Allgemein → **Sicherung herunterladen** eine Sicherung ziehen. Siehe Sicherung.
- Updates ohne Aufnahmelücke: neuen Ordner nach `\\homeassistant\share\gaslighter_update\` kopieren. Siehe Updates.

> **Wichtig:** GasLighter ist eine Gedächtnisstütze und Dokumentation, keine geeichte Lärmmessung in dB(A). Für Vermieter, Hausverwaltung oder Behörden zählt vor allem: regelmäßig, nachvollziehbar, mit eigenen Notizen. Siehe Lärmprotokoll.

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
| Mausrad oder Touchpad = Zeit zoomen | zwei Finger spreizen = Zeit zoomen |
| Ziehen oder seitlich wischen = in der Zeit blättern | waagerecht wischen = blättern, senkrecht = Seite scrollen |
| Umschalt + Ziehen = Bereich aufziehen und hineinzoomen | − / + |
| Umschalt + Mausrad oder Mausrad über der dB-Beschriftung = Höhe zoomen (unten bündig) | „Auto“ |
| Doppelklick = zurück zu Live | Doppeltippen = zurück zu Live |
| Über eine Störung fahren = Einzelheiten | Störung antippen = Einzelheiten |

Weiter zurück als die letzten 10 Minuten zeigt die Grafik den **ganzen Tag** aus der Tagesaufzeichnung (Zeitfenster 1 h, 6 h oder „Heute“).

### 📝 Notiz jetzt

Für das, was du gerade hörst – einfach lostippen oder Merkmale antippen (oben, unten, Klopfen, Bass, aufgewacht …).

- **Ohne eigene Uhrzeit**: Liegt kurz vorher eine Störung (Einstellung „Notiz zuordnen“, Standard 5 min), gilt die Notiz für sie. Die Leiste zeigt vorher, wohin sie kommt.
- **läuft noch**: Die Notiz bekommt einen Zeitraum von der ersten Eingabe bis zum Speichern.
- **Von / bis und Zeuge** stehen immer direkt im Bereich; leer lassen heißt „automatisch“ (Uhrzeit beim Speichern).
- **Nur Markierungen, kein Text?** Dann bildet GasLighter beim Speichern einen Satz daraus, z. B. „Deutliche Schritte im Treppenhaus“. Du kannst ihn später ändern.

**Abdocken (Pro):** Mit **⧉** neben dem Titel löst du den Notizbereich als eigenes kleines Fenster heraus. In Chrome und Edge bleibt es über anderen Programmen liegen (z. B. über einem Spiel oder Film), sonst ist es ein normales Zusatzfenster. **Zurückholen** oder das Fenster schließen setzt ihn wieder ein.
- Strg + Enter speichert. Am Handy ist die Leiste zunächst zugeklappt.

### 🏷 Bereich markieren

1. „🏷 Bereich markieren“ antippen – über der Grafik erscheint ein Hinweis mit **Fertig**.
2. Den Bereich waagerecht aufziehen (0,15 s bis 2 min).
3. Eine **vorhandene Art** antippen (Tonprofil 🧩 oder benannter Bereich 🏷) oder einen neuen Namen eingeben – gleicher Name = gleiche Art, die KI lernt daraus. Siehe KI.

### Ereignisse heute

Die Liste unten zeigt alle Störungen des Tages (alle Geräte oder das gewählte). Ein Klick öffnet die Störung, siehe Ereignis-Fenster. Spalten wählst du über ⚙. Am Handy erscheinen die Einträge als Karten.

## 3. Protokolle

Der Reiter **Protokolle** zeigt einen Zeitraum vollständig: Zusammenfassung, Wochenleiste, Verlauf aller Geräte, Auswertungen und die Liste aller Störungen.

### Zeitraum und Filter

- **Erfassungszeit** (eingestellte Überwachungszeit, z. B. 22–6 Uhr), **Heute**, **Gestern**, **7 Tage**, **30 Tage** oder **Von–bis**. ‹ › blättert um einen ganzen Zeitraum.
- **Quelle / Gerät**, **Art** (Mehrfachauswahl, z. B. Klopfen + Schritte) und **Liste** filtern alles darunter. Geräte, die es nicht mehr gibt, deren Daten aber vorhanden sind, stehen als „(ehemalig)“ in der Auswahl.
- **🖨 Protokoll** erstellt das Lärmprotokoll für Zeitraum, Gerät und Liste, **⬇ Bild (SVG)** ein Bild. Siehe Drucken.

### Bereiche anordnen (Dashboard)

Live und Protokolle bestehen aus **Bereichen** (Übersicht, Unterbrechungen, Verlauf, Ereignisse nach Uhrzeit, je Tag, Ereignisse im Zeitraum, Notizen und Bewegung, Sensoren im Zeitraum). Jeder Bereich hat oben eine Leiste:

- **▾ / ▸** klappt ein und aus (auch Doppelklick auf die Leiste).
- **✕** blendet aus. Wieder einschalten unter **▦ Layout anpassen**.
- **⌖ nur sichtbarer Bereich** (Ereignisse, Sensoren): zeigt nur, was im Verlauf gerade zu sehen ist – zieh im Verlauf z. B. 20:00–22:00 auf, dann zeigen Tabelle bzw. Liste nur diese Zeit.

**▦ Layout anpassen:** Bereiche am Griff ⠿ verschieben, an der Seite schmaler oder breiter ziehen (z. B. zwei nebeneinander), Bereiche ein- und ausschalten. **Fertig** speichert, **↺ Zurücksetzen** stellt die Standardanordnung wieder her. Die Höhe richtet sich nach dem Inhalt. Am Handy stehen alle Bereiche untereinander. Die Anordnung gilt für diesen Browser.

„Sensoren im Zeitraum“ ist anfangs ausgeblendet: Sensor-Ereignisse („als Ereignis“) stehen schon in der Tabelle, „nur festhalten“ (z. B. Fernseher) steht als 📡-Hinweis bei jeder Störung, die in die Zeit fällt.

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

GasLighter erkennt die **Art** eines Geräuschs mit einer kleinen KI, die komplett auf deinem Home-Assistant-Rechner läuft (YAMNet, keine Cloud). Zusätzlich lernt die App deine eigenen **Tonprofile**.

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

Einschalten: ⚙ Einstellungen → Allgemein → **Geräuschart erkennen (lokale KI)** (Standard an).

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

- **KI-Fingerabdruck durchgehend speichern** (⚙ → Speichern & Ton, Standard an, je Gerät): etwa 2–10 MB pro Gerät und Tag. Darunter steht, ob er läuft und wie viele Sekunden heute gespeichert wurden.
- **KI-Fingerabdruck speichern** (⚙ → Allgemein): zusätzlich der volle Fingerabdruck je Störung, für „Neu bewerten“.

> Wird der Rechner zu langsam, kommen die Geräte reihum dran; dann fehlt der Fingerabdruck an einzelnen Stellen. Die KI kann irren, besonders bei sehr leisen Geräuschen.

## 6. Geräte

Unter ⚙ Einstellungen → **Geräte** → Quellen stehen alle Mikrofone. Bis zu 9 Geräte sind möglich.

### Server-Mikrofon

Das Mikrofon am Home-Assistant-Rechner. Unter **Mikrofon** wählst du Eingang, Buchse und Lautstärke. Meist „Standard“ lassen. **Brummfilter** (50 Hz in Europa) entfernt Netzbrummen.

### Handy als Mikrofon

> **🔒 Pro:** Handys, Stream-URLs und IP-Kameras sind externe Geräte und gehören zu GasLighter Pro. Das Server-Mikrofon ist immer frei.

- **Handy (Browser)**: „+ Handy (Browser)“, QR-Code scannen, Seite in Chrome öffnen, Zertifikatswarnung bestätigen, **Start**. Der Bildschirm muss an bleiben (Ladegerät). Der Link ist geheim und gehört nur zu diesem Handy.
- **Stream (z. B. App „IP Webcam“)**: „+ Handy-App / Stream-URL“, Adresse `http://HANDY-IP:8080/audio.wav`. Läuft auch mit ausgeschaltetem Bildschirm. Mit Login: Benutzername und Passwort in die eigenen Felder.
- Der Handy-Port ist standardmäßig **18443** (Add-on → Netzwerk, „8443/tcp“).

### Video

Bei Streams lässt sich **🎥 Video aufnehmen** einschalten: Bei einer Störung entsteht eine mp4-Datei **ohne Ton**. Ohne Störung wird nichts gespeichert. Qualität und Speicherort unter Speichern & Ton → Video & Speicherort.

> Kameraaufnahmen in Wohnungen können nach § 201a StGB problematisch sein – nur eigene Räume, keine fremden Personen filmen.

### Handy als Bewegungsmelder

Ein als Gerät eingerichtetes Handy kann zusätzlich zum Mikrofon als **Bewegungsmelder** dienen – wie ein Bewegungs- oder Vibrationssensor in Home Assistant:

- **🫨 Erschütterung** (Beschleunigungssensor): Das Handy liegt flach auf dem Boden, einem Tisch oder an der Wand und meldet Vibrationen – z. B. Trampeln, Bass, der durch die Decke kommt, Türenknallen oder Möbelrücken. Das belegt Körperschall, den man nicht nur hört, sondern spürt.
- **🏃 Bewegung im Kamerabild**: Die Kamera des Handys erkennt Bewegung im Bild (z. B. im Treppenhaus). Plötzliche Helligkeitsänderungen (Licht an/aus) werden herausgerechnet.

**Einschalten:** ⚙ Einstellungen → Geräte → Karte des Handys → **Handy als Bewegungsmelder** → „Erschütterung“ und/oder „Bewegung im Kamerabild“ anhaken, **Empfindlichkeit** wählen (hoch, mittel, niedrig). Danach am Handy die Seite neu laden und **Start** tippen. Der Browser fragt nach der Kamera bzw. (iPhone) nach „Bewegung und Ausrichtung“.

> **Datenschutz:** Ausgewertet wird nur auf dem Handy. Gesendet werden nur Zahlen (Stärke der Erschütterung, Anteil der veränderten Bildpunkte) – **kein Bild und kein Video**. Das Vorschaubild sieht man nur auf dem Handy selbst.

**Was dabei entsteht:**
- Am Handy und in der Geräteleiste blinkt 🫨 bzw. 🏃, solange ausgelöst ist.
- Jede Erschütterung bzw. Bewegung wird mit Beginn, Ende und Spitze gespeichert (`bewegung.csv` im Datenordner). Sie gilt bis 20 s nach dem letzten Auslösen als „an“.
- Im Reiter **Protokolle** steht die Liste „Erschütterung und Bewegung im Zeitraum“; ein Klick zeigt die Stelle im Verlauf. Das Lärmprotokoll enthält eine eigene Tabelle.
- In **Home Assistant** erscheint je Handy ein Sensor „Erschütterung“ (Vibration) bzw. „Bewegung“ (Bewegung) – nutzbar in Automationen und in den Regeln, z. B. „nur festhalten“, damit es bei jeder Störung und im Tagesverlauf steht.

Gehört zu den externen Geräten und damit zu GasLighter Pro.

### Geräte-Karte

- **Name**, **aktiv**, **Verstärkung (dB)** und Brummfilter.
- **⚙ Pegel & Schwelle**: eigene Einstellungen nur für dieses Gerät.
- **📏 Eigene Referenzlinien**: z. B. „Fernseher −70 dB“, erscheinen in allen Grafiken dieses Geräts.
- **Protokolllisten**: Störungen dieses Geräts automatisch einer Liste zuordnen, auf Wunsch nur zu bestimmten Uhrzeiten.
- Aus einer Sicherung übernommene Geräte, die nicht erreichbar waren, sind ausgeschaltet und tragen den Hinweis „bitte prüfen“.

### Geräte einpegeln

Damit Pegel verschiedener Geräte vergleichbar sind:

1. Alle Mikrofone nebeneinander legen.
2. **Geräte einpegeln** → mitmessende Geräte anhaken (mindestens zwei) → Start.
3. 5 s Ruhe, dann ein gleichmäßiges Geräusch (z. B. Rauschen aus einem Handy-Lautsprecher, mindestens 10 dB lauter).

Jedes Gerät bekommt eine eigene Verstärkung, sodass alle beim selben Geräusch denselben Wert zeigen. Jede Messung wird festgehalten und erscheint im Lärmprotokoll. Ändert sich die Verstärkung später von Hand, steht beim Gerät „⚠ seit dem Einpegeln geändert“.

### Mehrere Räume vergleichen

Löst ein Gerät aus, speichern alle anderen für denselben Zeitraum mit („Bei einer Störung alle Geräte mitspeichern“). Im Ereignis-Fenster zeigt **Vergleich der Geräte** die Spitze je Gerät. Ein Fernseher im Wohnzimmer ist dort am lautesten und hat viele Höhen; Klopfen über Decke und Wände ist in allen Räumen ähnlich und tief.

## 7. Home Assistant

GasLighter arbeitet mit Home Assistant zusammen: Regeln fragen Zustände ab (Fernseher an, Waschmaschine läuft, Sensor ausgelöst), und über MQTT meldet die App Störungen, Prüfsummen und Schalter zurück.

### Regeln: pausieren oder festhalten

⚙ Einstellungen → Zeiten & Pausen → **Home Assistant: pausieren oder festhalten** → **Regel hinzufügen**.

| Feld | Bedeutung |
|---|---|
| Entität | z. B. `media_player.fernseher`, `binary_sensor.vibration_wand` |
| Gerät | für welches Mikrofon die Regel gilt (oder alle) |
| **Name** | Unter diesem Namen wird die Regel festgehalten, z. B. „Erschütterung Wand“. Leer = Name aus Home Assistant. |
| Aktion | **nur festhalten** (weiter aufnehmen und mitschreiben, z. B. eigener Fernseher), **als Ereignis** (wie festhalten, zusätzlich eigene Zeile in der Ereignistabelle, z. B. Tür- oder Vibrationssensor) oder **pausieren** (in dieser Zeit nicht aufnehmen) |
| an bei / pausieren bei | `on, playing` = einer davon, `!off` = alles außer off, `>1` = Zahl größer 1 |
| Nachlauf, höchstens | nur bei „pausieren“: so lange danach weiter pausieren, Höchstdauer |

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

Ist MQTT eingerichtet, erscheint in Home Assistant das Gerät **GasLighter** mit:

- Schalter **Aufzeichnung**, **Manuell erfassen (außerhalb der Zeit)**, Zahl **Pause (Minuten)**, Tasten **Pause 15 min**, **Pause 1 h**, **Fortsetzen**, Sensor **Pause bis**.
- Je Gerät: Ereignis **Störung (Auslöser)** (beginn, ende, erkannt – mit Spitze, Dauer, Art, Profil), Geräte-Auslöser für Automationen, Sensor „Letzte Geräuschart“ und stündlich die aktuelle **Prüfsumme** (in Home Assistant unabhängig gespeichert).

Beispiel – 10 Minuten Pause, wenn die Katzentoilette reinigt:

```yaml
automation:
  - alias: "GasLighter pausieren, wenn das Katzenklo reinigt"
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

Mit MQTT meldet das Add-on zwei Elemente am Gerät „GasLighter“:

- **Störung / Notiz erfassen**: Textfeld. Text eingeben, Enter drücken, schon ist die Notiz mit der aktuellen Uhrzeit gespeichert. Das Feld leert sich danach.
- **Störung jetzt markieren**: Knopf. Ein Tipp legt sofort eine Notiz „Störung (Home Assistant)“ an, ohne Text.

Beide legst du auf ein beliebiges Dashboard (z. B. als Karte „Entitäten“). Liegt kurz davor eine Störung, wird die Notiz ihr zugeordnet, genau wie bei der Notizleiste im Live-Bild.

### Keine Störung melden (Graph läuft weiter)

Manchmal soll eine Störung nicht gemeldet werden, der Graph aber trotzdem weiterlaufen, zum Beispiel wenn du selbst die Tür öffnest.

- **In einer Regel:** Wähle bei der Aktion **„keine Störung melden“**. Solange die Bedingung gilt und für den **Nachlauf** (z. B. 10 Minuten), entsteht keine Störung. Der Graph wird weiter aufgezeichnet, es gibt keine Lücke.
- **Als Knopf im Dashboard:** Am Gerät „GasLighter“ gibt es **„Keine Störung melden (Dauer starten)“**, **„Störungen wieder melden“**, die einstellbare **Dauer** (1–240 Minuten, Standard 10) und **„Keine Störungsmeldung bis“**. Lege sie auf dein Dashboard. Ein Tipp auf den Knopf startet die eingestellte Dauer.

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

Oben auf der Seite (wird nicht mitgedruckt) wählst du **Tagesgrafik** (Standard an) und **Grafik je Störung** (Standard aus): eine kleine Grafik mit Umfeld unter jeder Störung, die eine Notiz hat oder aus der gewählten Liste stammt (höchstens 300).

Im Browser drucken oder als PDF speichern. Das ausgedruckte Dokument heißt immer „Lärmprotokoll“.

> Pegel sind relative dBFS-Werte, keine geeichte Messung in dB(A). Tonaufnahmen kommen nie ins Protokoll. Keine Rechtsberatung.

### Verlauf drucken (Notenblatt)

Im Verlauf **🖨 Drucken**:

- **Zeitraum**: von–bis oder Schnellwahl „Sichtbarer Ausschnitt“, „Zeitraum des Berichts“, „Alle Daten“.
- **Zeit je Zeile**: 1 min bis 1 h (Standard 10 min – ein ganzer Tag sind 144 Zeilen).
- **Geräte** untereinander, **Inhalt** (Pegelspur, Spektrogramm, Störungs-Infos und Notizen), **Zeilen ohne Aufzeichnung zusammenfassen** (Standard an).
- **Skala**: gleich für alle Zeilen (vergleichbar) oder je Zeile angepasst (mehr Einzelheiten); **A4 quer** oder **hoch**.

Der Dialog schätzt Zeilen und Seiten. **Vorschau öffnen** baut die Seiten in einem neuen Fenster auf; dort **Drucken** oder als PDF speichern. Eine aktive Prüf-Schwelle wird mitgedruckt, mit Zählung je Zeile.

## 9. Sicherung, Import und Export

### Sicherung herunterladen

⚙ Einstellungen → Allgemein → **Sicherung der ganzen App** → **⬇ Sicherung herunterladen**. Die ZIP-Datei enthält alles: Einstellungen, Geräte, Zeitprofile, Regeln, `log.csv` und alle Protokolldateien, Tagesaufzeichnungen mit Prüfsummen, KI-Ergebnisse, Tonprofile, Notizen, Kommentare zu Unterbrechungen, benannte Bereiche, Listen, Videos und – falls gespeichert – Ton.

> Die Datei kann groß werden (Hunderte MB). Am besten regelmäßig herunterladen und an einem anderen Ort aufbewahren.

Zum Weiterverarbeiten gibt es außerdem `log.csv` (Reiter Protokolle), die Notizen als CSV (📝 Alle Notizen) und das Lärmprotokoll als PDF.

### Sicherung einspielen

> **🔒 Pro:** Der erste Import ist kostenlos (z. B. für den Umzug), weitere Importe gehören zu GasLighter Pro. Das Herunterladen einer Sicherung ist immer frei.

1. **📂 Sicherung wählen** und **Sicherung prüfen …** – die Datei wird hochgeladen und angesehen, noch nichts verändert.
2. Die Vorschau zeigt Version und Datum der Sicherung und – mit „Einstellungen und Geräte übernehmen“ – jedes Gerät aus der Sicherung:
   - **gibt es hier schon** (wird ersetzt) oder **neu**,
   - **bereit**, **Handy** (verbindet sich, sobald es die App öffnet) oder **nicht erreichbar** (wird ausgeschaltet übernommen, mit Hinweis „bitte prüfen“).
   - Geräte, die nur hier eingerichtet sind, **bleiben unverändert**.
   - Gibt es das Mikrofon der Sicherung hier nicht, bleibt das bisherige eingestellt.
3. Häkchen setzen oder entfernen und **Jetzt einspielen**.

Danach steht ein Bericht da: neue Dateien, zusammengeführte Tage, übersprungene Tage und übernommene Geräte.

### Tägliche Sicherung auf Netzlaufwerk, NAS oder USB

> **🔒 Pro:** Die tägliche Sicherung und „Platz sparen“ gehören zu GasLighter Pro. **„⬇ Sicherung herunterladen“ und `log.csv` bleiben immer frei.** Läuft Pro ab, hält die tägliche Sicherung an; schon ausgelagerte Tage bleiben lesbar.

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

### Platz sparen

Mit **„Platz sparen: alte Daten nur im Ziel behalten“** werden Dateien, die älter sind als „Löschen nach (Tagen)“ und geprüft im Ziel liegen, hier durch einen Verweis auf die Kopie ersetzt. **Protokolle, Verlauf, Druck und Prüfsummen-Kette funktionieren weiter** – sie lesen diese Tage aus dem Ziel. Schläft das Netzlaufwerk, dauert das erste Laden etwas länger („Netzlaufwerk wacht evtl. gerade auf“). Ist es gar nicht erreichbar, fehlen diese alten Tage, bis es wieder da ist. Einstellungen, `log.csv` und die Daten der letzten Tage bleiben immer hier.

Ist zusätzlich **„Alte Aufnahmen automatisch löschen“** eingeschaltet, löscht GasLighter bei eingestelltem Ziel nur noch, was geprüft im Ziel liegt.

### Was beim Einspielen passiert

- **Nichts wird doppelt und nichts überschrieben**: vorhandene Störungen, Notizen und Listen bleiben, nur Fehlendes kommt dazu. Mehrmals einspielen ist unschädlich.
- **Tage, die es schon gibt** (z. B. „heute“ nach einer Neuinstallation): Die fehlenden Minuten werden ergänzt. Die Prüfsummen-Kette bleibt prüfbar – der eingespielte Teil bekommt einen eigenen Abschnitt, und unter „Unterbrechungen“ steht „Import …: um N Minuten ergänzt“. Überschneiden sich die Zeiten mit anderen Daten, wird der Tag übersprungen und im Bericht genannt.
- **Geräte, die es nicht mehr gibt**: Ihre Daten werden trotzdem eingespielt und sind als „(ehemalig)“ im Verlauf, im Gerätefilter und im Druck auswählbar.
- Speicherorte (Ausgabe- und Clip-Ordner) bleiben die dieses Systems.

### Zurücksetzen

⚙ → Allgemein → **Zurücksetzen**: wahlweise Messdaten & Störungen, Notizen & Listen, Tonprofile oder Einstellungen auf Standard. Geräte und Verbindungen bleiben immer. Vorher wird eine Sicherung angeboten.

### Suchverzeichnis

GasLighter führt ein **Suchverzeichnis** (SQLite-Datei `suchindex.sqlite` im App-Datenordner). Es beschleunigt Lärmprotokolle über Wochen und Monate:

- **Kettenprüfung je Tag:** Das Ergebnis wird mit einer SHA-256-Prüfsumme über den *Inhalt* aller Dateien des Tages gespeichert. Ändert sich auch nur ein Byte, wird der Tag neu geprüft – die Prüfung ist genauso streng wie ohne Verzeichnis.
- **Verdichtete Tagesspuren** (je 10 Sekunden) für die Grafiken im Lärmprotokoll.

Das Verzeichnis enthält nur abgeleitete Daten, ändert nie Aufzeichnung, Datenkette oder Störungen, ist nicht in der Sicherung und füllt sich nach dem Start langsam im Hintergrund. **Einstellungen → Allgemein → Sicherung → Neu aufbauen** leert es; es baut sich danach von selbst wieder auf. Fehlt es oder ist es beschädigt, arbeitet GasLighter ohne – nur langsamer.

## 10. Unterbrechungen, Datenkette und Updates

### Unterbrechungen

Läuft das Add-on nicht (Stromausfall, Home Assistant neu gestartet, Update über den Add-on-Store), fehlt die Aufnahme. GasLighter merkt sich das beim nächsten Start und zeigt es in Protokolle unter der Zusammenfassung:

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

**Ohne Aufnahmelücke:** den Ordner `gaslighter` aus der Update-Zip per Samba nach `\\homeassistant\share\gaslighter_update\` kopieren (vorhandene Dateien überschreiben). Nach 10–20 s startet nur das Programm neu; die Aufnahme läuft weiter und wird nachgeliefert. Startet die neue Fassung nicht, nimmt das Add-on automatisch wieder die vorige.

**Volle Installation** (nur wenn eine Version es verlangt, z. B. neuer Name oder Watchdog): den Ordner aus der vollen Zip nach `\\homeassistant\addons\` kopieren und das Add-on in Home Assistant neu erstellen. Das gibt eine kurze Lücke.

Jeder Start, jedes Update und jede Unterbrechung steht mit Uhrzeit und Version in Protokolle und im Lärmprotokoll.

## 11. Einstellungen von A bis Z

Ganz oben wählst du **Alle Geräte** oder ein einzelnes Gerät. Beim Gerät lassen sich mit „Eigene Einstellungen für dieses Gerät“ abweichende Werte festlegen (Schwelle, Mindestdauer, Aufnahmezeit, Speichern). Die Leiste oben zeigt live Pegel, Hintergrund, Schwelle und die **Vorschau** (lila) deiner noch nicht gespeicherten Einstellungen. ⓘ erklärt jede Einstellung; „Hilfe anzeigen“ blendet die Texte aus.

### Geräte

- **Quellen (Mikrofone)** – siehe Geräte.
- **Geräte einpegeln** – siehe Einpegeln.
- **Mikrofon** – Eingang am Server, Buchse, Lautstärke, Tonqualität (16000 Hz reicht für Klopfen).

### Erkennung

### Wann gilt etwas als Störung?

> **🔒 Pro:** Ohne Pro sind diese Werte nur zum Ansehen; GasLighter arbeitet mit den Standardwerten. Ändern lassen sie sich mit GasLighter Pro.

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

**Tonprofile** – siehe KI. **Andere Werte zu bestimmten Uhrzeiten** (Zeitprofile) – z. B. nachts empfindlicher, allgemein oder je Gerät.

### Zeiten & Pausen

- **Wann wird überwacht?** – Überwachen ab / bis (beide leer = rund um die Uhr, über Mitternacht möglich). Außerhalb davon wird nichts gezählt; über die Anzeige oben lässt sich trotzdem erfassen.
- **Home Assistant: pausieren oder festhalten** – siehe Home Assistant.
- **Notizen & Protokoll** – Ruhezeit ab / bis (üblich 22:00–6:00), Sonntag ganztägig Ruhezeit. Notizen und Störungen in der Ruhezeit bekommen 🌙.

### Speichern & Ton

### Aufnahme der Störung

| Einstellung | Bedeutung |
|---|---|
| Umfeld (s) | so viele Sekunden vor und nach der Störung werden beim Ansehen gezeigt |
| … mit Ebenen | tief/mittel/hoch, Frequenz für den ganzen Tag (+1–2 MB pro Gerät und Tag) |
| … mit Spektrum | Spektrogramm für jeden Moment (+3–8 MB pro Gerät und Tag) |
| KI-Fingerabdruck durchgehend speichern | siehe KI-Fingerabdruck; darunter steht, ob er läuft |
| Alte Aufnahmen automatisch löschen / nach Tagen | aus = es wird nie etwas gelöscht |

### Echten Ton speichern (nicht empfohlen)

Standard **aus**. Eingeschaltet wird zu jeder Störung zusätzlich eine WAV-Datei gespeichert. **Ton nur ohne erkannte Stimmen** (empfohlen) verhindert das Speichern, sobald die KI irgendwo Stimmen erkennt. Lies vorher Rechtliches.

### Video & Speicherort

Ordner für Lärmspuren, Video-Breite, Bilder pro Sekunde, Videoqualität.

### Allgemein

- **Allgemein** – Geräuschart erkennen (lokale KI), KI-Fingerabdruck speichern, Gruppe: höchste Pause, Notiz zuordnen, Sprache.
- **Sicherung der ganzen App** – siehe Sicherung.
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

- „Die KI-Erkennung ist ausgeschaltet“: ⚙ → Allgemein → **Geräuschart erkennen** einschalten.
- „KI-Modell nicht gefunden“: das Add-on einmal mit der **vollen Zip** neu installieren (Update-Zips enthalten das Modell nicht).
- „kein Fingerabdruck an dieser Stelle“: An dieser Sekunde wurde nichts gespeichert (zu leise oder Rechner ausgelastet). Prüfe in ⚙ → Speichern & Ton, ob der Fingerabdruck läuft.

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

## 14. GasLighter Pro

GasLighter ist kostenlos. **Aufzeichnung, Live-Ansicht, Protokolle, Lärmprotokoll zum Drucken, Export (`log.csv`, Notizen) und das Erstellen einer Sicherung** sind immer frei – ohne Zeitlimit und ohne Werbung.

Die Jahreslizenz **GasLighter Pro** schaltet zusätzlich frei:

| Funktion | Ohne Pro | Mit Pro |
|---|---|---|
| Import einer Sicherung | einmal kostenlos (z. B. Umzug) | beliebig oft |
| Erweiterte Einstellungen der Erkennung (Reiter „Erkennung“ → „Wann gilt etwas als Störung?“) | nur ansehen, Standardwerte | frei einstellbar, auch je Gerät und in Zeitprofilen |
| Externe Geräte: Handy im Browser, Handy-App / Stream-URL, IP-Kamera | gesperrt | bis zu 8 zusätzliche Geräte |
| Handy als Bewegungsmelder (Erschütterung, Bewegung im Bild) | gesperrt | ✔ |
| Tägliche Sicherung auf Netzlaufwerk/NAS/USB und „Platz sparen“ (Sicherung) | „⬇ Sicherung herunterladen“ von Hand | jeden Tag automatisch, geprüft |

Das Server-Mikrofon (am Home-Assistant-Rechner) funktioniert immer ohne Pro.

### Kaufen

⚙ Einstellungen → Allgemein → **GasLighter Pro** → **🛒 Pro kaufen** öffnet die Seite von GasLighter auf gsimulations.de. Die Lizenz gilt **1 Jahr ab Kauf** für **1 Home-Assistant-Installation**. Sie verlängert sich **nicht** automatisch – es gibt kein Abo. Nach dem Kauf kommt der Lizenzschlüssel per E-Mail.

### Schlüssel eintragen

1. ⚙ Einstellungen → Allgemein → **GasLighter Pro**.
2. Den Schlüssel aus der E-Mail vollständig einfügen. Er beginnt mit `GL1-`; Leerzeichen und Zeilenumbrüche stören nicht.
3. **🔑 Aktivieren**. Danach steht dort „Pro aktiv – gültig bis …“.

Der Schlüssel wird **ohne Internet** geprüft – GasLighter sendet nichts an G-Simulation. Er wird in der Sicherung **nicht** mitgespeichert; nach einer Neuinstallation einfach wieder eintragen.

An gesperrten Stellen steht **🔒 Pro**. Ein Klick darauf erklärt die Funktion und bietet „Pro kaufen“ und „Schlüssel eintragen“ an.

### Ablauf und Verlängern

14 Tage vor dem Ablauf erscheint oben einmal ein Hinweis mit „Verlängern“. Nach dem Ablauf läuft alles Kostenlose weiter, aufgezeichnete Daten bleiben vollständig erhalten:

- Externe Geräte nehmen nicht mehr auf (sie bleiben eingerichtet und laufen mit einem neuen Schlüssel sofort weiter).
- Die erweiterten Einstellungen behalten ihre Werte, lassen sich aber nicht mehr ändern.
- Weitere Importe brauchen wieder Pro.

Zum Verlängern eine neue Lizenz kaufen und den neuen Schlüssel eintragen.

### Umzug auf einen neuen Rechner

Sicherung auf dem alten Rechner herunterladen, GasLighter auf dem neuen installieren und die Sicherung einspielen – der **erste Import ist kostenlos**. Danach den Pro-Schlüssel wieder eintragen.

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

GasLighter listens continuously and writes a **noise log**: when it was how loud, for how long and what kind of sound – with checksums so nobody can change the data unnoticed. **No sound is stored**, only measurements.

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

- Regularly download a backup under ⚙ Settings → General → **Download backup**. See Backup.
- Updates without a recording gap: copy the new folder to `\\homeassistant\share\gaslighter_update\`. See Updates.

> **Important:** GasLighter is a memory aid and documentation, not a calibrated dB(A) measurement. For landlords, property managers or authorities what counts most is: regular, traceable, with your own notes. See Noise log.

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
| Mouse wheel or touchpad = zoom time | spread two fingers = zoom time |
| Drag or swipe sideways = move in time | swipe horizontally = move, vertically = scroll the page |
| Shift + drag = select a range and zoom in | − / + |
| Shift + wheel or wheel over the dB labels = zoom height (bottom-aligned) | “Auto” |
| Double click = back to live | Double tap = back to live |
| Hover over a disturbance = details | Tap a disturbance = details |

Further back than the last 10 minutes the chart shows the **whole day** from the day recording (time window 1 h, 6 h or “Today”).

### 📝 Note now

For what you hear right now – just start typing or tap tags (upstairs, downstairs, knocking, bass, woke up …).

- **Without a time of its own**: if there was a disturbance shortly before (setting “Assign note”, default 5 min), the note belongs to it. The bar shows beforehand where it goes.
- **still going**: the note gets a period from the first input until saving.
- **From / to and witness** are always shown right in the area; leave them empty for “automatic” (time at saving).
- **Only tags, no text?** GasLighter builds a sentence from them when saving, e.g. “Clear footsteps in the stairwell”. You can edit it later.

**Detach (Pro):** **⧉** next to the title detaches the note area into its own small window. In Chrome and Edge it stays on top of other programs (e.g. over a game or film), otherwise it is a normal extra window. **Bring back** or closing the window puts it back.
- Ctrl + Enter saves. On a phone the bar starts collapsed.

### 🏷 Mark range

1. Tap “🏷 Mark range” – a hint with **Done** appears above the chart.
2. Drag across the range horizontally (0.15 s to 2 min).
3. Tap an **existing type** (sound profile 🧩 or named range 🏷) or enter a new name – same name = same type, the AI learns from it. See AI.

### Events today

The list at the bottom shows all disturbances of the day (all devices or the selected one). A click opens the disturbance, see Event window. Choose columns via ⚙. On a phone the entries appear as cards.

## 3. Logs

The **Logs** tab shows a period completely: summary, week strip, history of all devices, statistics and the list of all disturbances.

### Period and filters

- **Monitoring time** (the set monitoring hours, e.g. 22–6), **Today**, **Yesterday**, **7 days**, **30 days** or **From–to**. ‹ › moves by a whole period.
- **Source / device**, **Type** (multiple choice, e.g. knocking + footsteps) and **List** filter everything below. Devices that no longer exist but still have data are listed as “(former)”.
- **🖨 Noise log** creates the noise log for period, device and list, **⬇ Image (SVG)** an image. See Printing.

### Arranging sections (dashboard)

Live and Logs consist of **sections** (overview, interruptions, history, events by hour, per day, events in the period, notes and motion, sensors in the period). Each section has a bar at the top:

- **▾ / ▸** collapses and expands (also double-click on the bar).
- **✕** hides it. Switch it on again under **▦ Customise layout**.
- **⌖ visible range only** (events, sensors): only shows what is currently visible in the history – drag e.g. 20:00–22:00 in the history and the table or list shows only that time.

**▦ Customise layout:** move sections by the ⠿ handle, drag the side to make them narrower or wider (e.g. two side by side), switch sections on and off. **Done** saves, **↺ Reset** restores the default arrangement. The height follows the content. On phones all sections are stacked. The arrangement applies to this browser.

“Sensors in the period” is hidden at first: sensor events (“as event”) are already in the table, “only record state” (e.g. TV) appears as a 📡 hint on every disturbance that falls into that time.

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

GasLighter recognises the **type** of a sound with a small AI that runs entirely on your Home Assistant computer (YAMNet, no cloud). In addition the app learns your own **sound profiles**.

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

Switch on: ⚙ Settings → General → **Recognize sound type (local AI)** (on by default).

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

- **Store AI fingerprint continuously** (⚙ → Storage & sound, on by default, per device): about 2–10 MB per device and day. Below it you see whether it is running and how many seconds were stored today.
- **Store AI fingerprint** (⚙ → General): additionally the full fingerprint per disturbance, for “Re-evaluate”.

> If the computer becomes too slow, the devices take turns; then the fingerprint is missing at some spots. The AI can be wrong, especially with very quiet sounds.

## 6. Devices

All microphones are under ⚙ Settings → **Devices** → Sources. Up to 9 devices are possible.

### Server microphone

The microphone on the Home Assistant computer. Under **Microphone** you choose input, jack and volume. Usually leave it on “Default”. The **hum filter** (50 Hz in Europe) removes mains hum.

### Phone as a microphone

> **🔒 Pro:** phones, stream URLs and IP cameras are external devices and part of GasLighter Pro. The server microphone is always free.

- **Phone (browser)**: “+ Phone (browser)”, scan the QR code, open the page in Chrome, accept the certificate warning, **Start**. The screen must stay on (charger). The link is secret and belongs to this phone only.
- **Stream (e.g. the app “IP Webcam”)**: “+ Phone app / stream URL”, address `http://PHONE-IP:8080/audio.wav`. Also works with the screen off. With a login: user name and password in their own fields.
- The phone port is **18443** by default (add-on → Network, “8443/tcp”).

### Video

For streams you can switch on **🎥 Record video**: on a disturbance an mp4 file **without sound** is created. Nothing is stored without a disturbance. Quality and folder under Storage & sound → Video & storage.

> Camera recordings in homes can be problematic (§ 201a StGB in Germany) – only film your own rooms and no other people.

### Phone as a motion sensor

A phone set up as a device can additionally act as a **motion sensor** – like a motion or vibration sensor in Home Assistant:

- **🫨 Vibration** (accelerometer): the phone lies flat on the floor, a table or against the wall and reports vibrations – e.g. stomping, bass coming through the ceiling, slamming doors or moving furniture. This documents structure-borne noise you feel, not just hear.
- **🏃 Motion in the camera picture**: the phone camera detects motion in the picture (e.g. in the stairwell). Sudden brightness changes (light on/off) are compensated.

**Switch on:** ⚙ Settings → Devices → card of the phone → **Phone as motion sensor** → tick "Vibration" and/or "Motion in camera picture", choose the **sensitivity** (high, medium, low). Then reload the page on the phone and tap **Start**. The browser asks for the camera or (iPhone) for "motion and orientation".

> **Privacy:** everything is evaluated on the phone. Only numbers are sent (vibration strength, share of changed pixels) – **no picture and no video**. The preview is only visible on the phone itself.

**What you get:**
- On the phone and in the device bar 🫨 or 🏃 blinks while triggered.
- Each vibration or motion is stored with start, end and peak (`bewegung.csv` in the data folder). It counts as "on" until 20 s after the last trigger.
- The **Reports** tab lists "Vibration and motion in the period"; a click shows the spot in the history. The noise report contains its own table.
- In **Home Assistant** each phone gets a "Vibration" or "Motion" sensor – usable in automations and in the rules, e.g. "only record state", so it appears with every disturbance and in the daily chart.

Part of the external devices and therefore of GasLighter Pro.

### Device card

- **Name**, **active**, **gain (dB)** and hum filter.
- **⚙ Level & threshold**: own settings for this device only.
- **📏 Own reference lines**: e.g. “TV −70 dB”, shown in all charts of this device.
- **Log lists**: assign disturbances of this device to a list automatically, optionally only at certain times.
- Devices taken over from a backup that were not reachable are switched off and marked “please check”.

### Level-match devices

So that levels of different devices are comparable:

1. Put all microphones side by side.
2. **Level-match devices** → tick the devices to measure (at least two) → Start.
3. 5 s of quiet, then a steady sound (e.g. noise from a phone speaker, at least 10 dB louder).

Each device gets its own gain so that all show the same value for the same sound. Every measurement is recorded and listed in the noise log. If the gain is changed by hand later, the device shows “⚠ changed since level-matching”.

### Comparing rooms

When one device triggers, all others store the same period too (“On a disturbance store all devices”). In the event window **Device comparison** shows the peak per device. A TV in the living room is loudest there and has many highs; knocking through ceiling and walls is similar and low in all rooms.

## 7. Home Assistant

GasLighter works together with Home Assistant: rules read states (TV on, washing machine running, sensor triggered), and via MQTT the app reports disturbances, checksums and switches back.

### Rules: pause or record state

⚙ Settings → Times & pauses → **Home Assistant: pause or record state** → **Add rule**.

| Field | Meaning |
|---|---|
| Entity | e.g. `media_player.tv`, `binary_sensor.vibration_wall` |
| Device | which microphone the rule applies to (or all) |
| **Name** | The rule is recorded under this name, e.g. “wall vibration”. Empty = name from Home Assistant. |
| Action | **only record state** (keep recording and write it down, e.g. your own TV), **as event** (like record state, plus its own row in the events table, e.g. door or vibration sensor) or **pause** (do not record during that time) |
| on when / pause when | `on, playing` = one of them, `!off` = everything except off, `>1` = number above 1 |
| Delay, at most | only with “pause”: keep pausing this long afterwards, maximum duration |

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

With MQTT set up, Home Assistant shows the device **GasLighter** with:

- Switch **Recording**, **Record manually (outside hours)**, number **Pause (minutes)**, buttons **Pause 15 min**, **Pause 1 h**, **Resume**, sensor **Paused until**.
- Per device: event **Disturbance (trigger)** (start, end, detected – with peak, duration, type, profile), device triggers for automations, sensor “Last sound type” and hourly the current **checksum** (stored independently in Home Assistant).

Example – pause for 10 minutes while the litter box cleans:

```yaml
automation:
  - alias: "Pause GasLighter while the litter box cleans"
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

With MQTT the add-on adds two elements to the "GasLighter" device:

- **Log disturbance / note**: text field. Type text, press Enter, and the note is saved with the current time. The field clears afterwards.
- **Mark disturbance now**: button. One tap creates a note "Disturbance (Home Assistant)" immediately, without text.

Put both on any dashboard (for example in an "Entities" card). If a disturbance was detected just before, the note is attached to it, exactly like the note bar in the live view.

### No disturbance reports (graph keeps recording)

Sometimes a disturbance should not be reported while the graph keeps recording, for example when you open the door yourself.

- **In a rule:** choose the action **"no disturbance reports"**. While the condition holds and for the **delay** afterwards (for example 10 minutes), no disturbance is created. The graph keeps recording, with no gap.
- **As a dashboard button:** the "GasLighter" device has **"Start: no disturbance reports"**, **"Report disturbances again"**, an adjustable **duration** (1–240 minutes, default 10) and **"No disturbance reports until"**. Put them on your dashboard. One tap starts the set duration.

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

At the top of the page (not printed) choose **Day chart** (on by default) and **Chart per disturbance** (off by default): a small chart with context below every disturbance that has a note or comes from the chosen list (at most 300).

Print in the browser or save as PDF. The printed document is always titled “Lärmprotokoll” (noise log).

> Levels are relative dBFS values, not a calibrated dB(A) measurement. Sound recordings never go into the log. Not legal advice.

### Print history (score sheet)

In the history **🖨 Print**:

- **Period**: from–to or quick choice “Visible section”, “Period of the report”, “All data”.
- **Time per line**: 1 min to 1 h (default 10 min – a whole day is 144 lines).
- **Devices** below each other, **content** (level trace, spectrogram, disturbance info and notes), **Merge lines without recording** (on by default).
- **Scale**: the same for all lines (comparable) or fitted per line (more detail); **A4 landscape** or **portrait**.

The dialog estimates lines and pages. **Open preview** builds the pages in a new window; print there or save as PDF. An active test threshold is printed along, with a count per line.

## 9. Backup, import and export

### Download a backup

⚙ Settings → General → **Backup of the whole app** → **⬇ Download backup**. The ZIP file contains everything: settings, devices, time profiles, rules, `log.csv` and all log files, day recordings with checksums, AI results, sound profiles, notes, comments on interruptions, named ranges, lists, videos and – if stored – sound.

> The file can get large (hundreds of MB). Download it regularly and keep it in another place.

For further processing there are also `log.csv` (Logs tab), the notes as CSV (📝 All notes) and the noise log as PDF.

### Restore a backup

> **🔒 Pro:** the first import is free (e.g. when moving), further imports are part of GasLighter Pro. Downloading a backup is always free.

1. **📂 Choose backup** and **Check backup …** – the file is uploaded and examined, nothing is changed yet.
2. The preview shows version and date of the backup and – with “Take over settings and devices” – every device from the backup:
   - **already here** (will be replaced) or **new**,
   - **ready**, **phone** (connects as soon as it opens the app) or **not reachable** (taken over switched off, marked “please check”).
   - Devices set up only here **stay unchanged**.
   - If the backup's microphone does not exist here, the current one stays selected.
3. Set or clear the ticks and **Restore now**.

Afterwards a report shows new files, merged days, skipped days and the devices taken over.

### Daily backup to network drive, NAS or USB

> **🔒 Pro:** The daily backup and “save space” are part of GasLighter Pro. **“⬇ Download backup” and `log.csv` always stay free.** If Pro expires, the daily backup pauses; days already moved stay readable.

⚙ Settings → Storage & sound → **Daily backup**. With a target set, GasLighter copies everything new there every day (default 03:30) – the same files as the ZIP backup, but **incremental**: only new and changed files, each verified with SHA-256 afterwards.

- **Nothing is ever deleted in the target.** If an already backed-up file changes later, the old version stays next to it as `….alt-YYYYMMDD-hhmmss`.
- **Target unreachable** (NAS off, Wi-Fi gone): recording continues normally on this device. It is retried hourly, and the next run catches up everything missing.
- **Back up now** starts a run immediately; last run, number of files and errors are shown next to it.

**Examples for the target**

| Target | How to set up | Folder to enter |
|---|---|---|
| NAS / Windows share (SMB) | Home Assistant → Settings → System → Storage → **Add network storage**, name e.g. `nas_gaslighter`, usage **Share** | `/share/nas_gaslighter` |
| NAS as media folder | as above, usage **Media** | `/media/nas_gaslighter` |
| USB drive on the Home Assistant device | plug it in (appears under `/media`) | e.g. `/media/usb/gaslighter` |

> The target must already exist and must **not be on the same storage** as the data. Otherwise a network drive that is not mounted would silently fill your own storage – GasLighter reports this as an error and copies nothing.

### Save space

With **“Save space: keep old data only in the target”**, files older than “Delete after (days)” that are verified in the target are replaced here by a link to the copy. **Reports, history, printing and the checksum chain keep working** – they read these days from the target. If the network drive is asleep, the first load takes a little longer (“network drive may be waking up”). If it is unreachable, these old days are missing until it is back. Settings, `log.csv` and recent days always stay here.

If **“Delete old recordings automatically”** is also on, GasLighter only deletes what is verified in the target once a target is set.

### What happens when restoring

- **Nothing twice, nothing overwritten**: existing disturbances, notes and lists stay, only missing data is added. Restoring several times does no harm.
- **Days that already exist** (e.g. “today” after a reinstall): the missing minutes are added. The checksum chain stays verifiable – the restored part gets its own section, and “Interruptions” lists “Import …: extended by N minutes”. If the times overlap with other data, the day is skipped and named in the report.
- **Devices that no longer exist**: their data is still restored and can be chosen as “(former)” in the history, the device filter and printing.
- Storage locations (output and clip folder) stay those of this system.

### Reset

⚙ → General → **Reset**: measurements & disturbances, notes & lists, sound profiles or settings to default. Devices and connections always stay. A backup is offered first.

### Search index

GasLighter keeps a **search index** (SQLite file `suchindex.sqlite` in the app data folder). It speeds up noise reports over weeks and months:

- **Chain check per day:** the result is stored with a SHA-256 checksum over the *content* of all files of that day. If a single byte changes, the day is checked again – the check is exactly as strict as without the index.
- **Condensed day tracks** (every 10 seconds) for the charts in the noise report.

The index only contains derived data, never changes the recording, checksum chain or disturbances, is not part of the backup and fills slowly in the background after start. **Settings → General → Backup → Rebuild** clears it; it then rebuilds itself. If it is missing or damaged, GasLighter works without it – just slower.

## 10. Interruptions, data chain and updates

### Interruptions

If the add-on is not running (power cut, Home Assistant restarted, update via the add-on store), the recording is missing. GasLighter notices this at the next start and shows it in Logs below the summary:

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

**Without a recording gap:** copy the folder `gaslighter` from the update zip via Samba to `\\homeassistant\share\gaslighter_update\` (overwrite existing files). After 10–20 s only the program restarts; recording continues and is delivered afterwards. If the new version does not start, the add-on automatically goes back to the previous one.

**Full installation** (only when a version requires it, e.g. new name or watchdog): copy the folder from the full zip to `\\homeassistant\addons\` and rebuild the add-on in Home Assistant. This causes a short gap.

Every start, update and interruption is listed with time and version in Logs and in the noise log.

## 11. Settings from A to Z

At the very top choose **All devices** or a single device. For a device, “Own settings for this device” sets different values (threshold, minimum duration, monitoring time, storage). The bar at the top shows level, background, threshold and the **preview** (purple) of your not yet saved settings live. ⓘ explains every setting; “Show help” hides the texts.

### Devices

- **Sources (microphones)** – see Devices.
- **Level-match devices** – see Level-matching.
- **Microphone** – input on the server, jack, volume, sound quality (16000 Hz is enough for knocking).

### Detection

### When does something count as a disturbance?

> **🔒 Pro:** without Pro these values are view only and GasLighter uses the defaults. They can be changed with GasLighter Pro.

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

**Sound profiles** – see AI. **Different values at certain times** (time profiles) – e.g. more sensitive at night, general or per device.

### Times & pauses

- **When to monitor?** – monitor from / to (both empty = around the clock, can span midnight). Outside that nothing is counted; via the indicator at the top you can record anyway.
- **Home Assistant: pause or record state** – see Home Assistant.
- **Notes & log** – quiet hours from / to (usually 22:00–6:00), Sunday all day quiet. Notes and disturbances during quiet hours get 🌙.

### Storage & sound

### Recording the disturbance

| Setting | Meaning |
|---|---|
| Context (s) | this many seconds before and after the disturbance are shown when viewing |
| … with layers | low/mid/high, frequency for the whole day (+1–2 MB per device and day) |
| … with spectrum | spectrogram for every moment (+3–8 MB per device and day) |
| Store AI fingerprint continuously | see AI fingerprint; below it shows whether it runs |
| Delete old recordings automatically / after days | off = nothing is ever deleted |

### Store real audio (not recommended)

Default **off**. When on, a WAV file is stored with each disturbance. **Store audio only without detected voices** (recommended) prevents saving as soon as the AI detects voices anywhere. Read Legal first.

### Video & storage

Folder for noise tracks, video width, frames per second, video quality.

### General

- **General** – recognize sound type (local AI), store AI fingerprint, group: max. pause, assign note, language.
- **Backup of the whole app** – see Backup.
- **Reset** – see Reset.
- **Diagnostics** – details on microphone and sound card for troubleshooting.

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

- “AI detection is switched off”: ⚙ → General → switch on **Recognize sound type**.
- “AI model not found”: reinstall the add-on once with the **full zip** (update zips do not contain the model).
- “no fingerprint at this spot”: nothing was stored at that second (too quiet or computer busy). Check in ⚙ → Storage & sound whether the fingerprint is running.

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

## 14. GasLighter Pro

GasLighter is free. **Recording, the live view, reports, the printable noise report, export (`log.csv`, notes) and creating a backup** are always free – no time limit, no ads.

The yearly licence **GasLighter Pro** additionally unlocks:

| Feature | Without Pro | With Pro |
|---|---|---|
| Import a backup | once for free (e.g. moving) | as often as needed |
| Advanced detection settings (tab “Detection” → “When is something a disturbance?”) | view only, defaults | fully adjustable, also per device and in time profiles |
| External devices: phone in the browser, phone app / stream URL, IP camera | locked | up to 8 additional devices |
| Phone as motion sensor (vibration, motion in picture) | locked | ✔ |
| Daily backup to network drive/NAS/USB and “save space” (Backup) | “⬇ Download backup” by hand | automatic every day, verified |

The server microphone (on the Home Assistant computer) always works without Pro.

### Buy

⚙ Settings → General → **GasLighter Pro** → **🛒 Buy Pro** opens the GasLighter page on gsimulations.de. The licence is valid for **1 year from purchase** for **1 Home Assistant installation**. It does **not** renew automatically – there is no subscription. After purchase the licence key is sent by e-mail.

### Enter the key

1. ⚙ Settings → General → **GasLighter Pro**.
2. Paste the complete key from the e-mail. It starts with `GL1-`; spaces and line breaks do not matter.
3. **🔑 Activate**. It then shows “Pro active – valid until …”.

The key is checked **without internet** – GasLighter sends nothing to G-Simulation. It is **not** included in backups; after a reinstall simply enter it again.

Locked places show **🔒 Pro**. Clicking it explains the feature and offers “Buy Pro” and “Enter key”.

### Expiry and renewal

14 days before expiry a notice with “Renew” appears once at the top. After expiry everything free keeps working and recorded data stays complete:

- External devices stop recording (they stay configured and continue immediately with a new key).
- Advanced settings keep their values but can no longer be changed.
- Further imports need Pro again.

To renew, buy a new licence and enter the new key.

### Moving to a new computer

Download a backup on the old computer, install GasLighter on the new one and import the backup – the **first import is free**. Then enter your Pro key again.

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
