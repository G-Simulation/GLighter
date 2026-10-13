# Troubleshooting and FAQ

## “The signal is very quiet” {#leise}

The background is very low (below −85 dBFS). Is the microphone in the right jack? Raise the microphone volume in ⚙ → Devices → Microphone or increase the device gain.

## “The threshold is at the lower limit” {#untergrenze}

It is so quiet that the threshold may not go lower. That is intended if very quiet sounds should not count. Otherwise lower the limit in ⚙ → Detection.

## Too many or too few disturbances {#empfindlichkeit}

- Too many: raise “How much louder than normal?” or set “Minimum duration” to 40–60 ms.
- Too few: lower the distance, lower the lower limit.
- Your own TV counts: record a sound profile as **background** or add a Home Assistant rule “record state” or “pause”.

## “Type (AI)” column is empty {#keine-ki}

- “AI detection is switched off”: ⚙ → General → switch on **Recognize sound type**.
- “AI model not found”: reinstall the add-on once with the **full zip** (update zips do not contain the model).
- “no fingerprint at this spot”: nothing was stored at that second (too quiet or computer busy). Check in ⚙ → Storage & sound whether the fingerprint is running.

## Gap in the history {#luecke}

Hatched = the add-on was not running. The cause is listed in Logs under “Not recorded …”. Add a comment: click the hatching. See [Interruptions](#unterbrechungen).

## Phone does not connect {#handy}

- Is port 18443 open (add-on → Network)? Certificate warning accepted?
- Keep the screen on or use the app “IP Webcam” as a stream.
- New link: create the QR code again in the device card.

## Update is not picked up {#update}

The folder must be at `\\homeassistant\share\gaslighter_update\gaslighter\…`. After 10–20 s without further changes the program restarts. The version is shown at the top next to the name.

## Where is the data? {#daten}

`/share/gaslighter` (via Samba `\\homeassistant\share\gaslighter`): `log.csv`, `clips/` (day recording in `clips/tag/`, AI in `clips/ki/`, notes, lists, profiles), settings and devices in `/data`.
