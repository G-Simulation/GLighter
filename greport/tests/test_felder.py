"""Eigene Felder (felder.py, felder.json): Prüfen der Definitionen und Werte, Speichern je Notiz in „fields“,
Export (CSV, Tagebuch, JSON, Bericht), Einlesen, Vorlagen, Zähler. Alte Notizen ohne „fields“ bleiben unverändert."""
import csv, io, json, os, shutil, sys, tempfile, unittest
import datetime as dt

D = tempfile.mkdtemp()
os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import greport as G  # noqa: E402
import felder as F  # noqa: E402

CNT = {"id": "b_00000c", "type": "counter", "l": "Feuerzeug", "mode": "entry"}
NUM = {"id": "b_00000a", "type": "number", "l": "Gewicht", "unit": "kg", "min": 0, "max": 500}
YN = {"id": "b_00000b", "type": "yesno", "l": "Polizei da"}
SEL = {"id": "b_00000d", "type": "select", "l": "Raum", "opts": ["Küche", "Bad"], "multi": True}
SC = {"id": "b_00000e", "type": "scale", "l": "Stärke", "rng": "10", "lo": "leise", "hi": "laut"}
DUR = {"id": "b_00000f", "type": "duration", "l": "Dauer"}
DTB = {"id": "b_000010", "type": "datetime", "l": "Beginn"}
PL = {"id": "b_000011", "type": "place", "l": "Ort"}
PER = {"id": "b_000012", "type": "person", "l": "Zeuge 2"}
TX = {"id": "b_000013", "type": "text", "l": "Kennzeichen"}
ALL = [CNT, NUM, YN, SEL, SC, DUR, DTB, PL, PER, TX]


