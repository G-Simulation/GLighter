"""GReport: Text aus Dokumenten lesen (offline) und Zeitangaben darin finden.

- Text: txt und eml direkt, docx/odt über zipfile/XML (mit Schutz vor ZIP-Bomben und XML-Entitäten),
  PDF über pdftotext (poppler-utils), gescannte Seiten und Bilder über tesseract (Deutsch und Englisch).
  Fehlt ein Programm, kommt ein Fehlercode zurück – nichts stürzt ab. Das Original wird nie verändert.
- Zeitangaben: deutsche und englische Schreibweisen (12.03.2025, 12.3., 2025-03-12, „12. März“, Wochentag + Datum,
  „am Montag“, „gegen 23 Uhr“, „um 23:15“, „23:15–23:40“, „von 22 bis 1 Uhr“, „gestern Nacht“ …). Relative Angaben
  beziehen sich auf das Datum des Dokuments. Jeder Treffer wird als genau, ungefähr oder unklar eingestuft.
Nur Standardbibliothek; externe Programme nur, wenn vorhanden.
"""
import datetime as dt
import email
import email.policy
import email.utils
import html
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

KINDS = {".txt": "txt", ".text": "txt", ".log": "txt", ".pdf": "pdf", ".jpg": "jpg", ".jpeg": "jpg", ".png": "png", ".heic": "heic", ".heif": "heic",
         ".docx": "docx", ".odt": "odt", ".eml": "eml"}
MIME = {"txt": "text/plain; charset=utf-8", "pdf": "application/pdf", "jpg": "image/jpeg", "png": "image/png", "heic": "image/heic",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "odt": "application/vnd.oasis.opendocument.text",
        "eml": "message/rfc822"}
ZIP_MAX_ENTRIES = 2000
ZIP_MAX_TOTAL = 300 * 1024 * 1024            # entpackt höchstens so viel (alle Einträge zusammen)
ZIP_MAX_XML = 40 * 1024 * 1024               # die eine XML-Datei mit dem Text
ZIP_MAX_RATIO = 200                          # stärker gepackt = verdächtig (ZIP-Bombe)
OCR_MAX_PAGES = 40
TOOL_TIMEOUT = 180
TEXT_MAX = 2_000_000                         # so viele Zeichen erkannter Text höchstens


class ExtractError(Exception):
    """code: kind (Dateiart nicht unterstützt), tool (Programm fehlt), zip, xml, format, empty, timeout."""

    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code, self.detail = code, detail


def kind_of(name):
    return KINDS.get(os.path.splitext(str(name or ""))[1].lower())


def sniff_ok(kind, head):
    """Passt der Anfang der Datei zur Endung? (Schutz vor umbenannten Dateien)"""
    if kind == "pdf":
        return head[:1024].lstrip().startswith(b"%PDF")
    if kind == "png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if kind == "jpg":
        return head.startswith(b"\xff\xd8\xff")
    if kind == "heic":
        return head[4:8] == b"ftyp" and head[8:12] in (b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"heim", b"heis", b"avif")
    if kind in ("docx", "odt"):
        return head.startswith(b"PK\x03\x04")
    if kind in ("txt", "eml"):
        return b"\x00" not in head[:8192] or head.startswith((b"\xff\xfe", b"\xfe\xff"))
    return False


# ---------------------------------------------------------------- Programme
_TOOLS = {}


def _which(n):
    if n not in _TOOLS:
        _TOOLS[n] = shutil.which(n)
    return _TOOLS[n]


def ocr_langs():
    """Vorhandene Sprachdaten von tesseract (deu, eng …)."""
    if "_langs" not in _TOOLS:
        langs = []
        if _which("tesseract"):
            try:
                r = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)
                langs = [x.strip() for x in (r.stdout + "\n" + r.stderr).splitlines()[1:] if re.fullmatch(r"[a-z_]{3,10}", x.strip())]
            except (OSError, subprocess.SubprocessError):
                langs = []
        _TOOLS["_langs"] = langs
    return _TOOLS["_langs"]


def tools():
    lg = ocr_langs()
    return {"pdftotext": bool(_which("pdftotext")), "pdftoppm": bool(_which("pdftoppm")), "tesseract": bool(_which("tesseract")),
            "heic": bool(_which("heif-convert") or _which("heif-dec")), "langs": [x for x in lg if x in ("deu", "eng")]}


