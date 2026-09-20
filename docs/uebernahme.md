# MARLEI Tasks — Was aus MARLEI Boot übernommen wird

**Stack, Ablagebild, Design und die Karten — und warum die Gleichheit
selbst der Zweck ist.**

*Festgehalten am 06.09.2026 nach der Vorgabe: derselbe Technikstack,
dasselbe Design, vier Reiter. Die Angaben über Boot sind im Quelltext
nachgesehen und nicht aus dem Gedächtnis geschrieben. Was das Produkt
darüber hinaus ausmacht — die Reiter, die Projekte, die vier Register
und die Ablage —, steht in [Aufbau](aufbau.md).*

---

## 1. Die Regel steht über allem anderen

**Einheitlichkeit ist hier keine Sparmaßnahme, sondern ein Teil des
Produkts.** Wer MARLEI Boot bedient hat, muss MARLEI Tasks öffnen und
sofort wissen, wo er ist: dasselbe Band oben, dieselben Reiter an
derselben Stelle, dieselben Karten mit demselben Fragezeichen oben
rechts. Das ist der Wiedererkennungswert, und er ist der Grund, warum es
eine Suite heißt und nicht drei Programme.

Der Satz dazu steht schon in der Einordnung (`mappe/einordnung.md`,
nicht im Repository), Abschnitt 0, und gilt ab hier als Vorgabe:

> Ein zweites Produkt, das anders aussieht und anders bedient wird,
> beschädigt das erste.

**Daraus folgt eine harte Lesart: Im Zweifel wird nicht neu entworfen,
sondern übernommen.** Eine Abweichung braucht einen Grund, der im
Entscheidungsregister steht — nicht umgekehrt. Der Normalfall ist die
Gleichheit, die Ausnahme ist begründungspflichtig.

---

## 2. Der Technikstack — unverändert

Fünf Pakete, kein Bauschritt, kein JavaScript-Gerüst:

| Paket | wofür |
|---|---|
| `fastapi>=0.115` | die Anwendung |
| `uvicorn>=0.30` | der Server dahinter |
| `jinja2>=3.1` | die Vorlagen |
| `python-multipart>=0.0.9` | Formulare und Uploads |
| `pyyaml>=6.0` | Konfiguration |

**Nichts davon wird ersetzt, und es kommt auch nichts hinzu.** Die Form
der Ablage steht in [Datenhaltung](datenhaltung.md), Abschnitt 8 —
*Datenbank als Ablage, Oberfläche als Ansicht* —, und welche es wird, ist
seit dem 06.09.2026 entschieden: **SQLite**, wie in Boot. Sie steht in
Pythons Standardbibliothek, die Liste oben bleibt also, wie sie ist. Die
Begründung samt der Produktgrenze, die daran hängt, steht in
[Aufbau](aufbau.md), Abschnitt 4.

**Was ebenfalls zum Stack gehört und leicht übersehen wird**, weil es
keine Zeile in einer `requirements.txt` hat:

- **Kein Bundler, kein Präprozessor, kein Framework.** Das JavaScript
  steht als lesbares Stück im Fuß von `base.html`, das CSS als eine
  Datei mit den Werten als Token ganz oben. Wer die Seite ansieht, sieht
  den Quelltext, der läuft.
- **Serverseitig gerendert.** Jede Seite kommt fertig aus Jinja; Skripte
  holen nur nach, was von selbst veraltet — die Seitenkarten alle zehn
  Sekunden, die Zahlen der Auslastung alle fünf.
- **Python-Module nach Fachthema**, nicht nach Technik: eine Datei je
  Frage (`auslastung.py`, `dienste.py`, `firewall.py`), jede mit einem
  Kopftext, der sagt, warum es sie gibt. `app.py` bindet zusammen.
- **Läuft ohne Internet** und ohne Rechte, die es nicht braucht. Was der
  Server nicht ablesen kann, behauptet er nicht.

