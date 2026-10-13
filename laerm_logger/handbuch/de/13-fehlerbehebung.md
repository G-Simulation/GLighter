# Fehlerbehebung und häufige Fragen

## „Das Signal ist sehr leise“ {#leise}

Der Hintergrund liegt sehr tief (unter −85 dBFS). Mikrofon an der richtigen Buchse? Mikrofon-Lautstärke in ⚙ → Geräte → Mikrofon erhöhen oder die Verstärkung des Geräts anheben.

## „Die Schwelle liegt an der Untergrenze“ {#untergrenze}

Es ist so leise, dass die Schwelle nicht tiefer darf. Das ist gewollt, wenn sehr leise Geräusche nicht zählen sollen. Sonst die Untergrenze in ⚙ → Erkennung senken.

## Zu viele oder zu wenige Störungen {#empfindlichkeit}

- Zu viele: „Wie viel lauter als normal?“ erhöhen oder „Mindestdauer“ auf 40–60 ms.
- Zu wenige: Abstand verringern, Untergrenze senken.
- Eigener Fernseher zählt mit: Tonprofil als **Hintergrund** anlegen oder eine Home-Assistant-Regel „festhalten“ bzw. „pausieren“.

## Spalte „Art (KI)“ zeigt nichts {#keine-ki}

- „Die KI-Erkennung ist ausgeschaltet“: ⚙ → Allgemein → **Geräuschart erkennen** einschalten.
- „KI-Modell nicht gefunden“: das Add-on einmal mit der **vollen Zip** neu installieren (Update-Zips enthalten das Modell nicht).
- „kein Fingerabdruck an dieser Stelle“: An dieser Sekunde wurde nichts gespeichert (zu leise oder Rechner ausgelastet). Prüfe in ⚙ → Speichern & Ton, ob der Fingerabdruck läuft.

## Lücke im Verlauf {#luecke}

Schraffiert = das Add-on lief nicht. Die Ursache steht in Protokolle unter „Nicht aufgezeichnet …“. Kommentar setzen: auf die Schraffur klicken. Siehe [Unterbrechungen](#unterbrechungen).

## Handy verbindet nicht {#handy}

- Port 18443 freigegeben (Add-on → Netzwerk)? Zertifikatswarnung bestätigt?
- Bildschirm an lassen oder die App „IP Webcam“ als Stream nutzen.
- Neuer Link: in der Geräte-Karte den QR-Code neu erzeugen.

## Update wird nicht übernommen {#update}

Der Ordner muss als `\\homeassistant\share\laerm_update\laerm_logger\…` liegen. Nach 10–20 s ohne weitere Änderungen startet das Programm neu. Die Version steht oben neben dem Namen.

## Wo liegen die Daten? {#daten}

`/share/laerm` (über Samba `\\homeassistant\share\laerm`): `log.csv`, `clips/` (Tagesaufzeichnung in `clips/tag/`, KI in `clips/ki/`, Notizen, Listen, Profile), Einstellungen und Geräte in `/data`.
