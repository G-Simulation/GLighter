# Settings from A to Z

![Settings](einstellungen_{lang}.png)

At the very top choose **All devices** or a single device. For a device, “Own settings for this device” sets different values (threshold, minimum duration, monitoring time, storage). The bar at the top shows level, background, threshold and the **preview** (purple) of your not yet saved settings live. ⓘ explains every setting; “Show help” hides the texts.

## Devices {#geraete}

- **Sources (microphones)** – see [Devices](#geraete).
- **Level-match devices** – see [Level-matching](#geraete/einpegeln).
- **Microphone** {#s_audio} – input on the server, jack, volume, sound quality (16000 Hz is enough for knocking).

## Detection {#erkennung}

### When does something count as a disturbance? {#s_thr}

> **🔒 Pro:** without Pro these values are view only and GasLighter uses the defaults. They can be changed with [GasLighter Pro](#pro).

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

**Sound profiles** – see [AI](#ki/tonprofile). **Different values at certain times** (time profiles) {#s_sched} – e.g. more sensitive at night, general or per device.

## Times & pauses {#zeiten}

- **When to monitor?** {#s_time} – monitor from / to (both empty = around the clock, can span midnight). Outside that nothing is counted; via the indicator at the top you can record anyway.
- **Home Assistant: pause or record state** {#s_ha} – see [Home Assistant](#home-assistant/regeln).
- **Notes & log** {#s_notes} – quiet hours from / to (usually 22:00–6:00), Sunday all day quiet. Notes and disturbances during quiet hours get 🌙.

## Storage & sound {#speichern}

### Recording the disturbance {#s_rec}

| Setting | Meaning |
|---|---|
| Context (s) | this many seconds before and after the disturbance are shown when viewing |
| … with layers | low/mid/high, frequency for the whole day (+1–2 MB per device and day) |
| … with spectrum | spectrogram for every moment (+3–8 MB per device and day) |
| Store AI fingerprint continuously | see [AI fingerprint](#ki/fingerabdruck); below it shows whether it runs |
| Delete old recordings automatically / after days | off = nothing is ever deleted |

### Store real audio (not recommended) {#s_wav}

Default **off**. When on, a WAV file is stored with each disturbance. **Store audio only without detected voices** (recommended) prevents saving as soon as the AI detects voices anywhere. Read [Legal](#rechtliches) first.

### Video & storage {#s_video}

Folder for noise tracks, video width, frames per second, video quality.

## General {#allgemein}

- **General** {#s_misc} – recognize sound type (local AI), store AI fingerprint, group: max. pause, assign note, language.
- **Backup of the whole app** {#s_backup} – see [Backup](#sicherung).
- **Reset** – see [Reset](#sicherung/zuruecksetzen).
- **Diagnostics** – details on microphone and sound card for troubleshooting.