---

## 3. Das Ablagebild — dieselben Ordner mit denselben Namen

| Ordner | Inhalt |
|---|---|
| `webui/` | die Anwendung: `app.py`, die Fachmodule, `templates/`, `static/` |
| `docs/` | Voraussetzungen, Installation, Betrieb, Fehlersuche, Aufbau, Gestaltung |
| `mappe/` | die acht Steuerdokumente und ihre Skripte |
| `setup/` | die Installation, je System ein Ordner: `linux/`, `windows/` |
| `tests/` | die Prüfungen |
| `marke/` | `logo-bauen.py` und die erzeugten Dateien |
| `build/` | was daraus für die Veröffentlichung entsteht |
| `tools/` | Vorschauen für die Entwicklung |

**Die Namen sind wichtiger als der Zuschnitt.** Wer in einem der
Produkte etwas sucht, sucht es im anderen an derselben Stelle. Ein
Ordner, den es hier nicht braucht, bleibt weg — aber keiner bekommt
einen anderen Namen für dieselbe Sache.

**Eine Abweichung ist notiert, und zwar genau eine:** In Boot liegen
`install.sh` und `update.sh` direkt unter `setup/`, hier eine Ebene
tiefer unter `setup/linux/` — daneben steht `setup/windows/` mit den
PowerShell-Skripten. Der Name des Ordners ist derselbe geblieben, sein
Zuschnitt nicht. *Gemacht wurde der Umzug vor der ersten
Veröffentlichung:* Danach wäre jede Pfadänderung ein toter Link in jeder
Anleitung, die jemand verlinkt oder abgeschrieben hat. Boot betrifft das
nicht — ein Bootserver bootet keine Rechner von einem Windows aus.

---

## 4. Das Design — übernommen, nicht nachgebaut

**Die Entscheidungen samt ihren Zahlen stehen in Boots
`docs/gestaltung.md`** (1469 Zeilen, Stand 06.09.2026). Sie werden hier
nicht neu getroffen und nicht neu begründet. Was übernommen wird:

- **Die Farbtoken.** Marke und Akzent sind nicht dasselbe: Navy `#063b6f`
  und Türkis `#15bcb4` sind das Logo, die Oberfläche färbt sich aus
  abgeleiteten Werten, weil je Thema eine der beiden Markenhälften
  durchfällt. Beide Themen, hell und dunkel, kommen mit.
- **Das Band im Seitenkopf**, mit dem Produktnamen links und der
  Wortmarke rechts — und die Reiterleiste als eigenes Geschwister
  darunter, weil das Band wegscrollt und die Leiste kleben bleibt.
- **Die Karte** als Grundform: Kopf mit Titel und Fragezeichen, das in
  die Hilfe springt, Inhalt, Kartenfuß, der sagt, woher die Zahlen
  kommen und wie alt sie sind.
- **Die Seitenkarte** über der Seite — rot, gelb, blau — für Befunde,
  die dem Server gelten und keiner einzelnen Karte. Mitsamt „zur
  Kenntnis nehmen" und dem Nachholen alle zehn Sekunden.
- **Die Meldungszeile** nach einem Klick, die das Neuladen nicht
  überlebt: sie ist ein Ereignis, kein Zustand.
- **Die Fußzeile:** Produktname, Version aus Git, Lizenz, Quelltext.
  Mehr nicht.
- **Die Kennzeichnung**, wenn der Server nicht die Produktion ist —
  Wort und Sandfarbe, weil die Farbe allein ein Code wäre, den man
  kennen muss.

**Das Logo bleibt dasselbe und wird nicht produktweise abgewandelt.**
Herausgeber ist Exmig, `marke/logo-bauen.py` erzeugt alle vier Dateien
aus einer Quelle. Nur der Titel im Band wechselt.

---

## 5. Die Karten auf Server Health

**Zwei, nicht fünfzehn.** Entschieden am 06.09.2026 im Durchgang durch
den Reiter:

