# Legal and privacy

> **Not legal advice.** The law differs by country. If in doubt ask a lawyer or a tenants' association.

## What is stored {#gespeichert}

- **Measurements**: level, background, threshold, frequency bands (23 third-octave bands) in 125 ms steps. Research shows intelligible speech cannot be recovered at this resolution.
- **AI results** and **AI fingerprint**: numbers describing how it sounds – no audio, cannot be turned back into sound.
- **Your notes**, lists, sound profiles, states from Home Assistant.
- Everything stays **on your computer**. There is no cloud and no transfer to third parties.

## No sound, no speech recognition {#kein-ton}

Audio only lives briefly in memory (live view, detection) and is overwritten continuously. For voices only the **type** is detected, never the content – there is deliberately no speech recognition.

> **Warning (§ 201 StGB in Germany):** recording non-public speech can be a criminal offence unless it happens merely by chance. With continuous recording towards the neighbours this is foreseeable. That is why “Store real audio” is off by default and can only be switched on after a notice. Secret recordings are usually not admissible in court. Sound recordings never go into the noise log.

## Video {#video}

Camera recordings in homes can be problematic (§ 201a StGB). Only film your own rooms, no other people, not into other flats or the stairwell.

## Evidential value {#aussagekraft}

- Levels are **dBFS** (relative to the sound card), not a calibrated dB(A) measurement.
- A log is convincing when it is kept **regularly**, is **traceable** (time, duration, type, effect, witnesses) and **unchanged** (data chain).
- Your own notes (“woke up”, “child woken”) and witnesses make the difference.

## What the recording shows and what not {#belegt}

> **No legal advice.** The following points are factual hints from published decisions and expert articles (German law). They promise no success in court. For your case ask a lawyer, a tenants' association or a victim support service.

**It can show:** when, how long and how loud (relative, dBFS) it was, how often and at what times – over weeks and months, including that quiet days were measured too. And that the day recording has not been changed since (checksums).

**It cannot show:**

- **where** a sound comes from and who causes it – the detection “knocking” does not say which flat,
- **how loud in dB(A)** – the microphone is not calibrated: values are indications and do not replace an expert report,
- that the **sound type** is right while it is a “suggestion of the detection” – check it and confirm or correct it with a click in the event list. Your confirmation is kept separately (`bestaetigt.json`), the detection's estimate stays stored.

**What helps:** witnesses (neighbours, property management, police), timely notes with time, type, intensity, duration and frequency, reports with date and case number. In disputed cases courts obtain their own expert reports – the recording can show when a measurement is worthwhile.

**Checksums** show that the data has not been changed since recording; they are not an electronic signature. Digital data has no presumption of authenticity in court – so attach the raw data (CSV) and checksums (evidence package, see [Printing](#drucken/laermprotokoll)).

## Short hints in the app {#hinweise}

With **💡 Show help** (⚙ Settings → General) short hints appear in a few places. Each can be hidden with ✕; switching “Show help” off hides all of them. **Why?** names the source.

| Where | Hint | Source |
|---|---|---|
| Devices (setup) | Measure at a fixed place and note whether the window is open or closed. | AG Wolfratshausen 5 C 274/20 |
| Event list | Check detected sound types and confirm or correct them; the detection does not show which flat a sound comes from. | LG Berlin II 56 S 100/23 WEG |
| Recording, live | Keep measuring on quiet days – a gap-free time series shows frequency and pattern more convincingly. | BGH VIII ZR 1/16 Rn. 14; § 238 Abs. 2 StGB |
| Export, noise log | Pass on the values as an indication and suggest an expert report in a dispute. | AG München 472 C 18927/16; OLG Celle 4 U 199/09 |
| Export, noise log | Attach raw data (CSV) and checksums. | § 371 ZPO; Irskens, EDVGT 2024 |
| General | Do not add secret audio or video recordings of neighbours. | BGH VI ZR 1370/20; BVerfG 1 BvR 1611/96; AG München 173 C 11834/23 |
| General | Do not answer with counter-noise; document and take legal action. | AG München 173 C 11834/23 |
