"""GLighter – Suchverzeichnis (SQLite, in Python enthalten, Public Domain).

Nur abgeleitete Daten, jederzeit aus den Originalen neu aufbaubar. Die Originale (Tagesaufzeichnung .ltg,
Pruefsummen-Kette .chk, Spektrum .lts/.ltp, log.csv) werden hier nie geschrieben oder geaendert.

  chain  Ergebnis der Kettenpruefung je Geraet und Tag. Schluessel ist die SHA-256 ueber den *Inhalt* aller
         Dateien des Tages: aendert sich auch nur ein Byte, wird neu geprueft. So bleibt die Pruefung so streng wie
         ohne Verzeichnis, nur muss ein unveraenderter Tag nicht bei jedem Protokoll neu durchgerechnet werden.
  agg    Verdichtete Tagesspur (je 10 s: Spitze, Hintergrund, Schwelle als Maximum) fuer Protokolle ueber lange
         Zeitraeume. Schluessel: Groesse und Aenderungszeit der Tagesdatei. Nur fuer die Anzeige.

Jeder Fehler (Datei kaputt, Platte voll, gesperrt) fuehrt zum bisherigen Weg ohne Verzeichnis; eine beschaedigte
Datenbank wird verworfen und neu angelegt.
"""
import hashlib, io, json, os, sqlite3, threading, time

import numpy as np

AGG_S = 10                                    # Aufloesung der verdichteten Spur in Sekunden
SCHEMA = 1


class SuchIndex:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.db = None
        self.hits = self.miss = 0
        self.err = ""

    # ---------- Verbindung ----------
    def _open(self):
        if self.db is not None:
            return self.db
        for attempt in (0, 1):
            try:
                os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
                db = sqlite3.connect(self.path, timeout=10, check_same_thread=False, isolation_level=None)
                db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA synchronous=NORMAL")
                db.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
                v = db.execute("SELECT v FROM meta WHERE k='schema'").fetchone()
                if v is None or int(v[0]) != SCHEMA:
                    db.executescript("DROP TABLE IF EXISTS chain; DROP TABLE IF EXISTS agg;")
                db.executescript("""
                    CREATE TABLE IF NOT EXISTS chain (sid TEXT, day TEXT, h TEXT, res TEXT, t REAL, PRIMARY KEY (sid, day));
                    CREATE TABLE IF NOT EXISTS agg (sid TEXT, day TEXT, sig TEXT, blob BLOB, t REAL, PRIMARY KEY (sid, day));
                """)
                db.execute("INSERT OR REPLACE INTO meta VALUES ('schema', ?)", (str(SCHEMA),))
                db.execute("PRAGMA quick_check(1)")
                self.db = db; self.err = ""
                return db
            except (sqlite3.Error, OSError) as e:
                self.err = str(e)
                try:
                    db.close()
                except Exception:
                    pass
                if attempt == 0:                     # beschaedigt: verwerfen, neu anlegen
                    for suf in ("", "-wal", "-shm"):
                        try:
                            os.remove(self.path + suf)
                        except OSError:
                            pass
        return None

    def _run(self, fn):
        with self.lock:
            db = self._open()
            if db is None:
                return None
            try:
                return fn(db)
            except (sqlite3.Error, ValueError, TypeError, OSError) as e:
                self.err = str(e)
                return None

    # ---------- Kettenpruefung ----------
    @staticmethod
    def files_hash(files):
        h = hashlib.sha256()
        for f in files:
            h.update(os.path.basename(f).encode() + b"\0")
            try:
                with open(f, "rb") as fh:
                    while True:
                        b = fh.read(1 << 20)
                        if not b:
                            break
                        h.update(b)
            except OSError:
                h.update(b"-")
            h.update(b"\0")
        return h.hexdigest()

    def chain_get(self, sid, day, h):
        r = self._run(lambda db: db.execute("SELECT h, res FROM chain WHERE sid=? AND day=?", (sid, day)).fetchone())
        if r and r[0] == h:
            self.hits += 1
            try:
                return json.loads(r[1])
            except ValueError:
                return None
        self.miss += 1
        return None

    def chain_put(self, sid, day, h, res):
        self._run(lambda db: db.execute("INSERT OR REPLACE INTO chain VALUES (?,?,?,?,?)", (sid, day, h, json.dumps(res), time.time())))

    # ---------- verdichtete Tagesspur ----------
    @staticmethod
    def agg_make(d):
        """Aus day_load-Spalten: je AGG_S Sekunden Maximum von pk/bg/thr (NaN bleibt NaN)."""
        t = d["t"]
        if not len(t):
            return None
        b = (t // (AGG_S * 1000)) * (AGG_S * 1000)
        st = np.concatenate([[0], np.flatnonzero(np.diff(b)) + 1])
        out = {"t": b[st].astype(np.int64)}
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            for k in ("pk", "bg", "thr"):
                out[k] = np.fmax.reduceat(d[k], st).astype(np.float32)
        return out

    def agg_get(self, sid, day, sig):
        r = self._run(lambda db: db.execute("SELECT sig, blob FROM agg WHERE sid=? AND day=?", (sid, day)).fetchone())
        if not r or r[0] != sig:
            self.miss += 1
            return None
        try:
            z = np.load(io.BytesIO(r[1]))
            self.hits += 1
            return {"t": z["t"], "pk": z["pk"].astype(np.float64), "bg": z["bg"].astype(np.float64), "thr": z["thr"].astype(np.float64)}
        except Exception:
            return None

    def agg_put(self, sid, day, sig, a):
        bio = io.BytesIO(); np.savez_compressed(bio, **a)
        self._run(lambda db: db.execute("INSERT OR REPLACE INTO agg VALUES (?,?,?,?,?)", (sid, day, sig, bio.getvalue(), time.time())))

    # ---------- Verwaltung ----------
    def stats(self):
        def f(db):
            c = db.execute("SELECT COUNT(*) FROM chain").fetchone()[0]; a = db.execute("SELECT COUNT(*) FROM agg").fetchone()[0]
            return {"chain": c, "agg": a}
        s = self._run(f) or {"chain": 0, "agg": 0}
        size = 0
        for suf in ("", "-wal"):
            try:
                size += os.path.getsize(self.path + suf)
            except OSError:
                pass
        s.update(size=size, hits=self.hits, miss=self.miss, ok=self.db is not None, err=self.err)
        return s

    def clear(self):
        def f(db):
            db.execute("DELETE FROM chain"); db.execute("DELETE FROM agg"); db.execute("VACUUM")
            return True
        self.hits = self.miss = 0
        return bool(self._run(f))
