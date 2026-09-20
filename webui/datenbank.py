"""
Die Ablage -- SQLite, und der einzige Ort, der sie kennt.

**Warum eine eigene Datei und nicht app.py wie in Boot.** Dort sind es
zwei Tabellen, hier sind es dreizehn. Vor allem aber steht in
`docs/aufbau.md`, Abschnitt 4, eine Anforderung, die heute billig ist und
spaeter teuer: *Der Zugriff auf die Ablage gehoert an eine Stelle.*
Laeuft die Pro-Fassung dieselbe Anwendung mit einem anderen Speicher,
ist verstreutes SQL in zwanzig Modulen der Preis.

**Warum SQLite.** Sie ist schon da -- Boot benutzt sie, und `sqlite3`
steht in Pythons Standardbibliothek, die `requirements.txt` bleibt also
bei fuenf Zeilen. Ein Datenbankdienst liefe gegen die Vorgabe, dass die
Produkte getrennt installiert und getrennt verwaltet werden. Und ihre
Schwaeche, der zweite gleichzeitige Schreiber, ist zugleich die Grenze
zwischen der Community- und der Pro-Fassung: Sie liegt genau dort, wo
das Produkt ohnehin aufhoert.

**Drei Dinge in diesem Modul sind keine Stilfragen:**

- ``AUTOINCREMENT`` bei jeder Kennung. Ohne das Schluesselwort vergibt
  SQLite eine geloeschte Hoechstnummer neu -- und `docs/datenhaltung.md`,
  Abschnitt 4, verlangt das Gegenteil: *nie wiederverwenden, auch nach
  dem Archivieren nicht.* Jede Art zaehlt dabei fuer sich und ueber
  alle Projekte hinweg; das faellt aus je einer Tabelle von selbst
  richtig.
- ``journal_mode=WAL``. Es wird gelesen, waehrend im Hintergrund
  geschrieben wird; ohne WAL sperren die beiden einander aus.
- ``STRICH`` statt ``NULL``. *Eine fehlende Zeile liest sich wie ein
  Versehen, ein Strich wie eine Entscheidung* -- ein ``NULL`` ist genau
  die fehlende Zeile. Felder, bei denen *noch nicht entschieden* etwas
  anderes ist als *leer*, tragen deshalb ausdruecklich den Strich.

Warum so: `docs/aufbau.md`, Abschnitt 4, und `docs/datenhaltung.md`, Abschnitte 4
bis 8.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date
from pathlib import Path

# Der leere Wert, der eine Entscheidung ist -- nicht NULL, nicht "".
STRICH = "—"

# Wo die Datei liegt. Der Name der Variablen traegt kein PXE_: Das
# Praefix von Boot beschreibt dort einen Bootserver, hier waere es
# Unsinn. (Dass Boots Module es fest verdrahtet tragen, ist der Punkt,
# der ein spaeteres Teilen aufhaelt -- siehe docs/uebernahme.md, Abschnitt 8.)


def vorgabe_ablage() -> Path:
    r"""Wo die Ablage liegt, wenn MARLEI_DB nichts sagt.

    **Zwei Systeme, zwei Orte, und keiner davon ist geraten:** Unter
    Linux ist ``/var/lib`` der Platz fuer den veraenderlichen Zustand
    eines Dienstes, unter Windows ist es ``%ProgramData%``. Ein fester
    Unix-Pfad ergaebe dort ``C:\var\lib\marlei-tasks`` -- einen Ort,
    den niemand erwartet und den kein Installationsskript angelegt hat.

    **Windows ist noch nicht gebaut, aber es ist ein Ziel** (festgelegt
    im September 2026). Diese eine Funktion ist der Unterschied zwischen
    *laeuft, nachdem man eine Variable gesetzt hat* und *laeuft*.

    Fehlt ``ProgramData`` -- was auf einem eingerichteten Windows nicht
    vorkommt --, faellt es auf das Benutzerverzeichnis zurueck. Lieber
    ein Ort, der einem Menschen gehoert, als einer, den es nicht gibt.
    """
    if os.name == "nt":
        wurzel = (os.environ.get("ProgramData")
                  or os.environ.get("LOCALAPPDATA")
                  or str(Path.home()))
        return Path(wurzel) / "MARLEI Tasks" / "tasks.db"
    return Path("/var/lib/marlei-tasks/tasks.db")


def ablageort(roh: str = "") -> Path:
    """Der Ort aus MARLEI_DB -- oder die Vorgabe dieses Systems.

    **Ein leeres MARLEI_DB zaehlt als keins.** Dieselbe Falle wie beim
    Ausgang: ``Path("")`` ist ``Path(".")`` und damit wahr -- die Ablage
    laege dann im Arbeitsverzeichnis des Dienstes, lautlos und an einer
    Stelle, an der niemand danach sucht.

    Als eigene Funktion und nicht als Zeile beim Import: So laesst sich
    beides pruefen, ohne das Modul neu zu laden.
    """
    return Path(roh) if roh.strip() else vorgabe_ablage()


DB_PFAD = ablageort(os.environ.get("MARLEI_DB", ""))


SCHEMA = """
-- ---------------------------------------------------------------- --
-- Projekte. Die Auswahl hier baut alles Uebrige auf.
-- ---------------------------------------------------------------- --

-- Der Name ist EINDEUTIG, und das ist keine Ordnungsliebe: Das
-- Losungswort der Werkseinstellung ist der Projektname. Gaebe es zwei
-- gleichnamige Projekte, bestaetigte die Eingabe nicht mehr, welches
-- gemeint ist -- und genau dafuer ist sie da.
--
-- eingetragen_am wie in den vier Registern -- ohne Vorgabe, denn ein
-- erfundenes Datum waere schlimmer als eine Nachfrage.
CREATE TABLE IF NOT EXISTS projekte (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL UNIQUE,
    beschreibung   TEXT NOT NULL DEFAULT '',
    vision         TEXT NOT NULL DEFAULT '',
    zustand        TEXT NOT NULL DEFAULT 'AKTIV'
                   CHECK (zustand IN ('AKTIV', 'RUHT', 'ABGESCHLOSSEN')),
    eingetragen_am TEXT NOT NULL
);

-- Der Bereich sagt, woran etwas ruehrt -- und ist deshalb je Projekt ein
-- anderer. Boots sechs (systeme, quellen, server, oberflaeche,
-- veroeffentlichung, mappe) gelten nirgends sonst. Kategorie und
-- Prioritaet dagegen beschreiben die ART eines Eintrags und stehen
-- deshalb als CHECK weiter unten, nicht in einer Tabelle.
CREATE TABLE IF NOT EXISTS bereiche (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    projekt_id  INTEGER NOT NULL REFERENCES projekte(id),
    wert        TEXT NOT NULL,
    wofuer      TEXT NOT NULL DEFAULT '',
    UNIQUE (projekt_id, wert)
);


-- ---------------------------------------------------------------- --
-- Sammlung (B-) -- was aufgefallen ist, ungefiltert.
-- ---------------------------------------------------------------- --

-- KEIN Status, und das ist begruendet: Es gaebe nur einen, und der hiesse
-- "liegt da". An einer rohen Beobachtung arbeitet niemand.
--
-- eingetragen_am misst hier die LIEGEDAUER. Dasselbe Feld an der Aufgabe
-- misst die Arbeitsdauer -- zwei Zahlen, zwei Fragen.
--
-- Die fuenf Fehlerangaben MAHNEN, sie sperren nicht: Ein unvollstaendiger
-- FEHLER wird ein Befund, kein abgewiesenes Formular. Deshalb tragen sie
-- eine Vorgabe und keinen Zwang. Warum: die Huerde beim Eintragen ist
-- niedrig, und eine Regel, deren Weg teuer ist, wird umgangen.
CREATE TABLE IF NOT EXISTS topics (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    projekt_id         INTEGER NOT NULL REFERENCES projekte(id),
    titel              TEXT NOT NULL,
    kategorie          TEXT NOT NULL DEFAULT 'IDEE'
                       CHECK (kategorie IN ('IDEE', 'FEHLER')),
    bereich_id         INTEGER NOT NULL REFERENCES bereiche(id),
    prio               TEXT NOT NULL DEFAULT '—'
                       CHECK (prio IN ('MUSS', 'SOLL', 'KANN', '—')),
    eingetragen_am     TEXT NOT NULL,
    abschluss          TEXT NOT NULL DEFAULT '—'
                       CHECK (abschluss IN ('verworfen', 'aufgabe', '—')),
    ursprung           TEXT NOT NULL DEFAULT '',
    beschreibung       TEXT NOT NULL DEFAULT '',
    schaerfen          TEXT NOT NULL DEFAULT '',
    fehler_wann        TEXT NOT NULL DEFAULT '',
    fehler_woran       TEXT NOT NULL DEFAULT '',
    fehler_was_tun     TEXT NOT NULL DEFAULT '',
    fehler_warum_nicht TEXT NOT NULL DEFAULT '',
    fehler_kosten      TEXT NOT NULL DEFAULT ''
);


-- ---------------------------------------------------------------- --
-- Aufgaben (A-) -- woran gearbeitet wird.
-- ---------------------------------------------------------------- --

-- Die Kategorie faellt weg: Ob eine Beobachtung als Idee oder Fehler ins
-- Haus kam, ist beantwortet, sobald daraus Arbeit wird. Dafuer kommt der
-- Status hinzu, denn hier sitzt jemand dran.
--
-- Der CHECK auf status_seit setzt eine Regel der Mappe durch, die dort
-- nur dastand: "mit Datum ausser bei PASSIV".
--
-- dahinter ist laut Regel 5 Pflicht, MAHNT aber nur (entschieden am
-- 07.09.2026): Die Ursache kann man nachtragen, sobald man sie versteht.
-- Ein leeres Feld wird ein Befund, und der Zusammenlegen-Knopf fuellt es
-- aus den Ursprungstexten vor -- so nennt die Einordnung selbst die
-- Abhilfe, nicht als Sperre.
--
-- Die Abnahme dagegen SPERRT: Ohne sie weiss niemand, wann die Aufgabe
-- fertig ist, und das laesst sich spaeter nicht rekonstruieren. Sie
-- steht in aufgabe_punkte und wird beim Anlegen geprueft, nicht hier --
-- eine Bedingung ueber zwei Tabellen kann ein CHECK nicht.
CREATE TABLE IF NOT EXISTS aufgaben (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    projekt_id     INTEGER NOT NULL REFERENCES projekte(id),
    titel          TEXT NOT NULL,
    bereich_id     INTEGER NOT NULL REFERENCES bereiche(id),
    prio           TEXT NOT NULL DEFAULT '—'
                   CHECK (prio IN ('MUSS', 'SOLL', 'KANN', '—')),
    status         TEXT NOT NULL DEFAULT 'PASSIV'
                   CHECK (status IN ('PASSIV', 'AKTIV', 'PAUSE')),
    status_seit    TEXT NOT NULL DEFAULT '—'
                   CHECK (status = 'PASSIV' OR status_seit <> '—'),
    eingetragen_am TEXT NOT NULL,
    abschluss      TEXT NOT NULL DEFAULT '—'
                   CHECK (abschluss IN ('erledigt', 'verworfen',
                                        'meilenstein', '—')),
    dahinter       TEXT NOT NULL DEFAULT '',
    bedacht        TEXT NOT NULL DEFAULT '',
    ergebnis       TEXT NOT NULL DEFAULT '',
    meilenstein_id INTEGER REFERENCES meilensteine(id)
);

-- Zwei Listen an einer Aufgabe, und sie messen VERSCHIEDENES:
--   ARBEIT   den Fortschritt -- wie weit die Arbeit ist
--   ABNAHME  die Fertigkeit  -- woran man sie feststellt
-- Sie liegen in einer Tabelle, weil sie dieselbe Form haben. **In der
-- Oberflaeche duerfen sie nicht gleich aussehen** -- sonst verschwindet
-- der Unterschied und mit ihm die Abnahme als eigenstaendige Sache.
--
-- erledigt_am traegt den Strich, solange offen: Erledigtes wird nicht
-- geloescht, sondern bekommt ein Datum. In der Mappe war das ein
-- Textkniff ("[erledigt]"), hier ist es ein Zustand je Zeile.
CREATE TABLE IF NOT EXISTS aufgabe_punkte (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    aufgabe_id  INTEGER NOT NULL REFERENCES aufgaben(id) ON DELETE CASCADE,
    art         TEXT NOT NULL CHECK (art IN ('ARBEIT', 'ABNAHME')),
    folge       INTEGER NOT NULL,
    text        TEXT NOT NULL,
    erledigt_am TEXT NOT NULL DEFAULT '—'
);

-- Der Ursprung nennt die Topics, aus denen die Aufgabe entstand. Auch
-- keines ist erlaubt: Eine Aufgabe darf direkt entstehen.
CREATE TABLE IF NOT EXISTS aufgabe_ursprung (
    aufgabe_id INTEGER NOT NULL REFERENCES aufgaben(id) ON DELETE CASCADE,
    topic_id   INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    PRIMARY KEY (aufgabe_id, topic_id)
);


