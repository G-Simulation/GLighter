# GJarvis – Hilfe

Dein eigener deutscher Sprachassistent für Home Assistant – „wie im Film“.
Die Oberfläche findest du in der Seitenleiste unter **GJarvis**.

## Free und Pro

| | Free | Pro |
|---|:---:|:---:|
| „Hey Jarvis“ mit Rückmeldung „Ja, Moses?“ | ✓ | ✓ |
| Befehle an Home Assistant (Geräte, Listen, Satz-Automationen, dein KI-Agent) | ✓ | ✓ |
| Oberfläche, Kalibrierung, Lautstärke, Stimme, „hört“ / „spricht“, Ereignis `gjarvis_command` | ✓ | ✓ |
| Nachfragen ohne Weckwort, Unterbrechen mit „Hey Jarvis“, „Danke“ / „Stopp“ | | ✓ |
| Timer, Erinnerungen, Wecker | | ✓ |
| Gedächtnis | | ✓ |
| Morgen-Briefing, Ansagen aus Automationen | | ✓ |
| Wetter und Flugwetter sofort, Internet- und Wikipedia-Suche, KI-Verteiler, eigenes KI-Modell | | ✓ |
| „Moment, ich melde mich“ – lange Aufgaben im Hintergrund | | ✓ |
| Mealie (Essensplan, Rezepte, Rezept aus dem Internet, Kochen Schritt für Schritt), Listen aller Apps vorlesen | | ✓ |

