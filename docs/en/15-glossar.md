# Glossary

| Term | Meaning |
|---|---|
| **dBFS** | level relative to the sound card's maximum (0 dBFS). Always negative: −80 very quiet, −50 conversation, −20 very loud. Not calibrated dB(A). |
| **Background** | the learned “normal” level, from the quietest moments of the recent time |
| **Threshold** | from this level it counts as a disturbance; adapts to the background by default |
| **Disturbance / event** | a rise above the threshold (ends 0.5 s below it, at most 5 min) |
| **Peak** | the highest level within 125 ms or within a disturbance |
| **Group** | consecutive disturbances of the same type with short pauses |
| **Day recording** | continuous measurements of the whole day per device (`clips/tag/`) |
| **Noise track** | measurements of a disturbance with context (level, frequency bands), no sound |
| **Spectrogram** | frequency over time, bright = loud; low at the bottom, high at the top |
| **Third-octave bands** | 23 frequency ranges from 50 Hz to 8 kHz |
| **Layers** | additional curves: low/mid/high, dominant frequency, spectral centroid |
| **Sound profile** | your own trained sound type (🧩) |
| **Named range** | a section marked and named by hand (🏷), learning example |
| **AI fingerprint** | the AI's numbers per second, describes the sound, no audio (ⓕ) |
| **Test threshold** | freely chosen value for counting peaks afterwards, display only |
| **Data chain** | SHA-256 checksums per minute, make changes visible |
| **Monitoring time** | set monitoring hours (e.g. 22–6) |
| **Quiet hours** | period for 🌙 in the log (e.g. 22–6, Sunday) |
| **Level-matching** | aligning the gain of devices so levels are comparable |
| **Record state** | Home Assistant rule that writes down states without pausing |

---
[← GLighter Pro](14-pro.md) · [Contents](README.md)
