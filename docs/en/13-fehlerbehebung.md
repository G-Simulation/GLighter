# Troubleshooting and FAQ

<a id="leise"></a>

## “The signal is very quiet”

The background is very low (below −85 dBFS). Is the microphone in the right jack? Raise the microphone volume in ⚙ → Devices → Microphone or increase the device gain.

<a id="untergrenze"></a>

## “The threshold is at the lower limit”

It is so quiet that the threshold may not go lower. That is intended if very quiet sounds should not count. Otherwise lower the limit in ⚙ → Detection.

<a id="empfindlichkeit"></a>

## Too many or too few disturbances

- Too many: raise “How much louder than normal?” or set “Minimum duration” to 40–60 ms.
- Too few: lower the distance, lower the lower limit.
- Your own TV counts: record a sound profile as **background** or add a Home Assistant rule “record state” or “pause”.

<a id="keine-ki"></a>

## “Type (AI)” column is empty

- “AI detection is switched off”: ⚙ → General → switch on **Recognize sound type**.
- “AI model not found”: reinstall the add-on once with the **full zip** (update zips do not contain the model).
- “no fingerprint at this spot”: nothing was stored at that second (too quiet or computer busy). Check in ⚙ → Storage & sound whether the fingerprint is running.

<a id="luecke"></a>

## Gap in the history

Hatched = the add-on was not running. The cause is listed in Logs under “Not recorded …”. Add a comment: click the hatching. See [Interruptions](10-unterbrechungen.md).

<a id="handy"></a>

## Phone does not connect

- Is port 18443 open (add-on → Network)? Certificate warning accepted?
- Keep the screen on or use the app “IP Webcam” as a stream.
- New link: create the QR code again in the device card.

<a id="update"></a>

## Update is not picked up

The folder must be at `\\homeassistant\share\gaslighter_update\gaslighter\…`. After 10–20 s without further changes the program restarts. The version is shown at the top next to the name.

<a id="daten"></a>

## Where is the data?

`/share/gaslighter` (via Samba `\\homeassistant\share\gaslighter`): `log.csv`, `clips/` (day recording in `clips/tag/`, AI in `clips/ki/`, notes, lists, profiles), settings and devices in `/data`.

---
[← Legal and privacy](12-rechtliches.md) · [Contents](README.md) · [GasLighter Pro →](14-pro.md)
