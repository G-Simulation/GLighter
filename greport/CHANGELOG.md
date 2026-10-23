# Changelog

## 1.7.1
- **Neu: Weitergabe an GLighter einstellbar.** Unter ⋯ → **GLighter** lässt sich „Notizen an GLighter weitergeben“ ein- und ausschalten (Standard: an). Aus: GLighter zeigt keine Notizen aus GReport mehr – an den Störungen, im Verlauf und im Lärmprotokoll. Die Notizen bleiben in GReport unverändert. Die Änderung gilt sofort. Das 🔗 oben zeigt, wenn die Weitergabe aus ist.
- Braucht GLighter ab 1.76.3. Ältere GLighter zeigen die Notizen weiterhin.

## 1.7.0
- **Behoben:** Tagebuch und Exporte enthalten wieder alle Notizen. Bisher waren es höchstens 5000, die ältesten fielen still weg.
- **Behoben:** Notizen während der Zeitumstellung (z. B. 25.10.2026 zwischen 2 und 3 Uhr) werden mit der richtigen Uhrzeit gespeichert. Die Oberfläche speichert jetzt immer mit Zeitzone, und beim Bearbeiten bleibt ein unverändertes Zeitfeld exakt erhalten.
- Freischaltung mit dem Schlüssel aus dem Shop unverändert.

## 1.6.3
- **Pro mit dem Schlüssel aus dem Shop:** Der Schlüssel aus der Kauf-E-Mail (GReport oder GLighter) funktioniert jetzt direkt. GReport prüft ihn beim Eintragen einmal online bei gsimulations.de und arbeitet danach wieder ohne Internet.

## 1.6.2
- **Eigene Karte „GReport“:** GReport bringt jetzt eine fertige Dashboard-Karte mit. Sie wird beim Start automatisch eingerichtet und steht danach unter „Karte hinzufügen“ → „Nach Karte“ → **GReport**. Darin: Notiz, alle Auswahllisten (Woher, Was, Wie stark …), Zeuge und „Speichern“, dazu „Notizen heute“ und „Letzte Notiz“. Funktioniert für alle Benutzer, auch ohne Administratorrechte – ohne Adresse und ohne Bastelei.
- **Eigener Bereich „GReport“:** Bei einer neuen Installation legt Home Assistant das Gerät gleich im Bereich „GReport“ an. In „Zum Dashboard hinzufügen“ → „Nach Entität“ stehen alle GReport-Felder damit unter **GReport**. (Bei bestehenden Installationen den Bereich einmal von Hand zuweisen: Einstellungen → Geräte → GReport → Bereich.)
- Dafür braucht GReport jetzt Schreibzugriff auf den Home-Assistant-Ordner `www/greport` (nur für die Kartendatei).

## 1.6.1
- Neues GReport-Logo und App-Symbol (im App-Store, in der App und als Browser-Symbol).

## 1.6.0
- **Notiz direkt im Dashboard:** Das Gerät „GReport“ in Home Assistant hat jetzt alles, was man für eine Notiz braucht: Textfeld „Notiz“, je Gruppe eine Auswahlliste (Woher, Was, Wie stark, Folgen, Maßnahmen, Sonstiges, Eigene – eigene Tasten kommen automatisch in ihre Gruppe), „Zeuge“ und den Knopf „Speichern“. Danach sind die Felder wieder leer.
- **Neue Sensoren:** „Letzte Notiz“ (mit den letzten 10 Notizen als Attribut, z. B. für eine eigene Notizen-Kachel) und „Notizen heute“.
- Damit funktioniert bei jedem Nutzer „Zu Dashboard hinzufügen“ auf der Geräteseite – ohne Adresse und ohne Bastelei. „Schnellwahl“ und „Hinzufügen“ bleiben für Automationen.

## 1.5.1
- Behoben: Die Abschnitte von „Notiz jetzt“ lassen sich wieder ein- und ausblenden, auch im abgedockten Fenster. Dafür gibt es oben eine schmale Leiste mit Textfeld, Schnellwahl, Zeuge und Zeitraum. Ein ausgeblendeter Abschnitt zeigt, wie viel darin gewählt ist. Der Zustand wird pro Browser gemerkt.
- Im abgedockten Fenster ziehen sich die Zeilen nicht mehr in die Höhe, wenn Abschnitte ausgeblendet sind.

## 1.5.0
- **Dezentere Tasten:** Jede Taste hat jetzt einen dünnen Rahmen in der Farbe ihrer Gruppe, der Punkt davor entfällt. Gewählte Tasten sind leicht in der Gruppenfarbe getönt. Die Marken in der Liste sehen genauso aus.
- **Neu (Pro), unter „Schnellwahl verwalten“:**
  - **Eigene Tasten höchstens:** frei einstellbar von 5 bis 200, Standard 40.
  - **Je Gruppe zeigen:** zum Beispiel nur die ersten 4 je Gruppe, der Rest steckt hinter „+2 mehr“. 0 heißt alle. Gewählte Tasten bleiben immer sichtbar.

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
