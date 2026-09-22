"""
MARLEI Tasks -- die Weboberflaeche.

**Stand: sieben Reiter sind gebaut, zwei sind leer.**
Neun Reiter, neun Adressen, ein gemeinsamer Rahmen. Was auf den Seiten
passiert, kommt Reiter fuer Reiter dazu.

**Was hier schon entschieden ist und nicht wieder aufgemacht wird:**

- **Die Reihenfolge der Reiter folgt Boots Prinzip, nicht Boots
  Positionen** -- sortiert nach der Haeufigkeit im Betrieb. Dort ist der
  Server der Gegenstand und steht vorn; hier ist er Unterbau und steht
  hinten. Folge: ``/`` ist Projekte.
- **Das gewaehlte Projekt ist ein Zustand, kein Seiteninhalt.** Es steht
  im Kopfband und gilt fuer Sammlung, Aufgaben, Meilensteine und
  Entscheidungen. Gehalten wird es in einem Cookie -- siehe
  ``gewaehltes_projekt``.
- **Befunde gelten ueber alle Projekte** und sind damit das einzige, was
  die Vorauswahl nicht filtert.

Warum so: `docs/aufbau.md`, Abschnitte 1 und 2.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import (HTMLResponse, PlainTextResponse,
                               RedirectResponse)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import anmeldung
import auslastung
import befunde
import bericht
import datenbank
import einstellungen
import export
import firewall
import updatewacht
import versionsstand

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

app = FastAPI(title="MARLEI Tasks")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
html = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Unter welcher Adresse die Oberflaeche erreichbar ist -- steht im Band.
BASE_URL = os.environ.get("MARLEI_BASE_URL", "")

# Steht hier ein Wort, ist dieser Server nicht die Produktion: Es erscheint
# im Band, und der Seitengrund wechselt auf Sand. Die Farbe allein waere
# ein Code, den man kennen muss.
KENNZEICHNUNG = os.environ.get("MARLEI_KENNZEICHNUNG", "")

# Laeuft das hier auf einem Windows?
#
# **Drei Karten reden ueber die Maschine, und dort ist der Satz je System
# ein anderer** -- der Weg zum anderen Port, der Dienst, der neu zu starten
# ist, und was eine Firewall ist, die zum System gehoert. Die Weiche steht
# deshalb im Rahmen jeder Seite und nicht in drei Routen: Ein Reiter, der
# sie vergisst, faellt sonst genau dort auf, wo jemand einen Befehl
# abschreibt.
#
# **Und es ist kein Schalter, sondern eine Feststellung.** Er laesst sich
# nicht setzen; die Anwendung verhaelt sich nicht anders, sie sagt es nur
# anders.
WINDOWS = os.name == "nt"

# Das Cookie, in dem die Vorauswahl steht. Kein Serverzustand: Zwei
# Browserfenster duerfen verschiedene Projekte offen haben, und ein
# Neustart des Dienstes darf die Auswahl nicht vergessen.
COOKIE_PROJEKT = "marlei_projekt"


# Die neun Reiter, in der Reihenfolge der Leiste. Sie stehen hier UND in
# base.html -- das ist eine Doppelung und bleibt eine, solange die Liste
# neun Zeilen hat. Ein Reiter ist ein Stueck Gestaltung, kein Datensatz;
# ihn aus einer Schleife zu bauen, machte die Vorlage schwerer lesbar und
# spaeter kaum wartbarer.
REITER = ("projekte", "sammlung", "aufgaben", "meilensteine",
          "entscheidungen", "einrichtung", "history", "hilfe",
          "serverhealth")

# Die drei Zustaende eines Projekts, in Grossbuchstaben wie alle
# aufgezaehlten Werte der Mappe. Dieselbe Liste steht als CHECK in der
# Ablage; hier steht sie, damit ein erfundener Wert schon an der
# Oberflaeche auffaellt und nicht erst als IntegrityError.
#
# Der Unterschied zwischen den letzten beiden ist keine Feinheit:
# ABGESCHLOSSEN stellt die Liegeprobe still -- ein fertiges Projekt liegt
# nicht, es ist fertig --, RUHT tut das nicht. Ein ruhendes Projekt ist
# genau der Fall, fuer den die Probe gebaut ist.
ZUSTAENDE = ("AKTIV", "RUHT", "ABGESCHLOSSEN")


def datei_version(name: str) -> int:
    """Aenderungszeit einer Datei unter static/, als ganze Sekunden.

    Haengt als ``?v=`` an der Adresse: Aendert sich die Datei, aendert
    sich die Adresse, und der Browser holt sie zwangslaeufig neu. Fehlt
    sie, ist die Zahl 0 -- lieber ein unnoetiger Abruf als eine Ausnahme
    beim Aufbau jeder Seite.
    """
    try:
        return int((STATIC_DIR / name).stat().st_mtime)
    except OSError:
        return 0


def stil_version() -> int:
    """Aenderungszeit des juengeren der beiden Stylesheets.

    Es sind zwei: die gemeinsame ``style.css`` und die produkteigene
    ``produkt.css``. Eine gemeinsame Zahl reicht -- sie haengen an
    derselben Seite und aendern sich beim Bauen ohnehin zusammen.
    """
    return max(datei_version("style.css"), datei_version("produkt.css"))


def marken_version() -> int:
    """Aenderungszeit der juengsten Logodatei.

    Die beiden Wortmarken, das Zeichen und das Favicon entstehen aus
    derselben Quelle und aendern sich zusammen. Eine gemeinsame Zahl
    reicht deshalb -- und erspart vier fast gleiche Werte in jeder Seite.
    """
    return max(datei_version(n) for n in
               ("exmig-logo.svg", "exmig-logo-band.svg", "exmig-zeichen.svg",
                "favicon.ico"))


def stand_kurz() -> str:
    """Welcher Stand hier laeuft -- aus der Datei, die install.sh legt.

    Fehlt sie, steht in der Fusszeile nichts. **Lieber keine Angabe als
    eine erfundene:** Eine Versionsnummer, die niemand nachvollziehen
    kann, ist schlimmer als gar keine.

    Seit dem 22.09.2026 liest das webui/versionsstand.py: Die Datei traegt
    jetzt vier Felder statt einer Zeile, weil die Versionssuche den
    Commit braucht. Diese Funktion bleibt als der eine Satz stehen, den
    Fusszeile und Fehlerbericht wollen.
    """
    return versionsstand.kurz()


def gewaehltes_projekt(request: Request, conn) -> dict | None:
    """Welches Projekt gerade gilt.

    **Die Auswahl steht im Cookie, nicht im Server.** Sonst saehen zwei
    Browserfenster dasselbe Projekt, obwohl jemand in einem davon
    gewechselt hat -- und ein Neustart des Dienstes vergaesse sie ganz.

    **Ein Cookie, das auf ein geloeschtes Projekt zeigt, gilt als
    keines.** Ein Projekt kann verschwinden, waehrend der Browser die
    Nummer noch mit sich traegt; ohne diese Zeile stuende der Name eines
    Projekts im Band, das es nicht mehr gibt.
    """
    roh = request.cookies.get(COOKIE_PROJEKT)
    if not roh or not roh.isdigit():
        return None
    zeile = conn.execute(
        "SELECT id, name, zustand FROM projekte WHERE id = ?", (int(roh),)
    ).fetchone()
    if not zeile:
        return None
    gewaehlt = dict(zeile)
    gewaehlt["kennung"] = datenbank.kennung("P", gewaehlt["id"])
    return gewaehlt


def rahmen(request: Request, aktiv: str, **dazu) -> dict:
    """Was jede Seite braucht -- an einer Stelle statt neunmal.

    **Die Befunde laufen ueber ALLE Projekte** und nicht ueber das
    gewaehlte -- die einzige Stelle, an der die Vorauswahl nicht gilt.
    Sie entstehen deshalb hier und nicht in einer Route: Ein Befund, der
    nur auf dem Reiter erschiene, zu dem er gehoert, zeigte gerade das
    nie an, wonach niemand sucht.
    """
    if aktiv not in REITER:
        raise ValueError("kein Reiter dieser Leiste: %r" % aktiv)
    with datenbank.verbindung() as conn:
        projekt = gewaehltes_projekt(request, conn)
        offen, bekannt = befunde.teilen(conn, befunde.sammeln(conn))
        conn.commit()
    zusammen = {
        "request": request,
        "aktiv": aktiv,
        "projekt": projekt,
        # Dasselbe Projekt noch einmal, unter einem Namen, den keine Route
        # ueberschreibt: Einige legen unter "projekt" die volle Fassung
        # samt Bereichen ab. Die Zeile in der Reiterleiste und der Satz am
        # Anlegen-Knopf lesen von hier und finden immer dasselbe.
        "gewaehlt": projekt,
        "base_url": BASE_URL,
        "kennzeichnung": KENNZEICHNUNG,
        "windows": WINDOWS,
        "stil_version": stil_version(),
        "marken_version": marken_version(),
        "stand_kurz": stand_kurz(),
        "meldung": request.query_params.get("meldung", ""),
        "meldungsart": request.query_params.get("art", ""),
        "befunde": offen,
        "bekannte": bekannt,
        # Ob ein Kennwort gesetzt ist: dann steht im Band "Abmelden",
        # sonst "ohne Kennwort".
        "anmeldung": bool(anmeldung.gesetzt()),
    }
    zusammen.update(dazu)
    return zusammen


@app.on_event("startup")
def ablage_anlegen() -> None:
    """Beim Start: Schema anlegen und spaetere Spalten nachziehen.

    Meldet, wenn die Volltextsuche fehlt -- die Anwendung laeuft dann
    weiter, nur die Buendelprobe muss sich anders behelfen.
    """
    with datenbank.verbindung() as conn:
        if not datenbank.anlegen(conn):
            print("MARLEI Tasks: SQLite ohne FTS5 -- die Suche ueber die "
                  "Sammlung steht nicht zur Verfuegung.")
    # Die Wache laeuft immer mit und fragt stuendlich, ob sie darf. Sie
    # haengt weder am Intervall noch am Offline-Modus -- beides ist zur
    # Laufzeit umlegbar, und ein Schalter, der erst nach einem Neustart
    # wirkt, ist keiner. Siehe updatewacht.wacht_starten().
    updatewacht.wacht_starten()


# ==================================================================== #
# Die Anmeldung
# ==================================================================== #
#
# **Die Sperre steht vor jeder Route und nicht in ihnen.** Eine Route,
# die die Pruefung vergisst, waere eine offene Tuer, und niemand saehe
# sie -- neun Reiter und dreissig Formulare sind dreissig Gelegenheiten.
# So muss eine Route ausdruecklich AUSGENOMMEN werden, und die Ausnahmen
# stehen an einer Stelle.
#
# **Sie steht in der Anwendung und nicht im nginx davor**, obwohl der
# auf Linux ohnehin da ist: Unter Windows gibt es keinen, und eine
# Anmeldung, die auf beiden Systemen anders gebaut ist, wird auf einem
# davon vergessen.
#
# **Ohne gesetztes Kennwort ist die Tuer offen, und das Band sagt es.**
# So kommt eine bestehende Installation durch ein Update nicht in eine
# Lage, in der niemand mehr hineinkommt; install.sh und install.ps1
# fragen beim naechsten Lauf nach dem Kennwort.

# Was ohne Anmeldung erreichbar bleibt.
#
#   /health     maschinenlesbar, Zahlen statt Namen -- und wer den Dienst
#               ueberwacht, erreichte ihn sonst nicht mehr. Auch der
#               Selbsttest am Ende von install.sh und install.ps1 fragt
#               ihn.
#   /static/    Stylesheets und Marke: Die Anmeldeseite braucht sie selbst.
#   /anmelden   sonst kaeme niemand hinein.
#   /abmelden   wer abgelaufen ist und abmeldet, soll keinen Umweg gehen.
OHNE_ANMELDUNG = ("/health", "/anmelden", "/abmelden")


def angemeldet(request: Request) -> bool:
    """Darf diese Anfrage durch? -- ohne Kennwort immer."""
    gespeichert = anmeldung.gesetzt()
    if not gespeichert:
        return True
    return anmeldung.cookie_gilt(request.cookies.get(anmeldung.COOKIE, ""),
                                 gespeichert)


def _eigener_weg(weg: str) -> str:
    """Nur Wege auf diesem Server -- dieselbe Regel wie beim Zurueck des
    Kenntnis-Knopfes. Ein Ziel, das nach draussen zeigt, waere eine offene
    Weiterleitung, und hier gleich nach einer Anmeldung."""
    if not weg.startswith("/") or weg.startswith("//"):
        return "/"
    return weg


@app.middleware("http")
async def sperre(request: Request, call_next):
    """Wer nicht angemeldet ist, landet auf der Anmeldeseite.

    **Zwei Stuecke werden nicht umgeleitet, sondern abgewiesen**, und das
    ist keine Feinheit: /befunde.html und /auslastung.html holt jede
    Seite im Takt nach. Eine Umleitung beantwortete der Browser mit der
    Anmeldeseite, und das Skript setzte die ganze Seite in den
    Befund-Kasten. Eine 401 laesst es stehen, wie es ist.
    """
    weg = request.url.path
    if (weg in OHNE_ANMELDUNG or weg.startswith("/static/")
            or angemeldet(request)):
        return await call_next(request)
    if weg.endswith(".html"):
        return PlainTextResponse("Nicht angemeldet.", status_code=401)
    # Nach der Anmeldung dorthin zurueck, wohin jemand wollte -- aber nur
    # bei einem GET. Ein Formular, das abgelaufen abgeschickt wurde, ist
    # verloren; es nach der Anmeldung als GET zu wiederholen, ginge ins
    # Leere.
    weiter = "/"
    if request.method == "GET":
        weiter = weg + ("?" + request.url.query if request.url.query else "")
    return RedirectResponse("/anmelden?weiter=" + quote(weiter, safe=""),
                            status_code=303)


def _anmeldeseite(request: Request, weiter: str, fehler: str = "",
                  status: int = 200) -> HTMLResponse:
    """Die Anmeldeseite -- ohne Rahmen.

    **Sie bekommt nicht, was jede andere Seite bekommt**: kein gewaehltes
    Projekt, keine Befunde, keine Reiter. Beide nennen Projektnamen, und
    wer nicht angemeldet ist, soll nicht erfahren, woran hier gearbeitet
    wird.
    """
    return html.TemplateResponse(request, "anmelden.html", {
        "request": request,
        "base_url": BASE_URL,
        "kennzeichnung": KENNZEICHNUNG,
        "windows": WINDOWS,
        "stil_version": stil_version(),
        "marken_version": marken_version(),
        "weiter": weiter,
        "fehler": fehler,
    }, status_code=status)


@app.get("/anmelden", response_class=HTMLResponse)
def anmelden_seite(request: Request, weiter: str = "/") -> Response:
    """Das Formular. Ohne Kennwort, oder schon angemeldet: gleich weiter."""
    weiter = _eigener_weg(weiter)
    if not anmeldung.gesetzt() or angemeldet(request):
        return RedirectResponse(weiter, status_code=303)
    return _anmeldeseite(request, weiter)


@app.post("/anmelden")
async def anmelden(request: Request) -> Response:
    """Das Kennwort pruefen und das Cookie setzen.

    **Ein falsches Kennwort kostet eine Sekunde**, zusaetzlich zu dem, was
    PBKDF2 ohnehin kostet. Wer das Kennwort kennt, merkt davon nichts;
    wer raet, raet langsam. Gerechnet wird ausserhalb der Ereignisschleife
    -- sonst stuende waehrend jeder Pruefung die ganze Oberflaeche.
    """
    formular = await request.form()
    weiter = _eigener_weg(str(formular.get("weiter", "/")))
    gespeichert = anmeldung.gesetzt()
    if not gespeichert:
        return RedirectResponse(weiter, status_code=303)

    kennwort = str(formular.get("kennwort", ""))
    stimmt = await run_in_threadpool(anmeldung.kennwort_stimmt, kennwort,
                                     gespeichert)
    if not stimmt:
        await asyncio.sleep(1)
        return _anmeldeseite(request, weiter, "Das Kennwort stimmt nicht.",
                             status=401)

    antwort = RedirectResponse(weiter, status_code=303)
    # httponly: Kein Skript braucht es, also kommt keines heran.
    # samesite=lax: Ein Formular auf einer fremden Seite, das hierher
    # abschickt, kommt ohne das Cookie an und damit nicht durch.
    # Ohne secure, weil diese Oberflaeche http spricht -- mit secure kaeme
    # das Cookie nie zurueck.
    antwort.set_cookie(anmeldung.COOKIE, anmeldung.cookie_bilden(gespeichert),
                       max_age=anmeldung.GUELTIG, httponly=True,
                       samesite="lax")
    return antwort


@app.post("/abmelden")
def abmelden() -> RedirectResponse:
    """Das Cookie weg. Ein POST und kein Verweis: Ein Verweis liesse sich
    von jeder fremden Seite aus ausloesen, und ein Browser, der Verweise
    vorab laedt, meldete ab, ohne dass jemand geklickt hat."""
    antwort = RedirectResponse("/anmelden", status_code=303)
    antwort.delete_cookie(anmeldung.COOKIE)
    return antwort


# HIER STAND DER PLATZHALTER fuer die noch leeren Reiter -- eine Seite,
# die ausdruecklich sagt, dass hier noch nichts ist, weil eine leere
# Seite ohne Wort wie ein Fehler aussieht. **Seit dem 07.09.2026 sind
# alle neun Reiter gebaut**; er hat keinen Benutzer mehr und ist samt
# leer.html weggefallen. Wer einen zehnten Reiter anfaengt, holt sich
# beides aus der Geschichte zurueck.


def _auslastung() -> dict:
    """Was die Karte *Auslastung* zeigt -- in einem Griff.

    An zwei Stellen gebraucht: beim Aufbau der Seite und alle fuenf
    Sekunden beim Nachholen. Deshalb hier und nicht in der Route.

    ``dienst.seit`` wird HIER ausgerechnet und nicht in der Vorlage: Die
    Form haengt von der Zahl ab (*seit 1 Tag*, aber *seit 2 Tagen*), und
    eine Vorlage ist der falsche Ort fuer eine Fallunterscheidung ueber
    Grammatik.
    """
    eigen = dict(auslastung.dienst())
    if eigen:
        eigen["seit"] = auslastung.dauer_dativ(eigen.get("betrieb"))
    # Ohne /proc bleibt es leer, und die Zeile faellt GANZ weg statt als
    # Satzstumpf dazustehen: "Dieser Dienst laeuft ." -- aufgefallen beim
    # ersten Aufruf unter Windows.
    return {
        "cpu": auslastung.cpu(),
        "kerne": auslastung.kerne(),
        "last": auslastung.last(),
        "speicher": auslastung.speicher(),
        "netz": auslastung.netz(),
        "dienst": eigen,
    }


@app.get("/serverhealth", response_class=HTMLResponse)
def serverhealth_seite(request: Request) -> HTMLResponse:
    """Die Maschine, auf der das hier laeuft -- zwei Karten.

    **Der einzige Reiter, der ohne gewaehltes Projekt vollstaendig
    dasteht.** Er beschreibt nicht den Bestand, sondern den Unterbau; die
    Vorauswahl gilt hier so wenig wie fuer die Befunde.
    """
    return html.TemplateResponse(request, "serverhealth.html", rahmen(
        request, "serverhealth",
        auslastung=_auslastung(),
        serverdetails=bericht.karte(stand_kurz()),
    ))


@app.get("/auslastung.html", response_class=HTMLResponse)
def auslastung_stueck(request: Request) -> HTMLResponse:
    """Nur die Kacheln, fertig gerendert.

    **Fertig gerendert und nicht als Daten**, damit es die Darstellung
    genau einmal gibt -- dieselbe Ueberlegung wie bei ``_befunde.html``.
    """
    # "windows" auch hier, obwohl dieses Stueck keinen Rahmen bekommt: Die
    # Vorlage sagt je System einen anderen Satz, wenn keine Quelle
    # antwortet -- und sie wird alle fuenf Sekunden GENAU SO geholt, ohne
    # den Rahmen, in dem die Weiche sonst steht. Ohne diese Zeile stuende
    # im nachgeholten Stueck etwas anderes als im ersten Aufbau.
    return html.TemplateResponse(
        request, "_auslastung.html",
        {"request": request, "auslastung": _auslastung(),
         "windows": WINDOWS})


@app.get("/hilfe", response_class=HTMLResponse)
def hilfe_seite(request: Request) -> HTMLResponse:
    """Die Hilfe -- ein Kapitel je Reiter, ein Abschnitt je Karte.

    **Sie bekommt nichts ausser dem Rahmen.** Was sie zeigt, steht in der
    Vorlage; sie liest weder die Ablage noch die Umgebung. Damit gilt sie
    auch dann, wenn kein Projekt gewaehlt ist -- und genau dann sucht
    jemand sie am ehesten.

    Die Anker sind der Vertrag zwischen dieser Seite und den Karten:
    Jedes Fragezeichen in einem Kartenkopf zeigt auf ``/hilfe#reiter-karte``.
    Eine Pruefung geht beide Richtungen durch.
    """
    return html.TemplateResponse(request, "hilfe.html",
                                 rahmen(request, "hilfe"))

# Die fuenf Register sind gebaut und bekommen ihre Routen weiter unten.
# Projekte steht dabei unter "/": Ohne gewaehltes Projekt haben die vier
# folgenden Reiter nichts zu zeigen.


@app.get("/health")
def health():
    """Laeuft es? -- fuer den Selbsttest in install.sh und fuer Wachhunde.

    **Zahlen, keine Namen.** Dieselbe Regel wie beim Fehlerbericht, und
    sie ist hier noch wichtiger: Diese Auskunft ist maschinenlesbar und
    fragt niemanden, wer er ist. In einer Aufgabenverwaltung steht, woran
    eine Firma arbeitet -- ein Projektname gehoert deshalb nicht hierher.

    Die offenen Befunde stehen mit drin: Das ist die eine Zahl, die einen
    Wachhund ueberhaupt interessieren koennte -- liegt etwas, das jemand
    ansehen sollte.
    """
    with datenbank.verbindung() as conn:
        projekte = datenbank.projekte(conn)
        offen, bekannt = befunde.teilen(conn, befunde.sammeln(conn))
        conn.commit()
    return {
        "status": "ok",
        "stand": stand_kurz() or "unbekannt",
        "projekte": len(projekte),
        "befunde_offen": len(offen),
        "befunde_bekannt": len(bekannt),
    }


@app.post("/befund/kenntnis")
async def befund_kenntnis(request: Request) -> RedirectResponse:
    """Einen Befund in EINEM Projekt zur Kenntnis nehmen.

    **Je Projekt, nicht je Befund** -- das ist die eine Stelle, an der
    diese Mechanik von Boots abweicht, und sie steht deshalb im
    Formular: Ohne die Projektnummer naehme das Stillstellen in einem
    Projekt dieselbe Lage in einem anderen mit, und ein Befund
    verschwaende, den nie jemand gesehen hat.

    Die Marke kommt aus dem Formular und nicht aus einer neuen Messung:
    Zur Kenntnis genommen wird der Stand, DER DASTAND. Waere sie
    inzwischen gestiegen, bekaeme jemand ein Wegklicken fuer etwas, das
    er nicht gesehen hat.
    """
    formular = await request.form()
    kennung = str(formular.get("kennung", "")).strip()
    projekt = str(formular.get("projekt", "")).strip()
    marke = str(formular.get("marke", "0")).strip()
    zurueck = str(formular.get("zurueck", "/")).strip()

    # Nur eigene Wege. Ein "zurueck", das nach draussen zeigt, waere eine
    # offene Weiterleitung -- billig zu verhindern, teuer zu uebersehen.
    if not zurueck.startswith("/") or zurueck.startswith("//"):
        zurueck = "/"
    if kennung not in befunde.KENNUNGEN or not projekt.isdigit():
        return _meldung(zurueck, "Diesen Befund gibt es nicht.", "schlecht")

    with datenbank.verbindung() as conn:
        datenbank.kenntnis_nehmen(conn, int(projekt), kennung,
                                  int(marke) if marke.lstrip("-").isdigit()
                                  else 0)
        conn.commit()
    # OHNE MELDUNG ZURUECK: Der Klick beantwortet sich selbst -- die
    # Karte ist weg und steht als graue Zeile da. Ein Satz darueber waere
    # eine zweite Auskunft ueber dieselbe Handlung.
    return RedirectResponse(zurueck, status_code=303)


@app.get("/befunde.html", response_class=HTMLResponse)
def befunde_stueck(request: Request, von: str = "") -> HTMLResponse:
    """Nur die Befunde, fertig gerendert.

    Jede Seite holt dieses Stueck alle zehn Sekunden nach, damit eine
    behobene Ursache ihre Karte ohne Neuladen mitnimmt. **Fertig
    gerendert und nicht als Daten**, damit es die Darstellung genau
    einmal gibt.

    ``von`` sagt, auf welcher Seite der Aufrufer steht -- der Knopf "zur
    Kenntnis genommen" muss dorthin zurueckfuehren und nicht hierher.
    """
    with datenbank.verbindung() as conn:
        offen, bekannt = befunde.teilen(conn, befunde.sammeln(conn))
        conn.commit()
    return html.TemplateResponse(
        request, "_befunde.html",
        {"request": request, "befunde": offen, "bekannte": bekannt,
         "hier": von or "/"})


# ==================================================================== #
# Der Reiter Projekte
# ==================================================================== #
#
# **Gewaehlt wird in der Uebersicht, geaendert in den Eintragskarten.**
# Zwei Karten, zwei Aufgaben -- und nur EIN Waehlen-Knopf je Projekt: Zwei
# Wege zu demselben Schritt lehren, dass es zwei Schritte sind.
#
# **Gespeichert wird die ganze Seite auf einmal**, wie unter Systeme in
# Boot. Drei Karten mit je einem Knopf taeuschten drei Vorgaenge vor, und
# es ist einer: Was anders dasteht als beim Aufbau der Seite, wird
# geschrieben.

def _meldung(ziel: str, text: str, art: str = "") -> RedirectResponse:
    """Zurueck zur Seite, mit einem Satz darueber.

    303 und nicht 302: Danach ist es ein GET. Ohne das wiederholt ein F5
    die POST-Anfrage -- und beim Loeschen waere das kein Schoenheitsfehler.

    Die Sprungmarke steht hinter der Frage, nicht davor; der Browser
    verlangt diese Reihenfolge. Ohne sie landet man nach jedem Klick am
    Seitenanfang und muss sich zurueckscrollen.
    """
    anker = ""
    if "#" in ziel:
        ziel, anker = ziel.split("#", 1)
        anker = "#" + anker
    # **Das Trennzeichen haengt davon ab, ob schon eine Frage dasteht.**
    # Aufgefallen am 07.09.2026 beim Bau der Sammlung: Deren Ziele tragen
    # "?ansicht=durchsicht", und ein zweites "?" machte daraus
    # "durchsicht?meldung=..." -- die Ansicht fiel auf Eintragen zurueck
    # und die Meldung erschien nie. Bei den Projekten fiel es nicht auf,
    # weil deren Ziele keine Frage tragen.
    trenner = "&" if "?" in ziel else "?"
    frage = trenner + "meldung=" + quote(text) + ("&art=" + art if art else "")
    return RedirectResponse(ziel + frage + anker, status_code=303)


@app.get("/", response_class=HTMLResponse)
def projekte_seite(request: Request, loeschen: int = 0) -> HTMLResponse:
    """Die Startseite: Uebersicht, Eintragskarten, Neues Projekt.

    ``loeschen`` traegt die Nummer des Projekts, dessen Karte gerade im
    Loeschschritt steht. Es steht in der Adresse und nicht im Server:
    Der Schritt ist eine Ansicht, kein Zustand -- ein Neuladen darf ihn
    zeigen, ein zweiter Browser muss ihn nicht sehen.
    """
    with datenbank.verbindung() as conn:
        alle = datenbank.projekte(conn)
    # **Ein Cookie auf ein geloeschtes Projekt gilt als keines** -- hier
    # genauso wie im Band. Sonst stuende die Seite auf "eines ist
    # gewaehlt", markierte aber keine Zeile, und der Hinweis, dass keines
    # gilt, bliebe aus: die schlechteste der drei moeglichen Auskuenfte.
    nummer = _gewaehlte_nummer(request)
    gewaehlt = nummer if any(p["id"] == nummer for p in alle) else 0
    return html.TemplateResponse(
        request, "projekte.html",
        rahmen(request, "projekte", projekte=alle, gewaehlt_id=gewaehlt,
               loeschen_id=loeschen, zustaende=ZUSTAENDE))


def _gewaehlte_nummer(request: Request) -> int:
    roh = request.cookies.get(COOKIE_PROJEKT, "")
    return int(roh) if roh.isdigit() else 0


def _gewaehlt_setzen(antwort: RedirectResponse, nummer: int) -> None:
    """Die Vorauswahl ins Cookie.

    ``max_age`` auf ein Jahr: Ein Sitzungscookie waere jeden Morgen weg,
    und die erste Handlung des Tages waere jedes Mal dieselbe.
    """
    antwort.set_cookie(COOKIE_PROJEKT, str(nummer),
                       max_age=365 * 24 * 3600, samesite="lax")


@app.post("/projekte/waehlen")
async def projekt_waehlen(request: Request) -> RedirectResponse:
    """Die Vorauswahl umstellen.

    **Sie steht im Cookie, nicht im Server** -- zwei Browserfenster
    duerfen verschiedene Projekte offen haben, und ein Neustart des
    Dienstes darf die Auswahl nicht vergessen.
    """
    formular = await request.form()
    ziel = str(formular.get("id", "")).strip()
    if not ziel.isdigit():
        return _meldung("/", "Kein Projekt angegeben.", "schlecht")

    with datenbank.verbindung() as conn:
        p = datenbank.projekt(conn, int(ziel))
    if not p:
        # Ein Knopf aus einer Seite, die jemand offen liegen hatte.
        return _meldung("/", "Dieses Projekt gibt es nicht mehr.", "schlecht")

    # WOHIN DANACH. Aus der Projektuebersicht zurueck auf sie selbst --
    # aus einem Befund dagegen dorthin, wo das Gemeldete steht: Der Weg
    # dorthin gehoert an die Karte, und er fuehrt nur dann irgendwohin,
    # wenn das richtige Projekt dabei gewaehlt wird.
    #
    # Nur eigene Wege, wie beim Zurueck des Kenntnis-Knopfes.
    wohin = str(formular.get("ziel", "")).strip()
    if not wohin.startswith("/") or wohin.startswith("//"):
        wohin = "/#projektuebersicht"

    antwort = _meldung(wohin,
                       "Gewaehlt: %s. Die Auswahl gilt jetzt fuer Sammlung, "
                       "Aufgaben, Meilensteine und Entscheidungen."
                       % p["name"], "gut")
    _gewaehlt_setzen(antwort, int(ziel))
    return antwort


@app.post("/projekte/speichern")
async def projekte_speichern(request: Request) -> RedirectResponse:
    """Alle geaenderten Felder aller Projekte auf einmal.

    Die Felder heissen ``feld:nummer`` -- derselbe Zuschnitt wie auf
    Boots Systeme-Seite. Was nicht in ``datenbank.AENDERBAR`` steht, wird
    verworfen: Ein Feldname aus einem Formular darf nie ungeprueft in ein
    UPDATE wandern.
    """
    formular = await request.form()
    gesammelt: dict[int, dict[str, str]] = {}
    for schluessel, wert in formular.multi_items():
        feld, trenner, nummer = str(schluessel).partition(":")
        if not trenner or feld not in datenbank.AENDERBAR \
                or not nummer.isdigit():
            continue
        gesammelt.setdefault(int(nummer), {})[feld] = str(wert)

    geaendert = 0
    with datenbank.verbindung() as conn:
        for nummer, felder in gesammelt.items():
            vorher = datenbank.projekt(conn, nummer)
            if not vorher:
                continue
            # Nur, was wirklich anders dasteht. Sonst meldet die Seite
            # "3 Projekte gespeichert", wenn niemand etwas angefasst hat.
            neu = {k: v for k, v in felder.items() if v != vorher[k]}
            if not neu:
                continue
            if "name" in neu and not neu["name"].strip():
                return _meldung(
                    "/#eintrag-%d" % nummer,
                    "Ein Projekt ohne Namen geht nicht -- der Name ist das "
                    "Losungswort beim Loeschen.", "schlecht")
            try:
                datenbank.projekt_aendern(conn, nummer, **neu)
            except sqlite3.IntegrityError:
                # Der Name ist eindeutig, weil das Losungswort ihn
                # braucht. Hier faellt das auf, nicht erst beim Loeschen.
                return _meldung(
                    "/#eintrag-%d" % nummer,
                    "Den Namen »%s« traegt schon ein anderes "
                    "Projekt." % neu.get("name", ""), "schlecht")
            geaendert += 1

    if not geaendert:
        return _meldung("/", "Nichts geaendert.")
    return _meldung("/", "%d Projekt%s gespeichert."
                    % (geaendert, "e" if geaendert > 1 else ""), "gut")


@app.post("/projekte/neu")
async def projekt_neu(request: Request) -> RedirectResponse:
    """Ein Projekt anlegen -- und es gleich waehlen.

    **Wer ein Projekt anlegt, will darin arbeiten.** Es danach noch
    einmal in der Uebersicht zu waehlen, waere ein zweiter Klick fuer
    eine Absicht, die schon feststand.
    """
    formular = await request.form()
    name = str(formular.get("name", "")).strip()
    eingetragen = str(formular.get("eingetragen", "")).strip()
    zustand = str(formular.get("zustand", "AKTIV"))

    if not name:
        return _meldung("/#neues-projekt", "Ohne Namen geht es nicht.",
                        "schlecht")
    if not eingetragen:
        # Kein erfundenes Datum: Das Feld traegt keine Vorgabe, und dann
        # darf es auch nicht stillschweigend eine bekommen.
        return _meldung("/#neues-projekt", "Das Eintragsdatum fehlt.",
                        "schlecht")
    if zustand not in ZUSTAENDE:
        return _meldung("/#neues-projekt", "Diesen Zustand gibt es nicht.",
                        "schlecht")

    with datenbank.verbindung() as conn:
        try:
            nummer = datenbank.projekt_anlegen(
                conn, name, eingetragen,
                beschreibung=str(formular.get("beschreibung", "")),
                vision=str(formular.get("vision", "")),
                zustand=zustand)
        except sqlite3.IntegrityError:
            return _meldung(
                "/#neues-projekt",
                "Den Namen »%s« gibt es schon. Er muss eindeutig "
                "sein, weil er das Losungswort beim Loeschen ist." % name,
                "schlecht")
        # Die Bereiche kommen als eine Zeile mit Kommas -- sechs Felder
        # nebeneinander waeren beim Anlegen mehr Formular als Nutzen.
        for wert in str(formular.get("bereiche", "")).split(","):
            if wert.strip():
                datenbank.bereich_anlegen(conn, nummer, wert)

    antwort = _meldung("/#eintrag-%d" % nummer,
                       "%s angelegt als %s -- und gewaehlt."
                       % (name, datenbank.kennung("P", nummer)), "gut")
    _gewaehlt_setzen(antwort, nummer)
    return antwort


@app.post("/projekte/bereich")
async def bereich_dazu(request: Request) -> RedirectResponse:
    """Einen Bereich an ein Projekt haengen."""
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    wert = str(formular.get("wert", "")).strip()
    if not nummer.isdigit():
        return _meldung("/", "Kein Projekt angegeben.", "schlecht")
    if not wert:
        return _meldung("/#eintrag-%s" % nummer, "Kein Bereich eingegeben.")
    with datenbank.verbindung() as conn:
        datenbank.bereich_anlegen(conn, int(nummer), wert)
    return _meldung("/#eintrag-%s" % nummer,
                    "Bereich »%s« dazu." % wert, "gut")


@app.post("/projekte/bereich/loeschen")
async def bereich_weg(request: Request) -> RedirectResponse:
    """Einen Bereich entfernen -- solange nichts daran haengt.

    **Das sperrt, es mahnt nicht.** Der Bereich eines Eintrags waechst
    nicht nach: Er steht in keiner zweiten Spalte, aus der er sich
    wiederherstellen liesse, und ein Eintrag ohne Bereich waere in jeder
    Durchsicht unauffindbar.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    bereich = str(formular.get("bereich", ""))
    if not nummer.isdigit() or not bereich.isdigit():
        return _meldung("/", "Kein Bereich angegeben.", "schlecht")
    with datenbank.verbindung() as conn:
        haengt_dran = datenbank.bereich_loeschen(conn, int(bereich))
    if haengt_dran:
        return _meldung(
            "/#eintrag-%s" % nummer,
            "Der Bereich bleibt: %d Eintrag%s steh%s noch darauf."
            % (haengt_dran, "e" if haengt_dran > 1 else "",
               "en" if haengt_dran > 1 else "t"), "schlecht")
    return _meldung("/#eintrag-%s" % nummer, "Bereich entfernt.", "gut")


