# Live view

The **Live** tab shows what is happening now: tiles with current values, the chart of the last minutes, the spectrogram and today's events.

<a id="kopfzeile"></a>

## Header

| Element | Meaning |
|---|---|
| **LIVE** | The view follows the present. After rewinding, go back to live here. |
| **Quiet / DISTURBANCE** | State of the selected device. Red = currently above the threshold. Outside the monitoring time you can “record anyway” here. |
| **Stop recording** | Pauses recording (logged in `aufzeichnung.csv`). On a phone in the ⋯ menu. |
| **🌓 Auto / ☀ / 🌙** | Light, dark or like Home Assistant. |
| **⚙ Settings** | All settings, see [Settings](11-einstellungen.md). |

<a id="kacheln"></a>

## Device bar and tiles

The bar below the note shows all devices with today's number of disturbances. Tap to select. With several live devices the view **rotates** automatically (duration via ⚙ in the bar).

- **Level** – current peak level.
- **Background** – the learned “normal” level.
- **Threshold** – from here it counts as a disturbance; below it says how it is calculated.
- **Sound now** – what the AI hears right now (only with sound type detection on).
- **Events** – disturbances today and in total.

<a id="grafik"></a>

## The chart

![Live chart with threshold, background and reference lines](../../gaslighter/app/web/hb/livegraph_en.png)

- **Blue area** = level, **grey line** = background, **orange dashed** = threshold, **red** = disturbance, dotted coloured lines = your own reference lines (e.g. “TV −70 dB”).
- **Level trace / Loudness bars** switches the display.
- **🗂 Layers** toggles curves: background, threshold, low/mid/high, dominant frequency, spectral centroid.
- **Time window** and **− / +** change the time shown; **Auto** fits the height.
- Below, the **spectrogram**: frequency over time, bright = loud. Low sounds (bass, footfall) are at the bottom, voices and dishes higher up.

<a id="bedienung"></a>

### Controls

| Computer | Phone / tablet |
|---|---|
| Mouse wheel or touchpad = zoom time | spread two fingers = zoom time |
| Drag or swipe sideways = move in time | swipe horizontally = move, vertically = scroll the page |
| Shift + drag = select a range and zoom in | − / + |
| Shift + wheel or wheel over the dB labels = zoom height (bottom-aligned) | “Auto” |
| Double click = back to live | Double tap = back to live |
| Hover over a disturbance = details | Tap a disturbance = details |

Further back than the last 10 minutes the chart shows the **whole day** from the day recording (time window 1 h, 6 h or “Today”).

<a id="notiz"></a>

## 📝 Note now

![Note bar with quick tags](../../gaslighter/app/web/hb/notiz_en.png)

For what you hear right now – just start typing or tap tags (upstairs, downstairs, knocking, bass, woke up …).

- **Without a time of its own**: if there was a disturbance shortly before (setting “Assign note”, default 5 min), the note belongs to it. The bar shows beforehand where it goes.
- **still going**: the note gets a period from the first input until saving.
- **From / to and witness** are always shown right in the area; leave them empty for “automatic” (time at saving).
- **Only tags, no text?** GasLighter builds a sentence from them when saving, e.g. “Clear footsteps in the stairwell”. You can edit it later.

<a id="schnellwahl"></a>

### Custom quick select

- **＋ Custom** at the end of the buttons: enter a name (e.g. “washing machine”, “neighbour 2nd floor”) → **Create**. The button (★) then appears in all note fields, also when detached, and in the notes filter.
- **Right-click or long-press** a button to open “Manage quick select”: **rename** or **delete** your own, **hide and show** built-in ones. Old notes keep their label.
- **Learning:** if you type a word yourself more often (3× or more), GasLighter suggests it as a button (💡). It is only created when you press **＋**; **✕** means “stop suggesting”.
- **Order:** what you press most often comes first – on a phone these are the first 6.
- Your buttons are stored in `clips/schnellwahl.json` and are included in the backup (ZIP).

**Detach (Pro):** **⧉** next to the title detaches the note area into its own small window. In Chrome and Edge it stays on top of other programs (e.g. over a game or film), otherwise it is a normal extra window. **Bring back** or closing the window puts it back.
- <kbd>Ctrl</kbd> + <kbd>Enter</kbd> saves. On a phone the bar starts collapsed.

<a id="markieren"></a>

## 🏷 Mark range

![Mark a range and assign it to a type](../../gaslighter/app/web/hb/markieren_en.png)

1. Tap “🏷 Mark range” – a hint with **Done** appears above the chart.
2. Drag across the range horizontally (0.15 s to 2 min).
3. Tap an **existing type** (sound profile 🧩 or named range 🏷) or enter a new name – same name = same type, the AI learns from it. See [AI](05-ki.md#lernen).

<a id="ereignisse-heute"></a>

## Events today

The list at the bottom shows all disturbances of the day (all devices or the selected one). A click opens the disturbance, see [Event window](04-ereignis.md). Choose columns via ⚙. On a phone the entries appear as cards.

---
[← Quick start in 5 minutes](01-schnellstart.md) · [Contents](README.md) · [Logs →](03-protokolle.md)
