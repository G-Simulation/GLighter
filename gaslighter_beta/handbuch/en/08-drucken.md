# Printing and noise log

There are two printouts: the **noise log** (report with summary and list) and the **history as a score sheet** (the curves line by line).

## Noise log {#laermprotokoll}

Logs tab → **🖨 Noise log** (for period, device and list) or **📝 All notes** → log. It contains:

- period, devices, summary (count, disturbed time, longest quiet), detected sound types, named ranges,
- the **day history**: one chart per day and device over 24 h (peak, background, threshold, disturbances red, Home Assistant blue, not recorded hatched, notes), same scale per device,
- every disturbance with date, time, duration, level, type, notes, witnesses and states from Home Assistant,
- quiet hours (🌙), countermeasures, level-matching of the devices,
- **interruptions and updates** with cause and your comment,
- the **data chain** per device and day with checksum.

At the top of the page (not printed) choose **Day chart** (on by default) and **Chart per disturbance** (off by default): a small chart with context below every disturbance that has a note or comes from the chosen list (at most 300).

Print in the browser or save as PDF. The printed document is always titled “Lärmprotokoll” (noise log).

> Levels are relative dBFS values, not a calibrated dB(A) measurement. Sound recordings never go into the log. Not legal advice.

## Print history (score sheet) {#notenblatt}

![Print dialog](druckdialog_{lang}.png)

In the history **🖨 Print**:

- **Period**: from–to or quick choice “Visible section”, “Period of the report”, “All data”.
- **Time per line**: 1 min to 1 h (default 10 min – a whole day is 144 lines).
- **Devices** below each other, **content** (level trace, spectrogram, disturbance info and notes), **Merge lines without recording** (on by default).
- **Scale**: the same for all lines (comparable) or fitted per line (more detail); **A4 landscape** or **portrait**.

The dialog estimates lines and pages. **Open preview** builds the pages in a new window; print there or save as PDF. An active [test threshold](#protokolle/pruefschwelle) is printed along, with a count per line.

![Print preview](druckseite_{lang}.png)
