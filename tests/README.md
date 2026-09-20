# Tests

```bash
python tests/test_datenbank.py          # braucht nichts ausser Python

python -m venv venv                     # fuer den Rest:
./venv/bin/pip install -r webui/requirements.txt httpx
./venv/bin/python tests/test_app.py
./venv/bin/python tools/pruefe-gemeinsam.py
```

Unter Windows dasselbe mit den Pfaden, die es dort gibt:

```powershell
py -3 tests\test_datenbank.py

py -3 -m venv venv
.\venv\Scripts\pip install -r webui\requirements.txt httpx
.\venv\Scripts\python tests\test_app.py
.\venv\Scripts\python tools\pruefe-gemeinsam.py
```

**Beide Reihen laufen auf beiden Systemen, und sie pruefen auf beiden
dasselbe.** Das ist keine Selbstverstaendlichkeit: Wo eine Pruefung an
der Maschine haengt, auf der sie gerade laeuft, prueft sie auf der
anderen nichts -- und dort bleibt dann stehen, was falsch ist. Die
Weichen `auslastung.SYSTEM`, `firewall.SYSTEM`, `bericht.SYSTEM` und
`app.WINDOWS` sind genau dafuer Variablen und keine Abfragen mitten im
Code.

**test_datenbank.py** legt das Schema in einem Wegwerf-Verzeichnis an und
prüft **die Entscheidungen, nicht das Anlegen.** Dass ein `CREATE TABLE`
durchläuft, sagt nichts; geprüft wird, ob die Regeln in der Ablage
wirklich gelten:

- Eine gelöschte Kennung kommt nie wieder — sonst zeigte ein alter
  Verweis später auf etwas anderes.
- Die Arten zählen getrennt und über alle Projekte hinweg.
- Zwei Projekte können nicht denselben Namen tragen. Das ist keine
  Ordnungsliebe: Das Losungswort der Werkseinstellung *ist* der
  Projektname.
- `AKTIV` ohne Datum wird abgewiesen — *mit Datum außer bei PASSIV.*
- Prio und Abschluss stehen auf dem Strich, nicht auf `NULL`. *Eine
  fehlende Zeile liest sich wie ein Versehen, ein Strich wie eine
  Entscheidung.*
- Die Suche findet zwei zusammengehörende Einträge über ihre
  **Beschreibung**, nicht über den Titel — das ist die Bündelprobe aus
  der Einordnung, und der Grund, warum FTS5 mitkommt.

**test_app.py** startet die Anwendung gegen eine Wegwerf-Ablage und prüft
zweierlei: den Rahmen, den alle neun Reiter teilen, und den einen Reiter,
der gebaut ist. Zuerst der Rahmen:

- Alle neun Reiter antworten, und `/` ist **Projekte**, nicht Server
  Health. Ohne gewähltes Projekt haben die vier folgenden Reiter nichts
  zu zeigen.
- Beide Stylesheets werden geladen, und das eigene steht **hinter** dem
  geteilten — sonst überschriebe die falsche Datei.
- Die Fußzeile zeigt **nicht** auf ein Repository, das es noch nicht
  gibt.
- Das gewählte Projekt steht auf **allen neun** Reitern im Band, nicht
  nur auf dem, wo es gewählt wurde. Das ist der ganze Punkt: Eine
  Auswahl, die vier Seiten filtert und dort unsichtbar ist, lässt
  jemanden ins falsche Projekt eintragen.
- Ein Cookie auf ein gelöschtes Projekt gilt als keines.

Und dann der **Reiter Projekte**, seit dem 07.09.2026:

- Anlegen antwortet mit **303**, nicht 302 — danach ist es ein GET, und
  ein F5 wiederholt kein POST. Beim Löschen wäre das kein
  Schönheitsfehler.
- Wer ein Projekt anlegt, hat es danach **gewählt**. Ein zweiter Klick
  für eine Absicht, die schon feststand, ist keiner.
- Abgewiesen und **gesagt** wird: ohne Namen, ohne Eintragsdatum, mit
  einem Namen, den es schon gibt, mit einem erfundenen Zustand.
