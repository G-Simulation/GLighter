#!/usr/bin/env python3
"""GReport – Notizen zu Störungen festhalten (der Notiz-Teil von GLighter als eigene App).

- Notiz jetzt: Text, Schnellwahl (eigene Tasten, lernt mit), Zeuge, Zeitraum von–bis.
- Jede neue Notiz kommt ins Logbuch von Home Assistant.
- In Home Assistant: Auswahlliste „Schnellwahl“ und Knopf „Hinzufügen“ (über MQTT).
- Ist GLighter (Pro) installiert, liest es die Notizen aus /share/greport und zeigt sie mit an.
Nur Python-Standardbibliothek (MQTT über paho, wenn vorhanden).
"""
import csv
import datetime as dt
import fcntl
import glob
import hashlib
import http.server
import io
import json
import os
import re
import secrets
import socketserver
import sys
import threading
import time
import urllib.parse
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
sys.path.insert(0, HERE)
import lizenz  # noqa: E402

VERSION = "1.4.0"
BRAND = "GReport"
OPTIONS = os.environ.get("GR_OPTIONS", "/data/options.json")
PRIV = os.environ.get("GR_PRIVATE", "/data")                    # nur für GReport (Pro-Schlüssel)
PORT = int(os.environ.get("GR_PORT", "8099"))
ALLOWED = {"172.30.32.2", "127.0.0.1", "::1"}                   # nur über Home Assistant (Ingress)
RESTRICT = os.environ.get("GR_ALLOW_ALL") != "1"
HAID = TOPIC = "greport"


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def read_json(p, default=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":")); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)


OPT = {"language": "auto", "mqtt": True, "logbook": True, "output_dir": "/share/greport"}
OPT.update({k: v for k, v in (read_json(OPTIONS, {}) or {}).items() if k in OPT})
DIR = os.environ.get("GR_DIR") or OPT["output_dir"] or "/share/greport"
GL_DIR = os.environ.get("GR_GLIGHTER_DIR", "/share/gaslighter")


def lang():
    return "en" if OPT.get("language") == "en" else "de"


def now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def ms_of(iso):
    try:
        d = dt.datetime.fromisoformat(str(iso))
        if d.tzinfo is None:
            d = d.astimezone()
        return int(d.timestamp() * 1000)
    except (ValueError, TypeError):
        return None


def iso_of(ms):
    return dt.datetime.fromtimestamp(ms / 1000.0).astimezone().isoformat(timespec="seconds")


def clean_text(v, n=500):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(v or "")).strip()[:n]


# =====================================================================
# Pro (offline geprüfter Schlüssel; GReport- oder GLighter-Schlüssel)
# =====================================================================
def pro_file():
    return read_json(os.path.join(PRIV, "pro.json"), {}) or {}


PRO_CACHE = {"t": 0, "v": None}


def pro_info():
    if time.time() - PRO_CACHE["t"] > 60 or PRO_CACHE["v"] is None:
        k = pro_file().get("key") or ""
        PRO_CACHE.update(t=time.time(), v=lizenz.check(k))
    return dict(PRO_CACHE["v"], buy=lizenz.BUY_URL)


def pro_ok():
    return bool(pro_info().get("ok"))


def pro_set(key):
    r = lizenz.check(key)
    if r.get("ok") or r.get("state") == "expired":
        write_json(os.path.join(PRIV, "pro.json"), {"key": str(key).strip(), "at": now_iso()})
        PRO_CACHE["v"] = None
    return r


# =====================================================================
# Schnellwahl (wie in GLighter): eingebaute Tasten, eigene, ausgeblendete, Reihenfolge nach Gebrauch, gelernte Vorschläge
# =====================================================================
NOTE_TAGS = {
    "src": ["oben", "unten", "nebenan", "treppenhaus", "draussen", "unklar"],
    "kind": ["klopfen", "schritte", "musik", "stimmen", "tuer", "moebel", "bohren", "hund"],
    "lvl": ["leicht", "deutlich", "stark"],
    "eff": ["aufgewacht", "kind_geweckt", "kein_schlaf", "gestoert"],
    "act": ["geklingelt", "angesprochen", "verwaltung", "polizei"],
    "misc": ["zeuge", "serie"],
}
NOTE_TAG_SET = {t for v in NOTE_TAGS.values() for t in v}
TAG_DE = {"oben": "oben", "unten": "unten", "nebenan": "nebenan", "treppenhaus": "Treppenhaus", "draussen": "draußen", "unklar": "unklar",
          "klopfen": "Klopfen", "schritte": "Schritte", "musik": "Musik/Bass", "stimmen": "Stimmen", "tuer": "Tür", "moebel": "Möbelrücken",
          "bohren": "Bohren", "hund": "Hund", "leicht": "leicht", "deutlich": "deutlich", "stark": "stark", "aufgewacht": "aufgewacht",
          "kind_geweckt": "Kind geweckt", "kein_schlaf": "kein Einschlafen", "gestoert": "gestört", "geklingelt": "geklingelt",
          "angesprochen": "angesprochen", "verwaltung": "Hausverwaltung informiert", "polizei": "Polizei/Ordnungsamt", "zeuge": "Zeuge anwesend",
          "serie": "wiederholt"}
TAG_EN = {"oben": "above", "unten": "below", "nebenan": "next door", "treppenhaus": "stairwell", "draussen": "outside", "unklar": "unclear", "klopfen": "knocking", "schritte": "footsteps", "musik": "music/bass", "stimmen": "voices", "tuer": "door", "moebel": "moving furniture", "bohren": "drilling", "hund": "dog", "leicht": "slight", "deutlich": "clear", "stark": "strong", "aufgewacht": "woke up", "kind_geweckt": "child woken", "kein_schlaf": "could not sleep", "gestoert": "disturbed", "geklingelt": "rang the bell", "angesprochen": "talked to them", "verwaltung": "informed management", "polizei": "police/authority", "zeuge": "witness present", "serie": "repeated"}
QT_LOCK = threading.RLock()
QT = {"data": None}
QT_OWN_FREE, QT_OWN_MAX, QT_WORDS_MAX, QT_SUGGEST_N = 5, 40, 400, 3        # ohne Pro: 5 eigene Tasten
QT_STOP = set("""aber alle allem allen aller alles also auch auf aus bei beim bin bis bist dann darf das dass dem den denn der des dich die dies diese
diesem diesen dieser dir doch dort durch eine einem einen einer eines etwa euch eure fast fuer für gegen geht gibt habe haben hast hat hatte hatten heute
hier ihm ihn ihr ihre immer ist jede jedem jeden jeder jetzt kann kein keine konnte machen macht mal man mehr mein meine mich mir mit muss nach nicht
nichts noch nur oben oder ohne schon sehr sein seine seit sich sie sind soll sondern über um und uns unser unten vom von vor war waren warum was weil
weiter wenn wer werden wie wieder wir wird wo wurde zum zur zwei drei viel wohl ganz gerade gleich lang lange laut leise minuten stunde stunden uhr ca
morgens abends nachts mittags nacht abend morgen tag tage about after again also and any are because been before being both but can could did does
doing down during each few for from further had has have having her here hers him his how into its just more most not now off once only other our out
over own same she should some such than that the their them then there these they this those through too under until very was were what when where
which while who whom why will with would you your loud noise""".split())


