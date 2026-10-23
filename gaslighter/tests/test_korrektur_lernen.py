"""Ab 1.84.0: „Korrekturen lernen mit“ – von Hand korrigierte Geräuscharten werden Beispiele, ähnliche Störungen bekommen
diese Art als Vorschlag. Nur berechnet: art.json, bestaetigt.json und log.csv bleiben unverändert. Dazu Tabellen-Einstellungen in layout.json."""
import base64, copy, json, os, sys, tempfile, unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import laerm  # noqa: E402

BANDS = laerm.lernen.TERZ


def graph(peak_band, lvl=-20.0, n=40):
    """Kleine Ereignisgrafik: Hintergrund, in der Mitte 1 s laut mit Schwerpunkt auf einem Terzband."""
    recs = []
    for i in range(n):
        on = 15 <= i < 25
        sp = np.full(len(BANDS), 2 * (-90 + 130), np.uint8)
        if on:
            for j in range(len(BANDS)):
                sp[j] = int(2 * (max(-90, lvl - 6 * abs(j - peak_band)) + 130))
        recs.append([i * 100, lvl if on else -60.0, -60.0, None, 1 if on else 0, base64.b64encode(sp.tobytes()).decode()])
    return {"recs": recs, "bands": BANDS, "step": 100}


class KorrekturenLernen(unittest.TestCase):
    def setUp(self):
        self.keep = {k: getattr(laerm, k) for k in ("art_all", "best_all", "kl_rows", "_event_data")}
        self.cfg = dict(laerm.CFG)
        self.ART = {"a": {"g": "music", "c": 60}, "b": {"g": "music", "c": 55}, "c": {"g": "music", "c": 50}}
        self.BEST = {"a": {}}
        self.G = {"a": graph(3), "b": graph(3, -22.0), "c": graph(19)}       # b ähnlich wie a (tief), c ganz anders (hoch)
        laerm.art_all = lambda: self.ART
        laerm.best_all = lambda: self.BEST
        laerm.kl_rows = lambda: [({"start": f"2026-10-0{i + 1}T10:00:00", "quelle_id": "main"}, 0, d) for i, d in enumerate("abc")]
        laerm._event_data = lambda r, n: (self.G[next(d for rr, nn, d in laerm.kl_rows() if rr["start"] == r["start"])], None, "x")
        laerm.KL.update(sig=None, sug={}, pc={})
        laerm.CFG["ki_learn_fix"] = True; laerm.CFG["ki_learn_min"] = 75

    def tearDown(self):
        for k, v in self.keep.items():
            setattr(laerm, k, v)
        laerm.CFG.clear(); laerm.CFG.update(self.cfg); laerm.KL.update(sig=None, sug={}, pc={})

    def test_ohne_korrektur_kein_vorschlag(self):
        laerm.kl_step()
        self.assertEqual(laerm.art_fields("b")["art"], "music"); self.assertNotIn("art_lern", laerm.art_fields("b"))

    def test_korrektur_wird_vorschlag_fuer_aehnliche(self):
        before = copy.deepcopy(self.ART)
        self.ART["a"]["man"] = "knock"; before["a"]["man"] = "knock"     # Korrektur von Hand (wie art_set_manual)
        laerm.kl_step()
        f = laerm.art_fields("b")
        self.assertEqual(f["art"], "knock"); self.assertGreaterEqual(f["art_lern"], 75); self.assertEqual(f["art_lki"], "music")
        self.assertEqual(laerm.art_fields("c")["art"], "music")           # nicht ähnlich: Erkennung bleibt
        self.assertTrue(laerm.art_fields("a")["art_man"]); self.assertNotIn("art_lern", laerm.art_fields("a"))
        self.assertIn("Korrekturen", laerm.art_text(f, True))
        self.assertEqual(self.ART, before)                                # gespeicherte Arten unverändert
        laerm.CFG["ki_learn_fix"] = False                                 # Ausschalten: sofort wieder wie vorher
        self.assertEqual(laerm.art_fields("b")["art"], "music")
        laerm.CFG["ki_learn_fix"] = True; laerm.CFG["ki_learn_min"] = 98
        self.assertTrue(laerm.art_fields("b").get("art_lern") is None or laerm.art_fields("b")["art_lern"] >= 98)

    def test_bestaetigung_mit_anderer_art_zaehlt(self):
        self.BEST["a"]["a"] = {"g": "door", "ki": "music"}
        laerm.kl_step()
        self.assertEqual(laerm.art_fields("b")["art"], "door")
        self.BEST["a"]["a"] = {"g": "music", "ki": "music"}               # nur bestätigt: kein Beispiel
        laerm.kl_step()
        self.assertNotIn("art_lern", laerm.art_fields("b"))

    def test_einstellungen_gueltig(self):
        self.assertTrue(laerm.DEFAULTS["ki_learn_fix"]); self.assertEqual(laerm.DEFAULTS["ki_learn_min"], 75)


class TabellenLayout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.keep = laerm.LAYOUT_FILE
        laerm.LAYOUT_FILE = os.path.join(self.tmp, "layout.json"); laerm.LAYOUT["data"] = None

    def tearDown(self):
        laerm.LAYOUT_FILE = self.keep; laerm.LAYOUT["data"] = None

    def test_reihenfolge_ausblenden_dichte(self):
        j = laerm.layout_change({"tbl": {"live_ev": {"order": ["dur", "start", "x y", "dur"], "hide": ["bg"], "dense": "compact"}, "a/b": {"order": []}}})
        self.assertEqual(j["layout"]["tbl"], {"live_ev": {"order": ["dur", "start"], "hide": ["bg"], "dense": "compact"}})
        laerm.LAYOUT["data"] = None
        self.assertEqual(laerm.layout_public()["layout"]["tbl"]["live_ev"]["order"], ["dur", "start"])
        laerm.layout_change({"tbl": {"live_ev": None}})                    # „Spalten zurücksetzen“
        self.assertEqual(laerm.layout_public()["layout"]["tbl"], {})
        laerm.layout_change({"tbl": {"prot_ev": {"order": ["src"], "hide": [], "dense": "laut"}}})
        self.assertEqual(laerm.layout_public()["layout"]["tbl"]["prot_ev"], {"order": ["src"], "hide": []})
        laerm.layout_change({"reset": "cols"})
        self.assertEqual(laerm.layout_public()["layout"]["tbl"], {})
        with open(laerm.LAYOUT_FILE, encoding="utf-8") as f:
            self.assertIn("tbl", json.load(f))


if __name__ == "__main__":
    unittest.main()
