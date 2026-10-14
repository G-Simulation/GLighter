"""Regressionstests für die Datenpfade (ohne Mikrofon, ohne Home Assistant).
Aufruf:  python3 -m unittest discover -s tests -v     (aus dem Ordner gaslighter/)
Jeder Test legt seine Dateien in einem eigenen Wegwerf-Ordner an."""
import csv, datetime as dt, gzip, hashlib, json, os, sys, tempfile, time, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import numpy as np                                    # noqa: E402
import laerm                                          # noqa: E402

DAY = "2026-10-14"
SID = "mic"
T0 = int(dt.datetime(2026, 10, 14, 5, 0, 0).timestamp() * 1000)


def minute_line(i):
    return json.dumps({"m": T0 + i * 60000, "r": [[0, 1, 2, 3, 4, 0]]}, separators=(",", ":"))


def build_day(tmp, n=8, tear_block=None, tear_link=None):
    """Tagesdatei + Kette wie im Betrieb; optional ein Block bzw. eine Summe halb geschrieben (Stromausfall)."""
    laerm.day_dir = lambda: tmp
    prev = laerm.chain_seed(SID, DAY); blocks, links = [], []
    for i in range(n):
        line = minute_line(i)
        h = hashlib.sha256(prev.encode() + line.encode() + b"").hexdigest(); prev = h
        blocks.append(gzip.compress((line + "\n").encode())); links.append(f"{T0 + i * 60000} {h}")
    if tear_block is not None:
        blocks[tear_block] = blocks[tear_block][:15]
    if tear_link is not None:
        links[tear_link] = links[tear_link][:40]
    with open(laerm.day_path(SID, DAY), "wb") as f:
        f.write(b"".join(blocks))
    with open(laerm.chain_file(SID, DAY), "w") as f:
        f.write("\n".join(links) + ("" if tear_link == n - 1 else "\n"))
    return laerm.chain_file(SID, DAY)


