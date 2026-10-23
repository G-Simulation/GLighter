"""Sensor-Bestätigung von Störungen (nur Anzeige, nur Standardbibliothek).

Für jede Störung (Beginn t0) wird jeder eingestellte Sensor in einem asymmetrischen Suchfenster [t0 − vor, t0 + nach] geprüft.
Es zählen nur steigende Flanken (Übergang auf „erkannt“). Ergebnis je Sensor:
  ok   bestätigt (Sensor mit Rolle „Bestätigung“ hat im Fenster neu ausgelöst)
  no   nicht bestätigt (erreichbar, nicht gesperrt, nicht schon aktiv – aber nichts gemeldet; kein Gegenbeweis)
  nb   nicht beurteilbar, mit Grund: offline, lock (Sperrzeit), active (war schon aktiv), nodata (noch keine Daten)
  own  vermutlich eigene Quelle (Sensor mit Rolle „eigene Aktivität“ hat im Fenster ausgelöst bzw. lief)
  free eigene-Aktivität-Sensor ohne Meldung
Zufallstreffer: p = 1 − exp(−λ · Fensterbreite), λ = Flanken je Sekunde in der erreichbaren Zeit der letzten Tage.
Ändert nie gespeicherte Störungen oder Aufzeichnungen – alles wird beim Lesen berechnet.
"""
import bisect
import math

TYPES = ("vib", "motion", "door", "cam", "phone_vib", "power", "tilt", "other")
ROLES = ("ok", "own", "ctx")                       # Bestätigung, eigene Aktivität (Ausschluss), nur Kontext
DEF = {"vib": {"pre": 5, "post": 10, "lock": 60, "role": "ok"},
       "motion": {"pre": 10, "post": 10, "lock": 60, "role": "own"},
       "door": {"pre": 5, "post": 5, "lock": 0, "role": "own"},
       "cam": {"pre": 5, "post": 30, "lock": 0, "role": "own"},
       "phone_vib": {"pre": 10, "post": 10, "lock": 0, "role": "ok"},
       "power": {"pre": 60, "post": 10, "lock": 0, "role": "own"},          # mindestens ein Meldeintervall vorher
       "tilt": {"pre": 5, "post": 5, "lock": 0, "role": "own"},
       "other": {"pre": 5, "post": 5, "lock": 0, "role": "ctx"}}
NEAR_S = 120                                        # knapp daneben: nächste Flanke bis 2 min außerhalb des Fensters
RATE_DAYS = 14
VERSION = 1                                         # Version der Regeln (steht im Export)


def guess_type(entity, name=""):
    """Art aus Entität und Name raten (nur Voreinstellung, änderbar)."""
    s = (str(entity or "") + " " + str(name or "")).lower()
    if any(w in s for w in ("vibrat", "erschuett", "erschütt", "shake")):
        return "vib"
    if any(w in s for w in ("motion", "bewegung", "occupan", "presence", "praesenz", "präsenz", "pir")):
        return "motion"
    if any(w in s for w in ("door", "tuer", "tür", "window", "fenster", "contact", "kontakt", "opening")):
        return "door"
    if any(w in s for w in ("power", "leistung", "watt", "energy", "strom", "steckdose", "plug")):
        return "power"
    if any(w in s for w in ("camera", "kamera", "cam")):
        return "cam"
    return "other"


def _num(v, lo, hi, d):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return d
    if not math.isfinite(f):
        return d
    return int(round(max(lo, min(hi, f))))


def clean_sensor(d, typ_default="other"):
    d = d if isinstance(d, dict) else {}
    typ = d.get("type") if d.get("type") in TYPES else typ_default
    df = DEF[typ]
    return {"type": typ, "pre": _num(d.get("pre"), 0, 600, df["pre"]), "post": _num(d.get("post"), 0, 600, df["post"]),
            "lock": _num(d.get("lock"), 0, 3600, df["lock"]), "role": d.get("role") if d.get("role") in ROLES else df["role"],
            "off": d.get("off") is True}


CLOCK_WARN_S = 5                                    # Uhrabgleich: Warnung ab so vielen Sekunden Abweichung (einstellbar 1–600)


