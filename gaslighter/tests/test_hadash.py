"""Dashboard-Vorlage: gegen einen nachgebauten Home-Assistant-WebSocket (ohne echtes Home Assistant).
Aufruf:  python3 -m unittest tests.test_hadash -v     (aus dem App-Ordner)"""
import base64, hashlib, json, os, socket, struct, sys, threading, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("app", ""):
    p = os.path.join(HERE, "..", sub)
    if os.path.exists(os.path.join(p, "hadash.py")):
        sys.path.insert(0, p)
import hadash  # noqa: E402


class FakeHA:
    """Sehr kleiner WebSocket-Server, der die benutzten Befehle beantwortet und alles mitschreibt."""

    def __init__(self, registry, boards=None):
        self.registry, self.boards, self.saved, self.calls = registry, list(boards or []), {}, []
        self.srv = socket.socket(); self.srv.bind(("127.0.0.1", 0)); self.srv.listen(5)
        self.port = self.srv.getsockname()[1]
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while True:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            threading.Thread(target=self.client, args=(c,), daemon=True).start()

    @staticmethod
    def rd(c, n):
        b = b""
        while len(b) < n:
            x = c.recv(n - len(b))
            if not x:
                raise EOFError
            b += x
        return b

    def recv(self, c):
        b1, b2 = self.rd(c, 2); n = b2 & 0x7F
        if n == 126:
            n = struct.unpack(">H", self.rd(c, 2))[0]
        elif n == 127:
            n = struct.unpack(">Q", self.rd(c, 8))[0]
        m = self.rd(c, 4); p = self.rd(c, n)
        return json.loads(bytes(x ^ m[i % 4] for i, x in enumerate(p)))

    @staticmethod
    def send(c, o):
        p = json.dumps(o).encode(); n = len(p)
        h = bytes([0x81, n]) if n < 126 else (bytes([0x81, 126]) + struct.pack(">H", n) if n < 65536 else bytes([0x81, 127]) + struct.pack(">Q", n))
        c.sendall(h + p)

    def client(self, c):
        try:
            req = b""
            while b"\r\n\r\n" not in req:
                req += c.recv(4096)
            key = [l.split(b": ", 1)[1] for l in req.split(b"\r\n") if l.lower().startswith(b"sec-websocket-key")][0]
            acc = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
            c.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + acc + b"\r\n\r\n")
            self.send(c, {"type": "auth_required"})
            a = self.recv(c)
            self.send(c, {"type": "auth_ok" if a.get("access_token") == "tok" else "auth_invalid"})
            while True:
                m = self.recv(c); self.calls.append(m); t = m["type"]; res = None; ok = True
                if t == "config/entity_registry/list":
                    res = self.registry
                elif t == "lovelace/dashboards/list":
                    res = self.boards
                elif t == "lovelace/dashboards/create":
                    b = dict(m, id=f"d{len(self.boards)}"); b.pop("type"); self.boards.append(b); res = b
                elif t == "lovelace/dashboards/update":
                    res = {}
                elif t == "lovelace/config/save":
                    self.saved[m["url_path"]] = m["config"]
                else:
                    ok = False
                self.send(c, {"id": m["id"], "type": "result", "success": ok, "result": res,
                              **({} if ok else {"error": {"code": "unknown_command", "message": t}})})
        except (EOFError, OSError, IndexError):
            pass
        finally:
            c.close()