@app.post("/projekte/loeschen")
async def projekt_weg(request: Request) -> RedirectResponse:
    """Ein Projekt loeschen -- mit dem Namen als Losungswort.

    **Das Losungswort ist der Projektname und nicht das Wort "Loeschen".**
    Ein festes Wort bestaetigt nur, dass man gelesen hat, DASS geloescht
    wird; der Name bestaetigt, WELCHES. Genau dafuer ist die Abfrage da --
    der zerstoerende Knopf trifft ein Ziel, das oben im Band steht und
    nicht im Formular.

    Gross- und Kleinschreibung sind egal, Leerraum aussen auch: Geprueft
    wird, ob jemand das richtige Projekt gemeint hat, nicht ob er
    abschreiben kann.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    wort = str(formular.get("wort", "")).strip()
    if not nummer.isdigit():
        return _meldung("/", "Kein Projekt angegeben.", "schlecht")

    with datenbank.verbindung() as conn:
        p = datenbank.projekt(conn, int(nummer))
        if not p:
            return _meldung("/", "Dieses Projekt gibt es nicht mehr.",
                            "schlecht")
        if wort.casefold() != p["name"].casefold():
            return _meldung(
                "/?loeschen=%s#eintrag-%s" % (nummer, nummer),
                "Das Wort stimmt nicht. Zum Loeschen muss dort "
                "»%s« stehen." % p["name"], "schlecht")
        datenbank.projekt_loeschen(conn, int(nummer))

    antwort = _meldung("/", "%s (%s) ist geloescht."
                       % (p["name"], p["kennung"]), "gut")
    # Das Cookie zeigte womoeglich genau hierauf. Es stehen zu lassen
    # hiesse, dass im Band bis zum naechsten Klick ein Projekt steht, das
    # es nicht mehr gibt.
    if _gewaehlte_nummer(request) == int(nummer):
        antwort.delete_cookie(COOKIE_PROJEKT)
    return antwort


# ==================================================================== #
# Der Reiter Sammlung
# ==================================================================== #
#
# **Zwei Ansichten desselben Reiters**, und die Trennung ist keine
# Bequemlichkeit: Drei Regeln laufen auf die Durchsicht zu, nicht auf das
# Eintragen -- die Prioritaet steht auf dem Strich, *bis eine Durchsicht
# sie vergibt*; der Abschluss entscheidet sich dort; und ein neuer
# Bereich kommt bei einer Durchsicht dazu. Eine einzige Ansicht stellte
# dem Eintragenden Felder hin, die er nicht fuellen soll.
#
# **Eintragen ist die Startansicht** -- nach demselben Prinzip wie die
# Reiterleiste: Haeufigkeit im Betrieb. Eingetragen wird taeglich,
# durchgesehen alle paar Wochen.

ANSICHTEN = ("eintragen", "durchsicht")


def _ohne_projekt(ziel: str) -> RedirectResponse:
    """Antwort, wenn kein Projekt gewaehlt ist.

    Die vier Register haengen an der Vorauswahl. Statt eine leere Seite
    zu zeigen, die aussieht wie ein Fehler, geht es dorthin, wo die
    Auswahl getroffen wird -- mit dem Satz dazu.
    """
    return _meldung(ziel, "Dafuer muss ein Projekt gewaehlt sein.", "schlecht")


def _gewaehltes(request: Request, conn) -> dict | None:
    nummer = _gewaehlte_nummer(request)
    return datenbank.projekt(conn, nummer) if nummer else None


@app.get("/sammlung", response_class=HTMLResponse)
def sammlung_seite(request: Request, ansicht: str = "eintragen",
                   suche: str = "", buendeln: int = 0,
                   bearbeiten: int = 0) -> HTMLResponse:
    """Die Sammlung -- eintragen oder durchsehen.

    ``buendeln`` traegt die Zahl der markierten Eintraege, wenn die
    Seite gerade nach dem gemeinsamen Bild fragt. ``bearbeiten`` traegt
    die Nummer des Eintrags, der gerade als Formular dasteht statt als
    Text. Wie der Loeschschritt bei den Projekten steht der
    Zwischenschritt in der Adresse und nicht im Server: Er ist eine
    Ansicht, kein Zustand.

    **Genau einer auf einmal, und deshalb eine Nummer und kein
    Schalter:** Zwei offene Formulare auf einer Seite heisst, dass wer
    das eine speichert, das andere mitschickt -- auch das, was er nur
    aufgeklappt und wieder verlassen hatte.
    """
    if ansicht not in ANSICHTEN:
        ansicht = "eintragen"

    eintraege: list = []
    zahlen: dict = {}
    markiert: list = []
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if projekt:
            eintraege = datenbank.topics(conn, projekt["id"], suche)
            zahlen = datenbank.sammlung_zahlen(conn, projekt["id"])
            markiert = (_markierte(request, projekt["id"], conn)
                        if buendeln else [])

    # **projekt wird hier ueberschrieben, und das ist kein Versehen:**
    # rahmen() legt die schlanke Fassung aus dem Band hinein -- Kennung,
    # Name, Zustand. Diese Seite braucht die Bereiche dazu, denn ohne
    # einen laesst sich nichts eintragen. Beide heissen "projekt", weil
    # es dasselbe Projekt ist; die Vorlage soll nicht zwei Namen kennen.
    return html.TemplateResponse(
        request, "sammlung.html",
        rahmen(request, "sammlung", projekt=projekt, ansicht=ansicht,
               eintraege=eintraege, zahlen=zahlen, suche=suche,
               markiert=markiert, bearbeiten=bearbeiten,
               kategorien=datenbank.KATEGORIEN,
               prios=datenbank.PRIOS,
               fehlerangaben=datenbank.FEHLERANGABEN,
               heute=datenbank.heute()))


def _markierte(request: Request, projekt_id: int, conn) -> list[dict]:
    """Die Eintraege, die der Buendelschritt gerade zusammenlegen soll.

    Sie stehen als ``mark`` in der Adresse -- mehrfach, einmal je
    Eintrag. Ein Zwischenschritt, der die Auswahl im Server merkte,
    verloere sie beim Neuladen und zeigte sie einem zweiten Browser.
    """
    roh = [w for w in request.query_params.getlist("mark") if w.isdigit()]
    gefunden = [datenbank.topic(conn, int(w)) for w in roh]
    return [t for t in gefunden if t and t["projekt_id"] == projekt_id]


@app.post("/sammlung/neu")
async def topic_neu(request: Request) -> RedirectResponse:
    """Eintragen -- drei Angaben, der Rest steht schon da.

    **Die fuenf Fehlerangaben werden hier nicht geprueft.** Ein
    unvollstaendiger FEHLER wird angelegt und danach ein Befund; er wird
    nicht abgewiesen. Eine Regel, deren Weg teuer ist, wird umgangen --
    und dann steht die Ordnung auf dem Papier.
    """
    formular = await request.form()
    titel = str(formular.get("titel", "")).strip()
    bereich = str(formular.get("bereich", ""))
    kategorie = str(formular.get("kategorie", "IDEE"))
    eingetragen = str(formular.get("eingetragen", "")).strip()

    if not titel:
        return _meldung("/sammlung#neuer-eintrag", "Ohne Titel geht es nicht.",
                        "schlecht")
    if not bereich.isdigit():
        return _meldung("/sammlung#neuer-eintrag",
                        "Ohne Bereich geht es nicht -- er ist die Achse, "
                        "nach der spaeter sortiert wird.", "schlecht")
    if kategorie not in datenbank.KATEGORIEN:
        return _meldung("/sammlung#neuer-eintrag",
                        "Diese Kategorie gibt es nicht.", "schlecht")
    if not eingetragen:
        eingetragen = datenbank.heute()

    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/")
        if not any(b["id"] == int(bereich) for b in projekt["bereiche"]):
            # Ein Bereich aus einem anderen Projekt -- etwa aus einer
            # Seite, die noch offen lag, als jemand umgeschaltet hat.
            return _meldung("/sammlung#neuer-eintrag",
                            "Diesen Bereich gibt es in diesem Projekt nicht.",
                            "schlecht")
        texte = {spalte: str(formular.get(spalte, ""))
                 for spalte in datenbank.TOPIC_TEXTE}
        nummer = datenbank.topic_anlegen(
            conn, projekt["id"], titel, int(bereich), eingetragen,
            kategorie, **texte)
        neu = datenbank.topic(conn, nummer)

    satz = "%s angelegt: %s." % (neu["kennung"], titel)
    if neu["fehlt"]:
        # Gesagt, nicht verschwiegen -- und trotzdem angelegt.
        satz += (" %d von fuenf Fehlerangaben fehlen noch; der Eintrag "
                 "steht so lange als Befund." % len(neu["fehlt"]))
    return _meldung("/sammlung#eintrag-%d" % nummer, satz,
                    "gut" if not neu["fehlt"] else "")


@app.post("/sammlung/speichern")
async def topics_speichern(request: Request) -> RedirectResponse:
    """Was in der Durchsicht oder im Bearbeiten-Schritt geaendert wurde.

    Und der Vermerk, dass jemand hingesehen hat: **auch dann, wenn
    nichts anders dasteht.** Eine Durchsicht, bei der alles so bleibt,
    ist eine Durchsicht -- die Zahl misst das Hinsehen, nicht das
    Aendern.

    **Beide Wege laufen hier zusammen, und das ist keine Sparsamkeit:**
    Aus der Durchsicht kommen Prioritaeten fuer viele Eintraege, aus dem
    Bearbeiten-Schritt alle Felder eines einzigen. Beides heisst *aendere
    Feld X an Eintrag Y*, und die Form ``feld:nummer`` traegt beides.
    Eine zweite Route waere eine zweite Stelle, an der dieselben
    Pruefungen stehen muessten -- und die zweite vergisst man.
    """
    formular = await request.form()
    gesammelt: dict[int, dict[str, str]] = {}
    for schluessel, wert in formular.multi_items():
        feld, trenner, nummer = str(schluessel).partition(":")
        if not trenner or feld not in datenbank.TOPIC_AENDERBAR \
                or not nummer.isdigit():
            continue
        gesammelt.setdefault(int(nummer), {})[feld] = str(wert)

    ansicht = str(formular.get("ansicht", "durchsicht"))
    ziel = "/sammlung?ansicht=%s" % (ansicht if ansicht in ANSICHTEN
                                     else "durchsicht")

    # **Wer einen einzelnen Eintrag bearbeitet hat, will danach bei ihm
    # stehen** und nicht am Seitenanfang. Aus der Durchsicht kommen
    # viele Nummern auf einmal -- dann gibt es keine, zu der man
    # zurueckspringen koennte, und der Anker bleibt weg.
    if len(gesammelt) == 1:
        ziel += "#eintrag-%d" % next(iter(gesammelt))

    geaendert = 0
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/")
        for nummer, felder in gesammelt.items():
            vorher = datenbank.topic(conn, nummer)
            if not vorher or vorher["projekt_id"] != projekt["id"]:
                continue
            # Was aus einem Formularfeld kommt, traegt gern Leerzeichen
            # am Rand. topic_anlegen schneidet sie beim Anlegen ab, hier
            # geschieht dasselbe -- sonst gilt ein Titel als geaendert,
            # an dem niemand etwas geaendert hat.
            neu = {k: v.strip() for k, v in felder.items()
                   if v.strip() != str(vorher[k])}

            # **Bis zum Bearbeiten-Schritt kam aus diesem Formular nur
            # die Prioritaet.** Jetzt kommen Titel, Kategorie und Bereich
            # dazu, und was ein Formular schickt, ist keine Zusage
            # darueber, was drinsteht: Die Auswahllisten stehen im
            # Browser und nicht hier.
            if "prio" in neu and neu["prio"] not in datenbank.PRIOS:
                return _meldung(ziel, "Diese Prioritaet gibt es nicht.",
                                "schlecht")
            if "titel" in neu and not neu["titel"]:
                return _meldung(ziel, "Ohne Titel geht es nicht -- er ist "
                                      "das, was in jeder Liste steht.",
                                "schlecht")
            if "kategorie" in neu and neu["kategorie"] not in datenbank.KATEGORIEN:
                return _meldung(ziel, "Diese Kategorie gibt es nicht.",
                                "schlecht")
            # Der Bereich muss einer DIESES Projekts sein. Ein fremder
            # ergaebe eine Zeile, die auf einer Achse steht, die es in
            # ihrem Projekt gar nicht gibt.
            if "bereich_id" in neu and neu["bereich_id"] not in [
                    str(b["id"]) for b in projekt["bereiche"]]:
                return _meldung(ziel, "Diesen Bereich gibt es in diesem "
                                      "Projekt nicht.", "schlecht")
            if not neu:
                continue
            datenbank.topic_aendern(conn, nummer, **neu)
            geaendert += 1
        if ansicht == "durchsicht":
            datenbank.durchsicht_vermerken(conn, projekt["id"])

    if not geaendert:
        return _meldung(ziel, "Nichts geaendert -- die Durchsicht ist "
                              "trotzdem vermerkt.")
    return _meldung(ziel, "%d Eintrag%s gespeichert."
                    % (geaendert, "e" if geaendert > 1 else ""), "gut")


@app.post("/sammlung/verwerfen")
async def topic_verwerfen(request: Request) -> RedirectResponse:
    """Einen Eintrag verwerfen.

    **Das ist der Abschluss, der eine Zeile im Quittungsbuch bekommt** --
    anders als *aufgabe*: Es ist nicht fertig, es zieht um. Der Eintrag
    verschwindet danach aus dieser Liste und steht im Archiv.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    if not nummer.isdigit():
        return _meldung("/sammlung", "Kein Eintrag angegeben.", "schlecht")
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        t = datenbank.topic(conn, int(nummer))
        if not projekt or not t or t["projekt_id"] != projekt["id"]:
            return _meldung("/sammlung", "Diesen Eintrag gibt es nicht.",
                            "schlecht")
        datenbank.topic_abschliessen(conn, int(nummer), "verworfen")
        datenbank.durchsicht_vermerken(conn, projekt["id"])
    return _meldung("/sammlung?ansicht=durchsicht",
                    "%s ist verworfen und steht im Archiv." % t["kennung"],
                    "gut")


