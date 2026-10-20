#!/usr/bin/env python3
"""Starter und Aufnahme-Relais des Lärmprotokolls.

Läuft die ganze Zeit des Add-ons und ist bewusst klein (ändert sich selten):
- startet das eigentliche Programm (laerm.py) und startet es neu, wenn dessen Dateien aktualisiert wurden
  (neue, signierte Fassung nach /share/gaslighter_update/ kopieren, ohne das Add-on neu zu erstellen; nur mit Option share_update);
- hält die Aufnahme des Server-Mikrofons und der Stream-Quellen offen, auch während laerm.py neu startet.
  Der Ton liegt dabei nur im Arbeitsspeicher (höchstens 5 Minuten) und wird danach an laerm.py nachgeliefert.
  Er wird nie gespeichert.
- schreibt Start, Stopp, Update und Unterbrechungen mit Uhrzeit und Version in /data/laufzeit.jsonl.
"""
import collections
import hashlib
import json
import os
import re
import select
import signal
import socket
import struct
import subprocess
import sys
import shutil
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(os.environ.get("LAERM_SOURCES", "/data/sources.json")) or "/data"
SOCK = os.environ.get("LAERM_RELAY", "/tmp/laerm_relay.sock")
UPDATE_DIRS = [d for d in os.environ.get("LAERM_UPDATE_DIR", "/share/gaslighter_update:/share/laerm_update").split(":") if d]
RUNLOG = os.path.join(DATA_DIR, "laufzeit.jsonl")
STATE_FILE = os.path.join(DATA_DIR, "update_state.json")
ALIVE = os.path.join(DATA_DIR, "alive")
KEEP_S = 300                 # so lange wird Ton gepuffert, wenn laerm.py nicht abholt
RELAY_VERSION = 2
SENT_KEEP_S = 30             # bereits geschickter Ton: so lange aufheben, falls laerm.py ihn beim Neustart nicht mehr verarbeitet hat
OPTIONS_FILE = os.environ.get("LAERM_OPTIONS", "/data/options.json")
RUN_DIR = os.path.join(DATA_DIR, "update_run")   # geprüfte Kopien der Update-Fassungen (privat, nicht in /share)
MANIFEST, MANIFEST_SIG = "manifest.txt", "manifest.sig"
SIG_CONTEXT = b"GSIM-UPDATE-1\n"                # Domänentrennung: eine Update-Signatur ist nie eine gültige Lizenz und umgekehrt
KEEP_RUN_DIRS = 3


def log(*a):
    print(time.strftime("%H:%M:%S"), "[Starter]", *a, flush=True)


def now_iso(ts=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts if ts is not None else time.time())) + _tz(ts)