def _run(cmd, timeout=TOOL_TIMEOUT, text=True):
    env = dict(os.environ, OMP_THREAD_LIMIT="1", LC_ALL="C.UTF-8")
    try:
        r = subprocess.run(cmd, capture_output=True, text=text, timeout=timeout, stdin=subprocess.DEVNULL, env=env)
    except subprocess.TimeoutExpired:
        raise ExtractError("timeout", cmd[0])
    except OSError as e:
        raise ExtractError("tool", f"{cmd[0]}: {e}")
    return r


def _ocr(img):
    if not _which("tesseract"):
        raise ExtractError("tool", "tesseract")
    lg = [x for x in ("deu", "eng") if x in ocr_langs()]
    cmd = ["tesseract", img, "stdout"] + (["-l", "+".join(lg)] if lg else [])
    r = _run(cmd)
    if r.returncode != 0:
        raise ExtractError("format", (r.stderr or "")[:200])
    return r.stdout


# ---------------------------------------------------------------- Text lesen
def _decode(b):
    if b.startswith((b"\xff\xfe", b"\xfe\xff")):
        return b.decode("utf-16", errors="replace")
    try:
        return b.decode("utf-8-sig")
    except UnicodeDecodeError:
        return b.decode("cp1252", errors="replace")


def _zip_member(path, member):
    """Eine Datei aus docx/odt lesen – mit Grenzen gegen ZIP-Bomben."""
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            if len(infos) > ZIP_MAX_ENTRIES or sum(i.file_size for i in infos) > ZIP_MAX_TOTAL:
                raise ExtractError("zip", "too many or too large entries")
            try:
                i = z.getinfo(member)
            except KeyError:
                raise ExtractError("format", member)
            if i.file_size > ZIP_MAX_XML or (i.file_size > 1024 * 1024 and i.file_size > ZIP_MAX_RATIO * max(1, i.compress_size)):
                raise ExtractError("zip", "suspicious compression")
            with z.open(i) as f:
                data = f.read(ZIP_MAX_XML + 1)
    except zipfile.BadZipFile:
        raise ExtractError("format", "zip")
    if len(data) > ZIP_MAX_XML:
        raise ExtractError("zip", "too large")
    if re.search(rb"<!(DOCTYPE|ENTITY)", data, re.I):        # keine eigenen Entitäten (Billion Laughs, externe Dateien)
        raise ExtractError("xml", "doctype")
    try:
        return ET.fromstring(data)
    except ET.ParseError as e:
        raise ExtractError("format", str(e)[:120])


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _docx(path):
    root = _zip_member(path, "word/document.xml")
    pages, cur = [], []
    for p in root.iter(W + "p"):
        buf = []
        for e in p.iter():
            if e.tag == W + "t":
                buf.append(e.text or "")
            elif e.tag == W + "tab":
                buf.append("\t")
            elif e.tag in (W + "br", W + "cr"):
                if e.get(W + "type") == "page":
                    cur.append("".join(buf)); buf = []; pages.append("\n".join(cur)); cur = []
                else:
                    buf.append("\n")
            elif e.tag == W + "lastRenderedPageBreak" and (buf or cur):
                cur.append("".join(buf)); buf = []; pages.append("\n".join(cur)); cur = []
        cur.append("".join(buf))
    pages.append("\n".join(cur))
    return [x for x in pages] or [""]


TX = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"


def _odt_text(e):
    out = [e.text or ""]
    for c in e:
        if c.tag == TX + "s":
            out.append(" " * int(c.get(TX + "c") or 1))
        elif c.tag == TX + "tab":
            out.append("\t")
        elif c.tag == TX + "line-break":
            out.append("\n")
        elif c.tag not in (TX + "note", "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}annotation"):
            out.append(_odt_text(c))
        out.append(c.tail or "")
    return "".join(out)


def _odt(path):
    root = _zip_member(path, "content.xml")
    lines = [_odt_text(e) for e in root.iter() if e.tag in (TX + "p", TX + "h")]
    return ["\n".join(lines)]


def _strip_html(s):
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", s)
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


