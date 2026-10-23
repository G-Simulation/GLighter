"""GReport: Bericht für Dritte (Zusammenfassung, Ereignis- und Erfassungszeit mit markiertem Abstand, Zeugen mit Rolle,
Polizei/Meldungen/Atteste, Zeitachse mit leeren Tagen, Gewaltschutz-Fassung), Zeit-Tasten ab Erfassungsbeginn, Zeitquelle."""
import io, os, shutil, sys, tempfile, unittest, zipfile
import datetime as dt

D = tempfile.mkdtemp()
os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import greport as G  # noqa: E402


def ms(y, mo, d, h, mi=0, s=0):
    return int(dt.datetime(y, mo, d, h, mi, s).astimezone().timestamp() * 1000)


def iso(y, mo, d, h, mi=0, s=0):
    return dt.datetime(y, mo, d, h, mi, s).astimezone().isoformat(timespec="seconds")


class Basis(unittest.TestCase):
    def setUp(self):
        G.NOTES["data"] = None; G.QT["data"] = None; G.PROTO["state"] = None; G.ATT["data"] = None
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)


class Bericht(Basis):
    def test_inhalt(self):
        G.write_json(os.path.join(G.DIR, "personen.json"), {"list": ["Anna"], "info": {"Anna": {"r": "nachbar", "c": "Tel. 0171 1"}}})
        G.note_change("add", {"text": "Bass", "tags": ["musik", "stark", "oben"], "witness": "Anna", "from": iso(2026, 10, 1, 22), "to": iso(2026, 10, 1, 23, 30),
                              "cap": ms(2026, 10, 1, 23, 31), "ext": {"freq": "jede Nacht", "pol": True, "pol_nr": "AZ 123", "health": "kein Schlaf"}})
        G.note_change("add", {"text": "Drohung im Treppenhaus", "from": iso(2026, 10, 4, 18), "cap": ms(2026, 10, 6, 9),
                              "ext": {"threat": True, "rep_to": "hv", "rep_date": "2026-10-05", "attest": "Hausarzt, 06.10.", "wrole": "polizei", "wcontact": "PI Mitte"},
                              "witness": "Herr B"})
        t0, t1 = ms(2026, 10, 1, 0), ms(2026, 10, 5, 23, 59)
        rb = G.report_build(False, t0, t1)
        z = rb["zusammenfassung"]
        self.assertEqual((z["vorfaelle"], z["tage_mit_eintrag"], z["tage_im_zeitraum"]), (2, 2, 5))
        self.assertEqual(z["intensitaet"]["stark"], 1); self.assertEqual(z["dauer"]["gesamt_min"], 90); self.assertEqual(z["drohung_gewalt"], 1)
        self.assertEqual(z["spaet_notiert"], 1)
        v = rb["vorfaelle"]; self.assertEqual(v[0]["text"], "Bass"); self.assertEqual(v[1]["abstand_h"], 39.0)       # großer Abstand sichtbar
        self.assertEqual(v[0]["zeugen"][0], {"name": "Anna", "rolle": "nachbar", "erreichbar": "Tel. 0171 1"})          # Rolle aus der Personenliste
        self.assertEqual(v[1]["zeugen"][0]["rolle"], "polizei")
        self.assertEqual([d["anzahl"] for d in rb["tage"]], [1, 0, 0, 1, 0])                                         # Tage ohne Eintrag
        txt = G.report_text(rb)
        for s_ in ("1. Zusammenfassung", "⚠ erst 39.0 Std. nach dem Ereignis", "Anna – Nachbar – Tel. 0171 1", "Polizei, Vorgang AZ 123", "Meldung an Hausverwaltung",
                   "Attest: Hausarzt, 06.10.", "– kein Eintrag", "Häufigkeit (eigene Angaben): jede Nacht", "Keine Rechtsberatung", "nachträgliche Manipulation ist erkennbar"):
            self.assertIn(s_, txt)
        for bad in ("gerichtsfest", "rechtssicher"):
            self.assertNotIn(bad, txt.lower())
        gs = G.report_build(True, t0, t1)
        self.assertTrue(gs["vorfaelle"][0]["drohung_gewalt"])                                                         # Drohung/Gewalt zuerst
        gt = G.report_text(gs); self.assertIn("Gewaltschutzantrag", gt); self.assertNotIn("Zeitachse", gt)
        zf = zipfile.ZipFile(io.BytesIO(G.report_zip(True, t0, t1)))
        self.assertTrue({"bericht.txt", "bericht.json", "rohdaten.csv", "notizen_protokoll.jsonl"} <= set(zf.namelist()))
        self.assertTrue(any(n.startswith("greport_nachweis_") for n in zf.namelist()))


