"""Pro-Filter: ohne Lizenz gelten die Standardwerte der Erkennung – auch aus dem Reiter Konfiguration und aus dem kostenlosen Import.
Mit gültigem Schlüssel (Format des WordPress-Lizenzservers, hier mit Test-Schlüsselpaar) bleiben alle Pro-Werte erhalten.
Aufruf (aus gaslighter/):  python3 -m unittest discover -s tests -v"""
import base64, datetime as dt, json, os, shutil, struct, sys, tempfile, unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import laerm                 # noqa: E402
import lizenz                # noqa: E402
import gl_license as GL      # noqa: E402

SEED = bytes(range(32))
TEST_PUB = GL._secret_to_pub(SEED)[2].hex()


def wp_key(product="gaslighter", until="2099-12-31", prefix="GL1"):
    """Wie gsimulations-lizenz.php: chr(1) + pack('n', len(json)) + json + Ed25519-Signatur, Base32 ohne Padding, 5er-Gruppen."""
    js = json.dumps({"p": product, "e": until, "n": "4711", "i": dt.date.today().isoformat(), "w": "AB2CD"}, separators=(",", ":")).encode()
    body = b"\x01" + struct.pack(">H", len(js)) + js
    raw = base64.b32encode(body + GL.ed25519_sign(SEED, body)).decode().rstrip("=")
    return prefix + "-" + "-".join(raw[i:i + 5] for i in range(0, len(raw), 5))


class ProFilter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.keep = (laerm.OPTIONS_FILE, laerm.SETTINGS_FILE, laerm.PRO_FILE, dict(laerm.CFG), dict(laerm.CFG_META))
        laerm.OPTIONS_FILE = os.path.join(self.tmp, "options.json"); laerm.SETTINGS_FILE = os.path.join(self.tmp, "settings.json")
        laerm.PRO_FILE = os.path.join(self.tmp, "lizenz.json")
        laerm.PRO_CACHE.update(t=0.0, st=None); laerm.CFG_META.pop("pro_hold", None)
        self.pub = mock.patch.object(lizenz, "PUBLIC_KEY_HEX", TEST_PUB); self.pub.start()
        with open(laerm.OPTIONS_FILE, "w") as f:                       # im Reiter Konfiguration von Hand eingetragen
            json.dump({"offset_db": 12, "thr_mode": "fixed", "min_db": -80, "retention_days": 20}, f)

    def tearDown(self):
        self.pub.stop()
        laerm.OPTIONS_FILE, laerm.SETTINGS_FILE, laerm.PRO_FILE, cfg, meta = self.keep
        laerm.CFG.clear(); laerm.CFG.update(cfg); laerm.CFG_META.clear(); laerm.CFG_META.update(meta)
        laerm.PRO_CACHE.update(t=0.0, st=None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_license(self, key):
        with open(laerm.PRO_FILE, "w") as f:
            json.dump({"key": key}, f)
        laerm.PRO_CACHE.update(t=0.0, st=None)

    def test_ohne_lizenz_standardwerte_aus_konfiguration(self):
        cfg = laerm.load_settings()
        self.assertEqual((cfg["offset_db"], cfg["thr_mode"], cfg["min_db"]), (10, "bounded", -95))
        self.assertEqual(cfg["retention_days"], 20)                    # freie Werte bleiben
        with open(laerm.SETTINGS_FILE) as f:
            self.assertEqual(json.load(f)["offset_db"], 12)            # gespeichert bleibt der eingetragene Wert

    def test_mit_wp_schluessel_bleiben_alle_pro_werte(self):
        self.set_license(wp_key())
        self.assertTrue(laerm.pro_ok())
        cfg = laerm.load_settings()
        self.assertEqual((cfg["offset_db"], cfg["thr_mode"], cfg["min_db"]), (12, "fixed", -80))

    def test_greport_schluessel_schaltet_glighter_nicht_frei(self):
        self.set_license(wp_key(product="greport"))
        self.assertFalse(laerm.pro_ok())
        self.assertEqual(laerm.load_settings()["offset_db"], 10)

    def test_abgelaufen_gilt_als_ohne(self):
        self.set_license(wp_key(until="2020-01-01"))
        self.assertEqual(laerm.load_settings()["offset_db"], 10)

    def test_aktivieren_wendet_zurueckgehaltene_werte_an(self):
        laerm.CFG.update(laerm.load_settings())
        self.assertEqual(laerm.CFG["offset_db"], 10)
        r = laerm.pro_set(wp_key())
        self.assertTrue(r["ok"], r)
        self.assertEqual((laerm.CFG["offset_db"], laerm.CFG["thr_mode"]), (12, "fixed"))

    def test_import_ohne_pro_geraet(self):
        cur = {"id": "mic", "cfg": {"offset_db": 8, "save_audio": False}, "sched": [{"from": "22:00", "to": "06:00", "cfg": {"offset_db": 8}}]}
        inc = {"id": "mic", "name": "x", "cfg": {"offset_db": 3, "thr_mode": "fixed", "save_audio": True},
               "sched": [{"from": "20:00", "to": "07:00", "cfg": {"offset_db": 1}}]}
        out = laerm.pro_strip_source(inc, cur)
        self.assertEqual(out["cfg"], {"offset_db": 8, "save_audio": True})   # Pro-Wert vom Gerät hier, freier Wert aus der Sicherung
        self.assertEqual(out["sched"], cur["sched"])
        self.assertEqual(laerm.pro_strip_source(dict(inc, id="neu"), None)["cfg"], {"save_audio": True})
        self.assertEqual(inc["cfg"]["offset_db"], 3)                   # Eingabe nicht verändert

    def test_import_mit_pro_geraet_unveraendert(self):
        self.set_license(wp_key())
        inc = {"id": "mic", "cfg": {"offset_db": 3}, "sched": [{"from": "20:00", "to": "07:00", "cfg": {"offset_db": 1}}]}
        self.assertEqual(laerm.pro_strip_source(inc, {"id": "mic", "cfg": {}}), inc)


if __name__ == "__main__":
    unittest.main()
