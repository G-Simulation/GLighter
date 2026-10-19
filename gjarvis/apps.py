"""GJarvis – Home-Assistant-Apps per Sprache: Mealie (Rezepte, Essensplan, Rezept aus dem Internet holen)
und Einkaufs-/To-do-Listen aller Apps (Mealie, Bring!, Grocy, Todoist, HA-Einkaufsliste …).

Hinzufügen ("Setz Milch auf die Einkaufsliste") erledigt Home Assistants eigener Agent für jede To-do-Liste.
Hier kommt dazu, was der eingebaute Agent nicht kann: vorlesen, Rezepte suchen, kochen Schritt für Schritt.
"""
from __future__ import annotations

import datetime as dt
import logging
import re
import time
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests

_LOGGER = logging.getLogger("gjarvis")

HA_URL = ""
HA_TOKEN = ""

MEAL_TYPES = {
    "breakfast": "Frühstück", "lunch": "Mittagessen", "dinner": "Abendessen", "side": "Beilage",
    "dessert": "Nachtisch", "drink": "Getränk", "snack": "Snack",
}
MEAL_WORDS = [
    ("frühstück", "breakfast"), ("mittag", "lunch"), ("abend", "dinner"), ("beilage", "side"),
    ("nachtisch", "dessert"), ("dessert", "dessert"), ("snack", "snack"),
]
RECIPE_SITES = [
    "chefkoch.de", "lecker.de", "kitchenstories.com", "eatsmarter.de", "essen-und-trinken.de", "kuechengoetter.de",
    "einfachbacken.de", "springlane.de", "gutekueche.de", "hellofresh.de", "rezeptwelt.de", "lidl-kochen.de",
    "kochbar.de", "allrecipes.com", "bbcgoodfood.com",
]
BAD_SITES = ("youtube.", "pinterest.", "instagram.", "facebook.", "tiktok.", "amazon.", "wikipedia.")
YES = ("ja", "jo", "jep", "gern", "gerne", "bitte", "ok", "okay", "klar", "mach", "los", "weiter", "nächst",
       "und dann", "fertig", "erledigt", "genau", "sicher")
NO = ("nein", "nee", "nö", "lass", "nicht", "stopp", "stop", "danke", "das reicht", "reicht", "abbrechen")


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"[*_#`]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", s)


def _num(q) -> str:
    try:
        q = float(q)
    except (TypeError, ValueError):
        return ""
    if q <= 0:
        return ""
    for v, w in ((0.25, "ein Viertel"), (0.5, "einen halben"), (0.75, "drei Viertel"), (1.5, "anderthalb")):
        if abs(q - v) < 0.01:
            return w
    return str(int(q)) if abs(q - round(q)) < 0.01 else str(round(q, 1)).replace(".", ",")