@app.post("/sammlung/zusammenlegen")
async def topics_zusammenlegen(request: Request) -> RedirectResponse:
    """Aus markierten Eintraegen eine Aufgabe machen.

    **Zwei Schritte, und der erste ist eine Frage.** Der Knopf in der
    Tabellenkopfzeile fuehrt hierher ohne Titel; dann leitet diese Route
    in den Buendelschritt. Erst der zweite Aufruf legt an.

    **Gefragt wird nach ZWEIERLEI: dem gemeinsamen Bild und der
    Abnahme** -- in dem Augenblick, in dem das Denken gerade
    stattgefunden hat. Das ist die einzige Gelegenheit, zu der beides
    billig ist.

    **Die Abnahme sperrt, "Was dahintersteckt" mahnt.** Ohne Abnahme ist
    es keine Aufgabe, sondern eine Beobachtung mit Kopfzeile; die Ursache
    dagegen kann man nachtragen, sobald man sie versteht. Und weil die
    Abnahme sperrt, MUSS der Schritt den zweiten Ausgang anbieten --
    *das schaffe ich nicht, zurueck in die Sammlung.* Ein Pflichtfeld
    ohne Fluchtweg erzeugt keine besseren Daten, sondern Fuellsel.
    """
    formular = await request.form()
    markiert = [w for w in formular.getlist("mark") if str(w).isdigit()]
    if not markiert:
        return _meldung("/sammlung?ansicht=durchsicht",
                        "Nichts markiert -- die Kaestchen links sagen, "
                        "was zusammengehoert.", "schlecht")

    titel = str(formular.get("titel", "")).strip()
    if not titel:
        # Erster Schritt: nach dem gemeinsamen Bild und der Abnahme
        # fragen, statt stillschweigend anzulegen.
        frage = "&".join("mark=%s" % w for w in markiert)
        return RedirectResponse(
            "/sammlung?ansicht=durchsicht&buendeln=%d&%s#buendeln"
            % (len(markiert), frage), status_code=303)

    abnahme = datenbank.zeilen(str(formular.get("abnahme", "")))
    if not abnahme:
        frage = "&".join("mark=%s" % w for w in markiert)
        return _meldung(
            "/sammlung?ansicht=durchsicht&buendeln=%d&%s#buendeln"
            % (len(markiert), frage),
            "Ohne Abnahme ist es keine Aufgabe, sondern eine Beobachtung "
            "mit Kopfzeile. Laesst sie sich nicht beschreiben, bleiben die "
            "Eintraege in der Sammlung -- der Knopf daneben tut genau das.",
            "schlecht")

    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/")
        try:
            aufgabe = datenbank.zusammenlegen(
                conn, projekt["id"], [int(w) for w in markiert], titel,
                str(formular.get("dahinter", "")), abnahme,
                datenbank.zeilen(str(formular.get("arbeit", ""))))
        except ValueError as warum:
            return _meldung("/sammlung?ansicht=durchsicht", str(warum),
                            "schlecht")
        datenbank.durchsicht_vermerken(conn, projekt["id"])

    return _meldung(
        "/aufgaben#eintrag-%d" % aufgabe,
        "%s angelegt aus %d %s." % (datenbank.kennung("A", aufgabe),
                                    len(markiert),
                                    "Einträgen" if len(markiert) > 1
                                    else "Eintrag"),
        "gut")