-- ---------------------------------------------------------------- --
-- Meilensteine (M-) -- die Klammer um mehrere Aufgaben.
-- ---------------------------------------------------------------- --

-- "Wer geprueft hat" gibt es hier NICHT, anders als in der Mappe. In der
-- Community-Fassung ist es immer dieselbe Person; ein Feld, das auf jedem
-- Eintrag denselben Namen traegt, sagt nichts. Es kommt in Pro wieder --
-- die Einordnung zaehlt "die Frage, wer abnehmen darf" ausdruecklich
-- unter dem auf, was mit der zweiten Person kommt.
--
-- Ein abgenommener Meilenstein verschwindet hier nicht, er wird
-- gefiltert. Der Zweck der Mappenregel bleibt: Die Liste zeigt, was
-- offen ist.
CREATE TABLE IF NOT EXISTS meilensteine (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    projekt_id        INTEGER NOT NULL REFERENCES projekte(id),
    benennung         TEXT NOT NULL,
    prio              TEXT NOT NULL DEFAULT '—'
                      CHECK (prio IN ('MUSS', 'SOLL', 'KANN', '—')),
    eingetragen_am    TEXT NOT NULL,
    abschluss         TEXT NOT NULL DEFAULT '—'
                      CHECK (abschluss IN ('erledigt', 'verworfen', '—')),
    beschreibung      TEXT NOT NULL DEFAULT '',
    bedingung         TEXT NOT NULL DEFAULT '—',
    nachbereitung     TEXT NOT NULL DEFAULT '—',
    abnahme_kriterium TEXT NOT NULL DEFAULT '',
    abnahme_am        TEXT NOT NULL DEFAULT '—'
);

-- Vorgaenger und Nachfolger sind DIESELBE Beziehung, von zwei Seiten
-- gelesen -- deshalb eine Tabelle und keine zwei. Der CHECK verhindert
-- den Meilenstein, der auf sich selbst wartet.
CREATE TABLE IF NOT EXISTS meilenstein_vorgaenger (
    meilenstein_id INTEGER NOT NULL REFERENCES meilensteine(id) ON DELETE CASCADE,
    vorgaenger_id  INTEGER NOT NULL REFERENCES meilensteine(id) ON DELETE CASCADE,
    PRIMARY KEY (meilenstein_id, vorgaenger_id),
    CHECK (meilenstein_id <> vorgaenger_id)
);

-- Woher er kommt -- nicht, woraus er besteht. Woraus er besteht, sagt
-- aufgaben.meilenstein_id. Zwei verschiedene Fragen, zwei Orte.
CREATE TABLE IF NOT EXISTS meilenstein_ursprung (
    meilenstein_id INTEGER NOT NULL REFERENCES meilensteine(id) ON DELETE CASCADE,
    aufgabe_id     INTEGER NOT NULL REFERENCES aufgaben(id) ON DELETE CASCADE,
    PRIMARY KEY (meilenstein_id, aufgabe_id)
);

-- Was den geraden Weg gestoert hat. **Wird notiert, sobald es passiert**,
-- nicht bei der Abnahme -- deshalb traegt jede Zeile ihr eigenes Datum
-- und nicht das der Abnahme. Der Weg dorthin muss so kurz sein wie das
-- Eintragen in der Sammlung; sonst wird es aus dem Gedaechtnis
-- nachgetragen und ist wertlos.
--
-- **ES GIBT NUR NOCH DEN UMWEG.** Im September 2026 entschieden: Die
-- zweite Art, die *Rast*, faellt weg -- die Unterscheidung war zu
-- fliessend. Wann ein Warten eine Rast ist und wann ein Umweg, war an
-- jedem einzelnen Fall zu entscheiden, und zwei Etiketten, die sich
-- nicht auseinanderhalten lassen, sortieren nichts.
--
-- Damit hat die Spalte "art" keine Aufgabe mehr und ist gestrichen: Ein
-- CHECK, das immer denselben Wert erlaubt, ist eine Spalte, die auf
-- jeder Zeile dasselbe sagt. (In MARLEI Boot bleibt beides, wie es ist
-- -- die Mappe dort wird davon nicht angefasst.)
CREATE TABLE IF NOT EXISTS meilenstein_dazwischen (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    meilenstein_id INTEGER NOT NULL REFERENCES meilensteine(id) ON DELETE CASCADE,
    datum          TEXT NOT NULL,
    text           TEXT NOT NULL
);


-- ---------------------------------------------------------------- --
-- Entscheidungen (E-) -- warum es so ist.
-- ---------------------------------------------------------------- --

-- KEIN Feldschema fuer den Inhalt, und das ist der Punkt: Eine Abwaegung
-- hat keine Form, die sich vorher festlegen liesse, sie hat einen
-- Verlauf -- und der Verlauf zeigt, wie gruendlich entschieden wurde.
-- Ein Schema wuerde genau das plaetten.
--
-- Der Bezug darf leer bleiben: Abwaegungen ueber das Projekt selbst
-- gehoeren zu keinem Eintrag. Anders als in der Mappe traegt jede
-- Entscheidung trotzdem eine eigene Kennung -- damit auch die
-- freistehende verweisbar ist.
--
-- OFFEN und ENTSCHLUSS, festgelegt am 07.09.2026. OFFEN heisst nicht
-- "noch nichts geschrieben" -- es heisst, der Weg ist da und der
-- Entschluss steht aus. Beide Zustaende speisen einen eigenen Befund:
-- lange OFFEN heisst, etwas wartet auf einen Entschluss; ENTSCHLUSS bei
-- einem Eintrag, der trotzdem liegt, ist die Liegeprobe.
CREATE TABLE IF NOT EXISTS entscheidungen (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    projekt_id INTEGER NOT NULL REFERENCES projekte(id),
    titel      TEXT NOT NULL,
    zustand    TEXT NOT NULL DEFAULT 'OFFEN'
               CHECK (zustand IN ('OFFEN', 'ENTSCHLUSS')),
    datum      TEXT NOT NULL,
    bezug_art  TEXT NOT NULL DEFAULT '—'
               CHECK (bezug_art IN ('B', 'A', 'M', '—')),
    bezug_id   INTEGER,
    text       TEXT NOT NULL DEFAULT '',
    CHECK ((bezug_art = '—') = (bezug_id IS NULL))
);


-- ---------------------------------------------------------------- --
-- Was jemand zur Kenntnis genommen hat.
-- ---------------------------------------------------------------- --

-- Befunde laufen ueber ALLE Projekte -- die einzige Stelle, an der die
-- Vorauswahl nicht gilt. **Zur Kenntnis genommen wird trotzdem je
-- Projekt**: Sonst naehme das Stillstellen in einem Projekt dieselbe Lage
-- in einem anderen mit, und ein Befund verschwaende, den nie jemand
-- gesehen hat.
CREATE TABLE IF NOT EXISTS kenntnis (
    projekt_id INTEGER NOT NULL REFERENCES projekte(id),
    befund     TEXT NOT NULL,
    seit       TEXT NOT NULL,
    PRIMARY KEY (projekt_id, befund)
);
"""


# Die Suche ueber die Sammlung -- fuer die Buendelprobe.
#
# Die Einordnung sagt, die Verbindung zweier Eintraege werde NICHT durch
# die Titel gefunden, sondern beim Lesen der Beschreibungen. Genau dafuer
# ist das hier: FTS5 durchsucht Titel und Beschreibung zusammen.
#
# Eigener Block, weil FTS5 einkompiliert sein muss. Fehlt es, laeuft alles
# Uebrige weiter -- nur die Volltextsuche nicht. Lieber eine Funktion
# weniger als eine Anwendung, die nicht startet.
SCHEMA_SUCHE = """
CREATE VIRTUAL TABLE IF NOT EXISTS topics_suche
USING fts5(titel, beschreibung, content='topics', content_rowid='id');

CREATE TRIGGER IF NOT EXISTS topics_suche_ein AFTER INSERT ON topics BEGIN
    INSERT INTO topics_suche(rowid, titel, beschreibung)
    VALUES (new.id, new.titel, new.beschreibung);
END;

CREATE TRIGGER IF NOT EXISTS topics_suche_weg AFTER DELETE ON topics BEGIN
    INSERT INTO topics_suche(topics_suche, rowid, titel, beschreibung)
    VALUES ('delete', old.id, old.titel, old.beschreibung);
END;

CREATE TRIGGER IF NOT EXISTS topics_suche_neu AFTER UPDATE ON topics BEGIN
    INSERT INTO topics_suche(topics_suche, rowid, titel, beschreibung)
    VALUES ('delete', old.id, old.titel, old.beschreibung);
    INSERT INTO topics_suche(rowid, titel, beschreibung)
    VALUES (new.id, new.titel, new.beschreibung);
