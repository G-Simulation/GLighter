"""GReport: Dashboard-Vorlage für Home Assistant (ohne echtes Home Assistant)."""
import json, os, sys, tempfile, unittest

D = tempfile.mkdtemp()
os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import greport as G  # noqa: E402
import hadash  # noqa: E402
import yaml  # noqa: E402


def cards(cfg):
    for s in cfg["views"][0]["sections"]:
        for c in s["cards"]:
            yield c


class Vorlage(unittest.TestCase):
    def setUp(self):
        os.environ.pop("SUPERVISOR_TOKEN", None); os.environ.pop("HADASH_TOKEN", None)
        if os.path.exists(G.hadash_file()):
            os.remove(G.hadash_file())

    def test_vorschau_ohne_home_assistant(self):
        r = G.hadash_state()
        self.assertFalse(r["available"]); self.assertEqual(r["prefs"]["url"], "gsim-greport")
        cfg = yaml.safe_load(r["yaml"])
        self.assertEqual(cfg["views"][0]["type"], "sections")
        types = [c["type"] for c in cards(cfg)]
        self.assertIn("custom:greport-card", types); self.assertIn("markdown", types)
        self.assertTrue(all(c is not None and c.get("type") for c in cards(cfg)))

    def test_ohne_karte_einzelne_felder(self):
        cfg = G.hadash_config(G.hadash_clean({"parts": ["karte"]}), G.hadash_guess(), card=False)
        ent = [c for c in cards(cfg) if c["type"] == "entities"][0]
        self.assertEqual(ent["entities"][0]["entity"], "text.greport_notiz")
        self.assertTrue(any(c.get("tap_action", {}).get("perform_action") == "button.press" for c in cards(cfg)))

    def test_anlegen_merkt_sich_auswahl_und_fragt_bei_vorhandenem(self):
        from unittest import mock
        calls = []
        with mock.patch.object(hadash, "entity_map", lambda p: {"greport_notiz": "text.greport_notiz", "greport_letzte_notiz": "sensor.greport_letzte_notiz"}), \
                mock.patch.object(G, "hadash_card_ready", lambda: True), \
                mock.patch.object(hadash, "install", lambda *a, **k: calls.append(a) or ({"ok": False, "exists": True} if not a[-1] else {"ok": True, "created": False})):
            self._apply(calls)

    def _apply(self, calls):
        r = G.hadash_apply({"title": "Notizen", "url": "gsim-notizen", "parts": ["letzte"]})
        self.assertTrue(r.get("exists"))
        self.assertEqual(json.load(open(G.hadash_file()))["url"], "gsim-notizen")
        self.assertTrue(G.hadash_apply({"overwrite": True})["ok"])
        self.assertEqual(calls[-1][0], "gsim-notizen")
        self.assertEqual(G.hadash_apply({"url": "ohne"})["error"], "bad_url")


if __name__ == "__main__":
    unittest.main()