class AppFeatures:
    """Mixin für GJarvis (braucht self.o, self.anrede, self.parse_day, self.search_web, self.research)."""

    # ----------------------------- Home Assistant -------------------------- #
    def _ha_service(self, domain: str, service: str, data: dict, timeout: int = 30) -> dict:
        r = requests.post(
            f"{HA_URL}/services/{domain}/{service}?return_response",
            headers={"Authorization": f"Bearer {HA_TOKEN}"}, json=data, timeout=timeout,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"{domain}.{service}: HTTP {r.status_code} {r.text[:200]}")
        return r.json().get("service_response") or {}

    def _ha_template(self, tpl: str) -> str:
        r = requests.post(f"{HA_URL}/template", headers={"Authorization": f"Bearer {HA_TOKEN}"},
                          json={"template": tpl}, timeout=10)
        r.raise_for_status()
        return r.text.strip()

    def mealie_entry(self) -> str:
        """config_entry_id der Mealie-Integration ('' = Mealie nicht eingerichtet). 10 Minuten zwischengespeichert."""
        fixed = (self.o.get("mealie_config_entry_id") or "").strip()
        if fixed:
            return fixed
        cache = self.__dict__.setdefault("_mealie_cache", [None, ""])
        if cache[0] is not None and time.monotonic() - cache[0] < 600:
            return cache[1]
        try:
            eid = self._ha_template(
                "{% set l = integration_entities('mealie') %}{{ config_entry_id(l[0]) if l else '' }}")
            eid = "" if eid in ("None", "none") else eid
        except Exception as e:  # noqa: BLE001
            _LOGGER.info("Mealie nicht gefunden: %s", e)
            eid = ""
        cache[:] = [time.monotonic(), eid]
        return eid

    # ----------------------------- Erkennung ------------------------------- #
    def apps_on(self) -> bool:
        return bool(self.o.get("apps_enabled", True))

    @staticmethod
    def _meal_type(t: str) -> Optional[str]:
        for w, typ in MEAL_WORDS:
            if w in t:
                return typ
        return None

    @staticmethod
    def _dish(text: str) -> str:
        """'Such mir im Internet ein Rezept für Kürbissuppe' -> 'Kürbissuppe'."""
        t = text.strip(" .!?")
        m = re.search(r"rezept\w*\s+(?:für|von|zu|mit)\s+(?:eine[nmrs]?\s+|ein\s+|einen\s+|die\s+|den\s+|das\s+)?(.+)",
                      t, re.I)
        if not m:
            m = re.search(r"(?:wie\s+(?:koche|mache|backe|brate|bereite)\s+ich|zutaten\s+(?:für|von))\s+"
                          r"(?:eine[nmrs]?\s+|ein\s+|die\s+|den\s+|das\s+)?(.+)", t, re.I)
        if not m:
            m = re.search(r"(.+?)\s+rezept", t, re.I)
        dish = m.group(1) if m else ""
        dish = re.sub(r"\b(im\s+(internet|netz|web)|online|bei\s+chefkoch|auf\s+chefkoch|bitte|mal|schnell|"
                      r"such\w*|find\w*|hol\w*|mir|uns|ein|eine|einen|rezept\w*|zu|zubereitet|zubereiten|"
                      r"heraus|raus|und\s+speicher\w*.*|in\s+mealie.*)\b", " ", dish, flags=re.I)
        dish = re.sub(r"^(hey\s+)?jarvis\W*", "", dish.strip(), flags=re.I)
        return re.sub(r"\s+", " ", dish).strip(" ,.")

    def apps_answer(self, text: str) -> Optional[Tuple[str, bool]]:
        """Läuft in GJarvis.answer() vor dem HA-Agenten. None = nicht zuständig."""
        if not self.apps_on():
            return None
        redo = self.__dict__.pop("_app_redo", None)
        if redo:
            return self.recipe_from_web(redo)
        t = text.lower()
        try:
            if "rezept" in t and re.search(r"\b(internet|netz|online|web|chefkoch|google)\b", t):
                return self.recipe_from_web(self._dish(text))
            todo = self.todo_command(text)
            if todo is not None:
                return todo, False
            if (re.search(r"(einkaufsliste|einkaufszettel|to-?do|aufgabe|liste|zu tun)", t) and re.search(
                    r"(was steht|was ist|was muss|was brauch|lies|vorlesen|zeig|was fehlt|was habe? ich|was gibt)", t)) \
                    or re.search(r"was (muss|sollte|wollte) ich (heute |noch |heute noch )*(erledigen|machen|tun)", t):
                return self.read_todo(text), False
            if not self.mealie_entry():
                return None
            if re.search(r"(schlag\w* mir (ein|was|etwas)|was soll ich .*kochen|was könnte ich .*kochen|"
                         r"zufällig\w* (rezept|gericht|essen)|überrasch)", t):
                return self.random_meal(text), False
            if re.search(r"(speiseplan|essensplan|wochenplan|was gibt('?s| es)\b.*(essen|mittag|abend|frühstück)|"
                         r"was (essen|kochen) wir|was gibt('?s| es) (heute|morgen|übermorgen|am)\b.*\b(essen|zu essen))", t):
                return self.mealplan(text), False
            if re.search(r"(rezept\w* (für|von|zu)|wie (koche|mache|backe|brate|bereite) ich|zutaten (für|von))", t):
                return self.recipe_local(self._dish(text))
        except Exception as e:  # noqa: BLE001
            _LOGGER.warning("App-Befehl fehlgeschlagen: %s", e)
            return self.anrede("Das hat mit der App leider nicht geklappt"), False
        return None

    # ----------------------------- Listen ---------------------------------- #
    def todo_lists(self) -> List[Tuple[str, str]]:
        r = requests.get(f"{HA_URL}/states", headers={"Authorization": f"Bearer {HA_TOKEN}"}, timeout=15)
        r.raise_for_status()
        return [(s["entity_id"], s.get("attributes", {}).get("friendly_name") or s["entity_id"])
                for s in r.json() if s["entity_id"].startswith("todo.")]

    TODO_WORDS = r"(to-?do|aufgabe|zu tun|zutun|erledigen|task)"

    def pick_list(self, text: str, lists: List[Tuple[str, str]], prefer_todo: bool = False) -> Optional[Tuple[str, str]]:
        """Welche Liste ist gemeint? Name genannt > Einkauf/Aufgaben-Wort > Standard."""
        t = text.lower()
        for eid, name in lists:  # ganzer Name ("zu tun", "Baumarkt")
            n = re.sub(r"^mealie\s*", "", name.lower()).strip()
            if n and re.search(r"\b" + re.escape(n) + r"\b", t):
                return eid, name
        for eid, name in lists:  # einzelnes Wort aus dem Namen
            words = [w for w in re.split(r"\W+", name.lower()) if len(w) > 3 and w not in ("liste", "mealie")]
            if any(w in t for w in words):
                return eid, name
        if re.search(r"(einkauf|zettel|kaufen|besorgen)", t):
            hit = next(((e, n) for e, n in lists if re.search(r"(einkauf|shopping|bring|grocy|mealie)",
                                                                 (e.split(".", 1)[-1] + " " + n).lower())),
                       None)
            if hit:
                return hit
        if prefer_todo or re.search(self.TODO_WORDS, t):
            hit = next(((e, n) for e, n in lists if re.search(r"(tun|todo|to_do|aufgabe|task|erledig)",
                                                                 (e.split(".", 1)[-1] + " " + n).lower())),
                       None)
            if hit:
                return hit
        return None

    def list_items(self, eid: str) -> List[str]:
        resp = self._ha_service("todo", "get_items", {"entity_id": eid, "status": "needs_action"})
        return [i.get("summary", "") for i in (resp.get(eid) or {}).get("items", []) if i.get("summary")]

    @staticmethod
    def _list_name(name: str) -> str:
        return re.sub(r"^mealie\s*", "", name, flags=re.I) or "Liste"

    def read_todo(self, text: str) -> str:
        lists = self.todo_lists()
        if not lists:
            return self.anrede("Ich habe in Home Assistant keine Liste gefunden")
        pick = self.pick_list(text, lists) or lists[0]
        items = self.list_items(pick[0])
        name = self._list_name(pick[1])
        if not items:
            return f"Auf der Liste {name} steht gerade nichts."
        more = f" und {len(items) - 12} weitere" if len(items) > 12 else ""
        shown = items[:12]
        joined = ", ".join(shown[:-1]) + f" und {shown[-1]}" if len(shown) > 1 else shown[0]
        anzahl = "eine Sache" if len(items) == 1 else f"{len(items)} Sachen"
        return f"Auf der Liste {name} {'steht' if len(items) == 1 else 'stehen'} {anzahl}: {joined}{more}."

    @staticmethod
    def _norm_words(s: str) -> set:
        return {w for w in re.split(r"\W+", s.lower()) if len(w) > 2 and w not in (
            "der", "die", "das", "den", "dem", "ein", "eine", "einen", "und", "mit", "von", "auf", "bitte")}

    def find_item(self, what: str, text: str, lists: List[Tuple[str, str]]) -> Optional[Tuple[str, str, str]]:
        """Eintrag in der genannten Liste (oder allen Listen) suchen -> (entity_id, Listenname, Eintrag)."""
        named = self.pick_list(text, lists)
        want = self._norm_words(what)
        if not want:
            return None
        best, score = None, 0.0
        for eid, name in ([named] if named else lists):
            for item in self.list_items(eid):
                have = self._norm_words(item)
                hit = sum(1 for w in want if any(w in h or h in w for h in have))
                sc = hit / len(want)
                if item.lower().strip() == what.lower().strip():
                    sc = 2.0
                if sc > score:
                    best, score = (eid, name, item), sc
        return best if score >= 0.5 else None

    def todo_command(self, text: str) -> Optional[str]:
        """Abhaken, löschen, Aufgaben eintragen – was Home Assistants eigener Agent auf Deutsch nicht sicher kann."""
        t = text.strip(" .!?")
        low = t.lower()
        m = (re.search(r"^(?:bitte\s+)?(?:hak\w*|streich\w*|markier\w*)\s+(.+?)\s+(?:ab|durch|als erledigt)\b", low)
             or re.search(r"^(?:bitte\s+)?(.+?)\s+(?:ist|sind|habe ich|hab ich|wurde|wurden)\s+"
                          r"(?:jetzt\s+|schon\s+)?(?:erledigt|gemacht|fertig|gekauft|abgehakt|besorgt)\b", low))
        if m:
            lists = self.todo_lists()
            what = re.sub(r"\s+(?:auf|von|in)\s+(?:der|dem|meiner)?\s*\S*\s*liste.*$", "", m.group(1))
            found = self.find_item(what, low, lists)
            if not found:
                return self.anrede(f"Ich habe {what[:1].upper() + what[1:]} auf keiner Liste gefunden")
            eid, name, item = found
            self._ha_service("todo", "update_item", {"entity_id": eid, "item": item, "status": "completed"})
            return f"Abgehakt: {item}."
        m = re.search(r"^(?:bitte\s+)?(?:lösch\w*|entfern\w*|nimm)\s+(.+?)\s+(?:von|aus)\s+(?:der|dem|meiner|meinem)?\s*(.+?)"
                      r"(?:\s+(?:runter|raus|weg))?$", low)
        if m and re.search(r"liste|" + self.TODO_WORDS, m.group(2)):
            lists = self.todo_lists()
            found = self.find_item(m.group(1), low, lists)
            if not found:
                return self.anrede(f"Ich habe {m.group(1)} auf keiner Liste gefunden")
            eid, name, item = found
            self._ha_service("todo", "remove_item", {"entity_id": eid, "item": item})
            return f"{item} ist von der Liste {self._list_name(name)} gelöscht."
        m = (re.search(r"^(?:bitte\s+)?(?:setz\w*|schreib\w*|füg\w*|pack\w*|trag\w*|nimm)\s+(.+?)\s+(?:auf|zu|in|zur|unter)\s+"
                       r"(?:die |der |den |meine |meiner |meinen )?(?:to-?do|aufgaben|zu tun|zutun)\w*", low)
             or re.search(r"^(?:neue|neuer|eine neue)\s+(?:aufgabe|to-?do|eintrag)\s*:?\s*(.+)$", low))
        if m:
            lists = self.todo_lists()
            pick = self.pick_list(low, lists, prefer_todo=True)
            if not pick:
                return self.anrede("Ich habe keine Aufgabenliste gefunden")
            item = re.sub(r"\s+(?:hinzu|ein|drauf|dazu)$", "", m.group(1)).strip()
            item = item[:1].upper() + item[1:]
            self._ha_service("todo", "add_item", {"entity_id": pick[0], "item": item})
            return f"Notiert: {item} steht jetzt auf {self._list_name(pick[1])}."
        return None

    # ----------------------------- Mealie: Essensplan ---------------------- #
    def mealplan(self, text: str) -> str:
        t = text.lower()
        week = bool(re.search(r"(woche|wochenplan)", t))
        _, label, day = self.parse_day(text)
        end = day + dt.timedelta(days=6) if week else day
        resp = self._ha_service("mealie", "get_mealplan", {
            "config_entry_id": self.mealie_entry(), "start_date": day.isoformat(), "end_date": end.isoformat()})
        want = self._meal_type(t)
        rows = []
        for m in resp.get("mealplan", []):
            typ = m.get("entry_type") or ""
            if want and typ != want:
                continue
            dish = ((m.get("recipe") or {}).get("name") or m.get("title") or "").strip()
            if dish:
                rows.append((m.get("mealplan_date") or "", typ, dish))
        if not rows:
            wann = "diese Woche" if week else label.lower()
            return self.anrede(f"Für {wann} ist noch nichts geplant. Soll ich dir etwas vorschlagen? "
                               "Sag einfach: Schlag mir ein Gericht vor")
        order = list(MEAL_TYPES)
        rows.sort(key=lambda r: (r[0], order.index(r[1]) if r[1] in order else 9))
        if week:
            parts = []
            for d, typ, dish in rows[:10]:
                try:
                    wd = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][
                        dt.date.fromisoformat(str(d)[:10]).weekday()]
                except ValueError:
                    wd = ""
                parts.append(f"{wd} {dish}".strip())
            return "Der Plan für die Woche: " + "; ".join(parts) + "."
        parts = [f"zum {MEAL_TYPES.get(typ, typ)} {dish}" if typ in MEAL_TYPES else dish for _, typ, dish in rows]
        return f"{label} gibt es " + ", ".join(parts) + "."

    def random_meal(self, text: str) -> str:
        t = text.lower()
        _, label, day = self.parse_day(text)
        typ = self._meal_type(t) or "dinner"
        resp = self._ha_service("mealie", "set_random_mealplan", {
            "config_entry_id": self.mealie_entry(), "date": day.isoformat(), "entry_type": typ})
        dish = ((resp.get("mealplan") or {}).get("recipe") or {}).get("name") or ""
        if not dish:
            return self.anrede("Ich habe leider kein passendes Rezept gefunden")
        return (f"Wie wäre es mit {dish}? Ich habe es für {label.lower()} zum {MEAL_TYPES[typ]} eingeplant. "
                f"Sag „Rezept für {dish}“, dann lese ich dir die Zutaten vor.")

    # ----------------------------- Mealie: Rezepte ------------------------- #
    def recipe_local(self, dish: str) -> Optional[Tuple[str, bool]]:
        if not dish:
            return "Für welches Gericht?", True
        resp = self._ha_service("mealie", "get_recipes", {
            "config_entry_id": self.mealie_entry(), "search_terms": dish, "result_limit": 3})
        items = (resp.get("recipes") or {}).get("items", [])
        if not items:
            self.pending = f"app:netz:{dish}"
            self.app_ts = time.time()
            return (f"In deinen Rezepten habe ich nichts zu {dish} gefunden. "
                    "Soll ich im Internet eins suchen und in Mealie speichern?"), True
        r = items[0]
        return self.recipe_intro(r.get("slug") or r.get("recipe_id"), r.get("name") or dish)

    def recipe_intro(self, slug: str, name: str, quelle: str = "") -> Tuple[str, bool]:
        rec = self.get_recipe(slug)
        n_z, n_s = len(rec.get("ingredients") or []), len(rec.get("instructions") or [])
        zeit = _clean(rec.get("total_time") or "")
        info = f" Das dauert etwa {zeit}." if zeit and re.search(r"\d", zeit) else ""
        self.pending = f"app:zutaten:{slug}"
        self.app_ts = time.time()
        von = f" von {quelle}" if quelle else ""
        return (f"{name}{von}: {n_z} Zutaten, {n_s} Schritte.{info} Soll ich dir die Zutaten vorlesen?"), True

    def get_recipe(self, slug: str) -> dict:
        cache = self.__dict__.setdefault("_recipe_cache", {})
        if slug not in cache:
            resp = self._ha_service("mealie", "get_recipe", {"config_entry_id": self.mealie_entry(), "recipe_id": slug})
            cache.clear()
            cache[slug] = resp.get("recipe") or {}
        return cache[slug]

    @staticmethod
    def ingredient_text(i: dict) -> str:
        if i.get("display"):
            return _clean(i["display"])
        parts = [_num(i.get("quantity")), ((i.get("unit") or {}).get("name") or ""),
                 ((i.get("food") or {}).get("name") or ""), i.get("note") or ""]
        s = _clean(" ".join(p for p in parts if p))
        return s or _clean(i.get("original_text") or "")

    def recipe_from_web(self, dish: str) -> Tuple[str, bool]:
        if not dish:
            return "Welches Rezept soll ich suchen?", True
        hits = self.search_web(f"{dish} Rezept", n=10)
        urls = [h.get("source", "") for h in hits if h.get("source", "").startswith("http")]
        urls = [u for u in urls if not any(b in u for b in BAD_SITES)]
        urls.sort(key=lambda u: 0 if any(s in u for s in RECIPE_SITES) else 1)
        if not urls:
            return self.anrede(f"Ich habe im Internet kein Rezept für {dish} gefunden"), False
        if not self.mealie_entry():
            # Ohne Mealie: Rezept kurz zusammenfassen
            return self.research(f"Rezept für {dish}: Zutaten und Zubereitung kurz", f"{dish} Rezept Zutaten"), False
        for url in urls[:3]:
            try:
                resp = self._ha_service("mealie", "import_recipe", {
                    "config_entry_id": self.mealie_entry(), "url": url}, timeout=60)
            except Exception as e:  # noqa: BLE001
                _LOGGER.info("Import von %s fehlgeschlagen: %s", url, e)
                continue
            rec = resp.get("recipe") or {}
            slug, name = rec.get("slug") or rec.get("recipe_id"), rec.get("name") or dish
            if not slug:
                continue
            site = urlparse(url).netloc.replace("www.", "")
            _LOGGER.info("Rezept importiert: %s (%s)", name, url)
            speech, cont = self.recipe_intro(slug, name, site)
            return "Gefunden und in Mealie gespeichert. " + speech, cont
        return self.anrede(f"Ich habe Rezepte für {dish} gefunden, aber Mealie konnte keins übernehmen"), False

    # ----------------------------- Rückfragen / Kochmodus ------------------ #
    def app_followup(self, pending: str, text: str) -> Optional[Tuple[str, str]]:
        """Antwort auf eine offene App-Rückfrage – aus quick_answer(). (Antwort, Modus) oder None."""
        if time.time() - getattr(self, "app_ts", 0) > 1800:  # Rückfrage älter als 30 Minuten -> vergessen
            return None
        low = text.lower().strip(" .!?,")
        yes = any(low == y or low.startswith(y) for y in YES) or "vorles" in low or "schritt" in low
        no = not yes and any(low == n or low.startswith(n) for n in NO)
        parts = pending.split(":", 3)
        kind = parts[1] if len(parts) > 1 else ""
        if no:
            return (self.anrede("Gut") if kind == "netz" else self.anrede("Guten Appetit")), "ende"
        if kind == "netz":
            if not yes:
                return None
            self.__dict__["_app_redo"] = parts[2]  # dauert länger -> in answer() mit Zwischenmeldungen
            return None
        slug = parts[2] if len(parts) > 2 else ""
        rec = self.get_recipe(slug) if slug else {}
        if kind == "zutaten":
            if not yes:
                return None
            ings = [self.ingredient_text(i) for i in rec.get("ingredients") or []]
            ings = [i for i in ings if i]
            self.pending = f"app:schritte:{slug}:0"
            self.app_ts = time.time()
            if not ings:
                return "Zu dem Rezept sind keine Zutaten hinterlegt. Soll ich die Schritte vorlesen?", "frage"
            return "Du brauchst: " + "; ".join(ings[:20]) + ". Soll ich die Schritte vorlesen?", "frage"
        if kind == "schritte":
            steps = [_clean(s.get("text", "")) for s in rec.get("instructions") or []]
            steps = [s for s in steps if s]
            idx = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
            if re.search(r"(wiederhol|nochmal|noch mal|was war)", low):
                idx = max(0, idx - 1)
            elif re.search(r"(zurück|vorher)", low):
                idx = max(0, idx - 2)
            elif not yes:
                return None
            if idx >= len(steps):
                return "Das war der letzte Schritt. Guten Appetit!", "ende"
            last = idx == len(steps) - 1
            self.pending = None if last else f"app:schritte:{slug}:{idx + 1}"
            self.app_ts = time.time()
            ende = " Das war der letzte Schritt. Guten Appetit!" if last else " Sag „weiter“, wenn du so weit bist."
            return f"Schritt {idx + 1}: {steps[idx]}{ende}", ("ende" if last else "frage")
        return None
