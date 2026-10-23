# GReport

Eine kurze Hilfe gibt es auch in der App: „?“ oben rechts.

## Notiz jetzt
Oben steht groß die Uhrzeit – sie wird mit der Notiz festgehalten. Text eintippen (Enter speichert, Alt+Enter neue Zeile) oder Tasten der Schnellwahl antippen. Ohne Text bildet GReport aus den Tasten einen Satz, z. B. „Deutliche Schritte von oben“. Der Zeitpunkt ist der Moment des ersten Tastendrucks; unter „🕒 jetzt · Zeit ändern“ lassen sich von und bis von Hand setzen, „läuft noch“ setzt bis = beim Speichern. Mit ⧉ wird der Notizbereich als kleines Fenster abgedockt.

## Rubrik „Zeitpunkt“
Die Rubrik **Zeitpunkt** in der Schnellwahl setzt die Zeit der Notiz – sie hängt kein Wort an, sondern füllt „von“ (und bei ungefähren Tasten „bis“) sichtbar im Zeitfeld:
- **gerade eben**, **vor 5 Min.**, **vor 15 Min.**, **vor 1 Std.** – gerechnet wird immer vom Beginn der Erfassung (erstes Tippen bzw. erster Tastendruck), nicht vom Speichern. Eine zweite Zeit-Taste rechnet wieder vom Erfassungsbeginn.
- **heute Nacht** (22:00–06:00) und **gestern Abend** (18:00–22:00) setzen einen ungefähren Zeitraum. Die Notiz ist als „ungefähr“ markiert (≈); im Zeitfeld lässt sich die Zeit verfeinern.
- **ohne Zeitpunkt** – für allgemeine Notizen und Erinnerungen. Die Option gibt es auch unter „Zeit ändern“.
- Hast du die Zeit von Hand gesetzt, ersetzt eine Zeit-Taste sie erst nach einem Hinweis und erneutem Tippen.
- Gespeichert wird zusätzlich, wann du tatsächlich notiert hast. In der Liste steht dann klein „erfasst 14:32:10, Taste: vor 5 Min.“.
- Eigene Zeit-Tasten legst du unter **Layout anpassen** an: Name und Minuten zurück (z. B. 30) oder eine feste Uhrzeit (z. B. 06:30, die letzte, die schon war).
- In Home Assistant gibt es dafür die Auswahlliste `select.greport_zeitpunkt`.

**Notizen ohne Zeitpunkt** stehen in der Liste mit „ohne Zeitpunkt“ statt Uhrzeit (eigener Filter in Zeitleiste und Tabelle). Sie werden **nicht** an Störungen in GLighter gehängt: GLighter liest die Zeit aus dem Feld „von“, und das bleibt bei diesen Notizen leer. Sortiert und gezählt werden sie nach dem Zeitpunkt, zu dem sie geschrieben wurden. Im Sensor „Letzte Notiz“ erscheinen sie ohne Uhrzeit, im Tagebuch und in Exporten als „ohne Zeitpunkt“.

## Mehr: Zeugen, Polizei, Meldungen, Folgen
- **Zeuge:** Name ins Feld 👤, darunter **Rolle** (Mitbewohner, Nachbar, Hausverwaltung, Vermieter, Polizei, Sonstige) und **Erreichbarkeit** (z. B. Telefon). Bekannte Personen aus der Personenliste (Pro, ⋯ → Personen: Zeilen „Name; Rolle; Erreichbarkeit“) füllen Rolle und Erreichbarkeit selbst aus.
- Unter **Mehr** (alles freiwillig): Häufigkeit (z. B. „jede Nacht“), Polizei gerufen mit Vorgangsnummer, gemeldet an Hausverwaltung, Vermieter oder eine andere Stelle mit Datum, gesundheitliche Folgen oder Änderungen im Alltag, Vermerk zu einem ärztlichen Attest (nur Text – das Attest selbst kannst du als Anlage anhängen) und „Drohung oder Gewalt“. Die Intensität wählst du in der Rubrik „Wie stark“.
- Die Angaben stehen in Zeitleiste, Tabelle, Tagebuch, Exporten und im Bericht.

