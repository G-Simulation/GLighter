# Changelog

## 1.51.5
- Protokolle: Klick auf Notiz, Bewegung oder Sensor in den Listen **zoomt den Verlauf auf den Bereich** (Umfeld = halbe Länge, mindestens 15 s) und markiert ihn – bisher feste ±2 Minuten.

## 1.51.4
- Notizbereich: Die Uhrzeit **läuft mit** (in der Kopfzeile „von …“ und bei „Mehr …“ im Feld „von“) und wird erst **beim Speichern** festgelegt. Ändert man das Feld „von“ von Hand, bleibt die eigene Zeit stehen; „jetzt“ schaltet wieder auf mitlaufend. Auch abgedockt läuft die Uhr weiter, wenn die Seite im Hintergrund ist.

## 1.51.3
- Notizen: Sind nur Markierungen gesetzt und kein Text eingegeben, wird beim Speichern **ein Satz daraus gebildet** (z. B. „Deutliche Schritte im Treppenhaus“, „Starkes Klopfen von oben, aufgewacht“). Der Satz steht als Notiztext und lässt sich später ändern. Gilt für „Notiz jetzt“, Notiz-Dialog und Ereignis-Notiz, deutsch und englisch.

## 1.51.2
- Notizbereich: **„Mehr …“ blendet von/bis und Zeuge direkt im Bereich ein** statt ein Fenster zu öffnen – auch im abgedockten Fenster. Der Zustand wird gemerkt, wer es immer offen will, lässt es offen. Leere Zeiten = automatisch wie bisher.

## 1.51.1
- Notizfelder (Notiz jetzt, Notiz-Dialog, Ereignis-Notiz, Sensor-Notiz): **Enter speichert**, **Alt+Enter** (oder Umschalt+Enter) macht eine neue Zeile.

## 1.51.0
- **Pro: Notizbereich abdocken.** Der Button ⧉ im Notizbereich löst ihn als eigenes kleines Fenster heraus. In Chrome und Edge ist es ein Bild-im-Bild-Fenster, das über anderen Programmen liegen bleibt (verschiebbar, Größe änderbar); sonst ein normales Zusatzfenster. „Zurückholen“ oder Schließen setzt den Bereich wieder ein.

## 1.50.18
- Live-Verlauf: Kurze Zeitfenster (Live-Puffer) und lange Zeitfenster (Tagesaufzeichnung) sehen jetzt **gleich** aus: gleiche Farbe und gleiche Achsenbeschriftung (ohne „dB“-Zusatz) bei jedem Zoom.

## 1.50.17
- Verlauf: Fähnchen der Sensor-Ereignisse werden nach der Pegelkurve gezeichnet und liegen damit über Kurve und gestrichelter Linie.

## 1.50.16
- Verlauf: Die rote gestrichelte Linie der Sensor-Ereignisse ist wieder da, liegt aber **ganz unten**: Pegelkurve, Fähnchen und Punkte liegen darüber.

## 1.50.15
- Verlauf: Die rote gestrichelte Linie und die rote Tönung bei Sensor-Ereignissen sind weg; es bleiben das farbige Fähnchen oben und der rote Punkt unten.

## 1.50.14
- Live-Verlauf: Das **Zeitfenster reicht beliebig weit zurück**: neue Stufen 2 d, 7 d, 30 d, 90 d; mit Mausrad/−/+ bis zu 400 Tage. Über 2 Tage werden Minutenwerte gezeigt. Die Ereignisliste darunter zeigt bei älteren Einträgen das Datum.

## 1.50.13
- Verlauf: Sensor-Ereignisse („als Ereignis“) sind jetzt auf der **ganzen Höhe** anklickbar – rote Linie, Marker oben und unten – und öffnen das Fenster mit Notiz, auch bei Ereignissen von gestern im Live-Verlauf.

## 1.50.12
- **Alle Tabellen gleich gestaltet und filterbar** (gleiche Tabelle wie die Ereignisliste): Ereignisse pro Tag, Notizen & Bewegung (jetzt eine Tabelle mit Typ, Datum, Uhrzeit, Quelle, Text), Sensoren im Zeitraum, Lautstärke-Prüfung, Vergleich/Kalibrierung und Profil-Training. Jede Spalte: Auswahl, Mindestwert oder Text; sortierbar.

## 1.50.11
- Live-Reiter: Die Ereignisliste ist jetzt dieselbe Tabelle wie in den Logs – **jede Spalte filterbar** (Auswahl bei Quelle/Art, Mindestwert bei Dauer/Spitze/Schwelle/Hintergrund, Text bei Start/Notiz), sortierbar.
- Dort gibt es jetzt auch den Filter **📡 Sensoren** (Mehrfachauswahl, alle Regel-Sensoren inkl. Türsensor Tilt).

## 1.50.10
- Live-Reiter: Die Liste zeigt jetzt **alle Ereignisse des im Live-Verlauf sichtbaren Bereichs** (nicht nur ab Mitternacht), einschließlich der Sensor-Ereignisse (Heizungssensor, Türsensor …).

## 1.50.9
- Einstellungen → Home Assistant: Bei Regeln „nur festhalten“/„als Ereignis“ steht jetzt eine Statuszeile: ob die Historie von Home Assistant lesbar ist (sonst mit Fehlertext), wie oft der Sensor seit dem Start „an“ war und wann zuletzt. Damit lässt sich z. B. bei Tilt sofort sehen, ob die Meldungen ankommen.

## 1.50.8
- **Kurze Sensor-Meldungen (z. B. Türsensor Tilt) fehlten**, weil „an“ und „aus“ in derselben Sekunde gespeichert wurden und der Zeitraum dadurch die Länge 0 hatte. Zeiten werden jetzt auf die Millisekunde gespeichert, und jede Meldung ist mindestens 1 s lang sichtbar.

## 1.50.7
- Filter **„Art“** oben enthält jetzt alle in den Regeln angelegten Geräte (z. B. Fernseher, Heizungssensor, Türsensor Erschütterung, Türsensor Tilt) sowie Handy-Erschütterung und -Bewegung – zum Anhaken zusammen mit den Geräuscharten.

## 1.50.6
- **Kurze Sensor-Meldungen gehen nicht mehr verloren** (z. B. Türsensor Tilt nur 1 s an): Für Regeln „nur festhalten“ und „als Ereignis“ übernimmt GasLighter jeden Wechsel mit genauer Uhrzeit aus der Historie von Home Assistant, statt nur alle 5 s den aktuellen Zustand abzufragen. Nach einem Neustart werden bis zu 6 h nachgeholt. Ist die Historie nicht erreichbar, geht es wie bisher.
- Auswahllisten (📡 Sensoren, Art in der Tabelle) enthalten alle angelegten Regeln, auch wenn ein Sensor im Zeitraum nichts gemeldet hat.

## 1.50.5
- Sensor-Ereignisse: Das Fähnchen oben im Verlauf hat je Sensor eine **eigene Farbe** (auch in der Legende); die rote Linie bleibt. Farbe frei wählbar unter Einstellungen → Home Assistant → Regel → **Farbe** (↺ = automatisch).

## 1.50.4
- Verlauf wie Live: Sensor-Ereignisse („als Ereignis“, z. B. Türsensor) haben rote Marker – gestrichelte Linie über die ganze Höhe und rote Marke unten wie bei Störungen.
- Zeilen im Verlauf sind so hoch wie der Live-Graph (280 px, am Handy 220 px). Selbst eingestellte Höhen bleiben.

## 1.50.3
- Ereignistabelle: Die Filter unter **Quelle / Gerät** und **Art** sind jetzt eine Liste mit **Häkchen** (Mehrfachauswahl, „alle“, „keine Auswahl“); der Knopf zeigt „3 gewählt“. Vorher war die Mehrfachauswahl nicht zu erkennen.

## 1.50.2
- **Lücken in der Tagesaufzeichnung** werden jetzt auch erkannt, wenn der Starter sie nicht protokolliert hat (z. B. beim Umzug auf eine neue Installation): Sie stehen unter „Unterbrechungen“ mit Gerät und Zeit, sind im Verlauf schraffiert („nicht aufgezeichnet“, nur in der Zeile dieses Geräts), lassen sich kommentieren und stehen im Lärmprotokoll. Bewusste Pausen zählen nicht; Handys werden nicht geprüft, weil sie oft absichtlich offline sind.

## 1.50.1
- Filter **„Art“** oben in Protokolle mit **Mehrfachauswahl**, z. B. Stimme + TV/Musik. Gilt für Kopfzahlen, Verlauf und Tabelle; eine passende Art genügt.

## 1.50.0
- **Dashboard (GridStack, MIT-Lizenz, liegt in der App):** Live und Protokolle bestehen aus Bereichen mit eigener Kopfleiste.
  - Jeder Bereich lässt sich **einklappen** (▾) und **ausblenden** (✕).
  - **▦ Layout anpassen:** Bereiche verschieben, breiter/schmaler ziehen (z. B. nebeneinander), ein- und ausschalten, zurücksetzen. Gespeichert je Browser; am Handy untereinander.
  - **⌖ nur sichtbarer Bereich** für die Ereignistabelle und die Sensor-Liste: folgt dem Zoom im Verlauf.
- Die Liste „Sensoren im Zeitraum“ ist ein eigener Bereich und anfangs ausgeblendet (doppelt zur Tabelle).
- Regeln „nur festhalten“ (z. B. Fernseher): jede Störung in dieser Zeit zeigt in der Tabelle „📡 Fernseher an“.
- Anzahl der Zeilen: zusätzlich 5, 10, 20, 2000 und 5000.

## 1.49.0
- **Suchverzeichnis (SQLite):** Lärmprotokolle über lange Zeiträume sind deutlich schneller (Test: 6 Wochen von 39 s auf etwa 4 s, danach 2 s).
  - Gespeichert wird das Ergebnis der Kettenprüfung je Tag – mit SHA-256 über den Inhalt aller Dateien des Tages, ändert sich ein Byte, wird neu geprüft – und eine verdichtete Tagesspur für die Grafiken.
  - Nur abgeleitete Daten: Aufzeichnung, Datenkette und Störungen bleiben unverändert; nicht in der Sicherung; füllt sich im Hintergrund; „Neu aufbauen“ unter Einstellungen → Allgemein → Sicherung.
