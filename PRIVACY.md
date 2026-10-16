# Datenschutz / Privacy

## Deutsch

**Kurz:** GLighter läuft vollständig auf deinem Home-Assistant-Rechner. Es gibt keine Cloud, kein Konto, keine Telemetrie. G-Simulation erhält keine Daten.

**Was gespeichert wird** (im Ordner der App und unter `/share/laerm` auf deinem Rechner):
- Messwerte: Pegel alle 125 ms, Hintergrund, Schwelle, ein grobes Frequenzbild (Terzbänder) und Zeitpunkte von Störungen,
- Ergebnisse der lokalen Geräusch-Erkennung (z. B. „Musik“, „Schritte“) und Klang-Fingerabdrücke ohne Ton,
- deine Notizen, Zeugen, Maßnahmen, Regeln und Einstellungen,
- Prüfsummen der Aufzeichnung.

**Was nicht gespeichert wird:** Ton. Ausnahme: Du schaltest „Echten Ton speichern“ selbst ein – das ist standardmäßig aus und mit einem Warnhinweis versehen. Sprache wird **nie** in Text umgewandelt.

**Verbindungen:**
- zu Home Assistant (Regeln, Prüfsummen per MQTT) – innerhalb deines Netzes,
- zu Handys oder Kameras, die du selbst als Gerät einrichtest – innerhalb deines Netzes,
- keine Verbindung ins Internet. Der Pro-Lizenzschlüssel wird offline geprüft.

**Rechtlicher Hinweis:** Das heimliche Aufnehmen des nichtöffentlich gesprochenen Wortes ist in Deutschland strafbar (§ 201 StGB). GLighter ist deshalb so gebaut, dass standardmäßig kein Ton entsteht. Wenn du Ton speicherst oder Geräte in Räumen anderer Personen einsetzt, bist du selbst für die Rechtmäßigkeit verantwortlich. GLighter ersetzt keine Rechtsberatung.

## English

**In short:** GLighter runs entirely on your Home Assistant computer. No cloud, no account, no telemetry. G-Simulation receives no data.

**Stored** (in the app folder and in `/share/laerm` on your computer): levels every 125 ms, background, threshold, a coarse frequency picture (third-octave bands), times of disturbances, local sound recognition results and sound fingerprints without audio, your notes, witnesses, actions, rules and settings, checksums.

**Not stored:** audio – unless you switch on "store real audio" yourself (off by default, with a warning). Speech is **never** converted to text.

**Connections:** Home Assistant (rules, checksums via MQTT) and phones/cameras you add – all within your network. No internet connection; the Pro key is checked offline.

**Legal note:** secretly recording private spoken words is a criminal offence in Germany (§ 201 StGB) and many other countries. If you store audio or use devices in other people's rooms, you are responsible for doing so lawfully. GLighter is not legal advice.