class Stromausfall(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_gz_bytes_ueberspringt_halben_block(self):
        build_day(self.tmp, tear_block=3)
        lines, bad = laerm.gz_lines(laerm.day_path(SID, DAY))
        self.assertEqual(len(lines), 7)
        self.assertEqual(bad, 1)

    def test_gz_bytes_intakt(self):
        build_day(self.tmp)
        lines, bad = laerm.gz_lines(laerm.day_path(SID, DAY))
        self.assertEqual((len(lines), bad), (8, 0))

    def test_kette_intakt(self):
        build_day(self.tmp)
        c = laerm.chain_check_full(SID, DAY)
        self.assertTrue(c["ok"]); self.assertEqual(c["n"], 8)

    def test_kette_halber_block_meldet_nur_diese_minute(self):
        build_day(self.tmp, tear_block=3)
        c = laerm.chain_check_full(SID, DAY)
        self.assertFalse(c["ok"]); self.assertTrue(c.get("missing"))
        self.assertEqual(c["miss_list"], [T0 + 3 * 60000])
        self.assertEqual(c["n"], 7)                    # der Rest des Tages bleibt geprueft

    def test_kette_abgeschnittene_summe_ist_kein_fehler(self):
        build_day(self.tmp, tear_link=7)               # letzte Summe halb geschrieben, Block vorhanden
        c = laerm.chain_check_full(SID, DAY)
        self.assertTrue(c["ok"], c)

    def test_kette_veraenderter_wert_wird_erkannt(self):
        build_day(self.tmp)
        lines = [minute_line(i) for i in range(8)]
        lines[4] = lines[4].replace("[0,1,2,3,4,0]", "[0,9,9,9,9,0]")      # nachtraeglich veraendert
        with open(laerm.day_path(SID, DAY), "wb") as f:
            f.write(b"".join(gzip.compress((l + "\n").encode()) for l in lines))
        c = laerm.chain_check_full(SID, DAY)
        self.assertFalse(c["ok"]); self.assertEqual(c["bad"], T0 + 4 * 60000)
        self.assertFalse(c.get("missing"))

    def test_kette_anhaengen_nach_abgeschnittener_zeile(self):
        cf = build_day(self.tmp, tear_link=7)
        laerm.CHAIN.clear()
        laerm.chain_add(SID, DAY, T0 + 8 * 60000, minute_line(8), [])
        txt = open(cf).read().splitlines()
        self.assertEqual(len(txt), 9)                  # abgeschnittene Zeile bleibt eigene Zeile, neue Summe steht sauber dahinter
        self.assertTrue(laerm.HEX64.fullmatch(txt[-1].split()[1]))
        self.assertEqual(txt[-1].split()[0], str(T0 + 8 * 60000))

    def test_feste_saetze_nach_halbem_satz_werden_ausgerichtet(self):
        rl = 8 + 4
        lo, hi = T0 - 1000, T0 + 10 ** 9
        rec = lambda t: int(t).to_bytes(8, "little") + bytes([7, 7, 7, 7])
        raw = rec(T0) + rec(T0 + 1) + rec(T0 + 2)[:5] + rec(T0 + 3) + rec(T0 + 4)     # Strom weg im dritten Satz, danach weitergeschrieben
        out, skipped = laerm.realign_records(raw, rl, lo, hi)
        ts = [int.from_bytes(out[i:i + 8], "little") for i in range(0, len(out), rl)]
        self.assertEqual(ts, [T0, T0 + 1, T0 + 3, T0 + 4])
        self.assertGreater(skipped, 0)

    def test_auffuellen_haelt_ausrichtung(self):
        p = os.path.join(self.tmp, "x.ltp"); rl = 12
        with open(p, "wb") as f:
            f.write(b"a" * 25)
        laerm._PADDED.discard(p)
        laerm.pad_tail(p, rl)
        self.assertEqual(os.path.getsize(p) % rl, 0)


class HomeAssistant(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.f = os.path.join(self.tmp, "ha_zustand.csv")
        laerm.ha_hist_path = lambda: self.f
        laerm.DATA_DIR = self.tmp
        self.now = int(time.time() * 1000)
        self.iso = lambda ms: dt.datetime.fromtimestamp(ms / 1000).astimezone().isoformat(timespec="milliseconds")
        self.rule = {"id": "r1", "entity": "binary_sensor.x", "src": "all", "label": "Heiz", "states": ["on"], "mode": "event", "enabled": True, "color": ""}
        laerm.rule_match = lambda st, v: v == "on"
        laerm.ha_note_all = lambda: {}
        laerm.HA_RULES[:] = [self.rule]
        laerm.HA_HIST.update(key=None, rows=[])
        laerm.RUN_DOWNS.update(key=None, v=[])

    def write_rows(self, rows):
        with open(self.f, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["zeit", "regel", "name", "entitaet", "zustand", "an", "geraet"])
            for t, on in rows:
                w.writerow([self.iso(t), "r1", "Heiz", "binary_sensor.x", "on" if on else "off", 1 if on else 0, "all"])

    def test_abgleich_holt_verpasstes_aus_nach(self):
        a = self.now - 5 * 3600000
        self.write_rows([(a, True)])                    # „Frei“ wurde nie mitgeschrieben
        laerm.ha_get = lambda *x, **k: [[{"entity_id": "binary_sensor.x", "state": "off", "last_changed": self.iso(self.now - 20 * 3600000)},
                                          {"state": "on", "last_changed": self.iso(a)}, {"state": "off", "last_changed": self.iso(a + 6000)}]]
        self.assertEqual(laerm.ha_heal([self.rule], self.now), 1)
        rows = list(csv.DictReader(open(self.f)))
        self.assertEqual([r["an"] for r in rows], ["1", "0"])
        self.assertEqual(laerm.ha_heal([self.rule], self.now), 0)       # zweiter Lauf: nichts mehr zu tun
        self.assertTrue(os.path.exists(self.f + ".bak"))

    def test_intervall_endet_an_luecke(self):
        a = self.now - 5 * 3600000
        self.write_rows([(a, True), (a + 4 * 3600000, False)])         # „Aus“ kam erst nach dem Neustart
        d0 = a + 3600000
        with open(os.path.join(self.tmp, "laufzeit.jsonl"), "w") as fh:
            fh.write(json.dumps({"kind": "down", "from": self.iso(d0), "to": self.iso(d0 + 3000000)}) + "\n")
        out = laerm.ha_intervals("*", a - 1000, self.now)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0][1], int(laerm.ms_of(self.iso(d0))))     # endet am Beginn der Luecke, nicht erst beim spaeteren „Aus“

    def test_intervall_ohne_luecke_bleibt(self):
        a = self.now - 5 * 3600000
        self.write_rows([(a, True), (a + 6000, False)])
        out = laerm.ha_intervals("*", a - 1000, self.now)
        self.assertEqual(out[0][1] - out[0][0], 6000)


