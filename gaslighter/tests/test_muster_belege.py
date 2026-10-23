"""Musterfilter, Belegdaten (Lärmprotokoll, Beweispaket), Sicherung ohne Geheimnisse, Umzug mit Kennwort,
Grenzen beim Einspielen und Schutz des Handy-Servers.
Grundsatz: Gespeicherte Daten (log.csv, Tagesaufzeichnung, Prüfsummen, Ereignisdateien) bleiben unverändert.
Aufruf (aus gaslighter/):  python3 -m unittest discover -s tests -v"""
import csv, datetime as dt, gzip, hashlib, io, json, os, shutil, ssl, subprocess, sys, tempfile, unittest, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import laerm  # noqa: E402


def sha_tree(root, skip=()):
    out = {}
    for base, _d, files in os.walk(root):
        for fn in files:
            p = os.path.join(base, fn)
            rel = os.path.relpath(p, root)
            if rel in skip:
                continue
            with open(p, "rb") as f:
                out[rel] = hashlib.sha256(f.read()).hexdigest()
    return out


class Umgebung(unittest.TestCase):
    """Wegwerf-Ordner für Ausgabe, Clips und /data; log.csv mit echten Zeilen."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.out = os.path.join(self.tmp, "out"); self.data = os.path.join(self.tmp, "data")
        os.makedirs(os.path.join(self.out, "clips", "tag")); os.makedirs(self.data)
        self.keep = (dict(laerm.CFG), laerm.paths, laerm.DATA_DIR, laerm.SOURCES_FILE, laerm.art_fields, laerm.pro_ok, laerm.LAYOUT_FILE, laerm.day_dir)
        laerm.CFG.update(output_dir=self.out, clip_dir="", language="de", save_audio=False)
        laerm.paths = lambda: (self.out, self.out + "/clips", self.out + "/log.csv")
        laerm.day_dir = lambda: os.path.join(self.out, "clips", "tag")                    # (andere Tests ersetzen day_dir)
        laerm.DATA_DIR = self.data; laerm.SOURCES_FILE = os.path.join(self.data, "sources.json")
        laerm.LAYOUT_FILE = os.path.join(self.data, "layout.json"); laerm.LAYOUT["data"] = None
        laerm.MUSTER["data"] = None; laerm.BEST["data"] = None; laerm.LOG_CACHE["key"] = None
        laerm.CHAIN_KEYS.clear(); laerm.CHAIN_CK.clear(); laerm.CHAIN_FOREIGN.update(p=None, s=set())
        laerm.art_fields = lambda f: {"art": "signal" if str(f).startswith("uhr") else "knock", "art_c": 70, "art_man": False, "kinds": [], "prof": "", "prof_c": None,
                                      "prof_ok": False, "bg": False}
        laerm.pro_ok = lambda: False
        self.now = dt.datetime.now().replace(microsecond=0)
        rows = []
        # Uhrschlag: jede volle Stunde (± 1 Min.) der letzten 3 Tage, dazu Klopfen zu krummen Zeiten
        base = (self.now - dt.timedelta(days=3)).replace(minute=0, second=0)
        for h in range(0, 60):
            t = base + dt.timedelta(hours=h, seconds=40 if h % 2 else -50)
            if t < self.now:
                rows.append(self.row(t, 3.0, -35.0, f"uhr{h}"))
        for i, m in enumerate((17, 23, 41)):
            rows.append(self.row(base + dt.timedelta(hours=5, minutes=m), 12.0, -18.0, f"klopf{i}"))
        rows.sort(key=lambda r: r["start"])
        self.rows = rows
        with open(self.out + "/log.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=laerm.LOG_HEADER); w.writeheader(); w.writerows(rows)

    def tearDown(self):
        laerm.CFG.clear(); laerm.CFG.update(self.keep[0])
        laerm.paths, laerm.DATA_DIR, laerm.SOURCES_FILE, laerm.art_fields, laerm.pro_ok, laerm.LAYOUT_FILE, laerm.day_dir = self.keep[1:]
        laerm.MUSTER["data"] = None; laerm.BEST["data"] = None; laerm.LOG_CACHE["key"] = None; laerm.LAYOUT["data"] = None
        laerm.CHAIN_KEYS.clear(); laerm.CHAIN_CK.clear(); laerm.CHAIN_FOREIGN.update(p=None, s=set())
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def dump(p, obj):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f)

    @staticmethod
    def wbin(p, b):
        with open(p, "wb") as f:
            f.write(b)

    @staticmethod
    def row(t, dur, pk, datei, thr=-40.0, sid="main"):
        return {"start": t.isoformat(timespec="seconds"), "dauer_s": str(dur), "spitze_dbfs": str(pk), "hintergrund_dbfs": "-60", "datei": datei,
                "schwelle_dbfs": str(thr), "clip_s": "", "quelle": "Mic", "quelle_id": sid}


class MusterPruefen(unittest.TestCase):
    """Regeln: Wiederholung, Wochentage, Uhrzeit über Mitternacht, Dauer, Spitze, Abstand zur Schwelle, Zustand in Home Assistant."""

    def ev(self, t, **k):
        return dict({"t": t, "dur": 3.0, "pk": -35.0, "thr": -40.0, "kind": "signal", "dev": "main", "bg": False}, **k)

    def test_wiederholung_volle_stunde(self):
        m = laerm.muster_clean({"rep_every": 60, "rep_off": 0, "rep_tol": 2})
        for hh, mm, ss, hit in ((7, 0, 0, True), (7, 1, 59, True), (6, 58, 30, True), (7, 2, 30, False), (7, 30, 0, False), (6, 57, 0, False)):
            self.assertEqual(laerm.muster_match(m, self.ev(dt.datetime(2026, 10, 19, hh, mm, ss))), hit, (hh, mm, ss))
        m = laerm.muster_clean({"rep_every": 30, "rep_off": 15, "rep_tol": 1})        # alle 30 Min. ab Minute 15: :15 und :45
        self.assertTrue(laerm.muster_match(m, self.ev(dt.datetime(2026, 10, 19, 3, 45, 30))))
        self.assertFalse(laerm.muster_match(m, self.ev(dt.datetime(2026, 10, 19, 3, 30, 0))))

    def test_wochentage_und_uhrzeit(self):
        m = laerm.muster_clean({"wd": [0, 1, 2, 3, 4], "t_from": "22:30", "t_to": "01:00"})        # Mo–Fr, über Mitternacht
        self.assertTrue(laerm.muster_match(m, self.ev(dt.datetime(2026, 10, 19, 23, 10))))    # Montag
        self.assertTrue(laerm.muster_match(m, self.ev(dt.datetime(2026, 10, 20, 0, 40))))     # Dienstag früh
        self.assertFalse(laerm.muster_match(m, self.ev(dt.datetime(2026, 10, 19, 21, 0))))    # zu früh
        self.assertFalse(laerm.muster_match(m, self.ev(dt.datetime(2026, 10, 24, 23, 10))))   # Samstag
        self.assertEqual(laerm.muster_clean({"wd": list(range(7))})["wd"], [])                 # alle Tage = keine Einschränkung

    def test_dauer_spitze_abstand_geraet_art_ha(self):
        m = laerm.muster_clean({"dev": "main", "art": "signal", "dur_min": 1, "dur_max": 5, "pk_min": -40, "pk_max": -30, "over_min": 0, "over_max": 8, "ha": "r_tv"})
        t = dt.datetime(2026, 10, 19, 12, 0)
        self.assertTrue(laerm.muster_match(m, self.ev(t, ha={"r_tv"})))
        self.assertFalse(laerm.muster_match(m, self.ev(t, ha=set())))                         # Fernseher aus
        self.assertFalse(laerm.muster_match(m, self.ev(t, ha={"r_tv"}, dur=9)))
        self.assertFalse(laerm.muster_match(m, self.ev(t, ha={"r_tv"}, pk=-20)))
        self.assertFalse(laerm.muster_match(m, self.ev(t, ha={"r_tv"}, pk=-31, thr=-45)))     # 14 dB über der Schwelle
        self.assertFalse(laerm.muster_match(m, self.ev(t, ha={"r_tv"}, dev="flur")))
        self.assertFalse(laerm.muster_match(m, self.ev(t, ha={"r_tv"}, kind="knock")))
        mb = laerm.muster_clean({"art": "bg"})
        self.assertTrue(laerm.muster_match(mb, self.ev(t, bg=True))); self.assertFalse(laerm.muster_match(mb, self.ev(t)))

    def test_eingaben_bereinigt(self):
        m = laerm.muster_clean({"name": "<b>Uhr</b>" + "x" * 99, "color": "red", "t_from": "25:00", "t_to": "07:00", "dur_min": 9, "dur_max": 2, "rep_every": 1, "wd": ["1", 9, "x"]})
        self.assertNotIn("<", m["name"]); self.assertLessEqual(len(m["name"]), 60); self.assertEqual(m["color"], "#868e96")
        self.assertEqual((m["t_from"], m["t_to"]), ("", "")); self.assertEqual((m["dur_min"], m["dur_max"]), (2, 9))
        self.assertEqual(m["rep_every"], 0); self.assertEqual(m["wd"], [1])


class MusterWirkung(Umgebung):
    def test_vorschau_zaehlt_letzte_30_tage(self):
        pv = laerm.muster_preview({"rep_every": 60, "rep_off": 0, "rep_tol": 2, "art": "signal"})
        n_uhr = sum(1 for r in self.rows if r["datei"].startswith("uhr"))
        self.assertTrue(pv["ok"]); self.assertEqual(pv["n"], n_uhr); self.assertEqual(pv["of"], len(self.rows)); self.assertEqual(pv["days"], 30)
        self.assertLessEqual(len(pv["examples"]), 5)
        old = self.row(self.now - dt.timedelta(days=40), 3.0, -35.0, "uhr_alt")       # älter als 30 Tage: zählt nicht
        with open(self.out + "/log.csv", "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=laerm.LOG_HEADER).writerow(old)
        laerm.LOG_CACHE["key"] = None
        self.assertEqual(laerm.muster_preview({"rep_every": 60, "rep_tol": 2, "art": "signal"})["n"], n_uhr)

    def test_ein_muster_frei_mehr_mit_pro(self):
        j = laerm.muster_change({"action": "add", "def": {"name": "Uhrschlag", "rep_every": 60, "rep_tol": 2}})
        self.assertTrue(j["ok"])
        self.assertEqual(laerm.muster_change({"action": "add", "def": {"name": "Zwei"}})["error"], "pro")
        laerm.pro_ok = lambda: True
        self.assertTrue(laerm.muster_change({"action": "add", "def": {"name": "Zwei", "art": "knock"}})["ok"])
        self.assertEqual(len(laerm.muster_active()), 2)
        laerm.pro_ok = lambda: False                                                        # Pro abgelaufen: beide bleiben gespeichert, das erste gilt
        self.assertEqual([m["name"] for m in laerm.muster_active()], ["Uhrschlag"]); self.assertEqual(len(laerm.muster_list()), 2)

    def test_nichts_gespeichertes_aendert_sich(self):
        # Tagesaufzeichnung und Kette wie im Betrieb
        laerm.CFG["output_dir"] = self.out
        day = self.now.date().isoformat(); t0 = int(dt.datetime.combine(self.now.date(), dt.time(1, 0)).timestamp() * 1000)
        lines = [json.dumps({"m": t0 + i * 60000, "r": [[0, -40, -50, -60, -45, 0]]}, separators=(",", ":")) for i in range(5)]
        with open(laerm.day_path("main", day), "wb") as f:
            f.write(b"".join(gzip.compress((l + "\n").encode()) for l in lines))
        for i, l in enumerate(lines):
            laerm.chain_add("main", day, t0 + i * 60000, l, [])
        with open(os.path.join(self.out, "clips", "ereignisse.jsonl"), "w") as f:
            f.write('{"stem":"x"}\n')
        before = sha_tree(self.tmp)
        laerm.muster_change({"action": "add", "def": {"name": "Uhrschlag", "rep_every": 60, "rep_tol": 2, "art": "signal"}})
        mid = laerm.muster_list()[0]["id"]
        laerm.muster_change({"action": "edit", "id": mid, "def": {"name": "Uhr", "rep_every": 60, "rep_tol": 3, "art": "signal"}})
        laerm.muster_preview({"art": "knock"})
        k = next(k for r, k in zip(laerm.read_log(), laerm.row_keys(laerm.read_log())) if r["datei"] == "klopf0")
        self.assertTrue(laerm.art_confirm(k, "door")["ok"])                                # Art korrigieren: eigene Datei
        ev = laerm.evidence_core(self.now - dt.timedelta(days=5), self.now + dt.timedelta(minutes=1), None, False, True, with_chains=False)
        self.assertGreater(ev["muster"]["n"], 0); self.assertTrue(ev["summary"]["n"] > 0)
        laerm.export_csv({"from": [(self.now - dt.timedelta(days=5)).date().isoformat()]})
        laerm.muster_change({"action": "del", "id": mid})
        after = sha_tree(self.tmp, skip={os.path.join("out", "clips", "muster.json"), os.path.join("out", "clips", "bestaetigt.json")})
        self.assertEqual(before, after)                                                     # log.csv, Tagesdatei, Kette, Ereignisdateien unverändert
        self.assertTrue(os.path.exists(os.path.join(self.out, "clips", "muster.json")))
        with open(os.path.join(self.out, "clips", "bestaetigt.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["a"]["klopf0"]["g"], "door")
        self.assertIn(("clips/muster.json", os.path.join(self.out, "clips", "muster.json")), laerm.backup_items())

    def test_zaehlen_weglassen_und_kennzeichnen(self):
        laerm.muster_change({"action": "add", "def": {"name": "Uhrschlag", "color": "#1c7ed6", "rep_every": 60, "rep_tol": 2, "art": "signal"}})
        n_uhr = sum(1 for r in self.rows if r["datei"].startswith("uhr"))
        a, b = self.now - dt.timedelta(days=5), self.now + dt.timedelta(minutes=1)
        mit = laerm.evidence_core(a, b, None, False, True, with_chains=False)
        ohne = laerm.evidence_core(a, b, None, True, True, with_chains=False)
        self.assertEqual(mit["summary"]["n"], len(self.rows)); self.assertEqual(ohne["summary"]["n"], len(self.rows) - n_uhr)
        self.assertEqual(ohne["muster"]["used"], [["Uhrschlag", n_uhr]]); self.assertTrue(ohne["muster"]["omit"])
        self.assertEqual(len(mit["mf_ev"]), n_uhr)
        q = {"from": [a.date().isoformat()], "to": [self.now.date().isoformat()]}
        rows = list(csv.reader(io.StringIO(laerm.export_csv(q).decode("utf-8-sig")), delimiter=";"))
        col = rows[0].index("nach_muster_ausgefiltert")
        self.assertEqual(sum(1 for r in rows[1:] if r[col] == "Uhrschlag"), n_uhr)
        rows2 = list(csv.reader(io.StringIO(laerm.export_csv(dict(q, mfo=["1"])).decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(len(rows2) - 1, len(self.rows) - n_uhr)
        html = laerm.protocol_html(dict(q, all=["1"], mfo=["1"], g=["0"])).decode("utf-8")
        self.assertIn("weggelassen", html); self.assertIn("„Uhrschlag“ " + str(n_uhr) + "×", html)
        html = laerm.protocol_html(dict(q, all=["1"], g=["0"])).decode("utf-8")
        self.assertIn("nach Muster „Uhrschlag“ ausgefiltert", html)
        self.assertNotIn("gerichtsfest", html.lower()); self.assertNotIn("rechtssicher", html.lower())

    def test_kacheln_ohne_ausgefilterte(self):
        laerm.STAT["data"] = None
        a = int((self.now - dt.timedelta(days=5)).timestamp() * 1000); b = int((self.now + dt.timedelta(minutes=1)).timestamp() * 1000)
        voll = laerm.stat_compute({"src": "ev", "metric": "n", "by": "none"}, a, b)["total"]
        laerm.muster_change({"action": "add", "def": {"name": "Uhrschlag", "rep_every": 60, "rep_tol": 2, "art": "signal"}})
        n_uhr = sum(1 for r in self.rows if r["datei"].startswith("uhr"))
        self.assertEqual(laerm.stat_compute({"src": "ev", "metric": "n", "by": "none"}, a, b)["total"], voll - n_uhr)
        self.assertEqual(laerm.stat_compute({"src": "ev", "metric": "n", "by": "none", "mf_show": True}, a, b)["total"], voll)


class Belege(Umgebung):
    def test_zusammenfassung_zeitachse_methode(self):
        a = (self.now - dt.timedelta(days=6)).replace(hour=0, minute=0, second=0); b = self.now + dt.timedelta(minutes=1)
        ev = laerm.evidence_core(a, b, None, False, True, with_chains=False)
        s = ev["summary"]
        self.assertEqual(s["n"], len(self.rows))
        self.assertEqual(len(ev["timeline"]), (b.date() - a.date()).days + 1)              # jeder Tag, auch ohne Störung
        self.assertTrue(any(d["n"] == 0 for d in ev["timeline"]))
        self.assertEqual(sum(d["n"] for d in ev["timeline"]), s["n"])
        self.assertEqual(sum(c for _a, c in s["dur_b"]), s["n"]); self.assertEqual(sum(c for _a, c in s["over"]), s["n"])
        self.assertEqual(sum(s["hours"]), s["n"]); self.assertEqual(sum(s["wd"]), s["n"])
        self.assertEqual(s["peak"]["max"], -18.0)
        m = ev["method"]
        self.assertIn("Mikrofon nicht kalibriert: Werte sind Indizien und ersetzen kein Gutachten", m["calib"])
        self.assertIn("Es wird kein Ton gespeichert", m["audio_txt"])
        self.assertIn("keine rechtsberatung", ev["limits"].lower())
        txt = laerm.evidence_text(ev, True)
        for w in ("Zeitpunkt", "Art", "Intensität", "Dauer", "Häufigkeit", "Messmethode", "Prüfsummen"):
            self.assertIn(w, txt)
        self.assertNotIn("gerichtsfest", txt.lower()); self.assertNotIn("rechtssicher", txt.lower())

    def test_beweispaket(self):
        q = {"from": [(self.now - dt.timedelta(days=4)).date().isoformat()], "to": [self.now.date().isoformat()], "all": ["1"], "g": ["0"]}
        zf = zipfile.ZipFile(io.BytesIO(laerm.evidence_zip(q)))
        names = set(zf.namelist())
        self.assertEqual(names, {"laermprotokoll.html", "ereignisse_rohdaten.csv", "notizen.csv", "zeitachse.csv", "pruefsummen.csv", "zusammenfassung_und_methode.txt"})
        tl = list(csv.reader(io.StringIO(zf.read("zeitachse.csv").decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(tl[0][:3], ["tag", "stoerungen", "aufgezeichnet"]); self.assertEqual(len(tl) - 1, 5)
        self.assertIn("Impulse", zf.read("ereignisse_rohdaten.csv").decode("utf-8-sig").split("\n")[0].replace("impulse", "Impulse"))

    def test_art_vorschlag_und_bestaetigung(self):
        af = {"art": "knock", "art_c": 63.4, "art_man": False}
        self.assertEqual(laerm.art_text(af, True), "Klopfen – Vorschlag der Erkennung (Konfidenz 63 %)".replace("Klopfen", laerm.art_label("knock", True)))
        self.assertTrue(laerm.art_text(dict(af, art_ok=True), True).endswith("(bestätigt)"))


class SicherungOhneGeheimnisse(Umgebung):
    def setUp(self):
        super().setUp()
        self.src = {"sources": [{"id": "main", "type": "local", "name": "Mic"},
                                {"id": "handy", "type": "phone", "name": "Handy", "token": "ab" * 16},
                                {"id": "cam", "type": "url", "name": "Kamera", "url": "rtsp://x", "user": "u", "password": "geheim123"}]}
        with open(laerm.SOURCES_FILE, "w") as f:
            json.dump(self.src, f)
        self.key = {"own": "11" * 32, "since": 1, "known": []}
        self.dump(laerm.chain_key_path(), self.key)
        self.keep2 = (laerm.public_settings, laerm.move_secrets)
        laerm.public_settings = lambda: {"language": "de"}

    def tearDown(self):
        laerm.public_settings, laerm.move_secrets = self.keep2
        super().tearDown()

    def zip_of(self, move=None):
        b = io.BytesIO(); laerm.backup_write(b, move); return zipfile.ZipFile(io.BytesIO(b.getvalue()))

    def test_standard_ohne_schluessel_und_passwoerter(self):
        shutil.copy(laerm.chain_key_path(), os.path.join(self.out, "kette_schluessel.json"))   # auch wenn er im Datenordner läge
        zf = self.zip_of()
        names = zf.namelist()
        self.assertFalse([n for n in names if "kette_schluessel" in n or n.endswith("umzug.enc")])
        sj = zf.read("data/sources.json").decode()
        self.assertNotIn("geheim123", sj); self.assertNotIn("ab" * 16, sj)
        self.assertEqual(json.loads(zf.read("manifest.json"))["secrets"], "none")
        self.assertFalse(any("11" * 32 in zf.read(n).decode("utf-8", "ignore") for n in names if n.endswith(".json")))

    def test_spiegel_ohne_schluessel_und_passwoerter(self):
        ziel = os.path.join(self.tmp, "nas"); os.makedirs(ziel)
        keep = (laerm.mirror_target, laerm.mirror_check_target, laerm.mirror_index_path, laerm.pub)
        laerm.mirror_target = lambda: ziel; laerm.mirror_check_target = lambda d: ""; laerm.mirror_index_path = lambda: os.path.join(self.data, "mirror_idx.json")
        laerm.pub = lambda *a, **k: None; laerm.pro_ok = lambda: True
        try:
            self.assertTrue(laerm.mirror_run("Test"))
        finally:
            laerm.mirror_target, laerm.mirror_check_target, laerm.mirror_index_path, laerm.pub = keep
        alltxt = ""
        for base, _d, files in os.walk(ziel):
            for fn in files:
                self.assertNotIn("kette_schluessel", fn)
                with open(os.path.join(base, fn), encoding="utf-8", errors="ignore") as f:
                    alltxt += f.read()
        self.assertNotIn("geheim123", alltxt); self.assertNotIn("ab" * 16, alltxt); self.assertNotIn("11" * 32, alltxt)

    def test_umzug_mit_kennwort_hin_und_zurueck(self):
        laerm.move_secrets = lambda: {"secrets": {"handy": {"token": "ab" * 16}, "cam": {"password": "geheim123"}}, "chain_key": self.key}
        zf = self.zip_of("richtig-langes-Kennwort")
        self.assertIn("data/umzug.enc", zf.namelist()); self.assertEqual(json.loads(zf.read("manifest.json"))["secrets"], "move")
        enc = zf.read("data/umzug.enc").decode()
        self.assertNotIn("geheim123", enc); self.assertNotIn("11" * 32, enc)
        d = json.loads(laerm.unseal(enc, "richtig-langes-Kennwort"))
        self.assertEqual(d["chain_key"]["own"], "11" * 32); self.assertEqual(d["secrets"]["cam"]["password"], "geheim123")
        with self.assertRaises(ValueError):
            laerm.unseal(enc, "falsches-Kennwort")
        j = json.loads(enc); ct = bytearray(__import__("base64").b64decode(j["ct"])); ct[0] ^= 1
        j["ct"] = __import__("base64").b64encode(bytes(ct)).decode()
        with self.assertRaises(ValueError):                                                 # verändert: Prüfung schlägt an
            laerm.unseal(json.dumps(j), "richtig-langes-Kennwort")
        with self.assertRaises(ValueError):
            laerm.seal(b"x", "kurz")
        self.assertNotEqual(laerm.seal(b"gleich", "12345678"), laerm.seal(b"gleich", "12345678"))   # Salz und Startwert je Datei neu

    def test_umzug_spielt_schluessel_ein(self):
        laerm.move_secrets = lambda: {"secrets": {}, "chain_key": {"own": "22" * 32, "since": 1, "known": []}}
        b = io.BytesIO(); laerm.backup_write(b, "richtig-langes-Kennwort")
        p = os.path.join(self.tmp, "u.zip"); self.wbin(p, b.getvalue())
        os.remove(laerm.chain_key_path()); laerm.CHAIN_KEYS.clear()                         # neues Gerät
        laerm.restore_run(p, False, move_pass="falsch-falsch")
        self.assertEqual(laerm.BK_STATE["state"], "error"); self.assertNotIn("22" * 32, json.dumps(laerm.chain_keys()))
        self.wbin(p, b.getvalue())
        laerm.restore_run(p, False, move_pass="richtig-langes-Kennwort")
        self.assertEqual(laerm.BK_STATE["state"], "done", laerm.BK_STATE.get("msg"))
        self.assertIn("22" * 32, laerm.chain_keys()["known"])

    def test_alte_sicherung_mit_schluessel_wird_angenommen(self):
        p = os.path.join(self.tmp, "alt.zip")
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr("manifest.json", json.dumps({"fmt": laerm.BACKUP_FMT, "v": 1, "app": "1.79.0", "files": 1}))
            zf.writestr("data/kette_schluessel.json", json.dumps({"own": "33" * 32, "since": 1, "known": []}))
        laerm.restore_run(p, False)
        self.assertEqual(laerm.BK_STATE["state"], "done", laerm.BK_STATE.get("msg"))
        self.assertIn("33" * 32, laerm.chain_keys()["known"])

    def test_neue_handy_kennung_ohne_token(self):
        pub = json.loads(laerm.sources_public_json())
        self.assertTrue(all(not x.get("token") and not x.get("password") for x in pub["sources"]))
        laerm.RESTORE_INFO.clear()
        keep = (laerm.load_sources, laerm.save_sources, laerm.add_runner, laerm.pro_strip_source)
        laerm.load_sources = lambda: []; laerm.save_sources = lambda: None; laerm.add_runner = lambda s_: None; laerm.pro_strip_source = lambda s_, cur=None: s_
        try:
            laerm.restore_sources(pub, {})
        finally:
            laerm.load_sources, laerm.save_sources, laerm.add_runner, laerm.pro_strip_source = keep
        with open(laerm.SOURCES_FILE, encoding="utf-8") as f:
            got = {x["id"]: x for x in json.load(f)["sources"]}
        self.assertRegex(got["handy"]["token"], "^[0-9a-f]{32}$"); self.assertNotEqual(got["handy"]["token"], "ab" * 16)
        self.assertEqual(laerm.RESTORE_INFO.get("pair"), ["Handy"]); self.assertEqual(laerm.RESTORE_INFO.get("pw"), ["Kamera"])
        self.assertTrue(got["cam"].get("check")); self.assertNotIn("secret_removed", got["cam"])


class KetteOhneSchluessel(Umgebung):
    DAY = "2026-10-14"

    def write(self, key_hex):
        t0 = int(dt.datetime(2026, 10, 14, 5, 0).timestamp() * 1000)
        lines = [json.dumps({"m": t0 + i * 60000, "r": [[0, 1, 2, 3, 4, 0]]}, separators=(",", ":")) for i in range(5)]
        with open(laerm.day_path("main", self.DAY), "wb") as f:
            f.write(b"".join(gzip.compress((l + "\n").encode()) for l in lines))
        prev = laerm.chain_seed("main", self.DAY); out = []
        for i, l in enumerate(lines):
            prev = laerm.chain_mac(key_hex, prev, l, b""); out.append(f"{t0 + i * 60000} {prev} H")
        with open(laerm.chain_file("main", self.DAY), "w") as f:
            f.write("\n".join(out) + "\n")
        return out

    def test_eingespielt_ohne_schluessel_vollstaendig(self):
        self.dump(laerm.chain_key_path(), {"own": "44" * 32, "since": 1, "known": []}); laerm.CHAIN_KEYS.clear()
        chk = self.write("55" * 32)                                                         # fremder Schlüssel, nicht hier
        c = laerm.chain_check_full("main", self.DAY)
        self.assertFalse(c["ok"])                                                           # auf dem eigenen Gerät: streng
        with open(laerm.chain_file("main", self.DAY)) as f:
            before = f.read()
        laerm.chain_foreign_add({("main", self.DAY)})
        c = laerm.chain_check_full("main", self.DAY)
        self.assertTrue(c["ok"], c); self.assertTrue(c.get("nokey")); self.assertEqual(c["n"], 5)
        self.assertIn("Schlüssel fehlt: Echtheit nur mit Originalgerät prüfbar", laerm.chain_result_text(c, True))
        with open(laerm.chain_file("main", self.DAY)) as f:
            lines = f.read()
        self.assertEqual(lines, before)                                                     # Kette unverändert
        lines = lines.splitlines()                                                          # eine Minute fehlt: weiter erkannt
        with open(laerm.chain_file("main", self.DAY), "w") as f:
            f.write("\n".join(lines[:2] + lines[3:]) + "\n")
        self.assertFalse(laerm.chain_check_full("main", self.DAY)["ok"])
        self.assertEqual(len(chk), 5)

    def test_einspielen_ohne_schluessel_meldet(self):
        self.write("66" * 32)                                                               # Tag eines anderen Geräts
        tag = os.path.join(self.out, "clips", "tag")
        p = os.path.join(self.tmp, "fremd.zip")
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr("manifest.json", json.dumps({"fmt": laerm.BACKUP_FMT, "v": 1, "app": "1.80.0", "files": 2, "secrets": "none"}))
            for fn in os.listdir(tag):
                zf.write(os.path.join(tag, fn), "clips/tag/" + fn)
        shutil.rmtree(tag); os.makedirs(tag)                                                # neues Gerät
        self.dump(laerm.chain_key_path(), {"own": "44" * 32, "since": 1, "known": []}); laerm.CHAIN_KEYS.clear()
        laerm.restore_run(p, False)
        self.assertEqual(laerm.BK_STATE["state"], "done", laerm.BK_STATE.get("msg"))
        self.assertEqual(laerm.BK_STATE["stats"].get("chain_nokey"), 1)
        c = laerm.chain_check("main", self.DAY)
        self.assertTrue(c["ok"]); self.assertTrue(c["nokey"])

    def test_mit_schluessel_aus_umzug_echt(self):
        self.dump(laerm.chain_key_path(), {"own": "44" * 32, "since": 1, "known": ["55" * 32]}); laerm.CHAIN_KEYS.clear()
        self.write("55" * 32); laerm.chain_foreign_add({("main", self.DAY)})
        c = laerm.chain_check_full("main", self.DAY)
        self.assertTrue(c["ok"]); self.assertFalse(c.get("nokey")); self.assertTrue(c["fremd"])


class GrenzenEinspielen(Umgebung):
    def test_zu_viele_eintraege(self):
        p = os.path.join(self.tmp, "viele.zip")
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr("manifest.json", json.dumps({"fmt": laerm.BACKUP_FMT}))
            for i in range(12):
                zf.writestr(f"clips/x{i}.txt", "x")
        keep = laerm.ZIP_MAX_ENTRIES; laerm.ZIP_MAX_ENTRIES = 10
        try:
            with zipfile.ZipFile(p) as zf, self.assertRaises(ValueError):
                laerm.zip_guard(zf, self.out)
            with self.assertRaises(ValueError):
                laerm.backup_preview(p)
            laerm.restore_run(p, False)
            self.assertEqual(laerm.BK_STATE["state"], "error"); self.assertFalse(os.path.exists(os.path.join(self.out, "clips", "x0.txt")))
        finally:
            laerm.ZIP_MAX_ENTRIES = keep

    def test_platz_vor_dem_auspacken(self):
        p = os.path.join(self.tmp, "gross.zip")
        with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps({"fmt": laerm.BACKUP_FMT}))
            zf.writestr("clips/null.bin", b"\0" * (4 * 1024 * 1024))                     # packt sich klein, braucht ausgepackt 4 MB
        keep = laerm.shutil.disk_usage
        laerm.shutil.disk_usage = lambda d: type("U", (), {"free": 1024 * 1024, "total": 0, "used": 0})()
        try:
            with zipfile.ZipFile(p) as zf, self.assertRaises(ValueError) as cm:
                laerm.zip_guard(zf, self.out)
            self.assertIn("zu wenig freier Speicher", str(cm.exception))
        finally:
            laerm.shutil.disk_usage = keep

    def test_gesamtgroesse_ab_erstem_teil(self):
        sent = []

        class H(laerm.Handler):
            def __init__(self, path, body):
                self.path = path; self.headers = {"Content-Length": str(len(body))}; self.rfile = io.BytesIO(body); self.close_connection = False
                self.client_address = ("127.0.0.1", 1); self.command = "POST"

            def js(self, obj, code=200):
                sent.append((code, obj))
        laerm.BK_STATE.update(state="idle")
        H("/restore_part?id=00112233aabbccdd&off=0&total=20", b"x" * 10).restore_part()
        self.assertEqual(sent[-1][1], {"ok": True, "got": 10})
        H("/restore_part?id=00112233aabbccdd&off=10&total=10000000000", b"x" * 10).restore_part()   # Gesamtgröße nachträglich größer: abgelehnt
        self.assertEqual(sent[-1][0], 400)
        H("/restore_part?id=ffffffffffffffff&off=10&total=20", b"x" * 10).restore_part()         # ohne ersten Teil
        self.assertEqual(sent[-1][0], 400)


class ServerSchutz(unittest.TestCase):
    def test_allow_all_nur_genau_eins(self):
        code = "import os,sys;sys.path.insert(0,%r);import laerm;print(laerm.RESTRICT)" % os.path.join(HERE, "..", "app")
        res = {}
        for v in ("1", "true", "yes", "0"):
            env = dict(os.environ, SUPERVISOR_TOKEN="x", LAERM_ALLOW_ALL=v, LAERM_SETTINGS=os.path.join(tempfile.mkdtemp(), "s.json"),
                       LAERM_OPTIONS="/nicht/da.json", LAERM_SOURCES=os.path.join(tempfile.mkdtemp(), "sources.json"))
            res[v] = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120).stdout.strip().splitlines()[-1]
        self.assertEqual(res, {"1": "False", "true": "True", "yes": "True", "0": "True"})

    def test_fehler_kurz_im_browser(self):
        sent = []

        class H(laerm.BaseHandler):
            def __init__(self):
                self.close_connection = False; self.command = "GET"; self.path = "/x?geheim=1"

            def send(self, code, ctype, body, extra=None):
                sent.append((code, body.decode()))
        logs = []
        keep = laerm.log; laerm.log = lambda *a: logs.append(" ".join(map(str, a)))
        try:
            H().fail(ValueError("/data/geheimer/pfad kaputt"))
        finally:
            laerm.log = keep
        self.assertEqual(sent[0][0], 500); self.assertNotIn("geheimer", sent[0][1]); self.assertLess(len(sent[0][1]), 120)
        self.assertTrue(any("geheimer/pfad" in x for x in logs))
        self.assertEqual(laerm.Handler.timeout, 30)

    def test_handy_server_je_adresse_vier(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        srv = laerm.TLSServer(("127.0.0.1", 0), laerm.PhoneHandler, ctx)
        try:
            self.assertEqual(srv.MAX_PER_IP, 4); self.assertLessEqual(srv.HANDSHAKE_S, 3); self.assertGreaterEqual(srv.HANDSHAKE_S, 2)
            self.assertTrue(all(srv.ip_take("10.0.0.5") for _ in range(4)))
            self.assertFalse(srv.ip_take("10.0.0.5")); self.assertTrue(srv.ip_take("10.0.0.6"))
            srv.ip_give("10.0.0.5"); self.assertTrue(srv.ip_take("10.0.0.5"))
        finally:
            srv.server_close()
        laerm.PHONE_DROPS.clear()
        r = type("R", (), {"phone_ip": "10.0.0.7"})()
        self.assertIsNone(laerm.phone_disturbed(r))
        laerm.phone_drop("10.0.0.7", "handshake")
        d = laerm.phone_disturbed(r)
        self.assertEqual((d["why"], d["n"]), ("handshake", 1))
        laerm.PHONE_DROPS["10.0.0.7"][0] -= 3600
        self.assertIsNone(laerm.phone_disturbed(r))


if __name__ == "__main__":
    unittest.main()
