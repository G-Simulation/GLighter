# Geräte

Unter ⚙ Einstellungen → **Geräte** → Quellen stehen alle Mikrofone. Bis zu 9 Geräte sind möglich.

![Einstellungen: Geräte](geraete_{lang}.png)

## Server-Mikrofon {#server}

Das Mikrofon am Home-Assistant-Rechner. Unter **Mikrofon** wählst du Eingang, Buchse und Lautstärke. Meist „Standard“ lassen. **Brummfilter** (50 Hz in Europa) entfernt Netzbrummen.

## Handy als Mikrofon {#handy}

> **🔒 Pro:** Handys, Stream-URLs und IP-Kameras sind externe Geräte und gehören zu [GasLighter Pro](#pro). Das Server-Mikrofon ist immer frei.

![GasLighter am Handy](handy_{lang}.png)

- **Handy (Browser)**: „+ Handy (Browser)“, QR-Code scannen, Seite in Chrome öffnen, Zertifikatswarnung bestätigen, **Start**. Der Bildschirm muss an bleiben (Ladegerät). Der Link ist geheim und gehört nur zu diesem Handy.
- **Stream (z. B. App „IP Webcam“)**: „+ Handy-App / Stream-URL“, Adresse `http://HANDY-IP:8080/audio.wav`. Läuft auch mit ausgeschaltetem Bildschirm. Mit Login: Benutzername und Passwort in die eigenen Felder.
- Der Handy-Port ist standardmäßig **18443** (Add-on → Netzwerk, „8443/tcp“).

### Video {#video}

Bei Streams lässt sich **🎥 Video aufnehmen** einschalten: Bei einer Störung entsteht eine mp4-Datei **ohne Ton**. Ohne Störung wird nichts gespeichert. Qualität unter Speichern & Sicherung → Video, Ordner unter Speicherort.

> Kameraaufnahmen in Wohnungen können nach § 201a StGB problematisch sein – nur eigene Räume, keine fremden Personen filmen.

## Handy als Bewegungsmelder {#bewegung}

Ein als Gerät eingerichtetes Handy kann zusätzlich zum Mikrofon als **Bewegungsmelder** dienen – wie ein Bewegungs- oder Vibrationssensor in Home Assistant:

- **🫨 Erschütterung** (Beschleunigungssensor): Das Handy liegt flach auf dem Boden, einem Tisch oder an der Wand und meldet Vibrationen – z. B. Trampeln, Bass, der durch die Decke kommt, Türenknallen oder Möbelrücken. Das belegt Körperschall, den man nicht nur hört, sondern spürt.
- **🏃 Bewegung im Kamerabild**: Die Kamera des Handys erkennt Bewegung im Bild (z. B. im Treppenhaus). Plötzliche Helligkeitsänderungen (Licht an/aus) werden herausgerechnet.

**Einschalten:** ⚙ Einstellungen → Geräte → Karte des Handys → **Handy als Bewegungsmelder** → „Erschütterung“ und/oder „Bewegung im Kamerabild“ anhaken, **Empfindlichkeit** wählen (hoch, mittel, niedrig). Danach am Handy die Seite neu laden und **Start** tippen. Der Browser fragt nach der Kamera bzw. (iPhone) nach „Bewegung und Ausrichtung“.

> **Datenschutz:** Ausgewertet wird nur auf dem Handy. Gesendet werden nur Zahlen (Stärke der Erschütterung, Anteil der veränderten Bildpunkte) – **kein Bild und kein Video**. Das Vorschaubild sieht man nur auf dem Handy selbst.

**Was dabei entsteht:**
- Am Handy und in der Geräteleiste blinkt 🫨 bzw. 🏃, solange ausgelöst ist.
- Jede Erschütterung bzw. Bewegung wird mit Beginn, Ende und Spitze gespeichert (`bewegung.csv` im Datenordner). Sie gilt bis 20 s nach dem letzten Auslösen als „an“.
- Im Reiter **Protokolle** steht die Liste „Erschütterung und Bewegung im Zeitraum“; ein Klick zeigt die Stelle im Verlauf. Das [Lärmprotokoll](#drucken) enthält eine eigene Tabelle.
- In **Home Assistant** erscheint je Handy ein Sensor „Erschütterung“ (Vibration) bzw. „Bewegung“ (Bewegung) – nutzbar in Automationen und in den [Regeln](#home-assistant/regeln), z. B. „nur festhalten“, damit es bei jeder Störung und im Tagesverlauf steht.

Gehört zu den externen Geräten und damit zu [GasLighter Pro](#pro).

## Geräte-Karte {#karte}

- **Name**, **aktiv**, **Verstärkung (dB)** und Brummfilter.
- **⚙ Pegel & Schwelle**: eigene Einstellungen nur für dieses Gerät.
- **📏 Eigene Referenzlinien**: z. B. „Fernseher −70 dB“, erscheinen in allen Grafiken dieses Geräts.
- **Protokolllisten**: Störungen dieses Geräts automatisch einer Liste zuordnen, auf Wunsch nur zu bestimmten Uhrzeiten.
- Aus einer [Sicherung](#sicherung) übernommene Geräte, die nicht erreichbar waren, sind ausgeschaltet und tragen den Hinweis „bitte prüfen“.

## Geräte einpegeln {#einpegeln}

Damit Pegel verschiedener Geräte vergleichbar sind:

1. Alle Mikrofone nebeneinander legen, etwa gleich weit (ca. 1 m) vom Lautsprecher.
2. **Geräte einpegeln** → mitmessende Geräte anhaken (mindestens zwei).
3. **Testgeräusch** wählen: **hier abspielen** (über den PC oder das Handy, auf dem die Einstellungen offen sind; mit **▶ Probehören** die Lautstärke prüfen), **auf Handy X abspielen** (ein verbundenes Handy spielt das Rauschen und misst dafür selbst nicht mit) oder **eigenes Geräusch** (Dunstabzug, Föhn …).
4. **Messung starten**: Die Schritte **1 Ruhe → 2 Geräusch → 3 Ergebnis** stehen groß da, darunter der Pegel jedes Geräts – so sieht man sofort, ob jedes Gerät das Geräusch hört. Das Testgeräusch startet und stoppt von selbst.
5. Ergebnis prüfen: Ist ein Gerät zu leise oder unruhig, steht dabei, was zu tun ist (z. B. „näher an den Lautsprecher“). Dann **Übernehmen und festhalten**.

Jedes Gerät bekommt eine eigene Verstärkung, sodass alle beim selben Geräusch denselben Wert zeigen. Jede Messung wird festgehalten und erscheint im Lärmprotokoll. Ändert sich die Verstärkung später von Hand, steht beim Gerät „⚠ seit dem Einpegeln geändert“; liegt das Einpegeln über 3 Monate zurück, wird erneutes Einpegeln empfohlen.

## Mehrere Räume vergleichen {#vergleich}

Löst ein Gerät aus, speichern alle anderen für denselben Zeitraum mit („Bei einer Störung alle Geräte mitspeichern“). Im Ereignis-Fenster zeigt **Vergleich der Geräte** die Spitze je Gerät. Ein Fernseher im Wohnzimmer ist dort am lautesten und hat viele Höhen; Klopfen über Decke und Wände ist in allen Räumen ähnlich und tief.
