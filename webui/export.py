"""
Der Ausgang: aus der Ablage werden Textdateien.

**Warum es ihn gibt, und zwar dreimal.** `docs/datenhaltung.md`, Abschnitt 8,
gibt eine Zusage: *Der Ausgang bleibt Text* -- was heute eine Mappe aus
Markdown-Dateien leistet, lesbar ohne dieses Werkzeug und gesichert durch
Kopieren, muss der Export leisten. Dazu kam die erste der beiden
Sicherungen vor dem Zuruecksetzen. Und seit dem 07.09.2026 ein dritter
Zweck, der die Anforderungen veraendert: **Tasks gibt nach
`marlei-internal` aus**, ein privates Repository -- damit wird der Export
der Weg, auf dem der Bestand eine Versionsgeschichte bekommt.

**Daraus folgt die eine Anforderung, die man leicht verfehlt: Die Ausgabe
muss STABIL sein.** Bei unveraendertem Bestand byteweise dieselbe. Kein
Zeitstempel im Kopf, feste Sortierung, gleiche Formatierung -- sonst
erzeugt jeder Lauf einen Unterschied ueber alles, und die
Versionsgeschichte im Repository sagt nichts mehr.

**Ausgegeben wird das gewaehlte Projekt**, nicht alle auf einmal (so
entschieden im September 2026). Die Vorauswahl aus dem Reiter Projekte
gilt fuer Sammlung, Aufgaben, Meilensteine und Entscheidungen; sie gilt
hier genauso. Ein *alle auf einmal* waere die zweite Ausnahme neben den
Befunden.

**Geschrieben wird, nicht committet.** Was im Repository landet,
entscheidet, wer dort `git commit` tippt. Diese Anwendung fasst kein Git
an -- dieselbe Grenze wie bei der Firewall und der Netzkonfiguration.
"""

from __future__ import annotations

import io
import os
import re
import unicodedata
import zipfile
from pathlib import Path

import datenbank

# Wohin ausgegeben wird. Leer heisst: Es ist keiner eingerichtet -- dann
# sagt die Karte das, statt irgendwohin zu schreiben.
#
# **None und nicht Path("")**, und das ist kein Stilfrage: ``Path("")``
# ist ``Path(".")`` und damit WAHR. Ein leeres MARLEI_EXPORT haette so
# als eingerichtet gegolten, und der Export schriebe ins
# Arbeitsverzeichnis des Dienstes -- lautlos und an einer Stelle, an der
# niemand danach sucht.
ZIEL = Path(os.environ["MARLEI_EXPORT"]) \
    if os.environ.get("MARLEI_EXPORT", "").strip() else None


def _ziel(ziel: Path | None) -> Path | None:
    """Welches Verzeichnis gilt -- das uebergebene oder das eingerichtete.

    Ein leerer Pfad zaehlt als keiner. Siehe ``ZIEL``: Auch ``Path("")``
    und ``Path(".")`` sind hier kein Ziel, sondern ein Versehen.
    """
    wohin = ZIEL if ziel is None else ziel
    if wohin is None or str(wohin).strip() in ("", "."):
        return None
    return Path(wohin)

# Die fuenf Dateien, in dieser Reihenfolge. Sie steht hier und nicht in
# der Vorlage: Die Reihenfolge ist Teil der Stabilitaetszusage.
DATEIEN = ("projekt.md", "sammlung.md", "aufgaben.md", "meilensteine.md",
           "entscheidungen.md")

_UNSAUBER = re.compile(r"[^a-z0-9]+")


def verzeichnisname(projekt: dict) -> str:
    """``P-001-marlei-boot`` -- Kennung voran, Name dahinter.

    **Die Kennung steht vorn, weil sie sich nie aendert.** Wer ein
    Projekt umbenennt, bekaeme sonst ein zweites Verzeichnis daneben, und
    im Repository saehe das aus wie ein neues Projekt statt wie ein
    umbenanntes. Mit der Kennung vorn faellt beim Umbenennen auf, was
    zusammengehoert.
    """
    # ERST UMSCHREIBEN, DANN ZERLEGEN -- die Reihenfolge ist der ganze
    # Punkt. NFKD macht aus "ö" ein "o" mit angehaengtem Zeichen; wer
    # danach nach "ö" sucht, findet nichts mehr, und aus "Völlig" wird
    # "vollig" statt "voellig". Im Deutschen ist das keine Kleinigkeit:
    # Der Ordnername steht in einem Repository und wird gelesen.
    roh = projekt["name"].lower()
    for davor, danach in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"),
                          ("ß", "ss")):
        roh = roh.replace(davor, danach)
    # Alles Uebrige -- franzoesische Akzente, skandinavische Zeichen --
    # verliert hier seine Zutat. Dafuer ist NFKD da, und dafuer taugt es.
    roh = unicodedata.normalize("NFKD", roh)
    roh = "".join(z for z in roh if not unicodedata.combining(z))
    kurz = _UNSAUBER.sub("-", roh).strip("-")[:40]
    return "%s-%s" % (projekt["kennung"], kurz) if kurz else projekt["kennung"]