def _eml(path):
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)
    date = None
    try:
        if msg["Date"]:
            date = email.utils.parsedate_to_datetime(str(msg["Date"])).astimezone()
    except (TypeError, ValueError, IndexError):
        date = None
    body = ""
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
        if part is not None:
            body = part.get_content()
            if part.get_content_type() == "text/html":
                body = _strip_html(body)
    except (KeyError, LookupError, UnicodeError, AttributeError):
        body = ""
    head = []
    for k, label in (("From", "Von"), ("To", "An"), ("Subject", "Betreff")):
        if msg[k]:
            head.append(f"{label}: {msg[k]}")
    return ["\n".join(head + [""] + str(body or "").splitlines())], date


def _pdf_date(path):
    if not _which("pdfinfo"):
        return None
    try:
        r = _run(["pdfinfo", "-isodates", path], timeout=30)
    except ExtractError:
        return None
    m = re.search(r"^CreationDate:\s*(\S+)", r.stdout or "", re.M)
    if not m:
        return None
    try:
        d = dt.datetime.fromisoformat(m[1].replace("Z", "+00:00"))
        return d if d.tzinfo else d.astimezone()
    except ValueError:
        return None


def _pdf(path):
    if not _which("pdftotext"):
        raise ExtractError("tool", "pdftotext")
    r = _run(["pdftotext", "-layout", "-enc", "UTF-8", path, "-"])
    if r.returncode != 0:
        raise ExtractError("format", (r.stderr or "")[:200])
    pages = (r.stdout or "").split("\f")
    if len(pages) > 1 and not pages[-1].strip():
        pages.pop()
    method = "pdf"
    weak = [i for i, p in enumerate(pages) if len(re.sub(r"\s", "", p)) < 20]
    if weak and _which("tesseract") and _which("pdftoppm"):           # gescannte Seiten: Texterkennung
        with tempfile.TemporaryDirectory(prefix="greport_ocr_") as td:
            for i in weak[:OCR_MAX_PAGES]:
                base = os.path.join(td, f"s{i + 1}")
                rr = _run(["pdftoppm", "-r", "200", "-gray", "-png", "-singlefile", "-f", str(i + 1), "-l", str(i + 1), path, base])
                if rr.returncode == 0 and os.path.exists(base + ".png"):
                    pages[i] = _ocr(base + ".png")
                    method = "pdf+ocr" if len(weak) < len(pages) else "ocr"
    return pages or [""], method


def _image(path, kind):
    if kind == "heic":
        conv = _which("heif-convert") or _which("heif-dec")
        if not conv:
            raise ExtractError("tool", "heif-convert")
        with tempfile.TemporaryDirectory(prefix="greport_ocr_") as td:
            out = os.path.join(td, "bild.png")
            cmd = [conv, path, out] if os.path.basename(conv) == "heif-convert" else [conv, "-o", out, path]
            r = _run(cmd)
            if r.returncode != 0 or not os.path.exists(out):
                raise ExtractError("format", (r.stderr or "")[:200])
            return [_ocr(out)]
    return [_ocr(path)]


def extract(path, kind):
    """→ {"pages": [Text je Seite], "method": …, "date": Datum des Dokuments (datetime|None)}. Liest nur, schreibt nichts ans Original."""
    date = None
    if kind == "txt":
        with open(path, "rb") as f:
            pages, method = _decode(f.read(TEXT_MAX * 2)).replace("\r\n", "\n").replace("\r", "\n").split("\f"), "text"
    elif kind == "eml":
        pages, date = _eml(path); method = "eml"
    elif kind == "docx":
        pages, method = _docx(path), "docx"
    elif kind == "odt":
        pages, method = _odt(path), "odt"
    elif kind == "pdf":
        pages, method = _pdf(path); date = _pdf_date(path)
    elif kind in ("jpg", "png", "heic"):
        pages, method = _image(path, kind), "ocr"
    else:
        raise ExtractError("kind", str(kind))
    pages = [re.sub(r"[\x00-\x08\x0b\x0e-\x1f]", "", p) for p in pages]
    total = 0
    for i, p in enumerate(pages):
        total += len(p)
        if total > TEXT_MAX:
            pages = pages[:i + 1]; pages[-1] = p[:max(0, len(p) - (total - TEXT_MAX))]; break
    if not any(p.strip() for p in pages):
        raise ExtractError("empty")
    return {"pages": pages, "method": method, "date": date}


def pages_to_text(pages):
    return "\f".join(pages)


