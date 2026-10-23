"""GReport Sicherheit: erlaubte Pfade, fremde Dateien nicht überschreiben, CSV-Formeln, Bremse für Home Assistant,
ungültige Anfragen, Markdown in der Dashboard-Vorlage."""
import io, os, shutil, sys, tempfile, unittest

D = tempfile.mkdtemp()
os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import greport as G  # noqa: E402


class Pfade(unittest.TestCase):
    def setUp(self):
        G.NOTES["data"] = None; G.QT["data"] = None
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)
        self.root = os.path.dirname(G.DIR); self.media = os.path.join(D, "media"); os.makedirs(self.media, exist_ok=True)
        self.old = G.TXT_ROOTS[:]; G.TXT_ROOTS[:] = [self.root, self.media]

    def tearDown(self):
        G.TXT_ROOTS[:] = self.old

    def test_schreiben_nur_in_eigene_ordner(self):
        ok = (".txt", ".csv", ".json", ".log")
        self.assertIsNotNone(G.safe_path(os.path.join(G.DIR, "export", "a.txt"), ok))
        self.assertIsNotNone(G.safe_path(os.path.join(self.media, "greport", "a.csv"), ok))
        for bad in (os.path.join(G.DIR, "notizen.json"), os.path.join(G.DIR, "einstellungen.json"), os.path.join(G.DIR, "notizen_protokoll.log"),
                    os.path.join(self.root, "gaslighter", "x.json"), os.path.join(self.media, "gaslighter", "x.txt"), os.path.join(self.media, "a.txt"),
                    "/etc/passwd.txt", os.path.join(G.DIR, "export", "..", "notizen.json"), os.path.join(G.DIR, "export", "a.exe")):
            self.assertIsNone(G.safe_path(bad, ok), bad)

    def test_lesen_nur_aus_import_und_media(self):
        ok = (".txt", ".json")
        self.assertIsNotNone(G.safe_path(os.path.join(G.DIR, "import", "a.txt"), ok, write=False))
        self.assertIsNotNone(G.safe_path(os.path.join(self.media, "sub", "a.txt"), ok, write=False))
        for bad in (os.path.join(G.DIR, "notizen.json"), os.path.join(G.DIR, "export", "a.txt"), os.path.join(self.media, "gjarvis", "a.txt"),
                    os.path.join(self.root, "gaslighter", "notizen.json")):
            self.assertIsNone(G.safe_path(bad, ok, write=False), bad)

    def test_fremde_datei_wird_nicht_ueberschrieben(self):
        p = os.path.join(G.DIR, "export", "a.txt"); os.makedirs(os.path.dirname(p))
        with open(p, "w") as f:
            f.write("fremd")
        q = G._write_text(p, "neu"); self.assertEqual(q, os.path.join(G.DIR, "export", "a_2.txt"))
        with open(p) as f:
            self.assertEqual(f.read(), "fremd")
        self.assertEqual(G._write_text(p, "noch mal"), q)                       # eigene Datei: wieder dieselbe

    def test_alter_tagebuchpfad_wird_umgestellt(self):
        G.write_json(os.path.join(G.DIR, "einstellungen.json"), {"txt": {"on": True, "path": os.path.join(self.root, "gaslighter", "t.txt")}})
        c = G.txt_cfg(); self.assertEqual(c["path"], ""); self.assertTrue(c["moved"].endswith("t.txt"))
        self.assertTrue(G.txt_default_path().startswith(os.path.join(G.DIR, "export")))


class CsvUndAnfragen(unittest.TestCase):
    def setUp(self):
        G.NOTES["data"] = None; G.QT["data"] = None
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)

    def test_formeln_werden_entschaerft(self):
        for v, want in (("=HYPERLINK(\"x\")", "'=HYPERLINK(\"x\")"), ("+1", "'+1"), ("-2", "'-2"), ("@a", "'@a"), ("\tx", "'\tx"), ("Bass", "Bass"), ("", "")):
            self.assertEqual(G.csv_safe(v), want)
        G.note_change("add", {"text": "=1+2", "witness": "@Anna", "from": "2026-10-20T22:00:00+02:00"})
        out = G.export_csv().decode("utf-8")
        self.assertIn(";'=1+2;", out); self.assertIn(";'@Anna;", out)
        rows, _ = G.parse_import(out); self.assertEqual(rows[0]["text"], "=1+2")          # Import nimmt den Schutz wieder weg
        self.assertIn("'=1+2", G.export_text("csv"))

    def test_bremse_fuer_home_assistant(self):
        G.HA_RATE.update(last=0.0, tok=G.HA_BURST, day=None, n=0, warned=None)
        oks = [G.note_change("add", {"text": f"n{i}"}, by="homeassistant").get("ok") for i in range(8)]
        self.assertEqual(oks.count(True), 5); self.assertEqual(G.note_change("add", {"text": "x"}, by="homeassistant")["error"], "rate")
        self.assertTrue(all(G.note_change("add", {"text": f"app{i}"})["ok"] for i in range(10)))   # aus der App unbegrenzt
        G.HA_RATE.update(last=0.0, tok=G.HA_BURST, n=G.HA_MAX_DAY)
        self.assertEqual(G.note_change("add", {"text": "y"}, by="homeassistant")["error"], "rate")

    def test_ungueltige_laenge(self):
        class Fake:
            body = G.H.body

            def __init__(self, n):
                self.headers = {"Content-Length": n}; self.rfile = io.BytesIO(b"{}")
        for n in ("-5", "abc", str(30 * 1024 * 1024)):
            with self.assertRaises(ValueError):
                Fake(n).body()
        self.assertEqual(Fake("2").body(), {})
        self.assertEqual(G.H.timeout, 30)

    def test_markdown_in_vorlage_entschaerft(self):
        self.assertIn("replace('[','&#91;')", G.MD_ESC); self.assertIn("replace('(','&#40;')", G.MD_ESC)
        cfg = G.hadash_config({"parts": ["letzte"], "title": "GReport", "url": "gsim-greport", "icon": "mdi:note", "sidebar": True, "admin": False}, {"greport_letzte_notiz": "sensor.greport_letzte_notiz"})
        md = str(cfg)
        self.assertIn("x.text|string|replace('&','&amp;')", md); self.assertIn("x.zeuge|string", md)


if __name__ == "__main__":
    unittest.main()