class Modul(unittest.TestCase):
    """felder.py allein (gleiche Datei in GLighter)."""
    def test_definitionen(self):
        self.assertIsNone(F.clean_def({"id": "x", "type": "text"}))
        self.assertIsNone(F.clean_def({"id": "b_123456", "type": "zauber"}))
        d = F.clean_def({"id": "b_123456", "type": "number", "l": "<b>Gewicht</b>\n", "min": "5", "max": "2", "col": "#ABCDEF", "req": True, "hide": "ja", "boese": 1})
        self.assertEqual(d["l"], "bGewicht/b"); self.assertEqual(d["min"], 5); self.assertNotIn("max", d)    # max < min fällt weg
        self.assertEqual(d["col"], "#abcdef"); self.assertTrue(d["req"]); self.assertNotIn("hide", d); self.assertNotIn("boese", d)
        old = F.clean_def({"id": "b_123456", "type": "number", "l": "A", "ts": "2026-01-01T00:00:00+01:00"})
        d2 = F.clean_def({"id": "b_123456", "type": "text", "l": "B"}, old)                 # Art und Anlagedatum ändern sich nie
        self.assertEqual((d2["type"], d2["ts"], d2["l"]), ("number", "2026-01-01T00:00:00+01:00", "B"))
        s = F.clean_def({"id": "b_aaaaaa", "type": "select", "opts": ["a", "a", "", "b"] + ["x%d" % i for i in range(40)]})
        self.assertEqual(s["opts"][:3], ["a", "b", "x0"]); self.assertEqual(len(s["opts"]), 30)

    def test_text_und_datum_einstellbar(self):
        d = F.clean_def({"id": "b_111111", "type": "text", "ph": "z. B. Nachbar", "max": "80", "sug": True, "rows": 4})
        self.assertEqual((d["ph"], d["max"], d.get("sug"), d.get("rows")), ("z. B. Nachbar", 80, True, None))   # Zeilen nur mehrzeilig
        d = F.clean_def({"id": "b_111111", "type": "text", "ml": True, "rows": 6, "sug": True, "max": 5})
        self.assertEqual((d["ml"], d["rows"], d.get("sug"), d.get("max")), (True, 6, None, None))               # Vorschläge nur einzeilig, max < 10 fällt weg
        self.assertEqual(F.clean_value({"type": "text", "max": 10}, "x" * 50), (True, "x" * 10))
        k = F.clean_def({"id": "b_222222", "type": "datetime", "kind": "time", "def": "now", "nonow": True, "sec": True})
        self.assertEqual((k["kind"], k["def"], k["nonow"], k["sec"]), ("time", "now", True, True))
        self.assertNotIn("sec", F.clean_def({"id": "b_222222", "type": "datetime", "kind": "date", "sec": True}))
        self.assertNotIn("kind", F.clean_def({"id": "b_222222", "type": "datetime", "kind": "quatsch"}))
        self.assertEqual(F.clean_value({"type": "datetime", "kind": "time"}, "07:30"), (True, "07:30"))
        self.assertEqual(F.clean_value({"type": "datetime", "kind": "time"}, "25:00"), (False, None))
        self.assertEqual(F.clean_value({"type": "datetime", "kind": "date"}, "2026-10-24"), (True, "2026-10-24"))
        self.assertEqual(F.clean_value({"type": "datetime", "kind": "date"}, "2026-02-30"), (False, None))
        ok, v = F.clean_value({"type": "datetime"}, "2026-10-24T08:15:00+02:00"); self.assertTrue(ok and v.startswith("2026-10-24T08:15"))   # wie bisher

    def test_definitionen_gehen_nie_verloren(self):
        old, _ = F.clean_defs([CNT, NUM], [])
        new, errs = F.clean_defs([dict(NUM, l="Gewicht neu")], old)                         # CNT fehlt in der Liste → bleibt
        self.assertEqual([b["id"] for b in new], ["b_00000a", "b_00000c"]); self.assertEqual(new[0]["l"], "Gewicht neu"); self.assertEqual(errs, [])
        many = [{"id": "b_%06x" % i, "type": "text", "l": str(i)} for i in range(F.MAX_ACTIVE + 3)]
        out, errs = F.clean_defs(many, [])
        self.assertEqual(sum(1 for b in out if not b.get("del")), F.MAX_ACTIVE); self.assertEqual(len(errs), 3)
        self.assertTrue(all(e.endswith(":limit") for e in errs))

    def test_werte(self):
        b = F.by_id(F.clean_defs(ALL, [])[0])
        ok = lambda k, v: F.clean_value(b[k], v)
        self.assertEqual(ok("b_00000a", "12,5"), (True, 12.5)); self.assertEqual(ok("b_00000a", "600"), (False, None)); self.assertEqual(ok("b_00000a", "x"), (False, None))
        self.assertEqual(ok("b_00000b", "ja"), (True, True)); self.assertEqual(ok("b_00000b", False), (True, False)); self.assertEqual(ok("b_00000b", "vielleicht"), (False, None))
        self.assertEqual(ok("b_00000c", 1), (True, 1)); self.assertEqual(ok("b_00000c", 1.5), (False, None)); self.assertEqual(ok("b_00000c", True), (False, None))
        self.assertEqual(ok("b_00000d", ["Küche", "Küche", "Bad"]), (True, ["Küche", "Bad"]))
        self.assertEqual(ok("b_00000e", 0), (True, 0)); self.assertEqual(ok("b_00000e", 11), (False, None))
        self.assertEqual(ok("b_00000f", "90"), (True, 90)); self.assertEqual(ok("b_00000f", -1), (False, None))
        self.assertEqual(ok("b_000010", "2026-10-20T22:00:00Z"), (True, "2026-10-20T22:00:00+00:00")); self.assertFalse(ok("b_000010", "gestern")[0])
        self.assertEqual(ok("b_000012", {"n": "Anna", "r": "nachbar", "c": "0171", "x": 1}), (True, {"n": "Anna", "r": "nachbar", "c": "0171"}))
        self.assertEqual(ok("b_000012", {"n": " ", "r": "nachbar"}), (True, None)); self.assertEqual(ok("b_000012", "Bert"), (True, {"n": "Bert"}))
        self.assertEqual(ok("b_000013", "a\nb"), (True, "a b")); self.assertEqual(ok("b_000013", ""), (True, None))
        fv, bad = F.clean_fields(list(b.values()), {"b_00000a": "3", "b_ffffff": "x", "b_00000c": "zwei", "b_000013": ""})
        self.assertEqual(fv, {"b_00000a": 3}); self.assertEqual(bad, ["b_00000c"])
        self.assertEqual(F.clean_fields(ALL, None), ({}, []))

    def test_anzeige_und_csv(self):
        defs = F.clean_defs(ALL, [])[0]; b = F.by_id(defs)
        self.assertEqual(F.fmt(b["b_00000a"], 12.5), "12,5 kg"); self.assertEqual(F.fmt(b["b_00000a"], 12.5, de=False), "12.5 kg")
        self.assertEqual(F.fmt(b["b_00000c"], -1), "−1"); self.assertEqual(F.fmt(b["b_00000e"], 7), "7/10")
        self.assertEqual(F.fmt(b["b_00000f"], 125), "2 h 05 min"); self.assertEqual(F.fmt(b["b_00000b"], True, de=False), "yes")
        self.assertEqual(F.fmt(b["b_000012"], {"n": "Anna", "r": "nachbar"}), "Anna (Nachbar)")
        self.assertEqual(F.csv_head(b["b_00000a"]), "Gewicht [kg] (b_00000a)"); self.assertEqual(F.head_id("Gewicht [kg] (b_00000a)"), "b_00000a")
        self.assertIsNone(F.head_id("datum"))
        vals = {"b_00000a": 12.5, "b_00000b": True, "b_00000c": 1, "b_00000d": ["Küche", "Bad"], "b_00000e": 3, "b_00000f": 90,
                "b_000010": "2026-10-20T22:00:00+02:00", "b_000011": "Flur", "b_000012": {"n": "Anna", "r": "nachbar", "c": "0171"}, "b_000013": "AB 12"}
        for k, v in vals.items():                                                            # CSV-Zelle → Wert → gleich
            self.assertEqual(F.from_raw(b[k], F.raw(b[k], v)), v, k)
        self.assertEqual(F.compact_txt(defs, {"b_00000a": 2, "b_000011": "Flur"}), "Gewicht: 2 kg; Ort: Flur")
        dl = dict(defs[1], **{"del": True}); self.assertEqual(F.compact([dl], {"b_00000a": 2}), [("Gewicht", "2 kg")])   # gelöscht: Wert bleibt lesbar
        self.assertEqual(F.csv_defs([dl], []), []); self.assertEqual(F.csv_defs([dl], [{"fields": {"b_00000a": 1}}]), [dl])
        self.assertEqual(F.compact(defs, None), [])

    def test_zaehler(self):
        d0 = dt.date(2026, 10, 20); ms = lambda d, h: int(dt.datetime(d.year, d.month, d.day, h).timestamp() * 1000)
        ns = [{"a": ms(d0, 9), "fields": {"b_00000c": 1}}, {"a": ms(d0, 10), "fields": {"b_00000c": 1}},
              {"a": ms(d0 - dt.timedelta(days=1), 9), "fields": {"b_00000c": -1}}, {"a": ms(d0, 11)}, {"a": ms(d0, 12), "fields": {"b_00000c": True}}]
        self.assertEqual(F.counter_sum(ns, "b_00000c"), 1); self.assertEqual(F.counter_sum(ns, "b_00000c", ms(d0, 0)), 2)
        dl = F.daily(ns, "b_00000c", days=3, today=d0)
        self.assertEqual(dl, [["2026-10-18", 0], ["2026-10-19", -1], ["2026-10-20", 2]])
        self.assertEqual(F.suggestions([{"a": 2, "fields": {"p": "Flur"}}, {"a": 1, "fields": {"p": "Bad"}}, {"a": 3, "fields": {"p": "Flur"}}], "p"), ["Flur", "Bad"])
        self.assertTrue(F.BID.match(F.new_id({"b_000001"}, lambda: "000002")))


