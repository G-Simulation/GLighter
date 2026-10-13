"""Geraeuschart-Erkennung (lokal, YAMNet in numpy). Alles hier ist reine Zusatzinformation:
nichts wird wegen der Erkennung geloescht oder weggelassen."""
import io
import json
import math
import os
import shutil
import subprocess
import threading
import wave

import numpy as np

import yamnet_np

R = lambda *a: list(range(*a))
# Gruppe -> AudioSet-Klassen (Index laut yamnet_class_map.csv)
GROUPS = {
    "knock":  [353, 354, 460, 454, 455, 461, 462, 413, 168, 431, 432, 434, 428, 430, 161, 459, 465],
    "door":   [348, 349, 350, 351, 352, 356, 357],
    "steps":  [46, 47, 48, 83],
    "voice":  R(0, 13) + R(13, 23) + [33, 34, 63, 65, 64, 66, 61, 62],
    "tv":     R(24, 32) + R(132, 277) + [5, 518, 519, 213, 31],
    "noise":  R(277, 294) + R(294, 348) + [371, 367, 363, 362, 406, 407, 487, 490, 510, 516, 517, 482, 507, 508, 509, 514, 515, 372, 337],
    "scrape": [468, 469, 470, 480, 355, 473, 474, 472, 471, 493, 481, 485, 486, 399],
    "signal": R(382, 398) + [302, 303, 304, 349, 475, 476, 477, 378, 379, 380, 383, 384, 385],
    "animal": R(67, 132),
}
WEIGHT = {507: 0.6, 508: 0.6, 509: 0.6, 514: 0.6, 515: 0.6, 337: 0.7, 66: 0.8, 64: 0.8, 65: 0.8, 47: 0.9}
ORDER = ["knock", "door", "steps", "voice", "tv", "scrape", "signal", "animal", "noise", "other"]
MIN_SCORE = 0.10
FFMPEG = shutil.which("ffmpeg")

_LOCK = threading.Lock()
_NET = None
_IDX = None          # (Gruppe-Namen, Matrix 521 x G mit Gewichten)


def _net():
    global _NET, _IDX
    if _NET is None:
        _NET = yamnet_np.YamNet()
        names = [g for g in ORDER if g in GROUPS]
        _IDX = (names, GROUPS, WEIGHT)
    return _NET


def available():
    return os.path.exists(os.path.join(yamnet_np._DIR, "yamnet.npz"))


def group_of(cls):
    best = None
    for g in ORDER:
        if g in GROUPS and cls in GROUPS[g]:
            best = g; break
    return best or "other"