- **Mehrere Sensoren gleichzeitig:** Sind z. B. Fernseher und Türsensor zur selben Zeit an, hat jeder seine eigene Spur (feste Reihenfolge nach Name) und ist einzeln anklickbar. Notizen stehen untereinander statt übereinander.

## 1.48.0
- **Neue Ereignistabelle** (Tabulator, MIT-Lizenz, liegt in der App – ohne Internet):
  - Sortieren per Klick auf die Spaltenüberschrift (wird gemerkt).
  - Filter mit **Mehrfachauswahl** unter „Quelle / Gerät“ und „Art“ – auch nach einzelnen Sensoren.
  - Sensor-Ereignisse stehen zeitlich zwischen den Störungen (oranger Rand) statt in einem eigenen Abschnitt.
  - Zählung „… Störungen · … Sensor-Ereignisse“ über der Tabelle, folgt dem Filter.
  - Gruppen klappen in der Tabelle auf und zu; Auswahl, ⋮-Menü, Rechtsklick, Doppelklick und Sprung in den Verlauf wie bisher.
  - Schmale Bildschirme: weniger wichtige Spalten klappen unter die Zeile (⊕).

## 1.47.3
- **Home-Assistant-Regel „als Ereignis“:** neue Aktion neben „pausieren“ und „nur festhalten“, z. B. für Tür- und Vibrationssensoren. Jedes „an“ steht als eigene Zeile unter **📡 Sensor-Ereignisse** in der Ereignistabelle (Uhrzeit, Dauer, Notiz, Klick springt in den Verlauf) und zählt nicht als Störung. Gilt rückwirkend.
- Handy als Bewegungsmelder: Erschütterung und Bewegung stehen ebenfalls als Sensor-Ereignisse in der Tabelle.
- **„Nur festhalten“** (z. B. Fernseher) färbt den Verlauf nicht mehr in ganzer Höhe, sondern zeigt oben einen schmalen Streifen – je Sensor eine Spur. Darunter lässt sich normal ziehen und markieren.
- **Notiz zu Sensor-Zeiträumen:** Klick auf den Streifen oder ✎ in der Liste. Die Notiz steht im Verlauf, in der Liste „Sensoren aus Home Assistant“ und im Lärmprotokoll.
- **Filter „📡 Sensoren“** mit Mehrfachauswahl (Störungen, jeder Sensor, Handy-Erschütterung, Handy-Bewegung) für Verlauf, Listen und Tabelle.
- **🗑 Bereich löschen:** beliebig langen Zeitraum im Verlauf aufziehen und alle Störungen darin löschen, optional mit Notiz an der Stelle. Tagesaufzeichnung und Datenkette bleiben unverändert.
- Notizen und Sensor-Streifen haben größere Klickflächen (auch am Handy).
- „Profile & neu untersuchen“ lässt Sensoren unberührt (Hinweis im Fenster).

## 1.47.2
- Sicherung einspielen: Bei Tagen, die es hier noch nicht gab (neue Installation, neues Gerät), ging das Spektrum verloren – danach meldete die Datenkette „passt nicht“. Behoben. Dieselbe Sicherung noch einmal einspielen repariert bereits eingespielte Tage (fehlendes Spektrum wird ergänzt, Vorhandenes bleibt unverändert); der Bericht nennt die reparierten Tage.

## 1.47.1
- Sicherung einspielen: Große Sicherungen (über 16 MB) scheiterten in Home Assistant mit „Einspielen fehlgeschlagen: 413“, weil die Seitenleiste nur kleine Uploads durchlässt. Die Datei wird jetzt in Teilen zu 8 MB hochgeladen (mit Fortschritt und automatischem Wiederholen).

## 1.47.0
- **Handy als Bewegungsmelder:** Ein als Gerät eingerichtetes Handy meldet auf Wunsch **🫨 Erschütterung** (Beschleunigungssensor, z. B. Trampeln, Bass durch die Decke, Türenknallen) und **🏃 Bewegung im Kamerabild**. Einschalten je Handy unter Einstellungen → Geräte, mit Empfindlichkeit hoch/mittel/niedrig.
  - Ausgewertet wird nur auf dem Handy; gesendet werden nur Zahlen, kein Bild und kein Video.
  - Beginn, Ende und Spitze werden gespeichert (`bewegung.csv`), stehen in Protokolle („Erschütterung und Bewegung im Zeitraum“) und im Lärmprotokoll.
  - In Home Assistant erscheint je Handy ein Bewegungs- bzw. Vibrationssensor (MQTT), nutzbar in Automationen und Regeln.
