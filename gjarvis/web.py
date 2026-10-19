"""GJarvis – Web-Oberfläche (Home-Assistant-Seitenleiste über Ingress)."""

import asyncio
import json
import logging
import os
import re
import time
from collections import deque
from pathlib import Path

import requests
import yaml
from aiohttp import web

_LOGGER = logging.getLogger("gjarvis.web")
WEB_DIR = Path(os.environ.get("GJARVIS_WEB_DIR", Path(__file__).parent / "web"))
META_CONFIG = Path(os.environ.get("GJARVIS_META_CONFIG", Path(__file__).parent / "config.yaml"))
META_TRANS = Path(os.environ.get("GJARVIS_META_TRANS", Path(__file__).parent / "translations" / "de.yaml"))
PORT = int(os.environ.get("GJARVIS_WEB_PORT", "8099"))

# Bereiche der Einstellungen (Reihenfolge = Anzeige). Jede Option aus config.yaml erscheint genau einmal;
# was hier fehlt, landet automatisch unter "Erweitert". (id, Titel, Beschreibung, Pro?, Schlüssel)
GROUPS = [
    ("allgemein", "Allgemein", "Name, Anrede und Grundverhalten", False, [
        "assistant_name", "user_name", "home_city", "language", "agent_id", "local_agent_id", "quiet_hours",
    ]),
    ("stimme", "Stimme & Lautsprecher", "Wie und wo Jarvis spricht", False, [
        "tts_voice", "volume", "output_media_player", "output_tts_entity", "output_latency_seconds",
        "ack_phrases", "ack_order", "instant_ack_phrases",
    ]),
    ("satellit", "Mikrofon & Satellit", "Woher Jarvis hört – Server-Mikrofon oder ESPHome-Satellit", False, [
        "audio_source", "satellite_host", "satellite_port", "satellite_key", "satellite_led",
        "mic_gain", "stt_max_gain", "mic_watchdog_seconds",
    ]),
    ("weckwort", "Weckwort & Zuhören", "„Hey Jarvis“ erkennen und das Satzende finden", False, [
        "wake_threshold", "wake_refractory_seconds", "wake_auto_gain", "wake_max_gain", "wake_word_url",
        "speech_threshold", "end_of_speech_silence_seconds", "no_speech_timeout_seconds", "max_command_seconds",
        "one_breath_seconds", "preroll_ms", "speech_start_ms", "speech_energy_factor", "vad_mode",
    ]),
    ("gespraech", "Gespräch", "Nachfragen, Unterbrechen, Zwischenmeldungen", True, [
        "follow_up", "follow_up_seconds", "barge_in", "barge_in_threshold", "memory_enabled",
        "async_after_seconds", "async_ack", "async_result_prefix",
        "progress_enabled", "progress_interval_seconds", "progress_max", "progress_phrases",
    ]),
    ("funktionen", "Funktionen", "Briefing, Wetter, Flugwetter, Apps", True, [
        "briefing_triggers", "briefing_news", "briefing_flight", "briefing_calendars",
        "weather_entity", "weather_triggers", "apps_enabled", "mealie_config_entry_id",
        "flight_enabled", "flight_triggers", "flight_site_name", "flight_lat", "flight_lon",
        "paraglidable_api_key", "windy_api_key",
    ]),
    ("ki", "KI & Recherche", "Eigenes KI-Modell, Persönlichkeit, Internet-Suche", True, [
        "master_router", "research_llm_type", "llm_agent_id", "research_llm_url", "research_llm_model",
        "research_llm_api_key", "persona", "system_prompt", "research_enabled", "research_triggers",
        "research_ack", "searxng_url", "wikipedia_lang",
    ]),
    ("verbindungen", "Verbindungen", "Whisper, Piper und MQTT (GasLighter)", False, [
        "stt_host", "stt_port", "tts_host", "tts_port", "mqtt_state_topic", "mqtt_pause_enabled",
        "mqtt_pause_topic", "mqtt_pause_payload", "mqtt_resume_payload", "mqtt_resume_delay_seconds",
    ]),
    ("erweitert", "Erweitert", "Kalibrierung, Modelle, Fehlersuche", False, [
        "calibration_sentences", "calibration_wake_voice", "feature_models_url", "debug",
    ]),
]
# Diese Werte brauchen einen Neustart von GJarvis
RESTART_KEYS = {
    "wake_word_url", "feature_models_url", "debug", "mic_watchdog_seconds",
    "audio_source", "satellite_host", "satellite_port", "satellite_key", "mqtt_state_topic",
}