# ---------------------------------------------------------------- Zeitangaben finden
MONTHS = {}
for _n, _ws in {1: "januar jan january jänner", 2: "februar feb february", 3: "märz maerz mär mar march", 4: "april apr", 5: "mai may",
                6: "juni jun june", 7: "juli jul july", 8: "august aug", 9: "september sept sep", 10: "oktober okt october oct",
                11: "november nov", 12: "dezember dez december dec"}.items():
    for _w in _ws.split():
        MONTHS[_w] = _n
WDAYS = {}
for _n, _ws in enumerate(["montag monday mo mon", "dienstag tuesday di tue tues", "mittwoch wednesday mi wed", "donnerstag thursday do thu thurs",
                          "freitag friday fr fri", "samstag sonnabend saturday sa sat", "sonntag sunday so sun"]):
    for _w in _ws.split():
        WDAYS[_w] = _n
WD_FULL = "montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonnabend|sonntag|monday|tuesday|wednesday|thursday|friday|saturday|sunday"
WD_SHORT = "mo|di|mi|do|fr|sa|so|mon|tue|tues|wed|thu|thurs|fri|sat|sun"
WD_PRE = r"(?:(?P<wd>" + WD_FULL + r")\.?,?\s+|(?P<wd2>" + WD_SHORT + r")(?:\.,?|,)\s+)"     # „Montag, “ oder „Mo., “ (kurz nur mit Punkt/Komma)
MON_RE = "|".join(sorted(MONTHS, key=len, reverse=True))
CONF = ("genau", "ungefaehr", "unklar")
APPROX_RE = r"(?:gegen|ca\.?|circa|etwa|ungefähr|ungefaehr|so\s+um|um\s+ca\.?|around|about|approx\.?|approximately|roughly)"

_B = r"(?<![\w./:-])"                          # kein Teil einer längeren Zahl/eines Wortes
_E = r"(?![\w/-]|[.:]\d)"
DATE_RES = [
    ("iso", re.compile(_B + r"(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})" + _E)),
    ("dmy", re.compile(_B + r"(?:" + WD_PRE + r"(?:den\s+)?)?(?P<d>\d{1,2})\.\s?(?P<m>\d{1,2})\.\s?(?P<y>\d{4}|\d{2})" + _E, re.I)),
    ("dMy", re.compile(_B + r"(?:" + WD_PRE + r"(?:den\s+|the\s+)?)?(?P<d>\d{1,2})(?:\.|st|nd|rd|th)?\s*(?:of\s+)?(?P<mn>" + MON_RE + r")\.?(?:\s+(?P<y>\d{4}))?(?![\w])", re.I)),
    ("Mdy", re.compile(_B + r"(?:" + WD_PRE + r")?(?P<mn>" + MON_RE + r")\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(?P<y>\d{4}))?(?![\w.:])", re.I)),
    ("slash", re.compile(_B + r"(?P<a>\d{1,2})/(?P<b>\d{1,2})/(?P<y>\d{4}|\d{2})" + _E)),
    ("dm", re.compile(_B + r"(?:" + WD_PRE + r"(?:den\s+)?)?(?P<d>\d{1,2})\.(?P<m>\d{1,2})\.(?!\d)", re.I)),
    ("rel", re.compile(r"(?<![\w])(?P<r>vorgestern|gestern|heute|yesterday|today|tonight|last\s+night|letzte\s+nacht|vergangene\s+nacht)"
                       r"(?:\s*(?P<p>nacht|abend|morgen|früh|frueh|nachmittag|mittag|vormittag|night|evening|morning|afternoon))?(?![\w])", re.I)),
    ("wd", re.compile(r"(?<![\w])(?:(?P<pre>am|letzten|letztem|vergangenen|on|last)\s+)?(?P<wd>" + WD_FULL + r")"
                      r"(?P<p>nacht|abend|morgen|nachmittag|vormittag|\s+night|\s+evening|\s+morning|\s+afternoon)?(?![\w])", re.I)),
]
_H = r"(?:[01]?\d|2[0-4])"
_AP = r"am(?!\s+(?-i:[A-ZÄÖÜ\d]))|pm|a\.m\.|p\.m\."                # „am“ vor Großbuchstabe/Zahl = deutsch („23 Uhr am Montag“)
TIME_RES = [
    # 23:15–23:40, 23.15 - 23.40 Uhr, 22–1 Uhr, von 22 bis 1 Uhr, zwischen 22 und 23 Uhr, from 10 pm to 1 am, 10pm-1am
    ("range", re.compile(r"(?<![\w.:])(?:(?P<ap>" + APPROX_RE + r")\s+)?(?:(?:von|ab|zwischen|from|between)\s+)?"
                         r"(?P<h1>" + _H + r")(?:[:.](?P<m1>[0-5]\d))?\s*(?P<x1>uhr|" + _AP + r")?\s*"
                         r"(?P<rs>–|—|-|bis|und|to|until|till|and)\s*(?:ca\.?\s*)?"
                         r"(?P<h2>" + _H + r")(?:[:.](?P<m2>[0-5]\d))?\s*(?P<x2>uhr|h\b|" + _AP + r")?(?![\w:])", re.I)),
    ("one", re.compile(r"(?<![\w.:])(?:(?P<ap>" + APPROX_RE + r")\s+|(?P<um>um|at|ab|seit|since)\s+)?"
                       r"(?P<h1>" + _H + r")(?:(?P<sep>[:.])(?P<m1>[0-5]\d))?\s*(?P<x1>uhr|h\b|" + _AP + r")?(?![\w:])", re.I)),
]