def _absatz(ueberschrift: str, text: str) -> list[str]:
    """Ein Abschnitt -- oder nichts, wenn nichts drinsteht.

    **Ein leerer Abschnitt ist keine Auskunft.** In der Mappe steht dort
    ein Strich, weil eine fehlende Zeile wie ein Versehen aussieht; hier
    faellt er weg, denn die Datei wird als Ganzes gelesen und nicht als
    Formular abgehakt.
    """
    inhalt = (text or "").strip()
    return ["## %s" % ueberschrift, "", inhalt, ""] if inhalt else []


def _liste(ueberschrift: str, punkte: list[str]) -> list[str]:
    return ([ "## %s" % ueberschrift, ""] + ["- %s" % p for p in punkte]
            + [""]) if punkte else []


def _projekt_datei(projekt: dict) -> str:
    zeilen = ["# %s %s" % (projekt["kennung"], projekt["name"]), "",
              "*Zustand: %s · Eingetragen am %s*"
              % (projekt["zustand"], projekt["eingetragen_deutsch"]), ""]
    zeilen += _absatz("Beschreibung", projekt["beschreibung"])
    zeilen += _absatz("Vision", projekt["vision"])
    zeilen += _liste("Bereiche", [b["wert"] for b in projekt["bereiche"]])
    return "\n".join(zeilen).rstrip() + "\n"


def _sammlung_datei(conn, projekt: dict) -> str:
    zeilen = ["# Sammlung — %s" % projekt["name"], "",
              "*Was aufgefallen ist. Offene und abgeschlossene Einträge, "
              "nach Kennung.*", ""]
    for t in sorted(datenbank.topics(conn, projekt["id"], offen_nur=False),
                    key=lambda x: x["id"]):
        zeilen += ["## %s %s" % (t["kennung"], t["titel"]), "",
                   "*%s · %s · Priorität %s · Eingetragen am %s%s*"
                   % (t["kategorie"], t["bereich"], t["prio"],
                      t["eingetragen_deutsch"],
                      "" if t["abschluss"] == datenbank.STRICH
                      else " · Abschluss: %s am %s"
                           % (t["abschluss"],
                              datenbank.datum_zeigen(t["abschluss_am"]))), ""]
        if t["beschreibung"].strip():
            zeilen += ["### Beschreibung", "",
                       t["beschreibung"].strip(), ""]
        if t["schaerfen"].strip():
            zeilen += ["### Beim Schärfen", "", t["schaerfen"].strip(), ""]
        if t["kategorie"] == "FEHLER":
            for spalte, aufschrift in datenbank.FEHLERANGABEN:
                if t[spalte].strip():
                    zeilen += ["### %s" % aufschrift, "", t[spalte].strip(), ""]
        if t["ursprung"].strip():
            zeilen += ["*Ursprung: %s*" % t["ursprung"].strip(), ""]
    return "\n".join(zeilen).rstrip() + "\n"


