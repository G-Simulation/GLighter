# Backup, import and export

## Download a backup {#export}

⚙ Settings → General → **Backup of the whole app** → **⬇ Download backup**. The ZIP file contains everything: settings, devices, time profiles, rules, `log.csv` and all log files, day recordings with checksums, AI results, sound profiles, notes, comments on interruptions, named ranges, lists, videos and – if stored – sound.

> The file can get large (hundreds of MB). Download it regularly and keep it in another place.

For further processing there are also `log.csv` (Logs tab), the notes as CSV (📝 All notes) and the noise log as PDF.

## Restore a backup {#import}

> **🔒 Pro:** the first import is free (e.g. when moving), further imports are part of [GasLighter Pro](#pro/umzug). Downloading a backup is always free.

![Preview when restoring](sicherung_{lang}.png)

1. **📂 Choose backup** and **Check backup …** – the file is uploaded and examined, nothing is changed yet.
2. The preview shows version and date of the backup and – with “Take over settings and devices” – every device from the backup:
   - **already here** (will be replaced) or **new**,
   - **ready**, **phone** (connects as soon as it opens the app) or **not reachable** (taken over switched off, marked “please check”).
   - Devices set up only here **stay unchanged**.
   - If the backup's microphone does not exist here, the current one stays selected.
3. Set or clear the ticks and **Restore now**.

Afterwards a report shows new files, merged days, skipped days and the devices taken over.

### Daily backup to network drive, NAS or USB {#ziel}

> **🔒 Pro:** The daily backup and “save space” are part of [GasLighter Pro](#pro). **“⬇ Download backup” and `log.csv` always stay free.** If Pro expires, the daily backup pauses; days already moved stay readable.

⚙ Settings → Storage & sound → **Daily backup**. With a target set, GasLighter copies everything new there every day (default 03:30) – the same files as the ZIP backup, but **incremental**: only new and changed files, each verified with SHA-256 afterwards.

- **Nothing is ever deleted in the target.** If an already backed-up file changes later, the old version stays next to it as `….alt-YYYYMMDD-hhmmss`.
- **Target unreachable** (NAS off, Wi-Fi gone): recording continues normally on this device. It is retried hourly, and the next run catches up everything missing.
- **Back up now** starts a run immediately; last run, number of files and errors are shown next to it.

**Examples for the target**

| Target | How to set up | Folder to enter |
|---|---|---|
| NAS / Windows share (SMB) | Home Assistant → Settings → System → Storage → **Add network storage**, name e.g. `nas_gaslighter`, usage **Share** | `/share/nas_gaslighter` |
| NAS as media folder | as above, usage **Media** | `/media/nas_gaslighter` |
| USB drive on the Home Assistant device | plug it in (appears under `/media`) | e.g. `/media/usb/gaslighter` |

> The target must already exist and must **not be on the same storage** as the data. Otherwise a network drive that is not mounted would silently fill your own storage – GasLighter reports this as an error and copies nothing.

### Save space {#auslagern}

With **“Save space: keep old data only in the target”**, files older than “Delete after (days)” that are verified in the target are replaced here by a link to the copy. **Reports, history, printing and the checksum chain keep working** – they read these days from the target. If the network drive is asleep, the first load takes a little longer (“network drive may be waking up”). If it is unreachable, these old days are missing until it is back. Settings, `log.csv` and recent days always stay here.

If **“Delete old recordings automatically”** is also on, GasLighter only deletes what is verified in the target once a target is set.

## What happens when restoring {#zusammenfuehren}

- **Nothing twice, nothing overwritten**: existing disturbances, notes and lists stay, only missing data is added. Restoring several times does no harm.
- **Days that already exist** (e.g. “today” after a reinstall): the missing minutes are added. The checksum chain stays verifiable – the restored part gets its own section, and “Interruptions” lists “Import …: extended by N minutes”. If the times overlap with other data, the day is skipped and named in the report.
- **Devices that no longer exist**: their data is still restored and can be chosen as “(former)” in the history, the device filter and printing.
- Storage locations (output and clip folder) stay those of this system.

## Reset {#zuruecksetzen}

⚙ → General → **Reset**: measurements & disturbances, notes & lists, sound profiles or settings to default. Devices and connections always stay. A backup is offered first.

## Search index {#suchverzeichnis}

GasLighter keeps a **search index** (SQLite file `suchindex.sqlite` in the app data folder). It speeds up noise reports over weeks and months:

- **Chain check per day:** the result is stored with a SHA-256 checksum over the *content* of all files of that day. If a single byte changes, the day is checked again – the check is exactly as strict as without the index.
- **Condensed day tracks** (every 10 seconds) for the charts in the noise report.

The index only contains derived data, never changes the recording, checksum chain or disturbances, is not part of the backup and fills slowly in the background after start. **Settings → General → Backup → Rebuild** clears it; it then rebuilds itself. If it is missing or damaged, GasLighter works without it – just slower.