def decode(data, rate=None):
    """Bytes einer Audiodatei -> float32 mono 16 kHz. WAV direkt, anderes ueber ffmpeg."""
    try:
        with wave.open(io.BytesIO(data), "rb") as w:
            ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            raw = w.readframes(n)
        if sw == 2:
            x = np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0
        elif sw == 1:
            x = (np.frombuffer(raw, np.uint8).astype(np.float32) - 128) / 128.0
        elif sw == 3:
            b = np.frombuffer(raw, np.uint8).reshape(-1, 3)
            v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
            x = ((v ^ 0x800000) - 0x800000).astype(np.float32) / 8388608.0
        elif sw == 4:
            x = np.frombuffer(raw, "<i4").astype(np.float32) / 2147483648.0
        else:
            raise ValueError("bad sample width")
        if ch > 1:
            x = x[: len(x) // ch * ch].reshape(-1, ch).mean(axis=1)
        return _resample(x, sr)
    except (wave.Error, EOFError, ValueError):
        if not FFMPEG:
            raise ValueError("unsupported audio file (WAV expected)")
    p = subprocess.run([FFMPEG, "-v", "error", "-i", "pipe:0", "-t", "300", "-f", "f32le", "-ar", "16000", "-ac", "1", "pipe:1"],
                       input=data, capture_output=True, timeout=120)
    if p.returncode != 0 or not p.stdout:
        raise ValueError("audio file could not be read")
    return np.frombuffer(p.stdout, "<f4").copy()


def _resample(x, sr):
    if sr == 16000 or len(x) == 0:
        return x.astype(np.float32)
    g = math.gcd(int(sr), 16000)
    try:
        from scipy import signal as sps
        return sps.resample_poly(x, 16000 // g, int(sr) // g).astype(np.float32)
    except Exception:
        t = np.arange(int(len(x) * 16000 / sr)) * sr / 16000.0
        return np.interp(t, np.arange(len(x)), x).astype(np.float32)


def pcm_to_float(raw, rate):
    return _resample(np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0, rate)


def analyse(x, max_patches=240):
    """x: float32 mono 16 kHz. Gibt Gruppen, Top-Klassen und Zeitverlauf zurueck."""
    with _LOCK:
        net = _net()
        x = np.asarray(x, np.float32)
        if len(x) < 4000:
            raise ValueError("audio too short")
        cut = False
        if len(x) > (max_patches - 1) * yamnet_np.HOP + yamnet_np.PATCH:
            x = x[: (max_patches - 1) * yamnet_np.HOP + yamnet_np.PATCH]; cut = True
        sc = net.scores(x, max_patches=max_patches)          # (P, 521)
    P = len(sc)
    hop, pl = yamnet_np.HOP, yamnet_np.PATCH
    w = np.ones(sc.shape[1], np.float32)
    for c, v in WEIGHT.items():
        w[c] = v
    sc = sc * w
    gs = {}
    for g, idx in GROUPS.items():
        gs[g] = sc[:, idx].max(axis=1)
    rms = np.array([float(np.sqrt(np.mean(x[i * hop:i * hop + pl] ** 2) + 1e-12)) for i in range(P)])
    loud = np.where(rms >= rms.max() * 0.5)[0]
    loud = loud[np.argsort(-rms[loud])][:4]
    gloud = {g: float(gs[g][loud].max()) for g in gs}
    best = max(gloud, key=gloud.get)
    art, conf = (best, gloud[best]) if gloud[best] >= MIN_SCORE else ("other", gloud[best])
    top_scores = sc[loud].max(axis=0)
    top = []
    for c in np.argsort(-top_scores)[:5]:
        if top_scores[c] < 0.03:
            break
        top.append({"name": net.names[c], "pct": int(round(100 * float(top_scores[c]))), "group": group_of(int(c))})
    timeline = []
    for i in range(P):
        g = max(gs, key=lambda k: gs[k][i])
        timeline.append({"t": round(i * hop / 16000.0, 2), "g": g if gs[g][i] >= MIN_SCORE else "other",
                         "pct": int(round(100 * float(gs[g][i]))), "db": round(20 * math.log10(rms[i] + 1e-9), 1)})
    return {"ok": True, "art": art, "conf": int(round(100 * conf)), "top": top,
            "groups": {g: int(round(100 * v)) for g, v in sorted(gloud.items(), key=lambda kv: -kv[1])},
            "timeline": timeline, "seconds": round(len(x) / 16000.0, 1), "cut": cut}


def analyse_wav_file(path):
    with open(path, "rb") as f:
        return analyse(decode(f.read()))


# ---------------------------------------------------------------------------
# Feine Geraeuscharten fuer Marker auf der Grafik (Reihenfolge = Vorrang bei Gleichstand)
# Schluessel: (Deutsch, Englisch, Symbol, Gruppe, AudioSet-Klassen)
# Sprache wird nur als Art erkannt ("Stimmen", "Rufen" ...), nie der Inhalt.
# ---------------------------------------------------------------------------
FINE = {
    "slam":      ("Türknallen", "Door slam", "🚪", "door", [352]),
    "door":      ("Tür", "Door", "🚪", "door", [348, 351]),
    "cupboard":  ("Schrank/Schublade", "Cupboard/drawer", "🗄", "door", [356, 357]),
    "creak":     ("Knarren/Quietschen", "Creak/squeak", "🪵", "scrape", [480, 355, 479]),
    "knock":     ("Klopfen", "Knocking", "✊", "knock", [353, 354]),
    "thud":      ("Dumpfer Schlag", "Thud", "💥", "knock", [454, 455, 462, 461]),
    "bang":      ("Knall", "Bang", "💥", "knock", [460, 430, 428, 463, 464, 437]),
    "bounce":    ("Hüpfen/Ball", "Bouncing/ball", "⚽", "knock", [465, 459]),
    "hammer":    ("Hämmern", "Hammering", "🔨", "knock", [413, 414]),
    "steps":     ("Schritte", "Footsteps", "👣", "steps", [48, 46, 47]),
    "dishes":    ("Geschirr/Klappern", "Dishes/clatter", "🍽", "scrape", [358, 359, 483, 436, 435, 478, 489]),
    "kitchen":   ("Küche (Schneiden/Braten)", "Kitchen (chopping/frying)", "🍳", "noise", [360, 361, 484, 450]),
    "appliance": ("Küchengerät", "Kitchen appliance", "🔌", "noise", [362, 363]),
    "water":     ("Wasser/Spülung", "Water/flush", "🚿", "noise", [368, 364, 365, 366, 438, 439, 440, 442, 443, 444, 445, 446, 447]),
    "vacuum":    ("Staubsauger", "Vacuum cleaner", "🧹", "noise", [371]),
    "dryer":     ("Föhn", "Hair dryer", "💨", "noise", [367]),
    "drill":     ("Bohren/Werkzeug", "Drilling/tools", "🛠", "noise", [419, 418, 415, 416, 417, 412]),
    "furniture": ("Rücken/Schleifen", "Dragging/scraping", "🪑", "scrape", [469, 468, 470, 471, 472]),
    "fan":       ("Lüfter/Klima", "Fan/air conditioning", "🌀", "noise", [406, 407, 482, 490, 516, 517]),
    "speech":    ("Stimmen", "Voices", "🗣", "voice", [0, 1, 2, 3, 4, 63, 65, 12]),
    "shout":     ("Rufen/Schreien", "Shouting/screaming", "📢", "voice", [6, 7, 8, 9, 10, 11]),
    "laugh":     ("Lachen", "Laughter", "😄", "voice", [13, 15, 16, 17, 18]),
    "cry":       ("Weinen", "Crying", "😢", "voice", [19, 21, 22]),
    "baby":      ("Baby", "Baby", "👶", "voice", [20, 14]),
    "children":  ("Kinder spielen", "Children playing", "🧒", "voice", [66]),
    "party":     ("Feiern/Applaus", "Party/applause", "🎉", "voice", [61, 62, 64, 58]),
    "cough":     ("Husten/Niesen", "Cough/sneeze", "🤧", "voice", [42, 43, 44]),
    "snore":     ("Schnarchen", "Snoring", "😴", "voice", [38]),
    "singing":   ("Gesang", "Singing", "🎤", "tv", [24, 25, 29, 31, 32]),
    "bass":      ("Bass/Schlagzeug", "Bass/drums", "🥁", "tv", [137, 157, 158, 159, 160, 163, 238]),
    "music":     ("Musik", "Music", "🎵", "tv", list(range(132, 277))),
    "tv":        ("Fernseher/Radio", "TV/radio", "📺", "tv", [518, 519, 5]),
    "car":       ("Auto/Verkehr", "Car/traffic", "🚗", "noise", [300, 301, 308, 294, 321]),
    "horn":      ("Hupe/Autoalarm", "Horn/car alarm", "📯", "signal", [302, 304, 312]),
    "motorbike": ("Motorrad", "Motorcycle", "🏍", "noise", [320]),
    "truck":     ("Lkw/Bus", "Truck/bus", "🚚", "noise", [310, 311, 315]),
    "engine":    ("Motor", "Engine", "⚙", "noise", [337, 338, 342, 343, 345, 346, 347]),
    "siren":     ("Sirene", "Siren", "🚨", "signal", [316, 317, 318, 319, 390, 391]),
    "train":     ("Zug/Bahn", "Train/tram", "🚆", "noise", [323, 326, 327, 328, 322]),
    "aircraft":  ("Flugzeug", "Aircraft", "✈", "noise", [329, 330, 331, 332, 333]),
    "doorbell":  ("Türklingel", "Doorbell", "🔔", "signal", [349, 350]),
    "phone":     ("Telefon/Klingelton", "Phone/ringtone", "📱", "signal", [383, 384, 385]),
    "alarm":     ("Wecker/Alarm", "Alarm clock/alarm", "⏰", "signal", [382, 389, 392, 393, 394]),
    "beep":      ("Piepen", "Beeping", "📟", "signal", [475, 476, 477]),
    "dog":       ("Hund", "Dog", "🐕", "animal", [69, 70, 71, 72, 73, 74, 75]),
    "cat":       ("Katze", "Cat", "🐈", "animal", [76, 77, 78, 79, 80]),
    "bird":      ("Vögel", "Birds", "🐦", "animal", [106, 107, 108, 109, 110, 111, 112, 116]),
    "rain":      ("Regen/Gewitter", "Rain/thunder", "🌧", "noise", [283, 284, 285, 280, 281]),
    "wind":      ("Wind", "Wind", "🌬", "noise", [277, 278]),
}
FINE_MIN = 0.15          # Mindestsicherheit fuer einen Marker
# Stimm-Sicherung fuer die optionale Tonaufnahme: alle Klassen mit menschlicher Stimme (auch Gesang, TV/Radio).
# Streng: schon eine schwache Erkennung in einem einzigen Fenster verhindert das Speichern des Tons.
VOICE_CLASSES = sorted(set(sum((FINE[k][4] for k in ("speech", "shout", "laugh", "cry", "baby", "children", "party", "singing", "tv")), [])))
VOICE_GUARD_PCT = 8
_FIDX = None


def _fine_index():
    global _FIDX
    if _FIDX is None:
        keys = list(FINE)
        _FIDX = (keys, [np.asarray(FINE[k][4], int) for k in keys])
    return _FIDX


def fine_meta(lang="de"):
    """Feine Arten fuer die Oberflaeche: Schluessel -> Name, Symbol, Gruppe."""
    i = 0 if lang != "en" else 1
    out = {k: {"name": v[i], "icon": v[2], "group": v[3]} for k, v in FINE.items()}
    out["unknown"] = {"name": "Unbekannt" if lang != "en" else "Unknown", "icon": "❔", "group": "other"}   # Einzelereignis ohne erkannte Art
    return out


def analyse_full(x, max_patches=400, want_emb=False):
    """Wie analyse(), zusaetzlich je Fenster (0,975 s, Abstand 0,4875 s) die feinen Arten und auf Wunsch
    der 1024-stellige KI-Fingerabdruck (Embedding). Der Ton selbst wird nirgends gespeichert."""
    with _LOCK:
        net = _net()
        x = np.asarray(x, np.float32)
        if len(x) < 4000:
            raise ValueError("audio too short")
        if len(x) > (max_patches - 1) * yamnet_np.HOP + yamnet_np.PATCH:
            x = x[: (max_patches - 1) * yamnet_np.HOP + yamnet_np.PATCH]
        sc, emb = net.scores_emb(x, max_patches=max_patches)
    res = summarize(sc, x, net.names)
    res["patches"] = patch_marks(sc, x)
    # hoechster Stimmwert ueber alle Fenster (auch leise), roh und ungewichtet - fuer die Stimm-Sicherung
    res["voice_max"] = int(math.ceil(100 * float(sc[:, VOICE_CLASSES].max()))) if len(sc) else 100
    if want_emb:
        res["emb"] = emb
    return res


def summarize(sc, x, names):
    """Gruppen, Top-Klassen und Zeitverlauf aus den Fensterwerten (wie analyse())."""
    P = len(sc)
    hop, pl = yamnet_np.HOP, yamnet_np.PATCH
    w = np.ones(sc.shape[1], np.float32)
    for c, v in WEIGHT.items():
        w[c] = v
    sc = sc * w
    gs = {g: sc[:, idx].max(axis=1) for g, idx in GROUPS.items()}
    if x is not None and len(x):
        rms = np.array([float(np.sqrt(np.mean(x[i * hop:i * hop + pl] ** 2) + 1e-12)) for i in range(P)])
    else:
        rms = np.ones(P)
    loud = np.where(rms >= rms.max() * 0.5)[0]
    loud = loud[np.argsort(-rms[loud])][:4]
    gloud = {g: float(gs[g][loud].max()) for g in gs}
    best = max(gloud, key=gloud.get)
    art, conf = (best, gloud[best]) if gloud[best] >= MIN_SCORE else ("other", gloud[best])
    top_scores = sc[loud].max(axis=0)
    top = []
    for c in np.argsort(-top_scores)[:5]:
        if top_scores[c] < 0.03:
            break
        top.append({"name": names[c], "pct": int(round(100 * float(top_scores[c]))), "group": group_of(int(c))})
    return {"ok": True, "art": art, "conf": int(round(100 * conf)), "top": top,
            "groups": {g: int(round(100 * v)) for g, v in sorted(gloud.items(), key=lambda kv: -kv[1])},
            "seconds": round((len(x) if x is not None else 0) / 16000.0, 1)}


def patch_marks(sc, x=None):
    """Je Fenster die staerkste feine Art (oder None) mit Sicherheit in %. Leise Fenster (25 dB unter dem
    lautesten) bekommen keinen Marker, damit Stille nicht beschriftet wird."""
    keys, idx = _fine_index()
    P = len(sc)
    hop, pl = yamnet_np.HOP, yamnet_np.PATCH
    if x is not None and len(x):
        lv = np.array([20 * math.log10(float(np.sqrt(np.mean(x[i * hop:i * hop + pl] ** 2) + 1e-12))) for i in range(P)])
        loud = lv >= lv.max() - 25
    else:
        loud = np.ones(P, bool)
    fs = np.stack([sc[:, ix].max(axis=1) for ix in idx], axis=1)      # (P, Arten)
    out = []
    for i in range(P):
        j = int(np.argmax(fs[i])); v = float(fs[i, j])
        out.append([keys[j], int(round(100 * v))] if (loud[i] and v >= FINE_MIN) else None)
    return out


def scores_from_emb(emb):
    """Klassenwerte aus gespeicherten Fingerabdruecken (letzte Schicht von YAMNet) - fuer die Neubewertung ohne Ton."""
    with _LOCK:
        net = _net()
        x = np.asarray(emb, np.float32) @ net.w["fc_k"] + net.w["fc_b"]
        names = net.names
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30))), names