class Basis(unittest.TestCase):
    def setUp(self):
        G.NOTES["data"] = None; G.QT["data"] = None; G.PROTO["state"] = None; G.FB["data"] = None; G.ATT["data"] = None
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)
        self.keep = (G.mqtt_announce, G.pro_ok, G.pub, G.mqtt_form_state)
        G.mqtt_announce = lambda *a, **k: None; G.pro_ok = lambda: True

    def tearDown(self):
        G.mqtt_announce, G.pro_ok, G.pub, G.mqtt_form_state = self.keep

    def felder(self, defs=ALL):
        r = G.fb_change({"action": "set", "blocks": defs}); self.assertTrue(r["ok"]); return r


class AlteNotizen(Basis):
    def test_ohne_felder_export_wie_bisher(self):
        G.note_change("add", {"text": "Bass", "tags": ["musik"], "from": "2026-10-20T22:00:00+02:00"})
        head = next(csv.reader(io.StringIO(G.export_csv().decode("utf-8").lstrip("﻿")), delimiter=";"))
        self.assertEqual(head, ["datum", "von", "bis", "schnellwahl", "text", "zeuge", "von_iso", "bis_iso", "geschrieben", "kennung", "erfasst_iso",
                                "zeit_per_taste", "ungefaehr", "geaendert"] + G.EXT_COLS)
        txt = G.export_text("txt"); self.assertNotIn("{", txt)
        rb = G.report_build(); self.assertEqual(rb["vorfaelle"][0]["felder"], []); self.assertEqual(rb["zusammenfassung"]["zaehler"], [])
        self.assertNotIn("fields", G.notes_all()["free"][0])
        self.assertEqual(G.fb_state()["tpl"], "laerm")                                  # vorhandene Daten: wie bisher (Lärm), kein Vorlagen-Angebot
        self.assertFalse(G.fb_state()["first"])

    def test_alte_datei_ohne_fields_laedt(self):
        G.write_json(G.notes_path(), {"free": [{"id": "r_alt", "from": "2026-01-01T10:00:00+01:00", "to": "", "text": "alt", "tags": []}], "trash": []})
        G.NOTES["data"] = None; self.felder([NUM])
        n = G.notes_list()[0]; self.assertEqual(n["text"], "alt"); self.assertNotIn("fields", n)
        rows = list(csv.reader(io.StringIO(G.export_csv().decode("utf-8").lstrip("﻿")), delimiter=";"))
        self.assertEqual(rows[0][-1], "Gewicht [kg] (b_00000a)"); self.assertEqual(rows[1][-1], "")
        self.assertTrue(G.proto_verify()["ok"])

    def test_erster_start(self):
        self.assertTrue(G.fb_state()["first"]); self.assertIsNone(G.fb_state()["tpl"])


