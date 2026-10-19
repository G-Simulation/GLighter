# GReport

Notizen zu Störungen festhalten – eigenständige App für Home Assistant von G-Simulation. Läuft allein, arbeitet auf Wunsch mit [GLighter](https://github.com/G-Simulation/GSimulations-HomeAssistant#glighter) zusammen.

- **Notiz jetzt:** einfach lostippen oder eine Taste der Schnellwahl antippen, Zeuge und Zeitraum dazu, Enter speichert.
- **Schnellwahl anpassen:** eigene Tasten anlegen, eingebaute ausblenden; GReport schlägt oft getippte Wörter als neue Taste vor.
- **Home Assistant:** jede Notiz im Logbuch; Auswahlliste „Schnellwahl“ und Knopf „Hinzufügen“ fürs Dashboard (MQTT/Mosquitto).
- **Mit GLighter:** Ist GLighter installiert, erscheinen die Notizen mit GLighter Pro automatisch dort – ohne Kopplung.
- Läuft auch allein, die Notizen bleiben in `/share/greport`.

Pro (ein GLighter-Pro-Schlüssel gilt auch): Tagebuch als Textdatei, Export/Import (Text, CSV, JSON), bis zu 40 eigene Tasten, tägliche Sicherung, mehrere Zeugen.
Die Sicherung als ZIP ist immer frei. Es wird kein Ton aufgenommen.