def _tz(ts=None):
    off = -(time.altzone if time.localtime(ts if ts is not None else time.time()).tm_isdst > 0 else time.timezone)
    return "%+03d:%02d" % (off // 3600, abs(off) % 3600 // 60)


def runlog(kind, **kw):
    """Eintrag ins Laufzeit-Protokoll (nur anhängen)."""
    e = dict(at=now_iso(), kind=kind, **kw)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(RUNLOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    except OSError as ex:
        log("Laufzeit-Protokoll nicht geschrieben:", ex)


# ---------------------------------------------------------------------------------------------
# Aufnahme-Relais: je Quelle ein Rekorder-Prozess, 100-ms-Blöcke mit Ankunftszeit im Ringpuffer
# ---------------------------------------------------------------------------------------------
class Channel:
    def __init__(self, sid, cmd, block):
        self.sid, self.cmd, self.block = sid, cmd, block
        self.buf = collections.deque()           # (ts, bytes)
        self.sent = collections.deque()          # schon an laerm.py geschickt (ts, bytes), fuer die Uebergabe beim Neustart
        self.cond = threading.Condition()
        self.err = None                          # Rekorder beendet: letzte Meldungen
        self.tail = collections.deque(maxlen=20)
        self.client_at = time.time()
        self.attached = False
        self.dead = False
        self.p = None
        self.start()

    def start(self):
        try:
            self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        except FileNotFoundError as e:
            self.err = "Programm fehlt: " + str(e.filename); self.dead = True; return
        threading.Thread(target=self._drain, daemon=True).start()
        threading.Thread(target=self._read, daemon=True).start()

    def _drain(self):
        try:
            for line in iter(self.p.stderr.readline, b""):
                t = line.decode(errors="replace").strip()
                if t:
                    self.tail.append(re.sub(r"//[^/\s]*@", "//***@", t))
        except Exception:
            pass

    def _read(self):
        fd = self.p.stdout.fileno()
        size = self.block
        try:
            while not self.dead:
                b = bytearray()
                while len(b) < size and not self.dead:
                    r, _, _ = select.select([fd], [], [], 0.5)
                    if not r:
                        if self.p.poll() is not None:
                            break
                        continue
                    c = os.read(fd, size - len(b))
                    if not c:
                        break
                    b += c
                if len(b) < size:
                    break
                ts = time.time()
                with self.cond:
                    self.buf.append((ts, bytes(b)))
                    while self.buf and ts - self.buf[0][0] > KEEP_S:
                        self.buf.popleft()
                    self.cond.notify_all()
        finally:
            code = self.p.poll()
            with self.cond:
                self.err = " | ".join(self.tail)[-400:] or (f"Aufnahme beendet (Code {code})" if code is not None else "Keine Audiodaten")
                self.dead = True
                self.cond.notify_all()

    def kill(self):
        self.dead = True
        try:
            self.p.kill(); self.p.wait(timeout=2)
        except Exception:
            pass
        with self.cond:
            self.cond.notify_all()


CHANNELS = {}
CH_LOCK = threading.Lock()


def serve_client(conn):
    """Eine Verbindung von laerm.py: {"sid", "cmd", "block", "fresh"} -> Blöcke (ts, Länge, Daten).
    Länge 0xFFFFFFFF = Rekorder beendet, danach die Meldung. Schickt laerm.py "K", wird der Rekorder beendet."""
    f = conn.makefile("rb")
    try:
        req = json.loads(f.readline().decode() or "{}")
    except ValueError:
        conn.close(); return
    sid, cmd, block, fresh = str(req.get("sid", "")), req.get("cmd") or [], int(req.get("block") or 3200), bool(req.get("fresh"))
    try:
        since = float(req["since"]) if req.get("since") is not None else None   # bis hier hat das vorige Programm verarbeitet
    except (TypeError, ValueError):
        since = None
    with CH_LOCK:
        ch = CHANNELS.get(sid)
        if ch is not None and (fresh or ch.cmd != cmd or ch.block != block or ch.dead):
            ch.kill(); ch = None
        if ch is None:
            ch = CHANNELS[sid] = Channel(sid, cmd, block)
            log(f"Aufnahme {sid} gestartet")
        else:
            n_rep = 0
            with ch.cond:
                if since is not None:                # geschickt, aber vom vorigen Programm nicht mehr verarbeitet: noch einmal
                    rep_ = [x for x in ch.sent if x[0] > since + 1e-6]
                    ch.buf.extendleft(reversed(rep_)); n_rep = len(rep_)
                ch.sent.clear()
            if ch.buf:
                log(f"Aufnahme {sid}: {len(ch.buf) / 10:.1f} s aus dem Puffer nachgeliefert" + (f" (davon {n_rep / 10:.1f} s erneut)" if n_rep else ""))
        ch.attached = True
    conn.setblocking(True)
    stop = threading.Event()

    def watch_in():                              # "K" = Rekorder beenden (hängt, neue Einstellungen)
        try:
            while not stop.is_set():
                d = conn.recv(16)
                if not d:
                    break
                if b"K" in d:
                    ch.kill(); break
        except OSError:
            pass
        stop.set()
        with ch.cond:
            ch.cond.notify_all()
    threading.Thread(target=watch_in, daemon=True).start()
    try:
        while not stop.is_set():
            with ch.cond:
                while not ch.buf and not ch.dead and not stop.is_set():
                    ch.cond.wait(0.5)
                items = list(ch.buf); ch.buf.clear()
                dead, err = ch.dead, ch.err
            for k, (ts, b) in enumerate(items):
                try:
                    conn.sendall(struct.pack("<dI", ts, len(b)) + b)
                except OSError:
                    with ch.cond:                    # nicht angekommen: fuer das naechste Programm aufheben
                        ch.buf.extendleft(reversed(items[k:]))
                    raise
                with ch.cond:
                    ch.sent.append((ts, b))
                    while ch.sent and ts - ch.sent[0][0] > SENT_KEEP_S:
                        ch.sent.popleft()
            if dead and not items:
                m = (err or "").encode("utf-8", "replace")[:2000]
                conn.sendall(struct.pack("<dI", time.time(), 0xFFFFFFFF) + struct.pack("<I", len(m)) + m)
                break
    except OSError:
        pass                                     # laerm.py weg (Neustart): Rekorder läuft weiter, Ton wird gepuffert
    finally:
        stop.set()
        ch.attached = False; ch.client_at = time.time()
        try:
            conn.close()
        except OSError:
            pass
        with CH_LOCK:
            if ch.dead and CHANNELS.get(sid) is ch:
                CHANNELS.pop(sid, None)


def relay_janitor():
    """Niemand holt mehr ab (Quelle entfernt, laerm.py dauerhaft weg): nach 5 Minuten beenden."""
    while True:
        time.sleep(10)
        with CH_LOCK:
            for sid, ch in list(CHANNELS.items()):
                if ch.dead or (not ch.attached and time.time() - ch.client_at > KEEP_S):
                    ch.kill(); CHANNELS.pop(sid, None)
                    log(f"Aufnahme {sid} beendet (nicht mehr abgeholt)")


def relay_server():
    try:
        os.unlink(SOCK)
    except OSError:
        pass
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(SOCK); s.listen(16)
    threading.Thread(target=relay_janitor, daemon=True).start()
    while True:
        c, _ = s.accept()
        threading.Thread(target=serve_client, args=(c,), daemon=True).start()


# ---------------------------------------------------------------------------------------------
# Programm-Fassung wählen, starten, bei Aktualisierung neu starten, bei Fehler zurückfallen
# ---------------------------------------------------------------------------------------------
def version_of(d):
    try:
        with open(os.path.join(d, "laerm.py"), encoding="utf-8") as f:
            m = re.search(r'^VERSION = "([\d.]+)"', f.read(), re.M)
        return tuple(int(x) for x in m.group(1).split(".")) if m else None
    except (OSError, ValueError):
        return None


def vstr(v):
    return ".".join(map(str, v)) if v else "?"


def share_update_enabled():
    """Updates aus /share nur, wenn in der Konfiguration eingeschaltet (Option share_update, Standard: aus).
    Für Tests: LAERM_SHARE_UPDATE=1/0 hat Vorrang."""
    env = os.environ.get("LAERM_SHARE_UPDATE")
    if env is not None:
        return env == "1"
    try:
        with open(OPTIONS_FILE, encoding="utf-8") as f:
            return json.load(f).get("share_update") is True
    except (OSError, ValueError, AttributeError):
        return False


def update_pubkey():
    """Öffentlicher Schlüssel für Update-Signaturen: derselbe wie für Lizenzen (lizenz.py der eingebauten Fassung)."""
    import lizenz                                # immer das eingebaute /app/lizenz.py, nie eines aus /share
    return bytes.fromhex(lizenz.PUBLIC_KEY_HEX), lizenz.ed25519_verify


def parse_manifest(data):
    """manifest.txt: je Zeile „<sha256-hex>  <relativer/pfad>“ (wie sha256sum). Liefert {pfad: hash} oder wirft ValueError."""
    out = {}
    for ln in data.decode("utf-8").splitlines():
        if not ln.strip():
            continue
        m = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_][A-Za-z0-9_./-]*)", ln)
        if not m or ".." in m.group(2).split("/") or m.group(2) in (MANIFEST, MANIFEST_SIG) or m.group(2) in out:
            raise ValueError("Zeile ungültig: " + ln[:80])
        out[m.group(2)] = m.group(1)
    if "laerm.py" not in out:
        raise ValueError("laerm.py fehlt im Manifest")
    return out


