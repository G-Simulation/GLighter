# Änderungen

## 1.10.0

- Sicherer: Die Oberfläche und ihre Schnittstelle sind nur noch über Home Assistant (Seitenleiste) erreichbar, nicht mehr direkt von anderen Apps im Netz
- Sicherer: Der API-Schlüssel der eigenen KI wird nur noch an die eingetragene Adresse geschickt
- GJarvis braucht weniger Rechte (kein Zugriff mehr auf `/share`, Home-Assistant-Rolle „default“). „Whisper einrichten“ zeigt deshalb die Werte zum Eintragen an, statt Whisper selbst umzustellen
- Freischaltung mit dem Schlüssel aus dem Shop unverändert

## 1.9.0

- Pro mit dem Schlüssel aus dem Shop freischalten (z. B. GJ-XXXXX-XXXXX-XXXXX-XXXXX): GJarvis prüft ihn einmal online bei gsimulations.de und arbeitet danach wieder ganz ohne Internet
- Sofort-Rückmeldung: Fragst du nach Wetter, Internet, Nachrichten oder etwas, wofür die KI nachdenken muss, sagt Jarvis direkt nach dem Verstehen „Moment, ich schaue nach“ (beim Wetter „Moment, ich schaue nach dem Wetter“) – und sucht währenddessen schon. So weißt du sofort, dass er dich verstanden hat
- Das gilt jetzt auch, wenn du zuerst nur „Hey Jarvis“ sagst und nach „Ja?“ deine Frage stellst
- Licht, Timer, Uhrzeit und andere schnelle Befehle bekommen kein „Moment“ mehr; dauert etwas unerwartet länger als 0,9 s, meldet sich Jarvis trotzdem
- Neue Einstellungen: „Wann sofort zurückmelden“ (slow/always/off), Wartezeit, eigene Wetter-Sätze und eigene Wörter für sofortige Rückmeldung
- Rückmeldung und Antwort überschneiden sich nie mehr (vorher konnten bei Recherchen zwei Stimmen gleichzeitig sprechen)
- Bei zufälliger Reihenfolge kommt nie zweimal hintereinander derselbe Satz
- Jede Antwort etwas schneller: das Ereignis für eigene Automationen wird im Hintergrund gesendet und hält die Antwort nicht mehr auf

## 1.8.1

- Neues GJarvis-Logo und App-Symbol im GSimulations-Stil (wie GLighter und GReport) – im App-Store, in der Oberfläche und als Browser-Symbol

## 1.8.0

- Neue Oberfläche mit Reitern: Übersicht, Einstellungen, KI & Spracherkennung, Pro, Hilfe, Protokoll
- Alle Einstellungen jetzt auch in der Oberfläche – nach Themen sortiert, mit Suche, „geändert“-Markierung und Neustart-Hinweis
- Ein einziger Speicher: Oberfläche, Reiter „Konfiguration“ und die Regler in Home Assistant (Lautstärke, Stimme) schreiben alle in die App-Konfiguration – beide Ansichten zeigen immer dasselbe
- Bisherige Oberflächen-Einstellungen (ui_settings.json, settings.json) werden beim ersten Start einmalig übernommen
- Übersicht zeigt, worüber Jarvis hört und spricht, und die aktuelle LED-Farbe des Satelliten
- Protokoll mit Filter und Kopieren-Knopf
- Schlüssel und Passwörter werden in der Oberfläche nie angezeigt
- Satellit: Warnung im Protokoll, wenn der Satellit verbunden ist, aber kein Audio schickt (meist hält Home Assistant den Sprach-Stream); GJarvis verbindet dann neu
- Satellit: Fehler-Blinken bleibt bis zum nächsten „Hey Jarvis“ stehen; derselbe Fehler startet das Blinken nicht neu
- Lautsprecher: „Stopp“ beendet auch mehrsätzige Antworten und hält keine Musik mehr an, wenn Jarvis gar nicht spricht; fällt der Lautsprecher aus, bricht die Antwort sofort ab statt Satz für Satz zu warten
- Ungültige Werte (z. B. eine nicht mehr vorhandene Stimme) blockieren das Speichern nicht mehr
- Flugwetter-Koordinaten sind jetzt Zahlenfelder; Schieberegler haben ein Zahlenfeld für genaue Werte
- GitHub-Workflow: Versionsnummern und Namen werden korrekt übernommen; hochladen.bat funktioniert unter Windows