class HadashTest(unittest.TestCase):
    def setUp(self):
        reg = [{"unique_id": "gaslighter_level", "entity_id": "sensor.glighter_pegel"},
               {"unique_id": "gaslighter_mark", "entity_id": "button.glighter_mark"},
               {"unique_id": "gaslighter_off", "entity_id": "sensor.aus", "disabled_by": "user"},
               {"unique_id": "anderes_level", "entity_id": "sensor.fremd"}]
        self.ha = FakeHA(reg, boards=[{"id": "x1", "url_path": "schon-da", "title": "Eigenes"}])
        os.environ["HADASH_TOKEN"] = "tok"
        hadash.WS_URL = f"ws://127.0.0.1:{self.ha.port}/api/websocket"

    def tearDown(self):
        self.ha.srv.close(); os.environ.pop("HADASH_TOKEN", None)

    def test_entitaeten_nur_eigene_und_aktive(self):
        self.assertEqual(hadash.entity_map("gaslighter"), {"gaslighter_level": "sensor.glighter_pegel", "gaslighter_mark": "button.glighter_mark"})

    def test_neu_anlegen_und_speichern(self):
        cfg = hadash.board("Test", [hadash.section([hadash.heading("A"), hadash.tile("sensor.x")])])
        r = hadash.install("gsim-test", "Test", "mdi:ear-hearing", cfg)
        self.assertTrue(r["ok"]); self.assertTrue(r["created"])
        self.assertEqual(self.ha.saved["gsim-test"]["views"][0]["sections"][0]["cards"][1]["entity"], "sensor.x")
        self.assertEqual([c["type"] for c in self.ha.calls], ["lovelace/dashboards/list", "lovelace/dashboards/create", "lovelace/config/save"])

    def test_vorhandenes_nie_ohne_rueckfrage_ueberschreiben(self):
        r = hadash.install("schon-da", "X", "mdi:x", {"views": []})
        self.assertFalse(r["ok"]); self.assertTrue(r["exists"]); self.assertEqual(self.ha.saved, {})
        r = hadash.install("schon-da", "X", "mdi:x", {"views": []}, overwrite=True)
        self.assertTrue(r["ok"]); self.assertFalse(r["created"]); self.assertIn("schon-da", self.ha.saved)

    def test_adresse_wird_geprueft(self):
        for bad in ("ohnebindestrich", "Gross-Buchstaben", "-vorne", "a b-c", "x" * 41 + "-y"):
            self.assertFalse(hadash.valid_url(bad), bad)
            with self.assertRaises(hadash.HAError):
                hadash.install(bad, "X", "mdi:x", {})
        self.assertTrue(hadash.valid_url("gsim-glighter"))

    def test_ohne_token_keine_verbindung(self):
        os.environ.pop("HADASH_TOKEN"); os.environ.pop("SUPERVISOR_TOKEN", None)
        self.assertFalse(hadash.available())
        with self.assertRaises(hadash.HAError):
            hadash.call({"type": "lovelace/dashboards/list"})

    def test_yaml_lesbar_und_gequotet(self):
        y = hadash.to_yaml({"title": "GLighter: Test", "views": [{"type": "sections", "cards": [{"entity": "sensor.a", "n": 3, "on": "on"}], "leer": []}]})
        self.assertIn('title: "GLighter: Test"', y)
        self.assertIn("\n- type: sections\n  cards:\n  - entity: sensor.a\n    n: 3\n    \"on\": \"on\"\n  leer: []", y)
        try:
            import yaml
        except ImportError:
            return
        self.assertEqual(yaml.safe_load(y)["views"][0]["cards"][0], {"entity": "sensor.a", "n": 3, "on": "on"})

    def test_leere_bereiche_fallen_weg(self):
        b = hadash.board("T", [hadash.section([hadash.heading("nur Überschrift"), None]), hadash.section([hadash.heading("A"), hadash.tile("s.x")])])
        self.assertEqual(len(b["views"][0]["sections"]), 1)

    def test_slug_aus_hostname(self):
        os.environ["HOSTNAME"] = "eef0ca55-gaslighter"
        self.assertEqual(hadash.self_slug("x"), "eef0ca55_gaslighter")
        os.environ["HOSTNAME"] = "irgendwas"
        self.assertEqual(hadash.self_slug("local_gaslighter"), "local_gaslighter")

    def test_alle_apps_haben_dieselbe_datei(self):
        root = os.path.join(HERE, "..", "..")
        files = [os.path.join(root, a) for a in ("gaslighter/app/hadash.py", "greport/app/hadash.py", "gjarvis/hadash.py")]
        have = [open(f, "rb").read() for f in files if os.path.exists(f)]
        if len(have) > 1:
            self.assertTrue(all(h == have[0] for h in have))
        ui = [os.path.join(root, a) for a in ("gaslighter/app/web/hadash-ui.js", "greport/app/web/hadash-ui.js", "gjarvis/web/hadash-ui.js")]
        have = [open(f, "rb").read() for f in ui if os.path.exists(f)]
        if len(have) > 1:
            self.assertTrue(all(h == have[0] for h in have))


if __name__ == "__main__":
    unittest.main()