def check_signature(manifest, sig_txt):
    """Ed25519-Signatur (hex, 64 Byte) über SIG_CONTEXT + manifest.txt prüfen."""
    try:
        sig = bytes.fromhex(sig_txt.decode("ascii").strip())
    except (ValueError, UnicodeDecodeError):
        return False
    pub, verify = update_pubkey()
    return len(sig) == 64 and verify(pub, SIG_CONTEXT + manifest, sig)


def tree_files(d):
    out = set()
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for fn in files:
            out.add(os.path.relpath(os.path.join(root, fn), d).replace(os.sep, "/"))
    return out


REJECTED = {}                                    # Quelle -> letzter Grund (nur einmal protokollieren)
VERIFIED = {}                                    # (Quelle, Stand) -> geprüfte Kopie


def _reject(d, why):
    if REJECTED.get(d) != why:
        REJECTED[d] = why
        log(f"Update in {d} abgelehnt: {why}")
    return None


def verified_copy(d):
    """Update-Fassung nur mit gültiger Signatur übernehmen: Manifest prüfen, alle Dateien nach /data/update_run/<hash>
    kopieren und die Kopie gegen das Manifest prüfen. Gestartet wird nur die Kopie – spätere Änderungen in /share wirken nicht."""
    try:
        stamp = tuple(sorted((f, os.stat(os.path.join(d, f)).st_size, int(os.stat(os.path.join(d, f)).st_mtime)) for f in tree_files(d)))
    except OSError:
        return None
    if (d, stamp) in VERIFIED and os.path.isdir(VERIFIED[(d, stamp)]):
        return VERIFIED[(d, stamp)]
    try:
        with open(os.path.join(d, MANIFEST), "rb") as f:
            man = f.read()
        with open(os.path.join(d, MANIFEST_SIG), "rb") as f:
            sig = f.read()
    except OSError:
        return _reject(d, "manifest.txt/manifest.sig fehlen (nur signierte Updates werden angenommen)")
    if not check_signature(man, sig):
        return _reject(d, "Signatur ungültig")
    try:
        entries = parse_manifest(man)
    except (ValueError, UnicodeDecodeError) as e:
        return _reject(d, f"Manifest fehlerhaft ({e})")
    extra = sorted(tree_files(d) - set(entries) - {MANIFEST, MANIFEST_SIG})
    if extra:
        return _reject(d, "nicht signierte Dateien: " + ", ".join(extra[:5]))
    dst = os.path.join(RUN_DIR, hashlib.sha256(man).hexdigest()[:16])
    if not os.path.isdir(dst):
        tmp = dst + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        try:
            for rel, h in entries.items():
                with open(os.path.join(d, rel), "rb") as f:
                    data = f.read()
                if hashlib.sha256(data).hexdigest() != h:   # Prüfsumme über genau die Bytes, die kopiert werden
                    shutil.rmtree(tmp, ignore_errors=True)
                    return _reject(d, f"Prüfsumme passt nicht: {rel}")
                os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
                with open(os.path.join(tmp, rel), "wb") as f:
                    f.write(data)
            with open(os.path.join(tmp, MANIFEST), "wb") as f:
                f.write(man)
            os.replace(tmp, dst)
        except OSError as e:
            shutil.rmtree(tmp, ignore_errors=True)
            return _reject(d, f"Kopieren fehlgeschlagen ({e})")
        log(f"Signiertes Update aus {d} geprüft und nach {dst} übernommen")
        prune_run_dirs(keep=dst)
    REJECTED.pop(d, None)
    VERIFIED[(d, stamp)] = dst
    return dst


