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

    def test_zuordnung_mit_fenster_je_notiz_und_von_hand(self):
        evs = [("e1", T0, T0 + 10 * S, "main"), ("e2", T0 + 20 * 60 * S, T0 + 21 * 60 * S, "main"), ("e3", T0 + 25 * 60 * S, T0 + 25 * 60 * S, "p2")]
        gl, gr = (2 * 60000, 15 * 60000), (10 * 60000, 30 * 60000)
        notes = [("f:a", T0 + 5 * 60 * S, None, "all", *gl), ("f:b", T0 - 8 * 60 * S, None, "all", *gl), ("g:b", T0 - 8 * 60 * S, None, "all", *gr),
                 ("g:c", T0 + 16 * 60 * S, None, "all", *gr), ("f:d", T0 + 2 * 3600 * S, None, "all", *gl)]
        m = BC.assign(notes, evs)
        self.assertEqual((m["f:a"]["k"], m["f:a"]["d"], m["f:a"]["man"]), ("e1", 5 * 60 * S, False))
        self.assertNotIn("f:b", m)                                                      # GLighter: 8 min davor liegt außerhalb −2 min
        self.assertEqual(m["g:b"]["k"], "e1")                                           # GReport: −10 min reicht
        self.assertEqual([c[0] for c in m["g:c"]["cand"]], ["e2", "e3", "e1"])          # alle passenden, die nächste zuerst
        self.assertNotIn("f:d", m)
        m2 = BC.assign(notes, evs, {"g:c": "e3", "f:a": None, "f:d": "weg"})           # von Hand: neu zuordnen, lösen; unbekannte Störung: automatisch
        self.assertEqual((m2["g:c"]["k"], m2["g:c"]["man"], m2["g:c"]["d"]), ("e3", True, -9 * 60 * S))
        self.assertEqual((m2["f:a"]["k"], m2["f:a"]["man"]), (None, True))
        self.assertNotIn("f:d", m2)
        self.assertEqual(BC.assign([("x", T0, None, "p9", *gl)], evs), {})               # anderes Gerät

    def test_uhrabgleich(self):
        st = BC.clock_eval([{"kind": "ha", "name": "Home Assistant", "off": 0.4}, {"kind": "phone", "name": "Handy Küche", "off": -1.6}])
        self.assertEqual(([x["off"] for x in st["items"]], st["max"], st["warn"]), ([0, -2], 2, False))
        self.assertEqual(BC.clock_text(st), "Uhrabgleich: Abweichung Home Assistant 0 s, Handy Küche 2 s")
        st = BC.clock_eval([{"kind": "ha", "name": "Home Assistant", "off": 7.2}, {"kind": "phone", "name": "Handy", "off": None}], 5)
        self.assertTrue(st["warn"]); self.assertIn("mehr als 5 s", BC.clock_text(st))
        self.assertEqual(BC.clock_text(BC.clock_eval([]), de=False), "Clock check: no reference clock available")
        c = BC.clean_cfg({"clock_warn": 9999, "lanes": False}); self.assertEqual((c["clock_warn"], c["lanes"]), (600, False))
        self.assertEqual((BC.clean_cfg({})["clock_warn"], BC.clean_cfg({})["lanes"]), (5, True))