## 1.7.1

- Umgestellt auf das neue Home-Assistant-Format „Apps“ (früher Add-ons): Bezeichnungen, Dockerfile mit Multi-Arch-Basis-Image (`base-debian:bookworm`), Labels im Dockerfile, `build.yaml` entfällt
- Neuer GitHub-Workflow mit den aktuellen Builder-Aktionen (ein Image für amd64 und aarch64)

## 1.7.0

- Neu: Satelliten – GJarvis hört über ein ESPHome-Gerät im Netzwerk (z. B. M5Stack Atom Echo) statt über das Server-Mikrofon; Weckwort und alle Funktionen bleiben bei GJarvis
- Neu: Antworten über einen Lautsprecher aus Home Assistant (z. B. Sonos) – mit Piper-Stimme oder einer TTS-Stimme aus Home Assistant (z. B. ElevenLabs)
- LED am Satelliten: grün = bereit, hellgrün = hört zu, gelb pulsierend = denkt nach, gelb = spricht, rot blinkend = Fehler mit Code (1 Whisper, 2 Home Assistant/KI, 3 Lautsprecher, 4 Sprachausgabe, 9 sonstiger Fehler)
- Einstellungen: Audio-Quelle, Satellit (Adresse, Port, Schlüssel, LED), Ausgabe-Lautsprecher, Stimme aus Home Assistant, Lautsprecher-Verzögerung

## 1.6.0

- Neu (Pro): Mealie per Sprache – „Was gibt es heute zum Abendessen?“, „Was steht diese Woche auf dem Speiseplan?“, „Schlag mir ein Gericht vor“ (plant ein Zufallsrezept ein)
- Neu (Pro): „Such im Internet ein Rezept für Kürbissuppe“ – Jarvis sucht (Chefkoch, Lecker, Kitchen Stories …), speichert es in Mealie und liest Zutaten vor; ohne Mealie fasst er das Rezept zusammen
- Neu (Pro): Kochen Schritt für Schritt – „Rezept für Lasagne“ → Zutaten → „weiter“, „nochmal“, „zurück“
- Neu (Pro): Listen vorlesen – „Was steht auf der Einkaufsliste?“ für jede To-do-Liste in Home Assistant (Mealie, Bring!, Grocy, Todoist, HA-Einkaufsliste); Hinzufügen erledigt wie bisher Home Assistant selbst
- Neu: Zwischenmeldungen – dauert eine Antwort länger (KI, Internet-Suche), sagt Jarvis regelmäßig „Ich schaue noch“, „Einen Moment noch“ … bis das Ergebnis da ist
- Abstand (Standard 8 s), Höchstzahl (Standard 4) und Sätze in der Oberfläche einstellbar; spricht nie in ein laufendes Gespräch hinein

## 1.5.1

- GJarvis-Icon in der Oberfläche (Kopfzeile) und als Browser-Tab-Symbol

## 1.5.0

- KI frei wählbar, nichts wird mitgeliefert: KI aus Home Assistant (Standard – OpenAI, Google, Anthropic, Ollama … was dort eingerichtet ist), eigener Ollama-Server oder jeder OpenAI-kompatible Dienst
- Karte „KI-Modell“: Verbindung wählen, KI-Server automatisch suchen, Modell aus Liste wählen, testen, vergleichen
- Ohne Modellangabe nimmt Jarvis das kleinste installierte Modell
- Sekunden bis „Moment, ich melde mich gleich“ und der Satz selbst direkt in der Oberfläche einstellbar
- Ohne KI funktioniert alles Übrige weiter; Internet-Antworten werden dann direkt vorgelesen

