"""Datenkette mit HMAC-SHA256 (geheimer Schlüssel in /data) – alte Tage mit reinem SHA-256 bleiben prüfbar.
Aufruf (aus gaslighter/):  python3 -m unittest discover -s tests -v"""
import datetime as dt, gzip, hashlib, json, os, shutil, stat, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import laerm                                          # noqa: E402

DAY = "2026-10-14"
SID = "mic"
T0 = int(dt.datetime(2026, 10, 14, 5, 0, 0).timestamp() * 1000)


def rd_lines(p):
    with open(p) as f:
        return f.read().splitlines()


def minute_line(i, v=1):
    return json.dumps({"m": T0 + i * 60000, "r": [[0, v, 2, 3, 4, 0]]}, separators=(",", ":"))


class HmacKette(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.keep = (laerm.DATA_DIR, laerm.day_dir)
        laerm.DATA_DIR = self.tmp; laerm.day_dir = lambda: self.tmp
        laerm.CHAIN_KEYS.clear(); laerm.CHAIN.clear(); laerm.CHAIN_CK.clear()

    def tearDown(self):
        laerm.DATA_DIR, laerm.day_dir = self.keep
        laerm.CHAIN_KEYS.clear(); laerm.CHAIN.clear(); laerm.CHAIN_CK.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_key(self, since, own="11" * 32, known=()):
        with open(laerm.chain_key_path(), "w") as f:
            json.dump({"own": own, "since": since, "known": list(known)}, f)
        laerm.CHAIN_KEYS.clear()

    def write_day(self, lines):
        with open(laerm.day_path(SID, DAY), "wb") as f:
            f.write(b"".join(gzip.compress((l + "\n").encode()) for l in lines))

    def record(self, n=6, start=0):
        """Wie im Betrieb: Minute in die Tagesdatei, dann chain_add."""
        lines = [minute_line(i) for i in range(n)]
        self.write_day(lines)
        for i in range(start, n):
            laerm.chain_add(SID, DAY, T0 + i * 60000, lines[i], [])
        return lines

    def old_chain(self, lines):
        """Kette nach altem Schema (nur SHA-256), wie vor der Umstellung bzw. wie ein Angreifer ohne Schlüssel sie neu rechnet."""
        prev = laerm.chain_seed(SID, DAY); out = []
        for i, l in enumerate(lines):
            prev = hashlib.sha256(prev.encode() + l.encode()).hexdigest(); out.append(f"{T0 + i * 60000} {prev}")
        return out

    def test_schluessel_wird_angelegt_und_behalten(self):
        k = laerm.chain_keys()
        self.assertRegex(k["own"], "^[0-9a-f]{64}$")
        self.assertEqual(stat.S_IMODE(os.stat(laerm.chain_key_path()).st_mode), 0o600)
        laerm.CHAIN_KEYS.clear()
        self.assertEqual(laerm.chain_keys()["own"], k["own"])          # nach Neustart derselbe

    def test_neue_kette_hmac_und_pruefbar(self):
        self.set_key(T0 - 1)
        self.record()
        chk = rd_lines(laerm.chain_file(SID, DAY))
        self.assertTrue(all(l.endswith(" H") for l in chk))
        c = laerm.chain_check_full(SID, DAY)
        self.assertTrue(c["ok"], c); self.assertEqual((c["n"], c["mac"]), (6, "hmac"))

    def test_ohne_schluessel_neu_gerechnet_wird_erkannt(self):
        self.set_key(T0 - 1)
        lines = self.record()
        lines[3] = minute_line(3, v=9)                                 # Wert geändert ...
        self.write_day(lines)
        with open(laerm.chain_file(SID, DAY), "w") as f:               # ... und die Kette ohne Schlüssel neu berechnet (H weggelassen)
            f.write("\n".join(self.old_chain(lines)) + "\n")
        c = laerm.chain_check_full(SID, DAY)
        self.assertFalse(c["ok"]); self.assertEqual(c["bad"], T0)
        with open(laerm.chain_file(SID, DAY), "w") as f:               # mit „H“ und falschem Schlüssel
            f.write("\n".join(l + " H" for l in self.old_chain(lines)) + "\n")
        self.assertFalse(laerm.chain_check_full(SID, DAY)["ok"])

    def test_alte_tage_bleiben_gueltig_und_heissen_alt(self):
        self.set_key(T0 + 10 ** 9)                                     # Umstellung erst nach diesem Tag
        lines = [minute_line(i) for i in range(5)]
        self.write_day(lines)
        with open(laerm.chain_file(SID, DAY), "w") as f:
            f.write("\n".join(self.old_chain(lines)) + "\n")
        c = laerm.chain_check_full(SID, DAY)
        self.assertTrue(c["ok"], c); self.assertEqual(c["mac"], "alt")

    def test_umstellung_mitten_am_tag(self):
        self.set_key(T0 + 3 * 60000)                                   # ab Minute 3 mit HMAC
        lines = [minute_line(i) for i in range(6)]
        self.write_day(lines)
        with open(laerm.chain_file(SID, DAY), "w") as f:
            f.write("\n".join(self.old_chain(lines)[:3]) + "\n")
        for i in range(3, 6):
            laerm.chain_add(SID, DAY, T0 + i * 60000, lines[i], [])
        c = laerm.chain_check_full(SID, DAY)
        self.assertTrue(c["ok"], c); self.assertEqual((c["n"], c["mac"]), (6, "gemischt"))

    def test_abgeschnittene_markierung(self):
        self.set_key(T0 - 1)
        self.record()
        cf = laerm.chain_file(SID, DAY); chk = rd_lines(cf)
        chk[-1] = chk[-1][:-2]                                         # Stromausfall: „ H“ fehlt
        with open(cf, "w") as f:
            f.write("\n".join(chk) + "\n")
        self.assertTrue(laerm.chain_check_full(SID, DAY)["ok"])

    def test_schluessel_aus_sicherung(self):
        self.set_key(T0 - 1, own="22" * 32)                            # anderer Rechner
        self.record()
        self.set_key(T0 - 1, own="33" * 32)                            # hier: eigener, anderer Schlüssel
        self.assertFalse(laerm.chain_check_full(SID, DAY)["ok"])
        self.assertEqual(laerm.chain_keys_merge({"own": "22" * 32, "known": []}), 1)
        c = laerm.chain_check_full(SID, DAY)
        self.assertTrue(c["ok"], c); self.assertTrue(c["fremd"])
        self.assertEqual(laerm.chain_keys()["own"], "33" * 32)         # eigener bleibt

    def test_ohne_speicherbaren_schluessel_weiter_sha256(self):
        laerm.DATA_DIR = os.path.join(self.tmp, "gibt_es_nicht"); laerm.CHAIN_KEYS.clear()
        self.record()
        self.assertFalse(rd_lines(laerm.chain_file(SID, DAY))[0].endswith(" H"))
        self.assertTrue(laerm.chain_check_full(SID, DAY)["ok"])


if __name__ == "__main__":
    unittest.main()
