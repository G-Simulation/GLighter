"""Starter: Updates aus /share nur eingeschaltet und nur mit gültiger Ed25519-Signatur (Domäne GSIM-UPDATE-1).
Aufruf (aus gaslighter/):  python3 -m unittest discover -s tests -v
Test-Schlüsselpaar: der öffentliche Schlüssel wird nur für den Test in lizenz.PUBLIC_KEY_HEX eingesetzt."""
import json, os, shutil, sys, tempfile, unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import aufnahme as A        # noqa: E402
import lizenz               # noqa: E402
import gl_license as GL     # noqa: E402
import gl_sign_update as SU  # noqa: E402

SEED = bytes(range(32))
TEST_PUB = GL._secret_to_pub(SEED)[2].hex()
OTHER_SEED = bytes(range(1, 33))


class SignierteUpdates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.share = os.path.join(self.tmp, "share", "gaslighter_update")
        self.pkg = os.path.join(self.share, "gaslighter", "app")
        os.makedirs(os.path.join(self.pkg, "web"))
        for rel, txt in (("laerm.py", 'VERSION = "9.9.9"\n'), ("lizenz.py", "# echt\n"), ("web/index.html", "<html></html>")):
            with open(os.path.join(self.pkg, rel), "w") as f:
                f.write(txt)
        self.patches = [mock.patch.object(lizenz, "PUBLIC_KEY_HEX", TEST_PUB),
                        mock.patch.object(A, "UPDATE_DIRS", [self.share]),
                        mock.patch.object(A, "RUN_DIR", os.path.join(self.tmp, "data", "update_run")),
                        mock.patch.object(A, "OPTIONS_FILE", os.path.join(self.tmp, "data", "options.json")),
                        mock.patch.dict(os.environ, {"LAERM_SHARE_UPDATE": "1"})]
        for p in self.patches:
            p.start()
        A.VERIFIED.clear(); A.REJECTED.clear()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def dirs(self):
        return A.app_dirs()[1:]

    def test_standard_aus(self):
        SU.sign_dir(SEED, self.pkg)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LAERM_SHARE_UPDATE")
            self.assertEqual(A.app_dirs(), [A.HERE])                      # ohne options.json: aus
            os.makedirs(os.path.dirname(A.OPTIONS_FILE), exist_ok=True)
            with open(A.OPTIONS_FILE, "w") as f:
                json.dump({"share_update": False}, f)
            self.assertEqual(A.app_dirs(), [A.HERE])
            with open(A.OPTIONS_FILE, "w") as f:
                json.dump({"share_update": True}, f)
            self.assertEqual(len(A.app_dirs()), 2)

    def test_unsigniert_abgelehnt(self):
        self.assertEqual(self.dirs(), [])

    def test_signiert_wird_kopie_gestartet(self):
        SU.sign_dir(SEED, self.pkg)
        d = self.dirs()
        self.assertEqual(len(d), 1)
        self.assertTrue(d[0].startswith(A.RUN_DIR))
        with open(os.path.join(d[0], "laerm.py")) as f:
            self.assertIn("9.9.9", f.read())
        with open(os.path.join(self.pkg, "lizenz.py"), "w") as f:      # später in /share geändert ...
            f.write("PRO = True\n")
        with open(os.path.join(d[0], "lizenz.py")) as f:                # ... die geprüfte Kopie bleibt unverändert
            self.assertEqual(f.read(), "# echt\n")
        self.assertEqual(self.dirs(), d)                                # weiter nur die geprüfte Kopie
        shutil.rmtree(A.RUN_DIR); A.VERIFIED.clear()                    # ohne Kopie: geänderte Quelle wird abgelehnt
        self.assertEqual(self.dirs(), [])
        self.assertIn("Prüfsumme", A.REJECTED[self.pkg])

    def test_falscher_schluessel(self):
        SU.sign_dir(OTHER_SEED, self.pkg)
        self.assertEqual(self.dirs(), [])
        self.assertIn("Signatur", A.REJECTED[self.pkg])

    def test_zusatzdatei_abgelehnt(self):
        SU.sign_dir(SEED, self.pkg)
        with open(os.path.join(self.pkg, "suchindex.py"), "w") as f:
            f.write("import os\n")
        self.assertEqual(self.dirs(), [])
        self.assertIn("nicht signierte", A.REJECTED[self.pkg])

    def test_ohne_domaenenpraefix_ungueltig(self):
        man = SU.build_manifest(self.pkg)
        sig = GL.ed25519_sign(SEED, man)                                # Signatur ohne „GSIM-UPDATE-1\n“
        with open(os.path.join(self.pkg, A.MANIFEST), "wb") as f:
            f.write(man)
        with open(os.path.join(self.pkg, A.MANIFEST_SIG), "w") as f:
            f.write(sig.hex())
        self.assertEqual(self.dirs(), [])

    def test_pfad_ausbruch_im_manifest(self):
        with self.assertRaises(ValueError):
            A.parse_manifest(b"0" * 64 + b"  ../../data/lizenz.json\n" + b"0" * 64 + b"  laerm.py\n")
        with self.assertRaises(ValueError):
            A.parse_manifest(b"0" * 64 + b"  /etc/passwd\n")


class DomaenenTrennung(unittest.TestCase):
    """Eine Update-Signatur ist nie eine Lizenz – und eine Lizenz-Signatur nie ein Update."""
    def test_update_signatur_ist_keine_lizenz(self):
        js = json.dumps({"p": "gaslighter", "e": "2099-01-01", "n": "1", "i": "2026-10-19"}, separators=(",", ":")).encode()
        body = bytes([1]) + len(js).to_bytes(2, "big") + js
        import base64
        with mock.patch.object(lizenz, "PUBLIC_KEY_HEX", TEST_PUB):
            good = lizenz.pretty(base64.b32encode(body + GL.ed25519_sign(SEED, body)).decode().rstrip("="))
            self.assertTrue(lizenz.check(good)["ok"])
            bad = lizenz.pretty(base64.b32encode(body + GL.ed25519_sign(SEED, A.SIG_CONTEXT + body)).decode().rstrip("="))
            self.assertEqual(lizenz.check(bad)["error"], "signature")
            self.assertFalse(A.check_signature(body, GL.ed25519_sign(SEED, body).hex().encode()))


if __name__ == "__main__":
    unittest.main()