def _aufgaben_datei(conn, projekt: dict) -> str:
    zeilen = ["# Aufgaben — %s" % projekt["name"], "",
              "*Woran gearbeitet wird. Nach Kennung.*", ""]
    for a in sorted(datenbank.aufgaben(conn, projekt["id"], offen_nur=False),
                    key=lambda x: x["id"]):
        kopf = ("*%s · Priorität %s · Status %s%s · Eingetragen am %s%s*"
                % (a["bereich"], a["prio"], a["status"],
                   "" if a["status_seit"] == datenbank.STRICH
                   else " seit %s" % a["seit_deutsch"],
                   a["eingetragen_deutsch"],
                   "" if a["abschluss"] == datenbank.STRICH
                   else " · Abschluss: %s am %s"
                        % (a["abschluss"],
                           datenbank.datum_zeigen(a["abschluss_am"]))))
        zeilen += ["## %s %s" % (a["kennung"], a["titel"]), "", kopf, ""]
        if a["ursprung"]:
            zeilen += ["*Ursprung: %s*"
                       % " · ".join("%s %s" % (u["kennung"], u["titel"])
                                    for u in a["ursprung"]), ""]
        if a["meilenstein"]:
            zeilen += ["*Meilenstein: %s %s*"
                       % (a["meilenstein"]["kennung"],
                          a["meilenstein"]["benennung"]), ""]
        for titel, feld in (("Was dahintersteckt", "dahinter"),
                            ("Was bedacht werden muss", "bedacht"),
                            ("Was ist das Ergebnis", "ergebnis")):
            if a[feld].strip():
                zeilen += ["### %s" % titel, "", a[feld].strip(), ""]
        for titel, punkte in (("Was getan werden muss", a["arbeit"]),
                              ("Wann es abgenommen ist", a["abnahme"])):
            if punkte:
                zeilen += ["### %s" % titel, ""]
                for p in punkte:
                    zeilen.append(
                        "- [%s] %s%s"
                        % ("x" if p["erledigt"] else " ", p["text"],
                           " *(erledigt am %s)*" % p["erledigt_deutsch"]
                           if p["erledigt"] else ""))
                zeilen.append("")
    return "\n".join(zeilen).rstrip() + "\n"


def _meilensteine_datei(conn, projekt: dict) -> str:
    zeilen = ["# Meilensteine — %s" % projekt["name"], "",
              "*Was zusammen fertig werden muss. Nach Kennung.*", ""]
    for m in sorted(datenbank.meilensteine(conn, projekt["id"],
                                           offen_nur=False),
                    key=lambda x: x["id"]):
        zeilen += ["## %s %s" % (m["kennung"], m["benennung"]), "",
                   "*Priorität %s · Eingetragen am %s%s*"
                   % (m["prio"], m["eingetragen_deutsch"],
                      "" if m["abschluss"] == datenbank.STRICH
                      else " · Abschluss: %s am %s"
                           % (m["abschluss"],
                              datenbank.datum_zeigen(m["abschluss_am"]))), ""]
        if m["vorgaenger"]:
            zeilen += ["*Hängt ab von: %s*"
                       % " · ".join("%s %s" % (v["kennung"], v["benennung"])
                                    for v in m["vorgaenger"]), ""]
        for titel, feld in (("Beschreibung", "beschreibung"),
                            ("Bedingung", "bedingung"),
                            ("Abnahme erfolgt", "abnahme_kriterium"),
                            ("Nachbereitung", "nachbereitung")):
            if m[feld].strip() and m[feld].strip() != datenbank.STRICH:
                zeilen += ["### %s" % titel, "", m[feld].strip(), ""]
        if m["aufgaben"]:
            zeilen += ["### Aufgaben", ""]
            for a in m["aufgaben"]:
                zeilen.append("- [%s] %s %s"
                              % ("x" if a["fertig"] else " ", a["kennung"],
                                 a["titel"]))
            zeilen.append("")
        if m["dazwischen"]:
            zeilen += ["### Was dazwischenkam", ""]
            for d in m["dazwischen"]:
                zeilen.append("- *%s* %s" % (d["datum_deutsch"], d["text"]))
            zeilen.append("")
    return "\n".join(zeilen).rstrip() + "\n"


def _entscheidungen_datei(conn, projekt: dict) -> str:
    zeilen = ["# Entscheidungen — %s" % projekt["name"], "",
              "*Warum es so ist. Nach Kennung.*", ""]
    for e in sorted(datenbank.entscheidungen(conn, projekt["id"]),
                    key=lambda x: x["id"]):
        zeilen += ["## %s %s" % (e["kennung"], e["titel"]), "",
                   "*%s · %s%s*"
                   % (e["zustand"], e["datum_deutsch"],
                      " · Bezug: %s %s" % (e["bezug"]["kennung"],
                                           e["bezug"]["titel"])
                      if e["bezug"] else ""), ""]
        if e["entschluss"].strip():
            zeilen += ["### Was entschieden wurde", "",
                       e["entschluss"].strip(), ""]
        if e["text"].strip():
            zeilen += ["### Der Verlauf", "", e["text"].strip(), ""]
    return "\n".join(zeilen).rstrip() + "\n"


