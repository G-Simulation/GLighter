"""GReport: Datums- und Zeitangaben in Dokumenten erkennen (deutsch und englisch, relativ zum Datum des Dokuments)."""
import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
os.environ.setdefault("TZ", "Europe/Berlin")
import dokument as D  # noqa: E402

REF = dt.date(2025, 3, 14)          # Freitag


def hm(iso):
    return iso[:16].replace("T", " ") if iso else ""


def one(text, ref=REF, known=True):
    hs = D.find_times([text], ref, known)
    assert len(hs) == 1, (text, hs)
    h = hs[0]
    return hm(h["from"]), hm(h["to"]), h["conf"], h


class Formate(unittest.TestCase):
    def test_genaue_angaben(self):
        cases = [
            ("Am 12.03.2025 um 23:15 Uhr war es laut.", "2025-03-12 23:15", "", "genau"),
            ("12.03.25 23:15 Bass", "2025-03-12 23:15", "", "genau"),
            ("2025-03-12 23:15–23:40 Musik", "2025-03-12 23:15", "2025-03-12 23:40", "genau"),
            ("12.03.2025, 23.15 Uhr Tür", "2025-03-12 23:15", "", "genau"),
            ("Mittwoch, 12.03.2025 um 22:00 Schritte", "2025-03-12 22:00", "", "genau"),
            ("Mi., 12.03.2025 22:00 Schritte", "2025-03-12 22:00", "", "genau"),
            ("Zwischen 22 und 23 Uhr am 11.03.2025 Bohren", "2025-03-11 22:00", "2025-03-11 23:00", "genau"),
            ("On March 12, 2025 at 11:15 pm loud music", "2025-03-12 23:15", "", "genau"),
            ("from 10 pm to 1 am party on 12 March 2025", "2025-03-12 22:00", "2025-03-13 01:00", "genau"),
            ("12th March 2025, 7:05 am drilling", "2025-03-12 07:05", "", "genau"),
            ("12/03/2025 13:00 Hund", "2025-03-12 13:00", "", "unklar"),            # Tag/Monat vertauschbar
            ("25/03/2025 13:00 Hund", "2025-03-25 13:00", "", "genau"),
        ]
        for text, f, t, c in cases:
            with self.subTest(text=text):
                self.assertEqual(one(text)[:3], (f, t, c))

    def test_ueber_mitternacht(self):
        self.assertEqual(one("Am 12.03.2025 von 22 bis 1 Uhr Musik.")[:2], ("2025-03-12 22:00", "2025-03-13 01:00"))
        self.assertEqual(one("12.03.2025 23:50 - 0:20 Uhr Feier")[:2], ("2025-03-12 23:50", "2025-03-13 00:20"))
        self.assertEqual(one("12.03.2025 22–2 Uhr")[:2], ("2025-03-12 22:00", "2025-03-13 02:00"))

    def test_ungefaehr(self):
        self.assertEqual(one("12.03.2025 gegen 23 Uhr Bass")[2], "ungefaehr")
        self.assertEqual(one("12.03.2025 ca. 23:30 Uhr Bass")[:3], ("2025-03-12 23:30", "", "ungefaehr"))
        self.assertEqual(one("on 12 March 2025 around 11 pm")[:3], ("2025-03-12 23:00", "", "ungefaehr"))

    def test_jahr_aus_dem_zusammenhang(self):
        self.assertEqual(one("12.3. gegen 23 Uhr Bass")[:3], ("2025-03-12 23:00", "", "ungefaehr"))     # Jahr aus dem Dokumentdatum
        self.assertEqual(one("Am 12. März um 23:15 Musik")[:3], ("2025-03-12 23:15", "", "ungefaehr"))
        self.assertEqual(one("am 20.12. um 22:00", ref=dt.date(2025, 1, 5))[0], "2024-12-20 22:00")    # nach dem Dokument = Vorjahr
        hs = D.find_times(["Protokoll 2023\n03.01.2023 Beginn\n12.3. 23:00 Tür"], REF)
        self.assertEqual(hm(hs[1]["from"]), "2023-03-12 23:00"); self.assertEqual(hs[1]["conf"], "genau")  # zuletzt genanntes Jahr

    def test_relativ_zum_dokument(self):
        self.assertEqual(one("gestern Nacht um 2 Uhr Geschrei")[:3], ("2025-03-14 02:00", "", "ungefaehr"))
        self.assertEqual(one("gestern Nacht um 23 Uhr Geschrei")[0], "2025-03-13 23:00")
        self.assertEqual(one("Gestern Nacht war es laut.")[:3], ("2025-03-13 22:00", "2025-03-14 06:00", "ungefaehr"))
        self.assertEqual(one("gestern Abend um 21:30 Lärm")[0], "2025-03-13 21:30")
        self.assertEqual(one("vorgestern um 14:00 Bohren")[0], "2025-03-12 14:00")
        self.assertEqual(one("am Montag um 22:30 Tür geknallt")[:3], ("2025-03-10 22:30", "", "ungefaehr"))
        self.assertEqual(one("23 Uhr am Montag")[0], "2025-03-10 23:00")                      # „am“ hier nicht „a.m.“
        self.assertEqual(one("letzten Freitag um 20:00")[0], "2025-03-07 20:00")
        self.assertEqual(one("last night at 3 am shouting")[0], "2025-03-14 03:00")
        self.assertEqual(one("yesterday at 9:15 pm")[0], "2025-03-13 21:15")
        self.assertEqual(one("am Montag um 22:30", known=False)[2], "unklar")                   # ohne Dokumentdatum: unklar

    def test_wochentag_passt_nicht(self):
        self.assertEqual(one("Dienstag, 12.03.2025 um 23:00")[2], "unklar")

    def test_mehrere_und_zeilen_danach(self):
        hs = D.find_times(["Protokoll\n12.03.2025\n23:15 Bass dröhnt\n23:40 Tür knallt.\n\n13.03.2025 kein Vorfall"], REF)
        self.assertEqual([(hm(h["from"]), h["line"], h["date_only"]) for h in hs],
                         [("2025-03-12 23:15", 3, False), ("2025-03-12 23:40", 4, False), ("2025-03-13 00:00", 6, True)])
        self.assertEqual(hs[0]["text"], "Bass dröhnt")
        hs = D.find_times(["12.03.2025 um 22:10 und 23:30 Tür"], REF)                   # zwei Zeiten, kein Zeitraum
        self.assertEqual([hm(h["from"]) for h in hs], ["2025-03-12 22:10", "2025-03-12 23:30"]); self.assertEqual(hs[0]["to"], "")

    def test_seiten_und_satz(self):
        hs = D.find_times(["Seite eins ohne Datum.", "Hallo.\nAm 12.03.2025 um 23:15 Uhr klopfte es\nwieder an der Wand. Danach Ruhe."], REF)
        self.assertEqual((hs[0]["page"], hs[0]["line"]), (2, 2))
        self.assertEqual(hs[0]["sentence"], "Am 12.03.2025 um 23:15 Uhr klopfte es wieder an der Wand.")

    def test_nur_datum(self):
        f, t, c, h = one("Fr., 7.3.: Hund bellt")
        self.assertEqual((f, t, c, h["date_only"]), ("2025-03-07 00:00", "2025-03-07 23:59", "ungefaehr", True))
        self.assertEqual(one("Gestern Abend war Party.")[:2], ("2025-03-13 18:00", "2025-03-13 22:00"))

    def test_kein_treffer(self):
        for text in ("Die Rechnung 2024-13-40 ist ungültig", "Er kostete 12 Euro und 50 Cent", "Version 1.2.3 installiert", "Zimmer 12, Etage 3",
                     "Ich hatte 3 Stunden Schlaf", "Telefon 0171 2233445"):
            with self.subTest(text=text):
                self.assertEqual(D.find_times([text], REF), [])


if __name__ == "__main__":
    unittest.main()
