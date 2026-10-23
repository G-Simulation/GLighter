"""GJarvis: Schlüssel in Adressen und Token landen nie im Protokoll (/api/log und Konsole); Protokoll liefert items."""
import logging, os, sys, types, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
for name, attrs in {"webrtcvad": ["Vad"], "wyoming": [], "wyoming.asr": ["Transcribe", "Transcript"], "wyoming.audio": ["AudioChunk", "AudioStart", "AudioStop"],
                    "wyoming.client": ["AsyncTcpClient"], "wyoming.tts": ["Synthesize", "SynthesizeVoice"]}.items():
    try:
        __import__(name)
    except ImportError:
        m = types.ModuleType(name)
        for a in attrs:
            setattr(m, a, type(a, (), {}))
        sys.modules[name] = m
import web  # noqa: E402


class Schwaerzen(unittest.TestCase):
    def setUp(self):
        self.ring = web.RingLog(50)
        self.log = logging.getLogger("gjarvis.test_schwaerzen"); self.log.handlers = [self.ring]; self.log.propagate = False; self.log.setLevel(logging.DEBUG)

    def test_url_schluessel(self):
        self.log.error("Fehler: 403 for url: https://api.paraglidable.com/?key=GEHEIM123&format=JSON&version=1")
        self.log.warning("x %s", "https://a.b/c?token=abc.def&apikey=zzz")
        txt = "\n".join(self.ring.lines)
        self.assertNotIn("GEHEIM123", txt); self.assertNotIn("abc.def", txt); self.assertNotIn("zzz", txt)
        self.assertIn("key=***&format=JSON", txt)
        self.assertNotIn("GEHEIM123", " ".join(i["msg"] for i in self.ring.items))

    def test_ausnahme_und_bearer(self):
        try:
            raise RuntimeError("GET https://x.y/?api_key=SECRET42 failed")
        except RuntimeError:
            self.log.exception("Wetter")
        self.log.info("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abcdef")
        txt = "\n".join(self.ring.lines)
        self.assertNotIn("SECRET42", txt); self.assertNotIn("eyJhbGciOiJIUzI1NiJ9", txt); self.assertIn("api_key=***", txt)

    def test_konsole(self):
        import io
        buf = io.StringIO(); h = logging.StreamHandler(buf); h.addFilter(web.RedactFilter())
        lg = logging.getLogger("gjarvis.test_konsole"); lg.handlers = [h]; lg.propagate = False
        lg.warning("GET %s", "https://api.openweathermap.org/data/2.5/weather?q=Berlin&appid=ABC123&units=metric")
        self.assertIn("appid=***&units=metric", buf.getvalue()); self.assertNotIn("ABC123", buf.getvalue())
        self.assertEqual(web.redact("https://x.y/?q=1"), "https://x.y/?q=1")          # ohne Schlüssel unverändert

    def test_items_fuer_tabelle(self):
        self.log.warning("Mikrofon leise")
        it = self.ring.items[-1]
        self.assertEqual((it["lvl"], it["name"], it["msg"]), ("WARNING", "gjarvis.test_schwaerzen", "Mikrofon leise"))
        self.assertEqual(self.ring.lines[-1].split(" ", 2)[1:], ["WARNING", "Mikrofon leise"])   # Textzeile wie bisher
        self.assertGreater(self.ring.items[-1]["id"], 0)


if __name__ == "__main__":
    unittest.main()
