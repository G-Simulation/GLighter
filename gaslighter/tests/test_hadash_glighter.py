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


class Blocktakt(unittest.TestCase):
    """Ton kommt in Schüben (wie am Server-Mikrofon beobachtet: alle ~15 s 1,3 s auf einmal)."""

    def run_clock(self, arrivals):
        st, out = None, []
        for b in arrivals:
            st = laerm.block_clock(st, b); out.append(st[0])
        return out

    def test_schuebe_erzeugen_keine_luecke(self):
        arr = []
        for i in range(3000):                          # 5 Minuten
            t = 1000 + i * 0.1
            lag = 0.03
            k = i % 150
            if k < 13:                                  # Schub: 13 Blöcke hängen und kommen dann zusammen
                lag = (13 - k) * 0.1 + 0.05
            arr.append(t + lag)
        ts = self.run_clock(arr)
        d = [b - a for a, b in zip(ts, ts[1:])]
        self.assertLess(max(d), 0.3)                   # keine scheinbare Lücke
        self.assertGreater(min(d), 0.0)
        true = [1000 + i * 0.1 for i in range(3000)]
        self.assertLess(max(abs(a - b) for a, b in zip(ts[100:], true[100:])), 0.5)

    def test_echte_luecke_bleibt_luecke(self):
        arr = [1000 + i * 0.1 + 0.03 for i in range(200)] + [1000 + i * 0.1 + 5.03 for i in range(200, 400)]   # 5 s Ton fehlen
        ts = self.run_clock(arr)
        self.assertLess(abs(ts[-1] - arr[-1]), 0.3)    # danach wieder an der echten Zeit

    def test_neustart_sofort(self):
        ts = self.run_clock([1000.0, 1000.1, 1100.0, 1100.1])
        self.assertAlmostEqual(ts[2], 1100.0)