## Anlagen
📎 unten im Erfassen-Bereich hängt eine oder mehrere Dateien an die Notiz, 📷 nimmt auf dem Handy direkt ein Foto auf. Je Datei gibt es eine Beschreibung. Hochgeladen wird beim Speichern. Erlaubt sind txt, pdf, jpg, png, heic, docx, odt und eml; höchstens 25 MB je Datei und 500 MB zusammen (einstellbar in der Konfiguration: `attach_max_mb`, `attach_total_mb`). Anhängen ist frei.
- Gespeichert wird **unverändert** unter `/share/greport/anlagen/<jahr>/<id>_<name>`, dazu `anlagen/anlagen.json` mit Name, Art, Größe, SHA-256, Zeit des Hochladens, Beschreibung und Notizen. Ob Endung und Inhalt zusammenpassen, prüft GReport beim Hochladen.
- Jede Anlage und jede Änderung daran (Beschreibung, an Notiz gehängt, in den Papierkorb, zurückgeholt, Text erkannt) steht im Änderungsprotokoll. „Nachweis prüfen“ rechnet die Prüfsumme jeder Datei nach.
- In der Liste zeigt 📎 die Anlagen einer Notiz. ⋯ → **Anlagen und Dokumente** zeigt alle mit Vorschau (Bilder, PDF, Text), Original zum Herunterladen und Papierkorb. Entfernen legt die Anlage in den Papierkorb; die Datei bleibt erhalten.
- Sicherung, Bericht und Exporte führen die Anlagen mit Prüfsumme auf; Sicherung und Bericht enthalten die Originale.

## Notizen aus Dokumenten
Bei einer Anlage tippst du **Notizen vorschlagen**. GReport liest den Text auf dem Home-Assistant-Rechner, ohne Internet:
- txt und E-Mail (eml) direkt, Word (docx) und Text-Dokumente (odt) über ihren Inhalt (mit Schutz vor manipulierten ZIP-Dateien),
- PDF über `pdftotext`, gescannte Seiten und Fotos (jpg, png, heic) mit Texterkennung (`tesseract`, Deutsch und Englisch).

Der erkannte Text wird als eigene Datei `<id>_<name>.erkannt.txt` mit eigener Prüfsumme abgelegt; das Original bleibt unberührt.

GReport sucht darin Datums- und Zeitangaben, z. B. 12.03.2025, 12.3., 2025-03-12, „12. März“, „Montag, 10.03.2025“, „am Montag“, „gegen 23 Uhr“, „um 23:15“, „23:15–23:40“, „von 22 bis 1 Uhr“ (über Mitternacht), „gestern Nacht“, und englisch „March 12, 2025“, „at 11:15 pm“, „last night“. Relative Angaben und fehlende Jahre beziehen sich auf das Datum des Dokuments (Datum der E-Mail oder des PDF, sonst das Änderungsdatum der Datei) bzw. auf das zuletzt genannte Jahr. Jede Fundstelle wird eingestuft:
- **genau** – Datum und Uhrzeit stehen vollständig da,
- **ungefähr** – z. B. „gegen 23 Uhr“, Jahr ergänzt, „gestern“, oder nur ein Datum ohne Uhrzeit (dann gilt der ganze Tag),
- **unklar** – z. B. Wochentag passt nicht zum Datum, 03/04/2025 (Tag und Monat vertauschbar) oder kein Bezugsdatum.

Je Fundstelle gibt es einen Vorschlag mit von–bis, dem Satz drumherum, Seite und Zeile sowie passenden Schnellwahl-Wörtern und bekannten Zeugen. Im Prüfdialog wählst du mit Häkchen aus und änderst Zeit, Text, Wörter und Zeuge. Doppelte (±5 Minuten und ähnlicher Text – schon als Notiz vorhanden oder doppelt im Dokument) sind markiert und nicht vorgewählt. **Angelegt wird erst mit „Übernehmen“.** Übernommene Notizen tragen „aus Dokument erkannt“ mit Dokument, Seite und Zeile (`src_doc`); ihre Erfassungszeit ist der Moment der Übernahme, das Datum des Dokuments steht getrennt daneben. Hochladen, Erkennen und Vorschläge ansehen sind frei; **Übernehmen gehört wie der Import zu Pro.**

