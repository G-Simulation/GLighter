# Home Assistant

GLighter arbeitet mit Home Assistant zusammen: Regeln fragen Zustände ab (Fernseher an, Waschmaschine läuft, Sensor ausgelöst), und über MQTT meldet die App Störungen, Prüfsummen und Schalter zurück.

<a id="regeln"></a>

## Regeln

![Regel „Schwelle anheben“ als Karte](../../gaslighter/app/web/hb/regeln_de.png)

⚙ Einstellungen → Reiter **Regeln** → **＋ Regel hinzufügen**. Zuerst wählst du, was die Regel tun soll, danach das Gerät aus der Liste (mit Suche). Zustände, Nachlauf und Höchstdauer werden passend vorbelegt. Keine Automation, kein YAML.

| Art | Was passiert | Beispiel |
|---|---|---|
| 📈 **Schwelle anheben** (Pro) | Erkennung läuft weiter, nur unempfindlicher | eigener Fernseher, Sonos |
| 🔕 **keine Störung melden** | Graph läuft weiter, keine Störung | Sprachassistent, eigene Tür |
| ⏸ **pausieren** | in dieser Zeit nicht auswerten | Staubsauger |
| 📝 **nur festhalten** | weiter aufnehmen und mitschreiben, wann es an war | Fernseher |
| 🚩 **als Ereignis** | wie festhalten, dazu Fähnchen und eigene Zeile | Tür-, Vibrationssensor |

Jede Regel ist eine **Karte**. Zugeklappt zeigt sie Name, Art, Gerät, den Zustand jetzt und einen Schalter (an/aus). Ein Klick klappt sie auf:

| Feld | Bedeutung |
|---|---|
| **Name** | Unter diesem Namen wird die Regel festgehalten, z. B. „Erschütterung Wand“. Leer = Name aus Home Assistant. |
| Aktion | die Art (oben), jederzeit änderbar |
| Gerät (Home Assistant) | z. B. `media_player.fernseher`, `binary_sensor.vibration_wand` |
| Für welches Gerät | für welches Mikrofon die Regel gilt (oder alle) |
| aktiv bei | Zustände zum Anhaken (z. B. *an*, *spielt*). Unter **Bedingung als Text** geht auch `!off` = alles außer off, `>1` = Zahl größer 1 |
| Nachlauf, höchstens | bei Schwelle anheben, keine Störung melden und pausieren: so lange danach weiter, Höchstdauer |

Unten in der Karte: **▶ Testen** (fragt Home Assistant jetzt und sagt, ob die Regel greift), **⧉ Kopieren**, **✕ Löschen**. Oben im Reiter steht, ob Home Assistant verbunden ist und welche Regeln gerade aktiv sind.

<a id="anheben"></a>

### Schwelle anheben (Fernseher, Sonos)

Läuft dein eigener Fernseher, soll er keine Störung auslösen – Lärm von außen, der deutlich lauter ist, aber schon. Die Regel hebt dafür die Schwelle an, solange das Gerät an ist (plus Nachlauf). Die Erkennung läuft weiter.

- **Anhebung:** z. B. +10 dB (0–40). Im Graph siehst du die angehobene Schwelle.
- **Mit der Lautstärke mitgehen:** Meldet das Gerät seine Lautstärke, folgt die Anhebung ihr. Beispiel: eingepegelt bei 35 % mit +9 dB → bei 18 % etwa +4,5 dB, stumm keine Anhebung (höchstens das Doppelte).
- **🎚 Einpegeln – gedrückt halten:** Fernseher oder Sonos so laut laufen lassen wie sonst, sonst möglichst still. Taste mindestens 3 Sekunden gedrückt halten. Solange gemessen wird, nimmt GLighter den Pegel; beim Loslassen übernimmt es die aktuelle Lautstärke. Anhebung = Pegel des Geräts (95 %) + 3 dB Abstand über der normalen Schwelle. Das Ergebnis steht in der Karte und im Protokoll.
- **Nachweis:** In der Ereignistabelle steht bei jeder Störung in dieser Zeit „📈 Fernseher +9 dB“, in der Störung „Schwelle +9 dB“. Die Zeiträume stehen in `ha_anhebung.csv`. Die Tagesaufzeichnung läuft unverändert weiter.
- Ohne Pro wird die Regel gespeichert, wirkt aber nicht.