- **Neue Kennung `gaslighter`** (bisher `laerm_logger`): Home Assistant führt GasLighter damit als neue App. Datenordner jetzt `/share/gaslighter`, MQTT-Namen `gaslighter/…`. Updates ohne Neuinstallation liegen in `\\homeassistant\share\gaslighter_update\gaslighter\` (der alte Ordner `laerm_update` wird weiter gelesen). Umzug der bisherigen Daten: Sicherung in der alten App herunterladen und in der neuen einspielen (kostenlos).

## 1.46.0
- **GasLighter Pro** (Jahreslizenz, 1 Installation, kein Abo): Einstellungen → Allgemein → „GasLighter Pro“ mit Status, Feld für den Lizenzschlüssel und „🛒 Pro kaufen“. Der Schlüssel wird ohne Internet geprüft (digitale Signatur) und nicht in der Sicherung gespeichert.
  - Pro schaltet frei: **Import einer Sicherung** (der erste Import ist kostenlos, z. B. für den Umzug), **erweiterte Einstellungen der Erkennung** (ohne Pro nur zum Ansehen, es gelten die Standardwerte) und **externe Geräte** (Handy, Stream, IP-Kamera).
  - Aufzeichnung, Live-Ansicht, Protokolle, Lärmprotokoll, Druck, Export und das Erstellen einer Sicherung bleiben immer kostenlos.
  - An gesperrten Stellen steht 🔒 Pro mit kurzer Erklärung; 14 Tage vor Ablauf erscheint einmal ein Hinweis zum Verlängern. Nach dem Ablauf bleiben alle Daten erhalten, externe Geräte bleiben eingerichtet.
- Handbuch: neues Kapitel „GasLighter Pro“; Hinweise bei Geräten, Sicherung und Einstellungen.

## 1.45.2
- Name der App jetzt **GasLighter** (Schreibweise mit großem L) – in Kopfzeile, Seitenleiste, Handbuch, Handy-Seite und als Gerätename in Home Assistant (MQTT).

## 1.45.1
- Lärmprotokoll mit Grafiken: **Tagesverlauf** je Tag und Gerät über 24 h (Spitze, Hintergrund, Schwelle, Störungen rot, Home Assistant blau, nicht aufgezeichnet schraffiert mit Kommentar, Notizen), gleiche Skala je Gerät, als Vektorgrafik (scharf im PDF). Oben auf der Seite wählbar: „Tagesgrafik“ (Standard an) und „Grafik je Störung“ (Standard aus; kleine Grafik mit Umfeld für Störungen mit Notiz bzw. aus der gewählten Liste, höchstens 300).

## 1.45.0
- **📖 Handbuch** (oben in der Kopfzeile, am Handy im Menü ⋯): Bedienungsanleitung als Wiki mit 14 Kapiteln – Schnellstart, Live, Protokolle, Ereignis, KI, Geräte, Home Assistant, Drucken, Sicherung, Unterbrechungen, Einstellungen A–Z, Rechtliches, Fehlerbehebung, Glossar. Deutsch und Englisch, mit Bildern, Suche, Inhaltsverzeichnis und Querverweisen, druckbar, ohne Internet. „📖 Mehr im Handbuch“ in den Bedienhinweisen, bei der Prüf-Schwelle und 📖 an jedem Einstellungs-Abschnitt springen zum passenden Kapitel. Der Reiter „Dokumentation“ des Add-ons in Home Assistant zeigt denselben Text.
- Sicherung einspielen in zwei Schritten: erst **prüfen** (Version, Datum, Geräte der Sicherung mit Zustand), dann wählen und **einspielen**.
  - Geräte werden zusammengeführt statt ersetzt: hier eingerichtete Geräte bleiben, gewählte aus der Sicherung ersetzen das gleiche Gerät oder kommen dazu. Nicht erreichbare Geräte werden ausgeschaltet übernommen und tragen den Hinweis „bitte prüfen“ (kein endloses Neuverbinden).
  - Gibt es das Mikrofon der Sicherung hier nicht, bleibt das bisherige eingestellt.
  - Tage, die es hier schon gibt (z. B. „heute“ nach einer Neuinstallation), werden um die fehlenden Minuten ergänzt statt übersprungen. Die Prüfsummen-Kette bleibt prüfbar (eingespielter Teil als eigener Abschnitt); unter Unterbrechungen steht „Import …: um N Minuten ergänzt“. Überschneidet sich ein Tag mit anderen Daten, wird er übersprungen und genannt.
  - Kommentare zu Unterbrechungen sind jetzt Teil der Sicherung.
  - Bericht nach dem Einspielen: zusammengeführte und übersprungene Tage, übernommene und ausgeschaltete Geräte.
- Geräte, die es nicht mehr gibt, deren Daten aber vorhanden sind, stehen als „(ehemalig)“ im Gerätefilter, im Verlauf und im Druck zur Auswahl.

## 1.44.2
- Verlauf: Ein Klick (bzw. Antippen) auf eine schraffierte Unterbrechung öffnet direkt dort ein kleines Fenster für den Kommentar, mit Zeitraum und Ursache, „Speichern“ und „Entfernen“. Beim Darüberfahren zeigt eine Hand, dass es anklickbar ist; der Tooltip zeigt den Kommentar. Ziehen, Doppelklick und „Bereich markieren“ funktionieren unverändert. Gilt in Protokolle und im Tagesverlauf im Live-Reiter; gleiche Daten wie die Liste „Nicht aufgezeichnet“.

## 1.44.1
- Verlauf: Der Kommentar zu einer Unterbrechung wird in der Schraffur vollständig angezeigt und bei wenig Platz auf mehrere Zeilen umbrochen; ist es zu eng, steht der ganze Text als Tooltip beim Darüberfahren.

## 1.44.0
- Neuer Name der App: **Gaslighter**, im Kopf, im Seitenleisten-Eintrag, auf der Handy-Mikrofon-Seite und beim MQTT-Gerät. Die Kennung (slug `laerm_logger`) bleibt gleich, alle Daten bleiben erhalten. Das ausgedruckte bzw. exportierte Dokument heißt weiter „Lärmprotokoll“.
- Verlauf: Läuft der Tag noch, endet die Zeitachse bei „jetzt“, das Neueste steht also rechts. Der Verlauf wächst jede Minute mit. Vergangene Tage zeigen weiter 00–24 Uhr.
- Unterbrechungen: Es wird unterschieden zwischen „von Home Assistant angehalten / neu gestartet“ und „ohne Herunterfahren beendet, z. B. Stromausfall“. Zu jeder Unterbrechung lässt sich ein eigener Kommentar eingeben (📝 Kommentar). Er erscheint in Protokolle, in der Schraffur im Verlauf, im Druck und im exportierten Lärmprotokoll. Die Aufzeichnung selbst bleibt unverändert.
- Watchdog: Home Assistant kann das Add-on neu starten, wenn es unerwartet beendet wird (Schalter „Watchdog“ auf der Add-on-Seite). Dafür ist einmal eine volle Installation nötig.
- KI-Hinweis unterscheidet: Schalter „Geräuschart erkennen“ aus oder KI-Modell nicht gefunden.
- Hintergrund: Die ersten 2 s nach einem Start werden nicht gelernt, damit die Hintergrundlinie nach einem Neustart nicht kurz hochspringt.

## 1.43.1
- Protokolle: Die Wochenleiste (Kreise) zeigt immer die neueste Nacht, wenn ein Tag der letzten 7 gewählt ist; ältere Tage stehen in der Mitte.
- Prüf-Schwelle, Spalte „Art (KI)“: Alle Spitzen (bis 2000) werden zugeordnet statt nur die ersten 400. Ohne Fingerabdruck direkt in der Spitze zählt der nächste innerhalb von 2 s. Statt pauschal „keine KI-Daten“ steht jetzt „an diesem Tag kein KI-Fingerabdruck“, „kein Fingerabdruck an dieser Stelle“ oder „nicht geprüft“. Ist die KI-Erkennung aus, erscheint ein Hinweis.
- Einstellungen → Speichern & Ton: unter „KI-Fingerabdruck durchgehend speichern“ steht, ob er läuft und wie viele Sekunden heute je Gerät gespeichert wurden.
- Home-Assistant-Regeln: neues Feld „Name“ (z. B. „Erschütterung Wand“). Unter diesem Namen wird die Regel in der Störung, im Verlauf und in der Zustands-Datei festgehalten; leer = Name aus Home Assistant.
- Bedienung (Durchsicht der Oberfläche):
  - Prüf-Schwelle-Leiste und Wochenleiste waren auch ausgeblendet sichtbar – behoben.
  - Druck: Ende eines ganzen Tages heißt „24:00“ statt „00:00“ desselben Tages; neu „Zeilen ohne Aufzeichnung zusammenfassen“ (Standard an); Knöpfe im Druckdialog bleiben unten sichtbar.
  - Handy: Notizfeld startet zugeklappt, Merkmale mit „Mehr …“; Verlauf mit Werkzeug-Menü „⋯“, Ebenen hinter einem Knopf, höhere Graphen und größere Tasten; dB-Achse im Live-Bild schmaler; Ereignisse heute und Filter kompakt; Ereignis-Fenster zeigt den Graphen weiter oben.
  - Bereich markieren: Hinweis direkt über dem Graphen mit „Fertig“; Meldungen erscheinen unten.
  - „Sonstiges“-Symbol im hellen Modus sichtbar; Störungsflächen im Live-Bild dezenter; im Ereignis-Fenster Beginn und Ende der Störung als Linie, Vorschläge außerhalb blasser, Beschriftungen im dunklen Modus heller.
  - Texte: „Leiser als das Lauteste davor“, Home-Assistant-Zustand ohne doppeltes „aus · off“, Schwelle „passt sich an …“, „Alle Geräte“ in den Einstellungen.
  - LIVE-Anzeige neutral (roter Punkt), Info-Hinweise blau statt orange, Bedienhinweise zuklappbar („ⓘ Bedienung“, am Handy mit Touch-Text).
  - Verlauf: Zeiten ohne Aufzeichnung schraffiert; „Ganzer Zeitraum“ nur, wenn gezoomt; leere Spalte „Geräte (Spitze)“ ausgeblendet.
  - Zahlen in deutscher Schreibweise (−70,7); Tastatur und Bildschirmleser an mehreren Knöpfen verbessert.

## 1.43.0
- Protokolle → Verlauf: „📏 Prüf-Schwelle“ – ein frei wählbarer Wert in dB, gleich für alle Zeilen. Linie im Verlauf ziehen oder Wert eingeben; alles darüber wird violett hervorgehoben. Je Gerät Anzahl und Dauer der Spitzen im sichtbaren Ausschnitt, gezählt aus den vollen 125-ms-Werten (Abstand unter 0,5 s = eine Spitze). „Liste der Spitzen“ mit Uhrzeit, Dauer, Spitze, Abstand zur Prüf-Schwelle, Art (KI) und Tonprofil; Klick springt im Verlauf dorthin. Nur Anzeige: gespeicherte Daten, Störungen und Prüfsummen bleiben unverändert.
- Nachträgliche KI-Zuordnung je Spitze: in einer gespeicherten Störung deren Art und Tonprofil; sonst aus dem gespeicherten KI-Fingerabdruck (Gruppen-Werte und Vergleich mit den Tonprofilen, ⓕ); ohne Fingerabdruck „keine KI-Daten“.
- Druck (Notenblatt): Prüf-Schwelle als Linie mit hervorgehobenen Spitzen und Zählung je Zeile.

## 1.42.1
- Schwelle außerhalb der Skala (z. B. weit über den Messwerten): wieder als gestrichelte Linie am oberen bzw. unteren Rand mit Beschriftung und Pfeil („Schwelle −50,0 dB ↑“) – im Live-Bild (Pegelspur und Balken), im Verlauf und im Ereignis-Fenster. Die Skala bleibt unten bündig an den Messwerten. Hintergrund außerhalb ebenfalls mit Pfeil, ohne die Schwellen-Beschriftung zu überdecken.

## 1.42.0
- Kurven und Balken zeichnet jetzt die bewährte Bibliothek uPlot (MIT-Lizenz, im Add-on enthalten, kein Internet nötig): Live-Bild (Pegelspur und Lautstärke-Balken), Tagesverlauf im Live-Reiter, Verlauf in Protokolle und die Grafik im Ereignis-Fenster. Raster, Achsen, Kurven, Hintergrund und Schwelle kommen von uPlot; Störungen, Notizen, Tooltips, Bereich markieren und Beschriftungen liegen wie bisher darüber. Spektrogramm und Druck bleiben unverändert.
- Live-Bild ruhiger: rückt in ganzen Pixeln weiter, die Spitzen und unteren Enden der Kurve springen beim Mitlaufen nicht mehr, die Kurve reicht immer bis zum rechten Rand (die kleine Anzeige-Verzögerung passt sich an).
- Live-Bild: Uhrzeiten auch direkt unter der Pegelspur bzw. den Balken; auf schmalen Bildschirmen weniger Uhrzeiten, damit sie sich nicht überlappen.

## 1.41.5
- Verlauf (Protokolle) und Tagesverlauf im Live-Reiter: Solange Daten geladen werden, zeigt jede Grafik-Zeile ein Ladesymbol „Daten werden geladen …“ (erscheint erst nach einer Viertelsekunde, damit es bei schnellen Antworten nicht flackert); beim ersten Laden steht ein Platzhalter mit Ladesymbol da.

## 1.41.4
- Verlauf (Protokolle): Höhe jeder Zeile mit dem Griff darunter ziehen (70–900 px), Doppelklick auf den Griff = Standardhöhe; wird pro Browser gemerkt.
- Verlauf: Spektrogramm beim starken Hineinzoomen ohne Streifen (Spalten lückenlos bis zur nächsten Messung).
- Behoben: Änderungen an einer Verlaufs-Zeile (Gerät, Darstellung, Ebenen) gingen nach dem Zoomen manchmal verloren.

## 1.41.3
- Verlauf drucken („Notenblatt“): Reiter Protokolle → Verlauf → „🖨 Drucken“. Zeitraum frei (von–bis) oder per Knopf: sichtbarer Ausschnitt, Zeitraum des Berichts, alle Daten. Zeit je Zeile 1 min bis 1 h (Standard 10 min), Geräte wählbar (untereinander), Inhalt einstellbar (Pegelspur, Spektrogramm, Störungs-Infos und Notizen), Skala gleich für alle Zeilen oder je Zeile angepasst, A4 quer oder hoch. Die Vorschau öffnet sich in einem neuen Fenster; dort „Drucken“ (auch als PDF speichern). Seitenzahlen unten rechts, Störungen nummeriert mit Liste darunter (Zeit, Dauer, Spitze, Abstand zur Schwelle, Art, Tonprofil, Notizen), Notizen als N1, N2 … mit Text.
- Verlauf: Spektrogramm jetzt auch für den ganzen Tag (vorher erst ab 3 Stunden Zoom).
- Behoben: War „Gestern“ (oder ein anderer Zeitraum) gemerkt, zeigte der Reiter Protokolle beim Öffnen trotzdem heute; ein langsam geladener Verlauf konnte zum falschen Tag gehören. Frequenz-Beschriftung ohne Spektrum überlagerte sich.

## 1.41.2
- Zoomen wie in gängigen Diagramm-Werkzeugen (ECharts, Grafana, Chart.js), im Live-Bild und im Verlauf gleich: Mausrad, Touchpad-Spreizen oder zwei Finger zoomen die Zeit (stufenlos, an der Stelle unter der Maus; live bleibt der rechte Rand „jetzt“ und das Bild läuft weiter). Ziehen bzw. seitlich wischen verschiebt, Umschalt + Ziehen zieht einen Bereich auf und zoomt hinein, Umschalt + Mausrad oder Mausrad über der dB-Beschriftung zoomt die Höhe (unten bündig), Doppelklick setzt alles zurück.
- Live-Bild: Zeitfenster stufenlos (5 s bis „Heute“); weiter als 10 Minuten geht es nahtlos in den Tagesverlauf und beim Hineinzoomen wieder zurück ins Live-Bild. Die Auswahl „Zeitfenster“ zeigt den gezoomten Wert.
- Behoben: Fuhr man im Live-Bild über eine Störung, die schon in der Liste stand, blieb die Grafik stehen (Fehler im Tooltip).

## 1.41.1
- Update ohne Verlust: Ton, den das alte Programm beim Update schon bekommen, aber nicht mehr verarbeitet hatte, ging verloren (einige Zehntel bis Sekunden). Das alte Programm merkt sich jetzt beim Beenden, bis wohin es verarbeitet hat; das neue bekommt genau ab dort alles nachgeliefert. Dafür ist der Starter neu (Relais 2): diese Version einmal über den Ordner addons installieren, danach laufen Updates über share/laerm_update ohne Verlust.
- Live-Bild, Pegelspur: Zoomen (Mausrad, + / −) bleibt unten bündig am tiefsten sichtbaren Wert und streckt nur nach oben; die Schwelle bestimmt die Skala nicht mehr (liegt sie außerhalb, steht sie am Rand). Senkrecht ziehen verschiebt weiterhin frei.
- Verlauf (Protokolle): Skala unten bündig am tiefsten Wert, feinere Beschriftung bei kleinen Spannen.
- Verlauf zoomen: Daten erscheinen schon während des Zoomens (vorher erst nach dem Loslassen plus Ladezeit); nur eine Abfrage gleichzeitig, danach sofort der neueste Ausschnitt; Spektrum wird nur geladen, wo eine Zeile es zeigt; große Antworten werden gepackt übertragen.

## 1.41.0
- Bereich markieren im Live-Bild und im Verlauf (Protokolle): „🏷 Bereich markieren“, Bereich aufziehen, benennen. Vorhandene Arten (Tonprofile und benannte Bereiche) stehen zur Auswahl; der Bereich wird der Art zugeordnet. In einer Störung als benannter Bereich, sonst als Beispiel des Tonprofils (mit KI-Fingerabdruck, solange der Ton im Arbeitsspeicher ist).
- Ereignis-Fenster: beim Benennen eines Bereichs stehen die vorhandenen Arten (auch Tonprofile) zuerst.
- Behoben: Benannte Bereiche in Störungen aus der Tagesaufzeichnung wurden außerhalb der ersten Sekunde abgelehnt.
- Tooltip mit Einzelheiten beim Darüberfahren bzw. Antippen einer Störung im Live-Bild und im Verlauf (Zeit, Dauer, Spitze, Schwelle, Hintergrund, Art, Tonprofil, weitere Geräte, Gruppe, Notizen).
- Live-Bild: ohne „Echten Ton speichern“ kein Vorlauf mehr; Störungen innerhalb der Gruppen-Pause werden hell verbunden.
- Seite über Nacht geöffnet: Verbindung wird selbst wiederhergestellt (nach Ruhezustand bzw. abgelaufener Anmeldung neu laden), Messwerte erscheinen ohne manuelles Neuladen.
- Ruckeln bei Störungen verringert: Ereignislisten werden gedrosselt nachgeladen, KI-Ergebnisse gesammelt gespeichert, der KI-Fingerabdruck weicht der Auswertung von Störungen aus.
- Verlauf: Zoomen mit Touchpad fein abgestuft (auch Zwei-Finger-Spreizen), seitlich wischen scrollt; auf Tablets/Handys zoomen und verschieben zwei Finger, ohne dass die Seite mitscrollt; Zeilen ohne Daten im Ausschnitt bleiben stehen (nichts verrutscht); Antippen zeigt die Werte. Größere Bedienflächen auf Touch-Geräten.

## 1.40.6
- Verlauf im Reiter Protokolle: Mausrad zoomt jetzt direkt (ohne Strg), um die Stelle unter der Maus; Umschalt + Mausrad bzw. seitlich wischen scrollt.

## 1.40.5
- Speichern & Ton: „Echten Ton speichern“ steht mit Vor-/Nachlauf, Länge, Stimm-Sicherung und Mitspeichern in einem eigenen, rot umrahmten Abschnitt „Echten Ton speichern (nicht empfohlen)“, standardmäßig zugeklappt, mit Erklärung, warum man es ausgeschaltet lassen sollte.

## 1.40.4
- Zurücksetzen ohne Sicherung: nur noch eine Sicherheitsabfrage (nennt, was gelöscht wird).

## 1.40.3
- Einstellungen → Allgemein → „Zurücksetzen“: Messdaten & Störungen, Notizen & Listen, Tonprofile und/oder Einstellungen (auf Standard) wählbar; Geräte und Verbindungen bleiben. Vorher wird die Sicherung zum Herunterladen angeboten; ohne Sicherung kommt eine doppelte Sicherheitsabfrage. Das Zurücksetzen wird im Laufzeit-Protokoll vermerkt.
- Nach dem Löschen von Störungen werden Kopfzahlen und Verlauf im Reiter Protokolle sofort aktualisiert.

## 1.40.2
- Einstellungen → Erkennung: Abschnitt „KI einlernen (Profile)“ mit „🧩 Tonprofil aufnehmen“ und „Profile verwalten & neu untersuchen“.
- Das Einstellungsfenster behält in allen Reitern dieselbe Größe und Position.
- „Profil aufnehmen“ heißt jetzt „Tonprofil aufnehmen“.

## 1.40.1
- Abspielen nur noch, wenn echter Ton gespeichert ist: ▶ in der Ereignistabelle und „Ablauf zeigen“ im Ereignis sind sonst ausgeblendet (die Spalte verschwindet, wenn kein Eintrag Ton hat).
- Handy-Ansicht der Tabelle: Spalte „Geräte“ passend eingeordnet.

## 1.40.0
- Update ohne Aufnahmelücke: Starter mit Aufnahme-Relais (`aufnahme.py`). Neue Fassung nach `/share/laerm_update/` kopieren – nur das Programm startet neu, Server-Mikrofon und Streams laufen weiter (Puffer bis 5 min), Handys puffern bis 3 min. Rückfall auf die vorige Fassung, wenn eine neue nicht startet. Laufzeit-Protokoll (Start, Update, Unterbrechung) in den Daten, im Reiter Protokolle und im Lärmprotokoll.
- Prüfsummen-Kette der Tagesaufzeichnung je Minute; Prüfung im Reiter Protokolle und im Lärmprotokoll; stündlich als Sensor an Home Assistant.
- Ohne echten Ton: Störung = einzelner Ausschlag, kein Vor-/Nachlauf, keine eigene Lärmspur – Ansicht, Vergleich der Geräte und Download aus der Tagesaufzeichnung. Vor-/Nachlauf, Länge und Mitspeichern nur noch bei echtem Ton sichtbar. Tagesaufzeichnung immer an.
- Störungen über alle Geräte zusammengefasst (eine Zeile, Spitze je Gerät, zählt einmal) und als Gruppe gleicher Art/gleichen Profils; „Gruppen / Alle einzeln“. Im Verlauf Störungen der anderen Geräte schwach markiert.
- Profile: „Tonprofil aufnehmen“ (Ruhepegel, dann jeder Ausschlag je Gerät als eigenes Beispiel), Zuordnung jeder Störung mit Prozent, Bestätigen/Ändern im Ereignis (wird neues Beispiel), Hintergrund-Profile zählen nicht. „Neu untersuchen“ über einen Zeitraum, auch unter der Schwelle (Bereiche im Verlauf).
- KI-Fingerabdruck durchgehend (pro Gerät, Standard an), nur wenn etwas zu hören ist.
- Notiz ohne Uhrzeit wird der letzten Störung zugeordnet (einstellbar, Standard 5 min; alle Geräte bzw. gewähltes Gerät), Vorschau in der Notiz-Leiste.
- Auslöser je Gerät für Home Assistant (Ereignis-Entität und Geräte-Auslöser: beginnt, endet, Art erkannt).
- Fernseher-Regeln standardmäßig „Nur vermerken“ (einmalig umgestellt, Pausieren bleibt wählbar); Lautstärke/stumm des Fernsehers wird mitgeschrieben, falls gemeldet.
- Handy-Seite zeigt „Aufzeichnung angehalten“. Fortsetzen über Home Assistant klappt jetzt auch nach `recording/set OFF`.
- Behoben: angefangene Minute der Tagesaufzeichnung ging bei Neustart verloren; Spektrum nach Pausen über 65 s innerhalb einer Stunde zeitlich verschoben; Tagesdaten werden beim Wachsen nur noch neu dazugelesen.

## 1.39.0
- Einstellungen: Ganz oben die Auswahl „Allgemein (alle Geräte)“ oder ein Gerät, darunter die Reiter dafür (statt „Einstellungen für“ in jedem Reiter). Beim Gerät: Reiter „Gerät“ mit nur dessen Karte, Erkennung, Zeiten & Pausen, Speichern & Ton; „Eigene Einstellungen für dieses Gerät“ direkt unter der Auswahl. Hinzufügen von Geräten und Einpegeln unter „Allgemein (alle Geräte)“. „⚙ Pegel & Schwelle“ in der Gerätekarte springt zum Reiter Erkennung.

## 1.38.0
- Geräte einpegeln: Geräte per Häkchen auswählen (mindestens zwei, pro Browser gemerkt); nur diese messen gemeinsam und werden angepasst. Kein Bezugsgerät mehr: Ziel ist der Mittelwert der ausgewählten Geräte, jedes Gerät bekommt seine eigene Verstärkung. Ziel steht im Ergebnis und im Lärmprotokoll.
- „📝 Notiz jetzt“ als Leiste oben im Live-Bild, einklappbar (pro Browser gemerkt), sofort tippbar (am PC hat das Textfeld gleich den Fokus). „von“ wird beim ersten Tippen bzw. Tag gesetzt, „läuft noch“ setzt „bis“ beim Speichern, Strg+Enter speichert, „Mehr …“ öffnet den bisherigen Dialog mit von/bis. Der Knopf im Live-Bild entfällt.
- Behoben: „Ereignisse heute“ machte die Seite auf dem Handy breiter als den Bildschirm; die Tabelle scrollt jetzt in sich.

## 1.37.0
- Verlauf im Reiter Protokolle zoom- und scrollbar, für alle Zeilen gleichzeitig: + / − und ‹ › im Kopf, Strg + Mausrad (Trackpad-Zoom) oder zwei Finger = zoomen um die Stelle, hineingezoomt ziehen, Umschalt + Mausrad oder die Leiste unter den Zeilen = scrollen. Bereich aufziehen geht weiter (hineingezoomt mit Umschalt). Doppelklick bzw. „Ganzer Zeitraum“ zurück. Normales Mausrad scrollt weiter die Seite.
- Dashboard (Live): Tabelle „Ereignisse heute“ mit allen Ereignissen des Tages, neueste oben. Gerät (alle oder das gewählte) und Spalten (⚙) einstellbar, pro Browser gemerkt. Klick auf eine Zeile öffnet das Ereignis.

## 1.36.0
- Die Diagnose (Mikrofon, Soundkarte) ist ausgeblendet. Einblenden über Einstellungen → Allgemein → Diagnose → „Diagnosemodus“; gilt pro Browser.

## 1.35.0
- Pro Gerät einstellbar, was den ganzen Tag abgelegt wird (Speichern & Ton): Pegel (wie bisher), „… mit Ebenen“ und neu „… mit Spektrum“ – die 23 Terzbänder je 125 ms, dieselben Werte wie in der Lärmspur einer Störung, nur durchgehend (kein Ton). Das Spektrum wird je Stunde roh mitgeschrieben und zur vollen Stunde verdichtet (`clips/tag/*.lts`); geschätzt +3–8 MB pro Gerät und Tag.
- Verlauf: neue Darstellung „Spektrogramm“ je Zeile; beim Zurückspulen im Live-Bild durchgehendes Spektrogramm, wo es gespeichert ist (sonst wie bisher nur bei Störungen). Bis 3 h Zeitraum.
- Verlauf und Zurückspulen zeigen auch die laufende, noch nicht geschriebene Minute.
- Neu: „📝 Notiz jetzt“ im Live-Bild – Notiz mit von (Zeitpunkt des Öffnens, änderbar) und optional bis, Gerät oder alle Geräte, Schnell-Tags, Text, Zeuge. Einmal gespeichert (`notes.json`, Teil der Sicherung), verknüpft über die Zeit: sichtbar im Live-Bild, im Verlauf aller Geräte, bei jeder Störung in diesem Zeitraum (Ereignisfenster, 📝-Zähler in der Tabelle), in „Alle Notizen“, im Reiter Protokolle und als eigene Zeile im Lärmprotokoll. Bearbeiten und Löschen (Papierkorb) jederzeit. Beim Einspielen einer Sicherung gilt je Notiz die neueste Fassung.

## 1.34.0
- Verlauf im Reiter Protokolle frei einstellbar: „＋ Zeile hinzufügen“, je Zeile Gerät, Darstellung (Pegelspur oder Lautstärke-Balken) und Ebenen (tief, mittel, hoch, dominante Frequenz, Klangschwerpunkt); Zeilen verschieben (↑ ↓) und entfernen (✕). Dasselbe Gerät kann mehrfach mit verschiedenen Ebenen stehen. Wird pro Browser gemerkt.
- Steht nur eine Zeile da und wird in der Tabelle eine Störung eines anderen Geräts gewählt, schaltet die Zeile auf dieses Gerät um; sonst wird nur zur Stelle gesprungen.

## 1.33.0
- Ein Reiter „Protokolle“ statt „Nachtbericht“ und „Protokolle“: Schnellwahl für den Zeitraum (Erfassungszeit, Heute, Gestern, 7 Tage, 30 Tage, Von–bis, ‹ › blättert weiter), Filter Gerät, Art und Protokollliste. Kopfzahlen, Verlauf, Diagramme (Ereignisse nach Uhrzeit, je Tag), Tabelle und Notizen nutzen denselben Datensatz.
- Verlauf aller Geräte untereinander; welche Geräte angezeigt werden, ist über Häkchen einstellbar (pro Browser). Bei mehr als 2 Tagen Minutenwerte, beim Hineinzoomen 125-ms-Werte.
- Klick auf eine Zeile der Ereignistabelle springt im Verlauf aller Geräte zu dieser Störung und markiert sie; Doppelklick oder ▶ öffnet das Ereignis.
- Protokolllisten sind ein Filter; Anlegen, Umbenennen, Löschen und die Notiz der Liste direkt daneben. Markierte Ereignisse „In Liste übernehmen“ oder „Aus Liste nehmen“.
- „🖨 Protokoll“ erstellt das Lärmprotokoll für den gewählten Zeitraum, das Gerät und die Liste (der Knopf der Protokolllisten öffnete bisher nicht das Protokoll – behoben).
- Live-Reiter zeigt nur noch das Live-Bild; Ereignisliste und Statistik sind in „Protokolle“.

## 1.32.0
- Nachtbericht: Zeitraum ist die eingestellte Erfassungszeit („Überwachen ab/bis“), ohne Erfassungszeit der ganze Tag (00:00–24:00, bisher 20:00–08:00).
- Nachtbericht „Verlauf“ (bisher „Ganzer Tag“): standardmäßig alle Geräte untereinander mit gemeinsamer Zeitachse, für denselben Zeitraum wie der Bericht (auch über Mitternacht). Hineinzoomen gilt für alle Geräte; einzelnes Gerät weiter wählbar.
- Nachtberichte werden nicht mehr als Bild in `berichte/` abgelegt. Nachtbericht und Lärmprotokoll entstehen immer aus den gespeicherten Daten; werden Daten gelöscht (von Hand oder mit „Löschen nach (Tagen)“), fehlen sie auch in den Berichten. „⬇ SVG“ erzeugt das Bild weiterhin nur bei Bedarf zum Herunterladen. Bereits vorhandene Bilder in `berichte/` bleiben liegen, bis sie von Hand oder durch „Löschen nach (Tagen)“ entfernt werden.

## 1.31.0
- Ganzer Tag jetzt mit allen Kurven des Live-Bilds außer dem Spektrogramm: zusätzlich die Ebenen tief/mittel/hoch, dominante Frequenz und Klangschwerpunkt (je 125 ms aus den Terzbändern berechnet, das Spektrum selbst wird nicht gespeichert). Beim Zurückspulen lassen sich die Ebenen wie live ein- und ausblenden; auch die Ansicht „Lautstärke-Balken“ funktioniert. Speicherbedarf gemessen etwa 5 MB pro Gerät und Tag. Tage vor dieser Version haben die Ebenen nicht.
- KI-Markierungen im zurückgespulten Bild und im Nachtbericht: oberhalb der Kurve je Störung die erkannte Art in ihrer Farbe (so wird ein Muster über den Tag sichtbar, z. B. Fernseher), beim Hineinzoomen (bis 3 h) jedes Einzelereignis mit Symbol, ab 20 min mit Namen.
- Spektrogramme beim Zurückspulen: bei vielen Störungen gleichmäßig verteilt statt nur die ersten.

## 1.30.0
- Live-Bild zurückspulen über den ganzen Tag: Wird weiter zurückgezogen, als der Arbeitsspeicher reicht (10 min), zeigt die Live-Grafik nahtlos den Tagesverlauf (Spitze je 125 ms, Hintergrund, Schwelle, Störungen rot, „Fernseher an“ blau). Ziehen = zurück- und vorspulen, Mausrad = Zeitraum, Doppelklick oder „Zurück zu Live“ = wieder live.
- Darunter das Spektrogramm nur bei Störungen (aus ihren Lärmspuren, auch den mitgespeicherten), bis 3 h Zeitraum; im Live-Betrieb wie bisher das Live-Spektrogramm.
- Neue Zeiträume im Live-Bild: 1 h, 6 h und „Heute (ganzer Tag)“, laufend aktualisiert.
- Ganzer Tag im Nachtbericht: Spitze als Fläche mit Linie statt Balken, Zeitachse passt sich der Breite an.

## 1.29.0
- Neu: Ganzer Tag. Pegel (Spitze), Hintergrund und Schwelle werden alle 125 ms durchgehend gespeichert, ohne Spektrogramm und ohne Ton (etwa 4–7 MB pro Gerät und Tag, `clips/tag/`). Im Nachtbericht unter „Ganzer Tag“: Gerät wählen, waagerecht ziehen zum Hineinzoomen, Doppelklick für den ganzen Tag; Störungen rot, Werte beim Darüberfahren. Einstellbar pro Gerät (Speichern & Ton → „Ganzen Tag aufzeichnen“, Standard an). Wird mit „Löschen nach (Tagen)“ aufgeräumt.
- Neu: Mitspeichern auf allen Geräten. Löst ein Gerät aus, speichern alle anderen für denselben Zeitraum eine Lärmspur (Pegel und Spektrum, kein Ton, kein Video; `clips/mit/`). Kein zusätzlicher Eintrag in der Liste. Abschaltbar (Speichern & Ton → „Bei einer Störung alle Geräte mitspeichern“).
- Neu: „Vergleich der Geräte“ im Ereignisfenster: Spitze je Gerät, Abstand zum lautesten, Einpegel-Stand und die Spektrogramme aller Geräte untereinander auf derselben Zeitachse und Farbskala. Im Lärmprotokoll als Zeile „Vergleich der Geräte (Spitze): … → am lautesten: …“.
- Neu: Geräte einpegeln (Einstellungen → Geräte). Alle Mikrofone messen gleichzeitig dasselbe gleichmäßige Geräusch (5 s Ruhe, dann 10–30 s Geräusch); die Verstärkung wird so angepasst, dass alle denselben Pegel zeigen wie das Bezugsgerät. „Übernehmen und festhalten“ oder „Nur festhalten (prüfen)“. Jede Messung wird mit Zeit, Ruhepegel, Messwert, Gleichmäßigkeit und Verstärkung alt → neu gespeichert (`clips/einpegeln.json`) und im Lärmprotokoll aufgeführt. In der Geräte-Karte steht „✓ eingepegelt …“ bzw. „⚠ Verstärkung seit dem Einpegeln geändert“.
- Neu: Home-Assistant-Regeln können statt zu pausieren „nur festhalten“: Es wird weiter aufgenommen und mitgeschrieben, wann z. B. der Fernseher lief (`ha_zustand.csv`). Bei jeder Störung steht im Ereignisfenster und im Lärmprotokoll „Fernseher: an/aus“, im ganzen Tag ein blaues Band.

## 1.28.0
- Neu: Nachweis „Über dem Lautesten davor“. Bei jeder Störung wird festgehalten, wie laut es vorher höchstens war (Spitze je 100 ms im eingestellten Hintergrund-Zeitraum, frühere Störungen nicht mitgezählt). Im Ereignisfenster z. B. „+9.0 dB · 10 min“, im Lärmprotokoll „9.0 dB über dem lautesten Pegel der 10 min davor (−41.0 dBFS, ohne Störungen)“. So ist belegbar, dass die Störung lauter war als z. B. ein laufender Fernseher. Gilt für neue Ereignisse, unabhängig von der gewählten Berechnungsart.

## 1.27.0
- „So wird ‚normal‘ berechnet“ hat jetzt fünf Möglichkeiten: Leiseste Momente (wie bisher, Standard), Typischer Pegel (wie bisher), neu Leisester Wert (Minimum), Durchschnitt und Lautester Wert (Maximum) des eingestellten Zeitraums. Bei „Maximum“ zählt die Spitze; die Schwelle liegt dann über dem Lautesten der letzten Zeit.
- Die Berechnungsart ist auch in den Zeitprofilen („Andere Werte zu bestimmten Uhrzeiten“) einstellbar, allgemein oder pro Gerät. Der Hintergrund merkt sich dafür Median und Spitze, ein Wechsel zur Uhrzeit gilt sofort.
- Beschriftung „„Normal“ = Durchschnitt der letzten“ geändert in „„Normal“ wird gelernt aus den letzten“, weil nicht mehr immer der Durchschnitt genommen wird.

## 1.26.1
- Handy: Die Grafik „Ereignisse nach Uhrzeit“ ist nicht mehr breiter als der Bildschirm (Seite ließ sich seitlich schieben). Zahlen über den Balken etwas kleiner, Abstände schmaler.

## 1.26.0
- Neu: Reiter „Protokolle“ mit eigenen Protokolllisten (z. B. „Bad“, „Garten“), jede mit eigener Notiz. Die Gesamtliste enthält weiterhin alle Ereignisse; Listen sammeln zusätzlich.
- Je Gerät wählbar, in welche Listen es automatisch einträgt und zu welcher Uhrzeit (mehrere Listen gleichzeitig, über Mitternacht möglich): Einstellungen → Geräte → Quellen → „Protokolllisten“.
- Von Hand: Ereignisse in der Gesamtliste markieren → „In Liste übernehmen“, oder im Ereignisfenster unter „Listen“. ✕ nimmt ein Ereignis nur aus der Liste.
- Lärmprotokoll je Liste: mit Notiz der Liste, Notiz zum Ereignis und allen Einzelereignissen eingerückt mit Datum und Uhrzeit (Zehntelsekunde), Art, Pegel und deren Notiz.
- Neu: Komplette Sicherung der App (Einstellungen → Allgemein): alles in einer ZIP-Datei – Einstellungen, Geräte, Zeitprofile, Pause-Regeln, Ereignisse, Lärmspuren, KI-Auswertungen, Notizen, Bereiche, Listen, Videos, Ton. Einspielen führt zusammen ohne Doppelte; gleiche Listen-Kennung wird ergänzt, andere Liste mit gleichem Namen kommt als „(importiert)“ dazu. Einstellungen und Geräte optional übernehmen.
- Einstellungen in Reitern: „Geräte“, „Erkennung“, „Zeiten & Pausen“, „Speichern & Ton“, „Allgemein“. Inhalte und Werte unverändert.

## 1.25.7
- Neu: „Notiz zum Ereignis“ – je Gesamtereignis ein Notizfeld im Ereignisfenster, wird beim Verlassen des Feldes gespeichert.
- Neu: Notiz je Einzelereignis – ✎ in der Tabelle „Einzelereignisse“, Bearbeiten direkt in der Zeile (Enter speichert, Esc bricht ab, leer löscht).
- Die Notizen an Zeitstellen (Taste N, Schnell-Tags) bleiben unverändert. Das 📝 in der Ereignisliste zählt alle Notizen eines Ereignisses. Beim Löschen eines Ereignisses wandern alle seine Notizen in den Papierkorb.

## 1.25.6
- Neu: Einzelereignisse. Eine längere Störung bleibt ein Eintrag; darin wird jedes Geräusch einzeln erfasst: jede Spitze über der Schwelle (Klopfen, Tür, Geschirr …) sowie jedes Signal, jeder Stimmlaut und jedes Dauergeräusch mit Dauer. Spitzen, die die KI keiner Art zuordnen kann, werden als „❔ Unbekannt“ erfasst. Tabelle „Einzelereignisse“ im Ereignisfenster mit Uhrzeit (Zehntelsekunde), Art, Sicherheit, Spitzenpegel und Dauer; ein Klick springt an die Stelle.
- „Was vorkam“ wird aus den Einzelereignissen gezählt, inklusive „Unbekannt“. Für bereits ausgewertete Ereignisse wird beides nach dem Start einmalig neu berechnet.

## 1.25.5
- Uhrzeitfelder in den Einstellungen („Überwachen ab/bis“, „Ruhezeit ab/bis“) haben eine Taste ✕ zum Leeren mit einem Klick; bei leerem Feld ist sie ausgegraut.

## 1.25.4
- Neu: „Was vorkam“ – je Störung eine Liste aller erkannten Geräuscharten mit Anzahl, z. B. „✊ Klopfen ×10 · 🍽 Geschirr/Klappern ×3“. Schläge (Klopfen, Tür, Geschirr, Schritte …) werden einzeln über der Schwelle gezählt, Signale und Stimmlaute (Klingel, Hund, Husten, Rufen …) je Vorkommen, Dauergeräusche (Musik, Wasser, Staubsauger …) mit Dauer. Als eigene Spalte in der Ereignisliste (auf dem Handy als Zeile der Karte) und im Ereignisfenster. Für bereits ausgewertete Ereignisse wird die Liste nach dem Start einmalig nachgetragen.

## 1.25.3
- Vorlauf wird markiert: In der Live-Grafik (Pegelspur, Lautstärke-Balken, Spektrogramm) wird beim Auslösen der Vorlauf rückwirkend hellrot markiert, so lang wie für das Gerät eingestellt; im Ereignisfenster ebenso vom Beginn der Aufnahme bis zur Störung. Damit ist sichtbar, was zum Ereignis gehört. Hinweistext im Ereignisfenster ergänzt.

## 1.25.2
- Geräteleiste (Geräte-Chips und „Handy hinzufügen“) steht fest ganz oben über dem Rundlauf und gleitet nicht mehr mit der Folie.
- „Ton nur ohne erkannte Stimmen“ ist immer sichtbar (wie „Löschen nach (Tagen)“), mit dem Hinweis „Nur wenn echter Ton gespeichert wird“.

## 1.25.1
- Neu, optional: „Echten Ton speichern (WAV)“ unter Einstellungen → Aufnahme der Störung, standardmäßig aus, auch pro Gerät. Einschalten nur nach Bestätigung eines rechtlichen Hinweises (§ 201 StGB). Ereignisse mit Ton sind in der Liste mit 🔊 gekennzeichnet; im Ereignis „▶ Abspielen (mit Ton)“, synchron zu Grafik und Video, Start am Beginn der Aufnahme.
- Dazu „Ton nur ohne erkannte Stimmen“ (empfohlen, standardmäßig an): Die KI prüft vor dem Speichern jede Sekunde der Aufnahme samt Vor- und Nachlauf auf menschliche Stimmen (auch Rufen, Lachen, Gesang, TV/Radio); ab 8 % in einer Sekunde wird kein Ton gespeichert, nur die Lärmspur. Ohne Geräuscherkennung wird mit Sicherung nie Ton gespeichert.
- Tonaufnahmen werden nur ausgeliefert und abgespielt, solange die Option für das Gerät an ist; sie kommen nie ins Lärmprotokoll. Beim Löschen eines Ereignisses wandert die WAV-Datei mit in den Papierkorb.
- Anleitung: Angabe zu geräteeigenen Werten korrigiert (das Umfeld gilt für alle Geräte).

## 1.25.0
Kein Ton mehr auf der Festplatte – Lärmspur statt Tonaufnahme:
- Statt WAV-Clips wird je Störung eine **Lärmspur** (`.lsp`) gespeichert: Pegel, Hintergrund, Schwelle und 23 Terzbänder (50 Hz – 8 kHz) in 125-ms-Schritten, plus einstellbares Umfeld davor und danach (Standard 30 s). Kurze Klopfer bleiben sichtbar (Spitzenwert je Block aus 20-ms-Messung). Aus dieser Auflösung lässt sich keine verständliche Sprache zurückgewinnen.
- Grafiken in Ereignis, Liste und Nachtbericht sehen aus wie bisher; „▶ Abspielen“ heißt jetzt „▶ Ablauf zeigen“ und lässt den Zeiger in Echtzeit ohne Ton über Grafik und Spektrogramm laufen.
- Ton liegt nur noch kurz im Arbeitsspeicher. Entfernt: „Anhören (10 s)“, Ausschnitt anhören, Lautstärke und Auto-Lauter.
- Videos werden ohne Tonspur gespeichert.
- Fälschungsschutz: Jede Lärmspur enthält die SHA-256-Prüfsumme der vorherigen Spur desselben Geräts; das Protokoll weist die Prüfsummen der Lärmspuren aus.
- Ältere Ereignisse mit WAV-Clip werden aus ihren gespeicherten Messwerten angezeigt; die WAV-Dateien bleiben unverändert liegen, bis du sie selbst löschst.

KI im Arbeitsspeicher, Marker und Lernen:
- Die KI wertet jede Störung aus, solange der Ton noch im Arbeitsspeicher liegt, und setzt etwa sekündlich Marker mit 49 feineren Arten in die Grafik (z. B. Türknallen, Schrank/Schublade, Geschirr/Klappern, Wasser/Spülung, Staubsauger, Bohren, Rufen/Schreien, Lachen, Babyweinen, Bass, Auto, Sirene, Türklingel, Hund).
- Stimmen werden nur als Art erkannt, nie der Inhalt; eine Spracherkennung gibt es bewusst nicht (§ 201 StGB).
- Neu: **Bereiche benennen** – in der Ereignis-Grafik waagerecht ziehen und einen Namen wählen („Teller klappern“). Benannte Bereiche erscheinen als Band über Grafik und Spektrogramm, in der Liste „Benannte Bereiche“ und im Protokoll.
- Neu: **Lernen** aus benannten Bereichen – ähnliche Stellen in anderen Ereignissen werden als Vorschlag gezeigt („✓ Stimmt“ / „✕ Stimmt nicht“); „🔎 Ähnliche finden“ durchsucht alle gespeicherten Ereignisse.
- Neu, optional: „KI-Fingerabdruck speichern“ (Einstellungen → Allgemein, Standard aus) – 1024 Zahlen je Sekunde, kein Ton rückrechenbar; ermöglicht „Neu bewerten“ ohne Ton und besseres Unterscheiden beim Lernen.
- Einstellungen: „Ton speichern“ entfällt, neu „Umfeld (s)“; nicht mehr benutzte Texte und Stilregeln entfernt.
- Behoben: Statistik-Karten ragten auf dem Handy 1 px über den Rand.

## 1.24.3
Sauberkeits-Prüfung der ganzen Oberfläche (Handy und Desktop, hell und dunkel):
- Behoben: Ereignisliste war nach Speicherzeitpunkt statt nach Beginn sortiert – lange Ereignisse standen zu weit unten. Jetzt immer nach Startzeit.
- Behoben: Einstellungen „Notizen & Protokoll“ zeigten interne Schlüssel („h_quiet_from“, „h_quiet_sunday“); Hilfetexte und ⓘ-Hinweise ergänzt (de/en).
- Behoben: Taste „⋯“ war am Desktop sichtbar und öffnete ein leeres Menü.
- Kopfzeile: alle Bedienelemente gleich hoch (Statusanzeige war höher, „● LIVE“ niedriger).
- Pause-Menü: Eingabezeilen „Minuten“ und „bis“ gleich aufgebaut, OK-Tasten bündig rechts und so hoch wie die Felder.
- Ereignisliste: Filter auf dem Handy als bündige Spalte (Beschriftung links, Auswahl rechts in gleicher Breite); Tasten und Auswahllisten gleich hoch; Zeilenmenü mit fester Symbolspalte, Texte bündig; markierte Karte auf dem Handy als Ganzes hinterlegt.
- Grafiken: Beschriftungen „Schwelle“ und „Hintergrund“ mit Hintergrund wie die Referenzlinien (lesbar über der Kurve); Uhrzeit unten überlappt nicht mehr „● LIVE“; leerer Bereich im Spektrogramm des Ereignisses neutral statt schwarz; „Störungen“-Spur im Nachtbericht auf dem Handy ohne Überlappung.
- Pegelbalken in den Einstellungen: Skala auf dem Handy unter dem Balken statt darüber.
- Kacheln auf dem Handy: Untertitel zweizeilig statt abgeschnitten, Kachelhöhe bleibt gleich.
- Notizen auf dem Handy: Nummer auf Höhe der ersten Zeile, Ruhezeit-Mond 🌙 und Gerät (Nachtbericht) werden wieder angezeigt.
- Quellen: Auge-Taste bleibt neben dem Passwortfeld; Pause-Regel zeigt die Entität auf dem Handy in voller Breite; Eingabefelder auf dem Handy so hoch wie Auswahllisten.
- „Geräusch prüfen“: „Datei wählen“ als Taste erkennbar, kein leeres Ergebnisfeld vor der Auswahl. „⬇ CSV“ in „Alle Notizen“ mit Rahmen wie die anderen Tasten.
- Nachtbericht: Uhrzeitspanne bricht nicht mehr mitten um.
- Einheitlicher Fokusrahmen in Akzentfarbe; veralteter englischer Text zum Rundlauf korrigiert; nicht mehr benutzte Stilregeln entfernt.

## 1.24.2
- Rundlauf als vollständige Folie: Kacheln, Bedienleiste, Geräteleiste, Grafik, Spektrogramm und Live-Bild gleiten gemeinsam als ein Block. Fest bleiben nur Folien-Anzeige (Balken, ⏸, ⚙), Seitenkopf und Ereignisliste.

## 1.24.1
- Symbole und Text in allen Tasten waagerecht und senkrecht mittig (Größe und Form der Tasten unverändert); Menü-Einträge bleiben linksbündig.
- Behoben: Hinweis in der Rundlauf-Leiste überlappte auf dem Handy die Fortschrittsbalken.

## 1.24.0
- Rundlauf als echter Slider: Kacheln und Grafik des aktuellen Geräts schieben sich komplett nach links hinaus, das nächste Gerät gleichzeitig von rechts herein – beide voll sichtbar, ohne Ausblenden oder Doppelbild, mit vorab geladenen aktuellen Daten.
- Anzeigedauer je Gerät (3–60 s) und Geschwindigkeit des Schiebens (0,15–2 s) einstellbar über ⚙ in der Leiste über den Kacheln (pro Browser).
- Manuelle Auswahl eines Geräts (Geräteleiste oder Balken) hält den Rundlauf an, bis die Seite neu geladen oder ▶ gedrückt wird.
- Ereignisliste „Automatisch“: im Rundlauf alle Geräte (springt nicht mehr mit), bei manueller Auswahl nur dieses Gerät. Fest auf „Alle Quellen“ oder ein Gerät weiterhin möglich.

## 1.23.0
- Neu: „Pause durch Home Assistant“ (Einstellungen). Das Add-on fragt alle 5 s selbst den Zustand von Entitäten ab (z. B. Fernseher, Katzenklo) und pausiert solange – mit Nachlauf und Höchstdauer, pro Gerät oder für alle. Keine Automation nötig. Im Zweifel wird aufgenommen (Home Assistant nicht erreichbar, „unavailable/unknown“, Höchstdauer überschritten). Der aktuelle Zustand wird live angezeigt; Pausen stehen im Banner, im Log und in aufzeichnung.csv.
- „Manuell erfassen“ (außerhalb der Erfassungszeit) gilt jetzt nur für das gewählte Gerät. Der Schalter in Home Assistant wirkt weiterhin auf alle.
- Rundlauf: kein Ausblenden und Neuladen mehr. Die Daten des nächsten Geräts werden vorab geladen und zwischengespeichert, das alte Bild gleitet über das neue weg. Gerätebezogene Hinweise erscheinen im Rundlauf kompakt in der Leiste, damit die Seite nicht springt.
- Benötigt Zugriff auf die Home-Assistant-API (homeassistant_api); beim Update einmal bestätigen.

## 1.22.2
- Behoben: Befehle aus Home Assistant (Pause, Aufzeichnung, Manuell erfassen) kamen manchmal nicht an, wenn sich das Add-on sehr schnell mit Mosquitto verband. Das Protokoll zeigt jetzt „MQTT verbunden, Befehle abonniert“.

## 1.22.1
- Notiz-Editor neu gestaltet: Kopfzeile mit Zeit-Feld (−/+ 0,1 s) und echter Uhrzeit, mehrzeiliges Textfeld, Tags in übersichtlichen Gruppen mit dezenter Auswahl (✓), Vorschau-Linie in der Grafik, Tastenhinweis (Enter speichern, Umschalt+Enter neue Zeile, Esc abbrechen).

## 1.22.0
- Neu: Aufzeichnung aus Home Assistant zeitweise anhalten. Neue MQTT-Entitäten: „Pause (Minuten)“ (Zahl), Tasten „Pause 15 min“, „Pause 1 h“, „Fortsetzen“ und Sensor „Pause bis“. Danach geht es automatisch weiter (übersteht Neustarts). Für Automationen: `mqtt.publish` auf `laerm_logger/pause/set` mit Minuten oder JSON `{"minutes": 10, "reason": "Katzenklo"}`; der Grund steht im Banner und in aufzeichnung.csv. Eine von Hand gestoppte Aufzeichnung startet nicht von selbst.
- Neu: Schalter „Manuell erfassen (außerhalb der Zeit)“ in Home Assistant.
- Neu: Ereignis-Entität „Störung erkannt“ für Auslöser in Automationen (event_type `stoerung` mit Quelle, Dauer, Spitze, Datei; `art` sobald die KI die Geräuschart kennt).
- „Aufzeichnung stoppen“ in der App fragt jetzt: für 15 Minuten, 1 Stunde, 3 Stunden oder bis ich wieder starte. Das Banner zeigt das Ende der Pause.

## 1.21.0
- Neu: Notizen zu Zeitpunkten im Clip. In der Ereignisansicht über „📝 Notiz bei …“ (Zeit folgt der Abspiel-Linie), Taste N, langes Drücken oder Rechtsklick auf die Grafik. Mit Text, Schnell-Tags (Herkunft, Art, Stärke, Auswirkung, Maßnahme, Zeuge mit Name, wiederholt), feinjustierbarer Zeit (±0,1 s) und echter Uhrzeit.
- Notizen erscheinen als nummerierte Fähnchen auf Pegelkurve und Spektrogramm und als Tabelle; Klick spielt ab 1 s vorher ab. Bearbeiten, Löschen mit „Rückgängig“.
- 🌙 Ruhezeit wird automatisch markiert (einstellbar unter Einstellungen → Notizen & Protokoll, Standard 22–6 Uhr und sonntags).
- Ereignisliste: „📝 n“ an Ereignissen mit Notizen, Filter „mit Notizen“. Nachtbericht: Notizen je Störung und Block „Notizen dieser Nacht“, auch im SVG.
- Neu: „Alle Notizen“ mit Filtern (Zeitraum, Gerät, Tags, Suche), CSV-Export und druckbarem Lärmprotokoll (als PDF speichern) mit Zusammenfassung, Ruhezeit-Anteil, Häufung, chronologischer Aufstellung, Zeugen, Gegenmaßnahmen und SHA-256-Prüfsummen der Clips (Clips mit Sprache gekennzeichnet).
- Notizen liegen in clips/notes.json (bleibt bei Updates erhalten); beim Löschen eines Ereignisses werden sie aufgehoben, nicht weggeworfen.

## 1.20.0
- Ereignisliste, „Ereignisse nach Uhrzeit“ und „Letzte 14 Tage“ folgen jetzt dem Gerät der Live-Ansicht (auch im Rundlauf, mit Einblenden). Über „Quelle / Gerät“ lässt sich stattdessen „Alle Quellen“ oder ein festes Gerät wählen (wird pro Browser gemerkt).
- Behoben: Die Anzeige „Manuell aktiv“ war riesig breit (Konflikt mit einer anderen Stilregel). Der Zusatz ▶/⏹ erscheint nur noch, wenn er passt (nicht bei „Störung“).

## 1.19.1
- Ereignisliste: Bei „Anzahl“ lässt sich über „eigene …“ jede Zahl von 1 bis 5000 eingeben (wird pro Browser gemerkt).

## 1.19.0
- Rundlauf wechselt jetzt den ganzen Live-Bereich (Kacheln, Pegelgrafik, Spektrogramm, Live-Bild) alle 8 s zum nächsten Gerät, das live ist, mit Animation (Ausblenden, Einschieben, Kacheln nacheinander).
- Fortschrittsbalken zeigt, wann das nächste Gerät kommt; Klick auf einen Balken springt direkt dorthin.
- Der Rundlauf pausiert automatisch, solange man etwas tut: in der Zeit zurückblättern, anhören, Clip abspielen, Dialog oder Nachtbericht offen, Seite im Hintergrund. Nach manueller Auswahl eines Geräts 30 s Pause.

## 1.18.0
- Neu: Rundlauf der Kacheln. Sind mehrere Geräte live, wechseln Pegel, Hintergrund, Schwelle, „Geräusch jetzt“ und Ereignisse alle 6 s zum nächsten Gerät. Über den Kacheln stehen der Gerätename (blau, wenn es nicht das Gerät der Grafik ist) und Punkte zum direkten Wechseln; ⏸/▶ hält den Rundlauf an (wird pro Browser gemerkt). Die Grafik bleibt beim gewählten Gerät.

## 1.17.0
- Neu: Anzahl der Ereignisse in der Liste wählbar (50, 100, 200, 500, 1000 oder alle, bis 5000), wird pro Browser gemerkt.
- Neu: Ereignisse nachträglich mit der KI prüfen: einzeln über ⋮ → „KI neu prüfen“ oder in der Ereignisansicht, mehrere über die Auswahl („Auswahl mit KI prüfen“). Auch bereits eingeordnete Ereignisse werden neu bewertet; eine manuelle Korrektur bleibt erhalten.
- Behoben: Das ⋮-Menü einer Zeile schloss sich manchmal sofort wieder.

## 1.16.0
- Ereignisliste: ein gemeinsamer Player (▶/⏸ mit Fortschrittsring) statt eines Players pro Zeile. Neue Ereignisse brechen die Wiedergabe nicht mehr ab, die Liste wird nur bei Änderungen neu aufgebaut.
- Ereignisliste auf dem Handy als Karten (Zeit, Art, Dauer, Spitze, Gerät, ▶, ⋮); Auswahl zum Löschen über das ⋮-Menü. Datum überall lesbar („So. 04.10. 12:25:20“).
- Startseite auf dem Handy kompakter: „Aufzeichnung stoppen“ und Design im Menü „⋯“, Einstellungen als ⚙-Knopf, Kennzahlen in zwei Reihen, Geräte-Leiste waagerecht scrollbar, größere Touch-Flächen.
- Einstellungen: Bereiche einklappbar (Zustand wird gemerkt), „Wann wird überwacht?“ ganz oben, Rückfrage beim Schließen mit ungespeicherten Änderungen (auch per Escape), auf dem Handy als Vollbild mit kleinerer Pegelanzeige. „Handy hinzufügen“ öffnet direkt den Bereich Quellen.
- Hinweise „Signal sehr leise“ und „Schwelle an der Grenze“ lassen sich wegklicken.
- „Stoppen“ heißt jetzt „Aufzeichnung stoppen“ (Verwechslung mit LIVE). Bedienhinweise auf Touch-Geräten passend zum Wischen.

## 1.15.0
- Video: Live-Bild und Aufnahme pro Gerät getrennt schaltbar („Live-Bild anzeigen“ / „Video aufnehmen“). Drehung 0/90/180/270° pro Gerät (gilt auch für gespeicherte Videos), Live-Bild in drei Größen (S/M/L) und als Vollbild per Klick.
- Handy: Die Seite lässt sich über den Grafiken wieder senkrecht scrollen (senkrechtes Ziehen verschiebt die Skala nur bei ausgeschaltetem Auto); Grafiken auf schmalen Bildschirmen niedriger.
- Ereignisansicht: Abspielen, Lautstärke, Ebenen und Download direkt unter den Kennzahlen, auf dem Handy als Vollbild, Datum lesbar („So 04.10. 12:25:20“). Das Spektrogramm wird nur noch einmal berechnet (flüssigere Wiedergabe).
- Markierung: Der Teil über der Schwelle ist kräftig rot, der Nachlauf nur noch hell (passt zur angezeigten Dauer). Ältere Ereignisse werden wie bisher angezeigt.
- Kontrast verbessert (dunkle Schrift auf hellblauen Knöpfen im Dunkelmodus, dunklere graue Statusanzeige); Beschriftungen für Screenreader ergänzt.
- Nachtbericht: Statistik und Ereignisliste darunter werden im Nachtbericht-Tab ausgeblendet, leere Nächte zeigen „–“ statt 0.
- Live-Daten werden alle 250 ms statt 100 ms abgefragt (schont Akku und Datenvolumen).
- Neu: Laufende Geräuscherkennung im Live-Bild: die Kachel „Geräusch jetzt“ zeigt etwa jede Sekunde die aktuelle Art (oder „ruhig“). Läuft nur für das angezeigte Gerät und nur, wenn die Geräuscherkennung aktiv ist.
- Neu: Das Feld „Außerhalb der Erfassungszeit“ ist anklickbar: damit startet die Erfassung manuell trotzdem („Manuell aktiv“, blau); erneuter Klick beendet sie, sonst endet sie automatisch mit Beginn der nächsten Erfassungszeit.
- Neu: Ebenen für die Kurven (wie bei einer Karte) im Live-Bild und in der Ereignisansicht: Pegel, Hintergrund, Schwelle sowie Tief/Mittel/Hoch (Frequenzbänder), dominante Frequenz und Klangschwerpunkt. Auswahl wird pro Browser gemerkt.

## 1.14.2
- Behoben: Die Markierung „spielt gerade“ im Nachtbericht hängt jetzt am Dateinamen statt an der Listenposition (kein Verrutschen bei sich ändernder Liste).

## 1.14.1
- Nachtbericht im selben Design wie der Rest der Seite (hell und dunkel), Ereignisse als Tabelle (Zeit, Art, Gerät, Dauer, Spitze) mit Art-Filter und scrollbarer Kopfzeile.
- Neu: Design-Umschalter „Auto / Hell / Dunkel“ im Kopf der Seite. Auto folgt dem Design von Home Assistant (wenn auslesbar), sonst dem Browser.

## 1.14.0
- Neu: Videoaufnahme für IP-Webcam-Handys (pro Gerät ein/aus, eigener Ordner). Bilder laufen im Arbeitsspeicher mit, bei einer Störung wird eine mp4 mit Ton und Vorlauf gespeichert.
- Neu: Live-Bild auf dem Startbildschirm, nur wenn das gewählte Gerät Video sendet.
- Neu: Qualität einstellbar (Breite, Bilder/s, Qualität) und eigener Ordner für Clips (unter /share oder /media).
- Neu: Video im Ereignis-Fenster, 🎥 in der Ereignisliste; Löschen und automatisches Löschen berücksichtigen Videos.

## 1.13.0
- Neu: Geräuschart-Erkennung (lokale KI, YAMNet, ca. 7 MB, keine Cloud): Klopfen, Tür, Schritte, Stimme, TV/Musik u. a. mit Sicherheit in %.
- Neu: Spalte „Art“ und Filter in der Ereignisliste, Korrektur im Ereignis-Fenster, Zählung im Nachtbericht, MQTT-Sensor „Letzte Geräuschart“.
- Neu: Alte Ereignisse mit Clip werden automatisch nachträglich eingeordnet.
- Neu: „Geräusch prüfen“ (Audiodatei hochladen) und „Art erkennen“ für den sichtbaren Live-Bereich.

## 1.12.x
- Anhören in voller Qualität (kein Brummen mehr durch Herunterrechnen), Auto-Lauter standardmäßig aus und höchstens +20 dB.
- Brummfilter (50/60 Hz), Lautstärkeregler für Wiedergabe, Ereignis-Fenster mit gespeicherter Grafik und Ton.
- Eigene Referenzlinien pro Gerät.

## 1.11.x und früher
- Zeitprofile mit unterschiedlichen Schwellen pro Gerät, eigene Einstellungen pro Gerät.
- Start/Stopp-Schalter, Zurück-zu-Live-Taste, genauere Skalen und Graphen.
- Mehrere Geräte: Server-Mikrofon, Handys per Browser und IP-Webcam mit Login.
- Nachtbericht, Hilfetexte und Tooltips, Deutsch/Englisch.