- Das Datum steht in der Ablage nach **ISO** und in der Ansicht
  **deutsch** — beides wird geprüft, denn beides ist Absicht.
- Gespeichert wird die ganze Seite auf einmal, und **nur was anders
  dasteht**. Ein Feldname aus dem Formular, den es nicht gibt, wandert
  nicht ins `UPDATE`.
- Ein Bereich mit einem Eintrag darauf **bleibt** — er sperrt, er mahnt
  nicht. *Sperren gehört zu dem, was nicht nachwachsen kann.*
- Das Losungswort beim Löschen ist der **Projektname**, nicht das Wort
  *Löschen*: Ein festes Wort bestätigt nur, DASS gelöscht wird, der Name
  bestätigt, WELCHES. Groß- und Kleinschreibung und Leerraum sind egal.
- Das Cookie auf ein gerade gelöschtes Projekt ist danach weg.
- Und zwei Prüfungen am **Satz**, nicht am Verhalten: Der Löschschritt
  zählt in Einzahl, wo einer liegt, und sagt bei einem leeren Projekt
  einen Satz statt vier Nullen. Beides ist beim ersten Blick auf die
  gebaute Seite aufgefallen, nicht in einem Test.

Und der **Reiter Sammlung**, ebenfalls seit dem 07.09.2026:

- **Ein unvollständiger `FEHLER` wird angelegt, nicht abgewiesen** — und
  es wird gesagt, wie viele der fünf Angaben fehlen. *Die fünf mahnen,
  sie sperren nicht.*
- **Der Bereich sperrt dagegen.** Ohne ihn, mit einem aus einem anderen
  Projekt, ohne Titel oder mit einer dritten Kategorie wird abgewiesen.
- **Ein leeres Eintragsdatum wird zu heute** — anders als beim Projekt:
  Was auffällt, fällt heute auf.
- **Die Suche findet zwei Einträge über ihre Beschreibung**, obwohl
  keiner der Titel das Wort enthält. Das ist die Bündelprobe.
- **Die Durchsicht vergibt die Priorität und vermerkt, dass hingesehen
  wurde** — auch wenn nichts geändert wurde.
- **Zusammenlegen fragt, bevor es anlegt:** ohne Titel führt der Knopf in
  den Bündelschritt. Die Aufgabe erbt danach die stärkste der
  Prioritäten, beide Einträge verschwinden aus der Sammlung, und die
  Meldung sagt, dass der Reiter Aufgaben noch fehlt.
- **Die Meldung hängt sich mit `&` an ein Ziel, das schon eine Frage
  trägt.** Ein zweites `?` ließ die Ansicht zurückfallen und die Meldung
  verschwinden — gefunden beim Bau der Sammlung, weil deren Ziele als
  erste eine Frage tragen.

Und der **Reiter Aufgaben**, seit dem 07.09.2026:

- **Ohne Abnahme wird nichts angelegt** — nicht im Formular und nicht
  beim Zusammenlegen. Die Meldung nennt dabei den Ausgang, nicht nur das
  Verbot.
- **Ohne Ursache wird sehr wohl angelegt** und trägt ein Abzeichen. Das
  ist die Gegenprobe: *Sperren gehört zu dem, was nicht nachwachsen kann.*
- **Der Bündelschritt fragt nach beidem** und bietet den zweiten Ausgang
  an — *das schaffe ich nicht, zurück in die Sammlung.*
- **Aus zwei Zeilen werden zwei Abnahmepunkte**, aus der Leerzeile
  dazwischen keiner.
- **Erledigt hängt an der Abnahme, nicht an der Arbeitsliste** — und der
  Server prüft es, nicht nur der ausgegraute Knopf.
- **Ein Haken lässt sich wieder wegnehmen.** Ohne die Liste aller Punkte
  im Formular ginge das nie: Ein leeres Kästchen schickt nichts mit.
- **Der letzte Abnahmepunkt bleibt** — sonst wäre die Sperre nachträglich
  zu umgehen.
- **AKTIV ohne Datum wird als Meldung abgewiesen**, nicht als Fehler; die
  Ablage lässt es ohnehin nicht zu.