def qt_path():
    return os.path.join(DIR, "schnellwahl.json")


def qt_all():
    with QT_LOCK:
        if QT["data"] is None:
            d = read_json(qt_path(), {})
            QT["data"] = d if isinstance(d, dict) else {}
        for k in ("own", "hide", "use", "words", "nope", "ren", "grp", "gcol", "req"):
            if not isinstance(QT["data"].get(k), dict):
                QT["data"][k] = {}
        if not isinstance(QT["data"].get("order"), list):
            QT["data"]["order"] = []
        if QT["data"].get("mode") not in ("use", "fixed"):
            QT["data"]["mode"] = "use"               # Reihenfolge: nach Gebrauch (häufigste zuerst) oder fest (selbst angeordnet)
        return QT["data"]


def qt_save():
    with QT_LOCK:
        write_json(qt_path(), qt_all())
    mqtt_announce()
    diary_soon()


def qt_clean_label(v):
    return re.sub(r"\s+", " ", re.sub(r"[\x00-\x1f<>]", "", str(v or ""))).strip()[:30]


def tag_ok(t):
    if not isinstance(t, str):
        return False
    if t in NOTE_TAG_SET:
        return True
    o = qt_all()["own"].get(t)
    return isinstance(o, dict) and not o.get("del")


def tag_label(t, lg=None):
    d = qt_all(); o = d["own"].get(t)
    if isinstance(o, dict):
        return o.get("l") or t
    if d["ren"].get(t):                                   # eingebautes Wort umbenannt
        return d["ren"][t]
    return (TAG_EN if (lg or lang()) == "en" else TAG_DE).get(t, t)


def clean_tags(v):
    return list(dict.fromkeys(t for t in v if tag_ok(t)))[:12] if isinstance(v, list) else []


def own_max():
    return QT_OWN_MAX if pro_ok() else QT_OWN_FREE


def qt_learn(tags, text):
    with QT_LOCK:
        d = qt_all()
        for t in tags or []:
            d["use"][t] = int(d["use"].get(t) or 0) + 1
        labels = {(o.get("l") or "").lower() for o in d["own"].values() if isinstance(o, dict) and not o.get("del")}
        labels |= {x.lower() for x in TAG_DE.values()} | {x.lower() for x in TAG_EN.values()}
        labels |= {str(x).lower() for x in d["ren"].values()}
        seen = set()
        for w in re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-]{3,23}", str(text or "")):
            lw = w.lower().strip("-")
            if len(lw) < 4 or lw in seen or lw in QT_STOP or lw in labels or lw in NOTE_TAG_SET or d["nope"].get(lw):
                continue
            seen.add(lw)
            e = d["words"].get(lw) if isinstance(d["words"].get(lw), dict) else {"n": 0, "w": w}
            e["n"] = int(e.get("n") or 0) + 1
            if w[:1].isupper():
                e["w"] = w
            d["words"][lw] = e
        if len(d["words"]) > QT_WORDS_MAX:
            for k in sorted(d["words"], key=lambda k: int(d["words"][k].get("n") or 0))[:len(d["words"]) - QT_WORDS_MAX]:
                d["words"].pop(k, None)
        write_json(qt_path(), d)


def qt_state():
    with QT_LOCK:
        d = qt_all()
        labels = {(o.get("l") or "").lower() for o in d["own"].values() if isinstance(o, dict) and not o.get("del")}
        sug = sorted(((k, e) for k, e in d["words"].items() if isinstance(e, dict) and int(e.get("n") or 0) >= QT_SUGGEST_N
                      and not d["nope"].get(k) and k not in labels), key=lambda x: -int(x[1].get("n") or 0))
        return {"ok": True, "tags": NOTE_TAGS, "own_max": own_max(), "pro": pro_ok(), "groups": GROUPS,
                "ren": {k: v for k, v in d["ren"].items() if k in NOTE_TAG_SET and v}, "grp": {k: v for k, v in d["grp"].items() if v in GROUPS},
                "order": [k for k in d["order"] if tag_known(k)], "mode": d["mode"],
                "gcol": {g: c for g, c in d["gcol"].items() if g in GROUPS and re.fullmatch(r"#[0-9a-fA-F]{6}", str(c))},
                "req": sorted(g for g, v in d["req"].items() if v and g in GROUPS),
                "own": [{"k": k, "l": o.get("l") or k, "del": bool(o.get("del"))} for k, o in d["own"].items() if isinstance(o, dict)],
                "hide": sorted(k for k, v in d["hide"].items() if v and k in NOTE_TAG_SET),
                "use": {k: int(v or 0) for k, v in d["use"].items() if isinstance(v, (int, float))},
                "suggest": [{"w": e.get("w") or k, "k": k, "n": int(e.get("n") or 0)} for k, e in sug[:5]]}


GROUPS = ["src", "kind", "lvl", "eff", "act", "misc", "own"]     # Woher, Was, Wie stark, Folgen, Maßnahmen, Sonstiges, Eigene


def tag_known(t):
    return isinstance(t, str) and (t in NOTE_TAG_SET or isinstance(qt_all()["own"].get(t), dict))