| Karte | Modul in Boot | Warum sie mitkommt |
|---|---|---|
| **Auslastung** | `auslastung.py` | Last und Speicher kommen aus `/proc`, ohne Zusatzpakete und ohne besondere Rechte; ohne `/proc` liefert jede Funktion leere Werte statt einer Behauptung. Der zweite Teil, „laufende Übertragungen", ist Boot-eigen und wird ersetzt, nicht gestrichen. |
| **Serverdetails** | `bericht.py` | Distribution, Kernel, Virtualisierung, Dienste mit Version. Beschreibt die Maschine, nicht das Produkt — dieselbe Angabe ist auf jedem Server dieselbe. |

**Was gestrichen wurde, und warum das Argument dafür nicht trug.** Der
erste Entwurf dieses Textes zählte fünfzehn Karten auf — Dienste,
Speicherplatz, Protokoll, Firewall und den Rest — mit der Begründung:
*die Mechanik kommt mit, die Liste ist eine andere.* Bei Dienste hält
das nicht. Ein Tasks-Server hat kein dnsmasq, kein TFTP, kein NFS und
kein Samba; übrig bliebe eine Karte mit drei Zeilen statt fünf.

**Das ist nicht dieselbe Karte in dünn, sondern eine andere Karte mit
demselben Namen.** Daraus die Regel für den weiteren Durchgang:

> Eine Karte wird übernommen, wenn sie dieselbe Frage beantwortet —
> nicht, wenn sie denselben Code benutzen könnte.

**Der Unterschied ist wichtiger, als er aussieht**, weil er in die
falsche Richtung verführt: Wiederverwendbarer Code ist ein Argument des
Bauens, und die Vorgabe aus Abschnitt 1 ist eines des Bedienens. Wer
Karten nach der ersten Regel auswählt, bekommt eine Oberfläche, die
überall gleich aussieht und an der Hälfte der Stellen nichts sagt. Das
beschädigt die Einheitlichkeit, statt sie zu tragen.

---

## 6. Die Karten auf Einrichtung

**Alle sieben kommen mit, eine davon zur Hälfte** — durchgegangen am
06.09.2026, Karte für Karte:

| Karte | Was sie beantwortet | Übernahme |
|---|---|---|
| **Stand** | Welche Version läuft hier, wann kam sie, gibt es eine neuere? | **wortgleich** — nur das Repository ist ein anderes |
| **Fehlerbericht** | Etwas geht nicht: wohin, mit welchem Betreff, und was schicke ich mit? | **wortgleich** — Betreff und Berichtsinhalt wechseln |
| **Verbesserungen** | Wohin mit einer Idee oder einer Frage? | **wortgleich** — nur der Betreff |
| **Ablageorte** | Wo liegt was, ist es da, ist es beschreibbar? | **Gerüst gleich, Zeilen anders** — hier Datenbank, Export, Anhänge |
| **Einstellungen** | Wie ist dieser Server aufgesetzt — ohne SSH? | **Gerüst gleich, Zeilen anders** — fünf statt Boots neun |
| **Firewall** | Ist eine Firewall an, und was braucht das Produkt? | **mitgenommen** |
| **Ersteinrichtung** | Zurück auf den Auslieferungszustand | **mitgenommen, aber nicht unverändert** — siehe unten |

**Der Export bekommt hier seine Zeile, und das ist mehr als Kosmetik.**
In [Datenhaltung](datenhaltung.md), Abschnitt 8, steht die Zusage: *Der
Ausgang bleibt Text* — was heute die Rohdatei leistet, lesbar ohne das
Werkzeug, muss ein Export leisten. Eine Zusage, deren Ablageort nirgends
steht, ist keine. **Unter Ablageorte steht sie als Pfad mit Zustand da**,
und damit auch, ob dorthin überhaupt geschrieben werden kann.