class Speichern(Basis):
    def test_notiz_mit_feldern(self):
        self.felder()
        r = G.note_change("add", {"from": "2026-10-20T22:00:00+02:00", "fields": {"b_00000a": "12,5", "b_00000b": "ja", "b_000012": {"n": "Anna", "r": "nachbar"}}})
        self.assertTrue(r["ok"], r)                                                      # nur Felder, kein Text: gültig
        x = G.notes_all()["free"][0]; self.assertEqual(x["fields"], {"b_00000a": 12.5, "b_00000b": True, "b_000012": {"n": "Anna", "r": "nachbar"}})
        bad = G.note_change("add", {"text": "x", "from": "2026-10-20T22:00:00+02:00", "fields": {"b_00000a": "999"}})
        self.assertEqual((bad["ok"], bad["error"], bad["fields"]), (False, "field", ["b_00000a"]))
        self.assertEqual(G.note_change("add", {"from": "2026-10-20T22:00:00+02:00", "fields": {"b_ffffff": 1}})["error"], "empty")
        G.note_change("edit", {"id": x["id"], "text": "ergänzt", "from": x["from"]})          # ohne „fields“ (ältere Oberfläche): Werte bleiben
        self.assertEqual(G.notes_all()["free"][0]["fields"]["b_00000a"], 12.5)
        G.note_change("edit", {"id": x["id"], "text": "ergänzt", "from": x["from"], "fields": {}})   # ausdrücklich geleert
        self.assertNotIn("fields", G.notes_all()["free"][0])
        self.assertTrue(G.proto_verify()["ok"])
        self.assertEqual(len(G.notes_list(q="nachbar")), 0); self.assertEqual(len(G.notes_list(q="ergänzt")), 1)

    def test_suche_findet_feldwerte(self):
        self.felder()
        G.note_change("add", {"from": "2026-10-20T22:00:00+02:00", "fields": {"b_000011": "Treppenhaus"}})
        self.assertEqual(len(G.notes_list(q="treppenhaus")), 1)

    def test_geloeschtes_feld_bleibt_lesbar(self):
        self.felder([NUM])
        G.note_change("add", {"from": "2026-10-20T22:00:00+02:00", "fields": {"b_00000a": 3}})
        self.felder([dict(NUM, **{"del": True})])
        self.assertTrue(next(b for b in G.fb_defs() if b["id"] == "b_00000a")["del"])
        head = next(csv.reader(io.StringIO(G.export_csv().decode("utf-8").lstrip("﻿")), delimiter=";"))
        self.assertIn("Gewicht [kg] (b_00000a)", head)                                   # mit Wert: Spalte bleibt
        self.assertIn("{Gewicht: 3 kg}", G.export_text("txt"))
        e = G.note_change("edit", {"id": G.notes_all()["free"][0]["id"], "text": "x", "from": "2026-10-20T22:00:00+02:00", "fields": {"b_00000a": 4}})
        self.assertTrue(e["ok"]); self.assertEqual(G.notes_all()["free"][0]["fields"]["b_00000a"], 4)


