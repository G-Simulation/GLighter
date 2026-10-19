"""GJarvis – 'wie im Film': Gedächtnis, Erinnerungen/Timer, Morgen-Briefing, Ansagen, Ruhezeiten.

Alles ohne KI (schnell und zuverlässig), alles auf Deutsch.
"""

import asyncio
import datetime as dt
import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import requests

_LOGGER = logging.getLogger("gjarvis")

# werden von gjarvis.py gesetzt
DATA_DIR = None
HA_URL = ""
HA_TOKEN = ""

ZAHLEN = {
    "null": 0, "ein": 1, "eins": 1, "eine": 1, "einer": 1, "einen": 1, "zwei": 2, "drei": 3, "vier": 4,
    "fünf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12,
    "dreizehn": 13, "vierzehn": 14, "fünfzehn": 15, "sechzehn": 16, "siebzehn": 17, "achtzehn": 18,
    "neunzehn": 19, "zwanzig": 20, "dreißig": 30, "dreissig": 30, "vierzig": 40, "fünfzig": 50,
    "sechzig": 60, "neunzig": 90,
}
EINER = {"ein": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9}
ZEHNER = {"zwanzig": 20, "dreißig": 30, "dreissig": 30, "vierzig": 40, "fünfzig": 50}
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
          "November", "Dezember"]

SECRET_WORDS = ["passwort", "kennwort", "pin ", "pin-", "pincode", "iban", "kreditkarte", "tan ", "geheimzahl",
                "zugangsdaten", "api-key", "apikey", "schlüssel für"]
CLOSERS = ["danke", "dankeschön", "vielen dank", "das wars", "das war's", "das war es", "passt", "nichts",
           "nein danke", "ok danke", "okay danke", "gut danke", "alles klar", "tschüss", "bis später"]
STOPPERS = ["stopp", "stop", "halt", "ruhe", "sei still", "sei ruhig", "abbrechen", "abbruch", "vergiss es",
            "schon gut", "egal"]


def zahl(wort: str) -> Optional[float]:
    """'5', '5,5', 'fünf', 'fünfundzwanzig', 'einer halben', 'anderthalb' -> Zahl."""
    w = wort.lower().strip().replace(",", ".")
    if re.fullmatch(r"\d+(\.\d+)?", w):
        return float(w)
    if w in ("halbe", "halben", "einer halben", "eine halbe", "ner halben"):
        return 0.5
    if w in ("anderthalb", "eineinhalb"):
        return 1.5
    if w in ZAHLEN:
        return float(ZAHLEN[w])
    m = re.fullmatch(r"(ein|zwei|drei|vier|fünf|sechs|sieben|acht|neun)und(zwanzig|dreißig|dreissig|vierzig|fünfzig)", w)
    if m:
        return float(EINER[m.group(1)] + ZEHNER[m.group(2)])
    return None


ZAHL_RE = (r"(\d+(?:[.,]\d+)?|einer halben|eine halbe|ner halben|halben|anderthalb|eineinhalb|"
           r"(?:ein|zwei|drei|vier|fünf|sechs|sieben|acht|neun)und(?:zwanzig|dreißig|dreissig|vierzig|fünfzig)|"
           + "|".join(sorted(ZAHLEN, key=len, reverse=True)) + r")")
DAUER_RE = re.compile(ZAHL_RE + r"\s*(sekunden?|sek|minuten?|min|stunden?|std|h)\b", re.I)


def dauer_sekunden(text: str) -> Optional[float]:
    """Summe aller Zeitangaben: '1 Stunde und 20 Minuten' -> 4800."""
    total, found = 0.0, False
    for m in DAUER_RE.finditer(text):
        n = zahl(m.group(1))
        if n is None:
            continue
        u = m.group(2).lower()
        total += n * (3600 if u.startswith(("stund", "std", "h")) else 60 if u.startswith("min") else 1)
        found = True
    if not found and re.search(r"\b(halbe|halben) stunde", text, re.I):
        return 1800.0
    if not found and re.search(r"\bviertelstunde\b", text, re.I):
        return 900.0
    return total if found and total > 0 else None


