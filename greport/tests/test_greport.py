"""GReport: Notizen, Schnellwahl, Pro-Grenzen, Home Assistant (Auswahlliste + Knopf)."""
import json, os, shutil, sys, tempfile, unittest

D = tempfile.mkdtemp()
os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import greport as G  # noqa: E402


class Notizen(unittest.TestCase):
    def setUp(self):
        G.NOTES["data"] = None; G.QT["data"] = None
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)
        G.pro_ok = lambda: False

    def test_anlegen_aendern_loeschen(self):
        r = G.note_change("add", {"tags": ["klopfen", "oben"], "text": "Bass", "witness": "Anna"})
        self.assertTrue(r["ok"]); n = r["note"]
        self.assertIn("zeuge", n["tags"])                        # Zeuge eingetragen = Taste „Zeuge anwesend“
        self.assertEqual(json.load(open(os.path.join(G.DIR, "notizen.json")))["free"][0]["id"], n["id"])
        self.assertTrue(G.note_change("edit", {"id": n["id"], "text": "Musik", "from": n["from"]})["ok"])
        self.assertEqual(G.notes_list(q="musik")[0]["id"], n["id"])
        self.assertTrue(G.note_change("del", {"id": n["id"]})["ok"])
        self.assertEqual(G.notes_list(), []); self.assertEqual(len(G.notes_all()["trash"]), 1)

    def test_leer_und_bis(self):
        self.assertEqual(G.note_change("add", {"text": " "})["error"], "empty")
        self.assertEqual(G.note_change("add", {"text": "x", "from": "2026-10-18T03:00:00", "to": "2026-10-18T02:00:00"})["error"], "to")

    def test_mehrere_zeugen_nur_pro(self):
        self.assertEqual(G.note_change("add", {"text": "x", "witness": "Anna, Bert"})["note"]["witness"], "Anna")
        G.pro_ok = lambda: True
        self.assertEqual(G.note_change("add", {"text": "x", "witness": "Anna, Bert"})["note"]["witness"], "Anna, Bert")

    def test_eigene_tasten_grenze(self):
        for i in range(5):
            self.assertTrue(G.qt_change({"action": "add", "l": f"Taste {i}"})["ok"])
        self.assertEqual(G.qt_change({"action": "add", "l": "zu viel"})["error"], "limit_free")
        G.pro_ok = lambda: True
        self.assertTrue(G.qt_change({"action": "add", "l": "zu viel"})["ok"])

    def test_export_import_pro(self):
        self.assertEqual(G.notes_import({"notes": []})["error"], "pro")
        G.pro_ok = lambda: True
        r = G.notes_import({"notes": [{"id": "r_x1", "from": "2026-10-18T01:00:00+02:00", "text": "alt"}, {"id": "r_x1", "from": "2026-10-18T01:00:00+02:00", "text": "doppelt"}]})
        self.assertEqual(r["n"], 1)
        self.assertIn("alt", G.export_csv().decode("utf-8"))

    def test_home_assistant_knopf(self):
        k = G.qt_change({"action": "add", "l": "Waschmaschine"})["k"]
        labels = [l for _, l in G.qt_visible()]
        self.assertIn("Waschmaschine", labels)
        G.mqtt_cmd("greport/schnellwahl/set", "Waschmaschine")
        r = G.mqtt_cmd("greport/hinzufuegen/set", "PRESS")
        self.assertTrue(r["ok"]); self.assertEqual(r["note"]["tags"], [k]); self.assertEqual(r["note"]["by"], "homeassistant")
        G.qt_change({"action": "hide", "k": "klopfen", "on": True})
        self.assertNotIn("Klopfen", [l for _, l in G.qt_visible()])  # ausgeblendet = auch nicht in Home Assistant

    def test_schluessel_beide_produkte(self):
        self.assertIn("gaslighter", G.lizenz.PRODUCTS); self.assertIn("greport", G.lizenz.PRODUCTS)
        self.assertEqual(G.lizenz.check("GL1-AAAAA")["state"], "invalid")


if __name__ == "__main__":
    unittest.main()