class RingLog(logging.Handler):
    def __init__(self, n: int = 400) -> None:
        super().__init__()
        self.lines: deque = deque(maxlen=n)
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.lines.append(self.format(record))
        except Exception:  # noqa: BLE001
            pass


RING = RingLog()


def parse_schema(spec) -> dict:
    """Home-Assistant-Schema (z. B. 'float(0,1)', 'list(a|b)', 'password?') in UI-Typ übersetzen."""
    if isinstance(spec, list):
        return {"type": "list"}
    s = str(spec).rstrip("?")
    m = re.match(r"(int|float)(?:\(([^,]*),([^)]*)\))?$", s)
    if m:
        return {"type": m.group(1), "min": float(m.group(2)) if m.group(2) else None,
                "max": float(m.group(3)) if m.group(3) else None}
    m = re.match(r"list\((.*)\)", s)
    if m:
        return {"type": "select", "options": m.group(1).split("|")}
    return {"type": {"bool": "bool", "port": "int", "password": "password", "url": "str"}.get(s, "str")}


def field_meta() -> dict:
    try:
        cfg = yaml.safe_load(META_CONFIG.read_text(encoding="utf-8"))
        tr = (yaml.safe_load(META_TRANS.read_text(encoding="utf-8")) or {}).get("configuration", {})
    except Exception as e:  # noqa: BLE001
        _LOGGER.warning("Metadaten nicht lesbar: %s", e)
        return {"fields": {}, "groups": [], "version": "?"}
    schema = cfg.get("schema") or {}
    fields = {}
    for k, spec in schema.items():
        meta = parse_schema(spec)
        meta["label"] = (tr.get(k) or {}).get("name", k)
        meta["help"] = (tr.get(k) or {}).get("description", "")
        meta["restart"] = k in RESTART_KEYS
        meta["optional"] = str(spec).endswith("?")
        fields[k] = meta
    groups, seen = [], set()
    for gid, title, desc, pro, keys in GROUPS:
        ks = [k for k in keys if k in fields and k not in seen]
        seen.update(ks)
        groups.append({"id": gid, "title": title, "desc": desc, "pro": pro, "keys": ks})
    rest = [k for k in fields if k not in seen]
    if rest:  # neue Optionen ohne Zuordnung nie verstecken
        groups[-1]["keys"] += rest
    return {"fields": fields, "groups": groups, "version": cfg.get("version", "?")}


