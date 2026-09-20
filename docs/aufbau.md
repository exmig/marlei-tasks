# MARLEI Tasks — Aufbau

**Die Reiter, die mehreren Projekte, die vier Register und die Ablage.**

*Festgehalten am 06.09.2026, Reiter für Reiter durchgegangen. Die Felder
sind nicht erfunden, sondern an der Mappe von `marlei-boot` abgelesen —
sie ist der Probelauf dieses Produkts. Ihre Regeln gelten dabei als
Beleg, nicht als Pflichtenheft; Abschnitt 3 sagt, warum. Was aus MARLEI
Boot unverändert übernommen wird, steht in
[Übernahme](uebernahme.md). Die Abschnitte 6 bis 11 kamen am
07.09.2026 dazu, als die fünf Register und die Rückschau gebaut
wurden -- sie halten fest, was dabei anders ausfiel als hier
beschrieben.*

---

## 1. Die Reiter

**Neun statt Boots sieben**, festgelegt am 06.09.2026:

```
Projekte · Sammlung · Aufgaben · Meilensteine · Entscheidungen ·
Einrichtung · History · Hilfe · Server Health
```

Der erste, **Projekte**, hat einen eigenen Abschnitt — er trägt die
Vorauswahl, aus der alle folgenden aufgebaut werden, siehe Abschnitt 2.

**Die Leiste ist damit am Anschlag, und das ist eine Randbedingung.**
Ueberschlagen am 07.09.2026: Boots sieben Reiter brauchen rund 652 px und
haben 307 px Luft bis zur Breitengrenze der Leiste (60rem = 960 px). Die
neun hier brauchen rund 938 px -- **21 px Luft.**

Unter etwa 1000 px Fensterbreite bricht sie auf zwei Zeilen. Das ist kein
Fehler: Das Skript in `base.html` misst die Hoehe genau deshalb, statt
sie im Stylesheet zu pflegen. **Aber ein zehnter Reiter passt nicht mehr,
und ein Name laenger als *Entscheidungen* auch nicht.** Wer einen
dazustellen will, kuerzt vorher einen anderen -- oder entscheidet, dass
die Leiste zweizeilig sein darf.

*(Ueberschlag mit angenommener mittlerer Zeichenbreite, keine Messung im
Browser; die Zahl kann um ein Sechstel danebenliegen. Der Befund traegt
trotzdem, weil Boots Abstand dreizehnmal groesser ist.)*

### Woher die mittleren vier kommen

Die Mappe von `marlei-boot` ist der Probelauf dieses Produkts, und ihre
acht Dateien fallen **1:1** auf die Ebenen aus der Einordnung
(`mappe/einordnung.md`, nicht im Repository) — *vier Ebenen, dazu drei
Ablagen und eine Richtung*:

| Datei | Anteil | Frage | Ebene | Reiter |
|---|---|---|---|---|
| `05-backlog` | 7 % | Was ist aufgefallen? | Sammlung | **Sammlung** |
| `04-aufgaben` | 5 % | Woran wird gearbeitet? | Aufgabe | **Aufgaben** |
| `03-meilensteine` | 2 % | Was muss zusammen fertig werden? | Meilenstein | **Meilensteine** |
| `08-entscheidungen` | **30 %** | Warum ist es so? | Entscheidungsregister | **Entscheidungen** |
| `02-roadmap` | 4 % | Wie sind wir hierhergekommen? | Rückschau | History |
| `06-erledigt` | 6 % | Was ist fertig? | Quittungsbuch | History |
| `07-archiv` | **43 %** | Was stand da im Wortlaut? | Archiv | History |
| `01-vision` | 2 % | Wohin soll es gehen? | die Richtung | **Projekte** (als Feld) |

**Die Verteilung ist das Argument für den Zuschnitt, nicht die Zahl der
Ebenen.** Die Einordnung behauptet in Abschnitt 3, die Hälfte des Systems
sei Rückschau und Begründung. Gemessen am 06.09.2026 über 599 KB Mappe
sind es **79 %** — Archiv und Entscheidungen allein tragen 73 %. Die
laufende Arbeit, also das, was jedes andere Werkzeug zeigt, sind **15 %**.

**Damit ist Entscheidungen ein eigener Reiter und kein Unterpunkt.** Ein
Register, das dreißig Prozent des Bestands hält, hinter einer anderen
Seite zu verstecken, wäre dieselbe Fehleinschätzung, die die Einordnung
den anderen Werkzeugen vorwirft: *die Entscheidung lebt in Kommentaren.*

**History bekommt drei Dateien, nicht eine** — Roadmap, Quittungsbuch,
Archiv, zusammen 53 %. Das ist die Rückschau aus der Einordnung, und der
Reiter behält dabei den Namen aus Boot.

### Die Reihenfolge folgt Boots Prinzip, nicht Boots Positionen

Boots Leiste ist begründet, und zwar so: *sortiert nach der Häufigkeit im
Betrieb, nicht nach dem Weg beim Aufsetzen.* Aufgesetzt wird ein Server
einmal, benutzt wird er jahrelang.

**Dasselbe Prinzip ergibt hier eine andere Reihenfolge**, weil der
Gegenstand ein anderer ist. In Boot ist der Server das Produkt, deshalb
steht Server Health vorn. Hier ist er Unterbau: **Niemand öffnet eine
Aufgabenverwaltung, um die Prozessorlast zu sehen.** Er steht deshalb
ganz hinten — so entschieden im September 2026.

**Die Position zu übernehmen hätte geheißen, Boots Schluss zu kopieren
und seinen Grund wegzulassen** — derselbe Fehler wie bei den Karten in
[Übernahme](uebernahme.md), Abschnitt 5, eine Ebene höher. Der Wiedererkennungswert hängt nicht an
der Position des ersten Reiters, sondern an dem, was überall gleich ist:
Band, Kartenform, Farben und die feste Rückseite der Leiste.

**Eine Folge davon betrifft den Router:** In Boot ist Server Health die
Startseite unter `/`. Hier ist es der Reiter Projekte — und das ist
zwingend, nicht nur stimmig: Ohne gewähltes Projekt haben die vier
folgenden Reiter nichts zu zeigen.

### Was kein Reiter wird

**Die Liegeprobe ist ein Befund, keine Seite.** Die Einordnung nennt in
Abschnitt 8 den eigentlichen Nutzen für einen Chef: der Blick darauf,
*was entschieden wurde und trotzdem liegt.* Das ist ein Zustand, der
keiner Seite gehört — genau die Gattung, für die Boots Seitenkarten
gebaut sind ([Übernahme](uebernahme.md), Abschnitt 4). **Als Reiter müsste man ihn aufsuchen; als
Befund über jeder Seite kommt er von selbst**, mit Ampel und „zur
Kenntnis nehmen".

Damit beantwortet sich auch, wo die zweite Zahl aus der Einordnung
hingehört: In der Sammlung misst das Eintragsdatum die Liegedauer, an der
Aufgabe die Arbeitsdauer. Beide werden Befunde, keine Spalten in einer
Tabelle, die niemand sortiert.

---

## 2. Mehrere Projekte

**MARLEI Tasks trägt mehr als ein Projekt.** Die Vorgabe aus dem
September 2026: Der erste Reiter heißt **Projekte**, dort werden sie
angelegt und beschrieben, und **die Auswahl dort bestimmt, was auf Sammlung,
Aufgaben, Meilensteine und Entscheidungen steht.**

**Der Plural ist die Regel, nicht die Ausnahme:** Boots Register heißen
Clients, Systeme, Quellen. Der Reiter tut zweierlei — er listet alle
Projekte und beschreibt das gewählte —, und benannt wird er nach dem
Register, nicht nach der Auswahl.

**Damit ist die Vision untergebracht — besser, als ein Reiter es
gekonnt hätte.** Abschnitt 1 ließ sie offen, weil sie als einzige der
acht Mappendateien kein Register ist, sondern ein durchgehender Text.
Genau deshalb gehört sie nicht in eine Liste: **Ein Projekt hat genau
eine Vision.** Als Eingabefeld der Projektbeschreibung steht sie bei
dem, wofür sie gilt; ein eigener Reiter hätte für 2 % des Bestands eine
Seite gekostet und die Frage offengelassen, für welches Projekt sie
überhaupt spricht.

**Mehrere Projekte sind nicht mehrere Menschen.** Die Einordnung
(`mappe/einordnung.md`, nicht im Repository) zählt in Abschnitt 4 auf,
was mit der zweiten Person käme: Anmeldung, Rechte, Benachrichtigung, Datenhaltung
mit Sperren. **Nichts davon kommt hierdurch dazu.** Es bleibt die
Ein-Personen-Instanz — sie hat nur mehr als eine Sache am Laufen, und
das ist der Normalfall bei einem Chef, nicht die Ausnahme. Die bewussten
Auslassungen bleiben Auslassungen.

### Was in einem Projekt steht

**Fünf Felder, festgelegt am 06.09.2026.** Der Reiter Projekte ist der
einzige der fünf neuen ohne Vorbild in der Mappe — sie kennt nur ein
Projekt, sich selbst.

| Feld | Wert |
|---|---|
| **Kennung** | `P-`, wie die anderen Register |
| **Name** | die Bezeichnung, unter der es überall auftaucht |
| **Beschreibung** | worum es geht |
| **Vision** | wohin es gehen soll — der Inhalt von `01-vision.md` |
| **Zustand** | `AKTIV`, `RUHT` oder `ABGESCHLOSSEN` |

**Die Schreibweise ist Absicht:** Alle aufgezählten Werte der Mappe
stehen in Großbuchstaben — `MUSS`, `SOLL`, `KANN`, `IDEE`, `FEHLER`,
`PASSIV`, `AKTIV`, `PAUSE`. Ein Zustand in Kleinbuchstaben sähe aus wie
etwas anderer Art.

**Dazu gehört ein sechstes, das kein Feld ist, sondern eine Liste: die
Bereiche.** Boots sechs — `systeme`, `quellen`, `server`, `oberflaeche`,
`veroeffentlichung`, `mappe` — gelten in keinem anderen Projekt. **Der
Bereich ist damit projektspezifisch und wird hier gepflegt**, anders als
Kategorie und Priorität: Die beschreiben die *Art* eines Eintrags und
sind überall dieselben, der Bereich beschreibt den *Gegenstand*.

**Drei Dinge folgen daraus, und zwei sind Bedingungen:**

- **Der Name muss eindeutig sein.** Das ist keine Ordnungsliebe, sondern
  eine Folge der Werkseinstellung: Ihr Losungswort *ist* der Projektname.
  Gäbe es zwei gleichnamige Projekte, bestätigte die Eingabe nicht mehr,
  welches gemeint ist — und genau dafür ist sie da.
- **`ABGESCHLOSSEN` stellt die Liegeprobe still.** Befunde laufen über
  alle Projekte; ohne diese Ausnahme meldete ein fertiges Projekt bis in
  alle Ewigkeit, dass dort etwas seit Wochen liegt. Ein abgeschlossenes
  Projekt liegt nicht, es ist fertig.
- **`RUHT` tut das nicht.** Ein ruhendes Projekt ist genau der Fall, für
  den die Liegeprobe gebaut ist — das, in das seit Wochen niemand
  geschaut hat.

**Dazu ein Eintragsdatum** (entschieden am 07.09.2026) — wie in den vier
Registern, und aus demselben Grund, aus dem
[Datenhaltung](datenhaltung.md) es in Abschnitt 8 unter den sinnvollen
Vorgaben nennt. **Es trägt keine Vorgabe:** Ein erfundenes Datum wäre
schlimmer als eine Nachfrage.

### Die Vorauswahl ist ein Zustand, kein Reiter

**Das ist die Stelle, an der so etwas schiefgeht.** Eine Auswahl, die auf
einer Seite getroffen wird und auf vier anderen wirkt, ist unsichtbar,
sobald man den Reiter gewechselt hat. Wer dann etwas einträgt, trägt es
ins falsche Projekt — und merkt es erst Wochen später, wenn die Sammlung
Dinge enthält, die nicht dazugehören.

**Boot hat den Platz dafür schon gebaut.** Im Kopfband stehen Titel und
Serveradresse, und daneben die Kennzeichnung für einen Server, der nicht
die Produktion ist — ein Wort, das auf jeder Seite mitläuft, weil die
Farbe allein ein Code wäre, den man kennen muss. **Das gewählte Projekt
gehört in dieselbe Zeile**, aus demselben Grund: Es gilt für alles, was
darunter steht, also darf es nicht auf einer Seite versteckt sein.

### Die Werkseinstellung räumt nur das gewählte Projekt weg

**Entschieden am 06.09.2026.** Sie setzt ein Projekt auf den Zustand
zurück, in dem es angelegt wurde — die anderen bleiben unberührt.

**Damit trifft ein zerstörender Knopf ein Ziel, das nirgends im Formular
steht, sondern im Kopfband.** Das ist die Falle aus dem Abschnitt oben,
in ihrer schlimmsten Form: Wer an Projekt A denkt und auf Einrichtung
steht, sieht das Projekt nur oben in der Zeile — und dort steht
vielleicht B. Ein Klick, und die Arbeit von Wochen ist weg, aus dem
falschen Projekt.

**Boot hat die Abhilfe schon, sie muss nur schärfer gestellt werden.**
Dort verlangt die Karte ein Losungswort: `Löschen`, eingetippt, Groß-
und Kleinschreibung egal, Umlaut oder nicht egal — **und das Feld steht
leer da und trägt das Wort nur als grauen Hinweis.** Der Grund steht im
Quelltext: *Wäre es vorbelegt, genügte ein Druck auf die Eingabetaste;
dann könnte man die Abfrage auch weglassen.*

> **Das Losungswort ist hier nicht `Löschen`, sondern der Name des
> Projekts.** Ein festes Wort bestätigt nur, dass man gelesen hat, dass
> gelöscht wird. Der Projektname bestätigt, **welches**.

**Zusammen mit der Anforderung aus [Übernahme](uebernahme.md),
Abschnitt 6 — vorher ein Export —
sind das zwei Sicherungen, die verschiedene Fehler abfangen:** Der
Export fängt den Fehler ab, es überhaupt getan zu haben; der Name den,
es am falschen getan zu haben.

#### Gelöscht wird auf dem Reiter Projekte

**Entschieden am 07.09.2026.** Die Werkseinstellung *leert* ein Projekt,
sie löscht es nicht — dafür gibt es einen eigenen Knopf, dort wo die
Projekte stehen.

**Beide Wege verlieren dasselbe und tragen deshalb dieselben zwei
Sicherungen:** vorher ein Export, und der Projektname als Losungswort.
Sie unterscheiden sich nicht im Verlust, sondern in dem, was übrig
bleibt — ein leeres Projekt, an dem man neu anfängt, oder keines.

**In der Ablage kaskadiert von einem Projekt mit Absicht nichts.** Ein
`DELETE FROM projekte` scheitert an den Fremdschlüsseln, statt still den
ganzen Bestand mitzunehmen; gelöscht wird nur durch eine Funktion, die
die Reihenfolge kennt. *Was sich nicht rückgängig machen lässt, soll
nicht nebenbei passieren.* **Innerhalb eines Eintrags kaskadiert es sehr
wohl** — die Punkte einer Aufgabe, die Umwege eines Meilensteins: Sie
gehören ihm und haben ohne ihn keine Bedeutung.

### Kennungen zählen über alle Projekte

**Entschieden am 06.09.2026.** Es gibt eine Zählung je Art — `B-`, `A-`,
`M-` — und nicht eine je Art und Projekt. Damit gehört `B-066` genau
einem Eintrag, für immer.

**Der Grund ist der Verweis im Fließtext.** In der Mappe steht *„B-050
ist darin aufgegangen"* mitten in einem Absatz, ohne Projektangabe —
so wird verwiesen, und so wird es bleiben. Zählte jedes Projekt bei eins
an, wäre jeder dieser Verweise mehrdeutig, sobald ein zweites Projekt
existiert. **Eine Kennung, die man nur mit Zusatzangabe auflösen kann,
ist keine Kennung, sondern eine Zeilennummer.**

**Der Preis steht ausdrücklich hier, damit ihn niemand später
„repariert":** Die Nummern eines einzelnen Projekts springen. Ein
Projekt hat `B-003`, `B-007`, `B-012`, und das sieht nach Verlust aus.
Es ist keiner — die Lücken sind die Einträge der anderen Projekte.

Das deckt sich mit [Datenhaltung](datenhaltung.md), Abschnitt 4 und 8:
Die Kennung ist eine Frage der **Richtigkeit**, nicht der Bequemlichkeit;
hochzählen tut die Ablage, wiederverwendet wird nie — auch nach dem
Archivieren nicht. **Und es passt zur Entscheidung über die Befunde:**
Wenn eine Meldung über alle Projekte läuft, muss sie einen Eintrag
benennen können, ohne zu erklären, aus welchem Projekt er stammt.

### Befunde gelten über alle Projekte

