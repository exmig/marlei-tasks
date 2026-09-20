# MARLEI Tasks — Datei oder Datenbank

**Wie die Einträge liegen sollen — und was ein Werkzeug an dieser Frage
ändert.**

*Entstanden am 06.09.2026 aus einer Frage beim Eintragen zweier
Beobachtungen in `marlei-boot`: „wie wäre es, wenn Aufgaben, Backlog,
Meilensteine in einer Datenbank stehen würden — wäre der Zugriff dann
schneller?" Die Zahlen in diesem Text sind an diesem Tag gemessen und
nicht geschätzt.*

---

## 1. Die Frage kam daher, dass es lange dauert

**Zwei Beobachtungen einzutragen kostete acht Arbeitsschritte, und sechs
davon hatten nichts mit dem Inhalt zu tun.** Verzeichnis lesen, Regeln
lesen, Muster lesen, den letzten Eintrag als Vorlage lesen, die
Zeilenenden prüfen, die höchste vergebene Kennung suchen. Erst danach
stand ein Zeichen Text.

Die naheliegende Erklärung war das Dateiformat: Die Sammlung ist eine
Markdown-Datei von 43 KB, das Archiv eine von 259 KB. Wer daraus etwas
wissen will, liest entweder alles oder tastet sich mit Zeilenbereichen
heran.

**Die Erklärung stimmt zur Hälfte, und die andere Hälfte ist die
wichtigere.**

---

## 2. Was das Anlegen wirklich kostet

Aufgeteilt nach dem, was eine Ablageform überhaupt beeinflussen kann:

| Kostenpunkt | Hängt an der Ablage? |
|---|---|
| Die nächste freie Kennung finden | ja |
| Die Kopfzeile bauen, Felder richtig schreiben | ja |
| Umbruch, Zeilenenden, Auszeichnung | ja — und nur an der *rohen* Datei |
| Den Block an die richtige Stelle hängen | ja |
| Das Verzeichnis nachziehen | ja |
| Titel, Bereich und Beschreibung schreiben | **nein** |
| Entscheiden, ob es ein Fehler oder eine Idee ist | **nein** |

**Die ersten fünf sind Formalie, der Rest ist die Sache selbst.** Eine
Datenbank nimmt die Formalie ab — aber sie schreibt keinen Titel und keine
Beschreibung, und sie entscheidet nicht, in welchen Bereich etwas gehört.

---

## 3. Ein Werkzeug nimmt dieselbe Formalie ab

Am selben Tag ist in `marlei-boot` ein kleines Skript entstanden, das
genau diese fünf Punkte erledigt: Kennung, Kopfzeile, Umbruch, Anhängen,
Verzeichnis. Danach kostet ein neuer Eintrag **drei Angaben** — Titel,
Bereich, Text. Alles andere hat eine Vorgabe.

**Genau drei Angaben verlangt auch ein `INSERT`.** Damit ist der Vergleich
nicht mehr *Datei gegen Datenbank*, sondern *Datei mit Werkzeug gegen
Datenbank* — und beim Anlegen nehmen die beiden einander nichts.

**Die Lehre ist deshalb nicht die Wahl der Ablage, sondern diese:** Wo
eine Regel Formalie verlangt, muss das Werkzeug sie übernehmen. Sonst wird
die Regel umgangen — siehe Abschnitt 7.

---

## 4. Wo die Datenbank tatsächlich gewinnt

Drei Punkte, und keiner davon heißt Bequemlichkeit.

**Die Kennung ist eine Frage der Richtigkeit.** Sie wird nie
wiederverwendet, also muss die höchste je vergebene gefunden werden — auch
die aus längst archivierten Einträgen. Das Skript sucht sie mit einem
Muster über alle Dateien und zählt dabei auch Kennungen mit, die bloß im
Fließtext erwähnt sind. Das ist die harmlose Richtung: höchstens eine
Nummer übersprungen, nie eine doppelt vergeben. Eine Ablage, die selbst
hochzählt, *kann* sich hier nicht irren.

**Das Lesen einer einzelnen Sache.** Eine Abfrage liefert einen Eintrag,
eine Datei liefert alle. Bei 43 KB fällt das nicht auf, bei 259 KB schon.

**Die Fragen, die quer stehen.** *Was liegt seit Wochen?* *Was ist
entschieden und trotzdem nicht angefangen?* Das sind Abfragen. Heute
beantwortet sie ein Skript, das Verzeichnistabellen in die Dateien
hineinschreibt — **eine Datenbank, die sich durch die Hintertür
einrichtet.** Man sollte sie durch die Vordertür hereinlassen.

