"""Sensor-Bestätigung von Störungen (bestaetigung.py und Einbindung in laerm.py): nur Flanken, asymmetrische Fenster, Sperrzeit,
offline, schon aktiv, eigene Quelle, Zufallstreffer, Zusammenfassung, Export, Notiz-Zuordnung. Gespeicherte Daten bleiben unverändert."""
import csv, hashlib, io, json, math, os, sys, tempfile, unittest
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import bestaetigung as BC  # noqa: E402

T0 = 1_760_000_000_000                                       # Störungsbeginn (ms)
S = 1000


def sensor(**k):
    d = dict(id="ha_vib", name="Decke", type="vib", role="ok", pre=5, post=10, lock=60, edges=[], on=[], offl=[], since=T0 - 86400000)
    d.update(k)
    d["edges"] = sorted(d["edges"]); d["on"] = sorted(d["on"]); d["_ona"] = [a for a, _ in d["on"]]
    return d


class Modul(unittest.TestCase):
    def test_treffer_und_fenster(self):
        r = BC.check(T0, "main", sensor(edges=[T0 + 3 * S], on=[[T0 + 3 * S, T0 + 5 * S]]))
        self.assertEqual((r["st"], r["dt"]), ("ok", 3.0))
        r = BC.check(T0, "main", sensor(edges=[T0 - 5 * S]))                    # Rand gehört dazu
        self.assertEqual(r["st"], "ok")
        r = BC.check(T0, "main", sensor(edges=[T0 + 12 * S]))                   # knapp daneben: nicht bestätigt, aber sichtbar
        self.assertEqual((r["st"], r["near"]), ("no", 12.0))
        r = BC.check(T0, "main", sensor(edges=[T0 - 7 * S, T0 + 8 * S]))        # nächste zum Beginn zählt
        self.assertEqual(r["dt"], 8.0)

    def test_nicht_beurteilbar(self):
        r = BC.check(T0, "main", sensor(edges=[T0 - 40 * S], on=[[T0 - 40 * S, T0 - 39 * S]]))
        self.assertEqual((r["st"], r["why"], r["ago_s"]), ("nb", "lock", 40.0))     # Sperrzeit 60 s
        r = BC.check(T0, "main", sensor(edges=[T0 - 40 * S], on=[[T0 - 40 * S, T0 - 39 * S]], lock=0))
        self.assertEqual(r["st"], "no")
        r = BC.check(T0, "main", sensor(edges=[T0 - 300 * S], on=[[T0 - 300 * S, T0 + 300 * S]]))
        self.assertEqual((r["st"], r["why"]), ("nb", "active"))                  # war schon an: keine neue Meldung
        r = BC.check(T0, "main", sensor(offl=[[T0 - 3600 * S, T0 + 2 * S]], edges=[T0 + 3 * S]))
        self.assertEqual((r["st"], r["why"]), ("nb", "offline"))
        r = BC.check(T0, "main", sensor(since=None))
        self.assertEqual((r["st"], r["why"]), ("nb", "nodata"))
        self.assertIsNone(BC.check(T0, "main", sensor(role="ctx")))
        self.assertIsNone(BC.check(T0, "main", sensor(off=True)))

    def test_eigene_quelle(self):
        r = BC.check(T0, "main", sensor(id="ha_pir", type="motion", role="own", pre=10, post=10, edges=[T0 - 8 * S]))
        self.assertEqual(r["st"], "own")
        r = BC.check(T0, "main", sensor(id="ha_pir", type="motion", role="own", edges=[]))
        self.assertEqual(r["st"], "free")
        r = BC.check(T0, "main", sensor(id="ha_w", type="power", role="own", lock=0, edges=[T0 - 600 * S], on=[[T0 - 600 * S, T0 + 600 * S]]))
        self.assertEqual((r["st"], r["why"]), ("own", "running"))                 # eigener Verbraucher läuft
        tilt = sensor(id="m_tilt_p1", type="tilt", role="own", dev="p1", only_dev=True, edges=[T0 + 1 * S])
        self.assertIsNone(BC.check(T0, "main", tilt)); self.assertEqual(BC.check(T0, "p1", tilt)["st"], "own")

    def test_zusammenfassen(self):
        ok = {"id": "a", "name": "Decke", "role": "ok", "st": "ok", "dt": 3.0, "p": 0.01}
        no = {"id": "b", "name": "Wand", "role": "ok", "st": "no", "p": 0.02}
        nb = {"id": "c", "name": "Boden", "role": "ok", "st": "nb", "why": "lock"}
        own = {"id": "d", "name": "Flur", "role": "own", "st": "own", "dt": -2.0}
        free = {"id": "d", "name": "Flur", "role": "own", "st": "free"}
        c = BC.combine([ok, no, nb, free])
        self.assertEqual((c["s"], c["n"], c["m"], c["t"]), ("ok", 1, 2, 3)); self.assertEqual(c["first"], ["Decke", 3.0])
        self.assertAlmostEqual(c["p"], 1 - 0.99 * 0.98, places=4)
        self.assertEqual(BC.combine([ok, own])["s"], "own")                      # eigene Aktivität geht vor
        self.assertEqual(BC.combine([nb])["s"], "nb"); self.assertEqual(BC.combine([no])["s"], "no"); self.assertEqual(BC.combine([free])["s"], "")
        sm = BC.summary([{"s": "ok", "p": 0.1}, {"s": "no", "p": 0.2}, {"s": "nb"}, {"s": "own"}, {"s": ""}])
        self.assertEqual((sm["n"], sm["ok"], sm["chk"], sm["rate"], sm["exp"]), (4, 1, 2, 0.5, 0.3))

    def test_grundrate_und_zufall(self):
        day = 86400000
        s = sensor(since=T0 - 14 * day, edges=[T0 - i * 1800 * S for i in range(1, 14 * 48 + 1)])     # 2 je Stunde
        lam, days, n = BC.base_rate(s, T0 - 14 * day, T0)
        self.assertAlmostEqual(lam * 3600, 2.0, places=2); self.assertAlmostEqual(days, 14.0, places=2)
        self.assertAlmostEqual(BC.p_chance(lam, 15), 1 - math.exp(-2 / 3600 * 15), places=6)   # etwa 0,8 %
        self.assertLess(BC.p_chance(lam, 15), 0.01)
        s2 = dict(s, offl=[[T0 - 7 * day, T0]])                                  # offline zählt nicht als erreichbare Zeit
        self.assertAlmostEqual(BC.base_rate(s2, T0 - 14 * day, T0)[1], 7.0, places=2)
        self.assertIsNone(BC.base_rate(sensor(since=None), 0, T0)[0])
        out, rates = BC.evaluate([("k1", T0 + 60 * S, "main")], [s], T0 + 3600 * S)
        self.assertIn("p", out["k1"]["res"][0]); self.assertFalse(rates["ha_vib"]["unsure"])

    def test_einstellungen(self):
        c = BC.clean_cfg({"on": False, "sens": {"ha_x": {"type": "vib", "pre": 999, "post": "7", "role": "boese"}, "bad key!": {}}})
        self.assertFalse(c["on"]); self.assertEqual(list(c["sens"]), ["ha_x"])
        self.assertEqual(c["sens"]["ha_x"], {"type": "vib", "pre": 600, "post": 7, "lock": 60, "role": "ok", "off": False})
        self.assertTrue(BC.clean_cfg({})["on"])
        self.assertEqual(BC.guess_type("binary_sensor.decke_vibration"), "vib"); self.assertEqual(BC.guess_type("binary_sensor.flur_motion"), "motion")
        self.assertEqual(BC.guess_type("binary_sensor.wohnungstuer_contact"), "door"); self.assertEqual(BC.guess_type("sensor.waschmaschine_power"), "power")
        self.assertEqual(BC.guess_type("media_player.tv"), "other")
        self.assertEqual(BC.clean_sensor({}, "cam"), {"type": "cam", "pre": 5, "post": 30, "lock": 0, "role": "own", "off": False})

    def test_notizen_zuordnen(self):
        incs = [("e1", T0, T0 + 10 * S, {"main"}), ("e2", T0 + 20 * 60 * S, T0 + 21 * 60 * S, {"main"})]
        pre, post = 2 * 60000, 15 * 60000
        m = BC.assign_notes([("n1", T0 + 5 * 60 * S, None, "all"), ("n2", T0 - 3 * 60 * S, None, "all"), ("n3", T0 + 18 * 60 * S, None, "all"),
                             ("n4", T0 - 60 * S, T0 + 60 * S, "p9")], incs, pre, post)
        self.assertEqual(m["n1"][:2], ("e1", 5 * 60 * S))
        self.assertNotIn("n2", m)                                                   # 3 min davor: außerhalb −2 min
        self.assertEqual((m["n3"][0], m["n3"][2]), ("e2", 1))                          # 18 min nach e1 (außerhalb), 2 min vor e2
        self.assertNotIn("n4", m)                                                   # anderes Gerät
        incs2 = [("e1", T0, T0 + 10 * S, {"main"}), ("e3", T0 + 10 * 60 * S, T0 + 10 * 60 * S, {"main"})]
        m2 = BC.assign_notes([("n5", T0 + 9 * 60 * S, None, "all")], incs2, pre, post)
        self.assertEqual(m2["n5"], ("e3", -60 * S, 2))                                 # zwei Kandidaten: der nähere (1 min davor)