**Damit ist auch die Frage nach dem Speicherplatz beantwortet.** Sie ist
auf Server Health durchgefallen (Abschnitt 5) und kommt hier durch die
richtige Tür wieder herein: Wo die Datenbank als Ablageort steht, gehört
ihre Größe daneben — nicht auf eine eigene Karte in einem Reiter, den
man selten aufsucht.

**Die Karte Einstellungen kommt mit, weil sie rein lesend ist.** Sie
zeigt die Env-Datei als Tabelle — Name, Wert, wofür — und ändert nichts;
der Grund steht in Boots Modulkopf: Die Datei gehört root, die Anwendung
kann dort nicht schreiben, *und das ist Absicht.* Damit beantwortet sie
eine Frage, die sich hier genauso stellt: **wie ist dieser Server
aufgesetzt, ohne dass ich mich per SSH anmelden muss?**

**Sie ist nicht dasselbe wie Ablageorte, obwohl beide Pfade zeigen:**
Einstellungen sagt, *was eingestellt ist*, Ablageorte, *ob es da und
beschreibbar ist*. Zwei Fragen, zwei Orte — genau die Regel aus der
Einordnung. Von Boots neun Werten haben drei ein Gegenstück
(`BASE_URL`, `DB`, `KENNZEICHNUNG`), dazu kommen der Exportpfad und die
Adresse für den Fehlerbericht. **Fünf Zeilen, keine eine** — und das ist
der Unterschied zur Firewall.

**Bei Firewall bleibt ein Einwand stehen, und er ist überstimmt.** Boots
Karte lebt davon, dass der Bootweg sieben Ports über vier Dienste
braucht; bei Tasks bliebe eine Zeile. Die Entscheidung im September 2026
ist, sie trotzdem mitzunehmen — die Frage *ist hier eine Firewall an,
und blockt sie mich* stellt sich auf jedem Server gleich, und die Antwort
„nichts im Weg" ist eine Auskunft, auch wenn sie kurz ist.

**Die Ersteinrichtung zerfällt in zwei Teile, und nur einer kommt mit:**

- *IP-Adresse übernehmen* fällt weg. Das ist Boot-eigen: Dort steht die
  Serveradresse in den iPXE-Skripten, deshalb ist ein Adresswechsel ein
  Ereignis. Für Tasks ist er keins.
- *Werkseinstellung* kommt mit — **aber sie ist hier gefährlicher als in
  Boot, und das muss die Karte zeigen.** Boot räumt Wiederholbares weg:
  Ein Abbild holt man erneut, ein Rechner meldet sich wieder an. Hier
  löscht derselbe Knopf die Einträge, und die gibt es nirgends sonst.
  Dieselbe Karte, dasselbe Aussehen, ein anderes Risiko.

**Daraus eine Anforderung, die beim Bauen nicht verlorengehen darf:**
Vor dem Zurücksetzen steht ein Export. Ein Knopf, der unwiederbringliche
Arbeit löscht, muss den Weg zurück anbieten, bevor er fragt — nicht
danach.

---

## 7. Was nicht mitkommt

Alles, was am Netzstart hängt: die Reiter Clients, Systeme und Quellen
samt ihren Modulen, die iPXE-Vorlagen, der Quellenwächter, das Einlesen
von Abbildern, Wake-on-LAN, die Freigaben.

**Und eine Klasse Regeln fällt ersatzlos weg:** die aus
[Datenhaltung](datenhaltung.md), Abschnitt 5 — 74 Spalten, eine
Fettstelle je Zeile, zwei unsichtbare Leerzeichen, LF. Sie sind der
Preis dafür, dass eine Rohdatei die Leseoberfläche ist. Dieses Produkt
hat ein eigenes Gesicht. **Ihr Zweck fällt aber nicht weg**, und Boots
Gestaltung trägt ihn schon: Werte oben vor der Beschreibung, eine
Führungszeile je Abschnitt, ein Zustand statt eines Textstils, und ein
ausdrücklicher Wert für *noch nicht entschieden* statt eines leeren
Feldes.

