# Home Assistant

GLighter works together with Home Assistant: rules read states (TV on, washing machine running, sensor triggered), and via MQTT the app reports disturbances, checksums and switches back.

## Rules {#regeln}

![Rule “raise threshold” as a card](regeln_{lang}.png)

⚙ Settings → tab **Rules** → **＋ Add rule**. First choose what the rule should do, then the device from the list (with search). States, delay and maximum duration are pre-filled to match. No automation, no YAML.

| Type | What happens | Example |
|---|---|---|
| 📈 **raise threshold** (Pro) | detection keeps running, only less sensitive | your own TV, Sonos |
| 🔕 **no disturbance reports** | graph keeps running, no disturbance | voice assistant, your own door |
| ⏸ **pause** | not evaluated during this time | vacuum |
| 📝 **only record state** | keep recording and note when it was on | TV |
| 🚩 **as event** | like record, plus a flag and its own row | door, vibration sensor |

Every rule is a **card**. Collapsed it shows name, type, device, the current state and a switch (on/off). A click expands it:

| Field | Meaning |
|---|---|
| **Name** | The rule is recorded under this name, e.g. “Wall vibration”. Empty = name from Home Assistant. |
| Action | the type (above), can be changed any time |
| Device (Home Assistant) | e.g. `media_player.tv`, `binary_sensor.wall_vibration` |
| For which device | which microphone the rule applies to (or all) |
| active when | states to tick (e.g. *on*, *playing*). Under **Condition as text** also `!off` = anything but off, `>1` = number greater than 1 |
| Delay, at most | for raise threshold, no disturbance reports and pause: keep going this long afterwards, maximum duration |

At the bottom of the card: **▶ Test** (asks Home Assistant now and tells whether the rule applies), **⧉ Copy**, **✕ Delete**. The top of the tab shows whether Home Assistant is connected and which rules are active right now.

### Raise threshold (TV, Sonos) {#anheben}

When your own TV is playing it should not cause a disturbance – noise from outside that is clearly louder still should. The rule raises the threshold while the device is on (plus delay). Detection keeps running.

- **Raise by:** e.g. +10 dB (0–40). The graph shows the raised threshold.
- **Follow the volume:** if the device reports its volume, the raise follows it. Example: calibrated at 35 % with +9 dB → at 18 % about +4.5 dB, muted no raise (at most double).
- **🎚 Calibrate – hold down:** let the TV or Sonos play as loud as usual, otherwise keep quiet. Hold the button for at least 3 seconds. While measuring, GLighter takes the level; on release it takes the current volume. Raise = device level (95 %) + 3 dB margin above the normal threshold. The result is shown in the card and in the log.
- **Evidence:** the events table shows “📈 TV +9 dB” for every disturbance in that time, the disturbance itself “threshold +9 dB”. The periods are stored in `ha_anhebung.csv`. The day recording keeps running unchanged.
- Without Pro the rule is saved but has no effect.


“now: …” shows live what Home Assistant reports – so you see which state a device really has. When in doubt, it records.

**Record state** writes every change to `ha_zustand.csv`. Each disturbance then shows e.g. “TV: on · 🔊 18 %”, the history shows a **blue band**, and the noise log names the state. If the TV reports its volume, it is recorded too.

> Entries already recorded keep their name, even if you change it later.

**As event** draws a coloured flag per sensor and a red line across the full height. Choose the colour in the rule under **Colour** (↺ = automatic). Every “on” appears under **📡 Sensor events** in the events table – with time, duration and note (✎). Sensor events do **not** count as disturbances and are counted separately. Switching applies retroactively, because the states are already in `ha_zustand.csv`. “Only record state” shows a thin blue strip at the top (one lane per sensor); only **pause** fills the full height.

**Note for a period:** click the strip (or ✎ in the list) to add a note, e.g. “watched a film”. It appears in the strip, the list and the noise report.

**Filter “📡 Sensors”** (Logs, top): multiple choice of which sensors, phone vibration/motion and whether disturbances are shown. Applies to history, lists and table.

## Zigbee sensors (vibration, motion, door) {#zigbee}

Sensors integrated in Home Assistant (e.g. via Zigbee2MQTT or ZHA) work the same way:

1. Add a rule, choose the sensor entity (e.g. `binary_sensor.vibration_ceiling_occupancy`).
2. Enter a name, e.g. “ceiling vibration”.
3. Action **as event** (or **only record state**), “on when” `on`.

From then on every disturbance shows whether a vibration was reported at the same time – a strong hint at footfall or knocking through the building.

## MQTT: control and reports {#mqtt}

With MQTT set up, Home Assistant shows the device **GLighter** with:

- Switch **Recording**, **Record manually (outside hours)**, number **Pause (minutes)**, buttons **Pause 15 min**, **Pause 1 h**, **Resume**, sensor **Paused until**.
- Per device: event **Disturbance (trigger)** (start, end, detected – with peak, duration, type, profile), device triggers for automations, sensor “Last sound type” and hourly the current **checksum** (stored independently in Home Assistant).

Example – pause for 10 minutes while the litter box cleans:

```yaml
automation:
  - alias: "Pause GLighter while the litter box cleans"
    trigger:
      - platform: state
        entity_id: sensor.litter_box_status
        to: "cleaning"
    action:
      - service: mqtt.publish
        data:
          topic: gaslighter/pause/set
          payload: '{"minutes": 10, "reason": "litter box"}'
```

Recording stopped by hand is not restarted automatically by a pause from Home Assistant.

## Log a disturbance right from the dashboard

With MQTT the add-on adds two elements to the "GLighter" device:

- **Log disturbance / note**: text field. Type text, press Enter, and the note is saved with the current time. The field clears afterwards.
- **Mark disturbance now**: button. One tap creates a note "Disturbance (Home Assistant)" immediately, without text.

Put both on any dashboard (for example in an "Entities" card). If a disturbance was detected just before, the note is attached to it, exactly like the note bar in the live view.

## No disturbance reports (graph keeps recording)

Sometimes a disturbance should not be reported while the graph keeps recording, for example when you open the door yourself.

- **In a rule:** choose the action **"no disturbance reports"**. While the condition holds and for the **delay** afterwards (for example 10 minutes), no disturbance is created. The graph keeps recording, with no gap.
- **Lead time (s), e.g. for a voice assistant:** the wake word (“Hey Jarvis”) comes *before* the assistant switches to “listening”. With **lead time**, a disturbance that started up to this many seconds before the rule switched on does not count either. For this, GLighter holds each disturbance back that long (lead time + 2 s) before reporting it. Levels and graph stay unchanged; the log says “not counted”. **Set up:** add a rule, choose the entity `assist_satellite.…` – states `!idle`, “no disturbance reports”, lead time 3 s and delay 0.5 min are pre-filled. Wake word, command and the spoken answer then don’t count.
- **As a dashboard button:** the "GLighter" device has **"Start: no disturbance reports"**, **"Report disturbances again"**, an adjustable **duration** (1–240 minutes, default 10) and **"No disturbance reports until"**. Put them on your dashboard. One tap starts the set duration.