# ==================================================================== #
# Der Reiter Aufgaben
# ==================================================================== #
#
# **Hier sitzt jemand dran, und das ist der Unterschied zur Sammlung.**
# Deshalb hat eine Aufgabe einen Status und ein Topic keinen: Niemand
# arbeitet an einer losen Beobachtung.
#
# **Das eine Pflichtfeld ist die Abnahme.** Sie sperrt beim Anlegen --
# eine Aufgabe ohne Abnahme ist keine unvollstaendige Aufgabe, sondern
# eine Beobachtung mit Kopfzeile. "Was dahintersteckt" mahnt dagegen nur:
# Die Ursache kann man nachtragen, sobald man sie versteht.


@app.get("/aufgaben", response_class=HTMLResponse)
def aufgaben_seite(request: Request, suche: str = "") -> HTMLResponse:
    """Uebersicht, Aufgaben, Neue Aufgabe."""
    liste: list = []
    steine: list = []
    projekt = None
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if projekt:
            liste = datenbank.aufgaben(conn, projekt["id"], suche)
            steine = datenbank.meilensteine(conn, projekt["id"])
    return html.TemplateResponse(
        request, "aufgaben.html",
        rahmen(request, "aufgaben", projekt=projekt, aufgaben=liste,
               steine=steine, suche=suche, prios=datenbank.PRIOS,
               status=datenbank.STATUS, heute=datenbank.heute()))


