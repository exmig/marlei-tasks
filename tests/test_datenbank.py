"""
Prueft das Schema -- und zwar die Regeln, nicht das Anlegen.

Dass ``CREATE TABLE`` durchlaeuft, sagt nichts. Geprueft wird, ob die
Entscheidungen aus `docs/aufbau.md` und `docs/datenhaltung.md` in der Ablage
wirklich gelten: dass eine Kennung nie wiederverwendet wird, dass zwei
Projekte nicht denselben Namen tragen koennen, dass ein Status ohne Datum
abgewiesen wird.

    python tests/test_datenbank.py

Braucht nichts ausser der Standardbibliothek -- die Ablage ist SQLite.
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webui"))
import datenbank  # noqa: E402

FEHLER: list[str] = []


def pruefe(bedingung, was: str) -> None:
    if bedingung:
        print("  ok    %s" % was)
    else:
        print("  FEHLT %s" % was)
        FEHLER.append(was)


def wirft(fn, was: str) -> None:
    """Erwartet, dass die Ablage sich wehrt."""
    try:
        fn()
    except sqlite3.IntegrityError:
        print("  ok    %s" % was)
        return
    print("  FEHLT %s -- wurde angenommen" % was)
    FEHLER.append(was)


tmp = Path(tempfile.mkdtemp())
conn = datenbank.verbindung(tmp / "test.db")
suche = datenbank.anlegen(conn)

print("Ablage")
pruefe(conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal",
       "journal_mode ist WAL")
pruefe(conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1,
       "Fremdschluessel sind eingeschaltet")
pruefe(suche, "Volltextsuche (FTS5) steht zur Verfuegung")

print("\nKennungen")
# AUTOINCREMENT: eine geloeschte Hoechstnummer darf nie wiederkommen.
conn.execute("INSERT INTO projekte (name, eingetragen_am) "
             "VALUES ('Erstes', '07.09.2026')")
conn.execute("INSERT INTO projekte (name, eingetragen_am) "
             "VALUES ('Zweites', '07.09.2026')")
zweite = conn.execute("SELECT id FROM projekte WHERE name='Zweites'").fetchone()[0]
conn.execute("DELETE FROM projekte WHERE id=?", (zweite,))
conn.execute("INSERT INTO projekte (name, eingetragen_am) "
             "VALUES ('Drittes', '07.09.2026')")
dritte = conn.execute("SELECT id FROM projekte WHERE name='Drittes'").fetchone()[0]
pruefe(dritte > zweite,
       "eine geloeschte Kennung wird nicht wiederverwendet (P-%03d nach P-%03d)"
       % (dritte, zweite))
pruefe(datenbank.kennung("B", 65) == "B-065", "kennung() formatiert dreistellig")

# Jede Art zaehlt fuer sich: das erste Topic ist B-001, obwohl es schon
# drei Projekte gibt.
projekt = conn.execute("SELECT id FROM projekte WHERE name='Erstes'").fetchone()[0]
conn.execute("INSERT INTO bereiche (projekt_id, wert) VALUES (?, 'oberflaeche')",
             (projekt,))
bereich = conn.execute("SELECT id FROM bereiche").fetchone()[0]
conn.execute("""INSERT INTO topics (projekt_id, titel, bereich_id, eingetragen_am)
                VALUES (?, 'Erstes Topic', ?, '06.09.2026')""", (projekt, bereich))
pruefe(conn.execute("SELECT id FROM topics").fetchone()[0] == 1,
       "die Arten zaehlen getrennt -- das erste Topic ist B-001")

print("\nWas die Ablage abweisen muss")
wirft(lambda: conn.execute("INSERT INTO projekte (name, eingetragen_am) "
                          "VALUES ('Erstes', '07.09.2026')"),
      "zwei Projekte mit demselben Namen (das Losungswort braucht Eindeutigkeit)")
wirft(lambda: conn.execute("INSERT INTO projekte (name) VALUES ('Ohne Datum')"),
      "ein Projekt ohne Eintragsdatum")
wirft(lambda: conn.execute(
        "INSERT INTO projekte (name, zustand, eingetragen_am) "
        "VALUES ('X', 'schlummert', '07.09.2026')"),
      "ein erfundener Projektzustand")
wirft(lambda: conn.execute("""INSERT INTO topics
        (projekt_id, titel, bereich_id, eingetragen_am, kategorie)
        VALUES (?, 'X', ?, '06.09.2026', 'WUNSCH')""", (projekt, bereich)),
      "eine dritte Kategorie neben IDEE und FEHLER")
wirft(lambda: conn.execute("""INSERT INTO aufgaben
        (projekt_id, titel, bereich_id, eingetragen_am, status)
        VALUES (?, 'X', ?, '06.09.2026', 'AKTIV')""", (projekt, bereich)),
      "AKTIV ohne Datum (die Regel sagt: mit Datum ausser bei PASSIV)")
wirft(lambda: conn.execute("""INSERT INTO entscheidungen
        (projekt_id, titel, datum, bezug_art) VALUES (?, 'X', '06.09.2026', 'B')""",
        (projekt,)),
      "ein Bezug ohne Kennung")
wirft(lambda: conn.execute("""INSERT INTO topics
        (projekt_id, titel, bereich_id, eingetragen_am)
        VALUES (?, 'X', 999, '06.09.2026')""", (projekt,)),
      "ein Bereich, den es nicht gibt")

print("\nVorgaben")
zeile = conn.execute("SELECT prio, abschluss FROM topics WHERE id=1").fetchone()
pruefe(zeile["prio"] == datenbank.STRICH and zeile["abschluss"] == datenbank.STRICH,
       "Prio und Abschluss stehen auf dem Strich, nicht auf NULL")
pruefe(conn.execute("SELECT zustand FROM projekte WHERE id=?",
                    (projekt,)).fetchone()[0] == "AKTIV",
       "ein neues Projekt ist AKTIV")

if suche:
    print("\nBuendelprobe")
    conn.execute("""INSERT INTO topics
        (projekt_id, titel, bereich_id, eingetragen_am, beschreibung)
        VALUES (?, 'Upload bricht ab', ?, '06.09.2026',
                'Waehrend einer Uebertragung reden Browser und Server nicht')""",
        (projekt, bereich))
    conn.execute("""INSERT INTO topics
        (projekt_id, titel, bereich_id, eingetragen_am, beschreibung)
        VALUES (?, 'Laufenden Upload abbrechen', ?, '06.09.2026',
                'Eine Uebertragung soll sich beenden lassen')""",
        (projekt, bereich))
    treffer = conn.execute(
        "SELECT rowid FROM topics_suche WHERE topics_suche MATCH 'Uebertragung'"
    ).fetchall()
    pruefe(len(treffer) == 2,
           "die Suche findet beide Eintraege ueber die BESCHREIBUNG, "
           "nicht ueber den Titel")

print("\nEin Projekt loeschen")

# Ein zweites Projekt daneben, an dem sich zeigen muss, dass es
# unberuehrt bleibt.
conn.execute("INSERT INTO projekte (name, eingetragen_am) "
             "VALUES ('Nachbar', '07.09.2026')")
nachbar = conn.execute("SELECT id FROM projekte WHERE name='Nachbar'").fetchone()[0]
conn.execute("INSERT INTO bereiche (projekt_id, wert) VALUES (?, 'server')",
             (nachbar,))
nachbar_bereich = conn.execute(
    "SELECT id FROM bereiche WHERE projekt_id=?", (nachbar,)).fetchone()[0]
conn.execute("""INSERT INTO topics (projekt_id, titel, bereich_id, eingetragen_am)
                VALUES (?, 'Bleibt stehen', ?, '07.09.2026')""",
             (nachbar, nachbar_bereich))

# Das Projekt, das weg soll, bekommt von jeder Sorte etwas.
conn.execute("""INSERT INTO meilensteine (projekt_id, benennung, eingetragen_am)
                VALUES (?, 'Erster Stein', '07.09.2026')""", (projekt,))
stein = conn.execute("SELECT id FROM meilensteine").fetchone()[0]
conn.execute("""INSERT INTO aufgaben
    (projekt_id, titel, bereich_id, eingetragen_am, meilenstein_id)
    VALUES (?, 'Eine Arbeit', ?, '07.09.2026', ?)""", (projekt, bereich, stein))
aufgabe = conn.execute("SELECT id FROM aufgaben").fetchone()[0]
conn.execute("""INSERT INTO aufgabe_punkte (aufgabe_id, art, folge, text)
                VALUES (?, 'ABNAHME', 1, 'Laeuft durch')""", (aufgabe,))
conn.execute("INSERT INTO aufgabe_ursprung (aufgabe_id, topic_id) VALUES (?, 1)",
             (aufgabe,))
conn.execute("""INSERT INTO meilenstein_ursprung (meilenstein_id, aufgabe_id)
                VALUES (?, ?)""", (stein, aufgabe))
conn.execute("""INSERT INTO meilenstein_dazwischen
                (meilenstein_id, datum, text)
                VALUES (?, '07.09.2026', 'Ging nicht')""", (stein,))
conn.execute("""INSERT INTO entscheidungen (projekt_id, titel, datum)
                VALUES (?, 'Warum so', '07.09.2026')""", (projekt,))
conn.execute("INSERT INTO kenntnis (projekt_id, befund, seit) "
             "VALUES (?, 'platz-knapp', '07.09.2026')", (projekt,))
conn.commit()

# Der stille Weg muss versperrt sein: Von einem Projekt kaskadiert nichts.
wirft(lambda: conn.execute("DELETE FROM projekte WHERE id=?", (projekt,)),
      "ein DELETE FROM projekte scheitert laut, statt still alles mitzunehmen")
conn.rollback()

datenbank.projekt_loeschen(conn, projekt)

pruefe(conn.execute("SELECT COUNT(*) FROM projekte WHERE id=?",
                    (projekt,)).fetchone()[0] == 0,
       "das Projekt ist weg")

# Keine Waise -- in keiner Tabelle darf etwas zurueckbleiben.
waisen = []
for tabelle, spalte in (
        ("bereiche", "projekt_id"), ("topics", "projekt_id"),
        ("aufgaben", "projekt_id"), ("meilensteine", "projekt_id"),
        ("entscheidungen", "projekt_id"), ("kenntnis", "projekt_id")):
    n = conn.execute("SELECT COUNT(*) FROM %s WHERE %s = ?" % (tabelle, spalte),
                     (projekt,)).fetchone()[0]
    if n:
        waisen.append("%s (%d)" % (tabelle, n))
for tabelle in ("aufgabe_punkte", "aufgabe_ursprung", "meilenstein_ursprung",
                "meilenstein_vorgaenger", "meilenstein_dazwischen"):
    n = conn.execute("SELECT COUNT(*) FROM %s" % tabelle).fetchone()[0]
    if n:
        waisen.append("%s (%d)" % (tabelle, n))
pruefe(not waisen,
       "nichts bleibt zurueck" + (" -- gefunden: " + ", ".join(waisen)
                                  if waisen else ""))
pruefe(not conn.execute("PRAGMA foreign_key_check").fetchall(),
       "kein Verweis zeigt ins Leere (foreign_key_check)")

pruefe(conn.execute("SELECT COUNT(*) FROM topics WHERE projekt_id=?",
                    (nachbar,)).fetchone()[0] == 1,
       "das Nachbarprojekt ist unberuehrt")

# Und die Kennung des geloeschten Projekts kommt nicht wieder.
conn.execute("INSERT INTO projekte (name, eingetragen_am) "
             "VALUES ('Danach', '07.09.2026')")
pruefe(conn.execute("SELECT id FROM projekte WHERE name='Danach'").fetchone()[0]
       > projekt,
       "die Kennung des geloeschten Projekts wird nicht wiederverwendet")

conn.commit()
conn.close()

print("\nProjekte lesen und schreiben")

# Eine frische Ablage: Die Pruefungen oben haben geloescht und
# umgeraeumt, und hier soll gezaehlt werden.
conn2 = datenbank.verbindung(tmp / "projekte.db")
datenbank.anlegen(conn2)

eins = datenbank.projekt_anlegen(conn2, "MARLEI Boot", "2026-08-24",
                                 beschreibung="Ein Bootserver",
                                 vision="Netz rein, fertig")
zwei = datenbank.projekt_anlegen(conn2, "MARLEI Tasks", "2026-09-05")
datenbank.bereich_anlegen(conn2, eins, "systeme")
datenbank.bereich_anlegen(conn2, eins, "quellen")
# Zweimal derselbe Bereich: Wer ihn eintippt, wollte, dass er dasteht.
datenbank.bereich_anlegen(conn2, eins, "quellen")

alle = datenbank.projekte(conn2)
pruefe([p["kennung"] for p in alle] == ["P-001", "P-002"],
       "projekte() gibt die Kennungen als P-001, P-002")
pruefe([p["id"] for p in alle] == sorted(p["id"] for p in alle),
       "sortiert nach Kennung, nicht nach Name -- die Liste springt nicht "
       "beim Umbenennen")
pruefe(len(datenbank.bereiche(conn2, eins)) == 2,
       "derselbe Bereich zweimal eingetragen gibt einen")

print("\nDas Datum")
pruefe(datenbank.datum_zeigen("2026-09-07") == "07.09.2026",
       "ISO in der Ablage, deutsch in der Ansicht")
pruefe(datenbank.datum_zeigen(datenbank.STRICH) == datenbank.STRICH,
       "ein Strich bleibt ein Strich")
pruefe(datenbank.datum_zeigen("") == "",
       "leer bleibt leer, statt zu einer Ausnahme zu fuehren")
# Der eigentliche Grund fuer ISO: Die drei Proben sind Abfragen.
datenbank.projekt_anlegen(conn2, "Aelter", "2025-12-31")
folge = [z[0] for z in conn2.execute(
    "SELECT name FROM projekte ORDER BY eingetragen_am")]
pruefe(folge[0] == "Aelter",
       "nach Datum sortiert steht 2025 vorn -- mit 31.12.2025 als Text "
       "stuende es hinten")

print("\nDer Bestand")
b = datenbank.projekt(conn2, eins)["bestand"]
pruefe(b == {"sammlung": 0, "aufgaben": 0, "meilensteine": 0,
             "entscheidungen": 0},
       "ein frisches Projekt hat einen Bestand von viermal null")
bereich_id = datenbank.bereiche(conn2, eins)[0]["id"]
conn2.execute("""INSERT INTO topics (projekt_id, titel, bereich_id, eingetragen_am)
                 VALUES (?, 'Faellt auf', ?, '2026-09-07')""", (eins, bereich_id))
conn2.commit()
pruefe(datenbank.projekt(conn2, eins)["bestand"]["sammlung"] == 1,
       "ein Eintrag der Sammlung zaehlt im Bestand mit")
pruefe(datenbank.projekt(conn2, zwei)["bestand"]["sammlung"] == 0,
       "und nicht im Nachbarprojekt")

print("\nWas gesperrt ist")
haengt = datenbank.bereich_loeschen(conn2, bereich_id)
pruefe(haengt == 1,
       "ein Bereich mit einem Eintrag darauf laesst sich nicht entfernen "
       "(er sperrt, er mahnt nicht)")
pruefe(len(datenbank.bereiche(conn2, eins)) == 2, "und er steht noch da")
frei = [b for b in datenbank.bereiche(conn2, eins) if not b["benutzt"]][0]
pruefe(datenbank.bereich_loeschen(conn2, frei["id"]) == 0
       and len(datenbank.bereiche(conn2, eins)) == 1,
       "ein Bereich ohne Eintraege geht weg")

print("\nAendern")
datenbank.projekt_aendern(conn2, zwei, name="MARLEI Aufgaben",
                          zustand="RUHT")
p2 = datenbank.projekt(conn2, zwei)
pruefe(p2["name"] == "MARLEI Aufgaben" and p2["zustand"] == "RUHT",
       "projekt_aendern() setzt Name und Zustand")
datenbank.projekt_aendern(conn2, zwei, id=99, erfunden="x")
pruefe(datenbank.projekt(conn2, zwei)["id"] == zwei,
       "ein Feldname, der nicht in AENDERBAR steht, wird verworfen")
wirft(lambda: datenbank.projekt_aendern(conn2, zwei, name="MARLEI Boot"),
      "zwei Projekte mit demselben Namen -- auch beim Aendern")

conn2.commit()
conn2.close()

print("\nSammlung: eintragen und finden")

conn3 = datenbank.verbindung(tmp / "sammlung.db")
datenbank.anlegen(conn3)
pj = datenbank.projekt_anlegen(conn3, "Probelauf", "2026-08-01")
datenbank.bereich_anlegen(conn3, pj, "quellen")
datenbank.bereich_anlegen(conn3, pj, "server")
br = {b["wert"]: b["id"] for b in datenbank.bereiche(conn3, pj)}

eins = datenbank.topic_anlegen(
    conn3, pj, "Der Upload bricht bei grossen Dateien ab", br["quellen"],
    "2026-08-28", "FEHLER",
    beschreibung="Waehrend einer Uebertragung reden Browser und Server nicht",
    fehler_wann="Ab etwa 6 GB", fehler_woran="Die Karte bleibt auf lädt")
zwei = datenbank.topic_anlegen(
    conn3, pj, "Laufenden Upload abbrechen koennen", br["quellen"],
    "2026-08-26", "IDEE",
    beschreibung="Eine Uebertragung soll sich beenden lassen")
drei = datenbank.topic_anlegen(
    conn3, pj, "Kein Weg zurueck", br["server"], datenbank.heute())

alle = datenbank.topics(conn3, pj)
pruefe([t["kennung"] for t in alle] == ["B-003", "B-002", "B-001"],
       "die Sammlung steht mit dem Juengsten oben")

# Die Buendelprobe: gefunden wird ueber die BESCHREIBUNG, nicht den Titel.
treffer = datenbank.topics(conn3, pj, suche="Uebertragung")
pruefe(sorted(t["id"] for t in treffer) == sorted([eins, zwei]),
       "die Suche findet beide ueber die Beschreibung -- keiner der beiden "
       "Titel enthaelt das Wort")
pruefe(len(datenbank.topics(conn3, pj, suche="Uebertr")) == 2,
       "sie findet auch beim Tippen, nicht erst beim ganzen Wort")
pruefe(datenbank.topics(conn3, pj, suche="Nilpferd") == [],
       "und nichts, wo nichts ist")

print("\nWas an einem FEHLER fehlt")
t1 = datenbank.topic(conn3, eins)
pruefe(len(t1["fehlt"]) == 3,
       "drei der fuenf Angaben fehlen und werden benannt")
pruefe("Was man tun kann" in t1["fehlt"],
       "und zwar mit ihrer Aufschrift, nicht mit dem Spaltennamen")
pruefe(datenbank.topic(conn3, zwei)["fehlt"] == [],
       "eine IDEE hat keine fehlenden Fehlerangaben -- die fuenf gehoeren "
       "zum Fehler, nicht zum Eintrag")

print("\nLiegedauer")
pruefe(datenbank.topic(conn3, drei)["liegt_seit"] == 0,
       "was heute eingetragen wurde, liegt null Tage")
pruefe(datenbank.tage_seit("") is None and datenbank.tage_seit("—") is None,
       "ohne Datum ist die Liegedauer unbekannt und nicht null")

print("\nZusammenlegen")
datenbank.topic_aendern(conn3, eins, prio="MUSS")
datenbank.topic_aendern(conn3, zwei, prio="KANN")
aufgabe = datenbank.zusammenlegen(
    conn3, pj, [eins, zwei], "Uploads, die nicht durchlaufen",
    "Beide Beobachtungen haengen an derselben Uebertragung.",
    abnahme=["Ein 8-GB-Abbild laesst sich abbrechen"])
a = conn3.execute("SELECT * FROM aufgaben WHERE id = ?", (aufgabe,)).fetchone()
pruefe(a["titel"] == "Uploads, die nicht durchlaufen",
       "die Aufgabe traegt das gemeinsame Bild als Titel")
pruefe(a["prio"] == "MUSS",
       "sie erbt die STAERKSTE Prioritaet -- sonst verschwaende das "
       "Buendeln die Dringlichkeit")
pruefe(a["bereich_id"] == br["quellen"], "und den Bereich des ersten")
pruefe(a["dahinter"].startswith("Beide Beobachtungen"),
       "das gemeinsame Bild steht unter Was dahintersteckt")
herkunft = [z[0] for z in conn3.execute(
    "SELECT topic_id FROM aufgabe_ursprung WHERE aufgabe_id = ?", (aufgabe,))]
pruefe(sorted(herkunft) == sorted([eins, zwei]),
       "beide Eintraege stehen als Ursprung an der Aufgabe")
pruefe(all(datenbank.topic(conn3, i)["abschluss"] == "aufgabe"
           for i in (eins, zwei)),
       "und tragen den Abschluss aufgabe")
pruefe(all(datenbank.topic(conn3, i)["abschluss_am"] == datenbank.heute()
           for i in (eins, zwei)),
       "mit dem Datum -- ohne das kann das Quittungsbuch keine Zeile "
       "schreiben")
pruefe([t["id"] for t in datenbank.topics(conn3, pj)] == [drei],
       "abgeschlossen heisst weg von hier: In der Sammlung steht nur "
       "noch der dritte")

print("\nWas beim Zusammenlegen abgewiesen wird")
try:
    datenbank.zusammenlegen(conn3, pj, [], "Nichts", "", abnahme=["x"])
    pruefe(False, "ohne Eintraege wird nicht zusammengelegt")
except ValueError:
    pruefe(True, "ohne Eintraege wird nicht zusammengelegt")

# DIE SPERRE GILT AUCH HIER -- der Knopf fragt nach zweierlei.
try:
    datenbank.zusammenlegen(conn3, pj, [drei], "Ohne Abnahme", "",
                            abnahme=[])
    pruefe(False, "ohne Abnahme wird auch beim Buendeln nicht angelegt")
except ValueError:
    pruefe(True, "ohne Abnahme wird auch beim Buendeln nicht angelegt")
pruefe(datenbank.topic(conn3, drei)["abschluss"] == datenbank.STRICH,
       "und der Eintrag bleibt, wo er ist")

fremd = datenbank.projekt_anlegen(conn3, "Nachbar", "2026-08-01")
try:
    datenbank.zusammenlegen(conn3, fremd, [drei], "Geklaut", "",
                            abnahme=["x"])
    pruefe(False, "ein Eintrag aus einem anderen Projekt wird abgewiesen")
except ValueError:
    pruefe(True, "ein Eintrag aus einem anderen Projekt wird abgewiesen")

print("\nVerwerfen und die Zahlen")
zahlen = datenbank.sammlung_zahlen(conn3, pj)
pruefe(zahlen["ohne_prio"] == 1 and zahlen["luecken"] == 0,
       "die Zahlen zaehlen nur, was offen ist")
pruefe(zahlen["durchsicht_her"] is None,
       "ohne Durchsicht ist die Zahl unbekannt und nicht null")
datenbank.durchsicht_vermerken(conn3, pj)
pruefe(datenbank.sammlung_zahlen(conn3, pj)["durchsicht_her"] == 0,
       "vermerkt wird das Hinsehen, auch wenn nichts geaendert wurde")

datenbank.topic_abschliessen(conn3, drei, "verworfen")
pruefe(datenbank.topics(conn3, pj) == [],
       "ein verworfener Eintrag steht nicht mehr in der Sammlung")
pruefe(datenbank.topic(conn3, drei)["abschluss_am"] == datenbank.heute(),
       "aber mit Datum im Archiv -- das ist die Zeile im Quittungsbuch")

conn3.commit()
conn3.close()

print("\nAufgaben: die eine Sperre")

conn4 = datenbank.verbindung(tmp / "aufgaben.db")
datenbank.anlegen(conn4)
pa = datenbank.projekt_anlegen(conn4, "Arbeitsprojekt", "2026-08-01")
datenbank.bereich_anlegen(conn4, pa, "quellen")
ba = datenbank.bereiche(conn4, pa)[0]["id"]

try:
    datenbank.aufgabe_anlegen(conn4, pa, "Ohne Abnahme", ba, "2026-09-01",
                              abnahme=[])
    pruefe(False, "ohne Abnahme wird nicht angelegt")
except ValueError as warum:
    pruefe("Sammlung" in str(warum),
           "ohne Abnahme wird nicht angelegt -- und der Grund nennt den "
           "Ausgang, nicht nur das Verbot")

# Und "Was dahintersteckt" sperrt NICHT -- das ist die Gegenprobe.
eine = datenbank.aufgabe_anlegen(
    conn4, pa, "Uploads, die nicht durchlaufen", ba, "2026-09-05",
    abnahme=["Ein 8-GB-Abbild bricht ab", "Der Reiterwechsel bricht nicht ab"],
    arbeit=["Abbruchknopf bauen", "Hilfe nachziehen"], prio="MUSS")
a = datenbank.aufgabe(conn4, eine)
pruefe(a["kennung"] == "A-001" and not a["dahinter"],
       "ohne Ursache wird sehr wohl angelegt -- sie kann man nachtragen, "
       "die Abnahme nicht")
pruefe(len(a["abnahme"]) == 2 and len(a["arbeit"]) == 2,
       "beide Listen stehen getrennt an der Aufgabe")
pruefe(a["status"] == "PASSIV" and a["status_seit"] == datenbank.STRICH,
       "eine neue Aufgabe ist PASSIV und hat kein Seit")

print("\nZeilen werden Punkte")
pruefe(datenbank.zeilen("eins\n\n  zwei  \n") == ["eins", "zwei"],
       "eine Zeile ein Punkt, Leerzeilen fallen weg")
pruefe(datenbank.zeilen("") == [], "und ein leeres Feld gibt keine Punkte")

print("\nErledigt haengt an der Abnahme, nicht an der Arbeit")
for p in datenbank.aufgabe(conn4, eine)["arbeit"]:
    datenbank.punkt_haken(conn4, p["id"], True)
a = datenbank.aufgabe(conn4, eine)
pruefe(a["arbeit_fertig"] == 2 and not a["abnehmbar"],
       "die Arbeitsliste ist durch, abnehmbar ist die Aufgabe trotzdem "
       "nicht -- die eine misst den Fortschritt, die andere die Fertigkeit")
datenbank.punkt_haken(conn4, a["abnahme"][0]["id"], True)
pruefe(not datenbank.aufgabe(conn4, eine)["abnehmbar"],
       "ein Haken von zweien reicht nicht")
datenbank.punkt_haken(conn4, a["abnahme"][1]["id"], True)
pruefe(datenbank.aufgabe(conn4, eine)["abnehmbar"],
       "erst wenn alle stehen, ist sie abnehmbar")
datenbank.punkt_haken(conn4, a["abnahme"][1]["id"], False)
pruefe(not datenbank.aufgabe(conn4, eine)["abnehmbar"]
       and datenbank.aufgabe(conn4, eine)["abnahme"][1]["erledigt_am"]
           == datenbank.STRICH,
       "ein Haken laesst sich wieder wegnehmen, und das Datum geht mit")

print("\nStatus und Datum haengen zusammen")
datenbank.aufgabe_aendern(conn4, eine, status="AKTIV", status_seit="2026-09-06")
pruefe(datenbank.aufgabe(conn4, eine)["status_seit"] == "2026-09-06",
       "AKTIV traegt ein Datum")
datenbank.aufgabe_aendern(conn4, eine, status="PASSIV")
pruefe(datenbank.aufgabe(conn4, eine)["status_seit"] == datenbank.STRICH,
       "zurueck auf PASSIV nimmt das Datum mit -- ein stehengebliebenes "
       "waere eine Behauptung")
wirft(lambda: conn4.execute(
        "UPDATE aufgaben SET status='AKTIV', status_seit='—' WHERE id=?",
        (eine,)),
      "AKTIV ohne Datum weist schon die Ablage ab")
conn4.rollback()

print("\nDer Ursprung ist ein Verweis, keine Kopie")
t_eins = datenbank.topic_anlegen(conn4, pa, "Der Upload bricht ab", ba,
                                 "2026-08-28")
t_zwei = datenbank.topic_anlegen(conn4, pa, "Abbrechen koennen", ba,
                                 "2026-08-26")
zwei = datenbank.zusammenlegen(
    conn4, pa, [t_eins, t_zwei], "Uploads", "Dieselbe Uebertragung.",
    abnahme=["Bricht ab"])
a2 = datenbank.aufgabe(conn4, zwei)
pruefe([u["kennung"] for u in a2["ursprung"]] == ["B-001", "B-002"],
       "beide Eintraege stehen als Ursprung an der Aufgabe")
pruefe(a2["ursprung"][0]["titel"] == "Der Upload bricht ab",
       "und ihr Titel wird geholt, nicht mitgespeichert")
datenbank.topic_aendern(conn4, t_eins, titel="Ganz anders benannt")
pruefe(datenbank.aufgabe(conn4, zwei)["ursprung"][0]["titel"]
       == "Ganz anders benannt",
       "wer den Eintrag umbenennt, benennt den Verweis mit -- es gibt "
       "keine zweite Fassung, die veralten koennte")

print("\nAbschliessen")
datenbank.aufgabe_abschliessen(conn4, zwei, "erledigt")
pruefe([x["id"] for x in datenbank.aufgaben(conn4, pa)] == [eine],
       "eine erledigte Aufgabe steht nicht mehr in der Liste")
pruefe(datenbank.aufgabe(conn4, zwei)["abschluss_am"] == datenbank.heute(),
       "aber mit Datum im Archiv")

print("\nSortiert nach dem, woran jemand sitzt")
drei = datenbank.aufgabe_anlegen(conn4, pa, "Spaeter", ba, "2026-09-07",
                                 abnahme=["irgendwas"])
datenbank.aufgabe_aendern(conn4, eine, status="AKTIV",
                          status_seit="2026-09-06")
pruefe([x["id"] for x in datenbank.aufgaben(conn4, pa)] == [eine, drei],
       "AKTIV steht oben, auch wenn es die aeltere Kennung ist")

conn4.commit()
conn4.close()

print("\nMeilensteine: leer entstehen, nicht leer bleiben")

conn5 = datenbank.verbindung(tmp / "steine.db")
datenbank.anlegen(conn5)
pm = datenbank.projekt_anlegen(conn5, "Steinprojekt", "2026-08-01")
datenbank.bereich_anlegen(conn5, pm, "server")
bm = datenbank.bereiche(conn5, pm)[0]["id"]

leer = datenbank.meilenstein_anlegen(conn5, pm, "Aus dem Gespraech",
                                     "2026-09-07", "KANN")
m = datenbank.meilenstein(conn5, leer)
pruefe(m["kennung"] == "M-001" and m["ohne_aufgabe"],
       "ein Meilenstein ohne Aufgabe wird angelegt -- und als solcher "
       "benannt: kein Sperren, ein Befund")
pruefe(not m["abnehmbar"],
       "abnehmbar ist er trotzdem nicht -- da waere nichts abzunehmen")

print("\nVorgaenger sind eingetragen, Nachfolger abgelesen")
zweiter = datenbank.meilenstein_anlegen(conn5, pm, "Linux Plattform",
                                        "2026-08-29", "SOLL")
datenbank.vorgaenger_setzen(conn5, leer, [zweiter])
pruefe([v["kennung"] for v in datenbank.meilenstein(conn5, leer)["vorgaenger"]]
       == ["M-002"], "der Vorgaenger steht am Stein")
pruefe([n["kennung"] for n in
        datenbank.meilenstein(conn5, zweiter)["nachfolger"]] == ["M-001"],
       "und der Nachfolger faellt am anderen ab, ohne eingetragen zu sein")
datenbank.meilenstein_aendern(conn5, zweiter, benennung="Linux, umbenannt")
pruefe(datenbank.meilenstein(conn5, leer)["vorgaenger"][0]["benennung"]
       == "Linux, umbenannt",
       "wer umbenennt, benennt den Verweis mit -- es gibt keine zweite "
       "Fassung")

print("\nEin Kreis wird abgewiesen")
try:
    datenbank.vorgaenger_setzen(conn5, zweiter, [leer])
    pruefe(False, "A haengt von B und B von A wird abgewiesen")
except ValueError as warum:
    pruefe("Kreis" in str(warum),
           "A haengt von B und B von A wird abgewiesen -- die Ablage "
           "verbietet nur den direkten Fall")
try:
    datenbank.vorgaenger_setzen(conn5, leer, [leer])
    pruefe(False, "und von sich selbst haengt keiner ab")
except ValueError:
    pruefe(True, "und von sich selbst haengt keiner ab")

dritter = datenbank.meilenstein_anlegen(conn5, pm, "Dritter", "2026-09-01")
datenbank.vorgaenger_setzen(conn5, dritter, [leer])
try:
    datenbank.vorgaenger_setzen(conn5, zweiter, [dritter])
    pruefe(False, "auch ein Kreis ueber drei Ecken wird abgewiesen")
except ValueError:
    pruefe(True, "auch ein Kreis ueber drei Ecken wird abgewiesen")

print("\nAufgaben zuschlagen und loesen")
a_eins = datenbank.aufgabe_anlegen(conn5, pm, "Erste Arbeit", bm, "2026-09-01",
                                   abnahme=["laeuft durch"])
a_zwei = datenbank.aufgabe_anlegen(conn5, pm, "Zweite Arbeit", bm, "2026-09-02",
                                   abnahme=["laeuft auch durch"])
datenbank.aufgabe_zuschlagen(conn5, a_eins, zweiter)
datenbank.aufgabe_zuschlagen(conn5, a_zwei, zweiter)
m = datenbank.meilenstein(conn5, zweiter)
pruefe(len(m["aufgaben"]) == 2 and not m["ohne_aufgabe"],
       "zwei Aufgaben haengen daran, der Befund ist weg")
pruefe(not m["abnehmbar"], "abnehmbar ist er nicht, solange eine offen ist")

datenbank.aufgabe_abschliessen(conn5, a_eins, "erledigt")
pruefe(not datenbank.meilenstein(conn5, zweiter)["abnehmbar"],
       "eine von zweien reicht nicht")
datenbank.aufgabe_abschliessen(conn5, a_zwei, "erledigt")
m = datenbank.meilenstein(conn5, zweiter)
pruefe(m["abnehmbar"] and m["aufgaben_fertig"] == 2,
       "erst wenn alle erledigt sind, ist er abnehmbar")
pruefe(len(m["aufgaben"]) == 2,
       "und die erledigten bleiben in der Liste stehen -- sonst saehe "
       "man nicht mehr, woraus der Stein bestand")

print("\nWas dazwischenkam")
datenbank.dazwischen_anlegen(conn5, zweiter, "2026-09-01",
                             "Der Pi war nicht da.")
datenbank.dazwischen_anlegen(conn5, zweiter, "2026-09-04",
                             "M-007 wurde davorgezogen.")
m = datenbank.meilenstein(conn5, zweiter)
pruefe([d["datum"] for d in m["dazwischen"]] == ["2026-09-01", "2026-09-04"],
       "die Umwege stehen nach Datum, nicht nach Eintragsreihenfolge")
pruefe(m["dazwischen"][0]["datum_deutsch"] == "01.09.2026",
       "und deutsch in der Ansicht")
datenbank.dazwischen_loeschen(conn5, m["dazwischen"][0]["id"])
pruefe(len(datenbank.meilenstein(conn5, zweiter)["dazwischen"]) == 1,
       "eine Zeile laesst sich wegnehmen")

print("\nDie Abnahme")
datenbank.meilenstein_abnehmen(conn5, zweiter)
m = datenbank.meilenstein(conn5, zweiter)
pruefe(m["abschluss"] == "erledigt" and m["abnahme_am"] == datenbank.heute(),
       "abgenommen setzt Abschluss und Datum in einem Zug -- vier "
       "Handgriffe, die sich einzeln vergessen lassen, sind einer")
pruefe([x["id"] for x in datenbank.meilensteine(conn5, pm)]
       == [leer, dritter],
       "und er verschwindet aus der Liste der offenen (Regel 7, "
       "umgedreht)")
pruefe(len(datenbank.meilensteine(conn5, pm, offen_nur=False)) == 3,
       "aus der Ablage aber nicht -- in einer Datenbank verschwindet "
       "nichts")

print("\nVerworfen -- und die Arbeit bleibt")
a_drei = datenbank.aufgabe_anlegen(conn5, pm, "Dritte Arbeit", bm,
                                   "2026-09-03", abnahme=["irgendwas"])
datenbank.aufgabe_zuschlagen(conn5, a_drei, dritter)
datenbank.meilenstein_verwerfen(conn5, dritter)
pruefe(datenbank.meilenstein(conn5, dritter)["abschluss"] == "verworfen",
       "der Stein ist verworfen")
pruefe(datenbank.aufgabe(conn5, a_drei)["meilenstein_id"] is None
       and datenbank.aufgabe(conn5, a_drei)["abschluss"] == datenbank.STRICH,
       "die Aufgabe darunter bleibt und steht wieder ohne Stein da -- "
       "verworfen ist der Termin, nicht die Arbeit")

conn5.commit()
conn5.close()

print("\nEntscheidungen: Ergebnis und Weg sind zweierlei")

conn6 = datenbank.verbindung(tmp / "abwaegungen.db")
datenbank.anlegen(conn6)
pe = datenbank.projekt_anlegen(conn6, "Abwaegungsprojekt", "2026-08-01")
datenbank.bereich_anlegen(conn6, pe, "server")
be = datenbank.bereiche(conn6, pe)[0]["id"]

frei = datenbank.entscheidung_anlegen(
    conn6, pe, "Eine Karte zur Kenntnis nehmen", "2026-09-02", "ENTSCHLUSS",
    entschluss="Gelb und Blau falten sich zusammen, Rot bleibt stehen.",
    text="Zeile eins\n## Ein Abschnitt\nZeile drei")
e = datenbank.entscheidung(conn6, frei)
pruefe(e["kennung"] == "E-001" and e["bezug"] is None,
       "eine freistehende Entscheidung wird angelegt -- zwei Drittel "
       "haengen an nichts")
pruefe(not e["ohne_satz"] and not e["liegt"],
       "mit Satz und ohne Bezug meldet sie nichts")
pruefe(e["zeilen"] == 3 and e["abschnitte"] == 1,
       "der Umfang wird gezaehlt: Zeilen und Abschnitte")

print("\nEin Entschluss ohne Satz ist keiner -- und das mahnt")
stumm = datenbank.entscheidung_anlegen(
    conn6, pe, "Ohne Satz", "2026-09-03", "ENTSCHLUSS")
pruefe(datenbank.entscheidung(conn6, stumm)["ohne_satz"],
       "ENTSCHLUSS ohne Satz wird angelegt und benannt -- gesperrt wird "
       "nichts, den Satz kann man nachtragen")
offen = datenbank.entscheidung_anlegen(
    conn6, pe, "Den Produktnamen festlegen", "2026-08-29", "OFFEN")
pruefe(not datenbank.entscheidung(conn6, offen)["ohne_satz"],
       "OFFEN ohne Satz ist dagegen kein Befund -- der Entschluss steht "
       "ja aus")

print("\nZeigen statt kopieren: der Kopf des bezogenen Eintrags")
t_id = datenbank.topic_anlegen(conn6, pe, "Der Upload bricht ab", be,
                               "2026-08-28")
datenbank.entscheidung_aendern(conn6, offen, bezug=("B", t_id))
e = datenbank.entscheidung(conn6, offen)
pruefe(e["bezug"]["kennung"] == "B-001"
       and e["bezug"]["titel"] == "Der Upload bricht ab",
       "der Titel des bezogenen Eintrags wird geholt, nicht gespeichert")
pruefe(e["bezug"]["reiter"] == "Sammlung" and e["bezug"]["offen"],
       "samt Register und Stand")
datenbank.topic_aendern(conn6, t_id, titel="Anders benannt")
pruefe(datenbank.entscheidung(conn6, offen)["bezug"]["titel"]
       == "Anders benannt",
       "wer den Eintrag umbenennt, benennt den Verweis mit")

print("\nDie Liegeprobe")
pruefe(not datenbank.entscheidung(conn6, offen)["liegt"],
       "OFFEN mit offenem Eintrag liegt nicht -- hier haelt der "
       "Entschluss auf, nicht die Arbeit")
datenbank.entscheidung_aendern(conn6, offen, zustand="ENTSCHLUSS",
                               entschluss="MARLEI.")
pruefe(datenbank.entscheidung(conn6, offen)["liegt"],
       "ENTSCHLUSS mit offenem Eintrag LIEGT -- das ist die Liegeprobe")
datenbank.topic_abschliessen(conn6, t_id, "aufgabe")
pruefe(not datenbank.entscheidung(conn6, offen)["liegt"],
       "und sobald der Eintrag abgeschlossen ist, liegt nichts mehr")
pruefe(datenbank.entscheidung(conn6, offen)["bezug"]["abschluss"] == "aufgabe",
       "die Entscheidung bleibt trotzdem stehen und zeigt weiter darauf "
       "-- sie ueberlebt das, wozu sie gehoert")

zahlen = datenbank.entscheidungs_zahlen(conn6, pe)
pruefe(zahlen == {"gesamt": 3, "liegt": 0, "offen": 0,
                  "aelteste_offene": None, "ohne_satz": 1},
       "die Zahlen der Liegeprobe stimmen")

print("\nWas abgewiesen wird")
try:
    datenbank.entscheidung_anlegen(conn6, pe, "Krumm", "2026-09-07",
                                   zustand="VIELLEICHT")
    pruefe(False, "ein erfundener Zustand wird abgewiesen")
except ValueError:
    pruefe(True, "ein erfundener Zustand wird abgewiesen")
try:
    datenbank.entscheidung_anlegen(conn6, pe, "Halb", "2026-09-07",
                                   bezug_art="B", bezug_id=None)
    pruefe(False, "Bezugsart ohne Kennung wird abgewiesen")
except ValueError:
    pruefe(True, "Bezugsart ohne Kennung wird abgewiesen")
wirft(lambda: conn6.execute(
        "INSERT INTO entscheidungen (projekt_id, titel, datum, bezug_art) "
        "VALUES (?, 'X', '2026-09-07', 'B')", (pe,)),
      "und die Ablage weist es ebenfalls ab, nicht nur die Funktion")
conn6.rollback()

print("\nSuchen und loeschen")
pruefe(len(datenbank.entscheidungen(conn6, pe, suche="MARLEI")) == 1,
       "die Suche geht ueber den Entschluss, nicht nur den Titel")
pruefe(len(datenbank.entscheidungen(conn6, pe, suche="Abschnitt")) == 1,
       "und ueber den Verlauf")
pruefe(len(datenbank.entscheidungen(conn6, pe, offen_nur=True)) == 0,
       "der Filter zeigt nur die offenen")
datenbank.entscheidung_loeschen(conn6, stumm)
pruefe(len(datenbank.entscheidungen(conn6, pe)) == 2,
       "geloescht wird wirklich -- es gibt kein Archiv fuer "
       "Entscheidungen")

conn6.commit()
conn6.close()

print("\nHistory: alles faellt ab, nichts wird eingetragen")

conn7 = datenbank.verbindung(tmp / "history.db")
datenbank.anlegen(conn7)
ph = datenbank.projekt_anlegen(conn7, "Rueckschau", "2026-08-01")
datenbank.bereich_anlegen(conn7, ph, "server")
bh = datenbank.bereiche(conn7, ph)[0]["id"]

# Ein Topic, das eine Aufgabe wurde -- und eines, das verworfen wurde.
t_um = datenbank.topic_anlegen(conn7, ph, "Zieht um", bh, "2026-08-20")
t_weg = datenbank.topic_anlegen(conn7, ph, "Faellt weg", bh, "2026-08-21")
datenbank.topic_abschliessen(conn7, t_weg, "verworfen", "2026-08-28")

a_fertig = datenbank.zusammenlegen(
    conn7, ph, [t_um], "Der Rueckweg", "Dieselbe Ursache.",
    abnahme=["laeuft durch"])
datenbank.aufgabe_abschliessen(conn7, a_fertig, "erledigt", "2026-09-02")
conn7.execute("UPDATE aufgaben SET eingetragen_am = '2026-08-25' WHERE id = ?",
              (a_fertig,))

stein = datenbank.meilenstein_anlegen(conn7, ph, "Linux Plattform",
                                      "2026-08-29", "SOLL")
datenbank.aufgabe_zuschlagen(conn7, a_fertig, stein)
datenbank.dazwischen_anlegen(conn7, stein, "2026-09-01", "Der Pi war nicht da.")
datenbank.meilenstein_abnehmen(conn7, stein, "2026-09-05")
conn7.commit()

print("\nDie Strasse")
weg = datenbank.strasse(conn7, ph)
pruefe(len(weg) == 1 and weg[0]["kennung"] == "M-001",
       "auf der Strasse steht, was abgenommen ist")
pruefe(weg[0]["dauer"] == 7,
       "die Dauer faellt aus den zwei Daten ab (29.08. -> 05.09.)")
pruefe(len(weg[0]["dazwischen"]) == 1,
       "und die Umwege aus dem, was notiert wurde, als es passierte")

print("\nEnde oder Umzug -- was frueher das Quittungsbuch trennte")
# Seit dem 22.09.2026 (E-027) gibt es keine zweite Ansicht mehr, sondern
# einen Filter. Die Zusage dahinter ist dieselbe geblieben, und sie ist
# der Grund fuer diesen Block: Wer Enden und Umzuege zusammenzaehlt,
# zaehlt dieselbe Arbeit zweimal.
buch = datenbank.archiv(conn7, ph, schluss="ende")
kennungen = [q["kennung"] for q in buch]
pruefe("B-002" in kennungen,
       "ein VERWORFENER Eintrag der Sammlung zaehlt als Ende")
pruefe("B-001" not in kennungen,
       "einer, aus dem eine Aufgabe wurde, NICHT -- es ist nicht fertig, "
       "es zieht um")
pruefe("B-001" in [u["kennung"] for u in
                   datenbank.archiv(conn7, ph, schluss="umzug")],
       "er steht dafuer unter den Umzuegen -- verschwunden ist er nicht")
pruefe("A-001" in kennungen and "M-001" in kennungen,
       "die erledigte Aufgabe und der abgenommene Stein zaehlen als Ende")
pruefe(buch[0]["fertig_am"] >= buch[-1]["fertig_am"],
       "sortiert nach dem Abschlussdatum, das Juengste oben")
zeile = [q for q in buch if q["kennung"] == "A-001"][0]
pruefe(zeile["dauer"] == 8 and zeile["register"] == "Aufgaben",
       "mit Dauer und Register in derselben Zeile")
pruefe(len(buch) + len(datenbank.archiv(conn7, ph, schluss="umzug"))
       == len(datenbank.archiv(conn7, ph)),
       "und jeder Eintrag ist genau eines von beiden")

print("\nEin verworfener Stein bekommt ein Datum, aber keine Abnahme")
zweiter = datenbank.meilenstein_anlegen(conn7, ph, "Faellt aus", "2026-08-30")
datenbank.meilenstein_verwerfen(conn7, zweiter, "2026-09-06")
m = datenbank.meilenstein(conn7, zweiter)
pruefe(m["abnahme_am"] == datenbank.STRICH and m["abschluss_am"] == "2026-09-06",
       "abnahme_am bleibt leer -- er wurde nicht abgenommen, er faellt weg")
pruefe(any(q["kennung"] == "M-002"
           for q in datenbank.archiv(conn7, ph, schluss="ende")),
       "trotzdem zaehlt er als Ende: verworfen ist ein Ende")
pruefe(not any(s["kennung"] == "M-002" for s in datenbank.strasse(conn7, ph)),
       "auf der Strasse steht er nicht -- dort stehen nur die "
       "abgenommenen")

print("\nDas Archiv")
alles = datenbank.archiv(conn7, ph)
pruefe(sorted(e["kennung"] for e in alles)
       == ["A-001", "B-001", "B-002", "M-001", "M-002"],
       "im Archiv steht alles Abgeschlossene -- auch das, was umgezogen "
       "ist, und der verworfene Stein")
pruefe(any(e["kennung"] == "B-001" for e in alles),
       "der Eintrag mit Abschluss aufgabe steht hier sehr wohl: Das "
       "Archiv fragt nicht, ob es fertig wurde, sondern was drinstand")
pruefe([e["art"] for e in datenbank.archiv(conn7, ph, art="M")] == ["M", "M"],
       "der Filter zeigt nur ein Register")
pruefe(len(datenbank.archiv(conn7, ph, suche="Rueckweg")) == 1,
       "und die Suche greift ueber den Titel")
eintrag = [e for e in alles if e["kennung"] == "A-001"][0]
pruefe(eintrag["satz"]["abnahme"] and eintrag["register"] == "Aufgaben",
       "ein Archiveintrag traegt den ganzen Satz mit, nicht nur den Kopf")

zahlen = datenbank.history_zahlen(conn7, ph)
pruefe(zahlen["steine"] == 1 and zahlen["umwege"] == 1
       and zahlen["archiv_je_art"]["M"] == 2,
       "die Zahlen in den Kartenkoepfen stimmen")

conn7.commit()
conn7.close()

print("\nDer Export")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webui"))
import export  # noqa: E402

conn8 = datenbank.verbindung(tmp / "ausgang.db")
datenbank.anlegen(conn8)
px = datenbank.projekt_anlegen(conn8, "MARLEI Boot", "2026-08-24",
                               beschreibung="Ein Bootserver.",
                               vision="Netz rein, fertig.")
datenbank.bereich_anlegen(conn8, px, "server")
bx = datenbank.bereiche(conn8, px)[0]["id"]
datenbank.topic_anlegen(conn8, px, "Kein Weg zurueck", bx, "2026-09-06",
                        beschreibung="Es fehlt ein uninstall.sh.")
ax = datenbank.aufgabe_anlegen(conn8, px, "Der Rueckweg", bx, "2026-09-06",
                               abnahme=["laeuft durch"],
                               arbeit=["Dienste abschalten"],
                               dahinter="Die Ursache dahinter.")
mx = datenbank.meilenstein_anlegen(conn8, px, "Linux Plattform", "2026-08-29")
datenbank.aufgabe_zuschlagen(conn8, ax, mx)
datenbank.dazwischen_anlegen(conn8, mx, "2026-09-01", "Der Pi war nicht da.")
datenbank.entscheidung_anlegen(conn8, px, "Die Firewall wird gemeldet",
                               "2026-09-05", "ENTSCHLUSS",
                               entschluss="Gemeldet, nicht angefasst.",
                               text="## Der Zwiespalt\nZwei Wege.")
conn8.commit()
pjx = datenbank.projekt(conn8, px)

pruefe(export.verzeichnisname(pjx) == "P-001-marlei-boot",
       "der Ordner heisst nach Kennung und Name -- die Kennung vorn, "
       "weil sie sich nie aendert")
umbenannt = dict(pjx, name="Völlig anders benannt")
pruefe(export.verzeichnisname(umbenannt).startswith("P-001-"),
       "und bleibt beim Umbenennen erkennbar")
pruefe("ö" not in export.verzeichnisname(umbenannt)
       and export.verzeichnisname(umbenannt).endswith("voellig-anders-benannt"),
       "Umlaute werden umschrieben, Grossbuchstaben klein -- nur die\n       Kennung bleibt, wie sie ist")

dateien = export.dateien(conn8, pjx)
pruefe(sorted(dateien) == sorted(export.DATEIEN),
       "es sind genau die fuenf Dateien")
pruefe(all(t.endswith(chr(10)) and not t.endswith(chr(10) * 2)
           for t in dateien.values()),
       "jede endet mit genau einem Zeilenumbruch")

# DIE STABILITAETSZUSAGE, und sie ist der Grund fuer diese Pruefung:
# Bei unveraendertem Bestand byteweise dieselbe Ausgabe.
pruefe(export.dateien(conn8, pjx) == dateien,
       "zweimal aufgerufen liefert zweimal dieselben Zeichen -- ohne das "
       "erzeugte jeder Lauf einen Unterschied ueber alles")

# DIE AUSGABE IST LF, auch wenn in der Ablage CRLF steht: Ein
# Browser schickt in einem Formularfeld CRLF, und gemischte
# Umbrueche in einer Datei brechen die Stabilitaetszusage beim
# ersten Auschecken -- Git schriebe sie um, und der naechste
# Export saehe in jeder Zeile geaendert aus.
datenbank.topic_aendern(conn8, 1,
                        beschreibung='Erste' + chr(13) + chr(10)
                        + 'Zweite')
conn8.commit()
pruefe(chr(13) not in export.dateien(conn8, pjx)['sammlung.md'],
       'die Ausgabe traegt nur LF, auch wenn im Feld CRLF steht')

print("\nWas in den Dateien steht")
pruefe("# P-001 MARLEI Boot" in dateien["projekt.md"]
       and "Netz rein, fertig." in dateien["projekt.md"],
       "das Projekt mit Kennung, Beschreibung und Vision")
pruefe("## B-001 Kein Weg zurueck" in dateien["sammlung.md"]
       and "### Beschreibung" in dateien["sammlung.md"],
       "die Sammlung mit Kennung und Abschnitten")
pruefe("- [x] Dienste abschalten" not in dateien["aufgaben.md"]
       and "- [ ] Dienste abschalten" in dateien["aufgaben.md"],
       "die Haekchenlisten als Markdown-Kaestchen, ungehakt was offen ist")
pruefe("Was dazwischenkam" in dateien["meilensteine.md"]
       and "Der Pi war nicht da." in dateien["meilensteine.md"],
       "die Umwege am Meilenstein")
pruefe("### Was entschieden wurde" in dateien["entscheidungen.md"]
       and "### Der Verlauf" in dateien["entscheidungen.md"],
       "Entschluss und Verlauf getrennt, wie in der Karte")

print("\nSchreiben und vergleichen")
ziel = tmp / "ausgang"
pruefe(export.aktuell(conn8, pjx, ziel) == list(export.DATEIEN),
       "vor dem ersten Lauf weichen alle fuenf ab")
export.schreiben(conn8, pjx, ziel)
pruefe(export.aktuell(conn8, pjx, ziel) == [],
       "danach keine mehr -- verglichen wird der Inhalt, nicht ein "
       "Zaehler")
datenbank.topic_anlegen(conn8, px, "Noch etwas", bx, "2026-09-07")
pruefe(export.aktuell(conn8, pjx, ziel) == ["sammlung.md"],
       "ein neuer Eintrag laesst genau eine Datei abweichen")
export.schreiben(conn8, pjx, ziel)
pruefe(export.aktuell(conn8, pjx, ziel) == [],
       "und ein zweiter Lauf gleicht sie wieder an")

stand = export.stand(pjx, ziel)
pruefe(stand["dateien"] == 5 and stand["bytes"] > 0
       and stand["beschreibbar"],
       "der Stand nennt Dateien, Groesse und ob geschrieben werden kann")
pruefe(export.stand(pjx, Path("."))["eingerichtet"] is False,
       "ohne Zielverzeichnis sagt der Stand das, statt irgendwohin zu "
       "zeigen")

print("\nDie Werkseinstellung")
vorher = datenbank.projekt(conn8, px)["bestand"]
weg = datenbank.projekt_leeren(conn8, px)
nachher = datenbank.projekt(conn8, px)
pruefe(weg["sammlung"] == vorher["sammlung"] and weg["bereiche"] == 1,
       "sie meldet, was weggeraeumt wurde")
pruefe(sum(nachher["bestand"].values()) == 0
       and not nachher["bereiche"],
       "danach ist der Bestand leer")
pruefe(nachher["name"] == "MARLEI Boot"
       and nachher["vision"] == "Netz rein, fertig.",
       "das Projekt selbst bleibt -- das ist der Unterschied zum "
       "Loeschen")

conn8.commit()
conn8.close()

print("\nEine Spalte, die weggefallen ist")

# Eine Ablage in der Fassung von gestern: meilenstein_dazwischen traegt
# noch die Spalte art, und zwar NOT NULL. Ohne den ENTFALLEN-Schritt
# scheitert danach jeder INSERT an etwas, das im Quelltext gar nicht
# mehr vorkommt.
alt = tmp / "alte-fassung.db"
vor = sqlite3.connect(alt)
vor.executescript("""
CREATE TABLE meilensteine (id INTEGER PRIMARY KEY, benennung TEXT);
CREATE TABLE meilenstein_dazwischen (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    meilenstein_id INTEGER NOT NULL REFERENCES meilensteine(id),
    art            TEXT NOT NULL CHECK (art IN ('UMWEG', 'RAST')),
    datum          TEXT NOT NULL,
    text           TEXT NOT NULL);
