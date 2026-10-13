# Geräte

Unter ⚙ Einstellungen → **Geräte** → Quellen stehen alle Mikrofone. Bis zu 9 Geräte sind möglich.

![Einstellungen: Geräte](../../gaslighter/app/web/hb/geraete_de.png)

<a id="server"></a>

## Server-Mikrofon

Das Mikrofon am Home-Assistant-Rechner. Unter **Mikrofon** wählst du Eingang, Buchse und Lautstärke. Meist „Standard“ lassen. **Brummfilter** (50 Hz in Europa) entfernt Netzbrummen.

<a id="handy"></a>

## Handy als Mikrofon

> **🔒 Pro:** Handys, Stream-URLs und IP-Kameras sind externe Geräte und gehören zu [GasLighter Pro](14-pro.md). Das Server-Mikrofon ist immer frei.

![GasLighter am Handy](../../gaslighter/app/web/hb/handy_de.png)

- **Handy (Browser)**: „+ Handy (Browser)“, QR-Code scannen, Seite in Chrome öffnen, Zertifikatswarnung bestätigen, **Start**. Der Bildschirm muss an bleiben (Ladegerät). Der Link ist geheim und gehört nur zu diesem Handy.
- **Stream (z. B. App „IP Webcam“)**: „+ Handy-App / Stream-URL“, Adresse `http://HANDY-IP:8080/audio.wav`. Läuft auch mit ausgeschaltetem Bildschirm. Mit Login: Benutzername und Passwort in die eigenen Felder.
- Der Handy-Port ist standardmäßig **18443** (Add-on → Netzwerk, „8443/tcp“).

<a id="video"></a>

### Video

Bei Streams lässt sich **🎥 Video aufnehmen** einschalten: Bei einer Störung entsteht eine mp4-Datei **ohne Ton**. Ohne Störung wird nichts gespeichert. Qualität und Speicherort unter Speichern & Ton → Video & Speicherort.

> Kameraaufnahmen in Wohnungen können nach § 201a StGB problematisch sein – nur eigene Räume, keine fremden Personen filmen.

<a id="bewegung"></a>

## Handy als Bewegungsmelder

Ein als Gerät eingerichtetes Handy kann zusätzlich zum Mikrofon als **Bewegungsmelder** dienen – wie ein Bewegungs- oder Vibrationssensor in Home Assistant:

- **🫨 Erschütterung** (Beschleunigungssensor): Das Handy liegt flach auf dem Boden, einem Tisch oder an der Wand und meldet Vibrationen – z. B. Trampeln, Bass, der durch die Decke kommt, Türenknallen oder Möbelrücken. Das belegt Körperschall, den man nicht nur hört, sondern spürt.
- **🏃 Bewegung im Kamerabild**: Die Kamera des Handys erkennt Bewegung im Bild (z. B. im Treppenhaus). Plötzliche Helligkeitsänderungen (Licht an/aus) werden herausgerechnet.

**Einschalten:** ⚙ Einstellungen → Geräte → Karte des Handys → **Handy als Bewegungsmelder** → „Erschütterung“ und/oder „Bewegung im Kamerabild“ anhaken, **Empfindlichkeit** wählen (hoch, mittel, niedrig). Danach am Handy die Seite neu laden und **Start** tippen. Der Browser fragt nach der Kamera bzw. (iPhone) nach „Bewegung und Ausrichtung“.

> **Datenschutz:** Ausgewertet wird nur auf dem Handy. Gesendet werden nur Zahlen (Stärke der Erschütterung, Anteil der veränderten Bildpunkte) – **kein Bild und kein Video**. Das Vorschaubild sieht man nur auf dem Handy selbst.

**Was dabei entsteht:**
- Am Handy und in der Geräteleiste blinkt 🫨 bzw. 🏃, solange ausgelöst ist.
- Jede Erschütterung bzw. Bewegung wird mit Beginn, Ende und Spitze gespeichert (`bewegung.csv` im Datenordner). Sie gilt bis 20 s nach dem letzten Auslösen als „an“.
- Im Reiter **Protokolle** steht die Liste „Erschütterung und Bewegung im Zeitraum“; ein Klick zeigt die Stelle im Verlauf. Das [Lärmprotokoll](08-drucken.md) enthält eine eigene Tabelle.
- In **Home Assistant** erscheint je Handy ein Sensor „Erschütterung“ (Vibration) bzw. „Bewegung“ (Bewegung) – nutzbar in Automationen und in den [Regeln](07-home-assistant.md#regeln), z. B. „nur festhalten“, damit es bei jeder Störung und im Tagesverlauf steht.

Gehört zu den externen Geräten und damit zu [GasLighter Pro](14-pro.md).

<a id="karte"></a>

## Geräte-Karte

- **Name**, **aktiv**, **Verstärkung (dB)** und Brummfilter.
- **⚙ Pegel & Schwelle**: eigene Einstellungen nur für dieses Gerät.
- **📏 Eigene Referenzlinien**: z. B. „Fernseher −70 dB“, erscheinen in allen Grafiken dieses Geräts.
- **Protokolllisten**: Störungen dieses Geräts automatisch einer Liste zuordnen, auf Wunsch nur zu bestimmten Uhrzeiten.
- Aus einer [Sicherung](09-sicherung.md) übernommene Geräte, die nicht erreichbar waren, sind ausgeschaltet und tragen den Hinweis „bitte prüfen“.

<a id="einpegeln"></a>

## Geräte einpegeln

Damit Pegel verschiedener Geräte vergleichbar sind:

1. Alle Mikrofone nebeneinander legen.
2. **Geräte einpegeln** → mitmessende Geräte anhaken (mindestens zwei) → Start.
3. 5 s Ruhe, dann ein gleichmäßiges Geräusch (z. B. Rauschen aus einem Handy-Lautsprecher, mindestens 10 dB lauter).

Jedes Gerät bekommt eine eigene Verstärkung, sodass alle beim selben Geräusch denselben Wert zeigen. Jede Messung wird festgehalten und erscheint im Lärmprotokoll. Ändert sich die Verstärkung später von Hand, steht beim Gerät „⚠ seit dem Einpegeln geändert“.

<a id="vergleich"></a>

## Mehrere Räume vergleichen

Löst ein Gerät aus, speichern alle anderen für denselben Zeitraum mit („Bei einer Störung alle Geräte mitspeichern“). Im Ereignis-Fenster zeigt **Vergleich der Geräte** die Spitze je Gerät. Ein Fernseher im Wohnzimmer ist dort am lautesten und hat viele Höhen; Klopfen über Decke und Wände ist in allen Räumen ähnlich und tief.

---
[← KI: Geräuscharten und Tonprofile](05-ki.md) · [Inhalt](README.md) · [Home Assistant →](07-home-assistant.md)