„jetzt: …“ zeigt live, was Home Assistant meldet – so siehst du, welchen Zustand ein Gerät wirklich hat. Im Zweifel wird aufgenommen.

**Festhalten** schreibt jeden Wechsel in `ha_zustand.csv`. An jeder Störung steht dann z. B. „Fernseher: an · 🔊 18 %“, im Verlauf erscheint oben ein **schmaler blauer Streifen** (je Sensor eine eigene Spur), und das Lärmprotokoll nennt den Zustand. Nur **pausieren** färbt die ganze Höhe (dort wurde nicht ausgewertet).

**Als Ereignis** zeichnet je Sensor ein farbiges Fähnchen und eine rote Linie über die ganze Höhe. Die Farbe wählst du in der Regel unter **Farbe** (↺ = automatisch). Jedes „an“ steht unter **📡 Sensor-Ereignisse** in der Ereignistabelle – mit Uhrzeit, Dauer und Notiz (✎). Sensor-Ereignisse zählen **nicht** als Störung und werden getrennt gezählt. Die Umstellung gilt auch rückwirkend, weil die Zustände schon in `ha_zustand.csv` stehen.

**Notiz zum Zeitraum:** Klick auf den Streifen (oder ✎ in der Liste) öffnet ein Fenster für eine Notiz, z. B. „eigener Film geschaut“. Sie steht im Streifen, in der Liste und im Lärmprotokoll.

**Filter „📡 Sensoren“** (Protokolle, oben): Mehrfachauswahl, welche Sensoren, Handy-Erschütterung/-Bewegung und ob Störungen gezeigt werden. Gilt für Verlauf, Listen und Tabelle. Meldet der Fernseher seine Lautstärke, wird sie mitgeschrieben.

> Bereits Festgehaltenes behält seinen Namen, auch wenn du ihn später änderst.

<a id="zigbee"></a>

## Zigbee-Sensoren (Vibration, Bewegung, Tür)

Sensoren, die in Home Assistant eingebunden sind (z. B. über Zigbee2MQTT oder ZHA), funktionieren genauso:

1. Regel hinzufügen, Entität des Sensors wählen (z. B. `binary_sensor.vibration_decke_occupancy`).
2. Name eingeben, z. B. „Erschütterung Decke“.
3. Aktion **als Ereignis** (oder **nur festhalten**), „an bei“ `on`.

Ab dann steht bei jeder Störung, ob gleichzeitig eine Erschütterung gemeldet wurde – ein starker Hinweis auf Trittschall oder Klopfen über das Gebäude.

<a id="mqtt"></a>

## MQTT: Steuern und Melden

Ist MQTT eingerichtet, erscheint in Home Assistant das Gerät **GLighter** mit:

- Schalter **Aufzeichnung**, **Manuell erfassen (außerhalb der Zeit)**, Zahl **Pause (Minuten)**, Tasten **Pause 15 min**, **Pause 1 h**, **Fortsetzen**, Sensor **Pause bis**.
- Je Gerät: Ereignis **Störung (Auslöser)** (beginn, ende, erkannt – mit Spitze, Dauer, Art, Profil), Geräte-Auslöser für Automationen, Sensor „Letzte Geräuschart“ und stündlich die aktuelle **Prüfsumme** (in Home Assistant unabhängig gespeichert).

Beispiel – 10 Minuten Pause, wenn die Katzentoilette reinigt:

```yaml
automation:
  - alias: "GLighter pausieren, wenn das Katzenklo reinigt"
    trigger:
      - platform: state
        entity_id: sensor.katzenklo_status
        to: "cleaning"
    action:
      - service: mqtt.publish
        data:
          topic: gaslighter/pause/set
          payload: '{"minutes": 10, "reason": "Katzenklo"}'
```

