"""
Befunde -- was gilt, ohne einer einzelnen Karte zu gehoeren.

**Die einzige Stelle in diesem Produkt, an der die Vorauswahl nicht
gilt.** Der Grund steht in docs/aufbau.md, Abschnitt 2, und er ist der
eigentliche Nutzen: *Was liegen bleibt, liegt gerade in dem Projekt, in
das seit Wochen niemand geschaut hat.* Ein Befund, der nur das gewaehlte
Projekt kennt, zeigte ihn nie -- er meldete Ruhe, wo keine ist.

Zwei Anforderungen folgen daraus, und beide sind leicht zu uebersehen:

- **Ein Befund nennt sein Projekt.** Ueber alle Projekte gerechnet ist
  eine Meldung ohne diese Angabe wertlos: Man wuesste, dass etwas liegt,
  aber nicht wo. Und der Weg dorthin gehoert an die Karte -- wer sie
  anklickt, landet im richtigen Projekt.
- **Zur Kenntnis genommen wird je Projekt, nicht je Befund.** Sonst
  naehme das Stillstellen in einem Projekt dieselbe Lage in einem
  anderen mit, und ein Befund verschwaende, den nie jemand gesehen hat.
  Deshalb gibt es je Projekt EINE Karte und nicht eine gemeinsame mit
  einer Liste darin.

**Drei Stufen, eine Ampel** (docs/gestaltung.md). Welche gilt, haengt
nicht daran, wie schlimm etwas klingt, sondern daran, *wann jemand
handeln muss*:

    fehler    Das Werkzeug erfuellt seine Aufgabe nicht -- jetzt handeln.
    warnung   Eingeschraenkt oder darauf zulaufend -- bald handeln.
    info      Wissenswert; niemand muss deswegen aufstehen.

**Rot gibt es hier vorerst nicht, und das ist kein Versehen.** In MARLEI
Boot ist Rot der Server, der nicht bootet -- eine Maschine, die ihre
Arbeit nicht tut. Hier taete das nur eine Ablage, die sich nicht
schreiben laesst; dann steht aber ohnehin keine Seite mehr. Was hier
gemeldet wird, ist von anderer Art: **Es fehlt etwas, das nachwachsen
kann** -- und genau dafuer ist Gelb da. *Sperren gehoert zu dem, was
nicht nachwachsen kann; mahnen zu dem, was nachwaechst.*

Was hier steht, ist die *Entscheidung*: ob ein Befund gilt, welche Stufe
er hat, und mit welchem Satz er zugeklappt dasteht. Die Erklaerung
darunter steht in ``templates/befunde/<kennung>.html`` -- dort, wo aller
andere Text der Oberflaeche auch steht. Die Zahlen kommen aus
``datenbank.befundzahlen()``.
"""

from __future__ import annotations

import datenbank

# Die Reihenfolge, in der die Karten stehen, wenn mehrere gleichzeitig
# gelten: dringend zuerst, von oben nach unten.
STUFEN = ("fehler", "warnung", "info")

# Rot ist nie wegklickbar -- hier gibt es zwar keines, aber die Regel
# steht mit, weil sie zur Mechanik gehoert und nicht zum Vorrat.
WEGKLICKBAR = ("warnung", "info")


def _menge(zahl: int, eins: str, viele: str) -> str:
    """"1 Aufgabe" gegen "3 Aufgaben" -- eine Eins ist kein "1 Aufgaben".

    Faellt erst an echten Daten auf, und dann auf jeder Karte. Dieselbe
    Ueberlegung wie beim Loeschschritt unter Projekte.
    """
    return "%d %s" % (zahl, eins if zahl == 1 else viele)


# Der Vorrat. Je Eintrag:
#
#   kennung   heisst auch die Vorlage: templates/befunde/<kennung>.html
#   stufe     warnung | info
#   feld      welche Zahl aus datenbank.befundzahlen() ihn ausloest
#   titel     bekommt Projektname und Zahl -- er nennt die FOLGE, nicht
#             den Vorgang: Zugeklappt ist er das Einzige, was jemand
#             sieht, und "3 Aufgaben ohne Feld X" sagt nicht, was daran
#             schlimm ist.
#   ziel      wohin die Karte fuehrt, samt Anker auf die richtige Karte
KATALOG = (
    {"kennung": "liegeprobe", "stufe": "warnung", "feld": "liegt",
     "eins": "Entscheidung ist getroffen, und es liegt trotzdem",
     "viele": "Entscheidungen sind getroffen, und es liegt trotzdem",
     "ziel": "/entscheidungen#liegeprobe"},
    {"kennung": "ohne_ursache", "stufe": "warnung", "feld": "ohne_ursache",
     "eins": "Aufgabe sagt nicht, was dahintersteckt",
     "viele": "Aufgaben sagen nicht, was dahintersteckt",
     "ziel": "/aufgaben#aufgaben"},
    {"kennung": "luecken", "stufe": "warnung", "feld": "luecken",
     "eins": "Fehler steht ohne die verlangten Angaben da",
     "viele": "Fehler stehen ohne die verlangten Angaben da",
     "ziel": "/sammlung#sammlung"},
    {"kennung": "ohne_aufgabe", "stufe": "warnung", "feld": "ohne_aufgabe",
     "eins": "Meilenstein hat keine Aufgabe unter sich",
     "viele": "Meilensteine haben keine Aufgabe unter sich",
     "ziel": "/meilensteine#meilensteine"},
    {"kennung": "ohne_satz", "stufe": "warnung", "feld": "ohne_satz",
     "eins": "Entschluss sagt nicht, was entschieden wurde",
     "viele": "Entschlüsse sagen nicht, was entschieden wurde",
     "ziel": "/entscheidungen#entscheidungen"},
    # Der einzige, der nichts vermisst, sondern etwas misst -- und der,
    # wegen dem die Befunde ueberhaupt ueber alle Projekte laufen.
    {"kennung": "durchsicht", "stufe": "info", "feld": "durchsicht_her",
     "ziel": "/sammlung?ansicht=durchsicht#durchsicht"},
)

