"""Eigene Felder („Bausteine“) für die Notiz-Erfassung – gemeinsam für GReport und GLighter (gleiche Datei in beiden Apps).

Ein Baustein ist eine Definition {"id": "b_xxxxxx", "type": …, "l": Name, "h": Hilfetext, "req": Pflicht, "hide": ausgeblendet,
"del": gelöscht, "ts": angelegt, …Einstellungen der Art}. Werte stehen je Notiz in einem freiwilligen Feld
"fields": {Baustein-Kennung: Wert}. Notizen ohne "fields" bleiben gültig, gelöschte Bausteine bleiben als Definition
(„del“) erhalten, damit alte Werte lesbar und exportierbar bleiben. Pillen-Rubriken sind keine Bausteine hier:
sie bleiben die Rubriken der Schnellwahl (Werte in "tags").

Nur Standardbibliothek. Ändert nie Daten – prüft und formatiert nur.
"""
import datetime as dt
import re

TYPES = ("text", "counter", "number", "yesno", "select", "scale", "duration", "datetime", "place", "person")
BID = re.compile(r"^b_[0-9a-f]{6}$")
MAX_ACTIVE = 20                              # wie die eigenen Rubriken der Schnellwahl (20, frei und Pro)
MAX_ALL = 200                                # mit gelöschten
ROLES = ("mitbewohner", "nachbar", "hausverwaltung", "vermieter", "polizei", "sonstige")
ROLE_DE = {"mitbewohner": "Mitbewohner", "nachbar": "Nachbar", "hausverwaltung": "Hausverwaltung", "vermieter": "Vermieter", "polizei": "Polizei", "sonstige": "Sonstige"}
ROLE_EN = {"mitbewohner": "flatmate", "nachbar": "neighbour", "hausverwaltung": "property management", "vermieter": "landlord", "polizei": "police", "sonstige": "other"}
SEC_KEYS = ("txt", "tags", "wit", "more", "time")          # eingebaute Bereiche (GLighter ohne „more“)
TYPE_DE = {"text": "Textfeld", "counter": "Zähler", "number": "Zahl", "yesno": "Ja/Nein", "select": "Auswahlliste", "scale": "Skala",
           "duration": "Dauer", "datetime": "Datum/Uhrzeit", "place": "Ort", "person": "Person/Zeuge"}
TYPE_EN = {"text": "Text field", "counter": "Counter", "number": "Number", "yesno": "Yes/No", "select": "Choice list", "scale": "Scale",
           "duration": "Duration", "datetime": "Date/time", "place": "Place", "person": "Person/witness"}


def _txt(v, n):
    return re.sub(r"\s+", " ", re.sub(r"[\x00-\x1f<>]", "", str(v or ""))).strip()[:n]


def _num(v):
    if isinstance(v, bool) or v in (None, ""):
        return None
    try:
        f = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return int(f) if f == int(f) and abs(f) < 1e15 else round(f, 6)


def now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def clean_def(d, old=None):
    """Eine Definition prüfen. Unbekanntes fällt weg. Art und Kennung einer schon vorhandenen Definition ändern sich nie."""
    if not isinstance(d, dict):
        return None
    old = old if isinstance(old, dict) else {}
    bid = str(old.get("id") or d.get("id") or "")
    typ = old.get("type") or d.get("type")
    if not BID.match(bid) or typ not in TYPES:
        return None
    out = {"id": bid, "type": typ, "l": _txt(d.get("l"), 40) or old.get("l") or (TYPE_DE.get(typ) or typ),
           "ts": old.get("ts") or (str(d.get("ts"))[:30] if d.get("ts") else now_iso())}
    h = _txt(d.get("h"), 160)
    if h:
        out["h"] = h
    for k in ("req", "hide", "del"):
        if d.get(k) is True:
            out[k] = True
    c = str(d.get("col") or "")
    if re.fullmatch(r"#[0-9a-fA-F]{6}", c):
        out["col"] = c.lower()
    if typ in ("text", "place"):
        ph = _txt(d.get("ph"), 80)
        if ph:
            out["ph"] = ph
    if typ == "text":
        if d.get("ml") is True:
            out["ml"] = True
            try:
                r = int(d.get("rows") or 2)
            except (TypeError, ValueError):
                r = 2
            if r in (3, 4, 6, 8):
                out["rows"] = r
        elif d.get("sug") is True:                     # frühere Eingaben als Vorschläge (nur einzeilig)
            out["sug"] = True
        mx = _num(d.get("max"))
        if mx is not None and mx == int(mx) and 10 <= mx < 500:
            out["max"] = int(mx)
    elif typ == "datetime":                            # Art: Datum und Uhrzeit (Standard) / nur Datum / nur Uhrzeit; vorbelegt mit „jetzt“; Jetzt-Taste; Sekunden
        if d.get("kind") in ("date", "time"):
            out["kind"] = d["kind"]
        if d.get("def") == "now":
            out["def"] = "now"
        if d.get("nonow") is True:
            out["nonow"] = True
        if d.get("sec") is True and d.get("kind") != "date":
            out["sec"] = True
    elif typ == "counter":
        out["mode"] = "add" if d.get("mode") == "add" else "entry"
        if d.get("minus") is True:
            out["minus"] = True
    elif typ == "number":
        u = _txt(d.get("unit"), 12)
        if u:
            out["unit"] = u
        lo, hi = _num(d.get("min")), _num(d.get("max"))
        if lo is not None:
            out["min"] = lo
        if hi is not None and (lo is None or hi >= lo):
            out["max"] = hi
    elif typ == "select":
        opts = d.get("opts") if isinstance(d.get("opts"), list) else []
        out["opts"] = list(dict.fromkeys(x for x in (_txt(o, 40) for o in opts) if x))[:30]
        if d.get("multi") is True:
            out["multi"] = True
    elif typ == "scale":
        out["rng"] = "10" if str(d.get("rng")) == "10" else "5"
        for k in ("lo", "hi"):
            v = _txt(d.get(k), 24)
            if v:
                out[k] = v
    return out


