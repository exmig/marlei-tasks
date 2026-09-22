#!/usr/bin/env python3
"""Die Hilfe eigenstaendig ausgeben -- ohne laufenden Server.

Wofuer das da ist, zweimal:

**Beim Bearbeiten.** Die Hilfe ist mit Abstand die laengste Seite dieser
Anwendung -- 1848 Zeilen ueber neun Register --, und wer einen Absatz
umstellt, will ihn ansehen, ohne den Dienst zu starten und sich
anzumelden. Das Skript rendert die Vorlage mit denselben Werten, die der
Server einsetzt, und legt sie zusammen mit den Dateien ab, auf die sie
verweist. Was dabei herauskommt, laesst sich im Browser oeffnen.

**Fuer die Veroeffentlichung.** Wer im Repository stoebert, soll die
Register ansehen koennen, bevor er irgendetwas installiert -- GitHub
zeigt eine Vorlage aber als Quelltext. Was hier entsteht, ist genau das,
was GitHub Pages ausliefern kann; der Ablauf dazu steht in
.github/workflows/hilfe.yml.

Deshalb schreibt es nicht nur die HTML-Dateien, sondern kopiert auch
jede Datei mit, die darin vorkommt. Eine Hilfe ohne ihr Stylesheet zeigt
die nachgebauten Ausschnitte der Oberflaeche als nackte Formulare -- und
die sind der Grund, warum es die Seite gibt.

**ZWEI SEITEN, NICHT EINE.** Das ist der Unterschied zu MARLEI Boot, aus
dem dieses Werkzeug abgeschrieben ist. Boots Hilfe kennt ein System;
diese hier traegt sechs Weichen ``{% if windows %}`` -- wie man das
Kennwort neu setzt, wer die Firewallregeln lesen darf, woher die
Auslastung kommt, wie man an die Maschine kommt. Der Server weiss, worauf
er laeuft, eine veroeffentlichte Seite weiss es nicht.

Aufloesen laesst sich die Weiche nicht: Die Zweige sitzen mitten im Satz
("ist nur fuer ``root`` lesbar" / "ist ohne Administratorrechte nicht
nachvollziehbar"), beide nebeneinander gaeben Kauderwelsch. Und eine der
beiden Seiten wegzulassen hiesse, die Haelfte der Leser mit Befehlen zu
bedienen, die es bei ihnen nicht gibt -- MARLEI Tasks wird mit beiden
Setups zugleich veroeffentlicht.

Also beide, und jede sagt oben, dass es die andere gibt.

Aufruf aus dem Projektordner:

    python tools/hilfe-vorschau.py [ZIELORDNER] [--streng]

Ohne Angabe landet alles in build/hilfe/.
"""
import pathlib
import re
import shutil
import sys

from jinja2 import Environment, FileSystemLoader

WURZEL = pathlib.Path(__file__).resolve().parent.parent
WEBUI = WURZEL / "webui"
STATISCH = WEBUI / "static"

# Die beiden Ausgaben. Linux liegt auf index.html, weil der Verweis von
# aussen auf eine Adresse zeigen soll und nicht auf einen Dateinamen --
# und weil der Server dieses Produkts im Regelfall ein Linux ist. Die
# Windows-Seite haengt daneben.
SEITEN = [
    {"windows": False, "datei": "index.html", "name": "Linux",
     "andere": "hilfe-windows.html", "andere_name": "Windows"},
    {"windows": True, "datei": "hilfe-windows.html", "name": "Windows",
     "andere": "index.html", "andere_name": "Linux"},
]

