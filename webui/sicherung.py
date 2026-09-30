"""
Die Sicherung: eine Kopie der Ablage in einem Ordner, den man waehlt.

**Nicht dasselbe wie der Export, und beide bleiben.** Der Export schreibt
Text -- lesbar ohne dieses Werkzeug, stabil fuer ein Repository. Die
Sicherung schreibt die Datenbank selbst: nicht lesbar, aber vollstaendig
und in einem Zug zurueckzulegen. Wer nach einem Plattenschaden wieder
arbeiten will, braucht die zweite.

**Kopiert wird ueber die Sicherungsschnittstelle von SQLite, nicht ueber
die Datei.** Die Ablage laeuft mit WAL; was zuletzt geschrieben wurde,
steht oft noch in ``tasks.db-wal`` und nicht in ``tasks.db``. Eine
Dateikopie verloere es lautlos. ``Connection.backup()`` liest den Stand,
den jede andere Verbindung auch saehe.

**Wann gesichert wird** (entschieden im September 2026): beim Start, auf
Knopfdruck, und einmal am Tag -- aber beim Start und am Tag nur, wenn
sich seit der letzten Sicherung etwas geaendert hat. Der Dienst startet
selten, oft erst nach Wochen; ohne den Tagestakt gaebe es so lange keine
neue Kopie. Und ohne die Pruefung auf Aenderung schoebe jeder Neustart
eine gleiche Kopie nach, die eine aeltere, verschiedene aus dem Ordner
draengt.

Das Vorbild steht in MEL Financial; uebernommen sind die Kopie ueber
eine Zwischendatei, die Schreibprobe beim Waehlen des Ordners und der
Befehl, der fehlende Rechte nachtraegt. Nicht uebernommen ist die
Aufbewahrung nach Tagen und Wochen: Hier bleiben die letzten N, weil
das eine Zahl ist, die man auf der Karte einstellen und verstehen kann.
"""

from __future__ import annotations

import errno
import hashlib
import os
import re
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

import datenbank
import einstellungen

# Unter welchem Konto der Dienst laeuft -- auf beiden Systemen derselbe
# Name. Er steht im Befehl, der fehlende Rechte nachtraegt.
KONTO = "marlei-tasks"

ZEITFORMAT = "%Y-%m-%d_%H%M%S"

# Die Grenzen dessen, was auf der Karte als Anzahl gewaehlt werden kann.
# Eine Sicherung behalten hiesse: Die, die gerade geschrieben wird,
# ersetzt die einzige, die es gibt -- und ist sie selbst schon kaputt,
# ist nichts mehr da.
BEHALTEN_MIN = 2
BEHALTEN_MAX = 365

# Wie oft die Wache fragt, ob die Tagessicherung faellig ist, und ab
# wann sie es ist. Gefragt wird stuendlich, damit ein Rechner, der nachts
# schlaeft, am Morgen nicht bis zum naechsten Tag wartet.
TAKT = 3600.0
TAG = 24 * 3600.0


class SicherungsFehler(Exception):
    """Etwas ging nicht -- mit dem Satz, den die Karte zeigt.

    ``befehl`` traegt, wenn es einen gibt, den Befehl, der das Recht
    nachtraegt. Die Karte zeigt ihn mit einem Knopf zum Kopieren.
    """

    def __init__(self, text: str, befehl: str = "", ordner: str = ""):
        super().__init__(text)
        self.befehl = befehl
        self.ordner = ordner


# ==================================================================== #
# Der Ordner
# ==================================================================== #

def vorgabe_ordner() -> Path:
    """Neben der Ablage -- dort darf der Dienst ohnehin schreiben.

    **Ein Ordner auf derselben Platte schuetzt vor einem Fehler in der
    Anwendung, nicht vor einem Plattenschaden.** Die Karte sagt das; wer
    mehr will, waehlt einen Ordner woanders.
    """
    return Path(datenbank.DB_PFAD).parent / "sicherung"