def clean_defs(new, old=()):
    """Liste aus der Oberfläche übernehmen: vorhandene ändern, neue anhängen. Fehlt eine vorhandene in der Liste,
    bleibt sie unverändert – Definitionen gehen nie verloren. Höchstens MAX_ACTIVE nicht gelöschte."""
    old = [x for x in (old or []) if isinstance(x, dict) and BID.match(str(x.get("id") or ""))]
    by = {x["id"]: x for x in old}
    out, seen, errs = [], set(), []
    for d in (new if isinstance(new, list) else [])[:MAX_ALL]:
        if not isinstance(d, dict):
            continue
        bid = str(d.get("id") or "")
        if bid in seen:
            continue
        c = clean_def(d, by.get(bid))
        if c is None:
            errs.append(bid or "?"); continue
        seen.add(bid); out.append(c)
    out += [x for x in old if x["id"] not in seen]
    act = 0
    for x in out:                                       # zu viele aktive: die neuesten bleiben ausgeblendet/gelöscht
        if not x.get("del"):
            act += 1
            if act > MAX_ACTIVE:
                if x["id"] in by and not by[x["id"]].get("del"):
                    continue
                x["del"] = True; errs.append(x["id"] + ":limit")
    return out[:MAX_ALL], errs


def clean_sec(d, keys=SEC_KEYS):
    """Eingebaute Bereiche: {Bereich: {"l": Name, "h": Hilfe, "req": bool, "hide": bool}} (nur, was vom Standard abweicht)."""
    out = {}
    d = d if isinstance(d, dict) else {}
    for k in keys:
        v = d.get(k)
        if not isinstance(v, dict):
            continue
        e = {}
        l, h = _txt(v.get("l"), 40), _txt(v.get("h"), 160)
        if l:
            e["l"] = l
        if h:
            e["h"] = h
        for x in ("req", "hide"):
            if v.get(x) is True:
                e[x] = True
        if e:
            out[k] = e
    return out


def by_id(defs):
    return {x["id"]: x for x in defs or [] if isinstance(x, dict) and x.get("id")}


def active(defs):
    return [x for x in defs or [] if isinstance(x, dict) and not x.get("del")]


