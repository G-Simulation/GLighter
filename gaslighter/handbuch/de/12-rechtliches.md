# Rechtliches und Datenschutz

> **Keine Rechtsberatung.** Die Rechtslage unterscheidet sich je nach Land. Im Zweifel einen Anwalt oder den Mieterverein fragen.

## Was gespeichert wird {#gespeichert}

- **Messwerte**: Pegel, Hintergrund, Schwelle, Frequenzbänder (23 Terzbänder) in 125-ms-Schritten. Aus dieser Auflösung lässt sich nach Forschungsergebnissen keine verständliche Sprache zurückgewinnen.
- **KI-Ergebnisse** und **KI-Fingerabdruck**: Zahlen, die beschreiben, wie es klingt – kein Ton, nicht zurückverwandelbar.
- **Deine Notizen**, Listen, Tonprofile, Zustände aus Home Assistant.
- Alles bleibt **auf deinem Rechner**. Es gibt keine Cloud und keine Übertragung an Dritte.

## Kein Ton, keine Spracherkennung {#kein-ton}

Ton liegt nur kurz im Arbeitsspeicher (Live-Anzeige, Erkennung) und wird laufend überschrieben. Bei Stimmen wird nur die **Art** erkannt, nie der Inhalt – eine Spracherkennung gibt es bewusst nicht.

> **Achtung § 201 StGB:** Das Aufnehmen des nichtöffentlich gesprochenen Worts kann strafbar sein, wenn es nicht nur zufällig geschieht. Bei einer Daueraufzeichnung Richtung Nachbarschaft ist das vorhersehbar. Deshalb ist „Echten Ton speichern“ standardmäßig aus und erst nach einem Hinweis einschaltbar. Heimliche Tonaufnahmen sind vor Gericht meist nicht verwertbar. Tonaufnahmen kommen nie ins Lärmprotokoll.

## Video {#video}

Kameraaufnahmen in Wohnungen können nach § 201a StGB problematisch sein. Nur eigene Räume filmen, keine fremden Personen, nicht in fremde Wohnungen oder den Hausflur.

## Aussagekraft {#aussagekraft}

- Pegel sind **dBFS** (relativ zur Soundkarte), keine geeichte Messung in dB(A).
- Überzeugend ist ein Protokoll, das **regelmäßig** geführt wird, **nachvollziehbar** ist (Uhrzeit, Dauer, Art, Auswirkung, Zeugen) und **unverändert** ist (Datenkette).
- Eigene Notizen („aufgewacht“, „Kind geweckt“) und Zeugen machen den Unterschied.

## Was die Aufzeichnung belegt und was nicht {#belegt}

> **Keine Rechtsberatung.** Die folgenden Punkte sind sachliche Hinweise aus veröffentlichten Entscheidungen und Fachbeiträgen. Sie versprechen keinen Erfolg vor Gericht. Für den Einzelfall eine Anwältin oder einen Anwalt, den Mieterverein oder eine Opferberatung fragen.

**Belegt werden kann:** wann es wie lange und wie laut (relativ, dBFS) war, wie oft und zu welchen Uhrzeiten – über Wochen und Monate, auch dass an ruhigen Tagen gemessen wurde. Dazu, dass die Tagesaufzeichnung seither unverändert ist (Prüfsummen).

**Nicht belegt werden kann:**

- **woher** ein Geräusch kommt und wer es verursacht – die Erkennung „Klopfen“ sagt nicht, aus welcher Wohnung,
- **wie laut in dB(A)** – das Mikrofon ist nicht kalibriert: Werte sind Indizien und ersetzen kein Gutachten,
- dass die **Geräuschart** stimmt, solange sie ein „Vorschlag der Erkennung“ ist – prüfe sie und bestätige oder korrigiere sie mit einem Klick in der Ereignisliste. Deine Bestätigung liegt getrennt (`bestaetigt.json`), die Einschätzung der Erkennung bleibt gespeichert.

**Was hilft:** Zeugen (Nachbarn, Hausverwaltung, Polizei), zeitnahe Notizen mit Zeitpunkt, Art, Intensität, Dauer und Häufigkeit, Meldungen mit Datum und Vorgangsnummer. In strittigen Fällen holen Gerichte eigene Gutachten ein – die Aufzeichnung kann zeigen, wann sich eine Messung lohnt.

**Prüfsummen** zeigen, dass die Daten seit der Aufzeichnung nicht verändert wurden; sie sind keine elektronische Signatur. Digitale Daten haben vor Gericht keine Echtheitsvermutung – lege deshalb Rohdaten (CSV) und Prüfsummen bei (Beweispaket, siehe [Drucken](#drucken/laermprotokoll)).

## Kurze Hinweise in der App {#hinweise}

Mit **💡 Hilfe anzeigen** (⚙ Einstellungen → Allgemein) erscheinen an einigen Stellen kurze Hinweise. Jeder lässt sich mit ✕ einzeln ausblenden; „Hilfe anzeigen“ aus blendet alle aus. **Warum?** nennt die Quelle.

| Wo | Hinweis | Quelle |
|---|---|---|
| Geräte (Einrichtung) | An einem festen Ort messen und eintragen, ob das Fenster offen oder geschlossen ist. | AG Wolfratshausen 5 C 274/20 |
| Ereignisliste | Erkannte Geräuscharten prüfen und bestätigen oder korrigieren; die Erkennung zeigt nicht, aus welcher Wohnung es kommt. | LG Berlin II 56 S 100/23 WEG |
| Aufzeichnung, Live | Auch an ruhigen Tagen messen – eine lückenlose Zeitreihe zeigt Häufigkeit und Muster glaubwürdiger. | BGH VIII ZR 1/16 Rn. 14; § 238 Abs. 2 StGB |
| Export, Lärmprotokoll | Messwerte als Indiz weitergeben und bei Streit ein Gutachten anregen. | AG München 472 C 18927/16; OLG Celle 4 U 199/09 |
| Export, Lärmprotokoll | Rohdaten (CSV) und Prüfsummen beilegen. | § 371 ZPO; Irskens, EDVGT 2024 |
| Allgemein | Keine heimlichen Ton- oder Videoaufnahmen von Nachbarn ergänzen. | BGH VI ZR 1370/20; BVerfG 1 BvR 1611/96; AG München 173 C 11834/23 |
| Allgemein | Nicht mit Gegenlärm antworten, sondern dokumentieren und den Rechtsweg gehen. | AG München 173 C 11834/23 |