- **Der Ursprung ist ein Verweis:** Wer den Eintrag umbenennt, benennt
  den Verweis mit — es gibt keine zweite Fassung, die veralten könnte.

Und der **Reiter Meilensteine**, seit dem 07.09.2026:

- **Er darf leer entstehen, aber nicht leer bleiben** — angelegt wird
  auch ohne Aufgabe, und es wird gesagt, dass er so lange als Befund
  steht.
- **Ein Kreis wird abgewiesen**, auch über drei Ecken. Die Ablage
  verbietet nur den direkten Fall.
- **Vorgänger sind eingetragen, Nachfolger abgelesen** — wer umbenennt,
  benennt den Verweis mit.
- **Abnehmen hängt an den Aufgaben:** solange eine offen ist, geht es
  nicht; ohne jede Aufgabe gibt es nichts abzunehmen. Der Server prüft
  es, nicht nur der ausgegraute Knopf.
- **Die Abnahme setzt Abschluss und Datum in einem Zug**, und die Meldung
  nennt Dauer und Umwege — die drei anderen Handgriffe fallen ab, statt
  getan zu werden.
- **Abgenommen verschwindet er aus der Liste der offenen**, aus der
  Ablage nicht. Das ist Regel 7, umgedreht.
- **Der kurze Weg notiert den Umweg** am gewählten Stein; ohne Satz ist
  es keine Notiz.
- **Verworfen ist der Termin, nicht die Arbeit:** Die Aufgaben darunter
  bleiben und stehen wieder ohne Stein da.
- **Das Feld Meilenstein an einer Aufgabe ist echt** — der Satz über den
  fehlenden Reiter ist ersetzt, nicht vergessen worden. Ein leeres Feld
  heißt *keinem zugeschlagen*, nicht die Nummer null.
- Und **eine weggefallene Spalte verschwindet beim nächsten Start**, ohne
  die vorhandenen Zeilen mitzunehmen — das Gegenstück zu `NACHZUEGLER`.

Und der **Reiter Entscheidungen**, seit dem 07.09.2026:

- **Freistehend ist erlaubt** — zwei Drittel der Entscheidungen in Boots
  Mappe hängen an nichts.
- **Ein ENTSCHLUSS ohne Satz wird trotzdem angelegt** und mahnt; bei
  `OFFEN` ist dasselbe leere Feld kein Befund, sondern die Auskunft
  selbst.
- **Nachtragen genügt** — der Befund verschwindet, ohne dass etwas
  gesperrt war.
- **Zeigen statt kopieren:** Der Titel des bezogenen Eintrags wird
  geholt, nicht gespeichert; wer ihn umbenennt, benennt den Verweis mit.
- **Die Liegeprobe:** `ENTSCHLUSS` mit noch offenem Eintrag *liegt*,
  `OFFEN` mit offenem Eintrag nicht — dort hält der Entschluss auf, nicht
  die Arbeit.
- **Die Entscheidung bleibt stehen**, auch wenn ihr Eintrag längst
  abgeschlossen ist. Das tut kein anderes Register.
- **Die Vorgabe ist alle, nicht offen**, und die Suche geht über Titel,
  Entschluss und Verlauf.
- **Gelöscht wird wirklich** — es gibt kein Archiv für Entscheidungen.
- Abgewiesen werden: ein erfundener Zustand, eine Bezugsart ohne Kennung
  (auch von der Ablage selbst), ein Bezug auf einen Eintrag, den es nicht
  gibt.

Und der **Reiter History**, seit dem 07.09.2026:

- **Es gibt keine einzige POST-Route** auf diesem Reiter — die Prüfung
  geht die Routentabelle durch. Er zeigt nur.
- **Die Straße trägt, was abgenommen ist**, mit der Dauer aus den zwei
  Daten und den Umwegen aus dem, was notiert wurde, als es passierte.
- **Ein verworfener Stein bekommt ein Datum, aber keine Abnahme:**
  `abnahme_am` bleibt leer, `abschluss_am` sagt, wann er die Liste
  verlassen hat. Auf der Straße steht er nicht, im Quittungsbuch schon.