class Export(Basis):
    def test_csv_json_bericht_und_zurueck(self):
        self.felder()
        G.note_change("add", {"text": "Bass", "from": "2026-10-20T22:00:00+02:00",
                              "fields": {"b_00000a": 2.5, "b_00000d": ["Küche"], "b_000012": {"n": "Anna", "r": "nachbar", "c": "0171"}, "b_000013": "=SUMME(1)"}})
        G.note_change("add", {"from": "2026-10-20T22:05:00+02:00", "fields": {"b_00000c": 1}})
        G.note_change("add", {"from": "2026-10-21T08:00:00+02:00", "fields": {"b_00000c": 1}})
        rows = list(csv.reader(io.StringIO(G.export_csv().decode("utf-8").lstrip("﻿")), delimiter=";"))
        h = rows[0]; r = dict(zip(h, rows[1]))
        self.assertEqual(r["Gewicht [kg] (b_00000a)"], "2,5"); self.assertEqual(r["Zeuge 2 (b_000012)"], "Anna; Nachbar; 0171")
        self.assertTrue(r["Kennzeichen (b_000013)"].startswith("'="))                    # Schutz vor Formeln
        self.assertTrue(any(x[0].startswith("#") for x in rows))                         # Prüfblock bleibt am Ende
        j = json.loads(G.export_text("json")); self.assertEqual(len([b for b in j["felder"] if not b.get("bind")]), len(ALL)); self.assertIn("fields", j["notes"][0])
        rb = G.report_build()
        self.assertEqual(rb["zusammenfassung"]["zaehler"], [{"id": "b_00000c", "name": "Feuerzeug", "summe": 2, "tage": 2}])
        v = [x for x in rb["vorfaelle"] if x["text"] == "Bass"][0]
        self.assertIn({"id": "b_00000a", "name": "Gewicht", "wert": 2.5, "text": "2,5 kg"}, v["felder"])
        rt = G.report_text(rb); self.assertIn("Zähler „Feuerzeug“: 2", rt); self.assertIn("Gewicht: 2,5 kg", rt)
        # Export wieder einlesen: alles schon da; in leerem Bestand kommen die Felder zurück
        csvtxt = G.export_csv().decode("utf-8").lstrip("﻿")
        self.assertEqual(G.import_text({"content": csvtxt})["new"], 0)
        G.NOTES["data"] = None; G.PROTO["state"] = None; os.remove(G.notes_path()); os.remove(G.proto_path())
        res = G.import_text({"content": csvtxt}, apply=True); self.assertEqual(res["applied"], 3)
        back = sorted(G.notes_all()["free"], key=lambda x: x["from"])
        self.assertEqual(back[0]["fields"]["b_00000a"], 2.5); self.assertEqual(back[0]["fields"]["b_000013"], "=SUMME(1)")
        self.assertEqual(back[0]["fields"]["b_000012"], {"n": "Anna", "r": "nachbar", "c": "0171"}); self.assertEqual(back[1]["fields"], {"b_00000c": 1})

    def test_sicherung_enthaelt_felder(self):
        self.felder([NUM])
        f = io.BytesIO(); G.backup_write(f, files=False)
        import zipfile
        self.assertIn("felder.json", zipfile.ZipFile(io.BytesIO(f.getvalue())).namelist())