END;
"""


# Spalten, die erst spaeter dazugekommen sind. "CREATE TABLE IF NOT
# EXISTS" ruehrt eine schon vorhandene Tabelle nicht mehr an -- eine
# Datenbank aus einer aelteren Fassung braucht die neuen Spalten deshalb
# per ALTER TABLE. Dasselbe Verfahren wie in Boot.
NACHZUEGLER: dict[str, dict[str, str]] = {}

# Und das Gegenstueck: Spalten, die weggefallen sind. Dieselbe
# Ueberlegung von der anderen Seite -- "CREATE TABLE IF NOT EXISTS"
# nimmt aus einer vorhandenen Tabelle nichts heraus, und eine Spalte,
# die es im Schema nicht mehr gibt, aber in der Datenbank noch, ist
# schlimmer als eine fehlende: Sie steht auf NOT NULL, und der naechste
# INSERT scheitert an etwas, das im Quelltext gar nicht mehr vorkommt.
#
# SQLite kann DROP COLUMN seit 3.35. Kann es die hier nicht, bleibt die
# Spalte stehen -- dann muss sie eine Vorgabe haben oder NULL erlauben.
ENTFALLEN: dict[str, tuple[str, ...]] = {
    # 07.09.2026: Von Umweg und Rast bleibt der Umweg.
    "meilenstein_dazwischen": ("art",),
}


# Welcher Buchstabe zu welcher Tabelle gehoert. Jede Art zaehlt fuer sich
# und ueber alle Projekte hinweg -- eine Kennung gehoert damit genau einem
# Eintrag, fuer immer. Dass die Nummern eines einzelnen Projekts dabei
# springen, ist der Preis und kein Fehler: Die Luecken sind die Eintraege
# der anderen Projekte.
ARTEN = {
    "P": "projekte",
    "B": "topics",
    "A": "aufgaben",
    "M": "meilensteine",
    "E": "entscheidungen",
}


def kennung(art: str, nummer: int) -> str:
    """``kennung("B", 65)`` -> ``B-065``.

    Drei Ziffern, wie in der Mappe. Wird die Nummer vierstellig, waechst
    die Kennung mit -- lieber eine Stelle mehr als eine abgeschnittene.
    """
    return "%s-%03d" % (art, nummer)


def verbindung(pfad: Path | None = None) -> sqlite3.Connection:
    """Eine Verbindung mit allem, was sie braucht.

    **WAL ist Pflicht, keine Kuer.** Es wird gelesen, waehrend im
    Hintergrund geschrieben wird; ohne WAL sperren die beiden einander
    aus und die Seite steht.

    **Fremdschluessel muss man einschalten.** SQLite prueft sie sonst
    nicht -- die Voreinstellung ist aus Ruecksicht auf alte Anwendungen
    ``OFF``, und ein Verweis auf einen geloeschten Eintrag faellt dann
    nirgends auf.
    """
    ziel = pfad or DB_PFAD
    ziel.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ziel)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def anlegen(conn: sqlite3.Connection) -> bool:
    """Schema anlegen und spaetere Spalten nachziehen.

    Gibt zurueck, ob die Volltextsuche zur Verfuegung steht. Fehlt FTS5
    in der SQLite dieser Maschine, laeuft alles Uebrige weiter -- nur die
    Buendelprobe muss sich dann anders behelfen.
    """
    conn.executescript(SCHEMA)

    for tabelle, spalten in NACHZUEGLER.items():
        vorhanden = {r["name"] for r in conn.execute(
            "PRAGMA table_info(%s)" % tabelle)}
        for name, typ in spalten.items():
            if name not in vorhanden:
                conn.execute("ALTER TABLE %s ADD COLUMN %s %s"
                             % (tabelle, name, typ))

    for tabelle, spalten in ENTFALLEN.items():
        vorhanden = {r["name"] for r in conn.execute(
            "PRAGMA table_info(%s)" % tabelle)}
        for name in spalten:
            if name in vorhanden:
                try:
                    conn.execute("ALTER TABLE %s DROP COLUMN %s"
                                 % (tabelle, name))
                except sqlite3.OperationalError:
                    # Aeltere SQLite kann kein DROP COLUMN. Die Spalte
                    # bleibt dann stehen; sie stoert nur, wenn sie NOT
                    # NULL ohne Vorgabe ist -- dann muss der naechste
                    # Umbau sie mitnehmen.
                    print("MARLEI Tasks: %s.%s liess sich nicht entfernen "
                          "-- diese SQLite kann kein DROP COLUMN."
                          % (tabelle, name))

    try:
        conn.executescript(SCHEMA_SUCHE)
        suche = True
    except sqlite3.OperationalError:
        suche = False

    conn.commit()
    return suche


def projekt_loeschen(conn: sqlite3.Connection, projekt_id: int) -> None:
    """Ein Projekt mit allem, was daranhaengt.

    **Von einem Projekt kaskadiert mit Absicht nichts.** Ein
    ``DELETE FROM projekte`` scheitert deshalb laut an den
    Fremdschluesseln, statt still den Bestand mitzunehmen -- und
    geloescht wird nur hier, wo die Reihenfolge steht. Das ist dieselbe
    Haltung wie beim Losungswort: Was sich nicht rueckgaengig machen
    laesst, soll nicht nebenbei passieren.

    **Innerhalb eines Eintrags kaskadiert es sehr wohl** -- die Punkte
    einer Aufgabe, die Umwege eines Meilensteins. Sie gehoeren ihm und
    haben ohne ihn keine Bedeutung.

    **Was der Aufrufer vorher erledigt haben muss** (docs/aufbau.md,
    Abschnitt 2): den Export anbieten und den Projektnamen als
    Losungswort abfragen. Diese Funktion prueft das nicht -- sie ist die
    Ablage, nicht die Oberflaeche.

    Alles in EINER Transaktion: Ein halb geloeschtes Projekt waere
    schlimmer als ein ganzes.
    """
    with conn:
        conn.execute("DELETE FROM kenntnis WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM entscheidungen WHERE projekt_id = ?",
                     (projekt_id,))
        # Erst die Aufgaben von ihrem Meilenstein loesen: Sonst haelt der
        # Verweis den Meilenstein fest, den wir gleich entfernen.
        conn.execute("UPDATE aufgaben SET meilenstein_id = NULL "
                     "WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM meilensteine WHERE projekt_id = ?",
                     (projekt_id,))
        conn.execute("DELETE FROM aufgaben WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM topics WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM bereiche WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM projekte WHERE id = ?", (projekt_id,))


# ==================================================================== #
# Datum
# ==================================================================== #

# **In der Ablage steht ein Datum nach ISO, in der Ansicht deutsch.**
# Entschieden am 07.09.2026 beim Bau des Reiters Projekte.
#
# Der Grund ist keine Vorliebe, sondern docs/datenhaltung.md, Abschnitt 8:
# *Was die Verzeichnisse heute von Hand tun, tut die Abfrage* -- und die
# drei Proben (Buendel, Dreimonate, Liegen) rechnen mit Daten. Als
# "07.09.2026" sortiert SQLite nach dem Tag und vergleicht Jahre gar
# nicht; "2026-09-07" sortiert und vergleicht sich als Text richtig.
#
# Angezeigt wird trotzdem nie so: Die Mappe schreibt 07.09.2026, und
# genau das steht in jedem Verweis, den jemand liest.
def datum_zeigen(iso: str) -> str:
    """``"2026-09-07"`` -> ``"07.09.2026"``.

    Was nicht wie ein ISO-Datum aussieht, kommt unveraendert zurueck --
    ein Strich bleibt ein Strich, und ein Wert aus einer aelteren
    Fassung wird nicht verstuemmelt.
    """
    teile = (iso or "").split("-")
    if len(teile) != 3 or not all(t.isdigit() for t in teile):
        return iso
    return "%s.%s.%s" % (teile[2], teile[1], teile[0])


# ==================================================================== #
# Projekte
# ==================================================================== #

def projekte(conn: sqlite3.Connection) -> list[dict]:
    """Alle Projekte, mit Bestand und Bereichen.

    **Sortiert nach der Kennung, nicht nach dem Namen.** Die Kennung ist
    die Reihenfolge, in der die Projekte entstanden sind; sie aendert
    sich nie. Nach Namen sortiert spraenge die Liste, sobald jemand ein
    Projekt umbenennt -- und die Stelle, an der man sein Projekt sucht,
    waere jedes Mal eine andere.
    """
    zeilen = conn.execute(
        "SELECT id, name, beschreibung, vision, zustand, eingetragen_am "
        "FROM projekte ORDER BY id").fetchall()
    return [_projekt_ausbauen(conn, dict(z)) for z in zeilen]


def projekt(conn: sqlite3.Connection, projekt_id: int) -> dict | None:
    """Ein Projekt, mit Bestand und Bereichen -- oder None."""
    zeile = conn.execute(
        "SELECT id, name, beschreibung, vision, zustand, eingetragen_am "
        "FROM projekte WHERE id = ?", (projekt_id,)).fetchone()
    return _projekt_ausbauen(conn, dict(zeile)) if zeile else None


def _projekt_ausbauen(conn: sqlite3.Connection, p: dict) -> dict:
    p["kennung"] = kennung("P", p["id"])
    p["eingetragen_deutsch"] = datum_zeigen(p["eingetragen_am"])
    p["bereiche"] = bereiche(conn, p["id"])
    p["bestand"] = bestand(conn, p["id"])
    return p


def projekt_anlegen(conn: sqlite3.Connection, name: str, eingetragen_am: str,
                    beschreibung: str = "", vision: str = "",
                    zustand: str = "AKTIV") -> int:
    """Ein neues Projekt. Gibt seine Kennungsnummer zurueck.

    Wirft ``sqlite3.IntegrityError``, wenn der Name schon vergeben ist --
    die Oberflaeche faengt das ab und sagt es. Sie darf es NICHT vorher
    selbst pruefen und dann einfuegen: Zwischen Frage und Antwort passt
    ein zweiter Browser.
    """
    with conn:
        cur = conn.execute(
            "INSERT INTO projekte (name, beschreibung, vision, zustand, "
            "eingetragen_am) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), beschreibung.strip(), vision.strip(), zustand,
             eingetragen_am))
    return int(cur.lastrowid)


# Was sich an einem Projekt aendern laesst. Die Liste steht hier und
# nicht in app.py: Ein Feldname aus dem Formular darf nie ungeprueft in
# ein UPDATE wandern.
AENDERBAR = ("name", "beschreibung", "vision", "zustand", "eingetragen_am")


def projekt_aendern(conn: sqlite3.Connection, projekt_id: int,
                    **felder: str) -> None:
    """Einzelne Felder eines Projekts. Unbekannte Namen fliegen raus."""
    setzen = {k: v for k, v in felder.items() if k in AENDERBAR}
    if not setzen:
        return
    with conn:
        conn.execute(
            "UPDATE projekte SET %s WHERE id = ?"
            % ", ".join("%s = ?" % k for k in setzen),
            (*setzen.values(), projekt_id))


def bestand(conn: sqlite3.Connection, projekt_id: int) -> dict:
    """Wie viel in einem Projekt liegt -- je Register eine Zahl.

    **Abgelesen, kein Feld.** Sie steht in der Fusszeile der Karte, weil
    sie ueber den Eintrag spricht, statt ihn zu sein -- und beim Loeschen
    sagt dieselbe Zahl, was verloren geht.
    """
    zahlen = {}
    for schluessel, tabelle in (("sammlung", "topics"),
                                ("aufgaben", "aufgaben"),
                                ("meilensteine", "meilensteine"),
                                ("entscheidungen", "entscheidungen")):
        zahlen[schluessel] = conn.execute(
            "SELECT COUNT(*) FROM %s WHERE projekt_id = ?" % tabelle,
            (projekt_id,)).fetchone()[0]
    return zahlen


# ==================================================================== #
# Bereiche -- je Projekt eine eigene Liste
# ==================================================================== #

def bereiche(conn: sqlite3.Connection, projekt_id: int) -> list[dict]:
    """Die Bereiche eines Projekts, mit der Zahl der Eintraege daran.

    Die Zahl ist kein Schmuck: An ihr haengt, ob sich der Bereich
    ueberhaupt noch entfernen laesst.
    """
    return [{
        "id": z["id"],
        "wert": z["wert"],
        "wofuer": z["wofuer"],
        "benutzt": z["benutzt"],
    } for z in conn.execute("""
        SELECT b.id, b.wert, b.wofuer,
               (SELECT COUNT(*) FROM topics  t WHERE t.bereich_id = b.id)
             + (SELECT COUNT(*) FROM aufgaben a WHERE a.bereich_id = b.id)
               AS benutzt
        FROM bereiche b WHERE b.projekt_id = ? ORDER BY b.wert
    """, (projekt_id,)).fetchall()]


def bereich_anlegen(conn: sqlite3.Connection, projekt_id: int,
                    wert: str) -> None:
    """Einen Bereich hinzufuegen. Doppelte werden still uebergangen.

    **Still, und das ist Absicht:** Wer einen Bereich eintippt, der schon
    dasteht, wollte, dass er dasteht. Eine Fehlermeldung beschriebe
    keinen Fehler.
    """
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO bereiche (projekt_id, wert) VALUES (?, ?)",
            (projekt_id, wert.strip()))


def bereich_loeschen(conn: sqlite3.Connection, bereich_id: int) -> int:
    """Einen Bereich entfernen. Gibt zurueck, wie viele daran hingen.

    **Ist die Zahl groesser als null, passiert nichts** -- und das
    sperrt, statt zu mahnen. Der Bereich eines Eintrags waechst nicht
    nach: Er steht in keiner zweiten Spalte, aus der er sich
    wiederherstellen liesse, und ein Eintrag ohne Bereich waere in jeder
    Durchsicht unauffindbar. *Sperren gehoert zu dem, was nicht
    nachwachsen kann.*
    """
    zeile = conn.execute("""
        SELECT (SELECT COUNT(*) FROM topics   WHERE bereich_id = ?)
             + (SELECT COUNT(*) FROM aufgaben WHERE bereich_id = ?)
    """, (bereich_id, bereich_id)).fetchone()
    haengt_dran = int(zeile[0])
    if haengt_dran:
        return haengt_dran
    with conn:
        conn.execute("DELETE FROM bereiche WHERE id = ?", (bereich_id,))
    return 0


# ==================================================================== #
# Sammlung (B-)
# ==================================================================== #

# Was aufgezaehlt werden darf. Dieselben Werte stehen als CHECK in der
# Ablage; hier stehen sie, damit ein erfundener Wert schon an der
# Oberflaeche auffaellt und nicht erst als IntegrityError.
KATEGORIEN = ("IDEE", "FEHLER")
PRIOS = ("MUSS", "SOLL", "KANN", STRICH)
ABSCHLUESSE = ("verworfen", "aufgabe", STRICH)

# Die fuenf Angaben, die ein FEHLER braucht -- Spalte und Aufschrift.
#
# **Sie mahnen, sie sperren nicht.** Ein unvollstaendiger FEHLER wird ein
# Befund, kein abgewiesenes Formular: Hier stossen zwei eigene Regeln
# aneinander -- *die Huerde beim Eintragen ist niedrig* gegen *fuenf
# Angaben* -- und eine Regel, deren Weg teuer ist, wird umgangen.
#
# Die Reihenfolge ist die aus docs/aufbau.md und wird nicht sortiert: Die
# vierte traegt die eigentliche Regel (*was keinen Grund hat, gehoert
# behoben und nicht eingetragen*) und steht deshalb dort, wo man beim
# Ausfuellen schon nachgedacht hat.
FEHLERANGABEN = (
    ("fehler_wann", "Wann er auftritt"),
    ("fehler_woran", "Woran man ihn merkt"),
    ("fehler_was_tun", "Was man tun kann"),
    ("fehler_warum_nicht", "Warum er jetzt nicht behoben wird"),
    ("fehler_kosten", "Was eine Lösung grob kostet"),
)

# Spalten, die spaeter dazugekommen sind -- siehe NACHZUEGLER oben.
NACHZUEGLER.update({
    # Wann ein Eintrag abgeschlossen wurde. Ohne das Datum kann das
    # Quittungsbuch keine Zeile schreiben: Es haelt fest, WAS WANN fertig
    # wurde, und "wann" stand bisher nirgends.
    "topics": {"abschluss_am": "TEXT NOT NULL DEFAULT ''"},
    # Wann zuletzt eine Durchsicht stattfand. Die Zahl *seit der letzten
    # Durchsicht* laesst sich sonst nicht bilden: Eine vergebene
    # Prioritaet hinterlaesst kein Datum, und aus dem Bestand ist nicht
    # abzulesen, wann jemand hingesehen und nichts getan hat.
    "projekte": {"durchsicht_am": "TEXT NOT NULL DEFAULT ''"},
})


def heute() -> str:
    """Das heutige Datum nach ISO -- so, wie es in der Ablage steht."""
    return date.today().isoformat()


def tage_seit(iso: str) -> int | None:
    """Wie viele Tage seit diesem Datum vergangen sind.

    ``None``, wenn dort kein Datum steht -- ein Strich, ein leeres Feld,
    ein Wert aus einer aelteren Fassung. **Nicht 0:** Null Tage heisst
    *heute*, und das ist etwas anderes als *unbekannt*.
    """
    try:
        return (date.today() - date.fromisoformat(iso)).days
    except (ValueError, TypeError):
        return None


def _topic_ausbauen(z: dict) -> dict:
    z["kennung"] = kennung("B", z["id"])
    z["eingetragen_deutsch"] = datum_zeigen(z["eingetragen_am"])
    z["liegt_seit"] = tage_seit(z["eingetragen_am"])
    # Was an einem FEHLER fehlt. Bei einer IDEE ist die Liste immer leer:
    # Die fuenf Angaben gehoeren zum Fehler, nicht zum Eintrag.
    z["fehlt"] = ([auf for spalte, auf in FEHLERANGABEN
                   if not (z.get(spalte) or "").strip()]
                  if z["kategorie"] == "FEHLER" else [])
    return z


def topics(conn: sqlite3.Connection, projekt_id: int, suche: str = "",
           offen_nur: bool = True) -> list[dict]:
    """Die Sammlung eines Projekts.

    **Sortiert nach der Kennung, absteigend** -- das Jüngste oben. Wer
    etwas einträgt, will es danach sehen; wer die Durchsicht macht, sucht
    ohnehin über die Spalte *liegt seit*.

    ``suche`` geht über **Titel und Beschreibung**, und zwar über FTS5.
    Das ist die Bündelprobe aus der Einordnung: *Die Verbindung zweier
    Einträge wird nicht durch die Titel gefunden, sondern beim Lesen der
    Beschreibungen.* Fehlt FTS5 auf dieser Maschine, fällt die Suche auf
    ein schlichtes LIKE zurück -- schlechter, aber nicht weg.

    ``offen_nur`` lässt weg, was einen Abschluss hat: *Abschluss setzen
    heißt weg von hier* -- der Eintrag steht danach im Archiv.
    """
    wo = ["t.projekt_id = ?"]
    werte: list = [projekt_id]
    if offen_nur:
        wo.append("t.abschluss = ?")
        werte.append(STRICH)

    if suche.strip():
        treffer = _suchtreffer(conn, suche.strip())
        if not treffer:
            return []
        wo.append("t.id IN (%s)" % ",".join("?" * len(treffer)))
        werte.extend(treffer)

    zeilen = conn.execute("""
        SELECT t.*, b.wert AS bereich
        FROM topics t JOIN bereiche b ON b.id = t.bereich_id
        WHERE %s ORDER BY t.id DESC
    """ % " AND ".join(wo), werte).fetchall()
    return [_topic_ausbauen(dict(z)) for z in zeilen]


def _suchtreffer(conn: sqlite3.Connection, wort: str) -> list[int]:
    """Die Kennungsnummern, die auf ein Suchwort passen.

    Getrennt von ``topics()``, weil hier der Rückfall sitzt: Ohne FTS5
    gibt es die virtuelle Tabelle nicht, und dann muss die Suche trotzdem
    etwas tun.
    """
    try:
        # Das Sternchen macht aus "upl" ein "upload" -- ohne es findet
        # FTS5 nur ganze Woerter, und eine Suche, die beim Tippen nichts
        # findet, sieht aus wie eine kaputte.
        muster = " ".join(w + "*" for w in wort.split())
        return [z[0] for z in conn.execute(
            "SELECT rowid FROM topics_suche WHERE topics_suche MATCH ?",
            (muster,)).fetchall()]
    except sqlite3.OperationalError:
        wie = "%" + wort + "%"
        return [z[0] for z in conn.execute(
            "SELECT id FROM topics WHERE titel LIKE ? OR beschreibung LIKE ?",
            (wie, wie)).fetchall()]


def topic(conn: sqlite3.Connection, topic_id: int) -> dict | None:
    """Ein Eintrag der Sammlung -- oder None."""
    z = conn.execute("""
        SELECT t.*, b.wert AS bereich
        FROM topics t JOIN bereiche b ON b.id = t.bereich_id
        WHERE t.id = ?""", (topic_id,)).fetchone()
    return _topic_ausbauen(dict(z)) if z else None


# Die Textfelder eines Eintrags. Wie AENDERBAR bei den Projekten: Ein
# Feldname aus einem Formular darf nie ungeprueft in ein INSERT oder
# UPDATE wandern.
TOPIC_TEXTE = ("beschreibung", "schaerfen", "ursprung") + tuple(
    spalte for spalte, _ in FEHLERANGABEN)
# **eingetragen_am steht NICHT darin, und das ist der Unterschied zu
# den Projekten und den Meilensteinen** (dort ist es aenderbar). Bei
# einem Eintrag der Sammlung ist das Datum keine Angabe, sondern die
# Messgrundlage: Daran haengt "liegt seit", die Liegeprobe und die Karte
# "Was am laengsten liegt". Ein verstellbares Eintragsdatum hiesse, eine
# Zahl geradebiegen zu koennen, statt den Eintrag zu bearbeiten.
#
# Die Sperre steht hier und nicht nur in der Vorlage: Ein Feld, das die
# Seite nicht zeigt, laesst sich trotzdem schicken -- und eine Sperre,
# die sich umgehen laesst, ist keine (docs/aufbau.md, "Die Sperre gilt auch
# nachtraeglich"). Wer das Datum wirklich braucht, aendert es dort, wo
# es herkommt.
TOPIC_AENDERBAR = ("titel", "kategorie", "bereich_id",
                   "prio") + TOPIC_TEXTE


def topic_anlegen(conn: sqlite3.Connection, projekt_id: int, titel: str,
                  bereich_id: int, eingetragen_am: str,
                  kategorie: str = "IDEE", **weitere: str) -> int:
    """Ein neuer Eintrag. Gibt seine Kennungsnummer zurück.

    **Prio und Abschluss werden hier nicht gesetzt** -- sie stehen auf
    dem Strich, bis eine Durchsicht sie vergibt. Das ist keine
    Sparsamkeit: An einer rohen Beobachtung arbeitet niemand, und ein
    Formular, das nach der Priorität fragt, verlangt eine Entscheidung
    von jemandem, der gerade nur etwas bemerkt hat.
    """
    spalten = {k: v for k, v in weitere.items() if k in TOPIC_TEXTE}
    namen = ["projekt_id", "titel", "bereich_id", "eingetragen_am",
             "kategorie"] + list(spalten)
    werte = [projekt_id, titel.strip(), bereich_id, eingetragen_am,
             kategorie] + [v.strip() for v in spalten.values()]
    with conn:
        cur = conn.execute(
            "INSERT INTO topics (%s) VALUES (%s)"
            % (", ".join(namen), ", ".join("?" * len(namen))), werte)
    return int(cur.lastrowid)


def topic_aendern(conn: sqlite3.Connection, topic_id: int,
                  **felder) -> None:
    """Einzelne Felder eines Eintrags. Unbekannte Namen fliegen raus."""
    setzen = {k: v for k, v in felder.items() if k in TOPIC_AENDERBAR}
    if not setzen:
        return
    with conn:
        conn.execute(
            "UPDATE topics SET %s WHERE id = ?"
            % ", ".join("%s = ?" % k for k in setzen),
            (*setzen.values(), topic_id))


def topic_abschliessen(conn: sqlite3.Connection, topic_id: int, art: str,
                       am: str | None = None) -> None:
    """Einen Eintrag abschliessen -- *verworfen* oder *aufgabe*.

    **Der Unterschied geht leicht verloren und ist der wichtige:**
    ``verworfen`` bekommt eine Zeile im Quittungsbuch, ``aufgabe``
    nicht -- *es ist nicht fertig, es zieht um.* Deshalb steht hier auch
    keine Unterscheidung im Code: Beide setzen dasselbe Feld, und das
    Quittungsbuch liest es. Wer die Zeile aus dem Abschluss ableitet,
    kann sie nicht vergessen.
    """
    if art not in ABSCHLUESSE:
        raise ValueError("kein Abschluss dieser Art: %r" % art)
    with conn:
        conn.execute("UPDATE topics SET abschluss = ?, abschluss_am = ? "
                     "WHERE id = ?", (art, am or heute(), topic_id))


def durchsicht_vermerken(conn: sqlite3.Connection, projekt_id: int,
                         am: str | None = None) -> None:
    """Festhalten, dass jemand hingesehen hat.

    **Auch dann, wenn nichts passiert ist.** Eine Durchsicht, bei der
    alles so bleibt, ist eine Durchsicht -- und die Zahl *seit der
    letzten Durchsicht* misst das Hinsehen, nicht das Ändern. Aus dem
    Bestand allein wäre das nie abzulesen.
    """
    with conn:
        conn.execute("UPDATE projekte SET durchsicht_am = ? WHERE id = ?",
                     (am or heute(), projekt_id))


def zusammenlegen(conn: sqlite3.Connection, projekt_id: int,
                  topic_ids: list[int], titel: str, dahinter: str,
                  abnahme: list[str], arbeit: list[str] | None = None) -> int:
    """Aus markierten Eintraegen eine Aufgabe machen.

    **Die Kernfunktion des Produkts** (Einordnung, Abschnitt 7): *ein
    Knopf, der zwei oder drei markierte Eintraege zu einer Aufgabe macht
    und dabei nach dem gemeinsamen Bild fragt.* Er nimmt auch einen
    einzigen -- *Zusammenlegen ist der haeufige Fall, nicht der einzige.*

    **Er fragt nach ZWEIERLEI: dem gemeinsamen Bild und der Abnahme** --
    und zwar in dem Augenblick, in dem das Denken gerade stattgefunden
    hat. Das ist die einzige Gelegenheit, zu der beides billig ist; die
    Abnahme spaeter nachzufordern hiesse, sie nie zu bekommen. Ohne sie
    wird nicht angelegt (siehe ``aufgabe_anlegen``).

    **Die Prioritaet ist die staerkste der Einzelnen.** Wer drei
    Eintraege buendelt, von denen einer MUSS ist, hat eine MUSS-Aufgabe
    -- die schwaechste zu nehmen liesse die Dringlichkeit im Buendeln
    verschwinden.

    **Der Bereich ist der des ersten.** Ein Buendel ueber zwei Bereiche
    hinweg gibt es, und dann ist die Wahl eine Setzung; sie steht danach
    an der Aufgabe und laesst sich dort aendern.
    """
    if not topic_ids:
        raise ValueError("ohne Eintraege gibt es nichts zusammenzulegen")
    fragezeichen = ",".join("?" * len(topic_ids))
    quelle = conn.execute(
        "SELECT id, bereich_id, prio FROM topics "
        "WHERE projekt_id = ? AND id IN (%s) ORDER BY id" % fragezeichen,
        (projekt_id, *topic_ids)).fetchall()
    if len(quelle) != len(topic_ids):
        raise ValueError("ein Eintrag gehoert nicht zu diesem Projekt")

    rang = {"MUSS": 0, "SOLL": 1, "KANN": 2, STRICH: 3}
    prio = min((z["prio"] for z in quelle), key=lambda p: rang.get(p, 3))

    return aufgabe_anlegen(
        conn, projekt_id, titel, quelle[0]["bereich_id"], heute(),
        abnahme=abnahme, arbeit=arbeit, prio=prio, dahinter=dahinter,
        topic_ids=[z["id"] for z in quelle])


def sammlung_zahlen(conn: sqlite3.Connection, projekt_id: int) -> dict:
    """Die Zahlen der Karten *Sammlungsübersicht* und *Was am längsten
    liegt*.

    Sie speisen dieselbe Quelle wie die Liegeprobe -- nur läuft die über
    alle Projekte, und diese Karten über das gewählte. ``offen`` zählt
    alle, ungefiltert: Die Übersicht sagt, wie viele es gibt, nicht wie
    viele die Suche gerade zeigt.
    """
    offen = topics(conn, projekt_id)
    ohne = [t for t in offen if t["prio"] == STRICH]
    tage = [t["liegt_seit"] for t in ohne if t["liegt_seit"] is not None]
    zeile = conn.execute("SELECT durchsicht_am FROM projekte WHERE id = ?",
                         (projekt_id,)).fetchone()
    return {
        "offen": len(offen),
        "ohne_prio": len(ohne),
        "aeltester": max(tage) if tage else None,
        "luecken": len([t for t in offen if t["fehlt"]]),
        "durchsicht_her": tage_seit(zeile["durchsicht_am"] if zeile else ""),
    }


# ==================================================================== #
# Aufgaben (A-)
# ==================================================================== #

STATUS = ("PASSIV", "AKTIV", "PAUSE")
AUFGABE_ABSCHLUESSE = ("erledigt", "verworfen", "meilenstein", STRICH)
PUNKT_ARTEN = ("ARBEIT", "ABNAHME")

NACHZUEGLER.update({
    # Wie bei den Topics: Ohne das Datum kann das Quittungsbuch keine
    # Zeile schreiben.
    "aufgaben": {"abschluss_am": "TEXT NOT NULL DEFAULT ''"},
})

AUFGABE_TEXTE = ("dahinter", "bedacht", "ergebnis")
AUFGABE_AENDERBAR = ("titel", "bereich_id", "prio", "status", "status_seit",
                     "eingetragen_am", "meilenstein_id") + AUFGABE_TEXTE


def zeilen(text: str) -> list[str]:
    """Ein Textfeld in Punkte zerlegen -- eine Zeile, ein Punkt.

    **Das ist die Bauform der Abnahme, und sie folgt einer Zahl:** Die
    Regel verlangt, dass sie *in dreissig Sekunden zu tippen* ist. Fuenf
    Felder mit einem Hinzufuegen-Knopf waeren dieselbe Liste und dreimal
    so lang -- und eine Regel, deren Weg teuer ist, wird umgangen.

    Leerzeilen fallen weg: Wer zwischen zwei Punkten eine Zeile frei
    laesst, meint keinen leeren Punkt.
    """
    return [z.strip() for z in (text or "").splitlines() if z.strip()]


def _aufgabe_ausbauen(conn: sqlite3.Connection, a: dict) -> dict:
    a["kennung"] = kennung("A", a["id"])
    a["eingetragen_deutsch"] = datum_zeigen(a["eingetragen_am"])
    a["seit_deutsch"] = datum_zeigen(a["status_seit"])
    # **Hier misst eingetragen_am die ARBEITSDAUER**, in der Sammlung
    # dasselbe Feld die Liegedauer. Zwei Fragen, ein Feld.
    a["arbeitet_seit"] = tage_seit(a["eingetragen_am"])

    punkte = [dict(z) for z in conn.execute(
        "SELECT id, art, folge, text, erledigt_am FROM aufgabe_punkte "
        "WHERE aufgabe_id = ? ORDER BY art, folge, id", (a["id"],))]
    for p in punkte:
        p["erledigt"] = p["erledigt_am"] != STRICH and bool(p["erledigt_am"])
        p["erledigt_deutsch"] = datum_zeigen(p["erledigt_am"])
    a["arbeit"] = [p for p in punkte if p["art"] == "ARBEIT"]
    a["abnahme"] = [p for p in punkte if p["art"] == "ABNAHME"]
    a["arbeit_fertig"] = len([p for p in a["arbeit"] if p["erledigt"]])
    a["abnahme_fertig"] = len([p for p in a["abnahme"] if p["erledigt"]])

    # **Der Knopf Erledigt haengt an der ABNAHME, nicht an der Arbeit.**
    # Die eine misst, wie weit es ist; die andere, ob es fertig ist.
    a["abnehmbar"] = bool(a["abnahme"]) and a["abnahme_fertig"] == len(a["abnahme"])

    # Der Ursprung ist ein VERWEIS, keine Kopie: gespeichert ist die
    # Kennung, der Titel wird hier geholt. In der Mappe kostet dieselbe
    # Regel ein Pruefskript mit 206 Zeilen; in einer Datenbank gibt es
    # keine zweite Fassung, die veralten koennte.
    # Der Meilenstein, dem sie zugeschlagen ist -- als Verweis, nicht als
    # Kopie. Bis zum 07.09.2026 stand hier ein Strich mit dem Satz, dass
    # es den Reiter noch nicht gibt.
    a["meilenstein"] = None
    if a["meilenstein_id"]:
        z = conn.execute("SELECT id, benennung FROM meilensteine WHERE id = ?",
                         (a["meilenstein_id"],)).fetchone()
        if z:
            a["meilenstein"] = {"id": z["id"],
                                "kennung": kennung("M", z["id"]),
                                "benennung": z["benennung"]}

    a["ursprung"] = [{
        "id": z["id"], "kennung": kennung("B", z["id"]), "titel": z["titel"],
    } for z in conn.execute("""
        SELECT t.id, t.titel FROM aufgabe_ursprung u
        JOIN topics t ON t.id = u.topic_id
        WHERE u.aufgabe_id = ? ORDER BY t.id""", (a["id"],))]
    return a


def aufgaben(conn: sqlite3.Connection, projekt_id: int, suche: str = "",
             offen_nur: bool = True) -> list[dict]:
    """Die Aufgaben eines Projekts.

    **Sortiert nach dem Status, dann nach der Kennung:** AKTIV zuerst,
    dann PAUSE, dann PASSIV. Anders als in der Sammlung ist die Frage
    hier nicht *was ist neu*, sondern *woran sitzt gerade jemand* -- und
    das ist die eine Zeile, wegen der jemand diesen Reiter aufmacht.
    """
    wo = ["a.projekt_id = ?"]
    werte: list = [projekt_id]
    if offen_nur:
        wo.append("a.abschluss = ?")
        werte.append(STRICH)
    if suche.strip():
        wie = "%" + suche.strip() + "%"
        wo.append("(a.titel LIKE ? OR a.dahinter LIKE ?)")
        werte.extend([wie, wie])

    zeilen_ = conn.execute("""
        SELECT a.*, b.wert AS bereich
        FROM aufgaben a JOIN bereiche b ON b.id = a.bereich_id
        WHERE %s
        ORDER BY CASE a.status WHEN 'AKTIV' THEN 0 WHEN 'PAUSE' THEN 1
                               ELSE 2 END, a.id DESC
    """ % " AND ".join(wo), werte).fetchall()
    return [_aufgabe_ausbauen(conn, dict(z)) for z in zeilen_]


def aufgabe(conn: sqlite3.Connection, aufgabe_id: int) -> dict | None:
    z = conn.execute("""
        SELECT a.*, b.wert AS bereich
        FROM aufgaben a JOIN bereiche b ON b.id = a.bereich_id
        WHERE a.id = ?""", (aufgabe_id,)).fetchone()
    return _aufgabe_ausbauen(conn, dict(z)) if z else None


def aufgabe_anlegen(conn: sqlite3.Connection, projekt_id: int, titel: str,
                    bereich_id: int, eingetragen_am: str,
                    abnahme: list[str], arbeit: list[str] | None = None,
                    prio: str = STRICH, dahinter: str = "",
                    topic_ids: list[int] | None = None) -> int:
    """Eine Aufgabe. Gibt ihre Kennungsnummer zurueck.

    **OHNE ABNAHME WIRD SIE NICHT ANGELEGT** -- das ist die eine Sperre
    dieses Produkts, und sie ist begruendet: *Eine Aufgabe ohne Abnahme
    ist keine unvollstaendige Aufgabe, sondern eine Beobachtung mit
    Kopfzeile.*

    **Der Unterschied zu den fuenf Fehlerangaben ist kein Widerspruch,
    sondern die Grenze zwischen zwei Arten von Pflichtfeld:** Die
    Fehlerangaben machen einen Eintrag vollstaendiger. Die Abnahme macht
    ihn erst zu dem, was er ist.

    ``dahinter`` sperrt dagegen NICHT, obwohl die Regel es ebenfalls
    Pflicht nennt: Die Ursache kann man nachtragen, sobald man sie
    versteht. *Sperren gehoert zu dem, was nicht nachwachsen kann.* Ein
    leeres Feld wird stattdessen ein Befund.

    ``topic_ids`` schliesst die Eintraege ab, aus denen sie entsteht --
    mit dem Abschluss *aufgabe*: **Es ist nicht fertig, es zieht um.**
    """
    if not abnahme:
        raise ValueError(
            "Ohne Abnahme ist es keine Aufgabe. Laesst sie sich nicht "
            "beschreiben, gehoert die Sache zurueck in die Sammlung.")
    tag = heute()
    with conn:
        cur = conn.execute("""
            INSERT INTO aufgaben (projekt_id, titel, bereich_id, prio,
                                  eingetragen_am, dahinter)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (projekt_id, titel.strip(), bereich_id, prio, eingetragen_am,
             dahinter.strip()))
        neu = int(cur.lastrowid)
        for art, texte in (("ABNAHME", abnahme), ("ARBEIT", arbeit or [])):
            for folge, text in enumerate(texte, start=1):
                conn.execute(
                    "INSERT INTO aufgabe_punkte (aufgabe_id, art, folge, text)"
                    " VALUES (?, ?, ?, ?)", (neu, art, folge, text))
        for topic_id in topic_ids or []:
            conn.execute("INSERT INTO aufgabe_ursprung (aufgabe_id, topic_id) "
                         "VALUES (?, ?)", (neu, topic_id))
            conn.execute("UPDATE topics SET abschluss = 'aufgabe', "
                         "abschluss_am = ? WHERE id = ?", (tag, topic_id))
    return neu