## Layout anpassen
▦ oben im Erfassen-Bereich (oder ⋯ → **Layout anpassen**) schaltet in den Bearbeiten-Modus direkt auf dem Bildschirm:
- **Tasten:** anlegen (＋ Taste), umbenennen (antippen), löschen (✕ bei eigenen) bzw. ausblenden (● / ○ bei eingebauten), per Ziehen innerhalb und zwischen Rubriken verschieben.
- **Rubriken:** anlegen (＋ Rubrik), umbenennen, einfärben, ausblenden („anzeigen“), löschen (nur eigene – ihre Tasten kommen nach „Eigene“) und am Griff ⠿ in der Reihenfolge verschieben.
- **Bereiche:** Textfeld, Schnellwahl, Zeuge, Mehr und Zeit anordnen.
- **Überschrift und Hinweis** („Notiz jetzt“ und der Satz darunter) direkt anklicken und tippen. Leer = Standardtext. Der eigene Hinweis ersetzt nur den Ruhezustand; Meldungen wie „wird geändert“ oder „Zeit gesetzt“ bleiben. Gespeichert wird in den Einstellungen, also auf allen Geräten gleich.
- **Tastatur:** Pfeiltasten verschieben (←/→ in der Rubrik, ↑/↓ in die Rubrik davor/danach; Rubriken und Bereiche mit den Pfeiltasten am Griff), Eingabetaste benennt um, Entf löscht bzw. blendet aus.
- **Fertig** speichert alles auf einmal, **Abbrechen** verwirft, **Zurücksetzen** stellt nach Rückfrage Namen, Reihenfolge, ausgeblendete Tasten und Rubriken, Überschrift und Hinweis wieder her (eigene Tasten und Rubriken bleiben).

Der Dialog „Schnellwahl verwalten“ bleibt als Alternative. Ausgeblendete Rubriken fehlen auch in Home Assistant; eigene Rubriken bekommen dort eine eigene Auswahlliste (`select.greport_rubrik_…`).

## Liste: Zeitleiste oder Tabelle
Über der Liste wählst du **Zeitleiste** (nach Tagen) oder **Tabelle** – das merkt sich der Browser. **Anzeigen:** Alle, Heute, Letzte 7 Tage, Letzte 30 Tage oder ein eigener Zeitraum; die Überschrift zeigt den Zeitraum. Die Tabelle lässt sich nach jeder Spalte sortieren (Standard: neueste zuerst) und in der Kopfzeile filtern: Datum (Zeitraum), Uhrzeit (mit/ohne Zeitpunkt, per Taste, ungefähr), Text, Schnellwahl-Wörter (mehrere wählbar), Zeuge. ⚙ wählt die Spalten. Die Zeile darüber zählt genau, was angezeigt wird, z. B. „12 von 340 Notizen (gefiltert)“; „Filter löschen“ setzt alles zurück. In der Zelle „Aktionen“ führt die Eingabetaste zu ✎ und 🗑, Esc zurück.

## Nachweis
Damit die Notizen nachvollziehbar bleiben, führt GReport neben `notizen.json` ein Änderungsprotokoll `notizen_protokoll.jsonl`. Es wird nur angehängt:
- Jeder Vorgang – angelegt, geändert, gelöscht, wiederhergestellt – ist ein Eintrag mit Zeit (ms und mit Zeitzone), Art, Kennung und dem vollständigen Inhalt der Notiz danach, beim Ändern auch der Fassung davor. Der erste Eintrag hält die vorhandenen Notizen als Ausgangsstand fest.
- Jeder Eintrag trägt eine Prüfsumme (SHA-256) über sich und die Prüfsumme des vorigen Eintrags (Prüfsummenkette). Zusätzlich gibt es eine zweite Prüfsumme mit einem Schlüssel, der nur im App-Ordner `/data` liegt und nicht bei den Daten in `/share`.
- Geänderte Notizen zeigen „geändert am …“; ein Klick darauf zeigt den Verlauf. Gelöschte Notizen bleiben im Papierkorb und im Protokoll und lassen sich wiederherstellen.
- Wird `notizen.json` außerhalb von GReport geändert, hält GReport das beim nächsten Start als „außerhalb von GReport geändert“ fest – die Änderung wird nicht verschwiegen.

