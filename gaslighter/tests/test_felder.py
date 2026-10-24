"""Eigene Felder der Notiz-Erfassung in GLighter (felder.py, gleiche Datei wie in GReport): Definitionen in layout.json (cap.blocks),
Werte je freie Notiz in „fields“, Export, Vorlagen, Zähler. Alte Notizen ohne „fields“ bleiben unverändert."""
import csv, io, json, os, sys, tempfile, unittest
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import laerm  # noqa: E402
import felder as F  # noqa: E402

NUM = {"id": "b_00000a", "type": "number", "l": "Gewicht", "unit": "kg", "max": 500}
CNT = {"id": "b_00000c", "type": "counter", "l": "Feuerzeug", "mode": "entry"}
PER = {"id": "b_000012", "type": "person", "l": "Zeuge 2"}


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); out = os.path.join(self.tmp, "out")
        self.keep = (laerm.LAYOUT_FILE, laerm.paths, laerm.fnote_target, laerm.GR_DIR)
        laerm.LAYOUT_FILE = os.path.join(self.tmp, "layout.json"); laerm.LAYOUT["data"] = None
        laerm.paths = lambda: (out, out + "/clips", out + "/log.csv")
        laerm.NOTES["data"] = None; laerm.QT["data"] = None
        laerm.fnote_target = lambda *a, **k: None
        laerm.GR_DIR = os.path.join(self.tmp, "kein_greport")

    def tearDown(self):
        laerm.LAYOUT_FILE, laerm.paths, laerm.fnote_target, laerm.GR_DIR = self.keep
        laerm.LAYOUT["data"] = None; laerm.NOTES["data"] = None; laerm.QT["data"] = None

    def felder(self, defs):
        j = laerm.layout_change({"cap": {"blocks": defs}}); self.assertTrue(j["ok"]); return j

    def csv_rows(self):
        return list(csv.reader(io.StringIO(laerm.notes_csv({}).decode("utf-8").lstrip("﻿"))))


class GleicheDatei(unittest.TestCase):
    def test_felder_py_wie_in_greport(self):
        other = os.path.join(HERE, "..", "..", "greport", "app", "felder.py")
        if not os.path.exists(other):
            self.skipTest("GReport liegt nicht daneben")
        for a, b in (("felder.py", other), (os.path.join("web", "felder.js"), os.path.join(HERE, "..", "..", "greport", "app", "web", "felder.js"))):
            with open(os.path.join(HERE, "..", "app", a), "rb") as x, open(b, "rb") as y:
                self.assertEqual(x.read(), y.read(), a)


