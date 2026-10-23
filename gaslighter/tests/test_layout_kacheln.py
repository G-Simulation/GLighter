"""Layout-Designer (layout.json) und Kacheln (eigene Statistiken als Sensoren in Home Assistant).
Nur Anzeige und Lesen: gespeicherte Daten bleiben unverändert."""
import datetime as dt, json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import laerm  # noqa: E402
import yaml  # noqa: E402


class LayoutSpeichern(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.keep = (laerm.LAYOUT_FILE, dict(laerm.CFG), laerm.paths)
        laerm.LAYOUT_FILE = os.path.join(self.tmp, "layout.json"); laerm.LAYOUT["data"] = None
        out = os.path.join(self.tmp, "out")
        laerm.paths = lambda: (out, out + "/clips", out + "/log.csv")   # eigener Wegwerf-Ordner (andere Tests ersetzen paths)

    def tearDown(self):
        laerm.LAYOUT_FILE = self.keep[0]; laerm.LAYOUT["data"] = None; laerm.CFG.clear(); laerm.CFG.update(self.keep[1]); laerm.paths = self.keep[2]

    def test_leer_ohne_datei(self):
        j = laerm.layout_public()
        self.assertTrue(j["ok"]); self.assertFalse(j["exists"]); self.assertEqual(j["layout"]["views"], {})

    def test_speichern_und_laden(self):
        v = {"lay": [{"id": "ldev", "x": 0, "y": 0, "w": 6}, {"id": "st_s_1234abcd", "x": 6, "y": 0, "w": 6}], "col": {"ldev": True},
             "off": ["fn"], "vis": {}, "ttl": {"ldev": "Meine Tabelle"}}
        j = laerm.layout_change({"views": {"live": v}, "cols": {"live_ev": {"start": 140, "peak": 90}}})
        self.assertTrue(j["ok"]); self.assertTrue(os.path.exists(laerm.LAYOUT_FILE))
        laerm.LAYOUT["data"] = None                       # neu von der Platte
        lo = laerm.layout_public()["layout"]
        self.assertEqual(lo["views"]["live"]["lay"][1], {"id": "st_s_1234abcd", "x": 6, "y": 0, "w": 6})
        self.assertEqual(lo["views"]["live"]["ttl"], {"ldev": "Meine Tabelle"}); self.assertEqual(lo["views"]["live"]["off"], ["fn"])
        self.assertEqual(lo["cols"]["live_ev"], {"start": 140, "peak": 90})
        laerm.layout_change({"cols": {"live_ev": {"peak": 120}}})          # Spaltenbreiten werden ergänzt
        self.assertEqual(laerm.layout_public()["layout"]["cols"]["live_ev"], {"start": 140, "peak": 120})
        laerm.layout_change({"reset": "live"})
        self.assertNotIn("live", laerm.layout_public()["layout"]["views"])
        laerm.layout_change({"reset": "cols"})
        self.assertEqual(laerm.layout_public()["layout"]["cols"], {})

    def test_pruefung(self):
        bad = {"lay": [{"id": "a b", "x": 0, "y": 0, "w": 3}, {"id": "ok", "x": 20, "y": 0, "w": 3}, {"id": "ok2", "x": 10, "y": 5, "w": 12},
                       {"id": "ok2", "x": 0, "y": 0, "w": 1}, "quatsch"],
               "col": {"x": "ja", "y": True}, "off": ["fn", "fn", 5, "<b>"], "ttl": {"z": "<script>x</script>" + "x" * 100, "q": 7}}
        j = laerm.layout_change({"views": {"live": bad, "fremd": {"lay": []}}, "cols": {"t": {"c": 5, "d": "x", "e": 99999, "f": 200}, "a/b": {"c": 100}}})
        lv = j["layout"]["views"]["live"]
        self.assertEqual(lv["lay"], [{"id": "ok2", "x": 10, "y": 5, "w": 2}])     # Breite passt in die 12 Spalten
        self.assertEqual(lv["col"], {"y": True}); self.assertEqual(lv["off"], ["fn"])
        self.assertNotIn("<", lv["ttl"]["z"]); self.assertLessEqual(len(lv["ttl"]["z"]), 60); self.assertNotIn("q", lv["ttl"])
        self.assertNotIn("fremd", j["layout"]["views"])
        self.assertEqual(j["layout"]["cols"], {"t": {"f": 200}})
        self.assertFalse(laerm.layout_change({"reset": "alles"})["ok"])
        self.assertFalse(laerm.layout_change([1, 2])["ok"])

    def test_sicherung_enthaelt_layout(self):
        laerm.layout_change({"views": {"prot": {"lay": [{"id": "ev", "x": 0, "y": 0, "w": 12}]}}})
        self.assertIn(("data/layout.json", laerm.LAYOUT_FILE), laerm.backup_items())
        laerm.layout_change({"reset": "prot"})
        self.assertTrue(laerm.layout_restore({"views": {"prot": {"lay": [{"id": "ev", "x": 0, "y": 3, "w": 8}]}}, "cols": {"prot_ev": {"start": 150}}}))
        lo = laerm.layout_public()["layout"]
        self.assertEqual(lo["views"]["prot"]["lay"][0]["w"], 8); self.assertEqual(lo["cols"]["prot_ev"]["start"], 150)


class KachelnRechnen(unittest.TestCase):
    """Kacheln: neue Darstellungen, Zeitraum, Schwellen; Vorlagen frei, eigene mit Pro; Sensor für Home Assistant."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.keep = (dict(laerm.CFG), laerm.pro_ok, laerm.read_log, laerm.sensor_events, laerm.art_fields, laerm.LAYOUT_FILE, laerm.pub, laerm.mq, laerm.paths)
        laerm.CFG.update(output_dir=self.tmp, clip_dir="", language="de"); laerm.STAT["data"] = None
        laerm.paths = lambda: (self.tmp, self.tmp + "/clips", self.tmp + "/log.csv")
        laerm.LAYOUT_FILE = os.path.join(self.tmp, "layout.json"); laerm.LAYOUT["data"] = None
        base = dt.datetime(2026, 10, 12, 23, 30)
        rows = []
        for i, (h, pk, du) in enumerate([(0, -20.0, 2.0), (0.5, -10.0, 30.0), (12, -30.0, 5.0), (49, -25.0, 1.0)]):
            t = base + dt.timedelta(hours=h)
            rows.append({"start": t.isoformat(timespec="seconds"), "dauer_s": str(du), "spitze_dbfs": str(pk), "hintergrund_dbfs": "-60", "datei": f"c{i}",
                         "schwelle_dbfs": "-40", "clip_s": "", "quelle": "Mic", "quelle_id": "main"})
        self.rows = rows
        laerm.read_log = lambda: rows
        laerm.sensor_events = lambda *a: []
        laerm.art_fields = lambda f: {"art": "knock" if f in ("c0", "c1") else "steps", "prof": "", "bg": False}
        self.a = int(dt.datetime(2026, 10, 12).timestamp() * 1000); self.b = int(dt.datetime(2026, 10, 16).timestamp() * 1000)
        self.sent = []
        laerm.pub = lambda topic, payload, retain=False: self.sent.append((topic, payload, retain))

    def tearDown(self):
        laerm.CFG.clear(); laerm.CFG.update(self.keep[0])
        laerm.pro_ok, laerm.read_log, laerm.sensor_events, laerm.art_fields, laerm.LAYOUT_FILE, laerm.pub, laerm.mq, laerm.paths = self.keep[1:]
        laerm.STAT["data"] = None; laerm.LAYOUT["data"] = None; laerm.TILES["conf"].clear(); laerm.TILES["last"].clear()

    def test_schwellen_filtern(self):
        j = laerm.stat_compute({"src": "ev", "metric": "n", "by": "none", "min_pk": -22}, self.a, self.b)
        self.assertEqual(j["total"], 2)                                       # -20 und -10
        j = laerm.stat_compute({"src": "ev", "metric": "n", "by": "none", "min_dur": 5}, self.a, self.b)
        self.assertEqual(j["total"], 2)                                       # 30 s und 5 s
        j = laerm.stat_compute({"src": "ev", "metric": "dur", "by": "none", "min_pk": -22, "min_dur": 5}, self.a, self.b)
        self.assertAlmostEqual(j["total"], 30.0, delta=0.5)

    def test_neue_felder_pruefen(self):
        d = laerm.stat_clean({"show": "list", "range": "custom", "from_d": "2026-10-20", "to_d": "2026-10-01", "min_pk": "abc", "min_dur": -5, "top": 99})
        self.assertEqual((d["show"], d["range"], d["from_d"], d["to_d"]), ("list", "custom", "2026-10-01", "2026-10-20"))
        self.assertIsNone(d["min_pk"]); self.assertIsNone(d["min_dur"]); self.assertEqual(d["top"], 20)
        self.assertEqual(laerm.stat_clean({"range": "custom"})["range"], "7")       # ohne Daten: letzte 7 Tage
        self.assertEqual(laerm.stat_clean({"show": "quatsch"})["show"], "bar")

    def test_zeitraum_ohne_browser(self):
        now = int(dt.datetime(2026, 10, 15, 10, 0).timestamp() * 1000)
        a, b = laerm.tile_range({"range": "today"}, now)
        self.assertEqual(dt.datetime.fromtimestamp(a / 1000).hour, 0); self.assertGreater(b, now)
        a, b = laerm.tile_range({"range": "sel"}, now); self.assertEqual(dt.datetime.fromtimestamp(a / 1000).date(), dt.date(2026, 10, 15))
        a, b = laerm.tile_range({"range": "7"}, now); self.assertEqual(now - a, 7 * 86400000)
        a, b = laerm.tile_range({"range": "custom", "from_d": "2026-10-12", "to_d": "2026-10-13"}, now)
        self.assertEqual(b - a, 2 * 86400000)

    def test_wert_und_attribute(self):
        d = laerm.stat_clean({"src": "ev", "metric": "n", "by": "art", "show": "list", "range": "custom", "from_d": "2026-10-12", "to_d": "2026-10-15", "top": 3})
        st, att = laerm.tile_value(d)
        self.assertEqual(st, 4)
        self.assertEqual([x["name"] for x in att["eintraege"]], ["Klopfen/Schlag", "Schritte"])
        d = laerm.stat_clean({"src": "ev", "metric": "pk_max", "by": "day", "show": "line", "range": "custom", "from_d": "2026-10-12", "to_d": "2026-10-15"})
        st, att = laerm.tile_value(d)
        self.assertEqual(st, -10.0); self.assertEqual(att["verlauf"][0][0], "12.10."); self.assertEqual(len(att["verlauf"]), 4)

    def test_vorlagen_frei_eigene_pro(self):
        laerm.pro_ok = lambda: False
        self.assertEqual(laerm.stat_change({"action": "add", "def": {"show": "num"}})["error"], "pro")
        j = laerm.stat_change({"action": "add", "tpl": "week_n", "view": "prot"}); self.assertTrue(j["ok"])
        k = j["id"]; d = next(x for x in j["list"] if x["id"] == k)
        self.assertEqual((d["view"], d["show"], d["range"]), ("prot", "num", "7"))
        self.assertEqual(laerm.stat_change({"action": "edit", "id": k, "def": {"show": "list"}})["error"], "pro")
        j = laerm.stat_change({"action": "add", "tpl": "today", "view": "prot"})        # „heute“ bleibt heute
        self.assertEqual(next(x for x in j["list"] if x["id"] == j["id"])["range"], "today")
        self.assertTrue(laerm.stat_change({"action": "del", "id": k})["ok"])            # Löschen geht immer

    def test_mqtt_discovery(self):
        laerm.pro_ok = lambda: True
        laerm.mq = object()
        k = laerm.stat_change({"action": "add", "def": {"name": "Klopfen nachts", "src": "ev", "metric": "dur", "by": "none", "show": "num", "range": "7"}})["id"]
        laerm.layout_change({"views": {"live": {"ttl": {"st_" + k: "Nachts"}}}})
        self.sent.clear()
        laerm.tiles_publish(force=True)
        conf = [json.loads(p) for t, p, r in self.sent if t == f"homeassistant/sensor/{laerm.HAID}/tile_{k}/config"]
        self.assertEqual(len(conf), 1); c = conf[0]
        self.assertEqual(c["unique_id"], f"{laerm.HAID}_tile_{k}"); self.assertEqual(c["name"], "Nachts")
        self.assertEqual(c["unit_of_measurement"], "s"); self.assertEqual(c["device_class"], "duration")
        self.assertEqual(c["state_topic"], f"{laerm.TOPIC}/tile/{k}"); self.assertEqual(c["json_attributes_topic"], f"{laerm.TOPIC}/tile/{k}/attr")
        self.assertTrue(all(r for t, p, r in self.sent))                                 # alles mit retain
        self.assertTrue(any(t == f"{laerm.TOPIC}/tile/{k}" for t, p, r in self.sent))
        self.sent.clear(); laerm.tiles_publish()
        self.assertEqual(self.sent, [])                                                    # nichts geändert: nichts senden
        self.assertEqual(laerm.layout_all()["ha_tiles"], [k])
        laerm.stat_change({"action": "del", "id": k}); self.sent.clear(); laerm.tiles_publish()
        self.assertIn((f"homeassistant/sensor/{laerm.HAID}/tile_{k}/config", "", True), self.sent)   # gelöscht: Entität entfernen
        self.assertEqual(laerm.layout_all()["ha_tiles"], [])

    def test_dashboard_vorlage_kacheln(self):
        laerm.pro_ok = lambda: True
        ids = {}
        for show in ("num", "line", "bar", "list", "table"):
            ids[show] = laerm.stat_change({"action": "add", "def": {"name": show, "src": "ev", "metric": "n", "by": "art" if show in ("list", "table") else "day", "show": show, "range": "7"}})["id"]
        d = laerm.hadash_clean({"parts": ["kacheln"]})
        cfg = laerm.hadash_config(d, laerm.HADASH_GUESS())
        cards = cfg["views"][0]["sections"][0]["cards"]
        types = [c["type"] for c in cards]
        self.assertEqual(types[0], "heading")
        self.assertIn("tile", types); self.assertIn("statistics-graph", types); self.assertIn("history-graph", types); self.assertEqual(types.count("markdown"), 2)
        md = [c for c in cards if c["type"] == "markdown"]
        self.assertTrue(all(f"sensor.{laerm.HAID}_tile_" in c["content"] and "eintraege" in c["content"] for c in md))
        yaml.safe_load(laerm.hadash.to_yaml(cfg))
        self.assertIn("kacheln", laerm.HADASH_PARTS)


if __name__ == "__main__":
    unittest.main()


class NotizErfassungAnpassen(unittest.TestCase):
    """Notiz-Erfassung wie GReport: eigene Rubriken/Tasten (schnellwahl.json) und Aussehen (layout.json „cap“), nur für GLighter."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); out = os.path.join(self.tmp, "out"); os.makedirs(out + "/clips")
        self.keep = (laerm.LAYOUT_FILE, laerm.paths)
        laerm.LAYOUT_FILE = os.path.join(self.tmp, "layout.json"); laerm.LAYOUT["data"] = None
        laerm.paths = lambda: (out, out + "/clips", out + "/log.csv"); laerm.QT["data"] = None

    def tearDown(self):
        laerm.LAYOUT_FILE, laerm.paths = self.keep; laerm.LAYOUT["data"] = None; laerm.QT["data"] = None

    def test_cap_pruefen_und_zuruecksetzen(self):
        j = laerm.layout_change({"cap": {"title": "<b>Meine</b> Notiz", "clock": "small", "dense": "x", "order": ["wit", "txt", "quatsch", "wit"], "hide": ["tags"]}})
        c = j["layout"]["cap"]
        self.assertEqual(c["title"], "bMeine/b Notiz"); self.assertEqual(c["clock"], "small"); self.assertEqual(c["dense"], "normal")
        self.assertEqual(c["order"], ["wit", "txt"]); self.assertEqual(c["hide"], ["tags"])
        laerm.layout_change({"cap": {"style": "filled"}})                    # nur geänderte Felder
        self.assertEqual(laerm.layout_public()["layout"]["cap"]["clock"], "small")
        laerm.layout_change({"reset": "cap"})
        self.assertEqual(laerm.layout_public()["layout"]["cap"]["clock"], "big")

    def test_rubriken_tasten_batch(self):
        j = laerm.qt_change({"action": "batch", "ops": [{"action": "gadd", "g": "g_abcdef", "l": "Nachbarn"}, {"action": "add", "k": "c_123456", "l": "Party", "g": "g_abcdef"},
                                                         {"action": "ren", "k": "oben", "l": "von oben"}, {"action": "grp", "k": "hund", "g": "src"}, {"action": "gcol", "g": "lvl", "c": "#2B8A3E"},
                                                         {"action": "req", "g": "kind", "on": True}, {"action": "gorder", "groups": ["lvl", "src"]}, {"action": "unsinn"}]})
        self.assertEqual(len(j["errors"]), 1)
        self.assertEqual(j["grp"], {"c_123456": "g_abcdef", "hund": "src"}); self.assertEqual(j["ren"], {"oben": "von oben"})
        self.assertEqual(j["gcol"], {"lvl": "#2b8a3e"}); self.assertEqual(j["req"], ["kind"])
        self.assertEqual([g["g"] for g in j["gall"]][:2], ["lvl", "src"]); self.assertIn({"g": "g_abcdef", "l": "Nachbarn", "custom": True, "hide": False, "renamed": False}, j["gall"])
        self.assertEqual(laerm.tag_label("oben"), "von oben")
        j = laerm.qt_change({"action": "gdel", "g": "g_abcdef"})
        self.assertNotIn("c_123456", j["grp"]); self.assertTrue(any(o["k"] == "c_123456" and not o["del"] for o in j["own"]))   # Taste bleibt, kommt nach „Eigene“
        j = laerm.qt_change({"action": "reset"})
        self.assertEqual((j["ren"], j["gcol"], j["req"], j["mode"]), ({}, {}, [], "use")); self.assertEqual(laerm.tag_label("oben"), "oben")
