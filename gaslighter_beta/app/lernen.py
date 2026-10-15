"""Lernen aus benannten Bereichen ("von hier bis hier war Teller klappern").

Alles arbeitet nur mit gespeicherten Messwerten, nie mit Ton:
- Band-Merkmal: Terz-Spektrum (Form), Pegelverlauf (Spitze ueber Hintergrund, Spitzigkeit, Dauer, Anstieg)
- KI-Fingerabdruck (optional): Mittel der YAMNet-Embeddings im Bereich

Ein Bereich wird mit allen Beispielen eines Namens verglichen; das aehnlichste Beispiel zaehlt (k-naechster Nachbar).
"""
import base64
import math

import numpy as np

TERZ = [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000]
TERZ_EXACT = [1000 * 10 ** (k / 10) for k in range(-13, 10)]
SUGGEST_MIN = 0.70        # ab dieser Aehnlichkeit wird ein Vorschlag angezeigt
MAX_SUGG = 6


def _edges_from_centers(c):
    c = np.asarray(c, float)
    if len(c) < 2:
        return np.array([c[0] / 1.12, c[0] * 1.12])
    mid = np.sqrt(c[:-1] * c[1:])
    lo = c[0] ** 2 / mid[0]
    hi = c[-1] ** 2 / mid[-1]
    return np.concatenate([[lo], mid, [hi]])


_W_CACHE = {}


def _to_terz_matrix(centers):
    key = tuple(int(x) for x in centers)
    if key in _W_CACHE:
        return _W_CACHE[key]
    if list(key) == TERZ[:len(key)] and len(key) == len(TERZ):
        W = None
    else:
        fe = _edges_from_centers(centers)
        te = [(c * 10 ** (-1 / 20), c * 10 ** (1 / 20)) for c in TERZ_EXACT]
        W = np.zeros((len(centers), len(TERZ)))
        for i in range(len(centers)):
            a, b = fe[i], fe[i + 1]
            for j, (c, d) in enumerate(te):
                ov = max(0.0, min(b, d) - max(a, c))
                if ov > 0:
                    W[i, j] = ov / (b - a)
    _W_CACHE[key] = W
    return W


def decode(g):
    """Grafikdaten eines Ereignisses -> (o_ms, Pegel, Hintergrund, aktiv, Terz-dB je Rahmen) als numpy."""
    R = g.get("recs") or []
    if not R:
        return None
    o = np.array([r[0] for r in R], float)
    lv = np.array([r[1] if r[1] is not None else -130 for r in R], float)
    bg = np.array([r[2] if r[2] is not None else np.nan for r in R], float)
    act = np.array([r[4] or 0 for r in R], float)
    nb = len(g.get("bands") or []) or 32
    sp = np.zeros((len(R), nb))
    for i, r in enumerate(R):
        raw = base64.b64decode(r[5] or "") if len(r) > 5 else b""
        if raw:
            v = np.frombuffer(raw, np.uint8)[:nb]
            sp[i, :len(v)] = v
    db = sp / 2.0 - 130.0
    W = _to_terz_matrix(g.get("bands") or [])
    if W is not None:
        p = 10 ** (db / 10) @ W
        db = 10 * np.log10(p + 1e-14)
    return {"o": o, "l": lv, "b": bg, "a": act, "t": db, "step": float(g.get("step") or 100)}


def band_feature(d, a, b):
    """Merkmalsvektor fuer den Bereich a..b (ms ab Beginn der Grafik)."""
    if d is None:
        return None
    o, st = d["o"], d["step"]
    m = (o > a) & (o - st < b)
    if m.sum() < 2:
        c = (a + b) / 2
        idx = np.argsort(np.abs(o - st / 2 - c))[:2]
        m = np.zeros(len(o), bool); m[idx] = True
    T = d["t"][m]; L = d["l"][m]
    P = 10 ** (T / 10)
    w = 10 ** (L / 10); w = w / (w.sum() + 1e-30)         # laute Rahmen praegen das Spektrum
    S = 10 * np.log10((P * w[:, None]).sum(axis=0) + 1e-14)
    shape = np.clip(S - S.max(), -40, 0) / 40.0
    base = np.nanmedian(d["b"]) if np.isfinite(d["b"]).any() else float(np.min(d["l"]))
    pk = float(L.max())
    over = float(np.clip((pk - base) / 40.0, 0, 1.5))
    crest = float(np.clip((pk - L.mean()) / 20.0, 0, 1.5))
    dur = math.log2(max(0.125, (b - a) / 1000.0)) / 4.0
    att = float(np.argmax(L)) / max(1, len(L) - 1)
    tilt = float(np.clip((S[-8:].mean() - S[:8].mean()) / 40.0, -1.5, 1.5))
    return np.concatenate([shape, 0.7 * np.array([over, crest, dur, att, tilt])])