def clean_cfg(d):
    """{"on": bool, "lanes": bool, "clock_warn": s, "sens": {Kennung: Einstellung}} – Einstellungen je Sensor nur, wenn gespeichert.
    lanes: Sensor-Spuren unter dem Pegelverlauf (ab 1.83), clock_warn: Uhrabgleich warnt ab so vielen Sekunden (ab 1.83)."""
    d = d if isinstance(d, dict) else {}
    out = {"on": d.get("on", True) is not False, "lanes": d.get("lanes", True) is not False,
           "clock_warn": _num(d.get("clock_warn"), 1, 600, CLOCK_WARN_S), "sens": {}}
    for k, v in (d.get("sens") if isinstance(d.get("sens"), dict) else {}).items():
        k = str(k)
        if len(k) <= 40 and all(c.isalnum() or c in "_-:" for c in k) and isinstance(v, dict):
            out["sens"][k] = clean_sensor(v, v.get("type") if v.get("type") in TYPES else "other")
        if len(out["sens"]) >= 64:
            break
    return out


def _overlap(a, b, lo, hi):
    return max(0, min(b, hi) - max(a, lo))


def base_rate(s, t_from, t_to):
    """Flanken je Sekunde über die erreichbare Zeit in [t_from, t_to] (ms). → (λ oder None, Tage Datenbasis, Anzahl)."""
    since = s.get("since")
    if since is None:
        return None, 0.0, 0
    lo = max(t_from, since)
    if t_to <= lo:
        return None, 0.0, 0
    reach = (t_to - lo) - sum(_overlap(a, b, lo, t_to) for a, b in s.get("offl") or [])
    if reach <= 0:
        return None, 0.0, 0
    n = sum(1 for e in s.get("edges") or [] if lo <= e < t_to)
    return n / (reach / 1000.0), reach / 86400000.0, n


def p_chance(lam, width_s):
    if lam is None:
        return None
    return 1.0 - math.exp(-lam * max(0.0, width_s))


def check(t0, src, s, lam=None):
    """Einen Sensor für eine Störung mit Beginn t0 (ms) am Gerät src prüfen. None = gilt für diese Störung nicht."""
    if s.get("off") or s.get("role") == "ctx":
        return None
    if s.get("only_dev") and s.get("dev") != src:
        return None
    pre, post = int(s.get("pre", 5)) * 1000, int(s.get("post", 5)) * 1000
    w0, w1 = t0 - pre, t0 + post
    r = {"id": s["id"], "name": s.get("name") or s["id"], "type": s.get("type"), "role": s.get("role"), "pre": s.get("pre"), "post": s.get("post"),
         "lock": s.get("lock", 0), "same": bool(s.get("dev") and s.get("dev") == src)}
    edges = s.get("edges") or []
    p = p_chance(lam, (pre + post) / 1000.0)
    if p is not None:
        r["p"] = round(p, 4)
    own = s.get("role") == "own"
    if s.get("since") is None or t0 < s["since"]:
        r.update(st="nb", why="nodata"); return r
    for a, b in s.get("offl") or []:
        if a < w1 and b > w0:
            r.update(st="nb", why="offline", off=[a, b]); return r
    i0, i1 = bisect.bisect_left(edges, w0), bisect.bisect_right(edges, w1)   # Flanken sind sortiert
    if i1 > i0:
        h = min(edges[i0:i1], key=lambda e: (abs(e - t0), e))
        r.update(st="own" if own else "ok", dt=round((h - t0) / 1000.0, 1))
        return r
    ons = s.get("on") or []
    j = bisect.bisect_left(s.get("_ona") or [a for a, _ in ons], w0) - 1   # letzte Zeit „an“, die vor dem Fenster begann
    act = tuple(ons[j]) if j >= 0 and ons[j][1] >= w0 else None
    if act and own and s.get("type") == "power":            # eigener Verbraucher lief schon: zählt als eigene Quelle
        r.update(st="own", why="running", dt=round((act[0] - t0) / 1000.0, 1)); return r
    lim = NEAR_S * 1000 + max(pre, post)
    near = [e for e in (edges[i0 - 1] if i0 > 0 else None, edges[i1] if i1 < len(edges) else None) if e is not None and abs(e - t0) <= lim]
    if near:
        r["near"] = round((min(near, key=lambda e: abs(e - t0)) - t0) / 1000.0, 1)
    if act:
        r.update(st="nb", why="active", since_s=round((t0 - act[0]) / 1000.0, 1)); return r
    lock = int(s.get("lock") or 0) * 1000
    last = edges[i0 - 1] if i0 > 0 else None
    if lock and last is not None and last + lock > t0:          # hat kurz vorher ausgelöst und konnte bauartbedingt nicht neu melden
        r.update(st="nb", why="lock", ago_s=round((t0 - last) / 1000.0, 1)); return r
    r["st"] = "free" if own else "no"
    return r