class Meldungen(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        laerm.DATA_DIR = self.tmp; laerm.day_dir = lambda: os.path.join(self.tmp, "tag")
        laerm.data_gaps = lambda *a, **k: []
        laerm.RUN_DOWNS.update(key=None, v=[])
        ev = [{"kind": "down", "from": "2026-10-14T05:38:19+02:00", "to": "2026-10-14T09:21:43+02:00", "version_new": "1.51.6"},
              {"kind": "update", "at": "2026-10-14T11:00:00+02:00", "version_old": "1", "version_new": "2"}]
        with open(os.path.join(self.tmp, "laufzeit.jsonl"), "w") as f:
            f.write("\n".join(json.dumps(e) for e in ev) + "\n")
        self.rng = (laerm.ms_of("2026-10-14T00:00:00+02:00"), laerm.ms_of("2026-10-14T23:00:00+02:00"))

    def events(self):
        return {e["kind"]: e for e in laerm.runtime_info(*self.rng)["events"]}

    def test_update_gilt_als_gelesen_stromausfall_ist_offen(self):
        e = self.events()
        self.assertTrue(e["update"]["ack"]); self.assertEqual(e["update"]["ack_by"], "auto")
        self.assertFalse(e["down"]["ack"])

    def test_bestaetigen_und_wieder_oeffnen(self):
        k = self.events()["down"]["key"]
        self.assertTrue(laerm.run_ack_set([k], True)["ok"])
        self.assertTrue(self.events()["down"]["ack"])
        laerm.run_ack_set([k], False)
        self.assertFalse(self.events()["down"]["ack"])

    def test_kette_halbe_minute_beim_stromausfall_ist_kein_fehler(self):
        os.makedirs(laerm.day_dir(), exist_ok=True)
        t0 = laerm.ms_of("2026-10-14T05:30:00+02:00")
        prev = laerm.chain_seed(SID, DAY); blocks, links = [], []
        for i in range(10):
            line = json.dumps({"m": t0 + i * 60000, "r": [[0, 1, 2, 3, 4, 0]]}, separators=(",", ":"))
            h = hashlib.sha256(prev.encode() + line.encode() + b"").hexdigest(); prev = h
            blocks.append(gzip.compress((line + "\n").encode())); links.append(f"{t0 + i * 60000} {h}")
        blocks[7] = blocks[7][:15]                      # Minute 05:37, danach 05:38:19 Strom weg
        open(laerm.day_path(SID, DAY), "wb").write(b"".join(blocks))
        open(laerm.chain_file(SID, DAY), "w").write("\n".join(links) + "\n")
        c = [x for x in laerm.runtime_info(*self.rng)["chains"] if x["day"] == DAY][0]
        self.assertTrue(c["ok"], c); self.assertEqual(c.get("explained"), 1)


class NotizAusHA(unittest.TestCase):
    """Textfeld/Knopf im Home-Assistant-Dashboard legen eine freie Notiz an."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        laerm.paths = lambda: (self.tmp, self.tmp)
        laerm.NOTES["data"] = None
        laerm.fnote_target = lambda *a, **k: None
        laerm.pub = lambda *a, **k: None
        laerm.HA_NOTE_LAST[:] = [0.0, ""]

    def notizen(self):
        return laerm.notes_all().get("free", [])

    def test_text_wird_notiz(self):
        laerm.ha_note_cmd("Klopfen von oben")
        n = self.notizen()
        self.assertEqual(len(n), 1); self.assertEqual(n[0]["text"], "Klopfen von oben")

    def test_knopf_ohne_text_markiert_stoerung(self):
        laerm.ha_note_cmd("")
        self.assertIn("Störung", self.notizen()[0]["text"])

    def test_doppelt_gesendet_zaehlt_einmal(self):
        laerm.ha_note_cmd("x"); laerm.ha_note_cmd("x")
        self.assertEqual(len(self.notizen()), 1)

    def test_unknown_wird_ignoriert(self):
        laerm.ha_note_cmd("unknown")
        self.assertEqual(len(self.notizen()), 0)


class SchwelleAutomatisch(unittest.TestCase):
    """Vorschlag für die Schwelle aus gespeicherten Pegeln: Störungen zählen nicht mit, gestörte Messung wird erkannt."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.keep = (laerm.day_dir, dict(laerm.RUNNERS))
        laerm.day_dir = lambda: self.tmp
        class R:                                            # Gerät ohne laufende Aufnahme
            id = "mic"; name = "Testmikro"; spur = []
            import threading as _t; rlock = _t.Lock()
        laerm.RUNNERS.clear(); laerm.RUNNERS["mic"] = R()
        laerm.DAY_CACHE.clear()

    def tearDown(self):
        laerm.day_dir = self.keep[0]; laerm.RUNNERS.clear(); laerm.RUNNERS.update(self.keep[1]); laerm.DAY_CACHE.clear()

    def write(self, t0, minutes, level, act_every=0, loud_every=0):
        rng = np.random.default_rng(1); blocks = []
        for m in range(minutes):
            rows = []
            for k in range(480):
                eq = level + rng.normal(0, 1.5); a = 0
                if act_every and (m * 480 + k) % act_every == 0:
                    eq, a = level + 30, 1
                if loud_every and (m * 480 + k) % loud_every < 40:
                    eq = level + 25
                rows.append([k * 125, int(eq * 10) + 5, int(eq * 10), int(level * 10), int((level + 10) * 10), a])
            blocks.append(gzip.compress((json.dumps({"m": t0 + m * 60000, "r": rows}) + "\n").encode()))
        day = dt.datetime.fromtimestamp(t0 / 1000).date().isoformat()
        with open(laerm.day_path("mic", day), "ab") as f:
            f.write(b"".join(blocks))

    def test_jetzt_messen(self):
        t0 = int(time.time() * 1000) - 120000; t0 -= t0 % 60000
        self.write(t0, 2, -62.0)
        j = laerm.thr_suggest("mic", "now", t0, t0 + 120000)
        self.assertTrue(j["ok"], j); self.assertFalse(j["disturbed"])
        self.assertAlmostEqual(j["p50"], -62.0, delta=1.0)
        self.assertTrue(6 <= j["sugg"]["offset_db"] <= 20); self.assertLess(j["sugg"]["min_db"], -55)

    def test_gestoerte_messung(self):
        t0 = int(time.time() * 1000) - 120000; t0 -= t0 % 60000
        self.write(t0, 2, -62.0, loud_every=400)          # 10 % der Zeit deutlich lauter (Reden)
        j = laerm.thr_suggest("mic", "now", t0, t0 + 120000)
        self.assertTrue(j["ok"]); self.assertTrue(j["disturbed"])

    def test_letzte_nacht_ohne_stoerungen(self):
        laerm.CFG.update(quiet_from="01:00", quiet_to="02:00")
        now = dt.datetime.now(); end = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if end > now: end -= dt.timedelta(days=1)
        t0 = int((end - dt.timedelta(hours=1)).timestamp() * 1000)
        self.write(t0, 60, -58.0, act_every=97)            # einzelne Störungen dazwischen
        j = laerm.thr_suggest("mic", "night")
        self.assertTrue(j["ok"], j); self.assertGreater(j["events"], 0)
        self.assertLess(j["p95"], -50)                     # Störungen (+30 dB) ziehen den Vorschlag nicht hoch

    def test_ohne_daten(self):
        j = laerm.thr_suggest("mic", "now", int(time.time() * 1000) - 60000, int(time.time() * 1000))
        self.assertFalse(j["ok"]); self.assertEqual(j["error"], "nodata")


class SicherungsZiel(unittest.TestCase):
    """Tägliche Sicherung: inkrementell, nichts geht verloren, Auslagern lässt Protokolle weiter lesen."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.out = os.path.join(self.tmp, "out"); self.dst = os.path.join(self.tmp, "nas")
        os.makedirs(os.path.join(self.out, "clips", "tag")); os.makedirs(self.dst)
        self.f = os.path.join(self.out, "clips", "tag", "mic_2026-01-01.ltd")
        open(self.f, "wb").write(b"alt" * 1000)
        self.keep = (laerm.DATA_DIR, laerm.backup_items, laerm.public_settings, dict(laerm.CFG), laerm.pro_ok)
        laerm.DATA_DIR = self.tmp; laerm.pro_ok = lambda: True
        laerm.backup_items = lambda: [("clips/tag/mic_2026-01-01.ltd", self.f)]
        laerm.public_settings = lambda: {"x": 1}
        laerm.CFG.update(output_dir=self.out, mirror_dir=self.dst, mirror_offload=False, retention_days=30)
        os.environ["LAERM_MIRROR_SAMEDEV"] = "1"

    def tearDown(self):
        laerm.DATA_DIR, laerm.backup_items, laerm.public_settings, cfg, laerm.pro_ok = self.keep
        laerm.CFG.clear(); laerm.CFG.update(cfg); os.environ.pop("LAERM_MIRROR_SAMEDEV", None)

    def test_inkrementell_und_alte_fassung(self):
        self.assertTrue(laerm.mirror_run("test")); self.assertEqual(laerm.MIRROR["copied"], 2)
        d = os.path.join(self.dst, "clips", "tag", "mic_2026-01-01.ltd")
        self.assertEqual(open(d, "rb").read(), b"alt" * 1000)
        self.assertTrue(laerm.mirror_run("test")); self.assertEqual(laerm.MIRROR["copied"], 0)   # nichts Neues: nichts kopiert
        old = time.time() - 3 * 86400; os.utime(d, (old, old))
        open(self.f, "wb").write(b"neu")                       # nachträglich geändert: alte Fassung bleibt im Ziel
        self.assertTrue(laerm.mirror_run("test"))
        self.assertEqual(open(d, "rb").read(), b"neu")
        alts = [x for x in os.listdir(os.path.dirname(d)) if ".alt-" in x]
        self.assertEqual(len(alts), 1)

    def test_auslagern_liest_weiter(self):
        old = time.time() - 60 * 86400; os.utime(self.f, (old, old))
        laerm.CFG["mirror_offload"] = True
        self.assertTrue(laerm.mirror_run("test"))
        self.assertTrue(os.path.islink(self.f))
        self.assertEqual(open(self.f, "rb").read(), b"alt" * 1000)   # Protokolle lesen weiter (aus dem Ziel)
        self.assertTrue(laerm.mirror_verified(self.f))
        self.assertTrue(laerm.mirror_run("test"))                   # zweiter Lauf: ausgelagerte Datei bleibt, nichts kaputt
        self.assertTrue(os.path.isfile(os.path.join(self.dst, "clips", "tag", "mic_2026-01-01.ltd")))

    def test_nur_mit_pro(self):
        laerm.pro_ok = lambda: False
        self.assertFalse(laerm.mirror_run("test")); self.assertEqual(laerm.MIRROR["error"], "pro")
        self.assertEqual(os.listdir(self.dst), [])                 # ohne Pro wird nichts kopiert

    def test_ziel_fehlt(self):
        laerm.CFG["mirror_dir"] = os.path.join(self.tmp, "nicht_da")
        self.assertFalse(laerm.mirror_run("test")); self.assertFalse(laerm.MIRROR["ok"])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "nicht_da")))   # legt nichts auf dem eigenen Speicher an

    def test_gleicher_speicher_abgelehnt(self):
        os.environ.pop("LAERM_MIRROR_SAMEDEV", None)
        self.assertIn("demselben Speicher", laerm.mirror_check_target(self.dst))


class ArtStumm(unittest.TestCase):
    def test_liste(self):
        laerm.CFG["art_silent"] = laerm.clean_value("art_silent", "animal,knock") if hasattr(laerm, "clean_value") else "animal,knock"
        self.assertEqual(laerm.art_silent_set(), {"animal", "knock"})
        laerm.CFG["art_silent"] = ""
        self.assertEqual(laerm.art_silent_set(), set())


class RegelKeineStoerung(unittest.TestCase):
    """Regel-Art „keine Störung melden“: Graph läuft weiter, es wird nur nichts als Störung erkannt."""
    def setUp(self):
        self.r = laerm.clean_rules([{"id": "q1", "entity": "binary_sensor.tuer", "states": "on", "after_min": 10, "max_h": 1, "mode": "quiet"},
                                    {"id": "p1", "entity": "binary_sensor.fenster", "states": "on", "mode": "pause"}])
        laerm.HA_RULES[:] = self.r
        laerm.HA_STATE.clear()

    def test_modus_bleibt_erhalten(self):
        self.assertEqual([x["mode"] for x in self.r], ["quiet", "pause"])
        self.assertEqual(self.r[0]["after_min"], 10.0)

    def test_hervorheben_nur_echtes_true(self):
        r = laerm.clean_rules([{"id": "a", "entity": "binary_sensor.x", "mode": "event", "big": True},
                               {"id": "b", "entity": "binary_sensor.y", "mode": "event", "big": "ja"}])
        self.assertEqual([x["big"] for x in r], [True, False])

    def test_aktiv_und_nachlauf(self):
        laerm.HA_STATE["q1"] = {"hold": True, "active": True, "state": "on", "name": "Tür"}
        self.assertIsNotNone(laerm.ha_quiet_for("x"))
        self.assertIsNone(laerm.ha_hold_for("x"))               # pausiert die Aufnahme nicht (Graph läuft weiter)
        laerm.HA_STATE["q1"] = {"hold": True, "active": False, "until": time.time() + 300, "state": "off", "name": "Tür"}
        self.assertIsNotNone(laerm.ha_quiet_for("x"))           # Nachlauf (10 min) gilt noch
        laerm.HA_STATE["q1"] = {"hold": True, "active": False, "until": time.time() - 1, "state": "off", "name": "Tür"}
        self.assertIsNone(laerm.ha_quiet_for("x"))              # Nachlauf vorbei

    def test_pausenregel_zaehlt_nicht_als_ruhig(self):
        laerm.HA_STATE["p1"] = {"hold": True, "active": True, "state": "on", "name": "Fenster"}
        self.assertIsNone(laerm.ha_quiet_for("x")); self.assertIsNotNone(laerm.ha_hold_for("x"))

    def test_gerätefilter(self):
        laerm.HA_RULES[0]["src"] = "mic1"
        laerm.HA_STATE["q1"] = {"hold": True, "active": True, "state": "on", "name": "Tür"}
        self.assertIsNone(laerm.ha_quiet_for("mic2")); self.assertIsNotNone(laerm.ha_quiet_for("mic1"))


class RuheKnopf(unittest.TestCase):
    """Knopf/Dauer aus Home Assistant: keine Störung melden für eine einstellbare Zeit."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        laerm.SETTINGS_FILE = os.path.join(self.tmp, "settings.json")
        laerm.paths = lambda: (self.tmp, self.tmp)
        laerm.pub = lambda *a, **k: None
        laerm.HA_RULES[:] = []; laerm.HA_STATE.clear()
        laerm.QUIET.update(until=0.0, minutes=10.0)

    def test_standarddauer_zehn_minuten(self):
        self.assertTrue(laerm.quiet_start())
        q = laerm.ha_quiet_for("irgendein_geraet")
        self.assertIsNotNone(q)
        self.assertAlmostEqual(laerm.QUIET["until"] - time.time(), 600, delta=3)

    def test_dauer_einstellbar_und_begrenzt(self):
        laerm.quiet_set_minutes("25"); self.assertEqual(laerm.QUIET["minutes"], 25.0)
        laerm.quiet_set_minutes("9999"); self.assertEqual(laerm.QUIET["minutes"], 240.0)
        laerm.quiet_set_minutes("abc"); self.assertEqual(laerm.QUIET["minutes"], 240.0)
        laerm.quiet_set_minutes("25"); laerm.quiet_start()
        self.assertAlmostEqual(laerm.QUIET["until"] - time.time(), 1500, delta=3)

    def test_stop_und_ablauf(self):
        laerm.quiet_start(5); laerm.quiet_stop()
        self.assertIsNone(laerm.ha_quiet_for("x"))
        laerm.QUIET["until"] = time.time() - 1
        self.assertIsNone(laerm.ha_quiet_for("x"))

    def test_ueberlebt_neustart(self):
        laerm.quiet_set_minutes(15); laerm.quiet_start()
        u = laerm.QUIET["until"]; laerm.QUIET.update(until=0.0, minutes=10.0)
        laerm.quiet_load()
        self.assertEqual(laerm.QUIET["minutes"], 15.0); self.assertAlmostEqual(laerm.QUIET["until"], u, delta=1)

    def test_ungueltige_dauer(self):
        self.assertFalse(laerm.quiet_start("0")); self.assertFalse(laerm.quiet_start("x")); self.assertFalse(laerm.quiet_start("nan"))


if __name__ == "__main__":
    unittest.main()
