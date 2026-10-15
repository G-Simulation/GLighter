# Einstellungen von A bis Z

![Einstellungen](einstellungen_{lang}.png)

Ganz oben wählst du **Alle Geräte** oder ein einzelnes Gerät. Beim Gerät lassen sich mit „Eigene Einstellungen für dieses Gerät“ abweichende Werte festlegen (Schwelle, Mindestdauer, Aufnahmezeit, Speichern). Die Leiste oben zeigt live Pegel, Hintergrund, Schwelle und die **Vorschau** (lila) deiner noch nicht gespeicherten Einstellungen.

**🎯 Schwelle automatisch einstellen** {#auto} (🔒 Pro) – schlägt Werte für „Wann gilt etwas als Störung?“ vor, für das oben gewählte Gerät (auch ein verbundenes Handy). **Aus der letzten Nacht** nimmt die Ruhezeit der letzten Nacht ohne die Störungen darin – kein Warten, am zuverlässigsten. **Jetzt messen** (30 s, 1 min oder 5 min): in der Zeit leise sein; war es zwischendurch deutlich lauter, steht „Messung gestört – bitte wiederholen“. Der Vorschlag steht als Tabelle „jetzt → Vorschlag“ da; erst **Übernehmen** trägt ihn ein (lila Vorschau), **Speichern** behält ihn. ⓘ erklärt jede Einstellung; „Hilfe anzeigen“ blendet die Texte aus.

## Geräte {#geraete}

- **Quellen (Mikrofone)** – siehe [Geräte](#geraete).
- **Geräte einpegeln (gleich laut stellen)** – siehe [Einpegeln](#geraete/einpegeln).
- **Mikrofon** {#s_audio} – Eingang am Server, Buchse, Lautstärke, Tonqualität (16000 Hz reicht für Klopfen).

## Erkennung {#erkennung}

### Wann gilt etwas als Störung? {#s_thr}

> **🔒 Pro:** Ohne Pro sind diese Werte nur zum Ansehen; GasLighter arbeitet mit den Standardwerten. Ändern lassen sie sich mit [GasLighter Pro](#pro).

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

### Geräuschart erkennen (KI) {#s_ki}

**Geräuschart erkennen (lokale KI)** – ordnet Störungen ein (Tür, Klopfen, Musik …), kein Ton wird gespeichert. **KI-Fingerabdruck zu jeder Störung speichern** – bessere Unterscheidung beim Lernen und „Neu bewerten“ ohne Ton. **KI-Fingerabdruck auch zwischen den Störungen speichern** – durchgehend, für „Neu untersuchen“; siehe [KI-Fingerabdruck](#ki/fingerabdruck).

**Tonprofile** – siehe [KI](#ki/tonprofile). **Andere Werte zu bestimmten Uhrzeiten** (Zeitprofile) {#s_sched} – z. B. nachts empfindlicher, allgemein oder je Gerät.

## Zeiten & Pausen {#zeiten}

- **Wann wird überwacht?** {#s_time} – Überwachen ab / bis (beide leer = rund um die Uhr, über Mitternacht möglich). Außerhalb davon wird nichts gezählt; über die Anzeige oben lässt sich trotzdem erfassen.
- **Ruhezeit** {#s_notes} – Ruhezeit ab / bis (üblich 22:00–6:00), Sonntag ganztägig Ruhezeit. Notizen und Störungen in der Ruhezeit bekommen 🌙.
- **Andere Werte zu bestimmten Uhrzeiten** – siehe oben (Zeitprofile).
- **Home Assistant: pausieren oder festhalten** {#s_ha} – siehe [Home Assistant](#home-assistant/regeln).

## Speichern & Sicherung {#speichern}

### Was wird gespeichert? {#s_rec}

| Einstellung | Bedeutung |
|---|---|
| Umfeld vor und nach der Störung (s) | so viele Sekunden vor und nach der Störung werden beim Ansehen gezeigt |
| Tagesaufzeichnung mit Ebenen | tief/mittel/hoch, Frequenz für den ganzen Tag (+1–2 MB pro Gerät und Tag) |
| Tagesaufzeichnung mit Spektrum | Spektrogramm für jeden Moment (+3–8 MB pro Gerät und Tag) |
| Bei einer Störung alle Geräte mitspeichern | die anderen Geräte speichern für denselben Zeitraum eine Lärmspur (kein Ton) – zum Vergleich der Räume |

### Echten Ton speichern (nicht empfohlen) {#s_wav}

Standard **aus**. Eingeschaltet wird zu jeder Störung zusätzlich eine WAV-Datei gespeichert. **Ton nur ohne erkannte Stimmen** (empfohlen) verhindert das Speichern, sobald die KI irgendwo Stimmen erkennt. Lies vorher [Rechtliches](#rechtliches).

### Video {#s_video}

Video-Breite, Bilder pro Sekunde, Videoqualität (für IP-Kameras und Handys).

### Speicherort {#s_place}

**Ordner für Lärmspuren** – leer = Standard. Nur ändern, wenn neue Lärmspuren woanders liegen sollen (z. B. `/media/gaslighter`). Für eine Kopie auf dem NAS ist die **tägliche Sicherung** gedacht, nicht dieser Ordner.

### Aufbewahren & automatisch löschen {#s_keep}

**Alte Aufnahmen automatisch löschen** und **Löschen nach (Tagen)** – aus = es wird nie etwas gelöscht. Mit tägliche Sicherung wird nur gelöscht, was geprüft im Ziel liegt.

### Sicherung {#s_backup}

**Sicherung herunterladen / einspielen (ZIP)** – immer kostenlos. **Tägliche Sicherung** auf Netzlaufwerk, NAS oder USB (Pro). Beides siehe [Sicherung](#sicherung).

## Allgemein {#allgemein}

- **Sprache** {#s_misc} – Deutsch, Englisch oder wie der Browser.
- **Protokoll & Notizen** {#s_list} – **Störungen zusammenfassen bei bis zu (s) Abstand** (Gruppen in der Liste), **Notiz gehört zur Störung, wenn bis zu (min) danach**.
- **GasLighter Pro** – siehe [Pro](#pro).
- **Zurücksetzen** – siehe [Zurücksetzen](#sicherung/zuruecksetzen).
- **Diagnose** – Angaben zu Mikrofon und Soundkarte für die Fehlersuche.