---

## 8. Wie das Gemeinsame geteilt wird

**Entschieden am 06.09.2026: abschreiben, aber unter Aufsicht** — und
mit einer benannten Bedingung, wann umgestiegen wird.

### Worum es geht

Diese Dateien sollen in beiden Produkten dieselben sein:

| | Umfang | produktbezogen |
|---|---|---|
| `static/style.css` | 1704 Zeilen, 285 Regeln | 18 Regeln (6 %) |
| `templates/base.html` | 288 Zeilen | 3 Zeilen — die Reiter |
| `_befunde` · `_auslastung` · `_status.html` | 108 Zeilen | nichts |
| die Servermodule, nach dem Kartenschnitt noch elf | ~2100 Zeilen | 1 bis 18 Zeilen je Modul |
| `docs/gestaltung.md` | 1469 Zeilen | wenige Beispiele |
| `marke/logo-bauen.py` und die vier erzeugten Dateien | 327 Zeilen | nichts |

### Zwei Wege sind schon ausgeschieden

**Eine gemeinsame Abhängigkeit zur Laufzeit.** Die Vorgabe: Die
Produkte werden getrennt installiert und getrennt verwaltet, jedes als
eigenes Produkt. Ein Server, auf dem MARLEI Tasks läuft, darf nichts
mitinstallieren, was zu MARLEI Boot gehört — sonst hängen zwei
Installationen aneinander, die nie zusammen gedacht waren, und ein
Update am einen fasst das andere an.

**Ein gemeinsames Repository.** Die Repositories bleiben getrennt, damit
jedes Produkt seine eigene Sichtbarkeit behält.

**Damit wird die Frage kleiner, als sie klingt.** Weil es keine
Laufzeit-Abhängigkeit gibt, müssen diese Dateien am Ende **physisch in
beiden Repositories liegen** — ein `install.sh` klont ein Repo und
findet alles vor. **Es geht also nicht um „kopieren oder teilen",
sondern um: von Hand kopieren oder mit Werkzeug.**

### Der gewählte Weg: abschreiben mit Prüfer

Die geteilten Dateien werden kopiert, **in einer Liste geführt und von
einem Skript gegen den vereinbarten Stand gehalten.** Es ist dieselbe
Bauart wie Boots `pruefe-verweise.py` — ein Skript, das eine Handregel
ehrlich hält, weil die Regel sich selbst nicht durchsetzen kann.

**Der Prüfer ist ein Entwicklungswerkzeug und gehört nach `tools/`,
nicht nach `webui/`.** Das folgt aus derselben Vorgabe wie oben: geteilt
wird beim Entwickeln, nicht beim Betreiben. Was auf einem Server liegt,
gehört genau einem Produkt und trägt dessen Namen.

**Gebaut wird er zusammen mit der ersten Kopie**, nicht vorher — heute
gäbe es nichts zu prüfen.

### Warum nicht gleich ein gemeinsames Repo mit `git subtree`

Der Weg wäre der sauberere: Die geteilten Dateien lägen in einem dritten
Repository und würden in beide Produkte gespiegelt — als **echte
Dateien**, nicht als Zeiger, sodass ein `git clone` weiterhin alles
liefert. *(Ein Submodul wäre der falsche Nachbar: Dort ist die Datei ein
Zeiger, und der Installer bräuchte `--recursive` — ein Betriebsschritt
mehr.)*

**Er verlangt aber Vorarbeit an Boot, und Boot läuft produktiv:**

- Die 18 produktbezogenen CSS-Regeln müssten aus `style.css` heraus.
- `base.html` müsste in ein gemeinsames Gerüst und eine
  Produkt-Reiterleiste zerfallen.