Pro ist eine Jahreslizenz ohne Abo: [gsimulations.de/gjarvis](https://www.gsimulations.de/gjarvis/#buypro).
Den Schlüssel (`GJ1-…`) trägst du in der Oberfläche unter **GJarvis Pro** ein. Er wird offline geprüft, nichts geht ins Internet.
Ein GasLighter-Schlüssel gilt nicht für GJarvis.

## Schnellstart

1. **Whisper** und **Piper** müssen als Apps laufen (Standard: `core-whisper`, `core-piper`).
2. **Mosquitto (MQTT)** installieren – dann erscheinen die GJarvis-Entitäten automatisch.
3. GJarvis starten, in der Seitenleiste **Kalibrieren** drücken und ca. 20 Sekunden ruhig sein.
4. „**Hey Jarvis**“ sagen → „Ja, Moses?“ → Befehl sprechen.

## Was du sagen kannst

In **Free** geht alles, was dein Home-Assistant-Agent versteht. Die Tabelle zeigt, was **Pro** zusätzlich kann.

| Bereich | Beispiele |
|---|---|
| Haus | „Schalte das Licht im Wohnzimmer ein“, „Setz Milch auf die Einkaufsliste“ |
| Wetter | „Wie wird das Wetter morgen?“, „Regnet es heute?“ |
| Flugwetter | „Wie ist das Flugwetter morgen?“, „Kann man am Startplatz fliegen?“ |
| Internet | „Was läuft heute im Kino?“, „Such im Internet nach …“, „Schau in Wikipedia, wie hoch der Eiffelturm ist“ |
| Wissen & Spaß | „Erzähl mir einen Witz“, „Wie viel ist 17 mal 23?“ |
| Timer | „Stell einen Timer auf 5 Minuten“, „Timer 10 Minuten für die Nudeln“, „Wie lange läuft der Timer noch?“, „Lösche den Timer“ |
| Erinnerungen | „Erinnere mich in 20 Minuten an die Wäsche“, „Erinnere mich morgen um halb acht, dass ich zum Arzt muss“, „Welche Erinnerungen habe ich?“ |
| Wecker | „Weck mich morgen um 7 Uhr“ |
| Gedächtnis | „Merk dir, dass mein Auto in Garage 3 steht“, „Was weißt du über mich?“, „Vergiss das mit dem Auto“, „Vergiss alles“ |
| Briefing | „Guten Morgen“, „Briefing“, „Was steht heute an?“ |
| Beenden | „Danke“, „Das war's“, „Stopp“ |

**Nachfragen ohne Weckwort:** Nach jeder Antwort hört Jarvis noch einige Sekunden zu (Einstellung *Nachfrage-Zeit*).

**Unterbrechen:** Sag „Hey Jarvis“, während er spricht – er verstummt und hört sofort zu.
Oder drück den Knopf *GJarvis Stopp*.

**Gedächtnis:** Passwörter, PINs und Ähnliches merkt er sich nie. Gespeichert wird nur in dieser App (`/data/memory.json`).

## Apps aus Home Assistant (Pro)

GJarvis nutzt, was in Home Assistant eingebunden ist – nichts extra einrichten.

**Mealie** (Integration „Mealie“ in Home Assistant):

- „Was gibt es heute zum Abendessen?“ · „Was steht diese Woche auf dem Speiseplan?“
- „Schlag mir ein Gericht für morgen vor“ – plant ein Zufallsrezept ein
- „Rezept für Lasagne“ / „Wie koche ich Gulasch?“ – sucht in deinen Rezepten, liest Zutaten vor, dann Schritt für Schritt („weiter“, „nochmal“, „zurück“; auch Minuten später mit „Hey Jarvis, weiter“)
- „Such im Internet ein Rezept für Kürbissuppe“ – sucht bei Chefkoch, Lecker, Kitchen Stories …, speichert es in Mealie und liest es vor. Ohne Mealie fasst Jarvis das Rezept kurz zusammen.

**Listen aller Apps** (Mealie, Bring!, Grocy, Todoist, HA-Einkaufsliste – alles, was in Home Assistant eine To-do-Liste ist):

- „Was steht auf der Einkaufsliste?“ · „Was steht auf der Baumarkt-Liste?“
- „Setz Milch auf die Einkaufsliste“ – erledigt Home Assistant selbst

Abschalten: Einstellungen → „Apps aus Home Assistant“.

## So entscheidet Jarvis

1. **Sofort, ohne KI:** Timer, Erinnerungen, Gedächtnis, Briefing, Danke/Stopp.
2. **Wetter und Flugwetter:** direkt aus Home Assistant bzw. Open-Meteo, Windy, Paraglidable.
3. **Home Assistant lokal:** Geräte-Befehle und deine eigenen Satz-Automationen.
4. **KI-Verteiler:** Das schnelle Modell entscheidet: im Internet suchen, Haus steuern oder selbst antworten.
5. Dauert etwas länger als 4 Sekunden, sagt er „Moment, ich melde mich gleich“ und liefert später nach. Solange er noch sucht, meldet er sich alle 8 Sekunden kurz („Ich schaue noch“, höchstens 4-mal – einstellbar unter „Zwischenmeldungen“).
   Du kannst ihn in der Zwischenzeit schon wieder ansprechen.

## Eigene Befehle (Wort → Automation)

**Weg 1 – Satz-Automation (empfohlen):** Neue Automation → Auslöser **„Satz“** → z. B. `Gute Nacht`.

**Weg 2 – Ereignis:** Jeder erkannte Satz kommt als Ereignis `gjarvis_command`:

```yaml
triggers:
  - trigger: event
    event_type: gjarvis_command
    event_data:
      text_lower: gute nacht
```

Fällige Erinnerungen und Timer kommen zusätzlich als Ereignis `gjarvis_reminder`.

## Ansagen aus Automationen

```yaml
action: mqtt.publish
data:
  topic: gjarvis/say
  payload: '{"text": "Die Waschmaschine ist fertig.", "prioritaet": "normal"}'
```

Einfacher Text als Payload geht auch. In der **Ruhezeit** (Standard 22:00–07:00) werden normale Ansagen
nicht gesprochen, `"prioritaet": "hoch"` immer. Vor jeder Ansage kommt ein kurzer Gong (`"gong": false` schaltet ihn ab).

Briefing per Automation, z. B. morgens bei Bewegung in der Küche:

```yaml
action: button.press
target:
  entity_id: button.gjarvis_briefing
```

## Entitäten in Home Assistant (über MQTT)

| Entität | Zweck |
|---|---|
| GJarvis hört | an, solange Jarvis zuhört |
| GJarvis spricht | an, solange Jarvis spricht |
| GJarvis Zustand | idle / listening / processing / responding / calibrating |
| GJarvis Lautstärke | Regler 0–100 % (nur Jarvis' eigene Ausgabe) |
| GJarvis Stimme | Auswahl der deutschen Piper-Stimme |
| GJarvis Stopp | Knopf – Sprachausgabe sofort beenden |
| GJarvis Briefing | Knopf – Tages-Briefing ansagen |
| GJarvis kalibrieren | Knopf – startet die Selbst-Kalibrierung |
| GJarvis Kalibrierung | Ergebnis: Rauschabstand, Whisper-Genauigkeit, Weckwort-Wert, Empfehlungen |
| GJarvis Erinnerungen | Anzahl offener Erinnerungen/Timer, nächste als Attribut |
| GJarvis letzter Befehl | zuletzt erkannter Satz |
| GJarvis letzte Antwort | zuletzt gesprochene Antwort |

**GasLighter** läuft unabhängig weiter und teilt sich das Mikrofon. Es kann „GJarvis hört“ / „GJarvis spricht“
abfragen (MQTT `gjarvis/hoert`, `gjarvis/spricht` = ON/OFF) und in dieser Zeit Ereignisse ignorieren.

## KI verbinden (deine eigene)

GJarvis bringt keine KI mit – du nutzt deine eigene. In der Oberfläche unter **KI-Modell**:

| Verbindung | Wann | Einrichtung |
|---|---|---|
| **KI aus Home Assistant** (Standard) | Du hast in Home Assistant schon eine KI (OpenAI, Google Gemini, Anthropic, Ollama-Integration …) | Agent aus der Liste wählen – fertig |
| **Eigener Ollama-Server** | Am schnellsten, läuft komplett bei dir | Adresse eintragen (z. B. `http://192.168.1.20:11434`) oder **Suchen**, Modell wählen |
| **OpenAI-kompatibel** | LM Studio, LocalAI, vLLM, Open WebUI, OpenRouter, Groq, OpenAI | Adresse + ggf. API-Schlüssel, Modell wählen |

**Testen** prüft die gespeicherte Verbindung, **Vergleichen** misst alle Modelle mit denselben Fragen.
Ohne KI funktionieren Hausbefehle, Uhrzeit, Wetter, Timer, Erinnerungen und Gedächtnis trotzdem.

Tipp für Ollama auf einem Rechner ohne Grafikkarte: Modelle mit 2–3 Mrd. Parametern antworten in etwa 5–10 Sekunden.

## Spracherkennung (Whisper) einrichten

In der Oberfläche unter **Spracherkennung** prüft GJarvis die Whisper-Einstellungen und zeigt Empfehlungen.
**„Whisper für GJarvis einrichten“** setzt Sprache, Beam size 1, deutsche Beispielsätze (mit deinem Namen) und
schaltet Debug aus; steht das Modell auf `auto`/`tiny`, wird `base-int8` gewählt. Danach startet Whisper neu.

Tipps für schnelle, genaue Erkennung:

- Läuft Home Assistant als VM (z. B. Proxmox): Prozessortyp **host** einstellen, sonst fehlt AVX und Whisper ist sehr langsam.
- Mit AVX ist `small-int8` meist schnell genug und versteht deutlich besser als `base-int8`.
- Den **Aufnahmepegel des Mikrofons** im System so einstellen, dass normale Sprache bei etwa −15 dBFS ankommt.
  GJarvis verändert den Pegel absichtlich nicht selbst, weil GasLighter dasselbe Mikrofon zum Messen nutzt.

## Oberfläche und Einstellungen

Die Oberfläche (GJarvis in der Seitenleiste) und der Reiter **Konfiguration** der App sind dieselben Einstellungen:
Was du in der Oberfläche speicherst, steht sofort auch in der Konfiguration – und umgekehrt (nach einem Neustart).
Werte mit dem Hinweis **Neustart** wirken erst, wenn GJarvis neu gestartet wurde; die Oberfläche bietet dafür einen Knopf an.
Schlüssel und Passwörter werden nie angezeigt – leer lassen heißt „unverändert“.

## Satellit und externer Lautsprecher

GJarvis kann statt über das Mikrofon am Server über einen **ESPHome-Satelliten** im Netzwerk hören
(z. B. M5Stack Atom Echo) und über einen **Lautsprecher aus Home Assistant** antworten (z. B. Sonos).
Weckwort, Rückmeldungen, Gedächtnis, Pro-Funktionen – alles bleibt GJarvis.

**Satellit einrichten**

1. Den Satelliten mit der offiziellen Sprach-Firmware flashen (für den Atom Echo:
   `github://esphome/wake-word-voice-assistants/m5stack-atom-echo/m5stack-atom-echo.yaml@main`).
2. In GJarvis: *Audio-Quelle* = `satellite`, *Satellit – Adresse* = IP des Geräts,
   *Satellit – Verschlüsselungsschlüssel* = der Wert hinter `api: encryption: key:` aus seiner ESPHome-Konfiguration.
3. GJarvis neu starten. Im Protokoll steht „Satellit verbunden“, und GJarvis stellt am Gerät
   die Weckwort-Erkennung auf „In Home Assistant“ – das Gerät streamt dann sein Mikrofon dauerhaft an GJarvis.

Hinweis: Die Umstellung auf „In Home Assistant“ bleibt im Gerät gespeichert. Willst du den Satelliten später wieder
direkt in Home Assistant nutzen, stell dort am Gerät *Wake word engine location* zurück auf „On device“.

Ein ESPHome-Gerät schickt sein Mikrofon immer nur an **einen** Empfänger. Ist es zusätzlich in Home Assistant
als Sprach-Satellit eingerichtet, gewinnt der, der zuerst verbunden ist. Deshalb das Gerät in Home Assistant
unter *Einstellungen → Geräte & Dienste → ESPHome* **deaktivieren** (nicht löschen), wenn GJarvis es nutzen soll.

**LED am Satelliten**

| LED | Bedeutung |
|---|---|
| grün, gedimmt | alles in Ordnung, wartet auf „Hey Jarvis“ |
| grün, hell | hört zu |
| gelb, pulsierend | denkt nach |
| gelb | spricht |
| rot blinkend | Fehler – die Anzahl der Blinker ist der Code |

Fehlercodes: **1×** Spracherkennung (Whisper) antwortet nicht · **2×** Home Assistant/KI antwortet nicht ·
**3×** Lautsprecher-Ausgabe fehlgeschlagen · **4×** Sprachausgabe (TTS) fehlgeschlagen · **9×** unerwarteter Fehler.
Der Code wiederholt sich 60 s lang oder bis zum nächsten „Hey Jarvis“. Die genaue Meldung steht im Protokoll
(„Fehlercode …“). LED ganz aus = keine Verbindung zu GJarvis.

**Lautsprecher einrichten**

- *Ausgabe über Lautsprecher* = z. B. `media_player.wohnzimmer_sonos`.
  GJarvis spricht dann mit seiner Piper-Stimme über diesen Lautsprecher (als Durchsage über laufende Musik).
- *Stimme aus Home Assistant* = z. B. `tts.elevenlabs_text_zu_sprache`, wenn statt Piper eine Stimme aus
  Home Assistant (ElevenLabs, Google, Nabu Casa …) sprechen soll.
- Netzwerk-Lautsprecher starten verzögert – dafür gibt es *Lautsprecher-Verzögerung* (Standard 1,5 s).

Hinweise: Über einen externen Lautsprecher kann „Hey Jarvis“ eine laufende Antwort nicht unterbrechen;
der Knopf *GJarvis Stopp* funktioniert weiter. GasLighter misst weiterhin am Mikrofon des Servers.

## Kalibrierung

Knopf „Kalibrieren“: Jarvis misst 3 s das Raumrauschen, spricht Testsätze und „Hey Jarvis“
über seinen Lautsprecher und hört sich selbst zu. Danach sagt er das Ergebnis an und gibt Empfehlungen.

## Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| Reagiert nicht auf „Hey Jarvis“ | In der Oberfläche den Weckwort-Wert beobachten, *Weckwort-Empfindlichkeit* senken (z. B. 0,4). Mikrofonpegel im Betriebssystem prüfen. |
| Reagiert ohne Grund | *Weckwort-Empfindlichkeit* erhöhen (z. B. 0,6). |
| „Ja, Moses?“ kommt, aber er versteht nichts | Kalibrieren. *Sprach-Schwelle* senken, Mikrofon lauter stellen. |
| Schneidet den Satzanfang ab | *Vorlauf* (preroll) erhöhen. |
| Hört zu früh auf | *Pause bis Satzende* erhöhen (z. B. 1,5 s). |
| Unterbricht sich selbst | *Schwelle fürs Unterbrechen* erhöhen oder *Unterbrechen* ausschalten. |
| Antworten dauern lange | In der Oberfläche *Verbindungen → Testen*. Whisper auf der CPU braucht einige Sekunden. |
| Keine Entitäten | Mosquitto-App installieren und GJarvis neu starten. |
| Satellit verbindet nicht | Adresse und Schlüssel prüfen. Im Protokoll steht der Grund. |
| Satellit verbunden, aber Jarvis hört nichts („schickt kein Audio“) | Das Gerät ist in Home Assistant noch als Sprach-Satellit aktiv und hält den Audio-Stream – unter ESPHome **deaktivieren**. GJarvis verbindet dann von selbst neu. |
| Kein Ton am Sonos | *Ausgabe über Lautsprecher* prüfen; in Home Assistant unter Medien testen, ob der Lautsprecher Durchsagen abspielt. |

Kommt länger als `mic_watchdog_seconds` nur Stille oder gar nichts vom Mikrofon, öffnet GJarvis es von selbst neu.
Das Protokoll findest du in der Oberfläche unten unter **Protokoll**.