""")
vor.execute("INSERT INTO meilensteine (id, benennung) VALUES (1, 'Alt')")
vor.execute("INSERT INTO meilenstein_dazwischen (meilenstein_id, art, datum, "
            "text) VALUES (1, 'RAST', '01.09.2026', 'Gewartet')")
vor.commit()
vor.close()

nach = datenbank.verbindung(alt)
datenbank.anlegen(nach)
spalten = [r["name"] for r in
           nach.execute("PRAGMA table_info(meilenstein_dazwischen)")]
pruefe("art" not in spalten,
       "die weggefallene Spalte ist beim naechsten Start weg -- von Umweg "
       "und Rast bleibt der Umweg")
zeile = nach.execute("SELECT text FROM meilenstein_dazwischen").fetchone()
pruefe(zeile and zeile["text"] == "Gewartet",
       "und die vorhandene Zeile bleibt stehen -- eine gestrichene Art "
       "loescht keine Notiz")
nach.execute("INSERT INTO meilenstein_dazwischen (meilenstein_id, datum, text) "
             "VALUES (1, '07.09.2026', 'Ging nicht')")
pruefe(True, "ein INSERT ohne art laeuft danach durch")
nach.commit()
nach.close()

print("\nWo die Ablage liegt")
# ZWEI SYSTEME, ZWEI ORTE. Windows ist noch nicht gebaut, aber es ist ein
# Ziel -- und ein fester Unix-Pfad ergaebe dort "C:\\var\\lib\\..." und
# damit einen Ort, den niemand erwartet.
vorgabe = datenbank.vorgabe_ablage()
pruefe(vorgabe.name == "tasks.db",
       "die Vorgabe endet auf tasks.db -- eine Datei, und sie ist alles")
if os.name == "nt":
    pruefe("var" not in vorgabe.parts and vorgabe.drive,
           "unter Windows steht sie unter %ProgramData%, nicht unter "
           "einem erfundenen C:\\var\\lib")
else:
    pruefe(str(vorgabe) == "/var/lib/marlei-tasks/tasks.db",
           "unter Linux bleibt es /var/lib -- der Platz fuer den "
           "veraenderlichen Zustand eines Dienstes")

# EIN LEERES MARLEI_DB ZAEHLT ALS KEINS: Path("") ist Path(".") und damit
# wahr -- die Ablage laege sonst im Arbeitsverzeichnis des Dienstes.
# Dieselbe Falle wie beim Ausgang, und dort hat sie schon einmal
# zugeschnappt.
pruefe(datenbank.ablageort("") == vorgabe
       and datenbank.ablageort("   ") == vorgabe,
       "ein leeres MARLEI_DB zaehlt als keins, nicht als »hier«")
pruefe(datenbank.ablageort(str(tmp / "anderswo.db")) == tmp / "anderswo.db",
       "und ein gesetztes gewinnt immer")


# ===================================================================== #
print("\nProjekt 0 -- ein Befund, der keinem Projekt gehoert")
# ===================================================================== #
#
# Seit dem 22.09.2026 traegt "kenntnis" keinen Fremdschluessel mehr:
# Der Befund "eine neuere Fassung liegt bereit" betrifft die
# Installation und nicht den Bestand, und er soll sich wegklicken
# lassen wie jeder andere.
#
# DER UMBAU AUF EINER BESTEHENDEN ABLAGE ist der Fall, der zaehlt.
# "CREATE TABLE IF NOT EXISTS" nimmt aus einer vorhandenen Tabelle nichts
# heraus, und SQLite kennt kein DROP CONSTRAINT -- ohne den Umbau in
# anlegen() scheiterte das Wegklicken auf jeder Maschine, die vor diesem
# Tag installiert wurde, mit "FOREIGN KEY constraint failed".

alt = Path(tempfile.mkdtemp()) / "alt.db"
mit_fk = sqlite3.connect(alt)
mit_fk.executescript("""
    CREATE TABLE projekte (id INTEGER PRIMARY KEY, name TEXT);
    INSERT INTO projekte (id, name) VALUES (1, 'eins');
    CREATE TABLE kenntnis (
        projekt_id INTEGER NOT NULL REFERENCES projekte(id),
        befund     TEXT NOT NULL,
        seit       TEXT NOT NULL,
        marke      INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (projekt_id, befund)
    );
    INSERT INTO kenntnis VALUES (1, 'luecken', '2026-09-01', 3);