def _y2(y):
    y = int(y)
    return 2000 + y if y < 100 else y


def _mk_date(y, m, d):
    try:
        return dt.date(int(y), int(m), int(d))
    except (TypeError, ValueError):
        return None


def _h24(h, x, base_eve=False):
    h = int(h)
    x = (x or "").lower().replace(".", "")
    if x == "pm" and h < 12:
        return h + 12
    if x == "am" and h == 12:
        return 0
    if base_eve and not x and 1 <= h < 12:
        return h + 12
    return h


def _worse(a, b):
    return CONF[max(CONF.index(a), CONF.index(b))]


def _find_dates(line, ref, ctx_year, ref_known):
    out, taken = [], []
    for kind, rx in DATE_RES:
        for m in rx.finditer(line):
            a, b = m.span()
            if any(not (b <= x or a >= y) for x, y in taken):
                continue
            g = m.groupdict()
            tok = {"span": (a, b), "kind": kind, "conf": "genau", "part": None, "txt": m.group(0)}
            if kind == "iso":
                tok["date"] = _mk_date(g["y"], g["m"], g["d"])
            elif kind == "dmy":
                tok["date"] = _mk_date(_y2(g["y"]), g["m"], g["d"])
            elif kind in ("dMy", "Mdy"):
                mo = MONTHS.get(g["mn"].lower().rstrip("."))
                if not mo or (kind == "Mdy" and g["mn"].lower() in ("mai", "may") and not g.get("y")):   # „Mai 5“ selten – „may“ ist auch ein Wort
                    continue
                if kind == "Mdy" and g["mn"].lower() == "mar" and not g.get("y"):
                    continue
                if g.get("y"):
                    tok["date"] = _mk_date(g["y"], mo, g["d"])
                else:
                    tok["date"], tok["conf"] = _guess_year(mo, int(g["d"]), ref, ctx_year, ref_known)
            elif kind == "slash":
                x1, x2 = int(g["a"]), int(g["b"])
                if x1 > 12:
                    d_, m_, c = x1, x2, "genau"
                elif x2 > 12:
                    d_, m_, c = x2, x1, "genau"
                else:
                    d_, m_, c = x1, x2, ("genau" if x1 == x2 else "unklar")
                tok["date"], tok["conf"] = _mk_date(_y2(g["y"]), m_, d_), c
            elif kind == "dm":
                tok["date"], tok["conf"] = _guess_year(int(g["m"]), int(g["d"]), ref, ctx_year, ref_known)
            elif kind == "rel":
                r = re.sub(r"\s+", " ", g["r"].lower()); p = (g.get("p") or "").lower()
                back = {"vorgestern": 2, "gestern": 1, "yesterday": 1, "heute": 0, "today": 0, "tonight": 0, "last night": 0, "letzte nacht": 0, "vergangene nacht": 0}[r]
                tok["date"] = ref - dt.timedelta(days=back)
                if r in ("last night", "letzte nacht", "vergangene nacht", "tonight") or p in ("nacht", "night"):
                    tok["part"] = "night"
                    if r in ("last night", "letzte nacht", "vergangene nacht", "tonight", "heute"):
                        tok["date"] = ref - dt.timedelta(days=1)       # die Nacht, die am Tag des Dokuments endet
                elif p in ("abend", "evening"):
                    tok["part"] = "eve"
                elif p in ("morgen", "früh", "frueh", "morning", "vormittag"):
                    tok["part"] = "morn"
                elif p in ("nachmittag", "afternoon", "mittag"):
                    tok["part"] = "aft"
                tok["conf"] = "ungefaehr" if ref_known else "unklar"
            elif kind == "wd":
                wd = WDAYS[g["wd"].lower()]; pre = (g.get("pre") or "").lower(); p = (g.get("p") or "").strip().lower()
                back = (ref.weekday() - wd) % 7
                if back == 0 and pre in ("letzten", "letztem", "vergangenen", "last"):
                    back = 7
                tok["date"] = ref - dt.timedelta(days=back)
                tok["part"] = {"nacht": "night", "night": "night", "abend": "eve", "evening": "eve", "morgen": "morn", "morning": "morn",
                               "vormittag": "morn", "nachmittag": "aft", "afternoon": "aft"}.get(p)
                tok["conf"] = "ungefaehr" if ref_known else "unklar"
            if not tok.get("date"):
                continue
            wdg = g.get("wd2") or (g.get("wd") if kind != "wd" else None)
            if wdg and WDAYS.get(wdg.lower()) != tok["date"].weekday():
                tok["conf"] = "unklar"; tok["wd_bad"] = True                 # Wochentag passt nicht zum Datum
            out.append(tok); taken.append((a, b))
    out.sort(key=lambda x: x["span"][0])
    return out