class Einbindung(unittest.TestCase):
    """laerm.py: Störungen aus log.csv, Sensor aus ha_zustand.csv – Anzeige und Export, gespeicherte Dateien bleiben gleich."""
    def setUp(self):
        import laerm
        self.L = laerm
        self.tmp = tempfile.mkdtemp(); out = os.path.join(self.tmp, "out"); os.makedirs(out)
        self.keep = (laerm.paths, laerm.BC_FILE, list(laerm.HA_RULES), dict(laerm.CFG), laerm.run_downs, laerm.GR_DIR, laerm.NA_FILE)
        laerm.NA_FILE = os.path.join(self.tmp, "notiz_zuordnung.json")
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
        L.paths, L.BC_FILE, rules, cfg, L.run_downs, L.GR_DIR, L.NA_FILE = self.keep
        L.HA_RULES[:] = rules; L.CFG.clear(); L.CFG.update(cfg); L.HA_HIST.update(key=None, rows=[]); L.HA_AVAIL.update(cur=None, key=None, rows=[])
        L.NOTES["data"] = None

    def unchanged(self):
        after = {fn: self.digest(fn) for fn in self.before}
        self.assertEqual(after, self.before)

    def test_dauer_einmal_ausloesen_und_obergrenze(self):
        """„Einmal auslösen“: Meldung nur mit fester Länge ab dem Einschalten; „höchstens“ kürzt; ha_zustand.csv bleibt gleich."""
        L = self.L
        a = int((self.t1 + dt.timedelta(seconds=3)).timestamp() * 1000)
        iv = lambda: [x for x in L.ha_intervals("*", 0, 2**62) if x[3] == "vib1"]
        self.assertEqual(iv()[0][1] - iv()[0][0], 87000)                       # solange gemeldet (wie bisher)
        L.HA_RULES[:] = L.clean_rules([{"id": "vib1", "entity": "binary_sensor.decke_vibration", "states": "on", "mode": "event", "label": "Decke", "dur": "pulse", "dur_s": 5}])
        self.assertEqual((iv()[0][0], iv()[0][1]), (a, a + 5000))
        self.assertEqual(L.HA_RULES[0]["dur"], "pulse")
        s = [x for x in L.bc_sensors() if x.get("rid") == "vib1"][0]
        self.assertEqual(s["on"][0], [a, a + 5000]); self.assertEqual(s["edges"], [a])
        L.HA_RULES[:] = L.clean_rules([{"id": "vib1", "entity": "binary_sensor.decke_vibration", "states": "on", "mode": "note", "label": "Decke", "cap_min": 1}])
        self.assertEqual(iv()[0][1] - iv()[0][0], 60000)
        L.HA_RULES[:] = L.clean_rules([{"id": "vib1", "entity": "x.y", "states": "on", "mode": "note", "dur": "quatsch", "dur_s": "abc", "cap_min": -5}])
        self.assertEqual((L.HA_RULES[0]["dur"], L.HA_RULES[0]["dur_s"], L.HA_RULES[0]["cap_min"]), ("state", 5.0, 0.0))
        self.unchanged()

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

    def note(self, t, text="Bass", **k):
        r = self.L.fnote_change("add", dict({"text": text, "from": t.strftime("%Y-%m-%dT%H:%M:%S")}, **k)); self.assertTrue(r["ok"]); return r["note"]

    def test_notiz_zuordnung_export_und_von_hand(self):
        L = self.L
        def csvh(b):
            return list(csv.reader(io.StringIO(b.decode("utf-8").lstrip("\ufeff")), delimiter=";"))
        h0 = csvh(L.export_csv({}))[0]; nh0 = next(csv.reader(io.StringIO(L.notes_csv({}).decode("utf-8").lstrip("\ufeff"))))
        self.assertNotIn("notizen_zugeordnet", h0); self.assertNotIn("stoerung_zugeordnet", nh0)      # ohne Notizen: wie bisher
        html0 = L.protocol_html({"all": ["1"]}); html0 = html0.decode() if isinstance(html0, bytes) else html0
        self.assertNotIn("Notiz zugeordnet", html0)
        n = self.note(self.t1 + dt.timedelta(minutes=5))
        notes_before = json.dumps(L.notes_all()["free"], sort_keys=True)
        j = L.events_summary("all", 50)
        a = [x for x in j["fnotes"] if x["id"] == n["id"]][0]["asg"]
        e1 = [e for e in j["events"] if e["start"][:19] == self.t1.isoformat()[:19]][0]
        self.assertEqual((a["k"], a["d"], a["man"], a["n"], a["pre"], a["post"]), (e1["k"], 300000, False, 1, 2, 15))
        rows = csvh(L.export_csv({})); h = rows[0]
        self.assertEqual(h[-1], "notizen_zugeordnet")
        body = {r[0][:19]: dict(zip(h, r)) for r in rows[1:] if r and not r[0].startswith("#")}
        self.assertEqual(body[self.t1.isoformat()[:19]]["notizen_zugeordnet"], "5 min danach, automatisch: Bass")
        self.assertEqual(body[self.t2.isoformat()[:19]]["notizen_zugeordnet"], "")
        nr = list(csv.reader(io.StringIO(L.notes_csv({}).decode("utf-8").lstrip("\ufeff"))))
        nd = dict(zip(nr[0], nr[1])); self.assertEqual(nd["zuordnung"], "5 min danach, automatisch"); self.assertEqual(nd["stoerung_zugeordnet"][:19], self.t1.isoformat()[:19])
        html = L.protocol_html({"all": ["1"]}); html = html.decode() if isinstance(html, bytes) else html
        self.assertIn("Notiz zugeordnet (5 min danach, automatisch", html)
        # von Hand: neu zuordnen nur auf eine passende Störung, lösen, zurück auf automatisch
        L.NA_FILE = os.path.join(self.tmp, "notiz_zuordnung.json")
        det = L.fn_asg_detail("f:" + n["id"]); self.assertTrue(det["ok"]); self.assertEqual(det["cur"]["k"], e1["k"]); self.assertEqual(det["cand"], [])
        e2 = [e for e in j["events"] if e["start"][:19] == self.t2.isoformat()[:19]][0]
        self.assertFalse(L.fn_asg_change({"id": "f:" + n["id"], "action": "set", "k": e2["k"]})["ok"])   # liegt nicht im Fenster
        r = L.fn_asg_change({"id": "f:" + n["id"], "action": "detach"}); self.assertTrue(r["detached"] and r["man"])
        a = [x for x in L.events_summary("all", 50)["fnotes"] if x["id"] == n["id"]][0]["asg"]; self.assertEqual((a["k"], a["man"]), (None, True))
        self.assertNotIn("notizen_zugeordnet", csvh(L.export_csv({}))[0])
        L.CFG.update(fn_pre_min=120)                                                     # größeres Fenster: zweite Störung passt auch
        det = L.fn_asg_detail("f:" + n["id"]); self.assertEqual([c["k"] for c in det["cand"]], [e1["k"], e2["k"]])
        r = L.fn_asg_change({"id": "f:" + n["id"], "action": "set", "k": e2["k"]}); self.assertTrue(r["man"]); self.assertEqual(r["cur"]["k"], e2["k"])
        rows = csvh(L.export_csv({})); body = {r_[0][:19]: dict(zip(rows[0], r_)) for r_ in rows[1:] if r_ and not r_[0].startswith("#")}
        self.assertEqual(body[self.t2.isoformat()[:19]]["notizen_zugeordnet"], "55 min davor, von Hand: Bass")
        r = L.fn_asg_change({"id": "f:" + n["id"], "action": "auto"}); self.assertFalse(r["man"]); self.assertEqual(r["cur"]["k"], e1["k"])
        self.assertEqual(json.dumps(L.notes_all()["free"], sort_keys=True), notes_before)        # Notiz und Zeiten unverändert
        self.unchanged()

    def test_greport_notiz_eigenes_fenster(self):
        L = self.L
        L.CFG.update(fn_gr_pre_min=10, fn_gr_post_min=30)
        n = {"id": "r_1", "a": int(self.t1.timestamp() * 1000) - 8 * 60000, "b": None, "src": "all", "gr": True}
        g = {"id": "x_1", "a": n["a"], "b": None, "src": "all"}
        m = L.fn_assign([n, g])
        self.assertIn("g:r_1", m); self.assertNotIn("f:x_1", m)                           # GReport −10 min, GLighter nur −2 min
        self.assertEqual(L.fn_win(n), (600000, 1800000)); self.assertEqual(L.fn_win(g), (120000, 900000))

    def test_sensor_spuren_und_uhr(self):
        L = self.L
        a = int(self.t1.timestamp() * 1000) - 3600000; b = int(self.t2.timestamp() * 1000) + 3600000
        j = L.sc_lanes(a, b)
        self.assertTrue(j["on"]); ln = {x["name"]: x for x in j["lanes"]}
        self.assertEqual(ln["Decke"]["edges"], [int(self.t1.timestamp() * 1000) + 3000]); self.assertEqual((ln["Decke"]["pre"], ln["Decke"]["post"]), (5, 10))
        self.assertEqual(len(ln["Flur"]["off"]), 1)                                       # offline schraffiert
        k = L.events_summary("all", 50)["events"][-1]["k"]
        self.assertIsNotNone(L.sc_lanes(a, b, k)["sel"])
        L.bc_save({"lanes": False}); self.assertEqual(L.sc_lanes(a, b)["lanes"], []); self.assertFalse(L.bc_public()["lanes"])
        L.bc_save({"lanes": True, "clock_warn": 3}); self.assertEqual(L.bc_public()["clock_warn"], 3)
        keep = L.clock_status
        L.clock_status = lambda cfg=None, wait=False: BC.clock_eval([{"kind": "ha", "name": "Home Assistant", "off": 0.2}, {"kind": "phone", "name": "Handy", "off": 4.4}], 3)
        try:
            rows = list(csv.reader(io.StringIO(L.export_csv({}).decode("utf-8").lstrip("\ufeff")), delimiter=";"))
            self.assertIn("Uhrabgleich: Abweichung Home Assistant 0 s, Handy 4 s – mehr als 3 s", rows[-1][1])
            html = L.protocol_html({"all": ["1"]}); html = html.decode() if isinstance(html, bytes) else html
            self.assertIn("Uhrabgleich: Abweichung Home Assistant 0 s, Handy 4 s", html)
            d = L.bc_detail(dict(L.events_summary("all", 50)["events"][0])); self.assertTrue(d["clock"]["warn"])
        finally:
            L.clock_status = keep
        self.unchanged()

    def test_uhr_home_assistant_ueber_date_kopf(self):
        L = self.L
        import email.utils, threading, time as tm
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b'{"message":"API running."}')

            def date_time_string(self, timestamp=None):
                return email.utils.formatdate(tm.time() + 7, usegmt=True)     # HA geht 7 s vor

            def log_message(self, *a):
                pass
        srv = HTTPServer(("127.0.0.1", 0), H); th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
        keep = os.environ.get("LAERM_HA_URL")
        os.environ["LAERM_HA_URL"] = f"http://127.0.0.1:{srv.server_address[1]}/api"
        try:
            off, err = L.clock_ha_check()
            self.assertEqual(err, ""); self.assertTrue(6 <= off <= 8.5, off)
            L.CLOCK.update(ha_at=0.0, busy=False)
            st = L.clock_status(wait=True)
            ha = [x for x in st["items"] if x["kind"] == "ha"][0]
            self.assertIn(ha["off"], (7, 8)); self.assertTrue(st["warn"])              # Standard: Warnung ab 5 s
            L.bc_save({"clock_warn": 10}); L.CLOCK.update(ha_at=0.0, busy=False)
            self.assertFalse(L.clock_status(wait=True)["warn"])
        finally:
            srv.shutdown()
            if keep is None:
                os.environ.pop("LAERM_HA_URL", None)
            else:
                os.environ["LAERM_HA_URL"] = keep
            L.CLOCK.update(ha=None, ha_at=0.0, busy=False, ha_err="")


