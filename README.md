<h1 align="center">GSimulations für Home Assistant</h1>

<p align="center">Drei eigenständige Apps von <a href="https://www.gsimulations.de/">G-Simulation</a> für Home Assistant – jede einzeln installierbar.<br>
<i>Three independent Home Assistant apps by G-Simulation – install each one on its own.</i></p>

<p align="center"><a href="#deutsch">🇩🇪 Deutsch</a> · <a href="#english">🇬🇧 English</a></p>

<table align="center">
<tr>
<td align="center" width="33%"><img src="gaslighter/icon.png" width="96" alt="GLighter"><br><b><a href="#glighter">GLighter</a></b><br>Lärmprotokoll<br><i>Noise log</i></td>
<td align="center" width="33%"><img src="greport/icon.png" width="96" alt="GReport"><br><b><a href="#greport">GReport</a></b><br>Notizen zu Störungen<br><i>Disturbance notes</i></td>
<td align="center" width="33%"><img src="gjarvis/icon.png" width="96" alt="GJarvis"><br><b><a href="#gjarvis">GJarvis</a></b><br>Sprachassistent<br><i>Voice assistant</i></td>
</tr>
</table>

---

<a id="deutsch"></a>

## Installation

Voraussetzung: Home Assistant OS oder Supervised (mit App-Store).

