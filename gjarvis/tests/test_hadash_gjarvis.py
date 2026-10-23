"""GJarvis: Dashboard-Vorlage für Home Assistant (ohne echtes Home Assistant)."""
import os, sys, tempfile, unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
os.environ["GJARVIS_DATA"] = tempfile.mkdtemp()
import yaml  # noqa: E402
import web  # noqa: E402


class Vorlage(unittest.TestCase):
    def setUp(self):
        os.environ.pop("SUPERVISOR_TOKEN", None); os.environ.pop("HADASH_TOKEN", None)
        web.HADASH_FILE = Path(os.environ["GJARVIS_DATA"]) / "hadash.json"

    def test_vorschau_und_datenschutz(self):
        r = web.hadash_state()
        cfg = yaml.safe_load(r["yaml"])
        heads = [c["heading"] for s in cfg["views"][0]["sections"] for c in s["cards"] if c["type"] == "heading"]
        self.assertIn("Steuerung", heads)
        self.assertNotIn("Letztes Gespräch", heads)          # was Jarvis verstanden hat: nur wenn ausdrücklich gewählt
        cfg = web.hadash_config(web.hadash_clean({"parts": ["gespraech"]}), web.HADASH_GUESS)
        self.assertEqual(cfg["views"][0]["sections"][0]["cards"][0]["heading"], "Letztes Gespräch")

    def test_stopp_drueckt_knopf(self):
        cfg = web.hadash_config(web.hadash_clean({"parts": ["steuerung"]}), web.HADASH_GUESS)
        stop = [c for c in cfg["views"][0]["sections"][0]["cards"] if c.get("entity") == "button.gjarvis_stopp"][0]
        self.assertEqual(stop["tap_action"]["perform_action"], "button.press")


if __name__ == "__main__":
    unittest.main()