class Vorlagen(Basis):
    def test_vorlagen_loeschen_nichts(self):
        G.note_change("add", {"text": "Bass", "tags": ["musik"], "from": "2026-10-20T22:00:00+02:00"})
        before = json.dumps(G.notes_all()["free"])
        r = G.fb_change({"action": "tpl", "tpl": "zaehler"}); self.assertTrue(r["ok"])
        cs = [b for b in G.fb_defs() if b["type"] == "counter"]; self.assertEqual(len(cs), 1)
        self.assertEqual(r["tpl"], "zaehler"); self.assertTrue(G.fb_all()["sec"]["txt"]["hide"]); self.assertEqual(G.prefs()["cap_order"][:2], [cs[0]["id"], "time"])
        G.fb_change({"action": "tpl", "tpl": "allg"})
        self.assertTrue(next(b for b in G.fb_defs() if b["type"] == "counter")["hide"])     # Zähler der Vorlage nur ausgeblendet
        self.assertEqual(next(b for b in G.fb_defs() if b.get("bind") == "witness")["l"], "Person")   # Zeuge ist ein normales Feld
        self.assertEqual(G.qt_all()["gren"].get("own"), "Stichworte"); self.assertTrue(G.qt_all()["ghide"].get("src"))
        self.assertEqual(G.fb_all()["sec"]["wit"]["l"], "Person")
        G.fb_change({"action": "tpl", "tpl": "zaehler"})
        self.assertEqual(len([b for b in G.fb_defs() if b["type"] == "counter"]), 1)    # wieder benutzt, nicht doppelt
        G.fb_change({"action": "tpl", "tpl": "laerm"})
        self.assertNotIn("own", G.qt_all()["gren"]); self.assertFalse(G.qt_all()["ghide"].get("src")); self.assertNotIn("l", G.fb_all()["sec"].get("wit", {}))
        self.assertEqual(json.dumps(G.notes_all()["free"]), before)
        self.assertFalse(G.fb_change({"action": "tpl", "tpl": "boese"})["ok"])
        self.assertTrue(G.proto_verify()["ok"])

    def test_vorlage_in_sprache_der_oberflaeche(self):
        keep = G.OPT.get("language"); G.OPT["language"] = "de"                       # Server deutsch, Oberfläche englisch
        try:
            G.fb_change({"action": "tpl", "tpl": "zaehler", "lang": "en"})
            self.assertEqual([b["l"] for b in G.fb_defs() if b["type"] == "counter"], ["Counter"])
            G.fb_change({"action": "tpl", "tpl": "allg", "lang": "en"})
            self.assertEqual(G.qt_all()["gren"].get("own"), "Keywords")
        finally:
            G.OPT["language"] = keep

    def test_zaehler_heute(self):
        self.felder([CNT])
        now = dt.datetime.now().astimezone()
        for _ in range(3):
            G.note_change("add", {"from": now.isoformat(timespec="seconds"), "fields": {"b_00000c": 1}})
        G.note_change("add", {"from": (now - dt.timedelta(days=2)).isoformat(timespec="seconds"), "fields": {"b_00000c": 1}})
        st = G.fb_state(); self.assertEqual(st["counts"]["b_00000c"], 3)
        self.assertEqual(sum(x[1] for x in st["daily"]["b_00000c"]), 4); self.assertEqual(len(st["daily"]["b_00000c"]), 14)


