# Einstellungen von A bis Z

![Einstellungen](../../gaslighter/app/web/hb/einstellungen_de.png)

Ganz oben wählst du **Alle Geräte** oder ein einzelnes Gerät. Beim Gerät lassen sich mit „Eigene Einstellungen für dieses Gerät“ abweichende Werte festlegen (Schwelle, Mindestdauer, Aufnahmezeit, Speichern). Die Leiste oben zeigt live Pegel, Hintergrund, Schwelle und die **Vorschau** (lila) deiner noch nicht gespeicherten Einstellungen. ⓘ erklärt jede Einstellung; „Hilfe anzeigen“ blendet die Texte aus.

<a id="geraete"></a>

## Geräte

- **Quellen (Mikrofone)** – siehe [Geräte](06-geraete.md).
- **Geräte einpegeln (gleich laut stellen)** – siehe [Einpegeln](06-geraete.md#einpegeln).
- **Mikrofon**<a id="s_audio"></a> – Eingang am Server, Buchse, Lautstärke, Tonqualität (16000 Hz reicht für Klopfen).

<a id="erkennung"></a>

## Erkennung

<a id="s_thr"></a>

### Wann gilt etwas als Störung?

> **🔒 Pro:** Ohne Pro sind diese Werte nur zum Ansehen; GasLighter arbeitet mit den Standardwerten. Ändern lassen sie sich mit [GasLighter Pro](14-pro.md).

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

<a id="s_ki"></a>

### Geräuschart erkennen (KI)

**Geräuschart erkennen (lokale KI)** – ordnet Störungen ein (Tür, Klopfen, Musik …), kein Ton wird gespeichert. **KI-Fingerabdruck zu jeder Störung speichern** – bessere Unterscheidung beim Lernen und „Neu bewerten“ ohne Ton. **KI-Fingerabdruck auch zwischen den Störungen speichern** – durchgehend, für „Neu untersuchen“; siehe [KI-Fingerabdruck](05-ki.md#fingerabdruck).

**Tonprofile** – siehe [KI](05-ki.md#tonprofile). **Andere Werte zu bestimmten Uhrzeiten** (Zeitprofile)<a id="s_sched"></a> – z. B. nachts empfindlicher, allgemein oder je Gerät.

<a id="zeiten"></a>

## Zeiten & Pausen

- **Wann wird überwacht?**<a id="s_time"></a> – Überwachen ab / bis (beide leer = rund um die Uhr, über Mitternacht möglich). Außerhalb davon wird nichts gezählt; über die Anzeige oben lässt sich trotzdem erfassen.
- **Ruhezeit**<a id="s_notes"></a> – Ruhezeit ab / bis (üblich 22:00–6:00), Sonntag ganztägig Ruhezeit. Notizen und Störungen in der Ruhezeit bekommen 🌙.
- **Andere Werte zu bestimmten Uhrzeiten** – siehe oben (Zeitprofile).
- **Home Assistant: pausieren oder festhalten**<a id="s_ha"></a> – siehe [Home Assistant](07-home-assistant.md#regeln).

<a id="speichern"></a>

## Speichern & Sicherung

<a id="s_rec"></a>

### Was wird gespeichert?

| Einstellung | Bedeutung |
|---|---|
| Umfeld vor und nach der Störung (s) | so viele Sekunden vor und nach der Störung werden beim Ansehen gezeigt |
| Tagesaufzeichnung mit Ebenen | tief/mittel/hoch, Frequenz für den ganzen Tag (+1–2 MB pro Gerät und Tag) |
| Tagesaufzeichnung mit Spektrum | Spektrogramm für jeden Moment (+3–8 MB pro Gerät und Tag) |
| Bei einer Störung alle Geräte mitspeichern | die anderen Geräte speichern für denselben Zeitraum eine Lärmspur (kein Ton) – zum Vergleich der Räume |

<a id="s_wav"></a>

### Echten Ton speichern (nicht empfohlen)

Standard **aus**. Eingeschaltet wird zu jeder Störung zusätzlich eine WAV-Datei gespeichert. **Ton nur ohne erkannte Stimmen** (empfohlen) verhindert das Speichern, sobald die KI irgendwo Stimmen erkennt. Lies vorher [Rechtliches](12-rechtliches.md).

<a id="s_video"></a>

### Video

Video-Breite, Bilder pro Sekunde, Videoqualität (für IP-Kameras und Handys).

<a id="s_place"></a>

### Speicherort

**Ordner für Lärmspuren** – leer = Standard. Nur ändern, wenn neue Lärmspuren woanders liegen sollen (z. B. `/media/gaslighter`). Für eine Kopie auf dem NAS ist die **tägliche Sicherung** gedacht, nicht dieser Ordner.

<a id="s_keep"></a>

### Aufbewahren & automatisch löschen

**Alte Aufnahmen automatisch löschen** und **Löschen nach (Tagen)** – aus = es wird nie etwas gelöscht. Mit tägliche Sicherung wird nur gelöscht, was geprüft im Ziel liegt.

<a id="s_backup"></a>

### Sicherung

**Sicherung herunterladen / einspielen (ZIP)** – immer kostenlos. **Tägliche Sicherung** auf Netzlaufwerk, NAS oder USB (Pro). Beides siehe [Sicherung](09-sicherung.md).

<a id="allgemein"></a>

## Allgemein

- **Sprache**<a id="s_misc"></a> – Deutsch, Englisch oder wie der Browser.
- **Protokoll & Notizen**<a id="s_list"></a> – **Störungen zusammenfassen bei bis zu (s) Abstand** (Gruppen in der Liste), **Notiz gehört zur Störung, wenn bis zu (min) danach**.
- **GasLighter Pro** – siehe [Pro](14-pro.md).
- **Zurücksetzen** – siehe [Zurücksetzen](09-sicherung.md#zuruecksetzen).
- **Diagnose** – Angaben zu Mikrofon und Soundkarte für die Fehlersuche.

---
[← Unterbrechungen, Datenkette und Updates](10-unterbrechungen.md) · [Inhalt](README.md) · [Rechtliches und Datenschutz →](12-rechtliches.md)