# Was der Server sonst einsetzt. Die Werte sind Beispiele und muessen es
# sein: Es gibt hier keinen Server, den man fragen koennte. Anders als in
# MARLEI Boot wird dafuer kein einziges Modul aus webui/ importiert --
# hilfe.html selbst setzt keine Werte ein, alles hier Aufgefuehrte steht
# in base.html und _befunde.html.
BEISPIEL = {
    # Ein Platzhalter und keine Adresse, und zwar dieselbe Schreibweise
    # wie in docs/installation.md. Eine echte IP waere hier die Adresse
    # eines fremden Heimnetzes, auf einer Seite im Netz.
    "base_url": "http://<Tasks-Server>",
    "aktiv": "hilfe",
    "meldung": "",
    "meldungsart": "",
    # Leer: Die Kennzeichnung sagt, dass eine Maschine NICHT die
    # Produktion ist. Eine Vorschau ist ueberhaupt keine Maschine.
    "kennzeichnung": "",
    # Leer, und das mit Absicht: Die Seitenkarten melden den Zustand
    # eines laufenden Servers. In einer Vorschau haetten sie keinen, den
    # sie melden koennten -- und auf einer veroeffentlichten Seite waere
    # eine Fehlerkarte eine Aussage ueber eine Maschine, die den Leser
    # nichts angeht.
    "befunde": [],
    "bekannte": [],
    # Wohin der Knopf einer Karte zurueckfuehrte. Hier fuehrt nichts
    # zurueck -- aber ohne die Angabe griffe _befunde.html nach
    # "request", und das gibt es in einer Vorschau nicht.
    "hier": "/",
    # WAHR, obwohl hier niemand angemeldet ist -- die Entscheidung ist
    # nicht offensichtlich, deshalb steht sie hier. Mit "falsch" traegt
    # das Band die Kennzeichnung "ohne Kennwort": eine Aussage ueber die
    # Absicherung eines Servers, und zwar eine falsche, denn es gibt
    # keinen. Mit "wahr" steht dort der Knopf "Abmelden" -- der gehoert
    # zu dem, was die Seite zeigen soll, naemlich wie die Oberflaeche
    # aussieht. Er wird weiter unten stillgelegt.
    "anmeldung": True,
    # Die Anhaengsel gegen den Zwischenspeicher des Browsers. Hier
    # stoeren sie nur: Die Dateien liegen daneben und heissen wie sie.
    "stil_version": "",
    "marken_version": "",
    # Leer: Die Fusszeile nennt sonst eine Version, die diese Seite nicht
    # hat. Was sie stattdessen nennen sollte, sagt der Ablauf nicht --
    # lieber keine Angabe als eine erfundene.
    "stand_kurz": "",
}

# "/static/style.css?v=abc" -> "style.css". Gesucht wird mit einem Muster
# und nicht mit einer Liste von Dateinamen: Kommt in base.html ein Bild
# dazu, faellt es hier sonst still hinten runter, und die Vorschau haette
# eine Luecke, die niemand bemerkt.
VERWEIS = re.compile(r"/static/([A-Za-z0-9._-]+)(\?v=[^\"']*)?")

# Die Reiterleiste -- der Block, der stehen bleibt und sein Ziel verliert.
LEISTE = re.compile(r'<div class="reiterleiste">.*?</div>', re.S)

# Der Abmelden-Knopf im Band. Siehe "anmeldung" oben: Er bleibt sichtbar
# und tut nichts. Die Form verliert dabei ``method`` und ``action`` --
# sie stehen in dem, was das Muster wegnimmt --, und der Knopf bekommt
# ``disabled``. Beides ist noetig: Ohne die Form schickte er nach
# /abmelden, ohne ``disabled`` schickte er die leere Form an die Seite
# selbst zurueck. Ein Knopf, der etwas anderes tut als das, was
# draufsteht, ist schlimmer als einer, der nichts tut.
ABMELDEN = re.compile(r'(<form class="abmelden")[^>]*(>)(.*?)(</form>)', re.S)

# Ein Verweis auf diese Seite selbst. Er wird nicht tot, er wird richtig:
# Auf dem Server heisst das Register /hilfe, hier ist es der Seitenanfang.
SELBST = re.compile(r'href="/hilfe(#[A-Za-z0-9_-]+)?"')

# Die beiden Rueckwege am Kopf und Fuss eines Abschnitts: "Zur Karte ->"
# und "Zum Register ->". Sie tragen keinen Inhalt, sie sind der Weg selbst
# -- ohne Ziel bliebe ein Pfeil stehen, der nirgendwohin zeigt. Also weg,
# und zwar der ganze Absatz.
WEGWEISER = re.compile(
    r'\s*<p class="(?:zurkarte|zumregister)">\s*<a\s[^>]*href="/[^"]*"'
    r'[^>]*>.*?</a>\s*</p>', re.S)

# Alles Uebrige, was auf eine Route des Servers zeigt: /sammlung,
# /meilensteine, /einrichtung#export. Der Text bleibt, die Klammer faellt
# -- "steht unter Sammlung" liest sich ohne Verweis genauso.
ROUTE = re.compile(r'<a\s[^>]*href="/[^"]*"[^>]*>(.*?)</a>', re.S)

# Das Stueck, das alle zehn Sekunden die Befunde nachholt. Auf einem
# Server ist es noetig, hier ist es schaedlich -- siehe veroeffentlichen().
NACHHOLEN = re.compile(r'// Die Befunde nachholen\..*?\n\}\)\(\);\n', re.S)

