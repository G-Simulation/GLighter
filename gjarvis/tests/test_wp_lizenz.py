"""Kompatibilität mit den Lizenzschlüsseln des WordPress-Plugins (gsimulations-lizenz.php) – GJarvis.
Test-Schlüsselpaar; der öffentliche Schlüssel wird nur im Test in lizenz.PUBLIC_KEY_HEX eingesetzt. Läuft vor und nach den Patches.
Schlüsseleingabe in der Oberfläche (/api/pro) muss über Ingress (172.30.32.2) weiter gehen.
Aufruf (aus gjarvis/):  python3 -m unittest discover -s tests -v   (braucht aiohttp + pyyaml)"""
# ---- gemeinsamer Teil (in allen drei Apps gleich) ----
import base64, datetime as dt, hashlib, io, json, os, struct, sys, tempfile, unittest
from unittest import mock

_TEST_SEED = hashlib.sha256(b"nur-fuer-tests-kein-echter-schluessel").digest()


def _sign(L, seed, msg):
    """Ed25519 (RFC 8032) mit den Rechenfunktionen aus lizenz.py – nur für den Test-Schlüssel."""
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    A = L._compress(L._mul(a, L._B))
    r = int.from_bytes(hashlib.sha512(h[32:] + msg).digest(), "little") % L._L
    R = L._compress(L._mul(r, L._B))
    k = int.from_bytes(hashlib.sha512(R + A + msg).digest(), "little") % L._L
    return R + ((r + k * a) % L._L).to_bytes(32, "little")


def _test_pub(L):
    h = hashlib.sha512(_TEST_SEED).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    return L._compress(L._mul(a, L._B)).hex()


def wp_key(L, product, until="2099-12-31", order="4711", wc_key="GL-ABCDE-FGHIJ-KLMNO-PQRST"):
    """Genau wie gsimulations-lizenz.php: chr(1) + pack('n', strlen(json)) + json + Ed25519-Signatur (detached, über
    chr(1)+Länge+json); Base32 A-Z2-7 ohne Padding, 5er-Gruppen mit '-'; Präfix GJ1 (gjarvis) bzw. GL1 (gaslighter, greport)."""
    js = json.dumps({"p": product, "e": until, "n": order, "i": dt.date.today().isoformat(), "w": wc_key[-5:]},
                    separators=(",", ":")).encode()
    body = b"\x01" + struct.pack(">H", len(js)) + js
    raw = base64.b32encode(body + _sign(L, _TEST_SEED, body)).decode().rstrip("=")
    return ("GJ1" if product == "gjarvis" else "GL1") + "-" + "-".join(raw[i:i + 5] for i in range(0, len(raw), 5))


class FakeWP:
    """Antwort des WordPress-Endpunkts /wp-json/gsim/v1/aktivieren (urlopen-Attrappe); merkt sich die Anfragen."""
    def __init__(self, reply, status=200):
        self.reply, self.status, self.reqs = reply, status, []

    def __call__(self, req, timeout=None):
        self.reqs.append((req.full_url, req.get_method(), json.loads(req.data.decode("utf-8"))))
        if self.status != 200:
            import urllib.error
            raise urllib.error.HTTPError(req.full_url, self.status, "x", {}, io.BytesIO(json.dumps(self.reply).encode()))
        r = mock.MagicMock(); r.read.return_value = json.dumps(self.reply).encode()
        r.__enter__.return_value = r
        return r


