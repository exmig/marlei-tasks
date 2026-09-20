"""
Der Fehlerbericht: der Server erzeugt ihn, verschickt wird er von Hand.

**Er sammelt, was bei einer Rueckfrage sonst einzeln erfragt werden
muesste** -- worauf der Server laeuft, welche Version, wie gross die
Ablage ist. Das erspart drei Mails, bevor die erste Antwort kommt.

**Der Server verschickt nichts.** Er erzeugt den Text, der Betreiber
liest ihn und schickt ihn. Ein Werkzeug, das ungefragt nach draussen
redet, ist genau das, wovor man Werkzeuge sonst warnt -- und hier waere
es besonders heikel: In einer Aufgabenverwaltung steht, woran eine Firma
arbeitet.

**Deshalb sind es zwei Bloecke, und der zweite ist freiwillig.** Ohne
Haken enthaelt der Bericht nur Angaben, die auf jedem Server gleich
aussehen -- **nichts aus den Projekten.** Mit Haken kommen Ablageorte,
Groessen und Zahlen dazu; auch dann keine Titel, keine Texte, keine
Namen. Was gezaehlt wird, steht in ``_umgebung``, damit man es
nachlesen kann, bevor man den Haken setzt.

**Unter Windows stehen dieselben Zeilen da, nur aus anderen Quellen.**
Es gibt dort kein ``/etc/os-release``, kein ``dpkg-query`` und kein
``uptime`` -- die Auskuenfte stehen in der Registry und beim Kernel, und
das Ablesen steht in ``windows.py``. **Was nicht ersetzt wird, wird
gesagt:** Die Zeile ``nginx`` verschwindet nicht, sie sagt, dass es dort
keinen gibt.

**Von hier kommt auch die Karte Serverdetails** (``karte()``), und das
ist Absicht: Zwei Quellen liefen auseinander, und dann stuende in der
Fehlermeldung ein anderer Kernel als auf der Seite, die der Betreiber
gerade vor sich hat. Aus MARLEI Boot uebernommen -- dort steht derselbe
Satz im selben Modul.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version as paketversion
from pathlib import Path

import auslastung
import datenbank
import export
import firewall
import windows

# Welches System hier antwortet -- wie in auslastung.py und firewall.py
# eine Variable, damit die Testreihe beide Seiten pruefen kann.
SYSTEM = os.name

ZEITLIMIT = 5.0

# Wie lange die Karte gilt, bevor sie neu gelesen wird. Eine Minute:
# Kernel und Paketversionen aendern sich zwischen zwei Aufrufen nicht --
# was sie aendert, ein Neustart oder ein apt upgrade, nimmt die Seite
# ohnehin mit.
KARTEN_TAKT = 60
_KARTE: dict = {"werte": None, "zeit": 0.0}


def _lauf(befehl: list[str]) -> str:
    """Einen Befehl ausfuehren und seine Ausgabe holen -- oder "" .

    **Fehlt das Programm, ist das kein Fehler, sondern eine Antwort:**
    Auf einem System ohne systemd gibt es kein systemd-detect-virt, und
    die Karte sagt dann "nicht feststellbar" statt abzustuerzen.
    """
    if not shutil.which(befehl[0]):
        return ""
    try:
        fertig = subprocess.run(befehl, capture_output=True, text=True,
                                timeout=ZEITLIMIT)
    except (OSError, subprocess.SubprocessError):
        return ""
    return fertig.stdout.strip()


def _distribution() -> str:
    """Name und Version aus /etc/os-release -- unter Windows aus der
    Registry.

    **Die Zeile heisst trotzdem weiter *Distribution*.** Sie beantwortet
    auf beiden Systemen dieselbe Frage -- *welches System ist das genau* --,
    und eine Zeile, die je nach Maschine anders heisst, laesst sich in zwei
    Fehlerberichten nicht nebeneinanderlegen.
    """
    if SYSTEM == "nt":
        return windows.systemname()
    werte = {}
    try:
        for zeile in Path("/etc/os-release").read_text(
                encoding="utf-8").splitlines():
            schluessel, trenner, wert = zeile.partition("=")
            if trenner:
                werte[schluessel.strip()] = wert.strip().strip('"')
    except OSError:
        return ""
    return werte.get("PRETTY_NAME") or werte.get("NAME", "")


# Was systemd-detect-virt ausgibt und was es heisst.
#
# **"oracle" ist VirtualBox.** Die Ausgabe nennt den Hersteller, nicht das
# Produkt -- wer das nicht weiss, liest den Datenbankhersteller. Der
# Rohwert bleibt trotzdem in Klammern stehen: Er ist das, wonach man
# sucht, wenn man den Fehler nachstellen will.
VIRT_NAMEN = {
    "oracle": "VirtualBox",
    "kvm": "KVM",
    "qemu": "QEMU",
    "vmware": "VMware",
    "microsoft": "Hyper-V",
    "xen": "Xen",
    "lxc": "LXC-Container",
    "lxc-libvirt": "LXC-Container",
    "systemd-nspawn": "nspawn-Container",
    "docker": "Docker-Container",
    "podman": "Podman-Container",
    "proxmox": "Proxmox",
}


def _virtualisierung() -> str:
    """Laeuft der Server in einer VM, und wenn ja, in welcher?

    **"none" ist eine Antwort und keine Fehlanzeige** -- sie heisst: Der
    Server laeuft auf Blech.
    """
    if SYSTEM == "nt":
        return windows.virtualisierung()
    roh = _lauf(["systemd-detect-virt"])
    if not roh:
        return "nicht feststellbar"
    if roh == "none":
        return "keine — der Server läuft auf Blech"
    name = VIRT_NAMEN.get(roh)
    return "%s (%s)" % (name, roh) if name else roh


def _dauer(sekunden: int) -> str:
    """Eine Dauer als Angabe im Nominativ: "3 Tage, 2 Stunden".

    **Nicht dasselbe wie ``auslastung.dauer_dativ``, und deshalb hier:**
    Dort steht die Dauer hinter "seit" und braucht den Dativ (*seit 2
    Tagen*); hier steht sie in einer Tabellenzeile *Laufzeit* und braucht
    den Nominativ (*2 Tage*). Und dort ist die Datei aus MARLEI Boot
    abgeschrieben -- eine zweite Formulierung gehoert nicht hinein.

    Zwei Einheiten, nicht vier: Genau so viel sagt ``uptime -p`` auf der
    anderen Seite auch.
    """
    if sekunden < 60:
        return "weniger als eine Minute"
    tage, rest = divmod(int(sekunden), 86400)
    stunden, rest = divmod(rest, 3600)
    minuten = rest // 60
    teile = []
    if tage:
        teile.append("%d Tag%s" % (tage, "" if tage == 1 else "e"))
    if stunden:
        teile.append("%d Stunde%s" % (stunden, "" if stunden == 1 else "n"))
    if minuten and not tage:
        teile.append("%d Minute%s" % (minuten, "" if minuten == 1 else "n"))
    return ", ".join(teile[:2])


def laufzeit() -> str:
    """Wie lange die MASCHINE schon laeuft -- "up 3 days, 2 hours".

    Nicht zu verwechseln mit ``auslastung.dienst()``: Das misst diesen
    Dienst. Zwei Zahlen, zwei Fragen -- und wenn sie auseinandergehen,
    ist der Dienst zwischendurch neu gestartet.

    **Unter Windows steht die Dauer auf Deutsch da, unter Linux auf
    Englisch** -- und das bleibt so: Links ist es die Ausgabe von
    ``uptime -p``, die diese Anwendung nicht uebersetzt, rechts eine Zahl
    vom Kernel, die hier erst zu einem Satzstueck wird. Eine Uebersetzung
    fremder Programmausgaben faengt klein an und hoert nie auf.
    """
    if SYSTEM == "nt":
        sekunden = windows.laufzeit_sekunden()
        return "" if sekunden is None else _dauer(sekunden)
    return _lauf(["uptime", "-p"])


def _paket(name: str, namen: list[str]) -> str:
    """Die Version eines Debian-Pakets, gefragt unter mehreren Namen.

    **Eine leere Version ist keine Auskunft:** Debian kennt Paketnamen,
    ohne dass sie installiert sein muessen -- dpkg-query gibt dann eine
    Zeile mit leerem Feld aus. Genommen wird der erste Name MIT Version.
    """
    ausgabe = _lauf(["dpkg-query", "-W", "-f=${Package} ${Version}\n",
                     *namen])
    gefunden = {}
    for zeile in ausgabe.splitlines():
        # NICHT "name": Das ist der Parameter, und ihn hier zu
        # ueberschreiben liess die Klammer unten immer verschwinden --
        # verglichen wurde dann mit dem zuletzt gelesenen Paketnamen
        # statt mit dem der Zeile. Gefunden von der Pruefung, nicht beim
        # Lesen.
        paket, _, wert = zeile.partition(" ")
        if paket and wert.strip():
            gefunden[paket] = wert.strip()
    for n in namen:
        if n in gefunden:
            # Der Paketname nur dann in Klammern, wenn er etwas sagt: Er
            # soll heissen "gefunden unter einem anderen Namen als
            # erwartet". Heisst das Paket wie die Zeile, ist die Klammer
            # Rauschen -- auf dev-marlei stand am 07.09.2026
            # "1.26.3-3+deb13u7 (nginx)" in der Zeile nginx.
            return gefunden[n] + ("" if n == name else " (%s)" % n)
    return "nicht installiert"


def _pythonpaket(name: str) -> str:
    """Die Version einer installierten Python-Abhaengigkeit."""
    try:
        return paketversion(name)
    except PackageNotFoundError:
        return "nicht installiert"


def _maschine() -> list[tuple[str, str]]:
    """Worauf dieser Server laeuft -- dieselben Zeilen wie im Bericht."""
    return [
        ("Distribution", _distribution() or "unbekannt"),
        ("Kernel", "%s %s" % (platform.system(), platform.release())),
        ("Architektur", platform.machine() or "unbekannt"),
        # NACHGETRAGEN FUER DIE WINDOWS-FASSUNG, und sie gilt auf beiden
        # Systemen: Die Kernzahl stand bisher nur in der Unterzeile der
        # Kachel *Last* -- und die gibt es unter Windows nicht, weil
        # Windows kein Lastmittel fuehrt. Dass sie im Fehlerbericht
        # ohnehin hingehoert, ist der zweite Grund: "zu langsam" ist ohne
        # sie keine Angabe.
        ("Prozessorkerne", auslastung.kerne()),
        ("Virtualisierung", _virtualisierung()),
    ]


def _zeile(name: str, wert) -> str:
    return "%-22s %s" % (name + ":", wert)


def _grundstock(stand: str) -> list[str]:
    """Was auf jedem Server gleich aussieht.

    **Kein Pfad, keine Adresse, keine Zahl aus dem Bestand.** Genau
    deshalb braucht dieser Block keinen Haken: Er sagt nichts, was nicht
    auf jeder Installation dasselbe waere.
    """
    zeilen = [
        "MARLEI Tasks — Fehlerbericht",
        "=" * 40,
        "",
        _zeile("Version", stand or "unbekannt (nicht über install.sh)"),
    ]
    # DIESELBE QUELLE WIE DIE KARTE Serverdetails, und genau deshalb
    # steht hier keine zweite Ableserei: Zwei Quellen liefen
    # auseinander, und dann nennt die Mail einen anderen Kernel als die
    # Seite, die der Betreiber gerade vor sich hat.
    zeilen += [_zeile(name, wert) for name, wert in _maschine()]
    zeilen += [
        _zeile("Python", platform.python_version()),
        _zeile("SQLite", __import__("sqlite3").sqlite_version),
    ]
    return zeilen


def _umgebung(conn) -> list[str]:
    """Der freiwillige Block -- Groessen und Zahlen, keine Inhalte.

    **Gezaehlt wird, nicht abgeschrieben.** Es steht hier, wie viele
    Eintraege es gibt, nicht wie sie heissen; wie gross die Ablage ist,
    nicht was darin steht. Der Unterschied ist der Grund, warum dieser
    Block ueberhaupt verschickbar ist.
    """
    zeilen = ["", "Serverumgebung (freiwillig)", "-" * 40, ""]

    db = Path(datenbank.DB_PFAD)
    zeilen.append(_zeile("Ablage", str(db)))
    try:
        zeilen.append(_zeile("Größe der Ablage", "%d Bytes" % db.stat().st_size))
    except OSError:
        zeilen.append(_zeile("Größe der Ablage", "nicht lesbar"))
    # str(None) waere "None" und damit wahr -- dieselbe Falle wie bei
    # Path(""), nur eine Ebene spaeter. In einem Fehlerbericht ist
    # "Export: None" die unbrauchbarste Zeile von allen: Sie sieht aus wie
    # eine Angabe.
    zeilen.append(_zeile("Export", str(export.ZIEL) if export.ZIEL
                         else "nicht eingerichtet"))

    lage = firewall.lage()
    zeilen.append(_zeile(
        "Firewall",
        ", ".join(lage["namen"]) + " — aktiv" if lage["aktiv"]
        else ("gefunden, aus" if lage["gefunden"] else "keine gefunden")))

    projekte = datenbank.projekte(conn)
    zeilen += ["", _zeile("Projekte", len(projekte))]
    for p in projekte:
        b = p["bestand"]
        zeilen.append(
            "  %-8s %3d Sammlung · %3d Aufgaben · %3d Meilensteine · "
            "%3d Entscheidungen"
            % (p["kennung"], b["sammlung"], b["aufgaben"], b["meilensteine"],
               b["entscheidungen"]))
    return zeilen


def text(conn, stand: str = "", umgebung: bool = False) -> str:
    """Der ganze Bericht.

    Ohne ``umgebung`` bleibt es beim Grundstock -- und der ist so knapp,
    dass man ihn in zwei Sekunden durchliest, bevor man ihn abschickt.
    """
    zeilen = _grundstock(stand)
    if umgebung:
        zeilen += _umgebung(conn)
    zeilen += ["", "-" * 40,
               "Bitte beschreiben Sie darunter, was nicht funktioniert:",
               "", "  Wann tritt es auf / was war die letzte Aktion davor:",
               "", "  Betrifft es einen Reiter oder die ganze Anwendung:",
               ""]
    return "\n".join(zeilen)


def karte(stand: str = "") -> dict:
    """Was die Karte *Serverdetails* zeigt -- zwei Bloecke und ihr Takt.

    ``maschine`` ist das, worauf der Server laeuft; ``dienste`` sind die
    vier, deren Version zaehlt, wenn eine fremde Fehlermeldung
    hereinkommt. **In Boot ist das Beispiel dnsmasq 2.89 gegen 2.90**;
    hier sind es FastAPI und uvicorn -- eine Meldung aus dem Innern von
    Starlette ist ohne die Version nicht einzuordnen, und die Rueckfrage
    danach kostet einen Tag.

    **Was hier NICHT hineingehoert, ist eine Paketliste.** Diese
    Oberflaeche kann ohne Kennwort laufen; jede Zeile mehr ist fuer jeden im
    Netz eine Zeile mehr Einkaufsliste. Aufgenommen wird, was der Bericht
    braucht -- und sonst nichts.

    **Und nichts aus den Projekten.** Die Karte beschreibt die Maschine;
    dieselbe Angabe ist auf jedem Server dieselbe.
    """
    jetzt = time.monotonic()
    if not _KARTE["werte"] or jetzt - _KARTE["zeit"] > KARTEN_TAKT:
        _KARTE["werte"] = {
            "maschine": _maschine() + [
                ("Laufzeit", laufzeit() or "unbekannt"),
                ("Python", platform.python_version()),
                ("SQLite", __import__("sqlite3").sqlite_version),
            ],
            "dienste": [
                # **Die Zeile bleibt stehen, auch wo es keinen nginx
                # gibt.** Ein "nicht installiert" waere dort die falsche
                # Auskunft -- es fehlt nichts, es ist keiner vorgesehen:
                # Unter Windows hoert uvicorn selbst auf dem Port der
                # Oberflaeche. Eine Zeile, die das sagt, ist mehr wert als
                # eine fehlende Zeile, die jemand sucht.
                ("nginx",
                 "nicht vorgesehen — uvicorn liefert die Oberfläche "
                 "selbst aus" if SYSTEM == "nt"
                 else _paket("nginx", ["nginx-core", "nginx-light",
                                       "nginx-full", "nginx"])),
                ("fastapi", _pythonpaket("fastapi")),
                ("uvicorn", _pythonpaket("uvicorn")),
            ],
        }
        _KARTE["zeit"] = jetzt

    # DER STEMPEL WIRD NICHT MITGEPUFFERT, und das ist kein Detail: Er
    # kommt vom Aufrufer, und ein Puffer, der ein Argument verschluckt,
    # ist eine Falle -- der zweite Aufruf mit einem anderen Wert bekaeme
    # den ersten zurueck. Aufgefallen in der Pruefung, nicht am Server.
    #
    # Diese Anwendung ist ohnehin kein Paket: Ihre Version ist der Stand,
    # den install.sh gestempelt hat -- derselbe, der in der Fusszeile
    # jeder Seite steht.
    gelesen = _KARTE["werte"]
    return {
        "maschine": gelesen["maschine"],
        "dienste": [("marlei-tasks",
                     stand or "kein Stempel (nicht über install.sh "
                              "installiert)")] + gelesen["dienste"],
        "takt": KARTEN_TAKT,
    }
