"""GReport ab 1.10.2: zwei Ansichten von „Notiz jetzt“ – angedockt (Einstellungen wie bisher) und abgedockt („pop“),
Schnell-Schalter je Ansicht (sechide / sechide_pop), alte Einstellungsdateien bleiben gültig, Sicherung enthält beides."""
import io, json, os, shutil, sys, tempfile, unittest, zipfile

D = tempfile.mkdtemp()
os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import greport as G  # noqa: E402


def pfile():
    return os.path.join(G.DIR, "einstellungen.json")


class Ansichten(unittest.TestCase):
    def setUp(self):
        G.NOTES["data"] = None; G.QT["data"] = None; G.PROTO["state"] = None
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)

    def test_alte_datei_ohne_ansichten(self):
        with open(pfile(), "w") as f:                    # Stand 1.10.1: nur angedockt
            json.dump({"date": "iso", "width": "narrow", "tipmode": "always", "cap_order": ["wit", "txt"], "txt": {"on": True}}, f)
        p = G.prefs()
        self.assertEqual((p["width"], p["tipmode"], p["dens"]), ("narrow", "always", "normal"))
        self.assertNotIn("pop", p); self.assertNotIn("sechide", p); self.assertNotIn("sechide_pop", p)
        self.assertEqual(p["cap_order"][:2], ["wit", "txt"])

    def test_abgedockt_eigene_ansicht_und_zurueck(self):
        G.prefs_set({"cap_order": ["tags", "txt"], "tipmode": "hover"})
        p = G.prefs_set({"pop": {"cap_order": ["time", "txt", "bogus", "time"], "hide": ["wit", "b_abc123", "x<y"], "ghide": ["kind", "g_1a2b3c", "<b>"],
                                 "tipmode": "off", "dens": "compact", "egal": 1}})
        pop = G.prefs()["pop"]
        self.assertEqual(pop["cap_order"], ["time", "txt", "tags", "wit", "more"])
        self.assertEqual(pop["hide"], ["wit", "b_abc123"]); self.assertEqual(pop["ghide"], ["kind", "g_1a2b3c"])
        self.assertEqual((pop["tipmode"], pop["dens"]), ("off", "compact")); self.assertNotIn("egal", pop)
        self.assertEqual(p["cap_order"][:2], ["tags", "txt"]); self.assertEqual(p["tipmode"], "hover")    # angedockt unverändert
        G.prefs_set({"cap_order": ["more", "txt"], "dens": "compact"})                                     # angedockt ändern
        self.assertEqual(G.prefs()["pop"], pop)                                                            # abgedockt unverändert
        self.assertEqual(G.prefs()["dens"], "compact")
        G.prefs_set({"pop": None})                                                                          # „wie angedockt übernehmen“
        self.assertNotIn("pop", G.prefs())
        with open(pfile()) as f:
            self.assertNotIn("pop", json.load(f))

    def test_teilweise_ansicht_ohne_fehlende_werte(self):
        p = G.prefs_set({"pop": {"tipmode": "nope", "dens": "huge"}})
        self.assertEqual(p["pop"], {"hide": [], "ghide": []})                  # fehlende Werte folgen in der App der angedockten Ansicht
        with open(pfile()) as f:
            d = json.load(f)
        d["pop"] = "kaputt"
        with open(pfile(), "w") as f:
            json.dump(d, f)
        self.assertNotIn("pop", G.prefs())

    def test_schnellschalter_je_ansicht(self):
        p = G.prefs_set({"sechide": ["more", "wit", "more", "zzz"]})               # übernommen aus gr_sechide (Browser)
        self.assertEqual(p["sechide"], ["more", "wit"]); self.assertNotIn("sechide_pop", p)
        p = G.prefs_set({"sechide_pop": ["tags"]}); self.assertEqual((p["sechide"], p["sechide_pop"]), (["more", "wit"], ["tags"]))
        p = G.prefs_set({"sechide_pop": None}); self.assertNotIn("sechide_pop", p); self.assertEqual(p["sechide"], ["more", "wit"])
        p = G.prefs_set({"sechide": []}); self.assertEqual(p["sechide"], [])     # leer bleibt gesetzt (keine zweite Übernahme)

    def test_vorlage_setzt_abgedockt_zurueck(self):
        G.prefs_set({"pop": {"hide": ["txt"]}})
        G.fb_change({"action": "tpl", "tpl": "zaehler", "lang": "de"})
        self.assertNotIn("pop", G.prefs())

    def test_sicherung_enthaelt_ansichten(self):
        G.prefs_set({"pop": {"dens": "compact"}, "sechide": ["more"]})
        bio = io.BytesIO(); G.backup_write(bio, files=False)
        with zipfile.ZipFile(bio) as z:
            d = json.loads(z.read("einstellungen.json"))
        self.assertEqual(d["pop"]["dens"], "compact"); self.assertEqual(d["sechide"], ["more"])


if __name__ == "__main__":
    unittest.main()