def dauer_text(sec: float) -> str:
    sec = int(round(sec))
    h, rest = divmod(sec, 3600)
    m, s = divmod(rest, 60)
    teile = []
    if h:
        teile.append("einer Stunde" if h == 1 else f"{h} Stunden")
    if m:
        teile.append("einer Minute" if m == 1 else f"{m} Minuten")
    if s and not h:
        teile.append("einer Sekunde" if s == 1 else f"{s} Sekunden")
    return " und ".join(teile) or "0 Sekunden"


def dauer_nominativ(sec: float) -> str:
    return dauer_text(sec).replace("einer Stunde", "eine Stunde").replace("einer Minute", "eine Minute") \
        .replace("einer Sekunde", "eine Sekunde")


def uhrzeit(text: str, jetzt: dt.datetime) -> Optional[dt.datetime]:
    """'um 18 Uhr', 'um 18:30', 'um halb sieben', 'morgen um 7' -> Zeitpunkt."""
    t = text.lower()
    tag = jetzt.date()
    if "übermorgen" in t:
        tag += dt.timedelta(days=2)
    elif "morgen" in t and not re.search(r"\bguten morgen\b|\bmorgens\b|\bheute morgen\b", t):
        tag += dt.timedelta(days=1)
    h = mi = None
    m = re.search(r"\bum (\d{1,2})[:.](\d{2})", t) or re.search(r"\bum (\d{1,2}) uhr (\d{1,2})\b", t)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
    else:
        m = re.search(r"\bum halb " + ZAHL_RE + r"\b", t)
        if m and zahl(m.group(1)) is not None:
            h, mi = int(zahl(m.group(1))) - 1, 30
        else:
            m = re.search(r"\bum viertel nach " + ZAHL_RE + r"\b", t)
            if m and zahl(m.group(1)) is not None:
                h, mi = int(zahl(m.group(1))), 15
            else:
                m = re.search(r"\bum viertel vor " + ZAHL_RE + r"\b", t)
                if m and zahl(m.group(1)) is not None:
                    h, mi = int(zahl(m.group(1))) - 1, 45
                else:
                    m = re.search(r"\bum " + ZAHL_RE + r"(?: uhr)?\b", t)
                    if m and zahl(m.group(1)) is not None:
                        h, mi = int(zahl(m.group(1))), 0
    if h is None:
        return None
    if re.search(r"\b(abends?|nachmittags?)\b", t) and h < 12:
        h += 12
    h %= 24
    ziel = dt.datetime.combine(tag, dt.time(h, mi % 60))
    if ziel <= jetzt and tag == jetzt.date():
        # 'um 7' am Abend gesagt -> 19 Uhr, falls noch heute; sonst morgen
        if h < 12 and ziel + dt.timedelta(hours=12) > jetzt and "morgens" not in t and "früh" not in t:
            ziel += dt.timedelta(hours=12)
        else:
            ziel += dt.timedelta(days=1)
    return ziel


def zeit_sprechen(z: dt.datetime, jetzt: dt.datetime) -> str:
    u = f"{z.hour} Uhr" + (f" {z.minute}" if z.minute else "")
    if z.date() == jetzt.date():
        return f"um {u}"
    if z.date() == jetzt.date() + dt.timedelta(days=1):
        return f"morgen um {u}"
    return f"am {WOCHENTAGE[z.weekday()]} um {u}"


def perspektive(text: str) -> str:
    """'ich/mein/mir' (so wie gesagt) -> 'du/dein/dir' (so wie Jarvis es zurücksagt)."""
    ersatz = {"ich": "du", "mich": "dich", "mir": "dir", "mein": "dein", "meine": "deine", "meinen": "deinen",
              "meinem": "deinem", "meiner": "deiner", "meines": "deines", "bin": "bist", "habe": "hast",
              "hab": "hast", "wir": "ihr", "unser": "euer", "unsere": "eure", "unseren": "euren"}

    if re.search(r"\b(ich|wir)\b", text, re.I):
        ersatz.update({"muss": "musst", "will": "willst", "soll": "sollst", "kann": "kannst", "darf": "darfst",
                       "möchte": "möchtest", "wollte": "wolltest", "werde": "wirst", "brauche": "brauchst"})

    def rep(m):
        w = m.group(0)
        r = ersatz.get(w.lower(), w)
        return r.capitalize() if w[0].isupper() else r

    return re.sub(r"\b\w+\b", rep, text)