class HomeAssistant(Basis):
    def test_zaehler_knopf_und_auswahl(self):
        self.felder([CNT, YN, dict(SEL, multi=False)])
        G.pub = lambda *a, **k: None; G.mqtt_form_state = lambda *a, **k: None
        kinds = {(k, s) for _, k, s in G.mqtt_fb()}
        self.assertIn(("button", "zaehler_00000c"), kinds); self.assertIn(("select", "feld_00000b"), kinds); self.assertIn(("select", "feld_00000d"), kinds)
        r = G.mqtt_cmd(f"{G.TOPIC}/zaehler_00000c/set", "PRESS"); self.assertTrue(r["ok"])
        self.assertEqual(G.notes_all()["free"][0]["fields"], {"b_00000c": 1}); self.assertEqual(G.notes_all()["free"][0]["by"], "homeassistant")
        G.mqtt_cmd(f"{G.TOPIC}/feld_00000b/set", "Ja"); G.mqtt_cmd(f"{G.TOPIC}/feld_00000d/set", "Bad"); G.mqtt_cmd(f"{G.TOPIC}/feld_00000d/set", "Keller")
        self.assertEqual(G.FORM["fields"], {"b_00000b": True, "b_00000d": "Bad"})
        G.FORM["fields"] = {}


if __name__ == "__main__":
    unittest.main()


class NotizArten(Basis):
    """Notiz-Arten (ab 1.11): anlegen, beim Erfassen setzen, filterbar exportieren; gehen nie verloren."""
    def test_arten(self):
        r = G.fb_change({"action": "set", "kinds": [{"id": "k_abcdef", "l": "Erinnerung", "col": "#7048E8", "ico": "⏰", "notime": True, "noassign": True},
                                                    {"id": "bad", "l": "x"}], "kind_def": "k_abcdef", "kind_keep": True})
        self.assertEqual([k["id"] for k in r["kinds"]], ["k_abcdef", "k_000001"]); self.assertEqual(r["kinds"][0]["col"], "#7048e8")   # „Erinnerung“ ist von Anfang an da
        self.assertEqual((r["kind_def"], r["kind_keep"]), ("k_abcdef", True))
        G.note_change("add", {"text": "Müll raus", "notime": True, "kind": "k_abcdef"})
        G.note_change("add", {"text": "Bass", "from": "2026-10-20T22:00:00+02:00", "kind": "k_gibtsnicht"})
        ns = {n["text"]: n for n in G.notes_all()["free"]}
        self.assertEqual(ns["Müll raus"]["kind"], "k_abcdef"); self.assertNotIn("kind", ns["Bass"])
        self.assertEqual(G.fb_state()["kind_n"], {"k_abcdef": 1})
        rows = list(csv.reader(io.StringIO(G.export_csv().decode("utf-8").lstrip("﻿")), delimiter=";"))
        self.assertEqual(rows[0][-1], "notiz_art"); self.assertIn("Erinnerung", [r_[-1] for r_ in rows[1:3]])
        nid = ns["Müll raus"]["id"]
        G.note_change("edit", {"id": nid, "text": "Müll raus!", "notime": True})          # ohne „kind“ (ältere Oberfläche): Art bleibt
        self.assertEqual(next(n for n in G.notes_all()["free"] if n["id"] == nid)["kind"], "k_abcdef")
        G.fb_change({"action": "set", "kinds": []})                                          # fehlt in der Liste: bleibt
        self.assertEqual(len(G.fb_state()["kinds"]), 2)
        G.fb_change({"action": "set", "kinds": [{"id": "k_abcdef", "l": "Erinnerung", "del": True}]})
        self.assertTrue(G.fb_state()["kinds"][0]["del"])
        self.assertEqual(G.note_change("add", {"text": "neu", "notime": True, "kind": "k_abcdef"})["ok"], True)
        self.assertNotIn("kind", next(n for n in G.notes_all()["free"] if n["text"] == "neu"))   # gelöschte Art: nicht mehr wählbar

    def test_ohne_arten_export_wie_bisher(self):
        G.note_change("add", {"text": "Bass", "from": "2026-10-20T22:00:00+02:00"})
        head = next(csv.reader(io.StringIO(G.export_csv().decode("utf-8").lstrip("﻿")), delimiter=";"))
        self.assertNotIn("notiz_art", head)

    def test_vorlage_bringt_erinnerung(self):
        G.tpl_apply("allg", "de")
        ls = [k["l"] for k in G.fb_state()["kinds"]]
        self.assertIn("Erinnerung", ls)
        G.tpl_apply("allg", "de"); self.assertEqual(len(G.fb_state()["kinds"]), len(ls))   # nicht doppelt


