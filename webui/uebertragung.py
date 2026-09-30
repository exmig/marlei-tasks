"""
Daten uebertragen: Projekte als eine Datei hinaus und wieder herein.

**Nicht der Export.** Der Export schreibt Text fuer Menschen und fuer ein
Repository; eingelesen werden kann er nicht. Diese Datei ist fuer die
andere Installation -- einen zweiten Rechner, eine frische Maschine nach
einem Umzug. Sie traegt jede Spalte, auch die, die keine Karte zeigt.

**Ausgewaehlt werden die Projekte hier, nicht vorausgewaehlt.** Die
Vorauswahl aus dem Reiter Projekte gilt sonst ueberall, auch im Export.
Hier nicht: Wer umzieht, zieht mit allem um, und ein Knopf je Projekt
waere ein Umzug in Raten (so entschieden im September 2026 -- die
zweite Ausnahme neben den Befunden).

**Eingelesen wird immer als neues Projekt.** Nichts wird ueberschrieben.
Die Kennungen sind die Nummern der Ablage und gelten ueber alle Projekte
hinweg; in einer anderen Installation sind sie meist schon vergeben.
Jeder Eintrag bekommt deshalb eine neue Nummer, und jeder Verweis wird
mitgezogen -- auch einer, der im Text steht: Wer in einer Aufgabe
"siehe B-065" geschrieben hat, meint danach denselben Eintrag unter
seiner neuen Kennung.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime

import datenbank

FORMAT = "marlei-tasks-daten"
VERSION = 1

# Die Tabellen eines Projekts, in der Reihenfolge, in der sie eingelesen
# werden. **Die Reihenfolge ist der Punkt:** Eine Zeile kann erst
# eingelesen werden, wenn es das gibt, worauf sie zeigt. Die Meilensteine
# stehen deshalb vor den Aufgaben -- eine Aufgabe zeigt auf ihren Stein,
# nicht umgekehrt.
#
# Je Tabelle: welche Spalte auf welche Tabelle zeigt. Die Spalte zum
# Projekt steht nicht dabei, sie wird immer gesetzt.
TABELLEN: dict[str, dict[str, str]] = {
    "bereiche": {},
    "topics": {"bereich_id": "bereiche"},
    "meilensteine": {},
    "aufgaben": {"bereich_id": "bereiche", "meilenstein_id": "meilensteine"},
    "aufgabe_punkte": {"aufgabe_id": "aufgaben"},
    "aufgabe_ursprung": {"aufgabe_id": "aufgaben", "topic_id": "topics"},
    "meilenstein_vorgaenger": {"meilenstein_id": "meilensteine",
                               "vorgaenger_id": "meilensteine"},
    "meilenstein_ursprung": {"meilenstein_id": "meilensteine",
                             "aufgabe_id": "aufgaben"},
    "meilenstein_dazwischen": {"meilenstein_id": "meilensteine"},
    "entscheidungen": {},
}

# Wie eine Tabelle an ihr Projekt kommt, wenn sie keine Spalte dafuer hat.
_ZUM_PROJEKT = {
    "aufgabe_punkte": ("aufgabe_id", "aufgaben"),
    "aufgabe_ursprung": ("aufgabe_id", "aufgaben"),
    "meilenstein_vorgaenger": ("meilenstein_id", "meilensteine"),
    "meilenstein_ursprung": ("meilenstein_id", "meilensteine"),
    "meilenstein_dazwischen": ("meilenstein_id", "meilensteine"),
}

# Die Entscheidung zeigt ueber zwei Spalten -- Art und Nummer.
_BEZUG = {"B": "topics", "A": "aufgaben", "M": "meilensteine"}

# Welcher Buchstabe zu welcher Tabelle gehoert, umgekehrt.
_ART = {t: a for a, t in datenbank.ARTEN.items()}

_KENNUNG = re.compile(r"\b([PBAME])-(\d{3,})\b")


class UebertragungsFehler(Exception):
    """Die Datei taugt nicht -- mit dem Satz, den die Karte zeigt."""


# ==================================================================== #
# Hinaus
# ==================================================================== #

def _zeilen(conn: sqlite3.Connection, sql: str, *werte) -> list[dict]:
    return [dict(z) for z in conn.execute(sql, werte)]


def _projekt_heraus(conn: sqlite3.Connection, projekt_id: int) -> dict:
    """Ein Projekt mit allem, was daranhaengt -- Spalte fuer Spalte.

    ``SELECT *`` mit Absicht: Kommt eine Spalte hinzu, geht sie mit,
    ohne dass hier jemand daran denken muss.
    """
    kopf = _zeilen(conn, "SELECT * FROM projekte WHERE id = ?", projekt_id)
    if not kopf:
        raise UebertragungsFehler("Dieses Projekt gibt es nicht.")
    tabellen = {}
    for t in TABELLEN:
        if t in _ZUM_PROJEKT:
            spalte, eltern = _ZUM_PROJEKT[t]
            sql = ('SELECT x.* FROM "%s" x JOIN "%s" e ON e.id = x.%s '
                   "WHERE e.projekt_id = ? ORDER BY x.rowid"
                   % (t, eltern, spalte))
        else:
            sql = 'SELECT * FROM "%s" WHERE projekt_id = ? ORDER BY id' % t
        tabellen[t] = _zeilen(conn, sql, projekt_id)
    return {"projekt": kopf[0], "tabellen": tabellen}


def exportieren(conn: sqlite3.Connection, projekt_ids: list[int],
                programm: str = "") -> dict:
    """Die gewaehlten Projekte als ein Dokument."""
    return {
        "format": FORMAT,
        "version": VERSION,
        "programm": programm,
        "exportiert_am": datetime.now().isoformat(timespec="seconds"),
        "projekte": [_projekt_heraus(conn, i) for i in projekt_ids],
    }


def als_json(daten: dict) -> bytes:
    return json.dumps(daten, ensure_ascii=False, indent=1).encode("utf-8")


# ==================================================================== #
# Herein
# ==================================================================== #

def lesen(roh: bytes) -> dict:
    """Die hochgeladene Datei pruefen, bevor irgendetwas geschrieben wird.

    **Abgewiesen wird, was eine neuere Fassung geschrieben hat** -- dann
    naemlich, wenn eine Spalte darin steht, die diese Ablage nicht
    kennt. Sie stillschweigend wegzulassen hiesse, beim Umzug etwas zu
    verlieren, ohne dass es jemand merkt.
    """
    try:
        daten = json.loads(roh.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise UebertragungsFehler(
            "Das ist keine Datei aus »Daten übertragen« — sie lässt sich "
            "nicht als JSON lesen.")
    if not isinstance(daten, dict) or daten.get("format") != FORMAT:
        raise UebertragungsFehler(
            "Das ist keine Datei aus »Daten übertragen« von MARLEI Tasks.")
    if not isinstance(daten.get("version"), int) or daten["version"] > VERSION:
        raise UebertragungsFehler(
            "Die Datei stammt aus einer neueren Fassung von MARLEI Tasks. "
            "Erst hier aktualisieren, dann einlesen.")
    projekte = daten.get("projekte")
    if not isinstance(projekte, list) or not projekte:
        raise UebertragungsFehler("In der Datei steht kein Projekt.")
    for p in projekte:
        if (not isinstance(p, dict) or not isinstance(p.get("projekt"), dict)
                or not isinstance(p.get("tabellen"), dict)
                or not str(p["projekt"].get("name", "")).strip()):
            raise UebertragungsFehler("Die Datei ist unvollständig.")
    return daten


def vorschau(daten: dict) -> list[dict]:
    """Was in der Datei steht -- je Projekt Name und Zahlen."""
    raus = []
    for i, p in enumerate(daten["projekte"]):
        t = p["tabellen"]
        raus.append({
            "nummer": i,
            "kennung": datenbank.kennung("P", int(p["projekt"].get("id", 0))),
            "name": p["projekt"]["name"],
            "sammlung": len(t.get("topics", [])),
            "aufgaben": len(t.get("aufgaben", [])),
            "meilensteine": len(t.get("meilensteine", [])),
            "entscheidungen": len(t.get("entscheidungen", [])),
        })
    return raus


def _spalten(conn: sqlite3.Connection, tabelle: str) -> set[str]:
    return {z[1] for z in conn.execute('PRAGMA table_info("%s")' % tabelle)}


def _freier_name(conn: sqlite3.Connection, name: str) -> str:
    """Der Projektname ist eindeutig -- er ist das Losungswort der
    Werkseinstellung. Gibt es ihn schon, bekommt der neue einen Zusatz,
    statt dass der Import scheitert."""
    kandidat, n = name, 1
    while conn.execute("SELECT 1 FROM projekte WHERE name = ?",
                       (kandidat,)).fetchone():
        kandidat = ("%s (übernommen)" % name if n == 1
                    else "%s (übernommen %d)" % (name, n))
        n += 1
    return kandidat


def _pruefen(conn: sqlite3.Connection, p: dict) -> None:
    """Kennt diese Ablage jede Spalte der Datei?"""
    unbekannt = set(p["projekt"]) - _spalten(conn, "projekte")
    for t, zeilen in p["tabellen"].items():
        if t not in TABELLEN:
            raise UebertragungsFehler(
                "Die Datei kennt eine Tabelle, die es hier nicht gibt (%s). "
                "Sie stammt vermutlich aus einer neueren Fassung." % t)
        vorhanden = _spalten(conn, t)
        for z in zeilen:
            unbekannt |= {"%s.%s" % (t, s) for s in z if s not in vorhanden}
    if unbekannt:
        raise UebertragungsFehler(
            "Die Datei kennt Felder, die es hier nicht gibt (%s). Sie "
            "stammt aus einer neueren Fassung — erst hier aktualisieren, "
            "dann einlesen." % ", ".join(sorted(unbekannt)[:5]))


def _einfuegen(conn: sqlite3.Connection, tabelle: str, zeile: dict) -> int:
    namen = list(zeile)
    cur = conn.execute(
        'INSERT INTO "%s" (%s) VALUES (%s)'
        % (tabelle, ", ".join('"%s"' % n for n in namen),
           ", ".join("?" for _ in namen)),
        [zeile[n] for n in namen])
    return cur.lastrowid


def _projekt_herein(conn: sqlite3.Connection, p: dict) -> dict:
    """Ein Projekt als neues anlegen. Gibt zurueck, wie es jetzt heisst.

    Hier nur die Zeilen -- und dabei merken, welche alte Nummer welche
    neue geworden ist. Die Texte kommen danach, in
    ``_kennungen_umschreiben``: Erst wenn alle neuen Nummern feststehen,
    laesst sich "B-065" im Text einer Aufgabe umschreiben -- der Eintrag,
    auf den es zeigt, kann nach ihr kommen.
    """
    neu: dict[str, dict[int, int]] = {t: {} for t in
                                      ("projekte", *TABELLEN)}
    texte: list[tuple[str, int]] = []

    kopf = {k: v for k, v in p["projekt"].items() if k != "id"}
    alt_name = kopf["name"]
    kopf["name"] = _freier_name(conn, alt_name)
    pid = _einfuegen(conn, "projekte", kopf)
    neu["projekte"][int(p["projekt"]["id"])] = pid
    texte.append(("projekte", pid))

    for t, verweise in TABELLEN.items():
        for z in p["tabellen"].get(t, []):
            zeile = dict(z)
            alt_id = zeile.pop("id", None)
            if "projekt_id" in zeile:
                zeile["projekt_id"] = pid
            for spalte, ziel in verweise.items():
                if zeile.get(spalte) is None:
                    continue
                try:
                    zeile[spalte] = neu[ziel][int(zeile[spalte])]
                except KeyError:
                    raise UebertragungsFehler(
                        "Die Datei ist in sich nicht stimmig: %s.%s zeigt "
                        "auf einen Eintrag, der nicht darin steht."
                        % (t, spalte))
            if t == "entscheidungen" and zeile.get("bezug_id") is not None:
                ziel = _BEZUG.get(zeile.get("bezug_art"))
                alt = int(zeile["bezug_id"])
                if ziel and alt in neu[ziel]:
                    zeile["bezug_id"] = neu[ziel][alt]
                else:
                    # Der Bezug zeigte schon beim Hinausgeben ins Leere --
                    # die Entscheidung ueberlebt, was sie betraf. Dann
                    # steht sie hier freistehend, statt zu scheitern.
                    zeile["bezug_art"], zeile["bezug_id"] = datenbank.STRICH, None
            neue_id = _einfuegen(conn, t, zeile)
            if alt_id is not None:
                neu[t][int(alt_id)] = neue_id
                texte.append((t, neue_id))

    return {"id": pid, "kennung": datenbank.kennung("P", pid),
            "name": kopf["name"], "alt_name": alt_name,
            "alt_kennung": datenbank.kennung("P", int(p["projekt"]["id"])),
            "neu": neu, "texte": texte}


def _kennungen_umschreiben(conn: sqlite3.Connection,
                           eingelesen: list[dict]) -> None:
    """Jede alte Kennung im Text durch ihre neue ersetzen.

    **Ueber alle eingelesenen Projekte zusammen**: Zeigt eine Aufgabe des
    einen auf eine Entscheidung des anderen, stimmt der Verweis danach
    auch. Was auf einen Eintrag zeigt, der nicht in der Datei stand,
    bleibt, wie es war -- es meint etwas, das hier nicht angekommen ist.
    """
    umschreiben = {}
    for e in eingelesen:
        for t, zuordnung in e["neu"].items():
            art = _ART.get(t)
            if art:
                for alt, jetzt in zuordnung.items():
                    umschreiben[(art, alt)] = datenbank.kennung(art, jetzt)

    def ersetzen(treffer: re.Match) -> str:
        return umschreiben.get((treffer.group(1), int(treffer.group(2))),
                               treffer.group(0))

    for e in eingelesen:
        for t, zeilen_id in e["texte"]:
            zeile = conn.execute('SELECT * FROM "%s" WHERE id = ?' % t,
                                 (zeilen_id,)).fetchone()
            aenderung = {}
            for spalte in zeile.keys():
                wert = zeile[spalte]
                if isinstance(wert, str) and _KENNUNG.search(wert):
                    anders = _KENNUNG.sub(ersetzen, wert)
                    if anders != wert:
                        aenderung[spalte] = anders
            if aenderung:
                conn.execute(
                    'UPDATE "%s" SET %s WHERE id = ?'
                    % (t, ", ".join('"%s" = ?' % s for s in aenderung)),
                    [*aenderung.values(), zeilen_id])


def importieren(conn: sqlite3.Connection, daten: dict,
                auswahl: list[int] | None = None) -> list[dict]:
    """Die gewaehlten Projekte der Datei als neue anlegen.

    **Alles oder nichts**, in einer Transaktion: Ein halb eingelesenes
    Projekt waere schlimmer als keines -- es saehe vollstaendig aus.
    """
    projekte = daten["projekte"]
    if auswahl is not None:
        projekte = [projekte[i] for i in auswahl if 0 <= i < len(projekte)]
    if not projekte:
        raise UebertragungsFehler("Es ist kein Projekt ausgewählt.")
    for p in projekte:
        _pruefen(conn, p)
    try:
        with conn:
            eingelesen = [_projekt_herein(conn, p) for p in projekte]
            _kennungen_umschreiben(conn, eingelesen)
    except sqlite3.IntegrityError as fehler:
        raise UebertragungsFehler(
            "Die Datei ließ sich nicht einlesen: %s. Es wurde nichts "
            "geändert." % fehler)
    return [{k: v for k, v in e.items() if k not in ("neu", "texte")}
            for e in eingelesen]