class MovieFeatures:
    """Wird von GJarvis geerbt. Erwartet self.o, self.announce(), self.publish(), self.ha_get()."""

    # ------------------------------------------------------------------ Hilfen
    def _json_load(self, name: str, default):
        try:
            return json.loads((Path(DATA_DIR) / name).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return default

    def _json_save(self, name: str, data) -> None:
        try:
            (Path(DATA_DIR) / name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("%s nicht gespeichert: %s", name, e)

    @property
    def user(self) -> str:
        return self.o.get("user_name") or ""

    def anrede(self, satz: str) -> str:
        """'Erledigt.' -> 'Erledigt, Moses.' (nur wenn ein Name eingestellt ist)."""
        if not self.user:
            return satz
        return re.sub(r"[.!]?$", f", {self.user}.", satz.rstrip(), count=1)

    def in_quiet_hours(self, now: Optional[dt.datetime] = None) -> bool:
        q = (self.o.get("quiet_hours") or "").strip()
        m = re.fullmatch(r"(\d{1,2}):?(\d{2})?\s*-\s*(\d{1,2}):?(\d{2})?", q)
        if not m:
            return False
        now = now or dt.datetime.now()
        a = int(m.group(1)) * 60 + int(m.group(2) or 0)
        b = int(m.group(3)) * 60 + int(m.group(4) or 0)
        n = now.hour * 60 + now.minute
        return (a <= n < b) if a <= b else (n >= a or n < b)

    # ------------------------------------------------------------------ Gedächtnis
    def memory_items(self) -> List[dict]:
        return self._json_load("memory.json", [])

    def memory_prompt(self) -> str:
        if not self.o.get("memory_enabled", True):
            return ""
        items = self.memory_items()[-40:]
        if not items:
            return ""
        who = self.user or "der Nutzer"
        lines = "\n".join(f"- {i['text']}" for i in items)
        return f"\n\nDas hat dir {who} früher gesagt (aus seiner Sicht, 'ich' = {who}):\n{lines}"

    def memory_command(self, text: str) -> Optional[str]:
        if not self.o.get("memory_enabled", True):
            return None
        t = text.strip().rstrip(".!?")
        low = t.lower()
        m = re.match(r"^(?:bitte\s+)?(?:merk|merke)(?:\s+dir)?(?:\s+bitte)?[,:]?\s+(?:dass\s+|das\s+)?(.+)$", low)
        if m:
            fact = t[len(t) - len(m.group(1)):].strip(" ,")
            if any(s in fact.lower() + " " for s in SECRET_WORDS):
                return self.anrede("Passwörter und Geheimzahlen merke ich mir aus Sicherheitsgründen nicht")
            items = self.memory_items()
            items.append({"text": fact, "ts": time.strftime("%Y-%m-%d %H:%M")})
            self._json_save("memory.json", items[-200:])
            _LOGGER.info("Gemerkt: %r", fact)
            return self.anrede("Notiert. Ich habe mir gemerkt, " + perspektive(fact).rstrip("."))
        m = re.match(r"^(?:bitte\s+)?vergiss(?:\s+bitte)?\s+(?:dass\s+|das mit\s+|das\s+)?(.+)$", low)
        if m and m.group(1) not in ("es", "das", "es bitte"):
            what = m.group(1)
            items = self.memory_items()
            if re.fullmatch(r"alles|alles was du (über mich )?weißt|alles über mich", what):
                self._json_save("memory.json", [])
                return self.anrede("Erledigt. Ich habe alles vergessen")
            words = [w for w in re.findall(r"\w{3,}", what) if w not in ("dass", "das", "mein", "meine", "ich")]
            keep = [i for i in items if not (words and sum(w in i["text"].lower() for w in words) >= max(1, len(words) // 2))]
            if len(keep) == len(items):
                return self.anrede("Dazu habe ich mir nichts gemerkt")
            self._json_save("memory.json", keep)
            return self.anrede(f"Erledigt. {len(items) - len(keep)} Notiz{'en' if len(items) - len(keep) > 1 else ''} gelöscht")
        if re.search(r"was (weißt|weisst) du (alles )?über mich|was hast du dir gemerkt|was du dir gemerkt hast", low):
            items = self.memory_items()
            if not items:
                return self.anrede("Bisher hast du mir noch nichts zum Merken gesagt")
            last = [perspektive(i["text"]).rstrip(".") for i in items[-5:]]
            more = f" und {len(items) - 5} weitere Dinge" if len(items) > 5 else ""
            return f"Ich weiß unter anderem: {'; '.join(last)}{more}."
        return None

    # ------------------------------------------------------------------ Erinnerungen / Timer
    def load_reminders(self) -> None:
        self.reminders = [r for r in self._json_load("reminders.json", []) if r.get("due", 0) > time.time() - 3600]

    def save_reminders(self) -> None:
        self._json_save("reminders.json", self.reminders)
        self.publish("gjarvis/reminders", json.dumps(
            {"anzahl": len(self.reminders), "naechste": self.next_reminder_text()}, ensure_ascii=False), retain=True)

    def next_reminder_text(self) -> str:
        if not self.reminders:
            return "keine"
        r = min(self.reminders, key=lambda x: x["due"])
        return f"{time.strftime('%H:%M', time.localtime(r['due']))} {r['text']}"

    def add_reminder(self, due: float, text: str, kind: str, dauer: float = 0) -> dict:
        r = {"id": uuid.uuid4().hex[:8], "due": due, "text": text, "kind": kind, "dauer": dauer,
             "erstellt": time.time()}
        self.reminders.append(r)
        self.save_reminders()
        _LOGGER.info("%s gestellt: %s um %s", "Timer" if kind == "timer" else "Erinnerung", text or "-",
                     time.strftime("%d.%m. %H:%M:%S", time.localtime(due)))
        return r

    def reminder_command(self, text: str) -> Optional[str]:
        t = text.strip().rstrip(".!?")
        low = t.lower()
        jetzt = dt.datetime.now()
        # --- Abfragen / Löschen
        if re.search(r"\b(timer|erinnerung|erinnerungen|wecker)\b", low) and re.search(
                r"\b(lösch|stopp|stop|abbrech|brich|beende|entfern|aus\b|weg\b|cancel)", low):
            alle = "alle" in low
            kind = "timer" if "timer" in low else None
            keep, weg = [], []
            for r in sorted(self.reminders, key=lambda x: x["due"]):
                if (kind is None or r["kind"] == kind) and (alle or not weg):
                    weg.append(r)
                else:
                    keep.append(r)
            if not weg:
                return self.anrede("Es läuft gerade nichts")
            self.reminders = keep
            self.save_reminders()
            if len(weg) == 1:
                return self.anrede(("Timer" if weg[0]["kind"] == "timer" else "Erinnerung") + " gelöscht")
            return self.anrede(f"{len(weg)} gelöscht")
        if re.search(r"wie lange (läuft |dauert )?(der |mein )?timer|wie viel zeit (hat|bleibt)|timer noch", low):
            timers = sorted([r for r in self.reminders if r["kind"] == "timer"], key=lambda x: x["due"])
            if not timers:
                return self.anrede("Es läuft kein Timer")
            return f"Noch {dauer_nominativ(max(1, timers[0]['due'] - time.time()))}."
        if re.search(r"welche (erinnerungen|timer|termine von dir)|was (hast du|steht) (für mich )?(an erinnerungen|vorgemerkt)|"
                     r"habe ich (noch )?(erinnerungen|timer)|meine erinnerungen", low):
            rs = sorted(self.reminders, key=lambda x: x["due"])
            if not rs:
                return self.anrede("Es sind keine Erinnerungen oder Timer gestellt")
            teile = []
            for r in rs[:5]:
                z = dt.datetime.fromtimestamp(r["due"])
                if r["kind"] == "timer":
                    teile.append(f"ein Timer, noch {dauer_nominativ(max(1, r['due'] - time.time()))}")
                else:
                    teile.append(f"{zeit_sprechen(z, jetzt)} {perspektive(r['text'])}".strip())
            return f"Du hast {len(rs)}: " + "; ".join(teile) + "."
        # --- Timer stellen
        if re.search(r"\b(timer|stoppuhr|countdown|eieruhr)\b", low) or re.match(r"^(stell|stelle)\b.*\bwecker\b.*\bin\b", low):
            sec = dauer_sekunden(low)
            if sec is None:
                if re.search(r"\b(stell|stelle|starte|setz|mach)\b", low):
                    return "Für wie lange soll der Timer laufen?"
                return None
            name = ""
            m = re.search(r"\b(?:für|fürs|zum)\s+(?:die |den |das )?(nudeln|eier|pizza|wäsche|tee|kuchen|ofen|essen|reis|kartoffeln|\w+)$", low)
            if m and not DAUER_RE.search(m.group(0)):
                name = m.group(1)
            self.add_reminder(time.time() + sec, name, "timer", sec)
            return "Timer " + (f"für {name.capitalize()} " if name else "") + f"auf {dauer_nominativ(sec)} gestellt."
        # --- Wecken
        m = re.match(r"^(?:bitte\s+)?(?:weck|wecke)\s+mich\s+(.+)$", low)
        if m:
            z = uhrzeit(m.group(1), jetzt)
            sec = dauer_sekunden(m.group(1)) if z is None else None
            if z is None and sec:
                z = jetzt + dt.timedelta(seconds=sec)
            if z is None:
                return "Wann soll ich dich wecken?"
            self.add_reminder(z.timestamp(), "Aufstehen", "wecker")
            return self.anrede(f"In Ordnung. Ich wecke dich {zeit_sprechen(z, jetzt)}")
        # --- Erinnerung
        m = re.match(r"^(?:bitte\s+)?(?:erinnere|erinner|erinnre)\s+mich\s+(.+)$", low)
        if not m:
            return None
        rest = t[len(t) - len(m.group(1)):]
        z = uhrzeit(rest, jetzt)
        if z is None:
            sec = dauer_sekunden(rest)
            if sec:
                z = jetzt + dt.timedelta(seconds=sec)
        if z is None:
            return "Wann soll ich dich erinnern?"
        # Inhalt: alles nach 'an'/'daran'/'dass', Zeitangaben entfernt
        inhalt = re.sub(r"\b(in|nach)\s+" + DAUER_RE.pattern + r"(\s+und\s+" + DAUER_RE.pattern + r")?", " ", rest, flags=re.I)
        inhalt = re.sub(r"\b(übermorgen|morgen früh|morgen|heute abend|heute|abends|nachmittags|morgens|früh)\b", " ",
                        inhalt, flags=re.I)
        inhalt = re.sub(r"\bum\s+(halb |viertel nach |viertel vor )?\S+(\s+uhr)?(\s+\d{1,2}\b)?", " ", inhalt, flags=re.I)
        dass = bool(re.search(r"\bdass\b", inhalt, re.I))
        inhalt = re.sub(r"^\s*[,]?\s*(daran|an|dass|das)\b[,]?\s*(dass\s+)?", "", inhalt.strip(), flags=re.I)
        inhalt = re.sub(r"\s+", " ", inhalt).strip(" ,.")
        inhalt = re.sub(r"^(daran|an|dass)\s+", "", inhalt, flags=re.I)
        r = self.add_reminder(z.timestamp(), inhalt or "deine Erinnerung", "erinnerung")
        r["dass"] = dass
        self.save_reminders()
        was = (f", dass {perspektive(inhalt)}" if dass else f" an {perspektive(inhalt)}") if inhalt else ""
        return self.anrede(f"Gern. Ich erinnere dich {zeit_sprechen(z, jetzt)}{was}")

    def reminder_speech(self, r: dict) -> str:
        u = f"{self.user}, " if self.user else ""
        if r["kind"] == "timer":
            name = f" für {r['text'].capitalize()}" if r.get("text") else ""
            return f"{u}dein Timer{name} über {dauer_nominativ(r.get('dauer') or 0)} ist abgelaufen."
        if r["kind"] == "wecker":
            n = dt.datetime.now()
            return f"Guten Morgen{', ' + self.user if self.user else ''}. Es ist {n.hour} Uhr {n.minute or ''}. Zeit zum Aufstehen.".replace(" .", ".")
        if r.get("dass"):
            return f"{u}ich soll dich daran erinnern, dass {perspektive(r['text'])}."
        return f"{u}ich soll dich erinnern: {perspektive(r['text'])}."

    async def reminder_loop(self) -> None:
        self.load_reminders()
        self.save_reminders()
        while True:
            await asyncio.sleep(1)
            now = time.time()
            due = [r for r in self.reminders if r["due"] <= now]
            if not due:
                continue
            self.reminders = [r for r in self.reminders if r["due"] > now]
            self.save_reminders()
            for r in due:
                speech = self.reminder_speech(r)
                _LOGGER.info("Fällig: %s", speech)
                try:
                    await asyncio.to_thread(
                        requests.post, f"{HA_URL}/events/gjarvis_reminder",
                        headers={"Authorization": f"Bearer {HA_TOKEN}"},
                        json={"text": r.get("text", ""), "art": r["kind"], "ansage": speech}, timeout=5)
                except Exception:  # noqa: BLE001
                    pass
                # Timer/Wecker zweimal ansagen, wenn er nicht unterbrochen wird
                await self.announce(speech, chime=True)
                if r["kind"] in ("timer", "wecker") and not self.interrupted:
                    await asyncio.sleep(6)
                    if not self.interrupted:
                        await self.announce(speech)
                self.interrupted = False

    # ------------------------------------------------------------------ Morgen-Briefing
    def wants_briefing(self, text: str) -> bool:
        t = text.lower().strip(" .!?")
        trig = self.o.get("briefing_triggers") or ["guten morgen", "briefing", "lagebericht", "was steht heute an"]
        return any(x.lower() in t for x in trig if x.strip())

    def calendar_today(self) -> List[str]:
        h = {"Authorization": f"Bearer {HA_TOKEN}"}
        wanted = [c.strip() for c in (self.o.get("briefing_calendars") or "").split(",") if c.strip()]
        cals = requests.get(f"{HA_URL}/calendars", headers=h, timeout=8).json()
        heute = dt.date.today()
        start = dt.datetime.combine(heute, dt.time(0, 0)).astimezone().isoformat()
        ende = dt.datetime.combine(heute, dt.time(23, 59)).astimezone().isoformat()
        out = []
        for c in cals:
            eid = c.get("entity_id", "")
            if wanted and eid not in wanted and c.get("name") not in wanted:
                continue
            try:
                evs = requests.get(f"{HA_URL}/calendars/{eid}", params={"start": start, "end": ende},
                                   headers=h, timeout=8).json()
            except Exception:  # noqa: BLE001
                continue
            for e in evs if isinstance(evs, list) else []:
                s = e.get("start", {})
                when = ""
                if s.get("dateTime"):
                    try:
                        z = dt.datetime.fromisoformat(s["dateTime"]).astimezone()
                        when = f"um {z.hour} Uhr" + (f" {z.minute}" if z.minute else "") + " "
                    except ValueError:
                        pass
                out.append((when or "ganztägig ", e.get("summary", "Termin")))
        out.sort()
        return [f"{w}{s}".strip() for w, s in out][:6]

    def news_headlines(self, n: int = 3) -> List[str]:
        r = requests.get("https://www.tagesschau.de/api2u/homepage/", timeout=8,
                         headers={"User-Agent": "GJarvis/1.2"})
        r.raise_for_status()
        titles = []
        for item in r.json().get("news", []):
            t = (item.get("title") or "").strip()
            if t and t not in titles:
                titles.append(t)
            if len(titles) >= n:
                break
        return titles

    def briefing(self, text: str = "") -> str:
        jetzt = dt.datetime.now()
        h = jetzt.hour
        gruss = "Guten Morgen" if 4 <= h < 11 else "Guten Tag" if h < 18 else "Guten Abend"
        if h < 4:
            gruss = "Noch wach"
        name = f", {self.user}" if self.user else ""
        teile = [f"{gruss}{name}. Es ist {h} Uhr {jetzt.minute or ''}, {WOCHENTAGE[jetzt.weekday()]}, "
                 f"der {jetzt.day}. {MONATE[jetzt.month - 1]}.".replace(" ,", ",")]
        try:
            teile.append(self.weather_answer("Wie wird das Wetter heute?"))
        except Exception as e:  # noqa: BLE001
            _LOGGER.info("Briefing ohne Wetter: %s", e)
        try:
            termine = self.calendar_today()
            if termine:
                teile.append(f"Heute im Kalender: {'; '.join(termine)}.")
            else:
                teile.append("Im Kalender steht heute nichts.")
        except Exception as e:  # noqa: BLE001
            _LOGGER.info("Briefing ohne Kalender: %s", e)
        heute = [r for r in self.reminders if dt.datetime.fromtimestamp(r["due"]).date() == jetzt.date()]
        if heute:
            teile.append(f"Außerdem habe ich {len(heute)} Erinnerung{'en' if len(heute) > 1 else ''} für heute notiert.")
        if self.o.get("briefing_flight") and self.o.get("flight_enabled"):
            try:
                teile.append(self.flight_answer("Wie ist das Flugwetter heute?"))
            except Exception as e:  # noqa: BLE001
                _LOGGER.info("Briefing ohne Flugwetter: %s", e)
        if self.o.get("briefing_news", True):
            try:
                news = self.news_headlines(3)
                if news:
                    teile.append("Die Schlagzeilen: " + ". ".join(n.rstrip(".") for n in news) + ".")
            except Exception as e:  # noqa: BLE001
                _LOGGER.info("Briefing ohne Nachrichten: %s", e)
        return " ".join(teile)

    # ------------------------------------------------------------------ Uhrzeit / Datum (sofort)
    def time_answer(self, text: str) -> Optional[str]:
        t = text.lower()
        n = dt.datetime.now()
        if re.search(r"wie (spät|spaet|spat) (ist|is|wär|war)|wieviel uhr|wie viel uhr|uhrzeit|wie spät", t):
            return f"Es ist {n.hour} Uhr {n.minute}." if n.minute else f"Es ist {n.hour} Uhr."
        if re.search(r"welche[rn]? (tag|datum|wochentag)|was für ein tag|der wievielte|welches datum|datum heute", t):
            return f"Heute ist {WOCHENTAGE[n.weekday()]}, der {n.day}. {MONATE[n.month - 1]} {n.year}."
        return None

    # ------------------------------------------------------------------ Schnelle Befehle (ohne KI)
    def quick_answer(self, text: str) -> Optional[Tuple[str, str]]:
        """(Antwort, Modus) oder None. Modus: 'ende' | 'frage' | 'ok'. Läuft vor allem anderen, ohne KI."""
        low = text.lower().strip(" .!?,")
        name = re.escape((self.o.get("assistant_name") or "jarvis").lower())
        low = re.sub(r"^(hey |hallo |hi |ok |okay )?(jarvis|" + name + r")[,]?\s*", "", low)
        if not low:
            return None
        words = low.split()
        if len(words) <= 3 and any(low == s or low.startswith(s + " ") for s in STOPPERS):
            self.pending = None
            return "", "ende"
        if len(words) <= 4 and any(low == c or low.startswith(c) for c in CLOSERS):
            self.pending = None
            if low.startswith(("danke", "vielen dank", "ok danke", "okay danke", "gut danke", "nein danke")):
                return self.anrede("Sehr gern"), "ende"
            if low.startswith(("tschüss", "bis später")):
                return self.anrede("Bis später"), "ende"
            return "", "ende"
        # Rückfrage von vorhin ergänzen ("Für wie lange?" -> "5 Minuten")
        pending, self.pending = getattr(self, "pending", None), None
        if pending and pending.startswith("app:") and hasattr(self, "app_followup"):
            try:
                r = self.app_followup(pending, text)
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("App-Rückfrage fehlgeschlagen: %s", e)
                r = None
            if r is not None:
                return r
        if pending == "timer" and dauer_sekunden(low):
            text = "Stell einen Timer auf " + text
        elif pending and pending.startswith("erinnerung:"):
            text = "Erinnere mich " + text + " an " + pending.split(":", 1)[1]
        for fn in (self.time_answer, self.memory_command, self.reminder_command):
            try:
                r = fn(text)
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Befehl nicht verarbeitet (%s): %s", fn.__name__, e)
                r = None
            if r is not None:
                if r.startswith("Für wie lange"):
                    self.pending = "timer"
                elif r.startswith("Wann soll ich dich erinnern"):
                    m = re.match(r"^(?:bitte\s+)?erinner\w*\s+mich\s+(?:an|daran)?\s*(?:dass\s+)?(.*)$", text.strip(" .!?"), re.I)
                    self.pending = "erinnerung:" + (m.group(1) if m else "")
                return r, ("frage" if r.endswith("?") else "ok")
        if self.wants_briefing(text):
            return self.briefing(text), "ok"
        return None