⋯ → **Nachweis prüfen** rechnet die Kette nach, vergleicht sie mit `notizen.json` und zeigt „Unverändert seit …“ oder genau, welcher Eintrag oder welche Notiz abweicht. Die Prüfung ändert nichts (Schnittstelle: `GET verify`). **Nachweis herunterladen** liefert `greport_nachweis_<datum>.json` mit dem ganzen Protokoll, den Prüfsummen und dem Prüfergebnis. Wie die Prüfsumme gebildet wird, steht in der Datei; so kann auch jemand anderes die Kette nachrechnen.

Tagebuch und Exporte (TXT, CSV, JSON) enthalten je Notiz die Erfassungszeit, „Zeit per Taste gesetzt (…)“, „ungefähr“, „geändert“ und die Anlagen und am Ende einen Prüfblock mit Anzahl, erster und letzter Prüfsumme und dem Erstellzeitpunkt. Die Sicherung (ZIP) enthält das Protokoll und die Anlagen. Prüfen, Nachweis-Datei und Sicherung sind frei. Auch die Anlagen werden geprüft: fehlt eine Datei oder passt ihre Prüfsumme nicht mehr, steht das in der Prüfung.

Zeitquelle ist die Uhr von Home Assistant (Systemzeit des Servers); jeder Eintrag nennt die Zeitzone. Ob die Uhr mit einem Zeitserver (NTP) abgeglichen ist, fragt GReport beim Supervisor ab und nennt es in der Prüfung und im Prüfblock („nicht bekannt“, wenn die Auskunft fehlt). Änderungen sind nachvollziehbar und nachträgliche Manipulation ist erkennbar. Wird das Protokoll ganz gelöscht, beginnt eine neue Kette mit neuem Ausgangsstand – „Unverändert seit …“ nennt dann das neue Datum.

## Bericht für Anwalt, Gericht oder Hausverwaltung
⋯ → **Nachweis prüfen** → **Bericht herunterladen** (frei) liefert für den angezeigten Zeitraum eine ZIP-Datei:
- `bericht.txt` und `bericht.json`: Zusammenfassung nach Zeitpunkt (nachts/tagsüber, Wochentage), Art, Intensität, Dauer und Häufigkeit; die Vorfälle chronologisch mit Ereignis- und Erfassungszeit – wurde mehr als 12 Stunden später notiert, ist das mit ⚠ markiert; Zeugen mit Rolle und Erreichbarkeit; Polizei, Meldungen, Folgen und Atteste; eine Zeitachse mit jedem Tag, auch den Tagen ohne Eintrag; Prüfsummen mit Erläuterung des Prüfverfahrens; die Anlagen mit Prüfsumme.
- `rohdaten.csv` (eine Zeile je Notiz), `greport_nachweis_<datum>.json`, `notizen_protokoll.jsonl` und die Anlagen als Originale im Ordner `anlagen/`.

**Für Gewaltschutzantrag (kompakt):** dieselben Angaben ohne Zeitachse, Vorfälle mit Drohung oder Gewalt zuerst.

## Tipps
An den passenden Stellen zeigt GReport kurze Tipps (beim Notieren, bei den Zeit-Tasten, beim Zeugen, unter „Mehr“, im Verlauf und beim Export). „Warum?“ nennt die Quelle. Jeder Tipp lässt sich mit ✕ ausblenden; ⋯ → **Datum und Uhrzeit** → „Tipps zeigen“ schaltet alle ab, „Ausgeblendete Tipps wieder zeigen“ holt sie zurück.