def qt_change(data):
    """Schnellwahl verwalten: add (l, g), ren (k, l – auch eingebaute), del (k), undel (k), hide (k, on), nope (w),
    grp (k, g), order (keys), mode (use|fixed), reset (eingebaute Wörter, Reihenfolge und Gruppen auf Standard)."""
    a = str(data.get("action") or "")
    with QT_LOCK:
        d = qt_all()
        k = str(data.get("k") or "")
        if a == "grp":
            if not tag_known(k) or data.get("g") not in GROUPS:
                return {"ok": False, "error": "not found"}
            dflt = next((g for g, v in NOTE_TAGS.items() if k in v), "own")
            if data["g"] == dflt:
                d["grp"].pop(k, None)
            else:
                d["grp"][k] = data["g"]
            qt_save()
            return qt_state()
        if a == "order":
            keys = [x for x in (data.get("keys") or []) if tag_known(x)] if isinstance(data.get("keys"), list) else None
            if keys is None:
                return {"ok": False, "error": "bad request"}
            d["order"] = list(dict.fromkeys(keys))[:200]; d["mode"] = "fixed"
            qt_save()
            return qt_state()
        if a == "req":                                        # Gruppe als „muss gewählt werden“ markieren (nur Hinweis, gespeichert wird immer)
            g = data.get("g")
            if g not in GROUPS:
                return {"ok": False, "error": "not found"}
            if data.get("on"):
                d["req"][g] = True
            else:
                d["req"].pop(g, None)
            qt_save()
            return qt_state()
        if a == "gcol":                                       # Farbe einer Gruppe (leer = Standardfarbe)
            g, c = data.get("g"), str(data.get("c") or "")
            if g not in GROUPS:
                return {"ok": False, "error": "not found"}
            if re.fullmatch(r"#[0-9a-fA-F]{6}", c):
                d["gcol"][g] = c.lower()
            else:
                d["gcol"].pop(g, None)
            qt_save()
            return qt_state()
        if a == "mode":
            d["mode"] = "fixed" if data.get("mode") == "fixed" else "use"
            qt_save()
            return qt_state()
        if a == "reset":
            d["ren"] = {}; d["grp"] = {k_: v for k_, v in d["grp"].items() if k_ not in NOTE_TAG_SET}; d["hide"] = {}; d["order"] = []; d["mode"] = "use"
            qt_save()
            return qt_state()
        if a == "ren" and k in NOTE_TAG_SET:                 # eingebautes Wort umbenennen (alte Notizen behalten den Schlüssel)
            l = qt_clean_label(data.get("l"))
            dflt = TAG_EN.get(k) if lang() == "en" else TAG_DE.get(k)
            if not l or l == dflt:
                d["ren"].pop(k, None)
            else:
                d["ren"][k] = l
            qt_save()
            return qt_state()
        if a == "add":
            l = qt_clean_label(data.get("l"))
            if not l:
                return {"ok": False, "error": "empty"}
            for k_, o in d["own"].items():
                if isinstance(o, dict) and (o.get("l") or "").lower() == l.lower():
                    o["del"] = False; o["l"] = l; break
            else:
                if sum(1 for o in d["own"].values() if isinstance(o, dict) and not o.get("del")) >= own_max():
                    return {"ok": False, "error": "limit" if pro_ok() else "limit_free"}
                k_ = "c_" + secrets.token_hex(3)
                d["own"][k_] = {"l": l, "ts": now_iso()}
                if data.get("g") in GROUPS and data.get("g") != "own":
                    d["grp"][k_] = data["g"]
                if d["mode"] == "fixed":
                    d["order"].append(k_)
            d["words"].pop(l.lower(), None)
            qt_save()
            return dict(qt_state(), k=k_)
        if a in ("ren", "del", "undel"):
            o = d["own"].get(k)
            if not isinstance(o, dict):
                return {"ok": False, "error": "not found"}
            if a == "ren":
                l = qt_clean_label(data.get("l"))
                if not l:
                    return {"ok": False, "error": "empty"}
                o["l"] = l
            else:
                o["del"] = a == "del"
            qt_save()
            return qt_state()
        if a == "hide":
            if k not in NOTE_TAG_SET:
                return {"ok": False, "error": "not found"}
            if data.get("on"):
                d["hide"][k] = True
            else:
                d["hide"].pop(k, None)
            qt_save()
            return qt_state()
        if a == "nope":
            w = str(data.get("w") or "").lower()[:24]
            if w:
                d["nope"][w] = True; d["words"].pop(w, None)
                qt_save()
            return qt_state()
    return {"ok": False, "error": "bad action"}


def qt_visible():
    """Sichtbare Tasten (für die Auswahlliste in Home Assistant): [(Schlüssel, Beschriftung)].
    Reihenfolge wie in der App: selbst angeordnet, sonst nach Gruppen."""
    d = qt_all(); keys = []
    for g in NOTE_TAGS.values():
        keys += [t for t in g if not d["hide"].get(t)]
    keys += [k for k, o in d["own"].items() if isinstance(o, dict) and not o.get("del")]
    if d["mode"] == "fixed" and d["order"]:
        pos = {k: i for i, k in enumerate(d["order"])}
        keys.sort(key=lambda k: pos.get(k, 10 ** 6))
    return [(k, tag_label(k)) for k in keys]


# =====================================================================
# Anzeige: Datum und Uhrzeit (gilt in der App und im Export)
# =====================================================================
PREF_DEF = {"date": "dmy4", "time": "hms", "rel": True, "wd": False}
DATE_FMTS = ("dmy4", "dmy2", "wdm", "iso", "long")
TIME_FMTS = ("hms", "hm", "h12")


def prefs():
    d = read_json(os.path.join(DIR, "einstellungen.json"), {}) or {}
    out = dict(PREF_DEF)
    if d.get("date") in DATE_FMTS:
        out["date"] = d["date"]
    if d.get("time") in TIME_FMTS:
        out["time"] = d["time"]
    for k in ("rel", "wd"):
        if isinstance(d.get(k), bool):
            out[k] = d[k]
    return out


def prefs_set(d):
    cur = prefs()
    if d.get("date") in DATE_FMTS:
        cur["date"] = d["date"]
    if d.get("time") in TIME_FMTS:
        cur["time"] = d["time"]
    for k in ("rel", "wd"):
        if isinstance(d.get(k), bool):
            cur[k] = d[k]
    allp = read_json(os.path.join(DIR, "einstellungen.json"), {}) or {}
    allp.update(cur)                                     # andere Einstellungen (z. B. Textdatei) bleiben
    write_json(os.path.join(DIR, "einstellungen.json"), allp)
    diary_soon()                                         # Tagebuch im neuen Datumsformat
    return dict(cur, ok=True)


MON_DE = ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sep.", "Okt.", "Nov.", "Dez."]
MON_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WD_DE = ["Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."]
WD_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def fmt_date(d, p=None):
    p = p or prefs(); en = lang() == "en"
    f = p["date"]
    if f == "dmy2":
        s = d.strftime("%d.%m.%y")
    elif f == "wdm":
        s = (WD_EN if en else WD_DE)[d.weekday()] + " " + d.strftime("%d.%m.")
    elif f == "iso":
        s = d.strftime("%Y-%m-%d")
    elif f == "long":
        s = f"{d.day}. {(MON_EN if en else MON_DE)[d.month - 1]} {d.year}" if not en else f"{d.day} {MON_EN[d.month - 1]} {d.year}"
    else:
        s = d.strftime("%d.%m.%Y")
    if p["wd"] and f != "wdm":
        s = (WD_EN if en else WD_DE)[d.weekday()] + " " + s
    return s


def fmt_time(d, p=None):
    p = p or prefs()
    if p["time"] == "hm":
        return d.strftime("%H:%M")
    if p["time"] == "h12":
        return (d.strftime("%I:%M:%S %p")).lstrip("0")
    return d.strftime("%H:%M:%S")


# =====================================================================
# Personen / Zeugen (Pro: Liste zum Antippen)
# =====================================================================
def persons():
    d = read_json(os.path.join(DIR, "personen.json"), {}) or {}
    return [p for p in d.get("list", []) if isinstance(p, str)][:50]


def persons_set(lst):
    if not pro_ok():
        return {"ok": False, "error": "pro"}
    clean = list(dict.fromkeys(clean_text(x, 80) for x in (lst if isinstance(lst, list) else []) if clean_text(x, 80)))[:50]
    write_json(os.path.join(DIR, "personen.json"), {"list": clean})
    return {"ok": True, "list": clean}


# =====================================================================
# Notizen (notizen.json: {"free": [...], "trash": [...]}) – gleiches Format wie die freien Notizen in GLighter
# =====================================================================
NOTES_LOCK = threading.RLock()
NOTES = {"data": None}
NOTES_MAX = 20000


def notes_path():
    return os.path.join(DIR, "notizen.json")


def notes_all():
    with NOTES_LOCK:
        if NOTES["data"] is None:
            d = read_json(notes_path(), {})
            NOTES["data"] = d if isinstance(d, dict) else {}
        for k in ("free", "trash"):
            if not isinstance(NOTES["data"].get(k), list):
                NOTES["data"][k] = []
        return NOTES["data"]


def notes_save():
    with NOTES_LOCK:
        write_json(notes_path(), notes_all())


def note_public(x):
    a = ms_of(x.get("from")); b = ms_of(x.get("to")) if x.get("to") else None
    return dict(x, a=a, b=b or a, tagl=[tag_label(t) for t in x.get("tags") or []])


