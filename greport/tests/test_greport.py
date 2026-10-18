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

    def test_home_assistant_felder_und_speichern(self):
        k = G.qt_change({"action": "add", "l": "Waschmaschine", "g": "kind"})["k"]
        e = G.qt_change({"action": "add", "l": "Nachbar B"})["k"]
        grp = G.qt_groups()
        self.assertIn((k, "Waschmaschine"), grp["kind"])                 # eigene Taste in ihrer Gruppe
        self.assertIn((e, "Nachbar B"), grp["own"])
        self.assertEqual(G.group_opts(grp["lvl"])[0], G.NONE_OPT)
        G.mqtt_cmd("greport/notiz/set", "Bass dröhnt")
        G.mqtt_cmd("greport/was/set", "Waschmaschine")
        G.mqtt_cmd("greport/woher/set", "oben")
        G.mqtt_cmd("greport/wie_stark/set", "gibt es nicht")              # unbekannt = ignoriert
        G.mqtt_cmd("greport/zeuge/set", "Anna")
        r = G.mqtt_cmd("greport/speichern/set", "PRESS")
        self.assertTrue(r["ok"]); n = r["note"]
        self.assertEqual(n["text"], "Bass dröhnt"); self.assertEqual(n["witness"], "Anna"); self.assertEqual(n["by"], "homeassistant")
        self.assertEqual(set(n["tags"]), {"oben", k, "zeuge"})
        self.assertEqual((G.FORM["text"], G.FORM["witness"], G.FORM["pick"]["kind"]), ("", "", G.NONE_OPT))   # Felder geleert
        self.assertEqual(G.mqtt_cmd("greport/speichern/set", "PRESS")["error"], "empty")              # leer: nichts gespeichert
        s = G.notes_summary()
        self.assertEqual(s["today"], 1); self.assertIn("Bass dröhnt", s["last"])
        self.assertEqual(s["attr"]["notizen"][0]["zeuge"], "Anna"); self.assertIn("Waschmaschine", s["attr"]["notizen"][0]["woerter"])

    def test_home_assistant_entitaeten(self):
        sent = {}

        class C:
            def publish(self, t, p, retain=False):
                sent[t] = p

            def subscribe(self, *_):
                pass
        G.MQ["c"] = C()
        try:
            G.qt_change({"action": "add", "l": "Waschmaschine"})
            G.mqtt_announce(G.MQ["c"])
            cfg = {t.split("/")[1] + "." + t.split("/")[3]: json.loads(p) for t, p in sent.items() if t.endswith("/config") and p}
            for e in ("text.notiz", "text.zeuge", "button.speichern", "sensor.letzte_notiz", "sensor.notizen_heute",
                      "select.woher", "select.was", "select.wie_stark", "select.folgen", "select.massnahmen", "select.eigene",
                      "select.schnellwahl", "button.hinzufuegen"):
                self.assertIn(e, cfg)
            self.assertEqual(cfg["select.eigene"]["options"], [G.NONE_OPT, "Waschmaschine"])
            self.assertEqual(cfg["sensor.letzte_notiz"]["json_attributes_topic"], "greport/notizen/attr")
            G.note_change("add", {"text": "Test"})
            self.assertEqual(sent["greport/notizen_heute"], "1")
            self.assertEqual(json.loads(sent["greport/notizen/attr"])["notizen"][0]["text"], "Test")
        finally:
            G.MQ["c"] = None

    def test_woerter_umbenennen_anordnen(self):
        G.qt_change({"action": "ren", "k": "musik", "l": "Bass"})
        self.assertEqual(G.tag_label("musik"), "Bass")
        k = G.qt_change({"action": "add", "l": "Waschmaschine", "g": "kind"})["k"]
        self.assertEqual(G.qt_state()["grp"][k], "kind")
        G.qt_change({"action": "order", "keys": ["unten", "oben", k]})
        vis = [x for x, _ in G.qt_visible()]
        self.assertEqual(vis[:3], ["unten", "oben", k])         # feste Reihenfolge auch in Home Assistant
        self.assertIn("Bass", [l for _, l in G.qt_visible()])
        G.qt_change({"action": "reset"})
        st = G.qt_state(); self.assertEqual(st["ren"], {}); self.assertEqual(st["mode"], "use"); self.assertEqual(st["grp"][k], "kind")   # eigene bleiben

    def test_gruppenfarbe(self):
        self.assertEqual(G.qt_change({"action": "gcol", "g": "src", "c": "#FF8800"})["gcol"], {"src": "#ff8800"})
        self.assertEqual(G.qt_change({"action": "gcol", "g": "src", "c": ""})["gcol"], {})
        self.assertFalse(G.qt_change({"action": "gcol", "g": "xyz", "c": "#000000"})["ok"])

    def test_pflicht_gruppen(self):
        self.assertEqual(G.qt_change({"action": "req", "g": "src", "on": True})["req"], ["src"])
        self.assertEqual(G.qt_change({"action": "req", "g": "src", "on": False})["req"], [])
        self.assertTrue(G.note_change("add", {"text": "trotzdem"})["ok"])     # gespeichert wird immer

    def test_pro_anzahl(self):
        self.assertEqual(G.qt_change({"action": "limit", "n": 80})["error"], "pro")
        G.pro_ok = lambda: True
        self.assertEqual(G.qt_change({"action": "limit", "n": 80})["limit"], 80)
        self.assertEqual(G.qt_change({"action": "limit", "n": 9999})["limit"], 200)
        self.assertEqual(G.qt_change({"action": "show", "n": 4})["show"], 4)
        G.pro_ok = lambda: False
        self.assertEqual(G.qt_state()["show"], 0); self.assertEqual(G.own_max(), 5)   # ohne Pro: alles zeigen, 5 eigene

    def test_datum_uhrzeit(self):
        d = G.dt.datetime(2026, 10, 18, 5, 7, 9)
        self.assertEqual(G.fmt_date(d, dict(G.PREF_DEF)), "18.10.2026")
        self.assertEqual(G.fmt_date(d, dict(G.PREF_DEF, date="iso", wd=True)), "So. 2026-10-18")
        self.assertEqual(G.fmt_time(d, dict(G.PREF_DEF, time="hm")), "05:07")
        self.assertEqual(G.fmt_time(d, dict(G.PREF_DEF, time="h12")), "5:07:09 AM")
        self.assertEqual(G.prefs_set({"date": "long", "time": "bogus"})["date"], "long")
        self.assertEqual(G.prefs()["time"], "hms")

    def test_tagebuch_und_import(self):
        G.pro_ok = lambda: True
        G.TXT_ROOTS[:] = [D]
        G.note_change("add", {"tags": ["klopfen", "oben"], "text": "Bass", "witness": "Anna", "from": "2026-10-18T05:07:12"})
        G.note_change("add", {"tags": ["schritte"], "from": "2026-10-18T05:15:08"})
        G.note_change("add", {"text": "Tür knallt", "from": "2026-10-17T23:41:10", "to": "2026-10-17T23:45:00"})
        path = os.path.join(G.DIR, "tagebuch.txt")
        self.assertTrue(G.txt_set({"on": True, "path": path})["ok"])
        txt = open(path, encoding="utf-8").read()
        self.assertIn("Sa. 17.10.2026\n23:41:10 – 23:45:00  Tür knallt\n\nSo. 18.10.2026\n05:07:12  [Klopfen, oben] Bass – Zeuge: Anna\n05:15:08  [Schritte]", txt)
        self.assertEqual(G.txt_set({"path": "/etc/passwd.txt"})["error"], "path")          # nur unter /share oder /media
        # zurücklesen: alles schon da
        r = G.import_text({"content": txt})
        self.assertEqual((r["new"], r["dup"]), (0, 3))
        # andere Datei mit neuem Wort
        r = G.import_text({"content": "Mo. 19.10.2026\n22:10  [Waschmaschine, stark] schleudert – Zeuge: Bert\n"}, apply=True)
        self.assertEqual((r["applied"], r["words"]), (1, ["Waschmaschine"]))
        n = G.notes_list(q="schleudert")[0]
        self.assertIn("stark", n["tags"]); self.assertEqual(n["witness"], "Bert"); self.assertIn("Waschmaschine", n["tagl"])
        # CSV-Export einlesen
        r = G.import_text({"content": G.export_text("csv")})
        self.assertEqual(r["new"], 0)
        e = G.export_file({"fmt": "json", "path": os.path.join(G.DIR, "x.json")}); self.assertTrue(e["ok"])
        self.assertEqual(G.import_text({"path": e["path"]})["dup"], 4)
        G.txt_set({"monthly": True}); G.diary_write()
        self.assertTrue(os.path.exists(os.path.join(G.DIR, "tagebuch_2026-10.txt")))

    def test_ingress_ueber_ipv6(self):
        self.assertIn(G.client_ip("::ffff:172.30.32.2"), G.ALLOWED)
        self.assertNotIn(G.client_ip("::ffff:192.168.1.5"), G.ALLOWED)

    def test_schluessel_beide_produkte(self):
        self.assertIn("gaslighter", G.lizenz.PRODUCTS); self.assertIn("greport", G.lizenz.PRODUCTS)
        self.assertEqual(G.lizenz.check("GL1-AAAAA")["state"], "invalid")


if __name__ == "__main__":
    unittest.main()
