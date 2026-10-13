# Logs

The **Logs** tab shows a period completely: summary, week strip, history of all devices, statistics and the list of all disturbances.

![Logs tab with summary and week strip](protokolle_{lang}.png)

## Period and filters {#zeitraum}

- **Monitoring time** (the set monitoring hours, e.g. 22–6), **Today**, **Yesterday**, **7 days**, **30 days** or **From–to**. ‹ › moves by a whole period.
- **Source / device**, **Type** (e.g. knocking only) and **List** filter everything below. Devices that no longer exist but still have data are listed as “(former)”.
- **🖨 Noise log** creates the noise log for period, device and list, **⬇ Image (SVG)** an image. See [Printing](#drucken).

## Arranging sections (dashboard) {#dashboard}

Live and Logs consist of **sections** (overview, interruptions, history, events by hour, per day, events in the period, notes and motion, sensors in the period). Each section has a bar at the top:

- **▾ / ▸** collapses and expands (also double-click on the bar).
- **✕** hides it. Switch it on again under **▦ Customise layout**.
- **⌖ visible range only** (events, sensors): only shows what is currently visible in the history – drag e.g. 20:00–22:00 in the history and the table or list shows only that time.

**▦ Customise layout:** move sections by the ⠿ handle, drag the side to make them narrower or wider (e.g. two side by side), switch sections on and off. **Done** saves, **↺ Reset** restores the default arrangement. The height follows the content. On phones all sections are stacked. The arrangement applies to this browser.

“Sensors in the period” is hidden at first: sensor events (“as event”) are already in the table, “only record state” (e.g. TV) appears as a 📡 hint on every disturbance that falls into that time.

## Summary and week strip {#wochenleiste}

The ring shows how much of the time was **undisturbed**. Next to it: number of disturbances, disturbed time, longest quiet, recorded time and the loudest event.

The **circles** below are the last 7 nights or days. Tap to choose a day; the newest one always stays visible. Below are the **data chain** (checksums) and interruptions, see [Interruptions](#unterbrechungen).

## History {#verlauf}

![History with level and spectrogram](verlauf_{lang}.png)

The history shows the devices below each other for the same period. Per row choose **device** and **display** (level trace, loudness bars, spectrogram) and toggle layers. “＋ Add row”, ↑ ↓ ✕ arrange the rows; the handle below each row changes its height.

- While the day is still running the time axis ends at **now** – the newest data is on the right and the history grows every minute.
- With more than 2 days it shows minute values, zooming in brings back the 125 ms values.
- At the top the AI marks the detected type of each disturbance in its colour; **blue** = on according to Home Assistant (e.g. TV).
- **Hatched** = not recorded (e.g. power cut). Click it to add a comment, see [Interruptions](#unterbrechungen/kommentar).

Controls as in the live view: wheel/two fingers zoom, drag a range, when zoomed drag or ‹ › to move, Shift + wheel for the height, double click or “Whole period” for everything. On a phone, test threshold, print and mark range are under **⋯ Tools**, the layers behind **🗂 Layers**.

## 📏 Test threshold {#pruefschwelle}

![Test threshold with the list of peaks](pruefschwelle_{lang}.png)

With the test threshold you check afterwards which peaks were above a freely chosen value – e.g. “How often was it above −50 dB?”

1. Tap “📏 Test threshold”, enter a value or drag the purple line in the history.
2. Per device you see number and duration of the peaks in the visible section (from the 125 ms values; less than 0.5 s apart = one peak).
3. “List of peaks” shows each peak with time, duration, height, distance, **Type (AI)** and **Sound profile**. A click jumps there in the history.

The type comes from the disturbance if the peak lies in one, otherwise from the stored **AI fingerprint** (ⓕ). Possible notes: “no fingerprint at this spot”, “no AI fingerprint on this day”, “not checked” (more than 2000 peaks). See [AI](#ki/fingerabdruck).

> The test threshold is **display only**. Stored data, disturbances and checksums stay unchanged. It is printed along when printing.

## Events in the period {#ereignisliste}

![List of events](ereignisliste_{lang}.png)

- **Groups** combines disturbances of the same type (at most “Group: max. pause” apart), **All single** shows each.
- **Sorting:** click a column header (start, duration, peak, threshold, background); click again to reverse. The sort order is remembered in the browser.
- **Filter with multiple choice:** under **Source / device** and **Type** click one or more entries, e.g. only “door sensor vibration” and “voice”. The line above the table counts disturbances and sensor events separately.
- **Sensor events** (Home Assistant rule “as event”, phone as motion sensor) are sorted in by time with an orange edge; ✎ = note.
- On narrow screens ⊕ at the start of a row expands the remaining columns.
- Click = jump there in the history, double click or ▶ = [open the event](#ereignis), ⋮ = more actions (download noise track, re-evaluate, delete).
- Select, then **Add to list** or delete. Deleted entries are kept in a recycle bin for safety; the day recording stays.
- **📝 All notes**, **🔎 Check a sound** (analyse your own audio file, not stored), **🧩 Profiles & re-scan**, **Download log.csv**.

## Log lists {#listen}

Your own lists such as “bathroom” or “garden” collect disturbances in addition to the full list – by hand (“Add to list”, or in the event under “Lists”) or automatically per device and time (⚙ Settings → Devices → device card → **Log lists**). Each list has its own note and its own noise log.
