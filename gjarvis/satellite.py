"""Satelliten und externe Lautsprecher für GJarvis.

Eingang:  Statt des Server-Mikrofons hört GJarvis über ein ESPHome-Gerät (z. B. M5Stack Atom Echo).
          GJarvis verbindet sich dafür selbst per ESPHome-API mit dem Gerät und bekommt dessen
          Mikrofon dauerhaft gestreamt. Weckwort, Whisper, Antworten – alles macht weiter GJarvis.
Ausgang:  Statt über den Server-Lautsprecher spricht GJarvis über einen media_player aus Home
          Assistant (z. B. Sonos) – entweder mit seiner Piper-Stimme oder mit einer TTS-Entität
          aus Home Assistant (z. B. ElevenLabs).
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
import wave
from collections import deque
from pathlib import Path
from typing import Optional

import numpy as np
import requests

_LOGGER = logging.getLogger("gjarvis")

HA_URL = ""
HA_TOKEN = ""
MEDIA_DIR = Path("/media/gjarvis")
MEDIA_ID = "media-source://media_source/local/gjarvis/"
KEEP_FILES = 20

# Auswahl am Atom-Echo-Firmware-Paket: Weckwort nicht auf dem Gerät, sondern beim Server erkennen,
# dann streamt das Gerät sein Mikrofon dauerhaft.
WAKE_LOCATION_NAMES = ("wake word engine location", "aktivierungswort-engine", "wake word engine")
WAKE_LOCATION_REMOTE = "In Home Assistant"


class RemoteOutputError(RuntimeError):
    """Ausgabe über den externen Lautsprecher fehlgeschlagen (Fehlercode 3 wurde schon gemeldet)."""


class AudioSource:
    """Ein Mikrofon für GJarvis: das Mikrofon am Server oder ein ESPHome-Satellit."""

    def __init__(self, gj, kind: str, cfg: Optional[dict] = None) -> None:
        cfg = cfg or {}
        self.gj = gj
        self.kind = kind  # "local" | "satellite"
        self.name = str(cfg.get("name") or "").strip()
        self.host = str(cfg.get("host") or "").strip()
        try:
            self.port = int(cfg.get("port") or 6053)
        except (TypeError, ValueError):
            self.port = 6053
        self.key = str(cfg.get("key") or "").strip()
        self.room = str(cfg.get("room") or "").strip()
        g = cfg.get("gain")
        try:
            self.gain = float(g) if g not in (None, "") else None
        except (TypeError, ValueError):
            self.gain = None
        self.media_player = str(cfg.get("media_player") or "").strip()
        self.led = bool(cfg.get("led", True))
        self.client = None
        self.connected = False
        self.streaming = False
        self.blocked = False
        self.taken = False
        self.light = None
        self.effects: list = []
        self.names: set = set()
        self.mac = ""
        self.last_audio = 0.0
        self.led_ts = 0.0
        self.oww = None
        self.recent: deque = deque(maxlen=20)  # letzte ~1,6 s – gehen beim Umschalten mit ins Gespräch
        self.last_score = 0.0
        self.last_wake = 0.0

    @property
    def label(self) -> str:
        if self.kind == "local":
            return "Server-Mikrofon"
        return self.name or self.room or self.host or "Satellit"

    def watch(self, frame: bytes) -> None:
        """Nicht aktives Mikrofon: eigene Weckwort-Erkennung. Hört es 'Hey Jarvis', übernimmt es das Gespräch."""
        self.recent.append(frame)
        gj = self.gj
        if gj.busy or not getattr(gj, "oww", None):
            return
        if self.oww is None:
            self.oww = gj.make_wake_model()
            if self.oww is None:
                return
        sc = self.oww.predict(np.frombuffer(frame, dtype=np.int16))
        self.last_score = float(max(sc.values())) if sc else 0.0
        thr = float(gj.o.get("wake_threshold", 0.5))
        refr = float(gj.o.get("wake_refractory_seconds", 2))
        if self.last_score >= thr and time.monotonic() - self.last_wake >= refr:
            self.last_wake = time.monotonic()
            gj.switch_source(self, self.last_score)

    def status(self) -> dict:
        sat = self.kind == "satellite"
        return {
            "kind": self.kind,
            "name": self.label,
            "host": self.host,
            "room": self.room,
            "connected": bool(self.connected) if sat else True,
            "streaming": bool(self.streaming) if sat else True,
            "blocked": bool(self.blocked),
            "taken": bool(self.taken),
            "active": self is getattr(self.gj, "active_src", None),
            "media_player": self.media_player,
            "led": bool(sat and self.led and self.light is not None),
        }


class SatelliteFeatures:
    """Mixin für GJarvis: ESPHome-Satellit als Mikrofon, Home-Assistant-Lautsprecher als Ausgabe."""

    # --------------------------------------------------------------------- #
    # Gemeinsame Helfer
    # --------------------------------------------------------------------- #
    def feed_frame(self, frame: bytes, src: "Optional[AudioSource]" = None) -> None:
        """Einen Mikrofon-Block (80 ms, 16 kHz, 16 Bit, mono) in die Verarbeitung geben – vom Server-Mikrofon
        oder von einem Satelliten. Bei mehreren Mikrofonen geht nur das aktive in die Verarbeitung; die anderen
        warten mit eigener Weckwort-Erkennung auf „Hey Jarvis“."""
        gain = src.gain if (src is not None and src.gain) else float(self.o.get("mic_gain", 1.0))
        if abs(gain - 1.0) >= 1e-3:
            a = np.frombuffer(frame, dtype=np.int16).astype(np.float32) * gain
            frame = np.clip(a, -32768, 32767).astype(np.int16).tobytes()
        if src is not None and len(getattr(self, "sources", ())) > 1 and src is not getattr(self, "active_src", None):
            src.watch(frame)
            return
        if self.discard:
            if self.barge_q is not None and not self.barge_q.full():
                self.barge_q.put_nowait(frame)
            sq = getattr(self, "stop_q", None)
            if sq is not None and not sq.full():
                sq.put_nowait(frame)
            return
        if self.queue.full():
            self.queue.get_nowait()
        self.queue.put_nowait(frame)

    def ha_service(self, domain: str, service: str, data: dict) -> None:
        r = requests.post(
            f"{HA_URL}/services/{domain}/{service}",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json=data,
            timeout=20,
        )
        r.raise_for_status()

    def sat_configs(self) -> list:
        """Alle eingetragenen Satelliten (Liste „satellites“ plus der alte Einzel-Eintrag satellite_host)."""
        out = [c for c in (self.o.get("satellites") or []) if isinstance(c, dict) and str(c.get("host") or "").strip()]
        host = str(self.o.get("satellite_host") or "").strip()
        if host and not any(str(c.get("host")).strip() == host for c in out):
            out.insert(0, {"host": host, "port": self.o.get("satellite_port", 6053),
                           "key": self.o.get("satellite_key", ""), "led": self.o.get("satellite_led", True)})
        return out

    @property
    def use_satellite(self) -> bool:
        return self.o.get("audio_source") in ("satellite", "both") and bool(self.sat_configs())

    @property
    def use_local(self) -> bool:
        return self.o.get("audio_source") in ("local", "both") or not self.use_satellite

    @property
    def sat_sources(self) -> list:
        return [s for s in getattr(self, "sources", []) if s.kind == "satellite"]

    def setup_sources(self) -> None:
        """Mikrofone anlegen: Satelliten und/oder Server-Mikrofon (Audio-Quelle „both“ = beides gleichzeitig)."""
        self.sources = [AudioSource(self, "satellite", c) for c in self.sat_configs()] if self.use_satellite else []
        self.local_src = AudioSource(self, "local") if self.use_local else None
        if self.local_src is not None:
            self.sources.append(self.local_src)
        self.active_src = self.sources[0] if self.sources else None
        names = ", ".join(s.label + (f" ({s.host})" if s.host else "") for s in self.sources)
        _LOGGER.info("Mikrofone: %s", names or "keins")

    def switch_source(self, src: "AudioSource", score: float = 0.0) -> None:
        """Ein anderes Mikrofon hat „Hey Jarvis“ gehört: dort zuhören und das Gespräch starten."""
        if self.busy or src is getattr(self, "active_src", None):
            return
        _LOGGER.info("Weckwort erkannt am %s (Score %.2f)", src.label, score)
        self.active_src = src
        self.flush()
        self.wake_audio = list(src.recent)
        src.recent.clear()
        if src.oww:
            src.oww.reset()
        if getattr(self, "oww", None):
            self.oww.reset()
        self.wake_switch = True
        self._led_for_state(getattr(self, "_sat_last", "idle"))

    def migrate_satellite(self) -> None:
        """Alter Einzel-Satellit -> erster Eintrag der Satellitenliste (einmalig, der Schlüssel bleibt erhalten)."""
        e = {"host": str(self.o.get("satellite_host")).strip(), "led": bool(self.o.get("satellite_led", True))}
        try:
            e["port"] = int(self.o.get("satellite_port") or 6053)
        except (TypeError, ValueError):
            e["port"] = 6053
        if (self.o.get("satellite_key") or "").strip():
            e["key"] = self.o["satellite_key"].strip()
        changes = {"satellites": [e], "satellite_host": "", "satellite_key": ""}
        ok, err = self.persist_options(changes)
        if ok:
            self.o.update(changes)
            self.raw.update(changes)
            _LOGGER.info("Satellit %s in die Satellitenliste übernommen", e["host"])
        else:
            _LOGGER.warning("Satellit nicht in die Liste übernommen: %s", err)

    def clean_satellites(self, value) -> list:
        """Satellitenliste aus der Oberfläche prüfen; „••••••“ heißt: gespeicherten Schlüssel behalten."""
        old = {str(s.get("host") or "").strip(): s for s in (self.raw.get("satellites") or []) if isinstance(s, dict)}
        out = []
        for s in value if isinstance(value, list) else []:
            if not isinstance(s, dict):
                continue
            host = str(s.get("host") or "").strip()
            if not host:
                continue
            e = {"host": host}
            for k in ("name", "room", "media_player"):
                if str(s.get(k) or "").strip():
                    e[k] = str(s[k]).strip()
            try:
                e["port"] = int(float(s.get("port") or 6053))
            except (TypeError, ValueError):
                e["port"] = 6053
            key = str(s.get("key") or "").strip()
            if key == "••••••":
                key = str((old.get(host) or {}).get("key") or "")
            if key:
                e["key"] = key
            if s.get("gain") not in (None, ""):
                try:
                    e["gain"] = min(10.0, max(0.1, float(str(s["gain"]).replace(",", "."))))
                except (TypeError, ValueError):
                    pass
            e["led"] = bool(s.get("led", True))
            out.append(e)
        return out

    @property
    def remote_player(self) -> str:
        """Lautsprecher: der des aktiven Satelliten, sonst der allgemeine (leer = Server)."""
        src = getattr(self, "active_src", None)
        mp = (getattr(src, "media_player", "") or "").strip() if src is not None else ""
        return mp or (self.o.get("output_media_player") or "").strip()

    @property
    def remote_tts(self) -> str:
        """TTS-Entität aus Home Assistant (z. B. tts.elevenlabs_…). Ist sie gesetzt, spricht GJarvis überall mit
        dieser Stimme – über den externen Lautsprecher oder, ohne ihn, über den Lautsprecher am Server."""
        return (self.o.get("output_tts_entity") or "").strip()

    @property
    def remote_tts_voice(self) -> str:
        """Feste Stimme der TTS-Entität (z. B. ElevenLabs-Voice-ID); leer = Standardstimme der Entität."""
        return (self.o.get("output_tts_voice") or "").strip()

    # --------------------------------------------------------------------- #
    # Eingang: ESPHome-Satellit
    # --------------------------------------------------------------------- #
    async def satellite_reader(self, src: "AudioSource") -> None:
        """Verbindet sich mit einem Satelliten und hält die Verbindung (mit automatischem Neuaufbau)."""
        try:
            from aioesphomeapi import APIClient, LightInfo, SelectInfo  # noqa: PLC0415
        except ImportError:
            _LOGGER.error("aioesphomeapi fehlt – Satellit kann nicht verbunden werden")
            return

        host, port = src.host, src.port
        key = src.key or None
        frame_bytes = 1280 * 2  # OWW_FRAME * WIDTH
        retry = 5.0
        while True:
            stopped = asyncio.Event()
            buf = bytearray()
            client = APIClient(host, port, None, noise_psk=key, client_info="GJarvis")

            async def on_stop(expected: bool, _ev=stopped) -> None:
                _ev.set()

            async def handle_start(*_args, _buf=buf) -> int:
                nonlocal retry
                retry = 5.0  # erst echtes Audio setzt die Wartezeit zurück
                _buf.clear()
                src.last_audio = time.monotonic()
                _LOGGER.info("%s streamt sein Mikrofon", src.label)
                return 0  # 0 = Audio über die API-Verbindung (kein eigener UDP-Port)

            async def handle_stop(*_args) -> None:
                _LOGGER.debug("%s hat das Streaming beendet", src.label)

            async def handle_audio(data: bytes, *_args, _buf=buf) -> None:
                src.last_audio = time.monotonic()
                _buf.extend(data)
                while len(_buf) >= frame_bytes:
                    self.feed_frame(bytes(_buf[:frame_bytes]), src)
                    del _buf[:frame_bytes]

            try:
                await client.connect(on_stop=on_stop, login=True)
                info = await client.device_info()
                src.names = {info.name or "", info.friendly_name or ""}
                src.mac = (info.mac_address or "").lower()
                if not src.name:
                    src.name = info.friendly_name or info.name or ""
                entities, _ = await client.list_entities_services()
                _LOGGER.info("Satellit verbunden: %s (%s)", src.label, host)
                # Erst abonnieren, dann die Weckwort-Erkennung umstellen – das Umstellen startet den Stream.
                src.last_audio = 0.0
                client.subscribe_voice_assistant(
                    handle_start=handle_start, handle_stop=handle_stop, handle_audio=handle_audio
                )
                src.light, src.effects = None, []
                for e in entities:
                    if isinstance(e, LightInfo) and src.light is None:
                        src.light, src.effects = e.key, list(e.effects or [])
                    if isinstance(e, SelectInfo) and any(n in (e.name or "").lower() for n in WAKE_LOCATION_NAMES):
                        if WAKE_LOCATION_REMOTE in (e.options or []):
                            client.select_command(e.key, WAKE_LOCATION_REMOTE)
                            _LOGGER.info("%s: Weckwort-Erkennung auf GJarvis umgestellt", src.label)
                src.client = client
                src.connected = True
                src.streaming = False
                self._led_for_state(self._state_for(src), src)
                connected_at = time.monotonic()
                silent_s = float(self.o.get("satellite_watchdog_seconds", 15))
                while not stopped.is_set():
                    try:
                        await asyncio.wait_for(stopped.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        last = src.last_audio or connected_at
                        src.streaming = time.monotonic() - last < silent_s
                        if src.streaming:
                            src.blocked = False
                        else:
                            # Typisch: Home Assistant (ESPHome-Integration) hält den Sprach-Stream des Geräts.
                            _LOGGER.error(
                                "%s (%s) schickt kein Audio. Wahrscheinlich nutzt Home Assistant das Gerät als "
                                "Sprach-Satellit – in GJarvis „Übernehmen“ klicken. Verbinde neu …", src.label, host)
                            src.blocked = True
                            break
                        # Firmware setzt die LED manchmal selbst zurück – Farbe regelmäßig auffrischen
                        if (not getattr(self, "sat_error_code", 0) and not self.busy
                                and time.monotonic() - src.led_ts > 30):
                            self._led_for_state(self._state_for(src), src)
                if stopped.is_set():
                    _LOGGER.warning("Verbindung zu %s getrennt – verbinde neu", src.label)
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if "encryption" in msg.lower() or "noise" in msg.lower() or "psk" in msg.lower():
                    _LOGGER.error("Satellit %s: Verschlüsselungsschlüssel fehlt oder ist falsch (%s)", host, msg)
                else:
                    _LOGGER.warning("Satellit %s nicht erreichbar: %s", host, msg)
            finally:
                src.client = None
                src.connected = False
                src.streaming = False
                try:
                    await client.disconnect()
                except Exception:  # noqa: BLE001
                    pass
            await asyncio.sleep(retry)
            retry = min(retry * 2, 60.0)

    # --------------------------------------------------------------------- #
    # LED am Satelliten
    # --------------------------------------------------------------------- #
    # Farbe (r, g, b), Helligkeit, Effekt (Effekt in den Einstellungen änderbar: ruhig / pulsierend / schnell)
    LED_STATES = {
        "idle": ((0.0, 1.0, 0.0), 0.25, None),                 # grün gedimmt: alles ok, wartet auf "Hey Jarvis"
        "listening": ((0.0, 1.0, 0.0), 0.9, "Slow Pulse"),     # grün pulsierend: hört zu
        "processing": ((1.0, 0.7, 0.0), 0.9, "Fast Pulse"),    # gelb schnell pulsierend: denkt nach
        "responding": ((1.0, 0.7, 0.0), 0.9, "Slow Pulse"),    # gelb pulsierend: spricht
    }
    LED_EFFECT_NAMES = {"ruhig": None, "pulsierend": "Slow Pulse", "schnell": "Fast Pulse"}
    # Fehlercodes = Anzahl roter Blinker
    ERROR_CODES = {
        1: "Spracherkennung (Whisper) antwortet nicht",
        2: "Home Assistant / KI antwortet nicht",
        3: "Lautsprecher-Ausgabe fehlgeschlagen",
        4: "Sprachausgabe (TTS) fehlgeschlagen",
        9: "Unerwarteter Fehler – siehe Protokoll",
    }

    def led_style(self, state: str):
        rgb, bri, eff = self.LED_STATES.get(state, self.LED_STATES["idle"])
        opt = str(self.o.get(f"led_{state}_effect", "") or "").strip().lower()
        if opt in self.LED_EFFECT_NAMES:
            eff = self.LED_EFFECT_NAMES[opt]
        return rgb, bri, eff

    def _led(self, on: bool, rgb=None, brightness=None, effect=None, src=None) -> None:
        if not self.o.get("satellite_led", True):
            return
        targets = [src] if src is not None else self.sat_sources
        loop = getattr(self, "loop", None)
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        for s in targets:
            c, key = s.client, s.light
            if not (c and key is not None and s.led):
                continue
            kw = {"state": on}
            if on:
                kw.update(rgb=rgb, brightness=brightness)
                if s.effects:
                    kw["effect"] = effect if effect in s.effects else "None"

            def send(c=c, key=key, kw=kw, s=s) -> None:
                try:
                    c.light_command(key, **kw)
                    s.led_ts = time.monotonic()
                except Exception as e:  # noqa: BLE001
                    _LOGGER.debug("Satellit-LED: %s", e)

            if loop and running is not loop:
                loop.call_soon_threadsafe(send)  # aus einem Thread: über die Ereignisschleife senden
            else:
                send()

    def _state_for(self, src) -> str:
        """Nur das aktive Mikrofon zeigt den Gesprächszustand, die anderen Satelliten „bereit“."""
        st = getattr(self, "_sat_last", "idle")
        return st if src is getattr(self, "active_src", None) else "idle"

    def _led_for_state(self, state: str, src=None) -> None:
        act = getattr(self, "active_src", None)
        for s in ([src] if src is not None else self.sat_sources):
            st = state if (src is not None or s is act) else "idle"
            rgb, bri, eff = self.led_style(st)
            self._led(True, rgb, bri, eff, s)

    def satellite_state(self, state: str) -> None:
        """LED passend zum GJarvis-Zustand. Läuft ein Fehler-Blinken, hat es Vorrang (gelöscht wird es erst
        beim nächsten erkannten Weckwort – clear_satellite_error() – oder nach Ablauf der Anzeigezeit)."""
        self._sat_last = state
        if getattr(self, "sat_error_code", 0):
            return
        self._led_for_state(state)

    def satellite_error(self, code: int, detail: str = "") -> None:
        """Fehler am Satelliten anzeigen: rot blinken, Anzahl = Code (für 60 s oder bis zum nächsten 'Hey Jarvis')."""
        _LOGGER.warning("Fehlercode %d: %s%s", code, self.ERROR_CODES.get(code, "Fehler"),
                        f" ({detail})" if detail else "")
        if not any(s.client for s in self.sat_sources):
            return  # ohne Satellit nur protokollieren (sonst bliebe der Code nach dem Verbinden hängen)
        old = getattr(self, "_sat_blink", None)
        if getattr(self, "sat_error_code", 0) == code and old and not old.done():
            return  # derselbe Fehler blinkt schon
        self.sat_error_code = code
        if old and not old.done():
            old.cancel()
        try:
            self._sat_blink = asyncio.get_running_loop().create_task(self._blink_error(code))
        except RuntimeError:  # aus einem Thread heraus aufgerufen
            loop = getattr(self, "loop", None)
            if loop:
                loop.call_soon_threadsafe(
                    lambda: setattr(self, "_sat_blink", loop.create_task(self._blink_error(code))))

    def clear_satellite_error(self) -> None:
        self.sat_error_code = 0
        t = getattr(self, "_sat_blink", None)
        if t and not t.done():
            t.cancel()

    async def _blink_error(self, code: int) -> None:
        red = (1.0, 0.0, 0.0)
        until = time.monotonic() + float(self.o.get("satellite_error_seconds", 60))
        try:
            while time.monotonic() < until and getattr(self, "sat_error_code", 0) == code:
                for _ in range(code):  # Anzahl Blinker = Fehlercode
                    self._led(True, red, 1.0)
                    await asyncio.sleep(0.3)
                    self._led(False)
                    await asyncio.sleep(0.3)
                await asyncio.sleep(1.5)  # Pause, dann Code wiederholen
        finally:
            # Nur die Aufgabe, der der Fehler gehört, räumt auf (eine neuere hat ihn sonst übernommen)
            if getattr(self, "_sat_blink", None) is asyncio.current_task():
                if getattr(self, "sat_error_code", 0) == code:
                    self.sat_error_code = 0
                if not getattr(self, "sat_error_code", 0):
                    self._led_for_state(getattr(self, "_sat_last", "idle"))

    # --------------------------------------------------------------------- #
    # Ausgang: Lautsprecher aus Home Assistant (z. B. Sonos)
    # --------------------------------------------------------------------- #
    def _cleanup_media(self) -> None:
        files = sorted(MEDIA_DIR.glob("say_*.wav"), key=lambda p: p.stat().st_mtime)
        for p in files[:-KEEP_FILES]:
            try:
                p.unlink()
            except OSError:
                pass

    async def _wait_spoken(self, seconds: float) -> None:
        """Warten, bis der externe Lautsprecher fertig ist (Mikrofon bleibt so lange stumm).
        'Hey Jarvis' unterbricht auch hier (Pro, wie beim Lautsprecher am Server)."""
        end = time.monotonic() + seconds
        watch = bool(self.o.get("barge_in", True) and getattr(self, "oww", None)
                     and getattr(self, "barge_ok", True) and getattr(self, "pro", False))
        own_q = watch and self.barge_q is None
        if own_q:
            self.barge_q = asyncio.Queue(maxsize=200)
            self.oww.reset()
        thr = max(float(self.o.get("wake_threshold", 0.5)), float(self.o.get("barge_in_threshold", 0.7)))
        try:
            while time.monotonic() < end and not self.interrupted and not getattr(self, "remote_stop", False):
                if not watch or self.barge_q is None:
                    await asyncio.sleep(0.1)
                    continue
                try:
                    fr = await asyncio.wait_for(self.barge_q.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                sc = self.oww.predict(np.frombuffer(fr, dtype=np.int16))
                if sc and max(sc.values()) >= thr:
                    _LOGGER.info("Unterbrochen durch Weckwort (Score %.2f)", max(sc.values()))
                    self.interrupted = True
                    await asyncio.to_thread(self.stop_remote)
                    break
        finally:
            if own_q:
                self.barge_q = None

    async def play_remote_pcm(self, pcm: bytes, rate: int, width: int, channels: int) -> None:
        """PCM als WAV nach /media/gjarvis schreiben und auf dem media_player abspielen."""
        if getattr(self, "remote_stop", False):
            return
        name = f"say_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"

        def write() -> None:
            MEDIA_DIR.mkdir(parents=True, exist_ok=True)
            with wave.open(str(MEDIA_DIR / name), "wb") as w:
                w.setnchannels(channels)
                w.setsampwidth(width)
                w.setframerate(rate)
                w.writeframes(pcm)
            self._cleanup_media()

        await asyncio.to_thread(write)
        seconds = len(pcm) / max(1, rate * width * channels)
        await asyncio.to_thread(
            self.ha_service,
            "media_player",
            "play_media",
            {
                "entity_id": self.remote_player,
                "media_content_id": MEDIA_ID + name,
                "media_content_type": "music",
                "announce": True,
            },
        )
        await self._wait_spoken(seconds + float(self.o.get("output_latency_seconds", 1.5)))

    async def speak_remote_tts(self, text: str) -> None:
        """Text über eine TTS-Entität aus Home Assistant (z. B. ElevenLabs) sprechen – auf dem media_player
        oder, wenn keiner eingestellt ist, über den Lautsprecher am Server. Klappt das nicht, spricht Piper."""
        if getattr(self, "remote_stop", False):
            return
        if not self.remote_player:
            try:
                pcm, rate, width, channels = await asyncio.to_thread(self._ha_tts_wav, text)
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Stimme %s nicht verfügbar (%s) – spreche mit Piper", self.remote_tts, e)
                pcm, fmt = await self.synthesize(text)
                rate, width, channels = fmt
            await self.play_pcm(pcm, rate, width, channels)
            return
        data = {
            "entity_id": self.remote_tts,
            "media_player_entity_id": self.remote_player,
            "message": text,
            "cache": True,
        }
        if self.remote_tts_voice:
            data["options"] = {"voice": self.remote_tts_voice}
        await asyncio.to_thread(self.ha_service, "tts", "speak", data)
        # Dauer schätzen: ~14 Zeichen pro Sekunde + Erzeugung und Netzwerk
        seconds = len(text) / 14.0 + float(self.o.get("output_latency_seconds", 1.5)) + 1.0
        await self._wait_spoken(seconds)

    def _ha_tts_wav(self, text: str):
        """Sprachausgabe der TTS-Entität als WAV aus Home Assistant holen -> (pcm, rate, width, channels)."""
        import io  # noqa: PLC0415

        opts = {"preferred_format": "wav", "preferred_sample_channels": 1}
        if self.remote_tts_voice:
            opts["voice"] = self.remote_tts_voice
        hdr = {"Authorization": f"Bearer {HA_TOKEN}"}
        r = requests.post(
            f"{HA_URL}/tts_get_url",
            headers=hdr,
            json={"engine_id": self.remote_tts, "message": text, "cache": True, "options": opts},
            timeout=30,
        )
        r.raise_for_status()
        path = (r.json() or {}).get("path") or ""
        if not path.startswith("/"):
            raise RuntimeError("keine Audio-Adresse erhalten")
        base = HA_URL[: -len("/api")] if HA_URL.endswith("/api") else HA_URL
        a = requests.get(base + path, headers=hdr, timeout=60)
        a.raise_for_status()
        raw = a.content
        if raw[:4] != b"RIFF":
            raise RuntimeError("keine WAV-Daten")
        with wave.open(io.BytesIO(raw), "rb") as w:
            rate, width, channels = w.getframerate(), w.getsampwidth(), w.getnchannels()
        i = raw.find(b"data", 12)
        pcm = raw[i + 8:] if i >= 0 else b""
        if not pcm:
            raise RuntimeError("leere Sprachausgabe")
        return pcm, rate, width, channels

    def stop_remote(self) -> None:
        if not self.remote_player:
            return
        try:
            self.ha_service("media_player", "media_stop", {"entity_id": self.remote_player})
        except Exception as e:  # noqa: BLE001
            _LOGGER.debug("Stopp am Lautsprecher: %s", e)

    # --------------------------------------------------------------------- #
    # Satellit von Home Assistant übernehmen (ein Klick in der Übersicht)
    # --------------------------------------------------------------------- #
    async def _ha_ws(self, *msgs):
        """Kurze Sitzung mit der WebSocket-API von Home Assistant; gibt die Ergebnisse der Befehle zurück."""
        import aiohttp  # noqa: PLC0415

        url = HA_URL.replace("https://", "wss://").replace("http://", "ws://")
        url = (url[: -len("/api")] if url.endswith("/api") else url) + "/websocket"
        out = []
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url, timeout=15) as ws:
                await ws.receive_json(timeout=15)  # auth_required
                await ws.send_json({"type": "auth", "access_token": HA_TOKEN})
                if (await ws.receive_json(timeout=15)).get("type") != "auth_ok":
                    raise RuntimeError("Anmeldung an Home Assistant fehlgeschlagen")
                for i, m in enumerate(msgs, 1):
                    await ws.send_json({"id": i, **m})
                    while True:
                        r = await ws.receive_json(timeout=30)
                        if r.get("id") == i:
                            break
                    if not r.get("success"):
                        raise RuntimeError((r.get("error") or {}).get("message") or "Home Assistant lehnt ab")
                    out.append(r.get("result"))
        return out

    async def _sat_ha_entities(self, src: "AudioSource") -> list:
        """Assist-Satelliten-Entitäten in Home Assistant, die zu diesem Satelliten gehören."""
        names = {n.lower() for n in src.names if n}
        mac = (src.mac or "").lower()
        if not names and not mac:
            raise RuntimeError(f"{src.label} ist noch nicht verbunden – erst Adresse und Schlüssel eintragen")
        devs, ents = await self._ha_ws({"type": "config/device_registry/list"}, {"type": "config/entity_registry/list"})
        ids = set()
        for d in devs or []:
            conns = {str(c[1]).lower() for c in (d.get("connections") or []) if len(c) > 1}
            dn = {str(d.get("name") or "").lower(), str(d.get("name_by_user") or "").lower()}
            if (mac and mac in conns) or (names & dn):
                ids.add(d.get("id"))
        return [
            e for e in (ents or [])
            if e.get("device_id") in ids and e.get("platform") == "esphome"
            and str(e.get("entity_id", "")).startswith("assist_satellite.")
        ]

    async def sat_takeover(self, take: bool = True, index=None) -> dict:
        """take=True: Assist-Satellit des Geräts in Home Assistant abschalten, damit das Mikrofon zu GJarvis
        kommt. take=False: wieder einschalten (zurückgeben). Nur auf Knopfdruck in der Oberfläche.
        index = Nummer in der Satellitenliste; ohne index: alle blockierten (bzw. alle) Satelliten."""
        sats = self.sat_sources
        if index is not None:
            try:
                sats = [sats[int(index)]]
            except (IndexError, ValueError, TypeError):
                return {"ok": False, "error": "Diesen Satelliten gibt es (noch) nicht – erst speichern"}
        elif take:
            sats = [s for s in sats if s.blocked] or sats
        if not sats:
            return {"ok": False, "error": "Kein Satellit eingetragen"}
        changed, missing = [], []
        for src in sats:
            ents = await self._sat_ha_entities(src)
            if not ents:
                missing.append(src.label)
                continue
            for e in ents:
                if take and e.get("disabled_by") is None:
                    await self._ha_ws({"type": "config/entity_registry/update", "entity_id": e["entity_id"],
                                       "disabled_by": "user"})
                    changed.append(e["entity_id"])
                elif not take and e.get("disabled_by") == "user":
                    await self._ha_ws({"type": "config/entity_registry/update", "entity_id": e["entity_id"],
                                       "disabled_by": None})
                    changed.append(e["entity_id"])
            src.taken = take
        if missing and len(missing) == len(sats):
            return {"ok": False, "error": "Zu " + ", ".join(missing) + " gibt es in Home Assistant keinen Assist-Satelliten"}
        if take:
            _LOGGER.info("Satellit übernommen – Home Assistant gibt das Mikrofon frei (%s)", ", ".join(changed) or "schon frei")
        else:
            _LOGGER.info("Satellit an Home Assistant zurückgegeben (%s)", ", ".join(changed) or "war nicht abgeschaltet")
        return {"ok": True, "changed": changed, "taken": take}

    async def sat_devices(self) -> list:
        """ESPHome-Sprachgeräte aus Home Assistant für die Einrichtung (Name, Vorschlag für die Adresse)."""
        devs, ents = await self._ha_ws({"type": "config/device_registry/list"}, {"type": "config/entity_registry/list"})
        voice = {e.get("device_id") for e in (ents or [])
                 if e.get("platform") == "esphome" and str(e.get("entity_id", "")).startswith("assist_satellite.")}
        out = []
        for d in devs or []:
            if d.get("id") not in voice:
                continue
            name = d.get("name_by_user") or d.get("name") or ""
            host = str(d.get("name") or "").strip().lower().replace(" ", "-")
            out.append({"name": name, "host": f"{host}.local" if host else "", "model": d.get("model") or ""})
        return out

    def satellite_status(self) -> dict:
        sats = self.sat_sources
        first = sats[0] if sats else None
        act = getattr(self, "active_src", None)
        return {
            "audio_source": (self.o.get("audio_source") or "local") if self.use_satellite else "local",
            "satellite_host": first.host if first else (self.o.get("satellite_host") or ""),
            "satellite_name": first.label if first else "",
            "satellite_connected": bool(first and first.connected),
            "satellite_streaming": bool(first and first.streaming),
            "satellite_blocked": any(s.blocked for s in sats),
            "satellite_taken": any(s.taken for s in sats),
            "satellite_error": int(getattr(self, "sat_error_code", 0)),
            "sources": [s.status() for s in getattr(self, "sources", [])],
            "active_source": act.label if act else "",
            "output": self.remote_player or "local",
            "output_tts": self.remote_tts or "piper",
        }
