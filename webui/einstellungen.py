"""
Was der Betreiber in der Oberflaeche entscheidet -- neben der Datenbank.

**Zwei Ablagen, und sie unterscheiden sich nicht im Format, sondern
darin, wer sie aendern darf.** In der Umgebungsdatei steht, *wie dieser
Server aufgesetzt ist*: Ablageorte, Adresse, Kennwort-Hash. Sie wird
einmal beim Start gelesen und gehoert dem, der die Maschine aufgesetzt
hat -- die Karte *Einstellungen* zeigt sie und aendert nichts daran.

Hier steht, *wie er betrieben wird*: zur Laufzeit gelesen und
geschrieben, ohne Neustart wirksam. Der Name ist derselbe wie in MARLEI
Boot, und die Doppeldeutigkeit mit der Karte ist dort dieselbe -- die
Entsprechung zwischen den Modulen wiegt schwerer als ein eigener Name.

**Die Werkseinstellung fasst diese Datei nicht an.** In Boot tut sie es,
weil sie dort den ganzen Ablageordner ausraeumt; hier setzt sie das
gewaehlte Projekt zurueck und sonst nichts. Das ist gut so, und zwar
gerade beim Offline-Modus: Wer seinen Bestand zurueckwirft, hat die
Maschine damit nicht ans Netz gehaengt.

Warum ueberhaupt in der Oberflaeche und nicht in der Umgebungsdatei:
siehe ``offline`` unten.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

import datenbank

DATEI = Path(os.environ.get("MARLEI_EINSTELLUNGEN", "")
             or Path(datenbank.DB_PFAD).parent / "einstellungen.yaml")

# Was gilt, solange niemand etwas eingestellt hat. Eine fehlende Datei ist
# der Normalfall und kein Mangel: So sieht eine frische Installation aus.
#
#   updatepruefung   Tage zwischen zwei Blicken ins Repository.
#                    0 = nie, 7 = woechentlich, 30 = monatlich.
#
#   offline          Diese Maschine fragt ueberhaupt nicht nach draussen.
#                    Nicht dasselbe wie updatepruefung=0, und der
#                    Unterschied ist der Grund, warum es beide gibt:
#                    "nie" ist eine Gewohnheit des Bedieners ("ich sehe
#                    selbst nach"), offline eine Eigenschaft der Maschine
#                    ("hier ist kein Ausgang"). Die Suche ist heute die
#                    einzige Abfrage nach draussen, die dieses Produkt
#                    kennt -- der Schalter gilt aber fuer alles, was
#                    dazukommt, damit die Zusage nicht bei jeder neuen
#                    Funktion neu geprueft werden muss.
#
#                    DASS ER IN DER OBERFLAECHE STEHT und nicht in der
#                    Umgebungsdatei, ist die Abweichung von Boot. Dort
#                    trennen root und der Dienstnutzer zwei Rollen, und
#                    der Server bedient fremde Rechner im Netz; hier
#                    arbeitet ein Mensch auf seiner eigenen Maschine, auf
#                    der er ohnehin Administrator ist. Ein Schalter in
#                    einer Datei, die nur er aendern koennte, bewachte
#                    nichts -- er machte bloss Arbeit.
VORGABEN: dict = {
    "updatepruefung": 7,
    "offline": False,
}


def _lesen() -> dict:
    try:
        with DATEI.open(encoding="utf-8") as fh:
            roh = yaml.safe_load(fh) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return roh if isinstance(roh, dict) else {}


def alle() -> dict:
    """Alle Einstellungen, fehlende mit ihrer Vorgabe."""
    werte = dict(VORGABEN)
    werte.update({k: v for k, v in _lesen().items() if k in VORGABEN})
    return werte


def hole(name: str):
    """Eine Einstellung -- oder ihre Vorgabe."""
    return alle().get(name, VORGABEN.get(name))


def setze(name: str, wert) -> None:
    """Eine Einstellung schreiben. Unbekannte Namen werden abgewiesen.

    Abgewiesen und nicht durchgereicht: Ein Tippfehler im Namen wuerde
    sonst eine Zeile in die Datei schreiben, die nie jemand liest -- und
    der Schalter, den man gerade umgelegt hat, bliebe wirkungslos.
    """
    if name not in VORGABEN:
        raise ValueError("Unbekannte Einstellung: %r" % name)
    daten = _lesen()
    daten[name] = wert
    DATEI.parent.mkdir(parents=True, exist_ok=True)
    # Erst daneben, dann umbenennen: Ein abgebrochener Schreibvorgang
    # laesst sonst eine halbe YAML-Datei zurueck, und die liest sich beim
    # naechsten Start als "keine Einstellungen".
    vorlaeufig = DATEI.with_suffix(".yaml.neu")
    with vorlaeufig.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(daten, fh, allow_unicode=True, sort_keys=False)
    os.replace(vorlaeufig, DATEI)