KENNUNGEN = tuple(e["kennung"] for e in KATALOG)


def sortiert(befunde: list[dict]) -> list[dict]:
    """Nach Stufe ordnen, dann nach Projekt.

    ``STUFEN.index`` laesst einen Tippfehler in der Stufe auffliegen,
    statt die Karte still an die falsche Stelle zu setzen: Die Befunde
    entstehen hier im Code und nicht aus einer Eingabe -- ein Fehler an
    dieser Stelle ist einer von uns und soll laut sein.
    """
    return sorted(befunde, key=lambda b: (STUFEN.index(b["stufe"]),
                                          b["projekt_id"],
                                          KENNUNGEN.index(b["kennung"])))


def sammeln(conn) -> list[dict]:
    """Alle Befunde, die gerade gelten -- geordnet, oben der dringendste.

    Jeder Befund traegt:

        stufe       warnung | info
        kennung     heisst auch die Vorlage
        projekt_id  fuer das Wegklicken UND fuer den Weg dorthin
        projekt     der Name, denn eine Meldung ohne ihn ist wertlos
        titel       der Satz, der zugeklappt dasteht
        marke       eine Zahl, die NUR steigt, wenn es schlimmer wird
        zahl        wie viele es sind (beim Durchsicht-Befund: Tage)
        ziel        wohin die Karte fuehrt

    **Nicht gepuffert**, anders als die Serverdetails. Ein
    zwischengespeicherter Befund, der veraltet, waere genau das, was
    diese Oberflaeche sonst vermeidet: Wer eine Luecke gerade
    nachgetragen hat, soll die Karte nicht noch zehn Sekunden lang sehen.
    Gerechnet wird auf einer lokalen Datei, und die Alternative waere
    keine Ersparnis, sondern eine Unwahrheit auf Zeit.
    """
    befunde: list[dict] = []
    for p in datenbank.befundzahlen(conn):
        for eintrag in KATALOG:
            zahl = p[eintrag["feld"]]

            if eintrag["kennung"] == "durchsicht":
                # Kein Vermerk heisst NICHT "seit null Tagen" -- es
                # heisst, es hat noch nie eine Durchsicht gegeben. Bei
                # einem frisch angelegten Projekt ist das keine Meldung
                # wert; bei einem, in dem etwas liegt, schon.
                if zahl is None:
                    if p["bestand"] == 0:
                        continue
                    zahl = datenbank.tage_seit(_angelegt(conn, p["projekt_id"]))
                if zahl is None or zahl < datenbank.DURCHSICHT_FRIST:
                    continue
                titel = ("%s: seit %s hat hier niemand hineingesehen"
                         % (p["name"], _menge(zahl, "Tag", "Tagen")))
                # GROB, und das ist der Sinn: Die Karte kommt erst nach
                # einem weiteren Monat zurueck. Eine Marke, die mit jedem
                # Tag steigt, waere kein Wegklicken, sondern ein Aufschub
                # bis morgen.
                marke = zahl // datenbank.DURCHSICHT_FRIST
            else:
                if not zahl:
                    continue
                titel = "%s: %s" % (p["name"],
                                    _menge(zahl, eintrag["eins"],
                                           eintrag["viele"]))
                marke = zahl

            befunde.append({
                "stufe": eintrag["stufe"],
                "kennung": eintrag["kennung"],
                "projekt_id": p["projekt_id"],
                "projekt": p["name"],
                "projekt_kennung": p["kennung"],
                "titel": titel,
                "marke": marke,
                "zahl": zahl,
                "ziel": eintrag["ziel"],
            })
    return sortiert(befunde)


def _angelegt(conn, projekt_id: int) -> str:
    zeile = conn.execute("SELECT eingetragen_am FROM projekte WHERE id = ?",
                         (projekt_id,)).fetchone()
    return zeile["eingetragen_am"] if zeile else ""


def teilen(conn, befunde: list[dict]) -> tuple[list[dict], list[dict]]:
    """Trennt die geltenden Befunde in offene und zur Kenntnis genommene.

    **Weggeklickt heisst nicht weg:** Die Karte schrumpft auf eine graue
    Zeile ueber der Seite. Wer nicht selbst geklickt hat, findet den
    Befund also trotzdem -- nur leise.

    **Weggeklickt heisst ausserdem: "ich weiss Bescheid, bis es schlimmer
    wird."** Steigt die Marke ueber die gemerkte, ist es ein neuer Befund
    und die Karte kommt zurueck. Eine Frist gibt es bewusst nicht: Jede
    Zahl darin waere gegriffen, und "sieben Tage" beantwortet keine
    Frage, die jemand hat.

    Nebenbei wird vergessen, was gerade nicht gilt -- **war ein Befund
    weg und kommt wieder, ist er neu.**
    """
    gelten = {(b["projekt_id"], b["kennung"]) for b in befunde}
    datenbank.kenntnis_aufraeumen(conn, gelten)
    stand = datenbank.kenntnis_stand(conn)

    offen: list[dict] = []
    bekannt: list[dict] = []
    for b in befunde:
        gemerkt = stand.get((b["projekt_id"], b["kennung"]))
        if (b["stufe"] in WEGKLICKBAR and gemerkt is not None
                and int(b["marke"]) <= gemerkt):
            bekannt.append(b)
        else:
            offen.append(b)
    return offen, bekannt
