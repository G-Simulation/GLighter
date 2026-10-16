# Schnellstart in 5 Minuten

GLighter hört dauerhaft mit und schreibt ein **Lärmprotokoll**: Wann war es wie laut, wie lange, welche Art von Geräusch – mit Prüfsummen, damit niemand die Daten unbemerkt ändern kann. **Ton wird dabei nicht gespeichert**, nur Messwerte.

![Die Live-Ansicht direkt nach dem Start](live_{lang}.png)

## 1. Mikrofon anschließen {#mikrofon}

- Ein USB-Mikrofon oder ein Mikrofon an der Soundkarte des Home-Assistant-Rechners anschließen. Der Eintrag „Server-Mikrofon“ ist schon da.
- Weitere Räume: Handys als Mikrofon hinzufügen, siehe [Geräte](#geraete).
- Zeigt die Kachel **Pegel** einen Wert und bewegt sich die Kurve bei einem Klopfer, kommt Ton an. Erscheint der blaue Hinweis „Das Signal ist sehr leise“, die Mikrofon-Lautstärke erhöhen (⚙ Einstellungen → Geräte → Mikrofon) oder die richtige Buchse wählen.

## 2. Schwelle prüfen {#schwelle}

Eine **Störung** wird gezählt, wenn der Pegel über der **Schwelle** liegt (orange gestrichelte Linie). Standard: „Passt sich an, mit Grenzen“ – die Schwelle liegt 10 dB über dem normalen Hintergrund, aber nie unter −95 und nie über −30 dBFS.

- Ein lautes Klopfen sollte deutlich über die Linie gehen und rot markiert werden.
- Werden zu viele Kleinigkeiten gezählt: „Wie viel lauter als normal?“ erhöhen (z. B. 12 dB). Wird zu wenig gezählt: verringern.
- Einzelheiten: [Einstellungen → Erkennung](#einstellungen/erkennung).

> **Tipp:** Pegel sind **dBFS** – relativ zur Soundkarte, deshalb negativ (−80 sehr leise, −20 sehr laut). Wichtig ist der Abstand zum Hintergrund, nicht der absolute Wert. Siehe [Glossar](#glossar).

## 3. Mehrere Mikrofone einpegeln (optional) {#einpegeln}

Wenn du mehrere Geräte vergleichen willst: ⚙ Einstellungen → Geräte → **Geräte einpegeln**. Alle Mikrofone nebeneinander legen, 5 s Ruhe, dann ein gleichmäßiges Geräusch. Danach zeigen alle Geräte beim selben Geräusch denselben Wert.

## 4. Erste Störung ansehen {#erste-stoerung}

- Im Reiter **Live** steht unten „Ereignisse heute“. Ein Klick öffnet die Störung mit Grafik, Spektrogramm und erkannter Art.
- Im Reiter **Protokolle** siehst du ganze Tage und Wochen, den Verlauf mit allen Geräten untereinander und die Liste aller Störungen.
- Was du gerade hörst, trägst du oben unter **📝 Notiz jetzt** ein („Schritte oben“, „Bass“) – die Notiz kommt automatisch zur letzten Störung.

## 5. Sichern und Updates {#sichern}

- Regelmäßig unter ⚙ Einstellungen → Speichern & Sicherung → **Sicherung herunterladen** eine Sicherung ziehen. Siehe [Sicherung](#sicherung).
- Updates ohne Aufnahmelücke: neuen Ordner nach `\\homeassistant\share\gaslighter_update\` kopieren. Siehe [Updates](#unterbrechungen/updates).

> **Wichtig:** GLighter ist eine Gedächtnisstütze und Dokumentation, keine geeichte Lärmmessung in dB(A). Für Vermieter, Hausverwaltung oder Behörden zählt vor allem: regelmäßig, nachvollziehbar, mit eigenen Notizen. Siehe [Lärmprotokoll](#drucken/laermprotokoll).
