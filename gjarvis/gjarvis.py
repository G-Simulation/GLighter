#!/usr/bin/env python3
"""GJarvis – eigener Sprachassistent als Home-Assistant-App.

Ablauf:
  Weckwort (openWakeWord, Modell per URL)  ->  Rückmeldung ("Ja, Moses?")
  -> zuhören (VAD, Abbruch bei Stille)  ->  Whisper (Wyoming)
  -> Home-Assistant-Agent (z. B. Ollama "KI Zuhause")  ->  Piper (Wyoming)
  -> zurück in Bereitschaft.

Während GJarvis selbst spricht, wird das Mikrofon ignoriert (kein Selbst-Hören).
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import requests
import webrtcvad
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncTcpClient
from wyoming.tts import Synthesize, SynthesizeVoice

OPTIONS_FILE = Path(os.environ.get("GJARVIS_OPTIONS", "/data/options.json"))
DATA_DIR = Path(os.environ.get("GJARVIS_DATA", "/data"))
HA_URL = os.environ.get("GJARVIS_HA_URL", "http://supervisor/core/api")
HA_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")

VOICES = ['de_DE-thorsten-medium', 'de_DE-thorsten-high', 'de_DE-thorsten-low', 'de_DE-thorsten_emotional-medium', 'de_DE-kerstin-low', 'de_DE-ramona-low', 'de_DE-eva_k-x_low', 'de_DE-karlsson-low', 'de_DE-pavoque-low', 'de_DE-mls-medium']

RATE = 16000
WIDTH = 2
CHANNELS = 1
OWW_FRAME = 1280  # 80 ms – Blockgröße, die openWakeWord erwartet
OWW_FRAME_BYTES = OWW_FRAME * WIDTH
VAD_CHUNK = 480  # 30 ms für webrtcvad
VAD_CHUNK_BYTES = VAD_CHUNK * WIDTH
SPEECH_START_MS = 240  # so lange muss am Stück gesprochen werden, bevor es als Sprache zählt
PREROLL_MS = 450

# Typische Whisper-Halluzinationen bei Stille/Rauschen
HALLUCINATIONS = [
    "untertitel",
    "amara.org",
    "vielen dank für ihre aufmerksamkeit",
    "vielen dank fürs zuschauen",
    "danke fürs zuschauen",
    "bis zum nächsten mal",
    "copyright",
    "swr",
    "zdf",
]

_LOGGER = logging.getLogger("gjarvis")


# --------------------------------------------------------------------------- #
# Hilfsfunktionen
# --------------------------------------------------------------------------- #
UI_SETTINGS = DATA_DIR / "ui_settings.json"

import apps  # noqa: E402
import features  # noqa: E402
import lizenz  # noqa: E402
import satellite  # noqa: E402
from features import MovieFeatures  # noqa: E402

features.DATA_DIR, features.HA_URL, features.HA_TOKEN = DATA_DIR, HA_URL, HA_TOKEN
apps.HA_URL, apps.HA_TOKEN = HA_URL, HA_TOKEN
satellite.HA_URL, satellite.HA_TOKEN = HA_URL, HA_TOKEN
PRO_FILE = DATA_DIR / "lizenz.json"


def load_raw_options() -> dict:
    with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
        o = json.load(f)
    try:
        o.update(json.loads(UI_SETTINGS.read_text(encoding="utf-8")))  # in der Oberfläche geänderte Werte
    except Exception:  # noqa: BLE001
        pass
    return o


def fill_options(raw: dict) -> dict:
    o = dict(raw)
    name = o.get("assistant_name") or "Jarvis"
    user = o.get("user_name") or ""

    def fill(t):
        if isinstance(t, str):
            if not user:  # ohne Namen: "Ja, {user}?" -> "Ja?"
                t = re.sub(r",?\s*\{user\}\s*,?", "", t)
            return t.replace("{name}", name).replace("{user}", user).replace(" ,", ",").strip()
        if isinstance(t, list):
            return [fill(x) for x in t]
        return t

    for key in ("ack_phrases", "instant_ack_phrases", "weather_ack_phrases", "progress_phrases", "async_ack", "async_result_prefix", "research_ack", "system_prompt", "persona"):
        if key in o:
            o[key] = fill(o[key])
    return o




def download(url_or_path: str, target_dir: Path) -> Path:
    """Lädt eine Datei von einer URL (oder nimmt einen lokalen Pfad) und cached sie."""
    if url_or_path.startswith("/"):
        p = Path(url_or_path)
        if not p.is_file():
            raise FileNotFoundError(f"Datei nicht gefunden: {p}")
        return p
    target_dir.mkdir(parents=True, exist_ok=True)
    name = url_or_path.rstrip("/").split("/")[-1].split("?")[0] or "model.onnx"
    digest = hashlib.sha1(url_or_path.encode()).hexdigest()[:8]
    target = target_dir / f"{digest}_{name}"
    if target.is_file() and target.stat().st_size > 0:
        return target
    _LOGGER.info("Lade %s ...", url_or_path)
    r = requests.get(url_or_path, timeout=120)
    r.raise_for_status()
    tmp = target.with_suffix(target.suffix + ".part")
    tmp.write_bytes(r.content)
    tmp.rename(target)
    _LOGGER.info("Gespeichert: %s (%d kB)", target, target.stat().st_size // 1024)
    return target


def apply_gain(frame: bytes, gain: float) -> bytes:
    if abs(gain - 1.0) < 1e-3:
        return frame
    a = np.frombuffer(frame, dtype=np.int16).astype(np.float32) * gain
    return np.clip(a, -32768, 32767).astype(np.int16).tobytes()


def is_garbage(text: str) -> bool:
    t = text.strip().lower()
    letters = re.sub(r"[^a-zäöüß]", "", t)
    if len(letters) < 2:
        return True
    return any(h in t for h in HALLUCINATIONS)


# --------------------------------------------------------------------------- #
# Hauptklasse
# --------------------------------------------------------------------------- #
class GJarvis(MovieFeatures, apps.AppFeatures, satellite.SatelliteFeatures):
    def __init__(self, opts: dict, raw: Optional[dict] = None) -> None:
        self.o = opts
        self.raw = dict(raw if raw is not None else opts)
        self.state = "start"
        self.level_db = -120.0
        self.last_score = 0.0
        self.last_command = ""
        self.last_answer = ""
        self.last_wake_time = ""
        self.calibration: dict = {}
        self.started = time.time()
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=400)
        self.discard = False  # True = Mikrofon ignorieren (während GJarvis spricht)
        self.barge_q: Optional[asyncio.Queue] = None
        self.current_play = None
        self.interrupted = False
        self.wake_pending = False
        self.reminders: list = []
        self.loop = None
        self.pending = None  # offene Rückfrage (z. B. "Für wie lange?")
        from collections import deque

        self.recent: deque = deque(maxlen=20)  # letzte ~1,6 s Mikrofon (für "Hey Jarvis, wie spät …" ohne Pause)
        self.wake_audio: List[bytes] = []
        self.history: list = []  # kurzer Gesprächsverlauf für Rückfragen
        self.history_ts = 0.0
        self.barge_ok = True
        self.busy = False
        self.last_wake = 0.0
        self.ack_index = 0
        self.ack_cache: dict = {}
        self.speech_lock = asyncio.Lock()  # nie zwei Ausgaben gleichzeitig (Rückmeldung + Antwort)
        self._ack_began = False
        self._last_phrase: dict = {}
        self.conversation_id: Optional[str] = None
        self.conversation_ts = 0.0
        self.resume_task: Optional[asyncio.Task] = None
        self.mqtt = None
        self.oww = None
        self.noise_floor = 50.0  # RMS des Grundrauschens, wird im Ruhezustand nachgeführt
        self.background: set = set()
        self.noise_paused = False
        self.flags: dict = {"hoert": False, "spricht": False}
        self.silero_path = None
        self.calibrate_requested = False
        self.volume = int(opts.get("volume", 80))
        try:
            saved = json.loads((DATA_DIR / "settings.json").read_text())
            self.volume = int(saved.get("volume", self.volume))
            if saved.get("tts_voice"):
                self.o["tts_voice"] = saved["tts_voice"]
        except Exception:  # noqa: BLE001
            pass

    # ----------------------------- Free / Pro ----------------------------- #
    # Free: "Hey Jarvis" -> Rückmeldung -> Befehl an Home Assistant (wie ein normaler Sprach-Satellit),
    #       dazu Oberfläche, Kalibrierung, Lautstärke, Stimme, hört/spricht, Ereignis gjarvis_command.
    # Pro:  alles andere – Nachfragen ohne Weckwort, Unterbrechen, Gedächtnis, Timer/Erinnerungen, Briefing,
    #       Ansagen, Wetter/Flugwetter direkt, Internet-Recherche, KI-Verteiler, eigenes KI-Modell, Hintergrund.
    def pro_state(self) -> dict:
        c = getattr(self, "_pro_cache", None)
        if c and time.time() - c[0] < 60:
            return c[1]
        try:
            d = json.loads(PRO_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            d = {}
        st = lizenz.check(d.get("key"))
        st["buy"] = lizenz.BUY_URL
        if d.get("key"):
            st["key_hint"] = "GJ1-…" + lizenz.normalize(d["key"])[-5:]
        self._pro_cache = (time.time(), st)
        return st

    @property
    def pro(self) -> bool:
        return bool(self.pro_state().get("ok"))

    def pro_set(self, key: str) -> dict:
        key, r, shop = lizenz.resolve(key)  # Shop-Schlüssel (WordPress) werden einmal online getauscht
        if r["state"] != "active":
            return {"ok": False, "error": r.get("state") if r["state"] == "expired" else (r.get("error") or "invalid")}
        rec = {"key": key.strip(), "set": time.strftime("%Y-%m-%d %H:%M")}
        if shop:
            rec["shop_key"] = shop
        PRO_FILE.write_text(json.dumps(rec), encoding="utf-8")
        self._pro_cache = None
        _LOGGER.info("Pro-Lizenz eingetragen, gültig bis %s", r["until"])
        return {"ok": True}

    def pro_del(self) -> dict:
        try:
            PRO_FILE.unlink()
            _LOGGER.info("Pro-Lizenz entfernt")
        except FileNotFoundError:
            pass
        self._pro_cache = None
        return {"ok": True}

    def update_noise_floor(self, frame: bytes) -> None:
        a = np.frombuffer(frame, dtype=np.int16).astype(np.float32)
        rms = float(np.sqrt(np.mean(a * a)))
        if rms < self.noise_floor * 1.5:
            self.noise_floor = 0.95 * self.noise_floor + 0.05 * rms  # leise: schnell folgen
        else:
            # lauter als Rauschen (Sprache, Klappern): nur ganz langsam und begrenzt anheben
            self.noise_floor = 0.998 * self.noise_floor + 0.002 * min(rms, self.noise_floor * 2)
        self.noise_floor = min(max(self.noise_floor, 5.0), 3000.0)

    # ----------------------------- Setup ----------------------------------- #
    def setup_wakeword(self) -> None:
        from openwakeword.model import Model  # import hier, damit Fehler sauber geloggt werden

        model_dir = DATA_DIR / "models"
        base = self.o["feature_models_url"].rstrip("/")
        mel = download(f"{base}/melspectrogram.onnx", model_dir / "features")
        emb = download(f"{base}/embedding_model.onnx", model_dir / "features")
        wake = download(self.o["wake_word_url"], model_dir / "wake")
        try:
            self.silero_path = download(f"{base}/silero_vad.onnx", model_dir / "features")
            _LOGGER.info("Sprach-Erkennung: Silero VAD")
        except Exception as e:  # noqa: BLE001
            self.silero_path = None
            _LOGGER.warning("Silero VAD nicht verfügbar (%s) – nutze webrtcvad", e)
        if wake.suffix.lower() != ".onnx":
            raise ValueError(
                f"Weckwort-Modell muss eine .onnx-Datei sein (bekommen: {wake.name})."
            )
        self.oww = Model(
            wakeword_models=[str(wake)],
            inference_framework="onnx",
            melspec_model_path=str(mel),
            embedding_model_path=str(emb),
        )
        _LOGGER.info(
            "Weckwort-Modell geladen: %s (Schwelle %.2f)",
            wake.name,
            self.o["wake_threshold"],
        )

    def setup_mqtt(self) -> None:
        host = os.environ.get("MQTT_HOST")
        if not host:
            return
        try:
            import paho.mqtt.client as mqtt

            c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="gjarvis")
            if os.environ.get("MQTT_USER"):
                c.username_pw_set(os.environ["MQTT_USER"], os.environ.get("MQTT_PASSWORD"))
            c.on_connect = lambda cl, ud, fl, rc, pr=None: self.mqtt_announce_entities(cl)
            c.on_message = self.on_mqtt_message
            c.connect_async(host, int(os.environ.get("MQTT_PORT", "1883")))
            c.loop_start()
            self.mqtt = c
            _LOGGER.info("MQTT verbunden mit %s", host)
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("MQTT nicht verfügbar: %s", e)

    # Anzeigen in Home Assistant (per MQTT-Discovery): "hört" / "spricht"
    FLAGS = {"hoert": "GJarvis hört", "spricht": "GJarvis spricht"}

    def mqtt_announce_entities(self, client) -> None:
        dev = {"identifiers": ["gjarvis"], "name": "GJarvis", "manufacturer": "GSimulations", "model": "GJarvis App"}
        icons = {"hoert": "mdi:ear-hearing", "spricht": "mdi:account-voice"}
        for key, name in self.FLAGS.items():
            client.publish(
                f"homeassistant/binary_sensor/gjarvis/{key}/config",
                json.dumps({
                    "name": name,
                    "unique_id": f"gjarvis_{key}",
                    "state_topic": f"gjarvis/{key}",
                    "payload_on": "ON",
                    "payload_off": "OFF",
                    "icon": icons[key],
                    "device": dev,
                }),
                qos=1,
                retain=True,
            )
            client.publish(f"gjarvis/{key}", "ON" if self.flags.get(key) else "OFF", qos=1, retain=True)
        client.publish(
            "homeassistant/button/gjarvis/calibrate/config",
            json.dumps({
                "name": "GJarvis kalibrieren",
                "unique_id": "gjarvis_calibrate",
                "command_topic": "gjarvis/calibrate",
                "payload_press": "START",
                "icon": "mdi:tune-vertical",
                "device": dev,
            }),
            qos=1,
            retain=True,
        )
        client.subscribe("gjarvis/calibrate", qos=1)
        for key, name, icon in (("stop", "GJarvis Stopp", "mdi:stop-circle"),
                                ("briefing", "GJarvis Briefing", "mdi:weather-sunset-up")):
            client.publish(
                f"homeassistant/button/gjarvis/{key}/config",
                json.dumps({"name": name, "unique_id": f"gjarvis_{key}", "command_topic": f"gjarvis/{key}",
                            "payload_press": "START", "icon": icon, "device": dev}),
                qos=1, retain=True,
            )
            client.subscribe(f"gjarvis/{key}", qos=1)
        client.publish(
            "homeassistant/sensor/gjarvis/reminders/config",
            json.dumps({"name": "GJarvis Erinnerungen", "unique_id": "gjarvis_reminders",
                        "state_topic": "gjarvis/reminders", "value_template": "{{ value_json.anzahl }}",
                        "json_attributes_topic": "gjarvis/reminders", "icon": "mdi:bell-ring", "device": dev}),
            qos=1, retain=True,
        )
        client.publish(
            "homeassistant/sensor/gjarvis/last_answer/config",
            json.dumps({"name": "GJarvis letzte Antwort", "unique_id": "gjarvis_last_answer",
                        "state_topic": "gjarvis/last_answer", "icon": "mdi:message-reply-text", "device": dev}),
            qos=1, retain=True,
        )
        client.subscribe("gjarvis/say", qos=1)
        client.publish(
            "homeassistant/number/gjarvis/volume/config",
            json.dumps({
                "name": "GJarvis Lautstärke",
                "unique_id": "gjarvis_volume",
                "command_topic": "gjarvis/volume/set",
                "state_topic": "gjarvis/volume",
                "min": 0,
                "max": 100,
                "step": 5,
                "unit_of_measurement": "%",
                "mode": "slider",
                "icon": "mdi:volume-high",
                "device": dev,
            }),
            qos=1,
            retain=True,
        )
        client.subscribe("gjarvis/volume/set", qos=1)
        voices = list(dict.fromkeys(VOICES + [self.o.get("tts_voice", "")]))
        client.publish(
            "homeassistant/select/gjarvis/voice/config",
            json.dumps({
                "name": "GJarvis Stimme",
                "unique_id": "gjarvis_voice",
                "command_topic": "gjarvis/voice/set",
                "state_topic": "gjarvis/voice",
                "options": [v for v in voices if v],
                "icon": "mdi:account-voice",
                "device": dev,
            }),
            qos=1,
            retain=True,
        )
        client.subscribe("gjarvis/voice/set", qos=1)
        client.publish("gjarvis/voice", self.o.get("tts_voice", ""), qos=1, retain=True)
        client.publish("gjarvis/volume", str(self.volume), qos=1, retain=True)
        client.publish(
            "homeassistant/sensor/gjarvis/calibration/config",
            json.dumps({
                "name": "GJarvis Kalibrierung",
                "unique_id": "gjarvis_calibration",
                "state_topic": "gjarvis/calibration",
                "value_template": "{{ value_json.zusammenfassung }}",
                "json_attributes_topic": "gjarvis/calibration",
                "icon": "mdi:tune-vertical",
                "device": dev,
            }),
            qos=1,
            retain=True,
        )
        client.publish(
            "homeassistant/sensor/gjarvis/last_command/config",
            json.dumps({
                "name": "GJarvis letzter Befehl",
                "unique_id": "gjarvis_last_command",
                "state_topic": "gjarvis/last_command",
                "icon": "mdi:text-recognition",
                "device": dev,
            }),
            qos=1,
            retain=True,
        )
        client.publish(
            "homeassistant/sensor/gjarvis/state/config",
            json.dumps({
                "name": "GJarvis Zustand",
                "unique_id": "gjarvis_state",
                "state_topic": self.o.get("mqtt_state_topic") or "gjarvis/state",
                "icon": "mdi:robot",
                "device": dev,
            }),
            qos=1,
            retain=True,
        )

    def on_mqtt_message(self, client, userdata, msg) -> None:
        if msg.topic == "gjarvis/voice/set":
            voice = msg.payload.decode().strip()
            if voice:
                self.o["tts_voice"] = voice
                self.ack_cache.clear()  # Rückmeldungen mit neuer Stimme neu erzeugen
                self.save_settings("tts_voice")
                client.publish("gjarvis/voice", voice, qos=1, retain=True)
                _LOGGER.info("Stimme: %s", voice)
            return
        if msg.topic == "gjarvis/volume/set":
            try:
                self.volume = max(0, min(100, int(float(msg.payload.decode()))))
                self.save_settings("volume")
                client.publish("gjarvis/volume", str(self.volume), qos=1, retain=True)
                _LOGGER.info("Lautstärke: %d %%", self.volume)
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Ungültige Lautstärke: %s", e)
            return
        if msg.topic == "gjarvis/calibrate":
            _LOGGER.info("Kalibrierung angefordert")
            self.calibrate_requested = True
            return
        if msg.topic == "gjarvis/stop":
            if self.loop:
                self.loop.call_soon_threadsafe(self.stop_speaking)
            return
        if msg.topic == "gjarvis/briefing":
            self.run_in_loop(self.briefing_announce())
            return
        if msg.topic == "gjarvis/say":
            self.run_in_loop(self.proactive_say(msg.payload.decode("utf-8", "replace")))

    def run_in_loop(self, coro) -> None:
        """Aus dem MQTT-Thread eine Aufgabe in der Hauptschleife starten."""
        if not self.loop:
            coro.close()
            return
        def _start() -> None:
            t = asyncio.ensure_future(coro)
            self.background.add(t)
            t.add_done_callback(self.background.discard)

        self.loop.call_soon_threadsafe(_start)

    async def briefing_announce(self) -> None:
        if not self.pro:
            _LOGGER.info("Briefing gibt es nur in GJarvis Pro")
            return
        text = await asyncio.to_thread(self.briefing)
        self.last_answer = text
        await self.announce(text, chime=True)

    async def proactive_say(self, payload: str) -> None:
        """Ansage von außen (MQTT 'gjarvis/say'): Text oder JSON {"text": "...", "prioritaet": "hoch"}."""
        text, prio, chime = payload.strip(), "normal", True
        try:
            d = json.loads(payload)
            if isinstance(d, dict):
                text = str(d.get("text") or d.get("message") or "").strip()
                prio = str(d.get("prioritaet") or d.get("priority") or "normal").lower()
                chime = bool(d.get("gong", d.get("chime", True)))
        except ValueError:
            pass
        if not text:
            return
        if not self.pro:
            _LOGGER.info("Ansagen gibt es nur in GJarvis Pro: %r", text)
            return
        if self.in_quiet_hours() and prio not in ("hoch", "high", "dringend"):
            _LOGGER.info("Ruhezeit – Ansage nicht gesprochen: %r", text)
            return
        _LOGGER.info("Ansage: %r", text)
        await self.announce(text, chime=chime)

    def save_settings(self, key: str = "") -> None:
        """Lautstärke/Stimme (z. B. per Schieberegler in Home Assistant geändert) dauerhaft in die
        App-Konfiguration schreiben – kurz verzögert, damit ein Schieberegler nicht 20 Schreibvorgänge auslöst.
        Die Werte werden erst beim Speichern gelesen, damit immer der neueste Stand gewinnt."""
        import threading

        keys = getattr(self, "_save_keys", set()) | ({key} if key else {"volume", "tts_voice"})
        self._save_keys = keys
        self.raw["volume"] = self.volume
        if self.o.get("tts_voice"):
            self.raw["tts_voice"] = self.o["tts_voice"]

        def fire() -> None:
            ks, self._save_keys = self._save_keys, set()
            vals = {"volume": self.volume, "tts_voice": self.o.get("tts_voice", "")}
            self.persist_options({k: vals[k] for k in ks if k in vals})

        t = getattr(self, "_save_timer", None)
        if t:
            t.cancel()
        self._save_timer = threading.Timer(1.5, fire)
        self._save_timer.daemon = True
        self._save_timer.start()

    # ----------------------------- Einstellungen speichern ------------------ #
    # Es gibt genau EINEN Speicher: die App-Konfiguration in Home Assistant (Supervisor).
    # Oberfläche, Konfigurations-Reiter und MQTT-Regler schreiben alle dorthin.
    def schema(self) -> dict:
        try:
            import yaml

            cfg = yaml.safe_load(Path(os.environ.get("GJARVIS_META_CONFIG", Path(__file__).parent / "config.yaml"))
                                 .read_text(encoding="utf-8"))
            return dict(cfg.get("schema") or {})
        except Exception:  # noqa: BLE001
            return {}

    def sanitize_options(self, changes: dict) -> dict:
        """Nur Werte behalten, die der Supervisor annimmt – sonst lehnt er ALLE Änderungen ab."""
        schema = self.schema()
        if not schema:
            return dict(changes)
        out = {}
        for k, v in changes.items():
            spec = schema.get(k)
            if spec is None:
                _LOGGER.info("Unbekannte Einstellung '%s' wird ignoriert", k)
                continue
            st = str(spec)
            m = re.match(r"list\((.*)\)\??$", st)
            if m and not isinstance(spec, list):
                if v not in m.group(1).split("|"):
                    _LOGGER.warning("Wert '%s' für %s ist nicht erlaubt – ignoriert", v, k)
                    continue
            m = re.match(r"(int|float)(?:\(([^,]*),([^)]*)\))?\??$", st)
            if m:
                try:
                    v = int(float(v)) if m.group(1) == "int" else float(v)
                except (TypeError, ValueError):
                    _LOGGER.warning("Wert '%s' für %s ist keine Zahl – ignoriert", v, k)
                    continue
                if m.group(2):
                    v = max(type(v)(float(m.group(2))), v)
                if m.group(3):
                    v = min(type(v)(float(m.group(3))), v)
            if st.startswith("port"):
                try:
                    v = int(float(v))
                except (TypeError, ValueError):
                    continue
            out[k] = v
        return out

    def persist_options(self, changes: dict) -> Tuple[bool, str]:
        """Änderungen in die App-Konfiguration von Home Assistant schreiben (gleiche Werte wie im Reiter
        'Konfiguration'). Ohne Supervisor (Entwicklung) landen sie in ui_settings.json."""
        changes = self.sanitize_options(changes or {})
        if not changes:
            return True, ""
        lock = getattr(self, "_persist_lock", None)
        if lock is None:
            import threading

            lock = self._persist_lock = threading.Lock()
        with lock:
            if HA_TOKEN:
                try:
                    current = dict(self.sup("GET", "/addons/self/info").get("options") or {})
                    current.update(changes)
                    r = requests.post(f"{self.SUP_URL}/addons/self/options",
                                      headers={"Authorization": f"Bearer {HA_TOKEN}"},
                                      json={"options": current}, timeout=20)
                    if r.status_code >= 400:
                        try:
                            msg = r.json().get("message") or r.text
                        except Exception:  # noqa: BLE001
                            msg = r.text
                        _LOGGER.warning("Einstellungen nicht gespeichert: %s", msg)
                        return False, str(msg)[:300]
                    _LOGGER.info("In der App-Konfiguration gespeichert: %s", ", ".join(changes))
                    return True, ""
                except Exception as e:  # noqa: BLE001
                    _LOGGER.warning("Einstellungen nicht gespeichert: %s", e)
                    return False, str(e)[:300]
            try:  # Entwicklung ohne Supervisor
                try:
                    saved = json.loads(UI_SETTINGS.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    saved = {}
                saved.update(changes)
                UI_SETTINGS.write_text(json.dumps(saved, ensure_ascii=False, indent=1), encoding="utf-8")
                return True, ""
            except Exception as e:  # noqa: BLE001
                return False, str(e)[:300]

    def migrate_legacy_settings(self) -> None:
        """Bis 1.7: Oberfläche speicherte in ui_settings.json, Regler in settings.json – beides überschrieb
        still die App-Konfiguration. Einmalig in die App-Konfiguration übernehmen und die Dateien umbenennen.
        Reihenfolge wie bisher zur Laufzeit: Konfiguration < ui_settings.json < settings.json."""
        if not HA_TOKEN:
            return
        legacy: dict = {}
        files = []
        for f in (UI_SETTINGS, DATA_DIR / "settings.json"):
            if f.is_file():
                try:
                    legacy.update(json.loads(f.read_text(encoding="utf-8")))
                    files.append(f)
                except Exception as e:  # noqa: BLE001
                    _LOGGER.warning("%s nicht lesbar: %s", f.name, e)
        if not files:
            return
        # Laufender Stand (Lautstärke/Stimme) ist maßgeblich
        legacy["volume"] = self.volume
        if self.o.get("tts_voice"):
            legacy["tts_voice"] = self.o["tts_voice"]
        clean = self.sanitize_options(legacy)
        ok, err = self.persist_options(clean)
        if ok:
            self.raw.update(clean)
            for f in files:
                try:
                    f.rename(f.with_name(f.stem + ".migriert.json"))
                except OSError as e:
                    _LOGGER.warning("%s nicht umbenannt: %s", f.name, e)
            _LOGGER.info("Alte Oberflächen-Einstellungen in die App-Konfiguration übernommen (%d Werte)", len(clean))
        else:
            _LOGGER.warning("Alte Einstellungen konnten nicht übernommen werden (%s) – bleiben vorerst aktiv", err)

    def set_flag(self, key: str, on: bool) -> None:
        if self.flags.get(key) == on:
            return
        self.flags[key] = on
        self.publish(f"gjarvis/{key}", "ON" if on else "OFF", retain=True)

    def update_noise_logger(self, state: str) -> None:
        """Pausiert/fortsetzt GasLighter je nach Zustand und Schaltern."""
        if not self.o.get("mqtt_pause_enabled", True) or not self.mqtt:
            return
        want = state in ("listening", "responding")
        if state == "processing":
            return  # Zustand beibehalten
        if want:
            if self.resume_task:
                self.resume_task.cancel()
                self.resume_task = None
            self.publish(self.o["mqtt_pause_topic"], self.o["mqtt_pause_payload"])
            self.noise_paused = True
        elif self.noise_paused:
            delay = float(self.o["mqtt_resume_delay_seconds"]) if state == "idle" else 0.0
            self.schedule_resume(delay)

    def publish(self, topic: str, payload: str, retain: bool = False) -> None:
        if self.mqtt and topic:
            try:
                self.mqtt.publish(topic, payload, qos=1, retain=retain)
            except Exception as e:  # noqa: BLE001
                _LOGGER.debug("MQTT publish fehlgeschlagen: %s", e)

    def set_state(self, state: str) -> None:
        self.state = state
        _LOGGER.info("Zustand: %s", state)
        self.publish(self.o.get("mqtt_state_topic", ""), state, retain=True)
        self.set_flag("hoert", state == "listening")
        self.update_noise_logger(state)
        self.satellite_state(state)

    # ----------------------------- Audio ----------------------------------- #
    async def mic_reader(self) -> None:
        """Liest dauerhaft vom Standard-Mikrofon (PulseAudio) – teilt es mit anderen Apps."""
        while True:
            proc = await asyncio.create_subprocess_exec(
                "parec",
                "--raw",
                "--format=s16le",
                f"--rate={RATE}",
                f"--channels={CHANNELS}",
                "--latency-msec=40",
                stdout=asyncio.subprocess.PIPE,
            )
            _LOGGER.info("Mikrofon geöffnet")
            silent_frames = 0
            max_silent = int(float(self.o.get("mic_watchdog_seconds", 3)) * RATE / OWW_FRAME)
            try:
                while True:
                    try:
                        frame = await asyncio.wait_for(proc.stdout.readexactly(OWW_FRAME_BYTES), timeout=3)
                    except asyncio.TimeoutError:
                        _LOGGER.warning("Mikrofon liefert keine Daten mehr – öffne es neu")
                        break
                    if not any(frame):  # reine digitale Stille = Mikrofon hängt
                        silent_frames += 1
                        if silent_frames >= max_silent:
                            _LOGGER.warning("Mikrofon liefert nur noch Stille – öffne es neu")
                            break
                    else:
                        silent_frames = 0
                    self.feed_frame(frame)
            except (asyncio.IncompleteReadError, ConnectionError) as e:
                _LOGGER.warning("Mikrofon-Stream beendet (%s) – starte neu", e)
            finally:
                if proc.returncode is None:
                    proc.kill()
                await proc.wait()
            await asyncio.sleep(0.5)

    def flush(self) -> None:
        while not self.queue.empty():
            self.queue.get_nowait()

    async def play_pcm(self, pcm: bytes, rate: int, width: int, channels: int) -> None:
        if width == 2 and self.volume != 100:
            pcm = pcm[: len(pcm) // 2 * 2]
            a = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) * (self.volume / 100.0)
            pcm = np.clip(a, -32768, 32767).astype(np.int16).tobytes()
        was = self.flags.get("spricht")
        self.set_flag("spricht", True)
        try:
            async with self.speech_lock:
                await self._play_pcm(pcm, rate, width, channels)
        finally:
            if not was:
                self.set_flag("spricht", False)

    async def _barge_monitor(self, proc) -> None:
        """Während Jarvis spricht: 'Hey Jarvis' unterbricht ihn (wie im Film)."""
        if not (self.o.get("barge_in", True) and self.oww and self.barge_ok and self.pro):
            return
        self.oww.reset()
        thr = max(float(self.o.get("wake_threshold", 0.5)), float(self.o.get("barge_in_threshold", 0.7)))
        while proc.returncode is None:
            try:
                fr = await asyncio.wait_for(self.barge_q.get(), timeout=0.3)
            except asyncio.TimeoutError:
                continue
            sc = self.oww.predict(np.frombuffer(fr, dtype=np.int16))
            if sc and max(sc.values()) >= thr:
                _LOGGER.info("Unterbrochen durch Weckwort (Score %.2f)", max(sc.values()))
                self.interrupted = True
                proc.kill()
                return

    async def _play_pcm(self, pcm: bytes, rate: int, width: int, channels: int) -> None:
        if self.remote_player:  # externer Lautsprecher aus Home Assistant (z. B. Sonos)
            try:
                await self.play_remote_pcm(pcm, rate, width, channels)
            except Exception as e:  # noqa: BLE001
                _LOGGER.error("Ausgabe über %s fehlgeschlagen: %s", self.remote_player, e)
                self.satellite_error(3, str(e))
                raise satellite.RemoteOutputError(str(e)) from e
            return
        fmt = {1: "u8", 2: "s16le", 4: "s32le"}.get(width, "s16le")
        self.barge_q = asyncio.Queue(maxsize=200)
        proc = await asyncio.create_subprocess_exec(
            "pacat",
            "--playback",
            "--raw",
            f"--format={fmt}",
            f"--rate={rate}",
            f"--channels={channels}",
            stdin=asyncio.subprocess.PIPE,
        )
        limit = len(pcm) / max(1, rate * width * channels) + 5
        self.current_play = proc
        mon = asyncio.create_task(self._barge_monitor(proc))
        try:
            proc.stdin.write(pcm)
            await asyncio.wait_for(proc.stdin.drain(), timeout=limit)
            proc.stdin.close()
            await asyncio.wait_for(proc.wait(), timeout=limit)
        except (asyncio.TimeoutError, BrokenPipeError, ConnectionResetError) as e:
            if not self.interrupted:
                _LOGGER.warning("Wiedergabe hing (%s) – abgebrochen", type(e).__name__)
            if proc.returncode is None:
                proc.kill()
            await proc.wait()
        finally:
            mon.cancel()
            self.current_play = None
            self.barge_q = None

    def stop_speaking(self) -> None:
        """Sprachausgabe sofort beenden (Knopf 'GJarvis Stopp' / Oberfläche)."""
        p = self.current_play
        if p and p.returncode is None:
            _LOGGER.info("Sprachausgabe gestoppt")
            p.kill()
        if self.remote_player and self.flags.get("spricht"):  # Musik am Lautsprecher nur stoppen, wenn Jarvis spricht
            import threading

            self.remote_stop = True
            threading.Thread(target=self.stop_remote, daemon=True).start()

    @staticmethod
    def split_sentences(text: str, min_len: int = 40) -> List[str]:
        parts = re.split(r"(?<=[.!?;])\s+", text.strip())
        out: List[str] = []
        for p in parts:
            if out and len(out[-1]) < min_len:
                out[-1] += " " + p
            else:
                out.append(p)
        return [p for p in out if p.strip()]

    async def speak(self, text: str, chime: bool = False) -> None:
        """Text über Piper sprechen – Satz für Satz (der erste Satz kommt sofort, der Rest wird
        im Hintergrund erzeugt). 'Hey Jarvis' unterbricht. Mikrofon ist währenddessen stumm."""
        if not text or not text.strip():
            return
        self.discard = True
        self.interrupted = False
        self.remote_stop = False
        name = (self.o.get("assistant_name") or "jarvis").lower()
        self.barge_ok = name not in text.lower() and "jarvis" not in text.lower()  # sonst weckt er sich selbst
        self.set_flag("spricht", True)
        nxt = None
        try:
            if chime:
                async with self.speech_lock:
                    await self._play_pcm(*self.chime_pcm())
            if self.remote_tts:  # Stimme aus Home Assistant (z. B. ElevenLabs) auf dem externen Lautsprecher
                async with self.speech_lock:
                    await self.speak_remote_tts(text)
                return
            sentences = self.split_sentences(text)
            nxt = asyncio.create_task(self.synthesize(sentences[0]))
            for i in range(len(sentences)):
                pcm, fmt = await nxt
                nxt = asyncio.create_task(self.synthesize(sentences[i + 1])) if i + 1 < len(sentences) else None
                if pcm:
                    await self.play_pcm(pcm, *fmt)
                if self.interrupted or self.remote_stop:
                    break
        except satellite.RemoteOutputError:
            pass  # schon als Fehlercode 3 gemeldet
        except Exception as e:  # noqa: BLE001
            _LOGGER.error("Sprachausgabe fehlgeschlagen: %s", e)
            self.satellite_error(4, str(e))
        finally:
            if nxt:
                nxt.cancel()
            self.set_flag("spricht", False)
            self.barge_ok = True
            await asyncio.sleep(0.25)  # Nachhall abwarten
            self.flush()
            self.discard = False

    def chime_pcm(self):
        """Kurzer Zwei-Ton-Gong vor Ansagen (wie im Film)."""
        rate = 22050
        out = []
        for f, d in ((880.0, 0.12), (1318.5, 0.22)):
            t = np.arange(int(rate * d)) / rate
            env = np.minimum(1, t * 80) * np.exp(-t * 9)
            out.append(np.sin(2 * np.pi * f * t) * env)
        a = np.concatenate(out) * 9000 * (self.volume / 100.0)
        return a.astype(np.int16).tobytes(), rate, 2, 1

    # ----------------------------- Wyoming --------------------------------- #
    async def synthesize(self, text: str) -> Tuple[bytes, Tuple[int, int, int]]:
        client = AsyncTcpClient(self.o["tts_host"], int(self.o["tts_port"]))
        await client.connect()
        try:
            voice = SynthesizeVoice(name=self.o["tts_voice"]) if self.o.get("tts_voice") else None
            await client.write_event(Synthesize(text=text, voice=voice).event())
            fmt = (22050, 2, 1)
            chunks: List[bytes] = []
            while True:
                ev = await asyncio.wait_for(client.read_event(), timeout=30)
                if ev is None:
                    break
                if AudioStart.is_type(ev.type):
                    s = AudioStart.from_event(ev)
                    fmt = (s.rate, s.width, s.channels)
                elif AudioChunk.is_type(ev.type):
                    chunks.append(AudioChunk.from_event(ev).audio)
                elif AudioStop.is_type(ev.type):
                    break
            return b"".join(chunks), fmt
        finally:
            await client.disconnect()

    def normalize_for_stt(self, audio: bytes) -> bytes:
        """Leise Aufnahmen für Whisper auf normale Lautstärke bringen (nur Jarvis' Kopie)."""
        a = np.frombuffer(audio[: len(audio) // 2 * 2], dtype=np.int16).astype(np.float32)
        if not len(a):
            return audio
        a -= float(np.mean(a))  # Gleichanteil entfernen
        peak = float(np.percentile(np.abs(a), 99.9))
        if peak < 1:
            return audio
        self.last_peak_db = self.dbfs(peak)
        gain = min(float(self.o.get("stt_max_gain", 30.0)), 0.6 * 32767 / peak)
        if gain > 1.05:
            _LOGGER.info("Aufnahme für Whisper verstärkt: x%.1f (Spitze vorher %.0f dBFS)", gain, self.dbfs(peak))
        return np.clip(a * max(gain, 1.0), -32768, 32767).astype(np.int16).tobytes()

    async def transcribe(self, audio: bytes) -> str:
        audio = self.normalize_for_stt(audio)
        client = AsyncTcpClient(self.o["stt_host"], int(self.o["stt_port"]))
        await client.connect()
        try:
            await client.write_event(Transcribe(language=self.o["language"]).event())
            await client.write_event(AudioStart(rate=RATE, width=WIDTH, channels=CHANNELS).event())
            step = RATE * WIDTH  # 1 s
            for i in range(0, len(audio), step):
                await client.write_event(
                    AudioChunk(rate=RATE, width=WIDTH, channels=CHANNELS, audio=audio[i : i + step]).event()
                )
            await client.write_event(AudioStop().event())
            while True:
                ev = await asyncio.wait_for(client.read_event(), timeout=60)
                if ev is None:
                    return ""
                if Transcript.is_type(ev.type):
                    return Transcript.from_event(ev).text or ""
        finally:
            await client.disconnect()

    # ----------------------------- Home Assistant -------------------------- #
    def converse(self, text: str) -> Tuple[str, bool]:
        if time.monotonic() - self.conversation_ts > 300:
            self.conversation_id = None
        body = {"text": text, "language": self.o["language"]}
        if self.o.get("agent_id"):
            body["agent_id"] = self.o["agent_id"]
        if self.conversation_id:
            body["conversation_id"] = self.conversation_id
        r = requests.post(
            f"{HA_URL}/conversation/process",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json=body,
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        self.conversation_id = data.get("conversation_id")
        self.conversation_ts = time.monotonic()
        speech = (
            data.get("response", {}).get("speech", {}).get("plain", {}).get("speech", "")
        ) or ""
        if "<tool" in speech or "</tool>" in speech:
            _LOGGER.info("KI-Agent hat ein Werkzeug nicht ausgeführt: %r", speech[:120])
            speech = ""
        if data.get("response", {}).get("response_type") == "error" or not speech:
            if not self.pro:
                return speech or "Das habe ich leider nicht verstanden.", False
            _LOGGER.info("Home Assistant hat es nicht verstanden – frage das KI-Modell direkt")
            return self.chat(text), False
        return speech, bool(data.get("continue_conversation", False))

    def chat(self, text: str, extra: str = "") -> str:
        """Direkte Frage an das KI-Modell (z. B. Witze, Allgemeinwissen, Wetter formulieren)."""
        if not self.has_llm():
            return self.anrede("Dafür brauche ich eine KI. Richte sie in meiner Oberfläche unter KI-Modell ein")
        content = f"{extra}\n\nFrage: {text}" if extra else text
        if time.monotonic() - self.history_ts > 300:
            self.history = []
        now = time.strftime("%d.%m.%Y, %H:%M Uhr")
        # System-Text bleibt immer gleich -> das KI-Modell kann ihn zwischenspeichern (viel schneller auf CPU)
        system = f"{self.o['system_prompt']} {self.o.get('persona', '')}".strip()
        ctx = f"(Jetzt: {now}.{self.memory_prompt()})\n"
        messages = ([{"role": "system", "content": system}] + self.history[-6:]
                    + [{"role": "user", "content": ctx + content}])
        ans = self.clean_for_speech(self.ask_llm(messages))
        self.history += [{"role": "user", "content": text}, {"role": "assistant", "content": ans}]
        self.history = self.history[-12:]
        self.history_ts = time.monotonic()
        return ans

    # ----------------------------- Wetter ---------------------------------- #
    def wants_weather(self, text: str) -> bool:
        t = text.lower()
        if re.search(r"wie wird (es|das wetter)\b.*\b(heute|morgen|später|woche|wochenende|tage|montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)", t):
            return True
        return any(w in t for w in self.o.get("weather_triggers", []) if w.strip())

    def ha_get(self, path: str):
        r = requests.get(f"{HA_URL}{path}", headers={"Authorization": f"Bearer {HA_TOKEN}"}, timeout=15)
        r.raise_for_status()
        return r.json()

    COND_DE = {
        "clear-night": "klar", "cloudy": "bewölkt", "exceptional": "ungewöhnlich", "fog": "neblig",
        "hail": "mit Hagel", "lightning": "gewittrig", "lightning-rainy": "gewittrig mit Regen",
        "partlycloudy": "teilweise bewölkt", "pouring": "sehr regnerisch", "rainy": "regnerisch",
        "snowy": "verschneit", "snowy-rainy": "mit Schneeregen", "sunny": "sonnig",
        "windy": "windig", "windy-variant": "windig und bewölkt",
    }
    TAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    def parse_day(self, text: str):
        import datetime as dt

        t = text.lower()
        today = dt.date.today()
        if "übermorgen" in t:
            offset, label = 2, "Übermorgen"
        elif re.search(r"(?<!heute )morgen", t):
            offset, label = 1, "Morgen"
        else:
            offset, label = 0, "Heute"
            for i, tag in enumerate(self.TAGE):
                if tag.lower() in t:
                    offset = (i - today.weekday()) % 7 or 7
                    label = f"Am {tag}"
                    break
        return offset, label, today + dt.timedelta(days=offset)

    # ----------------------------- Flugwetter (Gleitschirm) ---------------- #
    OPENMETEO_URL = os.environ.get("GJARVIS_OPENMETEO_URL", "https://api.open-meteo.com/v1/forecast")
    WINDY_URL = os.environ.get("GJARVIS_WINDY_URL", "https://api.windy.com/api/point-forecast/v2")
    PARAGLIDABLE_URL = os.environ.get("GJARVIS_PARAGLIDABLE_URL", "https://paraglidable.com/apps/api/get.php")
    RICHTUNG = ["Nord", "Nordost", "Ost", "Südost", "Süd", "Südwest", "West", "Nordwest"]

    def wants_flight(self, text: str) -> bool:
        if not self.o.get("flight_enabled", True):
            return False
        t = text.lower()
        return any(w.lower() in t for w in self.o.get("flight_triggers", []) if w.strip())

    def flight_position(self):
        lat, lon = float(self.o.get("flight_lat") or 0), float(self.o.get("flight_lon") or 0)
        if not lat and not lon:
            cfg = self.ha_get("/config")
            lat, lon = float(cfg.get("latitude", 0)), float(cfg.get("longitude", 0))
        return lat, lon

    def paraglidable_day(self, target):
        key = (self.o.get("paraglidable_api_key") or "").strip()
        if not key:
            return []
        r = requests.get(self.PARAGLIDABLE_URL, params={"key": key, "format": "JSON", "version": 1}, timeout=15)
        r.raise_for_status()
        data = r.json()
        entries = data.get(target.isoformat()) or []
        out = []
        for e in entries if isinstance(entries, list) else [entries]:
            fc = e.get("forecast", {}) if isinstance(e, dict) else {}
            name = e.get("name") or (e.get("takeoff") or {}).get("name") or ""
            if isinstance(name, dict):
                name = name.get("name", "")
            fly = fc.get("fly")
            xc = fc.get("XC", fc.get("xc"))
            if fly is not None:
                out.append({"name": str(name), "fly": float(fly), "xc": None if xc is None else float(xc)})
        if not out:
            _LOGGER.info("Paraglidable: keine Daten für %s (Schlüssel: %s)", target, list(data)[:5])
        return out

    def wind_day(self, target, lat, lon):
        """Wind/Böen/Höhenwind/Regen/Wolken für 11–17 Uhr des Tages (Windy, sonst Open-Meteo)."""
        import datetime as dt

        hours = range(11, 18)
        wkey = (self.o.get("windy_api_key") or "").strip()
        if wkey:
            r = requests.post(
                self.WINDY_URL,
                json={
                    "lat": lat, "lon": lon, "model": "gfs",
                    "parameters": ["wind", "windGust", "precip", "lclouds"],
                    "levels": ["surface", "850h"], "key": wkey,
                },
                timeout=20,
            )
            r.raise_for_status()
            d = r.json()
            idx = [
                i for i, ts in enumerate(d.get("ts", []))
                if dt.datetime.fromtimestamp(ts / 1000).date() == target
                and dt.datetime.fromtimestamp(ts / 1000).hour in hours
            ]
            if idx:
                def sp(u, v):
                    return [float(np.hypot(d[u][i], d[v][i])) * 3.6 for i in idx]

                def dr(u, v):
                    return float(np.degrees(np.arctan2(-np.mean([d[u][i] for i in idx]), -np.mean([d[v][i] for i in idx]))) % 360)

                return {
                    "quelle": "Windy",
                    "wind": float(np.mean(sp("wind_u-surface", "wind_v-surface"))),
                    "richtung": dr("wind_u-surface", "wind_v-surface"),
                    "boeen": max(float(d["gust-surface"][i]) * 3.6 for i in idx) if "gust-surface" in d else None,
                    "hoehe": float(np.mean(sp("wind_u-850h", "wind_v-850h"))) if "wind_u-850h" in d else None,
                    "regen": None,
                    "regen_mm": sum(float(d.get("past3hprecip-surface", [0] * len(d["ts"]))[i] or 0) for i in idx),
                    "wolken": float(np.mean([d["lclouds-surface"][i] for i in idx])) if "lclouds-surface" in d else None,
                    "basis": None,
                }
        r = requests.get(
            self.OPENMETEO_URL,
            params={
                "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 7,
                "wind_speed_unit": "kmh",
                "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,wind_speed_850hPa,"
                "precipitation_probability,cloud_cover_low,boundary_layer_height",
            },
            timeout=15,
        )
        r.raise_for_status()
        h = r.json()["hourly"]
        idx = [
            i for i, ts in enumerate(h["time"])
            if ts.startswith(target.isoformat()) and int(ts[11:13]) in hours
        ]
        if not idx:
            return None

        def vals(k):
            return [float(h[k][i]) for i in idx if h.get(k) and h[k][i] is not None]

        dirs = np.radians(vals("wind_direction_10m"))
        richtung = float(np.degrees(np.arctan2(np.mean(np.sin(dirs)), np.mean(np.cos(dirs)))) % 360) if len(dirs) else None
        bl = vals("boundary_layer_height")
        return {
            "quelle": "Open-Meteo",
            "wind": float(np.mean(vals("wind_speed_10m"))) if vals("wind_speed_10m") else None,
            "richtung": richtung,
            "boeen": max(vals("wind_gusts_10m")) if vals("wind_gusts_10m") else None,
            "hoehe": float(np.mean(vals("wind_speed_850hPa"))) if vals("wind_speed_850hPa") else None,
            "regen": max(vals("precipitation_probability")) if vals("precipitation_probability") else None,
            "regen_mm": None,
            "wolken": float(np.mean(vals("cloud_cover_low"))) if vals("cloud_cover_low") else None,
            "basis": max(bl) if bl else None,
        }

    def flight_answer(self, text: str) -> str:
        offset, label, target = self.parse_day(text)
        lat, lon = self.flight_position()
        site = self.o.get("flight_site_name") or ""
        parts = [f"Flugwetter {label.lower() if offset < 3 else label}" + (f" am {site}" if site else "")]
        try:
            pg = self.paraglidable_day(target)
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("Paraglidable nicht erreichbar: %s", e)
            pg = []
        if pg:
            best = sorted(pg, key=lambda x: x["fly"], reverse=True)[:2]
            for b in best:
                s = f"Paraglidable {round(b['fly'] * 100)} Prozent fliegbar"
                if b.get("name"):
                    s = f"{b['name']}: " + s
                if b.get("xc") is not None:
                    s += f", Streckenflug {round(b['xc'] * 100)} Prozent"
                parts.append(s)
        try:
            w = self.wind_day(target, lat, lon)
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("Winddaten nicht erreichbar: %s", e)
            w = None
        verdict = []
        if w:
            s = []
            if w.get("wind") is not None:
                rt = "" if w.get("richtung") is None else f" aus {self.RICHTUNG[int((w['richtung'] + 22.5) // 45) % 8]}"
                s.append(f"Wind {round(w['wind'])} km/h{rt}")
            if w.get("boeen") is not None:
                s.append(f"Böen bis {round(w['boeen'])}")
            if w.get("hoehe") is not None:
                s.append(f"in 1500 Metern {round(w['hoehe'])} km/h")
            if s:
                parts.append(", ".join(s))
            if w.get("regen") is not None:
                parts.append(f"Regenrisiko {round(w['regen'])} Prozent")
            elif w.get("regen_mm"):
                parts.append(f"Regen etwa {w['regen_mm']:.1f} Millimeter")
            if w.get("basis"):
                parts.append(f"Thermik bis etwa {int(round(w['basis'], -2))} Meter über Grund")
            # Grobe Einschätzung (kein Ersatz für eigene Prüfung!)
            if (w.get("boeen") or 0) > 35 or (w.get("wind") or 0) > 25 or (w.get("hoehe") or 0) > 35:
                verdict.append("zu viel Wind")
            if (w.get("regen") or 0) >= 50 or (w.get("regen_mm") or 0) >= 2:
                verdict.append("Regen wahrscheinlich")
        if pg and max(b["fly"] for b in pg) < 0.4:
            verdict.append("Paraglidable ist skeptisch")
        if w or pg:
            parts.append(
                ("Eher nichts: " + " und ".join(verdict)) if verdict else "Sieht fliegbar aus, bitte vor Ort selbst prüfen"
            )
        else:
            parts.append("leider habe ich keine Flugwetterdaten bekommen")
        _LOGGER.info("Flugwetter %s (%s)", label, (w or {}).get("quelle", "keine Winddaten"))
        return ". ".join(parts) + "."

    def weather_answer(self, text: str) -> str:
        """Wetter direkt aus den HA-Daten vorlesen – ohne KI, daher sofort."""
        import datetime as dt

        ent = self.o.get("weather_entity", "").strip()
        if not ent:
            ws = [x["entity_id"] for x in self.ha_get("/states") if x["entity_id"].startswith("weather.")]
            if not ws:
                return "Ich habe in Home Assistant keine Wetter-Entität gefunden."
            ent = ws[0]
            self.o["weather_entity"] = ent  # merken, damit es beim nächsten Mal schneller geht
        offset, label, target = self.parse_day(text)
        today = dt.date.today()
        simple = re.fullmatch(
            r"(hey |ok )?(jarvis,? )?(wie (wird|ist) (das|denn das) wetter|wetter)( (heute|morgen|übermorgen|am \w+))?( (heute|morgen|übermorgen|am \w+))?",
            text.lower().strip(" ?.!"))
        if self.pro and not simple and self.has_llm():
            # Jede andere Wetterfrage ("Brauche ich morgen einen Schirm?", "Wird es am Wochenende warm?"):
            # die KI beantwortet sie aus den echten Vorhersagedaten
            try:
                return self.weather_llm(ent, text)
            except LookupError:
                raise
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Wetter mit KI nicht möglich (%s) – ohne KI", e)
        span = self.parse_span(text)
        if span:
            return self.weather_span(ent, *span)

        if offset == 0:
            cur = self.ha_get(f"/states/{ent}")
            at = cur.get("attributes", {})
            cond = self.COND_DE.get(cur.get("state", ""), cur.get("state", ""))
            parts = [f"Draußen ist es gerade {cond} bei {round(float(at.get('temperature', 0)))} Grad"]
        else:
            parts = []
        r = requests.post(
            f"{HA_URL}/services/weather/get_forecasts?return_response",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json={"entity_id": ent, "type": "daily"},
            timeout=15,
        )
        r.raise_for_status()
        fc = r.json().get("service_response", {}).get(ent, {}).get("forecast", [])
        day = None
        for f in fc:
            try:
                d = dt.datetime.fromisoformat(str(f.get("datetime")).replace("Z", "+00:00")).astimezone().date()
            except Exception:  # noqa: BLE001
                continue
            if d == target:
                day = f
                break
        if day is None and offset < len(fc):
            day = fc[offset]
        if day:
            cond = self.COND_DE.get(day.get("condition", ""), day.get("condition", ""))
            hi, lo = day.get("temperature"), day.get("templow")
            if hi is not None and lo is not None and round(float(lo)) != round(float(hi)):
                temp = f"zwischen {round(float(lo))} und {round(float(hi))} Grad"
            elif hi is not None and lo is not None:
                temp = f"um {round(float(hi))} Grad"
            elif hi is not None:
                temp = f"bis {round(float(hi))} Grad"
            else:
                temp = ""
            pre = "tagsüber wird es" if offset == 0 else "wird es"
            sentence = f"{label if offset else ''} {pre} {cond}{', ' + temp if temp else ''}".strip()
            parts.append(sentence[0].upper() + sentence[1:])
            pp = day.get("precipitation_probability")
            if pp is not None and float(pp) >= 20:
                parts.append(f"Regenwahrscheinlichkeit {round(float(pp))} Prozent")
        _LOGGER.info("Wetter von %s (%s)", ent, label)
        return ". ".join(parts) + "." if parts else "Für diesen Tag habe ich keine Vorhersage."

    def parse_span(self, text: str):
        """'diese Woche', 'nächste Woche', 'Wochenende', 'die nächsten Tage' -> (von, bis, Bezeichnung)."""
        import datetime as dt

        t = text.lower()
        today = dt.date.today()
        wd = today.weekday()
        if "wochenende" in t:
            sa = today + dt.timedelta(days=(5 - wd) % 7 if wd <= 5 else 0)
            if wd == 6:
                sa = today - dt.timedelta(days=1)
            if "nächste" in t and wd < 5:
                sa += dt.timedelta(days=7)
            return max(sa, today), sa + dt.timedelta(days=1), "Am Wochenende"
        if re.search(r"nächste[nr]? woche|kommende[nr]? woche", t):
            mo = today + dt.timedelta(days=7 - wd)
            return mo, mo + dt.timedelta(days=6), "Nächste Woche"
        if re.search(r"(diese[rn]?|der) woche|nächsten tage|kommenden tage|die woche", t):
            start = today + dt.timedelta(days=1) if "später" in t or "rest" in t else today
            return start, today + dt.timedelta(days=6 - wd if wd < 6 else 0) if "diese" in t else today + dt.timedelta(days=4), "In den nächsten Tagen" if "tage" in t else "Diese Woche"
        return None

    def weather_llm(self, ent: str, text: str) -> str:
        import datetime as dt

        cur = self.ha_get(f"/states/{ent}")
        at = cur.get("attributes", {})
        r = requests.post(
            f"{HA_URL}/services/weather/get_forecasts?return_response",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json={"entity_id": ent, "type": "daily"},
            timeout=15,
        )
        r.raise_for_status()
        fc = r.json().get("service_response", {}).get(ent, {}).get("forecast", [])
        lines = [f"Jetzt: {self.COND_DE.get(cur.get('state', ''), cur.get('state', ''))}, {at.get('temperature')} Grad"]
        for f in fc:
            try:
                d = dt.datetime.fromisoformat(str(f.get("datetime")).replace("Z", "+00:00")).astimezone().date()
            except Exception:  # noqa: BLE001
                continue
            bits = [f"{self.TAGE[d.weekday()]} {d.day}.{d.month}.", self.COND_DE.get(f.get("condition", ""), f.get("condition", ""))]
            if f.get("templow") is not None:
                bits.append(f"tiefst {round(float(f['templow']))} Grad")
            if f.get("temperature") is not None:
                bits.append(f"höchst {round(float(f['temperature']))} Grad")
            if f.get("precipitation_probability") is not None:
                bits.append(f"Regenrisiko {round(float(f['precipitation_probability']))} Prozent")
            if f.get("precipitation"):
                bits.append(f"{f['precipitation']} mm Niederschlag")
            if f.get("wind_speed") is not None:
                bits.append(f"Wind {round(float(f['wind_speed']))} km/h")
            lines.append(", ".join(bits))
        heute = dt.date.today()
        prompt = (
            f"Heute ist {self.TAGE[heute.weekday()]}, der {heute.day}.{heute.month}.{heute.year}. "
            "Beantworte die Frage NUR mit diesen Wetterdaten, auf Deutsch, in höchstens zwei kurzen Sätzen zum Vorlesen, "
            "ohne Aufzählung. Nenne Wochentage statt Datum. Wenn die Daten den gefragten Zeitraum nicht oder nur "
            "teilweise abdecken, antworte ausschließlich mit dem Wort FEHLT.\n\nWetterdaten:\n" + "\n".join(lines)
        )
        t0 = time.monotonic()
        ans = self.clean_for_speech(self.ask_llm(
            [{"role": "system", "content": prompt}, {"role": "user", "content": text}], max_tokens=120))
        _LOGGER.info("Wetter mit KI aus %s (%.1f s)", ent, time.monotonic() - t0)
        if not ans or "FEHLT" in ans.upper():
            raise LookupError(self.extract_query(text))
        return ans

    def weather_span(self, ent: str, start, end, label: str) -> str:
        import datetime as dt

        r = requests.post(
            f"{HA_URL}/services/weather/get_forecasts?return_response",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json={"entity_id": ent, "type": "daily"},
            timeout=15,
        )
        r.raise_for_status()
        fc = r.json().get("service_response", {}).get(ent, {}).get("forecast", [])
        teile = []
        for f in fc:
            try:
                d = dt.datetime.fromisoformat(str(f.get("datetime")).replace("Z", "+00:00")).astimezone().date()
            except Exception:  # noqa: BLE001
                continue
            if not (start <= d <= end):
                continue
            cond = self.COND_DE.get(f.get("condition", ""), f.get("condition", ""))
            hi = f.get("temperature")
            name = "heute" if d == dt.date.today() else "morgen" if d == dt.date.today() + dt.timedelta(days=1) else self.TAGE[d.weekday()]
            teile.append(f"{name} {cond}" + (f" bei {round(float(hi))} Grad" if hi is not None else ""))
        _LOGGER.info("Wetter von %s (%s, %d Tage)", ent, label, len(teile))
        wanted = (end - start).days + 1
        if self.pro and self.o.get("research_enabled", True) and len(teile) < max(1, wanted * 0.6):
            raise LookupError(label.lower())
        if not teile:
            return f"{label} habe ich noch keine Vorhersage – sie reicht meist nur etwa eine Woche weit."
        if len(teile) > 1:
            teile[-1] = "und " + teile[-1]
        return f"{label}: " + ", ".join(teile) + "."

    def fire_command_event(self, text: str) -> None:
        """Erkannten Satz als HA-Ereignis 'gjarvis_command' bereitstellen (für eigene Automationen)."""
        try:
            requests.post(
                f"{HA_URL}/events/gjarvis_command",
                headers={"Authorization": f"Bearer {HA_TOKEN}"},
                json={"text": text, "text_lower": text.lower().strip(" .!?")},
                timeout=5,
            )
        except Exception as e:  # noqa: BLE001
            _LOGGER.debug("Ereignis nicht gesendet: %s", e)

    def local_command(self, text: str) -> Optional[Tuple[str, bool]]:
        """Home Assistants eigener Agent: Geräte-Befehle UND deine eigenen Satz-Automationen."""
        agent = self.o.get("local_agent_id", "conversation.home_assistant")
        if not agent:
            return None
        r = requests.post(
            f"{HA_URL}/conversation/process",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json={"text": text, "language": self.o["language"], "agent_id": agent},
            timeout=15,
        )
        r.raise_for_status()
        resp = r.json().get("response", {})
        if resp.get("response_type") == "error":
            return None
        speech = resp.get("speech", {}).get("plain", {}).get("speech", "") or self.anrede("Erledigt")
        _LOGGER.info("Lokal erledigt (Home Assistant)")
        return speech, False

    def answer(self, text: str) -> Tuple[str, bool]:
        import threading

        threading.Thread(target=self.fire_command_event, args=(text,), daemon=True).start()  # blockiert nicht
        if not self.pro:
            # Free: wie ein normaler Home-Assistant-Sprachsatellit (Uhrzeit/Datum sofort selbst)
            ta = self.time_answer(text)
            if ta:
                return ta, False
            try:
                local = self.local_command(text)
                if local:
                    return local
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Lokaler HA-Agent nicht erreichbar: %s", e)
            return self.converse(text)
        # Apps aus Home Assistant: Mealie (Essensplan, Rezepte, Rezept aus dem Internet), Listen vorlesen
        app = self.apps_answer(text)
        if app is not None:
            return app
        if not self.wants_weather(text) and not self.wants_research(text) and not self.wants_flight(text):
            try:
                local = self.local_command(text)
                if local:
                    return local
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Lokaler HA-Agent nicht erreichbar: %s", e)
        if self.wants_flight(text):
            try:
                return self.flight_answer(text), False
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Flugwetter fehlgeschlagen: %s", e)
        if self.wants_weather(text):
            try:
                return self.weather_answer(text), False
            except LookupError as e:
                # Vorhersage reicht nicht so weit -> im Internet nachschauen
                _LOGGER.info("Wetter: %s – schaue im Internet nach", e)
                city = (self.o.get("home_city") or "").strip()
                q = str(e)
                if "wetter" not in q.lower():
                    q = f"Wetter {q}"
                if city and city.lower() not in q.lower():
                    q = f"{q} {city}"
                return self.research(text, q), False
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Wetter direkt fehlgeschlagen (%s) – frage Home Assistant", e)
        if self.o.get("master_router", True) and self.o.get("research_enabled", True) and self.has_llm():
            try:
                t0 = time.monotonic()
                r = self.master_route(text)
                _LOGGER.info("Verteiler (%.1f s): %s %s", time.monotonic() - t0, r["aktion"], r["suchanfrage"])
                if r["aktion"] == "suche":
                    return self.research(text, r["suchanfrage"] or None), False
                if r["aktion"] == "antwort":
                    if r["antwort"] and not self.is_refusal(r["antwort"]):
                        return r["antwort"], False
                    return self.chat(text), False
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Verteiler nicht verfügbar: %s", e)
        speech, cont = self.converse(text)
        if self.o.get("research_enabled", True) and self.is_refusal(speech):
            _LOGGER.info("KI kann es nicht beantworten – recherchiere selbst")
            try:
                return self.research(text), False
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Recherche fehlgeschlagen: %s", e)
        return speech, cont

    # ----------------------------- Recherche (Wikipedia / Internet) -------- #
    # Fragen nach Aktuellem -> immer recherchieren (zusätzlich zu den Suchwörtern in den Einstellungen)
    CURRENT_HINTS = [
        "kino", "kinoprogramm", "nachrichten", "news", "neuigkeiten", "schlagzeilen", "aktuell",
        "öffnungszeit", "geöffnet", "hat offen", "wer hat gewonnen", "ergebnis", "spielstand", "tabelle",
        "was kostet", "preis von", "benzinpreis", "spritpreis", "veranstaltung", "konzert", "fahrplan",
        "verkehr", "stau", "börse", "aktienkurs", "wechselkurs", "was läuft", "was gibt es neues",
        "wer ist der", "wer ist die", "wann ist", "wann kommt", "wann spielt",
    ]
    REFUSALS = [
        "kann ich nicht", "kann über", "nicht informieren", "keinen zugriff", "keine aktuellen",
        "suchmaschine", "nicht verfügbar", "habe keine informationen", "keine echtzeit", "nicht abrufen",
        "kann leider nicht", "nicht in der lage", "nicht unter den integrierten", "kann keine", "keine prognose",
        "nicht vorhersagen", "keinen zugang",
    ]

    def wants_research(self, text: str) -> bool:
        if not self.o.get("research_enabled", True) or not self.pro:
            return False
        t = text.lower()
        trig = [x for x in self.o.get("research_triggers", []) if x.strip()]
        return any(x.lower() in t for x in trig) or any(h in t for h in self.CURRENT_HINTS)

    ROUTER_PROMPT = (
        "Du bist der Verteiler eines Sprachassistenten. Entscheide, wie die Anfrage erledigt wird, und antworte NUR "
        'mit JSON: {"aktion": "suche"|"haus"|"antwort", "suchanfrage": "...", "antwort": "..."}.\n'
        "- suche: braucht aktuelle oder externe Informationen aus dem Internet (Kino, Nachrichten, Öffnungszeiten, "
        "Preise, Personen, Ereignisse, Sport, Termine, Produkte, alles nach 2023). Formuliere eine kurze, gute "
        "Suchanfrage auf Deutsch.\n"
        "- haus: Geräte, Licht, Heizung, Szenen, Listen, Timer, Erinnerungen, Zustände im Haus.\n"
        "- antwort: allgemeines Wissen, Rechnen, Witze, Plaudern, Ratschläge. Dann schreibst du die fertige, "
        "vorlesbare Antwort (höchstens drei kurze Sätze, Deutsch) direkt in das Feld antwort.\n"
        "Beispiele:\n"
        'Was läuft heute im Kino? -> {"aktion":"suche","suchanfrage":"Kinoprogramm heute"}\n'
        'Wie hat Bayern gespielt? -> {"aktion":"suche","suchanfrage":"FC Bayern letztes Spiel Ergebnis"}\n'
        'Mach es im Wohnzimmer gemütlich -> {"aktion":"haus","suchanfrage":""}\n'
        'Wie viel ist 17 mal 23? -> {"aktion":"antwort","suchanfrage":"","antwort":"17 mal 23 ist 391."}'
    )

    def master_route(self, text: str) -> dict:
        """Die KI entscheidet in EINEM Aufruf: suchen, Haus steuern oder gleich selbst antworten."""
        now = time.strftime("%d.%m.%Y, %H:%M Uhr")
        # gleichbleibender System-Text (Zwischenspeicher im KI-Modell), Wechselndes in die Nutzer-Nachricht
        system = (f"{self.ROUTER_PROMPT}\n\nFür das Feld antwort: {self.o.get('system_prompt', '')} "
                  f"{self.o.get('persona', '')}")
        if time.monotonic() - self.history_ts > 300:
            self.history = []
        ctx = f"(Jetzt: {now}.{self.memory_prompt()})\n"
        msgs = [{"role": "system", "content": system}] + self.history[-4:] + [{"role": "user", "content": ctx + text}]
        raw = self.ask_llm(msgs, json_mode=True, max_tokens=220)
        m = re.search(r"\{.*\}", raw, re.S)
        try:
            d = json.loads(m.group(0) if m else raw)
        except Exception:  # noqa: BLE001
            d = {}
        a = str(d.get("aktion", "")).lower()
        if a not in ("suche", "haus", "antwort"):
            a = "antwort"
        ans = self.clean_for_speech(str(d.get("antwort") or ""))
        if a == "antwort" and ans:
            self.history += [{"role": "user", "content": text}, {"role": "assistant", "content": ans}]
            self.history = self.history[-12:]
            self.history_ts = time.monotonic()
        return {"aktion": a, "suchanfrage": str(d.get("suchanfrage") or "").strip(), "antwort": ans}

    def is_refusal(self, answer: str) -> bool:
        a = (answer or "").lower()
        return any(r in a for r in self.REFUSALS)

    @staticmethod
    def extract_query(text: str) -> str:
        q = text.strip().rstrip("?.!")
        patterns = [
            r"^(hey |hallo )?jarvis[, ]*",
            r"\b(kannst du |könntest du |bitte |mal |doch )",
            r"\b(such(e)?|schau|guck)( mal)?( bitte)? (im internet|bei google|in (der )?wikipedia|auf wikipedia|bei wikipedia|online|im netz)( nach)?\b",
            r"\b(google|googel|recherchier(e)?)( mal)?( bitte)?( nach)?\b",
            r"\b(such(e)?|schau|guck)( mal)?( bitte)? nach\b",
            r"\b(was sagt|laut) (die )?wikipedia (zu|über)?\b",
            r"\b(in|auf|bei) (der )?wikipedia\b",
            r"\b(im internet|im netz|bei google)\b",
            r"^(nach|über|zu)\s+",
        ]
        for p in patterns:
            q = re.sub(p, " ", q, flags=re.IGNORECASE)
            q = re.sub(r"\s+", " ", q).strip()
        q = re.sub(r"\s+", " ", q).strip(" ,")
        return q or text

    def search_wikipedia(self, query: str, n: int = 2) -> List[dict]:
        lang = self.o.get("wikipedia_lang", "de")
        base = os.environ.get("GJARVIS_WIKI_BASE") or f"https://{lang}.wikipedia.org"
        headers = {"User-Agent": "GJarvis/1.7 (Home Assistant app)"}
        r = requests.get(
            f"{base}/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query, "srlimit": n, "format": "json"},
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        out = []
        for hit in r.json().get("query", {}).get("search", [])[:n]:
            title = hit["title"]
            s = requests.get(
                f"{base}/api/rest_v1/page/summary/{requests.utils.quote(title.replace(' ', '_'))}",
                headers=headers,
                timeout=10,
            )
            if s.ok:
                out.append({"title": title, "text": s.json().get("extract", ""), "source": "Wikipedia"})
        return out

    def search_web(self, query: str, n: int = 6) -> List[dict]:
        url = (self.o.get("searxng_url") or "").rstrip("/")
        if url:
            r = requests.get(
                f"{url}/search",
                params={"q": query, "format": "json", "language": self.o.get("language", "de")},
                timeout=15,
            )
            r.raise_for_status()
            return [
                {"title": x.get("title", ""), "text": x.get("content", ""), "source": x.get("url", "")}
                for x in r.json().get("results", [])[:n]
            ]
        # Eingebaute Suche ohne Schlüssel (DuckDuckGo, Bing, Google u. a. über ddgs)
        try:
            from ddgs import DDGS

            hits = DDGS().text(query, region="de-de", safesearch="moderate", max_results=n)
            return [{"title": h.get("title", ""), "text": h.get("body", ""), "source": h.get("href", "")} for h in hits]
        except Exception as e:  # noqa: BLE001
            _LOGGER.info("ddgs nicht nutzbar (%s) – versuche DuckDuckGo HTML", e)
        r = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "de-de"},
            headers={"User-Agent": "Mozilla/5.0 (GJarvis)"},
            timeout=15,
        )
        r.raise_for_status()
        out = []
        for m in re.finditer(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</a>',
            r.text,
            re.S,
        ):
            strip = lambda h: re.sub(r"<[^>]+>", "", h).replace("&amp;", "&").replace("&quot;", '"').strip()
            out.append({"title": strip(m.group(2)), "text": strip(m.group(3)), "source": m.group(1)})
            if len(out) >= n:
                break
        return out

    def localize_query(self, query: str, text: str) -> str:
        """Bei Ortsfragen (Kino, Öffnungszeiten …) den Wohnort ergänzen."""
        city = (self.o.get("home_city") or "").strip()
        t = text.lower()
        if city and city.lower() not in query.lower() and any(
            w in t for w in ("kino", "öffnungszeit", "geöffnet", "hat offen", "veranstaltung", "konzert", "stau",
                             "verkehr", "fahrplan", "benzinpreis", "spritpreis", "in der nähe", "hier")
        ):
            query = f"{query} {city}"
        if "kino" in t and "programm" not in query.lower():
            query = f"Kinoprogramm heute {query.replace('Was läuft aktuell im Kino', '').strip()}".strip()
        return query

    def ask_llm(self, messages: List[dict], json_mode: bool = False, max_tokens: int = 300,
                model: Optional[str] = None) -> str:
        kind = self.o.get("research_llm_type", "ollama")
        if kind == "ha_agent":
            return self.ask_ha_agent(messages, json_mode, model)
        url = (self.o.get("research_llm_url") or "").rstrip("/")
        if not url:
            raise RuntimeError("Kein KI-Modell eingetragen (Oberfläche: Karte „KI-Modell“)")
        model = model or self.o.get("research_llm_model") or self.auto_model(kind, url)
        if kind == "openai":
            if not url.endswith("/v1"):
                url += "/v1"
            headers = {}
            if self.o.get("research_llm_api_key"):
                headers["Authorization"] = f"Bearer {self.o['research_llm_api_key']}"
            r = requests.post(
                f"{url}/chat/completions",
                json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3,
                      **({"response_format": {"type": "json_object"}} if json_mode else {})},
                headers=headers,
                timeout=180,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        body = {"model": model, "messages": messages, "stream": False, "keep_alive": -1,
                "options": {"num_predict": max_tokens, "temperature": 0.2 if json_mode else 0.3,
                            "num_ctx": int(self.o.get("llm_context", 4096))},
                **({"format": "json"} if json_mode else {})}
        if re.match(r"(qwen3|deepseek-r1|gemma4|gpt-oss|magistral)", model.lower()):
            body["think"] = False  # Denk-Modus aus – sonst "denkt" das Modell minutenlang, bevor es antwortet
        r = requests.post(f"{url}/api/chat", json=body, timeout=180)
        if r.status_code == 400 and "think" in body:
            body.pop("think")
            r = requests.post(f"{url}/api/chat", json=body, timeout=180)
        r.raise_for_status()
        return r.json()["message"]["content"]

    def has_llm(self) -> bool:
        """Gibt es eine echte KI? (Der eingebaute HA-Agent 'conversation.home_assistant' ist keine.)"""
        kind = self.o.get("research_llm_type", "ollama")
        if kind == "ha_agent":
            agent = self.o.get("llm_agent_id") or self.o.get("agent_id") or ""
            return bool(agent) and agent != "conversation.home_assistant"
        return bool(self.o.get("research_llm_url"))

    def auto_model(self, kind: str, url: str) -> str:
        """Kein Modell eingetragen: das kleinste installierte nehmen (der Nutzer bringt sein eigenes mit)."""
        ms = self.llm_models(kind, url)
        if not ms:
            raise RuntimeError("Auf dem KI-Server ist kein Modell installiert")
        name = ms[0]["name"]
        self.o["research_llm_model"] = name
        _LOGGER.info("Kein KI-Modell gewählt – nehme %s", name)
        return name

    def ask_ha_agent(self, messages: List[dict], json_mode: bool, agent: Optional[str] = None) -> str:
        """KI über einen Home-Assistant-Gesprächsagenten (OpenAI, Google, Anthropic, Ollama … – was der Nutzer
        in Home Assistant eingerichtet hat). Die Anweisungen werden als Text vorangestellt."""
        agent = agent or self.o.get("llm_agent_id") or self.o.get("agent_id") or "conversation.home_assistant"
        parts = []
        for m in messages:
            if m["role"] == "system":
                parts.append(f"Anweisung: {m['content']}")
            elif m["role"] == "assistant":
                parts.append(f"Deine letzte Antwort: {m['content']}")
            else:
                parts.append(m["content"])
        if json_mode:
            parts.append("Antworte ausschließlich mit dem JSON-Objekt, ohne weiteren Text.")
        r = requests.post(f"{HA_URL}/conversation/process", headers={"Authorization": f"Bearer {HA_TOKEN}"},
                          json={"text": "\n\n".join(parts), "language": self.o.get("language", "de"), "agent_id": agent},
                          timeout=180)
        r.raise_for_status()
        return ((r.json().get("response") or {}).get("speech") or {}).get("plain", {}).get("speech", "")

    def llm_discover(self) -> List[dict]:
        """KI-Server im Netz/Home Assistant finden: Ollama-App, eingetragene Adresse, typische Adressen."""
        found, seen = [], set()
        cands = []
        try:
            for a in self.sup("GET", "/addons").get("addons", []):
                slug = a.get("slug", "")
                if "ollama" in slug.lower() and a.get("state") == "started":
                    cands.append(("ollama", f"http://{slug.replace('_', '-')}:11434", f"App {a.get('name', slug)}"))
        except Exception:  # noqa: BLE001
            pass
        if self.o.get("research_llm_url"):
            cands.append((self.o.get("research_llm_type", "ollama"), self.o["research_llm_url"], "eingetragen"))
        cands += [("ollama", "http://homeassistant.local:11434", "Home Assistant"),
                  ("openai", "http://homeassistant.local:1234", "LM Studio")]
        for kind, url, label in cands:
            url = url.rstrip("/")
            if url in seen:
                continue
            seen.add(url)
            try:
                if kind == "ollama":
                    r = requests.get(f"{url}/api/tags", timeout=2)
                    n = len(r.json().get("models", []))
                else:
                    r = requests.get(f"{url}/v1/models", timeout=2)
                    n = len(r.json().get("data", []))
                found.append({"type": kind, "url": url, "label": label, "models": n})
            except Exception:  # noqa: BLE001
                continue
        return found

    # ----------------------------- KI-Modell wählen / vergleichen ----------- #
    BENCH_QUESTIONS = [
        "Erzähl mir einen kurzen Witz.",
        "Was ist ein U-Boot?",
        "Was läuft heute im Kino?",
    ]

    def same_llm_url(self, url: str) -> bool:
        """Ist url die eingetragene research_llm_url (ohne / am Ende, mit oder ohne /v1)?"""
        norm = lambda u: re.sub(r"/v1$", "", str(u or "").strip().rstrip("/")).rstrip("/").lower()
        conf = norm(self.o.get("research_llm_url"))
        return bool(conf) and norm(url) == conf

    def llm_models(self, kind: Optional[str] = None, url: Optional[str] = None, key: Optional[str] = None) -> List[dict]:
        kind = kind or self.o.get("research_llm_type", "ollama")
        url = (url if url is not None else (self.o.get("research_llm_url") or "")).rstrip("/")
        if kind == "ha_agent":
            sts = self.ha_get("/states")
            return [{"name": x["entity_id"], "size_gb": None, "params": (x.get("attributes") or {}).get("friendly_name", "")}
                    for x in sts if x["entity_id"].startswith("conversation.")]
        if not url:
            return []
        if kind == "openai":
            u = url if url.endswith("/v1") else url + "/v1"
            if key is None and self.same_llm_url(url):
                # gespeicherten Schlüssel NUR an die eingetragene Adresse schicken – nie an eine fremde URL
                key = self.o.get("research_llm_api_key")
            r = requests.get(f"{u}/models", timeout=10, headers={"Authorization": f"Bearer {key}"} if key else {})
            r.raise_for_status()
            return sorted([{"name": m["id"], "size_gb": None, "params": ""} for m in r.json().get("data", [])],
                          key=lambda m: m["name"])
        r = requests.get(f"{url}/api/tags", timeout=10)
        r.raise_for_status()
        out = [{"name": m["name"], "size_gb": round(m.get("size", 0) / 1e9, 1),
                "params": (m.get("details") or {}).get("parameter_size", "")} for m in r.json().get("models", [])]
        return sorted(out, key=lambda m: m["size_gb"] or 0)

    def llm_unload(self, model: str) -> None:
        url = (self.o.get("research_llm_url") or "").rstrip("/")
        if url and model and self.o.get("research_llm_type", "ollama") == "ollama":
            try:
                requests.post(f"{url}/api/generate", json={"model": model, "keep_alive": 0}, timeout=30)
            except Exception:  # noqa: BLE001
                pass

    def llm_benchmark(self, models: List[str]) -> None:
        """Jedes Modell mit denselben Fragen testen (wie Jarvis sie stellt) – Ladezeit, Antwortzeit, Antworten."""
        self.bench = {"running": True, "results": [], "current": ""}
        url = (self.o.get("research_llm_url") or "").rstrip("/")
        current = self.o.get("research_llm_model", "")
        for m in models:
            self.bench["current"] = m
            res = {"model": m, "load_s": None, "avg_s": None, "answers": [], "error": ""}
            try:
                t0 = time.monotonic()
                if self.o.get("research_llm_type", "ollama") == "ollama":
                    requests.post(f"{url}/api/generate", json={"model": m, "keep_alive": "5m",
                                  "options": {"num_ctx": int(self.o.get("llm_context", 4096))}}, timeout=300)
                res["load_s"] = round(time.monotonic() - t0, 1)
                times = []
                for q in self.BENCH_QUESTIONS:
                    system = (f"{self.ROUTER_PROMPT}\n\nFür das Feld antwort: {self.o.get('system_prompt', '')} "
                              f"{self.o.get('persona', '')}")
                    t1 = time.monotonic()
                    raw = self.ask_llm([{"role": "system", "content": system}, {"role": "user", "content": q}],
                                       json_mode=True, max_tokens=220, model=m)
                    times.append(time.monotonic() - t1)
                    try:
                        d = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
                    except Exception:  # noqa: BLE001
                        d = {"aktion": "?", "antwort": raw[:120]}
                    res["answers"].append({"frage": q, "aktion": str(d.get("aktion", "?")),
                                           "text": self.clean_for_speech(str(d.get("antwort") or d.get("suchanfrage") or ""))[:160],
                                           "s": round(times[-1], 1)})
                res["avg_s"] = round(sum(times) / len(times), 1)
            except Exception as e:  # noqa: BLE001
                res["error"] = str(e)[:160]
            self.bench["results"].append(res)
            if m != current and self.o.get("research_llm_type", "ollama") == "ollama":
                self.llm_unload(m)
            _LOGGER.info("Modell-Vergleich %s: laden %s s, Antwort Ø %s s", m, res["load_s"], res["avg_s"])
        self.bench.update(running=False, current="")

    async def llm_warm_loop(self) -> None:
        """Hält das KI-Modell im Speicher, damit die erste Frage nicht 20 s Ladezeit kostet."""
        await asyncio.sleep(5)
        while True:
            if (self.pro and self.o.get("research_llm_url") and self.o.get("research_llm_model")
                    and self.o.get("research_llm_type", "ollama") == "ollama" and not self.busy):
                try:
                    t0 = time.monotonic()
                    await asyncio.to_thread(
                        requests.post, self.o["research_llm_url"].rstrip("/") + "/api/generate",
                        json={"model": self.o["research_llm_model"], "keep_alive": -1,
                              "options": {"num_ctx": int(self.o.get("llm_context", 4096))}}, timeout=120)
                    dt_s = time.monotonic() - t0
                    if dt_s > 2:
                        _LOGGER.info("KI-Modell %s geladen (%.0f s)", self.o["research_llm_model"], dt_s)
                except Exception as e:  # noqa: BLE001
                    _LOGGER.debug("KI-Modell nicht vorgeladen: %s", e)
            self.llm_next_warm = time.monotonic() + 600
            while time.monotonic() < getattr(self, "llm_next_warm", 0):
                await asyncio.sleep(5)  # bei Modellwechsel (llm_next_warm = 0) sofort neu laden

    @staticmethod
    def clean_for_speech(text: str) -> str:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # Markdown-Links
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"[\u3000-\u9fff\uac00-\ud7af\uff00-\uffef]+", "", text)  # verirrte chinesische Zeichen (Qwen)
        text = re.sub(r"[*_#`>|]+", "", text)
        text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.MULTILINE)
        return re.sub(r"\s+", " ", text).strip()

    def research(self, text: str, query: Optional[str] = None) -> str:
        query = self.localize_query(query or self.extract_query(text), text)
        t = text.lower()
        only_wiki = "wikipedia" in t
        _LOGGER.info("Recherche: %r", query)
        results: List[dict] = []
        try:
            if not only_wiki:
                results += self.search_web(query)
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("Internetsuche fehlgeschlagen: %s", e)
        try:
            if only_wiki or len(results) < 2:
                results += self.search_wikipedia(query)
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("Wikipedia-Suche fehlgeschlagen: %s", e)
        _LOGGER.info("%d Suchergebnisse", len(results))
        if not results:
            return self.anrede("Dazu habe ich leider nichts gefunden")
        context = "\n\n".join(
            f"[{i + 1}] {r['title']} ({r['source']}): {r['text'][:1200]}" for i, r in enumerate(results)
        )
        messages = [
            {"role": "system", "content": self.o["system_prompt"]},
            {
                "role": "user",
                "content": f"Heute ist {time.strftime('%d.%m.%Y')}. Frage: {text}\n\nSuchergebnisse:\n{context}\n\n"
                "Beantworte die Frage nur mit Hilfe der Suchergebnisse. Nenne konkrete Namen, Zeiten oder Zahlen, "
                "wenn sie drinstehen.",
            },
        ]
        if not self.has_llm():
            # ohne KI: den besten Treffer vorlesen (erste zwei Sätze)
            r0 = results[0]
            sents = re.split(r"(?<=[.!?])\s+", self.clean_for_speech(r0["text"]))
            return " ".join(sents[:2])[:300] or self.anrede("Dazu habe ich leider nichts gefunden")
        t0 = time.monotonic()
        answer = self.clean_for_speech(self.ask_llm(messages))
        _LOGGER.info("KI-Antwort (%.1f s, %s)", time.monotonic() - t0, self.o.get("research_llm_model") or self.o.get("research_llm_type"))
        return answer or self.anrede("Dazu habe ich leider keine Antwort gefunden")

    # ----------------------------- Rückmeldung ----------------------------- #
    INSTANT_DEFAULT = ["Moment, ich schaue nach.", "Einen Augenblick.", "Ich sehe mal nach."]
    WEATHER_ACK_DEFAULT = ["Moment, ich schaue nach dem Wetter.", "Ich sehe mir das Wetter an.", "Einen Augenblick, ich schaue nach."]
    PROGRESS_DEFAULT = ["Ich schaue noch.", "Einen Moment noch.", "Ich bin noch dran.", "Gleich habe ich es."]
    PHRASE_DEFAULTS = {
        "instant_ack_phrases": INSTANT_DEFAULT,
        "weather_ack_phrases": WEATHER_ACK_DEFAULT,
        "progress_phrases": PROGRESS_DEFAULT,
    }

    def next_ack(self, key: str = "ack_phrases") -> Optional[str]:
        raw = self.o.get(key)
        if raw is None:
            raw = self.PHRASE_DEFAULTS.get(key)
        phrases = [p for p in (raw or []) if p.strip()]
        if not phrases:
            return None
        if self.o.get("ack_order") == "random":
            # zufällig, aber nie zweimal hintereinander derselbe Satz
            last = self._last_phrase.get(key)
            pick = random.choice([p for p in phrases if p != last] or phrases)
            self._last_phrase[key] = pick
            return pick
        if key == "ack_phrases":
            idx = self.ack_index
            self.ack_index += 1
        else:
            counters = self.__dict__.setdefault("phrase_index", {})
            idx = counters.get(key, 0)
            counters[key] = idx + 1
        return phrases[idx % len(phrases)]

    # ----------------------- Zwischenmeldungen ----------------------------- #
    def progress_settings(self) -> Tuple[float, int]:
        """Abstand und Höchstzahl der Zwischenmeldungen ("Ich schaue noch") – (0, 0) = aus."""
        if not self.o.get("progress_enabled", True):
            return 0.0, 0
        return max(3.0, float(self.o.get("progress_interval_seconds", 8))), int(self.o.get("progress_max", 4))

    async def wait_with_progress(self, task: "asyncio.Future", timeout: float) -> bool:
        """Im Gespräch auf eine Antwort warten und dabei regelmäßig "Ich schaue noch" sagen.
        Gibt True zurück, wenn die Antwort innerhalb von timeout fertig wurde."""
        interval, max_n = self.progress_settings()
        end = time.monotonic() + timeout
        said = 0
        while True:
            left = end - time.monotonic()
            if left <= 0:
                return task.done()
            step = min(left, interval) if (interval and said < max_n) else left
            done, _ = await asyncio.wait({task}, timeout=step)
            if done:
                return True
            if interval and said < max_n and end - time.monotonic() > 1.0:
                said += 1
                await self.play_ack("progress_phrases")

    async def progress_in_background(self, task: "asyncio.Future") -> None:
        """Hintergrund-Aufgabe läuft: regelmäßig kurz melden, dass Jarvis noch dran ist –
        aber nur, wenn er gerade frei ist (kein Gespräch, keine andere Ansage)."""
        interval, max_n = self.progress_settings()
        said = 0
        while interval and said < max_n and not task.done():
            done, _ = await asyncio.wait({task}, timeout=interval)
            if done:
                return
            if self.busy:
                continue
            self.busy = True
            try:
                self.set_state("responding")
                await self.play_ack("progress_phrases")
                said += 1
            finally:
                self.busy = False
                self.flush()
                if self.oww:
                    self.oww.reset()
                self.last_wake = time.monotonic()
                self.set_state("idle")

    # ------------------- Sofort-Rückmeldung ("Moment, ich schaue nach") ------------------- #
    SLOW_HINTS = (
        "recherch", "such ", "suche ", "google", "im internet", "nachrichten", "rezept", "essensplan",
        "erklär", "erzähl", "warum ", "wieso ", "weshalb ", "wer ist", "wer war", "was ist ein", "was bedeutet",
        "wie funktioniert", "wie viel kostet", "wann ist", "wann kommt", "wann spielt", "brauche ich", "schirm",
    )

    def is_slow(self, text: str) -> bool:
        """Dauert die Antwort voraussichtlich länger (Internet, Wetter, KI)? Dann sagt Jarvis sofort
        "Moment, ich schaue nach" – bei Licht, Timer, Uhrzeit nicht."""
        t = " " + text.lower().strip(" .!?") + " "
        try:
            if self.wants_weather(text) or self.wants_flight(text) or self.wants_research(text):
                return True
            if hasattr(self, "wants_briefing") and self.wants_briefing(text):
                return True
        except Exception:  # noqa: BLE001
            pass
        extra = [x.lower() for x in (self.o.get("ack_slow_triggers") or []) if x.strip()]
        return any(h in t for h in self.SLOW_HINTS) or any(x in t for x in extra)

    def ack_key_for(self, text: str) -> str:
        try:
            if self.wants_weather(text) or self.wants_flight(text):
                return "weather_ack_phrases"
        except Exception:  # noqa: BLE001
            pass
        return "instant_ack_phrases"

    def start_ack(self, text: str) -> Optional["asyncio.Task"]:
        """Rückmeldung planen: bei langsamen Fragen sofort, sonst erst, wenn die Antwort nach
        ack_delay_ms noch nicht fertig ist. settle_ack() bricht sie ab, wenn die Antwort schneller war."""
        mode = self.o.get("ack_mode", "slow")
        if mode == "off" or not self.pro:
            return None
        slow = mode == "always" or self.is_slow(text)
        delay = 0.0 if slow else max(0.0, float(self.o.get("ack_delay_ms", 900)) / 1000.0)
        if not slow and delay <= 0:
            return None
        key = self.ack_key_for(text)
        self._ack_began = False
        _LOGGER.info("Rückmeldung %s", "sofort" if slow else f"nach {delay:.1f} s, falls nötig")

        async def run() -> bool:
            if delay:
                await asyncio.sleep(delay)
            self._ack_began = True
            await self.play_ack(key)
            return True

        return asyncio.create_task(run())

    async def settle_ack(self, task: Optional["asyncio.Task"]) -> bool:
        """Vor der eigentlichen Antwort: noch nicht begonnene Rückmeldung abbrechen, laufende zu Ende
        sprechen lassen. True = es wurde eine Rückmeldung gesprochen."""
        if task is None:
            return False
        if not task.done() and not self._ack_began:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
            return False
        try:
            return bool(await task)
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            return self._ack_began

    async def preload_acks(self) -> None:
        for p in (list(self.o.get("ack_phrases", [])) + list(self.o.get("instant_ack_phrases", self.INSTANT_DEFAULT))
                  + list(self.o.get("weather_ack_phrases", self.WEATHER_ACK_DEFAULT))
                  + list(self.o.get("progress_phrases", self.PROGRESS_DEFAULT))):
            try:
                self.ack_cache[p] = await self.synthesize(p)
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Rückmeldung '%s' konnte nicht vorbereitet werden: %s", p, e)
        _LOGGER.info("%d Rückmeldungen vorbereitet", len(self.ack_cache))

    async def play_ack(self, key: str = "ack_phrases") -> None:
        phrase = self.next_ack(key)
        if not phrase:
            return
        self.discard = True
        self.remote_stop = False
        try:
            if self.remote_tts:
                async with self.speech_lock:
                    await self.speak_remote_tts(phrase)
                return
            if phrase not in self.ack_cache:
                self.ack_cache[phrase] = await self.synthesize(phrase)
            pcm, fmt = self.ack_cache[phrase]
            await self.play_pcm(pcm, *fmt)
        except Exception as e:  # noqa: BLE001
            _LOGGER.error("Rückmeldung fehlgeschlagen: %s", e)
        finally:
            await asyncio.sleep(0.2)
            self.flush()
            self.discard = False

    # ----------------------------- Zuhören --------------------------------- #
    async def speech_continues(self, seconds: float = 0.6) -> Tuple[bool, List[bytes]]:
        """Direkt nach dem Weckwort kurz hinhören: Spricht er schon weiter ("Hey Jarvis, wie spät ist es")?
        Gibt (ja/nein, gehörte Blöcke) zurück – die Blöcke gehen danach in die Aufnahme, nichts geht verloren."""
        vad = self.make_vad()
        frames: List[bytes] = []
        voiced = 0
        end = time.monotonic() + seconds
        buf = b""
        while time.monotonic() < end:
            try:
                fr = await asyncio.wait_for(self.queue.get(), timeout=max(0.05, end - time.monotonic()))
            except asyncio.TimeoutError:
                break
            frames.append(fr)
            buf += fr
            while len(buf) >= VAD_CHUNK_BYTES:
                chunk, buf = buf[:VAD_CHUNK_BYTES], buf[VAD_CHUNK_BYTES:]
                sp, _ = self.is_speech(vad, chunk, voiced > 0)
                voiced += int(sp)
        need = max(3, int(self.o.get("speech_start_ms", 150)) // 30)
        return voiced >= need, frames

    def make_vad(self):
        """Silero-Sprach-Erkennung (robust, pegelunabhängig); Fallback webrtcvad."""
        if self.silero_path:
            from openwakeword.vad import VAD

            v = VAD(str(self.silero_path))

            class _S:
                def prob(self, a16):
                    return float(v.predict(a16, frame_size=VAD_CHUNK))

                def reset(self):
                    v.reset_states()

            return _S()
        w = webrtcvad.Vad(int(self.o.get("vad_mode", 1)))

        class _W:
            def prob(self, a16):
                return 1.0 if w.is_speech(a16.tobytes(), RATE) else 0.0

            def reset(self):
                pass

        return _W()

    def is_speech(self, vad, chunk: bytes, started: bool = False) -> Tuple[bool, float]:
        """Sprache erkennen – relativ zum Raumrauschen, mit Hysterese (Wortpausen werden toleriert)."""
        a = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
        rms = float(np.sqrt(np.mean(a * a))) if len(a) else 0.0
        if rms < 1.0:  # digitale Stille (Mikrofon hing) -> Erkennung zurücksetzen
            vad.reset()
            return False, rms
        gain = min(20.0, 600.0 / max(self.noise_floor, 1.0))
        a16 = np.clip(a * gain, -32768, 32767).astype(np.int16)
        p = vad.prob(a16)
        thr = float(self.o.get("speech_threshold", 0.4))
        return (p >= (thr * 0.7 if started else thr)), rms

    async def record_command(self, timeout: Optional[float] = None, prefill: Optional[List[bytes]] = None) -> Optional[bytes]:
        """Nimmt einen Befehl auf. None = nichts gesagt (Abbruch nach Timeout)."""
        vad = self.make_vad()
        no_speech = float(timeout if timeout else self.o["no_speech_timeout_seconds"])
        end_sil_ms = float(self.o["end_of_speech_silence_seconds"]) * 1000
        max_ms = float(self.o["max_command_seconds"]) * 1000
        start_need = max(1, int(self.o.get("speech_start_ms", SPEECH_START_MS)) // 30)
        window_n = start_need * 2  # z. B. 5 von 10 Blöcken müssen Sprache sein
        preroll_n = int(self.o.get("preroll_ms", 2000)) // 30

        started = False
        flags: List[bool] = []
        silence_ms = 0.0
        speech_ms = 0.0
        max_rms = 0.0
        voiced_total = 0
        preroll: List[bytes] = []
        audio: List[bytes] = []
        buf = b""
        t0 = time.monotonic()

        while True:
            remaining = no_speech - (time.monotonic() - t0)
            if not started and remaining <= 0:
                _LOGGER.info(
                    "Nichts gesagt – Abbruch nach %.0f s (lautester Pegel %.0f, Grundrauschen %.0f, "
                    "Sprachblöcke %d)",
                    no_speech,
                    max_rms,
                    self.noise_floor,
                    voiced_total,
                )
                return None
            try:
                if prefill:
                    frame = prefill.pop(0)
                else:
                    frame = await asyncio.wait_for(self.queue.get(), timeout=max(0.1, remaining if not started else 2))
            except asyncio.TimeoutError:
                if started:
                    return b"".join(audio)
                continue
            buf += frame
            while len(buf) >= VAD_CHUNK_BYTES:
                chunk, buf = buf[:VAD_CHUNK_BYTES], buf[VAD_CHUNK_BYTES:]
                speech, rms = self.is_speech(vad, chunk, started)
                max_rms = max(max_rms, rms)
                voiced_total += int(speech)
                if not started:
                    preroll.append(chunk)
                    if len(preroll) > preroll_n:
                        preroll.pop(0)
                    flags.append(speech)
                    if len(flags) > window_n:
                        flags.pop(0)
                    if sum(flags) >= start_need:
                        started = True
                        audio = list(preroll)
                        _LOGGER.info("Sprache erkannt (Pegel %.0f, Grundrauschen %.0f)", rms, self.noise_floor)
                else:
                    audio.append(chunk)
                    speech_ms += 30
                    silence_ms = 0 if speech else silence_ms + 30
                    if silence_ms >= end_sil_ms:
                        return b"".join(audio)
                    if speech_ms >= max_ms:
                        _LOGGER.info("Maximale Befehlslänge erreicht")
                        return b"".join(audio)

    # ----------------------------- Lärmprotokoll --------------------------- #
    def schedule_resume(self, delay: float = 0.0) -> None:
        if self.resume_task:
            self.resume_task.cancel()

        async def _resume() -> None:
            await asyncio.sleep(delay)
            self.publish(self.o["mqtt_pause_topic"], self.o["mqtt_resume_payload"])
            self.noise_paused = False
            self.resume_task = None

        self.resume_task = asyncio.create_task(_resume())

    # ----------------------------- Hintergrund-Aufgaben -------------------- #
    async def run_research(self, text: str) -> str:
        try:
            return await asyncio.to_thread(self.research, text)
        except Exception as e:  # noqa: BLE001
            _LOGGER.error("Recherche fehlgeschlagen: %s", e)
            return self.anrede("Die Recherche hat leider nicht geklappt")

    def start_background(self, task: "asyncio.Task", text: str, unpack: bool = False) -> None:
        async def _deliver() -> None:
            t0 = time.monotonic()
            try:
                result = await task
                speech = result[0] if unpack else result
            except Exception as e:  # noqa: BLE001
                _LOGGER.error("Hintergrund-Aufgabe fehlgeschlagen: %s", e)
                speech = self.anrede("Bei deiner Anfrage ist leider etwas schiefgegangen")
            _LOGGER.info("Hintergrund fertig nach %.1f s: %r", time.monotonic() - t0, speech)
            self.publish("gjarvis/last_answer", speech or "")
            self.last_answer = speech or ""
            self.last_answer = speech or ""
            if speech:
                prefix = self.o.get("async_result_prefix", "")
                await self.announce(f"{prefix} {speech}".strip())

        bg = asyncio.create_task(_deliver())
        prog = asyncio.create_task(self.progress_in_background(task))
        bg.add_done_callback(lambda _: prog.cancel())
        self.background.add(bg)
        bg.add_done_callback(self.background.discard)
        _LOGGER.info("Hintergrund-Aufgabe gestartet: %r (%d offen)", text, len(self.background))

    async def announce(self, speech: str, chime: bool = False) -> None:
        """Hintergrund-Ergebnis, Erinnerung oder Ansage sprechen, sobald Jarvis frei ist.
        Wird er dabei mit 'Hey Jarvis' unterbrochen, hört er sofort zu."""
        while self.busy:
            await asyncio.sleep(0.3)
        self.busy = True
        try:
            self.set_state("responding")
            await self.speak(speech, chime=chime)
            if self.interrupted:
                self.wake_pending = True
        finally:
            self.busy = False
            self.flush()
            if self.oww:
                self.oww.reset()
            self.last_wake = time.monotonic()
            self.set_state("idle")

    # ----------------------------- Sitzung --------------------------------- #
    async def session(self) -> None:
        self.busy = True
        pro = self.pro
        follow = float(self.o.get("follow_up_seconds", 6)) if (self.o.get("follow_up", True) and pro) else 0.0
        try:
            self.set_state("listening")
            one_breath, heard = await self.speech_continues(float(self.o.get("one_breath_seconds", 0.6)))
            if one_breath:
                # "Hey Jarvis, wie spät ist es" in einem Atemzug: kein "Ja, Moses?" dazwischen.
                # Das Weckwort wird erst kurz nach "Jarvis" erkannt – die ersten Wörter des Befehls stecken dann
                # schon im Puffer davor. Deshalb geht der Puffer mit an Whisper; "Hey Jarvis" wird danach entfernt.
                heard = list(self.wake_audio) + heard
                _LOGGER.info("Befehl direkt nach dem Weckwort – keine Rückfrage")
            else:
                heard = None
                await self.play_ack()
            timeout = None
            while True:
                audio = await self.record_command(timeout, heard)
                heard = None
                if audio is None:
                    # Kochmodus bleibt offen: später reicht "Hey Jarvis, weiter"
                    if not str(self.pending or "").startswith("app:schritte"):
                        self.pending = None
                    break
                self.set_state("processing")
                t = time.monotonic()
                one_breath = False
                try:
                    text = (await asyncio.wait_for(self.transcribe(audio), timeout=60)).strip()
                    text = re.sub(r"^\W*((hey|hi|hallo|ok|okay|he|ey)\W+)?\w{0,4}(vis|wis|ves|wiss|weis|fis)\b\W*", "", text, flags=re.I).strip() or text
                except asyncio.TimeoutError:
                    _LOGGER.error("Whisper hat nicht geantwortet – Abbruch")
                    self.satellite_error(1)
                    break
                _LOGGER.info("Erkannt (%.1f s): %r", time.monotonic() - t, text)
                if is_garbage(text):
                    _LOGGER.info("Kein sinnvoller Text – Ende")
                    break
                self.publish("gjarvis/last_command", text)
                self.last_command = text
                t = time.monotonic()
                # Sofort zeigen, dass er verstanden hat: "Moment, ich schaue nach" – läuft parallel zur Arbeit
                instant = self.start_ack(text)
                quick = None
                if pro:
                    try:
                        quick = await asyncio.wait_for(asyncio.to_thread(self.quick_answer, text), timeout=30)
                    except asyncio.TimeoutError:
                        _LOGGER.warning("Schnelle Antwort dauerte zu lange")
                if quick is not None:
                    speech, mode = quick
                    self.last_answer = speech
                    _LOGGER.info("Direkt (%.1f s): %r", time.monotonic() - t, speech)
                    await self.settle_ack(instant)
                    instant = None
                    if speech:
                        self.set_state("responding")
                        await self.speak(speech)
                    if mode == "ende" and not self.interrupted:
                        break
                    cont = mode == "frage"
                elif self.wants_research(text):
                    # Größere Aufgabe: im Hintergrund erledigen, Jarvis bleibt ansprechbar
                    task = asyncio.create_task(self.run_research(text))
                    said = await self.settle_ack(instant)
                    instant = None
                    if self.o.get("research_ack") and not said:
                        await self.speak(self.o["research_ack"])
                    self.start_background(task, text)
                    break
                else:
                    task = asyncio.create_task(asyncio.to_thread(self.answer, text))
                    wait_s = float(self.o.get("async_after_seconds", 4)) if pro else 120.0
                    done = await self.wait_with_progress(task, wait_s)
                    if not done and not pro:
                        _LOGGER.warning("Home Assistant antwortet nicht")
                        self.satellite_error(2)
                        break
                    if not done:
                        # Dauert länger -> "Moment, ich melde mich" und später nachliefern
                        _LOGGER.info("Antwort dauert länger – läuft im Hintergrund weiter")
                        said = await self.settle_ack(instant)
                        instant = None
                        if self.o.get("async_ack") and not said:
                            await self.speak(self.o["async_ack"])
                        self.start_background(task, text, unpack=True)
                        break
                    speech, cont = task.result()
                    self.last_answer = speech
                    self.publish("gjarvis/last_answer", speech or "")
                    _LOGGER.info("Antwort (%.1f s): %r", time.monotonic() - t, speech)
                    await self.settle_ack(instant)
                    instant = None
                    if speech:
                        self.set_state("responding")
                        await self.speak(speech)
                if self.interrupted:
                    # 'Hey Jarvis' während er spricht -> verstummen und sofort neu zuhören
                    self.interrupted = False
                    self.set_state("listening")
                    await self.play_ack()
                    timeout = None
                    continue
                if cont:
                    timeout = None  # Rückfrage: volle Zeit zum Antworten
                elif follow > 0:
                    timeout = follow  # Nachfragen ohne Weckwort (wie im Film)
                    _LOGGER.info("Höre noch %.0f s ohne Weckwort zu", follow)
                else:
                    break
                self.set_state("listening")
        except Exception as e:  # noqa: BLE001
            _LOGGER.exception("Fehler in der Sitzung: %s", e)
            self.satellite_error(9, str(e))
        finally:
            self.busy = False
            self.interrupted = False
            self.flush()
            if self.oww:
                self.oww.reset()
            self.last_wake = time.monotonic()
            self.set_state("idle")

    # ----------------------------- Kalibrierung ---------------------------- #
    async def record_while(self, coro, extra_s: float = 0.6) -> bytes:
        """Nimmt das Mikrofon auf, während coro läuft (z. B. eigene Sprachausgabe)."""
        self.flush()
        frames: List[bytes] = []
        stop = asyncio.Event()

        async def collect() -> None:
            while not stop.is_set():
                try:
                    frames.append(await asyncio.wait_for(self.queue.get(), timeout=0.2))
                except asyncio.TimeoutError:
                    pass

        col = asyncio.create_task(collect())
        try:
            await coro
            await asyncio.sleep(extra_s)
        finally:
            stop.set()
            await col
        return b"".join(frames)

    @staticmethod
    def dbfs(rms: float) -> float:
        return 20 * np.log10(max(rms, 1e-3) / 32768.0)

    async def calibrate(self) -> None:
        import difflib

        self.busy = True
        self.set_state("calibrating")
        res: dict = {}
        try:
            await self.speak("Kalibrierung startet. Bitte drei Sekunden ruhig sein.")
            # 1) Raumrauschen
            self.flush()
            noise = b""
            t0 = time.monotonic()
            while time.monotonic() - t0 < 3:
                noise += await self.queue.get()
            n = np.frombuffer(noise, dtype=np.int16).astype(np.float32)
            noise_rms = float(np.sqrt(np.mean(n * n)))
            self.noise_floor = max(noise_rms, 5.0)
            res["rauschen_dbfs"] = round(self.dbfs(noise_rms), 1)

            # 2) Eigene Stimme: Testsätze sprechen und selbst zuhören
            sentences = self.o.get("calibration_sentences") or ["Wie spät ist es?"]
            scores, levels, detect = [], [], []
            for sent in sentences:
                pcm, fmt = await self.synthesize(sent)
                rec = await self.record_while(self.play_pcm(pcm, *fmt))
                a = np.frombuffer(rec, dtype=np.int16).astype(np.float32)
                chunks = [a[i : i + VAD_CHUNK] for i in range(0, len(a) - VAD_CHUNK, VAD_CHUNK)]
                rms = sorted(float(np.sqrt(np.mean(c * c))) for c in chunks)
                voice = float(np.mean(rms[int(len(rms) * 0.7) :])) if rms else 0.0
                levels.append(voice)
                vad = self.make_vad()
                flags = [self.is_speech(vad, c.astype(np.int16).tobytes())[0] for c in chunks]
                detect.append(float(np.mean(flags)) if flags else 0.0)
                text = (await asyncio.wait_for(self.transcribe(rec), timeout=60)).strip()
                ratio = difflib.SequenceMatcher(
                    None, re.sub(r"\W", "", sent.lower()), re.sub(r"\W", "", text.lower())
                ).ratio()
                scores.append(ratio)
                _LOGGER.info("Kalibrierung: %r -> gehört %r (%.0f %%)", sent, text, ratio * 100)
            voice_rms = float(np.mean(levels)) if levels else 0.0
            res["stimme_dbfs"] = round(self.dbfs(voice_rms), 1)
            res["rauschabstand_db"] = round(res["stimme_dbfs"] - res["rauschen_dbfs"], 1)
            res["sprache_erkannt_prozent"] = round(100 * float(np.mean(detect)) if detect else 0, 0)
            res["whisper_genauigkeit_prozent"] = round(100 * float(np.mean(scores)) if scores else 0, 0)

            # 3) Weckwort mit eigener Stimme
            wake_voice = self.o.get("calibration_wake_voice") or self.o.get("tts_voice")
            saved = self.o.get("tts_voice")
            try:
                self.o["tts_voice"] = wake_voice
                pcm, fmt = await self.synthesize("Hey Jarvis!")
            finally:
                self.o["tts_voice"] = saved
            rec = await self.record_while(self.play_pcm(pcm, *fmt))
            self.oww.reset()
            a = np.frombuffer(rec, dtype=np.int16)
            best = 0.0
            for i in range(0, len(a) - OWW_FRAME, OWW_FRAME):
                sc = self.oww.predict(a[i : i + OWW_FRAME])
                best = max(best, max(sc.values()) if sc else 0.0)
            self.oww.reset()
            res["weckwort_wert"] = round(float(best), 2)

            # 4) Empfehlungen
            tips = []
            if res["stimme_dbfs"] < -38:
                gain = min(10.0, round(10 ** ((-30 - res["stimme_dbfs"]) / 20) * float(self.o.get("mic_gain", 1.0)), 1))
                tips.append(f"Mikrofon-Verstärkung auf {gain} erhöhen")
            if res["rauschabstand_db"] < 12:
                tips.append("Raum ist laut oder Mikrofon zu weit weg")
            if res["whisper_genauigkeit_prozent"] < 70:
                tips.append("Whisper versteht schlecht – lauter oder näher sprechen")
            if best < float(self.o["wake_threshold"]):
                tips.append(f"Weckwort-Schwelle eventuell auf {max(0.2, float(best) * 0.8):.2f} senken")
            res["empfehlungen"] = tips
            res["zeit"] = time.strftime("%d.%m.%Y %H:%M")
            res["zusammenfassung"] = (
                f"Rauschabstand {res['rauschabstand_db']:.0f} dB, Whisper {res['whisper_genauigkeit_prozent']:.0f} %, "
                f"Weckwort {res['weckwort_wert']:.2f}"
            )
            _LOGGER.info("Kalibrierung fertig: %s", json.dumps(res, ensure_ascii=False, default=float))
            self.publish("gjarvis/calibration", json.dumps(res, ensure_ascii=False, default=float), retain=True)
            self.calibration = json.loads(json.dumps(res, default=float))
            self.calibration = json.loads(json.dumps(res, default=float))
            spoken = (
                f"Kalibrierung fertig. Rauschabstand {res['rauschabstand_db']:.0f} Dezibel, "
                f"Whisper hat {res['whisper_genauigkeit_prozent']:.0f} Prozent verstanden, "
                f"Weckwort-Wert {str(res['weckwort_wert']).replace('.', ' Komma ')}."
            )
            if tips:
                spoken += " Empfehlung: " + ". ".join(tips) + "."
            await self.speak(spoken)
        except Exception as e:  # noqa: BLE001
            _LOGGER.exception("Kalibrierung fehlgeschlagen: %s", e)
            await self.speak(self.anrede("Die Kalibrierung ist leider fehlgeschlagen"))
        finally:
            self.busy = False
            self.flush()
            self.oww.reset()
            self.last_wake = time.monotonic()
            self.set_state("idle")

    # ----------------------------- Oberfläche ------------------------------ #
    def status(self) -> dict:
        return {
            "state": self.state,
            "busy": self.busy,
            "hoert": self.flags.get("hoert", False),
            "spricht": self.flags.get("spricht", False),
            "level_db": round(self.level_db, 1),
            "noise_db": round(self.dbfs(self.noise_floor), 1),
            "wake_score": round(float(self.last_score), 2),
            "wake_threshold": float(self.o.get("wake_threshold", 0.5)),
            "wake_gain": round(float(getattr(self, "wake_gain", 1.0)), 1),
            "last_wake": self.last_wake_time,
            "last_command": self.last_command,
            "last_answer": self.last_answer,
            "background": len(self.background),
            "volume": self.volume,
            "voice": self.o.get("tts_voice", ""),
            "name": self.o.get("assistant_name", "Jarvis"),
            "user": self.o.get("user_name", ""),
            "mqtt": self.mqtt_ok(),
            "vad": "Silero" if self.silero_path else "webrtcvad",
            "calibration": self.calibration,
            "uptime_s": round(time.time() - self.started),
            "reminders": [
                {"zeit": time.strftime("%d.%m. %H:%M", time.localtime(r["due"])), "text": r.get("text") or r["kind"],
                 "art": r["kind"], "id": r["id"]}
                for r in sorted(self.reminders, key=lambda x: x["due"])
            ],
            "memory": len(self.memory_items()),
            "quiet": self.in_quiet_hours(),
            "pro": self.pro_state(),
            "last_peak_db": round(getattr(self, "last_peak_db", 0.0), 1) if hasattr(self, "last_peak_db") else None,
            **self.satellite_status(),
        }

    # ----------------------------- Whisper einrichten ----------------------- #
    SUP_URL = os.environ.get("GJARVIS_SUPERVISOR_URL", "http://supervisor")

    def sup(self, method: str, path: str, **kw):
        r = requests.request(method, f"{self.SUP_URL}{path}", headers={"Authorization": f"Bearer {HA_TOKEN}"},
                             timeout=20, **kw)
        r.raise_for_status()
        return r.json().get("data", {})

    def whisper_slug(self) -> str:
        addons = self.sup("GET", "/addons").get("addons", [])
        cands = [a for a in addons if "whisper" in a.get("slug", "").lower()]
        if not cands:
            raise RuntimeError("Whisper ist nicht installiert (Einstellungen → Apps → Whisper)")
        cands.sort(key=lambda a: (a.get("state") != "started", a.get("slug") != "core_whisper"))
        return cands[0]["slug"]

    def whisper_prompt(self) -> str:
        n = self.o.get("assistant_name") or "Jarvis"
        u = self.o.get("user_name") or ""
        city = self.o.get("home_city") or ""
        return (f"Hey {n}. Wie spät ist es? Wie wird das Wetter morgen? Schalte das Licht im Wohnzimmer ein. "
                f"Setze Milch auf die Einkaufsliste. Stell einen Timer auf fünf Minuten. Erinnere mich morgen an den "
                f"Termin. Was läuft heute im Kino{' in ' + city if city else ''}? Guten Morgen{', ' + u if u else ''}.")

    def whisper_check(self) -> dict:
        """Whisper-Einstellungen lesen und Empfehlungen für GJarvis geben."""
        slug = self.whisper_slug()
        info = self.sup("GET", f"/addons/{slug}/info")
        opt = info.get("options", {}) or {}
        tipps = []
        model = str(opt.get("model", ""))
        if model in ("", "auto", "tiny", "tiny-int8"):
            tipps.append("Modell 'base-int8' oder (schneller Rechner) 'small-int8' versteht Deutsch deutlich besser")
        if "initial_prompt" in opt or "initial_prompt" in str(info.get("schema", "")):
            if not str(opt.get("initial_prompt") or "").strip():
                tipps.append("Beispielsätze (Initial prompt) fehlen – sie verbessern die Erkennung von Befehlen")
        if str(opt.get("language", "")) not in (self.o.get("language", "de"), ""):
            tipps.append(f"Sprache steht auf '{opt.get('language')}', GJarvis nutzt '{self.o.get('language', 'de')}'")
        if opt.get("beam_size") not in (1, "1", None):
            tipps.append("Beam size 1 ist am schnellsten")
        if opt.get("debug_logging"):
            tipps.append("Debug logging ausschalten")
        return {"slug": slug, "state": info.get("state"), "version": info.get("version"), "model": model,
                "language": opt.get("language"), "beam_size": opt.get("beam_size"),
                "prompt": bool(str(opt.get("initial_prompt") or "").strip()), "tipps": tipps}

    def whisper_setup(self) -> str:
        """Whisper für GJarvis einstellen: Sprache, Beam 1, Beispielsätze, Debug aus – dann neu starten.
        Das Modell wird nur geändert, wenn 'auto'/'tiny' eingestellt ist (dann base-int8)."""
        slug = self.whisper_slug()
        info = self.sup("GET", f"/addons/{slug}/info")
        opt = dict(info.get("options", {}) or {})
        keys = set(opt) | set(re.findall(r"'name': '([a-z_]+)'", str(info.get("schema", ""))))
        new = dict(opt)
        if "language" in keys:
            new["language"] = self.o.get("language", "de")
        if "beam_size" in keys:
            new["beam_size"] = 1
        if "initial_prompt" in keys:
            new["initial_prompt"] = self.whisper_prompt()
        if "debug_logging" in keys:
            new["debug_logging"] = False
        if "model" in keys and str(opt.get("model", "auto")) in ("auto", "tiny", "tiny-int8"):
            new["model"] = "base-int8"
            if opt.get("local_files_only"):
                new["local_files_only"] = False  # neues Modell muss erst heruntergeladen werden
        changed = [k for k in new if new.get(k) != opt.get(k)]
        if not changed:
            return "Whisper ist schon passend eingestellt."
        try:
            self.sup("POST", f"/addons/{slug}/options", json={"options": new})
            self.sup("POST", f"/addons/{slug}/restart")
        except requests.HTTPError as e:
            if e.response is None or e.response.status_code not in (401, 403):
                raise
            # GJarvis darf andere Apps nicht mehr selbst umstellen (hassio_role: default) – Werte zum Abtippen nennen
            hint = ", ".join(f"{k} = {new[k]!r}" for k in changed if k != "initial_prompt")
            if "initial_prompt" in changed:
                _LOGGER.info("Whisper-Beispielsätze (initial_prompt) zum Kopieren: %s", new.get("initial_prompt", ""))
                hint += (", " if hint else "") + "initial_prompt = Beispielsätze aus dem Protokoll"
            raise RuntimeError(f"Bitte von Hand setzen (Einstellungen → Apps → {slug} → Konfiguration): {hint}") from None
        _LOGGER.info("Whisper eingerichtet (%s): %s", slug, ", ".join(changed))
        return "Whisper eingerichtet (" + ", ".join(changed) + ") und neu gestartet. Beim ersten Mal kann es ein paar Minuten dauern."

    def mqtt_ok(self) -> bool:
        try:
            return bool(self.mqtt and self.mqtt.is_connected())
        except Exception:  # noqa: BLE001
            return False

    def apply_settings(self, changes: dict) -> bool:
        """Änderungen sofort übernehmen (gespeichert wird vorher über persist_options)."""
        if not changes:
            return False
        old_model = self.o.get("research_llm_model")
        self.raw.update(changes)
        if {"volume", "tts_voice"} & set(changes):
            self._save_keys = set(getattr(self, "_save_keys", set())) - set(changes)
        keep = {k: self.o[k] for k in ("weather_entity",) if k in self.o and k not in changes and not self.raw.get(k)}
        self.o.clear()
        self.o.update(fill_options(self.raw))
        self.o.update(keep)
        if {"ack_phrases", "instant_ack_phrases", "weather_ack_phrases", "progress_phrases", "tts_voice", "assistant_name", "user_name"} & set(changes):
            self.ack_cache.clear()
        if "research_llm_model" in changes and old_model and old_model != changes["research_llm_model"]:
            # altes Modell aus dem Speicher werfen, neues sofort laden
            import threading

            threading.Thread(target=self.llm_unload, args=(old_model,), daemon=True).start()
            self.llm_next_warm = 0
        if "volume" in changes:
            self.volume = int(changes["volume"])
            self.publish("gjarvis/volume", str(self.volume), retain=True)
        if "tts_voice" in changes:
            self.publish("gjarvis/voice", self.o.get("tts_voice", ""), retain=True)
        _LOGGER.info("Einstellungen geändert: %s", ", ".join(changes))
        from web import RESTART_KEYS

        return bool(RESTART_KEYS & set(changes))

    def route_text(self, text: str) -> Tuple[str, bool]:
        """Getippte Frage genauso verarbeiten wie eine gesprochene (ohne Hintergrund-Ansage)."""
        self.publish("gjarvis/last_command", text)
        quick = self.quick_answer(text) if self.pro else None
        if quick is not None:
            return quick[0] or "(beendet)", quick[1] == "frage"
        if self.wants_research(text):
            return self.research(text), False
        return self.answer(text)

    async def test_connection(self, what: str) -> str:
        import datetime as dt

        if what == "ha":
            r = requests.get(f"{HA_URL}/", headers={"Authorization": f"Bearer {HA_TOKEN}"}, timeout=10)
            r.raise_for_status()
            return r.json().get("message", "OK")
        if what == "whisper":
            text = await asyncio.wait_for(self.transcribe(b"\0" * RATE * WIDTH), timeout=60)
            return f"Whisper antwortet (Stille ergab: {text!r})"
        if what == "piper":
            pcm, fmt = await self.synthesize("Test")
            return f"Piper antwortet ({len(pcm) // 1024} kB Audio, {fmt[0]} Hz, Stimme {self.o.get('tts_voice')})"
        if what == "llm":
            ans = await asyncio.to_thread(
                self.ask_llm, [{"role": "user", "content": "Antworte nur mit dem Wort: bereit"}]
            )
            return f"{self.o.get('research_llm_model')}: {self.clean_for_speech(ans)[:80]}"
        if what == "agent":
            r = requests.get(f"{HA_URL}/states/{self.o.get('agent_id')}", headers={"Authorization": f"Bearer {HA_TOKEN}"}, timeout=10)
            r.raise_for_status()
            return f"{self.o.get('agent_id')} vorhanden"
        if what == "mqtt":
            if self.mqtt and self.mqtt.is_connected():
                return f"verbunden mit {os.environ.get('MQTT_HOST')}"
            raise RuntimeError("nicht verbunden")
        if what == "wikipedia":
            res = await asyncio.to_thread(self.search_wikipedia, "Home Assistant", 1)
            return f"{len(res)} Treffer"
        if what == "searxng":
            if not self.o.get("searxng_url"):
                raise RuntimeError("keine URL eingetragen")
            res = await asyncio.to_thread(self.search_web, "Wetter", 3)
            return f"{len(res)} Treffer"
        if what in ("openmeteo", "windy"):
            if what == "windy" and not (self.o.get("windy_api_key") or "").strip():
                raise RuntimeError("kein Windy-Schlüssel eingetragen")
            lat, lon = await asyncio.to_thread(self.flight_position)
            w = await asyncio.to_thread(self.wind_day, dt.date.today(), lat, lon)
            if not w:
                raise RuntimeError("keine Daten für heute")
            return f"{w['quelle']}: Wind {round(w['wind'] or 0)} km/h, Böen {round(w['boeen'] or 0)} ({lat:.2f}, {lon:.2f})"
        if what == "paraglidable":
            if not (self.o.get("paraglidable_api_key") or "").strip():
                raise RuntimeError("kein Paraglidable-Schlüssel eingetragen")
            res = await asyncio.to_thread(self.paraglidable_day, dt.date.today() + dt.timedelta(days=1))
            return f"{len(res)} Startplätze für morgen" + (f", z. B. {res[0]['name']} {round(res[0]['fly'] * 100)} %" if res else "")
        if what == "weather":
            return await asyncio.to_thread(self.weather_answer, "Wie ist das Wetter heute?")
        raise RuntimeError(f"unbekannter Test: {what}")

    # ----------------------------- Hauptschleife --------------------------- #
    async def run(self) -> None:
        try:
            await asyncio.to_thread(self.migrate_legacy_settings)
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("Übernahme alter Einstellungen fehlgeschlagen: %s", e)
        self.setup_wakeword()
        self.setup_mqtt()
        try:
            from web import start_web

            await start_web(self)
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("Oberfläche nicht gestartet: %s", e)
        self._tasks = getattr(self, "_tasks", set())
        if self.use_satellite:
            _LOGGER.info("Audio-Quelle: Satellit %s", self.o.get("satellite_host"))
            self._tasks.add(asyncio.create_task(self.satellite_reader()))
        else:
            self._tasks.add(asyncio.create_task(self.mic_reader()))
        if self.remote_player:
            _LOGGER.info("Ausgabe über %s (%s)", self.remote_player, self.remote_tts or "Piper-Stimme")
        asyncio.create_task(self.reminder_loop())
        asyncio.create_task(self.llm_warm_loop())
        self.loop = asyncio.get_running_loop()
        await self.preload_acks()
        self.flush()
        self.set_state("idle")
        if os.environ.get("GJARVIS_CALIBRATE_ON_START"):
            self.calibrate_requested = True
        hb_t, hb_peak, hb_score, hb_frames = time.monotonic(), 0.0, 0.0, 0
        while True:
            if self.calibrate_requested and not self.busy:
                self.calibrate_requested = False
                await self.calibrate()
                continue
            if self.wake_pending and not self.busy:
                self.wake_pending = False
                self.interrupted = False
                _LOGGER.info("Nach Unterbrechung: höre zu")
                self.clear_satellite_error()
                await self.session()
                continue
            try:
                frame = await asyncio.wait_for(self.queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            self.update_noise_floor(frame)
            self.recent.append(frame)
            thr = float(self.o["wake_threshold"])
            refr = float(self.o["wake_refractory_seconds"])
            dbg = bool(self.o.get("debug"))
            wake_in = np.frombuffer(frame, dtype=np.int16)
            if self.o.get("wake_auto_gain", False):
                # Leise Mikrofone: Pegel nur für die Weckwort-Erkennung anheben (Raumrauschen -> ca. -50 dBFS)
                g = 10 ** ((float(self.o.get("wake_target_noise_db", -50)) - self.dbfs(self.noise_floor)) / 20)
                g = min(max(g, 1.0), float(self.o.get("wake_max_gain", 8)))
                self.wake_gain = 0.98 * getattr(self, "wake_gain", g) + 0.02 * g
                if self.wake_gain > 1.05:
                    wake_in = np.clip(wake_in.astype(np.float32) * self.wake_gain, -32768, 32767).astype(np.int16)
            scores = self.oww.predict(wake_in)
            score = float(max(scores.values())) if scores else 0.0
            self.last_score = 0.8 * self.last_score + 0.2 * score if score < self.last_score else score
            # Lebenszeichen: einmal pro Minute Pegel + bester Weckwort-Wert ins Protokoll
            fa = np.frombuffer(frame, dtype=np.int16).astype(np.float32)
            self.level_db = self.dbfs(float(np.sqrt(np.mean(fa * fa))) if len(fa) else 0.0)
            hb_peak = max(hb_peak, float(np.abs(fa).max()) if len(fa) else 0.0)
            hb_score = max(hb_score, score)
            hb_frames += 1
            if time.monotonic() - hb_t >= 60:
                _LOGGER.info(
                    "Mikrofon aktiv: %d Blöcke/min, lautester Moment %.0f dBFS, Grundrauschen %.0f dBFS, "
                    "bester Weckwort-Wert %.2f (Verstärkung x%.1f)",
                    hb_frames,
                    self.dbfs(hb_peak),
                    self.dbfs(self.noise_floor),
                    hb_score,
                    getattr(self, "wake_gain", 1.0),
                )
                hb_t, hb_peak, hb_score, hb_frames = time.monotonic(), 0.0, 0.0, 0
            if dbg and score > 0.1:
                _LOGGER.debug("Weckwort-Score %.2f", score)
            thr = float(self.o["wake_threshold"])
            refr = float(self.o["wake_refractory_seconds"])
            if score >= thr and not self.busy and time.monotonic() - self.last_wake >= refr:
                _LOGGER.info("Weckwort erkannt (Score %.2f)", score)
                self.clear_satellite_error()
                self.last_wake_time = time.strftime("%H:%M:%S")
                self.wake_audio = list(self.recent)
                await self.session()


def main() -> None:
    raw = load_raw_options()
    opts = fill_options(raw)
    logging.basicConfig(
        level=logging.DEBUG if opts.get("debug") else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    try:
        from web import RING, RedactFilter

        for h in logging.getLogger().handlers:              # auch die Konsole (App-Protokoll in Home Assistant) schwärzt Schlüssel
            h.addFilter(RedactFilter())
        logging.getLogger().addHandler(RING)
    except Exception:  # noqa: BLE001
        pass
    asyncio.run(GJarvis(opts, raw).run())


if __name__ == "__main__":
    main()
