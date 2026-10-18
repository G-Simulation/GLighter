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

VERSION = "1.0.1"
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
        for k in ("own", "hide", "use", "words", "nope"):
            if not isinstance(QT["data"].get(k), dict):
                QT["data"][k] = {}
        return QT["data"]


def qt_save():
    with QT_LOCK:
        write_json(qt_path(), qt_all())
    mqtt_announce()


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
    o = qt_all()["own"].get(t)
    if isinstance(o, dict):
        return o.get("l") or t
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
        return {"ok": True, "tags": NOTE_TAGS, "own_max": own_max(), "pro": pro_ok(),
                "own": [{"k": k, "l": o.get("l") or k, "del": bool(o.get("del"))} for k, o in d["own"].items() if isinstance(o, dict)],
                "hide": sorted(k for k, v in d["hide"].items() if v and k in NOTE_TAG_SET),
                "use": {k: int(v or 0) for k, v in d["use"].items() if isinstance(v, (int, float))},
                "suggest": [{"w": e.get("w") or k, "k": k, "n": int(e.get("n") or 0)} for k, e in sug[:5]]}


def qt_change(data):
    """Schnellwahl verwalten: add (l), ren (k, l), del (k), undel (k), hide (k, on), nope (w)."""
    a = str(data.get("action") or "")
    with QT_LOCK:
        d = qt_all()
        k = str(data.get("k") or "")
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
    """Sichtbare Tasten in fester Reihenfolge (für die Auswahlliste in Home Assistant): [(Schlüssel, Beschriftung)]."""
    d = qt_all(); out = []
    for g in NOTE_TAGS.values():
        for t in g:
            if not d["hide"].get(t):
                out.append((t, tag_label(t)))
    for k, o in d["own"].items():
        if isinstance(o, dict) and not o.get("del"):
            out.append((k, o.get("l") or k))
    return out


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
    return {"ok": True, "n": n}


def export_csv():
    out = io.StringIO(); w = csv.writer(out, delimiter=";")
    w.writerow(["von", "bis", "schnellwahl", "text", "zeuge", "geschrieben", "kennung"])
    for p in sorted(notes_list(limit=5000), key=lambda p: p["a"]):
        w.writerow([p.get("from"), p.get("to"), ", ".join(p["tagl"]), p.get("text"), p.get("witness"), p.get("ts"), p.get("id")])
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
            "persons": persons(), "dir": DIR, "own_max": own_max()}


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
            return self.send(200, "text/csv; charset=utf-8", export_csv(), {"Content-Disposition": f'attachment; filename="greport_{dt.date.today()}.csv"'})
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
        if name == "import":
            return self.js(notes_import(d))
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
