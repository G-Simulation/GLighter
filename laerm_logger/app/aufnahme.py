#!/usr/bin/env python3
"""Starter und Aufnahme-Relais des Lärmprotokolls.

Läuft die ganze Zeit des Add-ons und ist bewusst klein (ändert sich selten):
- startet das eigentliche Programm (laerm.py) und startet es neu, wenn dessen Dateien aktualisiert wurden
  (neue Fassung einfach nach /share/laerm_update/ kopieren, ohne das Add-on neu zu erstellen);
- hält die Aufnahme des Server-Mikrofons und der Stream-Quellen offen, auch während laerm.py neu startet.
  Der Ton liegt dabei nur im Arbeitsspeicher (höchstens 5 Minuten) und wird danach an laerm.py nachgeliefert.
  Er wird nie gespeichert.
- schreibt Start, Stopp, Update und Unterbrechungen mit Uhrzeit und Version in /data/laufzeit.jsonl.
"""
import collections
import json
import os
import re
import select
import signal
import socket
import struct
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(os.environ.get("LAERM_SOURCES", "/data/sources.json")) or "/data"
SOCK = os.environ.get("LAERM_RELAY", "/tmp/laerm_relay.sock")
UPDATE_DIRS = [d for d in os.environ.get("LAERM_UPDATE_DIR", "/share/laerm_update").split(":") if d]
RUNLOG = os.path.join(DATA_DIR, "laufzeit.jsonl")
STATE_FILE = os.path.join(DATA_DIR, "update_state.json")
ALIVE = os.path.join(DATA_DIR, "alive")
KEEP_S = 300                 # so lange wird Ton gepuffert, wenn laerm.py nicht abholt
RELAY_VERSION = 2
SENT_KEEP_S = 30             # bereits geschickter Ton: so lange aufheben, falls laerm.py ihn beim Neustart nicht mehr verarbeitet hat


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


def app_dirs():
    """Mögliche Fassungen: eingebaut (/app) und Kopien unter /share/laerm_update (…/laerm_logger/app oder …/app)."""
    out = [HERE]
    for u in UPDATE_DIRS:
        for d in (os.path.join(u, "laerm_logger", "app"), os.path.join(u, "app")):
            if os.path.isfile(os.path.join(d, "laerm.py")) and os.path.realpath(d) != os.path.realpath(HERE):
                out.append(d)
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