def emb_feature(ki, a, b):
    """Mittel der KI-Fingerabdruecke, deren Fenster ueberwiegend in a..b liegen (normiert) - oder None."""
    if not ki or not ki.get("emb"):
        return None
    off, hop, pl = float(ki.get("off", 0)), float(ki.get("hop", 487.5)), float(ki.get("patch", 975))
    vs = []
    for i, (e, sc) in enumerate(zip(ki["emb"], ki.get("esc") or [])):
        s0 = off + i * hop; s1 = s0 + pl
        ov = min(s1, b) - max(s0, a)
        if ov >= 0.5 * min(pl, b - a):
            vs.append(np.frombuffer(base64.b64decode(e), np.uint8).astype(np.float32) * (sc / 255.0))
    if not vs:
        # Bereich kuerzer als ein Fenster: das Fenster mit der Mitte am naechsten
        c = (a + b) / 2
        n = len(ki["emb"])
        i = int(np.clip(round((c - off - pl / 2) / hop), 0, n - 1))
        s0 = off + i * hop
        if s0 > b + pl or s0 + pl < a - pl:
            return None
        vs = [np.frombuffer(base64.b64decode(ki["emb"][i]), np.uint8).astype(np.float32) * (ki["esc"][i] / 255.0)]
    v = np.mean(vs, axis=0)
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else None


def band_sim(f1, f2):
    d = float(np.linalg.norm(f1 - f2)) / math.sqrt(len(f1))
    return math.exp(-(d / 0.14) ** 2)


def emb_sim(e1, e2):
    c = float(np.dot(e1, e2))
    return float(np.clip((c - 0.55) / 0.40, 0, 1))


def score(proto, fb, fe):
    s_b = band_sim(proto["band"], fb) if (proto.get("band") is not None and fb is not None) else None
    s_e = emb_sim(proto["emb"], fe) if (proto.get("emb") is not None and fe is not None) else None
    if s_b is None and s_e is None:
        return 0.0
    if s_e is None:
        return s_b
    if s_b is None:
        return s_e
    return 0.6 * s_e + 0.4 * s_b


def proto_from(d, ki, a, b):
    return {"band": band_feature(d, a, b), "emb": emb_feature(ki, a, b), "dur": (b - a) / 1000.0}


def candidate_region(d):
    """Bereich mit Ereignis (Kern und Nachlauf) - dort wird gesucht."""
    act = np.where(d["a"] > 0)[0]
    if not len(act):
        return float(d["o"][0] - d["step"]), float(d["o"][-1])
    return float(d["o"][act[0]] - d["step"] - 500), float(d["o"][act[-1]] + 500)


def find(d, ki, protos_by_name, skip=()):
    """Vorschlaege fuer ein Ereignis: [[a, b, Name, Prozent], ...]. skip: (Name, a, b), die abgelehnt wurden."""
    if d is None or not protos_by_name:
        return []
    r0, r1 = candidate_region(d)
    r0 = max(r0, float(d["o"][0] - d["step"])); r1 = min(r1, float(d["o"][-1]))
    out = []
    for name, protos in protos_by_name.items():
        durs = [p["dur"] for p in protos if p.get("dur")]
        D = float(np.clip(np.median(durs) if durs else 1.0, 0.4, 12.0)) * 1000
        hits = []
        if r1 - r0 <= D:
            wins = [(r0, r1)]
        else:
            hop = max(125.0, D / 4)
            wins = [(x, x + D) for x in np.arange(r0, r1 - D + 1, hop)]
        for a, b in wins:
            fb = band_feature(d, a, b); fe = emb_feature(ki, a, b)
            s = max(score(p, fb, fe) for p in protos)
            if s >= SUGGEST_MIN:
                hits.append([a, b, s])
        hits.sort(key=lambda h: -h[2])
        kept = []
        for a, b, s in hits:
            if any(min(b, kb) - max(a, ka) > 0.3 * (b - a) for ka, kb, _ in kept):
                continue
            if any(n == name and min(b, sb) - max(a, sa) > 0.5 * (b - a) for n, sa, sb in skip):
                continue
            kept.append([a, b, s])
            if len(kept) >= 3:
                break
        out += [[int(a), int(b), name, int(round(100 * s))] for a, b, s in kept]
    out.sort(key=lambda h: -h[3])
    return out[:MAX_SUGG]


def best_in(d, ki, protos):
    """Bester Treffer eines Namens in einem Ereignis: (a, b, Prozent) oder None."""
    r = find(d, ki, {"x": protos})
    return (r[0][0], r[0][1], r[0][3]) if r else None