def _guess_year(mo, d, ref, ctx_year, ref_known):
    """Datum ohne Jahr: Jahr aus dem Zusammenhang (zuletzt genanntes Jahr im Dokument), sonst aus dem Datum des Dokuments;
    liegt das Datum dann deutlich nach dem Dokument, ist das Vorjahr gemeint."""
    y = ctx_year or ref.year
    x = _mk_date(y, mo, d)
    if x is None:
        return None, "unklar"
    if not ctx_year and x > ref + dt.timedelta(days=7):
        x = _mk_date(y - 1, mo, d) or x
    return x, ("genau" if ctx_year else "ungefaehr" if ref_known else "unklar")


def _find_times(line, dates):
    out, taken = [], [d["span"] for d in dates]
    for kind, rx in TIME_RES:
        for m in rx.finditer(line):
            a, b = m.span()
            if any(not (b <= x or a >= y) for x, y in taken):
                continue
            g = m.groupdict()
            h1 = int(g["h1"])
            if kind == "one":
                # nur mit Uhrzeit-Zeichen: 23:15, 23.15 Uhr, 23 Uhr, 11 pm, um 23 (mit „um“ nur 0–24 und ohne folgendes Wort wie „Euro“)
                if not (g.get("sep") == ":" or g.get("x1") or (g.get("um") and g.get("sep") is None and re.match(r"\s*(?:[,.;)!?]|$|und\b|and\b)", line[b:], re.I))):
                    continue
                if g.get("sep") == "." and not g.get("x1"):
                    continue
            else:
                if g["rs"].lower() in ("und", "and") and not re.match(r"(?:zwischen|between)\s", m.group(0).lstrip(), re.I) and not g.get("ap"):
                    continue                                    # „um 22:10 und 23:30“ = zwei Zeiten, kein Zeitraum
                has_unit = g.get("x1") or g.get("x2") or g.get("m1") or g.get("m2")
                if not has_unit:
                    continue
                if (g.get("m1") is None) != (g.get("m2") is None) and not (g.get("x2") or g.get("x1")):
                    continue
                if not g.get("m1") and not g.get("m2") and not re.search(r"(?:von|ab|zwischen|from|between)\s", m.group(0), re.I) and not g.get("x2"):
                    continue
                if re.fullmatch(r"\s*\d{1,2}\.\d{2}\s*[–-]\s*\d{1,2}\.\d{2}\s*", m.group(0)) and not (g.get("x2") or g.get("x1")):
                    continue
            m1 = int(g.get("m1") or 0)
            if h1 > 24 or (h1 == 24 and m1):
                continue
            t = {"span": (a, b), "h1": h1 % 24, "m1": m1, "x1": g.get("x1") or (g.get("x2") if kind == "range" and (g.get("x2") or "").lower() in ("am", "pm", "a.m.", "p.m.") and not g.get("x1") else None),
                 "approx": bool(g.get("ap")), "txt": m.group(0)}
            if kind == "range":
                h2, m2 = int(g["h2"]), int(g.get("m2") or 0)
                if h2 > 24 or (h2 == 24 and m2):
                    continue
                t.update(h2=h2 % 24, m2=m2, x2=g.get("x2"))
            out.append(t); taken.append((a, b))
    out.sort(key=lambda x: x["span"][0])
    return out