**Entschieden am 06.09.2026, und es ist die einzige Stelle, an der die
Vorauswahl nicht gilt.** Der Grund steht in der Einordnung: Die
Liegeprobe ist der eigentliche Nutzen für einen Chef — und **er will
gerade das sehen, was in dem Projekt liegt, in das er seit Wochen nicht
geschaut hat.** Ein Befund, der nur das gewählte Projekt kennt, zeigt
ihm das nie; er meldete Ruhe, wo keine ist.

**Zwei Anforderungen folgen daraus, und beide sind leicht zu übersehen:**

- **Ein Befund nennt sein Projekt.** Über alle Projekte gerechnet ist
  eine Meldung ohne diese Angabe wertlos — man wüsste, dass etwas liegt,
  aber nicht wo. Und der Weg dorthin gehört an die Karte: Wer sie
  anklickt, landet im richtigen Projekt.
- **Zur Kenntnis genommen wird je Projekt, nicht je Befund.** Boots
  Mechanik lässt eine Warnung stillstellen, damit sie nicht auf jeder
  Seite steht. Läuft sie über alle Projekte, darf das Stillstellen in
  einem Projekt die gleiche Lage in einem anderen nicht mitnehmen —
  sonst verschwindet ein Befund, den nie jemand gesehen hat.

---

## 3. Die vier Register

### Die Mappe ist ein Beleg, kein Pflichtenheft

**Die Vorgabe aus dem September 2026, und sie steht über allem, was in
diesem Abschnitt folgt:** Die Regeln der Mappe werden **nicht eins zu
eins übernommen.** Im Lauf der Entwicklung wird sich zeigen, welche
tragen und wo es Abweichungen gibt — und das ist kein Mangel, sondern
der Zweck des Bauens.

**Drei Gründe, warum sie es gar nicht können:**

- **Es gibt jetzt eine Oberfläche.** [Datenhaltung](datenhaltung.md),
  Abschnitt 5, zählt die Klasse von Regeln auf, die nur existiert, weil
  die Rohdatei die Leseoberfläche ist — 74 Spalten, eine Fettstelle je
  Zeile, LF. Sie entfällt ersatzlos. Andere kehren sich um: Was das
  Skript *nicht prüfen kann und nur anmahnt*, kann ein Formular zeigen.
- **Es gibt mehrere Projekte.** Jede Regel, die stillschweigend von
  einem ausgeht, muss neu gelesen werden — der Bereich war der erste
  Fall (Abschnitt 2).
- **Es ist ein Produkt für Fremde.** Die Mappe ist ein Werkzeug, das
  jemand für sich selbst geschrieben hat und dessen Regeln er im Kopf
  hat. Ein Produkt hat diesen Vorteil nicht.

**Die Bedingung dazu, und sie ist die ganze Vorsicht:** Eine Abweichung
wird **notiert, nicht stillschweigend gemacht.** Sonst weiß in einem
Jahr niemand mehr, ob ein Unterschied eine Entscheidung war oder ein
Versehen. Es ist dieselbe Regel wie in [Übernahme](uebernahme.md),
Abschnitt 1, eine Ebene tiefer:
*Die Gleichheit braucht keinen Grund, die Abweichung schon.*

**Ein Vorteil kommt dabei von selbst:** Sobald das Produkt läuft, führt
es seine eigene Mappe. Jede Regel wird dann von dem geprüft, der sie
aufgestellt hat — im Gebrauch, nicht im Entwurf.

### Sammlung

Neun Felder, wie im Backlog:

```
Kategorie: IDEE|FEHLER  ·  Bereich  ·  Prio: MUSS|SOLL|KANN|—
Eingetragen am          ·  Abschluss: verworfen|aufgabe|—
Ursprung: wer, wann, woraus
```

Dazu **Beschreibung** und **Was beim Schärfen zu bedenken ist**. **Kein
Status**, und das ist begründet: *Es gäbe nur einen, und der hieße liegt
da.* Ein Bereich je Eintrag, keine Mehrfachauswahl — *bei
Mehrfachnennung sortiert die Achse nichts mehr.*

**Zwei Ansichten desselben Reiters** (entschieden am 06.09.2026):

| Ansicht | wofür |
|---|---|
| **Eintragen** | niedrige Hürde, drei Angaben, sonst Vorgaben |
| **Durchsicht** | Priorität vergeben, bündeln, verwerfen |

**Warum die Trennung nicht Bequemlichkeit ist:** Drei Regeln des Backlogs
laufen auf die Durchsicht zu, nicht auf das Eintragen. Die Priorität
steht auf `—`, *bis eine Durchsicht sie vergibt*; der Abschluss
entscheidet sich dort; und ein neuer Bereich *kommt bei einer Durchsicht
dazu, nicht beim Eintragen.* Eine einzige Ansicht müsste beides zugleich
anbieten — und stellte damit dem Eintragenden Felder hin, die er nicht
füllen soll.

**Das Zusammenlegen gehört in die Durchsicht.** Es ist laut Einordnung,
Abschnitt 7, die Kernfunktion des ganzen Produkts: *ein Knopf, der zwei
oder drei markierte Einträge zu einer Aufgabe macht und dabei nach dem
gemeinsamen Bild fragt.*

#### Die fünf Fehlerangaben mahnen, sie sperren nicht

Ein `FEHLER` verlangt fünf Angaben, die eine `IDEE` nicht braucht: wann
er auftritt · woran man ihn merkt · was man tun kann · **warum er jetzt
nicht behoben wird** · was eine Lösung grob kosten würde. Die vorletzte
trägt die Regel: *Was keinen Grund hat, gehört behoben und nicht
eingetragen.*

**Hier stoßen zwei eigene Regeln aneinander** — *die Hürde beim
Eintragen ist niedrig* gegen *fünf Angaben*. Die Einordnung warnt in
Abschnitt 8 davor, was dann passiert: Eine Regel, deren Weg teuer ist,
wird umgangen.

**Entschieden am 06.09.2026: sichtbar und benannt, aber nicht sperrend.**
Die fünf stehen als eigene Felder da statt als leerer Kasten — und ein
unvollständiger `FEHLER` wird ein **Befund**, kein abgewiesenes Formular.
Die Hürde bleibt niedrig, die Lücke verschwindet trotzdem nicht aus dem
Blick.

**Das ist der Gewinn der eigenen Oberfläche, an einem Beispiel.** In der
Mappe steht dazu im Quelltext: *„Das Skript kann sie nicht prüfen — es
erinnert nur daran, solange die Datei jung ist."* Aus einer Regel, die
sich selbst nicht durchsetzen konnte, wird Verhalten.

#### Abschluss setzen heißt: weg von hier

Der Eintrag wandert vollständig und im Wortlaut ins Archiv, also nach
History. **Ein Unterschied dabei geht leicht verloren:** `verworfen`
bekommt eine Zeile im Quittungsbuch, `aufgabe` nicht — *es ist nicht
fertig, es zieht um.*

### Aufgaben

Dreizehn Felder. Die Kopfzeile gleicht der der Sammlung, aber die
Kategorie fällt weg — *ob eine Beobachtung als Idee oder Fehler ins Haus
kam, ist beantwortet, sobald daraus Arbeit wird* — und der Status kommt
hinzu, *denn hier sitzt jemand dran*:

```
Bereich · Prio  ·  Status: PASSIV|AKTIV|PAUSE (mit Datum außer bei PASSIV)
Eingetragen am  ·  Abschluss: erledigt|verworfen|meilenstein|—
Ursprung: B-009 · B-043   (auch keines ist erlaubt)
```

Fünf eigene Abschnitte, dazu der Meilenstein: **Was dahintersteckt**
(Pflicht) · Was getan werden muss · Was bedacht werden muss · **Was ist
das Ergebnis** · **Wann es abgenommen ist**.

**`Eingetragen am` misst hier die Arbeitsdauer, in der Sammlung die
Liegedauer.** Dasselbe Feld, zwei Fragen — für die Befunde sind es zwei
verschiedene Auswertungen.

#### Die Abnahme sperrt

**Entschieden am 06.09.2026, und anders als bei den Fehlerangaben.** Ohne
Abnahme wird die Aufgabe nicht angelegt. Die Einordnung ist an dieser
Stelle ungewöhnlich hart:

> **Abnahme als Pflichtfeld**, als Liste zum Abhaken. Lässt sie sich
> nicht beschreiben, ist es keine Aufgabe.

**Der Unterschied zu den fünf Fehlerangaben ist kein Widerspruch,
sondern die Grenze zwischen zwei Arten von Pflichtfeld:** Die
Fehlerangaben machen einen Eintrag **vollständiger**. Die Abnahme macht
ihn erst zu dem, was er ist. *Eine Aufgabe ohne Abnahme ist keine
unvollständige Aufgabe, sondern eine Beobachtung mit Kopfzeile.*

**Zwei Bedingungen hängen daran, und ohne sie schadet die Sperre mehr,
als sie nützt:**

- **Es braucht den Ausgang, den die Regel selbst nennt: zurück in die
  Sammlung.** Ein Pflichtfeld ohne Fluchtweg erzeugt keine besseren
  Daten, sondern Füllsel — wer nicht weiterkommt und nicht zurückkann,
  tippt irgendetwas hinein. Das Formular muss also anbieten: *das
  schaffe ich nicht, zurück damit.* Genau das steht in der Regel — *dann
  gehört sie zurück in den Backlog* —, und es ist kein Scheitern,
  sondern der zweite gültige Ausgang.
- **Sie muss in dreißig Sekunden zu tippen sein.** Die Einordnung nennt
  in Abschnitt 8 selbst die Zahl, unter dem, was gegen ihr größtes
  Risiko hilft: *die Abnahme als Häkchenliste, die man in dreißig
  Sekunden tippt.*

**Damit bleibt die Bündelprobe erfüllbar**, und das ist die eigentliche
Prüfung dieser Entscheidung: *zwei Einträge, die dasselbe Problem sind,
in unter einer Minute zu einer Aufgabe.* Der Knopf fragt nach zweierlei
— dem gemeinsamen Bild und der Abnahme. **Er fragt danach in dem
Augenblick, in dem das Denken gerade stattgefunden hat**, und nicht
irgendwann später; das ist die einzige Gelegenheit, zu der beides billig
ist.

#### Was dahintersteckt mahnt

**Entschieden am 07.09.2026, und es ist die Gegenprobe zur Abnahme.**
Regel 5 nennt dieses Feld ebenfalls Pflicht — *die Ursache hinter den
Beobachtungen ist der eigentliche Zweck dieser Ebene* —, und trotzdem
sperrt es nicht.

**Was darin steht, zeigt der Fall aus der Einordnung.** Zwei Topics
lagen getrennt in der Sammlung: *ein Upload bricht ab, wenn man den
Reiter wechselt* und *einen laufenden Upload abbrechen können*. Was
dahintersteckt, wurde der Satz, **der in keinem von beiden stand**:
*Während einer Übertragung reden Browser und Server nicht darüber, ob
noch jemand darauf wartet.*

**Der zweite Satz der Regel wird leicht überlesen und sagt das
Wichtigste:** Die Ursache ist auch bei *einem* Topic Pflicht —
*Zusammenlegen ist der häufige Fall, nicht der einzige.* Damit steht
dort eine Aussage über das ganze Produkt: **Die Kernfunktion ist das
Zusammenlegen, der Kernwert ist die Ursache.** Das Bündeln ist die
Gelegenheit, bei der man sie am ehesten findet, nicht der Zweck.

**Drei Gründe, warum es trotzdem mahnt und nicht sperrt:**

- **Regel 4 nennt einen Ausgang, Regel 5 nicht.** Bei der Abnahme steht
  dabei: *dann gehört sie zurück in den Backlog.* Regel 5 sagt nur *ist
  Pflicht* und nennt keine Folge — und eine Sperre ohne Fluchtweg
  erzeugt Füllsel statt besserer Daten.
- **Die Einordnung zählt in Abschnitt 7 ihre Pflichtfelder auf**, und
  dieses ist nicht dabei; genannt wird allein die Abnahme.
- **Die Einordnung nennt selbst die Gegenmaßnahme, und es ist nicht
  „sperren".** In Abschnitt 8, unter dem, was gegen ihr größtes Risiko
  hilft: *Zwei Sätze müssen genügen, und das muss die Oberfläche zeigen.
  Vorschläge aus den Ursprungstexten, statt ein leeres Feld
  hinzustellen.*

**Zwei Anforderungen folgen daraus, und beide gehören ins Produkt, nicht
in die Anleitung:**

- **Der Zusammenlegen-Knopf füllt vor.** Er trägt die Beschreibungen der
  Ursprungs-Topics ein, aus denen man streicht und formuliert — statt
  vor einem leeren Kasten zu sitzen.
- **Ein leeres *dahinter* ist ein Befund**, kein stilles leeres Feld.
  Die Einordnung sagt, dass das Produkt genau daran scheitert: *Bleibt
  das Feld leer, ist es wieder eine Liste mit Extraschritten.*

**Die Regel von oben trägt das:** Ohne Abnahme weiß niemand, wann die
Aufgabe fertig ist, und das lässt sich später nicht rekonstruieren. Die
Ursache dagegen kann man nachtragen, sobald man sie versteht — *sperren
gehört zu dem, was nicht nachwachsen kann.*

#### Zwei Häkchenlisten, die Verschiedenes messen

| Liste | misst |
|---|---|
| *Was getan werden muss* | den **Fortschritt** — wie weit die Arbeit ist |
| *Wann es abgenommen ist* | die **Fertigkeit** — woran man sie feststellt |

**Nebeneinander sehen sie aus wie zweimal dasselbe, und das wäre der
Verlust.** Die Regel sagt scharf, warum es zwei sind: *Eine Häkchenliste
allein tut das nicht — sie misst, aber sie beschreibt nicht.* Stellt die
Oberfläche beide gleich dar, verschwindet der Unterschied und mit ihm
die Abnahme als eigenständige Sache.

#### Zwei Regeln, die in der Oberfläche entfallen

**`[erledigt]` wird ein Zustand.** *Was getan werden muss* ist Liste und
Stand zugleich: Erledigtes bekommt `[erledigt]` und ein Datum und wird
nicht gelöscht. In der Mappe ist das ein Textkniff, weil der Editor
Tilden nicht rendert. Hier ist es ein Zustand je Zeile — genau die
Umkehrung, die [Datenhaltung](datenhaltung.md) in Abschnitt 6
vorhersagt.

**Die Verweis-Regel entfällt ganz, und sie ist der stärkste Beleg der
ganzen Sammlung.** Regel 10 der Meilensteine verlangt, dass ein Verweis
Kennung **und** Bezeichnung nennt, abgeschrieben, wie sie am Ziel steht:
*Eine ausgedachte Bezeichnung ist schlimmer als gar keine — sie sieht
aus wie eine Auskunft und ist keine.* Wer umbenennt, zieht alle Verweise
nach, und dafür gibt es ein eigenes Skript, `pruefe-verweise.py`, 206
Zeilen, samt vier Ausnahmen, die es selbst erkennt.

**In einer Datenbank gibt es keine Kopie.** Ein Verweis ist eine
Kennung, die Bezeichnung wird beim Anzeigen geholt. Es entfallen: das
Abschreiben, das Nachziehen, das Prüfskript und vier der fünf Ausnahmen.
Übrig bleibt die fünfte — die Merkhilfe in Klammern, *das ist meine
Kurzform, nicht die Überschrift* —, und die ist der Freitext eines
Menschen und bleibt es.

Es ist zugleich das Mittel, das die Einordnung gegen ihr eigenes Risiko
nennt: *Verweisen statt abschreiben — die Begründung bleibt im Ursprung
stehen und wird nur genannt.*

### Meilensteine

Vierzehn Felder, minus eines (siehe unten). Die Kopfzeile ist
**mehrzeilig**, und das bleibt so:

```
Priorität · Eingetragen am · Abschluss: erledigt|verworfen|—
Vorgänger:  je einer in einer eigenen Zeile
Nachfolger: je einer in einer eigenen Zeile
```

**Die Begründung dafür wird mit übernommen, weil sie überall gilt:**
*Bevor jemand anfängt, will er wissen, wovon der Meilenstein abhängt und
wer auf ihn wartet; das ist die erste Frage, nicht eine am Ende von zwei
Bildschirmseiten.*

Sieben Abschnitte: Ursprung (`A-001 · A-003`) · Beschreibung ·
**Bedingung** (was sachlich da sein muss — nicht andere Meilensteine,
die stehen unter Vorgänger) · Aufgaben · Abnahme erfolgt ·
Nachbereitung · Was dazwischenkam.

#### Leer entstehen darf er, leer bleiben nicht

**Hier widersprechen sich zwei Regeln derselben Datei**, und beim Bauen
eines Formulars muss entschieden werden, welche gilt:

| | |
|---|---|
| Regel 1 | *Eine Aufgabe darf ohne Topic entstehen und **ein Meilenstein ohne Aufgabe**, aus einer Rückmeldung oder einer Entscheidung im Gespräch.* |
| Regel 11 | ***Ein Meilenstein ohne Aufgabe ist keiner**, sondern selbst eine Aufgabe.* |

