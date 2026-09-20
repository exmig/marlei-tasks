"""
Die lokale Firewall: gemeldet, nicht angefasst.

**Der Bootserver richtet keine Firewall ein.** Sie gehoert der Maschine,
auf der er laeuft, und damit dem Betreiber -- dieselbe Grenze wie bei der
Netzkonfiguration, die diese Anwendung ebenfalls nur abliest. Ein Werkzeug,
das ungefragt Regeln auf einer fremden Maschine setzt, ist das, wovor man
Werkzeuge sonst warnt; und `ufw enable` ueber eine SSH-Sitzung sperrt aus,
wer 22 vergisst.

**Was bleibt, ist die Frage, die sich auf jedem Server gleich stellt:
Ist hier eine Firewall an, und blockt sie mich?** Bei MARLEI Tasks ist
die Antwort kurz -- es ist ein Port, nicht sieben ueber vier Dienste --,
und der Einwand dagegen ist bekannt und ueberstimmt (docs/uebernahme.md,
Abschnitt 6): *Die Antwort "nichts im Weg" ist eine Auskunft, auch wenn
sie kurz ist.*

**Der Unterschied zu Boot ist zugleich beruhigend:** Wer diese Seite
sieht, kommt offensichtlich durch. Ein zugemachter Port faellt hier
sofort auf und nicht erst beim naechsten Netzstart.

**Gemeldet wird, nicht geprueft, und das hat einen technischen Grund.** Diese
Anwendung laeuft als Benutzer ``pxeweb`` mit ``NoNewPrivileges=yes``; ``sudo``
gibt es dort nicht, und das ist Absicht. Ohne root ist zu erfahren:

    ob eine Firewall installiert ist      ja
    ob sie eingeschaltet ist              ja
    ob sie 69/udp durchlaesst             NEIN -- die Regeln liegen root-only

Die Karte sagt das auch. Ein Kasten, der aussieht, als haette er geprueft,
waere schlimmer als einer, der sagt, was er nicht weiss.

**Unter Windows ist es dieselbe Haltung mit einer anderen Quelle.** Die
Firewall gehoert dort erst recht der Maschine -- sie ist Teil des Systems
und von Haus aus an. Gelesen wird der Schalter, den ``netsh advfirewall
set`` umschreibt; er steht in der Registry und ist ohne
Administratorrechte lesbar, genau wie ``ufw.conf`` ohne root. Das Ablesen
steht in ``windows.py``, die Entscheidung, was es bedeutet, hier.

**Und eine dritte Antwort kommt dort dazu: nicht feststellbar.** Fehlt der
Schalter, waere "also an" ein Schluss aus der Vorgabe des Systems und
keine Auskunft. Windows laeuft von Haus aus mit eingeschalteter Firewall
-- eben deshalb ist das Raten hier besonders billig und besonders falsch.

**Zwei Fallen beim Fragen, und beide heissen ``is-active``.** Die erste:
``systemctl is-active ufw`` meldet ``active``, auch wenn die Firewall
abgeschaltet ist -- die Unit laeuft dann als leerer Rahmen. Gefragt wird
deshalb ``/etc/ufw/ufw.conf`` nach ``ENABLED``; das ist die Datei, die
``ufw enable`` schreibt, und sie ist ohne root lesbar. Die zweite:
``is-active`` antwortet ``inactive`` auch fuer eine Einheit, die es gar
nicht gibt -- siehe ``_systemd()``.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import windows

# Welches System hier antwortet. Wie in auslastung.py eine Variable und
# keine Abfrage im Code -- so prueft die Testreihe beide Seiten auf
# derselben Maschine.
SYSTEM = os.name

# Die Datei, die "ufw enable" umschreibt. Ueber die Umgebung zu setzen,
# damit der Test nicht auf ein echtes ufw angewiesen ist.
UFW_CONF = Path(os.environ.get("MARLEI_UFW_CONF", "") or "/etc/ufw/ufw.conf")

# Die anderen beiden fragt man ueber systemd. Bei ihnen gibt es die Falle
# von ufw nicht: Laeuft die Unit, ist ein Regelwerk geladen. Dafuer eine
# zweite -- siehe _systemd().
UEBER_SYSTEMD = ("nftables", "firewalld")

ZEITLIMIT = 5.0

_ENABLED = re.compile(r"^\s*ENABLED\s*=\s*(\w+)", re.M | re.I)

# --------------------------------------------------------------------------
# Was MARLEI Tasks braucht
# --------------------------------------------------------------------------
#
# **Reine Auskunft, keine Pruefung.** Der Server sagt, worauf er hoert; ob
# die Firewall es durchlaesst, sieht nur der Betreiber.
#
# **Eine Zeile statt Boots neun**, und das ist der ganze Unterschied
# zwischen den Produkten an dieser Stelle: Der Bootweg braucht sieben
# Ports ueber vier Dienste, weil ein Rechner ueber das Netz startet.
# Hier redet nur ein Browser mit einer Anwendung.
PORTS = (
    {"port": "80/tcp", "dienst": "nginx", "oberflaeche": True,
     "wofuer": "diese Oberfläche — mehr nicht"},
    {"port": "22/tcp", "dienst": "sshd",
     "wofuer": "gehört nicht dazu — aber wer ihn zumacht, während er "
               "über ihn angemeldet ist, sperrt sich aus"},
)

# Dieselben zwei Zeilen fuer Windows, und beide heissen anders.
#
# **Die erste, weil es den nginx dort nicht gibt:** Die Anwendung hoert
# selbst auf dem Port der Oberflaeche. Das ist keine Nachlaessigkeit,
# sondern faellt ohne Reverse Proxy so an -- und damit faellt auch der
# Satz weg, dass ein zweiter Port nicht offen gehoert.
#
# **Die zweite, weil man sich unter Windows anders aussperrt:** Wer den
# Remotedesktop zumacht, waehrend er ueber ihn angemeldet ist, sitzt vor
# demselben Problem wie der, der 22 zumacht. Dieselbe Warnung, anderer
# Port.
WINDOWS_PORTS = (
    {"port": "8081/tcp", "dienst": "MARLEI Tasks", "oberflaeche": True,
     "wofuer": "diese Oberfläche — mehr nicht"},
    {"port": "3389/tcp", "dienst": "Remotedesktop",
     "wofuer": "gehört nicht dazu — aber wer ihn zumacht, während er "
               "über ihn angemeldet ist, sperrt sich aus"},
)


def ports(oberflaeche: int = 80, system: str = "") -> tuple:
    """Die Portliste, mit dem Port, unter dem die Oberfläche WIRKLICH
    erreichbar ist.

    **80 ist die Vorgabe und auf einer Maschine mit MARLEI Boot falsch.**
    Dort laeuft dieses Werkzeug auf einem eigenen Port (MARLEI_PORT),
    weil Boots nginx-vhost die 80 mit einem ``default_server`` haelt.

    Aufgefallen am 07.09.2026 an der ersten echten Installation: Die
    Karte nannte 80, erreichbar war 8081. Wer danach eine Regel schreibt,
    oeffnet den falschen Port und sucht eine Stunde -- und die Karte
    haette ihn selbst dorthin geschickt.

    Woher die Zahl kommt: aus MARLEI_BASE_URL, also aus der Adresse, die
    im Kopfband steht. Sie ist das, was jemand tatsaechlich aufruft.

    **Eingesetzt wird an der Zeile mit ``oberflaeche`` und nicht an der
    mit dem Namen ``nginx``:** Unter Windows heisst dieselbe Zeile anders,
    weil dort kein nginx davorsteht. Wer nach dem Namen sucht, setzt die
    Zahl dann nirgends ein -- und die Karte nennt wieder die 80.
    """
    liste = WINDOWS_PORTS if (system or SYSTEM) == "nt" else PORTS
    return tuple(dict(z, port="%d/tcp" % oberflaeche)
                 if z.get("oberflaeche") else dict(z)
                 for z in liste)

# Und der Port, der ausdruecklich NICHT offen gehoert.
# **Mit %d, nicht mit 80.** Der Satz stand hier mit fester Zahl und war
# damit auf jeder Maschine falsch, auf der die Oberflaeche nicht auf 80
# liegt -- also auf jeder mit MARLEI Boot. Gefunden an der laufenden
# Installation, EINE ZEILE unter der Portliste, die kurz vorher aus
# demselben Grund korrigiert worden war: Die Liste zog mit, der Satz
# darunter nicht.
NICHT_OEFFNEN = (
    "18081/tcp gehört nicht dazu. Dort hört die Anwendung selbst, aber nur "
    "auf 127.0.0.1 — von außen kommt man über nginx auf %d, und dabei soll "
    "es bleiben."
)


# Unter Windows gibt es diesen zweiten Port nicht -- und deshalb steht
# hier nicht einfach nichts: **Dass die Liste vollstaendig ist, ist selbst
# eine Auskunft.** Ein Kasten, der an dieser Stelle schweigt, liest sich
# wie einer, der die Frage nicht bedacht hat.
WINDOWS_NICHT_OEFFNEN = (
    "Ein zweiter Port ist hier nicht im Spiel: Die Anwendung hört selbst "
    "auf %d, ohne nginx davor. Damit ist die Liste vollständig — sonst "
    "muss für dieses Werkzeug nichts offen sein."
)


def nicht_oeffnen(oberflaeche: int = 80, system: str = "") -> str:
    """Der Satz mit dem Port, der wirklich gilt -- wie ``ports()``."""
    satz = (WINDOWS_NICHT_OEFFNEN if (system or SYSTEM) == "nt"
            else NICHT_OEFFNEN)
    return satz % oberflaeche


def _ufw() -> dict | None:
    """Ist ufw da, und steht es auf an?"""
    try:
        text = UFW_CONF.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    treffer = _ENABLED.search(text)
    return {"name": "ufw",
            "an": bool(treffer) and treffer.group(1).lower() == "yes"}


def _systemd(namen: tuple) -> list:
    """Welche der genannten Einheiten es gibt -- und welche davon laufen.

    **Die zweite Falle beim Fragen, und sie sitzt eine Ebene tiefer als die
    von ufw:** ``systemctl is-active firewalld`` antwortet ``inactive`` auch
    dann, wenn firewalld auf dieser Maschine gar nicht installiert ist. Wer
    nur darauf hoert, schreibt "installiert, aber aus" neben etwas, das es
    nicht gibt -- eine Falschaussage genau dort, wo die Karte sonst nichts
    behauptet. Gefragt wird deshalb nach ``LoadState``: ``loaded`` heisst,
    die Unit ist da; ``not-found`` heisst, sie ist es nicht.
    """
    try:
        lauf = subprocess.run(
            ["systemctl", "show", "-p", "Id", "-p", "LoadState",
             "-p", "ActiveState", *namen],
            capture_output=True, text=True, timeout=ZEITLIMIT, check=False)
    except (OSError, subprocess.SubprocessError):
        # Kein systemd erreichbar -- etwa beim Entwickeln auf einem anderen
        # System. Dann lieber schweigen als etwas behaupten.
        return []
    gefunden = []
    # Ein Block je Einheit, durch eine Leerzeile getrennt. Zugeordnet wird
    # ueber die Id im Block und nicht ueber die Reihenfolge: Die stimmt
    # zwar, aber sie ist nirgends zugesichert.
    for block in lauf.stdout.split("\n\n"):
        felder = dict(z.split("=", 1) for z in block.splitlines() if "=" in z)
        name = felder.get("Id", "").rsplit(".", 1)[0]
        if name not in namen or felder.get("LoadState") != "loaded":
            continue
        gefunden.append({"name": name,
                         "an": felder.get("ActiveState") == "active"})
    return gefunden


def lage() -> dict:
    """Was diese Maschine an Firewall hat -- soweit es ohne root zu sehen ist.

    ``gefunden`` sind die installierten, jede mit ``an``. ``aktiv`` ist wahr,
    sobald eine davon eingeschaltet ist; ``namen`` nennt die eingeschalteten
    fuer die eine Zeile unter den Diensten.

    ``unklar`` ist die dritte Antwort und kommt von der Windows-Seite:
    **keine eingeschaltet, aber auch keine, von der sich sagen liesse,
    dass sie aus ist.** Ohne dieses Feld stuende auf der Karte "nichts im
    Weg" -- eine Zusage, fuer die dann nichts vorliegt. Unter Linux ist es
    nie gesetzt: Eine ufw.conf, die sich lesen laesst, sagt ja oder nein.
    """
    if SYSTEM == "nt":
        gemeldet = windows.firewall()
        gefunden = gemeldet["gefunden"]
        quelle = gemeldet["quelle"]
    else:
        gefunden = [f for f in (_ufw(),) if f] + _systemd(UEBER_SYSTEMD)
        # Wovon die Auskunft stammt -- damit auf der Karte steht, woher sie
        # kommt, und niemand sie fuer eine Pruefung haelt.
        quelle = str(UFW_CONF)
    # "kurz", wo es das gibt: Im Kartenkopf stehen die Namen hintereinander.
    laufende = [f.get("kurz") or f["name"] for f in gefunden if f["an"]]
    return {
        "gefunden": gefunden,
        "aktiv": bool(laufende),
        "namen": laufende,
        "unklar": not laufende and any(f["an"] is None for f in gefunden),
        "quelle": quelle,
    }
