"""
Welcher Stand dieser Anwendung hier laeuft.

Die Frage stellt sich in zwei Lagen: beim Betreiber ("bin ich aktuell?")
und bei einer Fehlermeldung von jemand anderem ("welcher Stand war das?").
Beide Male hilft nur eine Angabe, die sich nachvollziehen laesst -- eine
handgepflegte Nummer waere eine zweite Wahrheit neben Git und liefe
frueher oder spaeter daneben.

**Warum eine Datei und nicht Git selbst?** Der Ordner, aus dem der Dienst
laeuft, ist eine Kopie des Projektordners ohne ``.git``. Die Anwendung
kann Git also gar nicht fragen -- sie findet nur vor, was install.sh bzw.
install.ps1 beim Kopieren hinterlassen hat. Wer das uebersieht, baut die
Abfrage hier ein und wundert sich, dass sie auf dem Server nichts findet.

Fehlt die Datei, wird nicht geraten: Dann laeuft die Anwendung aus einem
Projektordner (Entwicklung) oder wurde von Hand kopiert, und die Seite
sagt genau das. Lieber keine Angabe als eine erfundene.

**VIER FELDER STATT EINER ZEILE, seit dem 22.09.2026.** Bis dahin stand
in ``VERSION`` nur der Stand, und mehr wurde nicht gebraucht: Es gab kein
oeffentliches Repository, bei dem sich etwas nachfragen liesse. Seit es
eines gibt, fragt webui/updatewacht.py dort nach -- und dafuer braucht es
den **Commit**, nicht den Stand. ``v1.0-8-g7831a68`` laesst sich mit
keinem Tag vergleichen, ein Commit sehr wohl.

**Die alte Fassung wird weiter gelesen.** Eine Installation, die vor
diesem Tag entstanden ist, traegt eine einzeilige Datei; sie gilt dann als
Stand ohne Commit, und die Karte sagt, dass nicht verglichen werden kann.
Das ist der ehrliche Zustand und kein Fehler -- ein Update schreibt die
Datei ohnehin neu.

Abgeschrieben aus MARLEI Boot, siehe tools/gemeinsam.txt.
"""

from __future__ import annotations

import os
from pathlib import Path

# Geschrieben von setup/linux/install.sh bzw. setup/windows/install.ps1,
# gleich nach dem Kopieren. Der Pfad laesst sich umbiegen -- die Tests
# legen sich eine eigene Datei an.
DATEI = Path(os.environ.get("MARLEI_VERSION_DATEI",
                            Path(__file__).resolve().parent / "VERSION"))

# Die Datei aendert sich nur bei einer Installation, wird aber auf jeder
# Seite gebraucht (die Fusszeile steht in base.html). Gemerkt wird deshalb
# ueber den Zeitstempel: neu geschrieben heisst neu gelesen, ohne dass
# jemand daran denken muss.
_CACHE: dict = {"stand": None, "werte": {}}

# Was die Installationsskripte schreiben. Alles andere in der Datei wird
# ignoriert -- sonst waere jede spaetere Ergaenzung dort ein Fehler hier.
FELDER = ("stand", "commit", "zweig", "installiert")


def _lies() -> dict:
    try:
        mtime = DATEI.stat().st_mtime
    except OSError:
        return {}
    if _CACHE["stand"] == mtime:
        return _CACHE["werte"]

    try:
        roh = DATEI.read_text(encoding="utf-8")
    except OSError:
        return {}

    werte: dict = {}
    for zeile in roh.splitlines():
        schluessel, trenner, wert = zeile.partition("=")
        if trenner and schluessel.strip() in FELDER:
            werte[schluessel.strip()] = wert.strip()

    # DIE ALTE EINZEILIGE FASSUNG. Sie traegt kein "=", also faende die
    # Schleife oben nichts -- und die Karte sagte "nicht ueber install.sh
    # hierhergekommen" ueber einen Server, der es sehr wohl war. Steht
    # etwas da, das kein Feld ist, ist es der Stand.
    if not werte:
        erste = next((z.strip() for z in roh.splitlines()
                      if z.strip() and not z.lstrip().startswith("#")), "")
        if erste:
            werte = {"stand": erste}

    _CACHE["stand"] = mtime
    _CACHE["werte"] = werte
    return werte


def auskunft() -> dict:
    """Was auf der Einrichtungsseite steht.

    "da" trennt die beiden Faelle, die man sonst verwechselt: Eine leere
    Angabe heisst nicht "Version 0", sondern "hier steht nichts, weil
    diese Anwendung nicht ueber install.sh hierhergekommen ist".
    """
    werte = _lies()
    if not werte.get("stand"):
        return {"da": False, "stand": "", "commit": "", "zweig": "",
                "installiert": "", "datei": str(DATEI)}

    return {
        "da": True,
        "stand": werte.get("stand", ""),
        "commit": werte.get("commit", ""),
        # Ein anderer Zweig als main ist keine Stoerung, aber die haeufigste
        # Erklaerung dafuer, dass jemand etwas anderes sieht als erwartet.
        "zweig": werte.get("zweig", ""),
        "installiert": werte.get("installiert", ""),
        "datei": str(DATEI),
    }


def kurz() -> str:
    """Eine Zeile fuer Fusszeile und Fehlerbericht -- oder leer."""
    return _lies().get("stand", "")