1. Repository hinzufügen – per Klick:<br>
   [![Repository zu Home Assistant hinzufügen](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FG-Simulation%2FGSimulations-HomeAssistant)<br>
   oder von Hand: **Einstellungen → Apps → App-Store → ⋮ → Repositories** → `https://github.com/G-Simulation/GSimulations-HomeAssistant`
2. Im App-Store erscheinen unter **GSimulations** alle drei Apps. Die gewünschte App öffnen → **Installieren** → **Starten**.
3. Die App in der Seitenleiste öffnen.

Jede App läuft für sich. Du kannst eine, zwei oder alle drei installieren. Updates erscheinen automatisch in Home Assistant.

---

<a id="glighter"></a>

## <img src="gaslighter/icon.png" width="32" alt=""> GLighter – Lärmprotokoll

Misst Lärm rund um die Uhr und protokolliert Störungen manipulationssicher – **ohne Tonaufnahme, ohne Cloud**.

<p align="center">
<img src="docs/images/01_live.png" width="24%" alt="Live">
<img src="docs/images/02_protokolle.png" width="24%" alt="Protokolle">
<img src="docs/images/03_ereignisse_notizen.png" width="24%" alt="Störungen und Notizen">
<img src="docs/images/08_laermprotokoll_druck.png" width="24%" alt="Lärmprotokoll">
</p>

- **Misst rund um die Uhr** mit einem USB-Mikrofon am Home-Assistant-Rechner und erkennt Störungen automatisch – mit Uhrzeit, Dauer und Spitzenpegel.
- **Speichert keinen Ton**, nur Messwerte. Sprache wird nie in Text umgewandelt.
- **Protokolle** für Tag, Woche, Monat oder frei gewählten Zeitraum, mit Tagesverlauf, Ruhezeiten und Statistik.
- **Lärmprotokoll zum Drucken oder als PDF** – für Vermieter, Hausverwaltung oder Anwalt.
- **Prüfkette:** Jede Minute bekommt eine SHA-256-Prüfsumme, nachträgliche Änderungen fallen auf.
- **Lokale Geräusch-Erkennung (KI)**, eigene Tonprofile, Regeln mit Home Assistant.

| | Kostenlos | GLighter Pro |
|---|:---:|:---:|
| Aufzeichnung, Live, Protokolle, Notizen | ✔ | ✔ |
| Lärmprotokoll, Druck, Export, Sicherung erstellen | ✔ | ✔ |
| Import einer Sicherung | einmal (Umzug) | ✔ |
| Erweiterte Einstellungen, eigene Statistiken | ansehen / Vorlagen | ✔ |
| Tägliche Sicherung auf NAS/USB | ZIP von Hand | ✔ |
| Externe Geräte (Handy, Stream, IP-Kamera) | – | ✔ |

**GLighter Pro:** Jahreslizenz für 1 Home-Assistant-Installation, **kein Abo** – [gsimulations.de/gaslighter](https://www.gsimulations.de/gaslighter/#buypro)

[Handbuch](docs/de/README.md) · [Schnellstart](docs/de/01-schnellstart.md) · [Fehlerbehebung](docs/de/13-fehlerbehebung.md) · [Rechtliches](docs/de/12-rechtliches.md) · [Änderungen](gaslighter/CHANGELOG.md)

---

<a id="greport"></a>

## <img src="greport/icon.png" width="32" alt=""> GReport – Notizen zu Störungen

Hält Störungen als Notiz fest – schnell, mit Uhrzeit, Zeuge und Zeitraum. **Eigenständige App**, braucht kein GLighter.

- **Notiz jetzt:** einfach lostippen oder eine Taste der Schnellwahl antippen, Zeuge und Zeitraum dazu, Enter speichert.
- **Schnellwahl anpassen:** eigene Tasten anlegen, eingebaute ausblenden, Gruppen mit Farben und Pflicht-Gruppen.
- **Eigene Dashboard-Karte „GReport“:** wird automatisch eingerichtet und steht unter „Karte hinzufügen“ – Notiz, Woher, Was, Wie stark, Folgen, Maßnahmen, Zeuge und Speichern in einer Karte. Funktioniert für alle Benutzer, auch ohne Administratorrechte.
- **Bereich „GReport“:** Alle GReport-Felder stehen in Home Assistant gesammelt unter einem eigenen Bereich.
- **Home Assistant:** jede Notiz im Logbuch, Sensoren „Letzte Notiz“ und „Notizen heute“ (MQTT/Mosquitto).
- Ist zusätzlich GLighter installiert, erscheinen die Notizen mit GLighter Pro automatisch auch dort.

**Pro** (ein GLighter-Pro-Schlüssel gilt auch): Tagebuch als Textdatei, Export/Import, mehr eigene Tasten, tägliche Sicherung, mehrere Zeugen – [gsimulations.de/greport](https://www.gsimulations.de/greport/)

[Mehr zu GReport](greport/README.md) · [Änderungen](greport/CHANGELOG.md)

---

<a id="gjarvis"></a>

## <img src="gjarvis/icon.png" width="32" alt=""> GJarvis – Sprachassistent

Deutscher Sprachassistent für Home Assistant – „wie im Film“: **„Hey Jarvis“ → „Ja?“ → Befehl.** Eigenständige App.

- **Kostenlos:** alles, was dein Home-Assistant-Agent kann (Licht, Geräte, Listen, Satz-Automationen, deine KI), Oberfläche in der Seitenleiste, Kalibrierung, Lautstärke, Stimme.
- **GJarvis Pro** (Jahreslizenz, kein Abo):
  - Nachfragen ohne Weckwort und Unterbrechen mit „Hey Jarvis“
  - Timer, Erinnerungen, Wecker und Gedächtnis
  - Morgen-Briefing mit Wetter, Kalender und Nachrichten
  - Ansagen aus Automationen mit Gong und Ruhezeit
  - Internet-Recherche und eigenes KI-Modell (Ollama oder OpenAI-kompatibel)

Voraussetzungen: die Apps **Whisper**, **Piper** und **Mosquitto**. – [gsimulations.de/gjarvis](https://www.gsimulations.de/gjarvis/#buypro)

[Mehr zu GJarvis](gjarvis/README.md) · [Änderungen](gjarvis/CHANGELOG.md)

---

## Datenschutz und Hilfe

Alle Daten bleiben auf deinem Home-Assistant-Rechner; keine der Apps sendet etwas an G-Simulation oder Dritte. Details: [PRIVACY.md](PRIVACY.md).

Fehler melden oder Idee vorschlagen: [Issues](https://github.com/G-Simulation/GSimulations-HomeAssistant/issues/new/choose) · Kontakt: [gsimulations.de](https://www.gsimulations.de/)

---

<a id="english"></a>

## English

Three independent Home Assistant apps by G-Simulation. Add the repository once and install any of them:

[![Add repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FG-Simulation%2FGSimulations-HomeAssistant)<br>
or manually: **Settings → Apps → App store → ⋮ → Repositories** → `https://github.com/G-Simulation/GSimulations-HomeAssistant`

| App | What it does |
|---|---|
| <img src="gaslighter/icon.png" width="24" alt=""> **GLighter** | Noise log – measures noise 24/7 and logs disturbances tamper-evident. No audio recording, no cloud. Printable noise report. [Manual](docs/en/README.md) |
| <img src="greport/icon.png" width="24" alt=""> **GReport** | Disturbance notes – note, quick select, witness, time span. Own dashboard card "GReport" for all users. Works on its own. |
| <img src="gjarvis/icon.png" width="24" alt=""> **GJarvis** | German voice assistant "Hey Jarvis". Pro: timers, reminders, memory, briefing, weather, web search. Needs Whisper, Piper and Mosquitto. |

All data stays on your Home Assistant computer. [Privacy](PRIVACY.md) · [Issues](https://github.com/G-Simulation/GSimulations-HomeAssistant/issues/new/choose) · [gsimulations.de](https://www.gsimulations.de/)

---

© G-Simulation (Patrick Gottberg). Alle Rechte vorbehalten / All rights reserved – siehe [LICENSE](LICENSE). Fremde Bestandteile / third-party components: [NOTICE.md](NOTICE.md).
