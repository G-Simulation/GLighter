# Logs

The **Logs** tab shows a period completely: summary, week strip, history of all devices, statistics and the list of all disturbances.

![Logs tab with summary and week strip](protokolle_{lang}.png)

## Period and filters {#zeitraum}

- **Monitoring time** (the set monitoring hours, e.g. 22–6), **Today**, **Yesterday**, **7 days**, **30 days** or **From–to**. ‹ › moves by a whole period.
- **Source / device**, **Type** (multiple choice, e.g. knocking + footsteps) and **List** filter everything below. Devices that no longer exist but still have data are listed as “(former)”.
- **🖨 Noise log** creates the noise log for period, device and list, **⬇ Image (SVG)** an image. See [Printing](#drucken).

## Arranging sections (dashboard) {#dashboard}

Live and Logs consist of **sections** (overview, interruptions, history, events by hour, per day, events in the period, notes and motion, sensors in the period). Each section has a bar at the top:

- **▾ / ▸** collapses and expands (also double-click on the bar).
- **✕** hides it. Insert it again via **▦ Customise layout** → **＋ Add section**.
- **⌖ visible range only** (events, sensors): only shows what is currently visible in the history – drag e.g. 20:00–22:00 in the history and the table or list shows only that time.

### ▦ Customise layout (designer) {#designer}

**▦ Customise layout** switches Live and Logs into edit mode – much like editing a dashboard in Home Assistant:

- **Move:** drag the ⠿ handle or use **↑ / ↓** in a section's bar to move it one place up or down.
- **Width:** drag the left or right edge (e.g. two sections side by side). The height follows the content.
- **✎ Change title:** your own name for the section or tile. Leave it empty to restore the original.
- **▾ / ▸** collapses and expands, **✕** takes the section out of the view.
- **＋ Add section** opens the library: all sections of this view (shown or hidden) to insert or remove, plus **new tiles** and **ready-made templates** (see below). You can also reset the remembered **table column widths** there.
- **↺ Reset** restores the default arrangement of this view after asking. **Done** ends editing.

**With the keyboard:** in edit mode pick a section with Tab (it gets a clear frame), then

| Key | Effect |
|---|---|
| ↑ / ↓ | one place up / down |
| ← / → | one column left / right |
| Shift + ← / → | narrower / wider |
| Shift + ↑ / ↓ | collapse / expand |
| F2 | change title |
| Delete | remove (after asking) |

Screen readers read the name of every section and announce the new position after each change.

**On phones** all sections are stacked. Change the order in edit mode with **↑ / ↓** – the arrangement on the PC is kept.

**Stored on the server:** arrangement, widths, collapsed and hidden sections, your own titles and the hand-dragged **table column widths** are kept in `layout.json` next to `sources.json`. PC, tablet and phone therefore show the same. If the server had no arrangement yet, GLighter takes the one saved in the browser the first time it opens. `layout.json` is part of the backup (ZIP) and comes back with “Take over settings and devices”. The layout never changes data.

“Sensors in the period” is hidden at first: sensor events (“as event”) are already in the table, “only record state” (e.g. TV) appears as a 📡 hint on every disturbance that falls into that time.

### 📊 Tiles (custom statistics) {#statistik}

**📊 ＋ Tile** (above the sections, in Live and Logs) or, in edit mode, **＋ Add section** → **New tile** adds a tile as its own section – move, widen, rename, collapse and hide it like the others.

**Kinds of tiles:**

- **Number** – big number with a label, e.g. disturbances today, disturbances in the last 7 days, average peak.
- **Trend** – line over days, weeks or months.
- **Bars** – e.g. per hour, weekday or day.
- **List** – the most frequent types, devices, sensors or note buttons (3 to 20 entries).
- **Table** – all values to sort and filter (like the other tables).

**Configuring:**

- **Templates (free for everyone):** e.g. “Disturbances today”, “Disturbances, last 7 days”, “Average peak (7 days)”, “Disturbance time today”, “Most frequent types (7 days)”, “Disturbances per device (30 days)”, “Trend per day (30 days)”, “Disturbances per hour (night)”, “Types compared”, “Trend per week”, “Per weekday”, “Total duration per day”, “Sensors per day”, “Notes by button”. A template goes into the view where you click it.
- **Configure your own (Pro):** *name*, *what to count* (disturbances – also just one type or sound profile –, sensors, notes with a quick-select button), *measure* (count, total duration, avg or highest peak), *split by* (hour, weekday, day, week, month, type, device, note button, sensor), *display* (number, line, bars, list, table), *period* (selected period, today, last 24 h / 7 / 30 / 90 / 365 days or a **custom period** from–to), *device*, **thresholds** (*only from peak* in dBFS, *only from duration* in seconds) and *night only / quiet hours only / weekend only*. The preview shows the result right away.
- **Clicking a bar**, a list entry or a table row (also with Enter or Space) filters the event table to it; click again or **✕** to remove the filter.
- **⚙** configures or deletes. Tiles only read – they never change data. Stored in `clips/statistik.json`, included in the backup.
- Every tile also appears **in Home Assistant** as a sensor (see [Home Assistant → Tiles](#home-assistant/kacheln)).

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

### Confirm or correct the sound type {#art-bestaetigen}

The detected type is shown as a coloured box in the **Type** column. Until you confirm it, it is a **“suggestion of the detection (confidence x %)”** – that is also how it appears in the noise log, the print and the raw data. **Click the box** (or ⋮ → Confirm sound type): **Correct** confirms the suggestion, another type corrects it, **Withdraw confirmation** undoes it. Your confirmation is kept in a separate file (`bestaetigt.json`); the detection's estimate, `log.csv` and the day recording stay unchanged. The detection says nothing about which flat a sound comes from.

### Filter out known sounds {#muster}

⋮ → **Filter out as pattern …** creates a [pattern](#einstellungen/muster) from the disturbance (device, type, time, duration and peak prefilled, with the preview “matches N disturbances of the last 30 days”). Filtered disturbances are then missing from the list; the count names them (“N filtered out by pattern”), **⊘ show filtered** brings them back with a mark.

### Notes in the table {#notizzeilen}

Every note you create appears as its own row **“📝 Note”** in the table, with time (from–to), device, tags, witness and text. If a disturbance lies in the note’s period, they are linked: the note row shows **“🔗 Disturbance …”** (click opens it) and the disturbance row shows the note text. **✎** edits the note. The filter **“📝 Notes”** hides or shows all note rows. Notes are not counted as disturbances.

## Log lists {#listen}

Your own lists such as “bathroom” or “garden” collect disturbances in addition to the full list – by hand (“Add to list”, or in the event under “Lists”) or automatically per device and time (⚙ Settings → Devices → device card → **Log lists**). Each list has its own note and its own noise log.
