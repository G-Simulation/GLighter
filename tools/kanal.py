#!/usr/bin/env python3
"""Zwei Apps im selben Repository:
  gaslighter/       = freigegebene Version (das bekommen alle)
  gaslighter_beta/  = Arbeitsversion „GasLighter Beta“ (eigene Entitäten, eigener Datenordner)

  python3 tools/kanal.py beta-config      config.yaml der Beta aus der stabilen ableiten (Name, Slug, Port, Ordner, Version)
  python3 tools/kanal.py freigeben        Beta-Stand in die stabile App übernehmen (Version ohne „-beta.N“)
Die Freigabe wird als Pull Request „Beta → freigegeben“ angelegt; erst der Klick auf „Merge“ verteilt sie an alle."""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST, BE = os.path.join(ROOT, "gaslighter"), os.path.join(ROOT, "gaslighter_beta")
PARTS = ["app", "handbuch", "tests", "tools", "translations", "Dockerfile", "run.sh", "build.yaml", "CHANGELOG.md", "DOCS.md", "icon.png", "logo.png"]


def ver(path):
    return re.search(r'^version: "([^"]+)"', open(os.path.join(path, "config.yaml"), encoding="utf-8").read(), re.M).group(1)


def beta_config(version=None):
    s = open(os.path.join(ST, "config.yaml"), encoding="utf-8").read()
    version = version or ver(BE)
    s = re.sub(r'^name: .*$', 'name: "GasLighter Beta"', s, count=1, flags=re.M)
    s = re.sub(r'^version: .*$', f'version: "{version}"', s, count=1, flags=re.M)
    s = re.sub(r'^slug: .*$', 'slug: gaslighter_beta', s, count=1, flags=re.M)
    s = re.sub(r'^description: "', 'description: "🧪 TESTVERSION / BETA – kann Fehler enthalten. Eigene Daten (/share/gaslighter_beta) und eigene Entitäten, läuft neben GasLighter. ', s, count=1, flags=re.M)
    s = s.replace("  8443/tcp: 18443", "  8443/tcp: 18444")
    s = re.sub(r'^panel_icon: .*$', 'panel_icon: mdi:flask', s, count=1, flags=re.M)
    s = re.sub(r'^panel_title: .*$', 'panel_title: "GasLighter Beta"', s, count=1, flags=re.M)
    s = s.replace('  output_dir: "/share/gaslighter"', '  output_dir: "/share/gaslighter_beta"')
    s = s.replace('# image: "ghcr.io/g-simulation/{arch}-gaslighter"', '# Beta wird immer von Home Assistant selbst gebaut')
    if "\nenvironment:" not in s:
        s = s.replace("\nhassio_api: true", "\nenvironment:\n  LAERM_CHANNEL: beta\nhassio_api: true", 1)
    open(os.path.join(BE, "config.yaml"), "w", encoding="utf-8").write(s)


def freigeben():
    v = ver(BE); stable = re.sub(r"-beta(\.\d+)?$", "", v)
    for p in PARTS:
        src, dst = os.path.join(BE, p), os.path.join(ST, p)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        elif os.path.isfile(src):
            shutil.copy2(src, dst)
    cf = os.path.join(ST, "config.yaml"); s = open(cf, encoding="utf-8").read()
    open(cf, "w", encoding="utf-8").write(re.sub(r'^version: .*$', f'version: "{stable}"', s, count=1, flags=re.M))
    lp = os.path.join(ST, "app", "laerm.py"); s = open(lp, encoding="utf-8").read()
    open(lp, "w", encoding="utf-8").write(re.sub(r'^VERSION = ".*"$', f'VERSION = "{stable}"', s, count=1, flags=re.M))
    print("freigegeben vorbereitet:", stable)


if __name__ == "__main__":
    {"beta-config": beta_config, "freigeben": freigeben}[sys.argv[1]]()
