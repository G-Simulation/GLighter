"""GReport Anlagen: ablegen (unverändert, mit SHA-256), Grenzen, Dateiart, Papierkorb, Protokoll und Prüfen (manipulierte Datei
wird erkannt), Sicherung und Export mit Prüfsummen, Text lesen (docx/odt/eml, Schutz vor ZIP-Bomben), Vorschläge und Übernahme."""
import hashlib, io, json, os, shutil, sys, tempfile, time, unittest, zipfile
import datetime as dt

D = tempfile.mkdtemp()
os.environ.update(GR_DIR=os.path.join(D, "share"), GR_PRIVATE=os.path.join(D, "priv"), GR_OPTIONS=os.path.join(D, "none.json"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
import greport as G  # noqa: E402
import dokument as DOK  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
TXT = "Lärmprotokoll\n12.03.2025\n23:15 Bass dröhnt von oben, Anna hat es gehört.\n23:40–23:55 Tür knallt.\n".encode("utf-8")


def up(data, name, **kw):
    return G.att_upload(io.BytesIO(data), len(data), name, **kw)


def wait_scan(aid):
    for _ in range(100):
        if G.SCAN.get(aid, {}).get("state") != "run":
            return
        time.sleep(0.05)


def mkzip(path, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, c in files.items():
            z.writestr(n, c)


class Basis(unittest.TestCase):
    def setUp(self):
        G.NOTES["data"] = None; G.QT["data"] = None; G.PROTO["state"] = None; G.ATT["data"] = None; G.SCAN.clear()
        shutil.rmtree(G.DIR, ignore_errors=True); os.makedirs(G.DIR)
        self.old_pro, self.old_opt = G.pro_ok, dict(G.OPT)

    def tearDown(self):
        G.pro_ok = self.old_pro; G.OPT.clear(); G.OPT.update(self.old_opt)


class Ablage(Basis):
    def test_unveraendert_mit_pruefsumme(self):
        n = G.note_change("add", {"text": "Bass", "from": "2026-10-20T22:00:00+02:00"})["note"]
        r = up(PNG, "Foto vom Flur (1).png", desc="Zettel an der Tür", note_ids=[n["id"], "gibt_es_nicht"])
        self.assertTrue(r["ok"], r); f = r["file"]
        p = G.att_path(G.att_get(f["id"]))
        self.assertTrue(p.startswith(os.path.join(G.DIR, "anlagen", str(dt.date.today().year), f["id"] + "_Foto_vom_Flur_1")))
        with open(p, "rb") as fh:
            self.assertEqual(fh.read(), PNG)                                      # Original unverändert
        self.assertEqual(f["sha256"], hashlib.sha256(PNG).hexdigest()); self.assertEqual(f["size"], len(PNG))
        self.assertEqual(f["notes"], [n["id"]]); self.assertEqual(f["desc"], "Zettel an der Tür")
        self.assertEqual(G.read_json(G.att_index_path())["files"][0]["sha256"], f["sha256"])   # Verzeichnis als JSON
        self.assertEqual(G.notes_list()[0]["att"][0]["id"], f["id"])               # 📎 an der Notiz
        e = [x for x in G.proto_read() if x["op"] == "file_add"][0]; self.assertEqual(e["file"]["sha256"], f["sha256"])
        self.assertTrue(G.proto_verify()["ok"])

    def test_grenzen_und_dateiart(self):
        self.assertEqual(up(b"MZ\x90\x00", "virus.exe")["error"], "kind")
        self.assertEqual(up(b"kein pdf", "brief.pdf")["error"], "type")             # Inhalt passt nicht zur Endung
        self.assertEqual(up(b"", "leer.txt")["error"], "empty")
        G.OPT["attach_max_mb"] = 1
        self.assertEqual(G.att_upload(io.BytesIO(b"x"), 2 * G.MB, "gross.txt")["error"], "too big")
        G.OPT["attach_max_mb"] = 25; G.OPT["attach_total_mb"] = 10
        self.assertTrue(G.att_upload(io.BytesIO(b"a" * (6 * G.MB)), 6 * G.MB, "a.txt")["ok"])
        self.assertEqual(G.att_upload(io.BytesIO(b"b" * (5 * G.MB)), 5 * G.MB, "b.txt")["error"], "full")      # zusammen höchstens 10 MB
        self.assertEqual(G.att_upload(io.BytesIO(b"kurz"), 100, "c.txt")["error"], "incomplete")
        self.assertEqual(len(G.att_all()["files"]), 1)
        self.assertFalse([f for f in os.listdir(os.path.join(G.DIR, "anlagen", str(dt.date.today().year))) if f.endswith(".part")])
        for k in ("txt", "pdf", "jpg", "png", "heic", "docx", "odt", "eml"):
            self.assertIn(k, set(DOK.KINDS.values()))

    def test_papierkorb_und_protokoll(self):
        f = up(TXT, "brief.txt")["file"]
        self.assertTrue(G.att_change({"action": "desc", "id": f["id"], "desc": "Brief vom Vermieter"})["ok"])
        self.assertTrue(G.att_change({"action": "del", "id": f["id"]})["file"]["del"])
        st = G.att_state(); self.assertEqual(st["files"], []); self.assertEqual(st["trash"][0]["id"], f["id"])
        self.assertTrue(os.path.exists(G.att_path(G.att_get(f["id"]))))               # Datei bleibt
        G.att_change({"action": "restore", "id": f["id"]})
        self.assertEqual([e["op"] for e in G.proto_read() if e["op"].startswith("file_")], ["file_add", "file_edit", "file_del", "file_restore"])
        self.assertTrue(G.proto_verify()["ok"])

    def test_manipulierte_datei_wird_erkannt(self):
        f = up(TXT, "brief.txt")["file"]
        p = G.att_path(G.att_get(f["id"])); os.chmod(p, 0o644)
        with open(p, "ab") as fh:
            fh.write(b"nachtraeglich")
        v = G.proto_verify(); self.assertFalse(v["ok"])
        self.assertTrue(any("verändert" in x["what"] or "changed" in x["what"] for x in v["problems"]))
        os.remove(p)
        self.assertTrue(any("fehlt" in x["what"] or "missing" in x["what"] for x in G.proto_verify()["problems"]))

    def test_verzeichnis_manipuliert(self):
        up(TXT, "brief.txt")
        d = G.read_json(G.att_index_path()); d["files"][0]["sha256"] = "0" * 64; G.write_json(G.att_index_path(), d)
        self.assertTrue(any("weichen" in x["what"] or "differ" in x["what"] for x in G.proto_verify()["problems"]))

    def test_sicherung_export_bericht(self):
        n = G.note_change("add", {"text": "Bass", "from": "2026-10-20T22:00:00+02:00"})["note"]
        f = up(PNG, "foto.png", note_ids=[n["id"]])["file"]
        z = zipfile.ZipFile(io.BytesIO(G.backup_zip()))                              # frei, mit Anlagen
        names = z.namelist(); self.assertIn("anlagen/anlagen.json", names)
        self.assertEqual(z.read(G.att_get(f["id"])["file"].join(["anlagen/", ""])), PNG)
        self.assertNotIn(G.att_get(f["id"])["file"].join(["anlagen/", ""]), zipfile.ZipFile(io.BytesIO(G.backup_zip(files=False))).namelist())
        txt = G.export_text("txt"); self.assertIn(f["sha256"], txt); self.assertIn("Anlage: foto.png", txt)
        self.assertIn(f["sha256"], G.export_csv().decode("utf-8"))
        self.assertEqual(json.loads(G.export_text("json"))["anlagen"][0]["sha256"], f["sha256"])
        rows, _ = G.parse_import(txt); self.assertEqual(rows[0]["text"], "Bass")          # Re-Import stört der Vermerk nicht
        rz = zipfile.ZipFile(io.BytesIO(G.report_zip()))
        self.assertIn("anlagen/" + G.att_get(f["id"])["file"], rz.namelist()); self.assertIn(f["sha256"], rz.read("bericht.txt").decode("utf-8"))


class TextLesen(Basis):
    def test_docx(self):
        p = os.path.join(D, "a.docx")
        w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        mkzip(p, {"word/document.xml": f'<?xml version="1.0"?><w:document xmlns:w="{w}"><w:body><w:p><w:r><w:t>Seite 1</w:t></w:r></w:p>'
                                       f'<w:p><w:r><w:br w:type="page"/><w:t>12.03.2025 um 23:15 Uhr Bass</w:t></w:r></w:p></w:body></w:document>'})
        r = DOK.extract(p, "docx"); self.assertEqual(len(r["pages"]), 2); self.assertIn("23:15", r["pages"][1])
        h = DOK.find_times(r["pages"], dt.date(2025, 3, 14)); self.assertEqual((h[0]["page"], h[0]["line"]), (2, 1))

    def test_odt(self):
        p = os.path.join(D, "a.odt"); tx = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
        mkzip(p, {"content.xml": f'<?xml version="1.0"?><office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="{tx}">'
                                 f'<office:body><office:text><text:h>Protokoll</text:h><text:p>12.03.2025<text:s/>23:15 <text:span>Tür</text:span></text:p></office:text></office:body></office:document-content>'})
        self.assertEqual(DOK.extract(p, "odt")["pages"][0], "Protokoll\n12.03.2025 23:15 Tür")

    def test_zip_bombe_und_entitaeten(self):
        p = os.path.join(D, "bombe.docx")
        mkzip(p, {"word/document.xml": "<a>" + "x" * (DOK.ZIP_MAX_XML + 10) + "</a>"})
        with self.assertRaises(DOK.ExtractError) as c:
            DOK.extract(p, "docx")
        self.assertEqual(c.exception.code, "zip")
        mkzip(p, {"word/document.xml": '<?xml version="1.0"?><!DOCTYPE a [<!ENTITY x "xxxxxxxx"><!ENTITY y "&x;&x;&x;">]><a>&y;</a>'})
        with self.assertRaises(DOK.ExtractError) as c:
            DOK.extract(p, "docx")
        self.assertEqual(c.exception.code, "xml")
        mkzip(p, {f"f{i}": "" for i in range(DOK.ZIP_MAX_ENTRIES + 1)})
        with self.assertRaises(DOK.ExtractError):
            DOK.extract(p, "docx")
        with open(p, "wb") as f:
            f.write(b"PK\x03\x04kaputt")
        with self.assertRaises(DOK.ExtractError):
            DOK.extract(p, "odt")

    def test_eml_mit_datum(self):
        p = os.path.join(D, "a.eml")
        with open(p, "w", encoding="utf-8") as f:
            f.write("From: a@b.de\nTo: c@d.de\nSubject: Ruhestörung\nDate: Fri, 14 Mar 2025 08:00:00 +0100\nContent-Type: text/plain; charset=utf-8\n\n"
                    "Gestern Nacht um 2 Uhr war wieder Musik.\n")
        r = DOK.extract(p, "eml"); self.assertEqual(r["date"].date(), dt.date(2025, 3, 14)); self.assertIn("Betreff: Ruhestörung", r["pages"][0])
        h = DOK.find_times(r["pages"], r["date"]); self.assertEqual(h[0]["from"][:16], "2025-03-14T02:00")

    @unittest.skipUnless(DOK.tools()["pdftotext"], "pdftotext fehlt")
    def test_pdf_original_bleibt(self):
        pdf = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
               b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 100]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj "
               b"4 0 obj<</Length 52>>stream\nBT /F1 12 Tf 10 50 Td (12.03.2025 23:15 Bass) Tj ET\nendstream endobj "
               b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n")
        f = up(pdf, "brief.pdf")["file"]
        G.att_scan(f["id"]); wait_scan(f["id"])
        x = G.att_get(f["id"]); self.assertTrue(x.get("txt"), G.SCAN.get(f["id"]))
        with open(G.att_path(x), "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), f["sha256"])     # Original unberührt
        self.assertIn("23:15", open(G.att_path(x, "txt"), encoding="utf-8").read())


class Vorschlaege(Basis):
    def test_vorschlaege_und_uebernahme(self):
        G.write_json(os.path.join(G.DIR, "personen.json"), {"list": ["Anna"]})
        f = up(TXT, "protokoll.txt", mtime=int(dt.datetime(2025, 3, 14, 9).timestamp() * 1000))["file"]
        self.assertEqual(G.att_scan(f["id"])["state"], "run"); wait_scan(f["id"])
        x = G.att_get(f["id"])
        with open(G.att_path(x, "txt"), "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), x["txt"]["sha256"])   # erkannter Text mit eigener Prüfsumme
        with open(G.att_path(x), "rb") as fh:
            self.assertEqual(fh.read(), TXT)
        self.assertIn("file_text", [e["op"] for e in G.proto_read()])
        s = G.doc_suggest(f["id"]); self.assertEqual(s["state"], "done"); self.assertTrue(s["doc_date_known"])
        sg = s["suggestions"]; self.assertEqual(len(sg), 2)
        self.assertEqual((sg[0]["from"][:16], sg[0]["page"], sg[0]["line"], sg[0]["conf"]), ("2025-03-12T23:15", 1, 3, "genau"))
        self.assertIn("oben", sg[0]["tags"]); self.assertIn("musik", sg[0]["tags"]); self.assertEqual(sg[0]["witness"], "Anna")
        self.assertEqual(sg[1]["to"][:16], "2025-03-12T23:55"); self.assertIn("tuer", sg[1]["tags"])
        self.assertEqual(G.notes_all()["free"], [])                                   # nichts angelegt
        self.assertEqual(G.doc_apply({"id": f["id"], "items": sg})["error"], "pro")    # Übernehmen = Pro (wie der Import)
        G.pro_ok = lambda: True
        t0 = int(time.time() * 1000)
        r = G.doc_apply({"id": f["id"], "items": [dict(sg[0], text="Bass dröhnt (geprüft)")]}); self.assertEqual(r["n"], 1)
        n = G.notes_list()[0]
        self.assertEqual(n["text"], "Bass dröhnt (geprüft)"); self.assertEqual(n["src_doc"]["id"], f["id"]); self.assertEqual((n["src_doc"]["page"], n["src_doc"]["line"]), (1, 3))
        self.assertGreaterEqual(n["cap"], t0)                                         # Erfassungszeit = Übernahme
        self.assertEqual(n["src_doc"]["doc_t"][:10], "2025-03-14")                    # Zeit des Dokuments getrennt
        self.assertEqual(n["by"], "dokument"); self.assertIn("aus Dokument erkannt", G.export_text("txt"))
        self.assertIn(n["id"], G.att_get(f["id"])["notes"])
        s2 = G.doc_suggest(f["id"])["suggestions"]; self.assertEqual(s2[0]["dup"], n["id"]); self.assertIsNone(s2[1]["dup"])   # doppelt markiert
        self.assertTrue(G.proto_verify()["ok"])

    def test_doppelt_im_dokument(self):
        data = "12.03.2025 23:15 Bass dröhnt\n12.03.2025 23:18 Bass dröhnt\n12.03.2025 23:50 Tür\n".encode()
        f = up(data, "a.txt")["file"]; G.att_scan(f["id"]); wait_scan(f["id"])
        sg = G.doc_suggest(f["id"])["suggestions"]
        self.assertEqual([x["dup_of"] for x in sg], [None, 0, None])

    def test_fehler_wird_gemeldet(self):
        f = up(b"PK\x03\x04kaputt" + b"\x00" * 30, "kaputt.docx")["file"]
        G.att_scan(f["id"]); wait_scan(f["id"])
        s = G.doc_suggest(f["id"]); self.assertEqual((s["state"], s["error"]), ("err", "format"))
        self.assertTrue(G.proto_verify()["ok"])


if __name__ == "__main__":
    unittest.main()
