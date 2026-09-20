"""
Was tut der Server gerade? -- Last, Speicher und dieser Dienst selbst.

Zwei Fragen, eine Quelle: alles kommt aus /proc, ohne Zusatzpakete und ohne
besondere Rechte. Auf einem System ohne /proc liefert jede Funktion leere
Werte statt einer Behauptung.

**Aus MARLEI Boot abgeschrieben**, und die erste Haelfte -- ``last``,
``kerne``, ``cpu``, ``speicher``, ``netz`` -- ist dieselbe. Sie beantwortet
auf jedem Server dieselbe Frage.

**Die zweite Haelfte ist ersetzt, nicht gestrichen.** Dort steht in Boot
``uebertragungen()``: welcher Rechner gerade sein Wurzeldateisystem zieht,
abgelesen an den offenen TCP-Verbindungen auf 80 und 2049. Das ist
Boot-eigen -- hier zieht niemand etwas, hier redet ein Browser mit einer
Anwendung. Die Frage *was tut der Server gerade* bleibt trotzdem, und die
ehrliche Antwort ist ``dienst()``: **seit wann laeuft dieser Dienst, und
was braucht er selbst.**

**Unter Windows gibt es dieselben Zahlen, nur nicht als Datei** -- sie
stehen hinter Aufrufen des Kernels, und die stehen in ``windows.py``. Hier
steht je Funktion eine Weiche und sonst nichts: Ein zweites Ablesewerk in
dieser Datei liesse sie von Boots Fassung um mehr auseinanderlaufen als um
die eine Haelfte, die ohnehin ersetzt ist.

**Eine Zahl fehlt dort und laesst sich nicht ersetzen: das Lastmittel.**
Windows fuehrt keins -- das ist kein fehlender Wert, sondern ein Begriff,
den dieses System nicht hat. Die Kachel faellt dort weg; die Kernzahl, die
in ihrer Unterzeile steht, ist deshalb unter Serverdetails nachgetragen.

Warum das eine Auskunft ist und keine Spielerei: Auf einer Maschine, die
sonst im Leerlauf steht, sagen Prozessorlast und Speicherbelegung wenig
darueber, ob die Maschine fuer diesen Dienst reicht. Sein eigener
Verbrauch sagt es. Und die Betriebszeit beantwortet die Frage, mit der
jede Fehlersuche anfaengt: **Laeuft er ueberhaupt noch, oder ist er
zwischendurch neu gestartet?**
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import windows

PROC = Path("/proc")

# Welches System hier antwortet -- "nt" fuer Windows, sonst /proc.
#
# **Als Variable und nicht als Abfrage mitten im Code:** Die Testreihe
# stellt sie um und prueft beide Wege auf derselben Maschine -- den
# Windows-Weg und den leeren Fall, in dem es keine Quelle gibt. Ohne diese
# Naht liesse sich die Haelfte dieses Moduls dort nie pruefen, wo
# entwickelt wird.
SYSTEM = os.name

# Fuer Werte, die sich nur aus der Differenz zweier Messungen ergeben.
_vorher: dict = {}


def _lies(name: str) -> str:
    try:
        return (PROC / name).read_text(encoding="utf-8")
    except OSError:
        return ""


def last() -> list[float] | None:
    """Lastmittel der letzten 1, 5 und 15 Minuten.

    **Unter Windows: nichts, und das bleibt so.** Es gibt dort kein
    Lastmittel -- weder eine andere Quelle noch einen anderen Namen
    dafuer. Eine Zahl, die hier dann dastuende, waere erfunden.
    """
    if SYSTEM == "nt":
        return None
    roh = _lies("loadavg").split()
    if len(roh) < 3:
        return None
    try:
        return [float(w) for w in roh[:3]]
    except ValueError:
        return None


def kerne() -> int:
    if SYSTEM == "nt":
        return windows.kerne()
    return sum(1 for z in _lies("cpuinfo").splitlines() if z.startswith("processor")) or 1


def cpu() -> int | None:
    """Auslastung in Prozent seit der letzten Abfrage.

    Der Kernel zaehlt nur Zeitscheiben, keine Prozente -- der Wert ergibt
    sich aus der Differenz zweier Messungen. Die erste Abfrage nach dem
    Start hat noch keinen Vergleichswert und liefert deshalb nichts.
    """
    if SYSTEM == "nt":
        return windows.cpu()
    zeile = next((z for z in _lies("stat").splitlines() if z.startswith("cpu ")), "")
    felder = [int(w) for w in zeile.split()[1:] if w.isdigit()]
    if len(felder) < 5:
        return None

    gesamt = sum(felder)
    untaetig = felder[3] + felder[4]          # idle + iowait
    alt = _vorher.get("cpu")
    _vorher["cpu"] = (gesamt, untaetig)
    if alt is None or gesamt <= alt[0]:
        return None

    d_gesamt = gesamt - alt[0]
    d_untaetig = untaetig - alt[1]
    return max(0, min(100, round((d_gesamt - d_untaetig) / d_gesamt * 100)))


def speicher() -> dict:
    if SYSTEM == "nt":
        return windows.speicher()
    werte = {}
    for zeile in _lies("meminfo").splitlines():
        name, _, rest = zeile.partition(":")
        zahl = rest.strip().split(" ")[0]
        if zahl.isdigit():
            werte[name] = int(zahl) * 1024
    gesamt = werte.get("MemTotal", 0)
    frei = werte.get("MemAvailable", werte.get("MemFree", 0))
    if not gesamt:
        return {}
    return {"gesamt": gesamt, "belegt": gesamt - frei,
            "anteil": round((gesamt - frei) / gesamt * 100)}


def netz() -> dict:
    """Durchsatz seit der letzten Abfrage, in Byte je Sekunde.

    Alle Schnittstellen ausser der Rueckschleife zusammen -- die VM hat
    ohnehin nur eine, und so muss hier nichts konfiguriert werden.
    """
    if SYSTEM == "nt":
        return windows.netz()
    rein = raus = 0
    gefunden = False
    for zeile in _lies("net/dev").splitlines():
        name, _, rest = zeile.partition(":")
        name = name.strip()
        if not rest or name in ("lo", "Inter-|   Receive"):
            continue
        felder = rest.split()
        if len(felder) < 9:
            continue
        gefunden = True
        rein += int(felder[0])
        raus += int(felder[8])
    if not gefunden:
        return {}

    jetzt = time.monotonic()
    alt = _vorher.get("netz")
    _vorher["netz"] = (rein, raus, jetzt)
    if alt is None or jetzt - alt[2] < 0.5 or rein < alt[0]:
        return {}
    dauer = jetzt - alt[2]
    return {"rein": int((rein - alt[0]) / dauer), "raus": int((raus - alt[1]) / dauer)}


def _takte() -> int:
    """Wie viele Zeitscheiben der Kernel je Sekunde zaehlt.

    ``os.sysconf`` gibt es unter Windows nicht -- dort ist ohnehin kein
    /proc da, und der Rueckfall auf 100 wird nie gebraucht.
    """
    try:
        return int(os.sysconf("SC_CLK_TCK")) or 100
    except (AttributeError, ValueError, OSError):
        return 100


def dienst() -> dict:
    """Seit wann laeuft dieser Dienst, und was braucht er selbst.

    **Das ist die Stelle, an der dieses Modul von Boots abweicht** -- dort
    stehen hier die laufenden Uebertragungen. Der Modulkopf sagt, warum.

    ``betrieb`` sind Sekunden seit dem Start **dieses Prozesses**, nicht
    der Maschine: Die Laufzeit der Maschine steht unter Serverdetails, und
    sie beantwortet eine andere Frage. ``speicher`` ist der wirklich
    belegte Arbeitsspeicher (VmRSS), nicht der reservierte -- die Zahl,
    die man mit dem Arbeitsspeicher der Maschine vergleichen kann.

    Fehlt /proc -- oder unter Windows die Antwort des Kernels --, kommt ein
    leerer Wert zurueck. **Kein Rueckfall auf ``time.time()`` beim Start
    des Moduls:** Das saehe wie eine Messung aus und waere eine Erfindung
    -- es maesse, wann Python dieses Modul geladen hat, nicht, seit wann
    der Dienst laeuft.
    """
    if SYSTEM == "nt":
        return windows.dienst()
    werte: dict = {}

    for zeile in _lies("self/status").splitlines():
        if zeile.startswith("VmRSS:"):
            felder = zeile.split()
            if len(felder) >= 2 and felder[1].isdigit():
                werte["speicher"] = int(felder[1]) * 1024
            break

    # Der Prozessname steht in Klammern und darf Leerzeichen enthalten --
    # deshalb hinter der LETZTEN schliessenden Klammer trennen und nicht
    # nach Feldern zaehlen. Danach ist "starttime" das 20. Feld.
    roh = _lies("self/stat")
    _, klammer, rest = roh.rpartition(") ")
    felder = rest.split()
    hoch = _lies("uptime").split()
    if klammer and len(felder) >= 20 and hoch:
        try:
            seit_start = float(hoch[0]) - int(felder[19]) / _takte()
        except (ValueError, ZeroDivisionError):
            seit_start = -1.0
        if seit_start >= 0:
            werte["betrieb"] = int(seit_start)

    return werte


def dauer_dativ(sekunden: int | None) -> str:
    """Eine Dauer als Satzstueck nach "seit": "3 Stunden", "2 Tagen".

    **Der Dativ steht hier und nicht in der Vorlage**, weil die Form von
    der Zahl abhaengt -- "seit 1 Tag", aber "seit 2 Tagen". Dieselbe
    Ueberlegung wie beim Makro ``liegt`` unter Sammlung; dort war "seit 9
    Tage" der Fehler, der beim ersten Blick auf die gebaute Seite auffiel.

    Unter einer Minute wird nicht gerundet, sondern gesagt, was Sache
    ist: Ein frisch gestarteter Dienst steht sonst mit "seit 0 Minuten"
    da.
    """
    if sekunden is None:
        return ""
    if sekunden < 60:
        return "weniger als einer Minute"
    if sekunden < 3600:
        n = sekunden // 60
        return "%d Minute%s" % (n, "" if n == 1 else "n")
    if sekunden < 86400:
        n = sekunden // 3600
        return "%d Stunde%s" % (n, "" if n == 1 else "n")
    n = sekunden // 86400
    return "%d Tag%s" % (n, "" if n == 1 else "en")