def notes_list(t_from=None, t_to=None, q="", limit=500):
    q = str(q or "").strip().lower()[:80]
    with NOTES_LOCK:
        out = []
        for x in notes_all()["free"]:
            p = note_public(x)
            if p["a"] is None:
                continue
            if t_from is not None and p["b"] < t_from:
                continue
            if t_to is not None and p["a"] > t_to:
                continue
            if q and q not in (" ".join([p.get("text") or "", p.get("witness") or ""] + p["tagl"])).lower():
                continue
            out.append(p)
    out.sort(key=lambda p: -p["a"])
    return out[:max(1, min(5000, int(limit or 500)))]


def note_text(x):
    """Kurztext für Logbuch: „Klopfen, oben · Text · Zeuge Anna“."""
    parts = [", ".join(tag_label(t) for t in x.get("tags") or [] if t != "zeuge")]
    if x.get("text"):
        parts.append(x["text"])
    if x.get("witness"):
        parts.append(("Witness " if lang() == "en" else "Zeuge ") + x["witness"])
    return " · ".join(p for p in parts if p)[:250]


def note_change(action, data, by="app"):
    with NOTES_LOCK:
        a = notes_all(); lst = a["free"]
        nid = str(data.get("id") or "")
        if action == "del":
            idx = next((i for i, x in enumerate(lst) if x.get("id") == nid), None)
            if idx is None:
                return {"ok": False, "error": "not found"}
            a["trash"].append(dict(lst.pop(idx), deleted=now_iso()))
            notes_save()
            diary_soon()
            return {"ok": True}
        f = str(data.get("from") or "")[:25] or now_iso(); to = str(data.get("to") or "")[:25]
        fa, tb = ms_of(f), (ms_of(to) if to else None)
        if fa is None:
            return {"ok": False, "error": "from"}
        if to and (tb is None or tb < fa):
            return {"ok": False, "error": "to"}
        text = clean_text(data.get("text"))
        tags = clean_tags(data.get("tags"))
        if not text and not tags:
            return {"ok": False, "error": "empty"}
        wit = clean_text(data.get("witness"), 200)
        if not pro_ok():                                   # mehrere Zeugen: Pro
            wit = wit.split(",")[0].strip()[:80]
        src = re.sub(r"[^a-z0-9_]", "", str(data.get("src") or "all"))[:16] or "all"
        rec = {"from": iso_of(fa), "to": iso_of(tb) if tb else "", "src": src, "text": text, "tags": tags,
               "witness": wit if (wit and ("zeuge" in tags or wit)) else ""}
        if rec["witness"] and "zeuge" not in rec["tags"]:
            rec["tags"].append("zeuge")
        if action == "add":
            if len(lst) >= NOTES_MAX:
                return {"ok": False, "error": "limit"}
            x = dict(rec, id="r_" + secrets.token_hex(5), ts=now_iso(), at=now_iso(), by=by)
            lst.append(x)
            qt_learn(rec["tags"], text if data.get("typed") else "")
        else:
            x = next((y for y in lst if y.get("id") == nid), None)
            if x is None:
                return {"ok": False, "error": "not found"}
            x.update(rec, edited=now_iso())
        notes_save()
    if action == "add":
        logbook(x)
    diary_soon()
    return {"ok": True, "note": note_public(x)}


def notes_import(data):
    """Pro: Notizen aus einer Export-Datei (JSON) übernehmen; vorhandene (gleiche Kennung) bleiben."""
    if not pro_ok():
        return {"ok": False, "error": "pro"}
    lst = data.get("notes") if isinstance(data, dict) else None
    if not isinstance(lst, list):
        return {"ok": False, "error": "format"}
    n = 0
    with NOTES_LOCK:
        a = notes_all(); have = {x.get("id") for x in a["free"]}
        for x in lst[:NOTES_MAX]:
            if not isinstance(x, dict) or ms_of(x.get("from")) is None:
                continue
            nid = re.sub(r"[^a-z0-9_]", "", str(x.get("id") or ""))[:20] or "r_" + secrets.token_hex(5)
            if nid in have:
                continue
            rec = {"id": nid, "from": iso_of(ms_of(x["from"])), "to": iso_of(ms_of(x["to"])) if ms_of(x.get("to")) else "",
                   "src": re.sub(r"[^a-z0-9_]", "", str(x.get("src") or "all"))[:16] or "all", "text": clean_text(x.get("text")),
                   "tags": [t for t in (x.get("tags") or []) if isinstance(t, str) and (t in NOTE_TAG_SET or t.startswith("c_"))][:12],
                   "witness": clean_text(x.get("witness"), 200), "ts": str(x.get("ts") or now_iso())[:30], "by": "import"}
            if not rec["text"] and not rec["tags"]:
                continue
            a["free"].append(rec); have.add(nid); n += 1
        if n:
            notes_save()
    diary_soon()
    return {"ok": True, "n": n}


# =====================================================================
# Textdatei (Pro): Tagebuch nach Tagen, Export in eine Datei, Import aus TXT/CSV/JSON
# =====================================================================
TXT_ROOTS = [r for r in os.environ.get("GR_TXT_ROOTS", "/share:/media").split(":") if r]
TXT_DEF = {"on": False, "path": "", "monthly": False, "fmt": "txt"}
DIARY = {"lock": threading.Lock(), "timer": None, "last": None, "error": "", "files": []}


def txt_default_path(ext="txt"):
    return os.path.join(DIR, "greport_tagebuch." + ext)


def txt_cfg():
    d = (read_json(os.path.join(DIR, "einstellungen.json"), {}) or {}).get("txt") or {}
    out = dict(TXT_DEF)
    if isinstance(d, dict):
        out["on"] = d.get("on") is True
        out["monthly"] = d.get("monthly") is True
        out["fmt"] = "csv" if d.get("fmt") == "csv" else "txt"
        out["path"] = str(d.get("path") or "")[:300]
    return out


def safe_path(p, exts):
    """Nur Dateien unter /share oder /media (Home Assistant), mit passender Endung. Liefert den echten Pfad oder None."""
    p = str(p or "").strip()
    if not p or "\x00" in p:
        return None
    full = os.path.realpath(p if os.path.isabs(p) else os.path.join(DIR, p))
    if os.path.splitext(full)[1].lower() not in exts:
        return None
    for r in TXT_ROOTS:
        rr = os.path.realpath(r)
        if full == rr or full.startswith(rr + os.sep):
            return full
    return None


def txt_set(d):
    if not pro_ok():
        return {"ok": False, "error": "pro"}
    cur = txt_cfg()
    if isinstance(d.get("on"), bool):
        cur["on"] = d["on"]
    if isinstance(d.get("monthly"), bool):
        cur["monthly"] = d["monthly"]
    if d.get("fmt") in ("txt", "csv"):
        cur["fmt"] = d["fmt"]
    if "path" in d:
        path = str(d.get("path") or "").strip()
        if path and not safe_path(path, (".txt", ".csv", ".log")):
            return {"ok": False, "error": "path"}
        cur["path"] = path
    allp = read_json(os.path.join(DIR, "einstellungen.json"), {}) or {}
    allp["txt"] = cur
    write_json(os.path.join(DIR, "einstellungen.json"), allp)
    if cur["on"]:
        diary_write()
    return txt_state()