class Einbindung(unittest.TestCase):
    """laerm.py: Störungen aus log.csv, Sensor aus ha_zustand.csv – Anzeige und Export, gespeicherte Dateien bleiben gleich."""
    def setUp(self):
        import laerm
        self.L = laerm
        self.tmp = tempfile.mkdtemp(); out = os.path.join(self.tmp, "out"); os.makedirs(out)
        self.keep = (laerm.paths, laerm.BC_FILE, list(laerm.HA_RULES), dict(laerm.CFG), laerm.run_downs, laerm.GR_DIR)
        laerm.paths = lambda: (out, out + "/clips", out + "/log.csv")
        laerm.BC_FILE = os.path.join(self.tmp, "bestaetigung.json")
        laerm.run_downs = lambda: []
        laerm.GR_DIR = os.path.join(self.tmp, "kein_greport")
        laerm.HA_HIST.update(key=None, rows=[]); laerm.HA_AVAIL.update(cur=None, key=None, rows=[])
        laerm.HA_RULES[:] = laerm.clean_rules([{"id": "vib1", "entity": "binary_sensor.decke_vibration", "states": "on", "mode": "note", "label": "Decke"},
                                               {"id": "pir1", "entity": "binary_sensor.flur_motion", "states": "on", "mode": "note", "label": "Flur"}])
        laerm.NOTES["data"] = None
        self.out = out
        now = dt.datetime.now().astimezone().replace(microsecond=0)
        self.t1 = now - dt.timedelta(hours=2); self.t2 = now - dt.timedelta(hours=1)
        hdr = ["start", "dauer_s", "spitze_dbfs", "hintergrund_dbfs", "schwelle_dbfs", "quelle", "quelle_id", "datei"]
        with open(out + "/log.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(hdr)
            for t in (self.t1, self.t2):
                w.writerow([t.isoformat(timespec="milliseconds"), "4.0", "-30.0", "-60.0", "-50.0", "Mikrofon", "main", ""])
        iso = lambda t: t.isoformat(timespec="milliseconds")
        with open(out + "/ha_zustand.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["zeit", "regel", "name", "entitaet", "zustand", "an", "geraet"])
            start = now - dt.timedelta(days=5)
            for rid, ent in (("vib1", "binary_sensor.decke_vibration"), ("pir1", "binary_sensor.flur_motion")):
                w.writerow([iso(start), rid, rid, ent, "off", "0", "all"])
            w.writerow([iso(self.t1 + dt.timedelta(seconds=3)), "vib1", "Decke", "binary_sensor.decke_vibration", "on", "1", "all"])
            w.writerow([iso(self.t1 + dt.timedelta(seconds=90)), "vib1", "Decke", "binary_sensor.decke_vibration", "off", "0", "all"])
        with open(out + "/ha_verfuegbar.csv", "w", newline="", encoding="utf-8") as f:   # Flur zur zweiten Störung offline
            w = csv.writer(f); w.writerow(["zeit", "regel", "entitaet", "offline"])
            w.writerow([iso(self.t2 - dt.timedelta(minutes=10)), "pir1", "binary_sensor.flur_motion", "1"])
            w.writerow([iso(self.t2 + dt.timedelta(minutes=10)), "pir1", "binary_sensor.flur_motion", "0"])
        self.before = {fn: self.digest(fn) for fn in os.listdir(out)}

    def digest(self, fn):
        with open(os.path.join(self.out, fn), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def tearDown(self):
        L = self.L
        L.paths, L.BC_FILE, rules, cfg, L.run_downs, L.GR_DIR = self.keep
        L.HA_RULES[:] = rules; L.CFG.clear(); L.CFG.update(cfg); L.HA_HIST.update(key=None, rows=[]); L.HA_AVAIL.update(cur=None, key=None, rows=[])
        L.NOTES["data"] = None

    def unchanged(self):
        after = {fn: self.digest(fn) for fn in self.before}
        self.assertEqual(after, self.before)

    def test_tabelle_detail_export(self):
        L = self.L
        j = L.events_summary("all", 50)
        ev = {e["start"][:19]: e for e in j["events"]}
        e1 = ev[self.t1.isoformat()[:19]]; e2 = ev[self.t2.isoformat()[:19]]
        self.assertEqual((e1["sc"]["s"], e1["sc"]["n"], e1["sc"]["m"]), ("ok", 1, 1)); self.assertEqual(e1["sc"]["first"], ["Decke", 3.0])
        self.assertEqual(e2["sc"]["s"], "no")                                     # Decke still, Flur offline (eigene Aktivität nicht prüfbar)
        sm = j["sc_sum"]; self.assertEqual((sm["n"], sm["ok"], sm["no"], sm["chk"]), (2, 1, 1, 2)); self.assertIsNotNone(sm["exp"])
        d = L.bc_detail(dict(e2))
        flur = [x for x in d["res"] if x["name"] == "Flur"][0]
        self.assertEqual((flur["st"], flur["why"]), ("nb", "offline")); self.assertIn("per_h", flur)
        rows = list(csv.reader(io.StringIO(L.export_csv({}).decode("utf-8").lstrip("﻿")), delimiter=";"))
        h = rows[0]; self.assertEqual(h[-4:], ["sensor_bestaetigung", "sensoren_zeitgleich", "sensoren_einzeln", "zufallstreffer_pct"])
        body = [dict(zip(h, r)) for r in rows[1:] if r and not r[0].startswith("#")]
        self.assertEqual(len(body), 2)                                            # nicht bestätigte bleiben drin
        self.assertEqual({b["sensor_bestaetigung"] for b in body}, {"bestaetigt", "nicht_bestaetigt"})
        self.assertIn("Decke +3 s", " ".join(b["sensoren_einzeln"] for b in body))
        self.assertTrue(rows[-1][0] == "#methode" and "zeitliche Übereinstimmung" in rows[-1][1])
        html = L.protocol_html({"all": ["1"]}); html = html.decode("utf-8") if isinstance(html, bytes) else html
        self.assertIn("Zeitgleiche Sensorereignisse", html); self.assertIn("zeitgleich registriert von 1 von 1", html)
        self.unchanged()

    def test_aus_und_rollen(self):
        L = self.L
        L.bc_save({"on": False})
        self.assertNotIn("sc", L.events_summary("all", 50)["events"][0]); self.assertIsNone(L.events_summary("all", 50)["sc_sum"])
        h = next(csv.reader(io.StringIO(L.export_csv({}).decode("utf-8").lstrip("﻿")), delimiter=";"))
        self.assertNotIn("sensor_bestaetigung", h)                                 # aus: Export wie bisher
        L.bc_save({"on": True, "sens": {"ha_vib1": {"type": "vib", "role": "ctx"}}})
        p = L.bc_public(); self.assertTrue(p["on"])
        v = [x for x in p["sensors"] if x["id"] == "ha_vib1"][0]; self.assertEqual((v["role"], v["saved"]), ("ctx", True))
        pir = [x for x in p["sensors"] if x["id"] == "ha_pir1"][0]; self.assertEqual((pir["type"], pir["role"], pir["saved"]), ("motion", "own", False))
        ev = L.events_summary("all", 50)["events"]
        self.assertTrue(all(e.get("sc", {}).get("s", "") in ("", "nb") for e in ev))   # nur noch Flur (eigene Aktivität): kein Bestätigungssensor
        L.bc_save({"sens": {"ha_vib1": {"type": "vib", "role": "ok", "post": 2}}})       # Fenster bis +2 s: Treffer bei +3 s knapp daneben
        e1 = [e for e in L.events_summary("all", 50)["events"] if e["start"][:19] == self.t1.isoformat()[:19]][0]
        self.assertEqual(e1["sc"]["s"], "no")
        d = L.bc_detail(dict(e1)); dec = [x for x in d["res"] if x["name"] == "Decke"][0]; self.assertEqual(dec["near"], 3.0)
        self.unchanged()

    def test_erreichbarkeit_wird_mitgeschrieben(self):
        L = self.L
        r = L.HA_RULES[0]; t_ = int(dt.datetime.now().timestamp() * 1000)
        L.ha_avail_add(r, t_, True); L.ha_avail_add(r, t_ + 1000, True); L.ha_avail_add(r, t_ + 5000, False)
        off = L.ha_offline()["vib1"]; self.assertEqual(off[-1], [t_, t_ + 5000])

    def test_notiz_fenster(self):
        L = self.L
        L.CFG.update(fn_pre_min=2, fn_post_min=15)
        at = int(self.t2.timestamp() * 1000) + 5 * 60000
        tg = L.fnote_target(at)
        self.assertIsNotNone(tg); self.assertEqual(tg["delta_s"], 300); self.assertEqual((tg["pre_min"], tg["post_min"]), (2, 15))
        self.assertIsNone(L.fnote_target(int(self.t2.timestamp() * 1000) - 3 * 60000))   # 3 min davor: außerhalb
        self.assertIsNotNone(L.fnote_target(int(self.t2.timestamp() * 1000) - 60000))   # 1 min davor: innerhalb
        L.CFG.update(fn_post_min=3)
        self.assertIsNone(L.fnote_target(at))
        j = L.events_summary("all", 50); self.assertEqual((j["fn_pre_min"], j["fn_post_min"]), (2, 3))


if __name__ == "__main__":
    unittest.main()
