#!/usr/bin/env python3
"""
Haelt die geteilten Dateien gegen das Schwesterprodukt.

**Wozu.** `style.css`, das Logo und ein paar Vorlagen sollen in beiden
Produkten dieselben sein -- das ist die ganze Einheitlichkeit, auf die
es ankommt. Geteilt wird durch Abschreiben (docs/uebernahme.md in MARLEI
Tasks, Abschnitt 8), und Abschreiben laeuft auseinander. Dieses Skript ist dieselbe Bauart
wie Boots `pruefe-verweise.py`: Es setzt keine Regel durch, es haelt eine
Handregel ehrlich.

**Die Handregel bleibt die Verpflichtung:** Eine Aenderung an einer
geteilten Datei wird IN DERSELBEN SITZUNG in beide Repositories getragen.
Dieses Skript findet nur, was trotzdem durchrutscht.

**Es liegt in BEIDEN Repositories, und das ist der Punkt.** Ein
Pruefer, den es nur auf einer Seite gibt, meldet nur, was auf dieser
Seite auffaellt: Wer in Boot etwas an `style.css` aendert, bekommt dort
keine Meldung -- die Abweichung faellt erst auf, wenn jemand zufaellig
im anderen Produkt prueft. Deshalb fragt es nicht, wo es steht, sondern
wer sein Gegenueber ist.

**Damit doppelt es sich selbst, und genau das bewacht es mit:** Skript
und Liste stehen als `gleich` in der Liste. Wer eines von beiden nur auf
einer Seite aendert, wird beim naechsten Lauf gemeldet -- von dem Stueck,
das er geaendert hat.

**Es gehoert nach tools/ und nicht nach webui/**, weil geteilt beim
Entwickeln wird und nicht beim Betreiben: Auf einem Server gibt es kein
zweites Repository, und dort hat es nichts zu suchen.

    python tools/pruefe-gemeinsam.py
    python tools/pruefe-gemeinsam.py --gegen /pfad/zum/anderen/produkt

Rueckgabe 1, sobald eine als `gleich` gefuehrte Datei abweicht oder
fehlt. `angepasst` gemeldete Unterschiede sind erwartet und zaehlen
nicht als Fehler -- gezeigt wird nur ihr Umfang, damit auffaellt, wenn
eine Datei sich still davonmacht.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
LISTE = HIER / "tools" / "gemeinsam.txt"

# Wer wessen Gegenueber ist. Die Liste beschreibt EIN Paar. Kaeme ein
# drittes Produkt dazu, waere nicht diese Tabelle das Problem, sondern
# dass "gleich mit wem" dann keine Antwort mehr hat.
PARTNER = {
    "marlei-tasks": "marlei-boot",
    "marlei-boot": "marlei-tasks",
}


def partner_vorgabe():
    """Das Gegenueber liegt ueblicherweise neben diesem Projekt.

    Eine Vermutung und keine Voraussetzung -- --gegen sticht sie. Heisst
    der Ordner anders als das Produkt, findet die Tabelle nichts; dann
    sagt das Skript das und prueft nicht.
    """
    anderer = PARTNER.get(HIER.name)
    return HIER.parent / anderer if anderer else None


def eintraege(pfad: Path):
    """Die Liste lesen -- Sorte, Pfad, und was sonst niemanden angeht."""
    for nr, zeile in enumerate(pfad.read_text(encoding="utf-8").splitlines(), 1):
        blank = zeile.strip()
        if not blank or blank.startswith("#"):
            continue
        teile = blank.split("#", 1)[0].split()
        if len(teile) != 2 or teile[0] not in ("gleich", "angepasst"):
            print("  ! %s Zeile %d unverstaendlich: %s" % (pfad.name, nr, blank))
            continue
        yield teile[0], teile[1]


def inhalt(pfad: Path) -> bytes:
    """Der Inhalt, ohne die Zeilenenden zu zaehlen.

    **Warum das noetig ist und nicht Bequemlichkeit:** Beide Repositories
    legen Textdateien mit LF ab -- das erzwingt ihre `.gitattributes`. Die
    ARBEITSKOPIEN koennen trotzdem auseinandergehen: Boots Dateien tragen
    unter Windows CRLF, weil sie dort ausgecheckt wurden, bevor die Regel
    galt. Byteweise verglichen waere jede geteilte Datei "abweichend", und
    ein Pruefer, der immer Alarm schlaegt, wird nach dem dritten Mal
    ignoriert.

    Verglichen wird deshalb der Inhalt, nicht die Zeilenenden. **Bei
    Binaerdateien nicht:** Dort ist ein CR ein Byte wie jedes andere, und
    ein Favicon zu "normalisieren" waere Unsinn. Erkannt werden sie am
    Nullbyte -- dieselbe Faustregel, die Git benutzt.
    """
    roh = pfad.read_bytes()
    if b"\0" in roh:
        return roh
    return roh.replace(b"\r\n", b"\n")


def summe(pfad: Path) -> str:
    return hashlib.sha256(inhalt(pfad)).hexdigest()[:12]


def zeilen(pfad: Path) -> list[str]:
    return inhalt(pfad).decode("utf-8", errors="replace").splitlines()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gegen", type=Path, default=partner_vorgabe(),
                   help="Projektordner des anderen Produkts")
    p.add_argument("--zeigen", action="store_true",
                   help="bei Abweichung die Unterschiede ausgeben")
    args = p.parse_args()

    if args.gegen is None:
        print("Ordner %s steht in keiner Paarung." % HIER.name)
        print("Nichts zu vergleichen. Mit --gegen den anderen angeben.")
        return 0

    if not (args.gegen / "webui").is_dir():
        # Kein Fehler, sondern eine Lage: Auf einer fremden Maschine liegt
        # das andere Produkt nicht daneben. Lieber nichts sagen als etwas
        # Falsches.
        print("Das andere Produkt nicht gefunden unter %s" % args.gegen)
        print("Nichts zu vergleichen. Mit --gegen den Ordner angeben.")
        return 0

    hier_name, dort_name = HIER.name, args.gegen.name
    fehler = 0
    gleich = angepasst = 0

    for sorte, rel in eintraege(LISTE):
        hier, dort = HIER / rel, args.gegen / rel
        if not hier.exists():
            print("  FEHLT in %s  %s" % (hier_name, rel))
            fehler += 1
            continue
        if not dort.exists():
            print("  FEHLT in %s  %s" % (dort_name, rel))
            fehler += 1
            continue

        a, b = summe(hier), summe(dort)
        if sorte == "gleich":
            if a == b:
                print("  gleich    %s" % rel)
                gleich += 1
            else:
                print("  ABWEICHUNG %s  (%s %s, %s %s)"
                      % (rel, hier_name, a, dort_name, b))
                fehler += 1
                if args.zeigen:
                    for z in difflib.unified_diff(
                            zeilen(dort), zeilen(hier),
                            dort_name + "/" + rel,
                            hier_name + "/" + rel, lineterm=""):
                        print("      " + z)
        else:
            unterschied = sum(1 for z in difflib.unified_diff(
                zeilen(dort), zeilen(hier), lineterm="")
                if z.startswith(("+", "-")) and not z.startswith(("+++", "---")))
            gesamt = len(zeilen(hier))
            print("  angepasst %s  (%d von %d Zeilen abweichend)"
                  % (rel, unterschied, gesamt))
            angepasst += 1

    print()
    print("%d geteilt, %d angepasst, %d Abweichung(en)."
          % (gleich, angepasst, fehler))
    if fehler:
        print()
        print("Eine geteilte Datei ist auseinandergelaufen. Zusammenfuehren")
        print("und in BEIDE Repositories tragen -- nicht nur hier.")
        print("Mit --zeigen stehen die Unterschiede darunter.")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