def ordner() -> Path:
    """Der Ordner, der gilt -- der gewaehlte oder die Vorgabe."""
    gewaehlt = str(einstellungen.hole("sicherung_ordner") or "").strip()
    return Path(gewaehlt) if gewaehlt else vorgabe_ordner()


def gewaehlt() -> bool:
    """Ob jemand einen Ordner gewaehlt hat."""
    return bool(str(einstellungen.hole("sicherung_ordner") or "").strip())


def behalten() -> int:
    """Wie viele Sicherungen bleiben."""
    try:
        wert = int(einstellungen.hole("sicherung_behalten"))
    except (TypeError, ValueError):
        wert = einstellungen.VORGABEN["sicherung_behalten"]
    return min(max(wert, BEHALTEN_MIN), BEHALTEN_MAX)


def _ist_absolut(text: str) -> bool:
    r"""Ein vollstaendiger Pfad -- auf welchem System auch immer.

    **Nicht ``Path.is_absolute()``:** Das beantwortet die Frage fuer das
    System, auf dem die Pruefung laeuft. ``C:\Sicherung`` ist unter Linux
    kein absoluter Pfad, und die Tests laufen auf beiden.
    """
    return bool(re.match(r"^([A-Za-z]:[\\/]|\\\\|//|/)", text))


def rechte_befehl(ziel: Path) -> str:
    """Der Befehl, der dem Dienst das Schreiben in ``ziel`` erlaubt.

    **Er wird genannt, nicht ausgefuehrt.** Die Anwendung darf das nicht,
    und sie soll es auch nicht duerfen: Wer einem Dienst einen Ordner
    freigibt, soll es selbst tun und sehen, was er tut.

    **Unter Windows** genuegt das Recht auf dem Ordner selbst -- die
    Ordner darueber muss das Konto nur durchqueren, und das darf jedes
    Konto.

    **Unter Linux** braucht es zwei Dinge: den Ordner, der dem Konto
    gehoert, und eine Freigabe in der Einheit. ``ProtectSystem=strict``
    macht sonst alles schreibgeschuetzt, was nicht ausdruecklich genannt
    ist. Die Freigabe steht in einer eigenen Datei neben der Einheit;
    ``install.sh`` schreibt die Einheit bei jedem Update neu, eine
    Datei in ``marlei-tasks.service.d`` laesst es stehen.
    """
    pfad = str(ziel)
    if os.name == "nt":
        return ('New-Item -ItemType Directory -Force "%s" | Out-Null\n'
                'icacls "%s" /grant "%s:(OI)(CI)M"' % (pfad, pfad, KONTO))
    return ('sudo install -d -o %s -g %s "%s"\n'
            'sudo mkdir -p /etc/systemd/system/%s.service.d\n'
            "printf '[Service]\\nReadWritePaths=-%s\\n' | sudo tee "
            '/etc/systemd/system/%s.service.d/sicherung.conf\n'
            'sudo systemctl daemon-reload && sudo systemctl restart %s'
            % (KONTO, KONTO, pfad, KONTO, pfad, KONTO, KONTO))


def _unter_home(ziel: Path) -> bool:
    """Liegt das unter einem Verzeichnis, das die Einheit ganz verbirgt?

    ``ProtectHome=yes`` macht ``/home``, ``/root`` und ``/run/user`` fuer
    den Dienst unsichtbar, und eine Freigabe hebt das nicht auf. Dort
    hilft kein Befehl -- die Karte sagt es, statt einen zu nennen, der
    nichts bewirkt.
    """
    if os.name == "nt":
        return False
    text = str(ziel)
    return any(text == w or text.startswith(w + "/")
               for w in ("/home", "/root", "/run/user"))