## 1.4.0

- Neu: Karte „KI-Modell“ – installierte Modelle auswählen und mit einem Klick vergleichen (Ladezeit, Antwortzeit, Antworten nebeneinander)
- Verirrte chinesische Schriftzeichen in KI-Antworten werden entfernt
- Beim Modellwechsel wird das alte Modell aus dem Speicher genommen und das neue sofort geladen

## 1.3.1

- KI-Modell mit kleinerem Arbeitsspeicher (4096 statt 16384 Token) – lädt schneller, braucht weniger RAM
- Neuere Modelle (Qwen 3/3.5, Gemma 4 …): Denk-Modus wird abgeschaltet, damit sie sofort antworten
- Uhrzeit und Datum sofort, ohne Home Assistant oder KI – auch wenn Whisper „Wie spät ist das?“ versteht

## 1.3.0

- Neu: Karte „Spracherkennung“ – prüft Whisper und richtet es mit einem Klick für GJarvis ein (Sprache, Beam 1, deutsche Beispielsätze, Debug aus)
- Warnung, wenn das Mikrofon zu leise ist

## 1.2.4

- „Hey Jarvis, wie spät ist es“ ohne Pause: die ersten Wörter gehen nicht mehr verloren (die Sekunde vor dem Weckwort geht mit an Whisper, „Hey Jarvis“ wird danach entfernt)
- Kein doppeltes „Moment …“ mehr
- KI schneller auf CPU: gleichbleibender System-Text, den das Modell zwischenspeichern kann

## 1.2.3

- „Hey Jarvis, wie spät ist es“ in einem Atemzug: kein „Ja, Moses?“ mehr dazwischen, der Befehl geht nicht mehr verloren. Jarvis sagt sofort „Moment, ich schaue.“ und erledigt es gleichzeitig

## 1.2.2

- Schneller: Verteiler und Antwort in einem einzigen KI-Aufruf statt zwei
- KI-Modell wird beim Start vorgeladen und im Speicher gehalten (keine 20 s Ladezeit bei der ersten Frage)
- Mehr Ausreden der KI erkannt („kann keine …“) – dann wird im Internet gesucht

## 1.2.1

- Wetter für „nächste Woche“, „diese Woche“, „Wochenende“ und „die nächsten Tage“ – reicht die Vorhersage nicht so weit, schaut Jarvis im Internet nach („Moment …“)
- Jede andere Wetterfrage („Brauche ich morgen einen Schirm?“) beantwortet die KI aus den echten Vorhersagedaten
- „um 12 Grad“ statt „zwischen 12 und 12 Grad“
- Halbe Werkzeug-Antworten des KI-Agenten (<tool>…) werden nicht mehr vorgelesen

## 1.2.0

- Nachfragen ohne Weckwort, „Danke“ / „Stopp“ beenden
- Unterbrechen mit „Hey Jarvis“, Knopf „GJarvis Stopp“
- Gedächtnis („Merk dir …“, „Was weißt du über mich?“, „Vergiss …“)
- Timer, Erinnerungen und Wecker ohne KI, bleiben nach Neustart erhalten
- Morgen-Briefing mit Wetter, Kalender, Erinnerungen und Tagesschau
- Ansagen aus Automationen (`gjarvis/say`) mit Gong und Ruhezeit
- Persönlichkeit einstellbar
- Lange Antworten werden Satz für Satz gesprochen
- Free und Pro: Free = „Hey Jarvis“ + Home Assistant, Pro = alles andere (Lizenzschlüssel GJ1-…, offline geprüft)
- Icon, Logo, Hilfe

## 1.1.0

- Oberfläche in der Seitenleiste, KI-Verteiler, Internet-Suche, Flugwetter

## 1.0.0

- Erste Version
