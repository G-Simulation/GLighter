"""Kurze Sitzung mit der WebSocket-API von Home Assistant – nur Python-Standardbibliothek.

Wird von GReport nur für die Dashboard-Karte gebraucht (Ressource eintragen/aktualisieren/austragen).
"""
import base64
import json
import secrets
import socket
import struct
import urllib.parse


def call(url, token, *msgs, timeout=15):
    """url = REST-Adresse von Home Assistant (z. B. http://supervisor/core/api). Gibt die Ergebnisse der Befehle zurück."""
    u = urllib.parse.urlparse(url)
    path = (u.path[:-4] if u.path.endswith("/api") else u.path).rstrip("/") + "/api/websocket"
    sock = socket.create_connection((u.hostname, u.port or 80), timeout=timeout)
    buf = b""

    def recv_n(n):
        nonlocal buf
        while len(buf) < n:
            ch = sock.recv(65536)
            if not ch:
                raise RuntimeError("Verbindung getrennt")
            buf += ch
        out, buf = buf[:n], buf[n:]
        return out

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
                raise RuntimeError("Verbindung geschlossen")
            if op in (0, 1, 2):
                data += payload
                if b1 & 0x80:
                    return json.loads(data.decode("utf-8"))

    def send(obj):
        p = json.dumps(obj).encode()
        n = len(p)
        if n < 126:
            hdr = bytes([0x81, 0x80 | n])
        elif n < 65536:
            hdr = bytes([0x81, 0x80 | 126]) + struct.pack(">H", n)
        else:
            hdr = bytes([0x81, 0x80 | 127]) + struct.pack(">Q", n)
        mask = secrets.token_bytes(4)
        sock.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(p)))

    try:
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {u.hostname}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                      f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        while b"\r\n\r\n" not in buf:
            ch = sock.recv(4096)
            if not ch:
                raise RuntimeError("WebSocket abgelehnt")
            buf += ch
        head, buf = buf.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise RuntimeError("WebSocket abgelehnt")
        recv()                                                   # auth_required
        send({"type": "auth", "access_token": token})
        if recv().get("type") != "auth_ok":
            raise RuntimeError("Anmeldung an Home Assistant fehlgeschlagen")
        out = []
        for i, m in enumerate(msgs, 1):
            send(dict(m, id=i))
            while True:
                r = recv()
                if r.get("id") == i and r.get("type") == "result":
                    break
            if not r.get("success"):
                raise RuntimeError((r.get("error") or {}).get("message") or "Home Assistant lehnt ab")
            out.append(r.get("result"))
        return out
    finally:
        try:
            sock.close()
        except OSError:
            pass