## So hilft GReport bei der Dokumentation
GReport hält fest, was Gerichte nach den ausgewerteten Entscheidungen für die Beschreibung von Lärm und Belästigung heranziehen: Zeitpunkt (von–bis), Art, Intensität, Dauer und Häufigkeit; die Zeit, zu der du notiert hast, getrennt von der Zeit des Ereignisses; Zeugen mit Rolle und Erreichbarkeit; Polizeieinsätze mit Vorgangsnummer, Meldungen an Hausverwaltung oder Vermieter, gesundheitliche Folgen und Atteste. Korrekturen sind offen sichtbar („geändert am …“ mit Verlauf) statt still überschrieben. Änderungen sind nachvollziehbar und nachträgliche Manipulation ist erkennbar.

GReport ersetzt keine Zeugen, kein Gutachten und keine anwaltliche Beratung. Die Tipps sind sachliche Ableitungen aus veröffentlichten Entscheidungen und **keine Rechtsberatung**; sie versprechen keinen Erfolg. Was ein Gericht als Beweis würdigt, entscheidet das Gericht. GReport speichert keinen Ton und wandelt keine Sprache in Text um.

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
- **Gerät „GReport“** (braucht den MQTT-Broker Mosquitto) – auf der Geräteseite „Zu Dashboard hinzufügen“, ohne Adresse und ohne Bastelei:
  - `text.greport_notiz` – freies Textfeld
  - je Gruppe eine Auswahlliste: `select.greport_woher`, `…_was`, `…_wie_stark`, `…_folgen`, `…_massnahmen`, `…_sonstiges`, `…_eigene` – eigene Tasten erscheinen automatisch in ihrer Gruppe, ausgeblendete nicht; dazu `select.greport_zeitpunkt` (setzt die Zeit beim Speichern) und je eigene Rubrik `select.greport_rubrik_…`
  - `text.greport_zeuge` und Knopf `button.greport_speichern` – legt die Notiz mit der Uhrzeit an und leert die Felder
  - `sensor.greport_letzte_notiz` (Attribut `notizen`: die letzten 10 mit Datum, Uhrzeit, Text, Zeuge, Wörtern) und `sensor.greport_notizen_heute`
- **Auswahlliste „Schnellwahl“ und Knopf „Hinzufügen“**: Wort wählen, Knopf drücken – die Notiz ist mit der Uhrzeit angelegt. Der Knopf lässt sich auch in Automationen verwenden (z. B. Zigbee-Taster).

### Dashboard mit einem Klick
⋯ → **Dashboard in Home Assistant**: Name, Adresse (z. B. `gsim-greport`), Seitenleiste, „nur für Administratoren“ und die Bereiche wählen – **Notiz erfassen** (als GReport-Karte oder als einzelne Felder), **Letzte Notizen**, Zähler **heute**, Knopf **GReport öffnen**. **In Home Assistant anlegen** erstellt das Dashboard; ein vorhandenes wird nur nach Rückfrage ersetzt. Ohne Klick ändert GReport nichts. Unter **Als YAML anzeigen** steht dieselbe Vorlage zum Einfügen in den Rohdaten-Editor eines Dashboards.

## Mit GLighter
Ist GLighter installiert, findet es GReport selbst (über `/share/greport`). Mit GLighter Pro erscheinen die Notizen dort an den Störungen, im Verlauf und im Lärmprotokoll; geändert werden sie in GReport.

Menü ⋯ → **GLighter**: „Notizen an GLighter weitergeben“ ein- oder ausschalten (Standard: an). Ausgeschaltet zeigt GLighter (ab 1.76.3) keine Notizen aus GReport mehr; die Notizen bleiben in GReport.

## Sicherung
Menü ⋯ → **Sicherung herunterladen (ZIP)** ist immer frei und enthält Notizen, Schnellwahl, Personen, Einstellungen, das Änderungsprotokoll und alle Anlagen (auch die im Papierkorb) mit dem erkannten Text. Mit Pro zusätzlich eine tägliche Sicherung nach `/share/greport/sicherung` (14 Tage); sie enthält das Verzeichnis der Anlagen mit Prüfsummen, aber nicht die Dateien selbst – die ändern sich nie und würden sonst 14-mal Platz belegen.