def _hinweis(ziel: Path, fehler: OSError) -> str:
    """Der Satz, wenn geschrieben werden soll und nicht kann."""
    if os.name == "nt":
        return ("In %s kann MARLEI Tasks nicht schreiben (%s). Der Dienst "
                "läuft unter dem Konto %s — ein Laufwerksbuchstabe, den "
                "ein angemeldeter Mensch verbunden hat, ist für ihn nicht "
                "da. Einen Netzordner als UNC-Pfad angeben (\\\\server\\"
                "freigabe\\ordner)." % (ziel, fehler.strerror or fehler,
                                         KONTO))
    return ("In %s kann MARLEI Tasks nicht schreiben (%s)."
            % (ziel, fehler.strerror or fehler))


def schreibprobe(ziel: Path) -> None:
    """Anlegen, eine Datei hineinschreiben, wieder loeschen.

    **Geprueft wird, indem man es tut** -- ``os.access`` beantwortet die
    Frage nach den Rechten, nicht die nach dem schreibgeschuetzten
    Dateisystem, das ``ProtectSystem=strict`` um den Dienst legt.
    """
    if _unter_home(ziel):
        raise SicherungsFehler(
            "%s liegt unter /home, /root oder /run/user. Diese "
            "Verzeichnisse sind für den Dienst unsichtbar "
            "(ProtectHome), und eine Freigabe hebt das nicht auf. Einen "
            "Ordner woanders wählen, etwa unter /srv oder /mnt." % ziel)
    probe = ziel / ".schreibprobe"
    try:
        ziel.mkdir(parents=True, exist_ok=True)
        probe.write_bytes(b"ok")
        probe.unlink()
    except OSError as fehler:
        # EROFS ist, was ProtectSystem=strict meldet: kein fehlendes
        # Recht im Dateisystem, sondern ein schreibgeschuetzter Blick
        # darauf. Behoben wird es mit demselben Befehl.
        if isinstance(fehler, PermissionError) or fehler.errno in (
                errno.EACCES, errno.EPERM, errno.EROFS):
            raise SicherungsFehler(
                "In %s darf MARLEI Tasks nicht schreiben. Der Befehl "
                "darunter erlaubt es dem Dienst — danach den Ordner "
                "noch einmal übernehmen." % ziel,
                befehl=rechte_befehl(ziel), ordner=str(ziel))
        raise SicherungsFehler(_hinweis(ziel, fehler))


def ordner_setzen(text: str) -> Path:
    """Einen Ordner waehlen. Leer heisst: zurueck zur Vorgabe.

    Uebernommen wird erst, wenn die Schreibprobe gelingt -- ein Ordner,
    in den nicht geschrieben werden kann, waere eine Sicherung, die es
    nur auf der Karte gibt.
    """
    roh = text.strip().strip('"').strip("'").strip()
    if not roh:
        einstellungen.setze("sicherung_ordner", "")
        return vorgabe_ordner()
    if not _ist_absolut(roh):
        raise SicherungsFehler(
            "Bitte einen vollständigen Pfad angeben — %s"
            % ("etwa D:\\Sicherung oder \\\\server\\freigabe\\ordner."
               if os.name == "nt" else "etwa /srv/sicherung."))
    ziel = Path(roh)
    schreibprobe(ziel)
    einstellungen.setze("sicherung_ordner", str(ziel))
    return ziel


def behalten_setzen(anzahl: int) -> int:
    if not BEHALTEN_MIN <= anzahl <= BEHALTEN_MAX:
        raise SicherungsFehler(
            "Behalten werden zwischen %d und %d Sicherungen."
            % (BEHALTEN_MIN, BEHALTEN_MAX))
    einstellungen.setze("sicherung_behalten", anzahl)
    aufraeumen()
    return anzahl


# ==================================================================== #
# Die Sicherungen im Ordner
# ==================================================================== #

def _muster() -> re.Pattern:
    """Nur was diese Anwendung selbst geschrieben hat.

    Der Ordner kann ein geteilter sein -- ein HiDrive-Ordner, in dem noch
    anderes liegt. **Aufgeraeumt wird nur, was auf dieses Muster passt**;
    alles andere gehoert jemand anderem.
    """
    stamm = re.escape(Path(datenbank.DB_PFAD).stem)
    return re.compile(r"^%s-(\d{4}-\d{2}-\d{2}_\d{6})(?:-([a-z0-9-]+))?\.db$"
                      % stamm)


