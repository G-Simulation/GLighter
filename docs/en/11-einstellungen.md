# Settings from A to Z

![Settings](../../laerm_logger/app/web/hb/einstellungen_en.png)

At the very top choose **All devices** or a single device. For a device, “Own settings for this device” sets different values (threshold, minimum duration, monitoring time, storage). The bar at the top shows level, background, threshold and the **preview** (purple) of your not yet saved settings live. ⓘ explains every setting; “Show help” hides the texts.

<a id="geraete"></a>

## Devices

- **Sources (microphones)** – see [Devices](06-geraete.md).
- **Level-match devices** – see [Level-matching](06-geraete.md#einpegeln).
- **Microphone**<a id="s_audio"></a> – input on the server, jack, volume, sound quality (16000 Hz is enough for knocking).

<a id="erkennung"></a>

## Detection

<a id="s_thr"></a>

### When does something count as a disturbance?

> **🔒 Pro:** without Pro these values are view only and GasLighter uses the defaults. They can be changed with [GasLighter Pro](14-pro.md).

| Setting | Meaning |
|---|---|
| Type of threshold | **Adapts, with limits** (recommended), **Adapts**, **Fixed** |
| How much louder than normal? | distance to the background, 8–10 dB is a good start. Smaller = more sensitive. |
| Lower / upper limit | the threshold never goes below or above |
| Fixed threshold | only with “Fixed” |
| “Normal” is learned from the last … | period for the background (e.g. 60 s) |
| How “normal” is calculated | **Quietest moments** (recommended), typical level, minimum, average, maximum |
| Adapting when it gets louder / quieter | large = noise hardly pulls the threshold along; small = follows quickly |
| Minimum duration (ms) | 0 = every knock counts; 40–60 filters clicks |

**Sound profiles** – see [AI](05-ki.md#tonprofile). **Different values at certain times** (time profiles)<a id="s_sched"></a> – e.g. more sensitive at night, general or per device.

<a id="zeiten"></a>

## Times & pauses

- **When to monitor?**<a id="s_time"></a> – monitor from / to (both empty = around the clock, can span midnight). Outside that nothing is counted; via the indicator at the top you can record anyway.
- **Home Assistant: pause or record state**<a id="s_ha"></a> – see [Home Assistant](07-home-assistant.md#regeln).
- **Notes & log**<a id="s_notes"></a> – quiet hours from / to (usually 22:00–6:00), Sunday all day quiet. Notes and disturbances during quiet hours get 🌙.

<a id="speichern"></a>

## Storage & sound

<a id="s_rec"></a>

### Recording the disturbance

| Setting | Meaning |
|---|---|
| Context (s) | this many seconds before and after the disturbance are shown when viewing |
| … with layers | low/mid/high, frequency for the whole day (+1–2 MB per device and day) |
| … with spectrum | spectrogram for every moment (+3–8 MB per device and day) |
| Store AI fingerprint continuously | see [AI fingerprint](05-ki.md#fingerabdruck); below it shows whether it runs |
| Delete old recordings automatically / after days | off = nothing is ever deleted |

<a id="s_wav"></a>

### Store real audio (not recommended)

Default **off**. When on, a WAV file is stored with each disturbance. **Store audio only without detected voices** (recommended) prevents saving as soon as the AI detects voices anywhere. Read [Legal](12-rechtliches.md) first.

<a id="s_video"></a>

### Video & storage

Folder for noise tracks, video width, frames per second, video quality.

<a id="allgemein"></a>

## General

- **General**<a id="s_misc"></a> – recognize sound type (local AI), store AI fingerprint, group: max. pause, assign note, language.
- **Backup of the whole app**<a id="s_backup"></a> – see [Backup](09-sicherung.md).
- **Reset** – see [Reset](09-sicherung.md#zuruecksetzen).
- **Diagnostics** – details on microphone and sound card for troubleshooting.

---
[← Interruptions, data chain and updates](10-unterbrechungen.md) · [Contents](README.md) · [Legal and privacy →](12-rechtliches.md)