**Entschieden am 06.09.2026: beides, nacheinander.** Kein Sperren beim
Anlegen — ein Meilenstein aus dem Gespräch ist ein echter Fall. Aber
**ein Befund, solange keine Aufgabe daranhängt.**

**Das trennt sauber von der Abnahme-Sperre bei der Aufgabe.** Dort fehlt
etwas, das den Eintrag *konstituiert* — eine Aufgabe ohne Abnahme wird
nie eine. Hier fehlt etwas, das **noch kommen kann**: Der Meilenstein
ist schon einer, er hat nur noch keine Arbeit unter sich. *Sperren
gehört zu dem, was nicht nachwachsen kann; mahnen zu dem, was nachwächst.*

#### Wer geprüft hat, fällt weg

**Abweichung von der Mappe, entschieden am 06.09.2026.** Das Feld
*Abnahme erfolgt* trägt dort dreierlei: solange offen das Kriterium,
danach das Datum **und wer geprüft hat.** Der dritte Teil fällt.

**Der Grund ist die Produktgrenze aus Abschnitt 4:** In der
Community-Fassung ist es immer dieselbe Person. Ein Feld, das auf jedem
Eintrag denselben Namen trägt, sagt nichts — es kostet nur eine Zeile im
Formular und eine Spalte in der Ablage.

**Es kommt in Pro wieder**, und zwar nicht zufällig: Die Einordnung
zählt unter dem, was mit der zweiten Person kommt, ausdrücklich *die
Frage, wer abnehmen darf* auf. **Das Feld ist keine Kleinigkeit, es ist
ein Stück der anderen Fassung** — und deshalb hier wegzulassen und
nicht mitzuschleppen.

#### Die Abnahme sind drei Handgriffe und wird ein Knopf

Heute: `Abschluss: erledigt` setzen, `archiviere.py --verschieben`
laufen lassen, eine Zeile ins Quittungsbuch schreiben, einen Stein auf
die Roadmap setzen — mit Dauer und *Was dazwischenkam*. Jeder Handgriff
beantwortet eine andere Frage (*was stand drin · was ist wann fertig ·
wie sind wir hierhergekommen*), und jeder lässt sich einzeln vergessen.

**Genau das meint [Datenhaltung](datenhaltung.md), Abschnitt 3:** *Wo
eine Regel Formalie verlangt, muss das Werkzeug sie übernehmen. Sonst
wird die Regel umgangen.*

#### Der Umweg muss von überall erreichbar sein

*Was dazwischenkam* ist ein kleines Register im Meilenstein. Dazu die
entscheidende Zeile der Regel: **„Wird notiert, sobald es passiert, nicht
bei der Abnahme."**

> **Nachgetragen am 07.09.2026: Es gibt nur noch den Umweg.** Die Mappe
> kennt zwei Arten — *Umweg* für einen Weg, der nicht ging, *Rast* für
> eine Wartezeit. Die Unterscheidung war zu fließend, um zu tragen: Wann
> ein Warten eine Rast ist und wann ein Umweg, war an jedem einzelnen
> Fall zu entscheiden; **zwei Etiketten, die sich nicht auseinanderhalten
> lassen, sortieren nichts.**
>
> Damit fällt auch die Spalte `art`: Ein `CHECK`, das immer denselben
> Wert erlaubt, ist eine Spalte, die auf jeder Zeile dasselbe sagt.
> `meilenstein_dazwischen` trägt jetzt `id · meilenstein_id · datum ·
> text`, und die Karte zeigt eine schlichte Liste ohne Abzeichen.
>
> **In MARLEI Boot bleibt beides, wie es ist** — dort gilt die Regel
> weiter, samt der einen echten Rast an M-001. Das ist eine
> ausdrückliche Entscheidung und die erste Stelle, an der die beiden
> Produkte in einer Regel auseinandergehen.

**Das ist dieselbe Falle wie bei der harten Regel.** Eine Notiz, die man
im Augenblick machen soll, aber nur an einer Stelle tief in einem
Meilenstein machen kann, wird nicht gemacht — sie wird bei der Abnahme
aus dem Gedächtnis nachgetragen, und dann ist sie wertlos. **Der Umweg
braucht denselben kurzen Weg wie das Eintragen in der Sammlung.**

> **Entschieden am 07.09.2026: vorerst nur über den Reiter
> Meilensteine.** Dort steht eine eigene Karte mit drei Feldern — Stein,
> Datum, ein Satz. *„Von überall"* heißt damit: von jeder Seite in zwei
> Klicks, weil die Reiterleiste oben klebt. **Kein seitenweites Element
> im Rahmen**, wie es die Befunde eines sind.
>
> **Der naheliegendere Weg ist erwogen und aufgeschoben, nicht
> verworfen:** ein Feld in der Aufgabenkarte, weil ein Umweg dort
> auffällt, wo gearbeitet wird — die Notiz ginge an den Meilenstein, dem
> die Aufgabe zugeschlagen ist.
>
> **Er hängt an einer Regel, die es noch nicht gibt.** Solange eine
> Aufgabe *keinem* Meilenstein zugeordnet sein muss, gibt es im Regelfall
> keinen Stein, dem die Notiz gehört. Der Vorschlag wäre erst dann
> passend, wenn festgelegt ist, dass eine Aufgabe einem Meilenstein
> zugeordnet sein MUSS. **Damit ist die Bedingung benannt, unter der
> diese Entscheidung wieder aufgeht** — und nicht nur ein Vorbehalt.
>
> *Dass an den Regeln in der Entwicklungs- und Testphase ohnehin noch
> nachgeschärft wird, ist dabei ausdrücklich mitgedacht.*

#### Regel 7 kehrt sich um

*Ist er abgenommen, verschwindet er ganz aus dieser Datei — eine Liste,
die mitwächst statt zu schrumpfen, verliert ihren Zweck.* In einer
Datenbank verschwindet nichts. **Der Zweck bleibt und wird ein
Vorgabefilter:** Die Liste zeigt, was offen ist. Dritte Regel, die sich
in der Oberfläche dreht.

### Entscheidungen

**Kein Feldschema** — als einziges der vier Register. Die Mappe begründet
das so: *Eine Abwägung hat keine Form, die sich vorher festlegen ließe;
sie hat einen Verlauf.* In der Ablage bleiben damit vier Angaben und ein
langer Text:

```
Kennung: E-  ·  Zustand  ·  Datum
Bezug: B-016 | A-020 | M-006 | —        (freistehend ist erlaubt)
Titel
Text — der Verlauf, ohne Gliederungsvorgabe
```

#### Der auslösende Grund entfällt, die Trennung bleibt

**Das Register entstand aus einem Größenproblem.** *Diese Datei gibt es,
weil der Backlog an einem einzigen Eintrag zu ersticken drohte. Am
30.08.2026 stand B-016 dort mit **1917 von 3334 Zeilen** — mehr als die
Hälfte der Datei für eine Frage, die technisch in drei Sätzen
beschrieben ist.*

**In einer Datenbank erstickt nichts.** Ein langes Textfeld verdrängt
nichts, es ist einfach lang. Der auslösende Grund ist damit weg — und
das gehört hierher, sonst hebt beim nächsten Lesen jemand die Trennung
auf. **Sie bleibt richtig, aber aus zwei anderen Gründen:**

| | |
|---|---|
| **Arbeitsteilung** | Sammlung: *das Technische* — was zu tun ist, woran man merkt, dass es fertig ist. Hier: *das Formelle* — was abgewogen wurde, was dagegen sprach, welche Regel daraus folgt |
| **Lebensdauer** | Der Eintrag zieht ins Archiv, **die Entscheidung bleibt stehen.** Sie überlebt das, wozu sie gehört — das tut kein anderes Register |

#### Der Name bleibt, und zwar mit einem besseren Grund

**Die Mappe hält ihren eigenen Namen für ungenau** und behält ihn aus
Bequemlichkeit: *Ein Name wie „Abwägungen" träfe das genauer. Er ist es
trotzdem nicht geworden: Der Dateiname ist das, was man tippt und sucht.*
Dieses Argument gibt es hier nicht — **ein Reiter wird angeklickt, nicht
getippt.**

**Er heißt trotzdem Entscheidungen, und der Grund ist ein anderer**
(festgehalten im September 2026): Wenn eine Entscheidung heute nicht
fällt, heißt das nicht, dass gar keine getroffen wird. Am Ende wurde
Exmig genommen und die Suite heißt MARLEI. **Was offen aussieht,
ist unterwegs, und das Ziel gibt dem Register den Namen** — *Abwägung*
benennt den Vorgang, *Entscheidung* das, wozu er da ist.

> **Am Ende muss jemand entscheiden.**

**Daraus folgt, was in den Text gehört, und es ist mehr als das
Ergebnis:** auch der **Weg** dorthin und die **Vorbereitung**. Die
Begründung dafür ist der eigentliche Fund dieses Abschnitts: Der Weg
spiegelt wider, wie gründlich eine Entscheidung war.

**Damit hat das fehlende Feldschema einen zweiten Grund.** Die Mappe
sagt, eine Abwägung habe keine Form. Hier kommt hinzu: **Ein Schema
würde genau das plätten, woran man die Gründlichkeit abliest.** Achtzig
geprüfte Wörter, drei Kandidaten und zwei verworfene Wege sehen in
Feldern gepresst aus wie eine Zeile.

#### Zustand: getroffen oder nicht getroffen

**Zwei Werte: `OFFEN` und `ENTSCHLUSS`**, festgelegt am 07.09.2026.

**`OFFEN` heißt nicht „da steht noch nichts".** Es heißt: Der Weg ist
da, die Abwägung läuft, und der Entschluss steht aus. Genau das ist der
Fall, den die Mappe an B-016 beschreibt — achtzig geprüfte Wörter, drei
Kandidaten, **keine Entscheidung**. Ein Register, das nur Fertiges
kennte, hätte diesen Eintrag nicht tragen können.

**Das Feld ist nicht nur beschreibend, es speist einen Befund:**
**Getroffen, und der Eintrag liegt trotzdem** — das ist wörtlich die
Liegeprobe aus der Einordnung: *was entschieden wurde und trotzdem
liegt.*

> **Hier stand bis zum 07.09.2026 ein zweiter.** *Offen und liegt lange*
> — eine Entscheidung, auf die etwas wartet. **Er wurde gestrichen**, und
> die Begründung trägt weiter als der Befund:
>
> *Der Befund ist offen, und das ist bewusst so gewählt — dann ist es
> egal, wie lange er offen ist.*
>
> **Das ist dieselbe Aussage wie im Absatz darüber, zu Ende gedacht:**
> `OFFEN` heißt nicht *da steht noch nichts*, sondern *der Weg ist da,
> der Entschluss steht aus.* Wer das als Zustand wählt, hat gewählt —
> ihn nach vier Wochen daran zu erinnern, hieße, seine Entscheidung für
> ein Versäumnis zu halten. **Gemahnt wird, was fehlt, nicht was
> absichtlich so dasteht.**
>
> Gebaut war er ohnehin nie; die sechs Befunde (Abschnitt 15) kennen ihn
> nicht. Notiert steht er trotzdem, denn er stand hier — *eine
> Abweichung wird notiert, nicht stillschweigend gemacht.*

**Zwei Zustände, zwei Fragen** — dieselbe Bauart wie beim
Eintragsdatum, das in der Sammlung die Liegedauer und an der Aufgabe die
Arbeitsdauer misst.

#### Was hier nicht hingehört, ist der Stand

*Was gerade gilt, steht im Backlog — sonst muss man zwei Stellen pflegen,
und eine ist in einem Monat falsch. Hier steht, warum es gilt.*

**Erzwingen lässt sich das nicht, erleichtern schon:** Steht der Kopf des
bezogenen Eintrags neben der Entscheidung, gibt es keinen Anlass, ihn
abzuschreiben. Es ist derselbe Griff wie bei der Verweis-Regel — zeigen
statt kopieren.

---

## 4. Die Datenbank: SQLite

**Entschieden am 06.09.2026.** [Datenhaltung](datenhaltung.md) hatte die
Form festgelegt — *Datenbank als Ablage, Oberfläche als Ansicht* — und
die Wahl ausdrücklich offengelassen. Sie fällt auf **SQLite**.

**Sie kommt nicht hinzu, sie ist schon da.** Boot benutzt sie: `PXE_DB`
ist eine SQLite-Datei, `app.py` legt die Tabellen mit `CREATE TABLE IF
NOT EXISTS` an und zieht später dazugekommene Spalten beim Start per
`ALTER TABLE` nach — ein benanntes Verzeichnis `NACHZÜGLER` sagt, welche.
**Das Verfahren kommt mit, nicht nur die Wahl.** Und weil `sqlite3` in
Pythons Standardbibliothek steht, bleibt die `requirements.txt` bei fünf
Zeilen: [Übernahme](uebernahme.md), Abschnitt 2, sagte, hinzu komme die
Datenbank — es kommt nichts
hinzu.

**Ein Datenbankdienst liefe gegen die eigene Betriebsvorgabe.** Ein
Postgres hieße: ein zweiter Dienst auf der Maschine, ein Benutzer, ein
Kennwort in der Env-Datei, `pg_dump` als eigener Sicherungsweg und eine
Version, die zur Distribution passen muss. Für einen Betrieb mit wenigen
Stunden IT im Monat ist jeder Dienst eine Last — und zwei Produkte, die
je einen mitbringen, sind genau die Kopplung, die
[Übernahme](uebernahme.md), Abschnitt 8, ausschließt.

Vier Vorgaben fallen damit von selbst richtig:

| Vorgabe | Wie SQLite sie erfüllt |
|---|---|
| Kennungen nie wiederverwenden ([Datenhaltung](datenhaltung.md), Abschnitt 4) | `INTEGER PRIMARY KEY AUTOINCREMENT`. **Ohne das Schlüsselwort vergibt SQLite eine gelöschte Höchstnummer neu** — es ist hier keine Stilfrage, sondern die Anforderung |
| eine Zählung je Art über alle Projekte (Abschnitt 2) | drei Tabellen, jede mit eigener Folge |
| *noch nicht entschieden* ist kein leeres Feld (Abschnitt 6 dort) | `NOT NULL DEFAULT '—'`; Boots Schema arbeitet schon so, nur der Vorgabewert unterscheidet sich |
| die Bündelprobe | **FTS5 ist eingebaut** (am 06.09.2026 geprüft). Die Einordnung sagt, die Verbindung zweier Einträge werde *nicht durch die Titel* gefunden, sondern beim Lesen der Beschreibungen — genau dafür |

**Eine Einstellung ist Pflicht und keine Kür: `journal_mode=WAL`.** Boot
hat Hintergrundwächter, die schreiben, während jemand eine Seite lädt;
ohne WAL sperren die sich gegenseitig aus. Das gehört in die Verbindung,
nicht in die Dokumentation.

**Der Umfang spricht nicht dagegen, er ist lächerlich klein:** Die echte
Mappe misst 599 KB. Hundert Projekte dieser Größe wären 60 MB.

### Die Grenze zwischen Community und Pro

**SQLites Schwäche ist der zweite gleichzeitige Schreiber — und genau
dort verläuft die Produktlinie.** So entschieden im September 2026.

Eine SQLite-Datei trägt beliebig viele Leser, aber **einen Schreiber zur
Zeit**; wer gleichzeitig schreiben will, wartet oder bekommt eine
Absage. Bei einem Menschen fällt das nie auf — er tippt nicht an zwei
Stellen zugleich. Bei mehreren fällt es sofort auf, und es lässt sich
nicht wegkonfigurieren: Es ist die Bauart der Ablage.

**Die Einordnung hat diese Grenze längst beschrieben, ohne sie zu
benennen.** In Abschnitt 4, über das, was mit der zweiten Person käme:

> Datenhaltung mit Sperren. Textdateien und drei Skripte tragen einen
> Menschen; bei mehreren braucht es eine Datenbank oder ein Verfahren,
> das Konflikte auflöst.

Daraus die Linie:

```
MARLEI Tasks Community    SQLite, eine Datei, ein Mensch
MARLEI Tasks Pro          ein Datenbankdienst, mehrere Menschen
```

**Die Grenze ist nicht „Datenbank oder keine".** Auch die freie Fassung
hat eine — SQLite *ist* eine. Getrennt wird nach dem gleichzeitigen
Schreiber, und mit ihm kommt alles, was die Einordnung an derselben
Stelle aufzählt: Anmeldung, Rechte, die Frage wer abnehmen darf,
Benachrichtigung. **Das ist kein abgeschaltetes Merkmal, sondern ein
anderer Anwendungsfall.**

**Und das ist die ehrliche Fassung von Open Core, an der die Linie zu
halten ist:** Die freie Fassung ist für ihren Fall **vollständig**. Wer
allein arbeitet, vermisst nichts — er bekommt nicht eine beschnittene
Version, sondern die ganze. Sobald der Community-Fassung etwas fehlt,
das ihr nur fehlt, damit Pro es verkaufen kann, ist die Linie verletzt
und das Vertrauen mit ihr.

