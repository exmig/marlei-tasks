"""
Die Anmeldung -- ein Kennwort vor jeder Seite, und nicht mehr.

**Ein Schloss, keine Benutzerverwaltung.** Es gibt ein Kennwort fuer
diese Installation und niemanden, dem es gehoert. Benutzer und Rechte
kommen mit dem zweiten Menschen und sind die Linie zu Pro
(docs/aufbau.md, Abschnitt 8); ein Schloss dagegen gehoert in beide
Fassungen.

**Ein eigenes Kennwort, nicht das des Systems.** Das Windows-Kennwort
durchzureichen ginge technisch, aber diese Oberflaeche spricht http: Das
Formular schickte das Kennwort des Kontos im Klartext durchs Netz, bei
einem Microsoft-Konto das fuer Mail und Ablage gleich mit. Wird dieses
hier mitgelesen, ist Tasks offen und nicht der Rechner.

**Gespeichert wird ein Hash, kein Kennwort** -- in der Umgebungsdatei als
MARLEI_KENNWORT_HASH, neben den uebrigen Einstellungen. Die Datei ist nur
fuer Administratoren bzw. root und den Dienst lesbar. Vergessen heisst
deshalb neu setzen und nicht wiederherstellen, und neu setzen darf, wer
Administrator der Maschine ist: install.ps1 -Kennwort bzw.
MARLEI_KENNWORT=neu fuer install.sh. Dieselbe Grenze wie bei der
Werkseinstellung -- wer an die Maschine darf, darf an Tasks.

**Nur Standardbibliothek.** PBKDF2 mit SHA-256 liegt in hashlib, in jeder
Python-Fassung und auf jedem System; ein Paket dafuer waere eine Zeile
mehr in requirements.txt, die bei jedem Update mitwill.

Aufgerufen als Skript liest dieses Modul ein Kennwort von der
Standardeingabe und schreibt den Hash hin -- so rechnen install.sh und
install.ps1 ihn aus, ohne dass das Kennwort je auf einer Befehlszeile
steht.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sys
import time

# Wie der Wert in der Umgebungsdatei heisst.
UMGEBUNG = "MARLEI_KENNWORT_HASH"

# Das Cookie, das eine Anmeldung traegt.
COOKIE = "marlei_anmeldung"

# Wie lange eine Anmeldung gilt. Ein Monat: Wer das Werkzeug taeglich
# benutzt, soll sich nicht taeglich anmelden -- eine Huerde, die jeden
# Morgen im Weg steht, wird irgendwann abgeschaltet.
GUELTIG = 30 * 24 * 3600

# Mindestlaenge. Mehr Regeln gibt es nicht: Vorschriften ueber Ziffern
# und Sonderzeichen fuehren zu "Passwort1!", Laenge fuehrt zu Laenge.
MINDESTLAENGE = 8

# Runden fuer PBKDF2. Die Zahl steht im Hash mit -- eine spaetere
# Erhoehung macht alte Hashes nicht ungueltig, sie gelten mit ihrer
# eigenen Zahl weiter.
RUNDEN = 600_000

# **Kein Dollarzeichen im Hash, und das ist Absicht.** Die uebliche
# Schreibweise solcher Hashes trennt mit $, und die Umgebungsdatei lesen
# zwei verschiedene Leser -- systemd und start.ps1. Ein $, ein
# Anfuehrungszeichen oder ein Backslash ist nicht in jedem davon nur ein
# Zeichen; Doppelpunkt und Hex sind es in beiden.
_VERFAHREN = "pbkdf2-sha256"


def hash_bilden(kennwort: str, runden: int = RUNDEN) -> str:
    """Aus einem Kennwort den Wert, der in die Umgebungsdatei kommt."""
    salz = secrets.token_bytes(16)
    wert = hashlib.pbkdf2_hmac("sha256", kennwort.encode("utf-8"), salz,
                               runden)
    return "%s:%d:%s:%s" % (_VERFAHREN, runden, salz.hex(), wert.hex())


def gesetzt() -> str:
    """Der Hash aus der Umgebung, oder leer.

    **Bei jedem Aufruf gelesen und nicht beim Laden des Moduls** -- die
    Pruefungen schalten die Anmeldung ein und wieder aus, und ein Wert,
    der beim Start eingefroren wird, liesse sich dort nicht pruefen.
    """
    return os.environ.get(UMGEBUNG, "").strip()


def kennwort_stimmt(kennwort: str, gespeichert: str) -> bool:
    """Passt das Kennwort zu dem Hash?

    **Ein kaputter Hash heisst nein, nicht Fehler.** Ein Tippfehler in der
    Umgebungsdatei soll die Tuer zu lassen und nicht die Seite mit einem
    Absturz beantworten.
    """
    try:
        verfahren, runden, salz, wert = gespeichert.split(":")
        if verfahren != _VERFAHREN:
            return False
        probe = hashlib.pbkdf2_hmac("sha256", kennwort.encode("utf-8"),
                                    bytes.fromhex(salz), int(runden))
        return hmac.compare_digest(probe, bytes.fromhex(wert))
    except (ValueError, TypeError):
        return False


def _schluessel(gespeichert: str) -> bytes:
    """Womit das Cookie unterschrieben wird: abgeleitet aus dem Hash.

    **Das ist der Grund, warum es keinen zweiten Geheimwert gibt.** Wird
    das Kennwort neu gesetzt, aendert sich der Hash, damit der Schluessel,
    damit jede Unterschrift -- und jede bestehende Anmeldung ist ungueltig,
    ohne dass irgendwo eine Liste gefuehrt wird. Wer ein Kennwort neu
    setzt, weil es jemand anderes kennt, will genau das.
    """
    return hashlib.sha256(b"marlei-anmeldung:" + gespeichert.encode()).digest()


def cookie_bilden(gespeichert: str, jetzt: float | None = None) -> str:
    """Der Wert des Anmeldecookies: Ablauf und Unterschrift."""
    ablauf = int((time.time() if jetzt is None else jetzt) + GUELTIG)
    unterschrift = hmac.new(_schluessel(gespeichert), str(ablauf).encode(),
                            hashlib.sha256).hexdigest()
    return "%d.%s" % (ablauf, unterschrift)


def cookie_gilt(wert: str, gespeichert: str,
                jetzt: float | None = None) -> bool:
    """Traegt dieses Cookie eine gueltige, nicht abgelaufene Anmeldung?"""
    if not wert or not gespeichert:
        return False
    ablauf, _, unterschrift = wert.partition(".")
    if not ablauf.isdigit():
        return False
    erwartet = hmac.new(_schluessel(gespeichert), ablauf.encode(),
                        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(erwartet, unterschrift):
        return False
    return int(ablauf) > (time.time() if jetzt is None else jetzt)


def _als_skript() -> int:
    """Kennwort von der Standardeingabe, Hash auf die Standardausgabe.

    Eine Zeile, ohne den Zeilenumbruch am Ende. Zu kurz ist ein Fehler
    mit Rueckgabewert 2 und einem Satz auf der Fehlerausgabe -- die
    Installationsskripte fragen dann noch einmal.

    **Gelesen werden Bytes, und sie sind UTF-8.** Liest Python unter
    Windows eine umgeleitete Eingabe als Text, nimmt es die Codepage des
    Systems -- ein Umlaut im Kennwort ergaebe dann einen anderen Hash als
    derselbe Umlaut im Anmeldeformular, und das Kennwort stimmte nie.
    "-sig", weil ein Byte-Order-Mark sonst Teil des Kennworts wuerde.
    """
    zeile = sys.stdin.buffer.readline().decode("utf-8-sig", errors="replace")
    kennwort = zeile.rstrip("\r\n")
    if len(kennwort) < MINDESTLAENGE:
        print("Das Kennwort braucht mindestens %d Zeichen." % MINDESTLAENGE,
              file=sys.stderr)
        return 2
    print(hash_bilden(kennwort))
    return 0


if __name__ == "__main__":
    sys.exit(_als_skript())