def txt_state():
    c = txt_cfg()
    return dict(c, ok=True, pro=pro_ok(), default=txt_default_path("csv" if c["fmt"] == "csv" else "txt"), roots=TXT_ROOTS,
                last=DIARY["last"], error=DIARY["error"], files=DIARY["files"][-6:])


def _line_txt(p, pf):
    a = dt.datetime.fromtimestamp(p["a"] / 1000).astimezone()
    s = fmt_time(a, pf)
    if p.get("to"):
        s += " – " + fmt_time(dt.datetime.fromtimestamp(p["b"] / 1000).astimezone(), pf)
    tags = [tag_label(t) for t in p.get("tags") or [] if not (t == "zeuge" and p.get("witness"))]
    s += "  "
    if tags:
        s += "[" + ", ".join(tags) + "] "
    if p.get("text"):
        s += p["text"].replace("\n", " / ")
    if p.get("witness"):
        s += (" – " if (tags or p.get("text")) else "") + ("Witness: " if lang() == "en" else "Zeuge: ") + p["witness"]
    if p.get("edited"):
        s += " (changed)" if lang() == "en" else " (geändert)"
    return s.rstrip()


def diary_render(notes, fmt, pf=None):
    """Tagebuch: je Tag eine Überschrift, darunter die Notizen nach Uhrzeit; zwischen den Tagen eine Leerzeile."""
    pf = pf or prefs()
    notes = sorted(notes, key=lambda p: p["a"])
    if fmt == "csv":
        out = io.StringIO(); w = csv.writer(out, delimiter=";")
        w.writerow(["datum", "uhrzeit", "bis", "schnellwahl", "text", "zeuge", "geaendert", "von_iso", "bis_iso", "kennung"])
        for p in notes:
            a = dt.datetime.fromtimestamp(p["a"] / 1000).astimezone(); b = dt.datetime.fromtimestamp(p["b"] / 1000).astimezone() if p.get("to") else None
            w.writerow([fmt_date(a, pf), fmt_time(a, pf), fmt_time(b, pf) if b else "", ", ".join(tag_label(t) for t in p.get("tags") or []),
                        p.get("text") or "", p.get("witness") or "", "ja" if p.get("edited") else "", p.get("from"), p.get("to") or "", p.get("id")])
        return "\ufeff" + out.getvalue()
    hp = dict(pf, wd=True)
    lines, day = [], None
    for p in notes:
        a = dt.datetime.fromtimestamp(p["a"] / 1000).astimezone()
        if a.date() != day:
            if day is not None:
                lines.append("")
            day = a.date(); lines.append(fmt_date(a, hp))
        lines.append(_line_txt(p, pf))
    return "\n".join(lines) + ("\n" if lines else "")


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def diary_write():
    """Tagebuch-Datei(en) neu schreiben (Pro, wenn eingeschaltet). Mit „je Monat“: name_JJJJ-MM.txt."""
    c = txt_cfg()
    if not (pro_ok() and c["on"]):
        return False
    path = safe_path(c["path"], (".txt", ".csv", ".log")) if c["path"] else txt_default_path("csv" if c["fmt"] == "csv" else "txt")
    if not path:
        DIARY["error"] = "path"; return False
    with DIARY["lock"]:
        try:
            notes = notes_list(limit=10 ** 6); pf = prefs(); files = []
            if c["monthly"]:
                base, ext = os.path.splitext(path); by = {}
                for p in notes:
                    by.setdefault(dt.datetime.fromtimestamp(p["a"] / 1000).astimezone().strftime("%Y-%m"), []).append(p)
                for m, ns in sorted(by.items()):
                    f = f"{base}_{m}{ext}"; _write_text(f, diary_render(ns, c["fmt"], pf)); files.append(f)
            else:
                _write_text(path, diary_render(notes, c["fmt"], pf)); files.append(path)
            DIARY.update(last=now_iso(), error="", files=files)
            return True
        except OSError as e:
            DIARY["error"] = str(e)[:160]; log("Textdatei:", e)
            return False


def diary_soon():
    """Nach einer Änderung kurz warten (mehrere Änderungen zusammen), dann die Datei schreiben."""
    c = txt_cfg()
    if not (c["on"] and pro_ok()):
        return
    t = DIARY.get("timer")
    if t:
        t.cancel()
    DIARY["timer"] = threading.Timer(1.0, diary_write); DIARY["timer"].daemon = True; DIARY["timer"].start()


def export_file(d):
    """Pro: alle Notizen in eine Datei auf dem Home-Assistant-Rechner schreiben (TXT-Tagebuch, CSV oder JSON)."""
    if not pro_ok():
        return {"ok": False, "error": "pro"}
    fmt = d.get("fmt") if d.get("fmt") in ("txt", "csv", "json") else "txt"
    path = safe_path(d.get("path") or os.path.join(DIR, f"greport_export_{dt.date.today()}.{fmt}"), ("." + fmt, ".log") if fmt == "txt" else ("." + fmt,))
    if not path:
        return {"ok": False, "error": "path"}
    _write_text(path, export_text(fmt))
    return {"ok": True, "path": path, "n": len(notes_all()["free"])}


def export_text(fmt):
    if fmt == "json":
        return json.dumps({"app": BRAND, "v": VERSION, "notes": notes_all()["free"]}, ensure_ascii=False, indent=1)
    return diary_render(notes_list(limit=10 ** 6), fmt)


# ---------- Import ----------
WD_ALL = set(x.lower().strip(".") for x in WD_DE + WD_EN) | {"montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag",
                                                         "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


def parse_date(s):
    """Datum in den Formaten von GReport (und üblichen): 18.10.2026, 18.10.26, 2026-10-18, 18. Okt. 2026, mit Wochentag davor."""
    s = str(s or "").strip().rstrip(":")
    s = re.sub(r"^([A-Za-zÄÖÜäöü]+)\.?,?\s+", lambda m: "" if m.group(1).lower() in WD_ALL else m.group(0), s)
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
    else:
        m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})?", s)
        if m:
            d, mo = int(m[1]), int(m[2]); y = int(m[3]) if m[3] else dt.date.today().year
            y = 2000 + y if y < 100 else y
        else:
            m = re.fullmatch(r"(\d{1,2})\.?\s+([A-Za-zäÄ]+)\.?\s+(\d{4})", s)
            if not m:
                return None
            mons = [x.lower().strip(".") for x in MON_DE]; mons_en = [x.lower() for x in MON_EN]; w = m[2].lower().strip(".")
            mo = next((i + 1 for i, x in enumerate(mons) if w.startswith(x[:3])), None) or next((i + 1 for i, x in enumerate(mons_en) if w.startswith(x[:3])), None)
            if not mo:
                return None
            d, y = int(m[1]), int(m[3])
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return None


def parse_time(s):
    m = re.match(r"\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp][Mm])?", str(s or ""))
    if not m:
        return None, None
    h, mi, se = int(m[1]), int(m[2]), int(m[3] or 0)
    if m[4]:
        h = h % 12 + (12 if m[4].lower() == "pm" else 0)
    if h > 23 or mi > 59 or se > 59:
        return None, None
    return dt.time(h, mi, se), m.end()


def _when(day, tm):
    return dt.datetime.combine(day, tm).astimezone().isoformat(timespec="seconds")