**Die Lizenzentscheidung hat darauf schon vorgebaut**, ein Jahr bevor es
konkret wurde: AGPL-3.0 wurde am 27.08.2026 gewählt, *weil* Open Core
die Richtung ist — unter MIT dürfte jeder eine geschlossene Fassung
danebenstellen. Und die CLA-Pflicht vom 29.08.2026 ist die Bedingung
dafür: **Eine kommerzielle Doppellizenz kann nur vergeben, wer alle
Rechte hält.** Diese Grenze ist der erste konkrete Fall dieses Plans.

**Eine Anforderung an den Bau folgt daraus, und sie ist heute billig:**
Der Zugriff auf die Ablage gehört an **eine** Stelle. Läuft Pro dieselbe
Anwendung mit einem anderen Speicher, ist verstreutes SQL in zwanzig
Modulen der Preis — heute ist es eine Datei, später ein Umbau.

---

## 5. Was hiermit entschieden ist

- **Neun Reiter**, und ihre Reihenfolge folgt Boots Prinzip statt Boots
  Positionen — Abschnitt 1. **Die Startseite unter `/` ist der Reiter
  Projekte**, nicht Server Health.
- **Fünf Reiter kommen neu dazu:** Projekte, Sammlung, Aufgaben,
  Meilensteine, Entscheidungen. Die vier hinteren sind die Ebenen aus
  der Einordnung, an der echten Mappe belegt.
- **Das Produkt trägt mehrere Projekte**, und die Auswahl auf dem
  ersten Reiter baut die vier folgenden auf. **Mehrere Projekte sind
  dabei nicht mehrere Menschen** — Abschnitt 2.
- **Ein Projekt trägt sechs Felder:** Kennung `P-`, Name, Beschreibung,
  Vision, Zustand (`AKTIV`/`RUHT`/`ABGESCHLOSSEN`) und Eintragsdatum —
  dazu die Liste der Bereiche, die je Projekt eine andere ist.
- **Die Vision ist ein Feld der Projektbeschreibung**, kein Reiter.
- **Das gewählte Projekt steht im Kopfband**, weil es auf jeder Seite
  gilt.
- **Befunde gelten über alle Projekte hinweg** und nennen das
  betroffene — die einzige Stelle, an der die Vorauswahl nicht gilt.
- **Kennungen zählen über alle Projekte**, eine Zählung je Art. `B-066`
  gehört einem Eintrag, für immer; dass die Nummern eines Projekts
  dabei springen, ist der Preis und kein Fehler.
- **Die Werkseinstellung leert nur das gewählte Projekt** — und ihr
  Losungswort ist dessen Name, nicht ein festes Wort. **Gelöscht** wird
  ein Projekt auf dem Reiter Projekte, mit denselben zwei Sicherungen.
- **Die Entscheidungszustände heißen `OFFEN` und `ENTSCHLUSS`.**
- **Die Liegeprobe wird ein Befund, kein Reiter.**
- **Die Regeln der Mappe werden nicht eins zu eins übernommen** — aber
  jede Abweichung wird notiert, nicht stillschweigend gemacht.
- **Die Sammlung hat zwei Ansichten:** Eintragen und Durchsicht. Die
  fünf Fehlerangaben mahnen, sie sperren nicht.
- **Die Abnahme einer Aufgabe sperrt** — ohne sie ist es keine Aufgabe.
  Dazu gehören zwingend der Ausgang *zurück in die Sammlung* und eine
  Form, die in dreißig Sekunden auszufüllen ist.
- **„Was dahintersteckt" mahnt, es sperrt nicht** — die Ursache kann
  man nachtragen. Dafür füllt der Zusammenlegen-Knopf vor, und ein
  leeres Feld wird ein Befund.
- **Ein Meilenstein darf leer entstehen, aber nicht leer bleiben** —
  kein Sperren, ein Befund. *Sperren gehört zu dem, was nicht
  nachwachsen kann; mahnen zu dem, was nachwächst.*
- **„Wer geprüft hat" fällt weg** — in der Community-Fassung immer
  dieselbe Person; das Feld gehört zu Pro.
- **Eine Entscheidung bekommt eine eigene Kennung `E-`** und einen
  Bezug, der leer bleiben darf. Kein Feldschema — der Verlauf ist der
  Inhalt.
- **Der Reiter heißt Entscheidungen**, obwohl auch Unentschiedenes darin
  steht: *Am Ende muss jemand entscheiden.* Festgehalten wird auch der
  Weg dorthin, **weil er zeigt, wie gründlich entschieden wurde.**
- **Eine Entscheidung ist getroffen oder nicht** — zwei Zustände, und
  sie speisen zwei verschiedene Befunde.
- **Die Ablage ist SQLite**, und **die Grenze zwischen Community und Pro
  ist der gleichzeitige Schreiber** — Abschnitt 4.

**Alle neun Reiter sind durchgegangen** — die vier übernommenen Karte
für Karte in [Übernahme](uebernahme.md), die fünf neuen hier Feld für
Feld.

**Damit ist am Entwurf nichts mehr offen.** Was ab hier entschieden
wird, entscheidet sich beim Bauen — und gehört dann in das
Entscheidungsregister dieses Produkts. Das ist keine Floskel mehr: Der
Reiter, der es trägt, ist beschrieben, und seine Tabelle steht.

---

## 6. Was beim Bauen dazukam — Reiter Projekte

*Am 07.09.2026 gebaut. Abschnitt 5 sagt: **Was ab hier entschieden wird,
entscheidet sich beim Bauen.** Hier steht, was das war — und wo der
gebaute Reiter vom Entwurf abweicht. Nichts davon ist stillschweigend
passiert; das ist der ganze Zweck dieses Abschnitts.*

### Drei Karten, und die Übersicht ist eine eigene

Abschnitt 2 sagt, der Reiter tue zweierlei: *er listet alle Projekte und
beschreibt das gewählte.* Gebaut sind daraus **drei Karten**, und die
Reihenfolge folgt demselben Prinzip wie die Reiterleiste — Häufigkeit im
Betrieb, nicht Ablauf beim Aufsetzen:

| Karte | wofür |
|---|---|
| **Projektübersicht** | listet alle und trägt den einen Knopf, wegen dem jemand diesen Reiter aufmacht: *wählen* |
| **Projekte** | eine Eintragskarte je Projekt, mit allen Feldern und dem Löschweg |
| **Neues Projekt** | das Formular zum Anlegen |

**Vorgabe aus dem September 2026**, nach einem Blick auf den Entwurf ohne
die Übersicht. Der Gewinn ist nicht die Liste — die stand vorher auch
da —, sondern dass **Wählen und Beschreiben nicht mehr
dieselbe Karte teilen.** Wer wechseln will, liest drei Zeilen; wer etwas
ändern will, klappt eine Karte auf.

**Zwei Folgen, und beide sind Regeln:**

- **Gewählt wird nur in der Übersicht.** In den Eintragskarten steht kein
  zweiter Wählen-Knopf. *Zwei Wege zu demselben Schritt lehren, dass es
  zwei Schritte sind.*
- **Beschrieben wird nicht nur das gewählte, sondern jedes** — nur steht
  die Karte des gewählten offen und alle anderen zu. Ein Projekt
  umbenennen zu können, ohne es vorher zu wählen, ist das Natürlichere;
  und eine Liste, in der die Hälfte der Karten aufgeklappt ist, hat keine
  geschlossene mehr.

### Der Bestand ist dazugekommen — als Fußzeile, nicht als Feld

Ein Projekt trägt nach Abschnitt 2 fünf Felder und eine Liste. **Dazu
steht jetzt in der Fußzeile jeder Eintragskarte, was im Projekt liegt** —
*65 Sammlung · 7 Aufgaben · 3 Meilensteine · 41 Entscheidungen.*

**Er ist kein siebtes Feld, und deshalb steht er unten.** Die Fußzeile ist
der Teil, der über den Inhalt spricht, statt ihn zu sein
(`docs/gestaltung.md`); der Bestand ist abgelesen und nicht eingetragen.
Ohne ihn wäre eine Projektkarte eine Beschreibung ohne Größe — und
**beim Löschen sagt dieselbe Zahl, was verloren geht.**

*Erst als Angabe entworfen, dann auf Vorgabe in die Fußzeile gewandert.*

### Was der Satz beim ersten Blick verriet

Der Löschschritt sagte *„mit ihm gehen 0 Einträge der Sammlung, 0
Aufgaben"* — bei einem leeren Projekt vier Nullen in einem Satz, bei
einer Aufgabe *„1 Aufgaben"*. Beides ist an der gebauten Seite
aufgefallen und nicht in einem Test: **Die Testreihe misst, ob gezählt
wird, nicht ob der Satz stimmt.** Jetzt zählt der Schritt in Einzahl, wo
einer liegt, und sagt bei einem leeren Projekt einen Satz statt vier
Nullen. Zwei Prüfungen sind dazugekommen, damit es so bleibt.

### Was gesperrt ist und was mahnt

**Ein Bereich, an dem Einträge hängen, lässt sich nicht entfernen.** Er
sperrt, er mahnt nicht — und das folgt der Regel aus Abschnitt 3: *Sperren
gehört zu dem, was nicht nachwachsen kann.* Der Bereich eines Eintrags
steht in keiner zweiten Spalte, aus der er sich wiederherstellen ließe,
und ein Eintrag ohne Bereich wäre in jeder Durchsicht unauffindbar. Die
Meldung nennt die Zahl der Einträge, die daran stehen.

### Ein Punkt bleibt offen, und er steht auf der Seite

**Der Export vor dem Löschen fehlt.** Abschnitt 2 nennt ihn als eine der
beiden Sicherungen — *der Export fängt den Fehler ab, es überhaupt getan
zu haben.* Er gehört auf den Reiter Einrichtung, und der ist leer.

Gebaut ist deshalb nur die zweite Sicherung, der Projektname als
Losungswort. **Und der Löschschritt sagt ausdrücklich, dass es die erste
noch nicht gibt** — mit dem Hinweis, dass bis dahin nur eine Kopie der
Datei `tasks.db` hilft. Ein Verweis, der ins Leere zeigt, wäre schlimmer
als der Satz; ihn wegzulassen wäre am schlimmsten.

*Beim Bau von Einrichtung ist dieser Satz zu ersetzen, nicht zu
vergessen.*

### Kleinigkeiten, die trotzdem Entscheidungen sind

- **Die Projektliste ist nach der Kennung sortiert, nicht nach dem
  Namen.** Nach Namen sortiert spränge die Liste, sobald jemand ein
  Projekt umbenennt — und die Stelle, an der man sein Projekt sucht, wäre
  jedes Mal eine andere.
- **Die Bereiche stehen alphabetisch**, nicht in der Reihenfolge des
  Eintragens. Sie sind eine Menge, keine Folge.
- **Wer ein Projekt anlegt, hat es danach gewählt.** Ein zweiter Klick
  für eine Absicht, die schon feststand, ist keiner.
- **Wer das Projekt wechselt, während ungespeicherte Felder dastehen,
  wird gefragt.** Wählen ist ein eigenes Formular und schickt die Felder
  am Seitenformular nicht mit; ohne die Frage wäre die Arbeit weg, und
  niemand hätte es gemerkt.
- **Das Datum liegt nach ISO in der Ablage und steht deutsch in der
  Ansicht** — die Begründung steht in [Datenhaltung](datenhaltung.md) am
  Ende.

---

## 7. Was beim Bauen dazukam — Reiter Sammlung

*Am 07.09.2026 gebaut, nach einer Vorschau, deren vier offene Punkte am
selben Tag alle bestätigt wurden: die Platzierung des Umschalters,
Eintragen als Startansicht, das Eintragsdatum mit Vorgabe, und die Karte
`Was am längsten liegt`.*

### Der Umschalter steht über den Karten

**Und das ist eine Stelle, die es in diesem Haus noch nicht gab.** Boots
`a.knopf` / `a.knopf.gewaehlt` gibt es schon — der UEFI/BIOS-Schalter
unter *Vorschau* —, aber dort steht er **in** einer Karte und stellt nur
sie um. Hier gilt er für die ganze Seite und sitzt deshalb zwischen
Reiterleiste und erster Karte.

**Kein eigenes Aussehen.** Wer den Schalter aus Boot kennt, erkennt ihn
wieder; nur sein Geltungsbereich ist größer.

### Die drei neuen Zahlen und die Spalte, die sie speist

**`abschluss_am` an einem Eintrag der Sammlung** und **`durchsicht_am` an
einem Projekt** sind über `NACHZUEGLER` nachgezogen worden — den
Mechanismus gab es, benutzt war er noch nie.

- **Ohne `abschluss_am` kann das Quittungsbuch keine Zeile schreiben.** Es
  hält fest, *was wann* fertig wurde; das *wann* stand nirgends.
- **Ohne `durchsicht_am` gibt es die Zahl *seit der letzten Durchsicht*
  nicht.** Eine vergebene Priorität hinterlässt kein Datum, und aus dem
  Bestand ist nicht abzulesen, wann jemand hingesehen und **nichts** getan
  hat. Genau das muss die Zahl aber messen: **Vermerkt wird das Hinsehen,
  nicht das Ändern** — deshalb schreibt auch ein *Speichern* ohne
  Änderung den Vermerk.

### Was gesperrt ist und was mahnt — der zweite Fall

**Die fünf Fehlerangaben sperren nicht.** Ein unvollständiger `FEHLER`
wird angelegt, bekommt ein Abzeichen *„3 Angaben fehlen"* und drei Felder
zum Nachtragen an Ort und Stelle. Die Meldung nach dem Eintragen sagt es
ebenfalls. Das ist die Regel aus Abschnitt 3, gebaut: *Eine Regel, deren
Weg teuer ist, wird umgangen.*

**Der Bereich sperrt dagegen** — ohne ihn geht kein Eintrag durch. Er ist
`NOT NULL`, und das ist keine Formalie: Er ist die Achse, nach der später
sortiert wird. Damit das nicht erst im abgewiesenen Formular auffällt,
sagt die Seite vorher, wenn das Projekt noch keinen hat.

### Zusammenlegen fragt, bevor es anlegt

**Zwei Schritte, und der erste ist eine Frage.** Der Knopf in der
Tabellenkopfzeile führt in einen Bündelschritt, der die markierten
Einträge auflistet und nach dem gemeinsamen Bild fragt. Ein Knopf, der
stillschweigend anlegte, wäre nicht die Kernfunktion, sondern eine
Abkürzung an ihr vorbei.

- **Die Aufgabe erbt die stärkste Priorität der Einzelnen.** Wer drei
  Einträge bündelt, von denen einer `MUSS` ist, hat eine
  `MUSS`-Aufgabe — die schwächste zu nehmen ließe die Dringlichkeit im
  Bündeln verschwinden.
- **Der Bereich ist der des ersten.** Ein Bündel über zwei Bereiche
  hinweg gibt es; dann ist die Wahl eine Setzung und an der Aufgabe
  änderbar.
- **`Was dahintersteckt` ist vorbelegt und keine Pflicht** — aus Kennung,
  Titel und Beschreibung der Einträge. Genau so steht es in Abschnitt 5:
  *Dafür füllt der Zusammenlegen-Knopf vor, und ein leeres Feld wird ein
  Befund.*
- **`→ Aufgabe` in der Zeile tut dasselbe mit einem einzigen** und geht
  durch denselben Schritt.

### Ein Punkt bleibt offen, und er steht in der Meldung

**Der Reiter Aufgaben ist leer.** Die Aufgabe entsteht wirklich — Zeile,
Herkunft, Priorität, alles steht in der Ablage —, aber ansehen kann man
sie nirgends. Die Meldung sagt das im Wortlaut: *„A-001 angelegt aus 2
Einträgen — zu sehen unter Aufgaben, sobald es den Reiter gibt."*

Das ist dieselbe Entscheidung wie beim fehlenden Export unter Projekte:
**Ein Verweis, der ins Leere zeigt, wäre schlimmer als der Satz; ihn
wegzulassen wäre am schlimmsten.** *Beim Bau von Aufgaben ist dieser Satz
zu ersetzen, nicht zu vergessen.*

### Ein Fehler, den erst diese Seite ans Licht gebracht hat

**`_meldung()` hängte immer ein `?` an.** Bei den Projekten fiel das nie
auf, weil deren Ziele keine Frage tragen. Die Sammlung hat welche —
`?ansicht=durchsicht` —, und daraus wurde `durchsicht?meldung=…`: **Die
Ansicht fiel auf Eintragen zurück und die Meldung erschien nie.** Jetzt
entscheidet ein Blick auf das Ziel, ob `?` oder `&` davor gehört; eine
Prüfung hält es fest.

### Kleinigkeiten, die trotzdem Entscheidungen sind

- **Die Sammlung steht mit dem Jüngsten oben.** Wer etwas einträgt, will
  es danach sehen; wer durchsieht, sortiert ohnehin über *liegt seit*.
