# Glossar

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
[← GasLighter Pro](14-pro.md) · [Inhalt](README.md)
