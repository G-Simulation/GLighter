# Live-Ansicht

Der Reiter **Live** zeigt, was gerade passiert: Kacheln mit den aktuellen Werten, die Grafik der letzten Minuten, das Spektrogramm und die Ereignisse von heute.

## Kopfzeile {#kopfzeile}

| Element | Bedeutung |
|---|---|
| **LIVE** | Die Anzeige folgt der Gegenwart. Nach dem Zurückspulen hier wieder zurück zu Live. |
| **Ruhig / STÖRUNG** | Zustand des gewählten Geräts. Rot = gerade über der Schwelle. Außerhalb der Überwachungszeit lässt sich hier „trotzdem erfassen“ einschalten. |
| **Aufzeichnung stoppen** | Hält die Aufzeichnung an (wird in `aufzeichnung.csv` festgehalten). Am Handy im Menü ⋯. |
| **🌓 Auto / ☀ / 🌙** | Hell, dunkel oder wie Home Assistant. |
| **⚙ Einstellungen** | Alle Einstellungen, siehe [Einstellungen](#einstellungen). |

## Geräteleiste und Kacheln {#kacheln}

Die Leiste unter der Notiz zeigt alle Geräte mit Anzahl der Störungen heute. Antippen wählt das Gerät. Sind mehrere Geräte live, wechselt die Ansicht im **Rundlauf** automatisch (Dauer über ⚙ in der Leiste).

- **Pegel** – aktueller Spitzenpegel.
- **Hintergrund** – der gelernte „normale“ Pegel.
- **Schwelle** – ab hier zählt es als Störung; darunter steht, wie sie berechnet wird.
- **Geräusch jetzt** – was die KI gerade hört (nur mit eingeschalteter Geräuscherkennung).
- **Ereignisse** – Störungen heute und insgesamt.

## Die Grafik {#grafik}

![Live-Grafik mit Schwelle, Hintergrund und Referenzlinien](livegraph_{lang}.png)

- **Blaue Fläche** = Pegel, **graue Linie** = Hintergrund, **orange gestrichelt** = Schwelle, **rot** = Störung, gepunktete farbige Linien = eigene Referenzlinien (z. B. „Fernseher −70 dB“).
- **Pegelspur / Lautstärke-Balken** schaltet die Darstellung um.
- **🗂 Ebenen** blendet Kurven ein und aus: Hintergrund, Schwelle, tief/mittel/hoch, dominante Frequenz, Klangschwerpunkt.
- **Zeitfenster** und **− / +** ändern die gezeigte Zeit; **Auto** passt die Höhe an.
- Darunter das **Spektrogramm**: Frequenz über Zeit, hell = laut. Tiefe Geräusche (Bass, Trittschall) liegen unten, Stimmen und Geschirr weiter oben.

### Bedienung {#bedienung}

| Am Computer | Am Handy / Tablet |
|---|---|
| Mausrad oder Touchpad = Zeit zoomen | zwei Finger spreizen = Zeit zoomen |
| Ziehen oder seitlich wischen = in der Zeit blättern | waagerecht wischen = blättern, senkrecht = Seite scrollen |
| Umschalt + Ziehen = Bereich aufziehen und hineinzoomen | − / + |
| Umschalt + Mausrad oder Mausrad über der dB-Beschriftung = Höhe zoomen (unten bündig) | „Auto“ |
| Doppelklick = zurück zu Live | Doppeltippen = zurück zu Live |
| Über eine Störung fahren = Einzelheiten | Störung antippen = Einzelheiten |

Weiter zurück als die letzten 10 Minuten zeigt die Grafik den **ganzen Tag** aus der Tagesaufzeichnung (Zeitfenster 1 h, 6 h oder „Heute“).

## 📝 Notiz jetzt {#notiz}

![Notiz-Leiste mit Schnell-Merkmalen](notiz_{lang}.png)

Für das, was du gerade hörst – einfach lostippen oder Merkmale antippen (oben, unten, Klopfen, Bass, aufgewacht …).

- **Ohne eigene Uhrzeit**: Liegt kurz vorher eine Störung (Einstellung „Notiz zuordnen“, Standard 5 min), gilt die Notiz für sie. Die Leiste zeigt vorher, wohin sie kommt.
- **läuft noch**: Die Notiz bekommt einen Zeitraum von der ersten Eingabe bis zum Speichern.
- **Mehr …** öffnet den Dialog mit von/bis, Gerät und Zeuge.
- [[Strg]] + [[Enter]] speichert. Am Handy ist die Leiste zunächst zugeklappt.

## 🏷 Bereich markieren {#markieren}

![Bereich markieren und einer Art zuordnen](markieren_{lang}.png)

1. „🏷 Bereich markieren“ antippen – über der Grafik erscheint ein Hinweis mit **Fertig**.
2. Den Bereich waagerecht aufziehen (0,15 s bis 2 min).
3. Eine **vorhandene Art** antippen (Tonprofil 🧩 oder benannter Bereich 🏷) oder einen neuen Namen eingeben – gleicher Name = gleiche Art, die KI lernt daraus. Siehe [KI](#ki/lernen).

## Ereignisse heute {#ereignisse-heute}

Die Liste unten zeigt alle Störungen des Tages (alle Geräte oder das gewählte). Ein Klick öffnet die Störung, siehe [Ereignis-Fenster](#ereignis). Spalten wählst du über ⚙. Am Handy erscheinen die Einträge als Karten.
