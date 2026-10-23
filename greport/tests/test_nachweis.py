"""GReport Nachweis: Änderungsprotokoll mit Prüfsummenkette, Prüfen (auch manipuliert), Export mit Prüfblock,
Notizen ohne Zeitpunkt (nicht für GLighter), Zeitpunkt-Tasten, eigene Rubriken, Layout in einem Rutsch."""
import io, json, os, shutil, sys, tempfile, unittest, zipfile
import datetime as dt

D = tempfile.mkdtemp()
os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import greport as G  # noqa: E402


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def wr(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def lines():
    return [json.loads(x) for x in rd(G.proto_path()).splitlines() if x.strip()]


class Basis(unittest.TestCase):
    def setUp(self):
        G.NOTES["data"] = None; G.QT["data"] = None; G.PROTO["state"] = None
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)


class Kette(Basis):
    def test_vorgaenge_und_kette(self):
        a = G.note_change("add", {"text": "Bass", "from": "2026-10-20T22:00:00+02:00"})["note"]
        G.note_change("edit", {"id": a["id"], "text": "Bass laut", "from": a["from"]})
        G.note_change("del", {"id": a["id"]})
        self.assertTrue(G.note_change("restore", {"id": a["id"]})["ok"])
        ops = [e["op"] for e in lines()]
        self.assertEqual(ops, ["start", "add", "edit", "del", "restore"])
        e = lines()
        self.assertEqual(e[2]["prev"]["text"], "Bass"); self.assertEqual(e[2]["note"]["text"], "Bass laut")   # vorige Fassung bleibt
        for i in range(1, len(e)):
            self.assertEqual(e[i]["prev_hash"], e[i - 1]["hash"])
        self.assertTrue(all(x.get("tz") is not None and "+" in x["iso"] or "-" in x["iso"][19:] for x in e))  # Zeitzone im Eintrag
        v = G.proto_verify()
        self.assertTrue(v["ok"], v["problems"]); self.assertEqual(v["n"], 5); self.assertEqual(v["last_hash"], e[-1]["hash"])
        self.assertIn("Home Assistant", v["clock"])
        self.assertEqual([h["op"] for h in G.proto_history(a["id"])], ["add", "edit", "del", "restore"])

    def test_start_mit_vorhandenen_notizen(self):
        G.write_json(G.notes_path(), {"free": [{"id": "r_alt", "from": "2026-01-01T10:00:00+01:00", "to": "", "text": "alt", "tags": []}], "trash": []})
        G.NOTES["data"] = None; G.notes_all()
        e = lines(); self.assertEqual(e[0]["op"], "start"); self.assertEqual(e[0]["notes"][0]["id"], "r_alt")
        self.assertTrue(G.proto_verify()["ok"])

    def test_manipulierte_notiz_wird_erkannt(self):
        G.note_change("add", {"text": "echt", "from": "2026-10-20T22:00:00+02:00"})
        d = G.read_json(G.notes_path()); d["free"][0]["text"] = "gefälscht"; G.write_json(G.notes_path(), d)
        v = G.proto_verify()
        self.assertFalse(v["ok"]); self.assertTrue(any("weicht" in p["what"] or "differs" in p["what"] for p in v["problems"]))

    def test_manipuliertes_protokoll_wird_erkannt(self):
        G.note_change("add", {"text": "eins", "from": "2026-10-20T22:00:00+02:00"})
        G.note_change("add", {"text": "zwei", "from": "2026-10-20T23:00:00+02:00"})
        ls = rd(G.proto_path()).splitlines()
        e = json.loads(ls[1]); e["note"]["text"] = "anders"; ls[1] = json.dumps(e)
        wr(G.proto_path(), "\n".join(ls) + "\n")
        v = G.proto_verify(); self.assertFalse(v["ok"])
        self.assertTrue(any(p.get("line") == 2 for p in v["problems"]))
        ls.pop(1); wr(G.proto_path(), "\n".join(ls) + "\n")   # Eintrag entfernt
        self.assertTrue(any("Verkettung" in p["what"] or "chain" in p["what"] for p in G.proto_verify()["problems"]))

    def test_neu_berechnete_kette_ohne_schluessel_faellt_auf(self):
        G.note_change("add", {"text": "eins", "from": "2026-10-20T22:00:00+02:00"})
        es = lines(); prev = G.PROTO_ZERO
        es[1]["note"]["text"] = "anders"
        for e in es:                                      # wer nur /share hat, rechnet SHA-256 neu – die HMAC passt dann nicht
            e["prev_hash"] = prev; e["hash"], _ = G.proto_hashes(prev, e, None); prev = e["hash"]
        wr(G.proto_path(), "".join(G.canon(e) + "\n" for e in es))
        v = G.proto_verify(); self.assertFalse(v["ok"])
        self.assertTrue(any("Schlüssel" in p["what"] or "keyed" in p["what"] for p in v["problems"]))

    def test_aenderung_ausserhalb_beim_start(self):
        G.note_change("add", {"text": "eins", "from": "2026-10-20T22:00:00+02:00"})
        d = G.read_json(G.notes_path()); d["free"][0]["text"] = "von außen"; G.write_json(G.notes_path(), d)
        G.NOTES["data"] = None; G.notes_all()            # Neustart: wird als „extern“ festgehalten, nicht verschwiegen
        v = G.proto_verify(); self.assertTrue(v["ok"]); self.assertEqual(len(v["warnings"]), 1)


