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


class SatelliteFeatures:
    """Mixin für GJarvis: ESPHome-Satellit als Mikrofon, Home-Assistant-Lautsprecher als Ausgabe."""

    # --------------------------------------------------------------------- #
    # Gemeinsame Helfer
    # --------------------------------------------------------------------- #
    def feed_frame(self, frame: bytes) -> None:
        """Einen Mikrofon-Block (80 ms, 16 kHz, 16 Bit, mono) in die Verarbeitung geben –
        egal ob er vom Server-Mikrofon oder vom Satelliten kommt."""
        if self.discard:
            if self.barge_q is not None and not self.barge_q.full():
                self.barge_q.put_nowait(frame)
            return
        gain = float(self.o.get("mic_gain", 1.0))
        if abs(gain - 1.0) >= 1e-3:
            a = np.frombuffer(frame, dtype=np.int16).astype(np.float32) * gain
            frame = np.clip(a, -32768, 32767).astype(np.int16).tobytes()
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

    @property
    def use_satellite(self) -> bool:
        return self.o.get("audio_source") == "satellite" and bool(self.o.get("satellite_host"))

    @property
    def remote_player(self) -> str:
        return (self.o.get("output_media_player") or "").strip()

    @property
    def remote_tts(self) -> str:
        """TTS-Entität aus Home Assistant (z. B. tts.elevenlabs_…) – nur zusammen mit externem Lautsprecher."""
        return (self.o.get("output_tts_entity") or "").strip() if self.remote_player else ""

    # --------------------------------------------------------------------- #
    # Eingang: ESPHome-Satellit
    # --------------------------------------------------------------------- #
    async def satellite_reader(self) -> None:
        """Verbindet sich mit dem Satelliten und hält die Verbindung (mit automatischem Neuaufbau)."""
        try:
            from aioesphomeapi import APIClient, LightInfo, SelectInfo  # noqa: PLC0415
        except ImportError:
            _LOGGER.error("aioesphomeapi fehlt – Satellit kann nicht verbunden werden")
            return

        host = str(self.o.get("satellite_host")).strip()
        port = int(self.o.get("satellite_port", 6053) or 6053)
        key = (self.o.get("satellite_key") or "").strip() or None
        frame_bytes = 1280 * 2  # OWW_FRAME * WIDTH
        self.sat_client = None
        self.sat_connected = False
        retry = 5.0
        while True:
            stopped = asyncio.Event()
            buf = bytearray()
            client = APIClient(host, port, None, noise_psk=key, client_info="GJarvis")

            async def on_stop(expected: bool, _ev=stopped) -> None:
                _ev.set()

            async def handle_start(*_args) -> int:
                nonlocal retry
                retry = 5.0  # erst echtes Audio setzt die Wartezeit zurück
                buf.clear()
                self.sat_last_audio = time.monotonic()
                _LOGGER.info("Satellit streamt sein Mikrofon")
                return 0  # 0 = Audio über die API-Verbindung (kein eigener UDP-Port)

            async def handle_stop(*_args) -> None:
                _LOGGER.debug("Satellit hat das Streaming beendet")

            async def handle_audio(data: bytes, *_args) -> None:
                self.sat_last_audio = time.monotonic()
                buf.extend(data)
                while len(buf) >= frame_bytes:
                    self.feed_frame(bytes(buf[:frame_bytes]))
                    del buf[:frame_bytes]

            try:
                await client.connect(on_stop=on_stop, login=True)
                info = await client.device_info()
                entities, _ = await client.list_entities_services()
                _LOGGER.info("Satellit verbunden: %s (%s)", info.friendly_name or info.name, host)
                # Erst abonnieren, dann die Weckwort-Erkennung umstellen – das Umstellen startet den Stream.
                self.sat_last_audio = 0.0
                client.subscribe_voice_assistant(
                    handle_start=handle_start, handle_stop=handle_stop, handle_audio=handle_audio
                )
                self.sat_light, self.sat_effects = None, []
                for e in entities:
                    if isinstance(e, LightInfo) and self.sat_light is None:
                        self.sat_light, self.sat_effects = e.key, list(e.effects or [])
                    if isinstance(e, SelectInfo) and any(n in (e.name or "").lower() for n in WAKE_LOCATION_NAMES):
                        if WAKE_LOCATION_REMOTE in (e.options or []):
                            client.select_command(e.key, WAKE_LOCATION_REMOTE)
                            _LOGGER.info("Satellit: Weckwort-Erkennung auf GJarvis umgestellt")
                self.sat_client = client
                self.sat_connected = True
                self.sat_streaming = False
                self._led_for_state(getattr(self, "_sat_last", "idle"))
                connected_at = time.monotonic()
                silent_s = float(self.o.get("satellite_watchdog_seconds", 15))
                while not stopped.is_set():
                    try:
                        await asyncio.wait_for(stopped.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        last = getattr(self, "sat_last_audio", 0.0) or connected_at
                        self.sat_streaming = time.monotonic() - last < silent_s
                        if not self.sat_streaming:
                            # Typisch: Home Assistant (ESPHome-Integration) hält den Sprach-Stream des Geräts.
                            _LOGGER.error(
                                "Satellit %s schickt kein Audio. Wahrscheinlich nutzt Home Assistant das Gerät als "
                                "Sprach-Satellit – bitte das Gerät in Home Assistant unter ESPHome deaktivieren. "
                                "Verbinde neu …", host)
                            break
                        # Firmware setzt die LED manchmal selbst zurück – Farbe regelmäßig auffrischen
                        if (not getattr(self, "sat_error_code", 0) and not self.busy
                                and time.monotonic() - getattr(self, "_sat_led_ts", 0) > 30):
                            self._led_for_state(getattr(self, "_sat_last", "idle"))
                if stopped.is_set():
                    _LOGGER.warning("Verbindung zum Satelliten getrennt – verbinde neu")
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if "encryption" in msg.lower() or "noise" in msg.lower() or "psk" in msg.lower():
                    _LOGGER.error("Satellit %s: Verschlüsselungsschlüssel fehlt oder ist falsch (%s)", host, msg)
                else:
                    _LOGGER.warning("Satellit %s nicht erreichbar: %s", host, msg)
            finally:
                self.sat_client = None
                self.sat_connected = False
                self.sat_streaming = False
                try:
                    await client.disconnect()
                except Exception:  # noqa: BLE001
                    pass
            await asyncio.sleep(retry)
            retry = min(retry * 2, 60.0)

    # --------------------------------------------------------------------- #
    # LED am Satelliten
    # --------------------------------------------------------------------- #
    # Farbe (r, g, b), Helligkeit, Effekt
    LED_STATES = {
        "idle": ((0.0, 1.0, 0.0), 0.25, None),        # grün gedimmt: alles ok, wartet auf "Hey Jarvis"
        "listening": ((0.0, 1.0, 0.0), 0.9, None),    # grün hell: hört zu
        "processing": ((1.0, 0.7, 0.0), 0.9, "Slow Pulse"),  # gelb pulsierend: denkt nach
        "responding": ((1.0, 0.7, 0.0), 0.9, None),   # gelb: spricht
    }
    # Fehlercodes = Anzahl roter Blinker
    ERROR_CODES = {
        1: "Spracherkennung (Whisper) antwortet nicht",
        2: "Home Assistant / KI antwortet nicht",
        3: "Lautsprecher-Ausgabe fehlgeschlagen",
        4: "Sprachausgabe (TTS) fehlgeschlagen",
        9: "Unerwarteter Fehler – siehe Protokoll",
    }

    def _led(self, on: bool, rgb=None, brightness=None, effect=None) -> None:
        c = getattr(self, "sat_client", None)
        key = getattr(self, "sat_light", None)
        if not (c and key is not None and self.o.get("satellite_led", True)):
            return
        kw = {"state": on}
        if on:
            kw.update(rgb=rgb, brightness=brightness)
            effects = getattr(self, "sat_effects", [])
            if effects:
                kw["effect"] = effect if effect in effects else "None"
        def send() -> None:
            try:
                c.light_command(key, **kw)
                self._sat_led_ts = time.monotonic()
            except Exception as e:  # noqa: BLE001
                _LOGGER.debug("Satellit-LED: %s", e)

        loop = getattr(self, "loop", None)
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if loop and running is not loop:
            loop.call_soon_threadsafe(send)  # aus einem Thread: über die Ereignisschleife senden
        else:
            send()

    def _led_for_state(self, state: str) -> None:
        rgb, bri, eff = self.LED_STATES.get(state, self.LED_STATES["idle"])
        self._led(True, rgb, bri, eff)

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
        if not getattr(self, "sat_client", None):
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
        """Warten, bis der externe Lautsprecher fertig ist (Mikrofon bleibt so lange stumm)."""
        end = time.monotonic() + seconds
        while time.monotonic() < end and not self.interrupted and not getattr(self, "remote_stop", False):
            await asyncio.sleep(0.1)

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
        """Text über eine TTS-Entität aus Home Assistant (z. B. ElevenLabs) auf dem media_player sprechen."""
        if getattr(self, "remote_stop", False):
            return
        await asyncio.to_thread(
            self.ha_service,
            "tts",
            "speak",
            {
                "entity_id": self.remote_tts,
                "media_player_entity_id": self.remote_player,
                "message": text,
                "cache": True,
            },
        )
        # Dauer schätzen: ~14 Zeichen pro Sekunde + Erzeugung und Netzwerk
        seconds = len(text) / 14.0 + float(self.o.get("output_latency_seconds", 1.5)) + 1.0
        await self._wait_spoken(seconds)

    def stop_remote(self) -> None:
        if not self.remote_player:
            return
        try:
            self.ha_service("media_player", "media_stop", {"entity_id": self.remote_player})
        except Exception as e:  # noqa: BLE001
            _LOGGER.debug("Stopp am Lautsprecher: %s", e)

    def satellite_status(self) -> dict:
        return {
            "audio_source": "satellite" if self.use_satellite else "local",
            "satellite_host": self.o.get("satellite_host") or "",
            "satellite_connected": bool(getattr(self, "sat_connected", False)),
            "satellite_streaming": bool(getattr(self, "sat_streaming", False)),
            "satellite_error": int(getattr(self, "sat_error_code", 0)),
            "output": self.remote_player or "local",
            "output_tts": self.remote_tts or "piper",
        }