SENT_SPLIT = re.compile(r"(?<=[a-zäöüß)\"“”]{2}[.!?])\s+(?=[A-ZÄÖÜ„\"(])")


def _sentence(lines, i, span):
    """Satz um die Fundstelle; geht über das Zeilenende, wenn der Satz dort nicht endet (höchstens 3 Zeilen)."""
    line = lines[i]
    parts, pos, sent = SENT_SPLIT.split(line), 0, line
    for p in parts:
        j = line.find(p, pos)
        if j <= span[0] < j + len(p) + 1:
            sent = p; break
        pos = j + len(p)
    k = i
    while not re.search(r"[.!?]\s*$", sent) and k + 1 < len(lines) and k < i + 2 and lines[k + 1].strip() and not _starts_with_date(lines[k + 1]):
        k += 1
        nxt = SENT_SPLIT.split(lines[k].strip())[0]
        sent = sent.rstrip() + " " + nxt.strip()
    return re.sub(r"\s+", " ", sent).strip()[:500]


def _starts_with_date(s):
    s = s.strip()
    return any(rx.match(s) for k, rx in DATE_RES if k not in ("rel", "wd")) or bool(re.match(r"\d{1,2}[:.]\d{2}", s))


LEAD_TIME = re.compile(r"(?:(?:um|gegen|ca\.?|ab|von|zwischen|at|around|from)\s+)?\d{1,2}(?:[:.]\d{2})?\s*(?:uhr|h|am|pm)?"
                       r"(?:\s*(?:–|—|-|bis|und|to)\s*\d{1,2}(?:[:.]\d{2})?\s*(?:uhr|h|am|pm)?)?(?:[\s:,;.–—-]+|$)", re.I)


def _strip_lead(sent, toks):
    """Datum/Uhrzeit am Satzanfang (z. B. „12.03.2025, 23:15 Uhr:“) aus dem Vorschlagstext nehmen."""
    s = sent
    for _ in range(4):
        hit = False
        for t in toks:
            tx = t["txt"].strip()
            if tx and s.lower().startswith(tx.lower()):
                s = s[len(tx):]; hit = True
        s2 = re.sub(r"^[\s:,;–—\-.)]+", "", s)
        s2 = re.sub(r"^(?:um|am|gegen|ab|von|at|on)\s+(?=\d)", "", s2, flags=re.I)
        m = LEAD_TIME.match(s2)
        if m and re.search(r"[:]|uhr|[ap]\.?m", m.group(0), re.I):
            s2 = s2[m.end():]
        hit = hit or s2 != s
        s = s2
        if not hit:
            break
    s = s.strip()
    return s if len(s) >= 3 else sent


def _iso(d):
    return d.astimezone().isoformat(timespec="seconds") if d.tzinfo is None else d.isoformat(timespec="seconds")