@app.post("/aufgaben/neu")
async def aufgabe_neu(request: Request) -> RedirectResponse:
    """Eine Aufgabe ohne Ursprung -- der seltenere, erlaubte Weg.

    Der uebliche fuehrt ueber die Sammlung: Dort fragt *Zusammenlegen*
    nach Ursache und Abnahme in dem Augenblick, in dem das Denken gerade
    stattgefunden hat.
    """
    formular = await request.form()
    titel = str(formular.get("titel", "")).strip()
    bereich = str(formular.get("bereich", ""))
    prio = str(formular.get("prio", datenbank.STRICH))
    eingetragen = str(formular.get("eingetragen", "")).strip()
    abnahme = datenbank.zeilen(str(formular.get("abnahme", "")))

    if not titel:
        return _meldung("/aufgaben#neue-aufgabe", "Ohne Titel geht es nicht.",
                        "schlecht")
    if not bereich.isdigit():
        return _meldung("/aufgaben#neue-aufgabe",
                        "Ohne Bereich geht es nicht.", "schlecht")
    if prio not in datenbank.PRIOS:
        return _meldung("/aufgaben#neue-aufgabe",
                        "Diese Prioritaet gibt es nicht.", "schlecht")
    if not abnahme:
        # DIE EINE SPERRE, und sie sagt zugleich, wo der Ausgang ist.
        return _meldung(
            "/aufgaben#neue-aufgabe",
            "Ohne Abnahme ist es keine Aufgabe. Laesst sie sich nicht "
            "beschreiben, gehoert die Sache in die Sammlung -- dort wird "
            "sie geschaerft, bis sie sich beschreiben laesst.", "schlecht")

    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/")
        if not any(b["id"] == int(bereich) for b in projekt["bereiche"]):
            return _meldung("/aufgaben#neue-aufgabe",
                            "Diesen Bereich gibt es in diesem Projekt nicht.",
                            "schlecht")
        nummer = datenbank.aufgabe_anlegen(
            conn, projekt["id"], titel, int(bereich),
            eingetragen or datenbank.heute(), abnahme,
            arbeit=datenbank.zeilen(str(formular.get("arbeit", ""))),
            prio=prio, dahinter=str(formular.get("dahinter", "")))
        neu = datenbank.aufgabe(conn, nummer)

    satz = "%s angelegt: %s." % (neu["kennung"], titel)
    if not neu["dahinter"].strip():
        satz += (" Was dahintersteckt fehlt noch -- die Aufgabe steht so "
                 "lange als Befund.")
    return _meldung("/aufgaben#eintrag-%d" % nummer, satz,
                    "gut" if neu["dahinter"].strip() else "")


@app.post("/aufgaben/speichern")
async def aufgaben_speichern(request: Request) -> RedirectResponse:
    """Felder und Haken einer Aufgabe auf einmal.

    **Die Haken brauchen zwei Listen, und das ist keine Umstaendlichkeit:**
    Ein nicht angekreuztes Kaestchen schickt gar nichts mit. Ohne die
    Liste aller Punkte ("punkt") liesse sich ein Haken nie WEGnehmen --
    das Formular saehe aus wie eines, in dem niemand etwas geaendert hat.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    if not nummer.isdigit():
        return _meldung("/aufgaben", "Keine Aufgabe angegeben.", "schlecht")

    felder = {k: str(v) for k, v in formular.items()
              if k in datenbank.AUFGABE_AENDERBAR}
    if felder.get("status") not in (None, *datenbank.STATUS):
        return _meldung("/aufgaben#eintrag-%s" % nummer,
                        "Diesen Status gibt es nicht.", "schlecht")
    if felder.get("prio") not in (None, *datenbank.PRIOS):
        return _meldung("/aufgaben#eintrag-%s" % nummer,
                        "Diese Prioritaet gibt es nicht.", "schlecht")
    # AKTIV und PAUSE ohne Datum weist schon die Ablage ab (CHECK). Hier
    # wird daraus eine Meldung statt eines Fehlers -- der Unterschied
    # zwischen "geht nicht" und "geht nicht, und zwar deshalb".
    if felder.get("status") in ("AKTIV", "PAUSE") \
            and not felder.get("status_seit", "").strip():
        return _meldung("/aufgaben#eintrag-%s" % nummer,
                        "%s braucht ein Datum: Es sagt, seit wann jemand "
                        "dransitzt." % felder["status"], "schlecht")

    # TITEL UND BEREICH lassen sich seit dem 19.09.2026 hier aendern
    # (B-073). Ein leerer Titel wird abgewiesen wie beim Anlegen -- ohne
    # ihn gaebe es in der Uebersicht nichts anzuklicken.
    if "titel" in felder:
        felder["titel"] = felder["titel"].strip()
        if not felder["titel"]:
            return _meldung("/aufgaben#eintrag-%s" % nummer,
                            "Ohne Titel geht es nicht.", "schlecht")
    if "bereich_id" in felder and not felder["bereich_id"].isdigit():
        return _meldung("/aufgaben#eintrag-%s" % nummer,
                        "Ohne Bereich geht es nicht.", "schlecht")

    # DER TEXT JEDER ZEILE, als "text:<nummer>". Eine geleerte Zeile wird
    # abgewiesen und nicht still weggenommen: Wegnehmen hat sein eigenes
    # Kreuz, und ein versehentlich geloeschter Text waere sonst eine
    # verschwundene Zeile.
    texte = {schluessel[5:]: str(wert).strip()
             for schluessel, wert in formular.items()
             if schluessel.startswith("text:") and schluessel[5:].isdigit()}
    if any(not t for t in texte.values()):
        return _meldung("/aufgaben#eintrag-%s" % nummer,
                        "Eine leere Zeile gibt es nicht -- wegnehmen geht "
                        "mit dem Kreuz dahinter.", "schlecht")

    gesetzt = {w for w in formular.getlist("haken") if str(w).isdigit()}
    alle = [w for w in formular.getlist("punkt") if str(w).isdigit()]
    stein = felder.get("meilenstein_id", "")
    if stein and not stein.isdigit():
        return _meldung("/aufgaben#eintrag-%s" % nummer,
                        "Diesen Meilenstein gibt es nicht.", "schlecht")

    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        a = datenbank.aufgabe(conn, int(nummer))
        if not projekt or not a or a["projekt_id"] != projekt["id"]:
            return _meldung("/aufgaben", "Diese Aufgabe gibt es nicht.",
                            "schlecht")
        if stein:
            m = datenbank.meilenstein(conn, int(stein))
            if not m or m["projekt_id"] != projekt["id"]:
                return _meldung("/aufgaben#eintrag-%s" % nummer,
                                "Diesen Meilenstein gibt es in diesem "
                                "Projekt nicht.", "schlecht")
        if "bereich_id" in felder and not any(
                b["id"] == int(felder["bereich_id"])
                for b in projekt["bereiche"]):
            return _meldung("/aufgaben#eintrag-%s" % nummer,
                            "Diesen Bereich gibt es in diesem Projekt nicht.",
                            "schlecht")
        neu = {k: v for k, v in felder.items()
               if v != str(a[k] if a[k] is not None else "")}
        if neu:
            datenbank.aufgabe_aendern(conn, int(nummer), **neu)
        eigene = {str(p["id"]) for p in a["arbeit"] + a["abnahme"]}
        for p in a["arbeit"] + a["abnahme"]:
            text = texte.get(str(p["id"]))
            if text is not None and text != p["text"]:
                datenbank.punkt_text(conn, p["id"], text)
        for punkt in alle:
            if punkt not in eigene:
                continue
            soll = punkt in gesetzt
            ist = any(p["id"] == int(punkt) and p["erledigt"]
                      for p in a["arbeit"] + a["abnahme"])
            if soll != ist:
                datenbank.punkt_haken(conn, int(punkt), soll)

    return _meldung("/aufgaben#eintrag-%s" % nummer, "Gespeichert.", "gut")


@app.post("/aufgaben/punkt")
async def aufgabe_punkt(request: Request) -> RedirectResponse:
    """Eine Zeile an eine der beiden Listen."""
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    art = str(formular.get("art", ""))
    text = str(formular.get("text", "")).strip()
    if not nummer.isdigit() or art not in datenbank.PUNKT_ARTEN:
        return _meldung("/aufgaben", "Keine Liste angegeben.", "schlecht")
    if not text:
        return _meldung("/aufgaben#eintrag-%s" % nummer, "Nichts eingegeben.")
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        a = datenbank.aufgabe(conn, int(nummer))
        if not projekt or not a or a["projekt_id"] != projekt["id"]:
            return _meldung("/aufgaben", "Diese Aufgabe gibt es nicht.",
                            "schlecht")
        datenbank.punkt_anlegen(conn, int(nummer), art, text)
    return _meldung("/aufgaben#eintrag-%s" % nummer, "Zeile dazu.", "gut")


@app.post("/aufgaben/punkt/weg")
async def aufgabe_punkt_weg(request: Request) -> RedirectResponse:
    """Eine Zeile wieder wegnehmen.

    **Der letzte Abnahmepunkt bleibt.** Ohne ihn waere die Aufgabe
    nachtraeglich das, was beim Anlegen nicht durchgegangen waere -- eine
    Sperre, die sich hinterher umgehen laesst, ist keine.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    punkt = str(formular.get("punkt", ""))
    if not nummer.isdigit() or not punkt.isdigit():
        return _meldung("/aufgaben", "Keine Zeile angegeben.", "schlecht")
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        a = datenbank.aufgabe(conn, int(nummer))
        if not projekt or not a or a["projekt_id"] != projekt["id"]:
            return _meldung("/aufgaben", "Diese Aufgabe gibt es nicht.",
                            "schlecht")
        gemeint = [p for p in a["arbeit"] + a["abnahme"]
                   if p["id"] == int(punkt)]
        if not gemeint:
            return _meldung("/aufgaben#eintrag-%s" % nummer,
                            "Diese Zeile gibt es nicht.", "schlecht")
        if gemeint[0]["art"] == "ABNAHME" and len(a["abnahme"]) == 1:
            return _meldung(
                "/aufgaben#eintrag-%s" % nummer,
                "Der letzte Abnahmepunkt bleibt: Ohne Abnahme waere es "
                "keine Aufgabe mehr.", "schlecht")
        datenbank.punkt_loeschen(conn, int(punkt))
    return _meldung("/aufgaben#eintrag-%s" % nummer, "Zeile weg.", "gut")


