"""GasLighter – Lizenzschlüssel prüfen (offline).

Ein Schlüssel sieht so aus:  GL1-XXXXX-XXXXX-…   (Base32, Bindestriche und Leerzeichen egal)
Inhalt: 1 Byte Version, 2 Byte Länge, JSON {"p":"gaslighter","e":"JJJJ-MM-TT","n":"Bestellnr.","k":"Kundenkennung","i":"Ausgabedatum"}
        + 64 Byte Ed25519-Signatur über Version+Länge+JSON.
Geprüft wird nur mit dem öffentlichen Schlüssel unten; der private Schlüssel liegt nie in der App.
Ed25519 nach RFC 8032 in reinem Python (nur Prüfen; einmal je Start bzw. Eingabe, Laufzeit ~10 ms).
"""
import base64, datetime, hashlib, json

PRODUCT = "gaslighter"
# öffentlicher Schlüssel (32 Byte, hex) – passt zum privaten Schlüssel auf dem Server von G-Simulation
PUBLIC_KEY_HEX = "e59303bd55fed27e39801ac948a5ae2168ae1f1e3a0dda74e71318e97e047488"
BUY_URL = "https://www.gsimulations.de/gaslighter/#buypro"

# ---------- Ed25519 (RFC 8032, Abschnitt 6) ----------
_p = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _inv(x):
    return pow(x, _p - 2, _p)


def _xrecover(y):
    xx = (y * y - 1) * _inv(_d * y * y + 1)
    x = pow(xx, (_p + 3) // 8, _p)
    if (x * x - xx) % _p != 0:
        x = (x * _I) % _p
    if x % 2 != 0:
        x = _p - x
    return x


_By = 4 * _inv(5) % _p
_B = (_xrecover(_By), _By, 1, _xrecover(_By) * _By % _p)   # erweiterte Koordinaten (X, Y, Z, T)


def _add(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % _p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % _p
    C = 2 * P[3] * Q[3] * _d % _p
    D = 2 * P[2] * Q[2] % _p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _p, G * H % _p, F * G % _p, E * H % _p)


def _mul(s, P):
    Q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _eq(P, Q):
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _compress(P):
    zi = _inv(P[2]); x = P[0] * zi % _p; y = P[1] * zi % _p
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(s):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little"); sign = y >> 255; y &= (1 << 255) - 1
    if y >= _p:
        return None
    xx = (y * y - 1) * _inv(_d * y * y + 1) % _p
    x = pow(xx, (_p + 3) // 8, _p)
    if (x * x - xx) % _p != 0:
        x = x * _I % _p
    if (x * x - xx) % _p != 0:
        return None
    if (x & 1) != sign:
        x = _p - x
    return (x, y, 1, x * y % _p)


def _h(m):
    return int.from_bytes(hashlib.sha512(m).digest(), "little")


def ed25519_verify(pub, msg, sig):
    if len(sig) != 64:
        return False
    A = _decompress(pub); R = _decompress(sig[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= _L:
        return False
    k = _h(sig[:32] + pub + msg) % _L
    return _eq(_mul(s, _B), _add(R, _mul(k, A)))


# ---------- Schlüssel ----------
def normalize(key):
    k = "".join(ch for ch in str(key or "").upper() if ch.isalnum())
    return k[3:] if k.startswith("GL1") else k


def decode(key):
    """Gibt (payload_bytes, sig, daten) zurück oder wirft ValueError."""
    raw = normalize(key)
    if not raw:
        raise ValueError("empty")
    try:
        b = base64.b32decode(raw + "=" * (-len(raw) % 8))
    except Exception:
        raise ValueError("format")
    if len(b) < 3 + 64 or b[0] != 1:
        raise ValueError("format")
    n = int.from_bytes(b[1:3], "big")
    if len(b) != 3 + n + 64:
        raise ValueError("format")
    body, sig = b[:3 + n], b[3 + n:]
    try:
        data = json.loads(body[3:].decode("utf-8"))
    except Exception:
        raise ValueError("format")
    return body, sig, data


def check(key, today=None):
    """Prüft einen Schlüssel. Ergebnis: dict(ok, state, until, order, days_left, error)
    state: none | invalid | expired | active"""
    if not str(key or "").strip():
        return {"ok": False, "state": "none"}
    try:
        body, sig, data = decode(key)
    except ValueError as e:
        return {"ok": False, "state": "invalid", "error": str(e)}
    try:
        pub = bytes.fromhex(PUBLIC_KEY_HEX)
    except ValueError:
        return {"ok": False, "state": "invalid", "error": "nokey"}
    if not ed25519_verify(pub, body, sig):
        return {"ok": False, "state": "invalid", "error": "signature"}
    if data.get("p") != PRODUCT:
        return {"ok": False, "state": "invalid", "error": "product"}
    try:
        until = datetime.date.fromisoformat(str(data.get("e")))
    except ValueError:
        return {"ok": False, "state": "invalid", "error": "format"}
    today = today or datetime.date.today()
    left = (until - today).days
    st = "active" if left >= 0 else "expired"
    return {"ok": st == "active", "state": st, "until": until.isoformat(), "days_left": left,
            "order": str(data.get("n") or ""), "issued": str(data.get("i") or "")}


def pretty(raw32):
    """Base32 ohne '=' in Fünfergruppen mit Präfix GL1."""
    return "GL1-" + "-".join(raw32[i:i + 5] for i in range(0, len(raw32), 5))
