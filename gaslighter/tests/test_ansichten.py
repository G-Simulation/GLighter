"""GLighter ab 1.83.2: zwei Ansichten der Notiz-Erfassung – angedockt („cap“ in layout.json, wie bisher) und abgedockt
(„cap_pop“). Nur Anzeige: alte layout.json bleibt gültig, Zurücksetzen/Vorlage/Sicherung nehmen die abgedockte Ansicht mit."""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import laerm  # noqa: E402


class Ansichten(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.keep = (laerm.LAYOUT_FILE, laerm.paths, laerm.tiles_kick)
        laerm.LAYOUT_FILE = os.path.join(self.tmp, "layout.json"); laerm.LAYOUT["data"] = None
        out = os.path.join(self.tmp, "out")
        laerm.paths = lambda: (out, out + "/clips", out + "/log.csv")
        laerm.tiles_kick = lambda: None

    def tearDown(self):
        laerm.LAYOUT_FILE, laerm.paths, laerm.tiles_kick = self.keep; laerm.LAYOUT["data"] = None

    def lay(self):
        return laerm.layout_public()["layout"]

    def test_alte_datei_ohne_abgedockt(self):
        with open(laerm.LAYOUT_FILE, "w") as f:          # Stand 1.83.1
            json.dump({"v": 1, "views": {}, "cols": {}, "cap": {"order": ["wit", "txt"], "hide": ["time"], "dense": "compact"}}, f)
        lo = self.lay()
        self.assertIsNone(lo["cap_pop"]); self.assertEqual(lo["cap"]["order"], ["wit", "txt"]); self.assertEqual(lo["cap"]["hide"], ["time"])

    def test_abgedockt_eigen_angedockt_bleibt(self):
        laerm.layout_change({"cap": {"order": ["tags", "txt"], "hide": ["wit"]}})
        j = laerm.layout_change({"cap_pop": {"order": ["time", "x<y", "txt", "time"], "hide": ["tags", "b_abc123", "zzz"], "ghide": ["kind", "a/b"],
                                             "clock": "small", "dense": "compact", "style": "bunt", "egal": 1}})
        cp = j["layout"]["cap_pop"]
        self.assertEqual(cp, {"order": ["time", "txt"], "hide": ["tags", "b_abc123"], "ghide": ["kind"], "clock": "small", "dense": "compact"})
        self.assertEqual(j["layout"]["cap"]["order"], ["tags", "txt"]); self.assertEqual(j["layout"]["cap"]["hide"], ["wit"])
        laerm.layout_change({"cap": {"hide": []}})                                       # angedockt ändern: abgedockt bleibt
        self.assertEqual(self.lay()["cap_pop"], cp)
        laerm.LAYOUT["data"] = None; self.assertEqual(self.lay()["cap_pop"], cp)       # auch nach Neustart
        laerm.layout_change({"cap_pop": None}); self.assertIsNone(self.lay()["cap_pop"])  # wie angedockt übernehmen
        laerm.layout_change({"cap_pop": {"dense": "compact"}}); laerm.layout_change({"reset": "cap_pop"}); self.assertIsNone(self.lay()["cap_pop"])

    def test_standard_und_vorlage_setzen_abgedockt_zurueck(self):
        laerm.layout_change({"cap_pop": {"hide": ["txt"]}}); laerm.layout_change({"reset": "cap"})
        self.assertIsNone(self.lay()["cap_pop"])
        laerm.layout_change({"cap_pop": {"hide": ["txt"]}})
        keep = (laerm.qt_save, laerm.felder_state, laerm.qt_state)
        try:
            laerm.qt_save = lambda: None; laerm.felder_state = lambda: {"ok": True}; laerm.qt_state = lambda: {}
            laerm.cap_tpl("allg", "de")
        finally:
            laerm.qt_save, laerm.felder_state, laerm.qt_state = keep
        self.assertIsNone(self.lay()["cap_pop"])

    def test_sicherung_mit_abgedockt(self):
        laerm.layout_change({"cap": {"order": ["wit"]}, "cap_pop": {"dense": "compact"}})
        with open(laerm.LAYOUT_FILE) as f:
            raw = json.load(f)
        self.assertEqual(raw["cap_pop"]["dense"], "compact")
        laerm.layout_change({"cap_pop": None})
        self.assertTrue(laerm.layout_restore(raw)); self.assertEqual(self.lay()["cap_pop"]["dense"], "compact")
        self.assertTrue(laerm.layout_restore({"cap": {"order": ["txt"]}})); self.assertIsNone(self.lay()["cap_pop"])   # Sicherung ohne: folgt angedockt


if __name__ == "__main__":
    unittest.main()
