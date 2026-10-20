"""GJarvis: Oberfläche nur über Ingress, API-Schlüssel nur an die eingetragene KI-Adresse.
Aufruf (aus gjarvis/):  python3 -m unittest discover -s tests -v
Braucht aiohttp + pyyaml; webrtcvad und wyoming werden für den Test durch Attrappen ersetzt."""
import os, sys, types, unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
for name, attrs in {"webrtcvad": ["Vad"], "wyoming": [], "wyoming.asr": ["Transcribe", "Transcript"],
                    "wyoming.audio": ["AudioChunk", "AudioStart", "AudioStop"], "wyoming.client": ["AsyncTcpClient"],
                    "wyoming.tts": ["Synthesize", "SynthesizeVoice"]}.items():
    if name not in sys.modules:
        try:
            __import__(name)
        except ImportError:
            m = types.ModuleType(name)
            for a in attrs:
                setattr(m, a, type(a, (), {}))
            sys.modules[name] = m

from aiohttp.test_utils import AioHTTPTestCase  # noqa: E402
import web  # noqa: E402
import gjarvis  # noqa: E402


class FakeGJ:
    raw, o, restart_pending = {}, {}, False

    def status(self):
        return {"state": "idle"}

    def pro_state(self):
        return {"ok": False}


class IngressNurHA(AioHTTPTestCase):
    async def get_application(self):
        return web.make_app(FakeGJ())

    async def test_fremde_ip_403(self):
        with mock.patch.object(web, "RESTRICT", True), mock.patch.object(web, "ALLOWED", {"172.30.32.2"}):
            for path in ("/api/status", "/api/settings", "/"):
                r = await self.client.request("GET", path)
                self.assertEqual(r.status, 403, path)
            r = await self.client.request("POST", "/api/ask", json={"text": "Licht aus"})
            self.assertEqual(r.status, 403)

    async def test_ingress_erlaubt(self):
        with mock.patch.object(web, "RESTRICT", True):              # Testclient kommt von 127.0.0.1 (wie Ingress erlaubt)
            r = await self.client.request("GET", "/api/status")
            self.assertEqual(r.status, 200)
            self.assertEqual((await r.json())["state"], "idle")

    def test_client_ip(self):
        self.assertEqual(web.client_ip("::ffff:172.30.32.2"), "172.30.32.2")
        self.assertIn(web.client_ip("::ffff:172.30.32.2"), web.ALLOWED)
        self.assertNotIn(web.client_ip("172.30.33.5"), web.ALLOWED)


class SchluesselNurAnEigeneUrl(unittest.TestCase):
    def setUp(self):
        self.gj = gjarvis.GJarvis.__new__(gjarvis.GJarvis)
        self.gj.o = {"research_llm_type": "openai", "research_llm_url": "http://ki.lan:1234/v1/", "research_llm_api_key": "GEHEIM"}
        self.calls = []

        def fake_get(url, timeout=None, headers=None):
            self.calls.append((url, headers or {}))
            r = mock.Mock(); r.raise_for_status = lambda: None; r.json = lambda: {"data": [{"id": "m1"}]}
            return r
        self.p = mock.patch.object(gjarvis.requests, "get", side_effect=fake_get); self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_eigene_url_bekommt_schluessel(self):
        self.gj.llm_models("openai", "http://KI.lan:1234", None)
        self.assertEqual(self.calls[-1][1].get("Authorization"), "Bearer GEHEIM")
        self.gj.llm_models("openai", None, None)                    # ohne url = eingetragene Adresse
        self.assertEqual(self.calls[-1][1].get("Authorization"), "Bearer GEHEIM")

    def test_fremde_url_ohne_schluessel(self):
        self.gj.llm_models("openai", "http://angreifer.example", None)
        self.assertEqual(self.calls[-1][0], "http://angreifer.example/v1/models")
        self.assertNotIn("Authorization", self.calls[-1][1])

    def test_fremde_url_mit_ausdruecklichem_schluessel(self):
        self.gj.llm_models("openai", "http://andere.lan", "EIGENER")
        self.assertEqual(self.calls[-1][1].get("Authorization"), "Bearer EIGENER")

    def test_ohne_eingetragene_url_nie_schluessel(self):
        self.gj.o["research_llm_url"] = ""
        self.gj.llm_models("openai", "http://x.lan", None)
        self.assertNotIn("Authorization", self.calls[-1][1])


class WhisperOhneManagerRolle(unittest.TestCase):
    def test_403_gibt_anleitung(self):
        gj = gjarvis.GJarvis.__new__(gjarvis.GJarvis)
        gj.o = {"language": "de"}
        gj.whisper_slug = lambda: "core_whisper"
        gj.whisper_prompt = lambda: "Licht an. Licht aus."

        def sup(method, path, **kw):
            if method == "GET":
                return {"options": {"language": "en", "beam_size": 5, "model": "small-int8"}}
            resp = mock.Mock(status_code=403)
            raise gjarvis.requests.HTTPError("403", response=resp)
        gj.sup = sup
        with self.assertRaises(RuntimeError) as cm:
            gj.whisper_setup()
        self.assertIn("language = 'de'", str(cm.exception))
        self.assertIn("beam_size = 1", str(cm.exception))


class Konfiguration(unittest.TestCase):
    def test_rolle_und_share(self):
        import yaml
        with open(os.path.join(HERE, "..", "config.yaml"), encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        self.assertEqual(cfg.get("hassio_role", "default"), "default")
        self.assertNotIn("share:rw", cfg.get("map") or [])


if __name__ == "__main__":
    unittest.main()