- **Die Suche geht über Titel *und* Beschreibung** und benutzt FTS5 mit
  Präfix — sie findet schon beim Tippen. Fehlt FTS5 auf der Maschine,
  fällt sie auf `LIKE` zurück: schlechter, aber nicht weg.
- **Der Titel ist in der Eintragskarte kein Eingabefeld**, anders als der
  Projektname. Ein Titel der Sammlung wird beim Schärfen geändert, nicht
  im Vorbeigehen.
- **Die fünf Angaben stehen nur an einem `FEHLER`.** An einer `IDEE`
  wären fünf leere Zeilen kein Hinweis, sondern Lärm. Was dasteht, steht
  als Text; was fehlt, als Feld.
- **`Speichern` über den Prioritäten bleibt bedienbar, wenn nichts
  geändert ist** — anders als unter Projekte und unter Systeme in Boot.
  Er vermerkt zugleich die Durchsicht, und ausgegraut hieße hier nicht
  *nichts zu tun*, sondern *das Hinsehen zählt nicht*.
- **`0 Tage` heißt `heute`.** Eine Zahl, die stimmt, und ein Satz, den
  niemand sagt — aufgefallen beim ersten Blick auf die gebaute Seite. Ein
  Strich heißt dagegen *nie* und nicht *null*.

---

## 8. Was beim Bauen dazukam — Reiter Aufgaben

*Am 07.09.2026 gebaut, samt der Nacharbeit an der Sammlung, die dazu
gehört.*

### Der Bündelschritt fragte nur die Hälfte

**Die Sammlung war einen Tag lang falsch gebaut, und der Entwurf sagt
es.** Abschnitt 3 verlangt: *Der Knopf fragt nach zweierlei — dem
gemeinsamen Bild und der Abnahme. Er fragt danach in dem Augenblick, in
dem das Denken gerade stattgefunden hat.* Gebaut war nur das erste.

Damit legte *Zusammenlegen* Aufgaben ohne Abnahme an — also genau das,
was nach derselben Regel keine Aufgabe ist. **Aufgefallen ist es nicht
beim Bauen der Sammlung, sondern beim Entwerfen von Aufgaben**, wo die
Sperre zum ersten Mal beschrieben wurde.

Der Schritt fragt jetzt nach beidem und trägt daneben den zweiten
Ausgang: **„Das schaffe ich nicht — zurück in die Sammlung."**

### Der zweite Ausgang ist ein Knopf, kein Abbrechen-Link

**Er sieht aus wie ein umrandeter Knopf und nicht wie das graue
*Abbrechen*, das er ersetzt hat.** Der Grund steht in Abschnitt 3: *Es
ist kein Scheitern, sondern der zweite gültige Ausgang.* Ein Link in Grau
läse sich als Rückzieher — und ohne diesen Weg schadet die Sperre mehr,
als sie nützt: *Wer nicht weiterkommt und nicht zurückkann, tippt
irgendetwas hinein.*

### Beide Listen sind ein Textfeld, eine Zeile je Punkt

**Auch das folgt einer Zahl, nicht einem Geschmack.** Die Einordnung
nennt sie selbst: *die Abnahme als Häkchenliste, die man in dreißig
Sekunden tippt.* Fünf Felder mit einem Hinzufügen-Knopf wären dieselbe
Liste und dreimal so lang — und eine Regel, deren Weg teuer ist, wird
umgangen. `datenbank.zeilen()` macht aus dem Feld die Punkte;
Leerzeilen fallen weg, weil niemand einen leeren Punkt meint.

**In der Karte wachsen beide Listen dann zeilenweise** — ein Feld je
Liste, Enter legt an. Wegnehmen tut ein Kreuz, das erst beim Draufzeigen
erscheint: Eine Liste mit einem Kreuz hinter jeder Zeile liest sich wie
eine Aufforderung.

### Die Sperre gilt auch nachträglich

**Der letzte Abnahmepunkt lässt sich nicht wegnehmen.** Ohne ihn wäre die
Aufgabe hinterher das, was beim Anlegen nicht durchgegangen wäre — und
*eine Sperre, die sich nachträglich umgehen lässt, ist keine.*

### Erledigt hängt an der Abnahme, und der Server prüft es

**Der Knopf steht ausgegraut da, solange ein Haken fehlt** — auch dann,
wenn die Arbeitsliste vollständig durch ist. Das ist der sichtbare Beleg
für die Unterscheidung aus Abschnitt 3: *Die eine misst den Fortschritt,
die andere die Fertigkeit.*

**Geprüft wird es trotzdem noch einmal am Server:** Ein ausgegrauter
Knopf ist keine Prüfung, sondern eine Auskunft.

### Die zwei Listen sehen verschieden aus

| Liste | Bauform |
|---|---|
| *Was getan werden muss* | offen, mit Balken und Erledigt-Datum je Zeile |
| *Wann es abgenommen ist* | in einem Rahmen, ohne Daten, mit einem Satz, der sagt, was sie misst |

**Der Rahmen ist durchgezogen und nicht gestrichelt wie der Fehlerblock
in der Sammlung: Der fragt, dieser gilt.** Ein `FEHLER` darf
unvollständig sein, eine Abnahme nicht.

### Ein Fehler, den erst diese Seite ans Licht gebracht hat

**Die Spalte hieß *In Arbeit seit* und stand auch neben einer Aufgabe auf
`PASSIV`** — an der sitzt aber ausdrücklich niemand. Gemessen wird, was
Abschnitt 3 misst: die Dauer seit dem Eintragen. Die Spalte heißt jetzt
**Arbeitsdauer**; ob gerade jemand dransitzt, sagt der Status daneben.

### Kleinigkeiten, die trotzdem Entscheidungen sind

- **Sortiert wird nach dem Status, dann nach der Kennung:** AKTIV,
  PAUSE, PASSIV. Anders als in der Sammlung ist die Frage hier nicht
  *was ist neu*, sondern *woran sitzt gerade jemand*.
- **Aufgeklappt ist, was AKTIV ist.** Dieselbe Regel wie beim gewählten
  Projekt.
- **`PASSIV` nimmt das Datum mit.** Ein stehengebliebenes *seit* wäre
  eine Behauptung; die Ablage lässt AKTIV und PAUSE ohne Datum ohnehin
  nicht zu, und die Oberfläche macht daraus eine Meldung statt eines
  Fehlers.
- **Der Ursprung ist ein Verweis.** Gespeichert ist die Kennung, der
  Titel wird beim Anzeigen geholt — wer den Eintrag umbenennt, benennt
  den Verweis mit. In der Mappe kostet dieselbe Regel ein Prüfskript mit
  206 Zeilen.
- **Die Haken brauchen zwei Listen im Formular** (`punkt` und `haken`).
  Ein nicht angekreuztes Kästchen schickt gar nichts mit; ohne die Liste
  aller Punkte ließe sich ein Haken nie *weg*nehmen.
- **Zahlen statt Prozent an der Abnahme.** „50 %" sagt nicht, ob es zwei
  von vier oder fünf von zehn sind — und Abnahmelisten sind kurz.

### Ein Punkt bleibt offen, und er steht auf der Karte

**Der Reiter Meilensteine ist leer.** Das Feld steht deshalb auf dem
Strich, mit dem Satz daneben. *Beim Bau von Meilensteine ist diese Zeile
zu ersetzen, nicht zu vergessen* — wie beim Export unter Projekte.

**Der andere offene Punkt ist damit geschlossen:** Die Meldung nach dem
Zusammenlegen sagte bis heute *„zu sehen unter Aufgaben, sobald es den
Reiter gibt."* Sie führt jetzt an ihr Ziel.

---

## 9. Was beim Bauen dazukam — Reiter Meilensteine

*Am 07.09.2026 gebaut. Der vierte Reiter, und der erste, bei dem eine
Regel der Mappe in diesem Produkt anders gilt als in Boot.*

### Vier Karten, und die zweite ist der Punkt

**Übersicht · Was dazwischenkam · Meilensteine · Neuer Meilenstein.** Die
zweite steht dort, weil *Wird notiert, sobald es passiert* eine Bauform
verlangt und keine Ermahnung: drei Felder in einer Zeile — Stein, Datum,
ein Satz. Gelesen wird es dann in der Karte des Steins, geschrieben nur
hier.

Dass sie unter der Übersicht steht und nicht darüber, ist am 07.09.2026
bestätigt worden.

### Vorgänger sind eingetragen, Nachfolger abgelesen

**Beides zu speichern hieße, dieselbe Beziehung zweimal zu halten** — und
eine der beiden Fassungen wäre in einem Monat falsch. `Wartet auf ihn`
ist deshalb kein Feld, sondern die Umkehrung derselben Tabelle. Wer einen
Stein umbenennt, benennt jeden Verweis darauf mit.

**Ein Kreis wird abgewiesen, und zwar über beliebig viele Ecken.** Die
Ablage verbietet nur den direkten Fall (`CHECK meilenstein_id <>
vorgaenger_id`); *A hängt von B und B von A* ließe sie durch. Für die
Anzeige ist das keine Feinheit: *Hängt ab von* und *Wartet auf ihn*
zeigten dann aufeinander, und keine der beiden Auskünfte wäre noch wahr.

### Die Abnahme ist wirklich ein Knopf

Vier Handgriffe waren es: `Abschluss: erledigt` setzen, `archiviere.py`
laufen lassen, eine Zeile ins Quittungsbuch, einen Stein auf die Roadmap
mit Dauer und *Was dazwischenkam*.

**Drei davon fallen jetzt ab, statt getan zu werden.** Die Dauer rechnet
sich aus `eingetragen_am` und `abnahme_am`; das Quittungsbuch liest den
Abschluss; und *Was dazwischenkam* steht schon da, weil es notiert wurde,
als es passierte. Übrig bleibt ein Klick — und die Meldung sagt, was er
getan hat: *„M-001 ist abgenommen. Der Stein steht im Archiv — mit 9
Tagen Dauer und 2 Umwegen."*

**Der Knopf hängt an den Aufgaben, und der Server prüft es.** Solange
eine zugeschlagene Aufgabe offen ist, steht er ausgegraut da; ohne jede
Aufgabe gibt es nichts abzunehmen. Ein ausgegrauter Knopf ist eine
Auskunft, keine Prüfung.

### Verworfen ist der Termin, nicht die Arbeit

**Die Aufgaben unter einem verworfenen Meilenstein bleiben** und stehen
danach wieder ohne Stein da. Ein verworfener Meilenstein sagt nichts
darüber, ob die Arbeit noch zu tun ist — sie hat nur keinen gemeinsamen
Termin mehr. Die Meldung sagt das mit.

**Erledigte Aufgaben bleiben dagegen in der Liste des Steins stehen** und
werden blass. Eine Liste, aus der Fertiges verschwindet, sagt nicht mehr,
woraus der Stein bestand — und genau das soll er später im Archiv
beantworten.

### Regel 7, umgedreht — und sie ist gebaut

Die Liste zeigt per Vorgabe, was offen ist; der Filter in der Kopfzeile
holt die anderen dazu. **In einer Datenbank verschwindet nichts**, aber
der Zweck der Regel bleibt.

### Ein Punkt aus dem Reiter Aufgaben ist geschlossen

Das Feld *Meilenstein* an einer Aufgabe trug bis heute einen Strich mit
dem Satz, dass es den Reiter noch nicht gibt. **Es ist jetzt eine
Auswahl** — Aufgaben lassen sich von beiden Seiten zuschlagen, aus der
Steinkarte und aus der Aufgabenkarte. Ein leeres Feld heißt dabei *keinem
zugeschlagen* und nicht die Nummer null: Die Spalte ist ein
Fremdschlüssel.

*Damit ist der zweite der drei Sätze eingelöst, die als „noch nicht
gebaut" auf einer Seite standen. Offen bleibt der Export unter
Einrichtung.*

### Kleinigkeiten, die trotzdem Entscheidungen sind

- **Aufgeklappt ist der Stein, der abnehmbar ist** — die eine Karte mit
  einer fälligen Handlung.
- **`Bedingung` heißt: was sachlich da sein muss.** Andere Meilensteine
  stehen oben unter *Hängt ab von* und nicht hier; sonst stünden
  Abhängigkeiten an zwei Stellen, und eine davon wäre in einem Monat
  falsch.
- **Zahlen statt Prozent**, wie schon bei der Abnahme der Aufgabe.
- **Die vier Felder der Umweg-Zeile tragen unsichtbare Aufschriften**
  (`.sr-nur`). In einer Zeile aus vier Feldern stehen die Wörter davor im
  Weg; weglassen darf man sie trotzdem nicht — ohne Aufschrift ist ein
  Feld für einen blinden Benutzer ein Feld ohne Namen.

---

## 10. Was beim Bauen dazukam — Reiter Entscheidungen

*Am 07.09.2026 gebaut. Das fünfte und letzte Register — und damit steht,
was dieses Produkt ausmacht.*

### Ein Feld ist dazugekommen: Was entschieden wurde

**Beim Ansehen der Vorschau festgelegt:** Wer eine Entscheidungskarte
ansieht, will zuerst sehen, was überhaupt entschieden wurde — und kann
dann im Verlauf nachlesen, warum.

Die Spalte `entschluss` ist über `NACHZUEGLER` dazugekommen und steht in
der Karte **vor** dem Verlauf, in einem Rahmen — demselben wie die
Abnahme einer Aufgabe. **Der Rahmen markiert in beiden Fällen das, worauf
es hinausläuft;** was darunter steht, ist der Weg dorthin.

**Das widerspricht dem fehlenden Feldschema nicht.** Ein Schema gäbe dem
**Verlauf** eine Gliederung vor — und genau das würde plätten, woran man
die Gründlichkeit abliest. Hier wird nur das Ergebnis vom Weg getrennt:
zwei Dinge, die man zu verschiedenen Zeiten liest.

### Ein Entschluss ohne Satz ist keiner — und das mahnt

**Steht der Zustand auf `ENTSCHLUSS` und das Feld ist leer, wird das ein
Befund.** Entschieden am 07.09.2026, und zwar gegen das Sperren: Den Satz
kann man nachtragen, und *sperren gehört zu dem, was nicht nachwachsen
kann.*

**Das ist das dritte Mal dieselbe Bauform** — nach *ohne Ursache* an der
Aufgabe und *ohne Aufgabe* am Meilenstein. Gesperrt wird in diesem
Produkt genau eines: die Abnahme.

**Bei `OFFEN` ist das leere Feld dagegen kein Befund**, sondern die
Auskunft selbst: Der Weg ist da, der Entschluss steht aus.

### Der Umfang steht am Eintrag, nicht in der Übersicht

**Erst als Spalte entworfen, dann auf Vorgabe in den Kartenfuß
gewandert.** Neben drei anderen Zeilen liest sich eine Zeilenzahl als
Bewertung — *lang gleich gründlich*, und das wäre falsch. Am eigenen
Eintrag beschreibt sie nur ihn selbst: *„17 Zeilen in 3 Abschnitten ·
offen seit 9 Tagen."*

### Zeigen statt kopieren, zum zweiten Mal

**Der Kopf des bezogenen Eintrags steht neben der Entscheidung**, mit
Register und Stand — *Sammlung · noch offen*, *Aufgaben · abgeschlossen
als erledigt*. Damit gibt es keinen Anlass, den Stand in den Verlauf
abzuschreiben: *Was gerade gilt, steht im Backlog; hier steht, warum es
gilt.* Erzwingen ließ sich das nie, erleichtern schon.

**Der Bezug ist ein Feld, nicht zwei.** Art und Kennung gehören zusammen
— die Ablage verlangt es ohnehin (`CHECK (bezug_art = '—') = (bezug_id IS
NULL)`) —, und zwei Auswahllisten, von denen die zweite von der ersten
abhängt, brauchen JavaScript, um nicht zu lügen. Eine Liste mit Gruppen
tut dasselbe ohne.

### Die Liegeprobe hat eine eigene Karte

**Sie ist laut Einordnung der eigentliche Nutzen dieses Registers für
einen Chef:** *der Blick darauf, was entschieden wurde und trotzdem
liegt.* Gebaut ist sie als Tabelle und nicht als Zahl, denn die Frage ist
*welche* und nicht *wie viele* — die Zahlen stehen darunter.

**Zwei Zustände, aber nur eine Frage** — seit dem 07.09.2026: *Getroffen,
und der Eintrag liegt trotzdem* ist die Liegeprobe. Was daneben stand,
*offen und liegt lange*, ist gestrichen: **Wer `OFFEN` wählt, hat
gewählt.** Die Begründung steht in Abschnitt 3.

### Gelöscht, nicht archiviert

**Das einzige Register, in dem das der Weg hinaus ist.** Anderswo wird
abgeschlossen und der Eintrag zieht ins Archiv; eine Entscheidung hat
keinen Abschluss — sie überlebt das, wozu sie gehört. Was falsch
eingetragen wurde, muss deshalb wirklich weg.

**Und die Vorgabe des Filters ist *alle*, nicht *offen*** — anders als
bei den Meilensteinen. Die häufigste Frage hier ist *warum gilt das*,
nicht *was ist noch zu tun*.

