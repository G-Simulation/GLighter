# Devices

All microphones are under ⚙ Settings → **Devices** → Sources. Up to 9 devices are possible.

![Settings: devices](geraete_{lang}.png)

## Server microphone {#server}

The microphone on the Home Assistant computer. Under **Microphone** you choose input, jack and volume. Usually leave it on “Default”. The **hum filter** (50 Hz in Europe) removes mains hum.

## Phone as a microphone {#handy}

> **🔒 Pro:** phones, stream URLs and IP cameras are external devices and part of [GasLighter Pro](#pro). The server microphone is always free.

![GasLighter on a phone](handy_{lang}.png)

- **Phone (browser)**: “+ Phone (browser)”, scan the QR code, open the page in Chrome, accept the certificate warning, **Start**. The screen must stay on (charger). The link is secret and belongs to this phone only.
- **Stream (e.g. the app “IP Webcam”)**: “+ Phone app / stream URL”, address `http://PHONE-IP:8080/audio.wav`. Also works with the screen off. With a login: user name and password in their own fields.
- The phone port is **18443** by default (add-on → Network, “8443/tcp”).

### Video {#video}

For streams you can switch on **🎥 Record video**: on a disturbance an mp4 file **without sound** is created. Nothing is stored without a disturbance. Quality and folder under Storage & sound → Video & storage.

> Camera recordings in homes can be problematic (§ 201a StGB in Germany) – only film your own rooms and no other people.

## Phone as a motion sensor {#bewegung}

A phone set up as a device can additionally act as a **motion sensor** – like a motion or vibration sensor in Home Assistant:

- **🫨 Vibration** (accelerometer): the phone lies flat on the floor, a table or against the wall and reports vibrations – e.g. stomping, bass coming through the ceiling, slamming doors or moving furniture. This documents structure-borne noise you feel, not just hear.
- **🏃 Motion in the camera picture**: the phone camera detects motion in the picture (e.g. in the stairwell). Sudden brightness changes (light on/off) are compensated.

**Switch on:** ⚙ Settings → Devices → card of the phone → **Phone as motion sensor** → tick "Vibration" and/or "Motion in camera picture", choose the **sensitivity** (high, medium, low). Then reload the page on the phone and tap **Start**. The browser asks for the camera or (iPhone) for "motion and orientation".

> **Privacy:** everything is evaluated on the phone. Only numbers are sent (vibration strength, share of changed pixels) – **no picture and no video**. The preview is only visible on the phone itself.

**What you get:**
- On the phone and in the device bar 🫨 or 🏃 blinks while triggered.
- Each vibration or motion is stored with start, end and peak (`bewegung.csv` in the data folder). It counts as "on" until 20 s after the last trigger.
- The **Reports** tab lists "Vibration and motion in the period"; a click shows the spot in the history. The [noise report](#drucken) contains its own table.
- In **Home Assistant** each phone gets a "Vibration" or "Motion" sensor – usable in automations and in the [rules](#home-assistant/regeln), e.g. "only record state", so it appears with every disturbance and in the daily chart.

Part of the external devices and therefore of [GasLighter Pro](#pro).

## Device card {#karte}

- **Name**, **active**, **gain (dB)** and hum filter.
- **⚙ Level & threshold**: own settings for this device only.
- **📏 Own reference lines**: e.g. “TV −70 dB”, shown in all charts of this device.
- **Log lists**: assign disturbances of this device to a list automatically, optionally only at certain times.
- Devices taken over from a [backup](#sicherung) that were not reachable are switched off and marked “please check”.

## Level-match devices {#einpegeln}

So that levels of different devices are comparable:

1. Put all microphones side by side.
2. **Level-match devices** → tick the devices to measure (at least two) → Start.
3. 5 s of quiet, then a steady sound (e.g. noise from a phone speaker, at least 10 dB louder).

Each device gets its own gain so that all show the same value for the same sound. Every measurement is recorded and listed in the noise log. If the gain is changed by hand later, the device shows “⚠ changed since level-matching”.

## Comparing rooms {#vergleich}

When one device triggers, all others store the same period too (“On a disturbance store all devices”). In the event window **Device comparison** shows the peak per device. A TV in the living room is loudest there and has many highs; knocking through ceiling and walls is similar and low in all rooms.