- **`verworfen` bekommt eine Zeile, `aufgabe` nicht** — es ist nicht
  fertig, es zieht um. **Im Archiv steht es trotzdem:** Das Archiv fragt
  nicht, ob etwas fertig wurde, sondern was drinstand.
- **Im Archiv gibt es weder `<textarea>` noch `type="checkbox"`** — ein
  Kästchen, das nichts tut, ist schlimmer als keines.
- Eine erfundene Ansicht fällt auf die Straße zurück, ein erfundenes
  Register auf *alle*.

Und der **Reiter Einrichtung**, seit dem 07.09.2026:

- **Die achte Karte ist da, und die neunte fehlt nicht, sondern steht
  da:** Dass die IP-Übernahme aus Boot es hier nicht gibt und dass nach
  neuen Versionen nicht gesucht wird, prüft die Suite als Text auf der
  Seite — beides sind Aussagen, keine Lücken.
- **Die Stabilitätszusage wird zweimal geprüft**, gegen die Datenbank
  (`export.dateien` zweimal aufgerufen) und gegen die laufende Anwendung
  (zweimal `POST /einrichtung/export`, dann Byte für Byte). Ohne sie
  erzeugte jeder Lauf im Repository einen Unterschied über alles.
- **Verglichen wird der Inhalt, nicht ein Zähler:** Ein neuer Eintrag
  lässt genau eine Datei abweichen, ein zweiter Lauf gleicht sie an.
- **`Path("")` ist `Path(".")`** — die Prüfung *ohne Zielverzeichnis*
  gibt deshalb `Path(".")` mit, nicht `Path("")`, sonst prüfte sie
  nichts.
- **Der Ordnername:** Kennung vorn (sie ändert sich nie), Umlaute
  umschrieben statt zerlegt — aus *Völlig* wird `voellig`, nicht
  `vollig`.
- **Der Fehlerbericht zählt, statt abzuschreiben:** Die Prüfung holt
  alle Titel der Sammlung und hält fest, dass keiner im Bericht steht.
  Ohne Haken fehlt der Umgebungsblock ganz.
- **Das Losungswort ist der Projektname**, nicht das Wort »Löschen«; mit
  dem falschen Wort passiert nichts.
- **Was bleibt, ist das Projekt selbst** — Name, Beschreibung, Vision
  stehen nach dem Zurücksetzen noch da. Das ist der ganze Unterschied
  zum Löschen, und deshalb wird es geprüft.


Und der **Reiter Hilfe**, seit dem 07.09.2026:

- **Die Anker sind ein Vertrag, und er wird in beide Richtungen
  geprüft:** jedes der 29 Fragezeichen auf den Karten findet seinen
  Abschnitt — und jeder Kartenabschnitt hier gehört zu einer Karte, die
  es noch gibt. Ohne die zweite Richtung bliebe beim Umbau ein Kapitel
  über eine Karte stehen, die niemand mehr findet.
- **Auch der Rückweg wird geprüft:** Jedes *Zur Karte →* landet auf einer
  `id`, die in der Vorlage dieses Reiters wirklich steht — und jeder
  Verweis innerhalb der Hilfe auf einen Abschnitt, den es gibt.
- **Sie schreibt nicht** — keine `POST`-Route unter `/hilfe`, dieselbe
  Prüfung wie unter History.
- **Sie gilt ohne gewähltes Projekt.** Die Prüfung holt sie mit einem
  frischen Client ohne Merkzettel: Wer nicht weiterkommt, hat oft genau
  deshalb keines gewählt.
- **Ein Satz wird im Wortlaut festgehalten:** dass es die seitenweiten
  Befunde noch nicht gibt. Was auf einer Hilfeseite steht, wird geglaubt —
  ein Versprechen ohne Mechanik ist dort der gefährlichste Fehler.


Und der **Reiter Server Health**, seit dem 07.09.2026:

- **Zwei Karten, nicht fünfzehn** — und die Prüfung hält fest, dass es
  keine Karte *Dienste* gibt: Eine Karte mit drei Zeilen statt fünf wäre
  eine andere Karte mit demselben Namen.
- **Er gilt ohne gewähltes Projekt.** Er beschreibt den Unterbau, nicht
  den Bestand — geholt mit einem frischen Client ohne Merkzettel.
- **Ohne Quelle liefert jede Funktion leere Werte statt einer
  Behauptung**, und die Zeile über den Dienst fällt ganz weg statt als
  Satzstumpf dazustehen (*„Dieser Dienst läuft .“*). **Der Fall wird
  hergestellt, nicht abgewartet:** ein leeres `/proc` und ein
  `auslastung.SYSTEM`, das auf `posix` gestellt ist. Vorher stand hier
  die Hoffnung, die Reihe laufe auf einer Maschine ohne `/proc` — auf dem
  Server prüfte sie damit gar nichts.
- **Und die Windows-Seite wird immer mitgeprüft**, auch auf einem Linux:
  `windows.py` ist dort importierbar und antwortet überall leer. Was auf
  einem Windows dazukommt, ist gemessen — Speicher, Prozessorlast,
  Betriebszeit und belegter Speicher dieses Prozesses.
- **Die Größe einer Struktur ist eine Prüfung wert:** `MIB_IF_ROW2` muss
  1352 Byte haben. Eine Zeile daneben, und der gemeldete Netzdurchsatz
  wäre eine Zahl aus fremdem Speicher — plausibel aussehend und falsch,
  der schlimmste Fehler, den eine Karte machen kann, die sonst nichts
  behauptet.
- **Das Lastmittel fehlt unter Windows und wird nicht ersetzt.** Es ist
  kein fehlender Wert, sondern ein Begriff, den dieses System nicht
  führt; die Kachel fällt weg. Die Kernzahl aus ihrer Unterzeile steht
  deshalb jetzt unter Serverdetails — und das wird auf beiden Systemen
  geprüft.
- **Die Zeile `nginx` bleibt stehen, wo es keinen gibt**, und sagt, dass
  keiner vorgesehen ist. *„nicht installiert“* wäre dort die falsche
  Auskunft: Es fehlt nichts.
- **Der Dativ zum vierten Mal, diesmal als Gegenprobe:** Die Laufzeit der
  Maschine steht im Nominativ (*2 Tage*), die Betriebszeit des Dienstes
  hinter „seit“ im Dativ (*seit 2 Tagen*). Zwei Funktionen, zwei Fälle.
- **Einmal fragen, dann prüfen.** `auslastung.cpu()` stand zweimal in
  einer Bedingung — und der zweite Aufruf kommt so schnell, dass der
  Kernel noch dieselbe Summe nennt: kein Unterschied, kein Prozentwert,
  und aus dem *oder* wurde ein Vergleich mit `None`.
- **`/proc` wird für eine Prüfung nachgebaut.** Ein Wegwerfverzeichnis,
  `auslastung.PROC` daraufgesetzt — und ein Prozessname, der die Falle
  enthält, um die es geht: `(uvi corn (x))`. Wer in `/proc/self/stat`
  nach Feldern zählt, statt hinter der letzten Klammer zu trennen,
  bekommt eine Zahl, die plausibel aussieht und falsch ist.
- **Der Dativ zum dritten Mal:** *seit 1 Tag*, aber *seit 2 Tagen* — und
  unter einer Minute wird nicht gerundet, sonst stünde ein frisch
  gestarteter Dienst mit *seit 0 Minuten* da.
- **Dieselben Angaben im Fehlerbericht und auf der Karte**, aus derselben
  Quelle. Zwei Quellen liefen auseinander, und dann nennt die Mail einen
  anderen Kernel als die Seite.
- **Der Stempel wird nicht mitgepuffert.** Ein zweiter Aufruf mit einem
  anderen Wert bekam den ersten zurück — in der Anwendung nie
  aufgefallen, weil der Stempel dort immer derselbe ist.
- **Der Platzhalter ist weg** (`leer.html`, `_seite()`), und die Prüfung
  hält auch das fest: Alle neun Reiter sind gebaut.