### Das Feld ist so hoch wie sein Inhalt

Boots Entscheidungen gehen von **7 bis 1917 Zeilen**. Eine Karte, die für
beide dieselbe Form hat, ist für die eine zu schwer und für die andere zu
klein — die Vorlage rechnet die Höhe aus der Zeilenzahl, mit einer
Untergrenze von sechs und einer Obergrenze von dreißig.

**Gerendert wird nichts.** Das ist am 07.09.2026 in
[Datenhaltung](datenhaltung.md) entschieden worden: Neben der Ansicht
gibt es keine gerenderte Textfassung. Was dasteht, steht so da, wie es
getippt wurde.

### Kleinigkeiten, die trotzdem Entscheidungen sind

- **Aufgeklappt ist, was `OFFEN` ist** — dort steht eine Frage, die
  jemand beantworten muss.
- **Die Suche geht über Titel, Entschluss und Verlauf.** Bei einem
  Register, dessen Inhalt der Text ist, wäre eine Titelsuche keine.
- **Ein zweites Makro für den Dativ.** *9 Tage* in der Kachel, *seit 9
  Tagen* im Satz — im Kartenfuß stand beim ersten Blick „seit 9 Tage
  offen".

---

## 11. Was beim Bauen dazukam — Reiter History

*Am 07.09.2026 gebaut. Der einzige Reiter, der nur zeigt.*

### Drei Ansichten, und sie sind die drei Mappendateien

`02-roadmap` (4 %) · `06-erledigt` (6 %) · `07-archiv` (43 %) — zusammen
53 % des Bestands. Sie beantworten drei verschiedene Fragen, und deshalb
sind es drei Ansichten und nicht eine lange Seite: **Wie sind wir
hierhergekommen · Was ist wann fertig geworden · Was stand da im
Wortlaut.** Derselbe Umschalter wie unter Sammlung.

### Hier wird nichts eingetragen

**Und das ist im Quelltext nachweisbar, nicht nur behauptet:** Es gibt
auf diesem Reiter keine einzige `POST`-Route. Eine Prüfung geht die
Routentabelle durch und hält es fest.

Jede Zeile fällt aus den fünf Registern ab — die Straße aus den
abgenommenen Meilensteinen, das Quittungsbuch aus den Abschlüssen, das
Archiv aus dem, was dort steht. In der Mappe sind das drei Dateien, die
von Hand gepflegt werden, plus `archiviere.py`.

### Kein ASCII-Diagramm

Die Mappe zeichnet die Straße mit Strichen und Kreisen — `──●───●───◉` —,
**weil eine Textdatei nichts anderes kann.** Hier ist es eine senkrechte
Linie mit Marken daran: dieselbe Auskunft, lesbar in jeder
Fensterbreite, und ohne Zeichensalat beim Vorlesen. Der letzte Punkt ist
offen und heißt *hier*.

**Auf dem Stein steht, was Boots Regel verlangt: Dauer und was
dazwischenkam, sonst nichts.** Beides fällt ab — die Dauer aus den zwei
Daten, die Umwege aus dem, was notiert wurde, als es passierte.

### Eine Spalte ist dazugekommen: `meilensteine.abschluss_am`

**Nicht dasselbe wie `abnahme_am`.** Das sagt, dass ein Stein
*abgenommen* wurde, und bleibt bei einem verworfenen leer — er wurde ja
nicht abgenommen, er fällt weg. `abschluss_am` sagt nur, wann er die
Liste verlassen hat.

**Ohne die zweite Spalte hätte ein verworfener Stein kein Datum**, und
das Quittungsbuch kann ohne Datum keine Zeile schreiben. Beim Abnehmen
fallen beide auf denselben Tag; beim Verwerfen gibt es nur das zweite.

### Der Unterschied, der leicht verloren geht — jetzt gebaut

`verworfen` bekommt eine Zeile im Quittungsbuch, `aufgabe` nicht: *Es ist
nicht fertig, es zieht um.* Ein Eintrag der Sammlung, aus dem eine
Aufgabe wurde, steht deshalb nicht darin; seine Zeile schreibt die
Aufgabe, wenn sie fertig ist. Dasselbe gilt für eine Aufgabe mit
Abschluss `meilenstein`.

**Im Archiv steht er trotzdem** — und das ist kein Widerspruch: Das
Archiv fragt nicht, ob etwas fertig wurde, sondern **was drinstand.**

### Ein Kästchen, das nichts tut, ist schlimmer als keines

Im Archiv gibt es keine Felder und keine Kästchen. Der Haken ist ein
Zeichen, kein Bedienelement; eine Prüfung hält fest, dass in der
Archivansicht weder `<textarea>` noch `type="checkbox"` vorkommt.

**Die Abnahme behält dort ihren Rahmen, verliert aber die Füllung.** Der
Rahmen sagt weiter, worauf es hinauslief; die Füllung gehörte zu einem
Feld, das man noch bedienen kann.

### Ein Punkt ist aufgeschoben, nicht vergessen

**Es gibt keinen Weg zurück.** Ein versehentlich abgeschlossener Eintrag
lässt sich hier nicht wiedereröffnen — herausholen ginge nur an der
Ablage selbst.

Am 07.09.2026 bewusst außen vor gelassen. **Solange nichts drinsteht, ist
es kein Problem; es wird eins, wenn es das erste Mal passiert** — und
dann wäre *Wiedereröffnen* der einzige Knopf auf diesem Reiter, der
schreibt. Das ist die Bedingung, unter der diese Entscheidung wieder
aufgeht.

### Eine Karte ist gestrichen worden

*Woraus sich für den nächsten Stein etwas schätzen lässt* — vier Zahlen
unter der Straße, Mittelwert der Dauern und Zahl der Umwege. **Auf
Vorgabe raus.** Die Dauer steht auf jedem Stein; die Summe darunter ist
eine Auskunft, nach der niemand gefragt hat.

---

## 12. Was beim Bauen dazukam — Reiter Einrichtung

*Am 07.09.2026 gebaut. Sieben Karten aus [Übernahme](uebernahme.md),
Abschnitt 6 — und eine achte.*

### Der Export ist eine eigene Karte geworden

**In `uebernahme.md` ist er eine Zeile unter *Ablageorte*.** Seit der
Entscheidung vom selben Tag trägt er drei Zwecke: die Zusage aus
[Datenhaltung](datenhaltung.md) (*der Ausgang bleibt Text*), die erste
der beiden Sicherungen vor dem Zurücksetzen — und **den Weg, auf dem der
Bestand eine Versionsgeschichte bekommt**, weil Tasks nach
`marlei-internal` ausgibt.

Der Pfad steht trotzdem auch unter *Ablageorte*, mit Zustand. Zwei
Fragen, zwei Orte: dort *ob es da und beschreibbar ist*, hier *was
geschrieben wird und ob es noch stimmt*.

### Ausgegeben wird das gewählte Projekt

**Die Vorgabe ist konsequenter als der Entwurf.** Die Vorauswahl aus dem
Reiter Projekte gilt für Sammlung, Aufgaben,
Meilensteine und Entscheidungen — sie gilt hier genauso. Der Knopf heißt
deshalb nach dem Projekt.

**Damit fällt auch die Gegenrichtung:** Ein *alle auf einmal* wäre die
zweite Ausnahme neben den Befunden, und die soll es nicht geben.

### Die Stabilitätszusage prüft sich selbst

**Bei unverändertem Bestand ist die Ausgabe byteweise dieselbe** — keine
Zeitstempel im Kopf, feste Sortierung, `newline="\n"` ausdrücklich, damit
dieselbe Ablage auf zwei Maschinen nicht zwei Ausgaben ergibt.

**Und die Karte beweist es nebenbei.** Die Zeile *Stand der Ausgabe* baut
auf, was ausgegeben würde, und hält es gegen das, was auf der Platte
steht. **Verglichen wird der Inhalt, nicht ein Zähler:** Ein Buchhalter
über geänderte Einträge wäre eine zweite Wahrheit neben der Ablage — und
damit eine, die falsch sein kann.

### Zwei Fehler, die erst der Bau ans Licht gebracht hat

**`Path("")` ist `Path(".")` und damit wahr.** Ein leeres
`MARLEI_EXPORT` hätte als eingerichtet gegolten, und der Export schriebe
ins Arbeitsverzeichnis des Dienstes — lautlos, an einer Stelle, an der
niemand danach sucht. `ZIEL` ist jetzt `None`, wenn nichts eingestellt
ist.

**`NFKD` zerlegt das ö, bevor ein `replace` es findet.** Aus *Völlig*
wurde *vollig* statt *voellig*. Erst umschreiben, dann zerlegen — im
Deutschen ist das keine Kleinigkeit: Der Ordnername steht in einem
Repository und wird gelesen.

### Die Werkseinstellung bietet den Export an, bevor sie fragt

**`uebernahme.md` verlangt genau das, und die Karte macht es konkret:**
Sie sagt, ob die letzte Ausgabe noch stimmt, und wenn nicht, in wie
vielen Dateien sie abweicht. Daneben steht *Ohne Export weiter* — ein
Ausgang, kein Zwang.

**Sie ist hier gefährlicher als in Boot, und die Karte sagt es:** *Ein
Abbild holt man erneut, einen eingetragenen Gedanken nicht.* Das
Losungswort ist dasselbe wie beim Löschen — der Projektname.

**Was bleibt, ist das Projekt selbst** mit Name, Beschreibung und Vision.
Das ist der ganze Unterschied zum Löschen.

### Was nicht gebaut ist, steht auf der Karte

**Nach neuen Versionen wird nicht gesucht.** `uebernahme.md` sagt
*wortgleich — nur das Repository ist ein anderes*; es gibt aber keines.
Ein Knopf, der ins Leere fragt, wäre schlimmer als der Satz. *Beim Bau
der Veröffentlichung ist diese Zeile zu ersetzen, nicht zu vergessen.*

### `firewall.py` ist abgeschrieben, nicht neu geschrieben

Drei Stellen geändert: der Modulkopf (dort ist der blinde Fleck der
Netzstart, hier die Frage, ob man überhaupt durchkommt), die
Umgebungsvariable ohne `PXE_`, und die Portliste — **zwei Zeilen statt
neun**. Der Rest, also die ganze Ableserei über ufw und systemd samt
beider `is-active`-Fallen, ist byteweise dieselbe. Sie steht als
`angepasst` in `tools/gemeinsam.txt`, mit der Anmerkung, was anders ist.

### Der Fehlerbericht zählt, statt abzuschreiben

**Der freiwillige Block enthält Zahlen und Pfade — keine Titel, keine
Texte, keine Namen.** Das ist der Grund, warum er überhaupt verschickbar
ist: In einer Aufgabenverwaltung steht, woran eine Firma arbeitet. Eine
Prüfung hält fest, dass kein einziger Eintragstitel im Bericht landet.

---

## 13. Was beim Bauen dazukam — Reiter Hilfe

*Am 07.09.2026 gebaut — **ohne Vorschau**, auf Vorgabe: Die Hilfe ist
selbsterklärend genug, um sie ohne Entwurfsrunde zu bauen. Der erste
Reiter ohne Entwurfsrunde, und der einzige, dessen Gliederung schon
feststand, bevor eine Zeile davon geschrieben war.*

### Die Gliederung stand schon da — auf den Karten

**Seit dem Bau des ersten Reiters trägt jeder Kartenkopf ein
Fragezeichen**, das auf `/hilfe#reiter-karte` zeigt. Neunundzwanzig
Stück, und bis heute zeigten sie alle ins Leere: Der Browser springt
dann an den Seitenanfang, und die Seite sieht dabei richtig aus.

**Damit war die Hilfe kein Entwurf, sondern eine Liste, die abgearbeitet
wird:** ein Kapitel je Reiter, ein Abschnitt je Karte, in der Reihenfolge
der Reiterleiste. Was die Karte tut, steht in ihrem Abschnitt; warum sie
es so tut, ebenfalls — die Gründe stehen ohnehin schon in den Abschnitten
6 bis 12 dieses Dokuments und in den Kommentaren der Vorlagen.

### Die Anker sind ein Vertrag, und er wird in beide Richtungen geprüft

**Ein Fragezeichen, das ins Leere zeigt, fällt niemandem auf** — genau
deshalb geht die Prüfung beide Wege:

- **Jeder Anker, den eine Karte anspringt, existiert hier** (29 von 29).
- **Jeder Abschnitt hier gehört zu einer Karte, die es noch gibt.** Ohne
  diese Richtung bliebe beim Umbau eines Reiters ein Kapitel über eine
  Karte stehen, die niemand mehr findet.
- **Auch der Rückweg** — jedes *Zur Karte →* landet auf einer
  `id`, die in der Vorlage dieses Reiters wirklich steht.
- **Und die Verweise innerhalb der Hilfe** untereinander.

### Zwei Kapitel gehören keiner Karte

**„Erste Schritte" und „Was überall gilt".** Das zweite ist beim
Schreiben entstanden und nimmt sechs Dinge aus den Kapiteln heraus, die
sonst siebenmal dagestanden hätten: das gewählte Projekt, die Kennungen
über alle Projekte, was sperrt und was mahnt, die Befunde, die Daten und
*zeigen statt kopieren*.

**Es ist mehr als eine Ersparnis.** Diese sechs sind die Regeln, an denen
sich dieses Produkt von einer Aufgabenliste unterscheidet — sie einmal im
Zusammenhang zu lesen, erklärt mehr als sechsmal ein Halbsatz an einer
Karte.

### Was nicht drinsteht

- **Die Installation.** Sie steht in den `.md`-Dateien des Projekts. Hier
  steht, was am laufenden Server zu bedienen ist — dieselbe Grenze wie in
  MARLEI Boot.
- **Lizenz und Quelltext.** In Boot ist das ein eigenes Kapitel; hier
  zeigten beide Verweise ins Leere, weil dieses Produkt mit Absicht noch
  kein öffentliches Repository hat. **Dieselbe Entscheidung wie in der
  Fußzeile**, und sie kommt mit der Veröffentlichung zurück.
- **Server Health.** Der Reiter ist noch nicht gebaut, also gibt es kein
  Kapitel dafür. *Beim Bau ist es dazuzuschreiben, samt der zwei
  Kartenabschnitte — die Prüfung merkt es sonst nicht: Sie prüft nur, was
  da ist.*

### Der Fund beim Schreiben: ein Versprechen ohne Mechanik

**Drei Karten sagen heute „steht als Befund über der Seite" — und es gibt
keine Befunde.** `rahmen()` gibt eine leere Liste weiter, ein Modul dafür
existiert nicht. Aufgefallen ist es erst beim Schreiben des Kapitels *Was
überall gilt*, wo der Mechanismus zum ersten Mal im Zusammenhang erklärt
werden musste.

**Die Hilfe sagt es deshalb ausdrücklich:** Die Stellen sind gebaut und
benannt, aber sie zeigen sich vorerst nur auf ihrer eigenen Karte. Das
ist dieselbe Entscheidung wie beim fehlenden Export unter Projekte und
beim leeren Reiter Aufgaben: **Ein Verweis, der ins Leere zeigt, wäre
schlimmer als der Satz; ihn wegzulassen wäre am schlimmsten.** Eine
Prüfung hält den Satz fest, damit er beim Bau der Befunde ersetzt und
nicht vergessen wird.

*Betroffen sind vier Stellen: die fünf Fehlerangaben in der Sammlung, das
leere „dahinter" an der Aufgabe, der Meilenstein ohne Aufgabe und der
Entschluss ohne Satz.*

### Kleinigkeiten, die trotzdem Entscheidungen sind

- **Die Hilfe bekommt nichts außer dem Rahmen.** Sie liest weder die
  Ablage noch die Umgebung — und gilt deshalb auch dann, wenn kein
  Projekt gewählt ist. **Gerade dann sucht sie jemand.**
- **Sie schreibt nicht.** Es gibt keine `POST`-Route unter `/hilfe`;
  dieselbe Prüfung wie unter History.
- **Die häufigen Fragen sind die Kehrseite der Sperren.** *Warum ist
  „Erledigt" grau · warum kann ich keine Aufgabe ohne Abnahme anlegen ·
  wohin ist mein Eintrag verschwunden* — jede Regel, die etwas verhindert,
  erzeugt genau eine Frage, und die gehört beantwortet, wo sie gestellt
  wird.
- **Ein Satz steht auf dieser Seite, der sonst nirgends steht:** dass
  diese Oberfläche niemanden fragt, wer er ist, und deshalb nicht ins
  offene Netz gehört. In einer Aufgabenverwaltung steht, woran eine Firma
  arbeitet.

---

## 14. Was beim Bauen dazukam — Reiter Server Health

*Am 07.09.2026 gebaut, ohne Vorschau. **Der neunte und letzte Reiter** —
und der einzige, dessen Zuschnitt schon vor dem Bau entschieden war:
[Übernahme](uebernahme.md), Abschnitt 5, zwei Karten statt fünfzehn.*