def aufgabe_aendern(conn: sqlite3.Connection, aufgabe_id: int,
                    **felder) -> None:
    """Einzelne Felder. Unbekannte Namen fliegen raus.

    **Status und Datum gehoeren zusammen und werden deshalb zusammen
    geschrieben.** Die Ablage laesst AKTIV oder PAUSE ohne Datum gar
    nicht zu (CHECK); wer nur eines von beiden setzte, liefe in einen
    IntegrityError statt in eine Meldung.
    """
    setzen = {k: v for k, v in felder.items() if k in AUFGABE_AENDERBAR}
    if not setzen:
        return
    # Ein leeres Feld heisst KEIN Meilenstein und nicht die Nummer null:
    # Die Spalte ist ein Fremdschluessel, und "" liefe in einen Fehler
    # ueber eine Kennung, die es nicht gibt.
    if setzen.get("meilenstein_id") in ("", "0"):
        setzen["meilenstein_id"] = None
    if setzen.get("status") == "PASSIV":
        # An einer passiven Aufgabe sitzt niemand -- dann gibt es kein
        # Seit, und ein stehengebliebenes Datum waere eine Behauptung.
        setzen["status_seit"] = STRICH
    with conn:
        conn.execute(
            "UPDATE aufgaben SET %s WHERE id = ?"
            % ", ".join("%s = ?" % k for k in setzen),
            (*setzen.values(), aufgabe_id))