Und die **Befunde**, seit dem 07.09.2026:

- **Sie laufen über alle Projekte** — die Prüfung wählt ein drittes
  Projekt und erwartet trotzdem die Karten der beiden anderen. Das ist
  die einzige Stelle, an der die Vorauswahl nicht gilt.
- **Sie stehen auf jeder Seite**, nicht auf dem Reiter, zu dem sie
  gehören; geprüft wird es auf der Hilfe und unter Einrichtung.
- **Jeder Befund nennt sein Projekt im Titel und trägt den Weg dorthin.**
  Ohne die Angabe wüsste man, dass etwas liegt, aber nicht wo.
- **Zur Kenntnis genommen wird je Projekt:** Das Stillstellen im einen
  lässt dieselbe Lage im anderen laut. Das ist der Unterschied zu Boots
  Mechanik, und er wird einzeln geprüft.
- **Steigt die Marke, kommt die Karte zurück** — aus drei Lücken werden
  vier, und der Befund ist wieder da. Beim Durchsicht-Befund sind es
  angefangene Monate, damit das Wegklicken kein Aufschub bis morgen ist.
- **Was gerade nicht gilt, wird vergessen:** Ein Befund, der wiederkommt,
  fängt offen an.
- **Ein abgeschlossenes Projekt meldet nichts**, ein ruhendes schon.
- **Zwei Wege nach draußen sind abgeschnitten:** ein `zurück` und ein
  `ziel`, die nicht mit einem einzelnen `/` anfangen, fallen auf eigene
  Seiten zurück. Eine offene Weiterleitung ist billig zu verhindern und
  teuer zu übersehen.


Und die **Installation**, seit dem 07.09.2026:

- **`install.sh` läuft hier nicht** — das geht nur auf einem Debian.
  Geprüft wird stattdessen der Zusammenhalt seiner vier Dateien: Ein
  Port, der in der Einheit steht und im vhost nicht, fiele sonst erst auf
  der Maschine auf. Sie liegen seit der Windows-Fassung unter
  `setup/linux/`; dass `setup/` selbst keine Dateien mehr trägt, wird
  mitgeprüft — **je System ein Ordner, und keiner davon ist der
  Vorzugsfall.**
- **Kein `default_server` im vhost** — geprüft an den Anweisungen, nicht
  an den Kommentaren: Der Modulkopf erklärt gerade, warum es keines gibt.
  Ein zweites auf Port 80 ließe nginx nicht mehr starten, und dann stünde
  der Bootserver.
- **Einheit und vhost nennen denselben Anwendungsport**, und einen
  anderen als Boots 8080.
- **Jede `MARLEI_*`-Variable, die der Code liest, steht in der Vorlage.**
  Sonst fehlt sie in `/etc/marlei-tasks.env`, und niemand merkt es, bis
  etwas nicht geht. **In beiden Vorlagen**, und beide nennen denselben
  Satz Namen: Zwei Dateien mit anderen Werten sind eine Doppelung, und
  geprüft wird sie in beide Richtungen. Der Fall, der sonst durchrutscht:
  Ein neuer Wert kommt in die Linux-Vorlage, und auf Windows fehlt er —
  ohne Meldung.
- **Und keine Datei von MARLEI Boot wird angefasst:** weder
  `/etc/pxeweb` noch `sites-enabled/pxe` kommen im Skript vor.
Und die **Installation unter Windows**, seit dem 19.09.2026:

- **`install.ps1` läuft hier genauso wenig** — es braucht Administrator,
  ein `%ProgramFiles%` und eine Aufgabenplanung. Geprüft wird wieder der
  Zusammenhalt; die Syntax der Skripte prüft PowerShell beim Aufruf.
- **Eine Zahl, eine Quelle.** Ohne nginx davor ist die Adresse der einzige
  Ort, an dem der Port steht: `start.ps1` gibt ihn an uvicorn, `update.ps1`
  merkt sich ihn, die Karte nennt ihn — alle drei aus `MARLEI_BASE_URL`.
  Gegenprobe: Die Linux-Einheit hört weiter nur auf `127.0.0.1`.
