"""Oberflächen-Rauchtest: startet GasLighter mit Wegwerf-Daten, klickt durch die Hauptseiten und prüft, dass keine
JavaScript-Fehler auftreten und die Meldungen (Unterbrechungen) bestätigt werden können.
Aufruf:  python3 tests/smoke_ui.py      (braucht: pip install playwright, Chromium; unter Linux PLAYWRIGHT_BROWSERS_PATH setzen)"""
import datetime as dt, json, os, shutil, socket, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def main():
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(); port = free_port(); data = os.path.join(tmp, "data"); os.makedirs(data); os.makedirs(os.path.join(tmp, "out"))
    json.dump({"output_dir": os.path.join(tmp, "out"), "device": "default"}, open(os.path.join(tmp, "options.json"), "w"))
    json.dump({}, open(os.path.join(tmp, "settings.json"), "w"))
    now = dt.datetime.now().astimezone().replace(microsecond=0)
    iso = lambda d: d.isoformat(timespec="seconds")
    m = (now - now.replace(hour=0, minute=0, second=0)).total_seconds() / 60 - 2      # alles heute, auch kurz nach Mitternacht
    k = lambda x: dt.timedelta(minutes=x * min(1.0, m / 180))
    ev = [{"at": iso(now - k(180)), "kind": "stop"},
          {"kind": "down", "from": iso(now - k(120)), "to": iso(now - k(90)), "version_new": "9.9"},
          {"at": iso(now - k(30)), "kind": "update", "version_old": "9.8", "version_new": "9.9"}]
    open(os.path.join(data, "laufzeit.jsonl"), "w").write("\n".join(json.dumps(e) for e in ev) + "\n")
    env = dict(os.environ, LAERM_OPTIONS=os.path.join(tmp, "options.json"), LAERM_SETTINGS=os.path.join(tmp, "settings.json"),
               LAERM_SOURCES=os.path.join(data, "sources.json"), LAERM_PORT=str(port), LAERM_ALLOW_ALL="1", LAERM_PHONE_PORT="0")
    srv = subprocess.Popen([sys.executable, os.path.join(APP, "laerm.py")], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors, fails = [], []
    try:
        url = f"http://127.0.0.1:{port}/"
        for _ in range(60):
            try:
                urllib.request.urlopen(url, timeout=1); break
            except Exception:
                time.sleep(0.5)
        else:
            raise SystemExit("Server startet nicht")
        kw = {"executable_path": "/opt/pw-browsers/chromium"} if os.path.exists("/opt/pw-browsers/chromium") else {}
        with sync_playwright() as p:
            b = p.chromium.launch(**kw); pg = b.new_context(locale="de-DE", viewport={"width": 1300, "height": 900}).new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
            pg.goto(url); pg.wait_for_selector("#tab_prot"); pg.wait_for_timeout(800)
            pg.click("#tab_prot"); pg.wait_for_timeout(500)
            pg.click('#nper button[data-p="today"]'); pg.wait_for_timeout(1500)
            box = pg.locator("#nrun")
            if box.is_hidden():
                fails.append("Kasten Unterbrechungen nicht sichtbar")
            else:
                txt = box.inner_text()
                if "9.9" not in txt and "Nicht aufgezeichnet" not in txt:
                    fails.append("Stromausfall fehlt im Kasten: " + txt[:200])
                if "Update" in txt:
                    fails.append("Update sollte automatisch als gelesen gelten")
                btns = box.locator(".ackbtn:not([data-all])")
                if btns.count() < 1:
                    fails.append("kein Bestätigen-Knopf")
                else:
                    if os.environ.get("DEBUG"): print("VOR:", repr(box.inner_text()), box.get_attribute("class"))
                    btns.first.click(); pg.wait_for_timeout(1200)
                    if os.environ.get("DEBUG"): print("NACH:", repr(pg.locator("#nrun").inner_text()), pg.locator("#nrun").get_attribute("class"), pg.locator("#nrun").is_hidden())
                    if not pg.locator("#nrun.quiet").count() and not pg.locator("#nrun").is_hidden():
                        fails.append("Kasten zeigt nach Bestätigen noch offene Meldungen")
                    tog = pg.locator("#nrun .rtoggle")
                    if tog.count():
                        if not tog.first.is_visible():          # nichts Offenes: Kasten ist eingeklappt, erst aufklappen
                            pq = pg.locator(".pnl.pquiet .pcol")
                            if not pq.count():
                                fails.append("Kasten ohne offene Meldungen ist nicht eingeklappt")
                            else:
                                pq.first.click(); pg.wait_for_timeout(300)
                        tog.first.click(); pg.wait_for_timeout(800)
                        if os.environ.get("DEBUG"): print("ALLE:", repr(pg.locator("#nrun").inner_text()))
                        if "Nicht aufgezeichnet" not in pg.locator("#nrun").inner_text():
                            fails.append("Bestätigte lassen sich nicht anzeigen")
            pg.click("#sbtn"); pg.wait_for_timeout(1500)
            if not pg.evaluate("() => !!document.getElementById('dlg') && document.getElementById('dlg').open"):
                fails.append("Einstellungen öffnen sich nicht")
            elif pg.locator('fieldset[data-sec="s_mirror"] #mirnow').count() != 1:
                fails.append("Kasten tägliche Sicherung fehlt")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
            pg.click("#tab_live"); pg.wait_for_timeout(600)
            vb = pg.locator("#ldevvis")                                    # Tabelle: nur sichtbarer Bereich (an/aus)
            if vb.count() != 1 or "on" not in (vb.get_attribute("class") or ""):
                fails.append("Knopf Nur sichtbarer Bereich fehlt oder ist nicht an")
            else:
                vb.click(); pg.wait_for_timeout(800)
                if "on" in (vb.get_attribute("class") or "") or pg.locator("#ldevh").inner_text().strip() != "Ereignisse":
                    fails.append("Nur sichtbarer Bereich lässt sich nicht ausschalten")
                vb.click(); pg.wait_for_timeout(800)
            if pg.locator("#fnptags .ntadd").count() != 1:                # eigene Schnellwahl im Notiz-Feld
                fails.append("Knopf ＋ Eigene fehlt in der Schnellwahl")
            else:
                pg.click("#fnptags .ntadd"); pg.fill("#fnptags_qt .qtnew", "Waschmaschine"); pg.click("#fnptags_qt .qtaddok"); pg.wait_for_timeout(800)
                if not pg.locator('#fnptags .ntchip:has-text("Waschmaschine")').count():
                    fails.append("eigene Schnellwahl-Taste erscheint nicht")
            b.close()
    finally:
        srv.terminate()
        try:
            srv.wait(5)
        except Exception:
            srv.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    errs = [e for e in errors if "favicon" not in e]
    for e in errs:
        print("FEHLER:", e)
    for f in fails:
        print("FEHLER:", f)
    print("OK" if not errs and not fails else "NICHT OK")
    return 0 if not errs and not fails else 1


if __name__ == "__main__":
    sys.exit(main())