class WPFormat:
    """Prüft lizenz.py der App mit Schlüsseln im WordPress-Format. Erwartet: L (Modul), PRODUCT, OWN (akzeptierte Produkte)."""
    L = None; PRODUCT = ""; OWN = ()

    def setUp(self):
        self._pub = mock.patch.object(self.L, "PUBLIC_KEY_HEX", _test_pub(self.L)); self._pub.start()

    def tearDown(self):
        self._pub.stop()

    def test_offline_schluessel_gueltig(self):
        for p in self.OWN:
            k = wp_key(self.L, p)
            r = self.L.check(k)
            self.assertTrue(r["ok"], (p, r)); self.assertEqual((r["until"], r["order"]), ("2099-12-31", "4711"))
            self.assertTrue(self.L.check(k.lower().replace("-", " "))["ok"])     # Leerzeichen/Kleinschreibung egal

    def test_fremdes_produkt_und_falsche_signatur(self):
        for p in {"gjarvis", "gaslighter", "greport"} - set(self.OWN):
            r = self.L.check(wp_key(self.L, p))                            # GJ1-Präfix in GLighter/GReport: schon „format“
            self.assertFalse(r["ok"], p); self.assertIn(r["error"], ("product", "format"), p)
        k = wp_key(self.L, self.OWN[0]); g = k.split("-")
        g[3] = "".join("A" if c != "A" else "B" for c in g[3])
        self.assertFalse(self.L.check("-".join(g))["ok"])
        with mock.patch.object(self.L, "PUBLIC_KEY_HEX", "00" * 31 + "01"):
            self.assertFalse(self.L.check(k)["ok"])                             # anderer öffentlicher Schlüssel

    def test_abgelaufen(self):
        r = self.L.check(wp_key(self.L, self.OWN[0], until="2020-01-01"))
        self.assertEqual((r["ok"], r["state"]), (False, "expired"))

    def test_aktivierung_beim_wordpress_server(self):
        off = wp_key(self.L, self.OWN[0])
        wp = FakeWP({"ok": True, "key": off})
        with mock.patch("urllib.request.urlopen", wp):
            key, r, shop = self.L.resolve("GL-ABCDE-FGHIJ-KLMNO-PQRST")
        self.assertEqual((key, r["ok"], shop), (off, True, "GL-ABCDE-FGHIJ-KLMNO-PQRST"))
        url, meth, body = wp.reqs[0]
        self.assertTrue(url.endswith("/wp-json/gsim/v1/aktivieren")); self.assertEqual(meth, "POST")
        self.assertEqual(body, {"key": "GL-ABCDE-FGHIJ-KLMNO-PQRST", "product": self.PRODUCT})

    def test_aktivierung_fehler_vom_server(self):
        with mock.patch("urllib.request.urlopen", FakeWP({"ok": False, "error": "disabled"}, status=403)):
            self.assertEqual(self.L.resolve("GL-ABCDE-FGHIJ-KLMNO-PQRST")[1]["error"], "disabled")
# ---- Ende gemeinsamer Teil ----

import pathlib, types  # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
for name, attrs in {"webrtcvad": ["Vad"], "wyoming": [], "wyoming.asr": ["Transcribe", "Transcript"],
                    "wyoming.audio": ["AudioChunk", "AudioStart", "AudioStop"], "wyoming.client": ["AsyncTcpClient"],
                    "wyoming.tts": ["Synthesize", "SynthesizeVoice"]}.items():
    if name not in sys.modules:
        try:
            __import__(name)
        except ImportError:
            m = types.ModuleType(name)
            for a in attrs:
                setattr(m, a, type(a, (), {}))
            sys.modules[name] = m
from aiohttp.test_utils import AioHTTPTestCase  # noqa: E402
import lizenz   # noqa: E402
import gjarvis  # noqa: E402
import web      # noqa: E402


class GJarvisWP(WPFormat, unittest.TestCase):
    L = lizenz; PRODUCT = "gjarvis"; OWN = ("gjarvis",)


class GJ:
    """Nur die Lizenz-Teile der echten Klasse."""
    raw, o, restart_pending = {}, {}, False
    pro_state = gjarvis.GJarvis.pro_state; pro_set = gjarvis.GJarvis.pro_set; pro_del = gjarvis.GJarvis.pro_del
    pro = gjarvis.GJarvis.pro

    def status(self):
        return {"state": "idle"}


class SchluesselUeberIngress(AioHTTPTestCase):
    async def get_application(self):
        return web.make_app(GJ())

    async def test_eingeben_aktivieren_entfernen(self):
        tmp = tempfile.mkdtemp()
        pubp = mock.patch.object(lizenz, "PUBLIC_KEY_HEX", _test_pub(lizenz))
        filep = mock.patch.object(gjarvis, "PRO_FILE", pathlib.Path(tmp) / "lizenz.json")
        extra = [mock.patch.object(web, "RESTRICT", True)] if hasattr(web, "RESTRICT") else []   # mit Ingress-Schutz (Patch 01)
        for p in [pubp, filep] + extra:
            p.start(); self.addCleanup(p.stop)
        with mock.patch("urllib.request.urlopen", FakeWP({"ok": True, "key": wp_key(lizenz, "gjarvis")})) as _:
            r = await self.client.request("POST", "/api/pro", json={"key": "GJ-MN63R-URMYH-YY3CA-2GU34"})
        self.assertEqual(r.status, 200, await r.text())
        r = await self.client.request("GET", "/api/pro")
        st = await r.json()
        self.assertTrue(st["ok"], st); self.assertEqual(st["until"], "2099-12-31")
        r = await self.client.request("POST", "/api/pro", json={"key": wp_key(lizenz, "gaslighter")})   # GLighter-Schlüssel gilt nicht
        self.assertEqual(r.status, 400)
        r = await self.client.request("POST", "/api/pro", json={"remove": True})
        self.assertEqual(r.status, 200)


if __name__ == "__main__":
    unittest.main()