def find_times(pages, ref=None, ref_known=None):
    """Zeitangaben in den Seiten finden. ref = Datum des Dokuments (date/datetime) für relative Angaben und fehlende Jahre.
    → Liste von Treffern {from, to, conf, page, line, sentence, text, date_only, match}."""
    if isinstance(ref, dt.datetime):
        ref = ref.astimezone().date() if ref.tzinfo else ref.date()
    if ref_known is None:
        ref_known = ref is not None
    ref = ref or dt.date.today()
    hits, pend, ctx, ctx_year, used = [], [], None, None, set()
    gline = 0
    for pi, page in enumerate(pages):
        lines = page.split("\n")
        for li, line in enumerate(lines):
            gline += 1
            if not line.strip() or len(line) > 5000:
                continue
            dates = _find_dates(line, ref, ctx_year, ref_known)
            times = _find_times(line, dates)
            for t in times:
                before = [d for d in dates if d["span"][1] <= t["span"][0]]
                after = [d for d in dates if d["span"][0] >= t["span"][1]]
                d = before[-1] if before else after[0] if after else None
                conf = None
                if d is None and ctx and gline - ctx["g"] <= 15:      # Uhrzeit ohne Datum: zuletzt genanntes Datum (bis 15 Zeilen davor)
                    d = ctx["tok"]
                if d is None:
                    d = {"date": ref, "conf": "unklar", "part": None, "span": (0, 0), "txt": ""}
                    conf = "unklar"
                used.add(id(d))
                base = d["date"]
                eve = d.get("part") in ("eve", "aft")
                h1 = _h24(t["h1"], t.get("x1"), eve)
                day1 = base
                if d.get("part") == "night" and h1 < 12:
                    day1 = base + dt.timedelta(days=1)
                a = dt.datetime.combine(day1, dt.time(h1, t["m1"])).astimezone()
                b = None
                if "h2" in t:
                    ap = lambda x: x if (x or "").lower().replace(".", "") in ("am", "pm") else None
                    h2 = _h24(t["h2"], ap(t.get("x2")) or ap(t.get("x1")), eve)
                    b = dt.datetime.combine(day1, dt.time(h2, t["m2"])).astimezone()
                    if b <= a:
                        b = dt.datetime.combine(day1 + dt.timedelta(days=1), dt.time(h2, t["m2"])).astimezone()   # über Mitternacht
                c = conf or d["conf"]
                if t["approx"]:
                    c = _worse(c, "ungefaehr")
                sent = _sentence(lines, li, t["span"])
                hits.append({"from": _iso(a), "to": _iso(b) if b else "", "conf": c, "page": pi + 1, "line": li + 1, "sentence": sent,
                             "text": _strip_lead(sent, dates + times), "date_only": False, "match": (d.get("txt", "") + " " + t["txt"]).strip()[:80],
                             "_pos": (pi, li, t["span"][0])})
            for d in dates:
                if d["kind"] in ("iso", "dmy") or (d["kind"] in ("dMy", "Mdy", "slash") and re.search(r"\d{4}", d["txt"])):
                    ctx_year = d["date"].year
                pend.append({"tok": d, "pi": pi, "li": li, "lines": lines, "times": times, "dates": dates})
            if dates:
                ctx = {"tok": dates[-1], "g": gline}
    for p_ in pend:                                     # Datum ohne Uhrzeit (und ohne Uhrzeiten in den Zeilen danach)
        if id(p_["tok"]) in used:
            continue
        d = p_["tok"]
        if d.get("part") == "night":
            a = dt.datetime.combine(d["date"], dt.time(22, 0)).astimezone(); b = dt.datetime.combine(d["date"] + dt.timedelta(days=1), dt.time(6, 0)).astimezone()
        elif d.get("part") == "eve":
            a = dt.datetime.combine(d["date"], dt.time(18, 0)).astimezone(); b = dt.datetime.combine(d["date"], dt.time(22, 0)).astimezone()
        elif d.get("part") == "morn":
            a = dt.datetime.combine(d["date"], dt.time(6, 0)).astimezone(); b = dt.datetime.combine(d["date"], dt.time(12, 0)).astimezone()
        elif d.get("part") == "aft":
            a = dt.datetime.combine(d["date"], dt.time(12, 0)).astimezone(); b = dt.datetime.combine(d["date"], dt.time(18, 0)).astimezone()
        else:
            a = dt.datetime.combine(d["date"], dt.time(0, 0)).astimezone(); b = dt.datetime.combine(d["date"], dt.time(23, 59, 59)).astimezone()
        sent = _sentence(p_["lines"], p_["li"], d["span"])
        hits.append({"from": _iso(a), "to": _iso(b), "conf": _worse(d["conf"], "ungefaehr"), "page": p_["pi"] + 1, "line": p_["li"] + 1, "sentence": sent,
                     "text": _strip_lead(sent, p_["dates"] + p_["times"]), "date_only": True, "match": d["txt"][:80], "_pos": (p_["pi"], p_["li"], d["span"][0])})
    hits.sort(key=lambda h: h["_pos"])
    for h in hits:
        h.pop("_pos", None)
    return hits[:2000]
