"""
Hat sich das Projekt bewegt, seit diese Anwendung installiert wurde?

**Git ist ein Hol-Verfahren.** Wer nie ``update.sh`` bzw. ``update.ps1``
tippt, bleibt ewig auf dem Installationsstand, ohne es zu merken; die
Anwendung sieht dabei kerngesund aus. Das ist derselbe Fall wie bei einem
Meilenstein ohne Aufgaben: Es fehlt etwas, und niemand sagt es.

**Verglichen werden Commits, nicht Versionsnummern.** Der naheliegende
Entwurf fragt nach dem hoechsten Tag und haelt ihn gegen den Stempel. Das
passt zu einem Projekt, das Ausgaben ausliefert; dieses wird ueber
``git clone`` und ein Update-Skript verteilt, und wer dem README folgt,
landet auf dem Kopf von ``main``. Der Stempel lautet dann
"v1.0-8-g7831a68" -- kein Tag, sondern ein Punkt dazwischen. Zwei solche
Angaben lassen sich nicht vergleichen: Ob das, was im Tag steckt, in den
acht Aenderungen danach schon enthalten ist, sagt keine von beiden.

Die beantwortbare Frage lautet: **Liegen Aenderungen bereit?** Sie geht,
weil die Installationsskripte neben dem Stand auch den **Commit**
stempeln -- GitHub vergleicht ihn mit dem Zweig und sagt, wie viele
Aenderungen dazwischenliegen. Die Versionsnummern behalten davon
unberuehrt ihre Aufgabe: Sie sagen, *was* drin ist, nicht, *ob* man holen
soll.

**Wie oft, entscheidet der Betreiber** (einstellungen.updatepruefung):
nie, woechentlich, monatlich. Darueber steht der **Offline-Modus**: Ist
er an, fragt diese Anwendung ueberhaupt nicht nach draussen, und die
Oberflaeche bietet die Auswahl gar nicht erst an.

**Dass der Offline-Modus ein Schalter in der Oberflaeche ist und keine
Variable in der Umgebungsdatei, ist die Abweichung von MARLEI Boot** --
begruendet in einstellungen.py. Dort steht auch, warum "nie" und
"offline" zwei verschiedene Dinge sind und nicht ein Regler mit vier
Stufen.

**DIES IST DIE EINZIGE ABFRAGE NACH DRAUSSEN, DIE DIESE ANWENDUNG
KENNT.** Sie war es am 22.09.2026, als dieses Modul entstand: keine
Schrift von einem fremden Server, kein CDN, kein Aufruf ausser diesem.
Wer eine zweite hinzufuegt, fragt vorher ``erlaubt()`` -- sonst ist die
Zusage "laeuft ohne Internet" still nicht mehr wahr.

**Ohne Netz passiert nichts, und es sieht auch nicht danach aus.** Ein
fehlgeschlagener Blick wird vermerkt und nicht gemeldet.

Stuendlicher Takt, Vorlauf nach dem Start, Stand in einer Datei. Ein
Prozess, der eine Woche am Stueck schlaeft, ueberlebt kein Update.

Abgeschrieben aus MARLEI Boot, siehe tools/gemeinsam.txt.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

import datenbank
import einstellungen
import versionsstand

# Was der letzte Blick ergeben hat.
STAND_DATEI = Path(os.environ.get("MARLEI_UPDATEWACHT_STAND", "")
                   or Path(datenbank.DB_PFAD).parent / "updatewacht.yaml")

# Wessen Stand verglichen wird. Ueber die Umgebung zu setzen, damit ein
# Fork sich mit sich selbst vergleicht -- und damit der Test nicht ins
# Netz muss.
REPO = os.environ.get("MARLEI_REPO", "exmig/marlei-tasks").strip("/ ")
VERGLEICH = os.environ.get("MARLEI_VERGLEICH_ADRESSE", "") or (
    "https://api.github.com/repos/" + REPO + "/compare/{commit}...{zweig}")

# Was zur Auswahl steht. Mehr Werte waeren eine Einstellung, die niemand
# trifft -- und "alle drei Tage" beantwortet keine Frage, die jemand hat.
AUSWAHL = ((0, "nie"), (7, "wöchentlich"), (30, "monatlich"))

TAKT = 3600.0
VORLAUF = 120.0
ZEITLIMIT = 10.0

# Wie lange die Seite auf einen angestossenen Blick wartet, bevor sie ohne
# sein Ergebnis gebaut wird. Eine Anfrage dauert rund 150 ms; zwei
# Sekunden decken auch eine muede Leitung ab. Ohne dieses Warten ginge das
# Ergebnis ins Leere: Die Seite entsteht nach dem Speichern genau einmal.
BEDENKZEIT = 2.0


def offline() -> bool:
    """Ist der Offline-Modus eingeschaltet?"""
    return bool(einstellungen.hole("offline"))


def erlaubt() -> bool:
    """Darf diese Anwendung ueberhaupt nach draussen fragen?

    **Die Frage, die jede kuenftige Netzabfrage zuerst stellt.** Sie steht
    hier und nicht bei der Einstellung, damit es eine Stelle gibt, auf die
    man zeigen kann -- und damit der Offline-Modus mehr ist als ein
    Haekchen, das nur diese eine Funktion kennt.
    """
    return not offline()


def intervall_tage() -> int:
    """Tage zwischen zwei Blicken. 0 heisst: abgeschaltet."""
    if not erlaubt():
        return 0
    try:
        tage = int(einstellungen.hole("updatepruefung"))
    except (TypeError, ValueError):
        return 7
    return tage if tage in dict(AUSWAHL) else 0


# --------------------------------------------------------------------------
# Der Stand
# --------------------------------------------------------------------------

def _lesen() -> dict:
    try:
        with STAND_DATEI.open(encoding="utf-8") as fh:
            roh = yaml.safe_load(fh) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return roh if isinstance(roh, dict) else {}


def _schreiben(daten: dict) -> None:
    STAND_DATEI.parent.mkdir(parents=True, exist_ok=True)
    vorlaeufig = STAND_DATEI.with_suffix(".yaml.neu")
    with vorlaeufig.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(daten, fh, allow_unicode=True, sort_keys=False)
    os.replace(vorlaeufig, STAND_DATEI)


def vergiss() -> None:
    """Den gemerkten Stand wegwerfen."""
    try:
        STAND_DATEI.unlink()
    except OSError:
        pass


def _woher() -> tuple[str, str]:
    """Commit und Zweig aus dem Stempel der Installation.

    Beides oder nichts: Ohne Commit gibt es keinen Punkt, von dem aus
    verglichen wird. Und der Zweig entscheidet, wogegen verglichen wird --
    wer von einem anderen Zweig installiert hat, will nicht gegen ``main``
    gemessen werden.
    """
    auskunft = versionsstand.auskunft()
    if not auskunft.get("da"):
        return "", ""
    return auskunft.get("commit", ""), (auskunft.get("zweig", "") or "main")


def _befund() -> dict:
    """Der gemerkte Befund -- oder nichts, wenn er zu einem anderen Stand
    gehoert.

    **Ein Befund gilt fuer den Stand, gegen den er gezaehlt wurde.** Ist
    ein anderer eingespielt, ist er keine veraltete Auskunft, sondern gar
    keine -- und wird weggeworfen statt gealtert. Sonst behauptet die
    Karte bis zum naechsten faelligen Blick, es lege etwas bereit, was
    laengst geholt ist. In Boot ist genau das am 05.09.2026 passiert: Die
    Karte zaehlte gegen den Commit VOR dem Update, und der naechste Blick
    war erst in einer Woche faellig.

    Damit faellt auch ``faellig()`` sofort auf True: Der Waechter fragt
    nach dem Neustart, den ein Update ohnehin ausloest, binnen zwei
    Minuten nach.
    """
    daten = _lesen()
    commit, zweig = _woher()
    if not commit or not daten.get("commit"):
        # Ohne Stempel gibt es nichts zu vergleichen -- dann steht im
        # Befund, warum (kein_stempel), und das soll stehen bleiben.
        return daten
    if daten.get("commit") != commit or (daten.get("zweig") or "main") != zweig:
        return {}
    return daten


# --------------------------------------------------------------------------
# Ein Blick
# --------------------------------------------------------------------------

_laeuft = threading.Lock()


def laeuft() -> bool:
    return _laeuft.locked()


def naechster_blick() -> datetime | None:
    tage = intervall_tage()
    if not tage:
        return None
    zeit = _befund().get("zeit")
    if not zeit:
        return None                       # noch nie gefragt -- sofort dran
    try:
        war = datetime.fromisoformat(zeit)
    except (TypeError, ValueError):
        return None
    if war.tzinfo is None:
        war = war.replace(tzinfo=timezone.utc)
    return war + timedelta(days=tage)


def faellig() -> bool:
    if not intervall_tage():
        return False
    naechster = naechster_blick()
    if naechster is None:
        return True
    return datetime.now(timezone.utc) >= naechster


def _frag_github(commit: str, zweig: str, hole=None) -> dict:
    """Wie weit liegt der Zweig vor dem installierten Commit?

    GitHub beantwortet das in einer Anfrage: "ahead_by" zaehlt, was auf
    dem Zweig dazugekommen ist, "behind_by" was diese Installation hat und
    der Zweig nicht -- letzteres bei einer Maschine mit eigenen Commits.
    """
    if hole is not None:
        return hole()
    ziel = VERGLEICH.format(commit=commit, zweig=zweig)
    anfrage = urllib.request.Request(
        ziel, headers={"User-Agent": "marlei-tasks/1.0",
                       "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(anfrage, timeout=ZEITLIMIT) as antwort:
        daten = json.loads(antwort.read().decode("utf-8", "replace"))
    return daten if isinstance(daten, dict) else {}


def blick(hole=None) -> bool:
    """Einmal nachsehen. Sagt, ob der Blick zustande kam."""
    if not intervall_tage() or _laeuft.locked():
        return False
    with _laeuft:
        commit, zweig = _woher()
        daten = {"zeit": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "commit": commit, "zweig": zweig,
                 "voraus": 0, "zurueck": 0,
                 "kein_stempel": not commit,
                 "ohne_netz": False, "erreicht": False}
        if not commit:
            # Ohne Stempel gibt es keinen Punkt, von dem aus verglichen
            # wird. Kein Fehler: Die Anwendung laeuft dann aus einem
            # Projektordner und kam nicht ueber ein Installationsskript
            # hierher.
            _schreiben(daten)
            return False
        try:
            antwort = _frag_github(commit, zweig, hole)
        except (urllib.error.URLError, OSError, ValueError, TimeoutError) as fehler:
            # Vermerkt, nicht gemeldet: Ohne Leitung ist nichts kaputt.
            #
            # "erreicht" trennt zwei Faelle, die man sonst verwechselt und
            # dann falsch benennt: gar keine Antwort (Leitung, DNS,
            # Zeitlimit) und eine Antwort, die keine Auskunft war -- etwa
            # 404, wenn der gestempelte Commit dort gar nicht existiert,
            # weil jemand mit eigener Historie arbeitet.
            daten["ohne_netz"] = True
            daten["erreicht"] = isinstance(fehler, urllib.error.HTTPError)
            daten["grund"] = str(fehler)[:200]
            _schreiben(daten)
            return False
        daten["voraus"] = int(antwort.get("ahead_by") or 0)
        daten["zurueck"] = int(antwort.get("behind_by") or 0)
        _schreiben(daten)
        return True


def stand() -> dict:
    """Was der letzte Blick ergeben hat -- fuer die Karte."""
    daten = _befund()
    naechster = naechster_blick()
    commit, zweig = _woher()
    voraus = int(daten.get("voraus") or 0)
    return {
        "zeit": daten.get("zeit", ""),
        "commit": daten.get("commit", "") or commit,
        "zweig": daten.get("zweig", "") or zweig,
        # Wieviele Aenderungen auf dem Zweig dazugekommen sind, seit diese
        # Installation entstand. Das ist die ganze Auskunft.
        "voraus": voraus,
        # Und was diese Installation hat und der Zweig nicht -- eigene
        # Commits.
        "zurueck": int(daten.get("zurueck") or 0),
        "neuer": voraus > 0,
        "kein_stempel": bool(daten.get("kein_stempel")) or not commit,
        "ohne_netz": bool(daten.get("ohne_netz")),
        "erreicht": bool(daten.get("erreicht")),
        "gesucht": bool(daten.get("zeit")),
        "offline": offline(),
        "intervall": intervall_tage(),
        "laeuft": laeuft(),
        "naechster": naechster.isoformat() if naechster else "",
    }


# --------------------------------------------------------------------------
# Der Waechter
# --------------------------------------------------------------------------

_wacht_laeuft = False


def starte_blick(hole=None, warten: float = 0.0) -> bool:
    """Einen Blick anstossen. False, wenn schon einer laeuft.

    **Fuer den Moment, in dem jemand gerade geklickt hat.** Die Wache
    schlaeft in Stunden-Schritten -- richtig fuers Warten, falsch fuers
    Klicken.

    In einem eigenen Faden, damit ein haengendes Netz die Seite nicht
    festhaelt -- aber mit ``warten`` sieht der Aufrufer ihm kurz zu.
    """
    if laeuft() or not intervall_tage():
        return False
    faden = threading.Thread(target=blick, args=(hole,), daemon=True)
    faden.start()
    if warten:
        faden.join(warten)
    return True


def _wache() -> None:
    time.sleep(VORLAUF)
    while True:
        try:
            if faellig():
                blick()
        except Exception:
            # Ein Waechter, der an einem Fehler stirbt, ist schlimmer als
            # keiner: Er meldet sich nie wieder, und niemand vermisst ihn.
            pass
        time.sleep(TAKT)


def wacht_starten() -> None:
    """Einmal beim Hochfahren der Anwendung.

    **Der Takt haengt bewusst weder am Intervall noch am Offline-Modus:**
    Wer die Einstellung von "nie" auf "woechentlich" dreht oder den
    Offline-Modus ausschaltet, soll nicht bis zum naechsten Neustart
    warten. Gefragt wird stuendlich, ob gerade gesucht werden darf --
    ``faellig()`` liest beides jedes Mal neu.

    Das ist der Unterschied zu Boot, wo die Notbremse in der
    Umgebungsdatei steht und sich zur Laufzeit gar nicht aendern kann:
    Dort startet die Wache erst gar nicht, wenn gesperrt ist.
    """
    global _wacht_laeuft
    if _wacht_laeuft:
        return
    _wacht_laeuft = True
    threading.Thread(target=_wache, daemon=True).start()