# Wohin die Hinweiszeile kommt: gleich unter die Reiterleiste, vor allem
# anderen. Wer die falsche Seite erwischt hat, soll es lesen, bevor er zu
# lesen anfaengt, und nicht am Fuss von 1800 Zeilen.
MAIN = re.compile(r"<main>")

HINWEIS = (
    '<main>\n'
    '    <p class="hint">Diese Seite zeigt MARLEI Tasks unter '
    '<strong>%s</strong>. '
    'Die Fassung für <a href="%s">%s</a> steht daneben.</p>'
)

# Ein href, das nach der Behandlung noch auf eine Route zeigt -- danach
# sucht die Pruefung.
UEBRIG = re.compile(r'href="/(?!/)[^"]*"')

# Und eine Abfrage, die im Browser des Lesers an einen Server ginge, den
# es nicht gibt.
ABFRAGE = re.compile(r'fetch\(\s*"/')

# Dasselbe fuer ein Formular: Es schickt ab, wohin niemand horcht.
ABSENDEN = re.compile(r'<form(?![^>]*\bdisabled\b)[^>]*action="/')

# Die Kennzeichnung im Band, die sagt, dass dieser Server offen steht.
# Gesucht wird die Marke und nicht die Wortfolge: "ohne Kennwort" steht
# auch im Fliesstext der Hilfe, wo sie genau das erklaert -- dort gehoert
# sie hin.
OFFEN = re.compile(r'class="kennzeichnung"[^>]*>\s*ohne Kennwort')


def veroeffentlichen(html: str, seite: dict) -> str:
    """Die Seite von allem befreien, was einen laufenden Server voraussetzt.

    **Der Grund ist ein Zahlenverhaeltnis.** Die gerenderte Hilfe traegt
    rund 100 Verweise auf Routen dieser Anwendung -- die Reiterleiste,
    jedes "unter *Sammlung*", jeden Sprung in eine Karte. Auf einem Server
    fuehren sie irgendwohin; auf einer veroeffentlichten Seite fuehren sie
    hundertmal ins Leere. Eine Hilfe, in der jeder zweite Verweis stirbt,
    ist schlechter als eine ohne Verweise.

    **Fuenf Faelle, fuenf Antworten** -- und der erste ist der beste:

        /hilfe#lizenz   ist diese Seite selbst    -> #lizenz
        Reiterleiste    zeigt, wie es aussieht    -> bleibt, ohne Ziel
        "Zur Karte ->"  ist nur der Weg           -> faellt ganz weg
        /sammlung       setzt einen Server voraus -> nur noch Text
        Abmelden        gehoert zum Band          -> bleibt, stillgelegt

    **Und ein Verweis, den man nicht sieht.** Jede Seite holt alle zehn
    Sekunden die Befunde nach; auf Pages ist das ein 404, und dessen
    Inhalt landete im Kasten ganz oben -- auf MARLEI Boots
    veroeffentlichter Hilfe stand im September 2026 nach ein paar
    Sekunden *"There isn't a GitHub Pages site here"* im Kopf. Das Stueck
    faellt hier weg: Wo es keinen Server gibt, gibt es auch keinen
    Befund, der sich aendern koennte.

    **Die Reiterleiste bleibt stehen**, weil sie zu dem gehoert, was die
    Seite zeigen soll: So sieht die Oberflaeche aus, neun Register.
    Ohne ``href`` ist sie kein Verweis mehr -- ``nav a`` faerbt sie
    ohnehin gedaempft, sie sieht also aus wie vorher und tut nichts.

    **Im Fliesstext faellt die Klammer dagegen ganz weg.** Ein ``<a>``
    ohne Ziel behielte dort die Verweisfarbe aus
    ``a { color: var(--accent) }`` und saehe aus wie ein Verweis, der
    nicht geht. Das ist schlimmer als gar keiner.

    **Die Hinweiszeile auf die andere Seite kommt hinzu** und steht so in
    keiner Vorlage -- der einzige Zusatz dieses Werkzeugs. Auf dem Server
    waere sie sinnlos: Dort gibt es nur das eine System, auf dem er
    laeuft.
    """
    html = SELBST.sub(lambda t: 'href="%s"' % (t.group(1) or "#"), html)
    html = LEISTE.sub(
        lambda t: re.sub(r'\s+href="/[^"]*"\s*', " ", t.group(0)), html)
    html = ABMELDEN.sub(
        lambda t: t.group(1) + t.group(2)
        + t.group(3).replace("<button", "<button disabled", 1) + t.group(4),
        html)
    html = WEGWEISER.sub("", html)
    html = NACHHOLEN.sub(
        "// Die Befunde werden hier NICHT nachgeholt -- siehe\n"
        "// tools/hilfe-vorschau.py, veroeffentlichen().\n", html)
    html = MAIN.sub(
        HINWEIS % (seite["name"], seite["andere"], seite["andere_name"]),
        html, count=1)
    return ROUTE.sub(r"\1", html)