def prune_run_dirs(keep):
    """Nur die neuesten geprüften Kopien behalten (die laufende bzw. gerade übernommene bleibt immer)."""
    try:
        ds = sorted((os.path.join(RUN_DIR, x) for x in os.listdir(RUN_DIR) if not x.endswith(".tmp")), key=os.path.getmtime, reverse=True)
    except OSError:
        return
    for x in ds[KEEP_RUN_DIRS:]:
        if x != keep and x != getattr(prune_run_dirs, "running", None):
            shutil.rmtree(x, ignore_errors=True)


def app_dirs():
    """Mögliche Fassungen: eingebaut (/app) und – nur wenn share_update eingeschaltet ist – signierte Fassungen unter
    /share/gaslighter_update bzw. /share/laerm_update (…/gaslighter/app, …/laerm_logger/app oder …/app).
    Gestartet wird nie direkt aus /share, sondern aus der geprüften Kopie unter /data/update_run."""
    out = [HERE]
    if not share_update_enabled():
        return out
    for u in UPDATE_DIRS:
        for d in (os.path.join(u, "gaslighter", "app"), os.path.join(u, "laerm_logger", "app"), os.path.join(u, "app")):
            if os.path.isfile(os.path.join(d, "laerm.py")) and os.path.realpath(d) != os.path.realpath(HERE):
                v = verified_copy(d)
                if v:
                    out.append(v)
    return out