def liste(wo: Path | None = None) -> list[dict]:
    """Die Sicherungen im Ordner, die neueste zuerst."""
    wo = wo or ordner()
    muster = _muster()
    raus = []
    try:
        dateien = list(wo.iterdir())
    except OSError:
        return []
    for datei in dateien:
        treffer = muster.match(datei.name)
        if not treffer or not datei.is_file():
            continue
        try:
            am = datetime.strptime(treffer.group(1), ZEITFORMAT)
            groesse = datei.stat().st_size
        except (ValueError, OSError):
            continue
        raus.append({"name": datei.name, "pfad": datei, "am": am,
                     "am_deutsch": am.strftime("%d.%m.%Y %H:%M"),
                     "bytes": groesse, "zusatz": treffer.group(2) or ""})
    raus.sort(key=lambda s: (s["am"], s["name"]), reverse=True)
    return raus


def aufraeumen(wo: Path | None = None, anzahl: int | None = None) -> list[str]:
    """Nur die letzten N behalten. Gibt zurueck, was weg ist.

    **Die Sicherung vor einem Import zaehlt nicht mit** und wird nie
    aufgeraeumt: Sie ist der Weg zurueck von einem bestimmten Schritt,
    und den soll kein Tagestakt wegschieben.
    """
    anzahl = anzahl or behalten()
    regulaer = [s for s in liste(wo) if not s["zusatz"]]
    weg = []
    for s in regulaer[anzahl:]:
        try:
            s["pfad"].unlink()
            weg.append(s["name"])
        except OSError:
            pass
    return weg


def _kopieren(quelle: Path, ziel: Path) -> None:
    """Die Ablage nach ``ziel`` -- ueber eine Zwischendatei.

    **Erst unter anderem Namen, dann umbenennen.** Ein Ordner, den ein
    Sync-Programm beobachtet, saehe sonst eine halbe Datei und laede sie
    hoch; und ein abgebrochener Lauf liesse etwas liegen, das wie eine
    Sicherung heisst und keine ist.
    """
    zwischen = ziel.with_name(ziel.name + ".teil")
    zwischen.unlink(missing_ok=True)
    von = sqlite3.connect(quelle, timeout=20)
    try:
        nach = sqlite3.connect(zwischen)
        try:
            von.backup(nach)
            # Die Kopie steht fuer sich: ohne -wal daneben, damit sie
            # sich als eine Datei verschieben und oeffnen laesst.
            nach.execute("PRAGMA journal_mode=DELETE")
        finally:
            nach.close()
    finally:
        von.close()
    zwischen.replace(ziel)


def sichern(zusatz: str = "", jetzt: datetime | None = None,
            wo: Path | None = None) -> dict:
    """Eine Sicherung schreiben. Gibt zurueck, was geschrieben wurde.

    Mit ``zusatz`` (etwa ``vor-import``) steht er im Namen, und die
    Sicherung faellt aus der Aufbewahrung heraus.
    """
    wo = wo or ordner()
    quelle = Path(datenbank.DB_PFAD)
    stempel = (jetzt or datetime.now()).strftime(ZEITFORMAT)
    name = "%s-%s%s.db" % (quelle.stem, stempel,
                           "-" + zusatz if zusatz else "")
    ziel = wo / name
    try:
        schreibprobe(wo)
        _kopieren(quelle, ziel)
    except SicherungsFehler:
        raise
    except (OSError, sqlite3.Error) as fehler:
        raise SicherungsFehler("Die Sicherung ging nicht: %s" % fehler)
    weg = [] if zusatz else aufraeumen(wo)
    return {"name": name, "pfad": str(ziel), "bytes": ziel.stat().st_size,
            "weg": weg}


# ==================================================================== #
# Hat sich etwas geaendert?
# ==================================================================== #