---

## 5. Die Regeln, die es nur wegen der Rohansicht gibt

Die Mappe wird **roh** gelesen, im Texteditor und nicht gerendert. Das ist
eine bewusste Entscheidung und der Grund für eine ganze Klasse von Regeln:

- Fließtext wird auf 74 Spalten gebrochen.
- Eine Fettstelle muss auf eine Zeile passen, sonst färbt der Editor sie
  halb ein.
- Die erste Kopfzeile endet mit zwei Leerzeichen — dem harten Umbruch aus
  Markdown, unsichtbar und beim Aufräumen schon verlorengegangen.
- Die Dateien halten LF; ein angehängtes CRLF hinterlässt sie gemischt.
- Erledigtes wird mit `[erledigt]` markiert statt durchgestrichen, weil
  der Editor Tilden nicht rendert.

**Keine dieser Regeln hat mit dem Inhalt eines Eintrags zu tun.** Sie sind
der Preis dafür, dass die Rohdatei die Leseoberfläche ist; ein eigenes
Skript existiert ausschließlich, um zwei davon durchzuhalten.

**In einem Produkt mit eigener Oberfläche entfällt diese ganze Klasse.**
Das ist der stärkste Punkt für die Datenbank — stärker als
Geschwindigkeit.

---

## 6. Was dabei nicht verlorengehen darf

**Die Regeln fallen weg, ihr Zweck nicht.** Jede zielt darauf, dass ein
langer Eintrag sich überfliegen lässt:

| Regel in der Datei | Was daraus in der Oberfläche wird |
|---|---|
| Werte oben, vor der Beschreibung | Der Kopf des Eintrags, immer sichtbar |
| Fett gliedert, kursiv betont | Typografie statt Zeichensetzung |
| Höchstens eine Fettstelle je Absatz | Eine Führungszeile je Abschnitt |
| `[erledigt]` statt durchgestrichen | Ein Zustand, kein Textstil |
| Ein Strich statt eines leeren Feldes | *Nicht entschieden* ist ein Wert |

**Der letzte Punkt ist der, den eine Datenbank am leichtesten kaputt
macht.** In der Mappe bekommt ein Feld ohne Inhalt einen Gedankenstrich,
und die Begründung steht in den Regeln: *Eine fehlende Zeile liest sich
wie ein Versehen, ein Strich wie eine Entscheidung.* Ein `NULL` ist genau
die fehlende Zeile. Priorität und Abschluss brauchen deshalb einen
ausdrücklichen Wert für „noch nicht entschieden" — und der ist etwas
anderes als *kein Wert*.

---

## 7. Der Beleg, der am meisten wiegt

**Die harte Regel wurde an dem Tag umgangen, an dem das Werkzeug entstand
— von uns selbst.** Sie lautet: An einer rohen Beobachtung wird nicht
gearbeitet, sie wird vorher zu einer Aufgabe geschärft. Tatsächlich wurde
die Beobachtung vormittags eingetragen, mittags gebaut, und die Aufgabe
entstand danach, um den Vorgang sauber abzuschließen.

Das ist kein Argument gegen die Regel. Es ist der Beleg für das, was in
der Einordnung (`mappe/einordnung.md`, nicht im Repository) unter
*Risiken* steht: **Eine Regel, deren
Weg teuer ist, wird umgangen — auch von dem, der sie aufgestellt hat.**
Der Weg zu einer Aufgabe muss zehn Minuten kosten, und davon dürfen neun
auf das Denken entfallen und keine auf die Form.

Für das Produkt heißt das: *Der Knopf „daraus eine Aufgabe machen" ist
keine Bequemlichkeit, sondern die Bedingung dafür, dass die Ebene
überhaupt benutzt wird.*

---

## 8. Was daraus für den Bau folgt

- **Datenbank als Ablage, Oberfläche als Ansicht.** Die Rohansicht ist
  eine Notlösung für ein Werkzeug ohne eigenes Gesicht; dieses Produkt
  hat eines.
- **Kennungen zählt die Ablage hoch**, nicht ein Suchlauf über den
  Bestand. Nie wiederverwenden, auch nach dem Archivieren nicht.
- **Jedes Feld hat einen Wert für „noch nicht entschieden"** und
  unterscheidet ihn von *leer*.
