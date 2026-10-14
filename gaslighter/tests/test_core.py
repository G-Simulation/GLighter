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


if __name__ == "__main__":
    unittest.main()