- **Vier Angaben an der Aufgabe, die keine Geschmacksfrage sind:** beim
  Hochfahren, unter dem Konto `marlei-tasks`, **ohne Zeitlimit** — die
  Vorgabe der Aufgabenplanung wären drei Tage, und der Dienst wäre weg,
  ohne dass etwas abgestürzt ist — und kein zweiter Lauf daneben, denn das
  wäre ein zweiter Schreiber auf einer SQLite-Datei.
- **Das Konto: nicht SYSTEM, ohne erhöhte Rechte, ohne Anmeldung am
  Bildschirm.** Geprüft werden die drei Rechte in `files/konto.ps1`, dass
  sein Kennwort nie auf einer Befehlszeile steht, dass es das
  Datenverzeichnis ändern und die Einstellungen nur lesen darf — und dass
  es unter Windows heißt wie unter Linux. Das VERHALTEN (Konto anlegen,
  Rechte vergeben) braucht Administratorrechte und ist Abnahme, nicht
  Teil dieser Reihe.
- **Die Firewall wird nicht ungefragt angefasst**, und das wird am Ort
  geprüft: Vor der Abfrage des Schalters steht im ganzen Skript keine
  Zeile, die eine Regel anlegen könnte — auch keine, die nur so aussieht.
- **Der Stempel entsteht nach dem Spiegeln.** `robocopy /MIR` räumte ihn
  sonst bei jedem Lauf wieder weg; dieselbe Falle wie `rsync --delete`.
  Und die Ablage kommt nicht mit ins Programmverzeichnis.
- **Ohne BOM.** Die Umgebungsdatei wird ohne Byte-Order-Mark geschrieben —
  mit einem hieße der erste Name nicht `MARLEI_BASE_URL`, sondern trüge
  ein unsichtbares Zeichen davor, und der Port fiele stumm auf 80 zurück.
- **Kein Unix-Pfad in den drei Skripten.** `C:\var\lib` wäre genau der
  Ort, den die Vorgabe in `datenbank.py` vermeidet.
- **Update ohne Administrator, Installation mit** — dieselbe Trennung wie
  das *bitte ohne sudo* auf der anderen Seite. `update.ps1` weigert sich
  mit erhöhten Rechten und holt sie sich für `install.ps1` selbst.
- **Das Update fragt die Installation, nicht den Pull** (beide Seiten,
  seit dem 19.09.2026). `update.sh` und `update.ps1` lesen den Stempel
  `VERSION` der Installation und vergleichen ihn mit derselben Formel,
  mit der der Installateur ihn schreibt (`git describe --tags --always
  --dirty`). *Schon aktuell* heißt nur noch: Die Installation steht auf
  diesem Stand — vorher hieß es: Der Pull hat nichts gebracht, und nach
  einem `git pull` von Hand lief der alte Stand weiter. Ein Stand mit
  `-dirty` wird immer übernommen. Geprüft wird die Bauart; ob ein echtes
  Update dann installiert, ist Abnahme.
- **`start.ps1` schreibt mit, was uvicorn sagt.** Eine Aufgabe wirft die
  Ausgabe ihres Programms weg, und ein `journalctl` gibt es hier nicht.

Und das **Wieder entfernen**, seit dem 19.09.2026:

- **Geprüft werden die Namen gegen den Installateur** — `$AUFGABE`,
  `$REGELNAME`, `APP_DIR`, `DATA_DIR`, `DIENST`, `VHOST`. Ein Name, der im
  Deinstallieren anders heißt, lässt genau das stehen, was weg soll: eine
  Aufgabe, die beim nächsten Hochfahren ein Programm startet, das es nicht
  mehr gibt, und eine Firewallregel auf einen Port, auf dem niemand mehr
  hört. Das fällt sonst Monate später auf, oder nie.
- **Der Bestand wird nur hinter dem Schalter gelöscht, und das wird am Ort
  geprüft:** Vor der Rückfrage steht in beiden Skripten keine Zeile, die
  ihn anfassen könnte — dieselbe Prüfung wie bei der Firewallregel in
  `install.ps1`. Dazu, dass das Losungswort auf beiden Seiten dasselbe ist
  und dass ohne jemanden, der antworten kann, abgebrochen wird statt
  gefragt.
