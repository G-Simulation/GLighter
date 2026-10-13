#!/usr/bin/env python3
"""Laermprotokoll / Noise Log - Home Assistant Add-on (v1.7)

Quellen: Server-Mikrofon (PulseAudio/ALSA), Handys im Browser (HTTPS-Port, Audio per POST),
Netzwerk-Streams (ffmpeg, z. B. Android-App "IP Webcam"). Jede Quelle hat einen eigenen Thread.

Ablauf je Quelle:
  Audio -> 100-ms-Bloecke -> 20-ms-Frames -> Pegel
  -> Hintergrund (Median/Ruhepegel ueber Fenster, asymmetrisch geglaettet)
  -> Schwelle (fest / dynamisch / dynamisch mit Grenzen) -> Ereignis -> log.csv + WAV
Live-Daten liegen nur im Arbeitsspeicher (Ringpuffer, 10 Minuten).
"""
import urllib.parse
import urllib.error
import io
import warnings
import zlib
import base64, collections, csv, datetime as dt, glob, gzip, hashlib, hmac, json, math, mimetypes, os, re, secrets, select, shutil, signal, socket, ssl, struct, subprocess, sys, threading, time, urllib.request, wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import queue
import itertools
try:
    from scipy import signal as sps          # fuer den Brummfilter
except Exception:                            # pragma: no cover
    sps = None

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
OPTIONS_FILE = os.environ.get("LAERM_OPTIONS", "/data/options.json")
SETTINGS_FILE = os.environ.get("LAERM_SETTINGS", "/data/settings.json")
VERSION = "1.46.0"

# =====================================================================
# Einstellungen
# =====================================================================
DEFAULTS = {
    "device": "default", "mic_volume": 100, "sample_rate": 16000,
    "thr_mode": "bounded", "offset_db": 10, "thr_fixed_db": -60, "min_db": -95, "thr_max_db": -30,
    "bg_window": 60, "bg_unit": "s", "bg_stat": "quiet", "rise_s": 300, "fall_s": 10, "min_event_ms": 0,
    "pre_roll_s": 5, "post_roll_s": 5, "max_clip_s": 60, "ctx_s": 30, "save_audio": False, "audio_novoice": True,
    "day_track": True, "day_layers": True, "day_spec": True, "co_record": True, "fp_store": True,
    "group_pause_s": 120, "fn_assign_min": 5,
    "auto_delete": False, "retention_days": 90,
    "active_from": "", "active_to": "", "mqtt": True, "output_dir": "/share/laerm", "language": "auto",
    "mic_port": "", "classify": True, "ki_embed": False,
    "clip_dir": "", "video_width": 640, "video_fps": 5, "video_crf": 30,
    "quiet_from": "22:00", "quiet_to": "06:00", "quiet_sunday": True,
}
SPEC = {
    # ("num", min, max, Aufloesung): Kommazahlen, auf die Aufloesung gerundet
    "device": ("str",), "mic_volume": ("int", 0, 400), "sample_rate": ("choice", [16000, 22050, 44100, 48000]),
    "thr_mode": ("choice", ["fixed", "dynamic", "bounded"]), "offset_db": ("num", 0.5, 40, 0.1),
    "thr_fixed_db": ("num", -120, 0, 0.1), "min_db": ("num", -120, -10, 0.1), "thr_max_db": ("num", -120, 0, 0.1),
    "bg_window": ("int", 1, 3600), "bg_unit": ("choice", ["s", "min"]), "bg_stat": ("choice", ["median", "quiet", "min", "mean", "max"]),
    "rise_s": ("num", 0.5, 3600, 0.5), "fall_s": ("num", 0.5, 3600, 0.5), "min_event_ms": ("int", 0, 2000),
    "pre_roll_s": ("num", 0, 30, 0.1), "post_roll_s": ("num", 0.1, 60, 0.1), "max_clip_s": ("num", 1, 300, 0.5),
    "ctx_s": ("int", 0, 120), "day_track": ("bool",), "day_layers": ("bool",), "day_spec": ("bool",), "co_record": ("bool",), "fp_store": ("bool",), "group_pause_s": ("int", 10, 3600), "fn_assign_min": ("int", 0, 60), "save_audio": ("bool",), "audio_novoice": ("bool",), "auto_delete": ("bool",), "retention_days": ("int", 1, 3650),
    "active_from": ("time",), "active_to": ("time",), "mqtt": ("bool",), "output_dir": ("str",),
    "language": ("choice", ["auto", "de", "en"]), "mic_port": ("optstr",), "classify": ("bool",), "ki_embed": ("bool",),
    "clip_dir": ("optstr",), "video_width": ("int", 0, 3840), "video_fps": ("int", 1, 30), "video_crf": ("int", 18, 40),
    "quiet_from": ("time",), "quiet_to": ("time",), "quiet_sunday": ("bool",),
}
# Diese Werte erfordern einen Neustart der Aufnahme
RESTART_KEYS = {"device", "sample_rate"}
# Diese Werte setzen den gelernten Hintergrund zurueck
RELEARN_KEYS = {"bg_window", "bg_unit", "bg_stat"}
# Diese Werte koennen pro Geraet (Quelle) eigen eingestellt werden
PER_KEYS = ["thr_mode", "offset_db", "thr_fixed_db", "min_db", "thr_max_db", "bg_window", "bg_unit", "bg_stat",
            "rise_s", "fall_s", "min_event_ms", "pre_roll_s", "post_roll_s", "max_clip_s",
            "active_from", "active_to", "save_audio", "audio_novoice", "day_track", "day_layers", "day_spec", "fp_store"]

CFG = {}
CFG_META = {}
CFG_LOCK = threading.Lock()
MAX_BG_S = 7200   # Hintergrundfenster hoechstens 2 Stunden
RESTART = threading.Event()
RELEARN = threading.Event()


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def clean(key, value):
    """Wert pruefen und in den erlaubten Bereich bringen. None = ungueltig."""
    spec = SPEC.get(key)
    if spec is None:
        return None
    kind = spec[0]
    try:
        if kind == "int":
            if isinstance(value, bool):
                return None
            return max(spec[1], min(spec[2], int(round(float(value)))))
        if kind == "num":
            if isinstance(value, bool):
                return None
            v = float(str(value).strip().replace(",", "."))
            if not math.isfinite(v):
                return None
            st = spec[3]
            v = round(round(v / st) * st, 3)
            v = max(spec[1], min(spec[2], v))
            return int(v) if float(v).is_integer() else v
        if kind == "bool":
            if isinstance(value, bool):
                return value
            v = str(value).strip().lower()
            if v in ("true", "on", "1", "yes"):
                return True
            if v in ("false", "off", "0", "no"):
                return False
            return None
        if kind == "choice":
            for c in spec[1]:
                if str(c) == str(value):
                    return c
            return None
        if kind == "time":
            v = str(value or "").strip()
            if v == "":
                return ""
            m = re.fullmatch(r"(\d{1,2}):(\d{2})(:\d{2})?", v)
            if m and int(m.group(1)) < 24 and int(m.group(2)) < 60:
                return f"{int(m.group(1)):02d}:{m.group(2)}"
            return None
        if kind == "str":
            v = str(value).strip()
            return v[:300] if v else None
        if kind == "optstr":
            return re.sub(r"[\x00-\x1f]", "", str(value or "")).strip()[:120]
    except (TypeError, ValueError, OverflowError):
        return None
    return None


def merge(target, src):
    for k, v in src.items():
        c = clean(k, v)
        if c is not None:
            target[k] = c


def opts_hash(o):
    # 10 und 10.0 gelten als gleich (Home Assistant speichert Kommazahl-Felder als 10.0)
    norm = {k: (int(v) if isinstance(v, float) and v.is_integer() else v) for k, v in (o or {}).items()}
    return hashlib.sha1(json.dumps(norm, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def normalize(cfg):
    if cfg["bg_unit"] == "min" and cfg["bg_window"] > MAX_BG_S // 60:
        cfg["bg_window"] = MAX_BG_S // 60
    if cfg["thr_max_db"] <= cfg["min_db"]:
        cfg["thr_max_db"] = min(0, round(cfg["min_db"] + 1, 1))
    return cfg


def load_settings():
    """Reihenfolge: Standardwerte -> Add-on-Konfiguration -> Werte aus der Oberflaeche.
    Die Oberflaechenwerte gelten, solange die Add-on-Konfiguration seit dem letzten Speichern
    nicht veraendert wurde (Pruefsumme). Wurde der Reiter Konfiguration geaendert, gewinnt er."""
    cfg = dict(DEFAULTS)
    opts = read_json(OPTIONS_FILE)
    sets = read_json(SETTINGS_FILE)
    merge(cfg, opts)
    h = opts_hash(opts)
    if sets.get("_opts") == h:
        merge(cfg, sets)
    elif sets and "_opts" not in sets:                      # Datei aus Version 1.5
        try:
            newer = os.path.getmtime(SETTINGS_FILE) >= os.path.getmtime(OPTIONS_FILE)
        except OSError:
            newer = True
        if newer:
            merge(cfg, sets)
    elif sets:
        log("Add-on-Konfiguration wurde geaendert, sie hat Vorrang vor den Werten aus der Oberflaeche")
    migrated = False
    # Migration bis 1.4: Mindestschwelle -60 blockierte die dynamische Schwelle
    if cfg["min_db"] == -60 and not sets.get("_migrated_150") and "_v" not in sets:
        cfg["min_db"] = DEFAULTS["min_db"]; migrated = True
        log("Migration: Untergrenze -60 -> %s dBFS" % cfg["min_db"])
    # Migration bis 1.5: eigenes Hintergrund-Zeitfenster uebernehmen
    if "bg_window" not in opts and "bg_window" not in sets:
        bm = sets.get("baseline_minutes", opts.get("baseline_minutes"))
        if isinstance(bm, (int, float)) and int(bm) != 10:
            cfg.update(bg_window=int(bm), bg_unit="min", bg_stat="median"); migrated = True
            log(f"Migration: Hintergrund-Zeitfenster {int(bm)} min uebernommen")
    normalize(cfg)
    CFG_META["opts_hash"] = h
    if migrated or sets.get("_v") != VERSION:
        CFG.update(cfg)
        ok = push_supervisor(cfg, list(DEFAULTS)) if migrated else False
        persist(cfg)
        if migrated and not ok:
            log("Hinweis: migrierte Werte gelten, erscheinen aber erst nach dem Speichern in der Oberflaeche im Reiter Konfiguration")
    return cfg


def push_supervisor(cfg, keys):
    """Geaenderte Werte in die Add-on-Konfiguration von Home Assistant uebernehmen (Reiter Konfiguration).
    Liest vorher die aktuelle Konfiguration, damit dort gemachte Aenderungen nicht ueberschrieben werden."""
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        return False
    hdr = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with urllib.request.urlopen(urllib.request.Request("http://supervisor/addons/self/info", headers=hdr), timeout=8) as r:
            cur = json.load(r).get("data", {}).get("options", {}) or {}
        body = dict(cur)
        for k in keys:
            body[k] = cfg[k]
        req = urllib.request.Request("http://supervisor/addons/self/options", method="POST",
                                     data=json.dumps({"options": body}).encode(), headers=hdr)
        with urllib.request.urlopen(req, timeout=8) as r:
            ok = r.status == 200
        if ok:
            CFG_META["opts_hash"] = opts_hash(body)
        return ok
    except Exception as e:
        log("Hinweis: Add-on-Konfiguration nicht aktualisiert:", e)
        return False


PERSIST_LOCK = threading.Lock()


def persist(cfg):
    data = {k: cfg[k] for k in DEFAULTS}
    data["_v"] = VERSION
    data["_opts"] = CFG_META.get("opts_hash", "")
    with PERSIST_LOCK:
        try:
            tmp = SETTINGS_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(data, f, indent=1)
            os.replace(tmp, SETTINGS_FILE)
        except OSError as e:
            log("Einstellungen konnten nicht gespeichert werden:", e)


def public_settings():
    return {k: CFG[k] for k in DEFAULTS}


def parse_t(s):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", s or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


# Aufzeichnung starten/stoppen (Taste in der Oberflaeche, MQTT-Schalter). Bleibt ueber Neustarts erhalten.
RUN_FILE = os.path.join(os.path.dirname(SETTINGS_FILE) or ".", "state.json")
RUN = {"paused": False, "since": None, "force": False, "until": None, "reason": "", "by": ""}   # force: manuell ausserhalb der Erfassungszeit (nur im Speicher); until: Pause endet automatisch
RUN_LOCK = threading.Lock()
FORCE = set()        # Geraete (Quellen-IDs), die gerade manuell ausserhalb der Erfassungszeit erfassen


def load_run():
    d = read_json(RUN_FILE)
    RUN["paused"] = d.get("paused") is True
    RUN["since"] = d.get("since") if isinstance(d.get("since"), str) else None
    RUN["until"] = d.get("until") if isinstance(d.get("until"), str) and RUN["paused"] else None
    RUN["reason"] = str(d.get("reason") or "")[:80] if RUN["paused"] else ""
    RUN["by"] = str(d.get("by") or "")[:80] if RUN["paused"] else ""


def save_run():
    try:
        tmp = RUN_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump({k: RUN.get(k) for k in ("paused", "since", "until", "reason", "by")}, f); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, RUN_FILE)
    except OSError as e:
        log("Hinweis: Zustand nicht gespeichert:", e)


def set_recording(on, by="UI"):
    """on=True: Aufzeichnung laeuft, False: gestoppt. Jede Aenderung wird in aufzeichnung.csv protokolliert."""
    with RUN_LOCK:
        if RUN["paused"] == (not on):
            return False
        RUN["paused"] = not on
        RUN["by"] = "" if on else str(by)
        RUN["since"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        if on:
            RUN["until"] = None; RUN["reason"] = ""
        save_run()
        try:
            out = paths()[0]
            os.makedirs(out, exist_ok=True)
            f = os.path.join(out, "aufzeichnung.csv")
            new = not os.path.exists(f)
            with open(f, "a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if new:
                    w.writerow(["zeit", "aktion", "durch"])
                w.writerow([RUN["since"], "gestartet" if on else "gestoppt", by])
        except OSError as e:
            log("Hinweis: aufzeichnung.csv nicht geschrieben:", e)
    log("Aufzeichnung", "GESTARTET" if on else "GESTOPPT", f"({by})")
    pub(f"{TOPIC}/recording", "ON" if on else "OFF", True)
    pub_pause()
    return True


def pause_for(minutes, by="Home Assistant", reason=""):
    """Aufzeichnung fuer eine Zeit anhalten, danach automatisch fortsetzen. 0 = sofort fortsetzen.
    Ein von Hand (ohne Ende) gestoppte Aufzeichnung wird nicht automatisch wieder gestartet."""
    reason = re.sub(r"[\x00-\x1f]", "", str(reason or "")).strip()[:80]
    try:
        minutes = float(minutes)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(minutes):
        return False
    if minutes <= 0:                                   # fortsetzen: Pause mit Ende oder von Home Assistant gestoppt (nicht von Hand ohne Ende)
        if RUN["paused"] and (RUN["until"] or str(RUN.get("by") or "").startswith("Home Assistant") or by != "Home Assistant"):
            set_recording(True, by + (": " + reason if reason else ""))
        return True
    minutes = min(minutes, 24 * 60)
    if RUN["paused"] and not RUN["until"]:
        log("Pause aus Home Assistant ignoriert: Aufzeichnung ist bereits von Hand gestoppt")
        return False
    until = dt.datetime.now().astimezone() + dt.timedelta(minutes=minutes)
    with RUN_LOCK:
        RUN["until"] = until.isoformat(timespec="seconds"); RUN["reason"] = reason
    if not set_recording(False, f"{by} (Pause {minutes:g} min" + (f": {reason}" if reason else "") + ")"):
        save_run(); pub_pause()                       # laufende Pause verlaengern/verkuerzen
        log(f"Pause geaendert: bis {until:%H:%M:%S}" + (f" ({reason})" if reason else ""))
    return True


def pause_left_min():
    if not (RUN["paused"] and RUN["until"]):
        return 0
    try:
        return max(0, math.ceil((dt.datetime.fromisoformat(RUN["until"]) - dt.datetime.now().astimezone()).total_seconds() / 60))
    except ValueError:
        return 0


def pub_pause():
    pub(f"{TOPIC}/pause", json.dumps({"until": RUN["until"] if RUN["paused"] else None, "reason": RUN["reason"], "minutes": pause_left_min()}), True)


def pause_watch():
    """Zeitlich begrenzte Pause beenden; Restzeit regelmaessig melden."""
    n = 0
    while True:
        time.sleep(5); n += 1
        try:
            if RUN["paused"] and RUN["until"]:
                if dt.datetime.fromisoformat(RUN["until"]) <= dt.datetime.now().astimezone():
                    set_recording(True, "automatisch nach Pause")
                elif n % 12 == 0:
                    pub_pause()
        except Exception as e:
            log("Pause-Ueberwachung:", e)


def in_hours(now, cfg=None):
    cfg = cfg or CFG
    a, b = parse_t(cfg["active_from"]), parse_t(cfg["active_to"])
    if a is None or b is None or a == b:
        return True
    m = now.hour * 60 + now.minute
    return a <= m < b if a < b else (m >= a or m < b)


def safe_dir(p):
    p = (p or "").strip().rstrip("/")
    return p if p.startswith("/") and ".." not in p.split("/") and len(p) > 1 else ""


def paths():
    out = (CFG["output_dir"] or "/share/laerm").rstrip("/")
    return out, safe_dir(CFG.get("clip_dir")) or out + "/clips", out + "/log.csv"


# =====================================================================
# Audio
# =====================================================================
def run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def list_sources():
    code, out = run(["pactl", "list", "sources", "short"])
    src = []
    if code == 0:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and not parts[1].endswith(".monitor"):
                src.append({"name": parts[1], "state": parts[-1].strip() if len(parts) > 4 else ""})
    code, default = run(["pactl", "get-default-source"])
    return src, default.strip() if code == 0 else ""


def source_details():
    """Pulse-Quellen mit Buchsen (Ports): [{name, desc, mute, volume, ports:[{name, desc, avail}], active}]"""
    code, out = run(["pactl", "list", "sources"])
    res, cur, in_ports = [], None, False
    if code != 0:
        return res
    for line in out.splitlines():
        s = line.strip()
        if line.startswith("Source #"):
            cur = {"name": "", "desc": "", "mute": False, "volume": "", "ports": [], "active": ""}; res.append(cur); in_ports = False
            continue
        if cur is None:
            continue
        if s.startswith("Name:"):
            cur["name"] = s[5:].strip()
        elif s.startswith("Description:"):
            cur["desc"] = s[12:].strip()
        elif s.startswith("Mute:"):
            cur["mute"] = s[5:].strip().lower() in ("yes", "ja")
        elif s.startswith("Volume:") and not cur["volume"]:
            m = re.search(r"(\d+)%", s); cur["volume"] = m.group(1) + "%" if m else ""
        elif s.startswith("Ports:"):
            in_ports = True
        elif s.startswith("Active Port:"):
            cur["active"] = s[12:].strip(); in_ports = False
        elif in_ports and line.startswith("\t\t") and ":" in s:
            pn, _, rest = s.partition(":")
            m = re.match(r"\s*(.*?)\s*\(", rest)
            cur["ports"].append({"name": pn.strip(), "desc": (m.group(1) if m else rest).strip()[:60],
                                 "avail": "not available" not in rest})
        elif in_ports and not line.startswith("\t\t"):
            in_ports = False
    return [x for x in res if x["name"] and not x["name"].endswith(".monitor")]


def describe_sources():
    code, out = run(["pactl", "list", "sources"])
    if code != 0:
        return "pactl: " + out.strip()
    keep, skip = [], False
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("Source #"):
            skip = False; keep.append(s)
        elif s.startswith("Name:"):
            skip = s.endswith(".monitor")
            if skip:
                keep.pop()
            else:
                keep.append("   " + s)
        elif not skip and s.startswith(("Description:", "State:", "Mute:", "Volume:", "Sample Specification:", "Active Port:")):
            keep.append("   " + s)
    return "\n".join(keep) or "(keine Quellen / no sources)"


def is_pulse_source(dev):
    return dev not in ("default", "pulse") and ":" not in dev and not dev.startswith(("hw", "plughw", "sysdefault", "dsnoop"))


def usb_cards():
    """Nummern der USB-Soundkarten. /proc/asound ist im Container verdeckt, daher ueber /dev/snd/controlC*
    und "amixer -c N info" (bzw. /sys/class/sound) erkennen."""
    out = []
    for dev in sorted(glob.glob("/dev/snd/controlC*")):
        m = re.search(r"controlC(\d+)$", dev)
        if not m:
            continue
        n = int(m.group(1))
        usb = False
        try:
            usb = "usb" in os.path.realpath(f"/sys/class/sound/card{n}/device").lower()
        except OSError:
            pass
        if not usb:
            code, info = run(["amixer", "-c", str(n), "info"])
            usb = code == 0 and "usb" in info.lower()
        if usb:
            out.append(n)
    if not out:                                   # Testumgebung / Fallback
        try:
            with open(os.environ.get("LAERM_ASOUND_CARDS", "/proc/asound/cards")) as f:
                for line in f:
                    m = re.match(r"\s*(\d+)\s+\[([^\]]*)\]:\s*(.*)", line)
                    if m and ("usb" in m.group(3).lower() or "usb" in m.group(2).lower()):
                        out.append(int(m.group(1)))
        except OSError:
            pass
    return out


def mixer_controls(card):
    """Einfache ALSA-Regler einer Karte: {name: {"cap": bool (Aufnahme), "vol": bool, "sw": bool, "val": str}}"""
    code, out = run(["amixer", "-c", str(card), "scontents"])
    ctl, cur = {}, None
    if code != 0:
        return None, out.strip()[:200]
    for line in out.splitlines():
        m = re.match(r"Simple mixer control '([^']+)',\d+", line)
        if m:
            cur = ctl.setdefault(m.group(1), {"cap": False, "vol": False, "sw": False, "val": ""}); continue
        if cur is None:
            continue
        s = line.strip()
        if s.startswith("Capabilities:"):
            caps = s.split(":", 1)[1].split()
            cur["cap"] = any(c in caps for c in ("cvolume", "cswitch", "cvolume-joined", "cswitch-joined"))
            cur["vol"] = any(c in caps for c in ("cvolume", "cvolume-joined"))
            cur["sw"] = any(c in caps for c in ("cswitch", "cswitch-joined"))
            if any(c == "pswitch" or c == "pswitch-joined" for c in caps) and not cur["cap"]:
                cur["pswitch"] = True
        elif re.match(r"(Mono|Front Left|Front Right|Capture)\b", s) and "[" in s and not cur["val"]:
            cur["val"] = " ".join(re.findall(r"\[([^\]]+)\]", s))
    return ctl, ""


def apply_mixer(vol):
    """Aufnahmeregler der USB-Soundkarte direkt stellen (Home Assistant tut das bei "mono-fallback" nicht):
    Mikrofon-Aufnahme an, Pegel = Empfindlichkeit (max. 100 %), automatische Verstaerkung aus
    (sonst schwanken die gemessenen Pegel)."""
    res = []
    for card in usb_cards():
        ctl, err = mixer_controls(card)
        if ctl is None:
            res.append(f"Karte {card}: Regler nicht erreichbar ({err})")
            continue
        for name, c in ctl.items():
            if c["cap"] and (c["vol"] or c["sw"]):
                args = ["amixer", "-q", "-c", str(card), "sset", name]
                if c["vol"]:
                    args += ["capture", f"{max(0, min(100, vol))}%"]
                if c["sw"]:
                    args += ["cap"]
                code, out = run(args)
                res.append(f"Karte {card} '{name}': Aufnahme {min(100, vol)}%" + ("" if code == 0 else f" fehlgeschlagen ({out.strip()[:80]})"))
            elif name.lower().startswith("auto gain"):
                code, out = run(["amixer", "-q", "-c", str(card), "sset", name, "off"])
                res.append(f"Karte {card} '{name}': aus" + ("" if code == 0 else " fehlgeschlagen"))
    if res:
        log("Soundkarte:", "; ".join(res))
    return res


def apply_volume():
    dev = CFG["device"]
    target = dev if is_pulse_source(dev) else "@DEFAULT_SOURCE@"
    port = CFG.get("mic_port") or ""
    if port:
        code, out = run(["pactl", "set-source-port", target, port])
        log(f"Eingang (Buchse) {port} -> {target}" + ("" if code == 0 else f" (fehlgeschlagen: {out.strip()})"))
    vol = CFG["mic_volume"]
    if vol <= 0:
        return
    # Erst Home Assistant (PulseAudio), dann der Regler auf der Karte: PulseAudio stellt beim Setzen seiner
    # Lautstaerke den Kartenregler teilweise selbst mit. Daher zuletzt den Kartenregler auf den gewuenschten Wert.
    run(["pactl", "set-source-mute", target, "0"])
    pv = max(100, vol)                                 # bis 100 % nur der Kartenregler, darueber digital
    code, out = run(["pactl", "set-source-volume", target, f"{pv}%"])
    log(f"Mikrofon-Lautstaerke {vol}% (digital {pv}%) -> {target}" + ("" if code == 0 else f" (fehlgeschlagen: {out.strip()})"))
    time.sleep(0.3)
    apply_mixer(vol)                                   # Regler auf der Soundkarte (bis 100 %), darueber digital
    DIAG["t"] = 0                                      # Diagnose sofort neu einlesen




def local_cmd(rate):
    dev = CFG["device"]
    if is_pulse_source(dev):
        return ["parec", f"--device={dev}", "--format=s16le", f"--rate={rate}", "--channels=1", "--raw", "--latency-msec=50"]
    return ["arecord", "-q", "-D", dev, "-f", "S16_LE", "-r", str(rate), "-c", "1", "-t", "raw"]


def fix_url(u):
    """Stream-Adresse vereinheitlichen: Protokoll klein (ffmpeg kennt "Https" nicht), bei IP Webcam
    (Port 8080) ohne Pfad automatisch /audio.wav anhaengen."""
    u = str(u or "").strip()
    if u and "://" not in u and re.match(r"^[\w.-]+(:\d+)?(/.*)?$", u):
        u = "http://" + u                                   # "192.168.1.5:8080" -> http://...
    m = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*)://(.*)$", u)
    if not m:
        return u
    scheme, rest = m.group(1).lower(), m.group(2)
    # Zugangsdaten (name:passwort@) im Host-Teil sicher kodieren (z. B. @ oder : im Passwort).
    # Passwoerter mit / ? # gehoeren in die Login-Felder, in der Adresse waeren sie mehrdeutig.
    auth = re.split(r"[/?#]", rest, maxsplit=1)[0]
    if "@" in auth:
        k = auth.rfind("@")
        user, sep, pw = auth[:k].partition(":")
        q = lambda x: urllib.parse.quote(re.sub(r"%(?![0-9A-Fa-f]{2})", "%25", x), safe="%!$&'()*+,;=-._~")
        rest = q(user) + (":" + q(pw) if sep else "") + auth[k:] + rest[len(auth):]
    if scheme in ("http", "https"):
        hostport, _, path = rest.partition("/")
        if path == "" and hostport.rsplit("@", 1)[-1].endswith(":8080"):
            rest = hostport + "/audio.wav"                   # IP Webcam: Ton-Adresse, nur http
            scheme = "http"
    return scheme + "://" + rest


def friendly_error(msg):
    """ffmpeg-Fehlermeldungen um einen verstaendlichen Hinweis ergaenzen."""
    de = CFG.get("language") != "en"
    low = msg.lower()
    hints = [
        (("protocol not found",), "Adresse muss mit http:// beginnen (IP Webcam: http://HANDY-IP:8080/audio.wav)",
         "Address must start with http:// (IP Webcam: http://PHONE-IP:8080/audio.wav)"),
        (("connection refused",), "Handy nicht erreichbar: läuft in IP Webcam „Server starten“? IP und Port prüfen",
         "Phone not reachable: is IP Webcam's server started? Check IP and port"),
        (("timed out", "no route to host", "network is unreachable", "keine audiodaten"), "Keine Verbindung: Handy im selben WLAN, eingeschaltet, App läuft?",
         "No connection: phone on the same Wi-Fi, switched on, app running?"),
        (("404", "not found"), "Pfad falsch: bei IP Webcam /audio.wav anhängen",
         "Wrong path: for IP Webcam append /audio.wav"),
        (("ssl", "tls handshake", "certificate"), "Verschlüsselung klappt nicht: http:// statt https:// verwenden",
         "Encryption failed: use http:// instead of https://"),
        (("401", "unauthorized"), "Benutzername/Passwort falsch oder fehlt: in der Karte unter „Login“ eintragen (wie in IP Webcam eingestellt)",
         "Username/password wrong or missing: enter them under “Login” in the card (as set in IP Webcam)"),
        (("invalid data",), "Unter der Adresse kommt kein Ton: bei IP Webcam /audio.wav verwenden",
         "No audio at this address: for IP Webcam use /audio.wav"),
    ]
    for keys, h_de, h_en in hints:
        if any(k in low for k in keys):
            return (h_de if de else h_en) + "  (" + msg[:200] + ")"
    return msg


def url_cmd(url, rate, user="", pw=""):
    """ffmpeg liest Netzwerk-Audio (z. B. Android-App „IP Webcam“: http://HANDY:8080/audio.wav, RTSP, Icecast)."""
    url = with_login(fix_url(url), user, pw)
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error"]
    low = url.lower()
    if low.startswith(("http://", "https://")):
        cmd += ["-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5", "-rw_timeout", "8000000"]
    elif low.startswith("rtsp://"):
        cmd += ["-rtsp_transport", "tcp", "-timeout", "8000000"]
    cmd += ["-probesize", "65536", "-analyzeduration", "1000000", "-fflags", "nobuffer",
            "-i", url, "-vn", "-f", "s16le", "-ac", "1", "-ar", str(rate), "-"]
    return cmd


def pipe_blocks(cmd, block, runner):
    """Startet einen Rekorder-Prozess und liefert 100-ms-Bloecke. Haengt er (kein Ton fuer 3 s),
    wird er beendet; stderr wird laufend in einem eigenen Thread geleert (sonst blockiert der Prozess)."""
    shown = ["<url>" if i and cmd[i - 1] == "-i" else c for i, c in enumerate(cmd)]   # URL kann Passwoerter enthalten
    log(f"[{runner.name}] Aufnahme:", " ".join(shown))
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    except FileNotFoundError as e:
        runner.status["error"] = f"Programm fehlt: {e.filename}"
        log(f"[{runner.name}] Programm fehlt:", e.filename)
        return
    tail = collections.deque(maxlen=20)

    def drain():
        try:
            for line in iter(p.stderr.readline, b""):
                txt = line.decode(errors="replace").strip()
                if txt:
                    tail.append(re.sub(r"//[^/\s]*@", "//***@", txt))     # Zugangsdaten sofort entfernen
        except Exception:
            pass
    threading.Thread(target=drain, daemon=True).start()
    size = block * 2
    fd = p.stdout.fileno()
    first = True
    try:
        while not runner.interrupted():
            buf = bytearray()
            deadline = time.monotonic() + (15.0 if first else 3.0)   # Streams brauchen fuer den Start laenger
            while len(buf) < size and not runner.interrupted():
                r, _, _ = select.select([fd], [], [], 0.5)
                if not r:
                    if time.monotonic() > deadline:
                        break
                    continue
                chunk = os.read(fd, size - len(buf))
                if not chunk:
                    break
                buf += chunk
            if runner.interrupted():
                return
            if len(buf) < size:
                time.sleep(0.3)
                code = p.poll()
                err = " | ".join(tail)[-400:]
                msg = err or (f"Aufnahme beendet (Code {code})" if code is not None else "Keine Audiodaten seit 3 s")
                msg = re.sub(r"//[^/\s]*@", "//***@", msg)          # Passwoerter aus URLs entfernen
                pw = runner.src.get("password")
                if pw:
                    for v in {pw, urllib.parse.quote(pw, safe="")}:
                        msg = msg.replace(v, "***")
                log(f"[{runner.name}] Aufnahmefehler:", msg)
                runner.status["error"] = friendly_error(msg) if runner.src.get("type") == "url" else msg
                return
            runner.status["error"] = ""
            first = False
            yield np.frombuffer(bytes(buf), dtype=np.int16).copy()
    finally:
        try:
            p.kill(); p.wait(timeout=2)
        except Exception:
            pass


RELAY_SOCK = os.environ.get("LAERM_RELAY", "")
RELAY_OPENED = set()          # Quellen, die in diesem Programmlauf schon einmal geoeffnet wurden
RELAY_POS_FILE = os.path.join(os.path.dirname(os.environ.get("LAERM_SOURCES", "/data/sources.json")) or "/data", "relay_pos.json")
RELAY_POS = {"d": None}


def relay_pos_take(sid):
    """Bis wohin das vorige Programm den Ton verarbeitet hat (nur direkt nach einem Neustart, einmal je Quelle)."""
    if RELAY_POS["d"] is None:
        try:
            with open(RELAY_POS_FILE) as fh:
                d = json.load(fh)
            os.remove(RELAY_POS_FILE)
        except (OSError, ValueError):
            d = {}
        RELAY_POS["d"] = {k: v for k, v in (d.items() if isinstance(d, dict) else []) if isinstance(v, list) and len(v) == 2 and time.time() - v[1] < 120}
    v = RELAY_POS["d"].pop(sid, None)
    return v[0] if v else None


def relay_pos_save(sid, ts):
    """Beim Beenden: letzter verarbeiteter Block (Zeit des Starters). Das naechste Programm bekommt alles danach."""
    try:
        with RELAY_POS_LOCK:
            try:
                with open(RELAY_POS_FILE) as fh:
                    d = json.load(fh)
            except (OSError, ValueError):
                d = {}
            d = d if isinstance(d, dict) else {}
            d[sid] = [ts, time.time()]
            with open(RELAY_POS_FILE + ".tmp", "w") as fh:
                json.dump(d, fh)
            os.replace(RELAY_POS_FILE + ".tmp", RELAY_POS_FILE)
    except OSError as e:
        log("Uebergabe-Stand nicht gespeichert:", e)


RELAY_POS_LOCK = threading.Lock()


def relay_on():
    return bool(RELAY_SOCK) and os.path.exists(RELAY_SOCK)


def relay_blocks(cmd, block, runner):
    """Wie pipe_blocks, aber der Rekorder laeuft im Starter (aufnahme.py) weiter, wenn dieses Programm neu startet.
    Beim ersten Oeffnen nach einem Neustart kommt zuerst der gepufferte Ton (mit seiner Aufnahmezeit), dann live."""
    shown = ["<url>" if i and cmd[i - 1] == "-i" else c for i, c in enumerate(cmd)]
    size = block * 2
    fresh = runner.id in RELAY_OPENED                 # erneutes Oeffnen im selben Lauf = neuer Rekorder (Einstellungen, Soundkarte)
    RELAY_OPENED.add(runner.id)
    since = None if fresh else relay_pos_take(runner.id)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(RELAY_SOCK)
        s.sendall((json.dumps({"sid": runner.id, "cmd": cmd, "block": size, "fresh": fresh, "since": since}) + "\n").encode())
    except OSError as e:
        log(f"[{runner.name}] Aufnahme-Relais nicht erreichbar:", e)
        s.close()
        yield from ((b, time.time()) for b in pipe_blocks(cmd, block, runner))
        return
    log(f"[{runner.name}] Aufnahme (ueber Starter{', neu' if fresh else ''}):", " ".join(shown))
    first = True
    kill = True
    try:
        buf = bytearray()
        while not runner.interrupted():
            deadline = time.monotonic() + (15.0 if first else 3.0)
            need = 12
            hdr = None
            while not runner.interrupted():
                while len(buf) < need:
                    r, _, _ = select.select([s], [], [], 0.5)
                    if runner.interrupted():
                        return
                    if not r:
                        if time.monotonic() > deadline:
                            raise TimeoutError("Keine Audiodaten seit 3 s")
                        continue
                    c = s.recv(65536)
                    if not c:
                        raise ConnectionError("Aufnahme-Relais getrennt")
                    buf += c
                if hdr is None:
                    ts, ln = struct.unpack("<dI", bytes(buf[:12])); del buf[:12]
                    if ln == 0xFFFFFFFF:                 # Rekorder beendet
                        while len(buf) < 4:
                            c = s.recv(65536)
                            if not c:
                                break
                            buf += c
                        ml = struct.unpack("<I", bytes(buf[:4]))[0] if len(buf) >= 4 else 0
                        while len(buf) < 4 + ml:
                            c = s.recv(65536)
                            if not c:
                                break
                            buf += c
                        msg = bytes(buf[4:4 + ml]).decode("utf-8", "replace")
                        kill = False
                        raise RuntimeError(msg or "Aufnahme beendet")
                    hdr = (ts, ln); need = ln
                    continue
                ts, ln = hdr
                data = bytes(buf[:ln]); del buf[:ln]
                break
            else:
                return
            runner.status["error"] = ""
            first = False
            if len(data) == size:
                yield np.frombuffer(data, dtype=np.int16).copy(), ts
    except (TimeoutError, ConnectionError, RuntimeError) as e:
        msg = re.sub(r"//[^/\s]*@", "//***@", str(e))
        pw = runner.src.get("password")
        if pw:
            for v in {pw, urllib.parse.quote(pw, safe="")}:
                msg = msg.replace(v, "***")
        log(f"[{runner.name}] Aufnahmefehler:", msg)
        runner.status["error"] = friendly_error(msg) if runner.src.get("type") == "url" else msg
    finally:
        try:
            if kill and runner.interrupted() and not runner.stop.is_set():
                s.sendall(b"K")                       # neue Einstellungen: Rekorder beenden, naechstes Oeffnen startet neu
            elif kill and not runner.interrupted():
                s.sendall(b"K")                       # haengt: beenden
        except OSError:
            pass
        s.close()


def ram_audio(r, t0=None, t1=None, sec=10):
    """Ton einer Quelle aus dem kurzen Arbeitsspeicher-Puffer (nur zur Auswertung durch die Erkennung, nie gespeichert
    oder abgespielt). Mit t0/t1 (ms): genau dieser Zeitraum, Luecken als Stille. Liefert (audio, start_ms)."""
    with r.hist_lock:
        h = list(r.hist)
        rate = r.hist_rate
    if not h:
        return np.zeros(0, np.int16), None
    if t0 is None or t1 is None:
        t1 = h[-1][0]; t0 = t1 - sec * 1000
    t1 = min(t1, t0 + BUF_SECONDS * 1000)
    sel = [(ts, b) for ts, b in h if t0 < ts <= t1 + 100]
    if not sel:
        return np.zeros(0, np.int16), None
    start = sel[0][0] - 100                     # Zeitstempel = Ende des Blocks
    parts, pos = [], start
    for ts, b in sel:
        gap = ts - 100 - pos
        if gap > 150:                            # Luecke (z. B. Handy getrennt): Stille einfuegen
            parts.append(np.zeros(int(gap * rate / 1000), np.int16))
        parts.append(b); pos = ts
    return np.concatenate(parts), start


class HumFilter:
    """Netzbrummen herausfiltern: schmale Kerbfilter bei 50 (bzw. 60) Hz und den Oberwellen bis 1 kHz.
    Je Kerbe nur wenige Hz breit, Klopfen und Stimmen bleiben praktisch unveraendert."""

    def __init__(self, base, rate):
        self.base, self.sos, self.zi = base, None, None
        if sps is None or base not in (50, 60):
            return
        secs = []
        for k in range(1, 21):
            f = base * k
            if f > 1000 or f >= rate * 0.45:
                break
            b, a = sps.iirnotch(f, 30.0, rate)
            secs.append(np.concatenate([b, a]))
        if secs:
            self.sos = np.array(secs)
            self.zi = np.zeros((len(secs), 2))

    def __call__(self, blk):
        if self.sos is None:
            return blk
        y, self.zi = sps.sosfilt(self.sos, blk.astype(np.float64), zi=self.zi)
        return np.clip(np.round(y), -32768, 32767).astype(np.int16)


def db(x):
    """RMS-Pegel in dBFS."""
    return 20.0 * np.log10(np.sqrt(np.mean(np.square(x.astype(np.float64) / 32768.0))) + 1e-9)


class Bands:
    """Logarithmische Frequenzbaender fuer das Spektrogramm."""
    N = 32

    def __init__(self, rate, block):
        hi = min(8000.0, rate / 2 - 1)
        edges = np.geomspace(50, hi, self.N + 1)
        freq = np.fft.rfftfreq(block, 1.0 / rate)
        self.win = np.hanning(block)
        self.k = 2.0 / (block ** 2 * 0.375)
        self.idx = []
        for lo, up in zip(edges[:-1], edges[1:]):
            sel = np.where((freq >= lo) & (freq < up))[0]
            if sel.size == 0:
                sel = np.array([int(np.argmin(np.abs(freq - (lo * up) ** 0.5)))])
            self.idx.append(sel)
        self.centers = [int(round((lo * up) ** 0.5)) for lo, up in zip(edges[:-1], edges[1:])]

    def __call__(self, x):
        sp = np.abs(np.fft.rfft(x.astype(np.float64) / 32768.0 * self.win)) ** 2 * self.k
        out = np.empty(self.N, dtype=np.uint8)
        for i, sel in enumerate(self.idx):
            d = 10 * np.log10(sp[sel].sum() + 1e-14)
            out[i] = int(max(0, min(255, round((d + 130) * 2))))   # 0.5-dB-Schritte, -130 ... -2.5 dB
        return out




# =====================================================================
# Quellen (Server-Mikrofon, Handy im Browser, Netzwerk-Stream)
# =====================================================================
SOURCES_FILE = os.environ.get("LAERM_SOURCES", "/data/sources.json")
DATA_DIR = os.path.dirname(SOURCES_FILE) or "/data"
REMOTE_RATE = 16000
SRC_TYPES = ("local", "phone", "url")
SRC_LOCK = threading.RLock()
RUNNERS = {}            # id -> Runner (Reihenfolge = Anzeige)
BOOT = int(time.time())  # erkennt Neustarts des Add-ons im Browser
BUF_SECONDS = 600
HIST_SECONDS = 60          # so lange liegt Ton im Arbeitsspeicher (danach ueberschrieben)


# =====================================================================
# GasLighter Pro: Lizenzschlüssel (offline geprüft, siehe lizenz.py)
# Pro schaltet frei: Import einer Sicherung (der erste Import ist kostenlos, z. B. für den Umzug),
# Erweiterte Einstellungen (Erkennung: Schwelle, Hintergrund, Anpassung) und externe Geräte (Handy, Stream).
# Aufzeichnung, Protokoll, Druck, Export und Sicherung erstellen bleiben immer frei.
# =====================================================================
import lizenz
PRO_FILE = os.path.join(DATA_DIR, "lizenz.json")
PRO_KEYS = {"thr_mode", "thr_fixed_db", "offset_db", "min_db", "thr_max_db", "bg_window", "bg_unit", "bg_stat",
            "rise_s", "fall_s", "min_event_ms"}
PRO_CACHE = {"t": 0.0, "st": None}
PRO_LOCK = threading.Lock()


def pro_file():
    try:
        with open(PRO_FILE) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def pro_write(d):
    tmp = PRO_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=1); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, PRO_FILE)
    PRO_CACHE["t"] = 0.0


def pro_state():
    with PRO_LOCK:
        if PRO_CACHE["st"] is not None and time.time() - PRO_CACHE["t"] < 60:
            return PRO_CACHE["st"]
        d = pro_file()
        st = lizenz.check(d.get("key"))
        st["free_import"] = not d.get("import_used")
        st["buy"] = lizenz.BUY_URL
        if d.get("key"):
            k = lizenz.normalize(d["key"])
            st["key_hint"] = "GL1-…" + k[-5:]
        PRO_CACHE.update(t=time.time(), st=st)
        return st


def pro_ok():
    return bool(pro_state().get("ok"))


def pro_set(key):
    r = lizenz.check(key)
    if r["state"] != "active":
        return {"ok": False, "error": r.get("state") if r["state"] == "expired" else (r.get("error") or "invalid"), "pro": pro_state()}
    d = pro_file(); d["key"] = str(key).strip(); d["set"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    pro_write(d)
    log("Pro-Lizenz eingetragen, gültig bis", r["until"], "(Bestellung", (r.get("order") or "-") + ")")
    with SRC_LOCK:
        for x in RUNNERS.values():
            if x.src["type"] != "local":
                x.restart.set()
    return {"ok": True, "pro": pro_state()}


def pro_del():
    d = pro_file()
    if d.pop("key", None) is not None:
        pro_write(d)
        log("Pro-Lizenz entfernt")
    return {"ok": True, "pro": pro_state()}


def pro_import_allowed():
    return pro_ok() or not pro_file().get("import_used")


def pro_import_mark():
    if pro_ok():
        return
    d = pro_file()
    if not d.get("import_used"):
        d["import_used"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        pro_write(d)
        log("Kostenloser Import genutzt (weitere Importe mit GasLighter Pro)")


def pro_strip(cfg):
    """Ohne Pro bleiben die erweiterten Einstellungen der Erkennung unverändert."""
    if isinstance(cfg, dict) and not pro_ok():
        for k in PRO_KEYS:
            cfg.pop(k, None)
    return cfg


def src_runs(src):
    """Darf diese Quelle aufnehmen? Externe Geräte (Handy, Stream) nur mit Pro."""
    return src.get("enabled", True) and (src.get("type") == "local" or pro_ok())


class Terz:
    """Terzbaender (IEC 61260, Basis 10) fuer die gespeicherte Laermspur: 125-ms-Rahmen, nur Pegelwerte.
    Aus dieser Aufloesung ist Sprache nicht verstaendlich zurueckzugewinnen (Gontier et al., Sensors 2017)."""
    STEP_MS = 125
    CENTERS = [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000]

    def __init__(self, rate):
        self.rate = rate
        self.n = int(round(rate * self.STEP_MS / 1000))
        self.sub = self.n // 5                                   # 5 x 25 ms fuer den Spitzenwert
        freq = np.fft.rfftfreq(self.n, 1.0 / rate)
        self.win = np.hanning(self.n)
        self.k = 2.0 / (self.n ** 2 * 0.375)
        self.idx = []
        for k in range(-13, 10):
            c = 1000 * 10 ** (k / 10); lo, up = c * 10 ** (-1 / 20), c * 10 ** (1 / 20)
            sel = np.where((freq >= lo) & (freq < up))[0]
            if sel.size == 0:
                sel = np.array([int(np.argmin(np.abs(freq - c)))])
            self.idx.append(sel)
        self.buf = np.zeros(0, np.int16)

    def feed(self, blk, end_ms):
        """Ton eines Blocks anhaengen; liefert fertige Rahmen [(Ende_ms, Spitze_dB, Mittel_dB, Baender_uint8)]."""
        self.buf = np.concatenate([self.buf, blk]) if len(self.buf) else blk.copy()
        out = []
        while len(self.buf) >= self.n:
            x = self.buf[:self.n]; self.buf = self.buf[self.n:]
            ts = end_ms - int(round(len(self.buf) * 1000 / self.rate))
            lmax = max(float(db(x[i * self.sub:(i + 1) * self.sub])) for i in range(5))
            sp = np.abs(np.fft.rfft(x.astype(np.float64) / 32768.0 * self.win)) ** 2 * self.k
            bands = np.empty(len(self.idx), dtype=np.uint8)
            for i, sel in enumerate(self.idx):
                d = 10 * np.log10(sp[sel].sum() + 1e-14)
                bands[i] = int(max(0, min(255, round((d + 130) * 2))))
            out.append((ts, round(lmax, 1), round(float(db(x)), 1), bands))
        return out


def default_name(kind, de=True):
    return {"local": "Server-Mikrofon" if de else "Server microphone", "phone": "Handy" if de else "Phone",
            "url": "Stream"}[kind]


# Zeitprofile: zu bestimmten Uhrzeiten andere Schwellen-Werte (allgemein oder pro Geraet)
SLOT_KEYS = ["thr_mode", "offset_db", "thr_fixed_db", "min_db", "thr_max_db", "min_event_ms", "bg_stat"]
SCHED_FILE = os.path.join(os.path.dirname(SETTINGS_FILE) or ".", "schedule.json")
SCHED = []
MAX_SLOTS = 12


def clean_slots(lst):
    """Liste von {"from": "22:00", "to": "06:00", "cfg": {...}} pruefen. Ungueltige Eintraege fallen weg."""
    out = []
    for d in (lst if isinstance(lst, list) else [])[:MAX_SLOTS]:
        if not isinstance(d, dict):
            continue
        a, b = clean("active_from", d.get("from")), clean("active_to", d.get("to"))
        if not a or not b or a == b:
            continue
        c = {}
        for k, v in (d.get("cfg") or {}).items() if isinstance(d.get("cfg"), dict) else []:
            if k in SLOT_KEYS:
                x = clean(k, v)
                if x is not None:
                    c[k] = x
        out.append({"from": a, "to": b, "cfg": c})
    return out


def load_sched():
    d = read_json(SCHED_FILE)
    SCHED[:] = clean_slots(d.get("slots") if isinstance(d, dict) else None)


def save_sched(slots):
    SCHED[:] = clean_slots(slots)
    tmp = SCHED_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"slots": SCHED}, f, indent=1); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, SCHED_FILE)
    log("Zeitprofile (alle Geraete):", json.dumps(SCHED, ensure_ascii=False))
    return SCHED


# =====================================================================
# Pause-Regeln ueber Zustaende in Home Assistant (z. B. Fernseher an, Katzenklo benutzt).
# Das Add-on fragt selbst nach (alle 5 s) - keine Automation noetig. Im Zweifel wird AUFGENOMMEN:
# nicht erreichbar, "unavailable"/"unknown" oder laenger als die Hoechstdauer aktiv -> keine Pause.
# =====================================================================
HA_FILE = os.path.join(os.path.dirname(SETTINGS_FILE) or ".", "ha_rules.json")
HA_RULES = []
HA_STATE = {}            # Regel-ID -> {"state", "name", "active", "since", "until", "hold", "err"}
HA_LOCK = threading.Lock()
HA_INFO = {"ok": None, "error": "", "checked": None}
MAX_RULES = 12


def ha_api():
    """(Basis-URL, Token) fuer die Home-Assistant-API; im Add-on ueber den Supervisor."""
    url = os.environ.get("LAERM_HA_URL") or ("http://supervisor/core/api" if os.environ.get("SUPERVISOR_TOKEN") else "")
    tok = os.environ.get("LAERM_HA_TOKEN") or os.environ.get("SUPERVISOR_TOKEN") or ""
    return url.rstrip("/"), tok


def ha_get(path, timeout=5):
    url, tok = ha_api()
    if not url:
        raise RuntimeError("keine Verbindung zu Home Assistant (nur im Add-on verfuegbar)")
    req = urllib.request.Request(url + path, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def clean_rules(lst):
    out = []
    for d in (lst if isinstance(lst, list) else [])[:MAX_RULES]:
        if not isinstance(d, dict):
            continue
        ent = re.sub(r"[^a-z0-9_.]", "", str(d.get("entity") or "").strip().lower())[:120]
        if not re.fullmatch(r"[a-z_]+\.[a-z0-9_]+", ent or ""):
            continue
        st = re.sub(r"[\x00-\x1f]", "", str(d.get("states") or "")).strip()[:200] or "on"
        try:
            after = max(0.0, min(240.0, float(d.get("after_min", 1))))
        except (TypeError, ValueError):
            after = 1.0
        try:
            mx = max(0.0, min(48.0, float(d.get("max_h", 8))))
        except (TypeError, ValueError):
            mx = 8.0
        rid = re.sub(r"[^a-z0-9]", "", str(d.get("id") or ""))[:12] or secrets.token_hex(3)
        src = re.sub(r"[^a-z0-9_]", "", str(d.get("src") or "all"))[:16] or "all"
        mode = "note" if d.get("mode") == "note" else "pause"      # pause: anhalten; note: nur festhalten (z. B. Fernseher an/aus)
        out.append({"id": rid, "entity": ent, "states": st, "after_min": round(after, 1), "max_h": round(mx, 1), "mode": mode,
                    "src": src, "enabled": d.get("enabled", True) is not False, "label": re.sub(r"[\x00-\x1f]", "", str(d.get("label") or ""))[:60]})
    return out


def load_ha_rules():
    d = read_json(HA_FILE)
    HA_RULES[:] = clean_rules(d.get("rules") if isinstance(d, dict) else None)
    if isinstance(d, dict) and not d.get("v140"):     # einmalig (1.40): Fernseher/Medienplayer nur noch vermerken statt anhalten
        ch = [r for r in HA_RULES if r["entity"].startswith("media_player.") and r["mode"] == "pause"]
        for r in ch:
            r["mode"] = "note"
        try:
            with open(HA_FILE + ".tmp", "w") as f:
                json.dump({"rules": HA_RULES, "v140": True}, f, indent=1)
            os.replace(HA_FILE + ".tmp", HA_FILE)
            if ch:
                log("Regeln fuer Fernseher/Medienplayer auf „nur vermerken“ umgestellt:", ", ".join(r["entity"] for r in ch))
        except OSError:
            pass


def save_ha_rules(rules):
    with HA_LOCK:
        HA_RULES[:] = clean_rules(rules)
        tmp = HA_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"rules": HA_RULES, "v140": True}, f, indent=1); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, HA_FILE)
        for k in list(HA_STATE):
            if not any(r["id"] == k for r in HA_RULES):
                HA_STATE.pop(k, None)
    log("Pause-Regeln (Home Assistant):", json.dumps(HA_RULES, ensure_ascii=False))
    return HA_RULES


def rule_match(states, value):
    """states: "on, playing" (einer davon), "!off, !standby" (alles ausser), ">1" / "<0.5" (Zahl).
    "unavailable"/"unknown" zaehlen nie als aktiv - dann wird aufgenommen."""
    if value is None or str(value).lower() in ("unavailable", "unknown", "none", ""):
        return False
    v = str(value).strip().lower()
    pos, neg, num = [], [], []
    for t in [x.strip().lower() for x in str(states).split(",") if x.strip()]:
        m = re.fullmatch(r"([<>]=?)\s*(-?\d+(?:[.,]\d+)?)", t)
        if m:
            num.append((m.group(1), float(m.group(2).replace(",", "."))))
        elif t.startswith("!"):
            neg.append(t[1:].strip())
        else:
            pos.append(t)
    if v in pos:
        return True
    if num:
        try:
            f = float(v.replace(",", "."))
            for op, lim in num:
                if (op == ">" and f > lim) or (op == ">=" and f >= lim) or (op == "<" and f < lim) or (op == "<=" and f <= lim):
                    return True
        except ValueError:
            pass
    if neg and v not in neg:
        return True
    return False


def ha_hold_for(src_id):
    """Haelt gerade eine Regel die Aufnahme dieses Geraets an? Liefert {label, state, until} oder None."""
    now = time.time()
    with HA_LOCK:
        for r in HA_RULES:
            if not r["enabled"] or r.get("mode") == "note" or (r["src"] != "all" and r["src"] != src_id):
                continue
            h = HA_STATE.get(r["id"])
            if h and h.get("hold") and (h.get("active") or (h.get("until") or 0) > now):
                return {"label": r["label"] or h.get("name") or r["entity"], "state": h.get("state"), "entity": r["entity"],
                        "until": None if h.get("active") else dt.datetime.fromtimestamp(h["until"]).astimezone().isoformat(timespec="seconds")}
    return None


def ha_watch():
    """Alle 5 s die Zustaende abfragen und den Pausezustand je Regel fuehren (mit Nachlauf und Hoechstdauer)."""
    was = {}
    while True:
        time.sleep(5)
        with HA_LOCK:
            rules = [dict(r) for r in HA_RULES if r["enabled"]]
        if not rules:
            continue
        for r in rules:
            now = time.time()
            prev = HA_STATE.get(r["id"]) or {}
            try:
                d = ha_get("/states/" + r["entity"])
                val, name, err = d.get("state"), (d.get("attributes") or {}).get("friendly_name") or r["entity"], ""
                at_ = d.get("attributes") or {}
                vol = at_.get("volume_level"); mute = at_.get("is_volume_muted")       # Fernseher: Lautstaerke 0..1 und stumm (falls gemeldet)
                vol = int(round(float(vol) * 100)) if isinstance(vol, (int, float)) else None
                mute = bool(mute) if isinstance(mute, bool) else None
                HA_INFO.update(ok=True, error="", checked=now)
            except urllib.error.HTTPError as e:
                vol = mute = None
                val, name, err = None, prev.get("name") or r["entity"], "nicht gefunden" if e.code == 404 else f"HTTP {e.code}"
                HA_INFO.update(ok=e.code == 404, error="" if e.code == 404 else err, checked=now)
            except Exception as e:
                vol = mute = None
                val, name, err = None, prev.get("name") or r["entity"], str(e)[:120]
                HA_INFO.update(ok=False, error=err, checked=now)
            act = rule_match(r["states"], val)
            if act and (vol != prev.get("vol") or mute != prev.get("mute") or not prev.get("active")) and (vol is not None or mute is not None):
                ha_vol_add(r, r["label"] or name, vol, mute)        # Lautstaerke des Fernsehers mitschreiben (nur wenn an)
            if r.get("mode") == "note":                          # nur festhalten: kein Nachlauf, keine Hoechstdauer, keine Pause
                with HA_LOCK:
                    HA_STATE[r["id"]] = {"state": val, "name": name, "active": act, "capped": False, "since": prev.get("since") if (act and prev.get("active")) else (now if act else None),
                                         "until": None, "hold": False, "err": err, "checked": now, "note": True, "vol": vol, "mute": mute}
                if val is not None and (act != prev.get("active") or val != prev.get("state") or not prev.get("note")):
                    ha_hist_add(r, r["label"] or name, val, act)
                continue
            since = prev.get("since") if (act and prev.get("active")) else (now if act else None)
            capped = bool(act and r["max_h"] > 0 and since and now - since > r["max_h"] * 3600)
            if act and not capped:
                until = None
            elif prev.get("active") and not prev.get("capped"):
                until = now + r["after_min"] * 60             # gerade aus: Nachlauf
            else:
                until = prev.get("until")
            hold = (act and not capped) or bool(until and until > now)
            with HA_LOCK:
                HA_STATE[r["id"]] = {"state": val, "name": name, "active": act and not capped, "capped": capped, "since": since,
                                     "until": until, "hold": hold, "err": err, "checked": now, "vol": vol, "mute": mute}
            label = r["label"] or name
            if hold != was.get(r["id"], False):
                was[r["id"]] = hold
                msg = (f"pausiert: {label} ist „{val}“" if hold else f"fortgesetzt: {label} ist „{val}“") + ("" if r["src"] == "all" else f" (Gerät {r['src']})")
                log("Home-Assistant-Regel", msg)
                rec_log("pausiert (Home Assistant)" if hold else "fortgesetzt (Home Assistant)", f"{label}: {val}")
            if capped and not prev.get("capped"):
                log(f"Home-Assistant-Regel: {label} seit über {r['max_h']:g} h aktiv - Pause aufgehoben, es wird wieder aufgenommen")


HA_HIST = {"key": None, "rows": []}


def ha_hist_path():
    return os.path.join(paths()[0], "ha_zustand.csv")


def ha_hist_add(rule, label, state, on):
    """Zustandswechsel einer Festhalte-Regel mitschreiben (Zeit, Regel, Name, Entitaet, Zustand, an)."""
    try:
        f = ha_hist_path(); os.makedirs(os.path.dirname(f), exist_ok=True); new = not os.path.exists(f)
        with open(f, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["zeit", "regel", "name", "entitaet", "zustand", "an", "geraet"])
            w.writerow([dt.datetime.now().astimezone().isoformat(timespec="seconds"), rule["id"], label, rule["entity"], str(state)[:60], 1 if on else 0, rule["src"]])
    except OSError as e:
        log("Home-Assistant-Zustand nicht gespeichert:", e)


def ha_intervals(src_id, t_from, t_to):
    """Zeitraeume „an“ der Festhalte-Regeln fuer ein Geraet: [[von_ms, bis_ms, Name]]."""
    f = ha_hist_path()
    try:
        stt = os.stat(f)
    except OSError:
        return []
    key = (stt.st_mtime_ns, stt.st_size)
    if HA_HIST["key"] != key:
        rows = []
        with open(f, newline="", encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                try:
                    rows.append((int(dt.datetime.fromisoformat(r["zeit"]).timestamp() * 1000), r["regel"], r["name"], r["an"] == "1", r.get("geraet") or "all"))
                except (ValueError, KeyError, TypeError):
                    continue
        HA_HIST.update(key=key, rows=rows)
    cur, out = {}, []
    now = int(time.time() * 1000)
    for t, rid, nm, on, src in HA_HIST["rows"]:
        if src not in ("all", src_id):
            continue
        if on and rid not in cur:
            cur[rid] = (t, nm)
        elif not on and rid in cur:
            a, n_ = cur.pop(rid)
            if t > t_from and a < t_to:
                out.append([a, t, n_])
    with HA_LOCK:
        live = {r["id"] for r in HA_RULES if r.get("mode") == "note" and r["enabled"]}
    for rid, (a, n_) in cur.items():                     # noch an (oder Regel inzwischen entfernt: bis zum letzten Eintrag offen lassen)
        if rid in live and a < t_to:
            out.append([a, min(now, t_to), n_])
    return out


def ha_notes(src_id):
    """Zustand der Festhalte-Regeln jetzt (fuer eine neue Stoerung): [{label, entity, state, on}]."""
    out = []
    with HA_LOCK:
        for r in HA_RULES:
            if not r["enabled"] or r.get("mode") != "note" or (r["src"] != "all" and r["src"] != src_id):
                continue
            h = HA_STATE.get(r["id"]) or {}
            out.append({"label": r["label"] or h.get("name") or r["entity"], "entity": r["entity"], "state": h.get("state"),
                        "on": None if h.get("state") in (None, "unavailable", "unknown") else bool(h.get("active")),
                        "vol": h.get("vol") if h.get("active") else None, "mute": h.get("mute") if h.get("active") else None})
    return out


def ha_text(g):
    v = (g or {}).get("ha") or []
    vt = lambda x: (", stumm" if x.get("mute") else (f', Lautstärke {x["vol"]} %' if x.get("vol") is not None else "")) if x.get("on") else ""
    return " · ".join(f'{x["label"]}: {"an" if x["on"] else "aus" if x["on"] is False else "unbekannt"}' + (f' ({x["state"]})' if x.get("state") else "") + vt(x) for x in v)


def ha_vol_path():
    return os.path.join(paths()[0], "ha_lautstaerke.csv")


def ha_vol_add(rule, label, vol, mute):
    try:
        f = ha_vol_path(); os.makedirs(os.path.dirname(f), exist_ok=True); new = not os.path.exists(f)
        with open(f, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["zeit", "regel", "name", "entitaet", "lautstaerke_pct", "stumm", "geraet"])
            w.writerow([dt.datetime.now().astimezone().isoformat(timespec="seconds"), rule["id"], label, rule["entity"], "" if vol is None else vol,
                        "" if mute is None else (1 if mute else 0), rule["src"]])
    except OSError as e:
        log("Lautstaerke nicht gespeichert:", e)


HA_VOL = {"key": None, "rows": []}


def ha_volumes(src_id, t_from, t_to):
    """Lautstaerke-Wechsel im Zeitraum: [[ms, Name, Prozent oder None, stumm]] (dazu der letzte Wert davor)."""
    f = ha_vol_path()
    try:
        stt = os.stat(f)
    except OSError:
        return []
    key = (stt.st_mtime_ns, stt.st_size)
    if HA_VOL["key"] != key:
        rows = []
        with open(f, newline="", encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                try:
                    rows.append((int(dt.datetime.fromisoformat(r["zeit"]).timestamp() * 1000), r["name"], int(r["lautstaerke_pct"]) if r.get("lautstaerke_pct") else None,
                                 r.get("stumm") == "1", r.get("geraet") or "all"))
                except (ValueError, KeyError, TypeError):
                    continue
        HA_VOL.update(key=key, rows=rows)
    out, before = [], {}
    for t, nm, v, m, src in HA_VOL["rows"]:
        if src not in ("all", src_id):
            continue
        if t <= t_from:
            before[nm] = [t_from, nm, v, m]
        elif t <= t_to:
            out.append([t, nm, v, m])
    return list(before.values()) + out


def rec_log(action, by):
    try:
        out = paths()[0]; os.makedirs(out, exist_ok=True)
        f = os.path.join(out, "aufzeichnung.csv"); new = not os.path.exists(f)
        with open(f, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["zeit", "aktion", "durch"])
            w.writerow([dt.datetime.now().astimezone().isoformat(timespec="seconds"), action, by])
    except OSError:
        pass


def ha_rules_payload():
    now = time.time()
    with HA_LOCK:
        rows = []
        for r in HA_RULES:
            h = HA_STATE.get(r["id"]) or {}
            rows.append(dict(r, now_state=h.get("state"), name=h.get("name"), active=bool(h.get("active")), hold=bool(h.get("hold") and (h.get("active") or (h.get("until") or 0) > now)),
                             until=dt.datetime.fromtimestamp(h["until"]).astimezone().isoformat(timespec="seconds") if h.get("until") else None,
                             capped=bool(h.get("capped")), err=h.get("err") or ""))
    url, _ = ha_api()
    return {"rules": rows, "available": bool(url), "ok": HA_INFO["ok"], "error": HA_INFO["error"]}


def ha_entities():
    try:
        lst = ha_get("/states", timeout=8)
    except Exception as e:
        return {"ok": False, "error": str(e)[:160], "entities": []}
    out = [{"id": x.get("entity_id"), "name": (x.get("attributes") or {}).get("friendly_name") or "", "state": x.get("state")}
           for x in lst if isinstance(x, dict) and str(x.get("entity_id", "")).split(".")[0] in
           ("media_player", "binary_sensor", "sensor", "switch", "input_boolean", "light", "fan", "vacuum", "remote", "device_tracker", "select", "climate")]
    out.sort(key=lambda e: e["id"])
    return {"ok": True, "entities": out[:2000]}


def active_slot(slots, now=None):
    """(index, slot) des zur Uhrzeit passenden Zeitprofils; das erste passende gewinnt."""
    if not slots:
        return None
    now = now or dt.datetime.now()
    m = now.hour * 60 + now.minute
    for i, sl in enumerate(slots):
        a, b = parse_t(sl.get("from")), parse_t(sl.get("to"))
        if a is None or b is None or a == b:
            continue
        if (a <= m < b) if a < b else (m >= a or m < b):
            return i, sl
    return None


def scope_slots(src):
    return (src.get("sched") or []) if src.get("own") else SCHED


def effective_cfg(src, now=None):
    """Gueltige Werte einer Quelle: allgemein bzw. eigene Einstellungen, dazu das gerade aktive Zeitprofil."""
    hit = active_slot(scope_slots(src), now)
    if not src.get("own") and hit is None:
        return CFG
    c = dict(CFG)
    if src.get("own"):
        c.update({k: v for k, v in (src.get("cfg") or {}).items() if k in PER_KEYS})
    if hit is not None:
        c.update({k: v for k, v in hit[1]["cfg"].items() if k in SLOT_KEYS})
    return normalize(c)


def slot_label(src):
    hit = active_slot(scope_slots(src))
    return f'{hit[1]["from"]}–{hit[1]["to"]}' if hit else None


def clean_dev_cfg(d, existing):
    """Eigene Einstellungen eines Geraets pruefen. Fehlende Werte kommen aus den allgemeinen Einstellungen."""
    out = {k: CFG[k] for k in PER_KEYS}
    out.update({k: v for k, v in (existing or {}).items() if k in PER_KEYS})
    if isinstance(d, dict):
        for k, v in d.items():
            if k in PER_KEYS:
                c = clean(k, v)
                if c is not None:
                    out[k] = c
    full = normalize(dict(CFG, **out))
    return {k: full[k] for k in PER_KEYS}


REF_COLORS = ["#7048e8", "#2b8a3e", "#e8590c", "#1c7ed6", "#c2255c", "#868e96"]


def clean_refs(lst):
    """Eigene Referenzlinien eines Geraets: [{"label": "Fernseher", "db": -52.5, "color": "#7048e8"}], hoechstens 8."""
    out = []
    for d in (lst if isinstance(lst, list) else [])[:8]:
        if not isinstance(d, dict):
            continue
        try:
            v = float(str(d.get("db")).replace(",", "."))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(v):
            continue
        lab = re.sub(r"[\x00-\x1f<>]", "", str(d.get("label") or "")).strip()[:30]
        col = d.get("color") if d.get("color") in REF_COLORS else REF_COLORS[len(out) % len(REF_COLORS)]
        out.append({"label": lab, "db": round(max(-130.0, min(0.0, v)), 1), "color": col})
    return out


def clean_source(d, existing=None):
    """Quelle pruefen. existing = bisheriger Stand (fuer Updates)."""
    s = dict(existing or {})
    if "name" in d:
        n = re.sub(r"[\x00-\x1f<>]", "", str(d["name"])).strip()[:40]
        if n:
            s["name"] = n
    if "enabled" in d:
        s["enabled"] = d["enabled"] in (True, "true", "on", 1, "1")
    if "own" in d:
        s["own"] = d["own"] in (True, "true", "on", 1, "1")
    if "cfg" in d or (s.get("own") and not s.get("cfg")):
        s["cfg"] = clean_dev_cfg(d.get("cfg"), s.get("cfg"))
    if "sched" in d:
        s["sched"] = clean_slots(d["sched"])
    if "refs" in d:
        s["refs"] = clean_refs(d["refs"])
    if "plists" in d:                                  # Protokolllisten, in die dieses Geraet eintraegt (je mit Uhrzeit)
        s["plists"] = clean_plist_rules(d["plists"])
    if "hum" in d:
        try:
            h = int(d["hum"])
        except (TypeError, ValueError):
            h = 0
        s["hum"] = h if h in (0, 50, 60) else 0
    if "gain_db" in d:
        try:
            g = float(str(d["gain_db"]).replace(",", "."))
            if math.isfinite(g):
                g = max(-20.0, min(40.0, round(g * 2) / 2))          # 0,5-dB-Schritte
                s["gain_db"] = int(g) if g.is_integer() else g
        except (TypeError, ValueError, OverflowError):
            pass
    if "url" in d and s.get("type") == "url":
        u = fix_url(d["url"])[:500]
        if re.match(r"^(https?|rtsp|rtmp|udp|tcp)://", u, re.I) or u == "":
            user, pw, u = split_userinfo(u)
            if user is not None:                     # name:passwort@ aus der Adresse in die eigenen Felder uebernehmen
                s["user"], s["password"] = user, pw
            s["url"] = u
    if s.get("type") == "url":
        if "video" in d:
            s["video"] = d["video"] in (True, "true", "on", 1, "1")
        if "video_view" in d:
            s["video_view"] = d["video_view"] in (True, "true", "on", 1, "1")
        if "video_rot" in d:
            try:
                s["video_rot"] = int(d["video_rot"]) % 360 // 90 * 90
            except (TypeError, ValueError):
                pass
        if "video_url" in d:
            u = fix_url(d["video_url"])[:500]
            if u == "" or re.match(r"^(https?|rtsp)://", u, re.I):
                user2, pw2, u = split_userinfo(u)
                s["video_url"] = u
        if "video_dir" in d:
            s["video_dir"] = safe_dir(re.sub(r"[\x00-\x1f]", "", str(d["video_dir"] or "")))[:200]
        if "video_delay_ms" in d:
            try:
                s["video_delay_ms"] = max(-3000, min(3000, int(float(d["video_delay_ms"]))))
            except (TypeError, ValueError, OverflowError):
                pass
        if "user" in d:
            s["user"] = re.sub(r"[\x00-\x1f]", "", str(d["user"] or "")).strip()[:100]
            if not s["user"]:
                s["password"] = ""
        if "password" in d and d["password"] is not None:
            s["password"] = re.sub(r"[\x00-\x1f]", "", str(d["password"]))[:200]
    return s


def clean_plist_rules(v):
    out = []
    for x in (v if isinstance(v, list) else [])[:20]:
        if not isinstance(x, dict):
            continue
        lid = re.sub(r"[^a-z0-9_]", "", str(x.get("id") or ""))[:24]
        if not lid:
            continue
        f, t_ = str(x.get("from") or "")[:5], str(x.get("to") or "")[:5]
        out.append({"id": lid, "from": f if parse_t(f) is not None else "", "to": t_ if parse_t(t_) is not None else ""})
    return out


def split_userinfo(u):
    """(name, passwort, adresse_ohne_zugangsdaten). name ist None, wenn die Adresse keine enthaelt."""
    try:
        p = urllib.parse.urlsplit(u)
        if p.username is None:
            return None, "", u
        host = p.netloc.rpartition("@")[2]
        return (urllib.parse.unquote(p.username), urllib.parse.unquote(p.password or ""),
                urllib.parse.urlunsplit((p.scheme, host, p.path, p.query, p.fragment)))
    except ValueError:
        return None, "", u


def with_login(url, user, pw):
    """Zugangsdaten fuer ffmpeg in die Adresse einsetzen (kodiert, Sonderzeichen erlaubt)."""
    if not user or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" in re.split(r"[/?#]", rest, 1)[0]:          # Adresse enthaelt schon Zugangsdaten
        return url
    q = lambda x: urllib.parse.quote(x, safe="")
    return f"{scheme}://{q(user)}" + (f":{q(pw)}" if pw else "") + "@" + rest


def load_sources():
    raw = read_json(SOURCES_FILE)
    if os.path.exists(SOURCES_FILE) and not raw:
        bad = SOURCES_FILE + time.strftime(".broken-%Y%m%d_%H%M%S")
        try:
            shutil.copy2(SOURCES_FILE, bad)
            log(f"WARNUNG: sources.json war nicht lesbar und wurde nach {os.path.basename(bad)} gesichert")
        except OSError:
            pass
    lst = raw.get("sources") if isinstance(raw, dict) else None
    out, seen = [], set()
    for d in lst or []:
        if not isinstance(d, dict) or d.get("type") not in SRC_TYPES:
            continue
        sid = str(d.get("id", ""))
        if not re.fullmatch(r"[a-z0-9_]{1,16}", sid) or sid in seen:
            continue
        s = clean_source(d, {"id": sid, "type": d["type"], "name": default_name(d["type"]), "enabled": True, "gain_db": 0, "url": ""})
        s["device_info"] = re.sub(r"[\x00-\x1f<>]", "", str(d.get("device_info", "")))[:60]
        if d.get("check") is True:                    # aus einer Sicherung, Geraet war nicht erreichbar: ausgeschaltet, bitte pruefen
            s["check"] = True
        c_ = d.get("cal")
        if isinstance(c_, dict) and isinstance(c_.get("at"), str):     # Stand des Einpegelns
            try:
                s["cal"] = {"at": c_["at"][:40], "gain": float(c_.get("gain") or 0), "ref": str(c_.get("ref") or "")[:16],
                            "level": None if c_.get("level") is None else float(c_["level"])}
            except (TypeError, ValueError):
                pass
        if d["type"] == "phone":
            tok = str(d.get("token", ""))
            s["token"] = tok if re.fullmatch(r"[0-9a-f]{32}", tok) else secrets.token_hex(16)
        seen.add(sid); out.append(s)
    if "main" not in seen:
        out.insert(0, {"id": "main", "type": "local", "name": default_name("local", CFG.get("language") != "en"), "enabled": True, "gain_db": 0, "url": ""})
    else:   # Server-Mikrofon immer vorne
        out.sort(key=lambda s: s["id"] != "main")
    return out


SAVE_LOCK = threading.Lock()


def save_sources():
    with SAVE_LOCK:
        with SRC_LOCK:
            data = {"sources": [dict(r.src) for r in RUNNERS.values()]}
        tmp = SOURCES_FILE + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(data, f, indent=1); f.flush(); os.fsync(f.fileno())
            os.replace(tmp, SOURCES_FILE)
        except OSError as e:
            log("Quellen konnten nicht gespeichert werden:", e)


def b64(arr):
    return base64.b64encode(arr.tobytes()).decode()


class PushBuffer:
    """Audio, das ein Handy per HTTPS sendet (16 kHz, 16 bit mono). Haelt hoechstens 200 s (Nachholen nach Update/Netzabbruch).
    Jeder Block bekommt die Aufnahmezeit des Handys (nicht die Ankunftszeit), damit Ereignisse
    nach einem Netzabbruch zur richtigen Uhrzeit protokolliert werden."""
    BPS = REMOTE_RATE * 2
    CHUNK = REMOTE_RATE * 2 // 5           # 200 ms pro Paket vom Handy

    def __init__(self):
        self.buf = bytearray()
        self.cond = threading.Condition()
        self.last = 0.0
        self.session = None
        self.seq = -1
        self.dropped = 0
        self.head_ts = None

    def push(self, session, first, seq, data, age_ms):
        """Rueckgabe: 'ok', 'dup' (schon empfangen) oder 'busy' (Link laeuft auf einem anderen Geraet)."""
        with self.cond:
            now = time.time()
            if session != self.session:
                if self.session is not None and now - self.last < 10:
                    return "busy"
                self.session, self.seq = session, -1
                self.buf.clear(); self.head_ts = None
            if first is None or first > seq:
                first = seq
            if seq <= self.seq:
                return "dup"
            if first <= self.seq:                       # Wiederholung, Anfang schon empfangen
                n = seq - first + 1
                per = (len(data) // n) // 2 * 2 if n > 0 else self.CHUNK
                data = data[(self.seq - first + 1) * per:]
            self.seq = seq
            end_ts = now - max(0, min(240000, age_ms or 0)) / 1000.0
            if not self.buf or self.head_ts is None:
                self.head_ts = end_ts - len(data) / self.BPS
            self.buf += data
            cap = self.BPS * 200
            if len(self.buf) > cap:
                drop = len(self.buf) - cap
                self.dropped += drop; del self.buf[:drop]; self.head_ts += drop / self.BPS
            self.last = now
            self.cond.notify_all()
            return "ok"

    def take(self, size, timeout):
        """(Daten, Aufnahmezeit des Blockendes) oder None nach Ablauf von timeout."""
        with self.cond:
            end = time.monotonic() + timeout
            while len(self.buf) < size:
                left = end - time.monotonic()
                if left <= 0:
                    return None
                self.cond.wait(left)
            out = bytes(self.buf[:size]); del self.buf[:size]
            self.head_ts += size / self.BPS
            return out, self.head_ts

    @property
    def online(self):
        return time.time() - self.last < 4


# =====================================================================
# MQTT
# =====================================================================
TOPIC = "laerm_logger"
mq = None
STATE = {"today": dt.date.today().isoformat(), "count": 0, "total": 0, "last": None, "attr": None}


def pub(topic, payload, retain=False):
    if mq is not None:
        try:
            mq.publish(topic, payload, retain=retain)
        except Exception:
            pass


def announce_source(r):
    """MQTT-Entitaeten einer Quelle. Das Server-Mikrofon behaelt die Topics und IDs von frueher."""
    de = CFG["language"] != "en"
    main = r.id == "main"
    t = r.topic
    uid = "laerm_logger" if main else f"laerm_logger_{r.id}"
    dev = {"identifiers": [uid], "name": "GasLighter" + ("" if main else f" – {r.name}"),
           "manufacturer": "Local", "sw_version": VERSION}
    ents = {
        ("sensor", "level"): {"name": "Pegel" if de else "Level", "unit_of_measurement": "dBFS", "state_class": "measurement", "icon": "mdi:volume-high"},
        ("sensor", "baseline"): {"name": "Hintergrund" if de else "Background", "unit_of_measurement": "dBFS", "state_class": "measurement", "icon": "mdi:volume-low"},
        ("sensor", "threshold"): {"name": "Schwelle" if de else "Threshold", "unit_of_measurement": "dBFS", "state_class": "measurement", "icon": "mdi:arrow-collapse-up"},
        ("binary_sensor", "active"): {"name": "Störung" if de else "Disturbance", "payload_on": "ON", "payload_off": "OFF", "device_class": "sound"},
        ("binary_sensor", "online"): {"name": "Verbunden" if de else "Connected", "payload_on": "ON", "payload_off": "OFF", "device_class": "connectivity"},
    }
    ents[("sensor", "pruefsumme")] = {"name": "Prüfsumme Tagesaufzeichnung" if de else "Day recording checksum", "icon": "mdi:shield-check",
                                      "json_attributes_topic": f"{t}/pruefsumme_attr", "entity_category": "diagnostic"}
    if CFG.get("classify"):
        ents[("sensor", "sound_type")] = {"name": "Letzte Geräuschart" if de else "Last sound type", "icon": "mdi:ear-hearing", "json_attributes_topic": f"{t}/sound_type_attr"}
    if main:
        ents[("sensor", "events_today")] = {"name": "Störungen heute" if de else "Events today", "state_class": "total_increasing", "icon": "mdi:counter"}
        ents[("sensor", "last_event")] = {"name": "Letzte Störung" if de else "Last event", "device_class": "timestamp", "json_attributes_topic": f"{TOPIC}/last_event_attr"}
    for (comp, key), c in ents.items():
        c.update(unique_id=f"{uid}_{key}", state_topic=f"{t}/{key}", device=dev, availability_topic=f"{TOPIC}/status")
        pub(f"homeassistant/{comp}/{uid}/{key}/config", json.dumps(c), True)
    pub(f"{t}/active", "ON" if r.status.get("active") else "OFF", True)
    # Ausloeser je Geraet fuer Automationen: Ereignis-Entitaet (mit Details) und Geraete-Ausloeser
    pub(f"homeassistant/event/{uid}/ausloeser/config", json.dumps({
        "name": "Störung (Auslöser)" if de else "Disturbance (trigger)", "unique_id": f"{uid}_ausloeser", "icon": "mdi:bell-alert",
        "state_topic": f"{t}/ausloeser", "event_types": ["beginn", "ende", "erkannt"], "device": dev, "availability_topic": f"{TOPIC}/status"}), True)
    for key, sub in (("beginn", "beginnt" if de else "starts"), ("ende", "endet" if de else "ends"), ("erkannt", "Art erkannt" if de else "type detected")):
        pub(f"homeassistant/device_automation/{uid}/stoerung_{key}/config", json.dumps({
            "automation_type": "trigger", "topic": f"{t}/trigger", "payload": key, "type": "Störung" if de else "Disturbance", "subtype": sub, "device": dev}), True)


def unannounce_source(sid):
    uid = f"laerm_logger_{sid}"
    for comp, key in (("sensor", "level"), ("sensor", "baseline"), ("sensor", "threshold"), ("binary_sensor", "active"), ("binary_sensor", "online"), ("sensor", "sound_type"), ("sensor", "pruefsumme")):
        pub(f"homeassistant/{comp}/{uid}/{key}/config", "", True)
    for key in ("active", "online"):
        pub(f"{TOPIC}/{sid}/{key}", "", True)
    pub(f"homeassistant/event/{uid}/ausloeser/config", "", True)
    for key in ("beginn", "ende", "erkannt"):
        pub(f"homeassistant/device_automation/{uid}/stoerung_{key}/config", "", True)


def pub_trigger(r, kind, **info):
    """Ausloeser eines Geraets: beginn (Stoerung faengt an), ende (mit Dauer und Spitze), erkannt (Art/Profil der KI)."""
    try:
        pub(f"{r.topic}/trigger", kind)
        pub(f"{r.topic}/ausloeser", json.dumps(dict(event_type=kind, quelle=r.name, quelle_id=r.id, **info), ensure_ascii=False))
    except Exception:
        pass


def announce(client=None, *_):
    """Bei jeder (Neu-)Verbindung: Entitaeten melden und Befehle abonnieren.
    Der Client kommt direkt aus dem Rueckruf - sonst kann das Abonnieren beim schnellen Verbinden verloren gehen."""
    cl = client if hasattr(client, "subscribe") else mq
    pub(f"{TOPIC}/status", "online", True)
    with SRC_LOCK:
        runners = list(RUNNERS.values())
    for r in runners:
        announce_source(r)
    de = CFG["language"] != "en"
    pub(f"homeassistant/switch/laerm_logger/recording/config", json.dumps({
        "name": "Aufzeichnung" if de else "Recording", "unique_id": "laerm_logger_recording", "icon": "mdi:record-rec",
        "state_topic": f"{TOPIC}/recording", "command_topic": f"{TOPIC}/recording/set", "payload_on": "ON", "payload_off": "OFF",
        "availability_topic": f"{TOPIC}/status",
        "device": {"identifiers": ["laerm_logger"], "name": "GasLighter", "manufacturer": "Local", "sw_version": VERSION}}), True)
    pub(f"{TOPIC}/recording", "OFF" if RUN["paused"] else "ON", True)
    devc = {"identifiers": ["laerm_logger"], "name": "GasLighter", "manufacturer": "Local", "sw_version": VERSION}
    av = f"{TOPIC}/status"
    pub("homeassistant/number/laerm_logger/pause/config", json.dumps({
        "name": "Pause (Minuten)" if de else "Pause (minutes)", "unique_id": "laerm_logger_pause", "icon": "mdi:timer-pause",
        "command_topic": f"{TOPIC}/pause/set", "state_topic": f"{TOPIC}/pause", "value_template": "{{ value_json.minutes }}",
        "min": 0, "max": 720, "step": 5, "mode": "box", "unit_of_measurement": "min", "availability_topic": av, "device": devc}), True)
    pub("homeassistant/sensor/laerm_logger/pause_until/config", json.dumps({
        "name": "Pause bis" if de else "Paused until", "unique_id": "laerm_logger_pause_until", "icon": "mdi:timer-sand", "device_class": "timestamp",
        "state_topic": f"{TOPIC}/pause", "value_template": "{{ value_json.until if value_json.until else None }}",
        "json_attributes_topic": f"{TOPIC}/pause", "availability_topic": av, "device": devc}), True)
    for key, mins, nm in (("pause15", "15", ("Pause 15 min", "Pause 15 min")), ("pause60", "60", ("Pause 1 h", "Pause 1 h")), ("resume", "0", ("Fortsetzen", "Resume"))):
        pub(f"homeassistant/button/laerm_logger/{key}/config", json.dumps({
            "name": nm[0] if de else nm[1], "unique_id": f"laerm_logger_{key}", "icon": "mdi:play" if mins == "0" else "mdi:pause",
            "command_topic": f"{TOPIC}/pause/set", "payload_press": mins, "availability_topic": av, "device": devc}), True)
    pub("homeassistant/switch/laerm_logger/force/config", json.dumps({
        "name": "Manuell erfassen (außerhalb der Zeit)" if de else "Record outside hours", "unique_id": "laerm_logger_force", "icon": "mdi:record-circle",
        "state_topic": f"{TOPIC}/force", "command_topic": f"{TOPIC}/force/set", "payload_on": "ON", "payload_off": "OFF", "availability_topic": av, "device": devc}), True)
    pub("homeassistant/event/laerm_logger/event/config", json.dumps({
        "name": "Störung erkannt" if de else "Disturbance detected", "unique_id": "laerm_logger_event", "icon": "mdi:bell-ring",
        "state_topic": f"{TOPIC}/event", "event_types": ["stoerung", "art"], "availability_topic": av, "device": devc}), True)
    pub(f"{TOPIC}/force", "ON" if FORCE else "OFF", True)
    pub_pause()
    if cl is not None:
        try:
            for tp in ("recording/set", "pause/set", "force/set"):
                cl.subscribe(f"{TOPIC}/{tp}")
            log("MQTT verbunden, Befehle abonniert (Pause, Aufzeichnung, Manuell erfassen)")
        except Exception as e:
            log("MQTT: Abonnieren fehlgeschlagen:", e)
    pub(f"{TOPIC}/events_today", str(STATE["count"]), True)
    if STATE["last"]:
        pub(f"{TOPIC}/last_event", STATE["last"], True)
        pub(f"{TOPIC}/last_event_attr", STATE["attr"], True)


def mqtt_start():
    global mq
    host = os.environ.get("MQTT_HOST")
    if not host or not CFG["mqtt"]:
        return
    try:
        import paho.mqtt.client as mqtt
        try:
            c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="laerm_logger")
        except AttributeError:
            c = mqtt.Client(client_id="laerm_logger")
        c.username_pw_set(os.environ.get("MQTT_USER"), os.environ.get("MQTT_PASS"))
        c.will_set(f"{TOPIC}/status", "offline", retain=True)
        c.on_connect = announce

        def on_message(_c, _u, msg):
            raw = msg.payload.decode(errors="ignore").strip()
            if msg.topic == f"{TOPIC}/recording/set":
                v = raw.upper()
                if v in ("ON", "OFF"):
                    set_recording(v == "ON", "Home Assistant")
            elif msg.topic == f"{TOPIC}/pause/set":       # Zahl (Minuten) oder JSON {"minutes": 10, "reason": "Katzenklo"}
                try:
                    d = json.loads(raw) if raw.startswith("{") else {"minutes": raw}
                except ValueError:
                    d = {}
                if isinstance(d, dict):
                    pause_for(d.get("minutes", 0), "Home Assistant", d.get("reason", ""))
            elif msg.topic == f"{TOPIC}/force/set":
                v = raw.upper()
                if v in ("ON", "OFF"):
                    with SRC_LOCK:
                        ids = list(RUNNERS)
                    if v == "ON":
                        FORCE.update(ids)                     # aus Home Assistant: alle Geraete
                    else:
                        FORCE.clear()
                    pub(f"{TOPIC}/force", v, True)
                    log("Erfassung ausserhalb der Erfassungszeit", "MANUELL AN" if v == "ON" else "MANUELL AUS", "(Home Assistant, alle Geraete)")
        c.on_message = on_message
        mq = c                                         # vor dem Verbinden setzen (Rueckruf kann sofort kommen)
        c.connect_async(host, int(os.environ.get("MQTT_PORT", "1883")))
        c.loop_start()
        log("MQTT aktiv:", host)
    except Exception as e:
        log("MQTT nicht verfuegbar:", e)


# =====================================================================
# Protokoll und Clips
# =====================================================================
LOG_HEADER = ["start", "dauer_s", "spitze_dbfs", "hintergrund_dbfs", "datei", "schwelle_dbfs", "clip_s", "quelle", "quelle_id"]
KNOWN_HEADERS = [LOG_HEADER[:5], LOG_HEADER[:6], LOG_HEADER[:7]]   # bis 1.5, Zwischenstand, 1.6
LOG_LOCK = threading.RLock()


def migrate_log():
    """Bekannte alte log.csv-Formate erweitern (vorher Sicherung log.csv.bak).
    Fremde Formate (z. B. in Excel mit Semikolon gespeichert) werden unveraendert beiseitegelegt."""
    _, _, lg = paths()
    if not os.path.exists(lg):
        return
    with LOG_LOCK:
        with open(lg, newline="", encoding="utf-8-sig", errors="replace") as f:
            rows = list(csv.reader(f))
        if not rows or rows[0] == LOG_HEADER:
            return
        if rows[0] not in KNOWN_HEADERS:
            keep = lg[:-4] + time.strftime("_%Y%m%d_%H%M%S") + ".csv"
            os.replace(lg, keep)
            log(f"Hinweis: log.csv hatte ein unbekanntes Format und wurde unveraendert nach {os.path.basename(keep)} verschoben")
            return
        shutil.copy2(lg, lg + ".bak")
        n = len(rows[0])
        out = [LOG_HEADER]
        for r in rows[1:]:
            if not r:
                continue
            r = (r + [""] * n)[:n] + [""] * (len(LOG_HEADER) - n)
            if not r[8]:
                r[7], r[8] = RUNNERS["main"].name if "main" in RUNNERS else "", "main"
            out.append(r)
        tmp = lg + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(out)
        os.replace(tmp, lg)
        log(f"log.csv auf neues Format umgestellt ({len(out) - 1} Eintraege), Sicherung: log.csv.bak")


LOG_CACHE = {"key": None, "rows": []}


def read_log():
    """Alle Eintraege. Zwischengespeichert, solange sich die Datei nicht aendert; geparst wird ausserhalb der Sperre."""
    _, _, lg = paths()
    with LOG_LOCK:
        try:
            st = os.stat(lg)
        except OSError:
            return []
        key = (lg, st.st_mtime_ns, st.st_size)
        if LOG_CACHE["key"] == key:
            return LOG_CACHE["rows"]
        with open(lg, "rb") as f:
            raw = f.read()
    rows = []
    for r in csv.DictReader(raw.decode("utf-8-sig", errors="replace").splitlines()):
        if r.get("start"):
            d = {k: (r.get(k) or "") for k in LOG_HEADER}
            d["quelle_id"] = d["quelle_id"] or "main"
            rows.append(d)
    LOG_CACHE.update(key=key, rows=rows)
    return rows


# =====================================================================
# Geraeuschart (lokale KI, YAMNet in numpy) - nur Zusatzinformation
# =====================================================================
try:
    import classify
except Exception as _e:                                   # pragma: no cover
    classify = None
    log("Geraeuscherkennung nicht verfuegbar:", _e)
import lernen                                             # Lernen aus benannten Bereichen (nur numpy)

ART_LABEL = {
    "knock": ("Klopfen/Schlag", "Knock/Bang"), "door": ("Tür", "Door"), "steps": ("Schritte", "Footsteps"),
    "voice": ("Stimme", "Voice"), "tv": ("TV/Musik", "TV/Music"), "scrape": ("Kratzen/Knarren", "Scrape/Creak"),
    "signal": ("Signal/Alarm", "Signal/Alarm"), "animal": ("Tier", "Animal"), "noise": ("Dauergeräusch", "Steady noise"),
    "other": ("Sonstiges", "Other"),
}
ART_LOCK = threading.RLock()
ART = {"data": None}
ART_Q = queue.PriorityQueue()      # (Prioritaet, Zaehler, Datei, Quelle): neue Ereignisse vor dem Nachholen
ART_SEQ = itertools.count()
ART_STATE = {"queued": set(), "done": 0, "error": ""}


def art_enabled():
    return classify is not None and bool(CFG.get("classify")) and classify.available()


def art_path():
    return os.path.join(paths()[1], "art.json")


def art_all():
    with ART_LOCK:
        if ART["data"] is None:
            ART["data"] = read_json(art_path()) if os.path.exists(art_path()) else {}
            if not isinstance(ART["data"], dict):
                ART["data"] = {}
        return ART["data"]


ART_TIMER = {"t": None}


def art_write():
    with ART_LOCK:
        ART_TIMER["t"] = None
        if ART["data"] is None:
            return
        os.makedirs(os.path.dirname(art_path()), exist_ok=True)
        tmp = art_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(art_all(), f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, art_path())


def art_save(now=False):
    """Einordnungen speichern - gesammelt nach 3 s (bei vielen Stoerungen hintereinander nicht jedes Mal die ganze Datei)."""
    if now:
        return art_write()
    with ART_LOCK:
        if ART_TIMER["t"] is None:
            t_ = threading.Timer(3.0, art_write); t_.daemon = True
            ART_TIMER["t"] = t_; t_.start()


def art_group(e):
    return (e.get("man") or e.get("g") or "") if e else ""


def art_fields(datei):
    e = art_all().get(datei) if datei else None
    if not e:
        return {"art": "", "art_c": None, "art_man": False, "kinds": [], "prof": "", "prof_c": None, "prof_ok": False, "bg": False}
    p_ = e.get("p") or ["", None, ""]
    return {"art": art_group(e), "art_c": None if e.get("man") else e.get("c"), "art_man": bool(e.get("man")), "kinds": e.get("k") or [],
            "prof": p_[0] or "", "prof_c": p_[1] if p_[0] else None, "prof_ok": p_[2] == "ok", "bg": bool(p_[0]) and profile_bg(p_[0])}


def art_label(g, de=None):
    de = (CFG["language"] != "en") if de is None else de
    return ART_LABEL.get(g, ART_LABEL["other"])[0 if de else 1]


def art_store(datei, res):
    with ART_LOCK:
        old = art_all().get(datei) or {}
        e = {"g": res["art"], "c": res["conf"], "top": [[t["name"], t["pct"], t["group"]] for t in res["top"][:5]],
             "gs": res["groups"], "v": 1}
        if res.get("kinds") is not None:
            e["k"] = res["kinds"]; e["kv"] = 3
        if old.get("man"):
            e["man"] = old["man"]
        if old.get("p"):
            e["p"] = old["p"]                          # Profil-Zuordnung bleibt
        art_all()[datei] = e
        art_save()


def art_enqueue(datei, rid=None, prio=0, payload=None):
    """Erkennung einreihen. payload: {"audio", "rate", "off", "stem"} (Ton im Arbeitsspeicher, neue Ereignisse)
    oder {"rescore": True} (Neubewertung aus gespeicherten Fingerabdruecken, ohne Ton)."""
    if not datei or not art_enabled() or not payload:
        return False
    with ART_LOCK:
        if datei in ART_STATE["queued"]:
            return False
        ART_STATE["queued"].add(datei)
    ART_Q.put((prio, next(ART_SEQ), datei, rid, payload))
    return True


def ki_dir():
    return os.path.join(paths()[1], "ki")


def ki_path(stem):
    return os.path.join(ki_dir(), os.path.basename(stem) + ".json")


def ki_load(stem):
    f = ki_path(stem)
    if not os.path.isfile(f):
        return None
    try:
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def ki_save(stem, d):
    os.makedirs(ki_dir(), exist_ok=True)
    tmp = ki_path(stem) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, separators=(",", ":"))
    os.replace(tmp, ki_path(stem))


def ki_marks(patches, off, hop, pl):
    """Fenster-Ergebnisse zu Markern zusammenfassen: [[von_ms, bis_ms, Art, Prozent], ...] (ms ab Beginn der Spur)."""
    out = []
    for i, p in enumerate(patches):
        if not p:
            continue
        a, b = off + i * hop, off + i * hop + pl
        if out and out[-1][2] == p[0] and a <= out[-1][1] + 1:
            out[-1][1] = b; out[-1][3] = max(out[-1][3], p[1])
        else:
            out.append([a, b, p[0], p[1]])
    return [[int(a), int(b), k, v] for a, b, k, v in out]


# Was kam in einer Stoerung vor: je Art Anzahl (Schlaege, Signale ...) oder Dauer (Musik, Wasser ...)
KIND_PEAKS = {"knock", "thud", "bang", "hammer", "slam", "door", "cupboard", "bounce", "dishes", "steps"}   # einzelne Schlaege zaehlen
KIND_SPANS = {"doorbell", "phone", "alarm", "beep", "horn", "siren", "dog", "cat", "cough", "laugh", "shout", "cry", "baby"}   # Vorkommen zaehlen


def track_for(datei):
    """Gespeicherte Messwerte (Laermspur oder alte Grafik) zu einem Clip-Namen."""
    clips = paths()[1]
    b = os.path.basename(datei or "")
    if b.endswith(VIRT_EXT):
        m = evmeta_all().get(b[:-len(VIRT_EXT)])
        return virtual_graph(m) if m else None
    f = os.path.join(clips, b) if b.endswith(SPUR_EXT) else os.path.join(clips, "graphen", os.path.splitext(b)[0] + ".json")
    try:
        return load_graph(f) if os.path.isfile(f) else None
    except (OSError, ValueError):
        return None


def sub_events(marks, g):
    """Einzelereignisse einer Stoerung: [[ms ab Beginn der Spur, Art, Sicherheit %, Spitze dBFS, Dauer ms], ...].
    - jede Spitze ueber der Schwelle (mind. 250 ms Abstand) ist ein Einzelereignis; liegt sie in einem Marker einer
      Schlag-Art (Klopfen, Tuer, Geschirr ...), bekommt sie diese Art, liegt sie in keinem Marker: "unknown"
    - Signale/Stimmlaute und Dauergeraeusche: je Marker ein Einzelereignis mit Dauer (Spitzen darin gehoeren dazu)
    - Marker einer Schlag-Art ohne Spitze ueber der Schwelle bleiben als ein Einzelereignis erhalten"""
    marks = marks or []
    recs = (g or {}).get("recs") or []
    step = (g or {}).get("step") or 100
    core = (g or {}).get("core")                     # nur die Stoerung selbst (Vorlauf bis Nachlauf), nicht das Umfeld
    lo_t, hi_t = (core[0], core[1]) if core else (-1e18, 1e18)
    vals = [r[1] if r[1] is not None else -999.0 for r in recs]
    win = max(1, int(round(500 / step)))             # Umgebung je Seite fuer die Hervorhebung
    peaks, last = [], -1e9
    for i in range(1, len(recs) - 1):
        r = recs[i]
        v, thr = r[1], r[3]
        t = r[0] - step / 2
        if v is None or thr is None or v < thr or not (lo_t <= t <= hi_t):
            continue
        if not (v >= vals[i - 1] and v > vals[i + 1]):
            continue
        left, right = min(vals[max(0, i - win):i]), min(vals[i + 1:i + 1 + win])
        if v - max(left, right) < 4.0:              # kein deutliches Einzelgeraeusch, nur Schwankung im Dauerpegel
            continue
        if t - last >= 250:
            peaks.append((t, v)); last = t
    def span_peak(a, b):
        vs = [r[1] for r in recs if r[1] is not None and a <= r[0] - step / 2 <= b]
        return max(vs) if vs else None
    out, used = [], set()
    for t, v in peaks:                               # jede Spitze genau einem Marker zuordnen (dem, in dem sie am zentralsten liegt)
        best, bd = None, -1
        for m in marks:
            a, b = m[0], m[1]
            if a <= t <= b and min(t - a, b - t) > bd:
                best, bd = m, min(t - a, b - t)
        if best is None:
            out.append([int(t), "unknown", 0, round(v, 1), 0])
        elif best[2] in KIND_PEAKS:
            out.append([int(t), best[2], int(best[3]), round(v, 1), 0]); used.add(id(best))
        # Spitzen in Signal-/Dauer-Markern gehoeren zu diesem Geraeusch (unten je Marker)
    for m in marks:
        a, b, k, pct = m[0], m[1], m[2], m[3]
        if k in KIND_PEAKS:
            if id(m) not in used:
                pk = span_peak(a, b); out.append([int(a), k, int(pct), None if pk is None else round(pk, 1), 0])
        else:
            pk = span_peak(a, b); out.append([int(a), k, int(pct), None if pk is None else round(pk, 1), int(b - a)])
    out.sort(key=lambda x: x[0])
    return out


def kinds_summary(marks, g, subs=None):
    """Liste der vorgekommenen Arten aus den Einzelereignissen: [[Art, Anzahl oder None, Dauer s], ...], groesste zuerst.
    Schlaege, Signale, Stimmlaute und Unbekanntes werden gezaehlt, Dauergeraeusche nur mit Dauer angegeben."""
    subs = sub_events(marks, g) if subs is None else subs
    out = {}
    for _t, k, _p, _v, d in subs:
        n, dd = out.get(k, (0, 0.0))
        out[k] = (n + 1, dd + d / 1000.0)
    counted = lambda k: k in KIND_PEAKS or k in KIND_SPANS or k == "unknown"
    res = [[k, (n if counted(k) else None), round(d, 1)] for k, (n, d) in out.items()]
    res.sort(key=lambda x: (x[0] == "unknown", -(x[1] or 0), -x[2]))
    return res


def kinds_backfill():
    """Einmalig nach dem Start: fuer bereits ausgewertete Ereignisse die Liste der vorgekommenen Arten nachtragen."""
    time.sleep(20)
    try:
        todo = [(d, e) for d, e in list(art_all().items()) if isinstance(e, dict) and e.get("kv") != 3]
        n = 0
        for d, e in todo:
            ki = ki_load(os.path.splitext(os.path.basename(d))[0])
            if not ki or not ki.get("marks"):
                continue
            subs = sub_events(ki["marks"], track_for(d))
            k = kinds_summary(None, None, subs)
            with ART_LOCK:
                cur = art_all().get(d)
                if isinstance(cur, dict):
                    cur["k"] = k; cur["kv"] = 3; n += 1
            time.sleep(0.02)
        if n:
            art_save(); log(f"Vorgekommene Geraeuscharten fuer {n} Ereignisse nachgetragen")
    except Exception as e:
        log("Nachtragen der Geraeuscharten fehlgeschlagen:", e)


def quant_emb(emb):
    """Fingerabdruecke (>= 0) auf 8 Bit: je Fenster ein Skalenwert und 1024 Bytes."""
    E, S = [], []
    for e in np.asarray(emb, np.float32):
        sc = float(e.max()) or 1.0
        E.append(base64.b64encode(np.clip(np.round(e / sc * 255), 0, 255).astype(np.uint8).tobytes()).decode())
        S.append(round(sc, 5))
    return E, S


def ki_from_result(res, off, emb=None):
    hop = classify.yamnet_np.HOP * 1000.0 / 16000
    pl = classify.yamnet_np.PATCH * 1000.0 / 16000
    d = {"v": 1, "off": int(off), "hop": hop, "patch": pl, "marks": ki_marks(res["patches"], off, hop, pl),
         "pt": res["patches"], "top": [[t["name"], t["pct"], t["group"]] for t in res["top"][:5]]}
    if emb is not None:
        d["emb"], d["esc"] = quant_emb(emb)
    return d


def art_worker():
    while True:
        _p, _n, datei, rid, pl = ART_Q.get()
        try:
            if not art_enabled():
                continue
            stem = os.path.splitext(os.path.basename(datei))[0]
            if pl.get("rescore"):                            # ohne Ton: aus gespeicherten Fingerabdruecken
                ki = ki_load(stem)
                if not ki or not ki.get("emb"):
                    continue
                emb = np.stack([np.frombuffer(base64.b64decode(e), np.uint8).astype(np.float32) * (sc / 255.0)
                                for e, sc in zip(ki["emb"], ki["esc"])])
                sc, names = classify.scores_from_emb(emb)
                res = classify.summarize(sc, None, names)
                res["patches"] = classify.patch_marks(sc, None)
                ki.update(ki_from_result(res, ki.get("off", 0)), emb=ki["emb"], esc=ki["esc"])
            else:
                x = classify.pcm_to_float(pl["audio"].tobytes(), pl["rate"])
                pcm = pl["audio"] if pl.get("wav") else None
                pl["audio"] = None                         # Ton freigeben (ausser er soll nach der Pruefung gespeichert werden)
                # Mit Stimm-Sicherung muss jede Sekunde geprueft werden, auch bei sehr langen Ereignissen und das Ende
                if pl.get("wav"):
                    P_, H_ = classify.yamnet_np.PATCH, classify.yamnet_np.HOP
                    rest = (len(x) - P_) % H_ if len(x) > P_ else 0
                    if rest:
                        x = np.concatenate([x, np.zeros(H_ - rest, np.float32)])
                mp = max(400, int(math.ceil(max(0, len(x) - classify.yamnet_np.PATCH) / classify.yamnet_np.HOP)) + 1) if pl.get("wav") else 400
                res = classify.analyse_full(x, max_patches=mp, want_emb=bool(CFG.get("ki_embed")))
                del x
                ki = ki_from_result(res, pl["off"], res.get("emb"))
                if pl.get("wav"):                          # Stimm-Sicherung: Ton nur ohne erkannte Stimmen
                    vm = res.get("voice_max", 100)
                    if vm < classify.VOICE_GUARD_PCT:
                        ok = write_wav(os.path.join(paths()[1], stem + ".wav"), pcm, pl["rate"])
                        ki["wav"] = "saved" if ok else "error"
                    else:
                        ki["wav"] = "voice"
                        log(f"Ton nicht gespeichert ({stem}): Stimmen erkannt ({vm} %), nur Laermspur")
                    ki["voice_max"] = vm
                pcm = None
            g_ = track_for(datei)
            ki["subs"] = sub_events(ki.get("marks"), g_)
            ki["kinds"] = kinds_summary(None, None, ki["subs"])
            res["kinds"] = ki["kinds"]
            ki_save(stem, ki)
            art_store(datei, res)
            try:
                pr_ = prof_assign(datei, rid or "main", g_, ki)          # gelernte Profile (je Geraet eigene Beispiele)
            except Exception as e_:
                pr_ = None; log("Profil-Zuordnung fehlgeschlagen:", datei, e_)
            ART_STATE["done"] += 1; ART_STATE["error"] = ""
            with SRC_LOCK:
                r = RUNNERS.get(rid) if rid else None
            if r is not None:
                pub_trigger(r, "erkannt", art=res["art"], art_name=art_label(res["art"]), sicherheit_pct=res["conf"], datei=datei,
                            profil=pr_[0] if pr_ else "", profil_pct=pr_[1] if pr_ else None, hintergrund=bool(pr_ and profile_bg(pr_[0])))
                pub(f"{r.topic}/sound_type", art_label(res["art"]), True)
                pub(f"{TOPIC}/event", json.dumps({"event_type": "art", "quelle": r.name, "quelle_id": r.id, "art": res["art"], "art_name": art_label(res["art"]),
                                                  "sicherheit_pct": res["conf"], "datei": datei}, ensure_ascii=False))
                pub(f"{r.topic}/sound_type_attr", json.dumps({"art": res["art"], "sicherheit_pct": res["conf"], "datei": datei,
                                                              "top": [[t["name"], t["pct"]] for t in res["top"][:3]]}, ensure_ascii=False), True)
        except Exception as e:
            ART_STATE["error"] = str(e)[:200]
            log("Geraeuscherkennung fehlgeschlagen fuer", datei, e)
        finally:
            pl.pop("audio", None)
            with ART_LOCK:
                ART_STATE["queued"].discard(datei)
            time.sleep(0.3)           # nie die Aufnahme ausbremsen


# =====================================================================
# Protokolllisten: eigene Sammlungen (z. B. "Bad", "Garten"). Die Gesamtliste (log.csv) bleibt unveraendert;
# eine Liste merkt sich nur, welche Ereignisse zu ihr gehoeren (automatisch je Geraet und Uhrzeit oder von Hand).
# =====================================================================
PLISTS_LOCK = threading.RLock()
PLISTS = {"data": None}
PLIST_MAX = 100


def plists_path():
    return os.path.join(paths()[1], "listen.json")


def plists_all():
    with PLISTS_LOCK:
        if PLISTS["data"] is None:
            d = read_json(plists_path()) if os.path.exists(plists_path()) else {}
            if not isinstance(d, dict):
                d = {}
            d.setdefault("v", 1); d.setdefault("lists", []); d.setdefault("mem", {})
            PLISTS["data"] = d
        return PLISTS["data"]


def plists_save():
    with PLISTS_LOCK:
        f = plists_path(); os.makedirs(os.path.dirname(f), exist_ok=True)
        tmp = f + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(plists_all(), fh, ensure_ascii=False, separators=(",", ":"))
            fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, f)


def plist_by_id(lid):
    return next((x for x in plists_all()["lists"] if x["id"] == lid), None)


def plists_payload():
    with PLISTS_LOCK:
        d = plists_all()
        return {"ok": True, "lists": [dict(x, n=len(d["mem"].get(x["id"]) or {})) for x in d["lists"]]}


def in_window(t, f, to):
    """Liegt die Uhrzeit t im Fenster von–bis (ueber Mitternacht moeglich)? Beide leer = immer."""
    a, b = parse_t(f or ""), parse_t(to or "")
    if a is None and b is None:
        return True
    a = 0 if a is None else a; b = 24 * 60 if b is None else b
    m = t.hour * 60 + t.minute
    return a <= m < b if a < b else (m >= a or m < b) if a != b else True


def plists_auto(runner, stem, start):
    """Neues Ereignis automatisch in die Listen des Geraets eintragen, deren Uhrzeit passt."""
    rules = runner.src.get("plists") or []
    if not rules:
        return
    with PLISTS_LOCK:
        d = plists_all(); now = dt.datetime.now().astimezone().isoformat(timespec="seconds"); n = 0
        for r in rules:
            if plist_by_id(r["id"]) and in_window(start, r.get("from"), r.get("to")):
                d["mem"].setdefault(r["id"], {})[stem] = {"by": "auto", "at": now}; n += 1
        if n:
            plists_save()


def plists_of(stem):
    d = plists_all()
    return [x["id"] for x in d["lists"] if stem in (d["mem"].get(x["id"]) or {})]


def plist_change(action, data):
    """add {name} / edit {id, name?, note?} / del {id} / mem {id, keys, add}"""
    name = lambda v: re.sub(r"[\x00-\x1f<>]", "", str(v or "")).strip()[:60]
    with PLISTS_LOCK:
        d = plists_all()
        if action == "add":
            nm = name(data.get("name"))
            if not nm:
                return {"ok": False, "error": "empty"}
            if len(d["lists"]) >= PLIST_MAX:
                return {"ok": False, "error": "limit"}
            x = {"id": "l" + secrets.token_hex(5), "name": nm, "note": "", "created": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
            d["lists"].append(x); plists_save()
            return dict(plists_payload(), id=x["id"])
        x = plist_by_id(str(data.get("id") or ""))
        if x is None:
            return {"ok": False, "error": "not found"}
        if action == "edit":
            if "name" in data:
                nm = name(data.get("name"))
                if nm:
                    x["name"] = nm
            if "note" in data:
                x["note"] = clean_text(data.get("note"), 2000)
        elif action == "del":                          # nur die Liste; Ereignisse bleiben in der Gesamtliste
            d["lists"].remove(x); d["mem"].pop(x["id"], None)
        elif action == "mem":
            keys = data.get("keys") if isinstance(data.get("keys"), list) else []
            rows = read_log(); km = dict(zip(row_keys(rows), rows))
            m = d["mem"].setdefault(x["id"], {}); now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
            for k in keys[:5000]:
                r = km.get(str(k))
                if r is None:
                    continue
                st = event_stem(r, int(str(k).rsplit("|", 1)[1] or 0))
                if data.get("add", True):
                    m.setdefault(st, {"by": "hand", "at": now})
                else:
                    m.pop(st, None)
        plists_save()
    return plists_payload()


# =====================================================================
# Benannte Bereiche ("von hier bis hier war Teller klappern") und Lernen daraus
# =====================================================================
LABELS_LOCK = threading.RLock()
LABELS = {"data": None}
LABEL_MAX = 5000
PROTO_CACHE = {}           # (stem, id, a, b, Datei-Zeit) -> Merkmale


def labels_path():
    return os.path.join(paths()[1], "bereiche.json")


def labels_all():
    with LABELS_LOCK:
        if LABELS["data"] is None:
            d = read_json(labels_path()) if os.path.exists(labels_path()) else {}
            LABELS["data"] = d if isinstance(d, dict) else {}
        return LABELS["data"]


def labels_save():
    with LABELS_LOCK:
        os.makedirs(os.path.dirname(labels_path()), exist_ok=True)
        tmp = labels_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(labels_all(), f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, labels_path())


def labels_for(stem):
    e = labels_all().get(stem) or {}
    return {"l": list(e.get("l") or []), "rej": list(e.get("rej") or [])}


def label_names():
    """Alle vergebenen Namen mit Anzahl Beispiele (fuer die Auswahl und das Lernen)."""
    c = collections.Counter(); pf_ = set()
    for e in labels_all().values():
        for x in e.get("l") or []:
            c[x["name"]] += 1
    for n, pf in profiles_all().items():              # angelegte Tonprofile stehen ebenfalls zur Auswahl (gleicher Name = gleiche Art)
        c[n] += len(pf.get("ex") or []); pf_.add(n)
    return [{"name": n, "n": k, "pf": n in pf_} for n, k in sorted(c.items(), key=lambda kv: (-kv[1], kv[0].lower()))]


def _event_data(row, n):
    """Grafik und KI-Ergebnis eines Eintrags laden (fuer Merkmale)."""
    if is_virtual(row.get("datei")):
        g = event_graph(row, n)
        return (g, ki_load(event_stem(row, n)), "virt") if g else (None, None, None)
    gf = graph_file(row, n)
    if not gf:
        return None, None, None
    try:
        g = load_graph(gf)
    except (OSError, ValueError):
        return None, None, None
    return g, ki_load(event_stem(row, n)), gf


def label_protos():
    """Merkmale aller Beispiele, nach Namen gruppiert: benannte Bereiche in Ereignissen und Beispiele aus „Profil aufnehmen“.
    Jedes Beispiel kennt sein Geraet (sid), damit beim Vergleich Beispiele aus demselben Raum staerker zaehlen."""
    rows = read_log(); keys = row_keys(rows)
    by_stem = {}
    for r, k in zip(rows, keys):
        by_stem.setdefault(event_stem(r, int(k.rsplit("|", 1)[1] or 0)), (r, int(k.rsplit("|", 1)[1] or 0)))
    out = {}
    for stem, e in list(labels_all().items()):
        ls = e.get("l") or []
        if not ls or stem not in by_stem:
            continue
        r, n = by_stem[stem]
        if is_virtual(r.get("datei")):
            m_ = meta_of(r)
            if not m_:
                continue
            mt = 1 if time.time() * 1000 > m_["t_to"] + 120000 else int(time.time() // 30)     # Tagesdaten aendern sich danach nicht mehr
        else:
            gf = graph_file(r, n)
            if not gf:
                continue
            try:
                mt = os.path.getmtime(gf)
            except OSError:
                continue
        kf = ki_path(stem)
        try:
            mk = os.path.getmtime(kf) if os.path.exists(kf) else 0
        except OSError:
            mk = 0
        need = [x for x in ls if (stem, x["id"], x["a"], x["b"], mt, mk) not in PROTO_CACHE]
        if need:
            g, ki, _ = _event_data(r, n)
            d = lernen.decode(g) if g else None
            for x in need:
                PROTO_CACHE[(stem, x["id"], x["a"], x["b"], mt, mk)] = lernen.proto_from(d, ki, x["a"], x["b"]) if d else None
        for x in ls:
            pr = PROTO_CACHE.get((stem, x["id"], x["a"], x["b"], mt, mk))
            if pr and pr.get("band") is not None:
                out.setdefault(x["name"], []).append(dict(pr, stem=stem, id=x["id"], sid=r.get("quelle_id") or "main"))
    for name, pf in profiles_all().items():          # Beispiele aus „Profil aufnehmen“ (ohne Ereignis)
        for x in pf.get("ex") or []:
            if x.get("band"):
                out.setdefault(name, []).append({"band": np.asarray(x["band"], float), "emb": emb_dec(x.get("emb")), "dur": x.get("dur") or 1.0,
                                                 "stem": "", "id": x.get("id"), "sid": x.get("sid") or "main"})
    return out


def suggestions_for(stem, g, ki):
    """Vorschlaege aus den gelernten Bereichen fuer ein Ereignis (eigene Beispiele dieses Ereignisses ausgenommen)."""
    if not g:
        return []
    protos = {}
    for name, ps in label_protos().items():
        ps = [p for p in ps if p["stem"] != stem]
        if ps:
            protos[name] = ps
    if not protos:
        return []
    e = labels_for(stem)
    own = [x for x in e["l"]]
    res = lernen.find(lernen.decode(g), ki, protos, skip=[(r[0], r[1], r[2]) for r in e["rej"]])
    # nichts vorschlagen, was schon von Hand benannt ist
    return [h for h in res if not any(min(h[1], x["b"]) - max(h[0], x["a"]) > 0.5 * (h[1] - h[0]) for x in own)]


def clean_label_name(v):
    v = re.sub(r"\s+", " ", str(v or "")).strip()[:60]
    return v


def label_change(action, data):
    k = str(data.get("k", ""))[:300]
    rows = read_log()
    for r, key in zip(rows, row_keys(rows)):
        if key != k:
            continue
        n = int(key.rsplit("|", 1)[1] or 0)
        stem = event_stem(r, n)
        span = (fnum(r.get("clip_s")) or 600) * 1000
        m_ = meta_of(r) if is_virtual(r.get("datei")) else None
        if m_:                                        # Grafik aus der Tagesaufzeichnung: Bereiche beziehen sich auf deren ganzen Zeitraum
            span = max(span, int(m_["t_to"]) - int(m_["t_from"]))
        with LABELS_LOCK:
            e = labels_all().setdefault(stem, {"l": [], "rej": []})
            e.setdefault("l", []); e.setdefault("rej", [])
            if action in ("add", "edit"):
                name = clean_label_name(data.get("name"))
                try:
                    a = int(round(float(data.get("a")))); b = int(round(float(data.get("b"))))
                except (TypeError, ValueError):
                    return {"ok": False, "error": "bad range"}
                a, b = max(0, min(a, b)), min(int(span) + 500, max(a, b))
                if not name or b - a < 100:
                    return {"ok": False, "error": "bad label"}
                if action == "add":
                    if sum(len(x.get("l") or []) for x in labels_all().values()) >= LABEL_MAX:
                        return {"ok": False, "error": "limit"}
                    e["l"].append({"id": secrets.token_hex(4), "a": a, "b": b, "name": name, "t": int(time.time())})
                else:
                    x = next((x for x in e["l"] if x["id"] == data.get("id")), None)
                    if not x:
                        return {"ok": False, "error": "not found"}
                    x.update(a=a, b=b, name=name)
            elif action == "del":
                e["l"] = [x for x in e["l"] if x["id"] != data.get("id")]
            elif action == "reject":
                name = clean_label_name(data.get("name"))
                try:
                    e["rej"].append([name, int(data.get("a")), int(data.get("b"))])
                except (TypeError, ValueError):
                    return {"ok": False, "error": "bad range"}
                e["rej"] = e["rej"][-200:]
            else:
                return {"ok": False, "error": "bad action"}
            if not e["l"] and not e["rej"]:
                labels_all().pop(stem, None)
            labels_save()
        g, ki, _ = _event_data(r, n)
        return {"ok": True, "labels": labels_for(stem), "sugg": suggestions_for(stem, g, ki), "names": label_names()}
    return {"ok": False, "error": "not found"}


def similar_search(name, limit=100, budget_s=20.0):
    """Alle Ereignisse nach einem gelernten Namen durchsuchen (neueste zuerst)."""
    protos = label_protos().get(name)
    if not protos:
        return {"ok": False, "error": "no examples"}
    t_end = time.time() + budget_s
    rows = read_log(); keys = row_keys(rows)
    order = sorted(range(len(rows)), key=lambda i: rows[i].get("start") or "", reverse=True)
    hits, done, cut = [], 0, False
    for i in order:
        if time.time() > t_end:
            cut = True; break
        r, k = rows[i], keys[i]
        n = int(k.rsplit("|", 1)[1] or 0)
        stem = event_stem(r, n)
        own = [x for x in labels_for(stem)["l"] if x["name"] == name]
        g, ki, _ = _event_data(r, n)
        done += 1
        if not g:
            continue
        if own:
            hits.append({"k": k, "start": r["start"], "quelle": r["quelle"], "a": own[0]["a"], "b": own[0]["b"], "pct": 100, "own": True})
            continue
        b = lernen.best_in(lernen.decode(g), ki, [p for p in protos if p["stem"] != stem])
        if b:
            hits.append({"k": k, "start": r["start"], "quelle": r["quelle"], "a": b[0], "b": b[1], "pct": b[2], "own": False})
    hits.sort(key=lambda h: (-h["pct"], h["start"]))
    return {"ok": True, "name": name, "hits": hits[:limit], "n": len(hits), "searched": done, "cut": cut}


# =====================================================================
# Profile: gelernte Geraeusche ("Tuer knallt", "Fernseher"). Beispiele kommen aus benannten Bereichen und aus
# „Profil aufnehmen“ (je Geraet eigene Beispiele). Ein Profil kann „Hintergrund / eigenes Geraet“ sein: solche
# Stoerungen bleiben sichtbar, zaehlen aber nicht als Stoerung. Alles nur aus Messwerten und KI-Fingerabdruecken, nie Ton.
# =====================================================================
PROF_LOCK = threading.RLock()
PROF = {"data": None}
PROF_MIN = 0.70            # ab dieser Aehnlichkeit gilt eine Stoerung als zugeordnet
PROF_OTHER_DEV = 0.92      # Beispiele eines anderen Geraets zaehlen etwas weniger (anderer Raum klingt anders)


def profiles_path():
    return os.path.join(paths()[1], "profile.json")


def profiles_raw():
    with PROF_LOCK:
        if PROF["data"] is None:
            d = read_json(profiles_path()) if os.path.exists(profiles_path()) else {}
            PROF["data"] = d if isinstance(d, dict) and isinstance(d.get("p"), dict) else {"v": 1, "p": {}}
        return PROF["data"]


def profiles_all():
    return profiles_raw()["p"]


def profiles_save():
    with PROF_LOCK:
        os.makedirs(os.path.dirname(profiles_path()), exist_ok=True)
        tmp = profiles_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(profiles_raw(), f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, profiles_path())


def emb_enc(v):
    """Normierter Fingerabdruck -> 8 Bit (b64) mit Skalenwert."""
    if v is None:
        return None
    v = np.asarray(v, np.float32); sc = float(np.abs(v).max()) or 1.0
    return [base64.b64encode(np.clip(np.round(v / sc * 127), -127, 127).astype(np.int8).tobytes()).decode(), round(sc, 6)]


def emb_dec(e):
    if not e:
        return None
    try:
        v = np.frombuffer(base64.b64decode(e[0]), np.int8).astype(np.float32) * (float(e[1]) / 127.0)
    except (TypeError, ValueError, IndexError):
        return None
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else None


def profile_bg(name):
    return bool((profiles_all().get(name) or {}).get("bg"))


def profile_names():
    """Alle Namen (Profile und benannte Bereiche) mit Anzahl Beispiele je Geraet und Hintergrund-Kennzeichen."""
    names = {}
    for e in labels_all().values():
        for x in e.get("l") or []:
            names.setdefault(x["name"], collections.Counter())["_lb"] += 1
    for n, pf in profiles_all().items():
        c = names.setdefault(n, collections.Counter())
        for x in pf.get("ex") or []:
            c[x.get("sid") or "main"] += 1
    out = []
    for n, c in names.items():
        pf = profiles_all().get(n) or {}
        out.append({"name": n, "bg": bool(pf.get("bg")), "n": sum(c.values()), "lb": c.get("_lb", 0),
                    "dev": {k: v for k, v in c.items() if k != "_lb"}, "created": pf.get("created", "")})
    out.sort(key=lambda x: x["name"].lower())
    return out


def profile_best(g, ki, sid, core=None, protos=None):
    """Bestes Profil fuer den Kern einer Stoerung: (Name, Prozent) oder None."""
    if not g:
        return None
    protos = label_protos() if protos is None else protos
    if not protos:
        return None
    d = lernen.decode(g)
    if d is None:
        return None
    a, b = (core or g.get("core") or [0, 0])[:2]
    if b - a < 100:
        a, b = a - 250, a + 250
    fb = lernen.band_feature(d, a, b); fe = lernen.emb_feature(ki, a, b)
    best = None
    for name, ps in protos.items():
        sc = 0.0
        for p_ in ps:
            v = lernen.score(p_, fb, fe) * (1.0 if (p_.get("sid") or "main") == sid else PROF_OTHER_DEV)
            sc = max(sc, v)
        if best is None or sc > best[1]:
            best = (name, sc)
    if best and best[1] >= PROF_MIN:
        return best[0], int(round(100 * best[1]))
    return None


def prof_assign(datei, sid, g=None, ki=None, protos=None):
    """Profil-Zuordnung einer Stoerung neu bestimmen (bestaetigte bleiben). Rueckgabe: (Name, Prozent) oder None."""
    with ART_LOCK:
        e = art_all().get(datei)
        if e and e.get("p") and e["p"][2] == "ok":
            return e["p"][0], e["p"][1]
    stem = os.path.splitext(os.path.basename(datei))[0]
    if g is None:
        g = track_for(datei)
    if ki is None:
        ki = ki_load(stem)
    res = profile_best(g, ki, sid, None, protos)
    with ART_LOCK:
        e = art_all().get(datei)
        if e is None:
            if not res:
                return None
            e = art_all()[datei] = {"g": "", "c": 0, "top": [], "gs": {}, "v": 1}
        old = e.get("p")
        e["p"] = [res[0], res[1], "auto"] if res else None
        if e["p"] is None:
            e.pop("p", None)
        if old != e.get("p"):
            art_save()
    return res


def profile_change(data):
    """Profile verwalten: rename (von -> nach), delete, bg (Hintergrund an/aus), delex (ein Beispiel entfernen), confirm (Zuordnung bestaetigen/aendern)."""
    act = str(data.get("action", ""))
    name = clean_label_name(data.get("name"))
    if act == "confirm":                              # Stoerung: Profil bestaetigen ("ok"), anderes setzen oder loesen ("")
        datei = os.path.basename(str(data.get("datei", "")))[:120]
        with ART_LOCK:
            e = art_all().setdefault(datei, {"g": "", "c": 0, "top": [], "gs": {}, "v": 1})
            if name:
                e["p"] = [name, 100 if (not e.get("p") or e["p"][0] != name) else e["p"][1], "ok"]
            else:
                e["p"] = ["", 0, "ok"]                # ausdruecklich keinem Profil zugeordnet
            art_save()
        if name:                                      # bestaetigt/korrigiert = neues Beispiel fuer das Profil (Kern der Stoerung)
            try:
                stem = os.path.splitext(datei)[0]
                g = track_for(datei)
                core = (g or {}).get("core")
                if core and core[1] - core[0] >= 100:
                    with LABELS_LOCK:
                        le = labels_all().setdefault(stem, {"l": [], "rej": []})
                        le.setdefault("l", [])
                        if not any(x["name"] == name and min(x["b"], core[1]) - max(x["a"], core[0]) > 0 for x in le["l"]):
                            le["l"].append({"id": secrets.token_hex(4), "a": int(core[0]), "b": int(core[1]), "name": name, "t": int(time.time()), "pf": True})
                            labels_save()
                    PROTO_CACHE.clear()
            except Exception as ex:
                log("Profil-Beispiel nicht gespeichert:", ex)
        return {"ok": True}
    if not name:
        return {"ok": False, "error": "name"}
    with PROF_LOCK:
        P = profiles_all()
        if act == "bg":
            P.setdefault(name, {"ex": [], "created": dt.datetime.now().astimezone().isoformat(timespec="seconds")})["bg"] = bool(data.get("on"))
        elif act == "delex":
            pf = P.get(name) or {}
            pf["ex"] = [x for x in pf.get("ex") or [] if x.get("id") != data.get("id")]
        elif act == "rename":
            to = clean_label_name(data.get("to"))
            if not to:
                return {"ok": False, "error": "name"}
            if name in P:
                pf = P.pop(name)
                if to in P:
                    P[to]["ex"] = (P[to].get("ex") or []) + (pf.get("ex") or [])
                else:
                    P[to] = pf
            with LABELS_LOCK:
                ch = False
                for e in labels_all().values():
                    for x in e.get("l") or []:
                        if x["name"] == name:
                            x["name"] = to; ch = True
                if ch:
                    labels_save()
            with ART_LOCK:
                for e in art_all().values():
                    if isinstance(e, dict) and e.get("p") and e["p"][0] == name:
                        e["p"][0] = to
                art_save()
            scan_rename(name, to)
        elif act == "delete":
            P.pop(name, None)
            with ART_LOCK:
                for e in art_all().values():
                    if isinstance(e, dict) and e.get("p") and e["p"][0] == name and e["p"][2] == "auto":
                        e.pop("p", None)
                art_save()
            scan_rename(name, None)
        else:
            return {"ok": False, "error": "bad action"}
        profiles_save()
    PROTO_CACHE.clear()
    return {"ok": True, "profiles": profile_names()}


# ---------- Profil aufnehmen: Ruhepegel erfassen, dann jeden Ausschlag je Geraet als Beispiel ----------
TEACH = {"state": "idle"}
TEACH_LOCK = threading.Lock()
TEACH_QUIET_MS = 3000       # so lange wird der Ruhepegel erfasst
TEACH_OVER_DB = 6.0         # Ausschlag: so viel ueber dem Maximum der Ruhe
TEACH_END_MS = 500          # so lange wieder darunter = Ende des Ausschlags
TEACH_IDLE_S = 120          # ohne Geraeusch endet die Aufnahme von selbst


def teach_start(name, ids=None):
    name = clean_label_name(name)
    if not name:
        return {"ok": False, "error": "name"}
    with TEACH_LOCK:
        if TEACH.get("state") in ("quiet", "armed"):
            return {"ok": False, "error": "busy"}
        with SRC_LOCK:
            rs = [r for r in RUNNERS.values() if r.src.get("enabled", True) and (not ids or r.id in ids)]
        now = int(time.time() * 1000)
        TEACH.clear()
        TEACH.update(state="quiet", name=name, t0=now, q1=now + TEACH_QUIET_MS, last=now, ids=[r.id for r in rs],
                     base={}, cur={}, segs={r.id: [] for r in rs}, open={}, names={r.id: r.name for r in rs})
    threading.Thread(target=teach_loop, daemon=True).start()
    return {"ok": True}


def teach_loop():
    while True:
        time.sleep(0.2)
        with TEACH_LOCK:
            st = TEACH.get("state")
            if st not in ("quiet", "armed"):
                return
            now = int(time.time() * 1000)
            for sid in TEACH["ids"]:
                with SRC_LOCK:
                    r = RUNNERS.get(sid)
                if r is None:
                    continue
                cur = TEACH["cur"].get(sid, TEACH["t0"])
                with r.rlock:
                    fr = [x for x in r.spur if x[0] > cur]
                if not fr:
                    continue
                TEACH["cur"][sid] = fr[-1][0]
                for x in fr:
                    ts, pk = x[0], x[1]
                    if ts <= TEACH["q1"]:
                        TEACH["base"][sid] = max(TEACH["base"].get(sid, -130.0), pk)
                        continue
                    base = TEACH["base"].get(sid)
                    if base is None:
                        TEACH["base"][sid] = base = pk
                    o = TEACH["open"].get(sid)
                    if pk >= base + TEACH_OVER_DB:
                        if o is None:
                            TEACH["open"][sid] = o = {"a": ts - Terz.STEP_MS, "b": ts, "pk": pk, "low": None}
                        o["b"] = ts; o["pk"] = max(o["pk"], pk); o["low"] = None
                        TEACH["last"] = now
                    elif o is not None:
                        if pk >= base + TEACH_OVER_DB - 3:
                            o["b"] = ts; o["low"] = None
                        else:
                            o["low"] = o["low"] or ts
                            if ts - o["low"] >= TEACH_END_MS:
                                TEACH["open"].pop(sid, None)
                                if o["b"] - o["a"] >= 100:
                                    seg = teach_feature(r, o, base)
                                    if seg:
                                        TEACH["segs"][sid].append(seg)
                                        TEACH["last"] = now
            if st == "quiet" and now >= TEACH["q1"]:
                TEACH["state"] = "armed"
            if TEACH["state"] == "armed" and now - TEACH["last"] > TEACH_IDLE_S * 1000:
                TEACH["state"] = "done"
                return


def teach_feature(r, o, base):
    """Merkmale eines Ausschlags aus dem Arbeitsspeicher: Terz-Spektrum/Pegelverlauf und KI-Fingerabdruck (Ton nur hier, danach weg)."""
    a, b = int(o["a"]), int(o["b"])
    t_from = a - 1500
    with r.rlock:
        fr = [x for x in r.spur if t_from < x[0] <= b + 1500]
    if not fr:
        return None
    g = {"recs": [[x[0] - t_from, x[1], x[3], x[4], 2 if a <= x[0] <= b else 0, x[6], x[2]] for x in fr], "bands": Terz.CENTERS, "step": Terz.STEP_MS}
    d = lernen.decode(g)
    band = lernen.band_feature(d, a - t_from, b - t_from)
    emb = None
    if classify is not None and art_enabled():
        try:
            au, a0 = ram_audio(r, a - 250, b + 250)
            if len(au) >= 4000:
                res = classify.analyse_full(classify.pcm_to_float(au.tobytes(), r.hist_rate), max_patches=40, want_emb=True)
                e = res.get("emb")
                if e is not None and len(e):
                    v = np.asarray(e, np.float32).mean(axis=0); n = float(np.linalg.norm(v))
                    emb = v / n if n > 0 else None
            del au
        except Exception as ex:
            log("Profil: Fingerabdruck nicht berechnet:", ex)
    return {"id": secrets.token_hex(4), "sid": r.id, "a": a, "b": b, "dur": round((b - a) / 1000.0, 3), "peak": round(o["pk"], 1),
            "over": round(o["pk"] - base, 1), "band": [round(float(x), 4) for x in band] if band is not None else None, "emb": emb_enc(emb),
            "at": dt.datetime.fromtimestamp(a / 1000.0).astimezone().isoformat(timespec="seconds")}


def teach_groups():
    """Ausschlaege der Geraete zu Beispielen zusammenfassen (gleicher Moment, Beginn innerhalb 1,5 s)."""
    allseg = sorted(((sg["a"], sid, sg) for sid, ls in TEACH.get("segs", {}).items() for sg in ls), key=lambda x: x[0])
    groups = []
    for a, sid, sg in allseg:
        g = next((g for g in groups if abs(g["a"] - a) <= 1500 and sid not in g["dev"]), None)
        if g is None:
            g = {"a": a, "dev": {}}; groups.append(g)
        g["dev"][sid] = sg
    return groups


def teach_status():
    with TEACH_LOCK:
        st = TEACH.get("state", "idle")
        if st == "idle":
            return {"state": "idle"}
        now = int(time.time() * 1000)
        gs = teach_groups()
        return {"state": st, "name": TEACH.get("name"), "now": now, "q1": TEACH.get("q1"), "idle_s": TEACH_IDLE_S,
                "left_s": max(0, int(TEACH_IDLE_S - (now - TEACH.get("last", now)) / 1000)),
                "base": {k: round(v, 1) for k, v in TEACH.get("base", {}).items()}, "names": TEACH.get("names", {}),
                "ids": TEACH.get("ids", []),
                "groups": [{"at": dt.datetime.fromtimestamp(g["a"] / 1000.0).strftime("%H:%M:%S"),
                            "dev": {sid: {"over": sg["over"], "dur": sg["dur"]} for sid, sg in g["dev"].items()}} for g in gs]}


def teach_finish(apply, skip=None):
    """Fertig: Beispiele uebernehmen (apply) oder verwerfen. skip: Nummern der Beispiele, die nicht uebernommen werden."""
    with TEACH_LOCK:
        if TEACH.get("state") == "idle":
            return {"ok": False, "error": "idle"}
        name = TEACH.get("name"); gs = teach_groups()
        TEACH.clear(); TEACH["state"] = "idle"
    if not apply:
        return {"ok": True, "n": 0}
    skip = set(int(x) for x in (skip or []) if str(x).isdigit())
    ex = [sg for i, g in enumerate(gs) if i not in skip for sg in g["dev"].values() if sg.get("band")]
    if not ex:
        return {"ok": False, "error": "none"}
    with PROF_LOCK:
        pf = profiles_all().setdefault(name, {"ex": [], "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "bg": False})
        pf.setdefault("ex", []).extend(ex)
        pf["ex"] = pf["ex"][-400:]
        profiles_save()
    PROTO_CACHE.clear()
    log(f"Profil „{name}“: {len(ex)} Beispiel(e) aus {len(gs) - len(skip)} Aufnahme(n) gelernt")
    return {"ok": True, "n": len(ex), "profiles": profile_names()}


def mark_feature(sid, a, b):
    """Merkmale eines im Verlauf/Live-Bild markierten Bereichs (ohne Stoerung): Terz-Spektrum/Pegel aus der Tagesaufzeichnung,
    KI-Fingerabdruck nur, solange der Ton noch im Arbeitsspeicher ist (danach weg, nie gespeichert)."""
    t_from = a - 1500
    fr = day_frames(sid, t_from, b + 1500)
    if not fr:
        return None
    g = {"recs": [[x[0] - t_from, x[1], x[3], x[4], 2 if a <= x[0] <= b else 0, x[6], x[2]] for x in fr], "bands": Terz.CENTERS, "step": Terz.STEP_MS}
    d = lernen.decode(g)
    band = lernen.band_feature(d, a - t_from, b - t_from) if d else None
    if band is None:
        return None
    pk = max((x[1] for x in fr if a <= x[0] <= b and x[1] is not None), default=None)
    bg = next((x[3] for x in fr if x[0] >= a and x[3] is not None), None)
    emb = None
    with SRC_LOCK:
        r = RUNNERS.get(sid)
    if r is not None and classify is not None and art_enabled():
        try:
            au, a0 = ram_audio(r, a - 250, b + 250)
            if len(au) >= max(4000, int(0.8 * (b - a + 500) / 1000.0 * r.hist_rate)):
                res = classify.analyse_full(classify.pcm_to_float(au.tobytes(), r.hist_rate), max_patches=40, want_emb=True)
                e = res.get("emb")
                if e is not None and len(e):
                    v = np.asarray(e, np.float32).mean(axis=0); n = float(np.linalg.norm(v))
                    emb = v / n if n > 0 else None
            del au
        except Exception as ex:
            log("Markierung: Fingerabdruck nicht berechnet:", ex)
    return {"id": secrets.token_hex(4), "sid": sid, "a": a, "b": b, "dur": round((b - a) / 1000.0, 3), "peak": round(pk, 1) if pk is not None else None,
            "over": round(pk - bg, 1) if pk is not None and bg is not None else None, "band": [round(float(x), 4) for x in band], "emb": emb_enc(emb),
            "src": "mark", "at": dt.datetime.fromtimestamp(a / 1000.0).astimezone().isoformat(timespec="seconds")}


def label_mark(data):
    """Bereich im Verlauf (Protokolle) oder im Live-Bild markiert und benannt: liegt er in einer Stoerung dieses Geraets,
    wird er dort als benannter Bereich gespeichert (mit den KI-Merkmalen der Stoerung), sonst als Beispiel des Profils."""
    name = clean_label_name(data.get("name"))
    sid = str(data.get("src") or "main")[:80]
    try:
        a, b = sorted((int(float(data.get("a"))), int(float(data.get("b")))))
    except (TypeError, ValueError):
        return {"ok": False, "error": "bad range"}
    if not name:
        return {"ok": False, "error": "bad label"}
    if b - a < 150 or b - a > 120000:
        return {"ok": False, "error": "length"}
    best = None
    rows = read_log(); em_ = evmeta_all()
    for r, key in zip(rows, row_keys(rows)):
        if (r.get("quelle_id") or "main") != sid:
            continue
        try:
            st = int(dt.datetime.fromisoformat(r["start"]).timestamp() * 1000)
        except (ValueError, KeyError, TypeError):
            continue
        if not (a - 600000 <= st <= b):
            continue
        datei = r.get("datei") or ""
        if is_virtual(datei):
            m_ = em_.get(os.path.splitext(os.path.basename(datei))[0])
            if not m_:
                continue
            t0, t1 = int(m_["t_from"]), int(m_["t_to"])          # Grafik der Stoerung (mit Rand)
            c0, c1 = int(m_["t0"]), int(m_["t_end"])            # die Stoerung selbst
        elif datei.endswith(SPUR_EXT):
            g_ = track_for(datei)
            if not g_ or not g_.get("t0"):
                continue
            t0 = int(g_["t0"]); t1 = t0 + int((fnum(r.get("clip_s")) or 60) * 1000)
            c0 = st; c1 = st + int((fnum(r.get("dauer_s")) or 0) * 1000)
        else:
            continue
        ov = min(b, c1 + 2000) - max(a, c0 - 2000)             # gehoert zur Stoerung (Kern +/- 2 s) und liegt in ihrer Grafik
        if ov >= 0.5 * (b - a) and min(b, t1) - max(a, t0) >= 0.9 * (b - a) and (best is None or ov > best[0]):
            best = (ov, key, t0, t1)
    if best:
        _, key, t0, t1 = best
        res = label_change("add", {"k": key, "a": max(a, t0) - t0, "b": min(b, t1) - t0, "name": name})
        if res.get("ok"):
            PROTO_CACHE.clear()
            return {"ok": True, "how": "event", "names": res.get("names")}
        return res
    ex = mark_feature(sid, a, b)
    if not ex:
        return {"ok": False, "error": "no data"}
    with PROF_LOCK:
        pf = profiles_all().setdefault(name, {"ex": [], "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "bg": False})
        pf.setdefault("ex", []).append(ex)
        pf["ex"] = pf["ex"][-400:]
        profiles_save()
    PROTO_CACHE.clear()
    log(f"Profil „{name}“: Beispiel aus markiertem Bereich ({sid}, {ex['dur']} s{', mit KI-Fingerabdruck' if ex.get('emb') else ''})")
    return {"ok": True, "how": "profile", "emb": bool(ex.get("emb")), "names": label_names()}


# =====================================================================
# KI-Fingerabdruck durchgehend (pro Geraet abschaltbar): einmal pro Sekunde, wenn etwas zu hoeren ist (mind. 3 dB ueber
# dem Hintergrund), rechnet die KI aus dem Ton im Arbeitsspeicher Zahlen aus. Gespeichert werden nur diese Zahlen
# (Gruppen-Werte und eine verkuerzte Fassung des Fingerabdrucks), nie Ton; daraus laesst sich nichts zurueckverwandeln.
# =====================================================================
FP_EXT = ".lfp"
FP_DIM = 128
FP_REC = struct.Struct("<qe10s128s")          # Zeit (ms), Skala, 10 Gruppen (%), 128 Werte (8 Bit)
FP_GROUPS = ["knock", "door", "steps", "voice", "tv", "scrape", "signal", "animal", "noise", "other"]
_FP_P = None


def fp_proj():
    """Feste Zufallsprojektion 1024 -> 128 (Abstaende/Winkel bleiben naeherungsweise erhalten)."""
    global _FP_P
    if _FP_P is None:
        _FP_P = (np.random.default_rng(140).standard_normal((1024, FP_DIM)) / math.sqrt(FP_DIM)).astype(np.float32)
    return _FP_P


def fp_vec(emb):
    """1024er-Fingerabdruck -> verkuerzte, normierte Fassung (wie gespeichert)."""
    v = np.asarray(emb, np.float32) @ fp_proj()
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def fp_path(sid, day):
    return os.path.join(day_dir(), f"{day}_{sid}{FP_EXT}")


def fp_pack(ms, sc, emb):
    gw = []
    for g in FP_GROUPS[:-1]:
        idx = classify.GROUPS.get(g) or []
        w = np.array([classify.WEIGHT.get(c, 1.0) for c in idx], np.float32)
        gw.append(int(round(100 * float((sc[idx] * w).max()))) if idx else 0)
    gw.append(0)
    v = fp_vec(emb); m = float(np.abs(v).max()) or 1.0
    q = np.clip(np.round(v / m * 127), -127, 127).astype(np.int8)
    return FP_REC.pack(int(ms), m, bytes(np.clip(gw, 0, 100).astype(np.uint8)), q.tobytes())


FP_CACHE = {}


def fp_load(sid, day):
    """(Zeiten, Gruppen n x 10 in %, Fingerabdruck n x 128 normiert) oder None."""
    p = fp_path(sid, day)
    try:
        size = os.path.getsize(p)
    except OSError:
        return None
    c = FP_CACHE.get(p)
    if c and c[0] == size:
        return c[1]
    try:
        raw = open(p, "rb").read()
    except OSError:
        return None
    n = len(raw) // FP_REC.size
    if not n:
        return None
    a = np.frombuffer(raw[:n * FP_REC.size], dtype=np.dtype([("t", "<i8"), ("s", "<f2"), ("g", "u1", 10), ("v", "i1", 128)]))
    v = a["v"].astype(np.float32) * (a["s"].astype(np.float32)[:, None] / 127.0)
    nv = np.linalg.norm(v, axis=1, keepdims=True); nv[nv == 0] = 1
    o = np.argsort(a["t"], kind="stable")
    res = (a["t"][o].astype(np.int64), a["g"][o], (v / nv)[o])
    if len(FP_CACHE) > 6:
        FP_CACHE.pop(next(iter(FP_CACHE)))
    FP_CACHE[p] = (size, res)
    return res


FP_STATE = {"on": False, "n": 0, "skip": 0, "ms": 0.0}


def fp_worker():
    """Einmal pro Sekunde je Geraet (nur wenn etwas zu hoeren ist). Wird es zu viel fuer den Rechner, kommen die Geraete reihum dran."""
    buf = {}
    last_flush = time.time()
    rr = 0
    while True:
        t_c = time.time()
        try:
            if classify is not None and art_enabled() and classify.available():
                with SRC_LOCK:
                    rs = [r for r in RUNNERS.values() if r.cfg().get("fp_store", True) and r.src.get("enabled", True)]
                FP_STATE["on"] = bool(rs)
                if rs:
                    rr = (rr + 1) % len(rs)
                    for r in rs[rr:] + rs[:rr]:
                        if time.time() - t_c > 0.35 or not ART_Q.empty():   # Zeit aufgebraucht oder Stoerung wartet auf die KI: Rest naechstes Mal
                            FP_STATE["skip"] += 1
                            break
                        with r.rlock:
                            fr = list(r.spur)[-8:]
                        if len(fr) < 8 or fr[-1][0] < time.time() * 1000 - 3000:
                            continue
                        base = fr[-1][3]
                        if base is None or max(x[1] for x in fr) - base < 3.0:
                            continue                         # Ruhe: nichts zu speichern
                        t1 = fr[-1][0]
                        au, a0 = ram_audio(r, t1 - 1000, t1)
                        if len(au) < int(r.hist_rate * 0.98):
                            continue
                        x = classify.pcm_to_float(au[-int(r.hist_rate * 0.975):].tobytes(), r.hist_rate)
                        del au
                        t_ = time.time()
                        with classify._LOCK:
                            net = classify._net()
                            sc, emb = net.scores_emb(x, max_patches=1)
                        FP_STATE["ms"] = round((time.time() - t_) * 1000, 1)
                        if len(sc):
                            day = dt.datetime.fromtimestamp(t1 / 1000.0).date().isoformat()
                            buf.setdefault((r.id, day), []).append(fp_pack(t1 - 487, sc[0], emb[0]))
                            FP_STATE["n"] += 1
            else:
                FP_STATE["on"] = False
        except Exception as e:
            log("Fingerabdruck fehlgeschlagen:", e)
        if buf and (time.time() - last_flush > 20):
            for (sid, day), recs in buf.items():
                try:
                    os.makedirs(day_dir(), exist_ok=True)
                    with open(fp_path(sid, day), "ab") as fh:
                        fh.write(b"".join(recs))
                except OSError as e:
                    log("Fingerabdruck nicht gespeichert:", e)
            buf = {}; last_flush = time.time()
        time.sleep(max(0.05, 1.0 - (time.time() - t_c)))


# =====================================================================
# Neu untersuchen: gespeicherte Daten eines Zeitraums mit den Profilen vergleichen.
# 1) jede Stoerung bekommt (neu) ihr Profil (bestaetigte bleiben),
# 2) in der Tagesaufzeichnung werden auch Stellen unter der Schwelle markiert ("Fernseher lief 20:10-23:40").
# Ergebnisse je Tag und Geraet in clips/scan/<Tag>_<Geraet>.json; eigene Markierungen werden nie veraendert.
# =====================================================================
SCAN = {"state": "idle", "done": 0, "total": 0, "msg": "", "areas": 0, "events": 0}
SCAN_LOCK = threading.Lock()
SCAN_MIN = 0.75            # durchgehende Suche etwas strenger als bei Stoerungen


def scan_dir():
    return os.path.join(paths()[1], "scan")


def scan_file(sid, day):
    return os.path.join(scan_dir(), f"{day}_{sid}.json")


def scan_load(sid, day):
    d = read_json(scan_file(sid, day)) if os.path.exists(scan_file(sid, day)) else {}
    return d.get("areas") if isinstance(d, dict) and isinstance(d.get("areas"), list) else []


def scan_save(sid, day, areas):
    os.makedirs(scan_dir(), exist_ok=True)
    tmp = scan_file(sid, day) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"v": 1, "at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "areas": areas}, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, scan_file(sid, day))


def scan_rename(old, new):
    for f in glob.glob(os.path.join(scan_dir(), "*.json")):
        d = read_json(f)
        if not isinstance(d, dict):
            continue
        a = d.get("areas") or []
        b = [[x[0], x[1], new, x[3]] if x[2] == old else x for x in a if new is not None or x[2] != old]
        if b != a:
            d["areas"] = b
            with open(f + ".tmp", "w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False, separators=(",", ":"))
            os.replace(f + ".tmp", f)


def scan_areas(sid, t_from, t_to):
    out = []
    d0 = dt.datetime.fromtimestamp(t_from / 1000.0).date(); d1 = dt.datetime.fromtimestamp(t_to / 1000.0).date()
    day = d0
    while day <= d1:
        for a in scan_load(sid, day.isoformat()):
            if a[1] > t_from and a[0] < t_to:
                out.append(a + [profile_bg(a[2])])
        day += dt.timedelta(days=1)
    return out


def _proto_sets(protos, sid):
    """Je Name: Bandmerkmale (Matrix), Gewichte (eigenes Geraet 1, sonst etwas weniger), Fingerabdruecke (verkuerzt), Dauer."""
    out = {}
    for name, ps in protos.items():
        B = [p_["band"] for p_ in ps if p_.get("band") is not None]
        if not B:
            continue
        W = np.array([1.0 if (p_.get("sid") or "main") == sid else PROF_OTHER_DEV for p_ in ps if p_.get("band") is not None])
        E = [(fp_vec(p_["emb"]), 1.0 if (p_.get("sid") or "main") == sid else PROF_OTHER_DEV) for p_ in ps if p_.get("emb") is not None]
        durs = [p_["dur"] for p_ in ps if p_.get("dur")]
        out[name] = {"B": np.asarray(B, float), "W": W, "E": E, "D": float(np.clip(np.median(durs) if durs else 1.0, 0.4, 12.0)) * 1000}
    return out


def scan_chunk(ts, L, BG, T, ps_, fp_):
    """Ein Stueck Tagesaufzeichnung (bis 1 h) durchsuchen: Liste [a, b, Name, Prozent]."""
    N = len(ts)
    if N < 4:
        return []
    P = 10 ** (T / 10.0); w = 10 ** (L / 10.0)
    Cw = np.concatenate([[0.0], np.cumsum(w)]); CPw = np.vstack([np.zeros((1, P.shape[1])), np.cumsum(P * w[:, None], axis=0)])
    CL = np.concatenate([[0.0], np.cumsum(L)])
    bgf = np.where(np.isfinite(BG), BG, L); CB = np.concatenate([[0.0], np.cumsum(bgf)])
    best = None                                       # je Rahmen: (Name, Wert) des besten Fensters
    win_hits = []
    for name, ps in ps_.items():
        Wn = max(2, int(round(ps["D"] / Terz.STEP_MS)))
        if N < Wn:
            continue
        hop = max(1, Wn // 4)
        st = np.arange(0, N - Wn + 1, hop)
        ok = (ts[st + Wn - 1] - ts[st]) <= ps["D"] * 1.6          # keine Luecke im Fenster
        st = st[ok]
        if not len(st):
            continue
        S = 10 * np.log10((CPw[st + Wn] - CPw[st]) / (Cw[st + Wn] - Cw[st])[:, None] + 1e-14)
        shape = np.clip(S - S.max(axis=1, keepdims=True), -40, 0) / 40.0
        win = np.lib.stride_tricks.sliding_window_view(L, Wn)[st]
        pk = win.max(axis=1); meanL = (CL[st + Wn] - CL[st]) / Wn; base = (CB[st + Wn] - CB[st]) / Wn
        loud = (pk - base) >= 3.0
        if not loud.any():
            continue
        over = np.clip((pk - base) / 40.0, 0, 1.5); crest = np.clip((pk - meanL) / 20.0, 0, 1.5)
        dur = np.full(len(st), math.log2(max(0.125, ps["D"] / 1000.0)) / 4.0)
        att = win.argmax(axis=1) / max(1, Wn - 1)
        tilt = np.clip((S[:, -8:].mean(axis=1) - S[:, :8].mean(axis=1)) / 40.0, -1.5, 1.5)
        F = np.hstack([shape, 0.7 * np.stack([over, crest, dur, att, tilt], axis=1)])
        if F.shape[1] != ps["B"].shape[1]:
            continue
        dist = np.sqrt(((F[:, None, :] - ps["B"][None, :, :]) ** 2).sum(axis=2)) / math.sqrt(F.shape[1])
        sb = (np.exp(-(dist / 0.14) ** 2) * ps["W"][None, :]).max(axis=1)
        sim = sb
        if fp_ is not None and ps["E"]:                # mit gespeichertem Fingerabdruck genauer
            ft, fv = fp_
            c = ts[st] + ps["D"] / 2
            j = np.clip(np.searchsorted(ft, c), 1, max(1, len(ft) - 1)) if len(ft) > 1 else np.zeros(len(c), int)
            if len(ft):
                j0 = np.clip(j - 1, 0, len(ft) - 1); j1 = np.clip(j, 0, len(ft) - 1)
                jj = np.where(np.abs(ft[j0] - c) <= np.abs(ft[j1] - c), j0, j1)
                near = np.abs(ft[jj] - c) <= max(700, ps["D"] / 2)
                EV = np.stack([e for e, _ in ps["E"]]); EW = np.array([wt for _, wt in ps["E"]])
                cs = fv[jj] @ EV.T
                se = (np.clip((cs - 0.55) / 0.40, 0, 1) * EW[None, :]).max(axis=1)
                sim = np.where(near, 0.6 * se + 0.4 * sb, sb)
        sim = np.where(loud, sim, 0.0)
        for i in np.where(sim >= SCAN_MIN)[0]:
            win_hits.append((int(ts[st[i]]), int(ts[st[i] + Wn - 1]), name, float(sim[i]), ps["D"]))
    if not win_hits:
        return []
    # ueberlappende Fenster verschiedener Namen: der bessere gewinnt; gleiche Namen zu Bereichen zusammenfassen
    win_hits.sort(key=lambda h: -h[3])
    taken = []
    for h in win_hits:
        if any(min(h[1], t[1]) - max(h[0], t[0]) > 0.5 * (h[1] - h[0]) and t[2] != h[2] for t in taken):
            continue
        taken.append(h)
    taken.sort(key=lambda h: (h[2], h[0]))
    areas = []
    for a, b, name, sv, D in taken:
        if areas and areas[-1][2] == name and a - areas[-1][1] <= D:
            areas[-1][1] = max(areas[-1][1], b); areas[-1][3] = max(areas[-1][3], int(round(100 * sv)))
        else:
            areas.append([a, b, name, int(round(100 * sv))])
    return areas


def scan_day(sid, day, protos, t_from, t_to):
    d = day_load(day_path(sid, day))
    if d is None or not len(d["t"]):
        return None
    sp = spec_load_cached(sid, day)
    if sp is None:
        return None
    sts, sb = sp
    t = d["t"]; m = (t > t_from) & (t <= t_to)
    idx = np.where(m)[0]
    if not len(idx):
        return []
    j = np.searchsorted(sts, t[idx]); jc = np.clip(j, 0, len(sts) - 1)
    hasb = (j < len(sts)) & (sts[jc] == t[idx])
    idx, jc = idx[hasb], jc[hasb]
    if not len(idx):
        return []
    ts = t[idx]; L = np.nan_to_num(d["pk"][idx], nan=-130.0); BG = d["bg"][idx]
    T = sb[jc].astype(np.float64) / 2.0 - 130.0
    fpd = fp_load(sid, day)
    fp_ = (fpd[0], fpd[2]) if fpd is not None else None
    ps_ = _proto_sets(protos, sid)
    out = []
    hour = 3600000
    k0 = 0
    while k0 < len(ts):                               # stundenweise (Speicher), mit Ueberlappung fuer Fenster an der Grenze
        k1 = int(np.searchsorted(ts, ts[k0] + hour))
        k1e = min(len(ts), int(np.searchsorted(ts, ts[min(k1, len(ts) - 1)] + 15000)))
        out += scan_chunk(ts[k0:k1e], L[k0:k1e], BG[k0:k1e], T[k0:k1e], ps_, fp_)
        if k1 >= len(ts):
            break
        k0 = k1
    out.sort(key=lambda x: (x[2], x[0]))
    merged = []
    for x in out:
        if merged and merged[-1][2] == x[2] and x[0] <= merged[-1][1] + 1000:
            merged[-1][1] = max(merged[-1][1], x[1]); merged[-1][3] = max(merged[-1][3], x[3])
        else:
            merged.append(list(x))
    merged.sort(key=lambda x: x[0])
    return merged


def scan_start(t_from, t_to, name="", events=True, areas=True):
    with SCAN_LOCK:
        if SCAN["state"] == "running":
            return {"ok": False, "error": "busy"}
        SCAN.clear(); SCAN.update(state="running", done=0, total=0, msg="", areas=0, events=0, name=name, t_from=t_from, t_to=t_to)
    threading.Thread(target=scan_run, args=(t_from, t_to, name, events, areas), daemon=True).start()
    return {"ok": True}


def scan_run(t_from, t_to, name, events, areas):
    try:
        protos = label_protos()
        if name:
            protos = {k: v for k, v in protos.items() if k == name}
        if not protos:
            SCAN.update(state="done", msg="no_profiles"); return
        a_, b_ = dt.datetime.fromtimestamp(t_from / 1000.0).isoformat(timespec="seconds"), dt.datetime.fromtimestamp(t_to / 1000.0).isoformat(timespec="seconds")
        rows = [r for r in read_log() if a_ <= (r.get("start") or "")[:19] < b_] if events else []
        days = []
        if areas:
            day = dt.datetime.fromtimestamp(t_from / 1000.0).date()
            while day <= dt.datetime.fromtimestamp(t_to / 1000.0).date():
                for f in glob.glob(os.path.join(day_dir(), f"{day.isoformat()}_*{DAY_EXT}")):
                    days.append((os.path.basename(f)[11:-len(DAY_EXT)], day.isoformat()))
                day += dt.timedelta(days=1)
        SCAN["total"] = len(rows) + len(days) * 20
        allp = label_protos() if name else protos
        for r in rows:                                # 1) Stoerungen
            if SCAN.get("cancel"):
                break
            if r.get("datei"):
                res = prof_assign(r["datei"], r.get("quelle_id") or "main", protos=allp)
                if res and (not name or res[0] == name):
                    SCAN["events"] += 1
            SCAN["done"] += 1
        for sid, day in days:                         # 2) durchgehend
            if SCAN.get("cancel"):
                break
            day0 = int(dt.datetime.fromisoformat(day).timestamp() * 1000)
            f0, f1 = max(t_from, day0), min(t_to, day0 + 86400000)
            res = scan_day(sid, day, protos, f0, f1)
            if res is not None:
                keep = [x for x in scan_load(sid, day) if not (x[1] > f0 and x[0] < f1 and x[2] in protos)]
                scan_save(sid, day, sorted(keep + res, key=lambda x: x[0]))
                SCAN["areas"] += len(res)
            SCAN["done"] += 20
        SCAN.update(state="done")
        log(f"Neu untersucht: {SCAN['events']} Stoerungen zugeordnet, {SCAN['areas']} Bereiche markiert")
    except Exception as e:
        SCAN.update(state="done", msg="error: " + str(e)[:200])
        log("Neu untersuchen fehlgeschlagen:", repr(e))


LIVE_ART = {}            # Quelle -> letztes Ergebnis der Live-Erkennung
LIVE_WANT = {}           # Quelle -> wann zuletzt angeschaut


def live_art_worker():
    """Laufende Geraeuscherkennung fuer die Live-Ansicht: nur fuer Quellen, die gerade angezeigt werden."""
    while True:
        time.sleep(0.8)
        try:
            if not art_enabled():
                LIVE_ART.clear(); continue
            now = time.time()
            with SRC_LOCK:
                rs = [r for r in RUNNERS.values() if now - LIVE_WANT.get(r.id, 0) < 10]
            for r in rs:
                audio, _s = ram_audio(r, sec=2)
                rate = r.hist_rate
                if len(audio) < rate * 1.0:
                    continue
                last = audio[-int(rate * 1.0):].astype(np.float32)
                lv = 20 * math.log10(float(np.sqrt(np.mean(last ** 2))) / 32768.0 + 1e-9)
                base = r.status.get("base")
                if r.status.get("silent") or (base is not None and lv < base + 4):
                    LIVE_ART[r.id] = {"g": "quiet", "c": 0, "ts": int(now * 1000)}; continue
                res = classify.analyse(classify.pcm_to_float(audio[-int(rate * 1.95):].tobytes(), rate))
                top = res["top"][0]["name"] if res["top"] else ""
                if top == "Silence" and res["art"] == "other":
                    LIVE_ART[r.id] = {"g": "quiet", "c": 0, "ts": int(now * 1000)}; continue
                LIVE_ART[r.id] = {"g": res["art"], "c": res["conf"], "top": top, "ts": int(now * 1000)}
        except Exception as e:
            ART_STATE["error"] = str(e)[:200]


def art_status():
    known = art_all()
    rows = read_log()
    spuren = [r["datei"] for r in rows if (r["datei"] or "").endswith((SPUR_EXT, VIRT_EXT))]
    done = sum(1 for d in spuren if d in known and (known[d].get("g") or not is_virtual(d)))
    return {"enabled": art_enabled(), "available": classify is not None and classify.available(), "pending": len(ART_STATE["queued"]),
            "done": done, "clips": len(spuren), "error": ART_STATE["error"], "embed": bool(CFG.get("ki_embed")), "fp": fp_status()}


def art_set_manual(key, group):
    rows = read_log()
    for r, k in zip(rows, row_keys(rows)):
        if k == key:
            d = r["datei"] or event_stem(r, int(k.rsplit("|", 1)[1] or 0))
            if group and group not in ART_LABEL:
                return {"ok": False, "error": "bad group"}
            with ART_LOCK:
                e = art_all().setdefault(d, {"g": "", "c": 0, "top": [], "gs": {}, "v": 1})
                if group:
                    e["man"] = group
                else:
                    e.pop("man", None)
                art_save()
            return {"ok": True, **art_fields(d)}
    return {"ok": False, "error": "not found"}


def classify_upload(data):
    if not art_enabled() and not (classify is not None and classify.available()):
        raise ValueError("classification not available")
    return classify.analyse(classify.decode(data))


def classify_range(r, t0, t1):
    audio, _start = ram_audio(r, t0, t1)
    if not len(audio):
        raise ValueError("no audio")
    return classify.analyse(classify.pcm_to_float(audio.tobytes(), r.hist_rate))


# =====================================================================
# Video (nur Stream-Quellen wie "IP Webcam"): Bilder laufen im Arbeitsspeicher mit (Vorlauf),
# bei einem Ereignis entsteht eine stumme mp4-Datei (ohne Ton). Ohne Ereignis wird nichts gespeichert.
# =====================================================================
SOI_EOI = b"\xff\xd9\xff\xd8"
VIDEO_MAX_BYTES = 150 * 1024 * 1024
VIDEO_MAX_AGE_MS = 150000
VIDEO_Q = queue.Queue(maxsize=2)


def video_url(src):
    u = (src.get("video_url") or "").strip()
    if not u:
        base = (src.get("url") or "").strip()
        if not base:
            return ""
        u = re.sub(r"/[^/]*$", "/video", base) if re.search(r"/audio\.[a-z0-9]+$", base, re.I) else \
            re.sub(r"^(\w+://[^/]+).*$", r"\1/video", base)
    return with_login(fix_url(u), src.get("user", ""), src.get("password", ""))


def video_view_on(src):
    """Live-Bild anzeigen (aeltere Geraete ohne eigene Einstellung: wie die Aufnahme)."""
    v = src.get("video_view")
    return bool(src.get("video")) if v is None else bool(v)


def video_dir_for(src):
    return safe_dir((src or {}).get("video_dir")) or paths()[1]


def video_path(name):
    """mp4 zu einem Clip-Namen (ohne Ordnerangaben) suchen: Ordner des Geraets, sonst allgemeiner Clip-Ordner."""
    name = os.path.basename(name)
    with SRC_LOCK:
        dirs = [safe_dir(r.src.get("video_dir")) for r in RUNNERS.values()]
    for d in [x for x in dirs if x] + [paths()[1]]:
        f = os.path.join(d, name)
        if os.path.isfile(f):
            return f
    return None


class VideoBuffer:
    """Liest die Bilder (MJPEG) eines Handys und haelt die letzten Sekunden in voller Aufloesung im Speicher."""

    def __init__(self, runner):
        self.r = runner
        self.frames = collections.deque()
        self.bytes = 0
        self.lock = threading.Lock()
        self.last = 0.0                 # Zeitpunkt des letzten Bildes (time.time)
        self.size = ""
        self.error = ""
        self.fps = 0.0
        self.thread = threading.Thread(target=self.loop, name="vid-" + runner.id, daemon=True)

    def wanted(self):
        """Bilder empfangen, wenn Aufnahme oder Live-Bild eingeschaltet ist."""
        s = self.r.src
        return bool((s.get("video") or video_view_on(s)) and s.get("enabled", True) and s.get("type") == "url" and (s.get("url") or s.get("video_url")))

    def recording(self):
        return self.wanted() and bool(self.r.src.get("video"))

    def sending(self):
        return self.wanted() and time.time() - self.last < 3.0

    def key(self):
        s = self.r.src
        return (self.wanted(), video_url(s))

    def add(self, ts, jpg):
        with self.lock:
            self.frames.append((ts, jpg)); self.bytes += len(jpg)
            while self.frames and (self.bytes > VIDEO_MAX_BYTES or ts - self.frames[0][0] > VIDEO_MAX_AGE_MS):
                self.bytes -= len(self.frames.popleft()[1])

    def latest(self):
        with self.lock:
            return self.frames[-1][1] if self.frames else None

    def window(self, t0, t1):
        with self.lock:
            return [f for f in self.frames if t0 <= f[0] <= t1]

    def cmd(self):
        url = video_url(self.r.src)
        c = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error"]
        low = url.lower()
        if low.startswith(("http://", "https://")):
            c += ["-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5", "-rw_timeout", "8000000"]
        elif low.startswith("rtsp://"):
            c += ["-rtsp_transport", "tcp", "-timeout", "8000000"]
        c += ["-fflags", "nobuffer", "-i", url, "-an"]
        if low.startswith("http") and re.search(r"/(video|videofeed|mjpeg|mjpg)[^/]*$", low.split("?")[0]):
            c += ["-c:v", "copy"]                       # MJPEG unveraendert durchreichen (kaum Rechenlast)
        else:
            c += ["-c:v", "mjpeg", "-q:v", "4", "-r", "10"]
        return c + ["-f", "mjpeg", "-"]

    def loop(self):
        r = self.r
        while not r.stop.is_set():
            if not self.wanted():
                self.error = ""; self.last = 0.0
                with self.lock:
                    self.frames.clear(); self.bytes = 0
                r.stop.wait(1.0)
                continue
            key = self.key()
            try:
                self.run(key)
            except Exception as e:
                self.error = str(e)[:200]; log(f"[{r.name}] Video:", e)
            r.stop.wait(5)

    def run(self, key):
        r = self.r
        cmd = self.cmd()
        log(f"[{r.name}] Video:", " ".join("<url>" if i and cmd[i - 1] == "-i" else c for i, c in enumerate(cmd)))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        tail = collections.deque(maxlen=10)

        def drain():
            for line in iter(p.stderr.readline, b""):
                txt = line.decode(errors="replace").strip()
                if txt:
                    tail.append(re.sub(r"//[^/\s]*@", "//***@", txt))
        threading.Thread(target=drain, daemon=True).start()
        buf = bytearray(); fd = p.stdout.fileno(); n = 0; t_fps = time.time()
        try:
            while not r.stop.is_set() and self.key() == key:
                rd, _, _ = select.select([fd], [], [], 1.0)
                if not rd:
                    if p.poll() is not None or time.time() - self.last > 15:
                        break
                    continue
                chunk = os.read(fd, 262144)
                if not chunk:
                    break
                buf += chunk
                while True:
                    i = buf.find(SOI_EOI, 2)
                    if i < 0:
                        break
                    jpg = bytes(buf[:i + 2]); del buf[:i + 2]
                    if jpg[:2] == b"\xff\xd8":
                        now = time.time(); self.last = now; self.error = ""
                        self.add(int(now * 1000), jpg); n += 1
                        if now - t_fps >= 3:
                            self.fps = round(n / (now - t_fps), 1); n = 0; t_fps = now
                if len(buf) > 8 * 1024 * 1024:
                    buf.clear()
        finally:
            try:
                p.kill(); p.wait(timeout=2)
            except Exception:
                pass
            msg = re.sub(r"//[^/\s]*@", "//***@", " | ".join(tail))
            pw = r.src.get("password")
            for v in ({pw, urllib.parse.quote(pw, safe="")} if pw else ()):
                msg = msg.replace(v, "***")
            if msg and self.key() == key:
                self.error = friendly_error(msg)[:200]


def video_enqueue(runner, stem, t0, clip_s):
    vb = getattr(runner, "video", None)
    if vb is None or not vb.recording():
        return
    delay = int(runner.src.get("video_delay_ms") or 0)
    frames = [(ts - delay, j) for ts, j in vb.window(t0 + delay - 400, t0 + delay + int(clip_s * 1000) + 600)]
    if not frames:
        log(f"[{runner.name}] Kein Video fuer dieses Ereignis (keine Bilder empfangen)")
        return
    out = os.path.join(video_dir_for(runner.src), stem + ".mp4")
    job = {"out": out, "t0": t0, "clip_s": clip_s, "frames": frames, "name": runner.name,
           "rot": int(runner.src.get("video_rot") or 0), "w": CFG["video_width"], "fps": CFG["video_fps"], "crf": CFG["video_crf"]}
    try:
        VIDEO_Q.put_nowait(job)
    except queue.Full:
        log(f"[{runner.name}] Video-Warteschlange voll: Video fuer dieses Ereignis uebersprungen")


def encode_video(job):
    fps = max(1, int(job["fps"])); w = int(job["w"])
    n = max(1, int(job["clip_s"] * fps))
    fr = job["frames"]; picked = []; j = 0
    for k in range(n):
        t = job["t0"] + k * 1000.0 / fps
        while j + 1 < len(fr) and fr[j + 1][0] <= t:
            j += 1
        picked.append(fr[j][1])
    vf = f"scale=min({w}\\,iw):-2" if w > 0 else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    rot = {90: "transpose=1", 180: "hflip,vflip", 270: "transpose=2"}.get(job.get("rot", 0))
    if rot:                                        # Handy liegt gedreht: Bild im Video gerade stellen
        vf = rot + "," + vf
    os.makedirs(os.path.dirname(job["out"]), exist_ok=True)
    tmp = job["out"] + ".part.mp4"
    # Nur Bild, keine Tonspur
    cmd = ["ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg",
           "-i", "-", "-an", "-vf", vf + ",format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", str(int(job["crf"])), "-movflags", "+faststart", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=lambda: os.nice(12))

    def feed():
        try:
            for jp in picked:
                p.stdin.write(jp)
            p.stdin.close()
        except Exception:
            pass
    th = threading.Thread(target=feed, daemon=True); th.start()
    err = p.stderr.read().decode(errors="replace")[-300:]
    p.wait(timeout=600); th.join(5)
    if p.returncode == 0 and os.path.exists(tmp):
        os.replace(tmp, job["out"])
        log(f"[{job['name']}] Video gespeichert: {os.path.basename(job['out'])} ({os.path.getsize(job['out']) // 1024} KB)")
    else:
        try:
            os.remove(tmp)
        except OSError:
            pass
        log(f"[{job['name']}] Video fehlgeschlagen:", err.strip())


def video_worker():
    while True:
        job = VIDEO_Q.get()
        try:
            encode_video(job)
        except Exception as e:
            log("Video-Fehler:", e)
        finally:
            job["frames"] = None
            time.sleep(0.2)


SPUR_EXT = ".lsp"         # Laermspur: gzip-JSON mit Pegel- und Terzwerten, kein Ton


def write_wav(path, audio, rate, runner=None):
    """Echten Ton speichern (nur wenn in den Einstellungen eingeschaltet)."""
    try:
        tmp = path + ".tmp"
        with wave.open(tmp, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(int(rate))
            w.writeframes(np.asarray(audio, np.int16).tobytes())
        os.replace(tmp, path)
        return True
    except (OSError, wave.Error) as e:
        log(f"[{runner.name if runner else '?'}] Ton konnte nicht gespeichert werden:", e)
        return False


def audio_allowed(row):
    """Darf der Ton eines Eintrags abgespielt werden? Nur, wenn fuer das Geraet „Echten Ton speichern" an ist."""
    with SRC_LOCK:
        r = RUNNERS.get(row.get("quelle_id") or "main")
    c = r.cfg() if r is not None else CFG
    return bool(c.get("save_audio"))


def wav_name(row):
    """Name der WAV-Datei zu einem Eintrag (alter Clip oder zusaetzlich gespeicherter Ton), sonst ''."""
    d = os.path.basename(row.get("datei") or "")
    if not d:
        return ""
    w = d if d.endswith(".wav") else os.path.splitext(d)[0] + ".wav"
    return w if os.path.isfile(os.path.join(paths()[1], w)) else ""


def wav_allowed(fn):
    """Tondatei nur ausliefern, wenn sie zu einem Eintrag gehoert und fuer dessen Geraet „Echten Ton speichern" an ist."""
    for r in read_log():
        if wav_name(r) == fn:
            return audio_allowed(r)
    return False


def log_event_row(runner, start, dur, ev, fname, span_s):
    """Zeile in log.csv, Zaehler, MQTT (Sensoren, Ereignis, Ausloeser „ende“)."""
    out, clips, lg = paths()
    with LOG_LOCK:
        header = None
        if os.path.exists(lg):
            with open(lg, newline="", encoding="utf-8-sig", errors="replace") as f:
                header = next(csv.reader(f), None)
        with open(lg, "a", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            if not header:
                wr.writerow(LOG_HEADER); header = LOG_HEADER
            row = [start.isoformat(timespec="seconds"), round(dur, 2), round(ev["peak"], 1), round(ev["base"], 1), fname,
                   round(ev["thr"], 1), round(span_s, 1), runner.name, runner.id]
            if header == LOG_HEADER:
                wr.writerow(row)
            else:
                m = dict(zip(LOG_HEADER, row)); wr.writerow([m.get(h, "") for h in header])
    today = dt.date.today().isoformat()
    with SRC_LOCK:
        if STATE["today"] != today:
            STATE["today"], STATE["count"] = today, 0
            for r in RUNNERS.values():
                r.count_today = 0
        STATE["count"] += 1; STATE["total"] += 1
        runner.count_today += 1; runner.count_total += 1
    STATE["last"] = start.astimezone().isoformat(timespec="seconds")
    STATE["attr"] = json.dumps({"quelle": runner.name, "dauer_s": round(dur, 2), "spur_s": round(span_s, 1),
                                "spitze_dbfs": round(ev["peak"], 1), "schwelle_dbfs": round(ev["thr"], 1), "datei": fname}, ensure_ascii=False)
    pub(f"{TOPIC}/events_today", str(STATE["count"]), True)
    pub(f"{TOPIC}/last_event", STATE["last"], True)
    pub(f"{TOPIC}/last_event_attr", STATE["attr"], True)
    pub(f"{TOPIC}/event", json.dumps({"event_type": "stoerung", "quelle": runner.name, "quelle_id": runner.id, "zeit": STATE["last"],
                                      "dauer_s": round(dur, 2), "spitze_dbfs": round(ev["peak"], 1), "datei": fname}, ensure_ascii=False))
    pub_trigger(runner, "ende", zeit=STATE["last"], dauer_s=round(dur, 2), spitze_dbfs=round(ev["peak"], 1), schwelle_dbfs=round(ev["thr"], 1),
                hintergrund_dbfs=round(ev["base"], 1), datei=fname)


def save_event_virtual(ev, rate, runner, audio, dur, stem):
    """Stoerung ohne eigene Laermspur: nur der Ausschlag (kein Vor-/Nachlauf). Gespeichert wird eine Zeile in log.csv und
    in ereignisse.jsonl (Zeitraum, Werte); die Messwerte selbst stehen in der Tagesaufzeichnung. Die KI wertet den Ton des
    Ausschlags (mit 1 s Umfeld) im Arbeitsspeicher aus; danach ist er weg."""
    start = ev["start"]
    t0 = ev.get("t0") or int(start.timestamp() * 1000)
    t_end = t0 + int(len(audio) * 1000 / rate) if len(audio) else t0 + 100
    ctx = max(5, int(runner.cfg().get("ctx_s", 30) or 0)) * 1000         # Umfeld zum Anschauen (nur Anzeige)
    t_from, t_to = t0 - ctx, t_end + ctx
    fname = stem + VIRT_EXT
    meta = {"stem": stem, "sid": runner.id, "name": runner.name, "start": start.astimezone().isoformat(timespec="seconds"),
            "t0": t0, "t_end": t_end, "t_from": t_from, "t_to": t_to, "core": [t0 - t_from, t_end - t_from],
            "peak": round(ev["peak"], 1), "thr": round(ev["thr"], 1), "base": round(ev["base"], 1),
            "first": round(ev.get("first_hit", 0), 2), "last": round(ev.get("last_hit", 0), 2),
            "pre_max": ev.get("pre_max"), "pre_s": ev.get("pre_s") or 0, "ha": ev.get("ha") if ev.get("ha") is not None else ha_notes(runner.id)}
    evmeta_add(meta)
    span_s = (t_end - t0) / 1000.0
    try:
        video_enqueue(runner, stem, t0, max(1.0, span_s))
    except Exception as e:
        log(f"[{runner.name}] Video nicht gestartet:", e)
    log_event_row(runner, start, dur, ev, fname, span_s)
    if art_enabled():                            # Erkennung im Arbeitsspeicher: Ausschlag mit 1 s Umfeld
        au, a0 = ram_audio(runner, t0 - 1000, t_end + 1000)
        if len(au) >= 4000 and a0 is not None:
            art_enqueue(fname, runner.id, 0, {"audio": au, "rate": runner.hist_rate, "off": a0 - t_from, "stem": stem, "wav": False})
        del au
    elif profiles_all() or labels_all():         # ohne KI: Profile nur ueber Spektrum und Pegel
        threading.Timer(3.0, lambda: prof_assign(fname, runner.id)).start()
    try:
        plists_auto(runner, stem, start.astimezone())
    except Exception as e:
        log(f"[{runner.name}] Protokollliste nicht aktualisiert:", e)
    log(f"[{runner.name}] Stoerung {start:%d.%m. %H:%M:%S}  {dur:.2f} s  Spitze {ev['peak']:.1f}  Schwelle {ev['thr']:.1f} dBFS")


def save_event(ev, rate, runner):
    """Ereignis abschliessen. Gespeichert werden nur Messwerte (Laermspur) und die Ergebnisse der Erkennung;
    der Ton liegt nur im Arbeitsspeicher, wird dort ausgewertet und danach verworfen."""
    out, clips, lg = paths()
    os.makedirs(clips, exist_ok=True)
    start = ev["start"]
    audio = np.concatenate(ev["blocks"]) if ev["blocks"] else np.zeros(0, np.int16)
    ev["blocks"] = None
    clip_s = len(audio) / rate                                   # Vorlauf + Ereignis + Nachlauf
    dur = max(0.02, ev["last_hit"] - ev["first_hit"] + 0.02)     # Dauer ueber der Schwelle
    gdir = os.path.join(clips, "graphen")
    base_name = start.strftime("%Y%m%d_%H%M%S") + ("" if runner.id == "main" else "_" + runner.id)
    stem, i = base_name, 1
    em = evmeta_all()
    while os.path.exists(f"{clips}/{stem}.wav") or os.path.exists(f"{gdir}/{stem}.json") or os.path.exists(f"{clips}/{stem}{SPUR_EXT}") or stem in em:
        stem = f"{base_name}_{i}"; i += 1
    if ev.get("virt"):
        return save_event_virtual(ev, rate, runner, audio, dur, stem)
    fname = stem + SPUR_EXT
    ctx = int(runner.cfg().get("ctx_s", 30) or 0) * 1000
    t0 = ev.get("t0") or int(start.timestamp() * 1000)
    with runner.rlock:
        first = runner.spur[0][0] - Terz.STEP_MS if runner.spur else t0
    t_from = max(t0 - ctx, first)
    t_to = t0 + int(clip_s * 1000) + ctx
    job = {"stem": stem, "path": os.path.join(clips, fname), "t_from": t_from, "t_to": t_to, "due": t_to + 300,
           "meta": {"start": start.astimezone().isoformat(timespec="seconds"), "peak": round(ev["peak"], 1),
                    "thr": round(ev["thr"], 1), "base": round(ev["base"], 1), "core": [t0 - t_from, t0 - t_from + int(clip_s * 1000)],
                    "pre_max": ev.get("pre_max"), "pre_s": ev.get("pre_s") or 0, "ha": ev.get("ha") if ev.get("ha") is not None else ha_notes(runner.id)}}
    span_s = (t_to - t_from) / 1000.0
    try:
        write_spur(runner, job, final=False)
    except Exception as e:
        log(f"[{runner.name}] Laermspur nicht gespeichert:", e)
    with runner.plock:
        runner.pending.append(job)
    co_enqueue(runner, stem, t0, t_from, t_to, clip_s)
    try:
        video_enqueue(runner, stem, t0, clip_s)
    except Exception as e:
        log(f"[{runner.name}] Video nicht gestartet:", e)
    log_event_row(runner, start, dur, ev, fname, span_s)
    # Echter Ton (WAV) nur, wenn ausdruecklich eingeschaltet (Standard: aus). Mit Stimm-Sicherung erst nach der Pruefung durch die KI.
    c = runner.cfg()
    want_wav = bool(c.get("save_audio")) and len(audio) > 0
    guard = want_wav and bool(c.get("audio_novoice", True))
    if want_wav and not guard:
        write_wav(os.path.join(clips, stem + ".wav"), audio, rate, runner)
    if len(audio) and art_enabled():          # Erkennung im Arbeitsspeicher; danach ist der Ton weg
        if not art_enqueue(fname, runner.id, 0, {"audio": audio, "rate": rate, "off": t0 - t_from, "stem": stem, "wav": guard}) and guard:
            log(f"[{runner.name}] Ton nicht gespeichert: Stimm-Pruefung nicht moeglich (Warteschlange voll)")
    elif guard:
        log(f"[{runner.name}] Ton nicht gespeichert: Stimm-Sicherung braucht die Geraeuscherkennung (Einstellungen -> Allgemein)")
    del audio
    try:
        plists_auto(runner, stem, start.astimezone())
    except Exception as e:
        log(f"[{runner.name}] Protokollliste nicht aktualisiert:", e)
    log(f"[{runner.name}] Ereignis {start:%d.%m. %H:%M:%S}  {dur:.2f} s (Spur {span_s:.0f} s)  Spitze {ev['peak']:.1f}  Schwelle {ev['thr']:.1f} dBFS")


SPUR_CHAIN_LOCK = threading.Lock()


def chain_path():
    return os.path.join(paths()[1], "spuren_kette.json")


def write_spur(runner, job, final=True):
    """Laermspur eines Ereignisses schreiben (Rahmen aus dem Arbeitsspeicher von t_from bis t_to).
    final: Umfeld nach dem Ereignis ist komplett; dann wird die Pruefsumme in die Kette eingetragen
    (jede Spur nennt die Pruefsumme der vorherigen Spur desselben Geraets)."""
    t_from, t_to = job["t_from"], job["t_to"]
    with runner.rlock:
        fr = [x for x in runner.spur if t_from < x[0] <= t_to]
    m = job["meta"]
    data = {"v": 2, "fmt": "laermspur", "step": Terz.STEP_MS, "t0": t_from, "start": m["start"], "src": runner.id,
            "name": runner.name, "clip": os.path.basename(job["path"]), "clip_s": round((t_to - t_from) / 1000.0, 2),
            "core": m["core"], "peak": m["peak"], "thr": m["thr"], "base": m["base"], "bands": Terz.CENTERS,
            "pre_max": m.get("pre_max"), "pre_s": m.get("pre_s") or 0,      # lautester Pegel davor (ohne Stoerungen), Zeitraum in s
            "ha": m.get("ha") or [],                                         # Zustaende aus Home Assistant zur Zeit der Stoerung (z. B. Fernseher an/aus)
            "unit": "dBFS", "refs": runner.src.get("refs") or [], "final": bool(final),
            # Rahmen: [Ende in ms ab t0, Spitze, Hintergrund, Schwelle, Zustand (0/1/2), Terzbaender (b64, 0,5 dB ab -130), Mittelpegel]
            "recs": [[x[0] - t_from, x[1], x[3], x[4], x[5], x[6], x[2]] for x in fr]}
    if final:
        with SPUR_CHAIN_LOCK:
            ch = read_json(chain_path()) if os.path.exists(chain_path()) else {}
            if not isinstance(ch, dict):
                ch = {}
            prev = ch.get(runner.id) or {}
            data["prev"] = {"file": prev.get("file", ""), "sha256": prev.get("sha256", "")}
            _write_gz(job["path"], data)
            ch[runner.id] = {"file": os.path.basename(job["path"]), "sha256": file_sha256(job["path"])}
            tmp = chain_path() + ".tmp"
            with open(tmp, "w") as f:
                json.dump(ch, f)
            os.replace(tmp, chain_path())
    else:
        _write_gz(job["path"], data)


def _write_gz(path, data):
    tmp = path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
        json.dump(data, f, separators=(",", ":"))
    os.replace(tmp, path)


def flush_pending(runner, now_ms=None, force=False):
    """Faellige Laermspuren (Umfeld nach dem Ereignis vorbei) endgueltig schreiben."""
    if not runner.pending:
        return
    with runner.plock:
        jobs, runner.pending = runner.pending, []
    keep = []
    for job in jobs:
        if force or (now_ms is not None and now_ms >= job["due"]):
            try:
                write_spur(runner, job, final=True)
            except Exception as e:
                log(f"[{runner.name}] Laermspur nicht abgeschlossen:", e)
        else:
            keep.append(job)
    with runner.plock:
        runner.pending = keep + runner.pending


def load_graph(path):
    """Grafikdaten laden: Laermspur (.lsp, gzip) oder alte Grafik (.json)."""
    if path.endswith(SPUR_EXT):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------------------------
# Stoerungen ohne eigene Laermspur (ab 1.40, ohne echten Ton): die Messwerte kommen aus der Tagesaufzeichnung.
# Je Stoerung nur eine Zeile in ereignisse.jsonl (Zeitraum, Spitze, Schwelle ...); "datei" endet auf .ltv.
# ---------------------------------------------------------------------------------------------
VIRT_EXT = ".ltv"
VIRT_END_FRAMES = 25          # 0,5 s (je 20 ms) unter der Schwelle beendet den Ausschlag
VIRT_MAX_S = 300
EVMETA = {"size": -1, "data": {}}
EVMETA_LOCK = threading.Lock()


def evmeta_path():
    return os.path.join(paths()[1], "ereignisse.jsonl")


def evmeta_all():
    p = evmeta_path()
    try:
        size = os.path.getsize(p)
    except OSError:
        return {}
    with EVMETA_LOCK:
        if size != EVMETA["size"]:
            start = EVMETA["size"] if 0 < EVMETA["size"] < size else 0
            d = EVMETA["data"] if start else {}
            try:
                with open(p, "rb") as fh:
                    fh.seek(start)
                    for line in fh.read().decode("utf-8", "replace").splitlines():
                        try:
                            e = json.loads(line)
                            d[e["stem"]] = e
                        except (ValueError, KeyError, TypeError):
                            pass
            except OSError:
                pass
            EVMETA["size"], EVMETA["data"] = size, d
        return EVMETA["data"]


def evmeta_add(e):
    p = evmeta_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with EVMETA_LOCK:
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n")


def is_virtual(datei):
    return (datei or "").endswith(VIRT_EXT)


def day_frames(sid, t_from, t_to):
    """Messwerte je 125 ms eines Geraets zwischen t_from und t_to (ms): Tagesaufzeichnung, dazu die noch nicht
    geschriebenen Rahmen aus dem Arbeitsspeicher. Liefert Liste [ts, Spitze, Mittel, Hintergrund, Schwelle, Zustand, Terz-b64]."""
    out = {}
    d0 = dt.datetime.fromtimestamp(t_from / 1000.0).date(); d1 = dt.datetime.fromtimestamp(t_to / 1000.0).date()
    day = d0
    while day <= d1:
        ds = day.isoformat()
        d = day_load(day_path(sid, ds))
        if d is not None and len(d["t"]):
            t = d["t"]; i0, i1 = np.searchsorted(t, t_from, "right"), np.searchsorted(t, t_to, "right")
            sp = spec_load_cached(sid, ds)
            sts, sb = sp if sp is not None else (None, None)
            for i in range(i0, i1):
                ts = int(t[i])
                f = lambda a: None if not np.isfinite(a[i]) else round(float(a[i]), 1)
                bands = ""
                if sts is not None:
                    j = int(np.searchsorted(sts, ts))
                    if j < len(sts) and sts[j] == ts:
                        bands = base64.b64encode(bytes(sb[j])).decode()
                act = d["act"][i]
                out[ts] = [ts, f(d["pk"]), f(d["eq"]), f(d["bg"]), f(d["thr"]), int(act) if np.isfinite(act) else 0, bands]
        day += dt.timedelta(days=1)
    with SRC_LOCK:
        r = RUNNERS.get(sid)
    if r is not None:
        with r.rlock:
            ram = [x for x in r.spur if t_from < x[0] <= t_to and x[0] not in out]
        for x in ram:
            out[x[0]] = [x[0], x[1], x[2], x[3], x[4], x[5], x[6]]
    return [out[k] for k in sorted(out)]


SPEC_CACHE = {}


def spec_load_cached(sid, day):
    """spec_load mit Zwischenspeicher je Tag (neu gelesen, wenn sich die Dateien aendern)."""
    fs = [spec_path(sid, day)] + sorted(glob.glob(os.path.join(day_dir(), f"{day}_{glob.escape(sid)}_[0-9][0-9].ltp")))
    key = tuple((f, os.path.getsize(f)) for f in fs if os.path.exists(f))
    c = SPEC_CACHE.get((sid, day))
    if c and c[0] == key:
        return c[1]
    v = spec_load(sid, day)
    if len(SPEC_CACHE) > 6:
        SPEC_CACHE.pop(next(iter(SPEC_CACHE)))
    SPEC_CACHE[(sid, day)] = (key, v)
    return v


def virtual_graph(meta, sid=None, name=None):
    """Grafikdaten (wie eine Laermspur) einer Stoerung aus der Tagesaufzeichnung; sid: anderes Geraet, gleicher Zeitraum."""
    sid = sid or meta.get("sid") or "main"
    t_from, t_to = int(meta["t_from"]), int(meta["t_to"])
    fr = day_frames(sid, t_from, t_to)
    with SRC_LOCK:
        r = RUNNERS.get(sid)
    nm = name or (r.name if r is not None else meta.get("name") or sid)
    own = sid == (meta.get("sid") or "main")
    return {"v": 2, "fmt": "laermspur", "virtual": True, "step": Terz.STEP_MS, "t0": t_from, "start": meta.get("start"), "src": sid, "name": nm,
            "clip": meta.get("stem", "") + VIRT_EXT, "clip_s": round((t_to - t_from) / 1000.0, 2), "core": meta.get("core") if own else meta.get("core"),
            "peak": meta.get("peak") if own else (max((x[1] for x in fr if x[1] is not None), default=None)),
            "thr": meta.get("thr") if own else None, "base": meta.get("base") if own else None, "bands": Terz.CENTERS,
            "pre_max": meta.get("pre_max") if own else None, "pre_s": meta.get("pre_s") or 0 if own else 0, "ha": meta.get("ha") or [] if own else [],
            "unit": "dBFS", "refs": (r.src.get("refs") if r is not None else []) or [], "final": time.time() * 1000 > t_to + 2000,
            "recs": [[x[0] - t_from, x[1], x[3], x[4], x[5], x[6], x[2]] for x in fr]}


def meta_of(row):
    return evmeta_all().get(os.path.splitext(os.path.basename(row.get("datei") or ""))[0])


def event_graph(row, n=0):
    """Grafikdaten eines Eintrags: eigene Laermspur/alte Grafik oder - bei .ltv - aus der Tagesaufzeichnung."""
    if is_virtual(row.get("datei")):
        m = meta_of(row)
        return virtual_graph(m) if m else None
    f = graph_file(row, n)
    if not f:
        return None
    try:
        return load_graph(f)
    except (OSError, ValueError):
        return None


def graph_file(row, n=0):
    """Grafik-Datei zu einem Protokolleintrag (gleicher Name wie der Clip, sonst ueber Zeit und Quelle)."""
    _, clips, _ = paths()
    gdir = os.path.join(clips, "graphen")
    d = row.get("datei") or ""
    if d.endswith(SPUR_EXT):
        f = os.path.join(clips, os.path.basename(d))
        return f if os.path.isfile(f) else None
    if d:
        f = os.path.join(gdir, os.path.splitext(os.path.basename(d))[0] + ".json")
        return f if os.path.isfile(f) else None
    try:
        st = dt.datetime.fromisoformat(row.get("start", ""))
    except ValueError:
        return None
    qid = row.get("quelle_id") or "main"
    base = st.strftime("%Y%m%d_%H%M%S") + ("" if qid == "main" else "_" + qid)
    cands = sorted(glob.glob(os.path.join(gdir, glob.escape(base) + ".json")) + glob.glob(os.path.join(gdir, glob.escape(base) + "_*.json")))
    cands = [c for c in cands if not os.path.exists(os.path.join(clips, os.path.splitext(os.path.basename(c))[0] + ".wav"))]
    return cands[n] if n < len(cands) else (cands[0] if cands else None)


def has_video(row):
    d = row.get("datei") or ""
    return bool(d) and video_path(os.path.splitext(os.path.basename(d))[0] + ".mp4") is not None


def has_audio(row):
    """Eintrag mit Tonaufnahme: alter Clip (vor 1.25) oder zusaetzlich gespeicherter Ton."""
    return bool(wav_name(row))


def event_detail(key):
    rows = read_log()
    for r, k in zip(rows, row_keys(rows)):
        if k == key:
            n = int(k.rsplit("|", 1)[1] or 0)
            g = event_graph(r, n)
            stem = event_stem(r, n)
            ki = ki_load(stem)
            lang = "en" if CFG.get("language") == "en" else "de"
            return {"ok": True, "row": dict(r, video=has_video(r)), "graph": g,
                    "art": art_all().get(r["datei"] or stem) or None,
                    "notes": notes_for(stem), "note_tags": NOTE_TAGS,
                    "enote": enotes_for(stem)[0], "snote": enotes_for(stem)[1], "plists": plists_of(stem),
                    "cmp": co_compare(r, g, stem),
                    "fnotes": (lambda ab: fnotes_in(ab[0], ab[1], r.get("quelle_id") or "main") if ab[0] is not None else [])(row_span(r)),
                    "ki": {"marks": ki.get("marks") or [], "top": ki.get("top") or [], "emb": bool(ki.get("emb")),
                           "subs": sub_events(ki.get("marks"), g),          # immer aus Markern und Messwerten (schnell, stets aktuell)
                           "kinds": kinds_summary(ki.get("marks"), g)} if ki else None,
                    "labels": labels_for(stem), "sugg": suggestions_for(stem, g, ki) if g else [], "names": label_names(),
                    "prof": art_fields(r.get("datei") or ""), "pnames": [p_["name"] for p_ in profile_names()],
                    "fine": classify.fine_meta(lang) if classify is not None else {},
                    "legacy": bool((r["datei"] or "").endswith(".wav")),
                    "wav": wav_name(r) if audio_allowed(r) else "", "has_wav": bool(wav_name(r)),
                    "wav_skip": (ki or {}).get("wav") if (ki or {}).get("wav") in ("voice", "error") else "",
                    "art_label": {k: v[0] for k, v in ART_LABEL.items()}}
    return {"ok": False, "error": "not found"}


def row_keys(rows):
    """Eindeutiger Schluessel je Eintrag: start|quelle|datei|n (n = wievielter gleicher Eintrag)."""
    seen = collections.Counter()
    keys = []
    for r in rows:
        base = f"{r.get('start', '')}|{r.get('quelle_id', '') or 'main'}|{r.get('datei', '')}"
        keys.append(f"{base}|{seen[base]}")
        seen[base] += 1
    return keys


def recount():
    """Zaehler und MQTT nach dem Loeschen neu setzen (unter LOG_LOCK aufrufen)."""
    rows = read_log(); today = dt.date.today().isoformat()
    with SRC_LOCK:
        STATE["count"] = sum(1 for r in rows if r["start"].startswith(today)); STATE["total"] = len(rows)
        for rn in RUNNERS.values():
            mine = [x for x in rows if x["quelle_id"] == rn.id]
            rn.count_total = len(mine); rn.count_today = sum(1 for x in mine if x["start"].startswith(today))
    if rows:
        lr = rows[-1]
        try:
            STATE["last"] = dt.datetime.fromisoformat(lr["start"]).astimezone().isoformat(timespec="seconds")
        except ValueError:
            pass
        STATE["attr"] = json.dumps({"quelle": lr["quelle"], "dauer_s": fnum(lr["dauer_s"]), "spitze_dbfs": fnum(lr["spitze_dbfs"]),
                                    "datei": lr["datei"]}, ensure_ascii=False)
    else:
        STATE["last"], STATE["attr"] = None, None
    pub(f"{TOPIC}/events_today", str(STATE["count"]), True)
    pub(f"{TOPIC}/last_event", STATE["last"] or "", True)
    pub(f"{TOPIC}/last_event_attr", STATE["attr"] or "{}", True)


def delete_events(keys):
    """Loescht Eintraege aus log.csv. Nichts geht unwiderruflich verloren:
    - vorheriger Stand des Logs: log_vor_loeschen_<Zeit>.csv
    - geloeschte Zeilen zusaetzlich in geloescht.csv
    - Clips wandern in clips/geloescht/ (Papierkorb)."""
    want = collections.Counter(str(k)[:240] for k in (keys if isinstance(keys, list) else [])[:5000])
    if not want:
        return 0
    out, clips, lg = paths()
    removed, files, gone_rows, gone_stems = 0, [], [], []
    with LOG_LOCK:
        if not os.path.exists(lg):
            return 0
        with open(lg, newline="", encoding="utf-8-sig", errors="replace") as fh:
            rows = list(csv.reader(fh))
        if not rows:
            return 0
        hdr = rows[0]
        body = [r for r in rows[1:] if r]
        dicts = [dict(zip(hdr, r)) for r in body]
        keep = [hdr]
        for r, d, k in zip(body, dicts, row_keys(dicts)):
            if want.get(k):
                want[k] -= 1; removed += 1; gone_rows.append(r)
                if d.get("datei"):
                    files.append(os.path.basename(d["datei"]))
                    files.append(os.path.splitext(os.path.basename(d["datei"]))[0] + ".mp4")
                    if d["datei"].endswith(SPUR_EXT):
                        files.append(os.path.splitext(os.path.basename(d["datei"]))[0] + ".wav")
                gf = graph_file(d, int(k.rsplit("|", 1)[1] or 0))
                st_ = event_stem(d, int(k.rsplit("|", 1)[1] or 0))
                gone_stems.append(st_)
                if gf and not gf.endswith(SPUR_EXT):
                    files.append(os.path.join("graphen", os.path.basename(gf)))
                if os.path.exists(ki_path(st_)):
                    files.append(os.path.join("ki", st_ + ".json"))
                files.extend(os.path.join("mit", os.path.basename(f)) for f in co_files(st_))     # mitgespeicherte Spuren der anderen Geraete
            else:
                keep.append(r)
        if removed:
            bk = os.path.join(out, time.strftime("log_vor_loeschen_%Y%m%d_%H%M%S"))
            n = 0
            while os.path.exists(bk + (f"_{n}" if n else "") + ".csv"):
                n += 1
            shutil.copy2(lg, bk + (f"_{n}" if n else "") + ".csv")
            gl = os.path.join(out, "geloescht.csv")
            new = not os.path.exists(gl)
            with open(gl, "a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if new:
                    w.writerow(["geloescht_am"] + hdr)
                for r in gone_rows:
                    w.writerow([dt.datetime.now().isoformat(timespec="seconds")] + r)
            tmp = lg + ".tmp"
            with open(tmp, "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(keep)
                fh.flush(); os.fsync(fh.fileno())
            os.replace(tmp, lg)
            trash = os.path.join(clips, "geloescht")
            for b in files:
                f = os.path.join(clips, b)
                if b.endswith(".mp4"):
                    f = video_path(b) or f
                try:
                    if (b.endswith(".wav") or b.endswith(".json") or b.endswith(".mp4") or b.endswith(SPUR_EXT)) and os.path.isfile(f):
                        dst_ = os.path.join(trash, "mit") if b.startswith("mit" + os.sep) else trash
                        os.makedirs(dst_, exist_ok=True)
                        os.replace(f, os.path.join(dst_, os.path.basename(b)))
                except OSError as e:
                    log("Clip konnte nicht verschoben werden:", b, e)
            recount()
            notes_trash(gone_stems)
            with PLISTS_LOCK:                          # geloeschte Ereignisse auch aus den Protokolllisten nehmen
                d_ = plists_all(); ch_ = False
                for m_ in d_["mem"].values():
                    for st_ in gone_stems:
                        if m_.pop(st_, None) is not None:
                            ch_ = True
                if ch_:
                    plists_save()
            with LABELS_LOCK:
                if any(st_ in labels_all() for st_ in gone_stems):
                    for st_ in gone_stems:
                        labels_all().pop(st_, None)
                    labels_save()
    if removed:
        log(f"{removed} Eintrag/Eintraege geloescht, zugehoerige Dateien in clips/geloescht verschoben")
    return removed


# =====================================================================
# Pegelverlauf (1 Wert pro Minute und Quelle, nur Zahlen) und Nachtbericht
# Zeiten werden mit UTC-Versatz gespeichert, damit Sommer-/Winterzeit stimmt.
# =====================================================================
LEVEL_LOCK = threading.Lock()
LEVEL_HEADER = ["zeit", "quelle_id", "median_dbfs", "max_dbfs", "hintergrund_dbfs", "schwelle_dbfs", "stoerung_anteil"]
LEVEL_CACHE = {}


def levels_dir():
    out, _, _ = paths()
    return os.path.join(out, "pegel")


def write_level(sid, minute, med, mx, base, thr, act):
    t = dt.datetime.fromtimestamp(minute * 60).astimezone()
    d = levels_dir(); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, t.strftime("%Y-%m-%d") + ".csv")
    row = [t.isoformat(timespec="minutes"), sid, round(med, 1), round(mx, 1),
           "" if base is None else round(base, 1), "" if thr is None else round(thr, 1), round(min(1.0, act), 2)]
    with LEVEL_LOCK:
        new = not os.path.exists(f)
        with open(f, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(LEVEL_HEADER)
            w.writerow(row)


def aware(t):
    """Naive Zeit = Ortszeit des Servers; mit Zeitzone versehen."""
    return t.astimezone() if t.tzinfo is None else t


def level_file(day):
    """Zeilen einer Tagesdatei, zwischengespeichert bis sich die Datei aendert."""
    f = os.path.join(levels_dir(), day.isoformat() + ".csv")
    try:
        st = os.stat(f)
    except OSError:
        return []
    key = (st.st_mtime_ns, st.st_size)
    c = LEVEL_CACHE.get(f)
    if c and c[0] == key:
        return c[1]
    with LEVEL_LOCK:
        with open(f, newline="", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    rows = []
    for r in csv.DictReader(raw.splitlines()):
        try:
            rows.append((aware(dt.datetime.fromisoformat(r["zeit"])), r))
        except (ValueError, KeyError, TypeError):
            continue
    if len(LEVEL_CACHE) > 40:
        LEVEL_CACHE.clear()
    LEVEL_CACHE[f] = (key, rows)
    return rows


def read_levels(start, end):
    """Minutenwerte zwischen start und end (Zeiten mit Zeitzone)."""
    out = []
    day = (start - dt.timedelta(days=1)).date()
    while day <= end.date() + dt.timedelta(days=1):
        out.extend((t, r) for t, r in level_file(day) if start <= t < end)
        day += dt.timedelta(days=1)
    return out


def fnum(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def night_window(date, src="all"):
    """Zeitraum des Berichts fuer date: die eingestellte Erfassungszeit (z. B. 22:00 bis 06:00), ohne Erfassungszeit der ganze Tag.
    Fuer ein einzelnes Geraet mit eigenen Einstellungen gilt dessen Erfassungszeit."""
    c = CFG
    if src != "all":
        with SRC_LOCK:
            r = RUNNERS.get(src)
        if r is not None:
            c = r.cfg()
    a, b = parse_t(c["active_from"]), parse_t(c["active_to"])
    if a is None or b is None or a == b:                 # keine Erfassungszeit: ganzer Tag 00:00-24:00
        return aware(dt.datetime.combine(date, dt.time())), aware(dt.datetime.combine(date + dt.timedelta(days=1), dt.time()))
    start = dt.datetime.combine(date, dt.time(a // 60, a % 60))
    end = dt.datetime.combine(date + dt.timedelta(days=1 if b <= a else 0), dt.time(b // 60, b % 60))
    return aware(start), aware(end)


def night_events(rows, start, end, src):
    ev = []
    for r in rows:
        if src != "all" and r["quelle_id"] != src:
            continue
        try:
            t = aware(dt.datetime.fromisoformat(r["start"]))
        except (ValueError, TypeError):
            continue
        if start <= t < end:
            ev.append((t, r))
    return ev


def night_summary(evs, start, end, covered):
    """covered = Menge der Minuten (Versatz ab start), fuer die ein Pegelwert vorliegt.
    Nur diese Minuten zaehlen fuer 'stoerungsfrei' und 'laengste Ruhe' – nicht aufgezeichnete Zeit gilt nicht als ruhig."""
    total = (end - start).total_seconds() / 60.0
    minutes = set()
    loud = None
    tsum = 0.0
    for t, r in evs:
        d = fnum(r["dauer_s"]) or 0.02
        tsum += d
        o = (t - start).total_seconds() / 60.0
        for m in range(int(o), int(o + max(d, 1) / 60.0) + 1):
            minutes.add(m)
        p = fnum(r["spitze_dbfs"])
        if p is not None and (loud is None or p > loud[0]):
            loud = (p, t.strftime("%H:%M"))
    rec = len(covered)
    dist_cov = len(minutes & covered)
    longest = run = 0
    for m in range(int(math.ceil(total))):
        if m in covered and m not in minutes:
            run += 1; longest = max(longest, run)
        else:
            run = 0
    return {"count": len(evs), "minutes": total, "recorded_min": rec, "disturbed_min": len(minutes),
            "quiet_pct": round(100.0 * (1 - dist_cov / rec), 1) if rec else None,
            "event_s": round(tsum, 1), "loudest": loud[0] if loud else None, "loudest_at": loud[1] if loud else None,
            "longest_quiet_min": longest if rec else None}


def pre_text(g, peak):
    """„9,0 dB über dem lautesten Pegel der 10 min davor (−41,0 dBFS)“ – nur bei Laermspuren ab 1.28."""
    if not g or g.get("pre_max") is None or peak is None or not g.get("pre_s"):
        return ""
    d = peak - g["pre_max"]; ps = int(g["pre_s"]); w = f"{ps} s" if ps < 60 else f"{round(ps / 60)} min"
    if d > 0:
        return f'{d:.1f} dB über dem lautesten Pegel der {w} davor ({g["pre_max"]:.1f} dBFS, ohne Störungen)'
    return f'nicht lauter als der lauteste Pegel der {w} davor ({g["pre_max"]:.1f} dBFS)'


def fmt_dur(sec):
    return f"{sec:.2f} s" if sec < 10 else (f"{sec:.1f} s" if sec < 60 else f"{int(sec // 60)} min {int(sec % 60)} s")


def src_name(src):
    if src == "all":
        return None
    with SRC_LOCK:
        r = RUNNERS.get(src)
    return r.name if r else src



# =====================================================================
# Notizen zu Zeitpunkten im Clip (notes.json neben den Clips, Schluessel = Clip-Stamm)
# =====================================================================
NOTES_LOCK = threading.RLock()
NOTES = {"data": None}
NOTE_TAGS = {   # Schnell-Tags: Gruppe -> Schluessel (Beschriftung im Browser)
    "src": ["oben", "unten", "nebenan", "treppenhaus", "draussen", "unklar"],
    "kind": ["klopfen", "schritte", "musik", "stimmen", "tuer", "moebel", "bohren", "hund"],
    "lvl": ["leicht", "deutlich", "stark"],
    "eff": ["aufgewacht", "kind_geweckt", "kein_schlaf", "gestoert"],
    "act": ["geklingelt", "angesprochen", "verwaltung", "polizei"],
    "misc": ["zeuge", "serie"],
}
NOTE_TAG_SET = {t for v in NOTE_TAGS.values() for t in v}
NOTES_MAX_PER, NOTES_MAX_ALL, NOTE_TEXT_MAX = 50, 20000, 500


def notes_path():
    return os.path.join(paths()[1], "notes.json")


def notes_all():
    with NOTES_LOCK:
        if NOTES["data"] is None:
            f = notes_path(); d = {}
            if os.path.exists(f):
                try:
                    with open(f, encoding="utf-8") as fh:
                        d = json.load(fh)
                except (OSError, ValueError) as e:      # nie stillschweigend ueberschreiben: defekte Datei beiseite legen
                    bad = f + time.strftime(".defekt_%Y%m%d_%H%M%S")
                    try:
                        os.replace(f, bad)
                    except OSError:
                        pass
                    log("notes.json unlesbar, gesichert als", os.path.basename(bad), e)
                    d = {}
            if not isinstance(d, dict):
                d = {}
            d.setdefault("v", 1); d.setdefault("notes", {}); d.setdefault("trash", {})
            d.setdefault("enote", {}); d.setdefault("snote", {})   # je Gesamtereignis eine Notiz, je Einzelereignis eine Notiz
            NOTES["data"] = d
        return NOTES["data"]


def notes_save():
    with NOTES_LOCK:
        f = notes_path(); os.makedirs(os.path.dirname(f), exist_ok=True)
        tmp = f + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(notes_all(), fh, ensure_ascii=False, separators=(",", ":"))
            fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, f)


def event_stem(row, n=0):
    """Gemeinsamer Name von Clip, Video und Grafik eines Eintrags; ohne beides: Zeit und Quelle."""
    d = row.get("datei") or ""
    if d:
        return os.path.splitext(os.path.basename(d))[0]
    gf = graph_file(row, n)
    if gf:
        return os.path.splitext(os.path.basename(gf))[0]
    return "row_" + re.sub(r"[^0-9A-Za-z_]", "", (row.get("start") or "").replace("T", "_")) + "_" + (row.get("quelle_id") or "main")


def event_t0(row, n=0):
    """Beginn des Clips in ms (aus der Grafik exakt, sonst geschaetzt). Liefert (t0_ms, ungefaehr)."""
    if is_virtual(row.get("datei")):
        m = meta_of(row)
        if m:
            return int(m["t_from"]), False
    gf = graph_file(row, n)
    if gf:
        try:
            t0 = load_graph(gf).get("t0")
            if isinstance(t0, (int, float)):
                return int(t0), False
        except (OSError, ValueError):
            pass
    try:
        st = aware(dt.datetime.fromisoformat(row["start"]))
    except (ValueError, TypeError, KeyError):
        return None, True
    pre = min(float(CFG.get("pre_roll_s", 5) or 0), fnum(row.get("clip_s")) or 0)
    return int((st.timestamp() - pre) * 1000), True


def is_quiet_time(t):
    """Ruhezeit (einstellbar, Standard 22-6 Uhr) oder Sonntag."""
    if CFG.get("quiet_sunday", True) and t.weekday() == 6:
        return True
    a, b = parse_t(CFG.get("quiet_from") or ""), parse_t(CFG.get("quiet_to") or "")
    if a is None or b is None or a == b:
        return False
    m = t.hour * 60 + t.minute
    return a <= m < b if a < b else (m >= a or m < b)


def note_public(nt):
    t = dt.datetime.fromtimestamp(nt["t"] / 1000.0).astimezone() if nt.get("t") else None
    return dict(nt, abs=t.isoformat(timespec="milliseconds") if t else "", clock=t.strftime("%H:%M:%S") if t else "",
                date=t.strftime("%Y-%m-%d") if t else "", rz=bool(t and is_quiet_time(t)))


def notes_for(stem):
    with NOTES_LOCK:
        return [note_public(n) for n in sorted(notes_all()["notes"].get(stem, []), key=lambda x: x.get("off", 0))]


def note_count(stem):
    """Alle Notizen eines Ereignisses: an Zeitstellen, zum Gesamtereignis und zu Einzelereignissen."""
    a = notes_all()
    return len(a["notes"].get(stem, [])) + (1 if stem in a["enote"] else 0) + len(a["snote"].get(stem) or {})


def find_row(key):
    rows = read_log()
    for r, k in zip(rows, row_keys(rows)):
        if k == key:
            return r, int(k.rsplit("|", 1)[1] or 0)
    return None, 0


def clean_note_input(data, clip_s):
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(data.get("text") or "")).strip()[:NOTE_TEXT_MAX]
    tags = [t for t in (data.get("tags") or []) if isinstance(t, str) and t in NOTE_TAG_SET][:12] if isinstance(data.get("tags"), list) else []
    witness = re.sub(r"[\x00-\x1f]", "", str(data.get("witness") or "")).strip()[:80]
    try:
        off = float(data.get("off"))
    except (TypeError, ValueError):
        off = None
    if off is not None:
        if not math.isfinite(off):
            off = None
        else:
            off = round(max(0.0, min(off, (clip_s or 600) + 0.5)), 2)
    return off, text, list(dict.fromkeys(tags)), witness


def note_change(action, data):
    """action: add / edit / del. Antwort: aktuelle Notizen des Ereignisses."""
    key = str(data.get("k") or "")[:240]
    row, n = find_row(key)
    if row is None:
        return {"ok": False, "error": "not found"}
    stem = event_stem(row, n); clip_s = fnum(row.get("clip_s")) or 600
    with NOTES_LOCK:
        allN = notes_all(); lst = allN["notes"].setdefault(stem, [])
        if action == "add":
            if len(lst) >= NOTES_MAX_PER or sum(len(v) for v in allN["notes"].values()) >= NOTES_MAX_ALL:
                return {"ok": False, "error": "limit"}
            off, text, tags, witness = clean_note_input(data, clip_s)
            if off is None:
                return {"ok": False, "error": "bad offset"}
            if not text and not tags:
                return {"ok": False, "error": "empty"}
            t0, approx = event_t0(row, n)
            nt = {"id": "n_" + secrets.token_hex(4), "off": off, "t": (t0 + int(off * 1000)) if t0 else None, "approx": approx,
                  "text": text, "tags": tags, "witness": witness if "zeuge" in tags else "",
                  "ts": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
            lst.append(nt)
        else:
            nid = str(data.get("id") or "")
            idx = next((i for i, x in enumerate(lst) if x.get("id") == nid), None)
            if idx is None:
                return {"ok": False, "error": "note not found"}
            if action == "del":
                lst.pop(idx)
            else:
                off, text, tags, witness = clean_note_input(data, clip_s)
                nt = lst[idx]
                if off is not None and off != nt.get("off"):
                    t0, approx = event_t0(row, n)
                    nt["off"] = off; nt["t"] = (t0 + int(off * 1000)) if t0 else None; nt["approx"] = approx
                if not text and not tags:
                    return {"ok": False, "error": "empty"}
                nt.update(text=text, tags=tags, witness=witness if "zeuge" in tags else "",
                          edited=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
        if not lst:
            allN["notes"].pop(stem, None)
        notes_save()
    return {"ok": True, "notes": notes_for(stem)}


# ---------------------------------------------------------------------
# Freie Notizen ("📝 Notiz jetzt"): einmal gespeichert mit Zeitraum von-bis (Datum und Uhrzeit) und Geraet ("all" = alle).
# Mit Stoerungen verknuepft ueber die Zeit - auch mit solchen, die erst spaeter erkannt werden. In notes.json unter "free".
# ---------------------------------------------------------------------
FNOTES_MAX = 20000


def ms_of(iso):
    try:
        return int(aware(dt.datetime.fromisoformat(iso)).timestamp() * 1000)
    except (ValueError, TypeError):
        return None


def fnote_public(x):
    a = ms_of(x.get("from")); b = ms_of(x.get("to")) if x.get("to") else None
    ta = dt.datetime.fromtimestamp(a / 1000.0).astimezone() if a else None
    tb = dt.datetime.fromtimestamp(b / 1000.0).astimezone() if b else None
    return dict(x, a=a, b=b or a, clock=ta.strftime("%H:%M:%S") if ta else "", clock_to=tb.strftime("%H:%M:%S") if tb else "",
                date=ta.strftime("%Y-%m-%d") if ta else "", rz=bool(ta and is_quiet_time(ta)), free=True)


def fnotes_in(t_from, t_to, src="all"):
    """Freie Notizen, die den Zeitraum [t_from, t_to] (ms) beruehren; Geraet passt oder Notiz gilt fuer alle."""
    out = []
    with NOTES_LOCK:
        for x in notes_all().get("free") or []:
            p = fnote_public(x)
            if p["a"] is None:
                continue
            if p["a"] <= t_to and p["b"] >= t_from and (src == "all" or x.get("src", "all") in ("all", src)):
                out.append(p)
    out.sort(key=lambda p: p["a"])
    return out


def row_core(r):
    """Ausschlag einer Stoerung in ms (genau aus ereignisse.jsonl, sonst aus Beginn und Dauer)."""
    if is_virtual(r.get("datei")):
        m = meta_of(r)
        if m:
            return int(m["t0"]), int(m["t_end"])
    a = ms_of(r.get("start"))
    if a is None:
        return None, None
    return a, a + int((fnum(r.get("dauer_s")) or 0) * 1000) + 100


def row_span(r):
    """Zeitraum einer Stoerung in ms: Beginn bis Ende der Aufnahme (Vor-/Nachlauf eingeschlossen; ab 1.40 nur der Ausschlag)."""
    if is_virtual(r.get("datei")):
        return row_core(r)
    a = ms_of(r.get("start"))
    if a is None:
        return None, None
    pre = float(CFG.get("pre_roll_s", 5) or 0) * 1000
    return a - pre, a + max(fnum(r.get("clip_s")) or 0, fnum(r.get("dauer_s")) or 0) * 1000


RUN_NOTES_LOCK = threading.Lock()


def run_notes_path():
    return os.path.join(DATA_DIR, "unterbrechung_notizen.json")


def run_notes():
    d = read_json(run_notes_path()) if os.path.exists(run_notes_path()) else {}
    return d if isinstance(d, dict) else {}


def run_note_set(key, text):
    """Kommentar zu einer Unterbrechung (Schluessel = Beginn wie in laufzeit.jsonl). Aendert keine Aufzeichnung."""
    key = str(key or "")[:40]; text = re.sub(r"[\x00-\x1f]", " ", str(text or "")).strip()[:300]
    if not key or ms_of(key) is None:
        return {"ok": False, "error": "key"}
    with RUN_NOTES_LOCK:
        d = run_notes()
        if text:
            d[key] = text
        else:
            d.pop(key, None)
        tmp = run_notes_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, run_notes_path())
    log("Unterbrechung " + key + ": Kommentar " + ("gesetzt" if text else "entfernt"))
    return {"ok": True, "key": key, "note": text}


def runtime_info(t_from=None, t_to=None):
    """Laufzeit-Protokoll des Starters (Start, Stopp, Update, Unterbrechung, Rueckfall) und Pruefsummen-Kette je Geraet und Tag."""
    now = int(time.time() * 1000)
    t_to = t_to or now; t_from = t_from if t_from is not None else t_to - 86400000
    ev = []
    try:
        with open(os.path.join(DATA_DIR, "laufzeit.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                a = ms_of(e.get("from") or e.get("at")); b = ms_of(e.get("to") or e.get("at"))
                if a is not None and b is not None and b >= t_from and a <= t_to:
                    ev.append(e)
    except OSError:
        pass
    chains = []
    day = dt.datetime.fromtimestamp(t_from / 1000.0).date(); d1 = dt.datetime.fromtimestamp(t_to / 1000.0).date()
    with SRC_LOCK:
        names = {r.id: r.name for r in RUNNERS.values()}
    while day <= d1:
        for f in sorted(glob.glob(os.path.join(day_dir(), f"{day.isoformat()}_*{DAY_EXT}"))):
            sid = os.path.basename(f)[11:-len(DAY_EXT)]
            c = chain_check(sid, day.isoformat())
            chains.append(dict(c, sid=sid, name=names.get(sid, sid), day=day.isoformat()))
        day += dt.timedelta(days=1)
    notes = run_notes()                               # eigene Kommentare zu Unterbrechungen (z. B. „Stromausfall“)
    stops = [ms_of(e.get("at")) for e in ev if e.get("kind") == "stop"]
    for e in ev:
        if e.get("kind") == "down":
            a_ = ms_of(e.get("from"))
            e["key"] = e.get("from") or ""
            e["note"] = notes.get(e["key"], "")
            # vom Starter sauber beendet (Home Assistant hat angehalten / neu gestartet) oder ohne Abmelden weg (Strom, Absturz)
            e["cause"] = "stopped" if a_ is not None and any(x is not None and -15000 <= x - a_ <= 40000 for x in stops) else "lost"
    return {"ok": True, "events": ev, "chains": chains, "relay": relay_on(), "version": VERSION,
            "code": os.environ.get("LAERM_CODE_DIR", HERE), "start": os.environ.get("LAERM_START_REASON", "")}


def fnote_target(at_ms, src="all"):
    """Welcher Stoerung eine Notiz ohne eingegebene Uhrzeit zugeordnet wird: der letzten innerhalb von fn_assign_min
    Minuten vor dem Zeitpunkt (alle Geraete bzw. nur das gewaehlte). Rueckgabe: {a, b, k, start, devs, kind} oder None."""
    win = int(CFG.get("fn_assign_min", 5) or 0) * 60000
    if win <= 0 or at_ms is None:
        return None
    lo = dt.datetime.fromtimestamp((at_ms - win - 600000) / 1000.0).isoformat(timespec="seconds")
    hi = dt.datetime.fromtimestamp((at_ms + 60000) / 1000.0).isoformat(timespec="seconds")
    allrows = read_log()
    near = [dict(r, k=k) for r, k in zip(allrows, row_keys(allrows)) if lo <= (r.get("start") or "")[:19] <= hi]
    if not near:
        return None
    near.sort(key=lambda r: r.get("start") or "")
    by_k, I, G = incidents(near)
    best = None
    for i, inc in I.items():
        if inc["a"] > at_ms + 1000 or at_ms - inc["b"] > win:
            continue
        if src != "all" and not any(d[0] == src for d in inc["devs"]):
            continue
        if best is None or inc["a"] > best[1]["a"]:
            best = (i, inc)
    if best is None:
        return None
    inc = best[1]
    if src != "all":                                   # nur das gewaehlte Geraet: dessen Ausschlag
        k = next(d[3] for d in inc["devs"] if d[0] == src)
        r = next(x for x in near if x["k"] == k)
        a, b_ = row_core(r)
        inc = dict(inc, a=a, b=b_, lead=k, devs=[d for d in inc["devs"] if d[0] == src])
    g = G.get(inc["grp"], {})
    return {"a": inc["a"], "b": inc["b"], "k": inc["lead"], "start": dt.datetime.fromtimestamp(inc["a"] / 1000.0).astimezone().isoformat(timespec="seconds"),
            "clock": dt.datetime.fromtimestamp(inc["a"] / 1000.0).strftime("%H:%M:%S"), "devs": [[d[1], d[2]] for d in inc["devs"]],
            "kind": g.get("kind", ""), "prof": g.get("prof", False), "ago_s": int(max(0, at_ms - inc["a"]) / 1000)}


def fnote_change(action, data):
    """add / edit / del einer freien Notiz. Antwort: die Notiz bzw. ok.
    auto (ohne eingegebene Uhrzeit): Zeitpunkt = jetzt bzw. erster Tastendruck; liegt kurz davor eine Stoerung, gilt die Notiz fuer sie."""
    tgt = None
    if action == "add" and data.get("auto"):
        at = ms_of(str(data.get("from") or "")[:25]) or int(time.time() * 1000)
        src_ = re.sub(r"[^a-z0-9_]", "", str(data.get("src") or "all"))[:16] or "all"
        tgt = fnote_target(at, src_)
        if tgt:
            data = dict(data, **{"from": dt.datetime.fromtimestamp(tgt["a"] / 1000.0).isoformat(timespec="seconds"),
                                 "to": dt.datetime.fromtimestamp(max(tgt["b"], tgt["a"] + 1000) / 1000.0).isoformat(timespec="seconds")})
        else:
            data = dict(data, **{"from": dt.datetime.fromtimestamp(at / 1000.0).isoformat(timespec="seconds"), "to": ""})
        data["_at"] = dt.datetime.fromtimestamp(at / 1000.0).astimezone().isoformat(timespec="seconds")
    with NOTES_LOCK:
        a = notes_all(); lst = a.setdefault("free", [])
        nid = str(data.get("id") or "")
        if action == "del":
            idx = next((i for i, x in enumerate(lst) if x.get("id") == nid), None)
            if idx is None:
                return {"ok": False, "error": "not found"}
            a["trash"].setdefault("_free", []).append(dict(lst.pop(idx), deleted=dt.datetime.now().astimezone().isoformat(timespec="seconds")))
            notes_save()
            return {"ok": True}
        f = str(data.get("from") or "")[:25]; to = str(data.get("to") or "")[:25]
        fa, tb = ms_of(f), (ms_of(to) if to else None)
        if fa is None:
            return {"ok": False, "error": "from"}
        if to and (tb is None or tb < fa):
            return {"ok": False, "error": "to"}
        text = clean_text(data.get("text"))
        tags = [t for t in (data.get("tags") or []) if isinstance(t, str) and t in NOTE_TAG_SET][:12] if isinstance(data.get("tags"), list) else []
        if not text and not tags:
            return {"ok": False, "error": "empty"}
        src = re.sub(r"[^a-z0-9_]", "", str(data.get("src") or "all"))[:16] or "all"
        witness = clean_text(data.get("witness"), 80) if "zeuge" in tags else ""
        now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        rec = {"from": dt.datetime.fromtimestamp(fa / 1000.0).astimezone().isoformat(timespec="seconds"),
               "to": dt.datetime.fromtimestamp(tb / 1000.0).astimezone().isoformat(timespec="seconds") if tb else "",
               "src": src, "text": text, "tags": list(dict.fromkeys(tags)), "witness": witness}
        if action == "add":
            if len(lst) >= FNOTES_MAX:
                return {"ok": False, "error": "limit"}
            x = dict(rec, id="f_" + secrets.token_hex(5), ts=now); lst.append(x)
            if data.get("_at"):
                x["at"] = data["_at"]                   # wann die Notiz wirklich geschrieben wurde
                if tgt:
                    x["ev"] = tgt["k"]; x["auto"] = True    # automatisch der Stoerung zugeordnet
        else:
            x = next((y for y in lst if y.get("id") == nid), None)
            if x is None:
                return {"ok": False, "error": "not found"}
            x.update(rec, edited=now)
        notes_save()
        return {"ok": True, "note": fnote_public(x), "target": tgt}


def clean_text(v, n=NOTE_TEXT_MAX):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(v or "")).strip()[:n]


def enotes_for(stem):
    """Notiz zum Gesamtereignis ('' wenn keine) und Notizen der Einzelereignisse {ms: text}."""
    with NOTES_LOCK:
        a = notes_all()
        e = a["enote"].get(stem) or {}
        return e.get("text", ""), {k: v.get("text", "") for k, v in (a["snote"].get(stem) or {}).items()}


def enote_change(kind, data):
    """kind: 'enote' (Gesamtereignis) oder 'snote' (Einzelereignis, data.ms). Leerer Text loescht die Notiz."""
    key = str(data.get("k") or "")[:240]
    row, n = find_row(key)
    if row is None:
        return {"ok": False, "error": "not found"}
    stem = event_stem(row, n)
    text = clean_text(data.get("text"))
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    with NOTES_LOCK:
        a = notes_all()
        if kind == "enote":
            if text:
                a["enote"][stem] = {"text": text, "ts": now}
            else:
                a["enote"].pop(stem, None)
        else:
            try:
                ms = str(int(data.get("ms")))
            except (TypeError, ValueError):
                return {"ok": False, "error": "bad ms"}
            d = a["snote"].setdefault(stem, {})
            if text:
                d[ms] = {"text": text, "ts": now}
            else:
                d.pop(ms, None)
            if not d:
                a["snote"].pop(stem, None)
        notes_save()
    en, sn = enotes_for(stem)
    return {"ok": True, "enote": en, "snote": sn}


def notes_trash(stems):
    """Notizen geloeschter Ereignisse aufheben (nicht wegwerfen)."""
    if not stems:
        return
    with NOTES_LOCK:
        allN = notes_all(); moved = 0
        for st in stems:
            if st in allN["notes"] or st in allN["enote"] or st in allN["snote"]:
                allN["trash"][st] = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "notes": allN["notes"].pop(st, []),
                                     "enote": allN["enote"].pop(st, None), "snote": allN["snote"].pop(st, None)}
                moved += 1
        if moved:
            notes_save()


def notes_query(q):
    """Alle Notizen mit Ereignis-Infos, gefiltert (Zeitraum, Quelle, Tags, Suchtext)."""
    g = lambda k, d="": (q.get(k) or [d])[0]
    try:
        d0 = dt.date.fromisoformat(g("from")) if g("from") else None
        d1 = dt.date.fromisoformat(g("to")) if g("to") else None
    except ValueError:
        d0 = d1 = None
    src = re.sub(r"[^a-z0-9_]", "", g("src", "all"))[:16] or "all"
    tags = {t for t in g("tags").split(",") if t in NOTE_TAG_SET}
    text = g("q").strip().lower()[:80]
    rows = read_log(); keys = row_keys(rows)
    with NOTES_LOCK:
        allN = notes_all()["notes"]
        out = []
        for r, k in zip(rows, keys):
            if src != "all" and r["quelle_id"] != src:
                continue
            st = event_stem(r, int(k.rsplit("|", 1)[1] or 0))
            for nt in allN.get(st, []):
                p = note_public(nt)
                day = p["date"] or r["start"][:10]
                if d0 and day < d0.isoformat() or d1 and day > d1.isoformat():
                    continue
                if tags and not tags.intersection(nt.get("tags") or []):
                    continue
                if text and text not in (nt.get("text", "") + " " + nt.get("witness", "")).lower():
                    continue
                out.append(dict(p, k=k, stem=st, start=r["start"], quelle=r["quelle"], quelle_id=r["quelle_id"], datei=r["datei"],
                                dauer_s=r["dauer_s"], spitze_dbfs=r["spitze_dbfs"], art=art_fields(r["datei"])["art"]))
    with SRC_LOCK:
        nm_ = {r_.id: r_.name for r_ in RUNNERS.values()}
    for p in fnotes_in(0, 10 ** 15, src):                 # freie Notizen ("Notiz jetzt")
        if d0 and p["date"] < d0.isoformat() or d1 and p["date"] > d1.isoformat():
            continue
        if tags and not tags.intersection(p.get("tags") or []):
            continue
        if text and text not in (p.get("text", "") + " " + p.get("witness", "")).lower():
            continue
        ta = dt.datetime.fromtimestamp(p["a"] / 1000.0).astimezone()
        out.append(dict(p, t=p["a"], off=0, approx=False, abs=ta.isoformat(timespec="milliseconds"), k="", stem="", start=p["from"],
                        quelle=nm_.get(p.get("src"), "alle Geräte" if CFG.get("language") != "en" else "all devices"),
                        quelle_id=p.get("src", "all"), datei="", dauer_s="", spitze_dbfs="", art=""))
    out.sort(key=lambda x: x.get("t") or 0)
    return out


def notes_csv(q):
    rows = notes_query(q)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["datum", "uhrzeit", "offset_s", "ungefaehr", "ruhezeit", "ereignis_start", "quelle", "datei", "dauer_s", "spitze_dbfs_relativ",
                "ki_art", "tags", "zeuge", "notiz", "erstellt"])
    safe = lambda v: ("'" + v) if isinstance(v, str) and v[:1] in ("=", "+", "-", "@") else v
    for x in rows:
        w.writerow([x["date"], x["clock"], x["off"], "ja" if x.get("approx") else "nein", "ja" if x["rz"] else "nein", x["start"], safe(x["quelle"]),
                    x["datei"], x["dauer_s"], x["spitze_dbfs"], x["art"], " ".join(x.get("tags") or []), safe(x.get("witness", "")),
                    safe(x.get("text", "")), x.get("ts", "")])
    return ("﻿" + buf.getvalue()).encode("utf-8")


NOTE_TAG_DE = {"oben": "oben", "unten": "unten", "nebenan": "nebenan", "treppenhaus": "Treppenhaus", "draussen": "draußen/Straße", "unklar": "Herkunft unklar",
               "klopfen": "Klopfen/Hämmern", "schritte": "Schritte/Trampeln", "musik": "Musik/Bass", "stimmen": "Stimmen/Schreien", "tuer": "Türenknallen",
               "moebel": "Möbelrücken", "bohren": "Bohren", "hund": "Hund", "leicht": "leicht", "deutlich": "deutlich", "stark": "stark",
               "aufgewacht": "aufgewacht", "kind_geweckt": "Kind geweckt", "kein_schlaf": "Einschlafen unmöglich", "gestoert": "Arbeit/Gespräch gestört",
               "geklingelt": "geklingelt", "angesprochen": "angesprochen", "verwaltung": "Hausverwaltung informiert", "polizei": "Polizei/Ordnungsamt gerufen",
               "zeuge": "Zeuge anwesend", "serie": "wiederholt (Serie)"}


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _nice_scale(vals):
    v = [x for x in vals if x is not None and x > -125]
    if not v:
        return -90.0, -30.0
    lo, hi = min(v), max(v); pad = max(0.5, (hi - lo) * 0.05)
    lo, hi = math.floor((lo - pad) / 5) * 5, math.ceil((hi + pad) / 5) * 5
    return float(lo), float(max(hi, lo + 10))


def proto_svg(tr, a, b, lo, hi, down=(), W=900, H=118, mini=False):
    """Grafik fuers Laermprotokoll (SVG, druckt scharf): Spitze als Flaeche, Hintergrund, Schwelle, Stoerungen rot, Zustaende aus
    Home Assistant blau, nicht aufgezeichnet schraffiert (mit Kommentar), Notizen als Marke. tr = day_track(...)."""
    L, R_, T, B = (30, 4, 4, 13) if mini else (34, 6, 8, 16)
    pw, ph = W - L - R_, H - T - B
    X = lambda t: L + pw * (t - a) / max(1, b - a)
    Y = lambda v: T + ph * (1 - max(0.0, min(1.0, (v - lo) / (hi - lo))))
    f1 = lambda v: f"{v:.1f}"
    o = [f'<svg class="pg{" mini" if mini else ""}" viewBox="0 0 {W} {H}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,Segoe UI,Arial" font-size="{8.5 if mini else 9.5}">',
         '<defs><pattern id="hz" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#b9bec6" stroke-width="1.2"/></pattern></defs>',
         f'<rect x="{L}" y="{T}" width="{pw}" height="{ph}" fill="#fafbfc" stroke="#d0d5db" stroke-width=".7"/>']
    st = 5 if hi - lo <= 30 else 10 if hi - lo <= 60 else 20
    v = math.ceil(lo / st) * st
    while v <= hi:                                   # dB-Raster
        y = Y(v); o.append(f'<line x1="{L}" x2="{L + pw}" y1="{f1(y)}" y2="{f1(y)}" stroke="#eceff2" stroke-width=".7"/><text x="{L - 3}" y="{f1(y + 3)}" text-anchor="end" fill="#6b7280">{int(v)}</text>')
        v += st
    span = b - a                                     # Zeitraster (volle Ortszeit)
    stp = next((x for x in (5e3, 10e3, 15e3, 30e3, 60e3, 300e3, 600e3, 1800e3, 3600e3, 7200e3, 10800e3) if span / x <= (5 if mini else 13)), 21600e3)
    tz = dt.datetime.fromtimestamp(a / 1000.0).astimezone().utcoffset().total_seconds() * 1000
    t = math.ceil((a + tz) / stp) * stp - tz
    while t <= b:
        x = X(t); lt = dt.datetime.fromtimestamp(t / 1000.0)
        lab = lt.strftime("%H:%M:%S") if stp < 60e3 else lt.strftime("%H:%M") if stp < 3600e3 or mini else lt.strftime("%H")
        o.append(f'<line x1="{f1(x)}" x2="{f1(x)}" y1="{T}" y2="{T + ph}" stroke="#eceff2" stroke-width=".7"/><text x="{f1(x)}" y="{H - 3}" text-anchor="middle" fill="#6b7280">{lab}</text>')
        t += stp
    for ha_ in tr.get("ha") or []:                   # Home Assistant: an
        x0, x1 = X(max(a, ha_[0])), X(min(b, ha_[1]))
        if x1 > x0:
            o.append(f'<rect x="{f1(x0)}" y="{T}" width="{f1(x1 - x0)}" height="{ph}" fill="#1c7ed6" fill-opacity=".08"/><rect x="{f1(x0)}" y="{T}" width="{f1(x1 - x0)}" height="2.5" fill="#1c7ed6"/>')
    for g_ in down:                                  # nicht aufgezeichnet
        x0, x1 = X(max(a, g_[0])), X(min(b, g_[1]))
        if x1 - x0 > 0.5:
            o.append(f'<rect x="{f1(x0)}" y="{T}" width="{f1(x1 - x0)}" height="{ph}" fill="url(#hz)" fill-opacity=".9"/>')
            if x1 - x0 > 70 and not mini:
                txt = "nicht aufgezeichnet" + (" – " + g_[2] if g_[2] else "")
                mx_ = int((x1 - x0 - 8) / 5.2)
                txt = txt if len(txt) <= mx_ else txt[:max(1, mx_ - 1)] + "…"
                o.append(f'<text x="{f1((x0 + x1) / 2)}" y="{T + ph / 2 + 3}" text-anchor="middle" fill="#4b5563" font-weight="600">{esc_xml(txt)}</text>')
    pts = [p_ for p_ in tr.get("pts") or [] if p_[1] is not None]
    segs, cur, stepv = [], [], tr.get("step") or (span / 720)
    for p_ in pts:                                   # Luecken bleiben leer
        if cur and p_[0] - cur[-1][0] > stepv * 3:
            segs.append(cur); cur = []
        cur.append(p_)
    if cur:
        segs.append(cur)
    for sg in segs:
        top = "L".join(f"{f1(X(p_[0]))} {f1(Y(p_[1]))}" for p_ in sg)
        o.append(f'<path d="M{f1(X(sg[0][0]))} {T + ph}L{top}L{f1(X(sg[-1][0] + stepv))} {f1(Y(sg[-1][1]))}L{f1(X(sg[-1][0] + stepv))} {T + ph}Z" fill="#cfe3f7" stroke="#2f7fd1" stroke-width=".6" stroke-linejoin="round"/>')
        bgp = "L".join(f"{f1(X(p_[0]))} {f1(Y(p_[3]))}" for p_ in sg if p_[3] is not None)
        if bgp:
            o.append(f'<path d="M{bgp}" fill="none" stroke="#868e96" stroke-width=".9"/>')
        thp = "L".join(f"{f1(X(p_[0]))} {f1(Y(p_[4]))}" for p_ in sg if p_[4] is not None and lo <= p_[4] <= hi)
        if thp:
            o.append(f'<path d="M{thp}" fill="none" stroke="#e8590c" stroke-width=".9" stroke-dasharray="3 2"/>')
    for e_ in tr.get("ev") or []:                    # Stoerungen dieses Geraets
        x0 = X(max(a, e_[0])); w_ = max(1.2, X(min(b, e_[0] + max(0, e_[1]))) - x0)
        if mini:
            o.append(f'<rect x="{f1(x0)}" y="{T}" width="{f1(w_)}" height="{ph}" fill="#e03131" fill-opacity=".12"/>')
        o.append(f'<rect x="{f1(x0)}" y="{T + ph - 3}" width="{f1(w_)}" height="3" fill="#e03131"/>')
    for n_ in tr.get("fn") or []:                    # Notizen
        x = X(n_[0])
        if L <= x <= L + pw:
            o.append(f'<path d="M{f1(x - 3)} {T}h6l-3 5z" fill="#7048e8"/>')
    o.append('</svg>')
    return "".join(o)


def proto_track(sid, a, b, n, evmap):
    """Schnelle Daten fuer die Grafiken im Laermprotokoll (ohne die Einzelheiten von day_track): Spitze/Hintergrund/Schwelle
    je Abschnitt aus der Tagesaufzeichnung, Stoerungen aus evmap {Geraet: [(t, dauer)]}, Home Assistant, Notizen."""
    parts = []
    x = dt.datetime.fromtimestamp(a / 1000.0).date()
    while x <= dt.datetime.fromtimestamp((b - 1) / 1000.0).date():
        p_ = day_path(sid, x.isoformat())
        if os.path.exists(p_):
            d_ = day_load(p_)
            if d_ is not None and len(d_["t"]):
                parts.append(d_)
        x += dt.timedelta(days=1)
    out = {"pts": [], "has": False, "step": (b - a) / n}
    if parts:
        T_ = np.concatenate([p_["t"] for p_ in parts]); i0, i1 = np.searchsorted(T_, a), np.searchsorted(T_, b)
        if i1 > i0:
            cols = {k: np.concatenate([p_[k] for p_ in parts])[i0:i1] for k in ("pk", "bg", "thr")}
            idx = ((T_[i0:i1] - a) / out["step"]).astype(np.int64).clip(0, n - 1)
            st_ = np.concatenate([[0], np.flatnonzero(np.diff(idx)) + 1])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                pk, bg, th = (np.fmax.reduceat(cols[k], st_) for k in ("pk", "bg", "thr"))
            r1 = lambda v: None if not np.isfinite(v) else round(float(v), 1)
            out["pts"] = [[int(a + idx[s_] * out["step"]), r1(pk[j]), None, r1(bg[j]), r1(th[j])] for j, s_ in enumerate(st_)]
            out["has"] = True
    out["ev"] = [[t, d] for t, d in evmap.get(sid, []) if t + d >= a and t <= b]
    out["ha"] = ha_intervals(sid, a, b)
    out["fn"] = [[x_["a"]] for x_ in fnotes_in(a, b, sid)]
    return out


def protocol_html(q):
    """Druckbares Laermprotokoll (im Browser als PDF speichern). Sachlich, mit Pruefsummen der Clips."""
    g = lambda k, d="": (q.get(k) or [d])[0]
    h = lambda v: esc_xml(v)
    notes = notes_query(q)
    try:
        d0 = dt.date.fromisoformat(g("from")) if g("from") else None
        d1 = dt.date.fromisoformat(g("to")) if g("to") else None
    except ValueError:
        d0 = d1 = None
    src = re.sub(r"[^a-z0-9_]", "", g("src", "all"))[:16] or "all"
    with_all = g("all") == "1"
    pl = plist_by_id(re.sub(r"[^a-z0-9_]", "", g("list"))[:24]) if g("list") else None   # Protokoll einer Protokollliste
    pmem = (plists_all()["mem"].get(pl["id"]) or {}) if pl else None
    if pl:
        with_all = True
    rows = read_log(); keys = row_keys(rows)
    by_key = {}
    for x in notes:
        by_key.setdefault(x["k"], []).append(x)
    evs = []
    for r, k in zip(rows, keys):
        if src != "all" and r["quelle_id"] != src:
            continue
        day = r["start"][:10]
        if d0 and day < d0.isoformat() or d1 and day > d1.isoformat():
            continue
        if pmem is not None and event_stem(r, int(k.rsplit("|", 1)[1] or 0)) not in pmem:
            continue
        if k in by_key or with_all:
            evs.append((r, k))
    clips = paths()[1]
    # Stoerungen ueber alle Geraete zusammenfassen (je Stoerung eine Zeile, die anderen Geraete mit ihrer Spitze)
    lo_ = (d0.isoformat() if d0 else ""); hi_ = ((d1 + dt.timedelta(days=1)).isoformat() if d1 else "9999")
    allk = sorted([dict(r, k=k) for r, k in zip(rows, keys) if lo_ <= (r.get("start") or "")[:10] < hi_], key=lambda x: x.get("start") or "")
    inc_by, INC, GRP = incidents(allk)
    lead_of = {k_: INC[i_]["lead"] for k_, (i_, _g) in inc_by.items()}
    in_evs = {k for _r, k in evs}
    evs = [(r, k) for r, k in evs if lead_of.get(k, k) == k or lead_of.get(k) not in in_evs]   # andere Geraete derselben Stoerung nicht doppelt
    bg_n = sum(1 for _r, k in evs if k in inc_by and INC[inc_by[k][0]]["bg"])
    total = len(evs) - bg_n
    rz_n = 0; per_hour = collections.Counter(); per_wd = collections.Counter()
    for r, k in evs:
        if k in inc_by and INC[inc_by[k][0]]["bg"]:
            continue
        try:
            t = aware(dt.datetime.fromisoformat(r["start"]))
            rz_n += 1 if is_quiet_time(t) else 0; per_hour[t.hour] += 1; per_wd[t.weekday()] += 1
        except ValueError:
            pass
    wdn = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    witnesses = sorted({x.get("witness") for x in notes if x.get("witness")})
    actions = [x for x in notes if set(x.get("tags") or []) & set(NOTE_TAGS["act"])]
    def dmy(iso):
        try:
            return dt.date.fromisoformat(iso[:10]).strftime("%d.%m.%Y")
        except ValueError:
            return iso
    first = (evs[0][0]["start"] if evs else (rows[0]["start"] if rows else ""))
    period = (d0.strftime("%d.%m.%Y") if d0 else (dmy(first) if first else "–")) + " – " + (d1.strftime("%d.%m.%Y") if d1 else dt.date.today().strftime("%d.%m.%Y"))
    devname = "alle Geräte" if src == "all" else (src_name(src) or src)
    name, addr, flat = g("name")[:120], g("addr")[:200], g("flat")[:120]
    o = ['<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>Lärmprotokoll ' + h(period) + '</title><style>',
         'body{font:13px/1.45 system-ui,"Segoe UI",Roboto,sans-serif;color:#111;margin:24px auto;max-width:960px;padding:0 16px}',
         'h1{font-size:22px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 6px;border-bottom:1px solid #999;padding-bottom:3px}',
         'table{border-collapse:collapse;width:100%}th,td{border:1px solid #bbb;padding:4px 6px;text-align:left;vertical-align:top}th{background:#eee}',
         '.ev td{background:#f6f6f6;font-weight:600}.sub td:nth-child(3){padding-left:22px}.sub td{font-size:12px}.en td{font-style:italic}.mut{color:#555}.rz{font-weight:700}.small{font-size:11px}.mono{font-family:Consolas,Menlo,monospace;font-size:10px;word-break:break-all}',
         '.bar{display:inline-block;height:8px;background:#555;vertical-align:middle}.noprint{margin:12px 0}@media print{.noprint{display:none}body{margin:0}h2{break-after:avoid}tr{break-inside:avoid}}',
         '.sig{margin-top:40px;display:flex;gap:60px}.sig div{border-top:1px solid #000;padding-top:4px;min-width:220px}',
         '.pgd{break-inside:avoid;margin:0 0 8px}.pgd .pgh{font-size:11.5px;font-weight:600;margin:2px 0}.pgd .pgh small{font-weight:400;color:#555}svg.pg{display:block;width:100%;height:118px}svg.pg.mini{width:330px;height:62px}',
         '.pgleg{font-size:10.5px;color:#555;margin:0 0 6px}.pgleg i{display:inline-block;width:14px;height:7px;margin:0 4px 0 10px;vertical-align:middle}',
         '</style></head><body>',
         '<div class="noprint"><button onclick="print()">🖨 Drucken / als PDF speichern</button>'
         f'<label style="margin-left:16px"><input type="checkbox" id="og"{" checked" if g("g", "1") != "0" else ""}> Tagesgrafik</label>'
         f'<label style="margin-left:12px"><input type="checkbox" id="oge"{" checked" if g("ge") == "1" else ""}> Grafik je Störung (nur mit Notiz bzw. aus der Liste)</label>'
         '<script>for(const[i,k]of[["og","g"],["oge","ge"]])document.getElementById(i).onchange=e=>{const u=new URLSearchParams(location.search);u.set(k,e.target.checked?"1":"0");location.search=u.toString()}</script></div>',
         f'<h1>Lärmprotokoll{(" – " + h(pl["name"])) if pl else ""}</h1><div class="mut">Zeitraum: {h(period)} · Gerät: {h(devname)} · erstellt am {dt.datetime.now():%d.%m.%Y %H:%M}</div>']
    if pl and pl.get("note"):
        o.append('<p style="white-space:pre-line;margin:8px 0 0">' + h(pl["note"]) + '</p>')
    if name or addr or flat:
        o.append('<table style="margin-top:10px"><tr><th style="width:160px">Name</th><td>' + h(name) + '</td></tr><tr><th>Anschrift</th><td>' + h(addr) +
                 '</td></tr><tr><th>Lage der Wohnung / Raum</th><td>' + h(flat) + '</td></tr></table>')
    o.append('<h2>Zusammenfassung</h2><table>')
    o.append(f'<tr><th style="width:260px">Störungen im Protokoll</th><td>{total}' + ('' if with_all else ' (nur Störungen mit Notiz)')
             + (' · eine Störung, die mehrere Geräte gehört haben, zählt einmal' if len(INC) and any(len(v["devs"]) > 1 for v in INC.values()) else '') + '</td></tr>')
    if bg_n:
        o.append(f'<tr><th>Hintergrund (eigene Geräte)</th><td>{bg_n} – erkannt als eigenes Gerät/Hintergrund (z. B. eigener Fernseher), nicht mitgezählt</td></tr>')
    o.append(f'<tr><th>davon in der Ruhezeit</th><td>{rz_n} ({round(100 * rz_n / total) if total else 0} %) · Ruhezeit {h(CFG.get("quiet_from"))}–{h(CFG.get("quiet_to"))} Uhr'
             + (' und sonntags' if CFG.get("quiet_sunday", True) else '') + '</td></tr>')
    o.append(f'<tr><th>Notizen</th><td>{len(notes)}</td></tr>')
    if per_wd:
        mx = max(per_wd.values())
        o.append('<tr><th>Häufung nach Wochentag</th><td>' + " ".join(f'{wdn[i]} <span class="bar" style="width:{int(40 * per_wd[i] / mx)}px"></span> {per_wd[i]}' for i in range(7) if per_wd[i]) + '</td></tr>')
    if per_hour:
        top = sorted(per_hour.items(), key=lambda kv: -kv[1])[:4]
        o.append('<tr><th>Häufigste Uhrzeiten</th><td>' + ", ".join(f'{hh:02d}–{(hh + 1) % 24:02d} Uhr ({n}×)' for hh, n in top) + '</td></tr>')
    o.append('</table>')
    # Grafiken: Tagesverlauf je Tag und Geraet (gleiche Skala je Geraet), auf Wunsch eine kleine Grafik je Stoerung
    show_day, show_ev = g("g", "1") != "0", g("ge") == "1"
    days_ = []
    if d0 or evs:
        dA = d0 or dt.date.fromisoformat(evs[0][0]["start"][:10]); dB = d1 or (dt.date.fromisoformat(evs[-1][0]["start"][:10]) if evs else dt.date.today())
        while dA <= dB:
            days_.append(dA.isoformat()); dA += dt.timedelta(days=1)
    cut_days = len(days_) > 62
    days_ = days_[-62:]
    try:
        rt_ = runtime_info(int(aware(dt.datetime.combine(dt.date.fromisoformat(days_[0]), dt.time())).timestamp() * 1000) if days_ else None,
                           int(aware(dt.datetime.combine(dt.date.fromisoformat(days_[-1]) + dt.timedelta(days=1), dt.time())).timestamp() * 1000) if days_ else None)
        down_ = [(ms_of(e["from"]), ms_of(e["to"]), e.get("note") or "") for e in rt_["events"] if e.get("kind") == "down" and ms_of(e.get("from")) and ms_of(e.get("to"))]
    except Exception:
        down_ = []
    evmap = {}                                       # Stoerungen je Geraet (Zeit, Dauer) fuer die Grafiken
    if show_day or show_ev:
        for r_, _k in zip(rows, keys):
            ca_, cb_ = row_core(r_)
            if ca_ is not None:
                evmap.setdefault(r_.get("quelle_id") or "main", []).append((ca_, max(0, cb_ - ca_)))
    if show_day and days_:
        grid = {}                                     # (Geraet, Tag) -> Daten
        for day in days_:
            ids_ = sorted({os.path.basename(f_)[11:-len(DAY_EXT)] for f_ in glob.glob(os.path.join(day_dir(), f"{day}_*{DAY_EXT}"))}, key=lambda x: (x != "main", x))
            for sid_ in ids_:
                if src != "all" and sid_ != src:
                    continue
                try:
                    d0_ = int(dt.datetime.combine(dt.date.fromisoformat(day), dt.time()).timestamp() * 1000)
                    tr_ = proto_track(sid_, d0_, d0_ + 86400000, 720, evmap); tr_["day0"], tr_["day1"] = d0_, d0_ + 86400000
                except Exception as e:
                    log("Laermprotokoll: Tagesgrafik", day, sid_, e); continue
                if tr_.get("has"):
                    grid[(sid_, day)] = tr_
        if grid:
            sc_ = {}
            for (sid_, _d), tr_ in grid.items():          # eine Skala je Geraet ueber den ganzen Zeitraum (vergleichbar)
                sc_.setdefault(sid_, []).extend(v for p_ in tr_["pts"] for v in (p_[1], p_[3]))
            sc_ = {k_: _nice_scale(v_) for k_, v_ in sc_.items()}
            o.append('<h2>Tagesverlauf</h2><div class="pgleg"><i style="background:#cfe3f7;border:1px solid #2f7fd1"></i>Spitze (dBFS, relativ)'
                     '<i style="background:#868e96;height:2px"></i>Hintergrund<i style="border-top:2px dashed #e8590c;height:0"></i>Schwelle'
                     '<i style="background:#e03131;height:3px"></i>Störung<i style="background:#1c7ed6;height:3px"></i>laut Home Assistant an'
                     '<i style="background:repeating-linear-gradient(45deg,#b9bec6 0 1px,transparent 1px 4px)"></i>nicht aufgezeichnet'
                     '<i style="width:0;height:0;border-left:4px solid transparent;border-right:4px solid transparent;border-top:6px solid #7048e8;margin-left:12px"></i> Notiz</div>'
                     + ('<div class="small mut">Nur die letzten 62 Tage als Grafik.</div>' if cut_days else ''))
            for day in days_:
                for (sid_, d_), tr_ in grid.items():
                    if d_ != day:
                        continue
                    a_ms, b_ms = tr_["day0"], tr_["day1"]
                    dd_ = dt.date.fromisoformat(day)
                    o.append(f'<div class="pgd"><div class="pgh">{wdn[dd_.weekday()]} {dd_:%d.%m.%Y}{(" · " + h(src_name(sid_) or sid_)) if src == "all" else ""}'
                             f' <small>· {len(tr_.get("ev") or [])} Störungen</small></div>{proto_svg(tr_, a_ms, b_ms, *sc_[sid_], down=down_)}</div>')
    ev_graph = set()
    if show_ev:                                      # nur Stoerungen mit Notiz bzw. aus der gewaehlten Liste (sonst zu lang)
        fr_ = fnotes_in(int(aware(dt.datetime.combine(dt.date.fromisoformat(days_[0]), dt.time())).timestamp() * 1000),
                        int(aware(dt.datetime.combine(dt.date.fromisoformat(days_[-1]) + dt.timedelta(days=1), dt.time())).timestamp() * 1000), src) if days_ else []
        for r_, k_ in evs:                             # mit Notiz: an der Stoerung, als Notiz zum Ereignis oder eine freie Notiz in ihrer Zeit
            ca_, cb_ = row_core(r_)
            if pl or k_ in by_key or (enotes_for(event_stem(r_, int(k_.rsplit("|", 1)[1] or 0)))[0]) or \
                    (ca_ is not None and any(x_["a"] <= cb_ + 60000 and x_["b"] >= ca_ - 5000 for x_ in fr_)):
                ev_graph.add(k_)
            if len(ev_graph) >= 300:
                break
    # freie Notizen ("Notiz jetzt"): als eigene Zeilen an ihrer Stelle; bei einer Liste nur die, die eine ihrer Stoerungen beruehren
    fa_ = int(aware(dt.datetime.combine(d0, dt.time())).timestamp() * 1000) if d0 else 0
    fb_ = int(aware(dt.datetime.combine(d1 + dt.timedelta(days=1), dt.time())).timestamp() * 1000) if d1 else 10 ** 14
    fns = fnotes_in(fa_, fb_, src)
    if pl:
        spans = [row_span(r) for r, _k in evs]
        fns = [x for x in fns if any(a2 is not None and x["a"] <= b2 and x["b"] >= a2 for a2, b2 in spans)]
    fns.sort(key=lambda x: x["a"])

    def fn_rows(limit):
        while fns and fns[0]["a"] <= limit:
            x = fns.pop(0); ta = dt.datetime.fromtimestamp(x["a"] / 1000.0).astimezone()
            tg = ", ".join(NOTE_TAG_DE.get(tt, tt) for tt in x.get("tags") or [])
            rng = x["clock"] + (f'–{x["clock_to"]}' if x.get("to") else "")
            o.append(f'<tr class="en"><td>{wdn[ta.weekday()]} {ta:%d.%m.%Y}</td><td>{h(rng)}</td><td>📝 Notiz: {h(x.get("text") or "")}'
                     f'{(" · Zeuge: " + h(x["witness"])) if x.get("witness") else ""}</td><td>{h(tg)}{" · <span class=rz>Ruhezeit</span>" if x.get("rz") else ""}</td></tr>')
    o.append('<h2>Chronologische Aufstellung</h2><table><tr><th style="width:92px">Datum</th><th style="width:70px">Uhrzeit</th><th>Notiz / Störung</th><th style="width:30%">Merkmale</th></tr>')
    last_grp = None
    for r, k in evs:
        try:
            t = aware(dt.datetime.fromisoformat(r["start"]))
        except ValueError:
            continue
        fn_rows(int(t.timestamp() * 1000))
        ig_ = inc_by.get(k)
        inc_ = INC[ig_[0]] if ig_ else None
        gr_ = GRP.get(ig_[1]) if ig_ else None
        if gr_ and gr_["n"] > 1 and ig_[1] != last_grp:          # Folge gleicher Art kurz hintereinander
            ga, gb = dt.datetime.fromisoformat(gr_["a"]), dt.datetime.fromisoformat(gr_["b"])
            kind_ = gr_["kind"] if gr_["prof"] else (art_label(gr_["kind"], True) if gr_["kind"] and gr_["kind"] != "?" else "noch nicht eingeordnet")
            o.append(f'<tr class="en"><td>{wdn[ga.weekday()]} {ga:%d.%m.%Y}</td><td>{ga:%H:%M:%S}</td><td colspan="2"><b>Folge: {h(kind_)}</b> – {gr_["n"]} Störungen von {ga:%H:%M:%S} bis {gb:%H:%M:%S} ({h(fmt_dur(gr_["dur"]))}){" · Hintergrund" if gr_["bg"] else ""}</td></tr>')
        last_grp = ig_[1] if ig_ else None
        a = art_fields(r["datei"] or event_stem(r, int(k.rsplit("|", 1)[1] or 0)))
        art = (art_label(a["art"], True) + (" (bestätigt)" if a["art_man"] else " (KI-Vorschlag)")) if a["art"] else ""
        bn = labels_for(event_stem(r, int(k.rsplit("|", 1)[1] or 0)))["l"]
        if bn:
            art += (" · " if art else "") + "von Hand benannt: " + ", ".join(sorted({x["name"] for x in bn}))
        if a.get("prof"):
            art = ("Profil: " + a["prof"] + (" (bestätigt)" if a["prof_ok"] else f' (KI {a["prof_c"]} %)' if a.get("prof_c") is not None else "")
                   + (" – Hintergrund/eigenes Gerät, nicht mitgezählt" if a.get("bg") else "") + (" · " + art if art else ""))
        rz = is_quiet_time(t)
        st_ = event_stem(r, int(k.rsplit("|", 1)[1] or 0))
        ki_ = ki_load(st_) or {}; g_ = track_for(r["datei"])
        ptxt = pre_text(g_, fnum(r["spitze_dbfs"]))
        htxt = ha_text(g_)
        if htxt:
            ptxt = (ptxt + " · " if ptxt else "") + htxt
        subs = sub_events(ki_.get("marks"), g_) if g_ and ki_.get("marks") else []
        kinds = kinds_summary(None, None, subs) if subs else []
        kname = lambda kk: "Unbekannt" if kk == "unknown" else (classify.FINE[kk][0] if classify is not None and kk in classify.FINE else kk)
        ktxt = ", ".join(f'{kname(kk)} ×{n}' if n is not None else f'{kname(kk)} {fmt_dur(d)}' for kk, n, d in kinds)
        o.append(f'<tr class="ev"><td>{wdn[t.weekday()]} {t:%d.%m.%Y}</td><td>{t:%H:%M:%S}</td><td>Störung · {h(r["quelle"])} · Dauer {h(fmt_dur(fnum(r["dauer_s"]) or 0))}'
                 f' · Spitze {h(r["spitze_dbfs"])} dBFS (relativ)</td><td>{h(art)}{(" · " + h(ktxt)) if ktxt else ""}{" · <span class=rz>Ruhezeit</span>" if rz else ""}{(" · " + h(ptxt)) if ptxt else ""}</td></tr>')
        if inc_ and len(inc_["devs"]) > 1:                    # dieselbe Stoerung an mehreren Geraeten
            ds_ = [d_ for d_ in inc_["devs"] if d_[2] is not None]
            ctx_ = ("Gehört von: " + " · ".join(f'{d_[1]} {d_[2]:.1f}' for d_ in ds_) + " dBFS → am lautesten: " + ds_[0][1]) if ds_ else ""
        else:
            ctx_ = co_text(co_compare(r, g_, st_)) if g_ and not is_virtual(r.get("datei")) else ""
        if ctx_:
            o.append(f'<tr class="en"><td></td><td></td><td colspan="2">{h(ctx_)}</td></tr>')
        if k in ev_graph:                                 # kleine Grafik der Stoerung mit Umfeld
            try:
                ca_, cb_ = row_core(r)
                if ca_ is not None:
                    pad_ = max(20000, (cb_ - ca_) * 2)
                    trm = proto_track(r.get("quelle_id") or "main", ca_ - pad_, cb_ + pad_, 240, evmap)
                    if trm.get("has"):
                        lo_m, hi_m = _nice_scale([v for p_ in trm["pts"] for v in (p_[1], p_[3])])
                        o.append(f'<tr class="en"><td></td><td></td><td colspan="2">{proto_svg(trm, ca_ - pad_, cb_ + pad_, lo_m, hi_m, down=down_, W=330, H=62, mini=True)}</td></tr>')
            except Exception as e:
                log("Laermprotokoll: Grafik je Stoerung", e)
        en_, sn_ = enotes_for(st_)
        if en_:
            o.append(f'<tr class="en"><td></td><td></td><td colspan="2">Notiz zum Ereignis: {h(en_)}</td></tr>')
        items = []                                   # Notizen an Zeitstellen und Einzelereignisse, chronologisch, eingerueckt
        for x in by_key.get(k, []):
            tg = ", ".join(NOTE_TAG_DE.get(tt, tt) for tt in x.get("tags") or [])
            wt = (" · Zeuge: " + h(x["witness"])) if x.get("witness") else ""
            items.append(((x.get("t") or 0), f'<tr><td></td><td>{h(x["clock"])}{"*" if x.get("approx") else ""}</td><td>{h(x.get("text") or "")}</td><td>{h(tg)}{wt}</td></tr>'))
        t0_ = (g_ or {}).get("t0")
        for ms, kk, pct, pk, dur in subs:
            ta = dt.datetime.fromtimestamp((t0_ + ms) / 1000.0).astimezone() if t0_ else None
            tm = f'{ta:%H:%M:%S},{int(ta.microsecond / 100000)}' if ta else ''
            dd = f'{ta:%d.%m.%Y}' if ta else ''
            nt = sn_.get(str(ms))
            feat = " · ".join(v for v in [f'{pct} %' if pct else '', f'Spitze {pk:.1f} dBFS' if pk is not None else '', f'Dauer {fmt_dur(dur / 1000.0)}' if dur else ''] if v)
            items.append(((t0_ or 0) + ms, f'<tr class="sub"><td>{dd}</td><td>{tm}</td><td>↳ {h(kname(kk))}{(" – " + h(nt)) if nt else ""}</td><td>{h(feat)}</td></tr>'))
        for _t, row_html in sorted(items, key=lambda z: z[0]):
            o.append(row_html)
    fn_rows(10 ** 15)
    if not evs:
        o.append('<tr><td colspan="4" class="mut">Keine Einträge im gewählten Zeitraum.</td></tr>')
    o.append('</table>' + ('<div class="small mut">* Uhrzeit aus dem Ereignisbeginn geschätzt (±1 s).</div>' if any(x.get("approx") for x in notes) else ''))
    if witnesses:
        o.append('<h2>Zeugen</h2><ul>' + "".join(f'<li>{h(w)}</li>' for w in witnesses) + '</ul>')
    if actions:
        o.append('<h2>Gegenmaßnahmen</h2><ul>' + "".join(
            f'<li>{h(dmy(x["date"]))} {h(x["clock"])}: {h(", ".join(NOTE_TAG_DE.get(tt, tt) for tt in x["tags"] if tt in NOTE_TAGS["act"]))}'
            + (f' – {h(x["text"])}' if x.get("text") else '') + '</li>' for x in actions) + '</ul>')
    o.append('<h2>Messdaten (Prüfsummen)</h2><div class="small mut">Zu jedem Ereignis gibt es eine Lärmspur-Datei mit Pegel- und Frequenzwerten, ohne Ton. '
             'Die SHA-256-Prüfsumme belegt, dass eine Datei seit dem Erstellen dieses Protokolls nicht verändert wurde. '
             'Jede Lärmspur enthält zusätzlich die Prüfsumme der vorherigen Spur desselben Geräts, so fällt das Entfernen oder Ändern einer Datei auf.</div>'
             '<table><tr><th style="width:150px">Ereignis</th><th style="width:220px">Datei</th><th>SHA-256</th></tr>')
    for r, k in evs:
        f = os.path.join(clips, os.path.basename(r["datei"])) if (r["datei"] or "").endswith(SPUR_EXT) else ""
        if not f or not os.path.isfile(f):
            continue
        try:
            hs = file_sha256(f)
        except OSError:
            hs = "–"
        o.append(f'<tr><td>{h(r["start"].replace("T", " "))}</td><td>{h(r["datei"])}</td><td class="mono">{hs}</td></tr>')
    o.append('</table>')
    # Tagesaufzeichnung: Pruefsummen-Kette je Geraet und Tag, Unterbrechungen und Updates
    if d0 or evs:
        ta_ = int(aware(dt.datetime.combine(d0 or dt.date.fromisoformat(evs[0][0]["start"][:10]), dt.time())).timestamp() * 1000)
        tb_ = int(aware(dt.datetime.combine((d1 or dt.date.today()) + dt.timedelta(days=1), dt.time())).timestamp() * 1000)
        ri_ = runtime_info(ta_, tb_)
        chs = [c for c in ri_["chains"] if src == "all" or c["sid"] == src]
        if chs:
            o.append('<h2>Tagesaufzeichnung und Datenkette</h2><div class="small mut">Ab Version 1.40 hat eine Störung keine eigene Datei mehr: ihre Messwerte stehen in der '
                     'durchgehenden Tagesaufzeichnung je Gerät (Pegel je 125 ms, Terzbänder, kein Ton). Jede geschriebene Minute bekommt eine SHA-256-Prüfsumme, die auf der '
                     'vorherigen aufbaut. Wird nachträglich ein Wert geändert oder eine Minute entfernt, passt die Kette ab dieser Stelle nicht mehr. Die letzte Summe wird '
                     'zusätzlich stündlich an Home Assistant gemeldet und dort unabhängig gespeichert.</div>'
                     '<table><tr><th style="width:90px">Tag</th><th style="width:150px">Gerät</th><th style="width:170px">Prüfung</th><th>letzte Prüfsumme</th></tr>')
            for c in chs:
                res_ = ("vollständig und unverändert (" + str(c["n"]) + " Minuten)") if c.get("ok") else ("keine Prüfsummen (vor 1.40)" if c.get("ok") is None or c.get("none")
                        else "ABWEICHUNG ab " + (dt.datetime.fromtimestamp(c["bad"] / 1000.0).strftime("%H:%M") if c.get("bad") else "?"))
                o.append(f'<tr><td>{h(dmy(c["day"]))}</td><td>{h(c["name"])}</td><td>{h(res_)}</td><td class="mono">{h(c.get("head") or "–")}</td></tr>')
            o.append('</table>')
        rev_ = [e for e in ri_["events"] if e.get("kind") in ("down", "update", "fallback")]
        if rev_:
            o.append('<h2>Unterbrechungen und Updates</h2><table><tr><th style="width:280px">Zeit</th><th>Vorgang</th></tr>')
            fm_ = lambda iso: dt.datetime.fromisoformat(iso).strftime("%d.%m.%Y %H:%M:%S") if iso else ""
            for e in rev_:
                if e["kind"] == "down":
                    o.append(f'<tr><td>{h(fm_(e.get("from")))} – {h(fm_(e.get("to")))}</td><td>nicht aufgezeichnet ({"Update" if e.get("reason") == "update" else "von Home Assistant angehalten bzw. neu gestartet" if e.get("cause") == "stopped" else "ohne Herunterfahren beendet, z. B. Stromausfall"}; danach Version {h(e.get("version_new", ""))}){(" – Kommentar: " + h(e["note"])) if e.get("note") else ""}</td></tr>')
                elif e["kind"] == "update":
                    o.append(f'<tr><td>{h(fm_(e.get("at")))}</td><td>Programm aktualisiert {h(e.get("version_old", ""))} → {h(e.get("version_new", ""))}; die Aufnahme lief dabei weiter</td></tr>')
                else:
                    o.append(f'<tr><td>{h(fm_(e.get("at")))}</td><td>Version {h(e.get("version", ""))} startete nicht, zurück auf {h(e.get("to", ""))}; die Aufnahme lief weiter</td></tr>')
            o.append('</table>')
    cl_ = [e for e in cal_log() if e.get("kind") in ("apply", "check")]
    if cl_:
        o.append('<h2>Einpegeln der Geräte</h2><p class="small">Alle Mikrofone haben gleichzeitig dasselbe gleichmäßige Geräusch gemessen; die Verstärkung wurde so angepasst, '
                 'dass alle denselben Pegel zeigen (Ziel: Mittelwert der ausgewählten Geräte bzw. bei älteren Messungen das genannte Bezugsgerät).</p><table><tr><th style="width:150px">Zeitpunkt</th><th>Art</th><th>Ergebnis je Gerät</th></tr>')
        for e in cl_[-20:]:
            try:
                tt = dt.datetime.fromisoformat(e["at"]).strftime("%d.%m.%Y %H:%M")
            except (ValueError, KeyError):
                tt = str(e.get("at", ""))
            rr = []
            for x in e.get("res") or []:
                if x.get("ok"):
                    rr.append(f'{x.get("name")}: {x.get("level")} dBFS' + (f', Verstärkung {x.get("gain_old")} → {x.get("gain_new")} dB' if e.get("kind") == "apply" and x.get("gain_new") is not None else f', Abweichung {x.get("delta"):+.1f} dB' if x.get("delta") is not None else ""))
                else:
                    rr.append(f'{x.get("name")}: nicht messbar')
            if e.get("ref") == "mean":
                bz = "Ziel Mittelwert der Geräte" + (f' {e["target"]} dBFS' if e.get("target") is not None else "")
            else:
                bz = "Bezug " + str(next((x.get("name") for x in e.get("res") or [] if x.get("id") == e.get("ref")), e.get("ref", "")))
            o.append(f'<tr><td>{h(tt)}</td><td>{"übernommen" if e.get("kind") == "apply" else "geprüft"} · {h(bz)} · {h(str(e.get("secs", "")))} s</td><td>{h("; ".join(rr))}{(" · " + h(e["note"])) if e.get("note") else ""}</td></tr>')
        o.append('</table>')
    o.append('<h2>Hinweise</h2><ul class="small"><li>Pegelangaben in dBFS sind relative, nicht kalibrierte Werte des Aufnahmegeräts und dienen nur dem Vergleich untereinander; '
             'sie sind keine Messung in dB(A).</li><li>Die Geräuschart wird von einer lokalen KI vorgeschlagen; „bestätigt“ heißt, dass sie von Hand geprüft wurde.</li>'
             '<li>Tonaufnahmen sind nicht Teil dieses Protokolls. Gespeichert und hier ausgewertet werden je Gerät durchgehend Pegelwerte und Terzband-Pegel in 125-ms-Schritten '
             '(Tagesaufzeichnung) sowie – wenn eingeschaltet – ein KI-Fingerabdruck (Zahlen, aus denen sich kein Ton zurückgewinnen lässt); daraus lässt sich keine Sprache '
             'zurückgewinnen. Gesprochenes wird nur als Geräuschart („Stimmen“) erkannt, nie inhaltlich.</li>'
             '<li>Profile (z. B. „Tür knallt“) sind von Hand angelernte Geräusche; die Zuordnung einer Störung zu einem Profil ist ein Vorschlag der KI mit Ähnlichkeit in Prozent, '
             '„bestätigt“ heißt von Hand geprüft.</li></ul>')
    o.append('<div class="sig"><div>Ort, Datum</div><div>Unterschrift</div></div></body></html>')
    return "\n".join(o).encode("utf-8")


def ev_match(r, k, plist="", art=""):
    """Filter des Reiters Protokolle: Protokollliste und Art (Gruppe, _none, _notes, lb:Name)."""
    st = event_stem(r, int(k.rsplit("|", 1)[1] or 0)) if k else event_stem(r)
    if plist and st not in (plists_all()["mem"].get(plist) or {}):
        return False
    if art:
        if art == "_notes":
            return note_count(st) > 0
        if art.startswith("lb:"):
            return any(x["name"] == art[3:] for x in labels_all().get(st, {}).get("l") or [])
        a = art_fields(r["datei"] or st)["art"]
        return (not a) if art == "_none" else a == art
    return True


def range_param(q):
    """Zeitraum aus from/to (Ortszeit JJJJ-MM-TTTHH:MM), sonst None."""
    try:
        a, b = (q.get("from") or [""])[0], (q.get("to") or [""])[0]
        if a and b:
            s_, e_ = aware(dt.datetime.fromisoformat(a)), aware(dt.datetime.fromisoformat(b))
            if e_ > s_ and (e_ - s_).days <= 400:
                return s_, e_
    except ValueError:
        pass
    return None


def night_data(date, src="all", start=None, end=None, plist="", art=""):
    if start is None or end is None:
        start, end = night_window(date, src)
    now = dt.datetime.now().astimezone()
    levels = {}
    for t, r in read_levels(start, end):
        if src != "all" and r.get("quelle_id") != src:
            continue
        m = int((t - start).total_seconds() // 60)
        med, mx, thr, base = fnum(r.get("median_dbfs")), fnum(r.get("max_dbfs")), fnum(r.get("schwelle_dbfs")), fnum(r.get("hintergrund_dbfs"))
        cur = levels.get(m)
        if cur is None:
            levels[m] = [med, mx, thr, base]
        else:   # mehrere Quellen (oder doppelte Minute): der lautere Wert zaehlt
            cur[0] = med if cur[0] is None else (cur[0] if med is None else max(cur[0], med))
            cur[1] = mx if cur[1] is None else (cur[1] if mx is None else max(cur[1], mx))
            cur[2] = thr if cur[2] is None else cur[2]
            cur[3] = base if cur[3] is None else cur[3]
    evs = sorted(night_events(read_log(), start, end, src), key=lambda x: x[0])
    with SRC_LOCK:
        names = {r.id: (r.name, r.src["type"]) for r in RUNNERS.values()}
    events = []
    keymap = {}
    allrows = read_log()
    for rr, kk in zip(allrows, row_keys(allrows)):
        keymap[id(rr)] = kk
    if plist or art:
        evs = [(t, r) for t, r in evs if ev_match(r, keymap.get(id(r), ""), plist, art)]
    for t, r in evs:
        kk = keymap.get(id(r), "")
        nts = [{"off": x["off"], "clock": x["clock"], "text": x.get("text", ""), "tags": x.get("tags", []), "witness": x.get("witness", ""), "rz": x["rz"]}
               for x in notes_for(event_stem(r, int(kk.rsplit("|", 1)[1] or 0) if kk else 0))]
        events.append({"k": kk, "notes": nts, "o": round((t - start).total_seconds() / 60.0, 2), "time": t.strftime("%H:%M:%S"), "start": r["start"],
                       "dur": fnum(r["dauer_s"]), "peak": fnum(r["spitze_dbfs"]), "thr": fnum(r["schwelle_dbfs"]),
                       "file": r["datei"], "src": r["quelle_id"], "art": art_fields(r["datei"])["art"], "name": r["quelle"] or names.get(r["quelle_id"], (r["quelle_id"],))[0],
                       "type": names.get(r["quelle_id"], ("", "local" if r["quelle_id"] == "main" else ""))[1]})
    covered = {m for m in levels if start + dt.timedelta(minutes=m) <= now}
    # je Stoerung (ueber alle Geraete) einmal zaehlen; Hintergrund-Profile (eigenes Geraet) zaehlen nicht
    a_iso, b_iso = start.strftime("%Y-%m-%dT%H:%M:%S"), end.strftime("%Y-%m-%dT%H:%M:%S")
    inr = sorted([dict(rr, k=kk) for rr, kk in zip(allrows, row_keys(allrows)) if a_iso <= (rr.get("start") or "")[:19] < b_iso], key=lambda x: x.get("start") or "")
    ib_, II_, _G = incidents(inr)
    nb_evs = [(t, r) for t, r in evs if not (keymap.get(id(r)) in ib_ and II_[ib_[keymap.get(id(r))][0]]["bg"])]
    sm = night_summary(nb_evs, start, end, covered)
    seen_ = {ib_[keymap.get(id(r))][0] for t, r in nb_evs if keymap.get(id(r)) in ib_}
    sm["count"] = len(seen_) + sum(1 for t, r in nb_evs if keymap.get(id(r)) not in ib_)
    sm["bg_n"] = len(evs) - len(nb_evs)
    if (end - start).total_seconds() > 26 * 3600 and sm.get("loudest_at"):          # mehrere Tage: Datum dazu
        lt = max(((t, r) for t, r in evs if fnum(r["spitze_dbfs"]) == sm["loudest"]), default=None, key=lambda x: 0)
        if lt:
            sm["loudest_at"] = lt[0].strftime("%d.%m. %H:%M")
    return {"date": date.isoformat(), "start": start.isoformat(timespec="minutes"), "end": end.isoformat(timespec="minutes"),
            "minutes": int((end - start).total_seconds() // 60), "running": start <= now < end, "src_name": src_name(src),
            "levels": [[m] + v for m, v in sorted(levels.items())], "events": events,
            "fnotes": fnotes_in(int(start.timestamp() * 1000), int(end.timestamp() * 1000), src),
            "summary": dict(sm, arts=dict(collections.Counter(e["art"] for e in events if e["art"])),
                            notes_n=sum(len(e["notes"]) for e in events))}


def nights_overview(last, n=7, src="all"):
    rows = read_log()
    now = dt.datetime.now().astimezone()
    out = []
    for i in range(n - 1, -1, -1):
        d = last - dt.timedelta(days=i)
        start, end = night_window(d, src)
        evs = night_events(rows, start, end, src)
        covered = set()
        for t, r in read_levels(start, end):
            if (src == "all" or r.get("quelle_id") == src) and t <= now:
                covered.add(int((t - start).total_seconds() // 60))
        sm = night_summary(evs, start, end, covered)
        out.append({"date": d.isoformat(), "count": sm["count"], "quiet_pct": sm["quiet_pct"],
                    "recorded_min": sm["recorded_min"], "data": bool(covered) or bool(evs)})
    return out


def esc_xml(s):
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(s))
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def night_svg(date, src="all", start=None, end=None, plist="", art=""):
    """Leichtgewichtiges Bild (SVG) eines Zeitraums: Lautstaerkekurve, Schwelle, Stoerungen, Zusammenfassung."""
    de = CFG["language"] != "en"
    nd = night_data(date, src, start, end, plist, art)
    start = dt.datetime.fromisoformat(nd["start"]); end = dt.datetime.fromisoformat(nd["end"])
    W, H, L, R, T0 = 1200, 720, 70, 30, 150
    CH = 300
    TR = T0 + CH + 40
    nn = sum(len(e.get("notes", [])) for e in nd["events"])
    if nn:                                              # Platz fuer den Notizblock
        er = math.ceil(min(len(nd["events"]), 24) / 4) if nd["events"] else 1
        H = max(H, TR + 84 + 22 + er * 17 + 26 + 20 + min(nn, 8) * 17 + 34)
    total = max(1, nd["minutes"])
    X = lambda m: L + (W - L - R) * m / total
    vals = [v for row in nd["levels"] for v in (row[1], row[2]) if v is not None] + [e["peak"] for e in nd["events"] if e["peak"] is not None]
    lo = min(vals) - 5 if vals else -100
    hi = max(vals) + 5 if vals else -20
    lo, hi = math.floor(lo / 10) * 10, math.ceil(hi / 10) * 10
    if hi - lo < 30:
        hi = lo + 30
    Y = lambda v: T0 + CH * (1 - (v - lo) / (hi - lo))
    sm = nd["summary"]
    wd = (["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"] if de else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    title = (f"Nacht {wd[start.weekday()]} {start:%d.%m.} – {wd[end.weekday()]} {end:%d.%m.%Y}" if de
             else f"Night {wd[start.weekday()]} {start:%m/%d} – {wd[end.weekday()]} {end:%m/%d/%Y}")
    srcname = nd["src_name"] or ("Alle Quellen" if de else "All sources")
    rec_h = sm["recorded_min"] / 60.0
    tot_h = total / 60.0
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Segoe UI,Roboto,Arial,sans-serif">')
    p.append('<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#38d9c4" stop-opacity=".55"/>'
             '<stop offset="1" stop-color="#38d9c4" stop-opacity=".02"/></linearGradient></defs>')
    p.append(f'<rect width="{W}" height="{H}" rx="18" fill="#10202a"/>')
    p.append(f'<text x="{L}" y="52" font-size="30" font-weight="700" fill="#fff">{esc_xml(title)}</text>')
    rec_txt = (f"aufgezeichnet {rec_h:.1f} von {tot_h:.0f} h" if de else f"recorded {rec_h:.1f} of {tot_h:.0f} h")
    p.append(f'<text x="{L}" y="80" font-size="15" fill="#9fb3bf">{esc_xml(srcname)} · {start:%H:%M}–{end:%H:%M} · {esc_xml(rec_txt)} · Lärmprotokoll</text>')
    qp = "–" if sm["quiet_pct"] is None else f'{sm["quiet_pct"]:.0f} %'
    lq = "–" if sm["longest_quiet_min"] is None else f'{sm["longest_quiet_min"]} min'
    stats = [(qp, "störungsfrei (der Aufnahme)" if de else "undisturbed (of recording)"), (str(sm["count"]), "Störungen" if de else "events"),
             (f'{sm["disturbed_min"]} min', "gestörte Zeit" if de else "disturbed"),
             (lq, "längste Ruhe" if de else "longest quiet"),
             ((f'{sm["loudest"]:.0f} dBFS' if sm["loudest"] is not None else "–"), ((f'lautestes {sm["loudest_at"]}' if sm["loudest_at"] else "lautestes") if de else "loudest"))]
    for i, (v, lab) in enumerate(stats):
        x = L + i * 215
        p.append(f'<text x="{x}" y="118" font-size="24" font-weight="700" fill="#ffa94d">{esc_xml(v)}</text>'
                 f'<text x="{x}" y="138" font-size="13" fill="#9fb3bf">{esc_xml(lab)}</text>')
    # dB-Skala: beschriftet alle 5 dB (bei wenig Platz alle 10), Zwischenstriche je 1 dB
    per = CH / float(hi - lo)
    major = 5 if per * 5 >= 20 else 10
    minor = 1 if per >= 4 else (2 if major == 10 else 5)
    for v in range(int(lo), int(hi) + 1):
        if v % minor:
            continue
        y = Y(v)
        if v % major == 0:
            p.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="#ffffff{"18" if v % 10 == 0 else "0e"}"/>'
                     f'<line x1="{L - 5}" x2="{L}" y1="{y:.1f}" y2="{y:.1f}" stroke="#7f95a3"/>'
                     f'<text x="{L - 8}" y="{y + 4:.1f}" font-size="12" text-anchor="end" fill="#7f95a3">{v}</text>')
        else:
            p.append(f'<line x1="{L - 3}" x2="{L}" y1="{y:.1f}" y2="{y:.1f}" stroke="#7f95a380"/>')
    # Stunden (echte Zeit; bei Zeitumstellung erscheint eine Stunde doppelt bzw. faellt aus)
    u = start.astimezone(dt.timezone.utc)
    h = u.replace(minute=0, second=0, microsecond=0) + (dt.timedelta(hours=1) if (u.minute or u.second) else dt.timedelta(0))
    while h <= end:
        x = X((h - start).total_seconds() / 60)
        p.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T0}" y2="{TR + 34}" stroke="#ffffff10"/><text x="{x:.1f}" y="{TR + 56}" font-size="13" text-anchor="middle" fill="#9fb3bf">{h.astimezone():%H:%M}</text>')
        h += dt.timedelta(hours=1)
    # Viertelstunden als kurze Striche an der Zeitachse
    q = u.replace(minute=(u.minute // 15) * 15, second=0, microsecond=0)
    if q < u:
        q += dt.timedelta(minutes=15)
    while q <= end:
        if q.minute:
            x = X((q - start).total_seconds() / 60)
            p.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{TR + 34}" y2="{TR + 40 if q.minute == 30 else TR + 37}" stroke="#7f95a3"/>')
        q += dt.timedelta(minutes=15)
    lv = nd["levels"]
    sm_med = {}
    for i, row in enumerate(lv):
        w = [r[1] for r in lv[max(0, i - 2):i + 3] if r[1] is not None and abs(r[0] - row[0]) <= 2]
        sm_med[row[0]] = sum(w) / len(w) if w else None

    def path(idx):
        segs, cur, last = [], [], None
        for row in lv:
            m, v = row[0], (sm_med.get(row[0]) if idx == 1 else row[idx])
            if v is None:
                continue
            if last is not None and m - last > 3:
                segs.append(cur); cur = []
            cur.append((X(m), Y(v))); last = m
        if cur:
            segs.append(cur)
        return segs
    for sg in path(1):
        if len(sg) > 1:
            d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in sg)
            p.append(f'<path d="{d} L{sg[-1][0]:.1f},{T0 + CH} L{sg[0][0]:.1f},{T0 + CH} Z" fill="url(#g)"/>')
            p.append(f'<path d="{d}" fill="none" stroke="#38d9c4" stroke-width="2.2" stroke-linejoin="round"/>')
    for sg in path(2):
        if len(sg) > 1:
            p.append(f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in sg)}" fill="none" stroke="#a5f3eb" stroke-opacity=".45" stroke-width="1"/>')
    thr = [row[3] for row in lv if row[3] is not None]
    if thr:
        tv = float(np.median(thr)); y = Y(tv)
        p.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="#ff922b" stroke-dasharray="8 5" stroke-width="1.6"/>'
                 f'<text x="{L + 6}" y="{y - 6:.1f}" font-size="12" fill="#ff922b">{"Schwelle" if de else "threshold"} {tv:.0f} dBFS</text>')
    if not lv:
        p.append(f'<text x="{W / 2}" y="{T0 + CH / 2}" font-size="16" text-anchor="middle" fill="#7f95a3">{"Für diese Nacht liegt kein Pegelverlauf vor." if de else "No level history for this night."}</text>')
    p.append(f'<text x="{L - 8}" y="{TR + 22}" font-size="12" text-anchor="end" fill="#9fb3bf">{"Störungen" if de else "Events"}</text>')
    p.append(f'<line x1="{L}" x2="{W - R}" y1="{TR + 18}" y2="{TR + 18}" stroke="#ffffff22"/>')
    for e in nd["events"]:
        x = X(e["o"]); wdt = max(3, X(e["o"] + (e["dur"] or 0.02) / 60) - x)
        hh = 8 + 10 * min(1, max(0, ((e["peak"] or lo) - lo) / (hi - lo)))
        p.append(f'<rect x="{x:.1f}" y="{TR + 18 - hh:.1f}" width="{wdt:.1f}" height="{2 * hh:.1f}" rx="2" fill="#ff6b6b"><title>{esc_xml(e["time"])} · {esc_xml(e["name"])} · {e["dur"] or 0:.2f} s · {e["peak"] or 0:.1f} dBFS</title></rect>')
    y0 = TR + 84
    p.append(f'<text x="{L}" y="{y0}" font-size="14" font-weight="600" fill="#fff">{"Störungen" if de else "Events"} ({len(nd["events"])})</text>')
    lines = [f'{e["time"][:5]}  {e["name"][:9]:<9} {e["dur"] or 0:>5.1f}s {e["peak"] or 0:>4.0f}dB' + (f'  {art_label(e["art"], de)[:8]}' if e.get("art") else '')
             + (f' ✎{len(e["notes"])}' if e.get("notes") else '') for e in nd["events"][:24]]
    per_col = max(1, math.ceil(len(lines) / 4))
    for i, ln in enumerate(lines):
        col, row = i // per_col, i % per_col
        p.append(f'<text x="{L + col * 275}" y="{y0 + 22 + row * 17}" font-size="11" fill="#c7d3da" font-family="Consolas,Menlo,monospace" xml:space="preserve">{esc_xml(ln)}</text>')
    if len(nd["events"]) > 24:
        p.append(f'<text x="{W - R}" y="{y0}" font-size="12" text-anchor="end" fill="#9fb3bf">+{len(nd["events"]) - 24} {"weitere in log.csv" if de else "more in log.csv"}</text>')
    nl = [(e, x) for e in nd["events"] for x in e.get("notes", [])]
    if nl:
        yN = y0 + 22 + per_col * 17 + 26
        p.append(f'<text x="{L}" y="{yN}" font-size="14" font-weight="600" fill="#fff">{"Notizen" if de else "Notes"} ({len(nl)})</text>')
        for i, (e, x) in enumerate(nl[:8]):
            tg = ", ".join(NOTE_TAG_DE.get(t, t) for t in x.get("tags", []))[:40]
            ln = f'{x["clock"]}  {(x.get("text") or "")[:60]}' + (f'  [{tg}]' if tg else '')
            p.append(f'<text x="{L}" y="{yN + 20 + i * 17}" font-size="11" fill="#c7d3da" font-family="Consolas,Menlo,monospace" xml:space="preserve">{esc_xml(ln)}</text>')
        if len(nl) > 8:
            p.append(f'<text x="{W - R}" y="{yN}" font-size="12" text-anchor="end" fill="#9fb3bf">+{len(nl) - 8}</text>')
    p.append(f'<text x="{W - R}" y="{H - 14}" font-size="11" text-anchor="end" fill="#5f7480">{"Pegel in dBFS (relativ, nicht kalibriert)" if de else "levels in dBFS (relative, not calibrated)"} · {"erstellt" if de else "created"} {dt.datetime.now():%d.%m.%Y %H:%M}</text>')
    p.append("</svg>")
    return "\n".join(p)


def reports_dir():
    out, _, _ = paths()
    return os.path.join(out, "berichte")


def save_night_svg(date):
    d = reports_dir(); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, f"{date.isoformat()}_nacht.svg")
    tmp = f + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(night_svg(date))
    os.replace(tmp, f)
    return f


def report_watch_once():
    """Nicht mehr verwendet (ab 1.32): Nachtberichte werden nicht mehr als Bild abgelegt, sondern immer aus den Daten erzeugt.
    Werden Daten geloescht, fehlen sie damit auch im Bericht."""
    now = dt.datetime.now().astimezone()
    for i in range(0, 8):
        d = now.date() - dt.timedelta(days=i)
        start, end = night_window(d)
        if end > now:
            continue
        f = os.path.join(reports_dir(), f"{d.isoformat()}_nacht.svg")
        if os.path.exists(f):
            continue
        if len(read_levels(start, end)) >= 30:
            try:
                save_night_svg(d); log("Nachtbericht abgelegt:", os.path.basename(f))
            except Exception as e:
                log("Nachtbericht fehlgeschlagen:", e)


def cleanup():
    """Automatisches Loeschen (nur wenn eingeschaltet): Clips, Papierkorb, Pegelverlauf und Nachtbilder."""
    if not CFG["auto_delete"]:
        return
    _, clips, _ = paths()
    limit = time.time() - CFG["retention_days"] * 86400
    with SRC_LOCK:
        vdirs = {safe_dir(r.src.get("video_dir")) for r in RUNNERS.values()} - {"", clips}
    extra = [p for d in vdirs for p in glob.glob(d + "/*.mp4") + glob.glob(d + "/geloescht/*.mp4")]
    for p in extra + glob.glob(clips + "/*.mp4") + glob.glob(clips + "/geloescht/*.mp4") + glob.glob(clips + "/*.wav") + glob.glob(clips + "/geloescht/*.wav") + \
            glob.glob(clips + "/graphen/*.json") + glob.glob(clips + "/geloescht/*.json") + \
            glob.glob(clips + "/*" + SPUR_EXT) + glob.glob(clips + "/geloescht/*" + SPUR_EXT) + glob.glob(clips + "/ki/*.json") + \
            glob.glob(os.path.join(levels_dir(), "*.csv")) + glob.glob(os.path.join(reports_dir(), "*.svg")) + \
            glob.glob(clips + "/tag/*" + DAY_EXT) + glob.glob(clips + "/tag/*.lts") + glob.glob(clips + "/tag/*.ltp") + glob.glob(clips + "/tag/*.chk") + \
            glob.glob(clips + "/tag/*" + FP_EXT) + glob.glob(clips + "/scan/*.json") + glob.glob(clips + "/mit/*" + SPUR_EXT) + glob.glob(clips + "/geloescht/mit/*" + SPUR_EXT):
        try:
            if os.path.getmtime(p) < limit:
                os.remove(p)
        except OSError:
            pass


# =====================================================================
# Erkennung
# =====================================================================
FRAMES = 5   # 5 x 20 ms pro 100-ms-Block


class Background:
    """Hintergrundpegel: Statistik ueber ein Fenster, danach asymmetrisch geglaettet.
    Bis 10 min Fenster: 10 Werte/s, darueber 1 Wert/s (Median je Sekunde) -> hoechstens 7200 Werte."""

    def __init__(self, cfg=None):
        self.cfg = cfg or (lambda: CFG)        # liefert die fuer diese Quelle gueltigen Einstellungen
        self.reset()

    def reset(self):
        c = self.cfg()
        win_s = int(min(MAX_BG_S, c["bg_window"] * (60 if c["bg_unit"] == "min" else 1)))
        self.win_s = win_s
        self.per_s = 10 if win_s <= 600 else 1
        self.vals = collections.deque(maxlen=max(10, win_s * self.per_s))
        self.acc = []
        self.learn_n = max(10, min(50, win_s * 10))                  # 1 ... 5 s bis zum ersten Wert
        self.seen = 0
        self.value = None
        self.raw = None
        self.n = 0
        self.skip = 20                        # erste 2 s nach Start/Neustart nicht lernen (Einschalt-Knacken o. ae.), sonst springt der Hintergrund kurz hoch

    def add(self, block_median_db, block_peak_db=None):
        """Je 100 ms Median und Spitze merken, damit jede Berechnungsart (auch wenn ein Zeitprofil sie umschaltet) sofort passt.
        Eintrag: (Median, Minimum, Durchschnitt, Spitze); bei 1 Wert/s je Sekunde zusammengefasst."""
        pk = block_median_db if block_peak_db is None else block_peak_db
        if self.skip > 0:
            self.skip -= 1
            return
        if block_median_db > -125:            # digitale Stille nicht lernen
            self.seen += 1
            if self.per_s == 10:
                self.vals.append((block_median_db, block_median_db, block_median_db, pk))
            else:
                self.acc.append((block_median_db, pk))
                if len(self.acc) >= 10:
                    m = [x[0] for x in self.acc]
                    self.vals.append((float(np.median(m)), min(m), float(np.mean(m)), max(x[1] for x in self.acc))); self.acc = []
        self.n += 1
        if self.n % 5 or self.seen < self.learn_n:   # alle 0,5 s neu berechnen
            return
        a = np.asarray(list(self.vals) + [(x[0], x[0], x[0], x[1]) for x in self.acc], dtype=np.float64)
        if not a.size:
            return
        c = self.cfg()
        st = c["bg_stat"]                          # quiet: leiseste 10 %, median: typischer Pegel, min/mean/max: Minimum/Durchschnitt/Maximum
        self.raw = float(np.percentile(a[:, 0], 10) if st == "quiet" else a[:, 3].max() if st == "max" else a[:, 1].min() if st == "min"
                         else a[:, 2].mean() if st == "mean" else np.median(a[:, 0]))
        if self.value is None:
            self.value = self.raw
        else:
            tau = c["rise_s"] if self.raw > self.value else c["fall_s"]
            self.value += (self.raw - self.value) * min(1.0, 0.5 / max(0.5, tau))

    def peak_max(self, skip_last=True):
        """Lautester Pegel (Spitze je 100 ms) im Zeitraum ohne Stoerungen und wie viele Sekunden das abdeckt: (dBFS, s).
        skip_last: der gerade gelernte Block (der ausloesende) zaehlt nicht mit."""
        vals, acc = list(self.vals), list(self.acc)
        if skip_last:
            if acc:
                acc = acc[:-1]
            elif vals:
                vals = vals[:-1]
        v = [x[3] for x in vals] + [x[1] for x in acc]
        if not v:
            return None, 0
        return round(float(max(v)), 1), int(round(len(vals) / self.per_s + len(acc) / 10.0))

    @property
    def stuck(self):
        return self.value is None and self.n >= 100

    @property
    def pct(self):
        return 100 if self.value is not None else int(100 * min(self.seen, self.learn_n) / self.learn_n)


def threshold(base, stuck=False, C=None):
    C = C or CFG
    mode = C["thr_mode"]
    if mode == "fixed":
        return float(C["thr_fixed_db"]), False, False
    if base is None:
        # Noch kein Hintergrund. Nur wenn das Lernen haengt (Mikrofon liefert seit >10 s fast nur digitale
        # Stille), gilt im Grenzen-Modus die Untergrenze. In den ersten Sekunden wird nichts ausgeloest.
        return (float(C["min_db"]), True, False) if (mode == "bounded" and stuck) else (None, False, False)
    t = base + C["offset_db"]
    if mode == "bounded":
        lo, hi = C["min_db"], max(C["min_db"] + 1, C["thr_max_db"])
        if t < lo:
            return float(lo), True, False
        if t > hi:
            return float(hi), False, True
    return t, False, False


def new_status():
    return {"level": None, "base": None, "thr": None, "active": False, "listening": True, "learning": True,
            "learn_pct": 0, "silent": False, "floor": False, "ceil": False, "error": "", "rate": 16000,
            "device": "", "bands": [], "ts": 0, "online": False}


class Runner:
    """Eine Quelle: eigener Thread, eigener Hintergrund, eigene Ereignisse, eigener Live-Puffer."""

    def __init__(self, src):
        self.src = src
        self.recs = collections.deque(maxlen=BUF_SECONDS * 10)   # ein Datensatz pro 100 ms (Live-Anzeige)
        self.spur = collections.deque(maxlen=BUF_SECONDS * 8)    # Laermspur-Rahmen (125 ms) fuer das Umfeld der Ereignisse
        self.pending = []                                         # Laermspuren, deren Umfeld noch laeuft
        self.plock = threading.Lock()                             # pending wird auch von anderen Geraeten befuellt (Mitspeichern)
        self.dayb = []                                            # Tagesspur: Rahmen der laufenden Minute
        self.rlock = threading.Lock()
        # Ton nur kurz im Arbeitsspeicher (Live-Erkennung, "Bereich pruefen"); wird nie gespeichert oder abgespielt
        self.hist = collections.deque(maxlen=HIST_SECONDS * 10)
        self.hist_lock = threading.Lock()
        self.hist_rate = 16000
        self.seq = 0
        self.status = new_status()
        self.restart = threading.Event()
        self.relearn = threading.Event()
        self.stop = threading.Event()
        self.push = PushBuffer() if src["type"] == "phone" else None
        self.count_today = 0
        self.count_total = 0
        self.thread = None
        self.bg = None
        self.mb = None           # Sammler fuer den Minutenwert (Nachtbericht)
        self.video = VideoBuffer(self) if src.get("type") == "url" else None

    id = property(lambda self: self.src["id"])
    name = property(lambda self: self.src["name"])
    topic = property(lambda self: TOPIC if self.src["id"] == "main" else f"{TOPIC}/{self.src['id']}")

    def interrupted(self):
        return self.restart.is_set() or self.stop.is_set()

    def cfg(self):
        """Gueltige Einstellungen fuer diese Quelle: allgemeine Werte, bei eigenen Einstellungen ueberschrieben."""
        return effective_cfg(self.src)

    def start(self):
        self.thread = threading.Thread(target=self.loop, name="src-" + self.id, daemon=True)
        self.thread.start()
        if self.video is not None:
            self.video.thread.start()

    def rate(self):
        return CFG["sample_rate"] if self.src["type"] == "local" else REMOTE_RATE

    def blocks(self, rate, block):
        """Liefert (Block, Zeitstempel). (None, None) = Luecke (Handy getrennt)."""
        kind = self.src["type"]
        if kind in ("local", "url"):
            if kind == "url" and not self.src.get("url"):
                self.status["error"] = "Keine Stream-URL eingetragen"
                return
            cmd = local_cmd(rate) if kind == "local" else url_cmd(self.src["url"], rate, self.src.get("user", ""), self.src.get("password", ""))
            if relay_on():                          # Rekorder im Starter: laeuft bei einem Update weiter
                yield from relay_blocks(cmd, block, self)
                return
            for b in pipe_blocks(cmd, block, self):
                yield b, time.time()
        else:   # phone
            size = block * 2
            gap = True
            while not self.interrupted():
                got = self.push.take(size, 1.0)
                if got is None:
                    self.status.update(online=False, error="")
                    if not gap and not self.push.online:
                        gap = True
                        yield None, None
                    continue
                gap = False
                yield np.frombuffer(got[0], dtype=np.int16).copy(), got[1]

    def loop(self):
        while not self.stop.is_set():
            self.restart.clear()
            if not src_runs(self.src):
                self.status.update(new_status(), error="", online=False, pro_lock=bool(self.src.get("enabled", True)))
                self.stop.wait(1.0)
                continue
            try:
                self.session()
            except Exception as e:
                log(f"[{self.name}] Fehler:", repr(e)); self.status["error"] = str(e)
            if self.stop.is_set():
                break
            if self.restart.is_set():
                log(f"[{self.name}] Aufnahme startet mit neuen Einstellungen neu")
                continue
            if self.src["type"] != "phone":
                self.status["online"] = False
                log(f"[{self.name}] Aufnahme unterbrochen, neuer Versuch in 5 s")
                self.stop.wait(5)

    def session(self):
        rate = self.rate()
        block = rate // 10
        frame = block // FRAMES
        bands = Bands(rate, block)
        terz = Terz(rate)
        if self.bg is None:
            self.bg = Background(self.cfg)      # bleibt bei kurzen Unterbrechungen erhalten
        bg = self.bg
        self.status.update(rate=rate, device=CFG["device"] if self.src["type"] == "local" else self.src["type"], bands=bands.centers)
        pre = collections.deque()
        ev = None
        above = zero_n = nblk = fc = busy_n = calm_n = 0
        hum = None
        sec_max, was_active, was_online = -130.0, None, None
        t = self.topic
        last_ts = 0
        clk = None
        for blk, bts in self.blocks(rate, block):
            if self.relearn.is_set():
                self.relearn.clear(); bg.reset()
            if blk is None:                     # Handy getrennt: offenes Ereignis abschliessen
                if ev is not None:
                    try:
                        save_event(ev, rate, self)
                    except Exception as e:
                        log(f"[{self.name}] Speichern fehlgeschlagen:", e)
                    ev = None
                pre.clear(); above = 0
                self.status.update(active=False, online=False)
                pub(f"{t}/active", "OFF", True); pub(f"{t}/online", "OFF", True)
                was_active, was_online = False, None
                log(f"[{self.name}] Verbindung unterbrochen")
                continue
            hb = self.src.get("hum", 0)
            if hum is None or hum.base != hb:
                hum = HumFilter(hb, rate)
                if hb and hum.sos is None:
                    log(f"[{self.name}] Brummfilter nicht verfuegbar (scipy fehlt)")
            blk = hum(blk)
            g = self.src.get("gain_db", 0)
            if g:
                blk = np.clip(blk.astype(np.float32) * (10 ** (g / 20.0)), -32768, 32767).astype(np.int16)
            # Gleichmaessiger Takt aus der Tonmenge (100 ms pro Block). Die Ankunftszeit schwankt, weil
            # Rekorder den Ton in Haeppchen liefern; daran wird nur langsam nachgefuehrt.
            if clk is None or abs(bts - (clk + 0.1)) > 1.0:
                clk = bts
            else:
                clk += 0.1
                clk += (bts - clk) * 0.02
            ms = max(int(clk * 1000), last_ts + 1)      # streng steigend fuer die Anzeige
            last_ts = ms
            self.relay_ts = bts                     # bis hier verarbeitet (fuer die Uebergabe beim Update)
            with self.hist_lock:
                if self.hist_rate != rate:          # andere Abtastrate: alter Ton passt nicht mehr dazu
                    self.hist.clear(); self.hist_rate = rate
                self.hist.append((ms, blk.copy()))
            now = dt.datetime.fromtimestamp(ms / 1000.0); nblk += 1
            C = self.cfg()
            fl = [float(db(blk[i * frame:(i + 1) * frame])) for i in range(FRAMES)]
            peak = max(fl)
            zero_n = zero_n + 1 if peak < -125 else 0
            sec_max = max(sec_max, peak)
            # Waehrend einer Aufnahme lernt der Hintergrund nicht, die Schwelle bleibt stehen. Ausnahmen:
            # - noch kein Hintergrund gelernt (Start, nach Aenderung der Einstellungen)
            # - Dauerpegel ueber 60 s ohne ruhige Moment (z. B. neues Mikrofon, Ventilator): das ist der neue Hintergrund.
            if ev is None:
                calm_n += 1
                if calm_n >= 10:
                    busy_n = 0
            else:
                busy_n += 1; calm_n = 0
                if busy_n == 600 and bg.value is not None:
                    log(f"[{self.name}] Seit 60 s durchgehend ueber der Schwelle: Hintergrund wird neu gelernt")
                    bg.reset()
            if ev is None or bg.value is None or busy_n > 600:
                bg.add(float(np.median(fl)), peak)
            base = bg.value
            inh = in_hours(now, C)
            if inh and self.id in FORCE:
                FORCE.discard(self.id)                   # Erfassungszeit hat begonnen: Handschalter zuruecksetzen
                pub(f"{TOPIC}/force", "ON" if FORCE else "OFF", True)
            hold = ha_hold_for(self.id)
            listening = (inh or self.id in FORCE) and not RUN["paused"] and not hold
            virt = not C.get("save_audio")                 # ohne echten Ton: Stoerung = nur der Ausschlag, Messwerte aus der Tagesaufzeichnung
            pre_max = 1 if virt else int(round(C["pre_roll_s"] * 10)) + 1
            pre.append(blk)
            while len(pre) > pre_max:
                pre.popleft()
            thr, at_floor, at_ceil = threshold(base, bg.stuck, C)
            f0 = fc; fc += FRAMES
            if ev is None:
                need = max(1, int(round(C["min_event_ms"] / 20.0)))
                hit = None
                if thr is not None and listening:
                    for i, v in enumerate(fl):
                        above = above + 1 if v > thr else 0
                        if above >= need:
                            hit = f0 + i
                            break
                else:
                    above = 0
                if hit is not None:
                    ev = {"start": now, "blocks": list(pre), "pre_n": len(pre) - 1, "t0": ms - len(pre) * 100,
                          "peak": peak, "base": base if base is not None else thr, "thr": thr, "quiet": 0,
                          "first_hit": (hit - need + 1) * 0.02, "last_hit": hit * 0.02}
                    ev["pre_max"], ev["pre_s"] = bg.peak_max()       # Nachweis: lauter als alles davor (z. B. laufender Fernseher)
                    ev["ha"] = ha_notes(self.id)                      # Zustaende aus Home Assistant beim Beginn der Stoerung
                    ev["virt"] = virt
                    above = 0
                    pub_trigger(self, "beginn", zeit=now.astimezone().isoformat(timespec="seconds"), schwelle_dbfs=round(thr, 1), spitze_dbfs=round(peak, 1))
            else:
                ev["blocks"].append(blk)
                ev["peak"] = max(ev["peak"], peak)
                end_thr = thr if thr is not None else ev["thr"]       # aktuelle Schwelle (Einstellungen gelten sofort)
                for i, v in enumerate(fl):
                    if v < end_thr:
                        ev["quiet"] += 1
                    else:
                        ev["quiet"] = 0; ev["last_hit"] = (f0 + i) * 0.02
                if ev.get("virt"):                   # Ende: 0,5 s unter der Schwelle; laenger als 5 min wird geteilt
                    too_long = len(ev["blocks"]) >= VIRT_MAX_S * 10
                    done_ = ev["quiet"] >= VIRT_END_FRAMES
                else:
                    too_long = len(ev["blocks"]) - ev["pre_n"] >= int(round(C["max_clip_s"] * 10))
                    done_ = ev["quiet"] >= max(1, int(round(C["post_roll_s"] * 50)))
                if done_ or too_long:
                    try:
                        save_event(ev, rate, self)
                    except Exception as e:
                        log(f"[{self.name}] Speichern fehlgeschlagen:", e)
                    ev = None              # Vorlaufpuffer bleibt gefuellt: auch ein direkt folgendes Ereignis hat vollen Vorlauf
            shown_thr = thr if thr is not None else (ev["thr"] if ev is not None else None)
            seg = blk.reshape(10, -1) if len(blk) % 10 == 0 else np.array_split(blk, 10)
            w = np.empty(20, dtype=np.int16)          # je 10 ms: Minimum, Maximum
            for i, s in enumerate(seg):
                w[2 * i] = int(np.min(s)); w[2 * i + 1] = int(np.max(s))
            ts = ms
            # 2 = ueber der Schwelle (Kern des Ereignisses), 1 = Nachlauf nach dem letzten Treffer, 0 = kein Ereignis
            act = 0 if ev is None else (2 if ev["quiet"] < FRAMES else 1)
            rec = (ts, round(peak, 1), None if base is None else round(base, 1),
                   None if shown_thr is None else round(shown_thr, 1), act, b64(w), b64(bands(blk)))
            fr = terz.feed(blk, ms)
            with self.rlock:
                self.seq += 1
                self.recs.append((self.seq,) + rec)
                for f_ts, f_max, f_eq, f_b in fr:
                    self.spur.append((f_ts, f_max, f_eq, rec[2], rec[3], act, b64(f_b)))
            if (not RUN["paused"] and not hold) or ev is not None:    # Tagesspur immer (ab 1.40 die Grundlage jeder Stoerung; gestoppt = Luecke)
                lay_, spc_ = C.get("day_layers", True), C.get("day_spec", True)       # pro Geraet einstellbar, was abgelegt wird
                self.dayb.extend((f_ts, f_max, f_eq, rec[2], rec[3], act, f_b if lay_ else None, f_b if spc_ else None) for f_ts, f_max, f_eq, f_b in fr)
            if self.dayb and (ms // 60000 != self.dayb[0][0] // 60000 or len(self.dayb) >= 600):
                db_, self.dayb = self.dayb, []
                try:
                    day_write(self.id, db_)
                except Exception as e:
                    log(f"[{self.name}] Tagesspur nicht gespeichert:", e)
            if self.pending:
                flush_pending(self, ms)
            if (not RUN["paused"] and not hold) or ev is not None:      # gestoppt/pausiert = Luecke im Nachtbericht
                self.minute_add(ms, peak, base, shown_thr, ev is not None)
            self.status.update(ts=ts, level=round(peak, 1), base=rec[2], thr=rec[3], active=ev is not None,
                               listening=listening, forced=bool(self.id in FORCE and not inh), ha_hold=hold or None, learning=base is None and C["thr_mode"] != "fixed",
                               learn_pct=bg.pct, silent=zero_n > 30, floor=at_floor, ceil=at_ceil, online=True)
            if nblk % 10 == 0:
                pub(f"{t}/level", f"{sec_max:.1f}")
                if base is not None:
                    pub(f"{t}/baseline", f"{base:.1f}")
                if shown_thr is not None:
                    pub(f"{t}/threshold", f"{shown_thr:.1f}")
                a = ev is not None
                if a != was_active:
                    pub(f"{t}/active", "ON" if a else "OFF", True); was_active = a
                if was_online is not True:
                    pub(f"{t}/online", "ON", True); was_online = True
                sec_max = -130.0
        if ev is not None:
            try:
                save_event(ev, rate, self)
            except Exception as e:
                log(f"[{self.name}] Speichern fehlgeschlagen:", e)
        flush_pending(self, force=True)                 # Ende der Sitzung: Spuren mit dem vorhandenen Umfeld abschliessen
        if self.stop.is_set() and getattr(self, "relay_ts", None) and relay_on() and self.src.get("type") in ("local", "url"):
            relay_pos_save(self.id, self.relay_ts)       # Programm endet (Update): das naechste macht genau dort weiter
        if self.dayb:                                   # angefangene Minute der Tagesspur sichern (Neustart, Update)
            db_, self.dayb = self.dayb, []
            try:
                day_write(self.id, db_)
            except Exception as e:
                log(f"[{self.name}] Tagesspur nicht gespeichert:", e)
        if self.stop.is_set() or (self.mb and int(time.time() // 60) != self.mb["m"]):
            self.minute_flush()          # sonst wird die angefangene Minute nach dem Neustart weitergefuehrt
        self.status["active"] = False
        pub(f"{t}/active", "OFF", True)
        pub(f"{t}/online", "OFF", True)

    def minute_add(self, ms, lvl, base, thr, active):
        m = ms // 60000
        if self.mb is not None and self.mb["m"] != m:
            self.minute_flush()
        if self.mb is None:
            self.mb = {"m": m, "l": [], "b": None, "t": None, "a": 0, "n": 0}
        mb = self.mb
        mb["n"] += 1
        if lvl > -125:
            mb["l"].append(lvl)
        if base is not None:
            mb["b"] = base
        if thr is not None:
            mb["t"] = thr
        mb["a"] += 1 if active else 0

    def minute_flush(self):
        mb, self.mb = self.mb, None
        if not mb or not mb["l"]:
            return
        a = np.asarray(mb["l"], dtype=np.float64)
        try:
            write_level(self.id, mb["m"], float(np.median(a)), float(a.max()), mb["b"], mb["t"], mb["a"] / max(1, mb["n"]))
        except Exception as e:
            log(f"[{self.name}] Minutenwert nicht gespeichert:", e)

    def public(self):
        s = {k: v for k, v in self.src.items() if k not in ("token", "password")}     # Passwort nie zurueckschicken
        if self.src["type"] == "url":
            s["has_password"] = bool(self.src.get("password"))
        s["hum_ok"] = sps is not None
        s["cal_state"] = cal_state(self.src)
        st = self.status
        s.update(online=bool(st.get("online")) and (time.time() - st["ts"] / 1000.0 < 4 if st["ts"] else False),
                 active=bool(st.get("active")), silent=bool(st.get("silent")), level=st.get("level"), thr=st.get("thr"), error=st.get("error", ""),
                 count_today=self.count_today, count_total=self.count_total, pro_lock=bool(self.src.get("type") != "local" and not pro_ok()))
        if self.src["type"] == "phone":
            s["has_token"] = True
        vb = self.video
        s["video_on"] = bool(vb and vb.wanted())
        s["video_sending"] = bool(vb and vb.sending())
        s["video_rec"] = bool(vb and vb.recording())
        s["video_show"] = bool(vb and vb.sending() and video_view_on(self.src))
        s["video_error"] = (vb.error if vb and vb.wanted() else "")
        s["video_fps"] = vb.fps if vb and vb.sending() else 0
        return s


def add_runner(src):
    r = Runner(src)
    with SRC_LOCK:
        RUNNERS[src["id"]] = r
    r.start()
    if mq is not None:
        announce_source(r)
    return r


def audio_watch():
    """Soundkarte umgesteckt? Aendert sich die Liste der Eingaenge, verbindet sich das Server-Mikrofon neu."""
    last = None
    while True:
        time.sleep(10)
        try:
            code, out = run(["pactl", "list", "sources", "short"])
            if code != 0:
                continue
            names = tuple(sorted(l.split("\t")[1] for l in out.splitlines() if "\t" in l and not l.split("\t")[1].endswith(".monitor")))
            if last is not None and names != last:
                log("Audio-Eingaenge geaendert (Soundkarte umgesteckt?):", ", ".join(names) or "keine", "-> Server-Mikrofon verbindet neu")
                time.sleep(2)
                apply_volume()
                with SRC_LOCK:
                    runners = [r for r in RUNNERS.values() if r.src["type"] == "local"]
                for r in runners:
                    r.relearn.set(); r.restart.set()
            last = names
        except Exception as e:
            log("Audio-Pruefung fehlgeschlagen:", e)


def pub_checksums():
    today = dt.date.today().isoformat()
    with SRC_LOCK:
        rs = list(RUNNERS.values())
    for r in rs:
        with CHAIN_LOCK:
            h = CHAIN.get((r.id, today))
        if h:
            pub(f"{r.topic}/pruefsumme", h[:16], True)
            pub(f"{r.topic}/pruefsumme_attr", json.dumps({"tag": today, "sha256": h, "zeit": dt.datetime.now().astimezone().isoformat(timespec="seconds")}), True)


def day_watch():
    """Tageswechsel und automatisches Loeschen, unabhaengig von den Quellen."""
    last = dt.date.today().isoformat()
    n = 0
    while True:
        time.sleep(30)
        n += 1
        if n % 4 == 0:                   # alle 2 Minuten: fertige Stunden des Spektrums verdichten
            try:
                spec_pack()
            except Exception as e:
                log("Spektrum verdichten fehlgeschlagen:", e)
        if n % 120 == 1:                 # stuendlich: aktuelle Pruefsumme je Geraet an Home Assistant (dort unabhaengig gespeichert)
            try:
                pub_checksums()
            except Exception as e:
                log("Pruefsumme nicht gemeldet:", e)
        d = dt.date.today().isoformat()
        if d != last:
            last = d
            with SRC_LOCK:
                STATE["today"], STATE["count"] = d, 0
                for r in RUNNERS.values():
                    r.count_today = 0
            pub(f"{TOPIC}/events_today", "0", True)
            cleanup()


def main():
    out, clips, _ = paths()
    os.makedirs(clips, exist_ok=True)
    log(f"Laermprotokoll {VERSION}")
    log("Einstellungen:", json.dumps(public_settings(), ensure_ascii=False))
    log("Audioquellen:\n" + describe_sources())
    srcs = load_sources()
    for s in srcs:
        RUNNERS[s["id"]] = Runner(s)
    save_sources()
    try:
        migrate_log()
    except Exception as e:
        log("log.csv-Umstellung fehlgeschlagen:", e)
    apply_volume()
    rows = read_log(); today = dt.date.today().isoformat()
    STATE["count"] = sum(1 for r in rows if r["start"].startswith(today)); STATE["total"] = len(rows)
    for r in RUNNERS.values():
        mine = [x for x in rows if x["quelle_id"] == r.id]
        r.count_total = len(mine); r.count_today = sum(1 for x in mine if x["start"].startswith(today))
    log("Quellen:", ", ".join(f"{r.name} ({r.src['type']})" for r in RUNNERS.values()))
    mqtt_start(); cleanup()
    for r in list(RUNNERS.values()):
        r.start()
    threading.Thread(target=day_watch, daemon=True).start()
    threading.Thread(target=audio_watch, daemon=True).start()
    threading.Thread(target=video_worker, daemon=True).start()
    threading.Thread(target=pause_watch, daemon=True).start()
    threading.Thread(target=ha_watch, daemon=True).start()
    if classify is not None:
        threading.Thread(target=art_worker, daemon=True).start()
        threading.Thread(target=live_art_worker, daemon=True).start()
        threading.Thread(target=kinds_backfill, daemon=True).start()
        threading.Thread(target=fp_worker, daemon=True).start()
    start_phone_server()

    def shutdown(signum, frame):
        log("Beende: offene Ereignisse werden gespeichert ...")
        with SRC_LOCK:
            runners = list(RUNNERS.values())
        for r in runners:
            r.stop.set()
        for r in runners:
            if r.thread:
                r.thread.join(timeout=4)
        try:
            if ART_TIMER["t"] is not None:
                art_write()                          # noch nicht gespeicherte Einordnungen sichern
        except Exception:
            pass
        pub(f"{TOPIC}/status", "offline", True)
        log("Beendet")
        sys.exit(0)
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    while True:
        time.sleep(3600)


# =====================================================================
# Zuruecksetzen (Einstellungen -> Allgemein): Messdaten & Stoerungen, Notizen & Listen, Tonprofile, Einstellungen.
# Geraete und Verbindungen bleiben immer. Vorher wird eine Sicherung zum Herunterladen angeboten.
# =====================================================================
RESET_KEEP = {"device", "mic_port", "mic_volume", "sample_rate", "output_dir", "clip_dir", "language", "mqtt"}


def _rm(paths_):
    n = 0
    for p_ in paths_:
        try:
            if os.path.isdir(p_):
                shutil.rmtree(p_); n += 1
            elif os.path.exists(p_):
                os.remove(p_); n += 1
        except OSError as e:
            log("Zuruecksetzen: nicht geloescht:", p_, e)
    return n


def reset_app(parts):
    parts = {p_ for p_ in (parts or []) if p_ in ("data", "notes", "profiles", "settings")}
    if not parts:
        return {"ok": False, "error": "nothing"}
    out, clips, lg = paths()
    n = 0
    if "data" in parts:                                   # Messdaten und Stoerungen
        with SRC_LOCK:
            vds = {safe_dir(r.src.get("video_dir")) for r in RUNNERS.values()} - {""}
            for r in RUNNERS.values():
                r.dayb = []
        with LOG_LOCK:
            files = [lg, os.path.join(out, "geloescht.csv"), os.path.join(out, "aufzeichnung.csv"), os.path.join(out, "ha_zustand.csv"),
                     os.path.join(out, "ha_lautstaerke.csv"), levels_dir(), reports_dir()] + glob.glob(os.path.join(out, "log_vor_loeschen_*.csv"))
            files += [os.path.join(clips, d_) for d_ in ("tag", "ki", "mit", "graphen", "geloescht", "scan")]
            files += [os.path.join(clips, f_) for f_ in ("art.json", "ereignisse.jsonl", "spuren_kette.json", "einpegeln.json")]
            files += glob.glob(os.path.join(clips, "*" + SPUR_EXT)) + glob.glob(os.path.join(clips, "*.wav")) + glob.glob(os.path.join(clips, "*.mp4"))
            for d_ in vds:
                files += glob.glob(os.path.join(d_, "*.mp4")) + glob.glob(os.path.join(d_, "geloescht", "*.mp4"))
            n += _rm(files)
            LOG_CACHE["key"] = None
            with ART_LOCK:
                ART["data"] = None
            with EVMETA_LOCK:
                EVMETA["size"], EVMETA["data"] = -1, {}
            for c_ in (DAY_CACHE, SPEC_CACHE, FP_CACHE, CHAIN_CK, LEVEL_CACHE, PROTO_CACHE):
                c_.clear()
            with CHAIN_LOCK:
                CHAIN.clear()
            HA_HIST.update(key=None, rows=[]); HA_VOL.update(key=None, rows=[])
            try:
                os.remove(os.path.join(DATA_DIR, "laufzeit.jsonl"))
            except OSError:
                pass
            recount()
    if "notes" in parts:                                  # Notizen, Protokolllisten, benannte Bereiche
        n += _rm([notes_path(), plists_path(), labels_path()])
        with NOTES_LOCK:
            NOTES["data"] = None
        with PLISTS_LOCK:
            PLISTS["data"] = None
        with LABELS_LOCK:
            LABELS["data"] = None
        with SRC_LOCK:
            for r in RUNNERS.values():
                r.src.pop("plists", None)                  # automatische Zuordnung zu Listen gehoert zu den Listen
        save_sources()
        PROTO_CACHE.clear()
    if "profiles" in parts:                               # Tonprofile
        n += _rm([profiles_path()])
        with PROF_LOCK:
            PROF["data"] = None
        PROTO_CACHE.clear()
        scan_rename("\x00", None)
    if "settings" in parts:                               # Einstellungen auf Standard; Geraete und Verbindungen bleiben
        update_settings({k: v for k, v in DEFAULTS.items() if k not in RESET_KEEP})
        save_sched([])
        save_ha_rules([])
        with SRC_LOCK:
            for r in RUNNERS.values():
                for k_ in ("own", "cfg", "sched"):
                    r.src.pop(k_, None)
                r.relearn.set()
        save_sources()
    try:
        with open(os.path.join(DATA_DIR, "laufzeit.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "kind": "reset", "parts": sorted(parts), "version": VERSION}) + "\n")
    except OSError:
        pass
    log("Zurueckgesetzt:", ", ".join(sorted(parts)), f"({n} Dateien/Ordner geloescht)")
    return {"ok": True, "parts": sorted(parts), "n": n}


def update_settings(data):
    data = pro_strip(dict(data))
    changed = {}
    with CFG_LOCK:
        new = dict(CFG)
        for k, v in data.items():
            if k in DEFAULTS:
                c = clean(k, v)
                if c is not None and c != new[k]:
                    new[k] = c
        normalize(new)
        changed = {k: new[k] for k in DEFAULTS if new[k] != CFG[k]}
        if not changed:
            return {"ok": True, "changed": [], "supervisor": False, "restart": False}
        CFG.update(new)
        snapshot = dict(CFG)
    sup = push_supervisor(snapshot, list(changed))         # ausserhalb der Sperre
    persist(snapshot)
    if {"mic_volume", "device", "mic_port"} & changed.keys():
        apply_volume()
    restart = bool(RESTART_KEYS & changed.keys())
    with SRC_LOCK:
        runners = list(RUNNERS.values())
    for r in runners:
        if restart and r.src["type"] == "local":
            r.relearn.set(); r.restart.set()
        elif RELEARN_KEYS & changed.keys() and not r.src.get("own"):
            r.relearn.set()
    if "language" in changed or "classify" in changed:
        announce()
    log("Einstellungen geaendert:", json.dumps(changed, ensure_ascii=False))
    return {"ok": True, "changed": list(changed), "supervisor": sup, "restart": restart,
            "supervisor_available": bool(os.environ.get("SUPERVISOR_TOKEN"))}


def update_sources(data):
    """Quellen anlegen, aendern, loeschen. Antwort: aktuelle Liste."""
    act = data.get("action")
    sid = str(data.get("id", ""))
    de = CFG["language"] != "en"
    with SRC_LOCK:
        if act == "add":
            kind = data.get("type")
            if kind not in ("phone", "url"):
                return {"ok": False, "error": "type"}
            if not pro_ok():
                return {"ok": False, "error": "pro"}
            if len(RUNNERS) >= 9:
                return {"ok": False, "error": "max"}
            nid = "s" + secrets.token_hex(3)
            n = sum(1 for r in RUNNERS.values() if r.src["type"] == kind) + 1
            src = {"id": nid, "type": kind, "name": f"{default_name(kind, de)} {n}", "enabled": True, "gain_db": 0, "url": ""}
            if kind == "phone":
                src["token"] = secrets.token_hex(16)
            src = clean_source(data, src)
            r = add_runner(src)
            sid = nid
        elif sid not in RUNNERS:
            return {"ok": False, "error": "unknown source"}
        elif act == "update":
            r = RUNNERS[sid]
            old = dict(r.src)
            if isinstance(data.get("cfg"), dict) and not pro_ok():
                data = dict(data, cfg=dict(pro_strip(dict(data["cfg"])), **{k: v for k, v in (r.src.get("cfg") or {}).items() if k in PRO_KEYS}))
            r.src = clean_source(data, r.src)
            if r.src.get("enabled") and r.src.get("check"):
                r.src.pop("check", None)                 # eingeschaltet: Hinweis aus der Sicherung erledigt
            if r.src["type"] == "url":
                try:
                    r.src["device_info"] = (urllib.parse.urlsplit(r.src.get("url", "")).hostname or "")[:60]
                except ValueError:
                    r.src["device_info"] = ""
            if r.src.get("url") != old.get("url") or r.src.get("enabled") != old.get("enabled"):
                r.relearn.set(); r.restart.set()
            elif r.src.get("user") != old.get("user") or r.src.get("password") != old.get("password"):
                r.status["error"] = ""; r.restart.set()          # neue Zugangsdaten: neu verbinden
            oc, nc = effective_cfg(old), effective_cfg(r.src)
            if any(oc[k] != nc[k] for k in RELEARN_KEYS):
                r.relearn.set()
            dev_changed = [k for k in PER_KEYS if oc[k] != nc[k]]
            if dev_changed:
                log(f"[{r.name}] Eigene Einstellungen:", "an" if r.src.get("own") else "aus",
                    json.dumps({k: nc[k] for k in dev_changed}, ensure_ascii=False))
            if r.src["name"] != old["name"] and mq is not None:
                announce_source(r)
        elif act == "token" and RUNNERS[sid].src["type"] == "phone":
            RUNNERS[sid].src["token"] = secrets.token_hex(16)
        elif act == "delete" and sid != "main":
            r = RUNNERS.pop(sid)
            r.stop.set()
            unannounce_source(sid)
        else:
            return {"ok": False, "error": "bad action"}
    save_sources()
    log("Quellen geaendert:", act, sid)
    return {"ok": True, "id": sid, "sources": sources_payload()}


# =====================================================================
# Tagesspur: ganzer Tag, Pegel/Hintergrund/Schwelle je 125 ms (Spitze), ohne Spektrogramm, ohne Ton.
# Datei je Geraet und Tag: clips/tag/JJJJ-MM-TT_<Geraet>.ltg (gzip, jede Minute ein angehaengter Block mit einer JSON-Zeile)
# =====================================================================
DAY_EXT = ".ltg"
DAY_CACHE = {}           # Datei -> (Groesse, Daten)
DAY_LOCK = threading.Lock()


def day_dir():
    return os.path.join(paths()[1], "tag")


def day_path(sid, day):
    return os.path.join(day_dir(), f"{day}_{sid}{DAY_EXT}")


TZ_C = np.asarray(Terz.CENTERS, dtype=np.float64)
TZ_LO, TZ_MID = TZ_C < 250, (TZ_C >= 250) & (TZ_C < 2000)


def terz_layers(b):
    """Ebenen aus den Terzbaendern (0,5 dB ab -130): tief/mittel/hoch (0,1 dB), dominante Frequenz und Klangschwerpunkt (Hz)."""
    if b is None or len(b) != len(TZ_C):
        return [None] * 5
    a = np.frombuffer(bytes(b), dtype=np.uint8).astype(np.float64)
    p = 10 ** ((a / 2 - 130) / 10)
    db = lambda x: int(round(100 * math.log10(x))) if x > 0 else None
    sp = float(p.sum())
    return [db(float(p[TZ_LO].sum())), db(float(p[TZ_MID].sum())), db(float(p[~(TZ_LO | TZ_MID)].sum())), int(TZ_C[int(np.argmax(a))]),
            int(round(math.exp(float((p * np.log(TZ_C)).sum()) / sp))) if sp > 0 else None]


def spec_part(sid, day, hour):
    return os.path.join(day_dir(), f"{day}_{sid}_{hour:02d}.ltp")


def spec_path(sid, day):
    return os.path.join(day_dir(), f"{day}_{sid}.lts")


SPEC_LOCK = threading.Lock()
SPEC_MAGIC = b"LTS1"
SPEC_MAGIC2 = b"LTS2"     # wie LTS1, Zeitabstaende aber 4 Byte (Pausen ueber 65 s innerhalb einer Stunde)


def spec_write(sid, frames):
    """Spektrum (23 Terzbaender je 125 ms) zunaechst roh je Stunde anhaengen (absturzsicher), zur vollen Stunde verdichtet (spec_pack)."""
    by = {}
    for f in frames:
        if len(f) > 7 and f[7] is not None and len(f[7]) == len(Terz.CENTERS):
            t = dt.datetime.fromtimestamp(f[0] / 1000.0)
            by.setdefault((t.date().isoformat(), t.hour), []).append(f)
    with SPEC_LOCK:
        for (day, hour), fr in by.items():
            with open(spec_part(sid, day, hour), "ab") as fh:
                fh.write(b"".join(int(f[0]).to_bytes(8, "little") + bytes(f[7]) for f in fr))


def spec_read_part(path):
    nb = len(Terz.CENTERS); rl = 8 + nb
    try:
        raw = open(path, "rb").read()
    except OSError:
        return np.zeros(0, np.int64), np.zeros((0, nb), np.uint8)
    n = len(raw) // rl
    a = np.frombuffer(raw[:n * rl], dtype=np.uint8).reshape(n, rl)
    return a[:, :8].copy().view("<i8").reshape(n), a[:, 8:].copy()


def spec_pack(force_all=False):
    """Fertige Stunden verdichten: Zeit als Abstand, Baender als Differenz zum vorigen Rahmen, bandweise, gzip.
    Ein Block je Stunde wird an die Tagesdatei .lts angehaengt; die Rohdatei der Stunde wird danach geloescht."""
    now = dt.datetime.now(); cur = (now.date().isoformat(), now.hour)
    nb = len(Terz.CENTERS)
    for f in sorted(glob.glob(os.path.join(day_dir(), "*.ltp"))):
        b = os.path.basename(f)[:-4]
        try:
            day, rest = b[:10], b[11:]; sid, hh = rest.rsplit("_", 1); hour = int(hh)
        except ValueError:
            continue
        if (day, hour) >= cur and not force_all:
            continue
        with SPEC_LOCK:
            ts, bands = spec_read_part(f)
            if len(ts):
                o = np.argsort(ts, kind="stable"); ts, bands = ts[o], bands[o]
                d_ = np.diff(ts, prepend=ts[0]).clip(0, None)
                wide = bool(d_.max() > 65535)
                dts = d_.astype("<u4" if wide else "<u2")
                dl = np.diff(bands.astype(np.int16), axis=0, prepend=np.zeros((1, nb), np.int16)).astype(np.int8)
                blk = (SPEC_MAGIC2 if wide else SPEC_MAGIC) + len(ts).to_bytes(4, "little") + int(ts[0]).to_bytes(8, "little") + dts.tobytes() + dl.T.copy().tobytes()
                with open(spec_path(sid, day), "ab") as fh:
                    fh.write(gzip.compress(blk, compresslevel=9))
            try:
                os.remove(f)
            except OSError:
                pass


SPEC_LTS_CACHE = {}


def spec_load(sid, day):
    """Spektrum eines Tages: (Zeiten, Baender n x 23) aus verdichteten Bloecken und der laufenden Stunde."""
    nb = len(Terz.CENTERS); T, B = [], []
    p = spec_path(sid, day)
    try:
        psz = os.path.getsize(p)
    except OSError:
        psz = -1
    pc = SPEC_LTS_CACHE.get(p)
    if pc and pc[0] == psz and psz >= 0:              # verdichtete Stunden unveraendert: nicht neu entpacken
        T.extend(pc[1]); B.extend(pc[2]); p = None
    if p and psz >= 0:
        try:
            with gzip.open(p, "rb") as fh:
                raw = fh.read()
        except (OSError, EOFError, zlib.error):
            raw = b""
        i = 0
        while i + 16 <= len(raw) and raw[i:i + 4] in (SPEC_MAGIC, SPEC_MAGIC2):
            w = 4 if raw[i:i + 4] == SPEC_MAGIC2 else 2
            n = int.from_bytes(raw[i + 4:i + 8], "little"); t0 = int.from_bytes(raw[i + 8:i + 16], "little"); i += 16
            if i + w * n + nb * n > len(raw):
                break
            dts = np.frombuffer(raw[i:i + w * n], dtype="<u4" if w == 4 else "<u2").astype(np.int64); i += w * n
            dl = np.frombuffer(raw[i:i + nb * n], dtype=np.int8).reshape(nb, n).T.astype(np.int16); i += nb * n
            T.append(t0 + np.cumsum(dts) - dts[0]); B.append(np.cumsum(dl, axis=0).astype(np.uint8))
        if len(SPEC_LTS_CACHE) > 8:
            SPEC_LTS_CACHE.pop(next(iter(SPEC_LTS_CACHE)))
        SPEC_LTS_CACHE[p] = (psz, list(T), list(B))
    for f in sorted(glob.glob(os.path.join(day_dir(), f"{day}_{glob.escape(sid)}_[0-9][0-9].ltp"))):
        ts, bands = spec_read_part(f)
        if len(ts):
            T.append(ts); B.append(bands)
    if not T:
        return None
    ts = np.concatenate(T); bands = np.concatenate(B)
    o = np.argsort(ts, kind="stable")
    return ts[o], bands[o]


DAYW_LOCK = threading.RLock()   # Tagesdateien schreiben bzw. beim Einspielen zusammenfuehren (nie gleichzeitig)


def day_write(sid, frames):
    """frames: [(ts_ms, spitze, mittel, hintergrund, schwelle, zustand, baender_fuer_ebenen, baender_fuer_spektrum)] -> je Tag ein Block.
    Gespeichert je 125 ms: Spitze, Mittel, Hintergrund, Schwelle, Zustand, die Ebenen (tief/mittel/hoch, dominante Frequenz,
    Klangschwerpunkt) und - wenn eingeschaltet - das Spektrum (eigene Datei .lts)."""
    with DAYW_LOCK:
        _day_write(sid, frames)


def _day_write(sid, frames):
    os.makedirs(day_dir(), exist_ok=True)
    spec_write(sid, frames)
    by = {}
    for f in frames:
        by.setdefault(dt.datetime.fromtimestamp(f[0] / 1000.0).date().isoformat(), []).append(f)
    os.makedirs(day_dir(), exist_ok=True)
    i10 = lambda v: None if v is None else int(round(v * 10))
    for day, fr in by.items():
        m = fr[0][0]
        line = json.dumps({"m": m, "r": [[f[0] - m, i10(f[1]), i10(f[2]), i10(f[3]), i10(f[4]), f[5]] + terz_layers(f[6] if len(f) > 6 else None) for f in fr]},
                          separators=(",", ":"))
        with open(day_path(sid, day), "ab") as fh:
            fh.write(gzip.compress((line + "\n").encode(), compresslevel=6))
        try:
            chain_add(sid, day, m, line, [f for f in fr if len(f) > 7 and f[7] is not None and len(f[7]) == len(Terz.CENTERS)])
        except Exception as e:
            log("Pruefsumme nicht geschrieben:", e)


# ---------------------------------------------------------------------------------------------
# Pruefsummen-Kette der Tagesaufzeichnung: je geschriebener Minute sha256(vorige Summe + Pegelzeile + Spektrum).
# Aendert jemand spaeter einen Wert oder entfernt eine Minute, passt die Kette ab dieser Stelle nicht mehr.
# ---------------------------------------------------------------------------------------------
CHAIN = {}
CHAIN_LOCK = threading.Lock()


def chain_file(sid, day):
    return os.path.join(day_dir(), f"{day}_{sid}.chk")


def chain_seed(sid, day):
    return hashlib.sha256(f"laermprotokoll|{day}|{sid}".encode()).hexdigest()


def chain_spec_bytes(ts_list, bands_list):
    return b"".join(int(t).to_bytes(8, "little") + bytes(b) for t, b in zip(ts_list, bands_list))


def chain_add(sid, day, m, line, spec_frames):
    with CHAIN_LOCK:
        key = (sid, day)
        prev = CHAIN.get(key)
        if prev is None:
            prev = chain_seed(sid, day)
            try:
                with open(chain_file(sid, day), "rb") as fh:
                    fh.seek(0, 2); n = fh.tell(); fh.seek(max(0, n - 200))
                    last = fh.read().decode(errors="replace").strip().splitlines()
                if last:
                    prev = last[-1].split()[1]
            except (OSError, IndexError):
                pass
        h = hashlib.sha256(prev.encode() + line.encode() + chain_spec_bytes([f[0] for f in spec_frames], [f[7] for f in spec_frames])).hexdigest()
        with open(chain_file(sid, day), "a") as fh:
            fh.write(f"{m} {h}\n")
        CHAIN[key] = h
        if len(CHAIN) > 64:
            CHAIN.pop(next(iter(CHAIN)))


CHAIN_CK = {}


def chain_check(sid, day):
    """Wie chain_check_full, zwischengespeichert, solange sich die Dateien nicht aendern."""
    fs = [day_path(sid, day), chain_file(sid, day), spec_path(sid, day)]
    key = tuple(os.path.getsize(f) if os.path.exists(f) else -1 for f in fs)
    c = CHAIN_CK.get((sid, day))
    if c and c[0] == key:
        return c[1]
    v = chain_check_full(sid, day)
    if len(CHAIN_CK) > 400:
        CHAIN_CK.pop(next(iter(CHAIN_CK)))
    CHAIN_CK[(sid, day)] = (key, v)
    return v


def chain_check_full(sid, day):
    """Kette eines Tages pruefen: {"ok", "n" (Minuten), "bad" (erste abweichende Minute, ms), "head" (letzte Summe), "none" (keine Kette)}."""
    cf, dp = chain_file(sid, day), day_path(sid, day)
    if not os.path.exists(dp):
        return {"ok": True, "n": 0, "bad": None, "head": "", "none": True}
    try:
        with open(cf) as fh:
            links = [l.split() for l in fh if l.strip()]
    except OSError:
        return {"ok": None, "n": 0, "bad": None, "head": "", "none": True}
    lines = []
    try:
        with gzip.open(dp, "rt", encoding="utf-8") as fh:
            lines = [l.rstrip("\n") for l in fh]
    except (OSError, EOFError, zlib.error):
        pass
    sp = spec_load(sid, day)
    sts, sb = (sp if sp is not None else (np.zeros(0, np.int64), None))
    # Minuten aus der Zeit vor der Kette (vor 1.40) haben keine Pruefsumme: diese ueberspringen
    first_m = int(links[0][0]) if links else None
    k0 = next((i for i, l in enumerate(lines) if l.startswith('{"m":' + str(first_m) + ',')), None) if first_m is not None else None
    if k0 is None:
        return {"ok": False if links else None, "n": 0, "bad": first_m, "head": links[-1][1] if links else "", "none": not links}
    prev = chain_seed(sid, day)
    n = 0; li = k0; segs = 1
    lm = []                                            # Minute je Zeile (fuer den Beginn eines Abschnitts)
    for l_ in lines:
        mm_ = re.match(r'\{"m":(-?\d+),', l_); lm.append(int(mm_.group(1)) if mm_ else None)
    for i, lk in enumerate(links):
        m_s, h_s = lk[0], lk[1]
        if i and len(lk) > 2 and lk[2] == "R":         # eingespielter Abschnitt: eigene Kette ab dem Startwert
            prev = chain_seed(sid, day); segs += 1
            j = next((x for x in range(li, len(lines)) if lm[x] == int(m_s)), None)
            if j is None:
                return {"ok": False, "n": n, "bad": int(m_s), "head": links[-1][1], "none": False, "missing": True, "segs": segs}
            li = j
        if li >= len(lines):
            return {"ok": False, "n": n, "bad": int(m_s), "head": links[-1][1], "none": False, "missing": True, "segs": segs}
        line = lines[li]
        try:
            b = json.loads(line); m = int(b["m"]); tl = [m + r[0] for r in b["r"]]
        except (ValueError, KeyError, TypeError):
            return {"ok": False, "n": n, "bad": int(m_s), "head": links[-1][1], "none": False, "segs": segs}
        if sb is not None and len(sts):
            idx = np.searchsorted(sts, tl); ok_ = (idx < len(sts)) & (sts[np.minimum(idx, len(sts) - 1)] == np.asarray(tl))
            spec = chain_spec_bytes([t for t, o in zip(tl, ok_) if o], [sb[j] for j, o in zip(idx, ok_) if o])
        else:
            spec = b""
        h = hashlib.sha256(prev.encode() + line.encode() + spec).hexdigest()
        if h != h_s or m != int(m_s):
            return {"ok": False, "n": n, "bad": int(m_s), "head": links[-1][1], "none": False, "segs": segs}
        prev = h; n += 1; li += 1
    extra = len(lines) - k0 - n
    return {"ok": True, "n": n, "bad": None, "head": prev, "none": False, "extra": max(0, extra), "segs": segs}


def _day_parse(text_lines):
    ts, cols = [], [[] for _ in range(10)]
    for line in text_lines:
        try:
            b = json.loads(line)
        except ValueError:
            continue
        m = b.get("m", 0)
        for r in b.get("r") or []:
            ts.append(m + r[0])
            for i in range(10):
                v = r[i + 1] if i + 1 < len(r) else None          # Ebenen erst ab 1.31 (vorher fehlen sie)
                cols[i].append(np.nan if v is None else v)
    return {"t": np.asarray(ts, dtype=np.int64), "pk": np.asarray(cols[0], np.float64) / 10, "eq": np.asarray(cols[1], np.float64) / 10,
            "bg": np.asarray(cols[2], np.float64) / 10, "thr": np.asarray(cols[3], np.float64) / 10, "act": np.asarray(cols[4], np.float64),
            "lo": np.asarray(cols[5], np.float64) / 10, "mid": np.asarray(cols[6], np.float64) / 10, "hi": np.asarray(cols[7], np.float64) / 10,
            "dom": np.asarray(cols[8], np.float64), "cen": np.asarray(cols[9], np.float64)}


def day_load(path):
    """Ganze Tagesdatei als Spalten (numpy). Zwischengespeichert; waechst die Datei, wird nur der neue Teil gelesen."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return None
    with DAY_LOCK:
        c = DAY_CACHE.get(path)
        if c and c[0] == size:
            return c[1]
    d = None
    if c and c[0] < size:                              # nur die neuen Bloecke (je Minute ein gzip-Block)
        try:
            with open(path, "rb") as fh:
                fh.seek(c[0]); raw = fh.read(size - c[0])
            nd = _day_parse(gzip.decompress(raw).decode("utf-8", "replace").splitlines())
            d = {k: np.concatenate([c[1][k], nd[k]]) for k in c[1]}
        except (OSError, EOFError, zlib.error, gzip.BadGzipFile):
            d = None                                   # z. B. gerade beim Schreiben: alles neu lesen
    if d is None:
        lines = []
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    lines.append(line)
        except (OSError, EOFError, zlib.error) as e:           # z. B. Strom weg mitten im Schreiben: Rest bis dahin gilt
            log("Tagesspur teilweise lesbar:", os.path.basename(path), e)
        d = _day_parse(lines)
    if len(d["t"]) > 1 and np.any(np.diff(d["t"]) < 0):
        o = np.argsort(d["t"], kind="stable"); d = {k: v[o] for k, v in d.items()}
    with DAY_LOCK:
        if len(DAY_CACHE) > 8 and path not in DAY_CACHE:
            DAY_CACHE.pop(next(iter(DAY_CACHE)))
        DAY_CACHE[path] = (size, d)
    return d


def exceed(sid, t_from, t_to, thr, merge_ms=500, limit=2000):
    """Pruef-Schwelle (nur Anzeige, aendert nichts): Spitzen ueber thr dBFS im Zeitraum aus den vollen 125-ms-Werten der
    Tagesaufzeichnung. Abschnitte mit weniger als merge_ms Abstand zaehlen als eine Spitze."""
    t_from, t_to = int(t_from), int(t_to)
    if t_to <= t_from or t_to - t_from > 40 * 86400000:
        return {"ok": False, "error": "range"}
    x = dt.datetime.fromtimestamp(t_from / 1000.0).date(); parts = []
    while x <= dt.datetime.fromtimestamp(t_to / 1000.0).date():
        p_ = day_path(sid, x.isoformat())
        if os.path.exists(p_):
            d_ = day_load(p_)
            if d_ is not None and len(d_["t"]):
                parts.append((d_["t"], d_["pk"]))
        x += dt.timedelta(days=1)
    with SRC_LOCK:
        rn_ = RUNNERS.get(sid)
    live_ = [f for f in (list(rn_.dayb) if rn_ is not None else []) if t_from <= f[0] <= t_to and f[1] is not None]
    if live_:
        parts.append((np.asarray([f[0] for f in live_], np.int64), np.asarray([f[1] for f in live_], np.float64)))
    if not parts:
        return {"ok": True, "n": 0, "dur_s": 0, "list": [], "cut": False, "thr": thr}
    T_ = np.concatenate([p_[0] for p_ in parts]); P_ = np.concatenate([p_[1] for p_ in parts])
    o_ = np.argsort(T_, kind="stable"); T_, P_ = T_[o_], P_[o_]
    k0, k1 = np.searchsorted(T_, t_from), np.searchsorted(T_, t_to)
    T_, P_ = T_[k0:k1], P_[k0:k1]
    m_ = np.nan_to_num(P_, nan=-200.0) > thr
    if not m_.any():
        return {"ok": True, "n": 0, "dur_s": 0, "list": [], "cut": False, "thr": thr}
    idx = np.flatnonzero(m_)
    brk = np.flatnonzero(np.diff(T_[idx]) > merge_ms) + 1        # neue Spitze, wenn mehr als merge_ms dazwischen
    starts = np.concatenate([[0], brk]); ends = np.concatenate([brk, [len(idx)]])
    out, dur = [], 0
    for a_, b_ in zip(starts, ends):
        sel = idx[a_:b_]
        ta, tb = int(T_[sel[0]]) - 125, int(T_[sel[-1]])
        dur += len(sel) * 125
        out.append([ta, tb, round(float(np.nanmax(P_[sel])), 1)])
    lst = out[:limit]
    try:
        exceed_ki(sid, lst)
    except Exception as e:
        log("Pruef-Schwelle: KI-Zuordnung fehlgeschlagen:", e)
    return {"ok": True, "n": len(out), "dur_s": round(dur / 1000.0, 1), "list": lst, "cut": len(out) > limit, "thr": thr, "ki": bool(art_enabled()), "ki_why": ki_why()}


def exceed_ki(sid, lst, maxn=2000):
    """Nachtraegliche Erkennung je Spitze (ohne Ton): liegt sie in einer gespeicherten Stoerung, deren Art und Tonprofil;
    sonst aus dem gespeicherten KI-Fingerabdruck (Gruppen-Werte, Vergleich mit den Tonprofilen). Haengt an jede Zeile
    ein Feld {src, art, pct, prof, ppct} an. src: "ev" Stoerung, "fp" Fingerabdruck, "gap" an dieser Stelle keiner
    (naechster mehr als 2 s entfernt), "day" an diesem Tag kein Fingerabdruck gespeichert, "nc" nicht geprueft."""
    if not lst:
        return
    a0, b0 = lst[0][0] - 2000, lst[-1][1] + 2000
    evs = []                                          # eigene Stoerungen im Zeitraum: [Beginn, Ende, Art-Felder]
    em_ = evmeta_all()
    for r in read_log():
        if (r.get("quelle_id") or "main") != sid:
            continue
        try:
            st = int(dt.datetime.fromisoformat(r["start"]).timestamp() * 1000)
        except (ValueError, KeyError, TypeError):
            continue
        if st > b0 or st < a0 - 600000:
            continue
        m_ = em_.get(os.path.splitext(os.path.basename(r.get("datei") or ""))[0]) if is_virtual(r.get("datei")) else None
        ea, eb = (int(m_["t0"]), int(m_["t_end"])) if m_ else (st, st + int((fnum(r.get("dauer_s")) or 0) * 1000))
        if eb >= a0:
            evs.append((ea - 300, eb + 300, art_fields(r.get("datei") or "")))
    fps = {}
    PM = None                                         # alle Tonprofil-Fingerabdruecke als Matrix (einmal)
    for k, row in enumerate(lst):
        if k >= maxn:
            row.append({"src": "nc"}); continue
        a, b = row[0], row[1]
        hit = next((e for e in evs if e[0] <= b and e[1] >= a), None)
        if hit and (hit[2]["art"] or hit[2]["prof"]):
            f = hit[2]; row.append({"src": "ev", "art": f["art"], "pct": f["art_c"], "prof": f["prof"], "ppct": f["prof_c"], "man": f["art_man"] or f["prof_ok"]})
            continue
        day = dt.datetime.fromtimestamp(a / 1000.0).date().isoformat()
        if day not in fps:
            fps[day] = fp_load(sid, day)
        fpd = fps[day]
        if fpd is None:
            row.append({"src": "day"}); continue
        T_, G_, V_ = fpd
        i0, i1 = np.searchsorted(T_, a - 600), np.searchsorted(T_, b + 600)
        if i1 <= i0:                                  # keiner direkt in der Spitze: den naechsten innerhalb von 2 s nehmen
            j = np.searchsorted(T_, a)
            cand = [x for x in (j - 1, j) if 0 <= x < len(T_)]
            dist = [min(abs(int(T_[x]) - a), abs(int(T_[x]) - b)) for x in cand]
            if not cand or min(dist) > 2000:
                row.append({"src": "gap"}); continue
            i0 = cand[int(np.argmin(dist))]; i1 = i0 + 1
        g = G_[i0:i1].max(axis=0).astype(float)          # je Gruppe der hoechste Wert in der Spitze
        gi = int(np.argmax(g[:-1])) if g[:-1].max() > 0 else len(g) - 1
        info = {"src": "fp", "art": FP_GROUPS[gi], "pct": int(g[gi])}
        if PM is None:
            names, vecs, ws = [], [], []
            for name, ps in _proto_sets(label_protos(), sid).items():
                for ev_, w_ in ps["E"]:
                    names.append(name); vecs.append(ev_); ws.append(w_)
            PM = (names, np.asarray(vecs, np.float32).reshape(len(vecs), -1), np.asarray(ws, np.float32))
        if PM[0]:
            sc_ = (V_[i0:i1] @ PM[1].T).max(axis=0) * PM[2]
            bi = int(np.argmax(sc_))
            if float(sc_[bi]) >= SCAN_MIN:
                info.update(prof=PM[0][bi], ppct=int(round(float(sc_[bi]) * 100)), pbg=profile_bg(PM[0][bi]))
        row.append(info)


def ki_why():
    """Warum die KI-Erkennung nicht laeuft: "" (laeuft), "off" (Schalter aus), "model" (Modell nicht gefunden / nicht ladbar)."""
    if not CFG.get("classify"):
        return "off"
    return "" if classify is not None and classify.available() else "model"


def fp_status():
    """Fuer die Einstellungen: laeuft der KI-Fingerabdruck, wie viele heute je Geraet gespeichert, uebersprungen, Rechenzeit."""
    day = dt.date.today().isoformat(); devs = []
    with SRC_LOCK:
        rs = list(RUNNERS.values())
    for r in rs:
        try:
            n = os.path.getsize(fp_path(r.id, day)) // FP_REC.size
        except OSError:
            n = 0
        devs.append({"id": r.id, "name": r.src.get("name") or r.id, "on": bool(r.cfg().get("fp_store", True) and r.src.get("enabled", True)), "today": int(n)})
    return {"ki": bool(art_enabled()), "why": ki_why(), "on": FP_STATE["on"], "n": FP_STATE["n"], "skip": FP_STATE["skip"], "ms": FP_STATE["ms"], "devs": devs}


def day_track(sid, day, t_from=None, t_to=None, n=1200, free=False, spec=True):
    """Ausschnitt eines Tages fuer die Anzeige: n Abschnitte mit hoechster Spitze, Mittelwert, Hintergrund, Schwelle, Stoerung.
    free: Zeitraum von–bis auch ueber Mitternacht (Live-Ansicht „letzte 6 h“), sonst auf den Tag begrenzt."""
    n = max(50, min(16000, int(n)))                   # bis 16000: Drucken holt mehrere Zeilen auf einmal
    d0 = dt.datetime.combine(dt.date.fromisoformat(day), dt.time())
    a0 = int(d0.timestamp() * 1000); a1 = int((d0 + dt.timedelta(days=1)).timestamp() * 1000)
    long_ = bool(free and t_from is not None and t_to is not None and 2 * 86400000 < t_to - t_from <= 400 * 86400000)
    if long_:
        days = []
    elif free and t_from is not None and t_to is not None and t_to - t_from <= 2 * 86400000:
        days = []
        x = dt.datetime.fromtimestamp(t_from / 1000.0).date()
        while x <= dt.datetime.fromtimestamp(t_to / 1000.0).date():
            days.append(x.isoformat()); x += dt.timedelta(days=1)
    else:
        days = [day]
        t_from = a0 if t_from is None else max(a0, t_from); t_to = a1 if t_to is None else min(a1, t_to)
    if t_to <= t_from:
        t_to = min(a1, t_from + 60000)
    srcs = sorted({os.path.basename(f)[11:-len(DAY_EXT)] for f in glob.glob(os.path.join(day_dir(), f"{day}_*{DAY_EXT}"))})
    out = {"ok": True, "src": sid, "date": day, "day0": a0, "day1": a1, "from": t_from, "to": t_to, "srcs": srcs, "pts": [], "has": False, "ev": [], "sp": [],
           "art": [], "subs": []}
    kinds_ = set()
    if long_:                                           # mehr als 2 Tage: Minutenwerte (Spitze und typischer Pegel je Minute)
        a_, b_ = dt.datetime.fromtimestamp(t_from / 1000.0).astimezone(), dt.datetime.fromtimestamp(t_to / 1000.0).astimezone()
        lv = [(int(t.timestamp() * 1000), r) for t, r in read_levels(a_, b_) if (r.get("quelle_id") or "main") == sid]
        lv.sort(key=lambda x: x[0])
        nan = lambda v: np.nan if v is None else v
        d = {"t": np.asarray([x[0] for x in lv], dtype=np.int64), "pk": np.asarray([nan(fnum(x[1].get("max_dbfs"))) for x in lv], np.float64),
             "eq": np.asarray([nan(fnum(x[1].get("median_dbfs"))) for x in lv], np.float64),
             "bg": np.asarray([nan(fnum(x[1].get("hintergrund_dbfs"))) for x in lv], np.float64),
             "thr": np.asarray([nan(fnum(x[1].get("schwelle_dbfs"))) for x in lv], np.float64),
             "act": np.asarray([1.0 if (fnum(x[1].get("stoerung_anteil")) or 0) > 0 else 0.0 for x in lv], np.float64)}
        for k in ("lo", "mid", "hi", "dom", "cen"):
            d[k] = np.full(len(lv), np.nan)
        d = d if len(lv) else None
        out["coarse"] = True                            # Hinweis fuer die Anzeige: Minutenwerte
    else:
        parts = [day_load(day_path(sid, x)) for x in days if os.path.exists(day_path(sid, x))]
        parts = [x for x in parts if x is not None and len(x["t"])]
        with SRC_LOCK:
            rn_ = RUNNERS.get(sid)
        live_ = list(rn_.dayb) if rn_ is not None else []        # laufende Minute (noch nicht geschrieben) gleich mitzeigen
        live_ = [f for f in live_ if t_from <= f[0] <= t_to]
        if live_:
            nan = lambda v: np.nan if v is None else v
            ly = [terz_layers(f[6]) for f in live_]
            parts.append({"t": np.asarray([f[0] for f in live_], np.int64), "pk": np.asarray([nan(f[1]) for f in live_], np.float64),
                          "eq": np.asarray([nan(f[2]) for f in live_], np.float64), "bg": np.asarray([nan(f[3]) for f in live_], np.float64),
                          "thr": np.asarray([nan(f[4]) for f in live_], np.float64), "act": np.asarray([f[5] for f in live_], np.float64),
                          "lo": np.asarray([nan(x[0]) for x in ly], np.float64) / 10, "mid": np.asarray([nan(x[1]) for x in ly], np.float64) / 10,
                          "hi": np.asarray([nan(x[2]) for x in ly], np.float64) / 10, "dom": np.asarray([nan(x[3]) for x in ly], np.float64),
                          "cen": np.asarray([nan(x[4]) for x in ly], np.float64)})
        d = parts[0] if len(parts) == 1 else ({k: np.concatenate([x[k] for x in parts]) for k in parts[0]} if parts else None)
    if d is not None and len(d["t"]):
        out["has"] = True; out["first"] = int(d["t"][0]); out["last"] = int(d["t"][-1])
        i0, i1 = np.searchsorted(d["t"], t_from), np.searchsorted(d["t"], t_to)
        if i1 > i0:
            step = (t_to - t_from) / n
            idx = ((d["t"][i0:i1] - t_from) / step).astype(np.int64).clip(0, n - 1)
            cut = np.flatnonzero(np.diff(idx)) + 1
            starts = np.concatenate([[0], cut])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                pk = np.fmax.reduceat(d["pk"][i0:i1], starts); eq = d["eq"][i0:i1]
                eqm = 10 * np.log10(np.add.reduceat(np.nan_to_num(10 ** (eq / 10), nan=0.0), starts) / np.diff(np.concatenate([starts, [len(eq)]])) + 1e-30)
                bg = np.fmax.reduceat(d["bg"][i0:i1], starts); th = np.fmax.reduceat(d["thr"][i0:i1], starts)
                ac = np.fmax.reduceat(d["act"][i0:i1], starts)
                lay = [np.fmax.reduceat(d[k][i0:i1], starts) for k in ("lo", "mid", "hi")]
                for k in ("dom", "cen"):                            # Frequenzen: Mittel der vorhandenen Werte
                    v = d[k][i0:i1]; ok = np.isfinite(v)
                    sm = np.add.reduceat(np.where(ok, v, 0.0), starts); cn = np.add.reduceat(ok.astype(np.float64), starts)
                    lay.append(np.where(cn > 0, sm / np.maximum(cn, 1), np.nan))
            if spec and not long_:                         # Spektrum je Abschnitt (lautestes Band), wenn gespeichert und gebraucht - auch fuer den ganzen Tag
                spT, spB = [], []
                for x in days:
                    sp_ = spec_load_cached(sid, x)
                    if sp_ is not None:
                        spT.append(sp_[0]); spB.append(sp_[1])
                if spT:
                    sT = spT[0] if len(spT) == 1 else np.concatenate(spT); sB = spB[0] if len(spB) == 1 else np.concatenate(spB)
                    j0, j1 = np.searchsorted(sT, t_from), np.searchsorted(sT, t_to)
                    if j1 > j0:
                        sidx = ((sT[j0:j1] - t_from) / step).astype(np.int64).clip(0, n - 1)
                        if len(sidx) > 1 and np.any(np.diff(sidx) < 0):
                            o_ = np.argsort(sidx, kind="stable"); sidx = sidx[o_]; seg = sB[j0:j1][o_]
                        else:
                            seg = sB[j0:j1]
                        st_ = np.concatenate([[0], np.flatnonzero(np.diff(sidx)) + 1])
                        mx = np.maximum.reduceat(seg, st_, axis=0)      # je Abschnitt das lauteste je Band (schnell, auch fuer 24 h)
                        out["spec"] = {"bands": Terz.CENTERS, "b": [[int(t_from + int(sidx[k]) * step), base64.b64encode(mx[i].tobytes()).decode()] for i, k in enumerate(st_)]}
            r1 = lambda v: None if not np.isfinite(v) else round(float(v), 1)
            r0 = lambda v: None if not np.isfinite(v) else int(round(float(v)))
            out["pts"] = [[int(t_from + idx[s] * step), r1(pk[j]), r1(eqm[j]), r1(bg[j]), r1(th[j]), int(ac[j]) if np.isfinite(ac[j]) else 0,
                           r1(lay[0][j]), r1(lay[1][j]), r1(lay[2][j]), r0(lay[3][j]), r0(lay[4][j])]
                          for j, s in enumerate(starts)]
            out["step"] = step
    out["evx"] = []
    em_ = evmeta_all()
    for r in read_log():                                 # Stoerungen dieses Geraets im Ausschnitt; die der anderen Geraete schwaecher markiert
        own_ = (r.get("quelle_id") or "main") == sid
        try:
            t = int(dt.datetime.fromisoformat(r["start"]).timestamp() * 1000)
        except ValueError:
            continue
        if not (t_from - 300000 <= t <= t_to):
            continue
        virt_ = is_virtual(r.get("datei"))
        m_ = em_.get(os.path.splitext(os.path.basename(r.get("datei") or ""))[0]) if virt_ else None
        if m_:
            t, dur_ = int(m_["t0"]), int(m_["t_end"] - m_["t0"])
        else:
            dur_ = int((fnum(r["dauer_s"]) or 0) * 1000)
        if not own_:
            out["evx"].append([t, dur_, fnum(r["spitze_dbfs"]), r.get("quelle_id") or "main"])
            continue
        a_ = art_fields(r.get("datei") or "")                # erkannte Art je Stoerung (fuer das Muster ueber den Tag)
        try:
            nt_ = note_count(event_stem(r))
        except Exception:
            nt_ = 0
        out["ev"].append([t, dur_, fnum(r["spitze_dbfs"]), {"th": fnum(r.get("schwelle_dbfs")), "bg": fnum(r.get("hintergrund_dbfs")),   # Einzelheiten fuer den Tooltip
                          "a": a_["art"] if art_enabled() else "", "ac": a_["art_c"], "am": a_["art_man"], "p": a_["prof"], "pc": a_["prof_c"], "pbg": a_["bg"], "nt": nt_}])
        if a_["art"] or a_["prof"]:
            out["art"].append([t, a_["art"] or "other", bool(a_["art_man"]), a_["prof"], a_["bg"]])
        if t_to - t_from <= 3 * 3600000 and len(out["subs"]) < 3000 and ((r.get("datei") or "").endswith(SPUR_EXT) or m_):
            st_ = os.path.splitext(os.path.basename(r["datei"]))[0]
            ki_ = ki_load(st_) or {}
            if ki_.get("marks"):
                if m_ and ki_.get("subs") is not None:
                    t0_, subs_ = int(m_["t_from"]), ki_["subs"]
                else:
                    g_ = track_for(r["datei"])
                    t0_ = g_.get("t0") if g_ else None
                    subs_ = (ki_.get("subs") or sub_events(ki_.get("marks"), g_)) if g_ else []
                if t0_:
                    for x in subs_[:200]:
                        out["subs"].append([t0_ + int(x[0]), x[1], x[2], x[3], x[4]]); kinds_.add(x[1])
        if (r.get("datei") or "").endswith(SPUR_EXT) and t_to - t_from <= 3 * 3600000:
            out["sp"].append([t, t + int((fnum(r.get("clip_s")) or 60) * 1000), os.path.basename(r["datei"])])
    out["pa"] = scan_areas(sid, t_from, t_to)            # Bereiche aus „Neu untersuchen“ (Profile, auch unter der Schwelle)
    if t_to - t_from <= 3 * 3600000:                      # mitgespeicherte Spuren dieses Geraets (Stoerung an einem anderen Geraet)
        for f in glob.glob(os.path.join(co_dir(), "*__" + glob.escape(sid) + SPUR_EXT)):
            b = os.path.basename(f)
            try:
                t = int(dt.datetime.strptime(b[:15], "%Y%m%d_%H%M%S").timestamp() * 1000)
            except ValueError:
                continue
            if t_from - 300000 <= t <= t_to:
                out["sp"].append([t, t + 120000, "mit/" + b])
    out["ha"] = ha_intervals(sid, t_from, t_to)
    out["hav"] = ha_volumes(sid, t_from, t_to)           # Lautstaerke des Fernsehers (falls gemeldet)
    out["fn"] = [[x["a"], x["b"], x.get("text", ""), x["id"], x.get("tags") or []] for x in fnotes_in(t_from, t_to, sid)]
    if kinds_ and classify is not None:
        fm = classify.fine_meta("en" if CFG.get("language") == "en" else "de")
        out["fine"] = {k: fm[k] for k in kinds_ if k in fm}
    return out


# =====================================================================
# Mitspeichern: loest ein Geraet aus, speichern alle anderen fuer denselben Zeitraum eine Laermspur
# (Pegel und Spektrum, nie Ton oder Video). Ablage clips/mit/<Ereignis>__<Geraet>.lsp, kein eigener Eintrag.
# =====================================================================
def co_dir():
    return os.path.join(paths()[1], "mit")


def co_files(stem):
    return sorted(glob.glob(os.path.join(co_dir(), glob.escape(stem) + "__*" + SPUR_EXT)))


def co_enqueue(runner, stem, t0, t_from, t_to, clip_s):
    if not CFG.get("co_record", True):
        return
    with SRC_LOCK:
        others = [r for r in RUNNERS.values() if r is not runner]
    for o in others:
        with o.rlock:
            ok = bool(o.spur) and o.spur[-1][0] >= t0 - 2000 and o.spur[0][0] <= t0
        if not ok:                                     # Geraet liefert gerade nichts
            continue
        st = o.status
        job = {"stem": stem, "path": os.path.join(co_dir(), f"{stem}__{o.id}{SPUR_EXT}"), "t_from": t_from, "t_to": t_to, "due": t_to + 300,
               "meta": {"start": dt.datetime.fromtimestamp(t0 / 1000.0).astimezone().isoformat(timespec="seconds"),
                        "peak": None, "thr": st.get("thr"), "base": st.get("base"), "core": [t0 - t_from, t0 - t_from + int(clip_s * 1000)],
                        "co_of": runner.id, "co_name": runner.name}}
        try:
            os.makedirs(co_dir(), exist_ok=True)
            write_spur(o, job, final=False)
            with o.plock:
                o.pending.append(job)
        except Exception as e:
            log(f"[{o.name}] Mitspeichern nicht moeglich:", e)


def co_compare(row, g, stem):
    """Pegel aller Geraete im Kern der Stoerung: ausloesendes Geraet und mitgespeicherte. Dazu Einpegel-Stand."""
    if not g or not g.get("core") or "t0" not in g:
        return []
    a, b = g["t0"] + g["core"][0], g["t0"] + g["core"][1]

    def peak_of(x):
        v = [r[1] for r in x.get("recs") or [] if a < x["t0"] + r[0] <= b + Terz.STEP_MS and r[1] is not None]
        return round(max(v), 1) if v else None
    with SRC_LOCK:
        srcs = {r.id: r.src for r in RUNNERS.values()}
    sid = row.get("quelle_id") or "main"
    out = [{"id": sid, "name": row.get("quelle") or sid, "peak": peak_of(g), "own": True, "cal": cal_state(srcs.get(sid))}]
    if g.get("virtual"):                              # ab 1.40: alle Geraete aus der Tagesaufzeichnung, derselbe Zeitraum
        m = meta_of(row)
        if m:
            with SRC_LOCK:
                others = [(r.id, r.name) for r in RUNNERS.values() if r.id != sid]
            for oid, oname in others:
                x = virtual_graph(m, sid=oid, name=oname)
                if not x["recs"]:
                    continue
                out.append({"id": oid, "name": oname, "peak": peak_of(x), "own": False, "cal": cal_state(srcs.get(oid)), "graph": x})
        return out if len(out) > 1 else []
    for f in co_files(stem):
        try:
            x = load_graph(f)
        except (OSError, ValueError, EOFError):
            continue
        oid = x.get("src") or os.path.basename(f)[len(stem) + 2:-len(SPUR_EXT)]
        out.append({"id": oid, "name": x.get("name") or oid, "peak": peak_of(x), "own": False, "cal": cal_state(srcs.get(oid)), "graph": x})
    return out if len(out) > 1 else []


def co_text(cmp):
    if not cmp:
        return ""
    v = [c for c in cmp if c["peak"] is not None]
    if len(v) < 2:
        return ""
    v.sort(key=lambda c: -c["peak"])
    nc = [c["name"] for c in v if not c["cal"]["ok"]]
    top = [c["name"] for c in v if v[0]["peak"] - c["peak"] < 1.0]
    lead = f'am lautesten: {top[0]}' if len(top) == 1 else f'etwa gleich laut (unter 1 dB): {", ".join(top)}'
    return ("Vergleich der Geräte (Spitze): " + " · ".join(f'{c["name"]} {c["peak"]:.1f}' for c in v) + f' dBFS → {lead}'
            + (" (alle eingepegelt)" if not nc else f' (nicht eingepegelt: {", ".join(nc)})'))


# =====================================================================
# Einpegeln: alle Geraete messen gleichzeitig dasselbe gleichmaessige Geraeusch; die Verstaerkung wird so
# angepasst, dass alle denselben Pegel zeigen. Jede Messung wird protokolliert (clips/einpegeln.json).
# =====================================================================
CAL = {"state": "idle", "q0": 0, "q1": 0, "t0": 0, "t1": 0, "secs": 15, "ref": "", "ids": [], "target": None, "res": [], "msg": "", "base": {}}
CAL_LOCK = threading.Lock()


def cal_path():
    return os.path.join(paths()[1], "einpegeln.json")


def cal_log():
    d = read_json(cal_path()) if os.path.exists(cal_path()) else {}
    return d.get("log") if isinstance(d, dict) and isinstance(d.get("log"), list) else []


def cal_state(src):
    """Einpegel-Stand eines Geraets: ok nur, wenn die Verstaerkung seitdem nicht geaendert wurde."""
    c = (src or {}).get("cal") or {}
    if not c.get("at"):
        return {"ok": False, "at": "", "changed": False}
    same = abs(float(c.get("gain", 0)) - float((src or {}).get("gain_db", 0) or 0)) < 0.01
    return {"ok": same, "at": c["at"], "changed": not same}


def cal_start(secs, ids=None):
    with CAL_LOCK:
        if CAL["state"] == "running":
            return {"ok": False, "error": "busy"}
        secs = max(5, min(60, int(secs or 15)))
        with SRC_LOCK:
            base = {r.id: r.status.get("base") for r in RUNNERS.values()}
        now = int(time.time() * 1000)
        # 5 s Ruhe (Grundpegel), 3 s zum Einschalten des Geraeuschs, dann Messung
        ids = [str(x)[:16] for x in (ids or []) if isinstance(x, str)][:24]     # ausgewaehlte Geraete (leer = alle)
        CAL.update(state="running", q0=now, q1=now + 5000, t0=now + 8000, t1=now + 8000 + secs * 1000, secs=secs, ref="mean", ids=ids, target=None, res=[], msg="", base=base)
    threading.Thread(target=cal_run, daemon=True).start()
    return {"ok": True}


def cal_run():
    time.sleep(max(0.0, (CAL["t1"] - time.time() * 1000) / 1000.0 + 1.0))
    with SRC_LOCK:
        runners = [r for r in RUNNERS.values() if not CAL["ids"] or r.id in CAL["ids"]]
    res = []
    for r in runners:
        with r.rlock:
            v = [x[2] for x in r.spur if CAL["t0"] < x[0] <= CAL["t1"] and x[2] is not None and x[2] > -125]
            pre = [x[2] for x in r.spur if CAL["q0"] < x[0] <= CAL["q1"] and x[2] is not None and x[2] > -125]
        need = int(CAL["secs"] * 1000 / Terz.STEP_MS * 0.8)
        e = {"id": r.id, "name": r.name, "gain_old": r.src.get("gain_db", 0) or 0, "n": len(v)}
        if len(v) < need:
            e.update(ok=False, why="nodata")
        else:
            a = np.asarray(v)
            lvl = 10 * np.log10(np.mean(10 ** (a / 10)))       # energetischer Mittelwert
            bg = float(np.median(pre)) if len(pre) >= 20 else CAL["base"].get(r.id)    # Ruhepegel vor der Messung
            e.update(level=round(float(lvl), 1), std=round(float(np.std(a)), 1), snr=None if bg is None else round(float(lvl - bg), 1),
                     quiet=None if bg is None else round(float(bg), 1))
            e["ok"] = (e["snr"] is None or e["snr"] >= 10) and e["std"] <= 6
            e["why"] = "" if e["ok"] else ("quiet" if e["snr"] is not None and e["snr"] < 10 else "unsteady")
        res.append(e)
    good = [e for e in res if e["ok"]]
    # Ziel: Mittelwert der gemessenen Pegel aller ausgewaehlten Geraete; jedes Geraet wird mit seiner eigenen Verstaerkung dorthin gebracht
    target = round(float(np.mean([e["level"] for e in good])), 1) if good else None
    for e in res:
        if e["ok"] and target is not None:
            e["delta"] = round(target - e["level"], 1)
            e["gain_new"] = max(-20.0, min(40.0, round((e["gain_old"] + e["delta"]) * 2) / 2))
    with CAL_LOCK:
        CAL.update(state="done", res=res, ref="mean", target=target, msg="" if len(good) >= 2 else "few")


def cal_apply(apply=True, note=""):
    """Ergebnis uebernehmen (Verstaerkung anpassen) oder nur protokollieren. Beides wird festgehalten."""
    with CAL_LOCK:
        if CAL["state"] != "done":
            return {"ok": False, "error": "no result"}
        res = [dict(e) for e in CAL["res"]]; ref = CAL["ref"]; target = CAL.get("target")
        CAL["state"] = "idle"
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    with SRC_LOCK:
        for e in res:
            r = RUNNERS.get(e["id"])
            if r is None or not e.get("ok"):
                continue
            if apply and "gain_new" in e:
                g = e["gain_new"]; r.src["gain_db"] = int(g) if float(g).is_integer() else g
                if abs(e["gain_new"] - e["gain_old"]) >= 0.5:
                    r.relearn.set()                          # Hintergrund mit neuer Verstaerkung neu lernen
            r.src["cal"] = {"at": now, "gain": r.src.get("gain_db", 0) or 0, "ref": ref, "level": e.get("level")}
    save_sources()
    entry = {"at": now, "kind": "apply" if apply else "check", "ref": ref, "target": target, "secs": CAL["secs"], "note": clean_text(note, 300),
             "res": [{k: e.get(k) for k in ("id", "name", "level", "quiet", "std", "snr", "ok", "why", "gain_old", "gain_new", "delta")} for e in res]}
    lg = cal_log() + [entry]
    f = cal_path(); os.makedirs(os.path.dirname(f), exist_ok=True)
    with open(f + ".tmp", "w", encoding="utf-8") as fh:
        json.dump({"v": 1, "log": lg[-500:]}, fh, ensure_ascii=False, indent=1)
    os.replace(f + ".tmp", f)
    log("Einpegeln", "uebernommen:" if apply else "protokolliert:", json.dumps(entry["res"], ensure_ascii=False))
    return {"ok": True, "entry": entry, "sources": sources_payload()}


def cal_payload():
    with CAL_LOCK:
        c = {k: CAL[k] for k in ("state", "q0", "q1", "t0", "t1", "secs", "ref", "ids", "target", "res", "msg")}
    c["now"] = int(time.time() * 1000); c["log"] = cal_log()[-10:][::-1]
    return c


# =====================================================================
# Komplette Sicherung der App (Einstellungen, Geraete, Ereignisse, Laermspuren, Notizen, Listen, Videos, Ton)
# Einspielen fuehrt zusammen: Vorhandenes bleibt, nur Fehlendes kommt dazu (keine Doppelten).
# =====================================================================
import zipfile

BACKUP_FMT = "laerm_backup"
BK_PENDING = {"path": None, "at": 0}       # hochgeladene Sicherung, die auf „Einspielen“ wartet
BK_STATE = {"state": "idle", "done": 0, "total": 0, "msg": "", "stats": {}, "restart": False}
BK_LOCK = threading.Lock()
BK_STORED = (".mp4", ".wav", SPUR_EXT, ".gz", ".zip", ".jpg", ".png")


class ChunkedOut:
    """Schreibt in den Antwortstrom mit Transfer-Encoding: chunked (Groesse vorher unbekannt)."""

    def __init__(self, w):
        self.w = w; self.buf = bytearray()

    def write(self, b):
        self.buf += b
        if len(self.buf) >= 262144:
            self.flush()
        return len(b)

    def flush(self):
        if self.buf:
            self.w.write(b"%x\r\n" % len(self.buf) + bytes(self.buf) + b"\r\n"); self.buf = bytearray()

    def close(self):
        self.flush(); self.w.write(b"0\r\n\r\n")


def backup_items():
    """(Name im Archiv, Datei) fuer alles, was zur App gehoert."""
    out, clips, _ = paths()
    items = []
    for name, f in (("data/settings.json", None), ("data/sources.json", SOURCES_FILE), ("data/schedule.json", SCHED_FILE), ("data/ha_rules.json", HA_FILE),
                    ("data/laufzeit.jsonl", os.path.join(DATA_DIR, "laufzeit.jsonl")), ("data/unterbrechung_notizen.json", run_notes_path())):
        if f and os.path.isfile(f):
            items.append((name, f))
    skip = lambda fn: fn.endswith(".tmp") or fn.startswith(".import_")
    co = os.path.realpath(clips)
    for base, arc in ((out, "out"), (clips, "clips")):
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            if arc == "out" and os.path.realpath(root) == co:
                dirs[:] = []; continue
            dirs[:] = [d for d in dirs if not (arc == "out" and os.path.realpath(os.path.join(root, d)) == co)]
            for fn in sorted(files):
                if skip(fn):
                    continue
                f = os.path.join(root, fn)
                items.append((arc + "/" + os.path.relpath(f, base).replace(os.sep, "/"), f))
    with SRC_LOCK:
        vds = [(r.id, safe_dir(r.src.get("video_dir"))) for r in RUNNERS.values()]
    seen = {co}
    for sid, d in vds:
        if not d or os.path.realpath(d) in seen or not os.path.isdir(d):
            continue
        seen.add(os.path.realpath(d))
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".mp4") and os.path.isfile(os.path.join(d, fn)):
                items.append((f"video/{sid}/{fn}", os.path.join(d, fn)))
    return items


def backup_write(stream):
    zf = zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
    items = backup_items(); n = 0
    man = {"fmt": BACKUP_FMT, "v": 1, "app": VERSION, "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "files": len(items)}
    zf.writestr("manifest.json", json.dumps(man, ensure_ascii=False, indent=1))
    zf.writestr("data/settings.json", json.dumps(public_settings(), ensure_ascii=False, indent=1))
    for arc, f in items:
        if f is None:
            continue
        try:
            zf.write(f, arc, compress_type=zipfile.ZIP_STORED if f.endswith(BK_STORED) else zipfile.ZIP_DEFLATED)
            n += 1
        except (OSError, ValueError) as e:              # Datei waehrend der Sicherung geloescht o. ae.
            log("Sicherung: Datei uebersprungen:", arc, e)
    zf.close()
    log(f"Sicherung heruntergeladen: {n} Dateien")


def merge_json(dst, src):
    """Fehlendes aus src in dst uebernehmen; Vorhandenes bleibt. Listen: nur neue Eintraege anhaengen."""
    if isinstance(dst, dict) and isinstance(src, dict):
        for k, v in src.items():
            if k not in dst:
                dst[k] = v
            else:
                dst[k] = merge_json(dst[k], v)
        return dst
    if isinstance(dst, list) and isinstance(src, list):
        have = {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in dst}
        for x in src:
            s = json.dumps(x, sort_keys=True, ensure_ascii=False)
            if s not in have:
                dst.append(x); have.add(s)
        return dst
    return dst


def merge_lines(dst, data):
    """CSV: Zeilen anhaengen, die es noch nicht gibt (Kopfzeile nur einmal; andere Spaltenreihenfolge wird angepasst)."""
    if not os.path.exists(dst):
        with open(dst, "wb") as f:
            f.write(data)
        return max(0, len(data.splitlines()) - 1)
    with open(dst, encoding="utf-8-sig", errors="replace", newline="") as f:
        old = f.read()
    orows = list(csv.reader(old.splitlines())); nrows = list(csv.reader(data.decode("utf-8-sig", "replace").splitlines()))
    if not nrows:
        return 0
    if not orows:
        with open(dst, "wb") as f:
            f.write(data)
        return len(nrows) - 1
    oh, nh = orows[0], nrows[0]
    if oh != nh and set(oh) & set(nh):                       # anderer Aufbau (aeltere Version): Spalten zuordnen
        ix = {c: i for i, c in enumerate(nh)}
        body = [[r[ix[c]] if c in ix and ix[c] < len(r) else "" for c in oh] for r in nrows[1:]]
    else:
        body = nrows[1:]
    have = {tuple(r) for r in orows}
    add = []
    for r in body:
        if r and any(r) and tuple(r) not in have:
            add.append(r); have.add(tuple(r))
    if add:
        with open(dst, "a", encoding="utf-8", newline="") as f:
            if old and not old.endswith("\n"):
                f.write("\n")
            csv.writer(f).writerows(add)
    return len(add)


def merge_plists(src, idmap):
    """Listen zusammenfuehren: gleiche ID -> Eintraege ergaenzen; anderer Liste mit gleichem Namen -> neue Liste „(importiert)“."""
    if not isinstance(src, dict):
        return 0
    imp = "imported" if CFG.get("language") == "en" else "importiert"
    with PLISTS_LOCK:
        d = plists_all(); n = 0
        for x in src.get("lists") or []:
            if not isinstance(x, dict) or not re.fullmatch(r"l[0-9a-f]{1,16}", str(x.get("id", ""))):
                continue
            lid = x["id"]; mem = (src.get("mem") or {}).get(lid) or {}
            cur = plist_by_id(lid)
            if cur is None:
                same = any(y["name"] == x.get("name") for y in d["lists"])
                nid = "l" + secrets.token_hex(5) if same else lid
                if len(d["lists"]) >= PLIST_MAX:
                    continue
                d["lists"].append({"id": nid, "name": (str(x.get("name") or "")[:46] + (f" ({imp})" if same else "")),
                                   "note": clean_text(x.get("note"), 2000), "created": str(x.get("created") or "")[:40]})
                cur = plist_by_id(nid); n += 1
            elif not cur.get("note") and x.get("note"):
                cur["note"] = clean_text(x.get("note"), 2000)
            idmap[lid] = cur["id"]
            m = d["mem"].setdefault(cur["id"], {})
            for st, v in (mem.items() if isinstance(mem, dict) else []):
                m.setdefault(st, v)
        plists_save()
    return n


DAY_GRP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+?)(\.ltg|\.chk|\.lts|\.lfp|_\d\d\.ltp)$")


def _ltg_minutes(raw):
    """Minuten (m) aller Bloecke einer Tagesdatei (gzip-Bloecke, je eine JSON-Zeile)."""
    try:
        txt = gzip.decompress(raw).decode("utf-8", "replace")
    except (OSError, EOFError, zlib.error):
        return None
    out = []
    for l_ in txt.splitlines():
        mm_ = re.match(r'\{"m":(-?\d+),', l_)
        if mm_:
            out.append(int(mm_.group(1)))
    return out


def day_merge(sid, day, inc):
    """Tag eines Geraets aus der Sicherung mit dem vorhandenen zusammenfuehren (Tagesaufzeichnung, Pruefsummen, Spektrum,
    Fingerabdruck). inc: {Endung: Bytes}. Ueberschneiden sich die Minuten, bleibt alles wie es ist (gleiche Daten).
    Der eingespielte Teil kommt zuerst in die Datei, der vorhandene folgt als eigener Abschnitt der Pruefsummen-Kette (R),
    damit die laufende Aufnahme dahinter weiter anhaengt. Rueckgabe: ("merged", Minuten) | ("same"|"overlap"|"bad", 0)."""
    dp = day_path(sid, day)
    with DAYW_LOCK, SPEC_LOCK:
        try:
            have = open(dp, "rb").read()
        except OSError:
            have = b""
        new = inc.get(".ltg") or b""
        mh, mn = _ltg_minutes(have) or [], _ltg_minutes(new)
        if mn is None:
            return ("bad", 0)
        if not mn:
            return ("same", 0)
        if set(mn) & set(mh):
            return ("same" if set(mn) <= set(mh) else "overlap", 0)
        cf = chain_file(sid, day)
        try:
            ch_have = [l for l in open(cf, encoding="utf-8").read().splitlines() if l.strip()]
        except OSError:
            ch_have = []
        ch_new = [l for l in (inc.get(".chk") or b"").decode("utf-8", "replace").splitlines() if l.strip()]
        if ch_have and ch_new:                       # vorhandener Teil: neuer Abschnitt der Kette
            p_ = ch_have[0].split(); ch_have[0] = " ".join(p_[:2] + ["R"])
        def wr(path, data):
            with open(path + ".tmp", "wb") as fh:
                fh.write(data); fh.flush(); os.fsync(fh.fileno())
            os.replace(path + ".tmp", path)
        wr(dp, new + have)
        if ch_have or ch_new:
            wr(cf, ("\n".join(ch_new + ch_have) + "\n").encode())
        if inc.get(".lts"):                          # Spektrum: gzip-Bloecke, Reihenfolge egal (wird beim Lesen sortiert)
            sp_ = spec_path(sid, day)
            old_ = open(sp_, "rb").read() if os.path.exists(sp_) else b""
            wr(sp_, inc[".lts"] + old_)
        for ext, data in inc.items():
            if ext.endswith(".ltp") or ext == ".lfp":    # Rohdaten mit eigener Zeit je Satz: anhaengen
                f_ = os.path.join(day_dir(), f"{day}_{sid}{ext}")
                with open(f_, "ab") as fh:
                    fh.write(data)
        for c_ in (DAY_CACHE, CHAIN_CK, SPEC_LTS_CACHE, FP_CACHE):
            c_.clear()
    try:
        with open(os.path.join(DATA_DIR, "laufzeit.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "kind": "import", "day": day, "sid": sid,
                                "minutes": len(mn), "version": VERSION}) + "\n")
    except OSError:
        pass
    log(f"Sicherung: Tag {day} ({sid}) um {len(mn)} Minuten ergaenzt")
    return ("merged", len(mn))


FORMER = {"key": None, "list": []}


def former_sources():
    """Geraete, von denen es Daten gibt (Tagesaufzeichnung oder Stoerungen), die aber nicht mehr eingerichtet sind:
    [{id, name}] - z. B. nach dem Einspielen einer Sicherung oder nach dem Entfernen eines Geraets. Nur zum Ansehen."""
    try:
        key = (os.stat(day_dir()).st_mtime_ns, os.path.getsize(paths()[2]))
    except OSError:
        key = None
    with SRC_LOCK:
        cur = set(RUNNERS)
    if FORMER["key"] == key and key is not None:
        return [x for x in FORMER["list"] if x["id"] not in cur]
    names = {}
    for r in read_log():
        q_ = r.get("quelle_id") or "main"
        if q_ not in names or not names[q_]:
            names[q_] = r.get("quelle") or ""
    ids = set(names)
    try:
        for fn in os.listdir(day_dir()):
            mm_ = re.match(r"^\d{4}-\d{2}-\d{2}_(.+?)\.ltg$", fn)
            if mm_:
                ids.add(mm_.group(1))
    except OSError:
        pass
    lst = [{"id": i, "name": names.get(i) or i} for i in sorted(ids) if re.fullmatch(r"[a-z0-9_]{1,24}", i)]
    FORMER.update(key=key, list=lst)
    return [x for x in lst if x["id"] not in cur]


def url_reachable(u, timeout=1.5):
    """Antwortet die Adresse eines Streams (nur Verbindungsaufbau, nichts wird gelesen)?"""
    try:
        sp = urllib.parse.urlsplit(u or "")
        host = sp.hostname; port = sp.port or {"https": 443, "rtsp": 554, "rtmp": 1935}.get(sp.scheme, 80)
        if not host:
            return False
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def backup_preview(path):
    """Was die Sicherung an Geraeten mitbringt und wie es hier aussieht: {devices:[{id,name,type,exists,status}], keep:[{id,name}],
    mic:{device, found}, app, created, files}. status: ok | phone | unreachable."""
    with zipfile.ZipFile(path) as zf:
        try:
            man = json.loads(zf.read("manifest.json"))
        except (KeyError, ValueError):
            man = {}
        if man.get("fmt") != BACKUP_FMT:
            raise ValueError("keine Sicherung dieser App" if CFG.get("language") != "en" else "not a backup of this app")
        rd = lambda n: json.loads(zf.read(n)) if n in zf.namelist() else None
        sr = rd("data/sources.json") or {}; st_ = rd("data/settings.json") or {}
    with SRC_LOCK:
        cur = {r.id: r.src.get("name") or r.id for r in RUNNERS.values()}
    devs = []
    for d in (sr.get("sources") or [] if isinstance(sr, dict) else []):
        if not isinstance(d, dict) or d.get("type") not in SRC_TYPES or not re.fullmatch(r"[a-z0-9_]{1,16}", str(d.get("id", ""))):
            continue
        t_ = d["type"]
        stt = "phone" if t_ == "phone" else ("ok" if t_ == "local" or url_reachable(d.get("url")) else "unreachable")
        devs.append({"id": d["id"], "name": str(d.get("name") or d["id"])[:40], "type": t_, "exists": d["id"] in cur, "status": stt})
    ids = {x["id"] for x in devs}
    dev_ = str(st_.get("device") or "default") if isinstance(st_, dict) else "default"
    names_ = {x["name"] for x in list_sources()[0]}
    return {"ok": True, "app": man.get("app", ""), "created": man.get("created", ""), "files": man.get("files", 0), "devices": devs,
            "keep": [{"id": k, "name": v} for k, v in cur.items() if k not in ids],
            "mic": {"device": dev_, "found": dev_ in ("default", "pulse", "") or dev_ in names_}}


def restore_sources(raw, idmap, pick=None, off=None):
    """Geraete aus der Sicherung uebernehmen: hier eingerichtete Geraete bleiben; gewaehlte aus der Sicherung ersetzen das gleiche
    Geraet bzw. kommen dazu (hoechstens 9). off: nicht erreichbar -> ausgeschaltet uebernehmen, Hinweis „bitte pruefen“."""
    inc = [s_ for s_ in (raw.get("sources") or [] if isinstance(raw, dict) else []) if isinstance(s_, dict)]
    for s_ in inc:
        if isinstance(s_.get("plists"), list):
            s_["plists"] = [dict(r, id=idmap.get(r.get("id"), r.get("id"))) for r in s_["plists"] if isinstance(r, dict)]
    with SRC_LOCK:
        cur = [dict(r.src) for r in RUNNERS.values()]
    out = list(cur); pos = {x["id"]: i for i, x in enumerate(out)}; taken = []
    for s_ in inc:
        sid = str(s_.get("id", ""))
        if pick is not None and sid not in pick:
            continue
        s_ = dict(s_)
        if off and sid in off:
            s_["enabled"] = False; s_["check"] = True
        if sid in pos:
            out[pos[sid]] = s_
        elif len(out) < 9:
            pos[sid] = len(out); out.append(s_)
        else:
            continue
        taken.append(sid)
    tmp = SOURCES_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"sources": out}, f, indent=1); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, SOURCES_FILE)
    lst = load_sources()
    with SRC_LOCK:
        old = list(RUNNERS.values()); RUNNERS.clear()
    for r in old:
        r.stop.set()
        if mq is not None:
            unannounce_source(r.id)
    for s_ in lst:
        add_runner(s_)
    save_sources()
    return taken


def restore_run(path, with_settings, pick=None, off=None):
    out, clips, _ = paths()
    st = {"new": 0, "same": 0, "merged": 0, "lists": 0, "rows": 0}
    try:
        with zipfile.ZipFile(path) as zf:
            try:
                man = json.loads(zf.read("manifest.json"))
            except (KeyError, ValueError):
                man = {}
            if man.get("fmt") != BACKUP_FMT:
                raise ValueError("keine Sicherung dieser App" if CFG.get("language") != "en" else "not a backup of this app")
            names = [i for i in zf.infolist() if not i.is_dir()]
            BK_STATE.update(total=len(names), done=0)
            idmap = {}
            if "clips/listen.json" in zf.namelist():
                try:
                    st["lists"] = merge_plists(json.loads(zf.read("clips/listen.json")), idmap)
                except ValueError:
                    pass
            if with_settings:
                rd = lambda n: json.loads(zf.read(n)) if n in zf.namelist() else None
                s = rd("data/settings.json")
                if isinstance(s, dict):                 # Speicherorte bleiben die dieses Systems (Daten werden dorthin eingespielt)
                    s = {k: v for k, v in s.items() if k not in ("output_dir", "clip_dir")}
                    dv_ = str(s.get("device") or "default")
                    if dv_ not in ("default", "pulse", "") and dv_ not in {x["name"] for x in list_sources()[0]}:
                        st["mic_kept"] = dv_                # Mikrofon der Sicherung gibt es hier nicht: bisheriges bleiben
                        s.pop("device", None); s.pop("mic_port", None)
                    update_settings(s)
                sc = rd("data/schedule.json")
                if isinstance(sc, dict):
                    save_sched(sc.get("slots"))
                ha = rd("data/ha_rules.json")
                if isinstance(ha, dict):
                    save_ha_rules(ha.get("rules"))
                sr = rd("data/sources.json")
                if isinstance(sr, dict):
                    st["devices"] = restore_sources(sr, idmap, pick, off)
                    st["devices_off"] = sorted(off or [])
                BK_STATE["restart"] = True
            with SRC_LOCK:
                vdir = {r.id: safe_dir(r.src.get("video_dir")) for r in RUNNERS.values()}
            dgrp = {}                                   # (Geraet, Tag) -> {Endung: Bytes} fuer Tage, die es schon gibt
            stores = {"notes.json": (NOTES_LOCK, notes_all, notes_save), "bereiche.json": (LABELS_LOCK, labels_all, labels_save),
                      "art.json": (ART_LOCK, art_all, art_save)}
            for i in names:
                BK_STATE["done"] += 1
                a = i.filename
                parts = a.split("/")
                if a == "data/laufzeit.jsonl":              # Laufzeit-Protokoll: fehlende Zeilen anhaengen
                    try:
                        lf = os.path.join(DATA_DIR, "laufzeit.jsonl")
                        have = set(open(lf, encoding="utf-8").read().splitlines()) if os.path.exists(lf) else set()
                        add = [l for l in zf.read(i).decode("utf-8", "replace").splitlines() if l.strip() and l not in have]
                        if add:
                            with open(lf, "a", encoding="utf-8") as f:
                                f.write("\n".join(add) + "\n")
                    except OSError:
                        pass
                    continue
                if a == "data/unterbrechung_notizen.json":   # Kommentare zu Unterbrechungen: fehlende ergaenzen, eigene bleiben
                    try:
                        inc_n = json.loads(zf.read(i))
                        if isinstance(inc_n, dict):
                            with RUN_NOTES_LOCK:
                                d_n = run_notes(); add_n = {k: v for k, v in inc_n.items() if k not in d_n and isinstance(v, str)}
                                if add_n:
                                    d_n.update(add_n)
                                    with open(run_notes_path() + ".tmp", "w", encoding="utf-8") as f:
                                        json.dump(d_n, f, ensure_ascii=False, indent=1)
                                    os.replace(run_notes_path() + ".tmp", run_notes_path())
                            st["merged"] += 1
                    except (ValueError, OSError):
                        pass
                    continue
                if ".." in parts or a.startswith("/") or a in ("manifest.json", "clips/listen.json") or a.startswith("data/"):
                    continue
                if parts[0] == "out" and len(parts) > 1:
                    dst = os.path.join(out, *parts[1:])
                elif parts[0] == "clips" and len(parts) > 1:
                    dst = os.path.join(clips, *parts[1:])
                elif parts[0] == "video" and len(parts) == 3 and parts[2].endswith(".mp4"):
                    dst = os.path.join(vdir.get(parts[1]) or clips, parts[2])
                else:
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                rel = "/".join(parts[1:])
                if parts[0] == "clips" and rel in stores:
                    lock, get, save = stores[rel]
                    try:
                        with lock:
                            merge_json(get(), json.loads(zf.read(i)))
                            if rel == "notes.json":                # freie Notizen: je Kennung nur die neueste Fassung
                                best = {}
                                for x in get().get("free") or []:
                                    k_ = x.get("id"); old = best.get(k_)
                                    if old is None or (x.get("edited") or x.get("ts") or "") > (old.get("edited") or old.get("ts") or ""):
                                        best[k_] = x
                                get()["free"] = list(best.values())
                            save()
                        st["merged"] += 1
                    except ValueError:
                        pass
                    continue
                if parts[0] == "clips" and rel == "ereignisse.jsonl":   # Stoerungen ab 1.40: fehlende anhaengen
                    have = evmeta_all()
                    add = []
                    for l in zf.read(i).decode("utf-8", "replace").splitlines():
                        try:
                            e_ = json.loads(l)
                        except ValueError:
                            continue
                        if isinstance(e_, dict) and e_.get("stem") and e_["stem"] not in have:
                            add.append(e_); have = dict(have, **{e_["stem"]: e_})
                    for e_ in add:
                        evmeta_add(e_)
                    st["merged"] += 1
                    continue
                if parts[0] == "clips" and rel == "profile.json":       # Profile: je Name zusammenfuehren, Beispiele ohne Doppelte
                    try:
                        inc_p = json.loads(zf.read(i)).get("p") or {}
                    except (ValueError, AttributeError):
                        continue
                    with PROF_LOCK:
                        P_ = profiles_all()
                        for nm_, pf_ in inc_p.items():
                            if not isinstance(pf_, dict):
                                continue
                            cur_ = P_.setdefault(nm_, {"ex": [], "created": pf_.get("created", ""), "bg": bool(pf_.get("bg"))})
                            ids_ = {x.get("id") for x in cur_.get("ex") or []}
                            cur_.setdefault("ex", []).extend(x for x in pf_.get("ex") or [] if isinstance(x, dict) and x.get("id") not in ids_)
                            cur_["bg"] = bool(cur_.get("bg") or pf_.get("bg"))
                        profiles_save()
                    PROTO_CACHE.clear(); st["merged"] += 1
                    continue
                if parts[0] == "clips" and rel in ("spuren_kette.json", "einpegeln.json"):
                    with SPUR_CHAIN_LOCK:
                        ch = read_json(dst) if os.path.exists(dst) else {}
                        try:
                            ch = merge_json(ch if isinstance(ch, dict) else {}, json.loads(zf.read(i)))
                        except ValueError:
                            continue
                        with open(dst + ".tmp", "w") as f:
                            json.dump(ch, f)
                        os.replace(dst + ".tmp", dst)
                    continue
                if a.endswith(".csv"):
                    with LOG_LOCK:
                        n = merge_lines(dst, zf.read(i))
                    if rel == "log.csv":
                        st["rows"] += n
                    st["merged"] += 1
                    continue
                gm = DAY_GRP_RE.match(parts[-1]) if parts[0] == "clips" and len(parts) == 3 and parts[1] == "tag" else None
                if gm and os.path.exists(day_path(gm.group(2), gm.group(1))):   # Tag gibt es hier schon: nach dem Durchlauf zusammenfuehren
                    dgrp.setdefault((gm.group(2), gm.group(1)), {})[gm.group(3)] = zf.read(i)
                    continue
                if os.path.exists(dst):
                    st["same"] += 1
                    continue
                with zf.open(i) as src, open(dst + ".tmp", "wb") as f:
                    shutil.copyfileobj(src, f, 1 << 20)
                os.replace(dst + ".tmp", dst)
                if i.date_time:
                    try:
                        ts = time.mktime(i.date_time + (0, 0, -1)); os.utime(dst, (ts, ts))
                    except (OverflowError, ValueError):
                        pass
                st["new"] += 1
            st["days_merged"] = []; st["days_skipped"] = []
            for (sid_, day_), inc_ in sorted(dgrp.items(), key=lambda x: (x[0][1], x[0][0])):
                if ".ltg" not in inc_:
                    continue
                res_, n_ = day_merge(sid_, day_, inc_)
                if res_ == "merged":
                    st["days_merged"].append([day_, sid_, n_])
                elif res_ == "same":
                    st["same"] += 1
                else:
                    st["days_skipped"].append([day_, sid_, res_])
        LOG_CACHE["key"] = None; PROTO_CACHE.clear(); LEVEL_CACHE.clear()
        BK_STATE.update(state="done", stats=st, msg="")
        log("Sicherung eingespielt:", json.dumps(st), "mit Einstellungen" if with_settings else "")
        if art_enabled():
            threading.Thread(target=kinds_backfill, daemon=True).start()
    except Exception as e:
        if isinstance(e, zipfile.BadZipFile):
            e = ValueError("keine gültige ZIP-Datei" if CFG.get("language") != "en" else "not a valid ZIP file")
        BK_STATE.update(state="error", msg=str(e)[:200])
        log("Sicherung einspielen fehlgeschlagen:", e)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# =====================================================================
# Web-Server (Ingress) fuer das Panel
# =====================================================================
DIAG = {"t": 0.0, "text": ""}


def describe_mixer():
    cards = usb_cards()
    if not cards:
        devs = sorted(glob.glob("/dev/snd/*"))
        if not any("controlC" in d for d in devs):
            return ("Soundkarten-Regler: kein Zugriff (/dev/snd/controlC* fehlt). Das Add-on einmal ganz stoppen und "
                    "wieder starten, damit die neue Berechtigung gilt." + (f" Vorhanden: {', '.join(devs)}" if devs else ""))
        return "Soundkarten-Regler: keine USB-Soundkarte gefunden. Vorhanden: " + ", ".join(devs)
    lines = []
    for card in cards:
        ctl, err = mixer_controls(card)
        if ctl is None:
            lines.append(f"Soundkarte {card}: Regler nicht erreichbar ({err}) – Add-on neu starten nach dem Update")
            continue
        lines.append(f"Soundkarte {card} (Regler):")
        for name, c in ctl.items():
            kind = "Aufnahme" if c["cap"] else "Wiedergabe/sonstig"
            lines.append(f"   {name}: {c['val'] or '-'}  ({kind})")
    return "\n".join(lines)


def diag_text():
    if time.time() - DIAG["t"] > 5:
        DIAG.update(t=time.time(), text=describe_sources() + "\n\n" + describe_mixer())
    return DIAG["text"]


EVENTS_MAX = 5000      # hoechstens so viele Zeilen in der Ereignisliste (0 = "alle" bis zu dieser Grenze)


def incidents(rows):
    """Stoerungen ueber alle Geraete zusammenfassen: ueberlappende Ausschlaege verschiedener Geraete = eine Stoerung
    (das lauteste Geraet fuehrt). Aufeinanderfolgende Stoerungen derselben Art bzw. desselben Profils mit hoechstens
    group_pause_s Abstand bilden eine Gruppe. rows: mit Schluessel k, nach Beginn sortiert. Rueckgabe: (je k: (inc, grp), incs, grps)."""
    items = []
    for r in rows:
        a, b = row_core(r)
        if a is None:
            continue
        af = art_fields(r.get("datei") or "")
        items.append((a, b, r, af))
    items.sort(key=lambda x: x[0])
    incs = []
    for a, b, r, af in items:
        sid = r.get("quelle_id") or "main"
        cur = incs[-1] if incs else None
        if cur is not None and a <= cur["b"] + 1000 and sid not in cur["sids"]:
            cur["b"] = max(cur["b"], b); cur["m"].append((r, af)); cur["sids"].add(sid)
        else:
            incs.append({"a": a, "b": b, "m": [(r, af)], "sids": {sid}})
    pause = int(CFG.get("group_pause_s", 120) or 120) * 1000
    by_k, I, G = {}, {}, {}
    grp = None
    for i, inc in enumerate(incs):
        lead_r, lead_af = max(inc["m"], key=lambda x: fnum(x[0].get("spitze_dbfs")) if fnum(x[0].get("spitze_dbfs")) is not None else -999)
        prof = next((af["prof"] for _, af in inc["m"] if af.get("prof")), "")
        kind = ("p:" + prof) if prof else ("a:" + (lead_af.get("art") or "?"))
        bg = bool(prof) and profile_bg(prof)
        if grp is None or grp["kind"] != kind or inc["a"] - grp["b"] > pause:
            grp = {"id": len(G), "kind": kind, "n": 0, "a": inc["a"], "b": inc["b"], "bg": bg}
            G[grp["id"]] = grp
        grp["n"] += 1; grp["b"] = max(grp["b"], inc["b"])
        I[i] = {"a": inc["a"], "b": inc["b"], "lead": lead_r["k"], "grp": grp["id"], "bg": bg,
                "devs": sorted([[x.get("quelle_id") or "main", x.get("quelle") or "", fnum(x.get("spitze_dbfs")), x["k"]] for x, _ in inc["m"]],
                               key=lambda d: -(d[2] if d[2] is not None else -999))}
        for x, _ in inc["m"]:
            by_k[x["k"]] = (i, grp["id"])
    iso = lambda ms: dt.datetime.fromtimestamp(ms / 1000.0).astimezone().isoformat(timespec="seconds")
    grps = {g["id"]: {"kind": g["kind"][2:], "prof": g["kind"].startswith("p:"), "n": g["n"], "a": iso(g["a"]), "b": iso(g["b"]),
                      "dur": round((g["b"] - g["a"]) / 1000.0, 1), "bg": g["bg"]} for g in G.values()}
    return by_k, I, grps


def events_summary(src="all", n=200, plist="", rng=None, art=""):
    allrows = read_log()
    keyed = [dict(r, k=k) for r, k in zip(allrows, row_keys(allrows))]
    if rng:                                          # Zeitraum (Reiter Protokolle)
        a_, b_ = rng[0].strftime("%Y-%m-%dT%H:%M:%S"), rng[1].strftime("%Y-%m-%dT%H:%M:%S")
        keyed = [r for r in keyed if a_ <= (r.get("start") or "")[:19] < b_]
    keyed = sorted(keyed, key=lambda r: r.get("start") or "")
    by_k, I, G = incidents(keyed)                    # ueber alle Geraete (auch wenn unten nach einem Geraet gefiltert wird)
    rows = keyed if src == "all" else [r for r in keyed if r["quelle_id"] == src]
    if plist or art:                                 # Protokollliste, Art
        rows = [r for r in rows if ev_match(r, r["k"], plist, art)]
    # Ein Eintrag wird erst am Ende des Ereignisses geschrieben; lange Ereignisse stehen daher spaeter in der Datei.
    # Fuer die Liste nach Beginn sortieren (stabil, gleiche Startzeit behaelt die Dateireihenfolge).
    hours = [0] * 24
    days = collections.Counter()
    seen, bg_n = set(), 0
    for r in rows:                                   # gezaehlt wird je Stoerung (nicht je Geraet), Hintergrund-Profile nicht
        ig = by_k.get(r["k"])
        if ig is not None:
            if ig[0] in seen:
                continue
            seen.add(ig[0])
            if I[ig[0]]["bg"]:
                bg_n += 1; continue
        try:
            days[r["start"][:10]] += 1; hours[int(r["start"][11:13])] += 1
        except (ValueError, IndexError):
            pass
    out_rows = []
    for r in rows[-(n or EVENTS_MAX):][::-1]:
        e = ev_row(r)
        ig = by_k.get(r["k"])
        if ig is not None:
            inc = I[ig[0]]
            e.update(inc=ig[0], grp=ig[1], lead=inc["lead"] == r["k"], devs=inc["devs"], inc_bg=inc["bg"])
        out_rows.append(e)
    used_i = {e["inc"] for e in out_rows if "inc" in e}; used_g = {e["grp"] for e in out_rows if "grp" in e}
    return {"total": sum(days.values()), "rows": len(rows), "bg_n": bg_n, "today": days.get(dt.date.today().isoformat(), 0), "hours": hours,
            "days": sorted(days.items(), reverse=True)[:(62 if rng else 14)], "n": n,
            "events": out_rows, "grps": {str(k): v for k, v in G.items() if k in used_g},
            "fine": classify.fine_meta("en" if CFG.get("language") == "en" else "de") if classify is not None else {}}


def ev_row(r):
    stem = event_stem(r, int(r["k"].rsplit("|", 1)[1] or 0))
    ls = labels_all().get(stem, {}).get("l") or []
    a_, b_ = row_span(r)
    fn_ = len(fnotes_in(a_, b_, r.get("quelle_id") or "main")) if a_ is not None else 0     # freie Notizen in der Zeit der Stoerung
    au_ = has_audio(r)
    return dict(r, video=has_video(r), audio=au_, play=bool(au_ and audio_allowed(r)), notes=note_count(stem) + fn_, fnotes=fn_, labels=sorted({x["name"] for x in ls}), plists=plists_of(stem),
                **art_fields(r["datei"] or stem))


def get_runner(q):
    sid = (q.get("src") or ["main"])[0]
    with SRC_LOCK:
        return RUNNERS.get(sid) or RUNNERS.get("main")


def status_payload(r, full=True):
    s = dict(r.status)
    LIVE_WANT[r.id] = time.time()
    la = LIVE_ART.get(r.id)
    s["live_art"] = la if la and time.time() * 1000 - la["ts"] < 6000 else None
    if not full:
        s.pop("bands", None)
    s["age"] = round(time.time() - s["ts"] / 1000.0, 2) if s["ts"] else 999
    s["count_today"] = r.count_today; s["count_total"] = r.count_total
    s["all_today"] = STATE["count"]; s["all_total"] = STATE["total"]
    s["src"] = r.id; s["type"] = r.src["type"]; s["enabled"] = r.src.get("enabled", True)
    s["paused"] = RUN["paused"]; s["paused_since"] = RUN["since"]; s["paused_until"] = RUN["until"] if RUN["paused"] else None; s["paused_reason"] = RUN["reason"]
    s["slot"] = slot_label(r.src)
    if r.push is not None:
        s["phone_online"] = r.push.online
    return s


SUP_INFO = {"t": 0.0, "port": None, "ip": None}


def phone_info():
    """Port und IP, unter denen Handys das Add-on erreichen (aus der Supervisor-API, sonst Umgebung)."""
    if time.time() - SUP_INFO["t"] < 60:
        return SUP_INFO
    SUP_INFO["t"] = time.time()
    port = int(os.environ.get("LAERM_PHONE_PORT", "0")) or None
    ip = os.environ.get("LAERM_LAN_IP") or None
    token = os.environ.get("SUPERVISOR_TOKEN")
    if token:
        hdr = {"Authorization": f"Bearer {token}"}
        try:
            with urllib.request.urlopen(urllib.request.Request("http://supervisor/addons/self/info", headers=hdr), timeout=5) as r:
                net = json.load(r).get("data", {}).get("network") or {}
            port = net.get(f"{PHONE_PORT}/tcp")
        except Exception as e:
            log("Hinweis: Port-Info nicht lesbar:", e)
        try:
            with urllib.request.urlopen(urllib.request.Request("http://supervisor/network/info", headers=hdr), timeout=5) as r:
                ifs = json.load(r).get("data", {}).get("interfaces") or []
            ifs.sort(key=lambda i: not i.get("primary"))
            for i in ifs:
                addrs = (i.get("ipv4") or {}).get("address") or []
                if addrs:
                    ip = addrs[0].split("/")[0]; break
        except Exception as e:
            log("Hinweis: Netzwerk-Info nicht lesbar:", e)
    elif port is None:
        port = PHONE_PORT
    SUP_INFO.update(port=port, ip=ip)
    return SUP_INFO


def sources_payload():
    with SRC_LOCK:
        runners = list(RUNNERS.values())
    return [r.public() for r in runners]


# Nur Home Assistant (Ingress-Proxy) darf zugreifen; zum Testen mit LAERM_ALLOW_ALL=1 abschaltbar
ALLOWED = {"172.30.32.2", "127.0.0.1", "::1"}
RESTRICT = bool(os.environ.get("SUPERVISOR_TOKEN")) and not os.environ.get("LAERM_ALLOW_ALL")
MAX_BODY = 65536
UPLOAD_MAX = 30 * 1024 * 1024        # Datei zum Pruefen (Geraeusch pruefen)


class BaseHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "laerm/" + VERSION

    def log_message(self, *a):
        pass

    def send(self, code, ctype, body, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        if self.close_connection:
            self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def js(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()
        if len(body) > 4096 and "gzip" in (self.headers.get("Accept-Encoding") or ""):   # grosse Antworten (Verlauf) gepackt: schneller ueber Home Assistant
            return self.send(code, "application/json; charset=utf-8", gzip.compress(body, compresslevel=4), {"Content-Encoding": "gzip", "Vary": "Accept-Encoding"})
        self.send(code, "application/json; charset=utf-8", body)

    def route(self):
        p = self.path.split("?")[0].rstrip("/")
        name = p.rsplit("/", 1)[-1]
        q = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
        return p, name, q

    def read_body(self, limit=MAX_BODY):
        """Body immer vollstaendig lesen (sonst geraet Keep-Alive durcheinander). None = ungueltig."""
        try:
            n = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > limit:
            self.close_connection = True
            return None
        return self.rfile.read(n) if n else b""

    def send_file(self, path, ctype):
        size = os.path.getsize(path)
        start, end, code = 0, size - 1, 200
        rng = self.headers.get("Range", "")
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip()) if rng else None
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1)); end = min(size - 1, int(m.group(2))) if m.group(2) else size - 1
            else:
                start = max(0, size - int(m.group(2)))
            if start > end or start >= size:
                return self.send(416, "text/plain", b"", {"Content-Range": f"bytes */{size}"})
            code = 206
        length = end - start + 1
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD":
            return
        with open(path, "rb") as f:
            f.seek(start)
            left = length
            while left > 0:
                chunk = f.read(min(65536, left))
                if not chunk:
                    break
                self.wfile.write(chunk); left -= len(chunk)

    def fail(self, e):
        if isinstance(e, (BrokenPipeError, ConnectionResetError)):
            self.close_connection = True
            return
        self.close_connection = True
        try:
            self.send(500, "text/plain; charset=utf-8", str(e).encode())
        except Exception:
            pass

    def do_HEAD(self):
        self.do_GET()


STATIC = {"app.js", "app.css", "i18n.js", "qrcode.js", "druck.js", "uplot.min.js", "uplot.min.css", "handbuch.js", "hb_inhalt.js"}   # uPlot (MIT, github.com/leeoniya/uPlot): Kurven und Balken


class Handler(BaseHandler):
    def allowed(self):
        if not RESTRICT or self.client_address[0] in ALLOWED:
            return True
        self.close_connection = True
        self.send(403, "text/plain", b"forbidden")
        return False

    def do_GET(self):
        if not self.allowed():
            return
        p, name, q = self.route()
        try:
            _, clips, lg = paths()
            if "/clips/" in p + "/":                    # Laermspur, stummes Video; Ton nur, wenn fuer das Geraet eingeschaltet
                fn = os.path.basename(p)
                f = os.path.join(clips, fn)
                if fn and fn.endswith(SPUR_EXT) and os.path.isfile(f):
                    return self.send_file(f, "application/gzip")
                if fn and fn.endswith(VIRT_EXT):          # Stoerung ab 1.40: Messwerte aus der Tagesaufzeichnung als Laermspur
                    m_ = evmeta_all().get(fn[:-len(VIRT_EXT)])
                    if m_:
                        body_ = gzip.compress(json.dumps(virtual_graph(m_), separators=(",", ":")).encode(), compresslevel=6)
                        return self.send(200, "application/gzip", body_, {"Content-Disposition": f'attachment; filename="{fn[:-len(VIRT_EXT)]}.lsp"'})
                if fn and fn.endswith(".wav") and os.path.isfile(f) and wav_allowed(fn):
                    return self.send_file(f, "audio/wav")
                if fn and fn.endswith(".mp4"):
                    vf = video_path(fn)
                    if vf:
                        return self.send_file(vf, "video/mp4")
                return self.send(404, "text/plain", b"not found")
            if name == "event":
                return self.js(event_detail(q.get("k", [""])[0]))
            if name == "video_live":                   # aktuelles Bild einer Quelle (nur wenn sie Video sendet)
                with SRC_LOCK:
                    r = RUNNERS.get(q.get("src", ["main"])[0])
                jp = r.video.latest() if r is not None and r.video is not None and r.video.sending() else None
                if jp is None:
                    return self.send(404, "text/plain", b"no video")
                return self.send(200, "image/jpeg", jp, {"Cache-Control": "no-store"})
            if name == "art_status":
                return self.js(art_status())
            if name == "similar":                      # gelernten Namen in allen Ereignissen suchen
                return self.js(similar_search(clean_label_name((q.get("name") or [""])[0])))
            if name == "label_names":
                return self.js({"names": label_names(), "fine": classify.fine_meta("en" if CFG.get("language") == "en" else "de") if classify is not None else {}})
            if name == "classify_range":               # Bereich aus dem Live-Verlauf einordnen
                with SRC_LOCK:
                    r = RUNNERS.get(q.get("src", ["main"])[0])
                if r is None or classify is None or not classify.available():
                    return self.send(404, "text/plain", b"not found")
                try:
                    t0 = int(q["from"][0]); t1 = int(q["to"][0])
                    return self.js(dict(classify_range(r, t0, min(t1, t0 + 60000)), labels={k: v[0] for k, v in ART_LABEL.items()}))
                except (ValueError, IndexError, KeyError) as e:
                    return self.js({"ok": False, "error": str(e)}, 400)
            if name == "data":
                r = get_runner(q)
                since = int(q.get("since", ["-1"])[0]); before = int(q.get("before", ["0"])[0])
                limit = max(1, min(6000, int(q.get("limit", ["1200"])[0])))
                with r.rlock:
                    if before > 0:
                        recs = [x for x in r.recs if x[0] < before][-limit:]
                    elif since >= 0:
                        recs = [x for x in r.recs if x[0] > since][:limit]        # naechste, nicht neueste
                    else:
                        recs = list(r.recs)[-limit:]
                    first = r.recs[0][0] if r.recs else 0
                    last = r.recs[-1][0] if r.recs else 0
                return self.js({"now": int(time.time() * 1000), "first": first, "last": last, "boot": BOOT, "src": r.id,
                                "st": status_payload(r, full=since < 0), "r": recs})
            if name == "status":
                return self.js(status_payload(get_runner(q)))
            if name == "sources":
                info = phone_info()
                return self.js({"sources": sources_payload(), "former": former_sources(), "phone_port": info["port"], "lan_ip": info["ip"],
                                "tls": TLS_STATE["ok"], "tls_error": TLS_STATE["error"], "ffmpeg": bool(shutil.which("ffmpeg"))})
            if name == "phonelink":
                sid = (q.get("id") or [""])[0]
                with SRC_LOCK:
                    r = RUNNERS.get(sid)
                if not r or r.src["type"] != "phone":
                    return self.send(404, "text/plain", b"not found")
                info = phone_info()
                return self.js({"token": r.src["token"], "port": info["port"], "ip": info["ip"], "name": r.name})
            if name in ("night", "nights", "night.svg"):
                ds = (q.get("date") or [""])[0]
                try:
                    day = dt.date.fromisoformat(ds) if ds else (dt.date.today() - dt.timedelta(days=0 if dt.datetime.now().hour >= 12 else 1))
                    if not (2000 <= day.year <= 2200):
                        raise ValueError
                except (ValueError, OverflowError):
                    return self.send(400, "text/plain", b"bad date")
                src = re.sub(r"[^a-z0-9_]", "", (q.get("src") or ["all"])[0])[:16] or "all"
                if name == "nights":
                    return self.js({"nights": nights_overview(day, 7, src), "last": day.isoformat()})
                rg = range_param(q) or (None, None)
                pl_ = re.sub(r"[^a-z0-9_]", "", (q.get("list") or [""])[0])[:24]
                art_ = (q.get("art") or [""])[0][:64]
                if name == "night":
                    return self.js(night_data(day, src, rg[0], rg[1], pl_, art_))
                body = night_svg(day, src, rg[0], rg[1], pl_, art_).encode()
                return self.send(200, "image/svg+xml; charset=utf-8", body,
                                 {"Content-Disposition": f'attachment; filename="laerm_{day.isoformat()}_nacht.svg"'})
            if name == "events":
                try:
                    n = max(0, min(EVENTS_MAX, int((q.get("n") or ["200"])[0])))
                except ValueError:
                    n = 200
                return self.js(events_summary((q.get("src") or ["all"])[0], n, re.sub(r"[^a-z0-9_]", "", (q.get("list") or [""])[0])[:24],
                                              range_param(q), (q.get("art") or [""])[0][:64]))
            if name == "diag":
                return self.js({"text": diag_text(), "version": VERSION, "settings": public_settings()})
            if name == "settings":
                src, default = list_sources()
                return self.js({"settings": public_settings(), "sources": src, "default_source": default, "version": VERSION, "schedule": SCHED,
                                "src_details": source_details(), "pro": pro_state(),
                                "supervisor_available": bool(os.environ.get("SUPERVISOR_TOKEN"))})
            if name == "pro":
                return self.js(pro_state())
            if name == "plists":
                return self.js(plists_payload())
            if name == "trackdays":                    # Tage mit Tagesaufzeichnung (fuer „Alle Daten“ beim Drucken)
                ds_ = sorted({os.path.basename(f)[:10] for f in glob.glob(os.path.join(day_dir(), "*" + DAY_EXT))})
                return self.js({"ok": True, "days": [d_ for d_ in ds_ if re.match(r"^\d{4}-\d{2}-\d{2}$", d_)]})
            if name == "exceed":                       # Pruef-Schwelle im Verlauf: Spitzen ueber einem Wert (nur Anzeige)
                sid = re.sub(r"[^a-z0-9_]", "", (q.get("src") or ["main"])[0])[:16] or "main"
                try:
                    return self.js(exceed(sid, int(q["from"][0]), int(q["to"][0]), float(q["thr"][0])))
                except (KeyError, ValueError, IndexError):
                    return self.js({"ok": False, "error": "bad request"}, 400)
            if name == "daytrack":                     # ganzer Tag eines Geraets (Pegel je 125 ms)
                sid = re.sub(r"[^a-z0-9_]", "", (q.get("src") or ["main"])[0])[:16] or "main"
                ds = (q.get("date") or [dt.date.today().isoformat()])[0]
                gi = lambda k: int(q[k][0]) if q.get(k) and q[k][0].lstrip("-").isdigit() else None
                return self.js(day_track(sid, dt.date.fromisoformat(ds).isoformat(), gi("from"), gi("to"), gi("n") or 1200, (q.get("free") or ["0"])[0] == "1",
                                         spec=(q.get("nospec") or ["0"])[0] != "1"))
            if name == "spur":                         # Laermspur als JSON (Spektrogramm im zurueckgespulten Live-Bild)
                f_ = (q.get("f") or [""])[0]
                sub = "mit" if f_.startswith("mit/") else ""
                b_ = os.path.basename(f_)
                fp = os.path.join(paths()[1], sub, b_)
                if b_.endswith(VIRT_EXT) and not sub:
                    m_ = evmeta_all().get(b_[:-len(VIRT_EXT)])
                    if not m_:
                        return self.send(404, "text/plain", b"not found")
                    g_ = virtual_graph(m_)
                    return self.js({k: g_.get(k) for k in ("t0", "step", "bands", "recs", "src", "core")})
                if not b_.endswith(SPUR_EXT) or not os.path.isfile(fp):
                    return self.send(404, "text/plain", b"not found")
                g_ = load_graph(fp)
                return self.js({k: g_.get(k) for k in ("t0", "step", "bands", "recs", "src", "core")})
            if name == "cal_status":
                return self.js(cal_payload())
            if name == "backup_status":
                return self.js(dict(BK_STATE))
            if name == "backup.zip":                   # komplette Sicherung, wird beim Herunterladen erzeugt
                self.close_connection = True
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", 'attachment; filename="' + time.strftime("laerm_sicherung_%Y%m%d_%H%M.zip") + '"')
                self.send_header("Transfer-Encoding", "chunked")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if self.command == "HEAD":
                    return
                co = ChunkedOut(self.wfile); backup_write(co); co.close()
                return
            if name == "ha_rules":
                return self.js(ha_rules_payload())
            if name == "ha_entities":
                return self.js(ha_entities())
            if name == "fnote_target":                 # Notiz-Leiste: welcher Stoerung die Notiz jetzt zugeordnet wuerde
                try:
                    at_ = int(q["at"][0])
                except (KeyError, ValueError, IndexError):
                    at_ = int(time.time() * 1000)
                return self.js({"ok": True, "target": fnote_target(at_, re.sub(r"[^a-z0-9_]", "", (q.get("src") or ["all"])[0])[:16] or "all"),
                                "min": int(CFG.get("fn_assign_min", 5) or 0)})
            if name == "profiles":
                return self.js({"ok": True, "profiles": profile_names(), "teach": teach_status(), "scan": dict(SCAN)})
            if name == "teach_status":
                return self.js(teach_status())
            if name == "scan_status":
                return self.js(dict(SCAN))
            if name == "runtime":                      # Laufzeit (Start, Update, Unterbrechung) und Pruefsummen-Kette
                gi = lambda k: int(q[k][0]) if q.get(k) and q[k][0].lstrip("-").isdigit() else None
                return self.js(runtime_info(gi("from"), gi("to")))
            if name == "fnotes":                       # freie Notizen eines Zeitraums (ms) fuer das Live-Bild
                try:
                    a_, b_ = int(q["from"][0]), int(q["to"][0])
                except (KeyError, ValueError, IndexError):
                    now_ = int(time.time() * 1000); a_, b_ = now_ - 900000, now_ + 60000
                return self.js({"ok": True, "notes": fnotes_in(a_, b_, re.sub(r"[^a-z0-9_]", "", (q.get("src") or ["all"])[0])[:16] or "all")})
            if name == "notes":
                return self.js({"notes": notes_query(q), "tags": NOTE_TAGS})
            if name == "notes.csv":
                return self.send(200, "text/csv; charset=utf-8", notes_csv(q), {"Content-Disposition": 'attachment; filename="notizen.csv"'})
            if name == "protokoll.html":
                return self.send(200, "text/html; charset=utf-8", protocol_html(q))
            if name == "log.csv":
                if os.path.exists(lg):
                    return self.send_file(lg, "text/csv; charset=utf-8")
                return self.send(200, "text/csv; charset=utf-8", b"")
            if name in STATIC:
                f = os.path.join(WEB, name)
                ctype = mimetypes.guess_type(f)[0] or "application/octet-stream"
                return self.send(200, ctype + "; charset=utf-8", open(f, "rb").read())
            if name == "handbuch.html":                 # Handbuch (Wiki) mit Suche, Bilder unter hb/
                html = open(os.path.join(WEB, "handbuch.html"), "rb").read().replace(b"{{VERSION}}", VERSION.encode())
                return self.send(200, "text/html; charset=utf-8", html)
            if p.endswith("/hb/" + name) and re.fullmatch(r"[a-z0-9_]+\.png", name or ""):
                f = os.path.join(WEB, "hb", name)
                if os.path.isfile(f):
                    return self.send(200, "image/png", open(f, "rb").read(), {"Cache-Control": "max-age=86400"})
            if name == "druck.html":                    # Verlauf drucken (Notenblatt): Vorschau-Seite
                html = open(os.path.join(WEB, "druck.html"), "rb").read().replace(b"{{VERSION}}", VERSION.encode())
                return self.send(200, "text/html; charset=utf-8", html)
            if name not in ("", "index.html") and "." in name:
                return self.send(404, "text/plain", b"not found")
            html = open(os.path.join(WEB, "index.html"), "rb").read().replace(b"{{VERSION}}", VERSION.encode())
            self.send(200, "text/html; charset=utf-8", html)
        except (ValueError, KeyError) as e:
            self.send(400, "text/plain; charset=utf-8", str(e).encode())
        except Exception as e:
            self.fail(e)

    def restore_upload(self):
        """Sicherung hochladen: direkt in eine Datei schreiben (nicht in den Arbeitsspeicher), dann im Hintergrund einspielen."""
        try:
            n = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            n = -1
        self.close_connection = True                  # Body wird ggf. nicht gelesen
        if not self.allowed():
            return
        if n <= 0:
            return self.js({"ok": False, "error": "empty"}, 400)
        with BK_LOCK:
            if BK_STATE["state"] == "running":
                return self.js({"ok": False, "error": "busy"}, 409)
            BK_STATE.update(state="running", done=0, total=0, msg="", stats={}, restart=False)
        out = paths()[0]
        try:
            os.makedirs(out, exist_ok=True)
            free = shutil.disk_usage(out).free
            if free < 2 * n + 50 * 1024 * 1024:
                BK_STATE.update(state="idle")
                return self.js({"ok": False, "error": "space", "need_mb": round((2 * n) / 1048576), "free_mb": round(free / 1048576)}, 507)
            for old_ in glob.glob(os.path.join(out, ".import_*.zip")):   # liegengebliebene Uploads (nicht eingespielt) aufraeumen
                try:
                    if time.time() - os.path.getmtime(old_) > 7200 and old_ != BK_PENDING.get("path"):
                        os.remove(old_)
                except OSError:
                    pass
            tmp = os.path.join(out, ".import_" + secrets.token_hex(4) + ".zip")
            left = n
            with open(tmp, "wb") as f:
                while left > 0:
                    c = self.rfile.read(min(1 << 20, left))
                    if not c:
                        break
                    f.write(c); left -= len(c)
            if left:
                os.remove(tmp); BK_STATE.update(state="idle")
                return self.js({"ok": False, "error": "incomplete"}, 400)
            _, _, q = self.route()
            if (q.get("preview") or ["0"])[0] == "1":   # erst ansehen: welche Geraete bringt die Sicherung mit (Einspielen folgt mit restore_go)
                old_ = BK_PENDING.get("path")
                if old_ and old_ != tmp and os.path.exists(old_):
                    os.remove(old_)
                try:
                    pv = backup_preview(tmp)
                except Exception as e:
                    os.remove(tmp); BK_STATE.update(state="idle")
                    if isinstance(e, zipfile.BadZipFile):
                        e = ValueError("keine gültige ZIP-Datei" if CFG.get("language") != "en" else "not a valid ZIP file")
                    return self.js({"ok": False, "error": str(e)[:200]})
                BK_PENDING.update(path=tmp, at=time.time()); BK_STATE.update(state="idle")
                if isinstance(pv, dict):
                    pv["pro_needed"] = not pro_import_allowed(); pv["free_import"] = not pro_ok() and not pro_file().get("import_used")
                return self.js(pv)
            if not pro_import_allowed():
                os.remove(tmp); BK_STATE.update(state="idle")
                return self.js({"ok": False, "error": "pro"}, 402)
            pro_import_mark()
            threading.Thread(target=restore_run, args=(tmp, (q.get("settings") or ["0"])[0] == "1"), daemon=True).start()
            return self.js({"ok": True})
        except Exception as e:
            BK_STATE.update(state="error", msg=str(e)[:200])
            return self.fail(e)

    def do_POST(self):
        if self.path.split("?")[0].rstrip("/").endswith("/restore"):
            return self.restore_upload()
        big = self.path.split("?")[0].rstrip("/").endswith("/classify")
        body = self.read_body(UPLOAD_MAX if big else MAX_BODY)
        if not self.allowed():
            return
        if body is None:
            return self.send(413, "text/plain", b"bad length")
        p, name, q = self.route()
        try:
            if name == "classify":                    # hochgeladene Audiodatei einordnen
                if not body:
                    return self.js({"ok": False, "error": "empty"}, 400)
                try:
                    return self.js(dict(classify_upload(body), labels={k: v[0] for k, v in ART_LABEL.items()}))
                except ValueError as e:
                    return self.js({"ok": False, "error": str(e)}, 400)
            if name in ("label_add", "label_edit", "label_del", "label_reject"):
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(label_change(name[6:], data))
            if name in ("cal_start", "cal_apply", "cal_cancel"):   # Einpegeln der Geraete
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                if name == "cal_start":
                    return self.js(cal_start(data.get("secs"), data.get("ids") if isinstance(data.get("ids"), list) else None))
                if name == "cal_apply":
                    return self.js(cal_apply(bool(data.get("apply", True)), data.get("note") or ""))
                with CAL_LOCK:
                    CAL["state"] = "idle"
                return self.js({"ok": True})
            if name in ("plist_add", "plist_edit", "plist_del", "plist_mem"):   # Protokolllisten
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(plist_change(name[6:], data))
            if name in ("enote", "snote"):              # Notiz zum Gesamt- bzw. Einzelereignis
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(enote_change(name, data))
            if name == "reset":                         # Zuruecksetzen (Einstellungen -> Allgemein)
                data = json.loads(body or b"{}")
                if not isinstance(data, dict) or data.get("confirm") != "RESET" or not isinstance(data.get("parts"), list):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(reset_app(data["parts"]))
            if name == "restore_go":                     # hochgeladene Sicherung einspielen (Geraete-Auswahl aus der Vorschau)
                data = json.loads(body or b"{}")
                pth = BK_PENDING.get("path")
                if not isinstance(data, dict) or not pth or not os.path.exists(pth):
                    return self.js({"ok": False, "error": "nofile"}, 400)
                if data.get("cancel"):
                    os.remove(pth); BK_PENDING.update(path=None)
                    return self.js({"ok": True})
                if not pro_import_allowed():
                    return self.js({"ok": False, "error": "pro"}, 402)
                with BK_LOCK:
                    if BK_STATE["state"] == "running":
                        return self.js({"ok": False, "error": "busy"}, 409)
                    BK_STATE.update(state="running", done=0, total=0, msg="", stats={}, restart=False)
                pro_import_mark()
                cl = lambda v: {str(x) for x in v if re.fullmatch(r"[a-z0-9_]{1,16}", str(x))} if isinstance(v, list) else None
                BK_PENDING.update(path=None)
                threading.Thread(target=restore_run, args=(pth, bool(data.get("settings")), cl(data.get("pick")), cl(data.get("off")) or set()), daemon=True).start()
                return self.js({"ok": True})
            if name == "pro":                            # Lizenzschlüssel eintragen / entfernen
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(pro_del() if data.get("action") == "del" else pro_set(str(data.get("key") or "")[:2000]))
            if name == "run_note":                       # Kommentar zu einer Unterbrechung (z. B. Stromausfall)
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(run_note_set(data.get("key"), data.get("text")))
            if name == "mark":                           # Bereich im Verlauf / Live-Bild markiert und benannt
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(label_mark(data))
            if name in ("profile", "teach", "scan"):     # Profile verwalten, Profil aufnehmen, neu untersuchen
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                if name == "profile":
                    return self.js(profile_change(data))
                if name == "teach":
                    act = data.get("action")
                    if act == "start":
                        return self.js(teach_start(data.get("name"), data.get("ids") if isinstance(data.get("ids"), list) else None))
                    if act in ("finish", "cancel"):
                        return self.js(teach_finish(act == "finish", data.get("skip") if isinstance(data.get("skip"), list) else None))
                    if act == "stop":                       # Aufnahme beenden, Vorschau zeigen
                        with TEACH_LOCK:
                            if TEACH.get("state") in ("quiet", "armed"):
                                TEACH["state"] = "done"
                        return self.js(teach_status())
                    return self.js({"ok": False, "error": "bad action"}, 400)
                if data.get("action") == "cancel":
                    SCAN["cancel"] = True
                    return self.js({"ok": True})
                try:
                    f_, t_ = int(data.get("from")), int(data.get("to"))
                except (TypeError, ValueError):
                    return self.js({"ok": False, "error": "range"}, 400)
                return self.js(scan_start(f_, t_, clean_label_name(data.get("name")) if data.get("name") else "", data.get("events", True) is not False, data.get("areas", True) is not False))
            if name == "fnote":                         # freie Notiz (📝 Notiz jetzt)
                data = json.loads(body or b"{}")
                if not isinstance(data, dict) or data.get("action") not in ("add", "edit", "del"):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(fnote_change(data["action"], data))
            if name in ("note_add", "note_edit", "note_del"):
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(note_change(name[5:], data))
            if name == "classify_events":            # Ereignisse nachtraeglich (neu) einordnen lassen
                data = json.loads(body or b"{}")
                files = data.get("files") if isinstance(data, dict) else None
                if not isinstance(files, list):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                if classify is None or not classify.available():
                    return self.js({"ok": False, "error": "model missing"})
                if not art_enabled():
                    return self.js({"ok": False, "error": "off"})
                n = noemb = 0                          # neu bewerten geht nur aus gespeicherten Fingerabdruecken
                for f in files[:EVENTS_MAX]:
                    f = os.path.basename(str(f))
                    ki = ki_load(os.path.splitext(f)[0]) if f else None
                    if ki and ki.get("emb"):
                        art_enqueue(f, None, 0, {"rescore": True}); n += 1
                    else:
                        noemb += 1
                return self.js({"ok": True, "queued": n, "noemb": noemb})
            if name == "art_set":
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                return self.js(art_set_manual(str(data.get("k", "")), str(data.get("group", ""))))
            if name == "delete_events":
                data = json.loads(body or b"{}")
                n = delete_events(data.get("keys") if isinstance(data, dict) else None)
                return self.js({"ok": True, "deleted": n})
            if name == "ha_rules":
                data = json.loads(body or b"{}")
                if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                save_ha_rules(data["rules"])
                return self.js(dict(ha_rules_payload(), ok=True))
            if name == "schedule":
                data = json.loads(body or b"{}")
                if not isinstance(data, dict) or not isinstance(data.get("slots"), list):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                old = json.dumps(SCHED)
                if not pro_ok():                     # ohne Pro: Werte der Erkennung in Zeitprofilen unverändert lassen
                    prev = {str(x.get("id")): x.get("cfg") or {} for x in SCHED if isinstance(x, dict)}
                    for sl in data["slots"]:
                        if isinstance(sl, dict) and isinstance(sl.get("cfg"), dict):
                            keep = {k: v for k, v in prev.get(str(sl.get("id")), {}).items() if k in PRO_KEYS}
                            sl["cfg"] = dict(pro_strip(dict(sl["cfg"])), **keep)
                slots = save_sched(data["slots"])
                return self.js({"ok": True, "slots": slots, "changed": json.dumps(slots) != old})
            if name == "force":
                data = json.loads(body or b"{}")
                if not isinstance(data, dict) or not isinstance(data.get("on"), bool):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                sid = str(data.get("src") or "main")
                with SRC_LOCK:
                    known = sid in RUNNERS
                if not known:
                    return self.js({"ok": False, "error": "unknown source"}, 404)
                if data["on"]:
                    FORCE.add(sid)
                else:
                    FORCE.discard(sid)
                pub(f"{TOPIC}/force", "ON" if FORCE else "OFF", True)
                log("Erfassung ausserhalb der Erfassungszeit", "MANUELL AN" if data["on"] else "MANUELL AUS", f"({sid})")
                return self.js({"ok": True, "force": sid in FORCE})
            if name == "pause":
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                ok = pause_for(data.get("minutes", 0), "Oberfläche", data.get("reason", ""))
                return self.js({"ok": ok, "paused": RUN["paused"], "since": RUN["since"], "until": RUN["until"], "reason": RUN["reason"]})
            if name == "recording":
                data = json.loads(body or b"{}")
                if not isinstance(data, dict) or not isinstance(data.get("on"), bool):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                set_recording(data["on"], "Oberfläche")
                return self.js({"ok": True, "paused": RUN["paused"], "since": RUN["since"]})
            if name in ("settings", "sources"):
                data = json.loads(body or b"{}")
                if not isinstance(data, dict):
                    return self.js({"ok": False, "error": "bad request"}, 400)
                if name == "sources":
                    return self.js(update_sources(data))
                res = update_settings(data)
                res["settings"] = public_settings()
                return self.js(res)
            self.send(404, "text/plain", b"not found")
        except json.JSONDecodeError:
            self.js({"ok": False, "error": "invalid json"}, 400)
        except Exception as e:
            self.fail(e)


# =====================================================================
# HTTPS-Server fuer Handys (eigener Port, nur Handy-Seite und Audio-Empfang)
# =====================================================================
PHONE_PORT = int(os.environ.get("LAERM_PHONE_LISTEN", "8443"))
TLS_STATE = {"ok": False, "error": ""}
PHONE_MAX_BODY = REMOTE_RATE * 2 * 5          # hoechstens 5 s Audio pro Anfrage


def device_from_ua(ua):
    """Handy-Modell aus dem User-Agent, z. B. 'Android 14 · SM-G991B' oder 'iPhone'."""
    ua = ua or ""
    m = re.search(r"Android ([\d.]+)(?:; ([^;)]+))?", ua)
    if m:
        model = (m.group(2) or "").strip()
        if model in ("K", "wv") or re.fullmatch(r"[a-z]{2}[-_][a-z]{2}", model.lower()):   # verborgenes Modell oder Sprachkennung                      # Chrome verbirgt das Modell teilweise
            model = ""
        return ("Android " + m.group(1) + (" · " + model if model else ""))[:60]
    if "iPhone" in ua:
        return "iPhone"
    if "iPad" in ua:
        return "iPad"
    for k in ("Windows", "Macintosh", "Linux"):
        if k in ua:
            return k
    return ""


def runner_by_token(tok):
    if not re.fullmatch(r"[0-9a-f]{32}", tok or ""):
        return None
    with SRC_LOCK:
        for r in RUNNERS.values():
            t = r.src.get("token")
            if t and hmac.compare_digest(t, tok):
                return r
    return None


class PhoneHandler(BaseHandler):
    timeout = 10

    def do_GET(self):
        p, name, q = self.route()
        try:
            m = re.fullmatch(r"/m/([0-9a-f]{32})(/info)?", p)
            r = runner_by_token(m.group(1)) if m else None
            if not r:
                self.close_connection = True
                return self.send(404, "text/plain", b"not found")
            if m.group(2):
                return self.js({"name": r.name, "rate": REMOTE_RATE, "version": VERSION, "enabled": r.src.get("enabled", True),
                                "lang": CFG["language"]})
            html = open(os.path.join(WEB, "mic.html"), "rb").read().replace(b"{{VERSION}}", VERSION.encode())
            self.send(200, "text/html; charset=utf-8", html, {"Permissions-Policy": "microphone=(self), screen-wake-lock=(self)"})
        except Exception as e:
            self.fail(e)

    def do_POST(self):
        p, name, q = self.route()
        try:
            m = re.fullmatch(r"/m/([0-9a-f]{32})/push", p)
            r = runner_by_token(m.group(1)) if m else None
            if not r:                                  # ohne gueltigen Link: Body nicht lesen, Verbindung schliessen
                self.close_connection = True
                return self.send(404, "text/plain", b"not found")
            body = self.read_body(PHONE_MAX_BODY)
            if body is None:
                return self.send(413, "text/plain", b"too large")
            if len(body) % 2:
                body = body[:-1]

            def qi(k, d=None):
                try:
                    return int(q.get(k, [d])[0])
                except (TypeError, ValueError):
                    return d
            seq, first, age = qi("seq", 0), qi("first"), qi("age", 0)
            sess = (q.get("sid") or [""])[0][:32]
            enabled = src_runs(r.src)
            res = r.push.push(sess, first, seq, body, age) if enabled else "off"
            if res == "ok":
                info = device_from_ua(self.headers.get("User-Agent", ""))
                dev = re.sub(r"[^\w .,()+-]", "", (q.get("dev") or [""])[0])[:40].strip()      # Modell vom Handy selbst
                pv = re.sub(r"[^0-9.]", "", (q.get("pv") or [""])[0])[:10]
                if info.startswith("Android") or pv:
                    info = "Android " + (pv or info.split(" ")[1].split("·")[0].strip()) + (" · " + dev if dev else (" · " + info.split(" · ")[1] if " · " in info else ""))
                elif dev:
                    info = dev
                if info and info != r.src.get("device_info"):
                    r.src["device_info"] = info[:60]
                    threading.Thread(target=save_sources, daemon=True).start()
            st = r.status
            out = {"ok": res in ("ok", "dup", "off"), "result": res, "enabled": enabled, "level": st.get("level"),
                   "base": st.get("base"), "thr": st.get("thr"), "active": st.get("active"),
                   "learning": st.get("learning"), "name": r.name,
                   "paused": bool(RUN["paused"]), "until": RUN["until"], "reason": RUN["reason"],     # auch am Handy zeigen, wenn angehalten
                   "hold": (st.get("ha_hold") or {}).get("label") if st.get("ha_hold") else None}
            return self.js(out, 409 if res == "busy" else 200)
        except Exception as e:
            self.fail(e)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        pass       # abgebrochene Verbindungen und TLS-Fehler (Zertifikat abgelehnt) nicht protokollieren


class TLSServer(Server):
    """TLS-Handshake erst im Verbindungs-Thread, damit ein langsames Handy den Server nicht blockiert."""

    MAX_CONN = 32

    def __init__(self, addr, handler, ctx):
        super().__init__(addr, handler)
        self.ctx = ctx
        self.slots = threading.BoundedSemaphore(self.MAX_CONN)

    def get_request(self):
        sock, addr = self.socket.accept()
        sock.settimeout(10)
        return self.ctx.wrap_socket(sock, server_side=True, do_handshake_on_connect=False), addr

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):      # zu viele Verbindungen: sofort schliessen
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


def ensure_cert():
    d = os.path.join(DATA_DIR, "tls")
    crt, key = os.path.join(d, "cert.pem"), os.path.join(d, "key.pem")
    if os.path.exists(crt) and os.path.exists(key):
        return crt, key
    os.makedirs(d, exist_ok=True)
    code, out = run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "3650",
                     "-subj", "/CN=Laermprotokoll", "-keyout", key, "-out", crt], timeout=60)
    if code != 0:
        raise RuntimeError("Zertifikat konnte nicht erzeugt werden: " + out.strip()[:200])
    os.chmod(key, 0o600)
    log("Selbstsigniertes Zertifikat fuer Handys erzeugt")
    return crt, key


def start_phone_server():
    try:
        crt, key = ensure_cert()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(crt, key)
        srv = TLSServer(("0.0.0.0", PHONE_PORT), PhoneHandler, ctx)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        TLS_STATE.update(ok=True, error="")
        log(f"Handy-Server (HTTPS) laeuft auf Port {PHONE_PORT}")
    except Exception as e:
        TLS_STATE.update(ok=False, error=str(e))
        log("Handy-Server nicht gestartet:", e)


if __name__ == "__main__":
    CFG.update(load_settings())
    load_run()
    load_sched(); load_ha_rules()
    threading.Thread(target=lambda: Server(("0.0.0.0", int(os.environ.get("LAERM_PORT", "8099"))), Handler).serve_forever(), daemon=True).start()
    main()