def parse_import(text):
    """TXT (Tagebuch), CSV (Export/Tagebuch) oder JSON → Liste roher Notizen {from, to, tags(labels|keys), text, witness, id}."""
    text = str(text or "").lstrip("\ufeff")
    st = text.lstrip()
    if st.startswith("{") or st.startswith("["):
        try:
            d = json.loads(text)
        except ValueError:
            return None, "format"
        lst = d.get("notes") if isinstance(d, dict) else d
        if not isinstance(lst, list):
            return None, "format"
        return [{"from": x.get("from"), "to": x.get("to") or "", "keys": x.get("tags") or [], "text": x.get("text") or "", "witness": x.get("witness") or "",
                 "id": x.get("id")} for x in lst if isinstance(x, dict)], None
    first = text.split("\n", 1)[0]
    if ";" in first and re.search(r"(datum|von_iso|schnellwahl)", first, re.I):
        out = []
        for r in csv.DictReader(io.StringIO(text), delimiter=";"):
            r = {str(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
            frm = r.get("von_iso")
            if not frm:
                day = parse_date(r.get("datum")); tm, _ = parse_time(r.get("uhrzeit") or r.get("von"))
                frm = _when(day, tm) if day and tm else ""
            to = r.get("bis_iso") or ""
            if not to and r.get("bis") and frm:
                tm, _ = parse_time(r["bis"]); to = _when(dt.datetime.fromisoformat(frm).date(), tm) if tm else ""
            out.append({"from": frm, "to": to, "labels": [x.strip() for x in (r.get("schnellwahl") or "").split(",") if x.strip()],
                        "text": r.get("text") or "", "witness": r.get("zeuge") or "", "id": r.get("kennung") or None})
        return out, None
    out, day = [], None
    wit_re = re.compile(r"\s*–\s*(?:Zeuge|Zeugin|Witness):\s*(.+?)\s*$")
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        tm, end = parse_time(line)
        if tm is None:
            d_ = parse_date(line)
            if d_:
                day = d_
            continue
        if day is None:
            continue
        rest = line[end:].strip(); to = ""
        m = re.match(r"[–-]\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*", rest)
        if m:
            t2, _ = parse_time(m[1]); to = _when(day, t2) if t2 else ""; rest = rest[m.end():]
        rest = re.sub(r"\s*\((?:geändert|changed)\)\s*$", "", rest)
        labels = []
        m = re.match(r"\[([^\]]*)\]\s*", rest)
        if m:
            labels = [x.strip() for x in m[1].split(",") if x.strip()]; rest = rest[m.end():]
        wit = ""
        m = wit_re.search(rest)
        if m:
            wit = m[1]; rest = rest[:m.start()]
        elif re.match(r"(?:Zeuge|Zeugin|Witness):\s*", rest):
            wit = re.sub(r"^(?:Zeuge|Zeugin|Witness):\s*", "", rest); rest = ""
        out.append({"from": _when(day, tm), "to": to, "labels": labels, "text": rest.replace(" / ", "\n").strip(), "witness": wit.strip(), "id": None})
    return out, None if out else "empty"


def _label_map():
    m = {}
    for g in NOTE_TAGS.values():
        for k in g:
            for l in (TAG_DE.get(k), TAG_EN.get(k), qt_all()["ren"].get(k), k):
                if l:
                    m[str(l).lower()] = k
    for k, o in qt_all()["own"].items():
        if isinstance(o, dict) and not o.get("del"):
            m[(o.get("l") or k).lower()] = k
    return m


def import_plan(text):
    """Vorschau/Übernahme: welche Notizen neu sind, welche schon da (gleiche Kennung oder gleiche Zeit, gleicher Text, gleiche Wörter)."""
    rows, err = parse_import(text)
    if err:
        return None, err
    lm = _label_map()
    with NOTES_LOCK:
        have_id = {x.get("id") for x in notes_all()["free"]}
        have_key = {(ms_of(x.get("from")), (x.get("text") or "").strip(), tuple(sorted(x.get("tags") or []))) for x in notes_all()["free"]}
    plan = {"new": [], "dup": 0, "bad": 0, "words": []}
    words = {}
    for r in rows:
        a = ms_of(r.get("from"))
        if a is None:
            plan["bad"] += 1; continue
        keys = [k for k in (r.get("keys") or []) if isinstance(k, str) and (k in NOTE_TAG_SET or k.startswith("c_"))]
        for l in r.get("labels") or []:
            k = lm.get(l.lower())
            if k:
                keys.append(k)
            else:
                words.setdefault(l.lower(), l); keys.append("?" + l)
        text = clean_text(r.get("text")); wit = clean_text(r.get("witness"), 200)
        if wit:
            keys.append("zeuge")
        keys = list(dict.fromkeys(keys))
        if not text and not keys:
            plan["bad"] += 1; continue
        nid = re.sub(r"[^a-z0-9_]", "", str(r.get("id") or ""))[:20]
        if (nid and nid in have_id) or (a, text, tuple(sorted(k for k in keys if not k.startswith("?")))) in have_key:
            plan["dup"] += 1; continue
        b = ms_of(r.get("to")) if r.get("to") else None
        plan["new"].append({"id": nid, "from": iso_of(a), "to": iso_of(b) if b and b >= a else "", "keys": keys, "text": text, "witness": wit})
    plan["words"] = sorted(words.values(), key=str.lower)
    return plan, None


def import_text(d, apply=False):
    if not pro_ok():
        return {"ok": False, "error": "pro"}
    if d.get("path"):
        p = safe_path(d["path"], (".txt", ".csv", ".json", ".log"))
        if not p or not os.path.isfile(p):
            return {"ok": False, "error": "path"}
        if os.path.getsize(p) > 20 * 1024 * 1024:
            return {"ok": False, "error": "too big"}
        with open(p, encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        text = str(d.get("content") or "")
    plan, err = import_plan(text)
    if err:
        return {"ok": False, "error": err}
    res = {"ok": True, "new": len(plan["new"]), "dup": plan["dup"], "bad": plan["bad"], "words": plan["words"][:30],
           "sample": [{"from": x["from"], "text": x["text"][:80]} for x in plan["new"][:5]]}
    if not apply:
        return res
    made = {}
    for w in plan["words"]:                            # unbekannte Wörter als eigene anlegen (so weit erlaubt)
        r = qt_change({"action": "add", "l": w})
        if r.get("ok") and r.get("k"):
            made[w.lower()] = r["k"]
    n = 0
    with NOTES_LOCK:
        a = notes_all(); have = {x.get("id") for x in a["free"]}
        for x in plan["new"][:NOTES_MAX - len(a["free"])]:
            keys, extra = [], []
            for k in x["keys"]:
                if k.startswith("?"):
                    kk = made.get(k[1:].lower())
                    (keys.append(kk) if kk else extra.append(k[1:]))
                else:
                    keys.append(k)
            text = x["text"] if not extra else ((", ".join(extra) + (" – " if x["text"] else "")) + x["text"])
            nid = x["id"] if x["id"] and x["id"] not in have else "r_" + secrets.token_hex(5)
            a["free"].append({"id": nid, "from": x["from"], "to": x["to"], "src": "all", "text": text, "tags": list(dict.fromkeys(keys))[:12],
                              "witness": x["witness"], "ts": now_iso(), "by": "import"})
            have.add(nid); n += 1
        if n:
            notes_save()
    diary_soon()
    return dict(res, applied=n, words_made=len(made))


def export_csv():
    """Tabelle: Datum und Uhrzeit wie in der Anzeige eingestellt, dazu die genaue Zeit (ISO) für den Abgleich."""
    out = io.StringIO(); w = csv.writer(out, delimiter=";"); pf = prefs()
    w.writerow(["datum", "von", "bis", "schnellwahl", "text", "zeuge", "von_iso", "bis_iso", "geschrieben", "kennung"])
    for p in sorted(notes_list(limit=5000), key=lambda p: p["a"]):
        a = dt.datetime.fromtimestamp(p["a"] / 1000).astimezone(); b = dt.datetime.fromtimestamp(p["b"] / 1000).astimezone() if p.get("to") else None
        w.writerow([fmt_date(a, pf), fmt_time(a, pf), fmt_time(b, pf) if b else "", ", ".join(p["tagl"]), p.get("text"), p.get("witness"),
                    p.get("from"), p.get("to"), p.get("ts"), p.get("id")])
    return ("﻿" + out.getvalue()).encode("utf-8")


def backup_zip():
    """Sicherung (immer frei): alle Dateien im Datenordner außer früheren Sicherungen."""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("notizen.json", "schnellwahl.json", "personen.json"):
            p = os.path.join(DIR, f)
            if os.path.exists(p):
                z.write(p, f)
        z.writestr("info.json", json.dumps({"app": BRAND, "version": VERSION, "at": now_iso()}, ensure_ascii=False))
    return bio.getvalue()


def daily_backup():
    """Pro: einmal am Tag eine Sicherung nach /share/greport/sicherung (die letzten 14 bleiben)."""
    if not pro_ok():
        return
    d = os.path.join(DIR, "sicherung"); day = dt.date.today().isoformat(); p = os.path.join(d, f"greport_{day}.zip")
    if os.path.exists(p):
        return
    os.makedirs(d, exist_ok=True)
    with open(p + ".tmp", "wb") as f:
        f.write(backup_zip())
    os.replace(p + ".tmp", p)
    for old in sorted(glob.glob(os.path.join(d, "greport_*.zip")))[:-14]:
        try:
            os.remove(old)
        except OSError:
            pass
    log("Tägliche Sicherung:", p)


# =====================================================================
# Home Assistant: Logbuch und Entitäten (MQTT)
# =====================================================================
def ha_api():
    url = os.environ.get("GR_HA_URL") or ("http://supervisor/core/api" if os.environ.get("SUPERVISOR_TOKEN") else "")
    return url.rstrip("/"), os.environ.get("GR_HA_TOKEN") or os.environ.get("SUPERVISOR_TOKEN") or ""


HA = {"ok": None, "error": "", "logged": 0}


def logbook(x):
    if not OPT.get("logbook", True):
        return
    url, tok = ha_api()
    if not url:
        return
    body = {"name": BRAND, "message": note_text(x) or "Notiz", "domain": "greport"}
    if MQ["ok"]:
        body["entity_id"] = "button.greport_hinzufuegen"

    def go():
        try:
            req = urllib.request.Request(url + "/services/logbook/log", data=json.dumps(body).encode(), method="POST",
                                         headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8):
                pass
            HA.update(ok=True, error=""); HA["logged"] += 1
        except Exception as e:
            HA.update(ok=False, error=str(e)[:120]); log("Logbuch:", e)
    threading.Thread(target=go, daemon=True).start()


MQ = {"c": None, "ok": False, "sel": None}


def pub(topic, payload, retain=False):
    c = MQ["c"]
    if c is not None:
        try:
            c.publish(topic, payload, retain=retain)
        except Exception:
            pass


def mqtt_announce(client=None, *_):
    c = client if hasattr(client, "subscribe") else MQ["c"]
    if c is None:
        return
    de = lang() == "de"
    dev = {"identifiers": [HAID], "name": BRAND, "manufacturer": "G-Simulation", "model": "GReport", "sw_version": VERSION}
    opts = [l for _, l in qt_visible()] or ["–"]
    opts = list(dict.fromkeys(opts))
    if MQ["sel"] not in opts:
        MQ["sel"] = opts[0]
    pub(f"{TOPIC}/status", "online", True)
    pub(f"homeassistant/select/{HAID}/schnellwahl/config", json.dumps({
        "name": "Schnellwahl" if de else "Quick select", "unique_id": f"{HAID}_schnellwahl", "object_id": f"{HAID}_schnellwahl",
        "command_topic": f"{TOPIC}/schnellwahl/set", "state_topic": f"{TOPIC}/schnellwahl", "options": opts, "icon": "mdi:format-list-bulleted",
        "availability_topic": f"{TOPIC}/status", "device": dev}, ensure_ascii=False), True)
    pub(f"homeassistant/button/{HAID}/hinzufuegen/config", json.dumps({
        "name": "Hinzufügen" if de else "Add", "unique_id": f"{HAID}_hinzufuegen", "object_id": f"{HAID}_hinzufuegen",
        "command_topic": f"{TOPIC}/hinzufuegen/set", "payload_press": "PRESS", "icon": "mdi:note-plus",
        "availability_topic": f"{TOPIC}/status", "device": dev}, ensure_ascii=False), True)
    pub(f"{TOPIC}/schnellwahl", MQ["sel"], True)
    if hasattr(c, "subscribe") and client is not None:
        c.subscribe([(f"{TOPIC}/schnellwahl/set", 0), (f"{TOPIC}/hinzufuegen/set", 0)])
        MQ["ok"] = True


def mqtt_cmd(topic, raw):
    """Befehl aus Home Assistant: Auswahl merken bzw. Notiz mit der gewählten Taste anlegen."""
    if topic.endswith("/schnellwahl/set"):
        if raw in [l for _, l in qt_visible()]:
            MQ["sel"] = raw; pub(f"{TOPIC}/schnellwahl", raw, True)
        return None
    if topic.endswith("/hinzufuegen/set"):
        key = next((k for k, l in qt_visible() if l == MQ["sel"]), None)
        if not key:
            return None
        r = note_change("add", {"tags": [key], "from": now_iso()}, by="homeassistant")
        log("Notiz aus Home Assistant:", MQ["sel"], "ok" if r.get("ok") else r.get("error"))
        return r
    return None


def mqtt_start():
    host = os.environ.get("MQTT_HOST")
    if not host or not OPT.get("mqtt", True):
        return
    try:
        import paho.mqtt.client as mqtt
        try:
            c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=HAID)
        except AttributeError:
            c = mqtt.Client(client_id=HAID)
        c.username_pw_set(os.environ.get("MQTT_USER"), os.environ.get("MQTT_PASS"))
        c.will_set(f"{TOPIC}/status", "offline", retain=True)
        c.on_connect = mqtt_announce
        c.on_message = lambda _c, _u, m: mqtt_cmd(m.topic, m.payload.decode(errors="ignore").strip())
        MQ["c"] = c
        c.connect_async(host, int(os.environ.get("MQTT_PORT", "1883")))
        c.loop_start()
        log("MQTT aktiv:", host)
    except Exception as e:
        log("MQTT nicht verfügbar:", e)


# =====================================================================
# GLighter: erkennen (Pro-Verbindung liest GLighter selbst aus /share/greport)
# =====================================================================
def glighter():
    """Liest, was GLighter (Pro) über sich in /share/greport/glighter.json schreibt: Geräte und ob verbunden."""
    g = read_json(os.path.join(DIR, "glighter.json"), {}) or {}
    fresh = bool(g) and time.time() - float(g.get("t") or 0) < 300
    return {"found": fresh or os.path.isdir(GL_DIR), "linked": fresh and bool(g.get("pro")),
            "sources": g.get("sources") if fresh and isinstance(g.get("sources"), list) else [], "v": g.get("v")}


def heartbeat():
    write_json(os.path.join(DIR, "greport.json"), {"app": BRAND, "v": VERSION, "t": time.time(), "notes": "notizen.json", "tags": "schnellwahl.json"})


def bg_loop():
    while True:
        try:
            heartbeat(); daily_backup()
        except Exception as e:
            log("Hintergrund:", e)
        time.sleep(60)


# =====================================================================
# Datenordner sperren (nie zwei GReport gleichzeitig)
# =====================================================================
LOCK_FH = None


def lock_dir():
    global LOCK_FH
    os.makedirs(DIR, exist_ok=True)
    LOCK_FH = open(os.path.join(DIR, ".lock"), "w")
    try:
        fcntl.flock(LOCK_FH, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


# =====================================================================
# Webserver (nur über Ingress)
# =====================================================================
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".png": "image/png", ".svg": "image/svg+xml", ".json": "application/json"}


def state():
    return {"ok": True, "version": VERSION, "lang": OPT.get("language", "auto"), "pro": pro_info(), "glighter": glighter(),
            "ha": {"api": bool(ha_api()[0]), "ok": HA["ok"], "error": HA["error"]}, "mqtt": bool(MQ["ok"]),
            "persons": persons(), "dir": DIR, "own_max": own_max(), "prefs": prefs()}


def client_ip(a):
    """Der Server lauscht auf IPv6 und IPv4: Home Assistant (Ingress) kommt dann als „::ffff:172.30.32.2“ an."""
    a = str(a or "")
    return a[7:] if a.startswith("::ffff:") else a


class H(http.server.BaseHTTPRequestHandler):
    server_version = "GReport"

    def log_message(self, *a):
        pass

    def allowed(self):
        if not RESTRICT or client_ip(self.client_address[0]) in ALLOWED:
            return True
        self.send(403, "text/plain", b"forbidden")
        return False

    def send(self, code, ctype, body, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def js(self, obj, code=200):
        self.send(code, "application/json", json.dumps(obj, ensure_ascii=False).encode())

    def route(self):
        u = urllib.parse.urlparse(self.path)
        return u.path.rstrip("/").split("/")[-1] if u.path not in ("", "/") else "", urllib.parse.parse_qs(u.query)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 20 * 1024 * 1024:
            raise ValueError("too big")
        try:
            d = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            d = {}
        return d if isinstance(d, dict) else {}

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self.allowed():
            return
        name, q = self.route()
        g = lambda k, d="": (q.get(k) or [d])[0]
        if name in ("", "index.html"):
            html = open(os.path.join(WEB, "index.html"), encoding="utf-8").read().replace("{{VERSION}}", VERSION)
            return self.send(200, TYPES[".html"], html.encode())
        ext = os.path.splitext(name)[1]
        if ext in TYPES and re.fullmatch(r"[a-z0-9_.\-]+", name) and os.path.isfile(os.path.join(WEB, name)):
            return self.send(200, TYPES[ext], open(os.path.join(WEB, name), "rb").read())
        if name == "state":
            return self.js(state())
        if name == "notetags":
            return self.js(qt_state())
        if name == "notes":
            ia = lambda k: int(g(k)) if re.fullmatch(r"-?\d+", g(k)) else None
            return self.js({"ok": True, "notes": notes_list(ia("from"), ia("to"), g("q"), ia("limit") or 500)})
        if name == "backup":
            return self.send(200, "application/zip", backup_zip(), {"Content-Disposition": f'attachment; filename="greport_{dt.date.today()}.zip"'})
        if name == "export":
            if not pro_ok():
                return self.js({"ok": False, "error": "pro"}, 403)
            if g("fmt") == "json":
                return self.send(200, "application/json", json.dumps({"app": BRAND, "v": VERSION, "notes": notes_all()["free"]}, ensure_ascii=False).encode(),
                                 {"Content-Disposition": f'attachment; filename="greport_{dt.date.today()}.json"'})
            if g("fmt") == "txt":
                return self.send(200, "text/plain; charset=utf-8", export_text("txt").encode("utf-8"), {"Content-Disposition": f'attachment; filename="greport_{dt.date.today()}.txt"'})
            return self.send(200, "text/csv; charset=utf-8", export_csv(), {"Content-Disposition": f'attachment; filename="greport_{dt.date.today()}.csv"'})
        if name == "textfile":
            return self.js(txt_state())
        if name == "pro":
            return self.js(pro_info())
        return self.send(404, "text/plain", b"not found")

    def do_POST(self):
        if not self.allowed():
            return
        name, q = self.route()
        try:
            d = self.body()
        except ValueError:
            return self.js({"ok": False, "error": "too big"}, 413)
        if name == "note":
            a = d.get("action") if d.get("action") in ("add", "edit", "del") else "add"
            return self.js(note_change(a, d))
        if name == "notetags":
            return self.js(qt_change(d))
        if name == "persons":
            return self.js(persons_set(d.get("list")))
        if name == "prefs":
            return self.js(prefs_set(d))
        if name == "import":
            if "content" in d or "path" in d:                 # Textdatei: Vorschau (preview) oder übernehmen
                return self.js(import_text(d, apply=d.get("apply") is True))
            return self.js(notes_import(d))
        if name == "textfile":
            if d.get("action") == "write":
                ok = diary_write()
                return self.js(dict(txt_state(), ok=ok, error=None if ok else (DIARY["error"] or ("pro" if not pro_ok() else "off"))))
            return self.js(txt_set(d))
        if name == "export_file":
            return self.js(export_file(d))
        if name == "pro":
            if d.get("action") == "del":
                try:
                    os.remove(os.path.join(PRIV, "pro.json"))
                except OSError:
                    pass
                PRO_CACHE["v"] = None
                return self.js({"ok": True, "pro": pro_info()})
            r = pro_set(d.get("key"))
            return self.js({"ok": bool(r.get("ok")), "error": r.get("error") or r.get("state"), "pro": pro_info()})
        return self.js({"ok": False, "error": "not found"}, 404)


class Srv(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    address_family = __import__("socket").AF_INET6


def main():
    if not lock_dir():
        log("Datenordner wird schon von einem anderen GReport benutzt:", DIR)
        sys.exit(1)
    log(f"{BRAND} {VERSION} – Daten in {DIR}")
    notes_all(); qt_all()
    mqtt_start()
    threading.Thread(target=bg_loop, daemon=True).start()
    try:
        srv = Srv(("::", PORT), H)
    except OSError:
        Srv.address_family = __import__("socket").AF_INET
        srv = Srv(("0.0.0.0", PORT), H)
    srv.serve_forever()


if __name__ == "__main__":
    main()