def pruefe(html: str) -> list:
    """Was auf dieser Seite nichts zu suchen hat.

    **Drei Dinge, und keines faellt von selbst jemandem auf.** Eine
    Seitenkarte meldet den Zustand eines laufenden Servers -- oeffentlich
    waere das eine Aussage ueber eine Maschine, die den Leser nichts
    angeht. Ein uebriggebliebener Verweis auf eine Route ist ein Klick,
    der auf einer fremden Seite im 404 endet. Und ein Formular, das noch
    absendet, ist dasselbe mit einem Knopf davor.

    Gemeldet wird alles als Fehler und nicht als Hinweis: Diese Pruefung
    laeuft in dem Schritt, der die Seite veroeffentlicht, und dort ist ein
    Hinweis dasselbe wie Schweigen.
    """
    klagen = []
    uebrig = sorted(set(UEBRIG.findall(html)))
    if uebrig:
        klagen.append("Verweise auf Routen des Servers: "
                      + ", ".join(uebrig[:5])
                      + (" (und %d weitere)" % (len(uebrig) - 5)
                         if len(uebrig) > 5 else ""))
    if 'class="seitenkarte' in html:
        klagen.append("Eine Seitenkarte steht auf der Seite -- sie meldet "
                      "den Zustand eines laufenden Servers.")
    if ABFRAGE.search(html):
        klagen.append("Die Seite fragt einen Server, den es hier nicht "
                      "gibt -- und traegt dessen Fehlerseite dann selbst.")
    if ABSENDEN.search(html):
        klagen.append("Ein Formular schickt an eine Route ab, die es hier "
                      "nicht gibt.")
    if OFFEN.search(html):
        klagen.append("Im Band steht \"ohne Kennwort\" -- eine Aussage "
                      "ueber die Absicherung eines Servers, den es hier "
                      "nicht gibt.")
    return klagen


def baue(ziel: pathlib.Path, streng: bool = False) -> pathlib.Path:
    # autoescape wie beim Server: FastAPIs Jinja2Templates schaltet es ein.
    # Eine Vorschau, die anders ausgibt als das Original, ist keine.
    umgebung = Environment(loader=FileSystemLoader(str(WEBUI / "templates")),
                           autoescape=True)
    vorlage = umgebung.get_template("hilfe.html")

    ziel.mkdir(parents=True, exist_ok=True)
    gebraucht = set()
    klagen = []

    for seite in SEITEN:
        html = vorlage.render(windows=seite["windows"], **BEISPIEL)
        gebraucht.update(VERWEIS.findall(html))
        html = VERWEIS.sub(r"\1", html)
        html = veroeffentlichen(html, seite)

        for klage in pruefe(html):
            klagen.append("%s: %s" % (seite["datei"], klage))

        (ziel / seite["datei"]).write_text(html, encoding="utf-8")
        print("%s -- %d Zeichen (%s)"
              % (ziel / seite["datei"], len(html), seite["name"]))

    for klage in klagen:
        print("NICHT IN ORDNUNG: " + klage)
    if klagen and streng:
        raise SystemExit(1)

    fehlend = []
    for name, _ in sorted(gebraucht):
        quelle = STATISCH / name
        if quelle.exists():
            shutil.copy2(quelle, ziel / name)
        else:
            fehlend.append(name)
    if fehlend:
        # Kein Abbruch: Eine Vorschau ohne Symbol ist brauchbar, eine
        # Vorschau, die gar nicht erst entsteht, nicht. Gesagt werden
        # muss es trotzdem.
        print("Nicht gefunden in webui/static: " + ", ".join(fehlend))

    print("%d Datei(en) daneben" % (len(gebraucht) - len(fehlend)))
    return ziel / "index.html"


if __name__ == "__main__":
    # --streng bricht ab, wenn die Pruefung etwas findet. Beim Bearbeiten
    # waere das laestig; in dem Schritt, der veroeffentlicht, ist es der
    # ganze Zweck.
    ordner = [a for a in sys.argv[1:] if not a.startswith("--")]
    baue(pathlib.Path(ordner[0]) if ordner else WURZEL / "build" / "hilfe",
         streng="--streng" in sys.argv)