def _nur_lf(text: str) -> str:
    r"""Zeilenumbrueche vereinheitlichen -- die Ausgabe ist LF.

    **Nicht Kosmetik, sondern Teil der Zusage.** Was in der Ablage steht,
    kommt teils aus Formularfeldern, und ein Browser schickt darin
    CRLF. Ohne diese Zeile traegt die Ausgabe gemischte Umbrueche: In
    derselben Datei stuenden LF (was der Export selbst setzt) und CRLF
    (was im Feld stand).

    Aufgefallen am 07.09.2026 beim ersten Export in ein Repository --
    Git meldete beim Hinzufuegen, es werde beim Auschecken umschreiben.
    **Damit waere die Stabilitaetszusage genau dort gebrochen, wo sie
    gebraucht wird:** Ein ausgecheckter Stand saehe nach dem naechsten
    Export in jeder Zeile geaendert aus, und "git diff" zeigte nicht
    mehr, was sich am Bestand geaendert hat.

    Nur beim Ausgeben, nicht beim Speichern: Was jemand eingetippt hat,
    bleibt in der Ablage, wie es ankam.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def dateien(conn, projekt: dict) -> dict[str, str]:
    """Was ausgegeben wuerde -- als Text, ohne etwas zu schreiben.

    **Diese Funktion ist der Kern der Stabilitaetszusage.** Sie haengt
    an nichts als der Ablage: kein Zeitpunkt, kein Zufall, keine
    Umgebung. Zweimal aufgerufen bei unveraendertem Bestand liefert sie
    zweimal dieselben Zeichen -- und genau daran wird auch geprueft, ob
    die Ausgabe auf der Platte noch aktuell ist.
    """
    return {name: _nur_lf(mach(conn, projekt) if mit_conn else mach(projekt))
            for name, mach, mit_conn in (
                ("projekt.md", _projekt_datei, False),
                ("sammlung.md", _sammlung_datei, True),
                ("aufgaben.md", _aufgaben_datei, True),
                ("meilensteine.md", _meilensteine_datei, True),
                ("entscheidungen.md", _entscheidungen_datei, True))}


def ort(ziel: Path | None = None) -> dict:
    """Der Ausgang selbst -- ohne Projekt.

    **Die Karte *Ablageorte* fragt nach dem ORT**, nicht nach einem
    Projekt darin: ob er eingerichtet ist und ob dorthin geschrieben
    werden kann. Das gilt auch, wenn gerade kein Projekt gewaehlt ist --
    ``stand()`` braucht eines und kann diese Frage deshalb nicht
    beantworten.

    Aufgefallen am 07.09.2026 auf dev-marlei, an der ersten echten
    Installation: Dort stand unter Ablageorte *"MARLEI_EXPORT ist leer"*,
    waehrend zwei Karten weiter unten der Pfad danebenstand. **Eine
    Karte, die einen Grund nennt, den es nicht gibt, ist schlimmer als
    eine, die schweigt.**
    """
    wohin = _ziel(ziel)
    if wohin is None:
        return {"eingerichtet": False, "pfad": "", "beschreibbar": False}
    # Beschreibbar heisst hier dasselbe wie in stand(): Das Verzeichnis
    # gibt es und es laesst sich beschreiben -- oder es gibt es noch
    # nicht, aber sein Elternteil laesst sich beschreiben. Ein Ordner,
    # den der erste Lauf anlegt, ist kein Fehler.
    pruefen = wohin if wohin.is_dir() else wohin.parent
    return {"eingerichtet": True, "pfad": str(wohin),
            "beschreibbar": pruefen.is_dir() and os.access(pruefen, os.W_OK)}


# Ein fester Zeitstempel fuer alles im Paket.
#
# **Die Stabilitaetszusage gilt auch hier.** Ein ZIP traegt zu jeder
# Datei eine Uhrzeit; nimmt es die echte, waeren zwei Pakete desselben
# Bestands byteweise verschieden -- und die Zusage waere an der Stelle
# gebrochen, an der man sie am ehesten pruefen kann. 1980 ist der
# frueheste Zeitpunkt, den das ZIP-Format kennt, und damit der einzige,
# der nichts behauptet.
ZIP_ZEIT = (1980, 1, 1, 0, 0, 0)


def als_zip(conn, projekt: dict) -> bytes:
    """Derselbe Ausgang als Paket -- ohne die Platte anzufassen.

    **Der Weg an den Bestand, der keine Shell braucht.** ``dateien()``
    baut die Texte ohnehin im Speicher, bevor ``schreiben()`` sie
    hinlegt; hier wird nur der zweite Schritt durch einen Download
    ersetzt.

    Deshalb haengt er auch **nicht** an MARLEI_EXPORT: Wo kein Ausgang
    eingerichtet ist, gibt es trotzdem etwas herunterzuladen. Und er
    ruehrt den eingerichteten nicht an -- *Stand der Ausgabe* bleibt, was
    er war.
    """
    ordner = verzeichnisname(projekt)
    puffer = io.BytesIO()
    # ZIP_DEFLATED, damit aus 300 KB Text ein Paket wird, das man
    # verschickt. Ohne zusaetzliche Abhaengigkeit: zipfile steht in der
    # Standardbibliothek.
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as paket:
        for name in DATEIEN:
            eintrag = zipfile.ZipInfo("%s/%s" % (ordner, name), ZIP_ZEIT)
            eintrag.compress_type = zipfile.ZIP_DEFLATED
            # 0644, damit die Dateien beim Auspacken unter Linux nicht
            # als ausfuehrbar landen.
            eintrag.external_attr = 0o644 << 16
            paket.writestr(eintrag, dateien(conn, projekt)[name])
    return puffer.getvalue()


def stand(projekt: dict, ziel: Path | None = None) -> dict:
    """Was von diesem Projekt auf der Platte liegt.

    Gibt zurueck, wohin geschrieben wuerde, ob das ueberhaupt geht, und
    was dort steht -- Dateien, Groesse, juengste Aenderung.
    """
    wohin = _ziel(ziel)
    if wohin is None:
        return {"eingerichtet": False, "pfad": "", "ordner": "",
                "beschreibbar": False, "dateien": 0, "bytes": 0, "am": ""}
    ordner = wohin / verzeichnisname(projekt)
    vorhanden = [ordner / n for n in DATEIEN if (ordner / n).is_file()]
    # Beschreibbar heisst: Das Zielverzeichnis existiert und laesst sich
    # beschreiben -- oder es existiert noch nicht, aber sein Elternteil
    # tut es. Ein Ordner, den der erste Lauf anlegt, ist kein Fehler.
    pruefen = ordner if ordner.is_dir() else Path(wohin)
    return {
        "eingerichtet": True,
        "pfad": str(wohin),
        "ordner": str(ordner),
        "beschreibbar": pruefen.is_dir() and os.access(pruefen, os.W_OK),
        "dateien": len(vorhanden),
        "bytes": sum(d.stat().st_size for d in vorhanden),
        "am": max((d.stat().st_mtime for d in vorhanden), default=0),
    }


def aktuell(conn, projekt: dict, ziel: Path | None = None) -> list[str]:
    """Welche Dateien anders auf der Platte stehen, als sie stehen wuerden.

    **Verglichen wird der Inhalt, nicht ein Zaehler.** Ein Buchhalter
    ueber geaenderte Eintraege waere eine zweite Wahrheit neben der
    Ablage -- und damit eine, die falsch sein kann. Der Vergleich hier
    kann es nicht: Er baut aus, was ausgegeben wuerde, und haelt es
    daneben.

    Leere Liste heisst: Die Ausgabe ist aktuell.
    """
    wohin = _ziel(ziel)
    if wohin is None:
        return list(DATEIEN)
    ordner = wohin / verzeichnisname(projekt)
    soll = dateien(conn, projekt)
    anders = []
    for name in DATEIEN:
        pfad = ordner / name
        try:
            ist = pfad.read_text(encoding="utf-8")
        except OSError:
            anders.append(name)
            continue
        if ist != soll[name]:
            anders.append(name)
    return anders


def schreiben(conn, projekt: dict, ziel: Path | None = None) -> dict:
    """Ausgeben. Gibt zurueck, was geschrieben wurde.

    **Geschrieben wird immer alles**, auch das Unveraenderte: Eine Datei
    mit gleichem Inhalt neu zu schreiben aendert im Repository nichts --
    sie zu ueberspringen aber hiesse, dass ein von Hand veraenderter Text
    stehen bliebe. Die Ausgabe ist der Stand der Ablage, nicht ihre
    Ergaenzung.
    """
    wohin = _ziel(ziel)
    if wohin is None:
        raise ValueError(
            "Es ist kein Zielverzeichnis eingerichtet. MARLEI_EXPORT sagt, "
            "wohin ausgegeben wird.")
    ordner = wohin / verzeichnisname(projekt)
    ordner.mkdir(parents=True, exist_ok=True)
    inhalt = dateien(conn, projekt)
    for name in DATEIEN:
        # newline="\n" ausdruecklich: Sonst schriebe Windows CRLF, und
        # dieselbe Ablage ergaebe auf zwei Maschinen zwei Ausgaben.
        (ordner / name).write_text(inhalt[name], encoding="utf-8",
                                   newline="\n")
    return {"ordner": str(ordner), "dateien": len(DATEIEN),
            "bytes": sum(len(t.encode("utf-8")) for t in inhalt.values())}