- **Kein Paketverwalter, keine fremde Deinstallation.** Beide Skripte
  *nennen* `apt-get remove nginx` — als Warnung. Geprüft werden deshalb
  nur die wirksamen Zeilen, nicht die Kommentare: dieselbe Unterscheidung
  wie beim `default_server` im vhost.
- **nginx wird neu geladen, nicht neu gestartet**, und vorher geprüft. Ein
  restart reißt die Verbindungen aller anderen Seiten hinter demselben
  nginx ab.
- **Die Firewallregel geht über ihren Namen weg, nicht über die
  Portnummer** — auf demselben Port kann etwas stehen, das jemand anderes
  braucht.
- **Das Dienstkonto geht nur mit dem Bestand.** Sonst blieben Dateien
  zurück, deren Besitzer eine Zahl ohne Namen ist.

**Das Verhalten von `uninstall.sh` ist zusätzlich nachgestellt geprüft**,
und zwar außerhalb dieser Reihe: eine Kopie mit umgebogenen Pfaden in
einem Wegwerfverzeichnis, sieben Fälle — nichts installiert, der
gewöhnliche Lauf, `--bestand` ohne Terminal, mit falschem und mit
richtigem Wort, ein zweiter Lauf, eine unbekannte Angabe. **Der Fall, auf
den es dabei ankommt:** In den drei Abbruchfällen ist hinterher *nichts*
angefasst — die Rückfrage kommt vor dem ersten Griff.

Und die **drei Karten, die von der Maschine reden**, werden auf beiden
Systemen geprüft — nicht nur auf dem, auf dem die Reihe gerade läuft:

- **Die Portliste und der Satz darunter, zweimal.** Unter Windows nennt
  sie die Anwendung selbst statt des nginx und den Remotedesktop statt
  `sshd`; der Satz darunter nennt dieselbe Zahl und keinen zweiten Port,
  den es dort nicht gibt. `system=` wird dabei ausdrücklich mitgegeben.
- **Die Karte *Einstellungen* sagt es je System anders**, und beide Sätze
  werden geprüft: Auf Debian gehört der Port dem nginx davor und steht
  *nicht* in der Umgebungsdatei, unter Windows steht er darin — als Teil
  der Adresse. Sonst prüft die Reihe den anderen Satz nie, und genau der
  bleibt dann falsch stehen.
- **Die dritte Antwort der Firewall: *nicht feststellbar*.** Fehlt der
  Schalter in der Registry, wäre *„also an“* ein Schluss aus der Vorgabe
  des Systems und keine Auskunft — auf der Karte stünde sonst *nichts im
  Weg*, eine Zusage, für die nichts vorliegt.

- **`/health` nennt Zahlen, keine Namen.** Die Prüfung legt ein Projekt
  mit einem auffälligen Namen an und hält fest, dass er in der Antwort
  nicht vorkommt — die Auskunft ist maschinenlesbar und fragt niemanden,
  wer er ist.


**pruefe-gemeinsam.py** ist kein Test der Anwendung, sondern des
Abschreibens: Es hält die mit MARLEI Boot geteilten Dateien gegeneinander
(`tools/gemeinsam.txt`). Es setzt keine Regel durch — die Regel lautet,
eine Änderung an einer geteilten Datei in **derselben Sitzung** in beide
Repositories zu tragen. Das Skript findet nur, was durchrutscht.

**Es liegt in beiden Repositories und läuft in beiden.** Ein Prüfer auf
nur einer Seite meldet nur, was auf dieser Seite auffällt: Wer in Boot
etwas an `style.css` ändert, bekommt dort keine Meldung. Skript und
Liste stehen deshalb selbst als `gleich` in der Liste — damit bewacht
der Prüfer die Doppelung, die er schafft. Das Gegenüber sucht er neben
dem eigenen Projektordner; `--gegen` gibt es von Hand an.
