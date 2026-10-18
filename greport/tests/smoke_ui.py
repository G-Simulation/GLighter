"""Oberflächen-Rauchtest GReport: Seite lädt ohne Fehler, Notiz speichern, Liste, Schnellwahl verwalten, Handy ohne Überbreite."""
import os, shutil, socket, subprocess, sys, tempfile, time, urllib.request

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")


def main():
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(); s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    env = dict(os.environ, GR_DIR=os.path.join(tmp, "share"), GR_PRIVATE=os.path.join(tmp, "priv"), GR_OPTIONS=os.path.join(tmp, "none.json"),
               GR_PORT=str(port), GR_ALLOW_ALL="1", GR_GLIGHTER_DIR=os.path.join(tmp, "nogl"))
    srv = subprocess.Popen([sys.executable, os.path.join(APP, "greport.py")], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors, fails = [], []
    try:
        url = f"http://127.0.0.1:{port}/"
        for _ in range(60):
            try:
                urllib.request.urlopen(url, timeout=1); break
            except Exception:
                time.sleep(0.3)
        kw = {"executable_path": "/opt/pw-browsers/chromium"} if os.path.exists("/opt/pw-browsers/chromium") else {}
        with sync_playwright() as p:
            b = p.chromium.launch(**kw)
            pg = b.new_context(locale="de-DE", viewport={"width": 1200, "height": 900}).new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
            pg.goto(url); pg.wait_for_selector("#fnptags .ntchip"); pg.wait_for_timeout(500)
            if pg.locator("#fnpsrcl").is_visible():
                fails.append("Quelle / Gerät sichtbar, obwohl GLighter nicht verbunden ist")
            pg.fill("#fnptext", "Bass dröhnt"); pg.click('#fnptags .ntchip[data-t="klopfen"]'); pg.click("#fnpsave"); pg.wait_for_timeout(800)
            if pg.locator("#grnotes .grn").count() != 1 or "Bass dröhnt" not in pg.locator("#grnotes").inner_text():
                fails.append("gespeicherte Notiz erscheint nicht in der Liste")
            pg.click("#grnotes .grn .gre"); pg.wait_for_timeout(300)
            if pg.input_value("#fnptext") != "Bass dröhnt" or not pg.locator("#fnpcancel").is_visible():
                fails.append("Ändern füllt die Notiz-Leiste nicht")
            pg.click("#fnpcancel"); pg.click("#fnptags .ntadd"); pg.fill("#fnptags_qt .qtnew", "Waschmaschine"); pg.click("#fnptags_qt .qtaddok"); pg.wait_for_timeout(600)
            if not pg.locator('#fnptags .ntchip:has-text("Waschmaschine")').count():
                fails.append("eigene Schnellwahl-Taste erscheint nicht")
            if any("fnp_" in x or "gr_" in x for x in [pg.locator("#fnpsec").inner_text(), pg.locator("#fnpmsg").inner_text()]):
                fails.append("Text-Schlüssel statt Text sichtbar")
            pg.click("#grmenu"); pg.wait_for_timeout(200)
            if pg.locator("#grmenul button").count() < 5:
                fails.append("Menü unvollständig")
            mp = b.new_context(locale="de-DE", viewport={"width": 375, "height": 760}, is_mobile=True, has_touch=True).new_page()
            mp.on("pageerror", lambda e: errors.append("pageerror (Handy): " + str(e)))
            mp.goto(url); mp.wait_for_selector("#fnptags .ntchip"); mp.wait_for_timeout(500)
            if mp.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth") > 1:
                fails.append("Handy: Seite breiter als der Bildschirm")
            b.close()
    finally:
        srv.terminate()
        try:
            srv.wait(5)
        except Exception:
            srv.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    for e in errors + fails:
        print("FEHLER:", e)
    print("OK" if not errors and not fails else "NICHT OK")
    return 0 if not errors and not fails else 1


if __name__ == "__main__":
    sys.exit(main())