def sig_of(d):
    """Stand der Programmdateien (Python) einer Fassung."""
    s = []
    for root, _, files in os.walk(d):
        if "__pycache__" in root:
            continue
        for fn in files:
            if fn.endswith(".py"):
                p = os.path.join(root, fn)
                try:
                    st = os.stat(p); s.append((os.path.relpath(p, d), st.st_size, int(st.st_mtime)))
                except OSError:
                    pass
    return tuple(sorted(s))


def newest_mtime(d):
    m = 0
    for root, _, files in os.walk(d):
        for fn in files:
            try:
                m = max(m, os.stat(os.path.join(root, fn)).st_mtime)
            except OSError:
                pass
    return m


def valid(d):
    """Fassung brauchbar? Alle Python-Dateien übersetzbar, Oberfläche vorhanden."""
    if version_of(d) is None or not os.path.isfile(os.path.join(d, "web", "index.html")):
        return False
    for fn in ("laerm.py", "classify.py", "lernen.py", "yamnet_np.py"):
        p = os.path.join(d, fn)
        if not os.path.isfile(p):
            return False
        try:
            with open(p, encoding="utf-8") as f:
                compile(f.read(), p, "exec")
        except (SyntaxError, ValueError, OSError):
            return False
    return True


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(st):
    try:
        with open(STATE_FILE + ".tmp", "w") as f:
            json.dump(st, f)
        os.replace(STATE_FILE + ".tmp", STATE_FILE)
    except OSError:
        pass


def choose():
    """Neueste brauchbare Fassung; als fehlerhaft gemerkte Stände werden übersprungen."""
    st = load_state(); bad = st.get("bad") or []
    best = None
    for d in app_dirs():
        v = version_of(d)
        if v is None:
            continue
        key = [d, list(sig_of(d))]
        if key in bad or not valid(d):
            continue
        if best is None or v > best[1] or (v == best[1] and d != HERE):
            best = (d, v)
    return best or (HERE, version_of(HERE))


class Main:
    def __init__(self):
        self.p = None; self.dir = None; self.ver = None; self.sig = None; self.t = 0; self.fails = 0

    def start(self, d, v, reason):
        env = dict(os.environ, LAERM_RELAY=SOCK, LAERM_CODE_DIR=d, LAERM_START_REASON=reason)
        if model_missing(d):
            env["LAERM_MODEL_DIR"] = os.path.join(HERE, "model")      # Kopie ohne KI-Modell: das eingebaute nehmen
        self.p = subprocess.Popen([sys.executable, "-u", os.path.join(d, "laerm.py")], env=env, cwd=d)
        self.dir, self.ver, self.sig, self.t = d, v, sig_of(d), time.time()
        prune_run_dirs.running = d                   # laufende Fassung nie aufräumen
        log(f"Programm {vstr(v)} gestartet aus {d} ({reason})")

    def stop(self, timeout=20):
        if self.p is None or self.p.poll() is not None:
            return
        self.p.send_signal(signal.SIGTERM)
        try:
            self.p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.p.kill(); self.p.wait(timeout=5)