def combine(res):
    """Ergebnisse aller Sensoren einer Störung → {s: ok|no|nb|own|"", n: Treffer, m: prüfbare Bestätigungssensoren, p: Zufall (mind. ein Treffer)}."""
    res = [x for x in res if x]
    okr = [x for x in res if x["role"] == "ok"]
    chk = [x for x in okr if x["st"] in ("ok", "no")]
    hits = [x for x in okr if x["st"] == "ok"]
    own = [x for x in res if x["st"] == "own"]
    q = 1.0; known = True
    for x in chk:
        if x.get("p") is None:
            known = False
        else:
            q *= 1.0 - x["p"]
    out = {"n": len(hits), "m": len(chk), "t": len(okr)}
    if known and chk:
        out["p"] = round(1.0 - q, 4)
    if own:
        out["s"] = "own"; out["own"] = [[x["name"], x.get("dt")] for x in own]
    elif hits:
        out["s"] = "ok"
    elif okr and not chk:
        out["s"] = "nb"; out["nb"] = [[x["name"], x.get("why", "")] for x in okr]
    elif chk:
        out["s"] = "no"
    else:
        out["s"] = ""
    if hits:
        h = min(hits, key=lambda x: abs(x.get("dt") or 0))
        out["first"] = [h["name"], h.get("dt")]
    return out


def evaluate(events, sensors, now_ms, rate_days=RATE_DAYS):
    """events: [(Schlüssel, t0 ms, Gerät)], sensors: Liste wie oben. → ({Schlüssel: {sum, res}}, {Sensor: Grundrate})."""
    rates = {}
    for s in sensors:
        s["edges"] = sorted(s.get("edges") or []); s["on"] = sorted(s.get("on") or []); s["_ona"] = [a for a, _ in s["on"]]
        lam, days, n = base_rate(s, now_ms - rate_days * 86400000, now_ms)
        rates[s["id"]] = {"lam": lam, "days": round(days, 2), "n": n, "per_h": None if lam is None else round(lam * 3600, 2), "unsure": days < 3}
    out = {}
    for key, t0, src in events:
        res = [check(t0, src, s, rates[s["id"]]["lam"]) for s in sensors]
        res = [x for x in res if x]
        if res:
            out[key] = {"sum": combine(res), "res": res}
    return out, rates


def summary(sums):
    """Zusammenfassung über Störungen: Anzahl je Zustand, Bestätigungsquote nur über prüfbare, erwartete Zufallstreffer."""
    c = {"ok": 0, "no": 0, "nb": 0, "own": 0}
    exp, exp_known = 0.0, True
    for s in sums:
        st = s.get("s")
        if st in c:
            c[st] += 1
        if st in ("ok", "no"):
            if s.get("p") is None:
                exp_known = False
            else:
                exp += s["p"]
    chk = c["ok"] + c["no"]
    return dict(c, n=sum(c.values()), chk=chk, rate=round(c["ok"] / chk, 3) if chk else None, exp=round(exp, 1) if exp_known else None)


def assign_notes(notes, incs, pre_ms, post_ms):
    """Notizen den Störungen zuordnen (nach Ereigniszeit der Notiz): Zeitraum der Notiz [a, b] überschneidet
    [Störungsbeginn − Vorlauf, Störungsende + Nachlauf]; bei mehreren die mit dem kleinsten Abstand zum Störungsbeginn.
    notes: [(id, a, b, Gerät)], incs: [(Schlüssel, a, b, {Geräte})]. → {Notiz: (Schlüssel, Abstand ms = Notiz − Beginn, Zahl der Kandidaten)}"""
    out = {}
    for nid, a, b, src in notes:
        if a is None:
            continue
        b = max(b or a, a)
        cand = [(abs(a - ia), ia, k) for k, ia, ib, devs in incs
                if (src in (None, "", "all") or not devs or src in devs) and a <= ib + post_ms and b >= ia - pre_ms]
        if cand:
            cand.sort(key=lambda x: (x[0], x[1]))
            out[nid] = (cand[0][2], a - cand[0][1], len(cand))
    return out