- Das Präfix `PXE_` / `pxeweb` müsste ein Parameter werden, den das
  Produkt mitgibt — sonst trüge ein Tasks-Server Variablen mit `PXE_` im
  Namen.

**Das ist ein Umbau an einem laufenden Produkt für ein zweites, das es
noch nicht gibt.** Er wird nicht verworfen, nur verschoben.

### Die Bedingung, die den Umstieg auslöst

Umgestiegen wird auf `subtree`, sobald **eines** von beidem eintritt:

- **Dieselbe Datei ist zum dritten Mal von Hand nachgezogen worden.**
- **MARLEI Inventory fängt an.** Bei drei Produkten trägt Handarbeit
  nicht mehr.

**Warum das kein Aufschieben ist:** Solange die Kopien **byteweise
gleich** sind und die Liste sie benennt, ist das spätere Herausziehen
mechanisch. Teuer wird es nur, wenn sie driften — und genau das meldet
der Prüfer. *Der Satz „wer zuerst abschreibt und später teilt, hat die
Arbeit zweimal" gilt deshalb nur für ein unbeaufsichtigtes Abschreiben.*

**Die Regel dazu, und sie ist die eigentliche Verpflichtung:** Eine
Änderung an einer geteilten Datei wird **in derselben Sitzung** in
beide Repositories getragen. Der Prüfer findet, was trotzdem
durchrutscht; er ersetzt die Regel nicht.

---

## 9. Was hiermit entschieden ist

- **Der Technikstack ist derselbe wie in MARLEI Boot.** Die Ablage ist
  **SQLite** — dieselbe wie dort, samt Boots Verfahren für spätere
  Spalten. Ergänzt wird nichts: `sqlite3` steht in Pythons
  Standardbibliothek.
- **Das Design wird übernommen, nicht neu entworfen.** Boots
  `docs/gestaltung.md` gilt; eine Abweichung braucht einen Eintrag im
  Entscheidungsregister.
- **Vier Reiter kommen aus Boot mit:** Server Health, Einrichtung,
  History, Hilfe. **Nicht deren Anordnung** — sie folgt Boots Prinzip
  (Häufigkeit im Betrieb) und stellt Server Health deshalb ganz nach
  hinten, statt wie dort nach vorn. Die ganze Leiste steht in
  [Aufbau](aufbau.md), Abschnitt 1.
- **Eine Karte wird übernommen, wenn sie dieselbe Frage beantwortet**,
  nicht, wenn sie denselben Code benutzen könnte.
- **Auf Server Health stehen zwei Karten:** Auslastung und
  Serverdetails. Alle übrigen fallen weg — Abschnitt 5 sagt, warum.
- **Auf Einrichtung kommen alle sieben Karten mit** — Stand,
  Fehlerbericht, Verbesserungen, Ablageorte, Einstellungen, Firewall
  und die Ersteinrichtung, diese aber nur zur Hälfte: die
  Werkseinstellung ja, das Übernehmen der IP-Adresse nicht.
  Abschnitt 6 sagt je Karte, warum.
- **Der Export bekommt einen Pfad unter Ablageorte**, und vor der
  Werkseinstellung steht er als Angebot.
- **History behält den Namen und bekommt den Inhalt dieses Produkts.**
- **Geteilt wird beim Entwickeln, nicht beim Betreiben.** Die beiden
  Produkte werden getrennt installiert und getrennt verwaltet; keine
  gemeinsame Abhängigkeit auf dem Server.

- **Geteilt wird durch Abschreiben unter Aufsicht** — eine Liste der
  geteilten Dateien und ein Prüfer in `tools/`. Umgestiegen wird auf
  `git subtree`, sobald dieselbe Datei zum dritten Mal von Hand
  nachgezogen wurde oder MARLEI Inventory anfängt. Abschnitt 8.

**Damit ist an diesem Dokument nichts mehr offen.** Was noch aussteht,
betrifft den Aufbau des Produkts und steht in [Aufbau](aufbau.md).
