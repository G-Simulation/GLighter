# Fehlerbehebung und häufige Fragen

<a id="leise"></a>

## „Das Signal ist sehr leise“

Der Hintergrund liegt sehr tief (unter −85 dBFS). Mikrofon an der richtigen Buchse? Mikrofon-Lautstärke in ⚙ → Geräte → Mikrofon erhöhen oder die Verstärkung des Geräts anheben.

<a id="untergrenze"></a>

## „Die Schwelle liegt an der Untergrenze“

Es ist so leise, dass die Schwelle nicht tiefer darf. Das ist gewollt, wenn sehr leise Geräusche nicht zählen sollen. Sonst die Untergrenze in ⚙ → Erkennung senken.

<a id="empfindlichkeit"></a>

## Zu viele oder zu wenige Störungen

- Zu viele: „Wie viel lauter als normal?“ erhöhen oder „Mindestdauer“ auf 40–60 ms.
- Zu wenige: Abstand verringern, Untergrenze senken.
- Eigener Fernseher zählt mit: Tonprofil als **Hintergrund** anlegen oder eine Home-Assistant-Regel „festhalten“ bzw. „pausieren“.

<a id="keine-ki"></a>

## Spalte „Art (KI)“ zeigt nichts

- „Die KI-Erkennung ist ausgeschaltet“: ⚙ → Erkennung → **Geräuschart erkennen** einschalten.
- „KI-Modell nicht gefunden“: das Add-on einmal mit der **vollen Zip** neu installieren (Update-Zips enthalten das Modell nicht).
- „kein Fingerabdruck an dieser Stelle“: An dieser Sekunde wurde nichts gespeichert (zu leise oder Rechner ausgelastet). Prüfe in ⚙ → Erkennung, ob der Fingerabdruck läuft.

<a id="luecke"></a>

## Lücke im Verlauf

Schraffiert = das Add-on lief nicht. Die Ursache steht in Protokolle unter „Nicht aufgezeichnet …“. Kommentar setzen: auf die Schraffur klicken. Siehe [Unterbrechungen](10-unterbrechungen.md).

<a id="handy"></a>

## Handy verbindet nicht

- Port 18443 freigegeben (Add-on → Netzwerk)? Zertifikatswarnung bestätigt?
- Bildschirm an lassen oder die App „IP Webcam“ als Stream nutzen.
- Neuer Link: in der Geräte-Karte den QR-Code neu erzeugen.

<a id="update"></a>

## Update wird nicht übernommen

Der Ordner muss als `\\homeassistant\share\gaslighter_update\gaslighter\…` liegen. Nach 10–20 s ohne weitere Änderungen startet das Programm neu. Die Version steht oben neben dem Namen.

<a id="daten"></a>

## Wo liegen die Daten?

`/share/gaslighter` (über Samba `\\homeassistant\share\gaslighter`): `log.csv`, `clips/` (Tagesaufzeichnung in `clips/tag/`, KI in `clips/ki/`, Notizen, Listen, Profile), Einstellungen und Geräte in `/data`.

---
[← Rechtliches und Datenschutz](12-rechtliches.md) · [Inhalt](README.md) · [GasLighter Pro →](14-pro.md)