class ZeitTasten(Basis):
    def test_ab_erfassungsbeginn(self):
        cap = dt.datetime(2026, 10, 23, 14, 32, 10).astimezone()          # erstes Tippen
        a5 = G.when_apply_full("w_5", cap)[0]; a15 = G.when_apply_full("w_15", cap)[0]
        self.assertEqual(a5, iso(2026, 10, 23, 14, 27, 10))                 # sekundengenau ab Erfassungsbeginn
        self.assertEqual(a15, iso(2026, 10, 23, 14, 17, 10))                # zweite Taste: wieder ab Erfassungsbeginn, nicht ab der ersten
        f, t, nt, ap = G.when_apply_full("w_eve", cap)
        self.assertEqual((f, t, nt, ap), (iso(2026, 10, 22, 18), iso(2026, 10, 22, 22), False, True))
        f, t, nt, ap = G.when_apply_full("w_night", dt.datetime(2026, 10, 23, 3, 0).astimezone())   # mitten in der Nacht: bis jetzt
        self.assertEqual((f, t), (iso(2026, 10, 22, 22), iso(2026, 10, 23, 3)))
        G.qt_change({"action": "wadd", "k": "t_aaaaaa", "l": "um 6", "at": "6:00"}); G.qt_change({"action": "wadd", "k": "t_bbbbbb", "l": "vor 30", "m": 30})
        self.assertEqual(G.when_apply_full("t_aaaaaa", cap)[0], iso(2026, 10, 23, 6))
        self.assertEqual(G.when_apply_full("t_aaaaaa", dt.datetime(2026, 10, 23, 5, 0).astimezone())[0], iso(2026, 10, 22, 6))   # die letzte, die schon war
        self.assertEqual(G.when_apply_full("t_bbbbbb", cap)[0], iso(2026, 10, 23, 14, 2, 10))
        self.assertEqual(G.when_apply_full("w_none", cap)[2], True)

    def test_gespeichert_mit_erfassungszeit(self):
        cap = ms(2026, 10, 23, 14, 32, 10)
        n = G.note_change("add", {"text": "Bass", "from": iso(2026, 10, 23, 14, 27, 10), "cap": cap, "wk": "w_5", "wl": "vor 5 Min."})["note"]
        self.assertEqual((n["cap"], n["wk"], n["wl"]), (cap, "w_5", "vor 5 Min.")); self.assertNotIn("approx", n)
        self.assertIn("erfasst 23.10.2026 14:32:10", G.export_text("txt")); self.assertIn("Zeit per Taste gesetzt (vor 5 Min.)", G.export_text("txt"))
        e = G.note_change("edit", {"id": n["id"], "text": "Bass laut", "from": n["from"], "cap": cap, "wk": "w_5", "wl": "vor 5 Min."})["note"]
        self.assertEqual(e["cap"], cap)                                     # Erfassungszeit bleibt beim Ändern
        x = G.note_change("add", {"text": "alt", "from": iso(2026, 10, 1, 1), "cap": 5})["note"]; self.assertNotIn("cap", x)   # ungültig = weg


class Zeitquelle(Basis):
    def test_ntp(self):
        G.CLOCK.update(t=G.time.time(), v={"ntp": True, "sync": True, "tz": "Europe/Berlin"})
        self.assertIn("NTP): ja", G.clock_text())
        G.CLOCK.update(t=G.time.time(), v={"ntp": True, "sync": False})
        self.assertIn("NTP): nein", G.proto_verify()["clock"])
        G.CLOCK.update(t=G.time.time(), v=None)
        self.assertIn("nicht bekannt", G.clock_text()); self.assertIn("Home Assistant", G.clock_text())


if __name__ == "__main__":
    unittest.main()