def clean_value(b, v):
    """Wert für Baustein b prüfen → (ok, Wert). ok=False: ungültig. Wert None: leer (wird nicht gespeichert)."""
    t = b.get("type")
    if v is None or v == "" or v == [] or v == {}:
        return True, None
    if t == "text":
        s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(v)).strip()[:int(b.get("max") or 500)]
        if not b.get("ml"):
            s = re.sub(r"\s*\n\s*", " ", s)
        return True, s or None
    if t in ("place",):
        s = _txt(v, 120)
        return True, s or None
    if t == "select":
        if isinstance(v, list):                       # Mehrfachauswahl
            vals = list(dict.fromkeys(x for x in (_txt(o, 60) for o in v) if x))[:30]
            return True, vals or None
        s = _txt(v, 60)
        return True, s or None
    if t == "yesno":
        if isinstance(v, bool):
            return True, v
        s = str(v).strip().lower()
        if s in ("ja", "yes", "true", "1", "j", "y"):
            return True, True
        if s in ("nein", "no", "false", "0", "n"):
            return True, False
        return False, None
    if t in ("counter", "number", "scale", "duration"):
        n = _num(v)
        if n is None:
            return False, None
        if t == "counter":
            return (True, int(n)) if n == int(n) and -1000 <= n <= 100000 else (False, None)
        if t == "scale":
            lo, hi = (0, 10) if b.get("rng") == "10" else (1, 5)
            return (True, int(n)) if n == int(n) and lo <= n <= hi else (False, None)
        if t == "duration":                            # Minuten
            return (True, int(n)) if n == int(n) and 0 <= n <= 100000 else (False, None)
        if b.get("min") is not None and n < b["min"] or b.get("max") is not None and n > b["max"]:
            return False, None
        return True, n
    if t == "datetime":
        s = str(v).strip()[:32]
        if b.get("kind") == "time" or re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", s):           # nur Uhrzeit: „HH:MM“ (oder mit Sekunden)
            m = re.fullmatch(r"(\d{2}):(\d{2})(?::(\d{2}))?", s)
            if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59 or (m.group(3) and int(m.group(3)) > 59):
                return False, None
            return True, s
        if b.get("kind") == "date" or re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):        # nur Datum: „JJJJ-MM-TT“
            try:
                return True, dt.date.fromisoformat(s[:10]).isoformat()
            except ValueError:
                return False, None
        try:
            d = dt.datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith(("Z", "z")) else s)
        except ValueError:
            return False, None
        if d.tzinfo is None:
            d = d.astimezone()
        return True, d.isoformat(timespec="seconds")
    if t == "person":
        if isinstance(v, str):
            v = {"n": v}
        if not isinstance(v, dict):
            return False, None
        n = _txt(v.get("n"), 80)
        if not n:
            return True, None
        out = {"n": n}
        r = str(v.get("r") or "")
        if r in ROLES:
            out["r"] = r
        c = _txt(v.get("c"), 120)
        if c:
            out["c"] = c
        return True, out
    return False, None


def clean_fields(defs, v):
    """Werte einer Notiz → (fields, Fehler). Unbekannte Bausteine fallen weg; gelöschte bleiben erlaubt (alte Werte beim Ändern)."""
    if not isinstance(v, dict):
        return {}, []
    b = by_id(defs)
    out, bad = {}, []
    for k, x in list(v.items())[:60]:
        if k not in b:
            continue
        ok, val = clean_value(b[k], x)
        if not ok:
            bad.append(k); continue
        if val is not None:
            out[k] = val
    return out, bad


def fmt_dur(m, de=True):
    m = int(m or 0)
    if m < 60:
        return f"{m} min"
    return f"{m // 60} h {m % 60:02d} min" if m % 60 else f"{m // 60} h"


def _numtxt(n, de=True):
    s = f"{n:g}" if isinstance(n, float) else str(n)
    return s.replace(".", ",") if de else s


def fmt(b, v, de=True, fmt_dt=None):
    """Wert lesbar (für Tagebuch, Bericht, Logbuch)."""
    t = b.get("type")
    if v is None:
        return ""
    if t == "counter":
        return (("+" if v > 0 else "−" if v < 0 else "") + str(abs(v))) if b.get("mode") != "add" else str(v)
    if t == "number":
        return _numtxt(v, de) + (" " + b["unit"] if b.get("unit") else "")
    if t == "yesno":
        return ("ja" if v else "nein") if de else ("yes" if v else "no")
    if t == "scale":
        return f"{v}/{10 if b.get('rng') == '10' else 5}"
    if t == "duration":
        return fmt_dur(v, de)
    if t == "datetime":
        if fmt_dt:
            try:
                return fmt_dt(dt.datetime.fromisoformat(v))
            except (ValueError, TypeError):
                return str(v)
        return str(v)
    if t == "person":
        if not isinstance(v, dict):
            return str(v)
        extra = [x for x in (((ROLE_DE if de else ROLE_EN).get(v.get("r"), "")), v.get("c", "")) if x]
        return v.get("n", "") + (" (" + ", ".join(extra) + ")" if extra else "")
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v)