def make_app(gj) -> web.Application:
    meta = field_meta()
    app = web.Application()

    async def index(request):
        return web.FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    async def status(request):
        return web.json_response(gj.status(), dumps=lambda o: json.dumps(o, default=float))

    async def logs(request):
        return web.json_response({"lines": list(RING.lines)[-250:]})

    async def get_settings(request):
        raw = dict(gj.raw)
        for k, f in meta["fields"].items():
            if f["type"] == "password" and raw.get(k):
                raw[k] = "••••••"
        return web.json_response({"values": raw, "restart_pending": bool(getattr(gj, "restart_pending", False)), **meta})

    async def post_settings(request):
        data = await request.json()
        changes = {}
        for k, v in (data.get("values") or {}).items():
            f = meta["fields"].get(k)
            if not f or (f["type"] == "password" and v == "••••••"):
                continue
            try:
                if f["type"] == "bool":
                    v = bool(v)
                elif f["type"] == "int":
                    v = int(float(str(v).replace(",", ".")))
                elif f["type"] == "float":
                    v = float(str(v).replace(",", "."))
                elif f["type"] == "list":
                    v = [str(x).strip() for x in (v if isinstance(v, list) else str(v).split("\n")) if str(x).strip()]
                else:
                    v = "" if v is None else str(v).strip()
                if f["type"] in ("int", "float"):
                    if f.get("min") is not None:
                        v = max(type(v)(f["min"]), v)
                    if f.get("max") is not None:
                        v = min(type(v)(f["max"]), v)
                if f["type"] == "select" and v not in f.get("options", []):
                    raise ValueError(v)
            except (TypeError, ValueError):
                return web.json_response({"ok": False, "key": k, "error": f"Ungültiger Wert für „{f['label']}“"},
                                         status=400)
            if gj.raw.get(k) != v:
                changes[k] = v
        if not changes:
            return web.json_response({"ok": True, "changed": [], "restart": False})
        ok, err = await asyncio.to_thread(gj.persist_options, changes)
        if not ok:
            return web.json_response({"ok": False, "error": "Home Assistant hat die Einstellungen abgelehnt: " + err},
                                     status=400)
        restart = gj.apply_settings(changes)
        if restart:
            gj.restart_pending = True
        return web.json_response({"ok": True, "changed": list(changes), "restart": restart})

    async def test(request):
        what = request.match_info["what"]
        t0 = time.monotonic()
        try:
            msg = await gj.test_connection(what)
            ok = True
        except Exception as e:  # noqa: BLE001
            ok, msg = False, str(e)[:300]
        return web.json_response({"ok": ok, "msg": msg, "ms": round((time.monotonic() - t0) * 1000)})

    async def ask(request):
        data = await request.json()
        text = (data.get("text") or "").strip()
        if not text:
            return web.json_response({"ok": False, "error": "Kein Text"}, status=400)
        t0 = time.monotonic()
        gj.last_command = text
        speech, _ = await asyncio.to_thread(gj.route_text, text)
        gj.last_answer = speech
        if data.get("speak") and speech:
            asyncio.create_task(gj.announce(speech))
        return web.json_response({"ok": True, "answer": speech, "ms": round((time.monotonic() - t0) * 1000)})

    async def say(request):
        data = await request.json()
        text = (data.get("text") or "").strip() or f"Hallo, hier ist {gj.o.get('assistant_name', 'Jarvis')}."
        asyncio.create_task(gj.announce(text))
        return web.json_response({"ok": True})

    async def calibrate(request):
        gj.calibrate_requested = True
        return web.json_response({"ok": True})

    async def stop(request):
        gj.stop_speaking()
        return web.json_response({"ok": True})

    async def briefing(request):
        asyncio.create_task(gj.briefing_announce())
        return web.json_response({"ok": True})

    async def reminder_delete(request):
        rid = request.match_info["rid"]
        gj.reminders = [r for r in gj.reminders if r["id"] != rid]
        gj.save_reminders()
        return web.json_response({"ok": True})

    async def pro_get(request):
        return web.json_response(gj.pro_state())

    async def pro_post(request):
        data = await request.json()
        if data.get("remove"):
            return web.json_response(gj.pro_del())
        r = gj.pro_set(str(data.get("key") or ""))
        return web.json_response(r, status=200 if r["ok"] else 400)

    def pro_only(handler):
        async def wrapped(request):
            if not gj.pro:
                return web.json_response({"ok": False, "error": "pro"}, status=402)
            return await handler(request)
        return wrapped

    async def whisper_get(request):
        try:
            return web.json_response({"ok": True, **(await asyncio.to_thread(gj.whisper_check))})
        except Exception as e:  # noqa: BLE001
            return web.json_response({"ok": False, "error": str(e)[:300]})

    async def whisper_setup(request):
        try:
            return web.json_response({"ok": True, "msg": await asyncio.to_thread(gj.whisper_setup)})
        except Exception as e:  # noqa: BLE001
            return web.json_response({"ok": False, "error": str(e)[:300]})

    async def llm_models(request):
        q = request.query
        kind = q.get("type") or gj.o.get("research_llm_type", "ollama")
        url = q.get("url") if "url" in q else None
        key = q.get("key") if q.get("key") not in (None, "", "••••••") else None
        cur = gj.o.get("llm_agent_id") or gj.o.get("agent_id") if kind == "ha_agent" else gj.o.get("research_llm_model")
        try:
            models = await asyncio.to_thread(gj.llm_models, kind, url, key)
            return web.json_response({"ok": True, "current": cur, "type": gj.o.get("research_llm_type"),
                                      "url": gj.o.get("research_llm_url", ""), "models": models})
        except Exception as e:  # noqa: BLE001
            return web.json_response({"ok": False, "error": str(e)[:300], "current": cur,
                                      "type": gj.o.get("research_llm_type"), "url": gj.o.get("research_llm_url", "")})

    async def llm_discover(request):
        return web.json_response({"found": await asyncio.to_thread(gj.llm_discover)})

    async def llm_test(request):
        t0 = time.monotonic()
        try:
            ans = await asyncio.to_thread(gj.ask_llm, [{"role": "user", "content": "Sag in einem kurzen Satz auf Deutsch Hallo."}])
            return web.json_response({"ok": True, "msg": gj.clean_for_speech(ans)[:160], "ms": round((time.monotonic() - t0) * 1000)})
        except Exception as e:  # noqa: BLE001
            return web.json_response({"ok": False, "msg": str(e)[:200], "ms": round((time.monotonic() - t0) * 1000)})

    async def llm_bench_start(request):
        data = await request.json()
        models = [m for m in (data.get("models") or []) if m][:6]
        if getattr(gj, "bench", {}).get("running"):
            return web.json_response({"ok": False, "error": "Vergleich läuft schon"})
        gj.bench = {"running": True, "results": [], "current": ""}
        asyncio.create_task(asyncio.to_thread(gj.llm_benchmark, models))
        return web.json_response({"ok": True})

    async def llm_bench_get(request):
        return web.json_response(getattr(gj, "bench", {"running": False, "results": []}))

    async def restart(request):
        async def _bye():
            await asyncio.sleep(0.5)
            os._exit(0)  # Supervisor startet die App neu (watchdog)

        asyncio.create_task(_bye())
        return web.json_response({"ok": True})

    app.router.add_get("/", index)
    app.router.add_get("/api/status", status)
    app.router.add_get("/api/log", logs)
    app.router.add_get("/api/settings", get_settings)
    app.router.add_post("/api/settings", post_settings)
    app.router.add_post("/api/test/{what}", test)
    app.router.add_post("/api/ask", ask)
    app.router.add_post("/api/say", say)
    app.router.add_post("/api/calibrate", calibrate)
    app.router.add_post("/api/restart", restart)
    app.router.add_post("/api/stop", stop)
    app.router.add_post("/api/briefing", pro_only(briefing))
    app.router.add_get("/api/pro", pro_get)
    app.router.add_get("/api/whisper", whisper_get)
    app.router.add_get("/api/llm/models", llm_models)
    app.router.add_get("/api/llm/discover", llm_discover)
    app.router.add_post("/api/llm/test", llm_test)
    app.router.add_post("/api/llm/benchmark", llm_bench_start)
    app.router.add_get("/api/llm/benchmark", llm_bench_get)
    app.router.add_post("/api/whisper/setup", whisper_setup)
    app.router.add_post("/api/pro", pro_post)
    app.router.add_post("/api/reminder/{rid}/delete", reminder_delete)
    return app


async def start_web(gj) -> None:
    app = make_app(gj)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    _LOGGER.info("Oberfläche bereit (Port %d, in der Seitenleiste: GJarvis)", PORT)