def fingerabdruck(pfad: Path) -> str:
    """Ein Abdruck des INHALTS, nicht der Datei.

    **Die Datei taugt dafuer nicht.** Zwei Kopien desselben Bestands
    unterscheiden sich in Kopfbytes, und die Uhrzeit der Ablage aendert
    sich schon, wenn SQLite beim Schliessen das WAL zurueckschreibt. Der
    Inhalt aendert sich nur, wenn jemand etwas eintraegt.

    Die Suchtabelle bleibt draussen: Sie ist aus der Sammlung abgeleitet
    und aendert sich nur mit ihr.
    """
    abdruck = hashlib.sha256()
    conn = sqlite3.connect("file:%s?mode=ro" % pfad.as_posix(), uri=True,
                           timeout=20)
    try:
        tabellen = [z[0] for z in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'topics_suche%' "
            "ORDER BY name")]
        for t in tabellen:
            abdruck.update(t.encode())
            for zeile in conn.execute('SELECT * FROM "%s" ORDER BY rowid' % t):
                abdruck.update(repr(tuple(zeile)).encode())
    finally:
        conn.close()
    return abdruck.hexdigest()


def geaendert(wo: Path | None = None) -> bool:
    """Steht in der Ablage etwas, das die letzte Sicherung nicht hat?

    Verglichen wird mit der juengsten Sicherung, welcher Art auch immer.
    Gibt es keine, oder laesst sie sich nicht lesen, gilt: geaendert --
    lieber eine Kopie zu viel als eine zu wenig.
    """
    vorhanden = liste(wo)
    if not vorhanden:
        return True
    try:
        return (fingerabdruck(Path(datenbank.DB_PFAD))
                != fingerabdruck(vorhanden[0]["pfad"]))
    except sqlite3.Error:
        return True


# ==================================================================== #
# Beim Start und einmal am Tag
# ==================================================================== #

# Was der letzte Lauf im Hintergrund ergeben hat. Die Karte zeigt es:
# Ein Fehler, den nur das Protokoll kennt, faellt erst auf, wenn man die
# Sicherung braucht.
_zustand: dict = {"fehler": "", "am": None}
_wache_laeuft = False
_sperre = threading.Lock()


def zustand() -> dict:
    return dict(_zustand)


def wenn_geaendert(jetzt: datetime | None = None) -> dict | None:
    """Sichern, wenn sich etwas geaendert hat. Gibt zurueck, was
    geschrieben wurde -- oder ``None``, wenn nichts zu tun war.

    **Fehler gehen nicht verloren**, sondern in den Zustand, den die
    Karte zeigt.
    """
    with _sperre:
        try:
            if not geaendert():
                _zustand.update(fehler="", am=jetzt or datetime.now())
                return None
            ergebnis = sichern(jetzt=jetzt)
        except SicherungsFehler as fehler:
            _zustand.update(fehler=str(fehler), am=jetzt or datetime.now())
            print("MARLEI Tasks: Sicherung fehlgeschlagen -- %s" % fehler)
            return None
        _zustand.update(fehler="", am=jetzt or datetime.now())
        return ergebnis


def tag_faellig(jetzt: float | None = None) -> bool:
    """Ist die juengste Sicherung einen Tag alt oder aelter?"""
    vorhanden = liste()
    if not vorhanden:
        return True
    alter = (jetzt or time.time()) - vorhanden[0]["am"].timestamp()
    return alter >= TAG


def _wache() -> None:
    wenn_geaendert()
    while True:
        time.sleep(TAKT)
        if tag_faellig():
            wenn_geaendert()


def wache_starten() -> None:
    """Einmal beim Hochfahren: gleich sichern, dann stuendlich fragen.

    Im Hintergrund, damit ein langsamer Netzordner den Start nicht
    aufhaelt -- die Oberflaeche ist da, waehrend die Kopie noch laeuft.
    """
    global _wache_laeuft
    if _wache_laeuft:
        return
    _wache_laeuft = True
    threading.Thread(target=_wache, daemon=True).start()