if __name__ == "__main__":
    unittest.main()


class Uhr(unittest.TestCase):
    def test_uhr_weicht_ab_nicht_beurteilbar(self):
        r = BC.check(T0, "main", sensor(edges=[T0 + 3 * S], clock_from=T0 - 60 * S, clock_off=9))
        self.assertEqual((r["st"], r["why"], r["clock_off"]), ("nb", "clock", 9))
        r = BC.check(T0, "main", sensor(edges=[T0 + 3 * S], clock_from=T0 + 60 * S))      # davor: normal geprüft
        self.assertEqual(r["st"], "ok")


class Kalibrieren(unittest.TestCase):
    def test_verschiebe_test_und_vorschlag(self):
        t0s = [T0 + i * 3600 * S for i in range(30)]
        s = sensor(edges=[t + 3 * S for t in t0s] + [T0 + 1800 * S], pre=5, post=10)
        c = BC.calib(t0s, s)
        self.assertEqual(c["real"], 30); self.assertLess(c["shift_mean"], 5); self.assertLess(c["p"], 0.1)
        self.assertEqual(sum(c["hist"]), 30); self.assertEqual(c["sug"], [1, 4])
        c2 = BC.calib(t0s, sensor(edges=[]))
        self.assertEqual((c2["real"], c2["sug"]), (0, None))

    def test_tag_nacht_grundrate(self):
        import time as _t
        base = int(_t.mktime((2026, 10, 1, 0, 0, 0, 0, 0, -1)) * 1000)
        ed = [base + d * 86400000 + h * 3600000 for d in range(10) for h in (1, 2, 3, 4, 13)]   # 4 nachts, 1 am Tag
        s = sensor(edges=ed, since=base)
        ld, ln = BC.base_rate_split(s, base, base + 10 * 86400000)
        self.assertGreater(ln, ld * 5)