""")
mit_fk.commit()
mit_fk.close()

frisch = sqlite3.connect(alt)
frisch.row_factory = sqlite3.Row
frisch.execute("PRAGMA foreign_keys = ON")
datenbank.anlegen(frisch)

pruefe(not list(frisch.execute("PRAGMA foreign_key_list(kenntnis)")),
       "der Fremdschluessel auf projekte ist weg")
uebrig = list(frisch.execute("SELECT * FROM kenntnis"))
pruefe(len(uebrig) == 1 and uebrig[0]["befund"] == "luecken"
       and uebrig[0]["marke"] == 3,
       "und die weggeklickten Karten sind dabei mitgekommen, nicht "
       "weggeworfen")
frisch.execute(
    "INSERT INTO kenntnis (projekt_id, befund, seit, marke) "
    "VALUES (0, 'neuefassung', '2026-09-22', 2)")
pruefe(True, "Projekt 0 laesst sich eintragen -- »gehoert der Maschine«")

# Und die Zusage, die das Schema nicht mehr gibt, haelt jetzt diese
# Pruefung: Jede Kenntnisnahme gehoert zu einem echten Projekt ODER zur
# 0. Eine dritte Moeglichkeit gaebe es nur durch einen Fehler im Code.
frisch.execute("INSERT INTO kenntnis VALUES (99, 'luecken', '2026-09-22', 1)")
verwaist = [z["projekt_id"] for z in frisch.execute(
    "SELECT projekt_id FROM kenntnis WHERE projekt_id <> 0 "
    "AND projekt_id NOT IN (SELECT id FROM projekte)")]
pruefe(verwaist == [99],
       "eine Kenntnisnahme ohne Projekt faellt jetzt einer Abfrage auf "
       "und nicht mehr der Ablage -- der Preis des Umbaus")
frisch.close()


print()
if FEHLER:
    print("%d Pruefung(en) fehlgeschlagen:" % len(FEHLER))
    for f in FEHLER:
        print("  - %s" % f)
    sys.exit(1)
print("Alle Pruefungen bestanden.")
