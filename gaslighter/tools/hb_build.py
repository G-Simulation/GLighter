#!/usr/bin/env python3
"""Handbuch bauen: handbuch/<de|en>/NN-slug.md -> app/web/hb_inhalt.js (für die Seite „📖 Handbuch“ in der App)
und DOCS.md (Reiter „Dokumentation“ des Add-ons in Home Assistant). Beides kommt aus derselben Quelle.
Aufruf im Add-on-Ordner: python3 tools/hb_build.py [--docs ../docs]
Mit --docs entsteht zusätzlich das Handbuch fürs GitHub-Repository (docs/de, docs/en, Bilder aus app/web/hb)."""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ("de", "en")


def chapters(lang):
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "handbuch", lang, "[0-9][0-9]-*.md"))):
        slug = os.path.basename(f)[3:-3]
        md = open(f, encoding="utf-8").read().strip() + "\n"
        m = re.search(r"^#\s+(.+)$", md, re.M)
        out.append({"slug": slug, "title": m.group(1).strip() if m else slug, "md": md})
    return out


def plain(md):
    """Für DOCS.md: keine Bilder, Verweise innerhalb des Handbuchs als Text, keine {#anker}."""
    md = re.sub(r"^!\[[^\]]*\]\([^)]*\)\s*$\n?", "", md, flags=re.M)
    md = re.sub(r"\[([^\]]+)\]\(#[^)]*\)", r"\1", md)
    md = re.sub(r"\s*\{#[a-z0-9_-]+\}", "", md)
    md = re.sub(r"\[\[([^\]]+)\]\]", r"\1", md)
    md = re.sub(r"^(#{1,2})(\s)", r"#\1\2", md, flags=re.M)          # Kapitel = Ebene 2
    return md.strip() + "\n"


def github(md, lang, slugs, hbrel):
    """Für GitHub: Bilder aus dem Add-on-Ordner, Verweise auf die Kapiteldateien, {#anker} als HTML-Anker."""
    md = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", lambda m: "![%s](%s/%s)" % (m.group(1), hbrel, m.group(2).split("/")[-1].replace("{lang}", lang)), md)
    def link(m):
        t, h = m.group(1), m.group(2)
        sl, _, a = h[1:].partition("/")
        if sl in slugs:
            return "[%s](%s%s)" % (t, slugs[sl], "#" + a if a else "")
        return "[%s](#%s)" % (t, h[1:])
    md = re.sub(r"\[([^\]]+)\]\((#[^)]*)\)", link, md)
    md = re.sub(r"^(#{1,6} .*?)[ \t]*\{#([a-z0-9_-]+)\}[ \t]*$", r'<a id="\2"></a>\n\n\1', md, flags=re.M)
    md = re.sub(r"\s*\{#([a-z0-9_-]+)\}", r'<a id="\1"></a>', md)
    md = re.sub(r"\[\[([^\]]+)\]\]", r"<kbd>\1</kbd>", md)
    return md


def docs(data, out):
    names = {"de": ("Handbuch", "Inhalt", "English"), "en": ("Manual", "Contents", "Deutsch")}
    idx = ["# GLighter – Handbuch / Manual\n"]
    for l in LANGS:
        d = os.path.join(out, l); os.makedirs(d, exist_ok=True)
        for f in glob.glob(os.path.join(d, "*.md")):
            os.remove(f)
        files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "handbuch", l, "[0-9][0-9]-*.md")))
        slugs = {f[3:-3]: f for f in files}
        hbrel = os.path.relpath(os.path.join(ROOT, "app", "web", "hb"), d).replace(os.sep, "/")
        toc = []
        for i, (c, fn) in enumerate(zip(data[l], files)):
            prv = files[i - 1] if i else None; nxt = files[i + 1] if i + 1 < len(files) else None
            nav = " · ".join(x for x in ["[← %s](%s)" % (data[l][i - 1]["title"], prv) if prv else "", "[%s](README.md)" % names[l][1], "[%s →](%s)" % (data[l][i + 1]["title"], nxt) if nxt else ""] if x)
            open(os.path.join(d, fn), "w", encoding="utf-8").write(github(c["md"], l, slugs, hbrel).rstrip() + "\n\n---\n" + nav + "\n")
            toc.append("%d. [%s](%s)" % (i + 1, c["title"], fn))
        other = "en" if l == "de" else "de"
        open(os.path.join(d, "README.md"), "w", encoding="utf-8").write("# GLighter – %s\n\n%s\n\n## %s\n\n%s\n" % (names[l][0], "[%s](../%s/README.md)" % (names[l][2], other), names[l][1], "\n".join(toc)))
        idx.append("- **%s:** [%s](%s/README.md)" % ("Deutsch" if l == "de" else "English", names[l][0], l))
    open(os.path.join(out, "README.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")


def main():
    data = {l: chapters(l) for l in LANGS}
    assert [c["slug"] for c in data["de"]] == [c["slug"] for c in data["en"]], "Kapitel de/en passen nicht zusammen"
    js = "/* erzeugt von tools/hb_build.py aus handbuch/ – nicht von Hand ändern */\nwindow.HB = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    open(os.path.join(ROOT, "app", "web", "hb_inhalt.js"), "w", encoding="utf-8").write(js)
    parts = ["# GLighter (Lärmprotokoll / Noise Log)\n",
             "Das vollständige Handbuch mit Bildern, Suche und Querverweisen steht in der App unter **📖 Handbuch**. "
             "The full manual with pictures, search and links is in the app under **📖 Manual**.\n",
             "**Inhalt / Contents:** " + " · ".join(f"{i + 1}. {c['title']}" for i, c in enumerate(data["de"])) + "\n"]
    for l, head in (("de", "Deutsch"), ("en", "English")):
        parts.append(f"\n---\n\n# {head}\n")
        for i, c in enumerate(data[l]):
            parts.append(plain(c["md"]).replace("## " + c["title"], f"## {i + 1}. {c['title']}", 1))
    parts.append("\n---\n\n**Fremde Bestandteile / Third-party components:** uPlot (MIT, `app/web/uplot.LICENSE.txt`), YAMNet (Apache-2.0).\n")
    open(os.path.join(ROOT, "DOCS.md"), "w", encoding="utf-8").write("\n".join(parts))
    n = sum(len(c["md"]) for l in LANGS for c in data[l])
    if "--docs" in sys.argv:
        docs(data, os.path.abspath(sys.argv[sys.argv.index("--docs") + 1]))
    print(f"Handbuch: {len(data['de'])} Kapitel je Sprache, {n // 1024} KB Text -> app/web/hb_inhalt.js, DOCS.md")


if __name__ == "__main__":
    main()