- **Vorgaben, wo es eine sinnvolle gibt** — Kategorie, Priorität,
  Eintragsdatum. Ein Eintrag darf nie an einem Pflichtfeld scheitern, für
  das es eine Vorgabe gäbe.
- **Der Ausgang bleibt Text.** Was heute die Rohdatei leistet — lesbar
  ohne das Werkzeug, gesichert durch Kopieren —, muss ein Export
  leisten. Sonst ist das Archiv nur so lange etwas wert, wie die
  Anwendung läuft.
- **Was die Verzeichnisse heute von Hand tun, tut die Abfrage.** Die drei
  Proben aus der Einordnung — Bündel, Dreimonate, Liegen — sind Abfragen
  und kein Text.

---

*Offen und hier bewusst nicht entschieden: welche Datenbank, und ob es
neben der Ansicht eine gerenderte Textfassung geben soll. Beides gehört in
das Entscheidungsregister dieses Produkts, sobald es eines gibt.*

**Nachgetragen am 06.09.2026:** Die erste der beiden Fragen ist
beantwortet — **SQLite**, mit der Begründung in [Aufbau](aufbau.md),
Abschnitt 4. Dort hängt mehr daran als eine Technikwahl: Ihre Schwäche,
der zweite gleichzeitige Schreiber, ist zugleich die Grenze zwischen der
Community- und der Pro-Fassung geworden.

**Die zweite Frage ist am 07.09.2026 verneint worden — vorerst.** Eine
gerenderte Textfassung neben der Ansicht wird nicht gebaut.

**Was dabei nicht wegfällt, und das ist der Unterschied:** Die Forderung
in Abschnitt 8, dass **der Ausgang Text bleibt**, steht weiter. Sie wird
vom **Export** erfüllt — nicht von einer gerenderten Fassung. Wer den
Export streicht, streicht die Zusage; wer die gerenderte Fassung
streicht, streicht eine Bequemlichkeit.

*Vorerst* heißt: Sollte sich zeigen, dass der Export gelesen und nicht
nur gesichert wird, ist die Frage wieder offen.

**Nachgetragen am 07.09.2026, beim Bau des Reiters Projekte:** Ein Datum
liegt in der Ablage nach **ISO** (`2026-09-07`) und steht in der Ansicht
**deutsch** (`07.09.2026`).

Das ist keine Vorliebe, sondern eine Folge des letzten Punktes in
Abschnitt 8: *Was die Verzeichnisse heute von Hand tun, tut die Abfrage.*
Die drei Proben rechnen mit Daten — als `07.09.2026` sortiert SQLite nach
dem Tag und vergleicht Jahre gar nicht. **Angezeigt wird trotzdem nie so:**
Die Mappe schreibt `07.09.2026`, und genau das steht in jedem Verweis, den
jemand liest. Die Umrechnung macht `datenbank.datum_zeigen()`; was nicht
wie ein ISO-Datum aussieht, kommt unverändert zurück — ein Strich bleibt
ein Strich.

**Nachgetragen am 07.09.2026: Der Export hat einen zweiten Zweck bekommen.**

Bisher war er zweierlei — die Zusage aus Abschnitt 8, dass **der Ausgang
Text bleibt**, und die erste der beiden Sicherungen vor dem Löschen eines
Projekts. Die Entscheidung an diesem Tag macht ihn zum dritten:
**Tasks exportiert in den Projektordner `marlei-internal`**, ein privates
Repository.

**Damit wird der Export der Weg, auf dem der Bestand eine
Versionsgeschichte bekommt** — datiert, mit Grund im Commit, nachlesbar.
Das ist es, was den Mappen von Boot und Tasks heute fehlt: Sie hängen an
einer Dateikopie, nicht an einem Verlauf.

**Und daraus folgt eine Anforderung, die man beim Bauen leicht verfehlt:
Der Export muss stabil sein.** Bei unverändertem Bestand muss er
byteweise dasselbe liefern — gleiche Reihenfolge, kein Zeitstempel im
Kopf, keine wechselnde Formatierung. Sonst erzeugt jeder Lauf einen
Unterschied über alles, und die Versionsgeschichte sagt nichts mehr.

*Nicht gebaut wird dafür eine dritte Papiermappe in `marlei-internal`.
Erwogen und am 07.09.2026 verworfen: Tasks wird fertig, der Bestand aus
Boot wird übernommen, dann exportiert Tasks dorthin. Drei Mappen zu
pflegen, kurz bevor das Werkzeug sie ersetzt, wäre die Arbeit zweimal.*