## Textdatei & Import/Export (Pro)
Menü ⋯ → **Textdatei & Import/Export**.

**Tagebuch als Textdatei:** Einschalten und Datei wählen (in `/share/greport/export` oder `/media/greport`, Standard `/share/greport/export/greport_tagebuch.txt`). GReport führt die Datei nach Tagen:

```
So. 18.10.2026
05:07:12  [Klopfen, oben, stark] Bass dröhnt seit 22 Uhr – Zeuge: Anna
05:15:08  [Schritte, oben]

Mo. 19.10.2026
23:41:10 – 23:45:00  [Tür, Treppenhaus] Tür knallt mehrmals (geändert)
```

Gibt es den Tag schon, kommt die Notiz nach Uhrzeit darunter, sonst entsteht am Ende ein neuer Absatz mit dem Datum. Geänderte Notizen werden ersetzt (mit „(geändert)“), gelöschte entfernt. Format Text oder CSV, auf Wunsch eine Datei pro Monat (`…_2026-10.txt`). Die Datei wird von GReport geführt – eigene Änderungen darin gehen beim nächsten Schreiben verloren. Maßgeblich bleiben die Daten von GReport mit dem Änderungsprotokoll.

**Export:** Text, CSV oder JSON – herunterladen oder direkt in eine Datei schreiben.

**Import:** Pfad einer Datei auf dem Home-Assistant-Rechner eintragen (aus `/share/greport/import` oder `/media`) oder eine Datei hochladen, dann **Vorschau** und **Übernehmen**. Gelesen werden das Text-Tagebuch, CSV und JSON (auch die Exporte von GReport). Doppelte Notizen (gleiche Kennung oder gleiche Zeit, gleicher Text, gleiche Wörter) werden übersprungen, unbekannte Wörter als eigene angelegt.

## Sicherheit
- GReport schreibt Dateien (Tagebuch, Export) nur in eigene Ordner: `/share/greport/export` und `/media/greport`. Die eigenen Datendateien und die Ordner anderer Apps (z. B. `/share/gaslighter`) sind gesperrt. Eine vorhandene Datei überschreibt GReport nur, wenn es sie selbst angelegt hat – sonst entsteht ein neuer Name mit Zähler (`…_2.txt`). Gelesen (Import) wird nur aus `/share/greport/import` und `/media`. Ein früher eingestellter Tagebuch-Pfad außerhalb dieser Ordner gilt nicht mehr; der Dialog zeigt dann einen Hinweis und den neuen Ort.
- In CSV-Dateien bekommen Werte, die mit `=`, `+`, `-`, `@`, Tabulator oder Zeilenumbruch beginnen, ein `'` davor, damit Tabellenprogramme sie nicht als Formel ausführen. Der Import nimmt das wieder weg.
- Notizen aus Home Assistant (MQTT, Automationen): höchstens 1 je Sekunde (kurz bis 5 hintereinander) und 500 am Tag; aus der App unbegrenzt.
- Anfragen mit ungültiger Länge werden abgelehnt; hängende Verbindungen nach 30 Sekunden getrennt. In der Dashboard-Vorlage werden Notiztext und Zeuge so ausgegeben, dass sie keine Links, Bilder oder Formatierungen einschleusen.

## Pro
Ein GReport-Schlüssel oder ein GLighter-Pro-Schlüssel (Menü ⋯ → Pro). Geprüft wird offline.

Frei: alles zum Notieren, 5 eigene Wörter, Anlagen, Texterkennung und Vorschläge aus Dokumenten ansehen, Nachweis prüfen, Bericht, Sicherung. Pro: mehr eigene Wörter, mehrere Zeugen und Personenliste, Textdatei, Export und Import, Vorschläge aus Dokumenten übernehmen, tägliche Sicherung.