@app.post("/aufgaben/abschliessen")
async def aufgabe_weg(request: Request) -> RedirectResponse:
    """Erledigt oder verworfen.

    **Erledigt haengt an der ABNAHME, nicht an der Arbeitsliste.** Die
    eine misst, wie weit es ist; die andere, ob es fertig ist. Der Knopf
    steht ausgegraut da, solange ein Haken fehlt -- und der Server prueft
    es noch einmal, denn ein ausgegrauter Knopf ist keine Pruefung.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    art = str(formular.get("art", ""))
    if not nummer.isdigit() or art not in ("erledigt", "verworfen"):
        return _meldung("/aufgaben", "Kein Abschluss angegeben.", "schlecht")
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        a = datenbank.aufgabe(conn, int(nummer))
        if not projekt or not a or a["projekt_id"] != projekt["id"]:
            return _meldung("/aufgaben", "Diese Aufgabe gibt es nicht.",
                            "schlecht")
        if art == "erledigt" and not a["abnehmbar"]:
            offen = len(a["abnahme"]) - a["abnahme_fertig"]
            return _meldung(
                "/aufgaben#eintrag-%s" % nummer,
                "%s: Es fehl%s noch %d Haken in der Abnahme. Woran die "
                "Arbeitsliste steht, zaehlt dafuer nicht."
                % (a["kennung"], "t" if offen == 1 else "en", offen),
                "schlecht")
        datenbank.aufgabe_abschliessen(conn, int(nummer), art)

    wort = ("ist erledigt" if art == "erledigt" else "ist verworfen")
    return _meldung("/aufgaben", "%s %s und steht im Archiv."
                    % (a["kennung"], wort), "gut")


# ==================================================================== #
# Der Reiter Meilensteine
# ==================================================================== #
#
# **Vier Karten, und die zweite ist der Punkt.** *Was dazwischenkam* wird
# notiert, sobald es passiert -- nicht bei der Abnahme. Eine Notiz, die
# man im Augenblick machen soll, aber erst tief in einer Karte suchen
# muss, wird aus dem Gedaechtnis nachgetragen und ist dann wertlos.
# Deshalb steht sie oben als eigene Karte mit drei Feldern.
#
# **Vorerst nur hier** (entschieden am 07.09.2026): kein seitenweites
# Element im Rahmen. Der naheliegendere Weg -- ein Feld in der
# Aufgabenkarte -- haengt an einer Regel, die es noch nicht gibt: dass
# eine Aufgabe einem Meilenstein zugeordnet sein MUSS.


@app.get("/meilensteine", response_class=HTMLResponse)
def meilensteine_seite(request: Request, zeigen: str = "offen") -> HTMLResponse:
    """Uebersicht, Umweg, Meilensteine, Neuer Meilenstein.

    ``zeigen`` ist Regel 7, umgedreht: Die Liste zeigt, was offen ist --
    in der Mappe verschwindet ein abgenommener Stein aus der Datei, hier
    wird daraus ein Filter.
    """
    offen_nur = zeigen != "alle"
    steine: list = []
    alle_zahl = 0
    freie: list = []
    projekt = None
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if projekt:
            steine = datenbank.meilensteine(conn, projekt["id"], offen_nur)
            alle_zahl = len(datenbank.meilensteine(conn, projekt["id"], False))
            # Aufgaben, die noch keinem Stein zugeschlagen sind -- sie
            # stehen in der Auswahl jeder Steinkarte.
            freie = [a for a in datenbank.aufgaben(conn, projekt["id"])
                     if not a["meilenstein_id"]]
    return html.TemplateResponse(
        request, "meilensteine.html",
        rahmen(request, "meilensteine", projekt=projekt, steine=steine,
               alle_zahl=alle_zahl, freie=freie, zeigen=zeigen,
               prios=datenbank.PRIOS, heute=datenbank.heute()))


def _stein_der_zaehlt(request: Request, conn, nummer: str):
    """Ein Stein dieses Projekts -- oder None."""
    projekt = _gewaehltes(request, conn)
    if not projekt or not str(nummer).isdigit():
        return None, None
    stein = datenbank.meilenstein(conn, int(nummer))
    if not stein or stein["projekt_id"] != projekt["id"]:
        return projekt, None
    return projekt, stein


@app.post("/meilensteine/neu")
async def meilenstein_neu(request: Request) -> RedirectResponse:
    """Ein Meilenstein. **Er darf leer entstehen.**

    Aus einer Rueckmeldung oder einem Gespraech ist er ein echter Fall --
    hier wird nichts gesperrt. Dass er leer nicht bleiben darf, ist ein
    Befund.
    """
    formular = await request.form()
    benennung = str(formular.get("benennung", "")).strip()
    prio = str(formular.get("prio", datenbank.STRICH))
    eingetragen = str(formular.get("eingetragen", "")).strip()

    if not benennung:
        return _meldung("/meilensteine#neuer-meilenstein",
                        "Ohne Benennung geht es nicht.", "schlecht")
    if prio not in datenbank.PRIOS:
        return _meldung("/meilensteine#neuer-meilenstein",
                        "Diese Prioritaet gibt es nicht.", "schlecht")

    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/")
        texte = {feld: str(formular.get(feld, ""))
                 for feld in datenbank.MEILENSTEIN_TEXTE}
        nummer = datenbank.meilenstein_anlegen(
            conn, projekt["id"], benennung, eingetragen or datenbank.heute(),
            prio, **texte)
        vorher = str(formular.get("vorgaenger", ""))
        if vorher.isdigit():
            try:
                datenbank.vorgaenger_setzen(conn, nummer, [int(vorher)])
            except ValueError as warum:
                return _meldung("/meilensteine#eintrag-%d" % nummer,
                                str(warum), "schlecht")

    return _meldung(
        "/meilensteine#eintrag-%d" % nummer,
        "%s angelegt: %s. Solange keine Aufgabe daranhaengt, steht er als "
        "Befund." % (datenbank.kennung("M", nummer), benennung), "gut")


@app.post("/meilensteine/speichern")
async def meilenstein_speichern(request: Request) -> RedirectResponse:
    """Die Felder eines Steins, samt Vorgaengern."""
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    felder = {k: str(v) for k, v in formular.items()
              if k in datenbank.MEILENSTEIN_AENDERBAR}
    if felder.get("prio") not in (None, *datenbank.PRIOS):
        return _meldung("/meilensteine#eintrag-%s" % nummer,
                        "Diese Prioritaet gibt es nicht.", "schlecht")

    vorgaenger = [int(w) for w in formular.getlist("vorgaenger")
                  if str(w).isdigit()]

    with datenbank.verbindung() as conn:
        projekt, stein = _stein_der_zaehlt(request, conn, nummer)
        if not projekt:
            return _ohne_projekt("/")
        if not stein:
            return _meldung("/meilensteine", "Diesen Meilenstein gibt es "
                                             "nicht.", "schlecht")
        neu = {k: v for k, v in felder.items() if v != str(stein[k])}
        if neu:
            datenbank.meilenstein_aendern(conn, int(nummer), **neu)
        if vorgaenger != [v["id"] for v in stein["vorgaenger"]]:
            try:
                datenbank.vorgaenger_setzen(conn, int(nummer), vorgaenger)
            except ValueError as warum:
                return _meldung("/meilensteine#eintrag-%s" % nummer,
                                str(warum), "schlecht")
    return _meldung("/meilensteine#eintrag-%s" % nummer, "Gespeichert.", "gut")


@app.post("/meilensteine/dazwischen")
async def dazwischen_neu(request: Request) -> RedirectResponse:
    """Ein Umweg -- der kurze Weg.

    **Notiert, sobald es passiert.** Drei Felder in einer Zeile: Stein,
    Datum, ein Satz. Laenger darf der Weg nicht sein, sonst wird die
    Notiz bei der Abnahme aus dem Gedaechtnis nachgetragen.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    text = str(formular.get("text", "")).strip()
    datum = str(formular.get("datum", "")).strip() or datenbank.heute()
    if not text:
        return _meldung("/meilensteine#dazwischen",
                        "Ein Satz fehlt -- ohne ihn ist es keine Notiz.",
                        "schlecht")
    with datenbank.verbindung() as conn:
        projekt, stein = _stein_der_zaehlt(request, conn, nummer)
        if not projekt:
            return _ohne_projekt("/")
        if not stein:
            return _meldung("/meilensteine#dazwischen",
                            "Kein Meilenstein gewaehlt.", "schlecht")
        datenbank.dazwischen_anlegen(conn, int(nummer), datum, text)
    return _meldung("/meilensteine#eintrag-%s" % nummer,
                    "Notiert an %s." % stein["kennung"], "gut")


@app.post("/meilensteine/dazwischen/weg")
async def dazwischen_weg(request: Request) -> RedirectResponse:
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    zeile = str(formular.get("zeile", ""))
    if not zeile.isdigit():
        return _meldung("/meilensteine", "Keine Zeile angegeben.", "schlecht")
    with datenbank.verbindung() as conn:
        projekt, stein = _stein_der_zaehlt(request, conn, nummer)
        if not projekt or not stein:
            return _meldung("/meilensteine", "Diesen Meilenstein gibt es "
                                             "nicht.", "schlecht")
        if not any(d["id"] == int(zeile) for d in stein["dazwischen"]):
            return _meldung("/meilensteine#eintrag-%s" % nummer,
                            "Diese Zeile gehoert nicht dazu.", "schlecht")
        datenbank.dazwischen_loeschen(conn, int(zeile))
    return _meldung("/meilensteine#eintrag-%s" % nummer, "Zeile weg.", "gut")


@app.post("/meilensteine/aufgabe")
async def stein_aufgabe(request: Request) -> RedirectResponse:
    """Eine Aufgabe zuschlagen oder loesen.

    **Geloest wird nichts geloescht:** Die Aufgabe bleibt, sie gehoert
    nur nicht mehr zu diesem Stein.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    aufgabe = str(formular.get("aufgabe", ""))
    loesen = str(formular.get("loesen", "")) == "ja"
    if not aufgabe.isdigit():
        # Der erste Eintrag der Auswahl ist seit dem 22.09.2026 leer --
        # wer auf "Hinzufügen" klickt, ohne etwas auszusuchen, landet
        # hier. Kein Fehler, nur nichts getan, und das steht dann da.
        return _meldung("/meilensteine#eintrag-%s" % nummer,
                        "Keine Aufgabe gewählt.")
    with datenbank.verbindung() as conn:
        projekt, stein = _stein_der_zaehlt(request, conn, nummer)
        if not projekt or not stein:
            return _meldung("/meilensteine", "Diesen Meilenstein gibt es "
                                             "nicht.", "schlecht")
        a = datenbank.aufgabe(conn, int(aufgabe))
        if not a or a["projekt_id"] != projekt["id"]:
            return _meldung("/meilensteine#eintrag-%s" % nummer,
                            "Diese Aufgabe gibt es nicht.", "schlecht")
        datenbank.aufgabe_zuschlagen(conn, int(aufgabe),
                                     None if loesen else int(nummer))
    return _meldung(
        "/meilensteine#eintrag-%s" % nummer,
        "%s ist %s." % (a["kennung"],
                        "gelöst" if loesen else "zugeordnet"), "gut")


def _abnahmedatum_taugt(tag: str, stein: dict) -> str:
    """Leer, wenn das Datum taugt -- sonst der Satz, der es sagt.

    **Zwei Faelle sind keine Tippfehler, sondern Unmoeglichkeiten**, und
    beide wuerden still eine falsche Dauer erzeugen:

      in der Zukunft   Ein Meilenstein, der morgen abgenommen wurde, ist
                       eine Behauptung ueber etwas, das nicht passiert
                       ist.
      vor dem Eintrag  Abgenommen, bevor es ihn gab -- die Dauer waere
                       negativ, und die Strasse zeigte einen Stein, der
                       rueckwaerts gebaut wurde.

    Geprueft wird hier und nicht im Browser: Ein Datumsfeld mit ``max``
    ist eine Auskunft, keine Pruefung -- es faellt weg, sobald jemand das
    Formular direkt abschickt.
    """
    try:
        gewaehlt = date.fromisoformat(tag)
    except ValueError:
        return "»%s« ist kein Datum." % tag
    if gewaehlt > date.today():
        return "Abgenommen wird nicht in der Zukunft."
    eingetragen = stein.get("eingetragen_am", "")
    try:
        if eingetragen and gewaehlt < date.fromisoformat(eingetragen):
            return ("%s wurde am %s eingetragen — davor kann er nicht "
                    "abgenommen worden sein."
                    % (stein["kennung"], datenbank.datum_zeigen(eingetragen)))
    except ValueError:
        pass
    return ""


@app.post("/meilensteine/abnehmen")
async def stein_abnehmen(request: Request) -> RedirectResponse:
    """Die Abnahme -- vier Handgriffe in einem Knopf.

    Der Server prueft noch einmal, was der ausgegraute Knopf schon sagt:
    Ein ausgegrauter Knopf ist eine Auskunft, keine Pruefung.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    tag = str(formular.get("datum", "")).strip() or datenbank.heute()
    with datenbank.verbindung() as conn:
        projekt, stein = _stein_der_zaehlt(request, conn, nummer)
        if not projekt or not stein:
            return _meldung("/meilensteine", "Diesen Meilenstein gibt es "
                                             "nicht.", "schlecht")
        # DAS DATUM WIRD GEPRUEFT UND NICHT GEGLAUBT. Es geht in die
        # Dauer auf der Straße ein, und eine Dauer, die niemand
        # nachrechnen kann, ist schlimmer als keine.
        fehler = _abnahmedatum_taugt(tag, stein)
        if fehler:
            return _meldung("/meilensteine#eintrag-%s" % nummer, fehler,
                            "schlecht")
        if not stein["abnehmbar"]:
            offen = len(stein["aufgaben"]) - stein["aufgaben_fertig"]
            if not stein["aufgaben"]:
                return _meldung(
                    "/meilensteine#eintrag-%s" % nummer,
                    "%s hat keine Aufgabe -- da ist nichts abzunehmen."
                    % stein["kennung"], "schlecht")
            return _meldung(
                "/meilensteine#eintrag-%s" % nummer,
                "%s: %d Aufgabe%s ist noch offen."
                % (stein["kennung"], offen, "n" if offen > 1 else ""),
                "schlecht")
        datenbank.meilenstein_abnehmen(conn, int(nummer), tag)
        # Gerechnet wird bis zum ABNAHMEDATUM und nicht bis heute. Bis
        # zum 22.09.2026 stand hier tage_seit(), und das war richtig,
        # solange nur heute gestempelt werden konnte -- mit einem
        # nachgetragenen Datum nennte es eine andere Zahl als die
        # Straße daneben.
        dauer = datenbank.tage_zwischen(stein["eingetragen_am"], tag)

    return _meldung(
        "/meilensteine",
        "%s ist abgenommen. Der Stein steht im Archiv -- mit %s Dauer und "
        "%d Umweg%s." % (stein["kennung"],
                         "einem Tag" if dauer == 1 else "%s Tagen" % dauer,
                         len(stein["dazwischen"]),
                         "en" if len(stein["dazwischen"]) != 1 else ""),
        "gut")