def assign(notes, evs, ovr=None):
    """Notizen den Störungen zuordnen (ab 1.83), je Notiz mit eigenem Fenster (GLighter −2/+15 min, GReport −10/+30 min):
    Zeitraum der Notiz [a, b] überschneidet [Störungsbeginn − vor, Störungsende + nach]; die nächste zum Beginn gewinnt.
    Eine Wahl von Hand (ovr: {Notiz: Schlüssel oder None = gelöst}) geht vor; sie liegt in einer eigenen Datei, die Notiz bleibt unverändert.
    notes: [(id, a, b, Gerät, vor ms, nach ms)], evs: [(Schlüssel, a, b, Gerät)].
    → {Notiz: {"k": Schlüssel oder None, "d": Abstand ms (Notiz − Beginn) oder None, "man": von Hand?, "cand": [[Schlüssel, Abstand ms], …]}}
    Notizen ohne passende Störung und ohne Wahl von Hand fehlen. Notizen zählen nie als Sensor-Bestätigung."""
    ovr = ovr or {}
    evs = sorted((e for e in evs if e[1] is not None), key=lambda e: e[1])
    starts = [e[1] for e in evs]
    by_k = {e[0]: e for e in evs}
    maxd = max([max(0, (e[2] or e[1]) - e[1]) for e in evs] or [0])
    out = {}
    for nid, a, b, src, pre, post in notes:
        if a is None:
            continue
        b = max(b or a, a)
        i0 = bisect.bisect_left(starts, a - post - maxd); i1 = bisect.bisect_right(starts, b + pre)
        cand = []
        for k, ea, eb, dev in evs[i0:i1]:
            eb = max(eb or ea, ea)
            if (src in (None, "", "all") or not dev or dev == src) and a <= eb + post and b >= ea - pre:
                cand.append((abs(a - ea), ea, k))
        cand.sort(key=lambda x: (x[0], x[1]))
        cl = [[k, a - ea] for _, ea, k in cand]
        if nid in ovr:
            k = ovr[nid]
            if k is None:
                out[nid] = {"k": None, "d": None, "man": True, "cand": cl}; continue
            if k in by_k:
                out[nid] = {"k": k, "d": a - by_k[k][1], "man": True, "cand": cl}; continue
        if cl:
            out[nid] = {"k": cl[0][0], "d": cl[0][1], "man": False, "cand": cl}
    return out


def clock_eval(items, warn_s=CLOCK_WARN_S):
    """Uhrabgleich (ab 1.83, bewusst grob: ganze Sekunden, kein NTP). items: [{"kind": "ha"|"phone", "name", "off": s oder None}].
    → {"items": [... off auf ganze Sekunden], "max": größte Abweichung (s) oder None, "warn": über der Schwelle?, "warn_s"}."""
    out = []
    for x in items or []:
        o = x.get("off")
        out.append(dict(x, off=None if o is None or not math.isfinite(o) else int(round(o))))
    known = [abs(x["off"]) for x in out if x["off"] is not None]
    mx = max(known) if known else None
    return {"items": out, "max": mx, "warn": mx is not None and mx > warn_s, "warn_s": warn_s}


def clock_text(st, de=True):
    """„Uhrabgleich: Abweichung Home Assistant 0 s, Handy Küche 1 s“ (nur prüfbare Uhren; sonst Hinweis)."""
    if not st:
        return ""
    known = [x for x in st.get("items") or [] if x.get("off") is not None]
    if not known:
        return "Uhrabgleich: keine Vergleichsuhr verfügbar" if de else "Clock check: no reference clock available"
    parts = [f"{x['name']} {abs(x['off'])} s" for x in known]
    s = ("Uhrabgleich: Abweichung " if de else "Clock check: offset ") + ", ".join(parts)
    if st.get("warn"):
        s += (f" – mehr als {st['warn_s']} s, Zeitfenster der Sensoren mit Vorsicht lesen" if de
              else f" – more than {st['warn_s']} s, read the sensor time windows with care")
    return s