class ZeugeUndMehrAlsFelder(Basis):
    """Ab 1.12: Zeuge und „Mehr“ sind normale Felder (Werte bleiben in witness/ext der Notiz)."""
    def test_standardfelder_angelegt_und_bearbeitbar(self):
        defs = G.fb_defs(); bs = {b["bind"]: b for b in defs if b.get("bind")}
        self.assertEqual(set(bs), set(G.BOUND_IDS)); self.assertEqual(bs["witness"]["type"], "person"); self.assertTrue(bs["ext:freq"]["fold"])
        self.assertTrue(G.fb_all()["sec"]["wit"]["hide"])                                # alter Bereich weg
        r = G.fb_change({"action": "set", "blocks": [dict(bs["witness"], l="Nachbar als Zeuge", req=True), dict(bs["ext:threat"], **{"del": True}),
                                                     dict(bs["ext:freq"], bind="witness", type="text")]})      # Art und Speicherort bleiben
        b2 = {b["bind"]: b for b in r["blocks"] if b.get("bind")}
        self.assertEqual((b2["witness"]["l"], b2["witness"].get("req")), ("Nachbar als Zeuge", True))
        self.assertTrue(b2["ext:threat"]["del"]); self.assertEqual((b2["ext:freq"]["type"], b2["ext:freq"]["bind"]), ("text", "ext:freq"))
        G.note_change("add", {"from": "2026-10-20T22:00:00+02:00", "text": "x", "witness": "Anna", "ext": {"wrole": "nachbar", "freq": "nachts"}})
        head = next(csv.reader(io.StringIO(G.export_csv().decode("utf-8").lstrip("\ufeff")), delimiter=";"))
        self.assertFalse(any("b_00a0" in h for h in head))                               # keine doppelten Spalten
        n = G.notes_all()["free"][0]; self.assertEqual((n["witness"], n["ext"]["freq"]), ("Anna", "nachts"))

    def test_alte_einstellungen_werden_uebernommen(self):
        G.write_json(G.fb_path(), {"blocks": [], "sec": {"wit": {"l": "Person", "h": "Wer war dabei?", "req": True}, "more": {"hide": True}}, "tpl": "laerm"})
        G.FB["data"] = None
        bs = {b["bind"]: b for b in G.fb_defs() if b.get("bind")}
        self.assertEqual((bs["witness"]["l"], bs["witness"]["h"], bs["witness"]["req"]), ("Person", "Wer war dabei?", True))
        self.assertTrue(bs["ext:pol"]["hide"])
        self.assertEqual(json.load(open(G.fb_path()))["bound_v"], 1)                      # einmalig, gespeichert
