# Home Assistant

GasLighter works together with Home Assistant: rules read states (TV on, washing machine running, sensor triggered), and via MQTT the app reports disturbances, checksums and switches back.

## Rules: pause or record state {#regeln}

![Home Assistant rule with name](regeln_{lang}.png)

⚙ Settings → Times & pauses → **Home Assistant: pause or record state** → **Add rule**.

| Field | Meaning |
|---|---|
| Entity | e.g. `media_player.tv`, `binary_sensor.vibration_wall` |
| Device | which microphone the rule applies to (or all) |
| **Name** | The rule is recorded under this name, e.g. “wall vibration”. Empty = name from Home Assistant. |
| Action | **only record state** (keep recording and write it down, e.g. your own TV), **as event** (like record state, plus its own row in the events table, e.g. door or vibration sensor) or **pause** (do not record during that time) |
| on when / pause when | `on, playing` = one of them, `!off` = everything except off, `>1` = number above 1 |
| Delay, at most | only with “pause”: keep pausing this long afterwards, maximum duration |

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

With MQTT set up, Home Assistant shows the device **GasLighter** with:

- Switch **Recording**, **Record manually (outside hours)**, number **Pause (minutes)**, buttons **Pause 15 min**, **Pause 1 h**, **Resume**, sensor **Paused until**.
- Per device: event **Disturbance (trigger)** (start, end, detected – with peak, duration, type, profile), device triggers for automations, sensor “Last sound type” and hourly the current **checksum** (stored independently in Home Assistant).

Example – pause for 10 minutes while the litter box cleans:

```yaml
automation:
  - alias: "Pause GasLighter while the litter box cleans"
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

With MQTT the add-on adds two elements to the "GasLighter" device:

- **Log disturbance / note**: text field. Type text, press Enter, and the note is saved with the current time. The field clears afterwards.
- **Mark disturbance now**: button. One tap creates a note "Disturbance (Home Assistant)" immediately, without text.

Put both on any dashboard (for example in an "Entities" card). If a disturbance was detected just before, the note is attached to it, exactly like the note bar in the live view.
