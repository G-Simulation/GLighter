"""GLighter: Dashboard-Vorlage für Home Assistant (ohne echtes Home Assistant)."""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import laerm  # noqa: E402
import yaml  # noqa: E402


class Vorlage(unittest.TestCase):
    def test_vorschau_alle_bereiche(self):
        os.environ.pop("SUPERVISOR_TOKEN", None); os.environ.pop("HADASH_TOKEN", None)
        r = laerm.hadash_state()
        cfg = yaml.safe_load(r["yaml"])
        cs = [c for s in cfg["views"][0]["sections"] for c in s["cards"]]
        self.assertTrue(all(c.get("type") for c in cs))
        self.assertIn("history-graph", [c["type"] for c in cs])
        self.assertTrue(any(c.get("entity") == "text.gaslighter_note" for e in cs for c in e.get("entities", []) if isinstance(c, dict)))

    def test_nur_gewaehlte_bereiche(self):
        d = laerm.hadash_clean({"parts": ["ruhe"], "title": "Ruhe"})
        cfg = laerm.hadash_config(d, laerm.HADASH_GUESS())
        self.assertEqual(cfg["title"], "Ruhe"); self.assertEqual(len(cfg["views"][0]["sections"]), 1)


if __name__ == "__main__":
    unittest.main()