### Die zweite Hälfte der Auslastung ist ersetzt, nicht gestrichen

**Das war die einzige offene Frage dieses Reiters.** `auslastung.py` aus
Boot zerfällt in zwei Teile: Last und Speicher aus `/proc` — auf jedem
Server dieselbe Frage — und `uebertragungen()`, die an den offenen
TCP-Verbindungen auf 80 und 2049 abliest, wer gerade sein
Wurzeldateisystem zieht. **Das zweite ist Boot-eigen; hier zieht niemand
etwas.**

Die Frage *was tut der Server gerade* bleibt trotzdem, und die ehrliche
Antwort ist **dieser Dienst selbst**: seit wann er läuft und was er
braucht. Zwei Gründe, und beide sind praktisch:

- **Auf einer Maschine, die sonst im Leerlauf steht, sagt die
  Prozessorlast wenig darüber, ob sie für diesen Dienst reicht.** Sein
  eigener Verbrauch sagt es.
- **Die Betriebszeit beantwortet die erste Frage jeder Fehlersuche:**
  Läuft er noch, oder hat er sich zwischendurch neu gestartet? Daneben
  steht die Laufzeit der Maschine — gehen die beiden auseinander, weiß
  man es.

**Kein Rückfall auf einen Zeitstempel beim Laden des Moduls.** Das sähe
wie eine Messung aus und wäre eine Erfindung: Es misst, wann Python das
Modul geladen hat. Fehlt `/proc`, fällt die Zeile ganz weg.

### Was ohne /proc dasteht, ist nichts — und das ist die Zusage

**Jede Funktion liefert leere Werte statt einer Behauptung.** Die Karte
sagt dann *Auslastung nicht abfragbar* und nennt den Grund. Aufgefallen
beim ersten Aufruf unter Windows: Dort stand einen Moment lang **„Dieser
Dienst läuft .“** — ein Satzstumpf, weil die Zeile gebaut wurde, obwohl
nichts zu messen war. Sie fällt jetzt ganz weg.

### Serverdetails kommt aus derselben Quelle wie der Fehlerbericht

**`webui/bericht.py`, und das ist Absicht.** Zwei Quellen liefen
auseinander, und dann nennt die Mail einen anderen Kernel als die Seite,
die der Betreiber gerade vor sich hat. `_maschine()` liefert beide.

**Der Fehlerbericht ist dabei besser geworden, nicht nur gleicher:** Er
nannte bisher `platform.system()` — auf einem Linux-Server also *Linux
6.1.0*, ohne die Distribution. Jetzt stehen Distribution und
Virtualisierung darin, und beides sind Angaben, die auf jeder
Installation gleich aussehen; der freiwillige Block bleibt unberührt.

**Die Dienstversionen sind andere als in Boot, das Argument ist
dasselbe.** Dort ist es *dnsmasq 2.89 gegen 2.90*; hier sind es
**FastAPI und uvicorn** — eine Meldung aus dem Innern von Starlette ist
ohne Versionsnummer nicht einzuordnen, und die Rückfrage danach kostet
einen Tag. Dazu `nginx` als Paket und `marlei-tasks` als Stempel aus
`install.sh`.

**Keine Paketliste.** Diese Oberfläche hat keine Anmeldung; jede Zeile
mehr wäre für jeden im Netz eine Zeile mehr Einkaufsliste.

### Ein Puffer, der ein Argument verschluckt

**`karte(stand)` gab beim zweiten Aufruf mit einem anderen Stempel den
ersten zurück** — Ableserei und Stempel lagen zusammen im Puffer. In der
Anwendung wäre es nie aufgefallen: Dort ist der Stempel immer derselbe.
**Gefunden hat es die Prüfung**, und das ist der seltene Fall, in dem ein
Test etwas findet, das die gebaute Seite nicht zeigt.

Gepuffert wird jetzt nur, was teuer ist — `dpkg-query`, `uptime`,
`systemd-detect-virt` —, eine Minute lang. Der Stempel kommt bei jedem
Aufruf frisch vom Aufrufer.

### /proc nachgebaut, weil es hier keines gibt

**Die Feldzählerei in `/proc/self/stat` ist die Stelle, an der ein Fehler
still danebenliegt.** Der Prozessname steht dort in Klammern und darf
Klammern und Leerzeichen enthalten — wer nach Feldern zählt, statt hinter
der letzten schließenden Klammer zu trennen, bekommt eine Zahl, die
plausibel aussieht und falsch ist.

Die Prüfung legt deshalb ein `/proc` in einem Wegwerfverzeichnis an,
setzt `auslastung.PROC` darauf und prüft gegen einen Prozessnamen, der
genau diese Falle enthält: `(uvi corn (x))`.

### Das Kapitel in der Hilfe ist mitgewachsen

**Abschnitt 13 nennt es als offenen Punkt** — *beim Bau ist es
dazuzuschreiben, die Prüfung merkt es sonst nicht: Sie prüft nur, was da
ist.* Es steht jetzt da, mit zwei Kartenabschnitten; damit sind es elf
Kapitel und **31 Anker**, und der Vertrag zwischen Karten und Hilfe hält
in beide Richtungen.

### Der Platzhalter ist weggefallen

`leer.html` und `_seite()` — *„Diese Seite ist noch nicht gebaut“* — sind
raus: **Alle neun Reiter sind gebaut.** Eine Prüfung hält fest, dass
beides weg ist; wer einen zehnten Reiter anfängt, holt sich beides aus
der Geschichte zurück.

### Ein Satz, der seit vier Reitern falsch war

**Der Löschschritt unter Projekte sagte noch immer, den Ausgang unter
Einrichtung gebe es nicht** — und dass bis dahin nur eine Kopie von
`tasks.db` helfe. Er ist seit dem Bau von Einrichtung falsch;
Abschnitt 6 hatte ausdrücklich verlangt, ihn zu **ersetzen, nicht zu
vergessen** — und beim Bau der Einrichtung ist er trotzdem
stehengeblieben. Gefunden hat ihn erst die Prüfung, die ihn festhielt:
Sie stand da und sagte weiter *„noch nicht gebaut“ steht drin*, grün und
falsch. **Eine Prüfung sichert einen Satz, sie erinnert nicht an ihn.**

Er führt jetzt an sein Ziel — **und nennt die Bedingung, die der
Kartentext nicht von selbst hergibt:** Gelöscht wird hier jedes Projekt,
ausgegeben aber immer nur das gewählte. Ohne den Zusatz exportiert jemand
A und löscht B.

*Damit sind alle drei „noch nicht gebaut“-Sätze eingelöst. Offen bleibt
allein der aus dem Reiter Hilfe: die seitenweiten Befunde.*

---

## 15. Was beim Bauen dazukam — die Befunde

*Am 07.09.2026 gebaut, nach allen neun Reitern. **Der letzte offene Satz
dieses Produkts** — drei Karten versprachen seit Tagen „steht als Befund
über der Seite", und es gab keinen.*

### Sechs Befunde, und einer ist von anderer Art

| Befund | Stufe | was er meldet |
|---|---|---|
| **Liegeprobe** | gelb | entschieden, und der Eintrag liegt trotzdem |
| **Ohne Ursache** | gelb | eine Aufgabe sagt nicht, was dahintersteckt |
| **Ohne die Angaben** | gelb | ein `FEHLER` ohne die fünf verlangten |
| **Ohne Aufgabe** | gelb | ein Meilenstein hat nichts unter sich |
| **Ohne Satz** | gelb | ein `ENTSCHLUSS` ohne das Ergebnis |
| **Lange nicht hingesehen** | blau | seit über einem Monat keine Durchsicht |

**Die ersten fünf sind die vier Mahnungen plus die Liegeprobe** — also
genau das, was auf den Karten schon versprochen war, und nichts darüber
hinaus.

**Der sechste ist der, wegen dem es die Befunde überhaupt gibt.** Er
vermisst nichts, er misst: *Der Chef will gerade das sehen, was in dem
Projekt liegt, in das er seit Wochen nicht geschaut hat.* Ein Befund, der
nur das gewählte Projekt kennt, zeigte ihn nie — er meldete Ruhe, wo
keine ist.

### Rot gibt es nicht, und das ist kein Versehen

**In Boot ist Rot der Server, der nicht bootet.** Hier täte das nur eine
Ablage, die sich nicht schreiben lässt — dann steht aber ohnehin keine
Seite mehr, auf der eine Karte stehen könnte.

**Was hier gemeldet wird, ist von anderer Art: Es fehlt etwas, das
nachwachsen kann.** Genau dafür ist Gelb da. Die Regel steht trotzdem im
Modulkopf, weil sie zur Mechanik gehört und nicht zum Vorrat: *Rot ist
nie wegklickbar.*

### Eine Karte je Projekt, nicht eine mit einer Liste darin

**Das folgt aus Abschnitt 2 und ist die einzige echte Abweichung von
Boots Mechanik:** *Zur Kenntnis genommen wird je Projekt, nicht je
Befund.* Eine gemeinsame Karte mit drei Projekten darin hätte einen
einzigen Knopf — und der stellte alle drei zugleich still.

**Der Preis ist sichtbar:** Bei fünf Lücken in einem Projekt stehen fünf
gelbe Karten übereinander. Das ist beim ersten Blick auf die gebaute
Seite bestätigt worden und bleibt so — sie sind zugeklappt, einzeilig und
einzeln wegklickbar. **Eine Karte, die drei Dinge zusammenfasst, ist eine
Karte, die man nicht abarbeiten kann.**

### Der Weg dorthin gehört an die Karte

**„Ansehen →" stellt die Vorauswahl um und führt zum Gemeldeten.** Beides
zusammen, und das Erste ist der Punkt: Ohne das Umstellen zeigte der
Reiter dahinter ein anderes Projekt — der Klick landete auf der richtigen
Seite im falschen Bestand.

Dafür nimmt `/projekte/waehlen` jetzt ein `ziel` entgegen. **Nur eigene
Wege:** Was nicht mit einem einzelnen `/` anfängt, fällt auf die
Projektübersicht zurück — dieselbe Prüfung wie beim `zurück` des
Kenntnis-Knopfes. Eine offene Weiterleitung ist billig zu verhindern und
teuer zu übersehen.

### Die Marke, und warum sie grob sein muss

**Weggeklickt heißt: „ich weiß Bescheid, bis es schlimmer wird."**
Gespeichert wird die Zahl, die dastand; steigt sie, kommt die Karte
zurück. Bei den fünf gelben ist es die Zahl der betroffenen Einträge.

**Beim Durchsicht-Befund sind es angefangene Monate und nicht Tage.**
Eine Marke, die mit jedem Tag steigt, wäre kein Wegklicken, sondern ein
Aufschub bis morgen.

**Eine Frist gibt es bewusst nicht.** Jede Zahl darin wäre gegriffen, und
*sieben Tage* beantwortet keine Frage, die jemand hat.

### Zwei Zeilen Ablage, und eine war schon da

Die Tabelle `kenntnis` steht seit dem ersten Tag im Schema — mit
`projekt_id`, `befund` und `seit`, und mit dem Kommentar, warum sie
zweispaltig ist. **Dazugekommen ist `marke`**, über `NACHZUEGLER`; ohne
sie wäre ein zur Kenntnis genommener Befund für immer leise, auch wenn
aus drei Lücken dreißig werden.

**Aufgeräumt wird bei jedem Aufbau:** Was gerade nicht gilt, wird
vergessen — *war ein Befund weg und kommt wieder, ist er neu.* Sonst
bliebe eine Lage von vorigem Monat stumm, wenn sie sich wiederholt.

### Nicht gepuffert

**Anders als die Serverdetails.** Die Zahlen kommen bei jedem Seitenaufbau
frisch aus der Ablage, und alle zehn Sekunden noch einmal für das
nachgeholte Stück.

**Der Grund ist derselbe, aus dem Boot es puffert, nur andersherum
gelesen:** Dort kostet eine Messung einen Prozessstart; hier ist es eine
lokale Datei. *Ein zwischengespeicherter Befund, der veraltet, wäre genau
das, was diese Oberfläche sonst vermeidet* — wer eine Lücke gerade
nachgetragen hat, soll die Karte nicht noch zehn Sekunden lang sehen.

**Gerechnet wird dabei aus den Listen, nicht aus eigenem SQL.** Was ein
fehlender Grund ist, was ein Stein ohne Aufgabe und was die Liegeprobe,
steht je einmal in `datenbank.py` — eine zweite Abfrage mit derselben
Bedingung wäre in einem Monat die falsche.

### Damit ist kein Satz mehr offen

Die drei Karten, die es versprachen, sagen jetzt die Wahrheit; das
Kapitel *Was überall gilt* in der Hilfe beschreibt beide Knöpfe statt
eines Fehlens; und der Satz *„Dieselbe Quelle speist später den Befund"*
unter Sammlung hat sein *später* verloren.

*Offen bleibt nichts aus dem Bau. Was jetzt kommt, ist die Übernahme des
Bestands aus MARLEI Boots Mappe.*

---

## 16. Was beim Bauen dazukam — die Installation

*Am 07.09.2026 gebaut, nachdem alle neun Reiter standen. **Bis dahin lief
dieses Werkzeug nur aus einem venv auf einem Windows-Arbeitsplatz** — die
Karte Serverdetails fragte nach einem Stempel, den niemand setzen konnte,
und `/var/lib/marlei-tasks/` legte nichts an.*

### Die Frage war nicht „wie installiert man", sondern „wie verträgt es sich"

**Vorgabe: auf `dev-marlei` (192.168.178.31).** Dort läuft seit dem
02.09.2026 ein vollständiger MARLEI Boot — alle fünf Dienste,
gekennzeichnet als *Entwicklung*.

**Alles Trennbare ist ohnehin getrennt:** eigener Benutzer, eigenes
Verzeichnis, eigene Einheit, eigene Umgebungsdatei, eigenes venv, eigener
Anwendungsport (8000 gegen Boots 8080). Das war nie das Problem.

**Der Weg von außen ist der einzige, den es nur einmal gibt.** Boots
vhost trägt:

```
listen 80 default_server;
server_name _;
```

Und `install.sh` dort entfernt zusätzlich `sites-enabled/default`. Ein
zweiter vhost auf Port 80 hat damit zwei mögliche Ausgänge, und beide
sind schlecht:

- **Ohne `default_server`:** nginx startet, meldet die doppelte
  Verwendung nur im Log — und diese Oberfläche ist unerreichbar, ohne
  dass irgendwo ein Fehler steht.
- **Mit `default_server`:** nginx startet gar nicht mehr. Dann steht
  nicht dieses Werkzeug still, sondern **der Bootserver**.

### Entschieden: eigener vhost auf eigenem Port, und vorher wird geprüft

**Die Wahl im September 2026** aus drei Vorschlägen — die beiden anderen
waren *ganz ohne nginx* (uvicorn direkt nach außen) und *install.sh sucht
sich selbst einen freien Port*.

**Der Port kommt aus `MARLEI_PORT`, Vorgabe 80.** Auf `dev-marlei` also:

```
sudo MARLEI_PORT=8081 ./setup/linux/install.sh
```

**Und der dritte Vorschlag ist aus einem Grund durchgefallen, der hier
öfter fällt:** Ein Skript, das sich den nächsten freien Port sucht, macht
die Adresse zu einem Fundstück statt zu einer Angabe. *Explizit vor
bequem.*

### Zwei Prüfungen, weil es zwei Arten gibt, einen Port zu belegen

- **`ss -lntp`** findet einen fremden Dienst auf dem Port. Der fiele beim
  Start von nginx ohnehin auf — aber dann ist die halbe Installation
  gelaufen.
- **Ein `grep` über `sites-enabled/`** findet den Fall, den man *nicht*
  sieht: einen anderen vhost auf demselben Port.

**Der zweite ist der eigentliche.** Er ist an Boots echter Datei geprüft:
Für Port 80 schlägt er an, für 8081 nicht — und die eigene Datei mit
`listen 8081` löst bei einer Prüfung auf 80 keinen Fehlalarm aus.

**Abgebrochen wird mit dem Weg im Text:** *Einen anderen Port wählen:
`sudo MARLEI_PORT=8081 …`*. Eine Fehlermeldung, die nicht sagt, was zu
tun ist, kostet dieselbe Zeit wie gar keine.

### Was das Skript nicht tut

- **Es fasst keine Datei von MARLEI Boot an.** Eine Prüfung hält fest,
  dass weder `/etc/pxeweb` noch `sites-enabled/pxe` darin vorkommen.
- **Es entfernt `sites-enabled/default` nur, wenn es selbst auf 80 ist.**
  Auf einem anderen Port steht die nginx-Standardseite nicht im Weg, und
  eine Datei zu entfernen, die einen nicht stört, ist ein Übergriff.
- **`systemctl reload nginx` statt `restart`.** Läuft hinter demselben
  nginx noch ein anderes Produkt, fiele es bei einem Neustart kurz aus.