class Export(Basis):
    def test_pruefblock_und_kennzeichnung(self):
        cap = int(dt.datetime(2026, 10, 20, 22, 10).astimezone().timestamp() * 1000)
        G.note_change("add", {"text": "Bass", "from": "2026-10-20T22:05:00+02:00", "cap": cap, "wk": "w_5", "wl": "vor 5 Min."})
        G.note_change("add", {"text": "Nacht", "from": "2026-10-19T22:00:00+02:00", "to": "2026-10-20T06:00:00+02:00", "wk": "w_night", "approx": True, "cap": cap})
        txt = G.export_text("txt")
        self.assertIn("Zeit per Taste gesetzt (vor 5 Min.)", txt); self.assertIn("ungefähr", txt); self.assertIn("erfasst", txt)
        self.assertIn("Prüfblock", txt); self.assertIn(lines()[-1]["hash"], txt)
        csv_ = G.export_text("csv"); self.assertIn("#letzter_hash", csv_); self.assertIn("erfasst_iso", csv_)
        j = json.loads(G.export_text("json")); self.assertEqual(j["nachweis"]["letzter_hash"], lines()[-1]["hash"])
        self.assertIn("#letzter_hash", G.export_csv().decode("utf-8"))
        rows, err = G.parse_import(txt)                   # Re-Import: Prüfblock und Kennzeichnung stören nicht
        self.assertEqual(sorted(r["text"] for r in rows), ["Bass", "Nacht"])
        rows, err = G.parse_import(csv_); self.assertEqual(len(rows), 2)
        n = G.nachweis_json(); self.assertTrue(n["pruefung"]["ok"]); self.assertEqual(len(n["eintraege"]), 3)
        z = zipfile.ZipFile(io.BytesIO(G.backup_zip())); self.assertIn("notizen_protokoll.jsonl", z.namelist())


class OhneZeitpunkt(Basis):
    def test_nicht_fuer_glighter(self):
        n = G.note_change("add", {"text": "Müll raus", "notime": True})["note"]
        raw = G.read_json(G.notes_path())["free"][0]
        self.assertEqual(raw["from"], ""); self.assertTrue(raw["notime"])          # GLighter liest „from“ – leer = an keine Störung
        self.assertIsNotNone(n["a"]); self.assertEqual(G.notes_list()[0]["id"], n["id"])
        self.assertNotIn(":", G.notes_summary()["last"].split(" ")[0])                # Sensor ohne Uhrzeit
        self.assertIn("ohne Zeitpunkt", G.export_text("txt"))
        e = G.note_change("edit", {"id": n["id"], "text": "Müll", "from": "2026-10-20T08:00:00+02:00"})["note"]   # mit Zeit
        self.assertNotIn("notime", e); self.assertEqual(e["from"], "2026-10-20T08:00:00+02:00")

    def test_import_json(self):
        old = G.pro_ok; G.pro_ok = lambda: True
        try:
            r = G.notes_import({"notes": [{"id": "r_x", "from": "", "notime": True, "at": "2026-10-20T08:00:00+02:00", "text": "ohne"}]})
        finally:
            G.pro_ok = old
        self.assertEqual(r.get("n"), 1, r)


class Schnellwahl(Basis):
    def test_zeitpunkt_rubrik_und_batch(self):
        r = G.qt_change({"action": "batch", "ops": [{"action": "gadd", "g": "g_aaaaaa", "l": "Küche"}, {"action": "add", "k": "c_bbbbbb", "l": "Spüle", "g": "g_aaaaaa"},
                                                    {"action": "wadd", "k": "t_cccccc", "l": "um 6", "at": "6:00"}, {"action": "gorder", "groups": ["when", "g_aaaaaa"]},
                                                    {"action": "ghide", "g": "lvl", "on": True}]})
        self.assertEqual(r["errors"], []); self.assertEqual([x["g"] for x in r["gall"]][:2], ["when", "g_aaaaaa"])
        self.assertEqual(r["grp"]["c_bbbbbb"], "g_aaaaaa"); self.assertTrue(any(w["k"] == "t_cccccc" and w["at"] == "06:00" for w in r["when"]))
        self.assertNotIn("leicht", [k for k, _ in G.qt_visible()])                        # ausgeblendete Rubrik auch in HA weg
        self.assertIn("zeitpunkt", [m[1] for m in G.mqtt_groups()]); self.assertIn("rubrik_aaaaaa", [m[1] for m in G.mqtt_groups()])
        n = dt.datetime(2026, 10, 23, 10, 0).astimezone()
        self.assertEqual(G.when_apply_full("w_night", n)[:2], (dt.datetime(2026, 10, 22, 22, 0).astimezone().isoformat(), dt.datetime(2026, 10, 23, 6, 0).astimezone().isoformat()))
        self.assertTrue(G.when_apply_full("w_night", n)[3])                               # ungefähr
        self.assertEqual(G.when_apply_full("w_5", n)[0], dt.datetime(2026, 10, 23, 9, 55).astimezone().isoformat())
        G.FORM["pick"]["when"] = "vor 15 Min."; G.FORM["text"] = "aus HA"
        x = G.form_save()["note"]; self.assertEqual(x["wk"], "w_15"); self.assertIn("cap", x)
        G.qt_change({"action": "reset"}); self.assertEqual(G.qt_all()["gorder"], [])

    def test_ueberschrift_in_einstellungen(self):
        p = G.prefs_set({"cap_title": "  Lärm <b>jetzt</b> ", "cap_sub": "x" * 300, "cap_order": ["wit", "txt"]})
        self.assertEqual(p["cap_title"], "Lärm bjetzt/b"); self.assertEqual(len(p["cap_sub"]), 160); self.assertEqual(p["cap_order"], ["wit", "txt", "tags", "more", "time"])
        p = G.prefs_set({"cap_title": "", "cap_sub": "", "cap_order": []}); self.assertNotIn("cap_title", G.prefs()); self.assertNotIn("cap_order", G.prefs())


if __name__ == "__main__":
    unittest.main()