def punkt_anlegen(conn: sqlite3.Connection, aufgabe_id: int, art: str,
                  text: str) -> int:
    """Eine Zeile an eine der beiden Listen."""
    if art not in PUNKT_ARTEN:
        raise ValueError("keine Punktart: %r" % art)
    with conn:
        folge = conn.execute(
            "SELECT COALESCE(MAX(folge), 0) + 1 FROM aufgabe_punkte "
            "WHERE aufgabe_id = ? AND art = ?", (aufgabe_id, art)).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO aufgabe_punkte (aufgabe_id, art, folge, text) "
            "VALUES (?, ?, ?, ?)", (aufgabe_id, art, folge, text.strip()))
    return int(cur.lastrowid)


def punkt_haken(conn: sqlite3.Connection, punkt_id: int, gesetzt: bool,
                am: str | None = None) -> None:
    """Einen Haken setzen oder wegnehmen.

    **Erledigtes wird nicht geloescht, es bekommt ein Datum.** In der
    Mappe ist das ein Textkniff -- ``[erledigt]`` mit Tag --, weil der
    Editor Tilden nicht rendert. Hier ist es ein Zustand je Zeile, und
    genau das sagt docs/datenhaltung.md voraus.
    """
    with conn:
        conn.execute("UPDATE aufgabe_punkte SET erledigt_am = ? WHERE id = ?",
                     ((am or heute()) if gesetzt else STRICH, punkt_id))


def punkt_text(conn: sqlite3.Connection, punkt_id: int, text: str) -> None:
    """Den Text einer Zeile aendern -- Haken und Datum bleiben.

    **Bis zum 19.09.2026 ging das nur ueber Wegnehmen und neu Anlegen**,
    und dabei ging der Haken samt Datum verloren: Wer einen Tippfehler in
    einer erledigten Zeile behob, machte sie wieder offen.
    """
    with conn:
        conn.execute("UPDATE aufgabe_punkte SET text = ? WHERE id = ?",
                     (text.strip(), punkt_id))


