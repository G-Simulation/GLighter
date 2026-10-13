#!/usr/bin/env python3
"""GasLighter – Lizenzschlüssel erzeugen (nur für G-Simulation, nicht Teil der App).

  python3 gl_license.py keygen  gaslighter_private.key      neues Schlüsselpaar; zeigt den öffentlichen Schlüssel
  python3 gl_license.py sign    gaslighter_private.key  --order 1234 [--until 2027-10-13 | --days 365] [--customer x]
  python3 gl_license.py check   GL1-....                     Schlüssel prüfen (mit dem in der App eingebauten öffentlichen Schlüssel)

Der private Schlüssel (32 Byte, hex) gehört nur auf den Lizenzserver (ERPNext) und in eine sichere Sicherung –
nie ins Repository, nie in die App. Wer ihn hat, kann gültige Schlüssel erzeugen.
"""
import argparse, base64, datetime, hashlib, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
import lizenz as L  # noqa: E402


def _secret_to_pub(seed):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8; a |= 1 << 254
    return a, h[32:], L._compress(L._mul(a, L._B))


def ed25519_sign(seed, msg):
    a, prefix, pub = _secret_to_pub(seed)
    r = L._h(prefix + msg) % L._L
    R = L._compress(L._mul(r, L._B))
    k = L._h(R + pub + msg) % L._L
    S = (r + k * a) % L._L
    return R + int.to_bytes(S, 32, "little")


def make_key(seed, order, until, customer=""):
    data = {"p": L.PRODUCT, "e": until.isoformat(), "n": str(order), "i": datetime.date.today().isoformat()}
    if customer:
        data["k"] = str(customer)
    js = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    body = bytes([1]) + len(js).to_bytes(2, "big") + js
    raw = base64.b32encode(body + ed25519_sign(seed, body)).decode().rstrip("=")
    return L.pretty(raw)


def read_seed(path):
    s = open(path).read().strip()
    seed = bytes.fromhex(s)
    if len(seed) != 32:
        raise SystemExit("privater Schlüssel muss 32 Byte (64 Hex-Zeichen) lang sein")
    return seed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("keygen"); g.add_argument("file")
    s = sub.add_parser("sign"); s.add_argument("file"); s.add_argument("--order", required=True)
    s.add_argument("--until"); s.add_argument("--days", type=int, default=365); s.add_argument("--customer", default="")
    c = sub.add_parser("check"); c.add_argument("key")
    a = ap.parse_args()
    if a.cmd == "keygen":
        if os.path.exists(a.file):
            raise SystemExit(a.file + " gibt es schon – nicht überschrieben")
        seed = os.urandom(32)
        fd = os.open(a.file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, (seed.hex() + "\n").encode()); os.close(fd)
        print("privater Schlüssel:   ", a.file, "(geheim halten!)")
        print("öffentlicher Schlüssel:", _secret_to_pub(seed)[2].hex())
    elif a.cmd == "sign":
        seed = read_seed(a.file)
        if _secret_to_pub(seed)[2].hex() != L.PUBLIC_KEY_HEX:
            print("Warnung: dieser private Schlüssel passt nicht zum öffentlichen Schlüssel in app/lizenz.py", file=sys.stderr)
        until = datetime.date.fromisoformat(a.until) if a.until else datetime.date.today() + datetime.timedelta(days=a.days)
        print(make_key(seed, a.order, until, a.customer))
    else:
        print(json.dumps(L.check(a.key), ensure_ascii=False))


if __name__ == "__main__":
    main()