class Felder(Basis):
    def test_ohne_felder_wie_bisher(self):
        laerm.fnote_change("add", {"text": "Bass", "tags": ["musik"], "from": "2026-10-20T22:00:00"})
        self.assertEqual(self.csv_rows()[0], ["datum", "uhrzeit", "offset_s", "ungefaehr", "ruhezeit", "ereignis_start", "quelle", "datei", "dauer_s",
                                              "spitze_dbfs_relativ", "ki_art", "tags", "zeuge", "notiz", "erstellt"])
        self.assertNotIn("fields", laerm.notes_all()["free"][0])
        st = laerm.felder_state(); self.assertEqual((st["tpl"], [(b["type"], b.get("bind")) for b in st["blocks"]]), ("laerm", [("person", "witness")]))   # ab 1.85: Zeuge als Standard-Feld
        self.assertNotIn("blocks", laerm.layout_public()["layout"]["cap"])

    def test_speichern_pruefen_export(self):
        self.felder([NUM, CNT, PER])
        r = laerm.fnote_change("add", {"from": "2026-10-20T22:00:00", "fields": {"b_00000a": "2,5", "b_000012": {"n": "Anna", "r": "polizei"}}})
        self.assertTrue(r["ok"], r); self.assertEqual(r["note"]["fields"], {"b_00000a": 2.5, "b_000012": {"n": "Anna", "r": "polizei"}})
        bad = laerm.fnote_change("add", {"text": "x", "from": "2026-10-20T22:00:00", "fields": {"b_00000a": 501}})
        self.assertEqual((bad["error"], bad["fields"]), ("field", ["b_00000a"]))
        nid = r["note"]["id"]
        laerm.fnote_change("edit", {"id": nid, "text": "dazu", "from": "2026-10-20T22:00:00"})          # Dialog ohne Felder: Werte bleiben
        self.assertEqual(laerm.notes_all()["free"][0]["fields"]["b_00000a"], 2.5)
        rows = self.csv_rows(); h = rows[0]
        self.assertEqual(h[-3:], ["Gewicht [kg] (b_00000a)", "Feuerzeug (b_00000c)", "Zeuge 2 (b_000012)"])
        row = dict(zip(h, rows[1])); self.assertEqual(row["Gewicht [kg] (b_00000a)"], "2,5"); self.assertEqual(row["Zeuge 2 (b_000012)"], "Anna; Polizei")
        self.assertEqual(laerm.fnote_fx(laerm.notes_all()["free"][0]), "Gewicht: 2,5 kg; Zeuge 2: Anna (Polizei)")
        laerm.fnote_change("edit", {"id": nid, "text": "dazu", "from": "2026-10-20T22:00:00", "fields": {}})
        self.assertNotIn("fields", laerm.notes_all()["free"][0])

    def test_definitionen_gehen_nie_verloren(self):
        self.felder([NUM, CNT])
        self.felder([dict(NUM, l="Neu")])                                            # CNT fehlt → bleibt
        ids = [b["id"] for b in laerm.cap_defs()]; self.assertEqual(ids, ["b_00000a", "b_00000c"])
        self.felder([dict(CNT, **{"del": True})])
        self.assertTrue(F.by_id(laerm.cap_defs())["b_00000c"]["del"]); self.assertNotIn("del", F.by_id(laerm.cap_defs())["b_00000a"])
        laerm.layout_change({"reset": "cap"})                                          # Standard: Felder bleiben
        self.assertEqual(len(laerm.cap_defs()), 2)
        laerm.layout_change({"cap": {"blocks": [dict(NUM, type="text")]}})                # Art ändert sich nie
        self.assertEqual(F.by_id(laerm.cap_defs())["b_00000a"]["type"], "number")

    def test_vorlage_und_zaehler(self):
        laerm.fnote_change("add", {"text": "Bass", "from": "2026-10-20T22:00:00"})
        before = json.dumps(laerm.notes_all()["free"])
        r = laerm.cap_tpl("zaehler"); self.assertTrue(r["ok"])
        c = [b for b in laerm.cap_defs() if b["type"] == "counter"]; self.assertEqual(len(c), 1)
        cap = laerm.layout_public()["layout"]["cap"]
        self.assertEqual(cap["tpl"], "zaehler"); self.assertEqual(cap["order"], [c[0]["id"], "time"]); self.assertEqual(cap["hide"], ["txt", "tags", "wit"])
        now = dt.datetime.now().isoformat(timespec="seconds")
        for _ in range(2):
            self.assertTrue(laerm.fnote_change("add", {"from": now, "fields": {c[0]["id"]: 1}})["ok"])
        st = laerm.felder_state(); self.assertEqual(st["counts"][c[0]["id"]], 2); self.assertEqual(st["daily"][c[0]["id"]][-1][1], 2)
        laerm.cap_tpl("allg")
        self.assertTrue(laerm.cap_defs()[0]["hide"]); self.assertEqual(laerm.qt_x("gren").get("own"), "Stichworte")
        laerm.cap_tpl("laerm")
        self.assertNotIn("own", laerm.qt_x("gren")); self.assertEqual(laerm.layout_public()["layout"]["cap"]["hide"], [])
        self.assertEqual(json.dumps(laerm.notes_all()["free"][:1]), json.dumps(json.loads(before)))
        self.assertFalse(laerm.cap_tpl("boese")["ok"])

    def test_vorlage_in_sprache_der_oberflaeche(self):
        keep = laerm.CFG.get("language"); laerm.CFG["language"] = "de"              # Server deutsch, Oberfläche englisch
        try:
            laerm.cap_tpl("zaehler", "en")
            self.assertEqual([b["l"] for b in laerm.cap_defs() if b["type"] == "counter"], ["Counter"])
            laerm.cap_tpl("allg", "en"); self.assertEqual(laerm.qt_x("gren").get("own"), "Keywords")
        finally:
            laerm.CFG["language"] = keep

    def test_greport_felder_werden_gelesen(self):
        os.makedirs(laerm.GR_DIR)
        with open(os.path.join(laerm.GR_DIR, "notizen.json"), "w", encoding="utf-8") as f:
            json.dump({"free": [{"id": "r_1", "from": "2026-10-20T22:00:00+02:00", "text": "", "tags": [], "fields": {"b_00000a": 3}}]}, f)
        with open(os.path.join(laerm.GR_DIR, "felder.json"), "w", encoding="utf-8") as f:
            json.dump({"blocks": [NUM]}, f)
        keep = laerm.pro_ok; laerm.pro_ok = lambda: True
        try:
            ns = laerm.gr_notes()
        finally:
            laerm.pro_ok = keep
        if not ns:
            self.skipTest("GReport-Notizen werden hier nicht gelesen")
        self.assertEqual(ns[0]["fx"], ["Gewicht: 3 kg"]); self.assertEqual(ns[0]["text"], "Gewicht: 3 kg")


if __name__ == "__main__":
    unittest.main()


class ArtNichtZuordnen(unittest.TestCase):
    """GReport-Notiz mit Art „nicht zuordnen“ hängt GLighter an keine Störung."""
    def test_fn_assign_ueberspringt(self):
        import laerm as L
        rows = [{"start": "2026-10-20T22:00:00", "dauer_s": "2", "quelle_id": "main", "k": "K1"}]
        a = int(L.ms_of("2026-10-20T22:01:00")); keep = L.na_ovr; L.na_ovr = lambda: {}
        try:
            n1 = {"id": "g1", "a": a, "b": a, "src": "all", "gr": True}
            n2 = dict(n1, id="g2", noassign=True)
            r = L.fn_assign([n1, n2], rows)
        finally:
            L.na_ovr = keep
        ks = [k for k in r]
        self.assertEqual(len(ks), 1)
