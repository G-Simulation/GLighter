"""Dashboard-Vorlage in Home Assistant anlegen – gemeinsam für GLighter, GReport und GJarvis.

Nur Python-Standardbibliothek. Spricht die WebSocket-API von Home Assistant über den Supervisor an
(SUPERVISOR_TOKEN, „homeassistant_api: true“). Ändert in Home Assistant nur dann etwas, wenn der
Benutzer in der App ausdrücklich „Dashboard anlegen“ bzw. „Überschreiben“ wählt.

Die Datei ist in allen drei Apps gleich (Test prüft das).
"""
import base64
import json
import os
import re
import secrets
import socket
import struct
import urllib.parse

WS_URL = os.environ.get("HADASH_WS", "ws://supervisor/core/websocket")


class HAError(RuntimeError):
    pass


def token():
    return os.environ.get("HADASH_TOKEN") or os.environ.get("SUPERVISOR_TOKEN") or ""


def available():
    return bool(token())


def call(*msgs, timeout=15):
    """Mehrere Befehle in einer kurzen Sitzung. Gibt die Ergebnisse in derselben Reihenfolge zurück."""
    tok = token()
    if not tok:
        raise HAError("no_supervisor")
    u = urllib.parse.urlparse(WS_URL)
    sock = socket.create_connection((u.hostname, u.port or 80), timeout=timeout)
    buf = b""

    def recv_n(n):
        nonlocal buf
        while len(buf) < n:
            ch = sock.recv(65536)
            if not ch:
                raise HAError("Verbindung getrennt")
            buf += ch
        out, buf = buf[:n], buf[n:]
        return out

    def send_frame(op, p):
        n = len(p)
        if n < 126:
            hdr = bytes([0x80 | op, 0x80 | n])
        elif n < 65536:
            hdr = bytes([0x80 | op, 0x80 | 126]) + struct.pack(">H", n)
        else:
            hdr = bytes([0x80 | op, 0x80 | 127]) + struct.pack(">Q", n)
        mask = secrets.token_bytes(4)
        sock.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(p)))

    def recv():
        data = b""
        while True:
            b1, b2 = recv_n(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", recv_n(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", recv_n(8))[0]
            payload = recv_n(n)
            op = b1 & 0x0F
            if op == 8:
                raise HAError("Verbindung geschlossen")
            if op == 9:                                   # Ping -> Pong
                send_frame(0xA, payload)
                continue
            if op in (0, 1, 2):
                data += payload
                if b1 & 0x80:
                    return json.loads(data.decode("utf-8"))

    def send(obj):
        send_frame(0x1, json.dumps(obj).encode())

    try:
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        path = u.path or "/"
        sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {u.hostname}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                      f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        while b"\r\n\r\n" not in buf:
            ch = sock.recv(4096)
            if not ch:
                raise HAError("WebSocket abgelehnt")
            buf += ch
        head, buf = buf.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n")[0] + b" ":
            raise HAError("WebSocket abgelehnt")
        recv()                                            # auth_required
        send({"type": "auth", "access_token": tok})
        if recv().get("type") != "auth_ok":
            raise HAError("Anmeldung an Home Assistant fehlgeschlagen")
        out = []
        for i, m in enumerate(msgs, 1):
            send(dict(m, id=i))
            while True:
                r = recv()
                if r.get("id") == i and r.get("type") == "result":
                    break
            if not r.get("success"):
                err = r.get("error") or {}
                raise HAError(err.get("message") or err.get("code") or "Home Assistant lehnt ab")
            out.append(r.get("result"))
        return out
    finally:
        try:
            sock.close()
        except OSError:
            pass


# ---------------------------------------------------------------- Entitäten und Dashboards

def entity_map(prefix):
    """unique_id -> entity_id für alle Entitäten, deren unique_id mit prefix beginnt (nur lesen)."""
    reg = call({"type": "config/entity_registry/list"})[0] or []
    out = {}
    for e in reg:
        uid = str(e.get("unique_id") or "")
        if uid.startswith(prefix) and not e.get("disabled_by"):
            out[uid] = e.get("entity_id")
    return out