def punkt_loeschen(conn: sqlite3.Connection, punkt_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM aufgabe_punkte WHERE id = ?", (punkt_id,))


def aufgabe_abschliessen(conn: sqlite3.Connection, aufgabe_id: int, art: str,
                         am: str | None = None) -> None:
    """Eine Aufgabe abschliessen -- erledigt, verworfen oder Meilenstein.

    Diese Funktion prueft die Abnahme NICHT: Sie ist die Ablage, nicht
    die Oberflaeche. Ob *erledigt* ueberhaupt angeboten wird, entscheidet
    ``abnehmbar`` an der Aufgabe -- und das haengt an der Abnahmeliste,
    nicht an der Arbeitsliste.
    """
    if art not in AUFGABE_ABSCHLUESSE:
        raise ValueError("kein Abschluss dieser Art: %r" % art)
    with conn:
        conn.execute("UPDATE aufgaben SET abschluss = ?, abschluss_am = ? "
                     "WHERE id = ?", (art, am or heute(), aufgabe_id))


# ==================================================================== #
# Meilensteine (M-)
# ==================================================================== #

MEILENSTEIN_ABSCHLUESSE = ("erledigt", "verworfen", STRICH)

MEILENSTEIN_TEXTE = ("beschreibung", "bedingung", "nachbereitung",
                     "abnahme_kriterium")
MEILENSTEIN_AENDERBAR = ("benennung", "prio", "eingetragen_am") \
    + MEILENSTEIN_TEXTE


def _stein_ausbauen(conn: sqlite3.Connection, m: dict) -> dict:
    m["kennung"] = kennung("M", m["id"])
    m["eingetragen_deutsch"] = datum_zeigen(m["eingetragen_am"])
    m["abnahme_deutsch"] = datum_zeigen(m["abnahme_am"])
    m["offen_seit"] = tage_seit(m["eingetragen_am"])

    # **Vorgaenger sind eingetragen, Nachfolger abgelesen.** Beides zu
    # speichern hiesse, dieselbe Beziehung zweimal zu halten -- und eine
    # der beiden Fassungen waere in einem Monat falsch.
    m["vorgaenger"] = _steinverweise(conn, """
        SELECT m.id, m.benennung FROM meilenstein_vorgaenger v
        JOIN meilensteine m ON m.id = v.vorgaenger_id
        WHERE v.meilenstein_id = ? ORDER BY m.id""", m["id"])
    m["nachfolger"] = _steinverweise(conn, """
        SELECT m.id, m.benennung FROM meilenstein_vorgaenger v
        JOIN meilensteine m ON m.id = v.meilenstein_id
        WHERE v.vorgaenger_id = ? ORDER BY m.id""", m["id"])

    m["aufgaben"] = [{
        "id": z["id"], "kennung": kennung("A", z["id"]), "titel": z["titel"],
        "status": z["status"], "abschluss": z["abschluss"],
        "fertig": z["abschluss"] == "erledigt",
    } for z in conn.execute(
        "SELECT id, titel, status, abschluss FROM aufgaben "
        "WHERE meilenstein_id = ? ORDER BY id", (m["id"],))]
    m["aufgaben_fertig"] = len([a for a in m["aufgaben"] if a["fertig"]])

    m["dazwischen"] = [{
        "id": z["id"], "datum": z["datum"],
        "datum_deutsch": datum_zeigen(z["datum"]), "text": z["text"],
    } for z in conn.execute(
        "SELECT id, datum, text FROM meilenstein_dazwischen "
        "WHERE meilenstein_id = ? ORDER BY datum, id", (m["id"],))]

    # **Abnehmbar ist er, wenn jede zugeschlagene Aufgabe erledigt ist --
    # und wenn ueberhaupt eine daranhaengt.** Ein Meilenstein ohne
    # Aufgabe ist keiner; abzunehmen gaebe es dort nichts.
    m["abnehmbar"] = bool(m["aufgaben"]) \
        and m["aufgaben_fertig"] == len(m["aufgaben"])
    # Er darf leer entstehen, aber nicht leer bleiben: kein Sperren,
    # ein Befund.
    m["ohne_aufgabe"] = not m["aufgaben"]
    return m


def _steinverweise(conn: sqlite3.Connection, sql: str, wert: int) -> list[dict]:
    return [{"id": z["id"], "kennung": kennung("M", z["id"]),
             "benennung": z["benennung"]}
            for z in conn.execute(sql, (wert,))]


def meilensteine(conn: sqlite3.Connection, projekt_id: int,
                 offen_nur: bool = True) -> list[dict]:
    """Die Meilensteine eines Projekts.

    **``offen_nur`` ist Regel 7, umgedreht.** In der Mappe verschwindet
    ein abgenommener Meilenstein aus der Datei -- *eine Liste, die
    mitwaechst statt zu schrumpfen, verliert ihren Zweck.* In einer
    Datenbank verschwindet nichts; der Zweck bleibt und wird ein
    Vorgabefilter.
    """
    wo = "projekt_id = ?"
    werte: list = [projekt_id]
    if offen_nur:
        wo += " AND abschluss = ?"
        werte.append(STRICH)
    return [_stein_ausbauen(conn, dict(z)) for z in conn.execute(
        "SELECT * FROM meilensteine WHERE %s ORDER BY id" % wo, werte)]


def meilenstein(conn: sqlite3.Connection, stein_id: int) -> dict | None:
    z = conn.execute("SELECT * FROM meilensteine WHERE id = ?",
                     (stein_id,)).fetchone()
    return _stein_ausbauen(conn, dict(z)) if z else None


def meilenstein_anlegen(conn: sqlite3.Connection, projekt_id: int,
                        benennung: str, eingetragen_am: str,
                        prio: str = STRICH, **texte: str) -> int:
    """Ein Meilenstein. Gibt seine Kennungsnummer zurueck.

    **ER DARF LEER ENTSTEHEN.** Ein Meilenstein aus einer Rueckmeldung
    oder einer Entscheidung im Gespraech ist ein echter Fall -- hier wird
    nichts gesperrt. Dass er leer nicht BLEIBEN darf, ist ein Befund und
    keine Sperre: *Sperren gehoert zu dem, was nicht nachwachsen kann;
    mahnen zu dem, was nachwaechst.*

    Der Unterschied zur Abnahme der Aufgabe ist damit sauber: Dort fehlt
    etwas, das den Eintrag konstituiert; hier etwas, das noch kommt.
    """
    spalten = {k: v.strip() for k, v in texte.items()
               if k in MEILENSTEIN_TEXTE}
    namen = ["projekt_id", "benennung", "eingetragen_am", "prio"] \
        + list(spalten)
    werte = [projekt_id, benennung.strip(), eingetragen_am, prio] \
        + list(spalten.values())
    with conn:
        cur = conn.execute(
            "INSERT INTO meilensteine (%s) VALUES (%s)"
            % (", ".join(namen), ", ".join("?" * len(namen))), werte)
    return int(cur.lastrowid)


def meilenstein_aendern(conn: sqlite3.Connection, stein_id: int,
                        **felder) -> None:
    setzen = {k: v for k, v in felder.items() if k in MEILENSTEIN_AENDERBAR}
    if not setzen:
        return
    with conn:
        conn.execute(
            "UPDATE meilensteine SET %s WHERE id = ?"
            % ", ".join("%s = ?" % k for k in setzen),
            (*setzen.values(), stein_id))


def _haengt_ab_von(conn: sqlite3.Connection, stein_id: int) -> set[int]:
    """Alle Steine, von denen dieser mittelbar abhaengt."""
    gefunden: set[int] = set()
    offen = [stein_id]
    while offen:
        jetzt = offen.pop()
        for z in conn.execute("SELECT vorgaenger_id FROM meilenstein_vorgaenger"
                              " WHERE meilenstein_id = ?", (jetzt,)):
            if z[0] not in gefunden:
                gefunden.add(z[0])
                offen.append(z[0])
    return gefunden


def vorgaenger_setzen(conn: sqlite3.Connection, stein_id: int,
                      vorgaenger: list[int]) -> None:
    """Wovon dieser Meilenstein abhaengt.

    **Ein Kreis wird abgewiesen.** Die Ablage verbietet nur den direkten
    Fall (``CHECK meilenstein_id <> vorgaenger_id``); A haengt von B und
    B von A liesse sie durch. Fuer die Anzeige ist das keine Feinheit:
    *Haengt ab von* und *Wartet auf ihn* zeigten dann aufeinander, und
    keine der beiden Auskuenfte waere noch wahr.
    """
    for kandidat in vorgaenger:
        if kandidat == stein_id:
            raise ValueError("Ein Meilenstein haengt nicht von sich selbst ab.")
        if stein_id in _haengt_ab_von(conn, kandidat):
            raise ValueError(
                "%s haengt schon von %s ab -- das gaebe einen Kreis."
                % (kennung("M", kandidat), kennung("M", stein_id)))
    with conn:
        conn.execute("DELETE FROM meilenstein_vorgaenger "
                     "WHERE meilenstein_id = ?", (stein_id,))
        for kandidat in vorgaenger:
            conn.execute("INSERT INTO meilenstein_vorgaenger "
                         "(meilenstein_id, vorgaenger_id) VALUES (?, ?)",
                         (stein_id, kandidat))


def aufgabe_zuschlagen(conn: sqlite3.Connection, aufgabe_id: int,
                       stein_id: int | None) -> None:
    """Eine Aufgabe einem Meilenstein zuschlagen -- oder wieder loesen.

    ``None`` loest sie. **Geloescht wird dabei nichts:** Die Aufgabe
    bleibt, sie gehoert nur nicht mehr dazu.
    """
    with conn:
        conn.execute("UPDATE aufgaben SET meilenstein_id = ? WHERE id = ?",
                     (stein_id, aufgabe_id))


def dazwischen_anlegen(conn: sqlite3.Connection, stein_id: int, datum: str,
                       text: str) -> int:
    """Ein Umweg. **Notiert, sobald es passiert -- nicht bei der Abnahme.**

    Deshalb traegt jede Zeile ihr eigenes Datum und nicht das der
    Abnahme, und deshalb ist der Weg dorthin kurz: eine Karte oben auf
    dem Reiter, drei Felder. Eine Notiz, die man im Augenblick machen
    soll, aber erst suchen muss, wird aus dem Gedaechtnis nachgetragen --
    und dann ist sie wertlos.

    **Es gibt nur den Umweg**, seit dem 07.09.2026: Die zweite Art der
    Mappe, die Rast, ist gestrichen -- die Unterscheidung war zu
    fliessend, um etwas zu sortieren.
    """
    with conn:
        cur = conn.execute(
            "INSERT INTO meilenstein_dazwischen (meilenstein_id, datum, text) "
            "VALUES (?, ?, ?)", (stein_id, datum, text.strip()))
    return int(cur.lastrowid)


def dazwischen_loeschen(conn: sqlite3.Connection, zeilen_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM meilenstein_dazwischen WHERE id = ?",
                     (zeilen_id,))


def meilenstein_abnehmen(conn: sqlite3.Connection, stein_id: int,
                         am: str | None = None) -> None:
    """Die Abnahme -- vier Handgriffe in einem.

    Heute sind es vier, und jeder laesst sich einzeln vergessen:
    ``Abschluss: erledigt`` setzen, ``archiviere.py --verschieben``
    laufen lassen, eine Zeile ins Quittungsbuch schreiben, einen Stein
    auf die Roadmap setzen -- mit Dauer und *Was dazwischenkam*.

    **Hier ist es einer**, und die drei anderen fallen ab statt getan zu
    werden: Die Dauer rechnet sich aus ``eingetragen_am`` und
    ``abnahme_am``, das Quittungsbuch liest den Abschluss, und *Was
    dazwischenkam* steht schon da, weil es notiert wurde, als es
    passierte. **Wo eine Regel Formalie verlangt, muss das Werkzeug sie
    uebernehmen. Sonst wird die Regel umgangen.**

    Diese Funktion prueft nicht, ob alle Aufgaben erledigt sind: Sie ist
    die Ablage, nicht die Oberflaeche. ``abnehmbar`` am Stein sagt es.
    """
    tag = am or heute()
    with conn:
        # Zwei Daten, und sie sagen Verschiedenes: abnahme_am heisst
        # ABGENOMMEN und bleibt bei einem verworfenen Stein leer;
        # abschluss_am heisst, dass er die Liste verlassen hat. Beim
        # Abnehmen fallen sie auf denselben Tag -- beim Verwerfen gibt es
        # nur das zweite.
        conn.execute("UPDATE meilensteine SET abschluss = 'erledigt', "
                     "abnahme_am = ?, abschluss_am = ? WHERE id = ?",
                     (tag, tag, stein_id))


def meilenstein_verwerfen(conn: sqlite3.Connection, stein_id: int,
                          am: str | None = None) -> None:
    """Verworfen -- er wird nie gebaut.

    **Die Aufgaben darunter bleiben, wo sie sind.** Ein verworfener
    Meilenstein sagt nichts darueber, ob die Arbeit noch zu tun ist; sie
    hat nur keinen gemeinsamen Termin mehr. Sie gehen deshalb zurueck in
    die Liste der Aufgaben ohne Stein, statt mitverworfen zu werden.
    """
    with conn:
        conn.execute("UPDATE aufgaben SET meilenstein_id = NULL "
                     "WHERE meilenstein_id = ?", (stein_id,))
        # abnahme_am bleibt leer: Er wurde nicht abgenommen, er faellt
        # weg. Das Datum sagt nur, wann er die Liste verlassen hat --
        # ohne es kann das Quittungsbuch keine Zeile schreiben.
        conn.execute("UPDATE meilensteine SET abschluss = 'verworfen', "
                     "abschluss_am = ? WHERE id = ?",
                     (am or heute(), stein_id))


# ==================================================================== #
# Entscheidungen (E-)
# ==================================================================== #
#
# **Das einzige Register ohne Feldschema.** *Eine Abwaegung hat keine
# Form, die sich vorher festlegen liesse; sie hat einen Verlauf.* Ein
# Schema wuerde genau das plaetten, woran man die Gruendlichkeit abliest:
# Achtzig geprueufte Woerter, drei Kandidaten und zwei verworfene Wege
# sehen in Feldern gepresst aus wie eine Zeile.

ENTSCHEIDUNGSZUSTAENDE = ("OFFEN", "ENTSCHLUSS")
BEZUG_ARTEN = ("B", "A", "M", STRICH)

# Wo ein Bezug hinzeigt: Buchstabe -> Tabelle, Titelspalte, Reiter.
BEZUG_ZIELE = {
    "B": ("topics", "titel", "Sammlung", "/sammlung?ansicht=eintragen"),
    "A": ("aufgaben", "titel", "Aufgaben", "/aufgaben"),
    "M": ("meilensteine", "benennung", "Meilensteine", "/meilensteine"),
}

NACHZUEGLER.update({
    # **Was entschieden wurde -- getrennt vom Verlauf.** Im September
    # 2026 so festgelegt: Wer eine Entscheidungskarte ansieht, will
    # zuerst sehen, was ueberhaupt entschieden wurde -- und kann dann im
    # Verlauf nachlesen, warum.
    #
    # Das widerspricht dem fehlenden Feldschema nicht: Ein Schema gaebe
    # dem VERLAUF eine Gliederung vor. Hier wird nur das Ergebnis vom Weg
    # getrennt -- zwei Dinge, die man zu verschiedenen Zeiten liest.
    "entscheidungen": {"entschluss": "TEXT NOT NULL DEFAULT ''"},
})

ENTSCHEIDUNG_AENDERBAR = ("titel", "zustand", "datum", "entschluss", "text")


def _bezugskopf(conn: sqlite3.Connection, art: str, ziel_id: int) -> dict | None:
    """Der Kopf des bezogenen Eintrags -- **zeigen statt kopieren**.

    Steht er neben der Entscheidung, gibt es keinen Anlass, den Stand in
    den Verlauf abzuschreiben: *Was gerade gilt, steht im Backlog; hier
    steht, warum es gilt.* Erzwingen laesst sich das nicht, erleichtern
    schon -- derselbe Griff wie bei der Verweis-Regel.
    """
    if art not in BEZUG_ZIELE or not ziel_id:
        return None
    tabelle, titelspalte, reiter, pfad = BEZUG_ZIELE[art]
    z = conn.execute("SELECT id, %s AS titel, abschluss FROM %s WHERE id = ?"
                     % (titelspalte, tabelle), (ziel_id,)).fetchone()
    if not z:
        return None
    return {
        "art": art, "id": z["id"], "kennung": kennung(art, z["id"]),
        "titel": z["titel"], "abschluss": z["abschluss"],
        "offen": z["abschluss"] == STRICH,
        "reiter": reiter, "pfad": "%s#eintrag-%d" % (pfad, z["id"]),
    }


def _entscheidung_ausbauen(conn: sqlite3.Connection, e: dict) -> dict:
    e["kennung"] = kennung("E", e["id"])
    e["datum_deutsch"] = datum_zeigen(e["datum"])
    e["seit"] = tage_seit(e["datum"])
    e["bezug"] = _bezugskopf(conn, e["bezug_art"], e["bezug_id"] or 0)

    # Der Umfang steht am Eintrag und nicht als Spalte in der Uebersicht:
    # Neben drei anderen liest er sich als Bewertung -- lang gleich
    # gruendlich, und das waere falsch.
    text = e["text"] or ""
    e["zeilen"] = len(text.splitlines()) if text.strip() else 0
    e["abschnitte"] = len([z for z in text.splitlines()
                           if z.lstrip().startswith("#")])

    # **Ein Entschluss ohne Satz ist keiner** -- und das mahnt, es
    # sperrt nicht: Den Satz kann man nachtragen, und sperren gehoert zu
    # dem, was nicht nachwachsen kann.
    e["ohne_satz"] = (e["zustand"] == "ENTSCHLUSS"
                      and not (e["entschluss"] or "").strip())
    # **Getroffen, und der Eintrag liegt trotzdem** -- das ist woertlich
    # die Liegeprobe aus der Einordnung und laut ihr der eigentliche
    # Nutzen dieses Registers.
    e["liegt"] = (e["zustand"] == "ENTSCHLUSS" and bool(e["bezug"])
                  and e["bezug"]["offen"])
    return e


def entscheidungen(conn: sqlite3.Connection, projekt_id: int,
                   suche: str = "", offen_nur: bool = False) -> list[dict]:
    """Die Entscheidungen eines Projekts.

    **Hier wird nichts archiviert.** Eine Entscheidung hat keinen
    Abschluss, sondern einen Zustand: Sie bleibt stehen, auch wenn der
    Eintrag, zu dem sie gehoert, laengst im Archiv ist -- das tut kein
    anderes Register. Deshalb ist die Vorgabe *alle* und nicht *offen*:
    Die haeufigste Frage hier ist *warum gilt das*, nicht *was ist noch
    zu tun*.
    """
    wo = ["projekt_id = ?"]
    werte: list = [projekt_id]
    if offen_nur:
        wo.append("zustand = 'OFFEN'")
    if suche.strip():
        wie = "%" + suche.strip() + "%"
        wo.append("(titel LIKE ? OR entschluss LIKE ? OR text LIKE ?)")
        werte.extend([wie, wie, wie])
    return [_entscheidung_ausbauen(conn, dict(z)) for z in conn.execute(
        "SELECT * FROM entscheidungen WHERE %s ORDER BY id DESC"
        % " AND ".join(wo), werte)]


def entscheidung(conn: sqlite3.Connection, e_id: int) -> dict | None:
    z = conn.execute("SELECT * FROM entscheidungen WHERE id = ?",
                     (e_id,)).fetchone()
    return _entscheidung_ausbauen(conn, dict(z)) if z else None


def entscheidung_anlegen(conn: sqlite3.Connection, projekt_id: int,
                         titel: str, datum: str, zustand: str = "OFFEN",
                         bezug_art: str = STRICH, bezug_id: int | None = None,
                         entschluss: str = "", text: str = "") -> int:
    """Eine Entscheidung. **Freistehend ist erlaubt.**

    Zwei Drittel der Entscheidungen in Boots Mappe haengen an nichts --
    das Feld *Bezug* darf deshalb wirklich leer bleiben, und die Ablage
    verlangt dann ausdruecklich auch keine Kennung (``CHECK``).
    """
    if zustand not in ENTSCHEIDUNGSZUSTAENDE:
        raise ValueError("diesen Zustand gibt es nicht: %r" % zustand)
    if bezug_art not in BEZUG_ARTEN:
        raise ValueError("diese Bezugsart gibt es nicht: %r" % bezug_art)
    if (bezug_art == STRICH) != (bezug_id is None):
        raise ValueError("Bezugsart und Kennung gehoeren zusammen.")
    with conn:
        cur = conn.execute("""
            INSERT INTO entscheidungen (projekt_id, titel, zustand, datum,
                                        bezug_art, bezug_id, entschluss, text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (projekt_id, titel.strip(), zustand, datum, bezug_art, bezug_id,
             entschluss.strip(), text))
    return int(cur.lastrowid)


def entscheidung_aendern(conn: sqlite3.Connection, e_id: int,
                         bezug: tuple[str, int | None] | None = None,
                         **felder) -> None:
    """Einzelne Felder. Der Bezug wird als Paar gesetzt, nie einzeln.

    Die Ablage verlangt beides zusammen (``CHECK (bezug_art = '—') =
    (bezug_id IS NULL)``); wer nur eines schriebe, liefe in einen
    IntegrityError statt in eine Meldung.
    """
    setzen = {k: v for k, v in felder.items() if k in ENTSCHEIDUNG_AENDERBAR}
    if bezug is not None:
        art, ziel = bezug
        if art not in BEZUG_ARTEN:
            raise ValueError("diese Bezugsart gibt es nicht: %r" % art)
        setzen["bezug_art"] = art
        setzen["bezug_id"] = ziel if art != STRICH else None
    if setzen.get("zustand") not in (None, *ENTSCHEIDUNGSZUSTAENDE):
        raise ValueError("diesen Zustand gibt es nicht")
    if not setzen:
        return
    with conn:
        conn.execute(
            "UPDATE entscheidungen SET %s WHERE id = ?"
            % ", ".join("%s = ?" % k for k in setzen),
            (*setzen.values(), e_id))


def entscheidung_loeschen(conn: sqlite3.Connection, e_id: int) -> None:
    """Eine Entscheidung wegwerfen.

    **Es ist das einzige Register, in dem geloescht statt archiviert
    wird** -- weil es hier kein Archiv gibt: Eine Entscheidung hat keinen
    Abschluss. Was falsch eingetragen wurde, muss deshalb wirklich weg.
    """
    with conn:
        conn.execute("DELETE FROM entscheidungen WHERE id = ?", (e_id,))


def bezug_auswahl(conn: sqlite3.Connection, projekt_id: int) -> list[dict]:
    """Woran sich eine Entscheidung haengen laesst -- eine Liste.

    **Ein Feld statt zweier:** Art und Kennung haengen zusammen, und zwei
    Auswahllisten, von denen die zweite von der ersten abhaengt, brauchen
    JavaScript, um nicht zu luegen. Die Vorlage gruppiert sie nach
    Register.
    """
    raus = []
    for art in ("B", "A", "M"):
        tabelle, titelspalte, reiter, _ = BEZUG_ZIELE[art]
        raus.append({"art": art, "reiter": reiter, "eintraege": [
            {"wert": "%s:%d" % (art, z["id"]),
             "kennung": kennung(art, z["id"]), "titel": z["titel"]}
            for z in conn.execute(
                "SELECT id, %s AS titel FROM %s WHERE projekt_id = ? "
                "ORDER BY id DESC" % (titelspalte, tabelle), (projekt_id,))]})
    return raus


def entscheidungs_zahlen(conn: sqlite3.Connection, projekt_id: int) -> dict:
    """Die drei Zahlen der Liegeprobe.

    **Zwei Zustaende, zwei Fragen** -- dieselbe Bauart wie beim
    Eintragsdatum, das in der Sammlung die Liegedauer und an der Aufgabe
    die Arbeitsdauer misst.
    """
    alle = entscheidungen(conn, projekt_id)
    offen = [e for e in alle if e["zustand"] == "OFFEN"]
    tage = [e["seit"] for e in offen if e["seit"] is not None]
    return {
        "gesamt": len(alle),
        "liegt": len([e for e in alle if e["liegt"]]),
        "offen": len(offen),
        "aelteste_offene": max(tage) if tage else None,
        "ohne_satz": len([e for e in alle if e["ohne_satz"]]),
    }


# ==================================================================== #
# History -- Strasse, Quittungsbuch, Archiv
# ==================================================================== #
#
# **Hier wird nichts eingetragen.** Der einzige Reiter, der nur zeigt:
# Jede Zeile faellt aus den fuenf Registern ab. In der Mappe sind es drei
# Dateien, die von Hand gepflegt werden, plus `archiviere.py`; hier sind
# es drei Abfragen.
#
# Die drei Ansichten sind die drei Dateien und beantworten drei
# verschiedene Fragen -- 02-roadmap (4 %), 06-erledigt (6 %), 07-archiv
# (43 %), zusammen 53 % des Bestands:
#
#   Strasse        Wie sind wir hierhergekommen?
#   Quittungsbuch  Was ist wann fertig geworden?
#   Archiv         Was stand da im Wortlaut?

NACHZUEGLER.update({
    # Wann ein Meilenstein die Liste verlassen hat. **Nicht dasselbe wie
    # abnahme_am:** Das sagt, dass er ABGENOMMEN wurde, und bleibt bei
    # einem verworfenen leer. Ohne die zweite Spalte haette ein
    # verworfener Stein kein Datum, und das Quittungsbuch kann ohne
    # Datum keine Zeile schreiben.
    "meilensteine": {"abschluss_am": "TEXT NOT NULL DEFAULT ''"},
})


def strasse(conn: sqlite3.Connection, projekt_id: int) -> list[dict]:
    """Die abgenommenen Meilensteine in der Reihenfolge ihrer Abnahme.

    **Auf den Stein kommt, was getan wurde -- nicht, was vorhatte, wer
    ihn eintrug.** Beschreibung, Bedingung und Abnahmekriterium stehen im
    Archiv; hier stehen Dauer und was dazwischenkam.

    Beides faellt ab: die Dauer aus den zwei Daten, die Umwege aus dem,
    was notiert wurde, als es passierte. In der Mappe wird beides von
    Hand auf den Stein geschrieben.
    """
    steine = []
    for z in conn.execute(
            "SELECT * FROM meilensteine WHERE projekt_id = ? "
            "AND abschluss = 'erledigt' ORDER BY abnahme_am, id",
            (projekt_id,)):
        m = _stein_ausbauen(conn, dict(z))
        m["abnahme_deutsch"] = datum_zeigen(m["abnahme_am"])
        m["dauer"] = _tage_zwischen(m["eingetragen_am"], m["abnahme_am"])
        steine.append(m)
    return steine


def _tage_zwischen(von: str, bis: str) -> int | None:
    """Wie viele Tage zwischen zwei Daten liegen -- oder None."""
    try:
        return (date.fromisoformat(bis) - date.fromisoformat(von)).days
    except (ValueError, TypeError):
        return None


# Woraus das Quittungsbuch seine Zeilen zieht: Register, Tabelle,
# Titelspalte, Buchstabe -- und welche Abschluesse eine Zeile bekommen.
#
# **DER UNTERSCHIED, DER LEICHT VERLOREN GEHT:** `verworfen` bekommt eine
# Zeile, `aufgabe` nicht -- *es ist nicht fertig, es zieht um.* Ein
# Eintrag der Sammlung, aus dem eine Aufgabe wurde, steht deshalb nicht
# im Quittungsbuch; seine Zeile schreibt die Aufgabe, wenn sie fertig
# ist. Dasselbe gilt fuer eine Aufgabe, die in einem Meilenstein
# aufgeht.
QUITTUNGSFAELLE = (
    ("B", "topics", "titel", "Sammlung", ("verworfen",)),
    ("A", "aufgaben", "titel", "Aufgaben", ("erledigt", "verworfen")),
    ("M", "meilensteine", "benennung", "Meilensteine",
     ("erledigt", "verworfen")),
)


def quittungsbuch(conn: sqlite3.Connection, projekt_id: int,
                  suche: str = "") -> list[dict]:
    """Eine Zeile je Eintrag, mehr soll es nicht sein.

    **Nach dem Abschlussdatum sortiert, das Juengste oben** -- die Frage
    ist *was ist zuletzt fertig geworden* und nicht *in welcher
    Reihenfolge wurde es eingetragen*.
    """
    zeilen = []
    for art, tabelle, titelspalte, register, abschluesse in QUITTUNGSFAELLE:
        fragezeichen = ",".join("?" * len(abschluesse))
        for z in conn.execute(
                "SELECT id, %s AS titel, abschluss, abschluss_am, "
                "eingetragen_am FROM %s WHERE projekt_id = ? "
                "AND abschluss IN (%s)" % (titelspalte, tabelle, fragezeichen),
                (projekt_id, *abschluesse)):
            if suche.strip() and suche.strip().lower() not in z["titel"].lower():
                continue
            zeilen.append({
                "art": art, "id": z["id"], "kennung": kennung(art, z["id"]),
                "titel": z["titel"], "register": register,
                "abschluss": z["abschluss"],
                "eingetragen_am": z["eingetragen_am"],
                "eingetragen_deutsch": datum_zeigen(z["eingetragen_am"]),
                "fertig_am": z["abschluss_am"],
                "fertig_deutsch": datum_zeigen(z["abschluss_am"]),
                "dauer": _tage_zwischen(z["eingetragen_am"], z["abschluss_am"]),
            })
    zeilen.sort(key=lambda q: (q["fertig_am"], q["kennung"]), reverse=True)
    return zeilen


def archiv(conn: sqlite3.Connection, projekt_id: int, art: str = "",
           suche: str = "") -> list[dict]:
    """Was abgeschlossen ist -- im Wortlaut, mit allen Feldern.

    **In einer Datenbank verschwindet nichts.** Das Archiv ist deshalb
    keine zweite Ablage, sondern dieselbe von der anderen Seite gesehen:
    Die Register davor zeigen, was offen ist; hier steht, was
    abgeschlossen wurde.

    **Und hier wird nichts geaendert.** Ein Archiv, in dem man
    nachtraeglich schreiben kann, ist keines. Diese Funktion liest nur;
    einen Weg zurueck gibt es (noch) nicht.
    """
    raus = []
    if art in ("", "B"):
        for t in topics(conn, projekt_id, offen_nur=False):
            if t["abschluss"] != STRICH:
                raus.append(_archiveintrag("B", "Sammlung", t, t["titel"],
                                           t["abschluss_am"]))
    if art in ("", "A"):
        for a in aufgaben(conn, projekt_id, offen_nur=False):
            if a["abschluss"] != STRICH:
                raus.append(_archiveintrag("A", "Aufgaben", a, a["titel"],
                                           a["abschluss_am"]))
    if art in ("", "M"):
        for m in meilensteine(conn, projekt_id, offen_nur=False):
            if m["abschluss"] != STRICH:
                raus.append(_archiveintrag("M", "Meilensteine", m,
                                           m["benennung"], m["abschluss_am"]))
    if suche.strip():
        wort = suche.strip().lower()
        raus = [e for e in raus if wort in e["titel"].lower()]
    raus.sort(key=lambda e: (e["fertig_am"], e["kennung"]), reverse=True)
    return raus


def _archiveintrag(art: str, register: str, satz: dict, titel: str,
                   fertig_am: str) -> dict:
    return {
        "art": art, "register": register, "id": satz["id"],
        "kennung": satz["kennung"], "titel": titel,
        "abschluss": satz["abschluss"], "fertig_am": fertig_am,
        "fertig_deutsch": datum_zeigen(fertig_am),
        "satz": satz,
    }


def history_zahlen(conn: sqlite3.Connection, projekt_id: int) -> dict:
    """Die Zahlen in den drei Kartenkoepfen."""
    steine = strasse(conn, projekt_id)
    dauern = [s["dauer"] for s in steine if s["dauer"] is not None]
    im_archiv = archiv(conn, projekt_id)
    return {
        "steine": len(steine),
        "tage": sum(dauern),
        "umwege": sum(len(s["dazwischen"]) for s in steine),
        "quittungen": len(quittungsbuch(conn, projekt_id)),
        "archiv": len(im_archiv),
        "archiv_je_art": {a: len([e for e in im_archiv if e["art"] == a])
                          for a in ("B", "A", "M")},
    }


def projekt_leeren(conn: sqlite3.Connection, projekt_id: int) -> dict:
    """Die Werkseinstellung: Der Bestand geht, das Projekt bleibt.

    **Sie ist hier gefaehrlicher als in MARLEI Boot, und das ist kein
    Gefuehl.** Boot raeumt Wiederholbares weg: Ein Abbild holt man
    erneut, ein Rechner meldet sich wieder an. Hier loescht derselbe
    Knopf die Eintraege, und **die gibt es nirgends sonst** -- ausser im
    Export, und deshalb steht der davor.

    **Sie trifft nur das gewaehlte Projekt.** Die anderen bleiben
    unberuehrt; das ist der Unterschied zum Loeschen, das auch das
    Projekt selbst mitnimmt.

    Gibt zurueck, was weggeraeumt wurde -- damit die Meldung danach eine
    Zahl nennen kann und nicht nur "erledigt".
    """
    weg = bestand(conn, projekt_id)
    weg["bereiche"] = len(bereiche(conn, projekt_id))
    with conn:
        conn.execute("DELETE FROM kenntnis WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM entscheidungen WHERE projekt_id = ?",
                     (projekt_id,))
        conn.execute("UPDATE aufgaben SET meilenstein_id = NULL "
                     "WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM meilensteine WHERE projekt_id = ?",
                     (projekt_id,))
        conn.execute("DELETE FROM aufgaben WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM topics WHERE projekt_id = ?", (projekt_id,))
        conn.execute("DELETE FROM bereiche WHERE projekt_id = ?", (projekt_id,))
    return weg


# ==================================================================== #
# Befunde -- was ueber alle Projekte hinweg gilt
# ==================================================================== #
#
# **Die einzige Stelle, an der die Vorauswahl nicht gilt.** Der Grund
# steht in docs/aufbau.md, Abschnitt 2: Was liegen bleibt, liegt gerade in dem
# Projekt, in das seit Wochen niemand geschaut hat -- ein Befund, der nur
# das gewaehlte Projekt kennt, zeigte ihn nie und meldete Ruhe, wo keine
# ist.
#
# Hier stehen nur die ZAHLEN. Welcher Befund daraus wird, welche Stufe er
# hat und mit welchem Satz er dasteht, entscheidet webui/befunde.py --
# dieselbe Arbeitsteilung wie in MARLEI Boot.

NACHZUEGLER.update({
    # Wie weit es war, als jemand es zur Kenntnis nahm. Boots Mechanik:
    # **Weggeklickt heisst "ich weiss Bescheid, bis es schlimmer wird."**
    # Ohne die Zahl waere ein zur Kenntnis genommener Befund fuer immer
    # leise -- auch wenn aus drei Luecken dreissig werden.
    "kenntnis": {"marke": "INTEGER NOT NULL DEFAULT 0"},
})

# Ab wann ein Projekt als "da hat lange niemand hingesehen" gilt.
#
# Dreissig Tage, und die Zahl ist gegriffen -- aber sie ist die einzige
# gegriffene hier, und sie steht an einer Stelle, wo man sie findet. Ein
# Monat ist der Takt, in dem ein Chef auf ein ruhendes Projekt schaut;
# eine Woche waere Laerm, ein Quartal zu spaet.
DURCHSICHT_FRIST = 30


def befundzahlen(conn: sqlite3.Connection) -> list[dict]:
    """Je Projekt die Zahlen, aus denen Befunde werden.

    **Abgeschlossene Projekte fallen heraus.** docs/aufbau.md, Abschnitt 2:
    *Ein abgeschlossenes Projekt liegt nicht, es ist fertig.* Ein
    ruhendes dagegen bleibt drin -- es ist genau der Fall, fuer den die
    Befunde gebaut sind.

    **Gerechnet wird aus den Listen, nicht aus eigenem SQL.** Was ein
    fehlender Grund ist, was ein Stein ohne Aufgabe und was die
    Liegeprobe, steht je einmal in diesem Modul -- eine zweite Abfrage
    mit derselben Bedingung waere in einem Monat die falsche.
    """
    zahlen = []
    for p in projekte(conn):
        if p["zustand"] == "ABGESCHLOSSEN":
            continue
        offene_topics = topics(conn, p["id"])
        offene_aufgaben = aufgaben(conn, p["id"])
        offene_steine = meilensteine(conn, p["id"])
        alle_entscheidungen = entscheidungen(conn, p["id"])
        stand = conn.execute(
            "SELECT durchsicht_am FROM projekte WHERE id = ?",
            (p["id"],)).fetchone()
        zahlen.append({
            "projekt_id": p["id"],
            "kennung": p["kennung"],
            "name": p["name"],
            "zustand": p["zustand"],
            # Ein FEHLER, dem Angaben fehlen. Die Liste steht am Eintrag
            # (``fehlt``); hier zaehlt nur, wie viele es sind.
            "luecken": len([t for t in offene_topics if t["fehlt"]]),
            # Eine Aufgabe ohne Ursache. Sie sperrt nicht -- die Ursache
            # kann man nachtragen, sobald man sie versteht.
            "ohne_ursache": len([a for a in offene_aufgaben
                                 if not (a["dahinter"] or "").strip()]),
            "ohne_aufgabe": len([m for m in offene_steine
                                 if m["ohne_aufgabe"]]),
            "ohne_satz": len([e for e in alle_entscheidungen
                              if e["ohne_satz"]]),
            "liegt": len([e for e in alle_entscheidungen if e["liegt"]]),
            "durchsicht_her": tage_seit(
                stand["durchsicht_am"] if stand else ""),
            "bestand": sum(p["bestand"].values()),
        })
    return zahlen


def kenntnis_stand(conn: sqlite3.Connection) -> dict:
    """Was zur Kenntnis genommen ist: (Projekt, Befund) -> Marke."""
    return {(z["projekt_id"], z["befund"]): z["marke"]
            for z in conn.execute(
                "SELECT projekt_id, befund, marke FROM kenntnis")}


def kenntnis_nehmen(conn: sqlite3.Connection, projekt_id: int, befund: str,
                    marke: int) -> None:
    """Diesen Befund in diesem Projekt auf diesem Stand zur Kenntnis nehmen.

    **Je Projekt, nicht je Befund** -- sonst naehme das Stillstellen in
    einem Projekt dieselbe Lage in einem anderen mit, und ein Befund
    verschwaende, den nie jemand gesehen hat.
    """
    conn.execute(
        "INSERT INTO kenntnis (projekt_id, befund, seit, marke) "
        "VALUES (?, ?, ?, ?) ON CONFLICT(projekt_id, befund) DO UPDATE "
        "SET seit = excluded.seit, marke = excluded.marke",
        (projekt_id, befund, heute(), int(marke)))


def kenntnis_aufraeumen(conn: sqlite3.Connection, gelten: set) -> None:
    """Vergessen, was gerade nicht mehr gilt.

    **War ein Befund weg und kommt wieder, ist er neu** -- sonst bliebe
    eine Lage von vorigem Monat stumm, wenn sie sich wiederholt. Aus Boot
    uebernommen, dort mit derselben Begruendung.
    """
    for zeile in list(conn.execute(
            "SELECT projekt_id, befund FROM kenntnis")):
        if (zeile["projekt_id"], zeile["befund"]) not in gelten:
            conn.execute(
                "DELETE FROM kenntnis WHERE projekt_id = ? AND befund = ?",
                (zeile["projekt_id"], zeile["befund"]))