Eine von Hand gestoppte Aufzeichnung wird durch eine Pause aus Home Assistant nicht automatisch wieder gestartet.

## Störung direkt im Dashboard erfassen

Mit MQTT meldet das Add-on zwei Elemente am Gerät „GLighter“:

- **Störung / Notiz erfassen**: Textfeld. Text eingeben, Enter drücken, schon ist die Notiz mit der aktuellen Uhrzeit gespeichert. Das Feld leert sich danach.
- **Störung jetzt markieren**: Knopf. Ein Tipp legt sofort eine Notiz „Störung (Home Assistant)“ an, ohne Text.

Beide legst du auf ein beliebiges Dashboard (z. B. als Karte „Entitäten“). Liegt kurz davor eine Störung, wird die Notiz ihr zugeordnet, genau wie bei der Notizleiste im Live-Bild.

## Keine Störung melden (Graph läuft weiter)

Manchmal soll eine Störung nicht gemeldet werden, der Graph aber trotzdem weiterlaufen, zum Beispiel wenn du selbst die Tür öffnest.

- **In einer Regel:** Wähle bei der Aktion **„keine Störung melden“**. Solange die Bedingung gilt und für den **Nachlauf** (z. B. 10 Minuten), entsteht keine Störung. Der Graph wird weiter aufgezeichnet, es gibt keine Lücke.
- **Vorlauf (s), z. B. für einen Sprachassistenten:** Das Rufwort („Hey Jarvis“) kommt, *bevor* der Assistent auf „hört zu“ wechselt. Mit **Vorlauf** zählt auch eine Störung nicht, die bis zu so viele Sekunden vor dem Einschalten der Regel begann. Dafür hält GLighter jede Störung so lange (Vorlauf + 2 s) zurück, bevor sie gemeldet wird. Pegel und Graph bleiben unverändert; im Protokoll steht „nicht gezählt“. **Einrichten:** Regel hinzufügen, Entität `assist_satellite.…` wählen – Zustände `!idle`, „keine Störung melden“, Vorlauf 3 s und Nachlauf 0,5 min werden vorbelegt. So zählen Rufwort, Befehl und die Antwort aus dem Lautsprecher nicht.
- **Als Knopf im Dashboard:** Am Gerät „GLighter“ gibt es **„Keine Störung melden (Dauer starten)“**, **„Störungen wieder melden“**, die einstellbare **Dauer** (1–240 Minuten, Standard 10) und **„Keine Störungsmeldung bis“**. Lege sie auf dein Dashboard. Ein Tipp auf den Knopf startet die eingestellte Dauer.

<a id="dashboard"></a>

## Dashboard in Home Assistant anlegen

⚙ Einstellungen → Reiter **Regeln** → **Dashboard in Home Assistant**. GLighter legt dort mit einem Klick ein fertiges Dashboard mit seinen Entitäten an. Du wählst:

- **Name** und **Adresse** (z. B. `gsim-glighter`, steht danach in der Adresszeile von Home Assistant),
- ob es in der **Seitenleiste** steht und ob es **nur für Administratoren** sichtbar ist,
- welche **Bereiche** hinein sollen: Jetzt (Störung, Pegel, heute), Pegel der letzten 24 Stunden, Störung erfassen, Keine Störung melden, Aufzeichnung und Pause, weitere Mikrofone, Knopf „GLighter öffnen“.

**In Home Assistant anlegen** erstellt das Dashboard. Gibt es unter der Adresse schon eins, fragt GLighter nach, bevor es ersetzt wird (Änderungen, die du dort gemacht hast, gehen dabei verloren). Ohne Klick ändert GLighter in Home Assistant nichts.

Unter **Als YAML anzeigen** steht dieselbe Vorlage zum Kopieren: in Home Assistant ein Dashboard anlegen, **Bearbeiten** → ⋮ → **Rohdaten-Konfigurationseditor**, einfügen, speichern. Das Dashboard kannst du danach in Home Assistant frei weiter bearbeiten.

---
[← Geräte](06-geraete.md) · [Inhalt](README.md) · [Drucken und Lärmprotokoll →](08-drucken.md)