def find(url_path):
    """Dashboard-Eintrag mit dieser Adresse oder None (nur lesen)."""
    boards = call({"type": "lovelace/dashboards/list"})[0] or []
    return next((x for x in boards if x.get("url_path") == url_path), None)


URL_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)+$")


def valid_url(url_path):
    return bool(URL_RE.match(url_path or "")) and len(url_path) <= 40


def install(url_path, title, icon, config, sidebar=True, admin=False, overwrite=False):
    """Dashboard anlegen (falls neu) und die Konfiguration speichern.
    Ein vorhandenes Dashboard wird nur mit overwrite=True ersetzt."""
    if not valid_url(url_path):
        raise HAError("bad_url")
    b = find(url_path)
    if b and not overwrite:
        return {"ok": False, "exists": True}
    if not b:
        call({"type": "lovelace/dashboards/create", "url_path": url_path, "title": title[:60] or "GSimulations",
              "icon": icon, "show_in_sidebar": bool(sidebar), "require_admin": bool(admin), "mode": "storage"})
    else:
        call({"type": "lovelace/dashboards/update", "dashboard_id": b["id"], "title": title[:60] or b.get("title"),
              "icon": icon, "show_in_sidebar": bool(sidebar), "require_admin": bool(admin)})
    call({"type": "lovelace/config/save", "url_path": url_path, "config": config})
    return {"ok": True, "created": not b, "url": "/" + url_path}


def self_slug(default):
    """Slug dieser App (z. B. eef0ca55_gaslighter) aus dem Hostnamen des Containers."""
    h = os.environ.get("HOSTNAME", "")
    return h.replace("-", "_") if re.match(r"^[0-9a-f]{8}-[a-z0-9_-]+$", h) else default


# ---------------------------------------------------------------- YAML zum Kopieren

def _scalar(v):
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or re.search(r"[:#\[\]{}&*!|>'\"%@`,]|^[\s\-?]|\s$|\n", s) or s.lower() in ("yes", "no", "on", "off", "true", "false", "null", "~") \
            or re.match(r"^[0-9.+-]", s):
        return json.dumps(s, ensure_ascii=False)
    return s


def to_yaml(obj, ind=0):
    pad = "  " * ind
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            k = _scalar(str(k))
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{k}:")
                out.append(to_yaml(v, ind + 1) if isinstance(v, dict) else to_yaml(v, ind))
            else:
                out.append(f"{pad}{k}: {_scalar(v) if not isinstance(v, (dict, list)) else ('{}' if isinstance(v, dict) else '[]')}")
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, dict) and v:
                sub = to_yaml(v, ind + 1).split("\n")
                out.append(f"{pad}- {sub[0].lstrip()}")
                out.extend(sub[1:])
            elif isinstance(v, list) and v:
                out.append(f"{pad}-")
                out.append(to_yaml(v, ind + 1))
            else:
                out.append(f"{pad}- {_scalar(v)}")
    else:
        out.append(pad + _scalar(obj))
    return "\n".join(out)


# ---------------------------------------------------------------- Bausteine für die Vorlagen

def tile(eid, name=None, **kw):
    c = {"type": "tile", "entity": eid}
    if name:
        c["name"] = name
    c.update(kw)
    return c


def press(eid, name=None, icon=None):
    """Kachel für eine Schaltfläche (button.*): ein Tipp drückt sie."""
    act = {"action": "perform-action", "perform_action": "button.press", "target": {"entity_id": eid}}
    c = tile(eid, name, tap_action=act, icon_tap_action=act)
    if icon:
        c["icon"] = icon
    return c


def heading(text, icon=None):
    c = {"type": "heading", "heading": text}
    if icon:
        c["icon"] = icon
    return c


def open_button(name, slug, icon):
    return {"type": "button", "name": name, "icon": icon, "show_state": False,
            "tap_action": {"action": "navigate", "navigation_path": f"/app/{slug}"}}


def section(cards):
    return {"type": "grid", "cards": [c for c in cards if c]}


def board(title, sections):
    return {"title": title,
            "views": [{"title": title, "path": "start", "type": "sections", "max_columns": 3,
                       "sections": [s for s in sections if len(s["cards"]) > 1]}]}