def raw(b, v, de=True):
    """Wert für eine CSV-Spalte: Zahlen als Zahl, Ja/Nein als ja/nein, Datum ISO, Person „Name; Rolle; Kontakt“."""
    t = b.get("type")
    if v is None:
        return ""
    if t == "yesno":
        return ("ja" if v else "nein") if de else ("yes" if v else "no")
    if t in ("counter", "scale", "duration"):
        return str(v)
    if t == "number":
        return _numtxt(v, de)
    if t == "person":
        return "; ".join(x for x in (v.get("n", ""), (ROLE_DE if de else ROLE_EN).get(v.get("r"), ""), v.get("c", "")) if x) if isinstance(v, dict) else str(v)
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v)


def compact(defs, fields, de=True, fmt_dt=None):
    """[(Name, Wert)] in der Reihenfolge der Definitionen (auch gelöschte, damit alte Werte sichtbar bleiben)."""
    if not isinstance(fields, dict) or not fields:
        return []
    out = []
    for b in defs or []:
        if b.get("id") in fields:
            s = fmt(b, fields[b["id"]], de, fmt_dt)
            if s != "":
                out.append((b.get("l") or b["id"], s))
    return out


def compact_txt(defs, fields, de=True, fmt_dt=None, sep="; "):
    return sep.join(f"{l}: {v}" for l, v in compact(defs, fields, de, fmt_dt))


def csv_defs(defs, notes):
    """Bausteine, die eine eigene Spalte bekommen: alle nicht gelöschten und gelöschte mit Werten."""
    used = set()
    for p in notes or []:
        used |= set((p.get("fields") or {}).keys())
    return [b for b in defs or [] if not b.get("del") or b["id"] in used]


def csv_head(b, de=True):
    """Spaltenkopf mit Name und Kennung, z. B. „Gewicht [kg] (b_1a2b3c)“."""
    u = {"number": b.get("unit") or "", "duration": "min"}.get(b.get("type"), "")
    return f"{b.get('l') or b['id']}" + (f" [{u}]" if u else "") + f" ({b['id']})"


def csv_cells(cols, p, de=True):
    f = p.get("fields") or {}
    return [raw(b, f.get(b["id"]), de) for b in cols]


def head_id(h):
    """Spaltenkopf → Baustein-Kennung (für den Import)."""
    m = re.search(r"\((b_[0-9a-f]{6})\)\s*$", str(h or ""))
    return m.group(1) if m else None


def from_raw(b, s):
    """CSV-Zelle → Wert (Import). Ungültig: None."""
    s = str(s or "").strip()
    if not s:
        return None
    t = b.get("type")
    if t == "person":
        parts = [x.strip() for x in s.split(";")]
        r = next((k for k in ROLES if parts[1:2] and parts[1].lower() in (k, ROLE_DE[k].lower(), ROLE_EN[k].lower())), "")
        v = {"n": parts[0], "r": r, "c": parts[2] if len(parts) > 2 else ""}
    elif t == "select" and b.get("multi"):
        v = [x.strip() for x in s.split(",") if x.strip()]
    else:
        v = s
    ok, val = clean_value(b, v)
    return val if ok else None


def counter_sum(notes, bid, t0=None, t1=None):
    n = 0
    for p in notes or []:
        v = (p.get("fields") or {}).get(bid)
        a = p.get("a")
        if isinstance(v, (int, float)) and not isinstance(v, bool) and (t0 is None or (a is not None and a >= t0)) and (t1 is None or (a is not None and a < t1)):
            n += v
    return n


def daily(notes, bid, days=14, today=None):
    """Zähler je Tag (Summe der Werte), die letzten „days“ Tage bis heute: [[JJJJ-MM-TT, Summe], …]."""
    today = today or dt.date.today()
    d0 = today - dt.timedelta(days=days - 1)
    by = {}
    for p in notes or []:
        v = (p.get("fields") or {}).get(bid)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or p.get("a") is None:
            continue
        day = dt.date.fromtimestamp(p["a"] / 1000)
        if d0 <= day <= today:
            by[day] = by.get(day, 0) + v
    return [[(d0 + dt.timedelta(days=i)).isoformat(), by.get(d0 + dt.timedelta(days=i), 0)] for i in range(days)]


def suggestions(notes, bid, n=30):
    """Ort: frühere Eingaben als Vorschläge (neueste zuerst, ohne Doppelte)."""
    out = []
    for p in sorted(notes or [], key=lambda p: -(p.get("a") or 0)):
        v = (p.get("fields") or {}).get(bid)
        if isinstance(v, str) and v and v not in out:
            out.append(v)
            if len(out) >= n:
                break
    return out


def new_id(taken, tok):
    """Neue Kennung b_xxxxxx (tok = Funktion für 3 zufällige Bytes als Hex)."""
    while True:
        i = "b_" + tok()
        if i not in taken:
            return i