@app.post("/meilensteine/verwerfen")
async def stein_verwerfen(request: Request) -> RedirectResponse:
    """Verworfen -- und die Aufgaben darunter bleiben.

    Ein verworfener Meilenstein sagt nichts darueber, ob die Arbeit noch
    zu tun ist; sie hat nur keinen gemeinsamen Termin mehr.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    with datenbank.verbindung() as conn:
        projekt, stein = _stein_der_zaehlt(request, conn, nummer)
        if not projekt or not stein:
            return _meldung("/meilensteine", "Diesen Meilenstein gibt es "
                                             "nicht.", "schlecht")
        datenbank.meilenstein_verwerfen(conn, int(nummer))
        wieder = len(stein["aufgaben"])

    satz = "%s ist verworfen." % stein["kennung"]
    if wieder:
        satz += (" %d Aufgabe%s steh%s wieder ohne Stein da -- verworfen "
                 "ist der Termin, nicht die Arbeit."
                 % (wieder, "n" if wieder > 1 else "",
                    "en" if wieder > 1 else "t"))
    return _meldung("/meilensteine", satz, "gut")


# ==================================================================== #
# Der Reiter Entscheidungen
# ==================================================================== #
#
# **Das groesste Register.** Gemessen an Boots Mappe am 06.09.2026
# tragen Archiv und Entscheidungen zusammen 73 % des Bestands -- die
# laufende Arbeit, also das, was jedes andere Werkzeug zeigt, sind 15 %.
#
# **Hier wird nichts archiviert.** Eine Entscheidung hat keinen
# Abschluss, sondern einen Zustand: Sie ueberlebt das, wozu sie gehoert.
# Deshalb ist die Vorgabe *alle* und nicht *offen*.


def _bezug_lesen(wert: str) -> tuple[str, int | None]:
    """``"B:16"`` -> ``("B", 16)``, alles andere -> kein Bezug.

    Ein Feld statt zweier: Art und Kennung stehen zusammen in einem
    Wert, weil sie zusammengehoeren -- die Ablage verlangt es ohnehin
    (``CHECK (bezug_art = '—') = (bezug_id IS NULL)``).
    """
    art, _, ziel = str(wert or "").partition(":")
    if art in ("B", "A", "M") and ziel.isdigit():
        return art, int(ziel)
    return datenbank.STRICH, None


@app.get("/entscheidungen", response_class=HTMLResponse)
def entscheidungen_seite(request: Request, zeigen: str = "alle",
                         suche: str = "") -> HTMLResponse:
    liste: list = []
    zahlen: dict = {}
    auswahl: list = []
    projekt = None
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if projekt:
            liste = datenbank.entscheidungen(conn, projekt["id"], suche,
                                             offen_nur=(zeigen == "offen"))
            zahlen = datenbank.entscheidungs_zahlen(conn, projekt["id"])
            auswahl = datenbank.bezug_auswahl(conn, projekt["id"])
    return html.TemplateResponse(
        request, "entscheidungen.html",
        rahmen(request, "entscheidungen", projekt=projekt,
               entscheidungen=liste, zahlen=zahlen, auswahl=auswahl,
               zeigen=zeigen, suche=suche,
               zustaende_e=datenbank.ENTSCHEIDUNGSZUSTAENDE,
               heute=datenbank.heute()))


@app.post("/entscheidungen/neu")
async def entscheidung_neu(request: Request) -> RedirectResponse:
    """Eine Entscheidung. **Freistehend ist erlaubt.**

    Und der Zustand darf OFFEN sein: *Es heisst ja nicht, wenn ich eine
    Entscheidung heute nicht treffe, dass gar keine Entscheidung
    getroffen wird.* Ein Register, das nur Fertiges kennte, koennte den
    Fall nicht tragen, den die Mappe an B-016 beschreibt -- achtzig
    geprueufte Woerter, drei Kandidaten, keine Entscheidung.
    """
    formular = await request.form()
    titel = str(formular.get("titel", "")).strip()
    zustand = str(formular.get("zustand", "OFFEN"))
    datum = str(formular.get("datum", "")).strip()

    if not titel:
        return _meldung("/entscheidungen#neue-entscheidung",
                        "Ohne Titel geht es nicht.", "schlecht")
    if zustand not in datenbank.ENTSCHEIDUNGSZUSTAENDE:
        return _meldung("/entscheidungen#neue-entscheidung",
                        "Diesen Zustand gibt es nicht.", "schlecht")

    art, ziel = _bezug_lesen(str(formular.get("bezug", "")))
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/")
        if ziel is not None and not datenbank._bezugskopf(conn, art, ziel):
            return _meldung("/entscheidungen#neue-entscheidung",
                            "Diesen Eintrag gibt es nicht.", "schlecht")
        nummer = datenbank.entscheidung_anlegen(
            conn, projekt["id"], titel, datum or datenbank.heute(), zustand,
            art, ziel, entschluss=str(formular.get("entschluss", "")),
            text=str(formular.get("text", "")))
        neu = datenbank.entscheidung(conn, nummer)

    satz = "%s angelegt: %s." % (neu["kennung"], titel)
    if neu["ohne_satz"]:
        # MAHNEN, NICHT SPERREN: Den Satz kann man nachtragen.
        satz += (" Der Zustand ist ENTSCHLUSS, aber Was entschieden wurde "
                 "ist leer -- ein Entschluss ohne Satz ist keiner.")
    return _meldung("/entscheidungen#eintrag-%d" % nummer, satz,
                    "" if neu["ohne_satz"] else "gut")


@app.post("/entscheidungen/speichern")
async def entscheidung_speichern(request: Request) -> RedirectResponse:
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    if not nummer.isdigit():
        return _meldung("/entscheidungen", "Keine Entscheidung angegeben.",
                        "schlecht")
    felder = {k: str(v) for k, v in formular.items()
              if k in datenbank.ENTSCHEIDUNG_AENDERBAR}
    art, ziel = _bezug_lesen(str(formular.get("bezug", "")))

    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        e = datenbank.entscheidung(conn, int(nummer))
        if not projekt or not e or e["projekt_id"] != projekt["id"]:
            return _meldung("/entscheidungen",
                            "Diese Entscheidung gibt es nicht.", "schlecht")
        if ziel is not None and not datenbank._bezugskopf(conn, art, ziel):
            return _meldung("/entscheidungen#eintrag-%s" % nummer,
                            "Diesen Eintrag gibt es nicht.", "schlecht")
        neu = {k: v for k, v in felder.items() if v != str(e[k])}
        wechsel = (art, ziel) != (e["bezug_art"], e["bezug_id"])
        try:
            datenbank.entscheidung_aendern(
                conn, int(nummer), bezug=(art, ziel) if wechsel else None,
                **neu)
        except ValueError as warum:
            return _meldung("/entscheidungen#eintrag-%s" % nummer,
                            str(warum), "schlecht")
        danach = datenbank.entscheidung(conn, int(nummer))

    if danach["ohne_satz"]:
        return _meldung(
            "/entscheidungen#eintrag-%s" % nummer,
            "Gespeichert. Der Zustand ist ENTSCHLUSS, aber Was entschieden "
            "wurde ist leer -- ein Entschluss ohne Satz ist keiner.")
    return _meldung("/entscheidungen#eintrag-%s" % nummer, "Gespeichert.",
                    "gut")


@app.post("/entscheidungen/loeschen")
async def entscheidung_weg(request: Request) -> RedirectResponse:
    """Wegwerfen -- das einzige Register, in dem das der Weg hinaus ist.

    Anderswo wird abgeschlossen und archiviert. Eine Entscheidung hat
    keinen Abschluss; was falsch eingetragen wurde, muss deshalb wirklich
    weg.
    """
    formular = await request.form()
    nummer = str(formular.get("id", ""))
    if not nummer.isdigit():
        return _meldung("/entscheidungen", "Keine Entscheidung angegeben.",
                        "schlecht")
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        e = datenbank.entscheidung(conn, int(nummer))
        if not projekt or not e or e["projekt_id"] != projekt["id"]:
            return _meldung("/entscheidungen",
                            "Diese Entscheidung gibt es nicht.", "schlecht")
        datenbank.entscheidung_loeschen(conn, int(nummer))
    return _meldung("/entscheidungen", "%s ist gelöscht." % e["kennung"],
                    "gut")


# ==================================================================== #
# Der Reiter History
# ==================================================================== #
#
# **Der einzige Reiter, der nur zeigt.** Es gibt hier keine POST-Route:
# Alles faellt aus den fuenf Registern ab. Zwei Ansichten aus drei
# Mappendateien -- Strasse und Archiv.
#
# **Bis zum 22.09.2026 waren es drei** (E-027). Das Quittungsbuch stand
# daneben und zeigte eine Teilmenge des Archivs, mit einem Verweis auf
# eben diese Eintraege. Was es beantwortete, beantwortet jetzt ein Filter
# im Archiv -- und die Unterscheidung, die dahinterstand, steht in
# datenbank.abschlussart().
#
# **Und einen Weg zurueck gibt es nicht.** Ein versehentlich
# abgeschlossener Eintrag laesst sich hier nicht wiedereroeffnen; das ist
# am 07.09.2026 aufgeschoben worden, nicht vergessen. Solange nichts
# darin steht, ist es kein Problem; es wird eins, wenn es das erste Mal
# passiert.

HISTORY_ANSICHTEN = ("strasse", "archiv")


@app.get("/history", response_class=HTMLResponse)
def history_seite(request: Request, ansicht: str = "strasse",
                  art: str = "", suche: str = "",
                  schluss: str = "") -> HTMLResponse:
    # ALTE LESEZEICHEN AUF DAS QUITTUNGSBUCH landen im Archiv, gefiltert
    # auf die Enden -- das ist genau das, was dort stand. Ein stilles
    # Zurueckfallen auf die Strasse waere die bequemere Zeile und die
    # falsche: Wer "quittung" aufruft, sucht Abschluesse und keine
    # Meilensteine. Siehe E-027.
    if ansicht == "quittung":
        ansicht, schluss = "archiv", schluss or "ende"
    if ansicht not in HISTORY_ANSICHTEN:
        ansicht = "strasse"
    if art not in ("", "B", "A", "M"):
        art = ""
    if schluss not in ("", "ende", "umzug"):
        schluss = ""

    steine: list = []
    im_archiv: list = []
    zahlen: dict = {}
    offene: list = []
    projekt = None
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if projekt:
            zahlen = datenbank.history_zahlen(conn, projekt["id"])
            if ansicht == "strasse":
                steine = datenbank.strasse(conn, projekt["id"])
                # Was noch vor uns liegt -- der letzte Punkt der Strasse
                # heisst "hier" und zeigt darauf.
                offene = datenbank.meilensteine(conn, projekt["id"])
            else:
                im_archiv = datenbank.archiv(conn, projekt["id"], art, suche,
                                             schluss)

    return html.TemplateResponse(
        request, "history.html",
        rahmen(request, "history", projekt=projekt, ansicht=ansicht,
               steine=steine, offene=offene,
               archiv=im_archiv, zahlen=zahlen, art=art, suche=suche,
               schluss=schluss))


# ==================================================================== #
# Der Reiter Einrichtung
# ==================================================================== #
#
# **Acht Karten** -- die sieben aus docs/uebernahme.md, Abschnitt 6, und der
# Export als achte. In Boot gibt es ihn nicht; hier traegt er drei
# Zwecke, und der dritte hat ihn zur eigenen Karte gemacht: Er ist der
# Weg, auf dem der Bestand eine Versionsgeschichte bekommt.
#
# **Was nicht mitkommt:** *IP-Adresse uebernehmen*. Das ist Boot-eigen --
# dort steht die Serveradresse in den iPXE-Skripten, deshalb ist ein
# Adresswechsel ein Ereignis. Fuer Tasks ist er keins.

# Wohin ein Fehlerbericht geht. Steht in der Umgebung, damit ein
# Betreiber ihn auf seine eigene Adresse umbiegen kann -- etwa, wenn er
# das Produkt selbst betreut.
BERICHT_ADRESSE = os.environ.get("MARLEI_BERICHT", "") or "support@exmig.de"


def _stand_kurz_oder_leer() -> str:
    return stand_kurz()


@app.get("/einrichtung", response_class=HTMLResponse)
def einrichtung_seite(request: Request, fehlerbericht: int = 0,
                      umgebung_mit: int = 0,
                      werkseinstellung: str = "") -> HTMLResponse:
    """Acht Karten -- Stand, Export, Ablageorte, Einstellungen, Firewall,
    Fehlerbericht, Verbesserungen, Werkseinstellung.

    ``werkseinstellung`` traegt den Schritt, in dem die Karte gerade
    steht -- wie der Loeschschritt unter Projekte in der Adresse und
    nicht im Server: Er ist eine Ansicht, kein Zustand.
    """
    text = ""
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        export_stand = export.stand(projekt) if projekt else {}
        # DER ORT HAENGT NICHT AM PROJEKT: Ablageorte fragt, ob der
        # Ausgang da und beschreibbar ist -- diese Frage hat auch ohne
        # gewaehltes Projekt eine Antwort.
        export_ort = export.ort()
        export_offen = export.aktuell(conn, projekt) if projekt else []
        bestand = projekt["bestand"] if projekt else {}
        db_bytes = 0
        try:
            db_bytes = Path(datenbank.DB_PFAD).stat().st_size
        except OSError:
            pass
        if fehlerbericht:
            text = bericht.text(conn, stand_kurz(), bool(umgebung_mit))

    return html.TemplateResponse(
        request, "einrichtung.html",
        rahmen(request, "einrichtung", projekt=projekt,
               stand=versionsstand.auskunft(),
               updatestand=updatewacht.stand(),
               updateauswahl=updatewacht.AUSWAHL,
               db_pfad=str(datenbank.DB_PFAD),
               db_bytes=db_bytes, export_stand=export_stand,
               export_offen=export_offen, export_dateien=export.DATEIEN,
               bestand=bestand, firewall=firewall.lage(),
               export_ort=export_ort,
               oberflaechenport=_oberflaechenport(),
               ports=firewall.ports(_oberflaechenport()),
               nicht_oeffnen=firewall.nicht_oeffnen(_oberflaechenport()),
               bericht_adresse=BERICHT_ADRESSE, bericht_text=text,
               bericht_umgebung=bool(umgebung_mit),
               werkseinstellung=werkseinstellung,
               einstellungen=_einstellungen()))


def _oberflaechenport() -> int:
    """Unter welchem Port diese Oberflaeche erreichbar ist.

    **Nicht der Port, auf dem die Anwendung hoert** -- das ist 18081 auf
    127.0.0.1, und dorthin kommt von aussen niemand. Gemeint ist der Port
    des nginx davor, und der steht in der Adresse, die im Kopfband steht:
    MARLEI_BASE_URL.

    **Unter Windows sind es dieselbe Zahl und dieselbe Quelle.** Dort
    steht kein nginx davor; uvicorn hoert selbst auf diesem Port -- und
    ``start.ps1`` liest ihn aus genau dieser Adresse, damit die Zahl nicht
    an zwei Stellen steht. Diese Funktion bleibt deshalb dieselbe, und die
    Karte stimmt auf beiden Systemen.

    **Ohne Angabe: 80, und das ist keine Vorgabe, sondern die Bedeutung
    einer Adresse ohne Port.** Die Vorgabe von install.sh ist 8081 -- nur
    steht die dann auch in MARLEI_BASE_URL. Eine Adresse ohne Doppelpunkt
    heisst 80, egal was das Installationsskript sonst tut.
    """
    rest = BASE_URL.rsplit(":", 1)[-1] if BASE_URL.count(":") > 1 else ""
    rest = rest.split("/")[0]
    return int(rest) if rest.isdigit() else 80


def _einstellungen() -> list[dict]:
    """Die Umgebungsdatei als Tabelle -- rein lesend.

    **Diese Karte aendert nichts, und das ist Absicht.** Die Datei
    gehoert root, die Anwendung kann dort nicht schreiben. Sie
    beantwortet die Frage, wie dieser Server aufgesetzt ist, ohne dass
    man sich per SSH anmelden muss.

    **Nicht dasselbe wie Ablageorte, obwohl beide Pfade zeigen:** Hier
    steht, *was eingestellt ist*; dort, *ob es da und beschreibbar ist*.
    """
    return [
        {"name": "MARLEI_BASE_URL", "wert": BASE_URL,
         "wofuer": "Steht im Kopfband, damit man weiß, mit welchem Server "
                   "man redet."},
        {"name": "MARLEI_DB", "wert": str(datenbank.DB_PFAD),
         "wofuer": "Wo die Ablage liegt."},
        # NICHT str(export.ZIEL): Ohne eingerichteten Ausgang ist das
        # None, und str(None) ist "None" -- ein Wort, das wie ein Pfad
        # aussieht. Leer heisst hier leer, und die Vorlage schreibt dann
        # "nicht gesetzt" hin.
        {"name": "MARLEI_EXPORT",
         "wert": str(export.ZIEL) if export.ZIEL else "",
         "wofuer": "Wohin der Export schreibt."},
        {"name": "MARLEI_KENNZEICHNUNG", "wert": KENNZEICHNUNG,
         "wofuer": "Steht hier ein Wort, ist dieser Server nicht die "
                   "Produktion — der Seitengrund wechselt dazu auf Sand."},
        {"name": "MARLEI_BERICHT", "wert": BERICHT_ADRESSE,
         "wofuer": "Wohin ein Fehlerbericht geht."},
        # **NUR OB, NIE WAS.** Aus dem Hash ist der Schluessel abgeleitet,
        # mit dem die Anmeldecookies unterschrieben sind -- wer ihn liest,
        # kann sich eines bauen. Er steht deshalb auf keiner Seite, auch
        # nicht fuer jemanden, der angemeldet ist.
        {"name": "MARLEI_KENNWORT_HASH",
         "wert": "gesetzt" if anmeldung.gesetzt() else "",
         "wofuer": "Das Kennwort der Oberfläche, als Hash. Hier steht nur, "
                   "ob eines gesetzt ist — neu setzen geht auf der "
                   "Maschine, mit dem Installationsskript."},
    ]


@app.get("/einrichtung/bericht.txt", response_class=PlainTextResponse)
def bericht_datei(request: Request, umgebung_mit: int = 0) -> PlainTextResponse:
    """Derselbe Bericht als Datei -- zum Anhaengen an eine Mail.

    **Auf dem Server bleibt nichts liegen:** Er wird bei jedem Abruf neu
    gebaut und nirgends abgelegt.
    """
    with datenbank.verbindung() as conn:
        text = bericht.text(conn, stand_kurz(), bool(umgebung_mit))
    return PlainTextResponse(
        text, headers={"content-disposition":
                       'attachment; filename="marlei-tasks-bericht.txt"'})


@app.get("/einrichtung/export.zip")
def export_paket(request: Request):
    """Der Ausgang als Paket -- der Weg an den Bestand ohne Shell.

    **Er schreibt nichts.** Die Texte entstehen im Speicher, der
    eingerichtete Ausgang bleibt unberuehrt, und *Stand der Ausgabe*
    sagt danach dasselbe wie davor. Wer den Bestand sichern will, braucht
    damit weder einen Zugang zur Maschine noch einen eingerichteten
    Ausgang.

    **Das gewaehlte Projekt**, wie ueberall: Ein Paket mit allen dreien
    waere die zweite Ausnahme neben den Befunden.
    """
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/einrichtung#export")
        daten = export.als_zip(conn, projekt)
    name = "%s-%s.zip" % (export.verzeichnisname(projekt), datenbank.heute())
    return Response(
        content=daten, media_type="application/zip",
        headers={"content-disposition": 'attachment; filename="%s"' % name})


@app.post("/einrichtung/export")
async def export_schreiben(request: Request) -> RedirectResponse:
    """Das gewaehlte Projekt ausgeben.

    **Nicht alle auf einmal** (entschieden im September 2026): Die
    Vorauswahl gilt fuer Sammlung, Aufgaben, Meilensteine und
    Entscheidungen -- sie gilt hier genauso.
    """
    formular = await request.form()
    weiter = str(formular.get("weiter", ""))
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/")
        try:
            geschrieben = export.schreiben(conn, projekt)
        except (ValueError, OSError) as warum:
            return _meldung("/einrichtung#export",
                            "Ausgeben ging nicht: %s" % warum, "schlecht")

    ziel = ("/einrichtung?werkseinstellung=wort#werkseinstellung"
            if weiter == "werkseinstellung" else "/einrichtung#export")
    return _meldung(
        ziel, "%s ausgegeben: %d Dateien nach %s."
        % (projekt["name"], geschrieben["dateien"], geschrieben["ordner"]),
        "gut")


@app.post("/einrichtung/updatepruefung")
async def updatepruefung_setzen(request: Request) -> RedirectResponse:
    """Wie oft nachgesehen wird, ob es eine neuere Fassung gibt.

    Eine von zwei Einstellungen, die diese Seite schreibt -- und sie
    schreibt sie **nicht** in die Umgebungsdatei, sondern neben die
    Ablage. Warum: siehe einstellungen.py. Sie wirkt sofort; der Waechter
    fragt stuendlich, ob er darf.
    """
    formular = await request.form()
    if updatewacht.offline():
        # Der Offline-Modus setzt den Rahmen, die Auswahl waehlt darin --
        # ueberstimmen kann sie ihn nicht. Erreichbar ist das nur, wer das
        # Formular von Hand abschickt: Die Karte zeigt die Auswahl dann
        # gar nicht erst.
        return _meldung(
            "/einrichtung#stand",
            "Der Offline-Modus ist an — diese Maschine fragt nicht nach "
            "draußen.", "schlecht")
    erlaubt = dict(updatewacht.AUSWAHL)
    try:
        wert = int(str(formular.get("tage", "")))
    except (TypeError, ValueError):
        wert = -1
    if wert not in erlaubt:
        return _meldung("/einrichtung#stand",
                        "Das ist kein gültiger Zeitraum.", "schlecht")
    einstellungen.setze("updatepruefung", wert)
    if not wert:
        # Wer auf "nie" stellt, soll die Auskunft nicht behalten, bis der
        # Waechter sie wegnimmt, den es nicht mehr gibt.
        updatewacht.vergiss()
    else:
        # Und wer sie einschaltet, soll nicht bis zum naechsten
        # Stundenschlag warten -- die Seite sieht dem Blick kurz zu, damit
        # sie sein Ergebnis schon tragen kann. Danach laeuft er notfalls
        # allein weiter; festhalten laesst sich die Seite nicht.
        await run_in_threadpool(updatewacht.starte_blick, None,
                                updatewacht.BEDENKZEIT)
    return _meldung("/einrichtung#stand",
                    "Nachgesehen wird jetzt %s." % erlaubt[wert], "gut")


@app.post("/einrichtung/offline")
async def offline_setzen(request: Request) -> RedirectResponse:
    """Den Offline-Modus umlegen.

    **Eine Eigenschaft der Maschine, keine Gewohnheit des Bedieners** --
    der Unterschied zu "nie" steht in einstellungen.py. Ist er an, fragt
    diese Anwendung ueberhaupt nicht mehr nach draussen.

    Der gemerkte Befund faellt dabei weg. Eine Zahl, die aus einer
    Abfrage stammt, hat auf einer Maschine nichts zu suchen, die gerade
    erklaert hat, dass sie nicht abfragt -- und beim Ausschalten waere sie
    von unbekanntem Alter.
    """
    formular = await request.form()
    an = str(formular.get("offline", "")) in ("1", "an", "on", "true")
    einstellungen.setze("offline", an)
    updatewacht.vergiss()
    if an:
        return _meldung(
            "/einrichtung#stand",
            "Offline-Modus an — diese Maschine fragt nicht mehr nach "
            "draußen.", "gut")
    # Beim Einschalten gleich einmal nachsehen, sonst stuende die Karte
    # bis zum naechsten Stundenschlag auf "Noch nicht gesucht".
    await run_in_threadpool(updatewacht.starte_blick, None,
                            updatewacht.BEDENKZEIT)
    return _meldung("/einrichtung#stand",
                    "Offline-Modus aus — es wird wieder nachgesehen.", "gut")


@app.post("/einrichtung/werkseinstellung")
async def werkseinstellung_setzen(request: Request) -> RedirectResponse:
    """Das gewaehlte Projekt auf den Zustand zuruecksetzen, in dem es
    angelegt wurde.

    **Dasselbe Losungswort wie beim Loeschen: der Projektname.** Ein
    festes Wort bestaetigte nur, DASS zurueckgesetzt wird; der Name
    bestaetigt, WELCHES -- und der zerstoerende Knopf trifft hier ein
    Ziel, das oben im Band steht und nicht im Formular.
    """
    formular = await request.form()
    wort = str(formular.get("wort", "")).strip()
    with datenbank.verbindung() as conn:
        projekt = _gewaehltes(request, conn)
        if not projekt:
            return _ohne_projekt("/")
        if wort.casefold() != projekt["name"].casefold():
            return _meldung(
                "/einrichtung?werkseinstellung=wort#werkseinstellung",
                "Das Wort stimmt nicht. Zum Zurücksetzen muss dort »%s« "
                "stehen." % projekt["name"], "schlecht")
        weg = datenbank.projekt_leeren(conn, projekt["id"])

    return _meldung(
        "/einrichtung#werkseinstellung",
        "%s ist zurückgesetzt: %d Einträge der Sammlung, %d Aufgaben, "
        "%d Meilensteine, %d Entscheidungen und %d Bereiche sind weg."
        % (projekt["name"], weg["sammlung"], weg["aufgaben"],
           weg["meilensteine"], weg["entscheidungen"], weg["bereiche"]),
        "gut")