def model_missing(d):
    return not os.path.isfile(os.path.join(d, "model", "yamnet.npz"))


def alive_loop():
    while True:
        try:
            with open(ALIVE + ".tmp", "w") as f:
                f.write(str(int(time.time())))
            os.replace(ALIVE + ".tmp", ALIVE)
        except OSError:
            pass
        time.sleep(10)


def main():
    # Unterbrechung seit dem letzten Lebenszeichen (Add-on gestoppt, neu erstellt, Stromausfall) festhalten
    try:
        with open(ALIVE) as f:
            last = int(f.read().strip() or 0)
    except (OSError, ValueError):
        last = 0
    d, v = choose()
    st = load_state(); prev_v = st.get("last_version")
    if last and time.time() - last > 15:
        runlog("down", **{"from": now_iso(last), "to": now_iso(), "version_old": prev_v or "", "version_new": vstr(v),
                          "reason": "update" if prev_v and prev_v != vstr(v) else "restart"})
    runlog("start", version=vstr(v), relay=RELAY_VERSION, code=d)
    threading.Thread(target=alive_loop, daemon=True).start()
    threading.Thread(target=relay_server, daemon=True).start()
    time.sleep(0.3)
    m = Main()
    m.start(d, v, "start")
    st["last_version"] = vstr(v); save_state(st)
    good = (d, v)
    stopping = threading.Event()

    def on_term(signum, frame):
        stopping.set()
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)
    seen = {}                                    # Fassung -> (Stand, seit wann unverändert)
    while not stopping.is_set():
        stopping.wait(5)
        if stopping.is_set():
            break
        code = m.p.poll()
        if code is not None:                     # Programm beendet
            quick = time.time() - m.t < 60
            if quick and m.dir != good[0] or quick and m.fails >= 2:
                st = load_state(); bad = st.get("bad") or []
                bad.append([m.dir, list(m.sig)]); st["bad"] = bad[-20:]; save_state(st)
                runlog("fallback", version=vstr(m.ver), to=vstr(good[1] if m.dir != good[0] else version_of(HERE)), code=m.dir, exit=code)
                log(f"Fassung {vstr(m.ver)} startet nicht (Code {code}): zurück auf die vorige")
                nd, nv = (good if m.dir != good[0] else (HERE, version_of(HERE)))
                m.fails = 0; m.start(nd, nv, "fallback"); continue
            m.fails = m.fails + 1 if quick else 0
            runlog("crash", version=vstr(m.ver), exit=code)
            time.sleep(2); m.start(m.dir, m.ver, "restart"); continue
        if time.time() - m.t > 60:
            good = (m.dir, m.ver); m.fails = 0
        # Neue oder geänderte Fassung? Erst übernehmen, wenn 10 s lang nichts mehr geschrieben wurde (Kopieren fertig)
        try:
            cand_d, cand_v = choose()
        except Exception:
            continue
        changed = cand_d != m.dir or cand_v != m.ver or sig_of(cand_d) != m.sig
        if not changed:
            continue
        mt = newest_mtime(cand_d)
        if time.time() - mt < 10:
            continue
        if sig_of(cand_d) == m.sig and cand_d == m.dir and cand_v == m.ver:
            continue
        log(f"Neue Fassung {vstr(cand_v)} gefunden – nur das Programm startet neu, die Aufnahme läuft weiter")
        runlog("update", version_old=vstr(m.ver), version_new=vstr(cand_v), code=cand_d,
               relay_changed=os.path.isfile(os.path.join(cand_d, "aufnahme.py")) and _differs(os.path.join(cand_d, "aufnahme.py"), __file__))
        m.stop()
        m.start(cand_d, cand_v, "update")
        st = load_state(); st["last_version"] = vstr(cand_v); save_state(st)
    runlog("stop", version=vstr(m.ver))
    m.stop()
    with CH_LOCK:
        for ch in CHANNELS.values():
            ch.kill()


def _differs(a, b):
    try:
        with open(a, "rb") as f1, open(b, "rb") as f2:
            return f1.read() != f2.read()
    except OSError:
        return False


if __name__ == "__main__":
    main()