- **Es legt keinen Ausgang außerhalb der Ablage an.** Zeigt
  `MARLEI_EXPORT` woandershin — etwa in ein Git-Repository —, gehört der
  Pfad jemand anderem; das Skript meldet ihn, statt dort Verzeichnisse zu
  bauen. Es trägt ihn aber in die Einheit ein, weil
  `ProtectSystem=strict` sonst jedes Schreiben verhindert.

### Aus Boot übernommen, weil es dort schon wehgetan hat

**`nachtragen_aus_vorlage()`.** Der dritte Fall neben *Datei fehlt* und
*Datei ist da*: Ein Name, den die Vorlage kennt und die Datei nicht, ist
keine eigene Änderung, sondern eine Lücke — sie entsteht, sobald der Code
einen Wert dazubekommt. In Boot ist genau das auf der produktiven
Maschine aufgefallen.

**Der Versionsstempel nach dem `rsync`**, nicht davor: Der läuft mit
`--delete` und räumte die Datei sonst bei jedem Lauf wieder weg. Samt
`safe.directory`, weil das Skript als root in einem fremden Projektordner
nachfragt.

### `/health` ist dazugekommen

**Der Selbsttest am Ende brauchte etwas, das man fragen kann.** Boot hat
`/health`, also hat es Tasks jetzt auch — mit einem Unterschied, der
hierher gehört: **Zahlen, keine Namen.** Dieselbe Regel wie beim
Fehlerbericht, und hier noch wichtiger, denn diese Auskunft ist
maschinenlesbar und fragt niemanden, wer er ist.

Darin steht auch die Zahl der **offenen Befunde** — die eine Angabe, die
einen Wachhund überhaupt interessieren könnte: *liegt etwas, das jemand
ansehen sollte.*

### Was ohne Debian trotzdem geprüft wird

**`install.sh` läuft hier nicht, seine vier Dateien hängen trotzdem
zusammen** — und ein Port, der in der Einheit steht und im vhost nicht,
fiele sonst erst auf der Maschine auf. Die Prüfung liest die vier Dateien
als Text:

- kein `default_server` im vhost — **die Anweisungen, nicht die
  Kommentare**: Der Modulkopf erklärt ja gerade, warum es keines gibt
- Einheit und vhost nennen denselben Anwendungsport, und einen anderen
  als Boots 8080
- jede `MARLEI_*`-Variable, die der Code liest, steht in der Vorlage
- die Vorlage nennt denselben Ablageort, den der Code als Vorgabe kennt

### Ein `uninstall.sh` gibt es nicht

**Und das steht in [Installation](installation.md), statt verschwiegen zu
werden** — mit den fünf Schritten von Hand und der Warnung, die auf einer
Maschine mit MARLEI Boot zählt: Ein `apt-get remove nginx` ist genau der
Griff, der den Bootserver mitnimmt.

*In Boots Sammlung steht derselbe Punkt als eigener Eintrag. Hier ist er
notiert, nicht gebaut.*

> **Nachtrag vom 19.09.2026: Jetzt gibt es beide** —
> `setup/linux/uninstall.sh` und `setup/windows/uninstall.ps1`. Der
> Abschnitt darüber bleibt stehen, weil er die Lage von damals richtig
> beschreibt; falsch ist nur seine Überschrift. Den Anstoß gab die
> Windows-Fassung: Dort liegen **zwei** der Dinge, die zu entfernen sind,
> außerhalb des Programmverzeichnisses — die Aufgabe in der
> Aufgabenplanung und die Regel in der Firewall —, und beide tragen einen
> Namen, den das Setup selbst gesetzt hat. Ein Skript muss dafür nichts
> raten; genau das war der Einwand gegen ein solches Skript.
>
> Der Bestand bleibt dabei liegen, sofern man ihn nicht ausdrücklich
> verlangt — und dann noch ein Wort tippt. Was stehen bleibt und warum,
> steht in [Installation](installation.md), Abschnitt 8.
>
> *Dies ist eine Korrektur und kein Fortschreiben: Dieses Dokument steht
> seit dem 09.09.2026 still, und was seither entsteht, wird am Code
> begründet. Ein Satz, der inzwischen das Gegenteil behauptet, bleibt
> trotzdem nicht stehen.*

---

## 17. Was die erste echte Installation gezeigt hat

*Am 07.09.2026 auf `dev-marlei` (192.168.178.31) installiert, neben dem
Bootserver, mit `MARLEI_PORT=8081`. **Drei Funde, und keiner davon wäre
hier aufgefallen** — sie brauchten eine Maschine mit `/proc`, mit `dpkg`
und mit einem Port, der nicht 80 ist.*

### Die Portprüfung hat getan, was sie soll

`sudo ./setup/linux/install.sh` bricht dort ab und nennt Boots Datei; mit
`MARLEI_PORT=8081` läuft es durch. **Der Bootserver daneben hat davon
nichts gemerkt** — `systemctl reload nginx` statt `restart`.

Auf Server Health steht seither, was diese Maschine wirklich ist: *Debian
GNU/Linux 13 (trixie) · Linux 6.12.107+deb13-amd64 · x86_64 ·
**VirtualBox (oracle)** · up 11 minutes*. Die Übersetzung des
Herstellernamens ist damit an echten Daten belegt.

### Der Ausgang hing am Projekt, und die Karte log

**Unter *Ablageorte* stand „nicht eingerichtet — `MARLEI_EXPORT` ist
leer", während zwei Karten weiter unten der Pfad danebenstand.** Beides
kann nicht stimmen.

Der Grund: Die Zeile fragte über `export.stand(projekt)`, und ohne
gewähltes Projekt wurde gar nicht erst nachgesehen. **Der Ort hängt aber
nicht am Projekt** — ob ein Verzeichnis da und beschreibbar ist, hat auch
ohne Projekt eine Antwort. Dafür gibt es jetzt `export.ort()`.

> **Eine Karte, die einen Grund nennt, den es nicht gibt, ist schlimmer
> als eine, die schweigt.**

### Die Firewall nannte den falschen Port

**Die Karte sagte `80/tcp`, erreichbar war 8081.** Auf einer Maschine mit
MARLEI Boot ist das der Normalfall und nicht die Ausnahme — und wer nach
dieser Zeile eine Regel schreibt, öffnet den falschen Port und sucht eine
Stunde. **Die Karte hätte ihn selbst dorthin geschickt.**

Die Zahl kommt jetzt aus `MARLEI_BASE_URL`, also aus der Adresse, die im
Kopfband steht — das ist die, die jemand tatsächlich aufruft. Nicht aus
dem Port, auf dem die Anwendung hört: Der ist 8000 auf `127.0.0.1`, und
dorthin kommt von außen niemand.

### Und eine Klammer, die nichts sagte

`nginx  1.26.3-3+deb13u7 (nginx)` — die Klammer soll heißen *gefunden
unter einem anderen Namen als erwartet*. Heißt das Paket wie die Zeile,
ist sie Rauschen; MARLEI Boot hat denselben Satz im Quelltext stehen, und
beim Abschreiben ist die halbe Bedingung verlorengegangen.

**Beim Beheben kam der eigentliche Fehler heraus, und den hat die Prüfung
gefunden, nicht das Lesen:** Die Schleife, die `dpkg-query` ausliest,
hieß ihre Laufvariable `name` — genau wie den Parameter. Verglichen wurde
damit gegen den zuletzt gelesenen Paketnamen statt gegen den der Zeile,
und die Klammer verschwand *immer*. Der erste Testfall war zufällig
richtig; erst der zweite fiel um.

*Drei Prüfungen halten die drei Funde fest.*

---

## 18. Der Port — eine Zahl, zwei Fragen

*Am 07.09.2026, nach der Installation auf `dev-marlei`. Die Frage:
**Lässt sich die Portnummer einstellen — ein Feld, Vorgabe 8081?** Die
Antwort ist zweigeteilt — die Vorgabe ja, das Feld nein.*

### 8081 ist jetzt der Produktport

**Bis dahin war die Vorgabe 80**, und `MARLEI_PORT=8081` musste man
dazusagen. Das war auf jeder Maschine mit MARLEI Boot der Normalfall —
also auf der einzigen, auf der dieses Werkzeug bisher läuft.

**Ein Port, der mal so und mal so ist, gehört in kein Lesezeichen.** 8081
gilt jetzt überall: auf einer Maschine mit Boot und auf einer ohne. Wer
die 80 will, sagt es — `sudo MARLEI_PORT=80 ./setup/linux/install.sh`.

*Nebenwirkung, die keine ist: Die Portprüfung in `install.sh` bleibt
genau so nötig wie vorher. Sie prüft, was tatsächlich gilt, nicht, was
üblich ist.*

### Das Feld gibt es nicht, und zwar aus demselben Grund wie bei der Firewall

**Der Port ist keine Einstellung dieser Anwendung.** Er steht nicht in
`/etc/marlei-tasks.env`, sondern in `/etc/nginx/sites-available/marlei-tasks`
— einer Datei, die root gehört, vor einem Dienst, der root gehört.

Ein Feld, das ihn ändert, müsste **als root in `/etc/nginx` schreiben,
`nginx -t` laufen lassen und einen Dienst neu laden** — aus einer
Oberfläche heraus, die niemanden fragt, wer er ist. Das ist genau die
Tür, die dieses Haus nicht aufmacht:

> **Gemeldet wird, nicht angefasst.** Dieselbe Grenze wie bei der
> Firewall eine Karte weiter unten — und dort steht sie schon
> ausgeschrieben: *Ein Werkzeug, das ungefragt Regeln auf einer fremden
> Maschine setzt, ist das, wovor man Werkzeuge sonst warnt.*

**Dazu kommt, dass es nicht einmal ginge:** Die Einheit läuft mit
`ProtectSystem=strict` und gibt genau ein Verzeichnis zum Schreiben frei.
Ein Feld, das den Port ändern soll, verlangt also zuerst, die Absicherung
des Dienstes zu lockern — und die ist kein Beiwerk, sondern der Grund,
warum eine Oberfläche ohne Anmeldung überhaupt vertretbar ist.

### Was stattdessen dasteht

**Unter *Einstellungen* ein eigener Abschnitt** — die Karte zeigt die
Umgebungsdatei, und der Port steht dort nicht; das sagt sie jetzt
ausdrücklich, statt die Frage offenzulassen. Daneben die Zahl, die
gerade gilt, und der Befehl **zum Kopieren**:

```
sudo MARLEI_PORT=9090 ./setup/linux/install.sh
```

**Die Bauform gibt es in diesem Haus schon** (`.befehlszeile` samt
Kopierknopf, aus MARLEI Boot): ein Befehl, der auf einer anderen Maschine
eingegeben wird, meist in einer SSH-Sitzung daneben. *Abtippen ist die
häufigste Fehlerquelle, die wir selbst abstellen können.*

**Eine Prüfung hält fest, dass an dieser Stelle kein `<form>` steht.**
Nicht weil ein Formular dort technisch scheitern würde — sondern weil die
Entscheidung sonst in einem Jahr niemand mehr erkennt.

### Und eine 80, die keine Vorgabe ist

`_oberflaechenport()` fällt auf 80 zurück, wenn in `MARLEI_BASE_URL` kein
Port steht. **Das ist keine Vorgabe, die zur 8081 im Widerspruch stünde**,
sondern die Bedeutung einer Adresse ohne Doppelpunkt. Steht dort ein Port,
gilt der; steht keiner da, ist es die 80 — egal, was das
Installationsskript sonst tut.

### Nachtrag: eine Zeile tiefer stand dieselbe Zahl noch einmal

**Am selben Tag an der laufenden Installation gefunden.** Unter der
Portliste steht ein Satz über den Port, der *nicht* geöffnet gehört —
und der endete mit *„von außen kommt man über nginx auf 80"*. Feste Zahl,
und damit auf jeder Maschine falsch, auf der die Oberfläche nicht auf 80
liegt.

**Die Liste zog mit, der Satz darunter nicht** — eine Zeile tiefer, auf
derselben Karte, aus demselben Grund. *Wer eine Zahl beweglich macht,
sucht die anderen Stellen, an denen sie fest steht.*

Die Prüfung hält jetzt beide gegeneinander: Liste und Satz müssen
dieselbe Zahl nennen.


---

## 19. Ein Pfad, der zwei Systeme kennt

*Am 07.09.2026, nach der Vorgabe: **MARLEI Tasks soll auch für
Windows-Benutzer verwendbar sein.** Nicht jetzt — zuerst wird
weiterentwickelt und damit gearbeitet. Aber das Ziel steht, und eine
Stelle im Code stand ihm im Weg.*

### Die Anwendung läuft dort längst

**Beide Testreihen laufen unter Windows**, und die Vorschauen dieses
ganzen Aufbaus kamen aus einem `uvicorn` auf einem Windows-Arbeitsplatz.
Der Kern ist reines Python; alles Systemnahe steckt in drei Modulen —
`auslastung.py`, `bericht.py`, `firewall.py` —, und die liefern bei
fehlender Quelle **leere Werte statt Behauptungen.** Genau deshalb läuft
sie dort ohne einen einzigen Fehler, nur mit stummen Karten.

### Die eine Ausnahme war die Ablage

`DB_PFAD` trug `/var/lib/marlei-tasks/tasks.db` fest im Code. **Unter
Windows ergibt das `C:\var\lib\marlei-tasks`** — einen Ort, den niemand
erwartet und den kein Installationsskript anlegt. Man musste `MARLEI_DB`
setzen, sonst lief es nicht.

**Jetzt kennt die Vorgabe beide Systeme:** unter Linux `/var/lib` — der
Platz für den veränderlichen Zustand eines Dienstes —, unter Windows
`%ProgramData%`. Keiner der beiden ist geraten; es sind die Orte, die
das jeweilige System dafür vorsieht.

### Und dieselbe Falle wie beim Ausgang, vorsorglich zugemacht

`Path("")` ist `Path(".")` und damit wahr. Ein leeres `MARLEI_DB` hätte
als Angabe gegolten, und die Ablage läge im Arbeitsverzeichnis des
Dienstes — lautlos. **Beim Export hat genau das schon einmal
zugeschnappt** (Abschnitt 12); hier ist es zu, bevor es jemanden trifft.

Die Wahl steht als eigene Funktion da und nicht als Zeile beim Import:
**So lässt sie sich prüfen, ohne das Modul neu zu laden** — und vier
Prüfungen tun das.

---

## 20. Der Ausgang zum Mitnehmen

*Am 07.09.2026, mitten in der Übernahme von Boots Mappe. Die Frage:
**Lässt sich ein Datei-Download einbauen?** — und sie hat eine kürzere
Antwort, als sie klingt.*

### Der Inhalt lag schon fertig da

`export.dateien()` baut die fünf Texte **im Speicher**; `schreiben()`
legt sie hin. Für einen Download fällt nur der zweite Schritt weg. Es ist
also kein zweiter Ausgang, sondern **derselbe, einen Schritt früher
abgegriffen.**

### Und er hängt an nichts

**Nicht an `MARLEI_EXPORT`:** Wo kein Ausgang eingerichtet ist, gibt es
trotzdem etwas herunterzuladen. **Nicht an einem Zugang zur Maschine:**
Der Anlass war genau das — auf `dev-marlei` liegt die Ablage unter
`/var/lib/marlei-tasks`, das dem Dienstkonto gehört, und der angemeldete
Benutzer kommt ohne `sudo` nicht heran.

> **Wer den Server nicht selbst bedienen kann oder darf, kommt trotzdem
> an seinen Bestand.** Das ist die eigentliche Zusage hinter *der Ausgang
> bleibt Text* — und bis heute stand sie nur für den, der eine Shell hat.

**Der Umweg, den er erspart, war schon geplant:** ein Verzeichnis mit
gemeinsamer Gruppe, ein geänderter `MARLEI_EXPORT`, ein erneuter Lauf von
`install.sh`, damit `ProtectSystem=strict` es freigibt — und danach ein
`rsync` vom Arbeitsplatz. Drei Handgriffe an Rechten, für eine Frage, die
ein Knopf beantwortet.

### Die Stabilitätszusage gilt auch für das Paket

**Ein ZIP trägt zu jeder Datei eine Uhrzeit.** Nähme es die echte, wären
zwei Pakete desselben Bestands byteweise verschieden — und die Zusage
wäre genau dort gebrochen, wo man sie am leichtesten prüft: durch
zweimaliges Herunterladen.

Deshalb steht in jedem Eintrag derselbe feste Zeitpunkt (1980, der
früheste, den das Format kennt) und `0644` als Modus, damit beim
Auspacken unter Linux keine ausführbaren Textdateien liegen.

### Was er nicht tut

- **Er schreibt nicht.** Der eingerichtete Ausgang bleibt unberührt, und
  *Stand der Ausgabe* sagt danach dasselbe wie davor. Eine Prüfung hält
  genau das fest.
- **Er packt nicht alle Projekte.** Ausgegeben wird das gewählte, wie
  überall — ein Paket mit allen dreien wäre die zweite Ausnahme neben den
  Befunden.

*Fünf Prüfungen, und die schärfste ist die einfachste: zweimal
heruntergeladen, byteweise verglichen.*
