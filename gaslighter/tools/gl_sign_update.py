#!/usr/bin/env python3
"""GLighter – Update-Fassung signieren (nur für G-Simulation, nicht Teil der App).

  python3 gl_sign_update.py  gaslighter_private.key  pfad/zu/gaslighter/app
  python3 gl_sign_update.py  --check                 pfad/zu/gaslighter/app

Schreibt in den App-Ordner:
  manifest.txt   je Datei eine Zeile „<sha256>  <relativer/pfad>“ (wie sha256sum, __pycache__ ausgenommen)
  manifest.sig   Ed25519-Signatur (128 Hex-Zeichen) über b"GSIM-UPDATE-1\\n" + manifest.txt

Derselbe private Schlüssel wie für Lizenzen (gl_license.py, 32 Byte hex). Durch das Präfix ist eine Update-Signatur
nie eine gültige Lizenz und umgekehrt. Der private Schlüssel gehört nie ins Repository und nie auf den Home-Assistant-Rechner:
signieren auf dem eigenen Rechner, danach den Ordner (mit manifest.txt + manifest.sig) nach /share/gaslighter_update/gaslighter/ kopieren.
Jede spätere Änderung an einer Datei macht die Signatur ungültig – dann neu signieren.
"""
import argparse, hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import gl_license as GL  # noqa: E402
import aufnahme as A     # noqa: E402  (Format und Prüfung genau wie im Starter)


def build_manifest(d):
    lines = []
    for rel in sorted(A.tree_files(d) - {A.MANIFEST, A.MANIFEST_SIG}):
        with open(os.path.join(d, rel), "rb") as f:
            lines.append(f"{hashlib.sha256(f.read()).hexdigest()}  {rel}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def sign_dir(seed, d):
    man = build_manifest(d)
    A.parse_manifest(man)                                   # gleiche Regeln wie beim Prüfen (Pfade, laerm.py vorhanden)
    sig = GL.ed25519_sign(seed, A.SIG_CONTEXT + man)
    with open(os.path.join(d, A.MANIFEST), "wb") as f:
        f.write(man)
    with open(os.path.join(d, A.MANIFEST_SIG), "w") as f:
        f.write(sig.hex() + "\n")
    return man.count(b"\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("key", nargs="?", help="Datei mit dem privaten Schlüssel (32 Byte hex)")
    ap.add_argument("dir", help="App-Ordner (enthält laerm.py)")
    ap.add_argument("--check", action="store_true", help="nur prüfen (mit dem eingebauten öffentlichen Schlüssel)")
    a = ap.parse_args()
    if a.check:
        A.RUN_DIR = os.path.join(os.path.abspath(a.dir), ".check_tmp")
        try:
            with open(os.path.join(a.dir, A.MANIFEST), "rb") as f:
                man = f.read()
            with open(os.path.join(a.dir, A.MANIFEST_SIG), "rb") as f:
                sig = f.read()
        except OSError as e:
            raise SystemExit(f"fehlt: {e}")
        ok = A.check_signature(man, sig) and build_manifest(a.dir) == man
        print("Signatur gültig" if ok else "NICHT gültig (Signatur oder Dateien geändert)")
        raise SystemExit(0 if ok else 1)
    if not a.key:
        raise SystemExit("Schlüsseldatei fehlt")
    n = sign_dir(GL.read_seed(a.key), a.dir)
    print(f"{n} Dateien signiert: {os.path.join(a.dir, A.MANIFEST)} + {A.MANIFEST_SIG}")


if __name__ == "__main__":
    main()
