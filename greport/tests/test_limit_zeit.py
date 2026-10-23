"""GReport: Tagebuch/Export ohne 5000er-Grenze; Zeiten mit Offset, auch in der doppelten Stunde am 25.10.2026."""
import json, os, re, shutil, subprocess, sys, tempfile, time, unittest

if "GR_DIR" not in os.environ:                       # wie test_greport.py (gleiche Umgebung, falls zusammen gestartet)
    D = tempfile.mkdtemp()
    os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import greport as G  # noqa: E402


class Berlin(unittest.TestCase):
    def setUp(self):
        self.tz = os.environ.get("TZ"); os.environ["TZ"] = "Europe/Berlin"; time.tzset()
        G.NOTES["data"] = None; G.QT["data"] = None
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)
        self.pro = G.pro_ok; G.pro_ok = lambda: True

    def tearDown(self):
        G.pro_ok = self.pro
        if self.tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = self.tz
        time.tzset()


class OhneGrenze(Berlin):
    def test_6000_notizen_im_export_und_tagebuch(self):
        t0 = G.ms_of("2025-01-01T00:00:00+01:00")
        notes = [{"id": f"n{i}", "from": G.iso_of(t0 + i * 3600000), "text": f"Notiz {i}"} for i in range(6000)]
        self.assertEqual(G.notes_import({"notes": notes})["n"], 6000)
        rows = [r for r in G.export_csv().decode("utf-8").strip().splitlines() if not r.startswith("#")]   # ohne Prüfblock am Ende
        self.assertEqual(len(rows), 6001)                               # Kopfzeile + alle 6000
        self.assertIn("Notiz 0", rows[1])                               # die älteste ist dabei
        txt = G.export_text("txt")
        self.assertIn("Notiz 0", txt); self.assertIn("Notiz 5999", txt)
        self.assertEqual(len(G.notes_list(limit=None)), 6000)
        self.assertEqual(len(G.notes_list(limit=10 ** 6)), 5000)        # Abfrage über die Oberfläche bleibt begrenzt


class Zeitumstellung(Berlin):
    def test_doppelte_stunde_mit_offset(self):
        a = G.ms_of("2026-10-25T02:30:00+02:00"); b = G.ms_of("2026-10-25T02:30:00+01:00")
        self.assertEqual(b - a, 3600000)
        self.assertEqual(G.iso_of(b), "2026-10-25T02:30:00+01:00")      # zweite 02:30 bleibt die zweite
        self.assertEqual(G.iso_of(a), "2026-10-25T02:30:00+02:00")
        self.assertEqual(G.ms_of("2026-10-25T00:30:00Z"), a)
        self.assertEqual(G.ms_of("2026-10-25T02:30:00"), a)             # ohne Offset: erste (Sommerzeit), wie im Browser

    def test_notiz_in_der_zweiten_0230(self):
        r = G.note_change("add", {"text": "Bass", "from": "2026-10-25T02:30:00+01:00", "to": "2026-10-25T02:45:00+01:00"})
        self.assertTrue(r["ok"], r)
        self.assertEqual((r["note"]["from"], r["note"]["to"]), ("2026-10-25T02:30:00+01:00", "2026-10-25T02:45:00+01:00"))
        r2 = G.note_change("add", {"text": "über die Umstellung", "from": "2026-10-25T02:50:00+02:00", "to": "2026-10-25T02:10:00+01:00"})
        self.assertTrue(r2["ok"], r2)                                   # 20 min, obwohl „02:10“ < „02:50“ aussieht

    def test_andere_zeitzone_des_browsers(self):
        r = G.note_change("add", {"text": "x", "from": "2026-10-18T09:00:00-04:00"})     # Browser in New York
        self.assertEqual(r["note"]["from"], "2026-10-18T15:00:00+02:00")


@unittest.skipUnless(shutil.which("node"), "node fehlt")
class OberflaecheSchicktOffset(unittest.TestCase):
    def test_dto_und_inIso(self):
        with open(os.path.join(HERE, "..", "app", "web", "app.js"), encoding="utf-8") as f:
            src = f.read()
        defs = "\n".join(m.group(0) for m in re.finditer(r"^const (pad|isoDay|dtl|tzo|dto|inIso) = .*$", src, re.M))
        js = defs + """
const out = [dto(new Date(Date.UTC(2026, 9, 25, 0, 30))), dto(new Date(Date.UTC(2026, 9, 25, 1, 30))),
  inIso('2026-10-25T02:30:00', '2026-10-25T02:30:00+01:00'), inIso('2026-10-25T02:40:00', '2026-10-25T02:30:00+01:00'), inIso('', 'x')];
console.log(JSON.stringify(out));"""
        r = subprocess.run(["node", "-e", js], capture_output=True, text=True, env=dict(os.environ, TZ="Europe/Berlin"), timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), ["2026-10-25T02:30:00+02:00", "2026-10-25T02:30:00+01:00",
                                                "2026-10-25T02:30:00+01:00", "2026-10-25T02:40:00+02:00", ""])


if __name__ == "__main__":
    unittest.main()
