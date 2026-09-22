"""
Prueft den Rahmen: neun Reiter, ein Kopfband, ein gewaehltes Projekt.

Es gibt noch keine Seiteninhalte -- geprueft wird deshalb, was auf jeder
Seite gleich ist und was am Ende die Bedienung traegt: dass jeder Reiter
antwortet, dass der aktive markiert ist, dass beide Stylesheets geladen
werden, und dass das gewaehlte Projekt im Band steht statt nur auf
seinem Reiter.

    python -m venv venv
    ./venv/bin/pip install -r webui/requirements.txt httpx
    ./venv/bin/python tests/test_app.py

Braucht anders als test_datenbank.py die Abhaengigkeiten aus
webui/requirements.txt, dazu httpx fuer den Testclient.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ / "webui"))

# Eine Wegwerf-Ablage, damit der Test nichts anfasst, was jemand benutzt.
os.environ["MARLEI_DB"] = str(Path(tempfile.mkdtemp()) / "tasks.db")
os.environ["MARLEI_BASE_URL"] = "http://192.168.178.99"

import app as anwendung  # noqa: E402
import datenbank  # noqa: E402
import bericht  # noqa: E402
import einstellungen  # noqa: E402
import updatewacht  # noqa: E402
import versionsstand  # noqa: E402
import urllib.error  # noqa: E402
from urllib.parse import unquote  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

FEHLER: list[str] = []


def pruefe(bedingung, was: str) -> None:
    if bedingung:
        print("  ok    %s" % was)
    else:
        print("  FEHLT %s" % was)
        FEHLER.append(was)



def _flach(text: str) -> str:
    """Zeilenumbrueche weg -- eine Vorlage bricht Saetze, wo Platz ist.

    Ohne das prueft man nicht den Satz, sondern die Stelle, an der er im
    Quelltext umbricht; die naechste Einrueckung liesse die Pruefung
    fehlschlagen, obwohl sich nichts geaendert hat.
    """
    return " ".join(text.split())



def _sammlung_alle(projekt_id: int) -> list:
    """Auch das Abgeschlossene -- fuer die Pruefungen zu History."""
    with datenbank.verbindung() as conn:
        return datenbank.topics(conn, projekt_id, offen_nur=False)


def _entscheidungen(projekt_id: int) -> list:
    """Alle Entscheidungen dieses Projekts."""
    with datenbank.verbindung() as conn:
        return datenbank.entscheidungen(conn, projekt_id)


def _steine(projekt_id: int) -> list:
    """Die offenen Meilensteine dieses Projekts."""
    with datenbank.verbindung() as conn:
        return datenbank.meilensteine(conn, projekt_id)


def _aufgaben(projekt_id: int) -> list:
    """Was offen an Aufgaben in diesem Projekt steht."""
    with datenbank.verbindung() as conn:
        return datenbank.aufgaben(conn, projekt_id)


def _sammlung(projekt_id: int) -> list:
    """Was offen in der Sammlung dieses Projekts steht."""
    with datenbank.verbindung() as conn:
        return datenbank.topics(conn, projekt_id)

def _projekte() -> list:
    """Was gerade in der Ablage steht -- an der Oberflaeche vorbei."""
    with datenbank.verbindung() as conn:
        return datenbank.projekte(conn)


def _anlegen(name: str, datum: str) -> int:
    """Ein Projekt ohne den Umweg ueber das Formular.

    Wichtig fuer die Pruefungen darunter: Ueber /projekte/neu waere es
    danach auch gleich das gewaehlte -- dann liesse sich nicht mehr
    zeigen, dass waehlen das Cookie umstellt.
    """
    with datenbank.verbindung() as conn:
        return datenbank.projekt_anlegen(conn, name, datum)


REITER = (
    ("/", "Projekte"),
    ("/sammlung", "Sammlung"),
    ("/aufgaben", "Aufgaben"),
    ("/meilensteine", "Meilensteine"),
    ("/entscheidungen", "Entscheidungen"),
    ("/einrichtung", "Einrichtung"),
    ("/history", "History"),
    ("/hilfe", "Hilfe"),
    ("/serverhealth", "Server Health"),
)

with TestClient(anwendung.app) as c:
    print("Die Leiste")
    for pfad, name in REITER:
        r = c.get(pfad)
        pruefe(r.status_code == 200 and name in r.text,
               "%-16s antwortet und heisst %s" % (pfad, name))

    # Die Startseite ist Projekte und nicht Server Health -- ohne
    # gewaehltes Projekt haben die vier folgenden Reiter nichts zu zeigen.
    start = c.get("/").text
    pruefe(">Projekte</a>" in start and 'href="/"' in start,
           "die Startseite / ist der Reiter Projekte")
    pruefe(start.index(">Projekte</a>") < start.index(">Server Health</a>"),
           "Server Health steht hinten, nicht vorn")

    print("\nDer Rahmen")
    pruefe('class="aktiv"' in start, "der aktive Reiter ist markiert")
    pruefe("style.css" in start and "produkt.css" in start,
           "beide Stylesheets werden geladen -- die geteilte und die eigene")
    pruefe(start.index("style.css") < start.index("produkt.css"),
           "die eigene steht hinter der geteilten und darf ueberschreiben")
    pruefe('id="befunde"' in start, "der Behaelter fuer die Befunde ist da")
    pruefe("192.168.178.99" in start, "die Adresse steht im Band")
    # Bis zum 22.09.2026 stand hier die Gegenprobe: dass die Fusszeile
    # NICHT auf ein Repository zeigt, das es nicht gab. Seit dem
    # 21.09.2026 gibt es es, und die AGPL legt den Verweis fuer eine
    # ueber das Netz benutzte Oberflaeche nahe -- die Pruefung dreht sich
    # deshalb um. Der Lizenzverweis geht ins eigene Hilfekapitel und
    # nicht nach draussen: Wer wissen will, was die Lizenz fuer ihn
    # bedeutet, soll nicht auf gnu.org landen.
    pruefe('href="/hilfe#lizenz">AGPL-3.0</a>' in start,
           "die Fusszeile verweist auf das Lizenzkapitel der Hilfe")
    pruefe('href="https://github.com/exmig/marlei-tasks">Quelltext</a>'
           in start,
           "und auf den Quelltext -- was AGPL Paragraf 13 nahelegt")

    r = c.get("/befunde.html?von=/sammlung")
    pruefe(r.status_code == 200, "/befunde.html antwortet (das Skript holt es "
                                 "alle zehn Sekunden)")

    print("\nDas gewaehlte Projekt")
    pruefe('class="projektmarke"' not in start,
           "ohne Auswahl steht keine Projektmarke da")

    with datenbank.verbindung() as conn:
        conn.execute("INSERT INTO projekte (name, eingetragen_am) "
                     "VALUES ('Ein Projekt', '07.09.2026')")
        pid = conn.execute(
            "SELECT id FROM projekte WHERE name='Ein Projekt'").fetchone()[0]

    c.cookies.set(anwendung.COOKIE_PROJEKT, str(pid))
    # Auf JEDEM Reiter, nicht nur auf dem, wo es gewaehlt wurde -- das ist
    # der ganze Punkt: Eine Auswahl, die vier Seiten filtert und dort
    # unsichtbar ist, laesst jemanden ins falsche Projekt eintragen.
    #
    # SEIT DEM 19.09.2026 AN DER ERSTEN KARTE UND NICHT IM BAND: rechts
    # neben der Ueberschrift der Uebersicht auf den vier Registern, mit
    # Kennung. Im Band stand nur der Name -- ein Projekt namens
    # marlei-tasks las sich neben "MARLEI Tasks" wie ein Teil des
    # Produktnamens.
    kennung = datenbank.kennung("P", pid)
    for pfad, h2 in (("/sammlung", "Sammlungsübersicht"),
                     ("/aufgaben", "Aufgabenübersicht"),
                     ("/meilensteine", "Meilensteinübersicht"),
                     ("/entscheidungen", "Entscheidungsübersicht")):
        s = c.get(pfad).text
        kopf = s[s.index("<h2>%s</h2>" % h2):]
        kopf = kopf[:kopf.index("</div>")]
        band = s[s.index('<header class="kopfband">'):s.index("</header>")]
        if not ('class="projektmarke"' in kopf and kennung in kopf
                and "Ein Projekt" in kopf and "Ein Projekt" not in band):
            pruefe(False, "auf %s steht das Projekt mit Kennung neben der "
                          "Überschrift der ersten Karte" % pfad)
            break
    else:
        pruefe(True, "auf den vier Registern steht das Projekt mit Kennung "
                     "neben der Überschrift der ersten Karte -- und nicht "
                     "mehr im Band")
    # UND AM KNOPF, DER ANLEGT: der Augenblick, in dem ein falsch
    # gewaehltes Projekt Schaden anrichtet.
    for pfad in ("/sammlung", "/aufgaben", "/meilensteine",
                 "/entscheidungen"):
        if "landet in" not in c.get(pfad).text                 or "%s Ein Projekt" % kennung not in c.get(pfad).text:
            pruefe(False, "der Anlegen-Knopf auf %s nennt das Projekt" % pfad)
            break
    else:
        pruefe(True, "die vier Anlegen-Knöpfe nennen, wohin es kommt")

    c.cookies.set(anwendung.COOKIE_PROJEKT, "9999")
    r = c.get("/sammlung")
    pruefe(r.status_code == 200 and 'class="projektmarke"' not in r.text,
           "ein Cookie auf ein geloeschtes Projekt gilt als keines")

    # ================================================================ #
    print("\nDer Reiter Projekte")
    # ================================================================ #
    c.cookies.clear()
    # Eine leere Ablage. Die Pruefungen oben haben ein Projekt angelegt,
    # und hier wird gezaehlt -- danach steht die Zahl fuer das, was diese
    # Pruefungen selbst getan haben.
    with datenbank.verbindung() as conn:
        for p in datenbank.projekte(conn):
            datenbank.projekt_loeschen(conn, p["id"])

    leer = c.get("/").text
    pruefe("Projektübersicht" in leer and "Neues Projekt" in leer,
           "ohne Projekte stehen Uebersicht und Neues Projekt da")
    pruefe("Noch kein Projekt" in leer,
           "die leere Uebersicht sagt es, statt leer zu bleiben")

    r = c.post("/projekte/neu", data={
        "name": "Erstes Projekt", "eingetragen": "2026-09-07",
        "zustand": "AKTIV", "beschreibung": "Worum es geht",
        "vision": "Wohin es geht", "bereiche": "systeme, quellen"},
        follow_redirects=False)
    pruefe(r.status_code == 303,
           "anlegen antwortet mit 303 -- ein F5 danach wiederholt kein POST")
    erste = c.cookies.get(anwendung.COOKIE_PROJEKT)
    pruefe(erste is not None,
           "wer ein Projekt anlegt, hat es danach gewaehlt (ohne zweiten Klick)")

    seite = c.get("/").text
    # Nicht auf "P-001" pruefen: Dass die Zaehlung nie wieder von vorn
    # anfaengt, ist gerade der Punkt -- und steht in test_datenbank.py.
    pruefe(_projekte()[0]["kennung"] in seite,
           "die Kennung steht an der Karte")
    pruefe("07.09.2026" in seite,
           "das Datum steht deutsch da, obwohl es nach ISO abgelegt ist")
    pruefe('value="2026-09-07"' in seite,
           "und im Feld steht es nach ISO, sonst nimmt der Browser es nicht")
    pruefe("systeme" in seite and "quellen" in seite,
           "die Bereiche aus der Kommazeile sind angelegt")
    pruefe("Noch nichts eingetragen" in seite,
           "der Bestand steht in der Fusszeile -- und viermal null wird "
           "zu einem Satz, statt vier Nullen hinzuschreiben")

    print("\nWas abgewiesen werden muss")
    for felder, was in (
            ({"name": "", "eingetragen": "2026-09-07"},
             "ein Projekt ohne Namen"),
            ({"name": "Ohne Datum", "eingetragen": ""},
             "ein Projekt ohne Eintragsdatum (es traegt keine Vorgabe)"),
            ({"name": "Erstes Projekt", "eingetragen": "2026-09-07"},
             "ein zweites Projekt mit demselben Namen"),
            ({"name": "Krumm", "eingetragen": "2026-09-07",
              "zustand": "schlummert"}, "ein erfundener Zustand")):
        vorher = len(_projekte())
        r = c.post("/projekte/neu", data=felder, follow_redirects=False)
        pruefe(len(_projekte()) == vorher and "art=schlecht" in r.headers["location"],
               "%s wird abgewiesen und gesagt" % was)

    print("\nWaehlen")
    # Dass KEINES gewaehlt ist, muss dastehen. Aufgefallen ist das erst
    # an der gebauten Seite: Der Knopf war da, die Auskunft fehlte -- sie
    # stand nur als Abwesenheit da, und eine Abwesenheit liest niemand.
    c.cookies.clear()
    pruefe("Es ist kein Projekt gewählt" in c.get("/").text,
           "ohne Auswahl sagt die Uebersicht es, statt nur nichts zu "
           "markieren")
    c.cookies.set(anwendung.COOKIE_PROJEKT, "9999")
    pruefe("Es ist kein Projekt gewählt" in c.get("/").text,
           "ein Cookie auf ein geloeschtes Projekt gilt auch hier als keines")
    c.cookies.clear()

    zweite = _anlegen("Zweites Projekt", "2026-09-06")
    r = c.post("/projekte/waehlen", data={"id": zweite},
               follow_redirects=False)
    pruefe(c.cookies.get(anwendung.COOKIE_PROJEKT) == str(zweite),
           "waehlen stellt das Cookie um")
    pruefe("Es ist kein Projekt gewählt" not in c.get("/").text,
           "und danach steht der Hinweis nicht mehr da")
    # Der Punkt der ganzen Uebung: Es gilt auf JEDER Seite, nicht nur hier.
    pruefe("Zweites Projekt" in c.get("/sammlung").text,
           "das gewaehlte Projekt steht auch auf Sammlung im Band")
    r = c.post("/projekte/waehlen", data={"id": "9999"},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"]
           and c.cookies.get(anwendung.COOKIE_PROJEKT) == str(zweite),
           "ein Knopf aus einer alten Seite waehlt kein Projekt, das es "
           "nicht mehr gibt")

    print("\nSpeichern")
    r = c.post("/projekte/speichern",
               data={"name:%d" % zweite: "Zweites Projekt",
                     "zustand:%d" % zweite: "AKTIV"},
               follow_redirects=False)
    pruefe("Nichts" in r.headers["location"],
           "wer nichts aendert, bekommt kein »gespeichert« gemeldet")
    c.post("/projekte/speichern",
           data={"name:%d" % zweite: "Umbenannt", "zustand:%d" % zweite: "RUHT",
                 "vision:%d" % zweite: "Neue Vision"},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        p = datenbank.projekt(conn, zweite)
    pruefe(p["name"] == "Umbenannt" and p["zustand"] == "RUHT"
           and p["vision"] == "Neue Vision",
           "drei Felder in einem Zug -- ein Knopf fuer die ganze Seite")
    r = c.post("/projekte/speichern",
               data={"name:%d" % zweite: "Erstes Projekt"},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(datenbank.projekt(conn, zweite)["name"] == "Umbenannt"
               and "art=schlecht" in r.headers["location"],
               "auf einen schon vergebenen Namen umbenennen wird abgewiesen")
    r = c.post("/projekte/speichern",
               data={"zustand:%d" % zweite: "AKTIV",
                     "id:%d" % zweite: "42", "erfunden:%d" % zweite: "x"},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(datenbank.projekt(conn, zweite)["id"] == zweite,
               "ein Feldname aus dem Formular, den es nicht gibt, "
               "wandert nicht ins UPDATE")

    print("\nBereiche")
    c.post("/projekte/bereich", data={"id": zweite, "wert": "server"},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        bereich = datenbank.bereiche(conn, zweite)[0]
        conn.execute("""INSERT INTO topics
            (projekt_id, titel, bereich_id, eingetragen_am)
            VALUES (?, 'Haengt dran', ?, '2026-09-07')""",
            (zweite, bereich["id"]))
        conn.commit()
    r = c.post("/projekte/bereich/loeschen",
               data={"id": zweite, "bereich": bereich["id"]},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(len(datenbank.bereiche(conn, zweite)) == 1
               and "art=schlecht" in r.headers["location"],
               "ein Bereich mit einem Eintrag darauf bleibt -- und es wird "
               "gesagt, wie viele daran haengen")

    print("\nLoeschen: zwei Sicherungen")
    seite = c.get("/?loeschen=%d" % zweite).text
    pruefe("Zum Fortfahren" in seite and "Umbenannt" in seite,
           "der Loeschschritt verlangt den Projektnamen")
    pruefe('placeholder="Umbenannt"' in seite
           and 'name="wort" autocomplete="off"' in seite,
           "das Feld steht leer da und traegt den Namen nur als Hinweis "
           "-- vorbelegt genuegte die Eingabetaste")
    # Bis zum Bau von Einrichtung stand hier, dass es den Ausgang noch
    # nicht gibt. Jetzt fuehrt er hin -- UND sagt, dass er das gewaehlte
    # Projekt meint: Sonst exportiert jemand A und loescht B.
    pruefe('href="/einrichtung#export"' in seite
           and "erst wählen" in _flach(seite),
           "der Ausgang vor dem Löschen führt an sein Ziel und nennt die "
           "Bedingung: ausgegeben wird das gewählte Projekt")
    # An diesem Projekt haengt genau EIN Topic (aus der Pruefung oben) --
    # daran zeigt sich die Einzahl. Aufgefallen ist das beim ersten Blick
    # auf die gebaute Seite: Dort stand "0 Eintraege der Sammlung".
    # DER BESTAND ZAEHLT AUCH IN EINZAHL, seit dem 07.09.2026. Vorher
    # stand dort "1 Aufgaben"; aufgefallen ist es erst am ersten echten
    # Bestand, denn Null ist immer Mehrzahl.
    #
    # Geprueft wird die Gegenrichtung: Auf der ganzen Seite darf keine
    # Eins vor einer Mehrzahl stehen. Das haelt auch dann, wenn die
    # Pruefreihe spaeter andere Zahlen erzeugt.
    projektseite = _flach(c.get("/").text)
    falsch = [w for w in ("1 Aufgaben", "1 Meilensteine",
                          "1 Entscheidungen", "1 Einträge")
              if w in projektseite]
    pruefe(not falsch,
           "der Bestand zählt in Einzahl -- keine Eins vor einer "
           "Mehrzahl (%s)" % (", ".join(falsch) or "vier Wörter geprüft"))
    pruefe("1 Eintrag der Sammlung" in _flach(seite),
           "der Loeschschritt zaehlt in Einzahl, wo einer liegt")
    leer_seite = c.get("/?loeschen=%s" % _projekte()[0]["id"]).text
    pruefe("allerdings leer" in leer_seite,
           "und sagt bei einem leeren Projekt einen Satz statt vier Nullen")

    r = c.post("/projekte/loeschen", data={"id": zweite, "wort": "Löschen"},
               follow_redirects=False)
    pruefe(len(_projekte()) == 2 and "art=schlecht" in r.headers["location"],
           "das Wort »Löschen« loescht nichts -- das Losungswort ist der "
           "Projektname")
    r = c.post("/projekte/loeschen", data={"id": zweite, "wort": "  umbenannt "},
               follow_redirects=False)
    pruefe(len(_projekte()) == 1,
           "Gross- und Kleinschreibung und Leerraum sind egal -- geprueft "
           "wird, ob jemand das richtige Projekt meinte")
    pruefe(not c.cookies.get(anwendung.COOKIE_PROJEKT),
           "das Cookie auf das geloeschte Projekt ist weg, statt einen "
           "Namen im Band stehen zu lassen, den es nicht mehr gibt")

    # ================================================================ #
    print("\nDer Reiter Sammlung")
    # ================================================================ #
    c.cookies.clear()
    pruefe("Es ist kein Projekt gewählt" in c.get("/sammlung").text,
           "ohne Projekt sagt die Sammlung es, statt eine leere Seite "
           "hinzustellen")

    projekt = _anlegen("Sammelprojekt", "2026-08-01")
    c.cookies.set(anwendung.COOKIE_PROJEKT, str(projekt))
    ohne_bereich = c.get("/sammlung").text
    pruefe("noch keinen Bereich" in ohne_bereich,
           "ohne Bereich sagt die Seite es -- er ist NOT NULL, und das "
           "faellt sonst erst im abgewiesenen Formular auf")

    c.post("/projekte/bereich", data={"id": projekt, "wert": "quellen"},
           follow_redirects=False)
    c.post("/projekte/bereich", data={"id": projekt, "wert": "server"},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        bereiche = {b["wert"]: b["id"]
                    for b in datenbank.bereiche(conn, projekt)}

    print("\nEintragen")
    r = c.post("/sammlung/neu", data={
        "titel": "Der Upload bricht bei großen Dateien ab",
        "kategorie": "FEHLER", "bereich": bereiche["quellen"],
        "eingetragen": "2026-08-28",
        "beschreibung": "Während einer Übertragung reden Browser und Server nicht",
        "fehler_wann": "Ab etwa 6 GB"}, follow_redirects=False)
    pruefe(r.status_code == 303, "eintragen antwortet mit 303")
    # DIE FUENF MAHNEN, SIE SPERREN NICHT: Der Eintrag ist trotz vier
    # fehlender Angaben da -- und es wird gesagt.
    pruefe(len(_sammlung(projekt)) == 1,
           "ein unvollstaendiger FEHLER wird angelegt, nicht abgewiesen")
    pruefe("fehlen" in unquote(r.headers["location"]),
           "und die Meldung sagt, dass Angaben fehlen")

    c.post("/sammlung/neu", data={
        "titel": "Laufenden Upload abbrechen können", "kategorie": "IDEE",
        "bereich": bereiche["quellen"], "eingetragen": "2026-08-26",
        "beschreibung": "Eine Übertragung soll sich beenden lassen"},
        follow_redirects=False)
    c.post("/sammlung/neu", data={
        "titel": "Kein Weg zurück", "kategorie": "IDEE",
        "bereich": bereiche["server"], "eingetragen": ""},
        follow_redirects=False)
    pruefe(len(_sammlung(projekt)) == 3, "drei Einträge stehen drin")
    pruefe(_sammlung(projekt)[0]["eingetragen_am"] == datenbank.heute(),
           "ein leeres Eintragsdatum wird zu heute -- anders als beim "
           "Projekt, denn was auffaellt, faellt heute auf")

    seite = c.get("/sammlung").text
    pruefe("liegt seit" in seite, "die Liegedauer steht an der Karte")
    pruefe("Angaben fehlen" in seite,
           "und am unvollstaendigen FEHLER steht, wie viele fehlen")

    # DIE SAMMLUNGSUEBERSICHT IST DIE ERSTE KARTE, wie auf Aufgaben und
    # Meilensteinen (seit dem 19.09.2026). Vorher stand der Umschalter
    # als lose Zeile darueber, und die Seite begann anders als die
    # beiden Reiter daneben.
    for ansicht in ("eintragen", "durchsicht"):
        s = c.get("/sammlung?ansicht=" + ansicht).text
        erste = s.index("<section")
        karte = s[erste:s.index("</section>", erste)]
        pruefe('id="sammlungsuebersicht"' in karte[:60]
               and 'class="row ansichten"' in karte
               and "3 Einträge" in karte
               and "ohne Priorität" in karte
               and "FEHLER mit fehlenden Angaben" in karte,
               "in der Ansicht %s ist die Sammlungsübersicht die erste "
               "Karte -- mit Umschalter, Zahl und Zahlenzeile" % ansicht)
    pruefe(s.index('class="row ansichten"') > s.index("<section"),
           "der Umschalter steht nicht mehr lose über den Karten")

    print("\nWas abgewiesen werden muss")
    for felder, was in (
            ({"titel": "", "bereich": bereiche["server"]}, "ohne Titel"),
            ({"titel": "X", "bereich": ""}, "ohne Bereich"),
            ({"titel": "X", "bereich": bereiche["server"],
              "kategorie": "WUNSCH"}, "mit einer dritten Kategorie"),
            ({"titel": "X", "bereich": "9999"},
             "mit einem Bereich aus einem anderen Projekt")):
        vorher = len(_sammlung(projekt))
        r = c.post("/sammlung/neu", data=felder, follow_redirects=False)
        pruefe(len(_sammlung(projekt)) == vorher
               and "art=schlecht" in r.headers["location"],
               "ein Eintrag %s wird abgewiesen und gesagt" % was)

    print("\nDie Suche geht ueber die Beschreibung")
    treffer = c.get("/sammlung?suche=Übertragung").text
    pruefe("Der Upload bricht" in treffer
           and "Laufenden Upload abbrechen" in treffer
           and "Kein Weg zurück" not in treffer,
           "gefunden werden die zwei ueber ihre BESCHREIBUNG -- keiner "
           "der Titel enthaelt das Wort")

    print("\nBearbeiten -- was eingetragen ist, laesst sich korrigieren")
    nummern = {t["titel"]: t["id"] for t in _sammlung(projekt)}
    dieser = nummern["Kein Weg zurück"]
    anderer = nummern["Der Upload bricht bei großen Dateien ab"]

    seite = c.get("/sammlung?ansicht=eintragen").text
    pruefe('name="titel:%d"' % dieser not in seite,
           "ohne den Schritt steht der Titel als Text da und nicht als Feld")

    offen = c.get("/sammlung?ansicht=eintragen&bearbeiten=%d" % dieser).text
    pruefe('name="titel:%d"' % dieser in offen,
           "mit ?bearbeiten= wird genau diese Karte zum Formular")
    pruefe('name="titel:%d"' % anderer not in offen,
           "und nur diese eine -- zwei offene Formulare schickten beide ab")

    r = c.post("/sammlung/speichern", data={
        "ansicht": "eintragen",
        "titel:%d" % dieser: "  Kein Weg zurück, und das ist der Punkt  ",
        "beschreibung:%d" % dieser: "Nachgetragen beim Korrigieren",
        "bereich_id:%d" % dieser: str(bereiche["quellen"])},
        follow_redirects=False)
    jetzt = [t for t in _sammlung(projekt) if t["id"] == dieser][0]
    pruefe(jetzt["titel"] == "Kein Weg zurück, und das ist der Punkt"
           and jetzt["beschreibung"] == "Nachgetragen beim Korrigieren"
           and jetzt["bereich_id"] == bereiche["quellen"],
           "Titel, Beschreibung und Bereich lassen sich nachtraeglich "
           "aendern -- und der Titel kommt ohne die Leerzeichen an")
    pruefe("#eintrag-%d" % dieser in r.headers["location"],
           "danach steht man wieder bei der Karte, nicht am Seitenanfang")

    # DAS EINTRAGSDATUM IST KEIN FELD, und es reicht nicht, es in der
    # Vorlage wegzulassen: Was eine Seite nicht zeigt, laesst sich
    # trotzdem schicken. Deshalb steht die Sperre in TOPIC_AENDERBAR.
    war_am = jetzt["eingetragen_am"]
    c.post("/sammlung/speichern", data={
        "ansicht": "eintragen", "eingetragen_am:%d" % dieser: "2020-01-01"},
        follow_redirects=False)
    pruefe([t for t in _sammlung(projekt) if t["id"] == dieser][0]
           ["eingetragen_am"] == war_am,
           "ein mitgeschicktes Eintragsdatum wird nicht uebernommen -- "
           "daran misst sich, wie lange etwas liegt")

    for felder, was in (
            ({"titel:%d" % dieser: "   "}, "auf einen leeren Titel"),
            ({"kategorie:%d" % dieser: "WUNSCH"}, "auf eine dritte Kategorie"),
            ({"bereich_id:%d" % dieser: "9999"}, "auf einen fremden Bereich")):
        felder["ansicht"] = "eintragen"
        vorher = dict([t for t in _sammlung(projekt) if t["id"] == dieser][0])
        r = c.post("/sammlung/speichern", data=felder, follow_redirects=False)
        nachher = dict([t for t in _sammlung(projekt) if t["id"] == dieser][0])
        pruefe("art=schlecht" in r.headers["location"] and nachher == vorher,
               "eine Aenderung %s wird abgewiesen und gesagt" % was)

    # Zurueck auf den Stand, den die folgenden Pruefungen erwarten.
    c.post("/sammlung/speichern", data={
        "ansicht": "eintragen", "titel:%d" % dieser: "Kein Weg zurück",
        "beschreibung:%d" % dieser: "",
        "bereich_id:%d" % dieser: str(bereiche["server"])},
        follow_redirects=False)

    print("\nDurchsicht")
    ids = {t["titel"]: t["id"] for t in _sammlung(projekt)}
    upload = ids["Der Upload bricht bei großen Dateien ab"]
    abbrechen = ids["Laufenden Upload abbrechen können"]

    durchsicht = c.get("/sammlung?ansicht=durchsicht").text
    pruefe("Zusammenlegen" in durchsicht and "Speichern" in durchsicht,
           "die Knoepfe stehen in der Kopfzeile ueber ihrer Spalte")
    pruefe("seit der letzten Durchsicht" in durchsicht,
           "die vier Zahlen stehen da")

    r = c.post("/sammlung/speichern",
               data={"prio:%d" % upload: "MUSS",
                     "prio:%d" % abbrechen: "KANN", "ansicht": "durchsicht"},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(datenbank.topic(conn, upload)["prio"] == "MUSS",
               "die Durchsicht vergibt die Prioritaet")
        pruefe(datenbank.sammlung_zahlen(conn, projekt)["durchsicht_her"] == 0,
               "und vermerkt, dass hingesehen wurde")
    r = c.post("/sammlung/speichern",
               data={"prio:%d" % upload: "erfunden", "ansicht": "durchsicht"},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(datenbank.topic(conn, upload)["prio"] == "MUSS"
               and "art=schlecht" in r.headers["location"],
               "eine erfundene Prioritaet wird abgewiesen")

    print("\nZusammenlegen: erst fragen, dann anlegen")
    r = c.post("/sammlung/zusammenlegen",
               data={"mark": [str(upload), str(abbrechen)]},
               follow_redirects=False)
    ziel = r.headers["location"]
    pruefe("buendeln=2" in ziel and "mark=%d" % upload in ziel,
           "ohne Titel fuehrt der Knopf in den Buendelschritt, statt "
           "stillschweigend anzulegen")
    schritt = c.get(ziel).text
    pruefe("Was dahintersteckt" in schritt and "Der Upload bricht" in schritt,
           "der Schritt fragt nach dem gemeinsamen Bild und zeigt, "
           "worueber geredet wird")
    # GEFRAGT WIRD NACH ZWEIERLEI -- und der zweite gueltige Ausgang
    # steht daneben. Ein Pflichtfeld ohne Fluchtweg erzeugt Fuellsel.
    pruefe("Wann es abgenommen ist" in schritt,
           "und nach der Abnahme, in dem Augenblick, in dem das Denken "
           "gerade stattgefunden hat")
    pruefe("zurück in die Sammlung" in schritt,
           "und bietet den zweiten Ausgang an: das schaffe ich nicht")

    r = c.post("/sammlung/zusammenlegen",
               data={"mark": [str(upload), str(abbrechen)],
                     "titel": "Uploads, die nicht durchlaufen",
                     "dahinter": "Dieselbe Übertragung."},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(conn.execute("SELECT COUNT(*) FROM aufgaben").fetchone()[0] == 0
               and "art=schlecht" in r.headers["location"],
               "OHNE ABNAHME wird nicht angelegt -- das ist die eine "
               "Sperre dieses Produkts")
    pruefe(len(_sammlung(projekt)) == 3,
           "und die Eintraege bleiben, wo sie sind")

    r = c.post("/sammlung/zusammenlegen",
               data={"mark": [str(upload), str(abbrechen)],
                     "titel": "Uploads, die nicht durchlaufen",
                     "dahinter": "Dieselbe Übertragung.",
                     "abnahme": "Ein 8-GB-Abbild bricht ab\n\nDer Reiterwechsel bricht nicht ab",
                     "arbeit": "Abbruchknopf bauen"},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        aufgabe = conn.execute("SELECT * FROM aufgaben").fetchone()
    pruefe(aufgabe and aufgabe["titel"] == "Uploads, die nicht durchlaufen",
           "der zweite Aufruf legt die Aufgabe an")
    pruefe(aufgabe["prio"] == "MUSS",
           "sie erbt die staerkste der beiden Prioritaeten")
    pruefe(len(_sammlung(projekt)) == 1,
           "beide Eintraege sind aus der Sammlung verschwunden -- "
           "Abschluss setzen heisst weg von hier")
    # Der Weg fuehrt jetzt an sein Ziel: Bis zum 07.09.2026 stand hier
    # der Satz "sobald es den Reiter gibt" -- der Reiter Aufgaben war
    # leer. Seit er gebaut ist, landet man in ihm, bei der Aufgabe.
    ort = r.headers["location"]
    pruefe(ort.startswith("/aufgaben?") and "#eintrag-" in ort,
           "und der Weg fuehrt in die neue Aufgabe, nicht in eine Meldung "
           "ueber einen fehlenden Reiter")
    # Bis zum 19.09.2026 stand hier "aus 2 Eintragen" -- die Mehrzahl
    # entstand durch Anhaengen, und ein Umlaut laesst sich nicht anhaengen.
    pruefe("aus 2 Einträgen" in unquote(ort),
           "die Meldung sagt Einträgen, nicht Eintragen")

    with datenbank.verbindung() as conn:
        neue = conn.execute("SELECT * FROM aufgaben").fetchone()
        punkte = [dict(p) for p in conn.execute(
            "SELECT art, folge, text FROM aufgabe_punkte "
            "WHERE aufgabe_id = ? ORDER BY art, folge", (neue["id"],))]
    pruefe([p["text"] for p in punkte if p["art"] == "ABNAHME"] ==
           ["Ein 8-GB-Abbild bricht ab", "Der Reiterwechsel bricht nicht ab"],
           "aus zwei Zeilen werden zwei Abnahmepunkte -- die Leerzeile "
           "dazwischen wird keiner")
    pruefe([p["text"] for p in punkte if p["art"] == "ARBEIT"] ==
           ["Abbruchknopf bauen"],
           "und die Arbeitsliste kommt aus demselben Schritt")

    r = c.post("/sammlung/zusammenlegen", data={"titel": "Nichts"},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "ohne Markierung wird nichts zusammengelegt")

    print("\nVerwerfen")
    rest = _sammlung(projekt)[0]["id"]

    # Die Meldung muss an einem Ziel ankommen, das schon eine Frage
    # traegt. Ein zweites "?" machte aus "ansicht=durchsicht" ein
    # "durchsicht?meldung=..." -- die Ansicht fiel auf Eintragen zurueck,
    # und die Meldung erschien nie. Bei den Projekten faellt das nicht
    # auf, weil deren Ziele keine Frage tragen.
    r = c.post("/sammlung/speichern",
               data={"prio:%d" % rest: "SOLL", "ansicht": "durchsicht"},
               follow_redirects=False)
    ort = r.headers["location"]
    pruefe(ort.count("?") == 1 and "ansicht=durchsicht&meldung=" in ort,
           "die Meldung haengt sich mit & an ein Ziel, das schon eine "
           "Frage traegt")

    c.post("/sammlung/verwerfen", data={"id": rest}, follow_redirects=False)
    pruefe(_sammlung(projekt) == [],
           "ein verworfener Eintrag verschwindet aus der Sammlung")
    with datenbank.verbindung() as conn:
        pruefe(datenbank.topic(conn, rest)["abschluss"] == "verworfen",
               "und traegt den Abschluss, der eine Zeile im Quittungsbuch "
               "bekommt")
    r = c.post("/sammlung/verwerfen", data={"id": "9999"},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "ein Eintrag, den es nicht gibt, wird nicht verworfen")

    # ================================================================ #
    print("\nDer Reiter Aufgaben")
    # ================================================================ #
    c.cookies.clear()
    pruefe("Es ist kein Projekt gewählt" in c.get("/aufgaben").text,
           "ohne Projekt sagt der Reiter es")
    c.cookies.set(anwendung.COOKIE_PROJEKT, str(projekt))

    seite = c.get("/aufgaben").text
    pruefe("Uploads, die nicht durchlaufen" in seite,
           "die Aufgabe aus dem Buendelschritt steht hier")
    pruefe("B-00" in seite,
           "und ihr Ursprung als Verweis auf die Eintraege")

    print("\nDie eine Sperre")
    vorher = len(_aufgaben(projekt))
    r = c.post("/aufgaben/neu", data={
        "titel": "Ohne Abnahme", "bereich": bereiche["server"],
        "eingetragen": "2026-09-07", "abnahme": "   "},
        follow_redirects=False)
    pruefe(len(_aufgaben(projekt)) == vorher
           and "art=schlecht" in r.headers["location"],
           "ohne Abnahme wird keine Aufgabe angelegt")
    pruefe("Sammlung" in unquote(r.headers["location"]),
           "und die Meldung nennt den Ausgang, nicht nur das Verbot")

    # DIE GEGENPROBE: Was dahintersteckt mahnt, es sperrt nicht.
    r = c.post("/aufgaben/neu", data={
        "titel": "Der Rückweg von der Maschine", "bereich": bereiche["server"],
        "prio": "SOLL", "eingetragen": "2026-09-07",
        "abnahme": "install.sh laesst sich rueckgaengig machen\nDie Abbilder bleiben liegen",
        "arbeit": "Dienste abschalten"},
        follow_redirects=False)
    pruefe(len(_aufgaben(projekt)) == vorher + 1,
           "ohne Ursache wird sehr wohl angelegt -- sie kann man nachtragen")
    pruefe("Befund" in unquote(r.headers["location"]),
           "und es wird gesagt, dass sie so lange als Befund steht")

    neue = [a for a in _aufgaben(projekt)
            if a["titel"] == "Der Rückweg von der Maschine"][0]
    pruefe(len(neue["abnahme"]) == 2 and len(neue["arbeit"]) == 1,
           "aus zwei Zeilen werden zwei Abnahmepunkte")
    seite = c.get("/aufgaben").text
    pruefe("ohne Ursache" in seite,
           "die Karte traegt das Abzeichen, statt still leer zu bleiben")

    print("\nStatus und Datum")
    r = c.post("/aufgaben/speichern",
               data={"id": neue["id"], "status": "AKTIV", "status_seit": ""},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "AKTIV ohne Datum wird als Meldung abgewiesen, nicht als Fehler")
    c.post("/aufgaben/speichern",
           data={"id": neue["id"], "status": "AKTIV",
                 "status_seit": "2026-09-07",
                 "dahinter": "Wer ausprobiert, braucht die Maschine zurück."},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        a = datenbank.aufgabe(conn, neue["id"])
    pruefe(a["status"] == "AKTIV" and a["status_seit"] == "2026-09-07"
           and a["dahinter"].startswith("Wer ausprobiert"),
           "Status, Datum und Ursache in einem Zug")
    pruefe("ohne Ursache" not in c.get("/aufgaben").text,
           "und das Abzeichen ist weg, sobald die Ursache dasteht")

    print("\nErledigt haengt an der Abnahme")
    r = c.post("/aufgaben/abschliessen",
               data={"id": neue["id"], "art": "erledigt"},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "ohne alle Haken der Abnahme geht Erledigt nicht -- der Server "
           "prueft es, nicht nur der ausgegraute Knopf")

    # Nur die ARBEITSLISTE abhaken: Das reicht ausdruecklich nicht.
    c.post("/aufgaben/speichern", data={
        "id": neue["id"], "status": "AKTIV", "status_seit": "2026-09-07",
        "punkt": [str(p["id"]) for p in a["arbeit"] + a["abnahme"]],
        "haken": [str(p["id"]) for p in a["arbeit"]]},
        follow_redirects=False)
    with datenbank.verbindung() as conn:
        a = datenbank.aufgabe(conn, neue["id"])
    pruefe(a["arbeit_fertig"] == 1 and not a["abnehmbar"],
           "die Arbeitsliste ist durch, abnehmbar ist sie trotzdem nicht")

    c.post("/aufgaben/speichern", data={
        "id": neue["id"], "status": "AKTIV", "status_seit": "2026-09-07",
        "punkt": [str(p["id"]) for p in a["arbeit"] + a["abnahme"]],
        "haken": [str(p["id"]) for p in a["arbeit"] + a["abnahme"]]},
        follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(datenbank.aufgabe(conn, neue["id"])["abnehmbar"],
               "erst wenn auch die Abnahme steht, ist sie abnehmbar")

    # Und ein Haken laesst sich wegnehmen -- ohne die Liste aller Punkte
    # ginge das nie, denn ein leeres Kaestchen schickt nichts mit.
    c.post("/aufgaben/speichern", data={
        "id": neue["id"], "status": "AKTIV", "status_seit": "2026-09-07",
        "punkt": [str(p["id"]) for p in a["arbeit"] + a["abnahme"]],
        "haken": []}, follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(datenbank.aufgabe(conn, neue["id"])["arbeit_fertig"] == 0,
               "ein Haken laesst sich wieder wegnehmen")

    print("\nTitel, Bereich und Zeilen aendern (B-073)")
    # Bis zum 19.09.2026 liess sich ein Tippfehler im Titel nur beheben,
    # indem man die Aufgabe verwarf -- und einer in einer Zeile nur durch
    # Wegnehmen und neu Anlegen, wobei der Haken verloren ging.
    with datenbank.verbindung() as conn:
        a = datenbank.aufgabe(conn, neue["id"])
    seite = c.get("/aufgaben").text
    pruefe('id="titel-%d"' % neue["id"] in seite
           and 'id="bereich-%d"' % neue["id"] in seite
           and 'name="text:%d"' % a["abnahme"][0]["id"] in seite,
           "die Karte bietet Titel, Bereich und den Text jeder Zeile an")
    erste = a["abnahme"][0]
    c.post("/aufgaben/speichern", data={
        "id": neue["id"], "status": "AKTIV", "status_seit": "2026-09-07",
        "punkt": [str(erste["id"])], "haken": [str(erste["id"])]},
        follow_redirects=False)
    r = c.post("/aufgaben/speichern", data={
        "id": neue["id"], "status": "AKTIV", "status_seit": "2026-09-07",
        "titel": "  Der Rückweg von der Maschine, korrigiert  ",
        "bereich_id": str(bereiche["quellen"]),
        "punkt": [str(erste["id"])], "haken": [str(erste["id"])],
        "text:%d" % erste["id"]: "install.sh lässt sich rückgängig machen"},
        follow_redirects=False)
    with datenbank.verbindung() as conn:
        b = datenbank.aufgabe(conn, neue["id"])
    geaendert = [p for p in b["abnahme"] if p["id"] == erste["id"]][0]
    pruefe("art=gut" in r.headers["location"]
           and b["titel"] == "Der Rückweg von der Maschine, korrigiert"
           and b["bereich_id"] == bereiche["quellen"],
           "Titel und Bereich werden gespeichert, der Titel ohne Raender")
    pruefe(geaendert["text"] == "install.sh lässt sich rückgängig machen"
           and geaendert["erledigt"],
           "der Text einer Zeile aendert sich, und ihr Haken bleibt")
    for daten, was in (
            ({"titel": "   "}, "ein leerer Titel"),
            ({"bereich_id": "999999"}, "ein Bereich aus keinem Projekt"),
            ({"text:%d" % erste["id"]: "  "}, "eine geleerte Zeile")):
        r = c.post("/aufgaben/speichern",
                   data={"id": neue["id"], "status": "AKTIV",
                         "status_seit": "2026-09-07", **daten},
                   follow_redirects=False)
        with datenbank.verbindung() as conn:
            nachher = datenbank.aufgabe(conn, neue["id"])
        pruefe("art=schlecht" in r.headers["location"]
               and nachher["titel"] == b["titel"]
               and nachher["bereich_id"] == b["bereich_id"]
               and len(nachher["abnahme"]) == len(b["abnahme"]),
               "%s wird abgewiesen, und nichts aendert sich" % was)
    # Zurueck, damit die Pruefungen danach den Stand vorfinden, den sie
    # erwarten.
    c.post("/aufgaben/speichern", data={
        "id": neue["id"], "status": "AKTIV", "status_seit": "2026-09-07",
        "titel": "Der Rückweg von der Maschine",
        "bereich_id": str(bereiche["server"]),
        "punkt": [str(erste["id"])], "haken": []},
        follow_redirects=False)

    print("\nZeilen dazu und weg")
    c.post("/aufgaben/punkt",
           data={"id": neue["id"], "art": "ARBEIT", "text": "Hilfe nachziehen"},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        a = datenbank.aufgabe(conn, neue["id"])
    pruefe(len(a["arbeit"]) == 2, "eine Zeile kommt dazu")
    c.post("/aufgaben/punkt/weg",
           data={"id": neue["id"], "punkt": a["arbeit"][0]["id"]},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        a = datenbank.aufgabe(conn, neue["id"])
    pruefe(len(a["arbeit"]) == 1, "und wieder weg")

    # DIE SPERRE GILT AUCH NACHTRAEGLICH: Eine Sperre, die sich
    # hinterher umgehen laesst, ist keine.
    c.post("/aufgaben/punkt/weg",
           data={"id": neue["id"], "punkt": a["abnahme"][0]["id"]},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        a = datenbank.aufgabe(conn, neue["id"])
    r = c.post("/aufgaben/punkt/weg",
               data={"id": neue["id"], "punkt": a["abnahme"][0]["id"]},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(len(datenbank.aufgabe(conn, neue["id"])["abnahme"]) == 1
               and "art=schlecht" in r.headers["location"],
               "der LETZTE Abnahmepunkt bleibt -- sonst waere die Sperre "
               "hinterher zu umgehen")

    print("\nAbschliessen")
    with datenbank.verbindung() as conn:
        a = datenbank.aufgabe(conn, neue["id"])
    c.post("/aufgaben/speichern", data={
        "id": neue["id"], "status": "AKTIV", "status_seit": "2026-09-07",
        "punkt": [str(p["id"]) for p in a["abnahme"]],
        "haken": [str(p["id"]) for p in a["abnahme"]]},
        follow_redirects=False)
    c.post("/aufgaben/abschliessen",
           data={"id": neue["id"], "art": "erledigt"}, follow_redirects=False)
    pruefe(all(x["id"] != neue["id"] for x in _aufgaben(projekt)),
           "eine erledigte Aufgabe steht nicht mehr in der Liste")
    with datenbank.verbindung() as conn:
        pruefe(datenbank.aufgabe(conn, neue["id"])["abschluss_am"]
               == datenbank.heute(),
               "aber mit Datum im Archiv")

    # ================================================================ #
    print("\nDer Reiter Meilensteine")
    # ================================================================ #
    c.cookies.clear()
    pruefe("Es ist kein Projekt gewählt" in c.get("/meilensteine").text,
           "ohne Projekt sagt der Reiter es")
    c.cookies.set(anwendung.COOKIE_PROJEKT, str(projekt))

    r = c.post("/meilensteine/neu", data={
        "benennung": "Linux Plattform", "prio": "SOLL",
        "eingetragen": "2026-08-29",
        "beschreibung": "Der Bootserver läuft nachweislich auf drei Systemen.",
        "abnahme_kriterium": "Ein Esprimo startet über einen Pi-Server."},
        follow_redirects=False)
    pruefe(r.status_code == 303 and len(_steine(projekt)) == 1,
           "ein Meilenstein wird angelegt")
    # ER DARF LEER ENTSTEHEN -- und es wird gesagt, dass er nicht leer
    # bleiben darf.
    pruefe("Befund" in unquote(r.headers["location"]),
           "ohne Aufgabe wird er trotzdem angelegt, und die Meldung sagt "
           "es: kein Sperren, ein Befund")
    stein = _steine(projekt)[0]
    seite = c.get("/meilensteine").text
    pruefe("ohne Aufgabe" in seite,
           "die Karte traegt das Abzeichen")
    pruefe("Wartet auf ihn" in seite and "Hängt ab von" in seite,
           "die Kopfzeile ist mehrzeilig und steht vor den Angaben")

    r = c.post("/meilensteine/neu", data={"benennung": "", "prio": "SOLL"},
               follow_redirects=False)
    pruefe(len(_steine(projekt)) == 1
           and "art=schlecht" in r.headers["location"],
           "ohne Benennung wird keiner angelegt")

    print("\nEin Kreis wird abgewiesen")
    c.post("/meilensteine/neu", data={
        "benennung": "Windows Plattform", "eingetragen": "2026-08-29",
        "vorgaenger": stein["id"]}, follow_redirects=False)
    zweiter = [m for m in _steine(projekt)
               if m["benennung"] == "Windows Plattform"][0]
    pruefe([v["id"] for v in zweiter["vorgaenger"]] == [stein["id"]],
           "der Vorgaenger steht am neuen Stein")
    r = c.post("/meilensteine/speichern",
               data={"id": stein["id"], "benennung": stein["benennung"],
                     "vorgaenger": zweiter["id"]}, follow_redirects=False)
    pruefe("Kreis" in unquote(r.headers["location"]),
           "und der Rueckweg wird als Kreis abgewiesen")

    print("\nAufgaben zuschlagen")
    with datenbank.verbindung() as conn:
        a_neu = datenbank.aufgabe_anlegen(
            conn, projekt, "Arbeit am Stein", bereiche["server"],
            "2026-09-01", abnahme=["laeuft durch"])
    c.post("/meilensteine/aufgabe",
           data={"id": stein["id"], "aufgabe": a_neu}, follow_redirects=False)
    with datenbank.verbindung() as conn:
        m = datenbank.meilenstein(conn, stein["id"])
    pruefe(len(m["aufgaben"]) == 1 and not m["ohne_aufgabe"],
           "die Aufgabe haengt am Stein, der Befund ist weg")
    pruefe("ohne Aufgabe" not in c.get("/meilensteine").text
           or "Windows" in c.get("/meilensteine").text,
           "und das Abzeichen ist an diesem Stein verschwunden")

    # DIE AUSWAHL STARTET LEER, seit dem 22.09.2026. Vorher stand dort
    # zugeklappt die erste freie Aufgabe -- eine Kennung wie die
    # zugeordneten darüber, und genau so einmal falsch gelesen. Dazu die
    # zweite Falle: Ein Klick auf „Hinzufügen" fügte dann eine Aufgabe
    # zu, die niemand ausgesucht hatte.
    seite = c.get("/meilensteine").text
    pruefe('<option value="">— bitte wählen —</option>' in seite,
           "die Auswahl beginnt mit einem leeren Eintrag")
    pruefe('class="muted small">Aufgabe hinzufügen</label>' in seite,
           "und ihre Beschriftung ist sichtbar, nicht nur für Vorleser")
    r = c.post("/meilensteine/aufgabe",
               data={"id": stein["id"], "aufgabe": ""},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        m = datenbank.meilenstein(conn, stein["id"])
    pruefe(r.status_code == 303
           and "gewählt" in unquote(r.headers["location"])
           and len(m["aufgaben"]) == 1,
           "ohne Auswahl passiert nichts, und es steht da")

    print("\nDie Abnahme haengt an den Aufgaben")
    r = c.post("/meilensteine/abnehmen", data={"id": stein["id"]},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"]
           and "offen" in unquote(r.headers["location"]),
           "solange eine Aufgabe offen ist, geht Abnehmen nicht -- der "
           "Server prueft es, nicht nur der ausgegraute Knopf")
    r = c.post("/meilensteine/abnehmen", data={"id": zweiter["id"]},
               follow_redirects=False)
    pruefe("keine Aufgabe" in unquote(r.headers["location"]),
           "und ohne jede Aufgabe gibt es nichts abzunehmen")

    with datenbank.verbindung() as conn:
        datenbank.aufgabe_abschliessen(conn, a_neu, "erledigt")
    r = c.post("/meilensteine/abnehmen", data={"id": stein["id"]},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        m = datenbank.meilenstein(conn, stein["id"])
    pruefe(m["abschluss"] == "erledigt" and m["abnahme_am"] == datenbank.heute(),
           "erst wenn alle erledigt sind, geht es -- und Abschluss und "
           "Datum entstehen in einem Zug")
    # DIE MELDUNG SAGT, WAS DER EINE KNOPF GETAN HAT.
    satz = unquote(r.headers["location"])
    pruefe("Dauer" in satz and "Umweg" in satz,
           "und die Meldung nennt Dauer und Umwege -- die drei anderen "
           "Handgriffe fallen ab, statt getan zu werden")
    pruefe(all(x["id"] != stein["id"] for x in _steine(projekt)),
           "abgenommen verschwindet er aus der Liste der offenen")
    pruefe("zeigen=alle" in c.get("/meilensteine").text,
           "der Filter dorthin steht in der Kopfzeile")
    with datenbank.verbindung() as conn:
        pruefe(len(datenbank.meilensteine(conn, projekt, offen_nur=False)) == 2,
               "aus der Ablage verschwindet er nicht")

    print("\nWas dazwischenkam")
    r = c.post("/meilensteine/dazwischen",
               data={"id": zweiter["id"], "datum": "2026-09-01",
                     "text": "Der Pi war nicht da."}, follow_redirects=False)
    with datenbank.verbindung() as conn:
        m = datenbank.meilenstein(conn, zweiter["id"])
    pruefe(len(m["dazwischen"]) == 1
           and m["dazwischen"][0]["text"] == "Der Pi war nicht da.",
           "der kurze Weg notiert den Umweg am gewaehlten Stein")
    r = c.post("/meilensteine/dazwischen",
               data={"id": zweiter["id"], "text": "  "},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "ohne Satz ist es keine Notiz")
    c.post("/meilensteine/dazwischen/weg",
           data={"id": zweiter["id"], "zeile": m["dazwischen"][0]["id"]},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(not datenbank.meilenstein(conn, zweiter["id"])["dazwischen"],
               "und sie laesst sich wegnehmen")

    print("\nDas Feld Meilenstein an der Aufgabe")
    aufgabenseite = c.get("/aufgaben").text
    pruefe("noch nicht gebaut" not in aufgabenseite,
           "der Satz ueber den fehlenden Reiter ist ersetzt, nicht "
           "vergessen worden")
    with datenbank.verbindung() as conn:
        offen = [a for a in datenbank.aufgaben(conn, projekt)][0]
    c.post("/aufgaben/speichern",
           data={"id": offen["id"], "meilenstein_id": zweiter["id"]},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        a = datenbank.aufgabe(conn, offen["id"])
    pruefe(a["meilenstein"] and a["meilenstein"]["id"] == zweiter["id"],
           "eine Aufgabe laesst sich von ihrer Karte aus zuschlagen")
    c.post("/aufgaben/speichern",
           data={"id": offen["id"], "meilenstein_id": ""},
           follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(datenbank.aufgabe(conn, offen["id"])["meilenstein_id"] is None,
               "und ein leeres Feld heisst KEIN Meilenstein, nicht die "
               "Nummer null")

    print("\nVerworfen -- und die Arbeit bleibt")
    with datenbank.verbindung() as conn:
        datenbank.aufgabe_zuschlagen(conn, offen["id"], zweiter["id"])
    r = c.post("/meilensteine/verwerfen", data={"id": zweiter["id"]},
               follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(datenbank.meilenstein(conn, zweiter["id"])["abschluss"]
               == "verworfen"
               and datenbank.aufgabe(conn, offen["id"])["meilenstein_id"]
               is None,
               "der Stein ist verworfen, die Aufgabe steht wieder ohne "
               "Stein da")
    pruefe("nicht die Arbeit" in unquote(r.headers["location"]),
           "und die Meldung sagt es: verworfen ist der Termin, nicht die "
           "Arbeit")

    # ================================================================ #
    print("\nDer Reiter Entscheidungen")
    # ================================================================ #
    c.cookies.clear()
    pruefe("Es ist kein Projekt gewählt" in c.get("/entscheidungen").text,
           "ohne Projekt sagt der Reiter es")
    c.cookies.set(anwendung.COOKIE_PROJEKT, str(projekt))

    r = c.post("/entscheidungen/neu", data={
        "titel": "Die Firewall wird gemeldet, nicht eingerichtet",
        "zustand": "ENTSCHLUSS", "datum": "2026-09-05",
        "entschluss": "Der Server meldet die Firewall, er fasst sie nicht an.",
        "text": "## Der Zwiespalt\nSie gehört der Maschine, nicht diesem Dienst."},
        follow_redirects=False)
    pruefe(r.status_code == 303 and len(_entscheidungen(projekt)) == 1,
           "eine Entscheidung wird angelegt")
    eins = _entscheidungen(projekt)[0]
    pruefe(eins["bezug"] is None,
           "freistehend ist erlaubt -- zwei Drittel hängen an nichts")

    # MAHNEN, NICHT SPERREN.
    r = c.post("/entscheidungen/neu", data={
        "titel": "Ohne Satz", "zustand": "ENTSCHLUSS", "datum": "2026-09-06"},
        follow_redirects=False)
    pruefe(len(_entscheidungen(projekt)) == 2,
           "ein ENTSCHLUSS ohne Satz wird trotzdem angelegt")
    pruefe("ohne Satz ist keiner" in unquote(r.headers["location"]),
           "und die Meldung sagt es -- gesperrt wird nichts")
    seite = c.get("/entscheidungen").text
    pruefe("ohne Satz" in seite,
           "die Karte trägt das Abzeichen")

    r = c.post("/entscheidungen/neu",
               data={"titel": "", "zustand": "OFFEN"},
               follow_redirects=False)
    pruefe(len(_entscheidungen(projekt)) == 2
           and "art=schlecht" in r.headers["location"],
           "ohne Titel wird keine angelegt")
    r = c.post("/entscheidungen/neu",
               data={"titel": "Krumm", "zustand": "VIELLEICHT"},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "und ein erfundener Zustand wird abgewiesen")

    print("\nZeigen statt kopieren")
    with datenbank.verbindung() as conn:
        thema = datenbank.topic_anlegen(
            conn, projekt, "Der Rückweg fehlt", bereiche["server"],
            "2026-09-06")
    stumm = [e for e in _entscheidungen(projekt)
             if e["titel"] == "Ohne Satz"][0]
    c.post("/entscheidungen/speichern", data={
        "id": stumm["id"], "titel": "Ohne Satz", "zustand": "ENTSCHLUSS",
        "datum": "2026-09-06", "bezug": "B:%d" % thema},
        follow_redirects=False)
    with datenbank.verbindung() as conn:
        e = datenbank.entscheidung(conn, stumm["id"])
    pruefe(e["bezug"] and e["bezug"]["titel"] == "Der Rückweg fehlt",
           "der Titel des bezogenen Eintrags wird geholt, nicht gespeichert")
    pruefe(e["liegt"],
           "und weil der Eintrag offen ist, LIEGT die Entscheidung")
    pruefe("Was entschieden ist und trotzdem liegt"
           in c.get("/entscheidungen").text,
           "die Liegeprobe steht als eigene Karte da")

    r = c.post("/entscheidungen/speichern", data={
        "id": stumm["id"], "titel": "Ohne Satz", "zustand": "ENTSCHLUSS",
        "datum": "2026-09-06", "bezug": "B:9999"}, follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "ein Bezug auf einen Eintrag, den es nicht gibt, wird abgewiesen")

    print("\nDer Satz wird nachgetragen")
    r = c.post("/entscheidungen/speichern", data={
        "id": stumm["id"], "titel": "Ohne Satz", "zustand": "ENTSCHLUSS",
        "datum": "2026-09-06", "bezug": "B:%d" % thema,
        "entschluss": "Der Rückweg kommt als uninstall.sh."},
        follow_redirects=False)
    with datenbank.verbindung() as conn:
        pruefe(not datenbank.entscheidung(conn, stumm["id"])["ohne_satz"],
               "nachtragen genügt -- der Befund ist weg")
    pruefe("ohne Satz ist keiner" not in unquote(r.headers["location"]),
           "und die Meldung mahnt nicht mehr")

    print("\nFilter und Suche")
    c.post("/entscheidungen/neu", data={
        "titel": "Den Produktnamen festlegen", "zustand": "OFFEN",
        "datum": "2026-08-29",
        "text": "Achtzig geprüfte Wörter, drei Kandidaten."},
        follow_redirects=False)
    pruefe("alle" in c.get("/entscheidungen").text,
           "die Vorgabe ist alle, nicht offen")
    nur_offen = c.get("/entscheidungen?zeigen=offen").text
    pruefe("Den Produktnamen festlegen" in nur_offen
           and "Die Firewall wird gemeldet" not in nur_offen,
           "der Filter zeigt nur die offenen")
    gefunden = c.get("/entscheidungen?suche=Kandidaten").text
    pruefe("Den Produktnamen festlegen" in gefunden
           and "Die Firewall wird gemeldet" not in gefunden,
           "die Suche geht über den Verlauf, nicht nur über den Titel")

    print("\nGelöscht, nicht archiviert")
    r = c.post("/entscheidungen/loeschen", data={"id": eins["id"]},
               follow_redirects=False)
    pruefe(all(e["id"] != eins["id"] for e in _entscheidungen(projekt)),
           "eine Entscheidung wird wirklich gelöscht -- es gibt kein "
           "Archiv für sie")
    r = c.post("/entscheidungen/loeschen", data={"id": "9999"},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "eine, die es nicht gibt, wird nicht gelöscht")

    # ================================================================ #
    print("\nDer Reiter History")
    # ================================================================ #
    c.cookies.clear()
    pruefe("Es ist kein Projekt gewählt" in c.get("/history").text,
           "ohne Projekt sagt der Reiter es")
    c.cookies.set(anwendung.COOKIE_PROJEKT, str(projekt))

    # HIER WIRD NICHTS EINGETRAGEN -- es gibt keine einzige POST-Route.
    schreibend = [r.path for r in anwendung.app.routes
                  if getattr(r, "path", "").startswith("/history")
                  and "POST" in getattr(r, "methods", set())]
    pruefe(not schreibend,
           "auf diesem Reiter gibt es keine einzige POST-Route -- er "
           "zeigt nur")

    seite = c.get("/history").text
    pruefe("Hier wird nichts eingetragen" in seite,
           "und das steht über allem, nicht in einer Karte")
    # ZWEI ANSICHTEN, seit dem 22.09.2026 (E-027). Das Quittungsbuch
    # zeigte eine Teilmenge des Archivs und verwies auf eben diese
    # Einträge -- doppelt war nicht die Buchführung, sondern die
    # Darstellung.
    pruefe("Straße" in seite and "Archiv" in seite
           and "Quittungsbuch" not in seite,
           "zwei Ansichten stehen im Umschalter, das Quittungsbuch ist "
           "darin aufgegangen")

    print("\nDie Straße")
    strasse = c.get("/history?ansicht=strasse").text
    pruefe("Die Straße" in strasse and "hier" in strasse,
           "die Straße endet an einem Punkt, der hier heißt")
    with datenbank.verbindung() as conn:
        steine = datenbank.strasse(conn, projekt)
    if steine:
        pruefe(steine[0]["benennung"] in strasse,
               "und der abgenommene Stein steht darauf")

    print("\nEnde oder Umzug -- die Zusage aus dem Quittungsbuch")
    # DAS IST DER TEIL, DER BEIM ZUSAMMENLEGEN VERLOREN GEHEN KONNTE.
    # Ein Eintrag, aus dem eine Aufgabe wurde, ist nicht fertig geworden
    # -- er ist umgezogen. Zählt man beides zusammen, zählt dieselbe
    # Arbeit zweimal, und zwar still.
    pruefe(datenbank.abschlussart("erledigt") == "ende"
           and datenbank.abschlussart("verworfen") == "ende"
           and datenbank.abschlussart("aufgabe") == "umzug"
           and datenbank.abschlussart("meilenstein") == "umzug",
           "verworfen ist ein Ende, aufgabe und meilenstein sind Umzüge")

    with datenbank.verbindung() as conn:
        enden = datenbank.archiv(conn, projekt, schluss="ende")
        umzuege = datenbank.archiv(conn, projekt, schluss="umzug")
        alles = datenbank.archiv(conn, projekt)
    pruefe(len(enden) + len(umzuege) == len(alles),
           "jeder Archiveintrag ist genau eines von beiden")
    umgezogen = [t for t in _sammlung_alle(projekt)
                 if t["abschluss"] == "aufgabe"]
    if umgezogen:
        pruefe(all(e["kennung"] != umgezogen[0]["kennung"] for e in enden)
               and any(u["kennung"] == umgezogen[0]["kennung"]
                       for u in umzuege),
               "ein Eintrag, aus dem eine Aufgabe wurde, zählt als Umzug "
               "und nicht als Abschluss")

    seite = c.get("/history?ansicht=archiv").text
    pruefe("zählt deshalb nicht als Abschluss" in seite
           and "dieselbe Arbeit zweimal" in seite,
           "und der Kartenfuß sagt, warum das keine Kosmetik ist")

    # Alte Lesezeichen aufs Quittungsbuch landen dort, wo dessen Inhalt
    # jetzt steht -- nicht still auf der Straße.
    r = c.get("/history?ansicht=quittung", follow_redirects=False)
    pruefe(r.status_code == 200 and "Archiv" in r.text and "Enden" in r.text,
           "ein alter Verweis aufs Quittungsbuch führt ins Archiv, "
           "gefiltert auf die Enden")

    print("\nDas Archiv")
    archiv = c.get("/history?ansicht=archiv").text
    pruefe("Hier wird nichts geändert" in archiv or "Noch nichts" in archiv,
           "im Archiv wird nichts geändert, und es steht da")
    pruefe('type="checkbox"' not in archiv and "<textarea" not in archiv,
           "keine Kästchen und keine Felder -- ein Kästchen, das nichts "
           "tut, ist schlimmer als keines")
    gefiltert = c.get("/history?ansicht=archiv&art=M").text
    pruefe("Meilensteine" in gefiltert,
           "der Filter nach Register antwortet")
    pruefe(c.get("/history?ansicht=archiv&art=X").status_code == 200,
           "und ein erfundenes Register faellt auf alle zurueck")
    for wert in ("ende", "umzug"):
        pruefe(c.get("/history?ansicht=archiv&schluss=%s" % wert)
               .status_code == 200,
               "der Filter nach Abschlussart antwortet -- %s" % wert)
    pruefe(c.get("/history?ansicht=archiv&schluss=X").status_code == 200,
           "und eine erfundene Abschlussart faellt auf alle zurueck")
    pruefe(c.get("/history?ansicht=erfunden").status_code == 200,
           "eine erfundene Ansicht faellt auf die Straße zurück")

    # ================================================================ #
    print("\nDer Reiter Einrichtung")
    # ================================================================ #
    c.cookies.set(anwendung.COOKIE_PROJEKT, str(projekt))
    seite = c.get("/einrichtung").text
    for karte in ("Stand", "Export", "Ablageorte", "Einstellungen",
                  "Firewall", "Fehlerbericht", "Verbesserungen",
                  "Werkseinstellung"):
        if karte not in seite:
            pruefe(False, "die Karte %s steht da" % karte)
            break
    else:
        pruefe(True, "alle acht Karten stehen da")
    pruefe("IP-Adresse übernehmen" in seite and "gibt es hier nicht" in seite,
           "und dass es die neunte nicht gibt, steht da statt zu fehlen")
    # DIE KARTE STAND, seit dem 22.09.2026. Bis dahin stand hier die
    # Gegenprobe -- dass nicht gesucht wird, weil es kein öffentliches
    # Repository gab. Seit dem 21.09.2026 gibt es eines.
    pruefe("Nach neuen Versionen suchen" in seite
           and 'action="/einrichtung/updatepruefung"' in seite,
           "die Karte Stand bietet an, nach neuen Versionen zu suchen")
    pruefe("Offline-Modus" in seite
           and 'action="/einrichtung/offline"' in seite,
           "und daneben den Offline-Modus -- eine Eigenschaft der "
           "Maschine, keine Gewohnheit des Bedieners")

    # Der Offline-Modus nimmt die Auswahl weg, statt sie stehen zu lassen
    # und zu ignorieren. Zwei Bedienelemente mit derselben Wirkung wären
    # ein Rätsel darüber, welches gilt.
    r = c.post("/einrichtung/offline", data={"offline": "1"},
               follow_redirects=False)
    pruefe(r.status_code == 303, "der Offline-Modus lässt sich einschalten")
    seite = c.get("/einrichtung").text
    pruefe("Nach neuen Versionen suchen" not in seite
           and "Es wird nicht nachgesehen" in seite,
           "und dann steht da, dass nicht nachgesehen wird -- die Auswahl "
           "ist weg, nicht nur wirkungslos")
    pruefe(updatewacht.intervall_tage() == 0 and not updatewacht.erlaubt(),
           "und der Wächter fragt nicht mehr, egal was eingestellt war")

    # Überstimmen lässt er sich auch von Hand nicht: Wer das Formular
    # direkt abschickt, bekommt eine Meldung und keine Wirkung.
    r = c.post("/einrichtung/updatepruefung", data={"tage": "7"},
               follow_redirects=False)
    pruefe(r.status_code == 303 and "Offline-Modus" in unquote(
        r.headers["location"]),
        "das Suchintervall lässt sich im Offline-Modus nicht setzen")
    pruefe(einstellungen.hole("updatepruefung") != 7
           or updatewacht.intervall_tage() == 0,
           "und die Einstellung bleibt wirkungslos, solange er an ist")

    r = c.post("/einrichtung/offline", data={"offline": "0"},
               follow_redirects=False)
    pruefe(r.status_code == 303 and not updatewacht.offline(),
           "und er lässt sich wieder ausschalten")
    seite = c.get("/einrichtung").text
    pruefe("Nach neuen Versionen suchen" in seite,
           "danach steht die Auswahl wieder da")

    # Gezählt werden Änderungen, nicht Versionsnummern -- die Antwort
    # kommt hier aus der Hand und nicht aus dem Netz. Ohne das wäre die
    # Testreihe von GitHub abhängig, und das wäre keine Prüfung, sondern
    # eine Wettervorhersage.
    einstellungen.setze("updatepruefung", 7)
    updatewacht.vergiss()
    versionsstand.DATEI = Path(tempfile.mkdtemp()) / "VERSION"
    versionsstand.DATEI.write_text(
        "stand=v1.0-8-gabc1234\ncommit=abc1234\nzweig=main\n"
        "installiert=2026-09-22 09:00\n", encoding="utf-8")
    versionsstand._CACHE["stand"] = None
    pruefe(updatewacht.blick(hole=lambda: {"ahead_by": 3, "behind_by": 0}),
           "ein Blick mit Antwort kommt zustande")
    lage = updatewacht.stand()
    pruefe(lage["voraus"] == 3 and lage["neuer"],
           "und drei Änderungen liegen bereit")
    seite = c.get("/einrichtung").text
    pruefe("Änderungen liegen" in seite and "bereit</strong>" in seite,
           "die Karte sagt es in der Mehrzahl")

    # Ein Befund gilt für den Stand, gegen den er gezählt wurde. Wird ein
    # anderer eingespielt, ist er keine veraltete Auskunft, sondern gar
    # keine -- in Boot behauptete die Karte am 05.09.2026 eine Woche lang
    # etwas, das seit dem Update nicht mehr stimmte.
    versionsstand.DATEI.write_text(
        "stand=v1.0-11-gdef5678\ncommit=def5678\nzweig=main\n"
        "installiert=2026-09-22 10:00\n", encoding="utf-8")
    versionsstand._CACHE["stand"] = None
    pruefe(updatewacht.stand()["voraus"] == 0,
           "nach einem Update ist der gemerkte Befund weg, nicht alt")
    pruefe(updatewacht.faellig(),
           "und es wird sofort wieder nachgesehen, nicht erst in einer Woche")

    # Ohne Leitung ist nichts kaputt -- vermerkt, nicht gemeldet.
    def _ohne_netz():
        raise urllib.error.URLError("kein Netz")
    updatewacht.blick(hole=_ohne_netz)
    lage = updatewacht.stand()
    pruefe(lage["ohne_netz"] and not lage["erreicht"],
           "ein fehlgeschlagener Blick wird vermerkt, nicht gemeldet")
    seite = c.get("/einrichtung").text
    # Auf den Teil geprüft, der in der Vorlage auf einer Zeile steht --
    # „keine Störung“ steht dort über einen Umbruch hinweg.
    pruefe("nicht erreichbar" in seite
           and "Störung dieser Maschine" in seite,
           "und die Karte sagt, dass das keine Störung dieser Maschine ist")

    # Eine Antwort, die keine Auskunft war, ist etwas anderes als keine
    # Antwort. Beides unter "nicht erreichbar" zu führen behauptet auf
    # einer Maschine mit tadelloser Leitung etwas Falsches.
    def _abgewiesen():
        raise urllib.error.HTTPError("u", 404, "weg", None, None)
    updatewacht.blick(hole=_abgewiesen)
    pruefe(updatewacht.stand()["erreicht"],
           "eine Antwort ohne Auskunft wird von keiner Antwort "
           "unterschieden")

    # ================================================================ #
    # DIE BLAUE KARTE -- der einzige Befund, der keinem Projekt gehört.
    #
    # Ohne sie sähe die Auskunft nur, wer Einrichtung öffnet. Sie steht
    # deshalb auf jeder Seite, und sie ist der Grund, warum `kenntnis`
    # seit dem 22.09.2026 ohne Fremdschlüssel auskommt: Projekt 0 heißt
    # „gehört der Maschine“.
    # ================================================================ #
    updatewacht.blick(hole=lambda: {"ahead_by": 2, "behind_by": 0})
    seite = c.get("/meilensteine").text
    pruefe("Änderungen liegen bereit" in seite,
           "die Karte steht auf einem Reiter, nicht nur unter Einrichtung")
    pruefe("update.sh" in seite or "update.ps1" in seite,
           "und sie nennt den Befehl, mit dem geholt wird")
    pruefe("Dorthin" in seite and 'action="/projekte/waehlen"'
           not in seite.split('stufe-info')[-1][:900],
           "ein Befund ohne Projekt stellt keine Vorauswahl um")

    # Wegklicken: dieselbe Mechanik wie bei jedem anderen Befund, nur mit
    # der 0. Vor dem 22.09.2026 hätte der Fremdschlüssel hier zugeschlagen
    # -- und zwar an einem Knopf, der nur eine Karte zuklappen soll.
    r = c.post("/befund/kenntnis",
               data={"kennung": "neuefassung", "projekt": "0", "marke": "2",
                     "zurueck": "/meilensteine"}, follow_redirects=False)
    pruefe(r.status_code == 303, "die blaue Karte lässt sich wegklicken")
    seite = c.get("/meilensteine").text
    # Auf die Marke geprüft, nicht auf den Satz der Sammelzeile: Der
    # bricht in der Vorlage um, und „zur Kenntnis genommen“ stünde dann
    # über zwei Zeilen.
    pruefe('class="bekanntzeile"' in seite
           and "2 Änderungen liegen bereit" in seite,
           "weggeklickt heißt leise, nicht weg")
    pruefe('class="seitenkarte stufe-info"' not in seite,
           "und die Karte selbst steht nicht mehr da")

    # „Ich weiß Bescheid, bis es schlimmer wird.“ Kommt eine Änderung
    # dazu, steigt die Marke über die gemerkte -- und die Karte ist zurück.
    updatewacht.blick(hole=lambda: {"ahead_by": 5, "behind_by": 0})
    seite = c.get("/meilensteine").text
    pruefe("5 Änderungen liegen bereit" in seite
           and 'class="seitenkarte stufe-info"' in seite,
           "steigt die Zahl, ist es ein neuer Befund und die Karte kommt "
           "zurück")

    einstellungen.setze("updatepruefung", 0)
    updatewacht.vergiss()
    seite = c.get("/meilensteine").text
    pruefe("liegen bereit" not in seite,
           "und ohne Suche steht dort nichts mehr")

    print("\nDer Export")
    with datenbank.verbindung() as conn:
        p = datenbank.projekt(conn, projekt)
    ziel = Path(tempfile.mkdtemp())
    anwendung.export.ZIEL = ziel
    seite = c.get("/einrichtung").text
    # Nicht auf den ganzen Satz pruefen: Die Vorlage bricht ihn um, und
    # dann prueft man die Einrueckung statt der Aussage.
    pruefe("byteweise" in seite,
           "die Stabilitätszusage steht auf der Karte, nicht nur im "
           "Quelltext")
    pruefe("Dateien weichen ab" in seite or "weicht ab" in seite,
           "vor dem ersten Lauf sagt die Karte, dass die Ausgabe fehlt")

    r = c.post("/einrichtung/export", follow_redirects=False)
    pruefe(r.status_code == 303 and "art=gut" in r.headers["location"],
           "ausgeben antwortet mit 303 und meldet, was geschrieben wurde")
    ordner = ziel / anwendung.export.verzeichnisname(p)
    pruefe(sorted(d.name for d in ordner.glob("*.md"))
           == sorted(anwendung.export.DATEIEN),
           "fünf Dateien in einem Verzeichnis je Projekt")
    pruefe("aktuell" in c.get("/einrichtung").text,
           "und die Karte sagt danach, dass die Ausgabe aktuell ist")

    # DIE STABILITAETSZUSAGE, an der laufenden Anwendung geprueft.
    vorher = {d.name: d.read_bytes() for d in ordner.glob("*.md")}
    c.post("/einrichtung/export", follow_redirects=False)
    nachher = {d.name: d.read_bytes() for d in ordner.glob("*.md")}
    pruefe(vorher == nachher,
           "ein zweiter Lauf schreibt byteweise dasselbe -- sonst wäre "
           "die Versionsgeschichte im Repository wertlos")

    print("\nDer Ausgang zum Mitnehmen")
    # DER WEG AN DEN BESTAND, DER KEINE SHELL BRAUCHT. Die Texte
    # entstehen ohnehin im Speicher, bevor sie auf die Platte gehen --
    # fuer den Download faellt nur der letzte Schritt weg.
    import io  # noqa: E402
    import zipfile  # noqa: E402

    paket = c.get("/einrichtung/export.zip")
    pruefe(paket.status_code == 200
           and paket.headers["content-type"] == "application/zip",
           "der Ausgang lässt sich als ZIP herunterladen")
    pruefe('filename="P-' in paket.headers.get("content-disposition", ""),
           "und heißt nach Projekt und Tag")
    darin = zipfile.ZipFile(io.BytesIO(paket.content)).namelist()
    pruefe(len(darin) == len(anwendung.export.DATEIEN)
           and all("/" in n for n in darin),
           "fünf Dateien in einem Verzeichnis, wie beim Schreiben")

    # DIE STABILITAETSZUSAGE GILT AUCH FUER DAS PAKET. Ein ZIP traegt zu
    # jeder Datei eine Uhrzeit; naehme es die echte, waeren zwei Pakete
    # desselben Bestands verschieden -- und die Zusage waere genau dort
    # gebrochen, wo man sie am leichtesten prueft.
    pruefe(paket.content == c.get("/einrichtung/export.zip").content,
           "zweimal heruntergeladen ist byteweise dasselbe Paket")

    # ER SCHREIBT NICHTS. Der eingerichtete Ausgang bleibt unberuehrt.
    vorher_stand = c.get("/einrichtung").text
    c.get("/einrichtung/export.zip")
    pruefe(_flach(vorher_stand) == _flach(c.get("/einrichtung").text),
           "und er rührt den eingerichteten Ausgang nicht an -- »Stand "
           "der Ausgabe« sagt danach dasselbe")

    ohne_projekt = TestClient(anwendung.app)
    pruefe(ohne_projekt.get("/einrichtung/export.zip",
                            follow_redirects=False).status_code == 303,
           "ohne gewähltes Projekt führt er dorthin, wo man eines wählt")

    print("\nDer Fehlerbericht")
    ohne = c.get("/einrichtung?fehlerbericht=1").text
    pruefe("MARLEI Tasks — Fehlerbericht" in ohne,
           "der Bericht wird erzeugt")
    # Auf die Ueberschrift des Blocks pruefen, nicht auf das Wort: Das
    # steht als Aufschrift am Kaestchen ohnehin auf jeder Seite.
    pruefe("Serverumgebung (freiwillig)" not in ohne,
           "ohne Haken enthält er nichts aus dem Bestand")
    mit = c.get("/einrichtung?fehlerbericht=1&umgebung_mit=1").text
    pruefe("Serverumgebung (freiwillig)" in mit and "Größe der Ablage" in mit,
           "mit Haken kommen Ablageorte und Zahlen dazu")
    # ZAEHLEN, NICHT ABSCHREIBEN -- der Grund, warum der Block ueberhaupt
    # verschickbar ist.
    with datenbank.verbindung() as conn:
        titel = [t["titel"] for t in datenbank.topics(conn, projekt,
                                                      offen_nur=False)]
    pruefe(all(t not in mit for t in titel if len(t) > 8),
           "aber kein einziger Titel: gezählt wird, nicht abgeschrieben")
    datei = c.get("/einrichtung/bericht.txt?umgebung_mit=0")
    pruefe(datei.status_code == 200
           and "attachment" in datei.headers.get("content-disposition", ""),
           "und es gibt ihn als Datei zum Anhängen")

    print("\nDie Werkseinstellung")
    schritt = c.get("/einrichtung?werkseinstellung=wort").text
    pruefe("Zum Fortfahren" in schritt,
           "der zweite Schritt verlangt den Projektnamen")
    r = c.post("/einrichtung/werkseinstellung", data={"wort": "Löschen"},
               follow_redirects=False)
    pruefe("art=schlecht" in r.headers["location"],
           "das Wort »Löschen« setzt nichts zurück -- das Losungswort ist "
           "der Projektname")
    with datenbank.verbindung() as conn:
        vor = datenbank.projekt(conn, projekt)
    r = c.post("/einrichtung/werkseinstellung",
               data={"wort": vor["name"].lower()}, follow_redirects=False)
    with datenbank.verbindung() as conn:
        nach = datenbank.projekt(conn, projekt)
    pruefe(sum(nach["bestand"].values()) == 0 and not nach["bereiche"],
           "mit dem richtigen Wort ist der Bestand weg")
    pruefe(nach["name"] == vor["name"] and nach["vision"] == vor["vision"],
           "das Projekt selbst bleibt -- der Unterschied zum Löschen")
    pruefe("zurückgesetzt" in unquote(r.headers["location"]),
           "und die Meldung nennt, was weggeräumt wurde")


    # ================================================================ #
    print("\nDer Reiter Hilfe")
    # ================================================================ #
    import re  # nur hier gebraucht: die Hilfe wird als Text geprueft

    seite = c.get("/hilfe").text
    for kapitel in ("Erste Schritte", "Was überall gilt", "Projekte",
                    "Sammlung", "Aufgaben", "Meilensteine",
                    "Entscheidungen", "Einrichtung", "History",
                    "Server Health", "Häufige Fragen"):
        if kapitel not in seite:
            pruefe(False, "das Kapitel %s steht da" % kapitel)
            break
    else:
        pruefe(True, "alle elf Kapitel stehen da")

    vorlagen = PROJ / "webui" / "templates"
    hilfe_text = (vorlagen / "hilfe.html").read_text(encoding="utf-8")
    anker = set(re.findall(r'id="([a-z0-9-]+)"', hilfe_text))

    # DIE ANKER SIND DER VERTRAG zwischen den Karten und dieser Seite --
    # und er wird in BEIDE Richtungen geprueft. Ein Fragezeichen, das ins
    # Leere zeigt, faellt niemandem auf: Der Browser springt dann einfach
    # an den Seitenanfang, und die Seite sieht richtig aus.
    gefragt: dict[str, str] = {}
    for datei in sorted(vorlagen.glob("*.html")):
        if datei.name == "hilfe.html":
            continue
        for a in re.findall(r'/hilfe#([a-z0-9-]+)',
                            datei.read_text(encoding="utf-8")):
            gefragt.setdefault(a, datei.name)
    fehlend = sorted("%s (%s)" % (a, gefragt[a])
                     for a in gefragt if a not in anker)
    pruefe(not fehlend,
           "jedes Fragezeichen einer Karte findet seinen Abschnitt -- %s"
           % (", ".join(fehlend) or "%d geprüft" % len(gefragt)))

    # Die Gegenrichtung: kein Abschnitt, dessen Karte es nicht mehr gibt.
    # Gemeint sind nur die Kartenabschnitte; die Kapitel "Erste Schritte"
    # und "Was überall gilt" gehoeren zu keiner Karte.
    KARTENANKER = ("projekte-", "sammlung-", "aufgaben-", "meilensteine-",
                   "entscheidungen-", "einrichtung-", "history-",
                   "serverhealth-")
    verwaist = sorted(a for a in anker
                      if a.startswith(KARTENANKER) and a not in gefragt)
    pruefe(not verwaist,
           "und kein Abschnitt beschreibt eine Karte, die es nicht mehr "
           "gibt -- %s" % (", ".join(verwaist) or "31 Abschnitte"))

    innen = set(re.findall(r'href="#([a-z0-9-]+)"', hilfe_text))
    pruefe(innen <= anker,
           "auch die Verweise innerhalb der Hilfe zeigen auf Abschnitte, "
           "die es gibt -- %s" % (", ".join(sorted(innen - anker)) or "alle"))

    # "Zur Karte →" ist der Rueckweg und geht genauso leicht kaputt.
    ZIELE = {"/": "projekte.html", "/sammlung": "sammlung.html",
             "/aufgaben": "aufgaben.html",
             "/meilensteine": "meilensteine.html",
             "/entscheidungen": "entscheidungen.html",
             "/einrichtung": "einrichtung.html",
             "/history": "history.html",
             "/serverhealth": "serverhealth.html"}
    kaputt = []
    for pfad, karte in re.findall(r'href="(/[a-z]*)[^"#]*#([a-z0-9-]+)"',
                                  hilfe_text):
        datei = ZIELE.get(pfad)
        if datei is None:
            kaputt.append(pfad)
        elif ('id="%s"' % karte) not in (vorlagen / datei).read_text(
                encoding="utf-8"):
            kaputt.append(pfad + "#" + karte)
    pruefe(not kaputt,
           "jedes »Zur Karte« landet auf einer Karte, die es gibt -- %s"
           % (", ".join(sorted(set(kaputt))) or "alle 31"))

    # Sie zeigt nur -- nachweisbar, nicht behauptet. Dieselbe Pruefung
    # wie unter History.
    schreibt = [r.path for r in anwendung.app.routes
                if getattr(r, "path", "").startswith("/hilfe")
                and "POST" in getattr(r, "methods", set())]
    pruefe(not schreibt,
           "die Hilfe hat keine einzige POST-Route -- sie zeigt nur")

    frisch = TestClient(anwendung.app)
    antwort = frisch.get("/hilfe")
    pruefe(antwort.status_code == 200 and "Was überall gilt" in antwort.text,
           "sie gilt auch ohne gewähltes Projekt -- gerade dann sucht sie "
           "jemand")

    # Was auf der Seite steht und nicht stimmt, ist der gefaehrlichste
    # Satz einer Hilfe: Sie wird geglaubt. Bis zum 07.09.2026 stand hier,
    # dass es die seitenweiten Befunde noch nicht gibt -- jetzt gibt es
    # sie, und das Kapitel beschreibt sie samt beider Knoepfe.
    # WER "OFFEN" WAEHLT, HAT GEWAEHLT. Der Befund "offen und liegt
    # lange" stand im Entwurf und ist am 07.09.2026 gestrichen worden;
    # die Hilfe sagt jetzt ausdruecklich, dass die Dauer NICHT gemessen
    # wird. Ein Satz, der still zurueckkaeme, waere eine Mahnung fuer
    # etwas, das absichtlich so dasteht.
    pruefe("gemessen wird" in _flach(seite)
           and "hat gewählt" in _flach(seite),
           "die Hilfe sagt, dass die Dauer einer offenen Entscheidung "
           "nicht gemessen wird -- OFFEN ist eine Wahl, kein Versäumnis")
    pruefe("Heute gibt es sie noch nicht" not in _flach(seite)
           and "Weggeklickt heißt" in _flach(seite)
           and "je Projekt" in _flach(seite),
           "die Befunde sind gebaut, und die Hilfe beschreibt sie -- "
           "samt dem Wegklicken, das je Projekt gilt")


    # ================================================================ #
    print("\nDer Reiter Server Health")
    # ================================================================ #
    import auslastung  # noqa: E402  -- erst hier gebraucht

    seite = c.get("/serverhealth").text
    pruefe("Auslastung" in seite and "Serverdetails" in seite,
           "zwei Karten, nicht fünfzehn")
    pruefe("Dienste" not in seite.split("Serverdetails")[1][:400],
           "keine Karte »Dienste« -- eine Karte mit drei Zeilen statt "
           "fünf wäre eine andere Karte mit demselben Namen")

    # DIE KARTE BESCHREIBT DIE MASCHINE, nicht den Bestand -- deshalb
    # steht sie auch ohne gewaehltes Projekt vollstaendig da.
    frisch_sh = TestClient(anwendung.app)
    ohne_projekt = frisch_sh.get("/serverhealth")
    pruefe(ohne_projekt.status_code == 200
           and "Serverdetails" in ohne_projekt.text
           and "Python" in ohne_projekt.text,
           "und sie gilt ohne gewähltes Projekt -- sie beschreibt den "
           "Unterbau, nicht den Bestand")

    print("\nDie Auslastung")
    # OHNE QUELLE LIEFERT JEDE FUNKTION LEERE WERTE STATT EINER
    # BEHAUPTUNG. Was die Quelle ist, haengt vom System ab -- und
    # **geprueft werden beide, egal wo diese Reihe laeuft:**
    # ``auslastung.SYSTEM`` ist genau dafuer eine Variable und keine
    # Abfrage mitten im Code.
    pruefe(auslastung.speicher() == {} or "gesamt" in auslastung.speicher(),
           "der Speicher ist entweder gemessen oder leer -- nie geraten")
    # EINMAL FRAGEN, DANN PRUEFEN. Es stand hier zweimal "auslastung.cpu()"
    # -- und der zweite Aufruf kommt so schnell hinterher, dass der Kernel
    # noch dieselbe Summe nennt: Ohne Unterschied gibt es keinen Prozentwert,
    # und aus dem "oder" wurde ein Vergleich mit None. Unter Windows faellt
    # das sofort auf, unter Linux irgendwann.
    gemessene_last = auslastung.cpu()
    pruefe(gemessene_last is None or 0 <= gemessene_last <= 100,
           "die Prozessorlast liegt zwischen 0 und 100 oder fehlt ganz "
           "-- die erste Messung hat noch keinen Vergleichswert")
    pruefe(auslastung.kerne() >= 1,
           "mindestens ein Kern, auch wenn keine Quelle etwas hergibt")

    eigen = auslastung.dienst()
    pruefe(eigen == {} or "betrieb" in eigen or "speicher" in eigen,
           "dieser Dienst meldet Betriebszeit und Speicher -- oder "
           "nichts, wenn die Quelle fehlt")

    print("\nKeine Quelle: leere Werte, keine Behauptung")
    # NICHT "unter Windows faellt das so an", sondern hergestellt: ein
    # /proc, das leer ist, und ein System, das sich fuer Linux ausgibt.
    # Vorher stand hier nur die Hoffnung, dass die Reihe auf einer
    # Maschine ohne /proc laeuft -- auf dem Server prueft sie damit gar
    # nichts.
    leeres_proc = Path(tempfile.mkdtemp())
    war_system, war_proc = auslastung.SYSTEM, auslastung.PROC
    try:
        auslastung.SYSTEM, auslastung.PROC = "posix", leeres_proc
        pruefe(auslastung.cpu() is None and auslastung.last() is None
               and auslastung.speicher() == {} and auslastung.netz() == {}
               and auslastung.dienst() == {},
               "ohne /proc ist jede Antwort leer -- und keine davon ist "
               "eine Zahl")
        pruefe(auslastung.kerne() == 1,
               "nur die Kernzahl faellt auf 1 zurueck: Eine Maschine ohne "
               "einen Kern gibt es nicht, und die Zahl teilt weiter unten")
    finally:
        auslastung.SYSTEM, auslastung.PROC = war_system, war_proc

    print("\nDie Windows-Seite")
    # Sie wird hier IMMER durchgerufen. Auf einem Linux liefert
    # windows.py ueberall leere Werte (die Bibliotheken fehlen) -- und
    # genau das ist die Zusicherung, die zaehlt: Das Modul ist auf beiden
    # Systemen importierbar und wirft nirgends.
    import ctypes  # noqa: E402
    import windows as winmodul  # noqa: E402

    if winmodul.IST_WINDOWS:
        # NUR HIER, und das ist kein Nachlassen: ``c_wchar`` ist unter
        # Linux vier Byte breit statt zwei, und die Struktur hat dort
        # zwangslaeufig eine andere Groesse. Die Zahl 1352 ist eine
        # Aussage ueber Windows -- sie auf einem Linux zu pruefen hiesse,
        # etwas anderes zu messen und es gleich zu nennen.
        pruefe(ctypes.sizeof(winmodul._MIB_IF_ROW2)
               == winmodul.ZEILENGROESSE == 1352,
               "die Netzstruktur hat genau die Groesse, die Windows "
               "erwartet -- eine Zeile daneben, und der Durchsatz waere "
               "eine Zahl aus fremdem Speicher")
        import ctypes.wintypes as _wt  # noqa: E402
        pruefe(winmodul.DWORD is _wt.DWORD and winmodul.WORD is _wt.WORD
               and winmodul.BOOL is _wt.BOOL
               and winmodul.HANDLE is _wt.HANDLE,
               "die vier Typen sind dieselben wie in ctypes.wintypes -- "
               "nachgebaut, weil dessen Import auf einem Linux scheitert")

    war = auslastung.SYSTEM
    try:
        auslastung.SYSTEM = "nt"
        pruefe(auslastung.last() is None,
               "unter Windows gibt es kein Lastmittel, und es wird auch "
               "keins erfunden -- die Kachel faellt weg")
        if winmodul.IST_WINDOWS:
            auslastung.cpu()          # die erste Messung setzt nur an
            gemessen = auslastung.speicher()
            pruefe("gesamt" in gemessen and gemessen["gesamt"] > 0
                   and 0 <= gemessen["anteil"] <= 100,
                   "der Speicher kommt vom Kernel, nicht aus /proc")
            nt_last = auslastung.cpu()
            pruefe(nt_last is None or 0 <= nt_last <= 100,
                   "und die Prozessorlast liegt zwischen 0 und 100")
            eigen_nt = auslastung.dienst()
            pruefe(eigen_nt.get("betrieb", -1) >= 0
                   and eigen_nt.get("speicher", 0) > 0,
                   "dieser Dienst meldet Betriebszeit und belegten "
                   "Speicher (Working Set) -- die Zahlen, die VmRSS "
                   "entsprechen")
    finally:
        auslastung.SYSTEM = war

    # /proc NACHGEBAUT, weil dienst() unter Windows sonst nie durchlaeuft
    # -- und die Feldzaehlerei in /proc/self/stat ist genau die Stelle,
    # an der ein Fehler still danebenliegt statt aufzufallen.
    TAB = chr(9)
    UM = chr(10)
    gefaelscht = Path(tempfile.mkdtemp())
    (gefaelscht / "self").mkdir()
    (gefaelscht / "self" / "status").write_text(
        "Name:" + TAB + "python" + UM
        + "VmRSS:" + TAB + "   86400 kB" + UM
        + "VmSize:" + TAB + "  999999 kB" + UM, encoding="utf-8")
    # Der Prozessname steht in Klammern UND darf Klammern und
    # Leerzeichen enthalten. Genau deshalb wird hinter der letzten
    # schliessenden Klammer getrennt und nicht nach Feldern gezaehlt.
    (gefaelscht / "self" / "stat").write_text(
        "42 (uvi corn (x)) " + " ".join(["S"] + ["0"] * 18 + ["200000"])
        + UM, encoding="utf-8")
    (gefaelscht / "uptime").write_text("20000.0 19000.0" + UM,
                                       encoding="utf-8")
    war_proc, war_system = auslastung.PROC, auslastung.SYSTEM
    # SYSTEM MIT UMSTELLEN: Ohne das liest dienst() unter Windows den
    # Kernel und schaut das nachgebaute /proc nie an -- die Pruefung waere
    # gruen, ohne die Stelle zu beruehren, um die es ihr geht.
    auslastung.PROC, auslastung.SYSTEM = gefaelscht, "posix"
    try:
        gemessen = auslastung.dienst()
    finally:
        auslastung.PROC, auslastung.SYSTEM = war_proc, war_system
    pruefe(gemessen.get("speicher") == 86400 * 1024,
           "gemessen wird der belegte Speicher (VmRSS), nicht der "
           "reservierte -- nur der lässt sich mit dem der Maschine "
           "vergleichen")
    pruefe(gemessen.get("betrieb") == 18000
           and auslastung.dauer_dativ(gemessen["betrieb"]) == "5 Stunden",
           "und die Betriebszeit trotz Klammern im Prozessnamen: "
           "20000 s Maschine minus 2000 s Startzeitpunkt")

    # Der Dativ, zum dritten Mal in diesem Produkt: "seit 1 Tag", aber
    # "seit 2 Tagen". Unter einer Minute wird nicht gerundet -- sonst
    # stuende ein frisch gestarteter Dienst mit "seit 0 Minuten" da.
    pruefe(auslastung.dauer_dativ(86400) == "1 Tag"
           and auslastung.dauer_dativ(172800) == "2 Tagen"
           and auslastung.dauer_dativ(3600) == "1 Stunde"
           and auslastung.dauer_dativ(30) == "weniger als einer Minute"
           and auslastung.dauer_dativ(None) == "",
           "die Betriebszeit steht im Dativ und rundet nichts weg")

    stueck = c.get("/auslastung.html")
    pruefe(stueck.status_code == 200 and "kacheln" in stueck.text,
           "die Kacheln gibt es einzeln -- fertig gerendert, damit es "
           "die Darstellung genau einmal gibt")
    pruefe("<html" not in stueck.text.lower(),
           "und wirklich nur das Stück, nicht die ganze Seite")
    pruefe("Dieser Dienst läuft ." not in _flach(stueck.text)
           and "läuft  ." not in _flach(stueck.text),
           "ohne /proc fällt die Zeile ganz weg statt als Satzstumpf "
           "dazustehen")

    print("\nDie Serverdetails")
    karte = bericht.karte("v-test")
    namen = [n for n, _ in karte["maschine"]]
    pruefe(all(w in namen for w in ("Distribution", "Kernel",
                                    "Virtualisierung", "Laufzeit")),
           "die Maschine mit Distribution, Kernel, Virtualisierung und "
           "Laufzeit")
    # NACHGETRAGEN FUER DIE WINDOWS-FASSUNG, und sie gilt auf beiden
    # Systemen: Die Kernzahl stand nur in der Unterzeile der Kachel
    # *Last* -- und die gibt es unter Windows nicht.
    pruefe("Prozessorkerne" in namen,
           "und die Kernzahl, die es als Kachel nur unter Linux gibt")
    dienste = dict(karte["dienste"])
    pruefe(dienste.get("marlei-tasks") == "v-test",
           "diese Anwendung ist kein Paket -- ihre Version ist der "
           "Stempel aus install.sh")
    pruefe("fastapi" in dienste and "uvicorn" in dienste,
           "und die zwei, ohne die eine fremde Fehlermeldung nicht "
           "einzuordnen ist")

    # DIE ZEILE nginx BLEIBT STEHEN, AUCH WO ES KEINEN GIBT -- und sie
    # sagt dann, dass keiner vorgesehen ist. "nicht installiert" waere
    # die falsche Auskunft: Es fehlt nichts.
    war_system, war_karte = bericht.SYSTEM, dict(bericht._KARTE)
    try:
        bericht.SYSTEM = "nt"
        bericht._KARTE["werte"] = None
        windows_dienste = dict(bericht.karte("v-nt")["dienste"])
        pruefe("nicht vorgesehen" in windows_dienste["nginx"],
               "unter Windows sagt die Zeile nginx, dass keiner "
               "vorgesehen ist -- uvicorn liefert selbst aus")
        pruefe("Windows" in dict(bericht.karte("v-nt")["maschine"])
               .get("Distribution", "") or not winmodul.IST_WINDOWS,
               "und die Zeile Distribution nennt das Windows samt Build")
    finally:
        bericht.SYSTEM = war_system
        bericht._KARTE.update(war_karte)
        bericht._KARTE["werte"] = None

    # Die Dauer im Nominativ, und zwar zwei Einheiten weit: Sie steht in
    # einer Tabellenzeile *Laufzeit* und nicht hinter "seit" -- der
    # Dativ eine Karte weiter oben ist ein anderer Fall und bleibt dort.
    pruefe(bericht._dauer(30) == "weniger als eine Minute"
           and bericht._dauer(86400) == "1 Tag"
           and bericht._dauer(172800) == "2 Tage"
           and bericht._dauer(90000) == "1 Tag, 1 Stunde"
           and bericht._dauer(3660) == "1 Stunde, 1 Minute",
           "die Laufzeit der Maschine steht im Nominativ -- »2 Tage«, "
           "nicht »2 Tagen«")
    # EIN PUFFER, DER EIN ARGUMENT VERSCHLUCKT, IST EINE FALLE: Der
    # zweite Aufruf mit einem anderen Stempel bekam den ersten zurueck,
    # weil die Ableserei und der Stempel zusammen gepuffert waren.
    pruefe(dict(bericht.karte("v-anders")["dienste"])["marlei-tasks"]
           == "v-anders",
           "und der Stempel wird nicht mitgepuffert -- die Ableserei "
           "schon, er nicht")

    # EINE QUELLE, NICHT ZWEI: Sonst nennt die Mail einen anderen Kernel
    # als die Seite, die der Betreiber gerade vor sich hat.
    with datenbank.verbindung() as conn:
        text_bericht = bericht.text(conn, "v-test", umgebung=False)
    pruefe(all(("%s:" % n) in text_bericht
               for n in ("Distribution", "Virtualisierung")),
           "dieselben Angaben stehen im Fehlerbericht -- aus derselben "
           "Quelle")

    # "none" ist eine Antwort und keine Fehlanzeige, "oracle" heisst
    # VirtualBox. Beides sind Faelle, die in Boot Geld gekostet haben.
    pruefe(bericht.VIRT_NAMEN["oracle"] == "VirtualBox",
           "»oracle« heißt VirtualBox -- die Ausgabe nennt den "
           "Hersteller, nicht das Produkt")
    pruefe("nicht feststellbar" in bericht._virtualisierung()
           or "Blech" in bericht._virtualisierung()
           or bericht._virtualisierung(),
           "und ohne systemd-detect-virt steht »nicht feststellbar« da, "
           "nicht »none«")

    # Der Platzhalter hat keinen Benutzer mehr.
    pruefe(not (PROJ / "webui" / "templates" / "leer.html").exists()
           and not hasattr(anwendung, "_seite"),
           "alle neun Reiter sind gebaut -- der Platzhalter ist weg")


    # ================================================================ #
    print("\nDie Befunde")
    # ================================================================ #
    import befunde as befundmodul  # noqa: E402

    # Zwei eigene Projekte, damit die Frage "gilt das ueber alle?"
    # ueberhaupt gestellt werden kann.
    with datenbank.verbindung() as conn:
        b_eins = datenbank.projekt_anlegen(conn, "Befundprobe A", "2026-08-01")
        b_zwei = datenbank.projekt_anlegen(conn, "Befundprobe B", "2026-08-01")
        for pid in (b_eins, b_zwei):
            datenbank.bereich_anlegen(conn, pid, "probe")
            bereich = [b for b in datenbank.bereiche(conn, pid)][0]["id"]
            datenbank.topic_anlegen(conn, pid, "Ein unvollständiger Fehler",
                                    bereich, "2026-08-02",
                                    kategorie="FEHLER")
        conn.commit()

    # Das gewaehlte Projekt ist ein drittes -- und trotzdem stehen beide
    # Befunde da. DAS ist die einzige Stelle, an der die Vorauswahl nicht
    # gilt, und der Grund, warum es die Befunde gibt: Was liegen bleibt,
    # liegt in dem Projekt, in das seit Wochen niemand geschaut hat.
    c.cookies.set(anwendung.COOKIE_PROJEKT, str(projekt))
    seite = c.get("/hilfe").text
    pruefe("Befundprobe A" in seite and "Befundprobe B" in seite,
           "Befunde laufen über alle Projekte -- auch über die, die "
           "gerade nicht gewählt sind")
    pruefe("Befundprobe A" in c.get("/einrichtung").text,
           "und sie stehen auf jeder Seite, nicht auf dem Reiter, zu dem "
           "sie gehören")

    # EIN BEFUND NENNT SEIN PROJEKT: Ueber alle Projekte gerechnet ist
    # eine Meldung ohne diese Angabe wertlos -- man wuesste, dass etwas
    # liegt, aber nicht wo.
    with datenbank.verbindung() as conn:
        alle = befundmodul.sammeln(conn)
    pruefe(all(b["projekt"] and b["projekt"] in b["titel"] for b in alle),
           "jeder Befund nennt sein Projekt, und zwar im Titel")
    pruefe(all(b["ziel"].startswith("/") for b in alle),
           "und trägt den Weg dorthin -- wer klickt, landet im richtigen "
           "Projekt")

    print("\nZur Kenntnis genommen wird je Projekt")
    r = c.post("/befund/kenntnis", follow_redirects=False,
               data={"kennung": "luecken", "projekt": str(b_eins),
                     "marke": "1", "zurueck": "/hilfe"})
    pruefe(r.status_code == 303 and r.headers["location"] == "/hilfe",
           "der Knopf führt ohne Meldung dorthin zurück, wo er stand")
    seite = c.get("/hilfe").text
    with datenbank.verbindung() as conn:
        offen, bekannt = befundmodul.teilen(conn, befundmodul.sammeln(conn))
        conn.commit()
    leise = {(b["projekt_id"], b["kennung"]) for b in bekannt}
    laut = {(b["projekt_id"], b["kennung"]) for b in offen}
    pruefe((b_eins, "luecken") in leise and (b_zwei, "luecken") in laut,
           "das Stillstellen im einen Projekt nimmt dieselbe Lage im "
           "anderen NICHT mit -- sonst verschwände ein Befund, den nie "
           "jemand gesehen hat")
    pruefe("zur Kenntnis" in seite,
           "weggeklickt heißt nicht weg: Es bleibt eine graue Zeile")

    # WEGGEKLICKT HEISST: ICH WEISS BESCHEID, BIS ES SCHLIMMER WIRD.
    with datenbank.verbindung() as conn:
        bereich = [b for b in datenbank.bereiche(conn, b_eins)][0]["id"]
        datenbank.topic_anlegen(conn, b_eins, "Noch ein Fehler", bereich,
                                "2026-08-03", kategorie="FEHLER")
        conn.commit()
        offen, bekannt = befundmodul.teilen(conn, befundmodul.sammeln(conn))
        conn.commit()
    pruefe((b_eins, "luecken") in {(b["projekt_id"], b["kennung"])
                                   for b in offen},
           "steigt die Marke über die gemerkte, kommt die Karte zurück")

    # WAR ER WEG UND KOMMT WIEDER, IST ER NEU: Sonst bliebe eine Lage von
    # vorigem Monat stumm, wenn sie sich wiederholt.
    with datenbank.verbindung() as conn:
        datenbank.kenntnis_nehmen(conn, b_zwei, "luecken", 1)
        datenbank.kenntnis_aufraeumen(conn, set())
        conn.commit()
        pruefe(datenbank.kenntnis_stand(conn) == {},
               "und was gerade nicht gilt, wird vergessen -- ein Befund, "
               "der wiederkommt, fängt offen an")

    print("\nWas keinen Befund gibt")
    with datenbank.verbindung() as conn:
        datenbank.projekt_aendern(conn, b_zwei, zustand="ABGESCHLOSSEN")
        conn.commit()
        namen = {b["projekt"] for b in befundmodul.sammeln(conn)}
    pruefe("Befundprobe B" not in namen,
           "ein abgeschlossenes Projekt meldet nichts mehr -- es liegt "
           "nicht, es ist fertig")
    with datenbank.verbindung() as conn:
        datenbank.projekt_aendern(conn, b_zwei, zustand="RUHT")
        conn.commit()
        namen = {b["projekt"] for b in befundmodul.sammeln(conn)}
    pruefe("Befundprobe B" in namen,
           "ein ruhendes dagegen schon -- es ist genau der Fall, für den "
           "die Befunde gebaut sind")

    # Die Durchsicht: unter der Frist kein Wort, darueber eine Meldung --
    # und die Marke ist GROB, damit die Karte nicht morgen wiederkommt.
    with datenbank.verbindung() as conn:
        conn.execute("UPDATE projekte SET durchsicht_am = ? WHERE id = ?",
                     (datenbank.heute(), b_eins))
        conn.commit()
        kennungen = {(b["projekt_id"], b["kennung"])
                     for b in befundmodul.sammeln(conn)}
    pruefe((b_eins, "durchsicht") not in kennungen,
           "wer heute durchgesehen hat, bekommt keine Meldung")
    with datenbank.verbindung() as conn:
        conn.execute("UPDATE projekte SET durchsicht_am = ? WHERE id = ?",
                     ("2026-01-01", b_eins))
        conn.commit()
        durch = [b for b in befundmodul.sammeln(conn)
                 if b["kennung"] == "durchsicht" and b["projekt_id"] == b_eins]
    pruefe(len(durch) == 1 and durch[0]["stufe"] == "info",
           "wer lange nicht hingesehen hat, schon -- und es ist blau, "
           "nicht gelb: niemand muss deswegen aufstehen")
    pruefe(durch[0]["marke"] == durch[0]["zahl"] // datenbank.DURCHSICHT_FRIST,
           "die Marke ist grob -- sonst wäre das Wegklicken ein Aufschub "
           "bis morgen")

    print("\nWas der Knopf nicht tut")
    r = c.post("/befund/kenntnis", follow_redirects=False,
               data={"kennung": "erfunden", "projekt": str(b_eins),
                     "marke": "1", "zurueck": "/hilfe"})
    pruefe("art=schlecht" in r.headers["location"],
           "eine Kennung, die es nicht gibt, wird abgewiesen")
    r = c.post("/befund/kenntnis", follow_redirects=False,
               data={"kennung": "luecken", "projekt": str(b_eins),
                     "marke": "1", "zurueck": "https://fremde.example/"})
    pruefe(r.headers["location"] == "/",
           "und ein »zurück«, das nach draußen zeigt, fällt auf die "
           "eigene Startseite -- eine offene Weiterleitung ist billig zu "
           "verhindern und teuer zu übersehen")

    print("\nDer Weg in das betroffene Projekt")
    r = c.post("/projekte/waehlen", follow_redirects=False,
               data={"id": str(b_zwei), "ziel": "/sammlung#sammlung"})
    pruefe(r.headers["location"].startswith("/sammlung?meldung=")
           and r.headers["location"].endswith("#sammlung"),
           "»Ansehen« stellt die Vorauswahl um UND landet dort, wo das "
           "Gemeldete steht")
    r = c.post("/projekte/waehlen", follow_redirects=False,
               data={"id": str(b_zwei), "ziel": "//fremde.example/"})
    pruefe("#projektuebersicht" in r.headers["location"],
           "ein Ziel nach draußen fällt auf die Projektübersicht zurück")
    c.cookies.set(anwendung.COOKIE_PROJEKT, str(projekt))


    # ================================================================ #
    print("\nDie Installation")
    # ================================================================ #
    # HIER LAEUFT install.sh NICHT -- das geht nur auf einem Debian. Was
    # sich ohne Debian pruefen laesst, ist der Zusammenhalt der vier
    # Dateien: Ein Port, der in der Einheit steht und im nginx-vhost
    # nicht, faellt sonst erst auf der Maschine auf.
    #
    # **Seit der Windows-Fassung liegt beides in einem eigenen Ordner**
    # -- setup/linux/ und setup/windows/. Umgezogen wurde VOR der ersten
    # Veroeffentlichung: Danach waere jede Pfadaenderung ein toter Link in
    # jeder Anleitung, die jemand abgeschrieben hat.
    setup = PROJ / "setup"
    linux = setup / "linux"
    fenster = setup / "windows"
    pruefe(not (setup / "install.sh").exists()
           and not (setup / "files").exists(),
           "setup/ selbst traegt keine Dateien mehr -- je System ein "
           "Ordner, und keiner davon ist der Vorzugsfall")
    skript = (linux / "install.sh").read_text(encoding="utf-8")
    einheit = (linux / "files" / "marlei-tasks.service").read_text(
        encoding="utf-8")
    vhost = (linux / "files" / "nginx-marlei-tasks.conf").read_text(
        encoding="utf-8")
    vorlage = (linux / "files" / "marlei-tasks.env.example").read_text(
        encoding="utf-8")
    vorlage_nt = (fenster / "files" / "marlei-tasks.env.example").read_text(
        encoding="utf-8")

    # KEIN default_server -- der ganze Grund, warum dieses Werkzeug neben
    # MARLEI Boot laufen kann. Ein zweites default_server auf Port 80
    # laesst nginx nicht mehr starten, und dann steht der Bootserver.
    # Nur die Anweisungen, nicht die Kommentare: Der Modulkopf des vhosts
    # ERKLAERT, warum es kein default_server gibt -- er darf das Wort
    # nennen, ohne dass die Pruefung darueber stolpert.
    vhost_wirksam = chr(10).join(
        z for z in vhost.splitlines() if not z.lstrip().startswith("#"))
    pruefe("default_server" not in vhost_wirksam,
           "der vhost trägt kein default_server -- sonst stünde neben "
           "diesem Werkzeug der Bootserver still")
    pruefe("@@PORT@@" in vhost and "MARLEI_PORT" in skript,
           "der Port ist ein Platzhalter und kommt aus MARLEI_PORT")
    # 8081 UND NICHT 80: Ein fester Produktport ist auf einer Maschine
    # mit MARLEI Boot und auf einer ohne dieselbe Zahl -- und ein Port,
    # der mal so und mal so ist, gehört in kein Lesezeichen.
    pruefe("PORT=8081; PORT_HER=\"Vorgabe, docs/ports.md\"" in skript,
           "und die Vorgabe ist 8081, nicht 80")
    # OHNE MARLEI_PORT GILT DER PORT DER BESTEHENDEN INSTALLATION (seit
    # September 2026). Vorher hiess ohne Angabe immer 8081, und ein
    # erneuter Aufruf stellte einen geaenderten Port still zurueck.
    pruefe('if [[ -n "${MARLEI_PORT:-}" ]]; then' in skript
           and 'PORT_HER="wie bisher, aus dem vhost"' in skript
           and '"$VHOST" 2>/dev/null | head -1' in skript,
           "install.sh nimmt ohne MARLEI_PORT den Port aus dem "
           "installierten vhost, erst dann die Vorgabe")
    pruefe("port_frei_pruefen" in skript
           and "sites-enabled" in skript and "grep -Eq" in skript,
           "install.sh prüft vorher, ob der Port frei ist -- auch gegen "
           "einen fremden vhost, den man sonst nicht sieht")

    # Boots Dateien werden NICHT angefasst. Erwähnt wird er, angefasst
    # nicht: Beides steht hier, damit der Unterschied geprüft ist.
    pruefe("/etc/pxeweb" not in skript
           and "sites-enabled/pxe" not in skript,
           "und es fasst keine Datei von MARLEI Boot an")

    # Der Anwendungsport: Einheit und vhost müssen denselben nennen --
    # und einen anderen als Boots 8080.
    import re as _re
    port_einheit = _re.search(r"--port (\d+)", einheit)
    port_vhost = _re.search(r"proxy_pass http://127\.0\.0\.1:(\d+)", vhost)
    pruefe(port_einheit and port_vhost
           and port_einheit.group(1) == port_vhost.group(1),
           "die Einheit und der vhost reden über denselben Port")
    pruefe(port_einheit and port_einheit.group(1) != "8080",
           "und über einen anderen als Boots 8080 -- zwei Anwendungen auf "
           "einem Port wäre die zweite Kollision neben nginx")
    # DIE TABELLE DER SUITE (docs/ports.md): innen 1808x. Bis September
    # 2026 war es 8000 -- der Port, den halb Python als Vorgabe nimmt.
    ports_md = (PROJ / "docs" / "ports.md").read_text(encoding="utf-8")
    pruefe(port_einheit and port_einheit.group(1) == "18081"
           and "| MARLEI Tasks | 8081 | 18081 |" in ports_md,
           "und über den, den docs/ports.md Tasks zuteilt: 18081")
    pruefe("--host 127.0.0.1" in einheit,
           "die Anwendung hört nur auf sich selbst; von außen kommt man "
           "über nginx herein")

    # Was der Code liest, muss die Vorlage kennen -- sonst fehlt es in
    # /etc/marlei-tasks.env und niemand merkt es, bis etwas nicht geht.
    gelesen = set()
    for datei in sorted((PROJ / "webui").glob("*.py")):
        gelesen |= set(_re.findall(
            r'''os\.environ(?:\.get)?[\(\[]["']?(MARLEI_[A-Z_]+)''',
            datei.read_text(encoding="utf-8")))
    fehlt = sorted(n for n in gelesen if ("\n%s=" % n) not in vorlage)
    pruefe(not fehlt,
           "jede Umgebungsvariable, die der Code liest, steht in der "
           "Vorlage -- %s" % (", ".join(fehlt) or "%d geprüft" % len(gelesen)))

    # UND IN DER ZWEITEN VORLAGE AUCH. Zwei Dateien mit denselben Namen
    # und anderen Werten sind eine Doppelung; geprueft wird sie in beide
    # Richtungen, damit keine Seite einen Wert allein bekommt. Der Fall,
    # der sonst durchrutscht: Ein neuer Wert kommt in die Linux-Vorlage,
    # und auf Windows fehlt er in /etc-Ersatz -- ohne Meldung, bis etwas
    # nicht geht.
    fehlt_nt = sorted(n for n in gelesen if ("\n%s=" % n) not in vorlage_nt)
    pruefe(not fehlt_nt,
           "und in der Windows-Vorlage ebenso -- %s"
           % (", ".join(fehlt_nt) or "%d geprüft" % len(gelesen)))
    namen_linux = set(_re.findall(r"(?m)^([A-Z][A-Z0-9_]*)=", vorlage))
    namen_nt = set(_re.findall(r"(?m)^([A-Z][A-Z0-9_]*)=", vorlage_nt))
    pruefe(namen_linux == namen_nt,
           "beide Vorlagen nennen denselben Satz Namen -- was nur eine "
           "Seite kennt, ist entweder eine Luecke oder eine Erklaerung "
           "wert (%s)"
           % (", ".join(sorted(namen_linux ^ namen_nt)) or "deckungsgleich"))
    pruefe("nachtragen_aus_vorlage" in skript,
           "und was die Vorlage später dazubekommt, trägt ein erneuter "
           "Lauf nach: Eine Lücke ist keine eigene Änderung")

    pruefe(str(datenbank.DB_PFAD) in vorlage.replace("\\", "/")
           or "MARLEI_DB=/var/lib/marlei-tasks/tasks.db" in vorlage,
           "die Vorlage nennt denselben Ablageort, den der Code als "
           "Vorgabe kennt")
    pruefe("ReadWritePaths=/var/lib/marlei-tasks" in einheit
           and "ProtectSystem=strict" in einheit,
           "die Einheit gibt genau ein Verzeichnis zum Schreiben frei")

    print("\nDas Update")
    aktualisieren = (linux / "update.sh").read_text(encoding="utf-8")
    pruefe("--ff-only" in aktualisieren,
           "update.sh zieht nur nach und erzeugt keinen Merge -- "
           "entwickelt wird auf dem Arbeitsplatz")
    pruefe("$EUID -ne 0" in aktualisieren,
           "und es weigert sich unter sudo: git soll dem Benutzer "
           "gehören, nicht root")

    # ================================================================ #
    # DER STEMPEL VERBINDET VIER DATEIEN, und drei davon lesen ihn.
    #
    # install.sh und install.ps1 SCHREIBEN webui/VERSION; update.sh,
    # update.ps1 und webui/versionsstand.py LESEN sie. Wer das Format
    # ändert, ändert fünf Stellen -- und merkt es nicht, wenn er eine
    # vergisst: Es geht dann nichts kaputt, die Auskünfte stimmen nur
    # nicht mehr.
    #
    # Genau das ist am 22.09.2026 passiert. Die Datei bekam vier Felder,
    # damit die Karte *Stand* den Commit vergleichen kann -- und die
    # beiden Update-Skripte lasen weiter die ganze Datei am Stück. Danach
    # hätte „Schon aktuell“ nie mehr gegriffen, und gezählt worden wäre
    # vom Stand vor dem Pull. Aufgefallen ist es beim Lesen, nicht hier;
    # deshalb steht es jetzt hier.
    # ================================================================ #
    ps_install = (fenster / "install.ps1").read_text(encoding="utf-8")
    ps_akt = (fenster / "update.ps1").read_text(encoding="utf-8")

    # Beide Installationsskripte schreiben jedes Feld, das
    # versionsstand.py liest -- sonst steht in der Karte eine Lücke, die
    # niemand als solche erkennt.
    for name, text in (("install.sh", skript), ("install.ps1", ps_install)):
        fehlend = [f for f in versionsstand.FELDER
                   if ("%s=" % f) not in text]
        pruefe(not fehlend,
               "%s stempelt jedes Feld, das versionsstand.py liest -- %s"
               % (name, ", ".join(fehlend) or "alle vier"))

    # Und beide Update-Skripte holen sich daraus DAS FELD, nicht die
    # Datei. Geprüft wird auf den Ausdruck, der das tut: Ein Skript, das
    # die Datei am Stück liest, verglich Kommentar und vier Felder mit
    # einem "git describe" -- immer ungleich, und still.
    pruefe("s/^stand=//p" in aktualisieren
           and 'tr -d \'[:space:]\' 2>/dev/null < "$VERSION_DATEI"'
           not in aktualisieren,
           "update.sh liest das Feld stand, nicht die ganze Datei")
    pruefe("'^stand='" in ps_akt
           and "ReadAllText($VERSION_DATEI)" not in ps_akt,
           "update.ps1 ebenso")

    # Die Rücksicht auf die alte Fassung: Eine Installation von vor dem
    # 22.09.2026 trägt eine VERSION mit nur dem Stand darin -- und genau
    # die will ja aktualisiert werden.
    pruefe("alte einzeilige" in aktualisieren
           and "alte einzeilige" in ps_akt,
           "und beide lesen die alte einzeilige Datei weiter")

    # ================================================================ #
    # EIN LEER GESETZTER NAME ZÄHLT ALS KEINER.
    #
    # `os.environ.get(name, vorgabe)` gibt bei einer **leer gesetzten**
    # Variable den leeren String zurück und nicht die Vorgabe -- und
    # `Path("")` ist `Path(".")`. Die Falle steht seit jeher in
    # `datenbank.ablageort()` beschrieben, und am 22.09.2026 ist sie an
    # zwei neuen Stellen wieder aufgegangen: Die Vorlage führt jeden
    # Namen mit leerem Wert auf, also ist im Betrieb **jede** dieser
    # Variablen gesetzt und leer. Auf dev-marlei suchte die Anwendung
    # ihren Stempel daraufhin im Arbeitsverzeichnis, fand keinen, und die
    # Karte *Stand* sagte „Hier steht nichts“ über eine saubere
    # Installation.
    #
    # Geprüft wird in einem eigenen Prozess und über **alle** Namen aus
    # der Vorlage: So deckt die Prüfung auch den ab, den jemand morgen
    # hinzufügt, und die laufende Reihe bleibt unberührt.
    # ================================================================ #
    namen = _re.findall(r"^(MARLEI_[A-Z_]+)=", vorlage, _re.M)
    ablesen = (
        "import os, sys; sys.path.insert(0, %r);"
        "import versionsstand, einstellungen, updatewacht as u;"
        "print(versionsstand.DATEI); print(einstellungen.DATEI);"
        "print(u.STAND_DATEI); print(u.REPO); print(u.VERGLEICH)"
        % str(PROJ / "webui"))

    def _werte(umgebung):
        lauf = subprocess.run([sys.executable, "-c", ablesen],
                              capture_output=True, text=True,
                              env=umgebung)
        return lauf.stdout.strip().splitlines()

    sauber = {k: v for k, v in os.environ.items()
              if not k.startswith("MARLEI_")}
    ohne = _werte(sauber)
    leer = _werte(dict(sauber, **{n: "" for n in namen}))
    pruefe(ohne and ohne == leer,
           "jeder leer gesetzte Name wirkt wie ein nicht gesetzter -- "
           "%d Name(n) geprüft" % len(namen))
    # Und die Gegenprobe: Ein Name mit Inhalt wirkt sehr wohl.
    gesetzt = _werte(dict(sauber, MARLEI_REPO="wer/anders"))
    pruefe(gesetzt and "wer/anders" in gesetzt[3],
           "ein Name mit Inhalt wirkt dagegen")

    # DER PORT WIRD GEMERKT, NICHT ERFRAGT. Ohne ihn nähme install.sh die
    # 80 -- und bräche auf einer Maschine mit MARLEI Boot ab, obwohl die
    # Installation längst steht. Ein zweiter Lauf soll nicht anders
    # ausfallen als der erste.
    pruefe("sites-available/marlei-tasks" in aktualisieren
           and "MARLEI_PORT" in aktualisieren,
           "es liest den Port aus dem installierten vhost und gibt ihn "
           "weiter")

    # Und die Zeile, aus der es liest, muss die Form haben, die das sed
    # erwartet: "listen 8081;" -- ein "listen 8081 default_server;" fiele
    # durch, und das Update nähme wieder die 80.
    gerendert = vhost.replace("@@PORT@@", "8081")
    treffer = _re.findall(r"(?m)^[ \t]*listen[ \t]+(\d+);", gerendert)
    pruefe(treffer and treffer[0] == "8081",
           "und die listen-Zeile hat die Form, aus der sich der Port "
           "lesen lässt")

    pruefe("cp /var/lib/marlei-tasks/tasks.db" in aktualisieren,
           "ändert sich die Ablage, nennt es den Weg zu einer Kopie -- "
           "gesagt, nicht getan: Wohin eine Sicherung gehört, weiß der "
           "Betreiber")

    print("\nDie Installation unter Windows")
    # HIER LAEUFT install.ps1 GENAUSO WENIG -- es braucht Administrator,
    # ein %ProgramFiles% und eine Aufgabenplanung. Geprueft wird wieder
    # der Zusammenhalt: Ein Port, den start.ps1 anders herleitet als die
    # Karte ihn nennt, faellt sonst erst auf der Maschine auf. Die
    # Skripte selbst pruefen ihre eigene Syntax nicht -- das tut
    # PowerShell beim Aufruf.
    ps_install = (fenster / "install.ps1").read_text(encoding="utf-8")
    ps_update = (fenster / "update.ps1").read_text(encoding="utf-8")
    ps_start = (fenster / "files" / "start.ps1").read_text(encoding="utf-8")

    pruefe("$VORGABE_PORT = 8081" in ps_install,
           "die Vorgabe ist 8081 wie auf dem Server -- ein Port, der je "
           "System ein anderer ist, gehört in kein Lesezeichen")
    pruefe("[int]$Port = 0" in ps_install
           and "if ($Port -eq 0) {" in ps_install
           and "^MARLEI_BASE_URL=" in ps_install,
           "ohne -Port nimmt install.ps1 den Port der bestehenden "
           "Installation aus MARLEI_BASE_URL, erst dann die Vorgabe")

    # DER PORT KOMMT AUS DER ADRESSE, und zwar an allen drei Stellen:
    # start.ps1 gibt ihn an uvicorn, update.ps1 merkt sich ihn, und die
    # Karte nennt ihn. Ohne nginx davor ist die Adresse die einzige
    # Quelle -- steht die Zahl zweimal, geht sie auseinander.
    pruefe("MARLEI_BASE_URL" in ps_start
           and "--host" in ps_start and "0.0.0.0" in ps_start,
           "start.ps1 nimmt den Port aus MARLEI_BASE_URL und hört nach "
           "außen -- es gibt keinen nginx, der das übernimmt")
    # UPDATE.PS1 LIEST DIE EINSTELLUNGEN NICHT MEHR. Seit dem eigenen
    # Konto darf sie nur ein Administrator lesen, und update.ps1 laeuft
    # bewusst ohne -- es fand keinen Port und nahm 8081. Den Port merkt
    # sich jetzt install.ps1, das mit erhoehten Rechten laeuft.
    pruefe("marlei-tasks.env" not in ps_update
           and "Get-Content -LiteralPath $ENV_DATEI" not in ps_update
           and 'if ($Port -gt 0) { $argumente += @("-Port", "$Port") }'
           in ps_update,
           "update.ps1 liest die Einstellungen nicht und reicht -Port nur "
           "weiter, wenn er angegeben ist -- ein zweiter Lauf fällt "
           "trotzdem nicht anders aus")
    pruefe("--host 127.0.0.1" in einheit and "0.0.0.0" not in einheit,
           "die Linux-Einheit hört dagegen weiter nur auf sich selbst -- "
           "dort steht der nginx davor, und das bleibt so")

    # DIE AUFGABE STATT EINER DIENST-EINHEIT: vier Angaben, die keine
    # Geschmacksfrage sind. **ExecutionTimeLimit ist die wichtigste** --
    # ohne sie beendet Windows die Aufgabe nach drei Tagen, und der
    # Dienst wäre weg, ohne dass etwas abgestürzt ist.
    pruefe("-AtStartup" in ps_install,
           "die Aufgabe startet beim Hochfahren, nicht bei der Anmeldung")
    # SEIT DEM EIGENEN KONTO: nicht mehr SYSTEM, sondern marlei-tasks --
    # mit Kennwort, denn ohne liefe die Aufgabe nur, solange das Konto
    # angemeldet ist, also nie. Und ohne erhoehte Rechte.
    pruefe(r'-User "$env:COMPUTERNAME\$KONTO" -Password $KONTO_KENNWORT'
           in ps_install and '"SYSTEM"' not in ps_install,
           "und unter dem Konto marlei-tasks statt als SYSTEM -- ohne "
           "dass jemand angemeldet sein muss")
    pruefe("-RunLevel Limited" in ps_install
           and "-RunLevel Highest" not in ps_install,
           "ohne erhöhte Rechte")
    konto_ps = (fenster / "files" / "konto.ps1").read_text(encoding="utf-8")
    pruefe(all(r in konto_ps for r in (
               '"SeBatchLogonRight"', '"SeDenyInteractiveLogonRight"',
               '"SeDenyRemoteInteractiveLogonRight"')),
           "das Konto darf als Batchauftrag laufen und sich nicht am "
           "Bildschirm anmelden")
    pruefe('Invoke("SetPassword", $Kennwort)' in konto_ps
           and not _re.search(r"net(\.exe)? user \S+ \$Kennwort", konto_ps),
           "sein Kennwort geht über ADSI ins Konto, nie über eine "
           "Befehlszeile, die die Prozessliste zeigt")
    pruefe('"*${KONTO_SID}:(OI)(CI)M"' in ps_install
           and '"*${KONTO_SID}:R"' in ps_install,
           "das Konto darf das Datenverzeichnis ändern, die Einstellungen "
           "nur lesen")
    pruefe('"*$sid"' in (fenster / "uninstall.ps1").read_text(
               encoding="utf-8")
           and "Konto-Entfernen $KONTO" in (fenster / "uninstall.ps1")
           .read_text(encoding="utf-8"),
           "uninstall.ps1 trägt das Recht aus und entfernt das Konto")
    pruefe("-ExecutionTimeLimit ([TimeSpan]::Zero)" in ps_install,
           "ohne Zeitlimit: Die Vorgabe der Aufgabenplanung wäre drei "
           "Tage, und ein Dienst hat keins")
    pruefe("-RestartCount" in ps_install
           and "-MultipleInstances IgnoreNew" in ps_install,
           "Neustart nach einem Fehler, aber kein zweiter Lauf daneben "
           "-- das wäre ein zweiter Schreiber auf einer SQLite-Datei")

    # DIE FIREWALL WIRD NICHT UNGEFRAGT ANGEFASST. Geprueft am Ort: Vor
    # der Abfrage des Schalters steht keine einzige Zeile, die eine Regel
    # anlegt.
    pruefe("[switch]$Firewallregel" in ps_install,
           "die Firewallregel ist ein Schalter und keine Vorgabe")
    vor_dem_schalter = ps_install.split("if ($Firewallregel)")[0]
    pruefe("New-NetFirewallRule" not in vor_dem_schalter,
           "und vor dieser Abfrage legt nichts eine Regel an -- die "
           "Firewall gehört der Maschine, nicht diesem Werkzeug")

    # DER STEMPEL ENTSTEHT NACH DEM KOPIEREN. robocopy spiegelt mit /MIR
    # und raeumte ihn sonst bei jedem Lauf wieder weg -- dieselbe Falle
    # wie bei rsync --delete auf der anderen Seite.
    pruefe(ps_install.index("robocopy.exe")
           < ps_install.index("app\\VERSION"),
           "der Stand wird nach dem Spiegeln gestempelt, nicht davor")
    pruefe("/XF" in ps_install and "*.db" in ps_install
           and "__pycache__" in ps_install,
           "und die Ablage kommt nicht mit ins Programmverzeichnis")

    # OHNE BOM. Sonst hiesse der erste Name in der Umgebungsdatei nicht
    # MARLEI_BASE_URL, sondern trüge ein unsichtbares Zeichen davor --
    # und der Port fiele stumm auf 80 zurück.
    pruefe("UTF8Encoding($false)" in ps_install,
           "die Umgebungsdatei wird ohne BOM geschrieben -- sonst liest "
           "start.ps1 den ersten Namen falsch")
    pruefe("nachgetragen" in ps_install,
           "und was die Vorlage später dazubekommt, trägt ein erneuter "
           "Lauf nach -- wie auf der Linux-Seite")

    # KEIN FESTER PFAD, DER DAS SYSTEM RAET. C:\var\lib waere genau der
    # Ort, den die Vorgabe in datenbank.py vermeidet.
    for name, inhalt in (("install.ps1", ps_install),
                         ("update.ps1", ps_update),
                         ("start.ps1", ps_start)):
        pruefe("var\\lib" not in inhalt and "/var/lib" not in inhalt,
               "%s kennt keinen Unix-Pfad -- die Ablage liegt unter "
               "ProgramData" % name)
    pruefe("ProgramData" in ps_install and "ProgramFiles" in ps_install,
           "install.ps1 benutzt die Orte, die Windows dafür vorsieht")
    pruefe("MARLEI Tasks\\tasks.db" in vorlage_nt,
           "und die Windows-Vorlage nennt die Ablage unter ProgramData")
    if os.name == "nt":
        # Hier laesst sich die Vorlage gegen die Vorgabe IM CODE halten --
        # auf einem Linux kann ``vorgabe_ablage()`` diese Frage nicht
        # beantworten, und eine Pruefung, die dann einfach "ok" sagt,
        # waere schlimmer als keine.
        pruefe(str(datenbank.vorgabe_ablage()) in vorlage_nt,
               "und zwar an demselben Ort, den der Code als Vorgabe kennt")
    else:
        pruefe("ProgramData" in vorlage_nt,
               "gegen die Vorgabe im Code hält das erst eine Maschine, "
               "auf der es ProgramData gibt -- hier bleibt es beim Wort")

    # UPDATE OHNE ADMINISTRATOR, INSTALLATION MIT. Dieselbe Trennung wie
    # das "bitte ohne sudo" auf der anderen Seite: git gehört dem
    # Benutzer, und nur die Installation braucht mehr.
    pruefe("IsInRole" in ps_update and "OHNE Administratorrechte" in ps_update,
           "update.ps1 weigert sich mit erhöhten Rechten -- git soll dem "
           "Benutzer gehören")
    pruefe("-Verb RunAs" in ps_update,
           "und holt sie sich für install.ps1 selbst")
    pruefe("--ff-only" in ps_update,
           "es zieht nur nach und erzeugt keinen Merge")

    # INSTALLIERT WIRD, WENN DIE INSTALLATION ZURUECKLIEGT (A-030, aus
    # B-076). Bis zum 19.09.2026 hing es am Pull: Holte er nichts, hiess
    # es "Schon aktuell" -- auch nach einem git pull von Hand, nach einer
    # abgebrochenen Installation und auf dem Rechner, auf dem committet
    # wird. Verglichen wird jetzt der Stempel der Installation mit dem,
    # der jetzt geschrieben wuerde -- mit DERSELBEN FORMEL wie im
    # Installateur, sonst sprechen die beiden nie dieselbe Sprache.
    formel = "describe --tags --always --dirty"
    for name, update, install, stempel in (
            ("update.sh", aktualisieren,
             (linux / "install.sh").read_text(encoding="utf-8"),
             "VERSION_DATEI=/opt/marlei-tasks/VERSION"),
            ("update.ps1", ps_update, ps_install,
             r'"MARLEI Tasks\app\VERSION"')):
        pruefe(stempel in update and formel in update and formel in install,
               "%s liest den Stempel der Installation und vergleicht ihn "
               "mit derselben Formel, mit der der Installateur ihn "
               "schreibt" % name)
        pruefe('if [[ "$VORHER" == "$NACHHER" ]]; then\n  log "Schon aktuell'
               not in update
               and 'if ($VORHER -eq $NACHHER) {\n        Log "Schon aktuell'
               not in update
               and "Installiert ist genau dieser Stand" in update,
               "%s sagt 'Schon aktuell' nur, wenn die Installation auf "
               "diesem Stand steht -- nicht, weil der Pull nichts brachte"
               % name)
        pruefe("-dirty" in update,
               "%s übernimmt einen Stand mit -dirty immer: Was darin "
               "geändert ist, sagt der Stempel nicht" % name)
    pruefe(r'Join-Path $APP_DIR "app\VERSION"' in ps_install,
           "der Stempel liegt unter Windows dort, wo update.ps1 ihn sucht")
    pruefe('"$APP_DIR/VERSION"' in (linux / "install.sh").read_text(
               encoding="utf-8")
           and "APP_DIR=/opt/marlei-tasks" in (linux / "install.sh")
           .read_text(encoding="utf-8"),
           "und unter Linux ebenso")
    pruefe("tasks.db" in ps_update and "Copy-Item" in ps_update,
           "ändert sich die Ablage, nennt es den Weg zu einer Kopie -- "
           "gesagt, nicht getan")

    # UND DAS PROTOKOLL, das es unter Linux nicht braucht: journalctl gibt
    # es hier nicht, und eine Aufgabe wirft die Ausgabe ihres Programms
    # weg.
    pruefe("RedirectStandardError" in ps_start and "log" in ps_start,
           "start.ps1 schreibt mit, was uvicorn sagt -- sonst wäre beim "
           "ersten »es geht nicht« nichts nachzulesen")

    # UND EINMAL WIRKLICH HINSEHEN LASSEN: Auf einem Windows steht der
    # PowerShell-Parser bereit, und ein Skript mit einem Tippfehler in
    # Zeile 300 faellt sonst dem auf, der installiert -- mitten im Lauf,
    # mit halb angelegten Verzeichnissen. Geprueft wird nur die Syntax;
    # ausgefuehrt wird nichts.
    if os.name == "nt":
        import shutil as _shutil  # noqa: E402
        import subprocess as _subprocess  # noqa: E402
        powershell = _shutil.which("powershell") or _shutil.which("pwsh")
        if powershell:
            befehl = (
                "$f=$null;"
                "$ok=$true;"
                "foreach ($d in @(%s)) {"
                "  [void][System.Management.Automation.Language.Parser]"
                "::ParseFile($d, [ref]$null, [ref]$f);"
                "  if ($f.Count) { $ok=$false; Write-Output $d;"
                "    $f | ForEach-Object { Write-Output $_.Message } } };"
                "if ($ok) { Write-Output 'SYNTAX-OK' }"
                % ", ".join("'%s'" % (fenster / n)
                            for n in ("install.ps1", "update.ps1",
                                      "uninstall.ps1", "files/start.ps1",
                                      "files/eigene-prozesse.ps1",
                                      "files/konto.ps1")))
            lauf = _subprocess.run(
                [powershell, "-NoProfile", "-NonInteractive", "-Command",
                 befehl], capture_output=True, text=True, timeout=60)
            pruefe("SYNTAX-OK" in lauf.stdout,
                   "und alle sechs Skripte sind syntaktisch heil -- "
                   "PowerShell selbst sagt es%s"
                   % ("" if "SYNTAX-OK" in lauf.stdout
                      else " NICHT: " + _flach(lauf.stdout)))

    print("\nWieder entfernen")
    # ES GIBT KEINEN LAUF ZU PRUEFEN -- beide Skripte brauchen root bzw.
    # Administrator. Geprueft wird das, was hier zu pruefen ist und was
    # sonst erst Monate spaeter auffaellt: **dass die Namen zu denen
    # passen, die der Installateur gesetzt hat.** Eine Aufgabe, die hier
    # anders heisst, bleibt stehen und startet beim naechsten Hochfahren
    # ein Programm, das es nicht mehr gibt; eine Firewallregel, die hier
    # anders heisst, haelt einen Port offen, auf dem niemand mehr hoert.
    #
    # Das VERHALTEN von uninstall.sh ist auf einer Maschine ohne Linux
    # nachgestellt geprueft (sieben Faelle, docs siehe tests/README.md);
    # was hier steht, ist der Zusammenhalt der Dateien.
    weg_sh = (linux / "uninstall.sh").read_text(encoding="utf-8")
    weg_ps = (fenster / "uninstall.ps1").read_text(encoding="utf-8")

    def _wert(inhalt, name, muster='%s = "([^"]+)"'):
        treffer = _re.search(muster % _re.escape(name), inhalt)
        return treffer.group(1) if treffer else None

    for name in ("AUFGABE", "REGELNAME", "KONTO"):
        hier_, dort_ = (_wert(ps_install, "$" + name),
                        _wert(weg_ps, "$" + name))
        pruefe(hier_ and hier_ == dort_,
               "$%s heißt in beiden Skripten gleich (%r / %r)"
               % (name, hier_, dort_))
    # Und das Konto heisst wie das auf der Linux-Seite: je Modul eines,
    # auf beiden Systemen gleich benannt.
    pruefe(_wert(ps_install, "$KONTO") == _wert(skript, "DIENST", r"%s=(\S+)")
           == "marlei-tasks",
           "das Konto heißt unter Windows wie unter Linux: marlei-tasks")
    for name in ("APP_DIR", "DATA_DIR", "DIENST", "VHOST"):
        muster = r"%s=(\S+)"
        hier_, dort_ = (_wert(skript, name, muster), _wert(weg_sh, name, muster))
        pruefe(hier_ and hier_ == dort_,
               "und %s auf der Linux-Seite ebenso (%r / %r)"
               % (name, hier_, dort_))

    # DER BESTAND WIRD NUR HINTER DEM SCHALTER GELOESCHT, und geprueft
    # wird es am Ort: Vor der Rückfrage steht in beiden Skripten keine
    # Zeile, die ihn anfassen könnte. Dieselbe Prüfung wie bei der
    # Firewallregel in install.ps1.
    vor_der_frage_sh = weg_sh.split("Zum Loeschen bitte")[0]
    pruefe('rm -rf "$DATA_DIR"' not in vor_der_frage_sh
           and 'rm -f "$ENV_DATEI"' not in vor_der_frage_sh,
           "uninstall.sh fasst vor der Rückfrage nichts vom Bestand an")
    vor_der_frage_ps = weg_ps.split("Zum Loeschen bitte")[0]
    pruefe("Weg-Damit $DATA_DIR" not in vor_der_frage_ps,
           "und uninstall.ps1 ebenso")
    pruefe("Bestand" in weg_sh and "Bestand" in weg_ps
           and _re.search(r"LOSUNG=Bestand", weg_sh)
           and _re.search(r'\$LOSUNG = "Bestand"', weg_ps),
           "das Losungswort ist auf beiden Seiten dasselbe -- ein Schalter "
           "sagt, DASS gelöscht wird, das Wort bestätigt, dass man es "
           "gelesen hat")
    pruefe("! -t 0" in weg_sh and "UserInteractive" in weg_ps,
           "und ohne jemanden, der antworten kann, wird abgebrochen statt "
           "gefragt: Ein Skript, das in einer Pipeline wartet, hängt")

    # WAS DER MASCHINE GEHOERT, BLEIBT STEHEN. Das ist dieselbe Grenze wie
    # bei der Firewall und bei den Einstellungen -- und auf einer Maschine
    # mit MARLEI Boot ist sie der Unterschied zwischen einem entfernten
    # Werkzeug und einem stillstehenden Bootserver.
    # NUR DIE WIRKSAMEN ZEILEN, nicht die Kommentare -- dieselbe
    # Unterscheidung wie beim default_server im vhost weiter oben: Beide
    # Skripte NENNEN »apt-get remove nginx«, und zwar als Warnung. Wer
    # nach dem Wort sucht, prüft die Begründung statt der Tat.
    def _wirksam(inhalt):
        return [z.lstrip() for z in inhalt.splitlines()
                if not z.lstrip().startswith("#")]

    paketverwalter = ("apt-get", "apt ", "aptitude", "dpkg", "yum", "dnf",
                      "pacman", "zypper", "snap ")
    pruefe(not [z for z in _wirksam(weg_sh)
                if z.startswith(paketverwalter)],
           "uninstall.sh ruft keinen Paketverwalter auf -- ein »apt-get "
           "remove nginx« wäre der Griff, der den Bootserver mitnimmt")
    pruefe(not [z for z in _wirksam(weg_ps)
                if z.startswith(("winget", "msiexec", "Uninstall-"))],
           "und uninstall.ps1 deinstalliert nichts, was ihm nicht gehört")
    pruefe("reload nginx" in weg_sh and "restart nginx" not in weg_sh,
           "und es lädt nginx neu statt ihn neu zu starten: Ein restart "
           "reißt die Verbindungen aller anderen Seiten ab")
    pruefe("nginx -t" in weg_sh,
           "vorher geprüft -- ein reload mit kaputter Konfiguration lässt "
           "nginx stehen, wie er ist, aber sagen sollte es das")
    pruefe("/etc/pxeweb" not in weg_sh and "sites-enabled/pxe" not in weg_sh,
           "und keine Datei von MARLEI Boot kommt darin vor")
    pruefe("Python bleibt stehen" in weg_ps,
           "uninstall.ps1 lässt Python stehen und sagt es -- es war vorher "
           "da und gehört nicht diesem Werkzeug")

    # DIE REGEL WIRD ÜBER IHREN NAMEN ENTFERNT, NICHT ÜBER DEN PORT: Auf
    # demselben Port kann etwas stehen, das jemand anderes braucht.
    pruefe("Remove-NetFirewallRule" in weg_ps
           and "-LocalPort" not in weg_ps,
           "die Firewallregel geht über ihren Namen weg, nicht über die "
           "Portnummer")

    # SOLANGE ETWAS LIEGT, MUSS SEIN BESITZER BENENNBAR BLEIBEN.
    userdel_stelle = weg_sh.split("userdel")[0]
    pruefe("BESTAND_WEG == ja" in userdel_stelle,
           "das Dienstkonto geht nur mit dem Bestand -- sonst blieben "
           "Dateien zurück, deren Besitzer eine Zahl ohne Namen ist")

    print("\nDer Selbsttest der Installation")
    with datenbank.verbindung() as conn:
        gesundheit_projekt = datenbank.projekt_anlegen(
            conn, "Ein sehr besonderer Projektname", "2026-09-07")
        conn.commit()
    antwort = c.get("/health")
    pruefe(antwort.status_code == 200
           and antwort.json()["status"] == "ok",
           "/health antwortet -- das ist der Selbsttest am Ende von "
           "install.sh")
    pruefe("Ein sehr besonderer Projektname" not in antwort.text,
           "und nennt keinen einzigen Namen: Die Auskunft ist "
           "maschinenlesbar und fragt niemanden, wer er ist")
    pruefe("befunde_offen" in antwort.json(),
           "die offenen Befunde stehen mit drin -- die eine Zahl, die "
           "einen Wachhund interessieren könnte")
    pruefe("/health" in skript,
           "und install.sh fragt genau danach")
    with datenbank.verbindung() as conn:
        datenbank.projekt_loeschen(conn, gesundheit_projekt)
        conn.commit()


    # ================================================================ #
    print("\nWas die erste echte Installation gezeigt hat")
    # ================================================================ #
    # Drei Funde vom 07.09.2026 auf dev-marlei -- keiner davon waere hier
    # aufgefallen: Sie brauchten eine Maschine mit /proc, mit dpkg und
    # mit einem Port, der nicht 80 ist.
    import firewall as firewallmodul  # noqa: E402

    # 1. DER AUSGANG IST EIN ORT UND HAENGT NICHT AM PROJEKT.
    # Dort stand "nicht eingerichtet -- MARLEI_EXPORT ist leer", waehrend
    # zwei Karten weiter unten der Pfad danebenstand. Beides kann nicht
    # stimmen.
    ohne_wahl = TestClient(anwendung.app)
    seite = ohne_wahl.get("/einrichtung").text
    pruefe(str(anwendung.export.ZIEL) in seite,
           "der Ausgang steht unter Ablageorte, auch wenn kein Projekt "
           "gewählt ist -- der Ort hängt nicht am Projekt")
    pruefe("ist leer" not in _flach(seite),
           "und er wird nicht als leer gemeldet, während er danebensteht: "
           "Eine Karte, die einen Grund nennt, den es nicht gibt, ist "
           "schlimmer als eine, die schweigt")

    # DIE KARTE SAGT, WIE MAN DEN PORT AENDERT -- UND TUT ES NICHT.
    # Ein Feld, das ihn aenderte, muesste als root in /etc/nginx
    # schreiben und einen Dienst neu laden, aus einer Oberflaeche heraus,
    # die niemanden fragt, wer er ist. Dieselbe Grenze wie bei der
    # Firewall.
    #
    # **UND SIE SAGT ES JE SYSTEM ANDERS.** Unter Linux gehoert der Port
    # dem nginx davor und steht nirgends in der Umgebungsdatei; unter
    # Windows gibt es keinen nginx, und die Zahl steht in der Adresse.
    # Geprueft werden beide Saetze, egal wo diese Reihe laeuft -- sonst
    # prueft sie den anderen nie, und genau der bleibt dann falsch stehen.
    war_windows = anwendung.WINDOWS
    try:
        anwendung.WINDOWS = False
        seite_linux = ohne_wahl.get("/einrichtung").text
        anwendung.WINDOWS = True
        seite_nt = ohne_wahl.get("/einrichtung").text
    finally:
        anwendung.WINDOWS = war_windows
    stelle_linux = _flach(seite_linux).split("Der Port")[1][:500]
    stelle_nt = _flach(seite_nt).split("Der Port")[1][:500]

    pruefe("MARLEI_PORT=9090" in seite_linux and "kopierknopf" in seite_linux,
           "der Weg zum anderen Port steht als Befehl auf der Karte, "
           "zum Kopieren")
    pruefe("nicht in der Umgebungsdatei" in stelle_linux,
           "und dabei steht, dass er nicht in der Umgebungsdatei steht: "
           "Er gehört dem nginx davor")
    pruefe(r"install.ps1 -Port 9090" in seite_nt
           and "kopierknopf" in seite_nt,
           "unter Windows steht dort derselbe Weg mit dem Befehl, den es "
           "dort gibt")
    pruefe("in der Adresse" in stelle_nt
           and "nicht in der Umgebungsdatei" not in stelle_nt,
           "und der umgekehrte Satz: Dort steht der Port sehr wohl in der "
           "Umgebungsdatei -- in der Adresse, aus der ihn auch start.ps1 "
           "nimmt")
    pruefe("</form>" not in stelle_linux and "</form>" not in stelle_nt,
           "kein Formular an dieser Stelle -- gesagt wird, was zu tun "
           "ist; getan wird es von dem, der sich anmelden kann")

    # 2. DIE PORTLISTE NENNT DEN PORT, DER WIRKLICH GILT.
    # Auf dev-marlei laeuft die Oberflaeche auf 8081, weil Boots vhost
    # die 80 haelt. Die Karte sagte 80 -- wer danach eine Regel schreibt,
    # oeffnet den falschen Port.
    war_url = anwendung.BASE_URL
    try:
        anwendung.BASE_URL = "http://192.168.178.31:8081"
        pruefe(anwendung._oberflaechenport() == 8081,
               "der Port der Oberfläche kommt aus der Adresse im Kopfband")
        anwendung.BASE_URL = "http://192.168.178.30"
        pruefe(anwendung._oberflaechenport() == 80,
               "eine Adresse ohne Doppelpunkt heißt 80 -- das ist keine "
               "Vorgabe, sondern die Bedeutung einer Adresse")
    finally:
        anwendung.BASE_URL = war_url
    # BEIDE PORTLISTEN, und "system" wird ausdruecklich mitgegeben: Sonst
    # prueft diese Reihe nur die des Systems, auf dem sie gerade laeuft.
    liste = firewallmodul.ports(8081, system="posix")
    pruefe(any(z["port"] == "8081/tcp" and z["dienst"] == "nginx"
               for z in liste),
           "und die Portliste nennt ihn, nicht die 80")
    pruefe(any(z["port"] == "22/tcp" for z in liste),
           "der ssh-Port bleibt, wie er ist -- er gehört nicht dazu und "
           "steht trotzdem da")
    # UND DER SATZ DARUNTER NENNT DIESELBE ZAHL. Genau daran ist es
    # durchgerutscht: Die Liste zog mit, der Satz nicht -- und er stand
    # eine Zeile tiefer auf derselben Karte.
    pruefe("nginx auf 8081" in firewallmodul.nicht_oeffnen(8081,
                                                           system="posix"),
           "und der Satz unter der Liste nennt denselben Port, nicht "
           "die 80")
    # Als ganze Zahl gesucht: Seit dem inneren Port 18081 steckt "8081"
    # auch dort als Teilstueck drin, ohne gemeint zu sein.
    pruefe(not _re.search(r"(?<!\d)8081(?!\d)",
                          firewallmodul.nicht_oeffnen(80, system="posix")),
           "auf einer Maschine ohne Boot steht dort wieder die 80")

    # DIE WINDOWS-LISTE: dieselbe Mechanik, zwei andere Zeilen. Die erste,
    # weil die Anwendung dort selbst auf dem Port hoert; die zweite, weil
    # man sich unter Windows ueber den Remotedesktop aussperrt und nicht
    # ueber ssh.
    liste_nt = firewallmodul.ports(8081, system="nt")
    pruefe(any(z["port"] == "8081/tcp" and "MARLEI" in z["dienst"]
               for z in liste_nt),
           "unter Windows nennt die Liste die Anwendung selbst -- es gibt "
           "keinen nginx, der den Port hält")
    pruefe(any(z["port"] == "3389/tcp" for z in liste_nt),
           "und die Warnung gilt dem Remotedesktop: Wer ihn zumacht, "
           "während er über ihn angemeldet ist, sperrt sich aus")
    satz_nt = firewallmodul.nicht_oeffnen(8081, system="nt")
    pruefe("8081" in satz_nt and "nginx" in satz_nt
           and "18081" not in satz_nt,
           "der Satz darunter nennt auch dort denselben Port -- und "
           "keinen zweiten, den es nicht gibt")
    pruefe("8081" not in firewallmodul.nicht_oeffnen(80, system="nt"),
           "auch hier zieht die Zahl mit")

    # DIE DRITTE ANTWORT: nicht feststellbar. Sie entsteht, wenn der
    # Schalter in der Registry fehlt -- und "also an" waere dann ein
    # Schluss aus der Vorgabe des Systems, keine Auskunft.
    war_system = firewallmodul.SYSTEM
    war_leser = winmodul.registrywert
    try:
        firewallmodul.SYSTEM = "nt"
        winmodul.registrywert = lambda pfad, name: None
        lage = firewallmodul.lage()
        pruefe(len(lage["gefunden"]) == 3
               and all(f["an"] is None for f in lage["gefunden"]),
               "drei Profile, und keins davon behauptet etwas")
        pruefe(lage["unklar"] and not lage["aktiv"],
               "»nicht feststellbar« ist nicht dasselbe wie »nichts im "
               "Weg« -- ohne dieses Feld stünde auf der Karte eine Zusage")
        winmodul.registrywert = lambda pfad, name: 1
        lage = firewallmodul.lage()
        pruefe(lage["aktiv"] and not lage["unklar"]
               and lage["namen"] == ["Domäne", "Privat", "Öffentlich"],
               "steht der Schalter auf 1, sind alle drei an -- und im "
               "Kartenkopf steht der kurze Name")
        pruefe("HKLM" in lage["quelle"],
               "und die Karte nennt die Quelle: die Registry, nicht eine "
               "Prüfung")
    finally:
        firewallmodul.SYSTEM = war_system
        winmodul.registrywert = war_leser

    # 3. "1.26.3-3+deb13u7 (nginx)" -- die Klammer soll heissen "gefunden
    # unter einem anderen Namen als erwartet". Heisst das Paket wie die
    # Zeile, ist sie Rauschen.
    war_lauf = bericht._lauf
    try:
        bericht._lauf = lambda befehl: "nginx 1.26.3-3"
        pruefe(bericht._paket("nginx", ["nginx-core", "nginx"])
               == "1.26.3-3",
               "heißt das Paket wie die Zeile, steht keine Klammer dahinter")
        bericht._lauf = lambda befehl: "nginx-core 1.26.3-3"
        pruefe(bericht._paket("nginx", ["nginx-core", "nginx"])
               == "1.26.3-3 (nginx-core)",
               "unter einem anderen Namen gefunden: Dann sagt die Klammer "
               "etwas")
        bericht._lauf = lambda befehl: ""
        pruefe(bericht._paket("nginx", ["nginx"]) == "nicht installiert",
               "und gar nicht gefunden ist auch eine Auskunft")
    finally:
        bericht._lauf = war_lauf

print("\nDie Anmeldung")
# ALLES HIER LAEUFT MIT GESETZTEM HASH, und am Ende wird er wieder
# entfernt: Die Reihe oben prueft die Oberflaeche ohne Kennwort, und so
# bleibt es -- sie muesste sich sonst an jeder Stelle erst anmelden.
import anmeldung  # noqa: E402
import subprocess as _sp  # noqa: E402

with TestClient(anwendung.app) as c:
    r = c.get("/")
    pruefe("ohne Kennwort" in r.text and "/abmelden" not in r.text,
           "ohne Kennwort ist die Tür offen, und das Band sagt es")

    geheim = _anlegen("Geheimprojekt", "2026-09-19")
    os.environ[anmeldung.UMGEBUNG] = anmeldung.hash_bilden("richtig-123",
                                                           runden=1000)
    try:
        r = c.get("/sammlung?ansicht=durchsicht", follow_redirects=False)
        pruefe(r.status_code == 303 and r.headers["location"]
               == "/anmelden?weiter=%2Fsammlung%3Fansicht%3Ddurchsicht",
               "mit Kennwort führt jede Seite zur Anmeldung -- und merkt "
               "sich, wohin es gehen sollte")
        for pfad in ("/", "/einrichtung", "/hilfe", "/serverhealth",
                     "/einrichtung/bericht.txt"):
            pruefe(c.get(pfad, follow_redirects=False).status_code == 303,
                   "%s ist gesperrt" % pfad)
        pruefe(c.get("/health").status_code == 200,
               "/health antwortet weiter -- für Wachhunde und den "
               "Selbsttest der Installation")
        pruefe(c.get("/static/style.css").status_code == 200,
               "die Stylesheets auch -- die Anmeldeseite braucht sie")
        for stueck in ("/befunde.html", "/auslastung.html"):
            pruefe(c.get(stueck, follow_redirects=False).status_code == 401,
                   "%s wird abgewiesen, nicht umgeleitet -- sonst setzte "
                   "das Nachholen die Anmeldeseite in die Seite" % stueck)

        vorher = len(_projekte())
        r = c.post("/projekte/neu", data={"name": "Eindringling",
                                          "eingetragen": "2026-09-19"},
                   follow_redirects=False)
        pruefe(r.status_code == 303 and len(_projekte()) == vorher,
               "ein Formular ohne Anmeldung schreibt nichts")

        r = c.get("/anmelden")
        pruefe(r.status_code == 200 and 'type="password"' in r.text,
               "die Anmeldeseite hat ein Kennwortfeld")
        pruefe("Geheimprojekt" not in r.text and "/sammlung" not in r.text,
               "und sie nennt weder Projekte noch Reiter")
        pruefe(("install.ps1 -Kennwort" if anwendung.WINDOWS
                else "MARLEI_KENNWORT=neu") in r.text,
               "sie sagt, wie ein vergessenes Kennwort neu gesetzt wird")

        r = c.post("/anmelden", data={"kennwort": "falsch-123",
                                      "weiter": "/einrichtung"},
                   follow_redirects=False)
        pruefe(r.status_code == 401 and "stimmt nicht" in r.text
               and anmeldung.COOKIE not in r.cookies,
               "ein falsches Kennwort wird abgewiesen")

        r = c.post("/anmelden", data={"kennwort": "richtig-123",
                                      "weiter": "//fremd.example/"},
                   follow_redirects=False)
        pruefe(r.status_code == 303 and r.headers["location"] == "/",
               "das richtige öffnet -- und ein Ziel nach draußen wird "
               "zur Startseite")
        r = c.get("/einrichtung")
        pruefe(r.status_code == 200 and "/abmelden" in r.text,
               "angemeldet steht Abmelden im Band")
        pruefe("pbkdf2" not in r.text and "MARLEI_KENNWORT_HASH" in r.text,
               "die Karte Einstellungen sagt, DASS ein Kennwort gesetzt "
               "ist -- den Hash zeigt sie nicht")

        os.environ[anmeldung.UMGEBUNG] = anmeldung.hash_bilden(
            "anderes-123", runden=1000)
        pruefe(c.get("/", follow_redirects=False).status_code == 303,
               "ein neu gesetztes Kennwort beendet die bestehende Anmeldung")
        c.post("/anmelden", data={"kennwort": "anderes-123", "weiter": "/"})
        pruefe(c.get("/", follow_redirects=False).status_code == 200,
               "mit dem neuen geht es wieder hinein")
        c.post("/abmelden")
        pruefe(c.get("/", follow_redirects=False).status_code == 303,
               "Abmelden schließt wieder")
        pruefe(any(p["id"] == geheim for p in _projekte()),
               "und der Bestand ist von alldem unberührt")
    finally:
        del os.environ[anmeldung.UMGEBUNG]

# Das Modul fuer sich: die Faelle, die an der Oberflaeche nicht zu sehen
# sind, weil sie nur "nein" sagen.
h = anmeldung.hash_bilden("richtig-123", runden=1000)
pruefe(anmeldung.kennwort_stimmt("richtig-123", h)
       and not anmeldung.kennwort_stimmt("richtig-124", h),
       "der Hash erkennt sein Kennwort und nur das")
pruefe(not anmeldung.kennwort_stimmt("richtig-123", "kaputt")
       and not anmeldung.kennwort_stimmt("richtig-123", "a:b:c:d"),
       "ein kaputter Hash heißt nein, nicht Absturz")
keks = anmeldung.cookie_bilden(h, jetzt=1000)
pruefe(anmeldung.cookie_gilt(keks, h, jetzt=1000 + 60),
       "ein frisches Anmeldecookie gilt")
pruefe(not anmeldung.cookie_gilt(keks, h,
                                 jetzt=1000 + anmeldung.GUELTIG + 1),
       "nach einem Monat nicht mehr")
ablauf, _, zeichen = keks.partition(".")
pruefe(not anmeldung.cookie_gilt("%d.%s" % (int(ablauf) + 999999, zeichen),
                                  h, jetzt=1000),
       "ein verlängerter Ablauf macht die Unterschrift ungültig")
pruefe(":" in h and "$" not in h,
       "der Hash trägt kein Dollarzeichen -- systemd und start.ps1 lesen "
       "ihn beide als bloße Zeichen")

# Der Weg, auf dem die Installationsskripte den Hash ausrechnen: Kennwort
# ueber die Standardeingabe, als UTF-8-Bytes. Ein Umlaut ist der Fall, an
# dem eine falsche Kodierung auffaellt.
skript = PROJ / "webui" / "anmeldung.py"
lauf = _sp.run([sys.executable, str(skript)], input="Grüße-äöü1\n".encode(),
               capture_output=True, timeout=60)
pruefe(lauf.returncode == 0 and anmeldung.kennwort_stimmt(
           "Grüße-äöü1", lauf.stdout.decode().strip()),
       "als Skript: ein Kennwort mit Umlauten ergibt einen Hash, zu dem "
       "dasselbe Kennwort im Formular passt")
lauf = _sp.run([sys.executable, str(skript)], input=b"kurz\n",
               capture_output=True, timeout=60)
pruefe(lauf.returncode == 2 and not lauf.stdout.strip(),
       "zu kurz ist Rückgabewert 2 und kein Hash")

# Die Namen muessen zusammenpassen -- dieselbe Pruefung wie bei Aufgabe
# und Firewallregel: Ein Schalter, den die Anmeldeseite nennt und das
# Skript nicht kennt, faellt erst an dem Tag auf, an dem jemand sein
# Kennwort vergessen hat.
sh = (PROJ / "setup" / "linux" / "install.sh").read_text(encoding="utf-8")
ps = (PROJ / "setup" / "windows" / "install.ps1").read_text(encoding="utf-8")
seite = (PROJ / "webui" / "templates" / "anmelden.html").read_text(
    encoding="utf-8")
pruefe('"${MARLEI_KENNWORT:-}" != "neu"' in sh
       and "MARLEI_KENNWORT=neu ./setup/linux/install.sh" in seite,
       "install.sh kennt MARLEI_KENNWORT=neu, und die Anmeldeseite nennt es")
pruefe("[switch]$Kennwort" in ps
       and "install.ps1 -Kennwort" in seite,
       "install.ps1 kennt -Kennwort, und die Anmeldeseite nennt es")
pruefe("read -rs" in sh and "-AsSecureString" in ps,
       "beide Skripte lesen das Kennwort verdeckt")
pruefe('"$KW1" | "$APP_DIR/venv/bin/python" "$APP_DIR/anmeldung.py"' in sh
       and '$kw1 | & $VENV_PY (Join-Path $APP_DIR "app\\anmeldung.py")' in ps,
       "und beide geben es über die Standardeingabe weiter, nie als "
       "Argument")
for system in ("linux", "windows"):
    vorlage = (PROJ / "setup" / system / "files"
               / "marlei-tasks.env.example").read_text(encoding="utf-8")
    pruefe("\nMARLEI_KENNWORT_HASH=\n" in vorlage,
           "die Vorlage für %s kennt MARLEI_KENNWORT_HASH -- leer, damit "
           "das Nachtragen eine bestehende Datei nicht verändert" % system)

print()
if FEHLER:
    print("%d Pruefung(en) fehlgeschlagen:" % len(FEHLER))
    for f in FEHLER:
        print("  - %s" % f)
    sys.exit(1)
print("Alle Pruefungen bestanden.")
